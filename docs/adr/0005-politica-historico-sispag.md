# ADR 0005 — Enriquecer o histórico que o processo manual deixava como `SISPAG FORNECEDORES`

- **Status:** Aceito
- **Data:** 2026-08-24
- **Fase:** 1

## Contexto

A coluna Histórico do arquivo Fortes alterna entre duas formas:

- rica: `Débito Banc. ref. NFS-e 889048 - Orsegups Monitoramento`
- genérica: `SISPAG FORNECEDORES`

A interpretação intuitiva é que `SISPAG FORNECEDORES` é o fallback de "não encontrei o título".
As medições rejeitam essa leitura.

### Medição 1 — a taxa é instável

| Mês | Linhas | `SISPAG` | % |
|---|---|---|---|
| 01/2026 | 407 | 44 | 10% |
| 02/2026 | 414 | 15 | 3% |
| 03/2026 | 457 | 11 | **2%** |
| 04/2026 | 406 | 132 | **32%** |
| 05/2026 | 364 | 116 | 31% |
| 06/2026 | 439 | 91 | 20% |

Ausência de dado produziria taxa estável. Variar de 2% a 32% entre meses consecutivos indica
esforço humano variável, não limitação técnica.

### Medição 2 — o dado estava disponível

Das 91 linhas `SISPAG` de junho, **85% têm o valor presente no Contas a Pagar** — contra 81% das
linhas que foram enriquecidas. A informação necessária existia e não foi usada.

### Explicação

`SISPAG` é o sistema de pagamento em lote do Itaú. No **extrato de conta corrente**, o banco
escreve apenas `SISPAG FORNECEDORES` na descrição e o favorecido fica invisível. Trabalhando a
partir do extrato, o contador não tinha como saber quem recebeu, então copiava a descrição bruta.

O **relatório de consulta de pagamentos**, que agora temos, traz `favorecido/beneficiário` e
`CPF/CNPJ` nessas mesmas linhas. E o extrato traz `Razão Social` em coluna separada da descrição.
Em ambos os layouts o favorecido é recuperável.

## Decisão

**Enriquecer.** Quando houver título correspondente no Contas a Pagar, montar o histórico completo,
inclusive nas linhas que o processo manual deixaria como `SISPAG FORNECEDORES`.

Quando não houver título correspondente, usar a descrição bancária original e marcar o lançamento
com o warning `HISTORICO_NAO_DERIVADO` — visível na tela de validação e editável, nunca silencioso.

### Consequência imediata para os testes

`CLICK SCM 062026.xlsx` **não é gabarito para a coluna Histórico**. Continua sendo gabarito
confiável para Débito, Crédito, Valor, Data e Centro de custo.

O teste ponta a ponta da Fase 4 compara:

- **348 linhas** de histórico derivado → devem bater
- **91 linhas** `SISPAG` → divergência **esperada**, contabilizada como melhoria

Um teste que exigisse 439/439 na coluna Histórico estaria pedindo ao software para reproduzir a
limitação do processo manual. Ele deve falhar se o enriquecimento **não** acontecer.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Preservar `SISPAG FORNECEDORES` para bater 100% com o histórico | Daria um teste ponta a ponta verde e limpo, e é tentador por isso. Mas entrega ao cliente menos do que os dados permitem, e a métrica de sucesso passaria a ser "reproduzir o trabalho manual" em vez de "melhorá-lo". O teste existe para provar o produto, não o contrário. |
| Enriquecer somente quando a confiança do casamento for alta | Meio-termo razoável, mas exige um limiar arbitrário e produz comportamento inconsistente entre linhas parecidas. O warning já dá ao humano a informação de que precisa, sem esconder decisão em heurística. |
| Deixar configurável por lote | Configuração para uma decisão que tem resposta certa. Adiciona superfície sem resolver nada. |

## Consequências

**Positivas**
- O produto entrega valor que o processo manual não entregava — é o argumento de adoção.
- As linhas de histórico incompleto ficam explicitamente marcadas, em vez de invisíveis.
- Rastreabilidade: cada histórico derivado aponta para o título que o originou.

**Negativas**
- O teste ponta a ponta fica mais complexo: precisa de duas expectativas em vez de uma.
- Divergir do histórico exige explicar ao cliente por que o arquivo novo não é idêntico ao antigo.
  Mitigação: a planilha de conferência (RF-06.3) deve destacar as linhas enriquecidas.
- Se o casamento por valor + fornecedor errar, o histórico fica **errado** em vez de genérico.
  Errado é pior que genérico. Mitigação: o casamento exige valor exato e fornecedor compatível;
  título já usado por outro pagamento gera `TITULO_REUTILIZADO`.

## Verificação

- Nas 91 linhas `SISPAG` de junho, o sistema deve derivar histórico para pelo menos as ~78 (85%)
  cujo valor consta no Contas a Pagar.
- Nenhuma linha deve sair com `SISPAG FORNECEDORES` **sem** o warning `HISTORICO_NAO_DERIVADO`.
