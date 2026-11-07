--!strict
--[[
	Tipos: forma de los datos que se guardan de cada jugador.

	Los usan el servidor (que los carga y guarda) y el cliente (que recibe una copia para mostrarla),
	por eso viven en la carpeta compartida. Este módulo no contiene lógica, solo tipos.

	La plantilla con los valores iniciales y las reglas de validación están en el servidor:
	Servicios/ServicioDatos/Esquema.
]]

local Bandos = require(script.Parent.Parent.Juego.Bandos)

-- Cantidad que tiene el jugador de cada objeto: { [idObjeto] = cantidad }.
export type Inventario = { [string]: number }

-- Nivel de cada mejora de la nave: { [idMejora] = nivel }. Un nivel 0 significa "sin mejorar".
export type MejorasNave = { [string]: number }

-- Veces que el jugador ha escaneado cada especie: { [idEspecie] = veces }. Una especie ausente no se ha descubierto.
export type Descubrimientos = { [string]: number }

export type Datos = {
	Bando: Bandos.IdBando, -- "Ninguno" hasta que el jugador elige
	Nivel: number, -- empieza en 1
	XP: number, -- experiencia acumulada
	Monedas: number,
	Inventario: Inventario,
	MejorasNave: MejorasNave,
	Descubrimientos: Descubrimientos,
	Graficos: string, -- nivel de gráficos elegido (Graficos/Config.Orden); "" hasta que lo elige
}

return {}
