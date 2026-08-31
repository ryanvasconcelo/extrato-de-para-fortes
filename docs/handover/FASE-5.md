# Handover — Fase 5: Export e entrega

- **Concluída em:** 2026-08-24
- **Fase anterior:** [Fase 4](FASE-4.md) · **Próxima:** [Fase 6 — Grade Fortes](FASE-6.md)

## Em uma frase

O arquivo gerado para junho tem a mesma forma do que o contador entregou ao Fortes — 440 linhas, 10
colunas, linha-modelo idêntica, soma igual ao centavo (R$ 7.272.691,01) — e só sai depois de aprovação
humana, com a trava dentro do gerador.

## O que foi produzido

| Artefato | Conteúdo |
|---|---|
| [`backend/app/export_fortes.py`](../../backend/app/export_fortes.py) | Arquivo final + planilha de conferência, com `ExportacaoBloqueada` |
| [ADR 0010](../adr/0010-layout-export-fortes.md) | Layout derivado dos 6 arquivos, e o que continua desconhecido |
| [`README.md`](../../README.md) | Reescrito: `specs/` está vazia, e a estrutura real do projeto |
| `TestArquivoFinalDeJunho` | Compara o arquivo gerado com o do cliente |

## Duas descobertas que mudaram o gerador

### 1. São 10 colunas, não 11

As fases anteriores registraram "11 colunas". Medindo os seis arquivos: dois têm uma 11ª coluna
**vazia** (artefato de formatação) e um — junho — tem `favorecido / beneficiário`, que é anotação de
conferência do contador, não campo de importação. A 11ª não entra no arquivo final; o dado dela já
aparece na planilha de conferência, que é onde serve.

### 2. A linha 1 não é cabeçalho: é um modelo híbrido

```
0001 | Data | Débito | Crédito | " Valor " | Histórico | 0001 | 001 | 0001 | 001
```

Rótulo nas colunas variáveis, constante **já preenchida** nas fixas. Idêntica nos seis arquivos,
inclusive os espaços em volta de `" Valor "`.

A primeira implementação omitia essa linha, com o comentário "sem cabeçalho: a linha 1 já é dado".
Estava errada. Sem a especificação do RCO010, a única evidência do formato aceito são arquivos que
**têm** essa linha, e divergir do que funcionou por conta de uma interpretação é aposta sem prêmio.

O teste `test_linha_modelo_confere_com_o_arquivo_do_cliente` compara a constante do código contra o
arquivo real, e não contra uma cópia no próprio teste. Se o cliente mudar o modelo, ele falha.

## Decisões desta fase

### 1. Reproduzir o que funcionou, inclusive o que não se entende (ADR 0010)

As colunas H, I e J são `001`, `0001`, `001` nas 2.487 linhas históricas e ninguém sabe o que
significam. Saem iguais. O espaço em `" Valor "` sai igual. Está registrado como consequência
negativa, não escondido: se o Fortes exigir valor diferente para outra filial, o gerador está errado
e nenhum teste detecta.

### 2. A trava mora no gerador, não na rota

`arquivo_final` levanta `ExportacaoBloqueada` se o lote não estiver `APROVADO`. Validar só na rota
deixaria a regra fora do único ponto por onde o arquivo pode sair — um comando de linha ou um
agendamento futuro passaria por cima sem perceber.

### 3. Conferência antes, arquivo depois

Padrão de [`folha-dealer-checklist-validacao.md`](../referencia/folha-dealer-checklist-validacao.md).
A planilha de conferência sai em qualquer estado, com status e códigos de ocorrência por linha e as
linhas problemáticas destacadas. O arquivo final exige aprovação. A tela de exportação numera as três
etapas na ordem, com o botão da etapa 3 visivelmente travado até a 2 acontecer.

### 4. O README passou a dizer a verdade sobre `specs/`

A afirmação de que `specs/RCO010_ImportarLote.pdf` existe estava no README desde o início e induziu ao
erro por três fases. A correção é explícita, com um aviso próprio, em vez de apagar a linha em
silêncio — quem leu a versão antiga precisa entender o que mudou.

## Estado final do projeto

| Medida | Valor |
|---|---|
| Testes | 71, ~40s, sobre os arquivos reais |
| Rotas de API | 13 |
| Lançamentos de junho | 439, R$ 7.272.691,01 |
| Classificação automática | 77,0% |
| Precisão da conta de débito | 99,7% entre as classificadas |
| Histórico derivado | 59,9% |
| Pendências | 101 linhas em 19 decisões de fornecedor |
| ADRs | 10 (o 0011 foi registrado na abertura da Fase 6; o código dela ainda não existia) |

## O que falta para o produto estar validado

Nada disso bloqueia a entrega, mas nenhum foi feito:

1. **Uma competência nova, do início ao fim, com o contador.** É a única medição de acurácia real que
   existe — todo número deste projeto foi medido contra a base minerada dos mesmos arquivos (ADR
   0009). Julho é o teste.
2. **Confirmar que o Fortes aceita o arquivo gerado.** A forma é idêntica à dos seis aceitos, o que é
   evidência forte, não prova.
3. **Revisão da aba `Ambiguos`** de [`base-depara-inicial.xlsx`](../base-depara-inicial.xlsx). São 13
   fornecedores, e os 6 maiores concentram 66 das 101 linhas pendentes de junho. É a intervenção com
   melhor retorno disponível hoje.
4. **Segunda conta corrente.** O modelo é lookup em `ContaBancaria`, nunca exercitado com valor
   diferente de `1.01.01.02.01.0003`.

## Armadilhas para quem continuar

- **Não "conserte" a divergência de histórico.** 91 linhas de junho divergem do gabarito porque o app
  enriquece o que o processo manual deixava genérico (ADR 0005). Um agente que exigir 439/439 em
  histórico está revertendo a decisão sem ADR.
- **Não fixe a conta de crédito no código**, mesmo sendo a mesma em 100% das linhas. Ela vem do
  cabeçalho do relatório, casada contra a Base Bancos.
- **Não remova a linha-modelo do export** por parecer cabeçalho espúrio. Ver ADR 0010.
- **`arquivos-clickip/` é dependência da suíte.** Se ela sair do repositório, a maioria dos testes
  para de ter o que rodar. Não crie fixture sintética para "consertar": seria fingir cobertura.
- **ADR não se edita.** Divergência gera ADR novo que supersede. Os números que a Fase 4 mediu
  diferente estão na seção de correções do ADR 0009, não editados nos ADRs originais.

## Como validar que esta fase está de fato concluída

```bash
cd backend && .venv/bin/python -m pytest -q -k "ArquivoFinal or Exportacao"
```

1. `test_mesma_forma_do_arquivo_do_cliente` — 440 linhas, 10 colunas, linha 1 idêntica.
2. `test_soma_bate_ao_centavo` — R$ 7.272.691,01 nos dois.
3. `test_linha_modelo_confere_com_o_arquivo_do_cliente` — a constante bate com o XLSX real.
4. `test_lote_bloqueado_nao_exporta` e `test_exportado_nao_aceita_mais_edicao` — a trava e a
   imutabilidade pós-export.
5. O README não afirma mais que `specs/RCO010_ImportarLote.pdf` existe, e diz onde o layout foi
   derivado.

## Confirmações do cliente (pós-auditoria, 2026-08-24)

Registradas contra os fluxogramas em [`fluxograma/`](../../fluxograma):

1. A tabela de exibição segue o padrão visual e estrutural do Excel Fortes.
2. O que for editado na tabela é o que será exportado — é assim que o contador trata exceções (um mesmo fornecedor com contas diferentes).
3. Hospedagem futura: **https://conciliador.projecont.com.br**

## Perguntas ao cliente, em ordem de valor

1. **Critério nos 13 fornecedores ambíguos** — 66 das 101 pendências de junho.
2. **O RCO010 existe?** Confirmaria H, I, J e a linha-modelo sem inferência.
3. **Semântica de H, I e J** — respondida pela #2, se ela for sim.
4. **As 5 linhas de junho sem correspondência nos PDFs Itaú** — origem desconhecida.
5. **Outras contas correntes entram no escopo?**
