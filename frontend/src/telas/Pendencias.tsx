/* Tela 2: pendências agrupadas por fornecedor.
 *
 * Resolver uma pendência cria REGRA, não corrige linha: é o que faz o volume cair
 * mês a mês (RF-04.5). Um fornecedor com 12 pagamentos é uma decisão, não doze. */

import { useState } from "react";
import { api, dinheiro, type Pendencia } from "../api/cliente";
import { BuscaConta } from "../componentes/BuscaConta";
import { IcoAlert } from "../componentes/icones";
import { Aviso, Botao, ROTULOS } from "../componentes/primitivos";

export function Pendencias({
  pendencias,
  onResolveu,
}: {
  pendencias: Pendencia[];
  onResolveu: () => void;
}) {
  const [aberta, setAberta] = useState<string | null>(null);
  const [conta, setConta] = useState("");
  const [centro, setCentro] = useState("0001");
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  if (!pendencias.length) {
    return (
      <div className="jornada">
        <header className="competencias__cabeca">
          <h1 className="ckp-h2">Pendências</h1>
          <p className="ckp-body-sm competencias__lede">
            Nada para decidir neste lote: todas as linhas já têm conta de
            débito válida. Siga para Validar e conferir a planilha Fortes.
          </p>
        </header>
        <Aviso tom="ok">
          Nenhuma pendência: todas as linhas têm conta de débito válida.
        </Aviso>
      </div>
    );
  }

  const linhas = pendencias.reduce((soma, p) => soma + p.linhas, 0);

  async function resolver(p: Pendencia) {
    if (!conta) {
      setErro("Escolha a conta de débito.");
      return;
    }
    setSalvando(true);
    setErro(null);
    try {
      await api.criarRegra({
        fornecedor_nome: p.fornecedor,
        documento: p.documento,
        conta_debito: conta,
        centro_custo: centro,
      });
      setAberta(null);
      setConta("");
      onResolveu();
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="jornada">
      <header className="competencias__cabeca">
        <h1 className="ckp-h2">Pendências</h1>
        <p className="ckp-body-sm competencias__lede">
          {pendencias.length} fornecedor(es) sem regra, cobrindo {linhas}{" "}
          linha(s). Atribua a conta de débito aqui. Cada regra vale para os
          próximos meses; a grade Validar não cria regra.
        </p>
      </header>

      <ul className="pendencias">
        {pendencias.map((p) => (
          <li key={p.fornecedor} className="card">
            <div className="card__body pendencias__cabeca">
              <div className="min-w-0">
                <div className="ckp-body pendencias__fornecedor">
                  {p.fornecedor}
                </div>
                <div className="pendencias__meta">
                  <span className="ckp-mono">{p.documento || "sem CPF/CNPJ"}</span>
                  <span>
                    {p.linhas} linha(s) · R$ {dinheiro(p.valor_total)}
                  </span>
                </div>
                <ul className="pendencias__motivos">
                  {p.motivos.map((m) => (
                    <li key={m} className="badge badge--error">
                      <IcoAlert className="i" />
                      {ROTULOS[m] ?? m}
                    </li>
                  ))}
                </ul>
              </div>
              <Botao
                tom={aberta === p.fornecedor ? "neutro" : "primario"}
                onClick={() => {
                  setAberta(aberta === p.fornecedor ? null : p.fornecedor);
                  setConta("");
                  setErro(null);
                }}
              >
                {aberta === p.fornecedor ? "Cancelar" : "Criar regra"}
              </Botao>
            </div>

            <div
              className={`pendencias__revela ${aberta === p.fornecedor ? "is-aberta" : ""}`}
              inert={aberta !== p.fornecedor ? true : undefined}
            >
              <div className="pendencias__revela-inner">
                <div className="pendencias__form">
                  {p.mensagens.length > 0 && (
                    <ul className="pendencias__msgs">
                      {p.mensagens.map((m) => (
                        <li key={m}>{m}</li>
                      ))}
                    </ul>
                  )}
                  <div className="pendencias__campos">
                    <div className="field pendencias__campo-conta">
                      <label className="field__label" htmlFor={`conta-${p.fornecedor}`}>
                        Conta de débito
                      </label>
                      <BuscaConta
                        id={`conta-${p.fornecedor}`}
                        valor={conta}
                        onEscolher={setConta}
                      />
                    </div>
                    <div className="field">
                      <label className="field__label" htmlFor={`centro-${p.fornecedor}`}>
                        Centro de custo
                      </label>
                      <input
                        id={`centro-${p.fornecedor}`}
                        value={centro}
                        onChange={(e) => setCentro(e.target.value)}
                        className="input input--mono pendencias__centro"
                      />
                    </div>
                    <Botao
                      tom="primario"
                      desabilitado={salvando || !conta}
                      onClick={() => void resolver(p)}
                    >
                      {salvando ? "Reprocessando…" : `Aplicar a ${p.linhas} linha(s)`}
                    </Botao>
                  </div>
                  {erro && aberta === p.fornecedor && <Aviso tom="erro">{erro}</Aviso>}
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
