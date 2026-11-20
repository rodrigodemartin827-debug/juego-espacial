--!strict
--[[
	EntradaIndice: una entrada del códex (86×104).

	  - Descubierta: imagen real, nombre debajo, borde cian y un check verde.
	  - No descubierta: fondo muy oscuro, un "?" grande, nombre "????" en gris y borde gris.
	  - Seleccionada: borde cian más grueso y halo.
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores

local EntradaIndice = {}

export type EntradaIndice = {
	Boton: TextButton,
	Seleccionar: (seleccionada: boolean) -> (),
}

export type Opciones = {
	Nombre: string?, -- nil = no descubierta
	Arte: string?,
	Rareza: string?,
	Orden: number,
	AlPulsar: (() -> ())?,
}

function EntradaIndice.Crear(padre: Instance, o: Opciones): EntradaIndice
	local oculta = o.Nombre == nil
	local boton = P.Crear("TextButton", {
		Name = o.Nombre or "Oculta",
		Text = "",
		AutoButtonColor = false,
		BackgroundColor3 = if oculta then C.FondoProfundo else C.Fondo1,
		BackgroundTransparency = if oculta then 0.15 else Theme.Alpha.Celda,
		LayoutOrder = o.Orden,
		ZIndex = 4,
		Active = not oculta,
		Parent = padre,
	}) :: TextButton
	P.Esquinas(boton, UDim.new(0, 7))
	local borde = P.Borde(
		boton,
		if oculta then C.Blanco else C.Acento,
		if oculta then 0.92 else 0.55,
		if oculta then 1 else Theme.Tamanos.TrazoActivo
	)

	if oculta then
		P.Texto(boton, {
			Texto = "?",
			Tamano = 26,
			Fuente = Theme.Fuentes.Negrita,
			Transparencia = 0.7,
			Posicion = UDim2.new(0.5, 0, 0, 38),
			Ancla = Vector2.new(0.5, 0.5),
			Z = 5,
		})
		P.Texto(boton, {
			Texto = "????",
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Negrita,
			Transparencia = 0.75,
			Espaciado = true,
			Posicion = UDim2.new(0.5, 0, 1, -18),
			Ancla = Vector2.new(0.5, 0),
			Z = 5,
		})
		return { Boton = boton, Seleccionar = function(_: boolean) end }
	end

	IconBuilder.Arte(boton, o.Arte or "item_cristal", {
		Tamano = 66,
		Posicion = UDim2.new(0.5, 0, 0, 6),
		Ancla = Vector2.new(0.5, 0),
		Z = 5,
		ColorRespaldo = Theme.ColorRareza(o.Rareza),
	})
	P.Texto(boton, {
		Texto = o.Nombre or "",
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Titulo,
		AlineacionX = Enum.TextXAlignment.Center,
		AlineacionY = Enum.TextYAlignment.Top,
		Caja = UDim2.new(1, -8, 0, 22),
		Posicion = UDim2.new(0.5, 0, 0, 75),
		Ancla = Vector2.new(0.5, 0),
		Envolver = true,
		Z = 5,
	})
	local ok = P.Marco(boton, {
		Nombre = "Descubierta",
		Tamano = UDim2.fromOffset(12, 12),
		Posicion = UDim2.new(1, -4, 0, 4),
		Ancla = Vector2.new(1, 0),
		Color = C.Exito,
		Radio = UDim.new(1, 0),
		Z = 6,
	})
	IconBuilder.Icono(ok, "ui_check", {
		Tamano = 7,
		Color = C.TextoSobreExito,
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 7,
	})

	UITweens.Hover(boton)
	if o.AlPulsar then
		boton.Activated:Connect(o.AlPulsar)
	end

	return {
		Boton = boton,
		Seleccionar = function(seleccionada: boolean)
			borde.Transparency = if seleccionada then 0 else 0.55
			borde.Thickness = if seleccionada then Theme.Tamanos.TrazoGrueso else Theme.Tamanos.TrazoActivo
		end,
	}
end

return EntradaIndice
