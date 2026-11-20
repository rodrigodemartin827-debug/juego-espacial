// Genera, a partir de iconos.mjs y arte.mjs (la única fuente de verdad):
//
//   1. un .svg por icono en  src/client/UI/Assets/IconSVGs/   (trazo y relleno blancos, 128×128)
//   2. un .svg por pieza de arte en  src/client/UI/Assets/ArteSVGs/   (a color)
//   3. los .png con fondo transparente: iconos a 128×128 en IconPNGs/ y arte a 256×256 en ArtePNGs/
//      (son los archivos que se suben a Roblox; ver src/client/UI/Modules/Iconos/IdsIconos.luau)
//   4. el sprite <svg> que va incrustado en el preview (src/client/UI/preview_ui_completa.html), entre las
//      marcas <!-- ICONOS:INICIO --> y <!-- ICONOS:FIN -->, para que el preview y los archivos sean idénticos
//   5. la lista de nombres en IdsIconos.luau, CONSERVANDO los IDs que ya se hayan pegado
//
// Uso, desde la raíz del repositorio (necesita Node 18+ y Playwright con Chromium):
//     node herramientas/iconos_ui/generar.mjs
//     (si Playwright está instalado de forma global: NODE_PATH=$(npm root -g) node herramientas/iconos_ui/generar.mjs)
//     node herramientas/iconos_ui/generar.mjs --sin-png      (solo SVG, sprite y lista; no abre el navegador)

import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { ICONOS, ATRIBUTOS_ICONO } from "./iconos.mjs";
import { ARTE } from "./arte.mjs";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const UI = path.join(RAIZ, "src/client/UI");
const DIR = {
	iconSvg: path.join(UI, "Assets/IconSVGs"),
	arteSvg: path.join(UI, "Assets/ArteSVGs"),
	iconPng: path.join(UI, "Assets/IconPNGs"),
	artePng: path.join(UI, "Assets/ArtePNGs"),
};
const PREVIEW = path.join(UI, "preview_ui_completa.html");
const IDS = path.join(UI, "Modules/Iconos/IdsIconos.luau");
const sinPng = process.argv.includes("--sin-png");

// Quita sangrías y saltos de línea sobrantes de un fragmento SVG.
const compacto = (s) =>
	s
		.split("\n")
		.map((l) => l.trim())
		.filter(Boolean)
		.join("");

// SVG de archivo de un icono: `currentColor` pasa a blanco para teñirlo en Roblox con ImageColor3.
function svgIcono(nombre) {
	const cuerpo = compacto(ICONOS[nombre]).replaceAll("currentColor", "#FFFFFF");
	const atributos = ATRIBUTOS_ICONO.replaceAll("currentColor", "#FFFFFF");
	return `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" ${atributos}>\n<!-- ${nombre} · Juego espacial · generado por herramientas/iconos_ui/generar.mjs -->\n${cuerpo}\n</svg>\n`;
}

function svgArte(nombre) {
	return `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">\n<!-- ${nombre} · Juego espacial · generado por herramientas/iconos_ui/generar.mjs -->\n${compacto(ARTE[nombre])}\n</svg>\n`;
}

// Sprite para el preview: <symbol id="i-..."> (iconos) y <symbol id="a-..."> (arte).
function sprite() {
	const iconos = Object.keys(ICONOS)
		.map((n) => `<symbol id="i-${n}" ${ATRIBUTOS_ICONO}>${compacto(ICONOS[n])}</symbol>`)
		.join("\n");
	const arte = Object.keys(ARTE)
		.map((n) => `<symbol id="a-${n}" viewBox="0 0 128 128">${compacto(ARTE[n])}</symbol>`)
		.join("\n");
	// Sin display:none: los degradados de dentro de un <symbol> no se pintan si el sprite está oculto así.
	return `<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true">\n${iconos}\n${arte}\n</svg>`;
}

function escribirSiCambia(ruta, contenido) {
	const previo = fs.existsSync(ruta) ? fs.readFileSync(ruta, "utf8") : null;
	if (previo !== contenido) {
		fs.writeFileSync(ruta, contenido);
		return true;
	}
	return false;
}

// Mete el sprite en el preview, entre sus marcas.
function actualizarPreview() {
	if (!fs.existsSync(PREVIEW)) {
		console.log("  (todavía no hay preview; se omite el sprite)");
		return;
	}
	const html = fs.readFileSync(PREVIEW, "utf8");
	const ini = "<!-- ICONOS:INICIO -->";
	const fin = "<!-- ICONOS:FIN -->";
	const a = html.indexOf(ini);
	const b = html.indexOf(fin);
	if (a < 0 || b < a) throw new Error("el preview no tiene las marcas ICONOS:INICIO / ICONOS:FIN");
	const nuevo = html.slice(0, a + ini.length) + "\n" + sprite() + "\n" + html.slice(b);
	console.log(escribirSiCambia(PREVIEW, nuevo) ? "  preview: sprite actualizado" : "  preview: sin cambios");
}

// Lista de nombres en IdsIconos.luau, conservando los IDs ya pegados.
function actualizarIds() {
	const previos = {};
	if (fs.existsSync(IDS)) {
		for (const m of fs.readFileSync(IDS, "utf8").matchAll(/^\s*([a-z0-9_]+)\s*=\s*"([^"]*)"/gm)) previos[m[1]] = m[2];
	}
	const fila = (n) => `\t${n} = "${previos[n] ?? ""}",`;
	const contenido = `--!strict
--[[
	IdsIconos: ID de Roblox de cada icono y de cada pieza de arte de la interfaz.

	ESTE ARCHIVO LO REESCRIBE herramientas/iconos_ui/generar.mjs (conserva los IDs que ya tenga). Para añadir
	un icono, dibújalo en herramientas/iconos_ui/iconos.mjs (o arte.mjs) y vuelve a ejecutar el generador.

	Cómo rellenar los IDs (una vez, y cada vez que cambie un icono):
	  1. En Studio: View > Asset Manager > Bulk Import, y elige todos los PNG de
	     src/client/UI/Assets/IconPNGs y src/client/UI/Assets/ArtePNGs (súbelos al GRUPO del juego).
	  2. Clic derecho en cada imagen > Copy ID, y pégalo aquí como "rbxassetid://<número>".

	Mientras un ID esté vacío, IconBuilder dibuja en su lugar un marcador discreto (un rombo con el color del
	icono) y avisa una sola vez por la consola de qué iconos faltan. Nunca se ve un hueco vacío.
	-- TODO: Subir iconos y reemplazar los assetId vacíos.
]]

local IdsIconos = {}

-- Iconos de una sola tinta (blancos; se tiñen con ImageColor3). Origen: Assets/IconPNGs/<nombre>.png
IdsIconos.Iconos = {
${Object.keys(ICONOS).map(fila).join("\n")}
} :: { [string]: string }

-- Arte a color (objetos, criaturas, planetas, tienda). Origen: Assets/ArtePNGs/<nombre>.png
IdsIconos.Arte = {
${Object.keys(ARTE).map(fila).join("\n")}
} :: { [string]: string }

return IdsIconos
`;
	console.log(escribirSiCambia(IDS, contenido) ? "  IdsIconos.luau actualizado" : "  IdsIconos.luau sin cambios");
}

async function generarPng() {
	// require (y no import) para que también valga un Playwright instalado de forma global (NODE_PATH).
	const { chromium } = createRequire(import.meta.url)("playwright");
	const navegador = await chromium.launch();
	const pagina = await navegador.newPage({ deviceScaleFactor: 1 });
	const trabajos = [
		...Object.keys(ICONOS).map((n) => [path.join(DIR.iconPng, `${n}.png`), svgIcono(n), 128]),
		...Object.keys(ARTE).map((n) => [path.join(DIR.artePng, `${n}.png`), svgArte(n), 256]),
	];
	for (const [ruta, svg, lado] of trabajos) {
		await pagina.setViewportSize({ width: lado, height: lado });
		const grande = svg.replace(/width="128" height="128"/, `width="${lado}" height="${lado}"`);
		await pagina.setContent(
			`<html><body style="margin:0;background:transparent">${grande}</body></html>`,
		);
		await pagina.screenshot({ path: ruta, omitBackground: true, clip: { x: 0, y: 0, width: lado, height: lado } });
	}
	await navegador.close();
	console.log(`  ${trabajos.length} PNG generados`);
}

// ===== Principal =====
for (const d of Object.values(DIR)) fs.mkdirSync(d, { recursive: true });
fs.mkdirSync(path.dirname(IDS), { recursive: true });

let n = 0;
for (const nombre of Object.keys(ICONOS)) n += escribirSiCambia(path.join(DIR.iconSvg, `${nombre}.svg`), svgIcono(nombre)) ? 1 : 0;
for (const nombre of Object.keys(ARTE)) n += escribirSiCambia(path.join(DIR.arteSvg, `${nombre}.svg`), svgArte(nombre)) ? 1 : 0;
console.log(`Iconos: ${Object.keys(ICONOS).length} · Arte: ${Object.keys(ARTE).length} · SVG cambiados: ${n}`);

// Borra los archivos de iconos que ya no existen en la fuente.
for (const [dir, lista, ext] of [
	[DIR.iconSvg, ICONOS, ".svg"],
	[DIR.arteSvg, ARTE, ".svg"],
	[DIR.iconPng, ICONOS, ".png"],
	[DIR.artePng, ARTE, ".png"],
]) {
	for (const f of fs.readdirSync(dir)) {
		if (f.endsWith(ext) && !(path.basename(f, ext) in lista)) {
			fs.unlinkSync(path.join(dir, f));
			console.log(`  borrado ${path.relative(RAIZ, path.join(dir, f))}`);
		}
	}
}

actualizarIds();
actualizarPreview();
if (!sinPng) await generarPng();
