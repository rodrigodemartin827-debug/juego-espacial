--!strict
--[[
	ServicioReplicacion: mantiene al cliente al tanto de sus propios datos.

	Los datos viven en el servidor (ServicioDatos) y el cliente solo recibe una copia para mostrarla
	(barra de XP, monedas, pantalla de la nave...). Este servicio envía esa copia por el remoto
	DatosJugador:
	  - cuando los datos del jugador acaban de cargarse,
	  - cuando el cliente la pide con PedirDatos (al arrancar: si el servidor ya la había enviado antes de
	    que el cliente estuviera escuchando, el mensaje se habría perdido), y
	  - cuando otro servicio llama a `EnviarDatos` tras modificarlos.

	Cada envío manda los datos completos, que son pocos; no se usa para cambios muy frecuentes (por
	ejemplo, a cada disparo). Agrupa los cambios y envía cuando haga falta.

	Uso (desde cualquier servicio del servidor):
		datos.Monedas += 10
		ServicioReplicacion.EnviarDatos(jugador)
]]

local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioRed = require(script.Parent.ServicioRed)

local ServicioReplicacion = {}

-- Envía al jugador una copia de sus datos actuales. No hace nada si todavía no se han cargado.
function ServicioReplicacion.EnviarDatos(jugador: Player)
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return
	end
	ServicioRed.EnviarACliente(jugador, "DatosJugador", datos)
end

--[[
	Empieza a replicar los datos. Debe llamarse una sola vez, después de ServicioRed.Iniciar() y ANTES de
	ServicioDatos.Iniciar(), para no perderse los jugadores cuyos datos carguen nada más arrancar.
]]
function ServicioReplicacion.Iniciar()
	ServicioDatos.DatosCargados:Conectar(ServicioReplicacion.EnviarDatos)
	ServicioRed.Conectar("PedirDatos", ServicioReplicacion.EnviarDatos)
end

return ServicioReplicacion
