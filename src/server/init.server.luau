--!strict
--[[
	Punto de entrada del servidor.

	Rojo sincroniza esta carpeta como `ServerScriptService.Server`: este archivo (init.server.luau)
	se convierte en un Script y el resto de módulos de la carpeta quedan como hijos suyos.

	Aquí solo se arrancan los servicios; la lógica vive en los módulos de `Servicios/`.
]]

-- EXPERIMENTO planeta redondo (solo en Studio): ajusta los datos de los planetas ANTES de que nadie los lea.
require(game:GetService("ReplicatedStorage").Shared.Experimentos.PlanetaRedondo).Aplicar()

local ServicioAsteroides = require(script.Servicios.ServicioAsteroides)
local ServicioBandos = require(script.Servicios.ServicioBandos)
local ServicioCombate = require(script.Servicios.ServicioCombate)
local ServicioCrafteo = require(script.Servicios.ServicioCrafteo)
local ServicioDatos = require(script.Servicios.ServicioDatos)
local ServicioEscaner = require(script.Servicios.ServicioEscaner)
local ServicioInventario = require(script.Servicios.ServicioInventario)
local ServicioMinado = require(script.Servicios.ServicioMinado)
local ServicioNaves = require(script.Servicios.ServicioNaves)
local ServicioPersonaje = require(script.Servicios.ServicioPersonaje)
local ServicioPlanetas = require(script.Servicios.ServicioPlanetas)
local ServicioRed = require(script.Servicios.ServicioRed)
local ServicioReplicacion = require(script.Servicios.ServicioReplicacion)
local ZonaPruebas = require(script.Servicios.ZonaPruebas)
local ExperimentoPlanetaRedondo = require(script.Experimentos.PlanetaRedondo)

--[[
	El orden importa:
	  1. La red, para crear los RemoteEvents antes de que los clientes los busquen.
	  2. Los servicios que escuchan remotos o señales (replicación, personaje R6, bandos, combate y naves).
	     El del personaje va antes que el combate para que sustituya cualquier R15 antes de que se registre.
	     Los asteroides van antes que las naves, porque preparan los grupos de colisión que ellas usan.
	     Exploración (inventario, minería, escáner y crafteo) va después de las naves, que le piden golpear minerales.
	     Los planetas van después de las naves (conectan con ellas el aterrizaje y el despegue) y antes de la zona de
	     pruebas (que pone plataformas para viajar a ellos).
	  3. Los datos, los últimos: empiezan a cargar jugadores y a disparar DatosCargados, y para entonces
	     todos los demás servicios ya deben estar escuchando.
]]
ServicioRed.Iniciar()
ServicioReplicacion.Iniciar()
ServicioPersonaje.Iniciar()
ServicioBandos.Iniciar()
ServicioCombate.Iniciar()
ServicioAsteroides.Iniciar()
ServicioNaves.Iniciar()
ServicioInventario.Iniciar()
ServicioMinado.Iniciar()
ServicioEscaner.Iniciar()
ServicioCrafteo.Iniciar()
ServicioPlanetas.Iniciar()
ZonaPruebas.Iniciar()
ExperimentoPlanetaRedondo.Iniciar() -- solo hace algo en Studio, con el experimento activo
-- EXPERIMENTO: esta rama sale de antes del cambio de bandos y no entiende los datos de Studio ya migrados. Usa su
-- propio almacén de pruebas para no tocar ni rechazar los datos de Studio de siempre.
if require(game:GetService("ReplicatedStorage").Shared.Experimentos.PlanetaRedondo).Activado() then
	ServicioDatos.Configuracion.NombreAlmacen = "DatosJugadorExperimentoPlaneta"
end
ServicioDatos.Iniciar()

print("[Servidor] Juego espacial iniciado")
