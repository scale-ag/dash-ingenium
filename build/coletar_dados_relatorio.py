#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera build/relatorios_dados.json: SÓ NÚMEROS (nenhuma interpretação/texto),
sobre o fechamento do DIA — não mais por 9 períodos. É o insumo lido pela
Routine do Claude (ver GUIA-RELATORIOS.md) para escrever build/relatorios.json
(Insights de Tráfego, 6 seções) — garante que os números do texto batem 1:1
com o site sem depender do Claude "fazer conta". Não chama nenhuma API de
IA/LLM.

Uso:
    python build/coletar_dados_relatorio.py --out build/relatorios_dados.json
    python build/coletar_dados_relatorio.py --leads-file leads.csv --meta-file meta.csv --sales-file vendas.csv --out build/relatorios_dados.json

Sem --leads-file/--meta-file/--sales-file, busca os CSVs públicos da
planilha (mesma URL de build.py) — precisa de acesso a docs.google.com (o
runner do GitHub Actions tem; o sandbox do agente normalmente não).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as bp  # reaproveita fetch/parse/process/constantes de build.py
from relatorio_lib import BRT, d, agg, derived, compare, shift_back  # noqa: F401


def _r(v, nd=2):
    return None if v is None else round(v, nd)


def totais_dict(a: dict) -> dict:
    return {
        "spend": round(a["spend"], 2), "impr": a["impr"], "clicks": a["clicks"], "pv": a["pv"],
        "leads": a["leads"], "mqls": a["mqls"], "vendas": a["vendas"], "faturamento": round(a["faturamento"], 2),
        "cpm": _r(a["cpm"]), "ctr": _r(a["ctr"], 4), "connect_rate": _r(a["connect_rate"], 4),
        "convlp": _r(a["convlp"], 4), "cpl": _r(a["cpl"]), "txmql": _r(a["txmql"], 4),
        "cpmql": _r(a["cpmql"]), "cac": _r(a["cac"]),
    }


def breakdown_today(meta: list[dict], leads: list[dict], sales: list[dict], today, dim: str,
                     volume_min: int) -> list[dict]:
    """Agrega por campanha/conjunto SÓ DO DIA (`today`) — usado na seção
    CLASSIFICAÇÃO POR CAMPANHA/CONJUNTO. Marca `abaixo_minimo` quando o
    recorte não atinge o volume mínimo amostral configurado no painel
    (`params.volume_min_amostral`, em MQLs — o mesmo número citado na fase
    de calibração)."""
    def key_of(r):
        return r["camp"] if dim == "camp" else (r["camp"], r["adset"])

    today_s = today.strftime("%Y-%m-%d")
    keys = set()
    for r in meta:
        if r["d"] == today_s:
            keys.add(key_of(r))
    for r in leads:
        if r["d"] == today_s:
            keys.add(key_of(r))

    out = []
    for k in sorted(keys, key=lambda x: str(x)):
        camp, adset = (k, None) if dim == "camp" else (k[0], k[1])
        a = derived(agg(meta, leads, sales, today, today, camp=camp, adset=adset))
        if not a["spend"] and not a["leads"]:
            continue
        row = totais_dict(a)
        row["abaixo_minimo"] = a["mqls"] < volume_min
        if dim == "camp":
            row["campanha"] = camp
        else:
            row["campanha"], row["conjunto"] = camp, adset
        out.append(row)
    out.sort(key=lambda r: -r["spend"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leads-file")
    ap.add_argument("--meta-file")
    ap.add_argument("--sales-file")
    ap.add_argument("--out", default="build/relatorios_dados.json")
    args = ap.parse_args()

    leads_rows = bp.load_rows(bp.sheet_url(bp.SPREADSHEET_ID_FUNIL, bp.SHEET_LEADS), args.leads_file)
    sales_rows = bp.load_rows(bp.sheet_url(bp.SPREADSHEET_ID_FUNIL, bp.SHEET_VENDAS), args.sales_file)
    meta_rows = bp.load_rows(bp.sheet_url(bp.SPREADSHEET_ID_META, bp.SHEET_META), args.meta_file)
    data = bp.process(leads_rows, meta_rows, sales_rows)
    leads, meta, sales = data["leads"], data["meta"], data["sales"]

    now_brt = datetime.now(BRT)
    today = now_brt.date()
    date_min = d(data["build"]["date_min"]) if data["build"]["date_min"] else today
    date_max = d(data["build"]["date_max"]) if data["build"]["date_max"] else today

    hoje = derived(agg(meta, leads, sales, today, today))
    j7 = derived(agg(meta, leads, sales, today - timedelta(days=6), today))
    j14 = derived(agg(meta, leads, sales, today - timedelta(days=13), today))
    j30 = derived(agg(meta, leads, sales, today - timedelta(days=29), today))
    acumulado = derived(agg(meta, leads, sales, date_min, date_max))

    volume_min = bp.VOLUME_MIN_AMOSTRAL
    mqls_acumulados = acumulado["mqls"] or 0
    em_calibracao = mqls_acumulados < volume_min

    out = {
        "generated_at": now_brt.strftime("%d/%m/%Y %H:%M"),
        "generated_at_iso": now_brt.isoformat(),
        "fonte": "Números brutos do fechamento do dia (mídia paga × Leads × Vendas) — insumo para a "
                 "Routine do Claude escrever build/relatorios.json (Insights de Tráfego, 6 seções). Sem "
                 "interpretação/texto aqui, só aritmética.",
        "data_referencia": today.strftime("%Y-%m-%d"),
        "params": {
            "tax_factor": bp.TAX_FACTOR,
            "sample_min_spend": bp.SAMPLE_MIN_SPEND,
            "sample_min_mqls": bp.SAMPLE_MIN_MQLS,
            "meta_cpmql": bp.META_CPMQL,
            "meta_cac": bp.META_CAC,
            "volume_min_amostral": volume_min,
            "n_dias_corte": bp.N_DIAS_CORTE,
        },
        # Funil: Impressões -> Cliques -> Page View -> Leads -> MQLs -> Agendamentos -> Vendas.
        # Agendamentos ainda não tem fonte conectada (nem aba, nem coluna) — só Vendas/Faturamento
        # já cruzam com Leads (build.py::build_purchases + process). Ver GUIA-RELATORIOS.md.
        "fontes_conectadas": {
            "impressoes_cliques": True, "page_view": True, "leads": True, "mqls": True,
            "agendamentos": False, "vendas": True, "faturamento": True,
        },
        "hoje": totais_dict(hoje),
        "janelas": {
            "7d": totais_dict(j7), "14d": totais_dict(j14), "30d": totais_dict(j30),
        },
        "acumulado_total": {
            "range": {"start": date_min.strftime("%Y-%m-%d"), "end": date_max.strftime("%Y-%m-%d")},
            **totais_dict(acumulado),
        },
        "calibracao": {
            "em_calibracao": em_calibracao,
            "mqls_acumulados": mqls_acumulados,
            "volume_min_amostral": volume_min,
            "faltam": max(0, volume_min - mqls_acumulados),
        },
        "por_campanha": breakdown_today(meta, leads, sales, today, "camp", volume_min),
        "por_conjunto": breakdown_today(meta, leads, sales, today, "adset", volume_min),
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("== coletar_dados_relatorio ok ==", file=sys.stderr)
    print(f"  data_referencia: {out['data_referencia']}", file=sys.stderr)
    print(f"  em_calibracao: {em_calibracao}  mqls_acumulados: {mqls_acumulados}/{volume_min}", file=sys.stderr)
    print(f"  out: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
