--!strict
--[[
	Catalogo: lo que venden las tiendas del planeta humano y a qué precio. Es la única lista que hay que tocar para
	añadir, quitar o equilibrar artículos, o para crear una tienda nueva.

	ARTÍCULOS (Catalogo.Articulos). Cada uno tiene:
	  Nombre, Descripcion   texto para la interfaz
	  Categoria             "Material" (da objetos al inventario) o "Mejora" (sube un nivel una mejora de la nave)
	  Precio                monedas que cuesta UNA compra. Puede ser fijo (40) o crecer con el nivel de la mejora:
	                        { Base = 220, PorNivel = 120 } vale `Base + PorNivel * nivelActual`, redondeado hacia arriba.
	  Resultado             Material:  { Objeto = idObjeto, Cantidad = n }   (ids de Exploracion/Datos/Objetos)
	                        Mejora:    { Mejora = idMejora }                  (ids de Naves/Datos/Mejoras)

	Los materiales se pueden comprar de varios en varios (hasta Config.CantidadMaximaPorPeticion de una vez); las mejoras,
	de una en una.

	Equilibrio: comprar sale más caro que picar y fabricar (una mejora comprada cuesta en monedas bastante más que sus
	materiales en la mesa de crafteo). Es la ventaja de los Humanos, que tienen tiendas, sin que deje de compensar
	explorar. Todo se paga con monedas del juego: no hay nada a la venta por Robux que dé ventaja en combate.

	TIENDAS (Catalogo.Tiendas). Cada una dice qué artículos vende y en qué orden. Un modelo de tienda en el mundo lleva el
	id de su tienda en el atributo Config.AtributoTiendaId (lo pone ServicioTiendas.CrearTienda).

	El servidor lo valida todo con Tiendas/Compras: el cliente solo pide un artículo por su id.
]]

export type Escalado = { Base: number, PorNivel: number }
export type Precio = number | Escalado

export type Articulo = {
	Nombre: string,
	Descripcion: string,
	Categoria: "Material" | "Mejora",
	Precio: Precio,
	Resultado: { Objeto: string?, Cantidad: number?, Mejora: string? },
}

export type Tienda = {
	Nombre: string, -- rótulo de la tienda
	Lema: string, -- subtítulo en el panel
	Articulos: { string }, -- ids de Catalogo.Articulos, en el orden en que se muestran
}

local Catalogo = {}

-- Orden de todos los artículos (el validador de la red acepta exactamente estos ids).
Catalogo.Orden = table.freeze({
	"Hierro",
	"Cobre",
	"Cristal",
	"Titanio",
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

Catalogo.Articulos = {
	-- ===== Materiales en bruto =====
	Hierro = {
		Nombre = "Hierro",
		Descripcion = "Un saco de mineral de hierro de las minas de la colonia.",
		Categoria = "Material",
		Precio = 6,
		Resultado = { Objeto = "Hierro", Cantidad = 1 },
	},
	Cobre = {
		Nombre = "Cobre",
		Descripcion = "Cobre en bruto, listo para estirar en cable.",
		Categoria = "Material",
		Precio = 8,
		Resultado = { Objeto = "Cobre", Cantidad = 1 },
	},
	Cristal = {
		Nombre = "Cristal de energía",
		Descripcion = "Cristal certificado por los laboratorios de la colonia.",
		Categoria = "Material",
		Precio = 18,
		Resultado = { Objeto = "Cristal", Cantidad = 1 },
	},
	Titanio = {
		Nombre = "Titanio",
		Descripcion = "Titanio de importación. Escaso y caro.",
		Categoria = "Material",
		Precio = 26,
		Resultado = { Objeto = "Titanio", Cantidad = 1 },
	},

	-- ===== Componentes ya fabricados =====
	LingoteHierro = {
		Nombre = "Lingote de hierro",
		Descripcion = "Hierro refinado en las fundiciones humanas.",
		Categoria = "Material",
		Precio = 24,
		Resultado = { Objeto = "LingoteHierro", Cantidad = 1 },
	},
	CableCobre = {
		Nombre = "Cable de cobre",
		Descripcion = "Una bobina de cable de calidad militar.",
		Categoria = "Material",
		Precio = 12,
		Resultado = { Objeto = "CableCobre", Cantidad = 1 },
	},
	LenteCristal = {
		Nombre = "Lente de cristal",
		Descripcion = "Lente tallada a máquina, sin una sola imperfección.",
		Categoria = "Material",
		Precio = 48,
		Resultado = { Objeto = "LenteCristal", Cantidad = 1 },
	},
	PlacaTitanio = {
		Nombre = "Placa de titanio",
		Descripcion = "Blindaje laminado de los astilleros humanos.",
		Categoria = "Material",
		Precio = 95,
		Resultado = { Objeto = "PlacaTitanio", Cantidad = 1 },
	},
	NucleoEnergia = {
		Nombre = "Núcleo de energía",
		Descripcion = "Núcleo sellado de fábrica. Lo mejor que el dinero puede comprar.",
		Categoria = "Material",
		Precio = 290,
		Resultado = { Objeto = "NucleoEnergia", Cantidad = 1 },
	},

	-- ===== Mejoras de la nave (cada compra sube un nivel) =====
	MejoraCasco = {
		Nombre = "Casco reforzado",
		Descripcion = "Los mecánicos de la colonia suben un nivel el Casco de tu nave.",
		Categoria = "Mejora",
		Precio = { Base = 240, PorNivel = 130 },
		Resultado = { Mejora = "Casco" },
	},
	MejoraEscudo = {
		Nombre = "Escudo mejorado",
		Descripcion = "Instalan un generador de escudo de un nivel más.",
		Categoria = "Mejora",
		Precio = { Base = 240, PorNivel = 130 },
		Resultado = { Mejora = "Escudo" },
	},
	MejoraMotor = {
		Nombre = "Motor potenciado",
		Descripcion = "Ajustan el motor de tu nave para que dé un nivel más.",
		Categoria = "Mejora",
		Precio = { Base = 320, PorNivel = 170 },
		Resultado = { Mejora = "Motor" },
	},
	MejoraArmas = {
		Nombre = "Láseres afinados",
		Descripcion = "Calibran tus láseres: un nivel más de Armas.",
		Categoria = "Mejora",
		Precio = { Base = 300, PorNivel = 160 },
		Resultado = { Mejora = "Armas" },
	},
	MejoraEscaner = {
		Nombre = "Escáner ampliado",
		Descripcion = "Un nivel más de Escáner: más alcance y más velocidad de análisis.",
		Categoria = "Mejora",
		Precio = { Base = 200, PorNivel = 110 },
		Resultado = { Mejora = "Escaner" },
	},
	MejoraCarga = {
		Nombre = "Bodega ampliada",
		Descripcion = "Un nivel más de Carga: más espacio en la bodega.",
		Categoria = "Mejora",
		Precio = { Base = 200, PorNivel = 100 },
		Resultado = { Mejora = "Carga" },
	},
} :: { [string]: Articulo }

Catalogo.Tiendas = {
	-- La tienda de ejemplo de la zona de pruebas: vende de todo.
	MercadoColonia = {
		Nombre = "Mercado de la Colonia",
		Lema = "Materiales y mejoras para tu nave · Solo humanos",
		Articulos = {
			"Hierro",
			"Cobre",
			"Cristal",
			"Titanio",
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
		},
	},
	-- Para las ciudades del planeta humano: un puesto de materiales y un astillero de mejoras.
	Suministros = {
		Nombre = "Suministros Orbitales",
		Lema = "Materiales en bruto y componentes",
		Articulos = {
			"Hierro",
			"Cobre",
			"Cristal",
			"Titanio",
			"LingoteHierro",
			"CableCobre",
			"LenteCristal",
			"PlacaTitanio",
			"NucleoEnergia",
		},
	},
	Astillero = {
		Nombre = "Astillero Humano",
		Lema = "Mejoras de nave instaladas al momento",
		Articulos = { "MejoraCasco", "MejoraEscudo", "MejoraMotor", "MejoraArmas", "MejoraEscaner", "MejoraCarga" },
	},
} :: { [string]: Tienda }

-- Ids de todas las tiendas, en orden alfabético (para validar y para las pruebas).
function Catalogo.IdsTiendas(): { string }
	local ids = {}
	for id in Catalogo.Tiendas do
		table.insert(ids, id)
	end
	table.sort(ids)
	return ids
end

-- ¿Vende la tienda `idTienda` el artículo `idArticulo`?
function Catalogo.Vende(idTienda: string, idArticulo: string): boolean
	local tienda = Catalogo.Tiendas[idTienda]
	if tienda == nil then
		return false
	end
	return table.find(tienda.Articulos, idArticulo) ~= nil
end

return Catalogo
