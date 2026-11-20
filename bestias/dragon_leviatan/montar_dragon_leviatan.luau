--[[
	Monta el Dragón Leviatán importado en Studio. Pégalo en la barra de comandos (View → Command Bar) con el
	modelo importado SELECCIONADO y pulsa Enter.

	Lo genera modelos/herramientas/dragon_leviatan.py: no lo edites a mano (los números salen de Blender).

	1. Junta las 25 piezas en un Model con el Torso como PrimaryPart.
	2. Une cada pieza a su padre con un Motor6D cuyo pivote es la articulación (cadena: Torso → Cuello_Base →
	   Cuello_Medio → Cuello_Superior → Cabeza → Mandibula; Torso → Ala_*_Hombro → Antebrazo → Mano; etc.).
	3. Convierte los 5 puntos de montaje en Attachments dentro de su pieza (y borra los cubos).
	4. Añade AnimationController + Animator (el dragón no es Humanoid).
]]

local RAIZ = "Torso"
local PIVOTES = {
	["Torso"] = Vector3.new(-0.0, 9.600000381469727, 0.5),
	["Cuello_Base"] = Vector3.new(-0.0, 11.199999809265137, -8.399999618530273),
	["Cuello_Medio"] = Vector3.new(-0.0, 14.600000381469727, -12.0),
	["Cuello_Superior"] = Vector3.new(-0.0, 14.399999618530273, -16.5),
	["Cabeza"] = Vector3.new(-0.0, 11.0, -19.600000381469727),
	["Mandibula"] = Vector3.new(-0.0, 8.75, -21.700000762939453),
	["Ala_Izq_Hombro"] = Vector3.new(-4.0, 13.399999618530273, -4.599999904632568),
	["Ala_Izq_Antebrazo"] = Vector3.new(-9.800000190734863, 18.600000381469727, -1.0),
	["Ala_Izq_Mano"] = Vector3.new(-14.600000381469727, 23.600000381469727, -1.600000023841858),
	["Ala_Der_Hombro"] = Vector3.new(4.0, 13.399999618530273, -4.599999904632568),
	["Ala_Der_Antebrazo"] = Vector3.new(9.800000190734863, 18.600000381469727, -1.0),
	["Ala_Der_Mano"] = Vector3.new(14.600000381469727, 23.600000381469727, -1.600000023841858),
	["Pata_Del_Izq_Muslo"] = Vector3.new(-5.199999809265137, 8.199999809265137, -6.199999809265137),
	["Pata_Del_Izq_Garra"] = Vector3.new(-7.699999809265137, 4.5, -4.199999809265137),
	["Pata_Del_Der_Muslo"] = Vector3.new(5.199999809265137, 8.199999809265137, -6.199999809265137),
	["Pata_Del_Der_Garra"] = Vector3.new(7.699999809265137, 4.5, -4.199999809265137),
	["Pata_Tras_Izq_Muslo"] = Vector3.new(-4.900000095367432, 10.100000381469727, 7.0),
	["Pata_Tras_Izq_Tibia"] = Vector3.new(-7.400000095367432, 6.599999904632568, 3.5999999046325684),
	["Pata_Tras_Der_Muslo"] = Vector3.new(4.900000095367432, 10.100000381469727, 7.0),
	["Pata_Tras_Der_Tibia"] = Vector3.new(7.400000095367432, 6.599999904632568, 3.5999999046325684),
	["Cola_Base"] = Vector3.new(-0.0, 10.600000381469727, 9.199999809265137),
	["Cola_Media"] = Vector3.new(-0.5, 8.600000381469727, 16.200000762939453),
	["Cola_Punta"] = Vector3.new(-1.899999976158142, 6.599999904632568, 23.0),
	["Cresta_Dorsal"] = Vector3.new(-0.0, 14.817999839782715, 1.312999963760376),
	["Cornamenta"] = Vector3.new(-0.0, 13.600000381469727, -21.600000381469727),
}
local CENTROS = {
	["Torso"] = Vector3.new(-0.003, 10.147, -0.23),
	["Cuello_Base"] = Vector3.new(-0.483, 11.961, -9.891),
	["Cuello_Medio"] = Vector3.new(-0.004, 14.65, -14.309),
	["Cuello_Superior"] = Vector3.new(0.009, 12.984, -18.415),
	["Cabeza"] = Vector3.new(-0.005, 10.234, -24.795),
	["Mandibula"] = Vector3.new(0.001, 7.418, -24.685),
	["Ala_Izq_Hombro"] = Vector3.new(-6.907, 15.854, -2.913),
	["Ala_Izq_Antebrazo"] = Vector3.new(-9.879, 16.769, 6.751),
	["Ala_Izq_Mano"] = Vector3.new(-19.638, 22.222, 7.195),
	["Ala_Der_Hombro"] = Vector3.new(6.882, 15.872, -2.914),
	["Ala_Der_Antebrazo"] = Vector3.new(9.879, 16.77, 6.751),
	["Ala_Der_Mano"] = Vector3.new(19.674, 22.234, 7.652),
	["Pata_Del_Izq_Muslo"] = Vector3.new(-6.743, 6.726, -5.427),
	["Pata_Del_Izq_Garra"] = Vector3.new(-7.891, 2.669, -7.507),
	["Pata_Del_Der_Muslo"] = Vector3.new(6.738, 6.73, -5.413),
	["Pata_Del_Der_Garra"] = Vector3.new(7.886, 2.666, -7.51),
	["Pata_Tras_Izq_Muslo"] = Vector3.new(-6.295, 8.987, 5.421),
	["Pata_Tras_Izq_Tibia"] = Vector3.new(-7.173, 3.799, 6.349),
	["Pata_Tras_Der_Muslo"] = Vector3.new(6.303, 8.992, 5.421),
	["Pata_Tras_Der_Tibia"] = Vector3.new(7.17, 3.798, 6.352),
	["Cola_Base"] = Vector3.new(-0.654, 10.013, 12.764),
	["Cola_Media"] = Vector3.new(-0.949, 7.948, 19.464),
	["Cola_Punta"] = Vector3.new(-2.803, 7.75, 28.078),
	["Cresta_Dorsal"] = Vector3.new(-0.0, 16.489, 1.313),
	["Cornamenta"] = Vector3.new(-0.0, 14.354, -20.85),
}
local PADRES = {
	["Cuello_Base"] = "Torso",
	["Cuello_Medio"] = "Cuello_Base",
	["Cuello_Superior"] = "Cuello_Medio",
	["Cabeza"] = "Cuello_Superior",
	["Mandibula"] = "Cabeza",
	["Ala_Izq_Hombro"] = "Torso",
	["Ala_Izq_Antebrazo"] = "Ala_Izq_Hombro",
	["Ala_Izq_Mano"] = "Ala_Izq_Antebrazo",
	["Ala_Der_Hombro"] = "Torso",
	["Ala_Der_Antebrazo"] = "Ala_Der_Hombro",
	["Ala_Der_Mano"] = "Ala_Der_Antebrazo",
	["Pata_Del_Izq_Muslo"] = "Torso",
	["Pata_Del_Izq_Garra"] = "Pata_Del_Izq_Muslo",
	["Pata_Del_Der_Muslo"] = "Torso",
	["Pata_Del_Der_Garra"] = "Pata_Del_Der_Muslo",
	["Pata_Tras_Izq_Muslo"] = "Torso",
	["Pata_Tras_Izq_Tibia"] = "Pata_Tras_Izq_Muslo",
	["Pata_Tras_Der_Muslo"] = "Torso",
	["Pata_Tras_Der_Tibia"] = "Pata_Tras_Der_Muslo",
	["Cola_Base"] = "Torso",
	["Cola_Media"] = "Cola_Base",
	["Cola_Punta"] = "Cola_Media",
	["Cresta_Dorsal"] = "Torso",
	["Cornamenta"] = "Cabeza",
}
local MONTAJES = {
	["Montura_Cria_Piloto"] = { pieza = "Cuello_Medio", pos = Vector3.new(-0.0, 17.170000076293945, -15.199999809265137) },
	["Montura_Cria_Pasajero"] = { pieza = "Torso", pos = Vector3.new(-0.0, 15.829000473022461, -2.4000000953674316) },
	["Agarre_Cuello_Izq"] = { pieza = "Cuello_Medio", pos = Vector3.new(-2.4149999618530273, 14.616000175476074, -14.199999809265137) },
	["Agarre_Cuello_Der"] = { pieza = "Cuello_Medio", pos = Vector3.new(2.4149999618530273, 14.616000175476074, -14.199999809265137) },
	["Punto_Aliento"] = { pieza = "Cabeza", pos = Vector3.new(-0.0, 8.449999809265137, -27.200000762939453) },
}

local seleccion = game:GetService("Selection"):Get()[1]
assert(seleccion, "Selecciona el modelo importado antes de ejecutar el script")

local piezas = {}
local cubos = {}
for _, d in seleccion:GetDescendants() do
	if d:IsA("BasePart") then
		if CENTROS[d.Name] then
			piezas[d.Name] = d
		elseif MONTAJES[d.Name] then
			cubos[d.Name] = d
		end
	end
end
for nombre in CENTROS do
	assert(piezas[nombre], `Falta la pieza {nombre} en el modelo importado`)
end

local modelo = Instance.new("Model")
modelo.Name = "DragonLeviatan"
modelo.Parent = seleccion.Parent

local raiz = piezas[RAIZ]
local base = raiz.Position - CENTROS[RAIZ] -- dónde ha quedado el origen del modelo de Blender

for nombre, parte in piezas do
	parte.Anchored = nombre == RAIZ
	parte.CanCollide = nombre == RAIZ
	parte.Massless = nombre ~= RAIZ
	parte.CFrame = CFrame.new(base + CENTROS[nombre])
	parte.Parent = modelo
end
modelo.PrimaryPart = raiz

for nombre, padre in PADRES do
	local parte = piezas[nombre]
	local p0 = piezas[padre]
	local marco = CFrame.new(base + PIVOTES[nombre])
	local m = Instance.new("Motor6D")
	m.Name = nombre
	m.Part0 = p0
	m.Part1 = parte
	m.C0 = p0.CFrame:Inverse() * marco
	m.C1 = parte.CFrame:Inverse() * marco
	m.Parent = p0
end

for nombre, d in MONTAJES do
	local a = Instance.new("Attachment")
	a.Name = nombre
	a.WorldPosition = base + d.pos
	a.Parent = piezas[d.pieza]
	a.WorldPosition = base + d.pos
	if cubos[nombre] then
		cubos[nombre]:Destroy()
	end
end

local controlador = Instance.new("AnimationController")
controlador.Parent = modelo
Instance.new("Animator").Parent = controlador

seleccion:Destroy()
game:GetService("Selection"):Set({ modelo })
print(`[Dragón] {modelo.Name} montado: 25 piezas, 24 Motor6D, 5 puntos de montaje`)
