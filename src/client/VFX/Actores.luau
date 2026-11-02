--!strict
--[[
	Actores: un único bucle por fotograma para todos los efectos que se mueven "a mano".

	En vez de crear una conexión a RenderStepped por cada proyectil, escombro o rayo parpadeante, cada
	efecto registra una función `actualizar(dt)` y este módulo las llama a todas desde UNA sola conexión.
	La función devuelve `true` cuando ha terminado y se retira. La conexión solo existe mientras hay
	actores en marcha.

	Un error dentro de un actor lo retira y avisa, sin afectar a los demás.
]]

local RunService = game:GetService("RunService")

export type Actor = (dt: number) -> boolean

local Actores = {}

local lista: { Actor } = {}
local conexion: RBXScriptConnection? = nil

local function paso(dt: number)
	local indice = 1
	while indice <= #lista do
		local ok, terminado = pcall(lista[indice], dt)
		if not ok then
			warn(`[VFX] Error en un actor, se retira: {terminado}`)
			terminado = true
		end
		if terminado then
			table.remove(lista, indice)
		else
			indice += 1
		end
	end
	if #lista == 0 and conexion then
		conexion:Disconnect()
		conexion = nil
	end
end

-- Registra un actor. Se llamará cada fotograma hasta que devuelva `true`.
function Actores.Agregar(actualizar: Actor)
	table.insert(lista, actualizar)
	if conexion == nil then
		conexion = RunService.RenderStepped:Connect(paso)
	end
end

-- Número de actores en marcha (para depurar).
function Actores.Cantidad(): number
	return #lista
end

return Actores
