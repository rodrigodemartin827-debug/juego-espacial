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
	  · Los Monstruos tendrán su propio editor: de momento su personaje no se toca.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Apariencia = require(ReplicatedStorage.Shared.Personaje.Apariencia)
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

-- Pone en el personaje actual del jugador la apariencia de su bando (si tiene una que poner).
function ServicioApariencia.Vestir(jugador: Player)
	local datos = ServicioDatos.ObtenerDatos(jugador)
	local personaje = jugador.Character
	if datos == nil or personaje == nil or datos.Bando ~= Bandos.Humanos then
		return
	end
	local ok, err = pcall(Constructor.Aplicar, personaje, datos.Apariencia.Humano)
	if not ok then
		warn(`[Apariencia] No se pudo vestir a {jugador.Name}: {err}`)
	end
end

--[[
	Guarda la apariencia humana del jugador. `valores`: campo -> valor (Personaje/Apariencia.Campos). Devuelve true
	si se aplicó. Rechaza lo que no exista: nada de opciones inventadas por el cliente.
]]
function ServicioApariencia.GuardarHumano(jugador: Player, valores: { [string]: any }): boolean
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

	ServicioRed.Conectar("GuardarAparienciaHumano", function(jugador: Player, ...: string)
		local valores = {}
		for i, campo in Apariencia.Campos do
			valores[campo] = select(i, ...)
		end
		ServicioApariencia.GuardarHumano(jugador, valores)
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
