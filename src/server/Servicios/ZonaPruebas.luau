--!strict
--[[
	ZonaPruebas: una plataforma de entrenamiento para probar el combate sin tener que montar un mapa.

	Al arrancar el servidor crea (en el Workspace):
	  - una plataforma amplia con muros bajos y columnas (para ver los escombros y los cráteres),
	  - un punto de aparición (SpawnLocation) en ella,
	  - tres muñecos de entrenamiento: uno de los Héroes, uno de los Villanos y uno sin bando.
	    Sirven para comprobar que los del mismo bando no se hacen daño, y renacen solos al "morir".
	  - dos pedestales "Unirse a Héroes / Villanos" (ProximityPrompt) para elegir bando sin interfaz.
	  - un cartel con los controles.

	Se desactiva quitando la llamada a ZonaPruebas.Iniciar() en init.server. Todo se crea por código, no hay
	nada que montar a mano en Studio.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local Bandos = require(Shared.Juego.Bandos)
local Config = require(Shared.Combate.Config)
local ServicioBandos = require(script.Parent.ServicioBandos)
local ServicioCombate = require(script.Parent.ServicioCombate)

local ZonaPruebas = {}

-- Centro de la plataforma y su tamaño.
local CENTRO = Vector3.new(0, 0, 0)
local TAMANO = Vector3.new(220, 2, 220)

local carpeta: Folder? = nil

local function crearParte(nombre: string, tamano: Vector3, posicion: Vector3, color: Color3, material: Enum.Material)
	local parte = Instance.new("Part")
	parte.Name = nombre
	parte.Size = tamano
	parte.Position = posicion
	parte.Color = color
	parte.Material = material
	parte.Anchored = true
	parte.TopSurface = Enum.SurfaceType.Smooth
	parte.BottomSurface = Enum.SurfaceType.Smooth
	return parte
end

-- Cartel flotante con texto (BillboardGui).
local function crearCartel(padre: Instance, texto: string, posicion: Vector3, ancho: number, alto: number)
	local ancla = crearParte("Cartel", Vector3.new(1, 1, 1), posicion, Color3.new(), Enum.Material.SmoothPlastic)
	ancla.Transparency = 1
	ancla.CanCollide = false
	ancla.CanQuery = false
	ancla.Parent = padre

	local gui = Instance.new("BillboardGui")
	gui.Size = UDim2.fromOffset(ancho, alto)
	gui.AlwaysOnTop = false
	gui.MaxDistance = 140
	gui.Parent = ancla

	local etiqueta = Instance.new("TextLabel")
	etiqueta.Size = UDim2.fromScale(1, 1)
	etiqueta.BackgroundColor3 = Color3.fromRGB(12, 14, 26)
	etiqueta.BackgroundTransparency = 0.25
	etiqueta.TextColor3 = Color3.fromRGB(235, 240, 255)
	etiqueta.TextScaled = true
	etiqueta.Font = Enum.Font.GothamMedium
	etiqueta.Text = texto
	etiqueta.Parent = gui
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, 8)
	esquina.Parent = etiqueta
end

-- Muñeco con aspecto de personaje R6 (si el motor lo permite) o, si no, una figura sencilla.
local function crearModeloMunieco(nombre: string, posicion: Vector3, color: Color3): Model
	local modelo: Model? = nil
	local ok, resultado = pcall(function()
		return Players:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R6)
	end)
	if ok and resultado then
		modelo = resultado
	end

	if modelo == nil then
		-- Plan B: cuerpo mínimo con Humanoid (suficiente para recibir daño).
		modelo = Instance.new("Model")
		local raiz =
			crearParte("HumanoidRootPart", Vector3.new(2, 2, 1), Vector3.zero, color, Enum.Material.SmoothPlastic)
		raiz.Parent = modelo
		local cabeza =
			crearParte("Head", Vector3.new(1.4, 1.4, 1.4), Vector3.new(0, 2, 0), color, Enum.Material.SmoothPlastic)
		cabeza.Parent = modelo
		local soldadura = Instance.new("WeldConstraint")
		soldadura.Part0 = raiz
		soldadura.Part1 = cabeza
		soldadura.Parent = raiz
		local humanoid = Instance.new("Humanoid")
		humanoid.Parent = modelo
		modelo.PrimaryPart = raiz
	end

	local model = modelo :: Model
	model.Name = nombre
	for _, parte in model:GetDescendants() do
		if parte:IsA("BasePart") then
			parte.Color = color
			parte.Material = Enum.Material.SmoothPlastic
		end
	end
	local raiz = model:FindFirstChild("HumanoidRootPart") :: BasePart
	raiz.Anchored = true -- el muñeco no se mueve ni sale volando
	model:PivotTo(CFrame.new(posicion + Vector3.new(0, 3.2, 0)) * CFrame.Angles(0, math.pi, 0))
	return model
end

-- Crea un muñeco y lo registra como objetivo. Cuando "muere" vuelve a aparecer.
local function crearMunieco(padre: Instance, nombre: string, bando: string, posicion: Vector3, color: Color3)
	local function aparecer()
		local modelo = crearModeloMunieco(nombre, posicion, color)
		local humanoid = modelo:FindFirstChildOfClass("Humanoid") :: Humanoid
		humanoid.DisplayName = `{nombre} ({Bandos.Info[bando].Nombre})`
		humanoid.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOn
		humanoid.NameDisplayDistance = 80
		humanoid.HealthDisplayDistance = 80
		modelo.Parent = padre
		ServicioCombate.RegistrarMunieco(modelo, bando)

		humanoid.Died:Once(function()
			task.delay(Config.SegundosRenacerMunieco, function()
				modelo:Destroy()
				aparecer()
			end)
		end)
	end
	aparecer()
end

-- Pedestal con un ProximityPrompt para elegir bando.
local function crearPedestal(padre: Instance, bando: Bandos.IdBando, posicion: Vector3, color: Color3)
	local base = crearParte(`Pedestal{bando}`, Vector3.new(8, 1, 8), posicion, color, Enum.Material.Neon)
	base.Parent = padre

	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText = `Unirse a {Bandos.Info[bando].Nombre}`
	prompt.ObjectText = "Elegir bando"
	prompt.HoldDuration = 0.4
	prompt.MaxActivationDistance = 12
	prompt.Parent = base
	prompt.Triggered:Connect(function(jugador)
		ServicioBandos.Elegir(jugador, bando)
	end)

	crearCartel(padre, Bandos.Info[bando].Nombre, posicion + Vector3.new(0, 6, 0), 160, 40)
end

-- Crea la zona de pruebas. Debe llamarse una sola vez, después de ServicioCombate.Iniciar().
function ZonaPruebas.Iniciar()
	assert(carpeta == nil, "ZonaPruebas.Iniciar() solo debe llamarse una vez")
	local zona = Instance.new("Folder")
	zona.Name = "ZonaDePruebas"
	carpeta = zona

	-- Suelo y muros: arena oscura para que los efectos brillantes destaquen.
	local suelo =
		crearParte("Suelo", TAMANO, CENTRO - Vector3.new(0, 1, 0), Color3.fromRGB(58, 56, 66), Enum.Material.Slate)
	suelo.Parent = zona
	local muroColor = Color3.fromRGB(38, 36, 46)
	local mitad = TAMANO.X / 2
	for indice, desplazamiento in
		{ Vector3.new(0, 0, mitad), Vector3.new(0, 0, -mitad), Vector3.new(mitad, 0, 0), Vector3.new(-mitad, 0, 0) }
	do
		local largo = if desplazamiento.X == 0 then Vector3.new(TAMANO.X, 8, 2) else Vector3.new(2, 8, TAMANO.Z)
		crearParte(`Muro{indice}`, largo, desplazamiento + Vector3.new(0, 3, 0), muroColor, Enum.Material.Concrete).Parent =
			zona
	end

	-- Columnas para ver cómo reaccionan los rayos y los escombros.
	for indice = 1, 6 do
		local angulo = (indice / 6) * math.pi * 2
		local posicion = CENTRO + Vector3.new(math.cos(angulo) * 70, 8, math.sin(angulo) * 70 - 20)
		crearParte(`Columna{indice}`, Vector3.new(6, 16, 6), posicion, Color3.fromRGB(80, 78, 92), Enum.Material.Marble).Parent =
			zona
	end

	-- Punto de aparición: Duration = 0 para que no tengan escudo (ForceField) al aparecer.
	local aparicion = Instance.new("SpawnLocation")
	aparicion.Size = Vector3.new(10, 1, 10)
	aparicion.Position = CENTRO + Vector3.new(0, 0.5, 60)
	aparicion.Anchored = true
	aparicion.Duration = 0
	aparicion.Neutral = true
	aparicion.Color = Color3.fromRGB(90, 200, 255)
	aparicion.Material = Enum.Material.Neon
	aparicion.Parent = zona

	crearPedestal(zona, Bandos.Heroes, CENTRO + Vector3.new(-14, 0.5, 52), Color3.fromRGB(70, 140, 255))
	crearPedestal(zona, Bandos.Villanos, CENTRO + Vector3.new(14, 0.5, 52), Color3.fromRGB(230, 70, 80))

	crearCartel(
		zona,
		"ZONA DE PRUEBAS · Click: combo · Z X C: Rayo · V B N: Gravedad",
		CENTRO + Vector3.new(0, 14, 30),
		460,
		44
	)

	zona.Parent = workspace

	-- Los muñecos se crean aparte: CreateHumanoidModelFromDescription espera a Roblox y no debe retrasar el arranque.
	task.spawn(function()
		crearMunieco(zona, "Muñeco Héroe", "Heroes", CENTRO + Vector3.new(-26, 0, 0), Color3.fromRGB(70, 140, 255))
		crearMunieco(zona, "Muñeco Neutral", "Ninguno", CENTRO + Vector3.new(0, 0, -6), Color3.fromRGB(190, 190, 200))
		crearMunieco(zona, "Muñeco Villano", "Villanos", CENTRO + Vector3.new(26, 0, 0), Color3.fromRGB(230, 70, 80))
	end)
end

return ZonaPruebas
