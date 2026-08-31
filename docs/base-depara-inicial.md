# Base De/Para inicial — o que foi minerado e o que precisa de revisão humana

> Gerado por [`tools/minerar_depara.py`](../tools/minerar_depara.py) · Fase 0
> Artefatos: [`base-depara-inicial.csv`](base-depara-inicial.csv) (seed do app) e
> `base-depara-inicial.xlsx` (revisão do contador)

## Resultado

| Métrica | Valor |
|---|---|
| Linhas de histórico lidas | 2.487 (6 meses, duplicata de abril descartada) |
| Fornecedores distintos | **174** |
| Confiança `ALTA` (conta única, 3+ meses) | 80 |
| Confiança `MEDIA` (conta única, 1–2 meses) | 81 |
| `AMBIGUO_CONTA` (bloqueante) | **13** |
| Com CPF/CNPJ identificado | 96 |
| Com mais de um centro de custo observado | 16 |
| Documentos usados por mais de um nome | 4 |
| Linhas não atribuídas a fornecedor | 852 (34%) |

161 dos 174 fornecedores (**93%**) saem com regra pronta. Os 13 restantes exigem decisão do
contador.

## Como a mineração funciona

Junho é o único mês cuja planilha traz a coluna `favorecido / beneficiário`. Ele define o
**conjunto autoritativo** de fornecedores; nenhum fornecedor é inventado a partir dos outros meses.

Janeiro a maio reforçam a confiança por duas vias, ambas conservadoras:

1. **Sufixo do histórico** após o último `" - "`, aceito somente quando casa com um fornecedor que
   junho já provou existir. O sufixo também carrega complementos que não são nome
   (`Santarém`, `Uso de Postes`), e descartá-los é o que evita criar regra falsa.
2. **Conta de débito exclusiva**: se junho usou uma conta para um único fornecedor, qualquer linha
   nos outros meses com aquela conta é do mesmo fornecedor.

As 852 linhas não atribuídas (34%) são o preço dessa postura: preferimos cobertura menor a regra
inventada. Elas não são perda — junho já cobre o conjunto de fornecedores; os outros meses só
elevam a confiança de `MEDIA` para `ALTA`.

### Normalizações que mudam o resultado

- **Sufixo societário colapsado.** Sem isso, `GRUPO MULTI S.A` e `GRUPO MULTI SA` viram dois
  fornecedores concorrentes com a mesma conta.
- **Truncamento em 29 caracteres.** Parte das fontes corta o nome em 30 caracteres, então
  `EQUATORIAL PARA DISTRIBUIDORA` e `EQUATORIAL PARA DISTRIBUIDORA DE ENERGIA S.A.` precisam
  colidir de propósito.

O efeito combinado: os 187 nomes crus de junho são 174 fornecedores reais.

## Os 13 fornecedores ambíguos (aba `Ambiguos`)

| Fornecedor | Contas | Natureza provável |
|---|---|---|
| `BRADESCO ADMINISTRADORA DE CON` | 10 | uma conta por cota de consórcio |
| `LIVETECH DA BAHIA INDUSTRIA E COMERCIO S` | 7 | parcelamento + imobilizado + estoque |
| `AMBAR ENERGIA AMAZONAS S A` | 3 | consumo vs uso de poste |
| `CLARO S A` | 3 | — |
| `EMBRACON ADMINISTRADORA DE CONSORCIO LTDA` | 3 | uma conta por cota |
| `ASSOCIACAO BRASILEIRA DE RECURSOS EM TELECOMUNICAC` | 2 | — |
| `C F BORGES EPP` | 2 | — |
| `EMBRATEL` | 2 | — |
| `ENERGISA MATO GR D DE ENERG SA` | 2 | consumo vs uso de poste |
| `EQUATORIAL PARA DISTRIBUIDORA DE ENERGIA S A` | 2 | consumo vs uso de poste |
| `LEBLON TECNOLOGIA E COMPUTADOR` | 2 | — |
| `PADTEC S A` | 2 | — |
| `TIM S A` | 2 | — |

Não é ruído de dados: consórcios usam uma conta por cota e distribuidoras de energia separam
consumo de uso de infraestrutura. **Escolher a conta mais frequente estaria errado por
construção.** Ou o contador decide, ou a chave ganha um segundo eixo — o código de despesa do
Contas a Pagar é o candidato (ver [`02-analise-arquivos-cliente.md`](02-analise-arquivos-cliente.md) §7.2).

## Centro de custo não é função do fornecedor

16 fornecedores aparecem com mais de um centro de custo mantendo **a mesma** conta de débito:

| Fornecedor | Dominante | Também visto em |
|---|---|---|
| `ORSEGUPS MONITORAMENTO ELETRONICO LTDA` | `0005` | `0001`, `0006`, `0007`, `0009`, `0010` |
| `TERACOM TELEMATICA S A` | `0001` | `0004`, `0005`, `0006`, `0007` |
| `MWM TUPY DO BRASIL LTDA` | `0001` | `0004`, `0011` |
| `PADTEC S A` | `0001` | `0005`, `0007` |
| … outros 12 | | |

Testamos se a coluna `referência da empresa` do relatório Itaú explicaria o centro. **Não
explica**: das 284 linhas de junho que casaram entre o relatório e a planilha, 164 têm essa
referência vazia, e o resto traz número de documento (`NF 188357`, `NFS 95`) ou nome de praça
(`CAMPINAS`, `OSASCO`) sem correspondência estável com o centro.

Conclusão de modelagem: **a regra De/Para fixa a conta de débito; o centro de custo é uma
sugestão** (o dominante) que a tela de validação permite ajustar por lançamento. Tratar o centro
como determinístico produziria erro silencioso em 16 fornecedores.

## CNPJ não é chave suficiente sozinho

4 documentos aparecem sob nomes diferentes. O caso claro é o CNPJ da própria empresa,
`19.402.859/0001-55`:

| Nome | Conta | O que é |
|---|---|---|
| `CLICK IP I MAIS` | `1.01.01.02.01.0004` | Banco do Brasil — transferência entre contas próprias |
| `CLICK IP SERVICOS DE COMUNICAC` | `1.01.05.01.01.0001` | conta intercompany |

Mesmo documento, propósitos contábeis distintos. A chave de casamento precisa ser
**documento + nome**, com o nome desempatando, e não documento sozinho. Registrado em
[`adr/0002-chave-casamento-cnpj.md`](adr/0002-chave-casamento-cnpj.md).

## O teste de falso positivo passa

O grupo `CLICK IP` é o caso que a abordagem por substring do plano original erraria:

| Documento | Nome | Conta |
|---|---|---|
| `19402859000155` | `CLICK IP I MAIS` | `1.01.01.02.01.0004` |
| `13169745000120` | `CLICK IP LOCACAO DE EQUIPAMENTOS LTD` | `1.01.05.01.02.0009` |
| `13184931000139` | `CLICK IP PROVEDORES DE ACESSO LTDA` | `1.01.05.01.02.0007` |
| `19402859000155` | `CLICK IP SERVICOS DE COMUNICAC` | `1.01.05.01.01.0001` |
| `39809271000128` | `CLICK IP TECNOLOGIA LTDA` | `1.01.05.01.02.0008` |

Cinco entidades, cinco contas, prefixo comum. `descricao.includes("CLICK IP")` casaria com todas.

## O que fazer com estes arquivos

1. Enviar o **XLSX** ao contador. Ele precisa: marcar a conta correta na aba `Ambiguos` (ou dar o
   critério de escolha) e conferir por amostragem a aba `Regras`.
2. O **CSV** é o seed versionado do app. As 13 regras `AMBIGUO_CONTA` entram desativadas: o
   lançamento cai em pendência até o humano escolher, em vez de ser classificado errado.
3. Reexecutar `python3 tools/minerar_depara.py` quando chegar um mês novo de histórico.

## Limitações conhecidas

- 78 fornecedores sem CPF/CNPJ (concessionárias como `AGUAS DE MANAUS` não têm documento no
  relatório Itaú). Para eles a chave é só o nome normalizado.
- A confiança mede **consistência histórica**, não correção contábil. Um erro que o contador
  repetiu por 3 meses sai como `ALTA`.
- Janeiro a maio não têm coluna de favorecido; a atribuição por conta exclusiva assume que a
  relação conta→fornecedor de junho valia nos meses anteriores.
