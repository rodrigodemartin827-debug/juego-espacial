--!strict
--[[
	Interfaz (Elección de bando): lo 2D de la pantalla de elección, encima de la escena 3D.

	  arriba       título y subtítulo
	  cada mitad   una zona invisible que recoge el ratón o el dedo, y el panel de su bando: nombre, dificultad, lema,
	               ventajas y punto débil (textos de Eleccion/Datos/Textos)
	  abajo        cómo se elige (ratón, táctil o mando), el aviso del cambio de pago y los mensajes de estado
	  al elegir    el nombre del bando estalla en el centro con su mensaje de bienvenida

	Con ratón, el panel de un bando se despliega al pasar por su mitad. En pantallas táctiles no hay "pasar por
	encima": los dos paneles se ven siempre (Config.Interfaz.InfoSiempreEnTactil), tocar una mitad la resalta y soltar
	el dedo sobre ella la elige.

	La CORTINA es una ScreenGui aparte, negra y por encima de todo, para los fundidos de entrada y salida.

	Todo escala con la pantalla (Eleccion/Encuadre): cada bloque lleva su UIScale (escala alrededor de su propio punto
	de anclaje, así nada se descoloca) y en móvil los paneles son más anchos.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Eleccion.Config)
local Encuadre = require(Shared.Eleccion.Encuadre)
local Textos = require(Shared.Eleccion.Datos.Textos)
local Utiles = require(script.Parent.Parent.VFX.Utiles)

local Interfaz = {}

export type Callbacks = {
	AlResaltar: (bando: string?) -> (),
	AlElegir: (bando: string) -> (),
}

type Panel = {
	Bando: string,
	Grupo: CanvasGroup,
	Detalle: Frame,
	Nombre: TextLabel,
	Trazo: UIStroke,
	Escala: UIScale,
}

local FUENTE_TITULO = Enum.Font.GothamBlack
local FUENTE_TEXTO = Enum.Font.GothamMedium
local FUENTE_FUERTE = Enum.Font.GothamBold

local pantalla: ScreenGui? = nil
local escalas: { UIScale } = {} -- las de los bloques fijos (cabecera, pie, estado, confirmación)
local escalaActual = 1
local paneles: { [string]: Panel } = {}
local estado: TextLabel? = nil
local ayuda: TextLabel? = nil
local conexiones: { RBXScriptConnection } = {}
local resaltado: string? = nil
local bloqueada = false
local tactil = false

local cortina: ScreenGui? = nil
local fondoCortina: Frame? = nil

-- ===== Utilidades =====

local function color(hex: string): Color3
	return Utiles.Hex(hex)
end

local function etiqueta(
	padre: Instance,
	texto: string,
	tamano: number,
	fuente: Enum.Font,
	colorTexto: Color3
): TextLabel
	local label = Instance.new("TextLabel")
	label.BackgroundTransparency = 1
	label.Text = texto
	label.TextSize = tamano
	label.Font = fuente
	label.TextColor3 = colorTexto
	label.TextWrapped = true
	label.AutomaticSize = Enum.AutomaticSize.Y
	label.Size = UDim2.fromScale(1, 0)
	label.Parent = padre
	return label
end

local function sombra(objeto: TextLabel, grosor: number?)
	local trazo = Instance.new("UIStroke")
	trazo.Color = Color3.new(0, 0, 0)
	trazo.Transparency = 0.35
	trazo.Thickness = grosor or 2
	trazo.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
	trazo.Parent = objeto
end

local function lista(padre: Instance, separacion: number, alineacion: Enum.HorizontalAlignment?)
	local disposicion = Instance.new("UIListLayout")
	disposicion.SortOrder = Enum.SortOrder.LayoutOrder
	disposicion.Padding = UDim.new(0, separacion)
	disposicion.HorizontalAlignment = alineacion or Enum.HorizontalAlignment.Center
	disposicion.Parent = padre
end

-- Da a un bloque su UIScale, que sigue el tamaño de la pantalla.
local function escalable(objeto: GuiObject): UIScale
	local escala = Instance.new("UIScale")
	escala.Scale = escalaActual
	escala.Parent = objeto
	table.insert(escalas, escala)
	return escala
end

local function esTactil(): boolean
	return UserInputService.TouchEnabled and not UserInputService.MouseEnabled
end

-- ===== Paneles de cada bando =====

local function crearPanel(padre: Instance, bando: string, lado: number): Panel
	local t = Textos.Bandos[bando]
	local principal = color(t.Color)

	-- CanvasGroup: se puede fundir el panel entero de una vez (GroupTransparency).
	local grupo = Instance.new("CanvasGroup")
	grupo.Name = `Panel_{bando}`
	grupo.AnchorPoint = Vector2.new(0.5, 1)
	grupo.Position = UDim2.fromScale(if lado == 1 then 0.25 else 0.75, 0.88)
	grupo.Size = UDim2.fromScale(0.3, 0)
	grupo.AutomaticSize = Enum.AutomaticSize.Y
	grupo.BackgroundColor3 = color(Config.Interfaz.Fondo)
	grupo.BackgroundTransparency = 0.3
	grupo.GroupTransparency = 0
	grupo.Parent = padre
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, 14)
	esquina.Parent = grupo
	local trazo = Instance.new("UIStroke")
	trazo.Color = principal
	trazo.Thickness = 2
	trazo.Transparency = 0.5
	trazo.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	trazo.Parent = grupo
	local degradado = Instance.new("UIGradient")
	degradado.Color = ColorSequence.new(color(t.ColorSuave), color(Config.Interfaz.Fondo))
	degradado.Rotation = 90
	degradado.Parent = grupo
	local relleno = Instance.new("UIPadding")
	relleno.PaddingTop = UDim.new(0, 14)
	relleno.PaddingBottom = UDim.new(0, 16)
	relleno.PaddingLeft = UDim.new(0, 18)
	relleno.PaddingRight = UDim.new(0, 18)
	relleno.Parent = grupo
	lista(grupo, 6)
	local escala = Instance.new("UIScale")
	escala.Parent = grupo

	local nombre = etiqueta(grupo, t.Nombre, 40, FUENTE_TITULO, principal)
	nombre.LayoutOrder = 1
	sombra(nombre, 3)

	local dificultad = etiqueta(grupo, string.upper(t.Dificultad), 13, FUENTE_FUERTE, color(Config.Interfaz.TextoSuave))
	dificultad.LayoutOrder = 2

	-- Lo que se despliega al resaltar: lema, ventajas y debilidad.
	local detalle = Instance.new("Frame")
	detalle.Name = "Detalle"
	detalle.BackgroundTransparency = 1
	detalle.Size = UDim2.fromScale(1, 0)
	detalle.AutomaticSize = Enum.AutomaticSize.Y
	detalle.LayoutOrder = 3
	detalle.Parent = grupo
	lista(detalle, 5, Enum.HorizontalAlignment.Left)

	local lema = etiqueta(detalle, t.Lema, 15, Enum.Font.GothamMedium, color(Config.Interfaz.TextoSuave))
	lema.TextXAlignment = Enum.TextXAlignment.Center
	lema.LayoutOrder = 1
	local separador = Instance.new("Frame")
	separador.BorderSizePixel = 0
	separador.BackgroundColor3 = principal
	separador.BackgroundTransparency = 0.6
	separador.Size = UDim2.new(1, 0, 0, 1)
	separador.LayoutOrder = 2
	separador.Parent = detalle
	for indice, ventaja in t.Ventajas do
		local linea = etiqueta(detalle, `✦  {ventaja}`, 17, FUENTE_FUERTE, color(Config.Interfaz.Texto))
		linea.TextXAlignment = Enum.TextXAlignment.Left
		linea.LayoutOrder = 2 + indice
	end
	local debilidad = etiqueta(detalle, `–  {t.Debilidad}`, 14, FUENTE_TEXTO, color(Config.Interfaz.TextoSuave))
	debilidad.TextXAlignment = Enum.TextXAlignment.Left
	debilidad.LayoutOrder = 10

	-- Indicación de que se elige con un clic.
	local elegir = etiqueta(detalle, `{Textos.Elegir} {t.Nombre}`, 15, FUENTE_TITULO, principal)
	elegir.LayoutOrder = 11

	return {
		Bando = bando,
		Grupo = grupo,
		Detalle = detalle,
		Nombre = nombre,
		Trazo = trazo,
		Escala = escala,
	}
end

-- Coloca y despliega cada panel según quién está resaltado y el tamaño de la pantalla.
local function actualizarPaneles(animar: boolean)
	local duracion = if animar then Config.Tiempos.Resaltado else 0
	local camara = workspace.CurrentCamera
	local tamano = if camara then camara.ViewportSize else Vector2.new(1280, 720)
	local disposicion = Encuadre.Disposicion(tamano.X, tamano.Y)
	escalaActual = disposicion.Escala
	for _, escala in escalas do
		escala.Scale = escalaActual
	end
	for _, panel in paneles do
		local activo = panel.Bando == resaltado
		local otroActivo = resaltado ~= nil and not activo
		-- En táctil la información se ve siempre; con ratón, solo la del lado resaltado.
		local verDetalle = activo or (tactil and Config.Interfaz.InfoSiempreEnTactil)
		panel.Detalle.Visible = verDetalle
		panel.Grupo.Size = UDim2.fromScale(disposicion.AnchoPanel / disposicion.Escala, 0)
		local factor = if activo then 1.06 else (if otroActivo then 0.94 else 1)
		Utiles.Tween(panel.Escala, duracion, { Scale = escalaActual * factor }, "Back")
		Utiles.Tween(panel.Grupo, duracion, { GroupTransparency = if otroActivo then 0.45 else 0 }, "Quad")
		Utiles.Tween(
			panel.Trazo,
			duracion,
			{ Transparency = if activo then 0 else 0.55, Thickness = if activo then 3 else 2 },
			"Quad"
		)
	end
end

-- ===== Zonas de entrada =====

local function crearZona(padre: Instance, bando: string, lado: number, callbacks: Callbacks)
	local zona = Instance.new("TextButton")
	zona.Name = `Zona_{bando}`
	zona.Text = ""
	zona.AutoButtonColor = false
	zona.BackgroundTransparency = 1
	zona.Selectable = false
	zona.Position = UDim2.fromScale(if lado == 1 then 0 else 0.5, 0)
	zona.Size = UDim2.fromScale(0.5, 1)
	zona.ZIndex = 0
	zona.Parent = padre

	table.insert(
		conexiones,
		zona.MouseEnter:Connect(function()
			if not bloqueada then
				callbacks.AlResaltar(bando)
			end
		end)
	)
	table.insert(
		conexiones,
		zona.MouseLeave:Connect(function()
			if not bloqueada and resaltado == bando and not tactil then
				callbacks.AlResaltar(nil)
			end
		end)
	)
	-- En táctil, poner el dedo resalta (por si el dispositivo no emite MouseEnter).
	table.insert(
		conexiones,
		zona.InputBegan:Connect(function(entrada: InputObject)
			if not bloqueada and entrada.UserInputType == Enum.UserInputType.Touch then
				callbacks.AlResaltar(bando)
			end
		end)
	)
	-- Un clic, o soltar el dedo sobre la misma mitad: se elige.
	table.insert(
		conexiones,
		zona.Activated:Connect(function()
			if not bloqueada then
				callbacks.AlElegir(bando)
			end
		end)
	)
end

-- ===== API: pantalla de elección =====

-- Monta la interfaz. `callbacks` recibe el resaltado (bando o nil) y la elección.
function Interfaz.Crear(callbacks: Callbacks)
	if pantalla ~= nil then
		return
	end
	tactil = esTactil()
	resaltado = nil
	bloqueada = false

	local gui = Instance.new("ScreenGui")
	gui.Name = "EleccionBando"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 50
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	pantalla = gui

	-- Las zonas ocupan toda la pantalla, por debajo del contenido (que no recoge entrada).
	for lado, bando in Config.Orden do
		crearZona(gui, bando, lado, callbacks)
	end

	local contenido = Instance.new("Frame")
	contenido.Name = "Contenido"
	contenido.BackgroundTransparency = 1
	contenido.Size = UDim2.fromScale(1, 1)
	contenido.Active = false
	contenido.ZIndex = 2
	contenido.Parent = gui

	-- Título y subtítulo.
	local cabecera = Instance.new("Frame")
	cabecera.BackgroundTransparency = 1
	cabecera.AnchorPoint = Vector2.new(0.5, 0)
	cabecera.Position = UDim2.fromScale(0.5, 0.045)
	cabecera.Size = UDim2.fromScale(0.9, 0)
	cabecera.AutomaticSize = Enum.AutomaticSize.Y
	cabecera.Parent = contenido
	escalable(cabecera)
	lista(cabecera, 2)
	local titulo = etiqueta(cabecera, Textos.Titulo, 52, FUENTE_TITULO, color(Config.Interfaz.Texto))
	titulo.LayoutOrder = 1
	sombra(titulo, 3)
	local brillo = Instance.new("UIGradient")
	brillo.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, color(Textos.Bandos[Config.Orden[1]].Color)),
		ColorSequenceKeypoint.new(0.5, Color3.new(1, 1, 1)),
		ColorSequenceKeypoint.new(1, color(Textos.Bandos[Config.Orden[2]].Color)),
	})
	brillo.Parent = titulo
	local subtitulo = etiqueta(cabecera, Textos.Subtitulo, 18, FUENTE_TEXTO, color(Config.Interfaz.TextoSuave))
	subtitulo.LayoutOrder = 2
	sombra(subtitulo, 1.5)

	for lado, bando in Config.Orden do
		paneles[bando] = crearPanel(contenido, bando, lado)
	end

	-- Ayuda y aviso abajo.
	local pie = Instance.new("Frame")
	pie.BackgroundTransparency = 1
	pie.AnchorPoint = Vector2.new(0.5, 1)
	pie.Position = UDim2.fromScale(0.5, 0.985)
	pie.Size = UDim2.fromScale(0.9, 0)
	pie.AutomaticSize = Enum.AutomaticSize.Y
	pie.Parent = contenido
	escalable(pie)
	lista(pie, 2)
	local textoAyuda = if tactil then Textos.AyudaTactil else Textos.AyudaRaton
	if UserInputService.GamepadEnabled then
		textoAyuda ..= `   ·   {Textos.AyudaMando}`
	end
	local ayudaLabel = etiqueta(pie, textoAyuda, 16, FUENTE_FUERTE, color(Config.Interfaz.Texto))
	ayudaLabel.LayoutOrder = 1
	sombra(ayudaLabel, 1.5)
	ayuda = ayudaLabel
	local aviso = etiqueta(pie, Textos.Aviso, 13, FUENTE_TEXTO, color(Config.Interfaz.TextoSuave))
	aviso.LayoutOrder = 2
	sombra(aviso, 1)

	-- Mensajes de estado (esperando al servidor, error) en el centro.
	local estadoLabel = etiqueta(contenido, "", 20, FUENTE_FUERTE, color(Config.Interfaz.Texto))
	estadoLabel.AnchorPoint = Vector2.new(0.5, 0.5)
	estadoLabel.Position = UDim2.fromScale(0.5, 0.2)
	estadoLabel.Size = UDim2.fromScale(0.6, 0)
	estadoLabel.TextTransparency = 1
	escalable(estadoLabel)
	sombra(estadoLabel, 2)
	estado = estadoLabel

	actualizarPaneles(false)
	local camara = workspace.CurrentCamera
	if camara then
		table.insert(
			conexiones,
			camara:GetPropertyChangedSignal("ViewportSize"):Connect(function()
				actualizarPaneles(false)
			end)
		)
	end
	table.insert(
		conexiones,
		UserInputService.LastInputTypeChanged:Connect(function()
			local ahora = esTactil()
			if ahora ~= tactil then
				tactil = ahora
				if ayuda then
					ayuda.Text = if tactil then Textos.AyudaTactil else Textos.AyudaRaton
				end
				actualizarPaneles(true)
			end
		end)
	)

	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
end

-- Resalta un bando (o ninguno) en los paneles.
function Interfaz.Resaltar(bando: string?)
	if resaltado == bando then
		return
	end
	resaltado = bando
	actualizarPaneles(true)
end

-- Mientras se espera al servidor, la interfaz no responde y muestra un mensaje.
function Interfaz.Esperando(activo: boolean)
	bloqueada = activo
	local label = estado
	if label then
		label.Text = Textos.Esperando
		Utiles.Tween(label, 0.25, { TextTransparency = if activo then 0 else 1 }, "Quad")
	end
end

-- El servidor no respondió: se vuelve a poder elegir y se avisa.
function Interfaz.Error()
	bloqueada = false
	local label = estado
	if label then
		label.Text = Textos.ErrorConfirmacion
		label.TextColor3 = color(Textos.Bandos.Monstruos.Color)
		label.TextTransparency = 0
		task.delay(3.5, function()
			if label.Parent ~= nil and label.Text == Textos.ErrorConfirmacion then
				Utiles.Tween(label, 0.4, { TextTransparency = 1 }, "Quad")
			end
		end)
	end
end

--[[
	El servidor confirmó: los paneles se van y el nombre del bando estalla en el centro (sale enorme y se asienta
	con un rebote), con su mensaje de bienvenida debajo.
]]
function Interfaz.Confirmar(bando: string)
	bloqueada = true
	resaltado = bando
	local gui = pantalla
	local t = Textos.Bandos[bando]
	if gui == nil or t == nil then
		return
	end
	local contenido = gui:FindFirstChild("Contenido")
	if contenido == nil then
		return
	end
	for _, panel in paneles do
		Utiles.Tween(panel.Grupo, 0.25, { GroupTransparency = 1 }, "Quad")
	end
	for _, hijo in contenido:GetChildren() do
		if hijo:IsA("Frame") then
			for _, texto in hijo:GetDescendants() do
				if texto:IsA("TextLabel") then
					Utiles.Tween(texto, 0.3, { TextTransparency = 1 }, "Quad")
				end
			end
		end
	end
	if estado then
		estado.TextTransparency = 1
	end

	local bloque = Instance.new("Frame")
	bloque.Name = "Confirmacion"
	bloque.BackgroundTransparency = 1
	bloque.AnchorPoint = Vector2.new(0.5, 0.5)
	bloque.Position = UDim2.fromScale(0.5, 0.42)
	bloque.Size = UDim2.fromScale(0.9, 0)
	bloque.AutomaticSize = Enum.AutomaticSize.Y
	bloque.Parent = contenido
	lista(bloque, 4)
	local escala = escalable(bloque)
	escala.Scale = escalaActual * 2.4

	local nombre = etiqueta(bloque, t.Nombre, 72, FUENTE_TITULO, color(t.Color))
	nombre.TextTransparency = 1
	sombra(nombre, 4)
	local mensaje = etiqueta(bloque, t.Confirmacion, 22, FUENTE_FUERTE, color(Config.Interfaz.Texto))
	mensaje.TextTransparency = 1
	mensaje.LayoutOrder = 2
	sombra(mensaje, 2)

	-- Impacto: el nombre entra de golpe (grande -> su tamaño, con rebote) y el mensaje aparece después.
	Utiles.Tween(escala, 0.45, { Scale = escalaActual }, "Back")
	Utiles.Tween(nombre, 0.12, { TextTransparency = 0 }, "Quad")
	task.delay(0.35, function()
		if mensaje.Parent ~= nil then
			Utiles.Tween(mensaje, 0.5, { TextTransparency = 0 }, "Quad")
		end
	end)
end

-- Quita la interfaz.
function Interfaz.Destruir()
	for _, conexion in conexiones do
		conexion:Disconnect()
	end
	table.clear(conexiones)
	table.clear(paneles)
	table.clear(escalas)
	if pantalla then
		pantalla:Destroy()
		pantalla = nil
	end
	estado = nil
	ayuda = nil
	resaltado = nil
end

-- ===== API: cortina negra (fundidos) =====

-- Pone la cortina negra por encima de todo, ya opaca (al entrar al juego, mientras llegan los datos).
function Interfaz.CrearCortina()
	if cortina ~= nil then
		return
	end
	local gui = Instance.new("ScreenGui")
	gui.Name = "EleccionCortina"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 100
	local fondo = Instance.new("Frame")
	fondo.BorderSizePixel = 0
	fondo.BackgroundColor3 = Color3.new(0, 0, 0)
	fondo.BackgroundTransparency = 0
	fondo.Size = UDim2.fromScale(1, 1)
	fondo.Active = false
	fondo.Parent = gui
	cortina = gui
	fondoCortina = fondo
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
end

-- Funde la cortina hasta `opacidad` (1 = negro, 0 = transparente) en `segundos`. Espera a que termine.
function Interfaz.Fundir(opacidad: number, segundos: number)
	Interfaz.CrearCortina()
	local fondo = fondoCortina
	if fondo == nil then
		return
	end
	local tween = Utiles.Tween(fondo, segundos, { BackgroundTransparency = 1 - opacidad }, "Sine")
	if segundos > 0 then
		tween.Completed:Wait()
	end
end

-- Quita la cortina (sin fundido).
function Interfaz.QuitarCortina()
	if cortina then
		cortina:Destroy()
		cortina = nil
		fondoCortina = nil
	end
end

return Interfaz
