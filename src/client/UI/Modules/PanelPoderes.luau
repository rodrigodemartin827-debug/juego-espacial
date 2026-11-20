--!strict
--[[
	PanelPoderes: árbol de habilidades (barra lateral o tecla K).

	  CLASE: Explorador          [Combate] [Exploración] [Soporte]          PUNTOS DE HABILIDAD: 7
	           COMBATE 2/7              EXPLORACIÓN 4/7              SOPORTE 1/7
	  TIER 1   ●──●──○                  ●──●──●                      ●──○──○
	  TIER 2     ○──○                     ●──○                         ○──○
	  TIER 3      ○                        ○                            ○
	  ULTIMATE    ◉                        ◉                            ◉
	  ┌ [icono] Pulso Gravitatorio  TIER 1 · COMBATE ───────────── [DESBLOQUEAR — 1 punto] ┐

	  - Tres ramas con su color: Combate (rojo/naranja), Exploración (cian), Soporte (verde). La pestaña elegida resalta
	    su rama y apaga las otras.
	  - Nodo desbloqueado: relleno del color de la rama con brillo. Bloqueado: contorno gris e interior oscuro con
	    candado. Siguiente disponible: contorno que late. La ultimate es más grande y pide toda su rama.
	  - Las líneas unen los nodos en orden (progresión lineal).
	  - Los nodos de Combate son los poderes reales del juego (Rayo y Gravedad); el árbol con puntos es de demostración.
]]

local Theme = require(script.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Componentes.Primitivas)
local Ventana = require(script.Parent.Componentes.Ventana)
local TabSelector = require(script.Parent.Componentes.TabSelector)
local EstadoUI = require(script.Parent.EstadoUI)
local DatosDemo = require(script.Parent.Datos.DatosDemo)
local Contexto = require(script.Parent.Contexto)

local C = Theme.Colores
local A = Theme.Alpha

local PanelPoderes = {}

local ANCHO_COLUMNA = 282
local Y_TIER = { 42, 112, 176, 236 }

local ctx: Contexto.Contexto = nil :: any
local ventana: Ventana.Ventana = nil :: any
local textoPuntos: TextLabel = nil :: any
local arbol: Frame = nil :: any
local detalle: Frame = nil :: any
local ramaActiva = "Combate"
local seleccion = { Rama = "Combate", Indice = 3 }

-- Posición (en el marco del árbol) del nodo `i` de la columna `columna`.
local function posicionNodo(columna: number, rama: DatosDemo.Rama, i: number): Vector2
	local x0 = 150 + (columna - 1) * ANCHO_COLUMNA
	local nodo = rama.Nodos[i]
	-- Cuántos nodos del mismo tier hay antes que este.
	local k = 0
	for j = 1, i - 1 do
		if rama.Nodos[j].T == nodo.T then
			k += 1
		end
	end
	if nodo.T == 1 then
		return Vector2.new(x0 - 76 + k * 76, Y_TIER[1])
	elseif nodo.T == 2 then
		return Vector2.new(x0 - 44 + k * 88, Y_TIER[2])
	elseif nodo.T == 3 then
		return Vector2.new(x0, Y_TIER[3])
	end
	return Vector2.new(x0, Y_TIER[4])
end

-- Línea recta entre dos puntos: un marco fino girado.
local function linea(padre: Instance, a: Vector2, b: Vector2, color: Color3, grosor: number, transparencia: number)
	local d = b - a
	local marco = P.Marco(padre, {
		Nombre = "Linea",
		Tamano = UDim2.fromOffset(d.Magnitude, grosor),
		Posicion = UDim2.fromOffset((a.X + b.X) / 2, (a.Y + b.Y) / 2),
		Ancla = Vector2.new(0.5, 0.5),
		Color = color,
		Transparencia = transparencia,
		Z = 3,
	})
	marco.Rotation = math.deg(math.atan2(d.Y, d.X))
end

-- ===== Detalle del nodo seleccionado =====

local function pintarDetalle()
	for _, hijo in detalle:GetChildren() do
		if hijo:IsA("GuiObject") then
			hijo:Destroy()
		end
	end
	local rama: DatosDemo.Rama? = nil
	for _, r in DatosDemo.Arbol do
		if r.Id == seleccion.Rama then
			rama = r
		end
	end
	if rama == nil then
		return
	end
	local nodo = rama.Nodos[seleccion.Indice]
	local estado = EstadoUI.EstadoNodos(rama.Id)[seleccion.Indice]
	local color = Theme.Ramas[rama.Id]
	local puntos = EstadoUI.Jugador().PuntosHabilidad

	local icono = P.Marco(detalle, {
		Nombre = "Icono",
		Tamano = UDim2.fromOffset(60, 60),
		Posicion = UDim2.new(0, 14, 0.5, 0),
		Ancla = Vector2.new(0, 0.5),
		Color = color,
		Transparencia = 0.75,
		Radio = UDim.new(0.5, 0),
		Z = 4,
	})
	P.Degradado(icono, ColorSequence.new(color, C.Fondo1), 90)
	P.Borde(icono, color, 0, Theme.Tamanos.TrazoGrueso)
	IconBuilder.Icono(
		icono,
		nodo.I,
		{ Tamano = 30, Color = color, Posicion = UDim2.fromScale(0.5, 0.5), Ancla = Vector2.new(0.5, 0.5), Z = 5 }
	)

	local info = P.Marco(
		detalle,
		{ Nombre = "Info", Tamano = UDim2.new(1, -330, 1, -20), Posicion = UDim2.fromOffset(88, 12), Z = 4 }
	)
	P.Lista(info, Enum.FillDirection.Vertical, 4)
	local titulo = P.Marco(info, { Tamano = UDim2.new(1, 0, 0, 16), Orden = 1, Z = 4 })
	P.Lista(titulo, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	if nodo.T == 4 then
		IconBuilder.Icono(titulo, "ui_estrella", { Tamano = 11, Color = C.Dorado, Orden = 0, Z = 5 })
	end
	P.Texto(titulo, { Texto = nodo.N, Tamano = Theme.Texto.Titulo, Fuente = Theme.Fuentes.Negrita, Orden = 1, Z = 5 })
	local etiqueta = P.Texto(titulo, {
		Texto = `{if nodo.T == 4 then "ULTIMATE" else `TIER {nodo.T}`} · {rama.Nombre}`,
		Tamano = Theme.Texto.Mini + 0.5,
		Fuente = Theme.Fuentes.Negrita,
		Color = color,
		Espaciado = true,
		Orden = 2,
		Z = 5,
	})
	etiqueta.BackgroundColor3 = color
	etiqueta.BackgroundTransparency = 0.86
	P.Esquinas(etiqueta, UDim.new(0, 4))
	P.Relleno(etiqueta, 2, 6)
	P.Texto(info, {
		Texto = nodo.D,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Medio,
		Color = C.TextoPrincipal,
		Transparencia = A.TextoMedio,
		Orden = 2,
		Z = 4,
	})
	local datos = {}
	table.insert(datos, if nodo.Cd > 0 then `COOLDOWN: <b>{P.Decimal(nodo.Cd)} s</b>` else "PASIVA")
	if nodo.En > 0 then
		table.insert(datos, `COSTE: <b>{nodo.En} energía</b>`)
	end
	table.insert(datos, `PUNTOS: <b>{nodo.Coste}</b>`)
	P.Texto(info, {
		Texto = table.concat(datos, "     "),
		Rico = true,
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoPrincipal,
		Transparencia = 0.35,
		Orden = 3,
		Z = 4,
	})

	-- Acción: desbloquear (si es el siguiente y hay puntos), desbloqueado o bloqueado.
	local accion = P.Marco(detalle, {
		Nombre = "Accion",
		Tamano = UDim2.fromOffset(240, 46),
		Posicion = UDim2.new(1, -14, 0.5, 0),
		Ancla = Vector2.new(1, 0.5),
		Z = 4,
	})
	local boton: TextButton
	local pie: string
	if estado == 1 then
		boton = P.Boton(accion, {
			Texto = "DESBLOQUEADO",
			Estilo = "Borde",
			Tamano = UDim2.fromOffset(200, 28),
			Posicion = UDim2.fromScale(1, 0),
			Ancla = Vector2.new(1, 0),
			Z = 5,
		})
		P.Habilitar(boton, false)
		pie = "Ya forma parte de tu kit"
	elseif estado == 2 then
		local suficiente = puntos >= nodo.Coste
		boton = P.Boton(accion, {
			Texto = `DESBLOQUEAR — {nodo.Coste} punto{if nodo.Coste > 1 then "s" else ""}`,
			Estilo = "Cian",
			Tamano = UDim2.fromOffset(200, 28),
			Posicion = UDim2.fromScale(1, 0),
			Ancla = Vector2.new(1, 0),
			Z = 5,
			AlPulsar = function()
				if EstadoUI.DesbloquearNodo(rama.Id, seleccion.Indice) then
					ctx.Notificar({
						Titulo = "Poder desbloqueado",
						Texto = `{nodo.N} (demo)`,
						Color = color,
						Icono = nodo.I,
					})
				end
			end,
		})
		P.Habilitar(boton, suficiente)
		pie = if suficiente then `Te quedarán {puntos - nodo.Coste} puntos` else "No tienes puntos suficientes"
	else
		boton = P.Boton(accion, {
			Texto = "BLOQUEADO",
			Estilo = "Gris",
			Tamano = UDim2.fromOffset(200, 28),
			Posicion = UDim2.fromScale(1, 0),
			Ancla = Vector2.new(1, 0),
			Z = 5,
		})
		P.Habilitar(boton, false)
		pie = `Requiere el nodo anterior de {string.lower(rama.Nombre)}`
	end
	P.Texto(accion, {
		Texto = pie,
		Tamano = Theme.Texto.Mini,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Posicion = UDim2.new(1, 0, 1, 0),
		Ancla = Vector2.new(1, 1),
		Z = 5,
	})
end

-- ===== Árbol =====

local function crearNodo(columna: number, rama: DatosDemo.Rama, i: number, estado: number, apagada: boolean)
	local nodo = rama.Nodos[i]
	local color = Theme.Ramas[rama.Id]
	local ultimate = nodo.T == 4
	local lado = if ultimate then 54 else 40
	local pos = posicionNodo(columna, rama, i)
	local seleccionado = seleccion.Rama == rama.Id and seleccion.Indice == i

	local contenedor = P.Grupo(arbol, {
		Nombre = nodo.N,
		Tamano = UDim2.fromOffset(84, lado + 22),
		Posicion = UDim2.fromOffset(pos.X, pos.Y - lado / 2),
		Ancla = Vector2.new(0.5, 0),
		Z = 5,
	})
	contenedor.GroupTransparency = if apagada then 0.62 else 0

	local boton = P.Crear("TextButton", {
		Name = "Nodo",
		Text = "",
		AutoButtonColor = false,
		Size = UDim2.fromOffset(lado, lado),
		Position = UDim2.fromScale(0.5, 0),
		AnchorPoint = Vector2.new(0.5, 0),
		BackgroundColor3 = if estado == 1 then color else C.FondoProfundo,
		BackgroundTransparency = 0,
		ZIndex = 6,
		Parent = contenedor,
	}) :: TextButton
	P.Esquinas(boton, UDim.new(0.5, 0))
	if estado == 1 then
		P.Degradado(boton, ColorSequence.new(color:Lerp(C.Blanco, 0.45), color), 90)
	end
	local borde = P.Borde(
		boton,
		if estado == 0 then C.GrisOscuro else (if estado == 1 then C.Blanco else color),
		if estado == 1 then 0.65 else 0,
		if estado == 2 then Theme.Tamanos.TrazoGrueso else Theme.Tamanos.TrazoActivo
	)
	if estado == 2 then
		UITweens.Pulso(borde, "Transparency", 0, 0.6, Theme.Tweens.Pulso)
	end
	IconBuilder.Icono(boton, nodo.I, {
		Tamano = if ultimate then 26 else 20,
		Color = if estado == 1 then C.Fondo1 elseif estado == 2 then color else C.Gris,
		Transparencia = if estado == 0 then 0.55 else 0,
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 7,
	})
	if estado == 0 then
		local candado = P.Marco(boton, {
			Nombre = "Candado",
			Tamano = UDim2.fromOffset(13, 13),
			Posicion = UDim2.new(1, 2, 1, 2),
			Ancla = Vector2.new(1, 1),
			Color = C.FondoProfundo,
			Radio = UDim.new(1, 0),
			Z = 8,
		})
		P.Borde(candado, C.GrisOscuro, 0)
		IconBuilder.Icono(
			candado,
			"ui_candado",
			{ Tamano = 7, Color = C.Gris, Posicion = UDim2.fromScale(0.5, 0.5), Ancla = Vector2.new(0.5, 0.5), Z = 9 }
		)
	end
	if ultimate then
		local anillo = P.Marco(contenedor, {
			Nombre = "Anillo",
			Tamano = UDim2.fromOffset(lado + 10, lado + 10),
			Posicion = UDim2.new(0.5, 0, 0, lado / 2),
			Ancla = Vector2.new(0.5, 0.5),
			Radio = UDim.new(0.5, 0),
			Z = 5,
		})
		P.Borde(anillo, color, 0.55, Theme.Tamanos.TrazoActivo)
	end
	if seleccionado then
		local marca = P.Marco(contenedor, {
			Nombre = "Seleccion",
			Tamano = UDim2.fromOffset(lado + 8, lado + 8),
			Posicion = UDim2.new(0.5, 0, 0, lado / 2),
			Ancla = Vector2.new(0.5, 0.5),
			Radio = UDim.new(0.5, 0),
			Z = 5,
		})
		P.Borde(marca, C.Blanco, 0, Theme.Tamanos.TrazoGrueso)
	end
	P.Texto(contenedor, {
		Texto = nodo.N,
		Tamano = Theme.Texto.Micro + 0.5,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoPrincipal,
		Transparencia = if estado == 1 then 0.3 else 0.6,
		AlineacionX = Enum.TextXAlignment.Center,
		AlineacionY = Enum.TextYAlignment.Top,
		Caja = UDim2.fromOffset(84, 18),
		Posicion = UDim2.fromOffset(0, lado + 3),
		Envolver = true,
		Z = 6,
	})
	UITweens.Hover(boton)
	boton.Activated:Connect(function()
		seleccion = { Rama = rama.Id, Indice = i }
		ramaActiva = rama.Id
		PanelPoderes.Refrescar()
	end)
end

function PanelPoderes.Refrescar()
	for _, hijo in arbol:GetChildren() do
		if hijo:IsA("GuiObject") then
			hijo:Destroy()
		end
	end
	textoPuntos.Text = P.Espaciar(`PUNTOS DE HABILIDAD: {EstadoUI.Jugador().PuntosHabilidad}`)
	for t, y in Y_TIER do
		P.Etiqueta(
			arbol,
			if t == 4 then "ULTIMATE" else `TIER {t}`,
			{ Posicion = UDim2.fromOffset(0, y), Ancla = Vector2.new(0, 0.5), Z = 4 }
		)
	end
	for columna, rama in DatosDemo.Arbol do
		local estados = EstadoUI.EstadoNodos(rama.Id)
		local color = Theme.Ramas[rama.Id]
		local apagada = rama.Id ~= ramaActiva
		local hechos = 0
		for _, e in estados do
			if e == 1 then
				hechos += 1
			end
		end
		P.Texto(arbol, {
			Texto = `{rama.Nombre}  <font transparency="0.5">{hechos}/{#rama.Nodos}</font>`,
			Rico = true,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Negrita,
			Color = color,
			Transparencia = if apagada then 0.55 else 0,
			Posicion = UDim2.fromOffset(150 + (columna - 1) * ANCHO_COLUMNA, 6),
			Ancla = Vector2.new(0.5, 0.5),
			Z = 4,
		})
		-- Líneas (por debajo de los nodos).
		for i = 2, #rama.Nodos do
			local activa = estados[i - 1] == 1 and estados[i] == 1
			linea(
				arbol,
				posicionNodo(columna, rama, i - 1),
				posicionNodo(columna, rama, i),
				if activa then color else C.GrisOscuro,
				if activa then 2.5 else 1.5,
				if apagada then 0.65 elseif activa then 0 else 0.3
			)
		end
		for i in rama.Nodos do
			crearNodo(columna, rama, i, estados[i], apagada)
		end
	end
	pintarDetalle()
end

-- ===== API =====

function PanelPoderes.Iniciar(contexto: Contexto.Contexto)
	ctx = contexto
	ventana = Ventana.Crear(contexto.Raiz, {
		Nombre = "Poderes",
		Titulo = "PODERES",
		Subtitulo = "ÁRBOL DE HABILIDADES",
		Icono = "sidebar_poderes",
		Tecla = "K",
		AlCerrar = contexto.Cerrar,
	})
	local cuerpo = ventana.Cuerpo
	local arriba = P.Marco(
		cuerpo,
		{ Nombre = "Arriba", Tamano = UDim2.new(1, -24, 0, 30), Posicion = UDim2.fromOffset(12, 12), Z = 3 }
	)
	local clase = P.Marco(arriba, { Tamano = UDim2.fromOffset(200, 30), Z = 3 })
	P.Lista(clase, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	IconBuilder.Icono(clase, "sidebar_personaje", { Tamano = 13, Color = C.Acento, Orden = 1, Z = 4 })
	P.Texto(clase, {
		Texto = `CLASE:  <font color="#{C.TextoPrincipal:ToHex()}">{EstadoUI.Jugador().Clase}</font>`,
		Rico = true,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.TextoPrincipal,
		Transparencia = A.TextoMedio,
		Orden = 2,
		Z = 4,
	})

	local opciones: { TabSelector.Opcion } = {}
	for _, rama in DatosDemo.Arbol do
		table.insert(opciones, { Id = rama.Id, Texto = rama.Nombre, Color = Theme.Ramas[rama.Id] })
	end
	local pestanas = TabSelector.Crear(arriba, {
		Opciones = opciones,
		Inicial = ramaActiva,
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		AlCambiar = function(id: string)
			ramaActiva = id
			-- Al cambiar de rama se selecciona su siguiente nodo disponible.
			local estados = EstadoUI.EstadoNodos(id)
			seleccion = { Rama = id, Indice = math.max(1, table.find(estados, 2) or 1) }
			PanelPoderes.Refrescar()
		end,
	})
	pestanas.Marco.AnchorPoint = Vector2.new(0.5, 0.5)

	textoPuntos = P.Texto(arriba, {
		Texto = "",
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Acento,
		Posicion = UDim2.new(1, 0, 0.5, 0),
		Ancla = Vector2.new(1, 0.5),
		Z = 4,
	})
	textoPuntos.BackgroundColor3 = C.Acento
	textoPuntos.BackgroundTransparency = 0.9
	P.Esquinas(textoPuntos, Theme.Tamanos.RadioBoton)
	P.Borde(textoPuntos, C.Acento, A.BordeActivo)
	P.Relleno(textoPuntos, 5, 10)

	arbol = P.Marco(
		cuerpo,
		{ Nombre = "Arbol", Tamano = UDim2.new(1, -24, 0, 262), Posicion = UDim2.fromOffset(12, 52), Z = 3 }
	)
	detalle = P.Caja(cuerpo, {
		Nombre = "Detalle",
		Tamano = UDim2.new(1, -24, 0, 92),
		Posicion = UDim2.new(0, 12, 1, -12),
		Ancla = Vector2.new(0, 1),
		Z = 3,
	})

	EstadoUI.Cambio:Conectar(function(que: string)
		if que == "Arbol" and ventana.EstaAbierta() then
			PanelPoderes.Refrescar()
		end
	end)
	PanelPoderes.Refrescar()
end

function PanelPoderes.Mostrar()
	PanelPoderes.Refrescar()
	ventana.Abrir()
end

function PanelPoderes.Ocultar()
	ventana.Cerrar()
end

return PanelPoderes
