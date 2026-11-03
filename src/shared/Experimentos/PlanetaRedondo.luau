--!strict
--[[
	EXPERIMENTO (rama experimento/planeta-redondo, NO para fusionar): planetas redondos de verdad.

	Nueva Tierra deja de ser una esfera decorativa con transición a un terreno plano: es una ESFERA DE TERRAIN en su
	sitio real del espacio, con gravedad hacia su centro. El personaje anda, corre y salta sobre ella (y le da la
	vuelta entera) con un controlador propio, la cámara se orienta con la superficie, y la nave aterriza y despega
	directamente sobre la esfera, sin fundidos.

	Piezas:
	  shared/Experimentos/PlanetaRedondo   (este módulo) datos del experimento y ajuste de Planetas/Datos
	  server/Experimentos/PlanetaRedondo   genera la esfera de Terrain, el puerto y los aterrizajes
	  client/Experimentos/GravedadPlaneta  controlador del personaje y cámara sobre la esfera
	  client/Naves/Vuelo y Naves/Camara    la nave usa como "arriba" el del planeta cuando está cerca

	Solo se activa en Studio (Activado): en un servidor de verdad el juego sigue exactamente igual.
	Para probar otro radio, cambia `Radio` y vuelve a darle a Play.
]]

local RunService = game:GetService("RunService")

local PlanetaRedondo = {}

-- Interruptor general del experimento (además, solo en Studio).
PlanetaRedondo.Activo = true

-- Qué planeta de Planetas/Datos se vuelve redondo, y con qué radio (studs). Probados: 2400, 5000 y 10000.
PlanetaRedondo.Planeta = "Humanos"
PlanetaRedondo.Radio = 2400

-- ===== Terreno (lo genera el servidor al arrancar) =====
PlanetaRedondo.Terreno = {
	-- La corteza: losas de FillBlock tangentes a la esfera (FillBall no admite radios de más de ~1000 studs).
	SeparacionLosas = 96, -- studs entre los centros de dos losas vecinas
	AnchoLosa = 150, -- lado de cada losa (más que la separación: se solapan y no quedan rendijas)
	Grosor = 40, -- grosor de la corteza (el interior es hueco: nadie lo ve y ahorra memoria)
	-- Colinas: bolas de terreno medio enterradas (cúpulas suaves). Cantidad por cada millón de studs² de superficie.
	ColinasPorMillon = 14,
	RadioColina = { 60, 420 },
	Enterrado = 0.84, -- fracción del radio de la bola que queda bajo el suelo (más = más suave)
	-- Grosor de las colinas huecas (0 = macizas). Probado: vaciarlas NO ahorra memoria (Roblox reserva el terreno por
	-- bloques, y la corteza ya los toca todos) y dobla el tiempo de generación, así que van macizas.
	GrosorColina = 0,
	RocasPorMillon = 30,
	RadioRoca = { 6, 22 },
	-- Piedras pequeñas (1-3 studs de alto) alrededor del puerto, para probar que se pasan por encima sin saltar.
	PiedrasPuerto = 260,
	RadioPiedra = { 1.5, 2.6 },
	ZonaPiedras = { 30, 380 }, -- studs desde el puerto (fuera de la explanada)
	-- Manchas de otros materiales (losas finas encima de la hierba), según un ruido 3D.
	EscalaRuido = 0.0016, -- por stud
	Semilla = 7,
	SegundosPorTanda = 0.03, -- se cede el hilo tras tanto tiempo de trabajo seguido (no congelar el servidor)
	-- Nombres de Enum.Material.
	Materiales = {
		Base = "Grass",
		Alta = "LeafyGrass",
		Tierra = "Ground",
		Arena = "Sand",
		Roca = "Rock",
		Nieve = "Snow",
	},
	LatitudNieve = 66, -- grados: casquetes polares
}

-- ===== Personaje =====
PlanetaRedondo.Personaje = {
	-- La gravedad actúa hasta esta altura sobre la superficie; más arriba, el personaje vuelve a la normal.
	Alcance = 1500,
	Gravedad = 196.2, -- studs/s², como la de Roblox
	Andar = 16,
	Correr = 28, -- con Mayús izquierda
	Salto = 50, -- velocidad vertical al saltar
	Aceleracion = 120, -- studs/s² al arrancar y frenar en el suelo
	AceleracionAire = 35,
	AlturaRaiz = 3, -- R6: el HumanoidRootPart va 3 studs por encima del suelo
	MargenSuelo = 1.6, -- hasta esta distancia extra se considera que pisa suelo (escalones y bajadas)
	RigidezSuelo = 18, -- cómo de deprisa recupera la altura correcta sobre el suelo
	Giro = 12, -- cómo de deprisa se gira el cuerpo hacia donde anda
	SondaDelante = 1.5, -- studs por delante del cuerpo a los que se mira el suelo...
	SondaPorVelocidad = 0.08, -- ...más estos segundos de avance (más lejos cuanto más rápido)
	AlturaPaso = 3, -- piedras y escalones de hasta esta altura (studs) se suben sin saltar
	-- Paredes (barrido de una esfera delante del cuerpo, que no choca con nada por sí mismo).
	RadioCuerpo = 1.2,
	AlturaBarrido = 0.5, -- centro de la esfera sobre la raíz
	MargenPared = 0.4, -- studs extra por delante
	PendienteMaxima = 0.6, -- coseno: superficies más empinadas que ~53° son pared
	-- Grupo de colisión del personaje mientras está en el planeta: no choca con nada (Roblox vuelve a poner
	-- CanCollide en el torso y las extremidades en cada paso, así que hace falta un grupo).
	GrupoColision = "PersonajePlaneta",
	SubidaMaxima = 22, -- studs/s: lo más deprisa que el muelle sube el cuerpo (más daría saltitos en los escalones)
	-- Por debajo de esta altura sobre el radio, si no hay terreno debajo (aún no ha llegado al cliente), el personaje
	-- espera quieto en vez de caer a través del planeta.
	AlturaEsperaTerreno = 300,
}

-- ===== Cámara =====
PlanetaRedondo.Camara = {
	Distancia = 14,
	DistanciaMin = 5,
	DistanciaMax = 60,
	Altura = 1.5, -- foco por encima de la raíz
	CabeceoInicial = 0.3, -- radianes (positivo = mira hacia abajo)
	CabeceoMin = -1.2,
	CabeceoMax = 1.35,
	Sensibilidad = 0.006, -- radianes por píxel
	Suavidad = 14,
}

-- ===== Nave =====
PlanetaRedondo.Nave = {
	-- La nave usa el "arriba" del planeta a menos de esta altura de la superficie (fuera, el del mundo).
	AlcanceReferencia = 2500,
	VelocidadGiroReferencia = 1.4, -- radianes por segundo que se reorienta el horizonte de la nave
	AlturaAterrizaje = 120, -- se puede aterrizar (F) con la nave a menos de esta altura del suelo
}

-- ¿Está activo el experimento en esta partida?
function PlanetaRedondo.Activado(): boolean
	return PlanetaRedondo.Activo and RunService:IsStudio()
end

--[[
	Ajusta Planetas/Datos para el experimento. Debe llamarse ANTES de que nadie más lea Planetas/Datos (lo primero de
	init.server y de init.client), porque algunos módulos copian los radios al cargarse.
	  - el planeta pasa a tener el radio del experimento,
	  - sin atmósfera de aterrizaje (no hay transición: se aterriza sobre la esfera),
	  - su zona segura del espacio crece con el radio.
]]
function PlanetaRedondo.Aplicar()
	if not PlanetaRedondo.Activado() then
		return
	end
	local Datos = require(script.Parent.Parent.Planetas.Datos) :: any
	local planeta = Datos.Planetas[PlanetaRedondo.Planeta]
	local escala = PlanetaRedondo.Radio / planeta.Radio
	planeta.Radio = PlanetaRedondo.Radio
	planeta.Atmosfera = -1
	planeta.RadioZonaSeguraEspacio *= escala
	-- Nadie aparece en las superficies planas (en el experimento no se generan): se aparece en el planeta redondo.
	Datos.AparecerEnPlanetaDelBando = false
end

-- Centro y radio del planeta redondo (después de Aplicar).
function PlanetaRedondo.Centro(): Vector3
	local Datos = require(script.Parent.Parent.Planetas.Datos) :: any
	local c = Datos.Planetas[PlanetaRedondo.Planeta].Centro
	return Vector3.new(c.X, c.Y, c.Z)
end

-- "Arriba" del planeta en una posición (hacia fuera desde el centro).
function PlanetaRedondo.Arriba(posicion: Vector3): Vector3
	local d = posicion - PlanetaRedondo.Centro()
	return if d.Magnitude > 1e-3 then d.Unit else Vector3.yAxis
end

--[[
	Marco con "arriba" = `arriba` y el frente lo más parecido posible a `frente` (proyectado sobre el plano tangente).
	Si `frente` es casi paralelo a `arriba`, se usa otro eje de apoyo.
]]
function PlanetaRedondo.Marco(posicion: Vector3, arriba: Vector3, frente: Vector3): CFrame
	local f = frente - arriba * frente:Dot(arriba)
	if f.Magnitude < 1e-3 then
		local apoyo = if math.abs(arriba.X) < 0.9 then Vector3.xAxis else Vector3.zAxis
		f = apoyo - arriba * apoyo:Dot(arriba)
	end
	f = f.Unit
	local derecha = f:Cross(arriba)
	return CFrame.fromMatrix(posicion, derecha, arriba, -f)
end

--[[
	Gira `marco` (solo su orientación) lo mínimo para que su eje Y pase de `desde` a `hacia`, como mucho `maximo`
	radianes. Es el "transporte paralelo": el rumbo se conserva al desplazarse sobre la esfera.
]]
function PlanetaRedondo.GirarArriba(marco: CFrame, desde: Vector3, hacia: Vector3, maximo: number?): CFrame
	local eje = desde:Cross(hacia)
	local seno = eje.Magnitude
	local coseno = math.clamp(desde:Dot(hacia), -1, 1)
	if seno < 1e-6 then
		return marco
	end
	local angulo = math.atan2(seno, coseno)
	if maximo then
		angulo = math.min(angulo, maximo)
	end
	local posicion = marco.Position
	return CFrame.new(posicion) * CFrame.fromAxisAngle(eje / seno, angulo) * (marco - posicion)
end

return PlanetaRedondo
