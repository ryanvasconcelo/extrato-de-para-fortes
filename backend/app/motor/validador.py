"""Validacao com blockers e warnings.

Blocker impede exportar; warning permite exportar com ciencia. Os codigos vem da
Fase 1 (docs/requisitos/01-requisitos-funcionais.md) e sao estaveis: os testes da
Fase 4 asseveram codigo, nao mensagem.

Padrao herdado de reference/de-para-folha/journal-builder.js (ADR 0004).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..modelos import Lancamento, PlanoContas, Severidade
from ..normalizacao import normalizar_conta


class Codigo:
    # Blockers
    CONTA_DEBITO_AUSENTE = "CONTA_DEBITO_AUSENTE"
    CONTA_INEXISTENTE = "CONTA_INEXISTENTE"
    CONTA_NAO_ANALITICA = "CONTA_NAO_ANALITICA"
    REGRA_AMBIGUA = "REGRA_AMBIGUA"
    VALOR_INVALIDO = "VALOR_INVALIDO"
    BANCO_NAO_MAPEADO = "BANCO_NAO_MAPEADO"
    # Warnings
    HISTORICO_NAO_DERIVADO = "HISTORICO_NAO_DERIVADO"
    CENTRO_CUSTO_SUGERIDO = "CENTRO_CUSTO_SUGERIDO"
    REGRA_CONFIANCA_MEDIA = "REGRA_CONFIANCA_MEDIA"
    FORNECEDOR_SEM_DOCUMENTO = "FORNECEDOR_SEM_DOCUMENTO"
    TITULO_REUTILIZADO = "TITULO_REUTILIZADO"
    DIVERGENCIA_TOTAL = "DIVERGENCIA_TOTAL"


BLOCKERS = frozenset(
    {
        Codigo.CONTA_DEBITO_AUSENTE,
        Codigo.CONTA_INEXISTENTE,
        Codigo.CONTA_NAO_ANALITICA,
        Codigo.REGRA_AMBIGUA,
        Codigo.VALOR_INVALIDO,
        Codigo.BANCO_NAO_MAPEADO,
    }
)


@dataclass(frozen=True)
class Achado:
    severidade: Severidade
    codigo: str
    mensagem: str


class Validador:
    def __init__(self, plano: list[PlanoContas]) -> None:
        self._contas = {c.codigo: c for c in plano}

    def validar(self, lancamento: Lancamento) -> list[Achado]:
        achados: list[Achado] = []

        if lancamento.valor <= 0:
            achados.append(
                Achado(
                    Severidade.BLOCKER,
                    Codigo.VALOR_INVALIDO,
                    f"Valor {lancamento.valor} nao e positivo.",
                )
            )

        if not lancamento.conta_credito:
            achados.append(
                Achado(
                    Severidade.BLOCKER,
                    Codigo.BANCO_NAO_MAPEADO,
                    "Conta corrente de origem sem conta contabil na Base Bancos.",
                )
            )

        debito = normalizar_conta(lancamento.conta_debito)
        if not debito:
            achados.append(
                Achado(
                    Severidade.BLOCKER,
                    Codigo.CONTA_DEBITO_AUSENTE,
                    "Lancamento sem conta de debito.",
                )
            )
        else:
            achados += self._validar_conta(debito, "debito")

        if lancamento.conta_credito:
            achados += self._validar_conta(normalizar_conta(lancamento.conta_credito), "credito")

        return achados

    def _validar_conta(self, codigo: str, lado: str) -> list[Achado]:
        conta = self._contas.get(codigo)
        if conta is None:
            return [
                Achado(
                    Severidade.BLOCKER,
                    Codigo.CONTA_INEXISTENTE,
                    f"Conta de {lado} {codigo} nao consta no plano de contas.",
                )
            ]
        if not conta.analitica:
            return [
                Achado(
                    Severidade.BLOCKER,
                    Codigo.CONTA_NAO_ANALITICA,
                    f"Conta de {lado} {codigo} e sintetica e nao aceita lancamento.",
                )
            ]
        return []


def tem_blocker(achados: list[Achado]) -> bool:
    return any(a.severidade is Severidade.BLOCKER for a in achados)
