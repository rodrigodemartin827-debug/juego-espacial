--!strict
--[[
	Datos (Planetas): dónde está cada cosa del sistema solar y cómo es.

	Aquí solo hay datos (números, textos y colores en hexadecimal "#RRGGBB"); las cuentas están en
	Planetas/Espacio, Planetas/Gravedad, Planetas/Calor y Planetas/Luz, y lo que se ve, en client/Planetas.
	Para equilibrar o retocar el sistema basta con tocar los números de este módulo.

	Contenido:
	  Espacio      tamaño del espacio jugable y cómo se dibujan los cuerpos lejanos
	  Transicion   tiempos y alturas del aterrizaje y el despegue (fundido a negro)
	  Planetas     los dos planetas de bando: Humanos y Monstruos (posición, tamaño, aspecto desde el
	               espacio, zona de superficie con su terreno, puerto y zona segura)
	  Sol          el sol de la zona humana (luz, aspecto y recalentamiento de las naves)
	  AgujeroNegro el "sol" de los monstruos (luz, aspecto y atracción de las naves)
	  AliasBandos  qué planeta corresponde a cada bando guardado

	EL MAPA (vista desde arriba; los planetas están en el plano Y = 0, el sol y el agujero negro algo por encima):

	      Sol                                                                   Agujero negro
	        \                                                                   /
	   [Planeta Humanos] ---------- ~10 min de crucero ---------- [Planeta Monstruos]
	      x = -35 000                 (0, 0, 0): estación                     x = 35 000
	                                 de pruebas y campo de asteroides

	Las SUPERFICIES (los terrenos donde se aterriza) están en el mismo lugar, lejos de todo lo anterior: a
	30 000 studs de altura. Ningún objeto del espacio está cerca, así que con StreamingEnabled no se cargan
	a la vez, y el servidor no deja entrar ni salir de ellas volando: solo con la transición (ver Espacio.ZonaDe).

	Coma flotante: Roblox guarda las posiciones en coma flotante de 32 bits. Todo lo jugable queda a menos de
	48 000 studs del origen, donde la precisión es de unos 4 milésimos de stud: de sobra para la física y la
	imagen (los problemas visibles empiezan mucho más lejos). Por eso no hace falta escalar velocidades: el
	viaje de ~10 minutos sale con las distancias reales (ver la prueba "el viaje entre planetas dura unos 10 min").
]]

local NavesConfig = require(script.Parent.Parent.Naves.Config)

export type Vec = { X: number, Y: number, Z: number }

-- Capa del aspecto de un planeta visto desde el espacio (la construye client/Planetas/Construccion).
export type CapaPlaneta = {
	Tipo: string, -- "Esfera" (una esfera concéntrica) | "Manchas" (continentes, hielo, grietas...) | "Nubes" | "Halo"
	Color: string,
	Escala: number?, -- radio de la capa respecto al del planeta (Esfera y Halo)
	Transparencia: number?,
	Material: string?, -- nombre de Enum.Material (por defecto SmoothPlastic)
	Neon: boolean?, -- brilla por sí misma (no le afecta la luz)
	Cantidad: number?, -- Manchas/Nubes: cuántos grupos
	Piezas: { number }?, -- Manchas/Nubes: piezas por grupo (mínimo y máximo)
	Tamano: { number }?, -- Manchas/Nubes: tamaño de cada pieza respecto al radio (mínimo y máximo)
	Relieve: number?, -- Manchas: cuánto asoma cada pieza sobre la esfera (fracción del radio)
	Aplanado: number?, -- Nubes/Manchas: grosor respecto al ancho (1 = esfera, 0.1 = lámina)
	Latitud: { number }?, -- Manchas: franja de latitudes en grados (por defecto, toda la esfera)
	Polos: boolean?, -- Manchas: repartir la franja de latitud entre los dos polos (casquetes)
	Colores: { string }?, -- Manchas: colores alternativos para dar variedad
	Giro: number?, -- Nubes: radianes por segundo que gira la capa
	Semilla: number?,
}

export type Superficie = {
	Centro: Vec, -- centro del terreno en el mundo (múltiplos de 4: Terrain trabaja en celdas de 4 studs)
	Tamano: number, -- lado del cuadrado de terreno (studs)
	Techo: number, -- altura sobre Centro.Y a partir de la cual una nave vuelve al espacio
	Margen: number, -- studs extra alrededor del cuadrado que aún cuentan como "superficie" (bordes)
	Terreno: { [string]: any }, -- parámetros del generador (Planetas/GeneradorTerreno)
	Iluminacion: string, -- preset de Planetas/Datos/Iluminacion
}

export type Puerto = {
	Posicion: Vec, -- relativa al centro de la superficie (Y = altura del suelo del puerto)
	Plataformas: number, -- naves que pueden despegar a la vez
	Separacion: number, -- studs entre plataformas
	RadioZonaSegura: number, -- zona sin PvP alrededor del puerto (cilindro)
	AltoZonaSegura: number, -- altura del cilindro
	Aparicion: Vec, -- donde aparece un jugador (relativo al puerto)
	Llegada: Vec, -- donde se baja de la nave al aterrizar con F (relativo al puerto)
	ColorNeon: string,
}

export type Planeta = {
	Id: string,
	Nombre: string,
	Centro: Vec,
	Radio: number,
	Atmosfera: number, -- grosor de la atmósfera: entrar en ella = aterrizar
	RadioZonaSeguraEspacio: number, -- sin PvP de naves a menos de esta distancia del centro
	-- Hacia dónde mira el punto de aterrizaje (vector unitario desde el centro): da el "arriba" de la superficie,
	-- y con él la dirección en que se ven el sol, el agujero negro y el otro planeta desde el suelo.
	NormalAterrizaje: Vec,
	Apariencia: { CapaPlaneta },
	Superficie: Superficie,
	Puerto: Puerto,
}

local Datos = {}

-- ===========================================================================================================
-- ESPACIO
-- ===========================================================================================================

Datos.Espacio = {
	-- Radio del espacio jugable alrededor del origen (es el mismo que vigila Naves: Naves/Config.RadioMundo).
	Radio = NavesConfig.RadioMundo,
	-- Hasta esta distancia (al centro) un cuerpo se dibuja en su sitio real. Más lejos se dibuja un "doble" a
	-- esta distancia, en la misma dirección y encogido en proporción: se ve exactamente igual (mismo tamaño
	-- aparente) pero nunca está tan lejos como para que el motor deje de dibujarlo o pierda precisión.
	DistanciaReal = 9000,
	-- Veces por segundo que se recolocan los cuerpos lejanos (los cercanos, cada fotograma).
	HzLejanos = 15,
	-- En la superficie, el otro planeta, el sol y el agujero negro se dibujan a esta distancia del jugador,
	-- en su dirección real (ver Espacio.DireccionEnCielo), y nunca por debajo de esta elevación (grados).
	DistanciaCielo = 1400,
	ElevacionMinimaCielo = 12,
}

-- ===========================================================================================================
-- TRANSICIÓN (aterrizar y despegar)
-- ===========================================================================================================

Datos.Transicion = {
	FundidoSalida = 0.7, -- segundos hasta negro
	NegroMinimo = 0.6, -- segundos en negro como mínimo (mientras el servidor coloca la nave y carga el terreno)
	FundidoEntrada = 1.1, -- segundos de negro a imagen
	AlturaLlegada = 160, -- la nave aparece a esta altura sobre el puerto de la superficie
	DistanciaLlegada = 260, -- ... y a esta distancia horizontal del puerto, mirando hacia él
	MargenOrbita = 500, -- al despegar, la nave aparece a esta distancia por fuera de la atmósfera
	SegundosEntreAvisos = 2.5, -- "no puedes aterrizar en pleno combate" no se repite más a menudo
}

-- ===========================================================================================================
-- PLANETAS DE BANDO
-- ===========================================================================================================

Datos.Planetas = {
	-- ===== Humanos: como la Tierra =====
	Humanos = {
		Id = "Humanos",
		Nombre = "Nueva Tierra",
		Centro = { X = -35000, Y = 0, Z = 0 },
		Radio = 2400,
		Atmosfera = 380,
		RadioZonaSeguraEspacio = 3600,
		-- Calculada para que desde el puerto el sol se vea alto (unos 42°) y el planeta de los monstruos, bajo
		-- en el horizonte (unos 14°). La prueba "desde cada puerto se ven el otro planeta y su fuente de luz" lo vigila.
		NormalAterrizaje = { X = 0.2730, Y = 0.5446, Z = 0.7930 },
		Apariencia = {
			-- Océano.
			{ Tipo = "Esfera", Color = "#1E5BB8", Escala = 1, Material = "SmoothPlastic" },
			-- Continentes: grupos de manchas de verdes y ocres que asoman un poco sobre el océano.
			{
				Tipo = "Manchas",
				Color = "#3E8E3A",
				Colores = { "#3E8E3A", "#4FA046", "#2F7432", "#8C8A4A", "#6E9A3C" },
				Cantidad = 11,
				Piezas = { 4, 7 },
				Tamano = { 0.12, 0.3 },
				Relieve = 0.004,
				Aplanado = 1,
				Latitud = { -62, 62 },
				Semilla = 1101,
			},
			-- Casquetes polares.
			{
				Tipo = "Manchas",
				Color = "#F2F7FF",
				Cantidad = 2,
				Piezas = { 3, 4 },
				Tamano = { 0.22, 0.3 },
				Relieve = 0.005,
				Aplanado = 1,
				Latitud = { 74, 90 },
				Polos = true,
				Semilla = 1102,
			},
			-- Nubes: una capa aparte que gira despacio.
			{
				Tipo = "Nubes",
				Color = "#FFFFFF",
				Transparencia = 0.18,
				Cantidad = 16,
				Piezas = { 2, 4 },
				Tamano = { 0.1, 0.24 },
				Escala = 1.022,
				Aplanado = 0.08,
				Giro = 0.006,
				Semilla = 1103,
			},
			-- Atmósfera: dos halos azules que dan el borde luminoso.
			{ Tipo = "Esfera", Color = "#7FB8FF", Escala = 1.035, Transparencia = 0.82 },
			{ Tipo = "Halo", Color = "#8CC4FF", Escala = 1.32, Transparencia = 0.55 },
		},
		Superficie = {
			Centro = { X = -12000, Y = 30000, Z = 0 },
			Tamano = 4096,
			Techo = 900,
			Margen = 200,
			Iluminacion = "SuperficieHumanos",
			Terreno = {
				Estilo = "Humanos",
				Semilla = 4242,
				Resolucion = 4, -- studs por celda (Terrain usa 4)
				Trozo = 64, -- celdas por lado de cada trozo que se genera de una vez
				Grosor = 3, -- celdas de suelo por debajo de la superficie (lo de más abajo nunca se ve)
				-- Relieve: suma de capas de ruido (escala en studs y amplitud en studs).
				Capas = {
					{ Escala = 1100, Amplitud = 95 },
					{ Escala = 380, Amplitud = 42 },
					{ Escala = 120, Amplitud = 12 },
					{ Escala = 36, Amplitud = 2.5 },
				},
				AlturaBase = 30,
				NivelAgua = 22, -- por debajo de esto hay agua (lagos y ríos)
				AnchoPlaya = 4, -- studs por encima del agua que son arena
				PendienteRoca = 0.85, -- a partir de esta pendiente (altura/distancia) asoma la roca
				AlturaNieve = 175, -- por encima, nieve
				-- Montañas en el borde del mapa para que nadie se caiga del mundo.
				BordeAncho = 520,
				BordeAltura = 300,
				-- El puerto se aplana para que las naves se posen.
				PuertoRadioPlano = 190,
				PuertoTransicion = 240,
				PuertoAltura = 44,
				-- Variedad de la hierba.
				EscalaHierba = 140,
				Materiales = {
					Hierba = "Grass",
					HierbaAlta = "LeafyGrass",
					Tierra = "Ground",
					Roca = "Rock",
					Arena = "Sand",
					Agua = "Water",
					Nieve = "Snow",
					Puerto = "Pavement",
				},
			},
		},
		Puerto = {
			Posicion = { X = 0, Y = 44, Z = 0 },
			Plataformas = 3,
			Separacion = 60,
			RadioZonaSegura = 230,
			AltoZonaSegura = 400,
			Aparicion = { X = 0, Y = 2, Z = 70 },
			Llegada = { X = 0, Y = 3.5, Z = 52 },
			ColorNeon = "#4DF0FF",
		},
	},

	-- ===== Monstruos: oscuro y siniestro =====
	Monstruos = {
		Id = "Monstruos",
		Nombre = "Umbra",
		Centro = { X = 35000, Y = 0, Z = 0 },
		Radio = 2400,
		Atmosfera = 380,
		RadioZonaSeguraEspacio = 3600,
		-- Desde el puerto, el agujero negro se ve a unos 36° y el planeta humano, a unos 15°.
		NormalAterrizaje = { X = -0.2882, Y = 0.7314, Z = -0.6181 },
		Apariencia = {
			-- Roca negra.
			{ Tipo = "Esfera", Color = "#16121C", Escala = 1, Material = "Slate" },
			-- Mesetas de ceniza.
			{
				Tipo = "Manchas",
				Color = "#2A2230",
				Colores = { "#2A2230", "#221A26", "#33283A" },
				Cantidad = 9,
				Piezas = { 3, 6 },
				Tamano = { 0.12, 0.28 },
				Relieve = 0.004,
				Aplanado = 1,
				Semilla = 2201,
			},
			-- Grietas que brillan en la oscuridad (se ven también en el lado de sombra).
			{
				Tipo = "Manchas",
				Color = "#B0123A",
				Colores = { "#B0123A", "#7A1FD6", "#D2332A" },
				Cantidad = 10,
				Piezas = { 4, 8 },
				Tamano = { 0.025, 0.05 },
				Relieve = 0.002,
				Aplanado = 1,
				Neon = true,
				Transparencia = 0.15,
				Semilla = 2202,
			},
			-- Bruma morada que gira despacio.
			{
				Tipo = "Nubes",
				Color = "#3A1F4A",
				Transparencia = 0.35,
				Cantidad = 12,
				Piezas = { 2, 4 },
				Tamano = { 0.14, 0.3 },
				Escala = 1.02,
				Aplanado = 0.07,
				Giro = -0.004,
				Semilla = 2203,
			},
			{ Tipo = "Esfera", Color = "#5B1F7A", Escala = 1.035, Transparencia = 0.84 },
			{ Tipo = "Halo", Color = "#8A2BE2", Escala = 1.3, Transparencia = 0.62 },
		},
		Superficie = {
			Centro = { X = 12000, Y = 30000, Z = 0 },
			Tamano = 4096,
			Techo = 900,
			Margen = 200,
			Iluminacion = "SuperficieMonstruos",
			Terreno = {
				Estilo = "Monstruos",
				Semilla = 6666,
				Resolucion = 4,
				Trozo = 64,
				Grosor = 3,
				Capas = {
					{ Escala = 900, Amplitud = 70 },
					{ Escala = 260, Amplitud = 34 },
					{ Escala = 70, Amplitud = 9 },
					{ Escala = 22, Amplitud = 2 },
				},
				AlturaBase = 40,
				-- Grietas: canales estrechos y profundos con roca fundida al fondo.
				Grietas = { Escala = 420, Anchura = 0.07, Profundidad = 46 },
				-- Agujas de roca retorcida.
				Agujas = { Escala = 55, Umbral = 0.62, Altura = 38 },
				PendienteRoca = 0.7,
				BordeAncho = 520,
				BordeAltura = 300,
				PuertoRadioPlano = 190,
				PuertoTransicion = 240,
				PuertoAltura = 50,
				EscalaHierba = 160,
				Materiales = {
					Base = "Basalt",
					Ceniza = "Slate",
					Roca = "Rock",
					Grieta = "CrackedLava",
					Puerto = "Asphalt",
				},
			},
		},
		Puerto = {
			Posicion = { X = 0, Y = 50, Z = 0 },
			Plataformas = 3,
			Separacion = 60,
			RadioZonaSegura = 230,
			AltoZonaSegura = 400,
			Aparicion = { X = 0, Y = 2, Z = 70 },
			Llegada = { X = 0, Y = 3.5, Z = 52 },
			ColorNeon = "#C04BFF",
		},
	},
} :: { [string]: Planeta }

-- Orden fijo en que se recorren (para que todo sea determinista).
Datos.OrdenPlanetas = { "Humanos", "Monstruos" }

-- ===========================================================================================================
-- SOL (zona humana)
-- ===========================================================================================================

Datos.Sol = {
	Centro = { X = -40750, Y = 6900, Z = 10350 },
	Radio = 1500, -- radio de la bola brillante (sólida: una nave no puede atravesarla)
	-- Recalentamiento de las naves (Planetas/Calor). Distancias al centro.
	Calor = {
		RadioAviso = 7800, -- empieza a calentarse
		RadioNucleo = 1900, -- aquí el calor objetivo es el máximo
		CalorMax = 100,
		Exponente = 1.6, -- cuanto más alto, más de golpe sube el calor al acercarse
		Inercia = 0.45, -- rapidez (por segundo) con la que el calor se acerca al de esa distancia
		SubidaMaxima = 16, -- el calor nunca sube más de esto por segundo
		UmbralAviso = 30, -- el panel avisa
		UmbralDano = 60, -- a partir de aquí el casco se daña
		DanoPorSegundo = 34, -- daño por segundo con el calor al máximo (proporcional por encima del umbral)
		IgnoraEscudo = true, -- el escudo no protege del calor
	},
	Apariencia = {
		Nucleo = "#FFF6D8",
		Corona = "#FFC14D",
		CoronaExterior = "#FF7A1F",
		Halo = { "#FFE7A8", "#FFB347", "#FF7A1F" }, -- de dentro a fuera
		EscalaHalo = 4.2, -- diámetro del halo respecto al radio
		Llamaradas = 7, -- arcos de plasma que crecen y se apagan
		ColorLlamarada = "#FF9A2E",
		Luz = "#FFF1D0",
	},
}

-- ===========================================================================================================
-- AGUJERO NEGRO (zona de los monstruos)
-- ===========================================================================================================

Datos.AgujeroNegro = {
	Centro = { X = 40750, Y = 6325, Z = -10350 },
	RadioHorizonte = 230, -- dentro: la nave se destruye
	-- Atracción (Planetas/Gravedad): velocidad de "arrastre" hacia el centro que se suma a la de la nave.
	Atraccion = {
		RadioInfluencia = 9000, -- más lejos no atrae nada
		RadioSinRetorno = 1800, -- aquí arrastra a VelocidadSinRetorno: una nave sin mejorar ya no escapa
		VelocidadSinRetorno = 125,
		VelocidadMaxima = 650,
		Holgura = 1.25, -- margen del servidor al vigilar que no se escape más deprisa de lo posible
	},
	Apariencia = {
		Disco = { "#FFF2D6", "#FFB25A", "#FF5A2A", "#7A1FD6" }, -- de dentro a fuera
		RadiosDisco = { 1.7, 2.6, 3.8, 5.6 }, -- respecto al horizonte
		InclinacionDisco = 14, -- grados
		Grumos = 26, -- trozos de materia que orbitan en el disco (se ve que gira)
		AnilloFotones = "#FFE9C2",
		Lente = "#FF9D5C",
		Particulas = 36, -- partículas absorbidas en espiral (se reduce con la calidad)
		ColorParticulas = { "#FFD7A0", "#C77DFF" },
		RadioParticulas = 7, -- de dónde salen las partículas (respecto al horizonte)
		SegundosParticula = { 5, 9 },
		Luz = "#B98CFF",
	},
}

-- ===========================================================================================================
-- BANDOS
-- ===========================================================================================================

--[[
	Planeta de cada bando guardado. Los nombres "Heroes" y "Villanos" son los actuales del DataStore; otra rama los
	está cambiando a "Humanos" y "Monstruos". Mientras tanto se aceptan los dos: cuando ese cambio se fusione,
	basta con borrar las dos primeras líneas.
]]
Datos.AliasBandos = {
	Heroes = "Humanos",
	Villanos = "Monstruos",
	Humanos = "Humanos",
	Monstruos = "Monstruos",
} :: { [string]: string }

-- Los jugadores con bando aparecen en el puerto de su planeta (false = en la zona de pruebas, como antes).
Datos.AparecerEnPlanetaDelBando = true

return Datos
