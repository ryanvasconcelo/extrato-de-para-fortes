# Prompt — sessão Fase 6

Copiar o bloco abaixo e colar como primeira mensagem do chat novo.

---

Execute a Fase 6 deste repositório com **subagent-driven development**.

## O que fazer

Implementar o plano, tarefa por tarefa, com um subagente novo por tarefa e revisão em duas etapas (spec, depois qualidade) depois de cada uma. Não parar no meio para perguntar se continua.

**Plano (fonte da verdade da implementação):**  
`docs/superpowers/plans/2026-08-24-grade-fortes-e-excecao-por-linha.md`

**Handover da fase:** `docs/handover/FASE-6.md`  
**Decisão já registrada:** `docs/adr/0011-grade-fortes-na-validacao.md` — não reescrever o ADR; só atualizar Verificação se o código divergir (divergência = ADR sucessor, não edição do 0011).

## Antes de qualquer código

1. Invocar e seguir `superpowers:subagent-driven-development`.
2. Ler por inteiro, nesta ordem:
   - `.cursor/rules/produto.mdc`
   - `docs/adr/0011-grade-fortes-na-validacao.md`
   - `docs/adr/0010-layout-export-fortes.md`
   - `docs/handover/FASE-6.md`
   - o plano acima (todas as tasks)
3. Trabalhar numa **branch nova** a partir do estado atual (`fase-6-grade-fortes` ou equivalente). Não implementar em `main`/`master`.
4. **Não fazer commit nem push** a menos que eu peça nesta sessão.
5. Não alterar `git config`.

## Objetivo de produto

A tela **Validar** é a planilha Fortes de 10 colunas (mesmo padrão do Excel). O que o usuário edita na célula é o que sai no XLSX. Exceção: o mesmo fornecedor pode ter contas diferentes em linhas diferentes — isso **não** cria regra De/Para e **não** reprocessa as irmãs.

Pendências continua sendo o lugar de **criar regra**. A grade **não** manda `criar_regra: true`.

## Não fazer

- Não reverter ADR 0002 (substring) nem ADR 0005 (enriquecer SISPAG).
- Não remover a linha-modelo do XLSX (ADR 0010).
- Não portar `reference/`.
- Não esconder a coluna de crédito.
- Não inventar heurística para os 13 fornecedores ambíguos.
- Não fazer deploy em `conciliador.projecont.com.br`.
- Não baixar limiares da suíte (ADR 0009) nem criar fixture sintética de PDF.

## Quando as 7 tasks do plano passarem

1. Rodar `cd backend && .venv/bin/python -m pytest -q` e o build do frontend.
2. Verificar a UI no browser (fluxo da seção “Como validar” do FASE-6).
3. Atualizar `docs/handover/FASE-6.md`: status **Concluída em** + resultados dos comandos.
4. Atualizar a tabela de fases do `README.md` se a Fase 6 ainda aparecer como “a executar”.
5. Parar. Relatar o que mudou e o que ficou para o humano (ambíguos, round-trip Fortes, deploy).

---
