--!strict
--[[
	Genera src/shared/Personaje/RecursosHumanos.luau a partir de:
	  · modelos/personaje_humano/piezas.json            (lo escribe modelos/herramientas/personaje_humano.py):
	    parte, centro, tamaño y rol de cada pieza 3D.
	  · modelos/personaje_humano/roblox/datos/ids_studio.json   la malla de cada pieza y la imagen de cada textura,
	    como las da Studio al cargar lo que subió herramientas/subir_modelos.luau.

	Uso, desde la raíz del repositorio:
		lune run herramientas/generar_recursos_humanos             -- el personaje humano
		lune run herramientas/generar_recursos_humanos monstruo    -- el monstruo (modelos/personaje_monstruo → RecursosMonstruo)

	Falla (y no escribe nada) si a alguna pieza le falta su malla: así no se cuela una pieza invisible en el juego.
]]

local fs = require("@lune/fs")
local process = require("@lune/process")
local serde = require("@lune/serde")

local monstruo = process.args[1] == "monstruo"
local RAIZ = if monstruo then "modelos/personaje_monstruo" else "modelos/personaje_humano"
local SALIDA = if monstruo
	then "src/shared/Personaje/RecursosMonstruo.luau"
	else "src/shared/Personaje/RecursosHumanos.luau"

local piezas = serde.decode("json", fs.readFile(RAIZ .. "/piezas.json")).Piezas
local ids = serde.decode("json", fs.readFile(RAIZ .. "/roblox/datos/ids_studio.json"))

local function numero(n: number): string
	local s = string.format("%.4f", n)
	s = string.gsub(s, "0+$", "")
	s = string.gsub(s, "%.$", "")
	if s == "-0" then
		s = "0"
	end
	return s
end

local function vector(v: { number }): string
	return `\{ {numero(v[1])}, {numero(v[2])}, {numero(v[3])} \}`
end

-- Agrupa las piezas por elemento («Cabello_Corto», «Chaqueta_Piloto»...) en orden estable.
local porElemento: { [string]: { string } } = {}
local elementos: { string } = {}
local faltan: { string } = {}
for nombre in piezas do
	local elemento = string.match(nombre, "^(.-)__") :: string
	if porElemento[elemento] == nil then
		porElemento[elemento] = {}
		table.insert(elementos, elemento)
	end
	table.insert(porElemento[elemento], nombre)
	if ids.Mallas[nombre] == nil then
		table.insert(faltan, nombre)
	end
end
if #faltan > 0 then
	table.sort(faltan)
	error("Faltan las mallas de: " .. table.concat(faltan, ", ") .. " (súbelas y apunta sus IDs en ids_studio.json)")
end
table.sort(elementos)

local lineas = {
	"--!strict",
	"--[[",
	"\tGENERADO por herramientas/generar_recursos_humanos.luau"
		.. (if monstruo then " monstruo" else "")
		.. ": no lo edites a mano.",
	"",
	"\tRecursos subidos " .. (if monstruo then "del monstruo (cuernos y deformaciones):" else "del personaje humano:"),
	"\t  · Piezas[elemento]: las piezas 3D de cada elemento (" .. RAIZ .. ").",
	"\t    Malla: la malla subida. Parte: la parte del R6 a la que va. Rol: de qué color se pinta (ver DatosHumanos.Roles).",
	"\t    Centro: dónde va su centro respecto al centro de la parte (studs). Tamano: su tamaño en studs (las mallas",
	"\t    llegan de Roblox a otra escala: se les pone este tamaño al crearlas).",
	"\t  · Imagenes[nombre]: las texturas de la cara (Decals) y la rueda de color del editor.",
	"]]",
	"",
	"export type Pieza = {",
	"\tNombre: string,",
	"\tMalla: string,",
	"\tParte: string,",
	"\tRol: string,",
	"\tCentro: { number },",
	"\tTamano: { number },",
	"}",
	"",
	"local Recursos = {}",
	"",
	"Recursos.Piezas = {",
}
for _, elemento in elementos do
	local nombres = porElemento[elemento]
	table.sort(nombres)
	table.insert(lineas, `\t{elemento} = \{`)
	for _, nombre in nombres do
		local p = piezas[nombre]
		table.insert(
			lineas,
			`\t\t\{ Nombre = "{nombre}", Malla = "rbxassetid://{string.format("%d", ids.Mallas[nombre])}", Parte = "{p.Parte}", Rol = "{p.Rol}", Centro = {vector(
				p.Centro
			)}, Tamano = {vector(p.Tamano)} \},`
		)
	end
	table.insert(lineas, "\t},")
end
table.insert(lineas, "} :: { [string]: { Pieza } }")
table.insert(lineas, "")
table.insert(lineas, "Recursos.Imagenes = {")
local imagenes = {}
for nombre in ids.Imagenes do
	table.insert(imagenes, nombre)
end
table.sort(imagenes)
for _, nombre in imagenes do
	table.insert(lineas, `\t{nombre} = "rbxassetid://{string.format("%d", ids.Imagenes[nombre])}",`)
end
table.insert(lineas, "} :: { [string]: string }")
table.insert(lineas, "")
table.insert(lineas, "return Recursos")
table.insert(lineas, "")

fs.writeFile(SALIDA, table.concat(lineas, "\n"))
print(`[ok] {SALIDA}: {#elementos} elementos, {#imagenes} imágenes`)
