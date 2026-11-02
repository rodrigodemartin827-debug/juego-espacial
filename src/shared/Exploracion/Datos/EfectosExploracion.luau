--!strict
--[[
	EfectosExploracion: las RECETAS visuales del escáner de mano y de la minería.

	Tienen el mismo formato que las del combate y las naves y las reproduce el mismo motor (client/VFX/Gestor.Reproducir):
	fases con capas de partículas, ondas, esferas, luces, proyectiles, rayos, escombros y efectos de pantalla. Aquí se cambian
	colores, tamaños, tiempos y cantidades sin tocar código. Los colores son nombres de Combate/Datos/Paleta; los sonidos,
	de Combate/Datos/Recursos.

	El ESCÁNER se compone de cuatro recetas, que el cliente (client/Exploracion/EfectosEscaneo) va encadenando:
	  Escaner_Carga        (Anticipacion) al empezar: la mano se carga de energía y la pantalla se estrecha un poco
	  Escaner_Pulso        (Lanzamiento)  se repite mientras dura el análisis: rayo, paquetes de datos y ondas sobre el objetivo
	  Escaner_Completado   (Impacto, Residuo) al terminar: estallido de luz, anillos, arcos, esquirlas de datos y destello
	  Escaner_Cancelado    (Impacto)      si se interrumpe: un chisporroteo rojo en la mano
	Además del motor, el cliente dibuja el contorno pulsante del objetivo y los barridos de luz que lo recorren de abajo a arriba.

	La MINERÍA tiene, por cada mineral de Datos/Minerales, dos recetas con la paleta de ese mineral:
	  Minado_Golpe_<id>    (Impacto) un golpe de pico o de láser: chispas, esquirlas y un destello
	  Minado_Rotura_<id>   (Impacto, Residuo) el mineral se rompe: estallido, onda, esquirlas, arcos y polvo

	Anclas que usan: "Mano" (la punta del brazo derecho R6) y "Objetivo" (el punto escaneado o golpeado).
]]

local Atajos = require(script.Parent.Parent.Parent.Combate.Datos.Atajos)
local Minerales = require(script.Parent.Minerales)

local capa, esfera, onda, chispas, humo, luz =
	Atajos.capa, Atajos.esfera, Atajos.onda, Atajos.chispas, Atajos.humo, Atajos.luz
local sacudida, tinte, arco, arcosRadiales, juntar =
	Atajos.sacudida, Atajos.tinte, Atajos.arco, Atajos.arcosRadiales, Atajos.juntar

-- Sin gravedad: las motas de datos y las chispas del escáner flotan.
local SIN_GRAVEDAD = { 0, 0, 0 }
local FLOTAR = { 0, 6, 0 }

local Recetas = {}

-- ===========================================================================================================
-- ESCÁNER DE MANO
-- ===========================================================================================================

-- Al pulsar: la mano se carga. Esferas que se encogen hacia la mano, anillos, chispas y luz.
Recetas.Escaner_Carga = {
	Paleta = "Escaner",
	Fases = {
		Anticipacion = {
			-- Núcleo de energía que se enciende en la mano y la acompaña.
			esfera(
				"Mano",
				6,
				0.7,
				0.55,
				"Secundario",
				{ Transparencia = { 0.85, 0.2 }, Sigue = true, Easing = "Cubic" }
			),
			esfera("Mano", 0.2, 1.3, 0.5, "Nucleo", { Transparencia = { 0.4, 0.05 }, Sigue = true, Easing = "Cubic" }),
			esfera("Mano", 3.2, 0.4, 0.5, "Principal", { Transparencia = { 0.9, 0.35 }, Sigue = true, Retraso = 0.06 }),
			-- Anillos que se cierran sobre la mano.
			onda(
				"Mano",
				7,
				0.8,
				0.5,
				"Principal",
				{ Orientacion = "Frente", Grosor = 0.12, Transparencia = { 0.9, 0.2 }, Easing = "Cubic" }
			),
			onda("Mano", 5, 0.6, 0.45, "Nucleo", {
				Orientacion = "Frente",
				Grosor = 0.08,
				Transparencia = { 0.9, 0.3 },
				Retraso = 0.1,
				Minimo = "Medio",
			}),
			luz("Mano", { 0, 5 }, { 4, 16 }, 0.6, "Principal"),
			chispas("Mano", 26, { 6, 20 }, { 0.3, 0.6 }, { "Nucleo", "Principal", "Secundario" }, {
				Aceleracion = SIN_GRAVEDAD,
				Tamano = { 0.5, 0 },
				Sigue = true,
				Dispersion = 180,
			}),
			-- Un halo de partículas que sigue a la mano mientras escanea.
			capa("Particulas", {
				Anclaje = "Mano",
				Textura = "Destello",
				Tasa = 24,
				Duracion = 0.6,
				Direccion = "Esfera",
				Velocidad = { 1, 4 },
				Vida = { 0.4, 0.8 },
				Tamano = { 0.5, 0 },
				Color = { "Nucleo", "Principal" },
				Aceleracion = FLOTAR,
				Brillo = 1,
				Sigue = true,
				Minimo = "Medio",
			}),
			-- La pantalla de quien escanea se tiñe de cian y se estrecha: "se concentra" en el objetivo.
			tinte(0.05, 0.25, 0.3, 0.5, "Principal", { Para = "Lanzador" }),
			capa("Zoom", { Delta = -3, Entrada = 0.25, Mantener = 0.3, Salida = 0.6, Para = "Lanzador" }),
			capa("Sonido", { Sonido = "EscanerCarga", Volumen = 0.6, Anclaje = "Mano" }),
		},
	},
}

-- Un pulso del análisis. Se repite cada ~0,4 s mientras escanea, así el rayo y las ondas "respiran".
Recetas.Escaner_Pulso = {
	Paleta = "Escaner",
	Fases = {
		Lanzamiento = {
			-- Rayo fino y brillante sobre un halo más grueso de color (comparten el zigzag).
			capa("Haz", {
				Desde = "Mano",
				Hasta = "Objetivo",
				Segmentos = 5,
				Desviacion = 0.35,
				Ancho = { 0.35, 0.05 },
				Color = { "Nucleo", "Principal" },
				Duracion = 0.42,
				Parpadeos = 3,
				Grupo = "escaner",
			}),
			capa("Haz", {
				Desde = "Mano",
				Hasta = "Objetivo",
				Segmentos = 5,
				Desviacion = 0.35,
				Ancho = { 1.3, 0.1 },
				Color = { "Principal", "Secundario" },
				Duracion = 0.42,
				Parpadeos = 3,
				Grupo = "escaner",
				Minimo = "Medio",
			}),
			-- Paquetes de datos que viajan por el rayo.
			capa("Proyectil", {
				Desde = "Mano",
				Hasta = "Objetivo",
				Duracion = 0.32,
				Diametro = 0.45,
				Color = "Principal",
				ColorNucleo = "Nucleo",
				Halo = 3,
				Estela = { Ancho = 0.8, Vida = 0.18 },
				Chispas = 40,
				Luz = 1.2,
			}),
			-- Lo que ocurre sobre el objetivo cuando llega el pulso: anillos, destello y motas de datos.
			onda(
				"Objetivo",
				1.5,
				9,
				0.55,
				"Principal",
				{ Orientacion = "Frente", Grosor = 0.12, Transparencia = { 0.3, 1 }, Retraso = 0.28 }
			),
			onda("Objetivo", 1, 6, 0.45, "Nucleo", {
				Orientacion = "Frente",
				Grosor = 0.08,
				Transparencia = { 0.4, 1 },
				Retraso = 0.36,
				Minimo = "Medio",
			}),
			esfera("Objetivo", 0.6, 3.2, 0.28, "Nucleo", { Transparencia = { 0.2, 1 }, Retraso = 0.28 }),
			luz("Objetivo", { 2.5, 0 }, { 6, 14 }, 0.4, "Principal", { Retraso = 0.28 }),
			chispas("Objetivo", 12, { 3, 14 }, { 0.4, 0.9 }, { "Nucleo", "Principal" }, {
				Aceleracion = FLOTAR,
				Tamano = { 0.6, 0 },
				Retraso = 0.28,
			}),
			capa("Sonido", { Sonido = "EscanerPulso", Volumen = 0.35, Anclaje = "Objetivo", Retraso = 0.28 }),
		},
	},
}

-- Análisis terminado: el objetivo se "revela" con un estallido de luz, anillos, arcos y esquirlas de datos.
Recetas.Escaner_Completado = {
	Paleta = "EscanerCompleto",
	Fases = {
		Impacto = juntar(
			{
				-- Destello blanco y bola de energía en tres capas.
				esfera("Objetivo", 1, 22, 0.55, "Nucleo", { Transparencia = { 0.05, 1 }, Easing = "Cubic" }),
				esfera("Objetivo", 3, 36, 0.95, "Principal", { Transparencia = { 0.45, 1 }, Easing = "Quart" }),
				esfera(
					"Objetivo",
					4,
					50,
					1.4,
					"Secundario",
					{ Transparencia = { 0.75, 1 }, Easing = "Quart", Minimo = "Medio" }
				),
				-- Anillos de confirmación en dos planos, escalonados.
				onda(
					"Objetivo",
					2,
					34,
					0.8,
					"Nucleo",
					{ Orientacion = "Frente", Grosor = 0.2, Transparencia = { 0.1, 1 }, Easing = "Quart" }
				),
				onda(
					"Objetivo",
					2,
					46,
					1,
					"Principal",
					{ Orientacion = "Frente", Grosor = 0.25, Transparencia = { 0.2, 1 }, Retraso = 0.12 }
				),
				onda(
					"Objetivo",
					2,
					40,
					0.95,
					"Secundario",
					{ Orientacion = "Suelo", Grosor = 0.2, Transparencia = { 0.3, 1 }, Retraso = 0.2, Minimo = "Medio" }
				),
				luz("Objetivo", { 7, 0 }, { 14, 46 }, 0.8, "Principal"),
				luz("Objetivo", { 3, 0 }, { 6, 22 }, 1.3, "Nucleo", { Retraso = 0.1, Minimo = "Medio" }),
				-- Chispas y motas de datos que suben flotando.
				chispas("Objetivo", 70, { 10, 55 }, { 0.5, 1.2 }, { "Nucleo", "Principal", "Secundario" }, {
					Aceleracion = SIN_GRAVEDAD,
					Tamano = { 1, 0 },
				}),
				capa("Particulas", {
					Anclaje = "Objetivo",
					Textura = "Destello",
					Cantidad = 36,
					Direccion = "Esfera",
					Velocidad = { 2, 9 },
					Vida = { 1, 2 },
					Tamano = { 0.7, 0 },
					Color = { "Nucleo", "Principal" },
					Aceleracion = FLOTAR,
					Brillo = 1,
					Rotacion = { 0, 360 },
					VelRotacion = { -60, 60 },
					Minimo = "Medio",
				}),
				-- Esquirlas luminosas de datos que salen disparadas sin gravedad.
				capa("Escombros", {
					Anclaje = "Objetivo",
					Libre = true,
					Gravedad = 0,
					Cantidad = 16,
					Radio = 1,
					Tamano = { 0.15, 0.45 },
					Dispersion = { 8, 26 },
					Vida = 1.8,
					Giro = 9,
					Material = "Neon",
					Neon = true,
					Color = { "Principal", "Nucleo" },
					Minimo = "Medio",
				}),
				-- El rayo se ensancha en un último fogonazo hacia el objetivo.
				capa("Haz", {
					Desde = "Mano",
					Hasta = "Objetivo",
					Segmentos = 6,
					Desviacion = 0.5,
					Ancho = { 2.6, 0 },
					Color = { "Nucleo", "Principal" },
					Duracion = 0.3,
					Parpadeos = 2,
					Ramas = 2,
				}),
				-- Efectos de pantalla para quien escaneó.
				tinte(0.24, 0.02, 0.05, 0.5, "Principal", { Para = "Lanzador" }),
				capa("Desenfoque", {
					Tamano = 7,
					Entrada = 0.03,
					Mantener = 0.05,
					Salida = 0.4,
					Para = "Lanzador",
					Minimo = "Medio",
				}),
				capa("Zoom", { Delta = 4, Entrada = 0.04, Mantener = 0.05, Salida = 0.5, Para = "Lanzador" }),
				sacudida(0.5, 0.35, { Radio = 60, Para = "Lanzador" }),
				capa("Sonido", { Sonido = "EscanerCompleto", Volumen = 0.85, Anclaje = "Objetivo" }),
			},
			-- Arcos eléctricos que recorren el objetivo.
			arcosRadiales("Objetivo", 6, 5, { "Nucleo", "Principal" }, 0.05, { Minimo = "Medio" })
		),
		Residuo = {
			capa("Particulas", {
				Anclaje = "Objetivo",
				Textura = "Destello",
				Tasa = 40,
				Duracion = 1.4,
				Direccion = "Esfera",
				Velocidad = { 1, 5 },
				Vida = { 0.8, 1.6 },
				Tamano = { 0.5, 0 },
				Color = { "Nucleo", "Principal" },
				Aceleracion = FLOTAR,
				Brillo = 1,
			}),
			luz("Objetivo", { 2, 0 }, { 10, 18 }, 1.2, "Principal"),
		},
	},
}

-- El escaneo se interrumpe: la carga se deshace en chispas rojas.
Recetas.Escaner_Cancelado = {
	Paleta = "EscanerFallo",
	Fases = {
		Impacto = {
			esfera("Mano", 2.2, 0.2, 0.25, "Principal", { Transparencia = { 0.4, 1 } }),
			onda("Mano", 0.8, 4, 0.3, "Secundario", { Orientacion = "Frente", Grosor = 0.1 }),
			luz("Mano", { 3, 0 }, { 8, 3 }, 0.3, "Principal"),
			chispas("Mano", 18, { 8, 28 }, { 0.2, 0.5 }, { "Nucleo", "Principal" }, {
				Aceleracion = { 0, -30, 0 },
				Tamano = { 0.6, 0 },
				Dispersion = 180,
			}),
			capa("Sonido", { Sonido = "EscanerFallo", Volumen = 0.5, Anclaje = "Mano" }),
		},
	},
}

-- ===========================================================================================================
-- MINERÍA (dos recetas por mineral, con su paleta)
-- ===========================================================================================================

for _, id in Minerales.Orden do
	local paleta = `Mineral_{id}`

	-- Un golpe: destello, chispas y esquirlas.
	Recetas[`Minado_Golpe_{id}`] = {
		Paleta = paleta,
		Fases = {
			Impacto = {
				esfera("Objetivo", 0.6, 4, 0.16, "Nucleo", { Transparencia = { 0.1, 1 } }),
				onda("Objetivo", 0.8, 6, 0.22, "Principal", { Orientacion = "Frente", Grosor = 0.12 }),
				luz("Objetivo", { 3, 0 }, { 6, 16 }, 0.2, "Principal"),
				chispas("Objetivo", 22, { 10, 38 }, { 0.2, 0.55 }, { "Nucleo", "Principal", "Secundario" }, {
					Aceleracion = { 0, -40, 0 },
					Tamano = { 0.8, 0 },
				}),
				capa("Escombros", {
					Anclaje = "Objetivo",
					Libre = true,
					Gravedad = 0,
					Cantidad = 5,
					Radio = 0.8,
					Tamano = { 0.2, 0.55 },
					Dispersion = { 8, 22 },
					Vida = 1.2,
					Giro = 8,
					Material = "Roca",
					Color = { "Secundario", "Principal" },
					Minimo = "Medio",
				}),
				sacudida(0.25, 0.14, { Radio = 25, Para = "Todos" }),
				capa("Sonido", { Sonido = "MinadoGolpe", Volumen = 0.6, Anclaje = "Objetivo" }),
			},
		},
	}

	-- La rotura: estallido de color, polvo, esquirlas y arcos.
	Recetas[`Minado_Rotura_{id}`] = {
		Paleta = paleta,
		Fases = {
			Impacto = juntar({
				esfera("Objetivo", 1, 10, 0.3, "Nucleo", { Transparencia = { 0, 1 }, Easing = "Cubic" }),
				esfera("Objetivo", 2, 16, 0.55, "Principal", { Transparencia = { 0.4, 1 }, Easing = "Quart" }),
				esfera("Objetivo", 3, 22, 0.8, "Secundario", { Transparencia = { 0.7, 1 }, Minimo = "Medio" }),
				onda("Objetivo", 1.5, 18, 0.5, "Principal", { Orientacion = "Frente", Grosor = 0.2 }),
				onda("Objetivo", 1.5, 22, 0.6, "Nucleo", {
					Orientacion = "Suelo",
					Grosor = 0.18,
					Transparencia = { 0.3, 1 },
					Retraso = 0.05,
					Minimo = "Medio",
				}),
				luz("Objetivo", { 6, 0 }, { 10, 30 }, 0.55, "Principal"),
				chispas("Objetivo", 60, { 14, 60 }, { 0.3, 0.9 }, { "Nucleo", "Principal", "Secundario" }, {
					Aceleracion = { 0, -35, 0 },
					Tamano = { 1, 0 },
				}),
				capa("Escombros", {
					Anclaje = "Objetivo",
					Libre = true,
					Gravedad = 0,
					Cantidad = 16,
					Radio = 1.5,
					Tamano = { 0.3, 1 },
					Dispersion = { 10, 34 },
					Vida = 1.8,
					Giro = 7,
					Material = "Roca",
					Color = { "Principal", "Secundario", "Oscuro" },
				}),
				arco("Objetivo", { 0, 0, 0 }, "Objetivo", { 4, 2, 1 }, 0.2, { "Nucleo", "Principal" }, {
					Segmentos = 4,
					Desviacion = 0.8,
					Minimo = "Medio",
				}),
				arco("Objetivo", { 0, 0, 0 }, "Objetivo", { -3, 3, -2 }, 0.2, { "Nucleo", "Secundario" }, {
					Segmentos = 4,
					Desviacion = 0.8,
					Retraso = 0.04,
					Minimo = "Alto",
				}),
				sacudida(0.7, 0.3, { Radio = 70, Para = "Todos" }),
				tinte(0.12, 0.02, 0.03, 0.25, "Principal", { Para = "Implicados" }),
				capa("Sonido", { Sonido = "MinadoRotura", Volumen = 0.9, Anclaje = "Objetivo" }),
			}, {
				humo("Objetivo", 14, { 4, 9 }, { 0.8, 1.6 }, {
					Direccion = "Esfera",
					Velocidad = { 3, 12 },
					Aceleracion = { 0, 4, 0 },
					Minimo = "Medio",
				}),
			}),
			Residuo = {
				humo("Objetivo", 8, { 4, 8 }, { 1, 2 }, {
					Velocidad = { 1, 5 },
					Aceleracion = { 0, 3, 0 },
					Minimo = "Alto",
				}),
			},
		},
	}
end

return Recetas
