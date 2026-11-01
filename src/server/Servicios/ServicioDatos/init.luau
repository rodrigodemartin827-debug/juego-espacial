--!strict
--[[
	ServicioDatos: carga, guarda y protege los datos de cada jugador en un DataStore, con bloqueo de
	sesión para que nunca los tengan abiertos dos servidores a la vez.

	QUÉ SE GUARDA: bando, nivel, XP, monedas, inventario y mejoras de la nave (ver Esquema y
	Datos/Tipos). Cada jugador tiene un registro con clave "Jugador_<UserId>".

	CÓMO FUNCIONA (las reglas del bloqueo están en BloqueoSesion):
	  - Al entrar un jugador se carga su registro con UpdateAsync, que a la vez TOMA el bloqueo. Si otro
	    servidor lo tiene (porque el jugador acaba de salir de él), se espera y se reintenta. Si tras
	    varios intentos sigue ocupado, o el DataStore falla, se expulsa al jugador con un mensaje
	    claro: es mejor que jugar con datos que luego no se pueden guardar.
	  - Mientras juega, sus datos viven en memoria y se guardan solos cada IntervaloAutoguardado
	    segundos. Cada guardado comprueba que el bloqueo sigue siendo nuestro y lo refresca. Si otro
	    servidor lo ha tomado (p. ej. tras un fallo largo del DataStore), NO se escribe nada, se
	    descartan los cambios sin guardar y se expulsa al jugador: así no se pueden pisar datos ajenos.
	  - Al salir el jugador, o al cerrarse el servidor, se hace un último guardado que además LIBERA el
	    bloqueo para que el siguiente servidor pueda cargarlo sin esperar.
	  - Los datos se concilian con el Esquema al cargar y antes de cada guardado, de modo que siempre
	    cumplen la plantilla y siempre se pueden guardar.
	  - Los fallos del DataStore (límites de peticiones, caídas) se reintentan con espera creciente.

	USO
		ServicioDatos.Iniciar()    -- una sola vez, al arrancar el servidor

		ServicioDatos.DatosCargados:Conectar(function(jugador) ... end)   -- ya hay datos disponibles
		local datos = ServicioDatos.ObtenerDatos(jugador)   -- nil si aún no han cargado
		datos.Monedas += 10                                  -- se modifican directamente y se guardan solos
		ServicioDatos.GuardarAhora(jugador)                  -- para guardar ya (tras una compra, por ejemplo)

	Los datos que devuelve ObtenerDatos son la tabla VIVA: modifícala solo desde el servidor. Para
	enviar una copia al cliente usa el remoto DatosJugador.

	EN STUDIO
	Se usa un almacén aparte ("<NombreAlmacen>_Studio") para no mezclar los datos de prueba con los
	reales. Si el DataStore no está disponible (lugar sin publicar o sin acceso a la API activado en la
	configuración del juego), se usa un almacén en memoria y se avisa por consola.
]]

local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage.Shared
local Senal = require(Shared.Utilidades.Senal)
local Tablas = require(Shared.Utilidades.Tablas)
local Tipos = require(Shared.Datos.Tipos)

local AlmacenMemoria = require(script.AlmacenMemoria)
local BloqueoSesion = require(script.BloqueoSesion)
local Esquema = require(script.Esquema)

type Datos = Tipos.Datos

--[[
	Estados de la sesión de un jugador:
	  Cargando  -> se está tomando el bloqueo y leyendo sus datos.
	  Activa    -> tiene los datos en memoria y el bloqueo; se autoguarda.
	  Liberando -> se está haciendo el guardado final.
	  Terminada -> ya no hay nada que hacer con ella.
]]
type EstadoSesion = "Cargando" | "Activa" | "Liberando" | "Terminada"

type Sesion = {
	Jugador: Player,
	UserId: number,
	Clave: string,
	IdSesion: string, -- identifica esta carga concreta en el bloqueo
	Estado: EstadoSesion,
	Datos: Datos?, -- nil mientras se cargan
	Cancelada: boolean, -- el jugador se fue mientras se cargaban sus datos
	OperacionEnCurso: boolean, -- hay un guardado en marcha: no se solapan
	ProximoGuardado: number, -- os.time() a partir del cual toca autoguardar
}

export type Configuracion = {
	NombreAlmacen: string, -- nombre del DataStore
	IntervaloAutoguardado: number, -- segundos entre guardados de cada jugador (también refresca el bloqueo)
	IntervaloComprobacion: number, -- cada cuántos segundos se revisa a quién le toca autoguardar
	CaducidadBloqueo: number, -- segundos sin refrescarse tras los que un bloqueo se da por abandonado
	EsperaBloqueo: number, -- segundos entre intentos cuando otro servidor tiene el bloqueo
	MaxIntentosBloqueo: number, -- intentos de cargar antes de rendirse si sigue ocupado
	MaxIntentosAlmacen: number, -- intentos por cada operación del DataStore ante errores
	EsperaReintentoInicial: number, -- espera tras el primer error; se duplica en cada reintento
	EsperaReintentoMaxima: number, -- tope de la espera entre reintentos
	EsperaSesionPrevia: number, -- segundos que se espera a que termine de liberarse una sesión anterior del mismo usuario
	TiempoMaximoCierre: number, -- segundos que se esperan los guardados al cerrar el servidor (Roblox da 30)
}

local ServicioDatos = {}

--[[
	Ajustes. Se leen en el momento de usarse, así que se pueden cambiar antes de llamar a Iniciar.

	CaducidadBloqueo debe ser MUCHO mayor que IntervaloAutoguardado: un servidor vivo refresca su bloqueo
	cada IntervaloAutoguardado segundos, y si el DataStore falla durante un rato no debe perderlo.
	Tras la caída de un servidor, sus jugadores no podrán entrar en otro hasta que pase ese tiempo.
]]
ServicioDatos.Configuracion = {
	NombreAlmacen = "DatosJugador",
	IntervaloAutoguardado = 60,
	IntervaloComprobacion = 5,
	CaducidadBloqueo = 300,
	EsperaBloqueo = 4,
	MaxIntentosBloqueo = 10,
	MaxIntentosAlmacen = 5,
	EsperaReintentoInicial = 1,
	EsperaReintentoMaxima = 8,
	EsperaSesionPrevia = 30,
	TiempoMaximoCierre = 25,
} :: Configuracion

-- Se dispara (con el jugador) cuando sus datos ya están cargados y disponibles con ObtenerDatos.
ServicioDatos.DatosCargados = Senal.nueva()

-- Se dispara (con el jugador) justo antes del guardado final, o al perder el bloqueo. Es la última
-- oportunidad para modificar sus datos (hazlo sin esperar) o para limpiar lo que dependa de ellos.
ServicioDatos.SesionFinalizada = Senal.nueva()

local MENSAJES = {
	Ocupado = "Tus datos siguen abiertos en otro servidor. Espera unos segundos e inténtalo de nuevo.",
	Error = "No se pudieron cargar tus datos. Inténtalo de nuevo en unos minutos.",
	Corrupto = "Tus datos no se pueden cargar. Contacta con el soporte del juego.",
	VersionFutura = "Tus datos pertenecen a una versión más reciente del juego. Inténtalo de nuevo en unos minutos.",
	SesionPerdida = "Tu sesión se abrió en otro servidor, por lo que esta se ha cerrado.",
}

-- Identifica a este servidor en el bloqueo. En Studio JobId está vacío, así que se inventa uno.
local ID_SERVIDOR = if game.JobId ~= "" then game.JobId else HttpService:GenerateGUID(false)

local almacen: any = nil
local iniciado = false
local apagando = false
local sesiones: { [number]: Sesion } = {} -- por UserId
local presentes: { [Player]: boolean } = {} -- jugadores que están ahora mismo en el servidor

-- ===== Acceso al DataStore =====

--[[
	Ejecuta UpdateAsync sobre la clave de la sesión, reintentando con espera creciente si falla.

	`transformar` recibe el registro actual y devuelve el nuevo, o nil para no escribir nada. Roblox puede
	llamarla varias veces y no permite que ceda el hilo, así que solo debe mirar el registro y asignar
	resultados a variables locales (que cada llamada vuelve a asignar).

	Devuelve true si la operación se completó (aunque `transformar` decidiera no escribir) o false y el
	último error si se agotaron los intentos.
]]
local function actualizarRegistro(
	sesion: Sesion,
	operacion: string,
	transformar: (registro: any) -> any
): (boolean, string)
	local cfg = ServicioDatos.Configuracion
	local espera = cfg.EsperaReintentoInicial
	local ultimoError = ""

	for intento = 1, cfg.MaxIntentosAlmacen do
		local ok, errorAlmacen = pcall(function()
			almacen:UpdateAsync(sesion.Clave, function(registro: any)
				local nuevo = transformar(registro)
				if nuevo == nil then
					return nil
				end
				-- Asociar el registro al UserId permite borrarlo si el jugador pide eliminar sus datos (RGPD).
				return nuevo, { sesion.UserId }
			end)
		end)

		if ok then
			return true, ""
		end

		ultimoError = tostring(errorAlmacen)
		warn(
			`[Datos] {operacion} de {sesion.Jugador.Name}: intento {intento}/{cfg.MaxIntentosAlmacen} fallido: {ultimoError}`
		)
		if intento < cfg.MaxIntentosAlmacen then
			task.wait(espera)
			espera = math.min(espera * 2, cfg.EsperaReintentoMaxima)
		end
	end

	return false, ultimoError
end

-- Quita la sesión de la lista (si sigue siendo la vigente) y la da por terminada.
local function eliminarSesion(sesion: Sesion)
	sesion.Estado = "Terminada"
	if sesiones[sesion.UserId] == sesion then
		sesiones[sesion.UserId] = nil
	end
end

-- Suelta el bloqueo sin tocar los datos guardados. Se usa cuando se tomó el bloqueo pero los datos
-- nunca llegaron a usarse. Si no se consigue, el bloqueo caducará solo.
local function soltarBloqueo(sesion: Sesion)
	local completado = actualizarRegistro(sesion, "Liberar el bloqueo", function(registro)
		local _, nuevo = BloqueoSesion.Soltar(registro, sesion.IdSesion)
		return nuevo
	end)
	if not completado then
		warn(`[Datos] No se pudo liberar el bloqueo de {sesion.Jugador.Name}; caducará solo en unos minutos`)
	end
end

local function crearBloqueo(sesion: Sesion): BloqueoSesion.Bloqueo
	return {
		IdSesion = sesion.IdSesion,
		IdServidor = ID_SERVIDOR,
		IdLugar = game.PlaceId,
		UltimaActividad = os.time(),
	}
end

-- ===== Carga =====

type ResultadoCarga = "Ok" | "Cancelada" | "Ocupado" | "Error" | "Corrupto" | "VersionFutura"

-- Intenta tomar el bloqueo y leer el registro, esperando si lo tiene otro servidor. Devuelve el
-- resultado y, si es "Ok", el registro leído.
local function tomarBloqueo(sesion: Sesion): (ResultadoCarga, any)
	local cfg = ServicioDatos.Configuracion
	local avisado = false

	for _ = 1, cfg.MaxIntentosBloqueo do
		if sesion.Cancelada then
			return "Cancelada", nil
		end

		local resultado: BloqueoSesion.ResultadoTomar = "Corrupto"
		local registroNuevo: any = nil
		local dueno: BloqueoSesion.Bloqueo? = nil

		local completado, errorAlmacen = actualizarRegistro(sesion, "Cargar los datos", function(registro)
			local r, nuevo, propietario = BloqueoSesion.Tomar(registro, crearBloqueo(sesion), os.time(), {
				Version = Esquema.VERSION,
				CrearDatos = Esquema.Nuevo,
				Caducidad = cfg.CaducidadBloqueo,
			})
			resultado, registroNuevo, dueno = r, nuevo, propietario
			return nuevo
		end)

		if not completado then
			warn(`[Datos] No se pudieron cargar los datos de {sesion.Jugador.Name}: {errorAlmacen}`)
			return "Error", nil
		end

		if resultado == "Ocupado" then
			if not avisado then
				avisado = true
				local servidor = if dueno then dueno.IdServidor else "desconocido"
				print(`[Datos] Los datos de {sesion.Jugador.Name} los tiene el servidor {servidor}; se espera`)
			end
			task.wait(cfg.EsperaBloqueo)
		elseif resultado == "Corrupto" or resultado == "VersionFutura" then
			warn(`[Datos] El registro de {sesion.Jugador.Name} no se puede cargar: {resultado} (clave {sesion.Clave})`)
			return resultado, nil
		else
			if resultado == "TomadoPorCaducidad" then
				warn(`[Datos] Se tomó el bloqueo abandonado de {sesion.Jugador.Name}`)
			end
			return "Ok", registroNuevo
		end
	end

	return "Ocupado", nil
end

-- Expulsa a un jugador cuyos datos no se pudieron cargar y descarta su sesión.
local function rechazarJugador(sesion: Sesion, mensaje: string)
	eliminarSesion(sesion)
	sesion.Jugador:Kick(mensaje)
end

local function cargarJugador(jugador: Player)
	local cfg = ServicioDatos.Configuracion
	local userId = jugador.UserId

	-- Reconexión rápida: si este mismo usuario acaba de salir y su sesión anterior aún se está guardando
	-- en este servidor, se espera a que termine para no confundir ambas.
	local previa = sesiones[userId]
	if previa ~= nil then
		local limite = os.clock() + cfg.EsperaSesionPrevia
		while sesiones[userId] == previa and os.clock() < limite do
			task.wait(0.1)
		end
	end
	if not presentes[jugador] then
		return -- se fue mientras esperaba
	end

	local sesion: Sesion = {
		Jugador = jugador,
		UserId = userId,
		Clave = `Jugador_{userId}`,
		IdSesion = HttpService:GenerateGUID(false),
		Estado = "Cargando",
		Datos = nil,
		Cancelada = false,
		OperacionEnCurso = false,
		ProximoGuardado = 0,
	}
	sesiones[userId] = sesion

	local resultado, registro = tomarBloqueo(sesion)

	if resultado == "Cancelada" then
		eliminarSesion(sesion)
		return
	elseif resultado ~= "Ok" then
		rechazarJugador(sesion, MENSAJES[resultado])
		return
	end

	-- Se tiene el bloqueo. Si el jugador se fue mientras tanto, se suelta sin tocar nada.
	if sesion.Cancelada then
		soltarBloqueo(sesion)
		eliminarSesion(sesion)
		return
	end

	local preparados, datosOError = pcall(function(): Datos
		local datos = Tablas.CopiaProfunda(registro.Datos)
		Esquema.Migrar(datos, registro.Version)
		local conciliados, reparaciones = Esquema.Conciliar(datos)
		if reparaciones > 0 then
			warn(`[Datos] Se repararon {reparaciones} valores inválidos en los datos de {jugador.Name}`)
		end
		return conciliados
	end)

	if not preparados then
		warn(`[Datos] Falló la migración de los datos de {jugador.Name}: {datosOError}`)
		soltarBloqueo(sesion)
		rechazarJugador(sesion, MENSAJES.Corrupto)
		return
	end

	sesion.Datos = datosOError :: any
	sesion.Estado = "Activa"
	sesion.ProximoGuardado = os.time() + cfg.IntervaloAutoguardado
	ServicioDatos.DatosCargados:Disparar(jugador)
end

-- ===== Guardado y liberación =====

type ResultadoGuardado = "Guardado" | "BloqueoPerdido" | "Error"

--[[
	Escribe los datos de la sesión en el DataStore comprobando que el bloqueo sigue siendo suyo.
	Con `liberar` además suelta el bloqueo (guardado final).
]]
local function guardar(sesion: Sesion, liberar: boolean): ResultadoGuardado
	local datos = sesion.Datos
	if datos == nil then
		return "Error"
	end

	sesion.OperacionEnCurso = true

	local resultado: BloqueoSesion.ResultadoGuardar = "BloqueoPerdido"
	local reparaciones = 0
	local completado = actualizarRegistro(
		sesion,
		if liberar then "Guardado final" else "Autoguardado",
		function(registro)
			-- Se concilian los datos justo antes de escribir: un NaN o un valor inválido haría fallar el guardado.
			local _, reparados = Esquema.Conciliar(datos)
			reparaciones = reparados

			local r, nuevo =
				BloqueoSesion.Guardar(registro, sesion.IdSesion, datos, os.time(), Esquema.VERSION, liberar)
			resultado = r
			return nuevo
		end
	)

	sesion.OperacionEnCurso = false

	if reparaciones > 0 then
		warn(
			`[Datos] Se repararon {reparaciones} valores inválidos antes de guardar los datos de {sesion.Jugador.Name}`
		)
	end
	if not completado then
		return "Error"
	end
	return resultado
end

-- La sesión ha perdido el bloqueo: otro servidor tiene los datos. No se escribe nada más y se expulsa.
local function perderSesion(sesion: Sesion)
	if sesion.Estado ~= "Activa" then
		return
	end

	warn(
		`[Datos] {sesion.Jugador.Name} perdió el bloqueo de sus datos (otro servidor lo tomó): se descartan sus cambios sin guardar`
	)
	ServicioDatos.SesionFinalizada:Disparar(sesion.Jugador)
	eliminarSesion(sesion)
	sesion.Jugador:Kick(MENSAJES.SesionPerdida)
end

local function autoguardar(sesion: Sesion)
	local resultado = guardar(sesion, false)

	-- Tanto si sale bien como si no, el siguiente intento es dentro de un intervalo completo: así un
	-- DataStore caído no se ve bombardeado con peticiones.
	sesion.ProximoGuardado = os.time() + ServicioDatos.Configuracion.IntervaloAutoguardado

	if resultado == "BloqueoPerdido" then
		perderSesion(sesion)
	elseif resultado == "Error" then
		warn(`[Datos] No se pudo autoguardar a {sesion.Jugador.Name}; se reintentará en el próximo intervalo`)
	end
end

-- Hace el guardado final de la sesión, libera el bloqueo y la da por terminada.
local function liberarSesion(sesion: Sesion)
	if sesion.Estado ~= "Activa" then
		return -- ya se está liberando, o se perdió
	end
	sesion.Estado = "Liberando"
	ServicioDatos.SesionFinalizada:Disparar(sesion.Jugador)

	-- Si hay un autoguardado en marcha, se espera a que termine para no solapar escrituras.
	while sesion.OperacionEnCurso do
		task.wait(0.05)
	end

	local resultado = guardar(sesion, true)
	if resultado == "Error" then
		warn(
			`[Datos] No se pudo guardar ni liberar los datos de {sesion.Jugador.Name}: se pierde el progreso desde el último guardado y el bloqueo caducará solo`
		)
	elseif resultado == "BloqueoPerdido" then
		warn(
			`[Datos] Los datos de {sesion.Jugador.Name} ya no estaban bloqueados por este servidor: no se escribió nada`
		)
	end

	eliminarSesion(sesion)
end

-- ===== Eventos de Roblox =====

local function alEntrarJugador(jugador: Player)
	presentes[jugador] = true
	cargarJugador(jugador)
end

local function alSalirJugador(jugador: Player)
	presentes[jugador] = nil

	local sesion = sesiones[jugador.UserId]
	if sesion == nil or sesion.Jugador ~= jugador then
		return
	end

	if sesion.Estado == "Cargando" then
		-- La carga en curso lo notará y soltará el bloqueo si llega a tomarlo.
		sesion.Cancelada = true
	elseif sesion.Estado == "Activa" then
		liberarSesion(sesion)
	end
end

-- Cada IntervaloComprobacion segundos, autoguarda a quien le toque.
local function bucleAutoguardado()
	while not apagando do
		task.wait(ServicioDatos.Configuracion.IntervaloComprobacion)
		if apagando then
			break
		end

		local ahora = os.time()
		for _, sesion in table.clone(sesiones) do
			if sesion.Estado == "Activa" and not sesion.OperacionEnCurso and ahora >= sesion.ProximoGuardado then
				task.spawn(autoguardar, sesion)
			end
		end
	end
end

-- Al cerrarse el servidor: guarda y libera a todos a la vez, dentro del tiempo que da Roblox.
local function alCerrarServidor()
	apagando = true

	for _, sesion in table.clone(sesiones) do
		if sesion.Estado == "Cargando" then
			sesion.Cancelada = true
		elseif sesion.Estado == "Activa" then
			task.spawn(liberarSesion, sesion)
		end
	end

	local limite = os.clock() + ServicioDatos.Configuracion.TiempoMaximoCierre
	while next(sesiones) ~= nil and os.clock() < limite do
		task.wait(0.1)
	end
	if next(sesiones) ~= nil then
		warn("[Datos] El servidor se cierra con sesiones sin guardar del todo")
	end
end

-- Elige el DataStore: el real, o uno en memoria si en Studio no está disponible.
local function crearAlmacen(): any
	local esStudio = RunService:IsStudio()
	local nombre = ServicioDatos.Configuracion.NombreAlmacen
	if esStudio then
		nombre ..= "_Studio" -- no se mezclan los datos de prueba con los reales
	end

	local ok, resultado = pcall(function()
		local datastore = DataStoreService:GetDataStore(nombre)
		if esStudio then
			-- Una lectura de prueba: falla si el lugar no está publicado o no hay acceso a la API.
			datastore:GetAsync("__comprobacion")
		end
		return datastore
	end)

	if ok then
		return resultado
	end
	if esStudio then
		warn(
			`[Datos] El DataStore no está disponible en Studio ({resultado}). Se usa un almacén en memoria: los datos se perderán al detener la prueba. Para probar con el DataStore real, publica el lugar y activa "Enable Studio Access to API Services" en la configuración del juego`
		)
		return AlmacenMemoria.nuevo()
	end
	error(`[Datos] No se pudo obtener el DataStore '{nombre}': {resultado}`)
end

-- ===== API pública =====

--[[
	Arranca el servicio: elige el DataStore, carga a los jugadores que ya estén en el servidor y a los
	que lleguen, y programa el autoguardado y el guardado al cerrar. Debe llamarse una sola vez.
]]
function ServicioDatos.Iniciar()
	assert(not iniciado, "ServicioDatos.Iniciar() solo debe llamarse una vez")
	iniciado = true
	almacen = crearAlmacen()

	Players.PlayerAdded:Connect(alEntrarJugador)
	Players.PlayerRemoving:Connect(alSalirJugador)
	game:BindToClose(alCerrarServidor)

	for _, jugador in Players:GetPlayers() do
		task.spawn(alEntrarJugador, jugador)
	end
	task.spawn(bucleAutoguardado)
end

--[[
	Devuelve los datos del jugador (la tabla viva, no una copia), o nil si todavía no se han cargado, si
	la carga falló o si ya terminó su sesión. Durante la señal SesionFinalizada aún están disponibles.
]]
function ServicioDatos.ObtenerDatos(jugador: Player): Datos?
	local sesion = sesiones[jugador.UserId]
	if sesion == nil or sesion.Jugador ~= jugador then
		return nil
	end
	if sesion.Estado == "Activa" or sesion.Estado == "Liberando" then
		return sesion.Datos
	end
	return nil
end

--[[
	Guarda ya los datos del jugador, sin esperar al autoguardado. Úsalo tras cambios importantes que no
	deban perderse si el servidor falla (una compra, subir de nivel...). Cede el hilo hasta terminar.
	Devuelve true si se guardó. No hay que abusar: cada guardado es una petición al DataStore.
]]
function ServicioDatos.GuardarAhora(jugador: Player): boolean
	local sesion = sesiones[jugador.UserId]
	if sesion == nil or sesion.Jugador ~= jugador or sesion.Estado ~= "Activa" then
		return false
	end

	-- Si ya hay un guardado en marcha se espera a que acabe, para no solaparlos.
	while sesion.OperacionEnCurso do
		task.wait(0.05)
	end
	if sesion.Estado ~= "Activa" then
		return false -- mientras esperaba, la sesión terminó
	end

	local resultado = guardar(sesion, false)
	if resultado == "BloqueoPerdido" then
		perderSesion(sesion)
	elseif resultado == "Guardado" then
		sesion.ProximoGuardado = os.time() + ServicioDatos.Configuracion.IntervaloAutoguardado
	end
	return resultado == "Guardado"
end

return ServicioDatos
