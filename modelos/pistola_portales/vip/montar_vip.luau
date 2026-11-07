--!strict
--[[
	Monta la pistola de portales importada como una Tool. Pégalo en la barra de comandos de Studio
	(View → Command Bar) con el modelo importado SELECCIONADO y pulsa Enter.

	Lo genera modelos/herramientas/pistola_portales.py: no lo edites a mano (los números salen de Blender).

	Qué hace:
	  1. Busca las MeshPart de la pistola dentro de la selección.
	  2. Corrige el giro de importación (GIRO_IMPORTACION) y coloca cada pieza en su sitio respecto al cuerpo.
	  3. Crea la Tool «PistolaPortalesVIP»: el cuerpo pasa a llamarse Handle y el resto se suelda a él.
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

local NOMBRE_TOOL = "PistolaPortalesVIP"
local CUERPO = "VIP_Cuerpo"

-- Centro de la caja de cada malla (studs, ejes de Roblox, en el marco del modelo: cañón hacia -Z).
local CENTROS: { [string]: Vector3 } = {
	["VIP_Cuerpo"] = Vector3.new(0.0, 0.3682, -0.3989),
	["VIP_Nucleo"] = Vector3.new(0.0, 0.755, -0.09),
	["VIP_Luces"] = Vector3.new(0.0, 0.4421, -0.425),
	["VIP_Anillo1"] = Vector3.new(-0.02, 0.8, -0.92),
	["VIP_Anillo1_Luz"] = Vector3.new(0.0, 0.8, -0.967),
	["VIP_Anillo2"] = Vector3.new(0.0088, 0.7797, -1.15),
	["VIP_Anillo2_Luz"] = Vector3.new(0.0, 0.8, -1.197),
	["VIP_Anillo3"] = Vector3.new(0.0199, 0.8141, -1.37),
	["VIP_Anillo3_Luz"] = Vector3.new(0.0, 0.8, -1.417),
}
local ANCLAJES: { [string]: Vector3 } = {
	Boca = Vector3.new(0.0, 0.8, -1.62),
	Agarre = Vector3.new(0.0, 0.05, 0.16),
}
local GIROS: { [string]: { pivote: Vector3, eje: string } } = {
	["VIP_Anillo1"] = { pivote = Vector3.new(0.0, 0.8, -0.92), eje = "Z" },
	["VIP_Anillo2"] = { pivote = Vector3.new(0.0, 0.8, -1.15), eje = "Z" },
	["VIP_Anillo3"] = { pivote = Vector3.new(0.0, 0.8, -1.37), eje = "Z" },
}
local NEON: { [string]: Color3 } = {
	["VIP_Nucleo"] = Color3.fromHex("#A64BFF"),
	["VIP_Luces"] = Color3.fromHex("#3FF0FF"),
	["VIP_Anillo1_Luz"] = Color3.fromHex("#3FF0FF"),
	["VIP_Anillo2_Luz"] = Color3.fromHex("#3FF0FF"),
	["VIP_Anillo3_Luz"] = Color3.fromHex("#3FF0FF"),
}
local CRISTAL: { [string]: { color: Color3, transparencia: number } } = {

}
local SOLDAR_A: { [string]: string } = {
	["VIP_Anillo1_Luz"] = "VIP_Anillo1",
	["VIP_Anillo2_Luz"] = "VIP_Anillo2",
	["VIP_Anillo3_Luz"] = "VIP_Anillo3",
}
local TEXTURIZADAS = { "VIP_Cuerpo", "VIP_Anillo1", "VIP_Anillo2", "VIP_Anillo3" }

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
