# ADR 0016 — Porta OAuth Google e Microsoft no FastAPI

- **Status:** Aceito
- **Data:** 2026-08-25
- **Fase:** 8
- **Decisor:** usuário (login com Gmail e Outlook; Better Auth citado como opção)

## Contexto

O conciliador ia para `conciliador.projecont.com.br` sem porta: qualquer um que
achasse a URL lia e alterava lotes. O usuário pediu autenticação simples e segura
com Google (Gmail) e Microsoft (Outlook).

Better Auth é biblioteca Node. O backend é FastAPI + SQLite ([ADR 0001](0001-arquitetura-stack.md)).
Um sidecar Node só para login duplica deploy e o contrato HTTP.

## Decisão

**OAuth 2.0 no próprio FastAPI.** Authorization Code + PKCE. Google e Microsoft
Identity (tenant `common`, cobre Outlook.com e contas de trabalho). Sessão opaca
em cookie `HttpOnly; SameSite=Lax`. POST/PATCH/DELETE conferem `Origin`.

Quem entra vê os mesmos lotes: a porta é do escritório, não um produto
multi-tenant. Lista opcional `AUTH_DOMINIOS` / `AUTH_EMAILS` (e-mail na
lista **ou** domínio). Sem lista, qualquer conta Google/Microsoft entra —
só para desenvolvimento. O FastAPI relê `backend/.env` se o arquivo mudar:
o `--reload` do Uvicorn não observa `.env`.

`AUTH_MODO=desligado` (padrão da suíte e do `.env` local) deixa a API aberta.
Em produção: `AUTH_MODO=ligado`, `AUTH_SECRET`, `AUTH_COOKIE_SECURE=1` e pelo
menos um par de client id/secret.

## Consequências

A casca mostra Entrar enquanto não houver cookie. Os testes HTTP da suíte
continuam com a porta desligada, e `TestPortaDeLogin` liga a porta na hora.
