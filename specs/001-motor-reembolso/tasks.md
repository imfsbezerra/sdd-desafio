# Tasks — Motor de Cálculo de Reembolso

**Base:** spec 1.1 e plano 1.0

Cada task deve caber em um commit de implementação, acompanhado dos testes que
provam seu aceite. Marcar `[x]` e preencher o hash somente depois de verificar.

## Fase 1 — Fundação

- [x] **T-001 — Criar núcleo monetário e estruturas de domínio**
  - **Atende:** RN-012, AMB-011
  - **Entrega:** pacote executável, estruturas de entrada/decisão e funções de
    normalização/formatação de valores.
  - **Aceite:** `test_rn012_arredonda_meio_para_longe_de_zero` e
    `test_rn012_formata_duas_casas` passam.
  - **Commit:** `0e4af2b`

- [x] **T-002 — Ler e validar o contrato completo de entrada**
  - **Atende:** RN-001, AMB-013
  - **Entrega:** leitura decimal, validação de campos, datas, competência e IDs.
  - **Aceite:** `test_rn001_carrega_exemplo_valido`,
    `test_rn001_rejeita_id_repetido` e
    `test_rn001_rejeita_periodo_incoerente` passam.
  - **Commit:** `a64cf45`

## Fase 2 — Elegibilidade

- [x] **T-003 — Aplicar competência, categoria e valor positivo**
  - **Atende:** RN-002, RN-003, RN-004, RN-011; AMB-005, AMB-009, AMB-010,
    AMB-013 e AMB-014
  - **Entrega:** primeiras decisões terminais e normalização controlada de
    categoria.
  - **Aceite:** testes `test_rn002_*`, `test_rn003_*`, `test_rn004_*` e
    `test_rn011_sem_dado_nao_amplia_limite` passam.
  - **Commit:** `e07f916`

- [x] **T-004 — Detectar duplicatas e exigir nota na precedência correta**
  - **Atende:** RN-005, RN-006; AMB-003, AMB-004, AMB-007, AMB-008 e AMB-015
  - **Entrega:** assinatura canônica, memória da primeira ocorrência e
    verificação documental sobre o valor solicitado.
  - **Aceite:** `test_rn005_fronteira_nota`, `test_rn006_primeira_ocorrencia`,
    `test_amb007_normaliza_assinatura` e `test_amb015_duplicata_precede_nota`
    passam.
  - **Commit:** `772d0f7`

## Fase 3 — Limites e decisões

- [x] **T-005 — Aplicar limites diários e alocação por ordem**
  - **Atende:** RN-007, RN-008, RN-010; AMB-001, AMB-002 e AMB-012
  - **Entrega:** saldos separados por data/categoria e estados aprovada, parcial
    e limite esgotado.
  - **Aceite:** `test_rn007_limite_alimentacao_compartilhado`,
    `test_rn008_limite_transporte_por_data` e
    `test_rn010_aloca_na_ordem_de_entrada` passam.
  - **Commit:** `8ea1319`

- [x] **T-006 — Aplicar limite de hospedagem por lançamento**
  - **Atende:** RN-009, RN-010; AMB-002 e AMB-006
  - **Entrega:** limite independente de R$ 250,00 para cada hospedagem elegível,
    sem interpretar a descrição.
  - **Aceite:** `test_rn009_cada_item_e_uma_diaria` e
    `test_amb006_nao_extrai_noites_da_descricao` passam.
  - **Commit:** `6e2619f`

- [x] **T-007 — Produzir decisões e resumo reconciliado**
  - **Atende:** RN-013 e contrato de saída da seção 5
  - **Entrega:** montagem do resultado, códigos estáveis, justificativas e totais.
  - **Aceite:** `test_rn013_preserva_ordem_e_reconcilia_totais` e
    `test_saida_obedece_schema_da_spec` passam.
  - **Commit:** `03d776b`

## Fase 4 — Interface e integração

- [x] **T-008 — Implementar a CLI e gravação segura**
  - **Atende:** RN-001 e critérios de aceite da seção 10
  - **Entrega:** comando `calcular --input --output`, códigos de saída e gravação
    que não deixa resultado parcial.
  - **Aceite:** `test_cli_calcular_cria_saida` e
    `test_cli_entrada_invalida_preserva_destino` passam.
  - **Commit:** `b11bfd7`

- [x] **T-009 — Fechar cenário de integração do arquivo de exemplo**
  - **Atende:** RN-001 a RN-013 e casos de borda da seção 8
  - **Entrega:** teste com `exemplos/despesas-exemplo.json` e resultado esperado
    calculado a partir da spec.
  - **Aceite:** `test_integracao_exemplo_gera_14_decisoes_e_totais_exatos` passa
    junto com toda a suíte.
  - **Commit:** `bf692b5`

## Fase 5 — Documentação e evidências

- [x] **T-010 — Documentar execução e convenções do agente**
  - **Atende:** critérios de aceite da seção 10 e entregáveis do desafio
  - **Entrega:** `README.md` executável e `CLAUDE.md` curto, apontando para a spec
    como fonte da verdade, sem identificar modelo de IA.
  - **Aceite:** uma pessoa em checkout limpo consegue executar o exemplo e os
    testes apenas com os comandos documentados.
  - **Commit:** `3caacda`

- [ ] **T-011 — Registrar sessões e preparar evidências do relatório**
  - **Atende:** critério “Relatório e discernimento” da rubrica
  - **Entrega:** registros de sessão existentes, lacunas declaradas e rascunho do
    relatório com referências verificáveis aos commits.
  - **Aceite:** `docs/sessions/` contém ao menos um registro desta etapa e o caso
    concreto do rascunho contraditório aponta para `05a079f` e `e6e4d3b`.
  - **Commit:** —

## Fase 6 — Envelope (Dia 2)

Criar novas tasks a partir de **T-012**, sem renumerar as anteriores. A ordem
obrigatória é: atualizar `spec.md` → registrar `DECISIONS.md` → criar tasks →
alterar testes e implementação.

## Matriz de cobertura planejada

| Regra / decisão | Task | Teste principal |
|---|---|---|
| RN-001 | T-002, T-008 | `test_rn001_rejeita_id_repetido` |
| RN-002 | T-003 | `test_rn002_intervalo_fechado` |
| RN-003 | T-003 | `test_rn003_categoria_case_insensitive` |
| RN-004 | T-003 | `test_rn004_negativo_contribui_zero` |
| RN-005 | T-004 | `test_rn005_fronteira_nota` |
| RN-006 | T-004 | `test_rn006_primeira_ocorrencia` |
| RN-007 | T-005 | `test_rn007_limite_alimentacao_compartilhado` |
| RN-008 | T-005 | `test_rn008_limite_transporte_por_data` |
| RN-009 | T-006 | `test_rn009_cada_item_e_uma_diaria` |
| RN-010 | T-005, T-006 | `test_rn010_aloca_na_ordem_de_entrada` |
| RN-011 | T-003 | `test_rn011_sem_dado_nao_amplia_limite` |
| RN-012 | T-001 | `test_rn012_arredonda_meio_para_longe_de_zero` |
| RN-013 | T-007, T-009 | `test_rn013_preserva_ordem_e_reconcilia_totais` |
| AMB-001–AMB-002 | T-005, T-006 | testes RN-007 a RN-010 |
| AMB-003–AMB-004 | T-004 | `test_rn005_fronteira_nota` |
| AMB-005 | T-003 | `test_rn011_sem_dado_nao_amplia_limite` |
| AMB-006 | T-006 | `test_amb006_nao_extrai_noites_da_descricao` |
| AMB-007–AMB-008 | T-004 | `test_amb007_normaliza_assinatura` |
| AMB-009–AMB-010 | T-003 | testes RN-003 e RN-004 |
| AMB-011 | T-001 | testes RN-012 |
| AMB-012 | T-005 | `test_rn010_aloca_na_ordem_de_entrada` |
| AMB-013–AMB-014 | T-002, T-003 | testes RN-002 |
| AMB-015 | T-004 | `test_amb015_duplicata_precede_nota` |

