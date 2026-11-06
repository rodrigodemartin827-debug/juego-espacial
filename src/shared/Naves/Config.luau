--!strict
--[[
	Config (Naves): constantes generales del sistema de naves.

	Aquí solo hay números y textos que NO dependen de las mejoras (esos están en Datos/Mejoras): la
	física del vuelo, las reglas de choque y las comprobaciones del servidor. Es la única pieza de "ajustes"
	que comparten servidor y cliente.
]]

local Config = {
	-- ===== Vuelo (el cliente del piloto simula la nave; el servidor solo la vigila) =====
	GiroMaximo = 2.4, -- radianes por segundo que puede girar (guiñada y cabeceo)
	CabeceoMaximo = math.rad(80), -- no se puede mirar más arriba/abajo que esto (evita la inversión)
	FraccionLateral = 0.6, -- velocidad máxima de los desplazamientos laterales y verticales, respecto a la de avance
	FraccionMarchaAtras = 0.5, -- ídem, marcha atrás
	FrenadoEstabilizador = 1.4, -- sin órdenes, la nave se frena con esta fuerza (veces la aceleración)
	SensibilidadRaton = 0.0028, -- radianes por píxel
	SensibilidadTactil = 0.0042, -- radianes por píxel al arrastrar el dedo

	-- ===== Turbo =====
	TurboConsumo = 30, -- energía de turbo que se gasta por segundo mientras está activo
	TurboRegeneracion = 14, -- energía de turbo que se recupera por segundo
	TurboMinimo = 12, -- energía mínima para poder activarlo

	-- ===== Comprobaciones del servidor =====
	IntervaloVigilancia = 0.2, -- cada cuántos segundos se revisa la posición de cada nave
	HolguraVelocidad = 1.35, -- se acepta moverse hasta velocidad máxima * esto (latencia, física del cliente)
	MargenPosicion = 10, -- studs extra por revisión antes de considerar un salto de posición
	AvisosParaCorregir = 3, -- revisiones seguidas fuera de rango antes de devolver la nave a su sitio
	-- Distancia máxima al centro del mundo antes de devolverla. Abarca los planetas de bando, el sol y el agujero
	-- negro (Planetas/Datos); a esta distancia la coma flotante de Roblox aún tiene precisión de sobra.
	RadioMundo = 48000,
	DtMaximo = 1.5, -- una revisión nunca da más margen que el de este tiempo

	-- ===== Nave =====
	RadioNave = 4.5, -- esfera que se usa para los choques
	SegundosInmunidadInicial = 3, -- tras despegar no se recibe daño
	SegundosRenacer = 4, -- espera tras ser destruida antes de poder volver a despegar
	SegundosEntreDespegues = 1.5,
	SegundosArranque = 1.4, -- desde que el piloto sube hasta que los motores le dejan volar
	SegundosSinDanoParaAterrizar = 4, -- no se puede huir de un combate aterrizando al instante

	-- ===== Choques con asteroides =====
	VelocidadMinimaChoque = 14, -- por debajo de esta velocidad un roce no hace daño
	DanoPorVelocidad = 0.5, -- daño por cada stud/s por encima del mínimo
	DanoChoqueMaximo = 140, -- tope de daño de un solo choque
	EnfriamientoChoque = 0.7, -- segundos entre dos daños de choque a la misma nave
	Elasticidad = 0.45, -- cuánto rebota (1 = rebote perfecto)
	ImpulsoSeparacion = 12, -- studs/s mínimos con los que sale despedida tras un choque

	-- ===== Armas =====
	ConoDisparo = 18, -- grados que puede desviarse un disparo respecto a la proa de la nave
	HolguraCadencia = 0.85, -- se acepta disparar cuando ha pasado esta fracción del intervalo (jitter de red)
	VelocidadProyectil = 520, -- studs/s (solo decide el retraso entre disparo e impacto)
	DanoAsteroideFactor = 1, -- multiplica el daño del arma contra asteroides

	-- ===== Etiquetas y nombres =====
	EtiquetaNave = "NaveEspacial", -- CollectionService: todo modelo de nave
	EtiquetaAsteroide = "Asteroide", -- CollectionService: todo asteroide (modelo)
	AtributoPiloto = "PilotoUserId", -- en el modelo de la nave: el UserId de quien la pilota
	AtributoPilotando = "Pilotando", -- en el personaje: true mientras va dentro de una nave
	GrupoNaves = "NavesEspaciales", -- grupo de colisión de naves y pilotos
	GrupoAsteroides = "AsteroidesEspaciales", -- grupo de colisión de asteroides

	-- ===== Asteroides =====
	SegundosRenacerAsteroide = 25,
}

return table.freeze(Config)
