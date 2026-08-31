# ADR 0002 — Chave de casamento De/Para: documento + nome, não substring

- **Status:** Aceito
- **Data:** 2026-08-24
- **Fase:** 0

## Contexto

[`00-plano-engenharia.md`](../00-plano-engenharia.md) §3 define o motor como
"um loop buscando o termo da regra dentro da descrição do banco". O análogo mais próximo no Rayo,
[`reference/extrato-financeiro/categoria-detector.js`](../../reference/extrato-financeiro/categoria-detector.js),
faz exatamente isso: `lower.includes(pattern)`.

Os dados do cliente mostram que essa chave não funciona neste domínio.

### Evidência 1 — substring gera falso positivo real

O grupo ClickIP tem cinco entidades com prefixo comum e cinco contas distintas:

| Documento | Nome | Conta |
|---|---|---|
| `19402859000155` | `CLICK IP I MAIS` | `1.01.01.02.01.0004` |
| `13169745000120` | `CLICK IP LOCACAO DE EQUIPAMENTOS LTD` | `1.01.05.01.02.0009` |
| `13184931000139` | `CLICK IP PROVEDORES DE ACESSO LTDA` | `1.01.05.01.02.0007` |
| `19402859000155` | `CLICK IP SERVICOS DE COMUNICAC` | `1.01.05.01.01.0001` |
| `39809271000128` | `CLICK IP TECNOLOGIA LTDA` | `1.01.05.01.02.0008` |

`descricao.includes("CLICK IP")` casa com todas. A seção 4 do plano manda testar falso positivo de
substring; este é o teste, e a abordagem original falha nele.

### Evidência 2 — nomes chegam degradados

- Truncados em 30 caracteres: `EQUINIX DO BRASIL SOLUCOES DE`.
- Em variantes entre fontes: `EQUATORIAL PARA DISTRIBUIDORA` vs `... DE ENERGIA S.A.`.
- Com sufixo societário inconsistente: `GRUPO MULTI S.A` e `GRUPO MULTI SA`.
- Quebrados em múltiplas linhas no PDF do extrato:
  `ASSOCIACAO BRASILEIRA DE` / `RECURSOS EM TELECOMUNICAC`.

### Evidência 3 — o documento existe e é canônico

Ambos os relatórios Itaú trazem `CPF/CNPJ`. Cobertura medida: 241 das 261 linhas do relatório de
pagamentos e 169 das 173 do extrato.

### Evidência 4 — mas o documento sozinho também não basta

4 documentos aparecem sob nomes diferentes com contas diferentes. O caso claro é o CNPJ da própria
empresa (`19.402.859/0001-55`), que serve tanto para transferência entre contas próprias quanto
para lançamento intercompany — linhas 1 e 4 da tabela acima.

## Decisão

A chave de casamento é **documento normalizado + nome normalizado**, resolvida em cascata:

1. **Documento + nome** batem exatamente → casamento forte.
2. **Documento** bate e é único para um só fornecedor → casamento forte.
3. **Documento** bate mas é compartilhado por vários nomes → desempata pelo nome normalizado; sem
   desempate, vira pendência.
4. **Sem documento** na origem (concessionárias) → casa por nome normalizado.
5. Nada bate → pendência. **Nunca** casamento parcial silencioso.

Normalizações obrigatórias:

- **Documento:** apenas dígitos; aceito com 11 (CPF) ou 14 (CNPJ). O extrato traz CPF de pessoa
  física em 4 linhas de 173, então rejeitar 11 dígitos perderia lançamento.
- **Nome:** maiúsculas, sem acento, sem pontuação, espaços colapsados, sufixo societário
  (`S.A`, `SA`, `LTDA`, `EIRELI`, `ME`, `EPP`, `MEI`) removido, truncado em 29 caracteres para
  absorver o corte de 30 das fontes.

Substring sobre descrição bancária **não é usada** para determinar conta contábil. A descrição
(`BOLETO PAGO`, `PIX ENVIADO`, `SISPAG FORNECEDORES`) entra só como metadado exibido ao humano.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Substring sobre descrição, como no plano | Falha no teste `CLICK IP`. Ver evidência 1. |
| Só documento | Falha nos 4 documentos compartilhados. Ver evidência 4. |
| Só nome normalizado | Funciona para os 78 sem documento, mas descarta a única chave canônica disponível para os outros 96 e reintroduz o risco de truncamento. |
| Fuzzy matching (Levenshtein) sobre nomes | Resolveria o truncamento sem regra explícita, mas introduz um limiar arbitrário em decisão contábil. Normalização determinística cobre os casos observados e é auditável. |

## Consequências

**Positivas**
- Casamento determinístico e auditável: dá para explicar ao contador por que uma linha casou.
- O falso positivo que o plano manda testar fica estruturalmente impossível.
- Suporta CPF de pessoa física sem código adicional.

**Negativas**
- 78 fornecedores (concessionárias) permanecem dependentes de nome, com risco residual de
  truncamento.
- A cascata de 5 níveis é mais código que um `includes()`.
- Nomes normalizados para 29 caracteres podem, em teoria, colidir entre fornecedores diferentes.
  Não ocorre nos dados atuais; a Fase 3 deve emitir aviso se ocorrer.

## Verificação

Teste obrigatório na Fase 4: as cinco entidades `CLICK IP` precisam produzir cinco contas
distintas. Se produzirem uma só, a decisão foi violada.
