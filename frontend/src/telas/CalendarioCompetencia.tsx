/* Calendário de competência: 12 meses, não dias (ADR 0012 / 0015). */

import { useEffect, useMemo, useRef, useState } from "react";
import type { Lote } from "../api/cliente";
import {
  IcoChevronLeft,
  IcoChevronRight,
  IcoClose,
} from "../componentes/icones";
import {
  Aviso,
  Botao,
  EtiquetaLote,
  MESES,
  formatarCompetencia,
} from "../componentes/primitivos";

interface Props {
  aberto: boolean;
  lotes: Lote[];
  origem: { x: number; y: number } | null;
  onFechar: () => void;
  onEscolherLote: (lote: Lote) => void;
  onCriarMes: (competencia: string) => Promise<void>;
}

export function CalendarioCompetencia({
  aberto,
  lotes,
  origem,
  onFechar,
  onEscolherLote,
  onCriarMes,
}: Props) {
  const hoje = new Date();
  const [ano, setAno] = useState(hoje.getFullYear());
  const [mesAberto, setMesAberto] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const folhaRef = useRef<HTMLDivElement>(null);
  const [posicao, setPosicao] = useState({ top: 120, left: 280 });

  useEffect(() => {
    if (!aberto) {
      setMesAberto(null);
      setErro(null);
      setOcupado(false);
      return;
    }
    const margem = 16;
    const largura = 352;
    const altura = 440;
    const origemX = origem?.x ?? window.innerWidth / 2;
    const origemY = origem?.y ?? 200;
    let left = origemX - largura / 2;
    let top = origemY + 12;
    left = Math.min(Math.max(margem, left), window.innerWidth - largura - margem);
    if (top + altura > window.innerHeight - margem) {
      top = Math.max(margem, origemY - altura - 12);
    }
    setPosicao({ top, left });

    function tecla(e: KeyboardEvent) {
      if (e.key === "Escape") onFechar();
    }
    function fora(e: PointerEvent) {
      if (folhaRef.current && !folhaRef.current.contains(e.target as Node)) {
        onFechar();
      }
    }
    window.addEventListener("keydown", tecla);
    const espera = window.setTimeout(() => {
      document.addEventListener("pointerdown", fora);
    }, 0);
    return () => {
      window.removeEventListener("keydown", tecla);
      window.clearTimeout(espera);
      document.removeEventListener("pointerdown", fora);
    };
  }, [aberto, origem, onFechar]);

  const porMes = useMemo(() => {
    const mapa = new Map<string, Lote[]>();
    for (const lote of lotes) {
      const lista = mapa.get(lote.competencia) ?? [];
      lista.push(lote);
      mapa.set(lote.competencia, lista);
    }
    return mapa;
  }, [lotes]);

  if (!aberto) return null;

  async function escolherMes(mes: number) {
    const competencia = `${String(mes).padStart(2, "0")}${ano}`;
    const existentes = porMes.get(competencia) ?? [];
    setErro(null);
    if (existentes.length === 0) {
      setOcupado(true);
      try {
        await onCriarMes(competencia);
      } catch (e) {
        setErro((e as Error).message);
      } finally {
        setOcupado(false);
      }
      return;
    }
    if (existentes.length === 1) {
      onEscolherLote(existentes[0]);
      return;
    }
    setMesAberto(competencia);
  }

  const candidatos = mesAberto ? (porMes.get(mesAberto) ?? []) : [];

  return (
    <div
      ref={folhaRef}
      className="vidro calendario__folha"
      data-calendario
      role="dialog"
      aria-modal="false"
      aria-labelledby="calendario-titulo"
      style={{ top: posicao.top, left: posicao.left }}
    >
      <header className="calendario__cabeca">
        <div className="calendario__cabeca-linha">
          <h2 id="calendario-titulo" className="ckp-h4">
            Qual mês você vai trabalhar?
          </h2>
          <button
            type="button"
            className="btn btn--secondary btn--icon"
            aria-label="Fechar calendário"
            onClick={onFechar}
          >
            <IcoClose />
          </button>
        </div>
        <p className="ckp-caption">
          Toque no mês dos relatórios. Se o mês já existe, ele abre. Se existir
          mais de um trabalho no mesmo mês, você escolhe qual continuar.
        </p>
      </header>

        <div className="calendario__ano">
          <button
            type="button"
            className="btn btn--secondary btn--icon"
            aria-label="Ano anterior"
            onClick={() => setAno((a) => a - 1)}
          >
            <IcoChevronLeft />
          </button>
          <div className="calendario__ano-num">{ano}</div>
          <button
            type="button"
            className="btn btn--secondary btn--icon"
            aria-label="Próximo ano"
            onClick={() => setAno((a) => a + 1)}
          >
            <IcoChevronRight />
          </button>
        </div>

        {erro && <Aviso tom="erro">{erro}</Aviso>}

        {mesAberto ? (
          <div className="calendario__lotes">
            <p className="ckp-body-sm">
              {formatarCompetencia(mesAberto)} já foi aberto mais de uma vez.
              Qual lote você quer abrir?
            </p>
            <ul>
              {candidatos.map((lote) => (
                <li key={lote.id}>
                  <button
                    type="button"
                    className="calendario__lote"
                    onClick={() => onEscolherLote(lote)}
                  >
                    <span className="ckp-mono">#{lote.id}</span>
                    <EtiquetaLote estado={lote.status} />
                    <span className="ckp-numeric">{lote.lancamentos} lançamentos</span>
                  </button>
                </li>
              ))}
            </ul>
            <Botao tom="terciario" onClick={() => setMesAberto(null)}>
              Voltar aos meses
            </Botao>
          </div>
        ) : (
          <div className="calendario__meses">
            {MESES.map((nome, i) => {
              const mes = i + 1;
              const competencia = `${String(mes).padStart(2, "0")}${ano}`;
              const qtd = porMes.get(competencia)?.length ?? 0;
              return (
                <button
                  key={competencia}
                  type="button"
                  className="calendario__mes"
                  disabled={ocupado}
                  aria-label={`${nome} ${ano}${qtd ? `, ${qtd} já aberto(s)` : ""}`}
                  onClick={() => void escolherMes(mes)}
                >
                  <span className="calendario__mes-nome">{nome.slice(0, 3)}</span>
                  {qtd > 0 ? (
                    <span className="calendario__ponto" aria-hidden>
                      {qtd > 1 ? qtd : ""}
                    </span>
                  ) : (
                    <span className="calendario__ponto calendario__ponto--vazio" />
                  )}
                </button>
              );
            })}
          </div>
        )}
    </div>
  );
}
