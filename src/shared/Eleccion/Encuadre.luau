--!strict
--[[
	Encuadre (Elección de bando): cálculos de cámara e interfaz que dependen del tamaño de la pantalla.

	Roblox fija el campo de visión VERTICAL de la cámara, así que en una pantalla estrecha (un móvil en vertical,
	una tableta 4:3) se vería menos escena a los lados y los planetas quedarían cortados. Aquí se calcula el campo
	vertical que hace caber siempre el mismo ANCHO de escena, y el tamaño de la interfaz para cada pantalla.

	Sin nada de Roblox: se prueba con Lune.
]]

local Encuadre = {}

--[[
	Campo de visión vertical (grados) para que a `distancia` studs de la cámara quepan `mitadAncho` studs a cada lado
	del centro, en una pantalla de proporción `aspecto` (ancho / alto). Se limita entre `minimo` y `maximo`: con un
	campo enorme la imagen se deforma, y con uno pequeño sobraría cielo.
]]
function Encuadre.CampoVertical(
	aspecto: number,
	mitadAncho: number,
	distancia: number,
	minimo: number,
	maximo: number
): number
	if aspecto ~= aspecto or aspecto <= 0 then
		aspecto = 16 / 9 -- tamaño de pantalla aún desconocido
	end
	local tanHorizontal = mitadAncho / math.max(distancia, 1e-3)
	local tanVertical = tanHorizontal / aspecto
	local grados = math.deg(2 * math.atan(tanVertical))
	return math.clamp(grados, minimo, maximo)
end

export type Disposicion = {
	Compacta: boolean, -- pantalla pequeña: textos y paneles más apretados
	Vertical: boolean, -- más alta que ancha: los paneles van uno encima del otro
	Escala: number, -- multiplicador del tamaño de toda la interfaz (UIScale)
	AnchoPanel: number, -- fracción del ancho de la pantalla que ocupa cada panel de bando
}

-- Tamaño de referencia: la interfaz está diseñada a 1280 x 720 píxeles.
local ALTO_REFERENCIA = 720
local ANCHO_REFERENCIA = 1280

--[[
	Cómo colocar la interfaz en una pantalla de `ancho` x `alto` píxeles. La escala sigue al lado más limitante,
	con un mínimo para que en un móvil pequeño el texto se siga leyendo.
]]
function Encuadre.Disposicion(ancho: number, alto: number): Disposicion
	ancho = math.max(ancho, 1)
	alto = math.max(alto, 1)
	local vertical = alto > ancho
	local escala = math.min(alto / ALTO_REFERENCIA, ancho / ANCHO_REFERENCIA)
	local compacta = alto < 500 or ancho < 900
	return {
		Compacta = compacta,
		Vertical = vertical,
		Escala = math.clamp(escala, if compacta then 0.62 else 0.75, 1.6),
		AnchoPanel = if vertical then 0.86 elseif compacta then 0.4 else 0.3,
	}
end

return Encuadre
