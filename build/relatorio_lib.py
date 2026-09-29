#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funções puras de datas/agregação compartilhadas entre `gerar_relatorios.py`
(fallback manual, determinístico) e `coletar_dados_relatorio.py` (coleta de
números para a Routine do Claude escrever os Insights de Tráfego). Nenhuma
lógica de texto/interpretação mora aqui — só aritmética sobre os registros
brutos de `build.py` (`leads[]`/`meta[]`/`sales[]`).

Funil deste cliente: Impressões → Cliques → Page View → Leads → MQLs →
Agendamentos → Vendas. Não há etapa de comparecimento (o agendamento acontece
via WhatsApp, fora da mídia paga) — a responsabilidade do tráfego termina no
MQL. Agendamentos não têm fonte de dado conectada ainda (ver
`build/GUIA-RELATORIOS.md` → "Gargalo de dado").
"""
from __future__ import annotations

from datetime import datetime, timedelta, date

import build as bp

BRT = bp.BRT


def d(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def ds(x: date) -> str:
    return x.strftime("%Y-%m-%d")


def in_range(row_date: str | None, start: date, end: date) -> bool:
    if not row_date:
        return False
    try:
        rd = d(row_date)
    except ValueError:
        return False
    return start <= rd <= end


def shift_back(start: date, end: date, n: int) -> tuple[date, date]:
    """Janela imediatamente anterior, mesmo tamanho, deslocada n vezes."""
    span = (end - start).days + 1
    new_end = start - timedelta(days=1 + span * (n - 1))
    new_start = new_end - timedelta(days=span - 1)
    return new_start, new_end


def agg(meta: list[dict], leads: list[dict], sales: list[dict], start: date, end: date,
        camp: str | None = None, adset: str | None = None, ad: str | None = None) -> dict:
    """Agrega mídia paga (spend/impr/clicks/pv) + leads/MQLs + vendas/faturamento
    dentro do intervalo [start, end], com filtro opcional de campanha/conjunto/
    anúncio. `sales` usa o mesmo campo `camp`/`adset`/`ad` de atribuição
    (herdado do lead de origem em `build.py::process`)."""
    def keep(r):
        if not in_range(r["d"], start, end):
            return False
        if camp is not None and r["camp"] != camp:
            return False
        if adset is not None and r["adset"] != adset:
            return False
        if ad is not None and r["ad"] != ad:
            return False
        return True

    m = [r for r in meta if keep(r)]
    l = [r for r in leads if keep(r)]
    s = [r for r in (sales or []) if keep(r)]
    spend = sum(r["sp"] for r in m) * bp.TAX_FACTOR
    impr = sum(r["im"] for r in m)
    clicks = sum(r["cl"] for r in m)
    pv = sum(r.get("pv", 0) for r in m)
    n_leads = len(l)
    n_mqls = sum(r["q"] for r in l)
    n_vendas = sum(r.get("vendas", 1) for r in s)
    faturamento = sum(r.get("fat", 0) for r in s)
    return {
        "spend": spend, "impr": impr, "clicks": clicks, "pv": pv,
        "leads": n_leads, "mqls": n_mqls, "vendas": n_vendas, "faturamento": faturamento,
    }


def derived(a: dict) -> dict:
    spend, impr, clicks, pv, leads, mqls, vendas = (
        a["spend"], a["impr"], a["clicks"], a["pv"], a["leads"], a["mqls"], a["vendas"],
    )
    return {
        "cpm": (spend / impr * 1000) if impr else None,
        "ctr": (clicks / impr) if impr else None,
        "connect_rate": (pv / clicks) if clicks else None,
        "convlp": (leads / pv) if pv else None,
        "cpl": (spend / leads) if leads else None,
        "txmql": (mqls / leads) if leads else None,
        "cpmql": (spend / mqls) if mqls else None,
        "cac": (spend / vendas) if vendas else None,
        **a,
    }


RATE_METRICS = {"ctr", "connect_rate", "convlp", "txmql"}
MATERIAL_PCT = 0.10     # variação relativa mínima p/ considerar mudança relevante
MATERIAL_PP = 0.03      # variação em pontos percentuais mínima p/ métricas de taxa


def compare(cur: dict, prev: dict | None) -> dict:
    """Compara duas agregações `derived()` métrica a métrica. Só marca
    `material=True` quando a variação passa os limiares mínimos — evita
    listar oscilações irrelevantes como se fossem alerta."""
    metrics = ["spend", "impr", "clicks", "pv", "leads", "mqls", "vendas", "faturamento",
               "cpm", "ctr", "connect_rate", "convlp", "cpl", "txmql", "cpmql", "cac"]
    out = {}
    for m in metrics:
        cv, pv_ = cur.get(m), (prev or {}).get(m)
        row = {"atual": cv, "anterior": pv_, "delta_abs": None, "delta_pct": None,
               "delta_pp": None, "direcao": "sem_dado", "material": False}
        if cv is not None and pv_ is not None:
            row["delta_abs"] = round(cv - pv_, 4)
            row["delta_pct"] = round((cv - pv_) / pv_, 4) if pv_ else None
            if m in RATE_METRICS:
                row["delta_pp"] = round((cv - pv_) * 100, 2)
            higher_is_better = m not in ("spend", "cpm", "cpl", "cpmql", "cac")
            if abs(cv - pv_) < 1e-9:
                row["direcao"] = "estavel"
            else:
                melhorou = (cv > pv_) == higher_is_better
                row["direcao"] = "melhorou" if melhorou else "piorou"
            if m in RATE_METRICS:
                row["material"] = row["delta_pp"] is not None and abs(row["delta_pp"]) >= MATERIAL_PP * 100
            else:
                row["material"] = row["delta_pct"] is not None and abs(row["delta_pct"]) >= MATERIAL_PCT
        elif cv is not None and pv_ is None:
            row["direcao"] = "sem_periodo_anterior"
        out[m] = row
    return out


# --------------------------------------------------------------------------- #
# Formatação (usada pelos templates de texto do gerar_relatorios.py)
# --------------------------------------------------------------------------- #
def money(v) -> str:
    if v is None:
        return "—"
    return f"R$ {v:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


def pct(v) -> str:
    if v is None:
        return "—"
    return f"{v * 100:.1f}%".replace(".", ",")


def num(v) -> str:
    if v is None:
        return "—"
    return f"{v:,.0f}".replace(",", ".")


def meta_status(nome: str, valor) -> str:
    return "meta não definida" if valor is None else f"meta {nome} = {money(valor)}"
