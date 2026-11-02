--!strict
--[[
	Especies: todo lo que el escáner puede analizar (criaturas, plantas y minerales) y lo que dice su ficha.

	Una instancia es escaneable si lleva la etiqueta "Escaneable" y el atributo EspecieId = id de esta tabla. La ficha
	que ve el jugador sale de aquí; el servidor solo decide si el escaneo es válido y reparte la recompensa.

	  Categoria    "Criatura" | "Planta" | "Mineral"
	  Rareza       "Comun" | "Poco comun" | "Rara" | "Epica" (decide el color de la ficha)
	  Duracion     segundos que tarda el análisis con el escáner sin mejorar (la mejora Escáner lo acelera)
	  Datos        filas { etiqueta, valor } de la ficha
	  XP, Monedas  recompensa por el PRIMER escaneo (los siguientes cobran una fracción, ver Config)

	Los minerales se generan solos a partir de Datos/Minerales: su id de especie es "Mineral_<id>".
	Los identificadores se guardan en los datos del jugador (lista de descubrimientos) y no deben cambiarse.
]]

local Minerales = require(script.Parent.Minerales)
local Objetos = require(script.Parent.Objetos)

export type Especie = {
	Categoria: string,
	Nombre: string,
	Descripcion: string,
	Rareza: string,
	Duracion: number,
	Datos: { { string } },
	XP: number,
	Monedas: number,
}

local Especies = {}

-- Color de la ficha según la rareza.
Especies.ColoresRareza = table.freeze(({
	["Comun"] = "#B8C4D6",
	["Poco comun"] = "#5CE08A",
	["Rara"] = "#5CB8FF",
	["Epica"] = "#C58CFF",
} :: any) :: { [string]: string })

local lista: { [string]: Especie } = {
	-- ===== Criaturas =====
	Criatura_MedusaVacio = {
		Categoria = "Criatura",
		Nombre = "Medusa del vacío",
		Descripcion = "Organismo gelatinoso que flota sin esfuerzo en atmósferas finas. Brilla al digerir la radiación.",
		Rareza = "Rara",
		Duracion = 2.6,
		Datos = {
			{ "Hábitat", "Atmósferas finas y asteroides húmedos" },
			{ "Dieta", "Radiación estelar" },
			{ "Peligrosidad", "Baja" },
			{ "Tamaño", "1,5 m" },
		},
		XP = 60,
		Monedas = 40,
	},
	Criatura_ReptadorLunar = {
		Categoria = "Criatura",
		Nombre = "Reptador lunar",
		Descripcion = "Animal acorazado que se arrastra por las lunas rocosas y se alimenta de minerales.",
		Rareza = "Poco comun",
		Duracion = 2,
		Datos = {
			{ "Hábitat", "Lunas rocosas" },
			{ "Dieta", "Hierro y cobre" },
			{ "Peligrosidad", "Media" },
			{ "Tamaño", "2,2 m" },
		},
		XP = 35,
		Monedas = 22,
	},

	-- ===== Plantas =====
	Planta_FlorEstelar = {
		Categoria = "Planta",
		Nombre = "Flor estelar",
		Descripcion = "Flor que abre sus pétalos con la luz de las estrellas y los cierra cuando hay tormentas solares.",
		Rareza = "Poco comun",
		Duracion = 1.6,
		Datos = {
			{ "Hábitat", "Planetas de luz tenue" },
			{ "Floración", "Constante" },
			{ "Toxicidad", "Ninguna" },
			{ "Altura", "0,8 m" },
		},
		XP = 25,
		Monedas = 15,
	},
	Planta_HongoLuminoso = {
		Categoria = "Planta",
		Nombre = "Hongo luminoso",
		Descripcion = "Hongo bioluminiscente que crece en cuevas y grietas. Su luz atrae a la fauna pequeña.",
		Rareza = "Comun",
		Duracion = 1.2,
		Datos = {
			{ "Hábitat", "Cuevas y grietas" },
			{ "Luminosidad", "Alta" },
			{ "Toxicidad", "Leve" },
			{ "Altura", "0,4 m" },
		},
		XP = 12,
		Monedas = 8,
	},
}

-- Un mineral escaneable por cada tipo de nodo. La rareza sale de su peso al repartirse: cuanto menos, más raro.
local function rarezaDe(peso: number): string
	if peso >= 4 then
		return "Comun"
	elseif peso >= 2 then
		return "Poco comun"
	elseif peso >= 1.5 then
		return "Rara"
	end
	return "Epica"
end

for _, id in Minerales.Orden do
	local mineral = Minerales.Lista[id]
	local objeto = Objetos.Lista[mineral.Objeto]
	lista[`Mineral_{id}`] = {
		Categoria = "Mineral",
		Nombre = objeto.Nombre,
		Descripcion = objeto.Descripcion,
		Rareza = rarezaDe(mineral.Peso),
		Duracion = 1.4,
		Datos = {
			{ "Aparece en", table.concat(mineral.Origen, " y ") },
			{ "Botín", `{mineral.Cantidad[1]} a {mineral.Cantidad[2]} unidades` },
			{ "Dureza", tostring(mineral.Vida) },
		},
		XP = math.floor(10 + 8 / mineral.Peso),
		Monedas = math.floor(5 + 4 / mineral.Peso),
	}
end

Especies.Lista = table.freeze(lista)

-- Id de la especie de un tipo de mineral.
function Especies.IdDeMineral(tipo: string): string
	return `Mineral_{tipo}`
end

-- Todos los ids, ordenados alfabéticamente (para validadores y pruebas).
function Especies.Ids(): { string }
	local ids = {}
	for id in Especies.Lista do
		table.insert(ids, id)
	end
	table.sort(ids)
	return ids
end

return Especies
