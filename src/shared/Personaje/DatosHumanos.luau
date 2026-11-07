--!strict
--[[
	DatosHumanos: todo lo que se puede elegir en el editor de personaje de los Humanos. Piezas propias, no el avatar
	de Roblox:
	  · Cabello y Accesorio: modelos 3D hechos en Blender (modelos/herramientas/personaje_humano.py) que se ponen como
	    Accessory sobre la cabeza del R6.
	  · Cejas, Ojos, Nariz y Boca: texturas (Decals) sobre la cara (modelos/herramientas/caras_humanas.py).
	  · Chaqueta y Pantalon: el cuerpo se pinta con su color y se le pegan detalles 3D (cuello, bolsillos, botas...).
	Las piezas y las imágenes de cada opción están en Personaje/RecursosHumanos (generado): se buscan por
	«<Categoria>_<Id>» (por ejemplo «Cabello_Corto» u «Ojos_Grandes»).

	Colores: la piel se elige de una lista (de clara a oscura). El pelo, la chaqueta, el pantalón y los detalles se
	eligen libres con la rueda de color del editor ("#RRGGBB"); `Muestras` son atajos de la paleta.
	Cada pieza 3D tiene un rol que dice de qué color se pinta (`Roles`).
]]

export type Opcion = {
	Id: string,
	Nombre: string,
	-- Chaqueta: de qué color van los brazos ("Chaqueta" si tiene mangas largas, "Piel" si son cortas).
	Brazos: string?,
	-- Cabello y Accesorio: el Attachment de la cabeza al que se sujeta el Accessory.
	Anclaje: string?,
}
export type Color = { Id: string, Nombre: string, Hex: string }
export type Rol = { Color: string?, Material: string, Transparencia: number? }

local Datos = {}

-- ===== Piel (de clara a oscura) =====

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

-- ===== Categorías (la lista de la izquierda del editor, en este orden) =====

Datos.Cabellos = {
	{ Id = "Ninguno", Nombre = "Sin pelo" },
	{ Id = "Corto", Nombre = "Corto", Anclaje = "HairAttachment" },
	{ Id = "Rapado", Nombre = "Rapado", Anclaje = "HairAttachment" },
	{ Id = "Flequillo", Nombre = "Flequillo", Anclaje = "HairAttachment" },
	{ Id = "Tupe", Nombre = "Tupé", Anclaje = "HairAttachment" },
	{ Id = "Despeinado", Nombre = "Despeinado", Anclaje = "HairAttachment" },
	{ Id = "Puntas", Nombre = "Puntas", Anclaje = "HairAttachment" },
	{ Id = "Cresta", Nombre = "Cresta", Anclaje = "HairAttachment" },
	{ Id = "Rizado", Nombre = "Rizado", Anclaje = "HairAttachment" },
	{ Id = "Melena", Nombre = "Melena", Anclaje = "HairAttachment" },
	{ Id = "Largo", Nombre = "Largo", Anclaje = "HairAttachment" },
	{ Id = "Coleta", Nombre = "Coleta", Anclaje = "HairAttachment" },
	{ Id = "Mono", Nombre = "Moño", Anclaje = "HairAttachment" },
} :: { Opcion }

Datos.Cejas = {
	{ Id = "Rectas", Nombre = "Rectas" },
	{ Id = "Arqueadas", Nombre = "Arqueadas" },
	{ Id = "Gruesas", Nombre = "Gruesas" },
	{ Id = "Finas", Nombre = "Finas" },
	{ Id = "Enfadadas", Nombre = "Enfadadas" },
	{ Id = "Preocupadas", Nombre = "Preocupadas" },
} :: { Opcion }

Datos.Ojos = {
	{ Id = "Redondos", Nombre = "Redondos" },
	{ Id = "Grandes", Nombre = "Grandes" },
	{ Id = "Almendrados", Nombre = "Almendrados" },
	{ Id = "Brillantes", Nombre = "Brillantes" },
	{ Id = "Serios", Nombre = "Serios" },
	{ Id = "Alegres", Nombre = "Alegres" },
	{ Id = "Cansados", Nombre = "Cansados" },
} :: { Opcion }

Datos.Narices = {
	{ Id = "Punto", Nombre = "Punto" },
	{ Id = "Boton", Nombre = "Botón" },
	{ Id = "Recta", Nombre = "Recta" },
	{ Id = "Ancha", Nombre = "Ancha" },
	{ Id = "Ninguna", Nombre = "Sin nariz" },
} :: { Opcion }

Datos.Bocas = {
	{ Id = "Sonrisa", Nombre = "Sonrisa" },
	{ Id = "Amplia", Nombre = "Amplia" },
	{ Id = "Ladeada", Nombre = "Ladeada" },
	{ Id = "Neutra", Nombre = "Neutra" },
	{ Id = "Seria", Nombre = "Seria" },
	{ Id = "Sorpresa", Nombre = "Sorpresa" },
} :: { Opcion }

Datos.Chaquetas = {
	{ Id = "Exploradora", Nombre = "Exploradora", Brazos = "Chaqueta" },
	{ Id = "Piloto", Nombre = "Piloto", Brazos = "Chaqueta" },
	{ Id = "Cazadora", Nombre = "Cazadora", Brazos = "Chaqueta" },
	{ Id = "Mecanico", Nombre = "Mecánico", Brazos = "Piel" },
	{ Id = "Camiseta", Nombre = "Camiseta", Brazos = "Piel" },
} :: { Opcion }

Datos.Pantalones = {
	{ Id = "Cargo", Nombre = "Cargo" },
	{ Id = "Piloto", Nombre = "Piloto" },
	{ Id = "Vaquero", Nombre = "Vaquero" },
	{ Id = "Tactico", Nombre = "Táctico" },
} :: { Opcion }

Datos.Accesorios = {
	{ Id = "Ninguno", Nombre = "Ninguno" },
	{ Id = "Visor", Nombre = "Visor", Anclaje = "FaceFrontAttachment" },
	{ Id = "Gafas", Nombre = "Gafas", Anclaje = "FaceFrontAttachment" },
	{ Id = "Auriculares", Nombre = "Auriculares", Anclaje = "HatAttachment" },
	{ Id = "Comunicador", Nombre = "Comunicador", Anclaje = "HatAttachment" },
	{ Id = "Gorra", Nombre = "Gorra", Anclaje = "HatAttachment" },
	{ Id = "Cinta", Nombre = "Cinta", Anclaje = "HatAttachment" },
} :: { Opcion }

-- ===== Colores libres (rueda de color) =====

-- Lo que colorea la rueda, en el orden del botón que cambia de uno a otro.
Datos.ObjetivosColor = {
	{ Campo = "ColorPelo", Nombre = "Pelo" },
	{ Campo = "ColorChaqueta", Nombre = "Chaqueta" },
	{ Campo = "ColorPantalon", Nombre = "Pantalón" },
	{ Campo = "ColorDetalle", Nombre = "Detalles" },
}

-- Atajos de la paleta debajo de la rueda (los mismos para todo; el primero de cada fila suele quedar bien de pelo).
Datos.Muestras = {
	"#1C1714",
	"#4A2E1E",
	"#7A4E2D",
	"#D8B467",
	"#ECE3C9",
	"#A8431E",
	"#E9EDF2",
	"#7C8592",
	"#2C313A",
	"#2F6FD6",
	"#5FC3F0",
	"#1E2E55",
	"#3E9B55",
	"#C8373A",
	"#E57D2B",
	"#7246B8",
}

-- ===== Roles de las piezas 3D =====

-- Color fijo (o nil = el del jugador: Pelo, Chaqueta, Pantalon, Detalle, Piel) y material de cada rol.
Datos.Roles = {
	Pelo = { Material = "SmoothPlastic" },
	Piel = { Material = "SmoothPlastic" },
	Chaqueta = { Material = "Fabric" },
	Pantalon = { Material = "Fabric" },
	Detalle = { Material = "SmoothPlastic" },
	Oscuro = { Color = "#1A1D22", Material = "SmoothPlastic" },
	Claro = { Color = "#F4F6F8", Material = "SmoothPlastic" },
	Metal = { Color = "#8C96A6", Material = "Metal" },
	Neon = { Color = "#4DE8FF", Material = "Neon" },
	Cristal = { Color = "#7FD8FF", Material = "Glass", Transparencia = 0.35 },
} :: { [string]: Rol }

-- ===== Por defecto =====

Datos.Defecto = {
	Piel = "Piel4",
	Cabello = "Corto",
	Cejas = "Rectas",
	Ojos = "Redondos",
	Nariz = "Punto",
	Boca = "Sonrisa",
	Chaqueta = "Exploradora",
	Pantalon = "Cargo",
	Accesorio = "Ninguno",
	ColorPelo = "#4A2E1E",
	ColorChaqueta = "#2F6FD6",
	ColorPantalon = "#2C313A",
	ColorDetalle = "#E9EDF2",
}

return Datos
