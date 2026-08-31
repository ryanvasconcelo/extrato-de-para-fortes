"""Carga da base De/Para minerada (docs/base-depara-inicial.csv).

Regras AMBIGUO_CONTA entram com ativo=False, para que o lancamento caia em
pendencia em vez de receber conta arbitraria. Ver ADR 0003.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from .modelos import Confianca, Fornecedor, OrigemRegra, RegraDePara
from .normalizacao import normalizar_conta, normalizar_documento, normalizar_nome_fornecedor

CSV_PADRAO = Path(__file__).resolve().parents[2] / "docs" / "base-depara-inicial.csv"


def carregar_base_depara(
    caminho: Path = CSV_PADRAO,
) -> tuple[list[Fornecedor], list[tuple[str, RegraDePara]]]:
    """Devolve fornecedores e regras.

    As regras saem pareadas com a chave do fornecedor porque os ids so existem
    depois do insert; quem persiste faz a ligacao.
    """
    linhas_por_fornecedor: dict[str, list[dict]] = defaultdict(list)
    with caminho.open(encoding="utf-8") as fh:
        for linha in csv.DictReader(fh):
            chave = normalizar_nome_fornecedor(linha["nome_canonico"])
            if chave:
                linhas_por_fornecedor[chave].append(linha)

    fornecedores: list[Fornecedor] = []
    regras: list[tuple[str, RegraDePara]] = []

    for chave, linhas in linhas_por_fornecedor.items():
        documentos = {normalizar_documento(l["documento"]) for l in linhas} - {""}
        nomes = sorted({l["nome_canonico"] for l in linhas}, key=len, reverse=True)
        fornecedores.append(
            Fornecedor(
                documento=sorted(documentos)[0] if len(documentos) == 1 else "",
                nome_canonico=nomes[0],
                chave_nome=chave,
                nomes_alternativos=nomes[1:],
            )
        )
        for l in linhas:
            confianca = Confianca(l["confianca"])
            regras.append(
                (
                    chave,
                    RegraDePara(
                        fornecedor_id=0,
                        conta_debito=normalizar_conta(l["conta_debito"]),
                        centro_custo_sugerido=l["centro_custo"] or "0001",
                        origem=OrigemRegra.MINERADA,
                        confianca=confianca,
                        ativo=confianca is not Confianca.AMBIGUO_CONTA,
                    ),
                )
            )

    return fornecedores, regras
