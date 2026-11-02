--!strict
--[[
	CinematicaR6: dónde queda cada pieza de un personaje R6 para una pose dada (cinemática directa).

	Reproduce lo que hace Roblox con los Motor6D del rig R6 de fábrica:
		Part1.CFrame = Part0.CFrame * C0 * Transform * C1:Inverse()
	con los C0/C1 estándar (los mismos que pone el Rig Builder y los personajes de jugador R6). El Transform de
	cada articulación sale de Animaciones.Articulacion, la MISMA función que usa el cliente para construir las
	KeyframeSequence, así que lo que se calcula aquí es lo que se verá en el juego.

	No depende de CFrame ni de nada de Roblox (matrices 3x3 por filas y vectores {x, y, z}): así lo pueden usar
	el horneado de animaciones (Animacion/Horneado), las pruebas con Lune y la exportación a Blender.

	Sistema de coordenadas: el de Roblox, con la HumanoidRootPart en el origen y sin girar. El personaje mira
	hacia -Z, su derecha es +X y arriba es +Y. En un R6 de pie el suelo queda en Y = -3 (Cinematica.ALTURA_SUELO).
]]

local Animaciones = require(script.Parent.Parent.Combate.Datos.Animaciones)

export type Vector = { number } -- { x, y, z }
export type Matriz = { { number } } -- 3x3 por filas
export type Marco = { P: Vector, R: Matriz } -- posición + rotación (como un CFrame)
-- Pose de una pieza: { cabeceo, giro, ladeo [, derecha, arriba, adelante] } (ver Combate/Datos/Animaciones).
export type Pose = { number }

local Cinematica = {}

-- Altura del suelo respecto al centro de la HumanoidRootPart en un R6 (2 de pierna + 1 de medio torso).
Cinematica.ALTURA_SUELO = -3

-- Tamaño de cada pieza del R6 clásico, en studs.
Cinematica.TAMANOS = {
	Torso = { 2, 2, 1 },
	Head = { 2, 1, 1 },
	["Right Arm"] = { 1, 2, 1 },
	["Left Arm"] = { 1, 2, 1 },
	["Right Leg"] = { 1, 2, 1 },
	["Left Leg"] = { 1, 2, 1 },
} :: { [string]: Vector }

-- Las seis piezas animables del R6, en el orden en que se recorren (el Torso primero: es el padre).
Cinematica.PIEZAS = { "Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg" }

local function marco(x: number, y: number, z: number, r: { number }): Marco
	return {
		P = { x, y, z },
		R = { { r[1], r[2], r[3] }, { r[4], r[5], r[6] }, { r[7], r[8], r[9] } },
	}
end

-- Rotaciones de fábrica de los C0/C1 del R6 (las mismas columnas que Animaciones usa como `Eje`).
local ROT_RAIZ = { -1, 0, 0, 0, 0, 1, 0, 1, 0 }
local ROT_DERECHA = { 0, 0, 1, 0, 1, 0, -1, 0, 0 }
local ROT_IZQUIERDA = { 0, 0, -1, 0, 1, 0, 1, 0, 0 }

-- Articulación de cada pieza: de qué pieza cuelga y sus C0/C1 de fábrica (valores de Roblox para R6).
local ARTICULACIONES: { [string]: { Padre: string, C0: Marco, C1: Marco } } = {
	Torso = { Padre = "HumanoidRootPart", C0 = marco(0, 0, 0, ROT_RAIZ), C1 = marco(0, 0, 0, ROT_RAIZ) },
	Head = { Padre = "Torso", C0 = marco(0, 1, 0, ROT_RAIZ), C1 = marco(0, -0.5, 0, ROT_RAIZ) },
	["Right Arm"] = { Padre = "Torso", C0 = marco(1, 0.5, 0, ROT_DERECHA), C1 = marco(-0.5, 0.5, 0, ROT_DERECHA) },
	["Left Arm"] = { Padre = "Torso", C0 = marco(-1, 0.5, 0, ROT_IZQUIERDA), C1 = marco(0.5, 0.5, 0, ROT_IZQUIERDA) },
	["Right Leg"] = { Padre = "Torso", C0 = marco(1, -1, 0, ROT_DERECHA), C1 = marco(0.5, 1, 0, ROT_DERECHA) },
	["Left Leg"] = { Padre = "Torso", C0 = marco(-1, -1, 0, ROT_IZQUIERDA), C1 = marco(-0.5, 1, 0, ROT_IZQUIERDA) },
}
Cinematica.ARTICULACIONES = ARTICULACIONES

-- Nodo del rig (con su `Eje`) de cada pieza, para llamar a Animaciones.Articulacion.
local NODOS: { [string]: any } = {}
local function indexar(nodo: any)
	NODOS[nodo.Nombre] = nodo
	for _, hijo in nodo.Hijos do
		indexar(hijo)
	end
end
indexar(Animaciones.Rig)
Cinematica.NODOS = NODOS

-- ===== Álgebra (matrices por filas) =====

function Cinematica.Multiplicar(a: Matriz, b: Matriz): Matriz
	local r = {}
	for i = 1, 3 do
		r[i] = {}
		for j = 1, 3 do
			r[i][j] = a[i][1] * b[1][j] + a[i][2] * b[2][j] + a[i][3] * b[3][j]
		end
	end
	return r
end

function Cinematica.Trasponer(m: Matriz): Matriz
	return {
		{ m[1][1], m[2][1], m[3][1] },
		{ m[1][2], m[2][2], m[3][2] },
		{ m[1][3], m[2][3], m[3][3] },
	}
end

function Cinematica.Aplicar(m: Matriz, v: Vector): Vector
	return {
		m[1][1] * v[1] + m[1][2] * v[2] + m[1][3] * v[3],
		m[2][1] * v[1] + m[2][2] * v[2] + m[2][3] * v[3],
		m[3][1] * v[1] + m[3][2] * v[2] + m[3][3] * v[3],
	}
end

-- a * b, como CFrame * CFrame.
function Cinematica.Componer(a: Marco, b: Marco): Marco
	local p = Cinematica.Aplicar(a.R, b.P)
	return { P = { a.P[1] + p[1], a.P[2] + p[2], a.P[3] + p[3] }, R = Cinematica.Multiplicar(a.R, b.R) }
end

-- Inversa de un marco rígido, como CFrame:Inverse().
function Cinematica.Invertir(a: Marco): Marco
	local rt = Cinematica.Trasponer(a.R)
	local p = Cinematica.Aplicar(rt, a.P)
	return { P = { -p[1], -p[2], -p[3] }, R = rt }
end

-- Rotación del sistema del personaje con los ángulos en grados, en el orden de Roblox (Rx * Ry * Rz).
function Cinematica.RotacionXYZ(rx: number, ry: number, rz: number): Matriz
	local cx, sx = math.cos(math.rad(rx)), math.sin(math.rad(rx))
	local cy, sy = math.cos(math.rad(ry)), math.sin(math.rad(ry))
	local cz, sz = math.cos(math.rad(rz)), math.sin(math.rad(rz))
	local mx = { { 1, 0, 0 }, { 0, cx, -sx }, { 0, sx, cx } }
	local my = { { cy, 0, sy }, { 0, 1, 0 }, { -sy, 0, cy } }
	local mz = { { cz, -sz, 0 }, { sz, cz, 0 }, { 0, 0, 1 } }
	return Cinematica.Multiplicar(mx, Cinematica.Multiplicar(my, mz))
end

-- Lo contrario de RotacionXYZ: los ángulos (grados) de una matriz Rx * Ry * Rz. Válido lejos de giro = ±90°.
function Cinematica.AngulosXYZ(m: Matriz): (number, number, number)
	local sy = math.clamp(m[1][3], -1, 1)
	local ry = math.asin(sy)
	local rx = math.atan2(-m[2][3], m[3][3])
	local rz = math.atan2(-m[1][2], m[1][1])
	return math.deg(rx), math.deg(ry), math.deg(rz)
end

--[[
	Rotación de una pieza respecto a su padre, en los ejes del personaje, para una pose escrita en el sistema
	de Datos/Animaciones. En el Torso y la cabeza (`Arriba`) el cabeceo y el ladeo van con el signo cambiado,
	igual que en Animaciones.Articulacion.
]]
function Cinematica.RotacionDePose(pieza: string, pose: Pose): Matriz
	local signo = if NODOS[pieza].Arriba then -1 else 1
	return Cinematica.RotacionXYZ(signo * pose[1], pose[2], signo * pose[3])
end

-- Lo contrario de RotacionDePose: los ángulos { cabeceo, giro, ladeo } de una rotación relativa a su padre.
function Cinematica.PoseDeRotacion(pieza: string, m: Matriz): Pose
	local signo = if NODOS[pieza].Arriba then -1 else 1
	local rx, ry, rz = Cinematica.AngulosXYZ(m)
	return { signo * rx, ry, signo * rz }
end

-- Transform del Motor6D de una pieza para una pose (lo que el cliente mete en Pose.CFrame).
function Cinematica.Transform(pieza: string, pose: Pose): Marco
	local m, t = Animaciones.Articulacion(NODOS[pieza], pose)
	return marco(t[1], t[2], t[3], m)
end

--[[
	Marcos (posición y rotación) de las seis piezas en el sistema de la HumanoidRootPart para un juego de poses
	{ [pieza] = pose }. Una pieza sin pose queda en reposo. Devuelve { [pieza] = Marco }.
]]
function Cinematica.Piezas(poses: { [string]: Pose }): { [string]: Marco }
	local resultado: { [string]: Marco } = {
		HumanoidRootPart = marco(0, 0, 0, { 1, 0, 0, 0, 1, 0, 0, 0, 1 }),
	}
	for _, pieza in Cinematica.PIEZAS do
		local articulacion = ARTICULACIONES[pieza]
		local pose = poses[pieza] or { 0, 0, 0 }
		local padre = resultado[articulacion.Padre]
		local conJunta = Cinematica.Componer(padre, articulacion.C0)
		local conTransform = Cinematica.Componer(conJunta, Cinematica.Transform(pieza, pose))
		resultado[pieza] = Cinematica.Componer(conTransform, Cinematica.Invertir(articulacion.C1))
	end
	return resultado
end

-- Punto de una pieza (en sus coordenadas locales) llevado al sistema de la HumanoidRootPart.
function Cinematica.Punto(m: Marco, local_: Vector): Vector
	local p = Cinematica.Aplicar(m.R, local_)
	return { m.P[1] + p[1], m.P[2] + p[2], m.P[3] + p[3] }
end

-- Las cuatro esquinas de la planta de una pierna (su cara inferior), en el sistema de la HumanoidRootPart.
function Cinematica.EsquinasPie(m: Marco): { Vector }
	return {
		Cinematica.Punto(m, { -0.5, -1, -0.5 }),
		Cinematica.Punto(m, { 0.5, -1, -0.5 }),
		Cinematica.Punto(m, { -0.5, -1, 0.5 }),
		Cinematica.Punto(m, { 0.5, -1, 0.5 }),
	}
end

-- Altura (Y) del punto más bajo de la planta de una pierna.
function Cinematica.AlturaPie(m: Marco): number
	local minimo = math.huge
	for _, esquina in Cinematica.EsquinasPie(m) do
		minimo = math.min(minimo, esquina[2])
	end
	return minimo
end

return Cinematica
