--!strict
--[[
	HUDController: controlador central de toda la interfaz. Solo orquesta: crea la ScreenGui y el lienzo, arranca el HUD,
	la barra lateral y las pantallas, y decide cuál se ve.

	  - Abrir una pantalla (barra lateral o tecla): el HUD se funde (0,2 s), el mundo se desenfoca, la ventana entra
	    deslizándose y se marca su botón. Pulsar el mismo botón (o la X, o Escape) vuelve a la partida.
	  - Teclas (ConfigUI.Teclas, se pueden cambiar en Ajustes): P personaje, I inventario, K poderes, M mapa (en partida
	    amplía el minimapa), 1/2 armas. Mando: Select abre/cierra el personaje y B cierra.
	  - Al pilotar una nave el HUD se oculta (la nave tiene su propio panel).
	  - Sustituye al HUD de combate y a la bodega antiguos (ConfigUI.SustituirInterfacesAntiguas).

	Es un ModuleScript (no un LocalScript aparte): lo arranca init.client.luau DESPUÉS de los demás servicios, porque
	necesita la red y los datos ya iniciados. Un segundo LocalScript correría en paralelo y podría adelantarse.
]]

local ContextActionService = game:GetService("ContextActionService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local Modulos = script.Parent.Modules
local Theme = require(Modulos.Temas.EspacialTheme)
local UITweens = require(Modulos.Animaciones.UITweens)
local Lienzo = require(Modulos.Componentes.Lienzo)
local Tooltip = require(Modulos.Componentes.Tooltip)
local Modal = require(Modulos.Componentes.Modal)
local Notificacion = require(Modulos.Componentes.Notificacion)
local ConfigUI = require(Modulos.Datos.ConfigUI)
local EstadoUI = require(Modulos.EstadoUI)
local Contexto = require(Modulos.Contexto)
local Sidebar = require(Modulos.Sidebar)
local HUDPartida = require(Modulos.HUDPartida)
local PanelPersonaje = require(Modulos.PanelPersonaje)
local PanelPoderes = require(Modulos.PanelPoderes)
local PanelClan = require(Modulos.PanelClan)
local PanelRanked = require(Modulos.PanelRanked)
local PanelIndice = require(Modulos.PanelIndice)
local PanelMapa = require(Modulos.PanelMapa)
local PanelAjustes = require(Modulos.PanelAjustes)
local PanelTienda = require(Modulos.PanelTienda)

local Cliente = script.Parent.Parent
local ServicioCombate = require(Cliente.Combate.ServicioCombate)
local ServicioExploracion = require(Cliente.Exploracion.ServicioExploracion)
local Calidad = require(Cliente.VFX.Calidad)

local HUDController = {}

-- ===== Estado =====
local panelActual: string? = nil
local menuAbierto = false
local pilotando = false
local iniciado = false
local desenfoque: BlurEffect? = nil
local liberarRaton: TextButton? = nil

-- Pantallas por id. "inventario" es la ventana de Personaje abierta en su pestaña de inventario.
local paneles: { [string]: Contexto.Pantalla } = {
	personaje = PanelPersonaje,
	inventario = {
		Iniciar = function(_: Contexto.Contexto) end,
		Mostrar = function(_: string?)
			PanelPersonaje.Mostrar("inventario")
		end,
		Ocultar = PanelPersonaje.Ocultar,
	},
	poderes = PanelPoderes,
	clan = PanelClan,
	ranked = PanelRanked,
	indice = PanelIndice,
	mapa = PanelMapa,
	ajustes = PanelAjustes,
	tienda = PanelTienda,
}

-- Las que comparten ventana (cambiar entre ellas no cierra la ventana).
local VENTANA: { [string]: string } = { inventario = "personaje" }
local function ventanaDe(id: string): string
	return VENTANA[id] or id
end

-- ===== Desenfoque del mundo =====

local function desenfocar(activo: boolean)
	if not ConfigUI.DesenfoqueMenu then
		return
	end
	local efecto = desenfoque
	if efecto == nil then
		local nuevo = Instance.new("BlurEffect")
		nuevo.Name = "DesenfoqueMenu"
		nuevo.Size = 0
		nuevo.Parent = Lighting
		desenfoque = nuevo
		efecto = nuevo
	end
	local tamano = if Calidad.EsMovil then Theme.Tiempos.DesenfoqueMenuMovil else Theme.Tiempos.DesenfoqueMenu
	UITweens.Tween(efecto :: BlurEffect, Theme.Tweens.Normal, { Size = if activo then tamano else 0 })
end

-- ===== Abrir y cerrar =====

local cerrarMenu: () -> ()

local function abrirPanel(id: string)
	local panel = paneles[id]
	if panel == nil then
		return
	end
	if panelActual == id then
		cerrarMenu()
		return
	end
	Tooltip.Ocultar()
	Modal.Cerrar()
	-- Cerrar la ventana anterior si es otra (inventario y personaje comparten la misma).
	local anterior = panelActual
	if anterior and paneles[anterior] and ventanaDe(anterior) ~= ventanaDe(id) then
		paneles[anterior].Ocultar()
	end
	HUDPartida.Ocultar()
	panelActual = id
	if not menuAbierto then
		menuAbierto = true
		Sidebar.ModoMenu(true)
		Notificacion.ModoMenu(true)
		desenfocar(true)
		if liberarRaton then
			liberarRaton.Visible = true
		end
	end
	panel.Mostrar()
	Sidebar.MarcarActivo(id)
end

function cerrarMenu()
	if not menuAbierto then
		return
	end
	Tooltip.Ocultar()
	Modal.Cerrar()
	local actual = panelActual
	if actual and paneles[actual] then
		paneles[actual].Ocultar()
	end
	panelActual = nil
	menuAbierto = false
	Sidebar.MarcarActivo(nil)
	Sidebar.ModoMenu(false)
	Notificacion.ModoMenu(false)
	desenfocar(false)
	if liberarRaton then
		liberarRaton.Visible = false
	end
	if not pilotando then
		HUDPartida.Mostrar()
	end
end

-- Una pantalla cambió de pestaña (Personaje <-> Inventario): solo cambia el botón marcado.
local function marcarPantalla(id: string)
	if menuAbierto and paneles[id] then
		panelActual = id
		Sidebar.MarcarActivo(id)
	end
end

-- ===== Teclas =====

local ACCION = "InterfazMenus"

local function teclaDe(nombre: string): Enum.KeyCode?
	local ok, tecla = pcall(function()
		return (Enum.KeyCode :: any)[nombre]
	end)
	return if ok then tecla else nil
end

local function alTecla(_: string, estado: Enum.UserInputState, entrada: InputObject): Enum.ContextActionResult
	if estado ~= Enum.UserInputState.Begin then
		return Enum.ContextActionResult.Pass
	end
	local nombre = entrada.KeyCode.Name
	local T = ConfigUI.Teclas
	if nombre == T.Personaje or nombre == T.MandoMenu then
		abrirPanel("personaje")
	elseif nombre == T.Inventario then
		abrirPanel("inventario")
	elseif nombre == T.Poderes then
		abrirPanel("poderes")
	elseif nombre == T.Mapa then
		if menuAbierto then
			abrirPanel("mapa")
		else
			HUDPartida.ToggleMinimap()
		end
	elseif nombre == T.MandoCerrar then
		if not menuAbierto then
			return Enum.ContextActionResult.Pass
		end
		cerrarMenu()
	elseif nombre == T.Arma1 and not menuAbierto then
		HUDPartida.CambiarArma(1)
	elseif nombre == T.Arma2 and not menuAbierto then
		HUDPartida.CambiarArma(2)
	else
		return Enum.ContextActionResult.Pass
	end
	return Enum.ContextActionResult.Sink
end

-- (Re)asocia las teclas. Prioridad alta: así la I llega aquí antes que a cualquier otro uso.
local function enlazarTeclas()
	ContextActionService:UnbindAction(ACCION)
	local teclas: { Enum.KeyCode } = {}
	for _, nombre in ConfigUI.Teclas do
		local tecla = teclaDe(nombre)
		if tecla and tecla ~= Enum.KeyCode.Escape then
			table.insert(teclas, tecla)
		end
	end
	ContextActionService:BindActionAtPriority(
		ACCION,
		alTecla,
		false,
		Enum.ContextActionPriority.High.Value,
		table.unpack(teclas)
	)
end

-- ===== Ajustes que afectan a la interfaz =====

local AJUSTES_TECLAS: { [string]: string } = {
	TeclaPersonaje = "Personaje",
	TeclaInventario = "Inventario",
	TeclaPoderes = "Poderes",
	TeclaMapa = "Mapa",
}

local function alCambiarAjuste(id: string, valor: any)
	if id == "TamanoHUD" then
		HUDPartida.Escalar((tonumber(valor) or 100) / 100)
	elseif id == "TransparenciaMinimapa" then
		HUDPartida.TransparenciaMinimapa((tonumber(valor) or 0) / 100)
	elseif id == "Notificaciones" then
		Notificacion.Activar(valor == true)
	elseif AJUSTES_TECLAS[id] and type(valor) == "string" then
		ConfigUI.Teclas[AJUSTES_TECLAS[id]] = valor
		enlazarTeclas()
	end
end

-- ===== Arranque =====

--[[
	Construye toda la interfaz. Llamar una vez desde init.client.luau, después de ServicioRed, ServicioDatos,
	ServicioCombate y ServicioExploracion.
]]
function HUDController.Iniciar()
	if iniciado then
		return
	end
	iniciado = true
	local jugador = Players.LocalPlayer

	Theme.Iniciar()
	EstadoUI.Iniciar()

	-- ScreenGui a pantalla completa (los elementos de arriba ya dejan sitio a los botones de Roblox).
	local gui = Instance.new("ScreenGui")
	gui.Name = "InterfazJuego"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.DisplayOrder = 20
	gui.Parent = jugador:WaitForChild("PlayerGui")

	local lienzo = Lienzo.Crear(gui, "Lienzo")
	local raiz = lienzo.Raiz

	-- Botón invisible con Modal = true: mientras hay un menú abierto, libera el ratón aunque la cámara lo bloquee.
	local boton = Instance.new("TextButton")
	boton.Name = "LiberarRaton"
	boton.Text = ""
	boton.BackgroundTransparency = 1
	boton.Size = UDim2.fromOffset(0, 0)
	boton.Modal = true
	boton.Visible = false
	boton.Parent = raiz
	liberarRaton = boton

	local contexto: Contexto.Contexto = {
		Raiz = raiz,
		AUnidades = lienzo.AUnidades,
		Abrir = abrirPanel,
		Cerrar = function()
			cerrarMenu()
		end,
		Notificar = Notificacion.Mostrar,
		MarcarPantalla = marcarPantalla,
	}

	HUDPartida.Iniciar(raiz, ServicioCombate.Solicitar)
	Sidebar.Iniciar(raiz, abrirPanel)
	for _, id in { "personaje", "poderes", "clan", "ranked", "indice", "mapa", "ajustes", "tienda" } do
		paneles[id].Iniciar(contexto)
	end
	Tooltip.Iniciar(raiz, lienzo.AUnidades)
	Modal.Iniciar(raiz)
	Notificacion.Iniciar(raiz)

	-- La UI nueva sustituye al HUD de combate antiguo y a la bodega de exploración.
	if ConfigUI.SustituirInterfacesAntiguas then
		ServicioCombate.SustituirInterfaz()
		ServicioExploracion.SustituirBodega()
	end

	-- Al pilotar una nave el HUD a pie se oculta; al aterrizar vuelve.
	ServicioCombate.PausaCambiada:Conectar(function(pausado: boolean)
		pilotando = pausado
		if pausado then
			HUDPartida.Ocultar()
		elseif not menuAbierto then
			HUDPartida.Mostrar()
		end
	end)

	PanelAjustes.Cambio:Conectar(alCambiarAjuste)
	enlazarTeclas()
	-- Escape (si Roblox no se la queda para su menú) cierra el menú.
	UserInputService.InputBegan:Connect(function(entrada, procesada)
		if not procesada and entrada.KeyCode == Enum.KeyCode.Escape and menuAbierto then
			if Modal.EstaAbierto() then
				Modal.Cerrar()
			else
				cerrarMenu()
			end
		end
	end)
end

-- Para otros sistemas: abrir una pantalla o volver a la partida desde fuera (por ejemplo, un NPC que abre la tienda).
HUDController.Abrir = abrirPanel
HUDController.Cerrar = function()
	cerrarMenu()
end

return HUDController
