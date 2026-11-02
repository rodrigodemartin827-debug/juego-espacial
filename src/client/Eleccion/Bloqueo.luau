--!strict
--[[
	Bloqueo (Elección de bando): deja al jugador quieto y sin la interfaz del juego mientras elige bando, y lo
	devuelve TODO como estaba al terminar.

	Mientras está activo:
	  - Controles de Roblox desactivados (andar, saltar, joystick y botón de salto del móvil).
	  - Teclado y mando "tragados" con ContextActionService a una prioridad altísima: ni las teclas del combate, ni
	    las del escáner (Q), el pico (R) o la bodega (I) llegan al juego. Los clics en la interfaz sí funcionan,
	    porque la interfaz recibe la entrada antes que ContextActionService. Las teclas de la pantalla (flechas,
	    A/D, Intro, mando) se reenvían a quien la controla.
	  - Combate a pie en pausa (sin habilidades ni interfaz).
	  - Todas las ScreenGui del jugador ocultas, también las que aparezcan o intenten mostrarse mientras tanto,
	    salvo las de Config.Interfaz.GuisPermitidas (la propia pantalla, la cortina, las barras de cine).
	  - Mochila, vida y emotes de Roblox ocultos; avisos de proximidad (ProximityPrompt) apagados.
	  - Ratón libre y visible (por si el juego lo tenía bloqueado en el centro).
	  - Iluminación de la escena (exposición y una corrección de color propia).

	La cámara la lleva la Escena (client/Eleccion/Escena), que la deja en Scriptable; al terminar, este módulo la
	devuelve al personaje.

	El servidor, además, ancla el personaje y le da un ForceField invisible (Servicios/ServicioBandos): aunque un
	cliente manipulado se saltara todo esto, no podría moverse ni le harían daño.
]]

local ContextActionService = game:GetService("ContextActionService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")
local UserInputService = game:GetService("UserInputService")

local Config = require(ReplicatedStorage:WaitForChild("Shared").Eleccion.Config)
local ServicioCombate = require(script.Parent.Parent.Combate.ServicioCombate)

local Bloqueo = {}

local ACCION = "EleccionBloqueo"

-- Teclas que la pantalla usa (el resto se tragan sin más): "Izquierda", "Derecha" o "Elegir".
export type Tecla = string

local TECLAS: { [Enum.KeyCode]: Tecla } = {
	[Enum.KeyCode.Left] = "Izquierda",
	[Enum.KeyCode.A] = "Izquierda",
	[Enum.KeyCode.DPadLeft] = "Izquierda",
	[Enum.KeyCode.Right] = "Derecha",
	[Enum.KeyCode.D] = "Derecha",
	[Enum.KeyCode.DPadRight] = "Derecha",
	[Enum.KeyCode.Return] = "Elegir",
	[Enum.KeyCode.KeypadEnter] = "Elegir",
	[Enum.KeyCode.ButtonA] = "Elegir",
}

type Guardado = {
	Guis: { [ScreenGui]: boolean }, -- Enabled que tenía (o que quiso tener) cada ScreenGui
	Conexiones: { RBXScriptConnection },
	CoreGui: { [Enum.CoreGuiType]: boolean },
	Avisos: boolean?,
	Raton: Enum.MouseBehavior,
	IconoRaton: boolean,
	Exposicion: number,
	Color: ColorCorrectionEffect?,
	PalancaX: number, -- última posición del stick (para moverse con él una vez por empujón)
}

local guardado: Guardado? = nil

-- ===== Controles de Roblox =====

local function controles(activar: boolean)
	-- El PlayerModule puede tardar en existir al entrar al juego: se espera un poco, sin bloquear al que llama.
	task.spawn(function()
		pcall(function()
			local scripts = Players.LocalPlayer:WaitForChild("PlayerScripts", 10)
			local modulo = scripts and scripts:WaitForChild("PlayerModule", 10)
			if modulo == nil then
				return
			end
			local mando = (require(modulo :: ModuleScript) :: any):GetControls()
			if activar then
				mando:Enable()
			elseif guardado ~= nil then
				mando:Disable()
			end
		end)
	end)
end

-- ===== Interfaces =====

local function permitida(gui: ScreenGui): boolean
	return table.find(Config.Interfaz.GuisPermitidas, gui.Name) ~= nil
end

-- Oculta una ScreenGui y la vigila para que no se vuelva a mostrar mientras dure el bloqueo.
local function ocultar(estado: Guardado, gui: ScreenGui)
	if permitida(gui) or estado.Guis[gui] ~= nil then
		return
	end
	estado.Guis[gui] = gui.Enabled
	gui.Enabled = false
	table.insert(
		estado.Conexiones,
		gui:GetPropertyChangedSignal("Enabled"):Connect(function()
			if guardado == estado and gui.Enabled then
				-- Su sistema quiere mostrarla: se recuerda para cuando termine el bloqueo, pero sigue oculta.
				estado.Guis[gui] = true
				gui.Enabled = false
			end
		end)
	)
end

local function ocultarCoreGui(estado: Guardado)
	for _, nombre in Config.Interfaz.CoreGuiOcultas do
		local tipo = (Enum.CoreGuiType :: any)[nombre] :: Enum.CoreGuiType?
		if tipo then
			local ok, activo = pcall(function()
				return StarterGui:GetCoreGuiEnabled(tipo)
			end)
			if ok then
				estado.CoreGui[tipo] = activo
				pcall(function()
					StarterGui:SetCoreGuiEnabled(tipo, false)
				end)
			end
		end
	end
end

-- ===== Entrada =====

local function crearManejador(alPulsar: (Tecla) -> ())
	return function(_nombre: string, estadoEntrada: Enum.UserInputState, entrada: InputObject): Enum.ContextActionResult
		local estado = guardado
		if estado == nil then
			return Enum.ContextActionResult.Pass
		end
		if entrada.KeyCode == Enum.KeyCode.Thumbstick1 then
			-- El stick izquierdo mueve el resaltado una vez por cada empujón.
			local x = entrada.Position.X
			if math.abs(x) > 0.6 and math.abs(estado.PalancaX) <= 0.6 then
				alPulsar(if x < 0 then "Izquierda" else "Derecha")
			end
			estado.PalancaX = x
		elseif estadoEntrada == Enum.UserInputState.Begin then
			local tecla = TECLAS[entrada.KeyCode]
			if tecla then
				alPulsar(tecla)
			end
		end
		return Enum.ContextActionResult.Sink
	end
end

-- ===== API =====

-- ¿Está activo el bloqueo?
function Bloqueo.Activo(): boolean
	return guardado ~= nil
end

--[[
	Deja al jugador quieto y sin interfaz. `alPulsar` recibe las teclas de la pantalla ("Izquierda", "Derecha",
	"Elegir") que llegan por teclado o mando.
]]
function Bloqueo.Activar(alPulsar: (Tecla) -> ())
	if guardado ~= nil then
		return
	end
	local estado: Guardado = {
		Guis = {},
		Conexiones = {},
		CoreGui = {},
		Avisos = nil,
		Raton = UserInputService.MouseBehavior,
		IconoRaton = UserInputService.MouseIconEnabled,
		Exposicion = Lighting.ExposureCompensation,
		Color = nil,
		PalancaX = 0,
	}
	guardado = estado

	controles(false)
	if ServicioCombate.Pausar then
		ServicioCombate.Pausar(true)
	end

	-- Interfaces del juego: las que ya hay y las que vayan apareciendo.
	local interfaz = Players.LocalPlayer:WaitForChild("PlayerGui")
	for _, hijo in interfaz:GetChildren() do
		if hijo:IsA("ScreenGui") then
			ocultar(estado, hijo)
		end
	end
	table.insert(
		estado.Conexiones,
		interfaz.ChildAdded:Connect(function(hijo: Instance)
			if guardado == estado and hijo:IsA("ScreenGui") then
				ocultar(estado, hijo)
			end
		end)
	)
	ocultarCoreGui(estado)

	local ok, avisos = pcall(function()
		return ProximityPromptService.Enabled
	end)
	if ok then
		estado.Avisos = avisos
		pcall(function()
			ProximityPromptService.Enabled = false
		end)
	end

	-- Teclado y mando: todo se traga; las teclas de la pantalla se reenvían.
	ContextActionService:BindActionAtPriority(
		ACCION,
		crearManejador(alPulsar),
		false,
		Config.Interfaz.PrioridadBloqueo,
		Enum.UserInputType.Keyboard,
		Enum.UserInputType.Gamepad1
	)

	UserInputService.MouseBehavior = Enum.MouseBehavior.Default
	UserInputService.MouseIconEnabled = true

	-- Iluminación propia de la escena.
	Lighting.ExposureCompensation = Config.Iluminacion.ExposureCompensation
	local color = Instance.new("ColorCorrectionEffect")
	color.Name = "EleccionColor"
	color.Contrast = Config.Iluminacion.Contraste
	color.Saturation = Config.Iluminacion.Saturacion
	color.Parent = Lighting
	estado.Color = color

	-- Si reaparece mientras elige, los controles nuevos también se desactivan.
	table.insert(
		estado.Conexiones,
		Players.LocalPlayer.CharacterAdded:Connect(function()
			if guardado == estado then
				controles(false)
			end
		end)
	)
end

-- Devuelve todo como estaba antes de Activar. Se puede llamar aunque no esté activo.
function Bloqueo.Desactivar()
	local estado = guardado
	if estado == nil then
		return
	end
	guardado = nil

	for _, conexion in estado.Conexiones do
		conexion:Disconnect()
	end
	ContextActionService:UnbindAction(ACCION)

	for gui, enabled in estado.Guis do
		if gui.Parent ~= nil then
			gui.Enabled = enabled
		end
	end
	for tipo, activo in estado.CoreGui do
		pcall(function()
			StarterGui:SetCoreGuiEnabled(tipo, activo)
		end)
	end
	if estado.Avisos ~= nil then
		pcall(function()
			ProximityPromptService.Enabled = estado.Avisos :: boolean
		end)
	end

	UserInputService.MouseBehavior = estado.Raton
	UserInputService.MouseIconEnabled = estado.IconoRaton
	Lighting.ExposureCompensation = estado.Exposicion
	if estado.Color then
		estado.Color:Destroy()
	end

	if ServicioCombate.Pausar then
		ServicioCombate.Pausar(false)
	end
	controles(true)

	-- La cámara vuelve al personaje.
	local camara = workspace.CurrentCamera
	if camara then
		camara.CameraType = Enum.CameraType.Custom
		local personaje = Players.LocalPlayer.Character
		local humanoid = personaje and personaje:FindFirstChildOfClass("Humanoid")
		if humanoid then
			camara.CameraSubject = humanoid
		end
	end
end

return Bloqueo
