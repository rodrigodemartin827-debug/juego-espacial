--!strict
--[[
	Reglas: las reglas del combate como FUNCIONES PURAS (sin Instancias ni servicios de Roblox).

	El servidor las usa para decidir cada petición del cliente. Al ser puras (reciben números y tablas,
	devuelven un resultado), se pueden probar fuera de Studio y no dependen del estado de ningún servicio.

	Los puntos son cualquier cosa con campos X, Y, Z: un Vector3 de Roblox o una tabla { X=, Y=, Z= }.
]]

local Config = require(script.Parent.Config)

export type Punto = { X: number, Y: number, Z: number }

-- Lo que hace falta saber de un luchador para decidir si puede actuar.
export type Estado = {
	Vivo: boolean,
	AturdidoHasta: number, -- instante (os.clock) hasta el que no puede actuar
	OcupadoHasta: number, -- instante hasta el que está en mitad de otra habilidad
}

local Reglas = {}

-- ===== Estado, cooldown y energía =====

--[[
	¿Puede el luchador iniciar una habilidad ahora? Devuelve `true`, o `false` y el motivo:
	"muerto", "aturdido" u "ocupado".
]]
function Reglas.PuedeActuar(estado: Estado, ahora: number): (boolean, string?)
	if not estado.Vivo then
		return false, "muerto"
	end
	if ahora < estado.AturdidoHasta then
		return false, "aturdido"
	end
	if ahora < estado.OcupadoHasta then
		return false, "ocupado"
	end
	return true, nil
end

-- ¿Ha terminado el cooldown? `fin` es el instante en que termina (nil = nunca se ha usado).
function Reglas.CooldownListo(fin: number?, ahora: number): boolean
	return fin == nil or ahora >= fin
end

-- Segundos que faltan para que termine el cooldown (0 si ya ha terminado).
function Reglas.CooldownRestante(fin: number?, ahora: number): number
	if fin == nil or ahora >= fin then
		return 0
	end
	return fin - ahora
end

-- Energía que tiene un luchador ahora, sabiendo la que tenía en el instante `desde` y su regeneración por segundo.
function Reglas.EnergiaActual(energia: number, maxima: number, porSegundo: number, desde: number, ahora: number): number
	local transcurrido = math.max(0, ahora - desde)
	return math.min(maxima, energia + porSegundo * transcurrido)
end

function Reglas.TieneEnergia(energia: number, coste: number): boolean
	-- Un margen minúsculo evita rechazar por errores de coma flotante de la regeneración.
	return energia + 1e-6 >= coste
end

-- ===== Alcance =====

--[[
	Comprueba la distancia que pide el cliente. Se acepta hasta `rango * holgura` (latencia, redondeos) y
	se recorta al rango real. Devuelve `true` y la distancia ajustada, o `false` si pide demasiado lejos
	(o si no es un número usable).
]]
function Reglas.AjustarAlcance(distancia: number, rango: number, holgura: number?): (boolean, number)
	if distancia ~= distancia or distancia < 0 then
		return false, 0
	end
	if distancia > rango * (holgura or Config.HolguraRango) then
		return false, 0
	end
	return true, math.min(distancia, rango)
end

-- Recorta la pendiente (componente vertical) de una dirección unitaria para que no se apunte al cielo o al suelo.
function Reglas.LimitarPendiente(y: number, maxima: number?): number
	local limite = maxima or Config.PendienteMaxima
	return math.clamp(y, -limite, limite)
end

-- ===== Bandos =====

--[[
	¿Pueden hacerse daño? Los del mismo bando NO. "Ninguno" (sin bando) no cuenta como un bando:
	un jugador sin bando puede dañar y ser dañado por cualquiera.
]]
function Reglas.SonEnemigos(bandoA: string, bandoB: string): boolean
	if bandoA == "Ninguno" or bandoB == "Ninguno" then
		return true
	end
	return bandoA ~= bandoB
end

-- ===== Zonas seguras =====

-- Zona sin PvP: un cilindro vertical (centro, radio y alturas mínima y máxima del mundo).
export type ZonaSegura = { Centro: Punto, Radio: number, AltoMin: number, AltoMax: number }

-- ¿Está el punto dentro de alguna de las zonas seguras?
function Reglas.EnZonaSegura(p: Punto, zonas: { ZonaSegura }): boolean
	for _, zona in zonas do
		local dx, dz = p.X - zona.Centro.X, p.Z - zona.Centro.Z
		if dx * dx + dz * dz <= zona.Radio * zona.Radio and p.Y >= zona.AltoMin and p.Y <= zona.AltoMax then
			return true
		end
	end
	return false
end

--[[
	¿Impide una zona segura este golpe? Sí si el lanzador O el objetivo están dentro: ni se puede atacar a quien
	está a salvo, ni atacar desde dentro de la zona a quien está fuera.
]]
function Reglas.ZonaSeguraImpide(lanzador: Punto, objetivo: Punto, zonas: { ZonaSegura }): boolean
	return Reglas.EnZonaSegura(lanzador, zonas) or Reglas.EnZonaSegura(objetivo, zonas)
end

-- ===== Combo =====

--[[
	Golpe del combo que toca ahora.
	  anterior:    último golpe dado (0 = ninguno).
	  fin:         instante en que terminó el último golpe (su cooldown).
	  ventana:     segundos tras `fin` en los que aún se encadena.
	Si se encadena a tiempo, sube un paso; si el combo estaba completo o se pasó el tiempo, vuelve al 1.
]]
function Reglas.PasoDeCombo(anterior: number, fin: number, ahora: number, ventana: number, total: number): number
	if anterior <= 0 or anterior >= total then
		return 1
	end
	if ahora > fin + ventana then
		return 1
	end
	return anterior + 1
end

-- ===== Geometría =====

local function restar(a: Punto, b: Punto): Punto
	return { X = a.X - b.X, Y = a.Y - b.Y, Z = a.Z - b.Z }
end

local function punto(a: Punto, b: Punto): number
	return a.X * b.X + a.Y * b.Y + a.Z * b.Z
end

local function longitud(a: Punto): number
	return math.sqrt(punto(a, a))
end

-- Distancia del punto `p` al segmento que va de `a` a `b`.
function Reglas.DistanciaASegmento(p: Punto, a: Punto, b: Punto): number
	local ab = restar(b, a)
	local largo2 = punto(ab, ab)
	if largo2 < 1e-9 then
		return longitud(restar(p, a))
	end
	local t = math.clamp(punto(restar(p, a), ab) / largo2, 0, 1)
	local cercano = { X = a.X + ab.X * t, Y = a.Y + ab.Y * t, Z = a.Z + ab.Z * t }
	return longitud(restar(p, cercano))
end

export type Golpe = {
	Forma: string, -- "Linea" | "Area" | "Cono" | "Circulo"
	Origen: Punto, -- posición del lanzador al empezar
	Destino: Punto, -- punto de impacto
	Direccion: Punto, -- dirección unitaria del golpe
	Rango: number,
	Radio: number,
	Angulo: number?, -- solo "Cono": ángulo total en grados
}

--[[
	¿Está `objetivo` dentro de la zona que alcanza el golpe? `margen` es el radio del cuerpo del objetivo.
]]
function Reglas.EnForma(golpe: Golpe, objetivo: Punto, margen: number?): boolean
	local cuerpo = margen or Config.RadioCuerpo
	local forma = golpe.Forma

	if forma == "Linea" then
		return Reglas.DistanciaASegmento(objetivo, golpe.Origen, golpe.Destino) <= golpe.Radio + cuerpo
	elseif forma == "Area" then
		return longitud(restar(objetivo, golpe.Destino)) <= golpe.Radio + cuerpo
	elseif forma == "Circulo" then
		return longitud(restar(objetivo, golpe.Origen)) <= golpe.Radio + cuerpo
	elseif forma == "Cono" then
		local hacia = restar(objetivo, golpe.Origen)
		local distancia = longitud(hacia)
		if distancia > golpe.Rango + cuerpo then
			return false
		end
		if distancia < cuerpo then
			return true -- pegado al lanzador: siempre dentro
		end
		local coseno = punto(hacia, golpe.Direccion) / distancia
		local limite = math.cos(math.rad((golpe.Angulo or 90) / 2))
		return coseno >= limite
	end
	return false
end

-- ¿Está el objetivo a menos de `maximo` studs del lanzador? (no se golpea a quien queda fuera de alcance)
function Reglas.AlAlcance(objetivo: Punto, lanzador: Punto, maximo: number): boolean
	return longitud(restar(objetivo, lanzador)) <= maximo
end

-- ===== Daño =====

-- Vida que queda tras recibir `dano` (nunca baja de 0).
function Reglas.VidaTrasDano(vida: number, dano: number): number
	return math.max(0, vida - math.max(0, dano))
end

return Reglas
