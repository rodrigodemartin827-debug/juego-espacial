--!strict
--[[
	Sidebar: barra lateral izquierda, siempre visible (también en partida, más translúcida): es la forma de abrir los
	menús en móvil y la navegación entre pantallas con un menú abierto.

	  [Personaje] [Inventario] [Poderes] [Clan] [Ranked] [Índice] [Mapa] [Ajustes]  ─  [TIENDA dorada]

	52 unidades de ancho; arranca en y = 58 para no tapar los botones de Roblox de arriba a la izquierda.
]]

local Theme = require(script.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Animaciones.UITweens)
local P = require(script.Parent.Componentes.Primitivas)
local BotonSidebar = require(script.Parent.Componentes.BotonSidebar)
local ConfigUI = require(script.Parent.Datos.ConfigUI)

local C = Theme.Colores
local T = Theme.Tamanos

local Sidebar = {}

local marco: Frame? = nil
local botones: { [string]: BotonSidebar.BotonSidebar } = {}

-- Crea la barra dentro de `raiz`. `alPulsar(id)` se llama al pulsar un botón ("personaje", "tienda"...).
function Sidebar.Iniciar(raiz: Frame, alPulsar: (id: string) -> ())
	local barra = P.Marco(raiz, {
		Nombre = "BarraLateral",
		Tamano = UDim2.fromOffset(T.SidebarAncho, 0),
		Posicion = UDim2.fromOffset(T.SidebarX, T.SidebarY),
		Color = C.Fondo1,
		Transparencia = Theme.Alpha.SidebarJuego,
		Radio = UDim.new(0, 12),
		Z = 30,
	})
	barra.AutomaticSize = Enum.AutomaticSize.Y
	P.Degradado(barra, ColorSequence.new(C.Fondo1, C.Fondo3), 90)
	P.Borde(barra, C.Acento, Theme.Alpha.BordeSutil)
	P.Relleno(barra, 6)
	P.Lista(barra, Enum.FillDirection.Vertical, 4, Enum.HorizontalAlignment.Center)

	for i, b in ConfigUI.Sidebar do
		botones[b.Id] = BotonSidebar.Crear(barra, {
			Id = b.Id,
			Icono = b.Icono,
			Nombre = b.Nombre,
			Tecla = b.Tecla,
			Orden = i,
			AlPulsar = alPulsar,
		})
	end
	-- Separador y TIENDA (dorada, siempre destacada).
	P.Marco(barra, {
		Nombre = "Separador",
		Tamano = UDim2.new(1, -4, 0, 1),
		Color = C.Acento,
		Transparencia = Theme.Alpha.BordeActivo,
		Orden = 100,
		Z = 31,
	})
	local tienda = ConfigUI.BotonTienda
	botones[tienda.Id] = BotonSidebar.Crear(barra, {
		Id = tienda.Id,
		Icono = tienda.Icono,
		Nombre = tienda.Nombre,
		EsTienda = true,
		Orden = 101,
		AlPulsar = alPulsar,
	})
	marco = barra
end

-- Marca el botón de la pantalla abierta (nil = ninguno).
function Sidebar.MarcarActivo(id: string?)
	for idBoton, boton in botones do
		boton.MarcarActivo(idBoton == id)
	end
end

-- Más opaca con un menú abierto, más translúcida en partida.
function Sidebar.ModoMenu(menu: boolean)
	local barra = marco
	if barra then
		UITweens.Tween(
			barra,
			Theme.Tweens.Normal,
			{ BackgroundTransparency = if menu then Theme.Alpha.SidebarMenu else Theme.Alpha.SidebarJuego }
		)
	end
end

return Sidebar
