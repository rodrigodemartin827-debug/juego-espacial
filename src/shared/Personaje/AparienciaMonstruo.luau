--!strict
--[[
	AparienciaMonstruo: reglas sin Roblox de la apariencia de un Monstruo (se prueban con Lune). Las funciones son las
	de Personaje/FabricaApariencia (Campos, Categorias, Opciones, Buscar, Validar, Hecha, Mover, Aleatoria...).

	Una apariencia es una tabla:
	  · De opciones (un id de su lista en Personaje/DatosMonstruo): Piel, Silueta, Cuernos, Ojos, Boca, Deformacion
	    y Marcas.
	  · De colores libres ("#RRGGBB", rueda de color): ColorOjos, ColorCuernos y ColorDetalle.
	Colores(a): Cuerno, Hueso, Ojos, Piel y los roles de color fijo.
]]

local Datos = require(script.Parent.DatosMonstruo)
local Fabrica = require(script.Parent.FabricaApariencia)

export type Apariencia = {
	Piel: string,
	Silueta: string,
	Cuernos: string,
	Ojos: string,
	Boca: string,
	Deformacion: string,
	Marcas: string,
	ColorOjos: string,
	ColorCuernos: string,
	ColorDetalle: string,
}

local Apariencia: any
Apariencia = Fabrica.Crear({
	Datos = Datos,
	CamposOpcion = { "Piel", "Silueta", "Cuernos", "Ojos", "Boca", "Deformacion", "Marcas" },
	CamposColor = { "ColorOjos", "ColorCuernos", "ColorDetalle" },
	Categorias = {
		{ Campo = "Silueta", Nombre = "Silueta" },
		{ Campo = "Cuernos", Nombre = "Cuernos" },
		{ Campo = "Ojos", Nombre = "Ojos" },
		{ Campo = "Boca", Nombre = "Boca" },
		{ Campo = "Deformacion", Nombre = "Deformación" },
		{ Campo = "Marcas", Nombre = "Marcas" },
	},
	Listas = {
		Piel = Datos.Pieles,
		Silueta = Datos.Siluetas,
		Cuernos = Datos.Cuernos,
		Ojos = Datos.Ojos,
		Boca = Datos.Bocas,
		Deformacion = Datos.Deformaciones,
		Marcas = Datos.Marcas,
	},
	-- Al azar, lo «raro» suele quedarse en nada.
	Raros = { Deformacion = true, Marcas = true },
	CamposHecha = { "Piel", "Silueta" },
	Colores = function(a: any): { [string]: string }
		local colores: { [string]: string } = {
			Piel = Apariencia.Buscar("Piel", a.Piel).Hex,
			Ojos = a.ColorOjos,
			Cuerno = a.ColorCuernos,
			Hueso = a.ColorDetalle,
		}
		for rol, datos in Datos.Roles do
			if datos.Color then
				colores[rol] = datos.Color
			end
		end
		return colores
	end,
	AzarColores = function(azar: any, resultado: { [string]: string })
		local muestras = Datos.Muestras
		resultado.ColorOjos = muestras[azar:NextInteger(1, 9)] -- colores vivos
		resultado.ColorCuernos = muestras[azar:NextInteger(10, #muestras)]
		resultado.ColorDetalle = muestras[azar:NextInteger(1, #muestras)]
	end,
})

return Apariencia
