--!strict
--[[
	Monta la pistola de portales importada como una Tool. Pégalo en la barra de comandos de Studio
	(View → Command Bar) con el modelo importado SELECCIONADO y pulsa Enter.

	Lo genera modelos/herramientas/pistola_portales.py: no lo edites a mano (los números salen de Blender).

	Qué hace:
	  1. Busca las MeshPart de la pistola dentro de la selección.
	  2. Corrige el giro de importación (GIRO_IMPORTACION) y coloca cada pieza en su sitio respecto al cuerpo.
	  3. Crea la Tool «PistolaPortales»: el cuerpo pasa a llamarse Handle y el resto se suelda a él.
	     Las piezas que giran (rueda o anillos) llevan un Weld llamado «Giro» con el atributo C0Base: el juego las
	     hace girar con  weld.C0 = weld:GetAttribute("C0Base") * CFrame.Angles(0, 0, angulo).
	  4. Pone Neon a lo que brilla, Glass al cristal y una SurfaceAppearance (si se dan los IDs) a lo que lleva textura.
	  5. Crea los Attachment «Boca» (de ahí sale el portal, LookVector = hacia delante) y «Agarre» en el Handle, y
	     pone Tool.Grip para que «Agarre» caiga en el RightGripAttachment del brazo derecho R6.
]]

-- Si al montarla el cañón mira hacia atrás o las piezas salen descolocadas, el importador no ha girado las mallas:
-- cambia esto por CFrame.identity y vuelve a ejecutar sobre un modelo recién importado.
local GIRO_IMPORTACION = CFrame.Angles(0, math.pi, 0)

-- IDs (rbxassetid://...) de las texturas del atlas, después de subirlas. Vacío = no se crea SurfaceAppearance.
local IDS_TEXTURA = {
	ColorMap = "",
	NormalMap = "",
	MetalnessMap = "",
	RoughnessMap = "",
}

local NOMBRE_TOOL = "PistolaPortales"
local CUERPO = "Chatarra_Cuerpo"

-- Centro de la caja de cada malla (studs, ejes de Roblox, en el marco del modelo: cañón hacia -Z).
local CENTROS: { [string]: Vector3 } = {
	["Chatarra_Cuerpo"] = Vector3.new(-0.07, 0.3962, -0.4068),
	["Chatarra_Rueda"] = Vector3.new(0.3451, 0.66, 0.1),
	["Chatarra_Deposito"] = Vector3.new(0.0, 0.38, -0.74),
	["Chatarra_Combustible"] = Vector3.new(0.0, 0.3875, -0.72),
	["Chatarra_Luces"] = Vector3.new(0.0374, 0.875, -0.4287),
}
local ANCLAJES: { [string]: Vector3 } = {
	Boca = Vector3.new(0.0, 0.78, -1.66),
	Agarre = Vector3.new(0.0, 0.05, 0.12),
}
local GIROS: { [string]: { pivote: Vector3, eje: string } } = {
	["Chatarra_Rueda"] = { pivote = Vector3.new(0.33, 0.66, 0.1), eje = "X" },
}
local NEON: { [string]: Color3 } = {
	["Chatarra_Combustible"] = Color3.fromHex("#7DFF3A"),
	["Chatarra_Luces"] = Color3.fromHex("#7DFF3A"),
}
local CRISTAL: { [string]: { color: Color3, transparencia: number } } = {
	["Chatarra_Deposito"] = { color = Color3.fromHex("#B9E6D2"), transparencia = 0.55 },
}
local SOLDAR_A: { [string]: string } = {

}
local TEXTURIZADAS = { "Chatarra_Cuerpo", "Chatarra_Rueda" }

local Selection = game:GetService("Selection")
local seleccion = Selection:Get()[1]
assert(seleccion, "Selecciona el modelo importado antes de ejecutar el script")

local partes: { [string]: MeshPart } = {}
for nombre in CENTROS do
	local p = seleccion:FindFirstChild(nombre, true)
	assert(p and p:IsA("MeshPart"), "No encuentro la MeshPart " .. nombre)
	partes[nombre] = p :: MeshPart
end

-- Marco del modelo: el cuerpo está en base * CFrame.new(centro) * GIRO_IMPORTACION.
local cuerpo = partes[CUERPO]
local base = CFrame.new(cuerpo.Position) * CFrame.new(-CENTROS[CUERPO])

local tool = Instance.new("Tool")
tool.Name = NOMBRE_TOOL
tool.RequiresHandle = true
tool.CanBeDropped = false

for nombre, p in partes do
	p.CFrame = base * CFrame.new(CENTROS[nombre]) * GIRO_IMPORTACION
	p.Anchored = false
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = nombre == CUERPO
	p.Massless = nombre ~= CUERPO
	p.CastShadow = NEON[nombre] == nil
	local neon = NEON[nombre]
	local cristal = CRISTAL[nombre]
	if neon then
		p.Material = Enum.Material.Neon
		p.Color = neon
	elseif cristal then
		p.Material = Enum.Material.Glass
		p.Color = cristal.color
		p.Transparency = cristal.transparencia
	end
	p.Name = if nombre == CUERPO then "Handle" else nombre
	p.Parent = tool
end

if IDS_TEXTURA.ColorMap ~= "" then
	for _, nombre in TEXTURIZADAS do
		local sa = Instance.new("SurfaceAppearance")
		sa.ColorMap = IDS_TEXTURA.ColorMap
		sa.NormalMap = IDS_TEXTURA.NormalMap
		sa.MetalnessMap = IDS_TEXTURA.MetalnessMap
		sa.RoughnessMap = IDS_TEXTURA.RoughnessMap
		sa.Parent = partes[nombre]
	end
end

-- Piezas que giran: Weld con C0 animable. El eje local Z del pivote es el eje de giro.
local ORIENTACION_EJE: { [string]: CFrame } = {
	X = CFrame.Angles(0, math.pi / 2, 0),
	Y = CFrame.Angles(-math.pi / 2, 0, 0),
	Z = CFrame.identity,
}
for nombre, g in GIROS do
	local p = partes[nombre]
	local pivote = base * CFrame.new(g.pivote) * ORIENTACION_EJE[g.eje]
	local w = Instance.new("Weld")
	w.Name = "Giro"
	w.Part0 = cuerpo
	w.Part1 = p
	w.C0 = cuerpo.CFrame:Inverse() * pivote
	w.C1 = p.CFrame:Inverse() * pivote
	w:SetAttribute("C0Base", w.C0)
	w.Parent = p
end

-- El resto, soldado al Handle (o a la pieza que gira con él).
for nombre, p in partes do
	if nombre ~= CUERPO and GIROS[nombre] == nil then
		local w = Instance.new("WeldConstraint")
		local destino = SOLDAR_A[nombre]
		w.Part0 = if destino then partes[destino] else cuerpo
		w.Part1 = p
		w.Parent = p
	end
end

-- Anclajes en el Handle (si el importador trajo los Empty como algo, se quitan para no duplicarlos).
for nombre, pos in ANCLAJES do
	local viejo = seleccion:FindFirstChild(nombre, true)
	if viejo and not viejo:IsA("MeshPart") then
		viejo:Destroy()
	end
	local a = Instance.new("Attachment")
	a.Name = nombre
	a.CFrame = cuerpo.CFrame:Inverse() * (base * CFrame.new(pos))
	a.Parent = cuerpo
end
tool.Grip = cuerpo.CFrame:Inverse() * (base * CFrame.new(ANCLAJES.Agarre))

tool.Parent = seleccion.Parent
seleccion:Destroy()
Selection:Set({ tool })
print(("[pistola] %s montada: %d piezas"):format(NOMBRE_TOOL, #tool:GetChildren()))
