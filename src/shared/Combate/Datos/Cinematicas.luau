--!strict
--[[
	Cinematicas: los movimientos de cámara de las habilidades definitivas.

	Cada cinemática es una lista de PLANOS; cada plano mueve la cámara de `Desde` a `Hasta` durante `Duracion`
	segundos (sin `Hasta`, queda quieta). Un extremo tiene:
	  Pos     { Ancla, Desplazamiento }   dónde está la cámara
	  Mirar   { Ancla, Desplazamiento }   a qué mira
	  FOV     campo de visión (70 es lo normal; menos = zoom, más = angular)
	Las anclas son "Lanzador", "Mano", "Origen", "Objetivo", "Suelo" y "Cielo". El desplazamiento { x, y, z } es
	relativo al ancla en un sistema que MIRA hacia donde apunta el golpe: z positiva = DETRÁS del ancla,
	z negativa = delante, x positiva = a su derecha.

	La suma de las duraciones debe cubrir hasta pasado el impacto (Carga + Viaje de la habilidad) para que
	la cámara enseñe la explosión.
]]

local Cinematicas = {}

Cinematicas.Rayo_Definitiva = {
	Barras = true,
	Planos = {
		-- 1. Contrapicado desde atrás: el héroe empieza a cargar.
		{
			Duracion = 0.8,
			Easing = "Cubic",
			Desde = {
				Pos = { Ancla = "Lanzador", Desplazamiento = { 2.5, -1.5, 7 } },
				Mirar = { Ancla = "Lanzador", Desplazamiento = { 0, 3, 0 } },
				FOV = 55,
			},
			Hasta = {
				Pos = { Ancla = "Lanzador", Desplazamiento = { -3, 1.5, 10 } },
				Mirar = { Ancla = "Lanzador", Desplazamiento = { 0, 6, 0 } },
				FOV = 66,
			},
		},
		-- 2. Barrido hacia el cielo: se forma la tormenta.
		{
			Duracion = 1.0,
			Easing = "Quad",
			Desde = {
				Pos = { Ancla = "Lanzador", Desplazamiento = { 0, 7, 15 } },
				Mirar = { Ancla = "Cielo", Desplazamiento = { 0, -120, 0 } },
				FOV = 80,
			},
			Hasta = {
				Pos = { Ancla = "Lanzador", Desplazamiento = { 0, 12, 22 } },
				Mirar = { Ancla = "Cielo", Desplazamiento = { 0, -35, 0 } },
				FOV = 96,
			},
		},
		-- 3. Primer plano frontal del lanzador con los brazos al cielo.
		{
			Duracion = 0.7,
			Easing = "Cubic",
			Desde = {
				Pos = { Ancla = "Lanzador", Desplazamiento = { 2, 3.5, -8 } },
				Mirar = { Ancla = "Lanzador", Desplazamiento = { 0, 4, 0 } },
				FOV = 52,
			},
			Hasta = {
				Pos = { Ancla = "Lanzador", Desplazamiento = { 1, 3.5, -5 } },
				Mirar = { Ancla = "Lanzador", Desplazamiento = { 0, 4.5, 0 } },
				FOV = 40,
			},
		},
		-- 4. Corte seco al lugar del impacto, desde lo alto, justo antes de que caiga el rayo.
		{
			Duracion = 0.5,
			Easing = "Quad",
			Desde = {
				Pos = { Ancla = "Objetivo", Desplazamiento = { 22, 26, 30 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 2, 0 } },
				FOV = 72,
			},
			Hasta = {
				Pos = { Ancla = "Objetivo", Desplazamiento = { 16, 18, 22 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 2, 0 } },
				FOV = 62,
			},
		},
		-- 5. Tras el impacto: la cámara se aleja para ver el cráter.
		{
			Duracion = 1.0,
			Easing = "Quad",
			Desde = {
				Pos = { Ancla = "Objetivo", Desplazamiento = { 24, 12, 34 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 5, 0 } },
				FOV = 72,
			},
			Hasta = {
				Pos = { Ancla = "Objetivo", Desplazamiento = { 34, 26, 52 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 4, 0 } },
				FOV = 88,
			},
		},
	},
}

Cinematicas.Gravedad_Definitiva = {
	Barras = true,
	Planos = {
		-- 1. Desde atrás y abajo: el lanzador comprime la gravedad.
		{
			Duracion = 0.9,
			Easing = "Cubic",
			Desde = {
				Pos = { Ancla = "Lanzador", Desplazamiento = { -2.5, -1, 7 } },
				Mirar = { Ancla = "Lanzador", Desplazamiento = { 0, 3, 0 } },
				FOV = 58,
			},
			Hasta = {
				Pos = { Ancla = "Lanzador", Desplazamiento = { 3, 2, 11 } },
				Mirar = { Ancla = "Lanzador", Desplazamiento = { 0, 5, -2 } },
				FOV = 68,
			},
		},
		-- 2. La cámara viaja hasta el punto donde nace la singularidad.
		{
			Duracion = 1.0,
			Easing = "Quad",
			Desde = {
				Pos = { Ancla = "Lanzador", Desplazamiento = { 0, 6, 12 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 10, 0 } },
				FOV = 70,
			},
			Hasta = {
				Pos = { Ancla = "Objetivo", Desplazamiento = { 0, 20, 36 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 10, 0 } },
				FOV = 82,
			},
		},
		-- 3. Órbita lenta alrededor del agujero negro mientras crece y arrastra todo.
		{
			Duracion = 1.1,
			Easing = "Sine",
			Desde = {
				Pos = { Ancla = "Objetivo", Desplazamiento = { -22, 14, 26 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 11, 0 } },
				FOV = 76,
			},
			Hasta = {
				Pos = { Ancla = "Objetivo", Desplazamiento = { 20, 9, 22 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 11, 0 } },
				FOV = 62,
			},
		},
		-- 4. Acercamiento brusco justo antes del colapso.
		{
			Duracion = 0.3,
			Easing = "Quint",
			Desde = {
				Pos = { Ancla = "Objetivo", Desplazamiento = { 4, 11, 20 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 10, 0 } },
				FOV = 92,
			},
			Hasta = {
				Pos = { Ancla = "Objetivo", Desplazamiento = { 2, 10, 14 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 10, 0 } },
				FOV = 48,
			},
		},
		-- 5. La explosión: plano amplio que se aleja.
		{
			Duracion = 0.9,
			Easing = "Quad",
			Desde = {
				Pos = { Ancla = "Objetivo", Desplazamiento = { 30, 20, 40 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 8, 0 } },
				FOV = 84,
			},
			Hasta = {
				Pos = { Ancla = "Objetivo", Desplazamiento = { 44, 34, 62 } },
				Mirar = { Ancla = "Objetivo", Desplazamiento = { 0, 6, 0 } },
				FOV = 96,
			},
		},
	},
}

return Cinematicas
