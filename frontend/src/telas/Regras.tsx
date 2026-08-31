/* Cadastro De/Para: leitura. Novas regras nascem em Pendências (RF-02.9). */

import { useEffect, useState } from "react";
import { api, type Regra } from "../api/cliente";
import { Aviso } from "../componentes/primitivos";

export function Regras() {
  const [regras, setRegras] = useState<Regra[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    api
      .regras()
      .then(setRegras)
      .catch((e) => setErro((e as Error).message));
  }, []);

  const ativas = regras?.filter((r) => r.ativo).length ?? 0;

  return (
    <div className="regras" data-regras>
      <header className="tela__cabeca">
        <h1 className="ckp-h2">Regras</h1>
        <p className="ckp-body-sm tela__lede">
          Consulte o cadastro De/Para já existente. Para criar ou trocar a
          conta de um fornecedor, use Pendências na jornada — esta lista não
          grava regra nova.
        </p>
      </header>

      {erro && <Aviso tom="erro">{erro}</Aviso>}

      <section className="vidro">
        <div className="historico__lista-cabeca">
          <h2 className="ckp-h4">Cadastro</h2>
          <p className="ckp-caption">
            {regras
              ? `${regras.length} regra(s), ${ativas} ativa(s). Inativas nascem de ambiguidade de conta.`
              : "Carregando o cadastro."}
          </p>
        </div>
        {!regras ? (
          <div className="esqueleto" aria-busy="true" aria-label="Carregando regras">
            <span className="esqueleto__linha" />
            <span className="esqueleto__linha" />
            <span className="esqueleto__linha" />
          </div>
        ) : regras.length === 0 ? (
          <p className="historico__vazio">
            Nenhuma regra ainda. Elas entram quando você resolve uma pendência
            ou quando a mineração semeia a base.
          </p>
        ) : (
          <div className="regras__grade">
            <table className="table">
              <thead>
                <tr>
                  <th>Fornecedor</th>
                  <th>Documento</th>
                  <th>Conta</th>
                  <th>Centro</th>
                  <th>Origem</th>
                  <th>Ativa</th>
                </tr>
              </thead>
              <tbody>
                {regras.map((r) => (
                  <tr key={r.id} data-regra-id={r.id}>
                    <td>{r.fornecedor}</td>
                    <td className="ckp-mono">{r.documento || "—"}</td>
                    <td className="ckp-mono">{r.conta_debito}</td>
                    <td className="ckp-mono">{r.centro_custo}</td>
                    <td>{r.origem}</td>
                    <td>{r.ativo ? "sim" : "não"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
