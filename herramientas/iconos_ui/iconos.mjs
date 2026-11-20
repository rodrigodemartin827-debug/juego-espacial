// Iconos de la interfaz: fuente única de verdad.
//
// Cada icono es el CONTENIDO de un <svg viewBox="0 0 128 128"> dibujado con `currentColor`:
//   - en el preview HTML se tiñe con CSS (color),
//   - al exportar a archivo (generar.mjs) `currentColor` pasa a blanco (#FFFFFF), y en Roblox se tiñe con
//     ImageLabel.ImageColor3 (que multiplica: blanco × color = color).
//
// Estilo común (lo pone el contenedor): sin relleno, trazo de 8 unidades, puntas y uniones redondeadas.
// 8 unidades sobre 128 son unos 1,5-2 px cuando el icono se ve a 24-32 px, que es su tamaño en pantalla.
// Los iconos de estadística se ven a 18 px y por eso usan trazos de 9-11.
//
// Los detalles secundarios van con opacidad (0,35-0,7) para dar profundidad con un solo color.

const R = (n) => Math.round(n * 100) / 100;

// Estrella de `puntas` puntas centrada en (cx, cy).
function estrella(cx, cy, radioExt, radioInt, puntas = 5, giro = -90) {
	const p = [];
	for (let i = 0; i < puntas * 2; i++) {
		const r = i % 2 === 0 ? radioExt : radioInt;
		const a = ((giro + (i * 180) / puntas) * Math.PI) / 180;
		p.push(`${R(cx + r * Math.cos(a))} ${R(cy + r * Math.sin(a))}`);
	}
	return `M${p.join(" L")} Z`;
}

// Engranaje de `dientes` dientes.
function engranaje(cx, cy, radioExt, radioRaiz, dientes) {
	const p = [];
	const paso = 360 / dientes;
	for (let i = 0; i < dientes; i++) {
		const a = i * paso - 90;
		const puntos = [
			[radioRaiz, a - paso * 0.36],
			[radioExt, a - paso * 0.2],
			[radioExt, a + paso * 0.2],
			[radioRaiz, a + paso * 0.36],
		];
		for (const [r, g] of puntos) {
			const rad = (g * Math.PI) / 180;
			p.push(`${R(cx + r * Math.cos(rad))} ${R(cy + r * Math.sin(rad))}`);
		}
	}
	return `M${p.join(" L")} Z`;
}

// Rayos de un estallido: líneas desde r1 hasta r2 (alternando largos y cortos).
function rayos(cx, cy, r1, r2, r2corto, n, giro = -90) {
	let d = "";
	for (let i = 0; i < n; i++) {
		const a = ((giro + (i * 360) / n) * Math.PI) / 180;
		const fin = i % 2 === 0 ? r2 : r2corto;
		d += `M${R(cx + r1 * Math.cos(a))} ${R(cy + r1 * Math.sin(a))} L${R(cx + fin * Math.cos(a))} ${R(cy + fin * Math.sin(a))} `;
	}
	return d.trim();
}

// Atajos de estilo.
const F = (o) => `fill="currentColor" fill-opacity="${o}"`; // relleno tenue
const LLENO = `fill="currentColor" stroke="none"`;
const D = (o) => `opacity="${o}"`;

// Escudo base de las insignias de rango.
const ESCUDO = "M64 10 L106 25 V62 C106 89 88 108 64 119 C40 108 22 89 22 62 V25 Z";
const ESCUDO_INT = "M64 22 L95 33 V62 C95 83 82 98 64 107 C46 98 33 83 33 62 V33 Z";

export const ICONOS = {
	// =================================================================================================
	// BARRA LATERAL (9)
	// =================================================================================================

	// Personaje: hexágono (ficha) con busto dentro; los hombros nacen del borde inferior del hexágono.
	sidebar_personaje: `
		<path d="M64 10 L110 37 V91 L64 118 L18 91 V37 Z" ${F(0.1)}/>
		<circle cx="64" cy="52" r="16"/>
		<path d="M36 102 C38 84 50 77 64 77 C78 77 90 84 92 102" ${F(0.35)}/>`,

	// Inventario: cofre con la tapa abierta hacia atrás, bisagra marcada y una rejilla 2×2 de objetos dentro.
	sidebar_inventario: `
		<path d="M26 46 L32 12 H96 L102 46" ${F(0.14)}/>
		<path d="M46 26 H82" stroke-width="5" ${D(0.55)}/>
		<g ${LLENO}>
			<rect x="38" y="36" width="22" height="14" rx="3" opacity=".75"/><rect x="68" y="36" width="22" height="14" rx="3" opacity=".75"/>
			<rect x="34" y="50" width="26" height="14" rx="3"/><rect x="68" y="50" width="26" height="14" rx="3"/>
		</g>
		<path d="M20 46 H108"/>
		<path d="M14 64 H114 V102 L104 112 H24 L14 102 Z" ${F(0.16)}/>
		<path d="M14 84 H54 M74 84 H114" stroke-width="5" ${D(0.6)}/>
		<rect x="54" y="72" width="20" height="22" rx="4" ${LLENO}/>`,

	// Poderes: estallido (supernova): estrella de 5 puntas con núcleo y 8 rayos alrededor.
	sidebar_poderes: `
		<path d="${estrella(64, 64, 34, 15)}" ${F(0.22)}/>
		<circle cx="64" cy="64" r="7" ${LLENO}/>
		<path d="${rayos(64, 64, 45, 60, 54, 8, -67.5)}" stroke-width="7"/>`,

	// Tripulación: dos astronautas (casco con visor y hombros) y un + entre ellos.
	sidebar_clan: `
		<circle cx="36" cy="48" r="16" ${F(0.12)}/>
		<rect x="27" y="42" width="18" height="10" rx="4" ${LLENO}/>
		<path d="M10 106 C12 86 22 76 36 76 C50 76 60 86 62 106"/>
		<circle cx="92" cy="48" r="16" ${F(0.12)}/>
		<rect x="83" y="42" width="18" height="10" rx="4" ${LLENO}/>
		<path d="M66 106 C68 86 78 76 92 76 C106 76 116 86 118 106"/>
		<path d="M64 14 V34 M54 24 H74" stroke-width="7"/>`,

	// Ranked: podio de tres alturas (2º-1º-3º) con corona sobre el primero.
	sidebar_ranked: `
		<path d="M14 112 V68 H47 V48 H81 V82 H114 V112 Z" ${F(0.14)}/>
		<path d="M47 68 V112 M81 82 V112" stroke-width="6" ${D(0.7)}/>
		<path d="M64 62 V78" stroke-width="6" ${D(0.7)}/>
		<path d="M49 38 L52 16 L59 26 L64 11 L69 26 L76 16 L79 38 Z" ${LLENO}/>`,

	// Índice: libro abierto con líneas de texto y una lupa encima.
	sidebar_indice: `
		<path d="M64 58 C52 50 34 47 12 49 V106 C34 104 52 107 64 115 C76 107 94 104 116 106 V49 C108 48 100 48 94 49" ${F(0.1)}/>
		<path d="M64 58 V115"/>
		<path d="M22 66 C32 65 44 67 54 71 M22 80 C32 79 44 81 54 85 M22 94 C32 93 44 95 54 99" stroke-width="5" ${D(0.6)}/>
		<path d="M74 85 C84 82 96 81 106 82 M74 98 C84 95 96 94 106 95" stroke-width="5" ${D(0.6)}/>
		<circle cx="84" cy="30" r="16" ${F(0.2)}/>
		<path d="M96 42 L112 58" stroke-width="10"/>`,

	// Mapa: globo con meridiano, ecuador y paralelos, y tu posición brillando en el centro.
	sidebar_mapa: `
		<circle cx="64" cy="64" r="48" ${F(0.08)}/>
		<ellipse cx="64" cy="64" rx="21" ry="48" stroke-width="6"/>
		<path d="M16 64 H112" stroke-width="6"/>
		<path d="M24 40 C50 47 78 47 104 40 M24 88 C50 81 78 81 104 88" stroke-width="5" ${D(0.5)}/>
		<circle cx="64" cy="64" r="15" stroke-width="5" ${D(0.55)}/>
		<circle cx="64" cy="64" r="8" ${LLENO}/>`,

	// Ajustes: engranaje de 8 dientes con eje hueco.
	sidebar_ajustes: `
		<path d="${engranaje(64, 64, 54, 41, 8)}" ${F(0.14)}/>
		<circle cx="64" cy="64" r="16"/>`,

	// Tienda: toldo festoneado con un diamante, fachada, ventanas y puerta.
	sidebar_tienda: `
		<path d="M14 50 L27 18 H101 L114 50" ${F(0.22)}/>
		<path d="M14 50 Q22.3 62 30.7 50 Q39 62 47.3 50 Q55.7 62 64 50 Q72.3 62 80.7 50 Q89 62 97.3 50 Q105.7 62 114 50"/>
		<path d="M45 18 L40 50 M83 18 L88 50" stroke-width="5" ${D(0.55)}/>
		<path d="M64 25 L72 34 L64 43 L56 34 Z" ${LLENO}/>
		<path d="M22 60 V112 H106 V60"/>
		<path d="M52 112 V84 H76 V112"/>
		<rect x="31" y="70" width="13" height="13" rx="2" stroke-width="5"/>
		<rect x="84" y="70" width="13" height="13" rx="2" stroke-width="5"/>`,

	// =================================================================================================
	// SLOTS DE EQUIPO (8)
	// =================================================================================================

	// Casco espacial 3/4: cúpula, visor curvo, cuello y antena.
	slot_casco: `
		<path d="M30 88 C22 66 26 34 54 22 C80 12 104 30 106 58 C107 72 102 82 96 88" ${F(0.12)}/>
		<path d="M58 46 H97 C101 46 104 50 103 55 L100 72 C99 77 96 80 91 80 H60 C55 80 51 76 51 71 V53 C51 49 54 46 58 46 Z" ${F(0.45)}/>
		<path d="M62 55 H74" stroke-width="5" ${D(0.9)}/>
		<path d="M28 88 H98 L104 110 H22 Z" ${F(0.2)}/>
		<path d="M38 99 H88" stroke-width="5" ${D(0.6)}/>
		<path d="M44 26 L35 11" stroke-width="6"/>
		<circle cx="34" cy="9" r="5" ${LLENO}/>`,

	// Armadura: peto con hombreras angulares, núcleo de energía y líneas de panel.
	slot_armadura: `
		<path d="M40 38 L52 32 L64 40 L76 32 L88 38 V98 L64 114 L40 98 Z" ${F(0.12)}/>
		<path d="M16 40 L40 26 L48 50 L28 62 Z" ${F(0.35)}/>
		<path d="M112 40 L88 26 L80 50 L100 62 Z" ${F(0.35)}/>
		<circle cx="64" cy="64" r="16" stroke-width="5"/>
		<circle cx="64" cy="64" r="8" ${LLENO}/>
		<path d="M48 88 L64 96 L80 88" stroke-width="5" ${D(0.6)}/>
		<path d="M50 78 H40 M78 78 H88" stroke-width="5" ${D(0.6)}/>`,

	// Espada de energía: hoja con canal central, guarda, empuñadura y pomo.
	slot_espada: `
		<path d="M64 8 L76 24 V76 H52 V24 Z" ${F(0.15)}/>
		<path d="M64 26 V70" stroke-width="4" ${D(0.75)}/>
		<path d="M30 78 H98 L92 88 H36 Z" ${F(0.45)}/>
		<path d="M64 92 V106" stroke-width="10"/>
		<path d="M64 108 L71 115 L64 122 L57 115 Z" ${LLENO}/>`,

	// Pistola de energía de perfil: corredera, mira, gatillo con guarda, culata con celda de energía.
	slot_arma: `
		<path d="M14 38 H96 L112 46 V58 H14 Z" ${F(0.15)}/>
		<path d="M24 58 L16 104 C16 108 18 110 22 110 H40 C44 110 46 108 46 105 L50 82 C51 78 54 76 58 76 H70 C74 76 76 74 76 70 V58"/>
		<path d="M62 58 C62 64 61 68 58 70" stroke-width="5"/>
		<path d="M33 70 H45 L41 96 H29 Z" ${LLENO}/>
		<path d="M22 38 V29 H34 V38 M90 38 V31" stroke-width="6"/>
		<path d="M58 48 H70 M76 48 H88" stroke-width="5" ${D(0.6)}/>
		<path d="M112 52 H120" stroke-width="5" ${D(0.7)}/>`,

	// Amuleto: cadena curva de eslabones, colgante romboidal y gema central.
	slot_amuleto: `
		<path d="M22 14 C28 42 44 55 64 57 C84 55 100 42 106 14" stroke-width="6" stroke-dasharray="1 10"/>
		<circle cx="64" cy="62" r="5" stroke-width="5"/>
		<path d="M64 68 L91 90 L64 118 L37 90 Z" ${F(0.2)}/>
		<path d="M37 90 H52 M76 90 H91" stroke-width="4" ${D(0.6)}/>
		<circle cx="64" cy="91" r="10" ${LLENO}/>`,

	// Anillo en 3/4 con gema engarzada y un destello.
	slot_anillo: `
		<ellipse cx="64" cy="86" rx="40" ry="24" stroke-width="9"/>
		<ellipse cx="64" cy="90" rx="29" ry="14" stroke-width="4" ${D(0.4)}/>
		<path d="M52 66 L57 58 M76 66 L71 58" stroke-width="5"/>
		<path d="M64 20 L82 40 L64 60 L46 40 Z" ${F(0.3)}/>
		<path d="M46 40 H82 M55 40 L64 20 L73 40" stroke-width="4" ${D(0.75)}/>
		<path d="M100 8 L104 18 L114 22 L104 26 L100 36 L96 26 L86 22 L96 18 Z" ${LLENO}/>`,

	// Cinturón táctico: banda, hebilla cuadrada con pasador y dos cartucheras.
	slot_cinturon: `
		<path d="M6 48 C40 60 88 60 122 48 V72 C88 84 40 84 6 72 Z" ${F(0.14)}/>
		<rect x="45" y="44" width="38" height="44" rx="6" ${F(0.22)}/>
		<rect x="56" y="56" width="16" height="20" rx="2" stroke-width="5"/>
		<path d="M64 56 V76" stroke-width="4"/>
		<circle cx="98" cy="64" r="3.5" ${LLENO}/><circle cx="110" cy="60" r="3.5" ${LLENO}/>
		<path d="M14 62 H36 V96 C36 99 34 101 31 101 H19 C16 101 14 99 14 96 Z" stroke-width="6" ${F(0.3)}/>
		<path d="M14 74 H36" stroke-width="5"/>
		<circle cx="25" cy="86" r="3" ${LLENO}/>`,

	// Botas espaciales de perfil: caña alta, suela gruesa con tacos y luz en el tobillo.
	slot_botas: `
		<path d="M36 12 H70 V58 L100 70 C108 73 112 80 112 88 V92 H28 V20 C28 15 31 12 36 12 Z" ${F(0.14)}/>
		<path d="M28 24 H70" stroke-width="5" ${D(0.6)}/>
		<path d="M70 70 L78 62 M82 76 L90 68" stroke-width="5" ${D(0.6)}/>
		<rect x="37" y="50" width="20" height="13" rx="4" ${LLENO}/>
		<path d="M22 92 H116 V104 C116 108 114 110 110 110 H28 C24 110 22 108 22 104 Z" ${F(0.4)}/>
		<path d="M36 112 V119 M54 112 V119 M72 112 V119 M90 112 V119 M106 112 V119" stroke-width="6"/>`,

	// =================================================================================================
	// ESTADÍSTICAS (5) — se ven a 18 px: trazos más gruesos y menos detalle.
	// =================================================================================================

	// Fuerza: impacto central con ondas de choque en zigzag a los dos lados.
	stat_fuerza: `
		<path d="${estrella(64, 64, 22, 9, 8, -90)}" ${LLENO}/>
		<path d="M38 18 L22 42 L40 64 L22 86 L38 110" stroke-width="10"/>
		<path d="M90 18 L106 42 L88 64 L106 86 L90 110" stroke-width="10"/>`,

	// Aguante: escudo de doble borde con un check.
	stat_aguante: `
		<path d="M64 10 L106 25 V60 C106 88 88 107 64 118 C40 107 22 88 22 60 V25 Z" stroke-width="9" ${F(0.15)}/>
		<path d="M64 26 L92 36 V60 C92 80 80 93 64 101 C48 93 36 80 36 60 V36 Z" stroke-width="5" ${D(0.45)}/>
		<path d="M45 63 L58 76 L84 48" stroke-width="11"/>`,

	// Espada (mini).
	stat_espada: `
		<path d="M64 8 L77 24 V76 H51 V24 Z" stroke-width="9" ${F(0.3)}/>
		<path d="M32 82 H96" stroke-width="12"/>
		<path d="M64 90 V108" stroke-width="12"/>
		<circle cx="64" cy="116" r="6" ${LLENO}/>`,

	// Arma (mini).
	stat_arma: `
		<path d="M12 36 H100 L116 46 V60 H60 L52 104 H24 L32 60 H12 Z" stroke-width="9" ${F(0.3)}/>
		<path d="M60 60 V72 H76 V60" stroke-width="8"/>`,

	// Habilidad (mini): estrella con punto central.
	stat_habilidad: `
		<path d="${estrella(64, 66, 54, 23)}" stroke-width="9" ${F(0.2)}/>
		<circle cx="64" cy="68" r="10" ${LLENO}/>`,

	// =================================================================================================
	// EXTRA DE INTERFAZ (los usa la UI además de los 22 pedidos)
	// =================================================================================================

	ui_cerrar: `<path d="M34 34 L94 94 M94 34 L34 94" stroke-width="13"/>`,
	ui_check: `<path d="M24 66 L52 94 L104 36" stroke-width="15"/>`,
	ui_candado: `
		<path d="M42 58 V42 C42 29 52 20 64 20 C76 20 86 29 86 42 V58" stroke-width="10"/>
		<rect x="26" y="56" width="76" height="58" rx="10" ${F(0.25)}/>
		<circle cx="64" cy="80" r="8" ${LLENO}/>
		<path d="M64 84 V98" stroke-width="8"/>`,
	ui_estrella: `<path d="${estrella(64, 68, 56, 24)}" ${LLENO}/>`,
	ui_estrella_vacia: `<path d="${estrella(64, 68, 54, 23)}" stroke-width="8" ${F(0.12)}/>`,
	// Moneda (◆): moneda con un diamante grabado.
	ui_moneda: `
		<circle cx="64" cy="64" r="48" stroke-width="9" ${F(0.18)}/>
		<circle cx="64" cy="64" r="35" stroke-width="4" ${D(0.45)}/>
		<path d="M64 36 L84 64 L64 92 L44 64 Z" ${LLENO}/>`,
	// Gema (◇): gema tallada con facetas.
	ui_gema: `
		<path d="M34 24 H94 L116 50 L64 112 L12 50 Z" stroke-width="8" ${F(0.22)}/>
		<path d="M12 50 H116 M34 24 L48 50 L64 112 L80 50 L94 24 M48 50 L64 24 L80 50" stroke-width="5" ${D(0.75)}/>`,
	// Logros: trofeo con asas, estrella y peana.
	ui_logros: `
		<path d="M38 16 H90 V46 C90 62 78 74 64 74 C50 74 38 62 38 46 Z" ${F(0.2)}/>
		<path d="M38 26 H22 V36 C22 48 30 56 40 56 M90 26 H106 V36 C106 48 98 56 88 56" stroke-width="7"/>
		<path d="${estrella(64, 44, 13, 5.5)}" ${LLENO}/>
		<path d="M64 74 V92" stroke-width="9"/>
		<path d="M40 112 H88 V102 C88 98 85 94 81 94 H47 C43 94 40 98 40 102 Z" ${F(0.4)}/>`,
	// Viajar: cohete en diagonal con llama.
	ui_viajar: `
		<path d="M98 18 C80 18 62 28 50 44 L40 58 L70 88 L84 78 C100 66 110 48 110 30 V18 Z" ${F(0.18)}/>
		<circle cx="82" cy="46" r="9" ${LLENO}/>
		<path d="M44 52 L24 52 L14 66 L34 70 M76 84 L76 104 L62 114 L58 94" stroke-width="7"/>
		<path d="M38 92 L18 112 M48 98 L36 110 M30 84 L18 96" stroke-width="7" ${D(0.7)}/>`,
	// Posición (marcador de navegación).
	ui_posicion: `<path d="M64 10 L104 114 L64 90 L24 114 Z" ${LLENO}/>`,
	// Advertencia (para confirmaciones).
	ui_alerta: `
		<path d="M64 14 L118 108 H10 Z" stroke-width="9" ${F(0.2)}/>
		<path d="M64 48 V76" stroke-width="11"/>
		<circle cx="64" cy="92" r="6.5" ${LLENO}/>`,
	// Silueta R6 discontinua (holograma del personaje mientras no hay ViewportFrame).
	ui_holo_r6: `
		<g stroke-width="2.6" stroke-dasharray="5 4" ${F(0.08)}>
			<rect x="50" y="3" width="28" height="23" rx="7"/><rect x="45" y="28" width="38" height="40" rx="2"/>
			<rect x="30" y="28" width="13" height="40" rx="2"/><rect x="85" y="28" width="13" height="40" rx="2"/>
			<rect x="45" y="70" width="18" height="44" rx="2"/><rect x="65" y="70" width="18" height="44" rx="2"/>
		</g>
		<ellipse cx="64" cy="120" rx="36" ry="5" stroke-width="2" ${D(0.6)}/>
		<ellipse cx="64" cy="120" rx="22" ry="3" stroke-width="2" ${F(0.2)}/>`,
	// Interactuar (mano/puntero sobre un objetivo).
	ui_interactuar: `
		<circle cx="64" cy="64" r="44" stroke-width="7" stroke-dasharray="16 12" ${D(0.6)}/>
		<circle cx="64" cy="64" r="22" ${F(0.3)}/>
		<circle cx="64" cy="64" r="8" ${LLENO}/>`,

	// Categorías de Ajustes.
	aj_graficos: `
		<rect x="12" y="20" width="104" height="70" rx="8" ${F(0.15)}/>
		<path d="M30 74 L52 48 L66 62 L78 50 L98 74" stroke-width="6"/>
		<circle cx="88" cy="38" r="6" ${LLENO}/>
		<path d="M46 108 H82 M64 90 V108" stroke-width="8"/>`,
	aj_audio: `
		<path d="M16 50 H36 L62 26 V102 L36 78 H16 Z" ${F(0.25)}/>
		<path d="M78 46 C86 54 86 74 78 82" stroke-width="7"/>
		<path d="M92 32 C108 48 108 80 92 96" stroke-width="7" ${D(0.65)}/>`,
	aj_controles: `
		<path d="M30 40 H98 C110 40 118 50 116 64 L112 88 C110 100 96 104 88 94 L80 84 H48 L40 94 C32 104 18 100 16 88 L12 64 C10 50 18 40 30 40 Z" ${F(0.15)}/>
		<path d="M38 56 V72 M30 64 H46" stroke-width="7"/>
		<circle cx="86" cy="58" r="5" ${LLENO}/><circle cx="98" cy="70" r="5" ${LLENO}/>
		<path d="M58 30 C58 22 64 18 70 20" stroke-width="5" ${D(0.6)}/>`,
	aj_interfaz: `
		<rect x="12" y="16" width="104" height="96" rx="10" ${F(0.1)}/>
		<rect x="24" y="28" width="30" height="72" rx="4" ${LLENO} opacity=".85"/>
		<path d="M66 34 H104 M66 52 H96 M66 70 H104 M66 88 H88" stroke-width="7" ${D(0.7)}/>`,
	aj_juego: `
		<circle cx="64" cy="64" r="48" ${F(0.1)}/>
		<path d="M16 64 H112 M64 16 C44 36 44 92 64 112 C84 92 84 36 64 16" stroke-width="6"/>
		<path d="M24 40 H104 M24 88 H104" stroke-width="5" ${D(0.55)}/>`,

	// =================================================================================================
	// RAZAS (se ven grandes, ~60 px: más detalle)
	// =================================================================================================

	// Humano: busto de astronauta.
	raza_humano: `
		<circle cx="64" cy="50" r="33" stroke-width="6" ${F(0.1)}/>
		<path d="M40 44 C40 36 46 31 54 31 H74 C82 31 88 36 88 44 V55 C88 63 82 67 74 67 H54 C46 67 40 63 40 55 Z" stroke-width="5" ${F(0.45)}/>
		<path d="M48 40 H60" stroke-width="4"/>
		<circle cx="29" cy="50" r="5" ${LLENO}/><circle cx="99" cy="50" r="5" ${LLENO}/>
		<path d="M86 22 L98 8" stroke-width="5"/><circle cx="99" cy="7" r="4" ${LLENO}/>
		<path d="M40 86 H88" stroke-width="6"/>
		<path d="M12 122 C14 101 28 90 46 88 H82 C100 90 114 101 116 122" stroke-width="6" ${F(0.2)}/>
		<rect x="52" y="98" width="24" height="15" rx="3" stroke-width="5"/>
		<circle cx="64" cy="105.5" r="3" ${LLENO}/>`,

	// Monstruo: silueta original de creepypasta: cabeza alargada, tres ojos huecos desiguales,
	// boca dentada y hombros encorvados con púas.
	raza_monstruo: `
		<path d="M64 6 C80 6 91 20 91 42 C91 60 83 75 75 84 L71 98 H57 L53 84 C45 75 37 60 37 42 C37 20 48 6 64 6 Z" stroke-width="6" ${F(0.15)}/>
		<ellipse cx="53" cy="43" rx="7" ry="10" ${LLENO}/>
		<ellipse cx="76" cy="39" rx="5" ry="7.5" ${LLENO}/>
		<circle cx="67" cy="24" r="3.5" ${LLENO}/>
		<path d="M50 65 L55 72 L59 65 L64 74 L68 65 L73 72 L78 65" stroke-width="4"/>
		<path d="M8 124 C12 106 24 96 42 93 L52 100 M86 93 C104 96 116 106 120 124" stroke-width="6"/>
		<path d="M27 99 L19 82 L35 94 M101 99 L109 82 L93 94" stroke-width="5"/>`,

	// =================================================================================================
	// HABILIDADES (HUD y árbol de poderes)
	// =================================================================================================

	hab_rayo: `<path d="M74 8 L32 70 H60 L50 120 L96 52 H66 Z" stroke-width="7" ${F(0.35)}/>`,
	hab_trueno: `
		<path d="M30 54 C16 54 12 38 24 32 C24 16 42 12 50 22 C56 8 78 8 82 24 C96 20 108 32 102 44 C110 50 104 58 96 56 Z" stroke-width="7" ${F(0.15)}/>
		<path d="M68 58 L50 88 H64 L56 116 L82 80 H68 Z" ${LLENO}/>
		<path d="M18 120 H40 M88 120 H110" stroke-width="5" ${D(0.6)}/>`,
	hab_tormenta: `
		<path d="M26 50 C12 50 8 34 20 28 C20 12 38 8 46 18 C52 4 74 4 78 20 C92 16 104 28 98 40 C106 46 100 54 92 52 Z" stroke-width="7" ${F(0.15)}/>
		<path d="M38 58 L28 78 H38 L32 96 L50 72 H40 Z M70 58 L58 84 H70 L62 110 L84 76 H72 Z M98 58 L90 74 H98 L94 88 L106 70 H98 Z" ${LLENO}/>`,
	hab_pulso: `
		<circle cx="64" cy="64" r="12" ${LLENO}/>
		<circle cx="64" cy="64" r="28" stroke-width="7"/>
		<circle cx="64" cy="64" r="45" stroke-width="5" ${D(0.6)}/>
		<circle cx="64" cy="64" r="58" stroke-width="3" stroke-dasharray="6 9" ${D(0.45)}/>`,
	hab_aplastar: `
		<path d="M64 12 V62 M48 48 L64 64 L80 48" stroke-width="9"/>
		<path d="M30 22 V54 M20 44 L30 56 L40 44 M98 22 V54 M88 44 L98 56 L108 44" stroke-width="7" ${D(0.65)}/>
		<path d="M10 84 H118" stroke-width="8"/>
		<path d="M64 84 L56 98 L66 110 M40 84 L32 100 M90 84 L100 102" stroke-width="5" ${D(0.7)}/>`,
	hab_singularidad: `
		<ellipse cx="64" cy="64" rx="56" ry="17" transform="rotate(-20 64 64)" stroke-width="6" ${D(0.7)}/>
		<path d="M64 26 C88 26 102 46 98 64 M64 102 C40 102 26 82 30 64" stroke-width="6"/>
		<circle cx="64" cy="64" r="18" ${LLENO}/>
		<circle cx="64" cy="64" r="26" stroke-width="3" ${D(0.5)}/>`,
	hab_combo: `
		<path d="M44 46 C44 38 50 35 56 37 C57 29 66 27 71 32 C74 26 84 26 87 33 C92 29 100 32 100 40 V70 C100 88 88 102 70 102 H62 C52 102 44 94 44 84 Z" stroke-width="7" ${F(0.25)}/>
		<path d="M56 38 V58 M71 33 V56 M87 34 V56" stroke-width="5" ${D(0.6)}/>
		<path d="M44 62 C52 60 60 64 62 72" stroke-width="5"/>
		<path d="M8 50 H32 M14 68 H34 M8 86 H32" stroke-width="6" ${D(0.65)}/>`,
	hab_escaner: `
		<circle cx="64" cy="64" r="50" stroke-width="6" ${D(0.5)}/>
		<circle cx="64" cy="64" r="28" stroke-width="5" ${D(0.4)}/>
		<path d="M64 64 L64 14 A50 50 0 0 1 107 39 Z" ${F(0.4)} stroke-width="5"/>
		<circle cx="64" cy="64" r="6" ${LLENO}/>
		<circle cx="86" cy="40" r="6" ${LLENO}/><circle cx="40" cy="86" r="5" ${LLENO} opacity=".6"/>`,
	hab_propulsor: `
		<path d="M28 62 L64 26 L100 62" stroke-width="10"/>
		<path d="M36 90 L64 62 L92 90" stroke-width="8" ${D(0.65)}/>
		<path d="M64 98 C72 106 70 116 64 122 C58 116 56 106 64 98 Z" ${LLENO}/>`,
	hab_sigilo: `
		<path d="M10 64 C28 36 48 26 64 26 C80 26 100 36 118 64 C100 92 80 102 64 102 C48 102 28 92 10 64 Z" stroke-width="7" ${F(0.12)}/>
		<circle cx="64" cy="64" r="15" ${LLENO}/>
		<path d="M22 112 L106 16" stroke-width="9"/>`,
	hab_salto: `
		<path d="M18 64 H72 M54 44 L76 64 L54 84" stroke-width="9"/>
		<path d="M86 22 C102 30 112 46 112 64 C112 82 102 98 86 106" stroke-width="7"/>
		<path d="M14 40 H40 M14 88 H40" stroke-width="5" ${D(0.6)}/>`,
	hab_curar: `
		<path d="M64 10 L110 37 V91 L64 118 L18 91 V37 Z" stroke-width="7" ${F(0.12)}/>
		<path d="M54 36 H74 V54 H92 V74 H74 V92 H54 V74 H36 V54 H54 Z" ${LLENO}/>`,
	hab_escudo: `
		<path d="M64 10 L106 25 V60 C106 88 88 107 64 118 C40 107 22 88 22 60 V25 Z" stroke-width="8" ${F(0.15)}/>
		<path d="M42 56 C50 46 78 46 86 56 M48 72 C56 64 72 64 80 72" stroke-width="6"/>
		<circle cx="64" cy="86" r="6" ${LLENO}/>`,
	hab_aura: `
		<path d="${rayos(64, 64, 38, 58, 50, 12)}" stroke-width="6" ${D(0.7)}/>
		<circle cx="64" cy="64" r="26" stroke-width="7" ${F(0.18)}/>
		<path d="M64 48 L76 64 L64 80 L52 64 Z" ${LLENO}/>`,
	hab_dron: `
		<rect x="44" y="52" width="40" height="26" rx="8" stroke-width="7" ${F(0.25)}/>
		<circle cx="64" cy="65" r="5" ${LLENO}/>
		<path d="M44 58 L26 42 M84 58 L102 42 M44 72 L30 92 M84 72 L98 92" stroke-width="6"/>
		<path d="M10 40 H42 M86 40 H118" stroke-width="6" ${D(0.7)}/>
		<path d="M64 78 V96 M54 96 H74" stroke-width="6" ${D(0.7)}/>`,

	// =================================================================================================
	// INSIGNIAS DE RANGO (blancas: el color del rango se pone al teñirlas)
	// =================================================================================================

	rango_bronce: `
		<path d="${ESCUDO}" stroke-width="8" ${F(0.18)}/>
		<path d="M42 64 L64 80 L86 64" stroke-width="10"/>`,
	rango_plata: `
		<path d="${ESCUDO}" stroke-width="8" ${F(0.18)}/>
		<path d="M42 50 L64 66 L86 50 M42 72 L64 88 L86 72" stroke-width="9"/>`,
	rango_oro: `
		<path d="${ESCUDO}" stroke-width="8" ${F(0.2)}/>
		<path d="M44 42 L64 56 L84 42 M44 62 L64 76 L84 62 M44 82 L64 96 L84 82" stroke-width="8"/>`,
	rango_platino: `
		<path d="${ESCUDO}" stroke-width="8" ${F(0.2)}/>
		<path d="M22 36 L6 28 L10 58 L22 66 M106 36 L122 28 L118 58 L106 66" stroke-width="6"/>
		<path d="M44 56 L64 70 L84 56 M44 76 L64 90 L84 76" stroke-width="8"/>
		<circle cx="64" cy="38" r="6" ${LLENO}/>`,
	rango_diamante: `
		<path d="${ESCUDO}" stroke-width="8" ${F(0.2)}/>
		<path d="M22 36 L6 28 L10 58 L22 66 M106 36 L122 28 L118 58 L106 66" stroke-width="6"/>
		<path d="M50 34 H78 L90 50 L64 86 L38 50 Z" ${LLENO}/>
		<path d="M44 92 L64 104 L84 92" stroke-width="7"/>`,
	rango_maestro: `
		<path d="${ESCUDO_INT}" stroke-width="8" ${F(0.22)}/>
		<path d="M18 46 C10 72 22 100 50 114 M110 46 C118 72 106 100 78 114" stroke-width="7"/>
		<path d="M14 62 L24 66 M14 82 L26 82 M22 100 L32 96 M114 62 L104 66 M114 82 L102 82 M106 100 L96 96" stroke-width="5" ${D(0.7)}/>
		<path d="${estrella(64, 66, 24, 10)}" ${LLENO}/>`,
	rango_granmaestro: `
		<path d="${ESCUDO_INT}" stroke-width="8" ${F(0.24)}/>
		<path d="M18 46 C10 72 22 100 50 114 M110 46 C118 72 106 100 78 114" stroke-width="7"/>
		<path d="M14 62 L24 66 M14 82 L26 82 M22 100 L32 96 M114 62 L104 66 M114 82 L102 82 M106 100 L96 96" stroke-width="5" ${D(0.7)}/>
		<path d="M44 20 L46 4 L55 12 L64 0 L73 12 L82 4 L84 20 Z" ${LLENO}/>
		<path d="${estrella(64, 68, 22, 9)}" ${LLENO}/>`,
	rango_estelar: `
		<path d="${rayos(64, 64, 46, 62, 54, 16)}" stroke-width="5"/>
		<path d="${estrella(64, 64, 44, 30, 8, -90)}" stroke-width="7" ${F(0.25)}/>
		<path d="${estrella(64, 66, 26, 11)}" ${LLENO}/>
		<circle cx="64" cy="64" r="36" stroke-width="3" ${D(0.5)}/>`,
};

// Grupos (para la hoja de contactos y la galería del preview).
export const GRUPOS = [
	["Barra lateral", Object.keys(ICONOS).filter((n) => n.startsWith("sidebar_"))],
	["Slots de equipo", Object.keys(ICONOS).filter((n) => n.startsWith("slot_"))],
	["Estadísticas", Object.keys(ICONOS).filter((n) => n.startsWith("stat_"))],
	["Interfaz", Object.keys(ICONOS).filter((n) => n.startsWith("ui_"))],
	["Ajustes", Object.keys(ICONOS).filter((n) => n.startsWith("aj_"))],
	["Razas", Object.keys(ICONOS).filter((n) => n.startsWith("raza_"))],
	["Habilidades", Object.keys(ICONOS).filter((n) => n.startsWith("hab_"))],
	["Rangos", Object.keys(ICONOS).filter((n) => n.startsWith("rango_"))],
];

// Atributos comunes del <svg> de un icono.
export const ATRIBUTOS_ICONO =
	'viewBox="0 0 128 128" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"';
