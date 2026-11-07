--!strict
--[[
	DatosHumanos: todo lo que se puede elegir en el editor de personaje de los Humanos. Son piezas propias (no el
	avatar de Roblox): cada opción es una lista de piezas sencillas que se pegan al rig R6 (Personaje/Constructor).

	Coordenadas de las piezas: en el espacio de la parte a la que se pegan (Head, Torso, "Left Arm"...), en studs:
	X a la derecha del personaje, Y arriba, Z hacia atrás (la cara mira a -Z).
	  · Forma: "Bloque", "Bola" (esfera, que se estira con el tamaño) o "Cilindro" (eje X de la pieza).
	  · Color: "Piel", "Pelo", "Principal", "Detalle", "Oscuro", "Claro" o un color "#RRGGBB".
	  · Giro (opcional): grados en X, Y, Z.
	  · Neon (opcional): material de neón (visores).

	La cabeza clásica de R6 (SpecialMesh Head a 1,25) mide por fuera unos 1,25 de ancho, 1,2 de alto y 1,2 de fondo:
	la cara está en Z ≈ -0,6.
]]

export type Pieza = {
	Parte: string?, -- a qué parte del R6 se pega (por defecto, la de la sección)
	Forma: string,
	Pos: { number },
	Tam: { number },
	Color: string,
	Giro: { number }?,
	Neon: boolean?,
}
export type Opcion = { Id: string, Nombre: string, Piezas: { Pieza } }
export type Ropa = Opcion & {
	-- Color de cada parte del cuerpo: "Piel", "Principal", "Detalle" u "Oscuro".
	Torso: string,
	Brazos: string,
	Piernas: string,
}
export type Color = { Id: string, Nombre: string, Hex: string }

local Datos = {}

-- ===== Colores =====

Datos.Pieles = {
	{ Id = "Piel1", Nombre = "Porcelana", Hex = "#F6DCCB" },
	{ Id = "Piel2", Nombre = "Clara", Hex = "#EFC7A8" },
	{ Id = "Piel3", Nombre = "Rosada", Hex = "#E7B095" },
	{ Id = "Piel4", Nombre = "Trigo", Hex = "#D9A57A" },
	{ Id = "Piel5", Nombre = "Miel", Hex = "#C68A5E" },
	{ Id = "Piel6", Nombre = "Canela", Hex = "#A86E45" },
	{ Id = "Piel7", Nombre = "Avellana", Hex = "#8C5A38" },
	{ Id = "Piel8", Nombre = "Cacao", Hex = "#6E4329" },
	{ Id = "Piel9", Nombre = "Ébano", Hex = "#4E2E1D" },
	{ Id = "Piel10", Nombre = "Noche", Hex = "#3A2216" },
} :: { Color }

Datos.ColoresPelo = {
	{ Id = "Negro", Nombre = "Negro", Hex = "#1C1714" },
	{ Id = "Castano", Nombre = "Castaño", Hex = "#4A2E1E" },
	{ Id = "Avellana", Nombre = "Avellana", Hex = "#7A4E2D" },
	{ Id = "Rubio", Nombre = "Rubio", Hex = "#D8B467" },
	{ Id = "Platino", Nombre = "Platino", Hex = "#ECE3C9" },
	{ Id = "Pelirrojo", Nombre = "Pelirrojo", Hex = "#A8431E" },
	{ Id = "Gris", Nombre = "Gris", Hex = "#8D8F93" },
	{ Id = "Azul", Nombre = "Azul", Hex = "#2D5BD1" },
	{ Id = "Rosa", Nombre = "Rosa", Hex = "#E65C9C" },
	{ Id = "Verde", Nombre = "Verde", Hex = "#2E9E6A" },
} :: { Color }

-- Colores del traje (principal y detalle salen de la misma paleta).
Datos.ColoresRopa = {
	{ Id = "Blanco", Nombre = "Blanco", Hex = "#E9EDF2" },
	{ Id = "Gris", Nombre = "Gris", Hex = "#7C8592" },
	{ Id = "Grafito", Nombre = "Grafito", Hex = "#2C313A" },
	{ Id = "Azul", Nombre = "Azul", Hex = "#2F6FD6" },
	{ Id = "Celeste", Nombre = "Celeste", Hex = "#5FC3F0" },
	{ Id = "Marino", Nombre = "Marino", Hex = "#1E2E55" },
	{ Id = "Verde", Nombre = "Verde", Hex = "#3E9B55" },
	{ Id = "Oliva", Nombre = "Oliva", Hex = "#6B7440" },
	{ Id = "Rojo", Nombre = "Rojo", Hex = "#C8373A" },
	{ Id = "Naranja", Nombre = "Naranja", Hex = "#E57D2B" },
	{ Id = "Amarillo", Nombre = "Amarillo", Hex = "#E8C23A" },
	{ Id = "Morado", Nombre = "Morado", Hex = "#7246B8" },
	{ Id = "Marron", Nombre = "Marrón", Hex = "#6A4A32" },
	{ Id = "Arena", Nombre = "Arena", Hex = "#CDB48A" },
} :: { Color }

Datos.Oscuro = "#1A1D22" -- botas, pupilas, correas
Datos.Claro = "#F4F6F8" -- blanco de los ojos, brillos

-- ===== Caras (en la cabeza) =====
-- Ojos: dos piezas a ±Separacion; Cejas encima; Boca debajo. Todo en Z = -0,6 (sobre la cara).

local function cara(
	id: string,
	nombre: string,
	ojo: { number },
	separacion: number,
	ceja: number,
	boca: { Pieza }
): Opcion
	local piezas: { Pieza } = {}
	for _, lado in { -1, 1 } do
		table.insert(piezas, {
			Forma = "Bola",
			Pos = { lado * separacion, 0.08, -0.58 },
			Tam = { ojo[1], ojo[2], 0.06 },
			Color = "Oscuro",
		})
		table.insert(piezas, {
			Forma = "Bloque",
			Pos = { lado * separacion, 0.08 + ojo[2] / 2 + 0.07, -0.585 },
			Tam = { ojo[1] * 1.25, 0.045, 0.04 },
			Color = "Pelo",
			Giro = { 0, 0, -lado * ceja },
		})
	end
	for _, p in boca do
		table.insert(piezas, p)
	end
	return { Id = id, Nombre = nombre, Piezas = piezas }
end

local function bocaRecta(ancho: number): { Pieza }
	return { { Forma = "Bloque", Pos = { 0, -0.2, -0.59 }, Tam = { ancho, 0.045, 0.04 }, Color = "Oscuro" } }
end

-- Sonrisa: tres trazos (centro y dos subiendo).
local function bocaSonrisa(ancho: number, subida: number): { Pieza }
	local lado = ancho / 3
	return {
		{ Forma = "Bloque", Pos = { 0, -0.22, -0.59 }, Tam = { lado, 0.045, 0.04 }, Color = "Oscuro" },
		{
			Forma = "Bloque",
			Pos = { -lado, -0.2, -0.588 },
			Tam = { lado, 0.045, 0.04 },
			Color = "Oscuro",
			Giro = { 0, 0, -subida },
		},
		{
			Forma = "Bloque",
			Pos = { lado, -0.2, -0.588 },
			Tam = { lado, 0.045, 0.04 },
			Color = "Oscuro",
			Giro = { 0, 0, subida },
		},
	}
end

Datos.Caras = {
	cara("Amable", "Amable", { 0.1, 0.13 }, 0.2, 6, bocaSonrisa(0.3, 18)),
	cara("Decidida", "Decidida", { 0.11, 0.1 }, 0.21, -14, bocaRecta(0.24)),
	cara("Tranquila", "Tranquila", { 0.1, 0.07 }, 0.2, 0, bocaRecta(0.2)),
	cara("Alegre", "Alegre", { 0.12, 0.14 }, 0.22, 10, bocaSonrisa(0.38, 26)),
	cara("Seria", "Seria", { 0.09, 0.09 }, 0.19, -6, bocaRecta(0.28)),
	cara("Picara", "Pícara", { 0.11, 0.11 }, 0.21, 12, bocaSonrisa(0.26, 34)),
	cara("Valiente", "Valiente", { 0.12, 0.11 }, 0.23, -20, bocaSonrisa(0.3, 8)),
	cara("Soñadora", "Soñadora", { 0.13, 0.15 }, 0.21, 16, {
		{ Forma = "Bola", Pos = { 0, -0.21, -0.59 }, Tam = { 0.1, 0.08, 0.04 }, Color = "Oscuro" },
	}),
} :: { Opcion }

-- ===== Peinados (en la cabeza) =====

local function pelo(id: string, nombre: string, piezas: { any }): Opcion
	for _, p in piezas do
		p.Color = p.Color or "Pelo"
	end
	return { Id = id, Nombre = nombre, Piezas = piezas }
end

-- Casquete: la parte de arriba y la nuca, común a casi todos.
local function casquete(alto: number): { Pieza }
	return {
		{ Forma = "Bloque", Pos = { 0, 0.62 - alto / 2 + 0.06, 0.04 }, Tam = { 1.32, alto, 1.3 }, Color = "Pelo" },
		{ Forma = "Bloque", Pos = { 0, 0.2, 0.6 }, Tam = { 1.3, 0.7, 0.16 }, Color = "Pelo" },
	}
end

local function unir(...: { any }): { any }
	local todo = {}
	for _, lista in { ... } do
		for _, p in lista do
			table.insert(todo, p)
		end
	end
	return todo
end

Datos.Peinados = {
	pelo("Ninguno", "Sin pelo", {}),
	pelo("Rapado", "Rapado", {
		{ Forma = "Bloque", Pos = { 0, 0.6, 0.06 }, Tam = { 1.28, 0.1, 1.24 } },
		{ Forma = "Bloque", Pos = { 0, 0.25, 0.6 }, Tam = { 1.26, 0.55, 0.08 } },
	}),
	pelo(
		"Corto",
		"Corto",
		unir(casquete(0.26), {
			{ Forma = "Bloque", Pos = { -0.63, 0.32, 0.12 }, Tam = { 0.1, 0.32, 0.9 } },
			{ Forma = "Bloque", Pos = { 0.63, 0.32, 0.12 }, Tam = { 0.1, 0.32, 0.9 } },
		})
	),
	pelo(
		"Flequillo",
		"Flequillo",
		unir(casquete(0.3), {
			{ Forma = "Bloque", Pos = { -0.2, 0.42, -0.62 }, Tam = { 0.75, 0.26, 0.12 }, Giro = { 0, 0, 8 } },
			{ Forma = "Bloque", Pos = { 0.38, 0.47, -0.61 }, Tam = { 0.4, 0.16, 0.12 }, Giro = { 0, 0, -10 } },
			{ Forma = "Bloque", Pos = { -0.63, 0.25, 0.1 }, Tam = { 0.1, 0.45, 0.95 } },
			{ Forma = "Bloque", Pos = { 0.63, 0.25, 0.1 }, Tam = { 0.1, 0.45, 0.95 } },
		})
	),
	pelo("Cresta", "Cresta", {
		{ Forma = "Bloque", Pos = { 0, 0.7, 0.05 }, Tam = { 0.3, 0.32, 1.2 } },
		{ Forma = "Bloque", Pos = { 0, 0.84, -0.32 }, Tam = { 0.26, 0.2, 0.4 }, Giro = { -18, 0, 0 } },
		{ Forma = "Bloque", Pos = { 0, 0.6, 0.06 }, Tam = { 1.26, 0.08, 1.22 } },
	}),
	pelo(
		"Despeinado",
		"Despeinado",
		unir(casquete(0.3), {
			{ Forma = "Bloque", Pos = { -0.3, 0.78, -0.2 }, Tam = { 0.32, 0.22, 0.32 }, Giro = { 10, 20, 14 } },
			{ Forma = "Bloque", Pos = { 0.25, 0.8, 0.1 }, Tam = { 0.34, 0.24, 0.34 }, Giro = { -12, -25, -10 } },
			{ Forma = "Bloque", Pos = { 0.05, 0.76, 0.42 }, Tam = { 0.36, 0.2, 0.3 }, Giro = { 18, 8, 6 } },
			{ Forma = "Bloque", Pos = { -0.3, 0.42, -0.62 }, Tam = { 0.45, 0.2, 0.12 }, Giro = { 0, 0, 14 } },
		})
	),
	pelo(
		"Coleta",
		"Coleta",
		unir(casquete(0.28), {
			{ Forma = "Bloque", Pos = { -0.63, 0.25, 0.1 }, Tam = { 0.1, 0.45, 0.95 } },
			{ Forma = "Bloque", Pos = { 0.63, 0.25, 0.1 }, Tam = { 0.1, 0.45, 0.95 } },
			{ Forma = "Bola", Pos = { 0, 0.32, 0.78 }, Tam = { 0.3, 0.3, 0.3 } },
			{ Forma = "Bloque", Pos = { 0, -0.12, 0.84 }, Tam = { 0.26, 0.8, 0.26 }, Giro = { -10, 0, 0 } },
		})
	),
	pelo(
		"Largo",
		"Largo",
		unir(casquete(0.32), {
			{ Forma = "Bloque", Pos = { -0.65, -0.05, 0.12 }, Tam = { 0.14, 1.05, 1.0 } },
			{ Forma = "Bloque", Pos = { 0.65, -0.05, 0.12 }, Tam = { 0.14, 1.05, 1.0 } },
			{ Forma = "Bloque", Pos = { 0, -0.15, 0.64 }, Tam = { 1.34, 1.25, 0.16 } },
			{ Forma = "Bloque", Pos = { -0.25, 0.43, -0.62 }, Tam = { 0.6, 0.2, 0.1 }, Giro = { 0, 0, 6 } },
		})
	),
	pelo(
		"Mono",
		"Moño",
		unir(casquete(0.26), {
			{ Forma = "Bola", Pos = { 0, 0.92, 0.18 }, Tam = { 0.5, 0.46, 0.5 } },
			{ Forma = "Bloque", Pos = { -0.63, 0.3, 0.1 }, Tam = { 0.1, 0.35, 0.9 } },
			{ Forma = "Bloque", Pos = { 0.63, 0.3, 0.1 }, Tam = { 0.1, 0.35, 0.9 } },
		})
	),
} :: { Opcion }

-- ===== Ropa =====

local function ropa(id: string, nombre: string, torso: string, brazos: string, piernas: string, piezas: { Pieza }): Ropa
	return { Id = id, Nombre = nombre, Torso = torso, Brazos = brazos, Piernas = piernas, Piezas = piezas }
end

-- Botas, comunes a toda la ropa (en cada pierna).
local BOTAS: { Pieza } = {
	{ Parte = "Left Leg", Forma = "Bloque", Pos = { 0, -0.78, -0.03 }, Tam = { 1.06, 0.46, 1.1 }, Color = "Oscuro" },
	{ Parte = "Right Leg", Forma = "Bloque", Pos = { 0, -0.78, -0.03 }, Tam = { 1.06, 0.46, 1.1 }, Color = "Oscuro" },
}

local function conBotas(piezas: { Pieza }): { Pieza }
	return unir(piezas, BOTAS)
end

Datos.Ropas = {
	ropa(
		"Explorador",
		"Explorador",
		"Principal",
		"Principal",
		"Detalle",
		conBotas({
			{ Parte = "Torso", Forma = "Bloque", Pos = { 0, -0.82, 0 }, Tam = { 2.04, 0.24, 1.06 }, Color = "Oscuro" },
			{ Parte = "Torso", Forma = "Bloque", Pos = { 0, -0.82, -0.54 }, Tam = { 0.3, 0.2, 0.04 }, Color = "Claro" },
			{
				Parte = "Torso",
				Forma = "Bloque",
				Pos = { -0.5, 0.35, -0.52 },
				Tam = { 0.5, 0.4, 0.06 },
				Color = "Detalle",
			},
			{
				Parte = "Torso",
				Forma = "Bloque",
				Pos = { 0.5, 0.35, -0.52 },
				Tam = { 0.5, 0.4, 0.06 },
				Color = "Detalle",
			},
			{
				Parte = "Left Arm",
				Forma = "Bloque",
				Pos = { 0, 0.78, 0 },
				Tam = { 1.06, 0.36, 1.06 },
				Color = "Detalle",
			},
			{
				Parte = "Right Arm",
				Forma = "Bloque",
				Pos = { 0, 0.78, 0 },
				Tam = { 1.06, 0.36, 1.06 },
				Color = "Detalle",
			},
		})
	),
	ropa(
		"Piloto",
		"Mono de piloto",
		"Principal",
		"Principal",
		"Principal",
		conBotas({
			{ Parte = "Torso", Forma = "Bloque", Pos = { 0, 0.88, 0 }, Tam = { 1.4, 0.26, 1.08 }, Color = "Detalle" },
			{
				Parte = "Torso",
				Forma = "Bloque",
				Pos = { 0.2, 0, -0.52 },
				Tam = { 0.08, 1.7, 0.04 },
				Color = "Detalle",
			},
			{
				Parte = "Torso",
				Forma = "Bloque",
				Pos = { -0.55, 0.45, -0.52 },
				Tam = { 0.42, 0.26, 0.04 },
				Color = "Detalle",
			},
			{
				Parte = "Left Arm",
				Forma = "Bloque",
				Pos = { 0, -0.15, -0.51 },
				Tam = { 0.9, 0.1, 0.04 },
				Color = "Detalle",
			},
			{
				Parte = "Right Arm",
				Forma = "Bloque",
				Pos = { 0, -0.15, -0.51 },
				Tam = { 0.9, 0.1, 0.04 },
				Color = "Detalle",
			},
			{
				Parte = "Left Arm",
				Forma = "Bloque",
				Pos = { 0, -0.86, 0 },
				Tam = { 1.04, 0.28, 1.04 },
				Color = "Oscuro",
			},
			{
				Parte = "Right Arm",
				Forma = "Bloque",
				Pos = { 0, -0.86, 0 },
				Tam = { 1.04, 0.28, 1.04 },
				Color = "Oscuro",
			},
		})
	),
	ropa(
		"Chaqueta",
		"Chaqueta",
		"Principal",
		"Principal",
		"Detalle",
		conBotas({
			{ Parte = "Torso", Forma = "Bloque", Pos = { 0, 0, -0.51 }, Tam = { 0.7, 1.96, 0.04 }, Color = "Claro" },
			{
				Parte = "Torso",
				Forma = "Bloque",
				Pos = { -0.42, 0.55, -0.53 },
				Tam = { 0.22, 0.9, 0.04 },
				Color = "Detalle",
				Giro = { 0, 0, -14 },
			},
			{
				Parte = "Torso",
				Forma = "Bloque",
				Pos = { 0.42, 0.55, -0.53 },
				Tam = { 0.22, 0.9, 0.04 },
				Color = "Detalle",
				Giro = { 0, 0, 14 },
			},
			{ Parte = "Torso", Forma = "Bloque", Pos = { 0, 0.9, 0.1 }, Tam = { 1.5, 0.22, 0.9 }, Color = "Detalle" },
		})
	),
	ropa(
		"Camiseta",
		"Camiseta",
		"Principal",
		"Piel",
		"Detalle",
		conBotas({
			{
				Parte = "Left Arm",
				Forma = "Bloque",
				Pos = { 0, 0.62, 0 },
				Tam = { 1.04, 0.78, 1.04 },
				Color = "Principal",
			},
			{
				Parte = "Right Arm",
				Forma = "Bloque",
				Pos = { 0, 0.62, 0 },
				Tam = { 1.04, 0.78, 1.04 },
				Color = "Principal",
			},
			{
				Parte = "Torso",
				Forma = "Bloque",
				Pos = { 0, 0.2, -0.52 },
				Tam = { 0.9, 0.55, 0.04 },
				Color = "Detalle",
			},
		})
	),
	ropa(
		"Mecanico",
		"Mecánico",
		"Detalle",
		"Principal",
		"Principal",
		conBotas({
			{
				Parte = "Torso",
				Forma = "Bloque",
				Pos = { 0, -0.15, -0.52 },
				Tam = { 1.5, 1.4, 0.05 },
				Color = "Principal",
			},
			{
				Parte = "Torso",
				Forma = "Bloque",
				Pos = { -0.6, 0.55, -0.53 },
				Tam = { 0.16, 0.9, 0.04 },
				Color = "Principal",
			},
			{
				Parte = "Torso",
				Forma = "Bloque",
				Pos = { 0.6, 0.55, -0.53 },
				Tam = { 0.16, 0.9, 0.04 },
				Color = "Principal",
			},
			{
				Parte = "Torso",
				Forma = "Bloque",
				Pos = { 0, -0.25, -0.56 },
				Tam = { 0.6, 0.35, 0.04 },
				Color = "Oscuro",
			},
			{
				Parte = "Left Arm",
				Forma = "Bloque",
				Pos = { 0, 0.55, 0 },
				Tam = { 1.04, 0.9, 1.04 },
				Color = "Detalle",
			},
			{
				Parte = "Right Arm",
				Forma = "Bloque",
				Pos = { 0, 0.55, 0 },
				Tam = { 1.04, 0.9, 1.04 },
				Color = "Detalle",
			},
		})
	),
} :: { Ropa }

-- ===== Complementos (en la cabeza) =====

Datos.Complementos = {
	{ Id = "Ninguno", Nombre = "Nada", Piezas = {} },
	{
		Id = "Visor",
		Nombre = "Visor",
		Piezas = {
			{ Forma = "Bloque", Pos = { 0, 0.1, -0.62 }, Tam = { 1.2, 0.2, 0.06 }, Color = "#5CE6FF", Neon = true },
			{ Forma = "Bloque", Pos = { 0, 0.1, 0 }, Tam = { 1.3, 0.08, 1.26 }, Color = "Oscuro" },
		},
	},
	{
		Id = "Gafas",
		Nombre = "Gafas",
		Piezas = {
			{ Forma = "Bloque", Pos = { -0.21, 0.08, -0.63 }, Tam = { 0.3, 0.2, 0.04 }, Color = "Oscuro" },
			{ Forma = "Bloque", Pos = { 0.21, 0.08, -0.63 }, Tam = { 0.3, 0.2, 0.04 }, Color = "Oscuro" },
			{ Forma = "Bloque", Pos = { 0, 0.12, -0.63 }, Tam = { 0.16, 0.04, 0.04 }, Color = "Oscuro" },
		},
	},
	{
		Id = "Auriculares",
		Nombre = "Auriculares",
		Piezas = {
			{ Forma = "Cilindro", Pos = { -0.66, 0.05, 0.02 }, Tam = { 0.16, 0.42, 0.42 }, Color = "Oscuro" },
			{ Forma = "Cilindro", Pos = { 0.66, 0.05, 0.02 }, Tam = { 0.16, 0.42, 0.42 }, Color = "Oscuro" },
			{ Forma = "Bloque", Pos = { 0, 0.7, 0.02 }, Tam = { 1.4, 0.1, 0.16 }, Color = "Detalle" },
		},
	},
	{
		Id = "Cinta",
		Nombre = "Cinta",
		Piezas = { { Forma = "Bloque", Pos = { 0, 0.36, 0 }, Tam = { 1.3, 0.14, 1.26 }, Color = "Detalle" } },
	},
} :: { Opcion }

-- Lo que lleva un personaje nuevo antes de tocar nada.
Datos.Defecto = {
	Piel = "Piel4",
	Cara = "Amable",
	Pelo = "Corto",
	ColorPelo = "Castano",
	Ropa = "Explorador",
	ColorRopa = "Azul",
	ColorDetalle = "Blanco",
	Complemento = "Ninguno",
}

return Datos
