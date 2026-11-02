--!strict
--[[
	Entrada (combate): teclado y ratón.

	Cada habilidad de Datos/Poderes tiene una `Tecla` (nombre de un Enum.KeyCode, o "Click" para el botón
	principal del ratón). Este módulo escucha las teclas y llama a `solicitar(id)`. Mientras se mantiene
	pulsado el ratón se repite el combo. En móvil no se usa: los botones de la interfaz hacen lo mismo.

	Cambiar una tecla = cambiar `Tecla` en Datos/Poderes. No hay nada que tocar aquí.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Poderes = require(ReplicatedStorage:WaitForChild("Shared").Combate.Datos.Poderes)

local Entrada = {}

-- Segundos entre repeticiones del combo con el ratón mantenido.
local REPETICION_COMBO = 0.12

local iniciado = false

function Entrada.Iniciar(solicitar: (id: string) -> ())
	if iniciado then
		return
	end
	iniciado = true

	-- Nombre de tecla -> id de habilidad.
	local porTecla: { [string]: string } = {}
	local idClick: string? = nil
	for _, id in Poderes.Orden do
		local hab = Poderes.Presentacion(id)
		if hab then
			if hab.Tecla == "Click" then
				idClick = id
			else
				porTecla[hab.Tecla] = id
			end
		end
	end

	local ratonPulsado = false

	UserInputService.InputBegan:Connect(function(entrada: InputObject, procesado: boolean)
		if procesado then
			return -- el jugador estaba escribiendo o pulsando un botón de la interfaz
		end
		if entrada.UserInputType == Enum.UserInputType.Keyboard then
			local id = porTecla[entrada.KeyCode.Name]
			if id then
				solicitar(id)
			end
		elseif entrada.UserInputType == Enum.UserInputType.MouseButton1 and idClick then
			ratonPulsado = true
			solicitar(idClick)
			task.spawn(function()
				while ratonPulsado do
					task.wait(REPETICION_COMBO)
					if ratonPulsado then
						solicitar(idClick :: string)
					end
				end
			end)
		end
	end)

	UserInputService.InputEnded:Connect(function(entrada: InputObject)
		if entrada.UserInputType == Enum.UserInputType.MouseButton1 then
			ratonPulsado = false
		end
	end)
end

return Entrada
