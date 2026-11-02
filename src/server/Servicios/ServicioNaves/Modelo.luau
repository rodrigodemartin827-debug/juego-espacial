--!strict
--[[
	Modelo (Naves): construye por código el modelo 3D de una nave. No hay nada que montar a mano en Studio.

	La nave mira hacia -Z (como todo en Roblox): su proa es el lado de la LookVector de la parte principal.
	Es una nave de caza esbelta, hecha solo con formas básicas:

	  - Fuselaje (parte principal), morro y punta sensora
	  - Cabina de cristal
	  - Alas en flecha con un cañón láser en cada punta y luces de posición
	  - Dos propulsores con tobera brillante, y una aleta vertical
	  - Franjas de neón del color del bando

	Los Attachments marcan dónde ocurren las cosas (y el motor de efectos los usa como anclas por nombre, así que
	ninguna parte puede llamarse igual que uno de ellos):
	  Ejes            el centro, donde se atan las fuerzas del vuelo
	  Piloto          donde va sentado el piloto
	  CanonIzq/Der    las bocas de los cañones (de ahí salen los disparos)
	  MotorIzq/Der    las toberas (de ahí sale la estela)

	Todas las partes van soldadas a la parte principal, sin colisión física ni masa, así que la nave pesa lo
	que pese el fuselaje.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Naves.Config)
local GruposColision = require(script.Parent.GruposColision)

local Modelo = {}

-- Colores por bando: casco, detalles y neón.
local COLORES: { [string]: { Casco: Color3, Oscuro: Color3, Neon: Color3 } } = {
	Heroes = {
		Casco = Color3.fromRGB(226, 233, 246),
		Oscuro = Color3.fromRGB(86, 100, 130),
		Neon = Color3.fromRGB(77, 240, 255),
	},
	Villanos = {
		Casco = Color3.fromRGB(58, 56, 68),
		Oscuro = Color3.fromRGB(30, 28, 38),
		Neon = Color3.fromRGB(255, 77, 94),
	},
	Ninguno = {
		Casco = Color3.fromRGB(168, 176, 158),
		Oscuro = Color3.fromRGB(88, 94, 84),
		Neon = Color3.fromRGB(182, 255, 107),
	},
}

-- Altura de la nave sobre el suelo cuando está posada (para colocarla en la plataforma).
Modelo.ALTURA_POSADA = 2.4

-- Crea una parte soldada a la principal. `relativo` es su posición y giro respecto a ella.
local function crearParte(
	modelo: Model,
	principal: BasePart?,
	nombre: string,
	forma: Enum.PartType,
	tamano: Vector3,
	relativo: CFrame,
	color: Color3,
	material: Enum.Material
): Part
	local parte = Instance.new("Part")
	parte.Name = nombre
	parte.Shape = forma
	parte.Size = tamano
	parte.Color = color
	parte.Material = material
	parte.TopSurface = Enum.SurfaceType.Smooth
	parte.BottomSurface = Enum.SurfaceType.Smooth
	parte.CanCollide = false
	parte.CanTouch = false
	parte.Anchored = true -- mientras se construye; al final se sueltan
	parte.Massless = principal ~= nil
	parte.CFrame = relativo
	parte.Parent = modelo
	if principal then
		local soldadura = Instance.new("WeldConstraint")
		soldadura.Part0 = principal
		soldadura.Part1 = parte
		soldadura.Parent = parte
	end
	return parte
end

-- Un cilindro tumbado a lo largo del eje Z (el cilindro de Roblox tiene su eje en X).
local function cilindroZ(largo: number, diametro: number, posicion: Vector3): (Vector3, CFrame)
	return Vector3.new(largo, diametro, diametro), CFrame.new(posicion) * CFrame.Angles(0, math.pi / 2, 0)
end

local function crearAdjunto(parte: BasePart, nombre: string, posicion: Vector3): Attachment
	local adjunto = Instance.new("Attachment")
	adjunto.Name = nombre
	adjunto.Position = posicion
	adjunto.Parent = parte
	return adjunto
end

--[[
	Crea una nave con los colores del bando, en el origen y anclada. Devuelve el modelo (con PrimaryPart).
	El que la use la mueve con `PivotTo` y la suelta con `Modelo.Soltar`.
]]
function Modelo.Crear(bando: string, nombrePiloto: string, ocultarA: Player?): Model
	GruposColision.Preparar() -- sin los grupos registrados, asignar un CollisionGroup daría error
	local colores = COLORES[bando] or COLORES.Ninguno
	local modelo = Instance.new("Model")
	modelo.Name = `Nave de {nombrePiloto}`

	-- Fuselaje: la parte principal.
	local fuselaje = crearParte(
		modelo,
		nil,
		"Fuselaje",
		Enum.PartType.Block,
		Vector3.new(2.6, 1.8, 10),
		CFrame.identity,
		colores.Casco,
		Enum.Material.Metal
	)
	modelo.PrimaryPart = fuselaje
	fuselaje.Massless = false

	local function parte(
		nombre: string,
		forma: Enum.PartType,
		tamano: Vector3,
		relativo: CFrame,
		color: Color3,
		material: Enum.Material
	): Part
		return crearParte(modelo, fuselaje, nombre, forma, tamano, relativo, color, material)
	end

	-- Morro y punta sensora.
	local tamanoMorro, marcoMorro = cilindroZ(3.4, 1.8, Vector3.new(0, 0, -6.6))
	parte("Morro", Enum.PartType.Cylinder, tamanoMorro, marcoMorro, colores.Casco, Enum.Material.Metal)
	parte(
		"Punta",
		Enum.PartType.Ball,
		Vector3.new(1.8, 1.8, 1.8),
		CFrame.new(0, 0, -8.3),
		colores.Neon,
		Enum.Material.Neon
	)

	-- Cabina de cristal: una esfera achatada (malla esférica escalada dentro de un bloque).
	local cabina = parte(
		"Cabina",
		Enum.PartType.Block,
		Vector3.new(2.1, 1.5, 4.4),
		CFrame.new(0, 1.0, -1.4),
		Color3.fromRGB(110, 200, 255),
		Enum.Material.Glass
	)
	cabina.Transparency = 0.25
	cabina.Reflectance = 0.25
	local formaCabina = Instance.new("SpecialMesh")
	formaCabina.MeshType = Enum.MeshType.Sphere
	formaCabina.Parent = cabina

	-- Alas en flecha: la punta va hacia atrás. Y un cañón en cada punta.
	for _, lado in { -1, 1 } do
		local nombreLado = if lado < 0 then "Izq" else "Der"
		-- Ala de 6,2 de largo, centrada a 4 del eje; girada 22° para que la punta quede atrás.
		parte(
			`Ala{nombreLado}`,
			Enum.PartType.Block,
			Vector3.new(6.2, 0.28, 3.6),
			CFrame.new(4 * lado, -0.1, 1.2) * CFrame.Angles(0, math.rad(-22 * lado), 0),
			colores.Oscuro,
			Enum.Material.Metal
		)

		local tamanoCanon, marcoCanon = cilindroZ(4.4, 0.55, Vector3.new(6.9 * lado, -0.1, 0.4))
		parte(`Tubo{nombreLado}`, Enum.PartType.Cylinder, tamanoCanon, marcoCanon, colores.Oscuro, Enum.Material.Metal)
		crearAdjunto(fuselaje, `Canon{nombreLado}`, Vector3.new(6.9 * lado, -0.1, -1.9))

		-- Luz de posición en la punta del ala.
		parte(
			`Luz{nombreLado}`,
			Enum.PartType.Ball,
			Vector3.new(0.55, 0.55, 0.55),
			CFrame.new(6.95 * lado, -0.1, 2.4),
			if lado < 0 then Color3.fromRGB(255, 60, 60) else Color3.fromRGB(70, 255, 120),
			Enum.Material.Neon
		)

		-- Propulsor con su tobera brillante.
		local tamanoMotor, marcoMotor = cilindroZ(3, 1.5, Vector3.new(1.5 * lado, -0.2, 5.6))
		parte(
			`Propulsor{nombreLado}`,
			Enum.PartType.Cylinder,
			tamanoMotor,
			marcoMotor,
			colores.Oscuro,
			Enum.Material.Metal
		)
		local tamanoTobera, marcoTobera = cilindroZ(0.35, 1.2, Vector3.new(1.5 * lado, -0.2, 7.2))
		parte(`Tobera{nombreLado}`, Enum.PartType.Cylinder, tamanoTobera, marcoTobera, colores.Neon, Enum.Material.Neon)
		crearAdjunto(fuselaje, `Motor{nombreLado}`, Vector3.new(1.5 * lado, -0.2, 7.5))

		-- Franja de neón a lo largo del flanco.
		parte(
			`Franja{nombreLado}`,
			Enum.PartType.Block,
			Vector3.new(0.12, 0.2, 7),
			CFrame.new(1.33 * lado, 0.25, 0.5),
			colores.Neon,
			Enum.Material.Neon
		)
	end

	-- Aleta vertical de cola.
	parte(
		"Aleta",
		Enum.PartType.Block,
		Vector3.new(0.22, 2.4, 2.8),
		CFrame.new(0, 1.9, 4) * CFrame.Angles(math.rad(-18), 0, 0),
		colores.Oscuro,
		Enum.Material.Metal
	)

	-- Puntos de referencia.
	crearAdjunto(fuselaje, "Ejes", Vector3.zero)
	crearAdjunto(fuselaje, "Piloto", Vector3.new(0, 0.3, -0.8))

	-- Fuerzas del vuelo: el cliente del piloto las gobierna cambiando sus valores cada fotograma.
	local ejes = fuselaje:FindFirstChild("Ejes") :: Attachment
	local velocidad = Instance.new("LinearVelocity")
	velocidad.Name = "Velocidad"
	velocidad.Attachment0 = ejes
	velocidad.RelativeTo = Enum.ActuatorRelativeTo.World
	velocidad.VelocityConstraintMode = Enum.VelocityConstraintMode.Vector
	velocidad.MaxForce = math.huge
	velocidad.VectorVelocity = Vector3.zero
	velocidad.Enabled = false
	velocidad.Parent = fuselaje

	local orientacion = Instance.new("AlignOrientation")
	orientacion.Name = "Orientacion"
	orientacion.Mode = Enum.OrientationAlignmentMode.OneAttachment
	orientacion.Attachment0 = ejes
	orientacion.RigidityEnabled = false
	orientacion.MaxTorque = math.huge
	orientacion.MaxAngularVelocity = math.huge
	orientacion.Responsiveness = 40
	orientacion.CFrame = CFrame.identity
	orientacion.Enabled = false
	orientacion.Parent = fuselaje

	-- Nombre del piloto sobre la nave (el propio piloto no lo ve).
	local cartel = Instance.new("BillboardGui")
	cartel.Name = "Nombre"
	cartel.Size = UDim2.fromOffset(180, 26)
	cartel.StudsOffset = Vector3.new(0, 4.5, 0)
	cartel.MaxDistance = 400
	cartel.AlwaysOnTop = true
	cartel.Adornee = fuselaje
	if ocultarA then
		cartel.PlayerToHideFrom = ocultarA
	end
	cartel.Parent = fuselaje
	local texto = Instance.new("TextLabel")
	texto.Size = UDim2.fromScale(1, 1)
	texto.BackgroundTransparency = 1
	texto.Text = nombrePiloto
	texto.TextColor3 = colores.Neon
	texto.TextStrokeTransparency = 0.4
	texto.Font = Enum.Font.GothamBold
	texto.TextScaled = true
	texto.Parent = cartel

	modelo:SetAttribute("Bando", bando)
	GruposColision.Aplicar(modelo, Config.GrupoNaves)
	return modelo
end

--[[
	Suelta la nave: quita el anclaje de todas sus partes para que se mueva con la física (el cliente del piloto
	la simula). Antes de llamarla, el modelo debe estar ya en su sitio.
]]
function Modelo.Soltar(modelo: Model)
	for _, parte in modelo:GetDescendants() do
		if parte:IsA("BasePart") then
			parte.Anchored = false
		end
	end
end

-- Activa o desactiva las fuerzas del vuelo (apagadas cuando la nave está posada en el hangar).
function Modelo.ActivarFuerzas(modelo: Model, activar: boolean)
	local raiz = modelo.PrimaryPart
	if raiz == nil then
		return
	end
	local velocidad = raiz:FindFirstChild("Velocidad") :: LinearVelocity?
	local orientacion = raiz:FindFirstChild("Orientacion") :: AlignOrientation?
	if velocidad then
		velocidad.Enabled = activar
	end
	if orientacion then
		orientacion.Enabled = activar
	end
end

-- Decora una plataforma con una copia de exhibición de la nave (anclada, sin cartel, sin fuerzas).
function Modelo.CrearExhibicion(bando: string): Model
	local modelo = Modelo.Crear(bando, "Nave")
	modelo.Name = "NaveDeExhibicion"
	local cartel = modelo.PrimaryPart and modelo.PrimaryPart:FindFirstChild("Nombre")
	if cartel then
		cartel:Destroy()
	end
	return modelo
end

return Modelo
