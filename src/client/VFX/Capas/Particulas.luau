--!strict
--[[
	Capa "Particulas": un estallido o un chorro continuo de partículas.

	Campos (todos opcionales salvo los marcados):
	  Textura       nombre en Recursos.Texturas, o un ID de contenido                         (por defecto "Chispa")
	  Color         color de paleta, hexadecimal o lista (degradado)
	  Tamano        número o lista de números (evoluciona durante la vida de la partícula)
	  Transparencia número o lista                                                             ({0, 1})
	  Vida          segundos, número o { mín, máx }
	  Velocidad     studs/s, número o { mín, máx }
	  Dispersion    ángulo de apertura en grados (0 = recto, 180 = en todas direcciones)
	  Direccion     "Arriba" | "Abajo" | "Frente" | "Esfera"                                   ("Arriba")
	  Aceleracion   { x, y, z }
	  Arrastre, Brillo, Rotacion, VelRotacion, Estirar, Orientacion ("Velocidad" para estelas)
	  Area, Forma   tamaño { x, y, z } y forma ("Box", "Sphere", "Disc", "Cylinder") del volumen de nacimiento
	  Cantidad      partículas del estallido (se reduce en móviles lentos)
	  Tasa+Duracion partículas por segundo durante Duracion segundos (en lugar de Cantidad)
	  Sigue         si es true, el emisor acompaña a su ancla mientras dura
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Recursos = require(ReplicatedStorage:WaitForChild("Shared").Combate.Datos.Recursos)
local Actores = require(script.Parent.Parent.Actores)
local Calidad = require(script.Parent.Parent.Calidad)
local Pool = require(script.Parent.Parent.Pool)
local Utiles = require(script.Parent.Parent.Utiles)

local Particulas = {}

local ORIENTACIONES: { [string]: Enum.ParticleOrientation } = {
	Camara = Enum.ParticleOrientation.FacingCamera,
	Velocidad = Enum.ParticleOrientation.VelocityParallel,
	Perpendicular = Enum.ParticleOrientation.VelocityPerpendicular,
}

local FORMAS: { [string]: Enum.ParticleEmitterShape } = {
	Box = Enum.ParticleEmitterShape.Box,
	Sphere = Enum.ParticleEmitterShape.Sphere,
	Disc = Enum.ParticleEmitterShape.Disc,
	Cylinder = Enum.ParticleEmitterShape.Cylinder,
}

-- Orientación del emisor para que su cara "superior" (por donde salen las partículas) apunte donde toca.
local function orientar(marco: CFrame, direccion: string): CFrame
	local posicion = marco.Position
	if direccion == "Frente" then
		return marco * CFrame.Angles(-math.pi / 2, 0, 0)
	elseif direccion == "Abajo" then
		return CFrame.new(posicion) * CFrame.Angles(math.pi, 0, 0)
	end
	return CFrame.new(posicion) -- "Arriba" y "Esfera"
end

function Particulas.Reproducir(capa: any, ctx: any)
	local factor = Calidad.Factor("Particulas")
	if factor <= 0 then
		return
	end

	local direccion: string = capa.Direccion or "Arriba"
	local parte, emisor = Pool.Emisor()
	parte.Size = if capa.Area then Utiles.V3(capa.Area) else Vector3.one
	parte.CFrame = orientar(Utiles.Ancla(ctx, capa.Anclaje, capa.Desplazamiento), direccion)

	local dispersion: number = if direccion == "Esfera" then 180 else (capa.Dispersion or 0)
	emisor.Texture = Recursos.Texturas[capa.Textura or "Chispa"] or capa.Textura
	emisor.Color = Utiles.Gradiente(capa.Color or "Principal", ctx.Paleta)
	emisor.Size = Utiles.Numeros(capa.Tamano or 1)
	emisor.Transparency = Utiles.Numeros(capa.Transparencia or { 0, 1 })
	emisor.Lifetime = Utiles.Rango(capa.Vida or 0.6)
	emisor.Speed = Utiles.Rango(capa.Velocidad or 0)
	emisor.SpreadAngle = Vector2.new(dispersion, dispersion)
	emisor.Acceleration = Utiles.V3(capa.Aceleracion)
	emisor.Drag = capa.Arrastre or 0
	emisor.LightEmission = capa.Brillo or 1
	emisor.LightInfluence = 0
	emisor.Rotation = Utiles.Rango(capa.Rotacion or { 0, 360 })
	emisor.RotSpeed = Utiles.Rango(capa.VelRotacion or 0)
	emisor.Squash = NumberSequence.new(capa.Estirar or 0)
	emisor.Orientation = ORIENTACIONES[capa.Orientacion or "Camara"] or Enum.ParticleOrientation.FacingCamera
	emisor.Shape = FORMAS[capa.Forma or "Box"] or Enum.ParticleEmitterShape.Box
	emisor.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	emisor.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
	emisor.EmissionDirection = Enum.NormalId.Top
	emisor.LockedToPart = false
	emisor.ZOffset = capa.ZOffset or 0
	emisor.Rate = 0
	emisor.Enabled = false

	local vidaMaxima = Utiles.Rango(capa.Vida or 0.6).Max

	if capa.Tasa then
		-- Chorro continuo.
		local duracion: number = capa.Duracion or 0.5
		emisor.Rate = capa.Tasa * factor
		emisor.Enabled = true

		local transcurrido = 0
		Actores.Agregar(function(dt)
			transcurrido += dt
			if capa.Sigue and parte.Parent then
				parte.CFrame = orientar(Utiles.Ancla(ctx, capa.Anclaje, capa.Desplazamiento), direccion)
			end
			if transcurrido >= duracion or ctx.Cancelado then
				emisor.Enabled = false
				return true
			end
			return false
		end)
		Pool.LiberarEn(parte, duracion + vidaMaxima + 0.3)
	else
		-- Estallido.
		emisor:Emit(Utiles.Cantidad(capa.Cantidad or 10, factor))
		Pool.LiberarEn(parte, vidaMaxima + 0.3)
	end
end

return Particulas
