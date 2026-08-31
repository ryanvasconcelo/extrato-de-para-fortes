"""Modelo de dados. Ver ADR 0006 para o racional de cada decisao."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


class StatusLancamento(StrEnum):
    PENDENTE = "PENDENTE"
    AUTO = "AUTO"
    MANUAL = "MANUAL"
    APROVADO = "APROVADO"
    EXPORTADO = "EXPORTADO"


class StatusLote(StrEnum):
    RASCUNHO = "RASCUNHO"
    BLOQUEADO = "BLOQUEADO"
    PRONTO = "PRONTO"
    APROVADO = "APROVADO"
    EXPORTADO = "EXPORTADO"


class Confianca(StrEnum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    AMBIGUO_CONTA = "AMBIGUO_CONTA"


class OrigemRegra(StrEnum):
    MINERADA = "MINERADA"
    MANUAL = "MANUAL"


class TipoArquivo(StrEnum):
    ITAU_PAGAMENTOS = "ITAU_PAGAMENTOS"
    ITAU_EXTRATO = "ITAU_EXTRATO"
    CONTAS_PAGAR = "CONTAS_PAGAR"
    PLANO_CONTAS = "PLANO_CONTAS"


class Severidade(StrEnum):
    BLOCKER = "BLOCKER"
    WARNING = "WARNING"


class PlanoContas(SQLModel, table=True):
    """1.750 contas, 1.516 analiticas e 234 sinteticas.

    'codigo' e sem digito verificador e canonico para comparacao; 'codigo_dv' e
    como veio do cliente, para exibir. Ver ADR 0006.
    """

    codigo: str = Field(primary_key=True)
    codigo_dv: str
    descricao: str
    natureza: str | None = None
    reduzido: str | None = None
    analitica: bool = True


class ContaBancaria(SQLModel, table=True):
    """Base Bancos: conta corrente -> conta contabil de credito.

    Nao fixar a conta de credito no codigo mesmo que hoje so o Itau apareca.
    Ver handover FASE-1, armadilhas.
    """

    id: int | None = Field(default=None, primary_key=True)
    banco: str
    agencia: str
    conta_corrente: str
    conta_contabil: str = Field(index=True)

    __table_args__ = (UniqueConstraint("agencia", "conta_corrente"),)


class Fornecedor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    documento: str = Field(default="", index=True)
    nome_canonico: str = Field(index=True)
    chave_nome: str = Field(index=True)
    nomes_alternativos: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class RegraDePara(SQLModel, table=True):
    """Fornecedor -> conta de debito.

    O centro de custo e SUGESTAO, nao determinacao: 16 fornecedores usam varios
    centros com a mesma conta. Regras AMBIGUO_CONTA nascem com ativo=False para
    que o lancamento caia em pendencia em vez de receber conta arbitraria.
    """

    id: int | None = Field(default=None, primary_key=True)
    fornecedor_id: int = Field(foreign_key="fornecedor.id", index=True)
    conta_debito: str
    centro_custo_sugerido: str = "0001"
    origem: OrigemRegra = OrigemRegra.MINERADA
    confianca: Confianca = Confianca.MEDIA
    ativo: bool = True
    criada_em: datetime = Field(default_factory=datetime.now)
    criada_por: str = "mineracao"


class LoteImportacao(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    competencia: str = Field(index=True)
    status: StatusLote = StatusLote.RASCUNHO
    conta_bancaria_id: int | None = Field(default=None, foreign_key="contabancaria.id")
    criado_em: datetime = Field(default_factory=datetime.now)
    aprovado_por: str | None = None
    aprovado_em: datetime | None = None
    exportado_em: datetime | None = None


class ArquivoImportado(SQLModel, table=True):
    """sha256 implementa RF-01.8: detectar reimportacao do mesmo arquivo."""

    id: int | None = Field(default=None, primary_key=True)
    lote_id: int = Field(foreign_key="loteimportacao.id", index=True)
    nome: str
    sha256: str = Field(index=True)
    tipo: TipoArquivo
    linhas_lidas: int = 0


class Pagamento(SQLModel, table=True):
    """Fato importado, imutavel. Reprocessar recalcula Lancamento, nao Pagamento."""

    id: int | None = Field(default=None, primary_key=True)
    lote_id: int = Field(foreign_key="loteimportacao.id", index=True)
    arquivo_id: int | None = Field(default=None, foreign_key="arquivoimportado.id")
    data: date
    favorecido_raw: str
    documento_raw: str = ""
    tipo_pagamento: str = ""
    referencia_empresa: str = ""
    descricao_banco: str = ""
    valor: float


class TituloContasPagar(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    lote_id: int = Field(foreign_key="loteimportacao.id", index=True)
    fornecedor_raw: str
    documento_raw: str = ""
    conta_pag: str = ""
    vencimento: date | None = None
    tipo_doc: str = ""
    numero_titulo: str = ""
    doc_entrada: date | None = None
    valor_titulo: float = 0.0
    valor_pago: float = 0.0
    total_pago: float = 0.0
    despesa_codigo: str = ""
    despesa_descricao: str = ""


class Lancamento(SQLModel, table=True):
    """Resultado calculado. conta_credito e gravada, nao derivada no export,
    para que o arquivo seja reproduzivel apos a base mudar."""

    id: int | None = Field(default=None, primary_key=True)
    lote_id: int = Field(foreign_key="loteimportacao.id", index=True)
    pagamento_id: int = Field(foreign_key="pagamento.id", index=True)
    titulo_id: int | None = Field(default=None, foreign_key="titulocontaspagar.id")
    regra_id: int | None = Field(default=None, foreign_key="regradepara.id")
    filial: str = "0001"
    conta_debito: str = ""
    conta_credito: str = ""
    valor: float = 0.0
    historico: str = ""
    centro_custo: str = "0001"
    status: StatusLancamento = StatusLancamento.PENDENTE
    editado_por: str | None = None
    editado_em: datetime | None = None


class Ocorrencia(SQLModel, table=True):
    """Tabela, nao JSON: a tela de pendencias filtra por codigo e os testes da
    Fase 4 asseveram codigos especificos."""

    id: int | None = Field(default=None, primary_key=True)
    lancamento_id: int = Field(foreign_key="lancamento.id", index=True)
    severidade: Severidade
    codigo: str = Field(index=True)
    mensagem: str


class Usuario(SQLModel, table=True):
    """Conta de quem entrou com Google ou Microsoft. O escritório compartilha
    os lotes: a porta é quem entra, não isolamento por usuário."""

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    nome: str
    provedor: str
    provedor_id: str
    criado_em: datetime = Field(default_factory=datetime.now)
    ultimo_acesso_em: datetime = Field(default_factory=datetime.now)

    __table_args__ = (UniqueConstraint("provedor", "provedor_id"),)


class SessaoLogin(SQLModel, table=True):
    """Id opaco no cookie HttpOnly. Nada de token OAuth persistido."""

    id: str = Field(primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    criada_em: datetime = Field(default_factory=datetime.now)
    expira_em: datetime
