/* Ícones do kit ClickIP: grade 24, traço 1,5, pontas arredondadas, sem preenchimento. */

import type { ReactNode } from "react";

const TRACO = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.5,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function Icone({
  children,
  className = "i",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <svg className={className} aria-hidden {...TRACO}>
      {children}
    </svg>
  );
}

export const IcoSearch = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <circle cx="11" cy="11" r="7" />
    <path d="M20 20l-3.5-3.5" />
  </Icone>
);

export const IcoCalendar = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <rect x="3" y="5" width="18" height="16" rx="2" />
    <path d="M3 10h18M8 3v4M16 3v4" />
  </Icone>
);

export const IcoUpload = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M12 21V9m0 0L8 13m4-4l4 4M4 7V5a2 2 0 012-2h12a2 2 0 012 2v2" />
  </Icone>
);

export const IcoDownload = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
  </Icone>
);

export const IcoCheck = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M4 12l6 6L20 6" />
  </Icone>
);

export const IcoAlert = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M12 4l9 16H3z" />
    <path d="M12 10v4M12 17h.01" />
  </Icone>
);

export const IcoEdit = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M4 20h4L20 8l-4-4L4 16v4z" />
  </Icone>
);

export const IcoPlus = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M12 5v14M5 12h14" />
  </Icone>
);

export const IcoMoon = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z" />
  </Icone>
);

export const IcoSun = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 3v2M12 19v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M3 12h2M19 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" />
  </Icone>
);

export const IcoInfo = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5M12 8h.01" />
  </Icone>
);

export const IcoClose = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M18 6L6 18M6 6l12 12" />
  </Icone>
);

export const IcoDoc = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z" />
    <path d="M14 3v5h5" />
  </Icone>
);

export const IcoFilter = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M3 5h18l-7 8v6l-4 2v-8z" />
  </Icone>
);

export const IcoCheckCircle = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <circle cx="12" cy="12" r="9" />
    <path d="M8 12.5l2.5 2.5L16 9" />
  </Icone>
);

export const IcoXCircle = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <circle cx="12" cy="12" r="9" />
    <path d="M15 9l-6 6M9 9l6 6" />
  </Icone>
);

export const IcoHome = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M4 10.5L12 4l8 6.5V20a1 1 0 01-1 1h-5v-6H10v6H5a1 1 0 01-1-1z" />
  </Icone>
);

export const IcoHistory = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M4 12a8 8 0 118-8" />
    <path d="M4 4v4h4M12 8v4l3 2" />
  </Icone>
);

export const IcoBook = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M5 4.5A1.5 1.5 0 016.5 3H19v16H6.5A1.5 1.5 0 005 17.5z" />
    <path d="M5 17.5A1.5 1.5 0 016.5 16H19" />
  </Icone>
);

export const IcoHeart = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M12 19s-7-4.35-7-9.2A4 4 0 0112 7a4 4 0 017 2.8C19 14.65 12 19 12 19z" />
  </Icone>
);

export const IcoChevronLeft = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M15 5l-7 7 7 7" />
  </Icone>
);

export const IcoChevronRight = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M9 5l7 7-7 7" />
  </Icone>
);

export const IcoPlay = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M8 6l12 6-12 6z" />
  </Icone>
);

export const IcoLogout = (p: { className?: string }) => (
  <Icone className={p.className ?? "i"}>
    <path d="M9 4H6a2 2 0 00-2 2v12a2 2 0 002 2h3" />
    <path d="M10 12h10m0 0l-3-3m3 3l-3 3" />
  </Icone>
);

/** Marcas oficiais dos provedores: tinta da marca, não token do kit. */
export function MarcaGoogle({ className = "porta__marca" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden>
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  );
}

export function MarcaMicrosoft({ className = "porta__marca" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 23 23" aria-hidden>
      <rect fill="#F35325" x="1" y="1" width="10" height="10" />
      <rect fill="#81BC06" x="12" y="1" width="10" height="10" />
      <rect fill="#05A6F0" x="1" y="12" width="10" height="10" />
      <rect fill="#FFBA08" x="12" y="12" width="10" height="10" />
    </svg>
  );
}
