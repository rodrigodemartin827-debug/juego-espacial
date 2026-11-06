--!strict
--[[
	Persiana (datos): medidas, tiempos, colores, sonidos y efectos de la persiana metálica de las tiendas.

	Todo lo ajustable de la animación está aquí; el código que la reproduce (Cliente/Tiendas/Persianas) no tiene números
	propios. Las curvas (qué posición tiene la persiana en cada instante) son funciones puras en Tiendas/Persiana.

	La animación sigue las reglas de combate del proyecto, aplicadas a una persiana:
	  BAJAR    alarma y baliza roja → ANTICIPACIÓN (la persiana asoma y se recoge, como si se soltara el freno) →
	           CAÍDA acelerada → IMPACTO (congelado de un instante, polvo, chispas, golpe seco y temblor de cámara) →
	           REBOTE que se apaga → rótulo "CERRADO" en rojo.
	  SUBIR    cerrojo → DESBLOQUEO (la persiana tiembla al soltarse) → SUBIDA suave → ASENTADO (se recoge un poco más y
	           vuelve) → rótulo "ABIERTO" en verde.

	Sonidos: "" = sin sonido. Los que hay ahora son sonidos que trae el propio motor de Roblox, para que se oiga algo sin
	subir nada; CÁMBIALOS por sonidos de persiana de verdad (traqueteo metálico, golpe, cerrojo) subidos a Roblox
	("rbxassetid://...").
]]

local Persiana = {}

-- Medidas del modelo (studs). Las usa el servidor al construir la tienda (Servicios/ServicioTiendas/Modelo).
Persiana.Medidas = table.freeze({
	AnchoHueco = 16, -- ancho del hueco del escaparate que tapa la persiana
	AltoHueco = 9, -- alto desde el suelo hasta el cajón del rodillo
	Lamas = 14, -- número de lamas (más = más detalle, más piezas que mover)
	AltoBarra = 0.7, -- barra inferior, más gruesa, que asoma bajo el cajón cuando está subida
	GrosorLama = 0.35,
})

-- Segundos de cada fase.
Persiana.Tiempos = table.freeze({
	-- Bajar
	Anticipacion = 0.2, -- asoma y se recoge
	Caida = 0.42, -- caída acelerada
	Congelado = 0.07, -- hitstop: se queda clavada un instante al tocar el suelo
	Rebote = 0.38, -- rebotes que se apagan
	AmplitudAnticipacion = 0.06, -- fracción del recorrido que asoma antes de caer
	AmplitudRebote = 0.07, -- fracción del recorrido del primer rebote
	-- Subir
	Desbloqueo = 0.26, -- tiembla al soltar el cerrojo
	Subida = 0.85,
	Asentado = 0.22,
	AmplitudDesbloqueo = 0.03,
	AmplitudAsentado = 0.05,
})

-- Colores ("#RRGGBB").
Persiana.Colores = table.freeze({
	Lama = "#8A919E", -- acero galvanizado
	LamaOscura = "#6E7582", -- se alternan para que se vean las lamas
	Barra = "#3B3F48",
	Cajon = "#2A2E36",
	Abierto = "#4DF08A", -- rótulo y baliza con la tienda abierta
	Cerrado = "#FF3B4A", -- rótulo y baliza con la persiana bajada
	Polvo = "#B8AE9C",
	Chispas = "#FFC66B",
})

Persiana.Textos = table.freeze({
	Abierto = "ABIERTO",
	Cerrado = "CERRADO",
	RotuloPersiana = "CERRADO · NO SE ATIENDE A MONSTRUOS", -- pintado en la propia persiana
})

-- Sonidos (ver la nota de arriba). Volumen y Velocidad (tono) de cada uno.
Persiana.Sonidos = table.freeze({
	Alarma = { Id = "rbxasset://sounds/electronicpingshort.wav", Volumen = 0.7, Velocidad = 0.62 },
	Bajada = { Id = "rbxasset://sounds/swoosh.wav", Volumen = 0.8, Velocidad = 0.55 },
	Golpe = { Id = "rbxasset://sounds/hit.wav", Volumen = 1, Velocidad = 0.5 },
	Cerrojo = { Id = "rbxasset://sounds/clickfast.wav", Volumen = 0.9, Velocidad = 0.8 },
	Subida = { Id = "rbxasset://sounds/swoosh.wav", Volumen = 0.6, Velocidad = 0.42 },
	DistanciaMaxima = 120, -- studs: más lejos no se oye
})

-- Efectos del impacto (las cantidades se multiplican por el factor de calidad del dispositivo).
Persiana.Impacto = table.freeze({
	Polvo = 26, -- partículas de polvo a lo largo del suelo
	Chispas = 14, -- chispas que saltan de la barra
	Sacudida = { Intensidad = 2.6, Duracion = 0.32, Radio = 55 }, -- temblor de cámara (más débil cuanto más lejos)
	DestelloBaliza = 0.18, -- segundos que la baliza brilla a tope al golpear
})

-- Baliza: late mientras la persiana está bajada.
Persiana.Baliza = table.freeze({
	LatidosPorSegundo = 2.2,
	BrilloMin = 0.6,
	BrilloMax = 4,
	Alcance = 22,
})

-- Distancia (studs) a la que el cliente deja de animar la baliza para ahorrar en móvil.
Persiana.DistanciaAnimacion = 180

return table.freeze(Persiana)
