/* Porta de entrada: cartaz ConFast, ações à direita. Sem a casca vazia. */

import { CreditoRodape } from "../componentes/CreditoRodape";
import { IcoMoon, IcoSun, MarcaGoogle, MarcaMicrosoft } from "../componentes/icones";
import { MarcaClickip } from "../componentes/MarcaClickip";
import { Aviso } from "../componentes/primitivos";

export interface Provedores {
  ligado: boolean;
  google: boolean;
  microsoft: boolean;
}

const ERROS: Record<string, string> = {
  sessao: "A entrada expirou. Toque de novo em Google ou Outlook.",
  provedor: "O Google ou a Microsoft não confirmaram o login. Tente outra vez.",
  sem_email: "Essa conta não enviou um e-mail. Use outra, ou peça ao administrador.",
  nao_autorizado: "Esse e-mail não tem permissão neste conciliador.",
};

export function Entrar({
  provedores,
  erro,
  tema,
  onTema,
}: {
  provedores: Provedores | null;
  erro: string | null;
  tema: "claro" | "escuro";
  onTema: () => void;
}) {
  const mensagem = erro ? ERROS[erro] ?? "Não foi possível entrar." : null;
  const google = provedores?.google ?? false;
  const microsoft = provedores?.microsoft ?? false;
  const algum = google || microsoft;

  return (
    <div className="porta" data-entrar>
      <header className="porta__barra">
        <MarcaClickip className="porta__clickip" />
        <button
          type="button"
          className="btn btn--secondary btn--icon btn--tema"
          onClick={onTema}
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

        <div className="porta__miolo" id="conteudo">
        <div className="porta__texto">
          <p className="ckp-overline">Escritório · ClickIP</p>
          <h1 className="porta__titulo">
            Con<i>Fast</i>
          </h1>
          <p className="porta__tag">Assistente de conciliação</p>
          <p className="porta__lede">
            Entra com a conta Google ou Outlook do escritório. Não tem senha
            daqui: o provedor confirma e você volta para o conciliador.
            Se o Google mostrar várias contas, escolha exatamente o e-mail
            autorizado — não a conta que o Chrome usa por padrão.
          </p>
          {mensagem ? <Aviso tom="erro">{mensagem}</Aviso> : null}
        </div>

        <div className="porta__acoes">
          {google ? (
            <a className="btn porta__btn" href="/api/auth/entrar/google">
              <MarcaGoogle />
              Continuar com Google
            </a>
          ) : null}
          {microsoft ? (
            <a className="btn porta__btn" href="/api/auth/entrar/microsoft">
              <MarcaMicrosoft />
              Continuar com Outlook
            </a>
          ) : null}
          {provedores && !algum ? (
            <p className="porta__vazio">
              Falta configurar os clientes OAuth no backend.
            </p>
          ) : null}
        </div>
      </div>

      <CreditoRodape className="porta__credito" />
    </div>
  );
}
