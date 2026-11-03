--[[
	Ejecuta las pruebas del proyecto con Lune, desde la carpeta raíz del repositorio:

		lune run pruebas/ejecutar                -- todas las pruebas
		lune run pruebas/ejecutar ServicioRed    -- solo las que contengan ese texto en el nombre

	Las pruebas cargan los módulos reales de `src/` sobre una simulación mínima de la API de Roblox
	(ver pruebas/infraestructura). Cada archivo de pruebas/casos/ registra los casos de un módulo.
]]

local process = require("@lune/process")

local Entorno = require("./infraestructura/Entorno")
local Marco = require("./infraestructura/Marco")

-- Archivos de pruebas/casos/ (sin extensión), en el orden en que se ejecutan.
local CASOS = {
	require("./casos/Estructura"),
	require("./casos/SoloR6"),
	require("./casos/Utilidades"),
	require("./casos/Red"),
	require("./casos/ServicioRed"),
	require("./casos/Esquema"),
	require("./casos/BloqueoSesion"),
	require("./casos/AlmacenMemoria"),
	require("./casos/ServicioDatos"),
	require("./casos/Integracion"),
	require("./casos/Exploracion"),
	require("./casos/ExploracionVFX"),
	require("./casos/ExploracionRed"),
	require("./casos/ServicioPersonaje"),
	require("./casos/Combate"),
	require("./casos/CombateVFX"),
	require("./casos/Naves"),
	require("./casos/NavesVFX"),
	require("./casos/NavesRed"),
	require("./casos/PlanetaPrueba"),
}

Marco.verificarAlTerminar(Entorno.verificarSinErrores)
Marco.despuesDeCadaPrueba(Entorno.cerrarTodos)

for _, registrar in CASOS do
	registrar(Marco)
end

Marco.ejecutar(process.args[1])
