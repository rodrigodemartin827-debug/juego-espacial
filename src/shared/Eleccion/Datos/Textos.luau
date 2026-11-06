--!strict
--[[
	Textos (Elección de bando): todo lo que lee el jugador en la pantalla de elección.

	Cada bando tiene su nombre, una frase corta (lema), sus ventajas y su punto débil, y el mensaje que sale al
	elegirlo. Los colores son los de su lado de la pantalla (en hexadecimal "#RRGGBB").

	Las claves de `Bandos` son los identificadores de Juego/Bandos ("Humanos", "Monstruos"): no las cambies.
]]

export type TextosBando = {
	Nombre: string, -- en grande, en mayúsculas
	Lema: string,
	Ventajas: { string },
	Debilidad: string,
	Confirmacion: string, -- sale al elegirlo
	Color: string, -- color principal del lado
	ColorSuave: string, -- para fondos y bordes
	Dificultad: string, -- etiqueta pequeña ("Más fácil para empezar")
}

local Textos = {}

Textos.Titulo = "ELIGE TU BANDO"
Textos.Subtitulo = "Esta decisión te acompañará siempre"
Textos.AyudaRaton = "Pasa el ratón por un lado para conocerlo · Haz clic para elegir"
Textos.AyudaTactil = "Mantén el dedo en un lado para resaltarlo · Suelta para elegir"
Textos.AyudaMando = "◀ ▶ para mirar · Ⓐ para elegir"
Textos.Esperando = "Sellando tu destino..."
Textos.ErrorConfirmacion = "No se pudo confirmar tu elección. Inténtalo de nuevo."
Textos.Aviso =
	"La elección es permanente. Cambiar de bando cuesta muchas monedas, y solo se puede una vez cada 7 días."
Textos.Elegir = "ELEGIR"

Textos.Bandos = {
	Humanos = {
		Nombre = "HUMANOS",
		Lema = "La luz de un mundo que nunca se rinde.",
		Ventajas = {
			"Tiendas y comercio en tu planeta",
			"Muchos materiales de gran calidad",
			"Las mejores naves y tecnología",
		},
		Debilidad = "Menos fuerza, agilidad y vida que los monstruos",
		Confirmacion = "Bienvenido a la luz, explorador.",
		Color = "#4DC8FF",
		ColorSuave = "#1B4A7A",
		Dificultad = "Más fácil para empezar",
	},
	Monstruos = {
		Nombre = "MONSTRUOS",
		Lema = "Lo que acecha a la sombra del agujero negro.",
		Ventajas = {
			"Más fuerza",
			"Más agilidad",
			"Más vida",
		},
		Debilidad = "Menos materiales, y en el planeta humano no te venden nada",
		Confirmacion = "La oscuridad te reconoce.",
		Color = "#FF3A55",
		ColorSuave = "#5A1426",
		Dificultad = "Para quien busca un reto",
	},
} :: { [string]: TextosBando }

return Textos
