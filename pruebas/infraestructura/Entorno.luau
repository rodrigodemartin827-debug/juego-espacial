--[[
	Entorno: monta el código de `src/` dentro de un mundo simulado (ver Roblox.luau) y permite cargar
	sus módulos como lo haría Roblox.

	Sigue las mismas reglas que Rojo para convertir archivos en Instancias:
	  - nombre.luau          -> ModuleScript
	  - nombre.server.luau   -> Script
	  - nombre.client.luau   -> LocalScript
	  - carpeta/             -> Folder
	  - carpeta/init.luau (o init.server.luau / init.client.luau) -> la propia carpeta pasa a ser
	    un ModuleScript (o Script / LocalScript) cuyos hijos son el resto de archivos.
	y lee `default.project.json` para saber dónde va cada carpeta.

	Un entorno tiene dos "lados" (servidor y cliente) que comparten el mismo `game` pero tienen cachés
	de `require` separadas, como si cada lado cargara su propia copia de los módulos compartidos.

	Uso:
		local servidor = Entorno.nuevo({ Nube = nube })
		local ServicioDatos = servidor.servidor.requerir("ServerScriptService.Server.Servicios.ServicioDatos")
]]

local fs = require("@lune/fs")
local luau = require("@lune/luau")
local serde = require("@lune/serde")
local task = require("@lune/task")

local Roblox = require("./Roblox")

local Entorno = {}

-- Entornos creados desde el último `cerrarTodos`.
local activos = {}

-- ===== Archivos -> Instancias (reglas de Rojo) =====

local construirEntrada

local function construirDirectorio(mundo, ruta, nombre)
	local entradas = fs.readDir(ruta)

	local archivoInit, claseInit
	for _, entrada in entradas do
		if entrada == "init.luau" then
			archivoInit, claseInit = entrada, "ModuleScript"
		elseif entrada == "init.server.luau" then
			archivoInit, claseInit = entrada, "Script"
		elseif entrada == "init.client.luau" then
			archivoInit, claseInit = entrada, "LocalScript"
		end
	end

	local instancia = mundo.Instance.new(claseInit or "Folder")
	instancia.Name = nombre
	if archivoInit then
		instancia.Source = fs.readFile(`{ruta}/{archivoInit}`)
	end

	for _, entrada in entradas do
		if entrada ~= archivoInit then
			local hijo = construirEntrada(mundo, `{ruta}/{entrada}`, entrada)
			if hijo then
				hijo.Parent = instancia
			end
		end
	end
	return instancia
end

function construirEntrada(mundo, ruta, nombreArchivo)
	if fs.isDir(ruta) then
		return construirDirectorio(mundo, ruta, nombreArchivo)
	end

	local nombre, clase
	if string.match(nombreArchivo, "%.server%.luau$") then
		nombre, clase = string.gsub(nombreArchivo, "%.server%.luau$", ""), "Script"
	elseif string.match(nombreArchivo, "%.client%.luau$") then
		nombre, clase = string.gsub(nombreArchivo, "%.client%.luau$", ""), "LocalScript"
	elseif string.match(nombreArchivo, "%.luau$") then
		nombre, clase = string.gsub(nombreArchivo, "%.luau$", ""), "ModuleScript"
	else
		return nil -- otros archivos (.gitkeep, .md...) no se convierten en Instancias
	end

	local instancia = mundo.Instance.new(clase)
	instancia.Name = nombre
	instancia.Source = fs.readFile(ruta)
	return instancia
end

-- Crea la jerarquía descrita en default.project.json dentro de `mundo.game`.
local function montarProyecto(mundo, rutaProyecto)
	local proyecto = serde.decode("json", fs.readFile(rutaProyecto))

	local function construirNodo(nombre, nodo, padre)
		local instancia
		if nodo["$path"] then
			local ruta = nodo["$path"]
			if fs.isDir(ruta) then
				instancia = construirEntrada(mundo, ruta, nombre)
			else
				-- Un archivo suelto ("X.luau"): la clase sale de su extensión y el nombre, del nodo (como en Rojo).
				instancia = construirEntrada(mundo, ruta, string.match(ruta, "[^/\\]+$") or ruta)
				if instancia then
					instancia.Name = nombre
				end
			end
		else
			instancia = mundo.Instance.new(nodo["$className"] or "Folder")
			instancia.Name = nombre
		end
		instancia.Parent = padre

		for clave, hijo in nodo do
			if string.sub(clave, 1, 1) ~= "$" then
				construirNodo(clave, hijo, instancia)
			end
		end
	end

	-- Los hijos directos de la raíz son servicios: ya existen, solo hay que rellenarlos.
	for nombre, nodo in proyecto.tree do
		if string.sub(nombre, 1, 1) ~= "$" then
			local servicio = mundo.game:GetService(nombre)
			for clave, hijo in nodo do
				if string.sub(clave, 1, 1) ~= "$" then
					construirNodo(clave, hijo, servicio)
				end
			end
		end
	end
end

-- ===== Carga de módulos =====

-- Crea el "lado" (servidor o cliente) del entorno: sus globales y su propio `require` con caché.
local function nuevoLado(mundo)
	local lado = {}
	local cache = {}
	local cargando = {}

	local function globales(script)
		return {
			game = mundo.game,
			script = script,
			require = lado.require,
			task = mundo.task,
			warn = mundo.warn,
			print = mundo.print,
			typeof = mundo.typeof,
			Instance = mundo.Instance,
			Vector3 = mundo.Vector3,
			-- Solo los enumerados que usa el código del servidor (cada valor es una tabla con su Name).
			Enum = {
				HumanoidRigType = { R6 = { Name = "R6" }, R15 = { Name = "R15" } },
			},
			os = mundo.os,
		}
	end

	local function ejecutar(script)
		local funcion = luau.load(script.Source, {
			debugName = script:GetFullName(),
			environment = globales(script),
		})
		return funcion()
	end

	-- Equivalente a `require(ModuleScript)`: ejecuta el módulo una sola vez y devuelve su valor.
	function lado.require(modulo)
		assert(
			mundo.typeof(modulo) == "Instance" and modulo.ClassName == "ModuleScript",
			"require necesita un ModuleScript"
		)
		local guardado = cache[modulo]
		if guardado then
			return guardado.Valor
		end

		-- Si otro hilo está cargando ya este módulo (porque cedió el hilo a media carga), se espera a que
		-- termine, como hace Roblox. Si el hilo que lo carga es el actual, es una dependencia circular.
		local hiloCargador = cargando[modulo]
		if hiloCargador ~= nil then
			assert(hiloCargador ~= coroutine.running(), `dependencia circular al cargar {modulo:GetFullName()}`)
			while cargando[modulo] ~= nil do
				task.wait()
			end
			return cache[modulo].Valor
		end

		cargando[modulo] = coroutine.running()
		local resultado = table.pack(ejecutar(modulo))
		cargando[modulo] = nil
		assert(
			resultado.n == 1,
			`el módulo {modulo:GetFullName()} debe devolver exactamente un valor (devuelve {resultado.n})`
		)

		cache[modulo] = { Valor = resultado[1] }
		return resultado[1]
	end

	-- Busca una Instancia por su ruta desde `game`, p. ej. "ReplicatedStorage.Shared.Red.Validador".
	function lado.buscar(ruta)
		local actual = mundo.game
		for parte in string.gmatch(ruta, "[^%.]+") do
			actual = actual:FindFirstChild(parte)
			assert(actual ~= nil, `no existe '{parte}' en la ruta '{ruta}'`)
		end
		return actual
	end

	-- Carga un ModuleScript dado por su ruta y devuelve lo que exporta.
	function lado.requerir(ruta)
		return lado.require(lado.buscar(ruta))
	end

	-- Ejecuta un Script o LocalScript (como los init.server.luau / init.client.luau) en su propio hilo.
	function lado.ejecutarScript(ruta)
		local script = lado.buscar(ruta)
		assert(script.ClassName == "Script" or script.ClassName == "LocalScript", "no es un script")
		mundo.task.spawn(ejecutar, script)
	end

	return lado
end

-- ===== API =====

--[[
	Crea un entorno nuevo con todo `src/` montado.

	Opciones:
	  - Nube: NubeDatos compartida con otros entornos (necesaria para usar DataStores).
	  - JobId, PlaceId: identifican al servidor (game.JobId vacío = Studio).
	  - Studio: hace que RunService:IsStudio() devuelva true.
]]
function Entorno.nuevo(opciones)
	local mundo = Roblox.nuevoMundo(opciones)
	montarProyecto(mundo, "default.project.json")

	local entorno = {
		mundo = mundo,
		game = mundo.game,
		servidor = nuevoLado(mundo),
		cliente = nuevoLado(mundo),
	}

	function entorno.cerrar()
		mundo.cerrar()
	end

	table.insert(activos, entorno)
	return entorno
end

-- Falla si en algún entorno quedó un error ocurrido dentro de un hilo sin que la prueba lo revisara.
-- Las pruebas que provocan errores a propósito los vacían con `table.clear(entorno.mundo.Errores)`.
function Entorno.verificarSinErrores()
	local mensajes = {}
	for _, entorno in activos do
		for _, error_ in entorno.mundo.Errores do
			table.insert(mensajes, error_)
		end
	end
	if #mensajes > 0 then
		error(`hubo {#mensajes} error(es) dentro de hilos de la simulación:\n{table.concat(mensajes, "\n---\n")}`, 0)
	end
end

-- Cierra todos los entornos creados, para que sus bucles en segundo plano terminen.
function Entorno.cerrarTodos()
	for _, entorno in activos do
		entorno.cerrar()
	end
	table.clear(activos)
end

return Entorno
