--!strict
--[[
	ServicioInventario: el inventario del jugador en el servidor, con el límite de su bodega.

	El inventario (`datos.Inventario`, ver Datos/Tipos) se guarda con el resto de datos del jugador. Este servicio es la
	ÚNICA vía para cambiarlo: aplica las reglas de Exploracion/Inventario y calcula el límite a partir de la mejora Carga
	de la nave (Naves/Estadisticas → Capacidad), así que no se puede llevar más de lo que cabe. Después de cada cambio
	avisa al cliente con ServicioReplicacion (los cambios de un mismo instante se agrupan en un solo envío).

	El cliente nunca cambia su inventario: solo recibe una copia para mostrarla.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local Estadisticas = require(Shared.Naves.Estadisticas)
local Reglas = require(Shared.Exploracion.Inventario)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioReplicacion = require(script.Parent.ServicioReplicacion)

local ServicioInventario = {}

-- Jugadores con cambios que aún no se han enviado al cliente.
local pendientes: { [Player]: boolean } = {}

-- Envía los datos al cliente una sola vez aunque en el mismo instante haya habido varios cambios.
function ServicioInventario.Replicar(jugador: Player)
	if pendientes[jugador] then
		return
	end
	pendientes[jugador] = true
	task.defer(function()
		pendientes[jugador] = nil
		if jugador.Parent ~= nil then
			ServicioReplicacion.EnviarDatos(jugador)
		end
	end)
end

-- Espacio total de la bodega del jugador (0 si sus datos no han cargado).
function ServicioInventario.Capacidad(jugador: Player): number
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return 0
	end
	return Estadisticas.Calcular(datos.MejorasNave).Capacidad
end

-- Espacio libre en la bodega.
function ServicioInventario.EspacioLibre(jugador: Player): number
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return 0
	end
	return Reglas.EspacioLibre(datos.Inventario, ServicioInventario.Capacidad(jugador))
end

-- ¿Cuántas unidades de `id` caben todavía?
function ServicioInventario.CuantoCabe(jugador: Player, id: string): number
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return 0
	end
	return Reglas.CuantoCabe(datos.Inventario, ServicioInventario.Capacidad(jugador), id)
end

-- Cantidad que tiene el jugador de `id`.
function ServicioInventario.Cantidad(jugador: Player, id: string): number
	local datos = ServicioDatos.ObtenerDatos(jugador)
	return if datos then Reglas.Cantidad(datos.Inventario, id) else 0
end

--[[
	Añade hasta `cantidad` unidades de `id` (las que quepan) y devuelve cuántas se han añadido. Si no cabe nada o el
	jugador no tiene datos, devuelve 0.
]]
function ServicioInventario.Anadir(jugador: Player, id: string, cantidad: number): number
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return 0
	end
	local anadidas = Reglas.Anadir(datos.Inventario, ServicioInventario.Capacidad(jugador), id, cantidad)
	if anadidas > 0 then
		ServicioInventario.Replicar(jugador)
	end
	return anadidas
end

-- Quita exactamente `cantidad` unidades de `id`. Devuelve false (sin cambiar nada) si no tiene suficientes.
function ServicioInventario.Quitar(jugador: Player, id: string, cantidad: number): boolean
	local datos = ServicioDatos.ObtenerDatos(jugador)
	if datos == nil then
		return false
	end
	local quitado = Reglas.Quitar(datos.Inventario, id, cantidad)
	if quitado then
		ServicioInventario.Replicar(jugador)
	end
	return quitado
end

-- Libera la memoria de los jugadores que se van.
function ServicioInventario.Iniciar()
	Players.PlayerRemoving:Connect(function(jugador: Player)
		pendientes[jugador] = nil
	end)
end

return ServicioInventario
