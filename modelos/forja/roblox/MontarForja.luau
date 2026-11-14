--!strict
--[[
	Monta la forja en Studio a partir de las seis piezas importadas (modelos/forja/*.fbx).

	SIN PROBAR EN STUDIO: esta sesión no tiene Studio. El director tiene que probarlo antes de darlo por bueno.

	Uso (barra de comandos de Studio, una vez):
		local Montar = require(game.ReplicatedStorage.Forja.MontarForja)
		Montar.montar(game.ReplicatedStorage.Forja.Piezas, require(game.ReplicatedStorage.Forja.forja_montaje),
			CFrame.new(0, 10, 0))

	`piezas`: carpeta con las MeshPart importadas (forja_yunque, forja_horno, forja_horno_brasas, forja_mesa,
	forja_barril, forja_estanteria, forja_suelo), cada una con su SurfaceAppearance.
	`datos`: el contenido de datos/forja_montaje.json (Rojo convierte el .json en un ModuleScript).
	`origen`: dónde va el centro del suelo, a ras de tierra.

	Los FBX ya llevan aplicado el giro de importación (180° sobre el eje vertical): aquí NO se vuelve a girar.
]]

local MontarForja = {}

-- Todo lo ajustable de los efectos (colores, tamaños, ritmos).
MontarForja.AJUSTES = {
	ColorBrasas = Color3.fromRGB(255, 120, 40),
	LuzFuego = { Color = Color3.fromRGB(255, 140, 60), Brillo = 2.5, Alcance = 26 },
	Humo = { Ritmo = 6, Vida = NumberRange.new(5, 8), Velocidad = NumberRange.new(2, 3.5), Tamano = 3.5 },
	Vapor = { Ritmo = 3, Vida = NumberRange.new(1.5, 2.5), Velocidad = NumberRange.new(0.8, 1.6), Tamano = 1.4 },
}

export type DatosPieza = { posicion: { number }, giro_y_grados: number, anclajes: { [string]: { number } } }
export type Datos = { piezas: { [string]: DatosPieza } }

local function emisor(padre: Attachment, nombre: string, ajuste: any, color: Color3)
	local e = Instance.new("ParticleEmitter")
	e.Name = nombre
	e.Rate = ajuste.Ritmo
	e.Lifetime = ajuste.Vida
	e.Speed = ajuste.Velocidad
	e.SpreadAngle = Vector2.new(12, 12)
	e.EmissionDirection = Enum.NormalId.Top
	e.Color = ColorSequence.new(color)
	e.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, ajuste.Tamano * 0.4),
		NumberSequenceKeypoint.new(1, ajuste.Tamano),
	})
	e.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.6),
		NumberSequenceKeypoint.new(1, 1),
	})
	e.LightEmission = 0
	e.Parent = padre
end

function MontarForja.montar(piezas: Instance, datos: Datos, origen: CFrame): Model
	local forja = Instance.new("Model")
	forja.Name = "Forja"
	for nombre, info in datos.piezas do
		local plantilla = piezas:FindFirstChild(nombre)
		if not plantilla or not plantilla:IsA("MeshPart") then
			warn("MontarForja: falta la MeshPart " .. nombre)
			continue
		end
		local parte = plantilla:Clone()
		local p = info.posicion
		parte.CFrame = origen * CFrame.new(p[1], p[2], p[3]) * CFrame.Angles(0, math.rad(info.giro_y_grados), 0)
		parte.Anchored = true
		for clave, a in info.anclajes do
			local att = Instance.new("Attachment")
			att.Name = clave
			att.Position = Vector3.new(a[1], a[2], a[3])
			att.Parent = parte
		end
		if nombre == "forja_horno_brasas" then
			-- Las brasas brillan: Neon (sin SurfaceAppearance, que taparía el brillo) y sin colisión.
			parte.Material = Enum.Material.Neon
			parte.Color = MontarForja.AJUSTES.ColorBrasas
			parte.CanCollide = false
			parte.CastShadow = false
		end
		parte.Parent = forja
	end
	local horno = forja:FindFirstChild("forja_horno")
	if horno then
		local luz = horno:FindFirstChild("Luz")
		if luz then
			local l = Instance.new("PointLight")
			l.Color = MontarForja.AJUSTES.LuzFuego.Color
			l.Brightness = MontarForja.AJUSTES.LuzFuego.Brillo
			l.Range = MontarForja.AJUSTES.LuzFuego.Alcance
			l.Shadows = true
			l.Parent = luz
		end
		local humo = horno:FindFirstChild("Humo")
		if humo and humo:IsA("Attachment") then
			emisor(humo, "Humo", MontarForja.AJUSTES.Humo, Color3.fromRGB(60, 58, 56))
		end
	end
	local barril = forja:FindFirstChild("forja_barril")
	local vapor = barril and barril:FindFirstChild("Vapor")
	if vapor and vapor:IsA("Attachment") then
		emisor(vapor, "Vapor", MontarForja.AJUSTES.Vapor, Color3.fromRGB(220, 225, 230))
	end
	forja.Parent = workspace
	return forja
end

return MontarForja
