--!strict
--[[
	Monta la bestia cósmica «bestia_escarabajo» importada en Studio.
	Pégalo en la barra de comandos (View → Command Bar) con el modelo importado SELECCIONADO y pulsa Enter.

	Lo genera modelos/herramientas/planeta_monstruo/lib.py: no lo edites a mano (los números salen de Blender).

	Qué hace:
	  1. Junta las piezas rígidas en un Model con «cuerpo» como PrimaryPart.
	  2. Une cada pieza móvil a su padre con un Motor6D cuyo pivote es la articulación (para animarla).
	  3. Suelda las piezas que no se mueven (las que brillan pasan a material Neon).
	  4. Crea los asientos (Seat) de los puntos de montura, soldados a la raíz.
	  5. Añade AnimationController + Animator (las bestias no son Humanoid) y deja atributos para el juego.

	Las posiciones están en studs, relativas al origen del modelo, en los ejes del archivo FBX. Si Studio gira el
	modelo al importarlo (o lo giras tú), el script lo detecta solo.
]]

local RAIZ = "cuerpo"

-- Centro de cada pieza (así se sabe dónde ha quedado el origen del modelo al importarlo).
local CENTROS: { [string]: Vector3 } = {
	["cuerpo"] = Vector3.new(-0.0, 2.91, -0.866),
	["cabeza"] = Vector3.new(-0.002, 3.824, 2.298),
	["ojos_neon"] = Vector3.new(-0.0, 2.671, 2.009),
	["elitro_izq"] = Vector3.new(-0.661, 4.648, -1.992),
	["ala_izq"] = Vector3.new(-2.768, 4.827, -1.793),
	["pata_1_izq"] = Vector3.new(-2.694, 1.558, 1.364),
	["pata_2_izq"] = Vector3.new(-2.696, 1.562, -0.567),
	["pata_3_izq"] = Vector3.new(-2.696, 1.568, -2.4),
	["elitro_der"] = Vector3.new(0.656, 4.653, -1.983),
	["ala_der"] = Vector3.new(2.768, 4.827, -1.793),
	["pata_1_der"] = Vector3.new(2.693, 1.557, 1.362),
	["pata_2_der"] = Vector3.new(2.699, 1.564, -0.568),
	["pata_3_der"] = Vector3.new(2.694, 1.569, -2.395),
}

-- pieza = { padre, pivote }
local ARTICULACIONES: { [string]: { padre: string, pivote: Vector3 } } = {
	["cabeza"] = { padre = "cuerpo", pivote = Vector3.new(0.0, 2.564, 1.375) },
	["ojos_neon"] = { padre = "cabeza", pivote = Vector3.new(0.0, 2.671, 2.009) },
	["elitro_izq"] = { padre = "cuerpo", pivote = Vector3.new(-0.3, 3.794, -0.148) },
	["ala_izq"] = { padre = "cuerpo", pivote = Vector3.new(-0.599, 4.115, -0.402) },
	["pata_1_izq"] = { padre = "cuerpo", pivote = Vector3.new(-1.598, 1.815, 0.782) },
	["pata_2_izq"] = { padre = "cuerpo", pivote = Vector3.new(-1.598, 1.815, -0.571) },
	["pata_3_izq"] = { padre = "cuerpo", pivote = Vector3.new(-1.598, 1.815, -1.925) },
	["elitro_der"] = { padre = "cuerpo", pivote = Vector3.new(0.3, 3.794, -0.148) },
	["ala_der"] = { padre = "cuerpo", pivote = Vector3.new(0.599, 4.115, -0.402) },
	["pata_1_der"] = { padre = "cuerpo", pivote = Vector3.new(1.598, 1.815, 0.782) },
	["pata_2_der"] = { padre = "cuerpo", pivote = Vector3.new(1.598, 1.815, -0.571) },
	["pata_3_der"] = { padre = "cuerpo", pivote = Vector3.new(1.598, 1.815, -1.925) },
}

-- Piezas que brillan: material y color.
local NEON: { [string]: Color3 } = {
	["ojos_neon"] = Color3.fromRGB(192, 77, 255),
}

local CRISTAL: { [string]: number } = {

}

local MONTURAS: { { nombre: string, posicion: Vector3, mirando: Vector3 } } = {
	{ nombre = "asiento_1", posicion = Vector3.new(0.0, 4.384, -1.079), mirando = Vector3.new(0.0, 0.0, 1.0) },
	{ nombre = "asiento_2", posicion = Vector3.new(0.0, 4.17, -2.602), mirando = Vector3.new(0.0, 0.0, 1.0) },
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

-- Marco del origen del modelo. El importador puede girar el modelo entero sobre la vertical (en este proyecto las
-- mallas entran giradas 180°, ver MontarRegion.GIRO_IMPORTACION) y tú puedes haberlo girado después: el giro se
-- averigua comparando dónde ha quedado la pieza más alejada de la raíz con dónde estaba en Blender.
local function marcoOrigen(): CFrame
	local cRaiz = CENTROS[RAIZ]
	local lejos: string? = nil
	local distancia = 0
	for nombre, c in CENTROS do
		local d = Vector3.new(c.X - cRaiz.X, 0, c.Z - cRaiz.Z).Magnitude
		if nombre ~= RAIZ and d > distancia then
			lejos, distancia = nombre, d
		end
	end
	local giro = 0
	if lejos and distancia > 0.5 then
		local esperado = CENTROS[lejos] - cRaiz
		local real = piezas[lejos].Position - raiz.Position
		giro = math.atan2(real.X, real.Z) - math.atan2(esperado.X, esperado.Z)
	end
	return CFrame.new(raiz.Position) * CFrame.Angles(0, giro, 0) * CFrame.new(-cRaiz)
end
local origen = marcoOrigen()

local modelo = Instance.new("Model")
modelo.Name = "bestia_escarabajo"
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

modelo:SetAttribute("Bestia", "bestia_escarabajo")
modelo:SetAttribute("Asientos", #MONTURAS)
if seleccion ~= modelo and #seleccion:GetDescendants() == 0 then
	seleccion:Destroy()
end
game:GetService("Selection"):Set({ modelo })
print(`Bestia bestia_escarabajo montada: {#MONTURAS} asientos`)
