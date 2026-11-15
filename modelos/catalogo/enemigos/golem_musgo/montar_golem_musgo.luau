--!strict
--[[
	Monta el enemigo golem_musgo importado en Studio (rig de piezas rígidas con Motor6D, al estilo R6: sin huesos ni
	deformación). Pégalo en la barra de comandos (View → Command Bar) con el modelo importado SELECCIONADO y pulsa Enter.

	Lo genera modelos/catalogo/herramientas/generar.py: no lo edites a mano (los números salen del modelo de Blender).

	Qué hace:
	  1. Junta las piezas en un Model y crea un HumanoidRootPart invisible que mira al frente de la criatura.
	  2. Une cada pieza a su padre con un Motor6D cuyo pivote es la articulación (para el Animation Editor).
	     Las piezas sin articulación van soldadas a la raíz.
	  3. Humanoide (R6) o AnimationController + Animator, según el modelo.
	  4. Si tiene especie, la deja escaneable: etiqueta "Escaneable" y atributo EspecieId.

	OJO: no se ha podido probar en Studio desde la sesión que lo generó. Compruébalo antes de darlo por bueno.
]]

local NOMBRE = "golem_musgo"
local RAIZ = "torso"
local ESPECIE = "Criatura_GolemMusgo"
local HUMANOIDE = false

type Pieza = { centro: Vector3, pivote: Vector3?, padre: string?, articulacion: string? }
-- Studs, ejes de Roblox, respecto al origen del modelo (el suelo bajo la criatura).
local PIEZAS: { [string]: Pieza } = {
	["golem_musgo_torso"] = { centro = Vector3.new(-0.138, 8.616, -0.089), pivote = Vector3.new(0.0, 8.6, -0.0) },
	["golem_musgo_cabeza"] = { centro = Vector3.new(0.032, 13.488, 0.847), pivote = Vector3.new(0.0, 12.4, 0.6), padre = "golem_musgo_torso" },
	["golem_musgo_brazo_izq"] = { centro = Vector3.new(-4.929, 9.078, -0.154), pivote = Vector3.new(-4.3, 10.6, -0.0), padre = "golem_musgo_torso" },
	["golem_musgo_antebrazo_izq"] = { centro = Vector3.new(-5.724, 3.576, 0.821), pivote = Vector3.new(-5.6, 6.0, 0.3), padre = "golem_musgo_brazo_izq" },
	["golem_musgo_pierna_izq"] = { centro = Vector3.new(-1.771, 2.861, 0.119), pivote = Vector3.new(-1.6, 5.2, -0.0), padre = "golem_musgo_torso" },
	["golem_musgo_brazo_der"] = { centro = Vector3.new(5.0, 9.072, 0.124), pivote = Vector3.new(4.3, 10.6, -0.0), padre = "golem_musgo_torso" },
	["golem_musgo_antebrazo_der"] = { centro = Vector3.new(5.827, 3.609, 0.848), pivote = Vector3.new(5.6, 6.0, 0.3), padre = "golem_musgo_brazo_der" },
	["golem_musgo_pierna_der"] = { centro = Vector3.new(1.823, 2.899, 0.5), pivote = Vector3.new(1.6, 5.2, -0.0), padre = "golem_musgo_torso" },
}
-- El FBX importado mira a +Z; las articulaciones y la raíz se orientan al frente de la criatura.
local FRENTE = CFrame.Angles(0, math.pi, 0)

local CollectionService = game:GetService("CollectionService")
local seleccion = game:GetService("Selection"):Get()[1]
assert(seleccion, "Selecciona el modelo importado antes de ejecutar el script")

local piezas: { [string]: BasePart } = {}
for _, d in seleccion:GetDescendants() do
	if d:IsA("BasePart") and PIEZAS[d.Name] then
		piezas[d.Name] = d
	end
end
for nombre in PIEZAS do
	assert(piezas[nombre], `Falta la pieza {nombre} en el modelo importado`)
end

local modelo = Instance.new("Model")
modelo.Name = NOMBRE
modelo.Parent = seleccion.Parent

local raiz = piezas[RAIZ]
-- Dónde ha quedado el origen del modelo de Blender (las piezas ya vienen colocadas entre sí por el importador).
local base = raiz.Position - PIEZAS[RAIZ].centro

local hrp = Instance.new("Part")
hrp.Name = "HumanoidRootPart"
hrp.Size = Vector3.new(2, 2, 1)
hrp.Transparency = 1
hrp.CanCollide = false
hrp.Anchored = true -- suéltalo cuando el servidor tome el control de la criatura
hrp.CFrame = CFrame.new(raiz.Position) * FRENTE
hrp.Parent = modelo

for nombre, parte in piezas do
	parte.Anchored = false
	parte.CanCollide = nombre == RAIZ
	parte.Massless = nombre ~= RAIZ
	parte.Parent = modelo
end
modelo.PrimaryPart = hrp

local function unir(nombreJunta: string, padre: BasePart, hija: BasePart, marco: CFrame)
	local m = Instance.new("Motor6D")
	m.Name = nombreJunta
	m.Part0 = padre
	m.Part1 = hija
	m.C0 = padre.CFrame:ToObjectSpace(marco)
	m.C1 = hija.CFrame:ToObjectSpace(marco)
	m.Parent = padre
end

unir("RootJoint", hrp, raiz, hrp.CFrame)
for nombre, datos in PIEZAS do
	local parte = piezas[nombre]
	if nombre == RAIZ then
		continue
	end
	local padre = if datos.padre then piezas[datos.padre] else raiz
	if datos.pivote then
		local corto = string.gsub(nombre, "^" .. NOMBRE .. "_", "")
		unir(datos.articulacion or corto, padre, parte, CFrame.new(base + datos.pivote) * FRENTE)
	else
		local soldadura = Instance.new("WeldConstraint")
		soldadura.Part0 = padre
		soldadura.Part1 = parte
		soldadura.Parent = parte
	end
end

if HUMANOIDE then
	local humanoide = Instance.new("Humanoid")
	humanoide.RigType = Enum.HumanoidRigType.R6
	-- En R6 HipHeight se suma a las piernas estándar (2 studs) y a medio HumanoidRootPart (1 stud).
	humanoide.HipHeight = math.max(PIEZAS[RAIZ].centro.Y - 3, 0)
	humanoide.Parent = modelo
	Instance.new("Animator").Parent = humanoide
else
	local controlador = Instance.new("AnimationController")
	controlador.Parent = modelo
	Instance.new("Animator").Parent = controlador
end

if ESPECIE ~= "" then
	CollectionService:AddTag(modelo, "Escaneable")
	modelo:SetAttribute("EspecieId", ESPECIE)
end

seleccion:Destroy()
game:GetService("Selection"):Set({ modelo })
print(`[Rig] {NOMBRE} montado ({if HUMANOIDE then "Humanoid R6" else "AnimationController"})`)
