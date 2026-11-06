--!strict
--[[
	Fundido (Planetas, cliente): la pantalla negra de las transiciones (aterrizar, despegar, viajar).

	El servidor manda cuándo empieza y cuándo acaba (TransicionPlaneta); aquí solo se dibuja: un fundido a negro
	con el nombre del destino y, después, la vuelta a la imagen. Va por encima de todo lo demás.
]]

local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")

local Fundido = {}

local gui: ScreenGui? = nil
local negro: Frame? = nil
local titulo: TextLabel? = nil
local subtitulo: TextLabel? = nil

local function construir()
	if gui then
		return
	end
	local jugador = Players.LocalPlayer
	local pantalla = Instance.new("ScreenGui")
	pantalla.Name = "FundidoPlaneta"
	pantalla.DisplayOrder = 1000
	pantalla.IgnoreGuiInset = true
	pantalla.ResetOnSpawn = false
	pantalla.Enabled = false

	local fondo = Instance.new("Frame")
	fondo.Size = UDim2.fromScale(1, 1)
	fondo.BackgroundColor3 = Color3.new(0, 0, 0)
	fondo.BackgroundTransparency = 1
	fondo.BorderSizePixel = 0
	fondo.Parent = pantalla

	local texto = Instance.new("TextLabel")
	texto.AnchorPoint = Vector2.new(0.5, 0.5)
	texto.Position = UDim2.fromScale(0.5, 0.46)
	texto.Size = UDim2.fromScale(0.8, 0.07)
	texto.BackgroundTransparency = 1
	texto.Font = Enum.Font.GothamBold
	texto.TextScaled = true
	texto.TextColor3 = Color3.fromRGB(235, 240, 255)
	texto.TextTransparency = 1
	texto.Text = ""
	texto.Parent = fondo

	local detalle = texto:Clone()
	detalle.Position = UDim2.fromScale(0.5, 0.53)
	detalle.Size = UDim2.fromScale(0.7, 0.035)
	detalle.Font = Enum.Font.GothamMedium
	detalle.TextColor3 = Color3.fromRGB(170, 180, 210)
	detalle.Parent = fondo

	pantalla.Parent = jugador:WaitForChild("PlayerGui")
	gui, negro, titulo, subtitulo = pantalla, fondo, texto, detalle
end

local function animar(objeto: Instance, segundos: number, propiedades: { [string]: any })
	TweenService:Create(objeto, TweenInfo.new(segundos, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut), propiedades)
		:Play()
end

-- Funde a negro en `segundos`, con un título y un detalle opcionales.
function Fundido.Salida(segundos: number, texto: string?, detalle: string?)
	construir()
	local pantalla, fondo, t, d = gui :: ScreenGui, negro :: Frame, titulo :: TextLabel, subtitulo :: TextLabel
	pantalla.Enabled = true
	t.Text = texto or ""
	d.Text = detalle or ""
	animar(fondo, segundos, { BackgroundTransparency = 0 })
	animar(t, segundos, { TextTransparency = 0 })
	animar(d, segundos, { TextTransparency = 0.2 })
end

-- Vuelve a mostrar la imagen en `segundos`.
function Fundido.Entrada(segundos: number)
	construir()
	local pantalla, fondo, t, d = gui :: ScreenGui, negro :: Frame, titulo :: TextLabel, subtitulo :: TextLabel
	animar(fondo, segundos, { BackgroundTransparency = 1 })
	animar(t, segundos * 0.6, { TextTransparency = 1 })
	animar(d, segundos * 0.6, { TextTransparency = 1 })
	task.delay(segundos + 0.05, function()
		if fondo.BackgroundTransparency >= 0.999 then
			pantalla.Enabled = false
		end
	end)
end

return Fundido
