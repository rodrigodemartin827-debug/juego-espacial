--!strict
--[[
	ConstructorMonstruo: pone una apariencia de Monstruo (Personaje/AparienciaMonstruo) en un personaje R6. Lo usan el
	servidor (el aspecto de verdad) y el cliente del editor (la vista previa en una copia local). Misma forma que
	Personaje/Constructor (Aplicar, Colorear, Limpiar) para que el editor use uno u otro según el bando.

	  · Quita lo que trae el avatar de Roblox (accesorios, ropa, colores del cuerpo, cara, malla de la cabeza).
	  · Silueta: estira torso, brazos y piernas (Constructor.Complexion): la forma del cuerpo.
	  · Piel: las seis partes del R6 del color de piel elegido.
	  · Cara: ojos (textura blanca teñida con el color de ojos) y boca.
	  · Marcas: líneas luminosas en el pecho y la espalda, teñidas con el color de detalles.
	  · Cuernos: un Accessory en la cabeza. Deformación: piezas 3D en el cuerpo (soldadas a cada parte, sin masa ni
	    colisión), que se estiran con su parte.
	Las piezas 3D se clonan de ReplicatedStorage.PlantillasHumanas (las crea ServicioApariencia al arrancar; ahí están
	también las del humano). Si alguna plantilla aún no llegó, Aplicar devuelve cuántas piezas faltaron.
]]

local Apariencia = require(script.Parent.AparienciaMonstruo)
local Constructor = require(script.Parent.Constructor)
local Datos = require(script.Parent.DatosMonstruo)
local Recursos = require(script.Parent.RecursosMonstruo)

local ConstructorMonstruo = {}

local PARTES_R6 = { "Head", "Torso", "Left Arm", "Right Arm", "Left Leg", "Right Leg" }
local QUITAR = { "Accessory", "Shirt", "Pants", "ShirtGraphic", "BodyColors", "CharacterMesh" }
local ACCESORIO_CUERNOS = "Cuernos"

local function color(hex: string): Color3
	local ok, c = pcall(Color3.fromHex, hex)
	return if ok then c else Color3.new(1, 0, 1)
end

-- Quita lo que puso Aplicar (cuernos, deformaciones y decals).
function ConstructorMonstruo.Limpiar(modelo: Model)
	for _, d in modelo:GetChildren() do
		if d:IsA("Accessory") or d.Name == Constructor.CARPETA then
			d:Destroy()
		end
	end
	for _, nombre in PARTES_R6 do
		local parte = modelo:FindFirstChild(nombre)
		if parte then
			for _, d in parte:GetChildren() do
				if d:IsA("Decal") and (string.sub(d.Name, 1, 6) == "Rasgo_" or d.Name == "Marca") then
					d:Destroy()
				end
			end
		end
	end
end

local function pintarCuerpo(modelo: Model, colores: { [string]: string })
	for _, nombre in PARTES_R6 do
		local parte = modelo:FindFirstChild(nombre)
		if parte and parte:IsA("BasePart") then
			parte.Color = color(colores.Piel)
			parte.Material = Enum.Material.SmoothPlastic
		end
	end
end

local function decal(
	padre: BasePart,
	nombre: string,
	cara: Enum.NormalId,
	imagen: string,
	orden: number,
	tinte: Color3?
)
	local d = Instance.new("Decal")
	d.Name = nombre
	d.Face = cara
	d.Texture = imagen
	d.ZIndex = orden
	if tinte then
		d.Color3 = tinte
	end
	d.Parent = padre
end

function ConstructorMonstruo.Aplicar(modelo: Model, tabla: any, plantillas: Instance?): number
	local a = Apariencia.Validar(tabla)
	local colores = Apariencia.Colores(a)
	local fuente = plantillas or Constructor.Plantillas()

	-- Fuera el avatar de Roblox y lo que pusiera una llamada anterior.
	for _, d in modelo:GetChildren() do
		if table.find(QUITAR, d.ClassName) or d.Name == Constructor.CARPETA then
			d:Destroy()
		end
	end
	ConstructorMonstruo.Limpiar(modelo)
	local cabeza = modelo:FindFirstChild("Head")
	if cabeza and cabeza:IsA("BasePart") then
		for _, d in cabeza:GetChildren() do
			if d:IsA("Decal") then
				d:Destroy()
			end
		end
		-- Cabeza clásica de R6 (el orden importa: ver Constructor.Aplicar).
		local existente = cabeza:FindFirstChildOfClass("SpecialMesh")
		local m: SpecialMesh = if existente then existente else Instance.new("SpecialMesh")
		m.Parent = cabeza
		m.MeshId = ""
		m.TextureId = ""
		m.MeshType = Enum.MeshType.Head
		m.Offset = Vector3.zero
		m.Scale = Vector3.new(1.25, 1.25, 1.25)
	end

	Constructor.QuitarTatuajes(modelo)
	pintarCuerpo(modelo, colores)
	Constructor.Complexion(modelo, Apariencia.Buscar("Silueta", a.Silueta))

	-- Cara y marcas.
	if cabeza and cabeza:IsA("BasePart") then
		local boca = Recursos.Imagenes["Boca_" .. a.Boca]
		if boca then
			decal(cabeza, "Rasgo_Boca", Enum.NormalId.Front, boca, 2)
		end
		local ojos = Recursos.Imagenes["Ojos_" .. a.Ojos]
		if ojos then
			decal(cabeza, "Rasgo_Ojos", Enum.NormalId.Front, ojos, 3, color(colores.Ojos))
		end
	end
	local marcas = Recursos.Imagenes["Marcas_" .. a.Marcas]
	local torso = modelo:FindFirstChild("Torso")
	if marcas and torso and torso:IsA("BasePart") then
		decal(torso, "Marca", Enum.NormalId.Front, marcas, 1, color(colores.Hueso))
		decal(torso, "Marca", Enum.NormalId.Back, marcas, 1, color(colores.Hueso))
	end

	local faltan = 0

	-- Cuernos.
	local cuernos = Apariencia.Buscar("Cuernos", a.Cuernos)
	if cabeza and cabeza:IsA("BasePart") and cuernos and cuernos.Anclaje then
		faltan += Constructor.PonerAccesorio(
			modelo,
			cabeza,
			ACCESORIO_CUERNOS,
			"Cuerno_" .. a.Cuernos,
			cuernos.Anclaje,
			colores,
			fuente,
			Recursos,
			Datos.Roles
		)
	end

	-- Deformaciones: piezas 3D en el cuerpo.
	local carpeta = Instance.new("Folder")
	carpeta.Name = Constructor.CARPETA
	local lista: { any } = Recursos.Piezas["Deformacion_" .. a.Deformacion] or {}
	for _, pieza in lista do
		local base = modelo:FindFirstChild(pieza.Parte)
		if base == nil or not base:IsA("BasePart") then
			continue
		end
		local p = Constructor.CrearPieza(pieza, colores, fuente, Datos.Roles)
		if p == nil then
			faltan += 1
			continue
		end
		p.Name = pieza.Nombre
		local f = Constructor.Estiramiento(base)
		p.Size = Vector3.new(p.Size.X * f.X, p.Size.Y * f.Y, p.Size.Z * f.Z)
		local pos = Constructor.Centro(pieza).Position
		p.CFrame = base.CFrame * CFrame.new(pos.X * f.X, pos.Y * f.Y, pos.Z * f.Z)
		Constructor.Soldar(base, p)
		p.Parent = carpeta
	end
	carpeta.Parent = modelo
	return faltan
end

-- Solo cambia los colores (piel, ojos, cuernos y detalles) de un monstruo al que ya se le hizo Aplicar con las mismas
-- piezas. Mucho más barato: lo usa el editor mientras se arrastra por la rueda.
function ConstructorMonstruo.Colorear(modelo: Model, tabla: any)
	local a = Apariencia.Validar(tabla)
	local colores = Apariencia.Colores(a)
	pintarCuerpo(modelo, colores)
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") then
			local rol = d:GetAttribute("Rol")
			if type(rol) == "string" and colores[rol] then
				d.Color = color(colores[rol])
			end
		elseif d:IsA("Decal") then
			if d.Name == "Rasgo_Ojos" then
				d.Color3 = color(colores.Ojos)
			elseif d.Name == "Marca" then
				d.Color3 = color(colores.Hueso)
			end
		end
	end
end

return ConstructorMonstruo
