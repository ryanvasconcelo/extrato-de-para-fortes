# Handover — Fase 0: Descoberta e base De/Para

- **Concluída em:** 2026-08-24
- **Próxima fase:** [Fase 1 — Requisitos](FASE-1.md)

## Em uma frase

Os arquivos reais do cliente contradizem o plano original em três pontos estruturais; a base
De/Para, que não existia, foi minerada do histórico e cobre 93% dos fornecedores.

## O que foi produzido

| Artefato | Conteúdo |
|---|---|
| [`docs/02-analise-arquivos-cliente.md`](../02-analise-arquivos-cliente.md) | Análise medida dos 11 arquivos do cliente. **Leitura obrigatória.** |
| [`tools/minerar_depara.py`](../../tools/minerar_depara.py) | Minerador da base De/Para. Offline, fora do app. |
| [`docs/base-depara-inicial.csv`](../base-depara-inicial.csv) | Seed versionado: 203 regras de 174 fornecedores. |
| `docs/base-depara-inicial.xlsx` | Revisão para o contador: abas `Regras`, `Ambiguos`, `Colisoes`, `Resumo`. |
| [`docs/base-depara-inicial.md`](../base-depara-inicial.md) | Leitura dos resultados da mineração. |
| [ADR 0001](../adr/0001-arquitetura-stack.md) | React/Vite + FastAPI + SQLite |
| [ADR 0002](../adr/0002-chave-casamento-cnpj.md) | Chave = documento + nome, não substring |
| [ADR 0003](../adr/0003-constituicao-base-depara.md) | Base por mineração do histórico |
| [ADR 0004](../adr/0004-reaproveitamento-rayo.md) | Rayo: padrões sim, código não |

Skills instaladas em `~/.codex/skills/`: `impeccable`, `ui-ux-pro-max`, e o conjunto web de
`emilkowalski/skills` (`emil-design-eng`, `animate`, `animation-vocabulary`, `apple-design`,
`find-animation-opportunities`, `improve-animations`, `pick-ui-library`, `prototype`,
`review-animations`, `ask-sonner`). `karpathy-guidelines`, `taste-skill` e o catálogo
tech-leads-club já estavam presentes.

## O que o próximo agente precisa saber

### 1. O plano original está errado em três pontos

Não são detalhes; são o desenho do produto.

- **Três insumos, não um.** Dois relatórios Itaú *de layouts diferentes* mais o Contas a Pagar.
- **A chave é documento + nome, não substring da descrição.** Substring falha um teste real
  (grupo `CLICK IP`, cinco entidades com prefixo comum e cinco contas).
- **`specs/RCO010_ImportarLote.pdf` não existe.** `specs/` está vazia, apesar do
  [README](../../README.md) e da [análise Rayo](../01-analise-rayo-referencia.md) citarem o
  arquivo. O layout de export foi derivado dos 6 XLSX e confirmado contra o plano de contas.

### 2. Os dois PDFs Itaú são relatórios distintos

O erro fácil aqui é escrever um parser e assumir que serve para os dois arquivos.

| | `01 A 20` | `21 A 30` |
|---|---|---|
| Tipo | consulta de pagamentos | **extrato de conta corrente** |
| Colunas | 7 (com `favorecido`, `CPF/CNPJ`) | 6 (com `Lançamentos`, `Razão Social`) |
| Grade no PDF | sim → `extract_tables()` funciona | **não** → exige coordenada |
| Valores | positivos | **negativos** |
| Linhas | 261 | 173 |

### 3. Armadilhas confirmadas por medição

- **Dígito verificador.** O plano de contas grafa `1.01.01.02.01.0003-4`; o arquivo Fortes grafa
  `1.01.01.02.01.0003`. Sem normalizar, validar conta contra o plano falha em **100%** dos casos.
- **Duplicata de abril.** `CLICK SCM 042026 - ITAU.xlsx` e `... (1).xlsx` são byte-idênticos.
  Contar os dois inflaria o histórico de 2.487 para 2.893 linhas.
- **`SISPAG FORNECEDORES` não é falta de dado.** É dívida do processo manual. A taxa varia de 2% a
  32% entre meses, e 85% dessas linhas têm o valor presente no Contas a Pagar. Detalhes e
  consequência para os testes em [`02-analise`](../02-analise-arquivos-cliente.md) §6.
- **Centro de custo não é função do fornecedor.** 16 fornecedores usam múltiplos centros com a
  mesma conta. `ORSEGUPS` usa 6. A hipótese de que a coluna `referência da empresa` do Itaú
  explicaria isso **foi testada e rejeitada** — 164 de 284 linhas casadas têm essa coluna vazia.
  Não repetir esse teste.
- **CNPJ não é chave única.** O CNPJ da própria empresa (`19.402.859/0001-55`) aparece com duas
  contas de propósitos diferentes.

### 4. O maior risco técnico ainda não foi resolvido

O Contas a Pagar (59 páginas) devolve colunas colididas caractere a caractere:

```
DEYWISON BRUNO PEDROZA SILV2A0 7296305300403978238731/03/2026 NFS-E 41 27/03/2026 350,00
```

Sem esse arquivo não há coluna Histórico e o produto entrega 100% de `SISPAG`. É o spike
obrigatório da Fase 2 e a Fase 3 não deve começar sem ele.

## Como validar que esta fase está de fato concluída

Não confie neste relato; rode:

```bash
# 1. As skills estão instaladas
ls ~/.codex/skills/impeccable/SKILL.md ~/.codex/skills/ui-ux-pro-max/SKILL.md \
   ~/.codex/skills/emil-design-eng/SKILL.md

# 2. O minerador reproduz os números
python3 tools/minerar_depara.py
#   esperado: 2487 linhas, 174 fornecedores, 80 ALTA, 81 MEDIA, 13 AMBIGUO_CONTA
#   se aparecer 2893 linhas, a deduplicacao de abril quebrou

# 3. O teste de falso positivo passa
grep '^.*CLICK IP' docs/base-depara-inicial.csv | cut -d, -f1,2,3
#   esperado: 5 linhas, 5 contas distintas

# 4. specs/ realmente esta vazia (nao assuma que alguem colocou o RCO010)
ls -la specs/
```

## Perguntas abertas para o cliente

Nenhuma bloqueia a Fase 1, mas todas afetam a Fase 5.

1. Semântica das colunas H, I, J do arquivo Fortes (constantes `001`, `0001`, `001`).
2. Os 13 fornecedores ambíguos: qual critério humano de escolha? (aba `Ambiguos` do XLSX)
3. As 5 linhas de junho sem correspondência nos relatórios Itaú (434 extraídas vs 439 na planilha).
4. `SISPAG FORNECEDORES` deve ser enriquecido? (recomendação: sim — decidido na Fase 1)
5. O `RCO010_ImportarLote.pdf` existe em algum lugar?
6. Outras contas correntes (Bradesco, Cresol, BB, Sicoob) entram no escopo ou só Itaú?
