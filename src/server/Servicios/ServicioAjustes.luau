--!strict
--[[
	ServicioAjustes: guarda los ajustes del jugador que elige él mismo y que no afectan al juego de nadie más (de
	momento, el nivel de gráficos).

	El cliente solo pide (remoto ElegirGraficos, ya validado: uno de Graficos/Config.Orden); el servidor lo apunta en
	sus datos, se los reenvía y los guarda.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Niveles = require(ReplicatedStorage.Shared.Graficos.Niveles)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioRed = require(script.Parent.ServicioRed)
local ServicioReplicacion = require(script.Parent.ServicioReplicacion)

local ServicioAjustes = {}

local iniciado = false

-- Apunta el nivel de gráficos del jugador. Devuelve true si se aplicó.
function ServicioAjustes.ElegirGraficos(jugador: Player, nivel: string): boolean
	if not Niveles.Valido(nivel) then
		return false
	end
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return false
	end
	if datos.Graficos ~= nivel then
		datos.Graficos = nivel
		ServicioReplicacion.EnviarDatos(jugador)
		ServicioDatos.GuardarAhora(jugador)
	end
	return true
end

-- Empieza a atender los remotos. Una sola vez, después de ServicioRed.Iniciar().
function ServicioAjustes.Iniciar()
	assert(not iniciado, "ServicioAjustes.Iniciar() solo debe llamarse una vez")
	iniciado = true
	ServicioRed.Conectar("ElegirGraficos", function(jugador: Player, nivel: string)
		ServicioAjustes.ElegirGraficos(jugador, nivel)
	end)
end

return ServicioAjustes
