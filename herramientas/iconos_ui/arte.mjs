// Arte a color de objetos, criaturas, plantas, planetas y artículos de la tienda.
//
// Son las "imágenes reales" que se ven dentro de las casillas del inventario, del índice y de la tienda
// (no cuadrados de colores). Cada pieza es el contenido de un <svg viewBox="0 0 128 128"> con sus propios
// degradados; los id de los degradados llevan el nombre de la pieza delante para no chocar entre sí cuando
// todas viven en el mismo HTML.
//
// Los colores siguen los modelos 3D del repositorio (modelos/hoja_contactos_todo.png): el cristal cian, el
// cristal abisal índigo con brillo lila, el Brincador crema con orejas rosas y franjas verdeazuladas, el
// Acechador morado oscuro con ojos lila y púas de hueso, la nave Alba blanca y naranja...
//
// Estilo: contorno oscuro de 3 unidades, degradado de luz arriba-izquierda a sombra abajo-derecha, un brillo
// blanco y, en lo que tiene energía, un halo difuminado detrás.

const CONTORNO = "#070B18";
const O = `stroke="${CONTORNO}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"`;
const O2 = `stroke="${CONTORNO}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"`;

// Degradado lineal (por defecto de arriba-izquierda a abajo-derecha).
function lg(id, paradas, x1 = 0, y1 = 0, x2 = 1, y2 = 1) {
	const stops = paradas.map(([o, c, a = 1]) => `<stop offset="${o}" stop-color="${c}" stop-opacity="${a}"/>`).join("");
	return `<linearGradient id="${id}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}">${stops}</linearGradient>`;
}
// Degradado radial.
function rg(id, paradas, cx = 0.35, cy = 0.3, r = 0.8) {
	const stops = paradas.map(([o, c, a = 1]) => `<stop offset="${o}" stop-color="${c}" stop-opacity="${a}"/>`).join("");
	return `<radialGradient id="${id}" cx="${cx}" cy="${cy}" r="${r}">${stops}</radialGradient>`;
}
// Halo difuminado detrás de algo con energía.
function halo(id, color, cx, cy, r, opacidad = 0.55) {
	return {
		defs: `<filter id="${id}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="${r / 3}"/></filter>`,
		body: `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${color}" opacity="${opacidad}" filter="url(#${id})"/>`,
	};
}

// Prisma de cristal (punta hacia arriba) apoyado en (x, y), girado `ang` grados. Cara izquierda clara, derecha oscura.
function cristal(x, y, w, h, ang, claro, oscuro, borde = CONTORNO) {
	const m = w / 2;
	const hombro = y - h * 0.72;
	const izq = `M${x - m} ${y} L${x - m} ${hombro} L${x} ${y - h} L${x} ${y} Z`;
	const der = `M${x} ${y} L${x} ${y - h} L${x + m} ${hombro} L${x + m} ${y} Z`;
	return `<g transform="rotate(${ang} ${x} ${y})">
		<path d="${izq}" fill="${claro}"/><path d="${der}" fill="${oscuro}"/>
		<path d="M${x - m} ${y} L${x - m} ${hombro} L${x} ${y - h} L${x + m} ${hombro} L${x + m} ${y}" fill="none" stroke="${borde}" stroke-width="2.5" stroke-linejoin="round"/>
		<path d="M${x - m * 0.45} ${y - h * 0.2} L${x - m * 0.45} ${hombro + 2}" stroke="#fff" stroke-opacity=".55" stroke-width="2" stroke-linecap="round"/>
	</g>`;
}

// Roca irregular de base (para menas).
function roca(p, claro, oscuro) {
	return {
		defs: lg(`${p}-roca`, [[0, claro], [1, oscuro]]),
		body: `<path d="M14 92 L22 66 L44 54 L68 58 L90 50 L112 66 L116 92 L98 110 L50 114 L24 106 Z" fill="url(#${p}-roca)" ${O}/>
			<path d="M44 54 L50 80 L24 106 M50 80 L98 84 L116 92 M98 84 L90 50" fill="none" stroke="${CONTORNO}" stroke-opacity=".35" stroke-width="2"/>
			<path d="M24 68 L42 58" stroke="#fff" stroke-opacity=".25" stroke-width="3" stroke-linecap="round"/>`,
	};
}

// Pepita metálica (polígono redondeado con brillo).
function pepita(p, n, d, claro, oscuro) {
	return {
		defs: lg(`${p}-pep${n}`, [[0, claro], [1, oscuro]]),
		body: `<path d="${d}" fill="url(#${p}-pep${n})" ${O2}/>`,
	};
}

// Planeta: esfera con degradado, detalles recortados a la esfera, sombra del terminador y atmósfera.
function planeta(p, { base, atmosfera, detalles = "", anillo = "" }) {
	return {
		defs:
			rg(`${p}-base`, base, 0.36, 0.32, 0.78) +
			rg(`${p}-sombra`, [[0.55, "#000", 0], [1, "#000", 0.75]], 0.32, 0.28, 0.85) +
			`<clipPath id="${p}-clip"><circle cx="64" cy="64" r="44"/></clipPath>` +
			`<filter id="${p}-atm" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="4"/></filter>`,
		body: `<circle cx="64" cy="64" r="48" fill="${atmosfera}" opacity=".45" filter="url(#${p}-atm)"/>
			${anillo ? anillo.atras : ""}
			<circle cx="64" cy="64" r="44" fill="url(#${p}-base)"/>
			<g clip-path="url(#${p}-clip)">${detalles}</g>
			<circle cx="64" cy="64" r="44" fill="url(#${p}-sombra)"/>
			<circle cx="64" cy="64" r="44" fill="none" stroke="${atmosfera}" stroke-opacity=".7" stroke-width="2"/>
			<path d="M34 40 C40 30 50 24 60 22" stroke="#fff" stroke-opacity=".4" stroke-width="3" stroke-linecap="round" fill="none"/>
			${anillo ? anillo.delante : ""}`,
	};
}

// Une varias partes { defs, body } en una pieza.
function une(...partes) {
	return {
		defs: partes.map((x) => x.defs || "").join(""),
		body: partes.map((x) => x.body || "").join(""),
	};
}
// Las menas son anchas y bajas: se agrandan y se suben para que llenen la casilla.
function mena(...partes) {
	const { defs, body } = une(...partes);
	return { defs, body: `<g transform="translate(-5 -22) scale(1.08)">${body}</g>` };
}
const B = (body, defs = "") => ({ defs, body });

// =====================================================================================================
// Piezas
// =====================================================================================================

const PIEZAS = {
	// ===== Minerales (Exploracion/Datos/Objetos) =====
	item_hierro: (p) =>
		mena(
			roca(p, "#6B6560", "#2E2A27"),
			pepita(p, 1, "M40 74 L52 64 L66 70 L62 86 L46 88 Z", "#F2F2F6", "#7C828C"),
			pepita(p, 2, "M70 64 L84 58 L94 68 L86 80 L74 78 Z", "#E6E8EE", "#6E747E"),
			pepita(p, 3, "M58 92 L70 88 L76 98 L64 104 Z", "#D9DCE3", "#6A707A"),
			B(`<path d="M48 70 L56 68" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/><path d="M76 63 L84 61" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>`),
		),
	item_cobre: (p) =>
		mena(
			roca(p, "#5A4A40", "#241B16"),
			pepita(p, 1, "M36 76 C38 66 52 62 60 68 C64 76 56 88 46 88 C40 86 36 82 36 76 Z", "#FFC18F", "#B5562A"),
			pepita(p, 2, "M68 70 C72 60 88 58 94 66 C98 76 90 84 80 84 C72 82 68 78 68 70 Z", "#FFB27A", "#A24A22"),
			B(`<circle cx="66" cy="96" r="5" fill="#4FC9A0" ${O2}/><circle cx="90" cy="94" r="3.5" fill="#4FC9A0" ${O2}/>
				<path d="M44 70 L50 68 M76 64 L82 63" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>`),
		),
	item_titanio: (p) =>
		mena(
			roca(p, "#4C566A", "#1B2030"),
			pepita(p, 1, "M38 66 L54 60 L66 68 L64 84 L48 90 L36 82 Z", "#E6EEFF", "#7D93BA"),
			pepita(p, 2, "M68 62 L84 56 L98 64 L96 80 L80 86 L68 78 Z", "#D5E2FF", "#6D84AD"),
			B(`<path d="M38 66 L54 72 L66 68 M54 72 L48 90 M68 62 L82 70 L98 64 M82 70 L80 86" fill="none" stroke="${CONTORNO}" stroke-opacity=".3" stroke-width="2"/>
				<path d="M44 66 L52 63" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>`),
		),
	item_cristal: (p) =>
		une(
			halo(`${p}-h`, "#5CE1FF", 64, 60, 40, 0.5),
			B(`<path d="M24 100 L34 86 L60 82 L94 86 L106 100 L88 112 L42 112 Z" fill="#3A4256" ${O}/>
				<path d="M24 100 L42 104 L88 104 L106 100" fill="none" stroke="${CONTORNO}" stroke-opacity=".4" stroke-width="2"/>`),
			B(cristal(46, 94, 16, 44, -24, "#C9F6FF", "#5CB8E0")),
			B(cristal(84, 94, 16, 46, 22, "#C9F6FF", "#5CB8E0")),
			B(cristal(64, 94, 22, 76, 0, "#E8FCFF", "#6CCBEA")),
			B(cristal(72, 98, 10, 24, 8, "#BDF2FF", "#4FA9D2")),
		),
	item_cristal_abisal: (p) =>
		une(
			halo(`${p}-h`, "#B983FF", 64, 58, 40, 0.45),
			B(`<path d="M20 102 L32 88 L62 84 L96 88 L108 102 L86 114 L40 114 Z" fill="#1A1622" ${O}/>
				<path d="M40 104 L50 98 M78 104 L88 98" stroke="#D8B4FF" stroke-width="2.5" stroke-linecap="round"/>`),
			B(cristal(44, 96, 15, 44, -28, "#5B3FC4", "#2A1A6E", "#0B0618")),
			B(cristal(86, 96, 14, 40, 26, "#5B3FC4", "#2A1A6E", "#0B0618")),
			B(cristal(64, 96, 22, 82, 0, "#6C4FE0", "#2E1B80", "#0B0618")),
			B(`<path d="M64 20 L64 90" stroke="#E5CCFF" stroke-width="2" stroke-opacity=".85"/>
				<path d="M58 40 L58 84" stroke="#E5CCFF" stroke-width="1.5" stroke-opacity=".5"/>
				<circle cx="64" cy="20" r="3" fill="#F3E6FF"/>`),
		),

	// ===== Componentes =====
	item_lingote_hierro: (p) =>
		B(
			`<path d="M36 52 L90 40 L106 56 L50 70 Z" fill="url(#${p}-top)" ${O}/>
			<path d="M36 52 L50 70 L56 98 L20 82 Z" fill="#9C968E" ${O}/>
			<path d="M50 70 L106 56 L114 82 L56 98 Z" fill="url(#${p}-fr)" ${O}/>
			<path d="M54 56 L84 49" stroke="#fff" stroke-opacity=".7" stroke-width="3" stroke-linecap="round"/>
			<path d="M62 82 L98 72" stroke="${CONTORNO}" stroke-opacity=".25" stroke-width="2"/>`,
			lg(`${p}-top`, [[0, "#FFFFFF"], [1, "#C9C3BB"]]) + lg(`${p}-fr`, [[0, "#B8B2AA"], [1, "#77716A"]]),
		),
	item_cable_cobre: (p) =>
		B(
			`<ellipse cx="60" cy="70" rx="40" ry="34" fill="url(#${p}-c)" ${O}/>
			<ellipse cx="60" cy="70" rx="32" ry="26" fill="none" stroke="${CONTORNO}" stroke-opacity=".45" stroke-width="2"/>
			<ellipse cx="60" cy="70" rx="24" ry="18" fill="none" stroke="${CONTORNO}" stroke-opacity=".45" stroke-width="2"/>
			<ellipse cx="60" cy="70" rx="14" ry="10" fill="#2A1A12" ${O2}/>
			<path d="M28 56 C34 46 46 40 56 39" stroke="#FFE2C8" stroke-width="3" stroke-linecap="round" fill="none"/>
			<path d="M96 80 C106 86 110 96 106 106" stroke="${CONTORNO}" stroke-width="9" stroke-linecap="round" fill="none"/>
			<path d="M96 80 C106 86 110 96 106 106" stroke="#E08A4C" stroke-width="5" stroke-linecap="round" fill="none"/>
			<rect x="98" y="104" width="14" height="12" rx="2" fill="#C9CED8" ${O2}/>`,
			rg(`${p}-c`, [[0, "#FFC69B"], [0.6, "#E08A4C"], [1, "#8E3F18"]]),
		),
	item_lente_cristal: (p) =>
		une(
			halo(`${p}-h`, "#9EF0FF", 64, 64, 34, 0.4),
			B(
				`<circle cx="64" cy="64" r="44" fill="url(#${p}-m)" ${O}/>
				<circle cx="64" cy="64" r="33" fill="url(#${p}-v)" ${O2}/>
				<path d="M44 52 C48 42 56 37 64 36" stroke="#fff" stroke-width="4" stroke-linecap="round" fill="none"/>
				<circle cx="78" cy="78" r="4" fill="#fff" opacity=".6"/>
				<path d="M20 64 H28 M100 64 H108 M64 20 V28 M64 100 V108" stroke="${CONTORNO}" stroke-width="3"/>`,
				lg(`${p}-m`, [[0, "#E7ECF5"], [1, "#6B7487"]]) + rg(`${p}-v`, [[0, "#E8FDFF"], [0.6, "#7FE3FF", 0.9], [1, "#2A8FB8", 0.95]]),
			),
		),
	item_placa_titanio: (p) =>
		B(
			`<path d="M64 14 L106 38 V90 L64 114 L22 90 V38 Z" fill="url(#${p}-p)" ${O}/>
			<path d="M64 26 L96 44 V84 L64 102 L32 84 V44 Z" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="2.5"/>
			<path d="M64 26 L96 44 V84 L64 102" fill="none" stroke="${CONTORNO}" stroke-opacity=".25" stroke-width="2.5"/>
			<g fill="#E6EEFF" ${O2}><circle cx="64" cy="22" r="4"/><circle cx="99" cy="42" r="4"/><circle cx="99" cy="86" r="4"/><circle cx="64" cy="106" r="4"/><circle cx="29" cy="86" r="4"/><circle cx="29" cy="42" r="4"/></g>
			<path d="M42 50 L60 40" stroke="#fff" stroke-opacity=".7" stroke-width="3" stroke-linecap="round"/>`,
			lg(`${p}-p`, [[0, "#DCE7FF"], [0.5, "#9DB2D6"], [1, "#55698F"]]),
		),
	item_nucleo_energia: (p) =>
		une(
			halo(`${p}-h`, "#B58CFF", 64, 64, 36, 0.65),
			B(
				`<circle cx="64" cy="64" r="26" fill="url(#${p}-o)"/>
				<path d="M64 46 C74 52 74 76 64 82 C54 76 54 52 64 46 Z" fill="#fff" opacity=".45"/>
				<path d="M30 30 H98 V40 H30 Z M30 88 H98 V98 H30 Z" fill="url(#${p}-m)" ${O}/>
				<path d="M38 40 V88 M90 40 V88" stroke="${CONTORNO}" stroke-width="7"/>
				<path d="M38 40 V88 M90 40 V88" stroke="#A9B2C6" stroke-width="3.5"/>
				<path d="M34 34 H60" stroke="#fff" stroke-opacity=".6" stroke-width="2.5" stroke-linecap="round"/>`,
				rg(`${p}-o`, [[0, "#FFFFFF"], [0.35, "#E2CCFF"], [0.8, "#9B5CFF"], [1, "#5B2AB8"]], 0.45, 0.4, 0.7) +
					lg(`${p}-m`, [[0, "#D8DEEA"], [1, "#5E677B"]], 0, 0, 0, 1),
			),
		),

	// ===== Equipo (datos de demostración) =====
	item_espada_plasma: (p) =>
		une(
			halo(`${p}-h`, "#3DF2FF", 76, 50, 34, 0.5),
			B(
				`<path d="M104 12 L112 16 L60 78 L50 70 Z" fill="url(#${p}-hoja)" ${O}/>
				<path d="M106 16 L58 73" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>
				<path d="M40 60 L68 88 L62 94 L34 66 Z" fill="url(#${p}-g)" ${O}/>
				<path d="M48 80 L30 98" stroke="${CONTORNO}" stroke-width="12" stroke-linecap="round"/>
				<path d="M48 80 L30 98" stroke="#3A4560" stroke-width="7" stroke-linecap="round"/>
				<path d="M44 84 L40 88 M38 90 L34 94" stroke="#FFB800" stroke-width="2.5"/>
				<circle cx="24" cy="104" r="7" fill="#FFB800" ${O2}/>
				<circle cx="51" cy="77" r="4" fill="#3DF2FF" ${O2}/>`,
				lg(`${p}-hoja`, [[0, "#FFFFFF"], [0.4, "#B9FBFF"], [1, "#22B8D8"]]) + lg(`${p}-g`, [[0, "#FFE08A"], [1, "#B37A00"]]),
			),
		),
	item_pistola_foton: (p) =>
		une(
			halo(`${p}-h`, "#FF8844", 40, 82, 22, 0.55),
			B(
				`<path d="M14 40 H92 L112 50 V62 H14 Z" fill="url(#${p}-c)" ${O}/>
				<path d="M14 50 H92" stroke="#FF8844" stroke-width="4"/>
				<path d="M26 62 L18 104 C18 108 20 110 24 110 H42 C46 110 48 108 48 104 L52 84 H72 C76 84 78 82 78 78 V62 Z" fill="url(#${p}-c2)" ${O}/>
				<rect x="31" y="72" width="11" height="26" rx="3" fill="#FF8844" ${O2}/>
				<path d="M34 76 V94" stroke="#FFE0C8" stroke-width="2" stroke-linecap="round"/>
				<path d="M60 62 C60 70 58 74 55 76" stroke="${CONTORNO}" stroke-width="3" fill="none"/>
				<rect x="24" y="32" width="12" height="8" rx="2" fill="#3A4560" ${O2}/>
				<path d="M112 56 H122" stroke="#FFB27A" stroke-width="4" stroke-linecap="round"/>
				<path d="M20 44 H70" stroke="#fff" stroke-opacity=".8" stroke-width="2.5" stroke-linecap="round"/>`,
				lg(`${p}-c`, [[0, "#FFFFFF"], [1, "#B9C2D3"]], 0, 0, 0, 1) + lg(`${p}-c2`, [[0, "#E4E9F2"], [1, "#8C96AA"]]),
			),
		),
	item_casco_nova: (p) =>
		B(
			`<path d="M28 90 C18 66 24 32 54 20 C82 10 108 30 108 60 C108 74 104 84 98 90 Z" fill="url(#${p}-c)" ${O}/>
			<path d="M56 44 H98 C103 44 106 49 105 54 L102 72 C101 78 97 81 92 81 H60 C54 81 50 77 50 71 V51 C50 47 53 44 56 44 Z" fill="url(#${p}-v)" ${O}/>
			<path d="M58 52 C64 48 74 48 80 50" stroke="#fff" stroke-opacity=".8" stroke-width="3" stroke-linecap="round" fill="none"/>
			<path d="M34 50 C36 38 42 30 50 26" stroke="#FF8844" stroke-width="6" stroke-linecap="round" fill="none"/>
			<path d="M24 90 H102 L108 112 H18 Z" fill="#5B6478" ${O}/>
			<path d="M32 101 H94" stroke="#3DF2FF" stroke-width="3" stroke-linecap="round"/>
			<path d="M42 24 L34 10" stroke="${CONTORNO}" stroke-width="4"/><circle cx="33" cy="8" r="4.5" fill="#FF4444" ${O2}/>`,
			lg(`${p}-c`, [[0, "#FFFFFF"], [1, "#AEB8CC"]]) + lg(`${p}-v`, [[0, "#FFE8A0"], [0.5, "#FFB800"], [1, "#8A4A00"]]),
		),
	item_peto_reactor: (p) =>
		une(
			halo(`${p}-h`, "#3DF2FF", 64, 62, 18, 0.7),
			B(
				`<path d="M40 36 L52 30 L64 38 L76 30 L88 36 V98 L64 114 L40 98 Z" fill="url(#${p}-t)" ${O}/>
				<path d="M14 40 L40 24 L48 50 L26 64 Z" fill="url(#${p}-h2)" ${O}/>
				<path d="M114 40 L88 24 L80 50 L102 64 Z" fill="url(#${p}-h2)" ${O}/>
				<circle cx="64" cy="62" r="13" fill="#0E1A2E" ${O2}/>
				<circle cx="64" cy="62" r="8" fill="url(#${p}-n)"/>
				<path d="M48 88 L64 96 L80 88 M50 76 H42 M78 76 H86" stroke="#3DF2FF" stroke-opacity=".8" stroke-width="2.5" fill="none"/>
				<path d="M20 42 L38 31" stroke="#fff" stroke-opacity=".5" stroke-width="2.5" stroke-linecap="round"/>`,
				lg(`${p}-t`, [[0, "#5F6B85"], [1, "#22293A"]]) +
					lg(`${p}-h2`, [[0, "#7E8AA6"], [1, "#2D3549"]]) +
					rg(`${p}-n`, [[0, "#FFFFFF"], [0.5, "#9FF8FF"], [1, "#3DF2FF"]], 0.5, 0.5, 0.6),
			),
		),
	item_amuleto_vacio: (p) =>
		une(
			halo(`${p}-h`, "#A07AE8", 64, 88, 24, 0.6),
			B(
				`<path d="M22 12 C28 42 44 54 64 56 C84 54 100 42 106 12" fill="none" stroke="#C9CED8" stroke-width="4" stroke-dasharray="3 5" stroke-linecap="round"/>
				<circle cx="64" cy="61" r="5" fill="none" stroke="#C9CED8" stroke-width="3"/>
				<path d="M64 66 L92 90 L64 120 L36 90 Z" fill="url(#${p}-m)" ${O}/>
				<circle cx="64" cy="91" r="12" fill="url(#${p}-g)" ${O2}/>
				<path d="M58 86 C60 83 63 82 66 82" stroke="#fff" stroke-width="2.5" stroke-linecap="round" fill="none"/>`,
				lg(`${p}-m`, [[0, "#E7ECF5"], [1, "#59617A"]]) + rg(`${p}-g`, [[0, "#F2E6FF"], [0.5, "#A07AE8"], [1, "#3B1F7A"]]),
			),
		),
	item_anillo_estelar: (p) =>
		une(
			halo(`${p}-h`, "#4488FF", 64, 40, 20, 0.6),
			B(
				`<ellipse cx="64" cy="86" rx="40" ry="24" fill="none" stroke="${CONTORNO}" stroke-width="14"/>
				<ellipse cx="64" cy="86" rx="40" ry="24" fill="none" stroke="url(#${p}-o)" stroke-width="9"/>
				<path d="M30 78 C38 68 52 63 64 63" stroke="#FFF2C4" stroke-width="3" stroke-linecap="round" fill="none"/>
				<path d="M50 64 L58 54 M78 64 L70 54" stroke="${CONTORNO}" stroke-width="7"/><path d="M50 64 L58 54 M78 64 L70 54" stroke="#FFD24A" stroke-width="3.5"/>
				<path d="M64 18 L84 40 L64 62 L44 40 Z" fill="url(#${p}-g)" ${O}/>
				<path d="M44 40 H84 M54 40 L64 18 L74 40" stroke="#fff" stroke-opacity=".6" stroke-width="2" fill="none"/>
				<path d="M100 10 L103 19 L112 22 L103 25 L100 34 L97 25 L88 22 L97 19 Z" fill="#fff"/>`,
				lg(`${p}-o`, [[0, "#FFF0A8"], [0.5, "#FFB800"], [1, "#A86A00"]]) + lg(`${p}-g`, [[0, "#CFE2FF"], [0.5, "#4488FF"], [1, "#1A3E9C"]]),
			),
		),
	item_cinturon_tactico: (p) =>
		B(
			`<path d="M6 46 C40 58 88 58 122 46 V72 C88 84 40 84 6 72 Z" fill="url(#${p}-b)" ${O}/>
			<path d="M8 54 C40 64 88 64 120 54" stroke="#fff" stroke-opacity=".25" stroke-width="2" fill="none"/>
			<rect x="45" y="42" width="38" height="44" rx="6" fill="url(#${p}-h)" ${O}/>
			<rect x="56" y="54" width="16" height="20" rx="2" fill="#3A3426" ${O2}/>
			<path d="M64 54 V74" stroke="#C9CED8" stroke-width="3"/>
			<circle cx="98" cy="64" r="3" fill="#1A1610"/><circle cx="110" cy="60" r="3" fill="#1A1610"/>
			<path d="M12 60 H38 V98 C38 101 36 103 33 103 H17 C14 103 12 101 12 98 Z" fill="#6E6A4A" ${O}/>
			<path d="M12 72 H38" stroke="${CONTORNO}" stroke-width="2.5"/>
			<circle cx="25" cy="86" r="3.5" fill="#C9CED8" ${O2}/>`,
			lg(`${p}-b`, [[0, "#8C7A5C"], [1, "#3E3424"]], 0, 0, 0, 1) + lg(`${p}-h`, [[0, "#F2F4F8"], [1, "#7C8496"]]),
		),
	item_botas_gravitatorias: (p) =>
		une(
			halo(`${p}-h`, "#3DF2FF", 66, 104, 28, 0.6),
			B(
				`<path d="M36 12 H70 V58 L100 70 C108 73 112 80 112 88 V92 H28 V20 C28 15 31 12 36 12 Z" fill="url(#${p}-b)" ${O}/>
				<path d="M28 24 H70" stroke="#3DF2FF" stroke-width="3"/>
				<rect x="37" y="50" width="20" height="13" rx="4" fill="#3DF2FF" ${O2}/>
				<path d="M22 92 H116 V104 C116 108 114 110 110 110 H28 C24 110 22 108 22 104 Z" fill="#232A3C" ${O}/>
				<path d="M30 104 H108" stroke="#3DF2FF" stroke-width="3" stroke-linecap="round"/>
				<path d="M34 16 V48" stroke="#fff" stroke-opacity=".35" stroke-width="3" stroke-linecap="round"/>`,
				lg(`${p}-b`, [[0, "#5F6B85"], [1, "#1E2434"]]),
			),
		),

	// ===== Consumibles =====
	item_botiquin: (p) =>
		B(
			`<path d="M46 30 V22 C46 18 49 16 52 16 H76 C79 16 82 18 82 22 V30" fill="none" stroke="${CONTORNO}" stroke-width="8"/>
			<path d="M46 30 V22 C46 18 49 16 52 16 H76 C79 16 82 18 82 22 V30" fill="none" stroke="#9AA3B5" stroke-width="4"/>
			<rect x="14" y="30" width="100" height="76" rx="12" fill="url(#${p}-c)" ${O}/>
			<path d="M14 50 H114" stroke="${CONTORNO}" stroke-opacity=".25" stroke-width="2"/>
			<path d="M54 50 H74 V62 H86 V82 H74 V94 H54 V82 H42 V62 H54 Z" fill="#4AFF8B" ${O}/>
			<path d="M22 38 H70" stroke="#fff" stroke-width="3" stroke-linecap="round"/>`,
			lg(`${p}-c`, [[0, "#FFFFFF"], [1, "#AEB6C6"]]),
		),
	item_celula_energia: (p) =>
		une(
			halo(`${p}-h`, "#3DF2FF", 64, 68, 26, 0.5),
			B(
				`<rect x="38" y="22" width="52" height="92" rx="10" fill="url(#${p}-m)" ${O}/>
				<rect x="52" y="12" width="24" height="12" rx="3" fill="#C9CED8" ${O2}/>
				<rect x="46" y="38" width="36" height="64" rx="5" fill="#0E1A2E" ${O2}/>
				<rect x="49" y="58" width="30" height="41" rx="3" fill="url(#${p}-l)"/>
				<path d="M54 64 V94" stroke="#fff" stroke-opacity=".6" stroke-width="2.5" stroke-linecap="round"/>
				<path d="M44 28 V108" stroke="#fff" stroke-opacity=".35" stroke-width="3" stroke-linecap="round"/>`,
				lg(`${p}-m`, [[0, "#E7ECF5"], [1, "#5E677B"]], 0, 0, 1, 0) + lg(`${p}-l`, [[0, "#B9FBFF"], [1, "#1BA8C9"]], 0, 0, 0, 1),
			),
		),

	// ===== Especial =====
	item_chip_estelar: (p) =>
		une(
			halo(`${p}-h`, "#3DF2FF", 64, 40, 30, 0.35),
			B(
				`<path d="M30 24 L64 10 L98 24 L98 52 L64 66 L30 52 Z" fill="#3DF2FF" fill-opacity=".14" stroke="#3DF2FF" stroke-opacity=".7" stroke-width="2"/>
				<g fill="#E8FDFF"><circle cx="50" cy="30" r="2.5"/><circle cx="72" cy="22" r="2"/><circle cx="82" cy="40" r="3"/><circle cx="60" cy="46" r="2"/></g>
				<path d="M50 30 L72 22 L82 40 L60 46 Z" fill="none" stroke="#9FF8FF" stroke-opacity=".7" stroke-width="1.5"/>
				<path d="M46 66 L64 58 L82 66" stroke="#3DF2FF" stroke-opacity=".5" stroke-width="2" fill="none"/>
				<rect x="28" y="72" width="72" height="42" rx="5" fill="url(#${p}-c)" ${O}/>
				<rect x="50" y="80" width="28" height="26" rx="3" fill="#0B1628" stroke="#3DF2FF" stroke-width="2"/>
				<path d="M34 80 H50 M34 92 H50 M78 86 H94 M78 98 H94 M60 80 V72 M68 114 V106" stroke="#3DF2FF" stroke-width="2"/>`,
				lg(`${p}-c`, [[0, "#2C3A58"], [1, "#101826"]]),
			),
		),

	// ===== Criaturas (Exploracion/Datos/Especies) =====
	criatura_medusa_vacio: (p) =>
		une(
			halo(`${p}-h`, "#7C6CFF", 64, 50, 40, 0.45),
			B(
				`<path d="M38 70 C34 86 44 96 40 112 M52 74 C50 90 58 100 54 118 M68 74 C70 92 62 100 68 118 M82 70 C88 84 80 96 86 110" fill="none" stroke="#9FF8FF" stroke-width="3" stroke-linecap="round" stroke-opacity=".85"/>
				<path d="M20 66 C20 36 40 18 64 18 C88 18 108 36 108 66 C100 74 90 70 84 74 C76 78 70 72 64 76 C58 72 52 78 44 74 C38 70 28 74 20 66 Z" fill="url(#${p}-c)" ${O}/>
				<path d="M34 48 C38 36 48 28 60 26" stroke="#fff" stroke-opacity=".7" stroke-width="3.5" stroke-linecap="round" fill="none"/>
				<g fill="#E8FDFF"><circle cx="54" cy="52" r="4"/><circle cx="74" cy="46" r="3"/><circle cx="86" cy="58" r="3.5"/><circle cx="64" cy="62" r="2.5"/></g>`,
				rg(`${p}-c`, [[0, "#E2DAFF", 0.95], [0.55, "#8D7BFF", 0.9], [1, "#3B2A9C", 0.95]], 0.45, 0.35, 0.8),
			),
		),
	criatura_brincador_lanudo: (p) =>
		B(
			`<path d="M36 50 C26 34 20 18 28 12 C36 8 46 26 48 44 Z" fill="#F4D9C2" ${O}/><path d="M34 44 C30 32 28 22 31 18" stroke="#F07C8A" stroke-width="5" stroke-linecap="round" fill="none"/>
			<path d="M92 50 C102 34 108 18 100 12 C92 8 82 26 80 44 Z" fill="#F4D9C2" ${O}/><path d="M94 44 C98 32 100 22 97 18" stroke="#F07C8A" stroke-width="5" stroke-linecap="round" fill="none"/>
			<rect x="34" y="94" width="16" height="22" rx="8" fill="#E7C7AA" ${O}/><rect x="78" y="94" width="16" height="22" rx="8" fill="#E7C7AA" ${O}/>
			<path d="M22 74 C20 52 38 38 64 38 C90 38 108 52 106 74 C104 96 88 106 64 106 C40 106 24 96 22 74 Z" fill="url(#${p}-c)" ${O}/>
			<path d="M26 70 C28 80 32 88 38 92 M102 70 C100 80 96 88 90 92" stroke="#2BA8A0" stroke-width="5" stroke-linecap="round" fill="none"/>
			<circle cx="48" cy="66" r="10" fill="#0B0B12"/><circle cx="80" cy="66" r="10" fill="#0B0B12"/>
			<circle cx="45" cy="62" r="3.5" fill="#fff"/><circle cx="77" cy="62" r="3.5" fill="#fff"/>
			<ellipse cx="64" cy="80" rx="5" ry="3.5" fill="#C9786F"/>
			<path d="M32 58 C36 48 46 42 56 41" stroke="#fff" stroke-opacity=".6" stroke-width="3" stroke-linecap="round" fill="none"/>`,
			rg(`${p}-c`, [[0, "#FFF4E6"], [0.6, "#F0D2B4"], [1, "#C69A78"]], 0.4, 0.3, 0.8),
		),
	criatura_acechador_abismo: (p) =>
		une(
			halo(`${p}-h`, "#C9A2FF", 64, 74, 16, 0.6),
			B(
				`<g fill="none" stroke="${CONTORNO}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
					<path d="M46 66 L22 44 L8 74 M44 74 L16 74 L6 104 M46 82 L24 96 L18 120 M82 66 L106 44 L120 74 M84 74 L112 74 L122 104 M82 82 L104 96 L110 120"/>
				</g>
				<g fill="none" stroke="#4B3A66" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
					<path d="M46 66 L22 44 L8 74 M44 74 L16 74 L6 104 M46 82 L24 96 L18 120 M82 66 L106 44 L120 74 M84 74 L112 74 L122 104 M82 82 L104 96 L110 120"/>
				</g>
				<path d="M48 40 L52 26 L56 40 M60 36 L64 18 L68 36 M72 40 L76 26 L80 40" fill="#D8C8A8" ${O2}/>
				<ellipse cx="64" cy="64" rx="26" ry="28" fill="url(#${p}-c)" ${O}/>
				<path d="M44 52 C50 42 58 38 66 38" stroke="#7E5CB8" stroke-width="3" stroke-linecap="round" fill="none"/>
				<path d="M52 92 L48 104 L56 98 M76 92 L80 104 L72 98" fill="#D8C8A8" ${O2}/>
				<g fill="#E5CCFF"><circle cx="56" cy="74" r="4.5"/><circle cx="72" cy="74" r="4.5"/><circle cx="64" cy="82" r="3.5"/><circle cx="48" cy="80" r="2.5"/><circle cx="80" cy="80" r="2.5"/></g>`,
				rg(`${p}-c`, [[0, "#5A4380"], [0.7, "#2A1E40"], [1, "#140E22"]], 0.4, 0.3, 0.8),
			),
		),
	criatura_reptador_lunar: (p) =>
		B(
			`<g stroke="${CONTORNO}" stroke-width="3" stroke-linecap="round">
				<path d="M30 92 L24 102 M46 98 L42 110 M62 100 L62 112 M78 98 L82 110 M94 90 L102 100"/>
			</g>
			<circle cx="28" cy="84" r="14" fill="url(#${p}-c)" ${O}/>
			<circle cx="46" cy="90" r="15" fill="url(#${p}-c)" ${O}/>
			<circle cx="64" cy="92" r="15" fill="url(#${p}-c)" ${O}/>
			<circle cx="82" cy="88" r="15" fill="url(#${p}-c)" ${O}/>
			<path d="M84 74 C84 52 94 36 108 34 C120 34 122 50 116 64 C110 78 98 84 90 82 Z" fill="url(#${p}-c)" ${O}/>
			<circle cx="108" cy="48" r="5" fill="#0B0B12"/><circle cx="106.5" cy="46.5" r="1.8" fill="#fff"/>
			<path d="M114 62 L120 66" stroke="${CONTORNO}" stroke-width="2.5" stroke-linecap="round"/>
			<g fill="#9FF8FF"><circle cx="46" cy="84" r="3"/><circle cx="64" cy="86" r="3"/><circle cx="82" cy="82" r="3"/><circle cx="28" cy="80" r="2.5"/></g>
			<path d="M96 40 C100 36 104 35 108 35" stroke="#fff" stroke-opacity=".6" stroke-width="2.5" stroke-linecap="round" fill="none"/>`,
			rg(`${p}-c`, [[0, "#F2F4FA"], [0.6, "#B9C0D2"], [1, "#6A7288"]], 0.4, 0.3, 0.8),
		),
	planta_flor_estelar: (p) =>
		une(
			halo(`${p}-h`, "#FFE27A", 64, 46, 34, 0.5),
			B(
				`<path d="M64 70 C62 88 66 100 64 120" stroke="${CONTORNO}" stroke-width="7" fill="none" stroke-linecap="round"/>
				<path d="M64 70 C62 88 66 100 64 120" stroke="#4AC97A" stroke-width="3.5" fill="none" stroke-linecap="round"/>
				<path d="M64 98 C52 86 36 88 30 98 C42 104 54 104 64 98 Z M64 106 C76 94 92 96 98 106 C86 112 74 112 64 106 Z" fill="#3FAE6A" ${O2}/>
				<path d="M64 8 L74 34 L102 30 L82 50 L96 76 L64 64 L32 76 L46 50 L26 30 L54 34 Z" fill="url(#${p}-p)" ${O}/>
				<circle cx="64" cy="46" r="11" fill="url(#${p}-n)" ${O2}/>
				<path d="M58 22 L62 32" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>`,
				rg(`${p}-p`, [[0, "#FFFFFF"], [0.5, "#FFF0A8"], [1, "#FFB800"]], 0.5, 0.45, 0.6) +
					rg(`${p}-n`, [[0, "#E8FDFF"], [1, "#3DF2FF"]], 0.4, 0.4, 0.7),
			),
		),
	planta_hongo_luminoso: (p) =>
		une(
			halo(`${p}-h`, "#4AFFC8", 58, 50, 34, 0.45),
			B(
				`<path d="M50 62 C48 82 46 98 42 114 H70 C66 98 66 82 66 62 Z" fill="url(#${p}-t)" ${O}/>
				<path d="M14 64 C14 36 34 18 58 18 C82 18 102 36 102 64 C86 70 30 70 14 64 Z" fill="url(#${p}-c)" ${O}/>
				<g fill="#E8FFF6"><circle cx="40" cy="44" r="5"/><circle cx="62" cy="32" r="4"/><circle cx="80" cy="48" r="5.5"/><circle cx="54" cy="54" r="3"/></g>
				<path d="M24 50 C28 38 38 28 50 24" stroke="#fff" stroke-opacity=".6" stroke-width="3" stroke-linecap="round" fill="none"/>
				<path d="M92 112 C92 104 92 98 94 92 H102 C102 98 102 104 104 112 Z" fill="url(#${p}-t)" ${O2}/>
				<path d="M82 94 C82 80 90 72 98 72 C106 72 114 80 114 94 C104 97 92 97 82 94 Z" fill="url(#${p}-c)" ${O2}/>`,
				lg(`${p}-t`, [[0, "#EAF2F0"], [1, "#8FA6A0"]]) + rg(`${p}-c`, [[0, "#C8FFF0"], [0.5, "#36D6B0"], [1, "#0E6E6A"]], 0.4, 0.3, 0.8),
			),
		),

	// ===== Planetas (datos de demostración salvo los dos de bando) =====
	planeta_nueva_tierra: (p) =>
		planeta(p, {
			base: [[0, "#7FC4FF"], [0.6, "#1E5BB8"], [1, "#0A2350"]],
			atmosfera: "#8CC4FF",
			detalles: `<path d="M26 50 C34 40 50 42 54 52 C58 62 48 70 38 68 C30 66 22 58 26 50 Z M70 34 C82 28 98 36 100 48 C96 58 84 56 76 50 C70 46 66 40 70 34 Z M62 78 C74 74 92 80 94 92 C86 104 70 100 64 92 C60 86 58 80 62 78 Z" fill="#4FB86A"/>
				<path d="M30 56 C36 52 44 54 48 58 M76 40 C84 38 92 42 94 46" stroke="#E8D9A8" stroke-width="3" fill="none" opacity=".7"/>
				<path d="M20 40 C40 34 60 38 80 30 M30 84 C50 92 80 70 108 76" stroke="#fff" stroke-width="5" stroke-linecap="round" fill="none" opacity=".75"/>`,
		}),
	planeta_umbra: (p) =>
		planeta(p, {
			base: [[0, "#4A3A5E"], [0.6, "#16121C"], [1, "#060408"]],
			atmosfera: "#8A2BE2",
			detalles: `<path d="M24 52 L40 58 L52 50 L66 62 L80 56 M36 84 L52 78 L60 90 L78 82 L92 92 M70 28 L76 40 L92 38" stroke="#C084FF" stroke-width="2.5" fill="none" stroke-linecap="round"/>
				<path d="M24 52 L40 58 L52 50 L66 62 L80 56" stroke="#8A2BE2" stroke-width="7" fill="none" opacity=".35"/>
				<circle cx="88" cy="70" r="9" fill="#0A070E" stroke="#5B1F7A" stroke-width="2"/>`,
		}),
	planeta_verdalia: (p) =>
		planeta(p, {
			base: [[0, "#B8F5A8"], [0.6, "#3E9E5C"], [1, "#123A24"]],
			atmosfera: "#9CFFC0",
			detalles: `<path d="M20 60 C40 52 60 64 80 56 C94 50 104 56 112 52 M18 80 C40 74 64 88 90 80" stroke="#2E7A48" stroke-width="7" fill="none" opacity=".7"/>
				<path d="M30 36 C44 30 56 34 66 30 M54 98 C70 92 86 100 100 94" stroke="#fff" stroke-width="5" stroke-linecap="round" fill="none" opacity=".8"/>
				<circle cx="76" cy="66" r="7" fill="#3DA8E0" opacity=".9"/>`,
		}),
	planeta_ignea: (p) =>
		planeta(p, {
			base: [[0, "#7A3A2A"], [0.6, "#3A1410"], [1, "#120504"]],
			atmosfera: "#FF8844",
			detalles: `<path d="M22 46 L40 54 L48 44 L64 56 L82 48 L100 60 M30 78 L48 72 L56 86 L74 78 L94 90 M58 22 L64 36 L80 32" stroke="#FFB070" stroke-width="2.5" fill="none" stroke-linecap="round"/>
				<path d="M22 46 L40 54 L48 44 L64 56 L82 48 L100 60 M30 78 L48 72 L56 86 L74 78 L94 90" stroke="#FF6A1A" stroke-width="8" fill="none" opacity=".45"/>
				<circle cx="44" cy="64" r="5" fill="#FFB800" opacity=".9"/>`,
		}),
	planeta_nerea: (p) =>
		planeta(p, {
			base: [[0, "#9FE6FF"], [0.6, "#1F7FC0"], [1, "#062A4A"]],
			atmosfera: "#7FE3FF",
			detalles: `<path d="M18 52 C36 44 54 58 72 50 C88 44 100 52 112 46 M16 74 C36 66 56 80 78 72 C94 66 104 72 112 70 M26 94 C46 88 66 100 90 94" stroke="#BDF2FF" stroke-width="3.5" fill="none" opacity=".55"/>
				<circle cx="80" cy="40" r="4" fill="#E8D9A8"/>`,
		}),
	planeta_grisalla: (p) =>
		planeta(p, {
			base: [[0, "#D9DCE3"], [0.6, "#7C828C"], [1, "#2A2E36"]],
			atmosfera: "#C9CED8",
			detalles: `<g fill="#5A6070" stroke="#ECEFF4" stroke-opacity=".5" stroke-width="1.5">
					<circle cx="46" cy="50" r="9"/><circle cx="78" cy="38" r="6"/><circle cx="74" cy="78" r="11"/><circle cx="40" cy="86" r="5"/><circle cx="96" cy="62" r="4"/>
				</g>`,
		}),

	// ===== Tienda: cosméticos y pases (nada que dé ventaja en combate) =====
	skin_nebula: (p) =>
		une(
			halo(`${p}-h`, "#C66BFF", 64, 64, 40, 0.4),
			B(
				`<path d="M64 8 L76 44 L116 82 L112 94 L76 84 L70 104 H58 L52 84 L16 94 L12 82 L52 44 Z" fill="url(#${p}-n)" ${O}/>
				<path d="M64 20 L70 46 H58 Z" fill="#E8FDFF" ${O2}/>
				<g fill="#fff"><circle cx="44" cy="74" r="1.8"/><circle cx="86" cy="68" r="2.2"/><circle cx="96" cy="84" r="1.5"/><circle cx="64" cy="70" r="2"/><circle cx="30" cy="84" r="1.5"/></g>
				<path d="M58 104 L54 120 M70 104 L74 120" stroke="#FF8844" stroke-width="5" stroke-linecap="round"/>
				<path d="M58 104 L56 114 M70 104 L72 114" stroke="#FFE0A8" stroke-width="2.5" stroke-linecap="round"/>`,
				lg(`${p}-n`, [[0, "#3DF2FF"], [0.45, "#A07AE8"], [0.8, "#FF4FA8"], [1, "#4A1A7A"]], 0, 0, 1, 1),
			),
		),
	estela_aurora: (p) =>
		B(
			`<path d="M10 118 C30 96 40 70 64 58 C78 52 90 50 98 40" stroke="url(#${p}-a)" stroke-width="22" stroke-linecap="round" fill="none" opacity=".85"/>
			<path d="M14 116 C32 96 44 74 66 62 C80 56 90 52 98 42" stroke="#fff" stroke-opacity=".6" stroke-width="3" stroke-linecap="round" fill="none"/>
			<path d="M118 10 L112 42 L102 46 L96 40 L88 34 L92 24 Z" fill="#F2F4F8" ${O}/>
			<path d="M118 10 L104 36" stroke="#FF8844" stroke-width="3"/>`,
			lg(`${p}-a`, [[0, "#4AFF8B", 0], [0.4, "#4AFF8B"], [0.7, "#3DF2FF"], [1, "#A07AE8"]], 0, 1, 1, 0),
		),
	aura_cosmica: (p) =>
		une(
			halo(`${p}-h`, "#A07AE8", 64, 66, 46, 0.55),
			B(
				`<path d="M64 6 C74 20 70 30 80 38 C90 30 92 22 96 14 C104 34 98 50 108 64 C112 90 92 118 64 120 C36 118 16 90 20 64 C30 50 24 34 32 14 C36 22 38 30 48 38 C58 30 54 20 64 6 Z" fill="url(#${p}-a)" opacity=".85"/>
				<rect x="52" y="28" width="24" height="22" rx="4" fill="#E0E6F0" ${O2}/>
				<rect x="46" y="52" width="36" height="34" rx="2" fill="#C9CED8" ${O2}/>
				<rect x="32" y="52" width="13" height="34" rx="2" fill="#AEB6C6" ${O2}/><rect x="83" y="52" width="13" height="34" rx="2" fill="#AEB6C6" ${O2}/>
				<rect x="46" y="87" width="17" height="30" rx="2" fill="#9AA3B5" ${O2}/><rect x="65" y="87" width="17" height="30" rx="2" fill="#9AA3B5" ${O2}/>`,
				lg(`${p}-a`, [[0, "#3DF2FF"], [0.5, "#A07AE8"], [1, "#4A1A7A"]], 0, 0, 0, 1),
			),
		),
	pack_explorador: (p) =>
		une(
			halo(`${p}-h`, "#3DF2FF", 64, 60, 30, 0.35),
			B(
				`<path d="M18 50 L64 30 L110 50 L64 70 Z" fill="url(#${p}-t)" ${O}/>
				<path d="M18 50 V94 L64 116 V70 Z" fill="url(#${p}-l)" ${O}/>
				<path d="M110 50 V94 L64 116 V70 Z" fill="url(#${p}-r)" ${O}/>
				<path d="M18 72 L64 94 L110 72" stroke="#3DF2FF" stroke-width="3" fill="none"/>
				<path d="M41 40 L87 60" stroke="#3DF2FF" stroke-width="3"/>
				<path d="M86 84 L92 90 L98 80" stroke="#FFB800" stroke-width="3.5" fill="none" stroke-linecap="round"/>
				<path d="M30 50 L58 38" stroke="#fff" stroke-opacity=".6" stroke-width="2.5" stroke-linecap="round"/>`,
				lg(`${p}-t`, [[0, "#6B7894"], [1, "#3A4560"]]) + lg(`${p}-l`, [[0, "#4A5670"], [1, "#222A3C"]]) + lg(`${p}-r`, [[0, "#36405A"], [1, "#151B2A"]]),
			),
		),
	pase_x2: (p) =>
		B(
			`<ellipse cx="54" cy="92" rx="34" ry="12" fill="#B37A00" ${O}/>
			<path d="M20 80 V92 C20 99 35 104 54 104 C73 104 88 99 88 92 V80" fill="#C98A00" ${O}/>
			<ellipse cx="54" cy="80" rx="34" ry="12" fill="url(#${p}-m)" ${O}/>
			<path d="M20 64 V76 C20 83 35 88 54 88 C73 88 88 83 88 76 V64" fill="#D99A10" ${O}/>
			<ellipse cx="54" cy="64" rx="34" ry="12" fill="url(#${p}-m)" ${O}/>
			<path d="M54 56 L62 64 L54 72 L46 64 Z" fill="#8A5A00"/>
			<text x="94" y="50" text-anchor="middle" font-family="Montserrat, Gotham, Arial, sans-serif" font-weight="800" font-size="34" fill="#fff" stroke="${CONTORNO}" stroke-width="3" paint-order="stroke">x2</text>`,
			lg(`${p}-m`, [[0, "#FFF0A8"], [1, "#FFB800"]]),
		),
	pase_almacen: (p) =>
		B(
			`<path d="M20 46 L28 20 H100 L108 46 Z" fill="url(#${p}-t)" ${O}/>
			<path d="M14 46 H114 V104 L104 114 H24 L14 104 Z" fill="url(#${p}-c)" ${O}/>
			<path d="M14 66 H114" stroke="${CONTORNO}" stroke-opacity=".35" stroke-width="2.5"/>
			<rect x="52" y="56" width="24" height="22" rx="4" fill="#FFB800" ${O2}/>
			<path d="M36 90 L28 98 M28 90 V98 H36 M92 90 L100 98 M100 90 V98 H92" stroke="#3DF2FF" stroke-width="3.5" fill="none" stroke-linecap="round"/>
			<path d="M24 52 H70" stroke="#fff" stroke-opacity=".5" stroke-width="2.5" stroke-linecap="round"/>`,
			lg(`${p}-t`, [[0, "#7E8AA6"], [1, "#3A4560"]]) + lg(`${p}-c`, [[0, "#5F6B85"], [1, "#22293A"]]),
		),
	pase_vip: (p) =>
		une(
			halo(`${p}-h`, "#FFB800", 64, 64, 36, 0.4),
			B(
				`<rect x="16" y="30" width="96" height="68" rx="10" fill="url(#${p}-c)" ${O}/>
				<rect x="22" y="36" width="84" height="56" rx="7" fill="none" stroke="#FFF0A8" stroke-opacity=".6" stroke-width="2"/>
				<path d="M44 30 L46 14 L55 22 L64 10 L73 22 L82 14 L84 30 Z" fill="#FFD24A" ${O}/>
				<text x="64" y="80" text-anchor="middle" font-family="Montserrat, Gotham, Arial, sans-serif" font-weight="800" font-size="30" fill="#2A1A00">VIP</text>
				<path d="M24 44 H64" stroke="#fff" stroke-opacity=".7" stroke-width="3" stroke-linecap="round"/>`,
				lg(`${p}-c`, [[0, "#FFE08A"], [0.5, "#FFB800"], [1, "#FF8800"]]),
			),
		),
};

// Contenido final de cada pieza (con su <defs>).
export const ARTE = Object.fromEntries(
	Object.entries(PIEZAS).map(([nombre, fn]) => {
		const { defs, body } = fn(`a-${nombre}`);
		return [nombre, `<defs>${defs}</defs>${body}`];
	}),
);

export const GRUPOS_ARTE = [
	["Minerales", ["item_hierro", "item_cobre", "item_titanio", "item_cristal", "item_cristal_abisal"]],
	["Componentes", ["item_lingote_hierro", "item_cable_cobre", "item_lente_cristal", "item_placa_titanio", "item_nucleo_energia"]],
	[
		"Equipo",
		[
			"item_espada_plasma",
			"item_pistola_foton",
			"item_casco_nova",
			"item_peto_reactor",
			"item_amuleto_vacio",
			"item_anillo_estelar",
			"item_cinturon_tactico",
			"item_botas_gravitatorias",
		],
	],
	["Consumibles y especial", ["item_botiquin", "item_celula_energia", "item_chip_estelar"]],
	[
		"Criaturas y plantas",
		["criatura_medusa_vacio", "criatura_brincador_lanudo", "criatura_acechador_abismo", "criatura_reptador_lunar", "planta_flor_estelar", "planta_hongo_luminoso"],
	],
	["Planetas", ["planeta_nueva_tierra", "planeta_umbra", "planeta_verdalia", "planeta_ignea", "planeta_nerea", "planeta_grisalla"]],
	["Tienda", ["skin_nebula", "estela_aurora", "aura_cosmica", "pack_explorador", "pase_x2", "pase_almacen", "pase_vip"]],
];
