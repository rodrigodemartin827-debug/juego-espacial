--!strict
--[[
	Apariencia (Humanos): reglas sin Roblox (se prueban con Lune). Las comunes a los dos bandos están en
	Personaje/FabricaApariencia (la lista de funciones, ahí); aquí solo lo propio de los Humanos.

	Una apariencia es una tabla:
	  · De opciones (un id de su lista en Personaje/DatosHumanos): Piel, Cabello, Cejas, Ojos, Nariz, Boca, Chaqueta,
	    Pantalon, Accesorio, Barba, Cicatriz, Tatuaje y Complexion.
	  · De colores libres ("#RRGGBB", rueda de color): ColorPelo, ColorChaqueta, ColorPantalon y ColorDetalle.
	  · TatuajeVisible(a): ¿se ve el tatuaje? Solo con los brazos al aire.
	Colores(a): Pelo, Chaqueta, Pantalon, Detalle, Piel y los roles de color fijo.
]]

local Datos = require(script.Parent.DatosHumanos)
local Fabrica = require(script.Parent.FabricaApariencia)

export type Apariencia = {
	Piel: string,
	Cabello: string,
	Cejas: string,
	Ojos: string,
	Nariz: string,
	Boca: string,
	Chaqueta: string,
	Pantalon: string,
	Accesorio: string,
	Barba: string,
	Cicatriz: string,
	Tatuaje: string,
	Complexion: string,
	ColorPelo: string,
	ColorChaqueta: string,
	ColorPantalon: string,
	ColorDetalle: string,
}

export type Categoria = Fabrica.Categoria

local Apariencia: any
Apariencia = Fabrica.Crear({
	Datos = Datos,
	CamposOpcion = {
		"Piel",
		"Cabello",
		"Cejas",
		"Ojos",
		"Nariz",
		"Boca",
		"Chaqueta",
		"Pantalon",
		"Accesorio",
		"Barba",
		"Cicatriz",
		"Tatuaje",
		"Complexion",
	},
	CamposColor = { "ColorPelo", "ColorChaqueta", "ColorPantalon", "ColorDetalle" },
	Categorias = {
		{ Campo = "Complexion", Nombre = "Complexión" },
		{ Campo = "Cabello", Nombre = "Cabello" },
		{ Campo = "Barba", Nombre = "Vello facial" },
		{ Campo = "Cejas", Nombre = "Cejas" },
		{ Campo = "Ojos", Nombre = "Ojos" },
		{ Campo = "Nariz", Nombre = "Nariz" },
		{ Campo = "Boca", Nombre = "Boca" },
		{ Campo = "Cicatriz", Nombre = "Cicatriz" },
		{ Campo = "Chaqueta", Nombre = "Chaqueta" },
		{ Campo = "Pantalon", Nombre = "Pantalón" },
		{ Campo = "Tatuaje", Nombre = "Tatuaje" },
		{ Campo = "Accesorio", Nombre = "Accesorio" },
	},
	Listas = {
		Piel = Datos.Pieles,
		Cabello = Datos.Cabellos,
		Cejas = Datos.Cejas,
		Ojos = Datos.Ojos,
		Nariz = Datos.Narices,
		Boca = Datos.Bocas,
		Chaqueta = Datos.Chaquetas,
		Pantalon = Datos.Pantalones,
		Accesorio = Datos.Accesorios,
		Barba = Datos.Barbas,
		Cicatriz = Datos.Cicatrices,
		Tatuaje = Datos.Tatuajes,
		Complexion = Datos.Complexiones,
	},
	-- Estos campos, al azar, suelen quedarse en «nada» (si no, casi todos los personajes aleatorios llevarían cicatriz,
	-- tatuaje y barba).
	Raros = { Barba = true, Cicatriz = true, Tatuaje = true },
	-- Un jugador con el editor anterior (sin Chaqueta) vuelve a pasar por él.
	CamposHecha = { "Piel", "Chaqueta" },
	Colores = function(a: any): { [string]: string }
		local colores: { [string]: string } = {
			Piel = Apariencia.Buscar("Piel", a.Piel).Hex,
			Pelo = a.ColorPelo,
			Chaqueta = a.ColorChaqueta,
			Pantalon = a.ColorPantalon,
			Detalle = a.ColorDetalle,
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
		-- El pelo casi siempre de un color natural (las seis primeras muestras); a veces, de fantasía.
		local natural = azar:NextInteger(1, 5) <= 4
		resultado.ColorPelo = muestras[if natural then azar:NextInteger(1, 6) else azar:NextInteger(7, #muestras)]
		resultado.ColorChaqueta = muestras[azar:NextInteger(7, #muestras)]
		resultado.ColorPantalon = muestras[azar:NextInteger(7, #muestras)]
		resultado.ColorDetalle = muestras[azar:NextInteger(7, #muestras)]
	end,
})

-- ¿Se ve el tatuaje? Solo con los brazos al aire (la chaqueta elegida es de manga corta o sin mangas).
function Apariencia.TatuajeVisible(a: Apariencia): boolean
	local chaqueta = Apariencia.Buscar("Chaqueta", a.Chaqueta)
	return chaqueta ~= nil and chaqueta.Brazos == "Piel"
end

return Apariencia
