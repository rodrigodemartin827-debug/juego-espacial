--!strict
--[[
	PanelTienda (cliente): el panel de compra de una tienda humana.

	Arriba, el nombre de la tienda y tus monedas. A la izquierda, lo que vende esa tienda (Tiendas/Datos/Catalogo); a la
	derecha, el artículo elegido: qué es, cuánto tienes, el precio (en verde si te llega, en rojo si no) y los botones de
	comprar. Para las mejoras de la nave se ve el efecto del nivel nuevo estadística a estadística.

	Es solo una vista: usa las MISMAS reglas que el servidor (Tiendas/Compras.Planificar) para pintar y activar los
	botones, pero quien decide es el servidor, que lo vuelve a comprobar todo (bando, persiana, distancia, monedas...).
	Se cierra sola si te alejas del mostrador o si baja la persiana (se acerca un monstruo).
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Catalogo = require(Shared.Tiendas.Datos.Catalogo)
local Compras = require(Shared.Tiendas.Compras)
local Config = require(Shared.Tiendas.Config)
local Estadisticas = require(Shared.Naves.Estadisticas)
local Mejoras = require(Shared.Naves.Datos.Mejoras)
local Objetos = require(Shared.Exploracion.Datos.Objetos)
local Avisos = require(script.Parent.Parent.Exploracion.Avisos)
local Estilo = require(script.Parent.Parent.Exploracion.Estilo)
local ServicioDatos = require(script.Parent.Parent.Servicios.ServicioDatos)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)

local PanelTienda = {}

-- Cantidades de los botones de compra de materiales.
local CANTIDADES = { 1, 5, 10 }

local pantalla: ScreenGui? = nil
local panel: Frame? = nil
local titulo: TextLabel? = nil
local lema: TextLabel? = nil
local monedas: TextLabel? = nil
local lista: ScrollingFrame? = nil
local detalle: Frame? = nil
local abierto = false
local tienda: Model? = nil -- la tienda abierta
local idTienda: string? = nil
local seleccionado: string? = nil
local vigilanciaPersiana: RBXScriptConnection? = nil

local function numero(valor: number): string
	if math.abs(valor - math.floor(valor + 0.5)) < 0.005 then
		return tostring(math.floor(valor + 0.5))
	end
	return string.format("%.1f", valor)
end

local function capacidadDe(datos: any): number
	return Estadisticas.Calcular(datos.MejorasNave).Capacidad
end

local function persianaBajada(): boolean
	return tienda ~= nil and tienda:GetAttribute(Config.AtributoPersiana) == true
end

local function planDe(datos: any, idArticulo: string, cantidad: number): Compras.Plan
	return Compras.Planificar(datos, idTienda or "", idArticulo, capacidadDe(datos), cantidad, persianaBajada())
end

-- Pide comprar al servidor.
local function comprar(cantidad: number)
	local datos, articulo = ServicioDatos.Obtener(), seleccionado
	if datos == nil or articulo == nil or tienda == nil then
		return
	end
	-- Aviso inmediato si no se puede (el servidor lo comprueba igualmente).
	local plan = planDe(datos, articulo, cantidad)
	if not plan.Ok then
		Avisos.Mostrar(Compras.Mensajes[plan.Motivo :: string], "Mal")
		return
	end
	if Catalogo.Articulos[articulo].Categoria == "Mejora" then
		ServicioRed.Enviar("ComprarArticulo", tienda, articulo)
	else
		ServicioRed.Enviar("ComprarArticulo", tienda, articulo, cantidad)
	end
end

local function fila(contenedor: Instance, texto: string, color: Color3, y: number): number
	local etiqueta = Estilo.Etiqueta(
		contenedor,
		texto,
		13,
		color,
		UDim2.new(1, 0, 0, Estilo.Texto(13) + 4),
		UDim2.fromOffset(0, y),
		false
	)
	etiqueta.TextWrapped = false
	return y + Estilo.Texto(13) + 5
end

-- Dibuja el artículo elegido en la parte derecha.
local function pintarDetalle()
	local contenedor, datos, idArticulo = detalle, ServicioDatos.Obtener(), seleccionado
	if contenedor == nil or datos == nil or idArticulo == nil then
		return
	end
	for _, hijo in contenedor:GetChildren() do
		hijo:Destroy()
	end

	local articulo = Catalogo.Articulos[idArticulo]
	local plan = planDe(datos, idArticulo, 1)
	local idMejora = articulo.Resultado.Mejora
	local nivel = if idMejora then Estadisticas.NivelValido(datos.MejorasNave[idMejora]) else 0

	local y = 0
	local nombre =
		Estilo.Etiqueta(contenedor, articulo.Nombre, 18, Estilo.TEXTO, UDim2.new(1, 0, 0, 24), UDim2.fromOffset(0, y))
	nombre.TextWrapped = false
	y += 26

	local subtitulo
	if idMejora then
		subtitulo = `Mejora de la nave · {Mejoras.Lista[idMejora].Nombre} nivel {nivel} → {math.min(
			nivel + 1,
			Mejoras.NivelMaximo
		)}`
	else
		local objeto = articulo.Resultado.Objeto :: string
		subtitulo = `Material · tienes {numero(datos.Inventario[objeto] or 0)}`
	end
	local etiquetaSub =
		Estilo.Etiqueta(contenedor, subtitulo, 12, Estilo.CIAN, UDim2.new(1, 0, 0, 16), UDim2.fromOffset(0, y))
	etiquetaSub.TextWrapped = false
	y += 20

	local descripcion = Estilo.Etiqueta(
		contenedor,
		articulo.Descripcion,
		12,
		Estilo.TEXTO_SUAVE,
		UDim2.new(1, 0, 0, 30),
		UDim2.fromOffset(0, y),
		false
	)
	descripcion.TextYAlignment = Enum.TextYAlignment.Top
	y += 36

	Estilo.Etiqueta(contenedor, "PRECIO", 11, Estilo.TEXTO_SUAVE, UDim2.new(1, 0, 0, 14), UDim2.fromOffset(0, y))
	y += 16
	local llega = datos.Monedas >= plan.PrecioUnidad
	y = fila(
		contenedor,
		`{numero(plan.PrecioUnidad)} monedas{if idMejora then "" else " / unidad"} · tienes {numero(datos.Monedas)}`,
		if llega then Estilo.VERDE else Estilo.ROJO,
		y
	)
	y += 6

	Estilo.Etiqueta(contenedor, "OBTIENES", 11, Estilo.TEXTO_SUAVE, UDim2.new(1, 0, 0, 14), UDim2.fromOffset(0, y))
	y += 16
	if idMejora then
		local ahora = Estadisticas.Calcular(datos.MejorasNave)
		local siguiente = Estadisticas.Calcular({ [idMejora] = math.min(nivel + 1, Mejoras.NivelMaximo) })
		for estadistica in Mejoras.Lista[idMejora].Efectos do
			local antes = (ahora :: any)[estadistica]
			local despues = (siguiente :: any)[estadistica]
			y = fila(
				contenedor,
				`{Estilo.NombresEstadisticas[estadistica] or estadistica}: {numero(antes)} → {numero(despues)}`,
				Estilo.TEXTO,
				y
			)
		end
	else
		local objeto = articulo.Resultado.Objeto :: string
		local info = Objetos.Lista[objeto]
		y = fila(
			contenedor,
			`{articulo.Resultado.Cantidad or 1} × {if info then info.Nombre else objeto}`,
			if info then Estilo.Hex(info.Color) else Estilo.TEXTO,
			y
		)
	end

	-- Botones: una mejora se compra de una en una; un material, de 1, 5 o 10.
	local alto = if Estilo.EsMovil then 38 else 32
	local cantidades = if idMejora then { 1 } else CANTIDADES
	local x = 0
	for _, cantidad in cantidades do
		local planCantidad = planDe(datos, idArticulo, cantidad)
		local texto = if cantidad == 1
			then `Comprar · {numero(planCantidad.Precio)}`
			else `× {cantidad} · {numero(planCantidad.Precio)}`
		-- En móvil el panel es más estrecho: botones más cortos y el texto se ajusta al botón.
		local ancho = if cantidad == 1
			then (if Estilo.EsMovil then 100 else 150)
			else (if Estilo.EsMovil then 70 else 100)
		local boton = Estilo.Boton(
			contenedor,
			texto,
			UDim2.fromOffset(ancho, alto),
			UDim2.new(0, x, 1, -alto),
			if planCantidad.Ok then Estilo.VERDE else Estilo.TEXTO_SUAVE,
			function()
				comprar(cantidad)
			end
		)
		boton.Name = `Comprar{cantidad}`
		boton.TextScaled = true
		local limite = Instance.new("UITextSizeConstraint")
		limite.MaxTextSize = Estilo.Texto(12)
		limite.Parent = boton
		local relleno = Instance.new("UIPadding")
		relleno.PaddingLeft = UDim.new(0, 6)
		relleno.PaddingRight = UDim.new(0, 6)
		relleno.Parent = boton
		x += ancho + 8
	end
	if not plan.Ok and plan.Motivo ~= nil then
		local motivo = Estilo.Etiqueta(
			contenedor,
			Compras.Mensajes[plan.Motivo],
			12,
			Estilo.AMARILLO,
			UDim2.new(1, 0, 0, 30),
			UDim2.new(0, 0, 1, -alto - 34),
			false
		)
		motivo.TextYAlignment = Enum.TextYAlignment.Bottom
	end
end

-- Lista de artículos de la izquierda.
local function pintarLista()
	local contenedor, datos, id = lista, ServicioDatos.Obtener(), idTienda
	if contenedor == nil or datos == nil or id == nil then
		return
	end
	for _, hijo in contenedor:GetChildren() do
		if hijo:IsA("TextButton") then
			hijo:Destroy()
		end
	end
	for indice, idArticulo in Catalogo.Tiendas[id].Articulos do
		local articulo = Catalogo.Articulos[idArticulo]
		local plan = planDe(datos, idArticulo, 1)
		local elegido = idArticulo == seleccionado
		local color = if plan.Ok then Estilo.VERDE elseif elegido then Estilo.CIAN else Estilo.TEXTO_SUAVE
		local boton = Instance.new("TextButton")
		boton.AutoButtonColor = true
		boton.BackgroundColor3 = if elegido then Color3.fromRGB(34, 44, 74) else Color3.fromRGB(22, 26, 44)
		boton.BorderSizePixel = 0
		boton.Size = UDim2.new(1, -6, 0, Estilo.Texto(13) + 16)
		boton.LayoutOrder = indice
		boton.Text =
			`{if articulo.Categoria == "Mejora" then "▲ " else ""}{articulo.Nombre} · {numero(plan.PrecioUnidad)}`
		boton.Font = Enum.Font.GothamBold
		boton.TextSize = Estilo.Texto(12)
		boton.TextColor3 = color
		boton.TextXAlignment = Enum.TextXAlignment.Left
		boton.TextTruncate = Enum.TextTruncate.AtEnd
		boton.Parent = contenedor
		Estilo.Redondear(boton, 6)
		local relleno = Instance.new("UIPadding")
		relleno.PaddingLeft = UDim.new(0, 8)
		relleno.PaddingRight = UDim.new(0, 6)
		relleno.Parent = boton
		boton.Activated:Connect(function()
			seleccionado = idArticulo
			pintarLista()
			pintarDetalle()
		end)
	end
end

local function refrescar()
	if not abierto then
		return
	end
	local datos = ServicioDatos.Obtener()
	if monedas and datos then
		monedas.Text = `{numero(datos.Monedas)} monedas`
	end
	pintarLista()
	pintarDetalle()
end

function PanelTienda.Cerrar()
	abierto = false
	tienda = nil
	if vigilanciaPersiana then
		vigilanciaPersiana:Disconnect()
		vigilanciaPersiana = nil
	end
	if panel then
		panel.Visible = false
	end
end

-- Distancia del jugador al mostrador de la tienda abierta (math.huge si no se puede medir).
local function distanciaAlMostrador(): number
	local personaje = Players.LocalPlayer.Character
	local raiz = if personaje then personaje:FindFirstChild("HumanoidRootPart") else nil
	local mostrador = if tienda then tienda:FindFirstChild("Mostrador") else nil
	if raiz == nil or not raiz:IsA("BasePart") or mostrador == nil or not mostrador:IsA("BasePart") then
		return math.huge
	end
	return ((raiz :: BasePart).Position - (mostrador :: BasePart).Position).Magnitude
end

-- Abre el panel de la tienda `modelo` (lo pide el servidor con AbrirTienda).
function PanelTienda.Abrir(modelo: Model)
	local id = modelo:GetAttribute(Config.AtributoTiendaId)
	if panel == nil or type(id) ~= "string" or Catalogo.Tiendas[id] == nil then
		return
	end
	if vigilanciaPersiana then
		vigilanciaPersiana:Disconnect()
	end
	tienda = modelo
	idTienda = id
	local datosTienda = Catalogo.Tiendas[id]
	if seleccionado == nil or table.find(datosTienda.Articulos, seleccionado) == nil then
		seleccionado = datosTienda.Articulos[1]
	end
	if titulo then
		titulo.Text = string.upper(datosTienda.Nombre)
	end
	if lema then
		lema.Text = datosTienda.Lema
	end
	abierto = true
	local marco = panel :: Frame
	marco.Visible = true
	refrescar()

	-- Si baja la persiana (se acerca un monstruo), la tienda cierra y el panel también.
	vigilanciaPersiana = modelo:GetAttributeChangedSignal(Config.AtributoPersiana):Connect(function()
		if modelo:GetAttribute(Config.AtributoPersiana) == true and tienda == modelo then
			PanelTienda.Cerrar()
			Avisos.Mostrar("¡Monstruo cerca! La tienda ha bajado la persiana", "Mal")
		end
	end)
	-- Se cierra sola si el jugador se aleja del mostrador.
	task.spawn(function()
		while abierto and tienda == modelo do
			if distanciaAlMostrador() > Config.AlcanceTienda * 1.5 then
				PanelTienda.Cerrar()
				return
			end
			task.wait(0.5)
		end
	end)
end

-- Resultado de un intento (del servidor).
function PanelTienda.AlRecibirResultado(idArticulo: string, ok: boolean, mensaje: string?)
	local articulo = Catalogo.Articulos[idArticulo]
	local nombre = if articulo then articulo.Nombre else idArticulo
	if ok then
		Avisos.Mostrar(`Comprado: {nombre}`, "Bien")
	else
		Avisos.Mostrar(mensaje or "No se pudo comprar", "Mal")
	end
	refrescar()
end

function PanelTienda.Iniciar()
	if pantalla then
		return
	end
	local nueva = Estilo.Pantalla("TiendaHumana", 19)
	nueva.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	pantalla = nueva

	local ancho = if Estilo.EsMovil then 460 else 640
	local marco = Estilo.Panel(nueva, UDim2.fromOffset(ancho, 400), UDim2.fromScale(0.5, 0.5), Estilo.AMARILLO)
	marco.AnchorPoint = Vector2.new(0.5, 0.5)
	marco.Visible = false
	panel = marco

	titulo = Estilo.Etiqueta(marco, "TIENDA", 16, Estilo.AMARILLO, UDim2.new(1, -200, 0, 22), UDim2.fromOffset(14, 8))
	lema =
		Estilo.Etiqueta(marco, "", 11, Estilo.TEXTO_SUAVE, UDim2.new(1, -200, 0, 14), UDim2.fromOffset(14, 30), false)
	local etiquetaMonedas =
		Estilo.Etiqueta(marco, "", 14, Estilo.AMARILLO, UDim2.fromOffset(140, 22), UDim2.new(1, -186, 0, 12))
	etiquetaMonedas.TextXAlignment = Enum.TextXAlignment.Right
	monedas = etiquetaMonedas
	Estilo.Boton(marco, "×", UDim2.fromOffset(28, 28), UDim2.new(1, -40, 0, 8), Estilo.ROJO, PanelTienda.Cerrar).TextSize =
		18

	local anchoLista = if Estilo.EsMovil then 160 else 210
	local desplazable = Instance.new("ScrollingFrame")
	desplazable.BackgroundTransparency = 1
	desplazable.BorderSizePixel = 0
	desplazable.Position = UDim2.fromOffset(12, 52)
	desplazable.Size = UDim2.new(0, anchoLista, 1, -64)
	desplazable.ScrollBarThickness = 4
	desplazable.CanvasSize = UDim2.new()
	desplazable.AutomaticCanvasSize = Enum.AutomaticSize.Y
	desplazable.Parent = marco
	local disposicion = Instance.new("UIListLayout")
	disposicion.Padding = UDim.new(0, 4)
	disposicion.SortOrder = Enum.SortOrder.LayoutOrder
	disposicion.Parent = desplazable
	lista = desplazable

	local derecha = Instance.new("Frame")
	derecha.BackgroundTransparency = 1
	derecha.Position = UDim2.new(0, anchoLista + 26, 0, 52)
	derecha.Size = UDim2.new(1, -(anchoLista + 40), 1, -64)
	derecha.Parent = marco
	detalle = derecha

	ServicioDatos.Actualizados:Conectar(refrescar)
end

return PanelTienda
