--!strict
--[[
	Graficos/Niveles: reglas sin Roblox (se prueban con Lune).
	  · Valido(nombre): si es uno de los niveles.
	  · Recomendado(esMovil, calidadRoblox): el nivel que viene marcado la primera vez.
	  · HayQueMostrar(guardado, esStudio): si la pantalla sale al entrar.
]]

local Config = require(script.Parent.Config)

local Niveles = {}

function Niveles.Valido(nombre: any): boolean
	return type(nombre) == "string" and Config.Niveles[nombre] ~= nil
end

-- `calidadRoblox`: el control de gráficos de Roblox del jugador (1-10; 0 o nil = automático).
function Niveles.Recomendado(esMovil: boolean, calidadRoblox: number?): string
	local r = Config.Recomendacion
	local q = calidadRoblox or 0
	if esMovil then
		if q > 0 and q <= r.CalidadRobloxSencilla then
			return r.MovilSencillo
		end
		return r.Movil
	end
	if q >= r.CalidadRobloxPotente then
		return r.OrdenadorPotente
	end
	return r.Ordenador
end

-- `guardado`: el nivel de sus datos ("" si nunca ha elegido).
function Niveles.HayQueMostrar(guardado: string?, esStudio: boolean): boolean
	if esStudio and Config.MostrarSiempreEnStudio then
		return true
	end
	return not Niveles.Valido(guardado)
end

return Niveles
