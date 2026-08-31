"""Parser do 'Contas a Pagar - Pagas' (Fortes AG Financeiro 5.65.1).

Fonte unica da coluna Historico. 59 paginas, 2.060 titulos.
Tecnica e ancoras validadas pelo spike da Fase 2 (ADR 0007).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pdfplumber

from ..modelos import TituloContasPagar
from ..normalizacao import moeda_para_decimal
from .pdf_coordenada import Coluna, linhas_por_baseline

# Ancoras medidas no PDF. Reproduziveis com:
#   python3 tools/spike_contas_pagar.py --ancoras --paginas 2
COLUNAS = [
    Coluna("fornecedor", 30.0, 166.0, "esq"),
    Coluna("conta_pag", 166.0, 222.0, "esq"),
    Coluna("vencimento", 222.0, 266.0, "esq"),
    Coluna("tipo_doc", 266.0, 337.0, "esq"),
    Coluna("titulo", 337.0, 440.0, "esq"),
    Coluna("doc_entrada", 440.0, 496.0, "dir"),
    Coluna("valor_titulo", 496.0, 553.0, "dir"),
    Coluna("valor_pago", 553.0, 610.0, "dir"),
    Coluna("desconto", 610.0, 655.0, "dir"),
    Coluna("juros", 655.0, 700.0, "dir"),
    Coluna("total_pago", 700.0, 792.0, "dir"),
]

X_MINIMO_LINHA_COMPLETA = 400.0

_DESPESA = re.compile(r"Despesa:\s*(?P<codigo>\d+)\s*-\s*(?P<descricao>.+)")
_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
_VALOR = re.compile(r"^[\d.]+,\d{2}$")

# O campo Fornecedor traz "NOME CPF" apenas para pessoa fisica: 15 de 2.060
# registros (0,7%). Nao e chave de join utilizavel (ADR 0007), mas quando existe
# vale extrair.
_NOME_COM_DOCUMENTO = re.compile(r"^(?P<nome>.*?)\s*(?P<doc>\d{11}|\d{14})$")


def _data(valor: str) -> date | None:
    if not _DATA.match(valor or ""):
        return None
    d, m, a = valor.split("/")
    return date(int(a), int(m), int(d))


def _separar_documento(fornecedor: str) -> tuple[str, str]:
    m = _NOME_COM_DOCUMENTO.match(fornecedor)
    return (m.group("nome").strip(), m.group("doc")) if m else (fornecedor, "")


def _e_titulo(r: dict[str, str]) -> bool:
    """Titulo pago tem fornecedor, vencimento valido e valor pago valido.

    Descarta cabecalho, linhas 'Despesa:', subtotais e rodape sem precisar
    enumera-los.
    """
    return bool(
        r["fornecedor"] and _DATA.match(r["vencimento"] or "") and _VALOR.match(r["valor_pago"] or "")
    )


def _despesas_da_pagina(pagina) -> list[tuple[float, str, str]]:
    """Localiza os cabecalhos 'Despesa: NNNNNN - Descricao' com a posicao y.

    Um grupo de despesa atravessa paginas e uma pagina pode conter varios grupos,
    entao a atribuicao precisa ser por posicao, nao por pagina.
    """
    achadas: list[tuple[float, str, str]] = []
    linhas: dict[int, list[dict]] = {}
    for palavra in pagina.extract_words(x_tolerance=1.5):
        linhas.setdefault(round(palavra["top"]), []).append(palavra)
    for top, palavras in linhas.items():
        texto = " ".join(w["text"] for w in sorted(palavras, key=lambda w: w["x0"]))
        m = _DESPESA.search(texto)
        if m:
            achadas.append((float(top), m.group("codigo"), m.group("descricao").strip()))
    return sorted(achadas)


def carregar_titulos(caminho: Path, lote_id: int) -> list[TituloContasPagar]:
    titulos: list[TituloContasPagar] = []
    # O grupo corrente atravessa paginas: nao reiniciar entre elas.
    codigo, descricao = "", ""

    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            despesas = _despesas_da_pagina(pagina)
            registros = linhas_por_baseline(
                pagina, COLUNAS, X_MINIMO_LINHA_COMPLETA, com_posicao=True
            )

            for r in registros:
                # Assume a ultima despesa declarada acima desta linha.
                for top, cod, desc in despesas:
                    if top <= r["_top"]:
                        codigo, descricao = cod, desc
                    else:
                        break
                if not _e_titulo(r):
                    continue
                nome, doc = _separar_documento(r["fornecedor"])
                titulos.append(
                    TituloContasPagar(
                        lote_id=lote_id,
                        fornecedor_raw=nome,
                        documento_raw=doc,
                        conta_pag=r["conta_pag"],
                        vencimento=_data(r["vencimento"]),
                        tipo_doc=r["tipo_doc"],
                        numero_titulo=r["titulo"],
                        doc_entrada=_data(r["doc_entrada"]),
                        valor_titulo=moeda_para_decimal(r["valor_titulo"]),
                        valor_pago=moeda_para_decimal(r["valor_pago"]),
                        total_pago=moeda_para_decimal(r["total_pago"]),
                        despesa_codigo=codigo,
                        despesa_descricao=descricao.strip(),
                    )
                )
    return titulos
