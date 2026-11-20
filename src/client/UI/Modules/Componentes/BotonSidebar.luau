--!strict
--[[
	BotonSidebar: un botón de la barra lateral (40×40).

	  - Inactivo: fondo cian al 8 %, icono cian al 50 %.
	  - Hover: fondo al 15 % y escala 1,05 (0,15 s); aparece a la derecha una etiqueta con el nombre y la tecla.
	  - Activo: degradado cian, icono oscuro y un halo.
	  - Tienda: siempre degradado dorado #FFB800 → #FF8800 con "TIENDA" debajo del icono.
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores
local A = Theme.Alpha
local T = Theme.Tamanos

local BotonSidebar = {}

export type BotonSidebar = {
	Boton: TextButton,
	MarcarActivo: (activo: boolean) -> (),
}

export type Opciones = {
	Id: string,
	Icono: string,
	Nombre: string,
	Tecla: string?,
	EsTienda: boolean?,
	Orden: number,
	AlPulsar: (id: string) -> (),
}

-- Etiqueta flotante a la derecha del botón ("PERSONAJE [P]").
local function crearPista(boton: GuiButton, nombre: string, tecla: string?): CanvasGroup
	local pista = P.Grupo(boton, {
		Nombre = "Pista",
		Tamano = UDim2.fromOffset(0, 20),
		Posicion = UDim2.new(1, 8, 0.5, 0),
		Ancla = Vector2.new(0, 0.5),
		Color = C.FondoProfundo,
		Transparencia = 0.05,
		Z = 40,
	})
	pista.AutomaticSize = Enum.AutomaticSize.X
	pista.GroupTransparency = 1
	pista.Visible = false
	P.Esquinas(pista, Theme.Tamanos.BorderRadiusSmall)
	P.Borde(pista, C.Acento, A.BordeActivo)
	P.Relleno(pista, 0, 8)
	P.Lista(pista, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	P.Texto(pista, {
		Texto = nombre,
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Negrita,
		Espaciado = true,
		Z = 41,
		Orden = 1,
	})
	if tecla then
		local t = P.Tecla(pista, tecla, { Z = 41 })
		t.LayoutOrder = 2
	end
	return pista
end

function BotonSidebar.Crear(padre: Instance, o: Opciones): BotonSidebar
	local tienda = o.EsTienda == true
	local boton = P.Crear("TextButton", {
		Name = o.Id,
		Text = "",
		AutoButtonColor = false,
		Size = UDim2.fromOffset(T.IconoSidebar, if tienda then T.BotonTiendaAlto else T.IconoSidebar),
		BackgroundColor3 = if tienda then C.Blanco else C.Acento,
		BackgroundTransparency = if tienda then 0 else A.BotonInactivo,
		LayoutOrder = o.Orden,
		ZIndex = 31,
		Parent = padre,
	}) :: TextButton
	P.Esquinas(boton, T.BorderRadius)

	-- Degradado del estado activo (cian) o de la tienda (dorado).
	local degradado =
		P.Degradado(boton, if tienda then Theme.Degradados.Dorado else Theme.Degradados.Cian, if tienda then 90 else 45)
	degradado.Enabled = tienda
	local halo =
		P.Borde(boton, if tienda then C.Dorado else C.Acento, if tienda then 0.55 else 1, Theme.Tamanos.TrazoGrueso)

	local icono = IconBuilder.Icono(boton, o.Icono, {
		Tamano = if tienda then 20 else T.IconoSidebarDibujo,
		Color = if tienda then C.TextoSobreDorado else C.Acento,
		Transparencia = if tienda then 0 else A.IconoDimmed,
		Posicion = UDim2.new(0.5, 0, if tienda then 0.42 else 0.5, 0),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 32,
	})
	if tienda then
		P.Texto(boton, {
			Texto = "TIENDA",
			Tamano = Theme.Texto.Micro,
			Fuente = Theme.Fuentes.Negrita,
			Color = C.TextoSobreDorado,
			Posicion = UDim2.new(0.5, 0, 1, -5),
			Ancla = Vector2.new(0.5, 1),
			Z = 32,
		})
	end

	local pista = crearPista(boton, o.Nombre, o.Tecla)
	local activo = false

	-- Hover: escala 1,05 y fondo al 15 % (solo si no está activo); la etiqueta aparece con un fundido.
	local escala = UITweens.EscalaDe(boton)
	boton.MouseEnter:Connect(function()
		UITweens.Tween(escala, Theme.Tweens.Rapido, { Scale = Theme.Tiempos.EscalaHover })
		if not activo and not tienda then
			UITweens.Tween(boton, Theme.Tweens.Rapido, { BackgroundTransparency = A.HoverFondo })
			UITweens.Tween(icono, Theme.Tweens.Rapido, { ImageTransparency = 0.15 })
		end
		UITweens.Fundir(pista, true, Theme.Tweens.Rapido)
	end)
	boton.MouseLeave:Connect(function()
		UITweens.Tween(escala, Theme.Tweens.Rapido, { Scale = 1 })
		if not activo and not tienda then
			UITweens.Tween(boton, Theme.Tweens.Rapido, { BackgroundTransparency = A.BotonInactivo })
			UITweens.Tween(icono, Theme.Tweens.Rapido, { ImageTransparency = A.IconoDimmed })
		end
		UITweens.Fundir(pista, false, Theme.Tweens.Rapido)
	end)
	boton.Activated:Connect(function()
		o.AlPulsar(o.Id)
	end)

	local function marcarActivo(valor: boolean)
		activo = valor
		if tienda then
			UITweens.Tween(
				halo,
				Theme.Tweens.Rapido,
				{ Color = if valor then C.Blanco else C.Dorado, Transparency = if valor then 0 else 0.55 }
			)
			return
		end
		degradado.Enabled = valor
		UITweens.Tween(boton, Theme.Tweens.Rapido, { BackgroundTransparency = if valor then 0 else A.BotonInactivo })
		UITweens.Tween(halo, Theme.Tweens.Rapido, { Transparency = if valor then 0.55 else 1 })
		IconBuilder.Tenir(icono, if valor then C.Fondo1 else C.Acento)
		UITweens.Tween(icono, Theme.Tweens.Rapido, { ImageTransparency = if valor then 0 else A.IconoDimmed })
	end

	return { Boton = boton, MarcarActivo = marcarActivo }
end

return BotonSidebar
