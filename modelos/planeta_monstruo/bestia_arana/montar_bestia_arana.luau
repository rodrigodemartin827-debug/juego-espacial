--!strict
--[[
	Monta la bestia cósmica «bestia_arana» importada en Studio.
	Pégalo en la barra de comandos (View → Command Bar) con el modelo importado SELECCIONADO y pulsa Enter.

	Lo genera modelos/herramientas/planeta_monstruo/lib.py: no lo edites a mano (los números salen de Blender).

	Qué hace:
	  1. Junta las piezas rígidas en un Model con «cuerpo» como PrimaryPart.
	  2. Une cada pieza móvil a su padre con un Motor6D cuyo pivote es la articulación (para animarla).
	  3. Suelda las piezas que no se mueven (las que brillan pasan a material Neon).
	  4. Crea los asientos (Seat) de los puntos de montura, soldados a la raíz.
	  5. Añade AnimationController + Animator (las bestias no son Humanoid) y deja atributos para el juego.

	Las posiciones están en studs, relativas al origen del modelo, en los ejes del FBX tal como se importa.
]]

local RAIZ = "cuerpo"

-- Centro de cada pieza (así se sabe dónde ha quedado el origen del modelo al importarlo).
local CENTROS: { [string]: Vector3 } = {
	["cuerpo"] = Vector3.new(-0.002, 3.06, 2.027),
	["ojos_neon"] = Vector3.new(-0.001, 4.183, 2.972),
	["abdomen"] = Vector3.new(-0.005, 3.842, -3.282),
	["pata_1_izq"] = Vector3.new(-2.134, 3.878, 4.541),
	["pata_2_izq"] = Vector3.new(-3.908, 4.011, 2.641),
	["pata_3_izq"] = Vector3.new(-4.007, 4.01, 0.248),
	["pata_4_izq"] = Vector3.new(-2.516, 3.884, -1.676),
	["pata_1_der"] = Vector3.new(2.137, 3.884, 4.531),
	["pata_2_der"] = Vector3.new(3.897, 4.024, 2.638),
	["pata_3_der"] = Vector3.new(4.0, 4.008, 0.251),
	["pata_4_der"] = Vector3.new(2.527, 3.887, -1.681),
}

-- pieza = { padre, pivote }
local ARTICULACIONES: { [string]: { padre: string, pivote: Vector3 } } = {
	["ojos_neon"] = { padre = "cuerpo", pivote = Vector3.new(-0.001, 4.121, 3.047) },
	["abdomen"] = { padre = "cuerpo", pivote = Vector3.new(-0.001, 3.599, 0.058) },
	["pata_1_izq"] = { padre = "cuerpo", pivote = Vector3.new(-0.815, 3.39, 2.497) },
	["pata_2_izq"] = { padre = "cuerpo", pivote = Vector3.new(-1.425, 3.39, 1.835) },
	["pata_3_izq"] = { padre = "cuerpo", pivote = Vector3.new(-1.462, 3.39, 0.88) },
	["pata_4_izq"] = { padre = "cuerpo", pivote = Vector3.new(-0.947, 3.39, 0.21) },
	["pata_1_der"] = { padre = "cuerpo", pivote = Vector3.new(0.812, 3.39, 2.497) },
	["pata_2_der"] = { padre = "cuerpo", pivote = Vector3.new(1.422, 3.39, 1.835) },
	["pata_3_der"] = { padre = "cuerpo", pivote = Vector3.new(1.459, 3.39, 0.88) },
	["pata_4_der"] = { padre = "cuerpo", pivote = Vector3.new(0.944, 3.39, 0.21) },
}

-- Piezas que brillan: material y color.
local NEON: { [string]: Color3 } = {
	["ojos_neon"] = Color3.fromRGB(255, 42, 42),
}

local CRISTAL: { [string]: number } = {

}

local MONTURAS: { { nombre: string, posicion: Vector3, mirando: Vector3 } } = {
	{ nombre = "asiento_1", posicion = Vector3.new(-0.001, 6.713, -1.195), mirando = Vector3.new(0.0, 0.0, 1.0) },
	{ nombre = "asiento_2", posicion = Vector3.new(-0.001, 6.817, -3.413), mirando = Vector3.new(0.0, 0.0, 1.0) },
}

local BAHIA_CARGA: { posicion: Vector3, tamano: Vector3 }? = nil

local seleccion = game:GetService("Selection"):Get()[1]
assert(seleccion, "Selecciona el modelo importado antes de ejecutar el script")

local piezas: { [string]: BasePart } = {}
for _, d in seleccion:GetDescendants() do
	if d:IsA("BasePart") and CENTROS[d.Name] then
		piezas[d.Name] = d
	end
end
for nombre in CENTROS do
	assert(piezas[nombre], `Falta la pieza {nombre} en el modelo importado`)
end

local raiz = piezas[RAIZ]
-- Marco del origen del modelo: todo lo demás se coloca respecto a él, así da igual dónde y cómo esté girado.
local origen = raiz.CFrame * CFrame.new(-CENTROS[RAIZ])

local modelo = Instance.new("Model")
modelo.Name = "bestia_arana"
modelo.Parent = seleccion.Parent

for nombre, parte in piezas do
	parte.Anchored = nombre == RAIZ
	parte.CanCollide = nombre == RAIZ
	parte.Massless = nombre ~= RAIZ
	parte.Parent = modelo
	if NEON[nombre] then
		parte.Material = Enum.Material.Neon
		parte.Color = NEON[nombre]
	end
	if CRISTAL[nombre] then
		parte.Material = Enum.Material.Glass
		parte.Transparency = CRISTAL[nombre]
	end
end
modelo.PrimaryPart = raiz

for nombre, parte in piezas do
	if nombre == RAIZ then
		continue
	end
	local art = ARTICULACIONES[nombre]
	if art then
		local padre = piezas[art.padre]
		local marco = origen * CFrame.new(art.pivote)
		local motor = Instance.new("Motor6D")
		motor.Name = nombre
		motor.Part0 = padre
		motor.Part1 = parte
		motor.C0 = padre.CFrame:Inverse() * marco
		motor.C1 = parte.CFrame:Inverse() * marco
		motor.Parent = padre
	else
		local soldadura = Instance.new("WeldConstraint")
		soldadura.Part0 = raiz
		soldadura.Part1 = parte
		soldadura.Parent = parte
	end
end

local asientos = Instance.new("Folder")
asientos.Name = "Monturas"
asientos.Parent = modelo
for i, m in MONTURAS do
	local asiento = Instance.new("Seat")
	asiento.Name = m.nombre
	asiento.Size = Vector3.new(2, 0.4, 2)
	asiento.Transparency = 1
	asiento.CanCollide = false
	asiento.Massless = true
	local pos = origen * m.posicion
	asiento.CFrame = CFrame.lookAt(pos, pos + origen:VectorToWorldSpace(m.mirando))
	asiento:SetAttribute("Orden", i)
	asiento.Parent = asientos
	local soldadura = Instance.new("WeldConstraint")
	soldadura.Part0 = raiz
	soldadura.Part1 = asiento
	soldadura.Parent = asiento
end

if BAHIA_CARGA then
	local bahia = Instance.new("Part")
	bahia.Name = "BahiaCarga"
	bahia.Size = BAHIA_CARGA.tamano
	bahia.CFrame = origen * CFrame.new(BAHIA_CARGA.posicion)
	bahia.Transparency = 1
	bahia.CanCollide = false
	bahia.Massless = true
	bahia.Parent = modelo
	local soldadura = Instance.new("WeldConstraint")
	soldadura.Part0 = raiz
	soldadura.Part1 = bahia
	soldadura.Parent = bahia
end

local controlador = Instance.new("AnimationController")
controlador.Parent = modelo
Instance.new("Animator").Parent = controlador

modelo:SetAttribute("Bestia", "bestia_arana")
modelo:SetAttribute("Asientos", #MONTURAS)
if seleccion ~= modelo and #seleccion:GetDescendants() == 0 then
	seleccion:Destroy()
end
game:GetService("Selection"):Set({ modelo })
print(`Bestia bestia_arana montada: {#MONTURAS} asientos`)
