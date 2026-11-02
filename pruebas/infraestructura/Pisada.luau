--[[
	Pisada: mide cómo pisan los pies de una animación de locomoción R6 (la usan las pruebas de AndarMonstruo y la
	exportación a Blender para sacar sus números).

	Se muestrea la animación muy fino (Pisada.MUESTRAS_POR_SEGUNDO) con la cinemática real del R6
	(Animacion/CinematicaR6) y, en cada muestra, se mira qué pie está en el suelo y qué punto de su planta lo toca.
	Mientras un pie apoya, el personaje avanza a velocidad V y el pie debería quedarse quieto respecto al suelo, es
	decir, moverse hacia atrás respecto al cuerpo a V studs/s (con la animación a velocidad 1). De ahí sale:
	  - VelocidadNatural: la velocidad media a la que el pie de apoyo va hacia atrás (= la velocidad de andar a la
	    que la animación no patina),
	  - Patinaje: cuánto se aleja, de media, el movimiento del pie de esa velocidad (0 = nunca patina),
	  - Aire: fracción del ciclo sin ningún pie en el suelo,
	  - Hundimiento: lo máximo que una esquina del pie se mete por debajo del suelo.
]]

local Pisada = {}

Pisada.MUESTRAS_POR_SEGUNDO = 240
-- Un pie a menos de esto (studs) del suelo cuenta como apoyado.
Pisada.TOLERANCIA_SUELO = 0.04

local PIERNAS = { "Right Leg", "Left Leg" }

-- Esquina más baja de la planta de una pierna: (índice, punto).
local function esquinaMasBaja(Cinematica, marco)
	local mejor, indice = nil, 0
	for i, esquina in Cinematica.EsquinasPie(marco) do
		if mejor == nil or esquina[2] < mejor[2] then
			mejor, indice = esquina, i
		end
	end
	return indice, mejor
end

--[[
	Analiza una definición (formato de Animacion/Horneado). `Horneado` y `Cinematica` son los módulos ya cargados.
	Devuelve { VelocidadNatural, Patinaje, Aire, Hundimiento, Muestras = { {T, Apoyo, Altura} } }.
]]
function Pisada.Analizar(Horneado, Cinematica, definicion)
	local n = math.max(8, math.round(definicion.Duracion * Pisada.MUESTRAS_POR_SEGUNDO))
	local dt = definicion.Duracion / n
	local suelo = Cinematica.ALTURA_SUELO

	local muestras = {}
	local hundimiento = 0
	for i = 0, n do
		local t = definicion.Duracion * i / n
		local piezas = Cinematica.Piezas(Horneado.PoseEn(definicion, t))
		local apoyo, esquina, punto, altura = nil, 0, nil, math.huge
		for _, pierna in PIERNAS do
			local indice, p = esquinaMasBaja(Cinematica, piezas[pierna])
			hundimiento = math.max(hundimiento, suelo - p[2])
			if p[2] < altura then
				apoyo, esquina, punto, altura = pierna, indice, p, p[2]
			end
		end
		local enSuelo = altura - suelo <= Pisada.TOLERANCIA_SUELO
		table.insert(muestras, {
			T = t,
			Apoyo = if enSuelo then apoyo else nil,
			Esquina = esquina,
			Punto = punto,
			Altura = altura - suelo,
		})
	end

	-- Tramos entre muestras seguidas en las que apoya el mismo pie con la misma esquina.
	local recorrido, tiempo = 0, 0
	local velocidades = {}
	local enElAire = 0
	for i = 1, n do
		local a, b = muestras[i], muestras[i + 1]
		if a.Apoyo == nil then
			enElAire += 1
		end
		if a.Apoyo ~= nil and a.Apoyo == b.Apoyo and a.Esquina == b.Esquina then
			local dz = b.Punto[3] - a.Punto[3] -- hacia atrás es +Z (el personaje mira a -Z)
			recorrido += dz
			tiempo += dt
			table.insert(velocidades, dz / dt)
		end
	end

	local natural = if tiempo > 0 then recorrido / tiempo else 0
	local referencia = definicion.VelocidadReferencia or natural
	local suma = 0
	for _, v in velocidades do
		suma += math.abs(v - referencia)
	end
	local patinaje = if #velocidades > 0 and referencia > 0 then suma / #velocidades / referencia else 0

	return {
		VelocidadNatural = natural,
		Patinaje = patinaje, -- error medio relativo a VelocidadReferencia (0,2 = 20 %)
		Aire = enElAire / n,
		Hundimiento = hundimiento,
		Muestras = muestras,
	}
end

return Pisada
