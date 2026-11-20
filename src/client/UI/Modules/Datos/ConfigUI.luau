--!strict
--[[
	ConfigUI: todo lo ajustable de la interfaz que no es un color (eso está en EspacialTheme): teclas, qué
	habilidades van en el HUD, interruptores de comportamiento, IDs de productos y la lista de ajustes.

	Teclas: se eligen para no chocar con las que el juego ya usa:
	  W A S D Espacio (moverse) · Q (escanear) · R (picar) · E (ProximityPrompt) · F (aterrizar) · Shift (turbo)
	  Z X C (Rayo) · V B N (Gravedad) · C y Ctrl (bajar con la nave)
	Por eso PERSONAJE va en P (no en C, que es la definitiva del Rayo) y las casillas del HUD muestran las teclas
	reales de Combate/Datos/Poderes en vez de Q/W/E/R (W es andar, Q escanear, E interactuar y R picar).
]]

local ConfigUI = {}

-- ===== Teclas de la interfaz =====
-- Nombres de Enum.KeyCode (texto, para que este módulo sea solo datos y lo puedan cargar las pruebas).
ConfigUI.Teclas = {
	Personaje = "P",
	Inventario = "I", -- sustituye a la tecla de la bodega antigua (Exploracion)
	Poderes = "K",
	Mapa = "M", -- con un menú abierto abre el mapa; en partida amplía el minimapa
	Cerrar = "Escape", -- Roblox puede quedarse Escape para su menú: la X de la ventana siempre funciona
	Arma1 = "One",
	Arma2 = "Two",
	-- Mando
	MandoMenu = "ButtonSelect", -- abre/cierra el personaje
	MandoCerrar = "ButtonB",
} :: { [string]: string }

-- Teclas que ya usa el juego fuera de la interfaz (la prueba InterfazUI comprueba que no se repiten).
ConfigUI.TeclasDelJuego = { "W", "A", "S", "D", "Space", "Q", "R", "E", "F", "LeftShift", "LeftControl" }

-- ===== HUD =====
ConfigUI.HUD = {
	-- Las 4 casillas de habilidad: ids de Combate/Datos/Poderes. La tecla, el nombre y el cooldown salen de allí.
	Habilidades = { "Rayo_Basico", "Rayo_Fuerte", "Rayo_Definitiva", "Gravedad_Basico" },
	-- Icono de cada habilidad (herramientas/iconos_ui/iconos.mjs).
	IconosHabilidad = {
		Rayo_Basico = "hab_rayo",
		Rayo_Fuerte = "hab_trueno",
		Rayo_Definitiva = "hab_tormenta",
		Gravedad_Basico = "hab_pulso",
		Gravedad_Fuerte = "hab_aplastar",
		Gravedad_Definitiva = "hab_singularidad",
		Combo = "hab_combo",
	} :: { [string]: string },
	-- Qué se ve en el minimapa.
	MinimapaJugadores = true, -- otros jugadores (verde si son de tu bando, rojo si no)
	MinimapaObjetivos = true, -- modelos con la etiqueta de combate (muñecos, criaturas hostiles)
	-- Info de partida mientras no haya un sistema de sectores y modos (el servidor podrá cambiarla con
	-- HUDPartida.PonerInfo).
	SectorInicial = "SECTOR 7-B",
	ModoInicial = "EXPLORACIÓN",
}

-- ===== Comportamiento =====
-- La UI nueva sustituye al HUD de combate antiguo (Combate/Interfaz) y a la pastilla de la bodega (Exploracion).
ConfigUI.SustituirInterfacesAntiguas = true
-- Los ProximityPrompt se dibujan con el aviso propio del HUD ("[E] Recoger") en vez del de Roblox.
ConfigUI.AvisoInteraccionPropio = true
-- Desenfoque del mundo con un menú abierto (BlurEffect en Lighting). En móvil, más suave.
ConfigUI.DesenfoqueMenu = true

-- ===== Compras con Robux =====
-- Productos de desarrollador para las gemas (MarketplaceService:PromptProductPurchase). 0 = sin configurar:
-- el botón avisa en vez de abrir la compra. OJO: hace falta un ProcessReceipt en el SERVIDOR que entregue las
-- gemas; sin él Roblox cobra y no se entrega nada. Ese servicio todavía no existe.
ConfigUI.ProductosGemas = {
	{ Gemas = 100, Robux = 99, ProductoId = 0 },
	{ Gemas = 550, Robux = 449, ProductoId = 0 },
	{ Gemas = 1200, Robux = 899, ProductoId = 0 },
}
-- Pases de juego (MarketplaceService:PromptGamePassPurchase). 0 = sin configurar.
ConfigUI.PasesJuego = {
	PaseX2 = 0,
	PaseAlmacen = 0,
	PaseVIP = 0,
} :: { [string]: number }

-- ===== Barra lateral =====
export type BotonBarra = { Id: string, Icono: string, Nombre: string, Tecla: string? }
ConfigUI.Sidebar = {
	{ Id = "personaje", Icono = "sidebar_personaje", Nombre = "PERSONAJE", Tecla = "P" },
	{ Id = "inventario", Icono = "sidebar_inventario", Nombre = "INVENTARIO", Tecla = "I" },
	{ Id = "poderes", Icono = "sidebar_poderes", Nombre = "PODERES", Tecla = "K" },
	{ Id = "clan", Icono = "sidebar_clan", Nombre = "TRIPULACIÓN" },
	{ Id = "ranked", Icono = "sidebar_ranked", Nombre = "RANKED" },
	{ Id = "indice", Icono = "sidebar_indice", Nombre = "ÍNDICE" },
	{ Id = "mapa", Icono = "sidebar_mapa", Nombre = "MAPA GALÁCTICO", Tecla = "M" },
	{ Id = "ajustes", Icono = "sidebar_ajustes", Nombre = "AJUSTES" },
} :: { BotonBarra }
ConfigUI.BotonTienda = { Id = "tienda", Icono = "sidebar_tienda", Nombre = "TIENDA" } :: BotonBarra

-- ===== Ajustes =====
-- Efecto: qué hace cada ajuste al cambiar (lo aplica PanelAjustes). Los que no tienen efecto todavía lo dicen.
export type FilaAjuste = {
	Id: string,
	Titulo: string,
	Descripcion: string?,
	Tipo: "Deslizador" | "Interruptor" | "Lista" | "Tecla",
	Min: number?,
	Max: number?,
	Unidad: string?,
	Opciones: { string }?,
	Valor: any, -- valor por defecto
	Bloqueado: boolean?, -- se ve pero no se puede cambiar todavía
}
export type CategoriaAjustes = { Id: string, Nombre: string, Icono: string, Filas: { FilaAjuste } }

ConfigUI.Ajustes = {
	{
		Id = "Graficos",
		Nombre = "GRÁFICOS",
		Icono = "aj_graficos",
		Filas = {
			{
				Id = "Calidad",
				Titulo = "Calidad",
				Descripcion = "Automática ajusta los efectos a lo que aguante tu dispositivo.",
				Tipo = "Lista",
				Opciones = { "Automática", "Bajo", "Medio", "Alto" },
				Valor = "Automática",
			},
			{
				Id = "Distancia",
				Titulo = "Distancia de render",
				Descripcion = "Cuánto terreno se carga alrededor.",
				Tipo = "Deslizador",
				Min = 256,
				Max = 2048,
				Unidad = "",
				Valor = 1024,
			},
			{
				Id = "Particulas",
				Titulo = "Partículas",
				Descripcion = "Desactívalas si el juego va lento.",
				Tipo = "Interruptor",
				Valor = true,
			},
		},
	},
	{
		Id = "Audio",
		Nombre = "AUDIO",
		Icono = "aj_audio",
		Filas = {
			{
				Id = "VolumenMaestro",
				Titulo = "Volumen maestro",
				Tipo = "Deslizador",
				Min = 0,
				Max = 100,
				Unidad = "%",
				Valor = 80,
			},
			{
				Id = "VolumenMusica",
				Titulo = "Música",
				Tipo = "Deslizador",
				Min = 0,
				Max = 100,
				Unidad = "%",
				Valor = 60,
			},
			{
				Id = "VolumenSFX",
				Titulo = "Efectos (SFX)",
				Tipo = "Deslizador",
				Min = 0,
				Max = 100,
				Unidad = "%",
				Valor = 90,
			},
			{
				Id = "VolumenVoces",
				Titulo = "Voces",
				Tipo = "Deslizador",
				Min = 0,
				Max = 100,
				Unidad = "%",
				Valor = 70,
			},
		},
	},
	{
		Id = "Controles",
		Nombre = "CONTROLES",
		Icono = "aj_controles",
		Filas = {
			{
				Id = "Sensibilidad",
				Titulo = "Sensibilidad del ratón",
				Tipo = "Deslizador",
				Min = 1,
				Max = 100,
				Unidad = "",
				Valor = 45,
			},
			{ Id = "TeclaPersonaje", Titulo = "Personaje", Tipo = "Tecla", Valor = "P" },
			{ Id = "TeclaInventario", Titulo = "Inventario", Tipo = "Tecla", Valor = "I" },
			{ Id = "TeclaPoderes", Titulo = "Poderes", Tipo = "Tecla", Valor = "K" },
			{ Id = "TeclaMapa", Titulo = "Mapa / minimapa", Tipo = "Tecla", Valor = "M" },
			{
				Id = "TeclasHabilidades",
				Titulo = "Habilidades",
				Descripcion = "Se cambian en los datos de Combate (Poderes).",
				Tipo = "Tecla",
				Valor = "Z X C V",
				Bloqueado = true,
			},
		},
	},
	{
		Id = "Interfaz",
		Nombre = "INTERFAZ",
		Icono = "aj_interfaz",
		Filas = {
			{
				Id = "TamanoHUD",
				Titulo = "Tamaño del HUD",
				Descripcion = "Escala de la interfaz en partida.",
				Tipo = "Deslizador",
				Min = 70,
				Max = 130,
				Unidad = "%",
				Valor = 100,
			},
			{
				Id = "TransparenciaMinimapa",
				Titulo = "Transparencia del minimapa",
				Tipo = "Deslizador",
				Min = 0,
				Max = 80,
				Unidad = "%",
				Valor = 0,
			},
			{
				Id = "Notificaciones",
				Titulo = "Notificaciones",
				Descripcion = "Avisos de objetos, compras y misiones.",
				Tipo = "Interruptor",
				Valor = true,
			},
		},
	},
	{
		Id = "Juego",
		Nombre = "JUEGO",
		Icono = "aj_juego",
		Filas = {
			{
				Id = "Idioma",
				Titulo = "Idioma",
				Tipo = "Lista",
				Opciones = { "Español", "English", "Português" },
				Valor = "Español",
			},
			{
				Id = "Region",
				Titulo = "Región del servidor",
				Tipo = "Lista",
				Opciones = { "Automática", "Europa", "Norteamérica", "Sudamérica", "Asia" },
				Valor = "Automática",
			},
		},
	},
} :: { CategoriaAjustes }

return ConfigUI
