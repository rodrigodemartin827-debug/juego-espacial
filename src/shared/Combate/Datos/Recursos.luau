--!strict
--[[
	Recursos: TODOS los identificadores de contenido del combate en un solo sitio.

	Para cambiar el aspecto o el movimiento de un poder no hace falta tocar código: pega aquí el ID del
	asset que quieras ("rbxassetid://123456") y listo.

	  - Texturas:    imágenes de las partículas, haces y rastros.
	  - Mallas:      meshes para ondas, esferas, cortes y rocas. Cadena vacía "" = se usa una forma básica
	                 (esfera, cilindro, bloque) con el mismo tamaño, así que siempre se ve algo.
	  - Animaciones: ID de la animación de cada movimiento. Cadena vacía "" = se usa la animación
	                 provisional hecha por código (Datos/Animaciones). Con un ID, se usa ese en su lugar.
	  - Sonidos:     "" = sin sonido.

	Las texturas por defecto son las que trae el propio motor de Roblox, para que funcione sin subir nada.
]]

local Recursos = {}

Recursos.Texturas = {
	Chispa = "rbxasset://textures/particles/sparkles_main.dds",
	Humo = "rbxasset://textures/particles/smoke_main.dds",
	Fuego = "rbxasset://textures/particles/fire_main.dds",
	Polvo = "rbxasset://textures/particles/smoke_main.dds",
	Destello = "rbxasset://textures/particles/sparkles_main.dds",
	Rayo = "rbxasset://textures/particles/sparkles_main.dds", -- textura de los haces de rayo
	Rastro = "rbxasset://textures/particles/sparkles_main.dds",
	Energia = "rbxasset://textures/particles/fire_main.dds",
}

Recursos.Mallas = {
	Anillo = "", -- anillo plano (onda expansiva). Vacío: disco fino
	Esfera = "", -- esfera. Vacío: Part de forma Ball
	Corte = "", -- media luna del corte. Vacío: se dibuja con un rastro
	Roca = "", -- escombro. Vacío: bloque
}

Recursos.Animaciones = {
	-- Poderes (carga = al empezar, lanzamiento = al soltar el poder).
	Alzar_Mano = "",
	Disparo_Frente = "",
	Golpe_Suelo = "",
	Alzar_Cielo = "",
	Lanzar_Cielo = "",
	Comprimir = "",
	-- Combo cuerpo a cuerpo.
	Combo1 = "",
	Combo2 = "",
	Combo3 = "",
	Combo4 = "", -- Remate: aquí va el ID del "puñetazo fuerte" (ver animaciones/README.md)
	-- Reacción del que recibe un golpe.
	Impacto = "",
}

Recursos.Sonidos = {
	CargaRayo = "",
	DisparoRayo = "",
	ImpactoRayo = "",
	TruenoDefinitiva = "",
	CargaGravedad = "",
	ImpactoGravedad = "",
	AgujeroNegro = "",
	GolpeLigero = "",
	GolpePesado = "",
	-- Naves.
	NaveLaser = "",
	NaveImpacto = "",
	NaveEscudo = "",
	NaveChoque = "",
	NaveExplosion = "",
	NaveDespegue = "",
	NaveTurbo = "",
	AsteroideRoto = "",
	-- Exploración.
	EscanerCarga = "",
	EscanerPulso = "",
	EscanerCompleto = "",
	EscanerFallo = "",
	MinadoGolpe = "",
	MinadoRotura = "",
	CrafteoExito = "",
	-- Elección de bando.
	EleccionAnticipar = "",
	EleccionConfirmar = "",
	EleccionResaltar = "",
	EleccionAmbiente = "", -- zumbido de la grieta mientras se elige (en bucle)
}

return Recursos
