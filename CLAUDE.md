# CLAUDE.md — Contexto do projeto (Dashboard Ingenium Advisers · IA)

> Este arquivo é lido automaticamente pelo Claude Code ao abrir o repositório.
> Mantenha-o atualizado. Para replicar este modelo para outro cliente, veja
> `GUIA-REPLICACAO.md`.

---

## Status da configuração

- **Cliente:** Ingenium Advisers · **Funil:** Funil de Sessão Estratégica ·
  **Subtítulo:** Captação de Leads · **Sigla de campanha:** `IA`.
- **Repositório:** `scale-ag/dash-ingenium` · **URL pública:**
  `https://scale-ag.github.io/dash-ingenium/`.
- **`build/build.py`:** `SPREADSHEET_ID_LEADS`, `SPREADSHEET_ID_META`,
  `SPREADSHEET_ID_VENDAS = None` (mockup), `CLIENT_NAME`, `MAIN_PRODUCT`,
  `MAIN_PRODUCT_PREFIX = "IA"`, `TAX_FACTOR = 1.1385` (13,85%, toggle ligado por padrão).
- **Insights de Tráfego por IA:** **removidos** a pedido do cliente (sem
  `briefing.yml`, sem `relatorios*.json`, sem Routine).

## O que é

Dashboard de **Captação de Leads** — app de BI estático (HTML/CSS/JS puro +
Chart.js via CDN) publicado no **GitHub Pages**, que cruza os leads do formulário
nativo do Meta com o gerenciador de anúncios e se atualiza sozinho a cada ~30 min
(build 100% na nuvem via GitHub Actions, disparado pelo cron-job.org).
**Somente leitura** das planilhas. Nunca escrever de volta.

## Fontes de dados (Google Sheets, busca por NOME de aba)

**Leads** — `SPREADSHEET_ID_LEADS = "1Gw6XZSL8OG4VYs8rEP2_vHvYLhbT4uhJFBOlLRyBZIg"`, aba **"Lead Ads"**:
`id` · `created_time` · `ad_id` · `ad_name` · `adset_id` · `adset_name` · `campaign_id` ·
`campaign_name` · `form_id` · `form_name` · `is_organic` · `platform` (fb/ig/an) ·
`qual_é_o_faturamento_anual_da_sua_empres?_` (**coluna M**, MQL) · `nome_completo` ·
`email` · `phone_number` · `lead_status`

**Meta Ads** — `SPREADSHEET_ID_META = "1urfcE0E-FnZ9UfctisN-LmXAO-7H28Sb0g13ft_qN1M"`, aba **"IA | QUERIES | GIACO"**:
`Day` · `Campaign Name` · `Ad Set Name` · `Ad Name` · `Amount Spent` · `Impressions` · `Link Clicks` · `Reach`

**Compradores** — ainda não conectada (`SPREADSHEET_ID_VENDAS = None`). `build_purchases()`
continua pronto (colunas esperadas: `lead_id`/`whatsapp`/`pago_em`/`valor`/`comprador`/`pago`).

### Regra de MQL
Coluna M ∈ {`de_r$_200.000,00_a_r$_500.000,00`, `acima_de_r$_500.000,00`} → MQL;
`até_r$_200.000,00` → não qualificado. `build.py` → `MQL_FAIXAS`/`is_qualificado()`.
O gráfico "Leads por faturamento anual" usa a mesma coluna (rótulos amigáveis em `FAIXA_LABELS`).

### Cruzamento Leads × Meta Ads
`Campaign Name = campaign_name` · `Ad Set Name = adset_name` · `Ad Name = ad_name`
(valores idênticos linha a linha). `created_time` (ISO com fuso) é convertido para BRT.

## Arquitetura / arquivos

```
build/build.py               # lê os CSVs (read-only), emite registros brutos; render() costura os arquivos abaixo
build/template.html          # esqueleto HTML (placeholders __STYLES__, __APP_JS__, __DATA_JSON__, __BUILD_ID__, __GENERATED_BRT__)
build/identidade-visual.css  # cores (tema claro/escuro)
build/estilos.css            # layout/componentes
build/app.js                 # lógica + renderização (tudo client-side)
.github/workflows/deploy.yml # build + publica no Pages (workflow_dispatch + schedule + push em build/**)
dist/index.html              # saída gerada (gitignored)
SETUP-CRON.md                # valores do cron-job.org
```

> **Layout modular:** o front-end é separado em `identidade-visual.css` + `estilos.css`
> + `app.js`, costurados por `render()` nos placeholders `__STYLES__`/`__APP_JS__`.
> Página 1 usa **funil vertical de leads** + KPIs secundários. Topbar tem
> **seletor de período em calendário** (default "Este mês"). **Heatmap** = cor FIXA
> por métrica (só opacidade varia): **Gasto=vermelho · Leads=azul · MQLs=ciano ·
> Vendas=verde · ROAS=amarelo** (`--heat-gasto/leads/mqls/vendas/roas`).

O `build.py` **não agrega**: exporta as linhas cruas e TODA a lógica (filtros de
data, filtro cruzado, KPIs, tabelas, gráficos, heatmap, imposto) roda no navegador.

## Rodar/testar local

```bash
python build/build.py --leads-file leads.csv --meta-file meta.csv --out dist/index.html
# (o sandbox do agente NÃO alcança docs.google.com; use CSVs locais para testar.
#  O runner do GitHub Actions tem internet e busca os CSVs ao vivo.)
```

## Especificação funcional (resumo)

Três **páginas separadas** (sidebar):
1. **Visão Geral de Leads** — funil vertical (Gasto → Impressões → Cliques → Leads →
   MQLs → Vendas/Faturamento) + KPIs secundários; gráfico combinado diário +
   tabela diária com heatmap (todos os leads); barras por origem/faixa/plataforma/profissão.
2. **Captura mídia paga** — funil em etapas; combinado diário; barras por utm_content;
   tabela diária com heatmap (só mídia paga); 3 tabelas hierárquicas Campanha →
   Conjunto → Anúncio, cada uma com gráfico de linha embaixo.
3. **Relatório** — espelha a Visão Geral + painel de Metas editável + Top Anúncios.

**Ordem das colunas nas tabelas:** `Data · Dia · Gasto · CPM · CTR · ConvForm · Leads ·
CPL · Tx‑MQL · MQLs · CPMQL · ConvMQL · Vendas · CAC · Fat. · Receita · ROAS`. Nas
tabelas diárias entram também **Checkouts** e **VisCHK** (da coluna "Adds to Cart"
do Meta Ads, proxy de Checkout). Sem essas colunas, ficam "-".

**Regras obrigatórias das tabelas** (ver `GUIA-REPLICACAO.md`): cabeçalho sticky;
ordenação tri‑state; colunas redimensionáveis (persist localStorage); linha
"Total Geral" fixa; dimensão nunca truncada; seleção com toggle + Ctrl multi;
filtro cruzado bidirecional; tabela diária com último dia no topo; heatmap de cor
fixa por métrica.

## Lacunas de dados
- **Compradores/Vendas** → planilha ainda não enviada pelo cliente; Vendas/CAC/
  Faturamento/ROAS aparecem como mockup ("sem dado"). Ligar: `SPREADSHEET_ID_VENDAS`.
- **Landing Page Views** → não existe no export Meta (formulário nativo, sem LP);
  Page View/Connect Rate/ConvLP/CPV ficam "-".
- **Agendamentos** → sem fonte conectada.

## Publicação — problemas conhecidos
1. **Push:** se a integração GitHub da sessão for somente‑leitura (403), o caminho
   é `git push` direto para `github.com` com o **PAT do usuário**. Nunca gravar o
   token no `.git/config` (usar URL efêmera `https://x-access-token:<TOKEN>@github.com/...`).
2. **cron-job.org só funciona na `main`:** `workflow_dispatch` só existe na branch
   padrão. Levar `build/` + `.github/workflows/deploy.yml` para a `main`.
3. **Pages liga sozinho:** `actions/configure-pages@v5` com `enablement: true`
   (precisa `permissions: pages: write, id-token: write`).
4. **Proxy do sandbox:** o ambiente do agente costuma NÃO alcançar `docs.google.com`,
   `*.github.io` nem a API REST de Actions/Pages — mas o runner do Actions alcança tudo.
5. **Token exposto:** se um token foi colado no chat, **revogar e gerar um novo**.

## Branch / git
- Desenvolvimento na branch designada da sessão; manter sincronizada com `main`.
