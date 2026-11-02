--!strict
--[[
	Catalogo: TODAS las animaciones hechas por código que conoce el juego, con un nombre único cada una.

	  - Las del combate (Combate/Datos/Animaciones), con su nombre tal cual: "Combo1", "Impacto"...
	  - Las del andar de monstruo (Personajes/Datos/AnimacionesMonstruo), horneadas con Animacion/Horneado y con
	    los nombres de AnimacionesMonstruo.Nombres: "Monstruo_Reposo", "Monstruo_Andar"...

	VFX/Animador lo usa para construir la animación de un nombre cuando no tiene un ID de asset en
	Combate/Datos/Recursos.Animaciones. Todas vienen en el formato de Combate/Datos/Animaciones (Cuadros con Poses).
]]

local Shared = script.Parent.Parent
local Animaciones = require(Shared.Combate.Datos.Animaciones)
local AnimacionesMonstruo = require(Shared.Personajes.Datos.AnimacionesMonstruo)
local Horneado = require(script.Parent.Horneado)

local Catalogo = {}

-- Nombre de la animación -> estado de AnimacionesMonstruo ("Monstruo_Andar" -> "Andar").
local ESTADO_DE: { [string]: string } = {}
for estado, nombre in AnimacionesMonstruo.Nombres do
	ESTADO_DE[nombre] = estado
end

local horneadas: { [string]: any } = {}

-- Definición (formato Combate/Datos/Animaciones) de la animación `nombre`, o nil si no existe.
function Catalogo.Definicion(nombre: string): any
	local combate = Animaciones.Definiciones[nombre]
	if combate ~= nil then
		return combate
	end
	local estado = ESTADO_DE[nombre]
	if estado == nil then
		return nil
	end
	local guardada = horneadas[nombre]
	if guardada == nil then
		guardada = Horneado.Hornear(AnimacionesMonstruo.Definiciones[estado])
		horneadas[nombre] = guardada
	end
	return guardada
end

-- Todos los nombres, ordenados alfabéticamente (el orden es siempre el mismo en todos los clientes).
function Catalogo.Nombres(): { string }
	local nombres: { string } = {}
	for nombre in Animaciones.Definiciones do
		table.insert(nombres, tostring(nombre))
	end
	for nombre in ESTADO_DE do
		table.insert(nombres, nombre)
	end
	table.sort(nombres)
	return nombres
end

return Catalogo
