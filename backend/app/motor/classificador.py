"""Casamento De/Para: pagamento -> conta de debito.

Implementa a cascata do ADR 0002. A regra que governa tudo aqui: NUNCA casar
parcialmente em silencio. Sem regra clara, o lancamento vira pendencia.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum

from ..modelos import Fornecedor, Pagamento, RegraDePara
from ..normalizacao import normalizar_documento, normalizar_nome_fornecedor, tokens_fornecedor


class Casamento(StrEnum):
    DOCUMENTO_E_NOME = "DOCUMENTO_E_NOME"
    DOCUMENTO = "DOCUMENTO"
    NOME = "NOME"
    AMBIGUO = "AMBIGUO"
    NENHUM = "NENHUM"


@dataclass
class Resultado:
    forma: Casamento
    regra: RegraDePara | None = None
    fornecedor: Fornecedor | None = None
    candidatas: list[RegraDePara] | None = None


class Classificador:
    """Indice de fornecedores e regras, montado uma vez por reprocessamento."""

    def __init__(self, fornecedores: list[Fornecedor], regras: list[RegraDePara]) -> None:
        self._por_id = {f.id: f for f in fornecedores}
        self._por_documento: dict[str, list[Fornecedor]] = defaultdict(list)
        self._por_chave_nome: dict[str, list[Fornecedor]] = defaultdict(list)
        for f in fornecedores:
            if f.documento:
                self._por_documento[f.documento].append(f)
            self._por_chave_nome[f.chave_nome].append(f)

        # Regras inativas ficam no indice de "todas" para explicar a pendencia,
        # mas nunca classificam. E assim que as 13 regras AMBIGUO_CONTA produzem
        # REGRA_AMBIGUA em vez de conta arbitraria (ADR 0003).
        self._ativas: dict[int, list[RegraDePara]] = defaultdict(list)
        self._todas: dict[int, list[RegraDePara]] = defaultdict(list)
        for r in regras:
            self._todas[r.fornecedor_id].append(r)
            if r.ativo:
                self._ativas[r.fornecedor_id].append(r)

    def classificar(self, pagamento: Pagamento) -> Resultado:
        documento = normalizar_documento(pagamento.documento_raw)
        chave = normalizar_nome_fornecedor(pagamento.favorecido_raw)

        # Nivel 1: documento e nome batem.
        if documento:
            exatos = [f for f in self._por_documento.get(documento, []) if f.chave_nome == chave]
            if len(exatos) == 1:
                return self._resolver(exatos[0], Casamento.DOCUMENTO_E_NOME)

            candidatos = self._por_documento.get(documento, [])
            # Nivel 2: documento unico.
            if len(candidatos) == 1:
                return self._resolver(candidatos[0], Casamento.DOCUMENTO)
            # Nivel 3: documento compartilhado - desempata pelo nome.
            if len(candidatos) > 1:
                melhor = self._melhor_por_nome(candidatos, pagamento.favorecido_raw)
                if melhor:
                    return self._resolver(melhor, Casamento.DOCUMENTO_E_NOME)
                return Resultado(forma=Casamento.AMBIGUO)

        # Nivel 4: sem documento na origem (concessionarias).
        por_nome = self._por_chave_nome.get(chave, [])
        if len(por_nome) == 1:
            return self._resolver(por_nome[0], Casamento.NOME)
        if len(por_nome) > 1:
            melhor = self._melhor_por_nome(por_nome, pagamento.favorecido_raw)
            if melhor:
                return self._resolver(melhor, Casamento.NOME)
            return Resultado(forma=Casamento.AMBIGUO)

        return Resultado(forma=Casamento.NENHUM)

    def _melhor_por_nome(
        self, candidatos: list[Fornecedor], favorecido: str
    ) -> Fornecedor | None:
        """Desempate por interseccao de tokens, exigindo vencedor unico."""
        alvo = tokens_fornecedor(favorecido)
        if not alvo:
            return None
        pontuados = [(len(alvo & tokens_fornecedor(f.nome_canonico)), f) for f in candidatos]
        melhor = max(p for p, _ in pontuados)
        if melhor == 0:
            return None
        empatados = [f for p, f in pontuados if p == melhor]
        return empatados[0] if len(empatados) == 1 else None

    def _resolver(self, fornecedor: Fornecedor, forma: Casamento) -> Resultado:
        ativas = self._ativas.get(fornecedor.id, [])
        if len(ativas) == 1:
            return Resultado(forma=forma, regra=ativas[0], fornecedor=fornecedor)
        # Mais de uma regra ativa, ou nenhuma ativa havendo inativas: em ambos os
        # casos existe fornecedor identificado mas nao ha conta unica a aplicar.
        todas = self._todas.get(fornecedor.id, [])
        if todas:
            return Resultado(
                forma=Casamento.AMBIGUO, fornecedor=fornecedor, candidatas=todas
            )
        return Resultado(forma=Casamento.NENHUM, fornecedor=fornecedor)
