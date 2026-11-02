--!strict
--[[
	ServicioEscaner: el escáner de mano, que analiza criaturas, plantas y minerales.

	El flujo, con el servidor al mando de todo lo que importa:

	  1. El cliente apunta y pide `EscanearObjetivo(instancia)`. Solo dice QUÉ.
	  2. El servidor comprueba que se pueda: el jugador vive, va a pie, no está ya escaneando, el objetivo es de verdad
	     escaneable (etiqueta + especie conocida), no está agotado, está al alcance de SU escáner (mejora Escáner) y se ve
	     (nada sólido en medio). Calcula cuánto dura el análisis con la velocidad de SU escáner.
	  3. Avisa a todos (`EscaneoIniciado`) para que dibujen los efectos de escaneo.
	  4. Cada pocas décimas vigila: si el jugador suelta, muere, se aleja demasiado, se pone a pilotar o el objetivo
	     desaparece, cancela (`EscaneoCancelado`).
	  5. Al acabar el tiempo, apunta el descubrimiento, reparte XP y monedas (más la primera vez) y envía la ficha
	     (`FichaEscaner`) a quien escaneó y el aviso de fin (`EscaneoCompletado`) a todos.

	Un objeto es escaneable si lleva la etiqueta "Escaneable" y el atributo EspecieId (ver Exploracion/Datos/Especies).
	`Marcar` lo pone en una instancia.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local Config = require(Shared.Exploracion.Config)
local Especies = require(Shared.Exploracion.Datos.Especies)
local Estadisticas = require(Shared.Naves.Estadisticas)
local Reglas = require(Shared.Exploracion.Escaner)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioRed = require(script.Parent.ServicioRed)
local ServicioReplicacion = require(script.Parent.ServicioReplicacion)

type Escaneo = {
	Jugador: Player,
	Personaje: Model,
	Objetivo: Instance,
	Especie: string,
	Inicio: number,
	Duracion: number,
	Alcance: number,
}

local ServicioEscaner = {}

local activos: { [Player]: Escaneo } = {}
local ultimoInicio: { [Player]: number } = setmetatable({}, { __mode = "k" }) :: any
local bucleActivo = false

-- ===== Utilidades =====

local function avisar(jugador: Player, texto: string, tono: string)
	ServicioRed.EnviarACliente(jugador, "AvisoExploracion", texto, tono)
end

-- Posición central de un objetivo (Model o Part).
local function posicionDe(objetivo: Instance): Vector3?
	if objetivo:IsA("Model") then
		return objetivo:GetPivot().Position
	elseif objetivo:IsA("BasePart") then
		return objetivo.Position
	end
	return nil
end

-- Radio aproximado del objetivo: el alcance se mide hasta su superficie, no hasta su centro.
local function radioDe(objetivo: Instance): number
	if objetivo:IsA("Model") then
		local _, tamano = objetivo:GetBoundingBox()
		return math.max(tamano.X, tamano.Y, tamano.Z) / 2
	elseif objetivo:IsA("BasePart") then
		return math.max(objetivo.Size.X, objetivo.Size.Y, objetivo.Size.Z) / 2
	end
	return 0
end

-- Pone a una instancia la etiqueta y la especie para que el escáner pueda analizarla.
function ServicioEscaner.Marcar(instancia: Instance, especie: string)
	assert(Especies.Lista[especie] ~= nil, `Especie desconocida: '{especie}'`)
	instancia:SetAttribute(Config.AtributoEspecie, especie)
	CollectionService:AddTag(instancia, Config.EtiquetaEscaneable)
end

-- El objetivo escaneable al que pertenece una instancia (ella o un antepasado), o nil.
function ServicioEscaner.ObjetivoDe(instancia: Instance): Instance?
	local actual: Instance? = instancia
	while actual ~= nil and actual ~= workspace do
		if CollectionService:HasTag(actual, Config.EtiquetaEscaneable) then
			return actual
		end
		actual = actual.Parent
	end
	return nil
end

-- ¿Se puede analizar ahora? (en el mundo, con especie conocida y sin estar agotado)
local function especieDe(objetivo: Instance): string?
	if objetivo.Parent == nil or not objetivo:IsDescendantOf(workspace) then
		return nil
	end
	if objetivo:GetAttribute(Config.AtributoMineralAgotado) == true then
		return nil
	end
	local especie = objetivo:GetAttribute(Config.AtributoEspecie)
	if type(especie) ~= "string" or Especies.Lista[especie] == nil then
		return nil
	end
	return especie
end

-- Distancia desde el personaje hasta la superficie del objetivo.
local function distanciaA(personaje: Model, objetivo: Instance): number?
	local raiz = personaje:FindFirstChild("HumanoidRootPart")
	local posicion = posicionDe(objetivo)
	if raiz == nil or not raiz:IsA("BasePart") or posicion == nil then
		return nil
	end
	return math.max(0, ((raiz :: BasePart).Position - posicion).Magnitude - radioDe(objetivo))
end

-- ¿Se ve el objetivo desde la cabeza del personaje? (un raycast que ignora al propio jugador)
local function seVe(personaje: Model, objetivo: Instance): boolean
	local cabeza = personaje:FindFirstChild("Head")
	local posicion = posicionDe(objetivo)
	if cabeza == nil or not cabeza:IsA("BasePart") or posicion == nil then
		return false
	end
	local origen = (cabeza :: BasePart).Position
	local parametros = RaycastParams.new()
	parametros.FilterType = Enum.RaycastFilterType.Exclude
	parametros.FilterDescendantsInstances = { personaje }
	local golpe = workspace:Raycast(origen, posicion - origen, parametros)
	-- Si el rayo no choca con nada antes de llegar al centro, o choca con el propio objetivo, se ve.
	return golpe == nil or golpe.Instance:IsDescendantOf(objetivo)
end

-- Estadísticas del escáner del jugador (alcance y velocidad), según su mejora Escáner.
local function estadisticasDe(jugador: Player): Estadisticas.Estadisticas?
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return nil
	end
	return Estadisticas.Calcular(datos.MejorasNave)
end

local function estaVivo(personaje: Model?): boolean
	local humanoid = if personaje then personaje:FindFirstChildOfClass("Humanoid") else nil
	return humanoid ~= nil and humanoid.Health > 0
end

-- ===== Fin del escaneo =====

local function cancelar(escaneo: Escaneo, aviso: string?)
	if activos[escaneo.Jugador] ~= escaneo then
		return
	end
	activos[escaneo.Jugador] = nil
	ServicioRed.EnviarATodos("EscaneoCancelado", escaneo.Personaje)
	if aviso then
		avisar(escaneo.Jugador, aviso, "Info")
	end
end

local function completar(escaneo: Escaneo)
	activos[escaneo.Jugador] = nil
	local jugador = escaneo.Jugador
	local datos = ServicioDatos.ObtenerDatos(jugador)
	local especie = Especies.Lista[escaneo.Especie]
	if datos == nil then
		ServicioRed.EnviarATodos("EscaneoCancelado", escaneo.Personaje)
		return
	end

	local veces = datos.Descubrimientos[escaneo.Especie] or 0
	local recompensa = Reglas.Recompensa(especie.XP, especie.Monedas, veces)
	datos.Descubrimientos[escaneo.Especie] = veces + 1
	datos.XP += recompensa.XP
	datos.Monedas += recompensa.Monedas
	ServicioReplicacion.EnviarDatos(jugador)

	local punto = posicionDe(escaneo.Objetivo) or Vector3.zero
	ServicioRed.EnviarATodos("EscaneoCompletado", escaneo.Personaje, escaneo.Objetivo, punto)
	ServicioRed.EnviarACliente(
		jugador,
		"FichaEscaner",
		escaneo.Especie,
		recompensa.Nuevo,
		recompensa.XP,
		recompensa.Monedas,
		veces + 1
	)

	-- Un descubrimiento nuevo no debe perderse si el servidor se cae.
	if recompensa.Nuevo then
		task.spawn(ServicioDatos.GuardarAhora, jugador)
	end
end

-- ===== Vigilancia =====

local function revisar(escaneo: Escaneo, ahora: number)
	local jugador = escaneo.Jugador
	if jugador.Parent == nil or jugador.Character ~= escaneo.Personaje or not estaVivo(escaneo.Personaje) then
		cancelar(escaneo, nil)
		return
	end
	if escaneo.Personaje:GetAttribute(Config.AtributoPilotando) == true then
		cancelar(escaneo, nil)
		return
	end
	if especieDe(escaneo.Objetivo) ~= escaneo.Especie then
		cancelar(escaneo, "El objetivo ha desaparecido")
		return
	end
	local distancia = distanciaA(escaneo.Personaje, escaneo.Objetivo)
	if distancia == nil or not Reglas.EnAlcance(distancia, escaneo.Alcance, true) then
		cancelar(escaneo, "Te has alejado demasiado")
		return
	end
	if ahora - escaneo.Inicio >= escaneo.Duracion then
		completar(escaneo)
	end
end

local function asegurarBucle()
	if bucleActivo then
		return
	end
	bucleActivo = true
	task.spawn(function()
		while next(activos) ~= nil do
			local ahora = os.clock()
			-- Se copia la lista: revisar() puede quitar escaneos mientras se recorre.
			local lista: { Escaneo } = {}
			for _, escaneo in activos do
				table.insert(lista, escaneo)
			end
			for _, escaneo in lista do
				revisar(escaneo, ahora)
			end
			task.wait(Config.IntervaloVigilanciaEscaner)
		end
		bucleActivo = false
	end)
end

-- ===== Peticiones del cliente =====

local function escanear(jugador: Player, instancia: Instance)
	if activos[jugador] ~= nil then
		return -- ya está escaneando
	end
	local ahora = os.clock()
	if ahora - (ultimoInicio[jugador] or -math.huge) < Config.EnfriamientoEscaner then
		return
	end

	local personaje = jugador.Character
	if personaje == nil or not estaVivo(personaje) or personaje:GetAttribute(Config.AtributoPilotando) == true then
		return
	end
	local stats = estadisticasDe(jugador)
	if stats == nil then
		return
	end

	local objetivo = ServicioEscaner.ObjetivoDe(instancia)
	local especieId = if objetivo then especieDe(objetivo) else nil
	if objetivo == nil or especieId == nil then
		avisar(jugador, "Eso no se puede escanear", "Mal")
		return
	end
	local distancia = distanciaA(personaje, objetivo)
	if distancia == nil or not Reglas.EnAlcance(distancia, stats.AlcanceEscaner, true) then
		avisar(jugador, "Demasiado lejos para escanear", "Mal")
		return
	end
	if not seVe(personaje, objetivo) then
		avisar(jugador, "No tienes línea de visión", "Mal")
		return
	end

	ultimoInicio[jugador] = ahora
	local duracion = Reglas.Duracion(Especies.Lista[especieId].Duracion, stats.VelocidadEscaner)
	activos[jugador] = {
		Jugador = jugador,
		Personaje = personaje,
		Objetivo = objetivo,
		Especie = especieId,
		Inicio = ahora,
		Duracion = duracion,
		Alcance = stats.AlcanceEscaner,
	}
	ServicioRed.EnviarATodos("EscaneoIniciado", personaje, objetivo, duracion)
	asegurarBucle()
end

local function alSoltar(jugador: Player)
	local escaneo = activos[jugador]
	if escaneo then
		cancelar(escaneo, nil)
	end
end

-- Registra las peticiones del cliente. Debe llamarse una vez, después de ServicioRed.Iniciar().
function ServicioEscaner.Iniciar()
	ServicioRed.Conectar("EscanearObjetivo", escanear)
	ServicioRed.Conectar("CancelarEscaneo", alSoltar)
	Players.PlayerRemoving:Connect(function(jugador: Player)
		activos[jugador] = nil
		ultimoInicio[jugador] = nil
	end)
end

return ServicioEscaner
