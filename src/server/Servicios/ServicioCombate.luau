--!strict
--[[
	ServicioCombate: el combate con el SERVIDOR como autoridad.

	El cliente solo PIDE usar una habilidad (remoto UsarHabilidad: qué habilidad, hacia dónde apunta y
	a qué distancia). Todo lo demás lo decide este servicio:

	  1. ESTADO     ¿sigue vivo, no está aturdido, no está en mitad de otra habilidad?
	  2. COOLDOWN   ¿ha terminado el cooldown de esa habilidad?
	  3. ENERGÍA    ¿tiene energía suficiente? Se regenera con el tiempo, sin bucles.
	  4. DISTANCIA  ¿pide un punto dentro del alcance? Se recorta al rango real.
	(Las cuatro las decide Combate/Arbitro, que no depende de Roblox y tiene sus propias pruebas.)

	Si todo es correcto, cobra la energía, arranca el cooldown y avisa a TODOS los clientes
	(HabilidadIniciada) para que reproduzcan animación y efectos de carga. Cuando pasa el tiempo de
	carga y de viaje, el servidor calcula él mismo a quién alcanza (forma, alcance, bando, invulnerabilidad),
	aplica el daño y avisa del impacto (HabilidadImpacto) con la lista de golpeados. El cliente nunca dice
	a quién golpea ni cuánto daño hace.

	Los del mismo bando no se hacen daño (Reglas.SonEnemigos). Un jugador sin bando puede dañar y ser
	dañado por cualquiera.

	Tipos de luchador: los jugadores (se registran solos al aparecer su personaje) y los muñecos de
	entrenamiento (ServicioCombate.RegistrarMunieco).
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local Arbitro = require(Shared.Combate.Arbitro)
local Config = require(Shared.Combate.Config)
local Reglas = require(Shared.Combate.Reglas)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioRed = require(script.Parent.ServicioRed)

type Habilidad = Poderes.Habilidad

-- El estado de combate puro (Arbitro.Luchador) más lo que solo existe en Roblox.
type Luchador = Arbitro.Luchador & {
	Modelo: Model,
	Jugador: Player?,
	Humanoid: Humanoid,
	Raiz: BasePart,
	Inmovilizaciones: number, -- cuántas habilidades lo mantienen quieto ahora mismo
	VelocidadBase: number,
	SaltoBase: number,
	AlturaSaltoBase: number,
	Generacion: number, -- sube al interrumpirlo: las acciones pendientes de una generación anterior se cancelan
}

local ServicioCombate = {}

local luchadores: { [Model]: Luchador } = {}
local iniciado = false

-- ===== Utilidades =====

local function luchadorDe(jugador: Player): Luchador?
	local personaje = jugador.Character
	return if personaje then luchadores[personaje] else nil
end

local function bandoDe(luchador: Luchador): string
	if luchador.Jugador then
		local datos = ServicioDatos.ObtenerDatos(luchador.Jugador)
		return if datos then datos.Bando else "Ninguno"
	end
	local bando = luchador.Modelo:GetAttribute(Config.AtributoBando)
	return if type(bando) == "string" then bando else "Ninguno"
end

local function estaVivo(luchador: Luchador): boolean
	return luchador.Humanoid.Health > 0 and luchador.Modelo:IsDescendantOf(workspace)
end

-- Parámetros de raycast que ignoran a todos los luchadores (para buscar suelo y paredes).
local function parametrosEscenario(): RaycastParams
	local lista = {}
	for modelo in luchadores do
		table.insert(lista, modelo)
	end
	local parametros = RaycastParams.new()
	parametros.FilterType = Enum.RaycastFilterType.Exclude
	parametros.FilterDescendantsInstances = lista
	return parametros
end

-- ===== Estado hacia el cliente =====

-- Envía al jugador su energía y los cooldowns que siguen en marcha.
local function enviarEstado(luchador: Luchador)
	local jugador = luchador.Jugador
	if not jugador then
		return
	end
	local ahora = os.clock()
	local cooldowns = {}
	for id, fin in luchador.Cooldowns do
		local restante = Reglas.CooldownRestante(fin, ahora)
		if restante > 0 then
			cooldowns[id] = restante
		end
	end
	ServicioRed.EnviarACliente(jugador, "EstadoCombate", {
		Energia = Arbitro.EnergiaActual(luchador, ahora),
		EnergiaMax = Config.EnergiaMaxima,
		Regeneracion = Config.EnergiaPorSegundo,
		Cooldowns = cooldowns,
	})
end

-- ===== Inmovilizar =====

local function aplicarInmovilizacion(luchador: Luchador)
	local humanoid = luchador.Humanoid
	if luchador.Inmovilizaciones > 0 then
		humanoid.WalkSpeed = 0
		humanoid.JumpHeight = 0
		humanoid.JumpPower = 0
	else
		humanoid.WalkSpeed = luchador.VelocidadBase
		humanoid.JumpPower = luchador.SaltoBase
		humanoid.JumpHeight = luchador.AlturaSaltoBase
	end
end

local function inmovilizar(luchador: Luchador, segundos: number)
	luchador.Inmovilizaciones += 1
	aplicarInmovilizacion(luchador)
	local generacion = luchador.Generacion
	task.delay(segundos, function()
		-- Si lo interrumpieron, `interrumpir` ya lo soltó: no se descuenta dos veces.
		if luchador.Generacion == generacion and luchador.Inmovilizaciones > 0 then
			luchador.Inmovilizaciones -= 1
			aplicarInmovilizacion(luchador)
		end
	end)
end

-- Cancela lo que el luchador tenía en marcha (lo hace el aturdimiento) y lo libera del bloqueo de movimiento.
local function interrumpir(luchador: Luchador)
	luchador.Generacion += 1
	luchador.Estado.OcupadoHasta = 0
	luchador.Inmovilizaciones = 0
	aplicarInmovilizacion(luchador)
end

-- ===== Resolver la petición =====

-- Dirección unitaria del golpe a partir de la que manda el cliente (que se sanea).
local function normalizarDireccion(luchador: Luchador, pedida: Vector3): Vector3
	local plana = Vector3.new(pedida.X, 0, pedida.Z)
	if plana.Magnitude < 0.05 then
		-- Sin dirección usable: se mira hacia donde mira el personaje.
		local mira = luchador.Raiz.CFrame.LookVector
		plana = Vector3.new(mira.X, 0, mira.Z)
	end
	plana = plana.Unit
	local magnitud = pedida.Magnitude
	local pendiente = if magnitud > 0.05 then Reglas.LimitarPendiente(pedida.Y / magnitud) else 0
	return Vector3.new(plana.X, pendiente, plana.Z).Unit
end

-- Punto de destino del golpe, calculado por el servidor.
local function calcularDestino(hab: Habilidad, origen: Vector3, direccion: Vector3, distancia: number): Vector3
	local parametros = parametrosEscenario()

	if hab.AlSuelo then
		-- Golpe de área: cae a la distancia pedida, sobre el suelo.
		local plana = Vector3.new(direccion.X, 0, direccion.Z).Unit
		local punto = origen + plana * distancia
		local suelo = workspace:Raycast(punto + Vector3.new(0, 60, 0), Vector3.new(0, -200, 0), parametros)
		return if suelo then suelo.Position else Vector3.new(punto.X, origen.Y - 3, punto.Z)
	end

	-- Proyectil o golpe cuerpo a cuerpo: recorre todo el rango, o hasta chocar con el escenario.
	local final = origen + direccion * hab.Rango
	if hab.Forma == "Linea" then
		local choque = workspace:Raycast(origen, direccion * hab.Rango, parametros)
		if choque then
			final = choque.Position
		end
	end
	return final
end

-- ===== Impacto =====

local function punto(vector: Vector3): Reglas.Punto
	return { X = vector.X, Y = vector.Y, Z = vector.Z }
end

-- Aplica el daño a todos los enemigos alcanzados por el golpe y avisa a los clientes.
local function aplicarImpacto(
	lanzador: Luchador,
	hab: Habilidad,
	origen: Vector3,
	destino: Vector3,
	direccion: Vector3,
	generacion: number
)
	if lanzador.Generacion ~= generacion or not estaVivo(lanzador) then
		return -- lo interrumpieron o murió: el golpe no llega a salir
	end
	-- Anti teletransporte: si el lanzador se ha ido muy lejos del origen, el golpe se cancela.
	if not Reglas.AlAlcance(lanzador.Raiz.Position :: any, origen :: any, Config.HolguraMovimiento) then
		return
	end

	local ahora = os.clock()
	local golpe: Reglas.Golpe = {
		Forma = hab.Forma,
		Origen = punto(origen),
		Destino = punto(destino),
		Direccion = punto(direccion),
		Rango = hab.Rango,
		Radio = hab.Radio,
		Angulo = hab.Angulo,
	}
	local bandoLanzador = bandoDe(lanzador)
	local alcanceMaximo = hab.Rango + hab.Radio + Config.RadioCuerpo + Config.HolguraMovimiento

	local golpeados = {}
	for _, objetivo in luchadores do
		if objetivo == lanzador then
			continue
		end
		objetivo.Estado.Vivo = estaVivo(objetivo)
		-- Enemigo (los del mismo bando no se hacen daño), vivo y no invulnerable.
		if not Arbitro.PuedeSerGolpeado(bandoLanzador, bandoDe(objetivo), objetivo, ahora) then
			continue
		end

		local posicion = objetivo.Raiz.Position
		-- El alcance se mide también desde donde está AHORA el lanzador (no basta con el origen guardado).
		if not Reglas.AlAlcance(posicion :: any, lanzador.Raiz.Position :: any, alcanceMaximo) then
			continue
		end
		if not Reglas.EnForma(golpe, punto(posicion)) then
			continue
		end

		-- Daño.
		objetivo.Humanoid:TakeDamage(hab.Dano)

		-- Aturdimiento: además de impedir actuar, interrumpe lo que estuviera lanzando.
		if hab.Aturdimiento > 0 then
			objetivo.Estado.AturdidoHasta = math.max(objetivo.Estado.AturdidoHasta, ahora + hab.Aturdimiento)
			interrumpir(objetivo)
		end

		-- Empuje: se aleja del lanzador, o se acerca al punto de impacto si el poder atrae.
		local horizontal = Vector3.new(posicion.X - origen.X, 0, posicion.Z - origen.Z)
		if hab.Empuje.Atrae then
			horizontal = Vector3.new(destino.X - posicion.X, 0, destino.Z - posicion.Z)
		end
		horizontal = if horizontal.Magnitude > 0.05 then horizontal.Unit else Vector3.new(direccion.X, 0, direccion.Z)
		local empuje = horizontal * hab.Empuje.Horizontal + Vector3.new(0, hab.Empuje.Vertical, 0)
		if not objetivo.Jugador then
			-- Los muñecos los mueve el servidor; a un jugador lo empuja su propio cliente.
			if not objetivo.Raiz.Anchored then
				objetivo.Raiz.AssemblyLinearVelocity = empuje
			end
		end

		table.insert(golpeados, { Modelo = objetivo.Modelo, Dano = hab.Dano, Empuje = empuje })
	end

	ServicioRed.EnviarATodos("HabilidadImpacto", hab.Id, lanzador.Modelo, destino, direccion, golpeados)
end

-- ===== Usar una habilidad =====

local function usarHabilidad(jugador: Player, idPedido: string, direccionPedida: Vector3, distanciaPedida: number)
	local luchador = luchadorDe(jugador)
	if luchador == nil then
		return
	end
	local ahora = os.clock()
	luchador.Estado.Vivo = estaVivo(luchador)

	-- El árbitro comprueba estado, cooldown, energía y distancia (ver Combate/Arbitro).
	local resultado = Arbitro.Evaluar(luchador, idPedido, ahora, distanciaPedida)
	local hab = resultado.Habilidad
	if not resultado.Ok or hab == nil then
		return
	end

	-- Todo correcto: se cobra, se arrancan los cooldowns y se bloquea al lanzador.
	local duracionTotal = Arbitro.Aplicar(luchador, idPedido, resultado, ahora)
	if hab.Inmoviliza then
		inmovilizar(luchador, duracionTotal)
	end

	local origen = luchador.Raiz.Position
	local direccion = normalizarDireccion(luchador, direccionPedida)
	local destino = calcularDestino(hab, origen, direccion, resultado.Distancia)

	-- A todos los clientes: empieza la habilidad (animación + efectos de carga).
	ServicioRed.EnviarATodos("HabilidadIniciada", hab.Id, luchador.Modelo, origen, destino, direccion, os.clock())
	enviarEstado(luchador)

	-- Y cuando llegue el momento, el servidor decide el impacto.
	local generacion = luchador.Generacion
	task.delay(
		hab.Tiempos.Carga + hab.Tiempos.Viaje,
		aplicarImpacto,
		luchador,
		hab,
		origen,
		destino,
		direccion,
		generacion
	)
end

-- ===== Registro de luchadores =====

local function registrar(modelo: Model, jugador: Player?, humanoid: Humanoid, raiz: BasePart): Luchador
	humanoid.MaxHealth = if jugador then Config.VidaMaxima else Config.VidaMunieco
	humanoid.Health = humanoid.MaxHealth

	local luchador = Arbitro.NuevoLuchador(os.clock()) :: any
	luchador.Modelo = modelo
	luchador.Jugador = jugador
	luchador.Humanoid = humanoid
	luchador.Raiz = raiz
	luchador.Inmovilizaciones = 0
	luchador.VelocidadBase = humanoid.WalkSpeed
	luchador.SaltoBase = humanoid.JumpPower
	luchador.AlturaSaltoBase = humanoid.JumpHeight
	luchador.Generacion = 0
	luchadores[modelo] = luchador :: Luchador
	CollectionService:AddTag(modelo, Config.EtiquetaObjetivo)

	humanoid.Died:Connect(function()
		luchador.Estado.Vivo = false
		interrumpir(luchador)
	end)
	modelo.Destroying:Connect(function()
		luchadores[modelo] = nil
	end)
	return luchador :: Luchador
end

local function alAparecerPersonaje(jugador: Player, personaje: Model)
	local humanoid = personaje:WaitForChild("Humanoid", 10) :: Humanoid?
	local raiz = personaje:WaitForChild("HumanoidRootPart", 10) :: BasePart?
	if humanoid == nil or raiz == nil or personaje.Parent == nil then
		return
	end
	local luchador = registrar(personaje, jugador, humanoid, raiz)
	enviarEstado(luchador)
end

local function alEntrarJugador(jugador: Player)
	jugador.CharacterAdded:Connect(function(personaje)
		alAparecerPersonaje(jugador, personaje)
	end)
	if jugador.Character then
		task.spawn(alAparecerPersonaje, jugador, jugador.Character)
	end
end

--[[
	Registra un muñeco de entrenamiento (un Model con Humanoid y HumanoidRootPart) como objetivo.
	`bando` decide quién puede dañarlo: los del mismo bando no le hacen daño.
]]
function ServicioCombate.RegistrarMunieco(modelo: Model, bando: string)
	local humanoid = modelo:FindFirstChildOfClass("Humanoid")
	local raiz = modelo:FindFirstChild("HumanoidRootPart")
	assert(humanoid and raiz and raiz:IsA("BasePart"), "El muñeco necesita Humanoid y HumanoidRootPart")
	modelo:SetAttribute(Config.AtributoBando, bando)
	registrar(modelo, nil, humanoid, raiz)
end

--[[
	Empieza a atender el combate. Debe llamarse una sola vez, después de ServicioRed.Iniciar() y antes de
	ServicioDatos.Iniciar().
]]
function ServicioCombate.Iniciar()
	assert(not iniciado, "ServicioCombate.Iniciar() solo debe llamarse una vez")
	iniciado = true

	ServicioRed.Conectar("UsarHabilidad", usarHabilidad)
	ServicioRed.Conectar("PedirEstadoCombate", function(jugador: Player)
		local luchador = luchadorDe(jugador)
		if luchador then
			enviarEstado(luchador)
		end
	end)

	Players.PlayerAdded:Connect(alEntrarJugador)
	for _, jugador in Players:GetPlayers() do
		alEntrarJugador(jugador)
	end
end

return ServicioCombate
