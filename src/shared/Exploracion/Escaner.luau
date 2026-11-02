--!strict
--[[
	Escaner (reglas): las cuentas del escáner de mano como FUNCIONES PURAS.

	  - cuánto dura un análisis según la velocidad del escáner (mejora Escáner),
	  - qué recompensa da cada escaneo (el primero de una especie paga todo; repetirlo, una fracción),
	  - si un objetivo está al alcance,
	  - qué objetivo elige el cliente al apuntar (ayuda de puntería).

	Los puntos y direcciones son cualquier cosa con campos X, Y, Z (un Vector3 o una tabla { X=, Y=, Z= }).
	El servidor decide con estas mismas funciones; el cliente las usa para mostrar la barra de progreso.
]]

local Config = require(script.Parent.Config)

export type Punto = { X: number, Y: number, Z: number }

export type Recompensa = {
	Nuevo: boolean, -- primera vez que se escanea esa especie
	XP: number,
	Monedas: number,
}

local Escaner = {}

--[[
	Segundos que tarda el análisis de una especie. `velocidad` es el multiplicador de la mejora Escáner (1 = normal,
	2 = el doble de rápido). Nunca baja de Config.DuracionMinimaEscaneo.
]]
function Escaner.Duracion(duracionBase: number, velocidad: number): number
	local rapidez = if velocidad > 0 then velocidad else 1
	return math.max(Config.DuracionMinimaEscaneo, duracionBase / rapidez)
end

-- Fracción de la recompensa que se cobra en un escaneo. `vecesAntes` = cuántas veces se había escaneado ya.
function Escaner.FraccionRecompensa(vecesAntes: number): number
	if vecesAntes <= 0 then
		return 1
	end
	local fracciones = Config.RecompensaRepeticion
	return fracciones[math.min(vecesAntes, #fracciones)]
end

-- Recompensa de un escaneo de una especie con esa XP y esas monedas base.
function Escaner.Recompensa(xpBase: number, monedasBase: number, vecesAntes: number): Recompensa
	local fraccion = Escaner.FraccionRecompensa(vecesAntes)
	return {
		Nuevo = vecesAntes <= 0,
		XP = math.floor(xpBase * fraccion),
		Monedas = math.floor(monedasBase * fraccion),
	}
end

-- Distancia entre dos puntos.
function Escaner.Distancia(a: Punto, b: Punto): number
	local dx, dy, dz = a.X - b.X, a.Y - b.Y, a.Z - b.Z
	return math.sqrt(dx * dx + dy * dy + dz * dz)
end

-- ¿Está a `distancia` dentro del alcance, con la holgura de Config.HolguraAlcance si se pide?
function Escaner.EnAlcance(distancia: number, alcance: number, conHolgura: boolean?): boolean
	local limite = if conHolgura then alcance * Config.HolguraAlcance else alcance
	return distancia == distancia and distancia <= limite
end

--[[
	Elige, entre los `candidatos` (lista de { Posicion = punto, ... }), el que mejor encaja con el rayo de la mira:
	el más cercano a la dirección del rayo que esté dentro del cono de `anguloMaximo` grados y a menos de `alcance`
	studs. Devuelve su índice, o nil si ninguno vale. Sirve para que, en móvil o con poca puntería, el escáner "se
	pegue" al objetivo que casi se está mirando.
]]
function Escaner.MejorObjetivo(
	origen: Punto,
	direccion: Punto,
	candidatos: { { Posicion: Punto } },
	alcance: number,
	anguloMaximo: number
): number?
	local largo = math.sqrt(direccion.X ^ 2 + direccion.Y ^ 2 + direccion.Z ^ 2)
	if largo < 1e-6 then
		return nil
	end
	local dx, dy, dz = direccion.X / largo, direccion.Y / largo, direccion.Z / largo
	local cosMinimo = math.cos(math.rad(anguloMaximo))

	local mejor: number? = nil
	local mejorCos = cosMinimo
	for indice, candidato in candidatos do
		local p = candidato.Posicion
		local vx, vy, vz = p.X - origen.X, p.Y - origen.Y, p.Z - origen.Z
		local distancia = math.sqrt(vx * vx + vy * vy + vz * vz)
		if distancia > 1e-6 and distancia <= alcance then
			local coseno = (vx * dx + vy * dy + vz * dz) / distancia
			if coseno >= mejorCos then
				mejorCos = coseno
				mejor = indice
			end
		end
	end
	return mejor
end

return Escaner
