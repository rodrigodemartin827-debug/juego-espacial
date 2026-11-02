--!strict
--[[
	ServicioCrafteo: la mesa de crafteo, validada en el servidor.

	El cliente solo pide `FabricarReceta(idReceta, cantidad)`. El servidor, en este orden:
	  1. comprueba que el jugador tenga datos, esté vivo, a pie y JUNTO A UNA MESA (Config.AlcanceMesa);
	  2. calcula con las reglas compartidas (Exploracion/Crafteo.Planificar) si se puede: materiales, monedas, nivel
	     máximo de la mejora y espacio en la bodega (que sale de la mejora Carga);
	  3. si se puede, cobra y entrega en el MISMO instante, sin esperas entre medias (Crafteo.Aplicar), de modo que
	     tampoco se pueden duplicar objetos pidiendo dos veces a la vez;
	  4. avisa al cliente del resultado, le reenvía sus datos, recalcula la nave si subió una mejora y guarda.

	Las recetas están en Exploracion/Datos/Recetas: añadir o equilibrar una no requiere tocar este servicio.

	`CrearMesa` construye una mesa con su ProximityPrompt; al usarla se abre el panel en el cliente (`AbrirMesaCrafteo`).
]]

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local Config = require(Shared.Exploracion.Config)
local Crafteo = require(Shared.Exploracion.Crafteo)
local Estadisticas = require(Shared.Naves.Estadisticas)
local ServicioDatos = require(script.Parent.ServicioDatos)
local ServicioNaves = require(script.Parent.ServicioNaves)
local ServicioRed = require(script.Parent.ServicioRed)
local ServicioReplicacion = require(script.Parent.ServicioReplicacion)

local ServicioCrafteo = {}

-- ¿Está el jugador a menos de Config.AlcanceMesa de alguna mesa?
local function cercaDeMesa(personaje: Model): boolean
	local raiz = personaje:FindFirstChild("HumanoidRootPart")
	if raiz == nil or not raiz:IsA("BasePart") then
		return false
	end
	for _, mesa in CollectionService:GetTagged(Config.EtiquetaMesa) do
		if mesa:IsDescendantOf(workspace) then
			local posicion = if mesa:IsA("Model")
				then mesa:GetPivot().Position
				elseif mesa:IsA("BasePart") then mesa.Position
				else nil
			if
				posicion
				and ((raiz :: BasePart).Position - posicion).Magnitude <= Config.AlcanceMesa * Config.HolguraAlcance
			then
				return true
			end
		end
	end
	return false
end

local function responder(jugador: Player, receta: string, ok: boolean, mensaje: string?)
	ServicioRed.EnviarACliente(jugador, "ResultadoCrafteo", receta, ok, mensaje)
end

-- Petición del cliente.
local function fabricar(jugador: Player, idReceta: string, cantidad: number?)
	local datos = ServicioDatos.ObtenerDatos(jugador)
	local personaje = jugador.Character
	local humanoid = if personaje then personaje:FindFirstChildOfClass("Humanoid") else nil
	if datos == nil or personaje == nil or humanoid == nil or humanoid.Health <= 0 then
		return
	end
	if personaje:GetAttribute(Config.AtributoPilotando) == true then
		responder(jugador, idReceta, false, "Aterriza para usar la mesa de crafteo")
		return
	end
	if not cercaDeMesa(personaje) then
		responder(jugador, idReceta, false, "Estás demasiado lejos de una mesa de crafteo")
		return
	end

	local capacidad = Estadisticas.Calcular(datos.MejorasNave).Capacidad
	local plan = Crafteo.Planificar(datos, idReceta, capacidad, cantidad)
	if not plan.Ok then
		responder(jugador, idReceta, false, Crafteo.Mensajes[plan.Motivo :: string])
		return
	end

	-- Comprobación y cobro seguidos, sin ceder el hilo: nadie puede colarse entre medias.
	if not Crafteo.Aplicar(datos, plan, capacidad) then
		responder(jugador, idReceta, false, "No se pudo fabricar, inténtalo de nuevo")
		return
	end

	responder(jugador, idReceta, true, nil)
	ServicioReplicacion.EnviarDatos(jugador)
	if plan.Mejora then
		ServicioNaves.ActualizarMejoras(jugador) -- por si hay una nave en vuelo; si no, no hace nada
	end
	-- Una compra no debe perderse si el servidor se cae.
	task.spawn(ServicioDatos.GuardarAhora, jugador)
end

--[[
	Construye una mesa de crafteo en `posicion` (sobre el suelo) y devuelve su modelo. Al usar su ProximityPrompt se abre el
	panel de recetas en el cliente de quien la usa.
]]
function ServicioCrafteo.CrearMesa(padre: Instance, posicion: Vector3): Model
	local mesa = Instance.new("Model")
	mesa.Name = "MesaCrafteo"

	local tablero = Instance.new("Part")
	tablero.Name = "Tablero"
	tablero.Size = Vector3.new(7, 0.8, 4)
	tablero.Position = posicion + Vector3.new(0, 3.4, 0)
	tablero.Color = Color3.fromRGB(70, 74, 92)
	tablero.Material = Enum.Material.Metal
	tablero.Anchored = true
	tablero.Parent = mesa
	mesa.PrimaryPart = tablero

	-- Cuatro patas.
	for _, lado in
		{ Vector3.new(-3, 0, -1.5), Vector3.new(3, 0, -1.5), Vector3.new(-3, 0, 1.5), Vector3.new(3, 0, 1.5) }
	do
		local pata = Instance.new("Part")
		pata.Name = "Pata"
		pata.Size = Vector3.new(0.6, 3, 0.6)
		pata.Position = posicion + Vector3.new(lado.X, 1.5, lado.Z)
		pata.Color = Color3.fromRGB(45, 48, 62)
		pata.Material = Enum.Material.Metal
		pata.Anchored = true
		pata.Parent = mesa
	end

	-- Un holograma sobre el tablero que indica que es una mesa de trabajo.
	local holograma = Instance.new("Part")
	holograma.Name = "Holograma"
	holograma.Shape = Enum.PartType.Ball
	holograma.Size = Vector3.one * 1.6
	holograma.Position = posicion + Vector3.new(0, 5.6, 0)
	holograma.Color = Color3.fromRGB(77, 240, 255)
	holograma.Material = Enum.Material.Neon
	holograma.Transparency = 0.35
	holograma.Anchored = true
	holograma.CanCollide = false
	holograma.CanQuery = false
	holograma.Parent = mesa
	local luz = Instance.new("PointLight")
	luz.Color = holograma.Color
	luz.Range = 16
	luz.Brightness = 2
	luz.Parent = holograma

	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText = "Fabricar"
	prompt.ObjectText = "Mesa de crafteo"
	prompt.HoldDuration = 0.2
	prompt.MaxActivationDistance = Config.AlcanceMesa - 3
	prompt.RequiresLineOfSight = false
	prompt.Parent = tablero
	prompt.Triggered:Connect(function(jugador: Player)
		ServicioRed.EnviarACliente(jugador, "AbrirMesaCrafteo")
	end)

	CollectionService:AddTag(mesa, Config.EtiquetaMesa)
	mesa.Parent = padre
	return mesa
end

-- Registra la petición del cliente. Debe llamarse una vez, después de ServicioRed.Iniciar().
function ServicioCrafteo.Iniciar()
	ServicioRed.Conectar("FabricarReceta", fabricar)
end

return ServicioCrafteo
