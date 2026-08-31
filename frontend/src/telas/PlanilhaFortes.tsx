/* Grade Fortes de 10 colunas. O que a celula grava e o que sai no XLSX
 * (ADR 0011). Editar aqui e excecao de linha: nunca criar_regra. */

import { useEffect, useRef, useState } from "react";
import { api, dinheiro, type Lancamento } from "../api/cliente";
import { BuscaConta } from "../componentes/BuscaConta";

const LINHA_MODELO = [
  "0001",
  "Data",
  "Débito",
  "Crédito",
  " Valor ",
  "Histórico",
  "0001",
  "001",
  "0001",
  "001",
] as const;

const FILIAL = "0001";
const CONSTANTE_H = "001";
const CONSTANTE_I = "0001";
const CONSTANTE_J = "001";

type Campo = "debito" | "credito" | "valor" | "historico" | "centro";

type Edicao = {
  conta_debito?: string;
  conta_credito?: string;
  centro_custo?: string;
  historico?: string;
  valor?: number;
};

export function PlanilhaFortes({
  lancamentos,
  editavel,
  onEditou,
  onErro,
}: {
  lancamentos: Lancamento[];
  editavel: boolean;
  onEditou: () => void;
  onErro: (mensagem: string) => void;
}) {
  return (
    <table className="planilha-fortes">
      <thead>
        <tr>
          {LINHA_MODELO.map((rotulo, i) => (
            <th key={i}>{rotulo}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {lancamentos.map((l) => (
          <Linha
            key={l.id}
            lancamento={l}
            editavel={editavel}
            onEditou={onEditou}
            onErro={onErro}
          />
        ))}
      </tbody>
    </table>
  );
}

function Linha({
  lancamento: l,
  editavel,
  onEditou,
  onErro,
}: {
  lancamento: Lancamento;
  editavel: boolean;
  onEditou: () => void;
  onErro: (mensagem: string) => void;
}) {
  const [campo, setCampo] = useState<Campo | null>(null);

  async function gravar(qual: Campo, edicao: Edicao) {
    setCampo((atual) => (atual === qual ? null : atual));
    try {
      await api.editar(l.id, edicao);
      onEditou();
    } catch (e) {
      onErro((e as Error).message);
    }
  }

  return (
    <tr data-estado={l.status} title={l.favorecido}>
      <td>{l.filial || FILIAL}</td>
      <td>{l.data}</td>
      <td className="celula-conta" onClick={editavel ? () => setCampo("debito") : undefined}>
        {campo === "debito" ? (
          <CampoConta
            inicial={l.conta_debito}
            onSalvar={(codigo) => void gravar("debito", { conta_debito: codigo })}
            onCancelar={() => setCampo(null)}
          />
        ) : (
          l.conta_debito
        )}
      </td>
      <td className="celula-conta" onClick={editavel ? () => setCampo("credito") : undefined}>
        {campo === "credito" ? (
          <CampoConta
            inicial={l.conta_credito}
            onSalvar={(codigo) => void gravar("credito", { conta_credito: codigo })}
            onCancelar={() => setCampo(null)}
          />
        ) : (
          l.conta_credito
        )}
      </td>
      <td className="celula-valor" onClick={editavel ? () => setCampo("valor") : undefined}>
        {campo === "valor" ? (
          <CampoValor
            inicial={l.valor}
            onSalvar={(valor) => void gravar("valor", { valor })}
            onCancelar={() => setCampo(null)}
            onErro={onErro}
          />
        ) : (
          dinheiro(l.valor)
        )}
      </td>
      <td onClick={editavel ? () => setCampo("historico") : undefined}>
        {campo === "historico" ? (
          <CampoTexto
            inicial={l.historico}
            onSalvar={(historico) => void gravar("historico", { historico })}
            onCancelar={() => setCampo(null)}
          />
        ) : (
          l.historico
        )}
      </td>
      <td onClick={editavel ? () => setCampo("centro") : undefined}>
        {campo === "centro" ? (
          <CampoTexto
            inicial={l.centro_custo}
            onSalvar={(centro_custo) => void gravar("centro", { centro_custo })}
            onCancelar={() => setCampo(null)}
          />
        ) : (
          l.centro_custo
        )}
      </td>
      <td>{CONSTANTE_H}</td>
      <td>{CONSTANTE_I}</td>
      <td>{CONSTANTE_J}</td>
    </tr>
  );
}

function CampoTexto({
  inicial,
  onSalvar,
  onCancelar,
}: {
  inicial: string;
  onSalvar: (valor: string) => void;
  onCancelar: () => void;
}) {
  const [rascunho, setRascunho] = useState(inicial);
  const ref = useRef<HTMLInputElement>(null);
  const rascunhoRef = useRef(inicial);
  const cancelou = useRef(false);
  const gravou = useRef(false);

  rascunhoRef.current = rascunho;

  useEffect(() => {
    ref.current?.focus();
    ref.current?.select();
  }, []);

  function confirmar(conectado: boolean) {
    if (cancelou.current || gravou.current) return;
    const atual = rascunhoRef.current;
    if (atual === inicial) {
      if (conectado) onCancelar();
      return;
    }
    gravou.current = true;
    onSalvar(atual);
  }

  return (
    <input
      ref={ref}
      value={rascunho}
      onChange={(e) => setRascunho(e.target.value)}
      onBlur={() => {
        requestAnimationFrame(() => confirmar(!!ref.current?.isConnected));
      }}
      onClick={(e) => e.stopPropagation()}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          confirmar(true);
        } else if (e.key === "Escape") {
          cancelou.current = true;
          onCancelar();
        }
      }}
    />
  );
}

function CampoValor({
  inicial,
  onSalvar,
  onCancelar,
  onErro,
}: {
  inicial: number;
  onSalvar: (valor: number) => void;
  onCancelar: () => void;
  onErro: (mensagem: string) => void;
}) {
  const [rascunho, setRascunho] = useState(inicial.toFixed(2).replace(".", ","));
  const ref = useRef<HTMLInputElement>(null);
  const rascunhoRef = useRef(rascunho);
  const cancelou = useRef(false);
  const gravou = useRef(false);

  rascunhoRef.current = rascunho;

  useEffect(() => {
    ref.current?.focus();
    ref.current?.select();
  }, []);

  function confirmar(conectado: boolean) {
    if (cancelou.current || gravou.current) return;
    const parsed = Number(rascunhoRef.current.replace(",", "."));
    if (!Number.isFinite(parsed)) {
      if (conectado) onErro("Valor inválido.");
      return;
    }
    if (parsed === inicial) {
      if (conectado) onCancelar();
      return;
    }
    gravou.current = true;
    onSalvar(parsed);
  }

  return (
    <input
      ref={ref}
      inputMode="decimal"
      value={rascunho}
      onChange={(e) => setRascunho(e.target.value)}
      onBlur={() => {
        requestAnimationFrame(() => confirmar(!!ref.current?.isConnected));
      }}
      onClick={(e) => e.stopPropagation()}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          confirmar(true);
        } else if (e.key === "Escape") {
          cancelou.current = true;
          onCancelar();
        }
      }}
    />
  );
}

function CampoConta({
  inicial,
  onSalvar,
  onCancelar,
}: {
  inicial: string;
  onSalvar: (codigo: string) => void;
  onCancelar: () => void;
}) {
  const caixa = useRef<HTMLDivElement>(null);
  const termoRef = useRef(inicial);
  const cancelou = useRef(false);
  const gravou = useRef(false);

  useEffect(() => {
    const input = caixa.current?.querySelector("input");
    input?.focus();
    input?.select();
  }, []);

  function ler(): string {
    return (caixa.current?.querySelector("input")?.value ?? termoRef.current).trim();
  }

  function confirmar(codigo: string, conectado: boolean) {
    if (cancelou.current || gravou.current) return;
    const normalizado = codigo.trim();
    if (normalizado === inicial) {
      if (conectado) onCancelar();
      return;
    }
    gravou.current = true;
    onSalvar(normalizado);
  }

  return (
    <div
      ref={caixa}
      onClick={(e) => e.stopPropagation()}
      onChange={(e) => {
        const alvo = e.target;
        if (alvo instanceof HTMLInputElement) termoRef.current = alvo.value;
      }}
      onBlur={(e) => {
        if (e.currentTarget.contains(e.relatedTarget as Node | null)) return;
        requestAnimationFrame(() => confirmar(ler(), !!caixa.current?.isConnected));
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          confirmar(ler(), true);
        } else if (e.key === "Escape") {
          cancelou.current = true;
          onCancelar();
        }
      }}
    >
      <BuscaConta valor={inicial} onEscolher={(codigo) => confirmar(codigo, true)} />
    </div>
  );
}
