# Dashboard de Captação de Leads · Ingenium Advisers

Dashboard **100% na nuvem** do **Funil de Sessão Estratégica** da **Ingenium
Advisers** (sigla de campanha **`IA`**). Cruza os leads do formulário nativo do
Meta (aba **Lead Ads** da planilha de Leads) com o gerenciador de anúncios
(aba **Lead Ads** da planilha Meta Ads), calcula os **Leads Qualificados (MQLs)**
e o custo de cada etapa (CPL, CPMQL, CAC), e se atualiza sozinho a cada ~30 min
(GitHub Actions → GitHub Pages, disparado pelo cron-job.org).

**URL pública:** `https://scale-ag.github.io/dash-ingenium/`

## Páginas

1. **Visão Geral de Leads** — funil vertical (Gasto → Impressões → Cliques → Leads →
   MQLs → Vendas/Faturamento), KPIs secundários, evolução diária, tabela diária com
   heatmap e distribuição de leads (origem · faixa de faturamento · plataforma · formulário).
2. **Captura Meta Ads** — funil de mídia, combinado diário, tabelas hierárquicas
   Campanha → Conjunto → Anúncio com filtro cruzado.
3. **Relatório** — espelho da Visão Geral + painel de metas editável + Top Anúncios.

## Critério de Lead Qualificado (MQL)

Vale para os **dois formulários**: faturamento **acima de R$ 200 mil** é MQL.
A coluna usada é a **M** de cada aba (V1: `qual_é_o_faturamento_anual_da_sua_empres?_`;
V2: `qual_é_o_seu_faturamento_mensal?` — a pergunta `qual_foi_o_seu_faturamento_do_ano_anterior?`
do V2 **não** é usada).

A regra não depende do texto exato da faixa (os forms usam formatos diferentes,
ex. V1 `até_r$_200.000,00` e V2 `até_r$_200_mil`):

| Valor (normalizado, sem acento) | Classificação |
|---|---|
| vazio ou começando com `até` | não qualificado |
| qualquer outra faixa com número (ex. `de_r$_200.000,00_a_r$_500.000,00`, `acima_de_r$_500.000,00`, `de_r$_200_mil_a_r$_500_mil`) | **MQL** |
| lead de teste da Meta (`<test lead ...>`) | nunca conta (excluído) |

Lógica em `build/build.py` → `is_qualificado()`.

## Fontes de dados (somente leitura)

- **Leads** (`1Gw6XZSL8OG4VYs8rEP2_vHvYLhbT4uhJFBOlLRyBZIg`), **duas abas**, uma por
  formulário (`SHEETS_LEADS` em `build/build.py`):
  - **Lead Ads** (form IA | FORM-01 [V1]): `id` · `created_time` · `ad_id` · `ad_name` ·
    `adset_id` · `adset_name` · `campaign_id` · `campaign_name` · `form_id` · `form_name` ·
    `is_organic` · `platform` · `qual_é_o_faturamento_anual_da_sua_empres?_` (M) ·
    `nome_completo` · `email` · `phone_number` · `lead_status`
  - **IA | FORM-01 [V2]**: mesmas colunas de atribuição/id/data/telefone, mas nome em
    `full_name` e faturamento em `qual_é_o_seu_faturamento_mensal?` (M); tem também
    `qual_foi_o_seu_faturamento_do_ano_anterior?`, dívidas e `whatsapp_number` (não usados).

  As duas abas são mapeadas pelo próprio cabeçalho para um cabeçalho canônico,
  unidas numa tabela só e **deduplicadas pelo `id` do lead** (protege também contra o
  export gviz devolver a 1ª aba quando o nome não existe). Se uma aba falhar ao carregar,
  o build loga um aviso e segue com a outra.
- **Meta Ads** (`1urfcE0E-FnZ9UfctisN-LmXAO-7H28Sb0g13ft_qN1M`), aba **IA | QUERIES | GIACO**:
  `Day` · `Campaign Name` · `Ad Set Name` · `Ad Name` · `Amount Spent` ·
  `Impressions` · `Link Clicks` · `Reach` (sem Landing Page Views → Page View/ConvLP ficam "-").
- **Compradores**: ainda não conectada — Vendas/CAC/Faturamento/ROAS aparecem como
  mockup ("sem dado"). Para ligar: preencher `SPREADSHEET_ID_VENDAS`/`SHEET_VENDAS`
  em `build/build.py`.

**Cruzamento Leads × Meta Ads:** `Campaign Name = campaign_name` ·
`Ad Set Name = adset_name` · `Ad Name = ad_name`.

**Imposto de mídia:** 13,85% (`TAX_FACTOR = 1.1385`), toggle "Imposto Meta" ligado por padrão.

## Rodar local

```bash
python build/build.py --leads-file lead_ads.csv --leads-file form_v2.csv --meta-file meta.csv --out dist/index.html
```

Automação e cron-job.org: ver `SETUP-CRON.md`.
