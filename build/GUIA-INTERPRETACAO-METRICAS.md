# GUIA — Interpretação de Métricas do Funil (Lucas Nigro)

> Referência **durável** para quem redige os Insights de Tráfego (a Routine
> do Claude, ou qualquer pessoa preenchendo `build/relatorios.json` à mão).
> Como cada execução automática é uma sessão nova, sem memória da conversa
> que originou este guia, **este arquivo precisa ser lido por inteiro antes
> de redigir** — é aqui que moram as regras de diagnóstico, não só no
> `GUIA-RELATORIOS.md` (que define o formato/estrutura do texto).

## Funil do Lucas Nigro

```
Impressões → Cliques → Page View → Leads → MQLs → Agendamentos → Vendas
```

Não existe etapa de comparecimento nesse funil — o agendamento acontece via
**WhatsApp** (fora da mídia paga) e a **responsabilidade do tráfego termina
no lead qualificado (MQL)**. A classificação de MQL já é automatizada dentro
do sistema (coluna `classificacao` da aba Leads == `"QUALIFICADO"`) — não
precisa ser explicada nem recalculada pela IA.

A conta começou recentemente e ainda não tem histórico de volume
consolidado — ver "Fase de calibração" no fim deste guia.

A forma mais útil de interpretar este funil é tratar cada métrica como um
**diagnóstico probabilístico**, nunca uma regra absoluta. Uma métrica ruim
isolada raramente é, sozinha, o problema — **sempre olhar a etapa anterior e
a posterior junto**.

## CTR (Cliques ÷ Impressões)

**Objetivo:** avaliar se o anúncio gera interesse suficiente pra levar até a
landing page.

**Possíveis gargalos:** criativo pouco chamativo, gancho fraco, copy
genérica, promessa pouco clara, público inadequado, fadiga criativa,
frequência elevada, comunicação desalinhada com a dor do público
(contador/consultor/BPO).

**Ações:** criar novos ganchos, testar novas headlines, melhorar os
primeiros segundos do vídeo, testar novas promessas, renovar criativos
saturados, revisar segmentação, testar anúncios com maior especificidade
pro público.

**Quando NÃO é problema:** CTR baixo pode ser positivo se o anúncio é
qualificador e afasta curiosos — nesse caso a TxMQL segue alta e o CPMQL
saudável, mesmo com menos cliques.

**Cruzar com:** ConvLP, TxMQL, CPMQL, CAC.

## Connect Rate (Page Views ÷ Cliques)

**Objetivo:** avaliar a eficiência da conexão entre o clique e o
carregamento da página.

**Possíveis gargalos:** página lenta, hospedagem ruim, imagens pesadas,
excesso de scripts, redirecionamentos, erros de carregamento, experiência
mobile ruim, pixel mal configurado (o pixel do Lucas roda via GTM).

**Ações:** melhorar velocidade da página, otimizar imagens, reduzir
scripts, remover redirecionamentos, verificar erros 404/500, testar em
diferentes dispositivos, revisar o evento de Page View no GTM.

**Quando NÃO é problema:** pode ser só falha de mensuração (AdBlock,
restrições do iOS, consentimento de cookies, diferença Meta x GTM/GA4) e
não um problema técnico real — se Leads e MQLs seguem normais e o
CPL/CPMQL saudável, não é gargalo operacional.

**Cruzar com:** ConvLP, CPL, CPMQL.

## ConvLP (Leads ÷ Page Views)

**Objetivo:** avaliar se a página e o formulário convencem o visitante a
preencher os dados.

**Possíveis gargalos:** promessa pouco clara, página desalinhada com o
anúncio, formulário longo, falta de prova social, design pouco confiável,
CTA fraco, página lenta, experiência mobile ruim.

**Ações:** melhorar headline, reforçar a promessa, alinhar anúncio e
página, melhorar o CTA, inserir provas sociais, reduzir fricção do
formulário, melhorar versão mobile, verificar erros de envio/integração.

**Quando NÃO é problema:** ConvLP baixa pode ser aceitável se o formulário é
intencionalmente qualificador (as perguntas de perfil e volume de clientes
filtram gente sem perfil) e a TxMQL segue alta e o CPMQL saudável.

**Cruzar com:** CPL, TxMQL, CPMQL, CAC.

## CPL (Investimento ÷ Leads)

**Objetivo:** avaliar a eficiência financeira da captação.

**Importante:** CPL alto é **efeito, não causa**. Nunca analisar isolado —
sempre identificar qual etapa anterior perdeu eficiência (CPM, CTR, Connect
Rate ou ConvLP) antes de sugerir ação.

**Quando NÃO é problema:** CPL alto pode ser saudável se a TxMQL é alta, a
taxa de agendamento é alta e o CAC segue dentro da meta. Um lead mais caro
que vira MQL vale mais que vários leads baratos e desqualificados.

**Cruzar com:** TxMQL, CPMQL, Taxa de Agendamento, CAC.

## TxMQL (MQLs ÷ Leads)

**Objetivo:** avaliar a qualidade dos leads gerados.

**Possíveis gargalos:** anúncios atraindo curiosos sem perfil de negócio,
promessa muito ampla, comunicação pouco qualificada, segmentação
inadequada, critérios de MQL mal definidos, conteúdo apelativo demais.

**Ações:** tornar a copy mais específica pro público (contador, consultor,
BPO), informar pra quem a formação é indicada e pra quem não é, revisar
critérios de MQL, testar novos públicos, otimizar campanhas olhando MQL e
não só lead.

**Quando NÃO é problema:** TxMQL baixa pode ocorrer em campanha de
expansão, com público mais amplo e volume de leads maior — se o CPMQL
segue saudável e o volume absoluto de MQL sobe, pode ser aceitável.

**Cruzar com:** CPL, CPMQL, Taxa de Agendamento, CAC.

## CPMQL (Investimento ÷ MQLs)

**Objetivo:** avaliar o custo real pra atrair uma oportunidade com perfil
comercial. Mais relevante que o CPL puro pra esse tipo de oferta.

**Possíveis gargalos:** CPL alto, TxMQL baixa, criativos atraindo gente sem
perfil, formulário pouco qualificador.

**Ações:** identificar se o problema tá no custo do lead ou na
qualificação, comparar CPMQL entre campanhas e públicos, ajustar
comunicação pro perfil ideal, melhorar as perguntas de qualificação.

**Quando NÃO é problema:** CPMQL alto pode ser saudável se a taxa de
agendamento e a taxa de vendas são boas e o CAC segue dentro da meta.

**Cruzar com:** Taxa de Agendamento, Custo por Agendamento, CAC.

## Taxa de Agendamento (Agendamentos ÷ MQLs)

**Objetivo:** avaliar se o time comercial transforma MQL em oportunidade
agendada via WhatsApp.

**Possíveis gargalos:** demora no primeiro contato, leads não atendidos,
abordagem comercial ruim, falta de follow-up, MQLs sem intenção real de
compra, dados de contato incorretos.

**Ações:** reduzir tempo de primeiro contato no WhatsApp, criar cadência de
follow-up, melhorar script de abordagem inicial, explicar o benefício da
sessão estratégica logo de cara, analisar a taxa por período e por origem
de campanha.

**Quando NÃO é problema:** pode ser baixa se os critérios de MQL são amplos
demais ou o lead ainda precisa de nutrição antes de agendar.

**Cruzar com:** CPMQL, Taxa de Vendas, CAC.

> **Fonte de dado:** Agendamentos não têm fonte conectada neste dashboard
> ainda (não há aba de comercial/WhatsApp integrada) — Taxa de Agendamento e
> Custo por Agendamento aparecem "-" até essa fonte ser conectada. Ver
> "Gargalo de dado" em `GUIA-RELATORIOS.md`.

## Custo por Agendamento (Investimento ÷ Agendamentos)

**Objetivo:** avaliar a eficiência conjunta do tráfego, qualificação e
contato comercial.

**Importante:** não atacar direto. Identificar em qual etapa está a perda
(captação, qualificação ou contato) e corrigir a de maior impacto.

**Quando NÃO é problema:** pode ser alto e saudável se a taxa de vendas é
alta e o CAC segue dentro da meta.

**Cruzar com:** CPMQL, Taxa de Vendas, CAC.

## Taxa de Vendas (Vendas ÷ Agendamentos)

**Objetivo:** avaliar a conversão do agendamento em venda da formação. Como
não existe etapa de comparecimento monitorada, essa taxa já engloba
comparecimento + fechamento.

**Possíveis gargalos:** script comercial fraco, diagnóstico superficial na
sessão, oferta mal apresentada, objeções não trabalhadas, falta de
follow-up pós-sessão, MQLs pouco qualificados chegando no agendamento,
preço/condições incompatíveis com o perfil do lead.

**Ações:** revisar gravações das sessões, melhorar o script comercial,
treinar diagnóstico e tratamento de objeções, criar cadência de follow-up
pós-sessão, separar perdas por motivo, revisar critérios de MQL se a
conversão for consistentemente baixa.

**Quando NÃO é problema:** pode ser baixa por ciclo comercial longo,
negociações em aberto, ou agendamentos muito recentes que ainda vão fechar
depois.

**Cruzar com:** TxMQL, Taxa de Agendamento, CAC.

> **Fonte de dado:** como o denominador é Agendamentos (sem fonte
> conectada), Taxa de Vendas aparece "-" mesmo quando o número absoluto de
> Vendas está disponível (a aba Vendas já está conectada e cruzada com
> Leads). Ver "Gargalo de dado" em `GUIA-RELATORIOS.md`.

## CAC (Investimento ÷ Vendas)

**Objetivo:** avaliar a eficiência financeira de toda a operação.

**Importante:** nunca atacar o CAC diretamente. Identificar em qual etapa
do funil está a maior perda (Impressão→Clique→Page View→Lead→MQL→
Agendamento→Venda) e corrigir a etapa responsável.

**Quando NÃO é problema:** pode ser alto e sustentável se a operação está
em fase de escala/teste de público, ou se existe indicação/upsell futuro
que não entra nessa conta.

**Cruzar com:** Taxa de Vendas, Taxa de Agendamento, CPMQL.

> **Fonte de dado:** CAC **é calculável** — a aba Vendas já está conectada e
> cruzada com Leads (por `lead_id`, com fallback por telefone), então o
> número absoluto de Vendas e o Investimento÷Vendas funcionam mesmo sem a
> fonte de Agendamentos.

## Regras gerais de interpretação

- Nunca concluir que uma métrica isolada é o gargalo do funil. Sempre olhar
  a etapa anterior e a posterior junto.
- Connect Rate baixo + ConvLP alta: investigar primeiro problema de
  mensuração (pixel via GTM, consentimento de cookies, bloqueadores) antes
  de assumir problema de carregamento de página.
- CPL alto é efeito, não causa — sempre identificar qual etapa anterior
  perdeu eficiência.
- Mudanças de público ou aumento de verba podem derrubar CTR ou ConvLP
  temporariamente — comparar a queda com o aumento de volume/receita antes
  de classificar como gargalo real.
- Campanha ou conjunto com volume abaixo do mínimo amostral não deve gerar
  decisão nenhuma sobre aquele recorte — apenas sinalizar que está abaixo
  do mínimo.
- Sempre comparar com o histórico da própria conta, **nunca com benchmark
  de mercado**, a menos que uma meta tenha sido explicitamente configurada
  no painel (CPMQL alvo, CAC alvo). Se a meta não estiver definida, dizer
  isso explicitamente.
- Se Agendamentos, Vendas ou Faturamento não tiverem fonte de dado
  conectada (ex: aguardando planilha do comercial), isso é **prioridade
  alta** e deve aparecer destacado — porque sem essa informação, CAC e
  Taxa de Vendas ficam "-" e qualquer decisão de otimização depois do MQL é
  decisão às cegas. Hoje, especificamente, Agendamentos não tem fonte
  conectada (Vendas/Faturamento já têm, via aba Vendas) — ver
  `GUIA-RELATORIOS.md` → "Gargalo de dado".

## Fase de calibração

A conta é recente e ainda não tem histórico de volume consolidado. Enquanto
o **total acumulado de leads/MQLs** (desde o início da conta, não só do dia)
estiver abaixo do mínimo amostral configurado no painel (`volume_min_amostral`
em `build/relatorios_dados.json` → `params`):

- A IA não deve comparar contra médias históricas nem inventar tendência.
- A seção RESUMO DO PERÍODO deve dizer explicitamente que a conta está em
  **fase de calibração** e que ainda não há base suficiente pra leitura
  confiável.
- Assim que o acumulado passar do mínimo configurado, a IA passa a comparar
  contra o próprio histórico normalmente — sem prazo fixo de dias, só por
  volume acumulado.

O mínimo amostral é um número **configurável no painel** (Metas & parâmetros
da aba Relatório, campo "Volume mín. amostral"), não fixo neste guia — leia
sempre `params.volume_min_amostral` do JSON do dia.

## Unidade de análise: campanha + conjunto

O mesmo anúncio pode rodar em campanhas/conjuntos diferentes com resultados
diferentes. Ao classificar por campanha/conjunto (ver
`GUIA-RELATORIOS.md` → CLASSIFICAÇÃO POR CAMPANHA/CONJUNTO), sempre nomeie
campanha e conjunto por inteiro (nunca abreviados).

## Como citar "meta" vs. "referência de mercado"

Nunca cite benchmark de mercado como se fosse uma meta da conta. Se
`meta_cpmql`/`meta_cac` vierem `null` no JSON, diga explicitamente "meta não
definida" — não invente um teto. A única referência válida sem meta
configurada é o **histórico da própria conta** (janelas de 7/14/30 dias).
