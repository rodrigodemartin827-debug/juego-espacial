--!strict
--[[
	PanelInventario: la vista INVENTARIO. Vive dentro de la ventana de PERSONAJE (es su segunda pestaña) y se abre también
	con el botón de inventario de la barra lateral o con la tecla I.

	  [Todo] [Armas] [Armadura] [Materiales] [Consumibles] [Especial]        BODEGA 34/80 ▬▬▬
	  ┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐      [CAS]          [AMU]
	  │img ││img ││img ││img ││ ?  ││ ?  │      [ARM] (pers.)  [ANI]
	  └────┘└────┘└────┘└────┘└────┘└────┘      [ESP]          [CIN]
	  ...                                         [ARM]          [BOT]

	  - Rejilla con UIGridLayout (65×65, separación 4) dentro de un ScrollingFrame.
	  - Clic = seleccionar y ficha con EQUIPAR / TIRAR / INFO · doble clic = equipar · clic en un slot del muñeco con
	    algo seleccionado = equiparlo ahí · arrastrar una casilla hasta su slot = equiparla.
	  - Materiales reales del servidor (con su capacidad de bodega) + equipo de demostración (ver EstadoUI).
]]

local GuiService = game:GetService("GuiService")
local UserInputService = game:GetService("UserInputService")

local Theme = require(script.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Componentes.Primitivas)
local TabSelector = require(script.Parent.Componentes.TabSelector)
local CardItem = require(script.Parent.Componentes.CardItem)
local Tooltip = require(script.Parent.Componentes.Tooltip)
local Modal = require(script.Parent.Componentes.Modal)
local Muneco = require(script.Parent.Componentes.Muneco)
local EstadoUI = require(script.Parent.EstadoUI)
local Contexto = require(script.Parent.Contexto)

local C = Theme.Colores
local T = Theme.Tamanos

local PanelInventario = {}

local FILTROS = { "Todo", "Armas", "Armadura", "Materiales", "Consumibles", "Especial" }

local ctx: Contexto.Contexto = nil :: any
local rejilla: ScrollingFrame = nil :: any
local textoBodega: TextLabel = nil :: any
local rellenoBodega: Frame = nil :: any
local muneco: Muneco.Muneco = nil :: any
local tarjetas: { CardItem.CardItem } = {}
local filtro = "Todo"
local seleccionado: string? = nil
local fijado = false -- la ficha se queda abierta (objeto seleccionado con clic)

-- ===== Acciones =====

local function avisoEquipo(objeto: EstadoUI.ObjetoUI, puesto: boolean)
	ctx.Notificar({
		Titulo = if puesto then "Equipado" else "Desequipado",
		Texto = objeto.Nombre,
		Color = if puesto then Theme.ColorRareza(objeto.Rareza) else C.Gris,
		Arte = objeto.Arte,
	})
end

local function deseleccionar()
	seleccionado = nil
	fijado = false
	for _, tarjeta in tarjetas do
		tarjeta.Seleccionar(false)
	end
	muneco.MarcarObjetivo(nil)
	Tooltip.Ocultar()
end

local function equipar(id: string)
	local objeto, puesto = EstadoUI.Equipar(id)
	deseleccionar()
	if objeto then
		avisoEquipo(objeto, puesto)
	end
end

local function accionesDe(objeto: EstadoUI.ObjetoUI): { Tooltip.Accion }
	local acciones: { Tooltip.Accion } = {}
	if objeto.Slot then
		table.insert(acciones, {
			Texto = if EstadoUI.EstaEquipado(objeto.Id) then "QUITAR" else "EQUIPAR",
			Estilo = "Cian",
			AlPulsar = function()
				equipar(objeto.Id)
			end,
		})
	elseif objeto.Filtro == "Consumibles" then
		table.insert(acciones, {
			Texto = "USAR",
			Estilo = "Cian",
			AlPulsar = function()
				-- TODO(servidor): enviar "UsarConsumible". Los consumibles aún no existen en el juego.
				ctx.Notificar({
					Titulo = "Usar",
					Texto = `{objeto.Nombre}: pendiente del servidor`,
					Color = C.Dorado,
					Arte = objeto.Arte,
				})
				deseleccionar()
			end,
		})
	end
	table.insert(acciones, {
		Texto = "TIRAR",
		Estilo = "Rojo",
		AlPulsar = function()
			local cantidad = if objeto.Cantidad then ` (x{objeto.Cantidad})` else ""
			Modal.Confirmar({
				Titulo = "¿TIRAR OBJETO?",
				Texto = `Vas a tirar <b>{objeto.Nombre}</b>{cantidad}. No se puede deshacer.`,
				Arte = objeto.Arte,
				Color = C.Peligro,
				TextoSi = "TIRAR",
				EstiloSi = "Rojo",
				AlSi = function()
					-- TODO(servidor): enviar "TirarObjeto" (el servidor lo quita con ServicioInventario.Quitar).
					ctx.Notificar({
						Titulo = "Tirar",
						Texto = `{objeto.Nombre}: pendiente del servidor`,
						Color = C.Peligro,
						Icono = "ui_alerta",
					})
				end,
			})
		end,
	})
	table.insert(acciones, {
		Texto = "INFO",
		Estilo = "Gris",
		AlPulsar = function()
			ctx.Abrir("indice")
		end,
	})
	return acciones
end

local function seleccionar(id: string, boton: GuiObject)
	if seleccionado == id and fijado then
		deseleccionar()
		return
	end
	local objeto = EstadoUI.Objeto(id)
	if objeto == nil then
		return
	end
	seleccionado = id
	fijado = true
	for _, tarjeta in tarjetas do
		tarjeta.Seleccionar(tarjeta.Id == id)
	end
	muneco.MarcarObjetivo(objeto.Slot)
	Tooltip.Mostrar(objeto, boton, accionesDe(objeto))
end

-- Clic en un slot del muñeco: equipa lo seleccionado si va ahí; si no hay nada seleccionado, quita lo que tenga.
local function alPulsarSlot(slot: string)
	local objeto = if seleccionado then EstadoUI.Objeto(seleccionado) else nil
	if objeto then
		if objeto.Slot == slot then
			equipar(objeto.Id)
		else
			ctx.Notificar({
				Titulo = "No encaja",
				Texto = `{objeto.Nombre} no va en ese slot`,
				Color = C.Peligro,
				Icono = "ui_alerta",
			})
		end
		return
	end
	local quitado = EstadoUI.Desequipar(slot)
	if quitado then
		avisoEquipo(quitado, false)
	end
end

-- ===== Arrastrar y soltar =====

local arrastre: { Id: string, Inicio: Vector2, Fantasma: ImageLabel? }? = nil

-- Posición del puntero en coordenadas de AbsolutePosition (la ScreenGui ignora la barra de Roblox).
local function punteroAbsoluto(entrada: InputObject): Vector2
	local inset = GuiService:GetGuiInset()
	return Vector2.new(entrada.Position.X, entrada.Position.Y) + inset
end

local function slotBajo(posicion: Vector2): string?
	for _, boton in muneco.Marco:GetDescendants() do
		if boton:IsA("TextButton") and boton:GetAttribute("SlotId") then
			local a, t = boton.AbsolutePosition, boton.AbsoluteSize
			if posicion.X >= a.X and posicion.X <= a.X + t.X and posicion.Y >= a.Y and posicion.Y <= a.Y + t.Y then
				return boton:GetAttribute("SlotId") :: string
			end
		end
	end
	return nil
end

local function empezarArrastre(id: string, entrada: InputObject)
	arrastre = { Id = id, Inicio = punteroAbsoluto(entrada) }
end

UserInputService.InputChanged:Connect(function(entrada)
	local a = arrastre
	if a == nil then
		return
	end
	if
		entrada.UserInputType ~= Enum.UserInputType.MouseMovement
		and entrada.UserInputType ~= Enum.UserInputType.Touch
	then
		return
	end
	local posicion = punteroAbsoluto(entrada)
	if a.Fantasma == nil and (posicion - a.Inicio).Magnitude > 8 then
		local objeto = EstadoUI.Objeto(a.Id)
		if objeto == nil or objeto.Slot == nil then
			arrastre = nil
			return
		end
		Tooltip.Ocultar()
		muneco.MarcarObjetivo(objeto.Slot)
		a.Fantasma = IconBuilder.Arte(
			ctx.Raiz,
			objeto.Arte,
			{ Tamano = 50, Ancla = Vector2.new(0.5, 0.5), Z = 95, Transparencia = 0.15 }
		)
	end
	local fantasma = a.Fantasma
	if fantasma then
		local u = ctx.AUnidades(posicion)
		fantasma.Position = UDim2.fromOffset(u.X, u.Y)
	end
end)

UserInputService.InputEnded:Connect(function(entrada)
	local a = arrastre
	if a == nil then
		return
	end
	if
		entrada.UserInputType ~= Enum.UserInputType.MouseButton1
		and entrada.UserInputType ~= Enum.UserInputType.Touch
	then
		return
	end
	arrastre = nil
	local fantasma = a.Fantasma
	if fantasma == nil then
		return
	end
	fantasma:Destroy()
	local slot = slotBajo(punteroAbsoluto(entrada))
	local objeto = EstadoUI.Objeto(a.Id)
	if objeto and slot == objeto.Slot then
		if not EstadoUI.EstaEquipado(objeto.Id) then
			equipar(objeto.Id)
		end
	end
	muneco.MarcarObjetivo(if seleccionado then (EstadoUI.Objeto(seleccionado) or {} :: any).Slot else nil)
end)

-- ===== Pintado =====

local function pintarBodega()
	local ocupado, capacidad = EstadoUI.Bodega()
	textoBodega.Text = P.Espaciar(`BODEGA {math.floor(ocupado)}/{math.floor(capacidad)}`)
	local fraccion = if capacidad > 0 then math.clamp(ocupado / capacidad, 0, 1) else 0
	UITweens.Barra(rellenoBodega, fraccion)
	textoBodega.TextColor3 = if fraccion >= 0.9 then C.Peligro else C.TextoSecundario
end

-- Rehace la rejilla (se llama al cambiar el inventario, el equipo o el filtro).
function PanelInventario.Refrescar()
	for _, hijo in rejilla:GetChildren() do
		if hijo:IsA("GuiObject") then
			hijo:Destroy()
		end
	end
	table.clear(tarjetas)
	local orden = 0
	for _, objeto in EstadoUI.Objetos() do
		if filtro == "Todo" or objeto.Filtro == filtro then
			orden += 1
			local tarjeta = CardItem.Crear(rejilla, {
				Id = objeto.Id,
				Arte = objeto.Arte,
				Rareza = objeto.Rareza,
				Cantidad = objeto.Cantidad,
				Equipado = EstadoUI.EstaEquipado(objeto.Id),
				Orden = orden,
				AlPulsar = seleccionar,
				AlDobleClic = function(id: string)
					local o = EstadoUI.Objeto(id)
					if o and o.Slot then
						equipar(id)
					end
				end,
				AlEntrar = function(id: string, boton: GuiObject)
					if not fijado then
						local o = EstadoUI.Objeto(id)
						if o then
							Tooltip.Mostrar(o, boton)
						end
					end
				end,
				AlSalir = function()
					if not fijado then
						Tooltip.Ocultar()
					end
				end,
			})
			tarjeta.Seleccionar(objeto.Id == seleccionado)
			tarjeta.Boton.InputBegan:Connect(function(entrada)
				if
					entrada.UserInputType == Enum.UserInputType.MouseButton1
					or entrada.UserInputType == Enum.UserInputType.Touch
				then
					empezarArrastre(objeto.Id, entrada)
				end
			end)
			table.insert(tarjetas, tarjeta)
		end
	end
	-- Casillas "?" de lo que aún no se ha encontrado (solo en "Todo").
	if filtro == "Todo" then
		for _ = 1, EstadoUI.CasillasOcultas() do
			orden += 1
			CardItem.Crear(rejilla, { Orden = orden })
		end
	end
	muneco.Refrescar()
	pintarBodega()
end

-- ===== API =====

-- Construye la vista dentro de `vista` (la pestaña de la ventana de Personaje).
function PanelInventario.Construir(vista: GuiObject, contexto: Contexto.Contexto)
	ctx = contexto

	TabSelector.Crear(vista, {
		Opciones = (function(): { TabSelector.Opcion }
			local lista: { TabSelector.Opcion } = {}
			for _, f in FILTROS do
				table.insert(lista, { Id = f, Texto = f })
			end
			return lista
		end)(),
		Inicial = filtro,
		Estilo = "Pildora",
		AlCambiar = function(id: string)
			filtro = id
			deseleccionar()
			PanelInventario.Refrescar()
		end,
		Z = 4,
	})

	textoBodega = P.Texto(vista, {
		Texto = "BODEGA 0/0",
		Tamano = Theme.Texto.Mini + 0.5,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoSecundario,
		Transparencia = Theme.Alpha.TextoSecundario,
		Posicion = UDim2.new(1, -78, 0, 10),
		Ancla = Vector2.new(1, 0.5),
		Z = 4,
	})
	local _, relleno = P.BarraProgreso(
		vista,
		{ Tamano = UDim2.fromOffset(70, 4), Posicion = UDim2.new(1, 0, 0, 10), Ancla = Vector2.new(1, 0.5), Z = 4 }
	)
	rellenoBodega = relleno

	rejilla = P.Crear("ScrollingFrame", {
		Name = "Rejilla",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = UDim2.new(0, 6 * T.CeldaInventario + 5 * T.PaddingInventario + 10, 1, -30),
		Position = UDim2.fromOffset(0, 30),
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 4,
		ScrollBarImageColor3 = C.Acento,
		ScrollBarImageTransparency = 0.5,
		ScrollingDirection = Enum.ScrollingDirection.Y,
		ZIndex = 4,
		Parent = vista,
	}) :: ScrollingFrame
	P.Relleno(rejilla, 2, 6, 2, 2)
	P.Crear("UIGridLayout", {
		CellSize = UDim2.fromOffset(T.CeldaInventario, T.CeldaInventario),
		CellPadding = UDim2.fromOffset(T.PaddingInventario, T.PaddingInventario),
		SortOrder = Enum.SortOrder.LayoutOrder,
		Parent = rejilla,
	})

	muneco = Muneco.Crear(vista, {
		Compacto = true,
		Tamano = UDim2.new(0, 190, 1, -30),
		Posicion = UDim2.new(1, 0, 0, 30) - UDim2.fromOffset(190, 0),
		AlPulsarSlot = alPulsarSlot,
		AlEntrarSlot = function(slot: string, boton: GuiObject)
			local id = EstadoUI.Equipado()[slot]
			if id and not fijado then
				local o = EstadoUI.Objeto(id)
				if o then
					Tooltip.Mostrar(o, boton)
				end
			end
		end,
		AlSalirSlot = function()
			if not fijado then
				Tooltip.Ocultar()
			end
		end,
	})

	EstadoUI.Cambio:Conectar(function(que: string)
		if que == "Equipo" or que == "Datos" then
			PanelInventario.Refrescar()
		end
	end)
	PanelInventario.Refrescar()
end

-- La vista se ve (o deja de verse): el personaje solo gira mientras se ve, y la ficha se cierra al salir.
function PanelInventario.Activar(visible: boolean)
	muneco.Activar(visible)
	if not visible then
		deseleccionar()
	end
end

PanelInventario.Deseleccionar = function()
	if muneco then
		deseleccionar()
	end
end

return PanelInventario
