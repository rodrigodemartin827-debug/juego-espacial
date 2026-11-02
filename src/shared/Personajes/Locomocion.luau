--!strict
--[[
	Locomocion: las decisiones del andar de monstruo, sin nada de Roblox (para poder probarlas con Lune).

	  - Locomocion.BandoDe: de qué bando es un personaje (el de su jugador, o el del muñeco).
	  - Locomocion.EsMonstruo: si ese personaje debe moverse con las animaciones de monstruo.
	  - Locomocion.Decidir: qué animación toca (Reposo, Andar, Correr, Saltar, Caer o ninguna) y a qué ritmo,
	    a partir de la velocidad del personaje y del estado de su Humanoid.

	El cliente (Personajes/AndarMonstruo) recoge los datos de cada personaje y aplica lo que se decide aquí.
]]

local Bandos = require(script.Parent.Parent.Juego.Bandos)

local Locomocion = {}

export type Estado = "Reposo" | "Andar" | "Correr" | "Saltar" | "Caer"

export type Entrada = {
	Velocidad: number, -- velocidad horizontal (studs/s)
	VelocidadVertical: number, -- studs/s, positiva hacia arriba
	-- Nombre del HumanoidStateType si se conoce (personaje propio). Nil en los de otros jugadores: su estado no
	-- llega fiable al cliente, así que se deduce de EnSuelo y de la velocidad vertical.
	EstadoHumanoid: string?,
	EnSuelo: boolean, -- hay suelo justo debajo (solo se usa si no hay EstadoHumanoid)
	Sentado: boolean,
	Muerto: boolean,
	SaltoTerminado: boolean?, -- la animación de saltar ya llegó al final
}

export type Ajustes = {
	EmpezarAndar: number,
	PararAndar: number,
	EmpezarCorrer: number,
	PararCorrer: number,
	RitmoMinimo: number,
	RitmoMaximo: number,
	VelocidadSalto: number,
	VelocidadCaida: number,
	[string]: any,
}

-- Estados del Humanoid en los que el monstruo NO pone su animación y deja la del Animate (sentarse, trepar,
-- nadar) o ninguna (muerto, ragdoll, físicas).
local SIN_ANIMACION_PROPIA = {
	Seated = true,
	Climbing = true,
	Swimming = true,
	Dead = true,
	Physics = true,
	Ragdoll = true,
	FallingDown = true,
	PlatformStanding = true,
	GettingUp = true,
}

--[[
	Bando de un personaje. `bandoJugador` es el atributo del Player (lo pone el servidor: ServicioBandos) y
	`bandoModelo` el del modelo (los muñecos de entrenamiento: Combate/Config.AtributoBando). Si el personaje es de
	un jugador manda SIEMPRE el del jugador: un cliente no puede hacerse pasar por otro bando poniendo un atributo en
	su personaje (además, los atributos que pone un cliente no se replican).
]]
function Locomocion.BandoDe(esDeJugador: boolean, bandoJugador: any, bandoModelo: any): string
	local bando = if esDeJugador then bandoJugador else bandoModelo
	return if Bandos.EsValido(bando) then bando else Bandos.Ninguno
end

-- ¿Se mueve como monstruo? Solo el bando Monstruos; los Humanos y quien no ha elegido siguen con lo normal.
function Locomocion.EsMonstruo(bando: string): boolean
	return bando == Bandos.Monstruos
end

-- Estados con su tipo exacto (un texto suelto se tomaría por `string`).
local REPOSO: Estado = "Reposo"
local ANDAR: Estado = "Andar"
local CORRER: Estado = "Correr"
local SALTAR: Estado = "Saltar"
local CAER: Estado = "Caer"

-- Estado en el suelo según la velocidad, con histéresis respecto al anterior.
local function enSuelo(anterior: Estado?, v: number, a: Ajustes): Estado
	if anterior == CORRER then
		if v >= a.PararCorrer then
			return CORRER
		end
		return if v >= a.PararAndar then ANDAR else REPOSO
	elseif anterior == ANDAR then
		if v >= a.EmpezarCorrer then
			return CORRER
		end
		return if v >= a.PararAndar then ANDAR else REPOSO
	end
	if v >= a.EmpezarCorrer then
		return CORRER
	end
	return if v >= a.EmpezarAndar then ANDAR else REPOSO
end

-- Estado en el aire: sube = Saltar (hasta que su animación termina), baja o flota = Caer.
local function enAire(anterior: Estado?, e: Entrada, subiendo: boolean): Estado
	if subiendo and not e.SaltoTerminado and anterior ~= CAER then
		return SALTAR
	end
	return CAER
end

--[[
	Decide la animación. Devuelve el estado (nil = ninguna animación de monstruo: se ve la del Animate o nada) y el
	ritmo de reproducción: en Andar y Correr, la velocidad real entre la VelocidadReferencia de esa animación (así
	los pies no patinan), dentro de [RitmoMinimo, RitmoMaximo]; en el resto, 1.
	`referencias` = { Andar = studs/s, Correr = studs/s }.
]]
function Locomocion.Decidir(
	anterior: Estado?,
	e: Entrada,
	a: Ajustes,
	referencias: { [string]: number }
): (Estado?, number)
	if e.Muerto or e.Sentado then
		return nil, 1
	end

	local estado: Estado
	local enElAire = anterior == SALTAR or anterior == CAER
	local humanoid = e.EstadoHumanoid
	if humanoid ~= nil then
		if SIN_ANIMACION_PROPIA[humanoid] then
			return nil, 1
		elseif humanoid == "Jumping" then
			estado = enAire(anterior, e, true)
		elseif humanoid == "Freefall" then
			estado = enAire(anterior, e, anterior == SALTAR and e.VelocidadVertical > 0)
		else
			estado = enSuelo(anterior, e.Velocidad, a)
		end
	elseif not e.EnSuelo and e.VelocidadVertical >= a.VelocidadSalto then
		estado = enAire(anterior, e, true)
	elseif not e.EnSuelo and (e.VelocidadVertical <= a.VelocidadCaida or enElAire) then
		-- Bajando rápido, o en lo alto del salto (casi sin velocidad vertical) tras haber saltado.
		estado = enAire(anterior, e, anterior == SALTAR and e.VelocidadVertical > 0)
	else
		estado = enSuelo(if enElAire then nil else anterior, e.Velocidad, a)
	end

	local referencia = referencias[estado]
	if referencia ~= nil and referencia > 0 then
		return estado, math.clamp(e.Velocidad / referencia, a.RitmoMinimo, a.RitmoMaximo)
	end
	return estado, 1
end

return Locomocion
