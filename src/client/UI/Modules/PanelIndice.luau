--!strict
--[[
	PanelIndice: el ÍNDICE (códex) de todo lo descubierto con el escáner.

	  [Criaturas 4] [Minerales 4] [Plantas 2] [Planetas 6]          DESCUBIERTOS: 3/4 ▬▬▬▬ 75%
	  ┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐     ┌ (imagen grande) ───────┐
	  │img ││img ││img ││ ?  ││ ?  ││ ?  │     │ MEDUSA DEL VACÍO       │
	  │Lobo││Roca││Cris││????││????││????│     │ Tipo, Peligro (estrellas), Hábitat │
	  └────┘└────┘└────┘└────┘└────┘└────┘     │ Drops con % · veces escaneado      │
	                                           │ "descripción en cursiva"          │

	Criaturas, plantas y minerales son REALES: salen de Exploracion/Datos/Especies y de los descubrimientos guardados
	del jugador (datos.Descubrimientos). Los planetas son de demostración hasta que exista el registro de descubrimientos.
]]

local Theme = require(script.Parent.Temas.EspacialTheme)
local IconBuilder = require(script.Parent.Iconos.IconBuilder)
local UITweens = require(script.Parent.Animaciones.UITweens)
local P = require(script.Parent.Componentes.Primitivas)
local Ventana = require(script.Parent.Componentes.Ventana)
local TabSelector = require(script.Parent.Componentes.TabSelector)
local EntradaIndice = require(script.Parent.Componentes.EntradaIndice)
local EstadoUI = require(script.Parent.EstadoUI)
local Contexto = require(script.Parent.Contexto)

local C = Theme.Colores
local A = Theme.Alpha

local PanelIndice = {}

local CATEGORIAS = { "Criaturas", "Minerales", "Plantas", "Planetas" }
local MINIMO_CASILLAS = 24 -- se rellena con "?" hasta esta cantidad para que la rejilla no quede vacía

local ventana: Ventana.Ventana = nil :: any
local textoProgreso: TextLabel = nil :: any
local rellenoProgreso: Frame = nil :: any
local rejilla: ScrollingFrame = nil :: any
local detalle: Frame = nil :: any
local categoria = "Criaturas"
local seleccionada = 1

local function pintarDetalle(entrada: EstadoUI.EntradaIndice?)
	for _, hijo in detalle:GetChildren() do
		if hijo:IsA("GuiObject") then
			hijo:Destroy()
		end
	end
	if entrada == nil then
		P.Etiqueta(
			detalle,
			"ESCANEA ALGO PARA VER SU FICHA",
			{ Posicion = UDim2.fromScale(0.5, 0.5), Ancla = Vector2.new(0.5, 0.5), Z = 4 }
		)
		return
	end
	local rareza = Theme.Rareza[entrada.Rareza] or Theme.Rareza.Comun
	local brillo = P.Marco(detalle, {
		Tamano = UDim2.fromOffset(132, 132),
		Posicion = UDim2.new(0.5, 0, 0, 14),
		Ancla = Vector2.new(0.5, 0),
		Color = rareza.Color,
		Transparencia = 0.9,
		Radio = UDim.new(0.5, 0),
		Z = 3,
	})
	UITweens.Pulso(brillo, "BackgroundTransparency", 0.93, 0.84, Theme.Tweens.PulsoLento)
	IconBuilder.Arte(detalle, entrada.A, {
		Tamano = 132,
		Posicion = UDim2.new(0.5, 0, 0, 14),
		Ancla = Vector2.new(0.5, 0),
		Z = 4,
		ColorRespaldo = rareza.Color,
	})
	P.Texto(detalle, {
		Texto = string.upper(entrada.N),
		Tamano = Theme.Texto.Destacado,
		Fuente = Theme.Fuentes.Negrita,
		Espaciado = true,
		Posicion = UDim2.new(0.5, 0, 0, 152),
		Ancla = Vector2.new(0.5, 0),
		Z = 4,
	})
	P.Texto(detalle, {
		Texto = string.upper(rareza.Nombre),
		Tamano = Theme.Texto.Mini + 0.5,
		Fuente = Theme.Fuentes.Negrita,
		Color = rareza.Color,
		Espaciado = true,
		Posicion = UDim2.new(0.5, 0, 0, 172),
		Ancla = Vector2.new(0.5, 0),
		Z = 4,
	})

	local filas = P.Marco(
		detalle,
		{ Nombre = "Filas", Tamano = UDim2.new(1, -28, 0, 100), Posicion = UDim2.fromOffset(14, 192), Z = 4 }
	)
	P.Lista(filas, Enum.FillDirection.Vertical, 5)
	local function fila(nombre: string, orden: number): Frame
		local marco = P.Marco(filas, { Nombre = nombre, Tamano = UDim2.new(1, 0, 0, 12), Orden = orden, Z = 4 })
		marco.AutomaticSize = Enum.AutomaticSize.Y
		P.Texto(marco, {
			Texto = nombre,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Negrita,
			Color = C.TextoSecundario,
			Transparencia = A.TextoSecundario,
			Espaciado = true,
			Z = 5,
		})
		return marco
	end
	local function valor(marco: Frame, texto: string)
		P.Texto(marco, {
			Texto = texto,
			Rico = true,
			Tamano = Theme.Texto.Pequeno + 0.5,
			Fuente = Theme.Fuentes.Titulo,
			AlineacionX = Enum.TextXAlignment.Right,
			Caja = UDim2.new(1, -70, 0, 0),
			Posicion = UDim2.fromScale(1, 0),
			Ancla = Vector2.new(1, 0),
			Envolver = true,
			Z = 5,
		}).AutomaticSize =
			Enum.AutomaticSize.Y
	end
	valor(fila("TIPO", 1), entrada.Tipo)
	-- Peligro: 5 estrellas custom (llenas en naranja, vacías en gris).
	local peligro = fila("PELIGRO", 2)
	local estrellas = P.Marco(
		peligro,
		{ Tamano = UDim2.fromOffset(60, 11), Posicion = UDim2.fromScale(1, 0), Ancla = Vector2.new(1, 0), Z = 5 }
	)
	P.Lista(estrellas, Enum.FillDirection.Horizontal, 1, Enum.HorizontalAlignment.Right)
	for k = 1, 5 do
		local llena = k <= entrada.Peligro
		IconBuilder.Icono(
			estrellas,
			if llena then "ui_estrella" else "ui_estrella_vacia",
			{ Tamano = 11, Color = if llena then C.Fuerza else C.GrisOscuro, Orden = k, Z = 6 }
		)
	end
	valor(fila("HÁBITAT", 3), entrada.Habitat)
	local drops = {}
	for _, d in entrada.Drops do
		table.insert(drops, `{d.Nombre} <font color="#{C.Acento:ToHex()}">({d.Porcentaje}%)</font>`)
	end
	valor(
		fila(if categoria == "Planetas" then "RECURSOS" else "DROPS", 4),
		if #drops > 0 then table.concat(drops, "\n") else "—"
	)
	valor(fila("ESCANEADO", 5), `{entrada.Veces} {if entrada.Veces == 1 then "vez" else "veces"}`)

	-- Descripción (lore) en cursiva, abajo.
	local lore = P.Marco(detalle, {
		Nombre = "Lore",
		Tamano = UDim2.new(1, -28, 0, 0),
		Posicion = UDim2.new(0, 14, 1, -14),
		Ancla = Vector2.new(0, 1),
		Color = C.FondoProfundo,
		Transparencia = 0.5,
		Radio = UDim.new(0, 6),
		Z = 4,
	})
	lore.AutomaticSize = Enum.AutomaticSize.Y
	P.Marco(lore, { Tamano = UDim2.new(0, 2, 1, 0), Color = C.Acento, Transparencia = A.BordeActivo, Z = 5 })
	P.Relleno(lore, 8, 10)
	P.Texto(lore, {
		Texto = `"{entrada.Lore}"`,
		Tamano = Theme.Texto.Pequeno + 0.5,
		Fuente = Theme.Fuentes.Cursiva,
		Color = C.TextoPrincipal,
		Transparencia = 0.4,
		Caja = UDim2.new(1, 0, 0, 0),
		Envolver = true,
		Z = 5,
	}).AutomaticSize =
		Enum.AutomaticSize.Y
end

function PanelIndice.Refrescar()
	for _, hijo in rejilla:GetChildren() do
		if hijo:IsA("GuiObject") then
			hijo:Destroy()
		end
	end
	local datos = EstadoUI.Indice(categoria)
	local descubiertas = #datos.Lista
	local porcentaje = if datos.Total > 0 then descubiertas / datos.Total * 100 else 0
	local textoPorcentaje = if porcentaje < 10 and porcentaje > 0
		then P.Decimal(math.floor(porcentaje * 10 + 0.5) / 10)
		else tostring(math.floor(porcentaje + 0.5))
	textoProgreso.Text = `DESCUBIERTOS: <font color="#{C.TextoPrincipal:ToHex()}">{descubiertas}/{datos.Total}</font>`
	UITweens.Barra(rellenoProgreso, porcentaje / 100)
	local pc = textoProgreso.Parent and textoProgreso.Parent:FindFirstChild("Porcentaje")
	if pc and pc:IsA("TextLabel") then
		pc.Text = `{textoPorcentaje}%`
	end

	if seleccionada > descubiertas then
		seleccionada = 1
	end
	local tarjetas: { EntradaIndice.EntradaIndice } = {}
	for i, entrada in datos.Lista do
		local tarjeta = EntradaIndice.Crear(rejilla, {
			Nombre = entrada.N,
			Arte = entrada.A,
			Rareza = entrada.Rareza,
			Orden = i,
			AlPulsar = function()
				seleccionada = i
				for k, t in tarjetas do
					t.Seleccionar(k == i)
				end
				pintarDetalle(entrada)
			end,
		})
		tarjeta.Seleccionar(i == seleccionada)
		table.insert(tarjetas, tarjeta)
	end
	local ocultas = math.min(datos.Ocultas, math.max(0, MINIMO_CASILLAS - descubiertas))
	for i = 1, ocultas do
		EntradaIndice.Crear(rejilla, { Orden = descubiertas + i })
	end
	pintarDetalle(datos.Lista[seleccionada])
end

function PanelIndice.Iniciar(contexto: Contexto.Contexto)
	ventana = Ventana.Crear(contexto.Raiz, {
		Nombre = "Indice",
		Titulo = "ÍNDICE",
		Subtitulo = "CÓDEX DE DESCUBRIMIENTOS",
		Icono = "sidebar_indice",
		AlCerrar = contexto.Cerrar,
	})
	local cuerpo = ventana.Cuerpo
	local opciones: { TabSelector.Opcion } = {}
	for _, c in CATEGORIAS do
		table.insert(opciones, { Id = c, Texto = c })
	end
	TabSelector.Crear(cuerpo, {
		Opciones = opciones,
		Inicial = categoria,
		Posicion = UDim2.fromOffset(12, 13),
		AlCambiar = function(id: string)
			categoria = id
			seleccionada = 1
			PanelIndice.Refrescar()
		end,
	})

	local progreso = P.Marco(cuerpo, {
		Nombre = "Progreso",
		Tamano = UDim2.fromOffset(320, 24),
		Posicion = UDim2.new(1, -12, 0, 13),
		Ancla = Vector2.new(1, 0),
		Z = 3,
	})
	textoProgreso = P.Texto(progreso, {
		Texto = "",
		Rico = true,
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.TextoPrincipal,
		Transparencia = A.TextoMedio,
		Posicion = UDim2.new(1, -206, 0.5, 0),
		Ancla = Vector2.new(1, 0.5),
		Z = 4,
	})
	local _, relleno = P.BarraProgreso(
		progreso,
		{ Tamano = UDim2.fromOffset(160, 6), Posicion = UDim2.new(1, -40, 0.5, 0), Ancla = Vector2.new(1, 0.5), Z = 4 }
	)
	rellenoProgreso = relleno
	P.Texto(progreso, {
		Nombre = "Porcentaje",
		Texto = "",
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Acento,
		Posicion = UDim2.new(1, 0, 0.5, 0),
		Ancla = Vector2.new(1, 0.5),
		Z = 4,
	})

	rejilla = P.Crear("ScrollingFrame", {
		Name = "Rejilla",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = UDim2.new(0, 556, 1, -60),
		Position = UDim2.fromOffset(12, 48),
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 4,
		ScrollBarImageColor3 = C.Acento,
		ScrollBarImageTransparency = 0.5,
		ZIndex = 3,
		Parent = cuerpo,
	}) :: ScrollingFrame
	P.Relleno(rejilla, 2)
	P.Crear("UIGridLayout", {
		CellSize = UDim2.fromOffset(86, 104),
		CellPadding = UDim2.fromOffset(6, 6),
		SortOrder = Enum.SortOrder.LayoutOrder,
		Parent = rejilla,
	})

	detalle = P.Caja(cuerpo, {
		Nombre = "Detalle",
		Tamano = UDim2.new(0, 272, 1, -60),
		Posicion = UDim2.new(1, -12, 0, 48),
		Ancla = Vector2.new(1, 0),
		Z = 3,
	})

	EstadoUI.Cambio:Conectar(function(que: string)
		if que == "Datos" and ventana.EstaAbierta() then
			PanelIndice.Refrescar()
		end
	end)
	PanelIndice.Refrescar()
end

function PanelIndice.Mostrar()
	PanelIndice.Refrescar()
	ventana.Abrir()
end

function PanelIndice.Ocultar()
	ventana.Cerrar()
end

return PanelIndice
