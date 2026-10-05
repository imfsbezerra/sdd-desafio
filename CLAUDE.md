# Convenções do Projeto

## Fonte da verdade

- `specs/001-motor-reembolso/spec.md` define o comportamento.
- `specs/001-motor-reembolso/plan.md` define a implementação.
- `specs/001-motor-reembolso/tasks.md` define a ordem do trabalho.
- Se código e spec divergirem, corrigir primeiro a spec e registrar a mudança em
  `DECISIONS.md`, ou tratar o código como defeito.

Antes de implementar, localizar a task correspondente. Uma regra explicada apenas
no chat é uma lacuna da spec e deve ser documentada antes do código.

## Comandos

```text
Executar: python -m src.cli calcular --input <entrada.json> --output <saida.json>
Testar:   python -m unittest discover -s tests -v
```

## Convenções

- Python 3.11+ e somente biblioteca padrão.
- Dinheiro usa `Decimal`; `float` não participa dos cálculos.
- O motor de regras não acessa arquivos, terminal ou relógio.
- Cada RN e caso de borda deve possuir teste cujo nome remeta ao seu ID.
- Todo commit de implementação ou teste referencia `T-NNN`.
- Alteração de negócio segue: spec → DECISIONS → tasks → teste → código.

## Fora de escopo

Não adicionar interface gráfica, persistência, autenticação, integrações externas,
inferência por texto livre ou regras que não estejam na spec.

