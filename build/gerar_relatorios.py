#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera build/relatorios.json (aba "Relatório" -> "Insights de Tráfego") aplicando
DETERMINISTICAMENTE as regras de build/GUIA-RELATORIOS.md sobre os mesmos dados
que alimentam o dashboard (mídia paga x Leads x Vendas), para o FECHAMENTO DO
DIA (não mais por 9 períodos).

Não chama nenhuma API de IA/LLM — é só aritmética + templates de texto em
Python. Custo zero de créditos Anthropic, roda 100% dentro do GitHub Actions.

**Status:** este script não roda automaticamente (o pipeline diário é
`coletar_dados_relatorio.py` + a Routine do Claude — ver `GUIA-RELATORIOS.md`).
Fica no repo como ferramenta manual/fallback: se a Routine falhar num dia,
rode este script pra garantir que a seção não fique vazia. Emite o MESMO
schema (6 seções) que a Routine — mais raso na profundidade analítica (sem
prosa livre), mas estruturalmente idêntico, então a interface não precisa de
nenhum caminho alternativo de renderização.

Uso:
    python build/gerar_relatorios.py --out build/relatorios.json
    python build/gerar_relatorios.py --leads-file leads.csv --meta-file meta.csv --sales-file vendas.csv --out build/relatorios.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as bp  # reaproveita fetch/parse/process/constantes de build.py
from relatorio_lib import BRT, d, agg, derived, compare, shift_back, money, pct, num, meta_status  # noqa: F401
from coletar_dados_relatorio import totais_dict, breakdown_today


# --------------------------------------------------------------------------- #
# 1 · RESUMO DO PERÍODO
# --------------------------------------------------------------------------- #
def sec_resumo(today, hoje: dict, j7: dict, j14: dict, j30: dict, calibracao: dict,
               meta_cpmql, meta_cac, volume_min: int) -> str:
    partes = [
        f"<p><b>{today.strftime('%d/%m/%Y')}</b> — investimento {money(hoje['spend'])}, "
        f"{num(hoje['leads'])} lead(s), {num(hoje['mqls'])} MQL(s).</p>",
    ]
    if calibracao["em_calibracao"]:
        partes.append(
            f"<p><b>Conta em fase de calibração:</b> {num(calibracao['mqls_acumulados'])} MQL(s) "
            f"acumulado(s) desde o início, abaixo do mínimo amostral configurado ({num(volume_min)}). "
            f"Faltam {num(calibracao['faltam'])} MQL(s) para leitura confiável — ainda não há base "
            f"suficiente para comparar com histórico ou apontar tendência.</p>"
        )
    else:
        partes.append(
            f"<p>CPL do dia {money(hoje['cpl'])} — janelas: 7d {money(j7['cpl'])} · 14d "
            f"{money(j14['cpl'])} · 30d {money(j30['cpl'])}. Tx-MQL (7d): {pct(j7['txmql'])}.</p>"
        )
    partes.append(
        f"<p>Metas: CPMQL — {meta_status('CPMQL', meta_cpmql)}"
        + (f", hoje {money(hoje['cpmql'])}" if hoje["cpmql"] is not None else "")
        + f"; CAC — {meta_status('CAC', meta_cac)}"
        + (f", hoje {money(hoje['cac'])}" if hoje["cac"] is not None else "")
        + f". Amostra mínima configurada: {num(volume_min)} MQLs.</p>"
    )
    return "".join(partes)


# --------------------------------------------------------------------------- #
# 2 · LEITURA DO FUNIL
# --------------------------------------------------------------------------- #
def sec_leitura_funil(hoje: dict, calibracao: dict, volume_min: int) -> str:
    if not hoje["leads"] and not hoje["spend"]:
        return "<p>Sem investimento/atividade registrada hoje — sem base para leitura de funil.</p>"

    partes = []
    if calibracao["em_calibracao"]:
        partes.append(
            f"<p>Volume do dia ({num(hoje['leads'])} lead(s), {num(hoje['mqls'])} MQL(s)) é baixo demais "
            f"para julgar qualquer etapa isoladamente — provável ruído por volume baixo, não sinal real "
            f"de gargalo. Faltam {num(calibracao['faltam'])} MQL(s) acumulados para confiança na "
            f"leitura ({num(calibracao['mqls_acumulados'])}/{num(volume_min)}).</p>"
        )
    else:
        partes.append(
            f"<p>CTR {pct(hoje['ctr'])} · Connect Rate {pct(hoje['connect_rate'])} · ConvLP "
            f"{pct(hoje['convlp'])} · Tx-MQL {pct(hoje['txmql'])}. Leia sempre cruzando etapa anterior "
            f"e posterior (ver GUIA-INTERPRETACAO-METRICAS.md) — nenhuma dessas métricas isolada define "
            f"o gargalo do dia.</p>"
        )
    partes.append(
        "<p>Agendamentos não têm fonte de dado conectada — Taxa de Agendamento, Custo por Agendamento "
        "e Taxa de Vendas não entram nesta leitura (ver GARGALO DE DADO).</p>"
    )
    return "".join(partes)


# --------------------------------------------------------------------------- #
# 3 · CLASSIFICAÇÃO POR CAMPANHA/CONJUNTO
# --------------------------------------------------------------------------- #
def sec_classificacao(por_campanha: list[dict], por_conjunto: list[dict]) -> str:
    if not por_campanha:
        return "<p>Sem campanhas com atividade hoje.</p>"

    partes = ["<p><b>Campanhas do dia:</b></p><ul>"]
    for r in por_campanha:
        flag = " — <b>abaixo do mínimo amostral, sem decisão</b>" if r["abaixo_minimo"] else ""
        partes.append(f"<li>{r['campanha']} — {num(r['leads'])} lead(s), {num(r['mqls'])} MQL(s){flag}</li>")
    partes.append("</ul><p><b>Conjuntos do dia:</b></p><ul>")
    for r in por_conjunto:
        flag = " — <b>abaixo do mínimo amostral, sem decisão</b>" if r["abaixo_minimo"] else ""
        partes.append(f"<li>{r['campanha']} · {r['conjunto']} — {num(r['leads'])} lead(s), {num(r['mqls'])} MQL(s){flag}</li>")
    partes.append("</ul>")
    if any(r["abaixo_minimo"] for r in por_campanha + por_conjunto):
        partes.append("<p>Recortes marcados acima ficam apenas sinalizados — nenhuma decisão de cortar/escalar deve ser tomada sobre eles ainda.</p>")
    return "".join(partes)


# --------------------------------------------------------------------------- #
# 4 · GARGALO DE DADO (opcional)
# --------------------------------------------------------------------------- #
def sec_gargalo_dado(fontes: dict) -> str | None:
    faltando = [k for k, v in fontes.items() if not v]
    if not faltando:
        return None
    return (
        "<p><b>Agendamentos não têm fonte de dado conectada</b> ao dashboard (o agendamento acontece "
        "via WhatsApp, fora da mídia paga). Impacto: Taxa de Agendamento e Custo por Agendamento ficam "
        "\"-\"; Taxa de Vendas também fica \"-\" (usa Agendamentos como denominador), mesmo com o número "
        "absoluto de Vendas e o CAC disponíveis (Vendas já está conectada e cruzada com Leads). Ação de "
        "maior impacto: conectar a planilha/lista do comercial com os agendamentos feitos via WhatsApp — "
        "sem isso, qualquer decisão de otimização depois do MQL é decisão às cegas.</p>"
    )


# --------------------------------------------------------------------------- #
# 5 · AÇÕES RECOMENDADAS
# --------------------------------------------------------------------------- #
def sec_acoes(calibracao: dict, hoje: dict, volume_min: int) -> str:
    if calibracao["em_calibracao"]:
        return (
            f"<p>Sem ação — seguir tendência até acumular {num(volume_min)} MQLs "
            f"(faltam {num(calibracao['faltam'])}). Ainda não há base suficiente para recomendar "
            f"escalar, cortar ou otimizar qualquer estrutura.</p>"
        )
    if not hoje["leads"] and not hoje["spend"]:
        return "<p>Sem ação recomendada — nenhum investimento/atividade hoje.</p>"
    return (
        "<p>Gerador determinístico (fallback): sem prosa analítica automática por gargalo — revisar "
        "manualmente a seção LEITURA DO FUNIL contra GUIA-INTERPRETACAO-METRICAS.md e priorizar a etapa "
        "com maior variação material do dia antes de agir.</p>"
    )


# --------------------------------------------------------------------------- #
# 6 · PRÓXIMA DECISÃO
# --------------------------------------------------------------------------- #
def sec_proxima_decisao(calibracao: dict, volume_min: int) -> str:
    if calibracao["em_calibracao"]:
        return (
            f"<p>Gatilho: acumulado atingir {num(volume_min)} MQLs (faltam {num(calibracao['faltam'])}). "
            f"Próxima revisão: atualização diária de amanhã, 23h59 BRT.</p>"
        )
    return "<p>Gatilho: qualquer variação material (≥10% ou ≥3pp) frente às janelas de 7/14/30 dias. Próxima revisão: atualização diária de amanhã, 23h59 BRT.</p>"


def build_payload(today, meta, leads, sales, meta_cpmql, meta_cac, volume_min: int) -> dict:
    hoje = derived(agg(meta, leads, sales, today, today))
    j7 = derived(agg(meta, leads, sales, today - timedelta(days=6), today))
    j14 = derived(agg(meta, leads, sales, today - timedelta(days=13), today))
    j30 = derived(agg(meta, leads, sales, today - timedelta(days=29), today))

    date_min = min((r["d"] for r in leads + meta + sales if r.get("d")), default=today.strftime("%Y-%m-%d"))
    date_max = max((r["d"] for r in leads + meta + sales if r.get("d")), default=today.strftime("%Y-%m-%d"))
    acumulado = derived(agg(meta, leads, sales, d(date_min), d(date_max)))
    mqls_acumulados = acumulado["mqls"] or 0
    calibracao = {
        "em_calibracao": mqls_acumulados < volume_min,
        "mqls_acumulados": mqls_acumulados,
        "volume_min_amostral": volume_min,
        "faltam": max(0, volume_min - mqls_acumulados),
    }

    por_campanha = breakdown_today(meta, leads, sales, today, "camp", volume_min)
    por_conjunto = breakdown_today(meta, leads, sales, today, "adset", volume_min)
    fontes = {"agendamentos": False, "vendas": True, "faturamento": True}

    payload = {
        "resumo_periodo": sec_resumo(today, totais_dict(hoje), totais_dict(j7), totais_dict(j14),
                                      totais_dict(j30), calibracao, meta_cpmql, meta_cac, volume_min),
        "leitura_funil": sec_leitura_funil(totais_dict(hoje), calibracao, volume_min),
        "classificacao_campanhas": sec_classificacao(por_campanha, por_conjunto),
        "acoes_recomendadas": sec_acoes(calibracao, totais_dict(hoje), volume_min),
        "proxima_decisao": sec_proxima_decisao(calibracao, volume_min),
    }
    gargalo = sec_gargalo_dado(fontes)
    if gargalo:
        payload["gargalo_dado"] = gargalo
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leads-file")
    ap.add_argument("--meta-file")
    ap.add_argument("--sales-file")
    ap.add_argument("--out", default="build/relatorios.json")
    args = ap.parse_args()

    leads_rows = bp.load_rows(bp.sheet_url(bp.SPREADSHEET_ID_FUNIL, bp.SHEET_LEADS), args.leads_file)
    sales_rows = bp.load_rows(bp.sheet_url(bp.SPREADSHEET_ID_FUNIL, bp.SHEET_VENDAS), args.sales_file)
    meta_rows = bp.load_rows(bp.sheet_url(bp.SPREADSHEET_ID_META, bp.SHEET_META), args.meta_file)
    data = bp.process(leads_rows, meta_rows, sales_rows)
    leads, meta, sales = data["leads"], data["meta"], data["sales"]

    now_brt = datetime.now(BRT)
    today = now_brt.date()

    payload = build_payload(today, meta, leads, sales, bp.META_CPMQL, bp.META_CAC, bp.VOLUME_MIN_AMOSTRAL)

    out = {
        "generated_at": now_brt.strftime("%d/%m/%Y %H:%M"),
        "data_referencia": today.strftime("%Y-%m-%d"),
        "fonte": "Insights de Tráfego gerados automaticamente (regras determinísticas do GUIA-RELATORIOS.md, "
                 "sem chamada de IA) a partir dos dados do funil (mídia paga × Leads × Vendas).",
        **payload,
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("== gerar_relatorios ok ==", file=sys.stderr)
    print(f"  data_referencia: {out['data_referencia']}", file=sys.stderr)
    print(f"  out: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
