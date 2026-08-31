"""API FastAPI. O backend e dono de todo parsing e de toda decisao contabil.

O frontend nunca parseia arquivo nem escolhe conta (ADR 0001).
"""

from __future__ import annotations

import hashlib
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlmodel import Session, delete, select

from . import autenticacao, export_fortes
from .banco import criar_tabelas, engine, obter_sessao, semear
from .modelos import (
    ArquivoImportado,
    Confianca,
    ContaBancaria,
    Fornecedor,
    Lancamento,
    LoteImportacao,
    Ocorrencia,
    OrigemRegra,
    Pagamento,
    PlanoContas,
    RegraDePara,
    Severidade,
    StatusLancamento,
    StatusLote,
    TipoArquivo,
    TituloContasPagar,
)
from .motor.processador import Processador, para_ocorrencias
from .motor.validador import Codigo, Validador
from .normalizacao import normalizar_conta, normalizar_nome_fornecedor
from .parsers import contas_pagar, itau

@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    criar_tabelas()
    with Session(engine) as sessao:
        semear(sessao)
    yield


app = FastAPI(title="Extrato → De/Para → FortesERP", version="0.1.0", lifespan=ciclo_de_vida)
autenticacao.instalar(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- contratos


class ResumoLote(BaseModel):
    id: int
    competencia: str
    status: str
    total: int
    automaticos: int
    pendentes: int
    manuais: int
    historico_derivado: int
    blockers: int
    warnings: int
    valor_total: float


class LancamentoOut(BaseModel):
    id: int
    data: str
    favorecido: str
    documento: str
    filial: str
    conta_debito: str
    conta_debito_descricao: str
    conta_credito: str
    valor: float
    historico: str
    centro_custo: str
    status: str
    blockers: list[str]
    warnings: list[str]


class EdicaoLancamento(BaseModel):
    conta_debito: str | None = None
    conta_credito: str | None = None
    centro_custo: str | None = None
    historico: str | None = None
    valor: float | None = None
    editado_por: str = "contador"
    criar_regra: bool = False


class NovaRegra(BaseModel):
    fornecedor_nome: str
    documento: str = ""
    conta_debito: str
    centro_custo: str = "0001"


class RegraOut(BaseModel):
    id: int
    fornecedor: str
    documento: str
    conta_debito: str
    centro_custo: str
    origem: str
    confianca: str
    ativo: bool


# ---------------------------------------------------------------- helpers


def _bases(sessao: Session):
    return (
        list(sessao.exec(select(PlanoContas))),
        list(sessao.exec(select(Fornecedor))),
        list(sessao.exec(select(RegraDePara))),
    )


def _exigir_conta(sessao: Session, codigo: str) -> str:
    conta = normalizar_conta(codigo)
    if not sessao.get(PlanoContas, conta):
        raise HTTPException(422, f"Conta {conta} nao consta no plano de contas.")
    return conta


_CODIGOS_VALIDADOR = frozenset(
    {
        Codigo.VALOR_INVALIDO,
        Codigo.BANCO_NAO_MAPEADO,
        Codigo.CONTA_DEBITO_AUSENTE,
        Codigo.CONTA_INEXISTENTE,
        Codigo.CONTA_NAO_ANALITICA,
    }
)


def _revalidar_linha(
    sessao: Session, lote: LoteImportacao, lancamento: Lancamento
) -> ResumoLote:
    """Revalida so a linha editada; nao recria o lote nem mexe nas irmas."""
    apagar = set(_CODIGOS_VALIDADOR)
    if lancamento.conta_debito:
        apagar.add(Codigo.REGRA_AMBIGUA)
    sessao.exec(
        delete(Ocorrencia).where(
            Ocorrencia.lancamento_id == lancamento.id,
            Ocorrencia.codigo.in_(apagar),
        )
    )
    sessao.commit()

    achados = Validador(list(sessao.exec(select(PlanoContas)))).validar(lancamento)
    if lancamento.conta_debito:
        achados = [
            a
            for a in achados
            if a.codigo not in (Codigo.REGRA_AMBIGUA, Codigo.CONTA_DEBITO_AUSENTE)
        ]
    sessao.add_all(para_ocorrencias(lancamento.id, achados))
    sessao.commit()

    lancamentos = list(sessao.exec(select(Lancamento).where(Lancamento.lote_id == lote.id)))
    ids = [l.id for l in lancamentos]
    ocorrencias = list(
        sessao.exec(select(Ocorrencia).where(Ocorrencia.lancamento_id.in_(ids or [0])))
    )
    por_linha: dict[int, list[Ocorrencia]] = {}
    for o in ocorrencias:
        por_linha.setdefault(o.lancamento_id, []).append(o)

    blockers = sum(1 for o in ocorrencias if o.severidade is Severidade.BLOCKER)
    warnings = sum(1 for o in ocorrencias if o.severidade is Severidade.WARNING)
    automaticos = 0
    manuais = 0
    pendentes = 0
    historico_derivado = 0
    for l in lancamentos:
        if l.status is StatusLancamento.AUTO:
            automaticos += 1
        elif l.status is StatusLancamento.MANUAL:
            manuais += 1
        else:
            pendentes += 1
        achados_linha = por_linha.get(l.id, [])
        if l.titulo_id is not None or not any(
            o.codigo == Codigo.HISTORICO_NAO_DERIVADO for o in achados_linha
        ):
            historico_derivado += 1

    if lote.status not in (StatusLote.APROVADO, StatusLote.EXPORTADO):
        if blockers:
            lote.status = StatusLote.BLOQUEADO
        elif lancamentos:
            lote.status = StatusLote.PRONTO
        else:
            lote.status = StatusLote.RASCUNHO
        sessao.add(lote)
        sessao.commit()

    return ResumoLote(
        id=lote.id,
        competencia=lote.competencia,
        status=lote.status.value,
        total=len(lancamentos),
        automaticos=automaticos,
        pendentes=pendentes,
        manuais=manuais,
        historico_derivado=historico_derivado,
        blockers=blockers,
        warnings=warnings,
        valor_total=round(sum(l.valor for l in lancamentos), 2),
    )


def _reprocessar(sessao: Session, lote: LoteImportacao) -> ResumoLote:
    """Recalcula os lancamentos do lote preservando as edicoes manuais.

    Chamado depois de importar arquivo, criar regra, ou editar com criar_regra.
    """
    plano, fornecedores, regras = _bases(sessao)
    pagamentos = list(sessao.exec(select(Pagamento).where(Pagamento.lote_id == lote.id)))
    titulos = list(
        sessao.exec(select(TituloContasPagar).where(TituloContasPagar.lote_id == lote.id))
    )
    conta = (
        sessao.get(ContaBancaria, lote.conta_bancaria_id) if lote.conta_bancaria_id else None
    )

    anteriores = list(sessao.exec(select(Lancamento).where(Lancamento.lote_id == lote.id)))
    edicoes = {
        l.pagamento_id: l for l in anteriores if l.status is StatusLancamento.MANUAL
    }

    ids = [l.id for l in anteriores]
    if ids:
        sessao.exec(delete(Ocorrencia).where(Ocorrencia.lancamento_id.in_(ids)))
        sessao.exec(delete(Lancamento).where(Lancamento.lote_id == lote.id))
        sessao.commit()

    processador = Processador(plano, fornecedores, regras, conta)
    itens, resumo = processador.processar(lote.id, pagamentos, titulos, edicoes)

    for item in itens:
        sessao.add(item.lancamento)
    sessao.commit()
    for item in itens:
        sessao.add_all(para_ocorrencias(item.lancamento.id, item.achados))
    sessao.commit()

    # Aprovado e exportado nao regridem por reprocessamento.
    if lote.status not in (StatusLote.APROVADO, StatusLote.EXPORTADO):
        lote.status = resumo.status_lote
        sessao.add(lote)
        sessao.commit()

    return ResumoLote(
        id=lote.id,
        competencia=lote.competencia,
        status=lote.status.value,
        total=resumo.total,
        automaticos=resumo.automaticos,
        pendentes=resumo.pendentes,
        manuais=resumo.manuais,
        historico_derivado=resumo.historico_derivado,
        blockers=resumo.blockers,
        warnings=resumo.warnings,
        valor_total=round(resumo.valor_total, 2),
    )


def _salvar_temporario(arquivo: UploadFile) -> tuple[Path, str]:
    conteudo = arquivo.file.read()
    sufixo = Path(arquivo.filename or "arquivo").suffix or ".pdf"
    destino = Path(tempfile.mkdtemp()) / f"upload{sufixo}"
    destino.write_bytes(conteudo)
    return destino, hashlib.sha256(conteudo).hexdigest()


# ---------------------------------------------------------------- rotas


@app.get("/api/saude")
def saude(sessao: Session = Depends(obter_sessao)):
    plano, fornecedores, regras = _bases(sessao)
    return {
        "plano_contas": len(plano),
        "fornecedores": len(fornecedores),
        "regras": len(regras),
        "regras_ativas": sum(1 for r in regras if r.ativo),
    }


@app.get("/api/lotes")
def listar_lotes(sessao: Session = Depends(obter_sessao)):
    lotes = sessao.exec(select(LoteImportacao).order_by(LoteImportacao.id.desc())).all()
    return [
        {
            "id": l.id,
            "competencia": l.competencia,
            "status": l.status.value,
            "criado_em": l.criado_em.isoformat(),
            "lancamentos": len(
                sessao.exec(select(Lancamento).where(Lancamento.lote_id == l.id)).all()
            ),
            # A tela de importacao precisa disso para dizer o que falta: sem o
            # Contas a Pagar nenhum Historico e derivado, e reabrir o app nao pode
            # apagar a memoria do que ja entrou.
            "arquivos": [
                {"nome": a.nome, "tipo": a.tipo.value, "linhas_lidas": a.linhas_lidas}
                for a in sessao.exec(
                    select(ArquivoImportado).where(ArquivoImportado.lote_id == l.id)
                )
            ],
        }
        for l in lotes
    ]


@app.post("/api/lotes")
def criar_lote(competencia: str, sessao: Session = Depends(obter_sessao)):
    lote = LoteImportacao(competencia=competencia)
    sessao.add(lote)
    sessao.commit()
    sessao.refresh(lote)
    return {
        "id": lote.id,
        "competencia": lote.competencia,
        "status": lote.status.value,
        "criado_em": lote.criado_em.isoformat(),
        "lancamentos": 0,
        "arquivos": [],
    }


@app.post("/api/lotes/{lote_id}/arquivos")
def importar_arquivo(
    lote_id: int, arquivo: UploadFile, sessao: Session = Depends(obter_sessao)
):
    """Detecta o layout, parseia e reprocessa (RF-01.1 a RF-01.8)."""
    lote = sessao.get(LoteImportacao, lote_id)
    if lote is None:
        raise HTTPException(404, "Lote nao encontrado.")
    if lote.status in (StatusLote.APROVADO, StatusLote.EXPORTADO):
        raise HTTPException(409, f"Lote em {lote.status.value} nao aceita novo arquivo.")

    if not (arquivo.filename or "").lower().endswith(".pdf"):
        raise HTTPException(
            415,
            "Somente PDF: o plano de contas e a Base Bancos sao carregados no seed, "
            "nao por upload.",
        )

    caminho, sha = _salvar_temporario(arquivo)
    existente = sessao.exec(
        select(ArquivoImportado).where(
            ArquivoImportado.lote_id == lote_id, ArquivoImportado.sha256 == sha
        )
    ).first()
    if existente:
        raise HTTPException(409, f"Arquivo ja importado neste lote: {existente.nome}.")

    tipo = itau.detectar_tipo(caminho)
    if tipo is None:
        raise HTTPException(422, "Layout nao reconhecido.")

    if tipo is TipoArquivo.CONTAS_PAGAR:
        registros = contas_pagar.carregar_titulos(caminho, lote_id)
    elif tipo is TipoArquivo.ITAU_PAGAMENTOS:
        registros = itau.carregar_pagamentos(caminho, lote_id)
    else:
        registros = itau.carregar_extrato(caminho, lote_id)

    if not registros:
        raise HTTPException(422, f"Nenhum registro extraido de {arquivo.filename}.")

    # A conta de credito vem do cabecalho do relatorio, nao de constante.
    if tipo in (TipoArquivo.ITAU_PAGAMENTOS, TipoArquivo.ITAU_EXTRATO):
        cabecalho = itau.conta_do_cabecalho(caminho)
        if cabecalho and lote.conta_bancaria_id is None:
            agencia, conta_corrente = cabecalho
            digitos = "".join(c for c in conta_corrente if c.isdigit())
            for banco in sessao.exec(select(ContaBancaria).where(ContaBancaria.agencia == agencia)):
                if "".join(c for c in banco.conta_corrente if c.isdigit()) in digitos:
                    lote.conta_bancaria_id = banco.id
                    break

    registro_arquivo = ArquivoImportado(
        lote_id=lote_id,
        nome=arquivo.filename or "sem-nome",
        sha256=sha,
        tipo=tipo,
        linhas_lidas=len(registros),
    )
    sessao.add(registro_arquivo)
    sessao.add_all(registros)
    sessao.add(lote)
    sessao.commit()

    resumo = _reprocessar(sessao, lote)
    return {"tipo": tipo.value, "linhas_lidas": len(registros), "resumo": resumo}


@app.post("/api/lotes/{lote_id}/reprocessar")
def reprocessar(lote_id: int, sessao: Session = Depends(obter_sessao)):
    """Recalcula o lote a partir dos fatos importados, preservando edicoes manuais.

    Existe porque a base De/Para tambem muda fora do fluxo de pendencias: o
    contador pode revisar docs/base-depara-inicial.xlsx e resemear, e o lote
    aberto precisa refletir isso sem reimportar PDF.
    """
    lote = sessao.get(LoteImportacao, lote_id)
    if lote is None:
        raise HTTPException(404, "Lote nao encontrado.")
    if lote.status is StatusLote.EXPORTADO:
        raise HTTPException(409, "Lote exportado e imutavel: abra outra competencia.")
    return _reprocessar(sessao, lote)


@app.get("/api/lotes/{lote_id}/lancamentos")
def listar_lancamentos(
    lote_id: int,
    status: str | None = None,
    apenas_blockers: bool = False,
    sessao: Session = Depends(obter_sessao),
):
    lancamentos = list(sessao.exec(select(Lancamento).where(Lancamento.lote_id == lote_id)))
    pagamentos = {
        p.id: p for p in sessao.exec(select(Pagamento).where(Pagamento.lote_id == lote_id))
    }
    descricoes = {c.codigo: c.descricao for c in sessao.exec(select(PlanoContas))}

    ocorrencias: dict[int, list[Ocorrencia]] = {}
    for o in sessao.exec(
        select(Ocorrencia).where(Ocorrencia.lancamento_id.in_([l.id for l in lancamentos] or [0]))
    ):
        ocorrencias.setdefault(o.lancamento_id, []).append(o)

    saida = []
    for l in sorted(lancamentos, key=lambda x: pagamentos[x.pagamento_id].data):
        if status and l.status.value != status:
            continue
        achados = ocorrencias.get(l.id, [])
        blockers = [a.codigo for a in achados if a.severidade is Severidade.BLOCKER]
        if apenas_blockers and not blockers:
            continue
        pagamento = pagamentos[l.pagamento_id]
        saida.append(
            LancamentoOut(
                id=l.id,
                data=pagamento.data.strftime("%d/%m/%Y"),
                favorecido=pagamento.favorecido_raw,
                documento=pagamento.documento_raw,
                filial=l.filial,
                conta_debito=l.conta_debito,
                conta_debito_descricao=descricoes.get(normalizar_conta(l.conta_debito), ""),
                conta_credito=l.conta_credito,
                valor=round(l.valor, 2),
                historico=l.historico,
                centro_custo=l.centro_custo,
                status=l.status.value,
                blockers=blockers,
                warnings=[a.codigo for a in achados if a.severidade is Severidade.WARNING],
            )
        )
    return saida


@app.patch("/api/lancamentos/{lancamento_id}")
def editar_lancamento(
    lancamento_id: int, edicao: EdicaoLancamento, sessao: Session = Depends(obter_sessao)
):
    """Edita a linha e, opcionalmente, cria a regra para as proximas (RF-04.3)."""
    lancamento = sessao.get(Lancamento, lancamento_id)
    if lancamento is None:
        raise HTTPException(404, "Lancamento nao encontrado.")
    lote = sessao.get(LoteImportacao, lancamento.lote_id)
    if lote.status in (StatusLote.APROVADO, StatusLote.EXPORTADO):
        raise HTTPException(409, f"Lote em {lote.status.value} nao aceita edicao.")

    if edicao.valor is not None and edicao.valor <= 0:
        raise HTTPException(422, "Valor nao e positivo.")

    if edicao.conta_debito is not None:
        lancamento.conta_debito = _exigir_conta(sessao, edicao.conta_debito)
    if edicao.conta_credito is not None:
        lancamento.conta_credito = _exigir_conta(sessao, edicao.conta_credito)
    if edicao.centro_custo is not None:
        lancamento.centro_custo = edicao.centro_custo
    if edicao.historico is not None:
        lancamento.historico = edicao.historico
    if edicao.valor is not None:
        lancamento.valor = edicao.valor

    lancamento.status = StatusLancamento.MANUAL
    lancamento.editado_por = edicao.editado_por
    lancamento.editado_em = datetime.now()
    sessao.add(lancamento)
    sessao.commit()

    if edicao.criar_regra and lancamento.conta_debito:
        pagamento = sessao.get(Pagamento, lancamento.pagamento_id)
        _garantir_regra(
            sessao,
            NovaRegra(
                fornecedor_nome=pagamento.favorecido_raw,
                documento=pagamento.documento_raw,
                conta_debito=lancamento.conta_debito,
                centro_custo=lancamento.centro_custo,
            ),
        )
        return _reprocessar(sessao, lote)

    return _revalidar_linha(sessao, lote, lancamento)


@app.get("/api/regras")
def listar_regras(sessao: Session = Depends(obter_sessao)):
    """Cadastro De/Para para consulta. Criar regra continua no POST (Pendências)."""
    regras = sessao.exec(select(RegraDePara).order_by(RegraDePara.id.desc())).all()
    fornecedores = {f.id: f for f in sessao.exec(select(Fornecedor)).all()}
    saida: list[RegraOut] = []
    for regra in regras:
        if regra.id is None:
            continue
        fornecedor = fornecedores.get(regra.fornecedor_id)
        saida.append(
            RegraOut(
                id=regra.id,
                fornecedor=fornecedor.nome_canonico if fornecedor else "",
                documento=fornecedor.documento if fornecedor else "",
                conta_debito=regra.conta_debito,
                centro_custo=regra.centro_custo_sugerido,
                origem=regra.origem,
                confianca=regra.confianca,
                ativo=regra.ativo,
            )
        )
    return saida


@app.post("/api/regras")
def criar_regra(regra: NovaRegra, sessao: Session = Depends(obter_sessao)):
    """Cria a regra e reprocessa todos os lotes abertos (RF-02.9)."""
    criada = _garantir_regra(sessao, regra)
    resumos = [
        _reprocessar(sessao, lote)
        for lote in sessao.exec(
            select(LoteImportacao).where(
                LoteImportacao.status.notin_([StatusLote.APROVADO, StatusLote.EXPORTADO])
            )
        )
    ]
    return {"regra_id": criada.id, "lotes_reprocessados": resumos}


def _garantir_regra(sessao: Session, nova: NovaRegra) -> RegraDePara:
    """Cria fornecedor se necessario e desativa regra anterior conflitante.

    Desativar em vez de apagar preserva o historico de uso da regra antiga.
    """
    chave = normalizar_nome_fornecedor(nova.fornecedor_nome)
    fornecedor = sessao.exec(
        select(Fornecedor).where(Fornecedor.chave_nome == chave)
    ).first()
    if fornecedor is None:
        fornecedor = Fornecedor(
            documento=nova.documento,
            nome_canonico=nova.fornecedor_nome,
            chave_nome=chave,
        )
        sessao.add(fornecedor)
        sessao.commit()
        sessao.refresh(fornecedor)
    elif nova.documento and not fornecedor.documento:
        fornecedor.documento = nova.documento
        sessao.add(fornecedor)

    conta = normalizar_conta(nova.conta_debito)
    for anterior in sessao.exec(
        select(RegraDePara).where(RegraDePara.fornecedor_id == fornecedor.id)
    ):
        if anterior.ativo and anterior.conta_debito != conta:
            anterior.ativo = False
            sessao.add(anterior)

    regra = RegraDePara(
        fornecedor_id=fornecedor.id,
        conta_debito=conta,
        centro_custo_sugerido=nova.centro_custo,
        origem=OrigemRegra.MANUAL,
        confianca=Confianca.ALTA,
        ativo=True,
        criada_por="contador",
    )
    sessao.add(regra)
    sessao.commit()
    sessao.refresh(regra)
    return regra


@app.get("/api/lotes/{lote_id}/pendencias")
def listar_pendencias(lote_id: int, sessao: Session = Depends(obter_sessao)):
    """Agrupa por fornecedor: resolver um resolve todas as linhas dele (RF-04.5)."""
    lancamentos = list(sessao.exec(select(Lancamento).where(Lancamento.lote_id == lote_id)))
    pagamentos = {
        p.id: p for p in sessao.exec(select(Pagamento).where(Pagamento.lote_id == lote_id))
    }
    ocorrencias: dict[int, list[Ocorrencia]] = {}
    for o in sessao.exec(
        select(Ocorrencia).where(
            Ocorrencia.lancamento_id.in_([l.id for l in lancamentos] or [0]),
            Ocorrencia.severidade == Severidade.BLOCKER,
        )
    ):
        ocorrencias.setdefault(o.lancamento_id, []).append(o)

    grupos: dict[str, dict] = {}
    for l in lancamentos:
        achados = ocorrencias.get(l.id, [])
        if not achados:
            continue
        pagamento = pagamentos[l.pagamento_id]
        chave = normalizar_nome_fornecedor(pagamento.favorecido_raw)
        grupo = grupos.setdefault(
            chave,
            {
                "fornecedor": pagamento.favorecido_raw,
                "documento": pagamento.documento_raw,
                "linhas": 0,
                "valor_total": 0.0,
                "motivos": set(),
                "lancamento_ids": [],
                "mensagens": [],
            },
        )
        grupo["linhas"] += 1
        grupo["valor_total"] += l.valor
        grupo["motivos"].update(a.codigo for a in achados)
        grupo["lancamento_ids"].append(l.id)
        for a in achados:
            if a.mensagem not in grupo["mensagens"]:
                grupo["mensagens"].append(a.mensagem)

    return sorted(
        (
            {**g, "motivos": sorted(g["motivos"]), "valor_total": round(g["valor_total"], 2)}
            for g in grupos.values()
        ),
        key=lambda g: -g["linhas"],
    )


@app.post("/api/lotes/{lote_id}/aprovar")
def aprovar(lote_id: int, aprovado_por: str = "contador", sessao: Session = Depends(obter_sessao)):
    """So a partir de PRONTO. Implementa RF-05.3 junto com RF-06.2."""
    lote = sessao.get(LoteImportacao, lote_id)
    if lote is None:
        raise HTTPException(404, "Lote nao encontrado.")
    resumo = _reprocessar(sessao, lote)
    if lote.status is not StatusLote.PRONTO:
        raise HTTPException(
            409,
            f"Lote em {lote.status.value}: resolva os {resumo.blockers} impedimentos "
            f"antes de aprovar.",
        )
    lote.status = StatusLote.APROVADO
    lote.aprovado_por = aprovado_por
    lote.aprovado_em = datetime.now()
    sessao.add(lote)
    sessao.commit()
    return {"id": lote.id, "status": lote.status.value, "aprovado_em": lote.aprovado_em}


@app.get("/api/lotes/{lote_id}/conferencia")
def baixar_conferencia(lote_id: int, sessao: Session = Depends(obter_sessao)):
    """Excel de conferencia: disponivel em qualquer status (RF-06.3)."""
    lote, lancamentos, datas = _material_export(sessao, lote_id)
    ocorrencias: dict[int, list[str]] = {}
    for o in sessao.exec(
        select(Ocorrencia).where(Ocorrencia.lancamento_id.in_([l.id for l in lancamentos] or [0]))
    ):
        ocorrencias.setdefault(o.lancamento_id, []).append(o.codigo)

    conteudo = export_fortes.planilha_conferencia(
        [(l, datas[l.pagamento_id]) for l in lancamentos], ocorrencias
    )
    return _xlsx(conteudo, f"conferencia-{lote.competencia}.xlsx")


@app.get("/api/lotes/{lote_id}/exportar")
def exportar(lote_id: int, sessao: Session = Depends(obter_sessao)):
    """Arquivo final. Travado atras da aprovacao (RF-06.2)."""
    lote, lancamentos, datas = _material_export(sessao, lote_id)
    try:
        conteudo = export_fortes.arquivo_final(
            lote.status, [(l, datas[l.pagamento_id]) for l in lancamentos]
        )
    except export_fortes.ExportacaoBloqueada as erro:
        raise HTTPException(409, str(erro)) from erro

    lote.status = StatusLote.EXPORTADO
    lote.exportado_em = datetime.now()
    for l in lancamentos:
        l.status = StatusLancamento.EXPORTADO
        sessao.add(l)
    sessao.add(lote)
    sessao.commit()
    return _xlsx(conteudo, f"fortes-{lote.competencia}.xlsx")


def _material_export(sessao: Session, lote_id: int):
    lote = sessao.get(LoteImportacao, lote_id)
    if lote is None:
        raise HTTPException(404, "Lote nao encontrado.")
    lancamentos = list(sessao.exec(select(Lancamento).where(Lancamento.lote_id == lote_id)))
    datas = {
        p.id: p.data for p in sessao.exec(select(Pagamento).where(Pagamento.lote_id == lote_id))
    }
    return lote, lancamentos, datas


def _xlsx(conteudo: bytes, nome: str) -> Response:
    return Response(
        content=conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@app.get("/api/plano-contas")
def buscar_contas(q: str = "", limite: int = 30, sessao: Session = Depends(obter_sessao)):
    """Busca por codigo ou descricao sobre as 1.516 analiticas (RF-04.4)."""
    termo = q.strip().lower()
    saida = []
    for c in sessao.exec(select(PlanoContas).where(PlanoContas.analitica == True)):  # noqa: E712
        if termo and termo not in c.codigo.lower() and termo not in (c.descricao or "").lower():
            continue
        saida.append({"codigo": c.codigo, "codigo_dv": c.codigo_dv, "descricao": c.descricao})
        if len(saida) >= limite:
            break
    return saida
