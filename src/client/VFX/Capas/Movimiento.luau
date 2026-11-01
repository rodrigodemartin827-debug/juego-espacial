--!strict
--[[
	Capas con movimiento propio: "Proyectil" y "Corte".

	"Proyectil"  Una bola de energía que viaja de un ancla a otra dejando estela, partículas y luz.
	  Desde, Hasta   anclas ("Mano" -> "Objetivo")
	  Duracion       segundos, o "Viaje" para usar el tiempo de vuelo de la habilidad
	  Diametro       tamaño del núcleo
	  Color, ColorHalo, Halo (multiplicador del tamaño del halo translúcido, 2.2)
	  Altura         arco: studs que se eleva a mitad de trayecto
	  Espiral        { radio, vueltas }: la bola gira alrededor de la trayectoria
	  Estela         { Ancho, Vida, Textura }
	  Chispas        partículas por segundo que suelta (se reduce según la calidad)
	  Luz            brillo de la luz que lleva (0 = sin luz)

	"Corte"  Un tajo con forma de media luna: un punto invisible recorre un arco dejando un Trail ancho.
	  Radio          distancia al centro del arco
	  Arco           { grados de inicio, grados de fin } (0 = delante, positivo = a la derecha)
	  Inclinacion    giro del plano del arco sobre el eje de avance (0 = horizontal, 90 = vertical)
	  Duracion, Color, Estela { Ancho, Vida, Textura }, Easing
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Recursos = require(ReplicatedStorage:WaitForChild("Shared").Combate.Datos.Recursos)
local Actores = require(script.Parent.Parent.Actores)
local Calidad = require(script.Parent.Parent.Calidad)
local Pool = require(script.Parent.Parent.Pool)
local Utiles = require(script.Parent.Parent.Utiles)

local Movimiento = {}

-- Configura un Trail de la reserva con las opciones de la capa.
local function configurarRastro(
	rastro: Trail,
	a0: Attachment,
	a1: Attachment,
	opciones: any,
	color: ColorSequence,
	ctx: any
)
	local ancho: number = opciones.Ancho or 1.5
	a0.Position = Vector3.new(0, ancho / 2, 0)
	a1.Position = Vector3.new(0, -ancho / 2, 0)
	rastro.Texture = Recursos.Texturas[opciones.Textura or "Rastro"] or opciones.Textura
	rastro.TextureMode = Enum.TextureMode.Stretch
	rastro.Lifetime = opciones.Vida or 0.3
	rastro.Color = color
	rastro.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.05),
		NumberSequenceKeypoint.new(1, 1),
	})
	rastro.WidthScale = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(1, 0),
	})
	rastro.LightEmission = 1
	rastro.MinLength = 0.05
	rastro.Enabled = true
	rastro:Clear()
end

function Movimiento.Proyectil(capa: any, ctx: any)
	local desde = Utiles.Ancla(ctx, capa.Desde or "Mano", capa.DesplazamientoDesde).Position
	local hasta = Utiles.Ancla(ctx, capa.Hasta or "Objetivo", capa.DesplazamientoHasta).Position
	local duracion: number = if capa.Duracion == "Viaje" then math.max(ctx.Viaje, 0.06) else (capa.Duracion or 0.3)
	local diametro: number = capa.Diametro or 2

	-- Núcleo y halo.
	local nucleo = Pool.Parte("Bola")
	nucleo.Size = Vector3.one * diametro
	nucleo.Color = Utiles.Color(capa.ColorNucleo or "Nucleo", ctx.Paleta)
	nucleo.Transparency = 0
	local halo = Pool.Parte("Bola")
	halo.Size = Vector3.one * diametro * (capa.Halo or 2.2)
	halo.Color = Utiles.Color(capa.Color or "Principal", ctx.Paleta)
	halo.Transparency = 0.55

	-- Estela.
	local rastroParte, rastro, a0, a1 = Pool.Rastro()
	configurarRastro(
		rastro,
		a0,
		a1,
		capa.Estela or { Ancho = diametro * 1.2 },
		Utiles.Gradiente({ "Nucleo", capa.Color or "Principal" }, ctx.Paleta),
		ctx
	)

	-- Chispas que suelta por el camino.
	local factor = Calidad.Factor("Particulas")
	local emisorParte, emisor
	if capa.Chispas and factor > 0 then
		emisorParte, emisor = Pool.Emisor()
		emisor.Texture = Recursos.Texturas.Chispa
		emisor.Color = Utiles.Gradiente({ "Nucleo", capa.Color or "Principal" }, ctx.Paleta)
		emisor.Size =
			NumberSequence.new({ NumberSequenceKeypoint.new(0, diametro * 0.5), NumberSequenceKeypoint.new(1, 0) })
		emisor.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) })
		emisor.Lifetime = NumberRange.new(0.25, 0.5)
		emisor.Speed = NumberRange.new(2, 8)
		emisor.SpreadAngle = Vector2.new(180, 180)
		emisor.LightEmission = 1
		emisor.Rate = capa.Chispas * factor
		emisor.Enabled = true
	end

	-- Luz que acompaña al proyectil.
	local luzParte, luz
	if (capa.Luz or 0) > 0 and Calidad.Factor("Luces") > 0 then
		luzParte, luz = Pool.Luz()
		luz.Color = Utiles.Color(capa.Color or "Principal", ctx.Paleta)
		luz.Brightness = capa.Luz
		luz.Range = diametro * 6
		luz.Enabled = true
	end

	local direccion = hasta - desde
	local lateral = direccion:Cross(Vector3.yAxis)
	lateral = if lateral.Magnitude > 0.01 then lateral.Unit else Vector3.xAxis
	local vertical = lateral:Cross(direccion.Magnitude > 0.01 and direccion.Unit or Vector3.zAxis)
	local altura: number = capa.Altura or 0
	local espiralRadio: number = if capa.Espiral then capa.Espiral[1] else 0
	local espiralVueltas: number = if capa.Espiral then capa.Espiral[2] else 0

	local transcurrido = 0
	Actores.Agregar(function(dt)
		transcurrido += dt
		local alfa = math.clamp(transcurrido / duracion, 0, 1)
		local recorrido = Utiles.Suavizar(alfa, capa.Easing or "Lineal")
		local posicion = desde:Lerp(hasta, recorrido)
		posicion += Vector3.yAxis * (altura * math.sin(math.pi * alfa))
		if espiralRadio > 0 then
			local angulo = alfa * espiralVueltas * math.pi * 2
			posicion += (lateral * math.cos(angulo) + vertical * math.sin(angulo)) * espiralRadio * math.sin(
				math.pi * alfa
			)
		end

		local marco =
			CFrame.lookAt(posicion, posicion + (if direccion.Magnitude > 0.01 then direccion.Unit else Vector3.zAxis))
		nucleo.CFrame = marco
		halo.CFrame = marco
		rastroParte.CFrame = marco
		if emisorParte then
			emisorParte.CFrame = marco
		end
		if luzParte then
			luzParte.CFrame = marco
		end

		if alfa >= 1 then
			-- Llega al destino: se apaga lo que se ve y se deja que la estela termine de desvanecerse.
			if emisor then
				emisor.Enabled = false
			end
			rastro.Enabled = false
			nucleo.Transparency = 1
			halo.Transparency = 1
			if luz then
				luz.Enabled = false
			end
			Pool.Liberar(nucleo)
			Pool.Liberar(halo)
			Pool.LiberarEn(rastroParte, (capa.Estela and capa.Estela.Vida or 0.3) + 0.1)
			if emisorParte then
				Pool.LiberarEn(emisorParte, 0.7)
			end
			if luzParte then
				Pool.Liberar(luzParte)
			end
			return true
		end
		return false
	end)
end

function Movimiento.Corte(capa: any, ctx: any)
	local centro = Utiles.Ancla(ctx, capa.Anclaje or "Lanzador", capa.Desplazamiento)
	local duracion: number = capa.Duracion or 0.18
	local radio: number = capa.Radio or 5
	local inicio: number = (capa.Arco and capa.Arco[1]) or -70
	local fin: number = (capa.Arco and capa.Arco[2]) or 70
	local inclinacion = math.rad(capa.Inclinacion or 0)
	local plano = centro * CFrame.Angles(0, 0, inclinacion)

	local punta, rastro, a0, a1 = Pool.Rastro()
	local estela = table.clone(capa.Estela or {})
	estela.Vida = estela.Vida or duracion * 1.4
	estela.Ancho = estela.Ancho or 1.2
	configurarRastro(rastro, a0, a1, estela, Utiles.Gradiente(capa.Color or { "Nucleo", "Principal" }, ctx.Paleta), ctx)

	local function puntoEn(grados: number): CFrame
		local angulo = math.rad(grados)
		local local3 = Vector3.new(math.sin(angulo) * radio, 0, -math.cos(angulo) * radio)
		local posicion = plano * local3
		-- El Trail se dibuja a lo largo de A0-A1: se orienta para que esa línea apunte al centro del arco.
		return CFrame.lookAt(posicion, plano.Position) * CFrame.Angles(0, 0, math.pi / 2)
	end

	punta.CFrame = puntoEn(inicio)
	local transcurrido = 0
	Actores.Agregar(function(dt)
		transcurrido += dt
		local alfa = math.clamp(transcurrido / duracion, 0, 1)
		punta.CFrame = puntoEn(inicio + (fin - inicio) * Utiles.Suavizar(alfa, capa.Easing or "Cubic"))
		if alfa >= 1 then
			rastro.Enabled = false
			Pool.LiberarEn(punta, estela.Vida + 0.1)
			return true
		end
		return false
	end)
end

return Movimiento
