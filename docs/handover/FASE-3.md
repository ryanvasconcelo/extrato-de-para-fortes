# Handover — Fase 3: Implementação

- **Concluída em:** 2026-08-24
- **Fase anterior:** [Fase 2](FASE-2.md) · **Próxima:** [Fase 4 — Testes](FASE-4.md)

## Em uma frase

O pipeline completo funciona sobre os PDFs reais de junho: 439 lançamentos, 338 classificados
automaticamente (77%), 263 com histórico derivado (60%), 19 fornecedores em pendência — e a interface
transforma cada pendência resolvida em regra que vale para os meses seguintes.

## O que foi produzido

| Camada | Módulos |
|---|---|
| Parsers | `plano_contas.py`, `pdf_coordenada.py`, `contas_pagar.py`, `itau.py` |
| Motor | `classificador.py`, `historico.py`, `validador.py`, `processador.py` |
| Persistência | `modelos.py`, `banco.py`, `seed.py` |
| API | `api.py` — 13 rotas em `/api` |
| Export | `export_fortes.py` |
| Interface | `frontend/src` — 4 telas, tokens semânticos, tema claro/escuro |

Capturas em [`docs/telas/`](../telas), geradas por
[`frontend/scripts/capturar-telas.mjs`](../../frontend/scripts/capturar-telas.mjs) contra o backend
com junho importado.

## Números medidos sobre junho, via HTTP

| Medida | Valor |
|---|---|
| Pagamentos extraídos | 439 (261 do relatório de pagamentos + 178 do extrato) |
| Títulos do Contas a Pagar | 2.060 |
| Classificados automaticamente | 338 (77,0%) |
| Em pendência | 101 linhas, agrupadas em **19 fornecedores** |
| Histórico derivado | 263 (59,9%) |
| Valor total | R$ 7.272.691,01 |

A razão de 101 linhas caberem em 19 decisões é o que faz o produto valer: `AMBAR ENERGIA` sozinha
são 32 linhas.

## Decisões desta fase

### 1. O frontend não decide nada de contábil

Toda escolha de conta, derivação de histórico e validação está no backend. O React exibe, filtra e
envia intenção. Consequência prática: um agente futuro que precise de outra interface (CLI, planilha,
integração) não reimplementa regra nenhuma.

### 2. Reprocessar é recalcular tudo, exceto o que o humano decidiu

`_reprocessar` apaga os lançamentos e ocorrências do lote e recalcula a partir dos `Pagamento` e
`TituloContasPagar` importados, que são imutáveis. As linhas em `MANUAL` são reinjetadas como
edições e vencem o resultado automático (RF-05.2).

Isso é o que faz "criar regra" mudar o status de todas as linhas do fornecedor de uma vez, e o que
mantém a edição manual viva depois de N reprocessamentos.

### 3. Resolver pendência cria regra, não corrige linha

A tela de pendências agrupa por fornecedor e o botão é **Criar regra**. Corrigir linha por linha
resolveria junho e nada mais; criar regra faz o volume cair mês a mes. Regra anterior conflitante é
**desativada**, não apagada, para preservar o rastro.

### 4. `REGRA_AMBIGUA` suprime `CONTA_DEBITO_AUSENTE`

São causa e efeito. Reportar os dois faria a tela mostrar dois motivos para uma única decisão. O
motivo acionável é a ambiguidade.

### 5. A coluna de crédito desaparece da tabela quando é constante

Ela é a mesma em 100% das linhas do mês, porque todo pagamento sai da mesma conta corrente. Repetir
isso 439 vezes gastaria a coluna mais disputada da tela; aparece uma vez, acima da tabela. Se
chegarem duas contas correntes, a coluna volta sozinha.

**Supersedido por [ADR 0011](../adr/0011-grade-fortes-na-validacao.md) (Fase 6):** crédito é coluna
em toda linha, porque a tela Validar passou a ser a planilha Fortes.

## Armadilhas para a Fase 4

- **`historico_derivado` no resumo conta a ausência do warning, não a presença de título.** As duas
  contagens divergem quando o histórico vem de enriquecimento SISPAG sem título casado. Ao medir
  taxa de derivação, decida qual das duas está medindo.
- **O gabarito de junho tem 5 linhas sem correspondência nos PDFs Itaú.** O `_indexar` dos testes
  casa por `(data, valor)`; essas 5 caem em `sem_par`. Não é bug do parser (pergunta aberta #3 do
  handover da Fase 1).
- **A ordem de importação importa para o histórico, não para a conta.** Importar o Contas a Pagar
  antes do Itaú produz o mesmo resultado final porque cada upload reprocessa o lote inteiro. O que
  muda é o resumo intermediário: `historico_derivado: 0` até o Contas a Pagar entrar.
- **`TestClient` precisa de `DATABASE_PATH` definido antes do import de `app.banco`**, porque o
  engine nasce no import. Daí o `monkeypatch` de escopo de módulo em `tests/test_api.py`.
- **Regras criadas em teste sobrevivem no banco daquele módulo.** `POST /api/regras` reprocessa
  todos os lotes abertos, então um teste que cria regra afeta os lotes de outros testes do mesmo
  módulo. Foi por isso que `TestExportacaoLiberada` usa lote próprio.

## Como validar que esta fase está de fato concluída

```bash
cd backend && .venv/bin/python -m pytest -q          # suíte inteira verde
cd frontend && npx tsc -b --noEmit && npx vite build
```

Verificação manual do ciclo completo:

```bash
# terminal 1
cd backend && DATABASE_PATH=/tmp/junho.db .venv/bin/python -m uvicorn app.api:app --port 8000
# terminal 2
cd frontend && npm run dev
```

1. `GET /api/saude` → 1.750 contas, 174 fornecedores, 203 regras, 161 ativas.
2. Importar os 3 PDFs de junho → 439 lançamentos, 19 grupos de pendência.
3. Resolver uma pendência de N linhas → as N saem de `PENDENTE` de uma vez.
4. Tentar exportar com lote `BLOQUEADO` → 409 com mensagem em português.
5. Alternar tema: nenhuma cor deve ser codificada em componente
   (`rg "#[0-9a-f]{6}" frontend/src --glob '!estilos/*'` sai vazio).

## Perguntas ao cliente que continuam abertas

As mesmas cinco da Fase 1. A #2 (critério nos fornecedores ambíguos) passou a ter preço medido: são
os **6 maiores grupos de pendência** de junho, cobrindo 66 das 101 linhas pendentes.
