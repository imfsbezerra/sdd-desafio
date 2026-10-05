# Tasks — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Status:** pronto para execução · **Última alteração:** 2026-10-05

> Cada task aqui é independente o suficiente para resultar em um commit.
> A ordem deve ser respeitada para evitar dependências circulares.
> Todos os testes passam no final de cada task.

---

## T-001 — Scaffolding inicial e estrutura de projeto

**Descrição:** Criar estrutura de pastas, pyproject.toml, requirements.txt, .gitignore e arquivo README.md básico.

**Requisitos atendidos:** (setup)

**Artefatos entregues:**
- `pyproject.toml` com metadados do projeto
- `requirements.txt` com dependências (click, pydantic, pytest, pytest-cov)
- `src/` com `__init__.py`
- `tests/` com `__init__.py` e `conftest.py`
- `.gitignore` com `*.pyc`, `__pycache__`, `.coverage`, `htmlcov/`, `.pytest_cache/`
- `README.md` com instruções de instalação e uso

**Critério de aceite:**
- [ ] Estrutura de pastas criada
- [ ] `pip install -r requirements.txt` funciona sem erros
- [ ] `pytest tests/` encontra 0 testes (estrutura vazia)

**Commit sugerido:** `chore(T-001): scaffolding inicial e estrutura de projeto`

---

## T-002 — Modelos Pydantic de entrada

**Descrição:** Implementar classes Pydantic para validação de entrada JSON: `Colaborador`, `Periodo`, `Despesa`, `EntradaReembolso`.

**Requisitos atendidos:** Seção 4 da spec (entrada)

**Artefatos entregues:**
- `src/models/__init__.py`
- `src/models/entrada.py` com modelos de entrada

**Implementação:**
```python
# Usar Decimal para valores monetários
# Validar que Periodo.inicio <= Periodo.fim
# Permitir valores negativos em Despesa.valor (estornos)
```

**Critério de aceite:**
- [ ] Arquivo `src/models/entrada.py` existe
- [ ] Classe `EntradaReembolso` valida JSON conforme `exemplos/despesas-exemplo.json`
- [ ] Rejeita entrada com schema inválido
- [ ] `Despesa.valor` é `Decimal`

**Commit sugerido:** `feat(T-002): modelos Pydantic de entrada com validação`

---

## T-003 — Modelos Pydantic de saída

**Descrição:** Implementar classes Pydantic para serialização de saída JSON: `DecisaoDespesa`, `ResultadoCategoria`, `SumarioProcessamento`, `SaidaReembolso`.

**Requisitos atendidos:** Seção 4 da spec (saída)

**Artefatos entregues:**
- `src/models/saida.py` com modelos de saída

**Implementação:**
```python
# Garantir serialização correta de Decimal em JSON
# Campo `regras_aplicadas` é lista de strings
# Timestamp em formato ISO 8601
```

**Critério de aceite:**
- [ ] Arquivo `src/models/saida.py` existe
- [ ] Classe `SaidaReembolso` pode ser serializada em JSON sem erros
- [ ] JSON gerado respeita schema documentado em spec.md

**Commit sugerido:** `feat(T-003): modelos Pydantic de saída`

---

## T-004 — Loader de entrada

**Descrição:** Implementar carregamento e validação de arquivo JSON de entrada.

**Requisitos atendidos:** Parte do fluxo de processamento (Fase 1)

**Artefatos entregues:**
- `src/loaders/__init__.py`
- `src/loaders/input_loader.py` com função `carregar_entrada(caminho: str) -> EntradaReembolso`

**Implementação:**
```python
def carregar_entrada(caminho: str) -> EntradaReembolso:
    # Ler arquivo JSON
    # Validar com Pydantic
    # Retornar objeto tipado ou lançar erro com mensagem clara
```

**Critério de aceite:**
- [ ] Função carrega `exemplos/despesas-exemplo.json` sem erros
- [ ] Retorna `EntradaReembolso` tipado
- [ ] Arquivo inválido lança `ValidationError` com mensagem legível

**Commit sugerido:** `feat(T-004): loader de entrada JSON com validação`

---

## T-005 — Constants e utilidades

**Descrição:** Centralizar limites, categorias válidas e funções de utilidade (arredondamento, normalização).

**Requisitos atendidos:** Suporta todas as regras (RN-001 a RN-009)

**Artefatos entregues:**
- `src/utils/__init__.py`
- `src/utils/constants.py` com limites, categorias e funções helper

**Implementação:**
```python
LIMITE_ALIMENTACAO = Decimal("60.00")
LIMITE_TRANSPORTE = Decimal("80.00")
LIMITE_HOSPEDAGEM = Decimal("250.00")
LIMITE_NOTA_FISCAL = Decimal("100.00")
CATEGORIAS_VALIDAS = {"alimentacao", "transporte_urbano", "hospedagem"}

def normalizar_categoria(cat: str) -> str:
    return cat.lower()

def arredondar_moeda(valor: Decimal) -> Decimal:
    # Arredondar para cima (ROUND_UP) com 2 casas decimais
    return valor.quantize(Decimal('0.01'), rounding=ROUND_UP)

def eh_fora_periodo(data: date, inicio: date, fim: date) -> bool:
    return data < inicio or data > fim
```

**Critério de aceite:**
- [ ] Arquivo `src/utils/constants.py` existe
- [ ] Função `arredondar_moeda(Decimal("33.333"))` retorna `Decimal("33.34")`
- [ ] Função `normalizar_categoria("ALIMENTACAO")` retorna `"alimentacao"`

**Commit sugerido:** `feat(T-005): constants e utilidades`

---

## T-006 — Validador de regras básicas (RN-007, RN-009, RN-005)

**Descrição:** Implementar validações iniciais: período de competência, categoria válida, nota fiscal.

**Requisitos atendidos:** RN-007, RN-009, RN-005

**Artefatos entregues:**
- `src/engine/__init__.py`
- `src/engine/validador.py` com funções de validação

**Implementação:**
```python
def validar_periodo(despesa: Despesa, inicio: date, fim: date) -> tuple[bool, str]:
    # Retorna (válido, motivo)
    if eh_fora_periodo(despesa.data, inicio, fim):
        return False, "fora do período de competência"
    return True, ""

def validar_categoria(despesa: Despesa) -> tuple[bool, str]:
    cat_normalizada = normalizar_categoria(despesa.categoria)
    if cat_normalizada not in CATEGORIAS_VALIDAS:
        return False, "categoria não está na política de reembolso"
    return True, ""

def validar_nota_fiscal(despesa: Despesa) -> tuple[bool, str]:
    if abs(despesa.valor) > LIMITE_NOTA_FISCAL and not despesa.tem_nota_fiscal:
        return False, "nota fiscal obrigatória acima de R$ 100"
    return True, ""
```

**Critério de aceite:**
- [ ] Teste: despesa de 2026-04-15 com período 2026-07 é rejeitada com motivo correto
- [ ] Teste: categoria "coworking" é rejeitada
- [ ] Teste: despesa de R$ 100,01 sem nota fiscal é rejeitada
- [ ] Teste: despesa de R$ 100,00 sem nota fiscal é aceita

**Commit sugerido:** `feat(T-006): validador de regras básicas (RN-007, RN-009, RN-005)`

---

## T-007 — Detector de duplicatas (RN-008)

**Descrição:** Implementar detecção de duplicatas exatas (data, categoria, valor, fornecedor).

**Requisitos atendidos:** RN-008

**Artefatos entregues:**
- Função em `src/engine/validador.py`: `detectar_duplicatas(despesas: list[Despesa]) -> dict[str, bool]`

**Implementação:**
```python
def detectar_duplicatas(despesas: list[Despesa]) -> dict[str, bool]:
    # Retorna {id_despesa: eh_duplicata}
    # Agrupar por (data, categoria, valor, fornecedor)
    # Primeira ocorrência: False
    # Demais: True
```

**Critério de aceite:**
- [ ] Teste: d-006 e d-007 (ambas R$ 54,90 no mesmo dia/fornecedor) — d-006 retorna False, d-007 retorna True
- [ ] Teste: d-003 e d-004 (diferentes valores) não são duplicatas

**Commit sugerido:** `feat(T-007): detector de duplicatas (RN-008)`

---

## T-008 — Normalização de entrada

**Descrição:** Normalizar categorias para minúscula e arredondar valores.

**Requisitos atendidos:** AMB-008, AMB-009

**Artefatos entregues:**
- Função em `src/engine/` ou loader: `normalizar_entrada(entrada: EntradaReembolso) -> EntradaReembolso`

**Implementação:**
```python
def normalizar_entrada(entrada: EntradaReembolso) -> EntradaReembolso:
    for despesa in entrada.despesas:
        despesa.categoria = normalizar_categoria(despesa.categoria)
        despesa.valor = arredondar_moeda(despesa.valor)
    return entrada
```

**Critério de aceite:**
- [ ] Teste: categoria "ALIMENTACAO" é convertida para "alimentacao"
- [ ] Teste: valor R$ 33,333 é arredondado para R$ 33,34

**Commit sugerido:** `feat(T-008): normalização de entrada (AMB-008, AMB-009)`

---

## T-009 — Acumulador por dia/categoria

**Descrição:** Agrupar despesas por (data, categoria) e agregar valores.

**Requisitos atendidos:** Suporte para RN-001, RN-002, RN-003

**Artefatos entregues:**
- `src/engine/acumulador.py` com classe `AcumuladorDia`

**Implementação:**
```python
class AcumuladorDia:
    def __init__(self, despesas: list[Despesa]):
        self.agregados = {}  # {(data, categoria): [despesas]}
    
    def agregar(self) -> dict:
        # Retorna {(data, categoria): total_valor}
```

**Critério de aceite:**
- [ ] Teste: d-001 (R$ 72,50) + d-002 (R$ 38,00) no mesmo dia/categoria resulta em (data, "alimentacao"): 110.50
- [ ] Teste: despesas em dias diferentes não são agregadas

**Commit sugerido:** `feat(T-009): acumulador por dia/categoria`

---

## T-010 — Calculador de limites (RN-001, RN-002, RN-003, RN-004, RN-006)

**Descrição:** Aplicar limites diários/por noite e processar FIFO. Tratar estornos.

**Requisitos atendidos:** RN-001, RN-002, RN-003, RN-004, RN-006

**Artefatos entregues:**
- `src/engine/calculador.py` com classe `CalculadorLimite`

**Implementação:**
```python
class CalculadorLimite:
    def calcular_reembolso_dia(self, despesas: list[Despesa], categoria: str) -> list[tuple[Despesa, Decimal, str]]:
        # Retorna [(despesa, valor_reembolsavel, motivo)]
        # Processar FIFO
        # Aplicar limite conforme categoria
        # Tratar estornos
```

**Critério de aceite:**
- [ ] Teste RN-001: d-001 (R$ 72,50) + d-002 (R$ 38,00) no mesmo dia — reembolso total R$ 60,00
- [ ] Teste RN-002: duas corridas de R$ 100,00 — reembolso total R$ 80,00
- [ ] Teste RN-006: R$ 60,00 + estorno -R$ 20,00 = espaço de R$ 20,00 para mais reembolsos

**Commit sugerido:** `feat(T-010): calculador de limites com FIFO (RN-001..006)`

---

## T-011 — Processador principal (orquestração)

**Descrição:** Orquestrar todas as fases de processamento (validação, agregação, cálculo, geração de relatório).

**Requisitos atendidos:** Todas as regras

**Artefatos entregues:**
- `src/engine/processador.py` com classe `ProcessadorReembolso`

**Implementação:**
```python
class ProcessadorReembolso:
    def processar(self, entrada: EntradaReembolso) -> SaidaReembolso:
        # Fase 1: Normalizar
        # Fase 2: Filtro inicial (período, categoria)
        # Fase 3: Nota fiscal
        # Fase 4: Duplicatas
        # Fase 5: Agregação
        # Fase 6: Cálculo de limites
        # Fase 7: Gerar relatório
```

**Critério de aceite:**
- [ ] Processa `exemplos/despesas-exemplo.json` sem erros
- [ ] Retorna `SaidaReembolso` válido
- [ ] Testes de integração com arquivo inteiro passam

**Commit sugerido:** `feat(T-011): processador principal de reembolso`

---

## T-012 — Writer de saída

**Descrição:** Serializar resultado para JSON e escrever arquivo.

**Requisitos atendidos:** Saída JSON

**Artefatos entregues:**
- `src/writers/__init__.py`
- `src/writers/output_writer.py` com função `escrever_resultado(resultado: SaidaReembolso, caminho: str)`

**Implementação:**
```python
def escrever_resultado(resultado: SaidaReembolso, caminho: str):
    # Serializar com json.dumps (Decimal handler)
    # Escrever arquivo com encoding UTF-8
```

**Critério de aceite:**
- [ ] Arquivo `src/writers/output_writer.py` existe
- [ ] Função serializa `SaidaReembolso` em JSON válido
- [ ] Arquivo de saída é legível e respeita o schema

**Commit sugerido:** `feat(T-012): writer de saída JSON`

---

## T-013 — CLI com Click

**Descrição:** Implementar interface CLI com Click para receber argumentos `--input` e `--output`.

**Requisitos atendidos:** Interface de utilização

**Artefatos entregues:**
- `src/main.py` com comando Click `calcular`

**Implementação:**
```python
@click.command()
@click.option('--input', type=click.Path(exists=True), required=True)
@click.option('--output', type=click.Path(), required=True)
def calcular(input, output):
    entrada = carregar_entrada(input)
    processador = ProcessadorReembolso()
    resultado = processador.processar(entrada)
    escrever_resultado(resultado, output)
    click.echo(f"Processamento concluído. Resultado em {output}")
```

**Critério de aceite:**
- [ ] `python -m src.main calcular --input exemplos/despesas-exemplo.json --output resultado.json` funciona
- [ ] Arquivo `resultado.json` é criado corretamente
- [ ] Erros exibem mensagem clara

**Commit sugerido:** `feat(T-013): CLI com Click`

---

## T-014 — Testes unitários para regras (RN-001 a RN-009)

**Descrição:** Implementar testes unitários cobrindo cada regra de negócio.

**Requisitos atendidos:** Cobertura de código

**Artefatos entregues:**
- `tests/test_validador.py` com testes de validação
- `tests/test_calculador.py` com testes de cálculo de limites
- `tests/fixtures/` com dados de teste

**Implementação:**
```python
# tests/test_validador.py
def test_rn007_fora_periodo():
    # Despesa de 2026-04-15 com período 2026-07 é rejeitada

def test_rn009_categoria_invalida():
    # Categoria "coworking" é rejeitada

def test_rn005_nota_fiscal_obrigatoria():
    # R$ 100,01 sem nota fiscal é rejeitada

# tests/test_calculador.py
def test_rn001_limite_alimentacao_dia():
    # R$ 72,50 + R$ 38,00 = R$ 60,00 reembolsado

def test_rn002_limite_transporte_dia():
    # Duas corridas de R$ 100,00 = R$ 80,00 reembolsado

def test_rn003_limite_hospedagem_noite():
    # Hospedagem dentro do limite é aceita

def test_rn004_reembolso_parcial():
    # R$ 100,00 com limite de R$ 60,00 = R$ 60,00 reembolsado

def test_rn006_estornos():
    # Estorno libera espaço no limite

def test_rn008_duplicata():
    # Primeira aceita, segunda rejeitada
```

**Critério de aceite:**
- [ ] Cobertura mínima 80% do código
- [ ] Todos os testes passam
- [ ] Cada regra tem no mínimo 1 teste

**Commit sugerido:** `test(T-014): testes unitários para regras (RN-001 a RN-009)`

---

## T-015 — Testes de integração

**Descrição:** Testar fluxo completo com arquivo real de entrada.

**Requisitos atendidos:** Integração

**Artefatos entregues:**
- `tests/test_engine.py` com testes de integração
- `tests/fixtures/entrada_valida.json` com exemplo de entrada

**Implementação:**
```python
def test_processamento_arquivo_completo():
    entrada = carregar_entrada("tests/fixtures/entrada_valida.json")
    processador = ProcessadorReembolso()
    resultado = processador.processar(entrada)
    
    assert resultado.sumario_processamento is not None
    assert len(resultado.decisoes_por_despesa) > 0
    assert resultado.resultado_por_categoria is not None
```

**Critério de aceite:**
- [ ] `tests/fixtures/entrada_valida.json` existe e é válido
- [ ] Testes de integração processam arquivo sem erros
- [ ] Sumário está preenchido corretamente

**Commit sugerido:** `test(T-015): testes de integração`

---

## T-016 — Testes E2E com CLI

**Descrição:** Testar execução completa via CLI.

**Requisitos atendidos:** Usabilidade

**Artefatos entregues:**
- `tests/test_cli.py` com testes E2E

**Implementação:**
```python
def test_cli_processa_arquivo():
    from click.testing import CliRunner
    from src.main import calcular
    
    runner = CliRunner()
    result = runner.invoke(calcular, [
        '--input', 'exemplos/despesas-exemplo.json',
        '--output', '/tmp/teste_output.json'
    ])
    
    assert result.exit_code == 0
    assert os.path.exists('/tmp/teste_output.json')
```

**Critério de aceite:**
- [ ] CLI executa com sucesso
- [ ] Arquivo de saída é criado
- [ ] Saída JSON é válida

**Commit sugerido:** `test(T-016): testes E2E com CLI`

---

## T-017 — Documentação README.md

**Descrição:** Documentar como instalar, executar e entender o projeto.

**Requisitos atendidos:** Usabilidade

**Artefatos entregues:**
- `README.md` com instruções completas

**Conteúdo mínimo:**
```markdown
# Motor de Cálculo de Reembolso

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
python -m src.main calcular --input despesas.json --output resultado.json
```

## Testes

```bash
pytest tests/ -v --cov=src
```

## Documentação

- `specs/001-motor-reembolso/spec.md` — O QUÊ e PORQUÊ
- `specs/001-motor-reembolso/plan.md` — COMO (arquitetura e decisões)
- `specs/001-motor-reembolso/tasks.md` — TAREFAS de implementação
```

**Critério de aceite:**
- [ ] README.md existe
- [ ] Instruções de instalação e execução são claras
- [ ] Referências para spec, plan e tasks estão presentes

**Commit sugerido:** `docs(T-017): documentação README.md`

---

## T-018 — Revisão de cobertura de testes

**Descrição:** Garantir 80%+ de cobertura de código e revisar casos de borda.

**Requisitos atendidos:** Qualidade

**Artefatos entregues:**
- Relatório de cobertura (`htmlcov/`)

**Implementação:**
```bash
pytest tests/ -v --cov=src --cov-report=html
# Revisar htmlcov/index.html
```

**Critério de aceite:**
- [ ] Cobertura >= 80%
- [ ] Todos os casos de borda (seção 7 da spec) têm testes
- [ ] Nenhum erro de cobertura crítico

**Commit sugerido:** `test(T-018): revisão de cobertura 80%+`

---

## T-019 — DECISIONS.md - Log de decisões

**Descrição:** Documentar decisões técnicas e ambiguidades resolvidas durante implementação.

**Requisitos atendidos:** Rastreabilidade

**Artefatos entregues:**
- `specs/001-motor-reembolso/DECISIONS.md`

**Conteúdo:**
```markdown
# Decisions — Motor de Reembolso

## DEC-001: Usar Decimal em vez de float
**Data:** 2026-10-05
**Status:** Implementado
**Impacto:** Precisão monetária garantida
```

**Critério de aceite:**
- [ ] Arquivo `DECISIONS.md` existe
- [ ] Todas as decisões de plan.md estão documentadas
- [ ] Decisões tomadas durante implementação estão registradas

**Commit sugerido:** `docs(T-019): DECISIONS.md com log de decisões`

---

## T-020 — CLAUDE.md - Convenções de projeto

**Descrição:** Documentar convenções para próximas iterações (envelope Dia 2).

**Requisitos atendidos:** Mantenibilidade

**Artefatos entregues:**
- `template/CLAUDE.md` com convenções

**Conteúdo:**
```markdown
# CLAUDE.md — Convenções do Projeto

## Estrutura de arquivos
- `src/` — código-fonte
- `tests/` — testes automatizados
- `specs/` — especificações e planos
- `exemplos/` — dados de exemplo

## Padrões de código
- Type hints obrigatórios
- Docstrings em toda classe/função
- Testes para cada feature

## Convenção de commits
- `feat(T-XXX): descrição`
- `test(T-XXX): descrição`
- `docs(T-XXX): descrição`
- `fix: descrição`

## Como contribuir (Dia 2)
1. Ler spec.md para entender o QUÊ
2. Ler plan.md para entender o COMO
3. Ler tasks.md para saber o que implementar
4. Criar teste antes de implementar (TDD)
5. Fazer commit com referência a task
6. Atualizar DECISIONS.md se houver desvio
```

**Critério de aceite:**
- [ ] Arquivo `template/CLAUDE.md` existe
- [ ] Convenções são claras e aplicáveis
- [ ] Inclui instruções para Dia 2

**Commit sugerido:** `docs(T-020): CLAUDE.md com convenções`

---

## T-021 — RELATORIO.md final

**Descrição:** Consolidar relatório final com resumo de implementação, ambiguidades resolvidas e pronto para envelope.

**Requisitos atendidos:** Entrega

**Artefatos entregues:**
- `template/docs/RELATORIO.md`

**Conteúdo:**
```markdown
# Relatório — Motor de Reembolso (Dia 1)

## Status
✅ MVP implementado e testado

## Ambiguidades resolvidas
- AMB-001 a AMB-010 conforme spec.md

## Testes
- Cobertura: 80%+
- Todos os testes passam
- Cada regra tem teste

## Pendências para Dia 2 (envelope)
- [ ] Campo `em_viagem` (AMB-004)
- [ ] Parsing de "N diárias" em hospedagem (AMB-010)
- [ ] Possível integração com BD

## Como validar
```bash
python -m src.main calcular --input exemplos/despesas-exemplo.json --output resultado.json
pytest tests/ -v --cov=src
```

## Próximos passos
Ver section "O que fica em aberto" em spec.md
```

**Critério de aceite:**
- [ ] Arquivo `template/docs/RELATORIO.md` existe
- [ ] Contém resumo de implementação
- [ ] Lista ambiguidades resolvidas
- [ ] Inclui instruções de validação

**Commit sugerido:** `docs(T-021): RELATORIO.md final`

---

## Resumo de progresso

| Task | Status | Requisitos | Commit |
|------|--------|-----------|--------|
| T-001 | ⬜ | Setup | `chore(T-001):` |
| T-002 | ⬜ | Modelos entrada | `feat(T-002):` |
| T-003 | ⬜ | Modelos saída | `feat(T-003):` |
| T-004 | ⬜ | Loader | `feat(T-004):` |
| T-005 | ⬜ | Constants | `feat(T-005):` |
| T-006 | ⬜ | Validador básico | `feat(T-006):` |
| T-007 | ⬜ | Detector duplicata | `feat(T-007):` |
| T-008 | ⬜ | Normalização | `feat(T-008):` |
| T-009 | ⬜ | Acumulador | `feat(T-009):` |
| T-010 | ⬜ | Calculador | `feat(T-010):` |
| T-011 | ⬜ | Processador | `feat(T-011):` |
| T-012 | ⬜ | Writer | `feat(T-012):` |
| T-013 | ⬜ | CLI | `feat(T-013):` |
| T-014 | ⬜ | Testes unit | `test(T-014):` |
| T-015 | ⬜ | Testes integração | `test(T-015):` |
| T-016 | ⬜ | Testes E2E | `test(T-016):` |
| T-017 | ⬜ | README | `docs(T-017):` |
| T-018 | ⬜ | Cobertura | `test(T-018):` |
| T-019 | ⬜ | DECISIONS | `docs(T-019):` |
| T-020 | ⬜ | CLAUDE.md | `
