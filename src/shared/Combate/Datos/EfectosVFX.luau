--!strict
--[[
	EfectosVFX: las RECETAS visuales de cada habilidad. Aquí se cambian colores, tamaños, tiempos y cantidades
	sin tocar código. (Para cambiar texturas, mallas, animaciones o sonidos: Datos/Recursos.)

	Una receta tiene:
	  Paleta        nombre de Datos/Paleta con los colores del efecto
	  Hitstop       segundos que se congelan las animaciones al golpear a alguien (opcional)
	  AlturaCielo   a qué altura sobre el impacto está "Cielo" (140 por defecto)
	  Fases         Anticipacion, Lanzamiento, Impacto, Residuo y Golpeado (todas opcionales). Cada una es una lista de
	                CAPAS que arrancan a la vez, cada una con su `Retraso` en segundos.

	Fases:
	  Anticipacion  desde que el servidor acepta la habilidad (carga, aura, avisos)
	  Lanzamiento   al terminar la carga (proyectil, rayo, onda de salida)
	  Impacto       cuando el servidor confirma el golpe (explosión, ondas, escombros, cráter, pantalla)
	  Residuo       justo después del impacto (humo, brasas, luz que se apaga)
	  Golpeado      una vez por cada enemigo alcanzado (destello, chispas, pantalla del golpeado)

	Tipos de capa y sus campos: ver los comentarios de los módulos de client/VFX/Capas:
	  Particulas (Capas/Particulas), Onda | Esfera | Luz (Capas/Formas), Proyectil | Corte (Capas/Movimiento),
	  Haz (Capas/Haz), Escombros | Crater (Capas/Terreno), y de pantalla (VFX/Pantalla): Tinte, Desenfoque, Zoom,
	  Sacudida, Hitstop; además Sonido.

	Campos comunes: Anclaje ("Lanzador" | "Mano" | "Origen" | "Objetivo" | "Suelo" | "Cielo" | "Victima"),
	Desplazamiento { x, y, z } (z negativa = hacia delante), Retraso, Minimo ("Medio" | "Alto": la capa se omite en
	dispositivos más lentos), Para (solo pantalla: "Lanzador" | "Golpeados" | "Implicados" | "Todos").

	Los colores son nombres de la paleta ("Nucleo", "Principal", "Secundario", "Oscuro") u hexadecimales.
]]

-- ===== Atajos para no repetir campos (solo construyen tablas de datos) =====

local function capa(tipo: string, campos: { [string]: any }): { [string]: any }
	campos.Tipo = tipo
	return campos
end

-- Destello esférico que crece (o se encoge) y se desvanece.
local function esfera(ancla: string, d0: number, d1: number, duracion: number, color: string, extra: { [string]: any }?)
	local campos: { [string]: any } =
		{ Anclaje = ancla, Diametro = { d0, d1 }, Duracion = duracion, Color = color, Transparencia = { 0.05, 1 } }
	for clave, valor in extra or {} do
		campos[clave] = valor
	end
	return capa("Esfera", campos)
end

-- Onda expansiva tumbada en el suelo.
local function onda(ancla: string, d0: number, d1: number, duracion: number, color: string, extra: { [string]: any }?)
	local campos: { [string]: any } = {
		Anclaje = ancla,
		Diametro = { d0, d1 },
		Duracion = duracion,
		Color = color,
		Transparencia = { 0.15, 1 },
		Grosor = 0.35,
	}
	for clave, valor in extra or {} do
		campos[clave] = valor
	end
	return capa("Onda", campos)
end

-- Estallido de chispas luminosas.
local function chispas(
	ancla: string,
	cantidad: number,
	velocidad: { number },
	vida: { number },
	color: any,
	extra: { [string]: any }?
)
	local campos: { [string]: any } = {
		Anclaje = ancla,
		Textura = "Chispa",
		Cantidad = cantidad,
		Direccion = "Esfera",
		Velocidad = velocidad,
		Vida = vida,
		Tamano = { 1.1, 0 },
		Color = color,
		Aceleracion = { 0, -45, 0 },
	}
	for clave, valor in extra or {} do
		campos[clave] = valor
	end
	return capa("Particulas", campos)
end

-- Nube de humo / polvo (no brilla, se ve oscura).
local function humo(ancla: string, cantidad: number, tamano: { number }, vida: { number }, extra: { [string]: any }?)
	local campos: { [string]: any } = {
		Anclaje = ancla,
		Textura = "Humo",
		Cantidad = cantidad,
		Direccion = "Arriba",
		Dispersion = 70,
		Velocidad = { 6, 18 },
		Vida = vida,
		Tamano = tamano,
		Transparencia = { 0.45, 1 },
		Color = "Oscuro",
		Brillo = 0,
		Rotacion = { 0, 360 },
		VelRotacion = { -40, 40 },
		Arrastre = 2,
	}
	for clave, valor in extra or {} do
		campos[clave] = valor
	end
	return capa("Particulas", campos)
end

local function luz(
	ancla: string,
	brillo: { number },
	rango: { number },
	duracion: number,
	color: string,
	extra: { [string]: any }?
)
	local campos: { [string]: any } =
		{ Anclaje = ancla, Brillo = brillo, Rango = rango, Duracion = duracion, Color = color }
	for clave, valor in extra or {} do
		campos[clave] = valor
	end
	return capa("Luz", campos)
end

local function sacudida(intensidad: number, duracion: number, extra: { [string]: any }?)
	local campos: { [string]: any } = { Intensidad = intensidad, Duracion = duracion, Frecuencia = 22, Radio = 150 }
	for clave, valor in extra or {} do
		campos[clave] = valor
	end
	return capa("Sacudida", campos)
end

-- Destello o tinte de pantalla.
local function tinte(
	brillo: number,
	entrada: number,
	mantener: number,
	salida: number,
	color: string,
	extra: { [string]: any }?
)
	local campos: { [string]: any } =
		{ Brillo = brillo, Entrada = entrada, Mantener = mantener, Salida = salida, Color = color }
	for clave, valor in extra or {} do
		campos[clave] = valor
	end
	return capa("Tinte", campos)
end

-- Rayo corto y quebrado entre dos anclas (arcos eléctricos, grietas de energía).
local function arco(
	desde: string,
	dd: { number },
	hasta: string,
	dh: { number },
	duracion: number,
	color: any,
	extra: { [string]: any }?
)
	local campos: { [string]: any } = {
		Desde = desde,
		DesplazamientoDesde = dd,
		Hasta = hasta,
		DesplazamientoHasta = dh,
		Segmentos = 7,
		Desviacion = 1.6,
		Ancho = { 0.9, 0 },
		Duracion = duracion,
		Parpadeos = 4,
		Color = color,
	}
	for clave, valor in extra or {} do
		campos[clave] = valor
	end
	return capa("Haz", campos)
end

-- Arcos eléctricos que se reparten radialmente desde un punto del suelo (`radio` studs), con retrasos escalonados.
local function arcosRadiales(
	ancla: string,
	cantidad: number,
	radio: number,
	color: any,
	retrasoBase: number,
	extra: { [string]: any }?
)
	local lista = {}
	for indice = 1, cantidad do
		local angulo = (indice / cantidad) * math.pi * 2 + 0.4
		local extraCapa: { [string]: any } = { Retraso = retrasoBase + (indice % 3) * 0.05 }
		for clave, valor in extra or {} do
			extraCapa[clave] = valor
		end
		table.insert(
			lista,
			arco(
				ancla,
				{ 0, 0.6, 0 },
				ancla,
				{ math.cos(angulo) * radio, 0.4, math.sin(angulo) * radio },
				0.34,
				color,
				extraCapa
			)
		)
	end
	return lista
end

-- Une listas de capas en una sola (para construir fases a partir de varios atajos).
local function juntar(...: { any }): { any }
	local resultado = {}
	for _, lista in { ... } do
		for _, elemento in lista do
			table.insert(resultado, elemento)
		end
	end
	return resultado
end

-- Carga de energía en la mano: núcleo brillante, halo, partículas que convergen y una luz que crece.
local function cargaEnMano(duracion: number, escala: number)
	return {
		esfera(
			"Mano",
			0.2,
			2.2 * escala,
			duracion,
			"Nucleo",
			{ Sigue = true, Transparencia = { 0.2, 0.35 }, Easing = "Cubic" }
		),
		esfera(
			"Mano",
			0.5,
			4.8 * escala,
			duracion,
			"Principal",
			{ Sigue = true, Transparencia = { 0.7, 0.8 }, Easing = "Cubic" }
		),
		capa("Particulas", {
			Anclaje = "Mano",
			Sigue = true,
			Textura = "Chispa",
			Tasa = 110,
			Duracion = duracion,
			Area = { 6, 6, 6 },
			Forma = "Sphere",
			Velocidad = { -9, -5 },
			Vida = { 0.2, 0.32 },
			Tamano = { 0.7, 0 },
			Color = { "Nucleo", "Principal" },
		}),
		luz("Mano", { 0, 4 }, { 4, 15 }, duracion, "Principal", { Sigue = true }),
	}
end

local Recetas = {}

-- ===========================================================================================================
-- RAYO
-- ===========================================================================================================

Recetas.Rayo_Basico = {
	Paleta = "Rayo",
	Hitstop = 0.05,
	Fases = {
		Anticipacion = juntar(cargaEnMano(0.28, 1), {
			arco(
				"Mano",
				{ 0, 0, 0 },
				"Mano",
				{ 1.8, 1.2, -1.6 },
				0.1,
				{ "Nucleo", "Principal" },
				{ Segmentos = 4, Desviacion = 0.5, Retraso = 0.04 }
			),
			arco(
				"Mano",
				{ 0, 0, 0 },
				"Mano",
				{ -1.6, -0.8, -1.9 },
				0.1,
				{ "Nucleo", "Secundario" },
				{ Segmentos = 4, Desviacion = 0.5, Retraso = 0.12 }
			),
			arco(
				"Mano",
				{ 0, 0, 0 },
				"Mano",
				{ 0.4, 1.9, -1.4 },
				0.1,
				{ "Nucleo", "Principal" },
				{ Segmentos = 4, Desviacion = 0.5, Retraso = 0.2 }
			),
		}),
		Lanzamiento = {
			capa("Proyectil", {
				Desde = "Mano",
				Hasta = "Objetivo",
				Duracion = "Viaje",
				Diametro = 1.8,
				Color = "Principal",
				ColorNucleo = "Nucleo",
				Halo = 2.6,
				Estela = { Ancho = 2.4, Vida = 0.28 },
				Chispas = 140,
				Luz = 3,
			}),
			-- Corriente de rayo: halo de color + núcleo blanco (mismo Grupo = mismo zigzag).
			capa("Haz", {
				Desde = "Mano",
				Hasta = "Objetivo",
				Segmentos = 10,
				Desviacion = 2.2,
				Ancho = { 2, 0 },
				Color = { "Principal", "Secundario" },
				Duracion = 0.24,
				Parpadeos = 5,
				Ramas = 3,
				Grupo = "A",
			}),
			capa("Haz", {
				Desde = "Mano",
				Hasta = "Objetivo",
				Segmentos = 10,
				Desviacion = 2.2,
				Ancho = { 0.7, 0 },
				Color = "Nucleo",
				Duracion = 0.24,
				Parpadeos = 5,
				Ramas = 3,
				Grupo = "A",
			}),
			onda(
				"Mano",
				1,
				9,
				0.22,
				"Principal",
				{ Orientacion = "Frente", Grosor = 0.2, Desplazamiento = { 0, 0, -1 } }
			),
			capa("Particulas", {
				Anclaje = "Mano",
				Direccion = "Frente",
				Textura = "Chispa",
				Cantidad = 30,
				Velocidad = { 22, 50 },
				Dispersion = 22,
				Vida = { 0.2, 0.45 },
				Tamano = { 0.7, 0 },
				Color = { "Nucleo", "Principal" },
			}),
			luz("Mano", { 5, 0 }, { 12, 18 }, 0.25, "Principal"),
			capa("Zoom", { Delta = -3, Entrada = 0.03, Mantener = 0.02, Salida = 0.25, Para = "Lanzador" }),
			capa("Sonido", { Sonido = "DisparoRayo", Anclaje = "Mano" }),
		},
		Impacto = {
			esfera("Objetivo", 2, 9, 0.18, "Nucleo"),
			esfera("Objetivo", 3, 14, 0.3, "Principal", { Transparencia = { 0.45, 1 } }),
			onda("Suelo", 2, 20, 0.38, "Principal"),
			onda("Suelo", 1, 13, 0.26, "Nucleo", { Retraso = 0.04, Grosor = 0.2 }),
			chispas("Objetivo", 46, { 18, 52 }, { 0.3, 0.75 }, { "Nucleo", "Principal" }),
			humo("Suelo", 9, { 3, 9 }, { 0.6, 1.1 }, { Velocidad = { 3, 9 } }),
			capa("Escombros", {
				Anclaje = "Suelo",
				Cantidad = 9,
				Radio = 3,
				Tamano = { 0.4, 0.9 },
				Impulso = { 14, 26 },
				Dispersion = { 3, 8 },
				Vida = 1.2,
				Emerge = true,
				Color = "Oscuro",
			}),
			luz("Objetivo", { 8, 0 }, { 10, 26 }, 0.32, "Principal"),
			arco(
				"Objetivo",
				{ 0, 0.5, 0 },
				"Objetivo",
				{ 3.5, 0.3, 2 },
				0.2,
				{ "Nucleo", "Principal" },
				{ Segmentos = 5 }
			),
			arco(
				"Objetivo",
				{ 0, 0.5, 0 },
				"Objetivo",
				{ -3, 0.3, -2.6 },
				0.2,
				{ "Nucleo", "Principal" },
				{ Segmentos = 5, Retraso = 0.05 }
			),
			sacudida(2.2, 0.25, { Radio = 90 }),
			capa("Sonido", { Sonido = "ImpactoRayo", Anclaje = "Objetivo" }),
		},
		Residuo = {
			capa("Particulas", {
				Anclaje = "Suelo",
				Textura = "Chispa",
				Tasa = 42,
				Duracion = 0.5,
				Area = { 5, 0.5, 5 },
				Forma = "Disc",
				Direccion = "Arriba",
				Dispersion = 40,
				Velocidad = { 4, 12 },
				Vida = { 0.4, 0.8 },
				Tamano = { 0.5, 0 },
				Color = { "Nucleo", "Principal" },
				Aceleracion = { 0, -20, 0 },
			}),
			capa(
				"Crater",
				{ Anclaje = "Suelo", Radio = 3.2, Duracion = 1.6, Desvanecer = 0.8, Grietas = 4, Rocas = 0 }
			),
		},
		Golpeado = {
			esfera("Victima", 1.5, 7, 0.16, "Nucleo"),
			chispas("Victima", 24, { 14, 36 }, { 0.25, 0.55 }, { "Nucleo", "Principal" }),
			tinte(0.25, 0.01, 0.03, 0.22, "Principal", { Para = "Golpeados" }),
			sacudida(3, 0.3, { Para = "Golpeados" }),
		},
	},
}

Recetas.Rayo_Fuerte = {
	Paleta = "Rayo",
	Hitstop = 0.09,
	AlturaCielo = 120,
	Fases = {
		Anticipacion = juntar(cargaEnMano(0.75, 1.5), {
			-- Aviso en el suelo: un círculo que se cierra sobre la zona de impacto.
			onda("Suelo", 34, 6, 0.75, "Principal", { Transparencia = { 0.7, 0.25 }, Grosor = 0.25 }),
			onda("Suelo", 6, 29, 0.55, "Secundario", { Transparencia = { 0.7, 0.4 }, Grosor = 0.2 }),
			capa("Particulas", {
				Anclaje = "Suelo",
				Tasa = 70,
				Duracion = 0.75,
				Textura = "Chispa",
				Area = { 24, 0.5, 24 },
				Forma = "Disc",
				Direccion = "Arriba",
				Velocidad = { 6, 16 },
				Vida = { 0.5, 0.9 },
				Tamano = { 0.7, 0 },
				Color = { "Nucleo", "Principal" },
			}),
			luz("Cielo", { 0, 3.5 }, { 30, 60 }, 0.75, "Principal", { Desplazamiento = { 0, -60, 0 } }),
			tinte(-0.1, 0.35, 0.3, 0.3, "#9DB5FF", { Contraste = 0.1, Saturacion = -0.2, Para = "Implicados" }),
			sacudida(1, 0.7, { Radio = 90 }),
			capa("Sonido", { Sonido = "CargaRayo", Anclaje = "Lanzador" }),
		}),
		Lanzamiento = {
			-- El rayo cae del cielo: halo exterior, cuerpo de color y núcleo blanco con el mismo zigzag.
			capa("Haz", {
				Desde = "Cielo",
				Hasta = "Suelo",
				Segmentos = 12,
				Desviacion = 6,
				Ancho = { 11, 0 },
				Color = "Secundario",
				Duracion = 0.55,
				Parpadeos = 7,
				Ramas = 5,
				Grupo = "B",
				Brillo = 0.8,
			}),
			capa("Haz", {
				Desde = "Cielo",
				Hasta = "Suelo",
				Segmentos = 12,
				Desviacion = 6,
				Ancho = { 5, 0 },
				Color = { "Principal", "Nucleo" },
				Duracion = 0.55,
				Parpadeos = 7,
				Ramas = 5,
				Grupo = "B",
			}),
			capa("Haz", {
				Desde = "Cielo",
				Hasta = "Suelo",
				Segmentos = 12,
				Desviacion = 6,
				Ancho = { 1.8, 0 },
				Color = "Nucleo",
				Duracion = 0.55,
				Parpadeos = 7,
				Ramas = 5,
				Grupo = "B",
			}),
			tinte(0.5, 0.02, 0.04, 0.3, "Nucleo", { Para = "Implicados", Retraso = 0.08 }),
			luz("Suelo", { 10, 0 }, { 30, 60 }, 0.6, "Nucleo", { Desplazamiento = { 0, 18, 0 }, Retraso = 0.08 }),
		},
		Impacto = juntar({
			esfera("Suelo", 6, 30, 0.22, "Nucleo", { Desplazamiento = { 0, 2, 0 } }),
			esfera("Suelo", 10, 26, 0.4, "Secundario", { Desplazamiento = { 0, 2, 0 }, Transparencia = { 0.4, 1 } }),
			onda("Suelo", 4, 46, 0.55, "Principal"),
			onda("Suelo", 2, 32, 0.36, "Nucleo", { Grosor = 0.25 }),
			onda("Suelo", 6, 62, 0.85, "Secundario", { Retraso = 0.08, Transparencia = { 0.55, 1 } }),
			chispas(
				"Suelo",
				90,
				{ 30, 80 },
				{ 0.4, 0.9 },
				{ "Nucleo", "Principal" },
				{ Tamano = { 1.5, 0 }, Aceleracion = { 0, -90, 0 }, Desplazamiento = { 0, 1, 0 } }
			),
			capa("Particulas", {
				Anclaje = "Suelo",
				Textura = "Chispa",
				Cantidad = 60,
				Direccion = "Arriba",
				Dispersion = 12,
				Velocidad = { 50, 95 },
				Vida = { 0.5, 1.1 },
				Tamano = { 1.8, 0 },
				Color = { "Nucleo", "Principal", "Secundario" },
				Aceleracion = { 0, -40, 0 },
			}),
			humo("Suelo", 30, { 6, 17 }, { 1, 2 }, { Area = { 20, 1, 20 }, Forma = "Disc", Velocidad = { 10, 26 } }),
			capa("Escombros", {
				Anclaje = "Suelo",
				Cantidad = 28,
				RadioMin = 3,
				Radio = 13,
				Tamano = { 0.8, 2.6 },
				Impulso = { 26, 52 },
				Dispersion = { 4, 14 },
				Vida = 2.2,
				Emerge = true,
				Giro = 5,
				Color = "Oscuro",
			}),
			capa("Escombros", {
				Anclaje = "Suelo",
				Cantidad = 12,
				RadioMin = 2,
				Radio = 9,
				Tamano = { 0.4, 0.9 },
				Impulso = { 30, 60 },
				Dispersion = { 4, 12 },
				Vida = 1.6,
				Neon = true,
				Color = "Principal",
			}),
			capa("Crater", { Anclaje = "Suelo", Radio = 11, Duracion = 6, Desvanecer = 1.5, Grietas = 12, Rocas = 14 }),
			luz("Suelo", { 14, 0 }, { 24, 60 }, 0.65, "Principal", { Desplazamiento = { 0, 3, 0 } }),
			sacudida(7, 0.7, { Frecuencia = 24, Radio = 150 }),
			capa("Desenfoque", { Tamano = 14, Entrada = 0.02, Mantener = 0.03, Salida = 0.35 }),
			tinte(0.55, 0.01, 0.05, 0.5, "Nucleo"),
			tinte(0, 0.05, 0.12, 0.6, "#8FA8FF", { Contraste = 0.25, Saturacion = -0.35, Retraso = 0.1 }),
			capa("Zoom", { Delta = -7, Entrada = 0.03, Mantener = 0.05, Salida = 0.4 }),
			capa("Sonido", { Sonido = "TruenoDefinitiva", Anclaje = "Suelo", Volumen = 0.7 }),
		}, arcosRadiales("Suelo", 6, 9, { "Nucleo", "Principal" }, 0.02)),
		Residuo = {
			capa("Particulas", {
				Anclaje = "Suelo",
				Textura = "Chispa",
				Tasa = 55,
				Duracion = 1.4,
				Area = { 16, 0.5, 16 },
				Forma = "Disc",
				Direccion = "Arriba",
				Velocidad = { 2, 8 },
				Vida = { 0.6, 1.2 },
				Tamano = { 0.6, 0 },
				Color = { "Nucleo", "Principal" },
				Aceleracion = { 0, 10, 0 },
			}),
			humo(
				"Suelo",
				0,
				{ 5, 11 },
				{ 1.4, 2.2 },
				{ Tasa = 12, Duracion = 2, Area = { 8, 1, 8 }, Forma = "Disc", Velocidad = { 4, 9 }, Retraso = 0.2 }
			),
			luz("Suelo", { 3, 0 }, { 12, 16 }, 1.6, "Principal", { Desplazamiento = { 0, 2, 0 }, Retraso = 0.4 }),
			arco("Suelo", { -4, 0.3, 2 }, "Suelo", { 3, 0.3, -4 }, 0.25, { "Nucleo", "Principal" }, { Retraso = 0.45 }),
			arco("Suelo", { 5, 0.3, 3 }, "Suelo", { -2, 0.3, -5 }, 0.25, { "Nucleo", "Principal" }, { Retraso = 0.8 }),
			arco("Suelo", { -3, 0.3, -4 }, "Suelo", { 4, 0.3, 3 }, 0.25, { "Nucleo", "Principal" }, { Retraso = 1.1 }),
		},
		Golpeado = {
			esfera("Victima", 2, 10, 0.2, "Nucleo"),
			chispas("Victima", 40, { 18, 46 }, { 0.3, 0.7 }, { "Nucleo", "Principal" }),
			tinte(0.35, 0.01, 0.05, 0.35, "Nucleo", { Para = "Golpeados" }),
			sacudida(6, 0.5, { Para = "Golpeados" }),
			capa("Zoom", { Delta = -6, Entrada = 0.02, Mantener = 0.04, Salida = 0.3, Para = "Golpeados" }),
		},
	},
}

Recetas.Rayo_Definitiva = {
	Paleta = "Rayo",
	Hitstop = 0.14,
	AlturaCielo = 150,
	Fases = {
		Anticipacion = juntar({
			-- Aura del lanzador y círculo de poder en el suelo que pulsa hacia fuera.
			esfera(
				"Lanzador",
				3,
				7,
				2.7,
				"Principal",
				{ Sigue = true, Transparencia = { 0.75, 0.6 }, Easing = "Sine" }
			),
			esfera("Lanzador", 1, 3.5, 2.7, "Nucleo", { Sigue = true, Transparencia = { 0.6, 0.4 }, Easing = "Sine" }),
			luz("Lanzador", { 0, 6 }, { 10, 40 }, 2.7, "Principal", { Sigue = true }),
			capa("Particulas", {
				Anclaje = "Lanzador",
				Desplazamiento = { 0, -3, 0 },
				Sigue = true,
				Textura = "Chispa",
				Tasa = 130,
				Duracion = 2.8,
				Area = { 11, 0.5, 11 },
				Forma = "Disc",
				Direccion = "Arriba",
				Velocidad = { 8, 22 },
				Vida = { 0.8, 1.4 },
				Tamano = { 0.9, 0 },
				Color = { "Nucleo", "Principal" },
				Aceleracion = { 0, 14, 0 },
			}),
			capa("Escombros", {
				Anclaje = "Lanzador",
				Desplazamiento = { 0, -3, 0 },
				Cantidad = 18,
				RadioMin = 3,
				Radio = 9,
				Tamano = { 0.5, 1.4 },
				Impulso = { 10, 20 },
				Dispersion = { 0, 2 },
				Gravedad = 0.05,
				Vida = 2.8,
				Emerge = true,
				Color = "Oscuro",
			}),
			-- Aviso de la zona de impacto.
			onda("Suelo", 70, 10, 2.6, "Principal", { Transparencia = { 0.8, 0.3 }, Grosor = 0.3 }),
			onda("Suelo", 12, 62, 1.0, "Secundario", { Transparencia = { 0.8, 0.5 }, Retraso = 0.4, Grosor = 0.25 }),
			onda("Suelo", 12, 62, 1.0, "Secundario", { Transparencia = { 0.8, 0.5 }, Retraso = 1.5, Grosor = 0.25 }),
			-- Tormenta en el cielo.
			capa("Particulas", {
				Anclaje = "Cielo",
				Desplazamiento = { 0, -22, 0 },
				Textura = "Humo",
				Tasa = 45,
				Duracion = 2.8,
				Area = { 90, 8, 90 },
				Forma = "Disc",
				Color = { "Oscuro", "Secundario", "Oscuro" },
				Tamano = { 36, 56 },
				Transparencia = { 1, 0.45, 1 },
				Brillo = 0.15,
				Velocidad = { 1, 5 },
				Vida = { 2.4, 3.2 },
				Direccion = "Arriba",
				Dispersion = 180,
				Minimo = "Medio",
			}),
			luz("Cielo", { 0, 5 }, { 30, 60 }, 2.8, "Secundario", { Desplazamiento = { 0, -60, 0 } }),
			tinte(-0.16, 0.6, 2.0, 0.5, "#8FA8FF", { Contraste = 0.18, Saturacion = -0.4, Para = "Implicados" }),
			tinte(0.35, 0.01, 0.03, 0.22, "Nucleo", { Retraso = 1.2, Para = "Implicados" }),
			tinte(0.35, 0.01, 0.03, 0.22, "Nucleo", { Retraso = 1.9, Para = "Implicados" }),
			tinte(0.4, 0.01, 0.03, 0.25, "Nucleo", { Retraso = 2.4, Para = "Implicados" }),
			sacudida(1.8, 2.7, { Radio = 170 }),
			capa("Sonido", { Sonido = "CargaRayo", Anclaje = "Lanzador", Volumen = 1 }),
		}, {
			-- Rayos sueltos que caen alrededor mientras se acumula la tormenta (cada vez más seguidos).
			capa("Haz", {
				Desde = "Cielo",
				DesplazamientoDesde = { 14, -20, 6 },
				Hasta = "Suelo",
				DesplazamientoHasta = { 13, 0, 6 },
				Segmentos = 12,
				Desviacion = 5,
				Ancho = { 2.6, 0 },
				Color = { "Nucleo", "Principal" },
				Duracion = 0.35,
				Parpadeos = 3,
				Ramas = 2,
				Retraso = 0.9,
			}),
			capa("Haz", {
				Desde = "Cielo",
				DesplazamientoDesde = { -18, -20, -4 },
				Hasta = "Suelo",
				DesplazamientoHasta = { -17, 0, -4 },
				Segmentos = 12,
				Desviacion = 5,
				Ancho = { 2.6, 0 },
				Color = { "Nucleo", "Principal" },
				Duracion = 0.35,
				Parpadeos = 3,
				Ramas = 2,
				Retraso = 1.3,
			}),
			capa("Haz", {
				Desde = "Cielo",
				DesplazamientoDesde = { 4, -20, -22 },
				Hasta = "Suelo",
				DesplazamientoHasta = { 4, 0, -21 },
				Segmentos = 12,
				Desviacion = 5,
				Ancho = { 2.6, 0 },
				Color = { "Nucleo", "Principal" },
				Duracion = 0.35,
				Parpadeos = 3,
				Ramas = 2,
				Retraso = 1.6,
			}),
			capa("Haz", {
				Desde = "Cielo",
				DesplazamientoDesde = { -8, -20, 20 },
				Hasta = "Suelo",
				DesplazamientoHasta = { -8, 0, 19 },
				Segmentos = 12,
				Desviacion = 5,
				Ancho = { 2.6, 0 },
				Color = { "Nucleo", "Principal" },
				Duracion = 0.35,
				Parpadeos = 3,
				Ramas = 2,
				Retraso = 1.85,
			}),
			capa("Haz", {
				Desde = "Cielo",
				DesplazamientoDesde = { 24, -20, -10 },
				Hasta = "Suelo",
				DesplazamientoHasta = { 23, 0, -10 },
				Segmentos = 12,
				Desviacion = 5,
				Ancho = { 2.6, 0 },
				Color = { "Nucleo", "Principal" },
				Duracion = 0.35,
				Parpadeos = 3,
				Ramas = 2,
				Retraso = 2.1,
			}),
			capa("Haz", {
				Desde = "Cielo",
				DesplazamientoDesde = { -24, -20, -12 },
				Hasta = "Suelo",
				DesplazamientoHasta = { -23, 0, -12 },
				Segmentos = 12,
				Desviacion = 5,
				Ancho = { 2.6, 0 },
				Color = { "Nucleo", "Principal" },
				Duracion = 0.35,
				Parpadeos = 3,
				Ramas = 2,
				Retraso = 2.3,
			}),
			capa("Haz", {
				Desde = "Cielo",
				DesplazamientoDesde = { 8, -20, 12 },
				Hasta = "Suelo",
				DesplazamientoHasta = { 8, 0, 12 },
				Segmentos = 12,
				Desviacion = 5,
				Ancho = { 2.6, 0 },
				Color = { "Nucleo", "Principal" },
				Duracion = 0.35,
				Parpadeos = 3,
				Ramas = 2,
				Retraso = 2.45,
			}),
			capa("Haz", {
				Desde = "Cielo",
				DesplazamientoDesde = { -2, -20, -2 },
				Hasta = "Suelo",
				DesplazamientoHasta = { -2, 0, -2 },
				Segmentos = 12,
				Desviacion = 5,
				Ancho = { 2.6, 0 },
				Color = { "Nucleo", "Principal" },
				Duracion = 0.35,
				Parpadeos = 3,
				Ramas = 2,
				Retraso = 2.6,
			}),
		}),
		Lanzamiento = {
			-- La columna de rayo definitiva: halo enorme, cuerpo de color y núcleo blanco.
			capa("Haz", {
				Desde = "Cielo",
				Hasta = "Suelo",
				Segmentos = 12,
				Desviacion = 9,
				Ancho = { 24, 0 },
				Color = "Secundario",
				Duracion = 0.95,
				Parpadeos = 9,
				Ramas = 8,
				Grupo = "C",
				Brillo = 0.7,
			}),
			capa("Haz", {
				Desde = "Cielo",
				Hasta = "Suelo",
				Segmentos = 12,
				Desviacion = 9,
				Ancho = { 11, 0 },
				Color = { "Principal", "Nucleo" },
				Duracion = 0.95,
				Parpadeos = 9,
				Ramas = 8,
				Grupo = "C",
			}),
			capa("Haz", {
				Desde = "Cielo",
				Hasta = "Suelo",
				Segmentos = 12,
				Desviacion = 9,
				Ancho = { 4, 0 },
				Color = "Nucleo",
				Duracion = 0.95,
				Parpadeos = 9,
				Ramas = 8,
				Grupo = "C",
			}),
			esfera("Mano", 1, 6, 0.3, "Nucleo"),
			onda("Lanzador", 3, 30, 0.45, "Principal", { Desplazamiento = { 0, -2.8, 0 } }),
			tinte(0.9, 0.02, 0.05, 0.45, "Nucleo", { Para = "Implicados", Retraso = 0.15 }),
			sacudida(4, 0.6),
		},
		Impacto = juntar(
			{
				esfera("Suelo", 10, 70, 0.35, "Nucleo", { Desplazamiento = { 0, 4, 0 } }),
				esfera(
					"Suelo",
					20,
					90,
					0.55,
					"Principal",
					{ Desplazamiento = { 0, 4, 0 }, Transparencia = { 0.3, 1 }, Retraso = 0.05 }
				),
				esfera(
					"Suelo",
					14,
					56,
					0.8,
					"Oscuro",
					{ Desplazamiento = { 0, 4, 0 }, Transparencia = { 0.2, 1 }, Retraso = 0.1, Material = "Plastico" }
				),
				onda("Suelo", 6, 120, 0.9, "Principal"),
				onda("Suelo", 4, 84, 0.6, "Nucleo", { Grosor = 0.3 }),
				onda("Suelo", 10, 160, 1.3, "Secundario", { Retraso = 0.1, Transparencia = { 0.6, 1 } }),
				chispas(
					"Suelo",
					170,
					{ 40, 120 },
					{ 0.6, 1.4 },
					{ "Nucleo", "Principal", "Secundario" },
					{ Tamano = { 2, 0 }, Aceleracion = { 0, -70, 0 }, Desplazamiento = { 0, 2, 0 } }
				),
				capa("Particulas", {
					Anclaje = "Suelo",
					Textura = "Chispa",
					Cantidad = 120,
					Direccion = "Arriba",
					Dispersion = 14,
					Velocidad = { 70, 140 },
					Vida = { 0.8, 1.6 },
					Tamano = { 3, 0 },
					Color = { "Nucleo", "Principal", "Secundario" },
					Aceleracion = { 0, -30, 0 },
				}),
				humo(
					"Suelo",
					40,
					{ 14, 34 },
					{ 1.6, 3 },
					{ Area = { 40, 1, 40 }, Forma = "Disc", Velocidad = { 20, 50 } }
				),
				capa("Escombros", {
					Anclaje = "Suelo",
					Cantidad = 60,
					RadioMin = 4,
					Radio = 28,
					Tamano = { 1.2, 4 },
					Impulso = { 40, 80 },
					Dispersion = { 8, 30 },
					Vida = 3,
					Emerge = true,
					Giro = 6,
					Color = "Oscuro",
				}),
				capa("Escombros", {
					Anclaje = "Suelo",
					Cantidad = 24,
					RadioMin = 2,
					Radio = 18,
					Tamano = { 0.5, 1.2 },
					Impulso = { 50, 90 },
					Dispersion = { 8, 26 },
					Vida = 2.2,
					Neon = true,
					Color = "Principal",
				}),
				capa(
					"Crater",
					{ Anclaje = "Suelo", Radio = 26, Duracion = 9, Desvanecer = 2, Grietas = 18, Rocas = 22 }
				),
				luz("Suelo", { 20, 0 }, { 40, 60 }, 1.0, "Nucleo", { Desplazamiento = { 0, 5, 0 } }),
				sacudida(10, 1.3, { Frecuencia = 28, Radio = 200 }),
				capa("Desenfoque", { Tamano = 24, Entrada = 0.02, Mantener = 0.06, Salida = 0.6 }),
				tinte(1, 0.01, 0.08, 0.8, "Nucleo"),
				tinte(0, 0.08, 0.3, 1.0, "#8FA8FF", { Contraste = 0.3, Saturacion = -0.5, Retraso = 0.15 }),
				capa("Zoom", { Delta = -10, Entrada = 0.03, Mantener = 0.08, Salida = 0.6 }),
				capa("Sonido", { Sonido = "TruenoDefinitiva", Anclaje = "Suelo", Volumen = 1 }),
			},
			arcosRadiales(
				"Suelo",
				8,
				24,
				{ "Nucleo", "Principal" },
				0.03,
				{ Segmentos = 9, Desviacion = 2.6, Ancho = { 1.6, 0 } }
			)
		),
		Residuo = {
			capa("Particulas", {
				Anclaje = "Suelo",
				Desplazamiento = { 0, 36, 0 },
				Textura = "Chispa",
				Tasa = 130,
				Duracion = 3,
				Area = { 60, 1, 60 },
				Forma = "Disc",
				Direccion = "Abajo",
				Velocidad = { 14, 36 },
				Vida = { 0.8, 1.3 },
				Tamano = { 0.7, 0 },
				Color = { "Nucleo", "Principal" },
				Retraso = 0.3,
			}),
			capa("Particulas", {
				Anclaje = "Suelo",
				Textura = "Chispa",
				Tasa = 70,
				Duracion = 3.5,
				Area = { 40, 0.5, 40 },
				Forma = "Disc",
				Direccion = "Arriba",
				Velocidad = { 3, 12 },
				Vida = { 0.8, 1.6 },
				Tamano = { 0.8, 0 },
				Color = { "Nucleo", "Principal" },
				Aceleracion = { 0, 12, 0 },
				Retraso = 0.3,
			}),
			humo(
				"Suelo",
				0,
				{ 10, 26 },
				{ 2, 3.4 },
				{ Tasa = 16, Duracion = 4, Area = { 30, 1, 30 }, Forma = "Disc", Velocidad = { 6, 16 }, Retraso = 0.4 }
			),
			luz("Suelo", { 5, 0 }, { 30, 40 }, 3, "Principal", { Desplazamiento = { 0, 4, 0 }, Retraso = 0.5 }),
			arco(
				"Suelo",
				{ -12, 0.3, 6 },
				"Suelo",
				{ 10, 0.3, -12 },
				0.3,
				{ "Nucleo", "Principal" },
				{ Retraso = 0.6, Segmentos = 8, Desviacion = 2 }
			),
			arco(
				"Suelo",
				{ 14, 0.3, 8 },
				"Suelo",
				{ -8, 0.3, -14 },
				0.3,
				{ "Nucleo", "Principal" },
				{ Retraso = 1.1, Segmentos = 8, Desviacion = 2 }
			),
			arco(
				"Suelo",
				{ -10, 0.3, -10 },
				"Suelo",
				{ 12, 0.3, 10 },
				0.3,
				{ "Nucleo", "Principal" },
				{ Retraso = 1.7, Segmentos = 8, Desviacion = 2 }
			),
		},
		Golpeado = {
			esfera("Victima", 3, 14, 0.25, "Nucleo"),
			chispas("Victima", 60, { 20, 60 }, { 0.4, 0.9 }, { "Nucleo", "Principal" }),
			tinte(0.6, 0.01, 0.08, 0.6, "Nucleo", { Para = "Golpeados" }),
			sacudida(8, 0.8, { Para = "Golpeados" }),
			capa("Zoom", { Delta = -8, Entrada = 0.02, Mantener = 0.06, Salida = 0.5, Para = "Golpeados" }),
		},
	},
}

-- ===========================================================================================================
-- GRAVEDAD
-- ===========================================================================================================

Recetas.Gravedad_Basico = {
	Paleta = "Gravedad",
	Hitstop = 0.06,
	Fases = {
		Anticipacion = {
			-- Orbe negro con anillo de energía; partículas que se comprimen hacia él.
			esfera(
				"Mano",
				0.2,
				2.4,
				0.32,
				"Oscuro",
				{ Sigue = true, Material = "Plastico", Transparencia = { 0, 0 }, Easing = "Cubic" }
			),
			esfera(
				"Mano",
				0.5,
				4.2,
				0.32,
				"Principal",
				{ Sigue = true, Transparencia = { 0.7, 0.8 }, Easing = "Cubic" }
			),
			onda(
				"Mano",
				8,
				2.5,
				0.32,
				"Secundario",
				{ Orientacion = "Frente", Grosor = 0.15, Transparencia = { 0.7, 0.2 } }
			),
			capa("Particulas", {
				Anclaje = "Mano",
				Sigue = true,
				Textura = "Chispa",
				Tasa = 100,
				Duracion = 0.32,
				Area = { 7, 7, 7 },
				Forma = "Sphere",
				Velocidad = { -12, -7 },
				Vida = { 0.2, 0.34 },
				Tamano = { 0.8, 0 },
				Color = { "Secundario", "Principal" },
			}),
			luz("Mano", { 0, 3 }, { 4, 14 }, 0.32, "Principal", { Sigue = true }),
			capa("Sonido", { Sonido = "CargaGravedad", Anclaje = "Mano" }),
		},
		Lanzamiento = {
			capa("Proyectil", {
				Desde = "Mano",
				Hasta = "Objetivo",
				Duracion = "Viaje",
				Diametro = 2.6,
				Color = "Principal",
				ColorNucleo = "Oscuro",
				Halo = 2.7,
				Espiral = { 1.3, 2 },
				Estela = { Ancho = 3.2, Vida = 0.42 },
				Chispas = 90,
				Luz = 3,
			}),
			capa("Proyectil", {
				Desde = "Mano",
				Hasta = "Objetivo",
				Duracion = "Viaje",
				Diametro = 0.9,
				Color = "Secundario",
				ColorNucleo = "Nucleo",
				Halo = 2,
				Espiral = { 2.4, 3 },
				Estela = { Ancho = 1.4, Vida = 0.35 },
			}),
			onda(
				"Mano",
				2,
				11,
				0.25,
				"Secundario",
				{ Orientacion = "Frente", Grosor = 0.2, Desplazamiento = { 0, 0, -1 } }
			),
			onda(
				"Mano",
				2,
				8,
				0.25,
				"Principal",
				{ Orientacion = "Frente", Grosor = 0.2, Desplazamiento = { 0, 0, -2 }, Retraso = 0.07 }
			),
			capa("Zoom", { Delta = 3, Entrada = 0.04, Mantener = 0.02, Salida = 0.25, Para = "Lanzador" }),
		},
		Impacto = {
			-- Implosión seguida de explosión.
			esfera(
				"Objetivo",
				16,
				2,
				0.24,
				"Oscuro",
				{ Material = "Plastico", Transparencia = { 0.6, 0 }, Easing = "Quad" }
			),
			esfera("Objetivo", 2, 24, 0.38, "Principal", { Retraso = 0.22, Transparencia = { 0.1, 1 } }),
			esfera("Objetivo", 4, 15, 0.3, "Nucleo", { Retraso = 0.24 }),
			onda("Suelo", 32, 3, 0.3, "Secundario", { Transparencia = { 0.7, 0.1 } }),
			onda("Suelo", 3, 36, 0.5, "Principal", { Retraso = 0.28 }),
			capa("Particulas", {
				Anclaje = "Objetivo",
				Textura = "Chispa",
				Cantidad = 70,
				Area = { 20, 20, 20 },
				Forma = "Sphere",
				Velocidad = { -34, -20 },
				Vida = { 0.2, 0.32 },
				Tamano = { 1, 0 },
				Color = { "Secundario", "Principal" },
			}),
			chispas(
				"Objetivo",
				56,
				{ 22, 52 },
				{ 0.4, 0.9 },
				{ "Nucleo", "Principal", "Secundario" },
				{ Retraso = 0.25 }
			),
			capa("Escombros", {
				Anclaje = "Suelo",
				Cantidad = 14,
				RadioMin = 2,
				Radio = 8,
				Tamano = { 0.5, 1.4 },
				Impulso = { 6, 14 },
				Dispersion = { 0, 2 },
				Gravedad = 0,
				Atraccion = 90,
				Vida = 0.55,
				Emerge = true,
				Color = "Oscuro",
			}),
			humo("Suelo", 14, { 4, 11 }, { 0.8, 1.4 }, { Retraso = 0.28, Color = "Oscuro" }),
			capa(
				"Crater",
				{ Anclaje = "Suelo", Radio = 5, Duracion = 3, Desvanecer = 1, Grietas = 6, Rocas = 6, Retraso = 0.25 }
			),
			luz("Objetivo", { 6, 0 }, { 14, 34 }, 0.5, "Principal", { Retraso = 0.22 }),
			sacudida(3.5, 0.4, { Retraso = 0.24, Radio = 100 }),
			capa("Sonido", { Sonido = "ImpactoGravedad", Anclaje = "Objetivo", Retraso = 0.22 }),
		},
		Residuo = {
			capa("Particulas", {
				Anclaje = "Suelo",
				Textura = "Chispa",
				Tasa = 40,
				Duracion = 0.8,
				Area = { 8, 0.5, 8 },
				Forma = "Disc",
				Direccion = "Arriba",
				Velocidad = { 3, 10 },
				Vida = { 0.5, 1 },
				Tamano = { 0.6, 0 },
				Color = { "Secundario", "Principal" },
				Aceleracion = { 0, 8, 0 },
				Retraso = 0.3,
			}),
			luz("Suelo", { 2, 0 }, { 8, 10 }, 1.2, "Secundario", { Desplazamiento = { 0, 2, 0 }, Retraso = 0.4 }),
		},
		Golpeado = {
			esfera("Victima", 6, 1, 0.2, "Oscuro", { Material = "Plastico", Transparencia = { 0.5, 0 } }),
			chispas(
				"Victima",
				24,
				{ 10, 30 },
				{ 0.3, 0.6 },
				{ "Secundario", "Principal" },
				{ Direccion = "Abajo", Dispersion = 60 }
			),
			tinte(0.12, 0.02, 0.05, 0.3, "Principal", { Saturacion = -0.25, Para = "Golpeados" }),
			sacudida(3, 0.35, { Para = "Golpeados" }),
		},
	},
}

Recetas.Gravedad_Fuerte = {
	Paleta = "Gravedad",
	Hitstop = 0.1,
	AlturaCielo = 90,
	Fases = {
		Anticipacion = {
			-- La zona se tiñe: anillos que se cierran, cúpula, rocas que empiezan a levitar.
			onda("Suelo", 40, 6, 0.85, "Principal", { Transparencia = { 0.8, 0.2 }, Grosor = 0.25 }),
			onda("Suelo", 28, 4, 0.7, "Secundario", { Transparencia = { 0.8, 0.3 }, Retraso = 0.15, Grosor = 0.2 }),
			esfera("Suelo", 30, 30, 0.9, "Principal", { Transparencia = { 0.9, 0.78 }, Material = "Cristal" }),
			capa("Escombros", {
				Anclaje = "Suelo",
				Cantidad = 22,
				Radio = 15,
				Tamano = { 0.6, 1.8 },
				Impulso = { 2, 8 },
				Dispersion = { 0, 1 },
				Gravedad = -0.12,
				Vida = 0.9,
				Emerge = true,
				Color = "Oscuro",
			}),
			capa("Particulas", {
				Anclaje = "Suelo",
				Textura = "Humo",
				Tasa = 40,
				Duracion = 0.85,
				Area = { 30, 0.5, 30 },
				Forma = "Disc",
				Direccion = "Arriba",
				Velocidad = { 3, 9 },
				Vida = { 0.6, 1 },
				Tamano = { 4, 8 },
				Color = "Oscuro",
				Transparencia = { 0.6, 1 },
				Brillo = 0,
			}),
			-- El lanzador junta las manos.
			esfera("Mano", 0.2, 2, 0.85, "Oscuro", { Sigue = true, Material = "Plastico", Transparencia = { 0, 0 } }),
			esfera("Mano", 0.4, 4, 0.85, "Principal", { Sigue = true, Transparencia = { 0.7, 0.8 } }),
			luz("Suelo", { 0, 4 }, { 10, 40 }, 0.85, "Principal", { Desplazamiento = { 0, 4, 0 } }),
			tinte(-0.08, 0.4, 0.4, 0.2, "#B98BFF", { Saturacion = -0.2, Para = "Implicados" }),
			sacudida(1.2, 0.8, { Radio = 90 }),
			capa("Sonido", { Sonido = "CargaGravedad", Anclaje = "Lanzador" }),
		},
		Lanzamiento = {
			-- Pilar de gravedad que cae sobre la zona: columna oscura con núcleo morado y lluvia de motas.
			capa("Haz", {
				Desde = "Cielo",
				Hasta = "Suelo",
				Segmentos = 3,
				Desviacion = 0.3,
				Ancho = { 26, 20 },
				Color = "Oscuro",
				Duracion = 0.32,
				Parpadeos = 2,
				Grupo = "G",
				Brillo = 0.1,
			}),
			capa("Haz", {
				Desde = "Cielo",
				Hasta = "Suelo",
				Segmentos = 3,
				Desviacion = 0.3,
				Ancho = { 14, 9 },
				Color = { "Principal", "Secundario" },
				Duracion = 0.32,
				Parpadeos = 2,
				Grupo = "G",
			}),
			capa("Particulas", {
				Anclaje = "Suelo",
				Desplazamiento = { 0, 60, 0 },
				Textura = "Chispa",
				Cantidad = 120,
				Area = { 30, 1, 30 },
				Forma = "Disc",
				Direccion = "Abajo",
				Velocidad = { 80, 140 },
				Vida = { 0.3, 0.45 },
				Tamano = { 2.2, 0 },
				Color = { "Nucleo", "Principal" },
			}),
			onda("Suelo", 40, 8, 0.22, "Oscuro", { Material = "Plastico", Transparencia = { 0.5, 0.1 } }),
			capa("Zoom", { Delta = 6, Entrada = 0.05, Mantener = 0.02, Salida = 0.2, Para = "Lanzador" }),
		},
		Impacto = {
			-- Aplastamiento: la cúpula colapsa y la onda sale disparada al ras de suelo.
			esfera("Suelo", 34, 4, 0.18, "Principal", { Transparencia = { 0.7, 0.1 }, Material = "Cristal" }),
			esfera("Suelo", 6, 28, 0.3, "Nucleo", { Desplazamiento = { 0, 1, 0 }, Retraso = 0.1 }),
			onda("Suelo", 4, 46, 0.5, "Principal", { Retraso = 0.08 }),
			onda("Suelo", 2, 64, 0.8, "Oscuro", { Retraso = 0.12, Material = "Plastico", Transparencia = { 0.3, 1 } }),
			onda("Suelo", 6, 38, 0.4, "Secundario", { Retraso = 0.1, Grosor = 0.2 }),
			capa("Particulas", {
				Anclaje = "Suelo",
				Textura = "Humo",
				Cantidad = 64,
				Area = { 8, 0.5, 8 },
				Forma = "Disc",
				Direccion = "Arriba",
				Dispersion = 88,
				Velocidad = { 30, 62 },
				Vida = { 0.8, 1.5 },
				Tamano = { 5, 14 },
				Color = "Oscuro",
				Transparencia = { 0.4, 1 },
				Brillo = 0,
				Retraso = 0.1,
				Arrastre = 3,
			}),
			chispas(
				"Suelo",
				70,
				{ 20, 60 },
				{ 0.4, 0.9 },
				{ "Nucleo", "Principal", "Secundario" },
				{ Retraso = 0.1, Direccion = "Arriba", Dispersion = 80 }
			),
			capa("Escombros", {
				Anclaje = "Suelo",
				Cantidad = 32,
				RadioMin = 2,
				Radio = 15,
				Tamano = { 0.8, 2.4 },
				Impulso = { 10, 24 },
				Dispersion = { 2, 10 },
				Gravedad = 2.2,
				Vida = 2.4,
				Emerge = true,
				Color = "Oscuro",
				Retraso = 0.1,
			}),
			capa("Crater", {
				Anclaje = "Suelo",
				Radio = 14,
				Duracion = 7,
				Desvanecer = 1.6,
				Grietas = 14,
				Rocas = 16,
				Retraso = 0.1,
			}),
			luz("Suelo", { 10, 0 }, { 20, 50 }, 0.6, "Principal", { Desplazamiento = { 0, 3, 0 }, Retraso = 0.1 }),
			sacudida(8, 0.8, { Frecuencia = 18, Retraso = 0.1, Radio = 150 }),
			capa("Desenfoque", { Tamano = 16, Entrada = 0.02, Mantener = 0.06, Salida = 0.4, Retraso = 0.1 }),
			tinte(0.2, 0.01, 0.04, 0.3, "Nucleo", { Retraso = 0.1 }),
			tinte(-0.1, 0.06, 0.2, 0.7, "#B98BFF", { Contraste = 0.3, Saturacion = -0.4, Retraso = 0.15 }),
			capa("Zoom", { Delta = 8, Entrada = 0.03, Mantener = 0.05, Salida = 0.45, Retraso = 0.1 }),
			capa("Sonido", { Sonido = "ImpactoGravedad", Anclaje = "Suelo", Volumen = 1, Retraso = 0.1 }),
		},
		Residuo = {
			humo(
				"Suelo",
				0,
				{ 6, 14 },
				{ 1.4, 2.4 },
				{ Tasa = 18, Duracion = 2, Area = { 20, 1, 20 }, Forma = "Disc", Velocidad = { 3, 9 }, Retraso = 0.3 }
			),
			capa("Particulas", {
				Anclaje = "Suelo",
				Textura = "Chispa",
				Tasa = 45,
				Duracion = 2,
				Area = { 22, 0.5, 22 },
				Forma = "Disc",
				Direccion = "Arriba",
				Velocidad = { 2, 8 },
				Vida = { 0.8, 1.4 },
				Tamano = { 0.6, 0 },
				Color = { "Secundario", "Principal" },
				Aceleracion = { 0, 14, 0 },
				Retraso = 0.4,
			}),
			luz("Suelo", { 4, 0 }, { 16, 20 }, 2, "Principal", { Desplazamiento = { 0, 2, 0 }, Retraso = 0.4 }),
			arco(
				"Suelo",
				{ -7, 0.3, 4 },
				"Suelo",
				{ 6, 0.3, -6 },
				0.3,
				{ "Secundario", "Principal" },
				{ Retraso = 0.5 }
			),
			arco(
				"Suelo",
				{ 8, 0.3, 5 },
				"Suelo",
				{ -4, 0.3, -8 },
				0.3,
				{ "Secundario", "Principal" },
				{ Retraso = 1.0 }
			),
		},
		Golpeado = {
			esfera("Victima", 8, 1, 0.22, "Oscuro", { Material = "Plastico", Transparencia = { 0.5, 0 } }),
			chispas(
				"Victima",
				36,
				{ 12, 36 },
				{ 0.3, 0.7 },
				{ "Secundario", "Principal" },
				{ Direccion = "Abajo", Dispersion = 70 }
			),
			tinte(0.1, 0.02, 0.1, 0.5, "Principal", { Saturacion = -0.4, Contraste = 0.2, Para = "Golpeados" }),
			sacudida(6, 0.6, { Para = "Golpeados" }),
			capa("Zoom", { Delta = 8, Entrada = 0.03, Mantener = 0.05, Salida = 0.4, Para = "Golpeados" }),
		},
	},
}

Recetas.Gravedad_Definitiva = {
	Paleta = "Gravedad",
	Hitstop = 0.15,
	AlturaCielo = 100,
	Fases = {
		Anticipacion = {
			-- El agujero negro nace sobre el objetivo y crece durante toda la carga.
			esfera(
				"Objetivo",
				1,
				15,
				2.9,
				"Oscuro",
				{ Desplazamiento = { 0, 10, 0 }, Material = "Plastico", Transparencia = { 0, 0 }, Easing = "Cubic" }
			),
			esfera(
				"Objetivo",
				2,
				24,
				2.9,
				"Principal",
				{ Desplazamiento = { 0, 10, 0 }, Transparencia = { 0.8, 0.88 }, Easing = "Cubic" }
			),
			esfera(
				"Objetivo",
				1,
				17,
				2.9,
				"Secundario",
				{ Desplazamiento = { 0, 10, 0 }, Transparencia = { 0.85, 0.7 }, Easing = "Quint", Minimo = "Medio" }
			),
			-- Disco de acreción: anillos que giran y se estrechan.
			onda(
				"Objetivo",
				6,
				34,
				0.9,
				"Secundario",
				{ Desplazamiento = { 0, 10, 0 }, Grosor = 0.3, Giro = 160, Transparencia = { 0.25, 1 } }
			),
			onda("Objetivo", 6, 34, 0.9, "Principal", {
				Desplazamiento = { 0, 10, 0 },
				Grosor = 0.3,
				Giro = -160,
				Transparencia = { 0.25, 1 },
				Retraso = 0.45,
			}),
			onda(
				"Objetivo",
				6,
				34,
				0.9,
				"Secundario",
				{ Desplazamiento = { 0, 10, 0 }, Grosor = 0.3, Giro = 160, Transparencia = { 0.25, 1 }, Retraso = 1.0 }
			),
			onda(
				"Objetivo",
				6,
				34,
				0.9,
				"Principal",
				{ Desplazamiento = { 0, 10, 0 }, Grosor = 0.3, Giro = -160, Transparencia = { 0.25, 1 }, Retraso = 1.5 }
			),
			onda(
				"Objetivo",
				6,
				34,
				0.9,
				"Secundario",
				{ Desplazamiento = { 0, 10, 0 }, Grosor = 0.3, Giro = 160, Transparencia = { 0.25, 1 }, Retraso = 2.0 }
			),
			onda("Suelo", 80, 12, 2.9, "Principal", { Transparencia = { 0.85, 0.3 }, Grosor = 0.3 }),
			-- Todo se ve arrastrado hacia el centro.
			capa("Particulas", {
				Anclaje = "Objetivo",
				Desplazamiento = { 0, 10, 0 },
				Textura = "Chispa",
				Tasa = 170,
				Duracion = 2.9,
				Area = { 56, 56, 56 },
				Forma = "Sphere",
				Velocidad = { -30, -14 },
				Vida = { 0.8, 1.4 },
				Tamano = { 1.5, 0 },
				Color = { "Secundario", "Principal" },
			}),
			capa("Escombros", {
				Anclaje = "Suelo",
				Cantidad = 42,
				RadioMin = 4,
				Radio = 30,
				Tamano = { 0.8, 3 },
				Impulso = { 6, 16 },
				Dispersion = { 0, 2 },
				Gravedad = 0.2,
				Atraccion = 58,
				Vida = 3,
				Emerge = true,
				Giro = 5,
				Color = "Oscuro",
			}),
			capa("Particulas", {
				Anclaje = "Suelo",
				Textura = "Humo",
				Tasa = 30,
				Duracion = 2.9,
				Area = { 60, 1, 60 },
				Forma = "Disc",
				Direccion = "Arriba",
				Velocidad = { 4, 12 },
				Vida = { 1.2, 2 },
				Tamano = { 8, 18 },
				Color = "Oscuro",
				Transparencia = { 0.7, 1 },
				Brillo = 0,
				Minimo = "Medio",
			}),
			-- Enlace de energía entre la mano del lanzador y la singularidad.
			capa("Haz", {
				Desde = "Mano",
				Hasta = "Objetivo",
				DesplazamientoHasta = { 0, 10, 0 },
				Segmentos = 12,
				Desviacion = 1.2,
				Ancho = { 0.8, 0.8 },
				Color = { "Nucleo", "Secundario" },
				Duracion = 2.4,
				Parpadeos = 14,
				Retraso = 0.5,
				Minimo = "Medio",
			}),
			esfera("Lanzador", 3, 7, 2.9, "Secundario", { Sigue = true, Transparencia = { 0.8, 0.65 } }),
			luz("Objetivo", { 0, 8 }, { 20, 60 }, 2.9, "Principal", { Desplazamiento = { 0, 10, 0 } }),
			tinte(-0.2, 1.8, 0.8, 0.4, "#B07BFF", { Contraste = 0.3, Saturacion = -0.6, Para = "Implicados" }),
			capa("Desenfoque", { Tamano = 5, Entrada = 2, Mantener = 0.8, Salida = 0.3, Para = "Implicados" }),
			sacudida(2.2, 2.9, { Radio = 190 }),
			capa("Sonido", { Sonido = "AgujeroNegro", Anclaje = "Objetivo", Volumen = 1 }),
		},
		Lanzamiento = {
			-- Colapso: la esfera se contrae de golpe y todo se precipita hacia dentro.
			esfera(
				"Objetivo",
				15,
				2,
				0.3,
				"Oscuro",
				{ Desplazamiento = { 0, 10, 0 }, Material = "Plastico", Transparencia = { 0, 0 }, Easing = "Quad" }
			),
			esfera("Objetivo", 24, 3, 0.3, "Nucleo", { Desplazamiento = { 0, 10, 0 }, Transparencia = { 0.9, 0.2 } }),
			onda("Suelo", 90, 4, 0.3, "Secundario", { Transparencia = { 0.7, 0.05 } }),
			capa("Particulas", {
				Anclaje = "Objetivo",
				Desplazamiento = { 0, 10, 0 },
				Textura = "Chispa",
				Cantidad = 130,
				Area = { 64, 64, 64 },
				Forma = "Sphere",
				Velocidad = { -90, -50 },
				Vida = { 0.25, 0.35 },
				Tamano = { 1.6, 0 },
				Color = { "Nucleo", "Secundario" },
			}),
			sacudida(5, 0.4, { Radio = 190 }),
		},
		Impacto = juntar(
			{
				-- Explosión de la singularidad.
				esfera("Objetivo", 4, 84, 0.45, "Nucleo", { Desplazamiento = { 0, 8, 0 } }),
				esfera(
					"Objetivo",
					10,
					104,
					0.6,
					"Principal",
					{ Desplazamiento = { 0, 8, 0 }, Transparencia = { 0.3, 1 }, Retraso = 0.05 }
				),
				esfera(
					"Objetivo",
					6,
					64,
					0.85,
					"Oscuro",
					{ Desplazamiento = { 0, 8, 0 }, Material = "Plastico", Transparencia = { 0.1, 1 }, Retraso = 0.1 }
				),
				onda("Suelo", 4, 132, 1.0, "Principal"),
				onda("Suelo", 4, 92, 0.8, "Secundario", { Retraso = 0.1, Grosor = 0.3 }),
				onda(
					"Suelo",
					10,
					168,
					1.4,
					"Oscuro",
					{ Retraso = 0.15, Material = "Plastico", Transparencia = { 0.4, 1 } }
				),
				onda(
					"Objetivo",
					6,
					120,
					0.9,
					"Nucleo",
					{ Desplazamiento = { 0, 8, 0 }, Grosor = 0.25, Retraso = 0.05, Orientacion = "Frente" }
				),
				chispas(
					"Objetivo",
					190,
					{ 50, 130 },
					{ 0.6, 1.5 },
					{ "Nucleo", "Principal", "Secundario" },
					{ Desplazamiento = { 0, 8, 0 }, Tamano = { 2.4, 0 }, Aceleracion = { 0, -50, 0 } }
				),
				capa("Particulas", {
					Anclaje = "Suelo",
					Textura = "Humo",
					Cantidad = 90,
					Area = { 12, 0.5, 12 },
					Forma = "Disc",
					Direccion = "Arriba",
					Dispersion = 88,
					Velocidad = { 50, 120 },
					Vida = { 1.4, 2.8 },
					Tamano = { 14, 36 },
					Color = "Oscuro",
					Transparencia = { 0.4, 1 },
					Brillo = 0,
					Retraso = 0.12,
					Arrastre = 2.5,
				}),
				capa("Escombros", {
					Anclaje = "Suelo",
					Cantidad = 76,
					RadioMin = 3,
					Radio = 22,
					Tamano = { 1.2, 4 },
					Impulso = { 30, 80 },
					Dispersion = { 24, 70 },
					Vida = 3.4,
					Emerge = true,
					Giro = 6,
					Color = "Oscuro",
					Retraso = 0.1,
				}),
				capa("Escombros", {
					Anclaje = "Suelo",
					Cantidad = 26,
					RadioMin = 2,
					Radio = 16,
					Tamano = { 0.5, 1.2 },
					Impulso = { 40, 90 },
					Dispersion = { 20, 60 },
					Vida = 2.4,
					Neon = true,
					Color = "Secundario",
					Retraso = 0.1,
				}),
				capa("Crater", {
					Anclaje = "Suelo",
					Radio = 28,
					Duracion = 10,
					Desvanecer = 2,
					Grietas = 20,
					Rocas = 26,
					Retraso = 0.1,
				}),
				luz("Objetivo", { 20, 0 }, { 40, 60 }, 1.1, "Nucleo", { Desplazamiento = { 0, 8, 0 } }),
				sacudida(11, 1.4, { Frecuencia = 26, Radio = 220 }),
				capa("Desenfoque", { Tamano = 26, Entrada = 0.02, Mantener = 0.08, Salida = 0.7 }),
				tinte(1, 0.01, 0.09, 0.85, "Nucleo"),
				tinte(0, 0.08, 0.3, 1.1, "#B07BFF", { Contraste = 0.32, Saturacion = -0.55, Retraso = 0.15 }),
				capa("Zoom", { Delta = 14, Entrada = 0.03, Mantener = 0.08, Salida = 0.7 }),
				capa("Sonido", { Sonido = "ImpactoGravedad", Anclaje = "Objetivo", Volumen = 1 }),
			},
			arcosRadiales(
				"Suelo",
				8,
				26,
				{ "Nucleo", "Secundario" },
				0.05,
				{ Segmentos = 9, Desviacion = 2.6, Ancho = { 1.8, 0 } }
			)
		),
		Residuo = {
			capa("Escombros", {
				Anclaje = "Suelo",
				Cantidad = 30,
				RadioMin = 4,
				Radio = 30,
				Tamano = { 0.6, 2 },
				Impulso = { 70, 100 },
				Dispersion = { 4, 16 },
				Vida = 3,
				Color = "Oscuro",
				Retraso = 0.6,
			}),
			capa("Particulas", {
				Anclaje = "Suelo",
				Textura = "Chispa",
				Tasa = 90,
				Duracion = 3.5,
				Area = { 50, 0.5, 50 },
				Forma = "Disc",
				Direccion = "Arriba",
				Velocidad = { 3, 12 },
				Vida = { 1, 1.8 },
				Tamano = { 0.9, 0 },
				Color = { "Secundario", "Principal" },
				Aceleracion = { 0, 14, 0 },
				Retraso = 0.4,
			}),
			humo(
				"Suelo",
				0,
				{ 12, 30 },
				{ 2.2, 3.6 },
				{ Tasa = 16, Duracion = 4, Area = { 36, 1, 36 }, Forma = "Disc", Velocidad = { 5, 14 }, Retraso = 0.5 }
			),
			luz("Suelo", { 5, 0 }, { 30, 40 }, 3.2, "Principal", { Desplazamiento = { 0, 4, 0 }, Retraso = 0.5 }),
			arco(
				"Suelo",
				{ -13, 0.3, 7 },
				"Suelo",
				{ 11, 0.3, -12 },
				0.3,
				{ "Nucleo", "Secundario" },
				{ Retraso = 0.7, Segmentos = 8, Desviacion = 2 }
			),
			arco(
				"Suelo",
				{ 15, 0.3, 8 },
				"Suelo",
				{ -9, 0.3, -15 },
				0.3,
				{ "Nucleo", "Secundario" },
				{ Retraso = 1.3, Segmentos = 8, Desviacion = 2 }
			),
		},
		Golpeado = {
			esfera("Victima", 10, 1, 0.25, "Oscuro", { Material = "Plastico", Transparencia = { 0.4, 0 } }),
			chispas("Victima", 60, { 16, 50 }, { 0.4, 0.9 }, { "Nucleo", "Secundario", "Principal" }),
			tinte(0.5, 0.01, 0.08, 0.7, "Nucleo", { Para = "Golpeados" }),
			sacudida(9, 0.9, { Para = "Golpeados" }),
			capa("Zoom", { Delta = 10, Entrada = 0.02, Mantener = 0.08, Salida = 0.5, Para = "Golpeados" }),
		},
	},
}

-- ===========================================================================================================
-- COMBO CUERPO A CUERPO
-- ===========================================================================================================

-- Efectos que comparten los cuatro golpes: cada uno añade su corte y su fuerza.
local function golpeCuerpo(corte: { [string]: any }, fuerza: number, extraImpacto: { any }?, extraGolpeado: { any }?)
	local estela = { Ancho = 2.2 * fuerza, Vida = 0.22 }
	corte.Estela = corte.Estela or estela
	return {
		Paleta = "Cuerpo",
		Hitstop = 0.04 + 0.025 * fuerza,
		Fases = {
			Lanzamiento = juntar({
				capa("Corte", corte),
				capa("Particulas", {
					Anclaje = "Lanzador",
					Desplazamiento = { 0, 0, -3 },
					Direccion = "Frente",
					Textura = "Chispa",
					Cantidad = 8 + 6 * fuerza,
					Velocidad = { 14, 34 },
					Dispersion = 40,
					Vida = { 0.15, 0.3 },
					Tamano = { 0.5, 0 },
					Color = { "Nucleo", "Principal" },
				}),
				capa("Sonido", { Sonido = if fuerza > 2 then "GolpePesado" else "GolpeLigero", Anclaje = "Lanzador" }),
			}, extraImpacto or {}),
			Impacto = {
				humo("Objetivo", 3, { 2, 5 }, { 0.4, 0.7 }, { Velocidad = { 3, 8 }, Transparencia = { 0.7, 1 } }),
				sacudida(0.7 * fuerza, 0.18, { Radio = 50 }),
			},
			Golpeado = juntar({
				esfera("Victima", 1, 4 + 1.5 * fuerza, 0.14, "Nucleo"),
				onda("Victima", 1, 6 + 3 * fuerza, 0.22, "Principal", { Orientacion = "Frente", Grosor = 0.15 }),
				chispas("Victima", 14 + 8 * fuerza, { 14, 36 }, { 0.2, 0.45 }, { "Nucleo", "Principal", "Secundario" }),
				luz("Victima", { 3 * fuerza, 0 }, { 8, 14 }, 0.2, "Principal"),
				tinte(0.06 * fuerza, 0.01, 0.02, 0.15, "Principal", { Para = "Golpeados" }),
				sacudida(1.5 * fuerza, 0.2, { Para = "Implicados", Radio = 60 }),
			}, extraGolpeado or {}),
		},
	}
end

-- Golpe 1: gancho de derecha, tajo horizontal de izquierda a derecha.
Recetas.Combo1 = golpeCuerpo({
	Anclaje = "Lanzador",
	Radio = 4.6,
	Arco = { -70, 50 },
	Inclinacion = -12,
	Duracion = 0.13,
	Color = { "Nucleo", "Principal" },
}, 1)
-- Golpe 2: revés de izquierda, el mismo tajo al revés.
Recetas.Combo2 = golpeCuerpo({
	Anclaje = "Lanzador",
	Radio = 4.6,
	Arco = { 70, -50 },
	Inclinacion = 14,
	Duracion = 0.13,
	Color = { "Nucleo", "Secundario" },
}, 1.2)
-- Golpe 3: patada giratoria, doble corte y anillo en el suelo.
Recetas.Combo3 = golpeCuerpo(
	{
		Anclaje = "Lanzador",
		Radio = 5.6,
		Arco = { -150, 150 },
		Inclinacion = 0,
		Duracion = 0.2,
		Color = { "Nucleo", "Principal" },
		Estela = { Ancho = 3, Vida = 0.3 },
	},
	2,
	{
		capa("Corte", {
			Anclaje = "Lanzador",
			Desplazamiento = { 0, -1.8, 0 },
			Radio = 5.2,
			Arco = { 150, -150 },
			Duracion = 0.2,
			Color = { "Nucleo", "Secundario" },
			Estela = { Ancho = 2, Vida = 0.25 },
		}),
		onda("Lanzador", 3, 16, 0.3, "Secundario", { Desplazamiento = { 0, -2.8, 0 }, Grosor = 0.2 }),
	}
)
-- Golpe 4: remate. Tajo vertical enorme, onda, escombros y grietas en el suelo; el golpeado sale despedido.
Recetas.Combo4 = golpeCuerpo(
	{
		Anclaje = "Lanzador",
		Radio = 6.4,
		Arco = { -80, 75 },
		Inclinacion = 90,
		Duracion = 0.2,
		Color = { "Nucleo", "Principal", "Secundario" },
		Estela = { Ancho = 4.2, Vida = 0.34 },
	},
	3,
	{
		onda("Lanzador", 3, 22, 0.35, "Principal", { Desplazamiento = { 0, -2.8, 0 }, Grosor = 0.25 }),
		capa(
			"Tinte",
			{ Brillo = 0.1, Entrada = 0.02, Mantener = 0.02, Salida = 0.15, Color = "Nucleo", Para = "Lanzador" }
		),
		capa("Zoom", { Delta = -5, Entrada = 0.03, Mantener = 0.03, Salida = 0.3, Para = "Lanzador" }),
	},
	{
		onda("Victima", 2, 26, 0.4, "Secundario", { Orientacion = "Suelo", Desplazamiento = { 0, -2.8, 0 } }),
		capa("Escombros", {
			Anclaje = "Victima",
			Desplazamiento = { 0, -2.8, 0 },
			Cantidad = 12,
			Radio = 5,
			Tamano = { 0.5, 1.4 },
			Impulso = { 16, 30 },
			Dispersion = { 4, 12 },
			Vida = 1.4,
			Emerge = true,
			Color = "Oscuro",
		}),
		capa("Crater", {
			Anclaje = "Victima",
			Desplazamiento = { 0, -2.8, 0 },
			Radio = 6,
			Duracion = 3,
			Desvanecer = 1,
			Grietas = 8,
			Rocas = 6,
		}),
		capa("Desenfoque", { Tamano = 6, Entrada = 0.02, Mantener = 0.03, Salida = 0.2, Para = "Golpeados" }),
	}
)

return Recetas
