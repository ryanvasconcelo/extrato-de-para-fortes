# ADR 0003 — Constituir a base De/Para minerando o histórico

- **Status:** Aceito
- **Data:** 2026-08-24
- **Fase:** 0
- **Decisor:** usuário (escolha explícita entre 4 opções apresentadas)

## Contexto

A primeira linha de [`00-plano-engenharia.md`](../00-plano-engenharia.md) diz: "vamos precisar
montar a base do de para antes de iniciar o processo de engenharia". O fluxograma do cliente mostra
uma "Base De x Para" com colunas `Conta Debito · Descricao · Fornecedor · Centro Custo`.

**Nenhum arquivo entregue é essa base.** Ela não existe.

O que existe são 6 meses de saída já classificada — 2.487 lançamentos que um contador produziu à
mão. A relação `fornecedor → conta` está lá, implícita. Junho traz até uma coluna
`favorecido / beneficiário` que não existe nos outros meses, dando o vínculo explícito.

Sem base, não há motor. Sem motor, não há produto. Isso torna a constituição da base o caminho
crítico de todo o projeto.

## Decisão

Minerar a base do histórico com [`tools/minerar_depara.py`](../../tools/minerar_depara.py),
entregando-a com **score de confiança** e **lista explícita de ambíguos** para o contador resolver.

A ferramenta é offline e fora do webapp: produz dados, não é código de produção.

Regras de mineração, todas conservadoras por escolha:

- **Junho é autoritativo.** A coluna de favorecido define o conjunto de fornecedores. Nenhum
  fornecedor é criado a partir de inferência.
- **Janeiro a maio só reforçam.** Duas vias: sufixo do histórico após o último `" - "`, aceito
  apenas quando casa com fornecedor que junho já provou existir; e conta de débito que junho usou
  para um único fornecedor.
- **Confiança mede consistência, não correção.** `ALTA` = conta única em 3+ meses. `MEDIA` = conta
  única em 1–2 meses. `AMBIGUO_CONTA` = mais de uma conta.
- **Ambíguo entra desativado.** A regra existe no seed mas não classifica: o lançamento cai em
  pendência até um humano escolher.

Resultado: **174 fornecedores, 161 com regra pronta (93%), 13 ambíguos**.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Pedir a base ao cliente antes de codar | É o que o plano sugere literalmente, e seria o caminho mais seguro. Rejeitado porque bloqueia o projeto por tempo indeterminado quando 93% da base é recuperável do que já temos — e o cliente teria que montar à mão o que a máquina extrai em 3 segundos. |
| Base vazia, aprendendo pela tela de pendências | Simples e sem risco de regra errada. Rejeitado porque a primeira importação cairia com 100% de pendências (439 linhas), o que na prática é pedir ao contador para refazer o trabalho manual dentro de uma ferramenta nova. Péssima primeira impressão e nenhum ganho. |
| Minerar dentro do app, como feature | Acopla lógica de bootstrap ao produto e cria uma feature que roda uma vez. Script offline é a forma honesta. |

## Consequências

**Positivas**
- O projeto não fica bloqueado esperando o cliente.
- O contador revisa 13 decisões em vez de digitar 174 regras.
- A confiança é explícita, então a Fase 4 pode medir acerto por faixa.
- Reexecutável: chega mês novo, roda de novo.

**Negativas**
- **A confiança mede consistência histórica, não correção contábil.** Um erro que o contador
  repetiu por 3 meses sai como `ALTA`. Isso não é detectável pela ferramenta e precisa ficar
  explícito na entrega ao cliente.
- 852 das 2.487 linhas (34%) não foram atribuídas a fornecedor. É o custo deliberado de não
  inventar regra; junho já cobre o conjunto, os outros meses só elevam confiança.
- A atribuição por conta exclusiva assume que a relação conta→fornecedor de junho valia nos meses
  anteriores. Vale para os dados observados, mas é suposição.
- 78 fornecedores sem CPF/CNPJ dependem de nome como chave.

## Verificação

- `python3 tools/minerar_depara.py` reproduz 174 fornecedores, 80 `ALTA`, 81 `MEDIA`,
  13 `AMBIGUO_CONTA`.
- A duplicata `CLICK SCM 042026 - ITAU.xlsx` (idêntica byte a byte à versão `(1)`) precisa ser
  descartada; se as contagens subirem para 2.893 linhas, a deduplicação quebrou.
- As cinco entidades `CLICK IP` devem sair com cinco contas distintas (ver
  [ADR 0002](0002-chave-casamento-cnpj.md)).
