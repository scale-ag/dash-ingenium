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

Coluna **M** da aba Leads (`qual_é_o_faturamento_anual_da_sua_empres?_`):

| Valor | Classificação |
|---|---|
| `de_r$_200.000,00_a_r$_500.000,00` | **MQL** |
| `acima_de_r$_500.000,00` | **MQL** |
| `até_r$_200.000,00` | não qualificado |

Lógica em `build/build.py` → `MQL_FAIXAS` / `is_qualificado()`.

## Fontes de dados (somente leitura)

- **Leads** (`1Gw6XZSL8OG4VYs8rEP2_vHvYLhbT4uhJFBOlLRyBZIg`), aba **Lead Ads**:
  `id` · `created_time` · `ad_id` · `ad_name` · `adset_id` · `adset_name` ·
  `campaign_id` · `campaign_name` · `form_id` · `form_name` · `is_organic` ·
  `platform` · `qual_é_o_faturamento_anual_da_sua_empres?_` · `nome_completo` ·
  `email` · `phone_number` · `lead_status`
- **Meta Ads** (`1MhIiyKadHKOqCQ0l5zEOD2gB7FqI8TNJVOQZhxBhmLY`), aba **Lead Ads**:
  `Day` · `Campaign Name` · `Ad Set Name` · `Ad Name` · `Impressions` ·
  `Link Clicks` · `Amount Spent` (sem Landing Page Views → Page View/ConvLP ficam "-").
- **Compradores**: ainda não conectada — Vendas/CAC/Faturamento/ROAS aparecem como
  mockup ("sem dado"). Para ligar: preencher `SPREADSHEET_ID_VENDAS`/`SHEET_VENDAS`
  em `build/build.py`.

**Cruzamento Leads × Meta Ads:** `Campaign Name = campaign_name` ·
`Ad Set Name = adset_name` · `Ad Name = ad_name`.

**Imposto de mídia:** 13,85% (`TAX_FACTOR = 1.1385`), toggle "Imposto Meta" ligado por padrão.

## Rodar local

```bash
python build/build.py --leads-file leads.csv --meta-file meta.csv --out dist/index.html
```

Automação e cron-job.org: ver `SETUP-CRON.md`.
