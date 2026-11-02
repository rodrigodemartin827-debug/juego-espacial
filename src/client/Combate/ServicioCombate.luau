--!strict
--[[
	ServicioCombate (cliente): une la entrada, la interfaz, la red y los efectos.

	El cliente NO decide nada del combate: solo
	  1. PIDE usar una habilidad (hacia dónde apunta y a qué distancia) con el remoto UsarHabilidad,
	  2. REPRODUCE lo que el servidor confirma (HabilidadIniciada -> animación y efectos de carga;
	     HabilidadImpacto -> efectos de impacto, números de daño, empuje al golpeado),
	  3. MUESTRA su estado (EstadoCombate -> energía y cooldowns).

	Antes de pedir, comprueba el cooldown que sabe, por cortesía (ahorrar tráfico); el servidor lo vuelve a
	comprobar todo y es quien manda.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")

local Combate = ReplicatedStorage:WaitForChild("Shared").Combate
local Config = require(Combate.Config)
local Poderes = require(Combate.Datos.Poderes)
local Calidad = require(script.Parent.Parent.VFX.Calidad)
local Entrada = require(script.Parent.Entrada)
local Gestor = require(script.Parent.Parent.VFX.Gestor)
local Interfaz = require(script.Parent.Interfaz)
local NumerosDano = require(script.Parent.NumerosDano)
local Pantalla = require(script.Parent.Parent.VFX.Pantalla)
local Pool = require(script.Parent.Parent.VFX.Pool)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)
local Utiles = require(script.Parent.Parent.VFX.Utiles)

local ServicioCombate = {}

-- Velocidad máxima de empuje que se acepta del servidor (ante un dato absurdo, no se sale volando).
local EMPUJE_MAXIMO = 160

-- ===== Apuntar =====

local function raizLocal(): BasePart?
	local personaje = Players.LocalPlayer.Character
	return personaje and personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
end

-- En móvil no hay cursor: se ayuda apuntando al enemigo más cercano delante de la cámara.
local function enemigoCercano(origen: Vector3, rango: number): Vector3?
	local camara = workspace.CurrentCamera
	local propio = Players.LocalPlayer.Character
	if camara == nil then
		return nil
	end
	local mejor: Vector3? = nil
	local mejorDistancia = rango + 15
	for _, modelo in CollectionService:GetTagged(Config.EtiquetaObjetivo) do
		local humanoid = modelo:FindFirstChildOfClass("Humanoid")
		local raiz = modelo:FindFirstChild("HumanoidRootPart")
		if modelo ~= propio and humanoid and humanoid.Health > 0 and raiz and raiz:IsA("BasePart") then
			local hacia = raiz.Position - origen
			local distancia = hacia.Magnitude
			if distancia < mejorDistancia and distancia > 0.1 then
				local coseno = hacia.Unit:Dot(camara.CFrame.LookVector)
				if coseno > 0.55 then -- unos 55° a cada lado
					mejor = raiz.Position
					mejorDistancia = distancia
				end
			end
		end
	end
	return mejor
end

-- Dirección (unitaria) y distancia al punto que señala el jugador, recortada al rango de la habilidad.
local function apuntar(hab: Poderes.Habilidad): (Vector3, number)
	local raiz = raizLocal()
	local camara = workspace.CurrentCamera
	if raiz == nil or camara == nil then
		return Vector3.zero, 0
	end
	local origen = raiz.Position

	local punto: Vector3
	if Calidad.EsMovil then
		punto = enemigoCercano(origen, hab.Rango) or (origen + camara.CFrame.LookVector * hab.Rango)
	else
		local posicion = game:GetService("UserInputService"):GetMouseLocation()
		local rayo = camara:ViewportPointToRay(posicion.X, posicion.Y)
		local parametros = Utiles.ParametrosEscenario()
		local choque = workspace:Raycast(rayo.Origin, rayo.Direction * 800, parametros)
		punto = if choque then choque.Position else rayo.Origin + rayo.Direction * 800
	end

	local hacia = punto - origen
	if hacia.Magnitude < 0.5 then
		hacia = camara.CFrame.LookVector * hab.Rango
	end
	local plana = Vector3.new(hacia.X, 0, hacia.Z).Magnitude
	return hacia.Unit, math.min(plana, hab.Rango)
end

-- ===== Pedir una habilidad =====

local function solicitar(id: string)
	local hab = Poderes.Presentacion(id)
	if hab == nil or raizLocal() == nil then
		return
	end
	if Interfaz.EnCooldown(id) then
		return
	end
	local personaje = Players.LocalPlayer.Character
	local humanoid = personaje and personaje:FindFirstChildOfClass("Humanoid")
	if humanoid == nil or humanoid.Health <= 0 then
		return
	end

	local direccion, distancia = apuntar(hab)
	ServicioRed.Enviar("UsarHabilidad", id, direccion, distancia)
end

-- ===== Lo que confirma el servidor =====

local function esModelo(valor: any): boolean
	return typeof(valor) == "Instance" and (valor :: Instance):IsA("Model")
end

local function alIniciarHabilidad(id: any, lanzador: any, origen: any, destino: any, direccion: any)
	if type(id) ~= "string" or not esModelo(lanzador) then
		return
	end
	if typeof(origen) ~= "Vector3" or typeof(destino) ~= "Vector3" or typeof(direccion) ~= "Vector3" then
		return
	end

	-- El propio personaje se gira hacia donde lanza (su cliente es quien lo mueve).
	if lanzador == Players.LocalPlayer.Character then
		local raiz = raizLocal()
		local plana = Vector3.new(direccion.X, 0, direccion.Z)
		if raiz and plana.Magnitude > 0.05 then
			raiz.CFrame = CFrame.lookAt(raiz.Position, raiz.Position + plana)
		end
	end

	Gestor.Iniciar(id, lanzador, origen, destino, direccion)
end

local function alImpactarHabilidad(id: any, lanzador: any, punto: any, direccion: any, golpeados: any)
	if
		type(id) ~= "string"
		or not esModelo(lanzador)
		or typeof(punto) ~= "Vector3"
		or typeof(direccion) ~= "Vector3"
	then
		return
	end
	if type(golpeados) ~= "table" then
		return
	end

	local modelos: { Model } = {}
	local propio = Players.LocalPlayer.Character
	for _, golpe in golpeados do
		if type(golpe) == "table" and esModelo(golpe.Modelo) then
			local modelo = golpe.Modelo :: Model
			table.insert(modelos, modelo)
			if type(golpe.Dano) == "number" then
				NumerosDano.Mostrar(modelo, golpe.Dano)
			end

			-- Si el golpeado soy yo, mi cliente me empuja (soy el dueño de mi personaje).
			if modelo == propio and typeof(golpe.Empuje) == "Vector3" then
				local raiz = raizLocal()
				local humanoid = propio:FindFirstChildOfClass("Humanoid")
				local empuje: Vector3 = golpe.Empuje
				if raiz and humanoid and empuje.Magnitude == empuje.Magnitude then
					if empuje.Magnitude > EMPUJE_MAXIMO then
						empuje = empuje.Unit * EMPUJE_MAXIMO
					end
					humanoid:ChangeState(Enum.HumanoidStateType.Freefall)
					raiz.AssemblyLinearVelocity = empuje
				end
			end
		end
	end

	Gestor.Impacto(id, lanzador :: Model, punto, direccion, modelos)
end

-- ===== Arranque =====

--[[
	Arranca el combate del cliente. Debe llamarse una sola vez, después de ServicioRed.Iniciar().
]]
function ServicioCombate.Iniciar()
	Calidad.Iniciar()
	Pantalla.Iniciar()
	Pool.Precalentar()

	-- Se usa la barra de vida propia del combate en lugar de la de Roblox.
	pcall(function()
		StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Health, false)
	end)

	Interfaz.Iniciar(solicitar)
	Entrada.Iniciar(solicitar)

	ServicioRed.Conectar("HabilidadIniciada", alIniciarHabilidad)
	ServicioRed.Conectar("HabilidadImpacto", alImpactarHabilidad)
	ServicioRed.Conectar("EstadoCombate", Interfaz.PonerEstado)
	ServicioRed.Enviar("PedirEstadoCombate")
end

return ServicioCombate
