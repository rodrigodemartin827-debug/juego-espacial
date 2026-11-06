--!strict
--[[
	Punto de entrada del cliente.

	Rojo sincroniza esta carpeta como `StarterPlayer.StarterPlayerScripts.Client`: este archivo
	(init.client.luau) se convierte en un LocalScript y el resto de módulos de la carpeta quedan
	como hijos suyos.

	Aquí solo se arrancan los servicios; la lógica vive en los módulos de `Servicios/`.
]]

-- EXPERIMENTO planeta redondo (solo en Studio): ajusta los datos de los planetas ANTES de que nadie los lea.
require(
	game:GetService("ReplicatedStorage")
		:WaitForChild("Shared")
		:WaitForChild("Experimentos")
		:WaitForChild("PlanetaRedondo") :: any
).Aplicar()

local ServicioCombate = require(script.Combate.ServicioCombate)
local ServicioDatos = require(script.Servicios.ServicioDatos)
local ServicioEleccion = require(script.Eleccion.ServicioEleccion)
local ServicioExploracion = require(script.Exploracion.ServicioExploracion)
local ServicioNaves = require(script.Naves.ServicioNaves)
local ServicioPlanetas = require(script.Planetas.ServicioPlanetas)
local ServicioRed = require(script.Servicios.ServicioRed)
local GravedadPlaneta = require(script.Experimentos.GravedadPlaneta)
local ServicioTiendas = require(script.Tiendas.ServicioTiendas)

-- Primero la red (espera a que el servidor publique los remotos) y después lo que los usa. La pantalla de elección
-- de bando va la última: pausa y oculta lo de los demás mientras el jugador elige (solo la primera vez).
ServicioEleccion.Preparar() -- cortina negra hasta saber si hay que elegir bando
ServicioRed.Iniciar()
ServicioDatos.Iniciar()
ServicioCombate.Iniciar()
ServicioNaves.Iniciar()
ServicioExploracion.Iniciar()
ServicioPlanetas.Iniciar()
ServicioTiendas.Iniciar()
GravedadPlaneta.Iniciar() -- EXPERIMENTO: solo hace algo en Studio, con el experimento activo
ServicioEleccion.Iniciar()

-- Aviso en la consola mientras no hay interfaz: permite comprobar que los datos llegan.
ServicioDatos.Actualizados:Conectar(function(datos)
	print(`[Cliente] Datos recibidos: bando {datos.Bando}, nivel {datos.Nivel}, {datos.Monedas} monedas`)
end)

print("[Cliente] Juego espacial iniciado")
