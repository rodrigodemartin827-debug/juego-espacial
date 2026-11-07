--!strict
--[[
	Apariencia (Humanos): reglas sin Roblox (se prueban con Lune).

	Una apariencia es una tabla:
	  · De opciones (un id de su lista en Personaje/DatosHumanos): Piel, Cabello, Cejas, Ojos, Nariz, Boca, Chaqueta,
	    Pantalon y Accesorio.
	  · De colores libres ("#RRGGBB", rueda de color): ColorPelo, ColorChaqueta, ColorPantalon y ColorDetalle.

	  · Campos: el orden de todos los campos (es también el orden de los argumentos del remoto GuardarAparienciaHumano).
	  · Categorias: las categorías de la lista del editor (con sus flechas ‹ ›), en orden.
	  · Opciones(campo) / Ids(campo) / Buscar(campo, id): las opciones de un campo de opciones.
	  · EsColor(valor) / NormalizarColor(valor): un color "#RRGGBB" válido.
	  · Validar(tabla): una apariencia completa y válida (lo que falte o no exista, por defecto).
	  · Hecha(tabla): si el jugador ya guardó una apariencia de este editor.
	  · Mover(campo, id, paso): la opción anterior o siguiente (las flechas), dando la vuelta.
	  · Aleatoria(azar): una apariencia al azar.
	  · Colores(a): el color de cada rol de las piezas (Pelo, Chaqueta, Pantalon, Detalle, Piel y los fijos).
]]

local Datos = require(script.Parent.DatosHumanos)

local Apariencia = {}

export type Apariencia = {
	Piel: string,
	Cabello: string,
	Cejas: string,
	Ojos: string,
	Nariz: string,
	Boca: string,
	Chaqueta: string,
	Pantalon: string,
	Accesorio: string,
	ColorPelo: string,
	ColorChaqueta: string,
	ColorPantalon: string,
	ColorDetalle: string,
}

export type Categoria = { Campo: string, Nombre: string }

Apariencia.CamposOpcion = { "Piel", "Cabello", "Cejas", "Ojos", "Nariz", "Boca", "Chaqueta", "Pantalon", "Accesorio" }
Apariencia.CamposColor = { "ColorPelo", "ColorChaqueta", "ColorPantalon", "ColorDetalle" }

Apariencia.Campos = table.clone(Apariencia.CamposOpcion)
for _, campo in Apariencia.CamposColor do
	table.insert(Apariencia.Campos, campo)
end

Apariencia.Categorias = {
	{ Campo = "Cabello", Nombre = "Cabello" },
	{ Campo = "Cejas", Nombre = "Cejas" },
	{ Campo = "Ojos", Nombre = "Ojos" },
	{ Campo = "Nariz", Nombre = "Nariz" },
	{ Campo = "Boca", Nombre = "Boca" },
	{ Campo = "Chaqueta", Nombre = "Chaqueta" },
	{ Campo = "Pantalon", Nombre = "Pantalón" },
	{ Campo = "Accesorio", Nombre = "Accesorio" },
} :: { Categoria }

local LISTAS: { [string]: { any } } = {
	Piel = Datos.Pieles,
	Cabello = Datos.Cabellos,
	Cejas = Datos.Cejas,
	Ojos = Datos.Ojos,
	Nariz = Datos.Narices,
	Boca = Datos.Bocas,
	Chaqueta = Datos.Chaquetas,
	Pantalon = Datos.Pantalones,
	Accesorio = Datos.Accesorios,
}

local ES_COLOR: { [string]: boolean } = {}
for _, campo in Apariencia.CamposColor do
	ES_COLOR[campo] = true
end

-- Patrón de un color: "#" y seis cifras hexadecimales.
Apariencia.PatronColor = "^#%x%x%x%x%x%x$"

function Apariencia.EsCampoColor(campo: string): boolean
	return ES_COLOR[campo] == true
end

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

-- Posición (1..n) de la opción en su lista, o nil.
function Apariencia.Indice(campo: string, id: any): number?
	for i, opcion in Apariencia.Opciones(campo) do
		if opcion.Id == id then
			return i
		end
	end
	return nil
end

function Apariencia.EsColor(valor: any): boolean
	return type(valor) == "string" and string.match(valor, Apariencia.PatronColor) ~= nil
end

-- "#a1b2c3" -> "#A1B2C3" (así dos colores iguales se guardan igual). nil si no es un color.
function Apariencia.NormalizarColor(valor: any): string?
	if not Apariencia.EsColor(valor) then
		return nil
	end
	return string.upper(valor)
end

-- ¿Es `valor` válido para `campo`?
function Apariencia.ValorValido(campo: string, valor: any): boolean
	if ES_COLOR[campo] then
		return Apariencia.EsColor(valor)
	end
	return Apariencia.Buscar(campo, valor) ~= nil
end

function Apariencia.Validar(tabla: any): Apariencia
	local fuente = if type(tabla) == "table" then tabla else {}
	local resultado: { [string]: string } = {}
	for _, campo in Apariencia.Campos do
		local valor = fuente[campo]
		if ES_COLOR[campo] then
			resultado[campo] = Apariencia.NormalizarColor(valor) or (Datos.Defecto :: any)[campo]
		else
			resultado[campo] = if Apariencia.Buscar(campo, valor) ~= nil then valor else (Datos.Defecto :: any)[campo]
		end
	end
	return resultado :: any
end

-- ¿Ha guardado ya una apariencia de este editor? (los datos de un jugador nuevo la tienen vacía; las de la versión
-- anterior del editor no tenían Chaqueta y se vuelven a pedir)
function Apariencia.Hecha(tabla: any): boolean
	return type(tabla) == "table"
		and Apariencia.Buscar("Piel", tabla.Piel) ~= nil
		and Apariencia.Buscar("Chaqueta", tabla.Chaqueta) ~= nil
end

-- La opción `paso` posiciones más allá (1 = siguiente, -1 = anterior), dando la vuelta al final de la lista.
function Apariencia.Mover(campo: string, id: any, paso: number): string
	local lista = Apariencia.Opciones(campo)
	assert(#lista > 0, "campo sin opciones: " .. campo)
	local i = Apariencia.Indice(campo, id) or 1
	local nuevo = ((i - 1 + paso) % #lista) + 1
	return lista[nuevo].Id
end

function Apariencia.Aleatoria(azar: Random): Apariencia
	local resultado: { [string]: string } = {}
	for _, campo in Apariencia.CamposOpcion do
		local lista = Apariencia.Opciones(campo)
		resultado[campo] = lista[azar:NextInteger(1, #lista)].Id
	end
	local muestras = Datos.Muestras
	-- El pelo casi siempre de un color natural (las seis primeras muestras); a veces, de fantasía.
	local natural = azar:NextInteger(1, 5) <= 4
	resultado.ColorPelo = muestras[if natural then azar:NextInteger(1, 6) else azar:NextInteger(7, #muestras)]
	resultado.ColorChaqueta = muestras[azar:NextInteger(7, #muestras)]
	resultado.ColorPantalon = muestras[azar:NextInteger(7, #muestras)]
	resultado.ColorDetalle = muestras[azar:NextInteger(7, #muestras)]
	return resultado :: any
end

-- El color ("#RRGGBB") de cada rol de las piezas en una apariencia válida.
function Apariencia.Colores(a: Apariencia): { [string]: string }
	local colores: { [string]: string } = {
		Piel = Apariencia.Buscar("Piel", a.Piel).Hex,
		Pelo = a.ColorPelo,
		Chaqueta = a.ColorChaqueta,
		Pantalon = a.ColorPantalon,
		Detalle = a.ColorDetalle,
	}
	for rol, datos in Datos.Roles do
		if datos.Color then
			colores[rol] = datos.Color
		end
	end
	return colores
end

return Apariencia
