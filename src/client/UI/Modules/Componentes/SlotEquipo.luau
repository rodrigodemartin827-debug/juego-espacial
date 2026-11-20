--!strict
--[[
	SlotEquipo: una casilla de equipo del muñeco (46×46, esquinas de 6).

	  - Vacía: fondo y borde con el tinte del color asociado al tipo y el icono del tipo apagado.
	  - Con objeto: la imagen del objeto, borde del color de su rareza y un iconito del tipo en la esquina.
	  - Objetivo: cuando hay un objeto seleccionado que va en esta casilla, borde cian que late (clic = equipar aquí).
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Parent.Iconos.IconBuilder)
local DatosDemo = require(script.Parent.Parent.Datos.DatosDemo)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores
local A = Theme.Alpha

local SlotEquipo = {}

export type SlotEquipo = {
	Boton: TextButton,
	PonerObjeto: (arte: string?, rareza: string?) -> (),
	MarcarObjetivo: (objetivo: boolean) -> (),
}

export type Opciones = {
	Slot: DatosDemo.Slot,
	Orden: number?,
	AlPulsar: (id: string) -> (),
	AlEntrar: ((id: string, boton: GuiObject) -> ())?,
	AlSalir: ((id: string) -> ())?,
}

function SlotEquipo.Crear(padre: Instance, o: Opciones): SlotEquipo
	local color = (Theme.Colores :: any)[o.Slot.Color] or C.Acento
	local lado = Theme.Tamanos.SlotEquipo
	local boton = P.Crear("TextButton", {
		Name = o.Slot.Id,
		Text = "",
		AutoButtonColor = false,
		Size = UDim2.fromOffset(lado, lado),
		BackgroundColor3 = color,
		BackgroundTransparency = A.SlotVacio,
		LayoutOrder = o.Orden or 0,
		ZIndex = 4,
		Parent = padre,
	}) :: TextButton
	boton:SetAttribute("SlotId", o.Slot.Id) -- lo usa el arrastrar y soltar del inventario
	P.Esquinas(boton, UDim.new(0, 6))
	local borde = P.Borde(boton, color, A.BordeSlotVacio, Theme.Tamanos.Trazo)
	UITweens.Hover(boton)

	-- Icono del tipo (vacía) y arte del objeto (llena).
	local icono = IconBuilder.Icono(boton, o.Slot.Icono, {
		Tamano = 24,
		Color = color,
		Transparencia = A.IconoSlotVacio,
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 5,
	})
	local arte: ImageLabel? = nil

	-- Iconito del tipo en la esquina (solo con objeto).
	local tipo = P.Marco(boton, {
		Nombre = "Tipo",
		Tamano = UDim2.fromOffset(13, 13),
		Posicion = UDim2.new(1, 3, 1, 3),
		Ancla = Vector2.new(1, 1),
		Color = C.FondoProfundo,
		Transparencia = 0.05,
		Radio = UDim.new(0, 4),
		Z = 7,
	})
	P.Borde(tipo, C.Blanco, 0.88)
	IconBuilder.Icono(
		tipo,
		o.Slot.Icono,
		{ Tamano = 8, Color = color, Posicion = UDim2.fromScale(0.5, 0.5), Ancla = Vector2.new(0.5, 0.5), Z = 8 }
	)
	tipo.Visible = false

	local objetivoActivo = false
	local rarezaActual: string? = nil

	local function pintarBorde()
		if objetivoActivo then
			UITweens.Parar(borde)
			borde.Color = C.Acento
			borde.Thickness = Theme.Tamanos.TrazoGrueso
			UITweens.Pulso(borde, "Transparency", 0, 0.5, Theme.Tweens.Pulso)
		else
			UITweens.Parar(borde)
			borde.Thickness = if rarezaActual then Theme.Tamanos.TrazoActivo else Theme.Tamanos.Trazo
			borde.Color = if rarezaActual then Theme.ColorRareza(rarezaActual) else color
			borde.Transparency = if rarezaActual then 0 else A.BordeSlotVacio
		end
	end

	local function ponerObjeto(nombreArte: string?, rareza: string?)
		if arte then
			arte:Destroy()
			arte = nil
		end
		rarezaActual = if nombreArte then rareza or "Comun" else nil
		if nombreArte then
			arte = IconBuilder.Arte(boton, nombreArte, {
				Tamano = UDim2.new(1, -8, 1, -8),
				Posicion = UDim2.fromScale(0.5, 0.5),
				Ancla = Vector2.new(0.5, 0.5),
				Z = 6,
				ColorRespaldo = Theme.ColorRareza(rareza),
			})
		end
		icono.Visible = nombreArte == nil
		tipo.Visible = nombreArte ~= nil
		boton.BackgroundColor3 = if nombreArte then C.Fondo1 else color
		boton.BackgroundTransparency = if nombreArte then A.Celda else A.SlotVacio
		pintarBorde()
	end

	boton.Activated:Connect(function()
		o.AlPulsar(o.Slot.Id)
	end)
	if o.AlEntrar then
		local alEntrar = o.AlEntrar
		boton.MouseEnter:Connect(function()
			alEntrar(o.Slot.Id, boton)
		end)
	end
	if o.AlSalir then
		local alSalir = o.AlSalir
		boton.MouseLeave:Connect(function()
			alSalir(o.Slot.Id)
		end)
	end

	return {
		Boton = boton,
		PonerObjeto = ponerObjeto,
		MarcarObjetivo = function(valor: boolean)
			if valor ~= objetivoActivo then
				objetivoActivo = valor
				pintarBorde()
			end
		end,
	}
end

return SlotEquipo
