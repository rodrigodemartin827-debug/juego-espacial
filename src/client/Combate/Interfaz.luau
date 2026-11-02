--!strict
--[[
	Interfaz (combate): barra de vida, barra de energía y botones de habilidades con su cooldown.

	Todo se construye por código (sin assets), con colores de Datos/Paleta, y se adapta al dispositivo:
	  - Ordenador: los botones van en una fila abajo, en el centro, con la tecla de cada uno.
	  - Móvil: los botones son grandes y van en la esquina inferior derecha (zona del pulgar), y las barras
	    suben arriba para no taparse con los controles.

	La vida es la del Humanoid del personaje; la energía y los cooldowns los envía el servidor
	(EstadoCombate) y la interfaz los hace avanzar sola entre un mensaje y otro (la energía se regenera a un
	ritmo conocido), así no hace falta recibir datos cada fotograma.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Combate = ReplicatedStorage:WaitForChild("Shared").Combate
local Config = require(Combate.Config)
local Paleta = require(Combate.Datos.Paleta)
local Poderes = require(Combate.Datos.Poderes)
local Calidad = require(script.Parent.Parent.VFX.Calidad)
local Utiles = require(script.Parent.Parent.VFX.Utiles)

local Interfaz = {}

type Casilla = {
	Id: string,
	Boton: TextButton,
	Cubierta: Frame,
	Tiempo: TextLabel,
	Coste: number,
	UltimoTexto: string,
}

local FONDO = Color3.fromRGB(12, 14, 26)
local TEXTO = Color3.fromRGB(235, 240, 255)

local casillas: { Casilla } = {}
local finCooldown: { [string]: number } = {}
local duracionCooldown: { [string]: number } = {}

-- Estado de energía enviado por el servidor.
local energia = {
	Valor = Config.EnergiaMaxima,
	Maxima = Config.EnergiaMaxima,
	Regeneracion = Config.EnergiaPorSegundo,
	Desde = os.clock(),
}

-- Se rellenan en Iniciar().
local barraVida: Frame = nil :: any
local textoVida: TextLabel = nil :: any
local barraEnergia: Frame = nil :: any
local textoEnergia: TextLabel = nil :: any
local humanoidActual: Humanoid? = nil
local pantalla: ScreenGui? = nil
local iniciada = false

-- ===== Construcción =====

local function redondear(objeto: GuiObject, radio: number?)
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, radio or 8)
	esquina.Parent = objeto
end

local function borde(objeto: GuiObject, color: Color3, grosor: number?)
	local trazo = Instance.new("UIStroke")
	trazo.Color = color
	trazo.Thickness = grosor or 2
	trazo.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	trazo.Parent = objeto
end

local function etiqueta(
	padre: Instance,
	texto: string,
	tamano: UDim2,
	posicion: UDim2,
	escalaFuente: boolean?
): TextLabel
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Size = tamano
	label.Position = posicion
	label.Font = Enum.Font.GothamBold
	label.TextColor3 = TEXTO
	label.Text = texto
	label.TextScaled = escalaFuente ~= false
	label.Parent = padre
	local trazo = Instance.new("UIStroke")
	trazo.Thickness = 1.5
	trazo.Color = Color3.fromRGB(0, 0, 0)
	trazo.Transparency = 0.3
	trazo.Parent = label
	return label
end

-- Barra con fondo, relleno y texto. Devuelve el relleno y el texto.
local function crearBarra(padre: Instance, tamano: UDim2, posicion: UDim2, color: Color3): (Frame, TextLabel)
	local fondo = Instance.new("Frame")
	fondo.AnchorPoint = Vector2.new(0.5, 0)
	fondo.Size = tamano
	fondo.Position = posicion
	fondo.BackgroundColor3 = FONDO
	fondo.BackgroundTransparency = 0.2
	fondo.BorderSizePixel = 0
	fondo.Parent = padre
	redondear(fondo, 7)
	borde(fondo, Color3.fromRGB(255, 255, 255), 1.5)

	local relleno = Instance.new("Frame")
	relleno.Size = UDim2.fromScale(1, 1)
	relleno.BackgroundColor3 = color
	relleno.BorderSizePixel = 0
	relleno.Parent = fondo
	redondear(relleno, 7)

	local texto = etiqueta(fondo, "", UDim2.fromScale(1, 1), UDim2.fromScale(0, 0))
	texto.TextScaled = false
	texto.TextSize = 13
	texto.ZIndex = 3
	return relleno, texto
end

-- Botón de una habilidad.
local function crearCasilla(padre: Instance, id: string, tamano: number, posicion: UDim2, anclaje: Vector2): Casilla
	local hab = Poderes.Presentacion(id) :: Poderes.Habilidad
	local colores = Paleta[hab.Poder]

	local boton = Instance.new("TextButton")
	boton.Name = id
	boton.AutoButtonColor = false
	boton.Text = ""
	boton.Size = UDim2.fromOffset(tamano, tamano)
	boton.Position = posicion
	boton.AnchorPoint = anclaje
	boton.BackgroundColor3 = Utiles.Hex(colores.Oscuro):Lerp(Utiles.Hex(colores.Principal), 0.18)
	boton.BorderSizePixel = 0
	boton.ClipsDescendants = true
	boton.Parent = padre
	redondear(boton, 10)
	borde(boton, Utiles.Hex(colores.Principal), 2)

	-- Nombre de la habilidad (el combo muestra "Combo").
	local nombre = if id == Poderes.IdCombo then "Combo" else hab.Nombre
	local textoNombre = etiqueta(boton, nombre, UDim2.new(1, -6, 0.38, 0), UDim2.new(0, 3, 0.4, 0))
	textoNombre.TextWrapped = true
	textoNombre.TextSize = 11

	-- Tecla.
	local tecla = if hab.Tecla == "Click" then "Click" else hab.Tecla
	local textoTecla =
		etiqueta(boton, if Calidad.EsMovil then "" else tecla, UDim2.new(0.5, 0, 0.3, 0), UDim2.new(0, 4, 0, 2))
	textoTecla.TextXAlignment = Enum.TextXAlignment.Left
	textoTecla.TextColor3 = Utiles.Hex(colores.Nucleo)

	-- Cubierta de cooldown: oscurece la casilla y baja a medida que se recupera.
	local cubierta = Instance.new("Frame")
	cubierta.AnchorPoint = Vector2.new(0, 1)
	cubierta.Position = UDim2.fromScale(0, 1)
	cubierta.Size = UDim2.fromScale(1, 0)
	cubierta.BackgroundColor3 = Color3.fromRGB(0, 0, 0)
	cubierta.BackgroundTransparency = 0.35
	cubierta.BorderSizePixel = 0
	cubierta.ZIndex = 4
	cubierta.Parent = boton

	local tiempo = etiqueta(boton, "", UDim2.fromScale(1, 0.5), UDim2.fromScale(0, 0.25))
	tiempo.ZIndex = 5
	tiempo.Font = Enum.Font.GothamBlack

	return { Id = id, Boton = boton, Cubierta = cubierta, Tiempo = tiempo, Coste = hab.Energia, UltimoTexto = "" }
end

-- ===== Vida =====

local function actualizarVida()
	local humanoid = humanoidActual
	if humanoid == nil then
		return
	end
	local maxima = math.max(humanoid.MaxHealth, 1)
	local proporcion = math.clamp(humanoid.Health / maxima, 0, 1)
	barraVida.Size = UDim2.fromScale(proporcion, 1)
	barraVida.BackgroundColor3 = Color3.fromRGB(235, 70, 80):Lerp(Color3.fromRGB(80, 220, 120), proporcion)
	textoVida.Text = `{math.ceil(humanoid.Health)} / {math.ceil(maxima)}`
end

local function seguirPersonaje(personaje: Model)
	local humanoid = personaje:WaitForChild("Humanoid", 10) :: Humanoid?
	if humanoid == nil then
		return
	end
	humanoidActual = humanoid
	humanoid.HealthChanged:Connect(actualizarVida)
	humanoid:GetPropertyChangedSignal("MaxHealth"):Connect(actualizarVida)
	actualizarVida()
end

-- ===== Actualización por fotograma =====

local function actualizar()
	local ahora = os.clock()

	-- Energía: avanza sola entre mensajes del servidor.
	local valor = math.min(energia.Maxima, energia.Valor + energia.Regeneracion * (ahora - energia.Desde))
	barraEnergia.Size = UDim2.fromScale(math.clamp(valor / energia.Maxima, 0, 1), 1)
	textoEnergia.Text = `{math.floor(valor)} / {energia.Maxima}`

	for _, casilla in casillas do
		local fin = finCooldown[casilla.Id]
		local restante = if fin then math.max(0, fin - ahora) else 0
		local total = duracionCooldown[casilla.Id] or 1
		casilla.Cubierta.Size = UDim2.fromScale(1, if restante > 0 then math.clamp(restante / total, 0, 1) else 0)

		local texto = if restante > 0
			then (if restante >= 10 then tostring(math.ceil(restante)) else string.format("%.1f", restante))
			else ""
		if texto ~= casilla.UltimoTexto then
			casilla.UltimoTexto = texto
			casilla.Tiempo.Text = texto
		end

		-- Sin energía suficiente, la casilla se ve apagada.
		casilla.Boton.BackgroundTransparency = if valor + 1e-6 < casilla.Coste then 0.55 else 0
	end
end

-- ===== API =====

--[[
	Recibe el estado de combate del servidor: energía y cooldowns que siguen en marcha
	(`{ Energia, EnergiaMax, Regeneracion, Cooldowns = { [id] = segundosRestantes } }`).
]]
function Interfaz.PonerEstado(estado: any)
	if type(estado) ~= "table" then
		return
	end
	energia.Valor = tonumber(estado.Energia) or energia.Valor
	energia.Maxima = tonumber(estado.EnergiaMax) or energia.Maxima
	energia.Regeneracion = tonumber(estado.Regeneracion) or energia.Regeneracion
	energia.Desde = os.clock()

	local ahora = os.clock()
	local nuevos: { [string]: number } = {}
	if type(estado.Cooldowns) == "table" then
		for id, restante in estado.Cooldowns do
			if type(id) == "string" and type(restante) == "number" then
				nuevos[id] = restante
			end
		end
	end
	for _, casilla in casillas do
		local restante = nuevos[casilla.Id]
		if restante and restante > 0 then
			finCooldown[casilla.Id] = ahora + restante
			-- La duración total: la mayor vista mientras sigue activo (un mensaje tardío trae un resto menor).
			local previa = duracionCooldown[casilla.Id]
			local sigueActivo = previa ~= nil and finCooldown[casilla.Id] ~= nil and previa >= restante
			duracionCooldown[casilla.Id] = if sigueActivo then previa else restante
		else
			finCooldown[casilla.Id] = nil
			duracionCooldown[casilla.Id] = nil
		end
	end
end

-- Muestra u oculta toda la interfaz de combate (mientras se pilota una nave no hace falta).
function Interfaz.Mostrar(visible: boolean)
	if pantalla then
		pantalla.Enabled = visible
	end
end

-- ¿Está la habilidad en cooldown según lo último que dijo el servidor? (para no pedir en vano)
function Interfaz.EnCooldown(id: string): boolean
	local fin = finCooldown[id]
	return fin ~= nil and os.clock() < fin
end

--[[
	Crea la interfaz. `alPulsar(id)` se llama cuando el jugador toca un botón de habilidad.
]]
function Interfaz.Iniciar(alPulsar: (id: string) -> ())
	if iniciada then
		return
	end
	iniciada = true

	local jugador = Players.LocalPlayer
	local gui = Instance.new("ScreenGui")
	gui.Name = "InterfazCombate"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = false
	gui.DisplayOrder = 10
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

	local movil = Calidad.EsMovil

	-- Barras. En ordenador, abajo y centradas; en móvil, arriba para no estorbar al pulgar.
	local contenedor = Instance.new("Frame")
	contenedor.BackgroundTransparency = 1
	contenedor.AnchorPoint = Vector2.new(0.5, if movil then 0 else 1)
	contenedor.Position = if movil then UDim2.new(0.5, 0, 0, 8) else UDim2.new(0.5, 0, 1, -14)
	contenedor.Size = UDim2.fromOffset(if movil then 260 else 380, 50)
	contenedor.Parent = gui

	barraVida, textoVida =
		crearBarra(contenedor, UDim2.new(1, 0, 0, 22), UDim2.new(0.5, 0, 0, 0), Color3.fromRGB(80, 220, 120))
	barraEnergia, textoEnergia =
		crearBarra(contenedor, UDim2.new(1, 0, 0, 15), UDim2.new(0.5, 0, 0, 28), Utiles.Hex(Paleta.Rayo.Principal))

	-- Botones de habilidades.
	local tamano = if movil then 62 else 60
	local separacion = 8
	local ids = Poderes.Orden

	if movil then
		-- Esquina inferior derecha: el combo grande a la derecha; Rayo y Gravedad en dos filas a su izquierda.
		local combo = crearCasilla(gui, Poderes.IdCombo, 92, UDim2.new(1, -14, 1, -18), Vector2.new(1, 1))
		table.insert(casillas, combo)
		local fila = { Rayo = 0, Gravedad = 1 }
		local columna = { Rayo = 0, Gravedad = 0 }
		for _, id in ids do
			local hab = Poderes.Presentacion(id) :: Poderes.Habilidad
			if id ~= Poderes.IdCombo then
				local f = fila[hab.Poder]
				local c = columna[hab.Poder]
				columna[hab.Poder] += 1
				local x = -(14 + 92 + separacion) - (2 - c) * (tamano + separacion)
				local y = -18 - f * (tamano + separacion)
				table.insert(casillas, crearCasilla(gui, id, tamano, UDim2.new(1, x, 1, y), Vector2.new(1, 1)))
			end
		end
	else
		-- Fila centrada sobre las barras: Combo, Rayo (3), Gravedad (3).
		local total = #ids * tamano + (#ids - 1) * separacion
		for indice, id in ids do
			local x = -total / 2 + (indice - 1) * (tamano + separacion)
			table.insert(casillas, crearCasilla(gui, id, tamano, UDim2.new(0.5, x, 1, -78), Vector2.new(0, 1)))
		end
	end

	for _, casilla in casillas do
		casilla.Boton.Activated:Connect(function()
			alPulsar(casilla.Id)
		end)
	end

	gui.Parent = jugador:WaitForChild("PlayerGui")
	pantalla = gui

	-- Vida: sigue al personaje actual y a los siguientes.
	if jugador.Character then
		task.spawn(seguirPersonaje, jugador.Character)
	end
	jugador.CharacterAdded:Connect(seguirPersonaje)

	RunService.RenderStepped:Connect(actualizar)
	actualizar()
end

return Interfaz
