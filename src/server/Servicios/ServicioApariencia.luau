--!strict
--[[
	ServicioApariencia: el aspecto de los personajes (editor de personaje) en el servidor, para que lo vean todos.

	  · Remoto GuardarAparienciaHumano (ya validado por Remotos: cada opción existe y cada color es "#RRGGBB"): solo
	    si el jugador es Humano. Se vuelve a validar aquí (este método también se puede llamar desde el servidor), se
	    guarda en sus datos (Apariencia.Humano), se le reenvían y se le pone en el personaje.
	  · Cada vez que aparece un personaje (y al elegir bando) se le pone la apariencia guardada de su bando. Los
	    Humanos que aún no han pasado por el editor llevan la de por defecto.
	  · Plantillas de las piezas 3D: al arrancar se crean con AssetService:CreateMeshPartAsync en
	    ReplicatedStorage.PlantillasHumanas (de ahí las clona Personaje/Constructor, también la vista previa del
	    editor en el cliente). Cuando terminan de llegar se vuelve a vestir a todos, por si alguien apareció antes.
	  · Avatar de Roblox (solo Humanos): si el jugador lo eligió, se carga con su UserId (el cliente no manda nada del
	    avatar), se prepara para R6 (Personaje/AvatarR6: sin ropa en capas, máximo de accesorios) y se aplica con
	    ApplyDescriptionAsync. Si Roblox no responde, se visten las piezas del juego.
	  · Los Monstruos tendrán su propio editor: de momento su personaje no se toca.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Apariencia = require(ReplicatedStorage.Shared.Personaje.Apariencia)
local AvatarR6 = require(ReplicatedStorage.Shared.Personaje.AvatarR6)
local ConfigEditor = require(ReplicatedStorage.Shared.Personaje.ConfigEditor)
local Bandos = require(ReplicatedStorage.Shared.Juego.Bandos)
local Constructor = require(ReplicatedStorage.Shared.Personaje.Constructor)
local Recursos = require(ReplicatedStorage.Shared.Personaje.RecursosHumanos)
local ServicioBandos = require(script.Parent.ServicioBandos)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioRed = require(script.Parent.ServicioRed)
local ServicioReplicacion = require(script.Parent.ServicioReplicacion)

local ServicioApariencia = {}

-- Cuántas mallas se piden a la vez al crear las plantillas.
local MALLAS_A_LA_VEZ = 6

local iniciado = false

-- Avatar de Roblox de cada jugador (HumanoidDescription), pedido con su UserId la primera vez que hace falta.
local avatares: { [Player]: HumanoidDescription } = setmetatable({}, { __mode = "k" }) :: any
-- Cada vez que se viste a un jugador sube su número: un vestido que tarda (el avatar) se descarta si mientras tanto se
-- vistió otra vez, para que no pise al más nuevo.
local vestidos: { [Player]: number } = setmetatable({}, { __mode = "k" }) :: any

local function avatarDe(jugador: Player): HumanoidDescription?
	local guardado = avatares[jugador]
	if guardado then
		return guardado
	end
	local c = ConfigEditor.Avatar
	for intento = 1, c.Intentos do
		local ok, d = pcall(function()
			return Players:GetHumanoidDescriptionFromUserId(jugador.UserId)
		end)
		if ok and d then
			avatares[jugador] = d
			return d
		end
		if intento < c.Intentos then
			task.wait(c.EsperaIntento)
		end
	end
	return nil
end

-- Pone el avatar de Roblox del jugador en su personaje R6 (con lo que un R6 puede llevar, ver Personaje/AvatarR6).
local function vestirAvatar(jugador: Player, personaje: Model, numero: number): boolean
	local humanoide = personaje:FindFirstChildOfClass("Humanoid")
	if humanoide == nil or humanoide.RigType ~= Enum.HumanoidRigType.R6 then
		return false
	end
	local original = avatarDe(jugador)
	if original == nil then
		return false
	end
	local d = original:Clone()
	AvatarR6.Preparar(d, ConfigEditor.Avatar.MaxAccesorios)
	if vestidos[jugador] ~= numero or jugador.Character ~= personaje then
		return true -- ya hay otro vestido más nuevo en marcha
	end
	-- (PonerAvatar espera a Roblox: si mientras tanto se viste otra cosa, el resultado se descarta en la comprobación
	-- de después.)
	local ok = Constructor.PonerAvatar(personaje, d, function()
		return vestidos[jugador] == numero and jugador.Character == personaje
	end)
	if not ok then
		warn(`[Apariencia] No se pudo poner el avatar de {jugador.Name}`)
	end
	return ok
end

local function vestirPiezas(jugador: Player, personaje: Model, datos: any)
	local ok, err = pcall(Constructor.Aplicar, personaje, datos.Apariencia.Humano)
	if not ok then
		warn(`[Apariencia] No se pudo vestir a {jugador.Name}: {err}`)
	end
end

-- Pone en el personaje actual del jugador la apariencia de su bando (si tiene una que poner): su avatar de Roblox o las
-- piezas del juego, según lo que guardó.
function ServicioApariencia.Vestir(jugador: Player)
	local datos = ServicioDatos.ObtenerDatos(jugador)
	local personaje = jugador.Character
	if datos == nil or personaje == nil or datos.Bando ~= Bandos.Humanos then
		return
	end
	local numero = (vestidos[jugador] or 0) + 1
	vestidos[jugador] = numero
	if datos.Apariencia.UsarAvatar then
		task.spawn(function()
			if not vestirAvatar(jugador, personaje, numero) and vestidos[jugador] == numero then
				-- Sin avatar (Roblox no respondió): que no se quede sin vestir.
				vestirPiezas(jugador, personaje, datos)
			end
		end)
		return
	end
	vestirPiezas(jugador, personaje, datos)
end

--[[
	Guarda la apariencia humana del jugador. `valores`: campo -> valor (Personaje/Apariencia.Campos). Devuelve true
	si se aplicó. Rechaza lo que no exista: nada de opciones inventadas por el cliente.
]]
function ServicioApariencia.GuardarHumano(jugador: Player, valores: { [string]: any }, usarAvatar: boolean?): boolean
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil or datos.Bando ~= Bandos.Humanos then
		return false
	end
	for _, campo in Apariencia.Campos do
		if not Apariencia.ValorValido(campo, valores[campo]) then
			return false
		end
	end
	datos.Apariencia.Humano = Apariencia.Validar(valores) :: any
	datos.Apariencia.UsarAvatar = usarAvatar == true
	ServicioReplicacion.EnviarDatos(jugador)
	ServicioDatos.GuardarAhora(jugador)
	ServicioApariencia.Vestir(jugador)
	return true
end

-- ===== Plantillas de las piezas 3D =====

local function crearMalla(AssetService: any, malla: string): MeshPart?
	local ok, resultado = pcall(function()
		return AssetService:CreateMeshPartAsync(malla, {
			CollisionFidelity = Enum.CollisionFidelity.Box,
			RenderFidelity = Enum.RenderFidelity.Automatic,
		})
	end)
	if not ok then
		warn(`[Apariencia] No se pudo crear la malla {malla}: {resultado}`)
		return nil
	end
	return resultado
end

local function crearPlantillas()
	-- Sin AssetService (solo pasa en el Roblox simulado de las pruebas de Lune) no hay mallas: los personajes se
	-- visten igual, solo que sin piezas 3D.
	local okServicio, AssetService = pcall(function()
		return game:GetService("AssetService")
	end)
	if not okServicio then
		return
	end
	local carpeta = Instance.new("Folder")
	carpeta.Name = Constructor.CARPETA_PLANTILLAS
	carpeta.Parent = ReplicatedStorage

	-- Varias piezas comparten malla (por ejemplo la hebilla del cinturón): cada malla se pide una sola vez.
	local porMalla: { [string]: { Recursos.Pieza } } = {}
	local mallas: { string } = {}
	for _, piezas in Recursos.Piezas do
		for _, pieza in piezas do
			if porMalla[pieza.Malla] == nil then
				porMalla[pieza.Malla] = {}
				table.insert(mallas, pieza.Malla)
			end
			table.insert(porMalla[pieza.Malla], pieza)
		end
	end

	local siguiente = 0
	local activos = 0
	local fallos = 0
	local function trabajador()
		activos += 1
		while siguiente < #mallas do
			siguiente += 1
			local malla = mallas[siguiente]
			local base = crearMalla(AssetService, malla)
			if base == nil then
				fallos += 1
				continue
			end
			base.Anchored = false
			base.CanCollide = false
			base.CanTouch = false
			base.CanQuery = false
			base.Massless = true
			for _, pieza in porMalla[malla] do
				local p = base:Clone()
				p.Name = pieza.Nombre
				p.Size = Vector3.new(pieza.Tamano[1], pieza.Tamano[2], pieza.Tamano[3])
				p.Parent = carpeta
			end
			base:Destroy()
		end
		activos -= 1
	end
	for _ = 1, MALLAS_A_LA_VEZ do
		task.spawn(trabajador)
	end
	while activos > 0 do
		task.wait(0.1)
	end
	carpeta:SetAttribute("Completas", true)
	if fallos > 0 then
		warn(`[Apariencia] {fallos} de {#mallas} mallas no se pudieron crear`)
	end
	-- Ya están todas: se viste otra vez a quien apareció antes de que llegaran.
	for _, jugador in Players:GetPlayers() do
		ServicioApariencia.Vestir(jugador)
	end
end

-- ===== Arranque =====

local function alAparecer(jugador: Player, personaje: Model)
	-- Espera a que esté en el mundo (ServicioPersonaje puede sustituirlo por un R6 justo al aparecer).
	local limite = os.clock() + 10
	while personaje.Parent == nil and os.clock() < limite do
		task.wait()
	end
	task.wait(0.3)
	if jugador.Character == personaje then
		ServicioApariencia.Vestir(jugador)
	end
end

-- Empieza. Una vez, después de ServicioRed.Iniciar() y de ServicioBandos.Iniciar().
function ServicioApariencia.Iniciar()
	assert(not iniciado, "ServicioApariencia.Iniciar() solo debe llamarse una vez")
	iniciado = true

	task.spawn(crearPlantillas)

	ServicioRed.Conectar("GuardarAparienciaHumano", function(jugador: Player, ...: any)
		local valores = {}
		for i, campo in Apariencia.Campos do
			valores[campo] = select(i, ...)
		end
		ServicioApariencia.GuardarHumano(jugador, valores, select(#Apariencia.Campos + 1, ...) == true)
	end)

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
	ServicioDatos.DatosCargados:Conectar(ServicioApariencia.Vestir)
	ServicioBandos.BandoElegido:Conectar(function(jugador: Player)
		ServicioApariencia.Vestir(jugador)
	end)
end

return ServicioApariencia
