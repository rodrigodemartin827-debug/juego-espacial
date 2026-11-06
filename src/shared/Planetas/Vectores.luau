--!strict
--[[
	Vectores (Planetas): cuentas de vectores 3D como FUNCIONES PURAS.

	Trabajan con cualquier cosa que tenga campos X, Y, Z (un Vector3 de Roblox o una tabla { X=, Y=, Z= }) y
	devuelven tablas nuevas. Así los módulos de Planetas se pueden probar fuera de Studio con Lune.
]]

export type Vec = { X: number, Y: number, Z: number }

local Vectores = {}

function Vectores.nuevo(x: number, y: number, z: number): Vec
	return { X = x, Y = y, Z = z }
end

function Vectores.sumar(a: Vec, b: Vec): Vec
	return { X = a.X + b.X, Y = a.Y + b.Y, Z = a.Z + b.Z }
end

function Vectores.restar(a: Vec, b: Vec): Vec
	return { X = a.X - b.X, Y = a.Y - b.Y, Z = a.Z - b.Z }
end

function Vectores.escalar(a: Vec, k: number): Vec
	return { X = a.X * k, Y = a.Y * k, Z = a.Z * k }
end

function Vectores.punto(a: Vec, b: Vec): number
	return a.X * b.X + a.Y * b.Y + a.Z * b.Z
end

function Vectores.cruz(a: Vec, b: Vec): Vec
	return {
		X = a.Y * b.Z - a.Z * b.Y,
		Y = a.Z * b.X - a.X * b.Z,
		Z = a.X * b.Y - a.Y * b.X,
	}
end

function Vectores.largo(a: Vec): number
	return math.sqrt(a.X * a.X + a.Y * a.Y + a.Z * a.Z)
end

function Vectores.distancia(a: Vec, b: Vec): number
	local dx, dy, dz = a.X - b.X, a.Y - b.Y, a.Z - b.Z
	return math.sqrt(dx * dx + dy * dy + dz * dz)
end

-- Vector unitario en la misma dirección. Un vector nulo devuelve `porDefecto` (o (0, 1, 0)).
function Vectores.unitario(a: Vec, porDefecto: Vec?): Vec
	local largo = Vectores.largo(a)
	if largo < 1e-9 then
		local d = porDefecto or { X = 0, Y = 1, Z = 0 }
		return { X = d.X, Y = d.Y, Z = d.Z }
	end
	return { X = a.X / largo, Y = a.Y / largo, Z = a.Z / largo }
end

-- Interpolación lineal entre dos vectores.
function Vectores.mezclar(a: Vec, b: Vec, t: number): Vec
	return { X = a.X + (b.X - a.X) * t, Y = a.Y + (b.Y - a.Y) * t, Z = a.Z + (b.Z - a.Z) * t }
end

-- Ángulo en grados entre dos direcciones (no hace falta que sean unitarias).
function Vectores.angulo(a: Vec, b: Vec): number
	local la, lb = Vectores.largo(a), Vectores.largo(b)
	if la < 1e-9 or lb < 1e-9 then
		return 0
	end
	return math.deg(math.acos(math.clamp(Vectores.punto(a, b) / (la * lb), -1, 1)))
end

-- Copia (por si se recibe un Vector3 y hace falta una tabla).
function Vectores.copiar(a: Vec): Vec
	return { X = a.X, Y = a.Y, Z = a.Z }
end

-- Paso suave de Hermite: 0 por debajo de `borde0`, 1 por encima de `borde1` y una curva suave en medio.
function Vectores.suave(borde0: number, borde1: number, x: number): number
	if borde1 == borde0 then
		return if x < borde0 then 0 else 1
	end
	local t = math.clamp((x - borde0) / (borde1 - borde0), 0, 1)
	return t * t * (3 - 2 * t)
end

return table.freeze(Vectores)
