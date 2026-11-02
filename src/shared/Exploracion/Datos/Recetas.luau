--!strict
--[[
	Recetas: todo lo que se puede fabricar en una mesa de crafteo. Es la única lista que hay que tocar para
	añadir, quitar o equilibrar recetas.

	Cada receta tiene:
	  Nombre, Descripcion   texto para la interfaz
	  Categoria             "Mejora" (sube un nivel una mejora de la nave) o "Objeto" (da objetos al inventario)
	  Ingredientes          { [idObjeto] = cantidad }, ids de Datos/Objetos
	  Monedas               (opcional) monedas que cuesta
	  Resultado             Objeto:  { Objeto = idObjeto, Cantidad = n }
	                        Mejora:  { Mejora = idMejora }   (ids de Naves/Datos/Mejoras)

	Una cantidad puede ser un número fijo (3) o crecer con el nivel de la mejora: { Base = 2, PorNivel = 1 } vale
	`Base + PorNivel * nivelActual` redondeado hacia arriba. Así, subir el Casco del nivel 0 al 1 cuesta `Base`, y del 4 al
	5 cuesta `Base + 4 * PorNivel`. En las recetas de objetos el nivel es siempre 0.

	El servidor valida todo con Exploracion/Crafteo: el cliente solo pide una receta por su id y el servidor
	comprueba la distancia a la mesa, los materiales, las monedas, el nivel máximo y el espacio de la bodega.
	Los ids de receta ("Casco"...) no se guardan en ningún sitio, pero el cliente y el servidor deben coincidir.
]]

export type Escalado = { Base: number, PorNivel: number }
export type Cantidad = number | Escalado

export type Receta = {
	Nombre: string,
	Descripcion: string,
	Categoria: "Mejora" | "Objeto",
	Ingredientes: { [string]: Cantidad },
	Monedas: Cantidad?,
	Resultado: { Objeto: string?, Cantidad: number?, Mejora: string? },
}

local Recetas = {}

-- Orden en que se muestran en la mesa: primero los componentes y después las mejoras de la nave.
Recetas.Orden = table.freeze({
	"LingoteHierro",
	"CableCobre",
	"LenteCristal",
	"PlacaTitanio",
	"NucleoEnergia",
	"MejoraCasco",
	"MejoraEscudo",
	"MejoraMotor",
	"MejoraArmas",
	"MejoraEscaner",
	"MejoraCarga",
})

Recetas.Lista = {
	-- ===== Componentes =====
	LingoteHierro = {
		Nombre = "Lingote de hierro",
		Descripcion = "Refina el hierro en bruto.",
		Categoria = "Objeto",
		Ingredientes = { Hierro = 3 },
		Resultado = { Objeto = "LingoteHierro", Cantidad = 1 },
	},
	CableCobre = {
		Nombre = "Cable de cobre",
		Descripcion = "Estira el cobre en cable.",
		Categoria = "Objeto",
		Ingredientes = { Cobre = 2 },
		Resultado = { Objeto = "CableCobre", Cantidad = 2 },
	},
	LenteCristal = {
		Nombre = "Lente de cristal",
		Descripcion = "Talla un cristal de energía y le pone montura.",
		Categoria = "Objeto",
		Ingredientes = { Cristal = 2, Cobre = 1 },
		Resultado = { Objeto = "LenteCristal", Cantidad = 1 },
	},
	PlacaTitanio = {
		Nombre = "Placa de titanio",
		Descripcion = "Lamina titanio y lo refuerza con un lingote.",
		Categoria = "Objeto",
		Ingredientes = { Titanio = 3, LingoteHierro = 1 },
		Resultado = { Objeto = "PlacaTitanio", Cantidad = 1 },
	},
	NucleoEnergia = {
		Nombre = "Núcleo de energía",
		Descripcion = "Condensa cristales en una fuente de energía compacta.",
		Categoria = "Objeto",
		Ingredientes = { Cristal = 3, CableCobre = 2, PlacaTitanio = 1 },
		Monedas = 50,
		Resultado = { Objeto = "NucleoEnergia", Cantidad = 1 },
	},

	-- ===== Mejoras de la nave (cada fabricación sube un nivel) =====
	MejoraCasco = {
		Nombre = "Casco reforzado",
		Descripcion = "Sube un nivel el Casco de tu nave.",
		Categoria = "Mejora",
		Ingredientes = { PlacaTitanio = { Base = 1, PorNivel = 1 }, LingoteHierro = { Base = 2, PorNivel = 1 } },
		Monedas = { Base = 40, PorNivel = 20 },
		Resultado = { Mejora = "Casco" },
	},
	MejoraEscudo = {
		Nombre = "Escudo mejorado",
		Descripcion = "Sube un nivel el Escudo de tu nave.",
		Categoria = "Mejora",
		Ingredientes = { LenteCristal = { Base = 1, PorNivel = 1 }, CableCobre = { Base = 2, PorNivel = 1 } },
		Monedas = { Base = 40, PorNivel = 20 },
		Resultado = { Mejora = "Escudo" },
	},
	MejoraMotor = {
		Nombre = "Motor potenciado",
		Descripcion = "Sube un nivel el Motor de tu nave.",
		Categoria = "Mejora",
		Ingredientes = { NucleoEnergia = { Base = 1, PorNivel = 0.5 }, LingoteHierro = { Base = 2, PorNivel = 1 } },
		Monedas = { Base = 60, PorNivel = 30 },
		Resultado = { Mejora = "Motor" },
	},
	MejoraArmas = {
		Nombre = "Láseres afinados",
		Descripcion = "Sube un nivel las Armas de tu nave.",
		Categoria = "Mejora",
		Ingredientes = { LenteCristal = { Base = 2, PorNivel = 1 }, PlacaTitanio = { Base = 1, PorNivel = 0.5 } },
		Monedas = { Base = 50, PorNivel = 25 },
		Resultado = { Mejora = "Armas" },
	},
	MejoraEscaner = {
		Nombre = "Escáner ampliado",
		Descripcion = "Sube un nivel el Escáner: más alcance y más velocidad de análisis.",
		Categoria = "Mejora",
		Ingredientes = { LenteCristal = { Base = 1, PorNivel = 1 }, CableCobre = { Base = 3, PorNivel = 1 } },
		Monedas = { Base = 30, PorNivel = 20 },
		Resultado = { Mejora = "Escaner" },
	},
	MejoraCarga = {
		Nombre = "Bodega ampliada",
		Descripcion = "Sube un nivel la Carga: más espacio en el inventario.",
		Categoria = "Mejora",
		Ingredientes = { PlacaTitanio = { Base = 1, PorNivel = 1 }, LingoteHierro = { Base = 3, PorNivel = 1 } },
		Monedas = { Base = 30, PorNivel = 15 },
		Resultado = { Mejora = "Carga" },
	},
} :: { [string]: Receta }

-- Ids de todas las recetas, en el orden en que se muestran.
function Recetas.Ids(): { string }
	return table.clone(Recetas.Orden :: any)
end

return Recetas
