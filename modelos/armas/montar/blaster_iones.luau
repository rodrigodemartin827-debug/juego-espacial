--!strict
-- Monta «Blaster de Iones» como Tool de Roblox a partir del modelo importado de blaster_iones.fbx.
-- Generado por modelos/herramientas/armas.py: no lo edites a mano, cambia la plantilla y vuelve a generar.
--
-- Uso (barra de comandos de Studio):
--   1. Importa blaster_iones.fbx con Import 3D (Scale Unit = Meter, Anchored desactivado).
--   2. Sube las texturas de modelos/armas/texturas/BlasterIones_*.png y pega sus IDs en TEXTURAS (opcional: si se
--      dejan vacías, el importador suele haber creado ya la SurfaceAppearance con el color).
--   3. Selecciona el modelo importado y pega este script en la barra de comandos.
--
-- Crea un Tool con un Handle invisible en el punto de agarre (eje Y hacia la hoja o el cañón, como pide Roblox),
-- suelda todas las piezas al Handle, pone Neon/Glass donde toca y, en armas de dos manos, un Attachment
-- "ManoIzquierda" en el agarre frontal.

local Selection = game:GetService("Selection")

local TEXTURAS = {
	ColorMap = "", -- BlasterIones_color.png
	NormalMap = "", -- BlasterIones_normal.png
	RoughnessMap = "", -- BlasterIones_roughness.png
	MetalnessMap = "", -- BlasterIones_metalness.png
}

local DATOS = {
	arma = "Blaster de Iones",
	archivo = "blaster_iones.fbx",
	rareza = "Poco común",
	colorBorde = "#4AFF8B",
	triangulos = 2036,
	trisMax = 3000,
	texturas = {
		color = "texturas/BlasterIones_color.png",
		normal = "texturas/BlasterIones_normal.png",
		roughness = "texturas/BlasterIones_roughness.png",
		metalness = "texturas/BlasterIones_metalness.png",
		emision = "texturas/BlasterIones_emision.png",
	},
	piezaRaiz = "BlasterIones_Grip",
	piezas = {
		{
			nombre = "BlasterIones_Cuerpo",
			rol = "tex",
			triangulos = 908,
			centro = { 0.0137, 0.365, -0.1061 },
			SurfaceAppearance = true,
		},
		{
			nombre = "BlasterIones_Neon_02",
			rol = "neon",
			triangulos = 24,
			centro = { 0.0137, 0.35, 0.0638 },
			Material = "Neon",
			Color = "#3DF2FF",
			nota = "Rejillas: subir el brillo al disparar",
		},
		{
			nombre = "BlasterIones_Neon_01",
			rol = "neon",
			triangulos = 96,
			centro = { 0.0137, 0.34, -0.7762 },
			Material = "Neon",
			Color = "#3DF2FF",
		},
		{
			nombre = "BlasterIones_Canon_Izq",
			rol = "tex",
			triangulos = 96,
			centro = { -0.0613, 0.34, -0.6262 },
			SurfaceAppearance = true,
		},
		{
			nombre = "BlasterIones_Canon_Der",
			rol = "tex",
			triangulos = 96,
			centro = { 0.0888, 0.34, -0.6262 },
			SurfaceAppearance = true,
		},
		{
			nombre = "BlasterIones_Grip",
			rol = "tex",
			triangulos = 664,
			centro = { -0.0, 0.0, 0.0 },
			SurfaceAppearance = true,
		},
		{
			nombre = "BlasterIones_Cargador",
			rol = "tex",
			triangulos = 152,
			centro = { 0.0137, -0.2875, 0.2229 },
			SurfaceAppearance = true,
		},
	},
	agarres = {
		Handle = {
			posicion = { 0.0137, 0.0, 0.0844 },
			ejeY = { -0.0, 0.0, -1.0 },
		},
	},
	notas = {  },
}

local modelo = Selection:Get()[1]
assert(modelo and modelo:IsA("Model"), "Selecciona el modelo importado de blaster_iones.fbx")

local raiz = modelo:FindFirstChild(DATOS.piezaRaiz, true) :: BasePart?
assert(raiz and raiz:IsA("BasePart"), "No encuentro la pieza raíz " .. DATOS.piezaRaiz)

local function v3(t: { number }): Vector3
	return Vector3.new(t[1], t[2], t[3])
end

-- CFrame del agarre: posición relativa al centro de la pieza raíz y eje Y hacia la hoja o el cañón.
local function cframeAgarre(agarre): CFrame
	local pos = raiz.CFrame:PointToWorldSpace(v3(agarre.posicion))
	local arriba = raiz.CFrame:VectorToWorldSpace(v3(agarre.ejeY)).Unit
	local ref = if math.abs(arriba.Z) < 0.9 then Vector3.zAxis else Vector3.xAxis
	local derecha = arriba:Cross(ref).Unit
	return CFrame.fromMatrix(pos, derecha, arriba)
end

local tool = Instance.new("Tool")
tool.Name = DATOS.arma
tool.CanBeDropped = false
tool.RequiresHandle = true
tool:SetAttribute("Rareza", DATOS.rareza)
tool:SetAttribute("ColorRareza", Color3.fromHex(DATOS.colorBorde))

local handle = Instance.new("Part")
handle.Name = "Handle"
handle.Size = Vector3.new(0.2, 0.2, 0.2)
handle.Transparency = 1
handle.CanCollide = false
handle.Massless = false
handle.CFrame = cframeAgarre(DATOS.agarres.Handle)
handle.Parent = tool

if DATOS.agarres.Handle_Frontal then
	local mano = Instance.new("Attachment")
	mano.Name = "ManoIzquierda"
	mano.CFrame = handle.CFrame:ToObjectSpace(cframeAgarre(DATOS.agarres.Handle_Frontal))
	mano.Parent = handle
end

local conTextura = TEXTURAS.ColorMap ~= ""
for _, info in DATOS.piezas do
	local p = modelo:FindFirstChild(info.nombre, true) :: MeshPart?
	if not p then
		warn("Falta la pieza " .. info.nombre)
		continue
	end
	p.Anchored = false
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.Massless = true
	if info.Material == "Neon" then
		p.Material = Enum.Material.Neon
		p.Color = Color3.fromHex(info.Color)
		local sa = p:FindFirstChildOfClass("SurfaceAppearance")
		if sa then
			sa:Destroy()
		end
	elseif info.Material == "Glass" then
		p.Material = Enum.Material.Glass
		p.Color = Color3.fromHex(info.Color)
		p.Transparency = info.Transparency
		local sa = p:FindFirstChildOfClass("SurfaceAppearance")
		if sa then
			sa:Destroy()
		end
	elseif conTextura then
		local sa = p:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")
		for propiedad, id in TEXTURAS do
			if id ~= "" then
				(sa :: any)[propiedad] = id
			end
		end
		-- (sin piezas translúcidas)
		sa.Parent = p
	end
	local w = Instance.new("WeldConstraint")
	w.Part0 = handle
	w.Part1 = p
	w.Parent = p
	p.Parent = tool
end

tool.Parent = modelo.Parent
modelo:Destroy()
Selection:Set({ tool })
print("Tool montado: " .. tool.Name)
