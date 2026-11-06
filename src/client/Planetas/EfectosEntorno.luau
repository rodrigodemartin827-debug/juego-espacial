--!strict
--[[
	EfectosEntorno (Planetas, cliente): los efectos visuales del entorno sobre la nave propia.

	Usa el motor de VFX del juego (client/VFX/Gestor) con las recetas de Planetas/Datos/Efectos:
	  - recalentamiento: un "latido" de chispas, tinte y temblor, más seguido cuanto más caliente;
	  - atracción del agujero negro: la imagen se estira y vibra, más a menudo cuanto más fuerte tira;
	  - entrada en la atmósfera y salida al espacio, con las transiciones;
	  - una nave que cae en el agujero negro implosiona en lugar de estallar.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Datos = require(Shared.Planetas.Datos)
local Efectos = require(Shared.Planetas.Datos.Efectos)
local Gravedad = require(Shared.Planetas.Gravedad)
local Gestor = require(script.Parent.Parent.VFX.Gestor)

local EfectosEntorno = {}

local CENTRO_AGUJERO =
	Vector3.new(Datos.AgujeroNegro.Centro.X, Datos.AgujeroNegro.Centro.Y, Datos.AgujeroNegro.Centro.Z)

local proximoCalor = 0
local proximaAtraccion = 0

local function reproducir(receta: string, fase: string, raiz: BasePart?, modelo: Model?, punto: Vector3?)
	local posicion = punto or (if raiz then raiz.Position else Vector3.zero)
	Gestor.Reproducir(receta, fase, {
		Origen = posicion,
		Punto = posicion,
		Direccion = if raiz then raiz.CFrame.LookVector else Vector3.new(0, 0, -1),
		Lanzador = modelo,
		Raiz = raiz,
		EsLocal = true,
		DistanciaMaxima = 2000,
	})
end

-- Registra las recetas en el motor. Debe llamarse una vez.
function EfectosEntorno.Iniciar()
	Gestor.RegistrarRecetas(Efectos)
end

-- Cada fotograma mientras se pilota: latidos de calor y de atracción.
function EfectosEntorno.Actualizar(nave: any, raiz: BasePart?)
	if nave == nil or raiz == nil or nave.Activa ~= true or nave.EnTransicion == true then
		return
	end
	local ahora = os.clock()
	local modelo = raiz:FindFirstAncestorOfClass("Model")

	if (nave.NivelCalor == "Peligro" or nave.NivelCalor == "Aviso") and ahora >= proximoCalor then
		local fraccion = math.clamp((nave.Calor or 0) / math.max(nave.CalorMax or 100, 1), 0, 1)
		proximoCalor = ahora + (if nave.NivelCalor == "Peligro" then 0.7 else 1.6) * (1.3 - fraccion * 0.6)
		reproducir("Espacio_Calor", "Impacto", raiz, modelo)
	end

	local arrastre = Gravedad.Arrastre((raiz.Position - CENTRO_AGUJERO).Magnitude, Datos.AgujeroNegro.Atraccion)
	if arrastre > 5 and ahora >= proximaAtraccion then
		local fuerza = math.clamp(arrastre / Datos.AgujeroNegro.Atraccion.VelocidadSinRetorno, 0, 1.5)
		proximaAtraccion = ahora + 2.6 - fuerza * 1.4
		reproducir("Espacio_Atraccion", "Impacto", raiz, modelo)
	end
end

-- La nave propia entra en la atmósfera (antes del fundido) o sale al espacio (al volver la imagen).
function EfectosEntorno.Entrada(raiz: BasePart?)
	if raiz then
		reproducir("Planeta_Entrada", "Lanzamiento", raiz, raiz:FindFirstAncestorOfClass("Model"))
	end
end

function EfectosEntorno.Salida(raiz: BasePart?)
	if raiz then
		reproducir("Planeta_Salida", "Lanzamiento", raiz, raiz:FindFirstAncestorOfClass("Model"))
	end
end

-- Una nave destruida: si ha sido junto al horizonte del agujero negro, se ve cómo lo engulle.
function EfectosEntorno.NaveDestruida(posicion: any)
	if typeof(posicion) ~= "Vector3" then
		return
	end
	local punto = posicion :: Vector3
	if (punto - CENTRO_AGUJERO).Magnitude <= Datos.AgujeroNegro.RadioHorizonte * 2 then
		reproducir("Espacio_Absorcion", "Impacto", nil, nil, punto)
	end
end

return EfectosEntorno
