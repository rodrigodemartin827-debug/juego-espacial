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

	Cada animación tiene su `Id`: son las de animaciones/movimiento/*.rbxmx subidas al grupo con
	`herramientas/subir_modelos --animaciones` (los IDs también están en animaciones/movimiento/datos/ids_modelos.json).
	Con `Id` se usa siempre esa (así se ven igual en Studio y en el juego publicado, y no salen las de Roblox por
	defecto). Sin `Id` (una animación nueva aún sin subir), en Studio se carga la KeyframeSequence de
	ReplicatedStorage.Animaciones.Movimiento (sincronizada por Rojo); fuera de Studio no hay nada que reproducir.
]]

export type Animacion = {
	Archivo: string, -- nombre de la KeyframeSequence en ReplicatedStorage.Animaciones.Movimiento
	Velocidad: number?, -- studs/s a los que está hecha (nil = no depende de la velocidad: el reposo)
	Id: string?, -- rbxassetid de la animación subida (para el juego publicado)
}

local Movimiento = {}

Movimiento.Animaciones = {
	Reposo = { Archivo = "Reposo", Id = "rbxassetid://120420854493370" },
	Andar = { Archivo = "Andar", Velocidad = 7.5, Id = "rbxassetid://86902537014363" },
	Trotar = { Archivo = "Trotar", Velocidad = 16, Id = "rbxassetid://87355423492577" },
	Correr = { Archivo = "Correr", Velocidad = 28, Id = "rbxassetid://71475396715695" },
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
