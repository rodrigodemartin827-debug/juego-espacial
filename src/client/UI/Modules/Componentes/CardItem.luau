--!strict
--[[
	CardItem: casilla de un objeto en la rejilla del inventario (65×65 la pone el UIGridLayout).

	  - Fondo rgba(10,20,45,.6) y borde del color de la rareza; los míticos además laten en rojo.
	  - Imagen REAL del objeto (arte de herramientas/iconos_ui/arte.mjs), no un cuadrado de color.
	  - Cantidad abajo a la derecha ("x12") y un check verde arriba a la izquierda si está equipado.
	  - Objeto no descubierto: fondo más oscuro, sin rareza y un "?" grande.
	  - Clic = seleccionar (tooltip con acciones), doble clic = equipar.
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores
local A = Theme.Alpha

local CardItem = {}

export type CardItem = {
	Boton: TextButton,
	Seleccionar: (seleccionada: boolean) -> (),
	Id: string?,
}

export type Opciones = {
	Id: string?, -- nil = casilla de objeto no descubierto
	Arte: string?,
	Rareza: string?,
	Cantidad: number?,
	Equipado: boolean?,
	Orden: number?,
	AlPulsar: ((id: string, boton: GuiObject) -> ())?,
	AlDobleClic: ((id: string) -> ())?,
	AlEntrar: ((id: string, boton: GuiObject) -> ())?,
	AlSalir: ((id: string) -> ())?,
}

function CardItem.Crear(padre: Instance, o: Opciones): CardItem
	local oculta = o.Id == nil
	local colorRareza = Theme.ColorRareza(o.Rareza)
	local boton = P.Crear("TextButton", {
		Name = o.Id or "Oculta",
		Text = if oculta then "?" else "",
		TextSize = 20,
		FontFace = Theme.Fuentes.Negrita,
		TextColor3 = C.Blanco,
		TextTransparency = 0.7,
		AutoButtonColor = false,
		BackgroundColor3 = if oculta then C.FondoProfundo else C.Fondo1,
		BackgroundTransparency = if oculta then A.CeldaOculta else A.Celda,
		LayoutOrder = o.Orden or 0,
		ZIndex = 4,
		Active = not oculta,
		Parent = padre,
	}) :: TextButton
	P.Esquinas(boton, UDim.new(0, 6))
	local borde = P.Borde(
		boton,
		if oculta then C.Blanco else colorRareza,
		if oculta then 0.95 else 0,
		if oculta then 1 else Theme.Tamanos.TrazoActivo
	)

	if oculta then
		return { Boton = boton, Seleccionar = function(_: boolean) end, Id = nil }
	end
	local id = o.Id :: string

	IconBuilder.Arte(boton, o.Arte or "item_cristal", {
		Tamano = UDim2.new(1, -14, 1, -14),
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 5,
		ColorRespaldo = colorRareza,
	})

	if o.Cantidad then
		local cantidad = P.Texto(boton, {
			Nombre = "Cantidad",
			Texto = `x{o.Cantidad}`,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Negrita,
			Posicion = UDim2.new(1, -3, 1, -3),
			Ancla = Vector2.new(1, 1),
			Z = 7,
		})
		cantidad.BackgroundColor3 = C.Negro
		cantidad.BackgroundTransparency = 0.4
		P.Esquinas(cantidad, UDim.new(0, 3))
		P.Relleno(cantidad, 1, 3)
	end

	if o.Equipado then
		local check = P.Marco(boton, {
			Nombre = "Equipado",
			Tamano = UDim2.fromOffset(13, 13),
			Posicion = UDim2.fromOffset(3, 3),
			Color = C.Exito,
			Radio = UDim.new(1, 0),
			Z = 7,
		})
		IconBuilder.Icono(check, "ui_check", {
			Tamano = 8,
			Color = C.TextoSobreExito,
			Posicion = UDim2.fromScale(0.5, 0.5),
			Ancla = Vector2.new(0.5, 0.5),
			Z = 8,
		})
	end

	-- Los míticos laten en rojo (un único tween infinito por casilla mítica).
	if o.Rareza == "Mitico" then
		local halo = P.Borde(boton, C.Mitico, 0.4, 3)
		UITweens.Pulso(halo, "Transparency", 0.9, 0.35, Theme.Tweens.Pulso)
	end

	UITweens.Hover(boton)

	local ultimoClic = 0
	boton.Activated:Connect(function()
		local ahora = os.clock()
		if ahora - ultimoClic <= Theme.Tiempos.DobleClic and o.AlDobleClic then
			ultimoClic = 0
			o.AlDobleClic(id)
			return
		end
		ultimoClic = ahora
		if o.AlPulsar then
			o.AlPulsar(id, boton)
		end
	end)
	if o.AlEntrar then
		local alEntrar = o.AlEntrar
		boton.MouseEnter:Connect(function()
			alEntrar(id, boton)
		end)
	end
	if o.AlSalir then
		local alSalir = o.AlSalir
		boton.MouseLeave:Connect(function()
			alSalir(id)
		end)
	end

	return {
		Boton = boton,
		Id = id,
		Seleccionar = function(seleccionada: boolean)
			borde.Color = if seleccionada then C.Acento else colorRareza
			borde.Thickness = if seleccionada then Theme.Tamanos.TrazoGrueso else Theme.Tamanos.TrazoActivo
		end,
	}
end

return CardItem
