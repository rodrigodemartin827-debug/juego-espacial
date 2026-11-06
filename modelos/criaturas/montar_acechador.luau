--[[
	Monta la criatura Acechador importada en Studio. Pégalo en la barra de comandos (View → Command Bar) con el modelo
	importado SELECCIONADO y pulsa Enter.

	Lo genera modelos/herramientas/criaturas.py: no lo edites a mano (los números salen del modelo de Blender).

	Qué hace:
	  1. Junta las piezas en un Model con la raíz (el cuerpo) como PrimaryPart.
	  2. Une cada pieza móvil (patas, orejas, mandíbulas, cola) al cuerpo con un Motor6D cuyo pivote es la
	     articulación, así se pueden animar con el Animation Editor. Los ojos van soldados.
	  3. Añade AnimationController + Animator (las criaturas no son Humanoid).
	  4. La deja ESCANEABLE: etiqueta "Escaneable" y atributo EspecieId (ver Exploracion/Datos/Especies).
]]

local ESPECIE = "Criatura_AcechadorAbismo"
local RAIZ = "Acechador_Cuerpo"
local PIVOTES = {
	["Acechador_Pata1"] = Vector3.new(-0.619, 1.423, -0.472),
	["Acechador_Pata2"] = Vector3.new(0.621, 1.423, -0.472),
	["Acechador_Pata3"] = Vector3.new(-0.619, 1.423, 0.328),
	["Acechador_Pata4"] = Vector3.new(0.621, 1.423, 0.328),
	["Acechador_Pata5"] = Vector3.new(-0.619, 1.423, 1.128),
	["Acechador_Pata6"] = Vector3.new(0.621, 1.423, 1.128),
	["Acechador_MandibulaIzq"] = Vector3.new(-0.299, 1.273, -1.522),
	["Acechador_MandibulaDer"] = Vector3.new(0.301, 1.273, -1.522),
}
local CENTROS = {
	["Acechador_Cuerpo"] = Vector3.new(-0.007, 1.993, 0.597),
	["Acechador_Pata1"] = Vector3.new(-1.644, 1.358, -0.81),
	["Acechador_Pata2"] = Vector3.new(1.647, 1.347, -0.8),
	["Acechador_Pata3"] = Vector3.new(-1.648, 1.371, 0.329),
	["Acechador_Pata4"] = Vector3.new(1.641, 1.371, 0.324),
	["Acechador_Pata5"] = Vector3.new(-1.64, 1.351, 1.43),
	["Acechador_Pata6"] = Vector3.new(1.633, 1.358, 1.414),
	["Acechador_MandibulaIzq"] = Vector3.new(-0.39, 1.151, -2.093),
	["Acechador_MandibulaDer"] = Vector3.new(0.388, 1.154, -2.088),
	["Acechador_Ojos"] = Vector3.new(0.001, 1.798, -1.507),
}
local SOLDADAS = { "Acechador_Ojos" }
local OJOS_NEON = true

local CollectionService = game:GetService("CollectionService")
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
modelo.Name = "Acechador"
modelo.Parent = seleccion.Parent

local raiz = piezas[RAIZ]
local base = raiz.Position - CENTROS[RAIZ] -- dónde ha quedado el origen del modelo de Blender

for nombre, parte in piezas do
	parte.Anchored = nombre == RAIZ -- el script de la criatura decide si la suelta (física) o la mueve a mano
	parte.CanCollide = nombre == RAIZ
	parte.Massless = nombre ~= RAIZ
	parte.CFrame = CFrame.new(base + CENTROS[nombre])
	parte.Parent = modelo
end
modelo.PrimaryPart = raiz

for nombre, pivote in PIVOTES do
	local parte = piezas[nombre]
	local marco = CFrame.new(base + pivote)
	local m = Instance.new("Motor6D")
	m.Name = string.gsub(nombre, "^[^_]*_", "") -- "Pata1", "OrejaIzq"...: lo que buscan las animaciones
	m.Part0 = raiz
	m.Part1 = parte
	m.C0 = raiz.CFrame:Inverse() * marco
	m.C1 = parte.CFrame:Inverse() * marco
	m.Parent = raiz
end

for _, nombre in SOLDADAS do
	local parte = piezas[nombre]
	local soldadura = Instance.new("WeldConstraint")
	soldadura.Part0 = raiz
	soldadura.Part1 = parte
	soldadura.Parent = parte
	if OJOS_NEON then
		parte.Material = Enum.Material.Neon
	else
		parte.Material = Enum.Material.SmoothPlastic
		parte.Reflectance = 0.25
	end
end

local controlador = Instance.new("AnimationController")
controlador.Parent = modelo
Instance.new("Animator").Parent = controlador

CollectionService:AddTag(modelo, "Escaneable")
modelo:SetAttribute("EspecieId", ESPECIE)

seleccion:Destroy()
game:GetService("Selection"):Set({ modelo })
print(`[Criatura] {modelo.Name} montada y escaneable como {ESPECIE}`)
