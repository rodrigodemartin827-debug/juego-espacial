--!strict
--[[
	Pantalla del editor de personaje (cliente). El personaje de verdad a la izquierda (se gira arrastrando), y a la
	derecha las pestañas (Personaje/ConfigEditor.Pestanas) con sus opciones. Abajo, ALEATORIO y CONTINUAR.

	Cada cambio se ve al momento en el personaje (AlCambiar; la vista previa la pone el cliente, solo para él). Al
	pulsar CONTINUAR se llama AlTerminar con la apariencia elegida (el servicio la guarda en el servidor).

	Mientras está abierta: personaje quieto, interfaz del juego oculta y la cámara es suya (el atributo de cámara de
	Graficos/Config: la del planeta redondo se aparta).
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local StarterGui = game:GetService("StarterGui")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Apariencia = require(Shared.Personaje.Apariencia)
local Config = require(Shared.Personaje.ConfigEditor)
local ConfigGraficos = require(Shared.Graficos.Config)

local Pantalla = {}

export type Opciones = {
	Inicial: Apariencia.Apariencia,
	AlCambiar: (Apariencia.Apariencia) -> (),
	AlTerminar: (Apariencia.Apariencia) -> (),
}

local NOMBRE_GUI = "EditorPersonaje"
local PASO_CAMARA = "EditorCamara"

local jugador = Players.LocalPlayer
local gui: ScreenGui? = nil
local ocultas: { [ScreenGui]: boolean } = {}
local conexiones: { RBXScriptConnection } = {}

local function color(hex: string): Color3
	return Color3.fromHex(hex)
end

-- ===== Bloqueo (quieto y sin la interfaz del juego) =====

local function controles(): any
	local ok, c = pcall(function()
		local modulo =
			require(jugador:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: ModuleScript) :: any
		return modulo:GetControls()
	end)
	return if ok then c else nil
end

local function bloquear()
	local c = controles()
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
	local c = controles()
	if c then
		c:Enable()
	end
	pcall(function()
		StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, true)
	end)
end

-- ===== Cámara =====

local giro = 0
local parametros = RaycastParams.new()
parametros.FilterType = Enum.RaycastFilterType.Exclude

-- Posición de la cámara para un giro dado: delante de la cara, desplazada a la derecha (el personaje queda a la
-- izquierda de la pantalla). Devuelve también el foco y el punto de mira.
local function encuadre(raiz: BasePart, angulo: number): (Vector3, Vector3, Vector3, Vector3)
	local c = Config.Camara
	local marco = raiz.CFrame * CFrame.Angles(0, angulo, 0)
	local foco = marco * Vector3.new(0, c.Mira, 0)
	local desde = marco * Vector3.new(0, c.Altura, -c.Distancia)
	local derecha = (foco - desde):Cross(marco.UpVector).Unit
	return desde + derecha * c.Desplazar, foco + derecha * c.Desplazar, foco, marco.UpVector
end

-- Piezas que hay cerca del personaje (a menos de `radio`), visibles. PROBADO EN STUDIO: las piezas decorativas de la
-- región no aceptan consultas (CanQuery desactivado, para que sean baratas), así que ni los rayos ni
-- GetPartsObscuringTarget las ven; se comprueba a mano.
local function piezasCerca(centro: Vector3, radio: number, excluir: Instance): { BasePart }
	local lista = {}
	for _, d in workspace:GetDescendants() do
		if d:IsA("BasePart") and d.Transparency < 0.9 and not d:IsDescendantOf(excluir) and d.Size.Magnitude < 60 then
			if (d.Position - centro).Magnitude < radio + d.Size.Magnitude / 2 then
				table.insert(lista, d)
			end
		end
	end
	return lista
end

-- ¿Atraviesa el segmento de `a` a `b` alguna de las piezas? (muestras a lo largo del segmento dentro de su caja)
local function tapado(a: Vector3, b: Vector3, piezas: { BasePart }): boolean
	for _, p in piezas do
		local medio = p.Size / 2
		for k = 1, 12 do
			local local_ = p.CFrame:PointToObjectSpace(a:Lerp(b, k / 13))
			if math.abs(local_.X) < medio.X and math.abs(local_.Y) < medio.Y and math.abs(local_.Z) < medio.Z then
				return true
			end
		end
	end
	return false
end

-- El giro inicial: el de delante de la cara, o el más cercano a él con la vista despejada hasta la cabeza, el pecho
-- y los pies (PROBADO EN STUDIO: un tronco o un poste se quedaban en medio).
local function giroLibre(raiz: BasePart, personaje: Model): number
	local piezas = piezasCerca(raiz.Position, Config.Camara.Distancia + 4, personaje)
	local arriba = raiz.CFrame.UpVector
	for _, angulo in { 0, 0.4, -0.4, 0.8, -0.8, 1.2, -1.2, 1.6, -1.6, 2.0, -2.0 } do
		local desde = encuadre(raiz, angulo)
		local libre = true
		for _, alto in { 1.8, 0, -2.4 } do
			if tapado(desde, raiz.Position + arriba * alto, piezas) then
				libre = false
				break
			end
		end
		if libre then
			return angulo
		end
	end
	return 0
end

local function empezarCamara()
	jugador:SetAttribute(ConfigGraficos.AtributoCamara, true)
	local c = Config.Camara
	local campoAntes = workspace.CurrentCamera and workspace.CurrentCamera.FieldOfView or 70
	local personajeInicial = jugador.Character
	parametros.FilterDescendantsInstances = { personajeInicial :: Instance }
	local raizInicial = personajeInicial and personajeInicial:FindFirstChild("HumanoidRootPart") :: BasePart?
	giro = if raizInicial and personajeInicial then giroLibre(raizInicial, personajeInicial) else 0
	RunService:BindToRenderStep(PASO_CAMARA, Enum.RenderPriority.Camera.Value + 2, function()
		local camara = workspace.CurrentCamera
		local personaje = jugador.Character
		local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
		if camara == nil or raiz == nil then
			return
		end
		camara.CameraType = Enum.CameraType.Scriptable
		camara.FieldOfView = c.CampoVision
		parametros.FilterDescendantsInstances = { personaje :: Instance }
		local desde, mira, foco, arriba = encuadre(raiz, giro)
		-- Si al girar algo se interpone, la cámara se acerca.
		local golpe = workspace:Raycast(foco, desde - foco, parametros)
		if golpe then
			desde = foco + (desde - foco).Unit * math.max(golpe.Distance - 0.5, 2)
		end
		camara.CFrame = CFrame.lookAt(desde, mira, arriba)
	end)
	-- Arrastrar (ratón o dedo) fuera de la interfaz gira al personaje.
	local arrastrando = false
	table.insert(
		conexiones,
		UserInputService.InputBegan:Connect(function(entrada: InputObject, procesada: boolean)
			if procesada then
				return
			end
			local t = entrada.UserInputType
			if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.Touch then
				arrastrando = true
			end
		end)
	)
	table.insert(
		conexiones,
		UserInputService.InputEnded:Connect(function(entrada: InputObject)
			local t = entrada.UserInputType
			if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.Touch then
				arrastrando = false
			end
		end)
	)
	table.insert(
		conexiones,
		UserInputService.InputChanged:Connect(function(entrada: InputObject)
			local t = entrada.UserInputType
			if arrastrando and (t == Enum.UserInputType.MouseMovement or t == Enum.UserInputType.Touch) then
				giro -= entrada.Delta.X * c.Sensibilidad
			end
		end)
	)
	return campoAntes
end

local function pararCamara(campoAntes: number)
	RunService:UnbindFromRenderStep(PASO_CAMARA)
	for _, conexion in conexiones do
		conexion:Disconnect()
	end
	table.clear(conexiones)
	jugador:SetAttribute(ConfigGraficos.AtributoCamara, nil)
	local camara = workspace.CurrentCamera
	if camara then
		camara.FieldOfView = campoAntes
		local personaje = jugador.Character
		local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
		if not (raiz and raiz:FindFirstChild("PlanetaRedondoAntigravedad")) then
			camara.CameraType = Enum.CameraType.Custom
		end
	end
end

-- ===== Interfaz =====

local function esquina(objeto: GuiObject, radio: number)
	local e = Instance.new("UICorner")
	e.CornerRadius = UDim.new(0, radio)
	e.Parent = objeto
end

local function texto(padre: Instance, props: { [string]: any }): TextLabel
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1
	t.Font = Enum.Font.GothamBold
	t.TextColor3 = color(Config.Colores.Texto)
	t.TextScaled = true
	for k, v in props do
		(t :: any)[k] = v
	end
	t.Parent = padre
	return t
end

local function boton(padre: Instance, props: { [string]: any }): TextButton
	local b = Instance.new("TextButton")
	b.AutoButtonColor = true
	b.Font = Enum.Font.GothamBold
	b.TextScaled = true
	b.TextColor3 = color(Config.Colores.Texto)
	b.BackgroundColor3 = color(Config.Colores.Panel)
	for k, v in props do
		(b :: any)[k] = v
	end
	b.Parent = padre
	esquina(b, 10)
	local relleno = Instance.new("UIPadding")
	relleno.PaddingTop = UDim.new(0.14, 0)
	relleno.PaddingBottom = UDim.new(0.14, 0)
	relleno.PaddingLeft = UDim.new(0.06, 0)
	relleno.PaddingRight = UDim.new(0.06, 0)
	relleno.Parent = b
	return b
end

function Pantalla.Abierta(): boolean
	return gui ~= nil
end

function Pantalla.Abrir(op: Opciones)
	if gui ~= nil then
		return
	end
	local col = Config.Colores
	local actual: { [string]: string } = table.clone(op.Inicial :: any)
	local pestana = Config.Pestanas[1]

	local nueva = Instance.new("ScreenGui")
	nueva.Name = NOMBRE_GUI
	nueva.IgnoreGuiInset = true
	nueva.ResetOnSpawn = false
	nueva.DisplayOrder = 120
	gui = nueva

	texto(nueva, {
		Text = Config.Textos.Titulo,
		Size = UDim2.fromScale(0.4, 0.07),
		Position = UDim2.fromScale(0.03, 0.04),
		TextXAlignment = Enum.TextXAlignment.Left,
	})
	texto(nueva, {
		Text = Config.Textos.Subtitulo,
		Font = Enum.Font.Gotham,
		TextColor3 = color(col.Texto),
		TextStrokeTransparency = 0.35, -- se lee sobre cualquier fondo
		Size = UDim2.fromScale(0.4, 0.032),
		Position = UDim2.fromScale(0.03, 0.115),
		TextXAlignment = Enum.TextXAlignment.Left,
	})

	-- Panel de la derecha: pestañas arriba, opciones debajo.
	local panel = Instance.new("Frame")
	panel.BackgroundColor3 = color(col.Fondo)
	panel.BackgroundTransparency = 0.15
	panel.Size = UDim2.fromScale(0.4, 0.8)
	panel.Position = UDim2.fromScale(0.575, 0.05)
	panel.Parent = nueva
	esquina(panel, 14)

	local barra = Instance.new("Frame")
	barra.BackgroundTransparency = 1
	barra.Size = UDim2.fromScale(0.94, 0.2)
	barra.Position = UDim2.fromScale(0.03, 0.025)
	barra.Parent = panel
	local rejillaPestanas = Instance.new("UIGridLayout")
	rejillaPestanas.CellSize = UDim2.fromScale(0.235, 0.44)
	rejillaPestanas.CellPadding = UDim2.fromScale(0.02, 0.08)
	rejillaPestanas.SortOrder = Enum.SortOrder.LayoutOrder
	rejillaPestanas.Parent = barra

	local zona = Instance.new("ScrollingFrame")
	zona.BackgroundTransparency = 1
	zona.BorderSizePixel = 0
	zona.ScrollBarThickness = 6
	zona.Size = UDim2.fromScale(0.94, 0.72)
	zona.Position = UDim2.fromScale(0.03, 0.25)
	zona.AutomaticCanvasSize = Enum.AutomaticSize.Y
	zona.CanvasSize = UDim2.new()
	zona.Parent = panel
	local rejilla = Instance.new("UIGridLayout")
	rejilla.CellSize = UDim2.new(0.31, 0, 0, 74)
	rejilla.CellPadding = UDim2.new(0.035, 0, 0, 10)
	rejilla.SortOrder = Enum.SortOrder.LayoutOrder
	rejilla.Parent = zona

	local botonesPestana: { [string]: TextButton } = {}
	local pintarOpciones: () -> ()

	local function marcarPestanas()
		for campo, b in botonesPestana do
			b.BackgroundColor3 = if campo == pestana.Campo then color(col.Elegido) else color(col.Panel)
			b.TextColor3 = if campo == pestana.Campo then color(col.Fondo) else color(col.Texto)
		end
	end

	pintarOpciones = function()
		for _, hijo in zona:GetChildren() do
			if hijo:IsA("GuiButton") then
				hijo:Destroy()
			end
		end
		for indice, opcion in Apariencia.Opciones(pestana.Campo) do
			local elegido = actual[pestana.Campo] == opcion.Id
			local b = boton(zona, {
				Name = opcion.Id,
				LayoutOrder = indice,
				Text = if pestana.Colores then "" else opcion.Nombre,
				BackgroundColor3 = if pestana.Colores then color(opcion.Hex) else color(col.Panel),
			})
			local borde = Instance.new("UIStroke")
			borde.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
			borde.Color = if elegido then color(col.Elegido) else color(col.Borde)
			borde.Thickness = if elegido then 3 else 1
			borde.Parent = b
			if pestana.Colores then
				texto(b, {
					Text = opcion.Nombre,
					Size = UDim2.fromScale(1, 0.34),
					Position = UDim2.fromScale(0, 0.66),
					TextStrokeTransparency = 0.3,
				})
			end
			b.Activated:Connect(function()
				actual[pestana.Campo] = opcion.Id
				op.AlCambiar(actual :: any)
				pintarOpciones()
			end)
		end
	end

	for indice, p in Config.Pestanas do
		local b = boton(barra, { Text = p.Nombre, LayoutOrder = indice })
		botonesPestana[p.Campo] = b
		b.Activated:Connect(function()
			pestana = p
			marcarPestanas()
			pintarOpciones()
		end)
	end
	marcarPestanas()
	pintarOpciones()

	local aleatorio = boton(nueva, {
		Text = Config.Textos.Aleatorio,
		Size = UDim2.fromScale(0.15, 0.065),
		Position = UDim2.fromScale(0.6, 0.885),
	})
	local continuar = boton(nueva, {
		Text = Config.Textos.Continuar,
		TextColor3 = color(col.Fondo),
		BackgroundColor3 = color(col.Elegido),
		Size = UDim2.fromScale(0.2, 0.065),
		Position = UDim2.fromScale(0.77, 0.885),
	})
	local azar = Random.new()
	aleatorio.Activated:Connect(function()
		actual = Apariencia.Aleatoria(azar) :: any
		op.AlCambiar(actual :: any)
		pintarOpciones()
	end)

	bloquear()
	local campoAntes = empezarCamara()
	nueva.Parent = jugador:WaitForChild("PlayerGui")
	op.AlCambiar(actual :: any)

	continuar.Activated:Connect(function()
		if gui ~= nueva then
			return
		end
		gui = nil
		nueva:Destroy()
		pararCamara(campoAntes)
		desbloquear()
		op.AlTerminar(actual :: any)
	end)
end

return Pantalla
