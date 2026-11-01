--!strict
--[[
	Esquema: define QUÉ se guarda de cada jugador y lo mantiene válido.

	Responsabilidades:
	  - Plantilla: los valores de un jugador nuevo.
	  - Conciliar: al cargar (y antes de cada guardado) rellena los campos que falten, repara los
	    valores inválidos (tipo equivocado, negativos, NaN, infinitos...) y devuelve cuántas
	    reparaciones hizo. Así los datos siempre cumplen la plantilla y siempre se pueden guardar:
	    un solo NaN en las monedas haría fallar TODOS los guardados de ese jugador.
	  - Migrar: aplica, en orden, las migraciones necesarias para llevar datos antiguos a la versión
	    actual del esquema.

	Cómo cambiar los datos en el futuro:
	  - Añadir un campo nuevo: basta con ponerlo en la PLANTILLA (y en Datos/Tipos). Los jugadores que
	    ya existen lo recibirán con su valor inicial la próxima vez que carguen.
	  - Renombrar, mover o borrar un campo: sube VERSION y añade en MIGRACIONES la función que
	    transforma los datos de la versión anterior (ver el ejemplo más abajo).
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local Bandos = require(Shared.Juego.Bandos)
local Tablas = require(Shared.Utilidades.Tablas)
local Tipos = require(Shared.Datos.Tipos)

type Datos = Tipos.Datos

local Esquema = {}

-- Versión actual del esquema. Se guarda junto a los datos de cada jugador.
Esquema.VERSION = 1

-- Valores de un jugador nuevo.
local PLANTILLA: Datos = {
	Bando = Bandos.Ninguno,
	Nivel = 1,
	XP = 0,
	Monedas = 0,
	Inventario = {}, -- se va llenando con { idObjeto = cantidad }
	MejorasNave = {
		-- Nivel de cada mejora de la nave. Añade aquí las que tenga el juego.
		Casco = 0,
		Escudo = 0,
		Motor = 0,
		Armas = 0,
		Escaner = 0,
		Carga = 0,
	},
}

--[[
	Migraciones: `Migraciones[n]` transforma, EN SITIO, unos datos de la versión n-1 a la versión n.
	Ejemplo, para cuando exista la versión 2 (y VERSION valga 2):

		Esquema.Migraciones[2] = function(datos)
			datos.Monedas = datos.Oro -- el campo "Oro" se renombró a "Monedas"
			datos.Oro = nil
		end
]]
Esquema.Migraciones = {} :: { [number]: (datos: any) -> () }

-- Devuelve los datos de un jugador nuevo (una copia: la plantilla nunca se entrega).
function Esquema.Nuevo(): Datos
	return Tablas.CopiaProfunda(PLANTILLA)
end

-- Lleva unos datos guardados con la versión `versionOrigen` hasta la versión actual.
function Esquema.Migrar(datos: any, versionOrigen: number): any
	for version = versionOrigen + 1, Esquema.VERSION do
		local migracion = Esquema.Migraciones[version]
		if migracion ~= nil then
			migracion(datos)
		end
	end
	return datos
end

-- ===== Conciliación =====

local function esFinito(valor: any): boolean
	return type(valor) == "number" and valor == valor and valor ~= math.huge and valor ~= -math.huge
end

-- Rellena en `destino` lo que falte respecto a `plantilla` y corrige los campos con tipo
-- equivocado. Un campo ausente es normal (jugadores anteriores a un campo nuevo) y no cuenta como
-- reparación; uno con el tipo equivocado sí. Devuelve el número de reparaciones.
local function conciliarEstructura(destino: { [any]: any }, plantilla: { [any]: any }): number
	local reparaciones = 0

	for clave, valorPlantilla in plantilla do
		local actual = destino[clave]

		if actual == nil then
			destino[clave] = Tablas.CopiaProfunda(valorPlantilla)
		elseif type(valorPlantilla) == "table" then
			if type(actual) == "table" then
				reparaciones += conciliarEstructura(actual, valorPlantilla)
			else
				destino[clave] = Tablas.CopiaProfunda(valorPlantilla)
				reparaciones += 1
			end
		elseif type(actual) ~= type(valorPlantilla) then
			destino[clave] = valorPlantilla
			reparaciones += 1
		end
	end

	return reparaciones
end

-- Deja `datos[clave]` como un entero finito >= minimo. Los decimales se truncan; lo que no es un
-- número finito (NaN, infinitos) o es menor que el mínimo vuelve al mínimo.
local function repararContador(datos: { [string]: any }, clave: string, minimo: number): number
	local valor = datos[clave]

	if not esFinito(valor) then
		datos[clave] = minimo
		return 1
	end

	local entero = math.floor(valor)
	if entero < minimo then
		datos[clave] = minimo
		return 1
	elseif entero ~= valor then
		datos[clave] = entero
		return 1
	end
	return 0
end

-- Limpia un mapa { [texto] = cantidad }: elimina las entradas cuya clave no es texto o cuya
-- cantidad no es un número finito mayor o igual que 0, y trunca las cantidades decimales.
local function repararMapa(mapa: { [any]: any }): number
	local reparaciones = 0

	for clave, cantidad in mapa do
		if type(clave) ~= "string" or not esFinito(cantidad) or cantidad < 0 then
			mapa[clave] = nil
			reparaciones += 1
		elseif cantidad ~= math.floor(cantidad) then
			mapa[clave] = math.floor(cantidad)
			reparaciones += 1
		end
	end

	return reparaciones
end

--[[
	Deja `entrada` cumpliendo el esquema, modificándola EN SITIO (quien tenga una referencia a la tabla
	seguirá viendo los datos vivos). Si `entrada` no es una tabla, devuelve datos nuevos.

	Devuelve los datos y el número de reparaciones (valores inválidos que hubo que corregir). Un valor
	distinto de 0 indica un fallo en alguna parte del juego que conviene investigar.
]]
function Esquema.Conciliar(entrada: any): (Datos, number)
	if type(entrada) ~= "table" then
		return Esquema.Nuevo(), 1
	end

	local datos = entrada :: { [string]: any }
	local reparaciones = 0

	-- 1) Se limpian primero los mapas, quitando las entradas inválidas...
	for _, campo in { "Inventario", "MejorasNave" } do
		if type(datos[campo]) == "table" then
			reparaciones += repararMapa(datos[campo])
		end
	end

	-- 2) ...y después se rellena lo que falte. Así una mejora conocida de la nave con un valor inválido
	--    (que se acaba de quitar) vuelve a su valor inicial en lugar de desaparecer.
	reparaciones += conciliarEstructura(datos, PLANTILLA :: any)

	-- 3) Contadores y bando.
	reparaciones += repararContador(datos, "Nivel", 1)
	reparaciones += repararContador(datos, "XP", 0)
	reparaciones += repararContador(datos, "Monedas", 0)

	if not Bandos.EsValido(datos.Bando) then
		datos.Bando = Bandos.Ninguno
		reparaciones += 1
	end

	return datos :: any, reparaciones
end

return Esquema
