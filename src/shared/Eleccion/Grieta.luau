--!strict
--[[
	Grieta (Elección de bando): la FORMA de la fisura de energía que separa a los dos bandos.

	Solo calcula puntos (números): el cliente (client/Eleccion/Escena) los convierte en piezas de Neon. Así la forma
	se prueba con Lune y es siempre la misma para la misma semilla.

	La grieta es un zigzag vertical: cada vértice se aparta del centro una cantidad fija (según la semilla) más un
	temblor que cambia con el tiempo. En las dos puntas no se aparta nada, y el grosor también se afina hacia ellas,
	así parece una rasgadura en el espacio que se abre más en el medio.
]]

local Azar = require(script.Parent.Parent.Utilidades.Azar)

export type Punto = { X: number, Y: number, Z: number, Grosor: number } -- Grosor: 0..1 (1 = centro)

export type Forma = {
	Alto: number,
	Desvio: number,
	Temblor: number,
	VelocidadTemblor: number,
	Base: { number }, -- desvío fijo de cada vértice (entre -1 y 1)
	Fase: { number }, -- fase del temblor de cada vértice
}

export type Rama = { Desde: number, Angulo: number, Largo: number, Puntos: number }

local Grieta = {}

-- Cuánto se puede abrir la grieta a una altura `u` (0 = punta de abajo, 1 = punta de arriba): 0 en las puntas.
function Grieta.Apertura(u: number): number
	return math.sin(math.clamp(u, 0, 1) * math.pi)
end

-- Prepara la forma de una grieta de `puntos` vértices (al menos 3).
function Grieta.nueva(
	semilla: number,
	puntos: number,
	alto: number,
	desvio: number,
	temblor: number,
	velocidad: number
): Forma
	local azar = Azar.nuevo(semilla)
	local base, fase = {}, {}
	local cantidad = math.max(3, math.floor(puntos))
	local signo = 1
	for indice = 1, cantidad do
		-- Alterna el lado casi siempre: así sale un zigzag de verdad y no una curva.
		if azar:Siguiente() < 0.8 then
			signo = -signo
		end
		base[indice] = signo * azar:Entre(0.35, 1)
		fase[indice] = azar:Entre(0, math.pi * 2)
	end
	return {
		Alto = alto,
		Desvio = desvio,
		Temblor = temblor,
		VelocidadTemblor = velocidad,
		Base = base,
		Fase = fase,
	}
end

--[[
	Vértices de la grieta en el instante `t`, en el sistema de la propia grieta (centro en 0, Y hacia arriba).
	`apertura` (1 normal) multiplica el desvío: sube al resaltar o al elegir, para que la grieta "se abra".
]]
function Grieta.Puntos(forma: Forma, t: number, apertura: number?): { Punto }
	local cantidad = #forma.Base
	local abre = apertura or 1
	local resultado = table.create(cantidad) :: { Punto }
	for indice = 1, cantidad do
		local u = (indice - 1) / (cantidad - 1)
		local hueco = Grieta.Apertura(u)
		local ola = math.sin(t * forma.VelocidadTemblor + forma.Fase[indice])
		local x = (forma.Base[indice] * forma.Desvio + ola * forma.Temblor) * hueco * abre
		-- Un poco de profundidad para que, al girar la cámara, no parezca un dibujo plano.
		local z = math.cos(t * forma.VelocidadTemblor * 0.7 + forma.Fase[indice]) * forma.Temblor * 0.6 * hueco
		resultado[indice] = {
			X = x,
			Y = (u - 0.5) * forma.Alto,
			Z = z,
			Grosor = 0.5 + 0.5 * hueco,
		}
	end
	return resultado
end

-- Desvío máximo posible de un vértice (para comprobar que la grieta no se sale de su sitio).
function Grieta.DesvioMaximo(forma: Forma, apertura: number?): number
	return (forma.Desvio + forma.Temblor) * (apertura or 1)
end

--[[
	Grietas secundarias: salen de vértices del tercio central hacia los lados, alternando izquierda y derecha.
	`largo` = { mínimo, máximo } en studs.
]]
function Grieta.Ramas(
	semilla: number,
	cantidad: number,
	puntosPrincipal: number,
	largo: { number },
	puntos: number
): { Rama }
	local azar = Azar.nuevo(semilla * 31 + 5)
	local ramas = {}
	local primero = math.max(2, math.floor(puntosPrincipal * 0.25))
	local ultimo = math.min(puntosPrincipal - 1, math.ceil(puntosPrincipal * 0.75))
	for indice = 1, cantidad do
		local lado = if indice % 2 == 0 then 1 else -1
		table.insert(ramas, {
			Desde = azar:Entero(primero, ultimo),
			-- Ángulo respecto a la horizontal, hacia arriba o hacia abajo, hacia su lado.
			Angulo = math.rad(azar:Entre(-55, 55)) + (if lado < 0 then math.pi else 0),
			Largo = azar:Entre(largo[1], largo[2] or largo[1]),
			Puntos = math.max(2, puntos),
		})
	end
	return ramas
end

-- Vértices de una rama que sale de `origen` (en el sistema de la grieta), con un zigzag pequeño.
function Grieta.PuntosRama(rama: Rama, origen: Punto, t: number, semilla: number): { Punto }
	local resultado = { { X = origen.X, Y = origen.Y, Z = origen.Z, Grosor = 0.6 } }
	local dx, dy = math.cos(rama.Angulo), math.sin(rama.Angulo)
	for paso = 1, rama.Puntos do
		local u = paso / rama.Puntos
		local lateral = math.sin(t * 2.3 + paso * 1.7 + semilla) * 0.6 * (1 - u)
		table.insert(resultado, {
			X = origen.X + dx * rama.Largo * u - dy * lateral,
			Y = origen.Y + dy * rama.Largo * u + dx * lateral,
			Z = origen.Z,
			Grosor = 0.6 * (1 - u) + 0.1,
		})
	end
	return resultado
end

return Grieta
