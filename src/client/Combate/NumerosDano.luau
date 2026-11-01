--!strict
--[[
	NumerosDano: números de daño que suben flotando desde el golpeado.

	Reutiliza los BillboardGui (pool) y no muestra más de MAXIMO a la vez, para no saturar la pantalla ni
	el móvil cuando una definitiva golpea a muchos a la vez.
]]

local Players = game:GetService("Players")

local Utiles = require(script.Parent.Parent.VFX.Utiles)

local NumerosDano = {}

local MAXIMO = 14
local libres: { BillboardGui } = {}
local enUso = 0

local function crear(): BillboardGui
	local gui = Instance.new("BillboardGui")
	gui.Name = "NumeroDano"
	gui.Size = UDim2.fromOffset(160, 60)
	gui.AlwaysOnTop = true
	gui.LightInfluence = 0
	gui.MaxDistance = 200

	local texto = Instance.new("TextLabel")
	texto.Name = "Texto"
	texto.BackgroundTransparency = 1
	texto.AnchorPoint = Vector2.new(0.5, 0.5)
	texto.Position = UDim2.fromScale(0.5, 0.5)
	texto.Size = UDim2.fromScale(1, 1)
	texto.Font = Enum.Font.GothamBlack
	texto.TextScaled = true
	texto.Parent = gui

	local borde = Instance.new("UIStroke")
	borde.Thickness = 2.5
	borde.Color = Color3.fromRGB(10, 10, 20)
	borde.Parent = texto
	return gui
end

--[[
	Muestra `cantidad` de daño sobre `modelo`. `color` es el color del número (por defecto, blanco cálido).
	Los golpes grandes (a partir de 30) salen más grandes.
]]
function NumerosDano.Mostrar(modelo: Model, cantidad: number, color: Color3?)
	if enUso >= MAXIMO then
		return
	end
	local ancla = modelo:FindFirstChild("Head") or modelo:FindFirstChild("HumanoidRootPart")
	local jugador = Players.LocalPlayer
	if ancla == nil or jugador == nil then
		return
	end

	enUso += 1
	local gui = table.remove(libres) or crear()
	local texto = gui:FindFirstChild("Texto") :: TextLabel
	local borde = texto:FindFirstChildOfClass("UIStroke") :: UIStroke

	local grande = cantidad >= 30
	texto.Text = tostring(math.floor(cantidad + 0.5))
	texto.TextColor3 = color or Color3.fromRGB(255, 240, 200)
	texto.TextTransparency = 0
	borde.Transparency = 0
	gui.Size = if grande then UDim2.fromOffset(220, 80) else UDim2.fromOffset(150, 55)
	gui.StudsOffsetWorldSpace = Vector3.new(Utiles.Azar:NextNumber(-1.2, 1.2), 3, Utiles.Azar:NextNumber(-1.2, 1.2))
	gui.Adornee = ancla :: BasePart
	gui.Parent = jugador:WaitForChild("PlayerGui")

	-- Sube y se desvanece; empieza con un pequeño "pop" de tamaño.
	local base = gui.Size
	gui.Size = UDim2.fromOffset(base.X.Offset * 0.5, base.Y.Offset * 0.5)
	Utiles.Tween(gui, 0.12, { Size = base }, "Back")
	Utiles.Tween(gui, 0.8, { StudsOffsetWorldSpace = gui.StudsOffsetWorldSpace + Vector3.new(0, 4, 0) }, "Quad")
	task.delay(0.45, function()
		Utiles.Tween(texto, 0.35, { TextTransparency = 1 }, "Quad", true)
		Utiles.Tween(borde, 0.35, { Transparency = 1 }, "Quad", true)
	end)
	task.delay(0.85, function()
		gui.Parent = nil
		gui.Adornee = nil
		table.insert(libres, gui)
		enUso -= 1
	end)
end

return NumerosDano
