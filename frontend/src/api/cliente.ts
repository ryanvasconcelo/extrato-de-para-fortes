/* Cliente HTTP. O frontend nao parseia arquivo nem escolhe conta: toda decisao
 * contabil vem do backend (ADR 0001). Aqui so ha transporte e tipos. */

export type StatusLote =
  | "RASCUNHO"
  | "BLOQUEADO"
  | "PRONTO"
  | "APROVADO"
  | "EXPORTADO";

export type StatusLancamento =
  | "PENDENTE"
  | "AUTO"
  | "MANUAL"
  | "APROVADO"
  | "EXPORTADO";

export interface ArquivoDoLote {
  nome: string;
  tipo: string;
  linhas_lidas: number;
}

export interface Lote {
  id: number;
  competencia: string;
  status: StatusLote;
  criado_em: string;
  lancamentos: number;
  arquivos: ArquivoDoLote[];
}

export interface Resumo {
  id: number;
  competencia: string;
  status: StatusLote;
  total: number;
  automaticos: number;
  pendentes: number;
  manuais: number;
  historico_derivado: number;
  blockers: number;
  warnings: number;
  valor_total: number;
}

export interface Lancamento {
  id: number;
  data: string;
  favorecido: string;
  documento: string;
  filial: string;
  conta_debito: string;
  conta_debito_descricao: string;
  conta_credito: string;
  valor: number;
  historico: string;
  centro_custo: string;
  status: StatusLancamento;
  blockers: string[];
  warnings: string[];
}

export interface Pendencia {
  fornecedor: string;
  documento: string;
  linhas: number;
  valor_total: number;
  motivos: string[];
  lancamento_ids: number[];
  mensagens: string[];
}

export interface Conta {
  codigo: string;
  codigo_dv: string;
  descricao: string;
}

export interface ImportacaoFeita {
  tipo: string;
  linhas_lidas: number;
  resumo: Resumo;
}

export interface Regra {
  id: number;
  fornecedor: string;
  documento: string;
  conta_debito: string;
  centro_custo: string;
  origem: string;
  confianca: string;
  ativo: boolean;
}

export class ErroApi extends Error {}
export class ErroSessao extends ErroApi {}

export interface Usuario {
  id: number;
  email: string;
  nome: string;
  modo: "ligado" | "desligado";
}

export interface ProvedoresAuth {
  ligado: boolean;
  google: boolean;
  microsoft: boolean;
}

async function pedir<T>(caminho: string, init?: RequestInit): Promise<T> {
  const resposta = await fetch(`/api${caminho}`, {
    credentials: "same-origin",
    ...init,
  });
  if (resposta.status === 401) {
    throw new ErroSessao((await corpoDetalhe(resposta)) || "Faça login.");
  }
  if (!resposta.ok) {
    // O backend responde 409/422 com detail em portugues, escrito para o
    // contador ler. Repassar essa mensagem em vez de inventar outra.
    throw new ErroApi(await detalhe(resposta, caminho));
  }
  return resposta.json() as Promise<T>;
}

async function detalhe(resposta: Response, caminho: string): Promise<string> {
  const corpo = await resposta.json().catch(() => null);
  return corpo?.detail ?? `Falha ${resposta.status} em ${caminho}`;
}

async function corpoDetalhe(resposta: Response): Promise<string | null> {
  const corpo = await resposta.json().catch(() => null);
  return typeof corpo?.detail === "string" ? corpo.detail : null;
}

export const api = {
  eu: () => pedir<Usuario>("/auth/eu"),
  provedores: () => pedir<ProvedoresAuth>("/auth/provedores"),
  sair: () => pedir<{ ok: boolean }>("/auth/sair", { method: "POST" }),

  saude: () =>
    pedir<{ plano_contas: number; regras: number; regras_ativas: number }>(
      "/saude",
    ),

  lotes: () => pedir<Lote[]>("/lotes"),

  criarLote: (competencia: string) =>
    pedir<Lote>(`/lotes?competencia=${encodeURIComponent(competencia)}`, {
      method: "POST",
    }),

  importar: (loteId: number, arquivo: File) => {
    const corpo = new FormData();
    corpo.append("arquivo", arquivo);
    return pedir<ImportacaoFeita>(`/lotes/${loteId}/arquivos`, {
      method: "POST",
      body: corpo,
    });
  },

  lancamentos: (loteId: number, filtro?: { status?: string }) => {
    const busca = filtro?.status ? `?status=${filtro.status}` : "";
    return pedir<Lancamento[]>(`/lotes/${loteId}/lancamentos${busca}`);
  },

  pendencias: (loteId: number) =>
    pedir<Pendencia[]>(`/lotes/${loteId}/pendencias`),

  editar: (
    lancamentoId: number,
    edicao: {
      conta_debito?: string;
      conta_credito?: string;
      centro_custo?: string;
      historico?: string;
      valor?: number;
      criar_regra?: boolean;
    },
  ) =>
    pedir<Resumo>(`/lancamentos/${lancamentoId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ criar_regra: false, ...edicao }),
    }),

  regras: () => pedir<Regra[]>("/regras"),

  criarRegra: (regra: {
    fornecedor_nome: string;
    documento: string;
    conta_debito: string;
    centro_custo: string;
  }) =>
    pedir<{ regra_id: number; lotes_reprocessados: Resumo[] }>("/regras", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(regra),
    }),

  buscarContas: (q: string) =>
    pedir<Conta[]>(`/plano-contas?q=${encodeURIComponent(q)}`),

  aprovar: (loteId: number) =>
    pedir<{ id: number; status: StatusLote }>(`/lotes/${loteId}/aprovar`, {
      method: "POST",
    }),
};

/** Download de XLSX. Fora de `pedir` porque a resposta e binaria, nao JSON. */
export async function baixarPlanilha(
  caminho: string,
  nomeSugerido: string,
): Promise<void> {
  const resposta = await fetch(`/api${caminho}`, { credentials: "same-origin" });
  if (resposta.status === 401) {
    throw new ErroSessao("Faça login.");
  }
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null);
    throw new ErroApi(corpo?.detail ?? `Falha ${resposta.status}`);
  }
  const blob = await resposta.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = nomeSugerido;
  link.click();
  URL.revokeObjectURL(url);
}

export const dinheiro = (valor: number) =>
  valor.toLocaleString("pt-BR", { minimumFractionDigits: 2 });
