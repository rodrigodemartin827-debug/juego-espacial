--!strict
--[[
	Espacio (Planetas): dónde está cada cosa y en qué zona está un punto, como FUNCIONES PURAS.

	Lo usan el servidor (para decidir aterrizajes, despegues, zonas seguras y si una nave se ha salido de
	donde puede estar) y el cliente (para saber qué luz y qué cielo poner). Las dos partes llegan así a la
	misma conclusión con las mismas cuentas, y las pruebas las comprueban fuera de Studio.

	ZONAS
	  "Superficie"  dentro del cuadrado de terreno de un planeta (con su margen y hasta su techo)
	  "Espacio"     a menos de Datos.Espacio.Radio del origen (y fuera de las superficies)
	  "Fuera"       más lejos: el servidor devuelve la nave a su sitio

	Una nave solo cambia entre Espacio y Superficie con la transición del servidor (aterrizar entrando en la
	atmósfera, o subir por encima del techo de la superficie). Si una nave aparece en otra zona por su cuenta,
	es que ha hecho trampa o algo ha ido mal, y el servidor la devuelve.

	LA SUPERFICIE Y EL CIELO
	Cada superficie es un trozo plano de terreno, pero representa el punto del planeta que indica
	`NormalAterrizaje`. Para saber en qué dirección del cielo se ve algo desde allí (el sol, el agujero negro, el
	otro planeta), se toma su dirección real en el espacio desde ese punto y se gira para que la normal del planeta
	sea el "arriba" (+Y) del terreno (ver DireccionEnCielo).
]]

local Datos = require(script.Parent.Datos)
local V = require(script.Parent.Vectores)

type Vec = V.Vec

export type Zona = {
	Tipo: string, -- "Espacio" | "Superficie" | "Fuera"
	Planeta: string?, -- en una superficie: de qué planeta
}

local Espacio = {}

-- Margen por debajo del suelo de una superficie que aún cuenta como superficie (cuevas, grietas).
local MARGEN_BAJO_SUELO = 400

-- ===== Planetas =====

-- Datos de un planeta por su id ("Humanos" | "Monstruos"), o nil.
function Espacio.Planeta(id: string): Datos.Planeta?
	return Datos.Planetas[id]
end

-- Planeta del bando de un jugador (acepta los nombres antiguos "Heroes"/"Villanos"), o nil si no tiene.
function Espacio.PlanetaDeBando(bando: any): string?
	if type(bando) ~= "string" then
		return nil
	end
	return Datos.AliasBandos[bando]
end

-- ===== Zonas =====

-- ¿En la superficie de qué planeta está este punto? (nil = en ninguna)
function Espacio.SuperficieDe(posicion: Vec): string?
	for _, id in Datos.OrdenPlanetas do
		local superficie = Datos.Planetas[id].Superficie
		local centro = superficie.Centro
		local mitad = superficie.Tamano / 2 + superficie.Margen
		if
			math.abs(posicion.X - centro.X) <= mitad
			and math.abs(posicion.Z - centro.Z) <= mitad
			and posicion.Y >= centro.Y - MARGEN_BAJO_SUELO
			and posicion.Y <= centro.Y + superficie.Techo + superficie.Margen
		then
			return id
		end
	end
	return nil
end

-- Zona del punto (ver la cabecera).
function Espacio.ZonaDe(posicion: Vec): Zona
	local planeta = Espacio.SuperficieDe(posicion)
	if planeta then
		return { Tipo = "Superficie", Planeta = planeta }
	end
	if V.largo(posicion) <= Datos.Espacio.Radio then
		return { Tipo = "Espacio", Planeta = nil }
	end
	return { Tipo = "Fuera", Planeta = nil }
end

-- ¿Son la misma zona?
function Espacio.MismaZona(a: Zona, b: Zona): boolean
	return a.Tipo == b.Tipo and a.Planeta == b.Planeta
end

-- Altura de un punto sobre el centro (nivel 0) de la superficie de un planeta.
function Espacio.AlturaEnSuperficie(id: string, posicion: Vec): number
	return posicion.Y - Datos.Planetas[id].Superficie.Centro.Y
end

-- ¿Ha subido lo bastante para volver al espacio?
function Espacio.SuperaTecho(id: string, posicion: Vec): boolean
	return Espacio.AlturaEnSuperficie(id, posicion) >= Datos.Planetas[id].Superficie.Techo
end

-- ===== Atmósfera, cuerpos sólidos y órbita =====

-- ¿Ha entrado en la atmósfera de algún planeta? Devuelve su id y la distancia al centro.
function Espacio.EnAtmosfera(posicion: Vec): (string?, number)
	for _, id in Datos.OrdenPlanetas do
		local planeta = Datos.Planetas[id]
		local distancia = V.distancia(posicion, planeta.Centro)
		if distancia <= planeta.Radio + planeta.Atmosfera then
			return id, distancia
		end
	end
	return nil, math.huge
end

--[[
	¿Está dentro de un cuerpo sólido (un planeta o el sol), contando `margen` studs de más? Devuelve el nombre
	("Humanos", "Monstruos" o "Sol"), su centro y su radio. El agujero negro no cuenta: se cae dentro.
]]
function Espacio.CuerpoSolido(posicion: Vec, margen: number?): (string?, Vec?, number)
	local extra = margen or 0
	for _, id in Datos.OrdenPlanetas do
		local planeta = Datos.Planetas[id]
		if V.distancia(posicion, planeta.Centro) < planeta.Radio + extra then
			return id, planeta.Centro, planeta.Radio
		end
	end
	if V.distancia(posicion, Datos.Sol.Centro) < Datos.Sol.Radio + extra then
		return "Sol", Datos.Sol.Centro, Datos.Sol.Radio
	end
	return nil, nil, 0
end

-- Lista de cuerpos sólidos (centro y radio) para la física del cliente.
function Espacio.CuerposSolidos(): { { Centro: Vec, Radio: number } }
	local lista = {}
	for _, id in Datos.OrdenPlanetas do
		local planeta = Datos.Planetas[id]
		table.insert(lista, { Centro = planeta.Centro, Radio = planeta.Radio })
	end
	table.insert(lista, { Centro = Datos.Sol.Centro, Radio = Datos.Sol.Radio })
	return lista
end

-- Al despegar de la superficie: dónde aparece la nave en el espacio y hacia dónde mira (hacia fuera del planeta).
function Espacio.PuntoOrbita(id: string): (Vec, Vec)
	local planeta = Datos.Planetas[id]
	local normal = V.unitario(planeta.NormalAterrizaje)
	local distancia = planeta.Radio + planeta.Atmosfera + Datos.Transicion.MargenOrbita
	return V.sumar(planeta.Centro, V.escalar(normal, distancia)), normal
end

-- Posición del puerto de un planeta en el mundo (a la altura de su suelo).
function Espacio.PosicionPuerto(id: string): Vec
	local planeta = Datos.Planetas[id]
	return V.sumar(planeta.Superficie.Centro, planeta.Puerto.Posicion)
end

-- Al aterrizar: dónde aparece la nave sobre la superficie y hacia dónde mira (hacia el puerto, en horizontal).
function Espacio.PuntoLlegada(id: string): (Vec, Vec)
	local puerto = Espacio.PosicionPuerto(id)
	local transicion = Datos.Transicion
	local punto = V.sumar(puerto, { X = 0, Y = transicion.AlturaLlegada, Z = transicion.DistanciaLlegada })
	return punto, { X = 0, Y = 0, Z = -1 }
end

-- Donde aparece un jugador a pie en el puerto de su planeta, y donde se baja de la nave al aterrizar con F.
function Espacio.PuntoAparicion(id: string): Vec
	return V.sumar(Espacio.PosicionPuerto(id), Datos.Planetas[id].Puerto.Aparicion)
end

function Espacio.PuntoBajada(id: string): Vec
	return V.sumar(Espacio.PosicionPuerto(id), Datos.Planetas[id].Puerto.Llegada)
end

-- ===== Zonas seguras =====

-- ¿Está en la zona segura de un puerto (cilindro vertical)? Devuelve el id del planeta.
function Espacio.EnZonaSeguraSuperficie(posicion: Vec): string?
	for _, id in Datos.OrdenPlanetas do
		local puerto = Datos.Planetas[id].Puerto
		local centro = Espacio.PosicionPuerto(id)
		local dx, dz = posicion.X - centro.X, posicion.Z - centro.Z
		local dy = posicion.Y - centro.Y
		if dx * dx + dz * dz <= puerto.RadioZonaSegura * puerto.RadioZonaSegura and dy >= -60 then
			if dy <= puerto.AltoZonaSegura then
				return id
			end
		end
	end
	return nil
end

-- ¿Está en la zona segura del espacio que rodea un planeta de bando? Devuelve el id del planeta.
function Espacio.EnZonaSeguraEspacio(posicion: Vec): string?
	for _, id in Datos.OrdenPlanetas do
		local planeta = Datos.Planetas[id]
		if V.distancia(posicion, planeta.Centro) <= planeta.RadioZonaSeguraEspacio then
			return id
		end
	end
	return nil
end

-- ¿Está en cualquier zona segura (sin PvP)?
function Espacio.EnZonaSegura(posicion: Vec): boolean
	return Espacio.EnZonaSeguraSuperficie(posicion) ~= nil or Espacio.EnZonaSeguraEspacio(posicion) ~= nil
end

--[[
	Las zonas seguras de los puertos en el formato de Combate/Reglas.EnZonaSegura (cilindros).
	Se calcula una vez: los datos no cambian durante la partida.
]]
local zonasCombate: { { Centro: Vec, Radio: number, AltoMin: number, AltoMax: number } }? = nil
function Espacio.ZonasSegurasCombate(): { { Centro: Vec, Radio: number, AltoMin: number, AltoMax: number } }
	if zonasCombate == nil then
		local lista = {}
		for _, id in Datos.OrdenPlanetas do
			local puerto = Datos.Planetas[id].Puerto
			local centro = Espacio.PosicionPuerto(id)
			table.insert(lista, {
				Centro = centro,
				Radio = puerto.RadioZonaSegura,
				AltoMin = centro.Y - 60,
				AltoMax = centro.Y + puerto.AltoZonaSegura,
			})
		end
		zonasCombate = lista
	end
	return zonasCombate :: any
end

-- ===== Viaje =====

-- Distancia entre las atmósferas de los dos planetas de bando (lo que hay que volar de uno a otro).
function Espacio.DistanciaEntrePlanetas(): number
	local humanos, monstruos = Datos.Planetas.Humanos, Datos.Planetas.Monstruos
	return V.distancia(humanos.Centro, monstruos.Centro)
		- (humanos.Radio + humanos.Atmosfera)
		- (monstruos.Radio + monstruos.Atmosfera)
end

-- Segundos de viaje entre los dos planetas a `velocidad` studs/s.
function Espacio.TiempoViaje(velocidad: number): number
	return Espacio.DistanciaEntrePlanetas() / math.max(velocidad, 1e-6)
end

-- ===== Cielo de la superficie =====

--[[
	Base del cielo de un planeta: los ejes del ESPACIO que corresponden a +X (este), +Y (arriba) y +Z (sur) del
	terreno. "Arriba" es la normal del punto de aterrizaje; los otros dos son perpendiculares, de modo que el
	giro conserva las distancias y los ángulos (es una rotación).
]]
function Espacio.BaseCielo(id: string): (Vec, Vec, Vec)
	local arriba = V.unitario(Datos.Planetas[id].NormalAterrizaje)
	-- El este es el eje X del espacio proyectado sobre el plano del suelo (o el Z, si la normal es casi X).
	-- Con la normal (0, 1, 0) la base es la identidad: el terreno y el espacio coinciden.
	local referencia: Vec = if math.abs(arriba.X) < 0.95 then { X = 1, Y = 0, Z = 0 } else { X = 0, Y = 0, Z = 1 }
	local este = V.unitario(V.restar(referencia, V.escalar(arriba, V.punto(referencia, arriba))))
	-- este × arriba = sur, igual que X × Y = Z: la base gira sin reflejar.
	local sur = V.cruz(este, arriba)
	return este, arriba, sur
end

-- Lleva una dirección del espacio al cielo del terreno de un planeta (devuelve un vector unitario del mundo).
function Espacio.EspacioACielo(id: string, direccion: Vec): Vec
	local este, arriba, sur = Espacio.BaseCielo(id)
	local d = V.unitario(direccion)
	return { X = V.punto(d, este), Y = V.punto(d, arriba), Z = V.punto(d, sur) }
end

-- Lo contrario: una dirección del cielo del terreno, al espacio.
function Espacio.CieloAEspacio(id: string, direccion: Vec): Vec
	local este, arriba, sur = Espacio.BaseCielo(id)
	return V.unitario(
		V.sumar(V.sumar(V.escalar(este, direccion.X), V.escalar(arriba, direccion.Y)), V.escalar(sur, direccion.Z))
	)
end

-- Punto del planeta (en el espacio) que representa el terreno: centro + normal * radio.
function Espacio.PuntoDeAterrizaje(id: string): Vec
	local planeta = Datos.Planetas[id]
	return V.sumar(planeta.Centro, V.escalar(V.unitario(planeta.NormalAterrizaje), planeta.Radio))
end

-- Dirección en el cielo del terreno de `id` en la que se ve el punto `objetivo` del espacio.
function Espacio.DireccionEnCielo(id: string, objetivo: Vec): Vec
	return Espacio.EspacioACielo(id, V.restar(objetivo, Espacio.PuntoDeAterrizaje(id)))
end

-- Elevación en grados de una dirección sobre el horizonte (Y arriba).
function Espacio.Elevacion(direccion: Vec): number
	local d = V.unitario(direccion)
	return math.deg(math.asin(math.clamp(d.Y, -1, 1)))
end

-- La misma dirección (mismo rumbo), subida hasta `minimo` grados si estaba por debajo.
function Espacio.SobreHorizonte(direccion: Vec, minimo: number): Vec
	local d = V.unitario(direccion)
	if Espacio.Elevacion(d) >= minimo then
		return d
	end
	local horizontal = V.unitario({ X = d.X, Y = 0, Z = d.Z }, { X = 0, Y = 0, Z = -1 })
	local angulo = math.rad(minimo)
	return {
		X = horizontal.X * math.cos(angulo),
		Y = math.sin(angulo),
		Z = horizontal.Z * math.cos(angulo),
	}
end

-- La fuente de luz de cada planeta (su "sol"): "Sol" o "AgujeroNegro", y su centro.
function Espacio.FuenteDeLuz(id: string): (string, Vec)
	if id == "Monstruos" then
		return "AgujeroNegro", Datos.AgujeroNegro.Centro
	end
	return "Sol", Datos.Sol.Centro
end

-- El otro planeta de bando.
function Espacio.OtroPlaneta(id: string): string
	return if id == "Humanos" then "Monstruos" else "Humanos"
end

return Espacio
