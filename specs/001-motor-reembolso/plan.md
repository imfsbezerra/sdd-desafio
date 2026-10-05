# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Baseado na spec:** 1.1 · **Data:** 2026-10-05

> Este documento define como implementar a spec. Nenhuma regra de negócio nova
> deve nascer aqui.

## 1. Stack

| Escolha | Decisão | Por quê | Alternativa descartada |
|---|---|---|---|
| Linguagem | Python 3.11+ | Legibilidade, boa biblioteca padrão e execução simples | Node.js: também serviria, mas exigiria configurar pacote para um domínio pequeno |
| CLI | `argparse` da biblioteca padrão | Suporta a interface fixa sem dependência externa | Click: ergonomia boa, mas acrescenta instalação sem benefício necessário |
| JSON e datas | Biblioteca padrão | O contrato é pequeno e estável | Validador externo: custo adicional e mensagens pouco controladas |
| Dinheiro | `Decimal`, com leitura decimal direta do JSON | Evita aritmética binária e preserva a regra RN-012 | `float`: pode introduzir resíduos; centavos inteiros: complica o valor original com mais de 2 casas |
| Testes | `unittest` da biblioteca padrão | Roda sem instalar pacotes | pytest: mais conciso, porém desnecessário para o prazo e escopo |

Não haverá dependências de produção nem de teste fora da distribuição do Python.

## 2. Arquitetura

```text
arquivo JSON
    ↓
leitura decimal → validação do contrato → motor puro → montagem do resultado
                                                            ↓
                                                     gravação atômica JSON
```

- `src/cli.py`: argumentos, códigos de saída e mensagens para o usuário;
- `src/io_json.py`: leitura, validação estrutural e gravação segura;
- `src/model.py`: estruturas internas de entrada e decisão;
- `src/money.py`: normalização e formatação monetária;
- `src/engine.py`: ordem das regras, duplicidade, limites e resumo;
- `tests/`: testes unitários do núcleo e testes ponta a ponta da CLI.

O núcleo recebe dados já validados e devolve um objeto de resultado sem acessar
arquivos, relógio ou terminal. Isso mantém as regras testáveis e reduz o custo de
uma futura mudança de política.

## 3. Modelo de dados interno

### Entrada validada

- `Colaborador`: `id`, `nome`, `centro_custo`;
- `Periodo`: `competencia`, `inicio`, `fim` como datas;
- `Despesa`: posição original, campos recebidos, valor original decimal, valor
  normalizado e textos canônicos usados apenas em comparações;
- `Solicitacao`: colaborador, período e lista ordenada de despesas.

### Resultado

- `Decisao`: ID, status, quatro valores monetários, código, justificativa e IDs de
  regras;
- `Resumo`: totais monetários e contagens por status;
- `Resultado`: versão da política, dados copiados, resumo e decisões ordenadas.

Os objetos internos usam `Decimal`; somente na fronteira de saída os valores são
convertidos para textos com duas casas.

## 4. Representação da política

Limites e versão da política ficam centralizados em dados imutáveis no módulo do
motor:

| Chave | Valor |
|---|---:|
| `alimentacao` | R$ 60,00 por data |
| `transporte_urbano` | R$ 80,00 por data |
| `hospedagem` | R$ 250,00 por item |
| nota fiscal | acima de R$ 100,00 |

A ordem das validações permanece explícita em uma única rotina de avaliação, pois
ela é comportamento observável definido na seção 9 da spec.

## 5. Decisões técnicas

### DT-001 — Somente biblioteca padrão

**Contexto:** a ferramenta precisa ser reproduzível em ambiente de correção.

**Decisão:** usar somente módulos da biblioteca padrão.

**Alternativa descartada:** framework de modelos e CLI; reduziria código local,
mas criaria etapa de instalação e risco de versão.

**Consequência:** validações serão escritas no projeto, porém execução e testes
não dependem de rede.

### DT-002 — Núcleo funcional e I/O separado

**Contexto:** regras serão alteradas no segundo dia e precisam de testes rápidos.

**Decisão:** o motor não lê nem grava arquivos e não encerra o processo.

**Alternativa descartada:** concentrar CLI, parsing e cálculo em um único módulo;
seria menor no início, mas tornaria testes e mudanças acoplados.

**Consequência:** testes de regra constroem entradas em memória; poucos testes E2E
cobrem as fronteiras.

### DT-003 — Saída gravada de forma atômica

**Contexto:** RN-001 proíbe resultado parcial e a CLI pode falhar ao serializar ou
gravar.

**Decisão:** gerar todo o conteúdo antes e substituir o destino somente após uma
gravação temporária bem-sucedida no mesmo diretório.

**Alternativa descartada:** escrever diretamente no destino; uma falha poderia
deixar JSON truncado.

**Consequência:** erro preserva um arquivo anterior e facilita afirmar que sucesso
significa resultado completo.

### DT-004 — Erros de entrada agregados quando possível

**Contexto:** RN-001 exige localizar o campo ou a condição inválida.

**Decisão:** validar toda a estrutura e devolver uma lista curta de problemas,
mantendo caminhos como `despesas[2].valor`.

**Alternativa descartada:** parar no primeiro campo; implementação menor, mas pior
para quem precisa corrigir o documento.

**Consequência:** a CLI usa código de saída 2 para uso/entrada inválida e 1 para
falha operacional inesperada.

## 6. Estratégia de testes

- testes unitários para dinheiro, contrato, assinatura de duplicidade, precedência
  e cada RN-001 a RN-013;
- testes parametrizados por subtestes para fronteiras de data, nota e dinheiro;
- teste de integração do arquivo de exemplo com as 14 decisões e totais exatos;
- testes ponta a ponta chamando a CLI em diretório temporário;
- teste de erro garantindo que destino anterior não seja sobrescrito.

Nomenclatura: `test_rnNNN_<comportamento>` e, quando útil,
`test_ambNNN_<decisao>`. A matriz no fim de `tasks.md` liga regra, task e teste.

Não haverá meta numérica isolada de cobertura. A condição é cada regra e cada caso
de borda possuir uma asserção relevante, além de todo o conjunto passar.

## 7. Riscos

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Serializar `Decimal` incorretamente | Média | Converter apenas na camada de saída e testar valores com 3 casas |
| Divergência entre precedência e testes | Média | Um teste com item atingido por múltiplas recusas |
| Totais não reconciliarem com valor negativo | Média | Centralizar contribuição positiva e testar RN-004/RN-013 juntas |
| Mudança futura exigir novo dado de entrada | Alta | Manter validação, modelo e motor separados |
| Mensagens humanas virarem base de decisão | Baixa | Usar `codigo_motivo` estável para testes e consumo automático |

