--!strict
--[[
	Capas de formas animadas con TweenService: "Onda", "Esfera" y "Luz".

	"Onda"   Onda expansiva: un disco (o un anillo, si Recursos.Mallas.Anillo tiene un mesh) que crece y se desvanece.
	  Diametro       { inicio, fin } en studs
	  Grosor         altura del disco (0.4)
	  Transparencia  { inicio, fin } ({0.2, 1})
	  Duracion       segundos
	  Color, Material (por defecto "Neon"), Easing ("Quad", "Exponential"...)
	  Orientacion    "Suelo" (tumbada), "Frente" (de pie, mirando al golpe) ("Suelo")
	  Giro           grados que gira mientras crece
	  Malla          nombre en Recursos.Mallas que sustituye al disco (el mesh debe medir 1 stud)

	"Esfera"  Esfera que crece o se encoge (si Diametro va de grande a pequeño es una implosión).
	  Diametro, Transparencia, Duracion, Color, Material, Easing, Malla
	  Sigue          si es true, acompaña a su ancla mientras dura (carga en la mano, aura)

	"Luz"     Destello de luz puntual que se apaga.
	  Brillo { inicio, fin }, Rango { inicio, fin }, Duracion, Color
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Recursos = require(ReplicatedStorage:WaitForChild("Shared").Combate.Datos.Recursos)
local Actores = require(script.Parent.Parent.Actores)
local Calidad = require(script.Parent.Parent.Calidad)
local Pool = require(script.Parent.Parent.Pool)
local Utiles = require(script.Parent.Parent.Utiles)

local Formas = {}

local MATERIALES: { [string]: Enum.Material } = {
	Neon = Enum.Material.Neon,
	Cristal = Enum.Material.Glass,
	Plastico = Enum.Material.SmoothPlastic,
	Roca = Enum.Material.Slate,
	Basalto = Enum.Material.Basalt,
}

-- Par { inicio, fin } de una capa, con valores por defecto.
local function par(valor: any, inicio: number, fin: number): (number, number)
	if type(valor) == "table" then
		return valor[1] or inicio, valor[2] or valor[1] or fin
	end
	return inicio, fin
end

-- Pide una forma al pool: con mesh propio si la capa lo indica y el ID está relleno.
local function obtenerForma(clase: string, nombreMalla: string?): (Part, SpecialMesh?)
	local idMalla = if nombreMalla then Recursos.Mallas[nombreMalla] else nil
	if idMalla and idMalla ~= "" then
		local parte = Pool.Parte("Malla")
		local malla = parte:FindFirstChild("Malla") :: SpecialMesh
		malla.MeshId = idMalla
		return parte, malla
	end
	return Pool.Parte(clase), nil
end

-- Tamaño de la forma. Con mesh se escala el mesh (que debe medir 1 stud); sin él, el propio Part.
local function ponerTamano(parte: Part, malla: SpecialMesh?, tamano: Vector3)
	if malla then
		malla.Scale = tamano
	else
		parte.Size = tamano
	end
end

local function animarTamano(parte: Part, malla: SpecialMesh?, tamano: Vector3, duracion: number, estilo: string?)
	if malla then
		Utiles.Tween(malla, duracion, { Scale = tamano }, estilo)
	else
		Utiles.Tween(parte, duracion, { Size = tamano }, estilo)
	end
end

-- Hace que la forma acompañe a su ancla mientras dura.
local function seguir(parte: Part, ctx: any, capa: any, duracion: number, ajuste: CFrame)
	local transcurrido = 0
	Actores.Agregar(function(dt)
		transcurrido += dt
		if transcurrido >= duracion or parte.Parent == nil then
			return true
		end
		parte.CFrame = Utiles.Ancla(ctx, capa.Anclaje, capa.Desplazamiento) * ajuste
		return false
	end)
end

function Formas.Onda(capa: any, ctx: any)
	local duracion: number = capa.Duracion or 0.5
	local d0, d1 = par(capa.Diametro, 2, 20)
	local t0, t1 = par(capa.Transparencia, 0.2, 1)
	local grosor: number = capa.Grosor or 0.4

	local parte, malla = obtenerForma("Cilindro", capa.Malla)
	local marco = Utiles.Ancla(ctx, capa.Anclaje, capa.Desplazamiento)
	-- El cilindro de Roblox tiene su eje en X: se gira para tumbarlo (Suelo) o ponerlo de pie (Frente).
	local ajuste = if capa.Orientacion == "Frente"
		then CFrame.Angles(0, math.pi / 2, 0)
		else CFrame.Angles(0, 0, math.pi / 2)
	if malla then
		ajuste = CFrame.identity -- un mesh de anillo ya viene tumbado
	end

	parte.Color = Utiles.Color(capa.Color or "Principal", ctx.Paleta)
	parte.Material = MATERIALES[capa.Material or "Neon"] or Enum.Material.Neon
	parte.Transparency = t0
	parte.CFrame = marco * ajuste
	ponerTamano(parte, malla, Vector3.new(grosor, d0, d0))

	animarTamano(parte, malla, Vector3.new(grosor, d1, d1), duracion, capa.Easing or "Quart")
	Utiles.Tween(parte, duracion, { Transparency = t1 }, "Quad", true)
	if capa.Giro then
		Utiles.Tween(parte, duracion, { CFrame = marco * ajuste * CFrame.Angles(0, math.rad(capa.Giro), 0) }, "Quad")
	end
	Pool.LiberarEn(parte, duracion + 0.05)
end

function Formas.Esfera(capa: any, ctx: any)
	local duracion: number = capa.Duracion or 0.5
	local d0, d1 = par(capa.Diametro, 1, 10)
	local t0, t1 = par(capa.Transparencia, 0.1, 1)

	local parte, malla = obtenerForma("Bola", capa.Malla)
	parte.Color = Utiles.Color(capa.Color or "Principal", ctx.Paleta)
	parte.Material = MATERIALES[capa.Material or "Neon"] or Enum.Material.Neon
	parte.Transparency = t0
	parte.CFrame = Utiles.Ancla(ctx, capa.Anclaje, capa.Desplazamiento)
	ponerTamano(parte, malla, Vector3.one * d0)

	animarTamano(parte, malla, Vector3.one * d1, duracion, capa.Easing or "Quad")
	Utiles.Tween(parte, duracion, { Transparency = t1 }, "Quad", true)
	if capa.Sigue then
		seguir(parte, ctx, capa, duracion, CFrame.identity)
	end
	Pool.LiberarEn(parte, duracion + 0.05)
end

function Formas.Luz(capa: any, ctx: any)
	if Calidad.Factor("Luces") <= 0 then
		return
	end
	local duracion: number = capa.Duracion or 0.4
	local b0, b1 = par(capa.Brillo, 6, 0)
	local r0, r1 = par(capa.Rango, 14, 30)

	local parte, luz = Pool.Luz()
	parte.CFrame = Utiles.Ancla(ctx, capa.Anclaje, capa.Desplazamiento)
	luz.Color = Utiles.Color(capa.Color or "Principal", ctx.Paleta)
	luz.Brightness = b0
	luz.Range = r0
	luz.Enabled = true

	Utiles.Tween(luz, duracion, { Brightness = b1, Range = r1 }, capa.Easing or "Quad")
	if capa.Sigue then
		seguir(parte, ctx, capa, duracion, CFrame.identity)
	end
	Pool.LiberarEn(parte, duracion + 0.05)
end

return Formas
