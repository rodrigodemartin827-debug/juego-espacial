--!strict
--[[
	EXPERIMENTO (servidor): Nueva Tierra como esfera de Terrain. Ver shared/Experimentos/PlanetaRedondo.

	  - Genera la esfera: una corteza de losas (FillBlock tangentes; FillBall no acepta radios tan grandes),
	    manchas de materiales, colinas (bolas medio enterradas) y rocas. Mide el tiempo y la memoria.
	  - Monta un puerto (un hangar normal, girado para que su suelo sea tangente a la esfera).
	  - En Studio, cada vez que aparece el personaje lo lleva al puerto.
	  - Aterrizar (F) cerca del suelo deja la nave aparcada ahí mismo, posada sobre la esfera, y baja al piloto a su
	    lado. Al usarla ("Despegar") se despega desde ese punto.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Experimento = require(ReplicatedStorage.Shared.Experimentos.PlanetaRedondo)
local Servicios = script.Parent.Parent.Servicios
local Hangar = require(Servicios.Hangar)
local ServicioDatos = require(Servicios.ServicioDatos)
local ServicioNaves = require(Servicios.ServicioNaves)
local Modelo = require(Servicios.ServicioNaves.Modelo)

local PlanetaRedondo = {}

local listo = false
local carpeta: Folder? = nil
local marcoPuerto: CFrame? = nil

local ANGULO_AUREO = math.pi * (3 - math.sqrt(5))

-- Punto i de n repartidos de forma uniforme sobre la esfera unidad (espiral de Fibonacci).
local function puntoFibonacci(i: number, n: number): Vector3
	local y = 1 - (i + 0.5) * 2 / n
	local r = math.sqrt(math.max(0, 1 - y * y))
	local fi = i * ANGULO_AUREO
	return Vector3.new(math.cos(fi) * r, y, math.sin(fi) * r)
end

local function direccionAleatoria(azar: Random): Vector3
	local y = azar:NextNumber(-1, 1)
	local fi = azar:NextNumber(0, 2 * math.pi)
	local r = math.sqrt(1 - y * y)
	return Vector3.new(math.cos(fi) * r, y, math.sin(fi) * r)
end

-- Material de la superficie en una dirección: casquetes de nieve, y manchas según un ruido 3D.
local function mat(nombre: string): Enum.Material
	return (Enum.Material :: any)[nombre]
end

local function materialEn(n: Vector3, radio: number): Enum.Material
	local t = Experimento.Terreno
	local m = t.Materiales
	local latitud = math.deg(math.asin(math.clamp(n.Y, -1, 1)))
	if math.abs(latitud) > t.LatitudNieve then
		return mat(m.Nieve)
	end
	local p = n * radio * t.EscalaRuido
	local ruido = math.noise(p.X, p.Y + t.Semilla, p.Z)
	if ruido > 0.3 then
		return mat(m.Alta)
	elseif ruido < -0.38 then
		return mat(m.Arena)
	elseif ruido < -0.25 then
		return mat(m.Tierra)
	end
	return mat(m.Base)
end

-- ¿Cae la dirección `n` en la cara del cubo inflado reservada para una región de mallas (Terreno.CaraReservada)?
-- Ahí no se ponen colinas ni rocas: asomarían a través de las mallas de la región.
local function enCaraReservada(n: Vector3): boolean
	local cara = Experimento.Terreno.CaraReservada
	if cara ~= "YP" then
		return false
	end
	return n.Y > math.max(math.abs(n.X), math.abs(n.Z)) - 0.08
end

-- ¿Está la dirección `n` cerca del puerto? (ahí no se ponen colinas ni rocas)
local function cercaDelPuerto(n: Vector3, normalPuerto: Vector3, radio: number, distancia: number): boolean
	return math.acos(math.clamp(n:Dot(normalPuerto), -1, 1)) * radio < distancia
end

--[[
	Genera la esfera de terreno. Devuelve un resumen con tiempos y cantidades.
]]
local function generar(centro: Vector3, radio: number, normalPuerto: Vector3): { [string]: any }
	local t = Experimento.Terreno
	local terreno = workspace.Terrain
	local azar = Random.new(t.Semilla)
	local inicio = os.clock()
	-- Se cede el hilo en cuanto se lleva un rato trabajando (si no, Roblox corta el script por tiempo).
	local ultimaPausa = os.clock()
	local function pausa()
		if os.clock() - ultimaPausa > t.SegundosPorTanda then
			task.wait()
			ultimaPausa = os.clock()
		end
	end

	-- 1. Colinas: bolas medio enterradas (cúpulas), más pequeñas que grandes. Se VACÍAN por dentro (una bola de aire
	-- algo menor en el mismo centro): Roblox guarda cada celda llena, y macizas ocupaban cientos de MB. La corteza,
	-- que va después, vuelve a rellenar lo que el vaciado quita entre su cara de abajo y la superficie.
	local area = 4 * math.pi * radio * radio
	local colinas = math.floor(t.ColinasPorMillon * area / 1e6)
	local hechas = 0
	for _ = 1, colinas do
		local n = direccionAleatoria(azar)
		local rmin, rmax = t.RadioColina[1], t.RadioColina[2]
		local r = rmin + (rmax - rmin) * azar:NextNumber() ^ 2
		if enCaraReservada(n) then
			continue
		end
		if cercaDelPuerto(n, normalPuerto, radio, 260 + r) then
			continue
		end
		local material = materialEn(n, radio)
		if material == mat(t.Materiales.Arena) then
			material = mat(t.Materiales.Base)
		end
		local centroColina = centro + n * (radio - r * t.Enterrado)
		terreno:FillBall(centroColina, r, material)
		if t.GrosorColina > 0 and r > t.GrosorColina + 8 then
			terreno:FillBall(centroColina, r - t.GrosorColina, Enum.Material.Air)
		end
		-- Las más grandes asoman una cima de roca.
		if r > 250 then
			local cima = centro + n * (radio + r * (1 - t.Enterrado) - r * 0.15)
			terreno:FillBall(cima, r * 0.25, mat(t.Materiales.Roca))
		end
		hechas += 1
		pausa()
	end
	local tiempoColinas = os.clock() - inicio

	-- 2. Corteza: losas tangentes.
	local losas = math.ceil(area / (t.SeparacionLosas * t.SeparacionLosas))
	local tamano = Vector3.new(t.AnchoLosa, t.Grosor, t.AnchoLosa)
	for i = 0, losas - 1 do
		local n = puntoFibonacci(i, losas)
		local marco = Experimento.Marco(centro + n * (radio - t.Grosor / 2), n, Vector3.zAxis)
		terreno:FillBlock(marco, tamano, materialEn(n, radio))
		pausa()
	end
	local tiempoCorteza = os.clock() - inicio - tiempoColinas

	-- 3. Rocas sueltas.
	local rocas = math.floor(t.RocasPorMillon * area / 1e6)
	for _ = 1, rocas do
		local n = direccionAleatoria(azar)
		if enCaraReservada(n) then
			continue
		end
		if cercaDelPuerto(n, normalPuerto, radio, 120) then
			continue
		end
		local r = azar:NextNumber(t.RadioRoca[1], t.RadioRoca[2])
		terreno:FillBall(centro + n * (radio + r * 0.15), r, mat(t.Materiales.Roca))
		pausa()
	end

	-- 3b. Piedras pequeñas alrededor del puerto (prueba de pasar por encima sin saltar).
	local referencia = Experimento.Marco(Vector3.zero, normalPuerto, Vector3.zAxis)
	for _ = 1, t.PiedrasPuerto do
		local angulo = azar:NextNumber(0, 2 * math.pi)
		local d = azar:NextNumber(t.ZonaPiedras[1], t.ZonaPiedras[2])
		local tangente = referencia.RightVector * math.cos(angulo) + referencia.LookVector * math.sin(angulo)
		local n = (normalPuerto + tangente * (d / radio)).Unit
		local r = azar:NextNumber(t.RadioPiedra[1], t.RadioPiedra[2])
		terreno:FillBall(centro + n * (radio + r * 0.2), r, mat(t.Materiales.Roca))
		pausa()
	end

	-- 4. Explanada del puerto (pavimento, a ras del suelo).
	local marcoPlano = Experimento.Marco(centro + normalPuerto * (radio - 4), normalPuerto, Vector3.zAxis)
	terreno:FillBlock(marcoPlano, Vector3.new(220, 8, 220), Enum.Material.Pavement)

	return {
		Losas = losas,
		Colinas = hechas,
		Rocas = rocas,
		SegundosCorteza = tiempoCorteza,
		SegundosColinas = tiempoColinas,
		SegundosTotal = os.clock() - inicio,
	}
end

-- Monta el hangar del puerto girado sobre la esfera. Devuelve el marco del suelo del puerto.
local function montarPuerto(padre: Instance, centro: Vector3, radio: number, normal: Vector3): CFrame
	local suelo = Experimento.Marco(centro + normal * radio, normal, Vector3.zAxis)
	local modelo = Instance.new("Model")
	modelo.Name = "Puerto"
	-- El hangar se construye en el origen y luego se gira entero hasta su sitio.
	local plataforma = Hangar.Crear(modelo, Vector3.zero)
	modelo.WorldPivot = CFrame.identity
	modelo:PivotTo(suelo)
	plataforma.Marco = suelo * plataforma.Marco
	modelo.Parent = padre
	return suelo
end

-- ===== Personaje =====

local function llevarAlPuerto(jugador: Player, personaje: Model)
	local marco = marcoPuerto
	if marco == nil then
		return
	end
	-- Delante de la boca del hangar (que se abre hacia -Z), mirando hacia fuera (de espaldas al hangar).
	local destino = marco * CFrame.new(0, 3.2, -40)
	pcall(function()
		jugador:RequestStreamAroundAsync(destino.Position, 10)
	end)
	if jugador.Character ~= personaje or personaje.Parent == nil then
		return
	end
	local raiz = personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
	if raiz then
		raiz.AssemblyLinearVelocity = Vector3.zero
	end
	personaje:PivotTo(destino)
end

local function alAparecer(jugador: Player, personaje: Model)
	-- CharacterAdded llega antes de que el personaje tenga padre, y ServicioPersonaje puede sustituirlo por un R6.
	local limite = os.clock() + 10
	while personaje.Parent == nil and os.clock() < limite do
		task.wait()
	end
	task.wait(0.5)
	while not listo do
		task.wait(0.2)
	end
	if jugador.Character == personaje then
		llevarAlPuerto(jugador, personaje)
	end
end

-- ===== Aterrizar sobre la esfera =====

-- Deja una nave posada en `suelo`; usarla la hace despegar desde ahí (y la aparcada desaparece).
local function aparcar(jugador: Player, suelo: CFrame)
	local datos = ServicioDatos.ObtenerDatos(jugador)
	local nave = Modelo.CrearExhibicion(if datos then datos.Bando else "Ninguno")
	nave.Name = `Nave aparcada de {jugador.Name}`
	nave:PivotTo(suelo * CFrame.new(0, Modelo.ALTURA_POSADA, 0))
	local plataforma: ServicioNaves.Plataforma = { Marco = suelo, Ocupada = false, AlCambiar = nil }
	local aviso = Instance.new("ProximityPrompt")
	aviso.ActionText = "Despegar"
	aviso.ObjectText = "Tu nave"
	aviso.HoldDuration = 0.5
	aviso.MaxActivationDistance = 16
	aviso.RequiresLineOfSight = false
	aviso.Parent = nave.PrimaryPart
	aviso.Triggered:Connect(function(quien: Player)
		if quien == jugador then
			ServicioNaves.Despegar(quien, plataforma)
		end
	end)
	plataforma.AlCambiar = function(ocupada: boolean)
		if ocupada then
			nave:Destroy()
		end
	end
	nave.Parent = carpeta
end

-- Si la nave está cerca del suelo del planeta redondo, se posa ahí y el piloto baja a su lado.
local function destinoAterrizaje(jugador: Player, posicion: Vector3): CFrame?
	local centro = Experimento.Centro()
	local radio = Experimento.Radio
	local hacia = posicion - centro
	local altura = hacia.Magnitude - radio
	if altura > Experimento.Nave.AlcanceReferencia then
		return nil
	end
	local arriba = hacia.Unit
	local parametros = RaycastParams.new()
	parametros.FilterType = Enum.RaycastFilterType.Include
	parametros.FilterDescendantsInstances = { workspace.Terrain }
	local golpe = workspace:Raycast(posicion, -arriba * (altura + 400), parametros)
	if golpe == nil or golpe.Distance > Experimento.Nave.AlturaAterrizaje then
		return nil -- demasiado alto: vuelve a su plataforma, como siempre
	end
	local nave = ServicioNaves.NaveDe(jugador)
	local frente = if nave then (nave :: any).Raiz.CFrame.LookVector else Vector3.zAxis
	local suelo = Experimento.Marco(golpe.Position, arriba, frente)
	aparcar(jugador, suelo)
	return suelo * CFrame.new(9, 3.2, 4)
end

-- ===== API =====

function PlanetaRedondo.Iniciar()
	if not Experimento.Activado() then
		return
	end
	local centro = Experimento.Centro()
	-- La esfera de Terrain puede ir hundida (Terreno.Hundimiento) para dejar sitio a una región hecha con mallas.
	local radio = Experimento.Radio - (Experimento.Terreno.Hundimiento or 0)
	local Datos = require(ReplicatedStorage.Shared.Planetas.Datos) :: any
	local n = Datos.Planetas[Experimento.Planeta].NormalAterrizaje
	local normal = Vector3.new(n.X, n.Y, n.Z).Unit

	-- Grupo de colisión del personaje en el planeta (lo usa client/Experimentos/GravedadPlaneta): no choca con nada.
	local PhysicsService = game:GetService("PhysicsService")
	local grupo = Experimento.Personaje.GrupoColision
	pcall(function()
		PhysicsService:RegisterCollisionGroup(grupo)
	end)
	PhysicsService:CollisionGroupSetCollidable(grupo, "Default", false)
	PhysicsService:CollisionGroupSetCollidable(grupo, grupo, false)

	local nueva = Instance.new("Folder")
	nueva.Name = "PlanetaRedondo"
	nueva:SetAttribute("Centro", centro)
	nueva:SetAttribute("Radio", radio)
	nueva.Parent = workspace
	carpeta = nueva

	-- Aterrizar sobre la esfera, sin perder lo que ya hacían los planetas (ServicioPlanetas).
	local anterior = ServicioNaves.ObtenerEntorno()
	ServicioNaves.PonerEntorno({
		AlEntrarEnAtmosfera = anterior.AlEntrarEnAtmosfera,
		AlSuperarTecho = anterior.AlSuperarTecho,
		DestinoAterrizaje = function(jugador: Player, posicion: Vector3): CFrame?
			local propio = destinoAterrizaje(jugador, posicion)
			if propio then
				return propio
			end
			local otro = anterior.DestinoAterrizaje
			return if otro then otro(jugador, posicion) else nil
		end,
	})

	Players.PlayerAdded:Connect(function(jugador)
		jugador.CharacterAdded:Connect(function(personaje)
			alAparecer(jugador, personaje)
		end)
	end)
	for _, jugador in Players:GetPlayers() do
		jugador.CharacterAdded:Connect(function(personaje)
			alAparecer(jugador, personaje)
		end)
		if jugador.Character then
			task.spawn(alAparecer, jugador, jugador.Character)
		end
	end

	task.spawn(function()
		local Stats = game:GetService("Stats") -- aquí y no arriba: la simulación de las pruebas no lo tiene
		local memoriaAntes = Stats:GetMemoryUsageMbForTag(Enum.DeveloperMemoryTag.TerrainVoxels)
		local resumen = generar(centro, radio, normal)
		marcoPuerto = montarPuerto(nueva, centro, radio, normal)
		task.wait(1)
		local memoria = Stats:GetMemoryUsageMbForTag(Enum.DeveloperMemoryTag.TerrainVoxels)
		nueva:SetAttribute("MemoriaTerrenoAntes", memoriaAntes)
		nueva:SetAttribute("MemoriaTerreno", memoria)
		nueva:SetAttribute("Listo", true)
		listo = true
		print(
			string.format(
				"[PlanetaRedondo] Radio %d: %d losas, %d colinas, %d rocas. Colinas %.1f s, corteza %.1f s, total %.1f s. Memoria de terreno: %.0f MB (antes %.0f MB)",
				radio,
				resumen.Losas,
				resumen.Colinas,
				resumen.Rocas,
				resumen.SegundosColinas,
				resumen.SegundosCorteza,
				resumen.SegundosTotal,
				memoria,
				memoriaAntes
			)
		)
	end)
end

return PlanetaRedondo
