--!strict
--[[
	Config (Exploración): constantes del escáner de mano, la minería, el inventario y el crafteo.

	Aquí solo hay números y nombres que NO dependen de las mejoras ni de las recetas:
	  - lo que cambia con la mejora Escáner (alcance y velocidad del escáner) está en Naves/Datos/Mejoras,
	  - lo que cambia con la mejora Carga (espacio del inventario) también,
	  - las recetas de crafteo están en Exploracion/Datos/Recetas.
	Lo comparten servidor y cliente.
]]

local Config = {
	-- ===== Etiquetas (CollectionService) y atributos =====
	EtiquetaEscaneable = "Escaneable", -- todo lo que se puede analizar con el escáner
	AtributoEspecie = "EspecieId", -- en lo escaneable: id en Datos/Especies
	EtiquetaMineral = "Mineral", -- todo nodo de mineral que se puede picar
	AtributoMineralTipo = "MineralTipo", -- en el nodo: id en Datos/Minerales
	AtributoMineralVida = "MineralVida", -- en el nodo: vida que le queda
	AtributoMineralAgotado = "MineralAgotado", -- en el nodo: true mientras espera a reaparecer
	EtiquetaMesa = "MesaCrafteo", -- toda mesa de crafteo
	AtributoPilotando = "Pilotando", -- en el personaje: true mientras va dentro de una nave (ver Naves/Config)

	-- ===== Escáner de mano =====
	HolguraAlcance = 1.2, -- el servidor acepta hasta alcance * esto (latencia y movimiento)
	EnfriamientoEscaner = 0.6, -- segundos entre dos escaneos del mismo jugador
	DuracionMinimaEscaneo = 0.5, -- por muy rápido que sea el escáner, un análisis nunca dura menos
	IntervaloVigilanciaEscaner = 0.1, -- cada cuánto revisa el servidor los escaneos en curso
	AnguloAyudaApuntado = 12, -- grados: el cliente "pega" la mira al objetivo escaneable más cercano a ella
	-- Qué fracción de la recompensa se cobra al repetir un escaneo (1 = completa). Se queda en el último valor.
	RecompensaRepeticion = { 0.25, 0.1, 0.05 },

	-- ===== Minería =====
	AlcancePicado = 11, -- studs desde el personaje hasta la superficie del mineral
	CadenciaPicado = 0.45, -- segundos entre dos golpes de pico del mismo jugador
	DanoPicadoBase = 8, -- daño de cada golpe
	DanoPicadoPorNivelJugador = 0.5, -- daño extra por cada nivel del jugador
	DanoNaveMineralFactor = 1.5, -- los láseres de la nave rompen el mineral más deprisa que el pico (× daño del arma)
	SegundosRenacerMineral = 45, -- tiempo hasta que un nodo agotado vuelve a aparecer

	-- ===== Inventario =====
	VolumenPorDefecto = 1, -- espacio que ocupa cada unidad de un objeto que no indica el suyo

	-- ===== Crafteo =====
	AlcanceMesa = 14, -- studs: distancia máxima a una mesa de crafteo para usarla
	CantidadMaximaPorPeticion = 20, -- unidades de un objeto que se pueden fabricar de una vez
}

return table.freeze(Config)
