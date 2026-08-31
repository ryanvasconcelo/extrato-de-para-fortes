"""Porta OAuth Google e Microsoft. Sessão opaca em cookie HttpOnly (não Better Auth:
isso é FastAPI, ADR 0001)."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlmodel import Session, select
from starlette.middleware.base import BaseHTTPMiddleware

from .banco import engine
from .modelos import SessaoLogin, Usuario

log = logging.getLogger("uvicorn.error")
_env_mtime: float | None = None


def _carregar_env_local() -> None:
    """Lê backend/.env de novo se o arquivo mudou. O --reload não observa .env."""
    global _env_mtime
    if "pytest" in sys.modules:
        return
    caminho = Path(__file__).resolve().parents[1] / ".env"
    if not caminho.is_file():
        return
    atual = caminho.stat().st_mtime
    if _env_mtime is not None and atual == _env_mtime:
        return
    _env_mtime = atual
    for bruta in caminho.read_text(encoding="utf-8").splitlines():
        linha = bruta.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.lstrip("\ufeff").partition("=")
        os.environ[chave.strip()] = valor.strip().strip("'").strip('"')


_carregar_env_local()

COOKIE_SESSAO = "concilia_sessao"
COOKIE_OAUTH = "concilia_oauth"
TTL_SESSAO = timedelta(days=7)
TTL_OAUTH = 600

GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO = "https://openidconnect.googleapis.com/v1/userinfo"

MS_AUTH = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MS_TOKEN = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
MS_USERINFO = "https://graph.microsoft.com/oidc/userinfo"
_GUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_AADSTS = re.compile(r"AADSTS\d+")

router = APIRouter(prefix="/api/auth")


def auth_ligado() -> bool:
    _carregar_env_local()
    modo = os.getenv("AUTH_MODO", "").strip().lower()
    if modo == "desligado":
        return False
    if modo == "ligado":
        return True
    return bool(provedor_google() or provedor_microsoft())


def provedor_google() -> bool:
    return bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))


def provedor_microsoft() -> bool:
    return bool(os.getenv("MICROSOFT_CLIENT_ID") and os.getenv("MICROSOFT_CLIENT_SECRET"))


def _segredo_microsoft_parece_id() -> bool:
    """O Azure mostra Secret ID (GUID) e Valor. O OAuth só aceita o Valor."""
    return bool(_GUID.match(os.getenv("MICROSOFT_CLIENT_SECRET", "").strip()))


def _lista_env(chave: str) -> set[str]:
    bruto = os.getenv(chave, "")
    return {item.strip().lower() for item in bruto.replace(";", ",").split(",") if item.strip()}


def email_permitido(email: str) -> bool:
    _carregar_env_local()
    local = email.strip().lower()
    if "@" not in local:
        return False
    emails = _lista_env("AUTH_EMAILS")
    dominios = _lista_env("AUTH_DOMINIOS")
    if not emails and not dominios:
        return True
    if local in emails:
        return True
    return local.rsplit("@", 1)[-1] in dominios


def url_publica() -> str:
    return os.getenv("AUTH_URL_PUBLICA", "http://localhost:5173").rstrip("/")


def destinos_oauth() -> dict[str, str]:
    base = url_publica()
    return {
        "google": f"{base}/api/auth/callback/google",
        "microsoft": f"{base}/api/auth/callback/microsoft",
    }


def origens_permitidas() -> set[str]:
    base = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://testserver",
        url_publica(),
    }
    for item in os.getenv("AUTH_ORIGENS", "").split(","):
        if item.strip():
            base.add(item.strip())
    return base


def cookie_segura() -> bool:
    return os.getenv("AUTH_COOKIE_SECURE", "0") == "1"


def _segredo() -> str:
    valor = os.getenv("AUTH_SECRET", "").strip()
    if valor:
        return valor
    if auth_ligado():
        raise RuntimeError("AUTH_SECRET é obrigatório com a porta ligada.")
    return "dev-nao-usar-em-producao"


def _serializador() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(_segredo(), salt="concilia-oauth")


def _pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    desafio = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, desafio


def _apos_login() -> str:
    return os.getenv("AUTH_DEPOIS_LOGIN", f"{url_publica()}/")


def _erro_login(codigo: str) -> RedirectResponse:
    return RedirectResponse(f"{url_publica()}/?erro={codigo}", status_code=302)


def _cookie_kwargs() -> dict:
    return {
        "httponly": True,
        "samesite": "lax",
        "secure": cookie_segura(),
        "path": "/",
    }


class PortaAuth(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        _carregar_env_local()
        caminho = request.url.path
        if request.method == "OPTIONS" or _publico(caminho) or not auth_ligado():
            return await call_next(request)
        if request.method not in ("GET", "HEAD") and not _origem_ok(request):
            return JSONResponse({"detail": "Origem recusada."}, status_code=403)
        usuario = usuario_da_requisicao(request)
        if usuario is None:
            return JSONResponse({"detail": "Faça login."}, status_code=401)
        request.state.usuario = usuario
        return await call_next(request)


def _publico(caminho: str) -> bool:
    if caminho in ("/docs", "/redoc", "/openapi.json"):
        return True
    return caminho in {
        "/api/auth/eu",
        "/api/auth/provedores",
        "/api/auth/entrar/google",
        "/api/auth/entrar/microsoft",
        "/api/auth/callback/google",
        "/api/auth/callback/microsoft",
    }


def _origem_ok(request: Request) -> bool:
    origem = request.headers.get("origin")
    if origem and origem in origens_permitidas():
        return True
    site = request.headers.get("sec-fetch-site", "")
    if site in ("same-origin", "none"):
        return True
    host = request.headers.get("host", "")
    if host.startswith("testserver") and not origem:
        return True
    return False


def usuario_da_requisicao(request: Request) -> Usuario | None:
    sid = request.cookies.get(COOKIE_SESSAO)
    if not sid:
        return None
    agora = datetime.now()
    with Session(engine) as sessao:
        registro = sessao.get(SessaoLogin, sid)
        if registro is None or registro.expira_em < agora:
            return None
        usuario = sessao.get(Usuario, registro.usuario_id)
        if usuario is None:
            return None
        usuario.ultimo_acesso_em = agora
        sessao.add(usuario)
        sessao.commit()
        sessao.refresh(usuario)
        return usuario


def instalar(app) -> None:
    app.add_middleware(PortaAuth)
    app.include_router(router)


@router.get("/provedores")
def provedores():
    return {
        "ligado": auth_ligado(),
        "google": provedor_google(),
        "microsoft": provedor_microsoft(),
    }


@router.get("/eu")
def eu(request: Request):
    if not auth_ligado():
        return {
            "id": 0,
            "email": "dev@local",
            "nome": "Modo local",
            "modo": "desligado",
        }
    usuario = usuario_da_requisicao(request)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Faça login.")
    return {
        "id": usuario.id,
        "email": usuario.email,
        "nome": usuario.nome,
        "modo": "ligado",
    }


@router.get("/entrar/google")
def entrar_google():
    return _entrar("google")


@router.get("/entrar/microsoft")
def entrar_microsoft():
    return _entrar("microsoft")


def _entrar(provedor: str) -> RedirectResponse:
    if provedor == "google" and not provedor_google():
        raise HTTPException(status_code=503, detail="Google não está configurado.")
    if provedor == "microsoft" and not provedor_microsoft():
        raise HTTPException(status_code=503, detail="Outlook não está configurado.")
    if provedor == "microsoft" and _segredo_microsoft_parece_id():
        log.info(
            "MICROSOFT_CLIENT_SECRET parece o Secret ID do Azure (GUID). "
            "Cole o Valor do segredo, que o portal mostra uma vez só."
        )
    verifier, desafio = _pkce()
    try:
        estado = _serializador().dumps({"p": provedor, "v": verifier})
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    redirect_uri = destinos_oauth()[provedor]
    if provedor == "google":
        params = {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": estado,
            "code_challenge": desafio,
            "code_challenge_method": "S256",
            "prompt": "select_account",
        }
        destino = f"{GOOGLE_AUTH}?{urlencode(params)}"
    else:
        params = {
            "client_id": os.environ["MICROSOFT_CLIENT_ID"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid profile email",
            "state": estado,
            "code_challenge": desafio,
            "code_challenge_method": "S256",
            "response_mode": "query",
            "prompt": "select_account",
        }
        destino = f"{MS_AUTH}?{urlencode(params)}"
    resposta = RedirectResponse(destino, status_code=302)
    resposta.set_cookie(
        COOKIE_OAUTH,
        estado,
        max_age=TTL_OAUTH,
        **_cookie_kwargs(),
    )
    return resposta


@router.get("/callback/google")
def callback_google(request: Request, code: str | None = None, state: str | None = None):
    return _callback(request, "google", code, state)


@router.get("/callback/microsoft")
def callback_microsoft(request: Request, code: str | None = None, state: str | None = None):
    return _callback(request, "microsoft", code, state)


def _callback(
    request: Request,
    provedor: str,
    code: str | None,
    state: str | None,
) -> RedirectResponse:
    cookie = request.cookies.get(COOKIE_OAUTH)
    if not code or not state or not cookie or cookie != state:
        log.info(
            "login recusado: sessão OAuth (code=%s state=%s cookie=%s)",
            bool(code),
            bool(state),
            bool(cookie) and cookie == state,
        )
        return _erro_login("sessao")
    try:
        dados = _serializador().loads(state, max_age=TTL_OAUTH)
    except (BadSignature, SignatureExpired):
        return _erro_login("sessao")
    if dados.get("p") != provedor:
        return _erro_login("sessao")
    verifier = dados.get("v")
    if not isinstance(verifier, str):
        return _erro_login("sessao")
    try:
        perfil = _trocar_codigo(provedor, code, verifier)
    except httpx.HTTPError as exc:
        log.info("login recusado: provedor %s (%s)", provedor, exc.__class__.__name__)
        return _erro_login("provedor")
    except ValueError:
        log.info("login recusado: %s não enviou e-mail", provedor)
        return _erro_login("sem_email")
    if not email_permitido(perfil["email"]):
        dominio = perfil["email"].rsplit("@", 1)[-1]
        log.info("login recusado: e-mail fora da lista (domínio %s)", dominio)
        return _erro_login("nao_autorizado")
    log.info("login ok via %s (domínio %s)", provedor, perfil["email"].rsplit("@", 1)[-1])
    usuario = _gravar_usuario(provedor, perfil)
    sid = secrets.token_urlsafe(32)
    agora = datetime.now()
    with Session(engine) as sessao:
        sessao.add(
            SessaoLogin(
                id=sid,
                usuario_id=usuario.id or 0,
                expira_em=agora + TTL_SESSAO,
            )
        )
        sessao.commit()
    resposta = RedirectResponse(_apos_login(), status_code=302)
    resposta.delete_cookie(COOKIE_OAUTH, path="/")
    resposta.set_cookie(
        COOKIE_SESSAO,
        sid,
        max_age=int(TTL_SESSAO.total_seconds()),
        **_cookie_kwargs(),
    )
    return resposta


def _trocar_codigo(provedor: str, code: str, verifier: str) -> dict[str, str]:
    redirect_uri = destinos_oauth()[provedor]
    if provedor == "google":
        token = httpx.post(
            GOOGLE_TOKEN,
            data={
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "code": code,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            timeout=15.0,
        )
        token.raise_for_status()
        pacote = token.json()
        acesso = pacote.get("access_token")
        if not acesso:
            raise ValueError("token")
        info = httpx.get(
            GOOGLE_USERINFO,
            headers={"Authorization": f"Bearer {acesso}"},
            timeout=15.0,
        )
        info.raise_for_status()
        corpo = info.json()
        email = _primeiro_email(corpo.get("email"), _email_do_id_token(pacote.get("id_token")))
        if not email or corpo.get("email_verified") is False:
            raise ValueError("email")
        return {
            "email": email,
            "nome": (corpo.get("name") or email).strip(),
            "provedor_id": str(corpo.get("sub") or email),
        }
    token = httpx.post(
        MS_TOKEN,
        data={
            "client_id": os.environ["MICROSOFT_CLIENT_ID"],
            "client_secret": os.environ["MICROSOFT_CLIENT_SECRET"],
            "code": code,
            "code_verifier": verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
        },
        timeout=15.0,
    )
    if token.is_error:
        _log_falha_token_microsoft(token)
        token.raise_for_status()
    corpo = token.json()
    acesso = corpo.get("access_token")
    if not acesso:
        raise ValueError("token")
    dados: dict = {}
    try:
        info = httpx.get(
            MS_USERINFO,
            headers={"Authorization": f"Bearer {acesso}"},
            timeout=15.0,
        )
        info.raise_for_status()
        dados = info.json()
    except httpx.HTTPError:
        dados = {}
    email = _primeiro_email(
        dados.get("email"),
        dados.get("preferred_username"),
        _email_do_id_token(corpo.get("id_token")),
    )
    if not email:
        email = _email_do_grafo(acesso)
    if not email:
        raise ValueError("email")
    return {
        "email": email,
        "nome": (dados.get("name") or email).strip(),
        "provedor_id": str(dados.get("sub") or email),
    }


def _log_falha_token_microsoft(resposta: httpx.Response) -> None:
    try:
        corpo = resposta.json()
    except ValueError:
        corpo = {}
    erro = corpo.get("error") if isinstance(corpo, dict) else None
    detalhe = str(corpo.get("error_description", "") if isinstance(corpo, dict) else "")
    codigo = match.group(0) if (match := _AADSTS.search(detalhe)) else ""
    log.info(
        "login recusado: microsoft token HTTP %s error=%s %s",
        resposta.status_code,
        erro or "?",
        codigo,
    )
    if _segredo_microsoft_parece_id():
        log.info(
            "MICROSOFT_CLIENT_SECRET parece o Secret ID do Azure (GUID). "
            "Cole o Valor do segredo, que o portal mostra uma vez só."
        )


def _primeiro_email(*candidatos: object) -> str:
    for item in candidatos:
        texto = str(item or "").strip().lower()
        if "@" in texto:
            return texto
    return ""


def _email_do_grafo(acesso: str) -> str:
    try:
        me = httpx.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {acesso}"},
            timeout=15.0,
        )
        me.raise_for_status()
    except httpx.HTTPError:
        return ""
    corpo = me.json()
    return _primeiro_email(corpo.get("mail"), corpo.get("userPrincipalName"))


def _email_do_id_token(id_token: object) -> str:
    if not isinstance(id_token, str) or id_token.count(".") < 2:
        return ""
    carga = id_token.split(".")[1]
    carga += "=" * (-len(carga) % 4)
    try:
        dados = json.loads(base64.urlsafe_b64decode(carga))
    except (ValueError, json.JSONDecodeError):
        return ""
    return str(dados.get("email") or dados.get("preferred_username") or "")


def _gravar_usuario(provedor: str, perfil: dict[str, str]) -> Usuario:
    agora = datetime.now()
    with Session(engine) as sessao:
        usuario = sessao.exec(
            select(Usuario).where(Usuario.email == perfil["email"])
        ).first()
        if usuario is None:
            usuario = Usuario(
                email=perfil["email"],
                nome=perfil["nome"],
                provedor=provedor,
                provedor_id=perfil["provedor_id"],
                criado_em=agora,
                ultimo_acesso_em=agora,
            )
        else:
            usuario.nome = perfil["nome"] or usuario.nome
            usuario.ultimo_acesso_em = agora
        sessao.add(usuario)
        sessao.commit()
        sessao.refresh(usuario)
        return usuario


@router.post("/sair")
def sair(request: Request):
    sid = request.cookies.get(COOKIE_SESSAO)
    if sid:
        with Session(engine) as sessao:
            registro = sessao.get(SessaoLogin, sid)
            if registro is not None:
                sessao.delete(registro)
                sessao.commit()
    resposta = JSONResponse({"ok": True})
    resposta.delete_cookie(COOKIE_SESSAO, path="/")
    return resposta
