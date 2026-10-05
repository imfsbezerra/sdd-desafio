# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 2.0 · **Baseado na spec:** 2.0 / Política v4 · **Data:** 2026-10-05

## 1. Resultado pretendido

Absorver os itens obrigatórios A e B do envelope sem reescrever o núcleo: carregar
política e câmbio externos, converter cada item para BRL e reutilizar a sequência
de elegibilidade, nota, duplicidade, limites e resumo.

O item C não será implementado nesta rodada.

## 2. Impacto na arquitetura existente

```text
politica-v4.json ─→ validação da política ─┐
                                           ├→ motor puro → resultado v4
cambio.json ──────→ validação das taxas ───┤      ↑
                                           │      │
despesas.json ────→ validação da entrada ──┘   valores BRL
                                                   ↓
                                            gravação atômica
```

| Componente | Absorve de graça | Precisa mudar |
|---|---|---|
| Leitura JSON decimal | Preserva taxas e valores | Validar dois contratos novos |
| Modelo de despesa | Ordem e valor original já existem | Adicionar moeda |
| Motor puro | Precedência, decisões e saldos | Receber política/câmbio e remover constantes |
| Dinheiro | `Decimal` e arredondamento já existem | Multiplicar e registrar conversão |
| Duplicidade | Função isolada | Incluir moeda na assinatura |
| Nota fiscal | Etapa isolada | Limiar externo e valor BRL |
| Limites | Saldo por chave já existe | Categoria, periodicidade e limite dirigidos por dados |
| Saída | Serialização centralizada | Identificar política e conversão |
| CLI | Parsing e escrita atômica já existem | Duas opções com defaults externos |

## 3. Stack

Mantém-se Python 3.11+ somente com biblioteca padrão, `Decimal` para todos os
valores e `unittest` para testes. Não há razão técnica trazida pelo envelope para
introduzir dependências.

## 4. Novos modelos

- `RegraCategoria`: limite decimal e periodicidade;
- `Politica`: versão, vigência, moeda-base, tabela padrão, tabelas por centro,
  limiar de nota e percentual de viagem;
- `TabelaSelecionada`: origem (`centro_custo`/`padrao`) e mapa de categorias;
- `Cambio`: moeda-base e taxas por data/moeda;
- `Conversao`: moeda original, taxa, data da taxa e valor BRL, ou ausência de
  cotação;
- `Despesa`: acrescenta `moeda`, já normalizada para três letras.

Objetos de política e câmbio são imutáveis depois da validação. O motor recebe os
dois explicitamente, sem estado global nem cache.

## 5. Fluxo técnico

1. CLI resolve os caminhos `--politica` e `--cambio` ou usa os defaults em
   `exemplos/envelope/`.
2. Leitor carrega decimais e valida política e câmbio por inteiro.
3. Solicitação é validada também contra a vigência da política.
4. Motor seleciona uma única tabela pelo centro de custo.
5. Para cada despesa, busca a taxa exata ou percorre datas anteriores em ordem
   decrescente para a mesma moeda.
6. Converte e arredonda o valor BRL.
7. Aplica categoria, valor, duplicidade, nota, periodicidade e limite.
8. Monta saída v4 e grava atomicamente.

## 6. Decisões técnicas

### DT-005 — Configuração injetada no motor

**Decisão:** funções de processamento recebem `Politica` e `Cambio` como
argumentos.

**Alternativa descartada:** constantes globais ou leitura de arquivo dentro do
motor.

**Consequência:** testes constroem políticas pequenas em memória e mudanças de
arquivo não contaminam outras execuções.

### DT-006 — Validação dedicada das fontes externas

**Decisão:** erros da política e do câmbio usam a mesma família de erro de entrada,
com caminhos como `politica.centros_custo.X` e `cambio.taxas.2026-07-14.EUR`.

**Alternativa descartada:** aceitar configuração parcial e falhar durante um item.

**Consequência:** erro estrutural impede resultado; ausência legítima de uma moeda
continua sendo decisão por item, conforme RN-008.

### DT-007 — Busca determinística da taxa

**Decisão:** para moeda estrangeira, filtrar datas `<= data_despesa` que tenham a
moeda e escolher a maior data.

**Alternativa descartada:** retroceder dia a dia ou usar a próxima taxa.

**Consequência:** funciona mesmo com lacunas longas e nunca usa conhecimento
futuro.

### DT-008 — Periodicidade dirigida pela política

**Decisão:** `dia` usa saldo por `(data, categoria)`; `diaria` aplica limite por
item. Categoria de limite zero termina antes de alocação.

**Alternativa descartada:** condicionais fixas para alimentação, transporte,
hospedagem e representação.

**Consequência:** novas categorias com periodicidades conhecidas entram apenas no
arquivo externo.

### DT-009 — Compatibilidade da interface

**Decisão:** manter `--input` e `--output` obrigatórios e adicionar `--politica` e
`--cambio` opcionais, com caminhos padrão versionados.

**Alternativa descartada:** tornar os dois novos parâmetros obrigatórios, o que
quebraria o comando fixo do desafio.

**Consequência:** o comando antigo passa a calcular o mesmo arquivo sob a v4, e
ambientes externos podem fornecer configurações diferentes.

## 7. Estratégia de testes

- validação isolada de política e câmbio, incluindo limite zero e periodicidade;
- seleção de centro conhecido/desconhecido e categoria ausente;
- moeda default, normalização e assinatura de duplicidade;
- conversão exata, último dia anterior, GBP sem taxa e arredondamento;
- nota fiscal depois da conversão;
- periodicidade genérica `dia`/`diaria` e limite zero;
- integração exata dos dois arquivos do envelope;
- regressão do exemplo v3 recalculado pela v4;
- CLI com defaults, caminhos explícitos e preservação do destino em configuração
  inválida.

Cada teste novo usa `test_rnNNN_` ou `test_ambNNN_`. A suíte v3 será atualizada
apenas quando o comportamento foi deliberadamente substituído pela v4.

## 8. Ordem de execução

1. T-012: contratos externos;
2. T-013: moeda e conversão;
3. T-014: política dinâmica;
4. T-015: orquestração e saída;
5. T-016: CLI;
6. T-017: integrações e regressão;
7. T-018: documentação e relatório.

Cada task termina com suíte completa verde e commit próprio antes da seguinte.

## 9. Riscos

| Risco | Mitigação |
|---|---|
| Resultado v3 mudar silenciosamente | Teste de regressão com novos números explícitos |
| Fallback misturar centro e padrão | Testes separados para centro ausente e categoria ausente |
| Nota ser comparada antes da conversão | Teste USD 40 sem nota → BRL 220 |
| Fim de semana usar taxa futura | Teste fixa data da taxa em 17/07 |
| Item sem taxa quebrar totais | Campo `quantidade_sem_conversao` e reconciliação apenas dos convertidos |
| Configuração inválida deixar saída parcial | Reutilizar gravação atômica e testar preservação |

