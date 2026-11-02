--!strict
--[[
	ServicioPlanetas (cliente): todo lo que el jugador ve de los planetas, el sol y el agujero negro.

	  Cuerpos          los cuerpos celestes en 3D (en el espacio) o en el cielo (en una superficie)
	  Ambiente         la luz, el cielo y la atmósfera de la zona en la que está la cámara
	  Fundido          la pantalla negra de las transiciones que manda el servidor (TransicionPlaneta)
	  Indicadores      temperatura del casco y atracción gravitatoria mientras se pilota
	  EfectosEntorno   los VFX del calor, la atracción, la entrada en la atmósfera y la absorción

	El cliente no decide nada: la zona la calcula con las mismas cuentas que el servidor (Planetas/Espacio) solo
	para saber qué dibujar, y las transiciones, el calor y el daño los decide el servidor.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Datos = require(Shared.Planetas.Datos)
local Espacio = require(Shared.Planetas.Espacio)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)
local Ambiente = require(script.Parent.Ambiente)
local Cuerpos = require(script.Parent.Cuerpos)
local EfectosEntorno = require(script.Parent.EfectosEntorno)
local Fundido = require(script.Parent.Fundido)
local Indicadores = require(script.Parent.Indicadores)

local ServicioPlanetas = {}

local iniciado = false
local nave: any = nil -- último EstadoNave
local raizNave: BasePart? = nil
local zonaActual: Espacio.Zona? = nil

local TEXTOS = {
	Aterrizaje = "Entrando en la atmósfera",
	Despegue = "Saliendo al espacio",
	Viaje = "Viajando",
}

local function alEstadoNave(datos: any)
	if type(datos) ~= "table" then
		return
	end
	if datos.Activa ~= true then
		nave = nil
		raizNave = nil
		return
	end
	nave = datos
	local modelo = datos.Modelo
	if typeof(modelo) == "Instance" and (modelo :: Instance):IsA("Model") then
		local principal = (modelo :: Model).PrimaryPart
		if principal then
			raizNave = principal
		end
	end
end

local function alTransicion(datos: any)
	if type(datos) ~= "table" or type(datos.Segundos) ~= "number" then
		return
	end
	local planeta = Datos.Planetas[datos.Planeta]
	local nombre = if planeta then planeta.Nombre else ""
	if datos.Fase == "Salida" then
		if datos.Tipo == "Aterrizaje" then
			EfectosEntorno.Entrada(raizNave)
		end
		local detalle = if datos.Tipo == "Despegue" then `Órbita de {nombre}` else nombre
		Fundido.Salida(datos.Segundos, TEXTOS[datos.Tipo] or "", detalle)
	elseif datos.Fase == "Entrada" then
		-- La cámara ya está en el destino: luz y cielo nuevos de golpe, sin mezcla.
		Ambiente.Reiniciar()
		Fundido.Entrada(datos.Segundos)
		if datos.Tipo == "Despegue" then
			task.delay(0.2, function()
				EfectosEntorno.Salida(raizNave)
			end)
		end
	end
end

local function paso(dt: number)
	local camara = workspace.CurrentCamera
	if camara == nil then
		return
	end
	local p = camara.CFrame.Position
	local zona = Espacio.ZonaDe({ X = p.X, Y = p.Y, Z = p.Z })
	if zonaActual == nil or not Espacio.MismaZona(zonaActual :: Espacio.Zona, zona) then
		zonaActual = zona
		Cuerpos.PonerZona(zona)
	end

	local raiz = if raizNave and raizNave.Parent then raizNave else nil
	Indicadores.Actualizar(nave, if raiz then raiz.Position else nil, dt)
	EfectosEntorno.Actualizar(nave, raiz)
end

-- Arranca los planetas del cliente. Debe llamarse una vez, después de ServicioRed.Iniciar().
function ServicioPlanetas.Iniciar()
	if iniciado then
		return
	end
	iniciado = true

	Cuerpos.Iniciar()
	Ambiente.Iniciar()
	EfectosEntorno.Iniciar()

	ServicioRed.Conectar("EstadoNave", alEstadoNave)
	ServicioRed.Conectar("TransicionPlaneta", alTransicion)
	ServicioRed.Conectar("NaveDestruida", EfectosEntorno.NaveDestruida)
	RunService.Heartbeat:Connect(paso)
end

return ServicioPlanetas
