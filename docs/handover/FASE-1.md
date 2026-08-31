# Handover — Fase 1: Requisitos

- **Concluída em:** 2026-08-24
- **Fase anterior:** [Fase 0](FASE-0.md) · **Próxima:** [Fase 2 — Design técnico](FASE-2.md)

## Em uma frase

Requisitos reescritos a partir dos dados medidos, com o ciclo de vida `blocker`/`warning` que trava
a exportação, e a decisão de enriquecer o histórico que o processo manual deixava genérico.

## O que foi produzido

| Artefato | Conteúdo |
|---|---|
| [`docs/requisitos/01-requisitos-funcionais.md`](../requisitos/01-requisitos-funcionais.md) | RF-01 a RF-06, ciclo de vida, 6 blockers e 6 warnings, fora de escopo |
| [ADR 0005](../adr/0005-politica-historico-sispag.md) | Enriquecer o histórico `SISPAG`; gabarito de teste em duas partes |

## Decisões desta fase

### 1. Enriquecer `SISPAG FORNECEDORES` (ADR 0005)

A taxa varia de 2% a 32% entre meses e 85% dessas linhas têm o valor no Contas a Pagar. É dívida
manual, não falta de dado.

**Efeito colateral que o próximo agente precisa respeitar:** o gabarito de junho vale para Débito,
Crédito, Valor, Data e Centro de custo, mas **não** para Histórico. O teste da Fase 4 compara 348
linhas derivadas e trata as 91 `SISPAG` como divergência esperada.

Um agente que "consertar" esse teste para exigir 439/439 estará revertendo a decisão sem ADR.

### 2. Desambiguação dos 13 fornecedores multi-conta

Resolvido como **pendência**, não como heurística. RF-02.7 e o blocker `REGRA_AMBIGUA`.

O código de despesa do Contas a Pagar como segundo eixo de chave ficou como **desejável**
(RF-02.12), não MVP. Razão: é hipótese não validada (ver
[`02-analise-arquivos-cliente.md`](../02-analise-arquivos-cliente.md) §7.2) e são 13 fornecedores
que o contador resolve uma vez. Construir a chave composta antes de provar que ela funciona seria
adicionar eixo ao modelo por especulação.

### 3. Centro de custo é sugestão, não determinação

RF-02.5. Consequência direta da medição da Fase 0: 16 fornecedores usam múltiplos centros com a
mesma conta, e a coluna `referência da empresa` do Itaú **não** explica a variação (hipótese testada
e rejeitada). O warning `CENTRO_CUSTO_SUGERIDO` avisa quando há alternativa.

### 4. Blockers travam o export, warnings não

Seis blockers, seis warnings, com código estável para cada. `BANCO_NAO_MAPEADO` existe porque a
Base Bancos tem 5 contas e só uma aparece no histórico — se chegar arquivo de outro banco, o
sistema precisa parar em vez de inventar a conta de crédito.

## Armadilhas para a Fase 2

- **A conta de crédito não é constante, é lookup.** Ela é `1.01.01.02.01.0003` em 100% das 2.487
  linhas históricas, o que convida a fixá-la no código. Não fixe: o plano de contas tem 5 contas
  correntes e o cabeçalho de cada relatório Itaú informa agência e conta. Modelar como Base Bancos
  desde já custa pouco; descobrir depois que está fixo custa caro.
- **`REGRA_AMBIGUA` é blocker, e as 13 regras ambíguas entram desativadas no seed.** Se elas
  entrarem ativas, o motor vai escolher uma conta arbitrária e o blocker nunca dispara.
- **O ciclo de lote só permite `APROVADO` a partir de `PRONTO`.** Modelar a transição como
  "aprovar de qualquer estado" quebraria RF-05.3 e RF-06.2 juntos.

## Como validar que esta fase está de fato concluída

Não há código para rodar; a validação é de consistência documental:

1. Todo requisito MVP tem contrapartida no modelo de dados da Fase 2. Requisito sem tabela ou campo
   correspondente é requisito esquecido.
2. Os 6 blockers e 6 warnings aparecem como códigos no contrato de validação da Fase 2.
3. Os 5 estados de lançamento e os 5 de lote aparecem como enum, não como string livre.
4. Nada de "Fora de escopo no MVP" apareceu no design da Fase 2 — em especial netting e
   matching Doc↔Origem.

## Perguntas ao cliente que continuam abertas

Herdadas da Fase 0, nenhuma bloqueia a Fase 2:

1. Semântica das colunas H, I, J.
2. Critério de escolha nos 13 fornecedores ambíguos.
3. As 5 linhas de junho sem correspondência nos relatórios Itaú.
4. Existe o `RCO010_ImportarLote.pdf`?
5. Outras contas correntes entram no escopo?

A #4 é a que mais economizaria trabalho: confirmaria H/I/J sem inferência.
