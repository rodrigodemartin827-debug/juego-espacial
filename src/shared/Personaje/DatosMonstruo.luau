--!strict
--[[
	DatosMonstruo: todo lo que se puede elegir en el editor de personaje de los Monstruos (estilo creepypasta, original).
	  · Piel: 10 tonos de piel de monstruo.
	  · Silueta: cuánto se estiran el torso, los brazos y las piernas (la forma del cuerpo).
	  · Cuernos: modelos 3D de Blender (modelos/herramientas/monstruo_editor.py), un Accessory en la cabeza.
	  · Ojos y Boca: texturas sobre la cara (modelos/herramientas/caras_monstruo.py). Los ojos van en blanco con brillo
	    y se tiñen con el color de ojos que elige el jugador.
	  · Deformación: piezas 3D en el cuerpo (espinas, vértebras, costillas, hombros de pinchos, brazo hinchado, joroba,
	    garras y placas óseas).
	  · Marcas: líneas luminosas sobre el pecho (textura que se tiñe con el color de detalles).
	Las piezas y las imágenes de cada opción están en Personaje/RecursosMonstruo (generado): se buscan por
	«<Categoria>_<Id>» (por ejemplo «Cuerno_Curvos» u «Ojos_Dos»).

	Colores libres (rueda de color): ojos, cuernos y detalles (hueso y marcas). `Muestras` son atajos de la paleta.
	Roles de las piezas 3D: Cuerno (color de cuernos), Hueso (color de detalles) y Piel (la piel del monstruo).
]]

export type Opcion = {
	Id: string,
	Nombre: string,
	Anclaje: string?, -- Cuernos: el Attachment de la cabeza al que se sujeta
	Escala: { Torso: { number }?, Brazos: { number }?, Piernas: { number }? }?, -- Silueta
}
export type Color = { Id: string, Nombre: string, Hex: string }
export type Rol = { Color: string?, Material: string }

local Datos = {}

Datos.Pieles = {
	{ Id = "Piel1", Nombre = "Ceniza", Hex = "#7A8A8F" },
	{ Id = "Piel2", Nombre = "Hueso", Hex = "#CFC8B4" },
	{ Id = "Piel3", Nombre = "Azul muerto", Hex = "#4A6A86" },
	{ Id = "Piel4", Nombre = "Verde podrido", Hex = "#5E7A4A" },
	{ Id = "Piel5", Nombre = "Violeta", Hex = "#6A4A7E" },
	{ Id = "Piel6", Nombre = "Carne", Hex = "#8E3A3A" },
	{ Id = "Piel7", Nombre = "Ámbar", Hex = "#A87A36" },
	{ Id = "Piel8", Nombre = "Pizarra", Hex = "#4A4F58" },
	{ Id = "Piel9", Nombre = "Pálido", Hex = "#B8B0A8" },
	{ Id = "Piel10", Nombre = "Negro", Hex = "#1E2024" },
} :: { Color }

Datos.Siluetas = {
	{ Id = "Normal", Nombre = "Base" },
	{
		Id = "Esqueletico",
		Nombre = "Esquelético",
		Escala = { Torso = { 0.8, 1.05, 0.7 }, Brazos = { 0.6, 1.15, 0.6 }, Piernas = { 0.7, 1.2, 0.7 } },
	},
	{
		Id = "Bestia",
		Nombre = "Bestia",
		Escala = { Torso = { 1.35, 1.05, 1.3 }, Brazos = { 1.45, 1.15, 1.45 }, Piernas = { 1.15, 0.95, 1.15 } },
	},
	{
		Id = "Aracnido",
		Nombre = "Arácnido",
		Escala = { Torso = { 0.8, 0.8, 0.8 }, Brazos = { 0.6, 1.45, 0.6 }, Piernas = { 0.6, 1.4, 0.6 } },
	},
	{
		Id = "Jorobado",
		Nombre = "Encorvado",
		Escala = { Torso = { 1.15, 0.9, 1.15 }, Brazos = { 1.1, 1.3, 1.1 }, Piernas = { 0.9, 0.85, 0.9 } },
	},
	{
		Id = "Colosal",
		Nombre = "Colosal",
		Escala = { Torso = { 1.3, 1.1, 1.2 }, Brazos = { 1.25, 1.2, 1.25 }, Piernas = { 1.2, 1.2, 1.2 } },
	},
} :: { Opcion }

Datos.Cuernos = {
	{ Id = "Ninguno", Nombre = "Sin cuernos" },
	{ Id = "Curvos", Nombre = "Curvos", Anclaje = "HatAttachment" },
	{ Id = "Rectos", Nombre = "Rectos", Anclaje = "HatAttachment" },
	{ Id = "Carnero", Nombre = "De carnero", Anclaje = "HatAttachment" },
	{ Id = "Astas", Nombre = "Astas", Anclaje = "HatAttachment" },
	{ Id = "Corona", Nombre = "Corona de espinas", Anclaje = "HatAttachment" },
	{ Id = "Unicornio", Nombre = "Un cuerno", Anclaje = "HatAttachment" },
	{ Id = "Diablillo", Nombre = "Diablillo", Anclaje = "HatAttachment" },
	{ Id = "Retorcidos", Nombre = "Retorcidos", Anclaje = "HatAttachment" },
} :: { Opcion }

Datos.Ojos = {
	{ Id = "Dos", Nombre = "Dos ojos" },
	{ Id = "Tres", Nombre = "Tres ojos" },
	{ Id = "Uno", Nombre = "Un ojo" },
	{ Id = "Cuatro", Nombre = "Cuatro ojos" },
	{ Id = "Rendija", Nombre = "Rendijas" },
	{ Id = "Cuencas", Nombre = "Cuencas vacías" },
	{ Id = "Grandes", Nombre = "Grandes" },
	{ Id = "Multiples", Nombre = "Muchos ojos" },
} :: { Opcion }

Datos.Bocas = {
	{ Id = "Cerrada", Nombre = "Cerrada" },
	{ Id = "Colmillos", Nombre = "Colmillos" },
	{ Id = "Vertical", Nombre = "Vertical" },
	{ Id = "SonrisaRota", Nombre = "Sonrisa rota" },
	{ Id = "Abierta", Nombre = "Abierta" },
	{ Id = "Cosida", Nombre = "Cosida" },
} :: { Opcion }

Datos.Deformaciones = {
	{ Id = "Ninguna", Nombre = "Ninguna" },
	{ Id = "Espinas", Nombre = "Espinas" },
	{ Id = "Vertebras", Nombre = "Vértebras" },
	{ Id = "Costillas", Nombre = "Costillas" },
	{ Id = "Hombros", Nombre = "Hombros de pinchos" },
	{ Id = "BrazoHinchado", Nombre = "Brazo hinchado" },
	{ Id = "Joroba", Nombre = "Joroba" },
	{ Id = "Garras", Nombre = "Garras largas" },
	{ Id = "Placas", Nombre = "Placas óseas" },
} :: { Opcion }

Datos.Marcas = {
	{ Id = "Ninguna", Nombre = "Ninguna" },
	{ Id = "Venas", Nombre = "Venas" },
	{ Id = "Runas", Nombre = "Runas" },
	{ Id = "Grietas", Nombre = "Grietas" },
	{ Id = "Espiral", Nombre = "Espiral" },
	{ Id = "Ojos", Nombre = "Ojos" },
	{ Id = "Costuras", Nombre = "Costura" },
} :: { Opcion }

-- Lo que colorea la rueda, en el orden del botón que cambia de uno a otro.
Datos.ObjetivosColor = {
	{ Campo = "ColorOjos", Nombre = "Ojos" },
	{ Campo = "ColorCuernos", Nombre = "Cuernos" },
	{ Campo = "ColorDetalle", Nombre = "Hueso y marcas" },
}

Datos.Muestras = {
	"#FF2B2B",
	"#FF8A1F",
	"#FFD21F",
	"#7CFF3A",
	"#34E6A0",
	"#4DE8FF",
	"#3A7BFF",
	"#B04DFF",
	"#FF4DB8",
	"#FFFFFF",
	"#D8D2C2",
	"#8C8676",
	"#4A4640",
	"#1A1D22",
	"#7A0F12",
	"#2E5A3A",
}

-- Color fijo (o nil = el que elige el jugador) de cada rol de las piezas 3D.
Datos.Roles = {
	Cuerno = { Material = "SmoothPlastic" },
	Hueso = { Material = "SmoothPlastic" },
	Piel = { Material = "SmoothPlastic" },
	Oscuro = { Color = "#1A1D22", Material = "SmoothPlastic" },
	Neon = { Color = "#FF3A3A", Material = "Neon" },
} :: { [string]: Rol }

Datos.Defecto = {
	Piel = "Piel1",
	Silueta = "Normal",
	Cuernos = "Ninguno",
	Ojos = "Dos",
	Boca = "Colmillos",
	Deformacion = "Ninguna",
	Marcas = "Ninguna",
	ColorOjos = "#FF2B2B",
	ColorCuernos = "#D8D2C2",
	ColorDetalle = "#D8D2C2",
}

return Datos
