--[[
	Pruebas de la red y del cableado de las tiendas.

	ServicioTiendas y la animación de la persiana usan Roblox de lleno (Part, CollectionService, ProximityPrompt, sonidos,
	partículas) y la simulación de las pruebas no lo tiene, así que no se ejecutan aquí: eso se revisa en Studio con la
	lista de comprobación (docs/comprobacion-tiendas.md). Lo que sí se comprueba es que estén bien CABLEADOS:

	  - cada remoto que usa el código está declarado en Red/Remotos y en la dirección correcta, y se usa por los dos lados,
	  - lo que manda el cliente se valida (un cliente manipulado no puede mandar basura),
	  - las reglas de seguridad del servidor están en el código (tienda registrada, distancia, nave, reglas compartidas,
	    cobro sin esperas, guardado inmediato, persiana decidida en el servidor),
	  - la persiana: las piezas que construye el servidor son las que busca el cliente, y el cliente no tiene números propios.
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

local DEL_CLIENTE = { "ComprarArticulo" }
local DEL_SERVIDOR = { "ResultadoCompra", "AbrirTienda" }

return function(Marco)
	local entorno = Entorno.nuevo()
	local Remotos = entorno.servidor.requerir("ReplicatedStorage.Shared.Red.Remotos")
	local Validador = entorno.servidor.requerir("ReplicatedStorage.Shared.Red.Validador")
	local Catalogo = entorno.servidor.requerir("ReplicatedStorage.Shared.Tiendas.Datos.Catalogo")
	local Config = entorno.servidor.requerir("ReplicatedStorage.Shared.Tiendas.Config")
	local ConfigNaves = entorno.servidor.requerir("ReplicatedStorage.Shared.Naves.Config")

	local servidor = leer(archivos("src/server/Servicios/ServicioTiendas", {}))
	local cliente = leer(archivos("src/client/Tiendas", {}))

	local escuchaServidor = capturas(servidor, 'ServicioRed%.Conectar%(%s*"([%w_]+)"')
	local envia = capturas(servidor, 'EnviarATodos%(%s*"([%w_]+)"')
	for nombre in capturas(servidor, 'EnviarACliente%(%s*[%w_%.]+%s*,%s*"([%w_]+)"') do
		envia[nombre] = true
	end
	local enviaCliente = capturas(cliente, 'ServicioRed%.Enviar%(%s*"([%w_]+)"')
	local escuchaCliente = capturas(cliente, 'ServicioRed%.Conectar%(%s*"([%w_]+)"')

	local function contiene(texto: string, fragmento: string, detalle: string)
		Marco.verdadero(string.find(texto, fragmento, 1, true) ~= nil, detalle)
	end

	Marco.grupo("Tiendas: red", function()
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

		Marco.prueba("comprar tiene manejador en el servidor y el cliente lo envía", function()
			for _, nombre in DEL_CLIENTE do
				Marco.verdadero(escuchaServidor[nombre], `{nombre}: nadie lo escucha en el servidor`)
				Marco.verdadero(enviaCliente[nombre], `{nombre}: el cliente nunca lo envía`)
			end
		end)

		Marco.prueba("las respuestas del servidor se envían y el cliente las escucha", function()
			for _, nombre in DEL_SERVIDOR do
				Marco.verdadero(envia[nombre], `{nombre}: el servidor nunca lo envía`)
				Marco.verdadero(escuchaCliente[nombre], `{nombre}: el cliente no lo escucha`)
			end
			-- Los avisos cortos van por el canal común de avisos, que el cliente ya escucha (Exploración).
			Marco.verdadero(envia.AvisoExploracion, "los avisos de la tienda usan AvisoExploracion")
		end)

		Marco.prueba("ComprarArticulo tiene límite por segundo bajo y validadores", function()
			local definicion = Remotos.Definiciones.ComprarArticulo
			Marco.distinto(definicion.Argumentos, nil)
			Marco.verdadero((definicion.LimitePorSegundo or 0) > 0 and definicion.LimitePorSegundo <= 6)
		end)
	end)

	Marco.grupo("Tiendas: validación de lo que manda el cliente", function()
		local function valida(...)
			local ok = Validador.ValidarArgumentos(Remotos.Definiciones.ComprarArticulo.Argumentos, ...)
			return ok
		end
		local modelo = entorno.mundo.Instance.new("Model")
		local parte = entorno.mundo.Instance.new("Part")

		Marco.prueba("acepta un modelo, un artículo del catálogo y una cantidad entera razonable", function()
			for _, id in Catalogo.Orden do
				Marco.verdadero(valida(modelo, id), id)
				Marco.verdadero(valida(modelo, id, 3), `{id} × 3`)
			end
			Marco.verdadero(valida(modelo, "Hierro", Config.CantidadMaximaPorPeticion))
		end)

		Marco.prueba("rechaza basura en la tienda", function()
			Marco.falso(valida(parte, "Hierro"), "una Part no es una tienda")
			Marco.falso(valida("MercadoColonia", "Hierro"), "el id en texto")
			Marco.falso(valida(nil, "Hierro"), "sin tienda")
			Marco.falso(valida(), "sin argumentos")
		end)

		Marco.prueba("rechaza artículos inventados y cantidades raras", function()
			Marco.falso(valida(modelo, "NoExiste"), "artículo inventado")
			Marco.falso(valida(modelo, 7), "id numérico")
			Marco.falso(valida(modelo, "Hierro", 0), "cantidad 0")
			Marco.falso(valida(modelo, "Hierro", -2), "negativa")
			Marco.falso(valida(modelo, "Hierro", 1.5), "decimal")
			Marco.falso(valida(modelo, "Hierro", 0 / 0), "NaN")
			Marco.falso(valida(modelo, "Hierro", math.huge), "infinito")
			Marco.falso(valida(modelo, "Hierro", Config.CantidadMaximaPorPeticion + 1), "demasiadas")
			Marco.falso(valida(modelo, "Hierro", 1, true), "argumentos de más")
		end)

		Marco.prueba("un artículo nuevo en Catalogo.Orden se puede pedir sin tocar la red", function()
			-- La lista de ids válidos sale de los datos: añadir un artículo no exige cambiar Remotos.
			contiene(
				fs.readFile("src/shared/Red/Remotos.luau"),
				"Validador.Enumeracion(Catalogo.Orden)",
				"ids del catálogo"
			)
		end)
	end)

	Marco.grupo("Tiendas: reglas de seguridad del servidor", function()
		local servicio = fs.readFile("src/server/Servicios/ServicioTiendas/init.luau")

		Marco.prueba("comprar exige tienda registrada, vivo, a pie y junto al mostrador", function()
			contiene(servicio, "tiendas[tienda :: Model]", "solo vale una tienda registrada por el servidor")
			contiene(servicio, "IsDescendantOf(workspace)", "la tienda está en el mundo")
			contiene(servicio, "Health <= 0", "el jugador debe estar vivo")
			contiene(servicio, "Config.AtributoPilotando", "no se compra dentro de una nave")
			contiene(servicio, "Config.AlcanceTienda * Config.HolguraAlcance", "distancia al mostrador")
		end)

		Marco.prueba("cobra con las reglas compartidas, sin esperas entre comprobar y cobrar, y guarda", function()
			contiene(servicio, "Compras.Planificar", "usa las reglas compartidas")
			contiene(servicio, "Compras.Aplicar", "cobra con las reglas compartidas")
			contiene(servicio, "GuardarAhora", "una compra se guarda enseguida")
			contiene(servicio, "ActualizarMejoras", "una mejora comprada se aplica a la nave en vuelo")
			local entre = string.match(servicio, "Compras%.Planificar(.-)Compras%.Aplicar") or ""
			Marco.verdadero(#entre > 0, "Planificar va antes que Aplicar")
			for _, espera in { "task.wait", "task.defer", "task.delay", ":Wait(", "WaitForChild" } do
				Marco.falso(
					string.find(entre, espera, 1, true) ~= nil,
					`no puede haber esperas entre medias ({espera})`
				)
			end
		end)

		Marco.prueba("la persiana la decide el servidor y también impide vender", function()
			contiene(servicio, "Persiana.Evaluar", "el estado lo calculan las reglas puras")
			contiene(servicio, "SetAttribute(Config.AtributoPersiana", "el servidor publica el estado")
			contiene(servicio, "registro.Estado.Bajada", "la compra usa el estado del servidor, no el del cliente")
			contiene(servicio, "Prompt.Enabled", "con la persiana bajada no se puede usar el mostrador")
			contiene(servicio, "esVetado(jugador)", "al usar el mostrador se comprueba el bando")
		end)

		Marco.prueba("el cliente nunca decide la persiana ni el bando", function()
			local clienteSinComentarios = string.gsub(cliente, "%-%-[^\n]*", "")
			Marco.falso(
				string.find(clienteSinComentarios, "SetAttribute(Config.AtributoPersiana", 1, true) ~= nil,
				"el cliente no escribe el estado de la persiana"
			)
			Marco.falso(string.find(clienteSinComentarios, "Persiana.Evaluar", 1, true) ~= nil)
		end)

		Marco.prueba("el atributo de piloto coincide con el de las naves", function()
			Marco.igual(Config.AtributoPilotando, ConfigNaves.AtributoPilotando)
		end)

		Marco.prueba(
			"ningún módulo de las tiendas modifica el inventario o las monedas sin pasar por las reglas",
			function()
				for _, ruta in archivos("src/server/Servicios/ServicioTiendas", {}) do
					local texto = fs.readFile(ruta)
					Marco.falso(
						string.find(texto, "Inventario%[[^%]]+%]%s*[%+%-]?=") ~= nil,
						`{ruta}: asigna directamente al inventario`
					)
					Marco.falso(string.find(texto, "Monedas%s*[%+%-]?=") ~= nil, `{ruta}: cambia las monedas a mano`)
				end
			end
		)

		Marco.prueba("las ayudas de la zona de pruebas solo existen en Studio", function()
			local zona = fs.readFile("src/server/Servicios/ZonaPruebas.luau")
			local antes, despues = string.find(zona, "if not RunService:IsStudio() then", 1, true)
			Marco.distinto(antes, nil, "las ayudas van detrás de RunService:IsStudio()")
			local cofre = string.find(zona, '"CofreMonedas"', 1, true)
			local olvidar = string.find(zona, '"OlvidarBando"', 1, true)
			Marco.verdadero(cofre ~= nil and cofre > despues, "el cofre de monedas solo en Studio")
			Marco.verdadero(olvidar ~= nil and olvidar > despues, "olvidar bando solo en Studio")
		end)
	end)

	Marco.grupo("Tiendas: piezas de la persiana", function()
		local modelo = fs.readFile("src/server/Servicios/ServicioTiendas/Modelo.luau")
		local persianas = fs.readFile("src/client/Tiendas/Persianas.luau")

		Marco.prueba("el servidor construye las piezas que busca el cliente", function()
			for _, nombre in { '"Origen"', '"Cortina"', '"Cajon"', '"Baliza"', '"Estado"', '"ZonaPolvo"', '"Rotulo"' } do
				contiene(modelo, nombre, `el modelo crea {nombre}`)
				contiene(persianas, nombre, `el cliente usa {nombre}`)
			end
			for _, atributo in { '"Recorrido"', '"AlturaCajon"' } do
				contiene(modelo, atributo, `el modelo publica {atributo}`)
				contiene(persianas, atributo, `el cliente lee {atributo}`)
			end
			contiene(modelo, '"Mostrador"', "el mostrador existe")
			contiene(fs.readFile("src/server/Servicios/ServicioTiendas/init.luau"), '"Mostrador"', "el servidor lo usa")
		end)

		Marco.prueba("el modelo llega entero por streaming (persiana y cajón juntos)", function()
			contiene(modelo, "Enum.ModelStreamingMode.Atomic", "streaming atómico")
		end)

		Marco.prueba("la animación usa las curvas y los datos compartidos, no números propios", function()
			contiene(persianas, "Curvas.Valor(", "la posición sale de Tiendas/Persiana")
			contiene(persianas, "DatosPersiana.Sonidos", "los sonidos salen de Tiendas/Datos/Persiana")
			contiene(persianas, "DatosPersiana.Impacto", "los efectos del impacto salen de los datos")
			Marco.falso(
				string.find(persianas, "rbxasset", 1, true) ~= nil,
				"ningún sonido ni textura escrito en el código"
			)
		end)

		Marco.prueba(
			"rendimiento: movimiento en bloque, partículas según calidad y bucle solo cuando hace falta",
			function()
				contiene(persianas, "BulkMoveTo", "las lamas se mueven de golpe")
				contiene(persianas, 'Calidad.Factor("Particulas")', "partículas según la calidad del dispositivo")
				contiene(persianas, ":Emit(", "emisores reutilizados (Emit), no creados en cada golpe")
				contiene(persianas, "conexionBucle:Disconnect()", "el bucle se apaga cuando no hay nada que animar")
			end
		)
	end)
end
