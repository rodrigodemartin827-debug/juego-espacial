--!strict
--[[
	Constructor: pone una apariencia de Humano (Personaje/Apariencia) en un personaje R6.

	  · Quita lo que trae el avatar de Roblox (accesorios, ropa, camiseta, cara, colores del cuerpo): el juego usa sus
	    propias piezas.
	  · Pinta las seis partes del R6 (piel o color de la ropa, según la ropa elegida).
	  · Crea las piezas de la cara, el pelo, la ropa y el complemento dentro de la carpeta «Apariencia» del personaje,
	    soldadas a su parte (sin masa ni colisión: no cambian cómo se mueve ni cómo choca).

	Lo usa el servidor (el aspecto de verdad, que ven todos) y el cliente del editor (la vista previa, solo suya).
	Se puede llamar las veces que se quiera: cada vez rehace la carpeta.
]]

local Apariencia = require(script.Parent.Apariencia)
local Datos = require(script.Parent.DatosHumanos)

local Constructor = {}

Constructor.CARPETA = "Apariencia"

local PARTES_R6 = { "Head", "Torso", "Left Arm", "Right Arm", "Left Leg", "Right Leg" }
local QUITAR = { "Accessory", "Shirt", "Pants", "ShirtGraphic", "BodyColors", "CharacterMesh" }

local function colorDe(nombre: string, colores: { [string]: string }): Color3
	local hex = colores[nombre] or nombre
	local ok, color = pcall(Color3.fromHex, hex)
	return if ok then color else Color3.new(1, 0, 1)
end

local function crearPieza(base: BasePart, p: Datos.Pieza, colores: { [string]: string }, carpeta: Instance)
	local pieza = Instance.new("Part")
	pieza.Name = "Pieza"
	pieza.Anchored = false
	pieza.CanCollide = false
	pieza.CanTouch = false
	pieza.CanQuery = false
	pieza.Massless = true
	pieza.TopSurface = Enum.SurfaceType.Smooth
	pieza.BottomSurface = Enum.SurfaceType.Smooth
	pieza.Material = if p.Neon then Enum.Material.Neon else Enum.Material.SmoothPlastic
	pieza.Color = colorDe(p.Color, colores)
	local tam = Vector3.new(p.Tam[1], p.Tam[2], p.Tam[3])
	if p.Forma == "Bola" or p.Forma == "Cilindro" then
		-- Una SpecialMesh deja estirar la esfera o el cilindro a cualquier tamaño (una Part Ball es siempre redonda).
		pieza.Size = Vector3.new(1, 1, 1)
		local malla = Instance.new("SpecialMesh")
		malla.MeshType = if p.Forma == "Bola" then Enum.MeshType.Sphere else Enum.MeshType.Cylinder
		malla.Scale = tam
		malla.Parent = pieza
	else
		pieza.Size = tam
	end
	local giro = p.Giro or { 0, 0, 0 }
	pieza.CFrame = base.CFrame
		* CFrame.new(p.Pos[1], p.Pos[2], p.Pos[3])
		* CFrame.Angles(math.rad(giro[1]), math.rad(giro[2]), math.rad(giro[3]))
	local soldadura = Instance.new("WeldConstraint")
	soldadura.Part0 = base
	soldadura.Part1 = pieza
	soldadura.Parent = pieza
	pieza.Parent = carpeta
end

-- Pone la apariencia `tabla` (se valida: lo que falte va por defecto) en el personaje R6 `modelo`.
function Constructor.Aplicar(modelo: Model, tabla: any)
	local a = Apariencia.Validar(tabla)
	local colores = Apariencia.Colores(a)

	-- Fuera el avatar de Roblox.
	for _, d in modelo:GetChildren() do
		if table.find(QUITAR, d.ClassName) then
			d:Destroy()
		end
	end
	local cabeza = modelo:FindFirstChild("Head")
	if cabeza then
		for _, d in cabeza:GetChildren() do
			if d:IsA("Decal") then
				d:Destroy()
			end
		end
		-- La cabeza clásica de R6. PROBADO EN STUDIO: el avatar de Roblox trae su cabeza como malla de la propia Head
		-- (por ejemplo una tele con cara), que taparía la cara y el pelo propios.
		local malla = cabeza:FindFirstChildOfClass("SpecialMesh")
		if malla == nil then
			malla = Instance.new("SpecialMesh")
			malla.Parent = cabeza
		end
		local m = malla :: SpecialMesh
		m.MeshType = Enum.MeshType.Head
		m.MeshId = ""
		m.TextureId = ""
		m.Offset = Vector3.zero
		m.Scale = Vector3.new(1.25, 1.25, 1.25)
	end
	local vieja = modelo:FindFirstChild(Constructor.CARPETA)
	if vieja then
		vieja:Destroy()
	end

	-- Colores del cuerpo.
	local ropa = Apariencia.Buscar("Ropa", a.Ropa)
	local colorParte = {
		Head = "Piel",
		Torso = ropa.Torso,
		["Left Arm"] = ropa.Brazos,
		["Right Arm"] = ropa.Brazos,
		["Left Leg"] = ropa.Piernas,
		["Right Leg"] = ropa.Piernas,
	}
	for _, nombre in PARTES_R6 do
		local parte = modelo:FindFirstChild(nombre)
		if parte and parte:IsA("BasePart") then
			parte.Color = colorDe(colorParte[nombre], colores)
			parte.Material = Enum.Material.SmoothPlastic
		end
	end

	-- Piezas.
	local carpeta = Instance.new("Folder")
	carpeta.Name = Constructor.CARPETA
	local function poner(piezas: { Datos.Pieza }, parteDefecto: string)
		for _, p in piezas do
			local base = modelo:FindFirstChild(p.Parte or parteDefecto)
			if base and base:IsA("BasePart") then
				crearPieza(base, p, colores, carpeta)
			end
		end
	end
	poner(Apariencia.Buscar("Cara", a.Cara).Piezas, "Head")
	poner(Apariencia.Buscar("Pelo", a.Pelo).Piezas, "Head")
	poner(ropa.Piezas, "Torso")
	poner(Apariencia.Buscar("Complemento", a.Complemento).Piezas, "Head")
	carpeta.Parent = modelo
end

return Constructor
