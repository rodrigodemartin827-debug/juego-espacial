--!strict
--[[
	Calor (Planetas): el recalentamiento de las naves cerca del sol, como FUNCIONES PURAS.

	Cada distancia al sol tiene un CALOR OBJETIVO: 0 fuera del radio de aviso y CalorMax en el núcleo, con una
	curva (Exponente) que hace que suba poco al principio y mucho al final:

	    objetivo(d) = CalorMax · t^Exponente,   t = (RadioAviso − d) / (RadioAviso − RadioNucleo), entre 0 y 1

	El calor de la nave no salta al objetivo: se acerca a él poco a poco (Inercia por segundo) y nunca sube más de
	SubidaMaxima por segundo. Así hay tiempo de reaccionar al ver el aviso, y al alejarse se enfría sola.

	Por encima de UmbralDano el casco se daña, más cuanto más caliente (DanoPorSegundo con el calor al máximo).
	Lo decide el SERVIDOR (ServicioNaves) con la posición que él ve; el cliente solo lo muestra.
]]

export type ParametrosCalor = {
	RadioAviso: number,
	RadioNucleo: number,
	CalorMax: number,
	Exponente: number,
	Inercia: number,
	SubidaMaxima: number,
	UmbralAviso: number,
	UmbralDano: number,
	DanoPorSegundo: number,
	IgnoraEscudo: boolean?,
}

local Calor = {}

-- Calor hacia el que tiende una nave a `distancia` studs del centro del sol.
function Calor.Objetivo(distancia: number, params: ParametrosCalor): number
	if distancia ~= distancia or distancia >= params.RadioAviso then
		return 0
	end
	local rango = math.max(params.RadioAviso - params.RadioNucleo, 1e-6)
	local t = math.clamp((params.RadioAviso - distancia) / rango, 0, 1)
	return params.CalorMax * t ^ params.Exponente
end

--[[
	Avanza el calor `dt` segundos estando a `distancia`. Devuelve el calor nuevo (entre 0 y CalorMax).
	Se acerca al objetivo exponencialmente (independiente de cada cuánto se llame) y con la subida limitada.
]]
function Calor.Paso(calor: number, distancia: number, dt: number, params: ParametrosCalor): number
	if calor ~= calor then
		calor = 0
	end
	if dt <= 0 or dt ~= dt then
		return math.clamp(calor, 0, params.CalorMax)
	end
	local objetivo = Calor.Objetivo(distancia, params)
	local alfa = 1 - math.exp(-params.Inercia * dt)
	local nuevo = calor + (objetivo - calor) * alfa
	nuevo = math.min(nuevo, calor + params.SubidaMaxima * dt)
	return math.clamp(nuevo, 0, params.CalorMax)
end

-- Daño por segundo que hace ese calor (0 por debajo del umbral).
function Calor.DanoPorSegundo(calor: number, params: ParametrosCalor): number
	if calor <= params.UmbralDano then
		return 0
	end
	local fraccion = (calor - params.UmbralDano) / math.max(params.CalorMax - params.UmbralDano, 1e-6)
	return params.DanoPorSegundo * math.clamp(fraccion, 0, 1)
end

-- Nivel del calor para el panel: "Normal", "Aviso" o "Peligro".
function Calor.Nivel(calor: number, params: ParametrosCalor): string
	if calor > params.UmbralDano then
		return "Peligro"
	elseif calor >= params.UmbralAviso then
		return "Aviso"
	end
	return "Normal"
end

--[[
	Distancia mínima al sol a la que se puede estar quieto sin que el calor llegue nunca al umbral de daño
	(donde el objetivo vale justo UmbralDano). Útil para colocar cosas y para las pruebas.
]]
function Calor.DistanciaSegura(params: ParametrosCalor): number
	local t = (params.UmbralDano / params.CalorMax) ^ (1 / params.Exponente)
	return params.RadioAviso - t * (params.RadioAviso - params.RadioNucleo)
end

return table.freeze(Calor)
