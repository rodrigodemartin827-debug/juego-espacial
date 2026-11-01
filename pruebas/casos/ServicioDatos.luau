--[[
	Pruebas de ServicioDatos con varios servidores simulados compartiendo una misma NubeDatos: carga,
	guardado, bloqueo de sesión entre servidores, pérdida del bloqueo, fallos del DataStore, datos
	corruptos, migraciones, Studio y cierre del servidor.

	Los tiempos del servicio se acortan (milisegundos) para que las pruebas sean rápidas, y los relojes
	de cada servidor se adelantan a mano con `Mundo.avanzarReloj` para provocar autoguardados y
	bloqueos caducados sin esperar de verdad.
]]

local Entorno = require("../infraestructura/Entorno")
local NubeDatos = require("../infraestructura/NubeDatos")

local RUTA_SERVICIO = "ServerScriptService.Server.Servicios.ServicioDatos"
local ALMACEN = "DatosJugador"

local contadorServidores = 0

--[[
	Crea un servidor simulado con ServicioDatos (iniciado, salvo que se indique `Iniciar = false`).
	Opciones: Config (ajustes de ServicioDatos.Configuracion), Studio, Iniciar.
	Devuelve una tabla con Entorno, Mundo, Servicio, Esquema y JobId.
]]
local function crearServidor(nube, opciones)
	opciones = opciones or {}
	contadorServidores += 1
	local jobId = `servidor-{contadorServidores}`

	local entorno = Entorno.nuevo({ Nube = nube, JobId = jobId, Studio = opciones.Studio })
	local servicio = entorno.servidor.requerir(RUTA_SERVICIO)

	-- Tiempos muy cortos para que las pruebas vayan rápido.
	local configuracion = servicio.Configuracion
	configuracion.IntervaloComprobacion = 0.01
	configuracion.EsperaBloqueo = 0.02
	configuracion.EsperaReintentoInicial = 0.005
	configuracion.EsperaReintentoMaxima = 0.01
	configuracion.EsperaSesionPrevia = 2
	configuracion.TiempoMaximoCierre = 5
	for clave, valor in opciones.Config or {} do
		configuracion[clave] = valor
	end

	local servidor = {
		Entorno = entorno,
		Mundo = entorno.mundo,
		Servicio = servicio,
		Esquema = entorno.servidor.requerir(`{RUTA_SERVICIO}.Esquema`),
		JobId = jobId,
	}
	if opciones.Iniciar ~= false then
		servicio.Iniciar()
	end
	return servidor
end

local function leerRegistro(nube, userId: number)
	return nube:Leer(ALMACEN, `Jugador_{userId}`)
end

return function(Marco)
	-- Espera a que los datos del jugador estén cargados en ese servidor.
	local function esperarCarga(servidor, jugador)
		Marco.esperarHasta(function()
			return servidor.Servicio.ObtenerDatos(jugador) ~= nil
		end, `los datos de {jugador.Name} deberían cargarse en {servidor.JobId}`)
	end

	-- Entra un jugador y espera a que sus datos estén cargados.
	local function entrar(servidor, userId: number, nombre: string?)
		local jugador = servidor.Mundo.unirJugador(userId, nombre or `Jugador{userId}`)
		esperarCarga(servidor, jugador)
		return jugador
	end

	-- Espera a que el registro del jugador exista y no tenga ningún bloqueo.
	local function esperarLiberacion(nube, userId: number)
		Marco.esperarHasta(function()
			local registro = leerRegistro(nube, userId)
			return registro ~= nil and registro.Bloqueo == nil
		end, `el registro de {userId} debería quedar liberado`)
	end

	-- ===== Carga =====

	Marco.grupo("ServicioDatos: carga", function()
		Marco.prueba("un jugador nuevo recibe los datos iniciales y el servidor toma el bloqueo", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)
			local cargados = {}
			servidor.Servicio.DatosCargados:Conectar(function(jugador)
				table.insert(cargados, jugador)
			end)

			local jugador = entrar(servidor, 1, "Ana")

			local datos = servidor.Servicio.ObtenerDatos(jugador)
			Marco.igual(datos.Bando, "Ninguno")
			Marco.igual(datos.Nivel, 1)
			Marco.igual(datos.XP, 0)
			Marco.igual(datos.Monedas, 0)
			Marco.igualProfundo(datos.Inventario, {})
			Marco.igual(datos.MejorasNave.Casco, 0)

			Marco.igual(#cargados, 1, "DatosCargados se dispara una vez")
			Marco.igual(cargados[1], jugador)

			local registro = leerRegistro(nube, 1)
			Marco.igual(registro.Version, 1)
			Marco.igual(registro.Bloqueo.IdServidor, servidor.JobId, "el bloqueo identifica al servidor")
			Marco.igualProfundo(registro.Datos, datos)
		end)

		Marco.prueba("carga los datos de un jugador existente y completa los campos que le faltan", function()
			local nube = NubeDatos.nueva()
			nube:Escribir(ALMACEN, "Jugador_7", {
				Version = 1,
				Datos = { Bando = "Heroes", Nivel = 3, XP = 40, Monedas = 500, Inventario = { hierro = 9 } },
				Meta = { Creado = 1, UltimoGuardado = 2 },
			})
			local servidor = crearServidor(nube)

			local jugador = entrar(servidor, 7)
			local datos = servidor.Servicio.ObtenerDatos(jugador)

			Marco.igual(datos.Bando, "Heroes")
			Marco.igual(datos.Nivel, 3)
			Marco.igual(datos.XP, 40)
			Marco.igual(datos.Monedas, 500)
			Marco.igual(datos.Inventario.hierro, 9)
			Marco.igual(datos.MejorasNave.Motor, 0, "las mejoras que no tenía se rellenan")
			Marco.igual(datos.MejorasNave.Carga, 0, "incluida la mejora Carga, añadida después")
		end)

		Marco.prueba("los datos no están disponibles hasta que terminan de cargarse", function()
			local nube = NubeDatos.nueva()
			nube.Latencia = 0.05
			local servidor = crearServidor(nube)

			local jugador = servidor.Mundo.unirJugador(1)
			Marco.esNil(servidor.Servicio.ObtenerDatos(jugador), "la carga aún está en curso")

			esperarCarga(servidor, jugador)
			Marco.esNil(
				servidor.Servicio.ObtenerDatos(servidor.Mundo.unirJugador(2)),
				"otro jugador no tiene datos hasta que cargan los suyos"
			)
		end)

		Marco.prueba("también carga a los jugadores que ya estaban en el servidor al iniciar el servicio", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube, { Iniciar = false })
			local jugador = servidor.Mundo.unirJugador(1, "Ana")

			servidor.Servicio.Iniciar()

			esperarCarga(servidor, jugador)
			Marco.distinto(leerRegistro(nube, 1).Bloqueo, nil)
		end)

		Marco.prueba("asocia cada registro al UserId del jugador (para poder borrar sus datos)", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)

			entrar(servidor, 4242)

			Marco.igual(#nube.Escrituras, 1)
			Marco.igual(nube.Escrituras[1].Clave, "Jugador_4242")
			Marco.igualProfundo(nube.Escrituras[1].UserIds, { 4242 })
		end)

		Marco.prueba("los jugadores de prueba de Studio (UserId negativo) se guardan sin UserIds asociados", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)

			local jugador = entrar(servidor, -1, "Prueba")
			servidor.Servicio.ObtenerDatos(jugador).Monedas = 3
			servidor.Mundo.salirJugador(jugador)
			esperarLiberacion(nube, -1)

			Marco.verdadero(#nube.Escrituras >= 2, "debe haber cargado y guardado")
			for _, escritura in nube.Escrituras do
				Marco.esNil(escritura.UserIds, "no debe asociar UserIds que no son de usuarios reales")
			end
			Marco.igual(leerRegistro(nube, -1).Datos.Monedas, 3)
		end)

		Marco.prueba("Iniciar solo puede llamarse una vez", function()
			local servidor = crearServidor(NubeDatos.nueva())
			Marco.lanzaError(servidor.Servicio.Iniciar, "solo debe llamarse una vez")
		end)
	end)

	-- ===== Guardado y liberación =====

	Marco.grupo("ServicioDatos: guardado", function()
		Marco.prueba("al salir guarda los datos y libera el bloqueo", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)
			local jugador = entrar(servidor, 1)
			local datos = servidor.Servicio.ObtenerDatos(jugador)
			datos.Monedas = 123
			datos.Inventario.hierro = 4
			datos.MejorasNave.Escudo = 2

			servidor.Mundo.salirJugador(jugador)
			esperarLiberacion(nube, 1)

			local registro = leerRegistro(nube, 1)
			Marco.igual(registro.Datos.Monedas, 123)
			Marco.igual(registro.Datos.Inventario.hierro, 4)
			Marco.igual(registro.Datos.MejorasNave.Escudo, 2)
			Marco.igual(registro.Version, 1)
			Marco.esNil(servidor.Servicio.ObtenerDatos(jugador), "ya no hay datos tras salir")
		end)

		Marco.prueba("SesionFinalizada se dispara una vez y los datos siguen disponibles en ese momento", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)
			local jugador = entrar(servidor, 1)
			servidor.Servicio.ObtenerDatos(jugador).Monedas = 55

			local finalizadas = {}
			servidor.Servicio.SesionFinalizada:Conectar(function(quien)
				local datos = servidor.Servicio.ObtenerDatos(quien)
				table.insert(finalizadas, datos and datos.Monedas)
			end)

			servidor.Mundo.salirJugador(jugador)
			esperarLiberacion(nube, 1)

			Marco.igualProfundo(finalizadas, { 55 })
		end)

		Marco.prueba("un cambio hecho en SesionFinalizada todavía entra en el guardado final", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)
			local jugador = entrar(servidor, 1)
			servidor.Servicio.SesionFinalizada:Conectar(function(quien)
				servidor.Servicio.ObtenerDatos(quien).Monedas = 999 -- último cambio, sin esperas
			end)

			servidor.Mundo.salirJugador(jugador)
			esperarLiberacion(nube, 1)

			Marco.igual(leerRegistro(nube, 1).Datos.Monedas, 999)
		end)

		Marco.prueba("el autoguardado escribe cada cierto tiempo y refresca el bloqueo", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)
			local jugador = entrar(servidor, 1)
			local datos = servidor.Servicio.ObtenerDatos(jugador)
			local escriturasIniciales = #nube.Escrituras

			Marco.esperar(0.1) -- varias comprobaciones del bucle, pero aún no toca guardar
			Marco.igual(#nube.Escrituras, escriturasIniciales, "no debe guardar antes de tiempo")

			datos.Monedas = 50
			servidor.Mundo.avanzarReloj(61)
			Marco.esperarHasta(function()
				return #nube.Escrituras > escriturasIniciales
			end, "debería autoguardar pasado el intervalo")

			local registro = leerRegistro(nube, 1)
			Marco.igual(registro.Datos.Monedas, 50)
			Marco.distinto(registro.Bloqueo, nil, "el jugador sigue en el servidor: el bloqueo se mantiene")
			Marco.verdadero(registro.Bloqueo.UltimaActividad >= os.time() + 60, "y se refresca su marca de tiempo")
		end)

		Marco.prueba("no autoguarda a cada comprobación: respeta el intervalo", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)
			entrar(servidor, 1)
			local escrituras = #nube.Escrituras

			servidor.Mundo.avanzarReloj(61)
			Marco.esperarHasta(function()
				return #nube.Escrituras > escrituras
			end)
			local tras = #nube.Escrituras
			Marco.esperar(0.1) -- muchas comprobaciones más sin que pase otro intervalo
			Marco.igual(#nube.Escrituras, tras)
		end)

		Marco.prueba("GuardarAhora guarda de inmediato y devuelve true", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)
			local jugador = entrar(servidor, 1)
			servidor.Servicio.ObtenerDatos(jugador).Monedas = 77

			Marco.verdadero(servidor.Servicio.GuardarAhora(jugador))

			Marco.igual(leerRegistro(nube, 1).Datos.Monedas, 77)
			Marco.distinto(leerRegistro(nube, 1).Bloqueo, nil, "no libera el bloqueo")
		end)

		Marco.prueba("GuardarAhora devuelve false si el jugador no tiene datos cargados", function()
			local nube = NubeDatos.nueva()
			nube.Latencia = 0.05
			local servidor = crearServidor(nube)
			local jugador = servidor.Mundo.unirJugador(1)

			Marco.falso(servidor.Servicio.GuardarAhora(jugador), "aún está cargando")
			esperarCarga(servidor, jugador)
			servidor.Mundo.salirJugador(jugador)
			Marco.falso(servidor.Servicio.GuardarAhora(jugador), "ya salió")
		end)

		Marco.prueba("dos guardados nunca se solapan, ni siquiera con el guardado final", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)
			local jugador = entrar(servidor, 1)
			nube.Latencia = 0.03

			servidor.Mundo.task.spawn(servidor.Servicio.GuardarAhora, jugador)
			servidor.Mundo.task.spawn(servidor.Servicio.GuardarAhora, jugador)
			Marco.esperar(0.005) -- los guardados siguen en marcha
			servidor.Mundo.salirJugador(jugador)
			esperarLiberacion(nube, 1)

			Marco.igual(nube.MaxEnVuelo, 1, "nunca debe haber dos escrituras a la vez para el mismo jugador")
		end)

		Marco.prueba("repara los datos inválidos antes de guardar: un NaN no impide guardar", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)
			local jugador = entrar(servidor, 1)
			local datos = servidor.Servicio.ObtenerDatos(jugador)
			datos.Monedas = 0 / 0
			datos.Inventario.hierro = -5
			datos.Nivel = 8

			servidor.Mundo.salirJugador(jugador)
			esperarLiberacion(nube, 1)

			local registro = leerRegistro(nube, 1)
			Marco.igual(registro.Datos.Monedas, 0)
			Marco.esNil(registro.Datos.Inventario.hierro)
			Marco.igual(registro.Datos.Nivel, 8, "lo válido se conserva")
			Marco.algunoContiene(servidor.Mundo.Avisos, "repararon")
		end)
	end)

	-- ===== Bloqueo entre servidores =====

	Marco.grupo("ServicioDatos: bloqueo de sesión entre servidores", function()
		Marco.prueba("el segundo servidor espera y carga el progreso del primero cuando éste lo libera", function()
			local nube = NubeDatos.nueva()
			nube.Latencia = 0.005
			local servidorA = crearServidor(nube)
			local servidorB = crearServidor(nube)

			local enA = entrar(servidorA, 1, "Ana")
			servidorA.Servicio.ObtenerDatos(enA).Monedas = 100

			-- El jugador salta al servidor B mientras A todavía lo tiene.
			local enB = servidorB.Mundo.unirJugador(1, "Ana")
			Marco.esperar(0.1) -- B reintenta varias veces
			Marco.esNil(servidorB.Servicio.ObtenerDatos(enB), "B no puede cargarlo mientras A lo tiene")
			Marco.igual(#servidorB.Mundo.Expulsiones, 0, "y tampoco debe expulsarlo todavía")
			Marco.igual(leerRegistro(nube, 1).Bloqueo.IdServidor, servidorA.JobId)

			-- A guarda y libera.
			servidorA.Mundo.salirJugador(enA)
			esperarCarga(servidorB, enB)

			Marco.igual(servidorB.Servicio.ObtenerDatos(enB).Monedas, 100, "B ve el progreso que guardó A")
			Marco.igual(leerRegistro(nube, 1).Bloqueo.IdServidor, servidorB.JobId)
		end)

		Marco.prueba("si el otro servidor no lo libera a tiempo, expulsa al jugador sin escribir nada", function()
			local nube = NubeDatos.nueva()
			local servidorA = crearServidor(nube)
			local servidorB = crearServidor(nube, { Config = { MaxIntentosBloqueo = 3 } })
			entrar(servidorA, 1, "Ana")
			local escrituras = #nube.Escrituras

			local enB = servidorB.Mundo.unirJugador(1, "Ana")
			Marco.esperarHasta(function()
				return #servidorB.Mundo.Expulsiones == 1
			end, "B debería rendirse tras varios intentos")

			Marco.igual(servidorB.Mundo.Expulsiones[1].Jugador, enB)
			Marco.contiene(servidorB.Mundo.Expulsiones[1].Mensaje, "otro servidor")
			Marco.igual(#nube.Escrituras, escrituras, "B no debe escribir nada mientras no tenga el bloqueo")
			Marco.igual(leerRegistro(nube, 1).Bloqueo.IdServidor, servidorA.JobId, "A conserva el bloqueo")
		end)

		Marco.prueba("toma el bloqueo de un servidor caído cuando pasa el tiempo de caducidad", function()
			local nube = NubeDatos.nueva()
			local ahora = os.time()
			nube:Escribir(ALMACEN, "Jugador_1", {
				Version = 1,
				Datos = { Monedas = 321 },
				Bloqueo = {
					IdSesion = "muerta",
					IdServidor = "servidor-caido",
					IdLugar = 1,
					UltimaActividad = ahora - 1000,
				},
				Meta = { Creado = 1, UltimoGuardado = 2 },
			})
			local servidor = crearServidor(nube)

			local jugador = entrar(servidor, 1)

			Marco.igual(servidor.Servicio.ObtenerDatos(jugador).Monedas, 321, "recupera lo último que se guardó")
			Marco.igual(leerRegistro(nube, 1).Bloqueo.IdServidor, servidor.JobId)
			Marco.algunoContiene(servidor.Mundo.Avisos, "bloqueo abandonado")
		end)

		Marco.prueba("respeta el bloqueo de un servidor que ha dado señales de vida hace poco", function()
			local nube = NubeDatos.nueva()
			nube:Escribir(ALMACEN, "Jugador_1", {
				Version = 1,
				Datos = { Monedas = 321 },
				Bloqueo = {
					IdSesion = "viva",
					IdServidor = "otro-servidor",
					IdLugar = 1,
					UltimaActividad = os.time() - 30,
				},
				Meta = { Creado = 1, UltimoGuardado = 2 },
			})
			local servidor = crearServidor(nube, { Config = { MaxIntentosBloqueo = 2 } })

			local jugador = servidor.Mundo.unirJugador(1)
			Marco.esperarHasta(function()
				return #servidor.Mundo.Expulsiones == 1
			end)

			Marco.esNil(servidor.Servicio.ObtenerDatos(jugador))
			Marco.igual(leerRegistro(nube, 1).Bloqueo.IdServidor, "otro-servidor")
		end)

		Marco.prueba(
			"el servidor que pierde el bloqueo no pisa los datos del que lo tiene y expulsa al jugador",
			function()
				local nube = NubeDatos.nueva()
				local servidorA = crearServidor(nube)
				local servidorB = crearServidor(nube)

				local enA = entrar(servidorA, 1, "Ana")
				servidorA.Servicio.ObtenerDatos(enA).Monedas = 10
				local finalizadasA = {}
				servidorA.Servicio.SesionFinalizada:Conectar(function(jugador)
					table.insert(finalizadasA, jugador)
				end)

				-- Desde el reloj de B, A lleva mucho tiempo sin dar señales de vida: B toma el bloqueo.
				servidorB.Mundo.avanzarReloj(400)
				local enB = entrar(servidorB, 1, "Ana")
				servidorB.Servicio.ObtenerDatos(enB).Monedas = 999
				Marco.verdadero(servidorB.Servicio.GuardarAhora(enB))

				-- A sigue creyendo que tiene al jugador y trabaja con datos obsoletos.
				servidorA.Servicio.ObtenerDatos(enA).Monedas = 5
				servidorA.Mundo.avanzarReloj(61) -- toca autoguardar
				Marco.esperarHasta(function()
					return #servidorA.Mundo.Expulsiones == 1
				end, "A debería notar que perdió el bloqueo")

				Marco.contiene(servidorA.Mundo.Expulsiones[1].Mensaje, "otro servidor")
				Marco.esNil(servidorA.Servicio.ObtenerDatos(enA))
				Marco.igual(#finalizadasA, 1, "A avisa de que la sesión terminó")

				local registro = leerRegistro(nube, 1)
				Marco.igual(registro.Datos.Monedas, 999, "los datos de B no se han pisado")
				Marco.igual(registro.Bloqueo.IdServidor, servidorB.JobId)

				-- Cuando el jugador termina de irse de A, tampoco se escribe nada.
				local escrituras = #nube.Escrituras
				Marco.dejarCorrer(5)
				Marco.igual(#nube.Escrituras, escrituras)
			end
		)

		Marco.prueba("si pierde el bloqueo justo al irse, el guardado final tampoco escribe", function()
			local nube = NubeDatos.nueva()
			local servidorA = crearServidor(nube)
			local servidorB = crearServidor(nube)
			local enA = entrar(servidorA, 1, "Ana")

			servidorB.Mundo.avanzarReloj(400)
			local enB = entrar(servidorB, 1, "Ana")
			servidorB.Servicio.ObtenerDatos(enB).Monedas = 999
			servidorB.Servicio.GuardarAhora(enB)

			servidorA.Servicio.ObtenerDatos(enA).Monedas = 5
			servidorA.Mundo.salirJugador(enA)
			Marco.dejarCorrer(5)

			local registro = leerRegistro(nube, 1)
			Marco.igual(registro.Datos.Monedas, 999)
			Marco.igual(registro.Bloqueo.IdServidor, servidorB.JobId)
			Marco.algunoContiene(servidorA.Mundo.Avisos, "ya no estaban bloqueados")
			Marco.igual(#servidorA.Mundo.Expulsiones, 0, "el jugador ya se había ido: no hay a quién expulsar")
		end)

		Marco.prueba("dos servidores cargando a la vez: solo uno obtiene los datos", function()
			local nube = NubeDatos.nueva()
			nube.Latencia = 0.01
			local servidorA = crearServidor(nube)
			local servidorB = crearServidor(nube)

			local enA = servidorA.Mundo.unirJugador(1, "Ana")
			local enB = servidorB.Mundo.unirJugador(1, "Ana")

			-- Durante todo este tiempo nunca deben tener los datos los dos a la vez.
			local ambos = false
			local propietario
			for _ = 1, 30 do
				Marco.esperar(0.005)
				local tieneA = servidorA.Servicio.ObtenerDatos(enA) ~= nil
				local tieneB = servidorB.Servicio.ObtenerDatos(enB) ~= nil
				ambos = ambos or (tieneA and tieneB)
				propietario = propietario or (tieneA and "A") or (tieneB and "B") or nil
			end
			Marco.falso(ambos, "los dos servidores tuvieron los datos a la vez")
			Marco.distinto(propietario, nil, "alguno de los dos debía conseguirlos")

			-- Cuando el dueño se va, el otro los obtiene.
			if propietario == "A" then
				servidorA.Mundo.salirJugador(enA)
				esperarCarga(servidorB, enB)
			else
				servidorB.Mundo.salirJugador(enB)
				esperarCarga(servidorA, enA)
			end
		end)

		Marco.prueba("saltando entre servidores no se pierde ningún cambio (con latencia y fallos al azar)", function()
			local nube = NubeDatos.nueva()
			nube.Latencia = 0.002
			local servidores = { crearServidor(nube), crearServidor(nube), crearServidor(nube) }
			math.randomseed(12345)

			local saltos = 30
			for _ = 1, saltos do
				local servidor = servidores[math.random(1, #servidores)]
				-- De vez en cuando el DataStore falla un par de veces seguidas.
				if math.random() < 0.25 then
					nube.Fallos += 2
				end

				local jugador = entrar(servidor, 1, "Ana")
				servidor.Servicio.ObtenerDatos(jugador).Monedas += 1
				servidor.Mundo.salirJugador(jugador) -- sin esperar a que termine de guardarse
			end

			esperarLiberacion(nube, 1)
			Marco.igual(leerRegistro(nube, 1).Datos.Monedas, saltos, "cada salto sumó una moneda y ninguna se perdió")
			for _, servidor in servidores do
				Marco.igual(#servidor.Mundo.Expulsiones, 0)
			end
		end)
	end)

	-- ===== Reconexión y cierre =====

	Marco.grupo("ServicioDatos: salidas, reconexiones y cierre del servidor", function()
		Marco.prueba("si el jugador se va mientras cargan sus datos, se suelta el bloqueo sin usarlos", function()
			local nube = NubeDatos.nueva()
			nube.Latencia = 0.05
			local servidor = crearServidor(nube)
			local cargados = 0
			servidor.Servicio.DatosCargados:Conectar(function()
				cargados += 1
			end)

			local jugador = servidor.Mundo.unirJugador(1)
			Marco.esperar(0.01) -- la petición de carga está en marcha
			servidor.Mundo.salirJugador(jugador)

			esperarLiberacion(nube, 1)
			Marco.igual(cargados, 0)
			Marco.esNil(servidor.Servicio.ObtenerDatos(jugador))
			Marco.igual(#servidor.Mundo.Expulsiones, 0)
		end)

		Marco.prueba("si se va antes de que empiece la carga, no se llega a tocar el DataStore", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube, { Iniciar = false })
			local viejo = servidor.Mundo.unirJugador(1)
			servidor.Servicio.Iniciar()
			-- Tras Iniciar, el jugador ya se está cargando en otro hilo; si sale de inmediato...
			servidor.Mundo.salirJugador(viejo)
			Marco.dejarCorrer(5)

			local registro = leerRegistro(nube, 1)
			Marco.verdadero(registro == nil or registro.Bloqueo == nil, "no debe quedar ningún bloqueo")
		end)

		Marco.prueba("reconexión rápida del mismo jugador mientras se guarda su sesión anterior", function()
			local nube = NubeDatos.nueva()
			nube.Latencia = 0.02
			local servidor = crearServidor(nube)
			local primera = entrar(servidor, 1, "Ana")
			servidor.Servicio.ObtenerDatos(primera).Monedas = 321

			servidor.Mundo.salirJugador(primera) -- el guardado final tarda un poco...
			local segunda = servidor.Mundo.unirJugador(1, "Ana") -- ...y el jugador ya vuelve a entrar
			esperarCarga(servidor, segunda)

			Marco.igual(servidor.Servicio.ObtenerDatos(segunda).Monedas, 321)
			Marco.esNil(servidor.Servicio.ObtenerDatos(primera), "la instancia anterior no tiene datos")
			Marco.igual(#servidor.Mundo.Expulsiones, 0)
		end)

		Marco.prueba("al cerrar el servidor guarda y libera a todos los jugadores a la vez", function()
			local nube = NubeDatos.nueva()
			nube.Latencia = 0.02
			local servidor = crearServidor(nube)
			for userId = 1, 3 do
				local jugador = entrar(servidor, userId)
				servidor.Servicio.ObtenerDatos(jugador).Monedas = userId * 100
			end
			nube.MaxEnVuelo = 0

			servidor.Entorno.cerrar()

			for userId = 1, 3 do
				local registro = leerRegistro(nube, userId)
				Marco.igual(registro.Datos.Monedas, userId * 100)
				Marco.esNil(registro.Bloqueo, `el jugador {userId} debe quedar liberado`)
			end
			Marco.igual(nube.MaxEnVuelo, 3, "los tres guardados deben ir en paralelo, no uno tras otro")
		end)

		Marco.prueba("al cerrar el servidor, un jugador que aún está cargando no deja el bloqueo tomado", function()
			local nube = NubeDatos.nueva()
			nube.Latencia = 0.05
			local servidor = crearServidor(nube)
			servidor.Mundo.unirJugador(1)
			Marco.esperar(0.01)

			servidor.Entorno.cerrar()

			local registro = leerRegistro(nube, 1)
			Marco.verdadero(registro == nil or registro.Bloqueo == nil, "no debe quedar ningún bloqueo")
		end)

		Marco.prueba("tras cerrar el servidor el bucle de autoguardado se detiene", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube)
			local jugador = entrar(servidor, 1)
			servidor.Entorno.cerrar()
			local peticiones = nube.Peticiones

			servidor.Mundo.avanzarReloj(1000)
			Marco.esperar(0.1)

			Marco.igual(nube.Peticiones, peticiones, "no debe haber más peticiones tras el cierre")
			Marco.esNil(servidor.Servicio.ObtenerDatos(jugador))
		end)
	end)

	-- ===== Fallos del DataStore =====

	Marco.grupo("ServicioDatos: fallos del DataStore", function()
		Marco.prueba("reintenta ante fallos transitorios y acaba cargando los datos", function()
			local nube = NubeDatos.nueva()
			nube.Fallos = 2
			local servidor = crearServidor(nube)

			local jugador = entrar(servidor, 1)

			Marco.distinto(servidor.Servicio.ObtenerDatos(jugador), nil)
			Marco.algunoContiene(servidor.Mundo.Avisos, "intento 1/5 fallido")
			Marco.algunoContiene(servidor.Mundo.Avisos, "intento 2/5 fallido")
			Marco.igual(#servidor.Mundo.Expulsiones, 0)
		end)

		Marco.prueba("si el DataStore falla siempre al cargar, expulsa al jugador en lugar de dejarle jugar", function()
			local nube = NubeDatos.nueva()
			nube.Fallos = 1000
			local servidor = crearServidor(nube, { Config = { MaxIntentosAlmacen = 3 } })

			local jugador = servidor.Mundo.unirJugador(1)
			Marco.esperarHasta(function()
				return #servidor.Mundo.Expulsiones == 1
			end)

			Marco.contiene(servidor.Mundo.Expulsiones[1].Mensaje, "No se pudieron cargar tus datos")
			Marco.esNil(servidor.Servicio.ObtenerDatos(jugador))
			Marco.igual(nube.Peticiones, 3, "debe intentarlo exactamente MaxIntentosAlmacen veces")
		end)

		Marco.prueba(
			"una respuesta perdida al tomar el bloqueo no deja al jugador fuera de su propio registro",
			function()
				local nube = NubeDatos.nueva()
				nube.FallosTrasAplicar = 1 -- el bloqueo se toma, pero el servidor cree que falló
				local servidor = crearServidor(nube)

				local jugador = entrar(servidor, 1)

				Marco.distinto(
					servidor.Servicio.ObtenerDatos(jugador),
					nil,
					"debe reconocer su propio bloqueo al reintentar"
				)
				Marco.igual(#servidor.Mundo.Expulsiones, 0)
				Marco.igual(leerRegistro(nube, 1).Bloqueo.IdServidor, servidor.JobId)
			end
		)

		Marco.prueba(
			"si falla un autoguardado, la sesión sigue activa y se reintenta en el siguiente intervalo",
			function()
				local nube = NubeDatos.nueva()
				local servidor = crearServidor(nube, { Config = { MaxIntentosAlmacen = 2 } })
				local jugador = entrar(servidor, 1)
				servidor.Servicio.ObtenerDatos(jugador).Monedas = 77

				nube.Fallos = 1000
				servidor.Mundo.avanzarReloj(61)
				Marco.esperarHasta(function()
					for _, aviso in servidor.Mundo.Avisos do
						if string.find(aviso, "No se pudo autoguardar", 1, true) then
							return true
						end
					end
					return false
				end, "debería avisar de que no pudo autoguardar")

				Marco.distinto(
					servidor.Servicio.ObtenerDatos(jugador),
					nil,
					"la sesión no se pierde por un fallo transitorio"
				)
				Marco.igual(#servidor.Mundo.Expulsiones, 0)
				Marco.igual(leerRegistro(nube, 1).Datos.Monedas, 0, "todavía no se ha guardado")

				-- El DataStore se recupera y llega el siguiente intervalo.
				nube.Fallos = 0
				servidor.Mundo.avanzarReloj(61)
				Marco.esperarHasta(function()
					return leerRegistro(nube, 1).Datos.Monedas == 77
				end, "el siguiente autoguardado debería escribir los datos")
			end
		)

		Marco.prueba(
			"si el guardado final falla del todo, el bloqueo caduca solo y no se pierde el último guardado",
			function()
				local nube = NubeDatos.nueva()
				local servidorA = crearServidor(nube, { Config = { MaxIntentosAlmacen = 2 } })
				local servidorB = crearServidor(nube)
				local enA = entrar(servidorA, 1)
				servidorA.Servicio.ObtenerDatos(enA).Monedas = 5

				nube.Fallos = 1000
				servidorA.Mundo.salirJugador(enA)
				Marco.esperarHasta(function()
					for _, aviso in servidorA.Mundo.Avisos do
						if string.find(aviso, "se pierde el progreso", 1, true) then
							return true
						end
					end
					return false
				end, "debería avisar de que se pierde el progreso")
				nube.Fallos = 0

				Marco.esNil(servidorA.Servicio.ObtenerDatos(enA))
				Marco.igual(leerRegistro(nube, 1).Bloqueo.IdServidor, servidorA.JobId, "el bloqueo no se pudo soltar")

				-- Pasado el tiempo de caducidad, B puede cargar al jugador con lo último que sí se guardó.
				servidorB.Mundo.avanzarReloj(400)
				local enB = entrar(servidorB, 1)
				Marco.igual(servidorB.Servicio.ObtenerDatos(enB).Monedas, 0)
			end
		)

		Marco.prueba(
			"una respuesta perdida al liberar no se trata como un error: los datos quedan guardados",
			function()
				local nube = NubeDatos.nueva()
				local servidor = crearServidor(nube)
				local jugador = entrar(servidor, 1)
				servidor.Servicio.ObtenerDatos(jugador).Monedas = 8

				nube.FallosTrasAplicar = 1 -- el guardado final se aplica, pero la respuesta se pierde
				servidor.Mundo.salirJugador(jugador)
				esperarLiberacion(nube, 1)
				Marco.dejarCorrer(5)

				Marco.igual(leerRegistro(nube, 1).Datos.Monedas, 8)
				for _, aviso in servidor.Mundo.Avisos do
					Marco.falso(string.find(aviso, "se pierde el progreso", 1, true), "no debe darlo por perdido")
				end
			end
		)
	end)

	-- ===== Datos corruptos y versiones =====

	Marco.grupo("ServicioDatos: registros corruptos y versiones del esquema", function()
		Marco.prueba("un registro corrupto no se sobrescribe: se expulsa al jugador", function()
			local nube = NubeDatos.nueva()
			nube:Escribir(ALMACEN, "Jugador_1", "esto no es un registro")
			local servidor = crearServidor(nube)

			local jugador = servidor.Mundo.unirJugador(1)
			Marco.esperarHasta(function()
				return #servidor.Mundo.Expulsiones == 1
			end)

			Marco.contiene(servidor.Mundo.Expulsiones[1].Mensaje, "soporte")
			Marco.esNil(servidor.Servicio.ObtenerDatos(jugador))
			Marco.igual(leerRegistro(nube, 1), "esto no es un registro")
			Marco.igual(#nube.Escrituras, 0)
		end)

		Marco.prueba("datos de una versión del esquema más nueva no se cargan ni se tocan", function()
			local nube = NubeDatos.nueva()
			local original = { Version = 99, Datos = { Monedas = 5 }, Meta = { Creado = 1, UltimoGuardado = 2 } }
			nube:Escribir(ALMACEN, "Jugador_1", original)
			local servidor = crearServidor(nube)

			servidor.Mundo.unirJugador(1)
			Marco.esperarHasta(function()
				return #servidor.Mundo.Expulsiones == 1
			end)

			Marco.contiene(servidor.Mundo.Expulsiones[1].Mensaje, "versión más reciente")
			Marco.igualProfundo(leerRegistro(nube, 1), original)
			Marco.igual(#nube.Escrituras, 0)
		end)

		Marco.prueba("migra los datos antiguos al cargar y los guarda con la versión actual", function()
			local nube = NubeDatos.nueva()
			nube:Escribir(ALMACEN, "Jugador_1", {
				Version = 1,
				Datos = { Oro = 40, Nivel = 2 },
				Meta = { Creado = 1, UltimoGuardado = 2 },
			})
			local servidor = crearServidor(nube, { Iniciar = false })
			servidor.Esquema.VERSION = 2
			servidor.Esquema.Migraciones[2] = function(datos)
				datos.Monedas = datos.Oro -- el campo Oro pasó a llamarse Monedas
				datos.Oro = nil
			end
			servidor.Servicio.Iniciar()

			local jugador = entrar(servidor, 1)
			Marco.igual(servidor.Servicio.ObtenerDatos(jugador).Monedas, 40)
			Marco.igual(servidor.Servicio.ObtenerDatos(jugador).Nivel, 2)

			servidor.Mundo.salirJugador(jugador)
			esperarLiberacion(nube, 1)
			local registro = leerRegistro(nube, 1)
			Marco.igual(registro.Version, 2)
			Marco.igual(registro.Datos.Monedas, 40)
			Marco.esNil(registro.Datos.Oro)
		end)

		Marco.prueba(
			"si la migración falla, suelta el bloqueo, expulsa al jugador y deja los datos como estaban",
			function()
				local nube = NubeDatos.nueva()
				local original = { Version = 1, Datos = { Oro = 40 }, Meta = { Creado = 1, UltimoGuardado = 2 } }
				nube:Escribir(ALMACEN, "Jugador_1", original)
				local servidor = crearServidor(nube, { Iniciar = false })
				servidor.Esquema.VERSION = 2
				servidor.Esquema.Migraciones[2] = function()
					error("migración defectuosa", 0)
				end
				servidor.Servicio.Iniciar()

				servidor.Mundo.unirJugador(1)
				Marco.esperarHasta(function()
					return #servidor.Mundo.Expulsiones == 1
				end)
				Marco.dejarCorrer(5)

				Marco.contiene(servidor.Mundo.Expulsiones[1].Mensaje, "soporte")
				Marco.algunoContiene(servidor.Mundo.Avisos, "migración defectuosa")
				local registro = leerRegistro(nube, 1)
				Marco.esNil(
					registro.Bloqueo,
					"el bloqueo se libera para que otro servidor (ya corregido) pueda cargarlo"
				)
				Marco.igualProfundo(registro.Datos, original.Datos)
				Marco.igual(registro.Version, 1)
			end
		)
	end)

	-- ===== Studio =====

	Marco.grupo("ServicioDatos: Roblox Studio", function()
		Marco.prueba("en Studio usa un almacén aparte para no mezclar datos de prueba con los reales", function()
			local nube = NubeDatos.nueva()
			local servidor = crearServidor(nube, { Studio = true })

			entrar(servidor, 1)

			Marco.distinto(nube:Leer("DatosJugador_Studio", "Jugador_1"), nil)
			Marco.esNil(nube:Leer("DatosJugador", "Jugador_1"))
		end)

		Marco.prueba("sin acceso al DataStore usa un almacén en memoria y avisa", function()
			local nube = NubeDatos.nueva()
			nube.ErrorAlObtenerAlmacen = "You must publish this place to the web to access DataStore."
			local servidor = crearServidor(nube, { Studio = true })

			local jugador = entrar(servidor, 1)
			servidor.Servicio.ObtenerDatos(jugador).Monedas = 9
			servidor.Mundo.salirJugador(jugador)

			Marco.algunoContiene(servidor.Mundo.Avisos, "almacén en memoria")
			Marco.igual(#nube.Escrituras, 0, "no debe haber tocado el DataStore")

			-- El almacén en memoria funciona como el real: al volver, el jugador recupera sus datos.
			local denuevo = entrar(servidor, 1)
			Marco.igual(servidor.Servicio.ObtenerDatos(denuevo).Monedas, 9)
		end)

		Marco.prueba("si la lectura de prueba del DataStore falla en Studio, también usa memoria", function()
			local nube = NubeDatos.nueva()
			nube.Fallos = 1 -- la primera petición (la lectura de comprobación) falla
			local servidor = crearServidor(nube, { Studio = true })

			entrar(servidor, 1)

			Marco.algunoContiene(servidor.Mundo.Avisos, "almacén en memoria")
			Marco.igual(nube.Peticiones, 1, "tras la comprobación fallida no se vuelve a usar el DataStore")
		end)

		Marco.prueba("fuera de Studio, si no hay DataStore, Iniciar falla en lugar de ocultarlo", function()
			local nube = NubeDatos.nueva()
			nube.ErrorAlObtenerAlmacen = "DataStore no disponible"
			local servidor = crearServidor(nube, { Iniciar = false })

			Marco.lanzaError(servidor.Servicio.Iniciar, "DataStore no disponible")
		end)
	end)
end
