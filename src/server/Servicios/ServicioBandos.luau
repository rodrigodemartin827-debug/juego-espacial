--!strict
--[[
	ServicioBandos: atiende la elección de bando del jugador (Humanos o Monstruos).

	Es el primer consumidor real de los sistemas de red y de datos, y sirve de ejemplo de cómo escribir
	un servicio:
	  - Recibe la petición por ServicioRed.Conectar. Cuando el manejador se ejecuta, el remoto ya ha pasado
	    el límite por segundo y la validación (el bando es "Humanos" o "Monstruos"), pero la lógica de la
	    partida sigue siendo cosa del manejador: ¿tiene ya bando? ¿han cargado sus datos?
	  - Modifica directamente los datos que devuelve ServicioDatos.ObtenerDatos.
	  - Avisa al cliente con ServicioReplicacion y guarda de inmediato, porque elegir bando es una decisión
	    que no debe perderse si el servidor falla.

	Regla actual: el bando se elige una sola vez y no se puede cambiar. Para permitir cambios (con un
	coste, un enfriamiento...) bastaría con modificar la comprobación del manejador.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Bandos = require(ReplicatedStorage.Shared.Juego.Bandos)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioRed = require(script.Parent.ServicioRed)
local ServicioReplicacion = require(script.Parent.ServicioReplicacion)

local ServicioBandos = {}

-- Asigna el bando al jugador si todavía no tiene (la regla de arriba). Lo usa el remoto y la zona de pruebas.
function ServicioBandos.Elegir(jugador: Player, bando: Bandos.IdBando)
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return -- sus datos todavía no han cargado: no hay dónde guardar la elección
	end
	if datos.Bando ~= Bandos.Ninguno then
		return -- ya eligió bando
	end

	datos.Bando = bando
	ServicioReplicacion.EnviarDatos(jugador)
	ServicioDatos.GuardarAhora(jugador)
end

-- Empieza a atender el remoto ElegirBando. Debe llamarse una sola vez, después de ServicioRed.Iniciar().
function ServicioBandos.Iniciar()
	ServicioRed.Conectar("ElegirBando", ServicioBandos.Elegir)
end

return ServicioBandos
