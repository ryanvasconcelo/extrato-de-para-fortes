# ADR 0012 — Há uma área para administrar competências

- **Status:** Aceito
- **Data:** 2026-08-25
- **Fase:** 7
- **Decisor:** usuário (confirmação explícita após usar a tela Importar da Fase 6)
- **Implementação:** [`docs/superpowers/plans/2026-08-25-design-usabilidade-e-competencias.md`](../superpowers/plans/2026-08-25-design-usabilidade-e-competencias.md)

## Contexto

O modelo já tem `LoteImportacao` por competência (`MMYYYY`) e `GET /api/lotes` devolve a lista. A
casca do app, porém, trata competência como detalhe da Importar: o campo “Mês de referência” e
**Abrir lote** ficam no mesmo cartão em que se sobe PDF. `App.tsx` retoma só `lotes[0]` (o id mais
novo). Na verificação da Fase 6 isso fez a UI abrir um rascunho vazio enquanto um lote com 439
linhas existia atrás.

O usuário disse que a forma do webapp não era a que imaginou, e que **deve haver uma área para
administrar competências**. Importar PDFs e fechar o mês são passos da jornada; escolher *qual*
mês está aberto é outra superfície.

## Decisão

**Competências têm área própria.** Nela o contador lista os lotes, vê status e quantidade de
lançamentos, abre um mês novo e troca o lote ativo. Importar fica só nos PDFs do lote escolhido —
não é o lugar onde se “cria o mês”.

O lote ativo é estado da sessão (e, se a implementação persistir a escolha, sobrevive a recarregar
a aba). Não é “sempre o último `id`”.

Este ADR **não altera** o contrato da grade Fortes ([ADR 0011](0011-grade-fortes-na-validacao.md))
nem o layout do XLSX ([ADR 0010](0010-layout-export-fortes.md)). Lote `APROVADO` / `EXPORTADO`
continua imutável.

Não é obrigatório apagar competência nesta fase. Administrar = listar, abrir, trocar.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Manter o cartão Competência na Importar como única entrada | É o que existe e foi lido como a home do produto, não como pasta do mês. |
| Só um lote no banco, sempre | O contador fecha um mês atrás do outro; RF-01.5 já admite vários arquivos *por* competência, e a API já lista vários lotes. |
| Apagar lote na mesma tela, sem pedido | Destrutivo; lote exportado é histórico. Fora desta decisão. |

## Consequências

**Positivas**
- A jornada do fluxograma (extrato → De/Para → histórico → validar → exportar) acontece *dentro* de
  um mês escolhido, não misturada com “criar competência”.
- Recarregar o app não troca o trabalho em curso pelo rascunho mais novo.

**Negativas**
- Uma superfície a mais. Se a lista for pobre, o contador volta a não achar o mês.
- Dois lotes com a mesma string `082026` já existem no banco de dev; a lista precisa distinguir por
  `id` e status, não só pelo `MMYYYY`.

## Verificação

Depois da Fase 7:

1. Dá para ver mais de um lote e escolher qual está ativo, sem depender de `lotes[0]`.
2. Importar não é a única forma de “abrir competência”.
3. Trocar o lote ativo muda o cabeçalho e as abas Pendências / Validar / Exportar para esse lote.
