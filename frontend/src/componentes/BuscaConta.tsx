/* Busca no plano de contas. São 1.516 contas analíticas: combo com filtro no
 * servidor, nunca <select> com tudo carregado (RF-04.4). */

import { useEffect, useRef, useState } from "react";
import { api, type Conta } from "../api/cliente";

export function BuscaConta({
  valor,
  onEscolher,
  id,
}: {
  valor: string;
  onEscolher: (codigo: string) => void;
  id?: string;
}) {
  const [termo, setTermo] = useState(valor);
  const [opcoes, setOpcoes] = useState<Conta[]>([]);
  const [aberto, setAberto] = useState(false);
  const digitado = useRef(false);

  useEffect(() => {
    if (!aberto) return;
    const id = setTimeout(() => {
      api.buscarContas(termo).then(setOpcoes).catch(() => setOpcoes([]));
    }, 180);
    return () => clearTimeout(id);
  }, [termo, aberto]);

  return (
    <div className="relative">
      <input
        value={termo}
        onChange={(e) => {
          digitado.current = true;
          setTermo(e.target.value);
          setAberto(true);
        }}
        onFocus={() => setAberto(true)}
        onBlur={() => setTimeout(() => setAberto(false), 150)}
        placeholder="código ou descrição da conta"
        className="input input--mono"
        id={id}
      />
      {aberto && opcoes.length > 0 && (
        <ul className="menu busca-conta__lista" role="listbox">
          {opcoes.map((c) => (
            <li key={c.codigo}>
              <button
                type="button"
                role="option"
                className="menu__item"
                onMouseDown={() => {
                  onEscolher(c.codigo);
                  setTermo(c.codigo);
                  setAberto(false);
                }}
              >
                <span className="busca-conta__opcao">
                  <span className="ckp-mono">{c.codigo_dv}</span>
                  <span className="ckp-caption">{c.descricao}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
