--!strict
--[[
	Senal: un evento sencillo escrito en Luau puro.

	Frente a un BindableEvent tiene dos ventajas: no crea Instancias y los argumentos se pasan por
	referencia (BindableEvent copia las tablas). Así, varios servicios pueden compartir los datos
	vivos de un jugador sin duplicarlos.

	Cada manejador se ejecuta en su propio hilo (task.spawn): un error o una espera dentro de un
	manejador no afecta a los demás ni a quien dispara la señal.

	Ejemplo:
		local alSubirNivel = Senal.nueva()
		local conexion = alSubirNivel:Conectar(function(jugador, nivel)
			print(jugador.Name, "ahora es nivel", nivel)
		end)
		alSubirNivel:Disparar(jugador, 5)
		conexion:Desconectar()
]]

local Conexion = {}
Conexion.__index = Conexion

local Senal = {}
Senal.__index = Senal

export type Conexion = typeof(setmetatable(
	{} :: {
		Conectada: boolean,
		_senal: any, -- la Senal a la que pertenece (any para evitar tipos circulares)
		_manejador: (...any) -> (),
	},
	Conexion
))

export type Senal = typeof(setmetatable(
	{} :: {
		_conexiones: { Conexion },
	},
	Senal
))

-- Crea una señal sin conexiones.
function Senal.nueva(): Senal
	return setmetatable({ _conexiones = {} }, Senal)
end

-- Registra `manejador`; se llamará cada vez que se dispare la señal, hasta que se desconecte.
function Senal.Conectar(self: Senal, manejador: (...any) -> ()): Conexion
	local conexion: Conexion = setmetatable({
		Conectada = true,
		_senal = self,
		_manejador = manejador,
	}, Conexion)
	table.insert(self._conexiones, conexion)
	return conexion
end

-- Llama a todos los manejadores conectados con los argumentos indicados.
function Senal.Disparar(self: Senal, ...: any)
	-- Se recorre una copia: un manejador puede conectar o desconectar otros mientras se dispara.
	for _, conexion in table.clone(self._conexiones) do
		if conexion.Conectada then
			task.spawn(conexion._manejador, ...)
		end
	end
end

-- Pausa el hilo actual hasta el próximo disparo y devuelve los argumentos con los que se disparó.
function Senal.Esperar(self: Senal): ...any
	local hilo = coroutine.running()
	local conexion: Conexion
	conexion = self:Conectar(function(...)
		conexion:Desconectar()
		task.spawn(hilo, ...)
	end)
	return coroutine.yield()
end

-- Desconecta todos los manejadores.
function Senal.Destruir(self: Senal)
	for _, conexion in table.clone(self._conexiones) do
		conexion:Desconectar()
	end
end

-- Deja de llamar al manejador. Es seguro llamarla más de una vez.
function Conexion.Desconectar(self: Conexion)
	if not self.Conectada then
		return
	end
	self.Conectada = false

	local conexiones: { Conexion } = self._senal._conexiones
	local indice = table.find(conexiones, self)
	if indice then
		table.remove(conexiones, indice)
	end
end

return Senal
