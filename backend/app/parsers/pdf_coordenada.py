"""Extracao de PDF por baseline e sequencia de caracteres.

Tecnica validada pelo spike da Fase 2 (tools/spike_contas_pagar.py) e registrada
em ADR 0007. Serve aos dois PDFs que nao tem linhas de grade: o Contas a Pagar
(colunas que se sobrepoem em x) e o extrato de conta corrente Itau.

Por que nao extract_text() nem extract_words(): as colunas do Contas a Pagar se
sobrepoem fisicamente em x, entao nenhuma fronteira vertical as separa. A saida
vem com caracteres de duas colunas no mesmo token:

    DEYWISON BRUNO PEDROZA SILV2A0 7296305300403978238731/03/2026
                             ^^^^^^^ "SILVA" e "20260..." entrelacados

Duas propriedades do PDF gerado pelo Fortes resolvem isso:
  1. campos que colidem ficam em baselines diferentes (0,75pt de diferenca);
  2. cada campo e uma sequencia contigua no stream de caracteres, ancorada num x
     estavel, mesmo quando a ordem dos campos no stream esta embaralhada.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

# Precisao de agrupamento por baseline. 0,4pt separa as duas baselines de uma
# mesma linha logica (que distam 0,75pt) sem fundir linhas vizinhas (~11pt).
PRECISAO_BASELINE = 0.4

# Uma nova sequencia comeca quando o caractere seguinte nao encosta no anterior.
FOLGA_ENTRE_SEQUENCIAS = 3.0


@dataclass(frozen=True)
class Coluna:
    nome: str
    inicio: float
    limite: float
    alinhamento: str = "esq"  # 'esq' ancora em x0, 'dir' ancora em x1


@dataclass(frozen=True)
class Sequencia:
    texto: str
    x0: float
    x1: float


def sequencias(chars: list[dict]) -> list[Sequencia]:
    """Quebra caracteres de uma baseline em sequencias contiguas.

    Percorre em ordem de stream, nao de x: e isso que mantem cada campo inteiro
    quando o gerador do PDF escreve as colunas fora de ordem.
    """
    achadas: list[Sequencia] = []
    atual: list[dict] = []
    for c in chars:
        if atual and not (
            atual[-1]["x1"] - 0.5 <= c["x0"] <= atual[-1]["x1"] + FOLGA_ENTRE_SEQUENCIAS
        ):
            achadas.append(_fechar(atual))
            atual = []
        atual.append(c)
    if atual:
        achadas.append(_fechar(atual))
    return [s for s in achadas if s.texto]


def _fechar(chars: list[dict]) -> Sequencia:
    return Sequencia(
        texto="".join(c["text"] for c in chars).strip(),
        x0=chars[0]["x0"],
        x1=chars[-1]["x1"],
    )


def coluna_de(seq: Sequencia, colunas: list[Coluna]) -> str | None:
    for col in colunas:
        ref = seq.x0 if col.alinhamento == "esq" else seq.x1
        if col.inicio <= ref < col.limite:
            return col.nome
    return None


def linhas_por_baseline(
    pagina,
    colunas: list[Coluna],
    x_minimo_linha_completa: float,
    distancia_baseline_extra: float = 2.0,
    com_posicao: bool = False,
) -> list[dict[str, str]]:
    """Monta um registro por linha logica.

    Baselines que nao alcancam `x_minimo_linha_completa` tem apenas as colunas da
    esquerda: sao a parte de cima de uma linha logica e ficam pendentes ate a
    proxima baseline completa.

    Com `com_posicao`, cada registro ganha a chave `_top` com a coordenada y, o
    que permite ao chamador atribuir cabecalhos de grupo por posicao.
    """
    por_baseline: dict[int, list[dict]] = defaultdict(list)
    for c in pagina.chars:
        por_baseline[round(c["top"] / PRECISAO_BASELINE)].append(c)

    registros: list[dict[str, str]] = []
    pendentes: list[dict] = []
    baseline_pendente: int | None = None

    for chave in sorted(por_baseline):
        chars = por_baseline[chave]
        completa = any(c["x1"] >= x_minimo_linha_completa for c in chars)

        if not completa:
            distante = baseline_pendente is not None and (
                (chave - baseline_pendente) * PRECISAO_BASELINE > distancia_baseline_extra
            )
            if distante:
                pendentes = []
            pendentes += chars
            baseline_pendente = chave
            continue

        grupo = chars
        if baseline_pendente is not None and (
            (chave - baseline_pendente) * PRECISAO_BASELINE <= distancia_baseline_extra
        ):
            grupo = pendentes + chars
        pendentes, baseline_pendente = [], None

        celulas: dict[str, list[str]] = defaultdict(list)
        for seq in sequencias(grupo):
            nome = coluna_de(seq, colunas)
            if nome:
                celulas[nome].append(seq.texto)

        if celulas:
            registro = {
                col.nome: re.sub(r"\s+", " ", " ".join(celulas.get(col.nome, []))).strip()
                for col in colunas
            }
            if com_posicao:
                registro["_top"] = chave * PRECISAO_BASELINE
            registros.append(registro)
    return registros
