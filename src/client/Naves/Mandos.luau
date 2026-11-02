--!strict
--[[
	Mandos (Naves): los controles táctiles para volar en móvil o tableta.

	  - Joystick virtual (abajo a la izquierda): arriba/abajo acelera y frena, izquierda/derecha se desplaza de lado.
	  - Arrastrar con el dedo por la mitad derecha de la pantalla: orienta la nave.
	  - Botones: DISPARAR (mantener), TURBO (mantener), ▲ subir y ▼ bajar (mantener), y ATERRIZAR.

	Este módulo solo dibuja los controles y guarda su estado; Entrada lo mezcla con el teclado, el ratón y el mando.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Config = require(ReplicatedStorage:WaitForChild("Shared").Naves.Config)

export type Lectura = {
	Adelante: number,
	Lateral: number,
	Vertical: number,
	Turbo: boolean,
	Disparar: boolean,
	DGuinada: number, -- giro acumulado desde la última lectura (radianes)
	DCabeceo: number,
}

local Mandos = {}

-- Qué hacer al pulsar ATERRIZAR (lo fija Entrada al activar los controles).
Mandos.AlAterrizar = nil :: (() -> ())?

local FONDO = Color3.fromRGB(12, 14, 26)
local CIAN = Color3.fromRGB(77, 240, 255)
local RADIO_JOYSTICK = 70 -- píxeles que puede alejarse el pomo del centro

local gui: ScreenGui? = nil

-- Estado de los mandos.
local joystick = Vector2.zero -- -1..1 en cada eje
local botones: { [string]: boolean } = { Disparar = false, Turbo = false, Subir = false, Bajar = false }
local giroAcumulado = Vector2.zero -- píxeles arrastrados desde la última lectura

local function redondear(objeto: GuiObject, radio: number)
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, radio)
	esquina.Parent = objeto
end

local function borde(objeto: GuiObject, color: Color3)
	local trazo = Instance.new("UIStroke")
	trazo.Color = color
	trazo.Thickness = 2
	trazo.Transparency = 0.2
	trazo.Parent = objeto
end

local function esToque(entrada: InputObject): boolean
	return entrada.UserInputType == Enum.UserInputType.Touch or entrada.UserInputType == Enum.UserInputType.MouseButton1
end

-- Botón que está activo MIENTRAS se mantiene pulsado.
local function crearBoton(
	padre: Instance,
	texto: string,
	clave: string,
	tamano: number,
	anclaje: Vector2,
	posicion: UDim2,
	color: Color3
)
	local boton = Instance.new("TextButton")
	boton.AutoButtonColor = false
	boton.Text = texto
	boton.Font = Enum.Font.GothamBold
	boton.TextSize = if tamano >= 80 then 18 else 22
	boton.TextColor3 = Color3.fromRGB(235, 240, 255)
	boton.BackgroundColor3 = FONDO
	boton.BackgroundTransparency = 0.35
	boton.AnchorPoint = anclaje
	boton.Position = posicion
	boton.Size = UDim2.fromOffset(tamano, tamano)
	boton.Parent = padre
	redondear(boton, tamano / 2)
	borde(boton, color)

	local pulsado = 0 -- cuántos dedos hay encima (un dedo que sale sin soltar no deja el botón atascado)
	local function marcar(activo: boolean)
		botones[clave] = activo
		boton.BackgroundColor3 = if activo then color else FONDO
		boton.BackgroundTransparency = if activo then 0.1 else 0.35
	end
	boton.InputBegan:Connect(function(entrada: InputObject)
		if esToque(entrada) then
			pulsado += 1
			marcar(true)
		end
	end)
	boton.InputEnded:Connect(function(entrada: InputObject)
		if esToque(entrada) then
			pulsado = math.max(0, pulsado - 1)
			if pulsado == 0 then
				marcar(false)
			end
		end
	end)
	return boton
end

-- Construye los controles (una sola vez) y los deja ocultos.
local function construir()
	local pantalla = Instance.new("ScreenGui")
	pantalla.Name = "MandosNave"
	pantalla.ResetOnSpawn = false
	pantalla.IgnoreGuiInset = true
	pantalla.DisplayOrder = 20
	pantalla.Enabled = false
	pantalla.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

	-- Zona de apuntado: toda la mitad derecha.
	local zona = Instance.new("Frame")
	zona.Name = "ZonaApuntado"
	zona.BackgroundTransparency = 1
	zona.AnchorPoint = Vector2.new(1, 0)
	zona.Position = UDim2.fromScale(1, 0)
	zona.Size = UDim2.fromScale(0.5, 1)
	zona.Active = true
	zona.Parent = pantalla

	local dedoApuntado: InputObject? = nil
	zona.InputBegan:Connect(function(entrada: InputObject)
		if entrada.UserInputType == Enum.UserInputType.Touch and dedoApuntado == nil then
			dedoApuntado = entrada
		end
	end)

	-- Joystick.
	local base = Instance.new("Frame")
	base.Name = "Joystick"
	base.BackgroundColor3 = FONDO
	base.BackgroundTransparency = 0.5
	base.AnchorPoint = Vector2.new(0, 1)
	base.Position = UDim2.new(0, 30, 1, -30)
	base.Size = UDim2.fromOffset(RADIO_JOYSTICK * 2 + 24, RADIO_JOYSTICK * 2 + 24)
	base.Active = true
	base.Parent = pantalla
	redondear(base, 999)
	borde(base, CIAN)

	local pomo = Instance.new("Frame")
	pomo.BackgroundColor3 = CIAN
	pomo.BackgroundTransparency = 0.2
	pomo.AnchorPoint = Vector2.new(0.5, 0.5)
	pomo.Position = UDim2.fromScale(0.5, 0.5)
	pomo.Size = UDim2.fromOffset(58, 58)
	pomo.Parent = base
	redondear(pomo, 999)

	local dedoJoystick: InputObject? = nil
	local function moverPomo(posicion: Vector2)
		local centro = base.AbsolutePosition + base.AbsoluteSize / 2
		local desplazamiento = posicion - centro
		if desplazamiento.Magnitude > RADIO_JOYSTICK then
			desplazamiento = desplazamiento.Unit * RADIO_JOYSTICK
		end
		pomo.Position = UDim2.new(0.5, desplazamiento.X, 0.5, desplazamiento.Y)
		joystick = Vector2.new(desplazamiento.X / RADIO_JOYSTICK, desplazamiento.Y / RADIO_JOYSTICK)
	end
	base.InputBegan:Connect(function(entrada: InputObject)
		if entrada.UserInputType == Enum.UserInputType.Touch and dedoJoystick == nil then
			dedoJoystick = entrada
			moverPomo(Vector2.new(entrada.Position.X, entrada.Position.Y))
		end
	end)

	UserInputService.InputChanged:Connect(function(entrada: InputObject)
		if entrada.UserInputType ~= Enum.UserInputType.Touch then
			return
		end
		if entrada == dedoJoystick then
			moverPomo(Vector2.new(entrada.Position.X, entrada.Position.Y))
		elseif entrada == dedoApuntado then
			giroAcumulado += Vector2.new(entrada.Delta.X, entrada.Delta.Y)
		end
	end)
	UserInputService.InputEnded:Connect(function(entrada: InputObject)
		if entrada == dedoJoystick then
			dedoJoystick = nil
			joystick = Vector2.zero
			pomo.Position = UDim2.fromScale(0.5, 0.5)
		elseif entrada == dedoApuntado then
			dedoApuntado = nil
		end
	end)

	-- Botones (esquina inferior derecha).
	crearBoton(
		pantalla,
		"DISPARAR",
		"Disparar",
		96,
		Vector2.new(1, 1),
		UDim2.new(1, -24, 1, -30),
		Color3.fromRGB(255, 77, 94)
	)
	crearBoton(
		pantalla,
		"TURBO",
		"Turbo",
		76,
		Vector2.new(1, 1),
		UDim2.new(1, -132, 1, -30),
		Color3.fromRGB(181, 140, 255)
	)
	crearBoton(pantalla, "▲", "Subir", 60, Vector2.new(1, 1), UDim2.new(1, -24, 1, -140), CIAN)
	crearBoton(pantalla, "▼", "Bajar", 60, Vector2.new(1, 1), UDim2.new(1, -24, 1, -208), CIAN)

	pantalla.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	return pantalla
end

-- Muestra u oculta los controles táctiles. Los crea la primera vez que se muestran.
function Mandos.Mostrar(visible: boolean, alAterrizar: (() -> ())?)
	if gui == nil then
		if not visible then
			return
		end
		gui = construir()
		-- El botón de aterrizar es pequeño y va arriba, lejos de los demás para no tocarlo sin querer.
		local aterrizar = Instance.new("TextButton")
		aterrizar.Text = "ATERRIZAR"
		aterrizar.Font = Enum.Font.GothamBold
		aterrizar.TextSize = 14
		aterrizar.TextColor3 = Color3.fromRGB(235, 240, 255)
		aterrizar.BackgroundColor3 = FONDO
		aterrizar.BackgroundTransparency = 0.35
		aterrizar.AnchorPoint = Vector2.new(1, 0)
		aterrizar.Position = UDim2.new(1, -16, 0, 56)
		aterrizar.Size = UDim2.fromOffset(104, 36)
		aterrizar.Name = "Aterrizar"
		aterrizar.Parent = gui
		redondear(aterrizar, 8)
		borde(aterrizar, CIAN)
		aterrizar.Activated:Connect(function()
			if Mandos.AlAterrizar then
				Mandos.AlAterrizar()
			end
		end)
	end
	Mandos.AlAterrizar = alAterrizar
	if gui then
		gui.Enabled = visible
	end
	if not visible then
		joystick = Vector2.zero
		giroAcumulado = Vector2.zero
		for clave in botones do
			botones[clave] = false
		end
	end
end

-- Lee los mandos. Los píxeles arrastrados desde la última lectura se convierten en giro y se reinician.
function Mandos.Leer(): Lectura
	local giro = giroAcumulado
	giroAcumulado = Vector2.zero
	return {
		Adelante = -joystick.Y,
		Lateral = joystick.X,
		Vertical = (if botones.Subir then 1 else 0) - (if botones.Bajar then 1 else 0),
		Turbo = botones.Turbo,
		Disparar = botones.Disparar,
		DGuinada = -giro.X * Config.SensibilidadTactil,
		DCabeceo = -giro.Y * Config.SensibilidadTactil,
	}
end

return Mandos
