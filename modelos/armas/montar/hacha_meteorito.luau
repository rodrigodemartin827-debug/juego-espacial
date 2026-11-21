--!strict
-- Monta «Hacha de Meteorito» como Tool de Roblox a partir del modelo importado de hacha_meteorito.fbx.
-- Generado por modelos/herramientas/armas.py: no lo edites a mano, cambia la plantilla y vuelve a generar.
--
-- Uso (barra de comandos de Studio):
--   1. Importa hacha_meteorito.fbx con Import 3D (Scale Unit = Meter, Anchored desactivado).
--   2. Sube las texturas de modelos/armas/texturas/HachaMeteorito_*.png y pega sus IDs en TEXTURAS (opcional: si se
--      dejan vacías, el importador suele haber creado ya la SurfaceAppearance con el color).
--   3. Selecciona el modelo importado y pega este script en la barra de comandos.
--
-- Crea un Tool con un Handle invisible en el punto de agarre (eje Y hacia la hoja o el cañón, como pide Roblox),
-- suelda todas las piezas al Handle, pone Neon/Glass donde toca y, en armas de dos manos, un Attachment
-- "ManoIzquierda" en el agarre frontal.

local Selection = game:GetService("Selection")

local TEXTURAS = {
	ColorMap = "", -- HachaMeteorito_color.png
	NormalMap = "", -- HachaMeteorito_normal.png
	RoughnessMap = "", -- HachaMeteorito_roughness.png
	MetalnessMap = "", -- HachaMeteorito_metalness.png
}

local DATOS = {
	arma = "Hacha de Meteorito",
	archivo = "hacha_meteorito.fbx",
	rareza = "Poco común",
	colorBorde = "#4AFF8B",
	triangulos = 2036,
	trisMax = 3000,
	texturas = {
		color = "texturas/HachaMeteorito_color.png",
		normal = "texturas/HachaMeteorito_normal.png",
		roughness = "texturas/HachaMeteorito_roughness.png",
		metalness = "texturas/HachaMeteorito_metalness.png",
		emision = "texturas/HachaMeteorito_emision.png",
	},
	piezaRaiz = "HachaMeteorito_Cabeza",
	piezas = {
		{
			nombre = "HachaMeteorito_Cabeza",
			rol = "tex",
			triangulos = 484,
			centro = { -0.0, 0.0, 0.0 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HachaMeteorito_Roca",
			rol = "tex",
			triangulos = 480,
			centro = { 0.0828, 0.2754, 0.0115 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HachaMeteorito_Neon_01",
			rol = "neon",
			triangulos = 256,
			centro = { 0.028, 0.2515, 0.0 },
			Material = "Neon",
			Color = "#3DF2FF",
		},
		{
			nombre = "HachaMeteorito_Mango",
			rol = "tex",
			triangulos = 212,
			centro = { 0.12, -0.74, 0.0 },
			SurfaceAppearance = true,
		},
		{
			nombre = "HachaMeteorito_Anillos",
			rol = "tex",
			triangulos = 604,
			centro = { 0.12, -1.03, 0.0 },
			SurfaceAppearance = true,
		},
	},
	agarres = {
		Handle = {
			posicion = { 0.12, -1.47, 0.0 },
			ejeY = { -0.0, 1.0, 0.0 },
		},
		Handle_Frontal = {
			posicion = { 0.12, -0.92, 0.0 },
			ejeY = { -0.0, 1.0, 0.0 },
		},
	},
	notas = {  },
}

local modelo = Selection:Get()[1]
assert(modelo and modelo:IsA("Model"), "Selecciona el modelo importado de hacha_meteorito.fbx")

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
