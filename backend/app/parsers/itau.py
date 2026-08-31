"""Parsers dos relatorios Itau.

Sao DOIS relatorios diferentes, apesar de os nomes de arquivo sugerirem duas
metades do mesmo (docs/02-analise-arquivos-cliente.md secao 2):

  ITAU_PAGAMENTOS  consulta de pagamentos, transferencias e Pix
                   7 colunas, COM linhas de grade -> extract_tables() funciona
                   valores positivos

  ITAU_EXTRATO     extrato de conta corrente
                   6 colunas, SEM grade -> extracao por coordenada
                   valores negativos, razao social em coluna separada

`detectar_tipo` escolhe o parser. Escrever um parser so e assumir que serve para
os dois arquivos e o erro facil aqui.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from pathlib import Path

import pdfplumber

from ..modelos import Pagamento, TipoArquivo
from ..normalizacao import moeda_para_decimal, normalizar_documento
from .pdf_coordenada import PRECISAO_BASELINE, Coluna, coluna_de, sequencias

_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")

# Cabecalho da conta, presente nos dois layouts:
# "CLICK IP / I_MAIS CNPJ 19.402.859/0001-55 Agencia 1557 Conta 0098810-0"
_CABECALHO_CONTA = re.compile(
    r"Ag[êe]ncia\s+(?P<agencia>\d+)\s+Conta\s+(?P<conta>[\d-]+)", re.IGNORECASE
)

# Colunas do extrato de conta corrente (pagina retrato 595x842), medidas no PDF.
COLUNAS_EXTRATO = [
    Coluna("data", 0.0, 85.0, "esq"),
    Coluna("lancamento", 85.0, 220.0, "esq"),
    Coluna("razao_social", 220.0, 358.0, "esq"),
    Coluna("documento", 358.0, 450.0, "esq"),
    Coluna("valor", 450.0, 520.0, "dir"),
    Coluna("saldo", 520.0, 600.0, "dir"),
]


def _data(valor: str) -> date | None:
    if not _DATA.match((valor or "").strip()):
        return None
    d, m, a = valor.strip().split("/")
    return date(int(a), int(m), int(d))


def detectar_tipo(caminho: Path) -> TipoArquivo | None:
    """Identifica o layout pelo texto da primeira pagina (RF-01.6)."""
    with pdfplumber.open(caminho) as pdf:
        texto = (pdf.pages[0].extract_text() or "") if pdf.pages else ""
    if "Lançamentos do período" in texto or "Saldo total" in texto:
        return TipoArquivo.ITAU_EXTRATO
    if "favorecido" in texto.lower() or "beneficiário" in texto.lower():
        return TipoArquivo.ITAU_PAGAMENTOS
    if "Contas a Pagar" in texto or "Fortes" in texto:
        return TipoArquivo.CONTAS_PAGAR
    return None


def conta_do_cabecalho(caminho: Path) -> tuple[str, str] | None:
    """Devolve (agencia, conta_corrente) para casar com a Base Bancos.

    A conta de credito nao e constante: vem daqui (ver handover FASE-1).
    """
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages[:2]:
            m = _CABECALHO_CONTA.search(pagina.extract_text() or "")
            if m:
                return m.group("agencia"), m.group("conta").lstrip("0")
    return None


def carregar_pagamentos(caminho: Path, lote_id: int) -> list[Pagamento]:
    """Relatorio de consulta de pagamentos. Tem grade, entao extract_tables serve.

    Colunas: favorecido | CPF/CNPJ | tipo de pagamento | referencia da empresa
             | data do pagamento | valor | status
    """
    pagamentos: list[Pagamento] = []
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            for tabela in pagina.extract_tables():
                for linha in tabela:
                    if len(linha) < 6:
                        continue
                    data = _data(str(linha[4] or ""))
                    if not data:
                        continue
                    valor = moeda_para_decimal(linha[5])
                    if valor <= 0:
                        continue
                    pagamentos.append(
                        Pagamento(
                            lote_id=lote_id,
                            data=data,
                            favorecido_raw=_limpar(linha[0]),
                            documento_raw=normalizar_documento(linha[1]),
                            tipo_pagamento=_limpar(linha[2]),
                            referencia_empresa=_limpar(linha[3]),
                            valor=valor,
                        )
                    )
    return pagamentos


def _linhas_do_extrato(pagina) -> list[dict[str, str]]:
    """Extrai as linhas do extrato, remontando razoes sociais quebradas.

    Diferente do Contas a Pagar, aqui a razao social pode quebrar tanto ACIMA
    quanto ABAIXO da linha do lancamento:

        CLICK IP PROVEDORES DE ACESSO          <- fragmento acima
        22/06/2026 PAGAMENTOS TRANSF CC ITAU 13.184.931/0001-39 -85.000,00
        LTDA                                   <- fragmento abaixo

    Por isso `linhas_por_baseline`, que so anexa o que vem acima, nao serve.
    Identificamos as linhas de lancamento (tem data e valor) e distribuimos cada
    fragmento de nome para a linha de lancamento mais proxima.
    """
    por_baseline: dict[int, list[dict]] = defaultdict(list)
    for c in pagina.chars:
        por_baseline[round(c["top"] / PRECISAO_BASELINE)].append(c)

    lancamentos: list[tuple[int, dict[str, str]]] = []
    fragmentos: list[tuple[int, str]] = []

    for chave in sorted(por_baseline):
        celulas: dict[str, list[str]] = defaultdict(list)
        for seq in sequencias(por_baseline[chave]):
            nome = coluna_de(seq, COLUNAS_EXTRATO)
            if nome:
                celulas[nome].append(seq.texto)
        registro = {
            col.nome: _limpar(" ".join(celulas.get(col.nome, []))) for col in COLUNAS_EXTRATO
        }
        if _DATA.match(registro["data"]) and registro["valor"]:
            lancamentos.append((chave, registro))
        elif registro["razao_social"] and not registro["data"]:
            fragmentos.append((chave, registro["razao_social"]))

    for chave, texto in fragmentos:
        if not lancamentos:
            continue
        alvo, registro = min(lancamentos, key=lambda item: abs(item[0] - chave))
        # Fragmento acima entra antes do que ja existe; abaixo, depois.
        if chave < alvo:
            registro["razao_social"] = _limpar(f"{texto} {registro['razao_social']}")
        else:
            registro["razao_social"] = _limpar(f"{registro['razao_social']} {texto}")

    return [r for _, r in lancamentos]


def carregar_extrato(caminho: Path, lote_id: int) -> list[Pagamento]:
    """Extrato de conta corrente. Sem grade, valores negativos.

    Somente saidas entram: o produto gera lancamento de pagamento, e credito
    (recebimento) esta fora do escopo do MVP.
    """
    pagamentos: list[Pagamento] = []
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            for r in _linhas_do_extrato(pagina):
                data = _data(r["data"])
                # Sem o sinal negativo nao e saida de caixa.
                if not data or not r["valor"].startswith("-"):
                    continue
                valor = moeda_para_decimal(r["valor"])
                if valor <= 0:
                    continue
                pagamentos.append(
                    Pagamento(
                        lote_id=lote_id,
                        data=data,
                        favorecido_raw=r["razao_social"],
                        documento_raw=normalizar_documento(r["documento"]),
                        descricao_banco=r["lancamento"],
                        valor=valor,
                    )
                )
    return pagamentos


def _limpar(valor) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()
