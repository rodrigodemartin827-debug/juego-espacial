--!strict
--[[
	CatalogoUI: cómo se PRESENTAN en la interfaz las cosas que ya existen en el juego (objetos del inventario,
	especies del escáner, planetas de bando). Qué son y cuánto valen sigue estando en sus módulos de siempre
	(Exploracion/Datos/Objetos, Exploracion/Datos/Especies...); aquí solo va el arte, la rareza y el filtro.

	Si se añade un objeto o una especie y no tiene entrada aquí, la UI la enseña igual con un arte genérico y
	rareza común (y la prueba InterfazUI avisa de que falta).
]]

local CatalogoUI = {}

export type PresentacionObjeto = {
	Arte: string, -- nombre en herramientas/iconos_ui/arte.mjs
	Rareza: string, -- clave de EspacialTheme.Rareza
	Filtro: string, -- "Armas" | "Armadura" | "Materiales" | "Consumibles" | "Especial"
}

-- Objetos de Exploracion/Datos/Objetos.
CatalogoUI.Objetos = {
	Hierro = { Arte = "item_hierro", Rareza = "Comun", Filtro = "Materiales" },
	Cobre = { Arte = "item_cobre", Rareza = "Comun", Filtro = "Materiales" },
	Cristal = { Arte = "item_cristal", Rareza = "Raro", Filtro = "Materiales" },
	Titanio = { Arte = "item_titanio", Rareza = "PocoComun", Filtro = "Materiales" },
	LingoteHierro = { Arte = "item_lingote_hierro", Rareza = "PocoComun", Filtro = "Materiales" },
	CableCobre = { Arte = "item_cable_cobre", Rareza = "PocoComun", Filtro = "Materiales" },
	LenteCristal = { Arte = "item_lente_cristal", Rareza = "Raro", Filtro = "Materiales" },
	PlacaTitanio = { Arte = "item_placa_titanio", Rareza = "Raro", Filtro = "Materiales" },
	NucleoEnergia = { Arte = "item_nucleo_energia", Rareza = "Epico", Filtro = "Materiales" },
} :: { [string]: PresentacionObjeto }

export type PresentacionEspecie = {
	Arte: string,
	Tipo: string,
	Peligro: number, -- 0..5 estrellas
	Drops: { { Nombre: string, Porcentaje: number } },
}

-- Especies de Exploracion/Datos/Especies (los minerales son "Mineral_<id>").
CatalogoUI.Especies = {
	Criatura_MedusaVacio = {
		Arte = "criatura_medusa_vacio",
		Tipo = "Invertebrado flotante",
		Peligro = 1,
		Drops = { { Nombre = "Gel luminiscente", Porcentaje = 35 } },
	},
	Criatura_BrincadorLanudo = {
		Arte = "criatura_brincador_lanudo",
		Tipo = "Herbívoro",
		Peligro = 0,
		Drops = { { Nombre = "Lana espesa", Porcentaje = 60 } },
	},
	Criatura_AcechadorAbismo = {
		Arte = "criatura_acechador_abismo",
		Tipo = "Depredador",
		Peligro = 4,
		Drops = { { Nombre = "Colmillo abisal", Porcentaje = 12 }, { Nombre = "Ojo lila", Porcentaje = 5 } },
	},
	Criatura_ReptadorLunar = {
		Arte = "criatura_reptador_lunar",
		Tipo = "Acorazado",
		Peligro = 2,
		Drops = { { Nombre = "Placa de quitina", Porcentaje = 25 }, { Nombre = "Hierro", Porcentaje = 40 } },
	},
	Planta_FlorEstelar = {
		Arte = "planta_flor_estelar",
		Tipo = "Flor",
		Peligro = 0,
		Drops = { { Nombre = "Polen estelar", Porcentaje = 30 } },
	},
	Planta_HongoLuminoso = {
		Arte = "planta_hongo_luminoso",
		Tipo = "Hongo",
		Peligro = 0,
		Drops = { { Nombre = "Esporas", Porcentaje = 45 } },
	},
	Mineral_Hierro = {
		Arte = "item_hierro",
		Tipo = "Metal",
		Peligro = 0,
		Drops = { { Nombre = "Hierro", Porcentaje = 100 } },
	},
	Mineral_Cobre = {
		Arte = "item_cobre",
		Tipo = "Metal",
		Peligro = 0,
		Drops = { { Nombre = "Cobre", Porcentaje = 100 } },
	},
	Mineral_Cristal = {
		Arte = "item_cristal",
		Tipo = "Cristal",
		Peligro = 1,
		Drops = { { Nombre = "Cristal de energía", Porcentaje = 100 } },
	},
	Mineral_Titanio = {
		Arte = "item_titanio",
		Tipo = "Metal",
		Peligro = 0,
		Drops = { { Nombre = "Titanio", Porcentaje = 100 } },
	},
} :: { [string]: PresentacionEspecie }

-- Rareza de Especies ("Comun", "Poco comun", "Rara", "Epica") -> clave de EspacialTheme.Rareza.
CatalogoUI.RarezaEspecie = {
	["Comun"] = "Comun",
	["Poco comun"] = "PocoComun",
	["Rara"] = "Raro",
	["Epica"] = "Epico",
	["Legendaria"] = "Legendario",
	["Mitica"] = "Mitico",
} :: { [string]: string }

-- Categoría de Especies -> pestaña del Índice.
CatalogoUI.CategoriaIndice = {
	Criatura = "Criaturas",
	Mineral = "Minerales",
	Planta = "Plantas",
} :: { [string]: string }

-- Arte de los planetas de bando (Planetas/Datos) por id de bando.
CatalogoUI.ArtePlaneta = {
	Humanos = "planeta_nueva_tierra",
	Monstruos = "planeta_umbra",
} :: { [string]: string }

-- Arte por defecto cuando algo no tiene entrada aquí.
CatalogoUI.ArteGenerico = "item_cristal"

return CatalogoUI
