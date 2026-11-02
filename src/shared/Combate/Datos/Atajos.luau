--!strict
--[[
	Atajos (VFX): funciones que construyen las CAPAS de las recetas de efectos sin repetir campos.

	Solo producen tablas de datos (no tocan Roblox), así que las usan tanto las recetas del combate
	(Datos/EfectosVFX) como las de otros sistemas que reutilizan el mismo motor de efectos (por ejemplo,
	las naves: Naves/Datos/EfectosNave). Para el significado de cada campo, ver los módulos de client/VFX/Capas.
]]

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

return {
	capa = capa,
	esfera = esfera,
	onda = onda,
	chispas = chispas,
	humo = humo,
	luz = luz,
	sacudida = sacudida,
	tinte = tinte,
	arco = arco,
	arcosRadiales = arcosRadiales,
	juntar = juntar,
}
