--!strict
--[[
	PanelPersonaje: pantalla PERSONAJE (botón de la barra lateral o tecla P). Sigue el diseño de Vox Seas:

	  ┌ PERSONAJE ───────────────────────────────────────────────────────────── [P] [X] ┐
	  │ [NIVEL 127] Rodrixx_777                         [LOGROS][PODERES][RANKED] │ TU RAZA  │
	  │             ARBUSTIX ▬▬▬▬ XP                                              │ (icono)  │
	  │ [Atributos] [Inventario] [Builds]                                         │ Humano   │
	  │ [CAS]          [AMU]   ┌ ESTADÍSTICAS ─── PUNTOS: 3 ┐                    │ Pasivas  │
	  │ [ARM] (pers.)  [ANI]   │ FUERZA      45(+12)        │                    │ ...      │
	  │ [ESP]          [CIN]   │ ...                        │                    │ SALUD    │
	  │ [ARM]          [BOT]   │            [EDITAR]        │                    │ ...      │
	  └──────────────────────────────────────────────────────────────────────────────────┘

	Pestañas con fundido cruzado (0,2 s): Atributos (muñeco + estadísticas), Inventario (PanelInventario) y Builds.
	EDITAR enseña los botones + y − de cada estadística y se convierte en CONFIRMAR.
]]

local Theme = require(script.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Componentes.Primitivas)
local Ventana = require(script.Parent.Componentes.Ventana)
local TabSelector = require(script.Parent.Componentes.TabSelector)
local StatRow = require(script.Parent.Componentes.StatRow)
local Muneco = require(script.Parent.Componentes.Muneco)
local Tooltip = require(script.Parent.Componentes.Tooltip)
local PanelInventario = require(script.Parent.PanelInventario)
local EstadoUI = require(script.Parent.EstadoUI)
local DatosDemo = require(script.Parent.Datos.DatosDemo)
local Contexto = require(script.Parent.Contexto)

local C = Theme.Colores
local A = Theme.Alpha

local PanelPersonaje = {}

local SUBTITULOS =
	{ atributos = "EQUIPO Y ATRIBUTOS", inventario = "BODEGA Y EQUIPO", builds = "CONFIGURACIONES GUARDADAS" }

local ctx: Contexto.Contexto = nil :: any
local ventana: Ventana.Ventana = nil :: any
local pestanas: TabSelector.TabSelector = nil :: any
local vistas: { [string]: Frame } = {}
local vistaActual = "atributos"
local muneco: Muneco.Muneco = nil :: any

-- Cabecera
local textoNivel: TextLabel = nil :: any
local textoNombre: TextLabel = nil :: any
local textoXP: TextLabel = nil :: any
local rellenoXP: Frame = nil :: any

-- Estadísticas
local filasStats: { [string]: StatRow.StatRow } = {}
local textoPuntos: TextLabel = nil :: any
local botonEditar: TextButton = nil :: any
local botonCancelar: TextButton = nil :: any
local editando = false
local reparto: { [string]: number } = {}

-- Raza
local razaPanel: Frame = nil :: any

-- ===== Cabecera =====

local function construirCabecera(padre: Frame)
	local cabecera = P.Marco(padre, { Nombre = "Cabecera", Tamano = UDim2.new(1, 0, 0, 50), Z = 3 })

	-- Badge de nivel: cuadrado con degradado cian, "NIVEL" pequeño arriba y el número grande.
	local badge = P.Marco(cabecera, {
		Nombre = "Nivel",
		Tamano = UDim2.fromOffset(44, 44),
		Posicion = UDim2.new(0, 0, 0.5, 0),
		Ancla = Vector2.new(0, 0.5),
		Color = C.Blanco,
		Radio = Theme.Tamanos.BorderRadius,
		Z = 3,
	})
	P.Degradado(badge, Theme.Degradados.Cian, 45)
	P.Borde(badge, C.Acento, 0.55, Theme.Tamanos.TrazoGrueso)
	P.Texto(badge, {
		Texto = "NIVEL",
		Tamano = Theme.Texto.Micro,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.TextoSobreAcento,
		Espaciado = true,
		Posicion = UDim2.new(0.5, 0, 0, 8),
		Ancla = Vector2.new(0.5, 0),
		Z = 4,
	})
	textoNivel = P.Texto(badge, {
		Texto = "1",
		Tamano = Theme.Texto.Destacado + 1,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.TextoSobreAcento,
		Posicion = UDim2.new(0.5, 0, 1, -7),
		Ancla = Vector2.new(0.5, 1),
		Z = 4,
	})

	textoNombre = P.Texto(cabecera, {
		Texto = "",
		Tamano = Theme.Texto.Titulo,
		Fuente = Theme.Fuentes.Negrita,
		Posicion = UDim2.fromOffset(54, 5),
		Z = 3,
	})
	P.Texto(cabecera, {
		Texto = DatosDemo.Jugador.Clan,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Acento,
		Espaciado = true,
		Posicion = UDim2.fromOffset(54, 21),
		Z = 3,
	})
	local _, relleno =
		P.BarraProgreso(cabecera, { Tamano = UDim2.fromOffset(150, 4), Posicion = UDim2.fromOffset(54, 38), Z = 3 })
	rellenoXP = relleno
	textoXP = P.Texto(cabecera, {
		Texto = "",
		Tamano = Theme.Texto.Mini,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Posicion = UDim2.fromOffset(210, 40),
		Ancla = Vector2.new(0, 0.5),
		Z = 3,
	})

	-- Mini-navegación: LOGROS / PODERES / RANKED.
	local mininav = P.Marco(cabecera, {
		Nombre = "MiniNav",
		Tamano = UDim2.fromOffset(130, 30),
		Posicion = UDim2.new(1, -4, 0, 4),
		Ancla = Vector2.new(1, 0),
		Z = 3,
	})
	P.Lista(mininav, Enum.FillDirection.Horizontal, 16, Enum.HorizontalAlignment.Right)
	for i, destino in
		{
			{ "logros", "ui_logros", "LOGROS" },
			{ "poderes", "sidebar_poderes", "PODERES" },
			{ "ranked", "sidebar_ranked", "RANKED" },
		}
	do
		local boton = P.Crear("TextButton", {
			Name = destino[1],
			Text = "",
			AutoButtonColor = false,
			Size = UDim2.fromOffset(30, 30),
			BackgroundColor3 = C.Acento,
			BackgroundTransparency = 0.93,
			LayoutOrder = i,
			ZIndex = 4,
			Parent = mininav,
		}) :: TextButton
		P.Esquinas(boton, UDim.new(0, 7))
		P.Borde(boton, C.Acento, A.BordeSutil)
		IconBuilder.Icono(boton, destino[2], {
			Tamano = 15,
			Color = C.Acento,
			Transparencia = 0.25,
			Posicion = UDim2.fromScale(0.5, 0.5),
			Ancla = Vector2.new(0.5, 0.5),
			Z = 5,
		})
		P.Texto(boton, {
			Texto = destino[3],
			Tamano = Theme.Texto.Micro,
			Fuente = Theme.Fuentes.Negrita,
			Color = C.TextoSecundario,
			Transparencia = A.TextoSecundario,
			Posicion = UDim2.new(0.5, 0, 1, 3),
			Ancla = Vector2.new(0.5, 0),
			Z = 5,
		})
		UITweens.Hover(boton, 0.84)
		boton.Activated:Connect(function()
			if destino[1] == "logros" then
				ctx.Notificar({
					Titulo = "Logros",
					Texto = "Pantalla pendiente de diseño",
					Color = C.Dorado,
					Icono = "ui_logros",
				})
			else
				ctx.Abrir(destino[1])
			end
		end)
	end
end

local function pintarCabecera()
	local jugador = EstadoUI.Jugador()
	textoNivel.Text = tostring(jugador.Nivel)
	textoNombre.Text = jugador.Nombre
	textoXP.Text = `XP {P.Numero(jugador.XP)} · Nv máx. 3.000`
	UITweens.Barra(rellenoXP, jugador.FraccionXP)
end

-- ===== Estadísticas =====

local function totalReparto(): number
	local total = 0
	for _, v in reparto do
		total += v
	end
	return total
end

local function pintarStats()
	local libres = EstadoUI.Jugador().PuntosStats - totalReparto()
	textoPuntos.Text = P.Espaciar(`PUNTOS: {libres}`)
	for id, valores in EstadoUI.Stats() do
		local fila = filasStats[id]
		if fila then
			fila.Poner(valores[1], valores[2], reparto[id] or 0, DatosDemo.StatMaximo)
			fila.Editar(editando, libres > 0)
		end
	end
	botonEditar.Text = P.Espaciar(if editando then "CONFIRMAR" else "EDITAR")
	botonCancelar.Visible = editando
end

local function construirStats(padre: GuiObject)
	local caja = P.Caja(padre, {
		Nombre = "Estadisticas",
		Tamano = UDim2.new(0, 300, 1, 0),
		Posicion = UDim2.fromScale(1, 0),
		Ancla = Vector2.new(1, 0),
		Z = 3,
	})
	P.Relleno(caja, 12, 14)
	P.Texto(caja, {
		Texto = "ESTADÍSTICAS",
		Tamano = Theme.Texto.Grande,
		Fuente = Theme.Fuentes.Negrita,
		Espaciado = true,
		Posicion = UDim2.new(0.5, 0, 0, 9),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 4,
	})
	textoPuntos = P.Texto(caja, {
		Texto = "",
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Aguante,
		Posicion = UDim2.new(1, 0, 0, 9),
		Ancla = Vector2.new(1, 0.5),
		Z = 5,
	})
	textoPuntos.BackgroundColor3 = C.Aguante
	textoPuntos.BackgroundTransparency = 0.9
	P.Esquinas(textoPuntos, UDim.new(0, 5))
	P.Borde(textoPuntos, C.Aguante, 0.65)
	P.Relleno(textoPuntos, 3, 7)

	local filas = P.Marco(
		caja,
		{ Nombre = "Filas", Tamano = UDim2.new(1, 0, 0, 5 * 34 + 4 * 8), Posicion = UDim2.fromOffset(0, 30), Z = 3 }
	)
	P.Lista(filas, Enum.FillDirection.Vertical, 8)
	for i, id in Theme.OrdenStats do
		filasStats[id] = StatRow.Crear(filas, {
			Stat = id,
			Orden = i,
			AlMas = function()
				if EstadoUI.Jugador().PuntosStats - totalReparto() > 0 then
					reparto[id] = (reparto[id] or 0) + 1
					pintarStats()
				end
			end,
			AlMenos = function()
				if (reparto[id] or 0) > 0 then
					reparto[id] -= 1
					pintarStats()
				end
			end,
		})
	end

	local pie = P.Marco(caja, {
		Nombre = "Pie",
		Tamano = UDim2.new(1, 0, 0, 24),
		Posicion = UDim2.fromScale(0, 1),
		Ancla = Vector2.new(0, 1),
		Z = 3,
	})
	P.Lista(pie, Enum.FillDirection.Horizontal, 8, Enum.HorizontalAlignment.Center)
	botonCancelar = P.Boton(pie, {
		Texto = "CANCELAR",
		Estilo = "Gris",
		Tamano = UDim2.fromOffset(92, 24),
		Orden = 1,
		Z = 4,
		AlPulsar = function()
			editando = false
			table.clear(reparto)
			pintarStats()
		end,
	})
	botonEditar = P.Boton(pie, {
		Texto = "EDITAR",
		Estilo = "Borde",
		Tamano = UDim2.fromOffset(92, 24),
		Orden = 2,
		Z = 4,
		AlPulsar = function()
			if not editando then
				editando = true
				table.clear(reparto)
			else
				local repartidos = EstadoUI.RepartirPuntos(reparto)
				editando = false
				table.clear(reparto)
				if repartidos > 0 then
					ctx.Notificar({
						Titulo = "Atributos guardados",
						Texto = `{repartidos} punto(s) repartido(s) (demo)`,
						Color = C.Exito,
						Icono = "stat_habilidad",
					})
				end
			end
			pintarStats()
		end,
	})
	pintarStats()
end

-- ===== Raza =====

local function pintarRaza()
	for _, hijo in razaPanel:GetChildren() do
		if hijo:IsA("GuiObject") then
			hijo:Destroy()
		end
	end
	local raza = EstadoUI.Raza()
	local color = (Theme.Colores :: any)[raza.Color] or C.Acento
	local lista = P.Marco(razaPanel, { Nombre = "Contenido", Z = 3 })
	P.Relleno(lista, 14)
	P.Lista(lista, Enum.FillDirection.Vertical, 2, Enum.HorizontalAlignment.Center)

	-- Icono grande circular con un anillo y un satélite que lo orbita.
	local icono = P.Marco(lista, { Nombre = "Icono", Tamano = UDim2.fromOffset(78, 78), Orden = 1, Z = 3 })
	local circulo = P.Marco(icono, {
		Tamano = UDim2.fromOffset(66, 66),
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Color = color,
		Transparencia = 0.78,
		Radio = UDim.new(0.5, 0),
		Z = 3,
	})
	P.Degradado(circulo, ColorSequence.new(color, C.Fondo1), 90)
	P.Borde(circulo, color, 0, Theme.Tamanos.TrazoGrueso)
	IconBuilder.Icono(
		circulo,
		raza.Icono,
		{ Tamano = 44, Color = color, Posicion = UDim2.fromScale(0.5, 0.5), Ancla = Vector2.new(0.5, 0.5), Z = 4 }
	)
	local orbita = P.Marco(icono, {
		Nombre = "Orbita",
		Tamano = UDim2.fromOffset(78, 78),
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 3,
	})
	local anillo = P.Marco(orbita, { Tamano = UDim2.fromScale(1, 1), Radio = UDim.new(0.5, 0), Z = 3 })
	P.Borde(anillo, color, 0.65)
	P.Marco(orbita, {
		Tamano = UDim2.fromOffset(5, 5),
		Posicion = UDim2.fromScale(0.5, 0),
		Ancla = Vector2.new(0.5, 0.5),
		Color = color,
		Radio = UDim.new(1, 0),
		Z = 4,
	})
	UITweens.Girar(orbita)

	P.Texto(
		lista,
		{ Texto = raza.Nombre, Tamano = Theme.Texto.Titulo + 1, Fuente = Theme.Fuentes.Negrita, Orden = 2, Z = 3 }
	)
	P.Texto(lista, {
		Texto = string.upper(raza.Clase),
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Acento,
		Espaciado = true,
		Orden = 3,
		Z = 3,
	})
	local bando = P.Texto(lista, {
		Texto = if EstadoUI.Jugador().Bando == "Ninguno" then "SIN BANDO" else raza.Bando,
		Tamano = Theme.Texto.Micro + 0.5,
		Fuente = Theme.Fuentes.Negrita,
		Color = color,
		Espaciado = true,
		Orden = 4,
		Z = 3,
	})
	bando.BackgroundColor3 = color
	bando.BackgroundTransparency = 0.88
	P.Esquinas(bando, UDim.new(0, 4))
	P.Relleno(bando, 3, 8)

	local function seccion(titulo: string, orden: number): Frame
		local marco = P.Marco(lista, { Nombre = titulo, Tamano = UDim2.new(1, 0, 0, 0), Orden = orden, Z = 3 })
		marco.AutomaticSize = Enum.AutomaticSize.Y
		P.Lista(marco, Enum.FillDirection.Vertical, 4)
		P.Relleno(marco, 10, 0, 0, 0)
		P.Etiqueta(marco, titulo, { Orden = 0, Z = 3 })
		return marco
	end

	-- Pasivas con un borde izquierdo de color.
	local pasivas = seccion("PASIVAS", 5)
	for i, pasiva in raza.Pasivas do
		local colorPasiva = (Theme.Colores :: any)[pasiva.Color] or C.Acento
		local fila = P.Marco(pasivas, {
			Nombre = pasiva.Nombre,
			Tamano = UDim2.new(1, 0, 0, 30),
			Color = colorPasiva,
			Transparencia = 0.9,
			Orden = i,
			Z = 3,
		})
		P.Degradado(fila, ColorSequence.new(colorPasiva), 0, NumberSequence.new(0.86, 1))
		P.Marco(fila, { Nombre = "Borde", Tamano = UDim2.new(0, 2.5, 1, 0), Color = colorPasiva, Z = 4 })
		P.Texto(fila, {
			Texto = pasiva.Nombre,
			Tamano = Theme.Texto.Pequeno + 0.5,
			Fuente = Theme.Fuentes.Negrita,
			Posicion = UDim2.fromOffset(9, 5),
			Z = 4,
		})
		P.Texto(fila, {
			Texto = pasiva.Texto,
			Tamano = Theme.Texto.Mini,
			Fuente = Theme.Fuentes.Medio,
			Color = C.TextoSecundario,
			Transparencia = A.TextoSecundario,
			Posicion = UDim2.fromOffset(9, 18),
			Z = 4,
		})
	end

	-- Estadísticas detalladas.
	local detalle = seccion("ESTADÍSTICAS", 6)
	for i, fila in raza.Detalle do
		local info = Theme.Stats[fila.Stat]
		local linea = P.Marco(detalle, { Nombre = fila.Etiqueta, Tamano = UDim2.new(1, 0, 0, 18), Orden = i, Z = 3 })
		P.Marco(linea, {
			Tamano = UDim2.new(1, 0, 0, 1),
			Posicion = UDim2.fromScale(0, 1),
			Color = C.Blanco,
			Transparencia = 0.96,
			Z = 3,
		})
		P.Texto(linea, {
			Texto = fila.Etiqueta,
			Tamano = Theme.Texto.Mini + 0.5,
			Fuente = Theme.Fuentes.Negrita,
			Color = C.TextoSecundario,
			Transparencia = A.TextoSecundario,
			Espaciado = true,
			Posicion = UDim2.new(0, 2, 0.5, 0),
			Ancla = Vector2.new(0, 0.5),
			Z = 4,
		})
		P.Texto(linea, {
			Texto = `{P.Numero(fila.Valor)} <font size="{Theme.Texto.Mini + 0.5}" color="#{(if info
				then info.Color
				else C.Acento):ToHex()}">+{P.Decimal(fila.Bonus)}</font>`,
			Rico = true,
			Tamano = Theme.Texto.Medio,
			Fuente = Theme.Fuentes.Negrita,
			Posicion = UDim2.new(1, -2, 0.5, 0),
			Ancla = Vector2.new(1, 0.5),
			Z = 4,
		})
	end
end

-- ===== Builds =====

local function construirBuilds(padre: GuiObject)
	local cuadricula = P.Marco(padre, { Nombre = "Builds", Z = 3 })
	P.Lista(cuadricula, Enum.FillDirection.Horizontal, 10)
	local tarjetas: { Frame } = {}
	local function pintar()
		for i, tarjeta in tarjetas do
			local borde = tarjeta:FindFirstChildOfClass("UIStroke")
			if borde then
				borde.Transparency = if i == DatosDemo.BuildActiva then 0 else A.BordeSutil
			end
			local cargar = tarjeta:FindFirstChild("Cargar", true)
			if cargar and cargar:IsA("TextButton") then
				cargar.Text = P.Espaciar(if i == DatosDemo.BuildActiva then "EN USO" else "CARGAR")
				P.Habilitar(cargar, i ~= DatosDemo.BuildActiva)
			end
		end
	end
	for i, build in DatosDemo.Builds do
		local info = Theme.Stats[build.Enfoque]
		local tarjeta =
			P.Caja(cuadricula, { Nombre = build.Nombre, Tamano = UDim2.new(1 / 3, -7, 1, 0), Orden = i, Z = 3 })
		P.Relleno(tarjeta, 12)
		P.Lista(tarjeta, Enum.FillDirection.Vertical, 8)
		P.Texto(
			tarjeta,
			{ Texto = build.Nombre, Tamano = Theme.Texto.Grande, Fuente = Theme.Fuentes.Negrita, Orden = 1, Z = 4 }
		)
		local enfoque = P.Marco(tarjeta, { Tamano = UDim2.new(1, 0, 0, 12), Orden = 2, Z = 4 })
		P.Lista(enfoque, Enum.FillDirection.Horizontal, 5, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
		IconBuilder.Icono(enfoque, info.Icono, { Tamano = 12, Color = info.Color, Orden = 1, Z = 4 })
		P.Texto(enfoque, {
			Texto = `ENFOQUE: {info.Nombre}`,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Negrita,
			Color = info.Color,
			Espaciado = true,
			Orden = 2,
			Z = 4,
		})

		-- Equipo de la build (por ahora, el equipo actual).
		local equipo = P.Marco(tarjeta, { Tamano = UDim2.new(1, 0, 0, 94), Orden = 3, Z = 4 })
		P.Crear("UIGridLayout", {
			CellSize = UDim2.new(0.25, -3, 0, 45),
			CellPadding = UDim2.fromOffset(4, 4),
			SortOrder = Enum.SortOrder.LayoutOrder,
			Parent = equipo,
		})
		for k, slot in DatosDemo.Slots do
			local id = EstadoUI.Equipado()[slot.Id]
			local objeto = if id then EstadoUI.Objeto(id) else nil
			local celda = P.Marco(
				equipo,
				{ Color = C.FondoProfundo, Transparencia = 0.4, Radio = UDim.new(0, 5), Orden = k, Z = 4 }
			)
			P.Borde(celda, if objeto then Theme.ColorRareza(objeto.Rareza) else C.Blanco, if objeto then 0.3 else 0.94)
			if objeto then
				IconBuilder.Arte(celda, objeto.Arte, {
					Tamano = UDim2.new(1, -6, 1, -6),
					Posicion = UDim2.fromScale(0.5, 0.5),
					Ancla = Vector2.new(0.5, 0.5),
					Z = 5,
				})
			else
				IconBuilder.Icono(celda, slot.Icono, {
					Tamano = 18,
					Color = C.Gris,
					Transparencia = 0.7,
					Posicion = UDim2.fromScale(0.5, 0.5),
					Ancla = Vector2.new(0.5, 0.5),
					Z = 5,
				})
			end
		end

		-- Reparto de puntos.
		local repartoMarco = P.Marco(tarjeta, { Tamano = UDim2.new(1, 0, 0, 5 * 12), Orden = 4, Z = 4 })
		P.Lista(repartoMarco, Enum.FillDirection.Vertical, 2)
		for k, id in Theme.OrdenStats do
			local stat = Theme.Stats[id]
			local valor = (build.Reparto :: any)[id] or 0
			local linea = P.Marco(repartoMarco, { Tamano = UDim2.new(1, 0, 0, 10), Orden = k, Z = 4 })
			P.Texto(linea, {
				Texto = stat.Nombre,
				Tamano = Theme.Texto.Mini,
				Fuente = Theme.Fuentes.Negrita,
				Color = C.TextoSecundario,
				Transparencia = A.TextoSecundario,
				Posicion = UDim2.fromScale(0, 0.5),
				Ancla = Vector2.new(0, 0.5),
				Z = 4,
			})
			local fondo = P.Marco(linea, {
				Tamano = UDim2.new(1, -86, 0, 4),
				Posicion = UDim2.new(0, 58, 0.5, 0),
				Ancla = Vector2.new(0, 0.5),
				Color = C.Negro,
				Transparencia = 0.5,
				Radio = UDim.new(1, 0),
				Z = 4,
			})
			P.Marco(
				fondo,
				{ Tamano = UDim2.fromScale(valor / 100, 1), Color = stat.Color, Radio = UDim.new(1, 0), Z = 5 }
			)
			P.Texto(linea, {
				Texto = tostring(valor),
				Tamano = Theme.Texto.Pequeno,
				Fuente = Theme.Fuentes.Negrita,
				Color = stat.Color,
				Posicion = UDim2.fromScale(1, 0.5),
				Ancla = Vector2.new(1, 0.5),
				Z = 4,
			})
		end

		local botones = P.Marco(tarjeta, { Tamano = UDim2.new(1, 0, 0, 24), Orden = 5, Z = 4 })
		P.Lista(botones, Enum.FillDirection.Horizontal, 6)
		P.Boton(botones, {
			Nombre = "Cargar",
			Texto = "CARGAR",
			Estilo = "Cian",
			Tamano = UDim2.new(0.5, -3, 1, 0),
			Orden = 1,
			Z = 5,
			AlPulsar = function()
				DatosDemo.BuildActiva = i
				pintar()
				ctx.Notificar({
					Titulo = "Build cargada",
					Texto = build.Nombre,
					Color = C.Acento,
					Icono = "sidebar_personaje",
				})
			end,
		})
		P.Boton(botones, {
			Texto = "GUARDAR",
			Estilo = "Gris",
			Tamano = UDim2.new(0.5, -3, 1, 0),
			Orden = 2,
			Z = 5,
			AlPulsar = function()
				ctx.Notificar({
					Titulo = "Build guardada",
					Texto = `{build.Nombre} (demo)`,
					Color = C.Exito,
					Icono = "ui_check",
				})
			end,
		})
		table.insert(tarjetas, tarjeta)
	end
	pintar()
end

-- ===== Pestañas =====

local function cambiarVista(id: string, desdeControlador: boolean?)
	if not vistas[id] then
		return
	end
	local anterior = vistas[vistaActual]
	if anterior ~= vistas[id] then
		UITweens.FundidoCruzado(anterior, vistas[id])
	end
	vistaActual = id
	ventana.PonerSubtitulo(SUBTITULOS[id] or "")
	Tooltip.Ocultar()
	muneco.Activar(id == "atributos")
	PanelInventario.Activar(id == "inventario")
	if not desdeControlador then
		ctx.MarcarPantalla(if id == "inventario" then "inventario" else "personaje")
	end
end

-- ===== API =====

function PanelPersonaje.Iniciar(contexto: Contexto.Contexto)
	ctx = contexto
	ventana = Ventana.Crear(contexto.Raiz, {
		Nombre = "Personaje",
		Titulo = "PERSONAJE",
		Subtitulo = SUBTITULOS.atributos,
		Icono = "sidebar_personaje",
		Tecla = "P",
		AlCerrar = contexto.Cerrar,
	})
	local cuerpo = ventana.Cuerpo
	local principal = P.Marco(
		cuerpo,
		{ Nombre = "Principal", Tamano = UDim2.new(0, 616, 1, -24), Posicion = UDim2.fromOffset(12, 12), Z = 3 }
	)
	construirCabecera(principal)

	pestanas = TabSelector.Crear(principal, {
		Opciones = {
			{ Id = "atributos", Texto = "Atributos" },
			{ Id = "inventario", Texto = "Inventario" },
			{ Id = "builds", Texto = "Builds" },
		},
		Inicial = "atributos",
		Posicion = UDim2.fromOffset(0, 58),
		AlCambiar = function(id: string)
			cambiarVista(id)
		end,
	})

	local contenido = P.Marco(
		principal,
		{ Nombre = "Contenido", Tamano = UDim2.new(1, 0, 1, -90), Posicion = UDim2.fromOffset(0, 90), Z = 3 }
	)
	for _, id in { "atributos", "inventario", "builds" } do
		local vista = P.Marco(contenido, { Nombre = id, Z = 3 })
		vista.Visible = id == "atributos"
		vistas[id] = vista
	end

	-- Atributos: muñeco + estadísticas.
	muneco = Muneco.Crear(vistas.atributos, {
		Tamano = UDim2.fromOffset(300, 318),
		Posicion = UDim2.new(),
		AlPulsarSlot = function(slot: string)
			local quitado = EstadoUI.Desequipar(slot)
			if quitado then
				ctx.Notificar({ Titulo = "Desequipado", Texto = quitado.Nombre, Color = C.Gris, Arte = quitado.Arte })
			else
				cambiarVista("inventario")
				pestanas.Seleccionar("inventario", true)
			end
		end,
		AlEntrarSlot = function(slot: string, boton: GuiObject)
			local id = EstadoUI.Equipado()[slot]
			local objeto = if id then EstadoUI.Objeto(id) else nil
			if objeto then
				Tooltip.Mostrar(objeto, boton)
			end
		end,
		AlSalirSlot = function()
			Tooltip.Ocultar()
		end,
	})
	construirStats(vistas.atributos)
	PanelInventario.Construir(vistas.inventario, contexto)
	construirBuilds(vistas.builds)

	razaPanel = P.Caja(cuerpo, {
		Nombre = "Raza",
		Tamano = UDim2.new(0, 220, 1, -24),
		Posicion = UDim2.new(1, -12, 0, 12),
		Ancla = Vector2.new(1, 0),
		Z = 3,
	})

	EstadoUI.Cambio:Conectar(function(que: string)
		if que == "Datos" then
			pintarCabecera()
			pintarRaza()
		elseif que == "Equipo" then
			muneco.Refrescar()
		elseif que == "Stats" then
			pintarStats()
		end
	end)
	pintarCabecera()
	pintarRaza()
end

-- Abre la ventana en la pestaña pedida ("atributos" por defecto, "inventario" desde la barra lateral o la tecla I).
function PanelPersonaje.Mostrar(subvista: string?)
	local destino = subvista or (if vistaActual == "inventario" then "atributos" else vistaActual)
	pestanas.Seleccionar(destino, true)
	cambiarVista(destino, true)
	pintarCabecera()
	ventana.Abrir()
end

function PanelPersonaje.Ocultar()
	Tooltip.Ocultar()
	PanelInventario.Deseleccionar()
	muneco.Activar(false)
	PanelInventario.Activar(false)
	if editando then
		editando = false
		table.clear(reparto)
		pintarStats()
	end
	ventana.Cerrar()
end

return PanelPersonaje
