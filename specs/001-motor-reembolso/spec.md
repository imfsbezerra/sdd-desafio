# Spec — Motor de Cálculo de Reembolso

**Versão:** 2.0 · **Política:** v4 · **Status:** aprovada para implementação · **Última alteração:** 2026-10-05

> Este documento define o que o produto faz e por quê. Decisões técnicas ficam no
> `plan.md`. A Política v4 substitui a v3 para a competência atual.

## 1. Problema e objetivo

O financeiro precisa avaliar despesas com limites que variam por centro de custo
e valores que podem estar em moeda estrangeira. O sistema deve carregar a política
e as cotações de fontes externas, calcular valores em BRL e justificar cada
decisão de maneira determinística e auditável.

## 2. Fora de escopo

- pagamentos, persistência, autenticação ou integrações externas;
- obtenção automática de cotação ou política pela internet;
- inferência de viagem ou quantidade de diárias a partir de texto livre;
- conversão inversa do valor reembolsável para a moeda original;
- mistura de duas versões de política na mesma execução;
- fila de aprovação manual do item C do envelope, que é opcional;
- regras por feriado, fim de semana ou finalidade comercial não declaradas.

## 3. Entradas da execução

A execução recebe:

1. um JSON de despesas no formato dos arquivos de exemplo;
2. um JSON de política no formato de `exemplos/envelope/politica-v4.json`;
3. um JSON de câmbio no formato de `exemplos/envelope/cambio.json`.

O comando obrigatório continua sendo `calcular --input <arquivo> --output
<arquivo>`. Os arquivos externos podem ser indicados por `--politica` e
`--cambio`; quando omitidos, usam-se os arquivos correspondentes em
`exemplos/envelope/`.

### 3.1 Solicitação de despesas

Mantêm-se os campos da v3. Cada despesa ganha o campo opcional `moeda`, texto com
três letras conforme ISO 4217. Quando ausente, seu valor é `BRL`. Espaços externos
e capitalização são ignorados; outros formatos tornam o documento inválido.

O período é válido quando `inicio <= fim`, ambas as datas pertencem a
`competencia` e não são anteriores à vigência da política carregada. IDs de
despesa devem ser únicos. Campo obrigatório ausente, tipo incorreto ou data
impossível invalida o documento inteiro.

### 3.2 Política externa

A política deve informar:

- `versao`, `vigencia` e `moeda_base` igual a `BRL`;
- tabela `padrao` não vazia;
- mapa `centros_custo`;
- limite de nota fiscal;
- percentual de acréscimo em viagem;
- para cada categoria, limite monetário não negativo e periodicidade `dia` ou
  `diaria`.

Política ausente ou inválida encerra a execução sem resultado. A política é lida
novamente em cada execução; nenhuma tabela de limites interna substitui sua fonte.

### 3.3 Câmbio externo

O arquivo deve declarar `moeda_base` igual a `BRL` e um mapa de datas para taxas
positivas. Cada moeda é identificada por três letras. Arquivo ausente ou inválido
encerra a execução sem resultado, mesmo quando todas as despesas forem BRL.

## 4. Saída

A saída preserva a ordem das despesas e usa textos monetários com duas casas.
Todos os totais e valores reembolsáveis são expressos em BRL.

| Campo | Significado |
|---|---|
| `politica.versao` | Versão carregada |
| `politica.origem_limites` | `centro_custo` ou `padrao` |
| `politica.centro_custo` | Centro avaliado |
| `politica.moeda_base` | `BRL` |
| `colaborador`, `periodo` | Dados copiados da entrada |
| `resumo.quantidade_despesas` | Total de itens |
| `resumo.total_solicitado` | Soma dos valores positivos convertidos para BRL |
| `resumo.total_reembolsavel` | Soma reembolsável em BRL |
| `resumo.total_nao_reembolsavel` | Diferença entre os dois totais anteriores |
| `resumo.quantidade_sem_conversao` | Itens sem valor BRL por falta de cotação |
| `resumo.quantidade_aprovadas` | Itens integralmente pagos |
| `resumo.quantidade_parciais` | Itens parcialmente pagos |
| `resumo.quantidade_rejeitadas` | Itens com pagamento zero |
| `decisoes` | Uma decisão por item, na ordem original |

Cada decisão contém os campos já existentes (`id`, `status`, valores, motivo,
justificativa e regras) e acrescenta:

| Campo | Significado |
|---|---|
| `moeda_original` | Moeda informada ou `BRL` por padrão |
| `taxa_cambio` | Taxa usada; `1.000000` para BRL; `null` sem cotação |
| `data_taxa_cambio` | Data da taxa; data da despesa para BRL; `null` sem cotação |
| `valor_convertido_brl` | Valor normalizado e convertido; `null` sem cotação |

`valor_normalizado` continua na moeda original. `valor_reembolsavel` e
`valor_nao_reembolsavel` são sempre BRL. Além dos códigos da v3, são permitidos
`COTACAO_INDISPONIVEL` e `CATEGORIA_NAO_REEMBOLSAVEL`.

## 5. Regras de negócio

### RN-001 — Validade do documento e configurações

Entrada, política e câmbio devem cumprir a seção 3. Qualquer erro estrutural
encerra a execução sem criar ou substituir a saída.

**Aceite:** moeda `EURO`, política com periodicidade desconhecida ou taxa zero
produzem erro de configuração/entrada e nenhum resultado.

### RN-002 — Competência e vigência

Datas inicial e final são inclusivas. Despesa fora do intervalo é rejeitada. A
execução aceita somente período integralmente coberto pela vigência da política.

**Aceite:** política vigente em 2026-07-01 processa julho, mas não uma solicitação
iniciada em junho.

### RN-003 — Seleção da tabela de limites

Se o centro de custo existir em `centros_custo`, usa-se exatamente sua tabela. Se
não existir, usa-se exatamente `padrao`. Uma categoria ausente na tabela escolhida
não herda outra tabela e não é reembolsável.

**Aceite:** `CC-SUPORTE-N2` usa os limites padrão; `CC-ADM` não recebe hospedagem,
pois seu centro existe e não contém essa categoria.

### RN-004 — Categorias externas

Uma categoria é coberta somente quando aparece na tabela selecionada e possui
limite maior que zero. Limite zero rejeita com `CATEGORIA_NAO_REEMBOLSAVEL`.

**Aceite:** `representacao` vale para `CC-COMERCIAL`, não para um centro ausente;
hospedagem é rejeitada para `CC-ENG-PLATAFORMA`.

### RN-005 — Moeda padrão e normalização

Moeda ausente equivale a `BRL`. O código é comparado sem diferenças de
capitalização e espaços externos.

**Aceite:** ausência, `BRL` e ` brl ` produzem moeda original `BRL`.

### RN-006 — Conversão cambial

BRL usa taxa 1. Para outra moeda, multiplica-se o valor original normalizado pela
taxa que representa quantos BRL equivalem a uma unidade da moeda. O resultado é
arredondado para centavos antes de nota fiscal e limites.

**Aceite:** EUR 22,00 em 2026-07-14 com taxa 5,93 converte para BRL 130,46.

### RN-007 — Data da cotação

Usa-se a taxa da data da despesa. Quando não houver publicação nessa data, usa-se
a taxa mais recente anterior disponível para a mesma moeda. Taxa futura nunca é
usada.

**Aceite:** EUR 30,00 em sábado, 2026-07-18, usa EUR 5,96 de 2026-07-17.

### RN-008 — Cotação indisponível

Se não existir taxa da moeda na data nem em data anterior, o item é rejeitado com
`COTACAO_INDISPONIVEL`. Ele contribui com zero para os três totais monetários e
incrementa `quantidade_sem_conversao`.

**Aceite:** GBP do arquivo de envelope é rejeitada porque não há taxa de GBP.

### RN-009 — Valores não positivos

Valor original normalizado igual a zero ou negativo é rejeitado, não cria crédito
e contribui com zero para os totais.

### RN-010 — Nota fiscal em BRL

O limiar vem da política externa. A nota é exigida quando o valor convertido em
BRL é estritamente maior que esse limiar, antes de aplicar limite de categoria.

**Aceite:** EUR 14,50 convertido para BRL 85,26 não exige nota; USD 40,00
convertido para BRL 220,00 exige.

### RN-011 — Duplicatas

Duplicata possui mesma data, categoria, descrição, fornecedor, moeda e valor
original normalizado. A primeira ocorrência segue e as posteriores são rejeitadas.
IDs, nota fiscal e valor convertido não compõem a assinatura.

### RN-012 — Periodicidade e alocação

Categoria com periodicidade `dia` compartilha seu limite entre itens da mesma
data e categoria, consumido na ordem de entrada. Periodicidade `diaria` aplica o
limite separadamente a cada lançamento. Texto livre não altera quantidades.

### RN-013 — Reembolso parcial

Paga-se até o saldo do limite selecionado e recusa-se o excedente. Pagamento
integral é `APROVADA`; maior que zero e menor que o convertido é `PARCIAL`; zero é
`REJEITADA`.

### RN-014 — Viagem

Embora a política externa informe percentual de acréscimo, o contrato de despesas
continua sem indicador de viagem. Nenhuma execução aplica esse acréscimo.

### RN-015 — Precisão monetária

O valor original é arredondado para duas casas pelo centavo mais próximo, com
empate afastado de zero. A multiplicação cambial usa a taxa completa do arquivo e
o resultado em BRL é arredondado pela mesma regra. Limites e totais usam o valor
BRL já arredondado.

### RN-016 — Explicação e reconciliação

Cada item gera uma decisão. As contagens por status somam a quantidade de itens.
Entre itens que possuem conversão, `total_solicitado = total_reembolsavel +
total_nao_reembolsavel`.

## 6. Ambiguidades novas da v4 e decisões

### AMB-016 — Significado de “política padrão”

**Ambiguidade:** não estava claro se o padrão completa categorias ausentes de um
centro conhecido.

**Decisão:** padrão só é usado quando o centro inteiro não existe; não mesclar
tabelas.

**Justificativa:** o comunicado condiciona o padrão a centros sem entrada, e o
limite zero explícito demonstra que ausência e proibição precisam ser observáveis.

**Regras:** RN-003 e RN-004.

### AMB-017 — Categoria dirigida pela configuração

**Ambiguidade:** a v3 tinha lista fixa, mas a v4 introduz `representacao` apenas
para um centro.

**Decisão:** a tabela selecionada define categorias válidas; não existe lista
global fixa.

**Justificativa:** permite que a política mude externamente sem alteração do motor.

**Regra:** RN-004.

### AMB-018 — Interpretação da taxa

**Ambiguidade:** o arquivo não declara se a taxa é BRL por moeda ou moeda por BRL.

**Decisão:** uma unidade estrangeira multiplicada pela taxa resulta em BRL.

**Justificativa:** os valores fornecidos são compatíveis com PTAX expressa em BRL.

**Regra:** RN-006.

### AMB-019 — Data sem cotação

**Ambiguidade:** há despesas em fim de semana e taxas somente em dias úteis.

**Decisão:** usar a última taxa anterior da mesma moeda.

**Justificativa:** não antecipa informação futura e representa a última cotação
conhecida na data da despesa.

**Regra:** RN-007.

### AMB-020 — Moeda desconhecida ou sem histórico

**Ambiguidade:** a entrada contém GBP, ausente de todo o arquivo de câmbio.

**Decisão:** rejeitar somente o item, com valor BRL desconhecido e contribuição
zero nos totais.

**Justificativa:** inventar taxa seria incorreto; abortar outros itens válidos
seria desnecessário.

**Regra:** RN-008.

### AMB-021 — Momento do arredondamento cambial

**Ambiguidade:** arredondar taxa, produto, agregado ou somente saída pode mudar
limites e nota.

**Decisão:** não arredondar a taxa; arredondar cada valor convertido para centavos
antes das regras seguintes.

**Justificativa:** cada despesa passa a ter um valor BRL audível e estável.

**Regra:** RN-015.

### AMB-022 — Nota fiscal em moeda estrangeira

**Ambiguidade:** comparar 100 na moeda original ou BRL convertido.

**Decisão:** comparar o valor convertido com o limiar externo em BRL.

**Justificativa:** a política declara que seus limites são sempre em BRL.

**Regra:** RN-010.

### AMB-023 — Duplicata multimoeda

**Ambiguidade:** duas moedas podem converter ao mesmo valor ou a mesma moeda pode
usar outra taxa.

**Decisão:** assinatura usa moeda e valor original, não valor convertido.

**Justificativa:** duplicidade descreve a transação submetida, não coincidência no
resultado do câmbio.

**Regra:** RN-011.

### AMB-024 — Política alterada sem aviso

**Ambiguidade:** não estava claro se o motor poderia manter cache ou constantes.

**Decisão:** ler e validar o arquivo a cada execução; resultado identifica versão
e origem dos limites.

**Justificativa:** garante que a execução use o documento fornecido naquele
momento e deixa evidência auditável.

**Regras:** RN-001 e RN-003.

### AMB-025 — Acréscimo de viagem ainda sem dado

**Ambiguidade:** a v4 preserva o percentual, mas a entrada ainda não informa
viagem.

**Decisão:** manter limites sem acréscimo.

**Justificativa:** o novo campo `moeda` prova internacionalização da despesa, não
o estado de viagem do colaborador para toda a política.

**Regra:** RN-014.

### AMB-026 — Item opcional de aprovação manual

**Ambiguidade:** o comunicado permite implementar somente se houver tempo.

**Decisão:** não implementar nesta absorção.

**Justificativa:** priorizar coerência e testes dos itens obrigatórios A e B.

**Escopo afetado:** seção 2.

As decisões AMB-001 a AMB-015 da v3 continuam válidas quando não forem
explicitamente substituídas por AMB-016 a AMB-026. Em particular: limites por dia
são agregados, excedentes são pagos parcialmente, datas-limite são inclusivas,
valores não positivos não geram crédito, fins de semana não mudam elegibilidade e
a ordem das regras define o motivo principal.

## 7. Ordem de aplicação

Para cada item, na ordem recebida:

1. normalizar valor, moeda e textos;
2. rejeitar data fora da competência;
3. localizar taxa e converter para BRL; rejeitar se indisponível;
4. selecionar a tabela do centro e rejeitar categoria ausente ou de limite zero;
5. rejeitar valor não positivo;
6. rejeitar ocorrência duplicada;
7. rejeitar falta de nota quando o valor BRL exceder o limiar;
8. aplicar periodicidade, limite e saldo;
9. produzir decisão e atualizar totais.

Itens rejeitados não consomem limite. A primeira assinatura elegível é reservada
antes da nota fiscal, como na v3.

## 8. Casos de aceite do envelope

| Caso | Resultado esperado |
|---|---|
| Centro desconhecido | Usa tabela `padrao` |
| `CC-COMERCIAL` + `representacao` R$ 340 | R$ 300 reembolsáveis |
| `CC-ENG-PLATAFORMA` + hospedagem | R$ 0 e categoria não reembolsável |
| EUR 22 em 14/07 | BRL 130,46 antes do limite |
| EUR 30 em 18/07 | Usa taxa EUR de 17/07 |
| USD 40 sem nota em 20/07 | BRL 220 e rejeição por nota |
| GBP sem cotação | Rejeição por cotação, sem valor BRL |
| Moeda ausente | Tratada como BRL |
| Política/câmbio inválido | Execução falha sem sobrescrever saída |

## 9. Critérios de conclusão

- [ ] política e câmbio são lidos externamente em cada execução;
- [ ] arquivos v3 continuam válidos porque moeda ausente equivale a BRL;
- [ ] todos os RN-001 a RN-016 possuem teste;
- [ ] AMB-016 a AMB-026 estão refletidas em teste ou escopo negativo;
- [ ] os dois arquivos de despesas do envelope têm resultados exatos testados;
- [ ] o arquivo v3 de exemplo é recalculado sob a Política v4;
- [ ] README documenta configuração externa e exemplos;
- [ ] suíte completa passa e o histórico segue as novas tasks.

