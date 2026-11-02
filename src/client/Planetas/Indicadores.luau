--!strict
--[[
	Indicadores (Planetas, cliente): avisos del entorno en pantalla mientras se pilota.

	  TEMPERATURA  barra del recalentamiento junto al sol. El valor lo decide el servidor (EstadoNave.Calor); aquí
	               solo se muestra, suavizado entre dos mensajes. Cambia de color en el aviso y en el peligro.
	  GRAVEDAD     la atracción del agujero negro en este punto (la misma cuenta que usa el vuelo, Planetas/Gravedad)
	               y si con este motor todavía se puede escapar.

	Solo aparecen cuando hay algo que contar; en móvil van arriba, lejos de los mandos táctiles.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Datos = require(Shared.Planetas.Datos)
local Gravedad = require(Shared.Planetas.Gravedad)

local Indicadores = {}

local COLOR_NORMAL = Color3.fromRGB(255, 196, 92)
local COLOR_AVISO = Color3.fromRGB(255, 140, 50)
local COLOR_PELIGRO = Color3.fromRGB(255, 70, 50)
local COLOR_GRAVEDAD = Color3.fromRGB(190, 120, 255)

local gui: ScreenGui? = nil
local barraCalor: Frame? = nil
local rellenoCalor: Frame? = nil
local textoCalor: TextLabel? = nil
local textoGravedad: TextLabel? = nil
local calorMostrado = 0

local function construir()
	if gui then
		return
	end
	local pantalla = Instance.new("ScreenGui")
	pantalla.Name = "IndicadoresEntorno"
	pantalla.DisplayOrder = 20
	pantalla.ResetOnSpawn = false

	local caja = Instance.new("Frame")
	caja.AnchorPoint = Vector2.new(0.5, 0)
	caja.Position = UDim2.new(0.5, 0, 0, 64)
	caja.Size = UDim2.fromOffset(300, 46)
	caja.BackgroundColor3 = Color3.fromRGB(12, 14, 26)
	caja.BackgroundTransparency = 0.35
	caja.Visible = false
	caja.Parent = pantalla
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, 8)
	esquina.Parent = caja

	local texto = Instance.new("TextLabel")
	texto.Position = UDim2.fromOffset(10, 4)
	texto.Size = UDim2.new(1, -20, 0, 18)
	texto.BackgroundTransparency = 1
	texto.Font = Enum.Font.GothamBold
	texto.TextScaled = true
	texto.TextXAlignment = Enum.TextXAlignment.Left
	texto.TextColor3 = COLOR_NORMAL
	texto.Text = "TEMPERATURA DEL CASCO"
	texto.Parent = caja

	local fondo = Instance.new("Frame")
	fondo.Position = UDim2.fromOffset(10, 26)
	fondo.Size = UDim2.new(1, -20, 0, 12)
	fondo.BackgroundColor3 = Color3.fromRGB(40, 30, 30)
	fondo.BorderSizePixel = 0
	fondo.Parent = caja
	local esquinaFondo = Instance.new("UICorner")
	esquinaFondo.CornerRadius = UDim.new(0, 6)
	esquinaFondo.Parent = fondo

	local relleno = Instance.new("Frame")
	relleno.Size = UDim2.fromScale(0, 1)
	relleno.BackgroundColor3 = COLOR_NORMAL
	relleno.BorderSizePixel = 0
	relleno.Parent = fondo
	local esquinaRelleno = Instance.new("UICorner")
	esquinaRelleno.CornerRadius = UDim.new(0, 6)
	esquinaRelleno.Parent = relleno

	local gravedad = Instance.new("TextLabel")
	gravedad.AnchorPoint = Vector2.new(0.5, 0)
	gravedad.Position = UDim2.new(0.5, 0, 0, 116)
	gravedad.Size = UDim2.fromOffset(420, 26)
	gravedad.BackgroundColor3 = Color3.fromRGB(12, 8, 22)
	gravedad.BackgroundTransparency = 0.35
	gravedad.Font = Enum.Font.GothamBold
	gravedad.TextScaled = true
	gravedad.TextColor3 = COLOR_GRAVEDAD
	gravedad.Visible = false
	gravedad.Parent = pantalla
	local esquinaGravedad = Instance.new("UICorner")
	esquinaGravedad.CornerRadius = UDim.new(0, 8)
	esquinaGravedad.Parent = gravedad

	pantalla.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	gui, barraCalor, rellenoCalor, textoCalor, textoGravedad = pantalla, caja, relleno, texto, gravedad
end

--[[
	Actualiza los indicadores. `nave` es el último EstadoNave (nil = no se pilota), `posicion` la de la nave y
	`dt` el tiempo desde la última llamada.
]]
function Indicadores.Actualizar(nave: any, posicion: Vector3?, dt: number)
	construir()
	local caja, relleno, texto, gravedad =
		barraCalor :: Frame, rellenoCalor :: Frame, textoCalor :: TextLabel, textoGravedad :: TextLabel
	if nave == nil or posicion == nil or nave.Activa ~= true then
		caja.Visible = false
		gravedad.Visible = false
		calorMostrado = 0
		return
	end

	-- Temperatura (se acerca suavemente a lo que dice el servidor).
	local calor = if type(nave.Calor) == "number" then nave.Calor else 0
	local maximo = if type(nave.CalorMax) == "number" then nave.CalorMax else 100
	calorMostrado += (calor - calorMostrado) * (1 - math.exp(-6 * dt))
	caja.Visible = calorMostrado > 0.5
	local fraccion = math.clamp(calorMostrado / maximo, 0, 1)
	relleno.Size = UDim2.fromScale(fraccion, 1)
	local tono = if nave.NivelCalor == "Peligro"
		then COLOR_PELIGRO
		elseif nave.NivelCalor == "Aviso" then COLOR_AVISO
		else COLOR_NORMAL
	relleno.BackgroundColor3 = tono
	texto.TextColor3 = tono
	texto.Text = if nave.NivelCalor == "Peligro"
		then "¡RECALENTAMIENTO! EL CASCO SE FUNDE"
		else `TEMPERATURA DEL CASCO · {math.floor(fraccion * 100)} %`

	-- Gravedad del agujero negro.
	local agujero = Datos.AgujeroNegro
	local centro = Vector3.new(agujero.Centro.X, agujero.Centro.Y, agujero.Centro.Z)
	local distancia = (posicion - centro).Magnitude
	local arrastre = Gravedad.Arrastre(distancia, agujero.Atraccion)
	gravedad.Visible = arrastre > 1
	if arrastre > 1 then
		local motor = (nave.VelocidadMax or 0) * (if nave.TurboActivo then nave.TurboMult or 1 else 1)
		local escapa = motor > arrastre
		gravedad.Text = if escapa
			then `ATRACCIÓN GRAVITATORIA · {math.floor(arrastre)} studs/s`
			else "¡SIN RETORNO! El motor no basta para escapar"
		gravedad.TextColor3 = if escapa then COLOR_GRAVEDAD else COLOR_PELIGRO
	end
end

return Indicadores
