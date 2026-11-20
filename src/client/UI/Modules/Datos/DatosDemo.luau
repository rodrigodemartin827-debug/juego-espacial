--!strict
--[[
	DatosDemo: datos de DEMOSTRACIÓN para las partes de la interfaz cuyos sistemas todavía no existen en el juego
	(equipo y atributos, árbol de poderes, clanes, ranked, gemas, planetas pequeños, builds...).

	Son los mismos datos que enseña el preview HTML, para que lo que Rodrigo aprueba en el navegador sea lo que
	se ve en Studio. Lo que SÍ existe ya en el juego (nivel, monedas, bando, inventario de materiales, especies
	descubiertas, poderes y sus cooldowns, vida) no sale de aquí sino de los datos reales (ver EstadoUI).

	Cuando un sistema exista, se borra su sección de aquí y EstadoUI pasa a leerlo del servidor.
]]

local DatosDemo = {}

-- ===== Jugador (lo que aún no guarda el servidor) =====
DatosDemo.Jugador = {
	Clan = "ARBUSTIX",
	Titulo = "Explorador Estelar",
	Clase = "Explorador",
	Gemas = 34,
	PuntosStats = 3,
	PuntosHabilidad = 7,
	FraccionXP = 0.68, -- TODO: fórmula de XP por nivel (todavía no existe en el juego)
}

-- ===== Atributos: { base, bonus del equipo } =====
DatosDemo.Stats = {
	Fuerza = { 45, 12 },
	Aguante = { 320, 8 },
	Espada = { 280, 34 },
	Arma = { 150, 5 },
	Habilidad = { 95, 20 },
} :: { [string]: { number } }
DatosDemo.StatMaximo = 400 -- para las barritas bajo cada atributo

-- Estadísticas rápidas del HUD (Stat = de qué color se pinta).
export type Valor = { Etiqueta: string, Stat: string, Valor: number, Bonus: number }
DatosDemo.Rapidas = {
	{ Etiqueta = "DMG", Stat = "Espada", Valor = 168, Bonus = 29 },
	{ Etiqueta = "SPD", Stat = "Aguante", Valor = 16, Bonus = 0.9 },
	{ Etiqueta = "DEF", Stat = "Fuerza", Valor = 320, Bonus = 8 },
} :: { Valor }

-- Escudo personal (todavía no existe: la vida sí es real, la del Humanoid).
DatosDemo.Escudo = { 800, 1200 }

-- ===== Razas (panel derecho del personaje) =====
export type Pasiva = { Nombre: string, Texto: string, Color: string } -- Color: clave de Theme.Colores
export type Raza = {
	Nombre: string,
	Clase: string,
	Icono: string,
	Color: string,
	Bando: string,
	Pasivas: { Pasiva },
	Detalle: { Valor },
}
DatosDemo.Razas = {
	Humanos = {
		Nombre = "Humano",
		Clase = "Explorador",
		Icono = "raza_humano",
		Color = "BandoHumanos",
		Bando = "BANDO HUMANOS",
		Pasivas = {
			{
				Nombre = "Adaptación atmosférica",
				Texto = "Respira en cualquier atmósfera sin casco.",
				Color = "Acento",
			},
			{ Nombre = "+15% daño con armas", Texto = "Las armas de fuego hacen más daño.", Color = "Aguante" },
			{
				Nombre = "Reparación rápida de naves",
				Texto = "Repara el casco de la nave un 40% antes.",
				Color = "Dorado",
			},
		},
		Detalle = {
			{ Etiqueta = "SALUD", Valor = 2400, Bonus = 320, Stat = "Aguante" },
			{ Etiqueta = "RESISTENCIA", Valor = 1800, Bonus = 120, Stat = "Aguante" },
			{ Etiqueta = "VELOCIDAD", Valor = 16, Bonus = 0.9, Stat = "Espada" },
			{ Etiqueta = "DMG ESPADA", Valor = 168, Bonus = 29, Stat = "Espada" },
			{ Etiqueta = "DMG ARMA", Valor = 95, Bonus = 12, Stat = "Arma" },
			{ Etiqueta = "DMG HABILIDAD", Valor = 72, Bonus = 18, Stat = "Habilidad" },
		},
	},
	Monstruos = {
		Nombre = "Monstruo",
		Clase = "Acechador",
		Icono = "raza_monstruo",
		Color = "BandoMonstruos",
		Bando = "BANDO MONSTRUOS",
		Pasivas = {
			{
				Nombre = "Visión en la penumbra",
				Texto = "Ve en la oscuridad del planeta del agujero negro.",
				Color = "Acento",
			},
			{ Nombre = "+20% vida máxima", Texto = "Más fuerza, agilidad y vida que un humano.", Color = "Aguante" },
			{
				Nombre = "Regeneración en la sombra",
				Texto = "Recupera vida lejos de la luz del sol.",
				Color = "Dorado",
			},
		},
		Detalle = {
			{ Etiqueta = "SALUD", Valor = 2900, Bonus = 380, Stat = "Aguante" },
			{ Etiqueta = "RESISTENCIA", Valor = 2100, Bonus = 140, Stat = "Aguante" },
			{ Etiqueta = "VELOCIDAD", Valor = 18, Bonus = 1.4, Stat = "Espada" },
			{ Etiqueta = "DMG ESPADA", Valor = 182, Bonus = 31, Stat = "Espada" },
			{ Etiqueta = "DMG ARMA", Valor = 70, Bonus = 6, Stat = "Arma" },
			{ Etiqueta = "DMG HABILIDAD", Valor = 88, Bonus = 22, Stat = "Habilidad" },
		},
	},
} :: { [string]: Raza }

-- ===== Slots del muñeco =====
export type Slot = { Id: string, Nombre: string, Icono: string, Color: string, Lado: number }
DatosDemo.Slots = {
	{ Id = "Casco", Nombre = "Casco", Icono = "slot_casco", Color = "Aguante", Lado = 0 },
	{ Id = "Armadura", Nombre = "Armadura", Icono = "slot_armadura", Color = "Aguante", Lado = 0 },
	{ Id = "Espada", Nombre = "Espada", Icono = "slot_espada", Color = "Espada", Lado = 0 },
	{ Id = "Arma", Nombre = "Arma de fuego", Icono = "slot_arma", Color = "Arma", Lado = 0 },
	{ Id = "Amuleto", Nombre = "Amuleto", Icono = "slot_amuleto", Color = "Habilidad", Lado = 1 },
	{ Id = "Anillo", Nombre = "Anillo", Icono = "slot_anillo", Color = "Habilidad", Lado = 1 },
	{ Id = "Cinturon", Nombre = "Cinturón", Icono = "slot_cinturon", Color = "Fuerza", Lado = 1 },
	{ Id = "Botas", Nombre = "Botas", Icono = "slot_botas", Color = "Aguante", Lado = 1 },
} :: { Slot }

-- ===== Objetos de equipo y especiales (todavía no existen en Exploracion/Datos/Objetos) =====
export type ObjetoDemo = {
	Id: string,
	Nombre: string,
	Arte: string,
	Filtro: string,
	Slot: string?,
	Rareza: string,
	Nivel: number?,
	Cantidad: number?,
	Stats: { Valor }?,
	Descripcion: string,
	Pasiva: string?,
}
DatosDemo.Objetos = {
	{
		Id = "EspadaPlasma",
		Nombre = "Espada de Plasma",
		Arte = "item_espada_plasma",
		Filtro = "Armas",
		Slot = "Espada",
		Rareza = "Raro",
		Nivel = 45,
		Stats = {
			{ Stat = "Espada", Etiqueta = "DMG", Valor = 168, Bonus = 29 },
			{ Stat = "Fuerza", Etiqueta = "IMPACTO", Valor = 12, Bonus = 0 },
		},
		Descripcion = "Hoja de plasma confinado en un campo magnético. Corta el blindaje ligero como si fuera papel.",
		Pasiva = "10% de probabilidad de quemar al enemigo durante 3 s.",
	},
	{
		Id = "PistolaFoton",
		Nombre = "Pistola Fotón",
		Arte = "item_pistola_foton",
		Filtro = "Armas",
		Slot = "Arma",
		Rareza = "Epico",
		Nivel = 52,
		Stats = {
			{ Stat = "Arma", Etiqueta = "DMG", Valor = 95, Bonus = 12 },
			{ Stat = "Arma", Etiqueta = "CADENCIA", Valor = 4, Bonus = 0.5 },
		},
		Descripcion = "Dispara ráfagas de fotones comprimidos. La celda naranja se recarga sola.",
		Pasiva = "Cada 5 disparos, el siguiente atraviesa escudos.",
	},
	{
		Id = "CascoNova",
		Nombre = "Casco Nova",
		Arte = "item_casco_nova",
		Filtro = "Armadura",
		Slot = "Casco",
		Rareza = "Legendario",
		Nivel = 60,
		Stats = {
			{ Stat = "Aguante", Etiqueta = "DEF", Valor = 64, Bonus = 8 },
			{ Stat = "Habilidad", Etiqueta = "ENFRIAMIENTO", Valor = 6, Bonus = 0 },
		},
		Descripcion = "Casco de exploración con visor de oro reflectante. Fabricado en Nueva Tierra.",
		Pasiva = "Inmune al cegado de las explosiones.",
	},
	{
		Id = "PetoReactor",
		Nombre = "Peto Reactor",
		Arte = "item_peto_reactor",
		Filtro = "Armadura",
		Slot = "Armadura",
		Rareza = "Epico",
		Nivel = 48,
		Stats = {
			{ Stat = "Aguante", Etiqueta = "DEF", Valor = 120, Bonus = 0 },
			{ Stat = "Aguante", Etiqueta = "VIDA", Valor = 320, Bonus = 0 },
		},
		Descripcion = "Blindaje con un núcleo de energía en el pecho que alimenta el escudo personal.",
		Pasiva = "El escudo se recarga un 20% más rápido.",
	},
	{
		Id = "BotasGravitatorias",
		Nombre = "Botas gravitatorias",
		Arte = "item_botas_gravitatorias",
		Filtro = "Armadura",
		Slot = "Botas",
		Rareza = "PocoComun",
		Nivel = 30,
		Stats = {
			{ Stat = "Espada", Etiqueta = "SPD", Valor = 0.9, Bonus = 0 },
			{ Stat = "Aguante", Etiqueta = "DEF", Valor = 22, Bonus = 0 },
		},
		Descripcion = "Suelas que se agarran a cualquier superficie. Útiles en asteroides.",
	},
	{
		Id = "CinturonTactico",
		Nombre = "Cinturón táctico",
		Arte = "item_cinturon_tactico",
		Filtro = "Armadura",
		Slot = "Cinturon",
		Rareza = "Comun",
		Nivel = 10,
		Stats = { { Stat = "Aguante", Etiqueta = "DEF", Valor = 8, Bonus = 0 } },
		Descripcion = "Cinturón con cartuchera para dos consumibles más.",
	},
	{
		Id = "AmuletoVacio",
		Nombre = "Amuleto del Vacío",
		Arte = "item_amuleto_vacio",
		Filtro = "Armadura",
		Slot = "Amuleto",
		Rareza = "Epico",
		Nivel = 50,
		Stats = { { Stat = "Habilidad", Etiqueta = "DMG HAB.", Valor = 20, Bonus = 0 } },
		Descripcion = "Una gema que absorbe la luz que la rodea.",
		Pasiva = "Las habilidades cuestan un 10% menos de energía.",
	},
	{
		Id = "AnilloEstelar",
		Nombre = "Anillo Estelar",
		Arte = "item_anillo_estelar",
		Filtro = "Armadura",
		Slot = "Anillo",
		Rareza = "Raro",
		Nivel = 40,
		Stats = { { Stat = "Fuerza", Etiqueta = "FUERZA", Valor = 12, Bonus = 0 } },
		Descripcion = "Oro forjado con polvo de estrella. Brilla más cerca de los soles.",
	},
	{
		Id = "Botiquin",
		Nombre = "Botiquín",
		Arte = "item_botiquin",
		Filtro = "Consumibles",
		Rareza = "Comun",
		Cantidad = 5,
		Stats = { { Stat = "Aguante", Etiqueta = "CURA", Valor = 600, Bonus = 0 } },
		Descripcion = "Restaura 600 de vida en 2 segundos.",
	},
	{
		Id = "CelulaEnergia",
		Nombre = "Célula de energía",
		Arte = "item_celula_energia",
		Filtro = "Consumibles",
		Rareza = "PocoComun",
		Cantidad = 3,
		Stats = { { Stat = "Habilidad", Etiqueta = "ENERGÍA", Valor = 50, Bonus = 0 } },
		Descripcion = "Recarga 50 de energía al instante.",
	},
	{
		Id = "CristalAbisal",
		Nombre = "Cristal abisal",
		Arte = "item_cristal_abisal",
		Filtro = "Especial",
		Rareza = "Mitico",
		Cantidad = 2,
		Descripcion = "Solo existe en Umbra, el planeta de los monstruos. Vibra cerca del agujero negro.",
		Pasiva = "Material de forja único del bando Monstruos.",
	},
	{
		Id = "ChipEstelar",
		Nombre = "Chip estelar",
		Arte = "item_chip_estelar",
		Filtro = "Especial",
		Rareza = "Legendario",
		Cantidad = 1,
		Descripcion = "Guarda las coordenadas de un sector lejano. Alguien lo perdió en un campo de asteroides.",
	},
} :: { ObjetoDemo }

DatosDemo.Equipado = {
	Casco = "CascoNova",
	Armadura = "PetoReactor",
	Espada = "EspadaPlasma",
	Arma = "PistolaFoton",
	Amuleto = "AmuletoVacio",
	Anillo = "AnilloEstelar",
	Botas = "BotasGravitatorias",
} :: { [string]: string }

DatosDemo.CasillasOcultas = 10 -- casillas "?" al final del inventario (objetos que aún no has encontrado)

-- ===== Builds =====
DatosDemo.Builds = {
	{
		Nombre = "Espadachín de plasma",
		Enfoque = "Espada",
		Reparto = { Fuerza = 60, Aguante = 40, Espada = 100, Arma = 10, Habilidad = 30 },
	},
	{
		Nombre = "Pistolero fotónico",
		Enfoque = "Arma",
		Reparto = { Fuerza = 20, Aguante = 40, Espada = 10, Arma = 100, Habilidad = 50 },
	},
	{
		Nombre = "Explorador blindado",
		Enfoque = "Aguante",
		Reparto = { Fuerza = 30, Aguante = 100, Espada = 40, Arma = 30, Habilidad = 40 },
	},
}
DatosDemo.BuildActiva = 1

-- ===== Árbol de poderes =====
-- E: 1 = desbloqueado. La progresión es lineal dentro de cada rama (cada nodo pide el anterior).
-- Cd: cooldown en segundos (0 = pasiva). En: coste de energía. Los de Combate son los poderes reales del juego.
export type Nodo = { N: string, I: string, T: number, Coste: number, E: number, D: string, Cd: number, En: number }
export type Rama = { Id: string, Nombre: string, Nodos: { Nodo } }
DatosDemo.Arbol = {
	{
		Id = "Combate",
		Nombre = "COMBATE",
		Nodos = {
			{
				N = "Golpe de Plasma",
				I = "hab_combo",
				T = 1,
				Coste = 1,
				E = 1,
				D = "Inflige 200% del daño de espada en área delante de ti.",
				Cd = 8,
				En = 30,
			},
			{
				N = "Chispa Voltaica",
				I = "hab_rayo",
				T = 1,
				Coste = 1,
				E = 1,
				D = "Lanza un rayo veloz en línea recta.",
				Cd = 1.2,
				En = 8,
			},
			{
				N = "Pulso Gravitatorio",
				I = "hab_pulso",
				T = 1,
				Coste = 1,
				E = 0,
				D = "Lanza una esfera de gravedad que aplasta lo que toca.",
				Cd = 1.4,
				En = 8,
			},
			{
				N = "Trueno Divino",
				I = "hab_trueno",
				T = 2,
				Coste = 2,
				E = 0,
				D = "Invoca un rayo del cielo que cae sobre la zona señalada.",
				Cd = 6,
				En = 25,
			},
			{
				N = "Aplastamiento",
				I = "hab_aplastar",
				T = 2,
				Coste = 2,
				E = 0,
				D = "Multiplica la gravedad en una zona y la hunde contra el suelo.",
				Cd = 7,
				En = 25,
			},
			{
				N = "Furia del núcleo",
				I = "hab_aura",
				T = 3,
				Coste = 3,
				E = 0,
				D = "Durante 8 s, cada golpe recarga 5 de energía.",
				Cd = 30,
				En = 40,
			},
			{
				N = "Tormenta Celestial",
				I = "hab_tormenta",
				T = 4,
				Coste = 5,
				E = 0,
				D = "Desata una tormenta eléctrica devastadora sobre una gran zona.",
				Cd = 45,
				En = 80,
			},
		},
	},
	{
		Id = "Exploracion",
		Nombre = "EXPLORACIÓN",
		Nodos = {
			{
				N = "Escáner profundo",
				I = "hab_escaner",
				T = 1,
				Coste = 1,
				E = 1,
				D = "El escáner analiza un 25% más rápido y desde más lejos.",
				Cd = 0,
				En = 0,
			},
			{
				N = "Propulsión",
				I = "hab_propulsor",
				T = 1,
				Coste = 1,
				E = 1,
				D = "Doble salto con los propulsores del traje.",
				Cd = 4,
				En = 10,
			},
			{
				N = "Pasos sigilosos",
				I = "hab_sigilo",
				T = 1,
				Coste = 1,
				E = 1,
				D = "Las criaturas tardan más en detectarte.",
				Cd = 0,
				En = 0,
			},
			{
				N = "Salto de fase",
				I = "hab_salto",
				T = 2,
				Coste = 2,
				E = 1,
				D = "Te teletransportas 12 studs en la dirección en la que miras.",
				Cd = 10,
				En = 20,
			},
			{
				N = "Ojo de halcón",
				I = "hab_escaner",
				T = 2,
				Coste = 2,
				E = 0,
				D = "Marca a los enemigos cercanos en el minimapa durante 6 s.",
				Cd = 20,
				En = 15,
			},
			{
				N = "Cartógrafo estelar",
				I = "sidebar_mapa",
				T = 3,
				Coste = 3,
				E = 0,
				D = "Los planetas que escaneas desde la nave revelan sus recursos.",
				Cd = 0,
				En = 0,
			},
			{
				N = "Singularidad",
				I = "hab_singularidad",
				T = 4,
				Coste = 5,
				E = 0,
				D = "Abre un agujero negro que arrastra a los enemigos y colapsa en una explosión.",
				Cd = 50,
				En = 80,
			},
		},
	},
	{
		Id = "Soporte",
		Nombre = "SOPORTE",
		Nodos = {
			{
				N = "Nanobots curativos",
				I = "hab_curar",
				T = 1,
				Coste = 1,
				E = 1,
				D = "Curas 300 de vida a ti y a los aliados cercanos.",
				Cd = 15,
				En = 30,
			},
			{
				N = "Escudo personal",
				I = "hab_escudo",
				T = 1,
				Coste = 1,
				E = 0,
				D = "Un escudo absorbe 400 de daño durante 5 s.",
				Cd = 18,
				En = 25,
			},
			{
				N = "Aura de ánimo",
				I = "hab_aura",
				T = 1,
				Coste = 1,
				E = 0,
				D = "Los aliados cercanos hacen un 8% más de daño.",
				Cd = 0,
				En = 0,
			},
			{
				N = "Dron de reparación",
				I = "hab_dron",
				T = 2,
				Coste = 2,
				E = 0,
				D = "Un dron te sigue y repara la nave o el escudo.",
				Cd = 25,
				En = 35,
			},
			{
				N = "Baliza de reagrupación",
				I = "ui_posicion",
				T = 2,
				Coste = 2,
				E = 0,
				D = "Los aliados pueden teletransportarse a tu lado una vez.",
				Cd = 60,
				En = 40,
			},
			{
				N = "Escudo de grupo",
				I = "hab_escudo",
				T = 3,
				Coste = 3,
				E = 0,
				D = "Extiende tu escudo personal a todo el grupo.",
				Cd = 40,
				En = 50,
			},
			{
				N = "Renacer estelar",
				I = "hab_curar",
				T = 4,
				Coste = 5,
				E = 0,
				D = "Revive a un aliado caído con toda su vida.",
				Cd = 120,
				En = 100,
			},
		},
	},
} :: { Rama }

-- ===== Clan =====
-- Miembro: rango ("Lider" | "Oficial" | "Miembro"), estado ("Online" | "AFK" | "Offline"), hace cuánto se fue, si eres tú.
export type Miembro = { Rango: string, Nombre: string, Nivel: number, Estado: string, Hace: string?, Tu: boolean? }
DatosDemo.Clan = {
	Nombre = "ARBUSTIX",
	Siglas = "AX",
	Nivel = 12,
	Lema = "Exploradores del cosmos",
	Maximo = 50,
	Miembros = 24,
	Ranking = 87,
	Planeta = "Verdalia",
	Puntos = 18420,
	Lista = {
		{ Rango = "Lider", Nombre = "Rodrixx_777", Nivel = 127, Estado = "Online", Tu = true },
		{ Rango = "Oficial", Nombre = "xDarkStar", Nivel = 98, Estado = "Online" },
		{ Rango = "Oficial", Nombre = "Lyra_Vex", Nivel = 91, Estado = "AFK" },
		{ Rango = "Miembro", Nombre = "Astra_IX", Nivel = 88, Estado = "Online" },
		{ Rango = "Miembro", Nombre = "NovaPlayer", Nivel = 76, Estado = "AFK" },
		{ Rango = "Miembro", Nombre = "Zeta_Ruiz", Nivel = 71, Estado = "Online" },
		{ Rango = "Miembro", Nombre = "Kronos_X", Nivel = 67, Estado = "Offline", Hace = "hace 1 d" },
		{ Rango = "Miembro", Nombre = "LunaDrift", Nivel = 62, Estado = "Online" },
		{ Rango = "Miembro", Nombre = "Orion_Byte", Nivel = 58, Estado = "Offline", Hace = "hace 3 d" },
		{ Rango = "Miembro", Nombre = "SpaceCat_22", Nivel = 54, Estado = "Offline", Hace = "hace 2 h" },
		{ Rango = "Miembro", Nombre = "PixelNomad", Nivel = 49, Estado = "Online" },
		{ Rango = "Miembro", Nombre = "Mr_Quasar", Nivel = 33, Estado = "Offline", Hace = "hace 5 min" },
		{ Rango = "Miembro", Nombre = "Vega_Kai", Nivel = 29, Estado = "Offline", Hace = "hace 6 h" },
		{ Rango = "Miembro", Nombre = "Nebulina", Nivel = 21, Estado = "Online" },
	} :: { Miembro },
	Actividad = {
		{ Quien = "xDarkStar", Que = "derrotó al Leviatán", Cuando = "hace 12 min" },
		{ Quien = "Lyra_Vex", Que = "descubrió el planeta Nerea", Cuando = "hace 1 h" },
		{ Quien = "Astra_IX", Que = "subió a Platino II", Cuando = "hace 3 h" },
	},
}
-- Rangos del clan: nombre, color (clave de Theme.Colores) e icono (sin icono = un punto).
export type RangoClan = { Nombre: string, Color: string, Icono: string? }
DatosDemo.RangosClan = {
	Lider = { Nombre = "Líder", Color = "Dorado", Icono = "ui_estrella" },
	Oficial = { Nombre = "Oficial", Color = "Acento", Icono = "stat_espada" },
	Miembro = { Nombre = "Miembro", Color = "Gris" },
} :: { [string]: RangoClan }

-- ===== Ranked =====
DatosDemo.Ranked = {
	Rango = "Plata",
	Division = "III",
	Elo = 1247,
	Siguiente = 1500,
	Victorias = 84,
	Derrotas = 41,
	Racha = 3,
	Posicion = 1284,
	Modos = {
		{ Modo = "1v1", Jugadores = 1, Espera = "~0:40" },
		{ Modo = "2v2", Jugadores = 2, Espera = "~1:10" },
		{ Modo = "3v3", Jugadores = 3, Espera = "~1:45" },
		{ Modo = "4v4", Jugadores = 4, Espera = "~2:30" },
	},
	Tabla = {
		{ Nombre = "xProGamer", Rango = "Estelar", Elo = 4891 },
		{ Nombre = "NovaKiller", Rango = "Diamante", Elo = 3456 },
		{ Nombre = "Vexa_Prime", Rango = "Diamante", Elo = 3302 },
		{ Nombre = "KaiserVoid", Rango = "Maestro", Elo = 3290 },
		{ Nombre = "Lumen_7", Rango = "Maestro", Elo = 3185 },
		{ Nombre = "Shard_Rex", Rango = "Platino", Elo = 2620 },
		{ Nombre = "OrbitaZ", Rango = "Platino", Elo = 2588 },
		{ Nombre = "Nyx_Hollow", Rango = "Platino", Elo = 2410 },
		{ Nombre = "Draco_Arc", Rango = "Oro", Elo = 1980 },
		{ Nombre = "Tempest_9", Rango = "Oro", Elo = 1902 },
		{ Nombre = "Ilia_Moon", Rango = "Oro", Elo = 1844 },
		{ Nombre = "RayoNeon", Rango = "Oro", Elo = 1790 },
	},
}

-- ===== Índice: planetas (los de bando y los pequeños de la v1, que aún no están en Planetas/Datos) =====
export type Drop = { Nombre: string, Porcentaje: number }
export type EntradaIndice = {
	N: string,
	A: string,
	Tipo: string,
	Peligro: number,
	Rareza: string,
	Habitat: string,
	Drops: { Drop },
	Lore: string,
	Veces: number,
}
DatosDemo.IndicePlanetas = {
	Total = 300,
	Lista = {
		{
			N = "Nueva Tierra",
			A = "planeta_nueva_tierra",
			Tipo = "Planeta de bando",
			Peligro = 0,
			Rareza = "Legendario",
			Habitat = "Base de los Humanos",
			Drops = { { Nombre = "Tiendas", Porcentaje = 100 } },
			Lore = "Luminoso, con un sol normal, ciudades y tiendas. El hogar de los Humanos.",
			Veces = 1,
		},
		{
			N = "Umbra",
			A = "planeta_umbra",
			Tipo = "Planeta de bando",
			Peligro = 5,
			Rareza = "Mitico",
			Habitat = "Base de los Monstruos",
			Drops = { { Nombre = "Cristal abisal", Porcentaje = 8 } },
			Lore = "Su sol es un agujero negro. Allí está lo único que los humanos no pueden fabricar.",
			Veces = 1,
		},
		{
			N = "Verdalia",
			A = "planeta_verdalia",
			Tipo = "Habitable",
			Peligro = 1,
			Rareza = "PocoComun",
			Habitat = "Sector 7-B",
			Drops = { { Nombre = "Hierro", Porcentaje = 40 }, { Nombre = "Flor estelar", Porcentaje = 20 } },
			Lore = "Praderas templadas y lagos. El primer viaje de casi todos los exploradores.",
			Veces = 1,
		},
		{
			N = "Ígnea",
			A = "planeta_ignea",
			Tipo = "Volcánico · disputado",
			Peligro = 4,
			Rareza = "Epico",
			Habitat = "Sector 9-A",
			Drops = { { Nombre = "Titanio", Porcentaje = 35 }, { Nombre = "Cristal de energía", Porcentaje = 15 } },
			Lore = "Ríos de lava y PvP sin zonas seguras. Los mejores minerales están en el centro.",
			Veces = 1,
		},
		{
			N = "Nerea",
			A = "planeta_nerea",
			Tipo = "Acuático",
			Peligro = 2,
			Rareza = "Raro",
			Habitat = "Sector 4-C",
			Drops = { { Nombre = "Cobre", Porcentaje = 30 }, { Nombre = "Gel luminiscente", Porcentaje = 20 } },
			Lore = "Un océano sin costas. Las islas flotantes se mueven con las mareas.",
			Veces = 1,
		},
		{
			N = "Grisalla",
			A = "planeta_grisalla",
			Tipo = "Estéril",
			Peligro = 1,
			Rareza = "Comun",
			Habitat = "Sector 2-D",
			Drops = { { Nombre = "Hierro", Porcentaje = 60 } },
			Lore = "Polvo, cráteres y silencio. Buen sitio para picar sin que te molesten.",
			Veces = 1,
		},
	} :: { EntradaIndice },
}
-- Total de cada categoría del Índice cuando el juego tenga más especies que las que hay en Especies.
-- (Mientras tanto se usa el número real de especies de cada categoría.)

-- ===== Mapa galáctico (coordenadas del mapa: 1600 × 1000) =====
export type PlanetaMapa = {
	Id: string,
	N: string,
	X: number,
	Y: number,
	R: number,
	Tipo: string, -- "Bando" | "Habitable" | "Esteril" | "Volcanico" | "Acuatico"
	A: string,
	Bando: string?,
	Recursos: string,
	Por: string,
	Disputado: boolean?,
}
DatosDemo.Mapa = {
	Yo = { X = 640, Y = 560, Sector = "Sector 7-B" },
	Planetas = {
		{
			Id = "nueva_tierra",
			N = "Nueva Tierra",
			X = 300,
			Y = 500,
			R = 34,
			Tipo = "Bando",
			A = "planeta_nueva_tierra",
			Bando = "Humanos",
			Recursos = "Tiendas · materiales",
			Por = "—",
		},
		{
			Id = "umbra",
			N = "Umbra",
			X = 1300,
			Y = 470,
			R = 34,
			Tipo = "Bando",
			A = "planeta_umbra",
			Bando = "Monstruos",
			Recursos = "Cristal abisal",
			Por = "—",
		},
		{
			Id = "verdalia",
			N = "Verdalia",
			X = 600,
			Y = 600,
			R = 13,
			Tipo = "Habitable",
			A = "planeta_verdalia",
			Recursos = "Hierro · flores",
			Por = "Rodrixx_777",
		},
		{
			Id = "ignea",
			N = "Ígnea",
			X = 820,
			Y = 360,
			R = 15,
			Tipo = "Volcanico",
			A = "planeta_ignea",
			Recursos = "Titanio · cristal",
			Por = "xDarkStar",
			Disputado = true,
		},
		{
			Id = "nerea",
			N = "Nerea",
			X = 520,
			Y = 300,
			R = 14,
			Tipo = "Acuatico",
			A = "planeta_nerea",
			Recursos = "Cobre · gel",
			Por = "Lyra_Vex",
		},
		{
			Id = "grisalla",
			N = "Grisalla",
			X = 980,
			Y = 700,
			R = 11,
			Tipo = "Esteril",
			A = "planeta_grisalla",
			Recursos = "Hierro",
			Por = "NovaKiller",
		},
	} :: { PlanetaMapa },
	Rutas = {
		{ "nueva_tierra", "verdalia" },
		{ "verdalia", "nerea" },
		{ "verdalia", "ignea" },
		{ "ignea", "umbra" },
		{ "verdalia", "grisalla" },
		{ "grisalla", "umbra" },
		{ "nueva_tierra", "nerea" },
	},
	NoDescubiertos = 294, -- puntos tenues (300 planetas en total)
	Semilla = 3,
	SegundosPorUnidad = 0.45, -- tiempo de viaje: distancia en el mapa × esto
	KmPorUnidad = 10,
}

-- ===== Tienda =====
-- Moneda: "Monedas" (se ganan jugando), "Gemas" (premium) o "Robux" (pases de juego).
-- Sin pay-to-win: con gemas y Robux solo hay cosméticos y pases de comodidad.
export type Producto = {
	Id: string,
	N: string,
	Sub: string,
	A: string,
	Cat: { string },
	Precio: number,
	Antes: number?,
	Moneda: string,
	Rareza: string,
	Nuevo: boolean?,
	Oferta: boolean?,
	Heroe: boolean?,
	Desc: string?,
	Fin: string?,
}
DatosDemo.Tienda = {
	Categorias = { "Destacado", "Armas", "Armadura", "Cosméticos", "Packs" },
	Productos = {
		{
			Id = "SkinNebula",
			N = "Skin Nebula",
			Sub = "Pintura de nave",
			A = "skin_nebula",
			Cat = { "Destacado", "Cosméticos" },
			Precio = 15,
			Moneda = "Gemas",
			Rareza = "Epico",
			Nuevo = true,
			Heroe = true,
			Desc = "Pinta tu nave con una nebulosa que cambia de color según la velocidad. Solo estética: no cambia las estadísticas.",
			Fin = "TERMINA EN 2 D 14 H",
		},
		{
			Id = "EspadaPlasma",
			N = "Espada de Plasma",
			Sub = "Espada · nivel 45",
			A = "item_espada_plasma",
			Cat = { "Destacado", "Armas" },
			Precio = 5000,
			Antes = 6500,
			Moneda = "Monedas",
			Rareza = "Raro",
			Oferta = true,
		},
		{
			Id = "CascoNova",
			N = "Casco Nova",
			Sub = "Casco · nivel 60",
			A = "item_casco_nova",
			Cat = { "Destacado", "Armadura" },
			Precio = 3200,
			Moneda = "Monedas",
			Rareza = "Legendario",
		},
		{
			Id = "PaseX2",
			N = "x2 Monedas",
			Sub = "Pase de juego",
			A = "pase_x2",
			Cat = { "Destacado", "Packs" },
			Precio = 199,
			Moneda = "Robux",
			Rareza = "Legendario",
		},
		{
			Id = "PistolaFoton",
			N = "Pistola Fotón",
			Sub = "Arma · nivel 52",
			A = "item_pistola_foton",
			Cat = { "Armas" },
			Precio = 4200,
			Moneda = "Monedas",
			Rareza = "Epico",
		},
		{
			Id = "PetoReactor",
			N = "Peto Reactor",
			Sub = "Armadura · nivel 48",
			A = "item_peto_reactor",
			Cat = { "Armadura" },
			Precio = 3800,
			Moneda = "Monedas",
			Rareza = "Epico",
		},
		{
			Id = "Botas",
			N = "Botas gravitatorias",
			Sub = "Botas · nivel 30",
			A = "item_botas_gravitatorias",
			Cat = { "Armadura" },
			Precio = 1900,
			Moneda = "Monedas",
			Rareza = "PocoComun",
		},
		{
			Id = "Cinturon",
			N = "Cinturón táctico",
			Sub = "Cinturón · nivel 10",
			A = "item_cinturon_tactico",
			Cat = { "Armadura" },
			Precio = 900,
			Moneda = "Monedas",
			Rareza = "Comun",
		},
		{
			Id = "EstelaAurora",
			N = "Estela Aurora",
			Sub = "Estela de nave",
			A = "estela_aurora",
			Cat = { "Cosméticos" },
			Precio = 10,
			Moneda = "Gemas",
			Rareza = "Raro",
		},
		{
			Id = "AuraCosmica",
			N = "Aura Cósmica",
			Sub = "Skin de poderes",
			A = "aura_cosmica",
			Cat = { "Cosméticos" },
			Precio = 22,
			Moneda = "Gemas",
			Rareza = "Legendario",
			Nuevo = true,
		},
		{
			Id = "PackExplorador",
			N = "Pack Explorador",
			Sub = "3 cosméticos",
			A = "pack_explorador",
			Cat = { "Packs" },
			Precio = 30,
			Moneda = "Gemas",
			Rareza = "Epico",
		},
		{
			Id = "PaseAlmacen",
			N = "Almacén extra",
			Sub = "Pase · +40 de bodega",
			A = "pase_almacen",
			Cat = { "Packs" },
			Precio = 149,
			Moneda = "Robux",
			Rareza = "Raro",
		},
		{
			Id = "PaseVIP",
			N = "VIP",
			Sub = "Pase · sala y chat VIP",
			A = "pase_vip",
			Cat = { "Packs" },
			Precio = 399,
			Moneda = "Robux",
			Rareza = "Legendario",
		},
	} :: { Producto },
}

return DatosDemo
