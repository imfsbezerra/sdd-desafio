# FAQ — Desafio SDD

O instrutor está fora durante estes dois dias. Este arquivo cobre as dúvidas previsíveis.

Uma fronteira que vale entender antes de continuar: **dúvida de processo tem resposta aqui; dúvida sobre o que a política do RH significa, não.** Isso não é falta de suporte — interpretar a política ambígua *é* o exercício, e vale 25 dos 100 pontos. A resposta para toda pergunta desse tipo é a mesma: **decida, justifique em uma linha e registre na spec.**

---

## Sobre a política e as regras

**"O que o RH quis dizer com [X]?"**
Ninguém sabe. É esse o ponto. Escolha uma interpretação defensável, escreva na `spec.md` qual você escolheu e por quê, e siga. Você não perde ponto por escolher a interpretação "errada" — não existe uma certa. Perde ponto por resolver a ambiguidade dentro do código sem registrar que existia uma decisão ali.

**"Minha interpretação de [X] está certa?"**
A pergunta certa não é essa. É: *está escrita, está justificada, e o sistema faz o que ela diz?* Se as três forem sim, pontua integralmente.

**"Achei uma ambiguidade que não parece intencional. Reporto?"**
Não precisa. Trate como as outras: identifique, decida, justifique, registre. Ambiguidade não intencional é a coisa mais realista que pode te acontecer neste desafio.

**"Quantas ambiguidades existem?"**
No mínimo oito. A `RUBRICA.md` descreve os tipos delas sem listá-las. Percorra `exemplos/despesas-exemplo.json` item por item antes de escrever a spec — cada linha daquele arquivo está lá por um motivo.

**"Preciso tratar o caso [X] que não está na política?"**
Se a entrada de exemplo contém o caso, sim — nem que seja para declarar explicitamente na spec que ele está fora de escopo e por quê. Silêncio da spec sobre um caso que existe nos dados conta como buraco.

---

## Sobre a spec

**"Quão detalhada a spec precisa ser?"**
O teste é um só: *uma pessoa que nunca viu o projeto consegue, lendo só a spec, verificar se o sistema está correto?* Spec longa não é spec boa — spec verificável é.

**"Posso usar o Claude para escrever a spec?"**
Sim, e é esperado que use. Mas as decisões sobre ambiguidade são suas e você vai defendê-las no relatório. Spec gerada e aceita sem revisão tem um cheiro característico e aparece na correção.

**"Posso mudar a spec no meio?"**
Deve. Spec que não muda em dois dias é spec que ninguém consultou. O que se avalia não é estabilidade — é se toda mudança tem entrada no `DECISIONS.md`.

**"Coloquei nome de biblioteca na spec. Problema?"**
Sim, pequeno. Mova para `plan.md`. A `spec.md` não sabe que existe código.

**"Não sei se algo é `spec.md` ou `plan.md`."**
Pergunte: *se eu trocasse de linguagem amanhã, isso mudaria?* Se muda, é `plan.md`.

---

## Sobre execução

**"Qual stack devo usar?"**
A que você domina. Você tem dois dias e o código vale 10 pontos — não é hora de aprender ferramenta nova.

**"Passei a manhã inteira do Dia 1 na spec e não escrevi código. Normal?"**
Normal e esperado. Mas feche a spec até o meio-dia mesmo imperfeita: o que falta se corrige via `DECISIONS.md`. Paralisia de especificação também custa nota.

**"Não vou terminar o produto."**
Entregue o que tem. São 10 pontos no produto e 90 no resto. Não sacrifique spec, rastreabilidade ou relatório para fechar feature — a troca é ruim em todos os cenários.

**"Meus commits ficaram grandes demais / esqueci de referenciar a task."**
Não reescreva o histórico para maquiar. Registre no relatório que aconteceu e siga com a convenção daí em diante. Histórico honesto imperfeito vale mais que histórico reescrito.

**"Posso usar subagentes, skills, MCP, hooks?"**
Sim. Se usar, conte no relatório: o que configurou e se valeu a pena. Vale ponto em Delegação.

---

## Sobre entrega

**"Meu fork está privado."**
Deixe público, ou não há como corrigir. Settings → General → Danger Zone → Change visibility.

**"Esqueci de exportar as sessões dos primeiros dias."**
Exporte as que ainda existirem e **declare a lacuna no relatório**, dizendo a partir de quando o registro começa. Declarar custa pouco; ser pego com sessões todas datadas do último dia custa muito mais.

**"O `/export` não está funcionando."**
Como alternativa: as conversas do Claude Code ficam em `~/.claude/projects/<slug-do-projeto>/` em arquivos `.jsonl` Copie os do período do desafio para `docs/sessions/` e explique no relatório por que o formato é esse.
Ou então execute o seguinte prompt no chat ```Exporte todas as mensagens desta janela de contexto como um único bloco que eu possa copiar e colar. Oculte informações pessoais identificáveis do usuário, como o nome do diretório pessoal.``` copie e coloque em um arquivo em `docs/sessions/export.md` 


**"Vou entregar depois do prazo."**
Entregue assim mesmo e diga no formulário. Atraso declarado é uma conversa; entrega silenciosamente atrasada é outra.

---

## Sobre o Dia 2

**"O que chega no Dia 2?"**
Uma mudança de requisito, às 10h, pelo canal da turma. Vale 20 pontos. Nada além disso vai ser dito antes da hora.

**"Como me preparo?"**
Chegue ao Dia 2 com o sistema base funcionando e testado. Você vai querer as mãos livres. E resista à tentação de otimizar demais na expectativa da mudança — você não sabe qual é, e uma arquitetura genérica no lugar errado é pior que uma simples.

**"E se eu não conseguir absorver a mudança inteira?"**
Não penaliza. O que penaliza é a mudança entrar por fora da spec. Ordem: spec → `DECISIONS.md` → tasks → código. Meia implementação com a spec correta vale mais que implementação completa com a spec desatualizada.

---

## Ainda travado?

Se a sua dúvida é de processo e não está aqui, registre a pergunta no relatório junto com a decisão que você tomou sem ela. Isso conta a seu favor: mostra onde a especificação encostou no limite do que dava para decidir sozinho — que é exatamente a situação que este desafio simula.
