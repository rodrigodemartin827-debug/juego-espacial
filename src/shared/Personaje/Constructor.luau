--!strict
--[[
	Constructor: pone una apariencia de Humano (Personaje/Apariencia) en un personaje R6.

	  · Quita lo que trae el avatar de Roblox (accesorios, ropa, camiseta, cara, colores del cuerpo y la malla de la
	    cabeza): el juego usa sus propias piezas.
	  · Pinta las seis partes del R6: cabeza de piel, torso y brazos de la chaqueta (o brazos de piel si la chaqueta es
	    de manga corta) y piernas del pantalón.
	  · Cara: cuatro Decals en la cara de la cabeza (ojos, cejas, nariz y boca). Las cejas se tiñen del color del pelo.
	  · Cabello y accesorio: un Accessory cada uno, con las piezas 3D de Blender, sujeto al Attachment de la cabeza
	    que diga su opción (HairAttachment, HatAttachment o FaceFrontAttachment).
	  · Chaqueta y pantalón: sus detalles 3D (cuello, bolsillos, botas...) soldados a cada parte, en la carpeta
	    «Apariencia» del personaje. Sin masa ni colisión: no cambian cómo se mueve ni cómo choca.

	Las piezas 3D se clonan de una carpeta de plantillas (MeshParts con el nombre de cada pieza), porque una
	MeshPart con malla subida solo se puede crear con AssetService:CreateMeshPartAsync, que es lento: el servidor
	las crea una vez al arrancar en ReplicatedStorage.PlantillasHumanas (ServicioApariencia) y de ahí las toman él
	y la vista previa del editor. Si una plantilla aún no ha llegado, esa pieza se salta y Aplicar devuelve cuántas
	faltaron (para volver a llamarlo cuando lleguen).

	Lo usa el servidor (el aspecto de verdad, que ven todos) y el cliente del editor (la vista previa, en una copia
	local del personaje). Se puede llamar las veces que se quiera: cada vez rehace todo.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Apariencia = require(script.Parent.Apariencia)
local Datos = require(script.Parent.DatosHumanos)
local Recursos = require(script.Parent.RecursosHumanos)

local Constructor = {}

Constructor.CARPETA = "Apariencia"
Constructor.CARPETA_PLANTILLAS = "PlantillasHumanas"
Constructor.ACCESORIO_CABELLO = "Cabello"
Constructor.ACCESORIO_COMPLEMENTO = "Accesorio"

local PARTES_R6 = { "Head", "Torso", "Left Arm", "Right Arm", "Left Leg", "Right Leg" }
local QUITAR = { "Accessory", "Shirt", "Pants", "ShirtGraphic", "BodyColors", "CharacterMesh" }

-- Rasgos de la cara: campo y orden de dibujo (los de arriba tapan a los de abajo).
local RASGOS = {
	{ Campo = "Nariz", Orden = 1 },
	{ Campo = "Boca", Orden = 2 },
	{ Campo = "Ojos", Orden = 3 },
	{ Campo = "Cejas", Orden = 4 },
}

-- Dónde están los Attachment de la cabeza de un R6 estándar (por si el personaje no los trae).
local ANCLAJES_CABEZA: { [string]: { number } } = {
	HairAttachment = { 0, 0.6, 0 },
	HatAttachment = { 0, 0.6, 0 },
	FaceFrontAttachment = { 0, 0, -0.6 },
}

local function color(hex: string): Color3
	local ok, c = pcall(Color3.fromHex, hex)
	return if ok then c else Color3.new(1, 0, 1)
end

local function material(nombre: string): Enum.Material
	local ok, m = pcall(function()
		return (Enum.Material :: any)[nombre]
	end)
	return if ok and m then m else Enum.Material.SmoothPlastic
end

-- La carpeta de plantillas (la del servidor en ReplicatedStorage si no se da otra).
function Constructor.Plantillas(): Instance?
	return ReplicatedStorage:FindFirstChild(Constructor.CARPETA_PLANTILLAS)
end

-- Clona la plantilla de la pieza y la deja lista (color, material, sin física). nil si la plantilla no está.
local function crearPieza(pieza: Recursos.Pieza, colores: { [string]: string }, plantillas: Instance?): MeshPart?
	local plantilla = plantillas and plantillas:FindFirstChild(pieza.Nombre)
	if plantilla == nil or not plantilla:IsA("MeshPart") then
		return nil
	end
	local p = plantilla:Clone()
	p.Size = Vector3.new(pieza.Tamano[1], pieza.Tamano[2], pieza.Tamano[3])
	local rol = Datos.Roles[pieza.Rol] or Datos.Roles.Detalle
	p.Color = color(colores[pieza.Rol] or "#FF00FF")
	p.Material = material(rol.Material)
	p.Transparency = rol.Transparencia or 0
	p.Anchored = false
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = false
	p.Massless = true
	p:SetAttribute("Rol", pieza.Rol)
	return p
end

local function centro(pieza: Recursos.Pieza): CFrame
	return CFrame.new(pieza.Centro[1], pieza.Centro[2], pieza.Centro[3])
end

local function soldar(a: BasePart, b: BasePart)
	local w = Instance.new("WeldConstraint")
	w.Part0 = a
	w.Part1 = b
	w.Parent = b
end

-- Accessory con las piezas de `clave` sujeto al Attachment `anclaje` de la cabeza. Devuelve cuántas piezas faltaron.
local function ponerAccesorio(
	modelo: Model,
	cabeza: BasePart,
	nombre: string,
	clave: string,
	anclaje: string,
	colores: { [string]: string },
	plantillas: Instance?
): number
	local piezas = Recursos.Piezas[clave]
	if piezas == nil then
		return 0
	end
	local accesorio = Instance.new("Accessory")
	accesorio.Name = nombre
	local faltan = 0
	local asa: BasePart? = nil
	for _, pieza in piezas do
		local p = crearPieza(pieza, colores, plantillas)
		if p == nil then
			faltan += 1
			continue
		end
		p.CFrame = cabeza.CFrame * centro(pieza)
		if asa == nil then
			-- La primera pieza es el asa (Handle) del Accessory: lleva el Attachment y la soldadura a la cabeza.
			p.Name = "Handle"
			local attCabeza = cabeza:FindFirstChild(anclaje)
			local cfCabeza = if attCabeza and attCabeza:IsA("Attachment")
				then attCabeza.CFrame
				else CFrame.new(table.unpack(ANCLAJES_CABEZA[anclaje] or { 0, 0, 0 }))
			local att = Instance.new("Attachment")
			att.Name = anclaje
			att.CFrame = centro(pieza):Inverse() * cfCabeza
			att.Parent = p
			local weld = Instance.new("Weld")
			weld.Name = "AccessoryWeld"
			weld.Part0 = p
			weld.Part1 = cabeza
			weld.C0 = att.CFrame
			weld.C1 = cfCabeza
			weld.Parent = p
			p.Parent = accesorio
			asa = p
		else
			p.Name = pieza.Rol
			soldar(asa :: BasePart, p)
			p.Parent = asa
		end
	end
	if asa == nil then
		accesorio:Destroy()
	else
		accesorio.Parent = modelo
	end
	return faltan
end

-- Colores de las seis partes del R6.
local function pintarCuerpo(modelo: Model, a: Apariencia.Apariencia, colores: { [string]: string })
	local chaqueta = Apariencia.Buscar("Chaqueta", a.Chaqueta)
	local rolBrazos = chaqueta.Brazos or "Chaqueta"
	local rolParte = {
		Head = "Piel",
		Torso = "Chaqueta",
		["Left Arm"] = rolBrazos,
		["Right Arm"] = rolBrazos,
		["Left Leg"] = "Pantalon",
		["Right Leg"] = "Pantalon",
	}
	for _, nombre in PARTES_R6 do
		local parte = modelo:FindFirstChild(nombre)
		if parte and parte:IsA("BasePart") then
			local rol = rolParte[nombre]
			parte.Color = color(colores[rol])
			parte.Material = if rol == "Piel" then Enum.Material.SmoothPlastic else Enum.Material.Fabric
		end
	end
end

--[[
	Solo cambia los colores (piel, pelo, chaqueta, pantalón y detalles) de un personaje al que ya se le hizo Aplicar
	con las mismas piezas. Es mucho más barato que Aplicar: lo usa el editor mientras se arrastra por la rueda.
]]
function Constructor.Colorear(modelo: Model, tabla: any)
	local a = Apariencia.Validar(tabla)
	local colores = Apariencia.Colores(a)
	pintarCuerpo(modelo, a, colores)
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") then
			local rol = d:GetAttribute("Rol")
			if type(rol) == "string" and colores[rol] then
				d.Color = color(colores[rol])
			end
		elseif d:IsA("Decal") and d.Name == "Rasgo_Cejas" then
			d.Color3 = color(colores.Pelo)
		end
	end
end

--[[
	Pone la apariencia `tabla` (se valida: lo que falte va por defecto) en el personaje R6 `modelo`. `plantillas`:
	la carpeta de donde clonar las piezas 3D (por defecto la de ReplicatedStorage). Devuelve cuántas piezas 3D no se
	pudieron poner porque su plantilla aún no estaba.
]]
function Constructor.Aplicar(modelo: Model, tabla: any, plantillas: Instance?): number
	local a = Apariencia.Validar(tabla)
	local colores = Apariencia.Colores(a)
	local fuente = plantillas or Constructor.Plantillas()

	-- Fuera el avatar de Roblox y lo que pusiera una llamada anterior.
	for _, d in modelo:GetChildren() do
		if table.find(QUITAR, d.ClassName) or d.Name == Constructor.CARPETA then
			d:Destroy()
		end
	end
	local cabeza = modelo:FindFirstChild("Head")
	if cabeza and cabeza:IsA("BasePart") then
		for _, d in cabeza:GetChildren() do
			if d:IsA("Decal") then
				d:Destroy()
			end
		end
		-- La cabeza clásica de R6. PROBADO EN STUDIO: el avatar de Roblox trae su cabeza como malla de la propia Head
		-- (por ejemplo una tele con cara), que taparía la cara y el pelo propios.
		local existente = cabeza:FindFirstChildOfClass("SpecialMesh")
		local m: SpecialMesh = if existente then existente else Instance.new("SpecialMesh")
		m.Parent = cabeza
		m.MeshType = Enum.MeshType.Head
		m.MeshId = ""
		m.TextureId = ""
		m.Offset = Vector3.zero
		m.Scale = Vector3.new(1.25, 1.25, 1.25)
	end

	pintarCuerpo(modelo, a, colores)

	-- Cara.
	if cabeza and cabeza:IsA("BasePart") then
		for _, rasgo in RASGOS do
			local campo, orden = rasgo.Campo, rasgo.Orden
			local imagen = Recursos.Imagenes[`{campo}_{(a :: any)[campo]}`]
			if imagen then
				local d = Instance.new("Decal")
				d.Name = "Rasgo_" .. campo
				d.Face = Enum.NormalId.Front
				d.Texture = imagen
				d.ZIndex = orden
				if campo == "Cejas" then
					d.Color3 = color(colores.Pelo)
				end
				d.Parent = cabeza
			end
		end
	end

	local faltan = 0

	-- Cabello y accesorio.
	if cabeza and cabeza:IsA("BasePart") then
		for _, cosa in
			{
				{ Constructor.ACCESORIO_CABELLO, "Cabello", a.Cabello },
				{ Constructor.ACCESORIO_COMPLEMENTO, "Accesorio", a.Accesorio },
			}
		do
			local opcion = Apariencia.Buscar(cosa[2], cosa[3])
			if opcion and opcion.Anclaje then
				faltan += ponerAccesorio(
					modelo,
					cabeza,
					cosa[1],
					`{cosa[2]}_{cosa[3]}`,
					opcion.Anclaje,
					colores,
					fuente
				)
			end
		end
	end

	-- Detalles 3D de la ropa.
	local carpeta = Instance.new("Folder")
	carpeta.Name = Constructor.CARPETA
	for _, clave in { "Chaqueta_" .. a.Chaqueta, "Pantalon_" .. a.Pantalon } do
		local lista: { Recursos.Pieza } = Recursos.Piezas[clave] or {}
		for _, pieza in lista do
			local base = modelo:FindFirstChild(pieza.Parte)
			if base == nil or not base:IsA("BasePart") then
				continue
			end
			local p = crearPieza(pieza, colores, fuente)
			if p == nil then
				faltan += 1
				continue
			end
			p.Name = pieza.Nombre
			p.CFrame = base.CFrame * centro(pieza)
			soldar(base, p)
			p.Parent = carpeta
		end
	end
	carpeta.Parent = modelo
	return faltan
end

return Constructor
