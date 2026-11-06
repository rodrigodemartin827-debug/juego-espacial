--!strict
--[[
	Apariencia (Planetas): reparte las PIEZAS que forman el aspecto de un planeta visto desde el espacio.

	Un planeta es una esfera grande (el océano o la roca) con unas pocas piezas encima: continentes, casquetes,
	grietas luminosas y nubes. Cada pieza es un elipsoide muy aplanado (una "lente") tumbado sobre la esfera, que
	asoma solo un poco: de lejos se ve como una mancha de otro color pintada en el planeta, sin necesidad de
	texturas ni mallas propias. Las nubes van en una capa aparte, algo más alta, que el cliente hace girar.

	Este módulo es PURO (solo cuentas y una semilla): devuelve la lista de piezas y el cliente
	(client/Planetas/Construccion) crea una parte por pieza. Con la misma semilla sale siempre el mismo planeta.

	Coordenadas: relativas al centro del planeta, en studs reales.
]]

local Datos = require(script.Parent.Datos)
local Azar = require(script.Parent.Parent.Utilidades.Azar)
local V = require(script.Parent.Vectores)

type Vec = V.Vec

export type Pieza = {
	Direccion: Vec, -- normal de la superficie donde se apoya (unitaria)
	Distancia: number, -- del centro del planeta al centro de la pieza
	Tamano: Vec, -- diámetros del elipsoide: X y Z a lo largo de la superficie, Y a lo largo de la normal
	Giro: number, -- radianes alrededor de la normal
	Color: string,
}

local Apariencia = {}

-- Dirección al azar dentro de una franja de latitudes (grados), repartida por igual en superficie.
local function direccionEnFranja(azar: Azar.Azar, latMin: number, latMax: number): Vec
	local s0, s1 = math.sin(math.rad(latMin)), math.sin(math.rad(latMax))
	local y = azar:Entre(math.min(s0, s1), math.max(s0, s1))
	local angulo = azar:Entre(0, math.pi * 2)
	local r = math.sqrt(math.max(0, 1 - y * y))
	return { X = r * math.cos(angulo), Y = y, Z = r * math.sin(angulo) }
end

-- Gira la dirección `base` un ángulo `desvio` (radianes) hacia un lado al azar.
local function desviar(azar: Azar.Azar, base: Vec, desvio: number): Vec
	local referencia: Vec = if math.abs(base.Y) < 0.9 then { X = 0, Y = 1, Z = 0 } else { X = 1, Y = 0, Z = 0 }
	local t1 = V.unitario(V.cruz(base, referencia))
	local t2 = V.cruz(base, t1)
	local angulo = azar:Entre(0, math.pi * 2)
	local lado = V.sumar(V.escalar(t1, math.cos(angulo)), V.escalar(t2, math.sin(angulo)))
	return V.unitario(V.sumar(V.escalar(base, math.cos(desvio)), V.escalar(lado, math.sin(desvio))))
end

--[[
	Grosor mínimo de una lente de radio `a` sobre una esfera de radio `r` para que sus bordes queden por debajo
	de la superficie (la esfera se curva y una lente plana sobresaldría por los lados), más lo que asoma.
]]
function Apariencia.GrosorLente(a: number, r: number, asoma: number): number
	return 1.15 * a * a / (2 * r) + asoma
end

--[[
	Piezas de una capa "Manchas" o "Nubes" de un planeta de radio `radio`.
	  Manchas: asoman `Relieve` × radio sobre la esfera.
	  Nubes: se apoyan en una esfera de radio `Escala` × radio, con el grosor de `Aplanado`.
]]
function Apariencia.Piezas(capa: Datos.CapaPlaneta, radio: number): { Pieza }
	local azar = Azar.nuevo(capa.Semilla or 1)
	local piezas: { Pieza } = {}
	local cantidad = capa.Cantidad or 0
	local rango = capa.Piezas or { 1, 1 }
	local tamanos = capa.Tamano or { 0.1, 0.1 }
	local franja = capa.Latitud or { -90, 90 }
	local colores = capa.Colores or { capa.Color }
	local esNube = capa.Tipo == "Nubes"
	local base = if esNube then radio * (capa.Escala or 1.02) else radio

	for grupo = 1, cantidad do
		local latMin, latMax = franja[1], franja[2]
		if capa.Polos and grupo % 2 == 0 then
			latMin, latMax = -latMax, -latMin -- un casquete en cada polo
		end
		local centro = direccionEnFranja(azar, latMin, latMax)
		local color = colores[((grupo - 1) % #colores) + 1]
		for _ = 1, azar:Entero(rango[1], rango[2]) do
			local a = azar:Entre(tamanos[1], tamanos[2]) * radio / 2 -- semieje a lo largo de la superficie
			-- Las piezas de un grupo se reparten alrededor de su centro: forman una mancha de borde irregular.
			local direccion = desviar(azar, centro, azar:Entre(0, (tamanos[2] * 0.9)))
			local grosor: number
			if esNube then
				grosor = math.max(a * (capa.Aplanado or 0.1), Apariencia.GrosorLente(a, base, 0) * 0.5)
			else
				grosor = Apariencia.GrosorLente(a, base, (capa.Relieve or 0.004) * radio)
			end
			local distancia = if esNube then base else base + (capa.Relieve or 0.004) * radio - grosor
			local ancho = a * azar:Entre(0.7, 1.3) -- algo alargadas
			table.insert(piezas, {
				Direccion = direccion,
				Distancia = distancia,
				Tamano = { X = ancho * 2, Y = grosor * 2, Z = a * 2 },
				Giro = azar:Entre(0, math.pi),
				Color = color,
			})
		end
	end
	return piezas
end

-- Cuántas partes hará falta crear para un planeta (para vigilar el rendimiento en las pruebas).
function Apariencia.ContarPartes(id: string): number
	local total = 0
	for _, capa in Datos.Planetas[id].Apariencia do
		if capa.Tipo == "Manchas" or capa.Tipo == "Nubes" then
			total += #Apariencia.Piezas(capa, Datos.Planetas[id].Radio)
		elseif capa.Tipo == "Esfera" then
			total += 1
		end
	end
	return total
end

return Apariencia
