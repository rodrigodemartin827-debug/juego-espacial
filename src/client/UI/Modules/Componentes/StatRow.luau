--!strict
--[[
	StatRow: fila de una estadística del personaje.

	  [icono 18] FUERZA ................ 45 (+12)
	  ▔▔▔▔▔▔▔▔ barrita del color del stat

	  - Icono custom del stat, nombre en gris medio, valor en el color del stat y el bonus del equipo más pequeño y apagado.
	  - En modo edición aparecen los botones − y + a los lados del valor y, si se han añadido puntos, un "+N" verde.
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local IconBuilder = require(script.Parent.Parent.Iconos.IconBuilder)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores

local StatRow = {}

export type StatRow = {
	Marco: Frame,
	Poner: (base: number, bonus: number, extra: number, maximo: number) -> (),
	Editar: (editando: boolean, puedeSumar: boolean) -> (),
}

export type Opciones = {
	Stat: string, -- clave de Theme.Stats
	Orden: number?,
	AlMas: () -> (),
	AlMenos: () -> (),
}

local function botoncito(padre: Instance, texto: string, color: Color3, orden: number, alPulsar: () -> ()): TextButton
	local boton = P.Crear("TextButton", {
		Name = if texto == "+" then "Mas" else "Menos",
		Text = texto,
		TextSize = Theme.Texto.Grande,
		FontFace = Theme.Fuentes.Negrita,
		TextColor3 = C.TextoPrincipal,
		AutoButtonColor = false,
		BackgroundColor3 = C.Blanco,
		BackgroundTransparency = 0.93,
		Size = UDim2.fromOffset(16, 16),
		LayoutOrder = orden,
		ZIndex = 6,
		Visible = false,
		Parent = padre,
	}) :: TextButton
	P.Esquinas(boton, UDim.new(0, 4))
	P.Borde(boton, C.Blanco, 0.85)
	UITweens.Hover(boton)
	boton.MouseEnter:Connect(function()
		if boton.Active then
			boton.BackgroundColor3 = color
			boton.BackgroundTransparency = 0
			boton.TextColor3 = C.TextoSobreAcento
		end
	end)
	boton.MouseLeave:Connect(function()
		boton.BackgroundColor3 = C.Blanco
		boton.BackgroundTransparency = 0.93
		boton.TextColor3 = C.TextoPrincipal
	end)
	boton.Activated:Connect(function()
		if boton.Active then
			alPulsar()
		end
	end)
	return boton
end

function StatRow.Crear(padre: Instance, o: Opciones): StatRow
	local info = Theme.Stats[o.Stat]
	local marco = P.Marco(padre, {
		Nombre = o.Stat,
		Tamano = UDim2.new(1, 0, 0, 34),
		Color = C.FondoProfundo,
		Transparencia = 0.55,
		Radio = UDim.new(0, 6),
		Orden = o.Orden,
		Z = 4,
	})
	IconBuilder.Icono(marco, info.Icono, {
		Tamano = Theme.Tamanos.IconoStat,
		Color = info.Color,
		Posicion = UDim2.new(0, 8, 0.5, 0),
		Ancla = Vector2.new(0, 0.5),
		Z = 5,
	})
	P.Texto(marco, {
		Texto = info.Nombre,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoPrincipal,
		Transparencia = Theme.Alpha.TextoMedio,
		Espaciado = true,
		Posicion = UDim2.new(0, 34, 0.5, 0),
		Ancla = Vector2.new(0, 0.5),
		Z = 5,
	})

	-- Valor (y botones − / + en modo edición), alineado a la derecha.
	local derecha = P.Marco(marco, {
		Nombre = "Valor",
		Tamano = UDim2.new(0, 140, 1, 0),
		Posicion = UDim2.new(1, -8, 0, 0),
		Ancla = Vector2.new(1, 0),
		Z = 5,
	})
	P.Lista(derecha, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Right, Enum.VerticalAlignment.Center)
	local menos = botoncito(derecha, "−", info.Color, 1, o.AlMenos)
	local valor = P.Texto(derecha, {
		Texto = "",
		Rico = true,
		Tamano = Theme.Texto.Grande,
		Fuente = Theme.Fuentes.Negrita,
		Color = info.Color,
		Orden = 2,
		Z = 6,
	})
	local mas = botoncito(derecha, "+", info.Color, 3, o.AlMas)

	-- Barrita del valor respecto al máximo.
	local pista = P.Marco(marco, {
		Nombre = "Pista",
		Tamano = UDim2.new(1, -42, 0, 2),
		Posicion = UDim2.new(0, 34, 1, -5),
		Color = C.Blanco,
		Transparencia = 0.95,
		Z = 5,
	})
	local barrita = P.Marco(
		pista,
		{ Nombre = "Relleno", Tamano = UDim2.fromScale(0, 1), Color = info.Color, Transparencia = 0.45, Z = 6 }
	)

	return {
		Marco = marco,
		Poner = function(base: number, bonus: number, extra: number, maximo: number)
			local hex = info.Color:ToHex()
			local texto =
				`{P.Numero(base + extra)}<font size="{Theme.Texto.Pequeno}" transparency="0.45" color="#{hex}">(+{P.Decimal(
					bonus
				)})</font>`
			if extra > 0 then
				texto ..= ` <font size="{Theme.Texto.Pequeno}" color="#{C.Exito:ToHex()}">+{extra}</font>`
			end
			valor.Text = texto
			UITweens.Barra(barrita, (base + extra + bonus) / math.max(maximo, 1))
			P.Habilitar(menos, extra > 0)
		end,
		Editar = function(editando: boolean, puedeSumar: boolean)
			menos.Visible = editando
			mas.Visible = editando
			P.Habilitar(mas, puedeSumar)
		end,
	}
end

return StatRow
