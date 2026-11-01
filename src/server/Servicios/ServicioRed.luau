--!strict
--[[
	ServicioRed (servidor)

	Es el único punto de entrada de las peticiones del cliente. Crea los RemoteEvents a partir de la
	lista compartida (Red/Remotos) y, por cada petición que recibe, hace en este orden:

	  1. Límite de peticiones por segundo, por jugador y por remoto (cubo de fichas).
	  2. Validación de los argumentos con los validadores declarados en la definición del remoto.
	  3. Llamada al manejador registrado con `Conectar`, protegida para que un error en la lógica del
	     juego no afecte al resto de peticiones.

	Las peticiones que fallan el paso 1 o el 2 se descartan en silencio (no se le responde nada al
	cliente, para no dar pistas a un tramposo) y cuentan como "infracciones". Si un jugador acumula
	demasiadas en poco tiempo, se le expulsa.

	El cliente NO es de confianza: los argumentos pueden tener cualquier tipo, valor o cantidad. Cuando
	el manejador se ejecuta, la FORMA de los argumentos ya está garantizada, pero comprobar que la
	acción tiene sentido en la partida (tiene monedas, está a tiro...) sigue siendo cosa del manejador.

	Uso:
	  ServicioRed.Iniciar()                                  -- una sola vez, al arrancar el servidor
	  ServicioRed.Conectar("ElegirBando", function(jugador, bando) ... end)
	  ServicioRed.EnviarACliente(jugador, "DatosJugador", datos)
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local LimitadorDeTasa = require(Shared.Red.LimitadorDeTasa)
local Remotos = require(Shared.Red.Remotos)
local Validador = require(Shared.Red.Validador)

export type Manejador = (jugador: Player, ...any) -> ()

--[[
	Política contra abusos: si un jugador acumula MAX_INFRACCIONES peticiones descartadas (por exceso
	de ritmo o por argumentos no válidos) dentro de una ventana de VENTANA_INFRACCIONES segundos, se le
	expulsa. Un cliente sin manipular nunca envía argumentos inválidos y se limita a sí mismo, así que
	estos valores solo afectan a clientes manipulados. Con MAX_INFRACCIONES = math.huge no se expulsa a
	nadie (las peticiones se siguen descartando).
]]
local MAX_INFRACCIONES = 30
local VENTANA_INFRACCIONES = 10

type Infracciones = {
	Inicio: number, -- instante en que empezó la ventana actual
	Cuenta: number, -- infracciones dentro de la ventana
	Expulsado: boolean, -- ya se ha ordenado su expulsión: se ignora todo lo que envíe
}

local ServicioRed = {}

local iniciado = false
local eventos: { [string]: RemoteEvent } = {}
local limitadores: { [string]: LimitadorDeTasa.LimitadorDeTasa } = {}
local manejadores: { [string]: Manejador } = {}
local infracciones: { [number]: Infracciones } = {} -- por UserId

-- Anota una petición descartada y expulsa al jugador si se pasa de la raya.
local function registrarInfraccion(jugador: Player, nombre: string, motivo: string)
	local ahora = os.clock()
	local registro = infracciones[jugador.UserId]

	if registro == nil or ahora - registro.Inicio > VENTANA_INFRACCIONES then
		registro = { Inicio = ahora, Cuenta = 0, Expulsado = false }
		infracciones[jugador.UserId] = registro
		-- Solo se avisa en la primera infracción de cada ventana, para no inundar la consola
		-- cuando alguien envía miles de peticiones por segundo.
		warn(`[Red] Petición '{nombre}' de {jugador.Name} descartada: {motivo}`)
	end

	registro.Cuenta += 1
	if registro.Cuenta >= MAX_INFRACCIONES then
		registro.Expulsado = true
		warn(`[Red] {jugador.Name} expulsado por exceso de peticiones inválidas`)
		jugador:Kick("Se detectó actividad de red anómala.")
	end
end

-- Pasa una petición del cliente por los tres filtros (límite, validación, manejador).
local function procesarPeticion(nombre: string, jugador: Player, ...: any)
	-- El jugador ya se fue o lo están expulsando: no hay nada que atender.
	local registro = infracciones[jugador.UserId]
	if jugador.Parent == nil or (registro ~= nil and registro.Expulsado) then
		return
	end

	-- 1) Límite de peticiones por segundo.
	if not limitadores[nombre]:Permitir(jugador.UserId) then
		registrarInfraccion(jugador, nombre, "demasiadas peticiones por segundo")
		return
	end

	-- 2) Validación de los argumentos.
	local definicion = Remotos.Definiciones[nombre]
	local valido, motivo = Validador.ValidarArgumentos(definicion.Argumentos or {}, ...)
	if not valido then
		registrarInfraccion(jugador, nombre, motivo or "argumentos no válidos")
		return
	end

	-- 3) Manejador. Si nadie lo ha registrado todavía (el servidor está arrancando), se descarta.
	local manejador = manejadores[nombre]
	if manejador == nil then
		warn(`[Red] Petición '{nombre}' de {jugador.Name} ignorada: no hay manejador registrado`)
		return
	end

	local ejecutado, errorManejador = xpcall(manejador, debug.traceback, jugador, ...)
	if not ejecutado then
		warn(`[Red] Error en el manejador de '{nombre}' (jugador {jugador.Name}):\n{errorManejador}`)
	end
end

-- Devuelve el RemoteEvent de `nombre` comprobando que existe y que va en la dirección esperada.
local function obtenerEvento(nombre: string, direccion: Remotos.Direccion): RemoteEvent
	local definicion = Remotos.Definiciones[nombre]
	assert(definicion ~= nil, `El remoto '{nombre}' no está definido en Red/Remotos`)
	assert(
		definicion.Direccion == direccion,
		`El remoto '{nombre}' es {definicion.Direccion}, y aquí se esperaba {direccion}`
	)

	local evento = eventos[nombre]
	assert(evento ~= nil, "ServicioRed.Iniciar() todavía no se ha ejecutado")
	return evento
end

--[[
	Crea los RemoteEvents y empieza a atender al cliente. Debe llamarse una sola vez, al arrancar el
	servidor y antes de registrar los manejadores.
]]
function ServicioRed.Iniciar()
	assert(not iniciado, "ServicioRed.Iniciar() solo debe llamarse una vez")
	iniciado = true

	local carpeta = Instance.new("Folder")
	carpeta.Name = Remotos.NOMBRE_CARPETA

	for nombre, definicion in Remotos.Definiciones do
		local evento = Instance.new("RemoteEvent")
		evento.Name = nombre
		evento.Parent = carpeta
		eventos[nombre] = evento

		if definicion.Direccion == "ClienteAServidor" then
			-- Obligamos a declarar los argumentos para que nunca se olvide validarlos.
			assert(
				definicion.Argumentos ~= nil,
				`El remoto '{nombre}' debe declarar Argumentos (usa una lista vacía si no lleva ninguno)`
			)

			limitadores[nombre] = LimitadorDeTasa.nuevo(
				definicion.LimitePorSegundo or Remotos.LIMITE_POR_DEFECTO,
				definicion.Rafaga
			)
			evento.OnServerEvent:Connect(function(jugador: Player, ...: any)
				procesarPeticion(nombre, jugador, ...)
			end)
		end
	end

	-- Libera la memoria de los jugadores que se van.
	Players.PlayerRemoving:Connect(function(jugador: Player)
		for _, limitador in limitadores do
			limitador:Olvidar(jugador.UserId)
		end
		infracciones[jugador.UserId] = nil
	end)

	-- La carpeta se publica al final, ya con todos los eventos dentro: así los clientes que la
	-- esperan la encuentran siempre completa.
	carpeta.Parent = ReplicatedStorage
end

--[[
	Registra la función que atiende un remoto ClienteAServidor. Solo puede haber un manejador por
	remoto. Recibe el jugador y los argumentos, que ya han pasado el límite y la validación.
]]
function ServicioRed.Conectar(nombre: string, manejador: Manejador)
	obtenerEvento(nombre, "ClienteAServidor")
	assert(manejadores[nombre] == nil, `El remoto '{nombre}' ya tiene un manejador`)
	manejadores[nombre] = manejador
end

-- Envía un mensaje a un jugador por un remoto ServidorACliente.
function ServicioRed.EnviarACliente(jugador: Player, nombre: string, ...: any)
	obtenerEvento(nombre, "ServidorACliente"):FireClient(jugador, ...)
end

-- Envía un mensaje a todos los jugadores por un remoto ServidorACliente.
function ServicioRed.EnviarATodos(nombre: string, ...: any)
	obtenerEvento(nombre, "ServidorACliente"):FireAllClients(...)
end

return ServicioRed
