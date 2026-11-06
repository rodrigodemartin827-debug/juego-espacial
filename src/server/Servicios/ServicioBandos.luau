--!strict
--[[
	ServicioBandos: atiende la elección de bando del jugador (Humanos o Monstruos).

	Es el primer consumidor real de los sistemas de red y de datos, y sirve de ejemplo de cómo escribir
	un servicio:
	  - Recibe la petición por ServicioRed.Conectar. Cuando el manejador se ejecuta, el remoto ya ha pasado
	    el límite por segundo y la validación (el bando es "Humanos" o "Monstruos"), pero la lógica de la
	    partida sigue siendo cosa del manejador: ¿tiene ya bando? ¿han cargado sus datos?
	  - Modifica directamente los datos que devuelve ServicioDatos.ObtenerDatos.
	  - Avisa al cliente con ServicioReplicacion y guarda de inmediato, porque elegir bando es una decisión
	    que no debe perderse si el servidor falla.

	Regla actual: el bando se elige una sola vez y no se puede cambiar. (El cambio de pago, una vez cada 7 días,
	irá en su propio servicio y no por este remoto.)

	PANTALLA DE ELECCIÓN. Mientras el jugador no tiene bando, su cliente le enseña la pantalla de elección
	(client/Eleccion) con la cámara lejos de su personaje. Para que nadie se aproveche de ese rato, el servidor:
	  - le pone el atributo Eleccion/Config.AtributoEligiendo en el Player (el combate no le deja usar habilidades,
	    y su cliente sabe que está eligiendo),
	  - ancla el HumanoidRootPart de su personaje (no se puede mover aunque el cliente esté manipulado), y
	  - le da un ForceField invisible (nadie le puede hacer daño mientras no mira).
	Todo se quita en cuanto elige. Si reaparece antes de elegir, se aplica al personaje nuevo.

	Cuando un jugador elige, se dispara `BandoElegido` (jugador, bando): ahí se engancha lo que empieza después de
	elegir, como el tutorial del planeta de su bando.

	SOLO EN STUDIO: escribiendo en el chat el comando Eleccion/Config.ComandoReiniciarBando (/reiniciarbando), el
	bando del jugador vuelve a "Ninguno" en los datos de prueba de Studio y la pantalla de elección sale otra vez.
	Fuera de Studio el comando ni siquiera se crea, y ReiniciarParaPruebas se niega.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage.Shared
local Bandos = require(Shared.Juego.Bandos)
local ConfigEleccion = require(Shared.Eleccion.Config)
local Senal = require(Shared.Utilidades.Senal)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioRed = require(script.Parent.ServicioRed)
local ServicioReplicacion = require(script.Parent.ServicioReplicacion)

local ServicioBandos = {}

-- Se dispara (jugador, bando) cuando un jugador elige bando por primera vez, ya guardado en sus datos.
ServicioBandos.BandoElegido = Senal.nueva()

-- Segundos que se espera a que el personaje recién aparecido tenga su HumanoidRootPart.
local ESPERA_PERSONAJE = 10

-- Personajes que este servicio ha anclado (para no desanclar lo que anclara otro sistema).
local anclados: { [Model]: BasePart } = setmetatable({}, { __mode = "k" }) :: any
local iniciado = false

-- ¿Está el jugador en la pantalla de elección? (datos cargados y sin bando)
function ServicioBandos.EstaEligiendo(jugador: Player): boolean
	local datos = ServicioDatos.ObtenerDatos(jugador)
	return datos ~= nil and datos.Bando == Bandos.Ninguno
end

-- ===== Protección mientras elige =====

local function protegerPersonaje(personaje: Model)
	if personaje:FindFirstChild(ConfigEleccion.NombreProteccion) == nil then
		local escudo = Instance.new("ForceField")
		escudo.Name = ConfigEleccion.NombreProteccion
		escudo.Visible = false
		escudo.Parent = personaje
	end
	local raiz = personaje:FindFirstChild("HumanoidRootPart")
	if raiz ~= nil and raiz:IsA("BasePart") and not raiz.Anchored then
		raiz.Anchored = true
		anclados[personaje] = raiz
	end
end

local function desprotegerPersonaje(personaje: Model)
	local escudo = personaje:FindFirstChild(ConfigEleccion.NombreProteccion)
	if escudo ~= nil then
		escudo:Destroy()
	end
	local raiz: BasePart? = anclados[personaje]
	if raiz ~= nil then
		anclados[personaje] = nil
		raiz.Anchored = false
	end
end

-- Pone o quita la protección del jugador y de su personaje actual según si está eligiendo.
local function actualizarProteccion(jugador: Player)
	local eligiendo = ServicioBandos.EstaEligiendo(jugador)
	jugador:SetAttribute(ConfigEleccion.AtributoEligiendo, if eligiendo then true else nil)
	local personaje = jugador.Character
	if personaje == nil then
		return
	end
	if eligiendo then
		protegerPersonaje(personaje)
	else
		desprotegerPersonaje(personaje)
	end
end

-- Un personaje nuevo (aparición o reaparición): si su jugador sigue eligiendo, se protege en cuanto tiene raíz.
local function alAparecerPersonaje(jugador: Player, personaje: Model)
	personaje:WaitForChild("HumanoidRootPart", ESPERA_PERSONAJE)
	if jugador.Character ~= personaje then
		return -- lo sustituyeron mientras tanto (p. ej. ServicioPersonaje lo cambió por un R6)
	end
	if ServicioBandos.EstaEligiendo(jugador) then
		protegerPersonaje(personaje)
	end
end

local function alEntrarJugador(jugador: Player)
	jugador.CharacterAdded:Connect(function(personaje: Model)
		alAparecerPersonaje(jugador, personaje)
	end)
end

-- ===== Elección =====

--[[
	Asigna el bando al jugador si todavía no tiene. Lo usa el remoto ElegirBando y la zona de pruebas.
	Devuelve true si se aplicó. Se vuelve a comprobar el bando aunque el remoto ya lo valide: este método también se
	llama desde otros sitios del servidor.
]]
function ServicioBandos.Elegir(jugador: Player, bando: Bandos.IdBando): boolean
	if not Bandos.EsElegible(bando) then
		return false -- "Ninguno" o un bando que no existe
	end
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return false -- sus datos todavía no han cargado: no hay dónde guardar la elección
	end
	if datos.Bando ~= Bandos.Ninguno then
		return false -- ya eligió bando
	end

	datos.Bando = bando
	actualizarProteccion(jugador)
	ServicioReplicacion.EnviarDatos(jugador)
	ServicioDatos.GuardarAhora(jugador)
	ServicioBandos.BandoElegido:Disparar(jugador, bando)
	return true
end

-- ===== Solo para pruebas en Studio =====

--[[
	Devuelve al jugador a "sin bando" para volver a ver la pantalla de elección. Solo funciona en Studio (los datos
	de Studio van en su propio almacén, ver ServicioDatos), así que nunca toca a jugadores del juego publicado.
	Devuelve true si se aplicó.
]]
function ServicioBandos.ReiniciarParaPruebas(jugador: Player): boolean
	if not RunService:IsStudio() then
		return false
	end
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return false
	end
	datos.Bando = Bandos.Ninguno
	actualizarProteccion(jugador) -- vuelve a quedar quieto y protegido mientras elige
	ServicioReplicacion.EnviarDatos(jugador) -- su cliente ve "Ninguno" y vuelve a montar la pantalla
	ServicioDatos.GuardarAhora(jugador)
	print(`[Bandos] {jugador.Name}: bando reiniciado a {Bandos.Ninguno} (solo Studio)`)
	return true
end

-- Crea el comando de chat que llama a ReiniciarParaPruebas. Solo se llama en Studio.
local function crearComandoPruebas()
	local TextChatService = game:GetService("TextChatService")
	local comando = Instance.new("TextChatCommand")
	comando.Name = "ReiniciarBando"
	comando.PrimaryAlias = ConfigEleccion.ComandoReiniciarBando
	comando.Triggered:Connect(function(origen: TextSource, _texto: string)
		local jugador = Players:GetPlayerByUserId(origen.UserId)
		if jugador ~= nil then
			ServicioBandos.ReiniciarParaPruebas(jugador)
		end
	end)
	comando.Parent = TextChatService
end

-- Empieza a atender el remoto ElegirBando. Debe llamarse una sola vez, después de ServicioRed.Iniciar() y antes de
-- ServicioDatos.Iniciar() (para no perderse a los jugadores cuyos datos cargan nada más arrancar).
function ServicioBandos.Iniciar()
	assert(not iniciado, "ServicioBandos.Iniciar() solo debe llamarse una vez")
	iniciado = true

	ServicioRed.Conectar("ElegirBando", function(jugador: Player, bando: Bandos.IdBando)
		ServicioBandos.Elegir(jugador, bando)
	end)

	-- Al cargar sus datos se sabe si tiene bando: si no, se le protege mientras elige. En Studio, con el modo de
	-- pruebas (ConfigEleccion.ElegirBandoSiempreEnStudio), el bando vuelve a «Ninguno» para elegir cada vez.
	ServicioDatos.DatosCargados:Conectar(function(jugador: Player)
		local datos = ServicioDatos.ObtenerDatos(jugador)
		if
			RunService:IsStudio()
			and ConfigEleccion.ElegirBandoSiempreEnStudio
			and datos ~= nil
			and datos.Bando ~= Bandos.Ninguno
		then
			ServicioBandos.ReiniciarParaPruebas(jugador)
			return
		end
		actualizarProteccion(jugador)
	end)

	Players.PlayerAdded:Connect(alEntrarJugador)
	for _, jugador in Players:GetPlayers() do
		alEntrarJugador(jugador)
	end

	if RunService:IsStudio() then
		crearComandoPruebas()
	end
end

return ServicioBandos
