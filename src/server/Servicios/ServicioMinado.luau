--!strict
--[[
	ServicioMinado: los minerales que se pueden picar, en planetas y en asteroides, a pie o desde la nave.

	Un NODO es un Model o una Part etiquetado "Mineral" con el atributo MineralTipo (id de Exploracion/Datos/Minerales) y
	la vida que le queda (MineralVida). Hay dos formas de golpearlo:

	  - A pie: el jugador pulsa la tecla de picar y el cliente pide `PicarMineral`. El servidor comprueba que el nodo
	    exista, que el jugador esté vivo, a pie y cerca, la cadencia del pico y que le quepa el botín en la bodega.
	  - Desde la nave: los láseres que dan en un nodo (ServicioNaves) llaman a `PicarDesdeNave`. Ahí ya valen las
	    comprobaciones de disparo de la nave (cadencia, cono, alcance).

	Cuando un nodo se agota suelta su botín en el inventario de quien lo rompió (ServicioInventario), se oculta y reaparece
	a los Config.SegundosRenacerMineral. Mientras está oculto no se puede golpear ni escanear.

	`CrearNodo` construye el modelo de una roca con su veta de color; lo usan la zona de pruebas (rocas del suelo) y los
	asteroides (vetas pegadas a la roca).
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local Config = require(Shared.Exploracion.Config)
local Especies = require(Shared.Exploracion.Datos.Especies)
local Minerales = require(Shared.Exploracion.Datos.Minerales)
local Objetos = require(Shared.Exploracion.Datos.Objetos)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioInventario = require(script.Parent.ServicioInventario)
local ServicioRed = require(script.Parent.ServicioRed)

local ServicioMinado = {}

local azar = Random.new()

-- Último golpe de pico de cada jugador (os.clock), para respetar la cadencia.
local ultimoGolpe: { [Player]: number } = setmetatable({}, { __mode = "k" }) :: any

-- Estado original de las partes de un nodo, para volver a mostrarlo al reaparecer.
type EstadoParte = { Transparencia: number, Colisiona: boolean, Consulta: boolean }
local originales: { [BasePart]: EstadoParte } = setmetatable({}, { __mode = "k" }) :: any

-- ===== Utilidades =====

local function color(hex: string): Color3
	local r, g, b = string.match(hex, "^#?(%x%x)(%x%x)(%x%x)$")
	if r == nil then
		return Color3.new(1, 1, 1)
	end
	return Color3.fromRGB(tonumber(r, 16) :: number, tonumber(g, 16) :: number, tonumber(b, 16) :: number)
end

local function material(nombre: string): Enum.Material
	local ok, valor = pcall(function()
		return (Enum.Material :: any)[nombre]
	end)
	if ok and valor ~= nil then
		return valor :: Enum.Material
	end
	return Enum.Material.Slate
end

-- Las partes de un nodo (él mismo, si es una parte).
local function partesDe(nodo: Instance): { BasePart }
	local partes: { BasePart } = {}
	if nodo:IsA("BasePart") then
		table.insert(partes, nodo)
	end
	for _, hijo in nodo:GetDescendants() do
		if hijo:IsA("BasePart") then
			table.insert(partes, hijo)
		end
	end
	return partes
end

-- Centro y radio aproximado de un nodo.
local function medida(nodo: Instance): (Vector3, number)
	if nodo:IsA("Model") then
		local marco, tamano = nodo:GetBoundingBox()
		return marco.Position, math.max(tamano.X, tamano.Y, tamano.Z) / 2
	elseif nodo:IsA("BasePart") then
		return nodo.Position, math.max(nodo.Size.X, nodo.Size.Y, nodo.Size.Z) / 2
	end
	return Vector3.zero, 0
end

local function ocultar(nodo: Instance)
	for _, parte in partesDe(nodo) do
		if originales[parte] == nil then
			originales[parte] =
				{ Transparencia = parte.Transparency, Colisiona = parte.CanCollide, Consulta = parte.CanQuery }
		end
		parte.Transparency = 1
		parte.CanCollide = false
		parte.CanQuery = false -- los raycasts (láseres de la nave, escáner) pasan de largo
	end
	for _, hijo in nodo:GetDescendants() do
		if hijo:IsA("Light") then
			hijo.Enabled = false
		end
	end
end

local function mostrar(nodo: Instance)
	for _, parte in partesDe(nodo) do
		local estado = originales[parte]
		if estado then
			parte.Transparency = estado.Transparencia
			parte.CanCollide = estado.Colisiona
			parte.CanQuery = estado.Consulta
		end
	end
	for _, hijo in nodo:GetDescendants() do
		if hijo:IsA("Light") then
			hijo.Enabled = true
		end
	end
end

-- ===== Nodos =====

-- Prepara una instancia ya construida como nodo de mineral: etiqueta, atributos y escaneable.
function ServicioMinado.Registrar(nodo: Instance, tipo: string)
	local mineral = Minerales.Lista[tipo]
	assert(mineral ~= nil, `Mineral desconocido: '{tipo}'`)
	nodo:SetAttribute(Config.AtributoMineralTipo, tipo)
	nodo:SetAttribute(Config.AtributoMineralVida, mineral.Vida)
	nodo:SetAttribute(Config.AtributoMineralAgotado, false)
	nodo:SetAttribute(Config.AtributoEspecie, Especies.IdDeMineral(tipo))
	CollectionService:AddTag(nodo, Config.EtiquetaMineral)
	CollectionService:AddTag(nodo, Config.EtiquetaEscaneable)
end

--[[
	Construye un nodo de mineral: una roca con cristales o vetas del color del mineral, ya registrado.
	  tipo      id de Datos/Minerales
	  marco     dónde y cómo se coloca (el centro de la roca)
	  tamano    diámetro aproximado en studs
	El llamador lo pone en el Workspace (o dentro de un asteroide).
]]
function ServicioMinado.CrearNodo(tipo: string, marco: CFrame, tamano: number): Model
	local mineral = Minerales.Lista[tipo]
	assert(mineral ~= nil, `Mineral desconocido: '{tipo}'`)
	local colorMineral = color(mineral.Color)
	local materialMineral = material(mineral.Material)
	local semilla = Random.new(math.floor(marco.X * 7 + marco.Y * 13 + marco.Z * 17) + #tipo)

	local modelo = Instance.new("Model")
	modelo.Name = `Mineral{tipo}`

	-- La roca de base, más oscura que el mineral.
	local nucleo = Instance.new("Part")
	nucleo.Name = "Roca"
	nucleo.Shape = Enum.PartType.Ball
	nucleo.Size = Vector3.one * tamano * 0.8
	nucleo.CFrame = marco
	nucleo.Color = colorMineral:Lerp(Color3.fromRGB(50, 46, 52), 0.55)
	nucleo.Material = Enum.Material.Slate
	nucleo.Anchored = true
	nucleo.CanTouch = false
	nucleo.Parent = modelo
	modelo.PrimaryPart = nucleo

	-- Las vetas: bloques inclinados que sobresalen de la roca, del color (y brillo) del mineral.
	for numero = 1, 5 do
		local veta = Instance.new("Part")
		veta.Name = `Veta{numero}`
		local largo = tamano * semilla:NextNumber(0.35, 0.6)
		veta.Size = Vector3.new(largo * 0.35, largo, largo * 0.35)
		local direccion =
			Vector3.new(semilla:NextNumber(-1, 1), semilla:NextNumber(0.1, 1), semilla:NextNumber(-1, 1)).Unit
		veta.CFrame = marco
			* CFrame.lookAt(direccion * tamano * 0.38, direccion * tamano * 2) -- sale hacia fuera
			* CFrame.Angles(math.pi / 2, 0, 0)
		veta.Color = colorMineral
		veta.Material = if mineral.Brillo > 0 then Enum.Material.Neon else materialMineral
		veta.Anchored = true
		veta.CanTouch = false
		veta.Parent = modelo
	end

	if mineral.Brillo > 0 then
		local luz = Instance.new("PointLight")
		luz.Color = colorMineral
		luz.Brightness = mineral.Brillo * 2
		luz.Range = math.clamp(tamano * 2.5, 8, 24)
		luz.Parent = nucleo
	end

	ServicioMinado.Registrar(modelo, tipo)
	return modelo
end

-- El nodo de mineral al que pertenece una instancia (ella misma o un antepasado), o nil.
function ServicioMinado.NodoDe(instancia: Instance): Instance?
	local actual: Instance? = instancia
	while actual ~= nil and actual ~= workspace do
		if CollectionService:HasTag(actual, Config.EtiquetaMineral) then
			return actual
		end
		actual = actual.Parent
	end
	return nil
end

-- ¿Se puede golpear ahora? (existe, está en el mundo y no está agotado)
local function disponible(nodo: Instance): boolean
	return nodo.Parent ~= nil
		and nodo:IsDescendantOf(workspace)
		and nodo:GetAttribute(Config.AtributoMineralAgotado) ~= true
		and Minerales.Lista[nodo:GetAttribute(Config.AtributoMineralTipo) :: any] ~= nil
end

-- ===== Golpear y romper =====

-- Reaparición de un nodo agotado.
local function reaparecer(nodo: Instance)
	if nodo.Parent == nil then
		return -- el asteroide que lo llevaba estalló: el nodo ya no existe
	end
	local mineral = Minerales.Lista[nodo:GetAttribute(Config.AtributoMineralTipo) :: any]
	if mineral == nil then
		return
	end
	nodo:SetAttribute(Config.AtributoMineralVida, mineral.Vida)
	nodo:SetAttribute(Config.AtributoMineralAgotado, false)
	mostrar(nodo)
end

-- Reparte el botín de un nodo roto a quien lo rompió. Devuelve las unidades recibidas y las que no cupieron.
local function repartirBotin(jugador: Player, mineral: Minerales.Mineral): (number, number)
	local total = azar:NextInteger(mineral.Cantidad[1], mineral.Cantidad[2])
	local recibidas = ServicioInventario.Anadir(jugador, mineral.Objeto, total)
	return recibidas, total - recibidas
end

local function avisar(jugador: Player, texto: string, tono: string)
	ServicioRed.EnviarACliente(jugador, "AvisoExploracion", texto, tono)
end

--[[
	Quita `dano` de vida al nodo y, si se agota, entrega el botín a `jugador`. Devuelve true si el golpe se aplicó (false
	si no se puede golpear: agotado, o sin sitio en la bodega para llevarse nada).
]]
local function golpear(jugador: Player, nodo: Instance, dano: number): boolean
	if dano ~= dano or dano <= 0 or not disponible(nodo) then
		return false
	end
	local tipo = nodo:GetAttribute(Config.AtributoMineralTipo) :: string
	local mineral = Minerales.Lista[tipo]

	-- Con la bodega llena no se rompe nada: se perdería el botín. Se avisa y se deja el mineral como está.
	if ServicioInventario.CuantoCabe(jugador, mineral.Objeto) < 1 then
		avisar(jugador, "Bodega llena: libera espacio o mejora la Carga", "Mal")
		return false
	end

	local vidaActual = nodo:GetAttribute(Config.AtributoMineralVida)
	local vida = (if type(vidaActual) == "number" then vidaActual else mineral.Vida) - dano
	local centro = medida(nodo)

	if vida > 0 then
		nodo:SetAttribute(Config.AtributoMineralVida, vida)
		ServicioRed.EnviarATodos("MineralGolpeado", centro, tipo, vida / mineral.Vida)
		return true
	end

	-- Roto.
	nodo:SetAttribute(Config.AtributoMineralVida, 0)
	nodo:SetAttribute(Config.AtributoMineralAgotado, true)
	local recibidas, perdidas = repartirBotin(jugador, mineral)
	ServicioRed.EnviarATodos("MineralRoto", centro, tipo)
	local nombre = Objetos.Lista[mineral.Objeto].Nombre
	if perdidas > 0 then
		avisar(jugador, `+{recibidas} {nombre} (la bodega se llenó: {perdidas} perdidas)`, "Info")
	else
		avisar(jugador, `+{recibidas} {nombre}`, "Bien")
	end
	ocultar(nodo)
	task.delay(Config.SegundosRenacerMineral, reaparecer, nodo)
	return true
end

-- Daño de un golpe de pico del jugador (crece un poco con su nivel).
function ServicioMinado.DanoPico(jugador: Player): number
	local datos = ServicioDatos.ObtenerDatos(jugador)
	local nivel = if datos then datos.Nivel else 1
	return Config.DanoPicadoBase + Config.DanoPicadoPorNivelJugador * (nivel - 1)
end

--[[
	Un jugador pica un nodo con el pico (petición del cliente: no se fía de nada). Comprueba que el nodo sea de verdad
	un mineral disponible, que el jugador esté vivo, a pie y a tiro, y la cadencia del pico.
]]
function ServicioMinado.Picar(jugador: Player, instancia: Instance)
	local nodo = ServicioMinado.NodoDe(instancia)
	if nodo == nil or not disponible(nodo) then
		return
	end
	local personaje = jugador.Character
	local humanoid = if personaje then personaje:FindFirstChildOfClass("Humanoid") else nil
	local raiz = if personaje then personaje:FindFirstChild("HumanoidRootPart") else nil
	if personaje == nil or humanoid == nil or humanoid.Health <= 0 or raiz == nil or not raiz:IsA("BasePart") then
		return
	end
	if personaje:GetAttribute(Config.AtributoPilotando) == true then
		return -- dentro de la nave se mina con los láseres
	end
	if ServicioDatos.ObtenerDatos(jugador) == nil then
		return
	end

	-- Distancia hasta la superficie del nodo, no hasta su centro.
	local centro, radio = medida(nodo)
	local distancia = ((raiz :: BasePart).Position - centro).Magnitude - radio
	if distancia > Config.AlcancePicado * Config.HolguraAlcance then
		return
	end

	-- Cadencia del pico.
	local ahora = os.clock()
	if ahora - (ultimoGolpe[jugador] or -math.huge) < Config.CadenciaPicado * 0.85 then
		return
	end
	ultimoGolpe[jugador] = ahora

	golpear(jugador, nodo, ServicioMinado.DanoPico(jugador))
end

--[[
	Un láser de la nave de `jugador` ha dado en el nodo. `danoArma` es el daño del arma; el mineral lo recibe multiplicado por
	Config.DanoNaveMineralFactor. Devuelve true si el nodo era minable y se golpeó.
]]
function ServicioMinado.PicarDesdeNave(jugador: Player, instancia: Instance, danoArma: number): boolean
	local nodo = ServicioMinado.NodoDe(instancia)
	if nodo == nil then
		return false
	end
	return golpear(jugador, nodo, danoArma * Config.DanoNaveMineralFactor)
end

-- ¿Es esta instancia (o un antepasado) un nodo de mineral? Lo usan las naves para decidir qué hace un disparo.
function ServicioMinado.EsNodo(instancia: Instance): boolean
	return ServicioMinado.NodoDe(instancia) ~= nil
end

-- Registra la petición del cliente. Debe llamarse una vez, después de ServicioRed.Iniciar().
function ServicioMinado.Iniciar()
	ServicioRed.Conectar("PicarMineral", ServicioMinado.Picar)
	Players.PlayerRemoving:Connect(function(jugador: Player)
		ultimoGolpe[jugador] = nil
	end)
end

return ServicioMinado
