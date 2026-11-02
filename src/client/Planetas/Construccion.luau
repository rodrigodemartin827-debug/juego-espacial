--!strict
--[[
	Construccion (Planetas, cliente): crea las piezas que forman cada cuerpo celeste visto desde lejos.

	  Planetas      una esfera grande + manchas (continentes, hielo, grietas) + una capa de nubes que gira +
	                la atmósfera (una esfera translúcida y un halo que siempre mira a la cámara)
	  Sol           núcleo de neón, dos coronas, halo de brillo, destellos en estrella y llamaradas que laten
	  Agujero negro horizonte negro, sombra y anillo de fotones (lente: siempre miran a la cámara), disco de
	                acreción en capas con grumos que orbitan (se ve girar) y partículas que caen en espiral

	Todo son partes con una SpecialMesh de esfera o cilindro escalada, más unos BillboardGui para los halos. Una
	Part no puede medir más de 2048 studs, pero su malla sí: así un planeta de casi 5000 studs es UNA pieza. Las
	piezas no chocan, no se pueden apuntar ni tocar y no dan sombra (rendimiento en móvil).

	Cada cuerpo se devuelve con sus ELEMENTOS en coordenadas locales (studs reales respecto a su centro) y una
	función Animar; client/Planetas/Cuerpos los coloca y los escala cada fotograma (ver allí el "doble" lejano).
	Los números y colores salen de Planetas/Datos; las piezas de los planetas, de Planetas/Apariencia.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Apariencia = require(Shared.Planetas.Apariencia)
local Azar = require(Shared.Utilidades.Azar)
local Datos = require(Shared.Planetas.Datos)
local Calidad = require(script.Parent.Parent.VFX.Calidad)

export type Elemento = {
	Parte: BasePart,
	Malla: SpecialMesh?, -- nil: se escala cambiando Size (piezas de menos de 2048 studs, como los discos)
	Local: CFrame, -- posición y giro respecto al centro del cuerpo (studs reales)
	Tamano: Vector3, -- tamaño real (studs)
	Grupo: string?, -- "Nubes", "Disco"...: lo que Animar mueve aparte
	Aplicado: Vector3?, -- último tamaño visible aplicado (Cuerpos solo reescala si cambia)
}

export type Halo = {
	Gui: BillboardGui,
	Diametro: number, -- studs reales
}

export type Cuerpo = {
	Nombre: string,
	Centro: Vector3, -- en el espacio (studs reales)
	Radio: number, -- radio visible aproximado (para decidir distancias)
	Carpeta: Folder,
	Ancla: BasePart, -- donde se pegan los halos
	Elementos: { Elemento },
	Halos: { Halo },
	-- Mueve lo que se anima (nubes, disco, llamaradas, partículas). `t` segundos desde el inicio, `cerca` si se ve
	-- de cerca (si no, se pueden saltar detalles). Cambia `Local` de los elementos; Cuerpos los recoloca.
	Animar: ((t: number, dt: number, cerca: boolean) -> ())?,
	-- Partículas o adornos que se gestionan solos (se ocultan con Mostrar(false)).
	Mostrar: ((visible: boolean) -> ())?,
}

local Construccion = {}

local TAMANO_MAXIMO = 2048

local function v3(v: { X: number, Y: number, Z: number }): Vector3
	return Vector3.new(v.X, v.Y, v.Z)
end

local function color(hex: string): Color3
	return Color3.fromHex(hex)
end

local function parteBase(
	carpeta: Instance,
	nombre: string,
	tono: Color3,
	material: Enum.Material,
	transparencia: number?
): Part
	local p = Instance.new("Part")
	p.Name = nombre
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Material = material
	p.Color = tono
	p.Transparency = transparencia or 0
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = carpeta
	return p
end

-- Elipsoide (parte con malla de esfera) de un tamaño real cualquiera, aunque pase de 2048 studs.
local function pieza(
	carpeta: Instance,
	nombre: string,
	tamano: Vector3,
	tono: Color3,
	material: Enum.Material,
	transparencia: number?
): (Part, SpecialMesh)
	local p = parteBase(carpeta, nombre, tono, material, transparencia)
	p.Size = Vector3.new(
		math.clamp(tamano.X, 0.05, TAMANO_MAXIMO),
		math.clamp(tamano.Y, 0.05, TAMANO_MAXIMO),
		math.clamp(tamano.Z, 0.05, TAMANO_MAXIMO)
	)
	local malla = Instance.new("SpecialMesh")
	malla.MeshType = Enum.MeshType.Sphere
	malla.Scale = tamano / p.Size
	malla.Parent = p
	return p, malla
end

-- Disco: un cilindro de Roblox (su eje es X). Debe medir menos de 2048 studs: se escala cambiando Size.
local function disco(carpeta: Instance, nombre: string, tamano: Vector3, tono: Color3, transparencia: number): Part
	local p = parteBase(carpeta, nombre, tono, Enum.Material.Neon, transparencia)
	p.Shape = Enum.PartType.Cylinder
	p.Size = Vector3.new(
		math.clamp(tamano.X, 0.05, TAMANO_MAXIMO),
		math.clamp(tamano.Y, 0.05, TAMANO_MAXIMO),
		math.clamp(tamano.Z, 0.05, TAMANO_MAXIMO)
	)
	return p
end

local function agregar(
	lista: { Elemento },
	parte: BasePart,
	malla: SpecialMesh?,
	marco: CFrame,
	tamano: Vector3,
	grupo: string?
): Elemento
	local elemento = { Parte = parte, Malla = malla, Local = marco, Tamano = tamano, Grupo = grupo }
	table.insert(lista, elemento)
	return elemento
end

-- Material por nombre (SmoothPlastic si no existe).
local function material(nombre: string?): Enum.Material
	if nombre == nil then
		return Enum.Material.SmoothPlastic
	end
	local ok, valor = pcall(function()
		return (Enum.Material :: any)[nombre]
	end)
	return if ok and valor then valor else Enum.Material.SmoothPlastic
end

--[[
	Halo que siempre mira a la cámara: círculos concéntricos (Frames redondos) de colores y transparencias que,
	superpuestos, hacen un degradado radial sin necesidad de texturas. `anillos` es una lista de
	{ fracción del diámetro, color, transparencia } de fuera a dentro.
]]
local function halo(ancla: BasePart, nombre: string, anillos: { { any } }): BillboardGui
	local gui = Instance.new("BillboardGui")
	gui.Name = nombre
	gui.Adornee = ancla
	gui.LightInfluence = 0
	gui.AlwaysOnTop = false
	gui.MaxDistance = math.huge
	gui.ResetOnSpawn = false
	gui.Size = UDim2.fromScale(1, 1)
	for indice, anillo in anillos do
		local fraccion: number, tono: Color3, transparencia: number = anillo[1], anillo[2], anillo[3]
		local circulo = Instance.new("Frame")
		circulo.Name = `Anillo{indice}`
		circulo.AnchorPoint = Vector2.new(0.5, 0.5)
		circulo.Position = UDim2.fromScale(0.5, 0.5)
		circulo.Size = UDim2.fromScale(fraccion, fraccion)
		circulo.BackgroundColor3 = tono
		circulo.BackgroundTransparency = transparencia
		circulo.BorderSizePixel = 0
		circulo.ZIndex = indice
		local esquina = Instance.new("UICorner")
		esquina.CornerRadius = UDim.new(0.5, 0)
		esquina.Parent = circulo
		circulo.Parent = gui
	end
	gui.Parent = ancla
	return gui
end

-- Marco cuyo eje Y apunta hacia `normal` (para tumbar una lente sobre la superficie), girado `giro` en ella.
local function marcoSobre(normal: Vector3, distancia: number, giro: number): CFrame
	local referencia = if math.abs(normal.Y) < 0.95 then Vector3.yAxis else Vector3.xAxis
	local derecha = referencia:Cross(normal).Unit
	local frente = derecha:Cross(normal)
	return CFrame.fromMatrix(normal * distancia, derecha, normal, frente) * CFrame.Angles(0, giro, 0)
end

-- ===========================================================================================================
-- PLANETAS
-- ===========================================================================================================

function Construccion.Planeta(id: string, padre: Instance): Cuerpo
	local datos = Datos.Planetas[id]
	local radio = datos.Radio
	local carpeta = Instance.new("Folder")
	carpeta.Name = `Planeta_{id}`
	carpeta.Parent = padre

	local elementos: { Elemento } = {}
	local halos: { Halo } = {}
	local ancla: BasePart? = nil
	local nubes: { { Elemento: Elemento, Base: CFrame } } = {}
	local giroNubes = 0

	for indiceCapa, capa in datos.Apariencia do
		local tono = color(capa.Color)
		local mat = if capa.Neon then Enum.Material.Neon else material(capa.Material)
		if capa.Tipo == "Esfera" then
			local diametro = 2 * radio * (capa.Escala or 1)
			local tamano = Vector3.one * diametro
			local p, m = pieza(carpeta, `Esfera{indiceCapa}`, tamano, tono, mat, capa.Transparencia)
			agregar(elementos, p, m, CFrame.identity, tamano)
			if ancla == nil then
				ancla = p
			end
		elseif capa.Tipo == "Manchas" or capa.Tipo == "Nubes" then
			local esNube = capa.Tipo == "Nubes"
			if esNube then
				giroNubes = capa.Giro or 0
			end
			for indice, datosPieza in Apariencia.Piezas(capa, radio) do
				local tamano = v3(datosPieza.Tamano)
				local p, m =
					pieza(carpeta, `{capa.Tipo}{indice}`, tamano, color(datosPieza.Color), mat, capa.Transparencia)
				local marco = marcoSobre(v3(datosPieza.Direccion), datosPieza.Distancia, datosPieza.Giro)
				local elemento = agregar(elementos, p, m, marco, tamano, if esNube then "Nubes" else nil)
				if esNube then
					table.insert(nubes, { Elemento = elemento, Base = marco })
				end
			end
		end
	end

	local anclaFinal = ancla :: BasePart
	-- Atmósfera: halo que asoma alrededor del planeta (el planeta tapa su centro).
	for _, capa in datos.Apariencia do
		if capa.Tipo == "Halo" then
			local tono = color(capa.Color)
			local base = capa.Transparencia or 0.5
			local escala = capa.Escala or 1.3
			local gui = halo(anclaFinal, "Atmosfera", {
				{ 1, tono, 0.97 },
				{ 0.94, tono, 0.93 },
				{ 0.88, tono, 0.88 },
				{ (1 + 1 / escala) / 2, tono, base + (1 - base) * 0.55 },
				{ 1 / escala * 1.02, tono, base },
			})
			table.insert(halos, { Gui = gui, Diametro = 2 * radio * escala })
		end
	end

	local function animar(t: number, _dt: number, _cerca: boolean)
		if giroNubes == 0 then
			return
		end
		local giro = CFrame.Angles(0, t * giroNubes, 0)
		for _, nube in nubes do
			nube.Elemento.Local = giro * nube.Base
		end
	end

	return {
		Nombre = id,
		Centro = v3(datos.Centro),
		Radio = radio,
		Carpeta = carpeta,
		Ancla = anclaFinal,
		Elementos = elementos,
		Halos = halos,
		Animar = animar,
		Mostrar = nil,
	}
end

-- ===========================================================================================================
-- SOL
-- ===========================================================================================================

function Construccion.Sol(padre: Instance): Cuerpo
	local datos = Datos.Sol
	local aspecto = datos.Apariencia
	local radio = datos.Radio
	local carpeta = Instance.new("Folder")
	carpeta.Name = "Sol"
	carpeta.Parent = padre
	local elementos: { Elemento } = {}
	local halos: { Halo } = {}

	local tamanoNucleo = Vector3.one * radio * 2
	local nucleo, mallaNucleo = pieza(carpeta, "Nucleo", tamanoNucleo, color(aspecto.Nucleo), Enum.Material.Neon)
	agregar(elementos, nucleo, mallaNucleo, CFrame.identity, tamanoNucleo)
	local tamanoCorona = Vector3.one * radio * 2.24
	local corona, mallaCorona = pieza(carpeta, "Corona", tamanoCorona, color(aspecto.Corona), Enum.Material.Neon, 0.55)
	agregar(elementos, corona, mallaCorona, CFrame.identity, tamanoCorona)
	local tamanoExterior = Vector3.one * radio * 2.7
	local exterior, mallaExterior =
		pieza(carpeta, "CoronaExterior", tamanoExterior, color(aspecto.CoronaExterior), Enum.Material.Neon, 0.82)
	agregar(elementos, exterior, mallaExterior, CFrame.identity, tamanoExterior)

	-- Halo de brillo (degradado radial con los colores de Halo, de dentro a fuera).
	local colores = aspecto.Halo
	local anillos: { { any } } = {}
	local pasos = 7
	for i = 1, pasos do
		local f = 1 - (i - 1) / pasos * 0.72 -- de 1 (fuera) a ~0.3 (dentro)
		local indiceColor = math.clamp(math.ceil((1 - (i - 1) / pasos) * #colores), 1, #colores)
		local anillo: { any } = { f, color(colores[indiceColor]), 0.955 - i * 0.02 }
		table.insert(anillos, anillo)
	end
	local gui = halo(nucleo, "Brillo", anillos)
	table.insert(halos, { Gui = gui, Diametro = radio * aspecto.EscalaHalo * 2 })

	-- Destellos en estrella: barras finas que se desvanecen hacia las puntas (UIGradient).
	local estrella = Instance.new("BillboardGui")
	estrella.Name = "Destellos"
	estrella.Adornee = nucleo
	estrella.LightInfluence = 0
	estrella.MaxDistance = math.huge
	estrella.Size = UDim2.fromScale(1, 1)
	for i, angulo in { 0, 90, 45, 135 } do
		local barra = Instance.new("Frame")
		barra.AnchorPoint = Vector2.new(0.5, 0.5)
		barra.Position = UDim2.fromScale(0.5, 0.5)
		local largo = if i <= 2 then 1 else 0.62
		barra.Size = UDim2.fromScale(largo, 0.012)
		barra.Rotation = angulo
		barra.BorderSizePixel = 0
		barra.BackgroundColor3 = color(aspecto.Nucleo)
		barra.BackgroundTransparency = 0.25
		local gradiente = Instance.new("UIGradient")
		gradiente.Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.5, 0.1),
			NumberSequenceKeypoint.new(1, 1),
		})
		gradiente.Parent = barra
		barra.Parent = estrella
	end
	estrella.Parent = nucleo
	table.insert(halos, { Gui = estrella, Diametro = radio * aspecto.EscalaHalo * 3.2 })

	-- Llamaradas: arcos de plasma (cadenas de elipsoides) que salen de la superficie, crecen y se apagan.
	local azar = Azar.nuevo(31337)
	type Llamarada = { Piezas: { Elemento }, Normal: Vector3, Lado: Vector3, Fase: number, Periodo: number }
	local llamaradas: { Llamarada } = {}
	local tono = color(aspecto.ColorLlamarada)
	for i = 1, aspecto.Llamaradas do
		local x, y, z = azar:Direccion()
		local normal = Vector3.new(x, y, z)
		local referencia = if math.abs(normal.Y) < 0.9 then Vector3.yAxis else Vector3.xAxis
		local lado = normal:Cross(referencia).Unit
		local lista = {}
		for j = 1, 5 do
			local tamano = Vector3.new(radio * 0.09, radio * 0.09, radio * 0.2)
			local p, m = pieza(carpeta, `Llamarada{i}_{j}`, tamano, tono, Enum.Material.Neon, 0.3)
			table.insert(lista, agregar(elementos, p, m, CFrame.identity, tamano, "Llamaradas"))
		end
		table.insert(
			llamaradas,
			{ Piezas = lista, Normal = normal, Lado = lado, Fase = azar:Entre(0, 10), Periodo = azar:Entre(6, 11) }
		)
	end

	local function animar(t: number, _dt: number, cerca: boolean)
		-- La corona late despacio.
		local latido = 1 + 0.025 * math.sin(t * 0.9)
		corona.Transparency = 0.55 + 0.05 * math.sin(t * 1.3)
		exterior.Transparency = 0.82 + 0.04 * math.sin(t * 0.7 + 1)
		elementos[2].Local = CFrame.identity
		elementos[2].Tamano = tamanoCorona * latido
		if not cerca then
			return
		end
		for _, ll in llamaradas do
			-- Cada llamarada crece desde la superficie hasta un arco y se apaga.
			local u = ((t + ll.Fase) % ll.Periodo) / ll.Periodo
			local altura = math.sin(u * math.pi) -- 0 → 1 → 0
			for j, elemento in ll.Piezas do
				local a = (j - 1) / (#ll.Piezas - 1) * math.pi -- de un pie del arco al otro
				local alto = radio * (1 + 0.32 * altura * math.sin(a))
				local ancho = radio * 0.28 * math.cos(a)
				local posicion = ll.Normal * alto + ll.Lado * ancho
				local tangente = (ll.Normal * math.cos(a) - ll.Lado * math.sin(a)).Unit
				elemento.Local = CFrame.lookAt(posicion, posicion + tangente)
				elemento.Parte.Transparency = 0.25 + 0.75 * (1 - altura)
			end
		end
	end

	return {
		Nombre = "Sol",
		Centro = v3(datos.Centro),
		Radio = radio * 1.35,
		Carpeta = carpeta,
		Ancla = nucleo,
		Elementos = elementos,
		Halos = halos,
		Animar = animar,
		Mostrar = nil,
	}
end

-- ===========================================================================================================
-- AGUJERO NEGRO
-- ===========================================================================================================

function Construccion.AgujeroNegro(padre: Instance): Cuerpo
	local datos = Datos.AgujeroNegro
	local aspecto = datos.Apariencia
	local rh = datos.RadioHorizonte
	local carpeta = Instance.new("Folder")
	carpeta.Name = "AgujeroNegro"
	carpeta.Parent = padre
	local elementos: { Elemento } = {}
	local halos: { Halo } = {}

	-- Horizonte: negro absoluto (el neón negro no recibe luz).
	local tamanoHorizonte = Vector3.one * rh * 2
	local horizonte, mallaHorizonte =
		pieza(carpeta, "Horizonte", tamanoHorizonte, Color3.new(0, 0, 0), Enum.Material.Neon)
	agregar(elementos, horizonte, mallaHorizonte, CFrame.identity, tamanoHorizonte)

	-- Disco de acreción: discos planos de más fino (fuera) a más grueso (dentro) para que no se pisen.
	local inclinacion = CFrame.Angles(math.rad(aspecto.InclinacionDisco), 0, math.rad(aspecto.InclinacionDisco * 0.4))
	local radiosDisco = aspecto.RadiosDisco
	local coloresDisco = aspecto.Disco
	for i = #radiosDisco, 1, -1 do
		local diametro = radiosDisco[i] * rh * 2
		local grosor = rh * (0.02 + 0.03 * (#radiosDisco - i))
		-- El eje del cilindro es X: se tumba para que el disco quede en el plano XZ.
		local tamano = Vector3.new(grosor, diametro, diametro)
		local transparencia = 0.12 + (i - 1) * 0.2
		local p = disco(carpeta, `Disco{i}`, tamano, color(coloresDisco[i]), transparencia)
		agregar(elementos, p, nil, inclinacion * CFrame.Angles(0, 0, math.pi / 2), tamano, "Disco")
	end

	-- Grumos que orbitan (velocidad de Kepler: los de dentro van más deprisa). Así se ve girar el disco.
	local azar = Azar.nuevo(4096)
	type Grumo = { Elemento: Elemento, Radio: number, Angulo: number, Velocidad: number }
	local grumos: { Grumo } = {}
	local radioInterior, radioExterior = radiosDisco[1] * rh * 0.9, radiosDisco[#radiosDisco] * rh * 0.85
	for i = 1, aspecto.Grumos do
		local r = radioInterior + (radioExterior - radioInterior) * azar:Siguiente() ^ 1.5
		local tamano = Vector3.new(rh * 0.08, rh * 0.05, rh * (0.25 + 0.35 * azar:Siguiente()))
		local fraccion = (r - radioInterior) / (radioExterior - radioInterior)
		local indiceColor = math.clamp(math.floor(fraccion * #coloresDisco) + 1, 1, #coloresDisco)
		local p, m = pieza(carpeta, `Grumo{i}`, tamano, color(coloresDisco[indiceColor]), Enum.Material.Neon, 0.1)
		local elemento = agregar(elementos, p, m, CFrame.identity, tamano, "Disco")
		table.insert(grumos, {
			Elemento = elemento,
			Radio = r,
			Angulo = azar:Entre(0, math.pi * 2),
			Velocidad = 0.9 * (radioInterior / r) ^ 1.5,
		})
	end

	-- Lente: la "sombra" negra (más grande que el horizonte, como en los agujeros de verdad), el anillo de fotones
	-- y el resplandor de la luz del disco curvada por detrás. Son halos: siempre miran a la cámara.
	local diametroLente = rh * 8
	local lente = halo(horizonte, "Lente", {
		{ 1, color(aspecto.Lente), 0.9 },
		{ 0.86, color(aspecto.Lente), 0.78 },
		{ 0.74, color(aspecto.AnilloFotones), 0.35 },
		{ 0.69, color(aspecto.AnilloFotones), 0.05 },
		{ 0.655, Color3.new(0, 0, 0), 0 },
	})
	table.insert(halos, { Gui = lente, Diametro = diametroLente })
	-- Distorsión aparente: un velo oscuro y ancho alrededor que oscurece las estrellas de detrás.
	local velo = halo(horizonte, "Velo", {
		{ 1, Color3.new(0, 0, 0), 0.94 },
		{ 0.8, Color3.new(0, 0, 0), 0.9 },
		{ 0.6, Color3.fromRGB(10, 0, 18), 0.84 },
	})
	table.insert(halos, { Gui = velo, Diametro = rh * 16 })

	-- Partículas absorbidas: caen en espiral hacia el horizonte, se estiran y se apagan. Se reutilizan siempre
	-- las mismas piezas (nunca se crean ni destruyen al animar). Cuántas, según la calidad (móvil: menos).
	type Particula = {
		Elemento: Elemento,
		Inicio: number,
		Duracion: number,
		Radio: number,
		Angulo: number,
		Altura: number,
	}
	local particulas: { Particula } = {}
	local coloresParticulas = aspecto.ColorParticulas
	local radioParticulas = aspecto.RadioParticulas * rh
	local segundos = aspecto.SegundosParticula
	local function reiniciar(p: Particula, ahora: number)
		p.Inicio = ahora
		p.Duracion = azar:Entre(segundos[1], segundos[2])
		p.Radio = radioParticulas * azar:Entre(0.6, 1)
		p.Angulo = azar:Entre(0, math.pi * 2)
		p.Altura = azar:Entre(-0.25, 0.25) * rh
	end
	for i = 1, aspecto.Particulas do
		local tamano = Vector3.new(rh * 0.04, rh * 0.04, rh * 0.12)
		local tono = color(coloresParticulas[(i % #coloresParticulas) + 1])
		local p, m = pieza(carpeta, `Particula{i}`, tamano, tono, Enum.Material.Neon, 0.2)
		local particula = {
			Elemento = agregar(elementos, p, m, CFrame.identity, tamano, "Particulas"),
			Inicio = 0,
			Duracion = 1,
			Radio = radioParticulas,
			Angulo = 0,
			Altura = 0,
		}
		reiniciar(particula, -azar:Entre(0, segundos[2])) -- cada una empieza en un punto distinto de su caída
		table.insert(particulas, particula)
	end

	local visibles = true
	local function mostrarParticulas(visible: boolean)
		local limite = math.max(4, math.floor(#particulas * Calidad.Factor("Particulas")))
		for i, p in particulas do
			p.Elemento.Parte.Transparency = if visible and i <= limite then 0.2 else 1
		end
		visibles = visible
	end

	local function animar(t: number, _dt: number, cerca: boolean)
		for _, g in grumos do
			local a = g.Angulo + t * g.Velocidad
			local posicion = Vector3.new(math.cos(a) * g.Radio, 0, math.sin(a) * g.Radio)
			local tangente = Vector3.new(-math.sin(a), 0, math.cos(a))
			g.Elemento.Local = inclinacion * CFrame.lookAt(posicion, posicion + tangente)
		end
		if cerca ~= visibles then
			mostrarParticulas(cerca)
		end
		if not cerca then
			return
		end
		for _, p in particulas do
			local u = (t - p.Inicio) / p.Duracion
			if u >= 1 then
				reiniciar(p, t)
				u = 0
			end
			-- Espiral que se acelera al caer: el radio baja y el ángulo gira cada vez más deprisa.
			local caida = u ^ 1.6
			local r = p.Radio + (rh * 0.95 - p.Radio) * caida
			local a = p.Angulo + 7 * caida + u * 2
			local posicion = Vector3.new(math.cos(a) * r, p.Altura * (1 - caida), math.sin(a) * r)
			local tangente = Vector3.new(-math.sin(a), 0, math.cos(a))
			local elemento = p.Elemento
			elemento.Local = inclinacion * CFrame.lookAt(posicion, posicion + tangente)
			-- Se estira al acercarse (marea gravitatoria).
			elemento.Tamano = Vector3.new(rh * 0.04, rh * 0.04, rh * (0.1 + 0.5 * caida))
		end
	end

	return {
		Nombre = "AgujeroNegro",
		Centro = v3(datos.Centro),
		Radio = radiosDisco[#radiosDisco] * rh,
		Carpeta = carpeta,
		Ancla = horizonte,
		Elementos = elementos,
		Halos = halos,
		Animar = animar,
		Mostrar = mostrarParticulas,
	}
end

return Construccion
