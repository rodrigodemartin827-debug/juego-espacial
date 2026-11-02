--!strict
--[[
	Hangar: un hangar abierto con una plataforma de despegue, creado por código.

	Tiene:
	  - una losa con un círculo de aterrizaje luminoso y un soporte bajo la nave,
	  - tres muros (el cuarto lado está abierto hacia la zona de pruebas), vigas, luces y un cartel,
	  - una NAVE DE EXHIBICIÓN posada en la plataforma, y
	  - una consola con un ProximityPrompt "Despegar".

	Al usar la consola, ServicioNaves.Despegar sube al jugador a su nave (con las mejoras de SUS datos) y la
	nave de exhibición se retira mientras la plataforma está ocupada; vuelve a aparecer cuando la nave aterriza
	o es destruida. Sin techo: la nave sale volando hacia arriba.
]]

local Modelo = require(script.Parent.ServicioNaves.Modelo)
local ServicioNaves = require(script.Parent.ServicioNaves)

local Hangar = {}

local COLOR_METAL = Color3.fromRGB(46, 50, 62)
local COLOR_METAL_CLARO = Color3.fromRGB(78, 84, 100)
local COLOR_NEON = Color3.fromRGB(77, 240, 255)

local function crearParte(
	padre: Instance,
	nombre: string,
	tamano: Vector3,
	posicion: Vector3,
	color: Color3,
	material: Enum.Material
): Part
	local parte = Instance.new("Part")
	parte.Name = nombre
	parte.Size = tamano
	parte.Position = posicion
	parte.Color = color
	parte.Material = material
	parte.Anchored = true
	parte.TopSurface = Enum.SurfaceType.Smooth
	parte.BottomSurface = Enum.SurfaceType.Smooth
	parte.Parent = padre
	return parte
end

-- Disco plano (un cilindro tumbado) de `diametro` studs y `grosor` de alto.
local function crearDisco(
	padre: Instance,
	nombre: string,
	diametro: number,
	grosor: number,
	posicion: Vector3,
	color: Color3,
	material: Enum.Material
): Part
	local disco = crearParte(padre, nombre, Vector3.new(grosor, diametro, diametro), posicion, color, material)
	disco.Shape = Enum.PartType.Cylinder
	disco.CFrame = CFrame.new(posicion) * CFrame.Angles(0, 0, math.pi / 2)
	return disco
end

local function crearCartel(padre: Instance, texto: string, posicion: Vector3, ancho: number, alto: number)
	local ancla = crearParte(padre, "Cartel", Vector3.one, posicion, COLOR_METAL, Enum.Material.SmoothPlastic)
	ancla.Transparency = 1
	ancla.CanCollide = false
	ancla.CanQuery = false

	local gui = Instance.new("BillboardGui")
	gui.Size = UDim2.fromOffset(ancho, alto)
	gui.MaxDistance = 220
	gui.Parent = ancla
	local etiqueta = Instance.new("TextLabel")
	etiqueta.Size = UDim2.fromScale(1, 1)
	etiqueta.BackgroundColor3 = Color3.fromRGB(12, 14, 26)
	etiqueta.BackgroundTransparency = 0.25
	etiqueta.TextColor3 = Color3.fromRGB(235, 240, 255)
	etiqueta.TextScaled = true
	etiqueta.Font = Enum.Font.GothamMedium
	etiqueta.Text = texto
	etiqueta.Parent = gui
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, 8)
	esquina.Parent = etiqueta
end

--[[
	Construye el hangar dentro de `padre`, centrado en `centro` (la altura del suelo es la Y de `centro`).
	La nave despega mirando hacia -Z. Devuelve la plataforma para ServicioNaves.Despegar.
]]
function Hangar.Crear(padre: Instance, centro: Vector3): ServicioNaves.Plataforma
	local carpeta = Instance.new("Folder")
	carpeta.Name = "Hangar"
	carpeta.Parent = padre
	local cx, cy, cz = centro.X, centro.Y, centro.Z

	-- Losa y círculo de aterrizaje (anillo luminoso con un disco oscuro encima).
	crearParte(
		carpeta,
		"Losa",
		Vector3.new(46, 0.6, 46),
		Vector3.new(cx, cy + 0.3, cz),
		COLOR_METAL,
		Enum.Material.DiamondPlate
	)
	crearDisco(carpeta, "AnilloNeon", 28, 0.15, Vector3.new(cx, cy + 0.65, cz), COLOR_NEON, Enum.Material.Neon)
	crearDisco(carpeta, "DiscoCentral", 26, 0.15, Vector3.new(cx, cy + 0.72, cz), COLOR_METAL, Enum.Material.Metal)

	-- Soporte bajo la nave: dos raíles justo debajo de su vientre.
	for _, lado in { -1, 1 } do
		crearParte(
			carpeta,
			"Soporte",
			Vector3.new(1, 1.7, 9),
			Vector3.new(cx + 1.4 * lado, cy + 0.6 + 0.85, cz + 0.5),
			COLOR_METAL_CLARO,
			Enum.Material.Metal
		)
	end

	-- Tres muros (la cara de -Z queda abierta) y vigas de borde.
	local ALTO = 20
	crearParte(
		carpeta,
		"MuroFondo",
		Vector3.new(46, ALTO, 1.5),
		Vector3.new(cx, cy + ALTO / 2, cz + 23),
		COLOR_METAL,
		Enum.Material.Concrete
	)
	for _, lado in { -1, 1 } do
		crearParte(
			carpeta,
			"MuroLateral",
			Vector3.new(1.5, ALTO, 46),
			Vector3.new(cx + 23 * lado, cy + ALTO / 2, cz),
			COLOR_METAL,
			Enum.Material.Concrete
		)
		crearParte(
			carpeta,
			"Viga",
			Vector3.new(2.2, 1.4, 48),
			Vector3.new(cx + 23 * lado, cy + ALTO + 0.7, cz),
			COLOR_METAL_CLARO,
			Enum.Material.Metal
		)
		-- Franja luminosa a lo largo del muro.
		crearParte(
			carpeta,
			"FranjaNeon",
			Vector3.new(0.3, 0.6, 40),
			Vector3.new(cx + 22.1 * lado, cy + 14, cz),
			COLOR_NEON,
			Enum.Material.Neon
		)
	end
	crearParte(
		carpeta,
		"VigaFondo",
		Vector3.new(48, 1.4, 2.2),
		Vector3.new(cx, cy + ALTO + 0.7, cz + 23),
		COLOR_METAL_CLARO,
		Enum.Material.Metal
	)
	crearParte(
		carpeta,
		"FranjaFondo",
		Vector3.new(40, 0.6, 0.3),
		Vector3.new(cx, cy + 14, cz + 22.1),
		COLOR_NEON,
		Enum.Material.Neon
	)

	-- Postes de luz en las esquinas abiertas.
	for _, lado in { -1, 1 } do
		crearParte(
			carpeta,
			"Poste",
			Vector3.new(1, 7, 1),
			Vector3.new(cx + 22 * lado, cy + 3.5, cz - 22),
			COLOR_METAL_CLARO,
			Enum.Material.Metal
		)
		local lampara = crearParte(
			carpeta,
			"Lampara",
			Vector3.new(1.6, 0.8, 1.6),
			Vector3.new(cx + 22 * lado, cy + 7.4, cz - 22),
			COLOR_NEON,
			Enum.Material.Neon
		)
		local luz = Instance.new("PointLight")
		luz.Color = COLOR_NEON
		luz.Range = 34
		luz.Brightness = 2.4
		luz.Parent = lampara
	end

	crearCartel(carpeta, "HANGAR · Consola: Despegar", Vector3.new(cx, cy + 25, cz + 18), 320, 44)

	-- La plataforma. La nave mira hacia -Z.
	local plataforma: ServicioNaves.Plataforma = {
		Marco = CFrame.new(cx, cy + 0.82, cz),
		Ocupada = false,
		AlCambiar = nil,
	}

	-- Nave de exhibición.
	local exhibicion = Modelo.CrearExhibicion("Ninguno")
	exhibicion:PivotTo(plataforma.Marco * CFrame.new(0, Modelo.ALTURA_POSADA, 0))
	exhibicion.Parent = carpeta

	-- Consola con el ProximityPrompt.
	local consolaPos = Vector3.new(cx - 17, cy + 1.7, cz - 15)
	local consola =
		crearParte(carpeta, "Consola", Vector3.new(3.4, 3.4, 2.2), consolaPos, COLOR_METAL_CLARO, Enum.Material.Metal)
	local pantalla = crearParte(
		carpeta,
		"Pantalla",
		Vector3.new(2.8, 1.5, 0.15),
		consolaPos + Vector3.new(0, 0.5, 1.15),
		COLOR_NEON,
		Enum.Material.Neon
	)
	pantalla.CanCollide = false

	local aviso = Instance.new("ProximityPrompt")
	aviso.ActionText = "Despegar"
	aviso.ObjectText = "Nave de caza"
	aviso.HoldDuration = 0.5
	aviso.MaxActivationDistance = 14
	aviso.RequiresLineOfSight = false
	aviso.Parent = consola
	aviso.Triggered:Connect(function(jugador)
		ServicioNaves.Despegar(jugador, plataforma)
	end)

	-- Mientras la nave está en el aire, la de exhibición no está y la consola avisa.
	plataforma.AlCambiar = function(ocupada: boolean)
		exhibicion.Parent = if ocupada then nil else carpeta
		aviso.Enabled = not ocupada
		pantalla.Color = if ocupada then Color3.fromRGB(255, 160, 60) else COLOR_NEON
	end

	-- Instrucciones al lado de la consola.
	crearCartel(
		carpeta,
		"VUELO · W/S acelerar · A/D lateral · Espacio/Ctrl subir/bajar · Ratón orientar · Clic disparar · Shift turbo · F aterrizar",
		Vector3.new(cx - 17, cy + 6.2, cz - 15),
		560,
		40
	)

	return plataforma
end

return Hangar
