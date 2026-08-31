# ADR 0011 — A tela Validar é a planilha Fortes; edição de linha não cria regra

- **Status:** Aceito
- **Data:** 2026-08-24
- **Fase:** 6
- **Decisor:** usuário (confirmação explícita após a auditoria de alinhamento, contra os fluxogramas em [`fluxograma/`](../../fluxograma))
- **Implementação:** [`docs/superpowers/plans/2026-08-24-grade-fortes-e-excecao-por-linha.md`](../superpowers/plans/2026-08-24-grade-fortes-e-excecao-por-linha.md) — a decisão está aceita; o código da Fase 6 ainda não tinha sido escrito quando este ADR foi registrado.

## Contexto

O gerador da Fase 5 ([ADR 0010](0010-layout-export-fortes.md)) já produz o XLSX de 10 colunas que o Fortes aceitou nos seis arquivos do cliente. A tela Validar da Fase 3 não é essa planilha: é um workbench com Favorecido, Estado, crédito oculto quando constante, e edição via formulário expandido.

Duas confirmações do cliente, na mesma data, fecharam o desenho do produto:

1. A tabela de exibição segue o padrão visual e estrutural do Excel de importação.
2. O que for editado na tabela é o que será exportado. É assim que o contador trata exceções — o mesmo fornecedor com contas diferentes em linhas diferentes.

O handover da Fase 3 registrou o oposto da (1) para a coluna de crédito: *“a coluna de crédito desaparece da tabela quando é constante”*. O `PATCH /api/lancamentos/{id}` da Fase 3, com o checkbox “Criar regra” ligado por padrão na UI, faz o oposto da (2): salvar uma linha promove a conta a regra e o reprocessamento aplica essa conta a todas as irmãs daquele fornecedor.

## Decisão

**A tela Validar renderiza as 10 colunas do arquivo Fortes**, na ordem de `LINHA_MODELO` / `linha_fortes()` (ADR 0010). A linha 1 da grade é o modelo híbrido. Crédito é coluna em toda linha, mesmo quando todas as linhas compartilham a mesma conta.

**Salvar uma célula não cria regra De/Para.** `criar_regra` permanece `false` no caminho da grade. A linha vira `MANUAL`, o PATCH muta aquele `Lancamento` no lugar, e as irmãs não são reprocessadas. Criar regra continua existindo, e só na aba Pendências (ou num controle explícito, nunca como padrão do save).

Colunas A, H, I e J ficam visíveis e não editáveis (constantes). B (data) permanece fato do pagamento. C, D, E, F e G são editáveis; o export lê o `Lancamento` depois da edição.

Este ADR **não altera** o layout do XLSX. Quem muda o arquivo ainda é o ADR 0010.

Este ADR **supersede** o trecho da Fase 3 que esconde a coluna de crédito.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Manter o workbench e só melhorar o XLSX baixado | O contador conferiria um lugar e exportaria outro. A confirmação do cliente pede a planilha na tela. |
| Checkbox “criar regra” ligado no save da célula | É o comportamento atual e é exatamente o que impede a exceção por linha. |
| Heurística para os 13 fornecedores multi-conta | Hipótese não validada (RF-02.12). A grade é a superfície de exceção; o critério humano nos ambíguos continua pergunta aberta. |
| Mudar o gerador para 11 colunas ou omitir a linha-modelo | Colide com o ADR 0010. A UI copia o arquivo; não o redefine. |

## Consequências

**Positivas**
- A jornada do fluxograma (validar e editar → exportar) acontece no mesmo artefato que o Fortes vai ler.
- Exceção de conta por linha deixa de destruir a classificação das irmãs.
- A planilha de conferência deixa de ser a superfície de revisão; vira download secundário.

**Negativas**
- Densidade: 10 colunas × ~440 linhas. Filtros e tom de linha (PENDENTE/MANUAL) substituem as colunas Favorecido/Estado — quem procurar favorecido como coluna não acha.
- `PATCH` sem reprocessar o lote inteiro exige revalidar só a linha (ocorrências e status do lote). Implementação incorreta ou deixa blocker fantasma ou recria ids e quebra a premissa de “a irmã não muda”.

## Verificação

Depois da Fase 6:

1. A tela Validar tem as 10 colunas, crédito visível, linha 1 igual a `LINHA_MODELO`.
2. Editar o débito de uma linha AUTO cuja irmã compartilha o documento: a irmã permanece AUTO com a conta antiga; os `id`s não mudam.
3. O XLSX exportado contém o débito/histórico/centro/valor gravados na célula.
4. `rg "mostrarCredito"` em `frontend/src` não esconde a coluna por `creditos.size === 1`.
