--!strict
--[[
	Monta la bestia cósmica «bestia_dragon» importada en Studio.
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
	["cuerpo"] = Vector3.new(-0.005, 5.48, -0.048),
	["cuello"] = Vector3.new(-0.01, 7.742, 4.01),
	["cabeza"] = Vector3.new(-0.004, 11.389, 6.405),
	["ojos_neon"] = Vector3.new(-0.004, 10.491, 6.79),
	["mandibula"] = Vector3.new(-0.005, 9.121, 6.726),
	["aliento_neon"] = Vector3.new(-0.062, 9.27, 8.329),
	["cola"] = Vector3.new(0.004, 4.106, -6.027),
	["pata_del_izq"] = Vector3.new(-2.113, 2.723, 2.361),
	["pata_tras_izq"] = Vector3.new(-2.114, 2.627, -2.024),
	["pata_del_der"] = Vector3.new(2.11, 2.729, 2.359),
	["pata_tras_der"] = Vector3.new(2.102, 2.637, -2.026),
	["ala_sup_izq"] = Vector3.new(-4.962, 10.088, -0.97),
	["ala_inf_izq"] = Vector3.new(-4.633, 6.815, -3.333),
	["ala_sup_der"] = Vector3.new(4.959, 10.077, -0.988),
	["ala_inf_der"] = Vector3.new(4.614, 6.799, -3.355),
}

-- pieza = { padre, pivote }
local ARTICULACIONES: { [string]: { padre: string, pivote: Vector3 } } = {
	["cuello"] = { padre = "cuerpo", pivote = Vector3.new(-0.004, 6.073, 2.973) },
	["cabeza"] = { padre = "cuello", pivote = Vector3.new(-0.004, 9.934, 5.559) },
	["mandibula"] = { padre = "cabeza", pivote = Vector3.new(-0.004, 9.645, 5.781) },
	["ojos_neon"] = { padre = "cabeza", pivote = Vector3.new(-0.004, 10.224, 6.224) },
	["aliento_neon"] = { padre = "cabeza", pivote = Vector3.new(-0.004, 9.5, 6.963) },
	["cola"] = { padre = "cuerpo", pivote = Vector3.new(-0.004, 4.818, -3.087) },
	["pata_del_izq"] = { padre = "cuerpo", pivote = Vector3.new(-1.77, 4.528, 1.864) },
	["pata_tras_izq"] = { padre = "cuerpo", pivote = Vector3.new(-1.77, 4.335, -2.274) },
	["pata_del_der"] = { padre = "cuerpo", pivote = Vector3.new(1.762, 4.528, 1.864) },
	["pata_tras_der"] = { padre = "cuerpo", pivote = Vector3.new(1.762, 4.335, -2.274) },
	["ala_sup_izq"] = { padre = "cuerpo", pivote = Vector3.new(-1.476, 6.749, 1.199) },
	["ala_inf_izq"] = { padre = "cuerpo", pivote = Vector3.new(-1.476, 5.783, -1.313) },
	["ala_sup_der"] = { padre = "cuerpo", pivote = Vector3.new(1.467, 6.749, 1.199) },
	["ala_inf_der"] = { padre = "cuerpo", pivote = Vector3.new(1.467, 5.783, -1.313) },
}

-- Piezas que brillan: material y color.
local NEON: { [string]: Color3 } = {
	["ojos_neon"] = Color3.fromRGB(57, 255, 20),
	["aliento_neon"] = Color3.fromRGB(57, 255, 20),
}

local CRISTAL: { [string]: number } = {

}

local MONTURAS: { { nombre: string, posicion: Vector3, mirando: Vector3 } } = {
	{ nombre = "asiento_lomo", posicion = Vector3.new(-0.004, 7.338, 0.239), mirando = Vector3.new(0.0, 0.0, 1.0) },
	{ nombre = "asiento_cuello", posicion = Vector3.new(-0.004, 8.928, 3.749), mirando = Vector3.new(0.0, 0.0, 1.0) },
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
modelo.Name = "bestia_dragon"
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

modelo:SetAttribute("Bestia", "bestia_dragon")
modelo:SetAttribute("Asientos", #MONTURAS)
if seleccion ~= modelo and #seleccion:GetDescendants() == 0 then
	seleccion:Destroy()
end
game:GetService("Selection"):Set({ modelo })
print(`Bestia bestia_dragon montada: {#MONTURAS} asientos`)
