**vamos precisar montar a base do de para antes de iniciar o processo de engenharia**

Fases vivas: [`README.md`](../README.md). A executar: Fase 7 — design, usabilidade e administração de competências ([FASE-7](handover/FASE-7.md)).

# plano/projeto de eng de sw

## 1. Levantamento de Requisitos (enxuto)
• Entrada de Dados: Importação de arquivo de extrato bancário

• Motor de De/Para: Regras para associar um fornecedor a uma conta

• Interface de Resolução: 
    1. Tela simples para tratar manualmente os lançamentos que o sistema
    não conseguiu associar sozinhos.
    2. Tela simples de exibicao para validacao humana

• Exportação: Relatório ou arquivo estruturado (.CSV) dos lançamentos já categorizados e
conciliados no modelo de importacao fortesERP

## 2. Projeto e Design Técnico
• Arquitetura: Aplicação web nuvem (possivelmente Python, Flask e SQLite)

• Estrutura de Banco de Dados Básica:
    Tabela Campos Principais
    Extrato Importado Data, Descrição Original, Valor, Status (Conciliado/Pendente)
    Regras De/Para, Termo de Busca (Texto Banco), Destino, Conta Contábil

## 3. Implementação (Sprint de Código)
• Passo 1: Desenvolver o parser do arquivo (ler o .pdf ou .CSV e salvar temporariamente).

• Passo 2: Criar a lógica do motor de busca (fazer um loop buscando o termo da regra dentro da
descrição do banco)

• Passo 3: Montar a tela para exibir, tela de ajustes, a tabela e o formulário para salvar novas regras
dinamicamente

## 4. Testes e Validação
• Usar um arquivo real de extrato bancário antigo para rodar o motor e verificar falsos positivos

• Validar se ao criar uma nova regra 'De/Para' na tela, os itens correspondentes mudam de status
automaticamente
