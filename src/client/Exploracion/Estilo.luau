--!strict
--[[
	Estilo (Exploración): colores y piezas de interfaz comunes a la ficha del escáner, el inventario y la mesa de crafteo.

	Todo se construye por código, con el mismo aspecto oscuro con borde de neón que el panel de la nave. En móvil los
	textos y las zonas pulsables son algo mayores.
]]

local Calidad = require(script.Parent.Parent.VFX.Calidad)
local Utiles = require(script.Parent.Parent.VFX.Utiles)

local Estilo = {}

Estilo.FONDO = Color3.fromRGB(12, 14, 26)
Estilo.TEXTO = Color3.fromRGB(235, 240, 255)
Estilo.TEXTO_SUAVE = Color3.fromRGB(165, 175, 205)
Estilo.CIAN = Color3.fromRGB(77, 240, 255)
Estilo.VERDE = Color3.fromRGB(80, 220, 120)
Estilo.ROJO = Color3.fromRGB(255, 96, 110)
Estilo.AMARILLO = Color3.fromRGB(255, 214, 102)
Estilo.MORADO = Color3.fromRGB(181, 140, 255)

Estilo.EsMovil = Calidad.EsMovil

-- Tamaño de texto: +2 en móvil.
function Estilo.Texto(tamano: number): number
	return if Estilo.EsMovil then tamano + 2 else tamano
end

-- "#RRGGBB" → Color3.
function Estilo.Hex(hex: string): Color3
	return Utiles.Hex(hex)
end

function Estilo.Redondear(objeto: GuiObject, radio: number?)
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, radio or 8)
	esquina.Parent = objeto
end

function Estilo.Borde(objeto: GuiObject, color: Color3, transparencia: number?, grosor: number?): UIStroke
	local trazo = Instance.new("UIStroke")
	trazo.Color = color
	trazo.Thickness = grosor or 1.5
	trazo.Transparency = transparencia or 0.4
	trazo.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	trazo.Parent = objeto
	return trazo
end

-- Un ScreenGui estándar de esta interfaz.
function Estilo.Pantalla(nombre: string, orden: number): ScreenGui
	local pantalla = Instance.new("ScreenGui")
	pantalla.Name = nombre
	pantalla.ResetOnSpawn = false
	pantalla.IgnoreGuiInset = false
	pantalla.DisplayOrder = orden
	pantalla.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	return pantalla
end

-- Un panel oscuro con borde.
function Estilo.Panel(padre: Instance, tamano: UDim2, posicion: UDim2, colorBorde: Color3?): Frame
	local marco = Instance.new("Frame")
	marco.BackgroundColor3 = Estilo.FONDO
	marco.BackgroundTransparency = 0.12
	marco.BorderSizePixel = 0
	marco.Size = tamano
	marco.Position = posicion
	marco.Parent = padre
	Estilo.Redondear(marco, 10)
	Estilo.Borde(marco, colorBorde or Estilo.CIAN, 0.45)
	return marco
end

function Estilo.Etiqueta(
	padre: Instance,
	texto: string,
	tamanoTexto: number,
	color: Color3?,
	tamano: UDim2?,
	posicion: UDim2?,
	negrita: boolean?
): TextLabel
	local objeto = Instance.new("TextLabel")
	objeto.BackgroundTransparency = 1
	objeto.Size = tamano or UDim2.new(1, 0, 0, Estilo.Texto(tamanoTexto) + 4)
	objeto.Position = posicion or UDim2.new()
	objeto.Text = texto
	objeto.Font = if negrita == false then Enum.Font.Gotham else Enum.Font.GothamBold
	objeto.TextSize = Estilo.Texto(tamanoTexto)
	objeto.TextColor3 = color or Estilo.TEXTO
	objeto.TextXAlignment = Enum.TextXAlignment.Left
	objeto.TextWrapped = true
	objeto.Parent = padre
	return objeto
end

-- Un botón de texto. `alPulsar` se llama al hacer clic o tocar.
function Estilo.Boton(
	padre: Instance,
	texto: string,
	tamano: UDim2,
	posicion: UDim2,
	color: Color3,
	alPulsar: () -> ()
): TextButton
	local boton = Instance.new("TextButton")
	boton.AutoButtonColor = true
	boton.BackgroundColor3 = color:Lerp(Estilo.FONDO, 0.6)
	boton.BorderSizePixel = 0
	boton.Size = tamano
	boton.Position = posicion
	boton.Text = texto
	boton.Font = Enum.Font.GothamBold
	boton.TextSize = Estilo.Texto(14)
	boton.TextColor3 = Estilo.TEXTO
	boton.Parent = padre
	Estilo.Redondear(boton, 8)
	Estilo.Borde(boton, color, 0.35)
	boton.Activated:Connect(alPulsar)
	return boton
end

-- Una barra de progreso (fondo + relleno). Devuelve el relleno: se cambia con `relleno.Size = UDim2.fromScale(f, 1)`.
function Estilo.Barra(padre: Instance, tamano: UDim2, posicion: UDim2, color: Color3): Frame
	local fondo = Instance.new("Frame")
	fondo.BackgroundColor3 = Color3.fromRGB(28, 32, 52)
	fondo.BorderSizePixel = 0
	fondo.Size = tamano
	fondo.Position = posicion
	fondo.Parent = padre
	Estilo.Redondear(fondo, 6)
	local relleno = Instance.new("Frame")
	relleno.BackgroundColor3 = color
	relleno.BorderSizePixel = 0
	relleno.Size = UDim2.fromScale(0, 1)
	relleno.Parent = fondo
	Estilo.Redondear(relleno, 6)
	return relleno
end

-- Carpeta compartida (en el cliente) de la que cuelgan los objetos de los efectos de escaneo.
function Estilo.CarpetaLocal(nombre: string): Folder
	local existente = workspace:FindFirstChild(nombre)
	if existente and existente:IsA("Folder") then
		return existente
	end
	local carpeta = Instance.new("Folder")
	carpeta.Name = nombre
	carpeta.Parent = workspace
	return carpeta
end

return Estilo
