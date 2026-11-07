--!strict
--[[
	Pantalla del editor de personaje humano (cliente): la interfaz. El personaje 3D está detrás (Editor/Estudio).

	Disposición ancha (ordenador):
	  · Izquierda: fila de colores de piel (de clara a oscura) y, debajo, las categorías (Personaje/Apariencia
	    .Categorias), cada una con flechas ‹ › y su nombre con el número de la opción («CABELLO 3») y cuál es.
	  · Centro: el personaje (se gira arrastrando).
	  · Derecha: selector de color (rueda de tono y saturación + barra de brillo) con un botón que cambia lo que se
	    colorea (pelo, chaqueta, pantalón o detalles) y unas muestras rápidas.
	  · Abajo: ATRÁS, ALEATORIO y CONTINUAR.
	Disposición estrecha (móvil o ventana pequeña): las categorías van abajo en horizontal (se desliza con el dedo),
	la piel arriba y el color a la derecha en pequeño; el personaje queda a la izquierda. Botones de al menos 44 px.

	Cada cambio llama a AlCambiar(apariencia, tipo) al momento: tipo "Pieza" (cambia una pieza: se rehace) o "Color"
	(solo colores: se repinta, que es más rápido mientras se arrastra por la rueda).

	Mientras está abierta: personaje quieto (controles desactivados) y la interfaz del juego oculta.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Personaje.ConfigEditor)

-- Lo propio del bando (Personaje/PerfilEditor): se pone al abrir.
local Apariencia: any = nil
local Datos: any = nil
local perfilActual: any = nil

local Pantalla = {}

export type Disposicion = "Ancha" | "Estrecha"
export type Opciones = {
	Perfil: any, -- Personaje/PerfilEditor del bando
	Inicial: any,
	AlCambiar: (any, string) -> (),
	AlDisponer: (Disposicion) -> (),
	AlAtras: () -> (),
	AlAleatorio: () -> any,
	UsarAvatar: boolean, -- si empieza usando su avatar de Roblox (solo Humanos)
	AlAvatar: (boolean) -> (), -- pide pasar al avatar (true) o a las piezas del juego (false)
	AlTerminar: (any, boolean) -> (),
}

local NOMBRE_GUI = "EditorPersonaje"

local jugador = Players.LocalPlayer
local gui: ScreenGui? = nil
local ocultas: { [ScreenGui]: boolean } = {}
-- Interfaz de Roblox que se quita mientras el editor está abierto. PROBADO EN STUDIO: la ventana del chat (aunque no
-- se vea) se quedaba los clics de la esquina de arriba a la izquierda, donde están la piel y las primeras categorías.
local CORE_OCULTOS =
	{ Enum.CoreGuiType.Chat, Enum.CoreGuiType.Backpack, Enum.CoreGuiType.PlayerList, Enum.CoreGuiType.EmotesMenu }
local coreAntes: { [Enum.CoreGuiType]: boolean } = {}
local chatAntes: { Ventana: boolean?, Barra: boolean? } = {}
local conexiones: { RBXScriptConnection } = {}

local C = Config.Colores
local I = Config.Interfaz

local function color(hex: string): Color3
	return Color3.fromHex(hex)
end

local function fuente(familia: string, peso: Enum.FontWeight?): Font
	return Font.new(familia, peso or Enum.FontWeight.Bold)
end

-- ===== Bloqueo (quieto y sin la interfaz del juego) =====

local function controles(): any
	local ok, c = pcall(function()
		local modulo =
			require(jugador:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: ModuleScript) :: any
		return modulo:GetControls()
	end)
	return if ok then c else nil
end

local function bloquear()
	local c = controles()
	if c then
		c:Disable()
	end
	for _, g in jugador:WaitForChild("PlayerGui"):GetChildren() do
		if g:IsA("ScreenGui") and g.Name ~= NOMBRE_GUI and g.Name ~= "EleccionCortina" and g.Enabled then
			ocultas[g] = true
			g.Enabled = false
		end
	end
	for _, tipo in CORE_OCULTOS do
		pcall(function()
			coreAntes[tipo] = StarterGui:GetCoreGuiEnabled(tipo)
			StarterGui:SetCoreGuiEnabled(tipo, false)
		end)
	end
	pcall(function()
		local TextChatService = game:GetService("TextChatService")
		chatAntes.Ventana = TextChatService.ChatWindowConfiguration.Enabled
		chatAntes.Barra = TextChatService.ChatInputBarConfiguration.Enabled
		TextChatService.ChatWindowConfiguration.Enabled = false
		TextChatService.ChatInputBarConfiguration.Enabled = false
	end)
end

local function desbloquear()
	for g in ocultas do
		if g.Parent then
			g.Enabled = true
		end
	end
	table.clear(ocultas)
	local c = controles()
	if c then
		c:Enable()
	end
	for tipo, antes in coreAntes do
		pcall(function()
			StarterGui:SetCoreGuiEnabled(tipo, antes)
		end)
	end
	table.clear(coreAntes)
	pcall(function()
		local TextChatService = game:GetService("TextChatService")
		if chatAntes.Ventana ~= nil then
			TextChatService.ChatWindowConfiguration.Enabled = chatAntes.Ventana
		end
		if chatAntes.Barra ~= nil then
			TextChatService.ChatInputBarConfiguration.Enabled = chatAntes.Barra
		end
	end)
	table.clear(chatAntes)
end

-- ===== Piezas de interfaz (estilo: metal oscuro, bordes cian, esquinas redondeadas) =====

local function crear(clase: string, props: { [string]: any }, padre: Instance?): any
	local o = Instance.new(clase)
	for k, v in props do
		(o :: any)[k] = v
	end
	if padre then
		o.Parent = padre
	end
	return o
end

local function esquina(o: GuiObject, radio: number)
	crear("UICorner", { CornerRadius = UDim.new(0, radio) }, o)
end

local function borde(o: GuiObject, hex: string, transparencia: number, grosor: number?): UIStroke
	return crear("UIStroke", {
		Color = color(hex),
		Transparency = transparencia,
		Thickness = grosor or 1,
		ApplyStrokeMode = Enum.ApplyStrokeMode.Border,
	}, o)
end

-- Panel de metal: degradado vertical, borde fino y una línea de luz cian arriba.
local function panel(padre: Instance, nombre: string): Frame
	local f = crear("Frame", {
		Name = nombre,
		BackgroundColor3 = Color3.new(1, 1, 1),
		BorderSizePixel = 0,
		BackgroundTransparency = 0.06,
	}, padre)
	esquina(f, 12)
	borde(f, C.Borde, 0.2, 1)
	crear("UIGradient", {
		Rotation = 90,
		Color = ColorSequence.new(color(C.PanelClaro), color(C.Panel)),
	}, f)
	local luz = crear("Frame", {
		Name = "Luz",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.fromScale(0.5, 0),
		Size = UDim2.new(0.55, 0, 0, 2),
		BackgroundColor3 = color(C.Cian),
		BorderSizePixel = 0,
		ZIndex = 3,
	}, f)
	crear("UIGradient", {
		Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1),
			NumberSequenceKeypoint.new(0.5, 0),
			NumberSequenceKeypoint.new(1, 1),
		}),
	}, luz)
	return f
end

local function etiqueta(padre: Instance, props: { [string]: any }): TextLabel
	local t = crear("TextLabel", {
		BackgroundTransparency = 1,
		TextColor3 = color(C.Texto),
		FontFace = fuente(Config.Fuentes.Texto),
		TextSize = 16,
		TextXAlignment = Enum.TextXAlignment.Left,
	}, padre)
	for k, v in props do
		(t :: any)[k] = v
	end
	return t
end

-- Botón con reacción: se ilumina el borde al pasar y se hunde un poco al pulsar.
local function boton(padre: Instance, props: { [string]: any }, principal: boolean?): TextButton
	local b = crear("TextButton", {
		AutoButtonColor = false,
		BackgroundColor3 = color(if principal then C.Cian else C.Metal),
		TextColor3 = color(if principal then "#06121A" else C.Texto),
		FontFace = fuente(Config.Fuentes.Titulo, Enum.FontWeight.Regular),
		TextSize = 18,
		BorderSizePixel = 0,
	}, padre)
	for k, v in props do
		(b :: any)[k] = v
	end
	esquina(b, 10)
	local trazo = borde(b, if principal then "#B8F6FF" else C.Borde, if principal then 0.2 else 0.1, 1.5)
	local escala = crear("UIScale", { Scale = 1 }, b)
	local rapido = TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	b.MouseEnter:Connect(function()
		TweenService:Create(trazo, rapido, { Color = color(C.Cian), Transparency = 0 }):Play()
	end)
	b.MouseLeave:Connect(function()
		TweenService:Create(trazo, rapido, {
			Color = color(if principal then "#B8F6FF" else C.Borde),
			Transparency = if principal then 0.2 else 0.1,
		}):Play()
		TweenService:Create(escala, rapido, { Scale = 1 }):Play()
	end)
	b.MouseButton1Down:Connect(function()
		TweenService:Create(escala, rapido, { Scale = 0.95 }):Play()
	end)
	b.MouseButton1Up:Connect(function()
		TweenService:Create(escala, TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
			Scale = 1,
		}):Play()
	end)
	return b
end

-- ===== Estado =====

local actual: { [string]: any } = {}
local op: Opciones? = nil
local objetivo = 1 -- índice en Datos.ObjetivosColor
local hsv = { 0, 0, 1 }
local disposicion: Disposicion = "Ancha"
local modoAvatar = false

-- Referencias de la interfaz que se actualizan.
local ui: { [string]: any } = {}

local function cambiar(tipo: string)
	local o = op
	if o then
		o.AlCambiar(table.clone(actual) :: any, tipo)
	end
end

-- ===== Piel =====

local function refrescarPiel()
	for id, muestra in ui.Pieles or {} do
		local sel = actual.Piel == id
		muestra.Seleccion.Transparency = if sel then 0 else 1
		muestra.Escala.Scale = if sel then 1.12 else 1
	end
end

local function crearPieles(padre: Instance)
	ui.Pieles = {}
	local fila = crear("Frame", { Name = "Pieles", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, padre)
	crear("UIListLayout", {
		FillDirection = Enum.FillDirection.Horizontal,
		HorizontalAlignment = Enum.HorizontalAlignment.Center,
		VerticalAlignment = Enum.VerticalAlignment.Center,
		Padding = UDim.new(0, 4),
		SortOrder = Enum.SortOrder.LayoutOrder,
	}, fila)
	for i, piel in Datos.Pieles do
		local b = crear("TextButton", {
			Name = piel.Id,
			LayoutOrder = i,
			Text = "",
			AutoButtonColor = false,
			BackgroundColor3 = color(piel.Hex),
			Size = UDim2.fromOffset(26, 26),
			BorderSizePixel = 0,
		}, fila)
		esquina(b, 13)
		borde(b, "#000000", 0.6, 1)
		local sel = crear("UIStroke", {
			Color = color(C.Cian),
			Thickness = 2.5,
			Transparency = 1,
			ApplyStrokeMode = Enum.ApplyStrokeMode.Border,
		}, b)
		local escala = crear("UIScale", { Scale = 1 }, b)
		b.MouseButton1Click:Connect(function()
			if actual.Piel ~= piel.Id then
				actual.Piel = piel.Id
				refrescarPiel()
				cambiar("Color")
			end
		end)
		ui.Pieles[piel.Id] = { Seleccion = sel, Escala = escala, Boton = b }
	end
	refrescarPiel()
end

-- ===== Categorías =====

local function refrescarCategorias()
	for campo, fila in ui.Categorias or {} do
		local i = Apariencia.Indice(campo, actual[campo]) or 1
		local opcion = Apariencia.Buscar(campo, actual[campo])
		fila.Numero.Text = tostring(i)
		local texto = if opcion then opcion.Nombre else ""
		-- Nota propia del bando (por ejemplo, un tatuaje tapado por la manga).
		local nota = if perfilActual and perfilActual.Nota then perfilActual.Nota(actual, campo) else nil
		if nota then
			texto ..= " " .. nota
		end
		fila.Opcion.Text = texto
	end
end

local function crearCategorias(padre: Instance)
	ui.Categorias = {}
	local cont = crear("ScrollingFrame", {
		Name = "Categorias",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		ScrollBarThickness = 0,
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.XY,
		ScrollingDirection = Enum.ScrollingDirection.Y,
		Size = UDim2.fromScale(1, 1),
	}, padre)
	ui.ListaCategorias = crear("UIListLayout", {
		Padding = UDim.new(0, 6),
		SortOrder = Enum.SortOrder.LayoutOrder,
		HorizontalAlignment = Enum.HorizontalAlignment.Center,
	}, cont)
	ui.ContCategorias = cont
	for orden, cat in Apariencia.Categorias do
		local fila = crear("Frame", {
			Name = cat.Campo,
			LayoutOrder = orden,
			BackgroundColor3 = color(C.Fondo),
			BackgroundTransparency = 0.35,
			BorderSizePixel = 0,
		}, cont)
		esquina(fila, 10)
		borde(fila, C.Borde, 0.45, 1)
		local flechas = {}
		local function flecha(texto: string, lado: number, paso: number)
			local b = boton(fila, {
				Name = if paso < 0 then "Anterior" else "Siguiente",
				Text = texto,
				TextSize = 26,
				FontFace = fuente(Config.Fuentes.Texto),
				AnchorPoint = Vector2.new(lado, 0.5),
				Position = UDim2.new(lado, if lado == 0 then 4 else -4, 0.5, 0),
				Size = UDim2.new(0, 44, 1, -8),
			})
			b.MouseButton1Click:Connect(function()
				actual[cat.Campo] = Apariencia.Mover(cat.Campo, actual[cat.Campo], paso)
				refrescarCategorias()
				cambiar("Pieza")
			end)
			table.insert(flechas, b)
		end
		flecha("‹", 0, -1)
		flecha("›", 1, 1)
		local nombre = etiqueta(fila, {
			Name = "Nombre",
			Text = string.upper(cat.Nombre),
			FontFace = fuente(Config.Fuentes.Titulo, Enum.FontWeight.Regular),
			TextSize = 13,
			TextXAlignment = Enum.TextXAlignment.Center,
			AnchorPoint = Vector2.new(0.5, 0),
			Position = UDim2.new(0.5, -9, 0, 5),
			Size = UDim2.new(1, -120, 0, 18),
		})
		local numero = etiqueta(fila, {
			Name = "Numero",
			Text = "1",
			FontFace = fuente(Config.Fuentes.Titulo, Enum.FontWeight.Regular),
			TextSize = 13,
			TextColor3 = color(C.Cian),
			Size = UDim2.fromOffset(24, 18),
		})
		-- El número va justo detrás del nombre («CABELLO 3»).
		local function ponerNumero()
			numero.Position = UDim2.new(0.5, nombre.TextBounds.X / 2 - 3, 0, 5)
		end
		nombre:GetPropertyChangedSignal("TextBounds"):Connect(ponerNumero)
		ponerNumero()
		local opcion = etiqueta(fila, {
			Name = "Opcion",
			Text = "",
			TextSize = 15,
			TextColor3 = color(C.TextoSuave),
			TextXAlignment = Enum.TextXAlignment.Center,
			AnchorPoint = Vector2.new(0.5, 1),
			Position = UDim2.new(0.5, 0, 1, -5),
			Size = UDim2.new(1, -110, 0, 18),
			TextTruncate = Enum.TextTruncate.AtEnd,
		})
		ui.Categorias[cat.Campo] = { Fila = fila, Numero = numero, Opcion = opcion, Nombre = nombre, Flechas = flechas }
	end
	refrescarCategorias()
end

-- ===== Color =====

local function campoObjetivo(): string
	return Datos.ObjetivosColor[objetivo].Campo
end

local function leerColorObjetivo()
	local h, s, v = color(actual[campoObjetivo()]):ToHSV()
	hsv = { h, s, v }
end

local function refrescarColor()
	local o = Datos.ObjetivosColor[objetivo]
	ui.Objetivo.Text = `{Config.Textos.Colorea}: {string.upper(o.Nombre)}  ›`
	ui.MuestraObjetivo.BackgroundColor3 = color(actual[o.Campo])
	-- Marca en la rueda: ángulo = tono (0 arriba, en el sentido del reloj), distancia al centro = saturación.
	local a = hsv[1] * 2 * math.pi
	local r = hsv[2] * 0.5
	ui.Marca.Position = UDim2.fromScale(0.5 + math.sin(a) * r, 0.5 - math.cos(a) * r)
	ui.Marca.BackgroundColor3 = Color3.fromHSV(hsv[1], hsv[2], 1)
	ui.Rueda.ImageColor3 = Color3.fromHSV(0, 0, math.max(hsv[3], 0.12))
	ui.GradienteBrillo.Color = ColorSequence.new(Color3.new(0, 0, 0), Color3.fromHSV(hsv[1], hsv[2], 1))
	ui.Pomo.Position = UDim2.fromScale(hsv[3], 0.5)
end

local function aplicarHSV()
	local c = Color3.fromHSV(hsv[1], hsv[2], hsv[3])
	actual[campoObjetivo()] = "#" .. string.upper(c:ToHex())
	refrescarColor()
	cambiar("Color")
end

-- Cubierta translúcida que atenúa y bloquea todo `padre` (un panel sin disposición automática).
local function cubrir(padre: GuiObject): Frame
	local f = crear("Frame", {
		Name = "Cubierta",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = color(C.Fondo),
		BackgroundTransparency = 0.2,
		BorderSizePixel = 0,
		Active = true,
		ZIndex = 30,
		Visible = false,
	}, padre)
	esquina(f, 10)
	return f
end

local function crearColor(raiz: Instance)
	local padre: Instance = raiz
	crear("UIListLayout", {
		Padding = UDim.new(0, 10),
		SortOrder = Enum.SortOrder.LayoutOrder,
		HorizontalAlignment = Enum.HorizontalAlignment.Center,
	}, padre)

	-- Botón para usar el avatar de Roblox (o volver a las piezas del juego) y el aviso de lo que no se pudo convertir.
	local avatarBoton = boton(raiz, {
		Name = "Avatar",
		LayoutOrder = 0,
		Text = Config.Textos.UsarAvatar,
		TextSize = 12,
		TextWrapped = true,
		Size = UDim2.new(1, 0, 0, 46),
	})
	ui.Avatar = avatarBoton
	avatarBoton.Visible = perfilActual.Avatar -- «Usar mi avatar de Roblox» es solo de los Humanos
	ui.Informe = etiqueta(raiz, {
		Name = "Informe",
		LayoutOrder = 6,
		Text = "",
		TextSize = 12,
		TextWrapped = true,
		TextColor3 = color("#FFC46B"),
		Size = UDim2.fromScale(1, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		Visible = false,
	})

	-- Los controles de color van en su propio contenedor, para poder cubrirlos con el aviso de «usando tu avatar».
	local contenedor = crear("Frame", {
		Name = "ControlColor",
		LayoutOrder = 1,
		BackgroundTransparency = 1,
		Size = UDim2.fromScale(1, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
	}, raiz)
	padre = crear("Frame", {
		Name = "Lista",
		BackgroundTransparency = 1,
		Size = UDim2.fromScale(1, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
	}, contenedor)
	crear("UIListLayout", {
		Padding = UDim.new(0, 10),
		SortOrder = Enum.SortOrder.LayoutOrder,
		HorizontalAlignment = Enum.HorizontalAlignment.Center,
	}, padre)
	ui.CubiertaColor = cubrir(contenedor)

	-- Botón que cambia lo que se colorea.
	local objetivoBoton = boton(padre, {
		Name = "Objetivo",
		LayoutOrder = 1,
		Text = "",
		TextSize = 13,
		Size = UDim2.new(1, 0, 0, 46),
		TextXAlignment = Enum.TextXAlignment.Left,
	})
	crear("UIPadding", { PaddingLeft = UDim.new(0, 44) }, objetivoBoton)
	local muestra = crear("Frame", {
		Name = "Muestra",
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.new(0, -34, 0.5, 0),
		Size = UDim2.fromOffset(24, 24),
		BorderSizePixel = 0,
	}, objetivoBoton)
	esquina(muestra, 12)
	borde(muestra, "#FFFFFF", 0.4, 1.5)
	objetivoBoton.MouseButton1Click:Connect(function()
		objetivo = objetivo % #Datos.ObjetivosColor + 1
		leerColorObjetivo()
		refrescarColor()
	end)
	ui.Objetivo = objetivoBoton
	ui.MuestraObjetivo = muestra
	avatarBoton.MouseButton1Click:Connect(function()
		local o = op
		if o and avatarBoton.Active then
			o.AlAvatar(not modoAvatar)
		end
	end)

	-- Rueda de tono y saturación.
	local rueda = crear("ImageButton", {
		Name = "Rueda",
		LayoutOrder = 2,
		Image = perfilActual.ImagenRueda,
		BackgroundTransparency = 1,
		AutoButtonColor = false,
		Size = UDim2.fromOffset(I.TamRueda, I.TamRueda),
	}, padre)
	esquina(rueda, 999)
	borde(rueda, C.Borde, 0, 3)
	local marca = crear("Frame", {
		Name = "Marca",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Size = UDim2.fromOffset(20, 20),
		BorderSizePixel = 0,
		ZIndex = 3,
	}, rueda)
	esquina(marca, 10)
	borde(marca, "#FFFFFF", 0, 3)
	ui.Rueda = rueda
	ui.Marca = marca

	-- Barra de brillo.
	local brillo = crear("TextButton", {
		Name = "Brillo",
		LayoutOrder = 3,
		Text = "",
		AutoButtonColor = false,
		BackgroundColor3 = Color3.new(1, 1, 1),
		Size = UDim2.new(1, -8, 0, 22),
		BorderSizePixel = 0,
	}, padre)
	esquina(brillo, 11)
	borde(brillo, C.Borde, 0, 2)
	ui.GradienteBrillo = crear("UIGradient", {}, brillo)
	local pomo = crear("Frame", {
		Name = "Pomo",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Size = UDim2.new(0, 14, 1, 10),
		BackgroundColor3 = Color3.new(1, 1, 1),
		BorderSizePixel = 0,
		ZIndex = 3,
	}, brillo)
	esquina(pomo, 7)
	borde(pomo, C.Cian, 0, 2)
	ui.Brillo = brillo
	ui.Pomo = pomo

	-- Muestras rápidas.
	local muestras = crear("Frame", {
		Name = "Muestras",
		LayoutOrder = 4,
		BackgroundTransparency = 1,
		Size = UDim2.new(1, 0, 0, 60),
	}, padre)
	ui.RejillaMuestras = crear("UIGridLayout", {
		CellSize = UDim2.fromOffset(26, 26),
		CellPadding = UDim2.fromOffset(6, 6),
		HorizontalAlignment = Enum.HorizontalAlignment.Center,
		SortOrder = Enum.SortOrder.LayoutOrder,
	}, muestras)
	ui.Muestras = muestras
	for i, hex in Datos.Muestras do
		local b = crear("TextButton", {
			LayoutOrder = i,
			Text = "",
			AutoButtonColor = false,
			BackgroundColor3 = color(hex),
			BorderSizePixel = 0,
		}, muestras)
		esquina(b, 6)
		borde(b, "#000000", 0.5, 1)
		b.MouseButton1Click:Connect(function()
			actual[campoObjetivo()] = hex
			leerColorObjetivo()
			refrescarColor()
			cambiar("Color")
		end)
	end

	-- Arrastrar por la rueda o por la barra.
	local arrastre: string? = nil
	local function leer(posicion: Vector2)
		if arrastre == "Rueda" then
			local centro = rueda.AbsolutePosition + rueda.AbsoluteSize / 2
			local d = posicion - centro
			local radio = rueda.AbsoluteSize.X / 2
			hsv[1] = (math.atan2(d.X, -d.Y) / (2 * math.pi)) % 1
			hsv[2] = math.clamp(d.Magnitude / radio, 0, 1)
			if hsv[3] < 0.15 then
				hsv[3] = 1 -- si estaba casi negro, al tocar la rueda se ve el color
			end
			aplicarHSV()
		elseif arrastre == "Brillo" then
			hsv[3] = math.clamp((posicion.X - brillo.AbsolutePosition.X) / brillo.AbsoluteSize.X, 0, 1)
			aplicarHSV()
		end
	end
	-- PROBADO EN STUDIO: la posición de la entrada y AbsolutePosition están en el mismo espacio (los dos sin la barra
	-- de arriba de Roblox, aunque la interfaz la ignore), así que no hay que corregir nada.
	local function posicionDe(entrada: InputObject): Vector2
		return Vector2.new(entrada.Position.X, entrada.Position.Y)
	end
	local function empezar(cual: string)
		return function(entrada: InputObject)
			local t = entrada.UserInputType
			if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.Touch then
				arrastre = cual
				leer(posicionDe(entrada))
			end
		end
	end
	rueda.InputBegan:Connect(empezar("Rueda"))
	brillo.InputBegan:Connect(empezar("Brillo"))
	table.insert(
		conexiones,
		UserInputService.InputChanged:Connect(function(entrada: InputObject)
			local t = entrada.UserInputType
			if arrastre and (t == Enum.UserInputType.MouseMovement or t == Enum.UserInputType.Touch) then
				leer(posicionDe(entrada))
			end
		end)
	)
	table.insert(
		conexiones,
		UserInputService.InputEnded:Connect(function(entrada: InputObject)
			local t = entrada.UserInputType
			if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.Touch then
				arrastre = nil
			end
		end)
	)
	leerColorObjetivo()
	refrescarColor()
end

-- ===== Disposición (ancha o estrecha) =====

-- Flechas y textos de las filas de categoría: más compactos en la tarjeta estrecha (móvil). PROBADO EN STUDIO: con
-- las medidas de escritorio, el nombre tocaba las flechas y la opción salía cortada.
local function ajustarFilas(estrecha: boolean)
	local anchoFlecha = if estrecha then 32 else 44
	for _, fila in ui.Categorias do
		for _, b in fila.Flechas do
			b.Size = UDim2.new(0, anchoFlecha, 1, -8)
			b.TextSize = if estrecha then 22 else 26
		end
		fila.Nombre.TextSize = if estrecha then 11 else 13
		fila.Nombre.Size = UDim2.new(1, -(2 * anchoFlecha + 26), 0, 18)
		fila.Numero.TextSize = if estrecha then 11 else 13
		fila.Opcion.TextSize = if estrecha then 13 else 15
		fila.Opcion.Size = UDim2.new(1, -(2 * anchoFlecha + 12), 0, 18)
	end
end

local function maquetar()
	local g = gui
	local cam = workspace.CurrentCamera
	if g == nil or cam == nil then
		return
	end
	local v = cam.ViewportSize
	local estrecha = v.X < I.AnchoMinimo or v.Y < I.AltoMinimo
	disposicion = if estrecha then "Estrecha" else "Ancha"
	local m = I.Margen

	local cabecera, izq, der, abajo = ui.Cabecera, ui.Izquierda, ui.Derecha, ui.Abajo
	local cats = ui.ContCategorias
	local lista = ui.ListaCategorias

	if not estrecha then
		cabecera.Position = UDim2.fromOffset(m + 4, m)
		ui.Titulo.TextSize = 30
		ui.Subtitulo.TextSize = 15
		izq.Visible = true
		izq.Position = UDim2.fromOffset(m, m + 78)
		izq.Size = UDim2.new(0, I.AnchoIzquierda, 1, -(m + 78) - I.AltoBoton - 2 * m)
		ui.PielesCont.Parent = izq
		ui.PielesCont.Position = UDim2.fromOffset(0, 28)
		ui.PielesCont.Size = UDim2.new(1, 0, 0, 36)
		ui.TituloPiel.Visible = true
		ui.TituloAspecto.Visible = true
		cats.Parent = izq
		cats.Position = UDim2.fromOffset(12, 104)
		cats.Size = UDim2.new(1, -24, 1, -116)
		cats.ScrollingDirection = Enum.ScrollingDirection.Y
		lista.FillDirection = Enum.FillDirection.Vertical
		for _, fila in ui.Categorias do
			fila.Fila.Size = UDim2.new(1, 0, 0, I.AltoFila)
		end
		ajustarFilas(false)
		der.Position = UDim2.new(1, -m - I.AnchoDerecha, 0, m + 78)
		der.Size = UDim2.fromOffset(I.AnchoDerecha, 0)
		ui.Rueda.Size = UDim2.fromOffset(I.TamRueda, I.TamRueda)
		ui.RejillaMuestras.CellSize = UDim2.fromOffset(26, 26)
		ui.RejillaMuestras.CellPadding = UDim2.fromOffset(6, 6)
		ui.Muestras.Size = UDim2.new(1, 0, 0, 60)
		ui.BarraInferior.Visible = false
		abajo.Position = UDim2.new(0, m, 1, -m - I.AltoBoton)
		abajo.Size = UDim2.new(1, -2 * m, 0, I.AltoBoton)
		for _, b in ui.Botones do
			b.Size = UDim2.new(0, 220, 1, 0)
			b.TextSize = 18
		end
	else
		cabecera.Position = UDim2.fromOffset(m, 10)
		ui.Titulo.TextSize = 20
		ui.Subtitulo.TextSize = 12
		izq.Visible = false
		ui.PielesCont.Parent = g
		ui.PielesCont.Position = UDim2.fromOffset(m - 4, 66)
		ui.PielesCont.Size = UDim2.fromOffset(300, 36)
		ui.TituloPiel.Visible = false
		ui.TituloAspecto.Visible = false
		local altoBarra = I.AltoCategoriaEstrecha + 12
		ui.BarraInferior.Visible = true
		ui.BarraInferior.Position = UDim2.new(0, 0, 1, -altoBarra - I.AltoBotonEstrecho - 16)
		ui.BarraInferior.Size = UDim2.new(1, 0, 0, altoBarra)
		cats.Parent = ui.BarraInferior
		cats.Position = UDim2.fromOffset(m, 6)
		cats.Size = UDim2.new(1, -2 * m, 1, -12)
		cats.ScrollingDirection = Enum.ScrollingDirection.X
		lista.FillDirection = Enum.FillDirection.Horizontal
		for _, fila in ui.Categorias do
			fila.Fila.Size = UDim2.fromOffset(I.AnchoCategoriaEstrecha, I.AltoCategoriaEstrecha)
		end
		ajustarFilas(true)
		der.Position = UDim2.new(1, -m - I.AnchoDerechaEstrecha, 0, 10)
		der.Size = UDim2.fromOffset(I.AnchoDerechaEstrecha, 0)
		ui.Rueda.Size = UDim2.fromOffset(I.TamRuedaEstrecha, I.TamRuedaEstrecha)
		-- 8 por fila en el panel estrecho (dos filas iguales).
		ui.RejillaMuestras.CellSize = UDim2.fromOffset(17, 17)
		ui.RejillaMuestras.CellPadding = UDim2.fromOffset(4, 4)
		ui.Muestras.Size = UDim2.new(1, 0, 0, 50)
		abajo.Position = UDim2.new(0, m, 1, -I.AltoBotonEstrecho - 8)
		abajo.Size = UDim2.new(1, -2 * m, 0, I.AltoBotonEstrecho)
		for _, b in ui.Botones do
			b.Size = UDim2.fromScale(0.31, 1)
			b.TextSize = 14
		end
	end
	local o = op
	if o then
		o.AlDisponer(disposicion)
	end
end

-- ===== Abrir y cerrar =====

function Pantalla.Abierta(): boolean
	return gui ~= nil
end

-- Cambia el modo: con el avatar de Roblox se atenúan las piezas y los colores (se conservan para cuando se vuelva).
function Pantalla.PonerAvatar(activo: boolean)
	modoAvatar = activo
	local b = ui.Avatar
	if b == nil then
		return
	end
	b.Text = if activo then Config.Textos.UsarPiezas else Config.Textos.UsarAvatar
	b.Active = true
	ui.CubiertaIzquierda.Visible = activo
	ui.CubiertaColor.Visible = activo
	if not activo then
		ui.Informe.Visible = false
		ui.Informe.Text = ""
	end
end

-- El avatar se está cargando (el botón espera) o ha terminado de cargarse.
function Pantalla.AvatarCargando(cargando: boolean)
	local b = ui.Avatar
	if b then
		b.Active = not cargando
		b.Text = if cargando
			then Config.Textos.CargandoAvatar
			else (if modoAvatar then Config.Textos.UsarPiezas else Config.Textos.UsarAvatar)
	end
end

-- Aviso bajo el botón (lo que no se pudo convertir, o un error). Vacío lo oculta.
function Pantalla.Informe(lineas: { string })
	local l = ui.Informe
	if l then
		l.Text = table.concat(lineas, "\n")
		l.Visible = #lineas > 0
	end
end

-- Pone otra apariencia en todos los controles (por ejemplo tras ALEATORIO).
function Pantalla.Poner(a: any)
	actual = table.clone(a :: any)
	refrescarPiel()
	refrescarCategorias()
	leerColorObjetivo()
	refrescarColor()
end

function Pantalla.Abrir(opciones: Opciones)
	Pantalla.Cerrar()
	op = opciones
	perfilActual = opciones.Perfil
	Apariencia = perfilActual.Apariencia
	Datos = perfilActual.Datos
	actual = table.clone(opciones.Inicial :: any)
	objetivo = 1
	modoAvatar = false
	bloquear()

	local g = crear("ScreenGui", {
		Name = NOMBRE_GUI,
		ResetOnSpawn = false,
		IgnoreGuiInset = true,
		DisplayOrder = 120,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
	}, nil)
	gui = g

	-- Viñeta oscura en los bordes: centra la mirada en el personaje.
	local vineta = crear("Frame", {
		Name = "Vineta",
		Size = UDim2.fromScale(1, 1),
		BackgroundColor3 = color(C.Fondo),
		BorderSizePixel = 0,
	}, g)
	crear("UIGradient", {
		Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0.35),
			NumberSequenceKeypoint.new(0.3, 1),
			NumberSequenceKeypoint.new(0.7, 1),
			NumberSequenceKeypoint.new(1, 0.35),
		}),
	}, vineta)

	-- Cabecera.
	local cabecera =
		crear("Frame", { Name = "Cabecera", BackgroundTransparency = 1, Size = UDim2.fromOffset(560, 60) }, g)
	ui.Cabecera = cabecera
	ui.Titulo = etiqueta(cabecera, {
		Name = "Titulo",
		Text = perfilActual.Titulo or Config.Textos.Titulo,
		FontFace = fuente(Config.Fuentes.Titulo, Enum.FontWeight.Regular),
		TextSize = 30,
		Size = UDim2.new(1, 0, 0, 36),
		TextStrokeTransparency = 0.6,
	})
	ui.Subtitulo = etiqueta(cabecera, {
		Name = "Subtitulo",
		Text = Config.Textos.Subtitulo,
		TextSize = 15,
		TextColor3 = color(C.Cian),
		Position = UDim2.fromOffset(2, 38),
		Size = UDim2.new(1, 0, 0, 20),
	})

	-- Izquierda: piel y categorías.
	local izq = panel(g, "Izquierda")
	ui.Izquierda = izq
	ui.TituloPiel = etiqueta(izq, {
		Name = "TituloPiel",
		Text = Config.Textos.Piel,
		FontFace = fuente(Config.Fuentes.Titulo, Enum.FontWeight.Regular),
		TextSize = 13,
		TextColor3 = color(C.TextoSuave),
		Position = UDim2.fromOffset(16, 10),
		Size = UDim2.new(1, -32, 0, 16),
	})
	local pieles = crear("Frame", { Name = "PielesCont", BackgroundTransparency = 1 }, izq)
	ui.PielesCont = pieles
	crearPieles(pieles)
	ui.TituloAspecto = etiqueta(izq, {
		Name = "TituloAspecto",
		Text = Config.Textos.Aspecto,
		FontFace = fuente(Config.Fuentes.Titulo, Enum.FontWeight.Regular),
		TextSize = 13,
		TextColor3 = color(C.TextoSuave),
		Position = UDim2.fromOffset(16, 78),
		Size = UDim2.new(1, -32, 0, 16),
	})
	crearCategorias(izq)

	-- Barra de categorías de la disposición estrecha.
	ui.BarraInferior = crear("Frame", {
		Name = "BarraCategorias",
		BackgroundColor3 = color(C.Fondo),
		BackgroundTransparency = 0.3,
		BorderSizePixel = 0,
		Visible = false,
	}, g)

	-- Derecha: color.
	local der = panel(g, "Derecha")
	der.AutomaticSize = Enum.AutomaticSize.Y
	crear("UIPadding", {
		PaddingTop = UDim.new(0, 12),
		PaddingBottom = UDim.new(0, 14),
		PaddingLeft = UDim.new(0, 12),
		PaddingRight = UDim.new(0, 12),
	}, der)
	ui.Derecha = der
	crearColor(der)
	ui.CubiertaIzquierda = cubrir(izq)

	-- Abajo: ATRÁS, ALEATORIO y CONTINUAR.
	local abajo = crear("Frame", { Name = "Abajo", BackgroundTransparency = 1 }, g)
	ui.Abajo = abajo
	local atras = boton(abajo, { Name = "Atras", Text = Config.Textos.Atras })
	local aleatorio = boton(abajo, {
		Name = "Aleatorio",
		Text = Config.Textos.Aleatorio,
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.fromScale(0.5, 0),
	})
	local continuar = boton(abajo, {
		Name = "Continuar",
		Text = Config.Textos.Continuar,
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.fromScale(1, 0),
	}, true)
	ui.Botones = { atras, aleatorio, continuar }

	local terminado = false
	atras.MouseButton1Click:Connect(function()
		if terminado then
			return
		end
		terminado = true
		opciones.AlAtras()
	end)
	aleatorio.MouseButton1Click:Connect(function()
		if modoAvatar then
			opciones.AlAvatar(false) -- aleatorio es de las piezas del juego
		end
		Pantalla.Poner(opciones.AlAleatorio())
		cambiar("Pieza")
	end)
	continuar.MouseButton1Click:Connect(function()
		if terminado then
			return
		end
		terminado = true
		opciones.AlTerminar(table.clone(actual) :: any, modoAvatar)
	end)

	g.Parent = jugador:WaitForChild("PlayerGui")
	maquetar()
	Pantalla.PonerAvatar(opciones.UsarAvatar)
	local cam = workspace.CurrentCamera
	if cam then
		table.insert(conexiones, cam:GetPropertyChangedSignal("ViewportSize"):Connect(maquetar))
	end

	-- Entrada: los paneles llegan deslizándose desde los lados.
	local function entrar(o: GuiObject, desde: UDim2)
		local destino = o.Position
		o.Position = destino + desde
		TweenService:Create(o, TweenInfo.new(0.55, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), {
			Position = destino,
		}):Play()
	end
	entrar(izq, UDim2.fromOffset(-420, 0))
	entrar(der, UDim2.fromOffset(420, 0))
	entrar(abajo, UDim2.fromOffset(0, 120))
	entrar(cabecera, UDim2.fromOffset(0, -90))
end

function Pantalla.Cerrar()
	for _, c in conexiones do
		c:Disconnect()
	end
	table.clear(conexiones)
	if gui then
		gui:Destroy()
		gui = nil
		desbloquear()
	end
	ui = {}
	op = nil
end

return Pantalla
