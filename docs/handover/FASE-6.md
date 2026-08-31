# Handover — Fase 6: Grade Fortes e exceção por linha

- **Concluída em:** 2026-08-25
- **Fase anterior:** [Fase 5](FASE-5.md) · **Próxima:** [Fase 7 — Design e competências](FASE-7.md)
- **Plano de execução:** [`docs/superpowers/plans/2026-08-24-grade-fortes-e-excecao-por-linha.md`](../superpowers/plans/2026-08-24-grade-fortes-e-excecao-por-linha.md)
- **Prompt da sessão:** [PROMPT-SESSAO-FASE-6.md](PROMPT-SESSAO-FASE-6.md)

## Em uma frase

A tela Validar vira a planilha de 10 colunas do Fortes, e editar uma célula grava só aquela linha no export — sem promover a conta a regra das irmãs.

## Por que esta fase existe

A Fase 5 fechou o **arquivo**. A auditoria de alinhamento mostrou que a **interface** ainda é um workbench: crédito some quando constante, edição é formulário, “Criar regra” vem ligado, e o XLSX só aparece no download.

O cliente confirmou, contra os prints em [`fluxograma/`](../../fluxograma):

1. A tabela de exibição tem o padrão do Excel Fortes.
2. O que for editado na tabela é o que será exportado (exceção: mesmo fornecedor, contas diferentes).
3. Hospedagem futura: **https://conciliador.projecont.com.br** (não é trabalho desta fase).

## O que saiu

| Artefato | Papel |
|---|---|
| `PATCH` in-place quando `criar_regra=false` | Irmãs intactas; `id` do lançamento estável. `EdicaoLancamento.criar_regra` default `False`; sem reprocessar o lote. |
| Testes em `backend/tests/test_api.py` | `TestExcecaoPorLinha` + `test_edicao_manual_sai_no_arquivo_final` (lote próprio `lote_exportavel`, não o `lote_limpo` compartilhado). |
| `frontend/src/telas/PlanilhaFortes.tsx` | Grade de 10 colunas; crédito sempre visível; linha 1 = modelo Fortes. |
| Aprovar / baixar na própria Validar | `Validacao.tsx`: “Aprovar competência” e “Baixar arquivo Fortes” na aba; conferência continua secundária. |
| `frontend/scripts/capturar-telas.mjs` | Na aba Validar, espera `table.planilha-fortes` em vez de sleep de 600ms. |
| Este handover | Status **Concluída em: 2026-08-25** e comandos que passaram. |

O [ADR 0011](../adr/0011-grade-fortes-na-validacao.md) **já estava escrito**. Não foi reescrito. A implementação segue: a grade não manda `criar_regra: true` (`api.editar` força `criar_regra: false`).

A grade **não** tem checkbox “Criar regra”. Pendências continua sendo o lugar de criar regra.

## Comandos que passaram

Suíte completa do backend (limiares do ADR 0009 intactos; sem fixture sintética de PDF):

```
cd backend && .venv/bin/python -m pytest -q
........................................................................ [ 92%]
......                                                                   [100%]
78 passed in 42.66s
```

Frontend (via `npm run typecheck`, equivalente a `npx tsc -b --noEmit`):

```
cd frontend && npm run typecheck && npx vite build
✓ 24 modules transformed.
dist/index.html                   0.42 kB │ gzip:  0.29 kB
dist/assets/index-qnCCGK2n.css   20.15 kB │ gzip:  5.08 kB
dist/assets/index-T4WMfZGg.js   215.67 kB │ gzip: 67.19 kB
✓ built in 125ms
```

`node scripts/capturar-telas.mjs` (vite e API já estavam no ar): as oito capturas claro/escuro das quatro abas gravaram em [`docs/telas/`](../telas). A espera de `table.planilha-fortes` na Validar funcionou. O script **falhou no extra** `2-pendencias-regra-aberta.png` — timeout de 30s em `getByRole('button', { name: 'Criar regra' })` (lote sem pendência visível / botão ausente). Esse PNG antigo não foi sobrescrito.

## Armadilhas

Herdadas, ainda válidas:

- Não “consertar” o histórico SISPAG para bater 439/439 ([ADR 0005](../adr/0005-politica-historico-sispag.md)).
- Não remover a linha-modelo do XLSX ([ADR 0010](../adr/0010-layout-export-fortes.md)).
- Não portar `reference/`.
- Testes de API compartilham banco por módulo. `TestExportacaoLiberada.lote_limpo` já é exportado por outro teste da classe — edição+export precisa de lote próprio (`lote_exportavel`). Ver [FASE-3](FASE-3.md) e o plano, Task 2.

Novas (e o que a implementação fez):

- **`criar_regra` permanece `false` no save da grade.** Pendências continua sendo o lugar de criar regra. Não ligar no PATCH da célula.
- **Crédito continua coluna.** Não esconder quando constante. O ADR 0011 supersede o trecho da Fase 3 que fazia isso.
- **Não full-reprocess no PATCH sem regra.** Reprocessar apaga e recria lançamentos (ids novos) e é exatamente o que o teste de irmãs pega.
- **Não resolver os 13 ambíguos com heurística.** A grade é a superfície; o critério é do contador.
- **Não fazer deploy** em `conciliador.projecont.com.br` nesta fase.

## Como validar quando esta fase estiver concluída

Comandos do plano — resultados:

```bash
cd backend && .venv/bin/python -m pytest -q
# 78 passed in 42.66s

cd backend && .venv/bin/python -m pytest tests/test_api.py -q -k "ExcecaoPorLinha or edicao_manual"
# coberto pela suíte completa acima (78 passed inclui esses testes)

cd frontend && npx tsc -b --noEmit && npx vite build
# passou via npm run typecheck && npx vite build (ver seção Comandos)
```

Verificação manual (obrigatória — mudou UI), contra o backend em `:8000` e o Vite em `:5173`.
Lote de conferência: competência `092026` (extrato Itaú 21–30/06, 178 linhas, `PRONTO` após resolver pendências).

1. Validar mostra 10 colunas, crédito em toda linha, linha 1 = `LINHA_MODELO` (incluindo `" Valor "`). **Passou.**
2. Editar débito de uma linha AUTO (Click Ip, 22/06) para `1.01.15.01.04.0001`: a irmã do mesmo documento (23/06) permaneceu AUTO com a conta antiga; os `id`s não mudaram. **Passou.**
3. Aprovar e baixar na própria Validar. O XLSX (`fortes-092026.xlsx`) tem 10 colunas, linha-modelo intacta, **uma** linha com o débito editado; a irmã saiu com a conta antiga; valor numérico. **Passou.**
4. Não há checkbox “Criar regra” na grade. **Passou.** Criar regra continua só em Pendências (o lote de conferência já estava sem pendências).

## Fora desta fase (humano)

1. Revisar aba `Ambiguos` de [`docs/base-depara-inicial.xlsx`](../base-depara-inicial.xlsx). São 13 fornecedores; os 6 maiores concentram boa parte das pendências de junho.
2. Importar um arquivo gerado no Fortes ERP (round-trip). Se falhar, ADR sucessor do 0010.
3. Competência nova *com o contador* (única acurácia real, ADR 0009) — distinto da área de lotes no app ([Fase 7](FASE-7.md), [ADR 0012](../adr/0012-administracao-de-competencias.md)).
4. Deploy em https://conciliador.projecont.com.br
