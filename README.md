# Motor de Cálculo de Reembolso

CLI que lê as despesas de um colaborador, aplica a Política de Reembolso v3 e
gera uma decisão justificada para cada lançamento.

## Requisitos

- Python 3.11 ou superior.
- Nenhuma dependência externa.

## Executar

Na raiz do repositório:

```bash
python -m src.cli calcular --input exemplos/despesas-exemplo.json --output resultado.json
```

Em caso de sucesso, o comando retorna código `0` e cria `resultado.json`. Entrada
inválida retorna `2`; falha operacional retorna `1`. Uma falha não substitui um
arquivo de saída anterior.

Para o exemplo oficial, o resumo esperado é:

```json
{
  "quantidade_despesas": 14,
  "total_solicitado": "1861.84",
  "total_reembolsavel": "585.43",
  "total_nao_reembolsavel": "1276.41",
  "quantidade_aprovadas": 3,
  "quantidade_parciais": 4,
  "quantidade_rejeitadas": 7
}
```

## Testar

```bash
python -m unittest discover -s tests -v
```

A suíte cobre as regras individualmente, a precedência entre recusas, a saída
completa do exemplo e a CLI ponta a ponta.

## Contratos e decisões

- [Spec](specs/001-motor-reembolso/spec.md): comportamento, saída, ambiguidades e
  critérios de aceite.
- [Plano](specs/001-motor-reembolso/plan.md): stack, arquitetura e estratégia de
  testes.
- [Tasks](specs/001-motor-reembolso/tasks.md): rastreabilidade entre regras,
  commits e testes.
- [Decisões](specs/001-motor-reembolso/DECISIONS.md): mudanças na spec e seus
  impactos.

Valores monetários da saída são textos com duas casas decimais. Isso evita que um
consumidor converta dinheiro implicitamente para ponto flutuante.

## Limitações conhecidas da versão base

- A entrada não informa viagem; portanto, não há ampliação de 50% nos limites.
- Cada lançamento de hospedagem representa uma diária; números na descrição não
  são interpretados.
- Valores iguais a zero ou negativos são rejeitados e não criam crédito.

Essas decisões são deliberadas e estão justificadas na spec, não são limitações
ocultas da implementação.

