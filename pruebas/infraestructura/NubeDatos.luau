--[[
	NubeDatos: simulación del servicio de DataStore de Roblox para las pruebas.

	Una misma NubeDatos puede compartirse entre varios servidores simulados, igual que en Roblox
	todos los servidores de un juego ven los mismos datos. Imita las reglas que más importan:

	  - Los valores se serializan al guardar y se deserializan al leer: se guardan y se devuelven COPIAS,
	    y se rechaza lo que un DataStore real rechazaría (funciones, NaN, infinitos, tablas mixtas...).
	  - UpdateAsync es atómico por clave y su función de transformación NO puede ceder el hilo
	    (task.wait, WaitForChild...). Si lo hace, se lanza un error, como en Roblox.
	  - Devolver nil desde la transformación cancela la escritura.

	Y permite provocar situaciones difíciles de ver en Studio:

	  - Latencia: cada petición tarda `Latencia` segundos, así que las peticiones de varios servidores se
	    entrelazan como en la realidad.
	  - Pausada: mientras sea true, las peticiones que empiecen se quedan esperando. Sirve para dejar una
	    operación a medias el tiempo que haga falta sin depender de la precisión del reloj.
	  - Fallos: `Fallos` peticiones fallan sin llegar a aplicarse (red caída, límite de peticiones...).
	  - FallosTrasAplicar: peticiones que SÍ se aplican pero cuya respuesta se pierde (el servidor cree que
	    ha fallado aunque el dato se haya guardado).
	  - FallarSi: función opcional (clave, operacion) -> boolean que limita los fallos a ciertas claves.

	Y lleva cuentas para comprobar el comportamiento: Peticiones, MaxEnVuelo (peticiones UpdateAsync
	simultáneas) y Escrituras (historial de lo escrito, con los UserIds asociados).
]]

local task = require("@lune/task")

local NubeDatos = {}

-- ===== Serialización =====

local function esFinito(numero: number): boolean
	return numero == numero and numero ~= math.huge and numero ~= -math.huge
end

-- Devuelve una copia del valor tal y como la guardaría un DataStore, o lanza un error si no se puede
-- guardar. `ruta` solo se usa para que los mensajes de error indiquen dónde está el problema.
local function serializar(valor: any, ruta: string): any
	local tipo = typeof(valor)

	if tipo == "number" then
		if not esFinito(valor) then
			error(`104: No se puede guardar un número no finito en {ruta}`, 0)
		end
		return valor
	elseif tipo == "string" then
		if utf8.len(valor) == nil then
			error(`104: Cadena con UTF-8 no válido en {ruta}`, 0)
		end
		return valor
	elseif tipo == "boolean" then
		return valor
	elseif tipo == "table" then
		local copia = {}
		local cantidad, claveNumerica, claveTexto = 0, false, false
		for clave, elemento in valor do
			cantidad += 1
			if type(clave) == "number" then
				claveNumerica = true
			elseif type(clave) == "string" then
				claveTexto = true
			else
				error(`104: Clave de tipo {typeof(clave)} no permitida en {ruta}`, 0)
			end
			copia[clave] = serializar(elemento, `{ruta}.{clave}`)
		end
		if claveNumerica and claveTexto then
			error(`104: Tabla mixta (claves numéricas y de texto) en {ruta}`, 0)
		end
		if claveNumerica then
			-- Un array debe ser consecutivo desde 1, sin huecos.
			for indice = 1, cantidad do
				if copia[indice] == nil then
					error(`104: Array con huecos en {ruta}`, 0)
				end
			end
		end
		return copia
	end

	error(`104: No se puede guardar un valor de tipo {tipo} en {ruta}`, 0)
end

local function copiar(valor: any): any
	if type(valor) ~= "table" then
		return valor
	end
	local copia = {}
	for clave, elemento in valor do
		copia[clave] = copiar(elemento)
	end
	return copia
end

-- ===== La nube =====

export type Nube = {
	Latencia: number,
	Pausada: boolean,
	Fallos: number,
	FallosTrasAplicar: number,
	FallarSi: ((clave: string, operacion: string) -> boolean)?,
	ErrorAlObtenerAlmacen: string?,
	Peticiones: number,
	Escrituras: { { Clave: string, Valor: any } },
	[string]: any,
}

function NubeDatos.nueva(): Nube
	local almacenes: { [string]: { [string]: any } } = {}

	local nube: any = {
		Latencia = 0,
		Pausada = false,
		Fallos = 0,
		FallosTrasAplicar = 0,
		FallarSi = nil,
		ErrorAlObtenerAlmacen = nil,
		Peticiones = 0,
		EnVuelo = 0, -- UpdateAsync en marcha ahora mismo
		MaxEnVuelo = 0, -- el máximo de UpdateAsync que han coincidido a la vez
		Escrituras = {}, -- historial de lo que se ha escrito, en orden: { Clave, Valor, UserIds }
	}

	local function debeFallar(clave: string, operacion: string): boolean
		if nube.FallarSi ~= nil and not nube.FallarSi(clave, operacion) then
			return false
		end
		return true
	end

	-- Lee lo que hay guardado en `clave` (una copia), sin pasar por la simulación de latencia o fallos.
	function nube.Leer(_, nombreAlmacen: string, clave: string): any
		local almacen = almacenes[nombreAlmacen]
		return if almacen then copiar(almacen[clave]) else nil
	end

	-- Escribe directamente en `clave`, para preparar el estado inicial de una prueba.
	function nube.Escribir(_, nombreAlmacen: string, clave: string, valor: any)
		almacenes[nombreAlmacen] = almacenes[nombreAlmacen] or {}
		almacenes[nombreAlmacen][clave] = serializar(valor, clave)
	end

	function nube.ObtenerAlmacen(_, nombreAlmacen: string)
		if nube.ErrorAlObtenerAlmacen ~= nil then
			error(nube.ErrorAlObtenerAlmacen, 0)
		end
		almacenes[nombreAlmacen] = almacenes[nombreAlmacen] or {}
		local datos = almacenes[nombreAlmacen]
		local almacen = {}

		-- Simula el tiempo de la petición y los fallos previos a aplicarla.
		local function iniciarPeticion(clave: string, operacion: string)
			nube.Peticiones += 1
			while nube.Pausada do
				task.wait()
			end
			if nube.Latencia > 0 then
				task.wait(nube.Latencia)
			end
			if nube.Fallos > 0 and debeFallar(clave, operacion) then
				nube.Fallos -= 1
				error("503: la petición al DataStore falló (simulado)", 0)
			end
		end

		function almacen.GetAsync(_, clave: string): any
			iniciarPeticion(clave, "GetAsync")
			return copiar(datos[clave])
		end

		local function actualizar(clave: string, transformacion: (any, any) -> (any, any, any)): (any, any)
			iniciarPeticion(clave, "UpdateAsync")

			local actual = copiar(datos[clave])
			local info = { Version = "1", CreatedTime = 0, UpdatedTime = 0 }

			-- La transformación se ejecuta en una corrutina aparte para detectar si intenta ceder.
			local hilo = coroutine.create(transformacion)
			local resultado = table.pack(coroutine.resume(hilo, actual, info))
			if coroutine.status(hilo) ~= "dead" then
				error("UpdateAsync: la función de transformación no puede ceder el hilo", 0)
			end
			if not resultado[1] then
				error(resultado[2], 0)
			end

			local nuevo, idsUsuario = resultado[2], resultado[3]
			if nuevo == nil then
				return nil -- escritura cancelada
			end
			assert(idsUsuario == nil or type(idsUsuario) == "table", "UpdateAsync: los UserIds deben ser una lista")

			datos[clave] = serializar(nuevo, clave)
			table.insert(nube.Escrituras, {
				Clave = clave,
				Valor = copiar(datos[clave]),
				UserIds = copiar(idsUsuario),
			})

			if nube.FallosTrasAplicar > 0 and debeFallar(clave, "UpdateAsync") then
				nube.FallosTrasAplicar -= 1
				error("504: se perdió la respuesta de la petición (simulado)", 0)
			end
			return copiar(datos[clave]), info
		end

		function almacen.UpdateAsync(_, clave: string, transformacion: (any, any) -> (any, any, any)): any
			nube.EnVuelo += 1
			nube.MaxEnVuelo = math.max(nube.MaxEnVuelo, nube.EnVuelo)
			local ok, resultado, info = pcall(actualizar, clave, transformacion)
			nube.EnVuelo -= 1
			if not ok then
				error(resultado, 0)
			end
			return resultado, info
		end

		return almacen
	end

	return nube
end

return NubeDatos
