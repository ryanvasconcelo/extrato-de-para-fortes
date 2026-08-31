# Código de referência (Rayo)

Cópias isoladas para estudo e reaproveitamento. **Não** é um app executável.

## Pastas

### `extrato-financeiro/` — prioridade alta
- `extrato-parser.js` — PDF (pdfjs) + XLSX; detecta Bradesco/Itaú/genérico
- `categoria-detector.js` — loop `includes(termo)` (modelo do motor de busca)
- `extrato-reconciler.js` — totais dia a dia extrato × financeiro
- `financeiro-parser.js` — wrapper fino

### `banco-razao/` — prioridade média
Matching por documento (outro caso de uso). Útil para netting/tolerância R$ 0,05 e parsers de razão/saldo se o produto crescer além do extrato puro.

### `conciliacao-bancaria/` — prioridade média (UX)
- `useConciliacaoBancaria.js` — orquestração upload → parse → netting → reconcile
- `ConciliacaoBancariaPage.jsx` — DropZones, filtros, Virtuoso, export XLSX multi-aba

### `de-para-ui/` + `assignments/` — prioridade alta (regras)
- `DeParaModal.jsx` — CRUD visual de regras De→Para
- `cst-assignments.js` — persistência `localStorage` + apply em lote + export CSV
- `useAssignments.js` — hook React espelhando o storage

### `de-para-folha/` — prioridade alta (modelo de domínio)
Melhor referência de De/Para “de produção”:
- `account-mapper.js` / `center-mapper.js` — lookup de regras ativas
- `journal-builder.js` — aplica mappings + emite issues bloqueantes
- `contracts.js` / `validation-summarizer.js` — códigos de validação e resumo

Espelhar como `BankMappingRule { searchTerm, accountCode, supplier, active }` no MVP.

## Dependências originais (Rayo)

- `xlsx`, `pdfjs-dist`, `react`, `react-virtuoso`
- Imports de `Icons`, `AppLayout`, etc. **não** foram copiados — adaptar ao criar o app real
