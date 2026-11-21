--!strict
-- Monta «Espada Estelar» como Tool de Roblox a partir del modelo importado de espada_estelar.fbx.
-- Generado por modelos/herramientas/armas.py: no lo edites a mano, cambia la plantilla y vuelve a generar.
--
-- Uso (barra de comandos de Studio):
--   1. Importa espada_estelar.fbx con Import 3D (Scale Unit = Meter, Anchored desactivado).
--   2. Sube las texturas de modelos/armas/texturas/EspadaEstelar_*.png y pega sus IDs en TEXTURAS (opcional: si se
--      dejan vacías, el importador suele haber creado ya la SurfaceAppearance con el color).
--   3. Selecciona el modelo importado y pega este script en la barra de comandos.
--
-- Crea un Tool con un Handle invisible en el punto de agarre (eje Y hacia la hoja o el cañón, como pide Roblox),
-- suelda todas las piezas al Handle, pone Neon/Glass donde toca y, en armas de dos manos, un Attachment
-- "ManoIzquierda" en el agarre frontal.

local Selection = game:GetService("Selection")

local TEXTURAS = {
	ColorMap = "", -- EspadaEstelar_color.png
	NormalMap = "", -- EspadaEstelar_normal.png
	RoughnessMap = "", -- EspadaEstelar_roughness.png
	MetalnessMap = "", -- EspadaEstelar_metalness.png
}

local DATOS = {
	arma = "Espada Estelar",
	archivo = "espada_estelar.fbx",
	rareza = "Legendario",
	colorBorde = "#FFB800",
	triangulos = 3692,
	trisMax = 6500,
	texturas = {
		color = "texturas/EspadaEstelar_color.png",
		normal = "texturas/EspadaEstelar_normal.png",
		roughness = "texturas/EspadaEstelar_roughness.png",
		metalness = "texturas/EspadaEstelar_metalness.png",
		emision = "texturas/EspadaEstelar_emision.png",
	},
	piezaRaiz = "EspadaEstelar_Empunadura",
	piezas = {
		{
			nombre = "EspadaEstelar_Hoja",
			rol = "tex",
			triangulos = 652,
			centro = { -0.0194, 1.9088, -0.0018 },
			SurfaceAppearance = true,
		},
		{
			nombre = "EspadaEstelar_Guarda",
			rol = "tex",
			triangulos = 860,
			centro = { 0.0008, 0.54, -0.0018 },
			SurfaceAppearance = true,
		},
		{
			nombre = "EspadaEstelar_Neon_02",
			rol = "neon",
			triangulos = 424,
			centro = { 0.0008, 0.5854, -0.0018 },
			Material = "Neon",
			Color = "#3DF2FF",
		},
		{
			nombre = "EspadaEstelar_Empunadura",
			rol = "tex",
			triangulos = 540,
			centro = { -0.0, 0.0, 0.0 },
			SurfaceAppearance = true,
		},
		{
			nombre = "EspadaEstelar_Neon_03",
			rol = "neon",
			triangulos = 180,
			centro = { 0.0004, 0.0, -0.001 },
			Material = "Neon",
			Color = "#3DF2FF",
		},
		{
			nombre = "EspadaEstelar_Pomo",
			rol = "tex",
			triangulos = 516,
			centro = { 0.0008, -0.535, -0.0018 },
			SurfaceAppearance = true,
		},
		{
			nombre = "EspadaEstelar_Neon_05",
			rol = "neon",
			triangulos = 192,
			centro = { -0.0051, -0.5383, 0.0016 },
			Material = "Neon",
			Color = "#3DF2FF",
		},
		{
			nombre = "EspadaEstelar_Neon_01",
			rol = "neon",
			triangulos = 232,
			centro = { -0.0303, 1.7932, -0.0018 },
			Material = "Neon",
			Color = "#3DF2FF",
		},
		{
			nombre = "EspadaEstelar_Neon_04",
			rol = "neon",
			triangulos = 48,
			centro = { 0.0012, 1.9382, -0.0006 },
			Material = "Neon",
			Color = "#3DF2FF",
			nota = "Núcleos de los 6 fragmentos: animarlos con ellos",
		},
		{
			nombre = "EspadaEstelar_Fragmento_01",
			rol = "tex",
			triangulos = 8,
			centro = { -0.3912, 1.114, 0.0833 },
			SurfaceAppearance = true,
		},
		{
			nombre = "EspadaEstelar_Fragmento_02",
			rol = "tex",
			triangulos = 8,
			centro = { -0.1224, 1.4498, 0.3337 },
			SurfaceAppearance = true,
		},
		{
			nombre = "EspadaEstelar_Fragmento_03",
			rol = "tex",
			triangulos = 8,
			centro = { 0.2541, 1.7857, 0.1799 },
			SurfaceAppearance = true,
		},
		{
			nombre = "EspadaEstelar_Fragmento_04",
			rol = "tex",
			triangulos = 8,
			centro = { 0.3957, 2.1226, -0.0915 },
			SurfaceAppearance = true,
		},
		{
			nombre = "EspadaEstelar_Fragmento_05",
			rol = "tex",
			triangulos = 8,
			centro = { 0.0964, 2.4565, -0.3529 },
			SurfaceAppearance = true,
		},
		{
			nombre = "EspadaEstelar_Fragmento_06",
			rol = "tex",
			triangulos = 8,
			centro = { -0.2816, 2.7944, -0.1836 },
			SurfaceAppearance = true,
		},
	},
	agarres = {
		Handle = {
			posicion = { 0.0008, 0.0, -0.0018 },
			ejeY = { -0.0, 1.0, 0.0 },
		},
	},
	notas = {
		"color con alfa: SurfaceAppearance.AlphaMode = Transparency",
	},
}

local modelo = Selection:Get()[1]
assert(modelo and modelo:IsA("Model"), "Selecciona el modelo importado de espada_estelar.fbx")

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
