/* Histórico de lotes (ADR 0012): listar e trocar o lote ativo. Abrir mês
 * novo é o calendário em Conciliar — não um campo MMYYYY nesta tela. */

import type { Lote } from "../api/cliente";
import { IcoCalendar } from "../componentes/icones";
import { Botao, EtiquetaLote, formatarCompetencia } from "../componentes/primitivos";

interface Props {
  lotes: Lote[];
  lotesCarregados: boolean;
  loteAtivoId: number | null;
  onEscolher: (lote: Lote) => void;
}

export function Historico({
  lotes,
  lotesCarregados,
  loteAtivoId,
  onEscolher,
}: Props) {
  return (
    <div className="historico">
      <header className="tela__cabeca">
        <h1 className="ckp-h2">Histórico</h1>
        <p className="ckp-body-sm tela__lede">
          Veja os lotes já abertos e escolha qual abrir. O mesmo mês pode ter
          mais de um lote — o id distingue. Para abrir um mês novo, volte ao
          Início e use Conciliar.
        </p>
      </header>

      <section
        className="vidro"
        data-lista-lotes
        data-lista-pronta={lotesCarregados ? "true" : "false"}
      >
        <div className="historico__lista-cabeca">
          <h2 className="ckp-h4">Lotes</h2>
          <p className="ckp-caption">
            Usar este lote entra na jornada daquele mês.
          </p>
        </div>
        {!lotesCarregados ? (
          <div className="esqueleto" aria-busy="true" aria-label="Carregando lotes">
            <span className="esqueleto__linha" />
            <span className="esqueleto__linha" />
            <span className="esqueleto__linha" />
            <span className="esqueleto__linha" />
          </div>
        ) : lotes.length === 0 ? (
          <p className="historico__vazio">
            Nenhum lote ainda. Em Início, use Conciliar e o calendário para
            abrir o primeiro mês.
          </p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Competência</th>
                <th>Lote</th>
                <th>Status</th>
                <th>Lançamentos</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {lotes.map((l) => {
                const ativo = l.id === loteAtivoId;
                return (
                  <tr
                    key={l.id}
                    data-lote-id={l.id}
                    data-lancamentos={l.lancamentos}
                    aria-current={ativo ? "true" : undefined}
                  >
                    <td>
                      <div className="historico__mes">
                        <IcoCalendar className="i" />
                        <div>
                          <div>{formatarCompetencia(l.competencia)}</div>
                          <div className="ckp-mono historico__mes-codigo">
                            {l.competencia}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="ckp-mono">{l.id}</td>
                    <td>
                      <EtiquetaLote estado={l.status} />
                    </td>
                    <td className="ckp-numeric">{l.lancamentos}</td>
                    <td>
                      <Botao
                        tom={ativo ? "neutro" : "primario"}
                        tamanho="sm"
                        onClick={() => onEscolher(l)}
                      >
                        Usar este lote
                      </Botao>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
