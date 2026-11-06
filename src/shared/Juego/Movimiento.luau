--!strict
--[[
	Movimiento: las animaciones de andar del personaje R6 (animaciones/movimiento, PR #17) y cuándo se usa cada una.

	Cada animación está hecha para una velocidad a la que el pie no patina (`Velocidad`, studs/s): se reproduce a
	velocidad real / Velocidad. Se elige por la rapidez del personaje:
	  · parado (menos de `Quieto`)                 → Reposo
	  · hasta `HastaAndar` (joystick a medias)     → Andar  (hecha para 7,5)
	  · hasta `HastaTrotar` (la W normal, 16)      → Trotar (hecha para 16)
	  · más (con Mayús, 28)                        → Correr (hecha para 28)
	`Histeresis`: margen para no saltar de una a otra si la velocidad ronda un límite.

	Las animaciones se cargan de ReplicatedStorage.Animaciones.Movimiento (KeyframeSequences sincronizadas por Rojo
	desde animaciones/movimiento/*.rbxmx). Para el juego publicado habrá que subirlas como Animation y poner aquí
	sus IDs (`Id`): las KeyframeSequences solo se pueden reproducir en Studio.
]]

export type Animacion = {
	Archivo: string, -- nombre de la KeyframeSequence en ReplicatedStorage.Animaciones.Movimiento
	Velocidad: number?, -- studs/s a los que está hecha (nil = no depende de la velocidad: el reposo)
	Id: string?, -- rbxassetid de la animación subida (para el juego publicado)
}

local Movimiento = {}

Movimiento.Animaciones = {
	Reposo = { Archivo = "Reposo" },
	Andar = { Archivo = "Andar", Velocidad = 7.5 },
	Trotar = { Archivo = "Trotar", Velocidad = 16 },
	Correr = { Archivo = "Correr", Velocidad = 28 },
} :: { [string]: Animacion }

Movimiento.Quieto = 0.6 -- studs/s
Movimiento.HastaAndar = 11
Movimiento.HastaTrotar = 22
Movimiento.Histeresis = 1

-- Segundos de fundido entre animaciones. Entre andar, trotar y correr el paso se conserva (todas empiezan con el
-- pie izquierdo apoyándose), así que el cambio de ritmo no da un salto de pierna.
Movimiento.FundidoReposo = 0.3
Movimiento.FundidoPaso = 0.25

return Movimiento
