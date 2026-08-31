# ADR 0009 — Estratégia de testes: golden file de junho e limiares medidos

- **Status:** Aceito
- **Data:** 2026-08-24
- **Fase:** 4

## Contexto

O produto não tem uma resposta "certa" verificável por construção. A saída é um lançamento contábil
cuja correção depende de julgamento humano — o mesmo julgamento que produziu os seis XLSX que o
cliente entregou. Testar isso tem três problemas específicos:

**1. O gabarito não é totalmente confiável.** `CLICK SCM 062026.xlsx` foi feito à mão, a partir do
extrato bruto, sem saber o favorecido. 91 das 439 linhas têm `SISPAG FORNECEDORES` como histórico.
Nosso insumo identifica o favorecido, então **divergir ali é o objetivo** (ADR 0005). Um gabarito
que o sistema deve bater em algumas colunas e superar em outra não se compara com `assertEqual`.

**2. A base De/Para saiu do próprio gabarito.** Ela foi minerada dos seis XLSX (ADR 0003). Medir
"acurácia" da classificação contra os mesmos arquivos é circular por construção, e um teste que se
apresenta como medição de acurácia sendo circular é pior que nenhum teste: dá confiança falsa.

**3. Não há entrada para cinco dos seis meses.** Só junho tem os relatórios Itaú. Janeiro a maio
existem apenas como saída, então o pipeline não pode ser executado para eles.

Sem decisão registrada, o próximo agente faz uma de duas coisas erradas: exige 439/439 em tudo (e
"conserta" o enriquecimento de histórico, revertendo o ADR 0005 sem ADR), ou lê 99,7% de precisão
como prova de que o produto está correto.

## Decisão

### Quatro camadas, com propósitos distintos e declarados

| Arquivo | Testes | O que afirma |
|---|---|---|
| `test_parsers.py` | 22 | Normalização e extração: dado de entrada vira estrutura correta |
| `test_ponta_a_ponta.py` | 23 | Motor sobre junho contra o gabarito, e o arquivo final gerado |
| `test_api.py` | 19 | Fronteira HTTP + SQLite: o que só existe com persistência |
| `test_regressao_meses.py` | 7 | Jan–Mai: cobertura de plano de contas e round-trip do seed |

### Os limiares são linha de base medida, não meta

Todo número abaixo foi medido, não escolhido. A regra: **subir um limiar exige medir de novo; baixar
exige justificar em ADR novo.**

| Métrica | Medido | Limiar no teste |
|---|---|---|
| Conta de débito, entre as classificadas | 337 acertos / 1 erro = **99,7%** | ≥ 90% |
| Classificação automática | 338/439 = **77,0%** | ≥ 75% |
| Centro de custo | 309/338 = **91,4%** | ≥ 85% |
| Histórico derivado | 263/439 = **59,9%** | ≥ 58% |
| SISPAG enriquecidas | **53/91** | ≥ 40 |

A folga entre medido e limiar é deliberada: o teste existe para pegar regressão estrutural, não para
travar em cima do número do dia. Limiar colado no valor medido quebra com qualquer refinamento
legítimo de normalização.

### O que cada número significa, e o que não significa

**99,7% de precisão de débito não é 99,7% de acurácia do produto.** É a taxa entre as linhas que o
sistema decidiu classificar (338 de 439), e a base que decidiu veio destes arquivos. Leitura
correta: *o caminho De/Para → conta reproduz o julgamento do contador quando tem regra*. As 101
linhas em pendência são justamente onde ele **não** tem regra, e é lá que está o risco real.

**59,9% de histórico derivado é o número honesto.** O processo manual chegou a 79% porque o contador
tinha contexto que o arquivo não tem. As 176 linhas restantes recebem `HISTORICO_NAO_DERIVADO` e
texto legível, nunca histórico inventado.

**A reprodução de 100% em Jan–Mai é circular e o teste diz isso no docstring.** Serve para detectar
quebra em `normalizar_nome_fornecedor` ou no loader do seed, não para medir qualidade.

### Testes que existem por causa de uma decisão anterior

Estes não medem taxa; afirmam comportamento que já foi decidido em ADR. São os que impedem que uma
refatoração reverta uma decisão em silêncio:

- **Falso positivo de substring** (ADR 0002). As cinco entidades `CLICK IP *` têm cinco contas
  distintas, e o classificador não as confunde. É o teste que a abordagem original do plano
  falharia.
- **Regra → status** (pedido explicitamente no plano original). Testado duas vezes: no motor, e via
  HTTP com persistência, porque as duas coisas podem quebrar separadamente.
- **Ambíguo bloqueia em vez de escolher** (ADR 0003). Se as 13 regras `AMBIGUO_CONTA` entrarem
  ativas, este teste falha.
- **`CONTA_INEXISTENTE == 0`** (ADR 0006). Se a normalização de dígito verificador quebrar, são 439
  falhas de uma vez.
- **Trava de exportação** (RF-06.2). Aprovar lote bloqueado → 409; exportar sem aprovação → 409.

### Correções de medição

Números publicados em fases anteriores que a Fase 4 mediu diferente. Registrados aqui porque ADR não
se edita:

| Onde | Dizia | Medido | Por quê |
|---|---|---|---|
| ADR 0006, `02-analise-arquivos-cliente.md` | 1.864 contas no plano | **1.750** | 1.864 era contagem de linha da planilha, incluindo cabeçalho de relatório e linhas em branco |
| ADR 0006 | 348 contas sintéticas | **234** | Consequência da mesma contagem |
| Plano de engenharia (mermaid) | 1.755 contas | **1.750** | Aproximação anterior à normalização de duplicatas |

O total de analíticas (**1.516**) e o de contas com dígito verificador (**1.519**) se confirmaram.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Igualdade exata contra as 439 linhas | Colide com o ADR 0005: o histórico **deve** divergir em 91 linhas. Um teste assim seria consertado desligando o enriquecimento. |
| Só teste unitário, sem golden file | Os bugs deste domínio moram na fronteira com o PDF real. Unitário com fixture sintética passaria com o parser quebrado — foi exatamente o que aconteceu no spike da Fase 2. |
| Mock dos PDFs para acelerar a suíte | 40 segundos para 71 testes sobre arquivo real é barato. Mock de PDF com colunas sobrepostas seria mais difícil de escrever que o parser, e testaria o mock. |
| Separar a base De/Para em treino/teste | Cientificamente correto, inútil na prática: 174 fornecedores, 13 ambíguos. Segmentar deixaria as duas metades pequenas demais para significar algo. |
| Snapshot do XLSX exportado byte a byte | Quebra a cada mudança de estilo do openpyxl. Os testes afirmam estrutura: 10 colunas, constantes nas posições certas, valor numérico, datas ordenadas. |

## Consequências

**Positivas**
- A suíte roda contra os arquivos que o cliente vai usar de verdade, em 40 segundos.
- Cada limiar tem procedência: quem mudar precisa medir.
- As decisões dos ADRs anteriores têm teste que as protege, então reverter uma exige falhar um teste
  com nome explícito.

**Negativas**
- A suíte depende de `arquivos-clickip/` estar presente. Sem os arquivos, a grande maioria dos testes
  não tem o que rodar. Não há fallback sintético de propósito: seria fingir cobertura.
- Nenhuma camada mede acurácia de verdade. Só o contador, usando o app em uma competência nova, dirá
  se as sugestões servem. O produto precisa dessa rodada antes de ser considerado validado.
- Os testes de API compartilham banco por módulo, então criar regra em um teste afeta outro. Está
  documentado no handover da Fase 3, mas é uma armadilha ativa.

## Verificação

```bash
cd backend && .venv/bin/python -m pytest -q          # 71 passando, ~40s
cd backend && .venv/bin/python -m pytest -q -s       # imprime as taxas medidas
```

Se um limiar falhar, a pergunta não é "como faço passar" e sim "o que mudou na medição".
