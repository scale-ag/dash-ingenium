# AGENTS.md — Dashboard de captação de leads · Ingenium Advisers (IA)

> Contexto completo em **`CLAUDE.md`** — leia-o antes de mexer no projeto.

- Repositório `scale-ag/dash-ingenium` · Pages `https://scale-ag.github.io/dash-ingenium/`.
- **`build/build.py`**: `SPREADSHEET_ID_LEADS` (abas "Lead Ads" + "IA | FORM-01 [V2]"), `SPREADSHEET_ID_META`
  (aba "IA | QUERIES | GIACO"), `SPREADSHEET_ID_VENDAS = None` (mockup), `CLIENT_NAME = "Ingenium Advisers"`,
  `MAIN_PRODUCT = "Funil de Sessão Estratégica"`, `MAIN_PRODUCT_PREFIX = "IA"`, `TAX_FACTOR = 1.1385`.
- **MQL:** coluna M (faturamento, V1 e V2) acima de R$ 200 mil — vazio/"até…" = não; outra faixa com número = MQL.
- **Cruzamento:** `Campaign Name = campaign_name` · `Ad Set Name = adset_name` · `Ad Name = ad_name`.
- Front-end: `build/template.html` + `identidade-visual.css` + `estilos.css` + `app.js`.
- Sem Insights de Tráfego por IA (removidos a pedido do cliente).
- Somente leitura das planilhas — nunca escrever de volta.
