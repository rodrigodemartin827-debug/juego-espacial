--!strict
--[[
	Objetos: todo lo que puede haber en el inventario del jugador.

	El inventario guarda { [idObjeto] = cantidad } (ver Datos/Tipos). Aquí se dice qué es cada id: nombre,
	categoría y cuánto espacio ocupa cada unidad en la bodega. El límite de la bodega depende de la mejora
	Carga de la nave (Naves/Datos/Mejoras → Capacidad).

	Los identificadores ("Hierro", "LingoteHierro"...) se guardan en el DataStore y no deben cambiarse.
	Para añadir un objeto nuevo basta con una entrada más aquí; si es un mineral, además hay que darle un nodo
	en Datos/Minerales, y si se fabrica, una receta en Datos/Recetas.
]]

export type Objeto = {
	Nombre: string, -- texto para mostrar
	Descripcion: string,
	Categoria: "Mineral" | "Componente", -- los minerales se pican; los componentes se fabrican
	Volumen: number?, -- espacio por unidad en la bodega (1 si se omite)
	Color: string, -- "#RRGGBB" para el icono en la interfaz
}

local Objetos = {}

-- Orden en que se muestran en el inventario.
Objetos.Orden = table.freeze({
	"Hierro",
	"Cobre",
	"Cristal",
	"Titanio",
	"LingoteHierro",
	"CableCobre",
	"LenteCristal",
	"PlacaTitanio",
	"NucleoEnergia",
})

Objetos.Lista = {
	-- ===== Minerales (se pican en planetas y asteroides) =====
	Hierro = {
		Nombre = "Hierro",
		Descripcion = "Metal común y resistente. La base de casi todo.",
		Categoria = "Mineral",
		Color = "#B7B2AC",
	},
	Cobre = {
		Nombre = "Cobre",
		Descripcion = "Buen conductor de la electricidad. Se vuelve cable.",
		Categoria = "Mineral",
		Color = "#E08A4C",
	},
	Cristal = {
		Nombre = "Cristal de energía",
		Descripcion = "Cristal que vibra al almacenar energía. Frágil y valioso.",
		Categoria = "Mineral",
		Color = "#5CE1FF",
	},
	Titanio = {
		Nombre = "Titanio",
		Descripcion = "Metal ligero y muy duro, escaso en los planetas.",
		Categoria = "Mineral",
		Color = "#8FA7C9",
	},

	-- ===== Componentes (se fabrican en la mesa de crafteo) =====
	LingoteHierro = {
		Nombre = "Lingote de hierro",
		Descripcion = "Hierro refinado, más compacto que el mineral en bruto.",
		Categoria = "Componente",
		Volumen = 2,
		Color = "#D9D4CE",
	},
	CableCobre = {
		Nombre = "Cable de cobre",
		Descripcion = "Cableado para sistemas eléctricos y escudos.",
		Categoria = "Componente",
		Color = "#FFB27A",
	},
	LenteCristal = {
		Nombre = "Lente de cristal",
		Descripcion = "Lente tallada para sensores, escáneres y armas.",
		Categoria = "Componente",
		Color = "#9EF0FF",
	},
	PlacaTitanio = {
		Nombre = "Placa de titanio",
		Descripcion = "Blindaje ligero para el casco y la bodega.",
		Categoria = "Componente",
		Volumen = 2,
		Color = "#B8CCEA",
	},
	NucleoEnergia = {
		Nombre = "Núcleo de energía",
		Descripcion = "Fuente de energía compacta para motores y sistemas avanzados.",
		Categoria = "Componente",
		Volumen = 3,
		Color = "#B58CFF",
	},
} :: { [string]: Objeto }

-- Espacio que ocupa una unidad del objeto (los ids desconocidos ocupan el volumen por defecto).
function Objetos.Volumen(id: string): number
	local objeto = Objetos.Lista[id]
	return (objeto and objeto.Volumen) or 1
end

return Objetos
