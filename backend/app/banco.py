"""Sessao SQLite e bootstrap das bases."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from .modelos import ContaBancaria, Fornecedor, PlanoContas, RegraDePara, SessaoLogin, Usuario
from .parsers.plano_contas import carregar_plano_contas, extrair_base_bancos
from .seed import carregar_base_depara

RAIZ = Path(__file__).resolve().parents[2]
CAMINHO_BANCO = Path(os.getenv("DATABASE_PATH", RAIZ / "backend" / "dados.db"))
PLANO_PADRAO = RAIZ / "arquivos-clickip" / "clickIP" / "PLANO DE CONTAS CLICK SCM 2026.xlsx"

engine = create_engine(f"sqlite:///{CAMINHO_BANCO}", connect_args={"check_same_thread": False})


def criar_tabelas() -> None:
    _ = (Usuario, SessaoLogin)
    SQLModel.metadata.create_all(engine)


def obter_sessao() -> Iterator[Session]:
    with Session(engine) as sessao:
        yield sessao


def semear(sessao: Session, plano: Path = PLANO_PADRAO) -> dict[str, int]:
    """Carrega plano de contas, Base Bancos e a base De/Para minerada.

    Idempotente: se as tabelas ja tem dados, nao faz nada. Reseed exige limpar o
    banco de proposito, para nao duplicar regra editada a mao pelo contador.
    """
    if sessao.exec(select(PlanoContas).limit(1)).first():
        return {"status": "ja semeado"}

    contas = carregar_plano_contas(plano)
    sessao.add_all(contas)
    bancos = extrair_base_bancos(contas)
    sessao.add_all(bancos)
    sessao.commit()

    fornecedores, pareadas = carregar_base_depara()
    sessao.add_all(fornecedores)
    sessao.commit()

    indice = {f.chave_nome: f.id for f in fornecedores}
    regras = []
    for chave, regra in pareadas:
        regra.fornecedor_id = indice[chave]
        regras.append(regra)
    sessao.add_all(regras)
    sessao.commit()

    return {
        "plano_contas": len(contas),
        "contas_bancarias": len(bancos),
        "fornecedores": len(fornecedores),
        "regras": len(regras),
        "regras_ativas": sum(1 for r in regras if r.ativo),
    }
