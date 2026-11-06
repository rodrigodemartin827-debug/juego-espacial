--[[
	Pruebas de integración: se ejecutan los scripts de arranque reales (init.server.luau e init.client.luau)
	y se comprueba de punta a punta que la red, los datos y los servicios trabajan juntos: los datos llegan al
	cliente, el jugador elige bando, y todo se guarda y se libera al salir.
]]

local Entorno = require("../infraestructura/Entorno")
local NubeDatos = require("../infraestructura/NubeDatos")

local RUTA_SERVIDOR = "ServerScriptService.Server"
local RUTA_CLIENTE = "StarterPlayer.StarterPlayerScripts.Client"
local ALMACEN = "DatosJugador"

-- Ejecuta init.server.luau. La zona de pruebas, los asteroides, las naves, la exploración (minería, escáner,
-- crafteo), los planetas (terreno y puertos) y las tiendas construyen un escenario con Part, Terrain,
-- CFrame, etc. y usan la física y la iluminación, que la simulación no tiene, así que se sustituyen por módulos
-- vacíos (la lógica de las naves, de la exploración, de los planetas y de las tiendas tiene sus propias pruebas:
-- Naves, NavesVFX, Exploracion, Planetas y Tiendas).
local function arrancarScriptServidor(entorno)
	for _, nombre in
		{
			"ZonaPruebas",
			"ServicioAsteroides",
			"ServicioNaves",
			"ServicioInventario",
			"ServicioMinado",
			"ServicioEscaner",
			"ServicioCrafteo",
			"ServicioPlanetas",
			"ServicioTiendas",
		}
	do
		entorno.servidor.buscar(`{RUTA_SERVIDOR}.Servicios.{nombre}`).Source = "return { Iniciar = function() end }"
	end
	-- El experimento del planeta redondo (solo Studio) genera terreno: fuera de la simulación.
	entorno.servidor.buscar(`{RUTA_SERVIDOR}.Experimentos.PlanetaRedondo`).Source =
		"return { Iniciar = function() end }"
	entorno.servidor.ejecutarScript(RUTA_SERVIDOR)
end

--[[
	Arranca el servidor completo (init.server.luau) sobre `nube`. Devuelve el entorno y el ServicioDatos del
	servidor. Los tiempos del servicio se acortan para que las pruebas vayan rápido.
]]
local function arrancarServidor(nube, studio: boolean?)
	local entorno = Entorno.nuevo({ Nube = nube, JobId = "servidor-integracion", Studio = studio })

	local ServicioDatos = entorno.servidor.requerir(`{RUTA_SERVIDOR}.Servicios.ServicioDatos`)
	ServicioDatos.Configuracion.IntervaloComprobacion = 0.01
	ServicioDatos.Configuracion.EsperaBloqueo = 0.02
	ServicioDatos.Configuracion.EsperaReintentoInicial = 0.005

	arrancarScriptServidor(entorno)
	return entorno, ServicioDatos
end

--[[
	Arranca el cliente (init.client.luau) del jugador indicado, que pasa a ser el jugador local. Devuelve el
	ServicioDatos y el ServicioRed del cliente.
]]
local function arrancarCliente(entorno, jugador)
	entorno.mundo.establecerJugadorLocal(jugador)
	-- El combate del cliente usa cámara, interfaz y efectos que la simulación no tiene: se sustituye por un módulo vacío.
	entorno.cliente.buscar(`{RUTA_CLIENTE}.Combate.ServicioCombate`).Source = "return { Iniciar = function() end }"
	entorno.cliente.buscar(`{RUTA_CLIENTE}.Naves.ServicioNaves`).Source = "return { Iniciar = function() end }"
	entorno.cliente.buscar(`{RUTA_CLIENTE}.Planetas.ServicioPlanetas`).Source = "return { Iniciar = function() end }"
	entorno.cliente.buscar(`{RUTA_CLIENTE}.Exploracion.ServicioExploracion`).Source =
		"return { Iniciar = function() end }"
	-- La pantalla de elección de bando monta una escena 3D e interfaz: tiene sus propias pruebas (EleccionBando).
	entorno.cliente.buscar(`{RUTA_CLIENTE}.Eleccion.ServicioEleccion`).Source =
		"return { Preparar = function() end, Iniciar = function() end }"
	entorno.cliente.buscar(`{RUTA_CLIENTE}.Experimentos.GravedadPlaneta`).Source = "return { Iniciar = function() end }"
	entorno.cliente.buscar(`{RUTA_CLIENTE}.Tiendas.ServicioTiendas`).Source = "return { Iniciar = function() end }"
	entorno.cliente.ejecutarScript(RUTA_CLIENTE)
	return entorno.cliente.requerir(`{RUTA_CLIENTE}.Servicios.ServicioDatos`),
		entorno.cliente.requerir(`{RUTA_CLIENTE}.Servicios.ServicioRed`)
end

local function leerRegistro(nube, userId: number)
	return nube:Leer(ALMACEN, `Jugador_{userId}`)
end

return function(Marco)
	Marco.grupo("Integración: arranque", function()
		Marco.prueba("el servidor publica los remotos y carga a los jugadores que entran", function()
			local nube = NubeDatos.nueva()
			local entorno, ServicioDatos = arrancarServidor(nube)

			Marco.distinto(entorno.game.ReplicatedStorage:FindFirstChild("Remotos"), nil)
			Marco.algunoContiene(entorno.mundo.Impresiones, "[Servidor] Juego espacial iniciado")

			local jugador = entorno.mundo.unirJugador(1, "Ana")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end, "el jugador debería tener sus datos cargados")
			Marco.igual(#entorno.mundo.Avisos, 0, "un arranque normal no debe producir avisos")
		end)

		Marco.prueba("los jugadores que ya estaban cuando arranca el servidor también se cargan", function()
			local nube = NubeDatos.nueva()
			local entorno = Entorno.nuevo({ Nube = nube })
			local jugador = entorno.mundo.unirJugador(1, "Ana")

			arrancarScriptServidor(entorno)

			local ServicioDatos = entorno.servidor.requerir(`{RUTA_SERVIDOR}.Servicios.ServicioDatos`)
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
		end)
	end)

	Marco.grupo("Integración: datos en el cliente", function()
		Marco.prueba("el cliente recibe sus datos cuando el servidor termina de cargarlos", function()
			local nube = NubeDatos.nueva()
			nube.Latencia = 0.03 -- la carga tarda: el cliente arranca mientras tanto
			local entorno = arrancarServidor(nube)
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			local DatosCliente = arrancarCliente(entorno, jugador)
			Marco.esNil(DatosCliente.Obtener(), "aún no han llegado")

			Marco.esperarHasta(function()
				return DatosCliente.Obtener() ~= nil
			end, "el cliente debería recibir los datos")

			local datos = DatosCliente.Obtener()
			Marco.igual(datos.Bando, "Ninguno")
			Marco.igual(datos.Nivel, 1)
			Marco.algunoContiene(entorno.mundo.Impresiones, "[Cliente] Datos recibidos: bando Ninguno, nivel 1")
		end)

		Marco.prueba("si el servidor los envió antes de que el cliente escuchara, el cliente los pide", function()
			local nube = NubeDatos.nueva()
			local entorno, ServicioDatos = arrancarServidor(nube)
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			Marco.dejarCorrer(5)
			Marco.igual(#entorno.mundo.MensajesAClientes, 1, "el servidor ya envió los datos, a nadie")

			local DatosCliente = arrancarCliente(entorno, jugador)

			Marco.esperarHasta(function()
				return DatosCliente.Obtener() ~= nil
			end, "el cliente debería recibirlos al pedirlos")
		end)

		Marco.prueba("el cliente que arranca antes que el servidor espera a que publique los remotos", function()
			local nube = NubeDatos.nueva()
			local entorno = Entorno.nuevo({ Nube = nube })
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			local DatosCliente = arrancarCliente(entorno, jugador)
			Marco.dejarCorrer(5)
			Marco.esNil(DatosCliente.Obtener())

			arrancarScriptServidor(entorno)

			Marco.esperarHasta(function()
				return DatosCliente.Obtener() ~= nil
			end, "el cliente debería terminar de arrancar y recibir los datos")
		end)

		Marco.prueba("PedirDatos tiene límite: no se puede usar para inundar al servidor", function()
			local nube = NubeDatos.nueva()
			local entorno, ServicioDatos = arrancarServidor(nube)
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			entorno.mundo.establecerJugadorLocal(jugador)
			local enviados = #entorno.mundo.MensajesAClientes

			for _ = 1, 10 do
				entorno.game.ReplicatedStorage.Remotos.PedirDatos:FireServer()
			end
			Marco.dejarCorrer(5)

			Marco.igual(#entorno.mundo.MensajesAClientes - enviados, 2, "solo se atienden 2 peticiones seguidas")
		end)
	end)

	Marco.grupo("Integración: elegir bando", function()
		Marco.prueba("el bando elegido se aplica, se envía al cliente y se guarda enseguida", function()
			local nube = NubeDatos.nueva()
			local entorno, ServicioDatos = arrancarServidor(nube)
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			local DatosCliente, RedCliente = arrancarCliente(entorno, jugador)
			Marco.esperarHasta(function()
				return DatosCliente.Obtener() ~= nil
			end)

			Marco.verdadero(RedCliente.Enviar("ElegirBando", "Humanos"))

			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador).Bando == "Humanos"
			end, "el servidor debería aplicar la elección")
			Marco.esperarHasta(function()
				return DatosCliente.Obtener().Bando == "Humanos"
			end, "el cliente debería recibir los datos actualizados")
			Marco.esperarHasta(function()
				return leerRegistro(nube, 1).Datos.Bando == "Humanos"
			end, "la elección debería guardarse sin esperar a que el jugador salga")
			Marco.distinto(leerRegistro(nube, 1).Bloqueo, nil, "el jugador sigue dentro: el bloqueo se mantiene")
			Marco.algunoContiene(entorno.mundo.Impresiones, "bando Humanos")
		end)

		Marco.prueba("una vez elegido, el bando no se puede cambiar", function()
			local nube = NubeDatos.nueva()
			local entorno, ServicioDatos = arrancarServidor(nube)
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			local DatosCliente, RedCliente = arrancarCliente(entorno, jugador)
			Marco.esperarHasta(function()
				return DatosCliente.Obtener() ~= nil
			end)
			RedCliente.Enviar("ElegirBando", "Humanos")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador).Bando == "Humanos"
			end)

			entorno.mundo.avanzarReloj(1) -- pasa el límite de una elección por segundo
			Marco.verdadero(
				RedCliente.Enviar("ElegirBando", "Monstruos"),
				"la petición es válida y llega al servidor"
			)
			Marco.dejarCorrer(5)

			Marco.igual(ServicioDatos.ObtenerDatos(jugador).Bando, "Humanos")
			Marco.igual(#entorno.mundo.Expulsiones, 0)
		end)

		Marco.prueba("elegir bando antes de que carguen los datos no hace nada", function()
			local nube = NubeDatos.nueva()
			local entorno, ServicioDatos = arrancarServidor(nube)
			-- La carga se queda a medias hasta que la prueba la suelte. Antes se usaba una latencia de
			-- 0,05 s, pero en Windows dejarCorrer(5) ya dura más que eso y los datos llegaban a cargarse.
			nube.Pausada = true
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			local _, RedCliente = arrancarCliente(entorno, jugador)

			RedCliente.Enviar("ElegirBando", "Monstruos") -- llega mientras la carga sigue en curso
			Marco.dejarCorrer(5)
			Marco.esNil(ServicioDatos.ObtenerDatos(jugador), "los datos aún no han cargado")
			nube.Pausada = false

			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			Marco.igual(ServicioDatos.ObtenerDatos(jugador).Bando, "Ninguno")
			Marco.igual(#entorno.mundo.Avisos, 0, "ignorar la petición no debe provocar ningún error")
		end)

		Marco.prueba("un cliente manipulado no puede elegir un bando inventado", function()
			local nube = NubeDatos.nueva()
			local entorno, ServicioDatos = arrancarServidor(nube)
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			entorno.mundo.establecerJugadorLocal(jugador)

			local remoto = entorno.game.ReplicatedStorage.Remotos.ElegirBando
			remoto:FireServer("Piratas") -- no existe
			Marco.dejarCorrer(5)
			entorno.mundo.avanzarReloj(1)
			remoto:FireServer("Ninguno") -- existe, pero no es elegible
			Marco.dejarCorrer(5)
			entorno.mundo.avanzarReloj(1)
			remoto:FireServer({ Bando = "Humanos" }) -- tipo equivocado
			Marco.dejarCorrer(5)

			Marco.igual(ServicioDatos.ObtenerDatos(jugador).Bando, "Ninguno")
			Marco.algunoContiene(entorno.mundo.Avisos, "ElegirBando")
		end)
	end)

	Marco.grupo("Integración: protección mientras se elige bando", function()
		local ATRIBUTO = "EligiendoBando"
		local PROTECCION = "ProteccionEleccion"

		-- Personaje simulado con su HumanoidRootPart, asignado al jugador y anunciado con CharacterAdded.
		local function darPersonaje(entorno, jugador, nombre, anclado)
			local mundo = entorno.mundo
			local modelo = mundo.Instance.new("Model")
			modelo.Name = nombre or jugador.Name
			local raiz = mundo.Instance.new("Part")
			raiz.Name = "HumanoidRootPart"
			raiz.Anchored = anclado == true
			raiz.Parent = modelo
			jugador.Character = modelo
			jugador.CharacterAdded:Fire(modelo)
			return modelo, raiz
		end

		local function protegido(modelo, raiz)
			local escudo = modelo:FindFirstChild(PROTECCION)
			return escudo ~= nil and escudo.ClassName == "ForceField" and escudo.Visible == false and raiz.Anchored
		end

		local function preparar()
			local nube = NubeDatos.nueva()
			local entorno, ServicioDatos = arrancarServidor(nube)
			local ServicioBandos = entorno.servidor.requerir(`{RUTA_SERVIDOR}.Servicios.ServicioBandos`)
			return nube, entorno, ServicioDatos, ServicioBandos
		end

		Marco.prueba("sin bando: el personaje queda quieto, protegido y marcado como eligiendo", function()
			local _, entorno, ServicioDatos, ServicioBandos = preparar()
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			local modelo, raiz = darPersonaje(entorno, jugador) -- el personaje aparece antes de cargar los datos
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			Marco.dejarCorrer(5)

			Marco.verdadero(ServicioBandos.EstaEligiendo(jugador))
			Marco.igual(jugador:GetAttribute(ATRIBUTO), true)
			Marco.verdadero(protegido(modelo, raiz), "debe estar anclado y con ForceField invisible")
		end)

		Marco.prueba("al elegir se quita todo, se avisa al tutorial y no se puede volver a elegir", function()
			local _, entorno, ServicioDatos, ServicioBandos = preparar()
			local elegidos = {}
			ServicioBandos.BandoElegido:Conectar(function(quien, bando)
				table.insert(elegidos, { Jugador = quien, Bando = bando })
			end)
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			local modelo, raiz = darPersonaje(entorno, jugador) -- aparece con los datos ya cargados
			Marco.esperarHasta(function()
				return protegido(modelo, raiz)
			end, "el personaje nuevo también se protege")
			entorno.mundo.establecerJugadorLocal(jugador)
			local remoto = entorno.game.ReplicatedStorage.Remotos.ElegirBando

			remoto:FireServer("Monstruos")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador).Bando == "Monstruos"
			end)
			Marco.esNil(jugador:GetAttribute(ATRIBUTO), "ya no está eligiendo")
			Marco.esNil(modelo:FindFirstChild(PROTECCION), "sin ForceField")
			Marco.falso(raiz.Anchored, "se puede mover")
			Marco.dejarCorrer(5)
			Marco.igual(#elegidos, 1)
			Marco.igual(elegidos[1].Jugador, jugador)
			Marco.igual(elegidos[1].Bando, "Monstruos")

			-- Un cliente manipulado insiste: ni por el remoto ni llamando de nuevo cambia nada.
			entorno.mundo.avanzarReloj(1)
			remoto:FireServer("Humanos")
			Marco.dejarCorrer(5)
			Marco.falso(ServicioBandos.Elegir(jugador, "Humanos"))
			Marco.igual(ServicioDatos.ObtenerDatos(jugador).Bando, "Monstruos")
			Marco.igual(#elegidos, 1, "el tutorial solo empieza una vez")
		end)

		Marco.prueba("dos peticiones seguidas con bandos distintos: solo cuenta la primera", function()
			local _, entorno, ServicioDatos = preparar()
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			entorno.mundo.establecerJugadorLocal(jugador)
			local remoto = entorno.game.ReplicatedStorage.Remotos.ElegirBando
			remoto:FireServer("Humanos")
			remoto:FireServer("Monstruos") -- en el mismo instante: además, el límite es de 1 por segundo
			Marco.dejarCorrer(5)
			Marco.igual(ServicioDatos.ObtenerDatos(jugador).Bando, "Humanos")
		end)

		Marco.prueba("el servidor rechaza bandos inventados aunque se le llame directamente", function()
			local _, entorno, ServicioDatos, ServicioBandos = preparar()
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			for _, malo in { "Ninguno", "Piratas", 3, nil } do
				Marco.falso(ServicioBandos.Elegir(jugador, malo :: any), `aceptó {tostring(malo)}`)
			end
			Marco.igual(ServicioDatos.ObtenerDatos(jugador).Bando, "Ninguno")
			Marco.igual(jugador:GetAttribute(ATRIBUTO), true, "sigue eligiendo")
		end)

		Marco.prueba("quien ya tiene bando entra sin protección ni pantalla", function()
			local nube, entorno, ServicioDatos = preparar()
			nube:Escribir(ALMACEN, "Jugador_1", {
				Version = 2,
				Datos = { Bando = "Humanos", Nivel = 3, XP = 0, Monedas = 10, Inventario = {}, MejorasNave = {} },
			})
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			local modelo, raiz = darPersonaje(entorno, jugador)
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			Marco.dejarCorrer(5)
			Marco.igual(ServicioDatos.ObtenerDatos(jugador).Bando, "Humanos")
			Marco.esNil(jugador:GetAttribute(ATRIBUTO))
			Marco.esNil(modelo:FindFirstChild(PROTECCION))
			Marco.falso(raiz.Anchored)
		end)

		Marco.prueba("si reaparece antes de elegir, el personaje nuevo también queda protegido", function()
			local _, entorno, ServicioDatos = preparar()
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			local primero, raizPrimera = darPersonaje(entorno, jugador, "Primero")
			Marco.esperarHasta(function()
				return protegido(primero, raizPrimera)
			end)
			local segundo, raizSegunda = darPersonaje(entorno, jugador, "Segundo")
			Marco.esperarHasta(function()
				return protegido(segundo, raizSegunda)
			end, "el personaje nuevo debe protegerse")
		end)

		Marco.prueba("no desancla lo que anclara otro sistema", function()
			local _, entorno, ServicioDatos, ServicioBandos = preparar()
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			-- Aparece ya anclado por otro sistema (por ejemplo, una cinemática del servidor).
			local modelo, raiz = darPersonaje(entorno, jugador, nil, true)
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			Marco.dejarCorrer(5)
			Marco.verdadero(ServicioBandos.Elegir(jugador, "Humanos"))
			Marco.verdadero(raiz.Anchored, "no lo ancló este servicio: no le toca soltarlo")
			Marco.esNil(modelo:FindFirstChild(PROTECCION))
		end)

		Marco.prueba("fuera de Studio no se puede reiniciar el bando ni existe el comando", function()
			local _, entorno, ServicioDatos, ServicioBandos = preparar()
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			Marco.verdadero(ServicioBandos.Elegir(jugador, "Humanos"))
			Marco.falso(ServicioBandos.ReiniciarParaPruebas(jugador))
			Marco.igual(ServicioDatos.ObtenerDatos(jugador).Bando, "Humanos")
			Marco.esNil(jugador:GetAttribute(ATRIBUTO))
			Marco.esNil(entorno.game:GetService("TextChatService"):FindFirstChild("ReiniciarBando"))
		end)

		Marco.prueba("en Studio, el comando de chat devuelve al jugador a Ninguno y vuelve a protegerle", function()
			local nube = NubeDatos.nueva()
			local entorno, ServicioDatos = arrancarServidor(nube, true)
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			local modelo, raiz = darPersonaje(entorno, jugador)
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador) ~= nil
			end)
			local ServicioBandos = entorno.servidor.requerir(`{RUTA_SERVIDOR}.Servicios.ServicioBandos`)
			Marco.verdadero(ServicioBandos.Elegir(jugador, "Monstruos"))
			Marco.falso(protegido(modelo, raiz))

			local comando = entorno.game:GetService("TextChatService"):FindFirstChild("ReiniciarBando")
			Marco.distinto(comando, nil, "en Studio debe existir el comando")
			Marco.igual(comando.PrimaryAlias, "/reiniciarbando")
			comando.Triggered:Fire({ UserId = 1 }, "/reiniciarbando")
			Marco.dejarCorrer(5)

			Marco.igual(ServicioDatos.ObtenerDatos(jugador).Bando, "Ninguno")
			Marco.igual(jugador:GetAttribute(ATRIBUTO), true)
			Marco.verdadero(protegido(modelo, raiz), "vuelve a quedar quieto y protegido")
			-- En Studio el almacén lleva «_Studio» detrás (y el experimento del planeta redondo puede cambiar el nombre).
			local almacen = ServicioDatos.Configuracion.NombreAlmacen .. "_Studio"
			Marco.igual(nube:Leer(almacen, "Jugador_1").Datos.Bando, "Ninguno", "se guarda en el acto")
			-- Y puede volver a elegir.
			Marco.verdadero(ServicioBandos.Elegir(jugador, "Humanos"))
		end)
	end)

	Marco.grupo("Integración: salida del jugador", function()
		Marco.prueba("al salir se guarda el progreso, el bando incluido, y se libera el registro", function()
			local nube = NubeDatos.nueva()
			local entorno, ServicioDatos = arrancarServidor(nube)
			local jugador = entorno.mundo.unirJugador(1, "Ana")
			local DatosCliente, RedCliente = arrancarCliente(entorno, jugador)
			Marco.esperarHasta(function()
				return DatosCliente.Obtener() ~= nil
			end)
			RedCliente.Enviar("ElegirBando", "Monstruos")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(jugador).Bando == "Monstruos"
			end)
			ServicioDatos.ObtenerDatos(jugador).Monedas = 250

			entorno.mundo.salirJugador(jugador)

			Marco.esperarHasta(function()
				return leerRegistro(nube, 1).Bloqueo == nil
			end, "el registro debería quedar liberado")
			Marco.igual(leerRegistro(nube, 1).Datos.Bando, "Monstruos")
			Marco.igual(leerRegistro(nube, 1).Datos.Monedas, 250)
		end)

		Marco.prueba("al volver a entrar, el jugador recupera su bando y su progreso", function()
			local nube = NubeDatos.nueva()
			local entorno, ServicioDatos = arrancarServidor(nube)
			local primera = entorno.mundo.unirJugador(1, "Ana")
			local DatosCliente, RedCliente = arrancarCliente(entorno, primera)
			Marco.esperarHasta(function()
				return DatosCliente.Obtener() ~= nil
			end)
			RedCliente.Enviar("ElegirBando", "Humanos")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(primera).Bando == "Humanos"
			end)
			ServicioDatos.ObtenerDatos(primera).Nivel = 4
			entorno.mundo.salirJugador(primera)
			Marco.esperarHasta(function()
				return leerRegistro(nube, 1).Bloqueo == nil
			end)

			local segunda = entorno.mundo.unirJugador(1, "Ana")
			Marco.esperarHasta(function()
				return ServicioDatos.ObtenerDatos(segunda) ~= nil
			end)

			Marco.igual(ServicioDatos.ObtenerDatos(segunda).Bando, "Humanos")
			Marco.igual(ServicioDatos.ObtenerDatos(segunda).Nivel, 4)
		end)
	end)
end
