--[[
	Marco: mini marco de pruebas para ejecutar con Lune (`lune run pruebas/ejecutar`).

	Cada archivo de `pruebas/casos/` devuelve una función que registra sus pruebas:

		return function(Marco)
			Marco.grupo("Mi módulo", function()
				Marco.prueba("hace lo esperado", function()
					Marco.igual(1 + 1, 2)
				end)
			end)
		end

	Las pruebas se ejecutan una detrás de otra y pueden esperar (task.wait): cada una corre en su
	propio hilo y tiene un tiempo máximo.
]]

local process = require("@lune/process")
local task = require("@lune/task")

local Marco = {}

-- Tiempo máximo de cada prueba, en segundos.
local TIEMPO_MAXIMO = 10

type Prueba = { Nombre: string, Funcion: () -> () }
type Grupo = { Nombre: string, Pruebas: { Prueba } }

local grupos: { Grupo } = {}
local grupoActual: Grupo? = nil

-- Funciones que se ejecutan al terminar la prueba en curso (sea cual sea su resultado).
local limpiezas: { () -> () } = {}

-- Funciones que se ejecutan al terminar CADA prueba para limpiar (sus errores se ignoran).
local ganchosFinales: { () -> () } = {}

-- Funciones que se ejecutan al terminar CADA prueba para comprobar algo: si lanzan un error, la
-- prueba se da por fallida.
local verificacionesFinales: { () -> () } = {}

-- ===== Registro de pruebas =====

function Marco.grupo(nombre: string, definir: () -> ())
	local grupo = { Nombre = nombre, Pruebas = {} }
	table.insert(grupos, grupo)
	grupoActual = grupo
	definir()
	grupoActual = nil
end

function Marco.prueba(nombre: string, funcion: () -> ())
	assert(grupoActual ~= nil, "Marco.prueba debe llamarse dentro de Marco.grupo")
	table.insert((grupoActual :: Grupo).Pruebas, { Nombre = nombre, Funcion = funcion })
end

-- Registra una función que se ejecutará al terminar la prueba actual.
function Marco.alTerminar(funcion: () -> ())
	table.insert(limpiezas, funcion)
end

-- Registra una función de limpieza que se ejecutará al terminar todas y cada una de las pruebas.
function Marco.despuesDeCadaPrueba(funcion: () -> ())
	table.insert(ganchosFinales, funcion)
end

-- Registra una comprobación que se ejecutará al terminar todas y cada una de las pruebas.
function Marco.verificarAlTerminar(funcion: () -> ())
	table.insert(verificacionesFinales, funcion)
end

-- ===== Aserciones =====

local function aTexto(valor: any): string
	if type(valor) == "string" then
		return `"{valor}"`
	end
	return tostring(valor)
end

local function fallar(mensaje: string, detalle: string?)
	error(if detalle then `{detalle}: {mensaje}` else mensaje, 3)
end

function Marco.verdadero(valor: any, detalle: string?)
	if not valor then
		fallar(`se esperaba un valor verdadero y se obtuvo {aTexto(valor)}`, detalle)
	end
end

function Marco.falso(valor: any, detalle: string?)
	if valor then
		fallar(`se esperaba un valor falso y se obtuvo {aTexto(valor)}`, detalle)
	end
end

function Marco.igual(real: any, esperado: any, detalle: string?)
	if real ~= esperado then
		fallar(`se esperaba {aTexto(esperado)} y se obtuvo {aTexto(real)}`, detalle)
	end
end

function Marco.distinto(real: any, noEsperado: any, detalle: string?)
	if real == noEsperado then
		fallar(`no se esperaba {aTexto(noEsperado)}`, detalle)
	end
end

function Marco.esNil(valor: any, detalle: string?)
	if valor ~= nil then
		fallar(`se esperaba nil y se obtuvo {aTexto(valor)}`, detalle)
	end
end

-- Comprueba que `texto` contiene `fragmento` (búsqueda literal, sin patrones).
function Marco.contiene(texto: any, fragmento: string, detalle: string?)
	if type(texto) ~= "string" or string.find(texto, fragmento, 1, true) == nil then
		fallar(`se esperaba que {aTexto(texto)} contuviera {aTexto(fragmento)}`, detalle)
	end
end

-- Comprueba que alguna de las cadenas de la lista contiene `fragmento`.
function Marco.algunoContiene(lista: { any }, fragmento: string, detalle: string?)
	for _, texto in lista do
		if type(texto) == "string" and string.find(texto, fragmento, 1, true) ~= nil then
			return
		end
	end
	fallar(`ningún elemento de la lista contiene {aTexto(fragmento)} (lista: {#lista} elementos)`, detalle)
end

-- Comprueba que llamar a `funcion` lanza un error; si se indica `fragmento`, que lo contenga.
function Marco.lanzaError(funcion: () -> (), fragmento: string?, detalle: string?)
	local ok, err = pcall(funcion)
	if ok then
		fallar("se esperaba que la función lanzara un error", detalle)
	end
	if fragmento ~= nil and string.find(tostring(err), fragmento, 1, true) == nil then
		fallar(`el error {aTexto(tostring(err))} no contiene {aTexto(fragmento)}`, detalle)
	end
end

local function igualProfundo(a: any, b: any): boolean
	if type(a) ~= "table" or type(b) ~= "table" then
		return a == b
	end
	for clave, valor in a do
		if not igualProfundo(valor, b[clave]) then
			return false
		end
	end
	for clave in b do
		if a[clave] == nil then
			return false
		end
	end
	return true
end

-- Compara dos valores recursivamente (tablas incluidas).
function Marco.igualProfundo(real: any, esperado: any, detalle: string?)
	if not igualProfundo(real, esperado) then
		fallar("las tablas no son iguales", detalle)
	end
end

-- Espera (cediendo el hilo) hasta que `condicion()` sea verdadera, o falla si pasa `maximo` segundos.
function Marco.esperarHasta(condicion: () -> any, detalle: string?, maximo: number?)
	local limite = os.clock() + (maximo or 3)
	while not condicion() do
		if os.clock() > limite then
			fallar("se agotó el tiempo esperando la condición", detalle)
		end
		task.wait(0.002)
	end
end

-- Cede el hilo unos ciclos para que se completen las tareas diferidas (remotos, señales...).
function Marco.dejarCorrer(ciclos: number?)
	for _ = 1, ciclos or 3 do
		task.wait()
	end
end

-- ===== Ejecución =====

local function ejecutarPrueba(prueba: Prueba): (boolean, string?)
	local terminada = false
	local exito = false
	local mensaje: string? = nil

	task.spawn(function()
		local ok, err = xpcall(prueba.Funcion, function(motivo)
			return `{tostring(motivo)}\n{debug.traceback("", 2)}`
		end)
		exito = ok
		if not ok then
			mensaje = tostring(err)
		end
		terminada = true
	end)

	local limite = os.clock() + TIEMPO_MAXIMO
	while not terminada and os.clock() < limite do
		task.wait(0.002)
	end
	if not terminada then
		return false, `la prueba superó el tiempo máximo de {TIEMPO_MAXIMO} s`
	end

	-- Si la prueba ha ido bien, se aplican las comprobaciones finales (p. ej. "sin errores en hilos").
	if exito then
		for _, verificar in verificacionesFinales do
			local ok, err = pcall(verificar)
			if not ok then
				exito = false
				mensaje = tostring(err)
				break
			end
		end
	end

	for _, limpiar in limpiezas do
		pcall(limpiar)
	end
	table.clear(limpiezas)
	for _, gancho in ganchosFinales do
		pcall(gancho)
	end
	return exito, mensaje
end

-- Ejecuta todas las pruebas registradas. `filtro` limita las que se ejecutan a las que lo contienen
-- en el nombre del grupo o de la prueba. Termina el proceso con código 1 si alguna falla.
function Marco.ejecutar(filtro: string?)
	local total, falladas = 0, 0
	local inicio = os.clock()

	for _, grupo in grupos do
		local impreso = false
		for _, prueba in grupo.Pruebas do
			local coincide = filtro == nil
				or string.find(string.lower(grupo.Nombre), string.lower(filtro), 1, true) ~= nil
				or string.find(string.lower(prueba.Nombre), string.lower(filtro), 1, true) ~= nil
			if coincide then
				if not impreso then
					print(`\n{grupo.Nombre}`)
					impreso = true
				end
				total += 1
				local ok, mensaje = ejecutarPrueba(prueba)
				if ok then
					print(`  ✔ {prueba.Nombre}`)
				else
					falladas += 1
					print(`  ✘ {prueba.Nombre}`)
					for linea in string.gmatch(tostring(mensaje), "[^\n]+") do
						print(`      {linea}`)
					end
				end
			end
		end
	end

	print(`\n{total - falladas} de {total} pruebas correctas ({string.format("%.2f", os.clock() - inicio)} s)`)
	-- Se termina el proceso a la fuerza: los bucles de los servicios simulados no acaban solos.
	process.exit(if falladas == 0 and total > 0 then 0 else 1)
end

return Marco
