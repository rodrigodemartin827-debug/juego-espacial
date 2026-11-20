--!strict
--[[
	FilaMiembro: una fila de la tabla de la tripulación.

	  RANGO          NOMBRE          NIVEL   ESTADO
	  (estrella) Líder   Rodrixx_777  127   ● Online
	  (espada) Oficial   xDarkStar     98   ● AFK
	  · Miembro      SpaceCat_22      54   ● Offline  hace 2h

	  - Líder en dorado con estrella, oficial en cian con espada, miembro en gris con un punto.
	  - Estado: círculo (Frame con UICorner 1,0) verde / ámbar / gris, más "hace X" si está desconectado.
	  - Filas alternas con fondo algo distinto; tu fila lleva una barrita cian a la izquierda.
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local IconBuilder = require(script.Parent.Parent.Iconos.IconBuilder)
local DatosDemo = require(script.Parent.Parent.Datos.DatosDemo)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores

local FilaMiembro = {}

-- Anchos de las columnas (los usa también la cabecera de la tabla).
FilaMiembro.Columnas = { Rango = 116, Nivel = 64, Estado = 150 }

function FilaMiembro.Crear(padre: Instance, miembro: DatosDemo.Miembro, indice: number): Frame
	local rango = DatosDemo.RangosClan[miembro.Rango] or DatosDemo.RangosClan.Miembro
	local colorRango = (Theme.Colores :: any)[rango.Color] or C.Gris
	local col = FilaMiembro.Columnas

	local fila = P.Marco(padre, {
		Nombre = miembro.Nombre,
		Tamano = UDim2.new(1, 0, 0, 30),
		Color = C.Blanco,
		Transparencia = if indice % 2 == 0 then Theme.Alpha.FilaAlterna else 1,
		Orden = indice,
		Z = 4,
	})
	P.Marco(fila, {
		Nombre = "Linea",
		Tamano = UDim2.new(1, 0, 0, 1),
		Posicion = UDim2.fromScale(0, 1),
		Ancla = Vector2.new(0, 1),
		Color = C.Blanco,
		Transparencia = 0.975,
		Z = 5,
	})
	if miembro.Tu then
		local barra = P.Marco(fila, {
			Nombre = "Tu",
			Tamano = UDim2.new(0, 2.5, 1, -8),
			Posicion = UDim2.fromOffset(0, 4),
			Color = C.Acento,
			Radio = UDim.new(1, 0),
			Z = 6,
		})
		P.Borde(barra, C.Acento, 0.6, 2)
	end

	-- Rango: icono (o punto) + nombre del rango.
	local celdaRango = P.Marco(
		fila,
		{ Nombre = "Rango", Tamano = UDim2.new(0, col.Rango, 1, 0), Posicion = UDim2.fromOffset(12, 0), Z = 5 }
	)
	P.Lista(celdaRango, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	if rango.Icono then
		IconBuilder.Icono(celdaRango, rango.Icono, { Tamano = 11, Color = colorRango, Orden = 1, Z = 6 })
	else
		local hueco = P.Marco(celdaRango, { Tamano = UDim2.fromOffset(11, 11), Orden = 1, Z = 6 })
		P.Marco(hueco, {
			Tamano = UDim2.fromOffset(5, 5),
			Posicion = UDim2.fromScale(0.5, 0.5),
			Ancla = Vector2.new(0.5, 0.5),
			Color = colorRango,
			Radio = UDim.new(1, 0),
			Z = 6,
		})
	end
	P.Texto(celdaRango, {
		Texto = rango.Nombre,
		Tamano = Theme.Texto.Pequeno + 0.5,
		Fuente = Theme.Fuentes.Negrita,
		Color = colorRango,
		Orden = 2,
		Z = 6,
	})

	-- Nombre (el líder en dorado y los oficiales en cian).
	P.Texto(fila, {
		Nombre = "Nombre",
		Texto = miembro.Nombre,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = if miembro.Rango == "Miembro" then Theme.Fuentes.Stats else Theme.Fuentes.Negrita,
		Color = if miembro.Rango == "Miembro" then C.TextoPrincipal else colorRango,
		Posicion = UDim2.new(0, 12 + col.Rango, 0.5, 0),
		Ancla = Vector2.new(0, 0.5),
		Z = 5,
	})

	P.Texto(fila, {
		Nombre = "Nivel",
		Texto = tostring(miembro.Nivel),
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		AlineacionX = Enum.TextXAlignment.Center,
		Caja = UDim2.new(0, col.Nivel, 1, 0),
		Posicion = UDim2.new(1, -(12 + col.Estado + col.Nivel), 0, 0),
		Z = 5,
	})

	-- Estado: círculo de color + texto (+ "hace X").
	local colorEstado = Theme.EstadoMiembro[miembro.Estado] or C.Offline
	local celdaEstado = P.Marco(fila, {
		Nombre = "Estado",
		Tamano = UDim2.new(0, col.Estado, 1, 0),
		Posicion = UDim2.new(1, -(12 + col.Estado), 0, 0),
		Z = 5,
	})
	P.Lista(celdaEstado, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	local punto = P.Marco(celdaEstado, {
		Nombre = "Punto",
		Tamano = UDim2.fromOffset(7, 7),
		Color = colorEstado,
		Radio = UDim.new(1, 0),
		Orden = 1,
		Z = 6,
	})
	if miembro.Estado ~= "Offline" then
		P.Borde(punto, colorEstado, 0.5, 2)
	end
	P.Texto(
		celdaEstado,
		{ Texto = miembro.Estado, Tamano = Theme.Texto.Cuerpo, Fuente = Theme.Fuentes.Stats, Orden = 2, Z = 6 }
	)
	if miembro.Hace then
		P.Texto(celdaEstado, {
			Texto = miembro.Hace,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Titulo,
			Color = C.TextoSecundario,
			Transparencia = Theme.Alpha.TextoSecundario,
			Orden = 3,
			Z = 6,
		})
	end
	return fila
end

return FilaMiembro
