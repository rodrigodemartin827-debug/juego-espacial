--!strict
--[[
	Pantalla de gráficos (cliente): cuatro tarjetas (Baja, Media, Alta, Ultra) abajo, y detrás el mundo de verdad con
	la cámara girando despacio alrededor del personaje, para ver el cambio en cuanto se pulsa un nivel.

	Mientras está abierta: el personaje no se mueve (controles desactivados), la interfaz del juego está oculta y la
	cámara es suya (atributo Config.AtributoCamara: la del planeta redondo se aparta). Al cerrar, todo vuelve.
	En la entrada, la cortina negra de la pantalla de bando se quita para ver el mundo y se vuelve a poner al
	terminar, para que el paso siguiente empiece desde negro como siempre.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local StarterGui = game:GetService("StarterGui")

local Config = require(ReplicatedStorage:WaitForChild("Shared").Graficos.Config)
local InterfazEleccion = require(script.Parent.Parent.Eleccion.Interfaz)

local Pantalla = {}

export type Opciones = {
	Inicial: string,
	Recomendado: string,
	PrimeraVez: boolean,
	AlProbar: (string) -> (),
	AlTerminar: (string) -> (),
}

local PASO_CAMARA = "GraficosCamara"
local NOMBRE_GUI = "PantallaGraficos"
local NOMBRE_BOTON = "BotonAjustesGraficos"

local jugador = Players.LocalPlayer
local gui: ScreenGui? = nil
local ocultas: { [ScreenGui]: boolean } = {}
local controles: any = nil

local function color(hex: string): Color3
	return Color3.fromHex(hex)
end

local function obtenerControles(): any
	if controles == nil then
		pcall(function()
			local modulo =
				require(jugador:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: ModuleScript) :: any
			controles = modulo:GetControls()
		end)
	end
	return controles
end

-- ===== Cámara =====

local function empezarCamara()
	jugador:SetAttribute(Config.AtributoCamara, true)
	local c = Config.Pantalla.Camara
	local inicio = os.clock()
	RunService:BindToRenderStep(PASO_CAMARA, Enum.RenderPriority.Camera.Value + 2, function()
		local camara = workspace.CurrentCamera
		local personaje = jugador.Character
		local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
		if camara == nil or raiz == nil then
			return
		end
		camara.CameraType = Enum.CameraType.Scriptable
		-- «Arriba» del sitio donde está (en el planeta redondo no es el eje Y).
		local arriba = (raiz.CFrame.UpVector).Unit
		local base = raiz.CFrame.LookVector
		base = (base - arriba * base:Dot(arriba)).Unit
		local angulo = (os.clock() - inicio) / c.VueltaSegundos * 2 * math.pi
		local fuera = CFrame.fromAxisAngle(arriba, angulo):VectorToWorldSpace(base)
		local foco = raiz.Position + arriba * c.Mira
		camara.CFrame = CFrame.lookAt(foco + fuera * c.Distancia + arriba * c.Altura, foco, arriba)
	end)
end

local function pararCamara()
	RunService:UnbindFromRenderStep(PASO_CAMARA)
	jugador:SetAttribute(Config.AtributoCamara, nil)
	local camara = workspace.CurrentCamera
	-- Fuera del planeta redondo la cámara normal de Roblox vuelve a llevar al personaje.
	local personaje = jugador.Character
	local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
	if camara and not (raiz and raiz:FindFirstChild("PlanetaRedondoAntigravedad")) then
		camara.CameraType = Enum.CameraType.Custom
	end
end

-- ===== Bloqueo (quieto y sin la interfaz del juego) =====

local function bloquear()
	local c = obtenerControles()
	if c then
		c:Disable()
	end
	for _, g in jugador:WaitForChild("PlayerGui"):GetChildren() do
		if g:IsA("ScreenGui") and g.Name ~= NOMBRE_GUI and g.Name ~= "EleccionCortina" and g.Enabled then
			ocultas[g] = true
			g.Enabled = false
		end
	end
	pcall(function()
		StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false)
	end)
end

local function desbloquear()
	for g in ocultas do
		if g.Parent then
			g.Enabled = true
		end
	end
	table.clear(ocultas)
	local c = obtenerControles()
	if c then
		c:Enable()
	end
	pcall(function()
		StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, true)
	end)
end

-- ===== Interfaz =====

local function texto(padre: Instance, props: { [string]: any }): TextLabel
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1
	t.Font = Enum.Font.GothamBold
	t.TextColor3 = color(Config.Pantalla.Colores.Texto)
	t.TextScaled = true
	for k, v in props do
		(t :: any)[k] = v
	end
	t.Parent = padre
	return t
end

local function redondear(objeto: GuiObject, radio: number)
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, radio)
	esquina.Parent = objeto
end

function Pantalla.Abierta(): boolean
	return gui ~= nil
end

function Pantalla.Abrir(op: Opciones)
	if gui ~= nil then
		return
	end
	local p = Config.Pantalla
	local col = p.Colores
	local elegido = op.Inicial

	local nueva = Instance.new("ScreenGui")
	nueva.Name = NOMBRE_GUI
	nueva.IgnoreGuiInset = true
	nueva.ResetOnSpawn = false
	nueva.DisplayOrder = 120
	nueva.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui = nueva

	-- Degradado oscuro abajo: el mundo se ve arriba y el panel se lee bien.
	local sombra = Instance.new("Frame")
	sombra.Size = UDim2.fromScale(1, 0.62)
	sombra.Position = UDim2.fromScale(0, 0.38)
	sombra.BackgroundColor3 = color(col.Fondo)
	sombra.BorderSizePixel = 0
	sombra.Parent = nueva
	local degradado = Instance.new("UIGradient")
	degradado.Rotation = 90
	degradado.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.35, 0.25),
		NumberSequenceKeypoint.new(1, 0.05),
	})
	degradado.Parent = sombra

	texto(nueva, {
		Text = p.Titulo,
		Size = UDim2.fromScale(0.5, 0.075),
		Position = UDim2.fromScale(0.25, 0.43),
	})
	texto(nueva, {
		Text = p.Subtitulo,
		Font = Enum.Font.Gotham,
		TextColor3 = color(col.TextoSuave),
		Size = UDim2.fromScale(0.7, 0.032),
		Position = UDim2.fromScale(0.15, 0.51),
	})

	-- Las cuatro tarjetas.
	local fila = Instance.new("Frame")
	fila.BackgroundTransparency = 1
	fila.Size = UDim2.fromScale(0.86, 0.27)
	fila.Position = UDim2.fromScale(0.07, 0.57)
	fila.Parent = nueva
	local lista = Instance.new("UIListLayout")
	lista.FillDirection = Enum.FillDirection.Horizontal
	lista.HorizontalAlignment = Enum.HorizontalAlignment.Center
	lista.Padding = UDim.new(0.015, 0)
	lista.SortOrder = Enum.SortOrder.LayoutOrder
	lista.Parent = fila

	local bordes: { [string]: UIStroke } = {}
	local function marcar()
		for nombre, borde in bordes do
			local si = nombre == elegido
			borde.Color = if si then color(col.Elegida) else color(col.Borde)
			borde.Thickness = if si then 3 else 1.5
		end
	end

	for indice, nombre in Config.Orden do
		local nivel = Config.Niveles[nombre]
		local tarjeta = Instance.new("TextButton")
		tarjeta.Name = nombre
		tarjeta.Text = ""
		tarjeta.AutoButtonColor = true
		tarjeta.LayoutOrder = indice
		tarjeta.Size = UDim2.fromScale(0.235, 1)
		tarjeta.BackgroundColor3 = color(col.Tarjeta)
		tarjeta.BackgroundTransparency = 0.1
		tarjeta.Parent = fila
		redondear(tarjeta, 12)
		local borde = Instance.new("UIStroke")
		borde.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
		borde.Parent = tarjeta
		bordes[nombre] = borde

		texto(
			tarjeta,
			{ Text = nivel.Nombre, Size = UDim2.fromScale(0.8, 0.24), Position = UDim2.fromScale(0.1, 0.16) }
		)
		texto(tarjeta, {
			Text = nivel.Descripcion,
			Font = Enum.Font.Gotham,
			TextColor3 = color(col.TextoSuave),
			TextWrapped = true,
			Size = UDim2.fromScale(0.86, 0.44),
			Position = UDim2.fromScale(0.07, 0.46),
		})
		if nombre == op.Recomendado then
			local etiqueta = texto(tarjeta, {
				Text = p.Recomendado,
				TextColor3 = color(col.Fondo),
				BackgroundTransparency = 0,
				BackgroundColor3 = color(col.Recomendado),
				Size = UDim2.fromScale(0.62, 0.13),
				Position = UDim2.fromScale(0.19, -0.065),
			})
			redondear(etiqueta, 8)
		end
		tarjeta.Activated:Connect(function()
			if elegido ~= nombre then
				elegido = nombre
				marcar()
				op.AlProbar(nombre)
			end
		end)
	end
	marcar()

	local boton = Instance.new("TextButton")
	boton.Text = if op.PrimeraVez then p.Continuar else p.Cerrar
	boton.Font = Enum.Font.GothamBold
	boton.TextScaled = true
	boton.TextColor3 = color(col.Fondo)
	boton.BackgroundColor3 = color(col.Elegida)
	boton.Size = UDim2.fromScale(0.2, 0.065)
	boton.Position = UDim2.fromScale(0.4, 0.875)
	boton.Parent = nueva
	redondear(boton, 12)
	local relleno = Instance.new("UIPadding")
	relleno.PaddingTop = UDim.new(0.18, 0)
	relleno.PaddingBottom = UDim.new(0.18, 0)
	relleno.Parent = boton

	bloquear()
	empezarCamara()
	nueva.Parent = jugador:WaitForChild("PlayerGui")
	op.AlProbar(elegido)
	-- Se quita la cortina de la entrada para ver el mundo de verdad.
	InterfazEleccion.Fundir(0, p.FundidoSegundos)
	task.delay(p.FundidoSegundos, function()
		if gui == nueva then
			InterfazEleccion.QuitarCortina()
		end
	end)

	boton.Activated:Connect(function()
		if gui ~= nueva then
			return
		end
		if op.PrimeraVez then
			-- A negro, como empieza el paso siguiente.
			InterfazEleccion.Fundir(1, p.FundidoSegundos)
			task.wait(p.FundidoSegundos)
		end
		gui = nil
		nueva:Destroy()
		pararCamara()
		desbloquear()
		op.AlTerminar(elegido)
	end)
end

-- El botón de ajustes (arriba a la derecha) que vuelve a abrir la pantalla.
function Pantalla.CrearBotonAjustes(alPulsar: () -> ())
	local contenedor = Instance.new("ScreenGui")
	contenedor.Name = NOMBRE_BOTON
	contenedor.ResetOnSpawn = false
	contenedor.DisplayOrder = 5
	local boton = Instance.new("TextButton")
	boton.Text = Config.Pantalla.BotonAjustes
	boton.Font = Enum.Font.GothamBold
	boton.TextScaled = true
	boton.TextColor3 = color(Config.Pantalla.Colores.Texto)
	boton.BackgroundColor3 = color(Config.Pantalla.Colores.Tarjeta)
	boton.BackgroundTransparency = 0.2
	boton.AnchorPoint = Vector2.new(1, 0)
	boton.Size = UDim2.fromOffset(110, 34)
	boton.Position = UDim2.new(1, -12, 0, 12)
	boton.Parent = contenedor
	redondear(boton, 10)
	local relleno = Instance.new("UIPadding")
	relleno.PaddingTop = UDim.new(0, 7)
	relleno.PaddingBottom = UDim.new(0, 7)
	relleno.Parent = boton
	boton.Activated:Connect(alPulsar)
	contenedor.Parent = jugador:WaitForChild("PlayerGui")
end

return Pantalla
