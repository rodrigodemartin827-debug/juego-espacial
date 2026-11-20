--!strict
--[[
	Ventana: marco común de todas las pantallas de menú (Personaje, Poderes, Clan...).

	  ┌─[icono] TÍTULO  subtítulo ────────────── [tecla] [X]┐
	  │ cuerpo (872 × 444 unidades)                          │
	  └──────────────────────────────────────────────────────┘

	Fondo con degradado azul marino (#0A142D → #0B1628 → #101B35) y textura sutil (rejilla y puntos de estrellas), borde
	cian del 12 %, esquinas decorativas y el botón X rojo de cerrar arriba a la derecha. Abrir y cerrar es un único
	fundido + deslizamiento de toda la ventana (UITweens.AbrirVentana / CerrarVentana).
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores
local A = Theme.Alpha
local V = Theme.Tamanos.Ventana

local Ventana = {}

export type Ventana = {
	Marco: Frame,
	Cuerpo: Frame,
	Titulo: TextLabel,
	Subtitulo: TextLabel,
	PonerSubtitulo: (texto: string) -> (),
	Abrir: () -> (),
	Cerrar: () -> (),
	EstaAbierta: () -> boolean,
}

export type Opciones = {
	Nombre: string,
	Titulo: string,
	Subtitulo: string?,
	Icono: string,
	ColorIcono: Color3?,
	Tecla: string?, -- se enseña junto a la X
	AlCerrar: () -> (),
}

-- Puntos de "estrellas" de la textura de fondo (posiciones en escala, fijas).
local ESTRELLAS =
	{ { 0.12, 0.18 }, { 0.72, 0.12 }, { 0.88, 0.64 }, { 0.34, 0.82 }, { 0.56, 0.46 }, { 0.22, 0.6 }, { 0.93, 0.3 } }

-- Esquina decorativa: dos líneas finas en L.
local function esquina(padre: Instance, x: number, y: number)
	local ancla = Vector2.new(x, y)
	local posicion = UDim2.new(x, if x == 0 then 4 else -4, y, if y == 0 then 4 else -4)
	P.Marco(padre, {
		Nombre = "EsquinaH",
		Tamano = UDim2.fromOffset(12, 1.5),
		Posicion = posicion,
		Ancla = ancla,
		Color = C.Acento,
		Transparencia = 0.3,
		Z = 5,
	})
	P.Marco(padre, {
		Nombre = "EsquinaV",
		Tamano = UDim2.fromOffset(1.5, 12),
		Posicion = posicion,
		Ancla = ancla,
		Color = C.Acento,
		Transparencia = 0.3,
		Z = 5,
	})
end

function Ventana.Crear(padre: Instance, o: Opciones): Ventana
	local posicion = UDim2.fromOffset(V.X, V.Y)
	local marco = P.Marco(padre, {
		Nombre = o.Nombre,
		Tamano = UDim2.fromOffset(V.Ancho, V.Alto),
		Posicion = posicion,
		Color = C.Blanco,
		Transparencia = 0,
		Recortar = true,
		Z = 20,
	})
	marco.Visible = false
	P.Esquinas(marco, Theme.Tamanos.RadioVentana)
	P.Degradado(marco, Theme.Degradados.Ventana, 35)
	P.Borde(marco, C.Acento, A.BordeSutil)

	-- Textura: rejilla muy tenue y unas pocas estrellas.
	local textura = P.Marco(marco, { Nombre = "Textura", Z = 1 })
	for i = 1, math.floor(V.Ancho / 24) do
		P.Marco(textura, {
			Tamano = UDim2.new(0, 1, 1, 0),
			Posicion = UDim2.fromOffset(i * 24, 0),
			Color = C.Acento,
			Transparencia = 0.982,
		})
	end
	for i = 1, math.floor(V.Alto / 24) do
		P.Marco(textura, {
			Tamano = UDim2.new(1, 0, 0, 1),
			Posicion = UDim2.fromOffset(0, i * 24),
			Color = C.Acento,
			Transparencia = 0.982,
		})
	end
	for _, punto in ESTRELLAS do
		P.Marco(textura, {
			Tamano = UDim2.fromOffset(1.5, 1.5),
			Posicion = UDim2.fromScale(punto[1], punto[2]),
			Color = C.Blanco,
			Transparencia = 0.7,
			Radio = UDim.new(1, 0),
		})
	end
	esquina(marco, 0, 0)
	esquina(marco, 1, 1)

	-- Barra de título.
	local barra = P.Marco(
		marco,
		{ Nombre = "BarraTitulo", Tamano = UDim2.new(1, 0, 0, V.Titulo), Color = C.Acento, Transparencia = 0, Z = 3 }
	)
	P.Esquinas(barra, Theme.Tamanos.RadioVentana) -- que no asome por las esquinas redondeadas de la ventana
	P.Degradado(barra, ColorSequence.new(C.Acento), 0, Theme.Degradados.TituloVentana)
	P.Marco(barra, {
		Nombre = "Linea",
		Tamano = UDim2.new(1, 0, 0, 1),
		Posicion = UDim2.fromScale(0, 1),
		Ancla = Vector2.new(0, 1),
		Color = C.Acento,
		Transparencia = A.BordeSutil,
		Z = 4,
	})
	local izquierda = P.Marco(barra, { Nombre = "Izquierda", Tamano = UDim2.new(1, -120, 1, 0), Z = 4 })
	P.Relleno(izquierda, 0, 0, 0, 14)
	P.Lista(izquierda, Enum.FillDirection.Horizontal, 8, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	IconBuilder.Icono(izquierda, o.Icono, { Tamano = 16, Color = o.ColorIcono or C.Acento, Z = 5, Orden = 1 })
	local titulo = P.Texto(izquierda, {
		Texto = o.Titulo,
		Tamano = Theme.Texto.Titulo,
		Fuente = Theme.Fuentes.Negrita,
		Espaciado = true,
		Z = 5,
		Orden = 2,
	})
	local subtitulo = P.Texto(izquierda, {
		Texto = o.Subtitulo or "",
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Espaciado = true,
		Z = 5,
		Orden = 3,
	})

	local derecha = P.Marco(barra, {
		Nombre = "Derecha",
		Tamano = UDim2.new(0, 110, 1, 0),
		Posicion = UDim2.new(1, -10, 0, 0),
		Ancla = Vector2.new(1, 0),
		Z = 4,
	})
	P.Lista(derecha, Enum.FillDirection.Horizontal, 8, Enum.HorizontalAlignment.Right, Enum.VerticalAlignment.Center)
	if o.Tecla then
		local tecla = P.Tecla(derecha, o.Tecla, { Z = 5 })
		tecla.LayoutOrder = 1
	end
	local cerrar = P.Crear("TextButton", {
		Name = "Cerrar",
		Text = "",
		AutoButtonColor = false,
		Size = UDim2.fromOffset(24, 24),
		BackgroundColor3 = C.Peligro,
		BackgroundTransparency = 0.86,
		LayoutOrder = 2,
		ZIndex = 5,
		Parent = derecha,
	}) :: TextButton
	P.Esquinas(cerrar, Theme.Tamanos.RadioBoton)
	P.Borde(cerrar, C.Peligro, 0.5)
	IconBuilder.Icono(cerrar, "ui_cerrar", {
		Tamano = 10,
		Color = C.PeligroClaro,
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 6,
	})
	UITweens.Hover(cerrar, 0.65)
	cerrar.Activated:Connect(o.AlCerrar)

	local cuerpo = P.Marco(
		marco,
		{ Nombre = "Cuerpo", Tamano = UDim2.new(1, 0, 1, -V.Titulo), Posicion = UDim2.fromOffset(0, V.Titulo), Z = 2 }
	)

	local abierta = false
	local ventana: Ventana = {
		Marco = marco,
		Cuerpo = cuerpo,
		Titulo = titulo,
		Subtitulo = subtitulo,
		PonerSubtitulo = function(texto: string)
			subtitulo.Text = P.Espaciar(texto)
		end,
		Abrir = function()
			if abierta then
				return
			end
			abierta = true
			UITweens.AbrirVentana(marco)
		end,
		Cerrar = function()
			if not abierta then
				return
			end
			abierta = false
			UITweens.CerrarVentana(marco)
		end,
		EstaAbierta = function(): boolean
			return abierta
		end,
	}
	return ventana
end

return Ventana
