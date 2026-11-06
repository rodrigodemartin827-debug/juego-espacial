--!strict
--[[
	Persiana (reglas): cuándo sube y baja la persiana de una tienda, y en qué posición está en cada instante de la
	animación. FUNCIONES PURAS: no usan Roblox, así que las pruebas las ejecutan fuera de Studio.

	  Nuevo, Evaluar    el estado de una persiana (lo usa el servidor, que es quien decide).
	  Duracion, Valor   las curvas de la animación (las usa el cliente para moverla).

	La posición se mide como "cierre": 0 = recogida en el cajón (tienda abierta), 1 = tocando el suelo (cerrada). Durante
	la anticipación y los rebotes sale un poco de ese rango a propósito.
]]

local ConfigTiendas = require(script.Parent.Config)
local DatosPersiana = require(script.Parent.Datos.Persiana)

export type Estado = {
	Bajada: boolean,
	LibreDesde: number?, -- con la persiana bajada: instante desde el que no hay ningún monstruo dentro de RadioApertura
}

export type Reglas = {
	RadioCierre: number,
	RadioApertura: number,
	SegundosParaReabrir: number,
}

export type Tipo = "Cierre" | "Apertura"

local Persiana = {}

-- Estado inicial: subida (tienda abierta).
function Persiana.Nuevo(): Estado
	return { Bajada = false, LibreDesde = nil }
end

--[[
	Actualiza `estado` EN SITIO según la distancia del monstruo más cercano (`math.huge` si no hay ninguno) en el instante
	`ahora` (segundos). Devuelve true si la persiana ha cambiado (ha bajado o ha subido).

	  - Subida: baja en cuanto hay un monstruo a RadioCierre o menos.
	  - Bajada: sube cuando lleva SegundosParaReabrir seguidos sin ningún monstruo a RadioApertura o menos.
]]
function Persiana.Evaluar(estado: Estado, distancia: number, ahora: number, reglas: Reglas?): boolean
	local r: Reglas = reglas or ConfigTiendas
	-- Una distancia que no es un número válido (NaN) cuenta como "hay alguien encima": antes cerrar que vender a un monstruo.
	local cerca = distancia ~= distancia or distancia <= r.RadioCierre
	local dentro = distancia ~= distancia or distancia <= r.RadioApertura

	if not estado.Bajada then
		if cerca then
			estado.Bajada = true
			estado.LibreDesde = nil
			return true
		end
		return false
	end

	if dentro then
		estado.LibreDesde = nil
		return false
	end
	if estado.LibreDesde == nil then
		estado.LibreDesde = ahora
	end
	if ahora - (estado.LibreDesde :: number) >= r.SegundosParaReabrir then
		estado.Bajada = false
		estado.LibreDesde = nil
		return true
	end
	return false
end

-- ===== Curvas de la animación =====

type Tiempos = typeof(DatosPersiana.Tiempos)

local function limitar(u: number): number
	return math.clamp(u, 0, 1)
end

-- Aceleración y frenada suaves (cúbica).
local function entradaSalida(u: number): number
	if u < 0.5 then
		return 4 * u * u * u
	end
	local v = -2 * u + 2
	return 1 - v * v * v / 2
end

-- Duración total de una animación.
function Persiana.Duracion(tipo: Tipo, tiempos: Tiempos?): number
	local t = tiempos or DatosPersiana.Tiempos
	if tipo == "Cierre" then
		return t.Anticipacion + t.Caida + t.Congelado + t.Rebote
	end
	return t.Desbloqueo + t.Subida + t.Asentado
end

-- Instante (desde el principio de la animación de cierre) en que la persiana toca el suelo.
function Persiana.InstanteImpacto(tiempos: Tiempos?): number
	local t = tiempos or DatosPersiana.Tiempos
	return t.Anticipacion + t.Caida
end

--[[
	Cierre de la persiana `segundos` después de empezar la animación `tipo`. Antes de empezar vale lo que valía (0 al
	cerrar, 1 al abrir) y al terminar vale exactamente el estado final (1 al cerrar, 0 al abrir).
]]
function Persiana.Valor(tipo: Tipo, segundos: number, tiempos: Tiempos?): number
	local t = tiempos or DatosPersiana.Tiempos
	local s = math.max(segundos, 0)
	-- Al terminar, el valor final exacto (restar fases acumula errores de redondeo).
	if s >= Persiana.Duracion(tipo, t) then
		return if tipo == "Cierre" then 1 else 0
	end

	if tipo == "Cierre" then
		-- Anticipación: asoma un poco y se recoge.
		if s < t.Anticipacion then
			return t.AmplitudAnticipacion * math.sin(math.pi * limitar(s / t.Anticipacion))
		end
		s -= t.Anticipacion
		-- Caída acelerada, como un peso que se suelta.
		if s < t.Caida then
			local u = limitar(s / t.Caida)
			return u * u
		end
		s -= t.Caida
		-- Congelado en el suelo (hitstop).
		if s < t.Congelado then
			return 1
		end
		s -= t.Congelado
		-- Dos rebotes que se apagan.
		if s < t.Rebote then
			local u = limitar(s / t.Rebote)
			return 1 - t.AmplitudRebote * math.abs(math.sin(2 * math.pi * u)) * (1 - u) ^ 2
		end
		return 1
	end

	-- Desbloqueo: tiembla en el suelo.
	if s < t.Desbloqueo then
		local u = limitar(s / t.Desbloqueo)
		return 1 - t.AmplitudDesbloqueo * math.abs(math.sin(3 * math.pi * u))
	end
	s -= t.Desbloqueo
	-- Subida suave.
	if s < t.Subida then
		return 1 - entradaSalida(limitar(s / t.Subida))
	end
	s -= t.Subida
	-- Asentado: se recoge un poco más dentro del cajón y vuelve.
	if s < t.Asentado then
		return -t.AmplitudAsentado * math.sin(math.pi * limitar(s / t.Asentado))
	end
	return 0
end

return Persiana
