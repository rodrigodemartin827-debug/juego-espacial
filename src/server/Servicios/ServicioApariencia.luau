--!strict
--[[
	ServicioApariencia: el aspecto de los personajes (editor de personaje) en el servidor, para que lo vean todos.

	  · Remoto GuardarAparienciaHumano (ya validado: cada argumento es una opción que existe): solo si el jugador es
	    Humano. Se guarda en sus datos (Apariencia.Humano), se le reenvían y se le pone en el personaje.
	  · Cada vez que aparece un personaje (y al elegir bando) se le pone la apariencia guardada de su bando. Los
	    Humanos que aún no han pasado por el editor llevan la de por defecto.
	  · Los Monstruos tendrán su propio editor: de momento su personaje no se toca.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Apariencia = require(ReplicatedStorage.Shared.Personaje.Apariencia)
local Bandos = require(ReplicatedStorage.Shared.Juego.Bandos)
local Constructor = require(ReplicatedStorage.Shared.Personaje.Constructor)
local ServicioBandos = require(script.Parent.ServicioBandos)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioRed = require(script.Parent.ServicioRed)
local ServicioReplicacion = require(script.Parent.ServicioReplicacion)

local ServicioApariencia = {}

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

-- Guarda la apariencia humana del jugador. Devuelve true si se aplicó.
function ServicioApariencia.GuardarHumano(jugador: Player, valores: { [string]: string }): boolean
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil or datos.Bando ~= Bandos.Humanos then
		return false
	end
	for _, campo in Apariencia.Campos do
		if Apariencia.Buscar(campo, valores[campo]) == nil then
			return false
		end
	end
	datos.Apariencia.Humano = Apariencia.Validar(valores) :: any
	ServicioReplicacion.EnviarDatos(jugador)
	ServicioDatos.GuardarAhora(jugador)
	ServicioApariencia.Vestir(jugador)
	return true
end

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
