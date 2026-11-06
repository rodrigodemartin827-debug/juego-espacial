--!strict
--[[
	Config (Elección de bando): todo lo ajustable de la pantalla de la primera entrada, donde el jugador elige entre
	Humanos y Monstruos con la grieta en medio.

	Solo hay datos: números, textos, colores en hexadecimal "#RRGGBB" y vectores como listas { x, y, z }. Así se
	pueden cargar en las pruebas (fuera de Roblox) y retocar sin tocar el código.

	ESCENA. Todo se coloca en el sistema de la CÁMARA: la cámara está en { 0, 0, 0 } y mira hacia -Z; +X es la
	derecha de la pantalla y +Y arriba. La escena entera se monta lejos del mapa, en `Escena.Origen`, y solo existe
	en el cliente del jugador que elige (nadie más la ve).

	Los textos que lee el jugador están aparte, en Eleccion/Datos/Textos; los efectos, en Eleccion/Datos/EfectosEleccion.
]]

local Config = {}

-- ===== Reglas =====

-- Orden de los bandos en pantalla, de izquierda a derecha. Deben ser exactamente los de Bandos.Elegibles.
Config.Orden = { "Humanos", "Monstruos" }

-- Atributo (en el Player) que pone el servidor mientras el jugador está en la pantalla de elección. Mientras lo
-- tiene, su personaje está quieto (anclado) y protegido (ForceField invisible), y no puede usar habilidades.
Config.AtributoEligiendo = "EligiendoBando"

-- MODO DE PRUEBAS: en Studio (RunService:IsStudio()), la pantalla de elección sale CADA VEZ que se entra, aunque ya
-- se tenga bando (al cargar los datos, el bando vuelve a «Ninguno», como con el comando /reiniciarbando). En el juego
-- publicado no hace nada: allí sale solo la primera vez. Ponlo a false para probar en Studio con el bando guardado.
Config.ElegirBandoSiempreEnStudio = true

-- Atributo (en el Player, solo en su cliente) que pone la escena mientras está montada: desde que aparece hasta que
-- termina el fundido final, también después de que el servidor confirme. Mientras está, la cámara y la luz son de la
-- escena (la cámara del planeta redondo y el ambiente de los planetas se apartan).
Config.AtributoEnPantalla = "PantallaEleccion"

-- Nombre del ForceField invisible que protege al personaje mientras elige.
Config.NombreProteccion = "ProteccionEleccion"

-- Comando de chat, SOLO EN STUDIO, que devuelve el bando del jugador a "Ninguno" para volver a ver la pantalla
-- (ver Servicios/ServicioBandos). En el juego publicado no existe.
Config.ComandoReiniciarBando = "/reiniciarbando"

-- ===== Tiempos (segundos) =====

Config.Tiempos = {
	-- Fundido de entrada: de negro a la escena (o al juego, si el jugador ya tiene bando).
	FundidoEntrada = 1.2,
	-- Si los datos no llegan en este tiempo, se quita la cortina negra igualmente (el servidor ya habrá
	-- expulsado al jugador si no se pudieron cargar): nunca debe quedarse la pantalla en negro.
	EsperaMaximaDatos = 25,
	-- Tiempo máximo esperando a que el servidor confirme la elección. Pasado, se puede volver a elegir.
	EsperaConfirmacion = 8,
	-- Anticipación al hacer clic: el lado elegido "toma aire" antes de la confirmación.
	Anticipacion = 0.14,
	-- Desde la confirmación hasta que empieza el fundido a negro (lo que dura el espectáculo).
	Celebracion = 2.4,
	-- Fundido a negro, negro mantenido (se desmonta la escena) y fundido de vuelta al juego.
	FundidoSalida = 0.7,
	NegroMantenido = 0.35,
	FundidoVuelta = 1.1,
	-- Transición del resaltado al pasar el ratón por un lado.
	Resaltado = 0.35,
	-- Congelación (hitstop) de la escena en el instante de la confirmación.
	Congelacion = 0.09,
}

-- ===== Cámara =====

Config.Camara = {
	-- La escena entera (incluida la cámara) se monta aquí, lejos del mapa. Solo la ve este cliente.
	Origen = { 0, 2600, 26000 },
	-- Encuadre: lo que debe caber SIEMPRE a lo ancho, a la distancia de referencia. El campo de visión vertical
	-- se calcula con la proporción de la pantalla (ver Eleccion/Encuadre), así en móvil y en un monitor 4:3 se
	-- ven los dos planetas enteros.
	MitadAnchoVisible = 58, -- studs a cada lado del centro...
	DistanciaReferencia = 78, -- ...a esta distancia de la cámara (el plano de los planetas)
	CampoMinimo = 38, -- grados (pantallas muy anchas)
	CampoMaximo = 78, -- grados (pantallas casi cuadradas o en vertical)
	-- Respiración: un vaivén lentísimo para que la imagen no parezca congelada. No la mueve el jugador.
	Vaiven = { Amplitud = 0.35, Periodo = 9 }, -- studs y segundos
	-- Al resaltar un lado, la cámara gira un poco hacia él.
	GiroResaltado = 2.2, -- grados
	Suavidad = 5, -- cuanto mayor, antes llega al giro deseado
}

-- ===== Escena =====

-- Cómo reacciona la escena al resaltar un lado.
Config.Escena = {
	-- Multiplicador de tamaño de los planetas al resaltarlos, y del lado contrario (se encoge un poco).
	EscalaResaltado = 1.07,
	EscalaApagado = 0.97,
	-- Brillo de las luces del lado no resaltado (fracción del normal).
	LuzApagada = 0.35,
	-- Al confirmar: golpe de escala del planeta elegido (y en lo que se asienta) y del lado que se apaga.
	EscalaGolpe = 1.22,
	EscalaElegido = 1.1,
	EscalaDescartado = 0.9,
	-- Fracción del camino hacia el planeta elegido que avanza la cámara durante la celebración.
	AcercamientoCamara = 0.22,
	-- Segundos mínimos entre dos rayos de "resaltar" (pasar el ratón de un lado a otro muy deprisa).
	EsperaRayoResaltar = 0.45,
	-- Polvo estelar delante del fondo (partículas por segundo en calidad alta).
	Polvo = { Tasa = 14, Color = "#BFD4FF" },
}

export type Mancha = {
	Direccion: { number }, -- hacia dónde está, desde el centro del planeta
	Tamano: number, -- radio de la mancha en fracción del radio del planeta
	Elevacion: number, -- cuánto sobresale (fracción del radio)
	Color: string,
	Material: string?, -- "Plastico" (por defecto), "Neon", "Roca", "Hielo", "Arena", "Cesped"
	Transparencia: number?,
}

export type Planeta = {
	Posicion: { number },
	Radio: number,
	Color: string, -- océano / superficie base
	Material: string?,
	Eje: { number }, -- eje de giro
	VueltaSegundos: number, -- lo que tarda en dar una vuelta entera
	Manchas: { Mancha }, -- continentes, polos, grietas de lava...
	Nubes: { Mancha }, -- giran un poco más deprisa que el suelo
	NubesVuelta: number,
	Atmosfera: { Color: string, Escala: number, Transparencia: number },
	Halo: { Color: string, Escala: number, Transparencia: number }, -- resplandor exterior (Neon muy transparente)
}

-- ----- Planeta de los Humanos: como la Tierra -----
-- Océano azul profundo: PROBADO EN STUDIO, con la luz nocturna de la escena el azul de antes (#1D63C9) se leía celeste.
local AZUL, VERDE, VERDE_OSCURO, TIERRA, HIELO = "#0B2F6E", "#3E9B45", "#2C7034", "#A88B57", "#F2F7FF"

Config.PlanetaHumanos = {
	Posicion = { -33, 3, -78 },
	Radio = 17,
	Color = AZUL,
	Material = "Plastico",
	Eje = { 0.18, 1, 0.08 },
	VueltaSegundos = 90,
	Manchas = {
		-- Continentes: varias esferas que asoman del océano y se solapan, con contornos irregulares.
		{ Direccion = { 0.55, 0.35, 0.75 }, Tamano = 0.46, Elevacion = 0.018, Color = VERDE },
		{ Direccion = { 0.75, 0.05, 0.62 }, Tamano = 0.36, Elevacion = 0.016, Color = VERDE_OSCURO },
		{ Direccion = { 0.35, -0.3, 0.88 }, Tamano = 0.32, Elevacion = 0.017, Color = VERDE },
		{ Direccion = { 0.62, 0.15, 0.78 }, Tamano = 0.2, Elevacion = 0.026, Color = TIERRA, Material = "Arena" },
		{ Direccion = { -0.65, 0.4, 0.62 }, Tamano = 0.42, Elevacion = 0.018, Color = VERDE },
		{ Direccion = { -0.82, 0.1, 0.5 }, Tamano = 0.3, Elevacion = 0.016, Color = VERDE_OSCURO },
		{ Direccion = { -0.55, -0.45, 0.68 }, Tamano = 0.28, Elevacion = 0.017, Color = TIERRA, Material = "Arena" },
		{ Direccion = { -0.1, 0.25, -0.95 }, Tamano = 0.5, Elevacion = 0.018, Color = VERDE },
		{ Direccion = { 0.3, -0.2, -0.92 }, Tamano = 0.34, Elevacion = 0.017, Color = VERDE_OSCURO },
		{ Direccion = { -0.9, -0.2, -0.35 }, Tamano = 0.3, Elevacion = 0.017, Color = VERDE },
		-- Casquetes polares.
		{ Direccion = { 0, 1, 0 }, Tamano = 0.42, Elevacion = 0.02, Color = HIELO, Material = "Hielo" },
		{ Direccion = { 0.05, -1, 0.1 }, Tamano = 0.36, Elevacion = 0.02, Color = HIELO, Material = "Hielo" },
	},
	Nubes = {
		{ Direccion = { 0.3, 0.55, 0.78 }, Tamano = 0.3, Elevacion = 0.05, Color = "#FFFFFF", Transparencia = 0.25 },
		{ Direccion = { -0.4, 0.2, 0.9 }, Tamano = 0.26, Elevacion = 0.05, Color = "#FFFFFF", Transparencia = 0.3 },
		{ Direccion = { 0.8, -0.35, 0.5 }, Tamano = 0.24, Elevacion = 0.05, Color = "#FFFFFF", Transparencia = 0.3 },
		{ Direccion = { -0.2, -0.6, 0.78 }, Tamano = 0.22, Elevacion = 0.05, Color = "#FFFFFF", Transparencia = 0.35 },
		{ Direccion = { -0.85, 0.45, -0.25 }, Tamano = 0.3, Elevacion = 0.05, Color = "#FFFFFF", Transparencia = 0.25 },
		{ Direccion = { 0.5, 0.3, -0.8 }, Tamano = 0.28, Elevacion = 0.05, Color = "#FFFFFF", Transparencia = 0.3 },
		{ Direccion = { 0.1, 0.85, 0.5 }, Tamano = 0.2, Elevacion = 0.05, Color = "#FFFFFF", Transparencia = 0.35 },
	},
	NubesVuelta = 70,
	-- Sin atmósfera (Transparencia 1): PROBADO EN STUDIO, la esfera de ForceField lavaba el planeta entero de celeste
	-- (el ForceField casi no hace caso a la transparencia). El halo, muy tenue, basta para el borde.
	Atmosfera = { Color = "#7FC8FF", Escala = 1.09, Transparencia = 1 },
	Halo = { Color = "#5FB2FF", Escala = 1.22, Transparencia = 0.97 },
} :: Planeta

-- ----- Planeta de los Monstruos: oscuro, con venas de lava y niebla púrpura -----
local ROCA, ROCA_CLARA, LAVA, LAVA_VIVA = "#1A1420", "#2B2230", "#FF2A3C", "#FF7A2A"

Config.PlanetaMonstruos = {
	Posicion = { 33, -1, -78 },
	Radio = 17,
	Color = "#120E16",
	Material = "Roca",
	Eje = { -0.25, 1, 0.1 },
	VueltaSegundos = 120,
	Manchas = {
		-- Relieve de roca más clara.
		{ Direccion = { -0.5, 0.4, 0.77 }, Tamano = 0.4, Elevacion = 0.02, Color = ROCA_CLARA, Material = "Roca" },
		{ Direccion = { 0.6, -0.3, 0.74 }, Tamano = 0.36, Elevacion = 0.02, Color = ROCA, Material = "Roca" },
		{ Direccion = { 0.1, 0.7, -0.7 }, Tamano = 0.44, Elevacion = 0.02, Color = ROCA_CLARA, Material = "Roca" },
		{ Direccion = { -0.7, -0.5, -0.5 }, Tamano = 0.38, Elevacion = 0.02, Color = ROCA, Material = "Roca" },
		-- Venas de lava: manchas pequeñas de Neon, solo un poco por encima de la roca (brillan entre el relieve).
		{ Direccion = { -0.15, 0.1, 0.98 }, Tamano = 0.12, Elevacion = 0.006, Color = LAVA, Material = "Neon" },
		{ Direccion = { 0.05, -0.12, 0.99 }, Tamano = 0.1, Elevacion = 0.006, Color = LAVA_VIVA, Material = "Neon" },
		{ Direccion = { 0.25, 0.3, 0.92 }, Tamano = 0.09, Elevacion = 0.006, Color = LAVA, Material = "Neon" },
		{ Direccion = { -0.4, -0.25, 0.88 }, Tamano = 0.08, Elevacion = 0.006, Color = LAVA, Material = "Neon" },
		{ Direccion = { 0.45, 0.05, 0.89 }, Tamano = 0.07, Elevacion = 0.006, Color = LAVA_VIVA, Material = "Neon" },
		{ Direccion = { -0.8, 0.2, 0.55 }, Tamano = 0.1, Elevacion = 0.006, Color = LAVA, Material = "Neon" },
		{ Direccion = { 0.75, 0.4, 0.5 }, Tamano = 0.09, Elevacion = 0.006, Color = LAVA, Material = "Neon" },
		{ Direccion = { 0.3, -0.6, 0.74 }, Tamano = 0.08, Elevacion = 0.006, Color = LAVA_VIVA, Material = "Neon" },
		{ Direccion = { -0.2, 0.75, 0.62 }, Tamano = 0.07, Elevacion = 0.006, Color = LAVA, Material = "Neon" },
		{ Direccion = { 0.2, 0.2, -0.95 }, Tamano = 0.11, Elevacion = 0.006, Color = LAVA, Material = "Neon" },
		{ Direccion = { -0.6, -0.1, -0.78 }, Tamano = 0.09, Elevacion = 0.006, Color = LAVA_VIVA, Material = "Neon" },
	},
	Nubes = {
		-- Bancos de niebla púrpura, más transparentes que las nubes humanas.
		{ Direccion = { 0.4, 0.5, 0.76 }, Tamano = 0.34, Elevacion = 0.045, Color = "#3A1450", Transparencia = 0.45 },
		{ Direccion = { -0.6, -0.35, 0.72 }, Tamano = 0.3, Elevacion = 0.045, Color = "#2A0E3A", Transparencia = 0.5 },
		{ Direccion = { -0.3, 0.6, -0.74 }, Tamano = 0.32, Elevacion = 0.045, Color = "#3A1450", Transparencia = 0.45 },
		{ Direccion = { 0.7, -0.4, -0.6 }, Tamano = 0.28, Elevacion = 0.045, Color = "#2A0E3A", Transparencia = 0.5 },
	},
	NubesVuelta = 95,
	Atmosfera = { Color = "#B0204A", Escala = 1.08, Transparencia = 0.15 },
	Halo = { Color = "#7A1FA0", Escala = 1.24, Transparencia = 0.92 },
} :: Planeta

-- ----- El sol de los Humanos (detrás de su planeta, arriba a la izquierda) -----
Config.Sol = {
	Posicion = { -78, 34, -150 },
	Radio = 7,
	Color = "#FFF4D6",
	Corona = { Color = "#FFC86B", Escala = 1.6, Transparencia = 0.75 },
	Resplandor = { Color = "#FFB347", Escala = 2.6, Transparencia = 0.92 },
	-- Luz que ilumina el planeta humano (una PointLight no llega más de 60 studs, por eso va cerca del planeta).
	Luz = { Posicion = { -58, 26, -60 }, Color = "#FFF1D8", Brillo = 1.3, Rango = 60 }, -- más, y el océano se quema
}

-- ----- El "sol" de los Monstruos: un agujero negro con disco de acreción -----
Config.AgujeroNegro = {
	Posicion = { 80, 30, -155 },
	Radio = 7.5,
	Inclinacion = { 16, 0, -14 }, -- grados: X = cuánto se ve el disco desde arriba, Z = ladeo
	Disco = { Radio = 19, Color = "#FF6A2A", Transparencia = 0.25 },
	DiscoExterior = { Radio = 25, Color = "#B0204A", Transparencia = 0.6 },
	Anillo = { Color = "#FFB36B", Escala = 1.12, Transparencia = 0.2 }, -- anillo de fotones (ForceField)
	Rafagas = { Cantidad = 14, Color = "#FFD2A6", Vuelta = 6 }, -- trozos de materia que giran en el disco
	-- Luz rojiza que recorta el planeta de los monstruos por detrás.
	Luz = { Posicion = { 58, 18, -98 }, Color = "#FF3A55", Brillo = 3.2, Rango = 55 },
}

-- ----- La grieta (en medio) -----
Config.Grieta = {
	Posicion = { 0, 0, -70 },
	Alto = 66, -- de punta a punta
	Puntos = 22, -- vértices del zigzag (en calidad baja se usan la mitad)
	Desvio = 4.2, -- cuánto se aparta el zigzag del centro (en el medio; en las puntas, nada)
	Temblor = 0.7, -- cuánto ondula con el tiempo
	VelocidadTemblor = 1.6,
	Semilla = 7, -- forma del zigzag (cambiarla da otra grieta)
	-- Capas del trazo (cintas de luz que siempre miran a la cámara), de atrás adelante. Grosor en studs en el centro
	-- de la grieta (en las puntas, la mitad); Brillo > 1 hace que resplandezca; Pulso = cuánto late el grosor; Emite =
	-- false para el vacío (negro, no suma luz). Lado = -1 / 1: es un borde, desplazado a ese lado del vacío.
	-- Minimo: nivel de calidad (VFX/Calidad) a partir del cual se dibuja.
	Capas = {
		{ Grosor = 7, Color = "#6A1FFF", Transparencia = 0.72, Brillo = 1.6, Pulso = 0.25 }, -- halo
		{ Grosor = 3.2, Color = "#C04BFF", Transparencia = 0.45, Brillo = 2.2, Pulso = 0.2, Minimo = "Medio" },
		{ Grosor = 1.7, Color = "#020005", Transparencia = 0.02, Brillo = 0, Pulso = 0.12, Emite = false }, -- vacío
		{ Grosor = 0.35, Color = "#F2D6FF", Transparencia = 0, Brillo = 4, Pulso = 0.1, Lado = -1 }, -- bordes
		{ Grosor = 0.35, Color = "#F2D6FF", Transparencia = 0, Brillo = 4, Pulso = 0.1, Lado = 1 },
	},
	-- Grietas secundarias que salen de la principal (halo y núcleo). No se dibujan en calidad baja.
	Ramas = {
		Cantidad = 6,
		Largo = { 5, 11 },
		Puntos = 4,
		Halo = { Grosor = 2.2, Color = "#8A2BFF", Transparencia = 0.6, Brillo = 1.8 },
		Nucleo = { Grosor = 0.4, Color = "#F2D6FF", Transparencia = 0, Brillo = 3.5 },
	},
	PeriodoLatido = 1.7, -- segundos entre latidos
	-- Luz violeta del centro.
	Luz = { Color = "#B04BFF", Brillo = 2.5, Rango = 45 },
	-- Partículas que salen de la grieta (por segundo, en calidad alta; se reducen con VFX/Calidad).
	Motas = { Tasa = 40, Color = { "#FFFFFF", "#C04BFF", "#5A1FB0" } },
	Vacio = { Tasa = 10, Color = "#05010A" }, -- jirones oscuros: el vacío que se escapa
	-- Cada cuánto salta un chispazo de energía (receta Eleccion_Grieta_Chispazo).
	IntervaloChispazo = { 0.9, 2.1 },
}

-- ----- Las figuras de cada bando (R6, en primer plano, abajo) -----
export type Figura = {
	Posicion: { number },
	Escala: number, -- 1 = tamaño de un personaje R6 (5 studs)
	GiroY: number, -- grados (hacia dónde mira)
	Colores: { [string]: string }, -- por pieza R6: Head, Torso, "Left Arm", "Right Arm", "Left Leg", "Right Leg"
	Material: string,
	Estiramiento: { [string]: { number } }?, -- multiplicadores de tamaño por pieza (los monstruos, más largos)
	Ojos: { Color: string, Tamano: number }?, -- dos ojos de Neon
	Visor: { Color: string }?, -- visor de casco (los humanos)
	Inclinacion: number?, -- grados de inclinación de la cabeza
	Luz: { Desplazamiento: { number }, Color: string, Brillo: number, Rango: number },
	Espasmos: { Intervalo: { number }, Fuerza: number }?, -- tirones bruscos de la cabeza (los monstruos)
	-- Modelo de verdad en lugar de la figura de piezas: nombre de una plantilla en ReplicatedStorage.Modelos (un
	-- personaje R6 montado). Si no está en el lugar, se usa la figura de piezas.
	Modelo: {
		Nombre: string,
		Alto: number, -- studs que mide en la escena (se escala la plantilla)
		Suelo: number, -- altura del suelo de la figura respecto a Posicion
		GiroCabeza: number, -- grados que ladea la cabeza (quieto)
		Encorvar: number, -- grados que inclina el torso hacia delante
		LuzAbajo: { Desplazamiento: { number }, Color: string, Brillo: number, Rango: number },
		LuzOjos: { Color: string, Brillo: number, Rango: number, Pulso: number },
	}?,
}

Config.FiguraHumanos = {
	-- De pie con los pies sobre la franja de abajo, junto a su panel (PROBADO EN STUDIO: más abajo, en pantallas
	-- anchas como la de Studio o un móvil apaisado, el encuadre las dejaba fuera).
	Posicion = { -30, -6, -44 },
	Escala = 2.2,
	GiroY = -18,
	-- Luz de relleno que ilumina la figura (posición relativa a la figura).
	Luz = { Desplazamiento = { 7, 6, 10 }, Color = "#DDEBFF", Brillo = 1.3, Rango = 24 },
	Colores = {
		Head = "#E8EDF5",
		Torso = "#DDE4EE",
		["Left Arm"] = "#C9D2DE",
		["Right Arm"] = "#C9D2DE",
		["Left Leg"] = "#3B4A63",
		["Right Leg"] = "#3B4A63",
	},
	Material = "Plastico",
	Visor = { Color = "#4DF0FF" },
} :: Figura

Config.FiguraMonstruos = {
	Posicion = { 27.5, -5.5, -44 },
	Escala = 2.3,
	GiroY = 18,
	-- Contraluz rojo detrás: la figura se ve como una silueta negra recortada.
	Luz = { Desplazamiento = { -2, 5, -7 }, Color = "#FF2238", Brillo = 4, Rango = 18 },
	Colores = {
		Head = "#0B090D",
		Torso = "#0E0B11",
		["Left Arm"] = "#0B090D",
		["Right Arm"] = "#0B090D",
		["Left Leg"] = "#0E0B11",
		["Right Leg"] = "#0E0B11",
	},
	Material = "Roca",
	-- Brazos larguísimos y cuerpo flaco: la silueta es lo que asusta.
	Estiramiento = {
		Torso = { 0.8, 1.1, 0.8 },
		["Left Arm"] = { 0.7, 1.75, 0.7 },
		["Right Arm"] = { 0.7, 1.75, 0.7 },
		["Left Leg"] = { 0.75, 1.2, 0.75 },
		["Right Leg"] = { 0.75, 1.2, 0.75 },
		Head = { 0.9, 1.15, 0.9 },
	},
	Ojos = { Color = "#FF1E2E", Tamano = 0.16 },
	Inclinacion = 14,
	Espasmos = { Intervalo = { 1.4, 3.6 }, Fuerza = 22 },
	-- «El Hueco» (modelos/monstruo, #14), quieto en reposo: luz roja desde abajo y los ojos brillando.
	Modelo = {
		Nombre = "Monstruo_R6",
		Alto = 15,
		Suelo = -5.5,
		GiroCabeza = 12,
		Encorvar = 10,
		-- Delante y por debajo de la figura (-Z es hacia la cámara): la luz le sube por la cara.
		LuzAbajo = { Desplazamiento = { 0, -4.5, -5 }, Color = "#FF2A3A", Brillo = 14, Rango = 18 },
		LuzOjos = { Color = "#FF2B2B", Brillo = 3, Rango = 6, Pulso = 1.7 },
	},
} :: Figura

-- ===== Interfaz y entrada =====

Config.Interfaz = {
	-- En pantallas táctiles no hay "pasar el ratón": la información de los dos bandos se ve siempre, y tocar un
	-- lado lo resalta mientras se mantiene el dedo; al soltarlo sobre el mismo lado, se elige.
	InfoSiempreEnTactil = true,
	-- Colores de la interfaz (los de cada bando están en Datos/Textos).
	Fondo = "#070812",
	Texto = "#EEF2FF",
	TextoSuave = "#9AA3C7",
	-- Prioridad con la que se bloquean el teclado y el mando mientras se elige (por encima de todo lo del juego).
	PrioridadBloqueo = 3000,
	-- ScreenGuis del jugador que NO se ocultan mientras se elige (las propias y las barras de cine de VFX).
	GuisPermitidas = { "EleccionBando", "EleccionCortina", "VFXCine" },
	-- Interfaces de Roblox que se ocultan mientras se elige (se devuelven como estaban).
	CoreGuiOcultas = { "Backpack", "Health", "EmotesMenu" },
	-- Barras de cine (Pantalla.Cine) mientras se elige.
	BarrasCine = true,
}

-- Ajustes de la iluminación del cliente mientras se ve la escena (se devuelven como estaban al terminar).
Config.Iluminacion = {
	ExposureCompensation = 0.1,
	Contraste = 0.18, -- ColorCorrection propia de la escena
	Saturacion = 0.22,
}

return Config
