# Handover — Fase 4: Testes e validação

- **Concluída em:** 2026-08-24
- **Fase anterior:** [Fase 3](FASE-3.md) · **Próxima:** [Fase 5 — Export e entrega](FASE-5.md)

## Em uma frase

67 testes em quatro camadas contra os arquivos reais do cliente (a Fase 5 acrescentou 4, totalizando
71), com limiares que são linha de base medida e não meta — e a constatação de que nenhum deles mede
acurácia de verdade, porque a base De/Para saiu do mesmo gabarito.

## O que foi produzido

| Artefato | Conteúdo |
|---|---|
| [`backend/tests/test_api.py`](../../backend/tests/test_api.py) | 18 testes na fronteira HTTP + SQLite |
| [`backend/tests/test_regressao_meses.py`](../../backend/tests/test_regressao_meses.py) | 7 testes de regressão sobre Jan–Mai |
| [ADR 0009](../adr/0009-estrategia-de-testes-e-golden-files.md) | Estratégia, limiares, correções de medição |

Somados aos 22 de `test_parsers.py` e 20 de `test_ponta_a_ponta.py`, produzidos na Fase 3: **67** ao
fim desta fase.

## Resultados medidos

| Métrica | Resultado |
|---|---|
| Conta de débito, entre as classificadas | 337 acertos, 1 erro — **99,7%** |
| Classificação automática | 338/439 — **77,0%** |
| Centro de custo | 309/338 — **91,4%** |
| Histórico derivado | 263/439 — **59,9%** |
| SISPAG enriquecidas | **53/91** |
| Contas exercitadas só por Jan–Mai | **87** |

## O que o próximo agente precisa entender antes de ler esses números

**99,7% não é a acurácia do produto.** É a taxa entre as 338 linhas que o sistema decidiu
classificar, com uma base minerada destes mesmos arquivos. As 101 linhas que ficaram em pendência são
exatamente onde não há regra — e é lá que mora o risco. O número correto para conversar com o cliente
é: *o sistema resolve 77% das linhas sozinho e reproduz o julgamento do contador quando tem regra*.

**Nenhuma camada mede acurácia real.** Isso só sai de uma competência nova, com os PDFs de julho, com
o contador usando o app. Está na seção de consequências negativas do ADR 0009 de propósito.

## Decisões desta fase

### 1. Limiar é linha de base, não meta

Subir exige medir de novo; baixar exige ADR. A folga entre medido (99,7%) e limiar (90%) é
deliberada: o teste pega regressão estrutural, não oscilação de refinamento.

### 2. Sem mock de PDF

Os bugs deste domínio moram na fronteira com o PDF real — o spike da Fase 2 provou. Fixture sintética
passaria com o parser quebrado. Custo aceito: 40 segundos de suíte e dependência de
`arquivos-clickip/` estar presente.

### 3. A regressão de Jan–Mai é honesta sobre ser circular

O teste de reprodução dá 100% e o docstring diz que isso não é evidência de acurácia. O valor real
está no outro teste do mesmo arquivo: **87 contas** que junho não exercita passam pela normalização
de dígito verificador. Se ela quebrar numa faixa específica, junho passa e este falha.

### 4. Correções de medição vão no ADR, não em edição retroativa

ADR não se edita (convenção do plano). O plano de contas tem **1.750** contas, não 1.864 — aquele
número contava linha de planilha. Registrado na seção de correções do ADR 0009 e corrigido nos
docstrings do código.

## Bugs que os testes desta fase encontraram

| Sintoma | Causa | Correção |
|---|---|---|
| Pendência mostrava dois motivos para uma decisão | `REGRA_AMBIGUA` e `CONTA_DEBITO_AUSENTE` disparavam juntos | Processador suprime o efeito quando a causa está presente |
| Coluna de estado saía da área visível | Tabela sem largura declarada; histórico empurrava o resto | `table-fixed` com `colgroup`; coluna de crédito só aparece se houver mais de uma |
| Reabrir o app perdia a memória do que foi importado | Lista de arquivos vivia no estado do React | `GET /api/lotes` devolve os arquivos do lote |
| Não havia como recalcular sem reimportar PDF | Faltava a rota | `POST /api/lotes/{id}/reprocessar`, idempotente |

## Armadilhas para a Fase 5

- **Os testes de API compartilham banco por módulo.** `POST /api/regras` reprocessa todos os lotes
  abertos, então um teste que cria regra afeta os lotes de outros testes. Teste novo que precise de
  estado limpo cria lote próprio, como faz `TestExportacaoLiberada`.
- **`test_gabarito_tem_as_91_linhas_sispag_esperadas` é sentinela do arquivo do cliente**, não do
  código. Se falhar, o XLSX mudou e o ADR 0005 precisa ser revisitado antes de confiar em qualquer
  outro teste de histórico.
- **O arquivo final não tem cabeçalho.** Um teste que leia `ws[1]` esperando nome de coluna está
  lendo o primeiro lançamento. É assim nos seis arquivos do cliente.
- **São 10 colunas no arquivo, não 11.** A décima primeira (`favorecido/beneficiário`) existe só em
  `CLICK SCM 062026.xlsx` e é anotação de trabalho do contador, não parte do layout de importação.

## Como validar que esta fase está de fato concluída

```bash
cd backend && .venv/bin/python -m pytest -q     # suíte inteira verde
cd backend && .venv/bin/python -m pytest -q -s  # imprime as taxas medidas
```

1. Os cinco números da tabela de resultados reaparecem na saída com `-s`.
2. `pytest -k "FalsoPositivo"` passa: as cinco entidades `CLICK IP *` produzem cinco contas.
3. `pytest -k "Trava"` passa: aprovar bloqueado e exportar sem aprovação dão 409.
4. Renomear `arquivos-clickip/` faz ~60 testes falharem por arquivo ausente, não passarem em
   silêncio. Se passarem, alguém introduziu fallback sintético.
