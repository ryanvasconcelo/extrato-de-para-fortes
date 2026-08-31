#!/usr/bin/env python3
"""SPIKE — extracao por coordenada do PDF 'Contas a Pagar - Pagas' do Fortes.

Maior risco tecnico do projeto (docs/02-analise-arquivos-cliente.md secao 7.1).
Este script existe para provar que a extracao e viavel antes de a Fase 3 escrever
o parser de producao. Conclusoes em docs/adr/0007-estrategia-extracao-pdf.md.

O PROBLEMA
    extract_text() e extract_words() devolvem colunas colididas:

        DEYWISON BRUNO PEDROZA SILV2A0 7296305300403978238731/03/2026 NFS-E 41
                                 ^^^^^^^ "SILVA" e "20260..." no mesmo token

    A causa nao e tolerancia de espacamento: o campo Fornecedor transborda sua
    coluna e invade a faixa x da coluna 'Conta a Pag.'. Nenhuma fronteira vertical
    separa os dois.

A SOLUCAO (validada por este spike)
    Duas observacoes sobre como o Fortes gera o PDF:

    1. O Fornecedor e escrito em uma BASELINE PROPRIA (top=130.91) enquanto todos
       os outros campos da mesma linha logica ficam 0,75pt abaixo (top=131.66).
       Agrupar por top exato ja separa o campo que colide.

    2. Cada campo e uma SEQUENCIA CONTIGUA no stream de caracteres, ancorada num
       x estavel - mesmo que a ordem dos campos no stream seja embaralhada
       (conta_pag e escrito por ultimo, depois de total_pago).

    Logo: agrupar por top, quebrar em sequencias, e atribuir cada sequencia a uma
    coluna pelo seu x. Nunca fatiar string por posicao.

Uso:
    python3 tools/spike_contas_pagar.py [--pdf CAMINHO] [--paginas N] [--ancoras]
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import pdfplumber

PDF_PADRAO = (
    "arquivos-clickip/clickIP/"
    "Contas a Pagar - Pagas - Click Ip SCM 01-01-2026 a 30-06-2026.pdf"
)

# Ancoras em x medidas no proprio PDF (ver --ancoras para reproduzir).
# Campos de texto sao alinhados a esquerda e ancoram em x0; os monetarios sao
# alinhados a direita e ancoram em x1. 'limite' e a fronteira superior da faixa.
COLUNAS: list[tuple[str, float, float, str]] = [
    # nome,          inicio, limite,  alinhamento
    ("fornecedor",     30.0,  166.0, "esq"),
    ("conta_pag",     166.0,  222.0, "esq"),
    ("vencimento",    222.0,  266.0, "esq"),
    ("tipo_doc",      266.0,  337.0, "esq"),
    ("titulo",        337.0,  440.0, "esq"),
    ("doc_entrada",   440.0,  496.0, "esq"),
    ("valor_titulo",  496.0,  553.0, "dir"),
    ("valor_pago",    553.0,  610.0, "dir"),
    ("desconto",      610.0,  655.0, "dir"),
    ("juros",         655.0,  700.0, "dir"),
    ("total_pago",    700.0,  792.0, "dir"),
]

# O Fornecedor fica ~0,75pt acima dos demais campos da mesma linha logica.
# 0,4 separa as duas baselines sem fundir linhas vizinhas (que distam ~11pt).
PRECISAO_BASELINE = 0.4

# Uma nova sequencia comeca quando o caractere seguinte nao encosta no anterior.
FOLGA_ENTRE_SEQUENCIAS = 3.0

# Distancia maxima entre a baseline do Fornecedor e a dos outros campos.
DISTANCIA_BASELINE_FORNECEDOR = 2.0


def sequencias(chars: list[dict]) -> list[dict]:
    """Quebra os caracteres de uma baseline em sequencias contiguas.

    Percorre em ordem de stream, nao de x: e isso que mantem cada campo inteiro
    mesmo quando o Fortes escreve as colunas fora de ordem.
    """
    achadas: list[dict] = []
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
    return achadas


def _fechar(chars: list[dict]) -> dict:
    return {
        "texto": "".join(c["text"] for c in chars).strip(),
        "x0": chars[0]["x0"],
        "x1": chars[-1]["x1"],
    }


def coluna_de(seq: dict) -> str | None:
    for nome, inicio, limite, alinhamento in COLUNAS:
        ref = seq["x0"] if alinhamento == "esq" else seq["x1"]
        if inicio <= ref < limite:
            return nome
    return None


# Uma baseline que nao alcanca esta coordenada tem apenas as colunas da esquerda,
# ou seja, e a linha do Fornecedor esperando os campos que vem logo abaixo.
X_MINIMO_LINHA_COMPLETA = 400.0


def extrair_pagina(pagina) -> list[dict[str, str]]:
    """Monta um registro por linha logica da pagina.

    O Fornecedor fica numa baseline propria, acima da dos outros campos. Como as
    duas precisam virar um registro so, as baselines incompletas ficam pendentes
    e sao anexadas a proxima baseline completa.
    """
    por_baseline: dict[int, list[dict]] = defaultdict(list)
    for c in pagina.chars:
        por_baseline[round(c["top"] / PRECISAO_BASELINE)].append(c)

    registros: list[dict[str, str]] = []
    pendentes: list[dict] = []
    baseline_pendente: int | None = None

    for chave in sorted(por_baseline):
        chars = por_baseline[chave]
        completa = any(c["x1"] >= X_MINIMO_LINHA_COMPLETA for c in chars)

        if not completa:
            # Descarta o pendente anterior se a distancia mostra que eram linhas
            # logicas diferentes (cabecalho, 'Despesa:', rodape).
            if baseline_pendente is not None and (
                (chave - baseline_pendente) * PRECISAO_BASELINE
                > DISTANCIA_BASELINE_FORNECEDOR
            ):
                pendentes = []
            pendentes += chars
            baseline_pendente = chave
            continue

        grupo = chars
        if baseline_pendente is not None and (
            (chave - baseline_pendente) * PRECISAO_BASELINE
            <= DISTANCIA_BASELINE_FORNECEDOR
        ):
            grupo = pendentes + chars
        pendentes = []
        baseline_pendente = None

        celulas: dict[str, list[str]] = defaultdict(list)
        for seq in sequencias(grupo):
            nome = coluna_de(seq)
            if nome and seq["texto"]:
                celulas[nome].append(seq["texto"])

        if celulas:
            registros.append(
                {
                    nome: re.sub(r"\s+", " ", " ".join(celulas.get(nome, []))).strip()
                    for nome, _, _, _ in COLUNAS
                }
            )
    return registros


def eh_registro_valido(r: dict[str, str]) -> bool:
    return bool(
        r["fornecedor"]
        and re.fullmatch(r"\d{2}/\d{2}/\d{4}", r["vencimento"])
        and re.fullmatch(r"[\d.]+,\d{2}", r["valor_pago"])
    )


def separar_documento(fornecedor: str) -> tuple[str, str]:
    """O campo Fornecedor traz 'NOME CPF/CNPJ' concatenado.

    Descoberta deste spike: o Contas a Pagar carrega o documento do fornecedor,
    o que da uma chave canonica de join com os relatorios Itau (ADR 0002).
    """
    m = re.match(r"^(.*?)\s*(\d{11}|\d{14})$", fornecedor)
    return (m.group(1).strip(), m.group(2)) if m else (fornecedor, "")


def moeda(valor: str) -> float:
    return float(valor.replace(".", "").replace(",", "."))


def relatar_ancoras(pdf, n_paginas: int) -> None:
    """Reproduz as ancoras da tabela COLUNAS a partir do PDF."""
    inicios: dict[int, int] = defaultdict(int)
    fins: dict[int, int] = defaultdict(int)
    for pagina in pdf.pages[:n_paginas]:
        por_baseline: dict[float, list[dict]] = defaultdict(list)
        for c in pagina.chars:
            por_baseline[round(c["top"] / PRECISAO_BASELINE)].append(c)
        for chars in por_baseline.values():
            for seq in sequencias(chars):
                inicios[round(seq["x0"])] += 1
                fins[round(seq["x1"])] += 1
    print("Ancoras x0 mais frequentes (colunas alinhadas a esquerda):")
    for x, n in sorted(inicios.items(), key=lambda kv: -kv[1])[:14]:
        print(f"  x0={x:4d}  {n:5d} sequencias")
    print("\nAncoras x1 mais frequentes (colunas alinhadas a direita):")
    for x, n in sorted(fins.items(), key=lambda kv: -kv[1])[:14]:
        print(f"  x1={x:4d}  {n:5d} sequencias")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pdf", default=PDF_PADRAO, type=Path)
    p.add_argument("--paginas", type=int, default=0, help="0 = todas")
    p.add_argument("--ancoras", action="store_true", help="so reporta as ancoras x")
    args = p.parse_args()

    if not args.pdf.exists():
        sys.exit(f"erro: nao encontrei {args.pdf}")

    with pdfplumber.open(args.pdf) as pdf:
        if args.ancoras:
            relatar_ancoras(pdf, args.paginas or len(pdf.pages))
            return
        paginas = pdf.pages[: args.paginas] if args.paginas else pdf.pages
        total_paginas = len(paginas)
        validos: list[dict] = []
        descartados: list[dict] = []
        for pagina in paginas:
            for r in extrair_pagina(pagina):
                (validos if eh_registro_valido(r) else descartados).append(r)

    print(f"Paginas processadas: {total_paginas}")
    print(f"Registros validos:   {len(validos)}")
    print(f"Linhas descartadas:  {len(descartados)} (cabecalho, 'Despesa:', totais)")

    if not validos:
        sys.exit("\nFALHOU: nenhum registro extraido.")

    com_doc = 0
    for r in validos:
        nome, doc = separar_documento(r["fornecedor"])
        r["fornecedor_nome"], r["fornecedor_doc"] = nome, doc
        com_doc += bool(doc)

    tipos: dict[str, int] = defaultdict(int)
    for r in validos:
        tipos[r["tipo_doc"] or "(vazio)"] += 1

    com_titulo = sum(1 for r in validos if r["titulo"])
    soma = sum(moeda(r["valor_pago"]) for r in validos)
    coerentes = sum(
        1 for r in validos if r["total_pago"] and abs(moeda(r["total_pago"]) - moeda(r["valor_pago"])) < 0.011
    )

    print(f"\nCom numero de titulo:     {com_titulo:5d}/{len(validos)} "
          f"({com_titulo * 100 // len(validos)}%)")
    print(f"Com CPF/CNPJ no campo:    {com_doc:5d}/{len(validos)} "
          f"({com_doc * 100 // len(validos)}%)")
    print(f"total_pago == valor_pago: {coerentes:5d}/{len(validos)} "
          f"({coerentes * 100 // len(validos)}%)  <- checagem de integridade")
    print(f"Soma de Valor Pago:       R$ {soma:,.2f}")
    print(f"\nTipos de documento ({len(tipos)}):")
    for t, n in sorted(tipos.items(), key=lambda kv: -kv[1])[:12]:
        print(f"  {n:5d}  {t}")

    print("\n--- as linhas que colidiam em extract_text() ---")
    for r in validos:
        if "DEYWISON" in r["fornecedor"] or "ENTULHO" in r["fornecedor"]:
            print(f"  nome={r['fornecedor_nome']!r} doc={r['fornecedor_doc']!r}")
            print(f"  conta_pag={r['conta_pag']!r} venc={r['vencimento']!r} "
                  f"tipo={r['tipo_doc']!r} titulo={r['titulo']!r} pago={r['valor_pago']!r}")

    print("\n--- 6 primeiros registros ---")
    for r in validos[:6]:
        print(f"  {r['fornecedor_nome'][:26]:26s} {r['fornecedor_doc']:>14s} | "
              f"{r['vencimento']} | {r['tipo_doc'][:9]:9s} | {r['titulo'][:14]:14s} | "
              f"{r['valor_pago']:>12s}")


if __name__ == "__main__":
    main()
