--!strict
--[[
	Iluminacion (Planetas/Datos): cómo se ilumina cada zona. Solo datos.

	Lighting en Roblox es GLOBAL (una sola luz direccional, un solo cielo), así que el CLIENTE de cada jugador lo
	ajusta según dónde está él (client/Planetas/Ambiente), mezclando estos "presets" con una transición suave:

	  En el espacio se mezclan EspacioProfundo, EspacioHumanos y EspacioMonstruos según la distancia al sol y al
	  agujero negro (Mezcla), y la luz direccional apunta hacia ellos: el lado de cada planeta que mira a su fuente
	  queda iluminado y el otro en sombra (con poca luz ambiente para que la sombra se note).
	  En cada superficie se usa su preset, con la luz llegando desde la dirección real de su sol en el cielo.

	Campos de un preset (los colores, en "#RRGGBB"):
	  Fuente               "Sol" (cielo de día) o "Luna" (cielo de noche con estrellas). En Roblox la luz
	                       direccional sale del sol de día y de la luna de noche: en el espacio se usa la luna para
	                       que el cielo siga negro y estrellado aunque la luz venga de un lado.
	  Brillo, Ambiente, AmbienteExterior, Exposicion, TonoLuz (ColorShift_Top), Difusa y Especular (los
	  EnvironmentDiffuse/SpecularScale de Lighting)
	  Atmosfera            Density, Offset, Color, Decay, Glare y Haze del objeto Atmosphere (Densidad 0 = sin atmósfera)
	  Cielo                Estrellas (StarCount) y Astros (si se ven el sol y la luna del cielo de Roblox)
	  Color                Tinte, Saturacion, Contraste y Brillo de una corrección de color propia
]]

local Iluminacion = {}

Iluminacion.Presets = {
	-- Entre los dos sistemas (la estación de pruebas): los valores de siempre de Juego/Ambiente.
	EspacioProfundo = {
		Fuente = "Luna",
		Brillo = 2,
		Ambiente = "#262A44",
		AmbienteExterior = "#2E3456",
		Exposicion = 0.25,
		TonoLuz = "#C8D2FF",
		Difusa = 0.6,
		Especular = 0.8,
		Atmosfera = { Densidad = 0, Desfase = 0, Color = "#000000", Decaimiento = "#000000", Brillo = 0, Bruma = 0 },
		Cielo = { Estrellas = 3000, Astros = false },
		Color = { Tinte = "#FFFFFF", Saturacion = 0, Contraste = 0, Brillo = 0 },
	},
	-- Cerca del sol: luz cálida e intensa y sombras profundas.
	EspacioHumanos = {
		Fuente = "Luna",
		Brillo = 4.5,
		Ambiente = "#0E1018",
		AmbienteExterior = "#14182A",
		Exposicion = 0.35,
		TonoLuz = "#FFE9C8",
		Difusa = 0.35,
		Especular = 0.9,
		Atmosfera = { Densidad = 0, Desfase = 0, Color = "#000000", Decaimiento = "#000000", Brillo = 0, Bruma = 0 },
		Cielo = { Estrellas = 2200, Astros = false },
		Color = { Tinte = "#FFF6EC", Saturacion = 0.05, Contraste = 0.05, Brillo = 0 },
	},
	-- Cerca del agujero negro: luz tenue, morada y anaranjada (la del disco), casi sin luz ambiente.
	EspacioMonstruos = {
		Fuente = "Luna",
		Brillo = 1.6,
		Ambiente = "#0C0612",
		AmbienteExterior = "#130A1C",
		Exposicion = 0.1,
		TonoLuz = "#E0A0FF",
		Difusa = 0.25,
		Especular = 0.6,
		Atmosfera = { Densidad = 0, Desfase = 0, Color = "#000000", Decaimiento = "#000000", Brillo = 0, Bruma = 0 },
		Cielo = { Estrellas = 4000, Astros = false },
		Color = { Tinte = "#F2E6FF", Saturacion = -0.1, Contraste = 0.12, Brillo = -0.02 },
	},
	-- Superficie humana: día luminoso con cielo azul y algo de bruma en el horizonte.
	SuperficieHumanos = {
		Fuente = "Sol",
		Brillo = 3,
		Ambiente = "#5A6070",
		AmbienteExterior = "#8C92A2",
		Exposicion = 0,
		TonoLuz = "#FFF4E0",
		Difusa = 1,
		Especular = 1,
		Atmosfera = {
			Densidad = 0.32,
			Desfase = 0.12,
			Color = "#C7DCFF",
			Decaimiento = "#6A7590",
			Brillo = 0.35,
			Bruma = 1.1,
		},
		Cielo = { Estrellas = 0, Astros = true },
		Color = { Tinte = "#FFFFFF", Saturacion = 0.12, Contraste = 0.06, Brillo = 0 },
	},
	-- Superficie de los monstruos: noche perpetua, niebla morada espesa y poca luz.
	SuperficieMonstruos = {
		Fuente = "Luna",
		Brillo = 1.4,
		Ambiente = "#1E1228",
		AmbienteExterior = "#281636",
		Exposicion = 0.15,
		TonoLuz = "#D6A0FF",
		Difusa = 0.5,
		Especular = 0.6,
		Atmosfera = {
			Densidad = 0.46,
			Desfase = 0.25,
			Color = "#3C1E50",
			Decaimiento = "#14081E",
			Brillo = 0,
			Bruma = 2.6,
		},
		Cielo = { Estrellas = 1500, Astros = false },
		Color = { Tinte = "#E8D8FF", Saturacion = -0.25, Contraste = 0.2, Brillo = -0.03 },
	},
}

--[[
	Mezcla en el espacio: a menos de RadioPleno de la fuente se usa su preset entero; a partir de RadioNulo, nada.
	Entre medias se mezcla con una curva suave (y lo que falta hasta 1 es EspacioProfundo).
]]
Iluminacion.Mezcla = {
	Sol = { Preset = "EspacioHumanos", RadioPleno = 16000, RadioNulo = 38000 },
	AgujeroNegro = { Preset = "EspacioMonstruos", RadioPleno = 16000, RadioNulo = 38000 },
	Profundo = "EspacioProfundo",
}

Iluminacion.Ajustes = {
	ElevacionMinima = 4, -- grados: la luz de Roblox no puede venir de debajo del horizonte (ver client/Planetas/Ambiente)
	Rapidez = 1.6, -- por segundo: lo deprisa que se pasa de un preset a otro (transición suave)
	HzOrientacion = 6, -- veces por segundo que se recalcula hacia dónde apunta la luz
	UmbralGrados = 0.35, -- si la dirección cambia menos que esto, no se recalcula
	-- Tabla de calibración de la dirección de la luz (horas × latitudes que se prueban al arrancar).
	PasoHora = 0.25,
	PasoLatitud = 3,
	Refinados = 9, -- pasos de búsqueda fina alrededor del mejor punto de la tabla
}

return Iluminacion
