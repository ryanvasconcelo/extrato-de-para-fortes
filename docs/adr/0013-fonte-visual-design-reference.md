# ADR 0013 — A Fase 7 lê `design-reference/` por inteiro; não busca visual fora

- **Status:** Aceito
- **Data:** 2026-08-25
- **Fase:** 7
- **Decisor:** usuário
- **Implementação:** [`docs/superpowers/plans/2026-08-25-design-usabilidade-e-competencias.md`](../superpowers/plans/2026-08-25-design-usabilidade-e-competencias.md)

## Contexto

A Fase 2 registrou o modo Operate e a convenção de nomes em [ADR 0008](0008-design-system-e-tokens.md),
a partir de parte de `design-reference/design clickip/`. Em 2026-08-25 a pasta
`design-reference/design system/` passou a ter o kit ClickIP (HTML/CSS/JSON). A UI em produção ainda
é a casca da Fase 3 + a grade da Fase 6: não passou por uma leitura ponta a ponta dessa árvore.

O usuário pediu a próxima fase focada em **design e usabilidade**, com essas pastas como única
referência visual, verificação Playwright, e **sem** ir buscar padrão na internet.

## Decisão

**Fonte visual da Fase 7 = todos os arquivos em `design-reference/`**, nas duas pastas, lidos de
ponta a ponta, sem pular. A lista canônica está no plano da fase. `.DS_Store` não conta.

Este ADR **não reescreve** o 0008. O 0008 continua valendo (Operate, não animar tabela de ~440
linhas, `prefers-reduced-motion`). Se o kit em `design system/` divergir do 0008, a divergência vira
ADR sucessor — não edição silenciosa do 0008.

**Não** consultar Dribbble, outros produtos, Context7 de UI kit, nem repositórios além das skills
listadas no prompt da sessão. **Não** copiar `reference/` (Rayo).

A conferência visual é **Playwright** contra o app no ar (já há `playwright` em
`frontend/package.json` e `frontend/scripts/capturar-telas.mjs`). Não é um segundo test runner de
unidade no frontend.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Extrair tokens neste ADR e mandar o agente só aplicar a tabela | O usuário pediu o contrário: consumir os arquivos, não um resumo. |
| Buscar “melhores práticas” de SaaS contábil na web | Fora da referência do cliente. |
| Portar o Rayo | ADR 0004. |

## Consequências

**Positivas**
- A UI passa a ser julgada contra o mesmo material que o cliente enviou.
- Playwright deixa evidência (PNG / script) no handover, não só descrição.

**Negativas**
- Ler vídeo, webp e HTML inteiros custa tempo de sessão; pular arquivo é exatamente o que este ADR
  proíbe.
- O kit em `design system/` pode brigar com a grade Excel da Validar (ADR 0011). A grade Fortes
  continua sendo a superfície de conferência; o chrome em volta é que se alinha à referência.

## Verificação

1. O handover da Fase 7 lista cada arquivo de `design-reference/` como lido.
2. Há captura Playwright das superfícies (incluindo a área de competências) em claro e escuro.
3. `rg` em `docs/superpowers/plans/2026-08-25-design-usabilidade-e-competencias.md` não ensina paleta
   nem componente — só aponta arquivos.
