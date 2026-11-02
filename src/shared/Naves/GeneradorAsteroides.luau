--!strict
--[[
	GeneradorAsteroides: decide DÓNDE va cada asteroide de un campo y cómo es. Función pura y determinista.

	No crea Instancias: devuelve una lista de descripciones (posición, tamaño, giro, fragmentos, color...) que el
	servidor convierte en modelos (ServicioAsteroides). Con la misma semilla siempre sale el mismo campo, así que
	se puede probar fuera de Studio y reproducir un campo exacto si hace falta depurarlo.

	Cómo se reparten:
	  - Los asteroides pequeños son mucho más abundantes que los grandes.
	  - Nunca se solapan (se deja una separación mínima, para poder pasar volando entre ellos).
	  - Se respetan las zonas de exclusión: por ejemplo, el pasillo de salida del hangar queda despejado.
	  - Cada asteroide es una esfera central más unos fragmentos de roca pegados, para que no parezca una bola.
]]

local Azar = require(script.Parent.Parent.Utilidades.Azar)

export type Punto = { X: number, Y: number, Z: number }

export type Exclusion = { Centro: Punto, Radio: number }

export type Opciones = {
	Semilla: number,
	Cantidad: number,
	Centro: Punto,
	Radio: number, -- radio de la región donde se reparten
	Aplanado: number?, -- 1 = esfera; 0.3 = disco achatado (cinturón). Por defecto 1
	TamanoMin: number?, -- diámetro de los más pequeños (por defecto 5)
	TamanoMax: number?, -- diámetro de los más grandes (por defecto 28)
	Separacion: number?, -- hueco mínimo entre dos asteroides, en studs (por defecto 10)
	Exclusiones: { Exclusion }?,
}

export type Fragmento = {
	Forma: string, -- "Bloque" | "Esfera"
	Desplazamiento: Punto, -- respecto al centro del asteroide
	Tamano: Punto, -- medidas en studs
	Giro: Punto, -- ángulos en radianes
}

export type Asteroide = {
	Posicion: Punto,
	Tamano: number, -- diámetro de la esfera central
	Giro: Punto,
	Material: string, -- "Roca" | "Basalto"
	Tono: number, -- 0..1: de más claro a más oscuro (el servidor lo traduce a color)
	Vida: number,
	Fragmentos: { Fragmento },
}

local GeneradorAsteroides = {}

-- Vida de un asteroide según su diámetro: los grandes aguantan varios disparos.
function GeneradorAsteroides.VidaPara(tamano: number): number
	return math.floor(tamano * 2.6)
end

-- Radio que ocupa un asteroide contando sus fragmentos (para que no se solapen).
local function radioOcupado(tamano: number): number
	return tamano * 0.5 * 1.35
end

local function distancia(a: Punto, b: Punto): number
	local dx, dy, dz = a.X - b.X, a.Y - b.Y, a.Z - b.Z
	return math.sqrt(dx * dx + dy * dy + dz * dz)
end

local function crearFragmentos(azar: Azar.Azar, tamano: number): { Fragmento }
	local lista: { Fragmento } = {}
	for _ = 1, azar:Entero(2, 4) do
		local dx, dy, dz = azar:Direccion()
		local escala = azar:Entre(0.45, 0.8)
		local lado = tamano * escala
		table.insert(lista, {
			Forma = if azar:Siguiente() < 0.25 then "Esfera" else "Bloque",
			Desplazamiento = { X = dx * tamano * 0.3, Y = dy * tamano * 0.3, Z = dz * tamano * 0.3 },
			Tamano = {
				X = lado * azar:Entre(0.8, 1.3),
				Y = lado * azar:Entre(0.8, 1.3),
				Z = lado * azar:Entre(0.8, 1.3),
			},
			Giro = {
				X = azar:Entre(0, math.pi * 2),
				Y = azar:Entre(0, math.pi * 2),
				Z = azar:Entre(0, math.pi * 2),
			},
		})
	end
	return lista
end

--[[
	Genera el campo. Si no consigue colocar todos los asteroides (región demasiado llena), devuelve los que
	haya colocado: nunca se queda en un bucle infinito.
]]
function GeneradorAsteroides.Generar(opciones: Opciones): { Asteroide }
	local azar = Azar.nuevo(opciones.Semilla)
	local tamanoMin = opciones.TamanoMin or 5
	local tamanoMax = opciones.TamanoMax or 28
	local separacion = opciones.Separacion or 10
	local aplanado = opciones.Aplanado or 1
	local centro = opciones.Centro
	local exclusiones = opciones.Exclusiones or {}

	local resultado: { Asteroide } = {}
	local INTENTOS = 40

	for _ = 1, opciones.Cantidad do
		-- Tamaño: la potencia reparte muchos pequeños y pocos grandes.
		local tamano = tamanoMin + (tamanoMax - tamanoMin) * (azar:Siguiente() ^ 2.2)
		local colocado: Punto? = nil

		for _ = 1, INTENTOS do
			local dx, dy, dz = azar:Direccion()
			-- Raíz cúbica: reparte uniformemente por el volumen y no amontona en el centro.
			local radio = opciones.Radio * azar:Siguiente() ^ (1 / 3)
			local candidato: Punto = {
				X = centro.X + dx * radio,
				Y = centro.Y + dy * radio * aplanado,
				Z = centro.Z + dz * radio,
			}

			local libre = true
			for _, zona in exclusiones do
				if distancia(candidato, zona.Centro) < zona.Radio + radioOcupado(tamano) then
					libre = false
					break
				end
			end
			if libre then
				for _, otro in resultado do
					local minimo = radioOcupado(tamano) + radioOcupado(otro.Tamano) + separacion
					if distancia(candidato, otro.Posicion) < minimo then
						libre = false
						break
					end
				end
			end
			if libre then
				colocado = candidato
				break
			end
		end

		if colocado then
			table.insert(resultado, {
				Posicion = colocado,
				Tamano = tamano,
				Giro = {
					X = azar:Entre(0, math.pi * 2),
					Y = azar:Entre(0, math.pi * 2),
					Z = azar:Entre(0, math.pi * 2),
				},
				Material = if azar:Siguiente() < 0.3 then "Basalto" else "Roca",
				Tono = azar:Siguiente(),
				Vida = GeneradorAsteroides.VidaPara(tamano),
				Fragmentos = crearFragmentos(azar, tamano),
			})
		end
	end

	return resultado
end

return GeneradorAsteroides
