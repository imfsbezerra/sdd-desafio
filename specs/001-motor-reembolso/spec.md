# Spec — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Status:** em aprovação · **Última alteração:** 2026-10-05

> **Regra de ouro deste arquivo:** ele descreve o QUÊ e o PORQUÊ. Nenhuma linha
> aqui pode citar linguagem, biblioteca, classe, função ou estrutura de pasta.
> Se apareceu solução, o lugar dela é o `plan.md`.
>
> **Teste de aceitação da própria spec:** uma pessoa que nunca viu o projeto
> consegue, lendo só este arquivo, verificar se o sistema está correto?

---

## 1. Problema

O RH processa reembolsos de despesas manualmente, item por item. O processo é lento, propenso a erros e não deixa trilha de decisão. Colaboradores não sabem por que foram recusados ou parcialmente reembolsados. Auditar decisões passadas é impossível.

## 2. Objetivo

Automatizar o cálculo de reembolso de despesas contra a política, gerando uma lista de decisões justificadas para cada item e resumo por categoria.

## 3. Fora de escopo

- Integração com sistemas de folha de pagamento ou banco de dados
- Interface gráfica — apenas CLI
- Autenticação ou controle de permissões
- Processamento de múltiplos colaboradores em lote (apenas um por execução)
- Sugestões de mudança de política
- Armazenamento persistente de histórico de processamento

---

## 4. Entrada e saída

**Entrada:** arquivo JSON conforme `exemplos/despesas-exemplo.json`. 

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `colaborador.id` | string | Identificador único do colaborador | Sim |
| `colaborador.nome` | string | Nome do colaborador | Sim |
| `colaborador.centro_custo` | string | Centro de custo para alocação | Sim |
| `periodo.competencia` | string | Período no formato YYYY-MM | Sim |
| `periodo.inicio` | string | Data de início (YYYY-MM-DD) | Sim |
| `periodo.fim` | string | Data de fim (YYYY-MM-DD) | Sim |
| `despesas[].id` | string | ID único da despesa | Sim |
| `despesas[].data` | string | Data da despesa (YYYY-MM-DD) | Sim |
| `despesas[].categoria` | string | Uma de: alimentacao, transporte_urbano, hospedagem | Sim |
| `despesas[].descricao` | string | Descrição da despesa | Sim |
| `despesas[].fornecedor` | string | Nome do fornecedor/estabelecimento | Sim |
| `despesas[].valor` | number | Valor em R$, pode ser negativo (estorno) | Sim |
| `despesas[].tem_nota_fiscal` | boolean | Se possui nota fiscal | Sim |

**Saída:** arquivo JSON com este schema:

```json
{
  "sumario_processamento": {
    "colaborador_id": "c-0417",
    "colaborador_nome": "Marina Volpi",
    "periodo_competencia": "2026-07",
    "data_processamento": "2026-10-05T14:30:00Z",
    "total_despesas_submetidas": 1850.84,
    "total_reembolsavel": 1234.50,
    "total_nao_reembolsavel": 616.34,
    "despesas_processadas": 14,
    "despesas_rejeitadas": 2,
    "despesas_parciais": 3
  },
  "resultado_por_categoria": {
    "alimentacao": {
      "total_submetido": 450.00,
      "total_reembolsavel": 300.00,
      "total_nao_reembolsavel": 150.00,
      "justificativa": "Limite diário de R$ 60 aplicado, com agregação por data"
    },
    "transporte_urbano": {
      "total_submetido": 200.01,
      "total_reembolsavel": 160.00,
      "total_nao_reembolsavel": 40.01,
      "justificativa": "Limite diário de R$ 80 aplicado"
    },
    "hospedagem": {
      "total_submetido": 1170.00,
      "total_reembolsavel": 700.00,
      "total_nao_reembolsavel": 470.00,
      "justificativa": "Limite por noite de R$ 250 aplicado"
    }
  },
  "decisoes_por_despesa": [
    {
      "id_despesa": "d-001",
      "data": "2026-07-03",
      "categoria": "alimentacao",
      "descricao": "Almoco com cliente",
      "valor_original": 72.50,
      "valor_reembolsavel": 60.00,
      "status": "PARCIAL",
      "motivo": "Limite diário de R$ 60 atingido. Excedente de R$ 12.50 não reembolsado.",
      "regras_aplicadas": ["RN-001", "RN-004"]
    }
  ]
}
```

---

## 5. Regras de negócio

### RN-001 — Limite diário de alimentação

**Regra:** O reembolso de despesas de alimentação em um mesmo dia é limitado a R$ 60,00. Se o total de despesas de alimentação em um dia exceder R$ 60, o valor excedente não é reembolsável.

**Origem:** Política do RH, item 1

**Aceite:** Entrada com duas refeições no mesmo dia (R$ 72,50 + R$ 38,00 = R$ 110,50) resulta em reembolso de R$ 60,00 total para esse dia, com R$ 50,50 rejeitado.

---

### RN-002 — Limite diário de transporte urbano

**Regra:** O reembolso de despesas de transporte urbano em um mesmo dia é limitado a R$ 80,00. Se o total de despesas de transporte urbano em um dia exceder R$ 80, o valor excedente não é reembolsável.

**Origem:** Política do RH, item 2

**Aceite:** Duas corridas de R$ 100,00 cada no mesmo dia (R$ 200,00 total) resultam em reembolso de R$ 80,00, com R$ 120,00 rejeitado.

---

### RN-003 — Limite por noite de hospedagem

**Regra:** O reembolso de despesas de hospedagem é limitado a R$ 250,00 por noite. Despesas lançadas como um único item especificando múltiplas noites devem ter seu valor dividido pelo número de noites; o resultado é comparado ao limite. Se ultrapassar, o reembolso é calculado como (número de noites × R$ 250,00).

**Origem:** Política do RH, item 3

**Aceite:** Uma despesa de R$ 480,00 descrita como "2 diárias" resulta em cálculo de R$ 240,00 por noite (dentro do limite), logo é totalmente reembolsada.

---

### RN-004 — Reembolso parcial por limite

**Regra:** Quando uma despesa ou agregado de despesas no período excede o limite, o sistema reembolsa até o limite e rejeita o excedente (não paga parcialmente o item individual; paga até o limite do dia/noite, depois para).

**Origem:** Política do RH, item 4

**Aceite:** Uma despesa de R$ 100,00 sozinha em um dia com limite de R$ 60,00 é reembolsada em R$ 60,00 (parcial).

---

### RN-005 — Nota fiscal obrigatória acima de R$ 100

**Regra:** Despesas com valor (absoluto) maior que R$ 100,00 sem nota fiscal não são reembolsáveis.

**Origem:** Política do RH, item 5

**Aceite:** Uma corrida de R$ 100,01 sem nota fiscal é rejeitada. Uma corrida de R$ 100,00 sem nota fiscal é aceita (não ultrapassa o limite).

---

### RN-006 — Estornos

**Regra:** Despesas com valor negativo (estornos/devoluções) reduzem o total do dia na categoria, permitindo reembolso adicional até o limite do dia se houver. Valores negativos puros (sem correspondência de despesa positiva) não geram crédito.

**Origem:** Política do RH, item 8 (duplicatas/tratamento especial)

**Aceite:** Dia com R$ 60,00 de alimentação e depois um estorno de -R$ 20,00 resulta em base de R$ 40,00, deixando R$ 20,00 de espaço no limite de R$ 60,00.

---

### RN-007 — Período de competência

**Regra:** Apenas despesas cuja data está dentro do intervalo `[periodo.inicio, periodo.fim]` são processadas. Despesas fora desse intervalo são rejeitadas com motivo "fora do período de competência".

**Origem:** Política do RH, item 7

**Aceite:** Uma despesa de abril em um período de julho é rejeitada.

---

### RN-008 — Duplicatas exatas

**Regra:** Se duas ou mais despesas têm idênticos: data, categoria, valor e fornecedor, apenas a primeira é reembolsada; as demais são rejeitadas com motivo "duplicata detectada".

**Origem:** Política do RH, item 8

**Aceite:** Duas despesas de R$ 54,90 no mesmo dia, mesma categoria, mesmo fornecedor (Bistro Central) — uma é aceita, a outra é rejeitada.

---

### RN-009 — Categorias válidas

**Regra:** Apenas as categorias alimentacao, transporte_urbano e hospedagem são reembolsáveis. Qualquer outra categoria é rejeitada com motivo "categoria não está na política de reembolso".

**Origem:** Política do RH, item 9

**Aceite:** Uma despesa com categoria "coworking" é rejeitada.

---

## 6. Ambiguidades identificadas e decisões

### AMB-001 — "R$ 60 por dia" — por dia ou por despesa?

**Texto original:** "Alimentação tem limite de R$ 60 por dia."

**O que não estava claro:** Se é R$ 60 por dia (total agregado) ou R$ 60 por despesa individual.

**Decisão:** R$ 60 por dia (agregado). Múltiplas refeições no mesmo dia têm seus valores somados, e o total não pode exceder R$ 60.

**Justificativa:** A palavra "dia" sugere período temporal, não itemização. Agregação por dia é mais restritiva (e portanto mais conservadora para a empresa), reduzindo o risco de reembolsos excessivos.

**Regra afetada:** RN-001

---

### AMB-002 — "Reembolsadas parcialmente" — até o limite ou rejeita tudo?

**Texto original:** "Despesas acima do limite são reembolsadas parcialmente."

**O que não estava claro:** Se é reembolso parcial (paga R$ 60 de uma despesa de R$ 100) ou rejeição total.

**Decisão:** Reembolso parcial. Sistema paga até o limite do dia/noite e rejeita o excedente.

**Justificativa:** "Parcialmente" denota divisão, não rejeição. Mais justo com o colaborador e aumenta satisfação.

**Regra afetada:** RN-004

---

### AMB-003 — "Acima de R$ 100" — R$ 100 é incluído?

**Texto original:** "Nota fiscal é obrigatória acima de R$ 100."

**O que não estava claro:** Se "acima" inclui R$ 100,00 exato ou começa a partir de R$ 100,01.

**Decisão:** Começa a partir de R$ 100,01. Despesas de R$ 100,00 exato não precisam de nota fiscal.

**Justificativa:** "Acima" em português tem interpretação limítrofe ambígua; escolhemos a leitura que protege o colaborador (mais permissiva). Importante: valores não-inteiros (R$ 100,01) requeiram nota fiscal.

**Regra afetada:** RN-005

---

### AMB-004 — "Em viagem" — o que caracteriza?

**Texto original:** "Colaborador em viagem tem limites ampliados em 50%."

**O que não estava claro:** Não há campo de entrada indicando se o colaborador está em viagem. Sem critério, não há forma de aplicar a regra.

**Decisão:** **Descartamos esta regra neste MVP.** Sem campo de entrada `em_viagem` na estrutura JSON, não é possível determinar quando aplicar. Entra no envelope (Dia 2).

**Justificativa:** SDD exige que a spec seja implementável com a entrada disponível. Requisitos sem dados de entrada são não-executáveis. Registrar agora evita tentativa de adivinhar.

**Regra afetada:** (nenhuma nesta versão — será AMB-X no envelope)

---

### AMB-005 — Duplicatas — qual deve ser rejeitada?

**Texto original:** "Duplicatas devem ser tratadas."

**O que não estava claro:** Se é rejeitar ambas, rejeitar a segunda, ou alguma heurística diferente.

**Decisão:** A primeira ocorrência é aceita (ou processada normalmente); a segunda e subsequentes são rejeitadas como duplicatas.

**Justificativa:** Lançamento duplo acidental é comum; preservar a primeira entrada é mais conservador. Colaborador pode investigar e corrigir.

**Regra afetada:** RN-008

---

### AMB-006 — Hospedagem — por noite ou por dia?

**Texto original:** "Hospedagem tem limite de R$ 250 por diária."

**O que não estava claro:** Se "diária" é por noite (período noturno) ou por dia (00:00 a 23:59). Alguns sistemas contam diferente.

**Decisão:** Uma diária = uma noite. Se descrito como "2 diárias", divide-se o valor por 2 noites.

**Justificativa:** "Diária" na hotelaria é a noite de pernoite. Padrão de mercado.

**Regra afetada:** RN-003

---

### AMB-007 — Estornos — negativo gera crédito?

**Texto original:** "Duplicatas devem ser tratadas." (implicitamente, há tratamento para ajustes/estornos)

**O que não estava claro:** Se um estorno (valor negativo) pode criar "espaço" no limite de um dia para mais reembolsos, ou se é apenas uma redução visual.

**Decisão:** Estornos reduzem o total consumido do limite do dia. Se um dia tem R$ 60,00 de alimentação e depois um estorno de -R$ 20,00, o consumo efetivo passa a R$ 40,00, liberando R$ 20,00 para mais reembolsos naquele dia.

**Justificativa:** Mais justo com o colaborador e reflete a realidade operacional (estorno é uma correção).

**Regra afetada:** RN-006

---

### AMB-008 — Sensibilidade a maiúsculas/minúsculas na categoria

**Texto original:** (não explicitado na política)

**O que não estava claro:** Se "ALIMENTACAO" (maiúscula) é o mesmo que "alimentacao" (minúscula).

**Decisão:** Categorias são **case-insensitive**. "ALIMENTACAO", "Alimentacao" e "alimentacao" são tratadas como a mesma categoria.

**Justificativa:** Evita rejeições por erro de tipagem do usuário. Normalização de dados é padrão em sistemas.

**Regra afetada:** RN-009

---

### AMB-009 — Precisão monetária — quantas casas decimais?

**Texto original:** (não explicitado)

**O que não estava claro:** Se valores como R$ 33,333 (três casas decimais) são aceitos ou arredondados.

**Decisão:** Valores são aceitos com até 2 casas decimais (centavos). Valores com mais casas decimais são arredondados para cima (teto) para 2 casas.

**Justificativa:** Centavos são a unidade mínima de moeda brasileira. Arredondar para cima protege o colaborador.

**Regra afetada:** (impacta todos os cálculos)

---

### AMB-010 — Hospedagem — como interpretar "2 diárias" no descritivo?

**Texto original:** "Hospedagem tem limite de R$ 250 por diária."

**O que não estava claro:** Como o sistema detecta que uma despesa de hospedagem se refere a múltiplas noites. A entrada não tem campo estruturado para isso.

**Decisão:** Na versão MVP, o sistema **não** interpreta automaticamente texto descritivo. Hospedagem de valor V é considerada 1 noite, e comparada contra R$ 250. Se o lançador deseja reembolsar 2 noites, deve lançar 2 despesas separadas ou lançar já convertido (ex: R$ 500 como "2 × R$ 250").

**Justificativa:** Parsing automático de texto livre é frágil e ambíguo. A entrada deve ser estruturada. Isso vai mudar no envelope (Dia 2) se for requisitado.

**Regra afetada:** RN-003

---

## 7. Casos de borda

| Caso | Entrada | Comportamento esperado | Regra |
|---|---|---|---|
| Duas refeições no mesmo dia | 2026-07-03: R$ 72,50 + R$ 38,00 | Total no dia = R$ 110,50; reembolso = R$ 60,00; rejeitado = R$ 50,50 | RN-001, RN-004 |
| Despesa exatamente no limite | 2026-07-06: R$ 60,00 (alimentação) | Reembolso integral = R$ 60,00 | RN-001 |
| Despesa de R$ 100,00 sem nota | 2026-07-06: R$ 100,00 (transporte) | Aceita (não ultrapassa R$ 100) | RN-005 |
| Despesa de R$ 100,01 sem nota | 2026-07-06: R$ 100,01 (transporte) | Rejeitada (exige nota fiscal) | RN-005 |
| Duplicata exata | d-006 e d-007 no exemplo | d-006 aceita, d-007 rejeitada | RN-008 |
| Categoria inválida | 2026-07-07: "coworking" | Rejeitada | RN-009 |
| Fora do período | 2026-04-15 (período é julho) | Rejeitada | RN-007 |
| Estorno | 2026-07-11: -R$ 45,00 (transporte) | Reduz consumo do dia; se houver espaço, libera reembolso | RN-006 |
| Categoria MAIÚSCULA | 2026-07-31: "ALIMENTACAO" | Tratada como "alimentacao" | RN-009 |
| Valor com 3 casas decimais | R$ 33,333 | Arredondado para R$ 33,34 | AMB-009 |
| Hospedagem múltiplas noites (texto) | "Airbnb 3 noites" R$ 690 | MVP: tratado como 1 noite, comparado contra R$ 250, excedente rejeitado | RN-003, AMB-010 |

---

## 8. Ordem de aplicação das regras

A sequência de processamento de cada despesa é:

1. **RN-007** — Verificar se está no período de competência. Se fora, REJEITAR e parar.
2. **RN-009** — Verificar se a categoria é válida. Se inválida, REJEITAR e parar.
3. **RN-005** — Verificar se valor > R$ 100 sem nota fiscal. Se sim, REJEITAR e parar.
4. **RN-008** — Verificar duplicata exata (data, categoria, valor, fornecedor). Se duplicata, REJEITAR e parar.
5. **RN-001/RN-002/RN-003** — Aplicar limites diários (alimentação, transporte) ou por noite (hospedagem). REEMBOLSAR até o limite, REJEITAR excedente.
6. **RN-006** — Se há estorno no mesmo dia, ajustar o total consumido e recalcular espaço disponível.

**Nota:** Duas despesas no mesmo dia com a mesma categoria têm seus valores agregados antes de aplicar o limite. A ordem numérica das despesas determina qual vai primeiro no limite (FIFO — first in, first out).

---

## 9. Critérios de aceite

O sistema está pronto quando:

- [ ] Processa um arquivo JSON conforme `exemplos/despesas-exemplo.json` sem erros
- [ ] Gera saída JSON com estrutura definida em seção 4, com todos os campos preenchidos
- [ ] Rejeita despesas fora do período de competência (RN-007)
- [ ] Rejeita categorias não-válidas (RN-009)
- [ ] Rejeita despesas > R$ 100 sem nota fiscal (RN-005)
- [ ] Detecta e rejeita duplicatas exatas (RN-008)
- [ ] Aplica limite diário de R$ 60 para alimentação (RN-001)
- [ ] Aplica limite diário de R$ 80 para transporte urbano (RN-002)
- [ ] Aplica limite de R$ 250 por noite para hospedagem (RN-003)
- [ ] Reembolsa parcialmente até o limite, rejeita excedente (RN-004)
- [ ] Processa estornos, reduzindo consumo do dia (RN-006)
- [ ] Normaliza categorias para minúsculas (AMB-008)
- [ ] Arredonda valores monetários para 2 casas decimais (AMB-009)
- [ ] Testes automatizados cobrem no mínimo um caso por regra
- [ ] Documentação está conforme spec.md, plan.md, tasks.md

---

## 10. O que fica em aberto

1. **Mudança de requisito esperada (envelope Dia 2):** Campo `em_viagem` deve ser adicionado à entrada JSON. Quando presente e true, os limites diários devem ser aumentados em 50% (exceto hospedagem, que fica em R$ 250). Esta mudança vai gerar novas tasks e pode afetar a ordem de aplicação das regras.

2. **Hospedagem com múltiplas noites — versão futura:** Caso o envelope exija parsing inteligente de "N diárias" ou "N noites" no campo descritivo, a spec vai mudar. MVP assume 1 noite por lançamento.

3. **Integração com terceiros:** Se houver integração com sistema de folha de pagamento ou banco de dados para validar centros de custo, isso entra como fase 2.

4. **Auditoria detalhada:** Versão futura pode incluir log de quem processou, quando, e com qual versão da política. Não está no MVP.

---

**Próximo passo:** Ver `plan.md` para decisões técnicas de implementação.
