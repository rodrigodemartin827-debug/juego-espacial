--!strict
--[[
	Ruido (Planetas): ruido de Perlin en 2D con SEMILLA, en Luau puro.

	Roblox tiene math.noise, pero no deja elegir semilla y no existe fuera de Studio. Este es determinista
	(misma semilla, mismo terreno en cualquier máquina) y se puede probar con Lune.

	  Ruido.nuevo(semilla)            un generador
	  generador:Valor(x, z)           ruido de Perlin en (x, z), entre −1 y 1 aprox. (0 en los enteros)
	  generador:Fractal(x, z, capas)  suma de octavas: { { Escala, Amplitud } }, en studs
	  generador:Crestas(x, z, escala) 1 − |ruido|: líneas finas (grietas, crestas), entre 0 y 1
]]

local Azar = require(script.Parent.Parent.Utilidades.Azar)

local Ruido = {}
Ruido.__index = Ruido

export type Ruido = typeof(setmetatable({} :: { Perm: { number } }, Ruido))

-- 8 direcciones de gradiente repartidas en el círculo.
local GX = { 1, -1, 1, -1, 1, -1, 0, 0 }
local GY = { 1, 1, -1, -1, 0, 0, 1, -1 }
local DIAGONAL = 1 / math.sqrt(2)
for i = 1, 4 do
	GX[i] *= DIAGONAL
	GY[i] *= DIAGONAL
end

function Ruido.nuevo(semilla: number): Ruido
	local azar = Azar.nuevo(semilla)
	local base = table.create(256, 0)
	for i = 1, 256 do
		base[i] = i - 1
	end
	-- Barajado de Fisher-Yates con el generador determinista.
	for i = 256, 2, -1 do
		local j = azar:Entero(1, i)
		base[i], base[j] = base[j], base[i]
	end
	-- Se duplica para no tener que hacer módulo dos veces.
	local perm = table.create(512, 0)
	for i = 1, 512 do
		perm[i] = base[((i - 1) % 256) + 1]
	end
	return setmetatable({ Perm = perm }, Ruido)
end

local function suavizar(t: number): number
	return t * t * t * (t * (t * 6 - 15) + 10)
end

-- Ruido de Perlin en (x, z).
function Ruido.Valor(self: Ruido, x: number, z: number): number
	local perm = self.Perm
	local x0, z0 = math.floor(x), math.floor(z)
	local fx, fz = x - x0, z - z0
	local ix, iz = x0 % 256, z0 % 256

	local a = perm[ix + 1] + iz
	local b = perm[ix + 2] + iz
	local g00 = perm[a + 1] % 8 + 1
	local g01 = perm[a + 2] % 8 + 1
	local g10 = perm[b + 1] % 8 + 1
	local g11 = perm[b + 2] % 8 + 1

	local n00 = GX[g00] * fx + GY[g00] * fz
	local n10 = GX[g10] * (fx - 1) + GY[g10] * fz
	local n01 = GX[g01] * fx + GY[g01] * (fz - 1)
	local n11 = GX[g11] * (fx - 1) + GY[g11] * (fz - 1)

	local u, w = suavizar(fx), suavizar(fz)
	local nx0 = n00 + (n10 - n00) * u
	local nx1 = n01 + (n11 - n01) * u
	-- El ruido de Perlin 2D llega a ±0,707: se reescala a ±1 aprox.
	return (nx0 + (nx1 - nx0) * w) * 1.41
end

-- Suma de capas de ruido: cada capa { Escala = studs, Amplitud = studs }. Devuelve studs.
function Ruido.Fractal(self: Ruido, x: number, z: number, capas: { { Escala: number, Amplitud: number } }): number
	local total = 0
	for indice, capa in capas do
		-- Cada capa se desplaza un poco para que no coincidan los ceros de todas en el origen.
		local desfase = indice * 31.7
		total += self:Valor(x / capa.Escala + desfase, z / capa.Escala - desfase) * capa.Amplitud
	end
	return total
end

-- Crestas: 1 − |ruido|, que vale 1 justo en las líneas donde el ruido cruza el cero.
function Ruido.Crestas(self: Ruido, x: number, z: number, escala: number): number
	return 1 - math.min(1, math.abs(self:Valor(x / escala + 101.3, z / escala - 57.9)))
end

return Ruido
