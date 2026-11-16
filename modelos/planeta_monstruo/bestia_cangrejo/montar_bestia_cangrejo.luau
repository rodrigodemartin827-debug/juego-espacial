--!strict
--[[
	Monta la bestia cósmica «bestia_cangrejo» importada en Studio.
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
	["cuerpo"] = Vector3.new(0.007, 3.613, -1.724),
	["ojos_neon"] = Vector3.new(-0.0, 4.575, 0.482),
	["pinza_izq"] = Vector3.new(-4.404, 3.508, 1.947),
	["dedo_izq"] = Vector3.new(-4.898, 4.476, 3.815),
	["pata_1_izq"] = Vector3.new(-4.776, 2.389, -1.379),
	["pata_2_izq"] = Vector3.new(-4.746, 2.389, -2.593),
	["pata_3_izq"] = Vector3.new(-3.808, 2.39, -3.816),
	["pata_4_izq"] = Vector3.new(-2.177, 2.38, -4.696),
	["pinza_der"] = Vector3.new(4.602, 3.621, 2.464),
	["dedo_der"] = Vector3.new(4.762, 4.769, 4.528),
	["pata_1_der"] = Vector3.new(4.778, 2.383, -1.376),
	["pata_2_der"] = Vector3.new(4.741, 2.388, -2.597),
	["pata_3_der"] = Vector3.new(3.806, 2.388, -3.808),
	["pata_4_der"] = Vector3.new(2.186, 2.389, -4.697),
}

-- pieza = { padre, pivote }
local ARTICULACIONES: { [string]: { padre: string, pivote: Vector3 } } = {
	["ojos_neon"] = { padre = "cuerpo", pivote = Vector3.new(0.0, 4.55, 0.482) },
	["pinza_izq"] = { padre = "cuerpo", pivote = Vector3.new(-3.001, 2.952, -0.447) },
	["dedo_izq"] = { padre = "pinza_izq", pivote = Vector3.new(-5.09, 4.151, 3.037) },
	["pata_1_izq"] = { padre = "cuerpo", pivote = Vector3.new(-3.048, 2.583, -1.516) },
	["pata_2_izq"] = { padre = "cuerpo", pivote = Vector3.new(-3.024, 2.583, -2.418) },
	["pata_3_izq"] = { padre = "cuerpo", pivote = Vector3.new(-2.456, 2.583, -3.168) },
	["pata_4_izq"] = { padre = "cuerpo", pivote = Vector3.new(-1.463, 2.583, -3.704) },
	["pinza_der"] = { padre = "cuerpo", pivote = Vector3.new(3.001, 2.952, -0.447) },
	["dedo_der"] = { padre = "pinza_der", pivote = Vector3.new(5.021, 4.335, 3.528) },
	["pata_1_der"] = { padre = "cuerpo", pivote = Vector3.new(3.048, 2.583, -1.516) },
	["pata_2_der"] = { padre = "cuerpo", pivote = Vector3.new(3.024, 2.583, -2.418) },
	["pata_3_der"] = { padre = "cuerpo", pivote = Vector3.new(2.456, 2.583, -3.168) },
	["pata_4_der"] = { padre = "cuerpo", pivote = Vector3.new(1.463, 2.583, -3.704) },
}

-- Piezas que brillan: material y color.
local NEON: { [string]: Color3 } = {
	["ojos_neon"] = Color3.fromRGB(192, 77, 255),
}

local CRISTAL: { [string]: number } = {

}

local MONTURAS: { { nombre: string, posicion: Vector3, mirando: Vector3 } } = {
	{ nombre = "asiento_1", posicion = Vector3.new(0.0, 5.182, -1.413), mirando = Vector3.new(0.0, 0.0, 1.0) },
	{ nombre = "asiento_2", posicion = Vector3.new(0.0, 5.084, -2.824), mirando = Vector3.new(0.0, 0.0, 1.0) },
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
modelo.Name = "bestia_cangrejo"
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

modelo:SetAttribute("Bestia", "bestia_cangrejo")
modelo:SetAttribute("Asientos", #MONTURAS)
if seleccion ~= modelo and #seleccion:GetDescendants() == 0 then
	seleccion:Destroy()
end
game:GetService("Selection"):Set({ modelo })
print(`Bestia bestia_cangrejo montada: {#MONTURAS} asientos`)
