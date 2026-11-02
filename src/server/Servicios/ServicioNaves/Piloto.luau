--!strict
--[[
	Piloto (Naves): sube y baja al jugador de su nave.

	Mientras pilota, el personaje del jugador va soldado a la nave en el puesto de piloto, invisible (la cabina
	ya es de cristal y el cuerpo de un avatar no cabe en un caza), sin colisiones físicas, sin poder moverse por
	su cuenta y protegido con un ForceField invisible para que las habilidades de combate de a pie no lo dañen
	mientras vuela. Al bajar, todo vuelve a como estaba.

	Este módulo solo cambia al personaje; qué pasa con la nave lo decide ServicioNaves.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Naves.Config)
local GruposColision = require(script.Parent.GruposColision)

export type Guardado = {
	Personaje: Model,
	Humanoid: Humanoid,
	Raiz: BasePart,
	Transparencias: { [Instance]: number }, -- lo que valía Transparency antes de ocultarlo
	Soldadura: WeldConstraint,
	Escudo: ForceField,
	DistanciaNombre: Enum.HumanoidDisplayDistanceType,
}

local Piloto = {}

--[[
	Sube al personaje a la nave (en el Attachment "Piloto" de su parte principal). Devuelve lo necesario para
	devolverlo a la normalidad, o nil si el personaje no está listo (sin Humanoid o sin HumanoidRootPart).
]]
function Piloto.Subir(personaje: Model, nave: Model): Guardado?
	local humanoid = personaje:FindFirstChildOfClass("Humanoid")
	local raiz = personaje:FindFirstChild("HumanoidRootPart")
	local principal = nave.PrimaryPart
	if humanoid == nil or raiz == nil or not raiz:IsA("BasePart") or principal == nil then
		return nil
	end
	local puesto = principal:FindFirstChild("Piloto") :: Attachment?
	if puesto == nil then
		return nil
	end

	-- Invisible: se guarda la transparencia de cada parte para devolverla luego.
	local transparencias: { [Instance]: number } = {}
	for _, parte in personaje:GetDescendants() do
		if parte:IsA("BasePart") then
			transparencias[parte] = parte.Transparency
			parte.Transparency = 1
		elseif parte:IsA("Decal") then
			transparencias[parte] = parte.Transparency
			parte.Transparency = 1
		end
	end

	local escudo = Instance.new("ForceField")
	escudo.Visible = false
	escudo.Parent = personaje

	GruposColision.Aplicar(personaje, Config.GrupoNaves)
	-- El combate a pie mira este atributo: quien pilota no usa habilidades ni puede ser objetivo de ellas.
	personaje:SetAttribute(Config.AtributoPilotando, true)

	local distanciaNombre = humanoid.DisplayDistanceType
	humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	humanoid.PlatformStand = true -- no responde a los controles de a pie ni se anima

	raiz.CFrame = puesto.WorldCFrame
	raiz.AssemblyLinearVelocity = Vector3.zero
	local soldadura = Instance.new("WeldConstraint")
	soldadura.Name = "SoldaduraPiloto"
	soldadura.Part0 = principal
	soldadura.Part1 = raiz
	soldadura.Parent = raiz

	return {
		Personaje = personaje,
		Humanoid = humanoid,
		Raiz = raiz,
		Transparencias = transparencias,
		Soldadura = soldadura,
		Escudo = escudo,
		DistanciaNombre = distanciaNombre,
	}
end

--[[
	Baja al piloto: lo suelta de la nave, le devuelve el aspecto y lo coloca en `destino`.
	Es seguro llamarla aunque el personaje ya no exista (el jugador se fue o murió).
]]
function Piloto.Bajar(guardado: Guardado, destino: CFrame?)
	local personaje = guardado.Personaje
	guardado.Soldadura:Destroy()
	guardado.Escudo:Destroy()

	if personaje.Parent == nil then
		return -- el personaje ya no está en el juego
	end
	for parte, transparencia in guardado.Transparencias do
		if parte.Parent ~= nil then
			(parte :: any).Transparency = transparencia
		end
	end
	GruposColision.Aplicar(personaje, "Default")
	personaje:SetAttribute(Config.AtributoPilotando, nil)
	guardado.Humanoid.DisplayDistanceType = guardado.DistanciaNombre
	guardado.Humanoid.PlatformStand = false

	if destino then
		guardado.Raiz.AssemblyLinearVelocity = Vector3.zero
		guardado.Raiz.AssemblyAngularVelocity = Vector3.zero
		personaje:PivotTo(destino)
	end
end

return Piloto
