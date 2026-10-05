# Log de Decisões e Mudanças de Spec

> Este arquivo registra mudanças no comportamento especificado. Decisões apenas
> técnicas ficam no `plan.md`. Ordem cronológica inversa: a mais recente primeiro.

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

