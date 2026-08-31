"""Orquestracao: pagamentos + titulos + regras -> lancamentos validados.

Reprocessar e sempre recalcular a partir dos fatos importados. Nenhum estado
intermediario e preservado, exceto as edicoes manuais que o chamador pedir para
respeitar (RF-02.9).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..modelos import (
    Confianca,
    ContaBancaria,
    Fornecedor,
    Lancamento,
    Ocorrencia,
    Pagamento,
    PlanoContas,
    RegraDePara,
    Severidade,
    StatusLancamento,
    StatusLote,
    TituloContasPagar,
)
from .classificador import Casamento, Classificador
from .historico import DerivadorHistorico
from .validador import Achado, Codigo, Validador, tem_blocker


@dataclass
class LancamentoProcessado:
    lancamento: Lancamento
    achados: list[Achado] = field(default_factory=list)


@dataclass
class Resumo:
    total: int = 0
    automaticos: int = 0
    pendentes: int = 0
    manuais: int = 0
    historico_derivado: int = 0
    blockers: int = 0
    warnings: int = 0
    valor_total: float = 0.0

    @property
    def status_lote(self) -> StatusLote:
        if self.blockers:
            return StatusLote.BLOQUEADO
        return StatusLote.PRONTO if self.total else StatusLote.RASCUNHO


class Processador:
    def __init__(
        self,
        plano: list[PlanoContas],
        fornecedores: list[Fornecedor],
        regras: list[RegraDePara],
        conta_bancaria: ContaBancaria | None,
    ) -> None:
        self._classificador = Classificador(fornecedores, regras)
        self._validador = Validador(plano)
        self._conta_credito = conta_bancaria.conta_contabil if conta_bancaria else ""

    def processar(
        self,
        lote_id: int,
        pagamentos: list[Pagamento],
        titulos: list[TituloContasPagar],
        edicoes: dict[int, Lancamento] | None = None,
    ) -> tuple[list[LancamentoProcessado], Resumo]:
        derivador = DerivadorHistorico(titulos)
        edicoes = edicoes or {}
        saida: list[LancamentoProcessado] = []
        resumo = Resumo()

        # Data crescente para que parcelas sejam consumidas na ordem em que foram
        # pagas; o derivador consome titulo, entao a ordem importa.
        for pagamento in sorted(pagamentos, key=lambda p: (p.data, p.id or 0)):
            saida.append(self._um(lote_id, pagamento, derivador, edicoes))

        for item in saida:
            resumo.total += 1
            resumo.valor_total += item.lancamento.valor
            resumo.blockers += sum(
                1 for a in item.achados if a.severidade is Severidade.BLOCKER
            )
            resumo.warnings += sum(
                1 for a in item.achados if a.severidade is Severidade.WARNING
            )
            if item.lancamento.status is StatusLancamento.AUTO:
                resumo.automaticos += 1
            elif item.lancamento.status is StatusLancamento.MANUAL:
                resumo.manuais += 1
            else:
                resumo.pendentes += 1
            if item.lancamento.titulo_id is not None or not any(
                a.codigo == Codigo.HISTORICO_NAO_DERIVADO for a in item.achados
            ):
                resumo.historico_derivado += 1

        return saida, resumo

    def _um(
        self,
        lote_id: int,
        pagamento: Pagamento,
        derivador: DerivadorHistorico,
        edicoes: dict[int, Lancamento],
    ) -> LancamentoProcessado:
        resultado = self._classificador.classificar(pagamento)
        nome = resultado.fornecedor.nome_canonico if resultado.fornecedor else ""
        historico = derivador.derivar(pagamento, nome)

        lancamento = Lancamento(
            lote_id=lote_id,
            pagamento_id=pagamento.id or 0,
            titulo_id=historico.titulo.id if historico.titulo else None,
            regra_id=resultado.regra.id if resultado.regra else None,
            conta_credito=self._conta_credito,
            valor=pagamento.valor,
            historico=historico.texto,
        )

        achados: list[Achado] = []

        if resultado.regra is not None:
            lancamento.conta_debito = resultado.regra.conta_debito
            lancamento.centro_custo = resultado.regra.centro_custo_sugerido
            lancamento.status = StatusLancamento.AUTO
            if resultado.regra.confianca is Confianca.MEDIA:
                achados.append(
                    Achado(
                        Severidade.WARNING,
                        Codigo.REGRA_CONFIANCA_MEDIA,
                        f"Regra de {nome} foi minerada com base em 1-2 meses.",
                    )
                )
        elif resultado.forma is Casamento.AMBIGUO:
            contas = sorted({r.conta_debito for r in (resultado.candidatas or [])})
            achados.append(
                Achado(
                    Severidade.BLOCKER,
                    Codigo.REGRA_AMBIGUA,
                    f"{nome or pagamento.favorecido_raw} tem mais de uma conta possivel: "
                    f"{', '.join(contas) or 'indeterminada'}.",
                )
            )

        # Edicao manual sempre vence o resultado automatico (RF-05.2).
        edicao = edicoes.get(pagamento.id or -1)
        if edicao is not None:
            lancamento.conta_debito = edicao.conta_debito or lancamento.conta_debito
            lancamento.conta_credito = edicao.conta_credito or lancamento.conta_credito
            lancamento.centro_custo = edicao.centro_custo or lancamento.centro_custo
            lancamento.historico = edicao.historico or lancamento.historico
            if edicao.valor is not None:
                lancamento.valor = edicao.valor
            lancamento.status = StatusLancamento.MANUAL
            lancamento.editado_por = edicao.editado_por
            lancamento.editado_em = edicao.editado_em
            achados = [a for a in achados if a.codigo != Codigo.REGRA_AMBIGUA]

        if not historico.derivado:
            achados.append(
                Achado(
                    Severidade.WARNING,
                    Codigo.HISTORICO_NAO_DERIVADO,
                    "Nenhum titulo do Contas a Pagar corresponde a este pagamento.",
                )
            )
        if not pagamento.documento_raw:
            achados.append(
                Achado(
                    Severidade.WARNING,
                    Codigo.FORNECEDOR_SEM_DOCUMENTO,
                    "Origem nao informou CPF/CNPJ; casamento feito por nome.",
                )
            )

        achados += self._validador.validar(lancamento)

        # REGRA_AMBIGUA e a causa; CONTA_DEBITO_AUSENTE e o efeito. Manter os dois
        # faz a tela de pendencias mostrar dois motivos onde ha uma decisao, e o
        # motivo acionavel e o primeiro.
        if any(a.codigo == Codigo.REGRA_AMBIGUA for a in achados):
            achados = [a for a in achados if a.codigo != Codigo.CONTA_DEBITO_AUSENTE]

        if tem_blocker(achados) and lancamento.status is not StatusLancamento.MANUAL:
            lancamento.status = StatusLancamento.PENDENTE

        return LancamentoProcessado(lancamento=lancamento, achados=achados)


def para_ocorrencias(lancamento_id: int, achados: list[Achado]) -> list[Ocorrencia]:
    return [
        Ocorrencia(
            lancamento_id=lancamento_id,
            severidade=a.severidade,
            codigo=a.codigo,
            mensagem=a.mensagem,
        )
        for a in achados
    ]
