# ADR 0007 — Extração de PDF por baseline e sequência de caracteres

- **Status:** Aceito
- **Data:** 2026-08-24
- **Fase:** 2 (spike obrigatório)
- **Spike:** [`tools/spike_contas_pagar.py`](../../tools/spike_contas_pagar.py)

## Contexto

O `Contas a Pagar - Pagas` (59 páginas) é a única fonte da coluna Histórico. Sem ele o produto
entrega 100% de `SISPAG FORNECEDORES` e não melhora nada. Era o maior risco técnico do projeto.

`extract_text()` e `extract_tables()` devolvem lixo:

```
DEYWISON BRUNO PEDROZA SILV2A0 7296305300403978238731/03/2026 NFS-E 41 27/03/2026 350,00
                         ^^^^^^^ "SILVA" e "20260..." no mesmo token
```

A primeira hipótese — aumentar `x_tolerance` — falha porque não é problema de espaçamento. Medindo
os caracteres: `SILVA` termina em x=172,26 e `Conta a Pag.` começa em x=166,50. **As duas colunas se
sobrepõem fisicamente em x.** Nenhuma fronteira vertical as separa.

A segunda hipótese — fronteiras por ponto médio do cabeçalho — também falha, e pela mesma razão.
Produziu 0 registros válidos em 3 páginas.

## Investigação

Descendo a `page.chars` e imprimindo em ordem de stream, a estrutura apareceu:

```
449 x0= 36.00 top=130.91 'D'     <- Fornecedor: baseline 130.91
...
488 x0=217.56 top=130.91 '7'
489 x0=307.50 top=131.66 'N'     <- todo o resto: baseline 131.66
...
520 x0=573.00 top=131.66 '3'  <<< x recuou
526 x0=223.50 top=131.66 '3'  <<< x recuou
542 x0=166.50 top=131.66 '2'  <<< x recuou
```

Dois fatos que resolvem o problema:

1. **O Fornecedor tem baseline própria.** Fica 0,75 pt acima dos outros campos da mesma linha
   lógica. Agrupar por `top` exato já separa o campo que colide. As linhas lógicas vizinhas distam
   ~11 pt, então não há risco de fundir linhas.
2. **Cada campo é uma sequência contígua no stream**, ancorada num x estável — mesmo que a ordem
   dos campos no stream seja embaralhada. O Fortes escreve `conta_pag` por último, depois de
   `total_pago`.

## Decisão

Extrair em três passos, nunca fatiando string por posição:

1. **Agrupar caracteres por baseline** (`top` arredondado a 0,4 pt).
2. **Quebrar cada baseline em sequências contíguas**, percorrendo em ordem de stream e cortando
   quando o caractere seguinte não encosta no anterior (folga de 3 pt).
3. **Atribuir cada sequência a uma coluna pelo x**: `x0` para as colunas de texto (alinhadas à
   esquerda), `x1` para as monetárias (alinhadas à direita).

Baselines que não alcançam x=400 são linhas de Fornecedor incompletas: ficam pendentes e são
anexadas à próxima baseline completa.

Âncoras medidas no PDF, reproduzíveis com `--ancoras`:

| Coluna | Âncora | Alinhamento |
|---|---|---|
| `fornecedor` | x0 = 36 | esquerda |
| `conta_pag` | x0 = 166 | esquerda |
| `vencimento` | x0 = 224 | esquerda |
| `tipo_doc` | x0 = 313 | esquerda |
| `titulo` | x0 = 338–392 | esquerda |
| `doc_entrada` | x1 = 485 | direita |
| `valor_titulo` | x1 = 539 | direita |
| `valor_pago` | x1 = 596 | direita |
| `desconto` | x1 = 642 | direita |
| `juros` | x1 = 687 | direita |
| `total_pago` | x1 = 746 | direita |

## Resultado do spike

| Métrica | Valor |
|---|---|
| Páginas | 59 |
| Registros válidos | **2.060** |
| Linhas descartadas (cabeçalho, `Despesa:`, totais) | 359 |
| Com número de título | 1.983 (96%) |
| `total_pago == valor_pago` (integridade) | 2.032 (98%) |
| Tipos de documento distintos | 19 |
| Tempo | ~10 s |

O risco de extração está **fechado**. As linhas que antes colidiam saem íntegras:

```
nome='DEYWISON BRUNO PEDROZA SILVA'  doc='79350437287'
conta_pag='20260300983'  venc='31/03/2026'  tipo='NFS-E'  titulo='41'  pago='350,00'
```

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| `x_tolerance` maior em `extract_words()` | Não é problema de espaçamento; as colunas se sobrepõem em x. |
| Fronteiras por ponto médio do cabeçalho | Testado: 0 registros válidos. Os dados não respeitam as posições do cabeçalho. |
| `extract_tables()` com `explicit_vertical_lines` | Mesmo limite: exige que as colunas não se sobreponham. |
| OCR | Descarta texto vetorial perfeito em troca de erro de reconhecimento. |
| Pedir o relatório em CSV ao cliente | **Continua sendo a melhor opção se o Fortes exportar CSV.** Vale perguntar. Não bloqueia: o PDF já está resolvido. |

## O que este spike revelou de negativo

Duas descobertas que corrigem suposições anteriores e mudam o trabalho da Fase 3.

### 1. O CPF/CNPJ do fornecedor não está disponível

O campo `Fornecedor` do primeiro registro traz `DEYWISON BRUNO PEDROZA SILVA 79350437287`, o que
sugeria uma chave canônica de join. Medindo: apenas **15 de 2.060 registros (0,7%)** têm documento.
São pessoas físicas; para empresas o Fortes não imprime o CNPJ.

O join com os relatórios Itaú **tem** que ser por valor + nome + data. Não há chave canônica.

### 2. A derivação do histórico fica em 58%, não em 100%

Medido contra junho, 439 lançamentos:

| Situação | Linhas | % |
|---|---|---|
| valor + nome + data ≤ 7 dias | 249 | 56% |
| valor + nome + data ≤ 31 dias | 9 | 2% |
| **derivável** | **258** | **58%** |
| valor casa mas data muito distante | 27 | 6% |
| valor casa e nome não | 71 | 16% |
| valor não existe no Contas a Pagar | 83 | 18% |

O processo manual enriqueceu 348/439 (79%). O automático chega a 58%. **O software fica atrás do
humano nesta coluna**, e isso precisa estar dito antes de a Fase 3 começar.

Causas identificadas:

- **Nomes divergentes entre fontes** (16%): o Itaú abrevia (`TERACOM TELEMATICA S A`), o Fortes usa
  a razão social completa.
- **Valor ausente** (18%): tributos (`DARF`, `DAR`, `DAM`, `GRU`) e concessionárias não passam pelo
  Contas a Pagar.
- **Parcela errada escolhida**: contratos parcelados têm valor idêntico em várias parcelas. O
  derivado sai `NF-e 3/10 297197` onde o real é `NF-e 297197 08/10` — número certo, parcela errada.

A Fase 3 deve tratar 58% como **linha de base a superar**, não como resultado final. Os 6% com data
distante e parte dos 16% com nome divergente são recuperáveis com casamento por tokens e por
`conta_pag`. Os 18% sem valor não são: viram `HISTORICO_NAO_DERIVADO`, exatamente o warning
previsto em [ADR 0005](0005-politica-historico-sispag.md).

## Consequências

**Positivas**
- O maior risco do projeto está fechado, com número reproduzível.
- A técnica (baseline + sequência + âncora) serve também ao relatório Itaú `21 A 30`, que não tem
  grade.
- A checagem `total_pago == valor_pago` dá um invariante de integridade barato para detectar
  regressão de parsing.

**Negativas**
- O parser fica acoplado ao layout do Fortes AG Financeiro 5.65.1. Mudança de versão pode mover as
  âncoras. Mitigação: `--ancoras` re-mede, e a checagem de integridade detecta a quebra.
- Sem chave canônica, o casamento é heurístico por construção — daí o warning obrigatório.

## Verificação

```bash
python3 tools/spike_contas_pagar.py
#   esperado: 2060 registros, 96% com titulo, 98% de integridade
python3 tools/spike_contas_pagar.py --ancoras --paginas 2
#   esperado: picos em x0=166, 224, 36, 392, 446 e x1=642, 214, 687, 485
```
