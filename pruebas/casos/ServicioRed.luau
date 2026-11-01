--[[
	Pruebas de ServicioRed (servidor y cliente): creación de los RemoteEvents, límite de peticiones por
	segundo, validación de argumentos, expulsión por abuso y entrega de mensajes en ambos sentidos.
]]

local task = require("@lune/task")

local Entorno = require("../infraestructura/Entorno")

local RUTA_SERVICIO_SERVIDOR = "ServerScriptService.Server.Servicios.ServicioRed"
local RUTA_SERVICIO_CLIENTE = "StarterPlayer.StarterPlayerScripts.Client.Servicios.ServicioRed"

-- Remotos que solo existen en las pruebas. Se insertan en la lista de Red/Remotos.
local REMOTOS_DE_PRUEBA = [[
	PruebaRapida = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 1000,
		Argumentos = { Validador.Entero(0, 10) },
	},
	PruebaLimite = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 5,
		Argumentos = {},
	},
	PruebaTipos = {
		Direccion = "ClienteAServidor",
		LimitePorSegundo = 1000,
		Argumentos = { Validador.Cadena({ MaxLongitud = 10 }), Validador.Opcional(Validador.Booleano()) },
	},
	PruebaAviso = {
		Direccion = "ServidorACliente",
	},
]]

-- Añade remotos de prueba a Red/Remotos. Hay que hacerlo antes de que ningún lado cargue el módulo.
local function agregarRemotos(entorno, codigo: string)
	local modulo = entorno.servidor.buscar("ReplicatedStorage.Shared.Red.Remotos")
	local fuente, cambios = string.gsub(
		modulo.Source,
		"local definiciones: { %[string%]: Definicion } = {\n",
		function(coincidencia)
			return coincidencia .. codigo
		end,
		1
	)
	assert(cambios == 1, "no se encontró dónde insertar los remotos de prueba en Red/Remotos")
	modulo.Source = fuente
end

--[[
	Prepara un servidor con el ServicioRed cargado (todavía sin Iniciar). Devuelve una tabla con:
	  Entorno, Mundo, Red (el ServicioRed del servidor),
	  Remoto(nombre) -> el RemoteEvent, Jugador(userId, nombre) -> jugador que además pasa a ser el local.

	`remotosExtra` es el código de los remotos que se añaden a Red/Remotos: por defecto, los
	REMOTOS_DE_PRUEBA; con "" no se añade ninguno.
]]
local function crearServidor(remotosExtra: string?)
	local entorno = Entorno.nuevo()
	local codigo = if remotosExtra == nil then REMOTOS_DE_PRUEBA else remotosExtra
	if codigo ~= "" then
		agregarRemotos(entorno, codigo)
	end

	local red = entorno.servidor.requerir(RUTA_SERVICIO_SERVIDOR)
	local mundo = entorno.mundo

	local servidor = { Entorno = entorno, Mundo = mundo, Red = red }

	function servidor.Remoto(nombre: string)
		return entorno.game.ReplicatedStorage.Remotos[nombre]
	end

	function servidor.Jugador(userId: number, nombre: string?)
		local jugador = mundo.unirJugador(userId, nombre or `Jugador{userId}`)
		mundo.establecerJugadorLocal(jugador)
		return jugador
	end

	return servidor
end

-- Registra un manejador que anota cada llamada en la lista que devuelve.
local function registrarLlamadas(red, nombre: string)
	local llamadas = {}
	red.Conectar(nombre, function(jugador, ...)
		table.insert(llamadas, { Jugador = jugador, Argumentos = table.pack(...) })
	end)
	return llamadas
end

return function(Marco)
	Marco.grupo("ServicioRed (servidor): creación de remotos", function()
		Marco.prueba(
			"Iniciar crea un RemoteEvent por cada remoto definido, dentro de ReplicatedStorage.Remotos",
			function()
				local servidor = crearServidor()
				Marco.esNil(servidor.Entorno.game.ReplicatedStorage:FindFirstChild("Remotos"), "aún no se ha iniciado")

				servidor.Red.Iniciar()

				local definiciones =
					servidor.Entorno.servidor.requerir("ReplicatedStorage.Shared.Red.Remotos").Definiciones
				local carpeta = servidor.Entorno.game.ReplicatedStorage.Remotos
				local cantidad = 0
				for nombre in definiciones do
					cantidad += 1
					local evento = carpeta:FindFirstChild(nombre)
					Marco.distinto(evento, nil, `falta el RemoteEvent '{nombre}'`)
					Marco.igual(evento.ClassName, "RemoteEvent")
				end
				Marco.igual(#carpeta:GetChildren(), cantidad)
			end
		)

		Marco.prueba("la carpeta se publica con todos los eventos ya dentro", function()
			local servidor = crearServidor()
			local alPublicar
			-- Se mira la carpeta en el mismo instante en que aparece por primera vez en ReplicatedStorage.
			servidor.Entorno.game.ReplicatedStorage.ChildAdded:Connect(function(hijo)
				if hijo.Name == "Remotos" and alPublicar == nil then
					alPublicar = #hijo:GetChildren()
				end
			end)

			servidor.Red.Iniciar()

			local total = #servidor.Entorno.game.ReplicatedStorage.Remotos:GetChildren()
			Marco.distinto(total, 0)
			Marco.igual(alPublicar, total, "al aparecer la carpeta ya debía tener todos los eventos")
		end)

		Marco.prueba("Iniciar solo puede llamarse una vez", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			Marco.lanzaError(servidor.Red.Iniciar, "solo debe llamarse una vez")
		end)

		Marco.prueba("Iniciar falla si un remoto ClienteAServidor no declara sus Argumentos", function()
			local servidor = crearServidor('SinValidar = { Direccion = "ClienteAServidor" },\n')
			Marco.lanzaError(servidor.Red.Iniciar, "SinValidar")
		end)
	end)

	Marco.grupo("ServicioRed (servidor): atención de peticiones", function()
		Marco.prueba("entrega al manejador el jugador y los argumentos ya validados", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaTipos")
			local jugador = servidor.Jugador(1, "Ana")

			servidor.Remoto("PruebaTipos"):FireServer("hola", true)
			Marco.dejarCorrer()

			Marco.igual(#llamadas, 1)
			Marco.igual(llamadas[1].Jugador, jugador)
			Marco.igual(llamadas[1].Argumentos[1], "hola")
			Marco.igual(llamadas[1].Argumentos[2], true)
			Marco.igual(#servidor.Mundo.Avisos, 0)
		end)

		Marco.prueba("descarta las peticiones con argumentos inválidos sin llegar al manejador", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaTipos")
			servidor.Jugador(1, "Ana")
			local remoto = servidor.Remoto("PruebaTipos")

			remoto:FireServer(123) -- tipo equivocado
			remoto:FireServer({ "tabla" }) -- una tabla en lugar de texto
			remoto:FireServer(string.rep("a", 11)) -- demasiado largo
			remoto:FireServer("a", "no es booleano") -- opcional con tipo equivocado
			remoto:FireServer("a", true, "argumento extra") -- argumentos de más
			remoto:FireServer() -- falta el obligatorio
			remoto:FireServer(nil, true) -- nil donde se exige texto
			Marco.dejarCorrer()

			Marco.igual(#llamadas, 0, "ninguna petición inválida debe llegar al manejador")
		end)

		Marco.prueba("acepta el argumento opcional omitido", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaTipos")
			servidor.Jugador(1)

			servidor.Remoto("PruebaTipos"):FireServer("solo texto")
			Marco.dejarCorrer()

			Marco.igual(#llamadas, 1)
		end)

		Marco.prueba("rechaza NaN e infinitos aunque sean números", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaRapida")
			servidor.Jugador(1)
			local remoto = servidor.Remoto("PruebaRapida")

			remoto:FireServer(0 / 0)
			remoto:FireServer(math.huge)
			remoto:FireServer(11)
			remoto:FireServer(5)
			Marco.dejarCorrer()

			Marco.igual(#llamadas, 1)
			Marco.igual(llamadas[1].Argumentos[1], 5)
		end)

		Marco.prueba("copia las tablas: el servidor nunca comparte referencias con el cliente", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			servidor.Jugador(1)
			local original = { 1, 2, 3 }
			local recibido

			servidor.Remoto("PruebaAviso").OnClientEvent:Connect(function(tabla)
				recibido = tabla
			end)
			servidor.Red.EnviarACliente(servidor.Mundo.JugadorLocal, "PruebaAviso", original)
			Marco.dejarCorrer()

			Marco.distinto(recibido, nil)
			Marco.distinto(recibido, original)
			Marco.igualProfundo(recibido, original)
		end)

		Marco.prueba("avisa y descarta una petición que llega antes de registrar el manejador", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			servidor.Jugador(1)

			servidor.Remoto("PruebaTipos"):FireServer("hola")
			Marco.dejarCorrer()

			Marco.algunoContiene(servidor.Mundo.Avisos, "no hay manejador registrado")
		end)

		Marco.prueba("un error en el manejador se registra y no impide atender las siguientes peticiones", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = 0
			servidor.Red.Conectar("PruebaRapida", function(_, numero)
				llamadas += 1
				if numero == 1 then
					error("fallo de la lógica del juego", 0)
				end
			end)
			servidor.Jugador(1)

			servidor.Remoto("PruebaRapida"):FireServer(1)
			servidor.Remoto("PruebaRapida"):FireServer(2)
			Marco.dejarCorrer()

			Marco.igual(llamadas, 2, "la segunda petición debe atenderse aunque la primera fallara")
			Marco.algunoContiene(servidor.Mundo.Avisos, "fallo de la lógica del juego")
			Marco.algunoContiene(servidor.Mundo.Avisos, "PruebaRapida")
			Marco.igual(#servidor.Mundo.Errores, 0, "el error debe quedar contenido, no escapar al hilo")
		end)

		Marco.prueba("ignora lo que envía un jugador que ya salió del juego", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaRapida")
			local jugador = servidor.Jugador(1)

			servidor.Remoto("PruebaRapida"):FireServer(3)
			servidor.Mundo.salirJugador(jugador)
			Marco.dejarCorrer()

			Marco.igual(#llamadas, 0, "la petición llegó cuando el jugador ya no estaba")
		end)
	end)

	Marco.grupo("ServicioRed (servidor): límite de peticiones por segundo", function()
		Marco.prueba("acepta tantas peticiones seguidas como el límite y descarta el resto", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaLimite")
			servidor.Jugador(1)

			for _ = 1, 8 do
				servidor.Remoto("PruebaLimite"):FireServer()
			end
			Marco.dejarCorrer()

			Marco.igual(#llamadas, 5, "el límite de PruebaLimite es 5 por segundo")
		end)

		Marco.prueba("vuelve a aceptar peticiones cuando pasa el tiempo", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaLimite")
			servidor.Jugador(1)

			for _ = 1, 8 do
				servidor.Remoto("PruebaLimite"):FireServer()
			end
			Marco.dejarCorrer()
			servidor.Mundo.avanzarReloj(1)
			for _ = 1, 8 do
				servidor.Remoto("PruebaLimite"):FireServer()
			end
			Marco.dejarCorrer()

			Marco.igual(#llamadas, 10, "5 en el primer segundo y otras 5 en el siguiente")
		end)

		Marco.prueba("cada jugador tiene su propio límite", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaLimite")

			servidor.Jugador(1, "Ana")
			for _ = 1, 8 do
				servidor.Remoto("PruebaLimite"):FireServer()
			end
			servidor.Jugador(2, "Beto")
			for _ = 1, 8 do
				servidor.Remoto("PruebaLimite"):FireServer()
			end
			Marco.dejarCorrer()

			Marco.igual(#llamadas, 10)
		end)

		Marco.prueba("cada remoto tiene su propio límite", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local limitadas = registrarLlamadas(servidor.Red, "PruebaLimite")
			local rapidas = registrarLlamadas(servidor.Red, "PruebaRapida")
			servidor.Jugador(1)

			for _ = 1, 8 do
				servidor.Remoto("PruebaLimite"):FireServer()
			end
			for _ = 1, 8 do
				servidor.Remoto("PruebaRapida"):FireServer(1)
			end
			Marco.dejarCorrer()

			Marco.igual(#limitadas, 5)
			Marco.igual(#rapidas, 8, "agotar un remoto no debe afectar a los demás")
		end)

		Marco.prueba("ElegirBando (el remoto real) solo admite una petición por segundo", function()
			local servidor = crearServidor("")
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "ElegirBando")
			servidor.Jugador(1)

			servidor.Remoto("ElegirBando"):FireServer("Heroes")
			servidor.Remoto("ElegirBando"):FireServer("Villanos")
			Marco.dejarCorrer()
			Marco.igual(#llamadas, 1)

			servidor.Mundo.avanzarReloj(1)
			servidor.Remoto("ElegirBando"):FireServer("Villanos")
			Marco.dejarCorrer()
			Marco.igual(#llamadas, 2)
			Marco.igual(llamadas[2].Argumentos[1], "Villanos")
		end)

		Marco.prueba("al salir el jugador se olvida su límite", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaLimite")

			local primera = servidor.Jugador(1, "Ana")
			for _ = 1, 8 do
				servidor.Remoto("PruebaLimite"):FireServer()
			end
			Marco.dejarCorrer()
			Marco.igual(#llamadas, 5)

			servidor.Mundo.salirJugador(primera)
			servidor.Jugador(1, "Ana") -- vuelve a entrar con el mismo UserId
			for _ = 1, 3 do
				servidor.Remoto("PruebaLimite"):FireServer()
			end
			Marco.dejarCorrer()

			Marco.igual(#llamadas, 8, "el cubo del jugador anterior no debe pasar al nuevo")
		end)
	end)

	Marco.grupo("ServicioRed (servidor): expulsión por abuso", function()
		Marco.prueba("expulsa al jugador que acumula demasiadas peticiones inválidas", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaRapida")
			local jugador = servidor.Jugador(1, "Tramposo")

			for _ = 1, 40 do
				servidor.Remoto("PruebaRapida"):FireServer("no es un número")
			end
			Marco.dejarCorrer()

			Marco.igual(#servidor.Mundo.Expulsiones, 1, "debe expulsarse una sola vez")
			Marco.igual(servidor.Mundo.Expulsiones[1].Jugador, jugador)
			Marco.contiene(servidor.Mundo.Expulsiones[1].Mensaje, "actividad de red anómala")
			Marco.igual(#llamadas, 0)
		end)

		Marco.prueba("también cuenta como infracción superar el límite por segundo", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			registrarLlamadas(servidor.Red, "PruebaLimite")
			servidor.Jugador(1)

			for _ = 1, 60 do
				servidor.Remoto("PruebaLimite"):FireServer()
			end
			Marco.dejarCorrer()

			Marco.igual(#servidor.Mundo.Expulsiones, 1)
		end)

		Marco.prueba("solo se avisa por consola de la primera infracción de cada ventana", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			servidor.Jugador(1)

			for _ = 1, 10 do
				servidor.Remoto("PruebaRapida"):FireServer("mal")
			end
			Marco.dejarCorrer()

			Marco.igual(#servidor.Mundo.Avisos, 1, "diez infracciones no deben producir diez avisos")
			Marco.contiene(servidor.Mundo.Avisos[1], "PruebaRapida")
			Marco.contiene(servidor.Mundo.Avisos[1], "Jugador1")
		end)

		Marco.prueba("las infracciones antiguas no se acumulan con las nuevas", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			servidor.Jugador(1)

			for _ = 1, 25 do
				servidor.Remoto("PruebaRapida"):FireServer("mal")
			end
			Marco.dejarCorrer()
			servidor.Mundo.avanzarReloj(11) -- la ventana de 10 s ya pasó
			for _ = 1, 25 do
				servidor.Remoto("PruebaRapida"):FireServer("mal")
			end
			Marco.dejarCorrer()

			Marco.igual(#servidor.Mundo.Expulsiones, 0, "25 + 25 en ventanas distintas no llega a 30")
			Marco.igual(#servidor.Mundo.Avisos, 2, "cada ventana avisa una vez")
		end)

		Marco.prueba("un cliente legítimo, que no envía nada inválido, nunca es expulsado", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaRapida")
			servidor.Jugador(1)

			for _ = 1, 200 do
				servidor.Remoto("PruebaRapida"):FireServer(3)
			end
			Marco.dejarCorrer()

			Marco.igual(#servidor.Mundo.Expulsiones, 0)
			Marco.igual(#llamadas, 200)
		end)
	end)

	Marco.grupo("ServicioRed (servidor): API de registro y envío", function()
		Marco.prueba("Conectar rechaza remotos desconocidos, de dirección contraria o ya conectados", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()

			Marco.lanzaError(function()
				servidor.Red.Conectar("NoExiste", function() end)
			end, "no está definido")
			Marco.lanzaError(function()
				servidor.Red.Conectar("PruebaAviso", function() end)
			end, "ServidorACliente")

			servidor.Red.Conectar("PruebaRapida", function() end)
			Marco.lanzaError(function()
				servidor.Red.Conectar("PruebaRapida", function() end)
			end, "ya tiene un manejador")
		end)

		Marco.prueba("EnviarACliente y EnviarATodos entregan el mensaje por el remoto indicado", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local jugador = servidor.Jugador(1)
			local recibidos = {}
			servidor.Remoto("PruebaAviso").OnClientEvent:Connect(function(...)
				table.insert(recibidos, table.pack(...))
			end)

			servidor.Red.EnviarACliente(jugador, "PruebaAviso", "uno", 2)
			servidor.Red.EnviarATodos("PruebaAviso", "para todos")
			Marco.dejarCorrer()

			Marco.igual(#recibidos, 2)
			Marco.igual(recibidos[1][1], "uno")
			Marco.igual(recibidos[1][2], 2)
			Marco.igual(recibidos[2][1], "para todos")
			Marco.igual(servidor.Mundo.MensajesAClientes[1].Jugador, jugador)
			Marco.esNil(servidor.Mundo.MensajesAClientes[2].Jugador)
		end)

		Marco.prueba("EnviarACliente rechaza remotos desconocidos o de dirección contraria", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local jugador = servidor.Jugador(1)

			Marco.lanzaError(function()
				servidor.Red.EnviarACliente(jugador, "NoExiste")
			end, "no está definido")
			Marco.lanzaError(function()
				servidor.Red.EnviarACliente(jugador, "PruebaRapida", 1)
			end, "ClienteAServidor")
			Marco.lanzaError(function()
				servidor.Red.EnviarATodos("PruebaRapida", 1)
			end, "ClienteAServidor")
		end)

		Marco.prueba("antes de Iniciar no se puede conectar ni enviar", function()
			local servidor = crearServidor()
			Marco.lanzaError(function()
				servidor.Red.Conectar("PruebaRapida", function() end)
			end, "Iniciar")
		end)
	end)

	Marco.grupo("ServicioRed (cliente)", function()
		-- Prepara servidor y cliente en el mismo mundo, con el jugador local ya dentro.
		local function crearParejaIniciada()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local jugador = servidor.Jugador(1, "Ana")
			local cliente = servidor.Entorno.cliente.requerir(RUTA_SERVICIO_CLIENTE)
			cliente.Iniciar()
			return servidor, cliente, jugador
		end

		Marco.prueba("Iniciar espera a que el servidor publique los remotos", function()
			local servidor = crearServidor()
			local cliente = servidor.Entorno.cliente.requerir(RUTA_SERVICIO_CLIENTE)

			local terminado = false
			task.spawn(function()
				cliente.Iniciar()
				terminado = true
			end)
			Marco.dejarCorrer(5)
			Marco.falso(terminado, "el servidor todavía no ha creado los remotos")

			servidor.Red.Iniciar()
			Marco.esperarHasta(function()
				return terminado
			end, "el cliente debería terminar al publicarse los remotos")
		end)

		Marco.prueba("Iniciar solo puede llamarse una vez", function()
			local _, cliente = crearParejaIniciada()
			Marco.lanzaError(cliente.Iniciar, "solo debe llamarse una vez")
		end)

		Marco.prueba("Enviar hace llegar la petición al manejador del servidor", function()
			local servidor, cliente, jugador = crearParejaIniciada()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaTipos")

			local enviado = cliente.Enviar("PruebaTipos", "hola", false)
			Marco.dejarCorrer()

			Marco.verdadero(enviado)
			Marco.igual(#llamadas, 1)
			Marco.igual(llamadas[1].Jugador, jugador)
			Marco.igual(llamadas[1].Argumentos[1], "hola")
			Marco.igual(llamadas[1].Argumentos[2], false)
		end)

		Marco.prueba("Enviar con argumentos inválidos no envía nada y avisa en el cliente", function()
			local servidor, cliente = crearParejaIniciada()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaTipos")

			local enviado = cliente.Enviar("PruebaTipos", 123)
			Marco.dejarCorrer()

			Marco.falso(enviado)
			Marco.igual(#llamadas, 0)
			Marco.algunoContiene(servidor.Mundo.Avisos, "No se envía 'PruebaTipos'")
			Marco.igual(#servidor.Mundo.Expulsiones, 0)
		end)

		Marco.prueba("el cliente se limita a sí mismo, así que el servidor nunca ve infracciones", function()
			local servidor, cliente = crearParejaIniciada()
			local llamadas = registrarLlamadas(servidor.Red, "PruebaLimite")

			local aceptadas = 0
			for _ = 1, 8 do
				if cliente.Enviar("PruebaLimite") then
					aceptadas += 1
				end
			end
			Marco.dejarCorrer()

			Marco.igual(aceptadas, 5)
			Marco.igual(#llamadas, 5)
			Marco.igual(#servidor.Mundo.Avisos, 0, "el servidor no debería haber descartado nada")
		end)

		Marco.prueba("una llamada inválida no gasta fichas del límite del cliente", function()
			local servidor, cliente = crearParejaIniciada()
			local llamadas = registrarLlamadas(servidor.Red, "ElegirBando")

			cliente.Enviar("ElegirBando", "NoEsUnBando")
			local enviado = cliente.Enviar("ElegirBando", "Heroes")
			Marco.dejarCorrer()

			Marco.verdadero(enviado)
			Marco.igual(#llamadas, 1)
		end)

		Marco.prueba("Conectar recibe los mensajes que envía el servidor", function()
			local servidor, cliente, jugador = crearParejaIniciada()
			local recibidos = {}
			cliente.Conectar("PruebaAviso", function(...)
				table.insert(recibidos, table.pack(...))
			end)

			servidor.Red.EnviarACliente(jugador, "PruebaAviso", "hola", { 1, 2 })
			Marco.dejarCorrer()

			Marco.igual(#recibidos, 1)
			Marco.igual(recibidos[1][1], "hola")
			Marco.igualProfundo(recibidos[1][2], { 1, 2 })
		end)

		Marco.prueba("Enviar y Conectar rechazan remotos desconocidos o de dirección contraria", function()
			local _, cliente = crearParejaIniciada()

			Marco.lanzaError(function()
				cliente.Enviar("NoExiste")
			end, "no está definido")
			Marco.lanzaError(function()
				cliente.Enviar("PruebaAviso")
			end, "ServidorACliente")
			Marco.lanzaError(function()
				cliente.Conectar("PruebaRapida", function() end)
			end, "ClienteAServidor")
		end)

		Marco.prueba("antes de Iniciar no se puede enviar", function()
			local servidor = crearServidor()
			servidor.Red.Iniciar()
			local cliente = servidor.Entorno.cliente.requerir(RUTA_SERVICIO_CLIENTE)
			Marco.lanzaError(function()
				cliente.Enviar("PruebaRapida", 1)
			end, "Iniciar")
		end)
	end)
end
