--!strict
--[[
	ServicioPersonaje: garantiza que TODOS los personajes de los jugadores son R6.

	El juego entero (animaciones del combate, anclas de los efectos, hitboxes) está hecho para el rig R6:
	Torso, Head, "Right Arm", "Left Arm", "Right Leg", "Left Leg" y HumanoidRootPart.

	La forma correcta de fijar R6 es la configuración del juego (Game Settings → Avatar → Avatar Type = R6;
	ver el README). Pero ese ajuste vive en la web de Roblox, no en el código del lugar ni en Rojo, así que
	puede olvidarse. Este servicio es la red de seguridad: si aparece un personaje R15, lo sustituye al
	instante por un R6 con el mismo aspecto, en la misma posición y con los mismos scripts.

	Es inofensivo cuando el juego ya está configurado en R6: no hace nada.
]]

local Players = game:GetService("Players")

local ServicioPersonaje = {}

-- ¿Es este personaje R6? (Sin Humanoid no se puede saber: se trata como "no R6" para que se intente corregir.)
function ServicioPersonaje.EsR6(personaje: Model): boolean
	local humanoid = personaje:FindFirstChildOfClass("Humanoid")
	return humanoid ~= nil and humanoid.RigType.Name == "R6"
end

-- Aspecto actual del personaje (ropa, colores, accesorios) para repetirlo en el rig R6.
local function descripcionDe(humanoid: Humanoid): HumanoidDescription
	local ok, descripcion = pcall(function()
		return humanoid:GetAppliedDescription()
	end)
	if ok and descripcion then
		return descripcion
	end
	return Instance.new("HumanoidDescription")
end

--[[
	Sustituye un personaje R15 por uno R6 y se lo asigna al jugador. Devuelve el personaje nuevo o nil si no
	se pudo (en ese caso el jugador sigue con el que tenía, que es mejor que dejarle sin personaje).
]]
function ServicioPersonaje.ConvertirAR6(jugador: Player, personaje: Model): Model?
	local humanoid = personaje:FindFirstChildOfClass("Humanoid")
	local padre = personaje.Parent
	if humanoid == nil or padre == nil then
		return nil
	end

	local ok, nuevo = pcall(function()
		return Players:CreateHumanoidModelFromDescription(descripcionDe(humanoid), Enum.HumanoidRigType.R6)
	end)
	if not ok or nuevo == nil then
		warn(`[ServicioPersonaje] No se pudo crear el personaje R6 de {jugador.Name}: {nuevo}`)
		return nil
	end

	nuevo.Name = personaje.Name
	-- Los scripts del personaje (Animate, los de StarterCharacterScripts...) se copian: una copia nueva
	-- arranca desde cero y ya ve el rig R6.
	for _, hijo in personaje:GetChildren() do
		if hijo:IsA("LuaSourceContainer") then
			hijo:Clone().Parent = nuevo
		end
	end
	nuevo:PivotTo(personaje:GetPivot())

	jugador.Character = nuevo
	nuevo.Parent = padre
	personaje:Destroy()
	return nuevo
end

local function alAparecerPersonaje(jugador: Player, personaje: Model)
	if personaje.Parent == nil then
		return
	end
	if ServicioPersonaje.EsR6(personaje) then
		return
	end
	warn(
		`[ServicioPersonaje] {jugador.Name} apareció con un personaje que no es R6: se sustituye. `
			.. "Pon Avatar Type = R6 en la configuración del juego (ver README)."
	)
	ServicioPersonaje.ConvertirAR6(jugador, personaje)
end

local function alEntrarJugador(jugador: Player)
	jugador.CharacterAdded:Connect(function(personaje)
		-- Diferido: el personaje acaba de asignarse y puede no estar completo ni en el mundo todavía.
		task.defer(alAparecerPersonaje, jugador, personaje)
	end)
	if jugador.Character then
		task.defer(alAparecerPersonaje, jugador, jugador.Character)
	end
end

function ServicioPersonaje.Iniciar()
	Players.PlayerAdded:Connect(alEntrarJugador)
	for _, jugador in Players:GetPlayers() do
		alEntrarJugador(jugador)
	end
end

return ServicioPersonaje
