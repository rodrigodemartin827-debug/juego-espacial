--!strict
--[[
	PanelMapa: MAPA GALÁCTICO, vista desde arriba (barra lateral, o M con un menú abierto).

	  - Nueva Tierra (cian) y Umbra (púrpura, junto a su agujero negro) siempre visibles, con su zona segura.
	  - Planetas descubiertos: círculos del color de su tipo (verde habitable, gris estéril, naranja volcánico, azul
	    acuático). El planeta disputado (PvP) lleva un aviso rojo.
	  - Los no descubiertos (hasta 300 planetas) son puntos tenues repartidos en espiral.
	  - Tu posición: marcador cian que late. Rutas discontinuas entre planetas cercanos y el campo de asteroides.
	  - Rueda (o pellizco) = zoom hacia el puntero; arrastrar = mover. Clic en un planeta = ficha lateral y VIAJAR.

	Los planetas pequeños, sus rutas y quién los descubrió son de demostración (DatosDemo.Mapa).
]]

local UserInputService = game:GetService("UserInputService")

local Theme = require(script.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Componentes.Primitivas)
local Ventana = require(script.Parent.Componentes.Ventana)
local DatosDemo = require(script.Parent.Datos.DatosDemo)
local EstadoUI = require(script.Parent.EstadoUI)
local Contexto = require(script.Parent.Contexto)

local C = Theme.Colores
local A = Theme.Alpha
local M = DatosDemo.Mapa

local PanelMapa = {}

local ANCHO_MUNDO, ALTO_MUNDO = 1600, 1000
local ZOOM_MIN, ZOOM_MAX, ZOOM_INICIAL = 0.38, 2.2, 0.66

local ctx: Contexto.Contexto = nil :: any
local ventana: Ventana.Ventana = nil :: any
local vista: Frame = nil :: any
local mundo: Frame = nil :: any
local escala: UIScale = nil :: any
local panel: CanvasGroup = nil :: any
local pie: Frame = nil :: any
local rutaActiva: Frame = nil :: any
local botonesPlaneta: { [string]: GuiObject } = {}
local seleccionado: DatosDemo.PlanetaMapa? = nil
local zoom = ZOOM_INICIAL
local desplazamiento = Vector2.zero

local function colorDe(p: DatosDemo.PlanetaMapa): Color3
	if p.Tipo == "Bando" then
		return if p.Bando == "Monstruos" then C.PlanetaMonstruos else C.PlanetaHumanos
	end
	return Theme.TipoPlaneta[p.Tipo] or C.Gris
end

local function nombreTipo(p: DatosDemo.PlanetaMapa): string
	if p.Tipo == "Bando" then
		return `PLANETA DE BANDO · {string.upper(p.Bando or "")}`
	end
	local nombres: { [string]: string } =
		{ Habitable = "HABITABLE", Esteril = "ESTÉRIL", Volcanico = "VOLCÁNICO", Acuatico = "ACUÁTICO" }
	return nombres[p.Tipo] or p.Tipo
end

-- ===== Vista (zoom y desplazamiento) =====

local function aplicarVista()
	escala.Scale = zoom
	mundo.Position = UDim2.fromOffset(desplazamiento.X, desplazamiento.Y)
end

local function centrar()
	local tamano = vista.Size
	zoom = ZOOM_INICIAL
	desplazamiento = Vector2.new(tamano.X.Offset / 2 - 800 * zoom, tamano.Y.Offset / 2 - 520 * zoom)
	aplicarVista()
end

-- Zoom manteniendo fijo el punto `centro` (en unidades de la vista).
local function hacerZoom(factor: number, centro: Vector2?)
	local nuevo = math.clamp(zoom * factor, ZOOM_MIN, ZOOM_MAX)
	local c = centro or Vector2.new(vista.Size.X.Offset / 2, vista.Size.Y.Offset / 2)
	desplazamiento = c - (c - desplazamiento) * (nuevo / zoom)
	zoom = nuevo
	aplicarVista()
end

-- ===== Dibujo del mundo =====

local function punto(x: number, y: number, r: number, color: Color3, transparencia: number, z: number?): Frame
	return P.Marco(mundo, {
		Tamano = UDim2.fromOffset(r * 2, r * 2),
		Posicion = UDim2.fromOffset(x, y),
		Ancla = Vector2.new(0.5, 0.5),
		Color = color,
		Transparencia = transparencia,
		Radio = UDim.new(0.5, 0),
		Z = z or 3,
	})
end

-- Línea discontinua (trozos de 7 con huecos de 6).
local function discontinua(
	padre: Frame,
	a: Vector2,
	b: Vector2,
	color: Color3,
	transparencia: number,
	grosor: number,
	z: number
): { Frame }
	local d = b - a
	local largo = d.Magnitude
	local dir = d.Unit
	local angulo = math.deg(math.atan2(d.Y, d.X))
	local trozos = {}
	local t = 0
	while t < largo do
		local fin = math.min(t + 7, largo)
		local medio = a + dir * ((t + fin) / 2)
		local trozo = P.Marco(padre, {
			Tamano = UDim2.fromOffset(fin - t, grosor),
			Posicion = UDim2.fromOffset(medio.X, medio.Y),
			Ancla = Vector2.new(0.5, 0.5),
			Color = color,
			Transparencia = transparencia,
			Z = z,
		})
		trozo.Rotation = angulo
		table.insert(trozos, trozo)
		t += 13
	end
	return trozos
end

local function anillo(x: number, y: number, r: number, color: Color3, texto: string?)
	local zona = punto(x, y, r, color, 0.97, 2)
	P.Borde(zona, color, 0.7)
	if texto then
		P.Texto(mundo, {
			Texto = texto,
			Tamano = Theme.Texto.Cuerpo,
			Fuente = Theme.Fuentes.Negrita,
			Color = color,
			Transparencia = 0.4,
			Espaciado = true,
			Posicion = UDim2.fromOffset(x, y - r - 10),
			Ancla = Vector2.new(0.5, 0.5),
			Z = 3,
		})
	end
end

local function dibujarMundo()
	local azar = Random.new(M.Semilla)
	-- Nebulosas: dos manchas grandes muy suaves.
	type Nebulosa = { X: number, Y: number, Ancho: number, Alto: number, Color: Color3 }
	local nebulosas: { Nebulosa } = {
		{ X = 1260, Y = 460, Ancho = 760, Alto = 520, Color = C.Habilidad },
		{ X = 380, Y = 520, Ancho = 800, Alto = 560, Color = C.AcentoOscuro },
	}
	for _, n in nebulosas do
		local mancha = P.Marco(mundo, {
			Tamano = UDim2.fromOffset(n.Ancho, n.Alto),
			Posicion = UDim2.fromOffset(n.X, n.Y),
			Ancla = Vector2.new(0.5, 0.5),
			Color = n.Color,
			Transparencia = 0.8,
			Radio = UDim.new(0.5, 0),
			Z = 1,
		})
		P.Degradado(
			mancha,
			ColorSequence.new(n.Color),
			0,
			NumberSequence.new({
				NumberSequenceKeypoint.new(0, 1),
				NumberSequenceKeypoint.new(0.5, 0.75),
				NumberSequenceKeypoint.new(1, 1),
			})
		)
	end
	-- Planetas no descubiertos: puntos tenues en una espiral de tres brazos.
	for i = 1, M.NoDescubiertos do
		local brazo = i % 3
		local t = azar:NextNumber() * 4.2
		local angulo = t + brazo * 2.09
		local radio = 90 + t * 150 + (azar:NextNumber() - 0.5) * 90
		local x = 800 + math.cos(angulo) * radio * 1.15
		local y = 500 + math.sin(angulo) * radio * 0.62
		punto(x, y, azar:NextNumber() * 1.6 + 0.8, C.PlanetaNoDescubierto, 0.65 + azar:NextNumber() * 0.25, 2)
	end
	-- Campo de asteroides: rocas sueltas a lo largo de un arco.
	for _ = 1, 70 do
		local angulo = -0.75 + azar:NextNumber() * 1.5
		local radio = 330 + (azar:NextNumber() - 0.5) * 46
		local r = azar:NextNumber() * 3.2 + 1
		local roca = punto(
			430 + math.cos(angulo) * radio,
			600 + math.sin(angulo) * radio * 0.55,
			r,
			C.Gris,
			0.35 + azar:NextNumber() * 0.4,
			2
		)
		roca.Size = UDim2.fromOffset(r * 2, r * 1.5)
	end
	P.Texto(mundo, {
		Texto = "CAMPO DE ASTEROIDES",
		Tamano = Theme.Texto.Grande,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Gris,
		Transparencia = 0.45,
		Espaciado = true,
		Posicion = UDim2.fromOffset(700, 805),
		Z = 3,
	})

	-- Zonas seguras, zona PvP y agujero negro de Umbra.
	local porId: { [string]: DatosDemo.PlanetaMapa } = {}
	for _, p in M.Planetas do
		porId[p.Id] = p
		if p.Tipo == "Bando" then
			anillo(p.X, p.Y, 120, colorDe(p), "ZONA SEGURA")
		elseif p.Disputado then
			anillo(p.X, p.Y, 40, C.Peligro, "PVP · DISPUTADO")
		end
		if p.Bando == "Monstruos" then
			local agujero = punto(p.X + 85, p.Y - 80, 14, C.Negro, 0, 3)
			P.Borde(agujero, C.DoradoOscuro, 0.2, 3)
			local disco = punto(p.X + 85, p.Y - 80, 24, C.PlanetaMonstruos, 0.85, 2)
			P.Borde(disco, C.PlanetaMonstruos, 0.6, 2)
		end
	end
	-- Rutas.
	for _, ruta in M.Rutas do
		local a, b = porId[ruta[1]], porId[ruta[2]]
		if a and b then
			discontinua(mundo, Vector2.new(a.X, a.Y), Vector2.new(b.X, b.Y), C.Acento, 0.72, 1.5, 3)
		end
	end
	rutaActiva = P.Marco(mundo, { Nombre = "RutaActiva", Tamano = UDim2.fromScale(1, 1), Z = 4 })

	-- Planetas descubiertos.
	for _, p in M.Planetas do
		local color = colorDe(p)
		local bando = p.Tipo == "Bando"
		local boton = P.Crear("TextButton", {
			Name = p.Id,
			Text = "",
			AutoButtonColor = false,
			Size = UDim2.fromOffset(p.R * 2, p.R * 2),
			Position = UDim2.fromOffset(p.X, p.Y),
			AnchorPoint = Vector2.new(0.5, 0.5),
			BackgroundColor3 = C.Blanco,
			ZIndex = 6,
			Parent = mundo,
		}) :: TextButton
		P.Esquinas(boton, UDim.new(0.5, 0))
		P.Degradado(
			boton,
			ColorSequence.new({
				ColorSequenceKeypoint.new(0, color:Lerp(C.Blanco, 0.55)),
				ColorSequenceKeypoint.new(0.45, color),
				ColorSequenceKeypoint.new(1, color:Lerp(C.Negro, 0.6)),
			}),
			45
		)
		local halo = P.Borde(boton, color, if bando then 0.35 else 0.55, if bando then 6 else 3)
		if bando then
			UITweens.Pulso(halo, "Transparency", 0.25, 0.6, Theme.Tweens.PulsoLento)
		end
		UITweens.Hover(boton)
		local etiqueta = P.Marco(mundo, {
			Tamano = UDim2.fromOffset(0, 14),
			Posicion = UDim2.fromOffset(p.X, p.Y + p.R + 5),
			Ancla = Vector2.new(0.5, 0),
			Z = 6,
		})
		etiqueta.AutomaticSize = Enum.AutomaticSize.X
		P.Lista(
			etiqueta,
			Enum.FillDirection.Horizontal,
			3,
			Enum.HorizontalAlignment.Center,
			Enum.VerticalAlignment.Center
		)
		if bando then
			IconBuilder.Icono(
				etiqueta,
				if p.Bando == "Monstruos" then "raza_monstruo" else "raza_humano",
				{ Tamano = 11, Color = color, Orden = 1, Z = 7 }
			)
		end
		P.Texto(etiqueta, {
			Texto = string.upper(p.N),
			Tamano = if bando then Theme.Texto.Titulo else Theme.Texto.Cuerpo,
			Fuente = Theme.Fuentes.Negrita,
			Color = if bando then color else C.TextoPrincipal,
			Espaciado = true,
			Contorno = true,
			Orden = 2,
			Z = 7,
		})
		boton.Activated:Connect(function()
			PanelMapa.Seleccionar(p.Id)
		end)
		botonesPlaneta[p.Id] = boton
	end

	-- Tu posición: flecha cian con un aro que late.
	local yo = P.Marco(mundo, {
		Nombre = "Yo",
		Tamano = UDim2.fromOffset(18, 18),
		Posicion = UDim2.fromOffset(M.Yo.X, M.Yo.Y),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 8,
	})
	IconBuilder.Icono(yo, "ui_posicion", { Tamano = 18, Color = C.Acento, Rotacion = 35, Z = 9 })
	local aro = P.Marco(yo, {
		Tamano = UDim2.fromOffset(36, 36),
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Radio = UDim.new(0.5, 0),
		Z = 8,
	})
	local bordeAro = P.Borde(aro, C.Acento, 0, Theme.Tamanos.TrazoActivo)
	UITweens.Infinito(
		UITweens.EscalaDe(aro),
		TweenInfo.new(1.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, -1),
		{ Scale = 1.6 }
	)
	UITweens.Infinito(
		bordeAro,
		TweenInfo.new(1.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, -1),
		{ Transparency = 1 }
	)
	P.Texto(mundo, {
		Texto = string.upper(M.Yo.Sector),
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Acento,
		Espaciado = true,
		Posicion = UDim2.fromOffset(M.Yo.X + 18, M.Yo.Y + 24),
		Z = 8,
	})
end

-- ===== Selección y viaje =====

local function distanciaA(p: DatosDemo.PlanetaMapa): number
	return (Vector2.new(p.X, p.Y) - Vector2.new(M.Yo.X, M.Yo.Y)).Magnitude
end

local function pintarPie()
	for _, hijo in pie:GetChildren() do
		if hijo:IsA("GuiObject") then
			hijo:Destroy()
		end
	end
	local p = seleccionado
	P.Texto(pie, {
		Texto = `TU POSICIÓN:  <font color="#{C.TextoPrincipal:ToHex()}">{M.Yo.Sector}</font>`,
		Rico = true,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Posicion = UDim2.fromOffset(12, 10),
		Z = 4,
	})
	P.Texto(pie, {
		Texto = if p
			then `DESTINO:  <font color="#{C.TextoPrincipal:ToHex()}">{p.N}</font>`
			else "DESTINO:  <i>[Selecciona un planeta]</i>",
		Rico = true,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Posicion = UDim2.fromOffset(12, 26),
		Z = 4,
	})
	local boton = P.Boton(pie, {
		Texto = "VIAJAR",
		Estilo = "Dorado",
		Tamano = UDim2.fromOffset(110, 26),
		Posicion = UDim2.fromOffset(12, 44),
		Z = 4,
		AlPulsar = PanelMapa.Viajar,
	})
	P.Habilitar(boton, p ~= nil)
end

function PanelMapa.Seleccionar(id: string?)
	seleccionado = nil
	for _, p in M.Planetas do
		if p.Id == id then
			seleccionado = p
		end
	end
	for idBoton, boton in botonesPlaneta do
		local borde = boton:FindFirstChildOfClass("UIStroke")
		if borde and idBoton == id then
			borde.Color = C.Blanco
		elseif borde then
			for _, p in M.Planetas do
				if p.Id == idBoton then
					borde.Color = colorDe(p)
				end
			end
		end
	end
	pintarPie()
	for _, hijo in panel:GetChildren() do
		if hijo:IsA("GuiObject") then
			hijo:Destroy()
		end
	end
	local p = seleccionado
	if p == nil then
		UITweens.Fundir(panel, false, Theme.Tweens.Rapido)
		return
	end
	local color = colorDe(p)
	local enemigo = p.Bando ~= nil and p.Bando ~= EstadoUI.Jugador().Bando
	local contenido = P.Marco(panel, { Nombre = "Contenido", Tamano = UDim2.new(1, 0, 0, 0), Z = 31 })
	contenido.AutomaticSize = Enum.AutomaticSize.Y
	P.Relleno(contenido, 12)
	P.Lista(contenido, Enum.FillDirection.Vertical, 5, Enum.HorizontalAlignment.Center)
	IconBuilder.Arte(contenido, p.A, { Tamano = 84, Orden = 1, Z = 32, ColorRespaldo = color })
	P.Texto(contenido, {
		Texto = string.upper(p.N),
		Tamano = Theme.Texto.Destacado - 1,
		Fuente = Theme.Fuentes.Negrita,
		Espaciado = true,
		Orden = 2,
		Z = 32,
	})
	P.Texto(contenido, {
		Texto = nombreTipo(p),
		Tamano = Theme.Texto.Mini + 0.5,
		Fuente = Theme.Fuentes.Negrita,
		Color = color,
		Espaciado = true,
		Orden = 3,
		Z = 32,
	})
	local segundos = distanciaA(p) * M.SegundosPorUnidad
	type Fila = { Nombre: string, Valor: string, Color: Color3 }
	local filas: { Fila } = {
		{ Nombre = "DISTANCIA", Valor = `{P.Numero(distanciaA(p) * M.KmPorUnidad)} km`, Color = C.TextoPrincipal },
		{ Nombre = "VIAJE", Valor = `{P.MinSeg(segundos)} min`, Color = C.TextoPrincipal },
		{ Nombre = "RECURSOS", Valor = p.Recursos, Color = C.TextoPrincipal },
		{
			Nombre = "PvP",
			Valor = if p.Disputado
				then "Disputado"
				elseif enemigo then "Territorio enemigo"
				elseif p.Bando then "Zona segura"
				else "Activo",
			Color = if p.Disputado or enemigo then C.PeligroClaro else C.Exito,
		},
	}
	for i, f in filas do
		local linea = P.Marco(contenido, { Tamano = UDim2.new(1, 0, 0, 16), Orden = 3 + i, Z = 32 })
		P.Marco(linea, {
			Tamano = UDim2.new(1, 0, 0, 1),
			Posicion = UDim2.fromScale(0, 1),
			Color = C.Blanco,
			Transparencia = 0.96,
			Z = 32,
		})
		P.Texto(linea, {
			Texto = f.Nombre,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Negrita,
			Color = C.TextoSecundario,
			Transparencia = A.TextoSecundario,
			Espaciado = true,
			Posicion = UDim2.fromScale(0, 0.5),
			Ancla = Vector2.new(0, 0.5),
			Z = 33,
		})
		P.Texto(linea, {
			Texto = f.Valor,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Titulo,
			Color = f.Color,
			Posicion = UDim2.fromScale(1, 0.5),
			Ancla = Vector2.new(1, 0.5),
			Z = 33,
		})
	end
	P.Texto(contenido, {
		Texto = `Descubierto por <font color="#{C.Dorado:ToHex()}"><b>{p.Por}</b></font>`,
		Rico = true,
		Tamano = Theme.Texto.Mini + 0.5,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Orden = 10,
		Z = 32,
	})
	P.Boton(contenido, {
		Texto = "VIAJAR",
		Estilo = "Dorado",
		Tamano = UDim2.new(1, 0, 0, 26),
		Orden = 11,
		Z = 32,
		AlPulsar = PanelMapa.Viajar,
	})
	UITweens.Fundir(panel, true, Theme.Tweens.Rapido)
end

-- TODO(servidor/naves): pedir el viaje (piloto automático o salto). Ahora solo marca la ruta y avisa.
function PanelMapa.Viajar()
	local p = seleccionado
	if p == nil then
		return
	end
	for _, hijo in rutaActiva:GetChildren() do
		hijo:Destroy()
	end
	local trozos = discontinua(rutaActiva, Vector2.new(M.Yo.X, M.Yo.Y), Vector2.new(p.X, p.Y), C.Dorado, 0, 2.5, 5)
	for i, trozo in trozos do
		task.delay(i * 0.02, function()
			UITweens.Pulso(trozo, "BackgroundTransparency", 0, 0.6, Theme.Tweens.Pulso)
		end)
	end
	ctx.Notificar({
		Titulo = `Rumbo a {p.N}`,
		Texto = `Llegada en {P.MinSeg(distanciaA(p) * M.SegundosPorUnidad)} · cuidado con los asteroides`,
		Color = C.Dorado,
		Icono = "ui_viajar",
	})
end

-- ===== Entrada (arrastrar y zoom) =====

local function conectarEntrada()
	local arrastre: { Inicio: Vector2, Desde: Vector2 }? = nil
	local function unidades(pixeles: Vector2): Vector2
		return ctx.AUnidades(pixeles)
			- Vector2.new(
					vista.AbsolutePosition.X - ctx.Raiz.AbsolutePosition.X,
					vista.AbsolutePosition.Y - ctx.Raiz.AbsolutePosition.Y
				)
				/ (ctx.Raiz.AbsoluteSize.X / ctx.Raiz.Size.X.Offset)
	end
	vista.InputBegan:Connect(function(entrada)
		if
			entrada.UserInputType == Enum.UserInputType.MouseButton1
			or entrada.UserInputType == Enum.UserInputType.Touch
		then
			arrastre = { Inicio = Vector2.new(entrada.Position.X, entrada.Position.Y), Desde = desplazamiento }
		end
	end)
	vista.InputChanged:Connect(function(entrada)
		if entrada.UserInputType == Enum.UserInputType.MouseWheel then
			local raton = UserInputService:GetMouseLocation()
			hacerZoom(if entrada.Position.Z > 0 then 1.12 else 1 / 1.12, unidades(raton))
		end
	end)
	UserInputService.InputChanged:Connect(function(entrada)
		local a = arrastre
		if
			a
			and (
				entrada.UserInputType == Enum.UserInputType.MouseMovement
				or entrada.UserInputType == Enum.UserInputType.Touch
			)
		then
			local escalaLienzo = ctx.Raiz.AbsoluteSize.X / ctx.Raiz.Size.X.Offset
			local d = (Vector2.new(entrada.Position.X, entrada.Position.Y) - a.Inicio) / escalaLienzo
			desplazamiento = a.Desde + d
			aplicarVista()
		end
	end)
	UserInputService.InputEnded:Connect(function(entrada)
		if
			entrada.UserInputType == Enum.UserInputType.MouseButton1
			or entrada.UserInputType == Enum.UserInputType.Touch
		then
			arrastre = nil
		end
	end)
	-- Pellizco en móvil.
	UserInputService.TouchPinch:Connect(function(_, escalaPellizco, _, estado)
		if ventana.EstaAbierta() and estado == Enum.UserInputState.Change then
			arrastre = nil
			hacerZoom(math.clamp(escalaPellizco, 0.9, 1.1))
		end
	end)
end

-- ===== API =====

function PanelMapa.Iniciar(contexto: Contexto.Contexto)
	ctx = contexto
	ventana = Ventana.Crear(contexto.Raiz, {
		Nombre = "Mapa",
		Titulo = "MAPA GALÁCTICO",
		Subtitulo = `{M.NoDescubiertos + #M.Planetas} PLANETAS · {#M.Planetas} DESCUBIERTOS`,
		Icono = "sidebar_mapa",
		Tecla = "M",
		AlCerrar = contexto.Cerrar,
	})
	local cuerpo = ventana.Cuerpo
	vista = P.Marco(cuerpo, {
		Nombre = "Vista",
		Tamano = UDim2.fromOffset(
			Theme.Tamanos.Ventana.Ancho,
			Theme.Tamanos.Ventana.Alto - Theme.Tamanos.Ventana.Titulo
		),
		Color = C.FondoProfundo,
		Transparencia = 0.2,
		Recortar = true,
		Radio = Theme.Tamanos.RadioVentana,
		Z = 2,
	})
	P.Degradado(vista, ColorSequence.new(C.Fondo3, C.FondoNegro), 90)
	mundo = P.Marco(vista, { Nombre = "Mundo", Tamano = UDim2.fromOffset(ANCHO_MUNDO, ALTO_MUNDO), Z = 2 })
	escala = Instance.new("UIScale")
	escala.Parent = mundo
	dibujarMundo()

	-- Leyenda.
	local leyenda = P.Caja(
		cuerpo,
		{ Nombre = "Leyenda", Tamano = UDim2.fromOffset(110, 0), Posicion = UDim2.fromOffset(12, 12), Z = 20 }
	)
	leyenda.AutomaticSize = Enum.AutomaticSize.Y
	P.Relleno(leyenda, 8, 10)
	P.Lista(leyenda, Enum.FillDirection.Vertical, 4)
	P.Etiqueta(leyenda, "LEYENDA", { Orden = 0, Z = 21 })
	local tipos = {
		{ "Habitable", "Habitable" },
		{ "Esteril", "Estéril" },
		{ "Volcanico", "Volcánico" },
		{ "Acuatico", "Acuático" },
	}
	for i, t in tipos do
		local fila = P.Marco(leyenda, { Tamano = UDim2.new(1, 0, 0, 10), Orden = i, Z = 21 })
		P.Marco(fila, {
			Tamano = UDim2.fromOffset(8, 8),
			Posicion = UDim2.fromScale(0, 0.5),
			Ancla = Vector2.new(0, 0.5),
			Color = Theme.TipoPlaneta[t[1]],
			Radio = UDim.new(1, 0),
			Z = 22,
		})
		P.Texto(fila, {
			Texto = t[2],
			Tamano = Theme.Texto.Mini + 0.5,
			Fuente = Theme.Fuentes.Titulo,
			Color = C.TextoPrincipal,
			Transparencia = A.TextoMedio,
			Posicion = UDim2.new(0, 14, 0.5, 0),
			Ancla = Vector2.new(0, 0.5),
			Z = 22,
		})
	end
	local fila = P.Marco(leyenda, { Tamano = UDim2.new(1, 0, 0, 10), Orden = 5, Z = 21 })
	P.Marco(fila, {
		Tamano = UDim2.fromOffset(8, 8),
		Posicion = UDim2.fromScale(0, 0.5),
		Ancla = Vector2.new(0, 0.5),
		Color = C.PlanetaNoDescubierto,
		Transparencia = 0.65,
		Radio = UDim.new(1, 0),
		Z = 22,
	})
	P.Texto(fila, {
		Texto = "No descubierto",
		Tamano = Theme.Texto.Mini + 0.5,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoPrincipal,
		Transparencia = A.TextoMedio,
		Posicion = UDim2.new(0, 14, 0.5, 0),
		Ancla = Vector2.new(0, 0.5),
		Z = 22,
	})

	-- Pie: tu posición, destino y VIAJAR.
	pie = P.Caja(cuerpo, {
		Nombre = "Pie",
		Tamano = UDim2.fromOffset(330, 80),
		Posicion = UDim2.new(0, 12, 1, -12),
		Ancla = Vector2.new(0, 1),
		Z = 20,
	})
	pintarPie()

	-- Zoom.
	local zoomMarco = P.Marco(cuerpo, {
		Nombre = "Zoom",
		Tamano = UDim2.fromOffset(140, 70),
		Posicion = UDim2.new(1, -12, 1, -12),
		Ancla = Vector2.new(1, 1),
		Z = 20,
	})
	type BotonZoom = { Texto: string, Factor: number }
	local botonesZoom: { BotonZoom } = { { Texto = "+", Factor = 1.25 }, { Texto = "−", Factor = 0.8 } }
	for i, z in botonesZoom do
		P.Boton(zoomMarco, {
			Texto = z.Texto,
			Estilo = "Borde",
			Tamano = UDim2.fromOffset(26, 26),
			Posicion = UDim2.new(1, 0, 0, (i - 1) * 30),
			Ancla = Vector2.new(1, 0),
			TamanoTexto = Theme.Texto.Destacado,
			Z = 21,
			AlPulsar = function()
				hacerZoom(z.Factor)
			end,
		})
	end
	P.Texto(zoomMarco, {
		Texto = "Rueda: zoom · Arrastrar: mover",
		Tamano = Theme.Texto.Micro + 0.5,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Posicion = UDim2.fromScale(1, 1),
		Ancla = Vector2.new(1, 1),
		Z = 21,
	})

	-- Ficha del planeta seleccionado.
	panel = P.Grupo(cuerpo, {
		Nombre = "Ficha",
		Tamano = UDim2.fromOffset(230, 0),
		Posicion = UDim2.new(1, -12, 0, 12),
		Ancla = Vector2.new(1, 0),
		Color = C.FondoProfundo,
		Transparencia = 0.08,
		Z = 30,
	})
	panel.AutomaticSize = Enum.AutomaticSize.Y
	panel.Visible = false
	P.Esquinas(panel, Theme.Tamanos.BorderRadius)
	P.Borde(panel, C.Acento, A.BordeSutil)

	conectarEntrada()
	centrar()
end

function PanelMapa.Mostrar()
	centrar()
	ventana.Abrir()
end

function PanelMapa.Ocultar()
	ventana.Cerrar()
end

return PanelMapa
