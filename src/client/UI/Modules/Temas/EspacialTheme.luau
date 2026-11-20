--!strict
--[[
	EspacialTheme: todas las constantes visuales de la interfaz en un solo lugar.

	REGLA: ningún módulo de la UI escribe un color, una transparencia, un tamaño de letra o un tiempo de animación
	a mano. Todo sale de aquí (la prueba `InterfazUI` lo comprueba buscando Color3.fromRGB / fromHex fuera de este
	archivo). Si hace falta un color nuevo, se añade aquí primero.

	Unidades: la interfaz se diseña en un lienzo de 960×540 "unidades de diseño" que se escala para llenar la
	pantalla (ver Componentes/Lienzo). A 1280×720 una unidad son 1,33 px; a 1920×1080, 2 px. Por eso aquí un
	tamaño de letra de 9 se ve como 12 px en la pantalla de referencia. El preview HTML usa los mismos números.
]]

local Theme = {}

-- =====================================================================================================
-- Colores
-- =====================================================================================================
Theme.Colores = {
	Fondo1 = Color3.fromHex("0A142D"), -- fondo más oscuro (degradado de las ventanas)
	Fondo2 = Color3.fromHex("0B1628"), -- fondo medio
	Fondo3 = Color3.fromHex("101B35"), -- fondo más claro
	FondoProfundo = Color3.fromHex("050A18"), -- casillas vacías, pistas de barras, tooltips
	FondoNegro = Color3.fromHex("020510"), -- velo de cooldown y modales

	Acento = Color3.fromHex("3DF2FF"), -- cian principal
	AcentoOscuro = Color3.fromHex("1BA8C9"), -- cian oscuro (final de degradados)
	AcentoClaro = Color3.fromHex("9FF8FF"), -- cian claro (brillos)
	TextoSobreAcento = Color3.fromHex("04121F"), -- texto e iconos sobre botones cian/dorados

	TextoPrincipal = Color3.fromHex("E0E6F0"), -- texto blanco
	TextoSecundario = Color3.fromRGB(255, 255, 255), -- se usa con Theme.Alpha.TextoSecundario
	Blanco = Color3.fromRGB(255, 255, 255),
	Negro = Color3.fromRGB(0, 0, 0),
	Gris = Color3.fromHex("9AA3B5"), -- texto e iconos apagados
	GrisOscuro = Color3.fromHex("3A4152"), -- nodos bloqueados, líneas apagadas

	-- Estadísticas
	Fuerza = Color3.fromHex("FF8844"),
	Aguante = Color3.fromHex("4AFF8B"),
	Espada = Color3.fromHex("3DF2FF"),
	Arma = Color3.fromHex("FF4444"),
	Habilidad = Color3.fromHex("A07AE8"),

	-- Rareza
	Comun = Color3.fromHex("888888"),
	PocoComun = Color3.fromHex("4AFF8B"),
	Raro = Color3.fromHex("4488FF"),
	Epico = Color3.fromHex("A07AE8"),
	Legendario = Color3.fromHex("FFB800"),
	Mitico = Color3.fromHex("FF4444"),

	-- Tienda y monedas
	Dorado = Color3.fromHex("FFB800"),
	DoradoOscuro = Color3.fromHex("FF8800"),
	DoradoClaro = Color3.fromHex("FFE08A"),
	TextoSobreDorado = Color3.fromHex("2A1500"),

	-- Avisos
	Peligro = Color3.fromHex("FF4444"),
	PeligroClaro = Color3.fromHex("FF7A7A"),
	Exito = Color3.fromHex("4AFF8B"),
	ExitoOscuro = Color3.fromHex("22C46A"),
	TextoSobreExito = Color3.fromHex("03170B"),

	-- Vida (degradado según el porcentaje: rojo < ámbar < verde)
	VidaAlta = Color3.fromHex("4AFF8B"),
	VidaMedia = Color3.fromHex("FFB800"),
	VidaBaja = Color3.fromHex("FF4444"),
	Fantasma = Color3.fromHex("FF4444"), -- barra de daño reciente
	Energia = Color3.fromHex("A07AE8"),
	EnergiaOscura = Color3.fromHex("6B4FC0"),

	-- Estado de los miembros del clan
	Online = Color3.fromHex("4AFF8B"),
	AFK = Color3.fromHex("FFB800"),
	Offline = Color3.fromHex("555555"),

	-- Rangos de ranked
	Bronce = Color3.fromHex("CD7F32"),
	Plata = Color3.fromHex("C0C0C0"),
	Oro = Color3.fromHex("FFD700"),
	Platino = Color3.fromHex("4AE0E0"),
	Diamante = Color3.fromHex("B9F2FF"),
	Maestro = Color3.fromHex("A07AE8"),
	GranMaestro = Color3.fromHex("FF4444"),
	-- Estelar: UIGradient animado con Theme.Degradados.Estelar

	-- Ramas del árbol de poderes
	RamaCombate = Color3.fromHex("FF6A3D"),
	RamaExploracion = Color3.fromHex("3DF2FF"),
	RamaSoporte = Color3.fromHex("4AFF8B"),

	-- Tipos de planeta en el mapa
	PlanetaHabitable = Color3.fromHex("4AFF8B"),
	PlanetaEsteril = Color3.fromHex("9AA3B5"),
	PlanetaVolcanico = Color3.fromHex("FF8844"),
	PlanetaAcuatico = Color3.fromHex("4488FF"),
	PlanetaNoDescubierto = Color3.fromHex("9AB6FF"),
	PlanetaHumanos = Color3.fromHex("3DF2FF"),
	PlanetaMonstruos = Color3.fromHex("B05CFF"),

	-- Bandos (icono de raza, holograma del personaje)
	BandoHumanos = Color3.fromHex("3DF2FF"),
	BandoMonstruos = Color3.fromHex("C084FF"),
}

local C = Theme.Colores

-- =====================================================================================================
-- Transparencias (0 = opaco, 1 = invisible)
-- =====================================================================================================
Theme.Alpha = {
	PanelFondo = 0.25, -- fondo de las ventanas
	Caja = 0.45, -- cajas dentro de una ventana (rgba(10,20,45,.55))
	BordeSutil = 0.88, -- rgba(61,242,255,.12)
	BordeActivo = 0.7, -- rgba(61,242,255,.3)
	TextoSecundario = 0.6, -- rgba(255,255,255,.4)
	TextoMedio = 0.3,
	TextoDimmed = 0.6,
	IconoDimmed = 0.5, -- icono inactivo de la barra lateral
	IconoSlotVacio = 0.62, -- icono del tipo en un slot vacío
	HoverFondo = 0.85, -- rgba(61,242,255,.15)
	BotonInactivo = 0.92, -- rgba(61,242,255,.08)
	SlotVacio = 0.91, -- tinte del slot vacío
	BordeSlotVacio = 0.68,
	Celda = 0.4, -- rgba(10,20,45,.6)
	CeldaOculta = 0.2,
	HUDFondo = 0.28, -- fondo de los elementos del HUD
	Cooldown = 0.22, -- velo oscuro del cooldown
	Arma_Inactiva = 0.6, -- el slot de arma que no está en la mano (opacidad 0,4)
	SidebarJuego = 0.38, -- barra lateral durante la partida
	SidebarMenu = 0.1, -- barra lateral con un menú abierto
	Velo = 0.45, -- velo del modal
	Tab = 0.85, -- pestaña activa rgba(61,242,255,.15)
	TabInactiva = 0.98,
	FilaAlterna = 0.978,
	Fantasma = 0.15,
}

-- =====================================================================================================
-- Tamaños (en unidades de diseño)
-- =====================================================================================================
Theme.Tamanos = {
	AnchoDiseno = 960,
	AltoDiseno = 540,
	EscalaMinima = 0.6, -- en pantallas muy pequeñas no se encoge más
	EscalaMaxima = 3,

	SidebarAncho = 52,
	SidebarX = 10,
	SidebarY = 58, -- debajo de los botones de Roblox de arriba a la izquierda
	IconoSidebar = 40, -- lado del botón
	IconoSidebarDibujo = 22, -- lado del icono dentro del botón
	BotonTiendaAlto = 50,
	SlotEquipo = 46,
	IconoStat = 18,
	CeldaInventario = 65,
	PaddingInventario = 4,
	ColumnasInventario = 6,

	Ventana = { X = 74, Y = 48, Ancho = 872, Alto = 480, Titulo = 36, Margen = 12 },

	BorderRadius = UDim.new(0, 8),
	BorderRadiusSmall = UDim.new(0, 5),
	RadioVentana = UDim.new(0, 10),
	RadioBoton = UDim.new(0, 6),
	RadioCirculo = UDim.new(0.5, 0),

	Trazo = 1, -- grosor de los bordes de paneles
	TrazoActivo = 1.5,
	TrazoGrueso = 2,
}

-- Disposición del HUD en partida (unidades de diseño, medidas desde la esquina que se indica).
Theme.HUD = {
	Vitales = { X = 74, Y = 48, AnchoVida = 158, AnchoEscudo = 110, AltoBarra = 11, AnchoEnergia = 278 },
	Info = { Y = 10 }, -- centrado un poco a la derecha
	Minimapa = { Margen = 14, Y = 48, Pequeno = 120, Grande = 220, RadioStuds = 160, Hz = 15 },
	Interaccion = { X = 560, Y = 290 },
	Armas = { X = 74, Margen = 16, Lado = 56 },
	Habilidades = { Margen = 14, Lado = 50, LadoDefinitiva = 58, Separacion = 12 },
	Rapidas = { Margen = 14 },
}

-- Tamaños de letra (unidades de diseño). Los nombres dicen para qué se usan.
Theme.Texto = {
	Micro = 6, -- "NIVEL" del badge, "TIENDA" bajo el icono
	Mini = 7, -- etiquetas de sección, pies
	Pequeno = 8, -- botones pequeños, filas de tabla secundarias
	Cuerpo = 9, -- texto normal
	Medio = 10,
	Grande = 11, -- valores de estadísticas, títulos de caja
	Titulo = 12, -- títulos de ventana, nombre del jugador
	Destacado = 14,
	Enorme = 17,
	Gigante = 20,
}

-- =====================================================================================================
-- Fuentes
-- =====================================================================================================
local FAMILIA = "rbxasset://fonts/families/GothamSSm.json"
Theme.Fuentes = {
	Titulo = Font.new(FAMILIA, Enum.FontWeight.Bold),
	Negrita = Font.new(FAMILIA, Enum.FontWeight.Heavy),
	Cuerpo = Font.new(FAMILIA, Enum.FontWeight.Regular),
	Medio = Font.new(FAMILIA, Enum.FontWeight.Medium),
	Stats = Font.new(FAMILIA, Enum.FontWeight.SemiBold),
	Cursiva = Font.new(FAMILIA, Enum.FontWeight.Regular, Enum.FontStyle.Italic),
	Mono = Font.new("rbxasset://fonts/families/RobotoMono.json", Enum.FontWeight.Regular),
}

-- =====================================================================================================
-- Animaciones
-- =====================================================================================================
Theme.Tweens = {
	Rapido = TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), -- hover de botones
	Normal = TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), -- abrir ventanas
	Suave = TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut),
	Rebote = TweenInfo.new(0.3, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
	Fundido = TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), -- HUD y pestañas
	Barra = TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), -- vida y escudo
	Fantasma = TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
	Tooltip = TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
	Toast = TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
	Pulso = TweenInfo.new(1.2, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), -- brillo que va y viene
	PulsoLento = TweenInfo.new(2.4, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
	Giro = TweenInfo.new(18, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut, -1),
	Arcoiris = TweenInfo.new(3, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut, -1),
}

Theme.Tiempos = {
	RetrasoFantasma = 0.55, -- lo que espera la barra roja antes de bajar
	DuracionToast = 3,
	DobleClic = 0.35, -- segundos máximos entre dos clics para que cuenten como doble clic
	DesplazamientoVentana = 14, -- unidades que se desliza una ventana al abrirse
	EscalaHover = 1.05,
	EscalaPulsado = 0.97,
	DesenfoqueMenu = 14, -- tamaño del BlurEffect con un menú abierto (0 = sin desenfoque)
	DesenfoqueMenuMovil = 6,
}

-- =====================================================================================================
-- Tablas de presentación (nombre y color de rarezas, estadísticas, rangos...)
-- =====================================================================================================
export type InfoRareza = { Nombre: string, Color: Color3, Orden: number }
Theme.Rareza = {
	Comun = { Nombre = "Común", Color = C.Comun, Orden = 1 },
	PocoComun = { Nombre = "Poco común", Color = C.PocoComun, Orden = 2 },
	Raro = { Nombre = "Raro", Color = C.Raro, Orden = 3 },
	Epico = { Nombre = "Épico", Color = C.Epico, Orden = 4 },
	Legendario = { Nombre = "Legendario", Color = C.Legendario, Orden = 5 },
	Mitico = { Nombre = "Mítico", Color = C.Mitico, Orden = 6 },
} :: { [string]: InfoRareza }

export type InfoStat = { Nombre: string, Color: Color3, Icono: string }
Theme.Stats = {
	Fuerza = { Nombre = "FUERZA", Color = C.Fuerza, Icono = "stat_fuerza" },
	Aguante = { Nombre = "AGUANTE", Color = C.Aguante, Icono = "stat_aguante" },
	Espada = { Nombre = "ESPADA", Color = C.Espada, Icono = "stat_espada" },
	Arma = { Nombre = "ARMA", Color = C.Arma, Icono = "stat_arma" },
	Habilidad = { Nombre = "HABILIDAD", Color = C.Habilidad, Icono = "stat_habilidad" },
} :: { [string]: InfoStat }
Theme.OrdenStats = { "Fuerza", "Aguante", "Espada", "Arma", "Habilidad" }

export type InfoRango = { Id: string, Nombre: string, Color: Color3, Elo: number, Icono: string, Divisiones: boolean }
Theme.Rangos = {
	{ Id = "Bronce", Nombre = "Bronce", Color = C.Bronce, Elo = 0, Icono = "rango_bronce", Divisiones = true },
	{ Id = "Plata", Nombre = "Plata", Color = C.Plata, Elo = 1000, Icono = "rango_plata", Divisiones = true },
	{ Id = "Oro", Nombre = "Oro", Color = C.Oro, Elo = 1500, Icono = "rango_oro", Divisiones = true },
	{ Id = "Platino", Nombre = "Platino", Color = C.Platino, Elo = 2000, Icono = "rango_platino", Divisiones = false },
	{
		Id = "Diamante",
		Nombre = "Diamante",
		Color = C.Diamante,
		Elo = 2600,
		Icono = "rango_diamante",
		Divisiones = false,
	},
	{ Id = "Maestro", Nombre = "Maestro", Color = C.Maestro, Elo = 3300, Icono = "rango_maestro", Divisiones = false },
	{
		Id = "GranMaestro",
		Nombre = "Gran Maestro",
		Color = C.GranMaestro,
		Elo = 4000,
		Icono = "rango_granmaestro",
		Divisiones = false,
	},
	{ Id = "Estelar", Nombre = "Estelar", Color = C.Oro, Elo = 4600, Icono = "rango_estelar", Divisiones = false },
} :: { InfoRango }

Theme.EstadoMiembro = {
	Online = C.Online,
	AFK = C.AFK,
	Offline = C.Offline,
} :: { [string]: Color3 }

Theme.Ramas = {
	Combate = C.RamaCombate,
	Exploracion = C.RamaExploracion,
	Soporte = C.RamaSoporte,
} :: { [string]: Color3 }

Theme.TipoPlaneta = {
	Habitable = C.PlanetaHabitable,
	Esteril = C.PlanetaEsteril,
	Volcanico = C.PlanetaVolcanico,
	Acuatico = C.PlanetaAcuatico,
} :: { [string]: Color3 }

-- Degradados (ColorSequence) reutilizables.
Theme.Degradados = {
	Ventana = ColorSequence.new({
		ColorSequenceKeypoint.new(0, C.Fondo1),
		ColorSequenceKeypoint.new(0.55, C.Fondo2),
		ColorSequenceKeypoint.new(1, C.Fondo3),
	}),
	Cian = ColorSequence.new(C.Acento, C.AcentoOscuro),
	Dorado = ColorSequence.new(C.Dorado, C.DoradoOscuro),
	Verde = ColorSequence.new(C.Aguante, C.ExitoOscuro),
	Energia = ColorSequence.new(C.EnergiaOscura, C.Energia),
	Escudo = ColorSequence.new(C.AcentoOscuro, C.Acento),
	Elo = ColorSequence.new({
		ColorSequenceKeypoint.new(0, C.Gris),
		ColorSequenceKeypoint.new(0.5, C.Plata),
		ColorSequenceKeypoint.new(1, C.Oro),
	}),
	-- Estelar: arcoíris dorado; se anima moviendo el Offset del UIGradient (ver UITweens.Arcoiris).
	Estelar = ColorSequence.new({
		ColorSequenceKeypoint.new(0, C.Oro),
		ColorSequenceKeypoint.new(0.25, Color3.fromHex("FF6AD5")),
		ColorSequenceKeypoint.new(0.5, Color3.fromHex("7AE7FF")),
		ColorSequenceKeypoint.new(0.75, Color3.fromHex("B6FF7A")),
		ColorSequenceKeypoint.new(1, C.Oro),
	}),
	TituloVentana = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.91),
		NumberSequenceKeypoint.new(0.55, 1),
		NumberSequenceKeypoint.new(1, 1),
	}),
}

-- Color de la barra de vida según la proporción (0..1): verde arriba del 50 %, ámbar a la mitad y rojo al final.
function Theme.ColorVida(proporcion: number): Color3
	local p = math.clamp(proporcion, 0, 1)
	if p > 0.5 then
		return C.VidaMedia:Lerp(C.VidaAlta, (p - 0.5) / 0.5)
	end
	return C.VidaBaja:Lerp(C.VidaMedia, p / 0.5)
end

-- Color de una rareza (las desconocidas cuentan como comunes).
function Theme.ColorRareza(rareza: string?): Color3
	local info = rareza and Theme.Rareza[rareza]
	return if info then info.Color else C.Comun
end

-- Rango por su id.
function Theme.Rango(id: string): InfoRango
	for _, rango in Theme.Rangos do
		if rango.Id == id then
			return rango
		end
	end
	return Theme.Rangos[1]
end

-- Precarga de las fuentes, para que no salgan con la de por defecto el primer fotograma.
function Theme.Iniciar()
	task.spawn(function()
		local ContentProvider = game:GetService("ContentProvider")
		local etiqueta = Instance.new("TextLabel")
		local muestras: { Instance } = {}
		local F = Theme.Fuentes
		for _, fuente: Font in { F.Titulo, F.Negrita, F.Cuerpo, F.Medio, F.Stats, F.Cursiva } do
			local copia = etiqueta:Clone()
			copia.FontFace = fuente
			table.insert(muestras, copia)
		end
		pcall(ContentProvider.PreloadAsync, ContentProvider, muestras)
	end)
end

return Theme
