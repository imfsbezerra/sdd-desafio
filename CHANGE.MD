# Mudança de requisito — Política de Reembolso v4

Bom dia. O RH revisou a política. Vigência imediata, retroativa à competência atual.

## Comunicado do RH — Política de Reembolso v4

Após auditoria interna, a política deixa de ser única para toda a empresa.

### A. Limites por centro de custo

Os limites passam a variar por centro de custo. Os limites não são mais
constantes. Cada centro de custo tem a sua tabela, mantida pelo financeiro num
arquivo à parte, e ela muda sem aviso. O motor precisa ler a política de fora,
não de dentro do código.

A tabela vigente está em `politica-v4.json`.

Observações que o financeiro fez questão de incluir:

- `CC-COMERCIAL` tem uma categoria nova, `representacao`, que não existia na v3 —
  limite de R$ 300 por dia.
- `CC-ENG-PLATAFORMA` não reembolsa hospedagem de forma alguma.
- Alguns centros de custo não têm entrada na tabela. Nesse caso, aplica-se a
  política padrão.

### B. Despesas internacionais

Colaboradores em viagem internacional lançam despesas em moeda estrangeira. A
entrada agora pode trazer um campo `moeda` (ISO 4217). Quando ausente, assume-se
`BRL`.

A conversão usa a taxa da data da despesa, não a taxa de hoje. As taxas estão em
`cambio.json`.

Os limites da política são sempre em BRL. Uma despesa em EUR é convertida antes
de ser comparada ao limite.

### C. Fila de aprovação manual — opcional

Itens cujo valor reembolsável passe de R$ 500 não são mais aprovados
automaticamente. Eles entram em estado de pendência aguardando aprovação do
gestor. O resultado deixa de ser apenas um valor: cada item passa a ter um estado.

## O que se espera de você agora

Nada de heroísmo. O que se avalia é o caminho, não a velocidade:

1. Primeiro a spec. Leia a mudança, identifique o que ela quebra na `spec.md`, e
   atualize a spec — incluindo as ambiguidades novas que este comunicado traz (e
   traz várias).
2. Registre no `DECISIONS.md`: o que mudou, por quê, quais requisitos foram
   invalidados e quais tasks precisam ser refeitas.
3. Crie novas tasks no `tasks.md`, continuando a numeração de onde parou.
4. Só então altere o código. Os commits devem referenciar as novas tasks, como
   antes.
5. Anote enquanto faz: quantos arquivos foram tocados manualmente, o que a
   arquitetura absorveu de graça e o que resistiu. Isso deve entrar no relatório.

O item C é opcional de propósito. Se ele não for implementado, não há perda de
pontos. Deixar a spec inconsistente para implementá-lo causa perda.

## Ambiguidades que este comunicado também traz

Elas não estão listadas. A Política v4 é tão ambígua quanto a v3. Devem ser
tratadas com o mesmo processo: identificar, decidir, justificar e registrar.

> Dica: a frase “aplica-se a política padrão” e a frase “a taxa da data da
> despesa” escondem, cada uma, pelo menos uma decisão que precisará ser tomada.

## Arquivos que acompanham o envelope

Os quatro arquivos devem ser guardados no repositório — sugestão:
`exemplos/envelope/` — e commitados como parte da entrega:

- `politica-v4.json` — tabela de limites por centro de custo;
- `cambio.json` — taxas de câmbio por data;
- `despesas-envelope.json` — conjunto de despesas que exercita as mudanças;
- `despesas-envelope-cc-desconhecido.json` — colaborador de um centro de custo
  ausente da tabela.

## `cambio.json`

```json
{
  "moeda_base": "BRL",
  "fonte": "Banco Central - PTAX de fechamento",
  "observacao": "Cotacoes publicadas apenas em dias uteis bancarios.",
  "taxas": {
    "2026-07-13": { "USD": 5.42, "EUR": 5.91 },
    "2026-07-14": { "USD": 5.44, "EUR": 5.93 },
    "2026-07-15": { "USD": 5.39, "EUR": 5.88 },
    "2026-07-16": { "USD": 5.41, "EUR": 5.90 },
    "2026-07-17": { "USD": 5.47, "EUR": 5.96 },
    "2026-07-20": { "USD": 5.50, "EUR": 6.01 },
    "2026-07-21": { "USD": 5.48, "EUR": 5.99 },
    "2026-07-22": { "USD": 5.45, "EUR": 5.95 },
    "2026-07-23": { "USD": 5.44, "EUR": 5.94 },
    "2026-07-24": { "USD": 5.46, "EUR": 5.97 },
    "2026-07-27": { "USD": 5.52, "EUR": 6.03 },
    "2026-07-28": { "USD": 5.51, "EUR": 6.02 }
  }
}
```

## `despesas-envelope-cc-desconhecido.json`

```json
{
  "colaborador": {
    "id": "c-1103",
    "nome": "Dani Okonkwo",
    "centro_custo": "CC-SUPORTE-N2"
  },
  "periodo": {
    "competencia": "2026-07",
    "inicio": "2026-07-01",
    "fim": "2026-07-31"
  },
  "despesas": [
    {
      "id": "f-001",
      "data": "2026-07-16",
      "categoria": "alimentacao",
      "descricao": "Almoco",
      "fornecedor": "Padaria Uniao",
      "valor": 58.00,
      "tem_nota_fiscal": true
    },
    {
      "id": "f-002",
      "data": "2026-07-17",
      "categoria": "hospedagem",
      "descricao": "Pousada - 1 diaria",
      "fornecedor": "Pousada do Vale",
      "valor": 310.00,
      "tem_nota_fiscal": true
    },
    {
      "id": "f-003",
      "data": "2026-07-17",
      "categoria": "representacao",
      "descricao": "Jantar com fornecedor",
      "fornecedor": "Casa Trindade",
      "valor": 190.00,
      "moeda": "BRL",
      "tem_nota_fiscal": true
    },
    {
      "id": "f-004",
      "data": "2026-07-21",
      "categoria": "transporte_urbano",
      "descricao": "Corrida",
      "fornecedor": "TaxiApp",
      "valor": 12.00,
      "moeda": "USD",
      "tem_nota_fiscal": true
    }
  ]
}
```

## `despesas-envelope.json`

```json
{
  "colaborador": {
    "id": "c-0912",
    "nome": "Rafael Nkemelu",
    "centro_custo": "CC-COMERCIAL"
  },
  "periodo": {
    "competencia": "2026-07",
    "inicio": "2026-07-01",
    "fim": "2026-07-31"
  },
  "despesas": [
    {
      "id": "e-001",
      "data": "2026-07-13",
      "categoria": "representacao",
      "descricao": "Jantar com prospect - fechamento de contrato",
      "fornecedor": "Casa Trindade",
      "valor": 340.00,
      "moeda": "BRL",
      "tem_nota_fiscal": true
    },
    {
      "id": "e-002",
      "data": "2026-07-14",
      "categoria": "alimentacao",
      "descricao": "Almoco - Lisboa",
      "fornecedor": "Taberna do Chiado",
      "valor": 22.00,
      "moeda": "EUR",
      "tem_nota_fiscal": true
    },
    {
      "id": "e-003",
      "data": "2026-07-15",
      "categoria": "alimentacao",
      "descricao": "Cafe e sanduiche",
      "fornecedor": "Padaria Lisboa",
      "valor": 14.50,
      "moeda": "EUR",
      "tem_nota_fiscal": false
    },
    {
      "id": "e-004",
      "data": "2026-07-18",
      "categoria": "alimentacao",
      "descricao": "Jantar de sabado",
      "fornecedor": "Cervejaria Ramiro",
      "valor": 30.00,
      "moeda": "EUR",
      "tem_nota_fiscal": true
    },
    {
      "id": "e-005",
      "data": "2026-07-20",
      "categoria": "transporte_urbano",
      "descricao": "Corridas do dia",
      "fornecedor": "Bolt",
      "valor": 40.00,
      "moeda": "USD",
      "tem_nota_fiscal": false
    },
    {
      "id": "e-006",
      "data": "2026-07-21",
      "categoria": "representacao",
      "descricao": "Almoco com parceiro - Londres",
      "fornecedor": "The Ivy",
      "valor": 55.00,
      "moeda": "GBP",
      "tem_nota_fiscal": true
    },
    {
      "id": "e-007",
      "data": "2026-07-22",
      "categoria": "hospedagem",
      "descricao": "Hotel Londres - 3 noites",
      "fornecedor": "Premier Inn",
      "valor": 1200.00,
      "moeda": "BRL",
      "tem_nota_fiscal": true
    },
    {
      "id": "e-008",
      "data": "2026-07-23",
      "categoria": "alimentacao",
      "descricao": "Almoco de equipe",
      "fornecedor": "Restaurante Tavola",
      "valor": 95.00,
      "moeda": "BRL",
      "tem_nota_fiscal": true
    },
    {
      "id": "e-009",
      "data": "2026-07-24",
      "categoria": "coworking",
      "descricao": "Sala de reuniao para demo",
      "fornecedor": "HubOffice",
      "valor": 120.00,
      "moeda": "BRL",
      "tem_nota_fiscal": true
    },
    {
      "id": "e-010",
      "data": "2026-07-27",
      "categoria": "alimentacao",
      "descricao": "Almoco",
      "fornecedor": "Bistro Central",
      "valor": 88.00,
      "tem_nota_fiscal": true
    }
  ]
}
```

## `politica-v4.json`

```json
{
  "versao": "v4",
  "vigencia": "2026-07-01",
  "moeda_base": "BRL",
  "padrao": {
    "alimentacao": { "limite": 60.00, "periodicidade": "dia" },
    "transporte_urbano": { "limite": 80.00, "periodicidade": "dia" },
    "hospedagem": { "limite": 250.00, "periodicidade": "diaria" }
  },
  "centros_custo": {
    "CC-ENG-PLATAFORMA": {
      "alimentacao": { "limite": 75.00, "periodicidade": "dia" },
      "transporte_urbano": { "limite": 80.00, "periodicidade": "dia" },
      "hospedagem": {
        "limite": 0.00,
        "periodicidade": "diaria",
        "observacao": "nao reembolsavel"
      }
    },
    "CC-COMERCIAL": {
      "alimentacao": { "limite": 90.00, "periodicidade": "dia" },
      "transporte_urbano": { "limite": 150.00, "periodicidade": "dia" },
      "hospedagem": { "limite": 400.00, "periodicidade": "diaria" },
      "representacao": { "limite": 300.00, "periodicidade": "dia" }
    },
    "CC-ADM": {
      "alimentacao": { "limite": 45.00, "periodicidade": "dia" },
      "transporte_urbano": { "limite": 60.00, "periodicidade": "dia" }
    }
  },
  "nota_fiscal_obrigatoria_acima_de": 100.00,
  "acrescimo_em_viagem_percentual": 50
}
```

