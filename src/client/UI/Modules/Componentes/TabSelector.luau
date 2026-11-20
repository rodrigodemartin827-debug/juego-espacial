--!strict
--[[
	TabSelector: fila de pestañas reutilizable (Atributos / Inventario / Builds, filtros del inventario, categorías...).

	  - Activa: fondo cian al 15 %, borde cian y texto cian (o del color propio de la pestaña).
	  - Inactiva: fondo casi transparente y texto gris.
	  - El cambio se anima (0,15 s). El contenido de cada pestaña lo cambia quien la usa, normalmente con
	    UITweens.FundidoCruzado.

	Estilo "Pildora": la variante redondeada de los filtros del inventario.
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores
local A = Theme.Alpha

local TabSelector = {}

export type Opcion = { Id: string, Texto: string, Extra: string?, Color: Color3? }

export type Opciones = {
	Opciones: { Opcion },
	Inicial: string?,
	AlCambiar: (id: string) -> (),
	Estilo: ("Tab" | "Pildora")?,
	Alto: number?,
	Separacion: number?,
	Posicion: UDim2?,
	Ancla: Vector2?,
	Z: number?,
}

export type TabSelector = {
	Marco: Frame,
	Seleccionar: (id: string, silencioso: boolean?) -> (),
	Actual: () -> string,
}

function TabSelector.Crear(padre: Instance, o: Opciones): TabSelector
	local pildora = o.Estilo == "Pildora"
	local alto = o.Alto or (if pildora then 20 else 24)
	local z = o.Z or 3
	local marco = P.Marco(padre, {
		Nombre = "Pestanas",
		Tamano = UDim2.fromOffset(0, alto),
		Posicion = o.Posicion,
		Ancla = o.Ancla,
		Z = z,
	})
	marco.AutomaticSize = Enum.AutomaticSize.X
	P.Lista(
		marco,
		Enum.FillDirection.Horizontal,
		o.Separacion or 4,
		Enum.HorizontalAlignment.Left,
		Enum.VerticalAlignment.Center
	)

	type Pestana = { Boton: TextButton, Borde: UIStroke, Color: Color3 }
	local pestanas: { [string]: Pestana } = {}
	local actual = o.Inicial or o.Opciones[1].Id

	local function pintar(id: string, animar: boolean)
		for idPestana, p in pestanas do
			local activa = idPestana == id
			local objetivo = {
				BackgroundColor3 = if activa then p.Color elseif pildora then C.FondoProfundo else C.Blanco,
				BackgroundTransparency = if activa then A.Tab elseif pildora then 0.25 else A.TabInactiva,
				TextColor3 = if activa then p.Color else C.TextoPrincipal,
				TextTransparency = if activa then 0 else (if pildora then 0.5 else A.TextoSecundario),
			}
			local borde = { Color = p.Color, Transparency = if activa then 0 else 1 }
			if animar then
				UITweens.Tween(p.Boton, Theme.Tweens.Rapido, objetivo)
				UITweens.Tween(p.Borde, Theme.Tweens.Rapido, borde)
			else
				for k, v in objetivo do
					(p.Boton :: any)[k] = v
				end
				p.Borde.Color = borde.Color
				p.Borde.Transparency = borde.Transparency
			end
		end
	end

	for i, opcion in o.Opciones do
		local boton = P.Crear("TextButton", {
			Name = opcion.Id,
			Text = if opcion.Extra
				then `{opcion.Texto}  <font transparency="0.35" size="{Theme.Texto.Mini}">{opcion.Extra}</font>`
				else opcion.Texto,
			RichText = opcion.Extra ~= nil,
			TextSize = if pildora then Theme.Texto.Pequeno else Theme.Texto.Cuerpo,
			FontFace = Theme.Fuentes.Titulo,
			AutoButtonColor = false,
			Size = UDim2.fromOffset(0, alto),
			AutomaticSize = Enum.AutomaticSize.X,
			BorderSizePixel = 0,
			LayoutOrder = i,
			ZIndex = z + 1,
			Parent = marco,
		}) :: TextButton
		P.Esquinas(boton, if pildora then UDim.new(1, 0) else Theme.Tamanos.RadioBoton)
		P.Relleno(boton, 0, if pildora then 10 else 14)
		local borde = P.Borde(boton, opcion.Color or C.Acento, 1, Theme.Tamanos.Trazo)
		pestanas[opcion.Id] = { Boton = boton, Borde = borde, Color = opcion.Color or C.Acento }
		boton.Activated:Connect(function()
			if actual ~= opcion.Id then
				actual = opcion.Id
				pintar(actual, true)
				o.AlCambiar(actual)
			end
		end)
	end
	pintar(actual, false)

	return {
		Marco = marco,
		Seleccionar = function(id: string, silencioso: boolean?)
			if pestanas[id] == nil then
				return
			end
			local cambia = actual ~= id
			actual = id
			pintar(id, true)
			if cambia and not silencioso then
				o.AlCambiar(id)
			end
		end,
		Actual = function(): string
			return actual
		end,
	}
end

return TabSelector
