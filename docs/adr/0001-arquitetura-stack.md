# ADR 0001 — Arquitetura: React/Vite + FastAPI + SQLite

- **Status:** Aceito
- **Data:** 2026-08-24
- **Fase:** 0
- **Decisor:** usuário (escolha explícita entre 4 opções apresentadas)

## Contexto

[`00-plano-engenharia.md`](../00-plano-engenharia.md) §2 sugere "aplicação web nuvem
(possivelmente Python, Flask e SQLite)". O monorepo Rayo, de onde vem o código de referência em
[`reference/`](../../reference), é React 19 + Vite inteiramente client-side, sem backend, com
persistência em `localStorage`.

Três forças em tensão:

1. **Os PDFs exigem Python.** O relatório `21 A 30-06` não tem linhas de grade e o Contas a Pagar
   tem colunas colididas caractere a caractere (ver
   [`02-analise-arquivos-cliente.md`](../02-analise-arquivos-cliente.md) §2.2 e §7.1).
   `pdfplumber` resolve extração por coordenada; o `pdfjs-dist` que o Rayo usa no browser não
   oferece equivalente prático.
2. **A base De/Para é o ativo do produto.** 174 fornecedores curados por um contador. Perder isso
   ao limpar o navegador é inaceitável, o que descarta `localStorage`/IndexedDB como persistência
   primária.
3. **A UI precisa ser boa.** [`design-reference/`](../../design-reference) aponta um design system
   com tokens semânticos (`element.tone.emphasis.state`), dark mode, sombras e um `animacao.mov`.
   As skills escolhidas para o projeto (`impeccable`, `ui-ux-pro-max`, `emil-design-eng`) são todas
   de front-end. Jinja server-rendered não atende esse nível.

## Decisão

- **Frontend:** React + Vite + TypeScript, Tailwind com tokens semânticos, shadcn/ui como base.
- **Backend:** FastAPI (Python), com `pdfplumber` e `openpyxl` para parsing.
- **Persistência:** SQLite via SQLModel.

Fronteira: o backend é dono de todo parsing, do motor de classificação e da validação. O frontend
não parseia arquivo nem decide conta contábil.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Flask + Jinja + SQLite (o plano original) | Menos peças, e o Python está certo. Mas não entrega a UI que as referências de design pedem, e a tela de pendências é interativa o suficiente (edição em linha, reprocessamento, filtros sobre centenas de linhas) para sofrer com round-trip de formulário. |
| React client-side + IndexedDB (padrão Rayo) | Zero backend e dado nunca sai da máquina, o que é atraente para LGPD. Rejeitado por dois motivos: extração dos PDFs difíceis fica inviável no browser, e a base De/Para curada fica presa a um navegador. |
| Next.js full-stack + Prisma | Um projeto só, e boa DX. Rejeitado porque empurraria o parsing para Node, perdendo `pdfplumber` — que é justamente o que torna o maior risco técnico do projeto tratável. |

## Consequências

**Positivas**
- Parsing na linguagem com as melhores ferramentas para o problema.
- Base De/Para persistida, versionável e auditável fora do navegador.
- Liberdade total de UI para as skills de design.

**Negativas**
- Duas stacks para manter, dois processos em desenvolvimento.
- Deploy mais complexo que um único artefato.
- Contrato de API para manter sincronizado entre backend e frontend.

**Mitigações**
- Tipos derivados do schema OpenAPI do FastAPI, para o contrato não divergir em silêncio.
- SQLite mantém o deploy sem serviço de banco separado.

## Notas

A escolha de LGPD não fica pior que o padrão Rayo por acidente: SQLite é arquivo local, então a
aplicação pode rodar on-premise sem nenhum dado do cliente sair da máquina. A diferença em relação
ao Rayo é que o dado sobrevive ao fechamento do navegador.
