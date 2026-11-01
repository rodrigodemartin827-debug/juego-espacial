--!strict
--[[
	Tablas: utilidades generales para trabajar con tablas.
]]

local Tablas = {}

--[[
	Devuelve una copia profunda de `valor`: las tablas (también las anidadas) se duplican y el
	resto de valores se devuelven tal cual.

	Se usa para que los datos de un jugador no compartan referencias con la plantilla ni con el
	registro que se envía al DataStore.

	Limitaciones: no conserva metatablas y no admite referencias circulares. Ninguna de las dos
	cosas puede aparecer en datos que se guarden en un DataStore, así que no se tratan.
]]
function Tablas.CopiaProfunda<T>(valor: T): T
	if type(valor) ~= "table" then
		return valor
	end

	local copia = {}
	for clave, elemento in valor :: any do
		copia[clave] = Tablas.CopiaProfunda(elemento)
	end
	return copia :: any
end

return Tablas
