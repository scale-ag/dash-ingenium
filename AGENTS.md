# AGENTS.md — Dashboard de captura de leads · Lucas Nigro (RAL)

> Contexto completo em **`CLAUDE.md`** (mesma pasta) — leia-o antes de mexer no
> projeto. Este arquivo é um resumo para agentes/ferramentas que seguem a
> convenção `AGENTS.md`.
>
> Cliente já configurado (não é mais template genérico): repositório
> `scale-ag/dash-lucas-nigro-ral`, Pages em
> `https://scale-ag.github.io/dash-lucas-nigro-ral/`.

## Configuração deste cliente

1. **`build/build.py` — constantes do topo:** `SPREADSHEET_ID_FUNIL` (Leads +
   Vendas), `SPREADSHEET_ID_META` (Página 1), `CLIENT_NAME = "Lucas Nigro"`,
   `MAIN_PRODUCT = "Funil de Sessão Estratégica"`, `MAIN_PRODUCT_PREFIX = "RAL"`,
   `TAX_FACTOR = 1.0`.
2. **Critério de MQL:** `is_qualificado()` — coluna `classificacao` (aba Leads,
   coluna O) == `"QUALIFICADO"`.
3. **Cruzamento de dados:** por UTMs. A aba Leads já traz
   `utm_campaign`/`utm_medium`/`utm_content` = Campanha/Conjunto/Anúncio (nomes
   idênticos ao Meta Ads). Vendas cruza com Leads por `lead_id` (fallback por
   telefone canônico).
4. **`build/app.js`:** rótulos de MQL/qualificação já ajustados para "qualificado"
   (sem referência a "médico" — esse cliente não usa esse critério).
5. **`build/template.html`:** `<title>` e logo (`logo-main`="Lucas Nigro" /
   `logo-sub`="RAL") já preenchidos.
6. **`README.md` / `CLAUDE.md` / `SETUP-CRON.md`:** owner/repo, URL do Pages,
   spreadsheet IDs já preenchidos.
7. **`build/GUIA-RELATORIOS.md`:** contexto do funil já preenchido.
8. **GitHub Pages + Actions:** `build/` + `.github/workflows/deploy.yml` na
   `main` (ativa `workflow_dispatch`).
9. **cron-job.org:** seguir `SETUP-CRON.md` — token fine-grained novo (Actions:
   read/write, só neste repo), nunca reaproveitar um token exposto em chat.
10. **Insights de Tráfego (opcional):** `build/relatorios.json` e
    `build/relatorios_dados.json` começam vazios (`{}`). Ativar: deixar `briefing.yml`
    gerar os números + criar a **Routine do Claude** (`create_trigger` apontando para
    este repo) que redige `relatorios.json` na `main`. **Não vem pronta** — precisa
    ser criada.

> **Fora do escopo:** não há Cloudflare Worker nem chamada paga à API da
> Anthropic. A automação de Insights é uma Routine agendada do Claude Code
> (item 10, opcional).

## Engine (não muda entre clientes)
`build/template.html`, `build/app.js`, `build/estilos.css`,
`.github/workflows/deploy.yml`, `.github/workflows/briefing.yml`,
`build/relatorio_lib.py`, `build/coletar_dados_relatorio.py`,
`build/gerar_relatorios.py`, `build/GUIA-INTERPRETACAO-METRICAS.md`,
`GUIA-REPLICACAO.md` — tabelas, filtros, gráficos, heatmap, tema claro/escuro,
coleta/redação dos Insights. Ver `GUIA-REPLICACAO.md` para os detalhes de
implementação (filtro cruzado, engine de tabela, gráficos Chart.js).

> `template.html` e `app.js` são engine, mas carregam o nome do cliente em pontos
> pontuais (título/logo e alguns rótulos de qualificação) — já preenchidos para
> este cliente.

## Específico do cliente (troca a cada replicação)
`build/build.py`, `build/identidade-visual.css` (cores, se aplicável),
`build/relatorios.json` + `build/relatorios_dados.json` (conteúdo — começam vazios),
`build/GUIA-RELATORIOS.md` (contexto do funil), `README.md`, `CLAUDE.md`,
`SETUP-CRON.md`.
