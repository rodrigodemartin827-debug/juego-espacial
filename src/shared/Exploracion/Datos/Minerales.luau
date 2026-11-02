--!strict
--[[
	Minerales: los tipos de nodo que se pueden picar.

	Un nodo es una roca (o una veta pegada a un asteroide) etiquetada "Mineral" con el atributo MineralTipo = id de
	esta tabla. Se pica a mano con el pico del personaje (tecla R) y también con los láseres de la nave.
	Cuando se agota suelta su botín en el inventario del que lo rompió y reaparece pasado un tiempo.

	  Objeto        id del objeto (Datos/Objetos) que suelta
	  Vida          golpes de daño que aguanta (el pico hace ~8 por golpe; el láser de una nave, bastante más)
	  Cantidad      { mínimo, máximo } de unidades que suelta al romperse
	  Origen        dónde aparece de forma natural: "Planeta" y/o "Asteroide"
	  Peso          probabilidad relativa de aparecer al repartir minerales por azar
	  Color, Material, Brillo   aspecto de la roca (Brillo > 0 la hace emitir luz)
]]

export type Mineral = {
	Objeto: string,
	Vida: number,
	Cantidad: { number },
	Origen: { string },
	Peso: number,
	Color: string,
	Material: string, -- nombre de un Enum.Material
	Brillo: number,
}

local Minerales = {}

Minerales.Orden = table.freeze({ "Hierro", "Cobre", "Cristal", "Titanio" })

Minerales.Lista = {
	Hierro = {
		Objeto = "Hierro",
		Vida = 40,
		Cantidad = { 3, 5 },
		Origen = { "Planeta", "Asteroide" },
		Peso = 5,
		Color = "#8C8782",
		Material = "Slate",
		Brillo = 0,
	},
	Cobre = {
		Objeto = "Cobre",
		Vida = 45,
		Cantidad = { 2, 4 },
		Origen = { "Planeta", "Asteroide" },
		Peso = 4,
		Color = "#C46A2E",
		Material = "Slate",
		Brillo = 0,
	},
	Cristal = {
		Objeto = "Cristal",
		Vida = 30,
		Cantidad = { 1, 3 },
		Origen = { "Planeta", "Asteroide" },
		Peso = 2,
		Color = "#4FD8FF",
		Material = "Glass",
		Brillo = 0.6,
	},
	Titanio = {
		Objeto = "Titanio",
		Vida = 90,
		Cantidad = { 1, 3 },
		Origen = { "Asteroide" },
		Peso = 1.5,
		Color = "#6E86AD",
		Material = "Metal",
		Brillo = 0,
	},
} :: { [string]: Mineral }

-- Lista de tipos que pueden aparecer en `origen` ("Planeta" o "Asteroide"), en el orden de Minerales.Orden.
function Minerales.De(origen: string): { string }
	local lista = {}
	for _, id in Minerales.Orden do
		if table.find(Minerales.Lista[id].Origen, origen) ~= nil then
			table.insert(lista, id)
		end
	end
	return lista
end

return Minerales
