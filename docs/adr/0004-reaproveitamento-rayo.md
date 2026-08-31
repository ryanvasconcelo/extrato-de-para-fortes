# ADR 0004 — Reaproveitamento do Rayo: padrões sim, código não

- **Status:** Aceito
- **Data:** 2026-08-24
- **Fase:** 0

## Contexto

[`reference/`](../../reference) contém 14 arquivos copiados do monorepo Rayo, catalogados em
[`01-analise-rayo-referencia.md`](../01-analise-rayo-referencia.md) e no
[`reference/README.md`](../../reference/README.md), que os classifica por prioridade de
reaproveitamento.

Duas decisões anteriores mudam esse cálculo: [ADR 0001](0001-arquitetura-stack.md) põe o parsing e
o motor em Python, e [ADR 0002](0002-chave-casamento-cnpj.md) descarta o casamento por substring.
O código do Rayo é todo JavaScript de browser. Reaproveitar código exigiria porte de linguagem
**e** mudança de algoritmo ao mesmo tempo — o que é reescrever, com a desvantagem de herdar
decisões que não se aplicam.

## Decisão

Reaproveitar **padrões de domínio e de UX**. Não portar código.

Veredicto por peça, substituindo a tabela de prioridades do `reference/README.md`:

| Peça | Veredicto | Racional |
|---|---|---|
| `de-para-folha/journal-builder.js` + `contracts.js` | **Padrão: adotar** | O melhor do lote. `blocker` vs `warning`, `ValidationIssue` com código, export travado até aprovação. É exatamente o que as fases 4 e 5 precisam. Renomear o vocabulário de folha (Lotação/Evento) para o nosso. |
| `de-para-folha/*-mapper.js` | **Padrão: adotar** | Lookup de regra ativa, N linhas por regra. Conceito reaproveitado, 40 linhas de Python no lugar. |
| `de-para-ui/DeParaModal.jsx` | **Padrão de UX: adotar** | Aplicar/Reverter, status "Aplicada", reprocessamento em lote. Valida o teste "criar regra → status muda" pedido no plano. |
| `assignments/cst-assignments.js` | **Padrão parcial** | O ciclo apply-em-lote serve. A persistência em `localStorage` não — ver ADR 0001, força 2. |
| `conciliacao-bancaria/ConciliacaoBancariaPage.jsx` | **Referência de layout** | StatCards, FilterBar, virtualização com Virtuoso. Útil porque teremos ~440 linhas por mês. As 3 DropZones e o NettingPanel não existem no nosso fluxo. |
| `extrato-financeiro/extrato-parser.js` | **Descartar, salvando 2 funções** | Resolve "Data + Histórico + Débito/Crédito" com heurística de cabeçalho. Nossos insumos são dois relatórios tabulares com colunas nomeadas, um deles sem grade. A heurística não se aplica. Salvar: normalização de data (serial Excel / `dd/mm/yyyy` / ISO) e parse de moeda BR. |
| `extrato-financeiro/categoria-detector.js` | **Descartar** | É o `includes(termo)` que o ADR 0002 rejeita por falso positivo demonstrado. |
| `extrato-financeiro/extrato-reconciler.js` | **Fora de escopo** | Totais dia a dia extrato × financeiro. Outro caso de uso. |
| `banco-razao/*` (4 arquivos) | **Fora de escopo** | Matching Doc↔Origem, outro produto. |
| `banco-razao/netting-engine.js` | **Fora de escopo, com bug conhecido** | [`01-analise-rayo-referencia.md`](../01-analise-rayo-referencia.md) §6 registra que ele espera `isEstorno`/`origemAnulada` e **nenhum parser preenche esses campos**. Portar seria herdar um bug documentado. |

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Portar `extrato-parser.js` para Python e adaptar | Tentador porque é o arquivo mais maduro. Mas ele é uma máquina de detectar cabeçalho em extrato Bradesco/Itaú, e nossos dois insumos não são extratos com cabeçalho detectável — um é relatório de pagamentos com grade, o outro é extrato sem grade. Adaptar seria trocar o corpo inteiro mantendo a casca. |
| Manter o frontend em JS reaproveitando os componentes do Rayo | Os componentes importam `Icons`, `AppLayout` e outros que não foram copiados (registrado no `reference/README.md`). O que existe é um esqueleto sem as dependências, e o design system que vamos adotar é outro. |
| Descartar `reference/` inteiro | Perderia o padrão `blocker`/`warning` e o ciclo `draft → approved → exported`, que são a parte realmente valiosa e difícil de redescobrir. |

## Consequências

**Positivas**
- Nenhum bug conhecido herdado (netting).
- Nenhum algoritmo inadequado herdado (substring).
- O código nasce na linguagem certa para o problema (ADR 0001).
- Os padrões de validação e human-in-the-loop chegam maduros, testados em produção no Rayo.

**Negativas**
- Mais código escrito do zero do que o `reference/README.md` sugeria.
- Perde-se a validação em campo dos parsers do Rayo contra arquivos reais de outros bancos. Nosso
  escopo é uma conta Itaú (ver [`02-analise-arquivos-cliente.md`](../02-analise-arquivos-cliente.md) §3.1),
  então a perda é teórica hoje e real se o escopo crescer.

## Nota para agentes futuros

[`reference/`](../../reference) permanece no repositório **como leitura**, não como dependência.
O `reference/README.md` avisa que os imports estão quebrados de propósito. Se um agente futuro
tentar `import` de qualquer coisa em `reference/`, está violando esta decisão.
