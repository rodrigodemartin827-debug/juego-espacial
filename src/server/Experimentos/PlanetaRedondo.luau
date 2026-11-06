--!strict
--[[
	EXPERIMENTO (servidor): Nueva Tierra como esfera de Terrain. Ver shared/Experimentos/PlanetaRedondo.

	  - Al arrancar, primero monta el puerto (un hangar normal, girado para que su suelo sea tangente a la esfera) y
	    la región 1: así se puede aparecer en menos de un segundo.
	  - Después, el Terrain esférico (TerrenoPlaneta): normalmente ya viene horneado en el lugar; si no, se genera
	    (casi un minuto) y se avisa.
	  - En Studio, cada vez que aparece el personaje lo lleva al puerto.
	  - Aterrizar (F) cerca del suelo deja la nave aparcada ahí mismo, posada sobre la esfera, y baja al piloto a su
	    lado. Al usarla ("Despegar") se despega desde ese punto.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Experimento = require(ReplicatedStorage.Shared.Experimentos.PlanetaRedondo)
local Espacio = require(ReplicatedStorage.Shared.Planetas.Espacio)
local Servicios = script.Parent.Parent.Servicios
local Hangar = require(Servicios.Hangar)
local ServicioDatos = require(Servicios.ServicioDatos)
local ServicioNaves = require(Servicios.ServicioNaves)
local Modelo = require(Servicios.ServicioNaves.Modelo)
local TerrenoPlaneta = require(script.Parent.TerrenoPlaneta)

local PlanetaRedondo = {}

-- Se puede aparecer en cuanto están el puerto y la región 1. El Terrain puede llegar después (si no estaba horneado
-- en el lugar): el personaje pisa mientras tanto la capa de colisión fija de la región (su mapa de alturas).
local listoAparicion = false
-- Donde aparece el jugador si se ha montado la región 1 (delante de su casa de Pradoverde). nil = el puerto.
local marcoAparicion: CFrame? = nil
local carpeta: Folder? = nil
local marcoPuerto: CFrame? = nil

--[[
	PRUEBA (rama prueba/region1-valle-alba): si en ReplicatedStorage están la región 1 y sus piezas importadas
	(Region1, ver modelos/region1_valle_del_alba/roblox), se monta sobre este planeta y el jugador aparece en
	Experimento.Region1.Aparicion (delante de su casa de Pradoverde). Los datos están en coordenadas del planeta.
]]
local function montarRegion1()
	local ajustes = Experimento.Region1
	local raiz = ReplicatedStorage:FindFirstChild("Region1")
	if not ajustes.Activa or raiz == nil then
		return
	end
	local piezas = raiz:FindFirstChild("Piezas")
	if piezas == nil or #piezas:GetChildren() == 0 then
		warn("[PlanetaRedondo] La región 1 no tiene piezas importadas: no se monta")
		return
	end
	local ok, err = pcall(function()
		local datos = raiz:WaitForChild("Datos")
		local ids = require(datos:WaitForChild("ids_texturas") :: ModuleScript) :: any
		local origen = CFrame.new(Experimento.Centro())
		local inicio = os.clock()
		local region = (require(raiz:WaitForChild("EjemploArranque") :: ModuleScript) :: any).montarEnStudio(
			ids[ajustes.Atlas],
			ids,
			origen
		)
		-- Toda la región llega siempre al cliente: su LOD (LodRegion) necesita tener todos los modelos.
		region.ModelStreamingMode = Enum.ModelStreamingMode.Persistent
		-- Aparición: delante de la casa elegida, en su vertical, a la altura del suelo (la colisión del terreno es fiable).
		for _, g in require(datos:WaitForChild(ajustes.Grupo) :: ModuleScript) :: any do
			if g.nombre == ajustes.Edificio then
				local c = g.cframe
				local marcoEdificio = origen
					* CFrame.new(c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], c[11], c[12])
				local d = ajustes.Delante
				local punto = marcoEdificio * CFrame.new(d[1], d[2], d[3])
				local arriba = (punto.Position - origen.Position).Unit
				local parametros = RaycastParams.new()
				parametros.FilterType = Enum.RaycastFilterType.Include
				parametros.FilterDescendantsInstances = { region:FindFirstChild("Terreno") :: Instance }
				local suelo = workspace:Raycast(punto.Position + arriba * 50, -arriba * 150, parametros)
				local base = if suelo then suelo.Position else punto.Position
				-- Mirando hacia la casa (su fachada con la puerta mira a +Z del edificio).
				local haciaCasa = marcoEdificio.Position + marcoEdificio.RightVector * d[1] - base
				marcoAparicion = Experimento.Marco(base + arriba * 3.2, arriba, haciaCasa)
			end
		end
		print(string.format("[PlanetaRedondo] Región 1 montada en %.1f s", os.clock() - inicio))
	end)
	if not ok then
		warn(`[PlanetaRedondo] No se pudo montar la región 1: {err}`)
	end
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
	local destino: CFrame
	if marcoAparicion then
		destino = marcoAparicion :: CFrame
	else
		local marco = marcoPuerto
		if marco == nil then
			return
		end
		-- Delante de la boca del hangar (que se abre hacia -Z), mirando hacia fuera (de espaldas al hangar).
		destino = marco * CFrame.new(0, 3.2, -40)
	end
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
	while not listoAparicion do
		task.wait(0.2)
	end
	-- Solo los de este planeta (y quien aún no ha elegido bando: elige aquí, quieto, y si elige este planeta ya está
	-- en su sitio). Los del otro bando aparecen en su superficie plana: los coloca ServicioPlanetas.
	local datos = ServicioDatos.ObtenerDatos(jugador)
	local limiteDatos = os.clock() + 15
	while datos == nil and os.clock() < limiteDatos and jugador.Parent ~= nil do
		task.wait(0.25)
		datos = ServicioDatos.ObtenerDatos(jugador)
	end
	local planeta = if datos then Espacio.PlanetaDeBando(datos.Bando) else nil
	if planeta ~= nil and planeta ~= Experimento.Planeta then
		return
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
	local parametros = TerrenoPlaneta.parametros()
	local centro, radio, normal = parametros.centro, parametros.radio, parametros.normalPuerto

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
		local inicio = os.clock()
		-- Primero lo que hace falta para aparecer (menos de un segundo): el puerto y la región 1.
		marcoPuerto = montarPuerto(nueva, centro, radio, normal)
		montarRegion1()
		listoAparicion = true
		nueva:SetAttribute("ListoAparicion", true)
		print(string.format("[PlanetaRedondo] Listo para aparecer en %.1f s", os.clock() - inicio))

		-- Después, el Terrain: normalmente ya viene horneado en el lugar (TerrenoPlaneta.hornearEnStudio).
		local Stats = game:GetService("Stats") -- aquí y no arriba: la simulación de las pruebas no lo tiene
		if TerrenoPlaneta.yaGenerado(parametros) then
			print("[PlanetaRedondo] Terreno ya horneado en el lugar: no se genera")
		else
			warn(
				"[PlanetaRedondo] El terreno no está horneado en el lugar (o sus ajustes han cambiado): se genera ahora y "
					.. "tarda casi un minuto. En Studio: require(game.ServerScriptService.Server.Experimentos.TerrenoPlaneta)"
					.. ".hornearEnStudio(true) y guardar el lugar."
			)
			local memoriaAntes = Stats:GetMemoryUsageMbForTag(Enum.DeveloperMemoryTag.TerrainVoxels)
			local resumen = TerrenoPlaneta.generar(parametros)
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
					Stats:GetMemoryUsageMbForTag(Enum.DeveloperMemoryTag.TerrainVoxels),
					memoriaAntes
				)
			)
		end
		nueva:SetAttribute("MemoriaTerreno", Stats:GetMemoryUsageMbForTag(Enum.DeveloperMemoryTag.TerrainVoxels))
		nueva:SetAttribute("Listo", true)
	end)
end

return PlanetaRedondo
