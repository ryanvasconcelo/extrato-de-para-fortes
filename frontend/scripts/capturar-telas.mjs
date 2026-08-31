/* Captura as superfícies em claro e escuro e confere o contrato da grade Fortes.
 *
 * Uso: node scripts/capturar-telas.mjs [destino]
 * Requer Vite em :5173 e backend com pelo menos um lote (junho importado, se houver).
 */

import { mkdir } from "node:fs/promises";
import { chromium } from "playwright";

const BASE = process.env.APP_URL ?? "http://localhost:5173";
const destino = process.argv[2] ?? "../docs/telas";

await mkdir(destino, { recursive: true });

const navegador = await chromium.launch({ channel: "chrome" });
const pagina = await navegador.newPage({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
});

await pagina.goto(BASE);
await pagina.waitForSelector("[data-inicio]", { timeout: 15000 });

async function irSistema(nome) {
  await pagina
    .getByRole("navigation", { name: "Sistema" })
    .getByRole("button", { name: new RegExp(`^${nome}`) })
    .click();
}

async function irJornada(aba) {
  await pagina
    .getByRole("navigation", { name: "Jornada" })
    .getByRole("button", { name: new RegExp(`^${aba}`) })
    .click();
  if (aba === "Validar") {
    await pagina.waitForSelector("table.planilha-fortes", { timeout: 15000 });
    if (melhorQtd > 0) {
      await pagina.waitForSelector("table.planilha-fortes tbody tr", { timeout: 15000 });
    }
  } else {
    await pagina.waitForTimeout(600);
  }
}

await irSistema("Histórico");
await pagina.waitForSelector('[data-lista-lotes][data-lista-pronta="true"]', { timeout: 15000 });

const linhas = pagina.locator("[data-lista-lotes] tbody tr");
const n = await linhas.count();
let melhor = -1;
let melhorQtd = -1;
for (let i = 0; i < n; i++) {
  const qtd = Number(await linhas.nth(i).getAttribute("data-lancamentos"));
  if (qtd > melhorQtd) {
    melhorQtd = qtd;
    melhor = i;
  }
}
if (melhor >= 0) {
  const usar = linhas.nth(melhor).getByRole("button", { name: /Usar este lote/ });
  if (await usar.count()) {
    await usar.click();
  }
  await pagina.waitForSelector("[data-wizard]", { timeout: 10000 });
} else {
  console.log("lista de lotes vazia — jornada sem lote; não há PDF sintético nesta fase.");
}

await irSistema("Início");
await pagina.waitForSelector("[data-inicio]");

for (const tema of ["claro", "escuro"]) {
  if (tema === "escuro") {
    await pagina.getByLabel("Alternar tema").click();
  }

  await irSistema("Início");
  await pagina.waitForSelector("[data-inicio]");
  await pagina.screenshot({ path: `${destino}/0-inicio-${tema}.png` });
  console.log(`${destino}/0-inicio-${tema}.png`);

  await irSistema("Conciliar");
  await pagina.waitForSelector("[data-conciliar]");
  await pagina.screenshot({ path: `${destino}/0-conciliar-${tema}.png` });
  console.log(`${destino}/0-conciliar-${tema}.png`);

  await pagina.getByRole("button", { name: "Iniciar" }).click();
  await pagina.waitForSelector("[data-calendario]", { timeout: 5000 });
  await pagina.screenshot({ path: `${destino}/0-calendario-${tema}.png` });
  console.log(`${destino}/0-calendario-${tema}.png`);
  await pagina.keyboard.press("Escape");
  await pagina.waitForTimeout(300);

  await irSistema("Histórico");
  await pagina.waitForSelector("[data-lista-lotes]");
  await pagina.screenshot({ path: `${destino}/0-historico-${tema}.png` });
  console.log(`${destino}/0-historico-${tema}.png`);

  await irSistema("Regras");
  await pagina.waitForSelector("[data-regras]");
  await pagina.waitForTimeout(400);
  await pagina.screenshot({ path: `${destino}/0-regras-${tema}.png` });
  console.log(`${destino}/0-regras-${tema}.png`);

  if (melhor >= 0) {
    await irSistema("Histórico");
    await pagina.waitForSelector("[data-lista-lotes]");
    await pagina
      .locator("[data-lista-lotes] tbody tr")
      .nth(melhor)
      .getByRole("button", { name: /Usar este lote/ })
      .click();
    await pagina.waitForSelector("[data-wizard]", { timeout: 8000 });

    for (const { aba, nome } of [
      { aba: "Importar", nome: "1-importar" },
      { aba: "Pendências", nome: "2-pendencias" },
      { aba: "Validar", nome: "3-validar" },
      { aba: "Exportar", nome: "4-exportar" },
    ]) {
      await irJornada(aba);
      const caminho = `${destino}/${nome}-${tema}.png`;
      await pagina.screenshot({ path: caminho });
      console.log(caminho);
    }
  }
}

if (melhor >= 0) {
  await irJornada("Validar");
  const cabecalhos = await pagina.locator("table.planilha-fortes thead th").allTextContents();
  if (cabecalhos.length !== 10) {
    throw new Error(`Validar deveria ter 10 colunas; veio ${cabecalhos.length}: ${JSON.stringify(cabecalhos)}`);
  }
  if (!cabecalhos.includes(" Valor ")) {
    throw new Error(`Cabeçalho sem ' Valor ' (com espaços): ${JSON.stringify(cabecalhos)}`);
  }
  const criarRegra = pagina.getByRole("checkbox", { name: /criar regra/i });
  if ((await criarRegra.count()) !== 0) {
    throw new Error("Validar não pode ter checkbox Criar regra");
  }
  console.log("ok: Validar tem 10 colunas, crédito visível, sem Criar regra");

  await irJornada("Pendências");
  try {
    await pagina.getByRole("button", { name: "Criar regra" }).first().click({ timeout: 4000 });
    await pagina.waitForTimeout(400);
    await pagina.screenshot({ path: `${destino}/2-pendencias-regra-aberta.png` });
    console.log(`${destino}/2-pendencias-regra-aberta.png`);
  } catch {
    console.log(
      "pendencias-regra-aberta: lote ativo sem pendências — não há PDF sintético nesta fase; pulado.",
    );
  }
}

await navegador.close();
