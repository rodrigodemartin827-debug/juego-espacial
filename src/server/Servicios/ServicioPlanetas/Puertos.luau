--!strict
--[[
	Puertos (ServicioPlanetas): lo que se construye en la superficie de cada planeta de bando.

	  - El PUERTO: varias plataformas de despegue (cada una es un Hangar, con su consola "Despegar"), un anillo
	    luminoso en el suelo que marca la ZONA SEGURA (sin PvP, ver Planetas/Espacio y Combate/Reglas) y carteles.
	  - Los MUROS invisibles del borde del mapa (las montañas del borde ya lo cierran; esto es por si acaso).

	Las medidas y los colores salen de Planetas/Datos.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Datos = require(ReplicatedStorage.Shared.Planetas.Datos)
local Espacio = require(ReplicatedStorage.Shared.Planetas.Espacio)
local Hangar = require(script.Parent.Parent.Hangar)

local Puertos = {}

local SEGMENTOS_ANILLO = 40 -- piezas del anillo de la zona segura
local ALTO_MUROS = 1600

local function color(hex: string): Color3
	return Color3.fromHex(hex)
end

local function parte(padre: Instance, nombre: string, tamano: Vector3, marco: CFrame): Part
	local p = Instance.new("Part")
	p.Name = nombre
	p.Size = tamano
	p.CFrame = marco
	p.Anchored = true
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = padre
	return p
end

local function cartel(padre: Instance, texto: string, posicion: Vector3, ancho: number, alto: number, distancia: number)
	local ancla = parte(padre, "Cartel", Vector3.one, CFrame.new(posicion))
	ancla.Transparency = 1
	ancla.CanCollide = false
	ancla.CanQuery = false
	ancla.CanTouch = false
	local gui = Instance.new("BillboardGui")
	gui.Size = UDim2.fromOffset(ancho, alto)
	gui.MaxDistance = distancia
	gui.Parent = ancla
	local etiqueta = Instance.new("TextLabel")
	etiqueta.Size = UDim2.fromScale(1, 1)
	etiqueta.BackgroundColor3 = Color3.fromRGB(12, 14, 26)
	etiqueta.BackgroundTransparency = 0.25
	etiqueta.TextColor3 = Color3.fromRGB(235, 240, 255)
	etiqueta.TextScaled = true
	etiqueta.Font = Enum.Font.GothamMedium
	etiqueta.Text = texto
	etiqueta.Parent = gui
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, 8)
	esquina.Parent = etiqueta
end

-- Anillo de piezas de neón en el suelo que marca el borde de la zona segura.
local function anilloZonaSegura(padre: Instance, centro: Vector3, radio: number, neon: Color3)
	local carpeta = Instance.new("Folder")
	carpeta.Name = "BordeZonaSegura"
	carpeta.Parent = padre
	local largo = 2 * math.pi * radio / SEGMENTOS_ANILLO * 0.62 -- con huecos entre piezas: se lee como "borde"
	for i = 1, SEGMENTOS_ANILLO do
		local angulo = (i / SEGMENTOS_ANILLO) * math.pi * 2
		local posicion = centro + Vector3.new(math.cos(angulo) * radio, 0.15, math.sin(angulo) * radio)
		local pieza = parte(
			carpeta,
			"Segmento",
			Vector3.new(largo, 0.3, 1.6),
			CFrame.lookAt(posicion, centro) * CFrame.Angles(0, math.pi / 2, 0)
		)
		pieza.Material = Enum.Material.Neon
		pieza.Color = neon
		pieza.Transparency = 0.2
		pieza.CanCollide = false
		pieza.CanQuery = false
		pieza.CanTouch = false
		pieza.CastShadow = false
	end
end

-- Muros invisibles en los cuatro lados de la superficie (cada lado en piezas de 2048 como mucho).
local function muros(padre: Instance, id: string)
	local superficie = Datos.Planetas[id].Superficie
	local c = superficie.Centro
	local centro = Vector3.new(c.X, c.Y, c.Z)
	local mitad = superficie.Tamano / 2
	local carpeta = Instance.new("Folder")
	carpeta.Name = "MurosDelBorde"
	carpeta.Parent = padre
	local tramos = math.ceil(superficie.Tamano / 2048)
	local largo = superficie.Tamano / tramos
	for _, lado in { { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } } do
		for t = 0, tramos - 1 do
			local a = -mitad + (t + 0.5) * largo
			local posicion = if lado[1] ~= 0
				then centro + Vector3.new(lado[1] * mitad, ALTO_MUROS / 2 - 100, a)
				else centro + Vector3.new(a, ALTO_MUROS / 2 - 100, lado[2] * mitad)
			local tamano = if lado[1] ~= 0 then Vector3.new(8, ALTO_MUROS, largo) else Vector3.new(largo, ALTO_MUROS, 8)
			local muro = parte(carpeta, "Muro", tamano, CFrame.new(posicion))
			muro.Transparency = 1
			muro.CanQuery = false
			muro.CastShadow = false
		end
	end
end

--[[
	Construye el puerto y los muros del planeta `id` en `padre`. Devuelve las plataformas de despegue
	(para ServicioNaves.Despegar).
]]
function Puertos.Crear(padre: Instance, id: string): { any }
	local planeta = Datos.Planetas[id]
	local puerto = planeta.Puerto
	local p = Espacio.PosicionPuerto(id)
	local centro = Vector3.new(p.X, p.Y, p.Z)
	local neon = color(puerto.ColorNeon)

	local carpeta = Instance.new("Folder")
	carpeta.Name = `Puerto_{id}`
	carpeta.Parent = padre

	local plataformas = {}
	for i = 1, puerto.Plataformas do
		local desplazamiento = (i - (puerto.Plataformas + 1) / 2) * puerto.Separacion
		table.insert(plataformas, Hangar.Crear(carpeta, centro + Vector3.new(desplazamiento, 0, 0)))
	end

	anilloZonaSegura(carpeta, centro, puerto.RadioZonaSegura, neon)
	cartel(
		carpeta,
		`PUERTO DE {string.upper(planeta.Nombre)} · ZONA SEGURA (sin PvP)`,
		centro + Vector3.new(0, 34, -40),
		520,
		46,
		400
	)
	cartel(
		carpeta,
		"Despega desde un hangar · sube por encima de las nubes para volver al espacio",
		centro + Vector3.new(0, 27, -40),
		560,
		34,
		200
	)

	muros(padre, id)
	return plataformas
end

return Puertos
