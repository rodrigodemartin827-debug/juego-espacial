--!strict
--[[
	PanelInventario (Exploración): la bodega del jugador en pantalla.

	  - Una pastilla siempre visible abajo a la izquierda con "Bodega 12/30" (se pone roja cuando está casi llena). Pulsarla
	    abre o cierra el panel.
	  - El panel (tecla I) lista cada objeto con su color, nombre, cantidad y espacio que ocupa, y una barra con lo lleno que está
	    el inventario. El límite sale de la mejora Carga.

	Solo MUESTRA: el inventario de verdad vive en el servidor y llega en cada copia de los datos (ServicioDatos).
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Estadisticas = require(Shared.Naves.Estadisticas)
local Inventario = require(Shared.Exploracion.Inventario)
local Objetos = require(Shared.Exploracion.Datos.Objetos)
local Estilo = require(script.Parent.Estilo)
local ServicioDatos = require(script.Parent.Parent.Servicios.ServicioDatos)

local PanelInventario = {}

local ANCHO = if Estilo.EsMovil then 250 else 300

local pantalla: ScreenGui? = nil
local pastilla: TextButton? = nil
local panel: Frame? = nil
local textoCapacidad: TextLabel? = nil
local barra: Frame? = nil
local lista: ScrollingFrame? = nil
local vacio: TextLabel? = nil
local abierto = false

-- Capacidad y espacio ocupado según la última copia de los datos.
local function medidas(): (number, number)
	local datos = ServicioDatos.Obtener()
	if datos == nil then
		return 0, 0
	end
	return Inventario.Volumen(datos.Inventario), Estadisticas.Calcular(datos.MejorasNave).Capacidad
end

local function refrescar()
	if pantalla == nil then
		return
	end
	local datos = ServicioDatos.Obtener()
	local ocupado, capacidad = medidas()
	local fraccion = if capacidad > 0 then math.clamp(ocupado / capacidad, 0, 1) else 0
	local lleno = fraccion >= 0.9

	if pastilla then
		pastilla.Text = `Bodega {math.floor(ocupado)}/{math.floor(capacidad)}`
		pastilla.TextColor3 = if lleno then Estilo.ROJO else Estilo.TEXTO
	end
	local etiquetaEspacio, relleno, contenedor, aviso = textoCapacidad, barra, lista, vacio
	if not abierto or panel == nil or datos == nil then
		return
	end
	if etiquetaEspacio == nil or relleno == nil or contenedor == nil or aviso == nil then
		return
	end

	etiquetaEspacio.Text = `Espacio {math.floor(ocupado)} / {math.floor(capacidad)}`
	relleno.Size = UDim2.fromScale(fraccion, 1)
	relleno.BackgroundColor3 = if lleno then Estilo.ROJO else Estilo.CIAN

	for _, hijo in contenedor:GetChildren() do
		if hijo:IsA("Frame") then
			hijo:Destroy()
		end
	end

	local hay = 0
	-- Primero los objetos conocidos, en su orden; después cualquier id raro que hubiera.
	local ids: { string } = {}
	for _, id in Objetos.Orden do
		if (datos.Inventario[id] or 0) > 0 then
			table.insert(ids, id)
		end
	end
	for id, cantidad in datos.Inventario do
		if cantidad > 0 and Objetos.Lista[id] == nil then
			table.insert(ids, id)
		end
	end

	for indice, id in ids do
		hay += 1
		local objeto = Objetos.Lista[id]
		local cantidad = datos.Inventario[id]
		local fila = Instance.new("Frame")
		fila.BackgroundColor3 = Color3.fromRGB(22, 26, 44)
		fila.BorderSizePixel = 0
		fila.Size = UDim2.new(1, -6, 0, Estilo.Texto(13) + 18)
		fila.LayoutOrder = indice
		fila.Parent = contenedor
		Estilo.Redondear(fila, 6)

		local icono = Instance.new("Frame")
		icono.BackgroundColor3 = if objeto then Estilo.Hex(objeto.Color) else Estilo.TEXTO_SUAVE
		icono.BorderSizePixel = 0
		icono.AnchorPoint = Vector2.new(0, 0.5)
		icono.Position = UDim2.new(0, 8, 0.5, 0)
		icono.Size = UDim2.fromOffset(16, 16)
		icono.Parent = fila
		Estilo.Redondear(icono, if objeto and objeto.Categoria == "Mineral" then 8 else 3)

		local nombre = Estilo.Etiqueta(
			fila,
			if objeto then objeto.Nombre else id,
			13,
			Estilo.TEXTO,
			UDim2.new(1, -90, 1, 0),
			UDim2.fromOffset(32, 0)
		)
		nombre.TextWrapped = false
		local numero = Estilo.Etiqueta(
			fila,
			`×{cantidad}`,
			14,
			Estilo.CIAN,
			UDim2.fromOffset(52, Estilo.Texto(13) + 18),
			UDim2.new(1, -58, 0, 0)
		)
		numero.TextXAlignment = Enum.TextXAlignment.Right
	end
	aviso.Visible = hay == 0
end

-- Abre o cierra el panel.
function PanelInventario.Alternar(forzar: boolean?)
	if panel == nil then
		return
	end
	abierto = if forzar ~= nil then forzar else not abierto
	panel.Visible = abierto
	refrescar()
end

function PanelInventario.EstaAbierto(): boolean
	return abierto
end

function PanelInventario.Iniciar()
	if pantalla then
		return
	end
	local nueva = Estilo.Pantalla("InventarioExploracion", 18)
	nueva.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	pantalla = nueva

	-- Pastilla de siempre.
	local boton = Estilo.Boton(
		nueva,
		"",
		UDim2.fromOffset(if Estilo.EsMovil then 130 else 150, if Estilo.EsMovil then 34 else 30),
		UDim2.new(0, 12, 1, if Estilo.EsMovil then -64 else -48),
		Estilo.CIAN,
		function()
			PanelInventario.Alternar()
		end
	)
	pastilla = boton
	boton.Text = "Bodega 0/0"

	-- Panel completo.
	local marco = Estilo.Panel(nueva, UDim2.fromOffset(ANCHO, 330), UDim2.new(0, 12, 1, -92), Estilo.CIAN)
	marco.AnchorPoint = Vector2.new(0, 1)
	marco.Position = UDim2.new(0, 12, 1, if Estilo.EsMovil then -104 else -88)
	marco.Visible = false
	panel = marco

	Estilo.Etiqueta(marco, "BODEGA", 16, Estilo.CIAN, UDim2.new(1, -50, 0, 22), UDim2.fromOffset(12, 8))
	Estilo.Boton(marco, "×", UDim2.fromOffset(26, 26), UDim2.new(1, -34, 0, 8), Estilo.ROJO, function()
		PanelInventario.Alternar(false)
	end).TextSize =
		18

	textoCapacidad =
		Estilo.Etiqueta(marco, "", 12, Estilo.TEXTO_SUAVE, UDim2.new(1, -24, 0, 16), UDim2.fromOffset(12, 34))
	barra = Estilo.Barra(marco, UDim2.new(1, -24, 0, 8), UDim2.fromOffset(12, 54), Estilo.CIAN)

	local desplazable = Instance.new("ScrollingFrame")
	desplazable.BackgroundTransparency = 1
	desplazable.BorderSizePixel = 0
	desplazable.Position = UDim2.fromOffset(12, 72)
	desplazable.Size = UDim2.new(1, -24, 1, -84)
	desplazable.ScrollBarThickness = 4
	desplazable.CanvasSize = UDim2.new()
	desplazable.AutomaticCanvasSize = Enum.AutomaticSize.Y
	desplazable.Parent = marco
	local disposicion = Instance.new("UIListLayout")
	disposicion.Padding = UDim.new(0, 4)
	disposicion.SortOrder = Enum.SortOrder.LayoutOrder
	disposicion.Parent = desplazable
	lista = desplazable

	vacio = Estilo.Etiqueta(
		marco,
		"Vacía. Pica minerales con R para llenarla.",
		13,
		Estilo.TEXTO_SUAVE,
		UDim2.new(1, -24, 0, 40),
		UDim2.fromOffset(12, 80),
		false
	)

	ServicioDatos.Actualizados:Conectar(refrescar)
	refrescar()
end

return PanelInventario
