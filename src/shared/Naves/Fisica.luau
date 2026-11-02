--!strict
--[[
	Fisica (Naves): el modelo de vuelo como FUNCIONES PURAS sobre números.

	El piloto manda con su cliente (así el control es inmediato, sin esperar al servidor) y el servidor vigila.
	Este módulo contiene las cuentas del vuelo para que no dependan de Roblox y se puedan probar:

	  - Orientación: guiñada y cabeceo acumulados, con límite de giro por segundo.
	  - Velocidad objetivo: lo que piden las teclas / el joystick, en el sistema de la nave.
	  - Aceleración: la velocidad real se acerca a la objetivo a un ritmo limitado (inercia).
	  - Rebote contra una superficie.

	Los vectores se pasan como tres números (x, y, z) para no crear tablas en cada fotograma.
]]

local Config = require(script.Parent.Config)

export type Entrada = {
	Adelante: number, -- -1 (marcha atrás) .. 1 (avance)
	Lateral: number, -- -1 (izquierda) .. 1 (derecha)
	Vertical: number, -- -1 (bajar) .. 1 (subir)
	Turbo: boolean,
}

local Fisica = {}

-- ===== Entrada =====

--[[
	Zona muerta de un eje analógico (joystick): por debajo de `zona` vale 0, y el resto se reescala a 0..1 para que
	no haya un salto al salir de la zona.
]]
function Fisica.ZonaMuerta(valor: number, zona: number): number
	local magnitud = math.abs(valor)
	if magnitud <= zona then
		return 0
	end
	return math.sign(valor) * math.min(1, (magnitud - zona) / (1 - zona))
end

-- ===== Orientación =====

--[[
	Suma un giro a la guiñada y al cabeceo. Cada incremento se limita a `GiroMaximo * dt` (la nave no gira más
	deprisa de lo que permite su motor), la guiñada se mantiene entre -π y π y el cabeceo no pasa de CabeceoMaximo.
	Devuelve la guiñada y el cabeceo nuevos.
]]
function Fisica.Girar(
	guinada: number,
	cabeceo: number,
	dGuinada: number,
	dCabeceo: number,
	dt: number
): (number, number)
	local tope = Config.GiroMaximo * dt
	local nuevaGuinada = guinada + math.clamp(dGuinada, -tope, tope)
	local nuevoCabeceo = cabeceo + math.clamp(dCabeceo, -tope, tope)
	-- La guiñada da la vuelta completa: se normaliza a (-π, π].
	nuevaGuinada = (nuevaGuinada + math.pi) % (math.pi * 2) - math.pi
	nuevoCabeceo = math.clamp(nuevoCabeceo, -Config.CabeceoMaximo, Config.CabeceoMaximo)
	return nuevaGuinada, nuevoCabeceo
end

--[[
	Alabeo (inclinación lateral) visual: la nave se inclina hacia el lado en que gira o se desplaza. Se acerca
	suavemente al valor deseado (`velocidadGiro` rad/s de guiñada y `lateral` -1..1).

	Convenio de Roblox: una guiñada positiva gira hacia la IZQUIERDA y un alabeo positivo levanta el ala derecha,
	es decir, inclina hacia la izquierda. Por eso girar a la izquierda da un alabeo positivo, y desplazarse a la
	derecha (lateral positivo), uno negativo.
]]
function Fisica.Alabeo(actual: number, velocidadGiro: number, lateral: number, dt: number): number
	local maximo = math.rad(55)
	local deseado = math.clamp(velocidadGiro * 0.35 - lateral * 0.5, -1, 1) * maximo
	-- Aproximación exponencial: independiente de la tasa de fotogramas.
	local alfa = 1 - math.exp(-6 * dt)
	return actual + (deseado - actual) * alfa
end

-- ===== Velocidad =====

--[[
	Velocidad que piden los controles, en el sistema de la nave (x derecha, y arriba, z hacia ATRÁS: avanzar es z
	negativa, como en Roblox). `velocidadMax` es la de la nave sin turbo y `turboMult` el multiplicador del turbo.
	Con el turbo activo la nave empuja hacia delante aunque no se pulse avanzar.
]]
function Fisica.VelocidadObjetivo(entrada: Entrada, velocidadMax: number, turboMult: number): (number, number, number)
	local adelante = math.clamp(entrada.Adelante, -1, 1)
	if entrada.Turbo and adelante <= 0 then
		adelante = 1
	end
	local lateral = math.clamp(entrada.Lateral, -1, 1)
	local vertical = math.clamp(entrada.Vertical, -1, 1)

	local avance = if adelante >= 0
		then adelante * velocidadMax
		else adelante * velocidadMax * Config.FraccionMarchaAtras
	local tope = velocidadMax
	if entrada.Turbo then
		avance *= turboMult
		tope = velocidadMax * turboMult
	end
	local x = lateral * velocidadMax * Config.FraccionLateral
	local y = vertical * velocidadMax * Config.FraccionLateral
	local z = -avance

	-- Las diagonales no pueden superar la velocidad máxima.
	return Fisica.LimitarVector(x, y, z, tope)
end

-- Reduce el vector (x, y, z) para que su longitud no supere `maximo`. Si ya cabe, no lo toca.
function Fisica.LimitarVector(x: number, y: number, z: number, maximo: number): (number, number, number)
	local largo = math.sqrt(x * x + y * y + z * z)
	if largo <= maximo or largo < 1e-9 then
		return x, y, z
	end
	local factor = maximo / largo
	return x * factor, y * factor, z * factor
end

--[[
	Mueve la velocidad actual hacia la objetivo, como mucho `maximoCambio` studs/s en total (aceleración * dt).
	Devuelve la velocidad nueva. Es lo que da inercia a la nave: no se para ni arranca de golpe.
]]
function Fisica.AcercarVelocidad(
	ax: number,
	ay: number,
	az: number,
	ox: number,
	oy: number,
	oz: number,
	maximoCambio: number
): (number, number, number)
	local dx, dy, dz = ox - ax, oy - ay, oz - az
	local distancia = math.sqrt(dx * dx + dy * dy + dz * dz)
	if distancia <= maximoCambio or distancia < 1e-9 then
		return ox, oy, oz
	end
	local factor = maximoCambio / distancia
	return ax + dx * factor, ay + dy * factor, az + dz * factor
end

--[[
	Aceleración efectiva del paso: la de la nave, o el frenado del estabilizador si el piloto no pide nada
	(sin órdenes, la nave se detiene sola un poco más deprisa de lo que acelera).
]]
function Fisica.Aceleracion(aceleracion: number, hayOrden: boolean): number
	return if hayOrden then aceleracion else aceleracion * Config.FrenadoEstabilizador
end

-- ===== Choques =====

--[[
	Rebote de la velocidad (vx, vy, vz) contra una superficie de normal unitaria (nx, ny, nz) que apunta hacia FUERA
	de la superficie. Solo se refleja la parte que va contra la superficie; `elasticidad` 1 = rebote perfecto,
	0 = se desliza. Si ya se aleja, no cambia. Devuelve la velocidad nueva, con un mínimo de separación para
	que no se quede pegada.
]]
function Fisica.Rebote(
	vx: number,
	vy: number,
	vz: number,
	nx: number,
	ny: number,
	nz: number,
	elasticidad: number
): (number, number, number)
	local contra = vx * nx + vy * ny + vz * nz
	if contra >= 0 then
		return vx, vy, vz
	end
	local factor = (1 + elasticidad) * contra
	local rx, ry, rz = vx - factor * nx, vy - factor * ny, vz - factor * nz
	-- Garantiza una velocidad de salida mínima en la dirección de la normal.
	local saliendo = rx * nx + ry * ny + rz * nz
	if saliendo < Config.ImpulsoSeparacion then
		local falta = Config.ImpulsoSeparacion - saliendo
		rx, ry, rz = rx + nx * falta, ry + ny * falta, rz + nz * falta
	end
	return rx, ry, rz
end

return Fisica
