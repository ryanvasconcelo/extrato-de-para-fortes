# ADR 0010 — Layout do export Fortes derivado empiricamente

- **Status:** Aceito
- **Data:** 2026-08-24
- **Fase:** 5

## Contexto

O [`README.md`](../../README.md) afirmava que `specs/RCO010_ImportarLote.pdf` traz a especificação do
layout de importação do FortesERP. **A pasta `specs/` está vazia.** A especificação nunca chegou.

O que existe são seis arquivos que o contador de fato entregou ao Fortes, cobrindo janeiro a junho de
2026 — 2.487 linhas de lançamento. Eles são a única evidência do formato aceito, e a evidência é
forte: foram usados em produção.

Medição dos seis arquivos:

| Arquivo | Linhas | Colunas |
|---|---|---|
| `CLICK SCM 012026 - ITAU CSV.xlsx` | 407 | 10 |
| `CLICK SCM 022026 - ITAU CSV.xlsx` | 414 | 10 |
| `CLICK SCM 032026 - ITAU 032026.xlsx` | 457 | 11 (a 11ª vazia) |
| `CLICK SCM 042026 - ITAU.xlsx` | 406 | 10 |
| `CLICK SCM 052026 - ITAU.xlsx` | 364 | 11 (a 11ª vazia) |
| `CLICK SCM 062026.xlsx` | 439 | 11 (a 11ª é `favorecido / beneficiário`) |

`CLICK SCM 042026 - ITAU (1).xlsx` é byte a byte idêntico a `CLICK SCM 042026 - ITAU.xlsx` e foi
descartado como duplicata.

Duas descobertas mudaram o gerador:

**1. São 10 colunas, não 11.** As fases anteriores registraram "11 colunas". A 11ª é vazia em dois
arquivos (artefato de formatação) e em junho contém `favorecido / beneficiário` — anotação de trabalho
que o contador usou para conferir, não campo de importação. Nenhum outro mês tem.

**2. A linha 1 não é cabeçalho nem lançamento: é um modelo híbrido.**

```
0001 | Data | Débito | Crédito | " Valor " | Histórico | 0001 | 001 | 0001 | 001
```

Rótulo nas colunas variáveis (B a F), constante **já preenchida** nas fixas (A, G, H, I, J). É o
formato de uma planilha-modelo preenchida à mão: quem a criou digitou os valores fixos na primeira
linha e o nome do que varia. Está idêntica nos seis arquivos, inclusive o espaço em volta de
`" Valor "`.

Sem a especificação, não sabemos se o Fortes ignora a linha 1, exige-a, ou a lê como lançamento
malformado e tolera. Sabemos que **com ela os seis arquivos funcionaram**.

## Decisão

### Reproduzir exatamente o que funcionou, incluindo o que não se entende

O arquivo final tem 10 colunas, sem a 11ª, com a linha 1 idêntica ao modelo do cliente:

| Col | Conteúdo | Origem |
|---|---|---|
| A | `0001` | filial, constante |
| B | `dd/mm/aaaa` como texto | data do pagamento |
| C | conta de débito, sem dígito verificador | regra De/Para ou edição manual |
| D | conta de crédito | Base Bancos, pelo cabeçalho do relatório |
| E | valor, **numérico** | pagamento |
| F | histórico | derivação do Contas a Pagar ou edição |
| G | centro de custo | sugestão da regra, ajustável |
| H | `001` | constante, semântica desconhecida |
| I | `0001` | constante, semântica desconhecida |
| J | `001` | constante, semântica desconhecida |

`LINHA_MODELO` sai igual, com o espaço em `" Valor "`. Copiar um espaço que parece erro de digitação
é deliberado: mudar o que funcionou, sem saber por que funciona, é assumir risco sem informação.

O teste `test_linha_modelo_confere_com_o_arquivo_do_cliente` compara a constante do código contra a
linha 1 de `CLICK SCM 062026.xlsx`. Se o cliente mudar o modelo, o teste falha e este ADR precisa de
sucessor — em vez de o arquivo sair errado em silêncio.

### O valor é numérico, a data é texto

Os arquivos do cliente gravam `1500` e `281.77` como número, e `02/01/2026` como texto. Reproduzido.
Valor como texto é o erro clássico de importação em ERP contábil.

### Duas saídas, em ordem obrigatória

Padrão de [`folha-dealer-checklist-validacao.md`](../referencia/folha-dealer-checklist-validacao.md):
**Excel de conferência primeiro, arquivo final só depois de aprovado.**

- `planilha_conferencia` — com cabeçalho, status e códigos de ocorrência por linha, linhas com
  ocorrência destacadas. Disponível em qualquer estado do lote (RF-06.3).
- `arquivo_final` — as 10 colunas. Exige lote `APROVADO`.

### A trava vive no gerador, não na rota

`arquivo_final` levanta `ExportacaoBloqueada` se o lote não estiver `APROVADO`. Validar apenas na rota
deixaria a regra do lado de fora do único ponto por onde o arquivo pode sair; qualquer chamador novo
(um comando de linha, um agendamento) a contornaria sem perceber.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Pedir o RCO010 ao cliente e esperar | Bloquearia a entrega por tempo indeterminado. A pergunta está aberta no handover da Fase 0 e continua valendo; se o documento chegar, o layout se confirma ou gera ADR sucessor. |
| Omitir a linha 1 e começar com dados | Foi a primeira implementação, e estava errada: os seis arquivos aceitos têm a linha. Divergir do que funcionou, sem especificação para justificar, é aposta. |
| Incluir a 11ª coluna com o favorecido | Existe em um arquivo de seis. É anotação de conferência do contador, e ela já aparece na planilha de conferência, que é onde esse dado serve. |
| Gerar CSV em vez de XLSX | Dois nomes de arquivo dizem "ITAU CSV" mas o conteúdo é XLSX nos seis. O ERP recebeu XLSX. |
| Normalizar `" Valor "` para `"Valor"` | Arrumaria a aparência de algo que não olhamos e que talvez o parser do Fortes compare literalmente. |
| Exportar direto, sem aprovação | Viola RF-06.2. Lançamento contábil errado importado no ERP custa estorno manual; o custo de um clique de aprovação é zero. |

## Consequências

**Positivas**
- O arquivo é indistinguível, em estrutura, dos seis que já funcionaram.
- A trava de aprovação é inescapável, porque está no gerador.
- Se o modelo do cliente mudar, um teste falha em vez de o arquivo sair torto.

**Negativas**
- Três colunas (H, I, J) são reproduzidas sem que se saiba o que significam. Se o Fortes exigir valor
  diferente para outra filial ou outro tipo de lote, o gerador está errado e nada aqui detecta.
- A linha 1 é copiada por evidência, não por entendimento. Um dia alguém vai perguntar por que o
  código tem `" Valor "` com espaços; a resposta é este ADR.
- O layout está confirmado para **uma** conta corrente e **uma** filial. Ambas são lookup no modelo
  de dados, mas nenhuma foi exercitada com valor diferente.

## Verificação

```bash
cd backend && .venv/bin/python -m pytest tests/test_api.py -q -k Exportacao
```

1. `test_linha_modelo_confere_com_o_arquivo_do_cliente` — a constante bate com o arquivo real.
2. `test_aprovar_e_exportar_reproduz_o_formato_do_cliente` — 10 colunas, linha 1 modelo, valor
   numérico, datas em ordem.
3. `test_lote_bloqueado_nao_exporta` — 409 antes da aprovação.
4. `test_exportado_nao_aceita_mais_edicao` — depois de exportar, o lote é imutável.
