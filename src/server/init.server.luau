--!strict
--[[
	Punto de entrada del servidor.

	Rojo sincroniza esta carpeta como `ServerScriptService.Server`: este archivo (init.server.luau)
	se convierte en un Script y el resto de módulos de la carpeta quedan como hijos suyos.

	Aquí solo se arrancan los servicios; la lógica vive en los módulos de `Servicios/`.
]]

local ServicioBandos = require(script.Servicios.ServicioBandos)
local ServicioDatos = require(script.Servicios.ServicioDatos)
local ServicioRed = require(script.Servicios.ServicioRed)
local ServicioReplicacion = require(script.Servicios.ServicioReplicacion)

--[[
	El orden importa:
	  1. La red, para crear los RemoteEvents antes de que los clientes los busquen.
	  2. Los servicios que escuchan remotos o señales (replicación y bandos).
	  3. Los datos, los últimos: empiezan a cargar jugadores y a disparar DatosCargados, y para entonces
	     todos los demás servicios ya deben estar escuchando.
]]
ServicioRed.Iniciar()
ServicioReplicacion.Iniciar()
ServicioBandos.Iniciar()
ServicioDatos.Iniciar()

print("[Servidor] Juego espacial iniciado")
