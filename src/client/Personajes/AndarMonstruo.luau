--!strict
--[[
	AndarMonstruo: pone el andar de monstruo (reposo, andar, correr, saltar y caer) a TODOS los personajes del
	bando Monstruos que ve este cliente: el propio, los de los demás jugadores y los muñecos de entrenamiento.

	CÓMO SE APLICA
	  Las animaciones se cargan con VFX/Animador (definición por código en Personajes/Datos/AnimacionesMonstruo o
	  un ID de asset en Combate/Datos/Recursos.Animaciones) y se reproducen con prioridad Movement:
	    - por ENCIMA de las del script Animate (Core), que siguen sonando debajo pero no se ven. No hace falta
	      tocar el Animate: da igual que se reinicie, que el personaje reaparezca o que sea el de otro jugador
	      (cuyo Animate ni siquiera se ejecuta en este cliente).
	    - por DEBAJO de las del combate (Action), que se ven encima sin cambiar nada.
	  Cuando el personaje deja de ser monstruo, se sienta, trepa, nada o muere, la animación de monstruo se funde
	  y vuelve a verse la normal del Animate.

	POR QUÉ LO HACE CADA CLIENTE PARA TODOS
	  Las animaciones registradas por código solo existen en el cliente que las registra. Así que cada cliente
	  decide por su cuenta, para cada monstruo que ve, qué animación toca (con su velocidad y si está en el aire) y
	  la reproduce él. Si además le llega replicada la copia que reproduce el dueño del personaje, la para: ya
	  tiene la suya, sincronizada con lo que ve.

	QUIÉN ES MONSTRUO
	  El atributo Bandos.Atributo del Player, que pone el servidor (ServicioBandos): un cliente no puede
	  falsearlo. Los muñecos llevan su bando en el atributo Combate/Config.AtributoBando del modelo.

	RENDIMIENTO (móvil)
	  Nada se crea por cuadro: cada personaje carga sus pistas una vez y solo se cambia de pista al cambiar de
	  estado. El personaje propio se revisa cada cuadro; los demás cada Ajustes.IntervaloOtros segundos (cuatro
	  veces menos si están lejos de la cámara), con un rayo hacia el suelo solo cuando hace falta.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local AnimacionesMonstruo = require(Shared.Personajes.Datos.AnimacionesMonstruo)
local Bandos = require(Shared.Juego.Bandos)
local Cinematica = require(Shared.Animacion.CinematicaR6)
local ConfigCombate = require(Shared.Combate.Config)
local Locomocion = require(Shared.Personajes.Locomocion)

local Animador = require(script.Parent.Parent.VFX.Animador)

local Ajustes = AnimacionesMonstruo.Ajustes

type Seguido = {
	Modelo: Model,
	Humanoid: Humanoid,
	Raiz: BasePart,
	Estado: Locomocion.Estado?,
	Pista: AnimationTrack?,
	Ritmo: number,
	Variacion: number, -- multiplica el ritmo de Reposo y Caer: cada monstruo va a su aire
	ProximaRevision: number,
	Conexiones: { RBXScriptConnection },
}

local AndarMonstruo = {}

local seguidos: { [Model]: Seguido } = {}
local preparando: { [Model]: boolean } = {} -- esperando a que tenga Humanoid y HumanoidRootPart
local vigilados: { [Instance]: { RBXScriptConnection } } = {} -- jugadores y modelos con su bando vigilado
local idsLocomocion: { [string]: boolean } = {} -- para reconocer las copias replicadas desde otro cliente
local iniciado = false

-- Velocidad de los personajes a la que Andar y Correr no patinan (ver AnimacionesMonstruo).
local REFERENCIAS: { [string]: number } = {
	Andar = AnimacionesMonstruo.Definiciones.Andar.VelocidadReferencia,
	Correr = AnimacionesMonstruo.Definiciones.Correr.VelocidadReferencia,
}

local azar = Random.new()
local parametrosSuelo = RaycastParams.new()
parametrosSuelo.FilterType = Enum.RaycastFilterType.Exclude
parametrosSuelo.IgnoreWater = false

-- ===== Quién es monstruo =====

local function bandoDe(modelo: Model): string
	local jugador = Players:GetPlayerFromCharacter(modelo)
	return Locomocion.BandoDe(
		jugador ~= nil,
		if jugador then jugador:GetAttribute(Bandos.Atributo) else nil,
		modelo:GetAttribute(ConfigCombate.AtributoBando)
	)
end

local function esPropio(modelo: Model): boolean
	local jugador = Players.LocalPlayer
	return jugador ~= nil and jugador.Character == modelo
end

-- ===== Seguir y soltar personajes =====

-- Deja de aplicar el andar de monstruo: funde su animación y vuelve a verse la del Animate.
local function soltar(modelo: Model)
	local seguido = seguidos[modelo]
	if seguido == nil then
		return
	end
	seguidos[modelo] = nil
	for _, conexion in seguido.Conexiones do
		conexion:Disconnect()
	end
	if seguido.Pista then
		seguido.Pista:Stop(Ajustes.FundidoSalida)
	end
end

local function seguir(modelo: Model, humanoid: Humanoid, raiz: BasePart)
	-- La primera carga crea el Animator si falta y comprueba que el personaje es R6.
	if Animador.Cargar(modelo, AnimacionesMonstruo.Nombres.Reposo) == nil then
		return
	end
	local seguido: Seguido = {
		Modelo = modelo,
		Humanoid = humanoid,
		Raiz = raiz,
		Estado = nil,
		Pista = nil,
		Ritmo = 1,
		Variacion = 1 + azar:NextNumber(-Ajustes.VariacionRitmo, Ajustes.VariacionRitmo),
		ProximaRevision = 0,
		Conexiones = {},
	}
	seguidos[modelo] = seguido

	-- Si llega replicada la copia que reproduce el dueño del personaje, se para: este cliente ya pone la suya.
	local animator = humanoid:FindFirstChildOfClass("Animator")
	if animator then
		table.insert(
			seguido.Conexiones,
			animator.AnimationPlayed:Connect(function(pista: AnimationTrack)
				local animacion = pista.Animation
				if
					animacion
					and idsLocomocion[animacion.AnimationId]
					and not esPropio(modelo)
					and not Animador.EsPropia(modelo, pista)
				then
					pista:Stop(0)
				end
			end)
		)
	end
	-- Si cambian el Humanoid o la raíz (algo los destruye), se vuelve a empezar con los nuevos.
	table.insert(
		seguido.Conexiones,
		humanoid.AncestryChanged:Connect(function()
			if humanoid.Parent ~= modelo then
				soltar(modelo)
				task.defer(AndarMonstruo.Revisar, modelo)
			end
		end)
	)
end

--[[
	Decide si el modelo debe llevar el andar de monstruo y lo empieza o lo suelta. Se llama al aparecer un
	personaje, al cambiar el bando de su jugador, al cambiar de sitio el modelo (sale del mundo al morir o
	reaparecer) y cuando cambian sus piezas. Se puede llamar todas las veces que haga falta.
]]
function AndarMonstruo.Revisar(modelo: Model)
	local debe = modelo:IsDescendantOf(Workspace) and Locomocion.EsMonstruo(bandoDe(modelo))
	if not debe then
		soltar(modelo)
		return
	end
	if seguidos[modelo] ~= nil or preparando[modelo] then
		return
	end

	-- El personaje puede estar a medio montar (acaba de aparecer): se esperan sus piezas sin bloquear a nadie.
	preparando[modelo] = true
	task.spawn(function()
		local humanoid = modelo:WaitForChild("Humanoid", 10)
		local raiz = modelo:WaitForChild("HumanoidRootPart", 10)
		preparando[modelo] = nil
		if humanoid == nil or raiz == nil or not humanoid:IsA("Humanoid") or not raiz:IsA("BasePart") then
			return
		end
		-- Mientras esperaba pudo cambiar de bando o desaparecer.
		if seguidos[modelo] == nil and modelo:IsDescendantOf(Workspace) and Locomocion.EsMonstruo(bandoDe(modelo)) then
			seguir(modelo, humanoid, raiz)
		end
	end)
end

-- Vigila un modelo (personaje o muñeco): cambios de su bando y de dónde está.
local function vigilarModelo(modelo: Model)
	if vigilados[modelo] then
		return
	end
	local conexiones = {
		modelo:GetAttributeChangedSignal(ConfigCombate.AtributoBando):Connect(function()
			AndarMonstruo.Revisar(modelo)
		end),
		modelo.AncestryChanged:Connect(function()
			AndarMonstruo.Revisar(modelo)
			if modelo.Parent == nil then
				local propias: { RBXScriptConnection } = vigilados[modelo] or {}
				vigilados[modelo] = nil
				for _, conexion in propias do
					conexion:Disconnect()
				end
			end
		end),
	}
	vigilados[modelo] = conexiones
	AndarMonstruo.Revisar(modelo)
end

local function vigilarJugador(jugador: Player)
	if vigilados[jugador] then
		return
	end
	vigilados[jugador] = {
		jugador:GetAttributeChangedSignal(Bandos.Atributo):Connect(function()
			local personaje = jugador.Character
			if personaje then
				AndarMonstruo.Revisar(personaje)
			end
		end),
		jugador.CharacterAdded:Connect(vigilarModelo),
		jugador.CharacterRemoving:Connect(soltar),
	}
	if jugador.Character then
		vigilarModelo(jugador.Character)
	end
end

local function olvidarJugador(jugador: Player)
	local conexiones: { RBXScriptConnection } = vigilados[jugador] or {}
	for _, conexion in conexiones do
		conexion:Disconnect()
	end
	vigilados[jugador] = nil
	if jugador.Character then
		soltar(jugador.Character)
	end
end

-- Los muñecos de entrenamiento llevan la etiqueta de objetivo y su bando en el modelo.
local function alEtiquetar(instancia: Instance)
	if instancia:IsA("Model") and Players:GetPlayerFromCharacter(instancia) == nil then
		vigilarModelo(instancia)
	end
end

-- ===== Cada cuadro =====

-- ¿Hay suelo justo debajo? (Solo para personajes ajenos: del propio se sabe por el estado del Humanoid.)
local function haySuelo(seguido: Seguido): boolean
	parametrosSuelo.FilterDescendantsInstances = { seguido.Modelo }
	local origen = seguido.Raiz.Position
	local alcance = Cinematica.ALTURA_SUELO - Ajustes.DistanciaSuelo -- de la raíz a los pies, y un poco más
	return Workspace:Raycast(origen, Vector3.new(0, alcance, 0), parametrosSuelo) ~= nil
end

local function aplicar(seguido: Seguido, estado: Locomocion.Estado?, ritmo: number)
	local ritmoFinal = if estado == "Andar" or estado == "Correr" then ritmo else ritmo * seguido.Variacion

	if estado == seguido.Estado then
		local pista = seguido.Pista
		if pista and math.abs(ritmoFinal - seguido.Ritmo) > 0.02 then
			pista:AdjustSpeed(ritmoFinal)
			seguido.Ritmo = ritmoFinal
		end
		return
	end

	local anterior = seguido.Estado
	local fundido = Ajustes.Fundido
	if (anterior == "Saltar" or anterior == "Caer") and estado ~= "Saltar" and estado ~= "Caer" then
		fundido = Ajustes.FundidoAlSuelo
	end
	if seguido.Pista then
		seguido.Pista:Stop(if estado == nil then Ajustes.FundidoSalida else fundido)
	end
	seguido.Estado = estado
	seguido.Pista = nil
	seguido.Ritmo = ritmoFinal
	if estado == nil then
		return
	end

	local pista = Animador.Cargar(seguido.Modelo, AnimacionesMonstruo.Nombres[estado])
	if pista == nil then
		return
	end
	pista:Play(fundido, 1, ritmoFinal)
	-- Reposo y Caer empiezan en un punto al azar del ciclo: dos monstruos juntos no hacen los tics a la vez.
	if (estado == "Reposo" or estado == "Caer") and pista.Length > 0 then
		pista.TimePosition = azar:NextNumber(0, pista.Length)
	end
	seguido.Pista = pista
end

local function actualizar()
	local ahora = os.clock()
	local camara = Workspace.CurrentCamera
	for modelo, seguido in seguidos do
		local propio = esPropio(modelo)
		if not propio and ahora < seguido.ProximaRevision then
			continue
		end
		local raiz = seguido.Raiz
		if raiz.Parent == nil then
			continue -- fuera del alcance de StreamingEnabled: se retoma cuando vuelva
		end
		local humanoid = seguido.Humanoid
		local velocidad = raiz.AssemblyLinearVelocity
		local estadoHumanoid = if propio then humanoid:GetState().Name else nil

		local enSuelo = true
		if not propio then
			-- El rayo solo hace falta si se mueve en vertical o venía del aire.
			local enAire = seguido.Estado == "Saltar" or seguido.Estado == "Caer"
			if enAire or math.abs(velocidad.Y) > 1 then
				enSuelo = haySuelo(seguido)
			end
			local lejos = camara ~= nil
				and (camara.CFrame.Position - raiz.Position).Magnitude > Ajustes.DistanciaDetalle
			seguido.ProximaRevision = ahora + Ajustes.IntervaloOtros * (if lejos then 4 else 1)
		end

		local estado, ritmo = Locomocion.Decidir(seguido.Estado, {
			Velocidad = Vector3.new(velocidad.X, 0, velocidad.Z).Magnitude,
			VelocidadVertical = velocidad.Y,
			EstadoHumanoid = estadoHumanoid,
			EnSuelo = enSuelo,
			Sentado = humanoid.Sit or humanoid.SeatPart ~= nil,
			Muerto = humanoid.Health <= 0,
			SaltoTerminado = seguido.Estado == "Saltar" and (seguido.Pista == nil or not seguido.Pista.IsPlaying),
		}, Ajustes, REFERENCIAS)
		aplicar(seguido, estado :: Locomocion.Estado?, ritmo)
	end
end

-- ===== Arranque =====

function AndarMonstruo.Iniciar()
	assert(not iniciado, "AndarMonstruo.Iniciar() solo debe llamarse una vez")
	iniciado = true

	Animador.Precargar()
	for _, nombre in AnimacionesMonstruo.Nombres do
		local id = Animador.Id(nombre)
		if id then
			idsLocomocion[id] = true
		end
	end

	Players.PlayerAdded:Connect(vigilarJugador)
	Players.PlayerRemoving:Connect(olvidarJugador)
	for _, jugador in Players:GetPlayers() do
		vigilarJugador(jugador)
	end

	CollectionService:GetInstanceAddedSignal(ConfigCombate.EtiquetaObjetivo):Connect(alEtiquetar)
	for _, instancia in CollectionService:GetTagged(ConfigCombate.EtiquetaObjetivo) do
		alEtiquetar(instancia)
	end

	RunService.Heartbeat:Connect(actualizar)
end

-- Modelos a los que se está aplicando ahora el andar de monstruo (para depurar desde la consola de Studio).
function AndarMonstruo.Seguidos(): { Model }
	local lista = {}
	for modelo in seguidos do
		table.insert(lista, modelo)
	end
	return lista
end

return AndarMonstruo
