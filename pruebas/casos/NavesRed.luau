--[[
	Pruebas de la red de las naves.

	El servidor y el cliente de las naves usan Roblox de lleno (Part, CFrame, física...) y la simulación de las
	pruebas no lo tiene, así que no se pueden ejecutar aquí. Lo que sí se puede comprobar es que están bien CABLEADOS:

	  - cada remoto que usa el código está declarado en Red/Remotos y en la dirección correcta,
	  - cada remoto de naves declarado se usa, por los dos lados,
	  - los remotos que manda el cliente validan sus argumentos (un cliente manipulado no puede mandar basura).
]]

local fs = require("@lune/fs")

local Entorno = require("../infraestructura/Entorno")

-- Lista los .luau de un directorio (y subdirectorios).
local function archivos(directorio: string, resultado: { string }): { string }
	for _, nombre in fs.readDir(directorio) do
		local ruta = `{directorio}/{nombre}`
		if fs.isDir(ruta) then
			archivos(ruta, resultado)
		elseif string.sub(nombre, -5) == ".luau" then
			table.insert(resultado, ruta)
		end
	end
	return resultado
end

-- Junta el texto de todos los archivos de las rutas indicadas.
local function leer(rutas: { string }): string
	local textos = {}
	for _, ruta in rutas do
		if fs.isDir(ruta) then
			for _, archivo in archivos(ruta, {}) do
				table.insert(textos, fs.readFile(archivo))
			end
		else
			table.insert(textos, fs.readFile(ruta))
		end
	end
	return table.concat(textos, "\n")
end

-- Nombres capturados por un patrón de Lua en un texto.
local function capturas(texto: string, patron: string): { [string]: boolean }
	local nombres = {}
	for nombre in string.gmatch(texto, patron) do
		nombres[nombre] = true
	end
	return nombres
end

-- Remotos que forman el sistema de naves.
local DEL_CLIENTE = { "AterrizarNave", "DispararNave", "TurboNave", "PedirEstadoNave" }
local DEL_SERVIDOR = {
	"EstadoNave",
	"NaveDespegue",
	"NaveDisparo",
	"NaveImpacto",
	"NaveChoque",
	"NaveDestruida",
	"AsteroideDestruido",
}

return function(Marco)
	local entorno = Entorno.nuevo()
	local Remotos = entorno.servidor.requerir("ReplicatedStorage.Shared.Red.Remotos")
	local Validador = entorno.servidor.requerir("ReplicatedStorage.Shared.Red.Validador")

	local servidor = leer({ "src/server/Servicios/ServicioNaves", "src/server/Servicios/ServicioAsteroides.luau" })
	local cliente = leer({ "src/client/Naves" })

	-- Lo que el servidor escucha y lo que envía.
	local escuchaServidor = capturas(servidor, 'ServicioRed%.Conectar%(%s*"([%w_]+)"')
	local envia = capturas(servidor, 'EnviarATodos%(%s*"([%w_]+)"')
	for nombre in capturas(servidor, 'EnviarACliente%(%s*[%w_%.]+%s*,%s*"([%w_]+)"') do
		envia[nombre] = true
	end
	-- Lo que el cliente envía y lo que escucha.
	local enviaCliente = capturas(cliente, 'ServicioRed%.Enviar%(%s*"([%w_]+)"')
	local escuchaCliente = capturas(cliente, 'ServicioRed%.Conectar%(%s*"([%w_]+)"')

	Marco.grupo("Naves: red", function()
		Marco.prueba("cada remoto que usa el código está declarado y en la dirección correcta", function()
			for nombre in escuchaServidor do
				Marco.distinto(
					Remotos.Definiciones[nombre],
					nil,
					`el servidor escucha '{nombre}', que no está en Remotos`
				)
				Marco.igual(
					Remotos.Definiciones[nombre].Direccion,
					"ClienteAServidor",
					`{nombre}: el servidor solo escucha ClienteAServidor`
				)
			end
			for nombre in enviaCliente do
				Marco.distinto(
					Remotos.Definiciones[nombre],
					nil,
					`el cliente envía '{nombre}', que no está en Remotos`
				)
				Marco.igual(
					Remotos.Definiciones[nombre].Direccion,
					"ClienteAServidor",
					`{nombre}: el cliente solo envía ClienteAServidor`
				)
			end
			for nombre in envia do
				Marco.distinto(
					Remotos.Definiciones[nombre],
					nil,
					`el servidor envía '{nombre}', que no está en Remotos`
				)
				Marco.igual(
					Remotos.Definiciones[nombre].Direccion,
					"ServidorACliente",
					`{nombre}: el servidor solo envía ServidorACliente`
				)
			end
			for nombre in escuchaCliente do
				Marco.distinto(
					Remotos.Definiciones[nombre],
					nil,
					`el cliente escucha '{nombre}', que no está en Remotos`
				)
				Marco.igual(
					Remotos.Definiciones[nombre].Direccion,
					"ServidorACliente",
					`{nombre}: el cliente solo escucha ServidorACliente`
				)
			end
		end)

		Marco.prueba("los remotos que pide el cliente tienen manejador en el servidor y quien los envía", function()
			for _, nombre in DEL_CLIENTE do
				Marco.verdadero(escuchaServidor[nombre], `{nombre}: nadie lo escucha en el servidor`)
				Marco.verdadero(enviaCliente[nombre], `{nombre}: el cliente nunca lo envía`)
				Marco.igual(Remotos.Definiciones[nombre].Direccion, "ClienteAServidor")
			end
		end)

		Marco.prueba("los avisos del servidor se envían y el cliente los escucha", function()
			for _, nombre in DEL_SERVIDOR do
				Marco.verdadero(envia[nombre], `{nombre}: el servidor nunca lo envía`)
				Marco.verdadero(escuchaCliente[nombre], `{nombre}: el cliente no lo escucha`)
				Marco.igual(Remotos.Definiciones[nombre].Direccion, "ServidorACliente")
			end
		end)

		Marco.prueba("todos los remotos del cliente tienen límite por segundo y lista de argumentos", function()
			for _, nombre in DEL_CLIENTE do
				local definicion = Remotos.Definiciones[nombre]
				Marco.distinto(definicion.Argumentos, nil, `{nombre}: faltan los validadores de argumentos`)
				Marco.verdadero((definicion.LimitePorSegundo or 0) > 0, `{nombre}: sin límite por segundo`)
			end
		end)
	end)

	Marco.grupo("Naves: validación de lo que manda el cliente", function()
		local function valida(nombre: string, ...)
			local ok = Validador.ValidarArgumentos(Remotos.Definiciones[nombre].Argumentos, ...)
			return ok
		end
		local V3 = entorno.mundo.Vector3.new

		Marco.prueba("DispararNave acepta una dirección y rechaza basura", function()
			Marco.verdadero(valida("DispararNave", V3(0, 0, -1)), "dirección unitaria")
			Marco.verdadero(valida("DispararNave", V3(0.3, 0.2, -0.9)), "dirección con inclinación")
			Marco.falso(valida("DispararNave", V3(0, 0, -50)), "vector enorme")
			Marco.falso(valida("DispararNave", V3(0 / 0, 0, 0)), "NaN")
			Marco.falso(valida("DispararNave", V3(math.huge, 0, 0)), "infinito")
			Marco.falso(valida("DispararNave", "adelante"), "texto")
			Marco.falso(valida("DispararNave"), "sin argumentos")
			Marco.falso(valida("DispararNave", V3(0, 0, -1), 5), "argumentos de más")
		end)

		Marco.prueba("TurboNave solo acepta un booleano", function()
			Marco.verdadero(valida("TurboNave", true))
			Marco.verdadero(valida("TurboNave", false))
			Marco.falso(valida("TurboNave", 1))
			Marco.falso(valida("TurboNave", "true"))
			Marco.falso(valida("TurboNave"))
		end)

		Marco.prueba("aterrizar y pedir el estado no llevan argumentos", function()
			for _, nombre in { "AterrizarNave", "PedirEstadoNave" } do
				Marco.verdadero(valida(nombre))
				Marco.falso(valida(nombre, 1), `{nombre} con argumentos`)
			end
		end)

		Marco.prueba("disparar tiene ráfaga para absorber la latencia pero un límite sostenido bajo", function()
			local definicion = Remotos.Definiciones.DispararNave
			Marco.verdadero(definicion.LimitePorSegundo <= 20, "límite sostenido demasiado alto")
			Marco.verdadero((definicion.Rafaga or definicion.LimitePorSegundo) >= 3, "sin margen para el jitter")
		end)
	end)
end
