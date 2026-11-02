--!strict
--[[
	Inventario (reglas): cuánto cabe en la bodega y cómo se añaden y quitan objetos. FUNCIONES PURAS.

	No usan Roblox: reciben el inventario del jugador (`{ [idObjeto] = cantidad }`, ver Datos/Tipos) y el límite de la
	bodega, y lo modifican EN SITIO. El servidor las aplica (Servicios/ServicioInventario), el cliente las usa para
	mostrar cuánto queda y las pruebas las ejecutan fuera de Studio.

	El límite (`capacidad`) es el espacio de la bodega: sale de la mejora Carga (Naves/Estadisticas → Capacidad).
	Cada objeto ocupa su `Volumen` por unidad (Datos/Objetos), así que 10 lingotes pesan más que 10 minerales.
]]

local Objetos = require(script.Parent.Datos.Objetos)

export type Inventario = { [string]: number }

local Inventario = {}

-- Una cantidad de objetos válida es un entero finito mayor que 0 (ni NaN, ni infinito, ni decimales).
local function esCantidadValida(cantidad: number): boolean
	return cantidad == cantidad and cantidad > 0 and cantidad < math.huge and cantidad == math.floor(cantidad)
end

-- Espacio que ocupa todo el inventario.
function Inventario.Volumen(inventario: Inventario): number
	local total = 0
	for id, cantidad in inventario do
		if type(cantidad) == "number" and cantidad > 0 then
			total += cantidad * Objetos.Volumen(id)
		end
	end
	return total
end

-- Espacio libre en la bodega (nunca negativo).
function Inventario.EspacioLibre(inventario: Inventario, capacidad: number): number
	return math.max(0, capacidad - Inventario.Volumen(inventario))
end

-- Unidades de `id` que caben todavía (0 si el objeto no existe o no cabe ni una).
function Inventario.CuantoCabe(inventario: Inventario, capacidad: number, id: string): number
	if Objetos.Lista[id] == nil then
		return 0
	end
	-- Un margen mínimo evita que los decimales de los volúmenes (0,1 + 0,2...) dejen una unidad fuera.
	return math.floor(Inventario.EspacioLibre(inventario, capacidad) / Objetos.Volumen(id) + 1e-9)
end

-- ¿Tiene al menos `cantidad` unidades de `id`?
function Inventario.Tiene(inventario: Inventario, id: string, cantidad: number): boolean
	return (inventario[id] or 0) >= cantidad
end

-- Cantidad de `id` que hay.
function Inventario.Cantidad(inventario: Inventario, id: string): number
	return inventario[id] or 0
end

--[[
	Añade hasta `cantidad` unidades de `id`, las que quepan. Devuelve cuántas se han añadido (puede ser menos de las
	pedidas, o 0 si la bodega está llena o el objeto no existe). Las cantidades inválidas (no enteras, NaN, <= 0) no
	añaden nada.
]]
function Inventario.Anadir(inventario: Inventario, capacidad: number, id: string, cantidad: number): number
	if not esCantidadValida(cantidad) then
		return 0
	end
	local anadidas = math.min(cantidad, Inventario.CuantoCabe(inventario, capacidad, id))
	if anadidas > 0 then
		inventario[id] = (inventario[id] or 0) + anadidas
	end
	return anadidas
end

--[[
	Quita exactamente `cantidad` unidades de `id`. Devuelve false (y no cambia nada) si no hay suficientes o la
	cantidad no es válida. Al llegar a 0 la entrada se elimina, para que el inventario guardado no acumule ceros.
]]
function Inventario.Quitar(inventario: Inventario, id: string, cantidad: number): boolean
	if not esCantidadValida(cantidad) then
		return false
	end
	local actual = inventario[id] or 0
	if actual < cantidad then
		return false
	end
	if actual == cantidad then
		inventario[id] = nil
	else
		inventario[id] = actual - cantidad
	end
	return true
end

return Inventario
