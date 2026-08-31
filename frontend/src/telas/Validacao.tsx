/* Tela 3: a planilha Fortes (ADR 0011). Filtros no topo, grade de 10 colunas,
 * aprovar/exportar embaixo. Editar célula não cria regra — isso fica em Pendências. */

import { useMemo, useState } from "react";
import {
  api,
  baixarPlanilha,
  dinheiro,
  type Lancamento,
  type Lote,
  type Resumo,
} from "../api/cliente";
import { IcoDownload } from "../componentes/icones";
import { Aviso, Botao } from "../componentes/primitivos";
import { PlanilhaFortes } from "./PlanilhaFortes";

type Filtro = "TODOS" | "PENDENTE" | "AUTO" | "MANUAL" | "AVISOS";

export function Validacao({
  lote,
  resumo,
  lancamentos,
  editavel,
  onEditou,
  onMudou,
}: {
  lote: Lote;
  resumo: Resumo | null;
  lancamentos: Lancamento[];
  editavel: boolean;
  onEditou: () => void;
  onMudou: () => void;
}) {
  const [filtro, setFiltro] = useState<Filtro>("TODOS");
  const [busca, setBusca] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const visiveis = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    return lancamentos.filter((l) => {
      if (filtro === "AVISOS" && !l.warnings.length) return false;
      if (filtro !== "TODOS" && filtro !== "AVISOS" && l.status !== filtro) return false;
      if (!termo) return true;
      return (
        l.favorecido.toLowerCase().includes(termo) ||
        l.historico.toLowerCase().includes(termo) ||
        l.conta_debito.includes(termo)
      );
    });
  }, [lancamentos, filtro, busca]);

  const soma = visiveis.reduce((total, l) => total + l.valor, 0);
  const blockers = resumo?.blockers ?? visiveis.reduce((n, l) => n + l.blockers.length, 0);

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
    <div className="jornada jornada--grade">
      <header className="competencias__cabeca">
        <h1 className="ckp-h2">Validar</h1>
        <p className="ckp-body-sm competencias__lede">
          Revise a planilha Fortes de 10 colunas. O que você editar na célula
          é o que será exportado. Exceção de conta fica nesta linha; criar
          regra só em Pendências.
        </p>
      </header>

      <div className="validar__barra">
        <div className="segmented" role="tablist" aria-label="Filtro da grade">
          {(["TODOS", "PENDENTE", "AUTO", "MANUAL", "AVISOS"] as Filtro[]).map((f) => (
            <button
              key={f}
              type="button"
              role="tab"
              aria-selected={filtro === f}
              className="segmented__item"
              onClick={() => setFiltro(f)}
            >
              {f}
            </button>
          ))}
        </div>
        <div className="input-group validar__busca">
          <svg className="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden>
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-3.5-3.5" />
          </svg>
          <input
            className="input"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="favorecido, histórico ou conta"
            aria-label="Buscar na grade"
          />
        </div>
      </div>

      {erro && <Aviso tom="erro">{erro}</Aviso>}

      <p className="ckp-caption">
        {visiveis.length} lançamentos · R$ {dinheiro(soma)} · {blockers} blockers
      </p>

      <div className="validar__grade">
        <PlanilhaFortes
          lancamentos={visiveis}
          editavel={editavel}
          onEditou={onEditou}
          onErro={setErro}
        />
      </div>

      <div className="validar__acoes">
        {lote.status === "BLOQUEADO" && (
          <p className="ckp-body-sm" style={{ color: "var(--text-weak)", margin: 0 }}>
            Resolva as linhas destacadas (sem débito) ou crie a regra na aba Pendências.
          </p>
        )}
        {lote.status === "PRONTO" && (
          <Botao
            tom="primario"
            desabilitado={ocupado}
            onClick={() =>
              void comErro(async () => {
                await api.aprovar(lote.id);
                onMudou();
              })
            }
          >
            Aprovar competência
          </Botao>
        )}
        {(lote.status === "APROVADO" || lote.status === "EXPORTADO") && (
          <button
            type="button"
            className="btn btn--primary btn--lg btn--morph"
            disabled={ocupado}
            onClick={() =>
              void comErro(() =>
                baixarPlanilha(
                  `/lotes/${lote.id}/exportar`,
                  `fortes-${lote.competencia}.xlsx`,
                ),
              )
            }
          >
            <span className="label label--in">
              <IcoDownload />
              Baixar arquivo Fortes
            </span>
            <span className="label label--out">
              <IcoDownload />
              fortes-{lote.competencia}.xlsx
            </span>
          </button>
        )}
        <Botao
          desabilitado={ocupado}
          onClick={() =>
            void comErro(() =>
              baixarPlanilha(
                `/lotes/${lote.id}/conferencia`,
                `conferencia-${lote.competencia}.xlsx`,
              ),
            )
          }
        >
          Baixar conferência
        </Botao>
      </div>
    </div>
  );
}
