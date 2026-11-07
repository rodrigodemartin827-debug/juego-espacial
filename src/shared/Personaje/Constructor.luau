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

local Players = game:GetService("Players")
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
-- Tamaño de cada parte de un R6 estándar (la complexión lo estira desde aquí, nunca desde lo que haya).
local TAM_STD: { [string]: Vector3 } = {
	Head = Vector3.new(2, 1, 1),
	Torso = Vector3.new(2, 2, 1),
	["Left Arm"] = Vector3.new(1, 2, 1),
	["Right Arm"] = Vector3.new(1, 2, 1),
	["Left Leg"] = Vector3.new(1, 2, 1),
	["Right Leg"] = Vector3.new(1, 2, 1),
}
local GRUPO_DE: { [string]: string } = {
	Torso = "Torso",
	["Left Arm"] = "Brazos",
	["Right Arm"] = "Brazos",
	["Left Leg"] = "Piernas",
	["Right Leg"] = "Piernas",
}

local function vector(t: { number }?): Vector3
	return if t then Vector3.new(t[1], t[2], t[3]) else Vector3.one
end

-- Cuánto está estirada una parte respecto a su tamaño estándar (para las piezas que lleva encima).
local function estiramiento(parte: BasePart): Vector3
	local std: Vector3? = TAM_STD[parte.Name]
	if std then
		return Vector3.new(parte.Size.X / std.X, parte.Size.Y / std.Y, parte.Size.Z / std.Z)
	end
	return Vector3.one
end

-- Una articulación con la posición estirada por `f` (la orientación no cambia).
local function estirar(cf: CFrame, f: Vector3): CFrame
	local p = cf.Position
	return CFrame.new(p.X * f.X, p.Y * f.Y, p.Z * f.Z) * (cf - p)
end

--[[
	Complexión: estira el torso, los brazos y las piernas del R6 (la cabeza no) según `opcion.Escala` (nil = normal) y
	recoloca las articulaciones (Motor6D) para que sigan encajando. Las animaciones solo giran, así que valen igual.
	Se puede llamar las veces que se quiera: parte siempre del tamaño estándar y de las articulaciones originales (que
	se guardan en atributos la primera vez).
]]
function Constructor.Complexion(modelo: Model, opcion: any)
	local escala = if opcion and opcion.Escala then opcion.Escala else {}
	local f: { [string]: Vector3 } = {}
	for nombre, std in TAM_STD do
		local grupo = GRUPO_DE[nombre]
		f[nombre] = if grupo then vector((escala :: any)[grupo]) else Vector3.one
		local parte = modelo:FindFirstChild(nombre)
		if parte and parte:IsA("BasePart") then
			parte.Size = Vector3.new(std.X * f[nombre].X, std.Y * f[nombre].Y, std.Z * f[nombre].Z)
		end
	end
	for _, d in modelo:GetDescendants() do
		if d:IsA("Motor6D") and d.Part0 and d.Part1 and (TAM_STD[d.Part1.Name] or d.Part1.Name == "Torso") then
			local c0 = d:GetAttribute("C0Base") or d.C0
			local c1 = d:GetAttribute("C1Base") or d.C1
			d:SetAttribute("C0Base", c0)
			d:SetAttribute("C1Base", c1)
			d.C0 = estirar(c0 :: CFrame, f[d.Part0.Name] or Vector3.one)
			d.C1 = estirar(c1 :: CFrame, f[d.Part1.Name] or Vector3.one)
		end
	end
end

-- Quita los tatuajes de los brazos.
local function quitarTatuajes(modelo: Model)
	for _, nombre in { "Left Arm", "Right Arm" } do
		local brazo = modelo:FindFirstChild(nombre)
		if brazo then
			for _, d in brazo:GetChildren() do
				if d:IsA("Decal") and d.Name == "Tatuaje" then
					d:Destroy()
				end
			end
		end
	end
end

local function pintarCuerpo(modelo: Model, a: Apariencia.Apariencia, colores: { [string]: string })
	local chaqueta = Apariencia.Buscar("Chaqueta", a.Chaqueta)
	local pantalon = Apariencia.Buscar("Pantalon", a.Pantalon)
	local rolBrazos = chaqueta.Brazos or "Chaqueta"
	local rolPiernas = pantalon.Piernas or "Pantalon"
	local rolParte = {
		Head = "Piel",
		Torso = "Chaqueta",
		["Left Arm"] = rolBrazos,
		["Right Arm"] = rolBrazos,
		["Left Leg"] = rolPiernas,
		["Right Leg"] = rolPiernas,
	}
	for _, nombre in PARTES_R6 do
		local parte = modelo:FindFirstChild(nombre)
		if parte and parte:IsA("BasePart") then
			local rol = rolParte[nombre]
			parte.Color = color(colores[rol])
			-- PROBADO EN STUDIO: la tela (Fabric) se ve como punto de lana a esta escala; liso queda mejor.
			parte.Material = Enum.Material.SmoothPlastic
		end
	end
end

-- Quita lo que puso Aplicar (accesorios del juego, detalles de ropa y rasgos de la cara), para dejar paso al avatar de
-- Roblox. El avatar trae lo suyo: ApplyDescription pone su cabeza, su cara, su ropa y sus colores.
function Constructor.Limpiar(modelo: Model)
	quitarTatuajes(modelo)
	Constructor.Complexion(modelo, nil)
	-- El HumanoidDescription que ya tiene el Humanoid se quita: si es igual al que se va a aplicar, ApplyDescription
	-- cree que el personaje ya lo lleva y no hace nada (PROBADO EN STUDIO).
	local humanoide = modelo:FindFirstChildOfClass("Humanoid")
	local anterior = humanoide and humanoide:FindFirstChildOfClass("HumanoidDescription")
	if anterior then
		anterior:Destroy()
	end
	for _, d in modelo:GetChildren() do
		if d:IsA("Accessory") or d.Name == Constructor.CARPETA then
			d:Destroy()
		end
	end
	local cabeza = modelo:FindFirstChild("Head")
	if cabeza then
		for _, d in cabeza:GetChildren() do
			if d:IsA("Decal") and string.sub(d.Name, 1, 6) == "Rasgo_" then
				d:Destroy()
			end
		end
	end
end

-- Lo que trae un personaje de Roblox con su aspecto (el avatar) y se copia de un R6 al otro.
local COPIAR_DEL_AVATAR = { "Shirt", "Pants", "ShirtGraphic", "BodyColors", "CharacterMesh" }

-- Un accesorio copiado de otro R6 viene soldado a la cabeza (o al torso) de ESE R6: se le vuelve a soldar al
-- Attachment del mismo nombre del personaje. PROBADO EN STUDIO: sin esto, al borrar el R6 temporal los sombreros se
-- quedaban sin soldadura (Part1 = nil) y flotando.
local function reatar(accesorio: Accessory, modelo: Model)
	local asa = accesorio:FindFirstChild("Handle")
	local soldadura = asa and asa:FindFirstChildWhichIsA("Weld")
	local propio = asa and asa:FindFirstChildOfClass("Attachment")
	if asa == nil or soldadura == nil or propio == nil then
		return
	end
	for _, d in modelo:GetDescendants() do
		if
			d:IsA("Attachment")
			and d.Name == propio.Name
			and d.Parent
			and d.Parent:IsA("BasePart")
			and d.Parent ~= asa
		then
			soldadura.Part0 = asa :: BasePart
			soldadura.C0 = propio.CFrame
			soldadura.Part1 = d.Parent
			soldadura.C1 = d.CFrame
			return
		end
	end
end

--[[
	Pone el avatar de Roblox (`descripcion`, ya preparada con Personaje/AvatarR6) en el personaje R6 `modelo`. Tarda
	un poco (Roblox carga los recursos): hay que llamarlo desde un hilo que pueda esperar. `sigueVigente` (opcional) se
	pregunta al volver de esa espera: si dice que no, no se toca nada. Devuelve false si no pudo.

	PROBADO EN STUDIO: Humanoid:ApplyDescription falla en un personaje editado («The current HumanoidDescription does
	not match the assets currently applied to the character»), y este juego lo edita (piezas propias, colores). Por eso se
	construye un R6 limpio con el avatar y se le pasan al personaje su ropa, accesorios, colores, cara y cabeza.
]]
function Constructor.PonerAvatar(
	modelo: Model,
	descripcion: HumanoidDescription,
	sigueVigente: (() -> boolean)?
): boolean
	local humanoide = modelo:FindFirstChildOfClass("Humanoid")
	local cabeza = modelo:FindFirstChild("Head")
	if humanoide == nil or cabeza == nil or not cabeza:IsA("BasePart") then
		return false
	end
	local ok, rig = pcall(function()
		return Players:CreateHumanoidModelFromDescriptionAsync(descripcion, Enum.HumanoidRigType.R6)
	end)
	if not ok or rig == nil then
		warn(`[Constructor] No se pudo crear el avatar: {rig}`)
		return false
	end
	local origen = rig :: Model
	-- Mientras Roblox cargaba, puede que se haya pedido otro aspecto: entonces este ya no vale.
	if sigueVigente and not sigueVigente() then
		origen:Destroy()
		return true
	end

	-- Fuera lo del aspecto anterior (piezas del juego y avatar anterior).
	Constructor.Limpiar(modelo)
	for _, d in modelo:GetChildren() do
		if table.find(COPIAR_DEL_AVATAR, d.ClassName) then
			d:Destroy()
		end
	end
	for _, d in cabeza:GetChildren() do
		if d:IsA("Decal") then
			d:Destroy()
		end
	end

	-- Ropa, colores y accesorios.
	for _, d in origen:GetChildren() do
		if table.find(COPIAR_DEL_AVATAR, d.ClassName) then
			d:Clone().Parent = modelo
		elseif d:IsA("Accessory") then
			local copia = d:Clone()
			copia.Parent = modelo
			reatar(copia, modelo)
		end
	end
	-- Colores de las partes (el BodyColors ya los pone, pero así no dependen de él) y cara.
	for _, nombre in PARTES_R6 do
		local de, a = origen:FindFirstChild(nombre), modelo:FindFirstChild(nombre)
		if de and a and de:IsA("BasePart") and a:IsA("BasePart") then
			a.Color = de.Color
			a.Material = de.Material
		end
	end
	local cabezaOrigen = origen:FindFirstChild("Head")
	if cabezaOrigen then
		for _, d in cabezaOrigen:GetChildren() do
			if d:IsA("Decal") then
				d:Clone().Parent = cabeza
			end
		end
		-- La cabeza del avatar (clásica, o una malla como la tele de algunos paquetes).
		local malla = cabezaOrigen:FindFirstChildOfClass("SpecialMesh")
		if malla then
			local existente = cabeza:FindFirstChildOfClass("SpecialMesh")
			local m: SpecialMesh = if existente then existente else Instance.new("SpecialMesh")
			m.Parent = cabeza
			m.MeshId = malla.MeshId
			m.TextureId = malla.TextureId
			m.MeshType = malla.MeshType
			m.Scale = malla.Scale
			m.Offset = malla.Offset
		end
	end
	origen:Destroy()
	return true
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
		-- Primero se vacían los ids y DESPUÉS se pone el tipo: al revés, un MeshId vacío cambia el tipo a FileMesh y la
		-- cabeza desaparece (PROBADO EN STUDIO al volver del avatar de Roblox, cuya cabeza era una malla).
		m.MeshId = ""
		m.TextureId = ""
		m.MeshType = Enum.MeshType.Head
		m.Offset = Vector3.zero
		m.Scale = Vector3.new(1.25, 1.25, 1.25)
	end

	pintarCuerpo(modelo, a, colores)
	quitarTatuajes(modelo)
	Constructor.Complexion(modelo, Apariencia.Buscar("Complexion", a.Complexion))

	-- Tatuajes: solo se ven (y solo se ponen) con los brazos al aire. Van por delante y por el lado de fuera.
	local tatuaje = Recursos.Imagenes["Tatuaje_" .. a.Tatuaje]
	if tatuaje and Apariencia.TatuajeVisible(a) then
		local brazos: { { nombre: string, lado: Enum.NormalId } } = {
			{ nombre = "Left Arm", lado = Enum.NormalId.Left },
			{ nombre = "Right Arm", lado = Enum.NormalId.Right },
		}
		for _, par in brazos do
			local brazo = modelo:FindFirstChild(par.nombre)
			if brazo and brazo:IsA("BasePart") then
				for _, cara in { Enum.NormalId.Front, par.lado } do
					local d = Instance.new("Decal")
					d.Name = "Tatuaje"
					d.Face = cara
					d.Texture = tatuaje
					d.Parent = brazo
				end
			end
		end
	end

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
		-- Cicatriz (por encima de los demás rasgos).
		local cicatriz = Recursos.Imagenes["Cicatriz_" .. a.Cicatriz]
		if cicatriz then
			local d = Instance.new("Decal")
			d.Name = "Rasgo_Cicatriz"
			d.Face = Enum.NormalId.Front
			d.Texture = cicatriz
			d.ZIndex = 5
			d.Parent = cabeza
		end
	end

	local faltan = 0

	-- Cabello y accesorio.
	if cabeza and cabeza:IsA("BasePart") then
		for _, cosa in
			{
				{ Constructor.ACCESORIO_CABELLO, "Cabello", a.Cabello },
				{ Constructor.ACCESORIO_COMPLEMENTO, "Accesorio", a.Accesorio },
				{ "Barba", "Barba", a.Barba },
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
			-- Las piezas siguen el estiramiento de su parte (la complexión).
			local f = estiramiento(base)
			p.Size = Vector3.new(p.Size.X * f.X, p.Size.Y * f.Y, p.Size.Z * f.Z)
			local pos = centro(pieza).Position
			p.CFrame = base.CFrame * CFrame.new(pos.X * f.X, pos.Y * f.Y, pos.Z * f.Z)
			soldar(base, p)
			p.Parent = carpeta
		end
	end
	carpeta.Parent = modelo
	return faltan
end

return Constructor
