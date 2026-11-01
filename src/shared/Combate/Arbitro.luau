--!strict
--[[
	Arbitro: decide si una petición de habilidad es válida y qué cambia cuando lo es.

	Es el "juez" del combate. Trabaja solo con datos (tiempos, números, tablas): no toca Instancias, así
	que el servicio del servidor se limita a darle el estado del luchador y a ejecutar lo que decida, y las
	pruebas pueden comprobar cada regla sin Roblox.

	Orden de las comprobaciones (la primera que falla rechaza la petición):
	  1. ESTADO     vivo, sin aturdimiento y sin otra habilidad en marcha
	  2. HABILIDAD  existe
	  3. COOLDOWN   ha terminado
	  4. ENERGÍA    tiene suficiente
	  5. DISTANCIA  el punto señalado está dentro del alcance
]]

local Config = require(script.Parent.Config)
local Poderes = require(script.Parent.Datos.Poderes)
local Reglas = require(script.Parent.Reglas)

-- Estado de combate de un luchador (jugador o muñeco).
export type Luchador = {
	Estado: Reglas.Estado,
	Energia: number,
	EnergiaDesde: number, -- instante en que la energía valía `Energia`
	Cooldowns: { [string]: number }, -- id pedido -> instante en que termina su cooldown
	ComboPaso: number, -- último golpe del combo dado (0 = ninguno)
	ComboFin: number, -- instante en que se puede dar el siguiente golpe
	ComboVentana: number, -- segundos de margen para encadenar tras ComboFin
	InvulnerableHasta: number,
}

export type Resultado = {
	Ok: boolean,
	Motivo: string?, -- si !Ok: "muerto" | "aturdido" | "ocupado" | "desconocida" | "cooldown" | "energia" | "distancia"
	Habilidad: Poderes.Habilidad?, -- la habilidad real (para "Combo", el golpe que toca)
	Paso: number, -- golpe del combo (0 si no es combo)
	Distancia: number, -- distancia ya recortada al rango
	Energia: number, -- energía que tiene en este instante
}

local Arbitro = {}

-- Los únicos ids que se pueden pedir (los golpes internos del combo, Combo1..4, no).
local pedibles: { [string]: boolean } = {}
for _, id in Poderes.Solicitables do
	pedibles[id] = true
end

function Arbitro.NuevoLuchador(ahora: number): Luchador
	return {
		Estado = { Vivo = true, AturdidoHasta = 0, OcupadoHasta = 0 },
		Energia = Config.EnergiaMaxima,
		EnergiaDesde = ahora,
		Cooldowns = {},
		ComboPaso = 0,
		ComboFin = 0,
		ComboVentana = Config.VentanaCombo,
		InvulnerableHasta = 0,
	}
end

-- Energía que tiene el luchador en el instante `ahora`.
function Arbitro.EnergiaActual(luchador: Luchador, ahora: number): number
	return Reglas.EnergiaActual(
		luchador.Energia,
		Config.EnergiaMaxima,
		Config.EnergiaPorSegundo,
		luchador.EnergiaDesde,
		ahora
	)
end

-- Qué habilidad real corresponde a lo que pide el cliente. Para "Combo", el golpe que toca según el estado.
function Arbitro.Resolver(luchador: Luchador, idPedido: string, ahora: number): (Poderes.Habilidad?, number)
	if not pedibles[idPedido] then
		return nil, 0
	end
	if idPedido ~= Poderes.IdCombo then
		return Poderes.Obtener(idPedido), 0
	end
	local paso =
		Reglas.PasoDeCombo(luchador.ComboPaso, luchador.ComboFin, ahora, luchador.ComboVentana, Poderes.GolpesCombo)
	return Poderes.Obtener(`Combo{paso}`), paso
end

--[[
	Evalúa la petición sin modificar nada. `Vivo` lo actualiza antes quien llama (mirando la vida real).
]]
function Arbitro.Evaluar(luchador: Luchador, idPedido: string, ahora: number, distanciaPedida: number): Resultado
	local function rechazo(motivo: string): Resultado
		return { Ok = false, Motivo = motivo, Paso = 0, Distancia = 0, Energia = 0 }
	end

	local puede, motivo = Reglas.PuedeActuar(luchador.Estado, ahora)
	if not puede then
		return rechazo(motivo or "ocupado")
	end

	local habilidad, paso = Arbitro.Resolver(luchador, idPedido, ahora)
	if habilidad == nil then
		return rechazo("desconocida")
	end

	if not Reglas.CooldownListo(luchador.Cooldowns[idPedido], ahora) then
		return rechazo("cooldown")
	end

	local energia = Arbitro.EnergiaActual(luchador, ahora)
	if not Reglas.TieneEnergia(energia, habilidad.Energia) then
		return rechazo("energia")
	end

	local alcanzable, distancia = Reglas.AjustarAlcance(distanciaPedida, habilidad.Rango)
	if not alcanzable then
		return rechazo("distancia")
	end

	return { Ok = true, Habilidad = habilidad, Paso = paso, Distancia = distancia, Energia = energia }
end

--[[
	Aplica el uso de una habilidad ya aceptada: cobra la energía, arranca el cooldown, marca al luchador
	como ocupado (y, si la habilidad lo indica, invulnerable) y avanza el combo.
	Devuelve la duración total (carga + viaje + recuperación) para que el servicio inmovilice el tiempo justo.
]]
function Arbitro.Aplicar(luchador: Luchador, idPedido: string, resultado: Resultado, ahora: number): number
	local habilidad = resultado.Habilidad
	assert(resultado.Ok and habilidad ~= nil, "Arbitro.Aplicar necesita un resultado aceptado")

	luchador.Energia = resultado.Energia - habilidad.Energia
	luchador.EnergiaDesde = ahora
	luchador.Cooldowns[idPedido] = ahora + habilidad.Cooldown

	local tiempos = habilidad.Tiempos
	local duracion = tiempos.Carga + tiempos.Viaje + tiempos.Recuperacion
	luchador.Estado.OcupadoHasta = ahora + duracion
	if habilidad.Invulnerable then
		luchador.InvulnerableHasta = ahora + duracion
	end
	if habilidad.Combo then
		luchador.ComboPaso = resultado.Paso
		luchador.ComboFin = ahora + habilidad.Cooldown
		luchador.ComboVentana = habilidad.Combo.Ventana
	end
	return duracion
end

--[[
	¿Puede el objetivo recibir daño de este lanzador? Es enemigo (distinto bando), está vivo y no es
	invulnerable en este instante.
]]
function Arbitro.PuedeSerGolpeado(
	bandoLanzador: string,
	bandoObjetivo: string,
	objetivo: Luchador,
	ahora: number
): boolean
	return objetivo.Estado.Vivo
		and ahora >= objetivo.InvulnerableHasta
		and Reglas.SonEnemigos(bandoLanzador, bandoObjetivo)
end

return Arbitro
