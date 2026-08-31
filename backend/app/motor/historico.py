"""Derivacao da coluna Historico a partir do Contas a Pagar.

Nao existe chave canonica: o Contas a Pagar traz CPF/CNPJ em apenas 0,7% dos
titulos (ADR 0007). O casamento e por valor + nome + proximidade de data, e por
isso e heuristico por construcao - dai o warning obrigatorio quando falha.

Linha de base medida pelo spike da Fase 2: 58% de derivacao em junho. O processo
manual chegava a 79%. Este modulo tenta superar os 58% usando tambem tokens de
nome e a conta_pag, e emite HISTORICO_NAO_DERIVADO no que sobrar.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..modelos import Pagamento, TituloContasPagar
from ..normalizacao import tokens_fornecedor

# Um titulo pago costuma liquidar perto do vencimento. Acima de 45 dias, casar por
# valor passa a ser coincidencia mais que evidencia.
JANELA_DIAS = 45

# Grafias do tipo de documento como o contador escreve no historico.
_GRAFIA_TIPO_DOC = {
    "NF-E": "NF-e",
    "NFS-E": "NFS-e",
    "DANFE": "DANFE",
    "ND": "ND",
    "DARF": "DARF",
    "DACTE": "DACTE",
}

PREFIXO = "Débito Banc. ref."


@dataclass
class HistoricoDerivado:
    texto: str
    titulo: TituloContasPagar | None
    derivado: bool


def _grafia(tipo_doc: str) -> str:
    limpo = (tipo_doc or "").strip().upper()
    return _GRAFIA_TIPO_DOC.get(limpo, limpo.title())


def montar_texto(titulo: TituloContasPagar, nome_fornecedor: str) -> str:
    """`Débito Banc. ref. NFS-e 889048 - Orsegups Monitoramento`"""
    partes = [PREFIXO, _grafia(titulo.tipo_doc)]
    if titulo.numero_titulo:
        partes.append(titulo.numero_titulo)
    texto = " ".join(p for p in partes if p)
    nome = (nome_fornecedor or titulo.fornecedor_raw or "").strip()
    return f"{texto} - {nome.title()}" if nome else texto


class DerivadorHistorico:
    """Indice de titulos por valor, consumido uma vez por titulo.

    Consumir evita que dois pagamentos de valor igual apontem para o mesmo
    titulo, o que produziria historico duplicado e errado em um dos dois.
    """

    def __init__(self, titulos: list[TituloContasPagar]) -> None:
        self._por_valor: dict[int, list[TituloContasPagar]] = defaultdict(list)
        for t in titulos:
            self._por_valor[self._centavos(t.valor_pago)].append(t)
        self._usados: set[int] = set()

    @staticmethod
    def _centavos(valor: float) -> int:
        return round(valor * 100)

    def derivar(self, pagamento: Pagamento, nome_fornecedor: str = "") -> HistoricoDerivado:
        candidatos = [
            t
            for t in self._por_valor.get(self._centavos(pagamento.valor), [])
            if id(t) not in self._usados
        ]
        if not candidatos:
            return self._nao_derivado(pagamento)

        alvo = tokens_fornecedor(pagamento.favorecido_raw)
        pontuados = [
            (len(alvo & tokens_fornecedor(t.fornecedor_raw)), t) for t in candidatos
        ]
        melhor_pontuacao = max(p for p, _ in pontuados)
        # Sem nenhum token em comum, so o valor coincide. Isso nao sustenta um
        # historico: preferimos declarar nao derivado a inventar o fornecedor.
        if melhor_pontuacao == 0:
            return self._nao_derivado(pagamento)

        elegiveis = [t for p, t in pontuados if p == melhor_pontuacao]
        # Entre parcelas do mesmo contrato (valores identicos), a data decide.
        escolhido = min(elegiveis, key=lambda t: self._distancia(pagamento, t))
        if self._distancia(pagamento, escolhido) > JANELA_DIAS:
            return self._nao_derivado(pagamento)

        self._usados.add(id(escolhido))
        return HistoricoDerivado(
            texto=montar_texto(escolhido, nome_fornecedor or pagamento.favorecido_raw),
            titulo=escolhido,
            derivado=True,
        )

    @staticmethod
    def _distancia(pagamento: Pagamento, titulo: TituloContasPagar) -> int:
        if titulo.vencimento is None:
            return 10**6
        return abs((titulo.vencimento - pagamento.data).days)

    @staticmethod
    def _nao_derivado(pagamento: Pagamento) -> HistoricoDerivado:
        """Fallback: descricao bancaria ou favorecido, sempre com o warning.

        Nunca devolve string vazia - o contador precisa de algo legivel na coluna
        para decidir o que editar.
        """
        base = pagamento.descricao_banco or pagamento.tipo_pagamento or "Pagamento"
        nome = (pagamento.favorecido_raw or "").strip()
        texto = f"{PREFIXO} {base}"
        if nome:
            texto = f"{texto} - {nome.title()}"
        return HistoricoDerivado(texto=texto, titulo=None, derivado=False)
