/* Crédito do rodapé + tag de versão. A versão é a do package.json do frontend. */

import pkg from "../../package.json" with { type: "json" };
import { IcoHeart } from "./icones";

const SITE = "https://ryanvasconcelo.com.br/";

export function CreditoRodape({ className }: { className: string }) {
  return (
    <footer className={className}>
      <p>
        Feito com <IcoHeart className="casca__coracao" /> por{" "}
        <a href={SITE} target="_blank" rel="noreferrer">
          Ryan Vasconcelo
        </a>{" "}
        © 2026 Projecont.
      </p>
      <span className="casca__versao"><b>Versão:</b> {pkg.version}</span>
    </footer>
  );
}
