"""Normalizacoes de dominio.

Todas as comparacoes de conta contabil, documento e nome de fornecedor passam por
aqui. Ver ADR 0002 (chave de casamento) e ADR 0006 (digito verificador).
"""

from __future__ import annotations

import re
import unicodedata

# O Plano de Contas grafa "1.01.01.02.01.0003-4"; o arquivo Fortes grafa
# "1.01.01.02.01.0003". Sem normalizar, validar conta contra o plano falha em
# 100% dos casos (1.519 das 1.750 contas do plano tem o sufixo). Ver ADR 0006.
_DIGITO_VERIFICADOR = re.compile(r"-\d$")

# "GRUPO MULTI S.A" e "GRUPO MULTI SA" sao o mesmo fornecedor.
_SUFIXOS_SOCIETARIOS = re.compile(r"\b(S A|SA|S S|LTDA|ME|EPP|EIRELI|MEI|S C|CIA)\b")

# Parte das fontes corta o nome em 30 caracteres. Comparar por um prefixo mais
# curto une "EQUATORIAL PARA DISTRIBUIDORA" e a versao completa.
TAMANHO_CHAVE_NOME = 29

# Palavras curtas ou genericas nao ajudam a identificar fornecedor.
_TOKENS_IGNORADOS = frozenset(
    {"DO", "DA", "DE", "DOS", "DAS", "E", "EM", "COM", "COMERCIO", "INDUSTRIA", "SERVICOS"}
)


def normalizar_conta(codigo: str | None) -> str:
    """Remove o digito verificador e espacos. Canonico para toda comparacao."""
    if not codigo:
        return ""
    return _DIGITO_VERIFICADOR.sub("", str(codigo).strip())


def conta_e_analitica(codigo: str | None) -> bool:
    """Contas analiticas do plano ClickIP tem 6 niveis (5 pontos)."""
    return normalizar_conta(codigo).count(".") == 5


def normalizar_documento(valor: str | None) -> str:
    """CPF/CNPJ reduzido a digitos. Devolve '' se nao tiver 11 ou 14 digitos.

    Aceitar 11 digitos nao e detalhe: o extrato Itau traz CPF de pessoa fisica em
    4 das 173 linhas, e rejeita-los perderia lancamento.
    """
    digitos = re.sub(r"\D", "", str(valor or ""))
    return digitos if len(digitos) in (11, 14) else ""


def normalizar_texto(valor: str | None) -> str:
    """Maiusculas, sem acento, sem pontuacao, espacos colapsados."""
    if not valor:
        return ""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", str(valor)) if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ]", " ", sem_acento)).strip().upper()


def normalizar_nome_fornecedor(valor: str | None) -> str:
    """Chave de agrupamento de fornecedor: sem sufixo societario, truncada."""
    sem_sufixo = _SUFIXOS_SOCIETARIOS.sub(" ", normalizar_texto(valor))
    return re.sub(r"\s+", " ", sem_sufixo).strip()[:TAMANHO_CHAVE_NOME]


def tokens_fornecedor(valor: str | None) -> frozenset[str]:
    """Tokens significativos do nome, para casar fontes que grafam diferente.

    O Itau abrevia ("TERACOM TELEMATICA S A") e o Fortes usa a razao social
    completa. Interseccao de tokens casa os dois onde igualdade de string falha.
    """
    return frozenset(
        t
        for t in _SUFIXOS_SOCIETARIOS.sub(" ", normalizar_texto(valor)).split()
        if len(t) >= 4 and t not in _TOKENS_IGNORADOS
    )


def moeda_para_decimal(valor: str | float | None) -> float:
    """Aceita '1.234,56' (BR), '1234.56' e float. Devolve sempre positivo.

    O extrato de conta corrente traz valores negativos (-85.000,00) e o relatorio
    de pagamentos traz positivos; o lancamento contabil usa o modulo.
    """
    if valor is None or valor == "":
        return 0.0
    if isinstance(valor, (int, float)):
        return abs(float(valor))
    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return abs(float(texto))
    except ValueError:
        return 0.0
