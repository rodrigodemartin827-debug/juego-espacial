--!strict
-- Monta «Hoja del Vacío» como Tool de Roblox a partir del modelo importado de hoja_vacio.fbx.
-- Generado por modelos/herramientas/armas.py: no lo edites a mano, cambia la plantilla y vuelve a generar.
--
-- Uso (barra de comandos de Studio):
--   1. Importa hoja_vacio.fbx con Import 3D (Scale Unit = Meter, Anchored desactivado).
--   2. Sube las texturas de modelos/armas/texturas/HojaVacio_*.png y pega sus IDs en TEXTURAS (opcional: si se
--      dejan vacías, el importador suele haber creado ya la SurfaceAppearance con el color).
--   3. Selecciona el modelo importado y pega este script en la barra de comandos.
--
-- Crea un Tool con un Handle invisible en el punto de agarre (eje Y hacia la hoja o el cañón, como pide Roblox),
-- suelda todas las piezas al Handle, pone Neon/Glass donde toca y, en armas de dos manos, un Attachment
-- "ManoIzquierda" en el agarre frontal.

local Selection = game:GetService("Selection")

local TEXTURAS = {
	ColorMap = "", -- HojaVacio_color.png
	NormalMap = "", -- HojaVacio_normal.png
	RoughnessMap = "", -- HojaVacio_roughness.png
	MetalnessMap = "", -- HojaVacio_metalness.png
}

local DATOS = {
	arma = "Hoja del Vacío",
	archivo = "hoja_vacio.fbx",
	rareza = "Mítico",
	colorBorde = "#FF4444",
	triangulos = 4448,
	trisMax = 8000,
	texturas = {
		color = "texturas/HojaVacio_color.png",
		normal = "texturas/HojaVacio_normal.png",
		roughness = "texturas/HojaVacio_roughness.png",
		metalness = "texturas/HojaVacio_metalness.png",
		emision = "texturas/HojaVacio_emision.png",
	},
	piezaRaiz = "HojaVacio_Empunadura",
	piezas = {
		{
			nombre = "HojaVacio_Hoja",
			rol = "tex",
			triangulos = 190,
			centro = { 0.0011, 2.075, 0.0022 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Aura",
			rol = "tex",
			triangulos = 382,
			centro = { 0.0011, 2.115, 0.0022 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Neon_01",
			rol = "neon",
			triangulos = 264,
			centro = { 0.0011, 2.0536, 0.0022 },
			Material = "Neon",
			Color = "#E0206A",
		},
		{
			nombre = "HojaVacio_Orbe",
			rol = "tex",
			triangulos = 396,
			centro = { 0.0011, 0.505, 0.0022 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Neon_03",
			rol = "neon",
			triangulos = 272,
			centro = { 0.0011, 0.6722, 0.0022 },
			Material = "Neon",
			Color = "#881111",
		},
		{
			nombre = "HojaVacio_Garra_Izq",
			rol = "tex",
			triangulos = 414,
			centro = { -0.282, 0.7295, 0.0004 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Garra_Der",
			rol = "tex",
			triangulos = 414,
			centro = { 0.2842, 0.7295, 0.004 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Empunadura",
			rol = "tex",
			triangulos = 1096,
			centro = { -0.0, 0.0, 0.0 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Ojo",
			rol = "tex",
			triangulos = 832,
			centro = { 0.0011, -0.575, -0.0163 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Neon_02",
			rol = "neon",
			triangulos = 140,
			centro = { 0.0011, -0.575, -0.1278 },
			Material = "Neon",
			Color = "#FF2222",
		},
		{
			nombre = "HojaVacio_Fragmento_01",
			rol = "tex",
			triangulos = 6,
			centro = { 0.3386, 2.644, -0.2049 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Fragmento_02",
			rol = "tex",
			triangulos = 6,
			centro = { 0.3972, 1.4832, 0.0427 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Fragmento_03",
			rol = "tex",
			triangulos = 6,
			centro = { 0.2343, 1.1938, -0.1273 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Fragmento_04",
			rol = "tex",
			triangulos = 6,
			centro = { -0.1159, 3.1165, 0.2592 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Fragmento_05",
			rol = "tex",
			triangulos = 6,
			centro = { -0.3674, 2.4905, -0.0025 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Fragmento_06",
			rol = "tex",
			triangulos = 6,
			centro = { 0.0044, 2.9108, -0.1958 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Fragmento_07",
			rol = "tex",
			triangulos = 6,
			centro = { -0.349, 3.1311, -0.1076 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HojaVacio_Fragmento_08",
			rol = "tex",
			triangulos = 6,
			centro = { -0.3508, 1.6978, 0.1237 },
			SurfaceAppearance = true,
		},
	},
	agarres = {
		Handle = {
			posicion = { 0.0011, 0.0, 0.0022 },
			ejeY = { -0.0, 1.0, 0.0 },
		},
	},
	notas = {
		"color con alfa: SurfaceAppearance.AlphaMode = Transparency",
	},
}

local modelo = Selection:Get()[1]
assert(modelo and modelo:IsA("Model"), "Selecciona el modelo importado de hoja_vacio.fbx")

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
		sa.AlphaMode = Enum.AlphaMode.Transparency
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
