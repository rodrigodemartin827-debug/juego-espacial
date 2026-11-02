--!strict
--[[
	ServicioAsteroides: crea campos de asteroides por código y se encarga de su vida.

	  - `CrearCampo` pide al generador (Naves/GeneradorAsteroides, puro y determinista) las posiciones y las formas
	    y construye los modelos. Con la misma semilla sale siempre el mismo campo.
	  - Cada asteroide es un Model etiquetado ("Asteroide") con su vida en atributos: una esfera central y varios
	    fragmentos de roca pegados, todo anclado. Es sólido para quien camine, pero las naves no chocan con él
	    físicamente (ver ServicioNaves/GruposColision): los choques los decide ServicioNaves.
	  - `Danar` quita vida. Al llegar a 0 el asteroide estalla (avisa a todos los clientes para el efecto), se
	    retira y vuelve a aparecer a los SegundosRenacerAsteroide, siempre que no haya una nave encima.

	Todos los campos cuelgan de una misma carpeta (`Workspace.CamposDeAsteroides`), de modo que las consultas
	espaciales del servidor solo miran ahí.
]]

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local Config = require(Shared.Naves.Config)
local Generador = require(Shared.Naves.GeneradorAsteroides)
local GruposColision = require(script.Parent.ServicioNaves.GruposColision)
local Minerales = require(Shared.Exploracion.Datos.Minerales)
local ServicioMinado = require(script.Parent.ServicioMinado)
local ServicioRed = require(script.Parent.ServicioRed)

export type OpcionesCampo = {
	Nombre: string,
	Semilla: number,
	Cantidad: number,
	Centro: Vector3,
	Radio: number,
	Aplanado: number?,
	TamanoMin: number?,
	TamanoMax: number?,
	Separacion: number?,
	Exclusiones: { { Centro: Vector3, Radio: number } }?,
	-- Fracción de asteroides (0 a 1) que llevan una veta de mineral pegada a la roca. Sin esto, ninguno la lleva.
	ProbabilidadVeta: number?,
}

local ServicioAsteroides = {}

local NOMBRE_RAIZ = "CamposDeAsteroides"
local ESPERA_REINTENTO = 3 -- segundos antes de volver a probar si había una nave encima

local raiz: Folder? = nil

-- Tipo de veta de cada asteroide de cada campo: { [carpeta] = { [indice] = idMineral } }. Se decide al crear el campo
-- (con la semilla, así es siempre el mismo) y se repite cuando el asteroide renace.
local vetasPorCampo: { [Folder]: { [number]: string } } = setmetatable({}, { __mode = "k" }) :: any

-- Descripción de cada asteroide vivo, para poder recrearlo cuando estalle.
local descripciones: { [Model]: Generador.Asteroide } = setmetatable({}, { __mode = "k" }) :: any

-- Colores de la roca, de más claro a más oscuro según el "tono" del asteroide (0..1).
local COLOR_ROCA_CLARO = Color3.fromRGB(158, 146, 132)
local COLOR_ROCA_OSCURO = Color3.fromRGB(82, 74, 68)
local COLOR_BASALTO_CLARO = Color3.fromRGB(86, 82, 92)
local COLOR_BASALTO_OSCURO = Color3.fromRGB(44, 42, 50)

local function vector(punto: Generador.Punto): Vector3
	return Vector3.new(punto.X, punto.Y, punto.Z)
end

local function angulos(giro: Generador.Punto): CFrame
	return CFrame.Angles(giro.X, giro.Y, giro.Z)
end

-- Carpeta que contiene todos los campos (se crea al primer uso).
function ServicioAsteroides.Raiz(): Folder
	if raiz == nil or raiz.Parent == nil then
		local carpeta = Instance.new("Folder")
		carpeta.Name = NOMBRE_RAIZ
		carpeta.Parent = workspace
		raiz = carpeta
	end
	return raiz :: Folder
end

-- Pega a la roca una veta de mineral que sobresale: es lo que se puede picar con los láseres de la nave o a pie.
local function anadirVeta(modelo: Model, descripcion: Generador.Asteroide, indice: number, tipo: string)
	local rng = Random.new(descripcion.Tamano * 1000 + indice)
	local direccion = Vector3.new(rng:NextNumber(-1, 1), rng:NextNumber(-0.4, 1), rng:NextNumber(-1, 1))
	direccion = if direccion.Magnitude > 0.1 then direccion.Unit else Vector3.yAxis
	local tamanoVeta = math.max(4, descripcion.Tamano * 0.4)
	-- Sobre la superficie del núcleo (radio 0,45 × tamaño), un poco hundida para que no parezca flotar.
	local centro = vector(descripcion.Posicion) + direccion * (descripcion.Tamano * 0.45 + tamanoVeta * 0.1)
	local veta = ServicioMinado.CrearNodo(tipo, CFrame.new(centro) * angulos(descripcion.Giro), tamanoVeta)
	veta.Name = "Veta"
	veta.Parent = modelo
end

-- Construye el modelo de un asteroide a partir de su descripción (con una veta de mineral si se indica el tipo).
local function construir(descripcion: Generador.Asteroide, indice: number, tipoVeta: string?): Model
	local claro = if descripcion.Material == "Basalto" then COLOR_BASALTO_CLARO else COLOR_ROCA_CLARO
	local oscuro = if descripcion.Material == "Basalto" then COLOR_BASALTO_OSCURO else COLOR_ROCA_OSCURO
	local color = claro:Lerp(oscuro, descripcion.Tono)
	local material = if descripcion.Material == "Basalto" then Enum.Material.Basalt else Enum.Material.Slate
	local centro = CFrame.new(vector(descripcion.Posicion)) * angulos(descripcion.Giro)

	local modelo = Instance.new("Model")
	modelo.Name = `Asteroide{indice}`

	local nucleo = Instance.new("Part")
	nucleo.Name = "Nucleo"
	nucleo.Shape = Enum.PartType.Ball
	nucleo.Size = Vector3.one * descripcion.Tamano * 0.9
	nucleo.CFrame = centro
	nucleo.Color = color
	nucleo.Material = material
	nucleo.Anchored = true
	nucleo.CanTouch = false
	nucleo.Parent = modelo
	modelo.PrimaryPart = nucleo

	for numero, fragmento in descripcion.Fragmentos do
		local parte = Instance.new("Part")
		parte.Name = `Fragmento{numero}`
		parte.Shape = if fragmento.Forma == "Esfera" then Enum.PartType.Ball else Enum.PartType.Block
		parte.Size = vector(fragmento.Tamano)
		parte.CFrame = centro * CFrame.new(vector(fragmento.Desplazamiento)) * angulos(fragmento.Giro)
		-- Cada fragmento es un poco más claro u oscuro que el núcleo, para que la roca tenga relieve.
		local variacion = 0.88 + ((numero * 37 + indice * 11) % 25) / 100
		parte.Color = Color3.new(
			math.clamp(color.R * variacion, 0, 1),
			math.clamp(color.G * variacion, 0, 1),
			math.clamp(color.B * variacion, 0, 1)
		)
		parte.Material = material
		parte.Anchored = true
		parte.CanTouch = false
		parte.Parent = modelo
	end

	if tipoVeta ~= nil then
		anadirVeta(modelo, descripcion, indice, tipoVeta)
	end

	modelo:SetAttribute("Vida", descripcion.Vida)
	modelo:SetAttribute("VidaMax", descripcion.Vida)
	modelo:SetAttribute("Tamano", descripcion.Tamano)
	CollectionService:AddTag(modelo, Config.EtiquetaAsteroide)
	GruposColision.Aplicar(modelo, Config.GrupoAsteroides)
	return modelo
end

-- ¿Hay alguna nave a menos de `distancia` de `posicion`?
local function hayNaveCerca(posicion: Vector3, distancia: number): boolean
	for _, nave in CollectionService:GetTagged(Config.EtiquetaNave) do
		if nave:IsA("Model") and (nave:GetPivot().Position - posicion).Magnitude < distancia then
			return true
		end
	end
	return false
end

--[[
	Crea un campo de asteroides y devuelve su carpeta (dentro de `Workspace.CamposDeAsteroides`).
	Si ya existe un campo con ese nombre, se sustituye.
]]
function ServicioAsteroides.CrearCampo(opciones: OpcionesCampo): Folder
	local contenedor = ServicioAsteroides.Raiz()
	local anterior = contenedor:FindFirstChild(opciones.Nombre)
	if anterior then
		anterior:Destroy()
	end

	local carpeta = Instance.new("Folder")
	carpeta.Name = opciones.Nombre

	local exclusiones: { Generador.Exclusion } = {}
	local zonas = opciones.Exclusiones
	if zonas then
		for _, zona in zonas do
			table.insert(exclusiones, {
				Centro = { X = zona.Centro.X, Y = zona.Centro.Y, Z = zona.Centro.Z },
				Radio = zona.Radio,
			})
		end
	end

	local lista = Generador.Generar({
		Semilla = opciones.Semilla,
		Cantidad = opciones.Cantidad,
		Centro = { X = opciones.Centro.X, Y = opciones.Centro.Y, Z = opciones.Centro.Z },
		Radio = opciones.Radio,
		Aplanado = opciones.Aplanado,
		TamanoMin = opciones.TamanoMin,
		TamanoMax = opciones.TamanoMax,
		Separacion = opciones.Separacion,
		Exclusiones = exclusiones,
	})

	-- Qué asteroides llevan veta y de qué mineral (decidido con la semilla del campo).
	local vetas: { [number]: string } = {}
	local probabilidad = opciones.ProbabilidadVeta or 0
	if probabilidad > 0 then
		local sorteo = Random.new(opciones.Semilla + 7919)
		for indice = 1, #lista do
			local tipo = Minerales.Elegir("Asteroide", sorteo:NextNumber())
			if sorteo:NextNumber() < probabilidad and tipo ~= nil then
				vetas[indice] = tipo
			end
		end
	end
	vetasPorCampo[carpeta] = vetas

	for indice, descripcion in lista do
		local modelo = construir(descripcion, indice, vetas[indice])
		modelo:SetAttribute("Indice", indice)
		modelo.Parent = carpeta
		descripciones[modelo] = descripcion
	end

	carpeta.Parent = contenedor
	return carpeta
end

-- Vuelve a crear un asteroide en su sitio cuando no haya ninguna nave encima.
local function renacer(descripcion: Generador.Asteroide, indice: number, carpeta: Folder)
	if carpeta.Parent == nil then
		return -- el campo se destruyó
	end
	local posicion = vector(descripcion.Posicion)
	if hayNaveCerca(posicion, descripcion.Tamano + 40) then
		task.delay(ESPERA_REINTENTO, renacer, descripcion, indice, carpeta)
		return
	end
	local vetas = vetasPorCampo[carpeta]
	local modelo = construir(descripcion, indice, if vetas then vetas[indice] else nil)
	modelo:SetAttribute("Indice", indice)
	modelo.Parent = carpeta
	descripciones[modelo] = descripcion
end

-- El asteroide al que pertenece una instancia (el Model etiquetado), o nil.
function ServicioAsteroides.AsteroideDe(instancia: Instance): Model?
	local modelo = if instancia:IsA("Model") then instancia else instancia:FindFirstAncestorWhichIsA("Model")
	-- Sube por los Model antepasados: las vetas de mineral son Models anidados dentro del asteroide.
	while modelo ~= nil do
		if modelo:HasTag(Config.EtiquetaAsteroide) then
			return modelo
		end
		modelo = modelo:FindFirstAncestorWhichIsA("Model")
	end
	return nil
end

--[[
	Quita `dano` de vida al asteroide. Si llega a 0 estalla: se avisa a los clientes, se retira y renacerá.
	Devuelve true si lo ha destruido.
]]
function ServicioAsteroides.Danar(asteroide: Model, dano: number): boolean
	if dano ~= dano or dano <= 0 or asteroide.Parent == nil then
		return false
	end
	local vida = asteroide:GetAttribute("Vida")
	if type(vida) ~= "number" then
		return false
	end
	vida -= dano
	asteroide:SetAttribute("Vida", math.max(vida, 0))
	if vida > 0 then
		return false
	end

	local tamano = asteroide:GetAttribute("Tamano")
	local posicion = asteroide:GetPivot().Position
	local descripcion = descripciones[asteroide]
	local indice = asteroide:GetAttribute("Indice")
	local carpeta = asteroide.Parent
	asteroide:Destroy()

	ServicioRed.EnviarATodos("AsteroideDestruido", posicion, if type(tamano) == "number" then tamano else 12)
	if descripcion and type(indice) == "number" and carpeta and carpeta:IsA("Folder") then
		task.delay(Config.SegundosRenacerAsteroide, renacer, descripcion, indice, carpeta)
	end
	return true
end

-- Prepara los grupos de colisión. Debe llamarse una vez al arrancar, antes de crear campos.
function ServicioAsteroides.Iniciar()
	GruposColision.Preparar()
	ServicioAsteroides.Raiz()
end

return ServicioAsteroides
