--!strict
--[[
	Monta la bestia cósmica «bestia_medusa» importada en Studio.
	Pégalo en la barra de comandos (View → Command Bar) con el modelo importado SELECCIONADO y pulsa Enter.

	Lo genera modelos/herramientas/planeta_monstruo/lib.py: no lo edites a mano (los números salen de Blender).

	Qué hace:
	  1. Junta las piezas rígidas en un Model con «nucleo» como PrimaryPart.
	  2. Une cada pieza móvil a su padre con un Motor6D cuyo pivote es la articulación (para animarla).
	  3. Suelda las piezas que no se mueven (las que brillan pasan a material Neon).
	  4. Crea los asientos (Seat) de los puntos de montura, soldados a la raíz.
	  5. Añade AnimationController + Animator (las bestias no son Humanoid) y deja atributos para el juego.

	Las posiciones están en studs, relativas al origen del modelo, en los ejes del archivo FBX. Si Studio gira el
	modelo al importarlo (o lo giras tú), el script lo detecta solo.
]]

local RAIZ = "nucleo"

-- Centro de cada pieza (así se sabe dónde ha quedado el origen del modelo al importarlo).
local CENTROS: { [string]: Vector3 } = {
	["campana_cristal"] = Vector3.new(-0.001, 15.056, 0.003),
	["patrones_neon"] = Vector3.new(-0.002, 14.838, 0.008),
	["nucleo"] = Vector3.new(-0.005, 13.556, 0.125),
	["brazos_orales"] = Vector3.new(-0.121, 8.305, 0.08),
	["tentaculos_a_neon"] = Vector3.new(-0.122, 6.272, 0.201),
	["tentaculos_b_neon"] = Vector3.new(-0.036, 6.331, -0.026),
}

-- pieza = { padre, pivote }
local ARTICULACIONES: { [string]: { padre: string, pivote: Vector3 } } = {
	["patrones_neon"] = { padre = "campana_cristal", pivote = Vector3.new(-0.002, 16.027, 0.008) },
	["campana_cristal"] = { padre = "nucleo", pivote = Vector3.new(-0.002, 15.532, 0.008) },
	["brazos_orales"] = { padre = "nucleo", pivote = Vector3.new(-0.002, 11.474, 0.008) },
	["tentaculos_a_neon"] = { padre = "campana_cristal", pivote = Vector3.new(-0.002, 12.563, 0.008) },
	["tentaculos_b_neon"] = { padre = "campana_cristal", pivote = Vector3.new(-0.002, 12.563, 0.008) },
}

-- Piezas que brillan: material y color.
local NEON: { [string]: Color3 } = {
	["patrones_neon"] = Color3.fromRGB(192, 77, 255),
	["tentaculos_a_neon"] = Color3.fromRGB(192, 77, 255),
	["tentaculos_b_neon"] = Color3.fromRGB(192, 77, 255),
}

local CRISTAL: { [string]: number } = {
	["campana_cristal"] = 0.4,
}

local MONTURAS: { { nombre: string, posicion: Vector3, mirando: Vector3 } } = {
	{ nombre = "asiento_1", posicion = Vector3.new(-0.002, 14.006, 1.796), mirando = Vector3.new(0.0, 0.0, 1.0) },
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
modelo.Name = "bestia_medusa"
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

modelo:SetAttribute("Bestia", "bestia_medusa")
modelo:SetAttribute("Asientos", #MONTURAS)
if seleccion ~= modelo and #seleccion:GetDescendants() == 0 then
	seleccion:Destroy()
end
game:GetService("Selection"):Set({ modelo })
print(`Bestia bestia_medusa montada: {#MONTURAS} asientos`)
