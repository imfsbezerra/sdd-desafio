# Relatório — Desafio SDD

**Aluno:** `<preencher>` · **Repositório:** `<preencher>` · **Data:** 2026-10-05

> Rascunho factual da etapa base. Campos do envelope permanecem explicitamente
> pendentes para não fabricar evidência antes da mudança de requisito.

## Delegação

| Atividade | Quem | Por quê / evidência |
|---|---|---|
| Ler enunciado, rubrica, FAQ e exemplo | Agente | Inventário registrado em `docs/sessions/01-especificacao-e-implementacao-base.md` |
| Identificar ambiguidades | Agente, com revisão humana pendente | AMB-001 a AMB-015 em `spec.md` |
| Decidir ambiguidades | Agente propôs; responsável deve ratificar | Decisões explícitas na spec 1.1, commit `e6e4d3b` |
| Escrever spec, plano e tasks | Agente | commits `e6e4d3b`, `0164f5c` e `3b87f57` |
| Implementar | Agente | T-001 a T-008, commits citados em `tasks.md` |
| Escrever testes | Agente | 33 testes; T-001 a T-009 |
| Verificar resultados | Agente nesta etapa | suíte completa e execução real do comando do README |
| Absorver o envelope | Pendente | ainda não recebido |

**Onde deleguei e me arrependi:** o rascunho inicial assistido por IA foi extenso,
mas escondia uma contradição central sobre hospedagem e antecipava uma mudança
futura sem evidência. Preservá-lo em `05a079f` permitiu revisar em vez de aceitar
o volume como sinal de qualidade.

**Onde não deleguei e deveria ter delegado:** `<preencher após revisão pessoal>`.

**Subagentes / skills / MCP / hooks:** não foram usados subagentes. A execução foi
sequencial para manter cada task e seu teste no mesmo contexto e commit.

## Descrição

Exemplo escolhido: quantidade de diárias de hospedagem.

**Versão 1 — contraditória, commit `05a079f`:**

> “Despesas lançadas como um único item especificando múltiplas noites devem ter
> seu valor dividido pelo número de noites.”

No mesmo documento, AMB-010 dizia:

> “Na versão MVP, o sistema não interpreta automaticamente texto descritivo.
> Hospedagem de valor V é considerada 1 noite.”

**Versão final — spec 1.1, RN-009:**

> “Cada lançamento de hospedagem representa exatamente uma diária e tem limite de
> R$ 250,00. Texto como ‘2 diárias’ ou ‘3 noites’ não altera essa quantidade.”

**O que estava ambíguo:** a política fala em diária, mas o contrato não informa a
quantidade; números aparecem apenas em texto livre.

**Como percebi:** a mesma entrada de R$ 480,00 teria reembolso de R$ 480,00 por uma
seção e R$ 250,00 por outra. As duas não poderiam gerar o mesmo teste.

**Commit da mudança:** `e6e4d3b`.

## Discernimento

### Caso 1 — Contradição e antecipação indevida

**O que o agente propôs:** interpretar quantidade de noites na descrição em uma
regra, não interpretar em outra e preparar explicitamente um campo supostamente
esperado no envelope.

**Por que estava errado:** produzia dois resultados válidos para a mesma entrada e
tratava uma mudança desconhecida como fato. Isso viola determinismo e o propósito
do envelope.

**Como detectei:** comparei as seções RN-003, AMB-010 e “O que fica em aberto” do
rascunho preservado. Em seguida transformei o exemplo de R$ 480,00 em critério de
aceite: resultados diferentes expuseram a contradição.

**O que fiz:** escolhi uma diária por lançamento, removi toda previsão do envelope,
registrei o que foi invalidado em D-001 e criei teste que garante que “2 diárias”
não é interpretado.

**Evidência:** `docs/sessions/01-especificacao-e-implementacao-base.md`, seção
“Revisão crítica”; commits `05a079f` e `e6e4d3b`; teste
`test_amb006_nao_extrai_noites_da_descricao` no commit `6e2619f`.

### Caso 2 — Suposição de ambiente no teste

**O que o agente propôs:** criar um diretório temporário durante o teste de JSON
malformado.

**Por que estava errado:** o sandbox do Windows negou escrita e limpeza nesse
diretório, fazendo um teste de parsing falhar por infraestrutura.

**Como detectei:** executei a suíte completa e li o traceback de `PermissionError`.

**O que fiz:** troquei o arquivo criado em tempo de teste por uma fixture inválida
versionada. O teste passou e deixou de depender de permissão de escrita.

**Evidência:** registro da sessão; fixture em
`tests/fixtures/malformado.json`; commit `a64cf45`.

## Diligência

**Procedimento de verificação:** após cada task, executei toda a suíte, não apenas
o teste novo. Só então criei o commit da task. Ao terminar a CLI, executei o
comando documentado no README e conferi os sete campos do resumo gerado.

**Leitura de diff:** nesta etapa, todos os arquivos alterados foram revisados antes
do commit por serem pequenos e separados por task. A revisão final da pessoa
responsável ainda é necessária, especialmente para as decisões de negócio.

**O que aceitei sem verificar direito:** inicialmente aceitei que
`TemporaryDirectory` funcionaria dentro do ambiente restrito. Isso custou duas
execuções de teste e deixou uma pasta temporária, removida depois.

**Como sei que os testes testam a coisa certa:** os resultados do exemplo estão
escritos por ID em `tests/test_integration_example.py`, e cada teste unitário cita
RN/AMB no nome. A matriz de `tasks.md` permite partir da regra e chegar ao teste.
Como código e testes foram escritos pelo mesmo agente, a revisão humana deve
comparar pelo menos os números do teste de integração diretamente com a spec.

## O envelope

**Status:** ainda não recebido.

**Quantos arquivos toquei na mão:** pendente.

**Quanto tempo levou:** pendente.

**Diff de absorção:** pendente.

**Absorveu de graça / resistiu / ordem / aprendizado:** preencher após criar uma
entrada em `DECISIONS.md`, novas tasks a partir de T-012 e os respectivos commits.

## Fechamento

**Para qual tamanho de projeto isto valeu a pena?** Já valeu para 13 regras que
interagem em uma precedência observável. Sem spec, nota, duplicidade e limite
produziriam justificativas diferentes conforme a ordem acidental do código.

**Para qual não valeria?** Um script descartável sem regra ambígua, auditoria ou
evolução prevista provavelmente não justificaria quatro artefatos separados.

**O que eu faria diferente:** pediria a revisão humana das decisões de negócio
antes de implementar todas as tasks, embora o histórico atual permita corrigir
isso de forma rastreável.

**A coisa mais desconfortável que aprendi sobre como trabalho com IA:** um texto
longo e bem formatado pode conter regras mutuamente exclusivas. A checagem útil
não foi “parece completo?”, mas “qual valor exato este exemplo produz?”.

