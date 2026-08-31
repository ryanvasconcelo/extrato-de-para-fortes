# ADR 0015 — A casca é trilho de sistema + início com vidro; a jornada vira wizard

- **Status:** Aceito
- **Data:** 2026-08-25
- **Fase:** 7 (sucessor de IA da casca)
- **Decisor:** usuário (`.cursor/rules/produto.mdc` itens 1–9)
- **Este ADR não reescreve** [0012](0012-administracao-de-competencias.md), [0013](0013-fonte-visual-design-reference.md) nem [0014](0014-mapeamento-semantico-do-kit-clickip.md).

## Contexto

A Fase 7 colocou Competências / Importar / Pendências / Validar / Exportar no trilho, com a
área de competências como primeira aba ([ADR 0012](0012-administracao-de-competencias.md)). A
fonte visual daquela fase foi só `design-reference/` ([ADR 0013](0013-fonte-visual-design-reference.md)),
e a cor semântica ficou no kit ClickIP ([ADR 0014](0014-mapeamento-semantico-do-kit-clickip.md)).

O usuário pediu outra informação: todas as telas em `100dvh`, trilho **fixo** também em `100dvh`,
home de dashboard (status do mês + cartões quadrados), jornada num **wizard**, trilho só com
opções de sistema (início, histórico, regras), tema no trilho, calendário ao conciliar, material
inspirado no vidro líquido do macOS, lede explícito em cada aba, e crédito
«feito com ♡ por Ryan Vasconcelo» + «um serviço projecont».

Isso diverge do 0013 (não buscar visual fora da pasta) e da casca da Fase 7 (jornada no trilho).
ADRs não se reescrevem: este sucessor registra a divergência.

## Decisão

**Trilho = sistema. Wizard = conciliar o lote ativo. Home = status + atalhos quadrados.**

1. `html`, `body`, `#raiz`, casca e trilho medem `100dvh`. O trilho é `position: fixed`. O
   conteúdo principal rola por baixo do vidro.
2. Abrir competência continua existindo ([ADR 0012](0012-administracao-de-competencias.md)), mas
   a porta de entrada passa a ser o calendário de **mês** (não dia) disparado por Conciliar. A
   lista de lotes vive em Histórico. Dois lotes no mesmo `MMYYYY` ainda se distinguem por `id`.
3. Tokens ClickIP, cunha laranja de seleção, grade Fortes opaca e a proibição de animar
   `table.planilha-fortes` **não mudam** ([ADR 0008](0008-design-system-e-tokens.md),
   [ADR 0011](0011-grade-fortes-na-validacao.md), [ADR 0014](0014-mapeamento-semantico-do-kit-clickip.md)).
   O vidro aplica-se ao cromo (trilho, topo, folha do calendário), com
   `prefers-reduced-transparency` e `prefers-reduced-motion`.
4. Cadastro de regras na barra é **leitura** (`GET /api/regras`). Criar regra continua em
   Pendências; a grade Validar não envia `criar_regra: true`.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Editar o 0013 para “agora vale Apple” | O 0013 descreve a Fase 7; sucessor registra o pedido novo. |
| Manter a jornada no trilho e só restilizar | O item 4 do produto manda mover a jornada para wizard. |
| Calendário de dias | Competência é `MMYYYY`. |
| Vidro na grade Fortes | ~440 linhas; ADR 0008 / 0011. |

## Consequências

**Positivas**
- O fluxograma do cliente (importar → cruzar → validar → exportar) aparece como sequência, não
  como cinco itens permanentes de navegação.
- O mês de referência é escolhido no calendário, que é o controle que o usuário pediu.

**Negativas**
- O kit ClickIP deixa de ser a única referência de *material*; paleta e tipo continuam dele.
- Quem procava “Competências” no trilho passa a achar a lista em Histórico e a abertura no
  calendário.

## Verificação

1. Trilho fixo, `100dvh`, tema e crédito no trilho.
2. Conciliar abre calendário de 12 meses; Histórico lista lotes; Validar segue 10 colunas.
3. Playwright captura Início, calendário, Histórico e os quatro passos do wizard, claro e escuro.
