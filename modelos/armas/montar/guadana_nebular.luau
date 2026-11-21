--!strict
-- Monta «Guadaña Nebular» como Tool de Roblox a partir del modelo importado de guadana_nebular.fbx.
-- Generado por modelos/herramientas/armas.py: no lo edites a mano, cambia la plantilla y vuelve a generar.
--
-- Uso (barra de comandos de Studio):
--   1. Importa guadana_nebular.fbx con Import 3D (Scale Unit = Meter, Anchored desactivado).
--   2. Sube las texturas de modelos/armas/texturas/GuadanaNebular_*.png y pega sus IDs en TEXTURAS (opcional: si se
--      dejan vacías, el importador suele haber creado ya la SurfaceAppearance con el color).
--   3. Selecciona el modelo importado y pega este script en la barra de comandos.
--
-- Crea un Tool con un Handle invisible en el punto de agarre (eje Y hacia la hoja o el cañón, como pide Roblox),
-- suelda todas las piezas al Handle, pone Neon/Glass donde toca y, en armas de dos manos, un Attachment
-- "ManoIzquierda" en el agarre frontal.

local Selection = game:GetService("Selection")

local TEXTURAS = {
	ColorMap = "", -- GuadanaNebular_color.png
	NormalMap = "", -- GuadanaNebular_normal.png
	RoughnessMap = "", -- GuadanaNebular_roughness.png
	MetalnessMap = "", -- GuadanaNebular_metalness.png
}

local DATOS = {
	arma = "Guadaña Nebular",
	archivo = "guadana_nebular.fbx",
	rareza = "Legendario",
	colorBorde = "#FFB800",
	triangulos = 3156,
	trisMax = 6500,
	texturas = {
		color = "texturas/GuadanaNebular_color.png",
		normal = "texturas/GuadanaNebular_normal.png",
		roughness = "texturas/GuadanaNebular_roughness.png",
		metalness = "texturas/GuadanaNebular_metalness.png",
		emision = "texturas/GuadanaNebular_emision.png",
	},
	piezaRaiz = "GuadanaNebular_Mango",
	piezas = {
		{
			nombre = "GuadanaNebular_Hoja",
			rol = "tex",
			triangulos = 306,
			centro = { 0.7831, 1.2479, 0.0013 },
			SurfaceAppearance = true,
		},
		{
			nombre = "GuadanaNebular_Wisps",
			rol = "tex",
			triangulos = 960,
			centro = { 0.8422, 1.4685, -0.0044 },
			SurfaceAppearance = true,
		},
		{
			nombre = "GuadanaNebular_Neon_01",
			rol = "neon",
			triangulos = 296,
			centro = { 0.7973, 1.1795, 0.0013 },
			Material = "Neon",
			Color = "#3DF2FF",
		},
		{
			nombre = "GuadanaNebular_Mango",
			rol = "tex",
			triangulos = 406,
			centro = { -0.0, 0.0, 0.0 },
			SurfaceAppearance = true,
		},
		{
			nombre = "GuadanaNebular_Runas",
			rol = "tex",
			triangulos = 216,
			centro = { -0.0169, 0.1266, 0.0013 },
			SurfaceAppearance = true,
		},
		{
			nombre = "GuadanaNebular_Neon_02",
			rol = "neon",
			triangulos = 216,
			centro = { -0.0169, 0.126, 0.0013 },
			Material = "Neon",
			Color = "#3DF2FF",
		},
		{
			nombre = "GuadanaNebular_Anillo",
			rol = "tex",
			triangulos = 552,
			centro = { 0.0229, 1.5542, 0.0013 },
			SurfaceAppearance = true,
		},
		{
			nombre = "GuadanaNebular_Puas",
			rol = "tex",
			triangulos = 60,
			centro = { -0.1423, 1.5466, 0.0013 },
			SurfaceAppearance = true,
		},
		{
			nombre = "GuadanaNebular_Gema",
			rol = "tex",
			triangulos = 80,
			centro = { 0.0281, -1.53, 0.0013 },
			SurfaceAppearance = true,
		},
		{
			nombre = "GuadanaNebular_Neon_03",
			rol = "neon",
			triangulos = 64,
			centro = { 0.0281, -1.53, 0.0013 },
			Material = "Neon",
			Color = "#3DF2FF",
		},
	},
	agarres = {
		Handle = {
			posicion = { -0.0012, -0.77, 0.0013 },
			ejeY = { -0.0, 1.0, 0.0 },
		},
		Handle_Frontal = {
			posicion = { -0.0194, 0.43, 0.0013 },
			ejeY = { -0.0, 1.0, 0.0 },
		},
	},
	notas = {
		"Hoja = textura de nebulosa; Neon_01 es el filo que brilla (la hoja entera en Neon taparía la textura)",
		"color con alfa: SurfaceAppearance.AlphaMode = Transparency",
	},
}

local modelo = Selection:Get()[1]
assert(modelo and modelo:IsA("Model"), "Selecciona el modelo importado de guadana_nebular.fbx")

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
