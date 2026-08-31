# ADR 0006 — Modelo de dados e normalização de códigos de conta

- **Status:** Aceito
- **Data:** 2026-08-24
- **Fase:** 2

## Contexto

Os requisitos da Fase 1 exigem persistir três bases (De/Para, Base Bancos, Plano de Contas), dois
insumos por lote (pagamentos e títulos) e os lançamentos com ciclo de vida de 5 estados.

### A armadilha do dígito verificador

O Plano de Contas grafa os códigos **com** dígito verificador:

```
1.01.01.02.01.0003-4    Banco Itaú Ag: 1557 Cc: 98810-0
```

O arquivo de destino Fortes grafa **sem**:

```
1.01.01.02.01.0003
```

1.519 das 1.864 linhas do plano têm o sufixo. Comparar as duas grafias diretamente faz a validação
"esta conta existe no plano?" falhar em **100%** dos casos — e falhar de forma que parece bug de
dado, não de código.

## Decisão

### Normalização

`PlanoContas` guarda **as duas** grafias em colunas separadas: `codigo` (sem DV, canônico para
comparação e para o export) e `codigo_dv` (como veio, para exibir ao contador). Toda comparação usa
`codigo`.

A normalização é uma função única, `normalizar_conta()`, aplicada em todo ponto de entrada. Não
existe comparação de conta que não passe por ela.

### Entidades

```
Fornecedor           id, documento(11|14, indexado), nome_canonico, nomes_alternativos[]
                     documento pode ser vazio: 78 concessionarias nao tem

RegraDePara          id, fornecedor_id, conta_debito, centro_custo_sugerido,
                     origem(MINERADA|MANUAL), confianca(ALTA|MEDIA|AMBIGUO_CONTA),
                     ativo, criada_em, criada_por
                     ambigua entra com ativo=False

ContaBancaria        id, banco, agencia, conta_corrente, conta_contabil
                     as 5 contas do plano; so o Itau aparece no historico

PlanoContas          codigo(PK, sem DV), codigo_dv, descricao, natureza,
                     reduzido, analitica(bool)
                     1864 linhas, 1516 analiticas

LoteImportacao       id, competencia, status(RASCUNHO|BLOQUEADO|PRONTO|APROVADO|EXPORTADO),
                     conta_bancaria_id, criado_em, aprovado_por, aprovado_em, exportado_em

ArquivoImportado     id, lote_id, nome, sha256, tipo(ITAU_PAGAMENTOS|ITAU_EXTRATO|
                     CONTAS_PAGAR|PLANO_CONTAS), linhas_lidas
                     sha256 implementa RF-01.8

Pagamento            id, lote_id, arquivo_id, data, favorecido_raw, documento_raw,
                     tipo_pagamento, referencia_empresa, valor, descricao_banco

TituloContasPagar    id, lote_id, fornecedor_raw, documento_raw, conta_pag, vencimento,
                     tipo_doc, numero_titulo, doc_entrada, valor_titulo, valor_pago,
                     desconto, juros, total_pago, despesa_codigo, despesa_descricao

Lancamento           id, pagamento_id, titulo_id?, regra_id?, filial, conta_debito,
                     conta_credito, valor, historico, centro_custo,
                     status(PENDENTE|AUTO|MANUAL|APROVADO|EXPORTADO),
                     editado_por, editado_em

Ocorrencia           id, lancamento_id, severidade(BLOCKER|WARNING), codigo, mensagem
                     os 6+6 codigos da Fase 1
```

### Decisões de modelagem que merecem registro

**`conta_credito` é gravada no lançamento, não derivada na exportação.** Vem de `ContaBancaria` via
o lote. Gravar torna o lançamento auto-contido e auditável depois que a base muda.

**`Ocorrencia` é tabela, não campo calculado.** Precisa sobreviver ao request para a tela de
pendências filtrar por código e para o teste da Fase 4 asseverar códigos específicos.

**`centro_custo_sugerido` na regra, `centro_custo` no lançamento.** Consequência direta da medição
da Fase 0: 16 fornecedores usam múltiplos centros com a mesma conta. Um campo só forçaria escolher
entre perder a sugestão e perder o ajuste manual.

**`titulo_id` é opcional.** 18% dos pagamentos não têm título correspondente
([ADR 0007](0007-estrategia-extracao-pdf.md)). Obrigatório impediria gravar o lançamento.

**`nomes_alternativos` é lista, não tabela.** Os nomes chegam truncados e em variantes; guardar
todas as formas vistas melhora o casamento futuro sem criar entidade para um atributo.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Guardar só `codigo` sem DV e recalcular o DV para exibir | O DV é do plano de contas do cliente, não um checksum que a gente saiba calcular. Recalcular seria inventar. |
| Guardar só `codigo_dv` e normalizar em toda comparação | Funciona, mas põe a normalização no caminho de toda query em vez de na entrada. Uma chamada esquecida vira bug silencioso. |
| Uma tabela `Movimento` unificando `Pagamento` e `Lancamento` | Menos tabelas, mas mistura fato importado (imutável) com resultado calculado (recalculável a cada reprocessamento). Separar permite reprocessar sem reimportar — que é o RF-02.9. |
| `Ocorrencia` como JSON no `Lancamento` | Menos uma tabela. Rejeitado por causa da tela de pendências, que filtra por código. |

## Consequências

**Positivas**
- A armadilha do DV fica resolvida num único ponto.
- Reprocessar não reimporta: `Pagamento` e `TituloContasPagar` são imutáveis, `Lancamento` é
  recalculável.
- O lançamento é auto-contido, então o arquivo exportado é reproduzível mesmo depois de a base De/Para
  mudar.

**Negativas**
- 9 tabelas para um app de escopo pequeno.
- `documento_raw` e `favorecido_raw` duplicam o que já está em `Fornecedor` depois do casamento.
  Deliberado: preserva o insumo original para auditoria e para reprocessar com regra melhor.
- `codigo` e `codigo_dv` são redundantes por construção.

## Verificação

- Validar `1.01.01.02.01.0003` contra o plano deve encontrar `1.01.01.02.01.0003-4`. Se não
  encontrar, a normalização não está no caminho.
- Contas sintéticas devem produzir `CONTA_NAO_ANALITICA`: 348 das 1.864 linhas do plano não aceitam
  lançamento.
