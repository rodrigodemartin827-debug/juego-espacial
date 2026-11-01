--!strict
--[[
	Remotos: lista central de todos los RemoteEvents del juego.

	Es la única fuente de verdad de la red: el servidor crea los RemoteEvents a partir de esta lista
	(ServicioRed.Iniciar), el cliente los busca por su nombre y ambos usan los mismos validadores.
	Para añadir un remoto nuevo basta con declararlo aquí.

	Cada definición tiene:
	  - Direccion: "ClienteAServidor" (el cliente pide algo) o "ServidorACliente" (el servidor avisa).
	  - LimitePorSegundo: (solo ClienteAServidor) peticiones por segundo que se aceptan por jugador.
	    Si se omite, se usa LIMITE_POR_DEFECTO.
	  - Rafaga: (solo ClienteAServidor) peticiones seguidas que se toleran de golpe. Por defecto, igual
	    a LimitePorSegundo. Súbela en acciones que puedan agruparse por la latencia, como disparar.
	  - Argumentos: (obligatorio en ClienteAServidor) lista de validadores, uno por argumento. Si el
	    remoto no recibe argumentos, pon una lista vacía: {}.

	Solo se usan RemoteEvents. No se usan RemoteFunctions: el servidor nunca debe esperar la respuesta
	de un cliente, porque un tramposo puede dejar la llamada colgada para siempre.
]]

local Bandos = require(script.Parent.Parent.Juego.Bandos)
local Validador = require(script.Parent.Validador)

export type Direccion = "ClienteAServidor" | "ServidorACliente"

export type Definicion = {
	Direccion: Direccion,
	LimitePorSegundo: number?,
	Rafaga: number?,
	Argumentos: { Validador.Validador }?,
}

local Remotos = {}

-- Nombre de la carpeta de ReplicatedStorage donde el servidor crea los RemoteEvents.
Remotos.NOMBRE_CARPETA = "Remotos"

-- Límite por segundo para los remotos ClienteAServidor que no indican uno propio.
Remotos.LIMITE_POR_DEFECTO = 10

local definiciones: { [string]: Definicion } = {
	-- El jugador elige su bando. Solo se acepta una vez (lo comprueba ServicioBandos).
	ElegirBando = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 1,
		Argumentos = { Validador.Enumeracion(Bandos.Elegibles) },
	},

	-- El servidor envía al cliente una copia de sus datos al cargarlos y cuando cambian.
	DatosJugador = {
		Direccion = "ServidorACliente",
	},

	-- El cliente pide una copia de sus datos. Lo hace al arrancar, por si el servidor ya los había
	-- enviado antes de que el cliente estuviera escuchando (los remotos no guardan mensajes).
	PedirDatos = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 2,
		Argumentos = {},
	},
}

-- Se congela la lista (dos niveles) para que ningún script la modifique por accidente.
for _, definicion in definiciones do
	if definicion.Argumentos ~= nil then
		table.freeze(definicion.Argumentos)
	end
	table.freeze(definicion)
end
Remotos.Definiciones = table.freeze(definiciones)

return Remotos
