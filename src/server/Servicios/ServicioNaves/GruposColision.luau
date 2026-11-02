--!strict
--[[
	GruposColision (Naves): grupos de colisión físicos de Roblox para naves y asteroides.

	Las naves NO chocan físicamente con nada: sus choques con los asteroides los decide el servidor (con
	consultas espaciales) y el piloto rebota por código. Si además chocaran con la física del motor, la nave
	temblaría contra la roca y el servidor y el cliente discreparían. Por eso las naves (y su piloto) van en un
	grupo que no colisiona con asteroides, ni con el suelo, ni con otras naves.

	Los asteroides siguen siendo sólidos para todo lo demás (un jugador a pie puede subirse a uno).
]]

local PhysicsService = game:GetService("PhysicsService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Naves.Config)

local GruposColision = {}

local preparados = false

-- Registra los grupos y sus reglas. Se puede llamar varias veces; solo actúa la primera.
function GruposColision.Preparar()
	if preparados then
		return
	end
	preparados = true

	for _, nombre in { Config.GrupoNaves, Config.GrupoAsteroides } do
		-- RegisterCollisionGroup falla si el grupo ya existe (p. ej. al reiniciar el script en Studio).
		pcall(function()
			PhysicsService:RegisterCollisionGroup(nombre)
		end)
	end
	local ok, motivo = pcall(function()
		PhysicsService:CollisionGroupSetCollidable(Config.GrupoNaves, Config.GrupoAsteroides, false)
		PhysicsService:CollisionGroupSetCollidable(Config.GrupoNaves, Config.GrupoNaves, false)
		PhysicsService:CollisionGroupSetCollidable(Config.GrupoNaves, "Default", false)
	end)
	if not ok then
		warn(`[Naves] No se pudieron configurar los grupos de colisión: {motivo}`)
	end
end

-- Pone `grupo` a la instancia y a todas las partes que contiene.
function GruposColision.Aplicar(raiz: Instance, grupo: string)
	if raiz:IsA("BasePart") then
		raiz.CollisionGroup = grupo
	end
	for _, descendiente in raiz:GetDescendants() do
		if descendiente:IsA("BasePart") then
			descendiente.CollisionGroup = grupo
		end
	end
end

return GruposColision
