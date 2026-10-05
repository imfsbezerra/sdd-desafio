# Log de Decisões e Mudanças de Spec

> Este arquivo registra mudanças no comportamento especificado. Decisões apenas
> técnicas ficam no `plan.md`. Ordem cronológica inversa: a mais recente primeiro.

---

## D-002 — Absorção da Política de Reembolso v4 · 2026-10-05

**Gatilho:** envelope registrado em `CHANGE.MD`, com limites externos por centro
de custo, categoria `representacao` e despesas em moeda estrangeira.

**O que mudou na spec:** versão 1.1/política v3 → versão 2.0/política v4.

- RN-003 deixou de usar categorias globais e passou a selecionar uma tabela por
  centro de custo, com fallback integral para `padrao` somente quando o centro
  não existe;
- RN-005 da v3 foi substituída por RN-010: nota fiscal usa limiar externo e valor
  convertido para BRL;
- RN-006/RN-011 passou a incluir moeda e valor original na duplicidade;
- RN-007 a RN-009 deixaram de usar limites internos; limite e periodicidade vêm
  do arquivo externo;
- RN-012 foi expandida para dois arredondamentos: moeda original e conversão BRL;
- foram criadas RN-003 a RN-008 específicas de seleção de política e câmbio;
- saída passou a identificar política, origem da tabela, moeda, taxa, data da taxa
  e valor convertido;
- AMB-016 a AMB-026 resolvem fallback, taxa de fim de semana, moeda sem cotação,
  arredondamento, nota em moeda estrangeira, duplicidade e escopo opcional.

**Por quê:** a política deixou de ser única e constante. Comparar moeda estrangeira
diretamente com limites BRL produziria decisões incorretas e não auditáveis.

**O que isso invalidou:** constantes internas do motor, lista fixa de categorias,
modelo de despesa sem moeda, assinatura de duplicidade, verificação de nota,
schema de saída, CLI sem fontes externas e resultados esperados da v3 para
`CC-ENG-PLATAFORMA`.

**Tasks afetadas:** T-002 a T-010 precisam de extensão ou regressão. Foram criadas
T-012 a T-018; as tasks antigas permanecem como trilha histórica e não são
renumeradas.

**Custo inicial:** 7 arquivos tocados antes do código: `CHANGE.MD`, quatro JSONs
do envelope, `spec.md` e este log. Tempo e diff final serão preenchidos ao fechar
a implementação.

**Decisão de escopo:** o item C, fila manual, não será implementado por ser
opcional. Os itens A e B são obrigatórios e prioritários.

---

## D-001 — Revisão crítica da especificação inicial · 2026-10-05

**Gatilho:** revisão do rascunho preservado no commit `05a079f` contra o enunciado,
a rubrica e o arquivo de exemplo revelou contradições e regras inventadas.

**O que mudou na spec:** a versão 1.0 foi substituída pela 1.1. Em particular:

- RN-009 passou a tratar cada lançamento de hospedagem como uma diária, sem
  interpretar números da descrição. A versão anterior simultaneamente mandava
  dividir “2 diárias” e dizia que texto livre não seria interpretado;
- RN-004 passou a rejeitar valores não positivos sem gerar crédito. A versão
  anterior inventava que estornos pertenciam à regra de duplicatas e liberavam
  limite, embora não exista vínculo com uma despesa original;
- RN-011 registra a decisão atual para viagem sem antecipar qual será uma futura
  mudança de requisito. A versão anterior afirmava conhecer o conteúdo do
  envelope do segundo dia;
- o contrato de saída foi reduzido a campos reconciliáveis e determinísticos;
- foram explicitadas a precedência das regras, a alocação FIFO, a base da nota
  fiscal, as fronteiras do período, o fim de semana e o arredondamento;
- a lista cresceu de 10 para 15 ambiguidades, todas ligadas a regras verificáveis.

**Por quê:** eliminar contradições, separar fatos disponíveis de suposições e
permitir que código e testes sejam derivados sem decisões silenciosas.

**O que isso invalidou:** todo o plano técnico e a lista de tasks do rascunho,
especialmente parsing de descrição de hospedagem, cálculo de estorno, schema de
saída com timestamp e dependências externas escolhidas antes da revisão.

**Tasks afetadas:** as tasks antigas T-001 a T-021 foram substituídas antes do
início da implementação; nenhuma havia sido executada.

**Custo:** 4 documentos de especificação reavaliados; implementação ainda não
iniciada, portanto nenhum código ou teste precisou ser refeito.

