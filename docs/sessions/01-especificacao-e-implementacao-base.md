# Sessão 01 — Especificação e implementação base

**Data:** 2026-10-05

> Registro estruturado da sessão. A ferramenta usada nesta etapa não oferece o
> comando `/export`; por isso este arquivo preserva pedidos, decisões, erros e
> evidências verificáveis sem se apresentar como transcrição automática.

## Pedidos do usuário

1. “Preciso fazer esse desafio, leia o desafio.md para entender o que preciso
   fazer.”
2. Depois do resumo: “pode continuar [...] mas não precisa especificar [o modelo]
   na documentação”.

## O que foi lido antes da implementação

- `DESAFIO.md`;
- `RUBRICA.md`;
- `FAQ.md`;
- `exemplos/despesas-exemplo.json`;
- todos os arquivos em `template/`;
- rascunhos já existentes em `specs/001-motor-reembolso/`.

## Revisão crítica do ponto de partida

O rascunho inicial foi preservado no commit `05a079f`. Na leitura, foram
encontrados estes problemas:

- RN-003 dizia para interpretar “2 diárias” e dividir o valor pelo número de
  noites;
- AMB-010 dizia que texto livre não seria interpretado e que todo lançamento
  equivaleria a uma noite;
- a seção de questões em aberto afirmava conhecer uma mudança futura do envelope;
- estorno foi associado ao item da política sobre duplicatas sem base textual;
- `tasks.md` continha centenas de linhas de código antecipado, em vez de tasks
  pequenas com critérios de aceite;
- `DECISIONS.md` misturava mudanças de spec, escolhas técnicas e detalhes de
  implementação.

A correção entrou primeiro na spec e no log de mudanças (`e6e4d3b`), depois no
plano (`0164f5c`) e nas tasks (`3b87f57`).

## Decisões de negócio propostas nesta sessão

- limites de alimentação e transporte são agregados por data e categoria;
- limite diário é consumido na ordem da entrada;
- excedente é recusado, mas o saldo do limite é pago;
- R$ 100,00 sem nota não é recusado por nota; R$ 100,01 é;
- nota é verificada sobre o valor solicitado, antes do teto da categoria;
- cada hospedagem representa uma diária; descrição não fornece quantidade;
- sem campo de viagem, nenhum limite é ampliado;
- duplicata usa data, categoria, descrição, fornecedor e valor normalizados;
- primeira ocorrência é processada e as posteriores são recusadas;
- valor não positivo é recusado e não cria crédito;
- valores são arredondados para centavos pelo meio para longe de zero;
- datas inicial e final pertencem ao período;
- fins de semana não recebem regra especial;
- a precedência das recusas está explícita na seção 9 da spec.

Essas decisões precisam de revisão consciente do responsável pelo projeto antes
da entrega final; não devem ser tratadas como corretas apenas porque os testes
passam.

## Implementação e verificação

| Etapa | Commit | Evidência |
|---|---|---|
| Dinheiro e domínio | `0e4af2b` | 3 testes |
| Contrato de entrada | `a64cf45` | 8 testes acumulados |
| Elegibilidade básica | `e07f916` | 13 testes acumulados |
| Duplicidade e nota | `772d0f7` | 18 testes acumulados |
| Limites diários | `8ea1319` | 22 testes acumulados |
| Hospedagem | `6e2619f` | 26 testes acumulados |
| Saída reconciliada | `03d776b` | 29 testes acumulados |
| CLI e escrita atômica | `b11bfd7` | 32 testes acumulados |
| Regressão do exemplo | `bf692b5` | 33 testes acumulados |
| README e convenções | `3caacda` | comando do README executado |

Resultado verificado para o exemplo: 14 decisões; R$ 1.861,84 solicitados;
R$ 585,43 reembolsáveis; R$ 1.276,41 não reembolsáveis.

## Erros e correções observáveis

### Caso 1 — Rascunho contraditório

O ponto de partida continha duas respostas incompatíveis para hospedagem e
antecipava o envelope. A contradição foi detectada comparando RN-003, AMB-010, a
rubrica e o JSON de exemplo. A spec 1.1 escolheu uma única regra verificável e
registrou a invalidação no `DECISIONS.md`.

**Evidência:** diff `05a079f..e6e4d3b`.

### Caso 2 — Teste temporário incompatível com o ambiente

A primeira versão de `test_rn001_rejeita_json_malformado` criou uma pasta com
`TemporaryDirectory`. No sandbox do Windows, o processo não conseguiu escrever
nem limpar essa pasta. A falha apareceu na execução da suíte; o teste foi alterado
para usar uma fixture malformada versionada em `tests/fixtures/malformado.json`.

**Evidência:** a falha ocorreu antes do commit `a64cf45`; esse commit contém a
versão corrigida e os oito testes passando.

## Pendências reais ao fim da sessão

- responsável revisar e assumir as decisões da spec 1.1;
- receber o envelope do Dia 2 e seguir spec → DECISIONS → tasks → testes → código;
- atualizar este registro ou criar `02-envelope.md`;
- finalizar as seções do relatório que dependem do envelope;
- publicar o repositório somente após revisar identidade Git e visibilidade.

