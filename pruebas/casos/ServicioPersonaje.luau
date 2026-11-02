--[[
	Pruebas del ServicioPersonaje: la red de seguridad que sustituye cualquier personaje R15 por uno R6.
]]

local Entorno = require("../infraestructura/Entorno")

local RUTA = "ServerScriptService.Server.Servicios.ServicioPersonaje"

-- Crea un personaje simulado: Model con Humanoid (del tipo de rig dado), un script Animate y su posición.
local function crearPersonaje(mundo, rig: string, nombre: string, conAnimate: boolean?)
	local modelo = mundo.Instance.new("Model")
	modelo.Name = nombre
	local humanoid = mundo.Instance.new("Humanoid")
	rawset(humanoid, "RigType", { Name = rig })
	humanoid.Parent = modelo
	if conAnimate ~= false then
		local animate = mundo.Instance.new("LocalScript")
		animate.Name = "Animate"
		rawset(animate, "Source", `-- animate de {rig}`)
		animate.Parent = modelo
	end
	modelo:PivotTo(`posicion-de-{nombre}`)
	return modelo
end

-- Prepara un servidor con el servicio, un jugador y un contador de personajes R6 creados.
local function preparar()
	local entorno = Entorno.nuevo()
	local mundo = entorno.mundo
	local Servicio = entorno.servidor.requerir(RUTA)

	local creados = {}
	rawset(mundo.Players, "CreateHumanoidModelFromDescription", function(_, descripcion, rig)
		table.insert(creados, rig.Name)
		-- El modelo que crea Roblox a partir de una descripción no trae scripts.
		return crearPersonaje(mundo, rig.Name, "Generado", false)
	end)

	local jugador = mundo.unirJugador(1, "Ana")
	-- El mundo simulado no tiene mundo 3D: un Folder hace de "workspace".
	local escenario = mundo.Instance.new("Folder")
	escenario.Name = "Escenario"
	escenario.Parent = entorno.game.ReplicatedStorage
	return entorno, Servicio, jugador, escenario, creados
end

return function(Marco)
	Marco.grupo("ServicioPersonaje: fuerza el rig R6", function()
		Marco.prueba("reconoce los personajes R6 y R15", function()
			local entorno, Servicio = preparar()
			Marco.verdadero(Servicio.EsR6(crearPersonaje(entorno.mundo, "R6", "A")))
			Marco.falso(Servicio.EsR6(crearPersonaje(entorno.mundo, "R15", "B")))
			Marco.falso(Servicio.EsR6(entorno.mundo.Instance.new("Model")), "sin Humanoid no es R6")
		end)

		Marco.prueba("un personaje R15 se sustituye por uno R6 con su posición y sus scripts", function()
			local entorno, Servicio, jugador, escenario, creados = preparar()
			local r15 = crearPersonaje(entorno.mundo, "R15", "Ana")
			r15.Parent = escenario
			jugador.Character = r15

			local nuevo = Servicio.ConvertirAR6(jugador, r15)

			Marco.distinto(nuevo, nil)
			Marco.igualProfundo(creados, { "R6" }, "debe pedir un rig R6")
			Marco.igual(jugador.Character, nuevo, "el jugador pasa a controlar el personaje nuevo")
			Marco.igual(nuevo.Name, "Ana")
			Marco.igual(nuevo.Parent, escenario, "aparece donde estaba el anterior")
			Marco.igual(nuevo:GetPivot(), "posicion-de-Ana", "en la misma posición")
			Marco.esNil(r15.Parent, "el R15 desaparece")
			Marco.contiene(nuevo:FindFirstChild("Animate").Source, "R15", "se copia el script Animate")
		end)

		Marco.prueba("al aparecer un personaje R15 se convierte solo y avisa", function()
			local entorno, Servicio, jugador, escenario, creados = preparar()
			Servicio.Iniciar()

			local r15 = crearPersonaje(entorno.mundo, "R15", "Ana")
			r15.Parent = escenario
			jugador.Character = r15
			jugador.CharacterAdded:Fire(r15)

			Marco.esperarHasta(function()
				return jugador.Character ~= r15
			end, "el personaje R15 debería sustituirse")
			Marco.igualProfundo(creados, { "R6" })
			Marco.algunoContiene(entorno.mundo.Avisos, "no es R6")
		end)

		Marco.prueba("un personaje que ya es R6 no se toca ni genera avisos", function()
			local entorno, Servicio, jugador, escenario, creados = preparar()
			Servicio.Iniciar()

			local r6 = crearPersonaje(entorno.mundo, "R6", "Ana")
			r6.Parent = escenario
			jugador.Character = r6
			jugador.CharacterAdded:Fire(r6)
			Marco.dejarCorrer(5)

			Marco.igual(jugador.Character, r6)
			Marco.igual(#creados, 0)
			Marco.igual(#entorno.mundo.Avisos, 0)
		end)

		Marco.prueba("si no se puede crear el R6, el jugador conserva su personaje y se avisa", function()
			local entorno, Servicio, jugador, escenario = preparar()
			rawset(entorno.mundo.Players, "CreateHumanoidModelFromDescription", function()
				error("sin acceso")
			end)
			local r15 = crearPersonaje(entorno.mundo, "R15", "Ana")
			r15.Parent = escenario
			jugador.Character = r15

			Marco.esNil(Servicio.ConvertirAR6(jugador, r15))
			Marco.igual(jugador.Character, r15)
			Marco.algunoContiene(entorno.mundo.Avisos, "No se pudo crear el personaje R6")
		end)
	end)
end
