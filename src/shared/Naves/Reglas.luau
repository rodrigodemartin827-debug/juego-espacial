--!strict
--[[
	Reglas (Naves): las reglas del vuelo y del combate de naves como FUNCIONES PURAS.

	Como Combate/Reglas, no usan Instancias ni servicios de Roblox: reciben números y tablas y devuelven un
	resultado. El servidor las aplica a cada petición del cliente y las pruebas las ejecutan fuera de Studio.

	Los puntos y las direcciones son cualquier cosa con campos X, Y, Z (un Vector3 o una tabla { X=, Y=, Z= }).
	Todas las funciones que cambian un estado lo dicen en su descripción.
]]

local Config = require(script.Parent.Config)
local Estadisticas = require(script.Parent.Estadisticas)

type Estadisticas = Estadisticas.Estadisticas

export type Punto = { X: number, Y: number, Z: number }

-- Vida y escudo de una nave. El escudo se recarga "perezosamente": no hay bucle, se calcula al consultarlo.
export type Estado = {
	Vida: number,
	Escudo: number, -- escudo que había en el instante `DesdeEscudo`
	DesdeEscudo: number, -- instante del último daño (o del despegue)
	InmuneHasta: number, -- no recibe daño hasta este instante
}

-- Depósito de turbo, también calculado "perezosamente".
export type Turbo = {
	Energia: number, -- energía que había en el instante `Desde`
	Desde: number,
	Activo: boolean, -- si el piloto lo tiene pulsado
}

export type ResultadoDano = {
	Aplicado: boolean, -- false si era inmune o el daño no valía
	DanoEscudo: number, -- lo que absorbió el escudo
	DanoCasco: number, -- lo que llegó al casco
	Destruida: boolean,
}

local Reglas = {}

-- ===== Vida y escudo =====

-- Estado de una nave recién despegada: todo lleno, e inmune unos segundos.
function Reglas.NuevoEstado(stats: Estadisticas, ahora: number): Estado
	return {
		Vida = stats.VidaMax,
		Escudo = stats.EscudoMax,
		DesdeEscudo = ahora,
		InmuneHasta = ahora + Config.SegundosInmunidadInicial,
	}
end

--[[
	Escudo que tiene la nave en `ahora`. Tras recibir daño espera `RetrasoEscudo` segundos y después se
	recarga a `RegenEscudo` por segundo, hasta el máximo.
]]
function Reglas.EscudoActual(estado: Estado, stats: Estadisticas, ahora: number): number
	local inicioRecarga = estado.DesdeEscudo + stats.RetrasoEscudo
	if ahora <= inicioRecarga then
		return math.min(estado.Escudo, stats.EscudoMax)
	end
	return math.min(stats.EscudoMax, estado.Escudo + stats.RegenEscudo * (ahora - inicioRecarga))
end

--[[
	Aplica `dano` a la nave (MODIFICA `estado`). El escudo absorbe primero; lo que sobra va al casco.
	Con `ignorarEscudo` todo va al casco (el calor del sol, por ejemplo), pero el escudo deja de recargarse igual.
	Un daño que no es un número positivo, o recibido durante la inmunidad, no hace nada.
]]
function Reglas.AplicarDano(
	estado: Estado,
	stats: Estadisticas,
	dano: number,
	ahora: number,
	ignorarEscudo: boolean?
): ResultadoDano
	if dano ~= dano or dano <= 0 or ahora < estado.InmuneHasta or estado.Vida <= 0 then
		return { Aplicado = false, DanoEscudo = 0, DanoCasco = 0, Destruida = estado.Vida <= 0 }
	end

	local escudo = Reglas.EscudoActual(estado, stats, ahora)
	local alEscudo = if ignorarEscudo then 0 else math.min(escudo, dano)
	local alCasco = dano - alEscudo

	estado.Escudo = escudo - alEscudo
	estado.DesdeEscudo = ahora -- cualquier daño reinicia la espera de la recarga
	estado.Vida = math.max(0, estado.Vida - alCasco)

	return { Aplicado = true, DanoEscudo = alEscudo, DanoCasco = alCasco, Destruida = estado.Vida <= 0 }
end

-- ¿Puede aterrizar? No si ha recibido daño hace muy poco (así no se huye de un combate al instante).
function Reglas.PuedeAterrizar(ultimoDano: number?, ahora: number): boolean
	return ultimoDano == nil or ahora - ultimoDano >= Config.SegundosSinDanoParaAterrizar
end

-- ===== Choques =====

--[[
	Daño de chocar contra un asteroide de `tamano` studs de diámetro a `velocidad` studs/s. Los roces lentos no
	hacen nada; los asteroides grandes duelen más; hay un tope para que un solo golpe no sea absurdo.
]]
function Reglas.DanoChoque(velocidad: number, tamano: number): number
	if velocidad ~= velocidad or tamano ~= tamano then
		return 0
	end
	local exceso = velocidad - Config.VelocidadMinimaChoque
	if exceso <= 0 then
		return 0
	end
	local masa = math.clamp(tamano / 12, 0.5, 2)
	return math.min(Config.DanoChoqueMaximo, exceso * Config.DanoPorVelocidad * masa)
end

-- ===== Armas =====

-- Segundos mínimos entre dos disparos con esa cadencia (disparos por segundo).
function Reglas.IntervaloDisparo(cadencia: number): number
	return 1 / math.max(cadencia, 0.01)
end

--[[
	¿Puede disparar ya? `ultimo` es el instante del último disparo (nil = nunca). Se tolera un pequeño adelanto
	(HolguraCadencia) porque los mensajes llegan con jitter: lo que cuenta es el ritmo sostenido.
]]
function Reglas.PuedeDisparar(ultimo: number?, ahora: number, cadencia: number): boolean
	if ultimo == nil then
		return true
	end
	return ahora - ultimo >= Reglas.IntervaloDisparo(cadencia) * Config.HolguraCadencia
end

local function normalizar(x: number, y: number, z: number): (number, number, number)
	local largo = math.sqrt(x * x + y * y + z * z)
	if largo < 1e-9 then
		return 0, 0, 0
	end
	return x / largo, y / largo, z / largo
end

--[[
	Limita la dirección de disparo que pide el cliente a un cono de `maxGrados` alrededor de la proa de la nave
	(las dos son vectores unitarios o se normalizan). Así el cliente puede apuntar con cierta libertad, pero no
	disparar hacia atrás ni hacia donde la nave no mira. Si se sale del cono, se devuelve la dirección más
	cercana DENTRO del cono. Si la dirección pedida no es utilizable, se dispara recto.
]]
function Reglas.LimitarCono(proa: Punto, direccion: Punto, maxGrados: number?): Punto
	local px, py, pz = normalizar(proa.X, proa.Y, proa.Z)
	local dx, dy, dz = normalizar(direccion.X, direccion.Y, direccion.Z)
	if dx == 0 and dy == 0 and dz == 0 then
		return { X = px, Y = py, Z = pz }
	end

	local limite = math.rad(maxGrados or Config.ConoDisparo)
	local coseno = math.clamp(px * dx + py * dy + pz * dz, -1, 1)
	if coseno >= math.cos(limite) then
		return { X = dx, Y = dy, Z = dz }
	end

	-- Fuera del cono: se gira desde la proa, hacia donde apunta la dirección pedida, justo `limite`.
	local ox, oy, oz = dx - px * coseno, dy - py * coseno, dz - pz * coseno
	local nx, ny, nz = normalizar(ox, oy, oz)
	if nx == 0 and ny == 0 and nz == 0 then
		return { X = px, Y = py, Z = pz } -- justo hacia atrás: no hay un lado mejor que otro
	end
	local c, s = math.cos(limite), math.sin(limite)
	return { X = px * c + nx * s, Y = py * c + ny * s, Z = pz * c + nz * s }
end

-- ===== Turbo =====

--[[
	Energía de turbo en `ahora`: baja mientras está activo y se recupera cuando no. No baja de 0 ni sube del máximo.
]]
function Reglas.EnergiaTurbo(turbo: Turbo, stats: Estadisticas, ahora: number): number
	local transcurrido = math.max(0, ahora - turbo.Desde)
	if turbo.Activo then
		return math.max(0, turbo.Energia - Config.TurboConsumo * transcurrido)
	end
	return math.min(stats.EnergiaTurbo, turbo.Energia + Config.TurboRegeneracion * transcurrido)
end

-- ¿Está dando empuje de turbo ahora mismo? Hace falta tenerlo pulsado Y que quede energía.
function Reglas.TurboActivo(turbo: Turbo, stats: Estadisticas, ahora: number): boolean
	return turbo.Activo and Reglas.EnergiaTurbo(turbo, stats, ahora) > 0
end

--[[
	El piloto pulsa o suelta el turbo (MODIFICA `turbo`). Para encenderlo hace falta energía mínima.
	Devuelve si queda activo.
]]
function Reglas.CambiarTurbo(turbo: Turbo, stats: Estadisticas, activar: boolean, ahora: number): boolean
	local energia = Reglas.EnergiaTurbo(turbo, stats, ahora)
	if activar and not turbo.Activo and energia < Config.TurboMinimo then
		return false
	end
	turbo.Energia = energia
	turbo.Desde = ahora
	turbo.Activo = activar
	return activar
end

-- Velocidad máxima permitida a la nave, con o sin turbo.
function Reglas.VelocidadTope(stats: Estadisticas, turboActivo: boolean): number
	return stats.VelocidadMax * (if turboActivo then stats.TurboMult else 1)
end

-- ===== Vigilancia del movimiento =====

--[[
	¿Es creíble que la nave haya recorrido `distancia` studs en `dt` segundos? Se acepta hasta la velocidad máxima
	por la holgura, más un margen fijo (los choques y la latencia dan saltos pequeños). `dt` se limita para que una
	pausa larga no regale un margen enorme.
]]
function Reglas.MovimientoValido(distancia: number, dt: number, velocidadTope: number): boolean
	if distancia ~= distancia or dt ~= dt then
		return false
	end
	local tiempo = math.clamp(dt, 0, Config.DtMaximo)
	return distancia <= velocidadTope * Config.HolguraVelocidad * tiempo + Config.MargenPosicion
end

-- ¿Sigue dentro del mundo jugable? Se mide la distancia al origen del mundo.
function Reglas.DentroDelMundo(posicion: Punto): boolean
	local distancia = math.sqrt(posicion.X * posicion.X + posicion.Y * posicion.Y + posicion.Z * posicion.Z)
	return distancia <= Config.RadioMundo
end

return Reglas
