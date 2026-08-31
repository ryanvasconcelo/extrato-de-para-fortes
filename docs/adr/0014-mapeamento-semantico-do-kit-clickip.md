# ADR 0014 — O kit ClickIP define o mapeamento semântico de cor na UI

- **Status:** Aceito
- **Data:** 2026-08-25
- **Fase:** 7
- **Decisor:** agente da Fase 7, aplicando [ADR 0013](0013-fonte-visual-design-reference.md) sobre `design-reference/design system/`
- **Implementação:** [`docs/superpowers/plans/2026-08-25-design-usabilidade-e-competencias.md`](../superpowers/plans/2026-08-25-design-usabilidade-e-competencias.md)

## Contexto

[ADR 0008](0008-design-system-e-tokens.md) fixou a convenção `element.tone.emphasis.state`, o modo Operate, `prefers-reduced-motion` e a proibição de animar a tabela de ~440 linhas. Na tabela de tons, `brand` era o navy da logo, `accent`/`success` compartilhavam o teal, e `warning` era o laranja da marca.

O kit em `design-reference/design system/` (lido na Fase 7) mapeia diferente: ação primária é teal-700 no claro / teal-400 no escuro; navy é estrutura e texto; laranja marca seleção (cunha da seta da logo), nunca botão nem alerta; sucesso é verde, atenção é âmbar, erro é carmim. Hover/press são véus (`--overlay-hover` / `--overlay-press`), não outra cor. ADR 0013 manda aplicar os arquivos e, se o kit divergir do 0008, registrar sucessor — não editar o 0008.

## Decisão

**Na UI, o mapeamento semântico de cor segue o kit ClickIP v1.0.** A convenção de nomes, o modo Operate, o anel de foco, a ausência de hex em componente e a regra de não animar a grade Fortes continuam as do 0008.

| Tom no componente | Kit (Fase 7) | 0008 (não reescrito) |
|---|---|---|
| `fill-brand-strong` | teal-700 / teal-400 | navy da logo |
| `fill-accent-strong` | laranja, só seleção | teal |
| `fill-success-strong` | verde (matiz 154°) | mesmo teal do accent |
| `fill-warning-strong` | âmbar | laranja da logo |
| `fill-error-strong` | carmim | vermelho derivado |

Tipografia do kit: Archivo (display ≥20px), Instrument Sans (corpo), JetBrains Mono (dado tabular). Ícones: grade 24, traço 1,5, só contorno.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Editar o 0008 para a tabela nova | ADRs não se reescrevem; o 0008 descreve o que valia na Fase 2. |
| Manter navy como fill de botão primário | O kit reprova o teal da logo como fundo de botão (contraste) e reserva navy para estrutura; seguir o 0008 aqui seria ignorar os arquivos 19–23. |
| Buscar paleta fora de `design-reference/` | ADR 0013. |

## Consequências

**Positivas**
- A casca e os cromos passam a ser julgados contra o mesmo kit que o cliente enviou.
- Dark mode sobe luminância da superfície em vez de fingir sombra.

**Negativas**
- Quem ler só o 0008 vai achar que o botão primário é navy. Este ADR é o ponteiro.
- `success` e `brand` deixam de compartilhar teal; conferir estados AUTO/APROVADO pelo ícone e pelo rótulo, não só pela cor (já era regra do 0008).

## Verificação

1. Componente não contém hex; consome `--fill-*` / `--text-*` / `--stroke-*`.
2. Item de navegação ativo usa a cunha laranja (`--fill-accent-strong`), não um botão laranja.
3. A grade `table.planilha-fortes` não anima linha.
