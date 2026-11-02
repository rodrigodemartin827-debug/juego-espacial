--!strict
--[[
	Punto de entrada del cliente.

	Rojo sincroniza esta carpeta como `StarterPlayer.StarterPlayerScripts.Client`: este archivo
	(init.client.luau) se convierte en un LocalScript y el resto de módulos de la carpeta quedan
	como hijos suyos.

	Aquí solo se arrancan los servicios; la lógica vive en los módulos de `Servicios/`.
]]

local ServicioCombate = require(script.Combate.ServicioCombate)
local ServicioDatos = require(script.Servicios.ServicioDatos)
local ServicioNaves = require(script.Naves.ServicioNaves)
local ServicioRed = require(script.Servicios.ServicioRed)

-- Primero la red (espera a que el servidor publique los remotos) y después lo que los usa.
ServicioRed.Iniciar()
ServicioDatos.Iniciar()
ServicioCombate.Iniciar()
ServicioNaves.Iniciar()

-- Aviso en la consola mientras no hay interfaz: permite comprobar que los datos llegan.
ServicioDatos.Actualizados:Conectar(function(datos)
	print(`[Cliente] Datos recibidos: bando {datos.Bando}, nivel {datos.Nivel}, {datos.Monedas} monedas`)
end)

print("[Cliente] Juego espacial iniciado")
