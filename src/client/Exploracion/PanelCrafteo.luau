--!strict
--[[
	PanelCrafteo (Exploración): el panel de la mesa de crafteo.

	A la izquierda, la lista de recetas (Exploracion/Datos/Recetas); a la derecha, la receta elegida con sus ingredientes
	(en verde lo que tienes, en rojo lo que te falta), lo que obtienes y el botón de fabricar. Para las mejoras de la nave
	se ve el efecto del nivel nuevo estadística a estadística.

	Es solo una vista: usa las MISMAS reglas que el servidor (Exploracion/Crafteo.Planificar) para pintar y activar el botón,
	pero quien decide de verdad es el servidor, que lo comprueba todo otra vez (incluida la distancia a la mesa).
	Se cierra sola si te alejas de las mesas.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Exploracion.Config)
local Crafteo = require(Shared.Exploracion.Crafteo)
local Mejoras = require(Shared.Naves.Datos.Mejoras)
local Estadisticas = require(Shared.Naves.Estadisticas)
local Objetos = require(Shared.Exploracion.Datos.Objetos)
local Recetas = require(Shared.Exploracion.Datos.Recetas)
local Avisos = require(script.Parent.Avisos)
local Estilo = require(script.Parent.Estilo)
local ServicioDatos = require(script.Parent.Parent.Servicios.ServicioDatos)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)

local PanelCrafteo = {}

local NOMBRES_ESTADISTICAS = Estilo.NombresEstadisticas

local pantalla: ScreenGui? = nil
local panel: Frame? = nil
local lista: ScrollingFrame? = nil
local detalle: Frame? = nil
local abierto = false
local seleccionada: string = Recetas.Orden[1]

-- Formato de un número para la interfaz: sin decimales si es entero, con uno si no.
local function numero(valor: number): string
	if math.abs(valor - math.floor(valor + 0.5)) < 0.005 then
		return tostring(math.floor(valor + 0.5))
	end
	return string.format("%.1f", valor)
end

local function nombreDe(id: string): string
	if id == "Monedas" then
		return "Monedas"
	end
	local objeto = Objetos.Lista[id]
	return if objeto then objeto.Nombre else id
end

local function capacidadDe(datos: any): number
	return Estadisticas.Calcular(datos.MejorasNave).Capacidad
end

-- Pide fabricar al servidor.
local function fabricar(cantidad: number)
	local datos = ServicioDatos.Obtener()
	if datos == nil then
		return
	end
	-- Aviso inmediato si no se puede (el servidor lo comprueba igualmente).
	local plan = Crafteo.Planificar(datos, seleccionada, capacidadDe(datos), cantidad)
	if not plan.Ok then
		Avisos.Mostrar(Crafteo.Mensajes[plan.Motivo :: string], "Mal")
		return
	end
	if Recetas.Lista[seleccionada].Categoria == "Mejora" then
		ServicioRed.Enviar("FabricarReceta", seleccionada)
	else
		ServicioRed.Enviar("FabricarReceta", seleccionada, cantidad)
	end
end

-- Dibuja la receta elegida en la parte derecha.
local function pintarDetalle()
	local contenedor, datos = detalle, ServicioDatos.Obtener()
	if contenedor == nil or datos == nil then
		return
	end
	for _, hijo in contenedor:GetChildren() do
		hijo:Destroy()
	end

	local receta = Recetas.Lista[seleccionada]
	local capacidad = capacidadDe(datos)
	local plan = Crafteo.Planificar(datos, seleccionada, capacidad, 1)

	local y = 0
	local nombre =
		Estilo.Etiqueta(contenedor, receta.Nombre, 18, Estilo.TEXTO, UDim2.new(1, 0, 0, 24), UDim2.fromOffset(0, y))
	nombre.TextWrapped = false
	y += 26

	local idMejora = receta.Resultado.Mejora
	local nivel = if idMejora then Estadisticas.NivelValido(datos.MejorasNave[idMejora]) else 0
	local subtitulo = if idMejora
		then `Mejora de la nave · {Mejoras.Lista[idMejora].Nombre} nivel {nivel} → {math.min(
			nivel + 1,
			Mejoras.NivelMaximo
		)}`
		else "Objeto"
	local etiquetaSub =
		Estilo.Etiqueta(contenedor, subtitulo, 12, Estilo.CIAN, UDim2.new(1, 0, 0, 16), UDim2.fromOffset(0, y))
	etiquetaSub.TextWrapped = false
	y += 20

	local descripcion = Estilo.Etiqueta(
		contenedor,
		receta.Descripcion,
		12,
		Estilo.TEXTO_SUAVE,
		UDim2.new(1, 0, 0, 30),
		UDim2.fromOffset(0, y),
		false
	)
	descripcion.TextYAlignment = Enum.TextYAlignment.Top
	y += 36

	Estilo.Etiqueta(contenedor, "NECESITAS", 11, Estilo.TEXTO_SUAVE, UDim2.new(1, 0, 0, 14), UDim2.fromOffset(0, y))
	y += 16
	for _, requisito in plan.Requisitos do
		local suficiente = requisito.Tiene >= requisito.Necesita
		local fila = Estilo.Etiqueta(
			contenedor,
			`{nombreDe(requisito.Id)}: {numero(requisito.Tiene)} / {numero(requisito.Necesita)}`,
			13,
			if suficiente then Estilo.VERDE else Estilo.ROJO,
			UDim2.new(1, 0, 0, Estilo.Texto(13) + 4),
			UDim2.fromOffset(0, y),
			false
		)
		fila.TextWrapped = false
		y += Estilo.Texto(13) + 5
	end
	y += 6

	-- Qué se obtiene.
	Estilo.Etiqueta(contenedor, "OBTIENES", 11, Estilo.TEXTO_SUAVE, UDim2.new(1, 0, 0, 14), UDim2.fromOffset(0, y))
	y += 16
	if idMejora then
		local ahora = Estadisticas.Calcular(datos.MejorasNave)
		local siguiente = Estadisticas.Calcular({ [idMejora] = math.min(nivel + 1, Mejoras.NivelMaximo) })
		for estadistica in Mejoras.Lista[idMejora].Efectos do
			-- Se compara contra las mismas mejoras con ese nivel subido (las demás no influyen en esta estadística).
			local antes = (ahora :: any)[estadistica]
			local despues = (siguiente :: any)[estadistica]
			local fila = Estilo.Etiqueta(
				contenedor,
				`{NOMBRES_ESTADISTICAS[estadistica] or estadistica}: {numero(antes)} → {numero(despues)}`,
				13,
				Estilo.TEXTO,
				UDim2.new(1, 0, 0, Estilo.Texto(13) + 4),
				UDim2.fromOffset(0, y),
				false
			)
			fila.TextWrapped = false
			y += Estilo.Texto(13) + 5
		end
	else
		for id, cantidad in plan.Anade do
			local fila = Estilo.Etiqueta(
				contenedor,
				`{cantidad} × {nombreDe(id)}`,
				13,
				Estilo.TEXTO,
				UDim2.new(1, 0, 0, Estilo.Texto(13) + 4),
				UDim2.fromOffset(0, y),
				false
			)
			fila.TextWrapped = false
			y += Estilo.Texto(13) + 5
		end
	end

	-- Botones.
	local colorBoton = if plan.Ok then Estilo.VERDE else Estilo.TEXTO_SUAVE
	local alto = if Estilo.EsMovil then 38 else 32
	local boton = Estilo.Boton(
		contenedor,
		"Fabricar",
		UDim2.fromOffset(120, alto),
		UDim2.new(0, 0, 1, -alto),
		colorBoton,
		function()
			fabricar(1)
		end
	)
	boton.Name = "Fabricar"
	if not idMejora then
		Estilo.Boton(contenedor, "× 5", UDim2.fromOffset(60, alto), UDim2.new(0, 128, 1, -alto), colorBoton, function()
			fabricar(5)
		end)
	end
	if not plan.Ok and plan.Motivo ~= nil then
		local motivo = Estilo.Etiqueta(
			contenedor,
			Crafteo.Mensajes[plan.Motivo],
			12,
			Estilo.AMARILLO,
			UDim2.new(1, 0, 0, 30),
			UDim2.new(0, 0, 1, -alto - 34),
			false
		)
		motivo.TextYAlignment = Enum.TextYAlignment.Bottom
	end
end

-- Lista de recetas de la izquierda.
local function pintarLista()
	local contenedor, datos = lista, ServicioDatos.Obtener()
	if contenedor == nil or datos == nil then
		return
	end
	for _, hijo in contenedor:GetChildren() do
		if hijo:IsA("TextButton") then
			hijo:Destroy()
		end
	end
	local capacidad = capacidadDe(datos)
	for indice, id in Recetas.Orden do
		local receta = Recetas.Lista[id]
		local plan = Crafteo.Planificar(datos, id, capacidad, 1)
		local elegida = id == seleccionada
		local color = if plan.Ok then Estilo.VERDE elseif elegida then Estilo.CIAN else Estilo.TEXTO_SUAVE
		local boton = Instance.new("TextButton")
		boton.AutoButtonColor = true
		boton.BackgroundColor3 = if elegida then Color3.fromRGB(34, 44, 74) else Color3.fromRGB(22, 26, 44)
		boton.BorderSizePixel = 0
		boton.Size = UDim2.new(1, -6, 0, Estilo.Texto(13) + 16)
		boton.LayoutOrder = indice
		boton.Text = (if receta.Categoria == "Mejora" then "▲ " else "") .. receta.Nombre
		boton.Font = Enum.Font.GothamBold
		boton.TextSize = Estilo.Texto(12)
		boton.TextColor3 = color
		boton.TextXAlignment = Enum.TextXAlignment.Left
		boton.TextTruncate = Enum.TextTruncate.AtEnd
		boton.Parent = contenedor
		Estilo.Redondear(boton, 6)
		local relleno = Instance.new("UIPadding")
		relleno.PaddingLeft = UDim.new(0, 8)
		relleno.PaddingRight = UDim.new(0, 6)
		relleno.Parent = boton
		boton.Activated:Connect(function()
			seleccionada = id
			pintarLista()
			pintarDetalle()
		end)
	end
end

local function refrescar()
	if abierto then
		pintarLista()
		pintarDetalle()
	end
end

function PanelCrafteo.Cerrar()
	abierto = false
	if panel then
		panel.Visible = false
	end
end

-- Distancia a la mesa más cercana (math.huge si no hay ninguna).
local function distanciaAMesa(): number
	local personaje = Players.LocalPlayer.Character
	local raiz = if personaje then personaje:FindFirstChild("HumanoidRootPart") else nil
	if raiz == nil or not raiz:IsA("BasePart") then
		return math.huge
	end
	local menor = math.huge
	for _, mesa in CollectionService:GetTagged(Config.EtiquetaMesa) do
		local posicion = if mesa:IsA("Model")
			then mesa:GetPivot().Position
			elseif mesa:IsA("BasePart") then mesa.Position
			else nil
		if posicion then
			menor = math.min(menor, ((raiz :: BasePart).Position - posicion).Magnitude)
		end
	end
	return menor
end

function PanelCrafteo.Abrir()
	if panel == nil then
		return
	end
	abierto = true
	panel.Visible = true
	refrescar()
	-- Se cierra sola si el jugador se aleja de las mesas.
	task.spawn(function()
		while abierto do
			if distanciaAMesa() > Config.AlcanceMesa * 1.5 then
				PanelCrafteo.Cerrar()
				return
			end
			task.wait(0.5)
		end
	end)
end

-- Resultado de un intento (del servidor).
function PanelCrafteo.AlRecibirResultado(idReceta: string, ok: boolean, mensaje: string?)
	local receta = Recetas.Lista[idReceta]
	local nombre = if receta then receta.Nombre else idReceta
	if ok then
		Avisos.Mostrar(`Fabricado: {nombre}`, "Bien")
	else
		Avisos.Mostrar(mensaje or "No se pudo fabricar", "Mal")
	end
	refrescar()
end

function PanelCrafteo.Iniciar()
	if pantalla then
		return
	end
	local nueva = Estilo.Pantalla("CrafteoExploracion", 19)
	nueva.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	pantalla = nueva

	local ancho = if Estilo.EsMovil then 440 else 600
	local marco = Estilo.Panel(nueva, UDim2.fromOffset(ancho, 380), UDim2.fromScale(0.5, 0.5), Estilo.VERDE)
	marco.AnchorPoint = Vector2.new(0.5, 0.5)
	marco.Visible = false
	panel = marco

	Estilo.Etiqueta(marco, "MESA DE CRAFTEO", 16, Estilo.VERDE, UDim2.new(1, -60, 0, 22), UDim2.fromOffset(14, 10))
	Estilo.Boton(marco, "×", UDim2.fromOffset(28, 28), UDim2.new(1, -40, 0, 8), Estilo.ROJO, PanelCrafteo.Cerrar).TextSize =
		18

	local desplazable = Instance.new("ScrollingFrame")
	desplazable.BackgroundTransparency = 1
	desplazable.BorderSizePixel = 0
	desplazable.Position = UDim2.fromOffset(12, 44)
	desplazable.Size = UDim2.new(0, if Estilo.EsMovil then 150 else 190, 1, -56)
	desplazable.ScrollBarThickness = 4
	desplazable.CanvasSize = UDim2.new()
	desplazable.AutomaticCanvasSize = Enum.AutomaticSize.Y
	desplazable.Parent = marco
	local disposicion = Instance.new("UIListLayout")
	disposicion.Padding = UDim.new(0, 4)
	disposicion.SortOrder = Enum.SortOrder.LayoutOrder
	disposicion.Parent = desplazable
	lista = desplazable

	local derecha = Instance.new("Frame")
	derecha.BackgroundTransparency = 1
	derecha.Position = UDim2.new(0, (if Estilo.EsMovil then 150 else 190) + 26, 0, 44)
	derecha.Size = UDim2.new(1, -((if Estilo.EsMovil then 150 else 190) + 40), 1, -56)
	derecha.Parent = marco
	detalle = derecha

	ServicioDatos.Actualizados:Conectar(refrescar)
end

return PanelCrafteo
