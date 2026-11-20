--!strict
--[[
	CardModo: tarjeta de un modo de ranked (1v1, 2v2, 3v3, 4v4).

	  ┌────────┐
	  │  2v2   │   nombre grande
	  │ ▮▮ VS ▮▮│  figuritas: tu equipo (cian) contra el rival (rojo)
	  │ESPERA ~1:10│
	  └────────┘
	Seleccionada: borde cian brillante, halo y fondo con un degradado cian.
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores

local CardModo = {}

export type CardModo = {
	Boton: TextButton,
	Seleccionar: (seleccionada: boolean) -> (),
}

export type Opciones = {
	Modo: string,
	Jugadores: number,
	Espera: string,
	Orden: number,
	AlPulsar: (modo: string, jugadores: number) -> (),
}

function CardModo.Crear(padre: Instance, o: Opciones): CardModo
	local boton = P.Crear("TextButton", {
		Name = o.Modo,
		Text = "",
		AutoButtonColor = false,
		Size = UDim2.fromOffset(95, 74),
		BackgroundColor3 = C.FondoProfundo,
		BackgroundTransparency = 0.45,
		LayoutOrder = o.Orden,
		ZIndex = 4,
		Parent = padre,
	}) :: TextButton
	P.Esquinas(boton, Theme.Tamanos.BorderRadius)
	local borde = P.Borde(boton, C.Acento, Theme.Alpha.BordeSutil, Theme.Tamanos.Trazo)
	local brillo = P.Degradado(boton, ColorSequence.new(C.Acento), 90, NumberSequence.new(0.86, 0.97))
	brillo.Enabled = false
	UITweens.Hover(boton)

	local titulo = P.Texto(boton, {
		Texto = o.Modo,
		Tamano = Theme.Texto.Enorme,
		Fuente = Theme.Fuentes.Negrita,
		Posicion = UDim2.new(0.5, 0, 0, 12),
		Ancla = Vector2.new(0.5, 0),
		Z = 5,
	})

	-- Figuritas: n cian, "VS", n rojas.
	local figuras = P.Marco(boton, {
		Nombre = "Figuras",
		Tamano = UDim2.fromOffset(0, 8),
		Posicion = UDim2.new(0.5, 0, 0, 40),
		Ancla = Vector2.new(0.5, 0),
		Z = 5,
	})
	figuras.AutomaticSize = Enum.AutomaticSize.X
	P.Lista(figuras, Enum.FillDirection.Horizontal, 2, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)
	for i = 1, o.Jugadores do
		P.Marco(figuras, {
			Tamano = UDim2.fromOffset(4, 7),
			Color = C.Acento,
			Transparencia = 0.3,
			Radio = UDim.new(0, 2),
			Orden = i,
			Z = 6,
		})
	end
	P.Texto(figuras, {
		Texto = " VS ",
		Tamano = Theme.Texto.Micro,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.TextoSecundario,
		Transparencia = Theme.Alpha.TextoSecundario,
		Orden = 10,
		Z = 6,
	})
	for i = 1, o.Jugadores do
		P.Marco(figuras, {
			Tamano = UDim2.fromOffset(4, 7),
			Color = C.Arma,
			Transparencia = 0.3,
			Radio = UDim.new(0, 2),
			Orden = 10 + i,
			Z = 6,
		})
	end

	P.Texto(boton, {
		Texto = `ESPERA {o.Espera}`,
		Tamano = Theme.Texto.Micro + 0.5,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoSecundario,
		Transparencia = Theme.Alpha.TextoSecundario,
		Posicion = UDim2.new(0.5, 0, 0, 54),
		Ancla = Vector2.new(0.5, 0),
		Z = 5,
	})

	boton.Activated:Connect(function()
		o.AlPulsar(o.Modo, o.Jugadores)
	end)

	return {
		Boton = boton,
		Seleccionar = function(seleccionada: boolean)
			brillo.Enabled = seleccionada
			UITweens.Tween(borde, Theme.Tweens.Rapido, {
				Transparency = if seleccionada then 0 else Theme.Alpha.BordeSutil,
				Thickness = if seleccionada then Theme.Tamanos.TrazoGrueso else Theme.Tamanos.Trazo,
			})
			titulo.TextColor3 = if seleccionada then C.Acento else C.TextoPrincipal
		end,
	}
end

return CardModo
