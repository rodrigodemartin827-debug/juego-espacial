--!strict
--[[
	AlmacenMemoria: un "DataStore" falso que guarda los datos en la memoria del servidor.

	ServicioDatos lo usa SOLO en Roblox Studio cuando el DataStore real no está disponible (el lugar
	no está publicado o no se ha activado el acceso a la API en la configuración del juego). Así se
	puede probar el juego sin configurar nada. Los datos se pierden al detener la prueba.

	Implementa solo las operaciones que usa ServicioDatos, con la misma semántica que el real:
	  - Los valores se copian al guardar y al leer (nunca se comparten referencias).
	  - Si la función de UpdateAsync devuelve nil, la escritura se cancela.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Tablas = require(ReplicatedStorage.Shared.Utilidades.Tablas)

local AlmacenMemoria = {}
AlmacenMemoria.__index = AlmacenMemoria

export type AlmacenMemoria = typeof(setmetatable(
	{} :: {
		_datos: { [string]: any },
	},
	AlmacenMemoria
))

function AlmacenMemoria.nuevo(): AlmacenMemoria
	return setmetatable({ _datos = {} }, AlmacenMemoria)
end

function AlmacenMemoria.GetAsync(self: AlmacenMemoria, clave: string): any
	return Tablas.CopiaProfunda(self._datos[clave])
end

function AlmacenMemoria.UpdateAsync(self: AlmacenMemoria, clave: string, transformar: (any) -> (any, any?)): any
	-- La función puede devolver varios valores (nuevo valor, UserIds...); solo interesa el primero.
	local nuevo = transformar(Tablas.CopiaProfunda(self._datos[clave]))
	if nuevo == nil then
		return nil
	end

	self._datos[clave] = Tablas.CopiaProfunda(nuevo)
	return Tablas.CopiaProfunda(nuevo)
end

return AlmacenMemoria
