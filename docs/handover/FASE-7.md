# Handover — Fase 7: Design, usabilidade e administração de competências

- **Concluída em:** 2026-08-25
- **Fase anterior:** [Fase 6](FASE-6.md)
- **Plano de execução:** [`docs/superpowers/plans/2026-08-25-design-usabilidade-e-competencias.md`](../superpowers/plans/2026-08-25-design-usabilidade-e-competencias.md)
- **Prompt da sessão:** [PROMPT-SESSAO-FASE-7.md](PROMPT-SESSAO-FASE-7.md)

## Em uma frase

A UI passa a ser lida contra `design-reference/` inteiro, e competências deixam de viver num cartão da Importar: há uma área para listar, abrir e trocar o lote ativo.

## Por que esta fase existe

A Fase 6 fechou o **contrato da planilha** (10 colunas, exceção por linha). O chrome — Importar como
home, `lotes[0]` silencioso, cartão “Competência” no meio do upload — não é a jornada do fluxograma
nem a referência visual do cliente.

O usuário confirmou: deve haver área para administrar competências; a próxima fase é design e
usabilidade; a única referência visual são os arquivos em `design-reference/`.

## O que saiu

| Artefato | Papel |
|---|---|
| `frontend/src/telas/Competencias.tsx` | Listar lotes, abrir mês (MMYYYY), escolher o lote ativo. Mesmo MMYYYY distingue-se por `id`. |
| `frontend/src/App.tsx` | Lote ativo escolhido + `localStorage` `loteIdAtivo`; landing em competências; jornada desabilitada sem lote. |
| `frontend/src/telas/Importacao.tsx` | Só PDFs do lote ativo. Sem cartão de abrir competência. |
| Casca e telas + `estilos/*` | Kit ClickIP (tokens/componentes). Grade Fortes inalterada em estrutura (ADR 0011). |
| `backend/tests/test_api.py` | `TestAdministracaoDeCompetencias`: `GET /api/lotes` já basta; sem DELETE. |
| [ADR 0014](../adr/0014-mapeamento-semantico-do-kit-clickip.md) | Sucessor do 0008 só no mapeamento de cor (kit: teal = ação, navy = estrutura, laranja = cunha). 0008/0012/0013 **não** reescritos. |
| `frontend/scripts/capturar-telas.mjs` | Cinco superfícies × claro/escuro; 10 colunas + ` Valor `; sem checkbox Criar regra na Validar. |
| Este handover | **Concluída em: 2026-08-25** e comandos que passaram. |

Os ADRs **0012 e 0013 não foram reescritos**. A UI aplica os arquivos; onde o kit diverge da tabela de tons do 0008, vale o 0014.

`api.editar` continua `{ criar_regra: false, ... }`. Crédito permanece coluna. A grade **não** anima as ~440 linhas. Morph de download (de `animacao.mov` / `.btn--morph`) só nos botões Fortes. Sem Million.js (`SKILL.md` local inexistente; GitHub não aberto).

## Comandos que passaram

Suíte completa do backend (limiares do ADR 0009 intactos; sem fixture sintética de PDF):

```
cd backend && .venv/bin/python -m pytest -q
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 43.37s
```

(78 anteriores + `TestAdministracaoDeCompetencias`.)

Frontend (`npm run typecheck` = `tsc -b --noEmit` local):

```
cd frontend && npm run typecheck && npx vite build
✓ 26 modules transformed.
dist/index.html                   0.81 kB │ gzip:  0.45 kB
dist/assets/index-CL7ZlsO0.css   39.82 kB │ gzip:  8.19 kB
dist/assets/index-B8ZUOM3u.js   221.79 kB │ gzip: 68.78 kB
✓ built in 114ms
```

Playwright (`node scripts/capturar-telas.mjs`; Vite em `http://localhost:5173` e API em `:8000` já no ar):

```
../docs/telas/0-competencias-claro.png
../docs/telas/1-importar-claro.png
../docs/telas/2-pendencias-claro.png
../docs/telas/3-validar-claro.png
../docs/telas/4-exportar-claro.png
../docs/telas/0-competencias-escuro.png
../docs/telas/1-importar-escuro.png
../docs/telas/2-pendencias-escuro.png
../docs/telas/3-validar-escuro.png
../docs/telas/4-exportar-escuro.png
ok: Validar tem 10 colunas, crédito visível, sem Criar regra
../docs/telas/2-pendencias-regra-aberta.png
```

O extra `2-pendencias-regra-aberta.png` **passou** neste lote (lote 7, agosto 2026, 9 pendências). Não foi necessário PDF sintético.

A captura espera `[data-lista-pronta="true"]` antes de clicar “Usar este lote” (evita o flash de lista vazia no fetch). Escolhe o lote com mais lançamentos, não `lotes[0]`.

## Verificação Playwright (checklist do handover)

1. **Competências** lista vários lotes (incluindo três `082026` distintos por `id`) e troca o ativo: cabeçalho e trilho passam a “Agosto 2026 · lote 7”; Validar carrega 439 linhas desse lote.
2. **Importar** é dropzone + insumos do lote ativo. Abrir mês ficou em Competências.
3. **Validar:** 10 `th`, rótulo ` Valor ` com espaços, coluna Crédito visível, zero checkbox “Criar regra”.
4. Capturas claro/escuro das cinco superfícies em [`docs/telas/`](../telas).
5. Inventário abaixo: os 23 arquivos foram abertos um a um (exceto `.DS_Store`).

## Inventário `design-reference/` (lidos)

### `design-reference/design clickip/`

1. `animacao.mov` — lido (morph Download → arquivo; blur/scale; ~16s)
2. `darkmode referencia.webp` — lido
3. `font hierarquia.webp` — lido
4. `icons referencia.png` — lido
5. `icons referencia.webp` — lido
6. `logo.svg` — lido
7. `overlay referencia.webp` — lido
8. `referencia color.webp` — lido
9. `referencia de UI 2.webp` — lido
10. `referencia de UI 3.webp` — lido
11. `referencia de UI.webp` — lido
12. `referencia hierarquia.webp` — lido
13. `referencia shadows e destaques.webp` — lido
14. `shadow ui referencia.webp` — lido
15. `ui de referencia.webp` — lido
16. `ui referencia 2.webp` — lido
17. `ui-referencia.webp` — lido
18. `ux referencia.webp` — lido

### `design-reference/design system/`

19. `clickip-components.css` — lido
20. `clickip-design-system.html` — lido
21. `clickip-tailwind.css` — lido
22. `clickip-tokens.css` — lido
23. `clickip-tokens.json` — lido

Ignorado: `design-reference/design clickip/.DS_Store`.

## Armadilhas

Herdadas, ainda válidas:

- Não reverter ADR 0002, 0005, 0010, 0011.
- Não esconder crédito; não ligar `criar_regra` na grade.
- Não portar `reference/`.
- Não baixar limiares da suíte (ADR 0009) nem criar fixture sintética de PDF.
- Não fazer deploy em `conciliador.projecont.com.br`.
- Tabela de ~440 linhas: não animar linha (ADR 0008).

Novas (e o que a implementação fez):

- **Leu cada arquivo da lista.** Não substituiu por ADR 0008 nem por paleta no chat.
- **Não buscou visual fora** de `design-reference/`.
- **Million.js:** sem `SKILL.md` local; pacote não instalado; GitHub não aberto.
- **Não apagou lote EXPORTADO** (há um `092026` EXPORTADO na lista e permanece).
- Dois lotes com o mesmo MMYYYY: a lista mostra `id` + status; o ativo é o escolhido, não o mais novo.
- Recarregar não cai em `lotes[0]`: chave `loteIdAtivo`. Se o id sumiu, a lista é a superfície — não escolhe o primeiro em silêncio.

## Fora desta fase (humano)

1. Revisar aba `Ambiguos` de [`docs/base-depara-inicial.xlsx`](../base-depara-inicial.xlsx).
2. Importar um arquivo gerado no Fortes ERP. Se falhar, ADR sucessor do 0010.
3. Competência nova *com o contador* (acurácia real, ADR 0009) — distinto de administrar lotes no app.
4. Deploy em https://conciliador.projecont.com.br
5. CRUD de regras (listar/desativar) e apagar competência — não pedidos nesta fase.
