--!strict
--[[
	Bandos: los dos bandos enfrentados del juego (Héroes y Villanos) y el valor "Ninguno" para el
	jugador que todavía no ha elegido.

	Los identificadores ("Heroes", "Villanos") son los que se guardan en el DataStore y los que viajan
	por la red: no los cambies una vez publicado el juego, o los datos existentes dejarían de ser
	válidos. Para cambiar lo que ve el jugador, edita solo `Nombre` en `Bandos.Info`.
]]

export type IdBando = "Ninguno" | "Heroes" | "Villanos"

export type InfoBando = {
	Id: IdBando,
	Nombre: string, -- texto que se muestra al jugador
}

local Bandos = {}

Bandos.Ninguno = "Ninguno" :: IdBando
Bandos.Heroes = "Heroes" :: IdBando
Bandos.Villanos = "Villanos" :: IdBando

-- Información de presentación de cada bando.
Bandos.Info = {
	Ninguno = { Id = "Ninguno", Nombre = "Sin bando" },
	Heroes = { Id = "Heroes", Nombre = "Héroes" },
	Villanos = { Id = "Villanos", Nombre = "Villanos" },
} :: { [string]: InfoBando }

-- Los bandos que un jugador puede elegir ("Ninguno" no es una opción).
Bandos.Elegibles = { "Heroes", "Villanos" } :: { string }

-- Indica si `valor` es el identificador de un bando conocido (incluido "Ninguno").
function Bandos.EsValido(valor: any): boolean
	return type(valor) == "string" and Bandos.Info[valor] ~= nil
end

-- Indica si `valor` es un bando que se puede elegir (Héroes o Villanos).
function Bandos.EsElegible(valor: any): boolean
	return type(valor) == "string" and valor ~= Bandos.Ninguno and Bandos.Info[valor] ~= nil
end

return Bandos
