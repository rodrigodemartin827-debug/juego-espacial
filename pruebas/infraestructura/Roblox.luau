--[[
	Roblox: simulación mínima de la API de Roblox para ejecutar los módulos de `src/` fuera de Studio.

	Solo implementa lo que usa este proyecto. Si un módulo llama a algo que no está aquí, la prueba
	falla con "attempt to call a nil value" y basta con añadirlo.

	Cada llamada a `Roblox.nuevoMundo` crea un `game` independiente (un servidor, o un servidor con su
	cliente). Varios mundos pueden compartir una NubeDatos, como los servidores reales comparten el
	DataStore.

	Fidelidad con la realidad que se ha querido conservar:
	  - Los eventos de Roblox ejecutan cada manejador en su propio hilo.
	  - Los RemoteEvents entregan los mensajes de forma diferida (no en la misma llamada) y copian las
	    tablas que se envían, de modo que servidor y cliente nunca comparten referencias.
	  - Al salir un jugador, PlayerRemoving se dispara cuando el jugador aún está dentro de Players.
	  - Player:Kick lo expulsa de forma asíncrona.
]]

local task = require("@lune/task")

local Roblox = {}

-- Contador compartido por todos los mundos para que los GUID generados no se repitan nunca.
local contadorGuid = 0

-- Servicios que se pueden pedir con game:GetService (el resto lanza error, como un nombre mal escrito).
local SERVICIOS = {
	Players = true,
	ReplicatedStorage = true,
	ServerScriptService = true,
	StarterPlayer = true,
	DataStoreService = true,
	HttpService = true,
	RunService = true,
	CollectionService = true,
}

-- Clases que cuentan como "padres" de otras para Instance:IsA.
local PADRES = {
	Script = { "LuaSourceContainer" },
	LocalScript = { "LuaSourceContainer" },
	ModuleScript = { "LuaSourceContainer" },
}

-- ===== Señales =====

-- Equivalente a un RBXScriptSignal: cada manejador se ejecuta en su propio hilo (el `tarea` del mundo,
-- que anota los errores en vez de perderlos en la consola).
local function nuevaSenal(tarea)
	local conexiones = {}
	local senal = {}

	function senal.Connect(_, manejador)
		local conexion = { Connected = true, _manejador = manejador }
		function conexion.Disconnect(self)
			self.Connected = false
			local indice = table.find(conexiones, self)
			if indice then
				table.remove(conexiones, indice)
			end
		end
		table.insert(conexiones, conexion)
		return conexion
	end

	function senal.Wait(self)
		local hilo = coroutine.running()
		local conexion
		conexion = self:Connect(function(...)
			conexion:Disconnect()
			tarea.spawn(hilo, ...)
		end)
		return coroutine.yield()
	end

	-- No existe en Roblox: sirve a la simulación para disparar el evento.
	function senal.Fire(_, ...)
		for _, conexion in table.clone(conexiones) do
			if conexion.Connected then
				tarea.spawn(conexion._manejador, ...)
			end
		end
	end

	return senal
end

-- Copia las tablas de una lista de argumentos, como hace Roblox al enviarlas por un RemoteEvent.
local function copiarArgumentos(argumentos)
	local function copiar(valor)
		if type(valor) == "function" then
			error("no se pueden enviar funciones por un RemoteEvent", 0)
		end
		if type(valor) ~= "table" or getmetatable(valor) ~= nil or rawget(valor, "__tipoRoblox") then
			return valor
		end
		local copia = {}
		for clave, elemento in valor do
			copia[clave] = copiar(elemento)
		end
		return copia
	end

	local copia = { n = argumentos.n }
	for indice = 1, argumentos.n do
		copia[indice] = copiar(argumentos[indice])
	end
	return copia
end

-- ===== El mundo =====

function Roblox.nuevoMundo(opciones)
	opciones = opciones or {}

	local mundo = {
		Avisos = {}, -- textos recibidos por warn()
		Impresiones = {}, -- textos recibidos por print()
		Errores = {}, -- errores ocurridos dentro de hilos (task.spawn, eventos...), con su traceback
		Expulsiones = {}, -- { Jugador, Mensaje } de cada Player:Kick
		MensajesAClientes = {}, -- { Evento, Jugador, Argumentos } de cada FireClient
		JugadorLocal = nil,
		Nube = opciones.Nube,
		Cerrado = false,
		_callbacksCierre = {},
		_desfaseReloj = 0,
	}

	-- Como en Roblox, un error dentro de un hilo no detiene a los demás: se anota en mundo.Errores
	-- (las pruebas fallan si queda alguno sin revisar, para que ningún error pase inadvertido).
	local function envolver(funcion)
		return function(...)
			local ok, err = xpcall(funcion, function(motivo)
				return debug.traceback(tostring(motivo), 2)
			end, ...)
			if not ok then
				table.insert(mundo.Errores, err)
			end
		end
	end

	mundo.task = {
		spawn = function(funcion, ...)
			if type(funcion) == "thread" then
				return task.spawn(funcion, ...)
			end
			return task.spawn(envolver(funcion), ...)
		end,
		defer = function(funcion, ...)
			if type(funcion) == "thread" then
				return task.defer(funcion, ...)
			end
			return task.defer(envolver(funcion), ...)
		end,
		delay = function(segundos, funcion, ...)
			if type(funcion) == "thread" then
				return task.delay(segundos, funcion, ...)
			end
			return task.delay(segundos, envolver(funcion), ...)
		end,
		wait = task.wait,
		cancel = task.cancel,
	}

	local metatabla = {}
	local Instancia = {} -- métodos comunes a todas las instancias
	local PorClase = {} -- por clase: { iniciar = function(self), metodos = { ... } }

	local function esInstancia(valor)
		return type(valor) == "table" and getmetatable(valor) == metatabla
	end

	local function reasignarPadre(self, nuevoPadre)
		local viejoPadre = rawget(self, "_padre")
		if viejoPadre then
			local hermanos = rawget(viejoPadre, "_hijos")
			local indice = table.find(hermanos, self)
			if indice then
				table.remove(hermanos, indice)
			end
		end
		rawset(self, "_padre", nuevoPadre)
		if nuevoPadre then
			table.insert(rawget(nuevoPadre, "_hijos"), self)
			-- ChildAdded se dispara en el mismo instante: los manejadores ven el estado de ese momento.
			rawget(nuevoPadre, "ChildAdded"):Fire(self)
		end
	end

	metatabla.__index = function(self, clave)
		if clave == "Parent" then
			return rawget(self, "_padre")
		end
		local clase = PorClase[rawget(self, "ClassName")]
		if clase and clase.metodos and clase.metodos[clave] then
			return clase.metodos[clave]
		end
		if Instancia[clave] then
			return Instancia[clave]
		end
		-- Como en Roblox, los hijos también se pueden obtener por su nombre: `padre.Hijo`.
		for _, hijo in rawget(self, "_hijos") do
			if rawget(hijo, "Name") == clave then
				return hijo
			end
		end
		return nil
	end

	metatabla.__newindex = function(self, clave, valor)
		if clave == "Parent" then
			reasignarPadre(self, valor)
		else
			rawset(self, clave, valor)
		end
	end

	-- ----- Métodos comunes -----

	function Instancia.GetChildren(self)
		return table.clone(rawget(self, "_hijos"))
	end

	function Instancia.FindFirstChild(self, nombre)
		for _, hijo in rawget(self, "_hijos") do
			if rawget(hijo, "Name") == nombre then
				return hijo
			end
		end
		return nil
	end

	function Instancia.WaitForChild(self, nombre, tiempoMaximo)
		local limite = if tiempoMaximo then os.clock() + tiempoMaximo else nil
		local hijo = self:FindFirstChild(nombre)
		while hijo == nil do
			if limite and os.clock() > limite then
				return nil
			end
			task.wait()
			hijo = self:FindFirstChild(nombre)
		end
		return hijo
	end

	-- Primer hijo cuya clase es (o hereda de) `clase`.
	function Instancia.FindFirstChildOfClass(self, clase)
		for _, hijo in rawget(self, "_hijos") do
			if hijo:IsA(clase) then
				return hijo
			end
		end
		return nil
	end

	-- Copia profunda sin padre. Solo copia los campos públicos simples (nombre, código, números...).
	function Instancia.Clone(self)
		local copia = mundo.Instance.new(rawget(self, "ClassName"))
		for clave, valor in self do
			if string.sub(clave, 1, 1) ~= "_" and type(valor) ~= "table" and clave ~= "ClassName" then
				rawset(copia, clave, valor)
			end
		end
		for _, hijo in rawget(self, "_hijos") do
			hijo:Clone().Parent = copia
		end
		return copia
	end

	-- Posición del modelo (la simulación guarda un valor opaco: basta para comprobar que se copia).
	function Instancia.GetPivot(self)
		return rawget(self, "_pivote")
	end

	function Instancia.PivotTo(self, pivote)
		rawset(self, "_pivote", pivote)
	end

	function Instancia.IsA(self, clase)
		local propia = rawget(self, "ClassName")
		if clase == propia or clase == "Instance" then
			return true
		end
		return PADRES[propia] ~= nil and table.find(PADRES[propia], clase) ~= nil
	end

	function Instancia.Destroy(self)
		self.Parent = nil
	end

	function Instancia.GetFullName(self)
		local nombre = rawget(self, "Name")
		local padre = rawget(self, "_padre")
		if padre == nil or rawget(padre, "ClassName") == "DataModel" then
			return nombre
		end
		return `{padre:GetFullName()}.{nombre}`
	end

	-- ----- Instance.new -----

	local Instance = {}

	function Instance.new(clase)
		local self = setmetatable({ ClassName = clase, Name = clase, _hijos = {}, _padre = nil }, metatabla)
		rawset(self, "ChildAdded", nuevaSenal(mundo.task))
		local definicion = PorClase[clase]
		if definicion and definicion.iniciar then
			definicion.iniciar(self)
		end
		return self
	end

	-- ----- Clases concretas -----

	PorClase.RemoteEvent = {
		iniciar = function(self)
			rawset(self, "OnServerEvent", nuevaSenal(mundo.task))
			rawset(self, "OnClientEvent", nuevaSenal(mundo.task))
		end,
		metodos = {
			-- Cliente -> servidor: llega diferido y con el jugador local como primer argumento.
			FireServer = function(self, ...)
				assert(mundo.JugadorLocal ~= nil, "FireServer necesita un jugador local")
				local jugador = mundo.JugadorLocal
				local argumentos = copiarArgumentos(table.pack(...))
				mundo.task.defer(function()
					self.OnServerEvent:Fire(jugador, table.unpack(argumentos, 1, argumentos.n))
				end)
			end,
			-- Servidor -> un cliente.
			FireClient = function(self, jugador, ...)
				local argumentos = copiarArgumentos(table.pack(...))
				table.insert(mundo.MensajesAClientes, {
					Evento = rawget(self, "Name"),
					Jugador = jugador,
					Argumentos = argumentos,
				})
				mundo.task.defer(function()
					self.OnClientEvent:Fire(table.unpack(argumentos, 1, argumentos.n))
				end)
			end,
			-- Servidor -> todos los clientes (en la simulación solo hay un cliente).
			FireAllClients = function(self, ...)
				local argumentos = copiarArgumentos(table.pack(...))
				table.insert(mundo.MensajesAClientes, {
					Evento = rawget(self, "Name"),
					Jugador = nil,
					Argumentos = argumentos,
				})
				mundo.task.defer(function()
					self.OnClientEvent:Fire(table.unpack(argumentos, 1, argumentos.n))
				end)
			end,
		},
	}

	PorClase.Player = {
		iniciar = function(self)
			rawset(self, "UserId", 0)
			rawset(self, "CharacterAdded", nuevaSenal(mundo.task))
		end,
		metodos = {
			-- Expulsa al jugador: se anota el mensaje y se le saca de forma asíncrona.
			Kick = function(self, mensaje)
				if rawget(self, "_padre") == nil then
					return
				end
				table.insert(mundo.Expulsiones, { Jugador = self, Mensaje = mensaje or "" })
				mundo.task.defer(function()
					mundo.salirJugador(self)
				end)
			end,
		},
	}

	PorClase.Players = {
		iniciar = function(self)
			rawset(self, "PlayerAdded", nuevaSenal(mundo.task))
			rawset(self, "PlayerRemoving", nuevaSenal(mundo.task))
		end,
		metodos = {
			GetPlayers = function(self)
				local lista = {}
				for _, hijo in rawget(self, "_hijos") do
					if rawget(hijo, "ClassName") == "Player" then
						table.insert(lista, hijo)
					end
				end
				return lista
			end,
		},
	}

	PorClase.DataStoreService = {
		metodos = {
			GetDataStore = function(_, nombre)
				assert(mundo.Nube ~= nil, "este mundo no tiene NubeDatos")
				return mundo.Nube:ObtenerAlmacen(nombre)
			end,
		},
	}

	PorClase.HttpService = {
		metodos = {
			GenerateGUID = function(_, envolverEnLlaves)
				contadorGuid += 1
				local guid = string.format("GUID-%06d-%06x", contadorGuid, math.random(0, 0xFFFFFF))
				return if envolverEnLlaves then "{" .. guid .. "}" else guid
			end,
		},
	}

	PorClase.RunService = {
		metodos = {
			IsStudio = function()
				return opciones.Studio == true
			end,
			IsServer = function()
				return true
			end,
			IsClient = function()
				return false
			end,
		},
	}

	PorClase.DataModel = {
		metodos = {
			GetService = function(self, nombre)
				assert(SERVICIOS[nombre], `'{nombre}' no es un servicio válido (¿falta en la simulación?)`)
				local servicio = self:FindFirstChild(nombre)
				if servicio == nil then
					servicio = Instance.new(nombre)
					servicio.Parent = self
				end
				return servicio
			end,
			BindToClose = function(_, funcion)
				table.insert(mundo._callbacksCierre, funcion)
			end,
		},
	}

	-- ----- game y Vector3 -----

	local game = Instance.new("DataModel")
	rawset(game, "JobId", opciones.JobId or "")
	rawset(game, "PlaceId", opciones.PlaceId or 1234)
	mundo.game = game
	mundo.Instance = Instance
	mundo.Players = game:GetService("Players")

	mundo.Vector3 = {
		new = function(x, y, z)
			return {
				__tipoRoblox = "Vector3",
				X = x,
				Y = y,
				Z = z,
				Magnitude = math.sqrt(x * x + y * y + z * z),
			}
		end,
	}

	-- ----- Funciones globales que sustituyen a las de Roblox -----

	mundo.typeof = function(valor)
		if esInstancia(valor) then
			return "Instance"
		end
		if type(valor) == "table" and rawget(valor, "__tipoRoblox") then
			return rawget(valor, "__tipoRoblox")
		end
		return typeof(valor)
	end

	mundo.warn = function(...)
		local partes = table.pack(...)
		for indice = 1, partes.n do
			partes[indice] = tostring(partes[indice])
		end
		table.insert(mundo.Avisos, table.concat(partes, " ", 1, partes.n))
	end

	mundo.print = function(...)
		local partes = table.pack(...)
		for indice = 1, partes.n do
			partes[indice] = tostring(partes[indice])
		end
		table.insert(mundo.Impresiones, table.concat(partes, " ", 1, partes.n))
	end

	-- `os` con un reloj que se puede adelantar sin esperar de verdad (mundo.avanzarReloj).
	mundo.os = setmetatable({
		time = function()
			return math.floor(os.time() + mundo._desfaseReloj)
		end,
		clock = function()
			return os.clock() + mundo._desfaseReloj
		end,
	}, { __index = os })

	function mundo.avanzarReloj(segundos)
		mundo._desfaseReloj += segundos
	end

	-- ----- Control de jugadores y del cierre del servidor -----

	function mundo.unirJugador(userId, nombre)
		local jugador = Instance.new("Player")
		jugador.Name = nombre or `Jugador{userId}`
		rawset(jugador, "UserId", userId)
		jugador.Parent = mundo.Players
		mundo.Players.PlayerAdded:Fire(jugador)
		return jugador
	end

	function mundo.salirJugador(jugador)
		if rawget(jugador, "_padre") ~= mundo.Players then
			return
		end
		-- PlayerRemoving se dispara con el jugador todavía dentro de Players.
		mundo.Players.PlayerRemoving:Fire(jugador)
		jugador.Parent = nil
	end

	function mundo.establecerJugadorLocal(jugador)
		mundo.JugadorLocal = jugador
		rawset(mundo.Players, "LocalPlayer", jugador)
	end

	-- Ejecuta las funciones de BindToClose a la vez y espera a que terminen (Roblox da 30 s).
	function mundo.cerrar()
		if mundo.Cerrado then
			return
		end
		mundo.Cerrado = true

		local pendientes = #mundo._callbacksCierre
		for _, funcion in mundo._callbacksCierre do
			mundo.task.spawn(function()
				local ok, err = pcall(funcion)
				if not ok then
					mundo.warn(`Error en BindToClose: {err}`)
				end
				pendientes -= 1
			end)
		end

		local limite = os.clock() + 35
		while pendientes > 0 and os.clock() < limite do
			task.wait(0.002)
		end
	end

	return mundo
end

return Roblox
