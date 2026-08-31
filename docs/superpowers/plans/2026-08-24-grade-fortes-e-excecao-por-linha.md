# Grade Fortes e exceção por linha

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The Validar screen becomes the 10-column Fortes import spreadsheet; a cell edit on one row is what gets exported, without rewriting the De/Para rule of sibling rows.

**Architecture:** Keep parsing, classification, and `arquivo_final` as they are. Change the edit contract: `PATCH /api/lancamentos/{id}` with `criar_regra=false` (the grid default) mutates that `Lancamento` in place, revalidates only that row, and leaves siblings untouched. The React table renders the same 10 columns as `LINHA_MODELO` + `linha_fortes()`, with inline save. Pendências remains the place to **create a rule** for a supplier; the grid is the place to **handle an exception**.

**Tech Stack:** FastAPI + SQLModel + pytest (backend). React 19 + Vite + Tailwind tokens (frontend). Playwright is already a frontend devDependency and is used only for `frontend/scripts/capturar-telas.mjs` — do not add a new test runner.

---

## Context the next agent must not rediscover

Read, in this order, before typing code:

1. `.cursor/rules/produto.mdc` — product invariants (this plan exists to implement them).
2. `docs/adr/0011-grade-fortes-na-validacao.md` — **already written.** Do not rewrite.
3. `docs/adr/0010-layout-export-fortes.md` — 10 columns, hybrid row 1, `" Valor "` with spaces.
4. `docs/handover/FASE-6.md` — phase brief, traps, verification.
5. `fluxograma/` — two client prints: jornada + mapping of Itaú × Contas a Pagar → Fortes XLSX.

**Do not:**

- Revert ADR 0002 (substring matching) or ADR 0005 (enrich SISPAG).
- Remove the model row from the XLSX.
- Port anything from `reference/`.
- Treat this plan as “build deploy to conciliador.projecont.com.br”. Hosting URL is recorded; deploy is out of scope.
- Resolve the 13 `AMBIGUO_CONTA` suppliers by inventing a heuristic. That is a conversation with the accountant, not code.
- Import a file into Fortes ERP. After this plan the file is *ready*; the round-trip is a human step listed at the end.

**Do not commit** unless the human running the session asked for commits. The commit steps below are optional and skipped when in doubt.

---

## File map

| File | Responsibility after this plan |
|---|---|
| `backend/app/api.py` | `PATCH` edits one row in place when `criar_regra` is false; still reprocesses the lote only when a rule is created. |
| `backend/app/motor/processador.py` | When reprocessing, MANUAL overrides keep `valor` and `conta_credito` too (not only débito/centro/histórico). |
| `backend/app/export_fortes.py` | Unchanged layout. Confirm `linha_fortes()` reads the mutated `Lancamento`. |
| `backend/tests/test_api.py` | New tests: sibling isolation, export reflects PATCH, `criar_regra=true` still fans out. |
| `frontend/src/api/cliente.ts` | `editar` payload includes crédito/valor; `criar_regra` defaults false. |
| `frontend/src/telas/PlanilhaFortes.tsx` | **New.** 10-column spreadsheet. |
| `frontend/src/telas/Validacao.tsx` | Toolbar + `PlanilhaFortes` + approve/export on this screen. |
| `frontend/src/estilos/planilha.css` | Spreadsheet chrome (grid lines, white cells). Tokens only — no raw hex. |
| `frontend/src/estilos/global.css` | Import `planilha.css`. |
| `frontend/src/App.tsx` | Wider main on Validar; pass `lote`/`resumo` into `Validacao`. |
| `docs/adr/0011-grade-fortes-na-validacao.md` | **New.** Supersedes “hide crédito when constant” from FASE-3. |
| `docs/handover/FASE-6.md` | **New.** What shipped, how to verify, what remains human. |

---

## Column contract (lock this)

UI row 1 is exactly `LINHA_MODELO` from `backend/app/export_fortes.py`. Data rows are `linha_fortes()`.

| Col | Header on row 1 | Source | Grid |
|---|---|---|---|
| A | `0001` | `lancamento.filial` | visible, not editable |
| B | `Data` | `pagamento.data` as `dd/mm/yyyy` | visible, not editable (fact from the statement) |
| C | `Débito` | `lancamento.conta_debito` | **editable** |
| D | `Crédito` | `lancamento.conta_credito` | **editable** (always shown, even if constant) |
| E | ` Valor ` | `lancamento.valor` | **editable** |
| F | `Histórico` | `lancamento.historico` | **editable** |
| G | `0001` (centro) | `lancamento.centro_custo` | **editable** |
| H | `001` | constant | visible, not editable |
| I | `0001` | constant | visible, not editable |
| J | `001` | constant | visible, not editable |

Favorecido, CPF/CNPJ, and status are **not columns**. Status is a row tone (PENDENTE / MANUAL / blocker) plus `title` on the row with the favorecido. Filters above the grid may still search favorecido.

Creating a De/Para rule stays on the **Pendências** tab (and an optional explicit control — not the default of a cell save).

---

### Task 1: PATCH mutates one row; siblings stay put

**Files:**
- Modify: `backend/app/api.py` (`EdicaoLancamento`, `editar_lancamento`, new helpers)
- Modify: `backend/app/motor/processador.py` (`_um`, MANUAL override block)
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

Add this class to `backend/tests/test_api.py` (keep using the existing `cliente` / `lote_junho` fixtures in that file):

```python
class TestExcecaoPorLinha:
    def _par_auto(self, cliente, lote_id):
        from collections import defaultdict

        auto = cliente.get(
            f"/api/lotes/{lote_id}/lancamentos", params={"status": "AUTO"}
        ).json()
        por_doc = defaultdict(list)
        for linha in auto:
            if linha["documento"]:
                por_doc[linha["documento"]].append(linha)
        par = next(v for v in por_doc.values() if len(v) >= 2)
        return par[0], par[1]

    def test_editar_uma_linha_nao_mexe_na_irma(self, cliente, lote_junho):
        a, b = self._par_auto(cliente, lote_junho["id"])
        id_a, id_b = a["id"], b["id"]
        conta_b = b["conta_debito"]
        conta_nova = cliente.get("/api/plano-contas", params={"q": "4."}).json()[0][
            "codigo"
        ]
        assert conta_nova != a["conta_debito"]

        resposta = cliente.patch(
            f"/api/lancamentos/{id_a}",
            json={"conta_debito": conta_nova, "criar_regra": False},
        )
        assert resposta.status_code == 200

        depois = {
            l["id"]: l
            for l in cliente.get(f"/api/lotes/{lote_junho['id']}/lancamentos").json()
        }
        assert id_a in depois and id_b in depois, (
            "edicao sem regra nao pode recriar o lote e trocar os ids"
        )
        assert depois[id_a]["conta_debito"] == conta_nova
        assert depois[id_a]["status"] == "MANUAL"
        assert depois[id_b]["conta_debito"] == conta_b
        assert depois[id_b]["status"] == "AUTO"

    def test_criar_regra_true_ainda_reprocessa_irmas(self, cliente, lote_junho):
        a, b = self._par_auto(cliente, lote_junho["id"])
        documento = a["documento"]
        conta_nova = cliente.get("/api/plano-contas", params={"q": "3.01"}).json()[0][
            "codigo"
        ]
        cliente.patch(
            f"/api/lancamentos/{a['id']}",
            json={"conta_debito": conta_nova, "criar_regra": True},
        )
        depois = cliente.get(f"/api/lotes/{lote_junho['id']}/lancamentos").json()
        irmas_auto = [
            l
            for l in depois
            if l["documento"] == documento and l["status"] == "AUTO"
        ]
        assert irmas_auto, "criar_regra deve reclassificar as irmas como AUTO"
        assert all(l["conta_debito"] == conta_nova for l in irmas_auto)
```


- [ ] **Step 2: Run the new tests and confirm they fail**

```bash
cd backend && .venv/bin/python -m pytest tests/test_api.py -q -k ExcecaoPorLinha
```

Expected: FAIL — after PATCH, ids are new (full `_reprocessar`) and/or the sibling account changed.

- [ ] **Step 3: Implement in-place edit when `criar_regra` is false**

In `backend/app/api.py`, extend `EdicaoLancamento`:

```python
class EdicaoLancamento(BaseModel):
    conta_debito: str | None = None
    conta_credito: str | None = None
    centro_custo: str | None = None
    historico: str | None = None
    valor: float | None = None
    editado_por: str = "contador"
    criar_regra: bool = False
```

Replace `editar_lancamento` so that:

1. Apply field updates on the existing `Lancamento` (normalize contas via `normalizar_conta`; reject unknown contas with 422 like today; reject `valor is not None and valor <= 0` with 422 `Valor nao e positivo.`).
2. Set `status = MANUAL`, `editado_por`, `editado_em`.
3. If `criar_regra` is true **and** there is `conta_debito`: call `_garantir_regra` then `return _reprocessar(sessao, lote)` (existing behaviour).
4. If `criar_regra` is false: **do not** delete/recreate lançamentos. Call a new `_revalidar_linha(sessao, lote, lancamento)` that:
   - deletes `Ocorrencia` rows for that `lancamento.id` only;
   - runs `Validador(list(sessao.exec(select(PlanoContas)))).validar(lancamento)`;
   - drops `REGRA_AMBIGUA` and `CONTA_DEBITO_AUSENTE` when `lancamento.conta_debito` is set (same rule as `processador.py`);
   - inserts new `Ocorrencia`s via `para_ocorrencias`;
   - recomputes lote status from remaining blockers (`BLOQUEADO` if any blocker left, else `PRONTO` if the lote has rows);
   - returns the same `ResumoLote` shape as `_reprocessar`.

Keep `test_edicao_manual_sobrevive_ao_reprocessamento` green: it already sends `criar_regra: False` then creates an unrelated rule (which **does** reprocess). MANUAL override in `processador._um` must still win — extend that block:

```python
        if edicao is not None:
            lancamento.conta_debito = edicao.conta_debito or lancamento.conta_debito
            lancamento.conta_credito = edicao.conta_credito or lancamento.conta_credito
            lancamento.centro_custo = edicao.centro_custo or lancamento.centro_custo
            lancamento.historico = edicao.historico or lancamento.historico
            if edicao.valor:
                lancamento.valor = edicao.valor
            lancamento.status = StatusLancamento.MANUAL
            lancamento.editado_por = edicao.editado_por
            lancamento.editado_em = edicao.editado_em
            achados = [a for a in achados if a.codigo != Codigo.REGRA_AMBIGUA]
```

Use `if edicao.valor:` only if zero is invalid; prefer `if edicao.valor is not None` **on the PATCH path**. On reprocess, `edicao` is the previous `Lancamento` ORM object, so `valor` is always set — copying it is correct (`lancamento.valor = edicao.valor`).

- [ ] **Step 4: Re-run the new tests and the old edit/export tests**

```bash
cd backend && .venv/bin/python -m pytest tests/test_api.py -q -k "ExcecaoPorLinha or edicao_manual or Exportacao or Trava"
```

Expected: PASS.

- [ ] **Step 5: Commit (only if the human asked)**

```bash
git add backend/app/api.py backend/app/motor/processador.py backend/tests/test_api.py
git commit -m "$(cat <<'EOF'
fix: cell edit stays on one row unless a rule is requested

EOF
)"
```

---

### Task 2: Edited débito, crédito, valor, histórico, centro appear in the Fortes XLSX

**Files:**
- Modify: `backend/tests/test_api.py` (`TestExportacaoLiberada`)
- Modify: `backend/app/export_fortes.py` only if a test proves `linha_fortes()` reads a stale field (it should not — it already reads the `Lancamento`)

- [ ] **Step 1: Write the failing test**

Do **not** hang this on `lote_limpo`: that fixture is class-scoped and `test_aprovar_e_exportar` already exports it. Add a function-scoped copy next to `lote_limpo`:

```python
    @pytest.fixture
    def lote_exportavel(self, cliente):
        lote = cliente.post("/api/lotes", params={"competencia": "082026"}).json()
        cliente.post(
            f"/api/lotes/{lote['id']}/arquivos",
            files={
                "arquivo": (
                    ITAU_EXTRATO.name,
                    ITAU_EXTRATO.read_bytes(),
                    "application/pdf",
                )
            },
        )
        conta = cliente.get("/api/plano-contas", params={"q": "3."}).json()[0]["codigo"]
        for p in cliente.get(f"/api/lotes/{lote['id']}/pendencias").json():
            cliente.post(
                "/api/regras",
                json={
                    "fornecedor_nome": p["fornecedor"],
                    "documento": p["documento"],
                    "conta_debito": conta,
                    "centro_custo": "0001",
                },
            )
        return lote
```

Trap documented in `docs/handover/FASE-3.md`. Then:

```python
    def test_edicao_manual_sai_no_arquivo_final(self, cliente, lote_exportavel):
```
        linhas = cliente.get(f"/api/lotes/{lote_limpo['id']}/lancamentos").json()
        alvo = linhas[0]
        conta = cliente.get("/api/plano-contas", params={"q": "2.01"}).json()[0]["codigo"]
        cliente.patch(
            f"/api/lancamentos/{alvo['id']}",
            json={
                "conta_debito": conta,
                "historico": "EXCECAO POR LINHA NO EXPORT",
                "centro_custo": "0009",
                "valor": 123.45,
                "criar_regra": False,
            },
        )
        assert cliente.post(f"/api/lotes/{lote_limpo['id']}/aprovar").status_code == 200
        resposta = cliente.get(f"/api/lotes/{lote_limpo['id']}/exportar")
        assert resposta.status_code == 200
        ws = openpyxl.load_workbook(BytesIO(resposta.content)).active
        encontrados = [
            row
            for row in ws.iter_rows(min_row=2, max_col=10, values_only=True)
            if row[5] == "EXCECAO POR LINHA NO EXPORT"
        ]
        assert len(encontrados) == 1
        linha = encontrados[0]
        assert linha[2] == conta
        assert linha[4] == 123.45
        assert linha[6] == "0009"
```

- [ ] **Step 2: Run it**

```bash
cd backend && .venv/bin/python -m pytest tests/test_api.py -q -k edicao_manual_sai_no_arquivo_final
```

Expected: FAIL until Task 1 PATCH accepts `valor` and does not wipe it on approve. Approve must **not** reprocess away MANUAL fields — if it does, stop and keep MANUAL through `_reprocessar` (already the design).

- [ ] **Step 3: Minimal fix if export still shows the old value**

`linha_fortes` already uses `lancamento.valor` / `conta_debito` / `historico` / `centro_custo`. If the test fails, the bug is PATCH or reprocess, not the generator. Do not change the 10-column layout.

- [ ] **Step 4: Run export tests**

```bash
cd backend && .venv/bin/python -m pytest tests/test_api.py -q -k "Exportacao or ArquivoFinal or edicao_manual"
```

Expected: PASS. `test_linha_modelo_confere_com_o_arquivo_do_cliente` still compares against `CLICK SCM 062026.xlsx`.

---

### Task 3: Confirm ADR 0011 is linked (do not rewrite)

**Files:**
- Already exists: `docs/adr/0011-grade-fortes-na-validacao.md`
- Modify only if missing: `README.md` ADR table (row 0011)

- [ ] **Step 1: Read ADR 0011**

Confirm it still matches this plan (grid = 10 Fortes columns, crédito always visible, cell save does not set `criar_regra`). Do **not** edit the ADR body. If implementation had to diverge, write a successor ADR instead.

- [ ] **Step 2: Confirm README lists 0011**

The row should already be in `README.md`. If a rebase dropped it, add:

`| [0011](docs/adr/0011-grade-fortes-na-validacao.md) | Validar é a planilha Fortes; edição de linha não cria regra |`

This task is a checkpoint, not a rewrite. Mark complete and continue.

---

### Task 4: Spreadsheet CSS (tokens only)

**Files:**
- Create: `frontend/src/estilos/planilha.css`
- Modify: `frontend/src/estilos/global.css` (add `@import "./planilha.css";`)

- [ ] **Step 1: Add the spreadsheet classes**

Match the client Excel: white cells, 1px grey grid, compact row height, tabular numbers, no row animation. Use existing CSS variables from `tokens.css` (`--stroke-neutral-weak`, `--background-neutral-weaker`, `--n-0`, `--text-neutral-strong`). **No hex in this file** except if you only reference variables.

```css
.planilha-fortes {
  width: 100%;
  border-collapse: collapse;
  background: var(--background-neutral-weaker);
  color: var(--text-neutral-strong);
  font-size: 12px;
  font-family: "Calibri", "Segoe UI", ui-sans-serif, system-ui, sans-serif;
}

.planilha-fortes th,
.planilha-fortes td {
  border: 1px solid var(--stroke-neutral-weak);
  padding: 2px 6px;
  font-weight: 400;
  vertical-align: middle;
}

.planilha-fortes thead th {
  background: var(--background-neutral-weaker);
  font-weight: 400;
  text-align: left;
  position: sticky;
  top: 0;
  z-index: 1;
}

.planilha-fortes .celula-valor {
  font-variant-numeric: tabular-nums;
  text-align: right;
  font-family: ui-monospace, "Cascadia Mono", monospace;
}

.planilha-fortes .celula-conta {
  font-family: ui-monospace, "Cascadia Mono", monospace;
  white-space: nowrap;
}

.planilha-fortes tr[data-estado="PENDENTE"] td {
  background: var(--background-error-weaker);
}

.planilha-fortes tr[data-estado="MANUAL"] td {
  background: var(--background-warning-weaker);
}

.planilha-fortes input {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 0;
  font: inherit;
  color: inherit;
}
```

- [ ] **Step 2: Confirm no raw hex in new UI files**

```bash
rg -n "#[0-9a-fA-F]{6}" frontend/src/telas frontend/src/estilos/planilha.css
```

Expected: empty (or only `tokens.css`, which already holds the palette).

---

### Task 5: `PlanilhaFortes` — 10 columns, always including crédito

**Files:**
- Create: `frontend/src/telas/PlanilhaFortes.tsx`
- Modify: `frontend/src/api/cliente.ts` (`editar` type)

- [ ] **Step 1: Extend the client**

In `frontend/src/api/cliente.ts`, change `api.editar`:

```typescript
  editar: (
    lancamentoId: number,
    edicao: {
      conta_debito?: string;
      conta_credito?: string;
      centro_custo?: string;
      historico?: string;
      valor?: number;
      criar_regra?: boolean;
    },
  ) =>
    pedir<Resumo>(`/lancamentos/${lancamentoId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ criar_regra: false, ...edicao }),
    }),
```

Never send `criar_regra: true` from the grid.

- [ ] **Step 2: Implement the grid**

`PlanilhaFortes` props: `{ lancamentos, editavel, onEditou, onErro }`.

Render `<table className="planilha-fortes">` with:

- `thead` one row: `0001`, `Data`, `Débito`, `Crédito`, ` Valor `, `Histórico`, `0001`, `001`, `0001`, `001` (copy the strings from `LINHA_MODELO` — including the spaces in `" Valor "`).
- `tbody`: one `<tr data-estado={l.status}>` per lançamento, `title={l.favorecido}`.
- Columns A/H/I/J: plain text.
- Column B: `l.data`.
- Columns C–G when `editavel`: click → input (for C and D, reuse `BuscaConta` **or** a compact `input` that PATCHes the typed code on blur — `BuscaConta` is the safer choice for débito/crédito because of the 1.516-account plan). On blur/Enter, call `api.editar` with **only the changed field** plus implicit `criar_regra: false`.
- Column E: parse with `Number(valor.replace(",", "."))` or keep using the existing number and format with `dinheiro` when not editing.
- When not `editavel` (lote `APROVADO` / `EXPORTADO`): all cells read-only.

Do **not** include Favorecido or Estado columns. Do **not** hide crédito. Do **not** animate rows.

Empty débito shows as blank cell (not “—”), so it still looks like Excel; the row tone already marks PENDENTE.

- [ ] **Step 3: Typecheck**

```bash
cd frontend && npx tsc -b --noEmit
```

Expected: no errors.

---

### Task 6: Validar screen = toolbar + grid + approve/export

**Files:**
- Modify: `frontend/src/telas/Validacao.tsx` (replace the current HTML table; keep filters)
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/telas/Exportacao.tsx` only to retitle the conference download as secondary (“baixar conferência com ocorrências”), not the place you review the Fortes file

- [ ] **Step 1: Change `Validacao` props**

```tsx
export function Validacao({
  lote,
  resumo,
  lancamentos,
  editavel,
  onEditou,
  onMudou,
}: {
  lote: Lote;
  resumo: Resumo | null;
  lancamentos: Lancamento[];
  editavel: boolean;
  onEditou: () => void;
  onMudou: () => void;
}) {
```

Keep the existing filter chips and search. Under them: a one-line summary `N lançamentos · R$ soma · B blockers` using `resumo` / filtered `soma`. Then `<PlanilhaFortes ... />`.

Below the grid, a compact action row (not a three-step wizard):

- If `lote.status === "BLOQUEADO"`: text “Resolva as linhas destacadas (sem débito) ou crie a regra na aba Pendências.”
- If `lote.status === "PRONTO"`: button “Aprovar competência” → `api.aprovar(lote.id)` then `onMudou()`.
- If `lote.status === "APROVADO"` or `"EXPORTADO"`: button “Baixar arquivo Fortes” → `baixarPlanilha(`/lotes/${lote.id}/exportar`, `fortes-${lote.competencia}.xlsx`)`.
- Optional secondary button “Baixar conferência” calling `/conferencia` — do not lead with it.

- [ ] **Step 2: Wire `App.tsx`**

Pass `lote` and `resumo` into `Validacao`. Widen the Validar main: when `aba === "validar"`, drop `max-w-7xl` on `<main>` (use `max-w-[1600px]` or none) so 10 columns fit.

- [ ] **Step 3: Typecheck and production build**

```bash
cd frontend && npx tsc -b --noEmit && npx vite build
```

Expected: success.

---

### Task 7: Full backend suite + visual capture

**Files:**
- Modify: `frontend/scripts/capturar-telas.mjs` — on the Validar screenshot, wait for `table.planilha-fortes` instead of a 600ms sleep if possible
- Create: `docs/handover/FASE-6.md`

- [ ] **Step 1: Run the whole backend suite**

```bash
cd backend && .venv/bin/python -m pytest -q
```

Expected: 71+ new tests green, ~40s. Do **not** lower ADR 0009 thresholds. Do **not** add synthetic PDF fixtures.

- [ ] **Step 2: Manual verification (required for UI)**

With backend on `:8000` and `npm run dev`:

1. Import the three June PDFs (or resume the existing lote).
2. Open Validar: 10 columns, crédito visible on every row, row 1 looks like the Excel model row.
3. Change débito on **one** of two lines that share a supplier (or any AUTO pair). Save. Reload. The other line still has the old account.
4. Confirm the checkbox “Criar regra” is **not** on the grid.
5. Pendências: creating a rule still updates all lines of that supplier.
6. After blockers are gone: Aprovar on Validar, then download. Open the XLSX — the edited cell is there; 10 columns; model row intact.

If no browser tools are available, say so in FASE-6 and still run `capturar-telas.mjs` against a running app with June loaded:

```bash
cd frontend && node scripts/capturar-telas.mjs
```

- [ ] **Step 3: Write `docs/handover/FASE-6.md`**

One page: what shipped, the two commands to verify, traps (`criar_regra` must stay false on the grid; crédito stays a column), and the human leftovers below.

---

## Out of this plan (human / later)

These are remaining product gaps that **code in this plan must not fake**:

| Item | Owner |
|---|---|
| Review the 13 rows in `docs/base-depara-inicial.xlsx` sheet `Ambiguos` | Accountant |
| Import a generated XLSX into Fortes ERP | Accountant — if it fails, successor ADR to 0010 |
| RF-01.7 reject PDF whose period ≠ lote competência | Later, small backend task |
| Deploy `https://conciliador.projecont.com.br` | Ops — URL is already in README and `.cursor/rules/produto.mdc` |
| CRUD screen to list/deactivate rules | Later; Pendências + grid cover the jornada |

---

## Self-review (spec coverage)

| Gap from the audit / client confirmation | Task |
|---|---|
| Grid is the Fortes spreadsheet (10 cols, Excel look) | 4, 5, 6 |
| Crédito always visible | 5 (and ADR 0011) |
| What you edit is what you export | 1, 2 |
| Same supplier, different accounts, one cell | 1 |
| `criar_regra` is not the default | 1, 5 |
| Approve/export from the spreadsheet | 6 |
| Do not replace the grid with the conference XLSX | 6 |
| Motor/export layout (ADR 0010) unchanged | 2 |
| 13 ambiguous suppliers / Fortes round-trip / hosting | Out of plan |
