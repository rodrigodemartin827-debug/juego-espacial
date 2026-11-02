--!strict
--[[
	Choques (Naves): detecta, desde el servidor, si una nave toca un asteroide.

	La nave del piloto se mueve con la física de su propio cliente y no tiene colisión física con los asteroides
	(ver GruposColision), así que el servidor la comprueba él mismo cada fotograma con dos consultas:

	  1. Un barrido esférico desde donde estaba hasta donde está: encuentra el primer asteroide con el que se
	     cruzó, aunque vaya tan deprisa que haya atravesado uno pequeño entre dos fotogramas.
	  2. Una consulta de solape en la posición actual, por si ya está dentro de uno (el barrido no ve lo que ya
	     tenía encima al empezar).

	Solo se consultan las partes de la carpeta de asteroides (filtro Include), así que el coste no depende de
	cuántas partes tenga el resto del mundo.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Naves.Config)

export type Golpe = {
	Modelo: Model, -- el asteroide
	Punto: Vector3, -- donde se toca
	Normal: Vector3, -- hacia fuera de la roca
}

local Choques = {}

-- El modelo de asteroide al que pertenece una parte (nil si no es de ninguno).
function Choques.AsteroideDe(instancia: Instance): Model?
	local modelo = instancia:FindFirstAncestorWhichIsA("Model")
	if modelo and modelo:HasTag(Config.EtiquetaAsteroide) then
		return modelo
	end
	return nil
end

--[[
	Busca el primer asteroide que toca una nave de radio `radio` que va de `previa` a `actual`.
	`carpeta` es el contenedor de todos los asteroides.
]]
function Choques.Buscar(previa: Vector3, actual: Vector3, radio: number, carpeta: Instance): Golpe?
	local desplazamiento = actual - previa
	if desplazamiento.Magnitude > 0.05 then
		local parametros = RaycastParams.new()
		parametros.FilterType = Enum.RaycastFilterType.Include
		parametros.FilterDescendantsInstances = { carpeta }
		local barrido = workspace:Spherecast(previa, radio, desplazamiento, parametros)
		if barrido then
			local modelo = Choques.AsteroideDe(barrido.Instance)
			if modelo then
				return { Modelo = modelo, Punto = barrido.Position, Normal = barrido.Normal }
			end
		end
	end

	local solape = OverlapParams.new()
	solape.FilterType = Enum.RaycastFilterType.Include
	solape.FilterDescendantsInstances = { carpeta }
	for _, parte in workspace:GetPartBoundsInRadius(actual, radio, solape) do
		local modelo = Choques.AsteroideDe(parte)
		if modelo then
			-- Dentro del asteroide: se sale por el lado de la nave respecto al centro de la parte tocada.
			local hacia = actual - parte.Position
			local normal = if hacia.Magnitude > 0.01 then hacia.Unit else Vector3.yAxis
			return { Modelo = modelo, Punto = actual - normal * radio, Normal = normal }
		end
	end
	return nil
end

return Choques
