"""Fixtures compartilhadas: os arquivos reais do cliente como golden files.

Junho e a fixture de ouro: os dois relatorios Itau cobrem o mes inteiro e
CLICK SCM 062026.xlsx tem as 439 linhas correspondentes, com a coluna K de
favorecido que so existe nesse arquivo.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("AUTH_MODO", "desligado")
# Antes de qualquer import de app.banco: senão o engine aponta para dados.db.
os.environ["DATABASE_PATH"] = str(Path(tempfile.mkdtemp(prefix="concilia-pytest-")) / "teste.db")

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))

ARQUIVOS = RAIZ / "arquivos-clickip" / "clickIP"
PLANO = ARQUIVOS / "PLANO DE CONTAS CLICK SCM 2026.xlsx"
ITAU_PAGAMENTOS = ARQUIVOS / "Relatorio ITAU CLICK-SCM - 01 A 20-06-2026.pdf"
ITAU_EXTRATO = ARQUIVOS / "Relatorio ITAU CLICK-SCM - 21 A 30-06-2026.pdf"
CONTAS_PAGAR = ARQUIVOS / "Contas a Pagar - Pagas - Click Ip SCM 01-01-2026 a 30-06-2026.pdf"
GABARITO_JUNHO = ARQUIVOS / "CLICK SCM 062026.xlsx"


@pytest.fixture(scope="session")
def plano_contas():
    from app.parsers.plano_contas import carregar_plano_contas

    return carregar_plano_contas(PLANO)


@pytest.fixture(scope="session")
def base_bancos(plano_contas):
    from app.parsers.plano_contas import extrair_base_bancos

    return extrair_base_bancos(plano_contas)


@pytest.fixture(scope="session")
def conta_itau(base_bancos):
    return next(b for b in base_bancos if "Ita" in b.banco)


@pytest.fixture(scope="session")
def pagamentos_junho():
    from app.parsers import itau

    pagamentos = itau.carregar_pagamentos(ITAU_PAGAMENTOS, lote_id=1)
    pagamentos += itau.carregar_extrato(ITAU_EXTRATO, lote_id=1)
    for i, p in enumerate(pagamentos, start=1):
        p.id = i
    return pagamentos


@pytest.fixture(scope="session")
def titulos():
    from app.parsers.contas_pagar import carregar_titulos

    titulos = carregar_titulos(CONTAS_PAGAR, lote_id=1)
    for i, t in enumerate(titulos, start=1):
        t.id = i
    return titulos


@pytest.fixture(scope="session")
def base_depara():
    """Fornecedores e regras com ids atribuidos, como ficariam no banco."""
    from app.seed import carregar_base_depara

    fornecedores, pareadas = carregar_base_depara()
    for i, f in enumerate(fornecedores, start=1):
        f.id = i
    indice = {f.chave_nome: f.id for f in fornecedores}
    regras = []
    for i, (chave, regra) in enumerate(pareadas, start=1):
        regra.id = i
        regra.fornecedor_id = indice[chave]
        regras.append(regra)
    return fornecedores, regras


@pytest.fixture(scope="session")
def processado(plano_contas, base_depara, conta_itau, pagamentos_junho, titulos):
    from app.motor.processador import Processador

    fornecedores, regras = base_depara
    processador = Processador(plano_contas, fornecedores, regras, conta_itau)
    return processador.processar(1, pagamentos_junho, titulos)


@pytest.fixture(scope="session")
def gabarito():
    """As 439 linhas de junho: (data, valor) -> conta_debito, centro, historico."""
    import openpyxl

    ws = openpyxl.load_workbook(GABARITO_JUNHO, data_only=True).active
    linhas = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if not r[1]:
            continue
        linhas.append(
            {
                "data": str(r[1]),
                "conta_debito": str(r[2] or "").strip(),
                "conta_credito": str(r[3] or "").strip(),
                "valor": round(float(r[4]), 2),
                "historico": str(r[5] or "").strip(),
                "centro_custo": str(r[6] or "").strip(),
                "favorecido": str(r[10] or "").strip() if len(r) > 10 else "",
            }
        )
    return linhas
