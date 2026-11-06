--!strict
--[[
	Gravedad (Planetas): la atracción del agujero negro y el choque con los cuerpos sólidos, como FUNCIONES PURAS.

	CÓMO ENCAJA CON EL VUELO (Naves/Fisica, client/Naves/Vuelo y ServicioNaves)
	La nave no tiene física libre: cada fotograma el cliente del piloto calcula la velocidad que piden los mandos
	(VelocidadObjetivo) y acerca la real a esa con la aceleración del motor. El agujero negro actúa como una
	CORRIENTE: suma a esa velocidad objetivo un "arrastre" hacia su centro, que crece al acercarse:

	    arrastre(d) = K · (1/d² − 1/R²)   (0 a partir del radio de influencia R, con un tope)

	K se elige para que en el radio "sin retorno" el arrastre valga exactamente VelocidadSinRetorno. Si el motor
	no da más velocidad que el arrastre, ni a toda potencia se sale: con mejoras de Motor (y turbo) se puede
	escapar desde más adentro. Es la misma cuenta en el cliente (para volar) y en el servidor (para vigilar).

	LO QUE VIGILA EL SERVIDOR
	  - La velocidad total permitida es la del motor MÁS el arrastre (si no, caer en el agujero contaría como
	    trampa).
	  - La velocidad con la que la nave se ALEJA del centro no puede superar la del motor MENOS el arrastre: un
	    cliente manipulado que ignore la atracción se detecta y se le devuelve a su sitio.
	  - Dentro del horizonte de sucesos la nave se destruye (lo decide ServicioNaves).
]]

local V = require(script.Parent.Vectores)

type Vec = V.Vec

export type Atraccion = {
	RadioInfluencia: number,
	RadioSinRetorno: number,
	VelocidadSinRetorno: number,
	VelocidadMaxima: number,
	Holgura: number?,
}

local Gravedad = {}

-- Constante K de la fórmula (ver la cabecera) para que arrastre(RadioSinRetorno) = VelocidadSinRetorno.
function Gravedad.Constante(params: Atraccion): number
	local r0, r1 = params.RadioSinRetorno, params.RadioInfluencia
	local diferencia = 1 / (r0 * r0) - 1 / (r1 * r1)
	if diferencia <= 0 then
		return 0
	end
	return params.VelocidadSinRetorno / diferencia
end

-- Velocidad de arrastre (studs/s) a `distancia` studs del centro. 0 fuera del radio de influencia.
function Gravedad.Arrastre(distancia: number, params: Atraccion): number
	if distancia ~= distancia or distancia >= params.RadioInfluencia then
		return 0
	end
	if distancia <= 1 then
		return params.VelocidadMaxima
	end
	local r1 = params.RadioInfluencia
	local valor = Gravedad.Constante(params) * (1 / (distancia * distancia) - 1 / (r1 * r1))
	return math.clamp(valor, 0, params.VelocidadMaxima)
end

--[[
	Vector de arrastre en `posicion` hacia `centro` (studs/s). Se devuelve como tres números para no crear
	tablas en cada fotograma.
]]
function Gravedad.VectorArrastre(posicion: Vec, centro: Vec, params: Atraccion): (number, number, number)
	local dx, dy, dz = centro.X - posicion.X, centro.Y - posicion.Y, centro.Z - posicion.Z
	local distancia = math.sqrt(dx * dx + dy * dy + dz * dz)
	local valor = Gravedad.Arrastre(distancia, params)
	if valor <= 0 or distancia < 1e-6 then
		return 0, 0, 0
	end
	local k = valor / distancia
	return dx * k, dy * k, dz * k
end

-- ¿Puede escapar una nave con esa velocidad máxima desde esa distancia? (su motor supera al arrastre)
function Gravedad.PuedeEscapar(distancia: number, velocidadMaxima: number, params: Atraccion): boolean
	return velocidadMaxima > Gravedad.Arrastre(distancia, params)
end

--[[
	Distancia a la que el arrastre iguala a `velocidad` (más cerca, una nave con esa velocidad máxima ya no
	puede salir). Si la velocidad supera el tope del arrastre, devuelve 0: siempre puede escapar.
]]
function Gravedad.RadioDeEscape(velocidad: number, params: Atraccion): number
	if velocidad >= params.VelocidadMaxima then
		return 0
	end
	if velocidad <= 0 then
		return params.RadioInfluencia
	end
	local r1 = params.RadioInfluencia
	-- K (1/d² − 1/r1²) = v  →  d = 1 / sqrt(v/K + 1/r1²)
	return 1 / math.sqrt(velocidad / Gravedad.Constante(params) + 1 / (r1 * r1))
end

--[[
	Vigilancia del servidor. ¿Es creíble el movimiento de `antes` a `despues` en `dt` segundos para una nave con
	esta velocidad tope (la del motor, con o sin turbo)? Comprueba:
	  1. que la distancia recorrida no supera (tope + arrastre máximo del tramo) por la holgura, más el margen;
	  2. que no se ha alejado del centro más deprisa de lo que permite el motor contra el arrastre.
	`holgura` y `margen` son los de la vigilancia normal (Naves/Config); `dt` ya viene limitado.
]]
function Gravedad.MovimientoValido(
	antes: Vec,
	despues: Vec,
	dt: number,
	tope: number,
	centro: Vec,
	params: Atraccion,
	holgura: number,
	margen: number
): boolean
	if dt ~= dt or dt < 0 then
		return false
	end
	local d0, d1 = V.distancia(antes, centro), V.distancia(despues, centro)
	if d0 ~= d0 or d1 ~= d1 then
		return false
	end
	-- El arrastre más fuerte del tramo es el del punto más cercano; el más débil, el del más lejano.
	local maximo = Gravedad.Arrastre(math.min(d0, d1), params)
	local minimo = Gravedad.Arrastre(math.max(d0, d1), params)

	local recorrido = V.distancia(antes, despues)
	if recorrido > (tope + maximo) * holgura * dt + margen then
		return false
	end

	local alejamiento = d1 - d0
	if alejamiento > 0 then
		local permitido = math.max(0, tope - minimo) * holgura * (params.Holgura or 1) * dt + margen
		if alejamiento > permitido then
			return false
		end
	end
	return true
end

--[[
	Choque con un cuerpo sólido (un planeta, el sol): si la posición está dentro de `radio` (más `margen`) y la
	velocidad va hacia dentro, se quita esa parte y la nave resbala por la superficie. Devuelve la velocidad
	nueva (sin cambios si no hace falta).
]]
function Gravedad.ContenerFuera(
	px: number,
	py: number,
	pz: number,
	vx: number,
	vy: number,
	vz: number,
	centro: Vec,
	radio: number
): (number, number, number)
	local nx, ny, nz = px - centro.X, py - centro.Y, pz - centro.Z
	local distancia = math.sqrt(nx * nx + ny * ny + nz * nz)
	if distancia >= radio or distancia < 1e-6 then
		return vx, vy, vz
	end
	nx, ny, nz = nx / distancia, ny / distancia, nz / distancia
	local haciaDentro = vx * nx + vy * ny + vz * nz
	-- Además de quitar lo que va hacia dentro, empuja un poco hacia fuera para salir del cuerpo.
	local empuje = math.min(40, (radio - distancia) * 2)
	local quitar = math.min(haciaDentro, 0) - empuje
	return vx - nx * quitar, vy - ny * quitar, vz - nz * quitar
end

return table.freeze(Gravedad)
