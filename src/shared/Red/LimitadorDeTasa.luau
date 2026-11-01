--!strict
--[[
	LimitadorDeTasa: limita cuántas veces por segundo se puede hacer algo, de forma independiente
	para cada "clave" (por ejemplo, el UserId de un jugador).

	Usa el algoritmo del "cubo de fichas":
	  - Cada clave tiene un cubo que guarda como máximo `rafaga` fichas (empieza lleno).
	  - Cada petición consume una ficha.
	  - El cubo se rellena a razón de `limitePorSegundo` fichas por segundo.
	  - Si no queda ninguna ficha, la petición se rechaza.

	Así el ritmo sostenido nunca supera `limitePorSegundo` peticiones por segundo, pero se tolera una
	pequeña ráfaga (por ejemplo, tras un pico de latencia que agrupa varios mensajes).

	Ejemplo con limitePorSegundo = 5 y rafaga = 5:
	  - Cinco peticiones seguidas se aceptan y la sexta se rechaza.
	  - Pasados 0,2 s vuelve a haber una ficha y se acepta otra petición.

	Lo usan el servidor (para hacer cumplir el límite) y el cliente (para no superarlo por su cuenta).
]]

-- Margen para el error de coma flotante: sin él, un cliente que envía justo al ritmo permitido
-- vería rechazada alguna petición por tener 0,9999999 fichas en lugar de 1.
local TOLERANCIA = 1e-6

local LimitadorDeTasa = {}
LimitadorDeTasa.__index = LimitadorDeTasa

type Cubo = {
	Fichas: number, -- fichas disponibles ahora mismo (puede ser fraccionaria)
	Ultima: number, -- instante de la última actualización del cubo
}

export type LimitadorDeTasa = typeof(setmetatable(
	{} :: {
		_tasa: number,
		_capacidad: number,
		_reloj: () -> number,
		_cubos: { [any]: Cubo },
	},
	LimitadorDeTasa
))

--[[
	Crea un limitador.

	- limitePorSegundo: peticiones por segundo que se permiten de forma sostenida (mayor que 0).
	- rafaga: máximo de peticiones seguidas que se aceptan de golpe. Por defecto, igual a
	  `limitePorSegundo`. Nunca es menor que 1.
	- reloj: función que devuelve el tiempo en segundos. Por defecto `os.clock`; solo se cambia
	  en las pruebas para controlar el tiempo.
]]
function LimitadorDeTasa.nuevo(limitePorSegundo: number, rafaga: number?, reloj: (() -> number)?): LimitadorDeTasa
	assert(
		type(limitePorSegundo) == "number" and limitePorSegundo > 0,
		"limitePorSegundo debe ser un número mayor que 0"
	)

	return setmetatable({
		_tasa = limitePorSegundo,
		-- Como mínimo 1 ficha: con menos, ninguna petición podría aceptarse nunca.
		_capacidad = math.max(1, rafaga or limitePorSegundo),
		_reloj = reloj or os.clock,
		_cubos = {},
	}, LimitadorDeTasa)
end

-- Registra una petición de `clave`. Devuelve `true` si se permite o `false` si supera el límite.
function LimitadorDeTasa.Permitir(self: LimitadorDeTasa, clave: any): boolean
	local ahora = self._reloj()

	local cubo = self._cubos[clave]
	if cubo == nil then
		cubo = { Fichas = self._capacidad, Ultima = ahora }
		self._cubos[clave] = cubo
	else
		-- Se rellena según el tiempo transcurrido (math.max protege de un reloj que retroceda).
		local transcurrido = math.max(0, ahora - cubo.Ultima)
		cubo.Fichas = math.min(self._capacidad, cubo.Fichas + transcurrido * self._tasa)
		cubo.Ultima = ahora
	end

	if cubo.Fichas >= 1 - TOLERANCIA then
		cubo.Fichas = math.max(0, cubo.Fichas - 1)
		return true
	end
	return false
end

-- Borra el cubo de `clave`. Hay que llamarlo cuando el jugador se va, para no acumular memoria.
function LimitadorDeTasa.Olvidar(self: LimitadorDeTasa, clave: any)
	self._cubos[clave] = nil
end

return LimitadorDeTasa
