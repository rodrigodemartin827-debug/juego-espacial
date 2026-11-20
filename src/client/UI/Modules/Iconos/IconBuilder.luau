--!strict
--[[
	IconBuilder: crea los iconos de la interfaz (opción A: imágenes PNG subidas a Roblox).

	Los iconos se dibujan como SVG en herramientas/iconos_ui/iconos.mjs (siluetas custom, ninguna librería ni emoji),
	se exportan a PNG blancos de 128×128 (src/client/UI/Assets/IconPNGs) y se tiñen aquí con ImageColor3. El arte a
	color (objetos, criaturas, planetas, tienda) va aparte, en ArtePNGs, y no se tiñe.

	Los ID de Roblox están en IdsIconos.luau. Mientras un ID esté vacío, en su lugar se dibuja un marcador discreto
	(un rombo del color del icono o una esfera del color del objeto) y se avisa UNA vez por la consola de lo que falta,
	así la interfaz nunca enseña un hueco vacío ni revienta.

	Uso:
		local icono = IconBuilder.Icono(padre, "sidebar_personaje", { Tamano = 22, Color = Theme.Colores.Acento })
		IconBuilder.Tenir(icono, Theme.Colores.Fondo1)
		local imagen = IconBuilder.Arte(padre, "item_espada_plasma", { Tamano = 50 })
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local IdsIconos = require(script.Parent.IdsIconos)

local C = Theme.Colores

local IconBuilder = {}

local faltan: { [string]: boolean } = {}
local avisoProgramado = false

-- Anota un nombre sin ID y programa un único aviso agrupado.
local function anotarFalta(nombre: string)
	if faltan[nombre] then
		return
	end
	faltan[nombre] = true
	if not avisoProgramado then
		avisoProgramado = true
		task.delay(3, function()
			local lista = {}
			for n in faltan do
				table.insert(lista, n)
			end
			table.sort(lista)
			warn(
				`[UI] {#lista} iconos sin ID de Roblox (se ve un marcador en su lugar). Súbelos y pega los ID en`
					.. ` UI/Modules/Iconos/IdsIconos.luau: {table.concat(lista, ", ")}`
			)
		end)
	end
end

export type Opciones = {
	Tamano: (number | UDim2)?, -- lado en unidades de diseño, o un UDim2
	Color: Color3?, -- tinte (solo iconos de una tinta)
	Transparencia: number?,
	Posicion: UDim2?,
	Ancla: Vector2?,
	Z: number?,
	Orden: number?,
	Nombre: string?,
	ColorRespaldo: Color3?, -- color del marcador si el arte no tiene ID todavía
	Rotacion: number?,
}

local function tamanoDe(o: Opciones): UDim2
	local t = o.Tamano
	if typeof(t) == "UDim2" then
		return t
	elseif type(t) == "number" then
		return UDim2.fromOffset(t, t)
	end
	return UDim2.fromScale(1, 1)
end

local function imagenBase(padre: Instance?, nombre: string, o: Opciones): ImageLabel
	local imagen = Instance.new("ImageLabel")
	imagen.Name = o.Nombre or nombre
	imagen.BackgroundTransparency = 1
	imagen.BorderSizePixel = 0
	imagen.Size = tamanoDe(o)
	imagen.Position = o.Posicion or UDim2.new()
	imagen.AnchorPoint = o.Ancla or Vector2.zero
	imagen.ZIndex = o.Z or 1
	imagen.LayoutOrder = o.Orden or 0
	imagen.Rotation = o.Rotacion or 0
	imagen.ScaleType = Enum.ScaleType.Fit
	imagen.ImageTransparency = o.Transparencia or 0
	imagen:SetAttribute("Icono", nombre)
	return imagen
end

-- Marcador de un icono sin ID: un rombo con borde del color del icono.
local function marcadorIcono(imagen: ImageLabel)
	local rombo = Instance.new("Frame")
	rombo.Name = "Marcador"
	rombo.AnchorPoint = Vector2.new(0.5, 0.5)
	rombo.Position = UDim2.fromScale(0.5, 0.5)
	rombo.Size = UDim2.fromScale(0.42, 0.42)
	rombo.Rotation = 45
	rombo.BackgroundColor3 = imagen.ImageColor3
	rombo.BackgroundTransparency = 0.75
	rombo.BorderSizePixel = 0
	rombo.ZIndex = imagen.ZIndex
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0.15, 0)
	esquina.Parent = rombo
	local borde = Instance.new("UIStroke")
	borde.Color = imagen.ImageColor3
	borde.Thickness = 1.5
	borde.Transparency = imagen.ImageTransparency
	borde.Parent = rombo
	rombo.Parent = imagen
end

-- Marcador de un arte sin ID: una esfera con degradado del color del objeto.
local function marcadorArte(imagen: ImageLabel, color: Color3)
	local esfera = Instance.new("Frame")
	esfera.Name = "Marcador"
	esfera.AnchorPoint = Vector2.new(0.5, 0.5)
	esfera.Position = UDim2.fromScale(0.5, 0.5)
	esfera.Size = UDim2.fromScale(0.62, 0.62)
	esfera.BackgroundColor3 = C.Blanco
	esfera.BorderSizePixel = 0
	esfera.ZIndex = imagen.ZIndex
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0.5, 0)
	esquina.Parent = esfera
	local degradado = Instance.new("UIGradient")
	degradado.Color = ColorSequence.new(color:Lerp(C.Blanco, 0.35), color:Lerp(C.Negro, 0.55))
	degradado.Rotation = 45
	degradado.Parent = esfera
	local borde = Instance.new("UIStroke")
	borde.Color = color
	borde.Thickness = 1.5
	borde.Transparency = 0.3
	borde.Parent = esfera
	esfera.Parent = imagen
end

-- ¿Hay un ID para este icono o arte?
function IconBuilder.TieneId(nombre: string): boolean
	local id = IdsIconos.Iconos[nombre] or IdsIconos.Arte[nombre]
	return id ~= nil and id ~= ""
end

-- ¿Existe el nombre en la lista (aunque aún no tenga ID)?
function IconBuilder.Existe(nombre: string): boolean
	return IdsIconos.Iconos[nombre] ~= nil or IdsIconos.Arte[nombre] ~= nil
end

-- Icono de una tinta (blanco en el PNG), teñido con `Color`.
function IconBuilder.Icono(padre: Instance?, nombre: string, o: Opciones?): ImageLabel
	local op: Opciones = o or {}
	local imagen = imagenBase(padre, nombre, op)
	imagen.ImageColor3 = op.Color or C.Acento
	local id = IdsIconos.Iconos[nombre]
	if id == nil then
		warn(
			`[UI] El icono "{nombre}" no existe en IdsIconos (¿falta dibujarlo en herramientas/iconos_ui/iconos.mjs?)`
		)
		marcadorIcono(imagen)
	elseif id == "" then
		anotarFalta(nombre)
		marcadorIcono(imagen)
	else
		imagen.Image = id
	end
	imagen.Parent = padre
	return imagen
end

-- Arte a color (no se tiñe). `ColorRespaldo` es el color del marcador mientras no haya ID.
function IconBuilder.Arte(padre: Instance?, nombre: string, o: Opciones?): ImageLabel
	local op: Opciones = o or {}
	local imagen = imagenBase(padre, nombre, op)
	local id = IdsIconos.Arte[nombre]
	if id == nil or id == "" then
		if id == nil then
			warn(
				`[UI] El arte "{nombre}" no existe en IdsIconos (¿falta dibujarlo en herramientas/iconos_ui/arte.mjs?)`
			)
		else
			anotarFalta(nombre)
		end
		marcadorArte(imagen, op.ColorRespaldo or C.Acento)
	else
		imagen.Image = id
	end
	imagen.Parent = padre
	return imagen
end

-- Cambia el tinte (y la transparencia) de un icono, también el de su marcador si no tiene ID.
function IconBuilder.Tenir(imagen: ImageLabel, color: Color3, transparencia: number?)
	imagen.ImageColor3 = color
	if transparencia then
		imagen.ImageTransparency = transparencia
	end
	local marcador = imagen:FindFirstChild("Marcador")
	if
		marcador
		and marcador:IsA("Frame")
		and imagen:GetAttribute("Icono") ~= nil
		and IdsIconos.Iconos[imagen:GetAttribute("Icono") :: string]
	then
		marcador.BackgroundColor3 = color
		local borde = marcador:FindFirstChildOfClass("UIStroke")
		if borde then
			borde.Color = color
			borde.Transparency = imagen.ImageTransparency
		end
	end
end

-- Cambia la imagen de un icono ya creado (otro nombre, mismo tamaño y tinte).
function IconBuilder.Cambiar(imagen: ImageLabel, nombre: string)
	local marcador = imagen:FindFirstChild("Marcador")
	if marcador then
		marcador:Destroy()
	end
	imagen:SetAttribute("Icono", nombre)
	local id = IdsIconos.Iconos[nombre] or IdsIconos.Arte[nombre]
	if id and id ~= "" then
		imagen.Image = id
	else
		imagen.Image = ""
		anotarFalta(nombre)
		if IdsIconos.Iconos[nombre] ~= nil then
			marcadorIcono(imagen)
		else
			marcadorArte(imagen, C.Acento)
		end
	end
end

-- Nombres que se han pedido y no tienen ID (para depurar).
function IconBuilder.Faltan(): { string }
	local lista = {}
	for n in faltan do
		table.insert(lista, n)
	end
	table.sort(lista)
	return lista
end

return IconBuilder
