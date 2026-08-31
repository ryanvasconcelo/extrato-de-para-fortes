# ADR 0008 — Design system: tokens semânticos `element.tone.emphasis.state`

- **Status:** Aceito
- **Data:** 2026-08-24
- **Fase:** 2

## Contexto

[`design-reference/design clickip/`](../../design-reference/design%20clickip) traz 18 arquivos de
referência. Dois definem decisões:

**`ux referencia.webp`** especifica a convenção de nomes de token:

```
element.tone.emphasis.state
   |       |       |       |
Text     Neutral  Strong  Hover
Stroke   Brand    Weak    Press
Icon     Error    Weaker  Focus
Fill     Warning          Disabled
Background Success        Selected
         Inverse
```

**`logo.svg`** define a identidade: `#003048` (navy profundo), `#1ea099` (teal), `#e56125`
(laranja), `#ffffff`.

`referencia color.webp` mostra uma rampa neutra fria com acento azul — mas é uma referência
genérica, não a marca do cliente.

A tensão: a referência de cor não é a marca. Resolver isso com "usar as duas" produziria paleta
incoerente.

## Decisão

**A referência define a estrutura; o logo define a identidade.**

Adotar a convenção `element.tone.emphasis.state` como nome de token, mapeando os tons às cores da
marca ClickIP:

| Tom | Cor | Origem |
|---|---|---|
| `brand` | `#003048` navy | logo |
| `accent` | `#1ea099` teal | logo |
| `warning` | `#e56125` laranja | logo |
| `success` | `#1ea099` teal | logo (mesma do accent) |
| `error` | vermelho derivado | necessário, não está no logo |
| `neutral` | rampa fria | `referencia color.webp` |

Implementação: CSS custom properties com nomes semânticos, consumidas pelo Tailwind. Componente
**nunca** recebe cor literal.

```css
--text-neutral-strong    --fill-brand-strong      --stroke-neutral-weak
--text-neutral-weak      --fill-brand-strong-hover --stroke-error-strong
--text-error-strong      --fill-success-weaker    --background-neutral-weaker
```

Dark mode redefine os mesmos nomes, então nenhum componente sabe qual tema está ativo. É o que
`darkmode referencia.webp` implica.

### Modo da interface: Operate

Pela taxonomia da skill `impeccable`, este produto é **Operate**, não Persuade: o usuário vem
completar uma tarefa (fechar a competência), não ser convencido. Consequências concretas:

- Densidade alta. São ~440 linhas por mês para conferir; espaçamento generoso vira scroll.
- Escaneabilidade acima de expressão. A marca aparece em detalhe preciso, não em hero.
- Números tabulares e alinhados à direita. Valor monetário desalinhado é erro de leitura.
- O estado do lançamento precisa ser legível **sem cor** — o contador pode imprimir. Cor mais
  ícone mais rótulo, nunca cor sozinha.

### Movimento

`animacao.mov` mostra transições com curva e duração deliberadas. A regra, seguindo
`emil-design-eng`: animação comunica mudança de estado, não decora.

- Transição de estado de lançamento: 150 ms, `ease-out`.
- Entrada de painel/modal: 200 ms, saída mais rápida que entrada.
- `prefers-reduced-motion` respeitado sempre.
- **Nada animado numa tabela de 440 linhas.** Animar linha em lista longa é jank garantido.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Usar a paleta de `referencia color.webp` como está | É referência genérica de rampa neutra, não a marca do cliente. O logo é a fonte de verdade da identidade. |
| Tailwind com utilitários de cor crus (`bg-blue-600`) | Mais rápido para escrever, e é o que o Rayo faz. Rejeitado porque dark mode passaria a exigir variante em cada componente, e a regra 6 da skill `ui-ux-pro-max` marca "raw hex in components" como anti-padrão. |
| Design system próprio do zero | Custo alto, nenhum ganho: shadcn/ui é código no projeto, não dependência opaca, então customizar é editar o componente. |
| Material UI / Ant Design | Trazem identidade visual própria que brigaria com a marca ClickIP. |

## Consequências

**Positivas**
- Dark mode sem tocar em componente.
- Nome de token diz a intenção (`text-error-strong`), não a aparência (`text-red-600`), então
  trocar a paleta não exige revisar componentes.
- Alinhado à referência que o cliente enviou, o que facilita aprovação.

**Negativas**
- Indireção: ler o componente não diz qual cor sai na tela.
- Definir a rampa completa antes da primeira tela custa tempo adiantado.
- `success` e `accent` compartilham o teal do logo. Se um dia precisarem divergir, é ADR novo.

## Verificação

- `grep -rE "#[0-9a-fA-F]{6}|bg-(blue|red|green)-[0-9]" src/` não deve retornar nada em componente.
- Alternar dark mode não deve exigir nenhuma classe condicional de cor.
- Estado de lançamento identificável em captura em escala de cinza.
