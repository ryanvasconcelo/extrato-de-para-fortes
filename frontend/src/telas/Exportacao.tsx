/* Tela 4: entrega. A revisão do arquivo Fortes é na aba Validar; aqui a
 * conferência é download secundário. Aprovar e exportar também existem nesta
 * aba. O botão de exportar fica visivelmente travado enquanto não houver
 * aprovação — a trava real está no backend (RF-06.2), aqui é só o reflexo dela. */

import { useState, type ReactNode } from "react";
import {
  api,
  baixarPlanilha,
  dinheiro,
  type Lote,
  type Resumo,
} from "../api/cliente";
import { IcoDownload } from "../componentes/icones";
import { Aviso, Botao, Etiqueta } from "../componentes/primitivos";

export function Exportacao({
  lote,
  resumo,
  onMudou,
}: {
  lote: Lote;
  resumo: Resumo | null;
  onMudou: () => void;
}) {
  const [erro, setErro] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const aprovado = lote.status === "APROVADO" || lote.status === "EXPORTADO";
  const podeAprovar = lote.status === "PRONTO";

  async function comErro(acao: () => Promise<void>) {
    setOcupado(true);
    setErro(null);
    try {
      await acao();
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div className="jornada">
      <header className="competencias__cabeca">
        <h1 className="ckp-h2">Exportar</h1>
        <p className="ckp-body-sm competencias__lede">
          Aprove o lote e baixe o template Fortes. A conferência abaixo é só
          um download auxiliar com ocorrências — a planilha oficial é a da
          aba Validar.
        </p>
      </header>

      {resumo && (
        <dl className="exportar__resumo">
          <div>
            <dt>Lançamentos</dt>
            <dd className="ckp-numeric">{resumo.total}</dd>
          </div>
          <div>
            <dt>Valor total</dt>
            <dd className="ckp-numeric">R$ {dinheiro(resumo.valor_total)}</dd>
          </div>
          <div>
            <dt>Impedimentos</dt>
            <dd className="ckp-numeric">{resumo.blockers}</dd>
          </div>
          <div>
            <dt>Histórico derivado</dt>
            <dd className="ckp-numeric">
              {resumo.historico_derivado}/{resumo.total}
            </dd>
          </div>
        </dl>
      )}

      <section className="card">
        <div className="card__body exportar__passos">
          <header className="exportar__status">
            <h2 className="ckp-h4" style={{ margin: 0 }}>
              Entrega
            </h2>
            <Etiqueta estado={lote.status} />
          </header>

          <Etapa
            titulo="Conferir"
            descricao="Download secundário: planilha com status e ocorrências por linha, não o arquivo Fortes."
          >
            <Botao
              onClick={() =>
                void comErro(() =>
                  baixarPlanilha(
                    `/lotes/${lote.id}/conferencia`,
                    `conferencia-${lote.competencia}.xlsx`,
                  ),
                )
              }
              desabilitado={ocupado}
            >
              Baixar conferência
            </Botao>
          </Etapa>

          <Etapa
            titulo="Aprovar"
            descricao={
              aprovado
                ? "Aprovado. O arquivo final está liberado."
                : podeAprovar
                  ? "Confirma que a conferência foi feita e libera o arquivo final."
                  : "Indisponível: resolva os impedimentos na tela de validação."
            }
          >
            <Botao
              tom="primario"
              desabilitado={ocupado || !podeAprovar}
              onClick={() =>
                void comErro(async () => {
                  await api.aprovar(lote.id);
                  onMudou();
                })
              }
            >
              {aprovado ? "Aprovado" : "Aprovar competência"}
            </Botao>
          </Etapa>

          <Etapa
            titulo="Exportar para o Fortes"
            descricao="XLSX no layout de importação, sem cabeçalho, uma linha por lançamento."
          >
            <button
              type="button"
              className="btn btn--primary btn--morph"
              disabled={ocupado || !aprovado}
              onClick={() =>
                void comErro(async () => {
                  await baixarPlanilha(
                    `/lotes/${lote.id}/exportar`,
                    `fortes-${lote.competencia}.xlsx`,
                  );
                  onMudou();
                })
              }
            >
              <span className="label label--in">
                <IcoDownload />
                Gerar arquivo final
              </span>
              <span className="label label--out">
                <IcoDownload />
                fortes-{lote.competencia}.xlsx
              </span>
            </button>
          </Etapa>

          {erro && <Aviso tom="erro">{erro}</Aviso>}
          {!aprovado && resumo?.warnings ? (
            <Aviso tom="aviso">
              {resumo.warnings} aviso(s) não impedem a exportação, mas constam na
              planilha de conferência.
            </Aviso>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function Etapa({
  titulo,
  descricao,
  children,
}: {
  titulo: string;
  descricao: string;
  children: ReactNode;
}) {
  return (
    <div className="exportar__etapa">
      <div className="min-w-0 flex-1">
        <div className="ckp-body-sm" style={{ fontWeight: 600 }}>
          {titulo}
        </div>
        <p className="ckp-caption" style={{ margin: "4px 0 0" }}>
          {descricao}
        </p>
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}
