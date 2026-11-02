--!strict
--[[
	Animaciones: los IDs de las animaciones del juego subidas a Roblox.

	Una animación subida tiene un ID numérico propio (no el del archivo .fbx de `animaciones/`). Cuando
	subas una, pega su ID en la tabla `ID`. Mientras valga 0 la animación se considera "sin configurar"
	y `Animaciones.Obtener` devuelve nil, de modo que el juego sigue funcionando sin ella.
	Cómo importarla en Studio: ver `animaciones/README.md`.

	Uso (cliente o servidor):
		local animacion = Animaciones.Obtener("PunetazoFuerte")
		if animacion then
			local pista = humanoide.Animator:LoadAnimation(animacion)
			pista:Play()
		end
]]

export type NombreAnimacion = "PunetazoFuerte"

local Animaciones = {}

-- ID numérico de cada animación subida (0 = todavía sin subir). Edita aquí.
Animaciones.ID = {
	PunetazoFuerte = 0,
} :: { [NombreAnimacion]: number }

-- Duración aproximada de cada animación en segundos y fotograma del impacto (30 fps), para sincronizar el daño.
Animaciones.Info = {
	PunetazoFuerte = { Duracion = 40 / 30, SegundoDelImpacto = 16 / 30 },
} :: { [NombreAnimacion]: { Duracion: number, SegundoDelImpacto: number } }

-- Devuelve una instancia `Animation` lista para cargar con un Animator, o nil si aún no tiene ID.
function Animaciones.Obtener(nombre: NombreAnimacion): Animation?
	local id = Animaciones.ID[nombre]
	if id == nil or id <= 0 then
		return nil
	end
	local animacion = Instance.new("Animation")
	animacion.Name = nombre
	animacion.AnimationId = `rbxassetid://{id}`
	return animacion
end

return Animaciones
