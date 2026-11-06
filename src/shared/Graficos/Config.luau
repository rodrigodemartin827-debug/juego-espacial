--!strict
--[[
	Graficos (datos): los cuatro niveles de gráficos, qué cambia en cada uno y la pantalla para elegirlos.

	La primera vez que entra, el jugador elige nivel (viene marcado el recomendado para su dispositivo, ver
	Graficos/Niveles.Recomendado). Se guarda con sus datos (campo Graficos) y se puede cambiar cuando quiera con el
	botón de ajustes. Es el primer paso de la entrada: gráficos → bando → editor.

	Qué toca cada nivel (todo en el cliente, no se replica):
	  · Calidad: nivel de los efectos visuales (VFX/Calidad: partículas, escombros, luces de efecto, desenfoque).
	  · Sombras: Lighting.GlobalShadows.
	  · Postefectos: qué clases de efecto de Lighting quedan encendidas (resplandor, corrección de color, rayos de sol,
	    profundidad de campo). Los de los VFX (nombre que empieza por "VFX_") no se tocan: los lleva cada efecto.
	  · Distancia: multiplica las distancias de detalle de la región (LodRegion): más bajo, las casas y el
	    mobiliario pasan antes a la versión simple o desaparecen.
	  · Vegetacion: multiplica las distancias de árboles, matas y hierba.
	  · Densidad: fracción de matas y hierba que se dibujan (los árboles siempre).
]]

export type Nivel = {
	Nombre: string, -- lo que se lee en el botón
	Descripcion: string,
	Calidad: string, -- nivel de VFX/Calidad: "Bajo" | "Medio" | "Alto"
	Sombras: boolean,
	Postefectos: { string }, -- clases de PostEffect encendidas
	Distancia: number,
	Vegetacion: number,
	Densidad: number,
}

local Config = {}

Config.Orden = { "Baja", "Media", "Alta", "Ultra" }

Config.Niveles = {
	Baja = {
		Nombre = "BAJA",
		Descripcion = "Para móviles sencillos: sin sombras ni efectos de luz, poca hierba y menos detalle a lo lejos.",
		Calidad = "Bajo",
		Sombras = false,
		Postefectos = {},
		Distancia = 0.6,
		Vegetacion = 0.6,
		Densidad = 0.25,
	},
	Media = {
		Nombre = "MEDIA",
		Descripcion = "Para la mayoría de móviles: sombras y resplandor, la mitad de la hierba.",
		Calidad = "Medio",
		Sombras = true,
		Postefectos = { "BloomEffect" },
		Distancia = 0.8,
		Vegetacion = 0.8,
		Densidad = 0.5,
	},
	Alta = {
		Nombre = "ALTA",
		Descripcion = "Todo como está pensado: sombras, todos los efectos de luz y toda la vegetación.",
		Calidad = "Alto",
		Sombras = true,
		Postefectos = { "BloomEffect", "ColorCorrectionEffect", "ColorGradingEffect", "SunRaysEffect" },
		Distancia = 1,
		Vegetacion = 1,
		Densidad = 1,
	},
	Ultra = {
		Nombre = "ULTRA",
		Descripcion = "Para ordenadores potentes: más detalle y más vegetación a lo lejos, y profundidad de campo.",
		Calidad = "Alto",
		Sombras = true,
		Postefectos = {
			"BloomEffect",
			"ColorCorrectionEffect",
			"ColorGradingEffect",
			"SunRaysEffect",
			"DepthOfFieldEffect",
		},
		Distancia = 1.4,
		Vegetacion = 1.5,
		Densidad = 1,
	},
} :: { [string]: Nivel }

-- Recomendación según el dispositivo (Graficos/Niveles.Recomendado). `CalidadRoblox` es el control de gráficos del
-- propio Roblox del jugador (1-10; 0 = automático).
Config.Recomendacion = {
	Movil = "Media",
	MovilSencillo = "Baja", -- móvil con el control de Roblox en CalidadRobloxSencilla o menos
	CalidadRobloxSencilla = 3,
	Ordenador = "Alta",
	OrdenadorPotente = "Ultra", -- ordenador con el control de Roblox en CalidadRobloxPotente o más
	CalidadRobloxPotente = 9,
}

-- MODO DE PRUEBAS: en Studio, la pantalla sale cada vez que se entra (en el juego publicado, solo la primera vez).
Config.MostrarSiempreEnStudio = true

-- Atributo (en el Player, solo en su cliente) mientras la pantalla tiene la cámara: la del personaje se aparta.
Config.AtributoCamara = "CamaraPantalla"

-- La pantalla.
Config.Pantalla = {
	Titulo = "GRÁFICOS",
	Subtitulo = "Elige cómo quieres que se vea. Puedes cambiarlo cuando quieras desde el botón de ajustes.",
	Recomendado = "RECOMENDADO",
	Continuar = "CONTINUAR",
	Cerrar = "LISTO",
	BotonAjustes = "Gráficos",
	-- La cámara se balancea despacio delante del personaje (± Arco grados respecto a su frente), para ver los
	-- cambios en el mundo de verdad. PROBADO EN STUDIO: dando la vuelta entera atravesaba su casa (aparece mirándola).
	Camara = { Distancia = 30, Altura = 11, Arco = 55, PeriodoSegundos = 24, Mira = 3 },
	Colores = {
		Fondo = "#0B0E16",
		Tarjeta = "#141A26",
		Borde = "#2C3A52",
		Elegida = "#4DC8FF",
		Recomendado = "#FFD27A",
		Texto = "#FFFFFF",
		TextoSuave = "#A9B6CC",
	},
	FundidoSegundos = 0.4,
}

return Config
