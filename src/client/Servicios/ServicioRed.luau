--!strict
--[[
	ServicioRed (cliente)

	Contraparte del ServicioRed del servidor. Localiza los RemoteEvents que el servidor ha creado a
	partir de la lista compartida (Red/Remotos) y ofrece dos operaciones:

	  - Enviar:   pide algo al servidor (remotos ClienteAServidor).
	  - Conectar: escucha los avisos del servidor (remotos ServidorACliente).

	Antes de enviar, el cliente aplica los mismos validadores y el mismo límite por segundo que hará
	cumplir el servidor. No es una medida de seguridad (un tramposo se la salta, y por eso el servidor
	lo vuelve a comprobar todo), sino de cortesía: un cliente legítimo nunca provoca infracciones y se
	ahorra tráfico inútil.

	Uso:
	  ServicioRed.Iniciar()                                  -- una sola vez, al arrancar el cliente
	  ServicioRed.Enviar("ElegirBando", "Humanos")
	  ServicioRed.Conectar("DatosJugador", function(datos) ... end)
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Se espera a que Roblox replique la carpeta compartida antes de requerir módulos de ella.
ReplicatedStorage:WaitForChild("Shared")
local Shared = ReplicatedStorage.Shared
local LimitadorDeTasa = require(Shared.Red.LimitadorDeTasa)
local Remotos = require(Shared.Red.Remotos)
local Validador = require(Shared.Red.Validador)

-- El cliente solo limita al jugador local, así que usa una única clave para su cubo de fichas.
local CLAVE_LOCAL = "jugador-local"

local ServicioRed = {}

local iniciado = false
local eventos: { [string]: RemoteEvent } = {}
local limitadores: { [string]: LimitadorDeTasa.LimitadorDeTasa } = {}

-- Devuelve el RemoteEvent de `nombre` comprobando que existe y que va en la dirección esperada.
local function obtenerEvento(nombre: string, direccion: Remotos.Direccion): RemoteEvent
	local definicion = Remotos.Definiciones[nombre]
	assert(definicion ~= nil, `El remoto '{nombre}' no está definido en Red/Remotos`)
	assert(
		definicion.Direccion == direccion,
		`El remoto '{nombre}' es {definicion.Direccion}, y aquí se esperaba {direccion}`
	)

	local evento = eventos[nombre]
	assert(evento ~= nil, "ServicioRed.Iniciar() todavía no ha terminado")
	return evento
end

--[[
	Busca los RemoteEvents. Debe llamarse una sola vez, al arrancar el cliente. Espera (puede tardar
	unos instantes) a que el servidor los haya creado y publicado.
]]
function ServicioRed.Iniciar()
	assert(not iniciado, "ServicioRed.Iniciar() solo debe llamarse una vez")
	iniciado = true

	-- El servidor publica la carpeta cuando ya tiene dentro todos los eventos.
	local carpeta = ReplicatedStorage:WaitForChild(Remotos.NOMBRE_CARPETA)

	for nombre, definicion in Remotos.Definiciones do
		eventos[nombre] = carpeta:WaitForChild(nombre) :: RemoteEvent

		if definicion.Direccion == "ClienteAServidor" then
			limitadores[nombre] =
				LimitadorDeTasa.nuevo(definicion.LimitePorSegundo or Remotos.LIMITE_POR_DEFECTO, definicion.Rafaga)
		end
	end
end

--[[
	Envía una petición al servidor por un remoto ClienteAServidor.

	Devuelve `true` si se ha enviado. Devuelve `false` (y no envía nada) si los argumentos no pasan
	la validación, o si se está enviando más deprisa de lo que permite el límite del remoto.
]]
function ServicioRed.Enviar(nombre: string, ...: any): boolean
	local evento = obtenerEvento(nombre, "ClienteAServidor")
	local definicion = Remotos.Definiciones[nombre]

	-- Primero se valida, para que una llamada incorrecta no gaste fichas del límite.
	local valido, motivo = Validador.ValidarArgumentos(definicion.Argumentos or {}, ...)
	if not valido then
		warn(`[Red] No se envía '{nombre}': {motivo}`)
		return false
	end

	if not limitadores[nombre]:Permitir(CLAVE_LOCAL) then
		return false
	end

	evento:FireServer(...)
	return true
end

-- Escucha un remoto ServidorACliente. Devuelve la conexión, para poder desconectarla.
function ServicioRed.Conectar(nombre: string, manejador: (...any) -> ()): RBXScriptConnection
	return obtenerEvento(nombre, "ServidorACliente").OnClientEvent:Connect(manejador)
end

return ServicioRed
