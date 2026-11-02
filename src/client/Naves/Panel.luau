--!strict
--[[
	Panel (Naves): el panel de mandos del piloto, todo construido por código.

	  - Casco, escudo y turbo en tres barras (en móvil, arriba para no tapar los pulgares).
	  - Velocidad, mira central, bodega y niveles de las mejoras.
	  - Radar de corto alcance, centrado en la nave y orientado a su proa: muestra asteroides y naves dentro del
	    alcance del ESCÁNER (que depende del nivel de esa mejora). Las naves enemigas salen en rojo y las aliadas
	    en verde.
	  - Avisos de texto que se desvanecen.

	El servidor manda una foto del estado (EstadoNave) unas veces por segundo y al ocurrir algo; entre una foto y
	otra el panel hace avanzar solo la recarga del escudo y el turbo con las mismas fórmulas, así que las barras
	se mueven con suavidad sin tráfico constante.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local CombateReglas = require(Shared.Combate.Reglas)
local Config = require(Shared.Naves.Config)
local Inventario = require(Shared.Exploracion.Inventario)
local Mejoras = require(Shared.Naves.Datos.Mejoras)
local Calidad = require(script.Parent.Parent.VFX.Calidad)
local ServicioDatos = require(script.Parent.Parent.Servicios.ServicioDatos)

local Panel = {}

local FONDO = Color3.fromRGB(12, 14, 26)
local TEXTO = Color3.fromRGB(235, 240, 255)
local CIAN = Color3.fromRGB(77, 240, 255)
local VERDE = Color3.fromRGB(80, 220, 120)
local ROJO = Color3.fromRGB(255, 77, 94)
local MORADO = Color3.fromRGB(181, 140, 255)

local MAX_PUNTOS_RADAR = 90
local INTERVALO_RADAR = 1 / 15

type Barra = { Relleno: Frame, Texto: TextLabel }

local gui: ScreenGui? = nil
local conexion: RBXScriptConnection? = nil
local foco: BasePart? = nil -- la parte principal de la nave del piloto
local foto: any = nil -- último EstadoNave recibido
local fotoEn = 0 -- cuándo (os.clock) se recibió

-- Se rellenan en construir().
local barraEscudo: Barra = nil :: any
local barraCasco: Barra = nil :: any
local barraTurbo: Barra = nil :: any
local textoVelocidad: TextLabel = nil :: any
local textoBodega: TextLabel = nil :: any
local textoMejoras: TextLabel = nil :: any
local textoAviso: TextLabel = nil :: any
local fondoRadar: Frame = nil :: any
local barrido: Frame = nil :: any
local puntos: { Frame } = {}
local ultimoRadar = 0
local textoAyuda: TextLabel? = nil

-- ===== Construcción =====

local function redondear(objeto: GuiObject, radio: number?)
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, radio or 6)
	esquina.Parent = objeto
end

local function borde(objeto: GuiObject, color: Color3, transparencia: number?)
	local trazo = Instance.new("UIStroke")
	trazo.Color = color
	trazo.Thickness = 1.5
	trazo.Transparency = transparencia or 0.4
	trazo.Parent = objeto
end

local function etiqueta(
	padre: Instance,
	texto: string,
	tamano: UDim2,
	posicion: UDim2,
	tamanoTexto: number,
	color: Color3?,
	alineacion: Enum.TextXAlignment?
): TextLabel
	local objeto = Instance.new("TextLabel")
	objeto.BackgroundTransparency = 1
	objeto.Size = tamano
	objeto.Position = posicion
	objeto.Text = texto
	objeto.Font = Enum.Font.GothamBold
	objeto.TextSize = tamanoTexto
	objeto.TextColor3 = color or TEXTO
	objeto.TextXAlignment = alineacion or Enum.TextXAlignment.Left
	objeto.TextStrokeTransparency = 0.6
	objeto.Parent = padre
	return objeto
end

local function crearBarra(padre: Instance, nombre: string, alto: number, y: number, color: Color3): Barra
	local fondo = Instance.new("Frame")
	fondo.BackgroundColor3 = FONDO
	fondo.BackgroundTransparency = 0.3
	fondo.Size = UDim2.new(1, 0, 0, alto)
	fondo.Position = UDim2.new(0, 0, 0, y)
	fondo.Parent = padre
	redondear(fondo, 5)
	borde(fondo, color, 0.55)

	local relleno = Instance.new("Frame")
	relleno.BackgroundColor3 = color
	relleno.BorderSizePixel = 0
	relleno.Size = UDim2.fromScale(1, 1)
	relleno.Parent = fondo
	redondear(relleno, 5)

	local texto = etiqueta(fondo, nombre, UDim2.fromScale(1, 1), UDim2.fromOffset(8, 0), alto - 4, TEXTO)
	texto.ZIndex = 3
	return { Relleno = relleno, Texto = texto }
end

local function construir()
	local jugador = Players.LocalPlayer
	local movil = Calidad.EsMovil
	local pantalla = Instance.new("ScreenGui")
	pantalla.Name = "PanelNave"
	pantalla.ResetOnSpawn = false
	pantalla.IgnoreGuiInset = false
	pantalla.DisplayOrder = 15
	pantalla.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

	-- Barras.
	local contenedor = Instance.new("Frame")
	contenedor.BackgroundTransparency = 1
	contenedor.AnchorPoint = Vector2.new(0.5, if movil then 0 else 1)
	contenedor.Position = if movil then UDim2.new(0.5, 0, 0, 8) else UDim2.new(0.5, 0, 1, -16)
	contenedor.Size = UDim2.fromOffset(if movil then 250 else 400, if movil then 46 else 62)
	contenedor.Parent = pantalla
	barraEscudo = crearBarra(contenedor, "ESCUDO", if movil then 14 else 18, 0, CIAN)
	barraCasco = crearBarra(contenedor, "CASCO", if movil then 14 else 20, if movil then 16 else 21, VERDE)
	barraTurbo = crearBarra(contenedor, "TURBO", if movil then 10 else 12, if movil then 32 else 44, MORADO)

	-- Mira central.
	local mira = Instance.new("Frame")
	mira.BackgroundTransparency = 1
	mira.AnchorPoint = Vector2.new(0.5, 0.5)
	mira.Position = UDim2.fromScale(0.5, 0.5)
	mira.Size = UDim2.fromOffset(44, 44)
	mira.Parent = pantalla
	local anillo = Instance.new("Frame")
	anillo.BackgroundTransparency = 1
	anillo.AnchorPoint = Vector2.new(0.5, 0.5)
	anillo.Position = UDim2.fromScale(0.5, 0.5)
	anillo.Size = UDim2.fromOffset(30, 30)
	anillo.Parent = mira
	redondear(anillo, 999)
	borde(anillo, CIAN, 0.2)
	local centro = Instance.new("Frame")
	centro.BackgroundColor3 = CIAN
	centro.AnchorPoint = Vector2.new(0.5, 0.5)
	centro.Position = UDim2.fromScale(0.5, 0.5)
	centro.Size = UDim2.fromOffset(4, 4)
	centro.Parent = mira
	redondear(centro, 2)
	for _, marca in { { 0.5, 0, 2, 8 }, { 0.5, 1, 2, 8 }, { 0, 0.5, 8, 2 }, { 1, 0.5, 8, 2 } } do
		local trazo = Instance.new("Frame")
		trazo.BackgroundColor3 = CIAN
		trazo.BorderSizePixel = 0
		trazo.AnchorPoint = Vector2.new(0.5, 0.5)
		trazo.Position = UDim2.fromScale(marca[1], marca[2])
		trazo.Size = UDim2.fromOffset(marca[3], marca[4])
		trazo.Parent = mira
	end

	-- Velocidad, bodega y mejoras (esquina superior izquierda en ordenador; en móvil, solo la velocidad).
	local datos = Instance.new("Frame")
	datos.BackgroundColor3 = FONDO
	datos.BackgroundTransparency = 0.35
	datos.Position = UDim2.fromOffset(12, if movil then 8 else 12)
	datos.Size = UDim2.fromOffset(if movil then 120 else 210, if movil then 30 else 92)
	datos.Parent = pantalla
	redondear(datos, 8)
	borde(datos, CIAN, 0.6)
	textoVelocidad =
		etiqueta(datos, "0", UDim2.new(1, -12, 0, 28), UDim2.fromOffset(8, 2), if movil then 20 else 26, CIAN)
	textoBodega = etiqueta(datos, "", UDim2.new(1, -12, 0, 16), UDim2.fromOffset(8, 32), 13, TEXTO)
	textoMejoras =
		etiqueta(datos, "", UDim2.new(1, -12, 0, 40), UDim2.fromOffset(8, 48), 12, Color3.fromRGB(170, 180, 205))
	textoMejoras.TextWrapped = true
	textoMejoras.TextYAlignment = Enum.TextYAlignment.Top
	textoBodega.Visible = not movil
	textoMejoras.Visible = not movil

	-- Radar.
	local diametro = if movil then 112 else 168
	fondoRadar = Instance.new("Frame")
	fondoRadar.Name = "Radar"
	fondoRadar.BackgroundColor3 = FONDO
	fondoRadar.BackgroundTransparency = 0.3
	fondoRadar.AnchorPoint = if movil then Vector2.new(0, 0) else Vector2.new(0, 1)
	fondoRadar.Position = if movil then UDim2.fromOffset(12, 46) else UDim2.new(0, 14, 1, -16)
	fondoRadar.Size = UDim2.fromOffset(diametro, diametro)
	fondoRadar.ClipsDescendants = true
	fondoRadar.Parent = pantalla
	redondear(fondoRadar, 999)
	borde(fondoRadar, CIAN, 0.3)
	for _, fraccion in { 0.5, 1 } do
		local circulo = Instance.new("Frame")
		circulo.BackgroundTransparency = 1
		circulo.AnchorPoint = Vector2.new(0.5, 0.5)
		circulo.Position = UDim2.fromScale(0.5, 0.5)
		circulo.Size = UDim2.fromScale(fraccion, fraccion)
		circulo.Parent = fondoRadar
		redondear(circulo, 999)
		borde(circulo, CIAN, 0.75)
	end
	-- Haz que gira, como un radar de verdad.
	barrido = Instance.new("Frame")
	barrido.BackgroundColor3 = CIAN
	barrido.BackgroundTransparency = 0.7
	barrido.BorderSizePixel = 0
	barrido.AnchorPoint = Vector2.new(0.5, 1)
	barrido.Position = UDim2.fromScale(0.5, 0.5)
	barrido.Size = UDim2.new(0, 2, 0.5, 0)
	barrido.Parent = fondoRadar
	-- La propia nave, en el centro, con la proa hacia arriba.
	local yo = Instance.new("Frame")
	yo.BackgroundColor3 = TEXTO
	yo.BorderSizePixel = 0
	yo.AnchorPoint = Vector2.new(0.5, 0.5)
	yo.Position = UDim2.fromScale(0.5, 0.5)
	yo.Size = UDim2.fromOffset(6, 9)
	yo.Parent = fondoRadar
	for indice = 1, MAX_PUNTOS_RADAR do
		local punto = Instance.new("Frame")
		punto.Name = `Punto{indice}`
		punto.BorderSizePixel = 0
		punto.AnchorPoint = Vector2.new(0.5, 0.5)
		punto.Visible = false
		punto.Parent = fondoRadar
		table.insert(puntos, punto)
	end

	-- Aviso central.
	textoAviso = etiqueta(
		pantalla,
		"",
		UDim2.fromOffset(520, 34),
		UDim2.new(0.5, -260, 0, if movil then 62 else 90),
		22,
		TEXTO,
		Enum.TextXAlignment.Center
	)
	textoAviso.TextTransparency = 1
	textoAviso.TextStrokeTransparency = 1

	-- Ayuda de controles (solo ordenador): se apaga sola.
	if not movil then
		local ayuda = etiqueta(
			pantalla,
			"W/S acelerar · A/D lateral · Espacio/Ctrl subir/bajar · Ratón orientar · Clic disparar · Shift turbo · F aterrizar",
			UDim2.fromOffset(760, 20),
			UDim2.new(0.5, -380, 1, -92),
			14,
			Color3.fromRGB(200, 210, 235),
			Enum.TextXAlignment.Center
		)
		textoAyuda = ayuda
	end

	pantalla.Parent = jugador:WaitForChild("PlayerGui")
	return pantalla
end

-- ===== Actualización =====

-- Color de la barra de casco: verde con mucha vida, amarillo y rojo al bajar.
local function colorVida(proporcion: number): Color3
	if proporcion > 0.5 then
		return Color3.fromRGB(255, 210, 80):Lerp(VERDE, (proporcion - 0.5) * 2)
	end
	return ROJO:Lerp(Color3.fromRGB(255, 210, 80), proporcion * 2)
end

local function ponerBarra(barra: Barra, valor: number, maximo: number, texto: string)
	local proporcion = if maximo > 0 then math.clamp(valor / maximo, 0, 1) else 0
	barra.Relleno.Size = UDim2.fromScale(proporcion, 1)
	barra.Texto.Text = `{texto}  {math.floor(valor + 0.5)}/{math.floor(maximo + 0.5)}`
end

-- Escudo y turbo "ahora", avanzando la última foto con las fórmulas del servidor.
local function valoresActuales(): (number, number)
	local pasado = os.clock() - fotoEn
	local recarga = math.max(0, pasado - foto.EsperaEscudo)
	local escudo = math.min(foto.EscudoMax, foto.Escudo + foto.RegenEscudo * recarga)
	local turbo
	if foto.TurboActivo then
		turbo = math.max(0, foto.Turbo - foto.TurboConsumo * pasado)
	else
		turbo = math.min(foto.TurboMax, foto.Turbo + foto.TurboRegeneracion * pasado)
	end
	return escudo, turbo
end

local function actualizarRadar(ahora: number)
	local raiz = foco
	if raiz == nil or foto == nil then
		return
	end
	local alcance: number = foto.RadioEscaner
	local radio = fondoRadar.AbsoluteSize.X / 2 - 4
	local marco = raiz.CFrame
	local _, guinada = marco:ToOrientation()
	-- Sistema de la nave sin cabeceo ni alabeo: delante = arriba en el radar.
	local plano = CFrame.new(marco.Position) * CFrame.Angles(0, guinada, 0)

	local candidatos: { { Posicion: Vector3, Tamano: number, Color: Color3, Distancia: number } } = {}
	for _, asteroide in CollectionService:GetTagged(Config.EtiquetaAsteroide) do
		if asteroide:IsA("Model") then
			local posicion = asteroide:GetPivot().Position
			local distancia = (posicion - marco.Position).Magnitude
			if distancia <= alcance then
				local tamano = asteroide:GetAttribute("Tamano")
				table.insert(candidatos, {
					Posicion = posicion,
					Tamano = 3 + math.clamp((if type(tamano) == "number" then tamano else 10) / 6, 0, 6),
					Color = Color3.fromRGB(150, 150, 165),
					Distancia = distancia,
				})
			end
		end
	end
	for _, nave in CollectionService:GetTagged(Config.EtiquetaNave) do
		if nave:IsA("Model") and nave.PrimaryPart ~= raiz and nave.PrimaryPart then
			local posicion = nave.PrimaryPart.Position
			local distancia = (posicion - marco.Position).Magnitude
			if distancia <= alcance then
				local bando = nave:GetAttribute("Bando")
				local enemigo = type(bando) == "string" and CombateReglas.SonEnemigos(foto.Bando, bando)
				table.insert(candidatos, {
					Posicion = posicion,
					Tamano = 8,
					Color = if enemigo then ROJO else VERDE,
					Distancia = 0, -- las naves siempre se dibujan por delante de las rocas
				})
			end
		end
	end
	table.sort(candidatos, function(a, b)
		return a.Distancia < b.Distancia
	end)

	for indice, punto in puntos do
		local candidato = candidatos[indice]
		if candidato == nil then
			punto.Visible = false
			continue
		end
		local relativo = plano:PointToObjectSpace(candidato.Posicion)
		-- x a la derecha; la z negativa (delante) sube en pantalla.
		local px = relativo.X / alcance * radio
		local py = relativo.Z / alcance * radio
		local altura = candidato.Posicion.Y - marco.Position.Y
		punto.Visible = true
		punto.Position = UDim2.new(0.5, px, 0.5, py)
		punto.Size = UDim2.fromOffset(candidato.Tamano, candidato.Tamano)
		-- Más claro si está por encima de la nave, más oscuro si está por debajo.
		local tono = math.clamp(altura / 120, -1, 1)
		punto.BackgroundColor3 = if tono >= 0
			then candidato.Color:Lerp(Color3.new(1, 1, 1), tono * 0.6)
			else candidato.Color:Lerp(Color3.new(0, 0, 0), -tono * 0.6)
		punto.BackgroundTransparency = if candidato.Distancia == 0 then 0 else 0.15
	end
	barrido.Rotation = (ahora * 120) % 360
end

local function paso()
	if gui == nil or foto == nil then
		return
	end
	local ahora = os.clock()
	local escudo, turbo = valoresActuales()

	ponerBarra(barraEscudo, escudo, foto.EscudoMax, "ESCUDO")
	ponerBarra(barraCasco, foto.Vida, foto.VidaMax, "CASCO")
	barraCasco.Relleno.BackgroundColor3 = colorVida(foto.Vida / foto.VidaMax)
	ponerBarra(barraTurbo, turbo, foto.TurboMax, "TURBO")
	-- Inmune tras despegar: el escudo parpadea.
	local inmune = foto.Inmune - (ahora - fotoEn)
	barraEscudo.Relleno.BackgroundTransparency = if inmune > 0 and math.floor(ahora * 6) % 2 == 0 then 0.6 else 0

	if foco then
		textoVelocidad.Text = `{math.floor(foco.AssemblyLinearVelocity.Magnitude + 0.5)} u/s`
	end

	if ahora - ultimoRadar >= INTERVALO_RADAR then
		ultimoRadar = ahora
		actualizarRadar(ahora)
	end
end

-- ===== API =====

--[[
	Muestra el panel. `raiz` es la parte principal de la nave del piloto (de ahí salen la velocidad y el radar).
]]
function Panel.Mostrar(raiz: BasePart)
	if gui == nil then
		gui = construir()
	end
	foco = raiz
	if gui then
		gui.Enabled = true
	end
	if conexion == nil then
		conexion = RunService.RenderStepped:Connect(paso)
	end
	if textoAyuda then
		local ayuda = textoAyuda
		ayuda.TextTransparency = 0
		task.delay(14, function()
			if ayuda.Parent then
				ayuda.TextTransparency = 1
				ayuda.TextStrokeTransparency = 1
			end
		end)
	end
end

function Panel.Ocultar()
	if conexion then
		conexion:Disconnect()
		conexion = nil
	end
	if gui then
		gui.Enabled = false
	end
	foco = nil
	foto = nil
end

-- Recibe una foto nueva del estado de la nave (EstadoNave).
function Panel.Actualizar(datos: any)
	foto = datos
	fotoEn = os.clock()
	if gui == nil then
		return
	end
	-- La bodega es el inventario del jugador: lo que lleva, sobre el límite que marca la mejora Carga.
	local misDatos = ServicioDatos.Obtener()
	local ocupado = if misDatos then Inventario.Volumen(misDatos.Inventario) else 0
	textoBodega.Text = `Bodega {math.floor(ocupado)}/{math.floor(datos.Capacidad)}`
	local partes = {}
	for _, id in Mejoras.Orden do
		table.insert(partes, `{Mejoras.Lista[id].Nombre} {datos.Niveles[id] or 0}`)
	end
	textoMejoras.Text = table.concat(partes, " · ")
end

-- Muestra un mensaje que se desvanece solo.
local avisoActual = 0
function Panel.Aviso(texto: string, color: Color3?)
	if gui == nil then
		return
	end
	avisoActual += 1
	local mio = avisoActual
	textoAviso.Text = texto
	textoAviso.TextColor3 = color or TEXTO
	textoAviso.TextTransparency = 0
	textoAviso.TextStrokeTransparency = 0.5
	task.delay(2.8, function()
		if avisoActual == mio and textoAviso.Parent then
			textoAviso.TextTransparency = 1
			textoAviso.TextStrokeTransparency = 1
		end
	end)
end

--[[
	Mensaje grande en el centro que sigue visible aunque el panel ya esté oculto (por ejemplo, "NAVE DESTRUIDA":
	el panel se apaga en cuanto la nave desaparece).
]]
function Panel.AvisoFinal(texto: string, color: Color3?)
	local pantalla = Instance.new("ScreenGui")
	pantalla.Name = "AvisoNave"
	pantalla.ResetOnSpawn = false
	pantalla.DisplayOrder = 30
	pantalla.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	local mensaje = etiqueta(
		pantalla,
		texto,
		UDim2.fromOffset(640, 60),
		UDim2.new(0.5, -320, 0.3, 0),
		40,
		color or ROJO,
		Enum.TextXAlignment.Center
	)
	mensaje.TextStrokeTransparency = 0.3
	task.delay(2.2, function()
		for paso = 1, 10 do
			mensaje.TextTransparency = paso / 10
			mensaje.TextStrokeTransparency = 0.3 + paso * 0.07
			task.wait(0.08)
		end
		pantalla:Destroy()
	end)
end

return Panel
