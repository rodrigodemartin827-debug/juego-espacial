--!strict
--[[
	Azar: generador de números pseudoaleatorios DETERMINISTA (misma semilla, misma secuencia).

	Roblox ya tiene `Random`, pero aquí hace falta que el resultado sea idéntico en cualquier máquina y
	que se pueda probar fuera de Studio: el campo de asteroides se genera a partir de una semilla y el
	servidor y las pruebas deben obtener exactamente el mismo campo.

	Es el generador de Park-Miller ("minstd"): x' = x * 48271 mod (2^31 - 1). Los productos caben
	justo en un `number` (doble de 64 bits) sin perder precisión, así que no hace falta nada más.
]]

local MODULO = 2147483647
local MULTIPLICADOR = 48271

local Azar = {}
Azar.__index = Azar

export type Azar = typeof(setmetatable({} :: { Estado: number }, Azar))

-- Crea un generador. Cualquier número sirve de semilla (se reduce al rango válido, que excluye el 0).
function Azar.nuevo(semilla: number): Azar
	local estado = math.floor(math.abs(semilla)) % MODULO
	if estado == 0 then
		estado = 1
	end
	return setmetatable({ Estado = estado }, Azar)
end

-- Número en [0, 1).
function Azar.Siguiente(self: Azar): number
	self.Estado = (self.Estado * MULTIPLICADOR) % MODULO
	return (self.Estado - 1) / (MODULO - 1)
end

-- Número decimal entre `minimo` y `maximo`.
function Azar.Entre(self: Azar, minimo: number, maximo: number): number
	return minimo + (maximo - minimo) * self:Siguiente()
end

-- Entero entre `minimo` y `maximo`, ambos incluidos.
function Azar.Entero(self: Azar, minimo: number, maximo: number): number
	return minimo + math.floor(self:Siguiente() * (maximo - minimo + 1))
end

-- Dirección unitaria al azar (distribuida uniformemente por la esfera): x, y, z.
function Azar.Direccion(self: Azar): (number, number, number)
	local cenit = self:Entre(-1, 1)
	local angulo = self:Entre(0, math.pi * 2)
	local radio = math.sqrt(1 - cenit * cenit)
	return math.cos(angulo) * radio, cenit, math.sin(angulo) * radio
end

return Azar
