"""Testes dos parsers contra os arquivos reais.

Os numeros aqui sao medicoes, nao expectativas arbitrarias. Se um deles mudar,
ou o arquivo mudou ou o parser regrediu - as duas coisas exigem investigacao.
"""

from __future__ import annotations

from app.normalizacao import (
    conta_e_analitica,
    moeda_para_decimal,
    normalizar_conta,
    normalizar_documento,
    normalizar_nome_fornecedor,
)
from app.parsers import itau
from app.modelos import TipoArquivo

from .conftest import CONTAS_PAGAR, ITAU_EXTRATO, ITAU_PAGAMENTOS


class TestNormalizacao:
    def test_remove_digito_verificador(self):
        """A armadilha do ADR 0006: sem isso a validacao falha em 100% dos casos."""
        assert normalizar_conta("1.01.01.02.01.0003-4") == "1.01.01.02.01.0003"
        assert normalizar_conta("1.01.01.02.01.0003") == "1.01.01.02.01.0003"

    def test_conta_analitica_tem_seis_niveis(self):
        assert conta_e_analitica("1.01.01.02.01.0003-4")
        assert not conta_e_analitica("1.01.01.02.01")

    def test_aceita_cpf_e_cnpj(self):
        assert normalizar_documento("19.402.859/0001-55") == "19402859000155"
        assert normalizar_documento("767.696.822-49") == "76769682249"

    def test_rejeita_documento_de_tamanho_invalido(self):
        assert normalizar_documento("123") == ""
        assert normalizar_documento("") == ""

    def test_sufixo_societario_nao_cria_fornecedor_duplicado(self):
        assert normalizar_nome_fornecedor("GRUPO MULTI S.A") == normalizar_nome_fornecedor(
            "GRUPO MULTI SA"
        )

    def test_truncamento_em_30_caracteres_colide_de_proposito(self):
        assert normalizar_nome_fornecedor(
            "EQUATORIAL PARA DISTRIBUIDORA"
        ) == normalizar_nome_fornecedor("EQUATORIAL PARA DISTRIBUIDORA DE ENERGIA S.A.")

    def test_valor_negativo_do_extrato_vira_positivo(self):
        assert moeda_para_decimal("-85.000,00") == 85000.0
        assert moeda_para_decimal("1.621,00") == 1621.0


class TestDeteccaoDeLayout:
    def test_reconhece_os_tres_pdfs(self):
        """Os dois relatorios Itau sao relatorios diferentes (analise secao 2)."""
        assert itau.detectar_tipo(ITAU_PAGAMENTOS) is TipoArquivo.ITAU_PAGAMENTOS
        assert itau.detectar_tipo(ITAU_EXTRATO) is TipoArquivo.ITAU_EXTRATO
        assert itau.detectar_tipo(CONTAS_PAGAR) is TipoArquivo.CONTAS_PAGAR


class TestPlanoContas:
    def test_contagens(self, plano_contas):
        assert sum(1 for c in plano_contas if c.analitica) == 1516

    def test_conta_do_itau_existe_sem_digito_verificador(self, plano_contas):
        """A conta de credito do arquivo Fortes precisa ser encontravel."""
        contas = {c.codigo: c for c in plano_contas}
        assert "1.01.01.02.01.0003" in contas
        assert contas["1.01.01.02.01.0003"].codigo_dv == "1.01.01.02.01.0003-4"

    def test_base_bancos_derivada_do_plano(self, base_bancos):
        assert len(base_bancos) == 5

    def test_conta_itau_bate_com_o_cabecalho_do_relatorio(self, conta_itau):
        assert conta_itau.agencia == "1557"
        assert conta_itau.conta_contabil == "1.01.01.02.01.0003"


class TestPagamentosItau:
    def test_junho_tem_exatamente_as_439_linhas_do_gabarito(self, pagamentos_junho, gabarito):
        """261 do relatorio de pagamentos + 178 do extrato = 439."""
        assert len(pagamentos_junho) == len(gabarito) == 439

    def test_soma_dos_valores_bate_com_o_gabarito(self, pagamentos_junho, gabarito):
        nosso = round(sum(p.valor for p in pagamentos_junho), 2)
        deles = round(sum(l["valor"] for l in gabarito), 2)
        assert abs(nosso - deles) < 0.02, f"nosso={nosso} gabarito={deles}"

    def test_todos_tem_favorecido(self, pagamentos_junho):
        """O extrato quebra a razao social em varias linhas; remontar e obrigatorio."""
        assert [p for p in pagamentos_junho if not p.favorecido_raw] == []

    def test_maioria_tem_documento(self, pagamentos_junho):
        com_documento = sum(1 for p in pagamentos_junho if p.documento_raw)
        assert com_documento / len(pagamentos_junho) > 0.90

    def test_valores_sempre_positivos(self, pagamentos_junho):
        assert all(p.valor > 0 for p in pagamentos_junho)


class TestContasPagar:
    def test_extrai_os_titulos_das_59_paginas(self, titulos):
        """Spike da Fase 2 (ADR 0007): 2.060 titulos."""
        assert len(titulos) == 2060

    def test_quase_todos_tem_numero_de_titulo(self, titulos):
        com_numero = sum(1 for t in titulos if t.numero_titulo)
        assert com_numero / len(titulos) > 0.95

    def test_integridade_total_pago_igual_valor_pago(self, titulos):
        """Invariante barato que detecta regressao de parsing por coordenada."""
        coerentes = sum(1 for t in titulos if abs(t.total_pago - t.valor_pago) < 0.011)
        assert coerentes / len(titulos) > 0.97

    def test_colunas_que_colidiam_saem_separadas(self, titulos):
        """A linha que provava o problema em extract_text()."""
        alvo = next(t for t in titulos if "DEYWISON" in t.fornecedor_raw)
        assert alvo.fornecedor_raw == "DEYWISON BRUNO PEDROZA SILVA"
        assert alvo.conta_pag == "20260300983"
        assert alvo.tipo_doc == "NFS-E"
        assert alvo.numero_titulo == "41"
        assert alvo.valor_pago == 350.0

    def test_despesa_e_atribuida_ao_titulo(self, titulos):
        com_despesa = sum(1 for t in titulos if t.despesa_codigo)
        assert com_despesa / len(titulos) > 0.95
