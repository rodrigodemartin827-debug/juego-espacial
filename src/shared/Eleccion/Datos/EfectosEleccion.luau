--!strict
--[[
	EfectosEleccion: las RECETAS visuales de la pantalla de elección de bando.

	Mismo formato que las del combate (Combate/Datos/EfectosVFX) y las naves (Naves/Datos/EfectosNave), y las
	reproduce el mismo motor (client/VFX/Gestor.Reproducir). Los colores son nombres de Combate/Datos/Paleta; las
	texturas y sonidos, de Combate/Datos/Recursos.

	Anclas que usa la pantalla (las pone client/Eleccion/Escena al reproducir):
	  "Origen"    el centro de la grieta
	  "Objetivo"  el centro del planeta elegido (o el punto de un chispazo)
	La dirección del efecto apunta del planeta hacia la cámara: las ondas con Orientacion = "Frente" se ven de cara.

	Qué receta se usa en cada momento:
	  Eleccion_Anticipar_<Bando>   al hacer clic: el planeta "toma aire" (implosión) mientras responde el servidor
	  Eleccion_Confirmar_<Bando>   el servidor confirma: estallido de luz (o de oscuridad), ondas, rayos desde la
	                               grieta, destello de pantalla, temblor y zoom. Fases Impacto y Residuo.
	  Eleccion_Grieta_Chispazo     un rayo de energía que salta de la grieta de vez en cuando
	  Eleccion_Grieta_Resaltar_<Bando>  al resaltar un lado, la grieta escupe energía hacia él
]]

local Atajos = require(script.Parent.Parent.Parent.Combate.Datos.Atajos)

local capa, esfera, onda, chispas, humo, luz =
	Atajos.capa, Atajos.esfera, Atajos.onda, Atajos.chispas, Atajos.humo, Atajos.luz
local sacudida, tinte, arco = Atajos.sacudida, Atajos.tinte, Atajos.arco

-- En el espacio no hay gravedad: las chispas no caen.
local SIN_GRAVEDAD = { 0, 0, 0 }
-- Radio de las sacudidas: la cámara está a unos 80 studs del planeta y debe notarlas con fuerza.
local RADIO_SACUDIDA = 420

local Recetas = {}

-- ===========================================================================================================
-- ANTICIPACIÓN (al hacer clic, antes de que el servidor responda)
-- ===========================================================================================================

-- La energía se recoge hacia el planeta: una esfera y un anillo que se encogen, luz que sube y una sacudida leve.
local function anticipar(paleta: string)
	return {
		Paleta = paleta,
		Fases = {
			Anticipacion = {
				esfera("Objetivo", 62, 30, 0.16, "Principal", { Transparencia = { 0.85, 0.4 }, Easing = "Quad" }),
				onda("Objetivo", 90, 34, 0.16, "Secundario", {
					Orientacion = "Frente",
					Grosor = 0.6,
					Transparencia = { 0.7, 0.1 },
					Easing = "Quad",
				}),
				luz("Objetivo", { 0, 7 }, { 20, 60 }, 0.16, "Principal"),
				chispas("Objetivo", 40, { 6, 16 }, { 0.2, 0.4 }, { "Nucleo", "Principal" }, {
					Aceleracion = SIN_GRAVEDAD,
					Area = { 30, 30, 30 },
					Forma = "Sphere",
					Tamano = { 1.4, 0 },
					Minimo = "Medio",
				}),
				arco("Origen", { 0, 8, 0 }, "Objetivo", { 0, 0, 0 }, 0.16, { "Nucleo", "Principal" }, {
					Segmentos = 9,
					Desviacion = 3,
					Ancho = { 1.6, 0 },
				}),
				tinte(0.08, 0.1, 0.02, 0.15, "Principal", { Para = "Lanzador", Contraste = 0.15 }),
				sacudida(1.4, 0.18, { Radio = RADIO_SACUDIDA, Para = "Lanzador" }),
				capa("Zoom", { Delta = 3, Entrada = 0.12, Mantener = 0.02, Salida = 0.1, Para = "Lanzador" }),
				capa("Sonido", { Sonido = "EleccionAnticipar", Volumen = 0.7, Anclaje = "Objetivo" }),
			},
		},
	}
end

Recetas.Eleccion_Anticipar_Humanos = anticipar("EleccionHumanos")
Recetas.Eleccion_Anticipar_Monstruos = anticipar("EleccionMonstruos")

-- ===========================================================================================================
-- CONFIRMACIÓN (el servidor ha aceptado la elección)
-- ===========================================================================================================

-- Rayos que salen de la grieta y se clavan en el planeta elegido, a distintas alturas y escalonados.
local function rayosDesdeLaGrieta(): { any }
	local lista = {}
	local salidas = { { 0, 22, 0 }, { 0, -16, 0 }, { 0, 6, 0 }, { 0, -4, 0 }, { 0, 14, 0 } }
	for indice, desde in salidas do
		table.insert(
			lista,
			arco(
				"Origen",
				desde,
				"Objetivo",
				{ (indice - 3) * 2, (indice % 2) * 4 - 2, 0 },
				0.32,
				{ "Nucleo", "Principal", "Secundario" },
				{
					Segmentos = 10,
					Desviacion = 4.5,
					Ancho = { 2.4, 0 },
					Parpadeos = 5,
					Ramas = if indice <= 2 then 3 else 0,
					Retraso = (indice - 1) * 0.05,
					Minimo = if indice > 3 then "Alto" elseif indice > 2 then "Medio" else nil,
				}
			)
		)
	end
	return lista
end

-- Estallido común a los dos bandos. `extra` añade las capas propias de cada uno (luz dorada o humo negro).
local function confirmar(paleta: string, extraImpacto: { any }, extraResiduo: { any })
	local impacto: { any } = {
		-- Destello central en capas: núcleo blanco, color del bando y halo enorme.
		esfera("Objetivo", 30, 58, 0.22, "Nucleo", { Transparencia = { 0, 1 }, Easing = "Cubic" }),
		esfera("Objetivo", 34, 86, 0.5, "Principal", { Transparencia = { 0.35, 1 }, Easing = "Quart" }),
		esfera("Objetivo", 40, 120, 0.9, "Secundario", { Transparencia = { 0.75, 1 }, Easing = "Quint" }),
		-- Ondas de cara a la cámara, una tras otra.
		onda("Objetivo", 36, 150, 0.6, "Nucleo", {
			Orientacion = "Frente",
			Grosor = 0.5,
			Transparencia = { 0.05, 1 },
			Easing = "Quart",
		}),
		onda("Objetivo", 36, 190, 0.85, "Principal", {
			Orientacion = "Frente",
			Grosor = 0.9,
			Transparencia = { 0.3, 1 },
			Easing = "Quint",
			Retraso = 0.08,
		}),
		onda("Objetivo", 34, 230, 1.15, "Secundario", {
			Orientacion = "Frente",
			Grosor = 1.2,
			Transparencia = { 0.55, 1 },
			Easing = "Quint",
			Retraso = 0.18,
			Minimo = "Medio",
		}),
		-- Anillo inclinado (como un ecuador que se expande): da volumen al estallido.
		onda("Objetivo", 36, 120, 0.7, "Principal", {
			Orientacion = "Suelo",
			Grosor = 0.6,
			Transparencia = { 0.2, 1 },
			Giro = 140,
			Retraso = 0.04,
		}),
		-- Luz que inunda la escena y se apaga despacio.
		luz("Objetivo", { 14, 0 }, { 40, 60 }, 1.6, "Principal"),
		luz("Origen", { 8, 0 }, { 30, 60 }, 0.9, "Nucleo"),
		-- Chispas en todas direcciones, rápidas y lentas.
		chispas("Objetivo", 120, { 40, 120 }, { 0.5, 1.2 }, { "Nucleo", "Principal", "Secundario" }, {
			Aceleracion = SIN_GRAVEDAD,
			Arrastre = 1.5,
			Area = { 26, 26, 26 },
			Forma = "Sphere",
			Tamano = { 2.2, 0 },
		}),
		chispas("Objetivo", 60, { 10, 30 }, { 1.2, 2.2 }, { "Nucleo", "Principal" }, {
			Aceleracion = SIN_GRAVEDAD,
			Arrastre = 0.6,
			Area = { 34, 34, 34 },
			Forma = "Sphere",
			Tamano = { 1.2, 0.6, 0 },
			Retraso = 0.1,
			Minimo = "Medio",
		}),
		-- Pantalla: destello del color del bando, sacudida fuerte, zoom de impacto y un desenfoque breve.
		tinte(0.55, 0.04, 0.08, 0.7, "Principal", { Para = "Lanzador", Contraste = 0.25, Saturacion = 0.3 }),
		sacudida(7, 0.7, { Radio = RADIO_SACUDIDA, Para = "Lanzador" }),
		capa("Zoom", { Delta = -9, Entrada = 0.05, Mantener = 0.12, Salida = 0.9, Para = "Lanzador" }),
		capa("Desenfoque", { Tamano = 14, Entrada = 0.03, Mantener = 0.05, Salida = 0.45, Para = "Lanzador" }),
		capa("Sonido", { Sonido = "EleccionConfirmar", Volumen = 1, Anclaje = "Objetivo" }),
	}
	for _, capaRayo in rayosDesdeLaGrieta() do
		table.insert(impacto, capaRayo)
	end
	for _, capaExtra in extraImpacto do
		table.insert(impacto, capaExtra)
	end

	local residuo: { any } = {
		-- Motas que siguen flotando alrededor del planeta mientras llega el fundido.
		capa("Particulas", {
			Anclaje = "Objetivo",
			Textura = "Chispa",
			Tasa = 70,
			Duracion = 1.8,
			Direccion = "Esfera",
			Velocidad = { 4, 12 },
			Vida = { 1, 2 },
			Tamano = { 0, 1.1, 0 },
			Color = { "Nucleo", "Principal" },
			Aceleracion = SIN_GRAVEDAD,
			Area = { 40, 40, 40 },
			Forma = "Sphere",
			Retraso = 0.25,
		}),
		onda("Objetivo", 40, 70, 1.6, "Principal", {
			Orientacion = "Frente",
			Grosor = 0.3,
			Transparencia = { 0.6, 1 },
			Easing = "Sine",
			Retraso = 0.4,
		}),
		luz("Objetivo", { 4, 0 }, { 50, 60 }, 1.8, "Secundario", { Retraso = 0.5 }),
	}
	for _, capaExtra in extraResiduo do
		table.insert(residuo, capaExtra)
	end

	return { Paleta = paleta, Fases = { Impacto = impacto, Residuo = residuo } }
end

-- Humanos: un amanecer. Rayos de luz dorada que salen hacia arriba y un segundo destello cálido.
Recetas.Eleccion_Confirmar_Humanos = confirmar("EleccionHumanos", {
	chispas("Objetivo", 70, { 50, 110 }, { 0.6, 1.1 }, { "Nucleo", "Secundario" }, {
		Direccion = "Arriba",
		Dispersion = 40,
		Aceleracion = SIN_GRAVEDAD,
		Estirar = 2,
		Orientacion = "Velocidad",
		Tamano = { 2.6, 0 },
		Retraso = 0.06,
	}),
	esfera("Objetivo", 20, 70, 0.6, "Secundario", { Transparencia = { 0.4, 1 }, Retraso = 0.22, Easing = "Quart" }),
	tinte(0.25, 0.1, 0.1, 0.8, "Secundario", { Para = "Lanzador", Retraso = 0.2 }),
}, {})

-- Monstruos: la oscuridad se traga la luz. Humo negro que se abre en espiral y un latido rojo después del estallido.
Recetas.Eleccion_Confirmar_Monstruos = confirmar("EleccionMonstruos", {
	humo("Objetivo", 36, { 14, 34 }, { 1, 1.8 }, {
		Direccion = "Esfera",
		Velocidad = { 18, 42 },
		Aceleracion = SIN_GRAVEDAD,
		Area = { 20, 20, 20 },
		Forma = "Sphere",
		Transparencia = { 0.2, 1 },
		Retraso = 0.05,
	}),
	esfera("Objetivo", 70, 30, 0.35, "Oscuro", {
		Material = "Plastico",
		Transparencia = { 0.6, 1 },
		Retraso = 0.3,
		Easing = "Quad",
	}),
	esfera("Objetivo", 30, 95, 0.55, "Principal", { Transparencia = { 0.45, 1 }, Retraso = 0.62, Easing = "Quart" }),
	tinte(0.15, 0.05, 0.15, 0.6, "Oscuro", { Para = "Lanzador", Saturacion = -0.3, Retraso = 0.25 }),
	sacudida(3, 0.4, { Radio = RADIO_SACUDIDA, Para = "Lanzador", Retraso = 0.62 }),
}, {
	humo("Objetivo", 18, { 20, 40 }, { 1.5, 2.5 }, {
		Direccion = "Esfera",
		Velocidad = { 3, 8 },
		Aceleracion = SIN_GRAVEDAD,
		Area = { 36, 36, 36 },
		Forma = "Sphere",
		Retraso = 0.4,
		Minimo = "Medio",
	}),
})

-- ===========================================================================================================
-- LA GRIETA
-- ===========================================================================================================

-- Un rayo corto que salta desde un punto de la grieta (Origen) hasta otro cercano (Objetivo), con chispas.
Recetas.Eleccion_Grieta_Chispazo = {
	Paleta = "EleccionGrieta",
	Fases = {
		Impacto = {
			arco("Origen", { 0, 0, 0 }, "Objetivo", { 0, 0, 0 }, 0.22, { "Nucleo", "Principal", "Secundario" }, {
				Segmentos = 7,
				Desviacion = 1.8,
				Ancho = { 1, 0 },
				Parpadeos = 3,
				Ramas = 1,
			}),
			esfera("Objetivo", 0.5, 3.5, 0.22, "Nucleo", { Transparencia = { 0.1, 1 } }),
			chispas("Objetivo", 14, { 8, 24 }, { 0.2, 0.5 }, { "Nucleo", "Principal" }, {
				Aceleracion = SIN_GRAVEDAD,
				Tamano = { 0.8, 0 },
				Minimo = "Medio",
			}),
			luz("Objetivo", { 3, 0 }, { 12, 22 }, 0.25, "Principal"),
		},
	},
}

-- Al resaltar un lado, la grieta lanza energía hacia ese planeta: un aviso de "esto es lo que vas a elegir".
local function resaltar(paleta: string)
	return {
		Paleta = paleta,
		Fases = {
			Impacto = {
				arco("Origen", { 0, 10, 0 }, "Objetivo", { 0, 4, 0 }, 0.2, { "Nucleo", "Principal" }, {
					Segmentos = 9,
					Desviacion = 3.5,
					Ancho = { 1.1, 0 },
					Parpadeos = 3,
				}),
				arco("Origen", { 0, -12, 0 }, "Objetivo", { 0, -5, 0 }, 0.2, { "Nucleo", "Secundario" }, {
					Segmentos = 9,
					Desviacion = 3.5,
					Ancho = { 0.9, 0 },
					Parpadeos = 3,
					Retraso = 0.06,
					Minimo = "Medio",
				}),
				onda("Objetivo", 34, 52, 0.45, "Principal", {
					Orientacion = "Frente",
					Grosor = 0.3,
					Transparencia = { 0.5, 1 },
				}),
				luz("Objetivo", { 4, 0 }, { 30, 50 }, 0.4, "Principal"),
				capa("Sonido", { Sonido = "EleccionResaltar", Volumen = 0.4, Anclaje = "Objetivo" }),
			},
		},
	}
end

Recetas.Eleccion_Grieta_Resaltar_Humanos = resaltar("EleccionHumanos")
Recetas.Eleccion_Grieta_Resaltar_Monstruos = resaltar("EleccionMonstruos")

return Recetas
