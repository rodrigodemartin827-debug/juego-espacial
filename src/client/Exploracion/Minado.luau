--!strict
--[[
	Minado (cliente): el pico. Mantén R (o el botón táctil "Picar") cerca de un mineral: cada pocas décimas se propone un golpe
	al servidor (PicarMineral). Los chispazos y la rotura los dibujan EfectosEscaneo cuando el servidor confirma el golpe.

	Desde la nave no se pica con esto: los láseres rompen las vetas de los asteroides (ServicioNaves → ServicioMinado).
	El servidor comprueba distancia, cadencia y espacio en la bodega; este módulo solo busca a qué mineral se apunta.
]]

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage:WaitForChild("Shared").Exploracion.Config)
local Apuntar = require(script.Parent.Apuntar)
local Avisos = require(script.Parent.Avisos)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)

local Minado = {}

local ACCION = "PicarMineral"

-- Grados del cono de ayuda: más generoso que el del escáner, los minerales son grandes y se pica deprisa.
local ANGULO_AYUDA = 25

local pulsado = false

local function pilotando(): boolean
	local personaje = Players.LocalPlayer.Character
	return personaje ~= nil and personaje:GetAttribute(Config.AtributoPilotando) == true
end

-- Bucle de golpes mientras se mantiene la tecla.
local function picar()
	local avisado = false
	while pulsado and not pilotando() do
		local nodo = Apuntar.Buscar(Config.EtiquetaMineral, Config.AlcancePicado, ANGULO_AYUDA)
		if nodo then
			ServicioRed.Enviar("PicarMineral", nodo)
		elseif not avisado then
			avisado = true
			Avisos.Mostrar("Acércate a un mineral y apunta hacia él", "Info")
		end
		task.wait(Config.CadenciaPicado)
	end
end

local function alAccion(_nombre: string, estado: Enum.UserInputState, _entrada: InputObject): Enum.ContextActionResult?
	if estado == Enum.UserInputState.Begin then
		if not pulsado then
			pulsado = true
			task.spawn(picar)
		end
	else
		pulsado = false
	end
	return Enum.ContextActionResult.Sink
end

-- Arranca el pico del cliente. Debe llamarse una vez.
function Minado.Iniciar()
	ContextActionService:BindAction(ACCION, alAccion, true, Enum.KeyCode.R, Enum.KeyCode.ButtonR1)
	ContextActionService:SetTitle(ACCION, "Picar")
	ContextActionService:SetPosition(ACCION, UDim2.new(1, -250, 1, -160))
end

return Minado
