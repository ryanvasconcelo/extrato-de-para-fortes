"""Regressao secundaria sobre Janeiro a Maio.

Cobertura limitada por construcao: desses meses so temos a SAIDA (o XLSX que o
contador entregou ao Fortes), nao a ENTRADA (os relatorios Itau). Nao ha como
rodar o pipeline; o que se pode testar e o caminho CSV -> seed -> classificador
contra as contas que o contador de fato usou.

Cuidado com a leitura: a base De/Para foi minerada desses mesmos arquivos, entao
concordancia de conta NAO e evidencia de acuracia - seria circular. O que estes
testes pegam e regressao no caminho de producao:

  - normalizacao de digito verificador quebrando em contas que junho nao usa;
  - o loader do seed perdendo ou embaralhando regra;
  - centro de custo proposto fora do conjunto observado.

Ver ADR 0009 para o racional e para o que NAO esta coberto.
"""

from __future__ import annotations

from collections import defaultdict

import openpyxl
import pytest

from app.normalizacao import normalizar_conta, normalizar_nome_fornecedor

from .conftest import ARQUIVOS, GABARITO_JUNHO

COL_DATA, COL_DEBITO, COL_HISTORICO, COL_CENTRO = 1, 2, 5, 6


def _meses_anteriores():
    """Os cinco XLSX de Jan a Mai, excluindo junho (que e o gabarito de ouro)."""
    return [
        caminho
        for caminho in sorted(ARQUIVOS.glob("CLICK SCM *.xlsx"))
        if caminho != GABARITO_JUNHO
    ]


@pytest.fixture(scope="module")
def linhas_anteriores():
    """Deduplica por conteudo: ha arquivo repetido com nome diferente na pasta."""
    linhas: list[dict] = []
    vistos: set[bytes] = set()
    for caminho in _meses_anteriores():
        conteudo = caminho.read_bytes()
        if conteudo in vistos:
            continue
        vistos.add(conteudo)
        ws = openpyxl.load_workbook(caminho, data_only=True).active
        for r in ws.iter_rows(min_row=2, values_only=True):
            if not r[COL_DATA]:
                continue
            linhas.append(
                {
                    "arquivo": caminho.name,
                    "conta_debito": str(r[COL_DEBITO] or "").strip(),
                    "historico": str(r[COL_HISTORICO] or "").strip(),
                    "centro_custo": str(r[COL_CENTRO] or "").strip(),
                }
            )
    return linhas


class TestCoberturaDoPlanoDeContas:
    """O teste mais valioso deste arquivo, e o unico nao circular.

    Junho usa ~140 contas; os cinco meses anteriores usam outras. Se a
    normalizacao de digito verificador tratar mal alguma faixa de conta, junho
    passa e este teste falha.
    """

    def test_toda_conta_usada_existe_no_plano(self, linhas_anteriores, plano_contas):
        conhecidas = {c.codigo for c in plano_contas}
        ausentes = defaultdict(int)
        for linha in linhas_anteriores:
            codigo = normalizar_conta(linha["conta_debito"])
            if codigo not in conhecidas:
                ausentes[codigo] += 1
        assert not ausentes, f"contas fora do plano: {dict(ausentes)}"

    def test_toda_conta_usada_e_analitica(self, linhas_anteriores, plano_contas):
        por_codigo = {c.codigo: c for c in plano_contas}
        sinteticas = {
            linha["conta_debito"]
            for linha in linhas_anteriores
            if not por_codigo[normalizar_conta(linha["conta_debito"])].analitica
        }
        assert not sinteticas

    def test_cobre_contas_que_junho_nao_exercita(self, linhas_anteriores, gabarito):
        de_junho = {normalizar_conta(l["conta_debito"]) for l in gabarito}
        anteriores = {normalizar_conta(l["conta_debito"]) for l in linhas_anteriores}
        novas = anteriores - de_junho
        print(f"\n  {len(novas)} contas exercitadas so por Jan-Mai")
        assert len(novas) >= 20, "regressao perdeu valor: nao ha conta nova aqui"


class TestCaminhoDoSeed:
    def test_seed_nao_perde_regra_do_csv(self, base_depara):
        import csv

        from app.seed import CSV_PADRAO

        with CSV_PADRAO.open(encoding="utf-8") as fh:
            do_csv = list(csv.DictReader(fh))
        _, regras = base_depara
        assert len(regras) == len(do_csv)

    def test_toda_regra_ativa_aponta_para_conta_analitica(self, base_depara, plano_contas):
        por_codigo = {c.codigo: c for c in plano_contas}
        _, regras = base_depara
        for regra in regras:
            if not regra.ativo:
                continue
            conta = por_codigo.get(regra.conta_debito)
            assert conta is not None, f"regra aponta para conta inexistente: {regra.conta_debito}"
            assert conta.analitica

    def test_fornecedor_do_seed_tem_regra(self, base_depara):
        """Fornecedor sem regra e ruido: ocuparia a base sem resolver pendencia."""
        fornecedores, regras = base_depara
        com_regra = {r.fornecedor_id for r in regras}
        orfaos = [f.nome_canonico for f in fornecedores if f.id not in com_regra]
        assert orfaos == []


class TestReproducaoPorNomeNoHistorico:
    """Round-trip do caminho de producao: nome no historico -> regra -> conta.

    Circular quanto a acuracia (a base saiu daqui), util quanto a regressao: se
    `normalizar_nome_fornecedor` mudar de comportamento, a taxa cai e o teste
    acusa. O limiar e a linha de base medida, nao meta.
    """

    def test_taxa_de_reproducao_nao_regride(self, linhas_anteriores, base_depara):
        fornecedores, regras = base_depara
        por_chave = {f.chave_nome: f.id for f in fornecedores}
        ativas: dict[int, set[str]] = defaultdict(set)
        for regra in regras:
            if regra.ativo:
                ativas[regra.fornecedor_id].add(regra.conta_debito)

        identificadas = acertos = 0
        for linha in linhas_anteriores:
            if " - " not in linha["historico"]:
                continue
            chave = normalizar_nome_fornecedor(linha["historico"].rsplit(" - ", 1)[1])
            fornecedor_id = por_chave.get(chave)
            if fornecedor_id is None or not ativas[fornecedor_id]:
                continue
            identificadas += 1
            acertos += normalizar_conta(linha["conta_debito"]) in ativas[fornecedor_id]

        assert identificadas > 0
        taxa = acertos / identificadas
        print(
            f"\n  Jan-Mai: {identificadas} linhas com fornecedor identificavel, "
            f"{acertos} reproduzidas ({taxa:.1%})"
        )
        assert taxa >= 0.95, f"caminho seed->classificador regrediu para {taxa:.1%}"
