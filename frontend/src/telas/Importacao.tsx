/* Tela 1: importação dos PDFs do lote ativo. Abrir competência vive na
 * área de competências — aqui só entram os insumos do mês escolhido. */

import { useState } from "react";
import { api, type Lote } from "../api/cliente";
import { IcoCheck, IcoUpload } from "../componentes/icones";
import { Aviso } from "../componentes/primitivos";

interface Props {
  lote: Lote;
  onImportou: () => void;
}

const NECESSARIOS = [
  {
    tipos: ["ITAU_PAGAMENTOS", "ITAU_EXTRATO"],
    rotulo: "Relatório Itaú",
    porque: "define quais linhas existem no mês",
  },
  {
    tipos: ["CONTAS_PAGAR"],
    rotulo: "Contas a Pagar Pagas",
    porque: "de onde sai o Histórico de cada lançamento",
  },
];

export function Importacao({ lote, onImportou }: Props) {
  const [enviando, setEnviando] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [sobre, setSobre] = useState(false);

  async function enviar(arquivos: FileList | null) {
    if (!arquivos) return;
    setErro(null);
    for (const arquivo of Array.from(arquivos)) {
      setEnviando(arquivo.name);
      try {
        await api.importar(lote.id, arquivo);
      } catch (e) {
        setErro(`${arquivo.name}: ${(e as Error).message}`);
      }
    }
    setEnviando(null);
    onImportou();
  }

  const importados = lote.arquivos ?? [];
  const tipos = new Set(importados.map((a) => a.tipo));
  const aceitaArquivo = lote.status !== "APROVADO" && lote.status !== "EXPORTADO";

  return (
    <div className="importacao">
      <header className="competencias__cabeca">
        <h1 className="ckp-h2">Importar</h1>
        <p className="ckp-body-sm competencias__lede">
          Suba os dois PDFs deste mês: o relatório Itaú diz quais linhas
          existem; o Contas a Pagar é de onde sai o Histórico de cada
          lançamento.
        </p>
      </header>

      <section
        className={`importacao__solta ${aceitaArquivo ? "" : "is-bloqueada"} ${sobre ? "is-sobre" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          if (aceitaArquivo) setSobre(true);
        }}
        onDragLeave={() => setSobre(false)}
        onDrop={(e) => {
          e.preventDefault();
          setSobre(false);
          if (aceitaArquivo) void enviar(e.dataTransfer.files);
        }}
      >
        <IcoUpload className="i importacao__solta-icone" />
        <p className="ckp-body-sm" style={{ margin: 0 }}>
          Arraste os PDFs ou{" "}
          <label className="importacao__escolher">
            escolha os arquivos
            <input
              type="file"
              multiple
              accept="application/pdf"
              disabled={!aceitaArquivo || !!enviando}
              className="sr-only"
              onChange={(e) => void enviar(e.target.files)}
            />
          </label>
        </p>
        <p className="ckp-caption">
          O layout é detectado pelo conteúdo: relatório Itaú de pagamentos,
          extrato de conta corrente ou Contas a Pagar Pagas.
        </p>
        {enviando && (
          <p className="ckp-body-sm" style={{ color: "var(--text-brand)", margin: 0 }}>
            Extraindo {enviando} por coordenada…
          </p>
        )}
        {!aceitaArquivo && (
          <p className="ckp-caption">
            Lote {lote.status.toLowerCase()}: não aceita novo PDF.
          </p>
        )}
      </section>

      {erro && <Aviso tom="erro">{erro}</Aviso>}

      <section className="card">
        <div className="card__body">
          <h2 className="ckp-h4" style={{ margin: "0 0 var(--ckp-space-4)" }}>
            Insumos do mês
          </h2>
          <ul className="importacao__insumos">
            {NECESSARIOS.map((necessario) => {
              const presentes = importados.filter((a) =>
                necessario.tipos.includes(a.tipo),
              );
              const ok = presentes.length > 0;
              return (
                <li key={necessario.rotulo} className="importacao__insumo">
                  <span
                    className={`importacao__marca ${ok ? "is-ok" : ""}`}
                    aria-hidden
                  >
                    {ok ? <IcoCheck className="i" /> : "—"}
                  </span>
                  <div>
                    <div className="ckp-body-sm" style={{ fontWeight: 600 }}>
                      {necessario.rotulo}
                    </div>
                    <div className="ckp-caption">{necessario.porque}</div>
                  </div>
                  <div className="ckp-caption importacao__insumo-meta">
                    {ok
                      ? presentes
                          .map((a) => `${a.tipo} · ${a.linhas_lidas} linha(s)`)
                          .join(" | ")
                      : "não importado"}
                  </div>
                </li>
              );
            })}
          </ul>
          {importados.length > 0 && !tipos.has("CONTAS_PAGAR") && (
            <div style={{ marginTop: "var(--ckp-space-4)" }}>
              <Aviso tom="aviso">
                Sem o Contas a Pagar Pagas nenhum Histórico é derivado: todas as
                linhas sairiam com aviso e texto genérico.
              </Aviso>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
