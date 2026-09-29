# GUIA — Insights de Tráfego da aba Relatório

> Texto lido de `build/relatorios.json` pela aba **Relatório** (seção
> "Insights de Tráfego"). **Não faz nenhuma chamada de API no build nem no
> navegador** — a página só exibe o texto já pronto. Os números vêm dos
> mesmos dados do site (mídia paga × Leads × Vendas); quem escreve o texto
> (hoje, uma Routine do Claude — ver seção abaixo) apenas **interpreta e
> redige**, nunca recalcula.
>
> **Este guia define o FORMATO/estrutura do texto.** As regras de
> **diagnóstico** (como interpretar cada métrica, quando um número ruim não
> é problema, o que analisar junto do quê) estão em
> `build/GUIA-INTERPRETACAO-METRICAS.md` — leitura obrigatória antes de
> redigir.

## Modelo: 1 análise por dia, não por período selecionado

Diferente do resto da dashboard (que reage ao seletor de período da
topbar), a seção **Insights de Tráfego** é **uma única análise estática por
dia**, gerada no fechamento do dia (23h59 BRT) sobre os dados já
consolidados daquele dia — e fica salva até a próxima atualização. Ela
**não muda** quando o usuário troca o período selecionado no resto da
página. Não é preciso nenhuma chamada de API em tempo real no navegador.

## Como `build/relatorios.json` é gerado (pipeline: Routine do Claude)

`build/relatorios.json` é escrito 1×/dia às **23:59 BRT** por uma **Routine
do Claude** (Claude Code Remote), não por uma chamada paga à API da
Anthropic — é a mesma infraestrutura de sessão/agente deste repositório, só
agendada. O fluxo tem 2 etapas, porque o ambiente onde a Routine roda não
alcança `docs.google.com` (só o runner do GitHub Actions alcança):

1. **Coleta de números (determinística, GitHub Actions)** —
   `build/coletar_dados_relatorio.py` lê os CSVs (mídia paga × Leads ×
   Vendas) e agrega **só aritmética** em `build/relatorios_dados.json`: os
   números do dia (`hoje`), as janelas rolantes de 7/14/30 dias
   (`janelas`), o acumulado desde o início da conta (`acumulado_total`, base
   da fase de calibração), a quebra por campanha e por conjunto do dia
   (`por_campanha`/`por_conjunto`, já marcada com `abaixo_minimo`), e as
   flags de fonte conectada (`fontes_conectadas`). Roda via
   `.github/workflows/briefing.yml` (1×/dia, 23:50 BRT, +
   `workflow_dispatch` manual) e commita direto na `main`. **Não é lido pelo
   site** — é só insumo intermediário, mas faz TODA a aritmética pesada
   pra Routine não precisar recalcular nada.
2. **Redação dos Insights (Claude, Routine agendada)** — 9 minutos depois,
   uma sessão do Claude lê `build/relatorios_dados.json` (números JÁ
   CALCULADOS — a sessão não deve recalcular soma/média/variação, só
   interpretar) + `build/GUIA-RELATORIOS.md` (este arquivo, formato) +
   `build/GUIA-INTERPRETACAO-METRICAS.md` (diagnóstico por métrica, funil,
   fase de calibração) e escreve `build/relatorios.json` no formato de **6
   seções** descrito abaixo, fazendo commit/push direto na `main` — o que
   dispara o `deploy.yml` e republica o dashboard.

Testar a coleta de números manualmente:

```bash
python build/coletar_dados_relatorio.py --leads-file leads.csv --meta-file meta.csv --sales-file vendas.csv --out build/relatorios_dados.json
```

`build/gerar_relatorios.py` (gerador **determinístico**, sem IA, mais raso)
continua no repo como **fallback manual** — não roda automaticamente. Se a
Routine falhar num dia, rode-o pra garantir que a seção não fique vazia:

```bash
python build/gerar_relatorios.py --leads-file leads.csv --meta-file meta.csv --sales-file vendas.csv --out build/relatorios.json
```

`build/relatorios.json` também pode ser editado à mão seguindo o mesmo
formato — o build só lê o arquivo, não importa como foi gerado. Se o
arquivo não existir ou vier vazio, a seção mostra uma mensagem dizendo que
os insights ainda não foram gerados (o resto da aba — funil, KPIs,
gráficos, Top/Piores Anúncios — segue funcionando normalmente).

## Contexto do funil

**Funil do Lucas Nigro** (captação de leads para a formação "Consultores
Financeiros Empresariais | Método RaL", via formulário de captura):

```
Impressões → Cliques → Page View → Leads → MQLs → Agendamentos → Vendas
```

- O anúncio no Meta Ads leva a uma landing page; a visita gera **Page View**
  (`Landing Page Views` do Meta Ads — já conectado, permite calcular Connect
  Rate e ConvLP).
- Ao preencher o formulário, o lead cai na aba **Leads** (fonte única de
  leads deste dashboard), já com campanha/conjunto/anúncio de origem via
  `utm_campaign`/`utm_medium`/`utm_content`.
- **MQL** = coluna `classificacao` (aba Leads) == `"QUALIFICADO"` — já
  automatizado no sistema, não precisa ser explicado nem recalculado.
- **Agendamento** acontece via **WhatsApp**, fora da mídia paga — **sem
  fonte de dado conectada** ao dashboard ainda. **Não existe etapa de
  comparecimento** nesse funil (o agendamento é direto por WhatsApp) — a
  **responsabilidade do tráfego termina no MQL**.
- **Venda** é registrada na aba **Vendas**, cruzada de volta ao anúncio de
  origem por `lead_id` (fallback por telefone) — **já conectada**.

> **Estado atual dos dados:** Impressões → Cliques → Page View → Leads →
> MQLs → Vendas estão todos conectados e cruzados. **Só Agendamentos não
> tem fonte conectada** — por isso Taxa de Agendamento e Custo por
> Agendamento aparecem "-", e Taxa de Vendas (que usa Agendamentos como
> denominador) também aparece "-" mesmo com o número absoluto de Vendas e o
> CAC disponíveis. Ver "Gargalo de dado" abaixo.

## Fórmulas fundamentais

- **CTR** = Cliques ÷ Impressões · **Connect Rate** = Page Views ÷ Cliques ·
  **ConvLP** = Leads ÷ Page Views
- **CPL** = Investimento ÷ Leads · **TxMQL** = MQLs ÷ Leads · **CPMQL** =
  Investimento ÷ MQLs
- **Taxa de Agendamento** = Agendamentos ÷ MQLs (hoje "-", sem fonte) ·
  **Custo por Agendamento** = Investimento ÷ Agendamentos (hoje "-")
- **Taxa de Vendas** = Vendas ÷ Agendamentos (hoje "-", denominador sem
  fonte) · **CAC** = Investimento ÷ Vendas (calculável — Vendas conectada)

Regra de ouro: **acumulativas somam** (impressões, cliques, page views,
leads, MQLs, gasto, vendas); **derivadas recalculam dos totais** (nunca some
percentuais).

## Princípio de interpretação

Trate cada métrica como **diagnóstico probabilístico**, nunca regra
absoluta. Leia **sempre** com a etapa anterior e a posterior, o histórico da
própria conta e o **volume da amostra**. As regras completas de diagnóstico
por métrica — incluindo quando um número ruim NÃO é problema — estão em
`build/GUIA-INTERPRETACAO-METRICAS.md`, leitura obrigatória antes de
redigir qualquer dia.

## Fase de calibração

Enquanto o **acumulado total de MQLs** (`acumulado_total.mqls` no JSON,
desde o início da conta) estiver abaixo do `params.volume_min_amostral`
configurado: **não compare contra médias históricas nem invente
tendência** — diga explicitamente, na seção RESUMO DO PERÍODO, que a conta
está em fase de calibração, quantos MQLs já acumulou e quantos faltam. Regra
completa em `GUIA-INTERPRETACAO-METRICAS.md`.

## Top Anúncios e Piores Anúncios (não faz parte do texto gerado por IA)

A aba Relatório calcula sozinha (client-side, `app.js`), acima da seção
Insights de Tráfego, as tabelas **Top Anúncios** e **Piores Anúncios** —
ranqueadas pelo resultado mais profundo disponível (hoje, MQL — Venda ainda
não é ranqueada por anúncio nessas tabelas), com amostra mínima
(`SAMPLE_MIN_SPEND`/`SAMPLE_MIN_MQLS` em `build.py`). O texto dos Insights
pode **citar** campanhas/conjuntos campeões (seção CLASSIFICAÇÃO POR
CAMPANHA/CONJUNTO), mas não precisa reexplicar como essas tabelas
funcionam.

## Formato "Insights de Tráfego" — 6 seções obrigatórias

> Tom: **gestor de tráfego experiente falando com outro gestor** — direto,
> escaneável, decisão no fim de cada seção, não descrição. **Texto corrido,
> sem tabelas.** Antes de redigir, leia por inteiro
> `build/GUIA-INTERPRETACAO-METRICAS.md` e aplique suas heurísticas: nunca
> julgue uma métrica isolada. Use os números JÁ CALCULADOS de
> `relatorios_dados.json` — não recalcule soma/média/variação/ranking, só
> interprete e redija.

Cada dia em `relatorios.json` (chave `hoje`, objeto único — não é mais
dividido por período) tem os seguintes campos, cada um uma string HTML
(tags permitidas: `<p> <ul> <li> <b>`):

### 1. RESUMO DO PERÍODO (`resumo_periodo`)

- Data do dia analisado, investimento do dia, leads, MQLs.
- **Fase de calibração:** se `calibracao.em_calibracao` for `true`, diga
  isso explicitamente (conta em fase de calibração, MQLs acumulados,
  quantos faltam para `params.volume_min_amostral`) **em vez de** comparar
  contra histórico. Se `false`, siga para o item seguinte.
- CPL do dia e comparação com o CPL das janelas de 7/14/30 dias
  (`janelas.7d/14d/30d`) — só quando fora da fase de calibração.
- TxMQL da janela de 7 dias (`janelas["7d"].txmql`).
- Metas: se `params.meta_cpmql`/`params.meta_cac` estiverem definidas,
  comparar o CPMQL/CAC do dia contra elas; se `null`, dizer explicitamente
  "meta não definida" (nunca comparar com benchmark de mercado nesse caso).
- Citar a amostra mínima configurada (`params.volume_min_amostral`).

### 2. LEITURA DO FUNIL (`leitura_funil`)

- Explicação da causa mais provável do resultado do dia, usando a base de
  conhecimento por métrica (`GUIA-INTERPRETACAO-METRICAS.md`) — sempre
  cruzando etapa anterior/posterior.
- Sinalizar explicitamente quando o resultado é **ruído por volume baixo**
  (dia com poucos leads/MQLs não sustenta conclusão de qualidade) e quanto
  falta, **em MQLs acumulados**, pra ter confiança na leitura
  (`calibracao.faltam`, ou a diferença entre `janelas["30d"].mqls` e o
  volume mínimo quando já fora da calibração mas ainda com amostra curta).
- Cite Connect Rate e ConvLP do dia (dados conectados via Page Views do
  Meta Ads) — não são "-", são parte normal da leitura.
- Onde Agendamentos/Taxa de Vendas aparecerem "-" na leitura, não invente
  número — remeta à seção GARGALO DE DADO.

### 3. CLASSIFICAÇÃO POR CAMPANHA/CONJUNTO (`classificacao_campanhas`)

- Lista os conjuntos/campanhas do dia (`por_campanha`/`por_conjunto` no
  JSON) com o volume de leads/MQLs de cada um.
- Sinaliza quais estão `abaixo_minimo: true` e reforça que **nenhuma
  decisão** deve ser tomada sobre eles ainda (nem "cortar", nem "escalar").
- Nomeie campanha/conjunto por inteiro, nunca abreviado.

### 4. GARGALO DE DADO — PRIORIDADE ALTA (`gargalo_dado`)

**Só inclua este campo no JSON quando existir uma fonte de dado
desconectada** (`fontes_conectadas` tiver algum `false`). Se todas as
fontes relevantes estiverem conectadas, **omita a chave** inteiramente (não
escreva `null` nem string vazia) — o front-end só mostra a seção quando a
chave existe.

Quando presente, explique:
- Qual dado está faltando (hoje: Agendamentos — `fontes_conectadas.agendamentos
  == false`).
- O impacto nas métricas dependentes: Taxa de Agendamento, Custo por
  Agendamento e Taxa de Vendas ficam "-" (CAC e Faturamento **não** são
  afetados — Vendas já está conectada).
- Qual é a ação de maior impacto pra resolver isso (conectar a lista/planilha
  do comercial com os agendamentos feitos via WhatsApp ao dashboard).

### 5. AÇÕES RECOMENDADAS (`acoes_recomendadas`)

- Se os dados forem insuficientes pra qualquer decisão (fase de calibração,
  ou dia sem investimento/atividade), diga isso claramente: **"sem ação,
  seguir tendência de X dias/MQLs"** — não force uma recomendação.
- Se houver dado suficiente, liste as ações concretas da base de
  conhecimento (`GUIA-INTERPRETACAO-METRICAS.md`), ligadas à etapa do funil
  identificada como gargalo real na seção 2. Cada ação cita a
  campanha/conjunto quando aplicável, nomeado por inteiro.

### 6. PRÓXIMA DECISÃO (`proxima_decisao`)

- Define um **gatilho objetivo** (condição numérica ou de tempo) que, se
  acontecer, deve disparar uma nova análise ou ação antes da próxima
  atualização diária (ex.: "se o CPL do dia passar de R$ X por 2 dias
  seguidos", "se os MQLs acumulados chegarem a Y").
- Define também o **prazo da próxima revisão programada** — sempre "próxima
  atualização diária, 23h59 BRT" neste dashboard, salvo gatilho antecipado.

## Rodapé fixo (gerado pelo sistema, não pela IA)

O front-end (`build/app.js`) monta sozinho, a partir de `generated_at`, a
linha:

```
Insights gerados por IA · última atualização {generated_at} · atualiza 1x/dia (23h59 BRT)
```

**Não inclua essa linha em nenhuma das 6 seções** — é gerada pelo sistema.

## Formato de `build/relatorios.json`

```json
{
  "generated_at": "DD/MM/AAAA HH:MM",
  "data_referencia": "YYYY-MM-DD",
  "fonte": "Insights de Tráfego redigidos pelo Claude (Routine diária, 23h59 BRT) a partir dos números agregados em relatorios_dados.json (mídia paga × Leads × Vendas).",
  "resumo_periodo": "<p>…</p>",
  "leitura_funil": "<p>…</p><ul>…</ul>",
  "classificacao_campanhas": "<p>…</p><ul>…</ul>",
  "gargalo_dado": "<p>…</p>",
  "acoes_recomendadas": "<p>…</p><ul>…</ul>",
  "proxima_decisao": "<p>…</p>"
}
```

- `gargalo_dado` é **opcional** — presente só quando alguma fonte relevante
  está desconectada (ver seção 4 acima).
- HTML permitido: `<p> <ul> <li> <b>` — **sem tabelas** (o formato pedido é
  texto corrido).
- Se não houver investimento/atividade no dia, as 6 seções ainda devem
  existir, mas dizendo isso claramente (ex.: `resumo_periodo`: "Sem
  investimento/atividade registrada hoje — nada a reportar."), sem inventar
  números.
- Se o arquivo não existir ou vier vazio (como no template), a seção mostra
  uma mensagem informativa e o resto da aba segue funcionando.
- **Formato antigo (obsoleto):** versões anteriores deste guia definiam um
  formato de 9 períodos × 4 quadrantes + bloco WhatsApp
  (`periodos.<chave>.quadro1_resumo` etc.). Esse formato foi **substituído**
  pelo formato de 6 seções acima (1 análise por dia, não por período) — não
  gere mais nesse formato antigo.

## Comparações e segurança analítica

- **Não invente** métricas/benchmarks; **não** trate ausência de dado como
  zero; **não** compare com benchmark de mercado sem meta configurada.
- **Não** recomende cortar/escalar campanha/conjunto com amostra
  insuficiente (`abaixo_minimo: true`).
- **Não** culpe o tráfego por perda que acontece depois do MQL (Agendamento
  em diante é responsabilidade comercial, via WhatsApp).
- Enquanto em fase de calibração, **não** compare contra histórico nem
  invente tendência — ver seção "Fase de calibração".

## Economia de tokens (leia antes de redigir)

Todo cálculo pesado já está feito em `relatorios_dados.json` (somas,
janelas de 7/14/30d, comparação de CPL, quebra por campanha/conjunto,
acumulado para calibração). A Routine **não deve**: recalcular
totais/variações, reprocessar CSVs, gerar HTML além das 6 seções + rodapé
fixo (gerado pelo sistema, não pela IA), ou repetir o mesmo número em seções
diferentes sem necessidade. Uma única leitura de `relatorios_dados.json` +
os 2 guias é suficiente pra escrever o dia — não é preciso reler os
documentos.
