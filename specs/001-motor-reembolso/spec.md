# Spec — Motor de Cálculo de Reembolso

**Versão:** 1.1 · **Status:** aprovada para implementação · **Última alteração:** 2026-10-05

> Este documento define o que o produto faz e por quê. Decisões de tecnologia e
> organização da implementação pertencem ao `plan.md`.

---

## 1. Problema

O financeiro confere manualmente cada despesa contra uma política textual. O
processo é demorado, sujeito a interpretações diferentes e não explica de forma
padronizada quanto foi aceito ou recusado em cada lançamento.

## 2. Objetivo

Receber as despesas de um colaborador em um período, calcular de forma
determinística o valor reembolsável e justificar a decisão tomada para cada
despesa.

## 3. Fora de escopo

- efetuar pagamentos ou integrar com folha, banco ou sistema contábil;
- autenticar usuários ou autorizar quem pode solicitar reembolso;
- armazenar histórico entre execuções;
- corrigir ou completar automaticamente dados ausentes;
- processar mais de um colaborador na mesma execução;
- inferir viagem, quantidade de diárias ou outros fatos a partir de texto livre;
- avaliar necessidade, razoabilidade ou finalidade comercial da despesa;
- aplicar regras diferentes por fim de semana, feriado ou centro de custo.

## 4. Contrato de entrada

A entrada é um documento JSON no formato de
`exemplos/despesas-exemplo.json`.

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `colaborador.id` | texto não vazio | Identificador do colaborador | Sim |
| `colaborador.nome` | texto não vazio | Nome do colaborador | Sim |
| `colaborador.centro_custo` | texto não vazio | Centro de custo | Sim |
| `periodo.competencia` | texto `AAAA-MM` | Competência declarada | Sim |
| `periodo.inicio` | data `AAAA-MM-DD` | Primeiro dia elegível | Sim |
| `periodo.fim` | data `AAAA-MM-DD` | Último dia elegível | Sim |
| `despesas` | lista | Lançamentos na ordem em que foram recebidos | Sim |
| `despesas[].id` | texto não vazio e único | Identificador do lançamento | Sim |
| `despesas[].data` | data `AAAA-MM-DD` | Data da despesa | Sim |
| `despesas[].categoria` | texto | Categoria informada | Sim |
| `despesas[].descricao` | texto não vazio | Descrição informada | Sim |
| `despesas[].fornecedor` | texto não vazio | Fornecedor informado | Sim |
| `despesas[].valor` | número finito | Valor em reais | Sim |
| `despesas[].tem_nota_fiscal` | booleano | Existência de nota fiscal | Sim |

O período é válido somente quando `inicio` não é posterior a `fim` e ambas as
datas pertencem ao mês indicado em `competencia`. Campo ausente, tipo incorreto,
data impossível, identificador de despesa repetido ou período inválido torna o
documento inteiro inválido. Nesse caso, nenhum cálculo é produzido e o erro deve
identificar o campo ou a condição inválida.

## 5. Contrato de saída

Quando a entrada é válida, a saída contém exatamente um resultado, preserva a
ordem original das despesas e usa textos monetários com duas casas decimais para
evitar perda de precisão.

| Campo | Tipo | Significado |
|---|---|---|
| `politica_versao` | texto | Versão da política aplicada; nesta spec, `3` |
| `colaborador` | objeto | Cópia dos três campos do colaborador |
| `periodo` | objeto | Cópia dos três campos do período |
| `resumo.quantidade_despesas` | inteiro | Quantidade recebida |
| `resumo.total_solicitado` | texto monetário | Soma dos valores normalizados maiores que zero |
| `resumo.total_reembolsavel` | texto monetário | Soma dos valores reembolsáveis |
| `resumo.total_nao_reembolsavel` | texto monetário | `total_solicitado - total_reembolsavel` |
| `resumo.quantidade_aprovadas` | inteiro | Itens reembolsados integralmente |
| `resumo.quantidade_parciais` | inteiro | Itens com reembolso maior que zero e menor que o solicitado |
| `resumo.quantidade_rejeitadas` | inteiro | Itens com reembolso igual a zero |
| `decisoes` | lista | Uma decisão por despesa, na ordem da entrada |
| `decisoes[].id` | texto | ID original da despesa |
| `decisoes[].status` | enum | `APROVADA`, `PARCIAL` ou `REJEITADA` |
| `decisoes[].valor_original` | texto | Valor recebido, sem arredondamento |
| `decisoes[].valor_normalizado` | texto monetário | Valor após a regra de precisão |
| `decisoes[].valor_reembolsavel` | texto monetário | Valor pago para o item |
| `decisoes[].valor_nao_reembolsavel` | texto monetário | Parte positiva solicitada que não será paga |
| `decisoes[].codigo_motivo` | enum | Motivo principal da decisão |
| `decisoes[].justificativa` | texto | Explicação legível e específica |
| `decisoes[].regras_aplicadas` | lista de textos | IDs das regras relevantes |

Os códigos de motivo permitidos são `APROVADA_INTEGRAL`, `LIMITE_PARCIAL`,
`LIMITE_ESGOTADO`, `FORA_DA_COMPETENCIA`, `CATEGORIA_NAO_COBERTA`,
`VALOR_NAO_POSITIVO`, `DUPLICATA` e `NOTA_FISCAL_AUSENTE`.

Exemplo mínimo de saída:

```json
{
  "politica_versao": "3",
  "colaborador": {"id": "c-1", "nome": "Ana", "centro_custo": "CC-1"},
  "periodo": {"competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31"},
  "resumo": {
    "quantidade_despesas": 1,
    "total_solicitado": "72.50",
    "total_reembolsavel": "60.00",
    "total_nao_reembolsavel": "12.50",
    "quantidade_aprovadas": 0,
    "quantidade_parciais": 1,
    "quantidade_rejeitadas": 0
  },
  "decisoes": [{
    "id": "d-1",
    "status": "PARCIAL",
    "valor_original": "72.5",
    "valor_normalizado": "72.50",
    "valor_reembolsavel": "60.00",
    "valor_nao_reembolsavel": "12.50",
    "codigo_motivo": "LIMITE_PARCIAL",
    "justificativa": "Reembolso limitado a R$ 60,00 para alimentação em 2026-07-03.",
    "regras_aplicadas": ["RN-007", "RN-010"]
  }]
}
```

## 6. Regras de negócio

### RN-001 — Validade do documento

**Regra:** a entrada deve cumprir integralmente o contrato da seção 4. Entrada
inválida encerra o processamento sem resultado parcial.

**Origem:** interface fixa do desafio.

**Aceite:** dois itens com o mesmo `id` produzem erro de entrada e nenhum JSON de
resultado.

### RN-002 — Período de competência

**Regra:** uma despesa é elegível quanto à data quando sua data pertence ao
intervalo fechado de `periodo.inicio` até `periodo.fim`. Os dois extremos estão
incluídos. Item fora desse intervalo é rejeitado.

**Origem:** política do RH, item 7.

**Aceite:** no período de 2026-07-01 a 2026-07-31, despesas nessas duas datas são
elegíveis e uma despesa em 2026-04-15 é rejeitada.

### RN-003 — Categorias cobertas

**Regra:** depois de remover espaços nas extremidades e ignorar diferenças entre
maiúsculas e minúsculas, somente `alimentacao`, `transporte_urbano` e
`hospedagem` são cobertas. Outras categorias são rejeitadas.

**Origem:** política do RH, item 9.

**Aceite:** `ALIMENTACAO` é tratada como `alimentacao`; `coworking` é rejeitada.

### RN-004 — Valores não positivos

**Regra:** valor igual a zero ou negativo não gera crédito nem reduz o consumo de
limite. O item é rejeitado e contribui com zero para os totais solicitado,
reembolsável e não reembolsável.

**Origem:** decisão necessária porque a entrada contém valor negativo e a
política não define estornos.

**Aceite:** uma despesa de R$ -45,00 é rejeitada com reembolso R$ 0,00 e não
altera o limite disponível do dia.

### RN-005 — Nota fiscal

**Regra:** item cujo valor normalizado seja estritamente maior que R$ 100,00 é
rejeitado quando `tem_nota_fiscal` for falso. A verificação considera o valor
solicitado antes de qualquer limite de categoria.

**Origem:** política do RH, item 5.

**Aceite:** R$ 100,00 sem nota continua elegível; R$ 100,01 sem nota é rejeitado,
mesmo quando o limite da categoria seria menor que R$ 100,01.

### RN-006 — Duplicatas

**Regra:** despesas formam uma duplicata quando, após normalização, têm a mesma
data, categoria, descrição, fornecedor e valor. A primeira ocorrência segue o
processamento normal; cada ocorrência posterior é rejeitada. Diferenças apenas
de espaços nas extremidades ou de maiúsculas/minúsculas em categoria, descrição
e fornecedor não tornam os itens distintos.

**Origem:** política do RH, item 8.

**Aceite:** entre `d-006` e `d-007` do exemplo, `d-006` segue o processamento e
`d-007` é rejeitada como duplicata.

### RN-007 — Limite diário de alimentação

**Regra:** a soma reembolsável de alimentação por data é limitada a R$ 60,00.

**Origem:** política do RH, item 1.

**Aceite:** itens elegíveis de R$ 72,50 e R$ 38,00 na mesma data recebem, juntos,
R$ 60,00.

### RN-008 — Limite diário de transporte urbano

**Regra:** a soma reembolsável de transporte urbano por data é limitada a
R$ 80,00.

**Origem:** política do RH, item 2.

**Aceite:** um item elegível de R$ 100,00 recebe R$ 80,00; outro item elegível
posterior na mesma data recebe somente o saldo que ainda existir.

### RN-009 — Limite de hospedagem

**Regra:** cada lançamento de hospedagem representa exatamente uma diária e tem
limite de R$ 250,00. Texto como “2 diárias” ou “3 noites” não altera essa
quantidade.

**Origem:** política do RH, item 3, aplicada com o dado disponível na entrada.

**Aceite:** uma hospedagem elegível de R$ 480,00 recebe R$ 250,00, ainda que sua
descrição mencione duas diárias.

### RN-010 — Reembolso parcial e alocação

**Regra:** quando um limite é ultrapassado, paga-se o saldo disponível e recusa-se
o excedente. Para limites diários, despesas elegíveis consomem o limite na ordem
em que aparecem na entrada. Um item que recebe o valor inteiro é `APROVADA`; um
item que recebe parte é `PARCIAL`; um item que recebe zero é `REJEITADA`.

**Origem:** política do RH, item 4.

**Aceite:** para duas alimentações de R$ 40,00 na mesma data, a primeira recebe
R$ 40,00 e a segunda R$ 20,00.

### RN-011 — Limites de viagem

**Regra:** como o contrato de entrada não informa se o colaborador está em
viagem, toda execução aplica os limites básicos, sem acréscimo de 50%.

**Origem:** política do RH, item 6, e ausência do dado necessário na interface.

**Aceite:** nenhuma combinação dos campos atuais ativa limite ampliado.

### RN-012 — Precisão monetária

**Regra:** cada valor recebido é arredondado para centavos antes da aplicação de
qualquer outra regra, usando o centavo mais próximo; empate de meio centavo é
arredondado para longe de zero. Todos os cálculos posteriores usam o valor
normalizado.

**Origem:** decisão necessária porque a entrada admite números com mais de duas
casas decimais.

**Aceite:** R$ 33,333 torna-se R$ 33,33; R$ 33,335 torna-se R$ 33,34.

### RN-013 — Explicação e reconciliação

**Regra:** toda despesa válida de entrada gera exatamente uma decisão. A soma das
quantidades por status equivale à quantidade de despesas, e
`total_solicitado = total_reembolsavel + total_nao_reembolsavel`.

**Origem:** necessidade de auditoria do processo.

**Aceite:** o resultado do arquivo de exemplo contém 14 decisões, na mesma ordem
dos 14 itens, e seus totais reconciliam.

## 7. Ambiguidades identificadas e decisões

### AMB-001 — Unidade dos limites diários

**Texto original do RH:** “Alimentação tem limite de R$ 60 por dia” e
“Transporte urbano tem limite de R$ 80 por dia”.

**O que não está claro:** o limite poderia valer para cada item ou para a soma da
categoria no dia.

**Decisão:** vale para a soma de todos os itens da categoria na mesma data.

**Justificativa:** “por dia” define uma unidade temporal compartilhada, não uma
unidade por comprovante.

**Regras afetadas:** RN-007 e RN-008.

### AMB-002 — Significado de reembolso parcial

**Texto original do RH:** “Despesas acima do limite são reembolsadas parcialmente.”

**O que não está claro:** pagar até o limite ou recusar o item inteiro.

**Decisão:** pagar até o saldo do limite e recusar apenas o excedente.

**Justificativa:** é a leitura literal de “parcialmente” e evita perder a parcela
expressamente coberta pela política.

**Regra afetada:** RN-010.

### AMB-003 — Fronteira da nota fiscal

**Texto original do RH:** “Nota fiscal é obrigatória acima de R$ 100.”

**O que não está claro:** se R$ 100,00 também exige nota.

**Decisão:** somente valores normalizados maiores que R$ 100,00 exigem nota.

**Justificativa:** “acima” é uma comparação estrita; “a partir de” incluiria a
fronteira.

**Regra afetada:** RN-005.

### AMB-004 — Base da verificação de nota fiscal

**Texto original do RH:** “Nota fiscal é obrigatória acima de R$ 100.”

**O que não está claro:** comparar o valor solicitado ou o valor já reduzido pelo
limite da categoria.

**Decisão:** comparar o valor solicitado normalizado, antes de aplicar limites.

**Justificativa:** a obrigação documental diz respeito à despesa realizada, não
ao montante que a empresa decide reembolsar.

**Regra afetada:** RN-005.

### AMB-005 — Identificação de viagem

**Texto original do RH:** “Colaborador em viagem tem limites ampliados em 50%.”

**O que não está claro:** o que caracteriza viagem e como identificá-la sem um
campo de entrada.

**Decisão:** com o contrato atual, nenhum item recebe ampliação.

**Justificativa:** aplicar 50% com base em descrição, fornecedor ou categoria
seria inventar um fato não informado.

**Regra afetada:** RN-011.

### AMB-006 — Quantidade de diárias

**Texto original do RH:** “Hospedagem tem limite de R$ 250 por diária.”

**O que não está claro:** a entrada não contém quantidade de diárias, embora a
descrição possa mencionar noites.

**Decisão:** cada lançamento representa uma diária; a descrição não é usada para
extrair quantidade.

**Justificativa:** texto livre não é um contrato confiável para cálculo e pode
conter números sem relação com a quantidade de diárias.

**Regra afetada:** RN-009.

### AMB-007 — Critério de duplicidade

**Texto original do RH:** “Duplicatas devem ser tratadas.”

**O que não está claro:** quais campos tornam dois lançamentos duplicados.

**Decisão:** mesma data, categoria, descrição, fornecedor e valor, comparados
após as normalizações declaradas.

**Justificativa:** o ID identifica o lançamento, não a transação; os demais
campos formam uma identidade de negócio suficientemente conservadora.

**Regra afetada:** RN-006.

### AMB-008 — Tratamento de duplicatas

**Texto original do RH:** “Duplicatas devem ser tratadas.”

**O que não está claro:** rejeitar todas, somar uma vez ou escolher uma ocorrência.

**Decisão:** processar a primeira ocorrência e rejeitar as posteriores.

**Justificativa:** preserva uma solicitação legítima e impede pagamento repetido
no mesmo lote.

**Regra afetada:** RN-006.

### AMB-009 — Valores negativos e zero

**Texto original do RH:** a política não menciona estornos, mas a entrada de
referência contém um valor negativo.

**O que não está claro:** se o valor reduz limites, reduz o total ou cria crédito.

**Decisão:** valor não positivo é rejeitado e tem contribuição monetária zero.

**Justificativa:** não há vínculo com uma despesa original que permita aplicar o
estorno com segurança.

**Regra afetada:** RN-004.

### AMB-010 — Capitalização das categorias

**Texto original do RH:** a política nomeia categorias, mas não define formato.

**O que não está claro:** se `ALIMENTACAO` é diferente de `alimentacao`.

**Decisão:** espaços externos e capitalização são ignorados; acentos, grafias e
sinônimos não são corrigidos.

**Justificativa:** capitalização não muda o significado, enquanto corrigir grafia
ou sinônimos exigiria uma lista não fornecida.

**Regra afetada:** RN-003.

### AMB-011 — Precisão e arredondamento

**Texto original do RH:** a política usa centavos, mas não define valores com
frações menores; a entrada contém R$ 33,333.

**O que não está claro:** rejeitar, truncar ou arredondar, e em qual momento.

**Decisão:** arredondar cada valor para centavos, pelo meio para longe de zero,
antes das demais regras.

**Justificativa:** preserva a unidade monetária e evita que a ordem das operações
mude o resultado.

**Regra afetada:** RN-012.

### AMB-012 — Distribuição do limite diário

**Texto original do RH:** a política não diz qual item recebe o limite quando o
total diário excede o teto.

**O que não está claro:** usar ordem da entrada, menor valor, maior valor ou rateio.

**Decisão:** consumir o limite na ordem dos lançamentos recebidos.

**Justificativa:** é determinístico, auditável e não inventa prioridade por valor.

**Regra afetada:** RN-010.

### AMB-013 — Fronteiras da competência

**Texto original do RH:** “Despesas devem ser lançadas dentro do período de
competência.”

**O que não está claro:** se as datas inicial e final pertencem ao período e qual
dos três campos do período é a referência operacional.

**Decisão:** usar o intervalo fechado `inicio`–`fim` e exigir que ele seja
coerente com `competencia`.

**Justificativa:** os campos de data fornecem fronteiras verificáveis; validar a
competência evita contratos contraditórios.

**Regras afetadas:** RN-001 e RN-002.

### AMB-014 — Fins de semana e plantões

**Texto original do RH:** a política não restringe dias da semana; a entrada cita
“sábado — plantão”.

**O que não está claro:** se fins de semana precisam de tratamento especial.

**Decisão:** dia da semana, feriado e plantão não alteram elegibilidade nem limite.

**Justificativa:** criar uma restrição ausente recusaria despesas sem base na
política recebida.

**Regras afetadas:** RN-007 a RN-010.

### AMB-015 — Precedência entre recusas

**Texto original do RH:** várias regras podem atingir o mesmo item, mas a política
não define qual justificativa prevalece.

**O que não está claro:** por exemplo, um item pode ser duplicado, sem nota e fora
da competência ao mesmo tempo.

**Decisão:** aplicar a ordem da seção 9 e registrar como motivo principal a
primeira causa terminal encontrada.

**Justificativa:** uma precedência explícita torna o resultado determinístico e
permite reproduzir a decisão.

**Regras afetadas:** RN-002 a RN-010.

## 8. Casos de borda

| Caso | Entrada | Resultado esperado | Regras |
|---|---|---|---|
| Limite compartilhado | Alimentação de R$ 72,50 e R$ 38,00 na mesma data | R$ 60,00 no total; primeiro item parcial e segundo rejeitado | RN-007, RN-010 |
| Fronteira documental | R$ 100,00 sem nota | Não é recusada pela regra de nota | RN-005 |
| Um centavo acima | R$ 100,01 sem nota | Rejeitada antes do limite de categoria | RN-005 |
| Duplicata | `d-006` e `d-007` do exemplo | Primeira processada; segunda rejeitada | RN-006 |
| Fora do período | 2026-04-15 em competência de julho | Rejeitada | RN-002 |
| Valor negativo | R$ -45,00 | Rejeitada; contribuição zero aos totais | RN-004 |
| Múltiplas noites em texto | Hospedagem de R$ 480,00 com “2 diárias” | Uma diária; R$ 250,00 reembolsáveis | RN-009 |
| Categoria em maiúsculas | `ALIMENTACAO` | Tratada como `alimentacao` | RN-003 |
| Fração de centavo | R$ 33,333 | Normalizada para R$ 33,33 | RN-012 |
| Último dia | Despesa em `periodo.fim` | Data elegível | RN-002 |
| Fim de semana | Alimentação em sábado | Mesmas regras de um dia útil | RN-007 |
| Limite já esgotado | Segundo item após consumir todo o teto diário | Rejeitado com `LIMITE_ESGOTADO` | RN-010 |

## 9. Ordem de aplicação das regras

Para cada item, preservando a ordem da entrada:

1. normalizar valor e textos usados nas comparações;
2. rejeitar data fora da competência;
3. rejeitar categoria não coberta;
4. rejeitar valor não positivo;
5. rejeitar ocorrência duplicada;
6. rejeitar falta de nota fiscal quando obrigatória;
7. aplicar o limite da categoria e o saldo diário, quando houver;
8. produzir a decisão e atualizar os totais.

Um item rejeitado não consome limite. A primeira ocorrência de uma assinatura de
duplicidade é registrada após passar pelas regras 2 a 4; portanto, mesmo que seja
recusada depois por falta de nota, uma repetição posterior continua sendo
duplicata.

## 10. Critérios de aceite

O sistema base está pronto quando:

- [ ] aceita a interface `calcular --input <arquivo> --output <arquivo>`;
- [ ] processa o arquivo de exemplo e gera 14 decisões na ordem original;
- [ ] implementa RN-001 a RN-013 exatamente como descritas;
- [ ] cobre cada ambiguidade AMB-001 a AMB-015 com decisão verificável;
- [ ] produz saída conforme a seção 5 e com totais reconciliados;
- [ ] não cria nem substitui o arquivo de saída quando a entrada é inválida;
- [ ] retorna sucesso somente quando o resultado foi gravado por completo;
- [ ] possui ao menos um teste automatizado por regra e por caso de borda;
- [ ] pode ser executado e testado seguindo apenas o README.

## 11. Questões em aberto

- A política prevê ampliação em viagem, mas o contrato fixo não fornece esse dado.
  Nesta versão aplica-se RN-011. Uma futura mudança do contrato deverá primeiro
  alterar esta spec e registrar impactos no `DECISIONS.md`.
- A entrada não informa quantidade de diárias. Nesta versão aplica-se RN-009. A
  decisão deve ser revista se surgir um campo estruturado para a quantidade.

