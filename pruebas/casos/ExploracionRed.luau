--[[
	Pruebas de la red y del cableado de la exploración (escáner, minería, inventario y crafteo).

	Los servicios usan Roblox de lleno (Part, CollectionService, ProximityPrompt...) y la simulación de las pruebas no lo
	tiene, así que no se ejecutan aquí. Lo que sí se comprueba es que estén bien CABLEADOS:

	  - cada remoto que usa el código está declarado en Red/Remotos y en la dirección correcta,
	  - cada remoto de la exploración se usa por los dos lados,
	  - lo que manda el cliente se valida (un cliente manipulado no puede mandar basura),
	  - las reglas de seguridad del servidor están en el código (distancia, cadencia, mesa, atomicidad...).
]]

local fs = require("@lune/fs")

local Entorno = require("../infraestructura/Entorno")

local function leer(rutas: { string }): string
	local textos = {}
	for _, ruta in rutas do
		table.insert(textos, fs.readFile(ruta))
	end
	return table.concat(textos, "\n")
end

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

local function capturas(texto: string, patron: string): { [string]: boolean }
	local nombres = {}
	for nombre in string.gmatch(texto, patron) do
		nombres[nombre] = true
	end
	return nombres
end

local DEL_CLIENTE = { "EscanearObjetivo", "CancelarEscaneo", "PicarMineral", "FabricarReceta" }
local DEL_SERVIDOR = {
	"EscaneoIniciado",
	"EscaneoCancelado",
	"EscaneoCompletado",
	"FichaEscaner",
	"MineralGolpeado",
	"MineralRoto",
	"AvisoExploracion",
	"ResultadoCrafteo",
	"AbrirMesaCrafteo",
}

return function(Marco)
	local entorno = Entorno.nuevo()
	local Remotos = entorno.servidor.requerir("ReplicatedStorage.Shared.Red.Remotos")
	local Validador = entorno.servidor.requerir("ReplicatedStorage.Shared.Red.Validador")
	local Recetas = entorno.servidor.requerir("ReplicatedStorage.Shared.Exploracion.Datos.Recetas")
	local ConfigNaves = entorno.servidor.requerir("ReplicatedStorage.Shared.Naves.Config")
	local Config = entorno.servidor.requerir("ReplicatedStorage.Shared.Exploracion.Config")

	local servidor = leer({
		"src/server/Servicios/ServicioEscaner.luau",
		"src/server/Servicios/ServicioMinado.luau",
		"src/server/Servicios/ServicioCrafteo.luau",
		"src/server/Servicios/ServicioInventario.luau",
	})
	local cliente = leer(archivos("src/client/Exploracion", {}))

	local escuchaServidor = capturas(servidor, 'ServicioRed%.Conectar%(%s*"([%w_]+)"')
	local envia = capturas(servidor, 'EnviarATodos%(%s*"([%w_]+)"')
	for nombre in capturas(servidor, 'EnviarACliente%(%s*[%w_%.]+%s*,%s*"([%w_]+)"') do
		envia[nombre] = true
	end
	local enviaCliente = capturas(cliente, 'ServicioRed%.Enviar%(%s*"([%w_]+)"')
	local escuchaCliente = capturas(cliente, 'ServicioRed%.Conectar%(%s*"([%w_]+)"')

	Marco.grupo("Exploración: red", function()
		Marco.prueba("cada remoto que usa el código está declarado y en la dirección correcta", function()
			local comprobaciones = {
				{ escuchaServidor, "el servidor escucha", "ClienteAServidor" },
				{ enviaCliente, "el cliente envía", "ClienteAServidor" },
				{ envia, "el servidor envía", "ServidorACliente" },
				{ escuchaCliente, "el cliente escucha", "ServidorACliente" },
			}
			for _, par in comprobaciones do
				for nombre in par[1] do
					local definicion = Remotos.Definiciones[nombre]
					Marco.distinto(definicion, nil, `{par[2]} '{nombre}', que no está en Remotos`)
					Marco.igual(definicion.Direccion, par[3], `{nombre}: {par[2]} en la dirección equivocada`)
				end
			end
		end)

		Marco.prueba("los remotos que pide el cliente tienen manejador en el servidor y quien los envía", function()
			for _, nombre in DEL_CLIENTE do
				Marco.verdadero(escuchaServidor[nombre], `{nombre}: nadie lo escucha en el servidor`)
				Marco.verdadero(enviaCliente[nombre], `{nombre}: el cliente nunca lo envía`)
			end
		end)

		Marco.prueba("los avisos del servidor se envían y el cliente los escucha", function()
			for _, nombre in DEL_SERVIDOR do
				Marco.verdadero(envia[nombre], `{nombre}: el servidor nunca lo envía`)
				Marco.verdadero(escuchaCliente[nombre], `{nombre}: el cliente no lo escucha`)
			end
		end)

		Marco.prueba("los remotos del cliente tienen límite por segundo y validadores", function()
			for _, nombre in DEL_CLIENTE do
				local definicion = Remotos.Definiciones[nombre]
				Marco.distinto(definicion.Argumentos, nil, `{nombre}: faltan los validadores`)
				Marco.verdadero((definicion.LimitePorSegundo or 0) > 0, `{nombre}: sin límite por segundo`)
				Marco.verdadero(definicion.LimitePorSegundo <= 10, `{nombre}: límite demasiado alto`)
			end
		end)
	end)

	Marco.grupo("Exploración: validación de lo que manda el cliente", function()
		local function valida(nombre: string, ...)
			local ok = Validador.ValidarArgumentos(Remotos.Definiciones[nombre].Argumentos, ...)
			return ok
		end
		local parte = entorno.mundo.Instance.new("Part")

		Marco.prueba("EscanearObjetivo y PicarMineral aceptan una Instancia y nada más", function()
			for _, nombre in { "EscanearObjetivo", "PicarMineral" } do
				Marco.verdadero(valida(nombre, parte), `{nombre}: una Instancia`)
				Marco.falso(valida(nombre, "roca"), `{nombre}: texto`)
				Marco.falso(valida(nombre, 5), `{nombre}: número`)
				Marco.falso(valida(nombre, nil), `{nombre}: nil`)
				Marco.falso(valida(nombre), `{nombre}: sin argumentos`)
				Marco.falso(valida(nombre, parte, parte), `{nombre}: argumentos de más`)
			end
		end)

		Marco.prueba("CancelarEscaneo no lleva argumentos", function()
			Marco.verdadero(valida("CancelarEscaneo"))
			Marco.falso(valida("CancelarEscaneo", 1))
		end)

		Marco.prueba("FabricarReceta solo acepta recetas que existen y cantidades enteras razonables", function()
			for _, id in Recetas.Orden do
				Marco.verdadero(valida("FabricarReceta", id), id)
				Marco.verdadero(valida("FabricarReceta", id, 3), `{id} × 3`)
			end
			Marco.falso(valida("FabricarReceta", "NoExiste"), "receta inventada")
			Marco.falso(valida("FabricarReceta", "LingoteHierro", 0), "cantidad 0")
			Marco.falso(valida("FabricarReceta", "LingoteHierro", -2), "cantidad negativa")
			Marco.falso(valida("FabricarReceta", "LingoteHierro", 1.5), "cantidad decimal")
			Marco.falso(valida("FabricarReceta", "LingoteHierro", Config.CantidadMaximaPorPeticion + 1), "demasiadas")
			Marco.falso(valida("FabricarReceta", "LingoteHierro", 0 / 0), "NaN")
			Marco.falso(valida("FabricarReceta", "LingoteHierro", math.huge), "infinito")
			Marco.falso(valida("FabricarReceta", 7), "id numérico")
			Marco.falso(valida("FabricarReceta"), "sin argumentos")
		end)

		Marco.prueba("una receta nueva en Recetas.Orden se puede pedir sin tocar la red", function()
			-- La lista de ids válidos sale de los datos: añadir una receta no exige cambiar Remotos.
			Marco.igual(#Recetas.Ids(), #Recetas.Orden)
		end)
	end)

	Marco.grupo("Exploración: reglas de seguridad del servidor", function()
		local function contiene(texto: string, fragmento: string, detalle: string)
			Marco.verdadero(string.find(texto, fragmento, 1, true) ~= nil, detalle)
		end
		local minado = fs.readFile("src/server/Servicios/ServicioMinado.luau")
		local escaner = fs.readFile("src/server/Servicios/ServicioEscaner.luau")
		local crafteo = fs.readFile("src/server/Servicios/ServicioCrafteo.luau")

		Marco.prueba("picar comprueba nodo, vida del jugador, nave, distancia, cadencia y espacio", function()
			contiene(minado, "Config.AtributoPilotando", "no se pica dentro de una nave")
			contiene(minado, "Humanoid", "el jugador debe estar vivo")
			contiene(minado, "Config.AlcancePicado", "distancia al mineral")
			contiene(minado, "Config.CadenciaPicado", "cadencia del pico")
			contiene(minado, "CuantoCabe", "espacio en la bodega antes de golpear")
			contiene(minado, "AtributoMineralAgotado", "no se golpea lo agotado")
		end)

		Marco.prueba(
			"escanear comprueba alcance de la mejora, línea de visión, cadencia y vigila mientras dura",
			function()
				contiene(escaner, "AlcanceEscaner", "el alcance sale de la mejora Escáner")
				contiene(escaner, "VelocidadEscaner", "la velocidad sale de la mejora Escáner")
				contiene(escaner, "seVe(", "línea de visión")
				contiene(escaner, "EnfriamientoEscaner", "cadencia del escáner")
				contiene(escaner, "IntervaloVigilanciaEscaner", "vigilancia del escaneo en curso")
				contiene(escaner, "EtiquetaEscaneable", "solo se escanea lo etiquetado")
			end
		)

		Marco.prueba("fabricar exige mesa cercana y cobra con el mismo código que comprueba", function()
			contiene(crafteo, "cercaDeMesa", "hay que estar junto a una mesa")
			contiene(crafteo, "Config.AlcanceMesa", "alcance de la mesa")
			contiene(crafteo, "Crafteo.Planificar", "usa las reglas compartidas")
			contiene(crafteo, "Crafteo.Aplicar", "cobra con las reglas compartidas")
			contiene(crafteo, "AtributoPilotando", "no se fabrica pilotando")
			contiene(crafteo, "GuardarAhora", "una compra se guarda enseguida")
			-- Entre Planificar y Aplicar no debe haber esperas que dejen colarse a otra petición.
			local entre = string.match(crafteo, "Crafteo%.Planificar(.-)Crafteo%.Aplicar") or ""
			Marco.falso(string.find(entre, "task.wait", 1, true) ~= nil, "no puede haber esperas entre medias")
			Marco.falso(string.find(entre, "task.defer", 1, true) ~= nil, "no puede haber esperas entre medias")
		end)

		Marco.prueba("el atributo de piloto coincide con el de las naves", function()
			Marco.igual(Config.AtributoPilotando, ConfigNaves.AtributoPilotando)
		end)

		Marco.prueba("las naves rompen vetas con sus láseres y el botín va al piloto", function()
			local naves = fs.readFile("src/server/Servicios/ServicioNaves/init.luau")
			contiene(naves, "ServicioMinado.PicarDesdeNave(nave.Jugador", "el láser pica el mineral")
		end)

		Marco.prueba("ningún módulo de la exploración modifica el inventario sin pasar por las reglas", function()
			-- El inventario solo se toca con Exploracion/Inventario (Anadir/Quitar) o con Crafteo.Aplicar.
			for _, ruta in
				{
					"src/server/Servicios/ServicioMinado.luau",
					"src/server/Servicios/ServicioEscaner.luau",
					"src/server/Servicios/ServicioCrafteo.luau",
				}
			do
				local texto = fs.readFile(ruta)
				Marco.falso(
					string.find(texto, "Inventario%[[^%]]+%]%s*[%+%-]?=") ~= nil,
					`{ruta}: asigna directamente al inventario`
				)
			end
		end)
	end)
end
