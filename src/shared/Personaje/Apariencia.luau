--!strict
--[[
	Apariencia (Humanos): reglas sin Roblox (se prueban con Lune).

	Una apariencia es una tabla de ids: { Piel, Cara, Pelo, ColorPelo, Ropa, ColorRopa, ColorDetalle, Complemento }.
	  · Campos: el orden de los campos (es también el orden de los argumentos del remoto GuardarAparienciaHumano).
	  · Opciones(campo): la lista de opciones de ese campo (Personaje/DatosHumanos).
	  · Ids(campo): sus ids válidos.
	  · Validar(tabla): una apariencia completa y válida (lo que falte o no exista, por defecto).
	  · Aleatoria(azar): una apariencia al azar.
]]

local Datos = require(script.Parent.DatosHumanos)

local Apariencia = {}

export type Apariencia = {
	Piel: string,
	Cara: string,
	Pelo: string,
	ColorPelo: string,
	Ropa: string,
	ColorRopa: string,
	ColorDetalle: string,
	Complemento: string,
}

Apariencia.Campos = { "Piel", "Cara", "Pelo", "ColorPelo", "Ropa", "ColorRopa", "ColorDetalle", "Complemento" }

local LISTAS: { [string]: { any } } = {
	Piel = Datos.Pieles,
	Cara = Datos.Caras,
	Pelo = Datos.Peinados,
	ColorPelo = Datos.ColoresPelo,
	Ropa = Datos.Ropas,
	ColorRopa = Datos.ColoresRopa,
	ColorDetalle = Datos.ColoresRopa,
	Complemento = Datos.Complementos,
}

function Apariencia.Opciones(campo: string): { any }
	return LISTAS[campo] or {}
end

function Apariencia.Ids(campo: string): { string }
	local ids = {}
	for _, opcion in Apariencia.Opciones(campo) do
		table.insert(ids, opcion.Id)
	end
	return ids
end

-- La opción con ese id en ese campo, o nil.
function Apariencia.Buscar(campo: string, id: any): any
	for _, opcion in Apariencia.Opciones(campo) do
		if opcion.Id == id then
			return opcion
		end
	end
	return nil
end

function Apariencia.Validar(tabla: any): Apariencia
	local fuente = if type(tabla) == "table" then tabla else {}
	local resultado: { [string]: string } = {}
	for _, campo in Apariencia.Campos do
		local id = fuente[campo]
		resultado[campo] = if Apariencia.Buscar(campo, id) ~= nil then id else (Datos.Defecto :: any)[campo]
	end
	return resultado :: any
end

-- ¿Ha guardado ya una apariencia? (los datos de un jugador nuevo la tienen vacía)
function Apariencia.Hecha(tabla: any): boolean
	return type(tabla) == "table" and Apariencia.Buscar("Piel", tabla.Piel) ~= nil
end

function Apariencia.Aleatoria(azar: Random): Apariencia
	local resultado: { [string]: string } = {}
	for _, campo in Apariencia.Campos do
		local lista = Apariencia.Opciones(campo)
		resultado[campo] = lista[azar:NextInteger(1, #lista)].Id
	end
	return resultado :: any
end

-- Los colores reales (Color3 en hexadecimal) de una apariencia válida.
function Apariencia.Colores(a: Apariencia): { [string]: string }
	return {
		Piel = Apariencia.Buscar("Piel", a.Piel).Hex,
		Pelo = Apariencia.Buscar("ColorPelo", a.ColorPelo).Hex,
		Principal = Apariencia.Buscar("ColorRopa", a.ColorRopa).Hex,
		Detalle = Apariencia.Buscar("ColorDetalle", a.ColorDetalle).Hex,
		Oscuro = Datos.Oscuro,
		Claro = Datos.Claro,
	}
end

return Apariencia
