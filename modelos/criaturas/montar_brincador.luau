--[[
	Monta la criatura Brincador importada en Studio. Pégalo en la barra de comandos (View → Command Bar) con el modelo
	importado SELECCIONADO y pulsa Enter.

	Lo genera modelos/herramientas/criaturas.py: no lo edites a mano (los números salen del modelo de Blender).

	Qué hace:
	  1. Junta las piezas en un Model con la raíz (el cuerpo) como PrimaryPart.
	  2. Une cada pieza móvil (patas, orejas, mandíbulas, cola) al cuerpo con un Motor6D cuyo pivote es la
	     articulación, así se pueden animar con el Animation Editor. Los ojos van soldados.
	  3. Añade AnimationController + Animator (las criaturas no son Humanoid).
	  4. La deja ESCANEABLE: etiqueta "Escaneable" y atributo EspecieId (ver Exploracion/Datos/Especies).
]]

local ESPECIE = "Criatura_BrincadorLanudo"
local RAIZ = "Brincador_Cuerpo"
local PIVOTES = {
	["Brincador_OrejaIzq"] = Vector3.new(-0.369, 2.279, -0.689),
	["Brincador_OrejaDer"] = Vector3.new(0.391, 2.279, -0.689),
	["Brincador_Pata1"] = Vector3.new(-0.489, 0.879, -0.489),
	["Brincador_Pata2"] = Vector3.new(0.511, 0.879, -0.489),
	["Brincador_Pata3"] = Vector3.new(-0.489, 0.879, 0.811),
	["Brincador_Pata4"] = Vector3.new(0.511, 0.879, 0.811),
	["Brincador_Cola"] = Vector3.new(0.011, 1.529, 1.011),
}
local CENTROS = {
	["Brincador_Cuerpo"] = Vector3.new(0.014, 1.538, -0.223),
	["Brincador_OrejaIzq"] = Vector3.new(-0.77, 2.265, -0.564),
	["Brincador_OrejaDer"] = Vector3.new(0.779, 2.273, -0.581),
	["Brincador_Pata1"] = Vector3.new(-0.531, 0.562, -0.615),
	["Brincador_Pata2"] = Vector3.new(0.553, 0.566, -0.607),
	["Brincador_Pata3"] = Vector3.new(-0.522, 0.565, 0.686),
	["Brincador_Pata4"] = Vector3.new(0.546, 0.576, 0.688),
	["Brincador_Cola"] = Vector3.new(-0.014, 1.528, 1.269),
	["Brincador_Ojos"] = Vector3.new(0.011, 2.029, -1.419),
}
local SOLDADAS = { "Brincador_Ojos" }
local OJOS_NEON = false

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
modelo.Name = "Brincador"
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
