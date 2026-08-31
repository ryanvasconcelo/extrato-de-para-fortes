/* Home: status do lote ativo + atalhos quadrados (produto.mdc 3).
   PNGs Liquid Glass da Icons8 nos cards. Sem atalho de retomar. */

import type { Lote, Resumo } from "../api/cliente";
import iconeHistorico from "../ativos/icone-historico.png";
import iconePlay from "../ativos/icone-play.png";
import iconeRegras from "../ativos/icone-regras.png";
import { EtiquetaLote, formatarCompetencia } from "../componentes/primitivos";

interface Props {
  lote: Lote | null;
  resumo: Resumo | null;
  onConciliar: () => void;
  onHistorico: () => void;
  onRegras: () => void;
}

export function Inicio({
  lote,
  resumo,
  onConciliar,
  onHistorico,
  onRegras,
}: Props) {
  return (
    <div className="inicio" data-inicio>
      <header className="tela__cabeca">
        <h1 className="ckp-h2">Início</h1>
        <p className="ckp-body-sm tela__lede">
          Veja o mês em andamento e escolha o que fazer. Conciliar explica o
          caminho e depois pede o mês no calendário.
        </p>
      </header>

      <div className="inicio__atalhos">
        <button
          type="button"
          className="atalho"
          onClick={onConciliar}
        >
          <span className="atalho__icone atalho__icone--brand">
            <img className="atalho__png" src={iconePlay} alt="" width={32} height={32} />
          </span>
          <span className="atalho__nome">Conciliar</span>
          <span className="atalho__dica">Ver o passo a passo e começar</span>
        </button>
        <button type="button" className="atalho" onClick={onHistorico}>
          <span className="atalho__icone atalho__icone--accent">
            <img className="atalho__png" src={iconeHistorico} alt="" width={32} height={32} />
          </span>
          <span className="atalho__nome">Histórico</span>
          <span className="atalho__dica">Lotes já abertos e o lote ativo</span>
        </button>
        <button type="button" className="atalho" onClick={onRegras}>
          <span className="atalho__icone atalho__icone--neutral">
            <img className="atalho__png" src={iconeRegras} alt="" width={32} height={32} />
          </span>
          <span className="atalho__nome">Regras</span>
          <span className="atalho__dica">Cadastro De/Para já existente</span>
        </button>
      </div>
      <a className="sr-only" href="https://icons8.com/icons/liquid-glass" target="_blank" rel="noreferrer">
        Ícones: Icons8 Liquid Glass
      </a>

      <section className="vidro inicio__status" aria-label="Status do mês">
        {lote ? (
          <>
            <div className="inicio__status-cabeca">
              <h2 className="ckp-h3 inicio__mes">{formatarCompetencia(lote.competencia)}</h2>
              <EtiquetaLote estado={lote.status} />
            </div>
            <p className="ckp-caption inicio__status-meta">
              Lote <span className="ckp-mono">#{lote.id}</span>
              {resumo
                ? ` · ${resumo.total} lançamento(s)`
                : lote.lancamentos
                  ? ` · ${lote.lancamentos} lançamento(s)`
                  : ""}
            </p>
            {resumo && (
              <dl className="inicio__metricas">
                <div>
                  <dt>Automáticos</dt>
                  <dd className="ckp-numeric">{resumo.automaticos}</dd>
                </div>
                <div>
                  <dt>Manuais</dt>
                  <dd className="ckp-numeric">{resumo.manuais}</dd>
                </div>
              </dl>
            )}
          </>
        ) : (
          <>
            <h2 className="ckp-h3">Nenhum mês aberto</h2>
            <p className="ckp-body-sm tela__lede">
              Toque em Conciliar e escolha o mês no calendário. Isso cria o lote
              antes de subir PDF.
            </p>
          </>
        )}
      </section>
    </div>
  );
}
