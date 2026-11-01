--!strict
--[[
	Capa "Haz": rayos con zigzag hechos con Beams (tantos tramos rectos como Segmentos).

	  Desde, Hasta     anclas ("Cielo" -> "Objetivo"), con DesplazamientoDesde / DesplazamientoHasta opcionales
	  Segmentos        tramos del rayo (más = más quebrado). Se reduce en móviles lentos
	  Desviacion       studs que se puede apartar cada punto de la línea recta
	  Ancho            { inicio, fin } del grosor durante la vida del rayo ({1.2, 0})
	  Color, Textura   color/degradado y nombre en Recursos.Texturas
	  Duracion         segundos que dura
	  Parpadeos        cuántas veces cambia de forma mientras dura (da la sensación de electricidad)
	  Ramas            rayos más pequeños que salen del principal
	  Grupo            capas con el mismo Grupo (y mismos Segmentos y Desviacion) comparten el zigzag: sirve para
	                   poner un núcleo blanco fino sobre un halo de color grueso
	  Brillo           LightEmission (1)
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Recursos = require(ReplicatedStorage:WaitForChild("Shared").Combate.Datos.Recursos)
local Actores = require(script.Parent.Parent.Actores)
local Calidad = require(script.Parent.Parent.Calidad)
local Pool = require(script.Parent.Parent.Pool)
local Utiles = require(script.Parent.Parent.Utiles)

local Haz = {}

-- Coloca los puntos del rayo entre `desde` y `hasta` con desvíos deterministas según `semilla`.
local function colocar(
	objeto: Pool.Haz,
	segmentos: number,
	desde: Vector3,
	hasta: Vector3,
	desviacion: number,
	semilla: number
)
	local rng = Random.new(semilla)
	local eje = hasta - desde
	local largo = eje.Magnitude
	local frente = if largo > 0.01 then eje / largo else Vector3.yAxis
	local lateral = frente:Cross(Vector3.yAxis)
	lateral = if lateral.Magnitude > 0.05 then lateral.Unit else Vector3.xAxis
	local vertical = lateral:Cross(frente)

	for indice = 0, segmentos do
		local punto = desde + eje * (indice / segmentos)
		if indice > 0 and indice < segmentos then
			-- El desvío es mayor en el medio del rayo y nulo en los extremos.
			local envolvente = math.sin(math.pi * indice / segmentos)
			punto += lateral * rng:NextNumber(-1, 1) * desviacion * envolvente
			punto += vertical * rng:NextNumber(-1, 1) * desviacion * envolvente
		end
		objeto.Adjuntos[indice + 1].WorldPosition = punto
	end
end

local function configurar(objeto: Pool.Haz, segmentos: number, capa: any, ctx: any)
	local color = Utiles.Gradiente(capa.Color or "Principal", ctx.Paleta)
	local textura = Recursos.Texturas[capa.Textura or "Rayo"] or capa.Textura
	for indice, rayo in objeto.Rayos do
		rayo.Enabled = indice <= segmentos
		rayo.Color = color
		rayo.Texture = textura
		rayo.TextureMode = Enum.TextureMode.Stretch
		rayo.LightEmission = capa.Brillo or 1
		rayo.Transparency = NumberSequence.new(0)
	end
end

local function ancho(objeto: Pool.Haz, valor: number)
	for _, rayo in objeto.Rayos do
		rayo.Width0 = valor
		rayo.Width1 = valor
	end
end

-- Un rayo (principal o rama) animado con el actor común.
local function animar(
	objeto: Pool.Haz,
	segmentos: number,
	desde: Vector3,
	hasta: Vector3,
	capa: any,
	semillaBase: number,
	escala: number
)
	local duracion: number = capa.Duracion or 0.3
	local desviacion: number = (capa.Desviacion or 3) * escala
	local ancho0, ancho1 = 1.2, 0
	if type(capa.Ancho) == "table" then
		ancho0, ancho1 = capa.Ancho[1], capa.Ancho[2] or 0
	elseif type(capa.Ancho) == "number" then
		ancho0 = capa.Ancho
	end
	local parpadeos: number = math.max(1, capa.Parpadeos or 3)
	local periodo = duracion / parpadeos

	objeto.Raiz.CFrame = CFrame.new(desde)
	colocar(objeto, segmentos, desde, hasta, desviacion, semillaBase)
	ancho(objeto, ancho0 * escala)

	local transcurrido, forma = 0, 0
	Actores.Agregar(function(dt)
		transcurrido += dt
		local alfa = math.clamp(transcurrido / duracion, 0, 1)

		local nuevaForma = math.floor(transcurrido / periodo)
		if nuevaForma ~= forma then
			forma = nuevaForma
			colocar(objeto, segmentos, desde, hasta, desviacion, semillaBase + forma * 7919)
		end

		local grosor = (ancho0 + (ancho1 - ancho0) * alfa * alfa) * escala
		ancho(objeto, grosor)
		local transparencia = NumberSequence.new(alfa * alfa * 0.9)
		for _, rayo in objeto.Rayos do
			rayo.Transparency = transparencia
		end

		if alfa >= 1 then
			Pool.Liberar(objeto)
			return true
		end
		return false
	end)
end

function Haz.Reproducir(capa: any, ctx: any)
	local factor = Calidad.Factor("Haces")
	local segmentos = math.clamp(math.floor((capa.Segmentos or 8) * factor + 0.5), 3, Pool.MaximoSegmentos)
	local desde = Utiles.Ancla(ctx, capa.Desde or "Cielo", capa.DesplazamientoDesde).Position
	local hasta = Utiles.Ancla(ctx, capa.Hasta or "Objetivo", capa.DesplazamientoHasta).Position

	-- Semilla compartida por las capas del mismo grupo (halo + núcleo).
	ctx.Semillas = ctx.Semillas or {}
	local clave = capa.Grupo or tostring(capa)
	if ctx.Semillas[clave] == nil then
		ctx.Semillas[clave] = Utiles.Azar:NextInteger(1, 1000000)
	end
	local semilla: number = ctx.Semillas[clave]

	local principal = Pool.Haz()
	configurar(principal, segmentos, capa, ctx)
	animar(principal, segmentos, desde, hasta, capa, semilla, 1)

	-- Ramas: pequeños rayos que salen de puntos del principal.
	local ramas = Utiles.Cantidad(capa.Ramas or 0, factor)
	for indice = 1, ramas do
		local rng = Random.new(semilla + indice * 31)
		local t = rng:NextNumber(0.25, 0.85)
		local nacimiento = desde:Lerp(hasta, t)
		local lado = Vector3.new(rng:NextNumber(-1, 1), rng:NextNumber(-0.3, 0.5), rng:NextNumber(-1, 1))
		lado = if lado.Magnitude > 0.05 then lado.Unit else Vector3.xAxis
		local longitud = (hasta - desde).Magnitude * rng:NextNumber(0.15, 0.3)
		local rama = Pool.Haz()
		configurar(rama, 4, capa, ctx)
		animar(rama, 4, nacimiento, nacimiento + lado * longitud, capa, semilla + indice * 977, 0.55)
	end
end

return Haz
