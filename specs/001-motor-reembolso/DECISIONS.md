# Decisions — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Status:** documentado · **Última alteração:** 2026-10-05

> Log de decisões técnicas, ambiguidades resolvidas e trade-offs considerados.
> Este arquivo é o registro permanente do "por quê" por trás de cada escolha.

---

## DEC-001: Usar Decimal em vez de float para valores monetários

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Precisão garantida em cálculos monetários

**Problema:** Float em Python/JavaScript tem precisão limitada. Exemplo: `0.1 + 0.2 ≠ 0.3`.
Em transações financeiras, isso resulta em centavos perdidos.

**Decisão:** Usar `Decimal` do módulo `decimal` (Python).

**Alternativas consideradas:**
- Usar inteiros (centavos): Funciona, mas menos legível. Descartado.
- Usar strings: Impede operações matemáticas. Descartado.

**Implementação:** Todos os modelos `Despesa`, `DecisaoDespesa`, `ResultadoCategoria` usam `Decimal`.

---

## DEC-002: Processar despesas em ordem FIFO (first-in, first-out)

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Fairness com o colaborador

**Problema:** Quando o total de despesas num dia ultrapassa o limite, qual despesa fica com o reembolso?
Ordem importa: se processar maior-para-menor, reembolsos grandes são favorecidos.

**Decisão:** Processar na ordem de chegada (FIFO). Primeira despesa tem prioridade até o limite, depois para.

**Alternativas consideradas:**
- Maior-para-menor: Favorecia contas altas. Descartado (injusto).
- Menor-para-maior: Favorecia contas baixas. Descartado (injusto).
- Rateio proporcional: Complica cálculo e não mapeia bem a política. Descartado.

**Justificativa:** FIFO é simples, transparent e não discrimina por valor.

---

## DEC-003: Normalizar categoria para minúscula

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Robustez contra erros de entrada

**Problema:** Usuário pode lançar "ALIMENTACAO", "Alimentacao", "alimentacao".
Sem normalização, diferentes estilos de capitalização causariam rejeição.

**Decisão:** No carregamento, converter todas categorias para minúscula.

**Implementação:** `despesa.categoria = despesa.categoria.lower()` no loader.

**Benefício:** Reduz rejeições por tipografia, aumenta usabilidade.

---

## DEC-004: Arredondar valores monetários para cima (ROUND_UP)

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Proteção do colaborador

**Problema:** Valores com mais de 2 casas decimais (ex: R$ 33,333) aparecem em sistemas de conversão de moeda.
Precisa decidir se arredonda para cima ou para baixo.

**Decisão:** Arredondar para **cima** (ceiling). `Decimal('33.333').quantize(Decimal('0.01'), rounding=ROUND_UP)` = `Decimal('33.34')`.

**Justificativa:** Mais favorável ao colaborador. Se o sistema recebeu uma fracção, é justo reconhecê-la.

---

## DEC-005: Estornos reduzem consumo de limite do dia

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Equidade em ajustes

**Problema:** Se um colaborador recebeu uma duplicata e depois fez estorno (valor negativo), deve isso liberar espaço?
Exemplo: Dia com R$ 60 de alimentação, depois estorno de -R$ 20. Total = R$ 40. Pode gastar mais R$ 20 do limite?

**Decisão:** Sim. Estornos reduzem o consumo efetivo do limite.

**Implementação:** Somar valores com sinal. Se total < limite, reembolsar até o limite.

**Justificativa:** Estorno é uma correção. O colaborador "consumiu" menos. Justo liberar espaço.

---

## DEC-006: Nota fiscal obrigatória a partir de R$ 100,01

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Clareza no limiar

**Problema:** Política diz "acima de R$ 100". Ambíguo: R$ 100,00 exato requer nota ou não?

**Decisão:** Nota fiscal obrigatória **apenas** se `valor > 100.00`. Valores <= R$ 100,00 **não** requerem.

**Implementação:** `if abs(despesa.valor) > LIMITE_NOTA_FISCAL and not despesa.tem_nota_fiscal: REJEITAR`

**Justificativa:** "Acima" em português é ambíguo. Escolhemos a interpretação mais leniente (protege o colaborador).

---

## DEC-007: Período de competência é intervalo fechado [inicio, fim]

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Clareza em bordas

**Problema:** Despesa no dia de início/fim: inclui ou não?

**Decisão:** Inclui. Intervalo é `[inicio, fim]` (ambos inclusive).

**Implementação:** `if data >= inicio and data <= fim: ACEITA`

**Justificativa:** Mais intuitivo. Período "julho" inclui 01/07 e 31/07.

---

## DEC-008: Duplicata = primeira ocorrência é aceita

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Determinismo

**Problema:** Se há 3 lançamentos idênticos (data, categoria, valor, fornecedor), qual rejeita?

**Decisão:** Primeira é aceita. Segunda e terceira são rejeitadas como duplicatas.

**Implementação:** Ao processar, guardar hash de (data, categoria, valor, fornecedor). Primeira vez: OK. Demais: REJEITAR.

**Justificativa:** Lançamento duplo acidental é comum. Preservar a primeira permite ao usuário investigar. Simples de explicar.

---

## DEC-009: MVP não implementa "em viagem" (AMB-004)

**Data:** 2026-10-05
**Status:** Decisão final / Deferred to Envelope
**Impacto:** Escopo MVP

**Problema:** Política menciona "colaborador em viagem tem limites ampliados 50%".
Porém, entrada JSON não tem campo `em_viagem`. Sem dados, sem forma de aplicar.

**Decisão:** **Não implementar no MVP**. Marcar como AMB-004, a resolver no envelope (Dia 2).

**Razão SDD:** "Requisito sem dados de entrada é não-executável." Registrar agora evita adivinhos.

**Próximas ações:** Se Dia 2 adicionar campo `em_viagem` na entrada, aplicar 50% no limite (exceto hospedagem).

---

## DEC-010: MVP não faz parsing automático de "N diárias" (AMB-010)

**Data:** 2026-10-05
**Status:** Decisão final / Deferred to Envelope
**Impacto:** Entrada estruturada vs. texto livre

**Problema:** Campo `descricao` pode conter "2 diárias", "3 noites", etc.
Parsing texto livre é frágil e ambíguo ("2 diárias" = 2 noites? 2 dias? diferença?).

**Decisão:** MVP não interpreta automaticamente. Uma despesa de hospedagem = 1 noite, comparada contra R$ 250.
Se lançador quer 2 noites, deve lançar 2 despesas separadas.

**Razão:** Entrada deve ser estruturada, não texto livre. Aumenta robustez.

**Próximas ações:** Dia 2 pode adicionar campo estruturado `num_noites` na entrada.

---

## DEC-011: Python + Click + Pydantic + pytest

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Stack escolhida

**Alternativas consideradas:**
- Node.js: Funciona, mas Python mais natural para dados/finanças.
- Go: Correto e rápido, mas over-engineering para MVP.
- Java: Muito verboso.

**Decisão:** **Python 3.10+** com:
- **Click**: CLI simples e testável
- **Pydantic**: Validação + serialização declarativa
- **pytest**: Testes leves e expressivos
- **Decimal**: Precisão monetária

**Justificativa:** Prototipagem rápida, código legível, comunidade forte em dados/finanças.

---

## DEC-012: Agregação por (data, categoria), não por colaborador/período

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Granularidade de limites

**Problema:** "Limite diário de R$ 60" — aplicar por dia ou por período completo?

**Decisão:** Por dia (ou por noite para hospedagem). Cada dia é independente.

**Implementação:** Agrupar por `(data, categoria)` antes de aplicar limite.

**Exemplo:** Julho com 31 dias pode ter R$ 60 × 31 = R$ 1.860 em alimentação (se todos os dias no limite).

**Justificativa:** Política está clara: "por dia". Não agregamos além disso.

---

## DEC-013: JSON de entrada exatamente conforme exemplos/despesas-exemplo.json

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Contrato de entrada

**Decisão:** Entrada deve respeitar schema em `exemplos/despesas-exemplo.json`.
Qualquer desvio resulta em erro de validação (Pydantic).

**Implementação:** Modelos Pydantic em `src/models/entrada.py` definem o contrato.

**Benefício:** Rejeição rápida de entrada inválida, mensagens claras.

---

## DEC-014: Saída JSON com schema definido em spec.md, seção 4

**Data:** 2026-10-05
**Status:** Decisão final
**Impacto:** Contrato de saída

**Decisão:** Saída segue rigorosamente o schema JSON em spec.md, seção 4.
Campos obrigatórios: `sumario_processamento`, `resultado_por_categoria`, `decisoes_por_despesa`.

**Implementação:** Modelos Pydantic em `src/models/saida.py` garantem conformidade.

**Benefício:** Consumidor da saída sabe exatamente o que esperar. JSON é previsível e validável.

---

## Histórico de mudanças

| Data | Decisão | Status |
|------|---------|--------|
| 2026-10-05 | DEC-001 a DEC-014 | Aprovadas |

---

## Próximas decisões (envelope, Dia 2)

- [ ] DEC-015: Como implementar `em_viagem` (AMB-004)?
- [ ] DEC-016: Adicionar campo `num_noites` para hospedagem (AMB-010)?
- [ ] DEC-017: Integração com sistema de folha/BD?
- [ ] DEC-018: Log de auditoria (quem processou, quando)?
