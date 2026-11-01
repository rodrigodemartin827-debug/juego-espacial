--!strict
--[[
	BloqueoSesion: las reglas del "bloqueo de sesión" de los datos de un jugador.

	EL PROBLEMA
	Un jugador puede estar en dos servidores a la vez durante unos instantes: al saltar de servidor,
	al reconectar tras una caída, con la cuenta abierta dos veces... Si los dos cargan sus datos y
	los guardan, el último en guardar pisa al otro: se pierde progreso o, peor, se duplican objetos.

	LA SOLUCIÓN
	Cada registro del DataStore lleva un "bloqueo" que dice qué sesión lo está usando:

	  1. Para cargar los datos, un servidor tiene que TOMAR el bloqueo. Si lo tiene otro servidor
	     (que sigue vivo), no puede: espera y lo reintenta.
	  2. Mientras el jugador está en el servidor, éste guarda cada cierto tiempo y refresca la marca
	     `UltimaActividad` del bloqueo para demostrar que sigue vivo.
	  3. Cada guardado COMPRUEBA que el bloqueo sigue siendo suyo. Si no lo es, no escribe nada: el
	     servidor que perdió el bloqueo nunca puede pisar los datos del que lo tiene.
	  4. Cuando el jugador se va, el servidor guarda y LIBERA el bloqueo.
	  5. Si un servidor se cae sin liberar, el bloqueo queda abandonado. Pasados `Caducidad`
	     segundos sin refrescarse, cualquier servidor puede tomarlo.

	Este módulo solo contiene las DECISIONES, como funciones sobre el registro. Están hechas para
	ejecutarse DENTRO de la función de transformación de `UpdateAsync`, que Roblox ejecuta de forma
	atómica (nadie más escribe esa clave a la vez) y que no puede ceder el hilo ni tener efectos
	secundarios: puede llamarse varias veces si hay conflicto. Por eso estas funciones no hacen más
	que mirar y modificar el registro que reciben, y devuelven nil cuando no hay que escribir nada.

	FORMA DEL REGISTRO EN EL DATASTORE
		{
			Version = 1,                 -- versión del esquema de `Datos` (ver Esquema.VERSION)
			Datos = { ... },             -- los datos del jugador
			Bloqueo = {                  -- ausente si nadie tiene el registro abierto
				IdSesion = "...",        -- identificador único de esta carga (un GUID)
				IdServidor = "...",      -- servidor que lo tiene, para depurar
				IdLugar = 123,
				UltimaActividad = 1700000000,   -- os.time() del último refresco
			},
			Meta = { Creado = ..., UltimoGuardado = ... },
		}
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Tablas = require(ReplicatedStorage.Shared.Utilidades.Tablas)

export type Bloqueo = {
	IdSesion: string,
	IdServidor: string,
	IdLugar: number,
	UltimaActividad: number,
}

export type Registro = {
	Version: number,
	Datos: { [string]: any },
	Bloqueo: Bloqueo?,
	Meta: { Creado: number, UltimoGuardado: number },
}

--[[
	Resultado de intentar tomar el bloqueo:
	  - "Nuevo":              el jugador no tenía registro; se ha creado uno con los datos iniciales.
	  - "Tomado":             el registro estaba libre (o el bloqueo ya era de esta sesión).
	  - "TomadoPorCaducidad": lo tenía un servidor que lleva demasiado tiempo sin dar señales de vida.
	  - "Ocupado":            lo tiene otro servidor que sigue activo: hay que esperar.
	  - "Corrupto":           el registro no tiene la forma esperada. No se toca.
	  - "VersionFutura":      el registro es de una versión del esquema más nueva que este servidor.
	                          No se toca, para no destrozar datos que no entendemos.
]]
export type ResultadoTomar = "Nuevo" | "Tomado" | "TomadoPorCaducidad" | "Ocupado" | "Corrupto" | "VersionFutura"

export type ResultadoGuardar = "Guardado" | "BloqueoPerdido"

export type OpcionesTomar = {
	Version: number, -- versión actual del esquema
	CrearDatos: () -> any, -- datos iniciales para un jugador nuevo
	Caducidad: number, -- segundos sin actividad tras los que un bloqueo se considera abandonado
}

local BloqueoSesion = {}

-- Un bloqueo caduca si su dueño lleva `caducidad` segundos o más sin refrescarlo. Un bloqueo mal
-- formado también cuenta como caducado: no hay forma de saber de quién es.
local function estaCaducado(bloqueo: any, ahora: number, caducidad: number): boolean
	if type(bloqueo) ~= "table" or type(bloqueo.UltimaActividad) ~= "number" then
		return true
	end
	return ahora - bloqueo.UltimaActividad >= caducidad
end

-- Indica si el bloqueo del registro pertenece a la sesión `idSesion`.
local function esMio(registro: any, idSesion: string): boolean
	return type(registro) == "table" and type(registro.Bloqueo) == "table" and registro.Bloqueo.IdSesion == idSesion
end

--[[
	Intenta tomar el bloqueo del `registro` actual (nil si el jugador no tiene ninguno) para `bloqueo`.

	Devuelve el resultado, el registro que hay que escribir (nil si no hay que escribir nada) y, si
	está "Ocupado", el bloqueo del servidor que lo tiene (útil para el registro de eventos).
]]
function BloqueoSesion.Tomar(
	registro: any,
	bloqueo: Bloqueo,
	ahora: number,
	opciones: OpcionesTomar
): (ResultadoTomar, Registro?, Bloqueo?)
	if registro == nil then
		return "Nuevo",
			{
				Version = opciones.Version,
				Datos = opciones.CrearDatos(),
				Bloqueo = bloqueo,
				Meta = { Creado = ahora, UltimoGuardado = ahora },
			},
			nil
	end

	if type(registro) ~= "table" or type(registro.Datos) ~= "table" or type(registro.Version) ~= "number" then
		return "Corrupto", nil, nil
	end
	if registro.Version > opciones.Version then
		return "VersionFutura", nil, nil
	end

	local resultado: ResultadoTomar = "Tomado"
	local actual = registro.Bloqueo
	if actual ~= nil then
		if type(actual) == "table" and actual.IdSesion == bloqueo.IdSesion then
			-- Ya era nuestro: ocurre al reintentar tras perder la respuesta de una petición que sí
			-- llegó a aplicarse. Se renueva sin más.
			resultado = "Tomado"
		elseif estaCaducado(actual, ahora, opciones.Caducidad) then
			resultado = "TomadoPorCaducidad"
		else
			return "Ocupado", nil, actual
		end
	end

	registro.Bloqueo = bloqueo
	return resultado, registro, nil
end

--[[
	Guarda `datos` en el `registro` si el bloqueo sigue siendo de la sesión `idSesion`.

	Si `liberar` es true, además suelta el bloqueo (es el guardado final al irse el jugador); si no,
	refresca `UltimaActividad` para que el bloqueo no caduque. Si el bloqueo ya no es nuestro,
	devuelve "BloqueoPerdido" y nil: no hay que escribir nada.
]]
function BloqueoSesion.Guardar(
	registro: any,
	idSesion: string,
	datos: any,
	ahora: number,
	version: number,
	liberar: boolean
): (ResultadoGuardar, Registro?)
	if not esMio(registro, idSesion) then
		return "BloqueoPerdido", nil
	end

	registro.Datos = Tablas.CopiaProfunda(datos)
	registro.Version = version

	local meta = if type(registro.Meta) == "table" then registro.Meta else { Creado = ahora }
	meta.UltimoGuardado = ahora
	registro.Meta = meta

	if liberar then
		registro.Bloqueo = nil
	else
		registro.Bloqueo.UltimaActividad = ahora
	end
	return "Guardado", registro
end

--[[
	Suelta el bloqueo de la sesión `idSesion` SIN tocar los datos del registro. Se usa cuando se ha
	tomado el bloqueo pero los datos nunca llegaron a usarse (el jugador se fue mientras cargaban, o
	falló la migración).

	Devuelve "Liberado" y el registro a escribir, o "BloqueoPerdido" y nil si el bloqueo ya no era
	nuestro (otro servidor lo tomó, o ya estaba liberado): entonces no hay nada que hacer.
]]
function BloqueoSesion.Soltar(registro: any, idSesion: string): ("Liberado" | "BloqueoPerdido", Registro?)
	if not esMio(registro, idSesion) then
		return "BloqueoPerdido", nil
	end

	registro.Bloqueo = nil
	return "Liberado", registro
end

return BloqueoSesion
