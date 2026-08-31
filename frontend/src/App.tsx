/* Casca: trilho de sistema fixo em 100dvh; jornada no wizard (ADR 0015).
 * Recarregar não cai em lotes[0] — só o loteIdAtivo da sessão. */

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import {
  api,
  ErroSessao,
  type Lancamento,
  type Lote,
  type Pendencia,
  type ProvedoresAuth,
  type Resumo,
  type Usuario,
} from "./api/cliente";
import {
  IcoBook,
  IcoCalendar,
  IcoCheck,
  IcoChevronLeft,
  IcoDoc,
  IcoDownload,
  IcoHistory,
  IcoHome,
  IcoLogout,
  IcoMoon,
  IcoSun,
  IcoUpload,
} from "./componentes/icones";
import { MarcaClickip } from "./componentes/MarcaClickip";
import { CreditoRodape } from "./componentes/CreditoRodape";
import { Aviso } from "./componentes/primitivos";
import { CalendarioCompetencia } from "./telas/CalendarioCompetencia";
import { Conciliar } from "./telas/Conciliar";
import { Entrar } from "./telas/Entrar";
import { Exportacao } from "./telas/Exportacao";
import { Historico } from "./telas/Historico";
import { Importacao } from "./telas/Importacao";
import { Inicio } from "./telas/Inicio";
import { Pendencias } from "./telas/Pendencias";
import { Regras } from "./telas/Regras";
import { Validacao } from "./telas/Validacao";

type Sistema = "inicio" | "historico" | "regras" | "conciliar";
type Passo = "importar" | "pendencias" | "validar" | "exportar";
type Superficie =
  | { tipo: "sistema"; tela: Sistema }
  | { tipo: "jornada"; passo: Passo };

type EstadoNav = {
  superficie: Superficie;
  calendario: boolean;
  n: number;
};

const CHAVE_LOTE = "loteIdAtivo";

const NAV: { id: Sistema | "conciliar"; rotulo: string; icone: ReactNode }[] = [
  { id: "inicio", rotulo: "Início", icone: <IcoHome /> },
  { id: "conciliar", rotulo: "Conciliar", icone: <IcoCalendar /> },
  { id: "historico", rotulo: "Histórico", icone: <IcoHistory /> },
  { id: "regras", rotulo: "Regras", icone: <IcoBook /> },
];

const PASSOS: { id: Passo; rotulo: string; icone: ReactNode }[] = [
  { id: "importar", rotulo: "Importar", icone: <IcoUpload /> },
  { id: "pendencias", rotulo: "Pendências", icone: <IcoDoc /> },
  { id: "validar", rotulo: "Validar", icone: <IcoCheck /> },
  { id: "exportar", rotulo: "Exportar", icone: <IcoDownload /> },
];

export default function App() {
  const [lotes, setLotes] = useState<Lote[]>([]);
  const [lotesCarregados, setLotesCarregados] = useState(false);
  const [lote, setLote] = useState<Lote | null>(null);
  const [superficie, setSuperficie] = useState<Superficie>(() => {
    return lerEndereco().superficie;
  });
  const [calendarioAberto, setCalendarioAberto] = useState(
    () => lerEndereco().calendario,
  );
  const nivelRef = useRef(0);
  const [calendarioOrigem, setCalendarioOrigem] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const [nivel, setNivel] = useState(0);
  const [lancamentos, setLancamentos] = useState<Lancamento[]>([]);
  const [pendencias, setPendencias] = useState<Pendencia[]>([]);
  const [resumo, setResumo] = useState<Resumo | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [tema, setTema] = useState<"claro" | "escuro">("claro");
  const [usuario, setUsuario] = useState<Usuario | null | undefined>(undefined);
  const [provedores, setProvedores] = useState<ProvedoresAuth | null>(null);
  const [erroLogin] = useState<string | null>(() => lerErroLogin());

  useEffect(() => {
    document.documentElement.dataset.theme = tema === "escuro" ? "dark" : "light";
  }, [tema]);

  useEffect(() => {
    const inicial = { ...lerEndereco(), n: 0 };
    gravarEndereco(inicial, "replace");
    function noHistorico(ev: PopStateEvent) {
      const estado = (ev.state as EstadoNav | null) ?? { ...lerEndereco(), n: 0 };
      nivelRef.current = estado.n;
      setNivel(estado.n);
      setSuperficie(estado.superficie);
      setCalendarioAberto(estado.calendario);
    }
    window.addEventListener("popstate", noHistorico);
    return () => window.removeEventListener("popstate", noHistorico);
  }, []);

  useEffect(() => {
    limparErroLogin();
    let vivo = true;
    api
      .eu()
      .then((conta) => {
        if (vivo) setUsuario(conta);
      })
      .catch(async (e) => {
        if (!vivo) return;
        if (e instanceof ErroSessao) {
          setUsuario(null);
          try {
            setProvedores(await api.provedores());
          } catch {
            setProvedores({ ligado: true, google: false, microsoft: false });
          }
          return;
        }
        setErro((e as Error).message);
        setUsuario(null);
      });
    return () => {
      vivo = false;
    };
  }, []);

  useEffect(() => {
    if (!usuario) return;
    api
      .lotes()
      .then((lista) => {
        setLotes(lista);
        const salvo = Number(localStorage.getItem(CHAVE_LOTE));
        const encontrado = Number.isFinite(salvo)
          ? lista.find((l) => l.id === salvo)
          : undefined;
        if (encontrado) setLote(encontrado);
      })
      .catch((e) => {
        if (e instanceof ErroSessao) {
          setUsuario(null);
          return;
        }
        setErro((e as Error).message);
      })
      .finally(() => setLotesCarregados(true));
  }, [usuario]);

  const recarregar = useCallback(async () => {
    if (!usuario) return;
    try {
      const lista = await api.lotes();
      setLotes(lista);
      if (!lote) return;
      const atual = lista.find((l) => l.id === lote.id);
      if (!atual) {
        localStorage.removeItem(CHAVE_LOTE);
        setLote(null);
        setLancamentos([]);
        setPendencias([]);
        setResumo(null);
        gravarEndereco(
          { superficie: { tipo: "sistema", tela: "inicio" }, calendario: false, n: 0 },
          "replace",
        );
        nivelRef.current = 0;
        setNivel(0);
        setSuperficie({ tipo: "sistema", tela: "inicio" });
        setCalendarioAberto(false);
        return;
      }
      const [novos, novasPendencias] = await Promise.all([
        api.lancamentos(atual.id),
        api.pendencias(atual.id),
      ]);
      setLote(atual);
      setLancamentos(novos);
      setPendencias(novasPendencias);
      setResumo(resumir(atual, novos));
      setErro(null);
    } catch (e) {
      if (e instanceof ErroSessao) {
        setUsuario(null);
        return;
      }
      setErro((e as Error).message);
    }
  }, [lote?.id, usuario]);

  useEffect(() => {
    void recarregar();
  }, [recarregar]);

  function ativar(proximo: Lote) {
    localStorage.setItem(CHAVE_LOTE, String(proximo.id));
    setLote(proximo);
  }

  function lembrarLote(criado: Lote) {
    ativar(criado);
    setLotes((atuais) => {
      if (atuais.some((l) => l.id === criado.id)) return atuais;
      return [criado, ...atuais];
    });
  }

  async function sair() {
    try {
      await api.sair();
    } catch {
      /* a sessão some mesmo se a API falhar */
    }
    setUsuario(null);
    try {
      setProvedores(await api.provedores());
    } catch {
      setProvedores({ ligado: true, google: false, microsoft: false });
    }
  }

  function irPara(proxima: Superficie) {
    if (calendarioAberto && mesmaSuperficie(superficie, proxima)) {
      voltar();
      return;
    }
    if (!calendarioAberto && mesmaSuperficie(superficie, proxima)) return;

    const estado: EstadoNav = {
      superficie: proxima,
      calendario: false,
      n: calendarioAberto ? nivelRef.current : nivelRef.current + 1,
    };
    nivelRef.current = estado.n;
    setNivel(estado.n);
    setCalendarioAberto(false);
    setSuperficie(proxima);
    gravarEndereco(estado, calendarioAberto ? "replace" : "push");
  }

  function voltar() {
    if (nivelRef.current <= 0) {
      if (!calendarioAberto) return;
      const estado: EstadoNav = { superficie, calendario: false, n: 0 };
      setCalendarioAberto(false);
      gravarEndereco(estado, "replace");
      return;
    }
    window.history.back();
  }

  function entrarJornada(proximo: Lote, passo?: Passo) {
    lembrarLote(proximo);
    irPara({
      tipo: "jornada",
      passo: passo ?? passoSugerido(proximo),
    });
  }

  async function criarMes(competencia: string) {
    const criado = await api.criarLote(competencia);
    entrarJornada(criado, "importar");
  }

  function abrirCalendario(origem: { x: number; y: number }) {
    setCalendarioOrigem(origem);
    if (calendarioAberto) return;
    const estado: EstadoNav = {
      superficie,
      calendario: true,
      n: nivelRef.current + 1,
    };
    nivelRef.current = estado.n;
    setNivel(estado.n);
    setCalendarioAberto(true);
    gravarEndereco(estado, "push");
  }

  const naJornada = superficie.tipo === "jornada";
  const telaSistema = superficie.tipo === "sistema" ? superficie.tela : null;
  const passo = superficie.tipo === "jornada" ? superficie.passo : null;
  const naInicio =
    superficie.tipo === "sistema" &&
    superficie.tela === "inicio" &&
    !calendarioAberto;
  const fora = usuario === null;
  const podeVoltar = !fora && !naInicio && (calendarioAberto || nivel > 0);
  const dentro = Boolean(usuario);

  if (usuario === undefined) {
    return (
      <div className="casca casca--porta">
        <div className="casca__fundo" aria-hidden />
      </div>
    );
  }

  if (fora) {
    return (
      <div className="casca casca--porta">
        <a className="casca__skip" href="#conteudo">
          Ir ao conteúdo
        </a>
        <div className="casca__fundo" aria-hidden />
        <Entrar
          provedores={provedores}
          erro={erroLogin}
          tema={tema}
          onTema={() => setTema(tema === "claro" ? "escuro" : "claro")}
        />
      </div>
    );
  }

  return (
    <div className="casca">
      <a className="casca__skip" href="#conteudo">
        Ir ao conteúdo
      </a>
      <div className="casca__fundo" aria-hidden />
      <aside className="casca__rail">
        <div className="casca__marca">
          <MarcaClickip />
        </div>
        <nav className="casca__nav" aria-label="Sistema">
          {!fora &&
            NAV.map((item) => (
              <button
                key={item.id}
                type="button"
                className="menu__item"
                aria-current={
                  item.id === "conciliar"
                    ? telaSistema === "conciliar" || calendarioAberto || naJornada
                      ? "true"
                      : undefined
                    : !calendarioAberto && !naJornada && telaSistema === item.id
                      ? "true"
                      : undefined
                }
                onClick={() => irPara({ tipo: "sistema", tela: item.id })}
              >
                {item.icone}
                {item.rotulo}
              </button>
            ))}
        </nav>
        {usuario && usuario.modo === "ligado" ? (
          <div className="casca__conta">
            <span className="casca__conta-nome">{usuario.nome}</span>
            <span className="casca__conta-email">{usuario.email}</span>
            <button type="button" className="btn btn--secondary btn--sm" onClick={() => void sair()}>
              <IcoLogout />
              Sair
            </button>
          </div>
        ) : null}
      </aside>

      <div className="casca__main">
        <header className="casca__topo">
          {podeVoltar ? (
            <button type="button" className="casca__voltar" onClick={voltar}>
              <IcoChevronLeft />
              Voltar
            </button>
          ) : null}
          {dentro && naJornada && lote ? (
            <nav className="wizard" aria-label="Jornada" data-wizard>
              {PASSOS.map((p, i) => (
                <button
                  key={p.id}
                  type="button"
                  className="wizard__passo"
                  aria-current={passo === p.id ? "true" : undefined}
                  onClick={() => irPara({ tipo: "jornada", passo: p.id })}
                >
                  <span className="wizard__n">{i + 1}</span>
                  {p.icone}
                  {p.rotulo}
                  {p.id === "pendencias" && pendencias.length ? (
                    <span className="badge badge--count">{pendencias.length}</span>
                  ) : p.id === "validar" && lancamentos.length ? (
                    <span className="casca__nav-conta">{lancamentos.length}</span>
                  ) : null}
                </button>
              ))}
            </nav>
          ) : (
            <div className="casca__topo-titulo">
              <h1 className="ckp-h2">
                Con<i>Fast</i>
              </h1>
              <div className="casca__marca-produto">Assistente de Conciliação</div>
            </div>
          )}
          <button
            type="button"
            className="btn btn--secondary btn--icon btn--tema casca__tema"
            onClick={() => setTema(tema === "claro" ? "escuro" : "claro")}
            aria-label="Alternar tema"
            title={tema === "claro" ? "Modo escuro" : "Modo claro"}
          >
            <span className="btn--tema-lua">
              <IcoMoon />
            </span>
            <span className="btn--tema-sol">
              <IcoSun />
            </span>
          </button>
        </header>

        <main
          id="conteudo"
          className={`casca__conteudo ${passo === "validar" ? "casca__conteudo--grade" : ""}`}
        >
          {erro && <Aviso tom="erro">{erro}</Aviso>}

          {telaSistema === "inicio" && (
            <Inicio
              lote={lote}
              resumo={resumo}
              onConciliar={() =>
                irPara({ tipo: "sistema", tela: "conciliar" })
              }
              onHistorico={() =>
                irPara({ tipo: "sistema", tela: "historico" })
              }
              onRegras={() => irPara({ tipo: "sistema", tela: "regras" })}
            />
          )}
          {dentro && telaSistema === "conciliar" && (
            <Conciliar onIniciar={abrirCalendario} />
          )}
          {dentro && telaSistema === "historico" && (
            <Historico
              lotes={lotes}
              lotesCarregados={lotesCarregados}
              loteAtivoId={lote?.id ?? null}
              onEscolher={(escolhido) => entrarJornada(escolhido)}
            />
          )}
          {dentro && telaSistema === "regras" && <Regras />}

          {dentro && passo === "importar" && lote && (
            <Importacao lote={lote} onImportou={() => void recarregar()} />
          )}
          {dentro && passo === "pendencias" && (
            <Pendencias pendencias={pendencias} onResolveu={() => void recarregar()} />
          )}
          {dentro && passo === "validar" && lote && (
            <Validacao
              lote={lote}
              resumo={resumo}
              lancamentos={lancamentos}
              editavel={lote.status !== "APROVADO" && lote.status !== "EXPORTADO"}
              onEditou={() => void recarregar()}
              onMudou={() => void recarregar()}
            />
          )}
          {dentro && passo === "exportar" && lote && (
            <Exportacao lote={lote} resumo={resumo} onMudou={() => void recarregar()} />
          )}
        </main>
        <CreditoRodape className="casca__credito" />
      </div>

      <CalendarioCompetencia
        aberto={Boolean(dentro && calendarioAberto)}
        lotes={lotes}
        origem={calendarioOrigem}
        onFechar={voltar}
        onEscolherLote={(escolhido) => entrarJornada(escolhido)}
        onCriarMes={criarMes}
      />
    </div>
  );
}

const TELAS_SISTEMA: Sistema[] = ["inicio", "historico", "regras", "conciliar"];
const PASSOS_JORNADA: Passo[] = ["importar", "pendencias", "validar", "exportar"];

function ehSistema(valor: string): valor is Sistema {
  return (TELAS_SISTEMA as string[]).includes(valor);
}

function ehPasso(valor: string): valor is Passo {
  return (PASSOS_JORNADA as string[]).includes(valor);
}

function lerErroLogin(): string | null {
  return new URLSearchParams(window.location.search).get("erro");
}

function limparErroLogin() {
  const url = new URL(window.location.href);
  if (!url.searchParams.has("erro")) return;
  url.searchParams.delete("erro");
  const busca = url.searchParams.toString();
  window.history.replaceState(
    window.history.state,
    "",
    `${url.pathname}${busca ? `?${busca}` : ""}${url.hash}`,
  );
}

function enderecoDe(estado: Pick<EstadoNav, "superficie" | "calendario">): string {
  if (estado.calendario) return "#/conciliar/mes";
  if (estado.superficie.tipo === "jornada") return `#/${estado.superficie.passo}`;
  return `#/${estado.superficie.tela}`;
}

function lerEndereco(): { superficie: Superficie; calendario: boolean } {
  const bruto = window.location.hash.replace(/^#/, "");
  const caminho =
    (bruto.startsWith("/") ? bruto : `/${bruto}`).replace(/\/+$/, "") || "/inicio";
  const partes = caminho.split("/").filter(Boolean);
  const primeiro = partes[0] ?? "inicio";
  if (primeiro === "conciliar" && partes[1] === "mes") {
    return { superficie: { tipo: "sistema", tela: "conciliar" }, calendario: true };
  }
  if (ehPasso(primeiro)) {
    return { superficie: { tipo: "jornada", passo: primeiro }, calendario: false };
  }
  const tela: Sistema = ehSistema(primeiro) ? primeiro : "inicio";
  return { superficie: { tipo: "sistema", tela }, calendario: false };
}

function gravarEndereco(estado: EstadoNav, modo: "push" | "replace") {
  const url = `${window.location.pathname}${window.location.search}${enderecoDe(estado)}`;
  if (modo === "replace") {
    window.history.replaceState(estado, "", url);
  } else {
    window.history.pushState(estado, "", url);
  }
}

function mesmaSuperficie(a: Superficie, b: Superficie): boolean {
  if (a.tipo !== b.tipo) return false;
  if (a.tipo === "sistema" && b.tipo === "sistema") return a.tela === b.tela;
  if (a.tipo === "jornada" && b.tipo === "jornada") return a.passo === b.passo;
  return false;
}

function passoSugerido(lote: Lote): Passo {
  if (lote.status === "RASCUNHO") return "importar";
  if (lote.status === "BLOQUEADO") return "pendencias";
  if (lote.status === "PRONTO") return "validar";
  return "exportar";
}

function resumir(lote: Lote, lancamentos: Lancamento[]): Resumo {
  return {
    id: lote.id,
    competencia: lote.competencia,
    status: lote.status,
    total: lancamentos.length,
    automaticos: lancamentos.filter((l) => l.status === "AUTO").length,
    pendentes: lancamentos.filter((l) => l.status === "PENDENTE").length,
    manuais: lancamentos.filter((l) => l.status === "MANUAL").length,
    historico_derivado: lancamentos.filter(
      (l) => !l.warnings.includes("HISTORICO_NAO_DERIVADO"),
    ).length,
    blockers: lancamentos.reduce((soma, l) => soma + l.blockers.length, 0),
    warnings: lancamentos.reduce((soma, l) => soma + l.warnings.length, 0),
    valor_total: lancamentos.reduce((soma, l) => soma + l.valor, 0),
  };
}
