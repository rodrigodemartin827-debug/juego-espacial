--!strict
--[[
	PerfilEditor: lo que distingue el editor de personaje de cada bando. La interfaz (Editor/Pantalla), la escena
	(Editor/Estudio) y el servicio (Editor/ServicioEditor) son los mismos para los dos: cada uno recibe el perfil de su
	bando.

	  · Bando / CampoDatos / Remoto: a quién sirve, dónde se guarda (datos.Apariencia[CampoDatos]) y el remoto.
	  · Apariencia / Datos / Constructor: sus reglas, su catálogo y quien lo pone en un R6.
	  · Avatar: si ofrece «Usar mi avatar de Roblox» (solo Humanos).
	  · Titulo: el título de la pantalla.
	  · Nota(a, campo): texto extra para la fila de una categoría (por ejemplo «(tapado)» en un tatuaje), o nil.
	  · ImagenRueda: la textura de la rueda de color.
]]

local Apariencia = require(script.Parent.Apariencia)
local AparienciaMonstruo = require(script.Parent.AparienciaMonstruo)
local Constructor = require(script.Parent.Constructor)
local ConstructorMonstruo = require(script.Parent.ConstructorMonstruo)
local Datos = require(script.Parent.DatosHumanos)
local DatosMonstruo = require(script.Parent.DatosMonstruo)
local RecursosHumanos = require(script.Parent.RecursosHumanos)

export type Perfil = {
	Bando: string,
	CampoDatos: string,
	Remoto: string,
	Apariencia: any,
	Datos: any,
	Constructor: any,
	Avatar: boolean,
	Titulo: string?,
	Nota: ((a: any, campo: string) -> string?)?,
	ImagenRueda: string,
}

local Perfiles: { [string]: Perfil } = {}

Perfiles.Humanos = {
	Bando = "Humanos",
	CampoDatos = "Humano",
	Remoto = "GuardarAparienciaHumano",
	Apariencia = Apariencia,
	Datos = Datos,
	Constructor = Constructor,
	Avatar = true,
	Titulo = nil,
	-- Un tatuaje solo se ve con los brazos al aire: con una chaqueta de manga larga queda tapado.
	Nota = function(a: any, campo: string): string?
		if campo == "Tatuaje" and a.Tatuaje ~= "Ninguno" and not Apariencia.TatuajeVisible(a) then
			return "(tapado)"
		end
		return nil
	end,
	ImagenRueda = RecursosHumanos.Imagenes.RuedaColor,
}

Perfiles.Monstruos = {
	Bando = "Monstruos",
	CampoDatos = "Monstruo",
	Remoto = "GuardarAparienciaMonstruo",
	Apariencia = AparienciaMonstruo,
	Datos = DatosMonstruo,
	Constructor = ConstructorMonstruo,
	Avatar = false,
	Titulo = "TU MONSTRUO",
	Nota = nil,
	ImagenRueda = RecursosHumanos.Imagenes.RuedaColor,
}

return Perfiles
