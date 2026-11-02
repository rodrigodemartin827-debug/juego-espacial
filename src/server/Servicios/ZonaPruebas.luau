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
	  - un HANGAR con una nave para despegar (consola "Despegar") y, a unos cientos de studs, un pequeño CAMPO DE
	    ASTEROIDES generado por código para probar el vuelo, las armas y los choques.
	  - una ZONA DE EXPLORACIÓN: rocas de mineral para picar (R), una criatura (medusa del vacío) y dos plantas para
	    escanear (Q), y una mesa de crafteo (E) donde fabricar componentes y mejoras de la nave. Los asteroides del campo
	    llevan además vetas de mineral que los láseres de la nave pueden picar.
	  - un ambiente nocturno con resplandor (bloom) para que se vean bien los efectos luminosos.

	Se desactiva quitando la llamada a ZonaPruebas.Iniciar() en init.server. Todo se crea por código, no hay
	nada que montar a mano en Studio.
]]

local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local Bandos = require(Shared.Juego.Bandos)
local Config = require(Shared.Combate.Config)
local Hangar = require(script.Parent.Hangar)
local ServicioAsteroides = require(script.Parent.ServicioAsteroides)
local ServicioBandos = require(script.Parent.ServicioBandos)
local ServicioCombate = require(script.Parent.ServicioCombate)
local ServicioCrafteo = require(script.Parent.ServicioCrafteo)
local ServicioEscaner = require(script.Parent.ServicioEscaner)
local ServicioMinado = require(script.Parent.ServicioMinado)

local ZonaPruebas = {}

-- Centro de la plataforma y su tamaño.
local CENTRO = Vector3.new(0, 0, 0)
local TAMANO = Vector3.new(220, 2, 220)

-- Dónde está el hangar y el campo de asteroides de pruebas (relativos al centro de la plataforma).
local POSICION_HANGAR = Vector3.new(75, 0, 62)
local CENTRO_CAMPO = Vector3.new(0, 130, -270)
local RADIO_CAMPO = 140

-- Zona de exploración (relativa al centro de la plataforma): rocas de mineral, bichos y plantas, y la mesa de crafteo.
local POSICION_MINAS = Vector3.new(-72, 0, 38)
local POSICION_CRIATURA = Vector3.new(-50, 0, -44)
local POSICION_MESA = Vector3.new(-38, 0, 68)

-- true = ambiente nocturno con bloom, que hace destacar láseres, explosiones y propulsores.
local AMBIENTE_ESPACIAL = true

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

-- Noche cerrada con un poco de luz ambiente, resplandor en lo que brilla y algo de contraste.
local function ambientarEspacio()
	Lighting.ClockTime = 0
	Lighting.Ambient = Color3.fromRGB(38, 42, 68)
	Lighting.OutdoorAmbient = Color3.fromRGB(46, 52, 86)
	Lighting.ExposureCompensation = 0.25
	Lighting.EnvironmentDiffuseScale = 0.6
	Lighting.EnvironmentSpecularScale = 0.8

	local resplandor = Instance.new("BloomEffect")
	resplandor.Name = "ResplandorEspacial"
	resplandor.Intensity = 0.75
	resplandor.Size = 30
	resplandor.Threshold = 0.85
	resplandor.Parent = Lighting

	local color = Instance.new("ColorCorrectionEffect")
	color.Name = "ColorEspacial"
	color.Contrast = 0.12
	color.Saturation = 0.18
	color.Parent = Lighting
end

-- Campo de asteroides de pruebas, con una baliza luminosa en un claro y un cartel que indica el camino.
local function crearCampoDePruebas(zona: Folder)
	ServicioAsteroides.CrearCampo({
		Nombre = "CampoDePruebas",
		Semilla = 20241102,
		Cantidad = 70,
		Centro = CENTRO_CAMPO,
		Radio = RADIO_CAMPO,
		Aplanado = 0.8,
		TamanoMin = 6,
		TamanoMax = 30,
		Separacion = 14,
		-- Un claro en el centro, donde está la baliza.
		Exclusiones = { { Centro = CENTRO_CAMPO, Radio = 34 } },
		-- Un tercio de los asteroides lleva una veta de mineral que los láseres de la nave pueden picar.
		ProbabilidadVeta = 0.35,
	})

	local baliza = crearParte("Baliza", Vector3.one * 6, CENTRO_CAMPO, Color3.fromRGB(77, 240, 255), Enum.Material.Neon)
	baliza.Shape = Enum.PartType.Ball
	baliza.CanCollide = false
	baliza.Parent = zona
	local luz = Instance.new("PointLight")
	luz.Color = baliza.Color
	luz.Range = 60
	luz.Brightness = 3
	luz.Parent = baliza
	crearCartel(zona, "CAMPO DE ASTEROIDES", CENTRO_CAMPO + Vector3.new(0, 12, 0), 360, 44)

	-- Una señal a la salida del hangar, para saber hacia dónde volar.
	crearCartel(zona, "↑ Campo de asteroides al norte (−Z)", CENTRO + Vector3.new(60, 30, -40), 440, 40)
end

-- Roca de mineral para picar: unas cuantas en un corro, de distintos tipos y tamaños.
local function crearZonaMinera(zona: Folder)
	local rocas = {
		{ Tipo = "Hierro", Desplazamiento = Vector3.new(0, 0, 0), Tamano = 7 },
		{ Tipo = "Hierro", Desplazamiento = Vector3.new(11, 0, 6), Tamano = 5 },
		{ Tipo = "Cobre", Desplazamiento = Vector3.new(-10, 0, 7), Tamano = 6 },
		{ Tipo = "Cobre", Desplazamiento = Vector3.new(6, 0, -11), Tamano = 5 },
		{ Tipo = "Cristal", Desplazamiento = Vector3.new(-9, 0, -9), Tamano = 5 },
		{ Tipo = "Cristal", Desplazamiento = Vector3.new(17, 0, -4), Tamano = 4 },
	}
	for _, roca in rocas do
		-- La roca (una esfera de 0,8 × tamaño) se apoya en el suelo.
		local posicion = POSICION_MINAS + roca.Desplazamiento + Vector3.new(0, roca.Tamano * 0.4, 0)
		ServicioMinado.CrearNodo(roca.Tipo, CFrame.new(posicion), roca.Tamano).Parent = zona
	end
	crearCartel(
		zona,
		"ZONA DE MINERÍA · Mantén R para picar · Q para escanear",
		POSICION_MINAS + Vector3.new(0, 16, 0),
		440,
		40
	)
end

-- Medusa del vacío: una criatura flotante y escaneable, hecha con partes sencillas.
local function crearMedusa(zona: Folder)
	local base = POSICION_CRIATURA + Vector3.new(0, 8, 0)
	local medusa = Instance.new("Model")
	medusa.Name = "MedusaDelVacio"

	local cuerpo = crearParte("Cuerpo", Vector3.one * 5.5, base, Color3.fromRGB(190, 150, 255), Enum.Material.Neon)
	cuerpo.Shape = Enum.PartType.Ball
	cuerpo.Transparency = 0.35
	cuerpo.CanCollide = false
	cuerpo.Parent = medusa
	medusa.PrimaryPart = cuerpo

	local nucleo = crearParte("Nucleo", Vector3.one * 2.2, base, Color3.fromRGB(255, 255, 255), Enum.Material.Neon)
	nucleo.Shape = Enum.PartType.Ball
	nucleo.CanCollide = false
	nucleo.Parent = medusa
	local luz = Instance.new("PointLight")
	luz.Color = Color3.fromRGB(190, 150, 255)
	luz.Range = 22
	luz.Brightness = 2
	luz.Parent = nucleo

	-- Tentáculos colgando.
	for indice = 1, 6 do
		local angulo = (indice / 6) * math.pi * 2
		local tentaculo = crearParte(
			`Tentaculo{indice}`,
			Vector3.new(0.45, 5, 0.45),
			base + Vector3.new(math.cos(angulo) * 1.9, -4.2, math.sin(angulo) * 1.9),
			Color3.fromRGB(150, 110, 230),
			Enum.Material.Neon
		)
		tentaculo.Transparency = 0.4
		tentaculo.CanCollide = false
		tentaculo.Parent = medusa
	end

	medusa.Parent = zona
	ServicioEscaner.Marcar(medusa, "Criatura_MedusaVacio")

	-- Flota arriba y abajo girando despacio. Se mueve unas 15 veces por segundo: de sobra para un adorno.
	task.spawn(function()
		local origen = medusa:GetPivot()
		local inicio = os.clock()
		while medusa.Parent ~= nil do
			local t = os.clock() - inicio
			medusa:PivotTo(origen * CFrame.new(0, math.sin(t * 1.4) * 1.2, 0) * CFrame.Angles(0, t * 0.3, 0))
			task.wait(0.07)
		end
	end)

	crearCartel(zona, "CRIATURA · mantén Q para escanear", base + Vector3.new(0, 8, 0), 330, 36)
end

-- Una planta luminosa: tallo, pétalos de neón y una luz. `tipo` es "Flor" u "Hongo".
local function crearPlanta(
	zona: Folder,
	nombre: string,
	especie: string,
	posicion: Vector3,
	color: Color3,
	tipo: string
)
	local planta = Instance.new("Model")
	planta.Name = nombre

	local altura = if tipo == "Flor" then 3.2 else 1.6
	local tallo = crearParte(
		"Tallo",
		Vector3.new(0.4, altura, 0.4),
		posicion + Vector3.new(0, altura / 2, 0),
		Color3.fromRGB(70, 130, 80),
		Enum.Material.Grass
	)
	tallo.CanCollide = false
	tallo.Parent = planta
	planta.PrimaryPart = tallo

	if tipo == "Flor" then
		for indice = 1, 6 do
			local angulo = (indice / 6) * math.pi * 2
			local petalo = crearParte(
				`Petalo{indice}`,
				Vector3.new(0.5, 0.2, 1.3),
				posicion + Vector3.new(math.cos(angulo) * 0.9, altura + 0.1, math.sin(angulo) * 0.9),
				color,
				Enum.Material.Neon
			)
			petalo.CFrame = CFrame.lookAt(petalo.Position, posicion + Vector3.new(0, altura + 0.1, 0))
			petalo.CanCollide = false
			petalo.Parent = planta
		end
	else
		local sombrero = crearParte(
			"Sombrero",
			Vector3.new(2.6, 1.1, 2.6),
			posicion + Vector3.new(0, altura + 0.3, 0),
			color,
			Enum.Material.Neon
		)
		sombrero.Shape = Enum.PartType.Ball
		sombrero.CanCollide = false
		sombrero.Parent = planta
	end

	local luz = Instance.new("PointLight")
	luz.Color = color
	luz.Range = 12
	luz.Brightness = 1.5
	luz.Parent = tallo

	planta.Parent = zona
	ServicioEscaner.Marcar(planta, especie)
end

-- La mesa de crafteo y su cartel.
local function crearMesa(zona: Folder)
	ServicioCrafteo.CrearMesa(zona, POSICION_MESA)
	crearCartel(zona, "MESA DE CRAFTEO · acércate y pulsa E", POSICION_MESA + Vector3.new(0, 9, 0), 380, 36)
end

-- Todo lo de la exploración: minerales, criatura, plantas y mesa de crafteo.
local function crearZonaExploracion(zona: Folder)
	crearZonaMinera(zona)
	crearMedusa(zona)
	crearPlanta(
		zona,
		"FlorEstelar",
		"Planta_FlorEstelar",
		POSICION_CRIATURA + Vector3.new(-14, 0, 6),
		Color3.fromRGB(255, 160, 220),
		"Flor"
	)
	crearPlanta(
		zona,
		"HongoLuminoso",
		"Planta_HongoLuminoso",
		POSICION_CRIATURA + Vector3.new(-9, 0, 14),
		Color3.fromRGB(120, 255, 200),
		"Hongo"
	)
	crearMesa(zona)
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

	-- Naves: el hangar y el campo de asteroides.
	Hangar.Crear(zona, CENTRO + POSICION_HANGAR)
	crearCampoDePruebas(zona)
	crearZonaExploracion(zona)
	if AMBIENTE_ESPACIAL then
		ambientarEspacio()
	end

	zona.Parent = workspace

	-- Los muñecos se crean aparte: CreateHumanoidModelFromDescription espera a Roblox y no debe retrasar el arranque.
	task.spawn(function()
		crearMunieco(zona, "Muñeco Héroe", "Heroes", CENTRO + Vector3.new(-26, 0, 0), Color3.fromRGB(70, 140, 255))
		crearMunieco(zona, "Muñeco Neutral", "Ninguno", CENTRO + Vector3.new(0, 0, -6), Color3.fromRGB(190, 190, 200))
		crearMunieco(zona, "Muñeco Villano", "Villanos", CENTRO + Vector3.new(26, 0, 0), Color3.fromRGB(230, 70, 80))
	end)
end

return ZonaPruebas
