"""A porta de login fecha e-mail que não está na lista."""

from __future__ import annotations


def test_sem_lista_aceita_qualquer_email(monkeypatch):
    monkeypatch.delenv("AUTH_EMAILS", raising=False)
    monkeypatch.delenv("AUTH_DOMINIOS", raising=False)
    from app.autenticacao import email_permitido

    assert email_permitido("qualquer@gmail.com")


def test_lista_de_emails_aceita_espaco_e_soma_ao_dominio(monkeypatch):
    monkeypatch.setenv("AUTH_DOMINIOS", "projecont.com.br")
    monkeypatch.setenv("AUTH_EMAILS", "ryan@pktech.ai, ryancdz9@gmail.com")
    from app.autenticacao import email_permitido

    assert email_permitido("ryancdz9@gmail.com")
    assert email_permitido("ryan@pktech.ai")
    assert email_permitido("alguem@projecont.com.br")
    assert not email_permitido("alguem@hotmail.com")


def test_id_token_entrega_email_com_arroba():
    import base64
    import json

    from app.autenticacao import _email_do_id_token, _primeiro_email

    carga = (
        base64.urlsafe_b64encode(json.dumps({"email": "Ryan@pktech.ai"}).encode())
        .rstrip(b"=")
        .decode()
    )
    assert _email_do_id_token(f"a.{carga}.b") == "Ryan@pktech.ai"
    assert _primeiro_email("nao-e-email", "ryan@pktech.ai") == "ryan@pktech.ai"


def test_segredo_microsoft_guid_e_o_id_nao_o_valor(monkeypatch):
    from app.autenticacao import _segredo_microsoft_parece_id

    monkeypatch.setenv("MICROSOFT_CLIENT_SECRET", "11111111-2222-3333-4444-555555555555")
    assert _segredo_microsoft_parece_id()
    monkeypatch.setenv("MICROSOFT_CLIENT_SECRET", "abc~valor-longo-que-o-azure-mostra-uma-vez")
    assert not _segredo_microsoft_parece_id()


def test_dominio_e_email_explícitos(monkeypatch):
    monkeypatch.delenv("AUTH_EMAILS", raising=False)
    monkeypatch.setenv("AUTH_DOMINIOS", "projecont.com.br")
    from app.autenticacao import email_permitido

    assert email_permitido("ryan@projecont.com.br")
    assert not email_permitido("alguem@gmail.com")
