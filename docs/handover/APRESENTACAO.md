# Apresentação — ConFast

Quem apresenta clona o GitHub e sobe **na máquina dele**.
Com `AUTH_MODO=desligado` não aparece tela de login.

---

## Texto para mandar no WhatsApp

Copia o bloco abaixo. Troca `COLA_O_LINK_DO_GITHUB` pelo URL do repositório
depois do primeiro push.

```
ConFast — como apresentar amanhã

Precisas: Python 3.11+ e Node 20+. Se o repo for privado, aceita o convite no GitHub.

1) Clonar e subir

git clone COLA_O_LINK_DO_GITHUB
cd extrato-de-para-fortes

# terminal 1 — API
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp ../.env.example .env
.venv/bin/python -m uvicorn app.api:app --reload --host 127.0.0.1 --port 8000

# terminal 2 — ecrã
cd extrato-de-para-fortes/frontend
npm install
npm run dev

Abre o URL que o npm mostrar (em geral http://localhost:5173).
Tens de ver a Início, sem Google.

2) Demo (8 min) — só junho de 2026

Início → Conciliar → Iniciar → junho 2026.

Arrasta ESTES três ficheiros, da pasta arquivos-clickip/clickIP/:
• Relatorio ITAU CLICK-SCM - 01 A 20-06-2026.pdf
• Relatorio ITAU CLICK-SCM - 21 A 30-06-2026.pdf
• Contas a Pagar - Pagas - Click Ip SCM 01-01-2026 a 30-06-2026.pdf

O terceiro é grande. Espera. Não abras outro mês.

Depois: Pendências → Validar → Exportar.
Não cliques Aprovar (assim podes repetir o demo).

O que dizer: 439 linhas em junho, ~77% automáticas. O que sobra é escolher conta, não digitar linha. São sempre dois relatórios (Itaú + Contas a Pagar), não só o extrato.

3) Se travar

• Tela Entrar / Google → no backend/.env põe AUTH_MODO=desligado e reinicia o primeiro terminal.
• Página vazia → o terminal da API (porta 8000) não está a correr.
• npm diz 5174 → abre esse endereço, não o 5173.
• “período não bate” → PDF de outro mês no lote de junho.
• Windows: usa .venv\Scripts\python e .venv\Scripts\pip em vez de .venv/bin/...
```

---

## Detalhe (se precisares)

O primeiro start cria o SQLite e semeia plano de contas + De/Para (174 fornecedores).
`backend/.env` e `dados.db` não vão no git — cada máquina gera os seus.

| Sintoma | O que fazer |
|---|---|
| Tela “Entrar” | `AUTH_MODO=desligado` no `.env` e reiniciar o uvicorn |
| API error | Backend não está em `127.0.0.1:8000` |
| Vite noutro porto | Usar o URL que o `npm run dev` imprimiu |
| Só um PDF | Faltam os dois Itaú ou o Contas a Pagar |
| Outlook | Não usar. No demo o login está desligado |

Não é um produto no ar em `conciliador.projecont.com.br`. É o fluxo do mês, a correr local.
