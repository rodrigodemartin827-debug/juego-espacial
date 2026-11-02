--!strict
--[[
	Escena (Elección de bando): el decorado 3D de la pantalla de elección y la cámara fija que lo mira.

	  izquierda   el planeta de los HUMANOS (océanos, continentes, casquetes, nubes y atmósfera azul) con su sol
	  centro      la GRIETA: una rasgadura en el espacio, con bordes de energía, vacío negro dentro, ramas, motas,
	              jirones oscuros y chispazos que saltan de vez en cuando
	  derecha     el planeta de los MONSTRUOS (roca negra, venas de lava, niebla púrpura) y su "sol": un agujero
	              negro con disco de acreción
	  delante     una figura R6 de cada bando: un explorador con casco y una silueta larguísima de ojos rojos que da
	              tirones con la cabeza

	Todo se construye por código, sin assets, a partir de Eleccion/Config, y solo existe en este cliente (lejos del
	mapa, en Config.Camara.Origen). Los efectos de resaltar y de confirmar usan el motor de VFX del juego
	(client/VFX/Gestor) con las recetas de Eleccion/Datos/EfectosEleccion.

	Un único bucle por fotograma (RenderStep, prioridad de cámara) coloca la cámara, gira los planetas, mueve la
	grieta y anima las figuras. Los temblores de pantalla de VFX/Pantalla se suman después (prioridad cámara + 1).

	Uso:
		Escena.Construir()
		Escena.Resaltar("Humanos")      -- o nil
		Escena.Anticipar("Humanos")     -- clic: tensión mientras responde el servidor
		Escena.Cancelar()               -- el servidor no respondió: se deshace la anticipación
		Escena.Confirmar("Humanos")     -- el servidor aceptó: estallido, congelación y acercamiento
		Escena.Destruir()
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Eleccion.Config)
local Encuadre = require(Shared.Eleccion.Encuadre)
local FormaGrieta = require(Shared.Eleccion.Grieta)
local EfectosEleccion = require(Shared.Eleccion.Datos.EfectosEleccion)
local Recursos = require(Shared.Combate.Datos.Recursos)
local Calidad = require(script.Parent.Parent.VFX.Calidad)
local Gestor = require(script.Parent.Parent.VFX.Gestor)
local Utiles = require(script.Parent.Parent.VFX.Utiles)

local Escena = {}

local NOMBRE_PASO = "EleccionEscena"

local MATERIALES: { [string]: Enum.Material } = {
	Plastico = Enum.Material.SmoothPlastic,
	Neon = Enum.Material.Neon,
	Roca = Enum.Material.Slate,
	Hielo = Enum.Material.Glacier,
	Arena = Enum.Material.Sand,
	Cesped = Enum.Material.Grass,
	Basalto = Enum.Material.Basalt,
}

-- ===== Tipos internos =====

-- Una pieza que se mueve con algo (un planeta, una figura...): su posición relativa y su tamaño de base.
type Pieza = { Parte: BasePart, Relativo: CFrame, Tamano: Vector3 }

type Planeta = {
	Bando: string,
	Datos: Config.Planeta,
	Centro: Vector3, -- en el mundo
	Eje: Vector3,
	Suelo: { Pieza }, -- núcleo, continentes, polos...
	Nubes: { Pieza },
	Envoltura: { Pieza }, -- atmósfera y halo (no giran: son esferas)
	Atmosfera: BasePart,
	Halo: BasePart,
	Luz: PointLight?,
	BrilloLuz: number,
	Escala: number, -- escala actual (suavizada)
	EscalaAplicada: number, -- la última que se aplicó a los tamaños
	Golpe: number, -- escala extra del golpe de la confirmación (decae sola)
}

-- Una capa de cintas de luz: sus Beams, sus datos y los adjuntos por los que pasa (los bordes tienen los suyos).
type Capa = { Beams: { Beam }, Datos: any, Adjuntos: { Attachment } }

type Figura = {
	Bando: string,
	Datos: Config.Figura,
	Raiz: CFrame, -- marco de la figura en el mundo (centro del torso)
	Piezas: { [string]: Pieza },
	Extras: { Pieza }, -- ojos y visor: siguen a la cabeza
	Hombro: number, -- altura de los hombros y del cuello sobre el centro del torso (ya escalada)
	AltoBrazo: number,
	AltoCabeza: number,
	Ojos: { BasePart },
	Espasmo: number, -- ángulo extra de la cabeza ahora mismo (decae)
	ProximoEspasmo: number,
	Luz: PointLight?,
}

-- ===== Estado =====

local carpeta: Folder? = nil
local marcoEscena = CFrame.identity
local tiempo = 0 -- tiempo de la escena (se para durante la congelación)
local congeladaHasta = 0
local planetas: { [string]: Planeta } = {}
local figuras: { [string]: Figura } = {}
local foco: { [string]: number } = {} -- 0..1 por bando (suavizado)
local resaltado: string? = nil
local elegido: string? = nil
local anticipando: string? = nil
local ultimoRayoResaltar = 0
local acercamiento = 0 -- 0..1 hacia el planeta elegido
local giroCamara = 0 -- radianes (suavizado)

-- Grieta
local grietaForma: FormaGrieta.Forma? = nil
local grietaRamas: { FormaGrieta.Rama } = {}
local grietaCentro = Vector3.zero
local grietaAdjuntos: { Attachment } = {} -- principal: un vértice por adjunto, por capa
local grietaCapas: { Capa } = {}
local ramasAdjuntos: { { Attachment } } = {}
local ramasCapas: { { Capa } } = {}
local grietaLuz: PointLight? = nil
local grietaApertura = 1
local grietaSurge = 0 -- empuje extra de la apertura (resaltar / confirmar); decae solo
local proximoChispazo = 0
local ultimoGrosor = -1

-- Agujero negro y sol
local rafagas: { { Parte: BasePart, Angulo: number, Radio: number } } = {}
local marcoDisco = CFrame.identity
local solPiezas: { BasePart } = {}
local sonidoAmbiente: Sound? = nil

local azar = Random.new()

-- Piezas y marcos que se mueven en este fotograma (una sola llamada a BulkMoveTo).
local movidas: { BasePart } = {}
local destinos: { CFrame } = {}

-- ===== Utilidades =====

local function v3(lista: { number }): Vector3
	return Vector3.new(lista[1] or 0, lista[2] or 0, lista[3] or 0)
end

local function color(hex: string): Color3
	return Utiles.Hex(hex)
end

-- Posición en el mundo de un punto dado en el sistema de la cámara (el de Config).
local function mundo(lista: { number }): Vector3
	return marcoEscena:PointToWorldSpace(v3(lista))
end

-- Pieza decorativa: anclada, sin colisiones, sin sombra y que no estorba a los rayos del juego.
local function nuevaParte(nombre: string, forma: Enum.PartType?, padre: Instance): Part
	local parte = Instance.new("Part")
	parte.Name = nombre
	parte.Shape = forma or Enum.PartType.Block
	parte.Anchored = true
	parte.CanCollide = false
	parte.CanTouch = false
	parte.CanQuery = false
	parte.CastShadow = false
	parte.TopSurface = Enum.SurfaceType.Smooth
	parte.BottomSurface = Enum.SurfaceType.Smooth
	parte.Parent = padre
	return parte
end

local function nuevaLuz(padre: Instance, posicion: Vector3, datos: any): (BasePart, PointLight)
	local ancla = nuevaParte("Luz", nil, padre)
	ancla.Transparency = 1
	ancla.Size = Vector3.one
	ancla.CFrame = CFrame.new(posicion)
	local luz = Instance.new("PointLight")
	luz.Color = color(datos.Color)
	luz.Brightness = datos.Brillo
	luz.Range = math.min(datos.Rango, 60)
	luz.Shadows = false
	luz.Parent = ancla
	return ancla, luz
end

-- Suavizado exponencial: igual de suave a 30 que a 144 fotogramas por segundo.
local function acercar(actual: number, objetivo: number, rapidez: number, dt: number): number
	return actual + (objetivo - actual) * (1 - math.exp(-rapidez * dt))
end

local function otroBando(bando: string): string
	return if bando == Config.Orden[1] then Config.Orden[2] else Config.Orden[1]
end

-- ===== Planetas =====

-- Una esfera pegada a la superficie (continente, polo, nube...): sobresale `Elevacion` por encima del planeta.
local function mancha(padre: Instance, radio: number, datos: Config.Mancha, nombre: string): Pieza
	local r = datos.Tamano * radio
	local direccion = v3(datos.Direccion)
	direccion = if direccion.Magnitude > 1e-3 then direccion.Unit else Vector3.yAxis
	local distancia = radio * (1 + datos.Elevacion) - r
	local parte = nuevaParte(nombre, Enum.PartType.Ball, padre)
	parte.Color = color(datos.Color)
	parte.Material = MATERIALES[datos.Material or "Plastico"] or Enum.Material.SmoothPlastic
	parte.Transparency = datos.Transparencia or 0
	local tamano = Vector3.one * (r * 2)
	parte.Size = tamano
	return { Parte = parte, Relativo = CFrame.new(direccion * distancia), Tamano = tamano }
end

local function construirPlaneta(bando: string, datos: Config.Planeta, padre: Instance): Planeta
	local modelo = Instance.new("Model")
	modelo.Name = `Planeta_{bando}`
	modelo.Parent = padre

	local radio = datos.Radio
	local nucleo = nuevaParte("Nucleo", Enum.PartType.Ball, modelo)
	nucleo.Color = color(datos.Color)
	nucleo.Material = MATERIALES[datos.Material or "Plastico"] or Enum.Material.SmoothPlastic
	nucleo.Size = Vector3.one * radio * 2
	local suelo: { Pieza } = { { Parte = nucleo, Relativo = CFrame.identity, Tamano = nucleo.Size } }
	for indice, datosMancha in datos.Manchas do
		table.insert(suelo, mancha(modelo, radio, datosMancha, `Mancha{indice}`))
	end

	local nubes: { Pieza } = {}
	for indice, datosNube in datos.Nubes do
		table.insert(nubes, mancha(modelo, radio, datosNube, `Nube{indice}`))
	end

	-- Atmósfera: el material ForceField brilla en el borde (efecto fresnel), justo como una atmósfera vista desde
	-- el espacio. El halo es un resplandor muy tenue alrededor.
	local atmosfera = nuevaParte("Atmosfera", Enum.PartType.Ball, modelo)
	atmosfera.Material = Enum.Material.ForceField
	atmosfera.Color = color(datos.Atmosfera.Color)
	atmosfera.Transparency = datos.Atmosfera.Transparencia
	atmosfera.Size = Vector3.one * radio * 2 * datos.Atmosfera.Escala
	local halo = nuevaParte("Halo", Enum.PartType.Ball, modelo)
	halo.Material = Enum.Material.Neon
	halo.Color = color(datos.Halo.Color)
	halo.Transparency = datos.Halo.Transparencia
	halo.Size = Vector3.one * radio * 2 * datos.Halo.Escala

	local eje = v3(datos.Eje)
	return {
		Bando = bando,
		Datos = datos,
		Centro = mundo(datos.Posicion),
		Eje = if eje.Magnitude > 1e-3 then eje.Unit else Vector3.yAxis,
		Suelo = suelo,
		Nubes = nubes,
		Envoltura = {
			{ Parte = atmosfera, Relativo = CFrame.identity, Tamano = atmosfera.Size },
			{ Parte = halo, Relativo = CFrame.identity, Tamano = halo.Size },
		},
		Atmosfera = atmosfera,
		Halo = halo,
		Luz = nil,
		BrilloLuz = 0,
		Escala = 1,
		EscalaAplicada = 1,
		Golpe = 0,
	}
end

-- Coloca las piezas de un planeta (giro y escala) usando BulkMoveTo: una sola llamada para todas.
local function colocarPlaneta(planeta: Planeta, partes: { BasePart }, marcos: { CFrame })
	local escala = planeta.Escala + planeta.Golpe
	local cambiarTamano = math.abs(escala - planeta.EscalaAplicada) > 0.002
	local giroSuelo = CFrame.fromAxisAngle(planeta.Eje, tiempo * math.pi * 2 / planeta.Datos.VueltaSegundos)
	local giroNubes = CFrame.fromAxisAngle(planeta.Eje, tiempo * math.pi * 2 / planeta.Datos.NubesVuelta)
	local centro = CFrame.new(planeta.Centro)

	local function poner(lista: { Pieza }, giro: CFrame)
		for _, pieza in lista do
			local relativo = pieza.Relativo
			local escalado = CFrame.new(relativo.Position * escala) * relativo.Rotation
			table.insert(partes, pieza.Parte)
			table.insert(marcos, centro * giro * escalado)
			if cambiarTamano then
				pieza.Parte.Size = pieza.Tamano * escala
			end
		end
	end
	poner(planeta.Suelo, giroSuelo)
	poner(planeta.Nubes, giroNubes)
	poner(planeta.Envoltura, CFrame.identity)
	if cambiarTamano then
		planeta.EscalaAplicada = escala
	end
end

-- ===== Sol y agujero negro =====

local function construirSol(padre: Instance)
	local datos = Config.Sol
	local centro = mundo(datos.Posicion)
	local modelo = Instance.new("Model")
	modelo.Name = "Sol"
	modelo.Parent = padre

	local nucleo = nuevaParte("Nucleo", Enum.PartType.Ball, modelo)
	nucleo.Material = Enum.Material.Neon
	nucleo.Color = color(datos.Color)
	nucleo.Size = Vector3.one * datos.Radio * 2
	nucleo.CFrame = CFrame.new(centro)
	for _, capa in { datos.Corona, datos.Resplandor } do
		local esfera = nuevaParte("Corona", Enum.PartType.Ball, modelo)
		esfera.Material = Enum.Material.Neon
		esfera.Color = color(capa.Color)
		esfera.Transparency = capa.Transparencia
		esfera.Size = Vector3.one * datos.Radio * 2 * capa.Escala
		esfera.CFrame = CFrame.new(centro)
		table.insert(solPiezas, esfera)
	end
end

local function construirAgujeroNegro(padre: Instance)
	local datos = Config.AgujeroNegro
	local centro = mundo(datos.Posicion)
	local modelo = Instance.new("Model")
	modelo.Name = "AgujeroNegro"
	modelo.Parent = padre

	local inclinacion = datos.Inclinacion
	-- El cilindro de Roblox tiene el eje en X: se pone en vertical (disco horizontal) y luego se inclina.
	marcoDisco = CFrame.new(centro)
		* CFrame.Angles(math.rad(inclinacion[1]), math.rad(inclinacion[2]), math.rad(inclinacion[3]))
		* CFrame.Angles(0, 0, math.pi / 2)

	for _, disco in { datos.DiscoExterior, datos.Disco } do
		local parte = nuevaParte("Disco", Enum.PartType.Cylinder, modelo)
		parte.Material = Enum.Material.Neon
		parte.Color = color(disco.Color)
		parte.Transparency = disco.Transparencia
		parte.Size = Vector3.new(0.15, disco.Radio * 2, disco.Radio * 2)
		parte.CFrame = marcoDisco
	end

	-- El horizonte de sucesos: negro absoluto, por delante del disco que pasa por detrás.
	local horizonte = nuevaParte("Horizonte", Enum.PartType.Ball, modelo)
	horizonte.Material = Enum.Material.SmoothPlastic
	horizonte.Color = Color3.new(0, 0, 0)
	horizonte.Reflectance = 0
	horizonte.Size = Vector3.one * datos.Radio * 2
	horizonte.CFrame = CFrame.new(centro)

	local anillo = nuevaParte("AnilloFotones", Enum.PartType.Ball, modelo)
	anillo.Material = Enum.Material.ForceField
	anillo.Color = color(datos.Anillo.Color)
	anillo.Transparency = datos.Anillo.Transparencia
	anillo.Size = Vector3.one * datos.Radio * 2 * datos.Anillo.Escala
	anillo.CFrame = CFrame.new(centro)

	-- Trozos de materia que giran en el disco: sin ellos, un disco liso parecería quieto.
	local cantidad = math.max(4, math.floor(datos.Rafagas.Cantidad * (if Calidad.Nivel() == "Bajo" then 0.5 else 1)))
	for indice = 1, cantidad do
		local parte = nuevaParte("Rafaga", nil, modelo)
		parte.Material = Enum.Material.Neon
		parte.Color = color(datos.Rafagas.Color)
		parte.Size = Vector3.new(0.25, 0.5, azar:NextNumber(2.5, 5))
		table.insert(rafagas, {
			Parte = parte :: BasePart,
			Angulo = (indice / cantidad) * math.pi * 2 + azar:NextNumber(-0.2, 0.2),
			Radio = azar:NextNumber(datos.Radio * 1.25, datos.Disco.Radio * 0.95),
		})
	end
end

local function moverRafagas(partes: { BasePart }, marcos: { CFrame })
	local vuelta = Config.AgujeroNegro.Rafagas.Vuelta
	for _, rafaga in rafagas do
		-- Más deprisa cuanto más cerca del agujero (como un remolino).
		local velocidad = (math.pi * 2 / vuelta) * (Config.AgujeroNegro.Disco.Radio / rafaga.Radio)
		local angulo = rafaga.Angulo + tiempo * velocidad
		-- En el sistema del disco, el plano es YZ (el eje del cilindro es X).
		local local_ = Vector3.new(0, math.cos(angulo) * rafaga.Radio, math.sin(angulo) * rafaga.Radio)
		local tangente = Vector3.new(0, -math.sin(angulo), math.cos(angulo))
		local posicion = marcoDisco:PointToWorldSpace(local_)
		local direccion = marcoDisco:VectorToWorldSpace(tangente)
		table.insert(partes, rafaga.Parte)
		table.insert(marcos, CFrame.lookAt(posicion, posicion + direccion))
	end
end

-- ===== La grieta =====

-- Una cinta de luz entre dos adjuntos. `orden` decide qué capa se dibuja delante (ZOffset: más alto, más delante).
local function nuevaCinta(padre: Instance, a0: Attachment, a1: Attachment, datos: any, orden: number): Beam
	local cinta = Instance.new("Beam")
	cinta.ZOffset = orden * 0.1
	cinta.Attachment0 = a0
	cinta.Attachment1 = a1
	cinta.FaceCamera = true
	cinta.Segments = 1
	cinta.Color = ColorSequence.new(color(datos.Color))
	cinta.Transparency = NumberSequence.new(datos.Transparencia or 0)
	local emite = datos.Emite ~= false
	cinta.LightEmission = if emite then 1 else 0
	cinta.LightInfluence = 0
	cinta.Brightness = if emite then (datos.Brillo or 1) else 1
	cinta.Width0 = datos.Grosor
	cinta.Width1 = datos.Grosor
	cinta.Parent = padre
	return cinta
end

local function construirGrieta(padre: Instance)
	local datos = Config.Grieta
	local bajo = Calidad.Nivel() == "Bajo"
	local puntos = if bajo then math.max(8, math.floor(datos.Puntos / 2)) else datos.Puntos
	grietaForma =
		FormaGrieta.nueva(datos.Semilla, puntos, datos.Alto, datos.Desvio, datos.Temblor, datos.VelocidadTemblor)
	grietaCentro = mundo(datos.Posicion)

	local modelo = Instance.new("Model")
	modelo.Name = "Grieta"
	modelo.Parent = padre

	-- Una pieza invisible sostiene los adjuntos; las cintas (Beams) van de un adjunto al siguiente y siempre miran a
	-- la cámara, así la grieta se ve igual de gruesa desde cualquier ángulo.
	local ancla = nuevaParte("Ancla", nil, modelo)
	ancla.Transparency = 1
	ancla.Size = Vector3.one
	ancla.CFrame = CFrame.new(grietaCentro)

	-- Cada capa necesita sus propios adjuntos cuando es un borde (va desplazada); las demás comparten los del centro.
	local centrales: { Attachment } = {}
	for indice = 1, puntos do
		local adjunto = Instance.new("Attachment")
		adjunto.Name = `V{indice}`
		adjunto.Parent = ancla
		centrales[indice] = adjunto
	end
	grietaAdjuntos = centrales

	for orden, datosCapa in datos.Capas do
		if not Calidad.Permite(datosCapa.Minimo) then
			continue
		end
		local adjuntos = centrales
		if datosCapa.Lado ~= nil then
			adjuntos = {}
			for indice = 1, puntos do
				local adjunto = Instance.new("Attachment")
				adjunto.Name = `B{datosCapa.Lado}_{indice}`
				adjunto.Parent = ancla
				adjuntos[indice] = adjunto
			end
		end
		local cintas: { Beam } = {}
		for indice = 1, puntos - 1 do
			table.insert(cintas, nuevaCinta(ancla, adjuntos[indice], adjuntos[indice + 1], datosCapa, orden))
		end
		table.insert(grietaCapas, { Beams = cintas, Datos = datosCapa, Adjuntos = adjuntos })
	end

	-- Ramas (no en calidad baja).
	if not bajo then
		grietaRamas =
			FormaGrieta.Ramas(datos.Semilla, datos.Ramas.Cantidad, puntos, datos.Ramas.Largo, datos.Ramas.Puntos)
		for indiceRama, rama in grietaRamas do
			local adjuntos: { Attachment } = {}
			for indice = 1, rama.Puntos + 1 do
				local adjunto = Instance.new("Attachment")
				adjunto.Name = `R{indiceRama}_{indice}`
				adjunto.Parent = ancla
				adjuntos[indice] = adjunto
			end
			local capas: { Capa } = {}
			for orden, datosCapa in { datos.Ramas.Halo, datos.Ramas.Nucleo } do
				local cintas: { Beam } = {}
				for indice = 1, rama.Puntos do
					-- Detrás del vacío de la grieta principal (las ramas nacen de su borde).
					local capaOrden = orden - 2
					table.insert(
						cintas,
						nuevaCinta(ancla, adjuntos[indice], adjuntos[indice + 1], datosCapa, capaOrden)
					)
				end
				table.insert(capas, { Beams = cintas, Datos = datosCapa, Adjuntos = adjuntos })
			end
			ramasAdjuntos[indiceRama] = adjuntos
			ramasCapas[indiceRama] = capas
		end
	end

	-- Luz violeta del centro.
	local luz = Instance.new("PointLight")
	luz.Color = color(datos.Luz.Color)
	luz.Brightness = datos.Luz.Brillo
	luz.Range = math.min(datos.Luz.Rango, 60)
	luz.Shadows = false
	luz.Parent = ancla
	grietaLuz = luz

	-- Motas de energía y jirones de vacío que se escapan por la grieta.
	local factor = Calidad.Factor("Particulas")
	local emisora = nuevaParte("Emisora", nil, modelo)
	emisora.Transparency = 1
	emisora.Size = Vector3.new(3, datos.Alto * 0.8, 1)
	emisora.CFrame = CFrame.new(grietaCentro)

	local motas = Instance.new("ParticleEmitter")
	motas.Texture = Recursos.Texturas.Chispa
	motas.Color = Utiles.Gradiente(datos.Motas.Color, {})
	motas.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(0.2, 0.55),
		NumberSequenceKeypoint.new(1, 0),
	})
	motas.Transparency = NumberSequence.new(0.1)
	motas.Lifetime = NumberRange.new(1.5, 3.2)
	motas.Speed = NumberRange.new(1.5, 5)
	motas.SpreadAngle = Vector2.new(180, 180)
	motas.LightEmission = 1
	motas.LightInfluence = 0
	motas.Drag = 0.5
	motas.Acceleration = Vector3.zero
	motas.Rate = datos.Motas.Tasa * factor
	motas.Shape = Enum.ParticleEmitterShape.Box
	motas.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	motas.Parent = emisora

	local vacio = Instance.new("ParticleEmitter")
	vacio.Texture = Recursos.Texturas.Humo
	vacio.Color = ColorSequence.new(color(datos.Vacio.Color))
	vacio.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1.5),
		NumberSequenceKeypoint.new(1, 6),
	})
	vacio.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.3, 0.55),
		NumberSequenceKeypoint.new(1, 1),
	})
	vacio.Lifetime = NumberRange.new(2.5, 4)
	vacio.Speed = NumberRange.new(0.5, 2)
	vacio.SpreadAngle = Vector2.new(180, 180)
	vacio.Rotation = NumberRange.new(0, 360)
	vacio.RotSpeed = NumberRange.new(-25, 25)
	vacio.LightEmission = 0
	vacio.LightInfluence = 0
	vacio.Rate = datos.Vacio.Tasa * factor
	vacio.Shape = Enum.ParticleEmitterShape.Box
	vacio.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	vacio.Parent = emisora

	-- Zumbido de la grieta (si hay sonido asignado en Recursos).
	local idSonido = Recursos.Sonidos.EleccionAmbiente
	if idSonido ~= nil and idSonido ~= "" then
		local sonido = Instance.new("Sound")
		sonido.SoundId = idSonido
		sonido.Looped = true
		sonido.Volume = 0.5
		sonido.RollOffMaxDistance = 400
		sonido.Parent = ancla
		sonido:Play()
		sonidoAmbiente = sonido
	end
end

-- Mueve los vértices de la grieta y late su grosor.
local function moverGrieta(dt: number)
	local forma = grietaForma
	if forma == nil then
		return
	end
	local datos = Config.Grieta
	local focoTotal = math.max(foco[Config.Orden[1]] or 0, foco[Config.Orden[2]] or 0)
	grietaSurge = acercar(grietaSurge, 0, 2.5, dt)
	grietaApertura = 1 + 0.35 * focoTotal + grietaSurge
	local puntos = FormaGrieta.Puntos(forma, tiempo, grietaApertura)

	-- Latido: un pico rápido cada PeriodoLatido segundos.
	local fase = (tiempo % datos.PeriodoLatido) / datos.PeriodoLatido
	local latido = math.exp(-fase * 7) + 0.25 * math.exp(-math.max(fase - 0.18, 0) * 9) * (if fase > 0.18 then 1 else 0)

	for indice, punto in puntos do
		grietaAdjuntos[indice].Position = Vector3.new(punto.X, punto.Y, punto.Z)
	end

	-- Las capas (y sus bordes desplazados a cada lado del vacío).
	local grosorVacio = 0
	for _, capa in grietaCapas do
		if capa.Datos.Emite == false then
			grosorVacio = capa.Datos.Grosor * grietaApertura
		end
	end
	-- El grosor se recalcula a 20 por segundo como mucho: no hace falta más y ahorra trabajo en móvil.
	local cuantizado = math.floor(tiempo * 20)
	local actualizarGrosor = cuantizado ~= ultimoGrosor
	ultimoGrosor = cuantizado
	for _, capa in grietaCapas do
		local datosCapa = capa.Datos
		local adjuntos = capa.Adjuntos
		if datosCapa.Lado ~= nil then
			for indice, punto in puntos do
				local desplazamiento = datosCapa.Lado * grosorVacio * 0.5 * punto.Grosor
				adjuntos[indice].Position = Vector3.new(punto.X + desplazamiento, punto.Y, punto.Z + 0.05)
			end
		end
		if actualizarGrosor then
			local base = datosCapa.Grosor * (1 + (datosCapa.Pulso or 0) * latido) * (0.8 + 0.2 * grietaApertura)
			for indice, cinta in capa.Beams do
				cinta.Width0 = base * puntos[indice].Grosor
				cinta.Width1 = base * puntos[indice + 1].Grosor
			end
		end
	end

	-- Ramas.
	for indiceRama, rama in grietaRamas do
		local origen = puntos[math.clamp(rama.Desde, 1, #puntos)]
		local puntosRama = FormaGrieta.PuntosRama(rama, origen, tiempo, indiceRama)
		local adjuntos = ramasAdjuntos[indiceRama]
		for indice, punto in puntosRama do
			adjuntos[indice].Position = Vector3.new(punto.X, punto.Y, punto.Z)
		end
		if actualizarGrosor then
			for _, capa in ramasCapas[indiceRama] do
				local base = capa.Datos.Grosor * (1 + 0.3 * latido) * grietaApertura
				for indice, cinta in capa.Beams do
					cinta.Width0 = base * puntosRama[indice].Grosor
					cinta.Width1 = base * puntosRama[indice + 1].Grosor
				end
			end
		end
	end

	if grietaLuz then
		grietaLuz.Brightness = datos.Luz.Brillo * (0.75 + 0.6 * latido + 0.5 * focoTotal + grietaSurge)
	end
end

-- Un chispazo de energía entre un vértice de la grieta y un punto cercano (receta Eleccion_Grieta_Chispazo).
local function chispazo(haciaCamara: Vector3)
	local forma = grietaForma
	if forma == nil then
		return
	end
	local puntos = FormaGrieta.Puntos(forma, tiempo, grietaApertura)
	local punto = puntos[azar:NextInteger(2, math.max(2, #puntos - 1))]
	local desde = grietaCentro + Vector3.new(punto.X, punto.Y, punto.Z)
	local lado = if azar:NextNumber() < 0.5 then -1 else 1
	local hasta = desde + Vector3.new(lado * azar:NextNumber(3, 8), azar:NextNumber(-4, 4), azar:NextNumber(-1, 1))
	Gestor.Reproducir("Eleccion_Grieta_Chispazo", "Impacto", {
		Origen = desde,
		Punto = hasta,
		Direccion = haciaCamara,
		EsLocal = true,
		DistanciaMaxima = 1000,
	})
end

-- ===== Figuras R6 =====

-- Las seis piezas de un personaje R6 y su tamaño a escala 1.
local PIEZAS_R6: { [string]: Vector3 } = {
	Torso = Vector3.new(2, 2, 1),
	Head = Vector3.new(2, 1, 1),
	["Left Arm"] = Vector3.new(1, 2, 1),
	["Right Arm"] = Vector3.new(1, 2, 1),
	["Left Leg"] = Vector3.new(1, 2, 1),
	["Right Leg"] = Vector3.new(1, 2, 1),
}

local function construirFigura(bando: string, datos: Config.Figura, padre: Instance): Figura
	local modelo = Instance.new("Model")
	modelo.Name = `Figura_{bando}`
	modelo.Parent = padre

	local escala = datos.Escala
	local estirar = datos.Estiramiento or {}
	local tamanos: { [string]: Vector3 } = {}
	for nombre, base in PIEZAS_R6 do
		local factor = estirar[nombre]
		tamanos[nombre] = base * (if factor then v3(factor) else Vector3.one) * escala
	end

	local material = MATERIALES[datos.Material] or Enum.Material.SmoothPlastic
	local piezas: { [string]: Pieza } = {}
	for nombre, tamano in tamanos do
		local parte = nuevaParte(nombre, nil, modelo)
		parte.Size = tamano
		parte.Color = color(datos.Colores[nombre] or "#FFFFFF")
		parte.Material = material
		if nombre == "Head" then
			-- La cabeza clásica de Roblox (cilindro redondeado).
			local malla = Instance.new("SpecialMesh")
			malla.MeshType = Enum.MeshType.Head
			malla.Scale = Vector3.new(1.25, 1.25, 1.25)
			malla.Parent = parte
		end
		piezas[nombre] = { Parte = parte, Relativo = CFrame.identity, Tamano = tamano }
	end

	local torso = tamanos.Torso
	local hombro = torso.Y / 2
	local brazo = tamanos["Right Arm"]
	local pierna = tamanos["Right Leg"]
	local cabeza = tamanos.Head
	-- Posiciones de reposo (los brazos y la cabeza se recolocan cada fotograma desde el hombro y el cuello).
	piezas["Left Leg"].Relativo = CFrame.new(-torso.X / 4, -hombro - pierna.Y / 2, 0)
	piezas["Right Leg"].Relativo = CFrame.new(torso.X / 4, -hombro - pierna.Y / 2, 0)

	-- Visor (humanos) u ojos (monstruos): siguen a la cabeza.
	local extras: { Pieza } = {}
	local ojos: { BasePart } = {}
	if datos.Visor then
		local visor = nuevaParte("Visor", nil, modelo)
		visor.Material = Enum.Material.Neon
		visor.Color = color(datos.Visor.Color)
		visor.Size = Vector3.new(cabeza.X * 0.6, cabeza.Y * 0.42, 0.08 * escala)
		table.insert(extras, {
			Parte = visor :: BasePart,
			Relativo = CFrame.new(0, cabeza.Y * 0.06, -cabeza.Z * 0.66),
			Tamano = visor.Size,
		})
	end
	if datos.Ojos then
		for _, lado in { -1, 1 } do
			local ojo = nuevaParte("Ojo", Enum.PartType.Ball, modelo)
			ojo.Material = Enum.Material.Neon
			ojo.Color = color(datos.Ojos.Color)
			ojo.Size = Vector3.one * datos.Ojos.Tamano * escala * 2
			table.insert(extras, {
				Parte = ojo :: BasePart,
				Relativo = CFrame.new(lado * cabeza.X * 0.17, cabeza.Y * 0.1, -cabeza.Z * 0.64),
				Tamano = ojo.Size,
			})
			table.insert(ojos, ojo)
		end
	end

	-- Mira hacia la cámara (+Z), girada GiroY grados.
	local raiz = CFrame.new(mundo(datos.Posicion)) * CFrame.Angles(0, math.pi + math.rad(datos.GiroY), 0)
	local luz: PointLight? = nil
	if datos.Luz then
		local _, nueva = nuevaLuz(modelo, raiz:PointToWorldSpace(v3(datos.Luz.Desplazamiento)), datos.Luz)
		luz = nueva
	end

	return {
		Bando = bando,
		Datos = datos,
		Raiz = raiz,
		Piezas = piezas,
		Extras = extras,
		Hombro = hombro,
		AltoBrazo = brazo.Y,
		AltoCabeza = cabeza.Y,
		Ojos = ojos,
		Espasmo = 0,
		ProximoEspasmo = 1,
		Luz = luz,
	}
end

-- Anima una figura: respiración, brazos, y (monstruos) tirones de cabeza. `f` = foco de su bando (0..1).
local function moverFigura(figura: Figura, dt: number, partes: { BasePart }, marcos: { CFrame })
	local datos = figura.Datos
	local f = foco[figura.Bando] or 0
	local respiracion = math.sin(tiempo * 1.6) * 0.04 * datos.Escala
	local inclinacionCuerpo = math.rad(6) * f -- se inclina hacia la cámara al resaltarlo
	local raiz = figura.Raiz * CFrame.new(0, respiracion, 0) * CFrame.Angles(-inclinacionCuerpo, 0, 0)

	-- Espasmos (solo si los tiene): un tirón seco que se relaja despacio.
	if datos.Espasmos then
		if tiempo >= figura.ProximoEspasmo then
			local intervalo = datos.Espasmos.Intervalo
			figura.ProximoEspasmo = tiempo + azar:NextNumber(intervalo[1], intervalo[2] or intervalo[1])
			figura.Espasmo = math.rad(datos.Espasmos.Fuerza) * (if azar:NextNumber() < 0.5 then -1 else 1)
		end
		figura.Espasmo = acercar(figura.Espasmo, 0, 6, dt)
	end
	local ladeo = math.rad(datos.Inclinacion or 0) * (1 - 0.6 * f) + figura.Espasmo
	local cuello = CFrame.new(0, figura.Hombro, 0)
		* CFrame.Angles(math.rad(8) * f, math.sin(tiempo * 0.7) * 0.06, ladeo)
		* CFrame.new(0, figura.AltoCabeza / 2, 0)

	-- Brazos: cuelgan con un vaivén lento; al resaltar, el humano saluda y el monstruo los abre como garras.
	local torso = figura.Piezas.Torso.Tamano
	local anchoBrazo = figura.Piezas["Right Arm"].Tamano.X
	local alzar = if datos.Ojos then math.rad(35) * f else math.rad(150) * f
	local function brazo(lado: number): CFrame
		local balanceo = math.sin(tiempo * 1.1 + lado) * 0.05
		-- Girar en Z hacia fuera: positivo para el brazo derecho (+X), negativo para el izquierdo.
		local giro = if lado > 0 then alzar else (if datos.Ojos then -alzar else 0)
		return CFrame.new(lado * (torso.X / 2 + anchoBrazo / 2), figura.Hombro - anchoBrazo / 2, 0)
			* CFrame.Angles(balanceo, 0, giro)
			* CFrame.new(0, -figura.AltoBrazo / 2 + anchoBrazo / 2, 0)
	end

	local marcoCabeza = raiz * cuello
	local ponerPieza = function(nombre: string, marco: CFrame)
		table.insert(partes, figura.Piezas[nombre].Parte)
		table.insert(marcos, marco)
	end
	ponerPieza("Torso", raiz)
	ponerPieza("Head", marcoCabeza)
	ponerPieza("Right Arm", raiz * brazo(1))
	ponerPieza("Left Arm", raiz * brazo(-1))
	ponerPieza("Right Leg", raiz * figura.Piezas["Right Leg"].Relativo)
	ponerPieza("Left Leg", raiz * figura.Piezas["Left Leg"].Relativo)
	for _, extra in figura.Extras do
		table.insert(partes, extra.Parte)
		table.insert(marcos, marcoCabeza * extra.Relativo)
	end

	-- Los ojos se encienden al resaltar; el contraluz, también.
	for _, ojo in figura.Ojos do
		ojo.Transparency = 0.25 * (1 - f) + (if math.abs(figura.Espasmo) > 0.15 then 0.4 else 0)
	end
	if figura.Luz and datos.Luz then
		figura.Luz.Brightness = datos.Luz.Brillo * (0.7 + 0.6 * f)
	end
end

-- ===== Cámara =====

local function colocarCamara(dt: number)
	local camara = workspace.CurrentCamera
	if camara == nil then
		return
	end
	if camara.CameraType ~= Enum.CameraType.Scriptable then
		camara.CameraType = Enum.CameraType.Scriptable
	end
	local cam = Config.Camara
	local tamano = camara.ViewportSize
	camara.FieldOfView = Encuadre.CampoVertical(
		if tamano.Y > 0 then tamano.X / tamano.Y else 16 / 9,
		cam.MitadAnchoVisible,
		cam.DistanciaReferencia,
		cam.CampoMinimo,
		cam.CampoMaximo
	)

	-- Gira un poco hacia el lado resaltado (izquierda = giro positivo en Y).
	local izquierda, derecha = foco[Config.Orden[1]] or 0, foco[Config.Orden[2]] or 0
	giroCamara = acercar(giroCamara, math.rad(cam.GiroResaltado) * (izquierda - derecha), cam.Suavidad, dt)

	local periodo = math.max(cam.Vaiven.Periodo, 0.1)
	local onda = tiempo * math.pi * 2 / periodo
	local vaiven = Vector3.new(math.sin(onda), math.sin(onda * 0.5) * 0.6, 0) * cam.Vaiven.Amplitud

	local posicion = marcoEscena.Position + vaiven
	local elegidoAhora = elegido
	if elegidoAhora and planetas[elegidoAhora] then
		posicion = posicion:Lerp(planetas[elegidoAhora].Centro, Config.Escena.AcercamientoCamara * acercamiento)
	end
	camara.CFrame = CFrame.new(posicion) * CFrame.Angles(0, giroCamara, 0)
	camara.Focus = CFrame.new(grietaCentro)
end

-- ===== Bucle por fotograma =====

local function paso(dt: number)
	dt = math.min(dt, 0.1)
	local ahora = os.clock()
	local congelada = ahora < congeladaHasta
	if not congelada then
		tiempo += dt
	end

	-- Foco suavizado de cada bando.
	local rapidez = 1 / math.max(Config.Tiempos.Resaltado, 0.05) * 3
	for _, bando in Config.Orden do
		local objetivo = if bando == resaltado then 1 else 0
		foco[bando] = acercar(foco[bando] or 0, objetivo, rapidez, dt)
	end
	if elegido and not congelada then
		acercamiento = acercar(acercamiento, 1, 0.9, dt)
	end

	colocarCamara(dt)

	-- Se reutilizan las listas de cada fotograma (sin basura para el recolector).
	table.clear(movidas)
	table.clear(destinos)
	local esc = Config.Escena
	for bando, planeta in planetas do
		-- Escala: elegido / descartado tras confirmar; resaltado / apagado mientras se elige.
		local objetivo = 1
		if elegido then
			objetivo = if bando == elegido then esc.EscalaElegido else esc.EscalaDescartado
		elseif anticipando == bando then
			objetivo = 0.95
		elseif resaltado ~= nil then
			objetivo = if bando == resaltado then esc.EscalaResaltado else esc.EscalaApagado
		end
		planeta.Escala = acercar(planeta.Escala, objetivo, 8, dt)
		if not congelada then
			planeta.Golpe = acercar(planeta.Golpe, 0, 5, dt)
		end
		colocarPlaneta(planeta, movidas, destinos)

		-- Luz y atmósfera: más intensas en el lado resaltado, más tenues en el otro.
		local f = foco[bando] or 0
		local otro = foco[otroBando(bando)] or 0
		local apagado = if elegido then (if bando == elegido then 0 else 1) else otro
		if planeta.Luz then
			local brillo = planeta.BrilloLuz * (1 + 0.5 * f) * (1 - (1 - esc.LuzApagada) * apagado)
			planeta.Luz.Brightness = brillo
		end
		local datos = planeta.Datos
		planeta.Atmosfera.Transparency = math.clamp(datos.Atmosfera.Transparencia - 0.08 * f + 0.4 * apagado, 0, 1)
		planeta.Halo.Transparency = math.clamp(datos.Halo.Transparencia - 0.05 * f + 0.06 * apagado, 0, 1)
	end
	if not congelada then
		moverRafagas(movidas, destinos)
	end
	for _, figura in figuras do
		moverFigura(figura, if congelada then 0 else dt, movidas, destinos)
	end
	if #movidas > 0 then
		workspace:BulkMoveTo(movidas, destinos, Enum.BulkMoveMode.FireCFrameChanged)
	end

	-- El sol late muy despacio.
	for indice, corona in solPiezas do
		corona.Transparency = (
			if indice == 1 then Config.Sol.Corona.Transparencia else Config.Sol.Resplandor.Transparencia
		) + math.sin(tiempo * 1.3 + indice) * 0.03
	end

	if not congelada then
		moverGrieta(dt)
	end

	-- Chispazos de la grieta de vez en cuando (más a menudo al resaltar).
	if tiempo >= proximoChispazo and grietaForma ~= nil then
		local intervalo = Config.Grieta.IntervaloChispazo
		local prisa = if resaltado then 0.6 else 1
		proximoChispazo = tiempo + azar:NextNumber(intervalo[1], intervalo[2] or intervalo[1]) * prisa
		local camara = workspace.CurrentCamera
		local haciaCamara = if camara then (camara.CFrame.Position - grietaCentro) else Vector3.zAxis
		chispazo(if haciaCamara.Magnitude > 1e-3 then haciaCamara.Unit else Vector3.zAxis)
	end
end

-- ===== API =====

-- ¿Está montada la escena?
function Escena.Activa(): boolean
	return carpeta ~= nil
end

-- Monta la escena y empieza a mover la cámara. Si ya estaba montada, no hace nada.
function Escena.Construir()
	if carpeta ~= nil then
		return
	end
	Gestor.RegistrarRecetas(EfectosEleccion)
	marcoEscena = CFrame.new(v3(Config.Camara.Origen))
	tiempo, congeladaHasta, acercamiento, giroCamara = 0, 0, 0, 0
	resaltado, elegido, anticipando = nil, nil, nil
	grietaApertura, grietaSurge, ultimoGrosor = 1, 0, -1
	proximoChispazo = 0.8
	table.clear(foco)

	local raiz = Instance.new("Folder")
	raiz.Name = "EscenaEleccion"
	carpeta = raiz

	planetas.Humanos = construirPlaneta("Humanos", Config.PlanetaHumanos, raiz)
	planetas.Monstruos = construirPlaneta("Monstruos", Config.PlanetaMonstruos, raiz)
	construirSol(raiz)
	construirAgujeroNegro(raiz)
	construirGrieta(raiz)

	-- Las luces de cada lado (una PointLight no pasa de 60 studs: por eso van cerca de su planeta). Se ponen siempre,
	-- también en calidad baja: son pocas y sin ellas los planetas se verían planos.
	local _, luzSol = nuevaLuz(raiz, mundo(Config.Sol.Luz.Posicion), Config.Sol.Luz)
	planetas.Humanos.Luz = luzSol
	planetas.Humanos.BrilloLuz = Config.Sol.Luz.Brillo
	local _, luzAgujero = nuevaLuz(raiz, mundo(Config.AgujeroNegro.Luz.Posicion), Config.AgujeroNegro.Luz)
	planetas.Monstruos.Luz = luzAgujero
	planetas.Monstruos.BrilloLuz = Config.AgujeroNegro.Luz.Brillo

	figuras.Humanos = construirFigura("Humanos", Config.FiguraHumanos, raiz)
	figuras.Monstruos = construirFigura("Monstruos", Config.FiguraMonstruos, raiz)

	-- Polvo estelar flotando delante del fondo: da profundidad a la imagen.
	local polvo = nuevaParte("Polvo", nil, raiz)
	polvo.Transparency = 1
	polvo.Size = Vector3.new(160, 90, 60)
	polvo.CFrame = CFrame.new(mundo({ 0, 0, -90 }))
	local emisor = Instance.new("ParticleEmitter")
	emisor.Texture = Recursos.Texturas.Chispa
	emisor.Color = ColorSequence.new(color(Config.Escena.Polvo.Color))
	emisor.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(0.5, 0.35),
		NumberSequenceKeypoint.new(1, 0),
	})
	emisor.Transparency = NumberSequence.new(0.3)
	emisor.Lifetime = NumberRange.new(5, 9)
	emisor.Speed = NumberRange.new(0.2, 0.8)
	emisor.SpreadAngle = Vector2.new(180, 180)
	emisor.LightEmission = 1
	emisor.LightInfluence = 0
	emisor.Rate = Config.Escena.Polvo.Tasa * Calidad.Factor("Particulas")
	emisor.Shape = Enum.ParticleEmitterShape.Box
	emisor.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	emisor.Parent = polvo

	raiz.Parent = workspace
	-- Se coloca todo una vez antes de mostrarlo, para que el primer fotograma ya esté en su sitio.
	paso(0)
	RunService:BindToRenderStep(NOMBRE_PASO, Enum.RenderPriority.Camera.Value, paso)
end

-- El ratón o el dedo está sobre un lado (o sobre ninguno). La grieta lanza energía hacia el planeta resaltado.
function Escena.Resaltar(bando: string?)
	if carpeta == nil or elegido ~= nil or resaltado == bando then
		return
	end
	resaltado = bando
	if bando == nil or planetas[bando] == nil then
		return
	end
	local ahora = os.clock()
	if ahora - ultimoRayoResaltar < Config.Escena.EsperaRayoResaltar then
		return
	end
	ultimoRayoResaltar = ahora
	grietaSurge = math.max(grietaSurge, 0.25)
	local planeta = planetas[bando]
	local camara = workspace.CurrentCamera
	local haciaCamara = if camara then (camara.CFrame.Position - planeta.Centro).Unit else Vector3.zAxis
	Gestor.Reproducir(`Eleccion_Grieta_Resaltar_{bando}`, "Impacto", {
		Origen = grietaCentro,
		Punto = planeta.Centro,
		Direccion = haciaCamara,
		EsLocal = true,
		DistanciaMaxima = 1000,
	})
end

-- Opciones comunes de los efectos que ocurren en un planeta: dirección hacia la cámara (las ondas se ven de cara).
local function opcionesPlaneta(planeta: Planeta): any
	local camara = workspace.CurrentCamera
	local haciaCamara = if camara then (camara.CFrame.Position - planeta.Centro) else Vector3.zAxis
	return {
		Origen = grietaCentro,
		Punto = planeta.Centro,
		Direccion = if haciaCamara.Magnitude > 1e-3 then haciaCamara.Unit else Vector3.zAxis,
		EsLocal = true,
		DistanciaMaxima = 1000,
	}
end

-- El jugador ha hecho clic: el planeta se encoge un poco y la energía se recoge hacia él (anticipación).
function Escena.Anticipar(bando: string)
	local planeta = planetas[bando]
	if carpeta == nil or planeta == nil or elegido ~= nil then
		return
	end
	resaltado = bando
	anticipando = bando
	grietaSurge = math.max(grietaSurge, 0.5)
	Gestor.Reproducir(`Eleccion_Anticipar_{bando}`, "Anticipacion", opcionesPlaneta(planeta))
end

-- El servidor no confirmó a tiempo: se deshace la anticipación y se puede volver a elegir.
function Escena.Cancelar()
	anticipando = nil
end

--[[
	El servidor ha confirmado el bando: congelación de un instante (hitstop), estallido del planeta elegido con rayos
	desde la grieta, el otro lado se apaga y la cámara se acerca despacio al planeta elegido.
]]
function Escena.Confirmar(bando: string)
	local planeta = planetas[bando]
	if carpeta == nil or planeta == nil or elegido ~= nil then
		return
	end
	elegido = bando
	resaltado = bando
	anticipando = nil
	congeladaHasta = os.clock() + Config.Tiempos.Congelacion
	-- Impacto exagerado: el planeta salta por encima de su tamaño y se asienta (recuperación).
	planeta.Golpe = Config.Escena.EscalaGolpe - Config.Escena.EscalaElegido
	grietaSurge = 1.4
	Gestor.Reproducir(`Eleccion_Confirmar_{bando}`, { "Impacto", "Residuo" }, opcionesPlaneta(planeta))
end

-- Desmonta la escena y suelta la cámara (Bloqueo la devuelve al personaje).
function Escena.Destruir()
	RunService:UnbindFromRenderStep(NOMBRE_PASO)
	if sonidoAmbiente then
		sonidoAmbiente:Stop()
		sonidoAmbiente = nil
	end
	if carpeta then
		carpeta:Destroy()
		carpeta = nil
	end
	table.clear(planetas)
	table.clear(figuras)
	table.clear(foco)
	table.clear(rafagas)
	table.clear(solPiezas)
	table.clear(grietaAdjuntos)
	table.clear(grietaCapas)
	table.clear(ramasAdjuntos)
	table.clear(ramasCapas)
	grietaRamas = {}
	grietaForma = nil
	grietaLuz = nil
	resaltado, elegido, anticipando = nil, nil, nil
end

return Escena
