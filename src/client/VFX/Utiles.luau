--!strict
--[[
	Utiles (VFX): conversiones entre los DATOS de los efectos (texto, números y listas) y los tipos de
	Roblox (Color3, NumberSequence, Vector3...), más el cálculo de los puntos donde se colocan las capas.

	Los datos de Datos/EfectosVFX son tablas puras para poder editarlas sin saber de Roblox; este módulo
	es el traductor.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Config = require(ReplicatedStorage:WaitForChild("Shared").Combate.Config)

local Utiles = {}

Utiles.Azar = Random.new()

-- ===== Colores =====

-- "#RRGGBB" -> Color3.
function Utiles.Hex(hex: string): Color3
	local r, g, b = string.match(hex, "^#?(%x%x)(%x%x)(%x%x)$")
	if r == nil then
		warn(`[VFX] Color no válido: '{hex}'`)
		return Color3.new(1, 1, 1)
	end
	return Color3.fromRGB(tonumber(r, 16) :: number, tonumber(g, 16) :: number, tonumber(b, 16) :: number)
end

-- Un color de la paleta del efecto ("Principal") o un hexadecimal suelto ("#FF8800").
function Utiles.Color(especificacion: any, paleta: { [string]: string }): Color3
	local texto = if type(especificacion) == "string" then (paleta[especificacion] or especificacion) else "#FFFFFF"
	return Utiles.Hex(texto)
end

-- Un color o una lista de colores repartidos a partes iguales -> ColorSequence.
function Utiles.Gradiente(especificacion: any, paleta: { [string]: string }): ColorSequence
	if type(especificacion) ~= "table" then
		return ColorSequence.new(Utiles.Color(especificacion, paleta))
	end
	local lista = especificacion :: { any }
	if #lista == 1 then
		return ColorSequence.new(Utiles.Color(lista[1], paleta))
	end
	local puntos = {}
	for indice, valor in lista do
		table.insert(puntos, ColorSequenceKeypoint.new((indice - 1) / (#lista - 1), Utiles.Color(valor, paleta)))
	end
	return ColorSequence.new(puntos)
end

-- ===== Números =====

-- Un número o una lista de números repartidos a partes iguales -> NumberSequence (con un factor opcional).
function Utiles.Numeros(valores: any, factor: number?): NumberSequence
	local multiplicador = factor or 1
	if type(valores) ~= "table" then
		return NumberSequence.new((valores or 0) * multiplicador)
	end
	local lista = valores :: { number }
	if #lista == 1 then
		return NumberSequence.new(lista[1] * multiplicador)
	end
	local puntos = {}
	for indice, valor in lista do
		table.insert(puntos, NumberSequenceKeypoint.new((indice - 1) / (#lista - 1), valor * multiplicador))
	end
	return NumberSequence.new(puntos)
end

-- Un número o { mínimo, máximo } -> NumberRange.
function Utiles.Rango(valores: any): NumberRange
	if type(valores) == "table" then
		local lista = valores :: { number }
		return NumberRange.new(lista[1], lista[2] or lista[1])
	end
	return NumberRange.new(valores or 0)
end

-- Un número o { mínimo, máximo } -> un valor al azar entre ambos.
function Utiles.Elegir(valores: any, porDefecto: number?): number
	if type(valores) == "table" then
		local lista = valores :: { number }
		return Utiles.Azar:NextNumber(lista[1], lista[2] or lista[1])
	end
	return valores or porDefecto or 0
end

-- { x, y, z } -> Vector3 (nil = cero).
function Utiles.V3(lista: { number }?): Vector3
	if lista == nil then
		return Vector3.zero
	end
	return Vector3.new(lista[1] or 0, lista[2] or 0, lista[3] or 0)
end

-- Número entero de elementos tras aplicar el factor de calidad (al menos 1 si la cantidad pedida no era 0).
function Utiles.Cantidad(base: number, factor: number): number
	if base <= 0 or factor <= 0 then
		return 0
	end
	return math.max(1, math.floor(base * factor + 0.5))
end

-- ===== Tweens =====

local ESTILOS: { [string]: Enum.EasingStyle } = {
	Lineal = Enum.EasingStyle.Linear,
	Quad = Enum.EasingStyle.Quad,
	Cubic = Enum.EasingStyle.Cubic,
	Quart = Enum.EasingStyle.Quart,
	Quint = Enum.EasingStyle.Quint,
	Exponential = Enum.EasingStyle.Exponential,
	Sine = Enum.EasingStyle.Sine,
	Back = Enum.EasingStyle.Back,
	Elastic = Enum.EasingStyle.Elastic,
}

-- Anima propiedades de una Instancia. `estilo` es uno de ESTILOS; `entrada` = true usa "In" en vez de "Out".
function Utiles.Tween(
	instancia: Instance,
	segundos: number,
	propiedades: { [string]: any },
	estilo: string?,
	entrada: boolean?
): Tween
	local info = TweenInfo.new(
		math.max(segundos, 0.01),
		ESTILOS[estilo or "Quad"] or Enum.EasingStyle.Quad,
		if entrada then Enum.EasingDirection.In else Enum.EasingDirection.Out
	)
	local tween = TweenService:Create(instancia, info, propiedades)
	tween:Play()
	return tween
end

-- Valor suavizado entre 0 y 1 (para animaciones por código dentro de un bucle).
function Utiles.Suavizar(alfa: number, estilo: string?, entrada: boolean?): number
	return TweenService:GetValue(
		math.clamp(alfa, 0, 1),
		ESTILOS[estilo or "Quad"] or Enum.EasingStyle.Quad,
		if entrada then Enum.EasingDirection.In else Enum.EasingDirection.Out
	)
end

-- ===== Escenario =====

local vfxCarpeta: Instance? = nil

-- Parámetros de raycast que ignoran personajes, muñecos y los propios efectos.
function Utiles.ParametrosEscenario(): RaycastParams
	local ignorar: { Instance } = {}
	for _, objetivo in CollectionService:GetTagged(Config.EtiquetaObjetivo) do
		table.insert(ignorar, objetivo)
	end
	for _, jugador in Players:GetPlayers() do
		if jugador.Character then
			table.insert(ignorar, jugador.Character)
		end
	end
	if vfxCarpeta == nil or vfxCarpeta.Parent == nil then
		vfxCarpeta = workspace:FindFirstChild("VFXLocal")
	end
	if vfxCarpeta then
		table.insert(ignorar, vfxCarpeta)
	end
	local parametros = RaycastParams.new()
	parametros.FilterType = Enum.RaycastFilterType.Exclude
	parametros.FilterDescendantsInstances = ignorar
	return parametros
end

-- Altura del suelo bajo un punto (y su normal). Si no hay suelo, la altura del propio punto menos 3.
function Utiles.Suelo(posicion: Vector3): (number, Vector3)
	local resultado =
		workspace:Raycast(posicion + Vector3.new(0, 20, 0), Vector3.new(0, -120, 0), Utiles.ParametrosEscenario())
	if resultado then
		return resultado.Position.Y, resultado.Normal
	end
	return posicion.Y - 3, Vector3.yAxis
end

-- ===== Anclas =====

local function planoDe(direccion: Vector3): Vector3
	local plano = Vector3.new(direccion.X, 0, direccion.Z)
	if plano.Magnitude < 0.01 then
		return Vector3.new(0, 0, -1)
	end
	return plano.Unit
end

--[[
	Marco de referencia (posición + orientación mirando en la dirección del golpe) de un "ancla".
	  "Lanzador"  el cuerpo del que lanza (posición actual)
	  "Mano"      su mano derecha (o el cuerpo si no la encuentra)
	  "Origen"    donde estaba el lanzador al empezar
	  "Objetivo"  el punto de impacto
	  "Suelo"     el punto de impacto, a la altura del suelo
	  "Cielo"     muy por encima del punto de impacto
	  "Victima"   el cuerpo del golpeado al que se aplica la fase "Golpeado"
	`desplazamiento` = { x, y, z } en el sistema local del ancla (z negativa = hacia delante).
]]
function Utiles.Ancla(ctx: any, nombre: string?, desplazamiento: { number }?): CFrame
	local posicion: Vector3
	local clave = nombre or "Objetivo"

	if clave == "Lanzador" then
		posicion = if ctx.Raiz and ctx.Raiz.Parent then ctx.Raiz.Position else ctx.Origen
	elseif clave == "Mano" then
		local mano = ctx.Lanzador
			and (ctx.Lanzador:FindFirstChild("RightHand") or ctx.Lanzador:FindFirstChild("Right Arm"))
		if mano then
			posicion = (mano :: BasePart).Position
		elseif ctx.Raiz and ctx.Raiz.Parent then
			posicion = ctx.Raiz.Position
		else
			posicion = ctx.Origen
		end
	elseif clave == "Origen" then
		posicion = ctx.Origen
	elseif clave == "Suelo" then
		posicion = Vector3.new(ctx.Punto.X, ctx.SueloY, ctx.Punto.Z)
	elseif clave == "Cielo" then
		posicion = ctx.Punto + Vector3.new(0, ctx.AlturaCielo or 140, 0)
	elseif clave == "Victima" then
		local raiz = ctx.Victima and ctx.Victima:FindFirstChild("HumanoidRootPart")
		posicion = if raiz then (raiz :: BasePart).Position else ctx.Punto
	else -- "Objetivo"
		posicion = ctx.Punto
	end

	local mira = planoDe(ctx.Direccion)
	local marco = CFrame.lookAt(posicion, posicion + mira)
	if desplazamiento then
		marco = marco * CFrame.new(Utiles.V3(desplazamiento))
	end
	return marco
end

return Utiles
