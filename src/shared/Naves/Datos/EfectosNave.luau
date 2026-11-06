--!strict
--[[
	EfectosNave: las RECETAS visuales del sistema de naves.

	Tienen el mismo formato que las del combate (Combate/Datos/EfectosVFX) y las reproduce el mismo motor
	(client/VFX/Gestor.Reproducir): fases con capas de partículas, ondas, esferas, luces, proyectiles, rayos,
	escombros y efectos de pantalla. Aquí se cambian colores, tamaños, tiempos y cantidades sin tocar código.
	Los colores son nombres de Combate/Datos/Paleta; las texturas, mallas y sonidos, de Combate/Datos/Recursos.

	Qué receta se usa en cada momento:
	  Nave_Laser_<Bando>        un disparo (fase Lanzamiento): fogonazo en el cañón + proyectil + haz
	  Nave_Impacto_Escudo       el láser golpea una nave con escudo
	  Nave_Impacto_Casco        el láser golpea el casco de una nave
	  Nave_Impacto_Asteroide    el láser golpea una roca
	  Nave_Choque_Escudo        una nave choca con un asteroide y el escudo aguanta
	  Nave_Choque_Casco         ídem, pero el golpe llega al casco
	  Nave_Explosion            una nave es destruida
	  Nave_Asteroide_<Tamaño>   un asteroide estalla (Pequeno, Mediano o Grande)
	  Nave_Propulsor            un pulso de los propulsores (se repite mientras se acelera)
	  Nave_Propulsor_Turbo      ídem, con turbo
	  Nave_Turbo_Arranque       el instante en que se enciende el turbo
	  Nave_Despegue             la nave arranca en el hangar

	Anclas especiales de las naves: "Origen" (la boca del cañón que dispara), "Objetivo" (el punto de impacto),
	"Lanzador" (el centro de la nave) y los Attachments del modelo "MotorIzq" y "MotorDer".
]]

local Atajos = require(script.Parent.Parent.Parent.Combate.Datos.Atajos)

local capa, esfera, onda, chispas, humo, luz =
	Atajos.capa, Atajos.esfera, Atajos.onda, Atajos.chispas, Atajos.humo, Atajos.luz
local sacudida, tinte, arco, arcosRadiales, juntar =
	Atajos.sacudida, Atajos.tinte, Atajos.arco, Atajos.arcosRadiales, Atajos.juntar

-- En el espacio no hay gravedad: las chispas no caen.
local SIN_GRAVEDAD = { 0, 0, 0 }

local Recetas = {}

-- ===========================================================================================================
-- DISPARO LÁSER
-- ===========================================================================================================

-- Un láser con la paleta del bando: fogonazo, proyectil con estela, haz de luz y un destello de chispas hacia delante.
local function laser(paleta: string)
	return {
		Paleta = paleta,
		Fases = {
			Lanzamiento = {
				-- Fogonazo en la boca del cañón.
				esfera("Origen", 0.3, 2.8, 0.13, "Nucleo", { Transparencia = { 0, 1 }, Easing = "Cubic" }),
				esfera("Origen", 0.6, 5.5, 0.22, "Principal", { Transparencia = { 0.5, 1 } }),
				luz("Origen", { 6, 0 }, { 10, 28 }, 0.22, "Principal"),
				onda(
					"Origen",
					1,
					7.5,
					0.24,
					"Principal",
					{ Orientacion = "Frente", Grosor = 0.15, Transparencia = { 0.2, 1 } }
				),
				chispas("Origen", 22, { 25, 80 }, { 0.12, 0.32 }, { "Nucleo", "Principal" }, {
					Direccion = "Frente",
					Dispersion = 24,
					Aceleracion = SIN_GRAVEDAD,
					Tamano = { 0.9, 0 },
				}),
				-- El proyectil de energía, con estela, halo y su propia luz.
				capa("Proyectil", {
					Desde = "Origen",
					Hasta = "Objetivo",
					Duracion = "Viaje",
					Diametro = 0.9,
					Color = "Principal",
					ColorNucleo = "Nucleo",
					Halo = 3.4,
					Estela = { Ancho = 1.6, Vida = 0.22 },
					Chispas = 80,
					Luz = 2.4,
				}),
				-- Línea de luz que se apaga enseguida: da la sensación de rayo láser.
				capa("Haz", {
					Desde = "Origen",
					Hasta = "Objetivo",
					Segmentos = 3,
					Desviacion = 0,
					Ancho = { 1.5, 0 },
					Color = { "Nucleo", "Principal" },
					Duracion = 0.12,
					Parpadeos = 1,
				}),
				capa("Sonido", { Sonido = "NaveLaser", Volumen = 0.55, Anclaje = "Origen" }),
			},
		},
	}
end

Recetas.Nave_Laser_Humanos = laser("NaveLaserHumanos")
Recetas.Nave_Laser_Monstruos = laser("NaveLaserMonstruos")
Recetas.Nave_Laser_Neutral = laser("NaveLaserNeutral")

-- ===========================================================================================================
-- IMPACTOS DEL LÁSER
-- ===========================================================================================================

-- Se ve una burbuja de energía que se ilumina donde pega el disparo, con una onda y chispas azules.
Recetas.Nave_Impacto_Escudo = {
	Paleta = "NaveEscudo",
	Fases = {
		Impacto = {
			esfera("Objetivo", 2, 12, 0.3, "Principal", { Transparencia = { 0.45, 1 }, Easing = "Cubic" }),
			esfera("Objetivo", 1, 5, 0.16, "Nucleo", { Transparencia = { 0.05, 1 } }),
			onda(
				"Objetivo",
				1.5,
				15,
				0.34,
				"Secundario",
				{ Orientacion = "Frente", Grosor = 0.2, Transparencia = { 0.25, 1 } }
			),
			luz("Objetivo", { 5, 0 }, { 8, 24 }, 0.3, "Principal"),
			chispas("Objetivo", 26, { 18, 60 }, { 0.2, 0.5 }, { "Nucleo", "Principal", "Secundario" }, {
				Aceleracion = SIN_GRAVEDAD,
				Tamano = { 0.9, 0 },
			}),
			arco("Objetivo", { 0, 0, 0 }, "Objetivo", { 3.5, 2, 1.5 }, 0.18, { "Nucleo", "Principal" }, {
				Segmentos = 4,
				Desviacion = 0.8,
				Minimo = "Medio",
			}),
			arco("Objetivo", { 0, 0, 0 }, "Objetivo", { -3, -2.5, 2 }, 0.18, { "Nucleo", "Secundario" }, {
				Segmentos = 4,
				Desviacion = 0.8,
				Retraso = 0.04,
				Minimo = "Alto",
			}),
			capa("Sonido", { Sonido = "NaveEscudo", Volumen = 0.6, Anclaje = "Objetivo" }),
		},
	},
}

-- Chispas naranjas, un trozo de chapa que sale despedido y un hilo de humo.
Recetas.Nave_Impacto_Casco = {
	Paleta = "NaveExplosion",
	Fases = {
		Impacto = {
			esfera("Objetivo", 1, 6.5, 0.2, "Nucleo", { Transparencia = { 0.05, 1 } }),
			esfera("Objetivo", 2, 9, 0.3, "Principal", { Transparencia = { 0.5, 1 } }),
			luz("Objetivo", { 6, 0 }, { 8, 26 }, 0.3, "Secundario"),
			onda("Objetivo", 1, 10, 0.26, "Principal", { Orientacion = "Frente", Grosor = 0.2 }),
			chispas("Objetivo", 38, { 20, 85 }, { 0.2, 0.6 }, { "Nucleo", "Principal", "Secundario" }, {
				Aceleracion = SIN_GRAVEDAD,
				Tamano = { 1.1, 0 },
			}),
			capa("Escombros", {
				Anclaje = "Objetivo",
				Libre = true,
				Gravedad = 0,
				Cantidad = 5,
				Radio = 1.5,
				Tamano = { 0.25, 0.6 },
				Dispersion = { 18, 45 },
				Vida = 1.2,
				Giro = 8,
				Material = "Basalto",
				Color = "Oscuro",
				Minimo = "Medio",
			}),
			capa("Sacudida", { Intensidad = 0.5, Duracion = 0.25, Frecuencia = 24, Radio = 90, Para = "Implicados" }),
			capa("Sonido", { Sonido = "NaveImpacto", Volumen = 0.6, Anclaje = "Objetivo" }),
		},
		Residuo = {
			humo("Objetivo", 7, { 3, 7 }, { 0.8, 1.6 }, {
				Direccion = "Esfera",
				Velocidad = { 3, 10 },
				Aceleracion = SIN_GRAVEDAD,
				Minimo = "Medio",
			}),
		},
	},
}

-- Polvo y esquirlas de roca: el disparo arranca un pedazo del asteroide.
Recetas.Nave_Impacto_Asteroide = {
	Paleta = "Asteroide",
	Fases = {
		Impacto = {
			esfera("Objetivo", 1, 7, 0.22, "Nucleo", { Transparencia = { 0.1, 1 } }),
			luz("Objetivo", { 5, 0 }, { 8, 22 }, 0.25, "Secundario"),
			onda("Objetivo", 1, 11, 0.28, "Secundario", { Orientacion = "Frente", Grosor = 0.2 }),
			chispas("Objetivo", 30, { 18, 70 }, { 0.2, 0.55 }, { "Nucleo", "Secundario" }, {
				Aceleracion = SIN_GRAVEDAD,
				Tamano = { 1, 0 },
			}),
			humo("Objetivo", 12, { 4, 9 }, { 0.9, 1.8 }, {
				Direccion = "Esfera",
				Velocidad = { 4, 16 },
				Aceleracion = SIN_GRAVEDAD,
			}),
			capa("Escombros", {
				Anclaje = "Objetivo",
				Libre = true,
				Gravedad = 0,
				Cantidad = 9,
				Radio = 1.5,
				Tamano = { 0.4, 1.3 },
				Dispersion = { 10, 38 },
				Vida = 2,
				Giro = 5,
				Material = "Roca",
				Color = "Principal",
			}),
			capa("Sonido", { Sonido = "NaveImpacto", Volumen = 0.5, Anclaje = "Objetivo" }),
		},
	},
}

-- ===========================================================================================================
-- CHOQUES CON ASTEROIDES
-- ===========================================================================================================

-- Choque contra una roca. `escudo` = el escudo absorbió el golpe: se ve la burbuja azul en lugar del casco roto.
local function choque(escudo: boolean)
	local paleta = if escudo then "NaveEscudo" else "NaveExplosion"
	return {
		Paleta = paleta,
		Fases = {
			Impacto = juntar({
				esfera(
					"Objetivo",
					2,
					if escudo then 18 else 13,
					0.34,
					"Principal",
					{ Transparencia = { 0.4, 1 }, Easing = "Cubic" }
				),
				esfera("Objetivo", 1, 8, 0.2, "Nucleo", { Transparencia = { 0, 1 } }),
				onda("Objetivo", 2, 26, 0.45, "Secundario", { Orientacion = "Frente", Grosor = 0.3 }),
				luz("Objetivo", { 8, 0 }, { 12, 40 }, 0.4, if escudo then "Principal" else "Secundario"),
				chispas("Objetivo", 55, { 25, 100 }, { 0.3, 0.9 }, { "Nucleo", "Principal", "Secundario" }, {
					Aceleracion = SIN_GRAVEDAD,
					Tamano = { 1.3, 0 },
				}),
			}, {
				-- Esquirlas de la roca.
				capa("Escombros", {
					Anclaje = "Objetivo",
					Libre = true,
					Gravedad = 0,
					Cantidad = 12,
					Radio = 2,
					Tamano = { 0.4, 1.5 },
					Dispersion = { 12, 45 },
					Vida = 2.2,
					Giro = 6,
					Material = "Roca",
					Color = { "Principal" },
					Minimo = "Medio",
				}),
				humo("Objetivo", 12, { 5, 11 }, { 1, 2 }, {
					Direccion = "Esfera",
					Velocidad = { 4, 18 },
					Aceleracion = SIN_GRAVEDAD,
					Color = "Oscuro",
					Minimo = "Medio",
				}),
				-- Todos los cercanos notan la sacudida; el tinte y el desenfoque son solo para el implicado.
				sacudida(1.4, 0.55, { Radio = 220, Para = "Todos" }),
				tinte(
					if escudo then 0.18 else 0.3,
					0.02,
					0.04,
					0.3,
					if escudo then "Principal" else "Secundario",
					{ Para = "Implicados" }
				),
				capa("Desenfoque", {
					Tamano = 8,
					Entrada = 0.02,
					Mantener = 0.05,
					Salida = 0.3,
					Para = "Implicados",
					Minimo = "Medio",
				}),
				capa(
					"Sonido",
					{ Sonido = if escudo then "NaveEscudo" else "NaveChoque", Volumen = 0.9, Anclaje = "Objetivo" }
				),
			}),
			Residuo = {
				humo("Objetivo", 8, { 4, 8 }, { 1, 2.2 }, {
					Direccion = "Esfera",
					Velocidad = { 2, 8 },
					Aceleracion = SIN_GRAVEDAD,
					Minimo = "Alto",
				}),
			},
		},
	}
end

Recetas.Nave_Choque_Escudo = choque(true)
Recetas.Nave_Choque_Casco = choque(false)

-- ===========================================================================================================
-- EXPLOSIÓN DE UNA NAVE
-- ===========================================================================================================

Recetas.Nave_Explosion = {
	Paleta = "NaveExplosion",
	Fases = {
		Impacto = juntar(
			{
				-- Destello blanco inicial y bola de fuego en tres capas (núcleo, llama, resplandor).
				esfera("Objetivo", 2, 34, 0.5, "Nucleo", { Transparencia = { 0, 1 }, Easing = "Cubic" }),
				esfera("Objetivo", 4, 58, 0.9, "Principal", { Transparencia = { 0.2, 1 }, Easing = "Quart" }),
				esfera("Objetivo", 6, 82, 1.4, "Secundario", { Transparencia = { 0.6, 1 }, Easing = "Quart" }),
				-- Ondas de choque en dos planos.
				onda(
					"Objetivo",
					6,
					130,
					1.1,
					"Nucleo",
					{ Orientacion = "Frente", Grosor = 0.5, Transparencia = { 0.1, 1 } }
				),
				onda(
					"Objetivo",
					4,
					105,
					1.3,
					"Principal",
					{ Orientacion = "Suelo", Grosor = 0.5, Transparencia = { 0.2, 1 }, Retraso = 0.05 }
				),
				onda(
					"Objetivo",
					4,
					80,
					1.5,
					"Secundario",
					{ Orientacion = "Frente", Grosor = 0.4, Giro = 60, Retraso = 0.12, Minimo = "Alto" }
				),
				-- Luz que ilumina las naves y asteroides de alrededor.
				luz("Objetivo", { 14, 0 }, { 40, 170 }, 1.3, "Principal"),
				luz("Objetivo", { 8, 0 }, { 30, 110 }, 0.7, "Nucleo"),
				-- Chispas, fuego y humo.
				chispas("Objetivo", 190, { 40, 170 }, { 0.6, 1.7 }, { "Nucleo", "Principal", "Secundario" }, {
					Aceleracion = SIN_GRAVEDAD,
					Tamano = { 1.5, 0 },
					Arrastre = 0.6,
				}),
				capa("Particulas", {
					Anclaje = "Objetivo",
					Textura = "Fuego",
					Cantidad = 70,
					Direccion = "Esfera",
					Velocidad = { 8, 55 },
					Vida = { 0.5, 1.3 },
					Tamano = { 8, 16 },
					Transparencia = { 0.2, 1 },
					Color = { "Nucleo", "Principal", "Secundario", "Oscuro" },
					Brillo = 1,
					Rotacion = { 0, 360 },
					VelRotacion = { -90, 90 },
					Arrastre = 1.2,
					Aceleracion = SIN_GRAVEDAD,
				}),
				humo("Objetivo", 46, { 9, 24 }, { 1.8, 3.6 }, {
					Direccion = "Esfera",
					Velocidad = { 5, 30 },
					Aceleracion = SIN_GRAVEDAD,
					Arrastre = 1.5,
					Minimo = "Medio",
				}),
				-- Restos del casco: chapa oscura y trozos al rojo vivo.
				capa("Escombros", {
					Anclaje = "Objetivo",
					Libre = true,
					Gravedad = 0,
					Cantidad = 26,
					Radio = 3,
					Tamano = { 0.7, 2.6 },
					Dispersion = { 28, 95 },
					Vida = 4.5,
					Giro = 3,
					Material = "Basalto",
					Color = "Oscuro",
				}),
				capa("Escombros", {
					Anclaje = "Objetivo",
					Libre = true,
					Gravedad = 0,
					Cantidad = 14,
					Radio = 3,
					Tamano = { 0.5, 1.4 },
					Dispersion = { 30, 105 },
					Vida = 3,
					Giro = 5,
					Neon = true,
					Color = "Secundario",
					Minimo = "Medio",
				}),
			},
			arcosRadiales("Objetivo", 6, 20, { "Nucleo", "Principal" }, 0.04, { Minimo = "Alto" }),
			{
				-- Explosiones secundarias, escalonadas.
				esfera(
					"Objetivo",
					3,
					26,
					0.45,
					"Principal",
					{ Retraso = 0.22, Desplazamiento = { 5, 2, 3 }, Transparencia = { 0.25, 1 } }
				),
				esfera(
					"Objetivo",
					3,
					22,
					0.4,
					"Secundario",
					{ Retraso = 0.4, Desplazamiento = { -6, -2, -4 }, Transparencia = { 0.3, 1 } }
				),
				luz("Objetivo", { 8, 0 }, { 20, 80 }, 0.5, "Secundario", { Retraso = 0.22 }),
				chispas("Objetivo", 70, { 30, 110 }, { 0.5, 1.3 }, { "Principal", "Secundario" }, {
					Retraso = 0.22,
					Aceleracion = SIN_GRAVEDAD,
					Tamano = { 1.2, 0 },
					Minimo = "Medio",
				}),
				-- Pantalla: sacude a quien esté cerca, y al piloto además lo deslumbra.
				sacudida(2.6, 1.0, { Radio = 700, Frecuencia = 18 }),
				tinte(0.6, 0.02, 0.05, 0.6, "Nucleo", { Para = "Implicados" }),
				capa("Desenfoque", {
					Tamano = 14,
					Entrada = 0.02,
					Mantener = 0.12,
					Salida = 0.6,
					Para = "Implicados",
					Minimo = "Medio",
				}),
				capa("Sonido", { Sonido = "NaveExplosion", Volumen = 1, Anclaje = "Objetivo" }),
			}
		),
		Residuo = {
			-- Brasas que se enfrían lentamente y nube de humo que se queda flotando.
			capa("Particulas", {
				Anclaje = "Objetivo",
				Textura = "Chispa",
				Cantidad = 60,
				Direccion = "Esfera",
				Velocidad = { 4, 22 },
				Vida = { 2, 4 },
				Tamano = { 0.9, 0 },
				Color = { "Nucleo", "Principal", "Secundario", "Oscuro" },
				Brillo = 1,
				Aceleracion = SIN_GRAVEDAD,
				Arrastre = 0.8,
				Minimo = "Medio",
			}),
			humo("Objetivo", 24, { 14, 30 }, { 3, 5.5 }, {
				Retraso = 0.3,
				Direccion = "Esfera",
				Velocidad = { 2, 12 },
				Aceleracion = SIN_GRAVEDAD,
				Arrastre = 1.4,
				Transparencia = { 0.55, 1 },
				Minimo = "Medio",
			}),
			luz("Objetivo", { 3, 0 }, { 30, 60 }, 2.2, "Secundario", { Retraso = 0.4 }),
		},
	},
}

-- ===========================================================================================================
-- ASTEROIDES QUE ESTALLAN
-- ===========================================================================================================

-- `escala` 1 = asteroide mediano. Las cantidades se reparten según el tamaño.
local function asteroideRoto(escala: number)
	local function e(valor: number): number
		return math.floor(valor * escala + 0.5)
	end
	return {
		Paleta = "Asteroide",
		Fases = {
			Impacto = {
				esfera(
					"Objetivo",
					2 * escala,
					22 * escala,
					0.38,
					"Nucleo",
					{ Transparencia = { 0.1, 1 }, Easing = "Cubic" }
				),
				esfera("Objetivo", 3 * escala, 34 * escala, 0.6, "Secundario", { Transparencia = { 0.55, 1 } }),
				onda(
					"Objetivo",
					3 * escala,
					60 * escala,
					0.7,
					"Principal",
					{ Orientacion = "Frente", Grosor = 0.35, Transparencia = { 0.3, 1 } }
				),
				luz("Objetivo", { 7, 0 }, { 14 * escala, 60 * escala }, 0.6, "Secundario"),
				chispas("Objetivo", math.min(e(60), 160), { 20, 90 }, { 0.3, 1 }, { "Nucleo", "Secundario" }, {
					Aceleracion = SIN_GRAVEDAD,
					Tamano = { 1.2, 0 },
				}),
				-- Nube de polvo y roca pulverizada.
				humo("Objetivo", math.min(e(30), 70), { 7 * escala, 18 * escala }, { 1.6, 3.2 }, {
					Direccion = "Esfera",
					Velocidad = { 4, 22 },
					Aceleracion = SIN_GRAVEDAD,
					Arrastre = 1.5,
					Color = "Oscuro",
				}),
				-- Los pedazos: unos grandes que giran despacio y otros pequeños y rápidos.
				capa("Escombros", {
					Anclaje = "Objetivo",
					Libre = true,
					Gravedad = 0,
					Cantidad = math.min(e(16), 60),
					Radio = 3 * escala,
					Tamano = { 0.8 * escala, 3 * escala },
					Dispersion = { 8, 38 },
					Vida = 4,
					Giro = 2.5,
					Material = "Roca",
					Color = "Principal",
				}),
				capa("Escombros", {
					Anclaje = "Objetivo",
					Libre = true,
					Gravedad = 0,
					Cantidad = math.min(e(14), 40),
					Radio = 3 * escala,
					Tamano = { 0.3, 0.9 },
					Dispersion = { 25, 85 },
					Vida = 2.4,
					Giro = 8,
					Material = "Basalto",
					Color = "Oscuro",
					Minimo = "Medio",
				}),
				sacudida(0.5 + escala * 0.5, 0.5, { Radio = 150 + 100 * escala }),
				capa("Sonido", { Sonido = "AsteroideRoto", Volumen = 0.5 + 0.2 * escala, Anclaje = "Objetivo" }),
			},
			Residuo = {
				humo("Objetivo", math.min(e(10), 24), { 8 * escala, 16 * escala }, { 2.5, 4.5 }, {
					Retraso = 0.2,
					Direccion = "Esfera",
					Velocidad = { 1, 8 },
					Aceleracion = SIN_GRAVEDAD,
					Arrastre = 1.2,
					Minimo = "Medio",
				}),
			},
		},
	}
end

Recetas.Nave_Asteroide_Pequeno = asteroideRoto(0.6)
Recetas.Nave_Asteroide_Mediano = asteroideRoto(1)
Recetas.Nave_Asteroide_Grande = asteroideRoto(1.8)

-- ===========================================================================================================
-- PROPULSORES
-- ===========================================================================================================

-- Un pulso de los dos propulsores. Se repite varias veces por segundo mientras la nave acelera, y su fuerza se
-- ajusta con la velocidad mediante la receta elegida. Cada capa sigue al propulsor (Sigue = true) mientras dura.
local function propulsor(
	paleta: string,
	tasa: number,
	velocidad: { number },
	vida: { number },
	tamano: { number },
	brillo: number
)
	local capas = {}
	for _, motor in { "MotorIzq", "MotorDer" } do
		-- Chorro de partículas hacia atrás.
		table.insert(
			capas,
			capa("Particulas", {
				Anclaje = motor,
				Sigue = true,
				Textura = "Fuego",
				Direccion = "Atras",
				Dispersion = 6,
				Tasa = tasa,
				Duracion = 0.3,
				Area = { 0.7, 0.7, 0.7 },
				Forma = "Sphere",
				Velocidad = velocidad,
				Vida = vida,
				Tamano = tamano,
				Transparencia = { 0.1, 1 },
				Color = { "Nucleo", "Principal", "Secundario", "Oscuro" },
				Brillo = 1,
				Aceleracion = SIN_GRAVEDAD,
			})
		)
		-- Chispas finas, para dar viveza.
		table.insert(
			capas,
			capa("Particulas", {
				Anclaje = motor,
				Sigue = true,
				Textura = "Chispa",
				Direccion = "Atras",
				Dispersion = 14,
				Tasa = tasa * 0.5,
				Duracion = 0.3,
				Velocidad = { velocidad[1] * 1.3, velocidad[2] * 1.6 },
				Vida = { vida[1], vida[2] * 1.2 },
				Tamano = { tamano[1] * 0.35, 0 },
				Color = { "Nucleo", "Principal" },
				Brillo = 1,
				Aceleracion = SIN_GRAVEDAD,
				Minimo = "Medio",
			})
		)
		-- Núcleo incandescente en la boca del propulsor. Del tamaño de la tobera (1,2 studs): los pulsos se
		-- solapan, así que uno mayor o más opaco se ve como una bola blanca que tapa la popa de la nave.
		table.insert(
			capas,
			esfera(
				motor,
				tamano[1] * 0.5,
				tamano[1] * 0.35,
				0.3,
				"Nucleo",
				{ Sigue = true, Transparencia = { 0.3, 0.75 } }
			)
		)
		-- Halo de color alrededor del núcleo.
		table.insert(
			capas,
			esfera(
				motor,
				tamano[1] * 1.15,
				tamano[1] * 0.8,
				0.3,
				"Principal",
				{ Sigue = true, Transparencia = { 0.78, 0.95 }, Minimo = "Medio" }
			)
		)
	end
	-- Un resplandor que ilumina el casco desde atrás.
	table.insert(
		capas,
		luz(
			"Lanzador",
			{ brillo, brillo * 0.7 },
			{ 14, 18 },
			0.3,
			"Principal",
			{ Sigue = true, Desplazamiento = { 0, 0, 3 } }
		)
	)
	return { Paleta = paleta, Fases = { Lanzamiento = capas } }
end

Recetas.Nave_Propulsor = propulsor("NavePropulsor", 70, { 14, 26 }, { 0.2, 0.36 }, { 2.2, 0 }, 2)
Recetas.Nave_Propulsor_Turbo = propulsor("NaveTurbo", 130, { 30, 60 }, { 0.3, 0.55 }, { 3.2, 0 }, 4)

--[[
	Al encender el turbo: la nave "da un tirón", con un anillo de energía, un fogonazo y una estela de chispas.

	Todo lo que va pegado a la nave la SIGUE y las ondas van tumbadas en el plano de las alas. Antes eran discos de
	30-40 studs de cara a la cámara y quietos en el mundo: la cámara, que persigue a la nave, se metía dentro y la
	pantalla entera se volvía rosa. (Sin malla de anillo en Recursos.Mallas.Anillo, una onda es un disco relleno.)
]]
Recetas.Nave_Turbo_Arranque = {
	Paleta = "NaveTurbo",
	Fases = {
		Lanzamiento = {
			esfera(
				"Lanzador",
				2,
				7,
				0.25,
				"Nucleo",
				{ Sigue = true, Desplazamiento = { 0, 0, 3 }, Transparencia = { 0.35, 1 } }
			),
			onda("Lanzador", 4, 26, 0.45, "Principal", {
				Sigue = true,
				Grosor = 0.2,
				Desplazamiento = { 0, 0, 2 },
				Transparencia = { 0.35, 1 },
			}),
			onda("Lanzador", 3, 18, 0.55, "Secundario", {
				Sigue = true,
				Grosor = 0.15,
				Desplazamiento = { 0, 0, 3 },
				Transparencia = { 0.45, 1 },
				Retraso = 0.06,
				Minimo = "Medio",
			}),
			luz("Lanzador", { 7, 0 }, { 14, 40 }, 0.5, "Principal"),
			chispas("Lanzador", 60, { 30, 100 }, { 0.3, 0.8 }, { "Nucleo", "Principal", "Secundario" }, {
				Desplazamiento = { 0, 0, 5 },
				Direccion = "Atras",
				Dispersion = 40,
				Aceleracion = SIN_GRAVEDAD,
				Tamano = { 1.1, 0 },
			}),
			capa("Sonido", { Sonido = "NaveTurbo", Volumen = 0.7, Anclaje = "Lanzador" }),
		},
	},
}

-- ===========================================================================================================
-- DESPEGUE
-- ===========================================================================================================

-- Las turbinas arrancan en el hangar: una onda de polvo en el suelo, llamarada y luz.
Recetas.Nave_Despegue = {
	Paleta = "NavePropulsor",
	Fases = {
		Lanzamiento = {
			onda("Suelo", 6, 70, 0.9, "Principal", { Grosor = 0.4, Transparencia = { 0.4, 1 } }),
			onda(
				"Suelo",
				4,
				48,
				1.1,
				"Nucleo",
				{ Grosor = 0.3, Transparencia = { 0.5, 1 }, Retraso = 0.08, Minimo = "Medio" }
			),
			luz("Suelo", { 8, 0 }, { 18, 70 }, 1.2, "Principal"),
			esfera("Suelo", 3, 24, 0.5, "Nucleo", { Desplazamiento = { 0, 4, 0 }, Transparencia = { 0.2, 1 } }),
			humo("Suelo", 40, { 7, 18 }, { 1.4, 2.8 }, {
				Direccion = "Esfera",
				Dispersion = 85,
				Velocidad = { 12, 38 },
				Color = "Oscuro",
				Transparencia = { 0.5, 1 },
				Aceleracion = { 0, 3, 0 },
			}),
			chispas("Suelo", 70, { 25, 90 }, { 0.4, 1.1 }, { "Nucleo", "Principal", "Secundario" }, {
				Desplazamiento = { 0, 1, 0 },
				Aceleracion = { 0, -20, 0 },
				Tamano = { 1.2, 0 },
			}),
			capa("Sacudida", { Intensidad = 0.9, Duracion = 0.9, Frecuencia = 18, Radio = 120, Para = "Todos" }),
			capa("Sonido", { Sonido = "NaveDespegue", Volumen = 0.9, Anclaje = "Suelo" }),
		},
	},
}

return Recetas
