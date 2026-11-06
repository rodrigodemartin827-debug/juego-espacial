--!strict
--[[
	Efectos (Planetas/Datos): las RECETAS visuales del entorno espacial.

	Tienen el mismo formato que las del combate y las naves y las reproduce el mismo motor
	(client/VFX/Gestor.Reproducir). Colores: nombres de Combate/Datos/Paleta.

	Qué receta se usa en cada momento (client/Planetas/EfectosEntorno):
	  Planeta_Entrada      la nave entra en la atmósfera de un planeta (justo antes del fundido a negro)
	  Planeta_Salida       la nave sale al espacio desde la superficie (al volver la imagen)
	  Espacio_Calor        latido de recalentamiento junto al sol (se repite mientras hay peligro)
	  Espacio_Atraccion    latido de la atracción del agujero negro (más fuerte cuanto más cerca)
	  Espacio_Absorcion    una nave cae en el agujero negro (en lugar de la explosión normal)

	Anclas: "Lanzador" es el centro de la nave propia; "Objetivo", el punto del suceso.
]]

local Atajos = require(script.Parent.Parent.Parent.Combate.Datos.Atajos)

local capa, esfera, onda, chispas, humo, luz =
	Atajos.capa, Atajos.esfera, Atajos.onda, Atajos.chispas, Atajos.humo, Atajos.luz
local sacudida, tinte = Atajos.sacudida, Atajos.tinte

local SIN_GRAVEDAD = { 0, 0, 0 }

local Recetas = {}

-- Entrada en la atmósfera: la nave se envuelve en plasma, la pantalla se tiñe de naranja y tiembla.
Recetas.Planeta_Entrada = {
	Paleta = "PlanetaAtmosfera",
	Fases = {
		Lanzamiento = {
			esfera("Lanzador", 10, 26, 0.7, "Principal", { Transparencia = { 0.35, 1 }, Easing = "Quad" }),
			esfera("Lanzador", 8, 18, 0.45, "Nucleo", { Transparencia = { 0.5, 1 }, Retraso = 0.1 }),
			chispas("Lanzador", 60, { 30, 90 }, { 0.3, 0.7 }, { "Nucleo", "Principal", "Secundario" }, {
				Direccion = "Atras",
				Dispersion = 40,
				Aceleracion = SIN_GRAVEDAD,
				Tamano = { 1.4, 0 },
			}),
			humo("Lanzador", 10, { 6, 16 }, { 0.6, 1.1 }, { Color = "Oscuro", Aceleracion = SIN_GRAVEDAD }),
			luz("Lanzador", { 5, 0 }, { 30, 60 }, 0.8, "Principal"),
			tinte(0.18, 0.15, 0.25, 0.4, "Principal", { Para = "Lanzador", Saturacion = 0.2 }),
			sacudida(0.7, 0.8, { Para = "Lanzador", Frecuencia = 16 }),
			capa("Zoom", { Delta = 8, Entrada = 0.2, Mantener = 0.3, Salida = 0.5, Para = "Lanzador" }),
		},
	},
}

-- Salida al espacio: una onda fría y un destello limpio.
Recetas.Planeta_Salida = {
	Paleta = "PlanetaDespegue",
	Fases = {
		Lanzamiento = {
			onda("Lanzador", 6, 70, 0.8, "Principal", { Orientacion = "Frente", Grosor = 0.4 }),
			esfera("Lanzador", 4, 30, 0.5, "Nucleo", { Transparencia = { 0.3, 1 }, Easing = "Cubic" }),
			chispas("Lanzador", 30, { 20, 60 }, { 0.3, 0.6 }, { "Nucleo", "Principal" }, {
				Direccion = "Esfera",
				Aceleracion = SIN_GRAVEDAD,
			}),
			tinte(0.25, 0.05, 0.1, 0.6, "Nucleo", { Para = "Lanzador" }),
		},
	},
}

-- Recalentamiento: el casco chisporrotea y la imagen se tiñe y tiembla un poco. Se repite mientras dura.
Recetas.Espacio_Calor = {
	Paleta = "EspacioCalor",
	Fases = {
		Impacto = {
			chispas("Lanzador", 16, { 8, 26 }, { 0.3, 0.6 }, { "Nucleo", "Principal", "Secundario" }, {
				Direccion = "Esfera",
				Aceleracion = SIN_GRAVEDAD,
				Tamano = { 0.9, 0 },
			}),
			humo("Lanzador", 4, { 4, 9 }, { 0.5, 0.9 }, { Color = "Secundario", Aceleracion = SIN_GRAVEDAD }),
			tinte(0.08, 0.15, 0.1, 0.45, "Principal", { Para = "Lanzador", Saturacion = 0.15 }),
			sacudida(0.25, 0.4, { Para = "Lanzador", Frecuencia = 30 }),
		},
	},
}

-- Atracción del agujero negro: la imagen se estira (zoom), se tiñe de morado y vibra.
Recetas.Espacio_Atraccion = {
	Paleta = "EspacioAgujero",
	Fases = {
		Impacto = {
			capa("Zoom", { Delta = 6, Entrada = 0.35, Mantener = 0.1, Salida = 0.6, Para = "Lanzador" }),
			tinte(-0.06, 0.3, 0.1, 0.6, "Principal", { Para = "Lanzador", Saturacion = -0.15, Contraste = 0.1 }),
			sacudida(0.2, 0.6, { Para = "Lanzador", Frecuencia = 12 }),
			chispas("Lanzador", 10, { 10, 30 }, { 0.4, 0.8 }, { "Nucleo", "Principal" }, {
				Direccion = "Esfera",
				Aceleracion = SIN_GRAVEDAD,
				Tamano = { 0.7, 0 },
			}),
		},
	},
}

-- Absorción: la nave implosiona hacia dentro con un destello morado en lugar de estallar.
Recetas.Espacio_Absorcion = {
	Paleta = "EspacioAgujero",
	Fases = {
		Impacto = {
			esfera("Objetivo", 60, 2, 0.7, "Principal", { Transparencia = { 0.2, 0.9 }, Easing = "Quart" }),
			esfera("Objetivo", 30, 1, 0.5, "Nucleo", { Transparencia = { 0, 1 }, Retraso = 0.15 }),
			onda("Objetivo", 120, 4, 0.8, "Secundario", { Orientacion = "Frente", Grosor = 0.6 }),
			luz("Objetivo", { 8, 0 }, { 80, 10 }, 0.9, "Principal"),
			sacudida(1.1, 0.7, { Radio = 300, Para = "Todos" }),
		},
	},
}

return Recetas
