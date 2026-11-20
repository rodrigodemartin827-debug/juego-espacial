--!strict
--[[
	PanelRanked: pantalla RANKED.

	  ┌ TU RANGO ───────────────────┐  ┌ LEADERBOARD ───────────── TOP 100 ┐
	  │ [insignia] Plata III         │  │ #1 xProGamer   (Estelar) 4.891   │  oro
	  │ 1.247 / 1.500 ELO ▬▬▬▬▬     │  │ #2 NovaKiller  (Diamante) 3.456  │  plata
	  │ W/L 67%  84 V · 41 D         │  │ #3 ...                           │  bronce
	  └──────────────────────────────┘  │ ...                              │
	  MODOS [1v1] [2v2] [3v3] [4v4]      │ #1.284 Rodrixx_777 (tú)          │  cian
	  ┌ BUSCANDO PARTIDA... ─────────┐  └──────────────────────────────────┘
	  │ ▬▬▬▬▬▬░░░  0:34  Jugadores 3/4│
	  │ [CANCELAR]                    │
	  └──────────────────────────────┘
	  BRONCE → PLATA → ORO → PLATINO → DIAMANTE → MAESTRO → GRAN MAESTRO → ESTELAR

	Cada rango tiene su insignia (escudo con un diseño distinto por tier) teñida de su color. ESTELAR, el rango
	supremo, lleva un degradado arcoíris/dorado que se mueve sin parar.

	El ranked aún no tiene servidor: la búsqueda es una simulación de demostración.
]]

local Theme = require(script.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Componentes.Primitivas)
local Ventana = require(script.Parent.Componentes.Ventana)
local CardModo = require(script.Parent.Componentes.CardModo)
local DatosDemo = require(script.Parent.Datos.DatosDemo)
local EstadoUI = require(script.Parent.EstadoUI)
local Contexto = require(script.Parent.Contexto)

local C = Theme.Colores
local A = Theme.Alpha

local PanelRanked = {}

local ctx: Contexto.Contexto = nil :: any
local ventana: Ventana.Ventana = nil :: any
local busqueda: Frame = nil :: any
local tarjetas: { [string]: CardModo.CardModo } = {}
local buscando: { Modo: string, Jugadores: number, Inicio: number, Hilo: thread }? = nil

type Colocacion = { Posicion: UDim2?, Ancla: Vector2?, Orden: number?, Z: number? }

-- Insignia de un rango (icono teñido; Estelar con degradado animado).
local function insignia(padre: Instance, idRango: string, lado: number, o: Colocacion?): ImageLabel
	local op: Colocacion = o or {}
	local rango = Theme.Rango(idRango)
	local imagen = IconBuilder.Icono(padre, rango.Icono, {
		Tamano = lado,
		Color = if idRango == "Estelar" then C.Blanco else rango.Color,
		Posicion = op.Posicion,
		Ancla = op.Ancla,
		Orden = op.Orden,
		Z = op.Z or 5,
	})
	if idRango == "Estelar" then
		local degradado = P.Degradado(imagen, Theme.Degradados.Estelar, 0)
		UITweens.Arcoiris(degradado)
	end
	return imagen
end

-- Texto con el nombre del rango (Estelar con el mismo degradado animado).
local function textoRango(padre: Instance, idRango: string, texto: string, tamano: number, o: Colocacion?): TextLabel
	local op: Colocacion = o or {}
	local rango = Theme.Rango(idRango)
	local etiqueta = P.Texto(padre, {
		Texto = texto,
		Tamano = tamano,
		Fuente = Theme.Fuentes.Negrita,
		Color = if idRango == "Estelar" then C.Blanco else rango.Color,
		Posicion = op.Posicion,
		Ancla = op.Ancla,
		Orden = op.Orden,
		Z = op.Z or 5,
	})
	if idRango == "Estelar" then
		UITweens.Arcoiris(P.Degradado(etiqueta, Theme.Degradados.Estelar, 0))
	end
	return etiqueta
end

-- ===== Tu rango =====

local function construirRango(cuerpo: Frame)
	local k = DatosDemo.Ranked
	local rango = Theme.Rango(k.Rango)
	local caja = P.Caja(
		cuerpo,
		{ Nombre = "TuRango", Tamano = UDim2.fromOffset(404, 120), Posicion = UDim2.fromOffset(12, 12), Z = 3 }
	)
	local halo = P.Marco(caja, {
		Tamano = UDim2.fromOffset(80, 80),
		Posicion = UDim2.new(0, 60, 0.5, 0),
		Ancla = Vector2.new(0.5, 0.5),
		Color = rango.Color,
		Transparencia = 0.86,
		Radio = UDim.new(0.5, 0),
		Z = 3,
	})
	UITweens.Pulso(halo, "BackgroundTransparency", 0.9, 0.78, Theme.Tweens.PulsoLento)
	insignia(caja, k.Rango, 88, { Posicion = UDim2.new(0, 60, 0.5, 0), Ancla = Vector2.new(0.5, 0.5) })

	local info = P.Marco(caja, { Tamano = UDim2.new(1, -130, 1, -24), Posicion = UDim2.fromOffset(118, 12), Z = 4 })
	P.Etiqueta(info, "TU RANGO", { Posicion = UDim2.fromOffset(0, 4), Z = 4 })
	textoRango(
		info,
		k.Rango,
		`{rango.Nombre} {k.Division}`,
		Theme.Texto.Gigante,
		{ Posicion = UDim2.fromOffset(0, 14), Z = 4 }
	)
	P.Texto(info, {
		Texto = `{P.Numero(k.Elo)} / {P.Numero(k.Siguiente)} ELO`,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoPrincipal,
		Transparencia = A.TextoMedio,
		Posicion = UDim2.fromOffset(0, 44),
		Z = 4,
	})
	P.Texto(info, {
		Texto = `Oro a {P.Numero(k.Siguiente - k.Elo)}`,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.Oro,
		Posicion = UDim2.new(1, 0, 0, 44),
		Ancla = Vector2.new(1, 0),
		Z = 4,
	})
	local _, relleno = P.BarraProgreso(
		info,
		{ Tamano = UDim2.new(1, 0, 0, 7), Posicion = UDim2.fromOffset(0, 58), Z = 4 },
		Theme.Degradados.Elo
	)
	relleno.Size = UDim2.fromScale((k.Elo - rango.Elo) / (k.Siguiente - rango.Elo), 1)
	local total = k.Victorias + k.Derrotas
	P.Texto(info, {
		Texto = `W/L: <b>{math.floor(k.Victorias / total * 100 + 0.5)}%</b>     <font color="#{C.Exito:ToHex()}"><b>{k.Victorias}</b></font> V · <font color="#{C.Arma:ToHex()}"><b>{k.Derrotas}</b></font> D     RACHA: <font color="#{C.Exito:ToHex()}"><b>{k.Racha}V</b></font>`,
		Rico = true,
		Tamano = Theme.Texto.Pequeno + 0.5,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoPrincipal,
		Transparencia = 0.3,
		Posicion = UDim2.fromOffset(0, 74),
		Z = 4,
	})
end

-- ===== Búsqueda de partida =====

local function pintarBusqueda()
	for _, hijo in busqueda:GetChildren() do
		if hijo:IsA("GuiObject") then
			hijo:Destroy()
		end
	end
	local b = buscando
	if b == nil then
		P.Etiqueta(
			busqueda,
			"ELIGE UN MODO PARA BUSCAR PARTIDA",
			{ Posicion = UDim2.fromScale(0.5, 0.5), Ancla = Vector2.new(0.5, 0.5), Tamano = Theme.Texto.Cuerpo, Z = 4 }
		)
		return
	end
	local segundos = os.clock() - b.Inicio
	local necesarios = b.Jugadores * 2
	local encontrados = math.min(necesarios, 1 + math.floor(segundos / 3))
	local completa = encontrados >= necesarios
	local titulo = P.Texto(busqueda, {
		Texto = if completa then "¡PARTIDA ENCONTRADA!" else "BUSCANDO PARTIDA...",
		Tamano = Theme.Texto.Grande,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Acento,
		Espaciado = true,
		Posicion = UDim2.new(0.5, 0, 0, 16),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 4,
	})
	if not completa then
		UITweens.Pulso(titulo, "TextTransparency", 0, 0.55, Theme.Tweens.Pulso)
	end
	local linea = P.Marco(busqueda, {
		Tamano = UDim2.fromOffset(290, 12),
		Posicion = UDim2.new(0.5, 0, 0, 36),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 4,
	})
	local _, relleno = P.BarraProgreso(
		linea,
		{ Tamano = UDim2.new(1, -54, 0, 7), Posicion = UDim2.fromScale(0, 0.5), Ancla = Vector2.new(0, 0.5), Z = 4 }
	)
	relleno.Size = UDim2.fromScale(encontrados / necesarios, 1)
	P.Texto(linea, {
		Texto = P.MinSeg(segundos),
		Tamano = Theme.Texto.Grande,
		Fuente = Theme.Fuentes.Negrita,
		Posicion = UDim2.fromScale(1, 0.5),
		Ancla = Vector2.new(1, 0.5),
		Z = 4,
	})
	local jugadores = P.Marco(
		busqueda,
		{ Tamano = UDim2.fromOffset(0, 12), Posicion = UDim2.new(0.5, 0, 0, 56), Ancla = Vector2.new(0.5, 0.5), Z = 4 }
	)
	jugadores.AutomaticSize = Enum.AutomaticSize.X
	P.Lista(jugadores, Enum.FillDirection.Horizontal, 5, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)
	P.Texto(jugadores, {
		Texto = `Jugadores: {encontrados}/{necesarios}`,
		Tamano = Theme.Texto.Pequeno + 0.5,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoPrincipal,
		Transparencia = A.TextoMedio,
		Orden = 0,
		Z = 4,
	})
	for i = 1, necesarios do
		local punto = P.Marco(jugadores, {
			Tamano = UDim2.fromOffset(8, 8),
			Color = if i <= encontrados then C.Acento else C.Blanco,
			Transparencia = if i <= encontrados then 0 else 0.9,
			Radio = UDim.new(1, 0),
			Orden = i,
			Z = 5,
		})
		P.Borde(punto, if i <= encontrados then C.Acento else C.Blanco, if i <= encontrados then 0.5 else 0.8)
	end
	P.Boton(busqueda, {
		Texto = "CANCELAR",
		Estilo = "Rojo",
		Tamano = UDim2.fromOffset(110, 22),
		Posicion = UDim2.new(0.5, 0, 1, -10),
		Ancla = Vector2.new(0.5, 1),
		Z = 4,
		AlPulsar = function()
			PanelRanked.CancelarBusqueda(true)
		end,
	})
end

function PanelRanked.CancelarBusqueda(avisar: boolean?)
	local b = buscando
	if b then
		task.cancel(b.Hilo)
		buscando = nil
		for _, tarjeta in tarjetas do
			tarjeta.Seleccionar(false)
		end
		pintarBusqueda()
		if avisar then
			ctx.Notificar({
				Titulo = "Búsqueda cancelada",
				Texto = "Has salido de la cola",
				Color = C.Peligro,
				Icono = "sidebar_ranked",
			})
		end
	end
end

-- TODO(servidor): pedir la cola de matchmaking; ahora es una simulación (un jugador más cada 3 s).
local function buscar(modo: string, jugadoresPorEquipo: number)
	PanelRanked.CancelarBusqueda(false)
	for id, tarjeta in tarjetas do
		tarjeta.Seleccionar(id == modo)
	end
	local inicio = os.clock()
	local hilo = task.spawn(function()
		while true do
			pintarBusqueda()
			local b = buscando
			if b and 1 + math.floor((os.clock() - inicio) / 3) >= jugadoresPorEquipo * 2 then
				ctx.Notificar({
					Titulo = "¡Partida encontrada!",
					Texto = `Arena {modo} (demo)`,
					Color = C.Acento,
					Icono = "sidebar_ranked",
				})
				return
			end
			task.wait(1)
		end
	end)
	buscando = { Modo = modo, Jugadores = jugadoresPorEquipo, Inicio = inicio, Hilo = hilo }
	pintarBusqueda()
end

-- ===== Leaderboard =====

local function filaTabla(
	padre: Instance,
	posicion: string,
	nombre: string,
	idRango: string,
	textoDelRango: string,
	elo: number,
	orden: number,
	estilo: string?
): Frame
	local fila = P.Marco(padre, { Nombre = nombre, Tamano = UDim2.new(1, 0, 0, 26), Orden = orden, Z = 4 })
	local colorTop = if estilo == "top1"
		then C.Oro
		elseif estilo == "top2" then C.Plata
		elseif estilo == "top3" then C.Bronce
		elseif estilo == "yo" then C.Acento
		else nil
	if colorTop then
		fila.BackgroundColor3 = colorTop
		fila.BackgroundTransparency = if estilo == "yo" then 0.88 else 0.84
		P.Degradado(
			fila,
			ColorSequence.new(colorTop),
			0,
			NumberSequence.new(if estilo == "yo" then 0 else 0.2, if estilo == "yo" then 0 else 1)
		)
		if estilo == "yo" then
			P.Borde(fila, C.Acento, A.BordeActivo)
		end
	end
	P.Marco(fila, {
		Tamano = UDim2.new(1, 0, 0, 1),
		Posicion = UDim2.fromScale(0, 1),
		Color = C.Blanco,
		Transparencia = 0.97,
		Z = 4,
	})
	P.Texto(fila, {
		Texto = posicion,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Color = colorTop or C.TextoSecundario,
		Transparencia = if colorTop then 0 else A.TextoSecundario,
		Posicion = UDim2.new(0, 12, 0.5, 0),
		Ancla = Vector2.new(0, 0.5),
		Z = 5,
	})
	P.Texto(fila, {
		Texto = nombre,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Color = if estilo
				and estilo ~= "yo"
				and colorTop
			then colorTop
			elseif estilo == "yo" then C.Acento
			else C.TextoPrincipal,
		Posicion = UDim2.new(0, 56, 0.5, 0),
		Ancla = Vector2.new(0, 0.5),
		Z = 5,
	})
	local celda = P.Marco(
		fila,
		{ Tamano = UDim2.fromOffset(108, 26), Posicion = UDim2.new(1, -76, 0, 0), Ancla = Vector2.new(1, 0), Z = 5 }
	)
	P.Lista(celda, Enum.FillDirection.Horizontal, 5, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	insignia(celda, idRango, 15, { Orden = 1, Z = 6 })
	textoRango(celda, idRango, textoDelRango, Theme.Texto.Pequeno, { Orden = 2, Z = 6 })
	P.Texto(fila, {
		Texto = P.Numero(elo),
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Color = if estilo == "yo" then C.Acento else C.TextoPrincipal,
		Posicion = UDim2.new(1, -12, 0.5, 0),
		Ancla = Vector2.new(1, 0.5),
		Z = 5,
	})
	return fila
end

local function construirTabla(cuerpo: Frame)
	local k = DatosDemo.Ranked
	local caja = P.Caja(cuerpo, {
		Nombre = "Leaderboard",
		Tamano = UDim2.fromOffset(420, 332),
		Posicion = UDim2.new(1, -12, 0, 12),
		Ancla = Vector2.new(1, 0),
		Recortar = true,
		Z = 3,
	})
	P.Texto(caja, {
		Texto = "LEADERBOARD",
		Tamano = Theme.Texto.Medio,
		Fuente = Theme.Fuentes.Negrita,
		Espaciado = true,
		Posicion = UDim2.fromOffset(12, 10),
		Z = 4,
	})
	P.Etiqueta(caja, "TOP 100 · GLOBAL", { Posicion = UDim2.new(1, -12, 0, 12), Ancla = Vector2.new(1, 0), Z = 4 })
	local lista = P.Crear("ScrollingFrame", {
		Name = "Filas",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 1, -62),
		Position = UDim2.fromOffset(0, 32),
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 4,
		ScrollBarImageColor3 = C.Acento,
		ScrollBarImageTransparency = 0.5,
		ZIndex = 4,
		Parent = caja,
	}) :: ScrollingFrame
	P.Lista(lista, Enum.FillDirection.Vertical, 0)
	for i, entrada in k.Tabla do
		filaTabla(
			lista,
			`#{i}`,
			entrada.Nombre,
			entrada.Rango,
			Theme.Rango(entrada.Rango).Nombre,
			entrada.Elo,
			i,
			if i <= 3 then `top{i}` else nil
		)
	end
	-- Tu posición, siempre visible abajo y resaltada en cian.
	local tu = filaTabla(
		caja,
		`#{P.Numero(k.Posicion)}`,
		`{EstadoUI.Jugador().Nombre} (tú)`,
		k.Rango,
		`{Theme.Rango(k.Rango).Nombre} {k.Division}`,
		k.Elo,
		0,
		"yo"
	)
	tu.Position = UDim2.new(0, 0, 1, -28)
end

-- ===== Escalera de rangos =====

local function construirEscalera(cuerpo: Frame)
	local k = DatosDemo.Ranked
	local caja = P.Caja(cuerpo, {
		Nombre = "Rangos",
		Tamano = UDim2.new(1, -24, 0, 76),
		Posicion = UDim2.new(0, 12, 1, -12),
		Ancla = Vector2.new(0, 1),
		Z = 3,
	})
	P.Relleno(caja, 0, 14)
	P.Lista(caja, Enum.FillDirection.Horizontal, 0, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center).HorizontalFlex =
		Enum.UIFlexAlignment.SpaceEvenly
	local actual = 1
	for i, r in Theme.Rangos do
		if r.Id == k.Rango then
			actual = i
		end
	end
	for i, r in Theme.Rangos do
		local peldano = P.Marco(caja, { Nombre = r.Id, Tamano = UDim2.fromOffset(84, 64), Orden = i * 2, Z = 4 })
		local esActual = i == actual
		insignia(
			peldano,
			r.Id,
			if esActual then 36 else 32,
			{ Posicion = UDim2.new(0.5, 0, 0, 2), Ancla = Vector2.new(0.5, 0), Z = 5 }
		)
		if esActual then
			local aro = P.Marco(peldano, {
				Tamano = UDim2.fromOffset(44, 44),
				Posicion = UDim2.new(0.5, 0, 0, 20),
				Ancla = Vector2.new(0.5, 0.5),
				Radio = UDim.new(0.5, 0),
				Z = 4,
			})
			P.Borde(aro, r.Color, 0.2, Theme.Tamanos.TrazoActivo)
		end
		local nombre = textoRango(
			peldano,
			r.Id,
			string.upper(r.Nombre),
			Theme.Texto.Mini + 0.5,
			{ Posicion = UDim2.new(0.5, 0, 0, 42), Ancla = Vector2.new(0.5, 0), Z = 5 }
		)
		nombre.TextTransparency = if i > actual then 0.45 else 0
		P.Texto(peldano, {
			Texto = `{P.Numero(r.Elo)}+{if r.Divisiones then " · III-I" else ""}`,
			Tamano = Theme.Texto.Micro,
			Fuente = Theme.Fuentes.Titulo,
			Color = C.TextoSecundario,
			Transparencia = A.TextoSecundario,
			Posicion = UDim2.new(0.5, 0, 0, 54),
			Ancla = Vector2.new(0.5, 0),
			Z = 5,
		})
		if i < #Theme.Rangos then
			P.Marco(caja, {
				Nombre = "Flecha",
				Tamano = UDim2.fromOffset(12, 1),
				Color = C.Acento,
				Transparencia = A.BordeActivo,
				Orden = i * 2 + 1,
				Z = 4,
			})
		end
	end
end

-- ===== API =====

function PanelRanked.Iniciar(contexto: Contexto.Contexto)
	ctx = contexto
	ventana = Ventana.Crear(contexto.Raiz, {
		Nombre = "Ranked",
		Titulo = "RANKED",
		Subtitulo = "TEMPORADA 3",
		Icono = "sidebar_ranked",
		AlCerrar = contexto.Cerrar,
	})
	local cuerpo = ventana.Cuerpo
	construirRango(cuerpo)
	P.Etiqueta(cuerpo, "MODOS", { Posicion = UDim2.fromOffset(12, 142), Z = 3 })
	local modos = P.Marco(
		cuerpo,
		{ Nombre = "Modos", Tamano = UDim2.fromOffset(404, 74), Posicion = UDim2.fromOffset(12, 156), Z = 3 }
	)
	P.Lista(modos, Enum.FillDirection.Horizontal, 8)
	for i, m in DatosDemo.Ranked.Modos do
		tarjetas[m.Modo] = CardModo.Crear(
			modos,
			{ Modo = m.Modo, Jugadores = m.Jugadores, Espera = m.Espera, Orden = i, AlPulsar = buscar }
		)
	end
	busqueda = P.Caja(
		cuerpo,
		{ Nombre = "Busqueda", Tamano = UDim2.fromOffset(404, 104), Posicion = UDim2.fromOffset(12, 240), Z = 3 }
	)
	pintarBusqueda()
	construirTabla(cuerpo)
	construirEscalera(cuerpo)
end

function PanelRanked.Mostrar()
	ventana.Abrir()
end

-- Cerrar la pantalla no cancela la búsqueda (como en cualquier juego con cola).
function PanelRanked.Ocultar()
	ventana.Cerrar()
end

return PanelRanked
