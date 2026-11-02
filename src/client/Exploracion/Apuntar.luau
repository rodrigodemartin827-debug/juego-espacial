--!strict
--[[
	Apuntar (Exploración): encuentra lo que el jugador está mirando con el escáner o con el pico.

	  1. Lanza un rayo desde la cámara por la posición del ratón (o por el centro de la pantalla en móvil o con mando) y
	     busca, entre lo que toca y sus antepasados, algo con la etiqueta pedida.
	  2. Si no hay nada justo en la mira, "se pega" al objeto con esa etiqueta que esté más cerca de la línea de mira, dentro de
	     un cono pequeño (Exploracion/Escaner.MejorObjetivo). Así no hace falta puntería de cirujano, sobre todo en móvil.

	Solo se consideran los objetos al alcance del personaje. El cliente propone y el servidor decide: esto no es una
	validación, solo comodidad.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Escaner = require(ReplicatedStorage:WaitForChild("Shared").Exploracion.Escaner)

local Apuntar = {}

-- Posición central y radio aproximado de un objeto (Model o Part).
local function medida(objeto: Instance): (Vector3, number)
	if objeto:IsA("Model") then
		local marco, tamano = objeto:GetBoundingBox()
		return marco.Position, math.max(tamano.X, tamano.Y, tamano.Z) / 2
	elseif objeto:IsA("BasePart") then
		return objeto.Position, math.max(objeto.Size.X, objeto.Size.Y, objeto.Size.Z) / 2
	end
	return Vector3.zero, 0
end

-- El antepasado (o la propia instancia) que lleva la etiqueta, o nil.
local function conEtiqueta(instancia: Instance, etiqueta: string): Instance?
	local actual: Instance? = instancia
	while actual ~= nil and actual ~= workspace do
		if CollectionService:HasTag(actual, etiqueta) then
			return actual
		end
		actual = actual.Parent
	end
	return nil
end

-- ¿Está el CENTRO del jugador a menos de `alcance` studs de la superficie del objeto?
local function alAlcance(raiz: BasePart, objeto: Instance, alcance: number): boolean
	local centro, radio = medida(objeto)
	return (raiz.Position - centro).Magnitude - radio <= alcance
end

--[[
	Devuelve el objeto con `etiqueta` al que apunta el jugador, o nil.
	  alcance        studs desde el personaje hasta la superficie del objeto
	  anguloAyuda    grados del cono de ayuda de puntería
]]
function Apuntar.Buscar(etiqueta: string, alcance: number, anguloAyuda: number): Instance?
	local personaje = Players.LocalPlayer.Character
	local raiz = if personaje then personaje:FindFirstChild("HumanoidRootPart") else nil
	local camara = workspace.CurrentCamera
	if personaje == nil or raiz == nil or not raiz:IsA("BasePart") or camara == nil then
		return nil
	end

	-- Rayo de la mira: por el ratón si hay uno, por el centro de la pantalla si no.
	local punto = if UserInputService.MouseEnabled then UserInputService:GetMouseLocation() else camara.ViewportSize / 2
	local rayo = camara:ViewportPointToRay(punto.X, punto.Y)
	local distanciaCamara = (camara.CFrame.Position - (raiz :: BasePart).Position).Magnitude

	local ignorar: { Instance } = { personaje }
	for _, nombre in { "EscaneoLocal", "VFXLocal" } do
		local carpeta = workspace:FindFirstChild(nombre)
		if carpeta then
			table.insert(ignorar, carpeta)
		end
	end
	local parametros = RaycastParams.new()
	parametros.FilterType = Enum.RaycastFilterType.Exclude
	parametros.FilterDescendantsInstances = ignorar

	local largo = alcance + distanciaCamara + 20
	local golpe = workspace:Raycast(rayo.Origin, rayo.Direction * largo, parametros)
	if golpe then
		local objeto = conEtiqueta(golpe.Instance, etiqueta)
		if objeto and alAlcance(raiz :: BasePart, objeto, alcance) then
			return objeto
		end
	end

	-- Ayuda de puntería: el objeto más cercano a la línea de mira, dentro del cono.
	local candidatos: { { Posicion: Escaner.Punto, Objeto: Instance } } = {}
	for _, objeto in CollectionService:GetTagged(etiqueta) do
		if objeto:IsDescendantOf(workspace) and alAlcance(raiz :: BasePart, objeto, alcance) then
			local centro = medida(objeto)
			table.insert(candidatos, { Posicion = { X = centro.X, Y = centro.Y, Z = centro.Z }, Objeto = objeto })
		end
	end
	local origen, direccion = rayo.Origin, rayo.Direction
	local indice = Escaner.MejorObjetivo(
		{ X = origen.X, Y = origen.Y, Z = origen.Z },
		{ X = direccion.X, Y = direccion.Y, Z = direccion.Z },
		candidatos,
		largo,
		anguloAyuda
	)
	return if indice then candidatos[indice].Objeto else nil
end

return Apuntar
