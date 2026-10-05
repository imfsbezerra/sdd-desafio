# Plan — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Status:** aprovado · **Última alteração:** 2026-10-05

> **Regra de ouro:** este arquivo descreve o COMO — stack, arquitetura, modelo de dados,
> decisões técnicas com alternativas consideradas. Aqui *sim* pode citar linguagem, biblioteca,
> classe, função. A spec já definiu o QUÊ; este arquivo explica como alcançar.

---

## 1. Stack e justificativa

**Linguagem:** Python 3.10+
**Framework CLI:** Click
**Validação:** Pydantic
**Testes:** pytest com pytest-cov

### Por quê Python?

- Manipulação de JSON é trivial (stdlib `json`)
- Pydantic oferece validação de schema + serialização de forma declarativa
- Click torna CLI robusta e testável sem complexidade
- Prototipagem rápida; fácil de ler e debugar
- Comunidade Python no universo de dados/finanças é forte
- Testes são simples de escrever e executar

### Alternativas descartadas

- **Node.js:** Teria funcionado, mas Python é mais natural para processamento de dados
- **Go:** Correto e rápido, mas seria over-engineering para este escopo
- **Java:** Muito verboso para MVP

---

## 2. Arquitetura em blocos

```
┌─────────────────────────────────────────────────────────┐
│                  CLI (Click)                            │
│  - Recebe --input e --output                            │
│  - Valida argumentos                                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│          Loader (input_loader.py)                       │
│  - Lê JSON do arquivo                                   │
│  - Validação estrutural com Pydantic                    │
│  - Retorna objeto EntradaReembolso tipado               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│      Motor de Cálculo (reembolso_engine.py)             │
│  - ProcessadorReembolso: orquestra o fluxo              │
│  - ValidadorDespesa: aplica regras de rejeição         │
│  - AcumuladorDia: agrupa por dia/noite                 │
│  - CalculadorLimite: aplica limites                    │
│  - GeradorRelatorio: monta a saída                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│        Writer (output_writer.py)                        │
│  - Serializa resultado para JSON                        │
│  - Escreve arquivo                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Modelo de dados

### Entrada (Pydantic)

```python
class Colaborador(BaseModel):
    id: str
    nome: str
    centro_custo: str

class Periodo(BaseModel):
    competencia: str  # YYYY-MM
    inicio: date
    fim: date

class Despesa(BaseModel):
    id: str
    data: date
    categoria: str
    descricao: str
    fornecedor: str
    valor: Decimal  # Usar Decimal para precisão monetária
    tem_nota_fiscal: bool

class EntradaReembolso(BaseModel):
    colaborador: Colaborador
    periodo: Periodo
    despesas: list[Despesa]
```

### Saída (Pydantic)

```python
class DecisaoDespesa(BaseModel):
    id_despesa: str
    data: date
    categoria: str
    descricao: str
    valor_original: Decimal
    valor_reembolsavel: Decimal
    status: str  # "ACEITA", "PARCIAL", "REJEITADA"
    motivo: str
    regras_aplicadas: list[str]  # ["RN-001", "RN-004", ...]

class ResultadoCategoria(BaseModel):
    total_submetido: Decimal
    total_reembolsavel: Decimal
    total_nao_reembolsavel: Decimal
    justificativa: str

class SumarioProcessamento(BaseModel):
    colaborador_id: str
    colaborador_nome: str
    periodo_competencia: str
    data_processamento: datetime
    total_despesas_submetidas: Decimal
    total_reembolsavel: Decimal
    total_nao_reembolsavel: Decimal
    despesas_processadas: int
    despesas_rejeitadas: int
    despesas_parciais: int

class SaidaReembolso(BaseModel):
    sumario_processamento: SumarioProcessamento
    resultado_por_categoria: dict[str, ResultadoCategoria]
    decisoes_por_despesa: list[DecisaoDespesa]
```

---

## 4. Fluxo de processamento detalhado

### Fase 1: Validação de entrada

1. Carregar JSON
2. Validar schema com Pydantic
3. Validar período: `inicio <= fim`, datas válidas
4. Validar cada despesa: valores >= 0 ou valores negativos permitidos

Se erro estrutural, falhar com mensagem clara.

### Fase 2: Filtro inicial (RN-007, RN-009)

Para cada despesa:
- Verificar se data está em `[periodo.inicio, periodo.fim]`
  - Não: marcar REJEITADA, motivo "fora do período de competência"
- Verificar se categoria está em `["alimentacao", "transporte_urbano", "hospedagem"]` (case-insensitive)
  - Não: marcar REJEITADA, motivo "categoria não está na política de reembolso"

Descartar despesas rejeitadas daqui em diante.

### Fase 3: Validação de nota fiscal (RN-005)

Para cada despesa restante:
- Se `abs(valor) > 100.00` e `tem_nota_fiscal == false`:
  - Marcar REJEITADA, motivo "nota fiscal obrigatória acima de R$ 100"

### Fase 4: Detecção de duplicatas (RN-008)

Agrupar por `(data, categoria, valor, fornecedor)`:
- Se grupo tem 2+ despesas: marcar a primeira como ACEITA_CANDIDATA, as outras como REJEITADA, motivo "duplicata detectada"

### Fase 5: Agregação por dia/noite

Agrupar despesas restantes por `(data, categoria)`:

```python
agregado = {
    ("2026-07-03", "alimentacao"): [d-001, d-002, ...],
    ("2026-07-06", "transporte_urbano"): [d-003, d-004, ...],
}
```

### Fase 6: Cálculo de limites (RN-001, RN-002, RN-003, RN-004, RN-006)

Para cada agregado:

1. Somar valores (incluindo negativos = estornos)
2. Determinar limite conforme categoria:
   - alimentacao: R$ 60
   - transporte_urbano: R$ 80
   - hospedagem: R$ 250
3. Se total <= limite: ACEITAR tudo
4. Se total > limite:
   - Processar FIFO: primeira despesa fica com min(valor, espaço_restante)
   - Próximas: mesmo processo
   - Excedente: REJEITADA, motivo "limite diário atingido"
5. Se há estornos: permitir reembolso adicional para itens posteriores

### Fase 7: Geração de relatório

1. Somar por categoria
2. Contar: processadas, rejeitadas, parciais
3. Montar saída JSON
4. Registrar timestamp

---

## 5. Decisões técnicas

### DEC-001: Usar Decimal em vez de float

**Por quê:** Float tem precisão limitada (ex: 0.1 + 0.2 ≠ 0.3 em binário).
Dinheiro exige precisão. Decimal garante.

**Alternativa descartada:** Usar inteiros (centavos). Funciona, mas menos legível.

---

### DEC-002: Processar FIFO em agregados

**Por quê:** Justo com o colaborador. Primeira despesa tem prioridade.

**Alternativa descartada:** Processar maior-para-menor. Favorecia reembolsos de contas altas primeiro.

---

### DEC-003: Normalizar categoria para minúscula

**Por quê:** "ALIMENTACAO", "alimentacao", "Alimentacao" são a mesma coisa. Evita rejeições por tipografia.

**Implementação:** No carregamento, fazer `despesa.categoria = despesa.categoria.lower()`.

---

### DEC-004: Arredondar valores para 2 casas decimais (teto)

**Por quê:** Moeda brasileira tem centavos. Valores como R$ 33,333 precisam ser tratados.

**Implementação:** `Decimal(str(valor)).quantize(Decimal('0.01'), rounding=ROUND_UP)`

---

### DEC-005: Estornos reduzem consumo de limite

**Por quê:** Se teve estorno, o colaborador consomiu menos. Justo liberar espaço.

**Implementação:** Somar valores (com sinal); se negativo, reduz o total da categoria no dia.

---

## 6. Estrutura de arquivos

```
src/
├── __init__.py
├── main.py                    # Entry point do CLI
├── models/
│   ├── __init__.py
│   ├── entrada.py             # Modelos Pydantic de entrada
│   └── saida.py               # Modelos Pydantic de saída
├── loaders/
│   ├── __init__.py
│   └── input_loader.py        # Carregamento e validação de JSON
├── engine/
│   ├── __init__.py
│   ├── validador.py           # Aplicação de regras
│   ├── acumulador.py          # Agregação por dia/noite
│   ├── calculador.py          # Cálculo de limites
│   └── processador.py         # Orquestração do fluxo
├── writers/
│   ├── __init__.py
│   └── output_writer.py       # Serialização de saída
└── utils/
    ├── __init__.py
    └── constants.py           # Limites, categorias válidas, etc.

tests/
├── __init__.py
├── test_entrada.py            # Validação de entrada
├── test_validador.py          # Testes de regras (RN-001 a RN-009)
├── test_engine.py             # Testes de integração
└── fixtures/
    ├── __init__.py
    ├── entrada_valida.json
    ├── entrada_com_duplicata.json
    └── entrada_fora_periodo.json
```

---

## 7. Estratégia de testes

### Pirâmide de testes

**Base (Unit):** 70%
- Cada regra tem seu teste isolado (RN-001, RN-002, ...)
- Testes de arredondamento, normalização
- Testes de validação Pydantic

**Meio (Integration):** 25%
- Processar arquivo inteiro
- Verificar sumário
- Comparar saída JSON

**Topo (E2E):** 5%
- Rodar CLI com arquivo real
- Verificar arquivo de saída

### Cobertura mínima

- 80% de cobertura de código
- 100% de cobertura de regras de negócio
- Cada caso de borda (seção 7 da spec) tem teste

### Casos de teste críticos

- `test_rn001_limite_alimentacao_dia`
- `test_rn002_limite_transporte_dia`
- `test_rn003_limite_hospedagem_noite`
- `test_rn004_reembolso_parcial`
- `test_rn005_nota_fiscal_obrigatoria`
- `test_rn006_estornos`
- `test_rn007_periodo_competencia`
- `test_rn008_duplicata`
- `test_rn009_categoria_valida`
- `test_amb001_agregacao_dia`
- `test_amb003_limite_100_exato`
- `test_amb009_arredondamento_moeda`

---

## 8. Dependências (requirements.txt)

```
click==8.1.7
pydantic==2.4.2
pytest==7.4.3
pytest-cov==4.1.0
python-dateutil==2.8.2
```

---

## 9. Como executar

```bash
# Instalação
pip install -r requirements.txt

# Execução
python -m src.main calcular --input despesas.json --output resultado.json

# Testes
pytest tests/ -v --cov=src --cov-report=html
```

---

## 10. Próximos passos

1. **tasks.md:** Decompor este plano em tarefas T-001, T-002, ... com commits específicos
2. **Implementação:** Seguir a ordem de tasks
3. **Envelope:** Estar pronto para mudanças (ex: campo `em_viagem`)
