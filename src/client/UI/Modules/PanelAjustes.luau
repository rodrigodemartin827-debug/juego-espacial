--!strict
--[[
	PanelAjustes: pantalla AJUSTES.

	  ┌ categorías ─┐  GRÁFICOS
	  │ GRÁFICOS    │  Calidad .................................. [Alto      v]
	  │ AUDIO       │  Distancia de render ....................... ━━━━●━━━ 1.024
	  │ CONTROLES   │  Partículas ................................ (●  )
	  │ INTERFAZ    │
	  │ JUEGO       │                                         [RESTAURAR VALORES]
	  └─────────────┘

	Los ajustes salen de ConfigUI.Ajustes. Al cambiar uno se dispara `PanelAjustes.Cambio(id, valor)` y quien lo use
	lo aplica (HUDController: tamaño del HUD, transparencia del minimapa, notificaciones, teclas; aquí mismo: calidad
	gráfica y volúmenes). RESTAURAR VALORES pide confirmación.

	Qué hace cada ajuste hoy:
	  - Calidad: fuerza el nivel de VFX/Calidad (Automática = el que elige el propio juego según los FPS).
	  - Partículas: apagadas = calidad Baja (VFX/Calidad escala las partículas por nivel).
	  - Volúmenes: SoundGroups "Musica", "SFX" y "Voces" en SoundService (los sonidos deben usar esos grupos).
	  - Tamaño del HUD, transparencia del minimapa, notificaciones y teclas de menú: se aplican al momento.
	  - Distancia de render, sensibilidad, idioma y región: todavía no tienen efecto (TODO): la distancia la decide
	    el servidor (StreamingTargetRadius) y Roblox no deja cambiar la sensibilidad desde el juego.
	  Los valores duran la sesión; guardarlos en la cuenta necesita un campo en ServicioDatos (TODO).
]]

local SoundService = game:GetService("SoundService")

local Theme = require(script.Parent.Temas.EspacialTheme)
local IconBuilder = require(script.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Componentes.Primitivas)
local Ventana = require(script.Parent.Componentes.Ventana)
local Controles = require(script.Parent.Componentes.Controles)
local Modal = require(script.Parent.Componentes.Modal)
local ConfigUI = require(script.Parent.Datos.ConfigUI)
local Contexto = require(script.Parent.Contexto)
local Senal = require(game:GetService("ReplicatedStorage"):WaitForChild("Shared").Utilidades.Senal)
local Calidad = require(script.Parent.Parent.Parent.VFX.Calidad)

local C = Theme.Colores
local A = Theme.Alpha

local PanelAjustes = {}

-- (id, valor): se dispara al cambiar cualquier ajuste.
PanelAjustes.Cambio = Senal.nueva()

local ctx: Contexto.Contexto = nil :: any
local ventana: Ventana.Ventana = nil :: any
local navegacion: Frame = nil :: any
local lista: ScrollingFrame = nil :: any
local categoriaActual = ConfigUI.Ajustes[1].Id
local valores: { [string]: any } = {}

for _, categoria in ConfigUI.Ajustes do
	for _, fila in categoria.Filas do
		valores[fila.Id] = fila.Valor
	end
end

-- ===== Efectos que se aplican aquí mismo =====

local function grupoSonido(nombre: string): SoundGroup
	local existente = SoundService:FindFirstChild(nombre)
	if existente and existente:IsA("SoundGroup") then
		return existente
	end
	local grupo = Instance.new("SoundGroup")
	grupo.Name = nombre
	grupo.Parent = SoundService
	return grupo
end

local function aplicarSonido()
	local maestro = (valores.VolumenMaestro or 100) / 100
	grupoSonido("Musica").Volume = maestro * (valores.VolumenMusica or 100) / 100
	grupoSonido("SFX").Volume = maestro * (valores.VolumenSFX or 100) / 100
	grupoSonido("Voces").Volume = maestro * (valores.VolumenVoces or 100) / 100
end

local function aplicarCalidad()
	if valores.Particulas == false then
		Calidad.Forzar("Bajo")
		return
	end
	local calidad = valores.Calidad
	Calidad.Forzar(if calidad == "Automática" then nil else calidad)
end

local function cambiar(id: string, valor: any)
	valores[id] = valor
	if id == "Calidad" or id == "Particulas" then
		aplicarCalidad()
	elseif string.sub(id, 1, 7) == "Volumen" then
		aplicarSonido()
	end
	PanelAjustes.Cambio:Disparar(id, valor)
end

-- ===== Construcción =====

local function control(padre: Frame, fila: ConfigUI.FilaAjuste)
	if fila.Tipo == "Deslizador" then
		Controles.Deslizador(padre, {
			Min = fila.Min or 0,
			Max = fila.Max or 100,
			Valor = valores[fila.Id],
			Unidad = fila.Unidad,
			AlCambiar = function(v: number)
				cambiar(fila.Id, v)
			end,
		})
	elseif fila.Tipo == "Interruptor" then
		Controles.Interruptor(padre, valores[fila.Id] == true, function(v: boolean)
			cambiar(fila.Id, v)
		end)
	elseif fila.Tipo == "Lista" then
		Controles.Desplegable(padre, fila.Opciones or {}, valores[fila.Id], function(v: string)
			cambiar(fila.Id, v)
		end)
	elseif fila.Tipo == "Tecla" then
		Controles.Tecla(padre, valores[fila.Id], fila.Bloqueado == true, function(tecla: Enum.KeyCode)
			cambiar(fila.Id, tecla.Name)
			ctx.Notificar({
				Titulo = "Tecla cambiada",
				Texto = `{fila.Titulo}: {tecla.Name}`,
				Color = C.Acento,
				Icono = "aj_controles",
			})
		end)
	end
end

local function pintarLista()
	for _, hijo in lista:GetChildren() do
		if hijo:IsA("GuiObject") then
			hijo:Destroy()
		end
	end
	local categoria = ConfigUI.Ajustes[1]
	for _, c in ConfigUI.Ajustes do
		if c.Id == categoriaActual then
			categoria = c
		end
	end
	P.Texto(lista, {
		Texto = categoria.Nombre,
		Tamano = Theme.Texto.Medio,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Acento,
		Espaciado = true,
		Caja = UDim2.new(1, 0, 0, 30),
		Orden = 0,
		Z = 4,
	})
	for i, fila in categoria.Filas do
		local marco = P.Marco(lista, { Nombre = fila.Id, Tamano = UDim2.new(1, 0, 0, 42), Orden = i, Z = 4 })
		P.Marco(marco, {
			Tamano = UDim2.new(1, 0, 0, 1),
			Posicion = UDim2.fromScale(0, 1),
			Color = C.Blanco,
			Transparencia = 0.96,
			Z = 4,
		})
		P.Texto(marco, {
			Texto = fila.Titulo,
			Tamano = Theme.Texto.Cuerpo + 0.5,
			Fuente = Theme.Fuentes.Titulo,
			Posicion = UDim2.new(0, 0, 0.5, if fila.Descripcion then -6 else 0),
			Ancla = Vector2.new(0, 0.5),
			Z = 5,
		})
		if fila.Descripcion then
			P.Texto(marco, {
				Texto = fila.Descripcion,
				Tamano = Theme.Texto.Mini + 0.5,
				Fuente = Theme.Fuentes.Medio,
				Color = C.TextoSecundario,
				Transparencia = A.TextoSecundario,
				Posicion = UDim2.new(0, 0, 0.5, 7),
				Ancla = Vector2.new(0, 0.5),
				Z = 5,
			})
		end
		-- La lista de opciones de un desplegable debe quedar por encima de las filas siguientes.
		local zona = P.Marco(marco, {
			Nombre = "Control",
			Tamano = UDim2.new(0, 230, 1, 0),
			Posicion = UDim2.fromScale(1, 0),
			Ancla = Vector2.new(1, 0),
			Z = 10 + (#categoria.Filas - i),
		})
		P.Lista(zona, Enum.FillDirection.Horizontal, 8, Enum.HorizontalAlignment.Right, Enum.VerticalAlignment.Center)
		control(zona, fila)
	end
end

local function pintarNavegacion()
	for _, boton in navegacion:GetChildren() do
		if boton:IsA("TextButton") then
			local activo = boton.Name == categoriaActual
			boton.BackgroundTransparency = if activo then A.Tab else 1
			local borde = boton:FindFirstChildOfClass("UIStroke")
			if borde then
				borde.Transparency = if activo then A.BordeActivo else 1
			end
			local texto = boton:FindFirstChild("Texto")
			if texto and texto:IsA("TextLabel") then
				texto.TextColor3 = if activo then C.Acento else C.TextoPrincipal
				texto.TextTransparency = if activo then 0 else A.TextoSecundario
			end
			local icono = boton:FindFirstChildOfClass("ImageLabel")
			if icono then
				icono.ImageTransparency = if activo then 0 else 0.5
			end
		end
	end
end

local function restaurar()
	for _, categoria in ConfigUI.Ajustes do
		for _, fila in categoria.Filas do
			if valores[fila.Id] ~= fila.Valor then
				cambiar(fila.Id, fila.Valor)
			end
		end
	end
	pintarLista()
	ctx.Notificar({
		Titulo = "Ajustes restaurados",
		Texto = "Valores por defecto",
		Color = C.Acento,
		Icono = "sidebar_ajustes",
	})
end

-- ===== API =====

function PanelAjustes.Valor(id: string): any
	return valores[id]
end

function PanelAjustes.Iniciar(contexto: Contexto.Contexto)
	ctx = contexto
	ventana = Ventana.Crear(
		contexto.Raiz,
		{ Nombre = "Ajustes", Titulo = "AJUSTES", Icono = "sidebar_ajustes", AlCerrar = contexto.Cerrar }
	)
	local cuerpo = ventana.Cuerpo

	navegacion = P.Caja(
		cuerpo,
		{ Nombre = "Categorias", Tamano = UDim2.new(0, 176, 1, -24), Posicion = UDim2.fromOffset(12, 12), Z = 3 }
	)
	P.Relleno(navegacion, 8)
	P.Lista(navegacion, Enum.FillDirection.Vertical, 4)
	for i, categoria in ConfigUI.Ajustes do
		local boton = P.Crear("TextButton", {
			Name = categoria.Id,
			Text = "",
			AutoButtonColor = false,
			Size = UDim2.new(1, 0, 0, 34),
			BackgroundColor3 = C.Acento,
			BackgroundTransparency = 1,
			LayoutOrder = i,
			ZIndex = 4,
			Parent = navegacion,
		}) :: TextButton
		P.Esquinas(boton, Theme.Tamanos.RadioBoton)
		P.Borde(boton, C.Acento, 1)
		IconBuilder.Icono(
			boton,
			categoria.Icono,
			{ Tamano = 15, Color = C.Acento, Posicion = UDim2.new(0, 10, 0.5, 0), Ancla = Vector2.new(0, 0.5), Z = 5 }
		)
		P.Texto(boton, {
			Nombre = "Texto",
			Texto = categoria.Nombre,
			Tamano = Theme.Texto.Cuerpo,
			Fuente = Theme.Fuentes.Negrita,
			Espaciado = true,
			Posicion = UDim2.new(0, 34, 0.5, 0),
			Ancla = Vector2.new(0, 0.5),
			Z = 5,
		})
		boton.MouseEnter:Connect(function()
			if boton.Name ~= categoriaActual then
				boton.BackgroundTransparency = 0.94
			end
		end)
		boton.MouseLeave:Connect(function()
			pintarNavegacion()
		end)
		boton.Activated:Connect(function()
			categoriaActual = categoria.Id
			pintarNavegacion()
			pintarLista()
		end)
	end

	lista = P.Crear("ScrollingFrame", {
		Name = "Lista",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = UDim2.new(1, -226, 1, -64),
		Position = UDim2.fromOffset(212, 12),
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 4,
		ScrollBarImageColor3 = C.Acento,
		ScrollBarImageTransparency = 0.5,
		ZIndex = 3,
		Parent = cuerpo,
	}) :: ScrollingFrame
	P.Relleno(lista, 4, 14, 60, 0)
	P.Lista(lista, Enum.FillDirection.Vertical, 0)

	local pie = P.Marco(cuerpo, {
		Nombre = "Pie",
		Tamano = UDim2.new(1, -212, 0, 28),
		Posicion = UDim2.new(0, 200, 1, -12),
		Ancla = Vector2.new(0, 1),
		Z = 3,
	})
	P.Texto(pie, {
		Texto = "Los ajustes se aplican al momento.",
		Tamano = Theme.Texto.Mini + 0.5,
		Fuente = Theme.Fuentes.Medio,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Posicion = UDim2.new(0, 12, 0.5, 0),
		Ancla = Vector2.new(0, 0.5),
		Z = 4,
	})
	P.Boton(pie, {
		Texto = "RESTAURAR VALORES",
		Estilo = "Gris",
		Tamano = UDim2.fromOffset(160, 28),
		Posicion = UDim2.fromScale(1, 0),
		Ancla = Vector2.new(1, 0),
		Z = 4,
		AlPulsar = function()
			Modal.Confirmar({
				Titulo = "¿RESTAURAR VALORES?",
				Texto = "Todos los ajustes volverán a sus valores por defecto.",
				TextoSi = "RESTAURAR",
				EstiloSi = "Cian",
				AlSi = restaurar,
			})
		end,
	})

	pintarNavegacion()
	pintarLista()
	aplicarSonido()
end

function PanelAjustes.Mostrar()
	ventana.Abrir()
end

function PanelAjustes.Ocultar()
	ventana.Cerrar()
end

return PanelAjustes
