--!strict
--[[
	UITweens: biblioteca de animaciones de la interfaz. Todas las transiciones pasan por aquí y usan TweenService
	con los TweenInfo de EspacialTheme.Tweens:

	  - abrir/cerrar ventanas: deslizamiento + fundido (con un CanvasGroup solo mientras dura, ver FundirMarco)
	  - hover de botones: escala 1,05 con un UIScale propio
	  - cambio de pestañas: fundido cruzado
	  - barras de vida: interpolación suave del tamaño
	  - pulsos infinitos (brillos) y giros

	Rendimiento: los tweens infinitos se guardan por objeto y se cancelan al pararlos o al destruir el objeto, para que
	no queden animaciones vivas de paneles cerrados.
]]

local TweenService = game:GetService("TweenService")

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)

local UITweens = {}

-- Tweens infinitos activos por objeto (para poder pararlos).
local infinitos: { [Instance]: { Tween } } = setmetatable({}, { __mode = "k" }) :: any

-- Crea y reproduce un tween. Devuelve el Tween por si se quiere esperar a que acabe.
function UITweens.Tween(objeto: Instance, info: TweenInfo, propiedades: { [string]: any }): Tween
	local tween = TweenService:Create(objeto, info, propiedades)
	tween:Play()
	return tween
end

-- Tween que se repite para siempre (info con RepeatCount = -1). Se puede parar con UITweens.Parar(objeto).
function UITweens.Infinito(objeto: Instance, info: TweenInfo, propiedades: { [string]: any }): Tween
	local tween = UITweens.Tween(objeto, info, propiedades)
	local lista = infinitos[objeto]
	if lista == nil then
		lista = {}
		infinitos[objeto] = lista
		objeto.Destroying:Once(function()
			UITweens.Parar(objeto)
		end)
	end
	table.insert(lista, tween)
	return tween
end

-- Cancela los tweens infinitos de un objeto.
function UITweens.Parar(objeto: Instance)
	local lista = infinitos[objeto]
	if lista then
		for _, tween in lista do
			tween:Cancel()
		end
		infinitos[objeto] = nil
	end
end

-- UIScale propio de un objeto (lo crea si no existe). Lo usan el hover y las apariciones con escala.
function UITweens.EscalaDe(objeto: GuiObject): UIScale
	local escala = objeto:FindFirstChild("EscalaAnimada")
	if escala and escala:IsA("UIScale") then
		return escala
	end
	local nueva = Instance.new("UIScale")
	nueva.Name = "EscalaAnimada"
	nueva.Parent = objeto
	return nueva
end

--[[
	Hover de un botón: al pasar el ratón crece a 1,05 (0,15 s) y al pulsarlo se hunde a 0,97. Opcionalmente cambia
	el fondo (`fondoHover` = transparencia del fondo con el ratón encima).
	Devuelve una función que quita el efecto.
]]
function UITweens.Hover(boton: GuiButton, fondoHover: number?): () -> ()
	local escala = UITweens.EscalaDe(boton)
	local fondoNormal = boton.BackgroundTransparency
	local conexiones: { RBXScriptConnection } = {}
	local dentro = false
	table.insert(
		conexiones,
		boton.MouseEnter:Connect(function()
			dentro = true
			UITweens.Tween(escala, Theme.Tweens.Rapido, { Scale = Theme.Tiempos.EscalaHover })
			if fondoHover then
				fondoNormal = boton.BackgroundTransparency
				UITweens.Tween(boton, Theme.Tweens.Rapido, { BackgroundTransparency = fondoHover })
			end
		end)
	)
	table.insert(
		conexiones,
		boton.MouseLeave:Connect(function()
			dentro = false
			UITweens.Tween(escala, Theme.Tweens.Rapido, { Scale = 1 })
			if fondoHover then
				UITweens.Tween(boton, Theme.Tweens.Rapido, { BackgroundTransparency = fondoNormal })
			end
		end)
	)
	table.insert(
		conexiones,
		boton.MouseButton1Down:Connect(function()
			UITweens.Tween(escala, Theme.Tweens.Rapido, { Scale = Theme.Tiempos.EscalaPulsado })
		end)
	)
	table.insert(
		conexiones,
		boton.MouseButton1Up:Connect(function()
			UITweens.Tween(escala, Theme.Tweens.Rapido, { Scale = if dentro then Theme.Tiempos.EscalaHover else 1 })
		end)
	)
	return function()
		for _, conexion in conexiones do
			conexion:Disconnect()
		end
		escala.Scale = 1
	end
end

-- ===== Fundidos de marcos grandes =====
--[[
	Un CanvasGroup dibuja su contenido en una textura y la rehace cada vez que algo de dentro cambia. Para una ventana
	entera (con un personaje girando, barras que laten...) o para todo el HUD eso sería redibujar una textura grande en
	cada fotograma, caro en móvil. Por eso los marcos grandes son Frames normales y solo DURANTE el fundido se meten en
	un CanvasGroup temporal, que se destruye al acabar.
]]

type Transicion = { Grupo: CanvasGroup, Tween: Tween, Terminar: () -> () }
local transiciones: { [GuiObject]: Transicion } = {}

-- Termina en seco la transición en curso de `marco` (si la hay), dejándolo en su estado final.
local function terminarTransicion(marco: GuiObject)
	local t = transiciones[marco]
	if t then
		transiciones[marco] = nil
		t.Tween:Cancel()
		t.Terminar()
	end
end

--[[
	Funde un marco cualquiera hacia `visible` (deslizándolo `desplazamiento` unidades en X si se indica: entra desde
	ahí y sale hacia ahí). Al terminar, el marco queda en su sitio de siempre, con Visible = `visible`.
]]
function UITweens.FundirMarco(marco: GuiObject, visible: boolean, info: TweenInfo?, desplazamiento: number?)
	terminarTransicion(marco)
	local padre = marco.Parent
	if padre == nil then
		marco.Visible = visible
		return
	end
	if marco.Visible == visible and visible then
		return
	end
	local original = { Posicion = marco.Position, Tamano = marco.Size, Ancla = marco.AnchorPoint }
	local grupo = Instance.new("CanvasGroup")
	grupo.Name = marco.Name .. "_Fundido"
	grupo.BackgroundTransparency = 1
	grupo.BorderSizePixel = 0
	grupo.Size = original.Tamano
	grupo.AnchorPoint = original.Ancla
	grupo.ZIndex = marco.ZIndex
	grupo.LayoutOrder = marco.LayoutOrder
	local d = UDim2.fromOffset(desplazamiento or 0, 0)
	grupo.Position = if visible then original.Posicion + d else original.Posicion
	grupo.GroupTransparency = if visible then 1 else 0
	grupo.Parent = padre
	marco.AnchorPoint = Vector2.zero
	marco.Position = UDim2.new()
	marco.Size = UDim2.fromScale(1, 1)
	marco.Visible = true
	marco.Parent = grupo

	local tween = TweenService:Create(grupo, info or Theme.Tweens.Fundido, {
		GroupTransparency = if visible then 0 else 1,
		Position = if visible then original.Posicion else original.Posicion + d,
	})
	local function terminar()
		marco.Parent = padre
		marco.AnchorPoint = original.Ancla
		marco.Position = original.Posicion
		marco.Size = original.Tamano
		marco.Visible = visible
		grupo:Destroy()
	end
	transiciones[marco] = { Grupo = grupo, Tween = tween, Terminar = terminar }
	tween.Completed:Once(function(estado)
		if estado == Enum.PlaybackState.Completed and transiciones[marco] and transiciones[marco].Tween == tween then
			transiciones[marco] = nil
			terminar()
		end
	end)
	tween:Play()
end

-- Abre una ventana: se desliza desde la derecha (Theme.Tiempos.DesplazamientoVentana) y aparece con un fundido.
function UITweens.AbrirVentana(ventana: GuiObject)
	UITweens.FundirMarco(ventana, true, Theme.Tweens.Normal, Theme.Tiempos.DesplazamientoVentana)
end

-- Cierra una ventana con el movimiento contrario y la oculta al terminar.
function UITweens.CerrarVentana(ventana: GuiObject)
	UITweens.FundirMarco(ventana, false, Theme.Tweens.Normal, Theme.Tiempos.DesplazamientoVentana)
end

-- Fundido de un CanvasGroup pequeño (tooltips, etiquetas, listas) a `visible`. Al ocultarlo del todo, Visible = false.
function UITweens.Fundir(grupo: CanvasGroup, visible: boolean, info: TweenInfo?)
	if visible then
		grupo.Visible = true
	end
	local tween = UITweens.Tween(grupo, info or Theme.Tweens.Fundido, { GroupTransparency = if visible then 0 else 1 })
	if not visible then
		tween.Completed:Once(function(estado)
			if estado == Enum.PlaybackState.Completed then
				grupo.Visible = false
			end
		end)
	end
end

-- Fundido cruzado entre dos vistas (pestañas): una se va mientras la otra llega (0,2 s).
function UITweens.FundidoCruzado(saliente: GuiObject?, entrante: GuiObject)
	if saliente and saliente ~= entrante then
		UITweens.FundirMarco(saliente, false)
	end
	if not entrante.Visible or transiciones[entrante] then
		entrante.Visible = false
		UITweens.FundirMarco(entrante, true)
	end
end

-- Aparición con escala 0,95 -> 1 y fundido (tooltips, modales).
function UITweens.Aparecer(grupo: CanvasGroup, info: TweenInfo?)
	local escala = UITweens.EscalaDe(grupo)
	escala.Scale = 0.95
	grupo.GroupTransparency = 1
	grupo.Visible = true
	local i = info or Theme.Tweens.Tooltip
	UITweens.Tween(escala, i, { Scale = 1 })
	UITweens.Tween(grupo, i, { GroupTransparency = 0 })
end

-- Interpola el ancho de una barra (Size.X.Scale) hasta `proporcion`.
function UITweens.Barra(relleno: GuiObject, proporcion: number, info: TweenInfo?): Tween
	local p = math.clamp(proporcion, 0, 1)
	return UITweens.Tween(relleno, info or Theme.Tweens.Barra, {
		Size = UDim2.new(p, relleno.Size.X.Offset, relleno.Size.Y.Scale, relleno.Size.Y.Offset),
	})
end

-- Brillo que va y viene sobre una propiedad numérica (por ejemplo la transparencia de un UIStroke).
function UITweens.Pulso(objeto: Instance, propiedad: string, desde: number, hasta: number, info: TweenInfo?): Tween
	(objeto :: any)[propiedad] = desde
	return UITweens.Infinito(objeto, info or Theme.Tweens.Pulso, { [propiedad] = hasta })
end

-- Giro continuo (anillos decorativos).
function UITweens.Girar(objeto: GuiObject, info: TweenInfo?): Tween
	objeto.Rotation = 0
	return UITweens.Infinito(objeto, info or Theme.Tweens.Giro, { Rotation = 360 })
end

-- Desplaza un UIGradient de lado a lado sin parar (rango Estelar).
function UITweens.Arcoiris(degradado: UIGradient): Tween
	degradado.Offset = Vector2.new(-1, 0)
	return UITweens.Infinito(degradado, Theme.Tweens.Arcoiris, { Offset = Vector2.new(1, 0) })
end

-- Sacudida corta (al recibir daño). Mueve el objeto y lo devuelve a su sitio.
function UITweens.Sacudir(objeto: GuiObject, fuerza: number?)
	local origen = objeto.Position
	local f = fuerza or 2
	task.spawn(function()
		for _, desplazamiento in
			{ Vector2.new(-f, f / 2), Vector2.new(f, -f / 2), Vector2.new(-f / 2, 0), Vector2.new(f / 2, f / 2) }
		do
			objeto.Position = origen + UDim2.fromOffset(desplazamiento.X, desplazamiento.Y)
			task.wait(0.04)
		end
		objeto.Position = origen
	end)
end

-- Destello de un objeto: crece un poco y vuelve (al desbloquear un nodo, al recargarse una habilidad).
function UITweens.Destello(objeto: GuiObject, escalaMaxima: number?)
	local escala = UITweens.EscalaDe(objeto)
	local subida = UITweens.Tween(escala, Theme.Tweens.Rapido, { Scale = escalaMaxima or 1.3 })
	subida.Completed:Once(function()
		UITweens.Tween(escala, Theme.Tweens.Rebote, { Scale = 1 })
	end)
end

return UITweens
