--!strict
--[[
	Config (Combate): constantes generales del sistema de combate.

	Es la única pieza de "ajustes" que comparten servidor y cliente. Aquí solo hay números y textos:
	lo que cada habilidad hace vive en Datos/Poderes, y cómo se ve en Datos/EfectosVFX.
]]

local Config = {
	-- ===== Atributos del luchador =====
	VidaMaxima = 200, -- vida de los jugadores (Humanoid.MaxHealth)
	EnergiaMaxima = 100,
	EnergiaPorSegundo = 7, -- regeneración de energía

	-- ===== Comprobaciones del servidor =====
	-- El cliente pide una distancia de objetivo: se acepta hasta Rango * HolguraRango (latencia, redondeos)
	-- y se recorta al rango real. Por encima de eso se rechaza la petición.
	HolguraRango = 1.2,
	-- Estando ya en marcha la habilidad, cuántos studs puede haberse movido el lanzador desde el
	-- origen antes de que su golpe se cancele (impide "teletransportar" el golpe con un lag switch).
	HolguraMovimiento = 14,
	-- Studs extra con los que se compara a un objetivo con el alcance de la habilidad (su cuerpo mide algo).
	RadioCuerpo = 2.5,
	-- Máximo de pendiente (componente Y de la dirección) que se acepta al apuntar.
	PendienteMaxima = 0.45,

	-- ===== Combo =====
	-- Tiempo extra, tras terminar un golpe, en el que se puede encadenar el siguiente.
	VentanaCombo = 0.7,

	-- ===== Etiquetas =====
	-- CollectionService: todo personaje o muñeco que puede recibir daño lleva esta etiqueta.
	EtiquetaObjetivo = "ObjetivoCombate",
	-- Atributo de un muñeco con el bando al que pertenece ("Heroes", "Villanos" o "Ninguno").
	AtributoBando = "BandoCombate",

	-- ===== Muñecos de entrenamiento =====
	VidaMunieco = 600,
	SegundosRenacerMunieco = 3,
}

return table.freeze(Config)
