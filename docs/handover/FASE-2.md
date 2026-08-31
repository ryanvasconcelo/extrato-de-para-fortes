# Handover — Fase 2: Design técnico

- **Concluída em:** 2026-08-24
- **Fase anterior:** [Fase 1](FASE-1.md) · **Próxima:** [Fase 3 — Implementação](FASE-3.md)

## Em uma frase

O maior risco técnico do projeto — extrair 59 páginas de PDF com colunas fisicamente sobrepostas —
foi resolvido em spike antes de qualquer código de produção, e o modelo de dados foi desenhado com
a normalização de dígito verificador embutida, sem a qual a validação contra o plano de contas
falharia em 100% dos lançamentos.

## O que foi produzido

| Artefato | Conteúdo |
|---|---|
| [`tools/spike_contas_pagar.py`](../../tools/spike_contas_pagar.py) | Prova de extração por coordenada: 2.060 títulos em 59 páginas |
| [ADR 0006](../adr/0006-modelo-dados-e-normalizacao-contas.md) | 9 entidades, normalização de conta, documento e nome |
| [ADR 0007](../adr/0007-estrategia-extracao-pdf.md) | Baseline + sequência + âncora, e as duas revelações negativas |
| [ADR 0008](../adr/0008-design-system-e-tokens.md) | Tokens `element.tone.emphasis.state`, modo Operate, movimento |

## Decisões desta fase

### 1. Extração por caractere, não por palavra (ADR 0007)

`extract_text()` e `extract_words()` do `pdfplumber` **não servem** para o Contas a Pagar. O
relatório do Fortes AG Financeiro deixa o nome do fornecedor invadir a coluna vizinha, com
sobreposição física de coordenada:

```
DEYWISON BRUNO PEDROZA SILV2A0 7296305300403978238731/03/2026
                            ^^ aqui o nome e a conta ocupam o mesmo x
```

A solução tem três camadas, e nenhuma pode ser removida:

1. **Agrupar por baseline exata** (`PRECISAO_BASELINE = 0.4pt`). Os dois campos sobrepostos estão em
   `top` ligeiramente diferentes; arredondar mais grosso os funde de novo.
2. **Quebrar a baseline em sequências contíguas na ordem do stream**, não na ordem de `x`. Ordenar
   por `x` embaralha campos sobrepostos.
3. **Atribuir sequência à coluna** por `x0` (alinhada à esquerda) ou `x1` (à direita).

Generalizado em `app/parsers/pdf_coordenada.py` e reaproveitado no extrato Itaú.

### 2. Duas revelações negativas que mudaram o escopo

O spike derrubou duas premissas, e é por isso que ele veio antes do código:

- **O Contas a Pagar não tem CPF/CNPJ utilizável.** Só 15 dos 2.060 títulos trazem documento, todos
  de pessoa física. A junção com o pagamento **não pode** ser por documento; é valor + tokens do
  nome + proximidade de data.
- **A derivação de histórico chega a ~58%, não a 79%.** O processo manual tinha contexto que o
  arquivo não tem. O restante recebe o warning `HISTORICO_NAO_DERIVADO` em vez de texto inventado.

### 3. Normalização de conta é obrigatória, não conveniência (ADR 0006)

O plano grafa `1.01.01.02.01.0003-4`; o arquivo Fortes grafa `1.01.01.02.01.0003`. **1.519 das
1.750 contas** têm o sufixo. Sem normalizar, todo lançamento sai com `CONTA_INEXISTENTE`.

`PlanoContas` guarda as duas grafias: `codigo` (canônico, sem DV, é a chave) e `codigo_dv` (como o
cliente escreve, para exibir).

### 4. `Ocorrencia` é tabela, não campo JSON

A tela de pendências filtra por código e os testes da Fase 4 afirmam códigos específicos. JSON num
campo forçaria varredura em memória para responder "quais lançamentos têm `REGRA_AMBIGUA`".

### 5. Design system: a referência dá a estrutura, o logo dá a identidade (ADR 0008)

Produto de modo **Operate**: o contador vem fechar a competência, não ser convencido. Densidade
alta, números tabulares alinhados à direita, estado legível sem cor (ele imprime), e nada animado
na tabela de ~440 linhas.

## Armadilhas para a Fase 3

- **Não escreva um único parser Itaú.** São dois relatórios com o mesmo prefixo de nome:
  `01 A 20-06` é consulta de pagamentos (com grade, valores positivos, tem CNPJ);
  `21 A 30-06` é extrato de conta corrente (sem grade, valores negativos, razão social em coluna
  própria). `detectar_tipo` escolhe.
- **No extrato, a razão social quebra para cima E para baixo** da linha do lançamento. Uma função
  que só anexa o fragmento anterior perde metade dos nomes.
- **O grupo `Despesa:` do Contas a Pagar atravessa páginas.** O cabeçalho aparece uma vez; títulos
  em páginas seguintes pertencem a ele. Extrair despesa "da página atual" cobre só 45%.
- **`Relationship` do SQLModel não conviveu com `from __future__ import annotations`** neste
  projeto. Os modelos usam chave estrangeira sem `Relationship`, e as consultas são explícitas. Se
  reintroduzir, espere `InvalidRequestError` na inicialização.

## Como validar que esta fase está de fato concluída

```bash
cd backend && .venv/bin/python -m pytest tests/test_parsers.py -q
```

1. `tools/spike_contas_pagar.py` extrai 2.060 registros das 59 páginas.
2. `normalizar_conta("1.01.01.02.01.0003-4") == "1.01.01.02.01.0003"`.
3. `carregar_plano_contas` devolve 1.750 contas, 1.516 analíticas.
4. Toda entidade do ADR 0006 existe como tabela em `app/modelos.py`, e os 5 estados de lote e 5 de
   lançamento são `StrEnum`.
