--!strict
--[[
	ConfigEditor: el editor de personaje humano (segundo paso de la entrada: bando → editor → gráficos → cinemática).
	Textos, tipografías, colores, escena 3D, cámara, giro y medidas de la interfaz. Lo que se puede elegir está en
	Personaje/DatosHumanos.
]]

local Config = {}

-- MODO DE PRUEBAS: en Studio el editor sale cada vez que se entra (en el juego publicado, solo la primera vez).
Config.MostrarSiempreEnStudio = true

Config.Textos = {
	Titulo = "TU PERSONAJE",
	Subtitulo = "Arrastra para girarlo · Los cambios se ven al momento",
	Piel = "PIEL",
	Aspecto = "ASPECTO",
	Color = "COLOR",
	Colorea = "COLOREA",
	Brillo = "BRILLO",
	Atras = "ATRÁS",
	Aleatorio = "ALEATORIO",
	Continuar = "CONTINUAR",
	UsarAvatar = "USAR MI AVATAR DE ROBLOX",
	UsarPiezas = "USAR LAS PIEZAS DEL JUEGO",
	CargandoAvatar = "CARGANDO TU AVATAR…",
	ErrorAvatar = "No se pudo cargar tu avatar de Roblox. Prueba otra vez.",
	AvatarActivo = "USANDO TU AVATAR",
}

-- Avatar de Roblox (solo Humanos). El máximo de accesorios es por rendimiento en móvil.
Config.Avatar = {
	MaxAccesorios = 6,
	Intentos = 3, -- veces que el servidor pide el avatar si falla (los servicios de Roblox a veces fallan)
	EsperaIntento = 1.5, -- segundos entre intentos
}

-- Tipografías (familias de Roblox): títulos anchos de estilo espacial y textos legibles.
Config.Fuentes = {
	Titulo = "rbxasset://fonts/families/Michroma.json",
	Texto = "rbxasset://fonts/families/Jura.json",
}

Config.Colores = {
	Fondo = "#070A10", -- detrás de los paneles (con transparencia)
	Panel = "#121926",
	PanelClaro = "#1C2536",
	Metal = "#2A3446",
	Borde = "#3A4A64",
	Cian = "#4DE8FF",
	CianOscuro = "#1B7F99",
	Texto = "#EAF6FF",
	TextoSuave = "#8FA3BD",
	Peligro = "#FF6B6B",
}

-- Escena 3D local (solo la ve el jugador): una sala redonda de metal con una plataforma y luces cian, lejos del
-- mapa para que nada se ponga delante.
Config.Escena = {
	Centro = { 0, 6000, 0 }, -- dónde se monta (studs)
	RadioSala = 26, -- más que la distancia de la cámara (~15): si no, la cámara queda pegada a la pared
	AltoSala = 20,
	Paneles = 30, -- paneles de la pared
	RadioPlataforma = 3.2,
	AltoPlataforma = 0.7,
	ColorPared = "#161C28",
	ColorSuelo = "#0D1118",
	ColorPlataforma = "#2A3242",
	ColorLuz = "#4DE8FF",
	LuzClave = { Brillo = 1.0, Color = "#FFF4E8" },
	LuzContra = { Brillo = 1.4, Color = "#4DE8FF" },
	LuzRelleno = { Brillo = 0.5, Color = "#9DB8FF" },
	LuzCara = { Brillo = 0.45, Color = "#FFF1E0" }, -- relleno suave desde delante: la cara siempre se lee
	Resplandor = 0.7, -- luz cian de la plataforma sobre el suelo
	Motas = 6, -- partículas por segundo (motas de luz flotando)
	-- Barrido de luz que recorre al personaje cada vez que cambia algo.
	Barrido = { Segundos = 0.5, Color = "#4DE8FF" },
}

-- Cámara: fija, de frente, encuadrando el cuerpo entero.
Config.Camara = {
	CampoVision = 36,
	AltoVisible = 9.6, -- studs de alto que caben en pantalla (el personaje mide ~5,5 con pelo; deja sitio a los botones)
	Mira = -0.45, -- altura del punto al que mira, respecto a la raíz
	-- Dónde queda el personaje en la pantalla (-1 izquierda, 0 centro, 1 derecha) según la disposición.
	PosicionX = { Ancha = 0.0, Estrecha = -0.32 },
}

-- Giro arrastrando el ratón o el dedo.
Config.Giro = {
	Inicial = -0.3, -- radianes: un poco de tres cuartos, que luce más que de frente
	Sensibilidad = 0.011, -- radianes por píxel
	Inercia = 6, -- cuánto tarda en pararse al soltar (más = antes)
}

-- Animación de reposo del personaje en el editor. En Studio se usa la KeyframeSequence de las animaciones de
-- movimiento (PR #17) si está; si no (y en el juego publicado, hasta que se suba la nuestra), la de R6 de Roblox.
Config.Reposo = {
	Carpeta = { "Animaciones", "Movimiento" }, -- dentro de ReplicatedStorage
	Nombre = "Reposo",
	Id = "rbxassetid://180435571",
}

-- Interfaz. Por debajo de estas medidas (píxeles) se usa la disposición estrecha (móvil): categorías abajo en
-- horizontal y paneles más pequeños.
Config.Interfaz = {
	AnchoMinimo = 980,
	AltoMinimo = 560,
	Margen = 20,
	AnchoIzquierda = 330,
	AnchoDerecha = 290,
	AltoFila = 50, -- filas de categorías (escritorio)
	AltoBoton = 54,
	TamRueda = 210,
	-- Estrecha (móvil)
	AnchoDerechaEstrecha = 190,
	TamRuedaEstrecha = 120,
	AltoCategoriaEstrecha = 62,
	AnchoCategoriaEstrecha = 168,
	AltoBotonEstrecho = 44,
}

return Config
