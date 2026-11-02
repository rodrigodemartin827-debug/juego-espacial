--!strict
--[[
	Ficha (Exploración): la ficha en pantalla que aparece al terminar un análisis con el escáner.

	Muestra la categoría (criatura, planta o mineral), el nombre, la rareza (con su color), la descripción, las filas de
	datos de la especie (Exploracion/Datos/Especies) y la recompensa. Si es la primera vez que se escanea esa especie se
	marca como NUEVO DESCUBRIMIENTO; si no, cuántas veces se ha analizado ya.

	Entra deslizándose desde la derecha, las filas aparecen una a una (como si el escáner las fuera leyendo) y se retira sola
	a los Ficha.SEGUNDOS_VISIBLE o al pulsar la X. Una ficha nueva sustituye a la anterior.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Especies = require(ReplicatedStorage:WaitForChild("Shared").Exploracion.Datos.Especies)
local Estilo = require(script.Parent.Estilo)
local Utiles = require(script.Parent.Parent.VFX.Utiles)

local Ficha = {}

Ficha.SEGUNDOS_VISIBLE = 10

local ICONOS: { [string]: string } = { Criatura = "CRIATURA", Planta = "PLANTA", Mineral = "MINERAL" }

local pantalla: ScreenGui? = nil
local actual: Frame? = nil
local version = 0 -- para que una ficha nueva cancele la retirada programada de la anterior

local function crearPantalla(): ScreenGui
	if pantalla and pantalla.Parent then
		return pantalla
	end
	local nueva = Estilo.Pantalla("FichaEscaner", 20)
	nueva.Parent = game:GetService("Players").LocalPlayer:WaitForChild("PlayerGui")
	pantalla = nueva
	return nueva
end

-- Quita la ficha que haya en pantalla (con una animación de salida).
function Ficha.Ocultar()
	version += 1
	local marco = actual
	actual = nil
	if marco == nil then
		return
	end
	Utiles.Tween(
		marco,
		0.3,
		{ Position = UDim2.new(1.1, 0, marco.Position.Y.Scale, marco.Position.Y.Offset) },
		"Quad",
		true
	)
	task.delay(0.35, function()
		marco:Destroy()
	end)
end

--[[
	Enseña la ficha de una especie.
	  idEspecie   id de Exploracion/Datos/Especies
	  nuevo       true si es la primera vez que el jugador la escanea
	  xp, monedas recompensa de este escaneo
	  veces       cuántas veces la ha escaneado ya (contando esta)
]]
function Ficha.Mostrar(idEspecie: string, nuevo: boolean, xp: number, monedas: number, veces: number)
	local especie = Especies.Lista[idEspecie]
	if especie == nil then
		return
	end
	if actual then
		actual:Destroy()
		actual = nil
	end
	version += 1
	local miVersion = version

	local colorRareza = Estilo.Hex(Especies.ColoresRareza[especie.Rareza])
	local ancho = if Estilo.EsMovil then 260 else 330
	local alto = 150 + #especie.Datos * (Estilo.Texto(13) + 8) + (if nuevo then 24 else 0)

	local marco = Estilo.Panel(crearPantalla(), UDim2.fromOffset(ancho, alto), UDim2.new(1.1, 0, 0.5, 0), colorRareza)
	marco.AnchorPoint = Vector2.new(1, 0.5)
	actual = marco

	-- Franja de color de la rareza.
	local franja = Instance.new("Frame")
	franja.BackgroundColor3 = colorRareza
	franja.BorderSizePixel = 0
	franja.Size = UDim2.new(1, -20, 0, 3)
	franja.Position = UDim2.fromOffset(10, 8)
	franja.Parent = marco

	local y = 18
	local categoria = Estilo.Etiqueta(
		marco,
		`{ICONOS[especie.Categoria] or especie.Categoria} · {string.upper(especie.Rareza)}`,
		11,
		colorRareza,
		UDim2.new(1, -50, 0, 16),
		UDim2.fromOffset(12, y)
	)
	categoria.TextWrapped = false
	y += 18

	local nombre =
		Estilo.Etiqueta(marco, especie.Nombre, 20, Estilo.TEXTO, UDim2.new(1, -24, 0, 26), UDim2.fromOffset(12, y))
	nombre.TextWrapped = false
	y += 28

	if nuevo then
		local etiquetaNuevo = Estilo.Etiqueta(
			marco,
			"★ NUEVO DESCUBRIMIENTO",
			12,
			Estilo.AMARILLO,
			UDim2.new(1, -24, 0, 18),
			UDim2.fromOffset(12, y)
		)
		etiquetaNuevo.TextWrapped = false
		y += 22
	end

	local descripcion = Estilo.Etiqueta(
		marco,
		especie.Descripcion,
		12,
		Estilo.TEXTO_SUAVE,
		UDim2.new(1, -24, 0, 50),
		UDim2.fromOffset(12, y),
		false
	)
	descripcion.TextYAlignment = Enum.TextYAlignment.Top
	y += 54

	-- Las filas de datos aparecen escalonadas.
	local filas: { TextLabel } = {}
	for _, fila in especie.Datos do
		local texto = Estilo.Etiqueta(
			marco,
			`<font color="#A5AFCD">{fila[1]}</font>  {fila[2]}`,
			13,
			Estilo.TEXTO,
			UDim2.new(1, -24, 0, Estilo.Texto(13) + 4),
			UDim2.fromOffset(12, y),
			false
		)
		texto.RichText = true
		texto.TextWrapped = false
		texto.TextTransparency = 1
		table.insert(filas, texto)
		y += Estilo.Texto(13) + 8
	end

	-- Recompensa.
	local pie = if xp > 0 or monedas > 0 then `+{xp} XP   +{monedas} monedas` else `Ya analizada · {veces} escaneos`
	if xp > 0 and not nuevo then
		pie ..= `   ({veces} escaneos)`
	end
	Estilo.Etiqueta(marco, pie, 13, Estilo.VERDE, UDim2.new(1, -24, 0, 18), UDim2.new(0, 12, 1, -28))

	-- Cerrar.
	local cerrar = Estilo.Boton(marco, "×", UDim2.fromOffset(26, 26), UDim2.new(1, -34, 0, 14), Estilo.ROJO, function()
		Ficha.Ocultar()
	end)
	cerrar.TextSize = 18

	-- Entrada y lectura de las filas.
	Utiles.Tween(marco, 0.45, { Position = UDim2.new(1, -16, 0.5, 0) }, "Back")
	for indice, texto in filas do
		task.delay(0.35 + indice * 0.12, function()
			if miVersion == version then
				Utiles.Tween(texto, 0.25, { TextTransparency = 0 }, "Quad")
			end
		end)
	end

	task.delay(Ficha.SEGUNDOS_VISIBLE, function()
		if miVersion == version then
			Ficha.Ocultar()
		end
	end)
end

return Ficha
