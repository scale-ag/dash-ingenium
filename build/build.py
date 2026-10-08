#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera a dashboard estatica (index.html) do cliente Ingenium Advisers
(Funil de Sessao Estrategica · sigla de campanha "IA") a partir de 2 planilhas:

  - "Lead Ads" (form IA | FORM-01 [V1]) e "IA | FORM-01 [V2]" (planilha de
    Leads, SPREADSHEET_ID_LEADS): leads dos 2 formularios nativos do Meta.
    Cada aba tem seu proprio cabecalho; load_leads() mapeia as duas para um
    cabecalho canonico (LEADS_CANON), junta e remove duplicados por id antes
    do process(). Cada linha ja traz campaign_name / adset_name / ad_name,
    que cruzam 1:1 com Campaign Name / Ad Set Name / Ad Name do Meta Ads.
  - "IA | QUERIES | GIACO" (planilha Meta Ads, SPREADSHEET_ID_META): investimento,
    impressoes e cliques do gerenciador.
  - Compradores/Vendas: AINDA NAO CONECTADA (SPREADSHEET_ID_VENDAS = None).
    A estrutura de Vendas/CAC/Faturamento/ROAS fica na tela como mockup
    (zerada/"-"); basta preencher o ID/aba para ligar o cruzamento.

Criterio de Lead Qualificado (MQL), igual para os 2 forms: faturamento acima
de R$ 200 mil. Coluna M de cada aba (V1: "qual_e_o_faturamento_anual_...";
V2: "qual_e_o_seu_faturamento_..."). Sem depender do texto exato: vazio ou
comecando com "ate" = nao qualificado; qualquer outra faixa com numero = MQL.
Lead de teste da Meta ("<test lead") nunca conta.

Este script apenas LE as planilhas (export CSV publico, buscado por NOME da
aba — sem depender de gid) e emite os REGISTROS BRUTOS (leads[], meta[] e
sales[]) dentro do HTML. Todos os filtros, agregacoes, KPIs, tabelas e
graficos sao calculados no navegador (client-side em app.js). Nunca escreve
nada de volta nas planilhas.

Teste local: --leads-file (repetivel, 1 CSV por aba de leads) / --meta-file /
--sales-file apontando para CSVs baixados.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

# Planilha de Leads (formularios nativos Meta) — busca por nome de aba, sem gid.
# Uma aba por formulario; todas sao lidas e unificadas em load_leads().
SPREADSHEET_ID_LEADS = "1Gw6XZSL8OG4VYs8rEP2_vHvYLhbT4uhJFBOlLRyBZIg"
SHEETS_LEADS = ["Lead Ads", "IA | FORM-01 [V2]"]   # V1, V2
# Planilha de Compradores — ainda nao conectada (mockup). Preencher para ligar
# o cruzamento de vendas (colunas esperadas em build_purchases()).
SPREADSHEET_ID_VENDAS = None
SHEET_VENDAS = "Vendas"
# Planilha do Meta Ads (separada da planilha de Leads).
SPREADSHEET_ID_META = "1urfcE0E-FnZ9UfctisN-LmXAO-7H28Sb0g13ft_qN1M"
SHEET_META = "IA | QUERIES | GIACO"
EXPORT_URL = "https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={sheet}"

# Identificação do cliente/conta (usada só em textos/relatórios — não afeta o cruzamento de dados).
CLIENT_NAME = "Ingenium Advisers"
MAIN_PRODUCT = "Funil de Sessão Estratégica"
# Prefixo comum a TODAS as campanhas da conta (usado para agrupar campanhas no
# dashboard, sem filtrar por sub-funil/etapa — ex. campanhas "E2-CAP" continuam
# entrando normalmente, só o prefixo "IA" é exigido).
MAIN_PRODUCT_PREFIX = "IA"

BRT = timezone(timedelta(hours=-3))   # horario de Brasilia (exibicao)
TAX_FACTOR = 1.1385   # imposto de 13,85% sobre o gasto de mídia (Meta Ads)

# --------------------------------------------------------------------------- #
# Regras da aba Relatório (Top/Piores anúncios)
# --------------------------------------------------------------------------- #
# Amostra mínima para julgar um anúncio como "vencedor" ou "ruim". Abaixo disso
# ele entra como "Em observação" (dado insuficiente) — nunca é classificado só
# porque teve 1 resultado com pouco investimento. Ajuste conforme o ticket/CAC.
SAMPLE_MIN_SPEND = 100.0   # gasto mínimo (R$) para amostra relevante
SAMPLE_MIN_MQLS = 3        # MQLs mínimos para julgar qualidade profunda
TOP_ADS_N = 10             # nº de linhas em Top / Piores anúncios

# Metas & parâmetros da conta (DEFAULTS do painel editável da aba Relatório).
# São só o valor inicial: o usuário edita no navegador (persistido em
# localStorage) e as tabelas de anúncios recoram CPMQL/CAC e reavaliam a
# amostra ao vivo. None = "meta não definida" (métrica aparece sem cor até o
# gestor preencher).
META_CPMQL = None          # meta de CPMQL (R$/MQL); None = não definida
META_CAC = None            # meta de CAC (R$/venda); None = não definida
VOLUME_MIN_AMOSTRAL = SAMPLE_MIN_MQLS  # conversões (MQLs) mínimas p/ amostra confiável
N_DIAS_CORTE = 5           # dias consecutivos acima do teto p/ considerar corte


# --------------------------------------------------------------------------- #
# Leitura
# --------------------------------------------------------------------------- #
def fetch_csv(url: str) -> list[list[str]]:
    req = urllib.request.Request(url, headers={"User-Agent": "dash-ingenium-bot/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return list(csv.reader(io.StringIO(raw)))


def read_csv_file(path: str) -> list[list[str]]:
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.reader(f))


def load_rows(url: str, local: str | None) -> list[list[str]]:
    return read_csv_file(local) if local else fetch_csv(url)


def sheet_url(sid: str, sheet: str) -> str:
    return EXPORT_URL.format(sid=sid, sheet=urllib.parse.quote(sheet))


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s: str | None) -> str:
    return strip_accents((s or "").strip().lower())


def to_float(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d,.\-]", "", str(v).strip())
    if not s:
        return 0.0
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_date(v: str) -> str | None:
    if not v:
        return None
    s = str(v).strip()
    if not s:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%d/%m/%y", "%b %d, %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_date_brt(v: str) -> str | None:
    """Como parse_date(), mas para timestamps COM FUSO (ISO-8601, ex.
    "2026-09-01T01:25:15+00:00" ou terminado em "Z") — CONVERTE para o fuso de
    Brasília (BRT, UTC-3) antes de extrair a data. Essencial pra bater com o
    Meta Ads, que reporta "Day" no fuso local da conta (BRT): um lead/venda
    registrado às 23h de um dia em BRT já é madrugada do dia seguinte em UTC,
    e sem essa conversão ele "vaza" pro dia errado (e pro período errado nos
    filtros). Strings sem hora/fuso (datas puras, ex. o "Day" do Meta) não têm
    o que converter — cai no parse_date() normal."""
    if not v:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            return dt.astimezone(BRT).strftime("%Y-%m-%d")
    except ValueError:
        pass
    return parse_date(s)


def is_test_lead(rowtext: str) -> bool:
    return "<test lead" in rowtext.lower()


def is_yes(v: str | None) -> bool:
    return norm(v) in ("sim", "s", "yes", "true", "1")


def is_qualificado(v: str | None) -> bool:
    """Critério de MQL (V1 e V2): faturamento acima de R$ 200 mil.
    Não depende do texto exato da faixa (V1 "de_r$_200.000,00_a_...",
    V2 "até_r$_200_mil", ...): vazio ou começando com "até" (sem acento) =
    não qualificado; qualquer outra faixa com número = MQL. Lead de teste da
    Meta ("<test lead ...>") nunca conta."""
    n = norm(v)
    if not n or is_test_lead(n) or n.startswith("ate"):
        return False
    return bool(re.search(r"\d", n))


FAIXA_LABELS = {
    "ate_r$_200.000,00": "Até R$ 200 mil",
    "de_r$_200.000,00_a_r$_500.000,00": "R$ 200 mil a R$ 500 mil",
    "acima_de_r$_500.000,00": "Acima de R$ 500 mil",
}


def pretty_faixa(v: str) -> str:
    s = (v or "").strip()
    if not s:
        return "Sem resposta"
    if norm(s) in FAIXA_LABELS:
        return FAIXA_LABELS[norm(s)]
    # Faixa fora do mapa (ex. V2 "até_r$_200_mil") -> "Até R$ 200 mil".
    s = re.sub(r"\s+", " ", s.replace("_", " ")).strip()
    s = re.sub(r"r\$", "R$", s, flags=re.I)
    return s[:1].upper() + s[1:]


def pretty_bucket(v: str) -> str:
    s = (v or "").strip()
    return s if s else "Sem resposta"


def mask_email(e: str) -> str:
    e = (e or "").strip()
    if "@" not in e:
        return "—"
    user, dom = e.split("@", 1)
    keep = user[:2] if len(user) > 2 else user[:1]
    return f"{keep}****@{dom}"


def mask_phone(p: str) -> str:
    digits = re.sub(r"\D", "", p or "")
    return f"…{digits[-4:]}" if len(digits) >= 4 else "—"


def norm_phone(p: str) -> str:
    return re.sub(r"\D", "", p or "")


def canon_phone(p: str) -> str:
    """Chave CANÔNICA de telefone p/ cruzar Vendas × Leads (fallback quando não
    há lead_id), robusta às 2 variações que fariam o mesmo número não bater
    quando comparado só por dígitos (norm_phone):
      - DDI "55" presente de um lado e ausente do outro
        (5511988887777 vs 11988887777);
      - 9º dígito do celular presente/ausente
        (11988887777 vs 1188887777).
    Estratégia: remove o DDI 55 (quando sobra DDD+número) e usa DDD (2 díg.) +
    ÚLTIMOS 8 DÍGITOS — que é o mesmo com ou sem o 9. Devolve chave de 10 díg.
    (DDD+8). Números curtos/estrangeiros (< 10 díg. após limpar) voltam como
    estão, pra não colidir à toa."""
    d = norm_phone(p)
    if len(d) > 11 and d.startswith("55"):
        d = d[2:]            # tira DDI do Brasil, sobrando DDD + local
    if len(d) >= 10:
        return d[:2] + d[-8:]   # DDD + últimos 8 (drop do 9º dígito, se houver)
    return d


def first_last_initial(name: str) -> str:
    parts = (name or "").strip().split()
    if not parts:
        return "—"
    return parts[0] if len(parts) == 1 else f"{parts[0]} {parts[-1][:1]}."


def valid_utm(campaign: str) -> bool:
    c = norm(campaign)
    return bool(c) and c not in ("-", "—", "nao encontrado")


# --------------------------------------------------------------------------- #
# Indexacao das colunas
# --------------------------------------------------------------------------- #
def header_index(header, wanted, fallback):
    """Casa cada alias com uma coluna do cabeçalho. Exact match tem prioridade
    sobre substring match (evita, por ex., o alias "pago" casar com a coluna
    "pago_em" antes de chegar na coluna "pago" de fato)."""
    idx = {}
    hn = [norm(h) for h in header]
    for key, aliases in wanted.items():
        norm_aliases = [norm(a) for a in aliases]
        found = None
        for a in norm_aliases:
            for i, h in enumerate(hn):
                if h == a:
                    found = i
                    break
            if found is not None:
                break
        if found is None:
            for a in norm_aliases:
                if not a:
                    continue
                for i, h in enumerate(hn):
                    if a in h:
                        found = i
                        break
                if found is not None:
                    break
        idx[key] = found if found is not None else fallback.get(key)
    return idx


def cell(row, i):
    if i is None or i < 0 or i >= len(row):
        return ""
    return (row[i] or "").strip()


# --------------------------------------------------------------------------- #
# Leads: varias abas (1 por formulario) -> tabela unica com cabecalho canonico
# --------------------------------------------------------------------------- #
# Coluna canonica -> nomes aceitos no cabecalho de cada aba (normalizados, sem
# acento). Casa por igualdade e, na falta, por PREFIXO — nunca por substring,
# para a pergunta de faturamento do V2 nao cair em "qual_foi_o_seu_faturamento
# _do_ano_anterior?" (outra pergunta, ignorada).
LEADS_CANON = {
    "id": ["id"],
    "created_time": ["created_time"],
    "campaign_name": ["campaign_name"],
    "adset_name": ["adset_name"],
    "ad_name": ["ad_name"],
    "platform": ["platform"],
    "form_name": ["form_name"],
    "phone_number": ["phone_number"],
    "nome": ["nome_completo", "full_name"],                      # V1, V2
    "faturamento": ["qual_e_o_faturamento_anual", "qual_e_o_seu_faturamento"],  # V1, V2 (coluna M)
}


def canon_index(header: list[str]) -> dict[str, int | None]:
    hn = [norm(h) for h in header]
    idx = {}
    for key, names in LEADS_CANON.items():
        found = next((hn.index(norm(n)) for n in names if norm(n) in hn), None)
        if found is None:
            found = next((i for n in names for i, h in enumerate(hn) if h.startswith(norm(n))), None)
        idx[key] = found
    return idx


def load_leads(sources: list[tuple[str, list[list[str]]]]) -> list[list[str]]:
    """Junta as abas de leads numa tabela só (cabeçalho = LEADS_CANON), cada
    aba mapeada pelo PRÓPRIO cabeçalho. Remove leads de teste da Meta e
    duplicados pelo id (mantém a 1ª ocorrência) — isso também neutraliza o
    gviz devolvendo a 1ª aba quando o nome pedido não existe."""
    header = list(LEADS_CANON)
    out = [header]
    seen = set()
    for name, rows in sources:
        if not rows:
            print(f"  AVISO: aba de leads '{name}' vazia — ignorada", file=sys.stderr)
            continue
        idx = canon_index(rows[0])
        missing = [k for k in ("id", "created_time", "faturamento") if idx[k] is None]
        if missing:
            print(f"  AVISO: aba de leads '{name}' sem coluna(s) {missing}", file=sys.stderr)
        kept = dup = test = 0
        for row in rows[1:]:
            if not any((c or "").strip() for c in row):
                continue
            if is_test_lead(" ".join(str(c) for c in row)):
                test += 1
                continue
            lead_id = cell(row, idx["id"])
            if lead_id and lead_id in seen:
                dup += 1
                continue
            if lead_id:
                seen.add(lead_id)
            out.append([cell(row, idx[k]) for k in header])
            kept += 1
        print(f"  leads aba '{name}': {kept} (duplicados ignorados: {dup}, teste: {test})", file=sys.stderr)
    return out


# --------------------------------------------------------------------------- #
# Vendas -> lista de compras (uma entrada por linha, nunca agregada)
# --------------------------------------------------------------------------- #
def build_purchases(sales_rows):
    """Lê a aba Vendas e devolve uma lista de compras CONFIRMADAS (pago == "sim"),
    uma entrada por linha: [{"lead_id","phone","d","fat","receita","nm"}, ...].
    Mantemos cada compra separada — com sua própria data ("pago_em") — pra
    atribuir a venda ao dia em que ela REALMENTE aconteceu, em vez de empilhar
    o histórico de um lead/telefone num único dia."""
    header = sales_rows[0] if sales_rows else []
    idx = header_index(
        header,
        {"lead_id": ["lead_id"], "phone": ["whatsapp", "telefone"], "date": ["pago_em", "data"],
         "valor": ["valor", "faturamento"], "name": ["comprador", "nome"], "pago": ["pago", "status"]},
        {"lead_id": 12, "phone": 6, "date": 1, "valor": 7, "name": 4, "pago": 3},
    )
    out = []
    for row in sales_rows[1:]:
        if not any((c or "").strip() for c in row):
            continue
        if not is_yes(cell(row, idx["pago"])):
            continue
        valor = to_float(cell(row, idx["valor"]))
        out.append({
            "lead_id": cell(row, idx["lead_id"]),
            "phone": norm_phone(cell(row, idx["phone"])),
            "d": parse_date_brt(cell(row, idx["date"])),
            "fat": valor,
            "receita": valor,
            "nm": cell(row, idx["name"]),
        })
    return out


def log_unmatched_sales(matched: int, total: int, unmatched: list[dict]):
    """Diagnóstico (stderr, não afeta a saída): compras da aba Vendas cujo
    lead_id não bate com nenhum lead E cujo telefone (canonicalizado) também
    não bate com nenhum lead da aba Leads. Essas vendas NÃO entram na dash
    (nem nos totais, nem na Visão Geral) — provavelmente compra de outro
    produto/origem que também cai na aba Vendas. Este log serve pra conferir
    quanto fica de fora e detectar lead_id/telefone genuinamente divergente
    (que deveria ter casado e não casou)."""
    print(f"  vendas atribuídas a anúncio: {matched}/{total} (cruzamento lead_id + telefone canônico Vendas × Leads)",
          file=sys.stderr)
    if not unmatched:
        return
    print(f"  {len(unmatched)} compra(s) SEM lead correspondente — EXCLUÍDAS da dash (fora deste funil):",
          file=sys.stderr)
    for p in unmatched:
        ph = p["phone"]
        print(f"    - {p['d'] or '?'}  {first_last_initial(p['nm'])}  tel …{ph[-4:] if len(ph) >= 4 else ph}",
              file=sys.stderr)


# --------------------------------------------------------------------------- #
# Processamento -> registros brutos
# --------------------------------------------------------------------------- #
def process(leads_rows, meta_rows, sales_rows):
    lheader = leads_rows[0] if leads_rows else []
    lidx = header_index(
        lheader,
        {"id": ["id"], "created": ["created_time"], "phone": ["phone_number"], "name": ["nome"],
         "qualif": ["faturamento"], "campaign": ["campaign_name"], "adset": ["adset_name"],
         "ad": ["ad_name"], "plat": ["platform"], "form": ["form_name"]},
        {k: i for i, k in enumerate(["id", "created", "campaign", "adset", "ad", "plat", "form",
                                     "phone", "name", "qualif"])},
    )

    leads = []
    # Atribuicao do ANUNCIO/campanha de uma venda: preferencialmente pelo
    # lead_id (chave direta Vendas.lead_id -> Leads.id); na ausencia, pelo 1o
    # lead (mais antigo) daquele telefone (mesma logica de "1a conversa" do
    # template generico, aqui aplicada sobre a propria aba Leads).
    rows_sorted = sorted(
        [r for r in leads_rows[1:] if any((c or "").strip() for c in r)],
        key=lambda r: parse_date_brt(cell(r, lidx["created"])) or "",
    )
    id_attrib: dict[str, dict] = {}
    phone_attrib: dict[str, dict] = {}
    for row in rows_sorted:
        if is_test_lead(" ".join(str(c) for c in row)):
            continue
        campaign_raw = cell(row, lidx["campaign"])
        campaign_valid = valid_utm(campaign_raw)
        src = "meta" if campaign_valid else "org"
        camp = campaign_raw if campaign_valid else "(sem campanha)"
        adset = cell(row, lidx["adset"]) if campaign_valid else "(sem conjunto)"
        ad = cell(row, lidx["ad"]) if campaign_valid else "(sem anúncio)"
        lead_date = parse_date_brt(cell(row, lidx["created"]))
        lead_id = cell(row, lidx["id"])
        phone = canon_phone(cell(row, lidx["phone"]))
        attrib = {"src": src, "camp": camp, "adset": adset, "ad": ad, "d": lead_date}
        if lead_id:
            id_attrib[lead_id] = attrib
        if phone and phone not in phone_attrib:
            phone_attrib[phone] = attrib
        bucket = pretty_faixa(cell(row, lidx["qualif"]))
        leads.append({
            "d": lead_date,
            "src": src,
            "plat": norm(cell(row, lidx["plat"])) or "—",
            "camp": camp,
            "adset": adset,
            "ad": ad,
            "prof": pretty_bucket(cell(row, lidx["form"])),
            "bucket": bucket,
            "q": 1 if is_qualificado(cell(row, lidx["qualif"])) else 0,
            "utm": 1 if campaign_valid else 0,
            "nm": first_last_initial(cell(row, lidx["name"])),
            "em": "—",
            "ph": mask_phone(cell(row, lidx["phone"])),
        })

    # Vendas: um registro POR COMPRA (nunca agregada), na data real da compra
    # ("pago_em"). Só entram vendas que casam com um lead deste funil — por
    # lead_id (FK direta) ou, na ausência, por telefone canônico. Uma venda
    # sem lead_id E sem telefone batendo não tem como ter vindo de um lead
    # capturado por este funil (decisão do cliente: a aba Vendas pode conter
    # compras de outras origens/produtos) — fica de fora da dash inteira, não
    # só da quebra por campanha do Meta. A aba Vendas em si nunca é alterada.
    purchases = build_purchases(sales_rows)
    sales = []
    matched = 0
    unmatched = []
    for p in purchases:
        attrib = id_attrib.get(p["lead_id"]) if p["lead_id"] else None
        if attrib is None:
            attrib = phone_attrib.get(canon_phone(p["phone"]))
        if attrib is None:
            unmatched.append(p)
            continue
        matched += 1
        sales.append({
            "d": p["d"] or attrib["d"],
            "src": attrib["src"],
            "camp": attrib["camp"],
            "adset": attrib["adset"],
            "ad": attrib["ad"],
            "vendas": 1,
            "fat": round(p["fat"], 2),
            "receita": round(p["receita"], 2),
        })

    log_unmatched_sales(matched, len(purchases), unmatched)

    mheader = meta_rows[0] if meta_rows else []
    midx = header_index(
        mheader,
        {"day": ["day", "data"], "campaign": ["campaign name", "campaign"], "adset": ["ad set name", "adset"],
         "ad": ["ad name"], "spent": ["amount spent", "valor gasto", "gasto"], "impr": ["impressions", "impress"],
         "clicks": ["link clicks", "clicks", "cliques"], "leads": ["leads"],
         "pv": ["landing page views", "page views", "pageviews"],
         # Conta não tem "Adds to Cart"/"Initiate Checkout" no export atual —
         # fica 0/"-" até o cliente adicionar essa coluna na planilha do Meta.
         "chk": ["adds to cart", "add to cart", "initiate checkout", "checkouts iniciados", "checkouts"],
         # Link do criativo — coluna opcional, ainda não existe no export do
         # cliente. Sem ela, o Link nas tabelas Top/Piores vira "—".
         "link": ["creative instagram permalink", "instagram permalink", "permalink",
                  "creative link", "link do anuncio", "link do criativo"]},
        {"day": 0, "campaign": 1, "adset": 2, "ad": 3, "spent": 4, "impr": 5, "clicks": 6, "leads": None, "pv": None},
    )

    meta = []
    # Anúncio (nome) -> 1 permalink do criativo, quando existir a coluna.
    ad_links = {}
    for row in meta_rows[1:]:
        if not any((c or "").strip() for c in row):
            continue
        ad = cell(row, midx["ad"]) or "(sem anúncio)"
        link = cell(row, midx["link"])
        if link and ad not in ad_links:
            ad_links[ad] = link
        meta.append({
            "d": parse_date(cell(row, midx["day"])),
            "camp": cell(row, midx["campaign"]) or "(sem campanha)",
            "adset": cell(row, midx["adset"]) or "(sem conjunto)",
            "ad": ad,
            "sp": round(to_float(cell(row, midx["spent"])), 4),
            "im": to_float(cell(row, midx["impr"])),
            "cl": to_float(cell(row, midx["clicks"])),
            "pv": to_float(cell(row, midx["pv"])),
            "ck": to_float(cell(row, midx["chk"])),
            "ml": to_float(cell(row, midx["leads"])),
        })

    dates = sorted({d for d in (
        [l["d"] for l in leads if l["d"]] + [m["d"] for m in meta if m["d"]] + [s["d"] for s in sales if s["d"]]
    )})
    now_brt = datetime.now(BRT)
    return {
        "build": {
            "generated_at_brt": now_brt.strftime("%d/%m/%Y %H:%M"),
            "build_id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
            "today": now_brt.strftime("%Y-%m-%d"),
            "date_min": dates[0] if dates else None,
            "date_max": dates[-1] if dates else None,
            "tax_factor": TAX_FACTOR,
            # config da aba Relatório (lida pelo front)
            "sample_min_spend": SAMPLE_MIN_SPEND,
            "sample_min_mqls": SAMPLE_MIN_MQLS,
            "top_ads_n": TOP_ADS_N,
            # metas & parâmetros (defaults do painel editável; None = não definida)
            "meta_cpmql": META_CPMQL,
            "meta_cac": META_CAC,
            "volume_min_amostral": VOLUME_MIN_AMOSTRAL,
            "n_dias_corte": N_DIAS_CORTE,
        },
        "leads": leads,
        "meta": meta,
        "sales": sales,
        # Anúncio -> permalink do criativo (aba Relatório).
        "ad_links": ad_links,
    }


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #
def render(data, template_path):
    # A dashboard e montada a partir de arquivos separados (visual x logica):
    #   template.html          -> esqueleto HTML (placeholders __STYLES__/__APP_JS__)
    #   identidade-visual.css  -> TODAS as cores (edite aqui p/ mexer so em cor)
    #   estilos.css            -> layout/componentes
    #   app.js                 -> logica + renderizacao
    # Esta funcao so COSTURA os arquivos e injeta os dados; nao altera nada deles.
    base = os.path.dirname(os.path.abspath(template_path))

    def readf(name):
        with open(os.path.join(base, name), "r", encoding="utf-8") as f:
            return f.read()

    with open(template_path, "r", encoding="utf-8") as f:
        tpl = f.read()
    styles = readf("identidade-visual.css") + "\n" + readf("estilos.css")
    tpl = tpl.replace("__STYLES__", styles)
    tpl = tpl.replace("__APP_JS__", readf("app.js"))
    tpl = tpl.replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False))
    tpl = tpl.replace("__BUILD_ID__", data["build"]["build_id"])
    tpl = tpl.replace("__GENERATED_BRT__", data["build"]["generated_at_brt"])
    return tpl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leads-file", action="append",
                    help="CSV local de uma aba de leads (repita: 1 por aba, ex. Lead Ads e IA | FORM-01 [V2])")
    ap.add_argument("--meta-file", help="CSV local da aba IA | QUERIES | GIACO (Meta Ads)")
    ap.add_argument("--sales-file", help="CSV local da aba Vendas (Compradores)")
    ap.add_argument("--template", default="build/template.html")
    ap.add_argument("--out", default="dist/index.html")
    args = ap.parse_args()

    if args.leads_file:
        sources = [(path, read_csv_file(path)) for path in args.leads_file]
    else:
        sources = []
        for sheet in SHEETS_LEADS:
            try:
                sources.append((sheet, fetch_csv(sheet_url(SPREADSHEET_ID_LEADS, sheet))))
            except Exception as e:   # uma aba fora do ar não derruba o build
                print(f"  AVISO: falha ao carregar aba de leads '{sheet}': {e}", file=sys.stderr)
        if not sources:
            sys.exit("ERRO: nenhuma aba de leads pôde ser carregada")
    leads_rows = load_leads(sources)
    # Vendas: mockup até a planilha de Compradores ser conectada.
    if args.sales_file or SPREADSHEET_ID_VENDAS:
        sales_rows = load_rows(sheet_url(SPREADSHEET_ID_VENDAS or "", SHEET_VENDAS), args.sales_file)
    else:
        sales_rows = []
    meta_rows = load_rows(sheet_url(SPREADSHEET_ID_META, SHEET_META), args.meta_file)

    data = process(leads_rows, meta_rows, sales_rows)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(render(data, args.template))

    b = data["build"]
    q = sum(l["q"] for l in data["leads"])
    vd = sum(s["vendas"] for s in data["sales"])
    fat = sum(s["fat"] for s in data["sales"])
    print("== build ok ==", file=sys.stderr)
    print(f"  periodo   : {b['date_min']} -> {b['date_max']}", file=sys.stderr)
    print(f"  leads     : {len(data['leads'])}  MQLs (qualificados): {q}", file=sys.stderr)
    print(f"  vendas    : {vd}  faturamento: R$ {fat:,.2f}", file=sys.stderr)
    print(f"  meta      : {len(data['meta'])} linhas", file=sys.stderr)
    print(f"  out       : {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
