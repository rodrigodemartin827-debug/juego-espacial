--[[
	Monta el monstruo importado como un personaje R6 de verdad. Pégalo en la barra de comandos de Studio
	(View → Command Bar) con el modelo importado SELECCIONADO y pulsa Enter.

	Lo genera modelos/herramientas/monstruo.py: no lo edites a mano (los números salen del modelo de Blender).

	Qué hace:
	  1. Busca las MeshPart Torso, Head, "Left Arm", "Right Arm", "Left Leg", "Right Leg" y Ojos dentro de la selección.
	  2. Crea HumanoidRootPart (invisible) y un Humanoid con RigType R6.
	  3. Crea los Motor6D de R6 (RootJoint, Neck, Left/Right Shoulder, Left/Right Hip) con su pivote en las
	     articulaciones de este monstruo y con la misma ORIENTACIÓN que los de un R6 estándar: así las animaciones
	     normales de R6 (y las de animaciones/) giran cada pieza sobre el eje correcto.
	  4. Suelda los Ojos a la cabeza y les pone material Neon.
	  5. Ajusta HipHeight porque las piernas miden más que las de un R6 normal.
]]

local ARTICULACIONES = {
	--ARTICULACIONES--
}
local CENTROS = {
	--CENTROS--
}
local ALTURA_CADERA = --ALTURA--
local COLOR_OJOS = Color3.fromHex("--COLOR_OJOS--")

-- Orientación de cada Motor6D en un R6 estándar (la que esperan las animaciones).
local GIRO = {
	RootJoint = CFrame.Angles(-math.pi / 2, 0, math.pi),
	Neck = CFrame.Angles(-math.pi / 2, 0, math.pi),
	["Right Shoulder"] = CFrame.Angles(0, math.pi / 2, 0),
	["Left Shoulder"] = CFrame.Angles(0, -math.pi / 2, 0),
	["Right Hip"] = CFrame.Angles(0, math.pi / 2, 0),
	["Left Hip"] = CFrame.Angles(0, -math.pi / 2, 0),
}
local PIEZA_DE = {
	Neck = "Head",
	["Right Shoulder"] = "Right Arm",
	["Left Shoulder"] = "Left Arm",
	["Right Hip"] = "Right Leg",
	["Left Hip"] = "Left Leg",
}

local seleccion = game:GetService("Selection"):Get()[1]
assert(seleccion, "Selecciona el modelo importado antes de ejecutar el script")

local piezas = {}
for _, d in seleccion:GetDescendants() do
	if d:IsA("BasePart") and CENTROS[d.Name] then
		piezas[d.Name] = d
	end
end
for nombre in CENTROS do
	assert(piezas[nombre], `Falta la pieza {nombre} en el modelo importado`)
end

local modelo = Instance.new("Model")
modelo.Name = "Monstruo"
modelo.Parent = seleccion.Parent

-- Desplazamiento entre el modelo de Blender (origen en el suelo) y donde ha quedado en Studio.
local torso = piezas.Torso
local base = torso.Position - CENTROS.Torso

for nombre, parte in piezas do
	parte.Anchored = false
	parte.CanCollide = nombre == "Torso" or nombre == "Head"
	parte.Massless = false
	parte.CFrame = CFrame.new(base + CENTROS[nombre]) -- sin giros: así las cuentas de abajo son exactas
	parte.Parent = modelo
end

local raiz = Instance.new("Part")
raiz.Name = "HumanoidRootPart"
raiz.Size = Vector3.new(2, 2, 1)
raiz.Transparency = 1
raiz.CanCollide = false
raiz.CFrame = CFrame.new(base + ARTICULACIONES.RootJoint)
raiz.Parent = modelo
modelo.PrimaryPart = raiz

local function motor(nombre: string, parte0: BasePart, parte1: BasePart)
	local pivote = CFrame.new(base + ARTICULACIONES[nombre]) * GIRO[nombre]
	local m = Instance.new("Motor6D")
	m.Name = nombre
	m.Part0 = parte0
	m.Part1 = parte1
	m.C0 = parte0.CFrame:Inverse() * pivote
	m.C1 = parte1.CFrame:Inverse() * pivote
	m.Parent = parte0
end

motor("RootJoint", raiz, torso)
for articulacion, pieza in PIEZA_DE do
	motor(articulacion, torso, piezas[pieza])
end

local ojos = piezas.Ojos
ojos.Material = Enum.Material.Neon
ojos.Color = COLOR_OJOS
ojos.CanCollide = false
ojos.Massless = true
local soldadura = Instance.new("WeldConstraint")
soldadura.Part0 = piezas.Head
soldadura.Part1 = ojos
soldadura.Parent = ojos

local humanoide = Instance.new("Humanoid")
humanoide.RigType = Enum.HumanoidRigType.R6
humanoide.HipHeight = ALTURA_CADERA - 2 -- un R6 normal tiene las piernas de 2 studs
humanoide.Parent = modelo

seleccion:Destroy()
game:GetService("Selection"):Set({ modelo })
print(`[Monstruo] R6 montado: {#modelo:GetDescendants()} instancias. HipHeight = {humanoide.HipHeight}`)
