--!strict
--[[
	ServicioPlanetas: los planetas de bando en el servidor (que es quien decide).

	Todo ocurre en el MISMO lugar (place): no se usa TeleportService. Las superficies son zonas lejanas del mapa
	(Planetas/Datos) y pasar de una a otra es una TRANSICIÓN:

	  1. El servidor avisa al cliente (TransicionPlaneta, fase "Salida") y este funde la imagen a negro.
	  2. Con la pantalla en negro, el servidor pide al motor que cargue la zona de destino para ese jugador
	     (RequestStreamAroundAsync, por StreamingEnabled), espera a que el terreno del puerto esté generado y
	     coloca la nave (ServicioNaves.Teletransportar) o al personaje.
	  3. Avisa de nuevo (fase "Entrada") y el cliente vuelve a mostrar la imagen, ya con la luz y el cielo del sitio.

	Cuándo hay transición (lo detecta ServicioNaves y llama a las funciones de PonerEntorno):
	  ATERRIZAR  una nave entra en la atmósfera de un planeta (si no está en pleno combate): aparece volando sobre
	             el puerto de su superficie. Desde ahí se puede volar sobre el terreno o posarse con F (se baja
	             en el puerto).
	  DESPEGAR   una nave sube por encima del techo de la superficie: aparece en el espacio, en órbita sobre ese
	             planeta y mirando hacia fuera. Para salir a pie, cualquier hangar del puerto sirve.

	Además:
	  - Genera el terreno de cada superficie (ServicioPlanetas/Terreno) y construye sus puertos (Puertos).
	  - Si Datos.AparecerEnPlanetaDelBando está activo, cada jugador con bando aparece en el puerto de su planeta.
	  - LlevarAPie lleva a un jugador a pie al puerto de un planeta (lo usan las plataformas de la zona de pruebas), y
	    cada puerto tiene otra plataforma para volver a pie a la estación de pruebas.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Datos = require(ReplicatedStorage.Shared.Planetas.Datos)
local ExperimentoPlanetaRedondo = require(game:GetService("ReplicatedStorage").Shared.Experimentos.PlanetaRedondo)
local Espacio = require(ReplicatedStorage.Shared.Planetas.Espacio)
local ServicioBandos = require(script.Parent.ServicioBandos)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioNaves = require(script.Parent.ServicioNaves)
local ServicioRed = require(script.Parent.ServicioRed)
local Puertos = require(script.Puertos)
local Terreno = require(script.Terreno)

local ServicioPlanetas = {}

local iniciado = false
local puertoListo: { [string]: boolean } = {}
local enTransicion: { [Player]: boolean } = {}

-- Segundos que se espera, como mucho, a que el terreno del puerto esté generado o a que lleguen los datos.
local ESPERA_PUERTO = 30
local ESPERA_DATOS = 15

local function aVector(v: Espacio.Vec): Vector3
	return Vector3.new(v.X, v.Y, v.Z)
end

-- Marco en `posicion` mirando hacia `mirada` (si mira casi en vertical, se usa otro "arriba").
local function marcoMirando(posicion: Espacio.Vec, mirada: Espacio.Vec): CFrame
	local p, m = aVector(posicion), aVector(mirada)
	local arriba = if math.abs(m.Unit.Y) > 0.95 then Vector3.zAxis else Vector3.yAxis
	return CFrame.lookAt(p, p + m, arriba)
end

local function esperarPuerto(id: string)
	local limite = os.clock() + ESPERA_PUERTO
	while not puertoListo[id] and os.clock() < limite do
		task.wait(0.2)
	end
end

-- Pide al motor que transmita a ese jugador la zona de destino antes de llevarle (StreamingEnabled).
local function cargarZona(jugador: Player, posicion: Vector3)
	pcall(function()
		jugador:RequestStreamAroundAsync(posicion, 8)
	end)
end

local function avisar(jugador: Player, fase: string, planeta: string, tipo: string)
	local t = Datos.Transicion
	ServicioRed.EnviarACliente(jugador, "TransicionPlaneta", {
		Fase = fase, -- "Salida" (fundido a negro) o "Entrada" (de negro a imagen)
		Planeta = planeta,
		Tipo = tipo, -- "Aterrizaje", "Despegue" o "Viaje"
		Segundos = if fase == "Salida" then t.FundidoSalida else t.FundidoEntrada,
	})
end

--[[
	Hace la transición completa para un jugador: fundido a negro, carga la zona de `destino`, ejecuta `mover`
	(que coloca la nave o el personaje) y vuelve a mostrar la imagen. Espera mientras tanto.
]]
local function transicion(jugador: Player, planeta: string, tipo: string, destino: Vector3, mover: () -> ())
	enTransicion[jugador] = true
	avisar(jugador, "Salida", planeta, tipo)
	task.wait(Datos.Transicion.FundidoSalida)

	local inicio = os.clock()
	if Espacio.SuperficieDe({ X = destino.X, Y = destino.Y, Z = destino.Z }) then
		esperarPuerto(planeta)
	end
	cargarZona(jugador, destino)
	if jugador.Parent ~= nil then
		local ok, err = pcall(mover :: any)
		if not ok then
			warn(`[ServicioPlanetas] No se pudo colocar a {jugador.Name}: {err}`)
		end
	end
	local resto = Datos.Transicion.NegroMinimo - (os.clock() - inicio)
	if resto > 0 then
		task.wait(resto)
	end
	avisar(jugador, "Entrada", planeta, tipo)
	enTransicion[jugador] = nil
end

-- ===== Naves =====

-- La nave ha entrado en la atmósfera de `planeta`: aparece volando sobre su puerto.
local function aterrizarEnPlaneta(jugador: Player, planeta: string)
	local posicion, mirada = Espacio.PuntoLlegada(planeta)
	local destino = marcoMirando(posicion, mirada)
	transicion(jugador, planeta, "Aterrizaje", destino.Position, function()
		ServicioNaves.Teletransportar(jugador, destino)
	end)
end

-- La nave ha subido por encima del techo de la superficie: aparece en órbita, mirando hacia fuera.
local function despegarDePlaneta(jugador: Player, planeta: string)
	local posicion, mirada = Espacio.PuntoOrbita(planeta)
	local destino = marcoMirando(posicion, mirada)
	transicion(jugador, planeta, "Despegue", destino.Position, function()
		ServicioNaves.Teletransportar(jugador, destino)
	end)
end

-- Aterrizar con F en una superficie: el piloto se baja en el puerto de ese planeta.
local function destinoAterrizaje(_jugador: Player, posicion: Vector3): CFrame?
	local planeta = Espacio.SuperficieDe({ X = posicion.X, Y = posicion.Y, Z = posicion.Z })
	if planeta == nil then
		return nil
	end
	local bajada = Espacio.PuntoBajada(planeta)
	return marcoMirando(bajada, { X = 0, Y = 0, Z = -1 })
end

-- ===== Personajes =====

local function marcoAparicion(planeta: string): CFrame
	return marcoMirando(Espacio.PuntoAparicion(planeta), { X = 0, Y = 0, Z = -1 }) + Vector3.new(0, 3, 0)
end

-- Coloca al personaje recién aparecido en el puerto del planeta de su bando (si tiene bando).
local function alAparecer(jugador: Player, personaje: Model)
	if not Datos.AparecerEnPlanetaDelBando then
		return
	end
	local limite = os.clock() + ESPERA_DATOS
	local datos = ServicioDatos.ObtenerDatos(jugador)
	while datos == nil and os.clock() < limite and jugador.Parent ~= nil do
		task.wait(0.25)
		datos = ServicioDatos.ObtenerDatos(jugador)
	end
	local planeta = if datos then Espacio.PlanetaDeBando(datos.Bando) else nil
	if planeta == nil or enTransicion[jugador] or Datos.AparicionPropia[planeta] then
		return
	end
	esperarPuerto(planeta)
	local destino = marcoAparicion(planeta)
	cargarZona(jugador, destino.Position)
	-- Puede haber cambiado de personaje mientras tanto (por ejemplo, la sustitución a R6 de ServicioPersonaje).
	if jugador.Character == personaje and personaje.Parent ~= nil then
		personaje:PivotTo(destino)
	end
end

-- ===== API =====

-- ¿Está listo (generado) el terreno alrededor del puerto de ese planeta?
function ServicioPlanetas.PuertoListo(id: string): boolean
	return puertoListo[id] == true
end

--[[
	Lleva a un jugador A PIE al puerto de `planeta`, con transición. Devuelve false si no puede (está pilotando,
	ya está en una transición o no tiene personaje).
]]
function ServicioPlanetas.LlevarAPie(jugador: Player, planeta: string): boolean
	if Datos.Planetas[planeta] == nil or enTransicion[jugador] or ServicioNaves.NaveDe(jugador) ~= nil then
		return false
	end
	local personaje = jugador.Character
	if personaje == nil then
		return false
	end
	local destino = marcoAparicion(planeta)
	task.spawn(transicion, jugador, planeta, "Viaje", destino.Position, function()
		if jugador.Character == personaje and personaje.Parent ~= nil then
			personaje:PivotTo(destino)
		end
	end)
	return true
end

-- Lleva a un jugador a pie a la estación de pruebas del centro, con transición.
function ServicioPlanetas.LlevarAEstacion(jugador: Player): boolean
	local personaje = jugador.Character
	if personaje == nil or enTransicion[jugador] or ServicioNaves.NaveDe(jugador) ~= nil then
		return false
	end
	local destino = CFrame.new(aVector(Datos.Estacion.Aparicion))
	task.spawn(transicion, jugador, "", "Viaje", destino.Position, function()
		if jugador.Character == personaje and personaje.Parent ~= nil then
			personaje:PivotTo(destino)
		end
	end)
	return true
end

--[[
	Construye los puertos, empieza a generar los terrenos y conecta las transiciones con las naves. Debe
	llamarse una sola vez, después de ServicioNaves.Iniciar().
]]
function ServicioPlanetas.Iniciar()
	assert(not iniciado, "ServicioPlanetas.Iniciar() solo debe llamarse una vez")
	iniciado = true

	local carpeta = Instance.new("Folder")
	carpeta.Name = "Planetas"
	carpeta.Parent = workspace

	for _, id in Datos.OrdenPlanetas do
		Puertos.Crear(carpeta, id, function(jugador)
			ServicioPlanetas.LlevarAEstacion(jugador)
		end)
		-- EXPERIMENTO planeta redondo (solo Studio): la superficie plana del planeta que sustituye no se usa (y
		-- falsearía las medidas de memoria de la esfera), así que no se genera. La del otro planeta sí: ahí aparecen
		-- los jugadores de ese bando.
		if ExperimentoPlanetaRedondo.Activado() and id == ExperimentoPlanetaRedondo.Planeta then
			continue
		end
		-- Los dos terrenos se generan a la vez, cada uno empezando por su puerto.
		task.spawn(Terreno.Generar, id, function()
			puertoListo[id] = true
			print(`[ServicioPlanetas] Puerto de {Datos.Planetas[id].Nombre} listo`)
		end)
	end

	ServicioNaves.PonerEntorno({
		AlEntrarEnAtmosfera = aterrizarEnPlaneta,
		AlSuperarTecho = despegarDePlaneta,
		DestinoAterrizaje = destinoAterrizaje,
	})

	local function conectar(jugador: Player)
		jugador.CharacterAdded:Connect(function(personaje)
			task.spawn(alAparecer, jugador, personaje)
		end)
		if jugador.Character then
			task.spawn(alAparecer, jugador, jugador.Character)
		end
	end
	Players.PlayerAdded:Connect(conectar)
	for _, jugador in Players:GetPlayers() do
		conectar(jugador)
	end

	-- Al elegir bando (pantalla de elección), el jugador viaja a pie al puerto de su planeta, salvo que de ese planeta
	-- se encargue otro sistema (Datos.AparicionPropia).
	ServicioBandos.BandoElegido:Conectar(function(jugador: Player, bando: string)
		local planeta = Espacio.PlanetaDeBando(bando)
		if not Datos.AparecerEnPlanetaDelBando or planeta == nil or Datos.AparicionPropia[planeta] then
			return
		end
		task.spawn(function()
			esperarPuerto(planeta)
			ServicioPlanetas.LlevarAPie(jugador, planeta)
		end)
	end)
	Players.PlayerRemoving:Connect(function(jugador)
		enTransicion[jugador] = nil
	end)
end

return ServicioPlanetas
