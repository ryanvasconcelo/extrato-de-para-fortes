/* Primitivos. Nenhum recebe cor literal: só token semântico do kit. */

import type { MouseEvent, ReactNode } from "react";
import type { StatusLancamento, StatusLote } from "../api/cliente";
import {
  IcoAlert,
  IcoCheckCircle,
  IcoDownload,
  IcoEdit,
  IcoInfo,
  IcoXCircle,
} from "./icones";

export function Botao({
  children,
  onClick,
  tom = "neutro",
  desabilitado,
  tipo = "button",
  tamanho,
  className = "",
}: {
  children: ReactNode;
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void;
  tom?: "primario" | "neutro" | "perigo" | "terciario";
  desabilitado?: boolean;
  tipo?: "button" | "submit";
  tamanho?: "sm" | "lg";
  className?: string;
}) {
  const tons = {
    primario: "btn--primary",
    neutro: "btn--secondary",
    perigo: "btn--danger",
    terciario: "btn--tertiary",
  };
  const tam = tamanho === "sm" ? "btn--sm" : tamanho === "lg" ? "btn--lg" : "";
  return (
    <button
      type={tipo}
      onClick={onClick}
      disabled={desabilitado}
      className={`btn ${tons[tom]} ${tam} ${className}`.trim()}
    >
      {children}
    </button>
  );
}

const ETIQUETAS: Record<
  string,
  { classe: string; icone: ReactNode }
> = {
  PENDENTE: {
    classe: "badge--error",
    icone: <IcoAlert className="i" />,
  },
  AUTO: {
    classe: "badge--brand",
    icone: <IcoCheckCircle className="i" />,
  },
  MANUAL: {
    classe: "badge--warning",
    icone: <IcoEdit className="i" />,
  },
  APROVADO: {
    classe: "badge--success",
    icone: <IcoCheckCircle className="i" />,
  },
  EXPORTADO: {
    classe: "badge--neutral",
    icone: <IcoDownload className="i" />,
  },
  RASCUNHO: {
    classe: "badge--neutral",
    icone: <IcoInfo className="i" />,
  },
  BLOQUEADO: {
    classe: "badge--error",
    icone: <IcoXCircle className="i" />,
  },
  PRONTO: {
    classe: "badge--success",
    icone: <IcoCheckCircle className="i" />,
  },
};

export function Etiqueta({ estado }: { estado: StatusLancamento | StatusLote }) {
  const { classe, icone } = ETIQUETAS[estado] ?? {
    classe: "badge--neutral",
    icone: <IcoInfo className="i" />,
  };
  return (
    <span className={`badge ${classe}`}>
      {icone}
      {estado}
    </span>
  );
}

/** RASCUNHO e BLOQUEADO são lote em curso, não um produto à parte. */
export function loteEmCurso(status: StatusLote): boolean {
  return status === "RASCUNHO" || status === "BLOQUEADO";
}

export function EtiquetaLote({ estado }: { estado: StatusLote }) {
  if (loteEmCurso(estado)) return null;
  return <Etiqueta estado={estado} />;
}

export const ROTULOS: Record<string, string> = {
  CONTA_DEBITO_AUSENTE: "Sem conta de débito: fornecedor não está na base De/Para",
  CONTA_INEXISTENTE: "Conta não existe no plano de contas",
  CONTA_NAO_ANALITICA: "Conta é sintética e não aceita lançamento",
  REGRA_AMBIGUA: "Fornecedor tem mais de uma conta possível no histórico",
  VALOR_INVALIDO: "Valor não é positivo",
  BANCO_NAO_MAPEADO: "Conta corrente sem conta contábil na Base Bancos",
  HISTORICO_NAO_DERIVADO: "Histórico não derivado do Contas a Pagar",
  CENTRO_CUSTO_SUGERIDO: "Centro de custo é sugestão, confirme",
  REGRA_CONFIANCA_MEDIA: "Regra minerada de 1 a 2 meses apenas",
  FORNECEDOR_SEM_DOCUMENTO: "Origem não informou CPF/CNPJ",
  TITULO_REUTILIZADO: "Título do Contas a Pagar usado por mais de um pagamento",
  DIVERGENCIA_TOTAL: "Soma dos lançamentos difere do total do extrato",
};

export function Ocorrencias({
  blockers,
  warnings,
}: {
  blockers: string[];
  warnings: string[];
}) {
  if (!blockers.length && !warnings.length) return null;
  return (
    <ul className="flex flex-wrap gap-1">
      {blockers.map((c) => (
        <li key={c} title={ROTULOS[c] ?? c} className="badge badge--error">
          {c}
        </li>
      ))}
      {warnings.map((c) => (
        <li key={c} title={ROTULOS[c] ?? c} className="badge badge--warning">
          {c}
        </li>
      ))}
    </ul>
  );
}

export function Aviso({
  tom,
  children,
}: {
  tom: "erro" | "aviso" | "ok";
  children: ReactNode;
}) {
  const tons = {
    erro: "alert--error",
    aviso: "alert--warning",
    ok: "alert--success",
  };
  const icones = {
    erro: <IcoXCircle className="i" />,
    aviso: <IcoAlert className="i" />,
    ok: <IcoCheckCircle className="i" />,
  };
  return (
    <div className={`alert ${tons[tom]}`} role="status">
      {icones[tom]}
      <div className="alert__text">{children}</div>
    </div>
  );
}

export const MESES = [
  "janeiro",
  "fevereiro",
  "março",
  "abril",
  "maio",
  "junho",
  "julho",
  "agosto",
  "setembro",
  "outubro",
  "novembro",
  "dezembro",
];

export function formatarCompetencia(mmYYYY: string): string {
  if (!/^\d{6}$/.test(mmYYYY)) return mmYYYY;
  const mes = Number(mmYYYY.slice(0, 2));
  const ano = mmYYYY.slice(2);
  if (mes < 1 || mes > 12) return mmYYYY;
  return `${MESES[mes - 1]} ${ano}`;
}
