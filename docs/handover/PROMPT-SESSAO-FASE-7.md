# Prompt — sessão Fase 7

Copiar o bloco abaixo e colar como primeira mensagem do chat novo.

---

Execute a Fase 7 deste repositório.

## O que fazer

Implementar o plano, tarefa por tarefa. Não parar no meio para perguntar se continua.

**Plano (fonte da verdade da implementação):**  
`docs/superpowers/plans/2026-08-25-design-usabilidade-e-competencias.md`

**Handover da fase:** `docs/handover/FASE-7.md`  
**Decisões já registradas:**  
`docs/adr/0012-administracao-de-competencias.md`  
`docs/adr/0013-fonte-visual-design-reference.md`  
Não reescrever esses ADRs. Divergência = ADR sucessor.

## Skills — só estas (já instaladas)

Invocar e seguir. Não usar Superpowers, `frontend-design`, `brainstorming`, Context7, nem qualquer skill que não esteja nesta lista.

| Origem | Nomes locais a invocar |
|---|---|
| https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | `ui-ux-pro-max` |
| https://github.com/emilkowalski/skills | `emil-design-eng`, `animate`, `review-animations`, `improve-animations`, `find-animation-opportunities`, `animation-vocabulary`, `apple-design`, `prototype`, `pick-ui-library`, `ask-sonner` (não usar `animate-expo` nem `write-swift`: este produto é web) |
| https://github.com/pbakaus/impeccable | `impeccable` |
| https://github.com/aidenybai/million | `million` **somente se** existir `SKILL.md` local. Se não existir, seguir em frente sem o pacote Million.js e **sem** abrir o GitHub nem a documentação na web. |
| https://github.com/tech-leads-club/agent-skills | `tlc-spec-driven` (execução do plano), `create-adr` (só se precisar de sucessor), `coding-guidelines`, `react-composition-patterns`, `modular-design-principles`, `playwright-skill` |
| https://github.com/Leonxlnx/taste-skill | `taste-skill` |
| https://github.com/multica-ai/andrej-karpathy-skills | `karpathy-guidelines` |

Ordem de processo: `karpathy-guidelines` + `tlc-spec-driven` no execute; depois as de UI (`impeccable`, `ui-ux-pro-max`, `emil-design-eng` e as de animação que o plano pedir); `playwright-skill` na verificação; `taste-skill` no julgamento visual contra os arquivos.

## Antes de qualquer código

1. Invocar `karpathy-guidelines` e `tlc-spec-driven`.
2. Ler por inteiro, nesta ordem:
   - `.cursor/rules/produto.mdc`
   - `docs/adr/0012-administracao-de-competencias.md`
   - `docs/adr/0013-fonte-visual-design-reference.md`
   - `docs/adr/0011-grade-fortes-na-validacao.md`
   - `docs/adr/0008-design-system-e-tokens.md` (não substitui os arquivos; não reescrever)
   - `docs/handover/FASE-7.md`
   - o plano (todas as tasks)
3. **Ler/ver cada arquivo de `design-reference/`** listado no plano, um a um, sem pular. Não resumir no lugar de abrir. Não extrair uma “paleta oficial” para o chat e trabalhar só com o resumo.
4. Trabalhar numa **branch nova** (`fase-7-design-usabilidade` ou equivalente). Não implementar em `main`/`master`.
5. **Não fazer commit nem push** a menos que eu peça nesta sessão.
6. Não alterar `git config`.

## Objetivo de produto

Há uma **área para administrar competências** (listar, abrir mês, trocar o lote ativo). Importar é só os PDFs desse lote. A casca e as telas seguem **somente** `design-reference/`. A aba Validar continua a planilha Fortes de 10 colunas (ADR 0011).

## Não fazer

- Não buscar referência visual fora de `design-reference/` (web, outros apps, bibliotecas de UI na internet).
- Não indicar nem inventar tokens no plano — o plano já só aponta arquivos; você aplica o que leu nos arquivos.
- Não reverter ADR 0002, 0005, 0010, 0011.
- Não esconder a coluna de crédito; não mandar `criar_regra: true` pela grade.
- Não animar as ~440 linhas da tabela.
- Não portar `reference/`.
- Não apagar lote `EXPORTADO`.
- Não inventar heurística para os 13 ambíguos.
- Não fazer deploy em `conciliador.projecont.com.br`.
- Não baixar limiares da suíte (ADR 0009) nem criar fixture sintética de PDF.
- Não adicionar test runner novo no frontend; Playwright já é devDependency e serve ao script de captura/checagem.

## Quando as tasks do plano passarem

1. Rodar `cd backend && .venv/bin/python -m pytest -q` e o build do frontend.
2. Playwright: fluxo da seção “Como validar” do FASE-7 (competências + demais telas, claro e escuro).
3. Atualizar `docs/handover/FASE-7.md`: **Concluída em** + resultados + lista de arquivos de `design-reference/` lidos.
4. Atualizar a tabela de fases do `README.md` se a Fase 7 ainda aparecer como “a executar”.
5. Parar. Relatar o que mudou e o que ficou para o humano (ambíguos, round-trip Fortes, deploy).

---
