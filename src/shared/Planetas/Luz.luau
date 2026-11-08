--!strict
--[[
	Luz (Planetas): las cuentas de la iluminación por zonas, como FUNCIONES PURAS.

	  Pesos y dirección   cuánto pesa cada preset de Datos/Iluminacion en un punto del espacio y de dónde
	                      viene la luz (del sol, del agujero negro o una mezcla suave de los dos).
	  Mezclar             interpola presets (números y colores "#RRGGBB"); lo que no se puede interpolar
	                      (la Fuente, los interruptores) lo pone el preset que más pesa.
	  Resolver            Roblox no deja poner la dirección de la luz directamente: sale de ClockTime y
	                      GeographicLatitude. Esta función busca la hora y la latitud que la dejan apuntando
	                      hacia donde se pide. No conoce la fórmula de Roblox: recibe una función `evaluar` que la
	                      calcula (el cliente le pasa una que pregunta a Lighting de verdad; las pruebas, una de
	                      mentira). Primero mira una tabla de muestras y luego afina alrededor del mejor punto.
]]

local Datos = require(script.Parent.Datos)
local DatosLuz = require(script.Parent.Datos.Iluminacion)
local V = require(script.Parent.Vectores)

type Vec = V.Vec

-- Dirección del sol y de la luna para una hora y una latitud.
export type Evaluar = (hora: number, latitud: number) -> (Vec, Vec)

export type Muestra = { Hora: number, Latitud: number, Sol: Vec, Luna: Vec }

local Luz = {}

-- ===== Colores =====

-- "#RRGGBB" -> r, g, b (0..255). Un texto mal formado da negro.
function Luz.Hex(hex: string): (number, number, number)
	local r, g, b = string.match(hex, "^#?(%x%x)(%x%x)(%x%x)$")
	if r == nil or g == nil or b == nil then
		return 0, 0, 0
	end
	return tonumber(r, 16) or 0, tonumber(g, 16) or 0, tonumber(b, 16) or 0
end

-- r, g, b (0..255) -> "#RRGGBB" (se redondea y se limita).
function Luz.AHex(r: number, g: number, b: number): string
	local function canal(c: number): number
		return math.clamp(math.floor(c + 0.5), 0, 255)
	end
	return string.format("#%02X%02X%02X", canal(r), canal(g), canal(b))
end

local function esColor(valor: any): boolean
	return type(valor) == "string" and string.match(valor, "^#%x%x%x%x%x%x$") ~= nil
end

-- ===== Mezcla de presets =====

--[[
	Mezcla varios presets (o tablas cualesquiera con la misma forma) con sus pesos. Los pesos no hace falta que
	sumen 1. Números y colores se interpolan; el resto de valores (textos, booleanos) se toman del más pesado.
]]
function Luz.Mezclar(presets: { any }, pesos: { number }): any
	local total = 0
	local mayor, indiceMayor = -math.huge, 1
	for indice, peso in pesos do
		total += math.max(peso, 0)
		if peso > mayor then
			mayor, indiceMayor = peso, indice
		end
	end
	if total <= 0 then
		total, pesos = 1, { 1 }
		indiceMayor = 1
	end

	local base = presets[indiceMayor]
	local resultado: { [string]: any } = {}
	for clave, valor in base do
		if type(valor) == "number" then
			local suma = 0
			for indice, preset in presets do
				local p = math.max(pesos[indice] or 0, 0)
				local v = preset[clave]
				suma += (if type(v) == "number" then v else valor) * p
			end
			resultado[clave] = suma / total
		elseif esColor(valor) then
			local r: number, g: number, b: number = 0, 0, 0
			for indice, preset in presets do
				local p = math.max(pesos[indice] or 0, 0)
				local v = preset[clave]
				local cr, cg, cb = Luz.Hex(if esColor(v) then v :: string else valor :: string)
				r += cr * p
				g += cg * p
				b += cb * p
			end
			resultado[clave] = Luz.AHex(r / total, g / total, b / total)
		elseif type(valor) == "table" then
			local partes = {}
			for indice, preset in presets do
				partes[indice] = if type(preset[clave]) == "table" then preset[clave] else valor
			end
			resultado[clave] = Luz.Mezclar(partes, pesos)
		else
			resultado[clave] = valor
		end
	end
	return resultado
end

-- Acerca `actual` a `objetivo` (transición suave independiente de los fotogramas). Devuelve un preset nuevo.
function Luz.Acercar(actual: any, objetivo: any, dt: number, rapidez: number): any
	local alfa = 1 - math.exp(-math.max(rapidez, 0) * math.max(dt, 0))
	if alfa >= 0.999 then
		return Luz.Mezclar({ objetivo }, { 1 })
	end
	-- Los valores no interpolables cambian a mitad de camino (no al primer fotograma).
	return Luz.Mezclar({ actual, objetivo }, { 1 - alfa, alfa + 1e-9 })
end

-- ===== Pesos y dirección en el espacio =====

-- Peso (0..1) de una fuente según la distancia: 1 dentro de RadioPleno, 0 a partir de RadioNulo.
local function pesoFuente(distancia: number, mezcla: { RadioPleno: number, RadioNulo: number }): number
	return 1 - V.suave(mezcla.RadioPleno, mezcla.RadioNulo, distancia)
end

--[[
	Pesos de los presets del espacio en `posicion`: devuelve la lista de nombres y la de pesos (suman 1).
]]
function Luz.PesosEspacio(posicion: Vec): ({ string }, { number })
	local mezcla = DatosLuz.Mezcla
	local sol = pesoFuente(V.distancia(posicion, Datos.Sol.Centro), mezcla.Sol)
	local agujero = pesoFuente(V.distancia(posicion, Datos.AgujeroNegro.Centro), mezcla.AgujeroNegro)
	local suma = sol + agujero
	if suma > 1 then
		sol, agujero = sol / suma, agujero / suma
		suma = 1
	end
	return { mezcla.Sol.Preset, mezcla.AgujeroNegro.Preset, mezcla.Profundo }, { sol, agujero, 1 - suma }
end

--[[
	De dónde viene la luz en un punto del espacio (vector unitario HACIA la fuente). Cerca de una fuente apunta a
	ella; entre las dos se mezcla, con un pequeño peso por cercanía para que nunca se quede sin dirección.
]]
function Luz.DireccionEspacio(posicion: Vec): Vec
	local _, pesos = Luz.PesosEspacio(posicion)
	local haciaSol = V.restar(Datos.Sol.Centro, posicion)
	local haciaAgujero = V.restar(Datos.AgujeroNegro.Centro, posicion)
	local dSol, dAgujero = math.max(V.largo(haciaSol), 1), math.max(V.largo(haciaAgujero), 1)
	-- El peso por cercanía (inverso del cuadrado) solo decide cuando los dos pesos de mezcla son 0.
	local cercaniaSol = 1e-3 * (10000 / dSol) ^ 2
	local cercaniaAgujero = 1e-3 * (10000 / dAgujero) ^ 2
	local a = pesos[1] + cercaniaSol
	local b = pesos[2] + cercaniaAgujero
	return V.unitario(V.sumar(V.escalar(V.unitario(haciaSol), a), V.escalar(V.unitario(haciaAgujero), b)))
end

--[[
	La luz direccional de Roblox no puede venir de debajo del horizonte (por debajo se hace de noche y la luz pasa
	a la luna, que sale por el otro lado). Si la dirección pedida está por debajo de `minimo` grados, se sube
	hasta ahí conservando el rumbo.
]]
function Luz.LimitarElevacion(direccion: Vec, minimo: number): Vec
	local d = V.unitario(direccion)
	local elevacion = math.deg(math.asin(math.clamp(d.Y, -1, 1)))
	if elevacion >= minimo then
		return d
	end
	local horizontal = V.unitario({ X = d.X, Y = 0, Z = d.Z }, { X = 1, Y = 0, Z = 0 })
	local angulo = math.rad(minimo)
	return { X = horizontal.X * math.cos(angulo), Y = math.sin(angulo), Z = horizontal.Z * math.cos(angulo) }
end

--[==[
	Baja la dirección de la luz hasta `maximo` grados sobre el horizonte del sitio (el plano perpendicular a `arriba`),
	conservando de qué lado viene. Si ya está más baja, no la toca. Es la hora dorada: sol bajo y sombras largas.
]==]
function Luz.TopeElevacion(direccion: Vec, arriba: Vec, maximo: number): Vec
	local d = V.unitario(direccion)
	local u = V.unitario(arriba)
	local seno = math.clamp(d.X * u.X + d.Y * u.Y + d.Z * u.Z, -1, 1)
	if math.deg(math.asin(seno)) <= maximo then
		return d
	end
	-- Si la luz viene justo de arriba no hay «lado»: se elige uno cualquiera perpendicular a `arriba`.
	local eje = if math.abs(u.Y) < 0.9 then { X = 0, Y = 1, Z = 0 } else { X = 1, Y = 0, Z = 0 }
	local lado = V.unitario({
		X = u.Y * eje.Z - u.Z * eje.Y,
		Y = u.Z * eje.X - u.X * eje.Z,
		Z = u.X * eje.Y - u.Y * eje.X,
	})
	local horizontal = V.unitario({ X = d.X - u.X * seno, Y = d.Y - u.Y * seno, Z = d.Z - u.Z * seno }, lado)
	local a = math.rad(maximo)
	local s, c = math.sin(a), math.cos(a)
	return {
		X = u.X * s + horizontal.X * c,
		Y = u.Y * s + horizontal.Y * c,
		Z = u.Z * s + horizontal.Z * c,
	}
end

-- ===== Búsqueda de hora y latitud =====

--[[
	Prepara la tabla de muestras: prueba todas las horas (cada `pasoHora`) y latitudes (cada `pasoLatitud`, de −90 a
	90). `ceder` (opcional) se llama cada cierto número de muestras para repartir el trabajo entre fotogramas.
]]
function Luz.CrearTabla(evaluar: Evaluar, pasoHora: number, pasoLatitud: number, ceder: (() -> ())?): { Muestra }
	local tabla: { Muestra } = {}
	local contador = 0
	local hora = 0
	while hora < 24 do
		local latitud = -90
		while latitud <= 90 do
			local sol, luna = evaluar(hora, latitud)
			table.insert(tabla, { Hora = hora, Latitud = latitud, Sol = sol, Luna = luna })
			contador += 1
			if ceder and contador % 400 == 0 then
				ceder()
			end
			latitud += pasoLatitud
		end
		hora += pasoHora
	end
	return tabla
end

-- ¿Sirve esa combinación para esa fuente? Con "Luna" tiene que ser de noche (sol bajo el horizonte), y con
-- "Sol", de día; si no, Roblox usaría la otra luz.
local function valida(fuente: string, sol: Vec, luna: Vec): boolean
	if fuente == "Luna" then
		return sol.Y < -0.02 and luna.Y > 0
	end
	return sol.Y > 0.02
end

local function errorDe(fuente: string, objetivo: Vec, sol: Vec, luna: Vec): number
	if not valida(fuente, sol, luna) then
		return math.huge
	end
	return V.angulo(objetivo, if fuente == "Luna" then luna else sol)
end

--[[
	Hora y latitud con las que la luz `fuente` ("Sol" o "Luna") apunta hacia `objetivo`. Devuelve la hora, la
	latitud y el error en grados (math.huge si ninguna muestra sirve). `refinados` pasos de búsqueda fina.
]]
function Luz.Resolver(
	objetivo: Vec,
	fuente: string,
	evaluar: Evaluar,
	tabla: { Muestra },
	pasoHora: number,
	pasoLatitud: number,
	refinados: number
): (number, number, number)
	local mejorHora, mejorLatitud, mejorError = 12, 0, math.huge
	for _, muestra in tabla do
		local e = errorDe(fuente, objetivo, muestra.Sol, muestra.Luna)
		if e < mejorError then
			mejorHora, mejorLatitud, mejorError = muestra.Hora, muestra.Latitud, e
		end
	end
	if mejorError == math.huge then
		return mejorHora, mejorLatitud, mejorError
	end

	-- Búsqueda fina: se prueba alrededor del mejor punto con pasos cada vez más pequeños.
	local paso1, paso2 = pasoHora, pasoLatitud
	for _ = 1, refinados do
		paso1, paso2 = paso1 / 2, paso2 / 2
		local mejorado = true
		while mejorado do
			mejorado = false
			for _, delta in { { paso1, 0 }, { -paso1, 0 }, { 0, paso2 }, { 0, -paso2 } } do
				local hora = (mejorHora + delta[1]) % 24
				local latitud = math.clamp(mejorLatitud + delta[2], -90, 90)
				local sol, luna = evaluar(hora, latitud)
				local e = errorDe(fuente, objetivo, sol, luna)
				if e < mejorError - 1e-6 then
					mejorHora, mejorLatitud, mejorError = hora, latitud, e
					mejorado = true
				end
			end
		end
	end
	return mejorHora, mejorLatitud, mejorError
end

return Luz
