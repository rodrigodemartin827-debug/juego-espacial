--!strict
--[[
	ConfigEditor: la pantalla del editor de personaje (segundo paso de la entrada: bando → editor → gráficos →
	cinemática). Textos, pestañas, cámara y colores. Lo que se puede elegir está en Personaje/DatosHumanos.
]]

local Config = {}

-- MODO DE PRUEBAS: en Studio el editor sale cada vez que se entra (en el juego publicado, solo la primera vez).
Config.MostrarSiempreEnStudio = true

-- Pestañas, en orden. `Campo` es el de Personaje/Apariencia; `Colores` = se muestran como muestras de color.
export type Pestana = { Campo: string, Nombre: string, Colores: boolean? }
Config.Pestanas = {
	{ Campo = "Piel", Nombre = "Piel", Colores = true },
	{ Campo = "Cara", Nombre = "Cara" },
	{ Campo = "Pelo", Nombre = "Pelo" },
	{ Campo = "ColorPelo", Nombre = "Color del pelo", Colores = true },
	{ Campo = "Ropa", Nombre = "Ropa" },
	{ Campo = "ColorRopa", Nombre = "Color de la ropa", Colores = true },
	{ Campo = "ColorDetalle", Nombre = "Color de detalles", Colores = true },
	{ Campo = "Complemento", Nombre = "Complementos" },
} :: { Pestana }

Config.Textos = {
	Titulo = "TU PERSONAJE",
	Subtitulo = "Así te verán los demás. Arrastra para girarlo.",
	Aleatorio = "ALEATORIO",
	Continuar = "CONTINUAR",
}

-- Cámara: delante del personaje, a la altura del pecho, girando cuando se arrastra.
Config.Camara = {
	Distancia = 13,
	Altura = 0.6, -- sobre la raíz
	Mira = -0.3, -- punto al que mira, sobre la raíz (algo por debajo: que se vea de la cabeza a los pies)
	Desplazar = 2.2, -- studs a la derecha de la cámara: el personaje queda a la izquierda de las opciones
	Sensibilidad = 0.01, -- radianes por píxel arrastrado
	CampoVision = 45,
}

Config.Colores = {
	Fondo = "#0B0E16",
	Panel = "#141A26",
	Borde = "#2C3A52",
	Elegido = "#4DC8FF",
	Texto = "#FFFFFF",
	TextoSuave = "#A9B6CC",
}

return Config
