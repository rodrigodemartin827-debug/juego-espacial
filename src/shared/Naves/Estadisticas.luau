--!strict
--[[
	Estadisticas (Naves): convierte los niveles de las mejoras del jugador en las cifras de su nave.

	Es una función PURA (no usa Roblox): recibe `datos.MejorasNave` y devuelve una tabla nueva con todas las
	estadísticas. El servidor la usa para decidir (vida, escudo, velocidad máxima, daño...) y el cliente para
	mostrar y para volar; al estar en la carpeta compartida los dos obtienen exactamente lo mismo.

	Se llama una vez al despegar (y al subir una mejora). Los datos del jugador no son de fiar del todo:
	un nivel que falta, que no es un número, que es negativo o que supera el máximo se corrige, nunca falla.
]]

local Mejoras = require(script.Parent.Datos.Mejoras)

export type Estadisticas = {
	Niveles: { [string]: number }, -- nivel ya saneado de cada mejora
	VidaMax: number,
	EscudoMax: number,
	RegenEscudo: number, -- escudo que se recupera por segundo
	RetrasoEscudo: number, -- segundos sin recibir daño antes de empezar a recargar
	VelocidadMax: number, -- studs/s sin turbo
	Aceleracion: number, -- studs/s²
	TurboMult: number, -- multiplicador de la velocidad máxima con turbo
	EnergiaTurbo: number, -- depósito de turbo
	Dano: number, -- daño de cada disparo
	Cadencia: number, -- disparos por segundo
	Alcance: number, -- studs
	RadioEscaner: number, -- studs
	Capacidad: number, -- espacio de la bodega
}

local Estadisticas = {}

-- Nivel saneado: entero entre 0 y el nivel máximo (cualquier cosa que no sea un número cuenta como 0).
function Estadisticas.NivelValido(valor: any): number
	if type(valor) ~= "number" or valor ~= valor then
		return 0
	end
	return math.clamp(math.floor(valor), 0, Mejoras.NivelMaximo)
end

--[[
	Calcula las estadísticas de la nave para esas mejoras (`mejoras` puede ser nil o estar incompleto).
]]
function Estadisticas.Calcular(mejoras: { [string]: any }?): Estadisticas
	local niveles: { [string]: number } = {}
	local resultado: { [string]: any } = { Niveles = niveles }

	for _, id in Mejoras.Orden do
		local nivel = Estadisticas.NivelValido(if mejoras then mejoras[id] else nil)
		niveles[id] = nivel
		for estadistica, efecto in Mejoras.Lista[id].Efectos do
			local valor = efecto.Base + efecto.PorNivel * nivel
			if efecto.Min then
				valor = math.max(valor, efecto.Min)
			end
			if efecto.Max then
				valor = math.min(valor, efecto.Max)
			end
			resultado[estadistica] = valor
		end
	end
	return resultado :: Estadisticas
end

return Estadisticas
