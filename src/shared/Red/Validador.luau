--!strict
--[[
	Validador: comprobaciones de tipo y de rango para los argumentos que llegan por red.

	Cada función de este módulo (Numero, Entero, Cadena...) devuelve un "validador": una función que
	recibe un valor y devuelve `true` si es aceptable, o `false` y el motivo si no lo es.

		local esPuntuacion = Validador.Entero(0, 1000)
		esPuntuacion(50)       --> true
		esPuntuacion(-3)       --> false, "debe ser >= 0"
		esPuntuacion("hola")   --> false, "se esperaba un número"

	El servidor NUNCA debe fiarse de lo que envía el cliente: un tramposo puede mandar cualquier tipo
	de valor, NaN, infinitos, cadenas enormes, más o menos argumentos de los previstos... Estos
	validadores son la primera barrera, antes de que el valor llegue a la lógica del juego.

	Un validador solo comprueba la FORMA del valor. Que tenga sentido en la partida (que el jugador
	tenga suficientes monedas, que el objetivo esté a tiro...) lo debe comprobar el manejador.
]]

export type Validador = (valor: any) -> (boolean, string?)

-- Longitud máxima de una cadena si no se indica otra: evita que alguien envíe textos gigantes.
local LONGITUD_MAXIMA_POR_DEFECTO = 256

local Validador = {}

-- Número finito (se rechazan NaN e infinitos), con límites opcionales (ambos incluidos).
function Validador.Numero(minimo: number?, maximo: number?): Validador
	return function(valor: any)
		if type(valor) ~= "number" then
			return false, "se esperaba un número"
		end
		-- NaN es el único valor que no es igual a sí mismo.
		if valor ~= valor or valor == math.huge or valor == -math.huge then
			return false, "el número no es finito"
		end
		if minimo ~= nil and valor < minimo then
			return false, `debe ser >= {minimo}`
		end
		if maximo ~= nil and valor > maximo then
			return false, `debe ser <= {maximo}`
		end
		return true, nil
	end
end

-- Número entero, con límites opcionales (ambos incluidos).
function Validador.Entero(minimo: number?, maximo: number?): Validador
	local esNumero = Validador.Numero(minimo, maximo)
	return function(valor: any)
		local valido, motivo = esNumero(valor)
		if not valido then
			return false, motivo
		end
		if valor % 1 ~= 0 then
			return false, "se esperaba un número entero"
		end
		return true, nil
	end
end

export type OpcionesCadena = {
	MinLongitud: number?, -- longitud mínima en bytes (por defecto 0)
	MaxLongitud: number?, -- longitud máxima en bytes (por defecto 256)
	Patron: string?, -- patrón de Luau que debe cumplir la cadena completa, p. ej. "^[%w_]+$"
}

-- Cadena de texto. Las longitudes se miden en bytes, que es lo que cuesta enviar y guardar.
function Validador.Cadena(opciones: OpcionesCadena?): Validador
	local minLongitud = if opciones and opciones.MinLongitud then opciones.MinLongitud else 0
	local maxLongitud = if opciones and opciones.MaxLongitud then opciones.MaxLongitud else LONGITUD_MAXIMA_POR_DEFECTO
	local patron = if opciones then opciones.Patron else nil

	return function(valor: any)
		if type(valor) ~= "string" then
			return false, "se esperaba una cadena de texto"
		end
		if #valor < minLongitud then
			return false, `debe tener al menos {minLongitud} caracteres`
		end
		if #valor > maxLongitud then
			return false, `debe tener como máximo {maxLongitud} caracteres`
		end
		if patron ~= nil and string.match(valor, patron) == nil then
			return false, "el formato no es válido"
		end
		return true, nil
	end
end

-- Valor booleano (true o false).
function Validador.Booleano(): Validador
	return function(valor: any)
		if type(valor) ~= "boolean" then
			return false, "se esperaba true o false"
		end
		return true, nil
	end
end

-- Una cadena que debe ser exactamente uno de los valores indicados.
function Validador.Enumeracion(valores: { string }): Validador
	local permitidos: { [string]: boolean } = {}
	for _, valorPermitido in valores do
		permitidos[valorPermitido] = true
	end
	local lista = table.concat(valores, ", ")

	return function(valor: any)
		if type(valor) ~= "string" or not permitidos[valor] then
			return false, `valor no permitido (los válidos son: {lista})`
		end
		return true, nil
	end
end

-- Vector3 con todas sus componentes finitas y, opcionalmente, una longitud máxima.
function Validador.Vector3(maxMagnitud: number?): Validador
	return function(valor: any)
		if typeof(valor) ~= "Vector3" then
			return false, "se esperaba un Vector3"
		end
		-- La magnitud es NaN si alguna componente es NaN, e infinita si alguna es infinita.
		local magnitud = (valor :: Vector3).Magnitude
		if magnitud ~= magnitud or magnitud == math.huge then
			return false, "el Vector3 no es finito"
		end
		if maxMagnitud ~= nil and magnitud > maxMagnitud then
			return false, `la magnitud debe ser <= {maxMagnitud}`
		end
		return true, nil
	end
end

-- Una Instancia, opcionalmente de una clase concreta (admite herencia, como `IsA`).
function Validador.Instancia(clase: string?): Validador
	return function(valor: any)
		if typeof(valor) ~= "Instance" then
			return false, "se esperaba una Instancia"
		end
		if clase ~= nil and not (valor :: Instance):IsA(clase) then
			return false, `la Instancia debe ser de la clase {clase}`
		end
		return true, nil
	end
end

-- Hace que un validador acepte también `nil` (argumento que puede omitirse).
function Validador.Opcional(validador: Validador): Validador
	return function(valor: any)
		if valor == nil then
			return true, nil
		end
		return validador(valor)
	end
end

--[[
	Comprueba la lista completa de argumentos de una petición contra un esquema.

	`esquema` es la lista de validadores, uno por posición. Se rechaza la petición si:
	  - llegan más argumentos que validadores hay (un tramposo podría añadir los que quiera), o
	  - algún argumento no pasa su validador (los que falten llegan como nil: pasan solo si son opcionales).

	Devuelve `true`, o `false` y un texto que explica el motivo.
]]
function Validador.ValidarArgumentos(esquema: { Validador }, ...: any): (boolean, string?)
	local cantidad = select("#", ...)
	if cantidad > #esquema then
		return false, `demasiados argumentos ({cantidad}, el máximo es {#esquema})`
	end

	for posicion, validador in esquema do
		-- Los paréntesis extra reducen select(...) a un único valor (nil si no existe).
		local valido, motivo = validador((select(posicion, ...)))
		if not valido then
			return false, `argumento {posicion}: {motivo or "no es válido"}`
		end
	end
	return true, nil
end

return Validador
