--!strict
--[[
	PanelTienda: la TIENDA (botón dorado de la barra lateral, siempre visible).

	  (moneda) 12.450 MONEDAS   (gema) 34 GEMAS [+]        [Destacado] [Armas] [Armadura] [Cosméticos] [Packs]
	  ┌──────── DESTACADO ────────┐┌──────────┐┌──────────┐┌──────────┐
	  │ NUEVO   (arte grande)     ││ OFERTA   ││          ││          │
	  │ Skin Nebula · desc · fin  ││ Espada   ││ Casco    ││ x2       │
	  │ (gema) 15  [COMPRAR]      ││ 5.000    ││ 3.200    ││ R$ 199   │
	  └───────────────────────────┘└──────────┘└──────────┘└──────────┘
	  [COMPRAR GEMAS — Robux]   Sin ventajas de pago: con gemas y Robux solo cosméticos y pases de comodidad.

	  - Monedas (se ganan jugando) en cian; gemas (premium) y Robux en dorado. Botón COMPRAR del mismo color.
	  - Insignias OFERTA (rojo-dorado, con el precio anterior tachado) y NUEVO (cian).
	  - COMPRAR pide confirmación ("¿Comprar X por Y?") o avisa si no llega el saldo.
	  - COMPRAR GEMAS abre la compra de Roblox (MarketplaceService) con los productos de ConfigUI.ProductosGemas.

	Sin pay-to-win (CLAUDE.md): con gemas o Robux solo hay cosméticos y pases de comodidad; las armas y armaduras
	se compran con monedas, que se ganan jugando.
	TODO(servidor): las compras con monedas y gemas deben pedirse al servidor (que valida saldo y entrega); hoy solo
	existe la compra de las tiendas físicas del planeta humano (Tiendas/Compras), con otro catálogo.
]]

local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")

local Theme = require(script.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Componentes.Primitivas)
local Ventana = require(script.Parent.Componentes.Ventana)
local TabSelector = require(script.Parent.Componentes.TabSelector)
local Modal = require(script.Parent.Componentes.Modal)
local ConfigUI = require(script.Parent.Datos.ConfigUI)
local DatosDemo = require(script.Parent.Datos.DatosDemo)
local EstadoUI = require(script.Parent.EstadoUI)
local Contexto = require(script.Parent.Contexto)

local C = Theme.Colores
local A = Theme.Alpha

local PanelTienda = {}

local ANCHO_TARJETA, ALTO_TARJETA = 158, 222

local ctx: Contexto.Contexto = nil :: any
local ventana: Ventana.Ventana = nil :: any
local rejilla: ScrollingFrame = nil :: any
local textoMonedas: TextLabel = nil :: any
local textoGemas: TextLabel = nil :: any
local categoria = DatosDemo.Tienda.Categorias[1]

-- Icono, color y estilo de botón de cada moneda.
local MONEDAS: { [string]: { Icono: string?, Color: Color3, Estilo: P.EstiloBoton, Nombre: string } } = {
	Monedas = { Icono = "ui_moneda", Color = C.Acento, Estilo = "Cian", Nombre = "monedas" },
	Gemas = { Icono = "ui_gema", Color = C.Dorado, Estilo = "Dorado", Nombre = "gemas" },
	Robux = { Icono = nil, Color = C.Dorado, Estilo = "Dorado", Nombre = "Robux" },
}

-- ===== Compras =====

local function saldo(moneda: string): number
	if moneda == "Monedas" then
		return EstadoUI.Jugador().Monedas
	elseif moneda == "Gemas" then
		return EstadoUI.Gemas()
	end
	return math.huge
end

local function precioTexto(producto: DatosDemo.Producto): string
	local m = MONEDAS[producto.Moneda]
	return if producto.Moneda == "Robux"
		then `R$ {P.Numero(producto.Precio)}`
		else `{P.Numero(producto.Precio)} {m.Nombre}`
end

local function comprar(producto: DatosDemo.Producto)
	local m = MONEDAS[producto.Moneda]
	-- Pases de juego: los vende Roblox.
	if producto.Moneda == "Robux" then
		local id = ConfigUI.PasesJuego[producto.Id] or 0
		if id > 0 then
			MarketplaceService:PromptGamePassPurchase(Players.LocalPlayer, id)
		else
			ctx.Notificar({
				Titulo = producto.N,
				Texto = "Falta el ID del pase en ConfigUI.PasesJuego",
				Color = C.Dorado,
				Arte = producto.A,
			})
		end
		return
	end
	local disponible = saldo(producto.Moneda)
	if disponible < producto.Precio then
		Modal.Confirmar({
			Titulo = "SALDO INSUFICIENTE",
			Texto = `Te faltan <b>{P.Numero(producto.Precio - disponible)} {m.Nombre}</b> para comprar <b>{producto.N}</b>.`,
			Arte = producto.A,
			Color = C.Peligro,
			TextoNo = "CERRAR",
		})
		return
	end
	Modal.Confirmar({
		Titulo = "¿CONFIRMAR COMPRA?",
		Texto = `¿Comprar <b>{producto.N}</b> por <font color="#{m.Color:ToHex()}"><b>{precioTexto(producto)}</b></font>?`,
		Arte = producto.A,
		Color = m.Color,
		TextoSi = "COMPRAR",
		EstiloSi = m.Estilo,
		AlSi = function()
			-- TODO(servidor): enviar la compra; el servidor cobra, entrega y reenvía los datos.
			ctx.Notificar({
				Titulo = "Compra pendiente del servidor",
				Texto = producto.N,
				Color = Theme.ColorRareza(producto.Rareza),
				Arte = producto.A,
			})
		end,
	})
end

local function comprarGemas()
	Modal.Confirmar({
		Titulo = "COMPRAR GEMAS",
		Texto = "Se abrirá la ventana de compra de Roblox.",
		Icono = "ui_gema",
		Color = C.Dorado,
		TextoNo = "CERRAR",
		Extra = function(marco: Frame, cerrar: () -> ())
			local fila = P.Marco(marco, { Tamano = UDim2.new(1, 0, 0, 62), Z = 83 })
			P.Lista(fila, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Center)
			for i, paquete in ConfigUI.ProductosGemas do
				local boton = P.Crear("TextButton", {
					Name = `Paquete{i}`,
					Text = "",
					AutoButtonColor = false,
					Size = UDim2.fromOffset(84, 62),
					BackgroundColor3 = C.Dorado,
					BackgroundTransparency = 0.92,
					LayoutOrder = i,
					ZIndex = 84,
					Parent = fila,
				}) :: TextButton
				P.Esquinas(boton, UDim.new(0, 7))
				P.Borde(boton, C.Dorado, 0.65)
				IconBuilder.Icono(boton, "ui_gema", {
					Tamano = 20,
					Color = C.Dorado,
					Posicion = UDim2.new(0.5, 0, 0, 8),
					Ancla = Vector2.new(0.5, 0),
					Z = 85,
				})
				P.Texto(boton, {
					Texto = P.Numero(paquete.Gemas),
					Tamano = Theme.Texto.Grande,
					Fuente = Theme.Fuentes.Negrita,
					Posicion = UDim2.new(0.5, 0, 0, 30),
					Ancla = Vector2.new(0.5, 0),
					Z = 85,
				})
				P.Texto(boton, {
					Texto = `{paquete.Robux} Robux`,
					Tamano = Theme.Texto.Mini + 0.5,
					Fuente = Theme.Fuentes.Negrita,
					Color = C.TextoSecundario,
					Transparencia = A.TextoSecundario,
					Posicion = UDim2.new(0.5, 0, 0, 45),
					Ancla = Vector2.new(0.5, 0),
					Z = 85,
				})
				UITweens.Hover(boton, 0.82)
				boton.Activated:Connect(function()
					cerrar()
					if paquete.ProductoId > 0 then
						MarketplaceService:PromptProductPurchase(Players.LocalPlayer, paquete.ProductoId)
					else
						ctx.Notificar({
							Titulo = "Gemas",
							Texto = "Falta el ProductoId en ConfigUI.ProductosGemas",
							Color = C.Dorado,
							Icono = "ui_gema",
						})
					end
				end)
			end
		end,
	})
end

-- ===== Tarjetas =====

local function tarjeta(producto: DatosDemo.Producto, orden: number, heroe: boolean)
	local rareza = Theme.Rareza[producto.Rareza] or Theme.Rareza.Comun
	local m = MONEDAS[producto.Moneda]
	local marco = P.Marco(rejilla, {
		Nombre = producto.Id,
		Tamano = UDim2.fromOffset(if heroe then ANCHO_TARJETA * 2 + 10 else ANCHO_TARJETA, ALTO_TARJETA),
		Color = C.Fondo3,
		Transparencia = 0.1,
		Radio = UDim.new(0, 9),
		Recortar = true,
		Orden = orden,
		Z = 4,
	})
	P.Degradado(marco, ColorSequence.new(C.Fondo3, C.FondoProfundo), 90)
	local borde = P.Borde(marco, rareza.Color, 0.3, Theme.Tamanos.TrazoActivo)

	-- Escaparate: brillo del color de la rareza detrás del arte y una sombra elíptica.
	local escaparate = P.Marco(marco, {
		Nombre = "Escaparate",
		Tamano = if heroe then UDim2.new(0.52, 0, 1, 0) else UDim2.new(1, 0, 0, 112),
		Z = 4,
	})
	local brillo = P.Marco(escaparate, {
		Tamano = UDim2.fromOffset(if heroe then 150 else 100, if heroe then 150 else 100),
		Posicion = UDim2.fromScale(0.5, 0.55),
		Ancla = Vector2.new(0.5, 0.5),
		Color = rareza.Color,
		Transparencia = 0.8,
		Radio = UDim.new(0.5, 0),
		Z = 4,
	})
	P.Degradado(
		brillo,
		ColorSequence.new(rareza.Color),
		0,
		NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0.85),
			NumberSequenceKeypoint.new(0.5, 0.55),
			NumberSequenceKeypoint.new(1, 0.85),
		})
	)
	P.Marco(escaparate, {
		Tamano = UDim2.new(0.6, 0, 0, 8),
		Posicion = UDim2.new(0.5, 0, 1, -8),
		Ancla = Vector2.new(0.5, 1),
		Color = rareza.Color,
		Transparencia = 0.75,
		Radio = UDim.new(0.5, 0),
		Z = 4,
	})
	local arte = IconBuilder.Arte(escaparate, producto.A, {
		Tamano = if heroe then 150 else 92,
		Posicion = UDim2.fromScale(0.5, 0.52),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 5,
		ColorRespaldo = rareza.Color,
	})

	-- Insignias.
	if producto.Oferta and producto.Antes then
		local insignia = P.Texto(marco, {
			Texto = `OFERTA -{math.floor((1 - producto.Precio / producto.Antes) * 100 + 0.5)}%`,
			Tamano = Theme.Texto.Micro + 0.5,
			Fuente = Theme.Fuentes.Negrita,
			Espaciado = true,
			Posicion = UDim2.fromOffset(7, 7),
			Z = 7,
		})
		insignia.BackgroundColor3 = C.Blanco
		insignia.BackgroundTransparency = 0
		P.Degradado(insignia, ColorSequence.new(C.Peligro, C.Dorado), 0)
		P.Esquinas(insignia, UDim.new(0, 4))
		P.Relleno(insignia, 2, 6)
	elseif producto.Nuevo then
		local insignia = P.Texto(marco, {
			Texto = "NUEVO",
			Tamano = Theme.Texto.Micro + 0.5,
			Fuente = Theme.Fuentes.Negrita,
			Color = C.TextoSobreAcento,
			Espaciado = true,
			Posicion = UDim2.fromOffset(7, 7),
			Z = 7,
		})
		insignia.BackgroundColor3 = C.Acento
		insignia.BackgroundTransparency = 0
		P.Esquinas(insignia, UDim.new(0, 4))
		P.Relleno(insignia, 2, 6)
	end

	-- Información y botón.
	local info = P.Marco(marco, {
		Nombre = "Info",
		Tamano = if heroe then UDim2.new(0.48, -14, 1, -70) else UDim2.new(1, -20, 0, ALTO_TARJETA - 112 - 56),
		Posicion = if heroe then UDim2.new(0.52, 4, 0, 14) else UDim2.fromOffset(10, 112),
		Z = 5,
	})
	P.Lista(info, Enum.FillDirection.Vertical, 3)
	P.Texto(info, {
		Texto = string.upper(rareza.Nombre),
		Tamano = Theme.Texto.Micro,
		Fuente = Theme.Fuentes.Negrita,
		Color = rareza.Color,
		Espaciado = true,
		Orden = 1,
		Z = 6,
	})
	P.Texto(info, {
		Texto = producto.N,
		Tamano = if heroe then Theme.Texto.Destacado + 1 else Theme.Texto.Medio + 0.5,
		Fuente = Theme.Fuentes.Negrita,
		Orden = 2,
		Z = 6,
	})
	P.Texto(info, {
		Texto = producto.Sub,
		Tamano = Theme.Texto.Mini + 0.5,
		Fuente = Theme.Fuentes.Medio,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Orden = 3,
		Z = 6,
	})
	if heroe and producto.Desc then
		local desc = P.Texto(info, {
			Texto = producto.Desc,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Medio,
			Color = C.TextoPrincipal,
			Transparencia = A.TextoMedio,
			Caja = UDim2.new(1, 0, 0, 0),
			Envolver = true,
			Orden = 4,
			Z = 6,
		})
		desc.AutomaticSize = Enum.AutomaticSize.Y
		if producto.Fin then
			P.Texto(info, {
				Texto = producto.Fin,
				Tamano = Theme.Texto.Mini + 0.5,
				Fuente = Theme.Fuentes.Negrita,
				Color = C.Dorado,
				Espaciado = true,
				Orden = 5,
				Z = 6,
			})
		end
	end

	-- Precio (con el anterior tachado si está de oferta) y botón COMPRAR, abajo.
	local abajo = P.Marco(marco, {
		Nombre = "Compra",
		Tamano = if heroe then UDim2.new(0.48, -18, 0, 44) else UDim2.new(1, -20, 0, 44),
		Posicion = if heroe then UDim2.new(0.52, 4, 1, -12) else UDim2.new(0, 10, 1, -10),
		Ancla = Vector2.new(0, 1),
		Z = 6,
	})
	local precio = P.Marco(abajo, { Tamano = UDim2.new(1, 0, 0, 14), Z = 6 })
	P.Lista(precio, Enum.FillDirection.Horizontal, 4, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	if m.Icono then
		IconBuilder.Icono(precio, m.Icono, { Tamano = 12, Color = m.Color, Orden = 1, Z = 7 })
	else
		P.Texto(precio, {
			Texto = "R$",
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Negrita,
			Color = m.Color,
			Orden = 1,
			Z = 7,
		})
	end
	P.Texto(precio, {
		Texto = P.Numero(producto.Precio) .. (if producto.Antes
			then `  <font size="{Theme.Texto.Pequeno}" transparency="0.55"><s>{P.Numero(producto.Antes)}</s></font>`
			else ""),
		Rico = true,
		Tamano = Theme.Texto.Grande,
		Fuente = Theme.Fuentes.Negrita,
		Orden = 2,
		Z = 7,
	})
	P.Boton(abajo, {
		Texto = "COMPRAR",
		Estilo = m.Estilo,
		Tamano = UDim2.new(1, 0, 0, 24),
		Posicion = UDim2.fromScale(0, 1),
		Ancla = Vector2.new(0, 1),
		Z = 7,
		AlPulsar = function()
			comprar(producto)
		end,
	})

	-- Hover de la tarjeta: sube el borde y el arte crece un poco.
	local escalaArte = UITweens.EscalaDe(arte)
	marco.MouseEnter:Connect(function()
		UITweens.Tween(borde, Theme.Tweens.Rapido, { Transparency = 0 })
		UITweens.Tween(escalaArte, Theme.Tweens.Rapido, { Scale = 1.06 })
		UITweens.Tween(arte, Theme.Tweens.Rapido, { Rotation = -2 })
	end)
	marco.MouseLeave:Connect(function()
		UITweens.Tween(borde, Theme.Tweens.Rapido, { Transparency = 0.3 })
		UITweens.Tween(escalaArte, Theme.Tweens.Rapido, { Scale = 1 })
		UITweens.Tween(arte, Theme.Tweens.Rapido, { Rotation = 0 })
	end)
end

function PanelTienda.Refrescar()
	textoMonedas.Text = P.Numero(EstadoUI.Jugador().Monedas)
	textoGemas.Text = P.Numero(EstadoUI.Gemas())
	for _, hijo in rejilla:GetChildren() do
		if hijo:IsA("GuiObject") then
			hijo:Destroy()
		end
	end
	local orden = 0
	for _, producto in DatosDemo.Tienda.Productos do
		if table.find(producto.Cat, categoria) then
			orden += 1
			tarjeta(producto, orden, producto.Heroe == true and categoria == "Destacado")
		end
	end
end

-- Pastilla de moneda (icono + cantidad + nombre).
local function pastilla(
	padre: Instance,
	icono: string,
	color: Color3,
	nombre: string,
	orden: number,
	conMas: boolean
): TextLabel
	local marco = P.Marco(padre, {
		Tamano = UDim2.fromOffset(0, 26),
		Color = C.FondoProfundo,
		Transparencia = 0.3,
		Radio = UDim.new(1, 0),
		Orden = orden,
		Z = 4,
	})
	marco.AutomaticSize = Enum.AutomaticSize.X
	P.Borde(marco, color, 0.2)
	P.Relleno(marco, 0, 10, 0, 6)
	P.Lista(marco, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	IconBuilder.Icono(marco, icono, { Tamano = 16, Color = color, Orden = 1, Z = 5 })
	local valor =
		P.Texto(marco, { Texto = "0", Tamano = Theme.Texto.Grande, Fuente = Theme.Fuentes.Negrita, Orden = 2, Z = 5 })
	P.Texto(marco, {
		Texto = nombre,
		Tamano = Theme.Texto.Mini,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Espaciado = true,
		Orden = 3,
		Z = 5,
	})
	if conMas then
		local mas = P.Boton(marco, {
			Texto = "+",
			Estilo = "Dorado",
			Tamano = UDim2.fromOffset(16, 16),
			TamanoTexto = Theme.Texto.Titulo,
			Orden = 4,
			Z = 5,
			AlPulsar = comprarGemas,
		})
		local esquina = mas:FindFirstChildOfClass("UICorner")
		if esquina then
			esquina.CornerRadius = UDim.new(1, 0)
		end
	end
	return valor
end

function PanelTienda.Iniciar(contexto: Contexto.Contexto)
	ctx = contexto
	ventana = Ventana.Crear(contexto.Raiz, {
		Nombre = "Tienda",
		Titulo = "TIENDA",
		Icono = "sidebar_tienda",
		ColorIcono = C.Dorado,
		AlCerrar = contexto.Cerrar,
	})
	local cuerpo = ventana.Cuerpo
	local arriba = P.Marco(
		cuerpo,
		{ Nombre = "Arriba", Tamano = UDim2.new(1, -24, 0, 28), Posicion = UDim2.fromOffset(12, 12), Z = 3 }
	)
	local monedas = P.Marco(arriba, { Tamano = UDim2.fromOffset(360, 28), Z = 3 })
	P.Lista(monedas, Enum.FillDirection.Horizontal, 10, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	textoMonedas = pastilla(monedas, "ui_moneda", C.Acento, "MONEDAS", 1, false)
	textoGemas = pastilla(monedas, "ui_gema", C.Dorado, "GEMAS", 2, true)

	local opciones: { TabSelector.Opcion } = {}
	for _, c in DatosDemo.Tienda.Categorias do
		table.insert(opciones, { Id = c, Texto = c })
	end
	local pestanas = TabSelector.Crear(arriba, {
		Opciones = opciones,
		Inicial = categoria,
		Posicion = UDim2.fromScale(1, 0.5),
		Ancla = Vector2.new(1, 0.5),
		AlCambiar = function(id: string)
			categoria = id
			PanelTienda.Refrescar()
		end,
	})
	pestanas.Marco.AnchorPoint = Vector2.new(1, 0.5)

	rejilla = P.Crear("ScrollingFrame", {
		Name = "Productos",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = UDim2.new(1, -24, 1, -108),
		Position = UDim2.fromOffset(12, 52),
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 4,
		ScrollBarImageColor3 = C.Acento,
		ScrollBarImageTransparency = 0.5,
		ZIndex = 3,
		Parent = cuerpo,
	}) :: ScrollingFrame
	P.Relleno(rejilla, 2)
	local disposicion = P.Lista(rejilla, Enum.FillDirection.Horizontal, 10)
	disposicion.Wraps = true

	local pie = P.Marco(cuerpo, {
		Nombre = "Pie",
		Tamano = UDim2.new(1, -24, 0, 32),
		Posicion = UDim2.new(0, 12, 1, -12),
		Ancla = Vector2.new(0, 1),
		Z = 3,
	})
	P.Boton(pie, {
		Texto = "COMPRAR GEMAS — Robux",
		Estilo = "Dorado",
		Tamano = UDim2.fromOffset(230, 32),
		TamanoTexto = Theme.Texto.Medio,
		Z = 4,
		AlPulsar = comprarGemas,
	})
	P.Texto(pie, {
		Texto = `<font color="#{C.Exito:ToHex()}"><b>Sin ventajas de pago.</b></font> Con gemas y Robux solo se compran cosméticos y pases de comodidad; las armas y armaduras se consiguen jugando.`,
		Rico = true,
		Tamano = Theme.Texto.Mini + 0.5,
		Fuente = Theme.Fuentes.Medio,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Caja = UDim2.new(1, -250, 1, 0),
		Posicion = UDim2.fromOffset(244, 0),
		Envolver = true,
		Z = 4,
	})

	EstadoUI.Cambio:Conectar(function(que: string)
		if que == "Datos" and ventana.EstaAbierta() then
			textoMonedas.Text = P.Numero(EstadoUI.Jugador().Monedas)
		end
	end)
	PanelTienda.Refrescar()
end

function PanelTienda.Mostrar()
	PanelTienda.Refrescar()
	ventana.Abrir()
end

function PanelTienda.Ocultar()
	ventana.Cerrar()
end

return PanelTienda
