# Design, usabilidade e administração de competências

> **For agentic workers:** REQUIRED: `karpathy-guidelines` + `tlc-spec-driven` to execute this plan task-by-task. UI skills only from the Fase 7 prompt. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The app has a dedicated surface to list, open, and switch competências; chrome and screens match `design-reference/` after every file in that tree has been read; Validar stays the 10-column Fortes grid.

**Architecture:** Keep parsing, De/Para, PATCH in-place, and `arquivo_final` as they are. `GET /api/lotes` already returns every lote. Stop treating `lotes[0]` as the session. Add a competências surface that sets the active lote; Importar only uploads into that lote. Restyle shell and screens using only files under `design-reference/` (ADR 0013). Playwright (`frontend` devDependency, `frontend/scripts/capturar-telas.mjs`) is the visual check.

**Tech Stack:** Same as today — FastAPI + SQLModel + pytest; React 19 + Vite + Tailwind. Playwright only for capture/check scripts, not a new unit-test runner.

---

## Context the next agent must not rediscover

Read before typing code (order in `docs/handover/PROMPT-SESSAO-FASE-7.md`).

Product: `.cursor/rules/produto.mdc` — Validar is the Fortes sheet; cell save is not “criar regra”.

**Do not:**

- Fetch visual references outside `design-reference/`.
- Skip any file in the inventory below (except `.DS_Store`).
- Rewrite ADR 0008, 0011, 0012, or 0013. Divergence = successor ADR.
- Revert ADR 0002 / 0005 / 0010 / 0011.
- Hide crédito; send `criar_regra: true` from the grid; animate ~440 table rows.
- Port `reference/`; deploy; lower ADR 0009 thresholds; add synthetic PDFs.
- Delete `EXPORTADO` lotes.
- Commit unless the human asked in that session.

**Do not commit** unless the human running the session asked.

---

## Visual inventory (mandatory; skip none)

Open and consume each path. Do not replace this list with a summary, with ADR 0008, or with `frontend/src/estilos/tokens.css`.

### `design-reference/design clickip/`

1. `design-reference/design clickip/animacao.mov`
2. `design-reference/design clickip/darkmode referencia.webp`
3. `design-reference/design clickip/font hierarquia.webp`
4. `design-reference/design clickip/icons referencia.png`
5. `design-reference/design clickip/icons referencia.webp`
6. `design-reference/design clickip/logo.svg`
7. `design-reference/design clickip/overlay referencia.webp`
8. `design-reference/design clickip/referencia color.webp`
9. `design-reference/design clickip/referencia de UI 2.webp`
10. `design-reference/design clickip/referencia de UI 3.webp`
11. `design-reference/design clickip/referencia de UI.webp`
12. `design-reference/design clickip/referencia hierarquia.webp`
13. `design-reference/design clickip/referencia shadows e destaques.webp`
14. `design-reference/design clickip/shadow ui referencia.webp`
15. `design-reference/design clickip/ui de referencia.webp`
16. `design-reference/design clickip/ui referencia 2.webp`
17. `design-reference/design clickip/ui-referencia.webp`
18. `design-reference/design clickip/ux referencia.webp`

### `design-reference/design system/`

19. `design-reference/design system/clickip-components.css`
20. `design-reference/design system/clickip-design-system.html`
21. `design-reference/design system/clickip-tailwind.css`
22. `design-reference/design system/clickip-tokens.css`
23. `design-reference/design system/clickip-tokens.json`

Ignore `design-reference/design clickip/.DS_Store`.

This plan does **not** restate colors, type scales, shadows, or component recipes. Those live in the files above.

---

## File map

| File | Responsibility after this plan |
|---|---|
| `frontend/src/telas/Competencias.tsx` | **New.** List lotes, open a month, set the active lote. |
| `frontend/src/App.tsx` | Active lote is chosen, not `lotes[0]`; competências surface wired; shell restyle. |
| `frontend/src/telas/Importacao.tsx` | PDFs of the **active** lote only — not the place that “is” competência. |
| `frontend/src/telas/Pendencias.tsx` | Same job; chrome from `design-reference/`. |
| `frontend/src/telas/Validacao.tsx` | Still PlanilhaFortes + approve/export (ADR 0011); chrome from `design-reference/`. |
| `frontend/src/telas/PlanilhaFortes.tsx` | 10 columns unchanged in **structure**; visual only if the files demand it **without** hiding crédito or adding “Criar regra”. |
| `frontend/src/telas/Exportacao.tsx` | Conferência remains secondary; chrome from `design-reference/`. |
| `frontend/src/estilos/*` | Align with files 19–23 after reading them; no hex in components (ADR 0008 still applies). |
| `frontend/src/componentes/*` | Primitives follow the same files. |
| `frontend/src/api/cliente.ts` | `lotes` / `criarLote` already exist; only change if the UI needs a field the JSON already has. |
| `backend/app/api.py` | `GET /api/lotes` already lists. Add a route **only** if a test proves a gap (do not add delete). |
| `backend/tests/test_api.py` | Tests that the list is usable for switching (more than one lote). |
| `frontend/scripts/capturar-telas.mjs` | Wait for competências + `table.planilha-fortes`; claro/escuro. |
| `docs/handover/FASE-7.md` | Fill **Concluída em** at the end. |
| `docs/adr/0012-*.md`, `0013-*.md` | **Do not rewrite.** |

---

### Task 1: Read the inventory (no production code)

**Files:** none created.

- [ ] **Step 1:** Open files 1–18 in `design-reference/design clickip/` in order. Watch `animacao.mov`. Do not skip webp/png/svg.

- [ ] **Step 2:** Open files 19–23 in `design-reference/design system/` in order. Read the HTML and CSS/JSON to the end.

- [ ] **Step 3:** Tick this task only after all 23 paths were actually opened. Note the list in your report. If a file is unreadable, stop with BLOCKED — do not invent a substitute from the web.

Skip commit.

---

### Task 2: List of lotes is enough to pick one (API lock)

**Files:**

- Test: `backend/tests/test_api.py`
- Modify `backend/app/api.py` **only if** the test proves `GET /api/lotes` is insufficient (it should not — it already returns `id`, `competencia`, `status`, `lancamentos`, `arquivos`).

- [ ] **Step 1: Write the failing test** (add a class; do not hang it on `lote_junho` if that collides — use fresh competências):

```python
class TestAdministracaoDeCompetencias:
    def test_listar_lotes_inclui_dois_meses(self, cliente):
        a = cliente.post("/api/lotes", params={"competencia": "012027"}).json()
        b = cliente.post("/api/lotes", params={"competencia": "022027"}).json()
        assert a["id"] != b["id"]
        lista = cliente.get("/api/lotes").json()
        por_id = {l["id"]: l for l in lista}
        assert a["id"] in por_id and b["id"] in por_id
        assert por_id[a["id"]]["competencia"] == "012027"
        assert por_id[b["id"]]["competencia"] == "022027"
        assert "status" in por_id[a["id"]]
        assert "lancamentos" in por_id[a["id"]]
```

- [ ] **Step 2:** Run

```bash
cd backend && .venv/bin/python -m pytest tests/test_api.py -q -k AdministracaoDeCompetencias
```

Expected: PASS if `GET /api/lotes` already matches. If FAIL, fix the list payload only — no delete endpoint.

- [ ] **Step 3:** Do not add `DELETE /api/lotes/{id}`.

Skip commit.

---

### Task 3: Active lote is chosen, not `lotes[0]`

**Files:**

- Create: `frontend/src/telas/Competencias.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/telas/Importacao.tsx`

- [ ] **Step 1:** `Competencias` props: `{ lotes, loteAtivoId, onEscolher, onCriou }` where `onCriou` receives the `Lote` from `api.criarLote`. Render the list from `lotes` (`id`, `competencia`, `status`, `lancamentos`). Control to open a new month (`MMYYYY` + `api.criarLote`) lives **here**, not as the hero of Importar. Visual from files 1–23 after Task 1 — do not copy recipes into this plan.

- [ ] **Step 2:** In `App.tsx`, stop `setLote(lotes[0])` as the only resume rule. Keep the chosen `lote.id` as the session. Optional: `localStorage` key `loteIdAtivo` so reload does not jump to the newest empty rascunho (the Fase 6 trap). If the stored id is missing from `GET /api/lotes`, pick another lote in the list — still not “always `[0]`” without showing the list.

- [ ] **Step 3:** `Importacao` keeps drag-and-drop and “Insumos do mês” for the **active** lote. Remove or demote the block that presents itself as administering competência (the “Competência” / “Abrir lote” card). Opening a month is Task 3 Step 1.

- [ ] **Step 4:**

```bash
cd frontend && npx tsc -b --noEmit
```

Expected: no errors.

Skip commit.

---

### Task 4: Restyle shell and journey screens from the inventory

**Files:**

- Modify: `frontend/src/App.tsx` (shell, nav, theme)
- Modify: `frontend/src/telas/Importacao.tsx`
- Modify: `frontend/src/telas/Pendencias.tsx`
- Modify: `frontend/src/telas/Validacao.tsx`
- Modify: `frontend/src/telas/Exportacao.tsx`
- Modify: `frontend/src/componentes/primitivos.tsx` and `frontend/src/componentes/BuscaConta.tsx` as needed
- Modify: `frontend/src/estilos/global.css`, `frontend/src/estilos/tokens.css`, `frontend/src/estilos/planilha.css` only after files 19–23 (and 1–18) were read — still no raw hex in *components* (ADR 0008)

- [ ] **Step 1:** Invoke `impeccable`, `ui-ux-pro-max`, `taste-skill`, `emil-design-eng`. Use `find-animation-opportunities` / `animate` only for chrome that the inventory actually moves — **not** for `table.planilha-fortes` rows (ADR 0008).

- [ ] **Step 2:** Apply the inventory to casca, competências, Importar, Pendências, Validar (around the grid), Exportar. Pendências remains the only place that creates a De/Para rule.

- [ ] **Step 3:** Validar still: 10 columns, crédito always visible, no “Criar regra” checkbox, `api.editar` stays `{ criar_regra: false, ... }`.

- [ ] **Step 4:**

```bash
cd frontend && npx tsc -b --noEmit && npx vite build
```

Expected: success.

Skip commit.

---

### Task 5: Playwright check of the running UI

**Files:**

- Modify: `frontend/scripts/capturar-telas.mjs`

- [ ] **Step 1:** Invoke `playwright-skill`. Backend `:8000` and Vite (`localhost` / `[::1]:5173`) must be up. Do not add Jest/Vitest.

- [ ] **Step 2:** Script must, in claro and escuro:

  1. Land on competências (or the surface Task 3 added) and wait for a lote list (not only `lotes[0]`).
  2. Open Validar and wait for `table.planilha-fortes`.
  3. Screenshot Importar, Pendências, Validar, Exportar, competências.
  4. Assert in the script (or a tiny sibling script in the same folder) that Validar thead still has 10 cells including the ` Valor ` label with spaces, and that no `getByRole('checkbox', { name: /criar regra/i })` exists on Validar.

- [ ] **Step 3:** If the extra “Criar regra” shot on Pendências times out because the active lote has zero pendências, document it in FASE-7 — do not invent a PDF fixture.

- [ ] **Step 4:** Run the script; keep PNGs under `docs/telas/` as today.

Skip commit.

---

### Task 6: Full suite + handover

**Files:**

- Modify: `docs/handover/FASE-7.md`
- Modify: `README.md` phase table if still “a executar”

- [ ] **Step 1:**

```bash
cd backend && .venv/bin/python -m pytest -q
```

Expected: existing 78+ tests green, plus Task 2. Do not lower ADR 0009 thresholds.

- [ ] **Step 2:** Fill FASE-7: **Concluída em**, commands, Playwright result, **checklist of all 23 `design-reference/` files as lidos**.

- [ ] **Step 3:** README phase 7 no longer “a executar” if this task finished the work.

Skip commit unless the human asked.

---

## Out of this plan (human / later)

| Item | Owner |
|---|---|
| 13 rows in `docs/base-depara-inicial.xlsx` sheet `Ambiguos` | Accountant |
| Import generated XLSX into Fortes ERP | Accountant — successor to ADR 0010 if it fails |
| New competência with the accountant (accuracy, ADR 0009) | Accountant — not the in-app list |
| Deploy `https://conciliador.projecont.com.br` | Ops |
| Delete competência / CRUD of rules | Later |

---

## Self-review (spec coverage)

| Ask | Task |
|---|---|
| Every `design-reference/` file consumed | 1 |
| Admin competências (list / open / switch) | 2, 3 |
| Importar is not the competência admin | 3, 4 |
| Visual from files only; Playwright | 4, 5 |
| ADR 0011 grid intact | 4, 5 |
| Handover + README | 6 |
| No tokens/recipes in this plan | entire document |
