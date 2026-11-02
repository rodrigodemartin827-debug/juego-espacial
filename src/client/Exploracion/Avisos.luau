--!strict
--[[
	Avisos (Exploración): mensajes cortos que aparecen arriba en el centro y se desvanecen ("+4 Hierro", "Bodega llena",
	"Demasiado lejos para escanear"...). Tres tonos: "Bien" (verde), "Mal" (rojo) e "Info" (cian). Se apilan; el más
	antiguo sube y desaparece primero.
]]

local Players = game:GetService("Players")

local Estilo = require(script.Parent.Estilo)
local Utiles = require(script.Parent.Parent.VFX.Utiles)

local Avisos = {}

local SEGUNDOS = 3.2
local MAXIMO = 4

local COLORES: { [string]: Color3 } = {
	Bien = Estilo.VERDE,
	Mal = Estilo.ROJO,
	Info = Estilo.CIAN,
}

local pantalla: ScreenGui? = nil
local lista: Frame? = nil

local function asegurar(): Frame
	if lista and lista.Parent then
		return lista
	end
	local nueva = Estilo.Pantalla("AvisosExploracion", 25)
	nueva.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	pantalla = nueva

	local contenedor = Instance.new("Frame")
	contenedor.BackgroundTransparency = 1
	contenedor.AnchorPoint = Vector2.new(0.5, 0)
	contenedor.Position = UDim2.new(0.5, 0, 0, if Estilo.EsMovil then 56 else 70)
	contenedor.Size = UDim2.fromOffset(if Estilo.EsMovil then 280 else 360, 200)
	contenedor.Parent = nueva
	local disposicion = Instance.new("UIListLayout")
	disposicion.Padding = UDim.new(0, 4)
	disposicion.SortOrder = Enum.SortOrder.LayoutOrder
	disposicion.HorizontalAlignment = Enum.HorizontalAlignment.Center
	disposicion.Parent = contenedor
	lista = contenedor
	return contenedor
end

local orden = 0

-- Muestra un aviso. `tono` es "Bien", "Mal" o "Info" (cualquier otro valor se trata como "Info").
function Avisos.Mostrar(texto: string, tono: string?)
	local contenedor = asegurar()
	local color = COLORES[tono or "Info"] or COLORES.Info

	-- Si ya hay demasiados, el más antiguo se va.
	local existentes = {}
	for _, hijo in contenedor:GetChildren() do
		if hijo:IsA("Frame") then
			table.insert(existentes, hijo)
		end
	end
	if #existentes >= MAXIMO then
		table.sort(existentes, function(a, b)
			return a.LayoutOrder < b.LayoutOrder
		end)
		existentes[1]:Destroy()
	end

	orden += 1
	local marco = Instance.new("Frame")
	marco.BackgroundColor3 = Estilo.FONDO
	marco.BackgroundTransparency = 0.2
	marco.BorderSizePixel = 0
	marco.Size = UDim2.new(1, 0, 0, Estilo.Texto(13) + 14)
	marco.LayoutOrder = orden
	marco.Parent = contenedor
	Estilo.Redondear(marco, 8)
	local trazo = Estilo.Borde(marco, color, 0.35, 1.5)

	local etiqueta = Estilo.Etiqueta(marco, texto, 13, color, UDim2.fromScale(1, 1), UDim2.new())
	etiqueta.TextXAlignment = Enum.TextXAlignment.Center
	etiqueta.TextWrapped = false

	task.delay(SEGUNDOS, function()
		if marco.Parent == nil then
			return
		end
		Utiles.Tween(marco, 0.4, { BackgroundTransparency = 1 }, "Quad")
		Utiles.Tween(etiqueta, 0.4, { TextTransparency = 1 }, "Quad")
		Utiles.Tween(trazo, 0.4, { Transparency = 1 }, "Quad")
		task.delay(0.45, function()
			marco:Destroy()
		end)
	end)
end

return Avisos
