--!strict
--[[
	Bandos: los dos bandos enfrentados del juego (Humanos y Monstruos) y el valor "Ninguno" para el
	jugador que todavía no ha elegido.

	Los identificadores ("Humanos", "Monstruos") son los que se guardan en el DataStore y los que viajan
	por la red: no los cambies una vez publicado el juego, o los datos existentes dejarían de ser
	válidos (si hiciera falta, con una migración en ServicioDatos/Esquema, como la de la versión 2, que
	pasó de Heroes/Villanos a Humanos/Monstruos). Para cambiar lo que ve el jugador, edita solo `Nombre`
	en `Bandos.Info`.
]]

export type IdBando = "Ninguno" | "Humanos" | "Monstruos"

export type InfoBando = {
	Id: IdBando,
	Nombre: string, -- texto que se muestra al jugador
}

local Bandos = {}

Bandos.Ninguno = "Ninguno" :: IdBando
Bandos.Humanos = "Humanos" :: IdBando
Bandos.Monstruos = "Monstruos" :: IdBando

-- Información de presentación de cada bando.
Bandos.Info = {
	Ninguno = { Id = "Ninguno", Nombre = "Sin bando" },
	Humanos = { Id = "Humanos", Nombre = "Humanos" },
	Monstruos = { Id = "Monstruos", Nombre = "Monstruos" },
} :: { [string]: InfoBando }

-- Los bandos que un jugador puede elegir ("Ninguno" no es una opción).
Bandos.Elegibles = { "Humanos", "Monstruos" } :: { string }

-- Indica si `valor` es el identificador de un bando conocido (incluido "Ninguno").
function Bandos.EsValido(valor: any): boolean
	return type(valor) == "string" and Bandos.Info[valor] ~= nil
end

-- Indica si `valor` es un bando que se puede elegir (Humanos o Monstruos).
function Bandos.EsElegible(valor: any): boolean
	return type(valor) == "string" and valor ~= Bandos.Ninguno and Bandos.Info[valor] ~= nil
end

return Bandos
