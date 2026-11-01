--!strict
--[[
	Calidad: cuánto "ruido" visual se permite según lo potente que sea el dispositivo.

	Hay tres niveles: Bajo, Medio y Alto. Cada efecto multiplica sus cantidades (partículas, escombros,
	segmentos de rayo...) por el factor del nivel actual, y las capas marcadas con `Minimo = "Alto"` se
	omiten por completo en niveles inferiores.

	  - En móvil se empieza en Medio y nunca se pasa de Medio.
	  - Se mide la fluidez (fotogramas por segundo): si baja de ~30 durante un par de segundos, se baja de
	    nivel; si se mantiene por encima de ~55 durante bastante rato, se sube (hasta el techo del dispositivo).

	Para fijar un nivel a mano (pruebas): `Calidad.Forzar("Bajo")`, y `Calidad.Forzar(nil)` para volver
	al ajuste automático.
]]

local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Senal = require(ReplicatedStorage:WaitForChild("Shared").Utilidades.Senal)

local NIVELES = { "Bajo", "Medio", "Alto" }
local POSICION: { [string]: number } = { Bajo = 1, Medio = 2, Alto = 3 }

-- Multiplicadores por tipo de elemento y nivel.
local FACTORES: { [string]: { [string]: number } } = {
	Bajo = { Particulas = 0.3, Escombros = 0.3, Luces = 0, Haces = 0.5, Desenfoque = 0 },
	Medio = { Particulas = 0.65, Escombros = 0.6, Luces = 1, Haces = 0.75, Desenfoque = 1 },
	Alto = { Particulas = 1, Escombros = 1, Luces = 1, Haces = 1, Desenfoque = 1 },
}

-- Medición de fluidez.
local VENTANA = 2 -- segundos por muestra
local FPS_BAJAR = 30
local FPS_SUBIR = 55
local MUESTRAS_PARA_SUBIR = 4 -- ventanas seguidas con buen rendimiento
local ESPERA_ENTRE_CAMBIOS = 4

local Calidad = {}

Calidad.EsMovil = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
Calidad.Cambio = Senal.nueva() -- se dispara con el nombre del nivel nuevo

local techo = if Calidad.EsMovil then "Medio" else "Alto"
local nivel = if Calidad.EsMovil then "Medio" else "Alto"
local forzado: string? = nil
local iniciado = false

-- Nivel actual ("Bajo" | "Medio" | "Alto").
function Calidad.Nivel(): string
	return forzado or nivel
end

local function cambiarA(nuevo: string)
	if nuevo ~= nivel then
		nivel = nuevo
		Calidad.Cambio:Disparar(Calidad.Nivel())
	end
end

-- Multiplicador del nivel actual para un tipo de elemento ("Particulas", "Escombros", "Luces", "Haces", "Desenfoque").
function Calidad.Factor(tipo: string): number
	return FACTORES[Calidad.Nivel()][tipo] or 1
end

-- ¿El nivel actual llega al mínimo que pide una capa? (nil = siempre)
function Calidad.Permite(minimo: string?): boolean
	if minimo == nil then
		return true
	end
	return (POSICION[Calidad.Nivel()] or 1) >= (POSICION[minimo] or 1)
end

-- Fija un nivel a mano (nil = automático).
function Calidad.Forzar(nuevo: string?)
	forzado = nuevo
	Calidad.Cambio:Disparar(Calidad.Nivel())
end

-- Empieza a vigilar la fluidez. Debe llamarse una sola vez.
function Calidad.Iniciar()
	if iniciado then
		return
	end
	iniciado = true

	local acumulado, fotogramas = 0, 0
	local buenasSeguidas = 0
	local ultimoCambio = os.clock()

	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		fotogramas += 1
		if acumulado < VENTANA then
			return
		end
		local fps = fotogramas / acumulado
		acumulado, fotogramas = 0, 0

		if forzado ~= nil or os.clock() - ultimoCambio < ESPERA_ENTRE_CAMBIOS then
			return
		end

		local posicion = POSICION[nivel]
		if fps < FPS_BAJAR and posicion > 1 then
			cambiarA(NIVELES[posicion - 1])
			buenasSeguidas = 0
			ultimoCambio = os.clock()
		elseif fps > FPS_SUBIR and posicion < POSICION[techo] then
			buenasSeguidas += 1
			if buenasSeguidas >= MUESTRAS_PARA_SUBIR then
				cambiarA(NIVELES[posicion + 1])
				buenasSeguidas = 0
				ultimoCambio = os.clock()
			end
		else
			buenasSeguidas = 0
		end
	end)
end

return Calidad
