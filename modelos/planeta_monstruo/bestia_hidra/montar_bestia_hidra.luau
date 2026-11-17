--!strict
--[[
	Monta la bestia cósmica «bestia_hidra» importada en Studio.
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
	["cuerpo"] = Vector3.new(0.021, 4.529, -0.656),
	["cola"] = Vector3.new(0.085, 3.234, -4.538),
	["pata_del_izq"] = Vector3.new(-2.802, 2.359, 1.636),
	["pata_tras_izq"] = Vector3.new(-2.802, 2.353, -1.607),
	["pata_del_der"] = Vector3.new(2.859, 2.367, 1.632),
	["pata_tras_der"] = Vector3.new(2.858, 2.364, -1.61),
	["cuello_verde"] = Vector3.new(-3.949, 7.814, 3.003),
	["cabeza_verde"] = Vector3.new(-6.436, 9.817, 4.199),
	["ojos_verde_neon"] = Vector3.new(-6.001, 9.693, 4.65),
	["mandibula_verde"] = Vector3.new(-6.391, 8.433, 4.359),
	["aliento_verde_neon"] = Vector3.new(-5.442, 8.324, 5.371),
	["cuello_violeta"] = Vector3.new(0.042, 9.252, 3.204),
	["cabeza_violeta"] = Vector3.new(0.027, 12.87, 4.527),
	["ojos_violeta_neon"] = Vector3.new(0.027, 12.883, 4.982),
	["mandibula_violeta"] = Vector3.new(0.025, 11.609, 5.088),
	["aliento_violeta_neon"] = Vector3.new(0.034, 11.9, 6.146),
	["cuello_roja"] = Vector3.new(4.105, 6.858, 3.237),
	["cabeza_roja"] = Vector3.new(6.601, 7.192, 4.782),
	["ojos_roja_neon"] = Vector3.new(6.246, 6.911, 5.125),
	["mandibula_roja"] = Vector3.new(6.764, 5.756, 4.623),
	["aliento_roja_neon"] = Vector3.new(5.836, 5.294, 5.573),
}

-- pieza = { padre, pivote }
local ARTICULACIONES: { [string]: { padre: string, pivote: Vector3 } } = {
	["cola"] = { padre = "cuerpo", pivote = Vector3.new(0.027, 3.927, -3.223) },
	["pata_del_izq"] = { padre = "cuerpo", pivote = Vector3.new(-2.338, 3.634, 1.247) },
	["pata_tras_izq"] = { padre = "cuerpo", pivote = Vector3.new(-2.338, 3.634, -1.99) },
	["pata_del_der"] = { padre = "cuerpo", pivote = Vector3.new(2.392, 3.634, 1.247) },
	["pata_tras_der"] = { padre = "cuerpo", pivote = Vector3.new(2.392, 3.634, -1.99) },
	["cuello_verde"] = { padre = "cuerpo", pivote = Vector3.new(-1.845, 5.782, 2.249) },
	["cabeza_verde"] = { padre = "cuello_verde", pivote = Vector3.new(-6.477, 9.493, 3.637) },
	["mandibula_verde"] = { padre = "cabeza_verde", pivote = Vector3.new(-6.477, 9.103, 3.868) },
	["ojos_verde_neon"] = { padre = "cabeza_verde", pivote = Vector3.new(-6.477, 9.493, 4.022) },
	["aliento_verde_neon"] = { padre = "cabeza_verde", pivote = Vector3.new(-6.477, 9.493, 4.022) },
	["cuello_violeta"] = { padre = "cuerpo", pivote = Vector3.new(0.027, 5.978, 2.326) },
	["cabeza_violeta"] = { padre = "cuello_violeta", pivote = Vector3.new(0.027, 12.423, 3.945) },
	["mandibula_violeta"] = { padre = "cabeza_violeta", pivote = Vector3.new(0.027, 12.032, 4.176) },
	["ojos_violeta_neon"] = { padre = "cabeza_violeta", pivote = Vector3.new(0.027, 12.423, 4.33) },
	["aliento_violeta_neon"] = { padre = "cabeza_violeta", pivote = Vector3.new(0.027, 12.423, 4.33) },
	["cuello_roja"] = { padre = "cuerpo", pivote = Vector3.new(1.899, 5.782, 2.249) },
	["cabeza_roja"] = { padre = "cuello_roja", pivote = Vector3.new(6.728, 6.954, 4.099) },
	["mandibula_roja"] = { padre = "cabeza_roja", pivote = Vector3.new(6.728, 6.564, 4.33) },
	["ojos_roja_neon"] = { padre = "cabeza_roja", pivote = Vector3.new(6.728, 6.954, 4.485) },
	["aliento_roja_neon"] = { padre = "cabeza_roja", pivote = Vector3.new(6.728, 6.954, 4.485) },
}

-- Piezas que brillan: material y color.
local NEON: { [string]: Color3 } = {
	["ojos_verde_neon"] = Color3.fromRGB(57, 255, 20),
	["aliento_verde_neon"] = Color3.fromRGB(57, 255, 20),
	["ojos_violeta_neon"] = Color3.fromRGB(192, 77, 255),
	["aliento_violeta_neon"] = Color3.fromRGB(192, 77, 255),
	["ojos_roja_neon"] = Color3.fromRGB(255, 42, 42),
	["aliento_roja_neon"] = Color3.fromRGB(255, 42, 42),
}

local CRISTAL: { [string]: number } = {

}

local MONTURAS: { { nombre: string, posicion: Vector3, mirando: Vector3 } } = {
	{ nombre = "asiento_1", posicion = Vector3.new(0.027, 7.147, 0.708), mirando = Vector3.new(0.0, 0.0, 1.0) },
}

local BAHIA_CARGA: { posicion: Vector3, tamano: Vector3 }? = { posicion = Vector3.new(0.027, 5.196, -1.682), tamano = Vector3.new(5.91, 1.76, 1.85) }

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
modelo.Name = "bestia_hidra"
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

modelo:SetAttribute("Bestia", "bestia_hidra")
modelo:SetAttribute("Asientos", #MONTURAS)
if seleccion ~= modelo and #seleccion:GetDescendants() == 0 then
	seleccion:Destroy()
end
game:GetService("Selection"):Set({ modelo })
print(`Bestia bestia_hidra montada: {#MONTURAS} asientos`)
