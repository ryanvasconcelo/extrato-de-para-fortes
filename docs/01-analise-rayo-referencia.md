# Análise Rayo — Referência para Extrato → De/Para → FortesERP

> Extraído do monorepo Rayo em 2026-08-24.  
> Foco: o que contribui para o plano em `00-plano-engenharia.md`.

---

## 0. Veredito

O Rayo tem vários motores de conciliação e padrões de De/Para, mas **não implementa** o produto deste projeto (extrato → regras texto→conta → pendências → CSV Fortes).

| Requisito do plano | Estado no Rayo |
|---|---|
| Importação de extrato (PDF/CSV) | Parcial — `reference/extrato-financeiro/extrato-parser.js` |
| Motor De/Para (termo → conta/fornecedor) | **Ausente** no bancário; análogos em Folha Dealer e PIS/COFINS |
| Tela de resolução de não associados | **Ausente** (só filtros read-only) |
| Export modelo FortesERP (RCO010) | **Ausente** (só PDF em `specs/`) |
| Persistência SQLite/regras | **Ausente** nas conciliações (`localStorage` só em CST) |
| Arquitetura Flask + SQLite | **Não adotada** — Rayo é React/Vite client-side |

---

## 1. Mapa de módulos no Rayo (contexto)

### Sem De/Para configurável (matching por chave)

| Módulo | Chave | Uso para este projeto |
|---|---|---|
| Contas e Razão | Nr. Recibo | Baixo — outro domínio |
| Conciliação de Notas | Nº Nota | Baixo |
| Conciliação Bancária | Doc ↔ Nº Origem | Médio — UX + netting; **não** é o MVP de extrato |
| Subvenções | Chave NF-e | Baixo |

### Com De/Para (ou semi)

| Módulo | Tipo | Persistência | Prioridade aqui |
|---|---|---|---|
| Folha Fortes → Dealer | Lotação→Centro; Evento→Conta+D/C | Config JS | Alta (modelo) |
| PIS/COFINS DeParaModal | NCM/Cód → CST | React state | Alta (UX CRUD) |
| CST Assignments | NCM → CST | localStorage | Alta (persistência) |
| Categorias de extrato | Substring → categoria | Hardcoded | Alta (motor de busca) |

---

## 2. Entrada de dados (padrão Rayo)

1. DropZone / `<input type="file">`
2. `File.arrayBuffer()`
3. Parser por layout (heurística de cabeçalho)
4. Processamento no browser
5. Resultado em estado React — sem DB

LGPD: dados sensíveis não sobem para nuvem no Rayo.

### Extrato — formatos suportados no parser copiado

- XLSX/CSV: Data + Histórico/Descrição + Débito/Crédito; Bradesco/Itaú/genérico
- PDF: pdfjs, coordenadas X/Y, até 500 páginas, layout genérico

### Conciliação bancária (referência) — 3 arquivos

1. Razão ERP (SAP)
2. Relatório financeiro (Simplificado)
3. Extrato opcional (ativa auditoria diária + categorias)

Mínimo 2 arquivos SAP+Simplificado. No **MVP deste projeto**, a entrada principal é só o extrato (+ regras De/Para).

---

## 3. Arquitetura Rayo vs plano

| Aspecto | Rayo | Plano deste projeto |
|---|---|---|
| Frontend | React 19 + Vite | Web |
| Backend conciliação | Quase nenhum | Flask (sugerido) |
| Persistência | Memória / localStorage | SQLite |
| Deploy | Local | Nuvem |

Camada típica Rayo:

```
UI (Page) → Hook → Parsers → Pré-processamento → Motor → Filtros → Export
```

**Decisão aberta:** Flask+SQLite (plano) vs React+IndexedDB (padrão Rayo).

---

## 4. Banco de dados

### No Rayo (conciliações)

Sem Prisma/SQLite para extratos. Efêmero na sessão.

### Persistência existente (padrão a espelhar)

`localStorage`:

- `rayo_cst_keys` → chaves CST
- `rayo_assignments` → NCM → cstKeyId

### Modelo do plano (a implementar)

| Tabela | Campos |
|---|---|
| Extrato importado | Data, Descrição Original, Valor, Status |
| Regras De/Para | Termo de Busca, Destino, Conta Contábil |

### Modelo Folha Dealer (melhor template)

Ver `docs/referencia/folha-dealer-data-contracts.md`:

- `CenterMapping`, `AccountMappingLine`, `AccountingEntry`, `ValidationIssue`, `PayrollAccountingRun`

Sugerido para este projeto:

```text
BankMappingRule:
  id, companyId?, searchTerm, matchMode (includes|exact|regex?),
  supplierName?, accountCode, historyOverride?, active, createdAt

BankStatementLine:
  id, importBatchId, date, descriptionOriginal, debit, credit,
  status (PENDING|MATCHED|MANUAL), matchedRuleId?, accountCode?, notes?

ImportBatch:
  id, filename, importedAt, bank?, lineCount
```

---

## 5. Parsers (o que foi copiado)

### `reference/extrato-financeiro/extrato-parser.js`

- Detecta banco nas primeiras linhas
- Localiza header data/histórico/débito/crédito
- Normaliza datas (serial Excel, dd/mm/yyyy, ISO)
- Parse moeda BR/EN
- PDF: agrupa linhas por Y, propaga data, acumula descrição

Saída: `{ id, data, dataStr, descricao, debito, credito, banco }`

### `reference/banco-razao/*`

Layouts SAP e Simplificado validados em arquivos reais do cliente. Úteis se o produto cruzar extrato × razão depois.

---

## 6. Motores de conciliação (sem De/Para de regras)

### Pipeline bancário Rayo

```
Upload → auto-detect → normalize
  → [opc] extrato × financeiro por dia + categorias
  → netting (anular pares Deb/Cred)
  → reconcileBanco (Doc ↔ Origem, tolerância 0,05)
  → UI + XLSX
```

### Gap no netting

`netting-engine.js` espera `isEstorno` / `origemAnulada`, mas **nenhum parser seta esses campos**. Só anulação por pares Deb/Cred funciona de fato.

### Extrato × Financeiro

Compara invertendo lógica bancária vs contábil; tolerância R$ 0,05/dia.

---

## 7. De/Para e motor de busca

### O que o plano pede

```
para cada lançamento do extrato:
  para cada regra:
    se descrição contém termo_busca → associar conta; Conciliado
  senão → Pendente (tela de resolução)
```

### Análogo mais próximo: `categoria-detector.js`

```javascript
CATEGORIA_RULES = [
  { key: 'aplicacao', patterns: ['aplic', 'apl '] },
  { key: 'resgate', patterns: ['resgate', 'resg', ...] },
  ...
]
// lower.includes(pattern) → categoria
```

Generalizar para regras CRUD `{ term, accountCode, supplier, active }`.

### De/Para maduro: Folha (`reference/de-para-folha/`)

```
consolidar → mapAccount → mapCenter → validar blockers → AccountingEntry → export gated
```

Padrões: lookup por código, N linhas por regra, blocker vs warning, human-in-the-loop.

### UX de regras: `DeParaModal` + Assignments

Aplicar/Reverter; status Aplicada; persistir e reaplicar em lote — alinha ao teste “criar regra → status muda”.

---

## 8. Exportação

### Rayo (bancária)

XLSX multi-aba: Conciliação Principal, Anulados, Extrato Diário, Categorias.  
Arquivo: `Auditoria_Completa_<ts>.xlsx`.

### Este projeto

Gerar a partir de `specs/RCO010_ImportarLote.pdf` (ainda sem código gerador).

### Folha Dealer (referência de export ERP-ready)

Excel de conferência + TXT só após aprovação. Checklist em `docs/referencia/folha-dealer-checklist-validacao.md`.

---

## 9. Design / telas

### Conciliação bancária (copiada)

Upload 3 DropZones → StatCards → painel extrato → NettingPanel → FilterBar → Virtuoso → Export.

**Falta para o MVP:** formulário de regra, associação manual, criar regra a partir da linha, persistência.

### DeParaModal

Melhor referência de tela de regras dinâmica.

### Folha Dealer

draft → blocked → ready → approved → exported.  
Pendência no Rayo: UI visual de De/Para (`folha-dealer-pendencias-producao.md`).

---

## 10. Testes no Rayo

| Área | Automatizado? |
|---|---|
| Extrato / Bancária / Netting | Não |
| Contas e Razão / Notas | Não |
| Folha Dealer + De/Para | Sim (forte) |

Testes do plano ainda a criar:

1. Extrato real → falsos positivos de substring
2. Criar regra na UI → reprocessar → status muda

---

## 11. Lacunas a fechar neste projeto

1. Motor De/Para bancário configurável
2. CRUD de regras + reprocessamento
3. Tela de resolução de pendências
4. Export RCO010
5. Persistência (SQLite ou IndexedDB) — decisão consciente
6. Testes do fluxo
7. (Opcional) Corrigir detecção de estorno se reusar netting

---

## 12. Ordem sugerida de implementação

1. Fixar produto: extrato → De/Para → pendência → Fortes (não misturar com Doc↔Origem)
2. Decidir persistência
3. Reusar: parser + generalizar `categoria-detector` + UX `DeParaModal`/`assignments` + contratos Folha
4. Implementar gerador RCO010
5. Fixtures de extrato real + testes de falso positivo e “regra → status”

---

## 13. Glossário de status (Rayo)

| Contexto | Status |
|---|---|
| Bancária | CONCILIADO, DIVERGENTE, PENDENTE_RAZAO, PENDENTE_BANCO |
| Extrato diário | CONCILIADO / DIVERGENTE |
| Folha | draft → blocked → ready → approved → exported |

Sugestão MVP deste projeto: `PENDING | MATCHED_AUTO | MATCHED_MANUAL | EXPORTED`.
