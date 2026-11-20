--!strict
--[[
	EstadoUI: la única fuente de datos de la interfaz.

	Une lo que YA existe en el juego con los datos de demostración de lo que todavía no existe, para que las pantallas
	no tengan que saber de dónde viene cada cosa:

	  REAL (servidor)                                     DEMO (DatosDemo, hasta que exista el sistema)
	  - nombre, nivel, XP, monedas, bando (ServicioDatos)   - gemas, clan, título, puntos de atributos y de poderes
	  - materiales de la bodega y su capacidad (Carga)      - equipo (armas, armaduras, accesorios), consumibles
	  - especies descubiertas y cuántas veces (escáner)     - árbol de poderes, clan, ranked, planetas pequeños
	  - poderes del HUD: nombre, tecla, cooldown, energía   - escudo personal, estadísticas detalladas

	El cliente nunca decide nada: lo que aquí se "cambia" (equipar, repartir puntos, desbloquear un nodo) solo cambia
	los datos de demostración en esta sesión y se avisa de ello. Cuando esos sistemas existan, estas funciones pasarán
	a ENVIAR una petición por ServicioRed y a esperar la respuesta del servidor, que es quien valida.

	Avisa de los cambios con la señal `Cambio` (argumento: qué ha cambiado: "Datos", "Equipo", "Stats", "Combate",
	"Arbol", "Vida").
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Especies = require(Shared.Exploracion.Datos.Especies)
local Estadisticas = require(Shared.Naves.Estadisticas)
local Inventario = require(Shared.Exploracion.Inventario)
local Objetos = require(Shared.Exploracion.Datos.Objetos)
local Poderes = require(Shared.Combate.Datos.Poderes)
local Senal = require(Shared.Utilidades.Senal)
local Tipos = require(Shared.Datos.Tipos)

local Cliente = script.Parent.Parent.Parent
local ServicioDatos = require(Cliente.Servicios.ServicioDatos)
local ServicioRed = require(Cliente.Servicios.ServicioRed)

local CatalogoUI = require(script.Parent.Datos.CatalogoUI)
local DatosDemo = require(script.Parent.Datos.DatosDemo)

local EstadoUI = {}

EstadoUI.Cambio = Senal.nueva()

-- ===== Tipos que usan las pantallas =====

export type ObjetoUI = {
	Id: string,
	Nombre: string,
	Arte: string,
	Filtro: string,
	Slot: string?,
	Rareza: string,
	Nivel: number?,
	Cantidad: number?,
	Stats: { DatosDemo.Valor }?,
	Descripcion: string,
	Pasiva: string?,
	Real: boolean, -- true si viene del inventario de verdad (servidor)
}

export type Jugador = {
	Nombre: string,
	Nivel: number,
	XP: number,
	FraccionXP: number,
	Monedas: number,
	Gemas: number,
	Bando: string, -- "Humanos" | "Monstruos" | "Ninguno"
	Clan: string,
	Titulo: string,
	Clase: string,
	PuntosStats: number,
	PuntosHabilidad: number,
}

export type EntradaIndice = DatosDemo.EntradaIndice
export type Indice = { Total: number, Lista: { EntradaIndice }, Ocultas: number }

export type EstadoCombate = {
	Energia: number,
	EnergiaMax: number,
	Regeneracion: number,
	Desde: number, -- os.clock() del último mensaje
	Fin: { [string]: number }, -- os.clock() en que termina el cooldown de cada habilidad
	Duracion: { [string]: number }, -- duración total del cooldown en curso
}

-- ===== Estado local (demo) =====

local equipado: { [string]: string } = table.clone(DatosDemo.Equipado)
local stats: { [string]: { number } } = {}
for id, valores in DatosDemo.Stats do
	stats[id] = table.clone(valores)
end
local puntosStats = DatosDemo.Jugador.PuntosStats
local puntosHabilidad = DatosDemo.Jugador.PuntosHabilidad
local gemas = DatosDemo.Jugador.Gemas
local desbloqueados: { [string]: { [number]: boolean } } = {}
for _, rama in DatosDemo.Arbol do
	desbloqueados[rama.Id] = {}
	for i, nodo in rama.Nodos do
		desbloqueados[rama.Id][i] = nodo.E == 1
	end
end

local combate: EstadoCombate = {
	Energia = 100,
	EnergiaMax = 100,
	Regeneracion = 0,
	Desde = os.clock(),
	Fin = {},
	Duracion = {},
}

local objetosDemoPorId: { [string]: DatosDemo.ObjetoDemo } = {}
for _, objeto in DatosDemo.Objetos do
	objetosDemoPorId[objeto.Id] = objeto
end

-- ===== Jugador =====

local function datosReales(): Tipos.Datos?
	return ServicioDatos.Obtener()
end

function EstadoUI.Jugador(): Jugador
	local datos = datosReales()
	local jugador = Players.LocalPlayer
	return {
		Nombre = if jugador then jugador.Name else "Jugador",
		Nivel = if datos then datos.Nivel else 1,
		XP = if datos then datos.XP else 0,
		FraccionXP = DatosDemo.Jugador.FraccionXP,
		Monedas = if datos then datos.Monedas else 0,
		Gemas = gemas,
		Bando = if datos then datos.Bando else "Ninguno",
		Clan = DatosDemo.Jugador.Clan,
		Titulo = DatosDemo.Jugador.Titulo,
		Clase = DatosDemo.Jugador.Clase,
		PuntosStats = puntosStats,
		PuntosHabilidad = puntosHabilidad,
	}
end

-- Raza que se enseña: la del bando (sin bando todavía, la de los Humanos).
function EstadoUI.Raza(): DatosDemo.Raza
	local bando = EstadoUI.Jugador().Bando
	return DatosDemo.Razas[bando] or DatosDemo.Razas.Humanos
end

-- ===== Inventario =====

-- Objeto del inventario real (Exploracion/Datos/Objetos) en formato de la UI.
local function objetoReal(id: string, cantidad: number): ObjetoUI
	local datos = Objetos.Lista[id]
	local presentacion = CatalogoUI.Objetos[id]
	return {
		Id = id,
		Nombre = if datos then datos.Nombre else id,
		Arte = if presentacion then presentacion.Arte else CatalogoUI.ArteGenerico,
		Filtro = if presentacion then presentacion.Filtro else "Materiales",
		Rareza = if presentacion then presentacion.Rareza else "Comun",
		Cantidad = cantidad,
		Descripcion = if datos then datos.Descripcion else "",
		Real = true,
	}
end

local function objetoDemo(o: DatosDemo.ObjetoDemo): ObjetoUI
	return {
		Id = o.Id,
		Nombre = o.Nombre,
		Arte = o.Arte,
		Filtro = o.Filtro,
		Slot = o.Slot,
		Rareza = o.Rareza,
		Nivel = o.Nivel,
		Cantidad = o.Cantidad,
		Stats = o.Stats,
		Descripcion = o.Descripcion,
		Pasiva = o.Pasiva,
		Real = false,
	}
end

-- Lista del inventario: primero el equipo (demo), después los materiales reales en el orden de Objetos.Orden, y al final
-- consumibles y especiales (demo).
function EstadoUI.Objetos(): { ObjetoUI }
	local lista: { ObjetoUI } = {}
	for _, o in DatosDemo.Objetos do
		if o.Slot then
			table.insert(lista, objetoDemo(o))
		end
	end
	local datos = datosReales()
	if datos then
		local vistos: { [string]: boolean } = {}
		for _, id in Objetos.Orden do
			local cantidad = datos.Inventario[id]
			if cantidad and cantidad > 0 then
				table.insert(lista, objetoReal(id, cantidad))
				vistos[id] = true
			end
		end
		-- Objetos que no están en Objetos.Orden (por si el servidor guarda alguno nuevo).
		for id, cantidad in datos.Inventario do
			if not vistos[id] and cantidad > 0 then
				table.insert(lista, objetoReal(id, cantidad))
			end
		end
	end
	for _, o in DatosDemo.Objetos do
		if not o.Slot then
			table.insert(lista, objetoDemo(o))
		end
	end
	return lista
end

function EstadoUI.Objeto(id: string): ObjetoUI?
	local demo = objetosDemoPorId[id]
	if demo then
		return objetoDemo(demo)
	end
	local datos = datosReales()
	if datos and datos.Inventario[id] then
		return objetoReal(id, datos.Inventario[id])
	end
	return nil
end

-- Espacio ocupado y capacidad de la bodega (la capacidad sale de la mejora Carga de la nave).
function EstadoUI.Bodega(): (number, number)
	local datos = datosReales()
	if datos == nil then
		return 0, 0
	end
	return Inventario.Volumen(datos.Inventario), Estadisticas.Calcular(datos.MejorasNave).Capacidad
end

function EstadoUI.CasillasOcultas(): number
	return DatosDemo.CasillasOcultas
end

-- ===== Equipo (demo) =====

function EstadoUI.Equipado(): { [string]: string }
	return equipado
end

function EstadoUI.EstaEquipado(id: string): boolean
	for _, puesto in equipado do
		if puesto == id then
			return true
		end
	end
	return false
end

-- Pone (o quita, si ya estaba) un objeto en su slot. Devuelve el objeto y si ha quedado puesto.
-- TODO(servidor): enviar "EquiparObjeto" y aplicar la respuesta; ahora solo cambia la demo de esta sesión.
function EstadoUI.Equipar(id: string): (ObjetoUI?, boolean)
	local objeto = EstadoUI.Objeto(id)
	if objeto == nil or objeto.Slot == nil then
		return nil, false
	end
	local slot = objeto.Slot :: string
	local puesto = equipado[slot] ~= id
	if puesto then
		equipado[slot] = id
	else
		equipado[slot] = nil
	end
	EstadoUI.Cambio:Disparar("Equipo")
	return objeto, puesto
end

function EstadoUI.Desequipar(slot: string): ObjetoUI?
	local id = equipado[slot]
	if id == nil then
		return nil
	end
	equipado[slot] = nil
	EstadoUI.Cambio:Disparar("Equipo")
	return EstadoUI.Objeto(id)
end

-- ===== Atributos (demo) =====

function EstadoUI.Stats(): { [string]: { number } }
	return stats
end

-- Reparte puntos de atributo. TODO(servidor): validarlo en el servidor (puntos disponibles, máximos).
function EstadoUI.RepartirPuntos(reparto: { [string]: number }): number
	local total = 0
	for id, cantidad in reparto do
		if stats[id] and cantidad > 0 then
			total += cantidad
		end
	end
	if total <= 0 or total > puntosStats then
		return 0
	end
	for id, cantidad in reparto do
		if stats[id] and cantidad > 0 then
			stats[id][1] += cantidad
		end
	end
	puntosStats -= total
	EstadoUI.Cambio:Disparar("Stats")
	return total
end

-- ===== Árbol de poderes (demo) =====

-- Estado de un nodo: 1 = desbloqueado, 2 = disponible (el siguiente de su rama), 0 = bloqueado.
function EstadoUI.EstadoNodos(idRama: string): { number }
	local resultado: { number } = {}
	local siguiente = true
	for _, rama in DatosDemo.Arbol do
		if rama.Id == idRama then
			for i in rama.Nodos do
				if desbloqueados[idRama][i] then
					resultado[i] = 1
				elseif siguiente then
					resultado[i] = 2
					siguiente = false
				else
					resultado[i] = 0
				end
			end
		end
	end
	return resultado
end

-- Desbloquea el siguiente nodo de una rama si hay puntos. TODO(servidor): validarlo en el servidor.
function EstadoUI.DesbloquearNodo(idRama: string, indice: number): boolean
	local estados = EstadoUI.EstadoNodos(idRama)
	if estados[indice] ~= 2 then
		return false
	end
	for _, rama in DatosDemo.Arbol do
		if rama.Id == idRama then
			local coste = rama.Nodos[indice].Coste
			if puntosHabilidad < coste then
				return false
			end
			puntosHabilidad -= coste
			desbloqueados[idRama][indice] = true
			EstadoUI.Cambio:Disparar("Arbol")
			return true
		end
	end
	return false
end

-- ===== Gemas (demo) =====

function EstadoUI.Gemas(): number
	return gemas
end

-- ===== Índice =====

-- Entradas del Índice de una categoría ("Criaturas" | "Minerales" | "Plantas" | "Planetas").
-- Criaturas, plantas y minerales salen de Especies y de los descubrimientos REALES del jugador.
function EstadoUI.Indice(categoria: string): Indice
	if categoria == "Planetas" then
		local demo = DatosDemo.IndicePlanetas
		return { Total = demo.Total, Lista = demo.Lista, Ocultas = demo.Total - #demo.Lista }
	end
	local datos = datosReales()
	local descubiertos = if datos then datos.Descubrimientos else {}
	local ids: { string } = {}
	for id, especie in Especies.Lista do
		if CatalogoUI.CategoriaIndice[especie.Categoria] == categoria then
			table.insert(ids, id)
		end
	end
	table.sort(ids, function(a, b)
		return Especies.Lista[a].Nombre < Especies.Lista[b].Nombre
	end)
	local lista: { EntradaIndice } = {}
	for _, id in ids do
		local veces = descubiertos[id]
		if veces and veces > 0 then
			local especie = Especies.Lista[id]
			local p = CatalogoUI.Especies[id]
			local habitat = "Desconocido"
			for _, fila in especie.Datos do
				if fila[1] == "Hábitat" or fila[1] == "Aparece en" then
					habitat = fila[2] or habitat
				end
			end
			table.insert(lista, {
				N = especie.Nombre,
				A = if p then p.Arte else CatalogoUI.ArteGenerico,
				Tipo = if p then p.Tipo else especie.Categoria,
				Peligro = if p then p.Peligro else 0,
				Rareza = CatalogoUI.RarezaEspecie[especie.Rareza] or "Comun",
				Habitat = habitat,
				Drops = if p then p.Drops else {},
				Lore = especie.Descripcion,
				Veces = veces,
			})
		end
	end
	return { Total = #ids, Lista = lista, Ocultas = #ids - #lista }
end

-- ===== Combate (real: EstadoCombate del servidor) =====

function EstadoUI.Combate(): EstadoCombate
	return combate
end

-- Energía actual (avanza sola entre mensajes del servidor, como en Combate/Interfaz).
function EstadoUI.EnergiaActual(): number
	return math.min(combate.EnergiaMax, combate.Energia + combate.Regeneracion * (os.clock() - combate.Desde))
end

-- Segundos que le quedan al cooldown de una habilidad (0 si está lista) y su duración total.
function EstadoUI.Cooldown(id: string): (number, number)
	local fin = combate.Fin[id]
	if fin == nil then
		return 0, 1
	end
	return math.max(0, fin - os.clock()), combate.Duracion[id] or 1
end

-- Presentación de una habilidad de Combate/Datos/Poderes (nombre, tecla, cooldown, coste).
function EstadoUI.Habilidad(id: string): Poderes.Habilidad?
	return Poderes.Presentacion(id)
end

local function alRecibirCombate(estado: any)
	if type(estado) ~= "table" then
		return
	end
	combate.Energia = tonumber(estado.Energia) or combate.Energia
	combate.EnergiaMax = tonumber(estado.EnergiaMax) or combate.EnergiaMax
	combate.Regeneracion = tonumber(estado.Regeneracion) or combate.Regeneracion
	combate.Desde = os.clock()
	local ahora = os.clock()
	local nuevos: { [string]: number } = {}
	if type(estado.Cooldowns) == "table" then
		for id, restante in estado.Cooldowns do
			if type(id) == "string" and type(restante) == "number" and restante > 0 then
				nuevos[id] = restante
			end
		end
	end
	for id in combate.Fin do
		if nuevos[id] == nil then
			combate.Fin[id] = nil
			combate.Duracion[id] = nil
		end
	end
	for id, restante in nuevos do
		-- La duración total: la mayor vista mientras sigue activo (un mensaje tardío trae un resto menor).
		local previa = combate.Duracion[id]
		local sigue = previa ~= nil and combate.Fin[id] ~= nil and previa >= restante
		combate.Duracion[id] = if sigue then previa else restante
		combate.Fin[id] = ahora + restante
	end
	EstadoUI.Cambio:Disparar("Combate")
end

-- ===== Arranque =====

local iniciado = false

-- Empieza a escuchar los datos del jugador y el estado de combate. Después de ServicioRed y ServicioDatos.
function EstadoUI.Iniciar()
	if iniciado then
		return
	end
	iniciado = true
	ServicioDatos.Actualizados:Conectar(function()
		EstadoUI.Cambio:Disparar("Datos")
	end)
	ServicioRed.Conectar("EstadoCombate", alRecibirCombate)
end

return EstadoUI
