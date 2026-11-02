--!strict
--[[
	Pool: reutiliza los objetos de los efectos en vez de crearlos y destruirlos cada vez.

	Crear Instancias es caro, y en móvil provoca tirones. Cada clase de objeto tiene su "cesta" de libres:
	`Obtener` saca uno (o lo crea si la cesta está vacía) y `Liberar` lo devuelve limpio. Si la cesta ya
	está llena, el sobrante se destruye, así que la memoria no crece sin control.

	Clases:
	  Parte("Bola" | "Bloque" | "Cilindro" | "Malla")   Part sin colisión, anclada, lista para tweens.
	  Emisor()    Part invisible con un ParticleEmitter apagado.
	  Luz()       Part invisible con un PointLight.
	  Rastro()    Part con un Trail y sus dos Attachments.
	  Haz()       Cadena de Attachments unidos por Beams (rayos con zigzag).

	Todo vive en `workspace.VFXLocal`, una carpeta que solo existe en este cliente.
]]

local Pool = {}

local MAXIMO_LIBRES = 60
local MAXIMO_SEGMENTOS = 12

export type Haz = {
	Raiz: Part,
	Adjuntos: { Attachment },
	Rayos: { Beam },
}

local carpeta: Folder? = nil
local libres: { [string]: { any } } = {}
local claseDe: { [any]: string } = setmetatable({}, { __mode = "k" }) :: any

-- Carpeta donde viven los objetos de efectos (se crea al primer uso).
function Pool.Carpeta(): Folder
	if carpeta == nil or carpeta.Parent == nil then
		local nueva = Instance.new("Folder")
		nueva.Name = "VFXLocal"
		nueva.Parent = workspace
		carpeta = nueva
	end
	return carpeta :: Folder
end

-- ===== Fabricación =====

local function configurarParte(parte: Part)
	parte.Anchored = true
	parte.CanCollide = false
	parte.CanQuery = false
	parte.CanTouch = false
	parte.CastShadow = false
	parte.Massless = true
	parte.Material = Enum.Material.Neon
	parte.TopSurface = Enum.SurfaceType.Smooth
	parte.BottomSurface = Enum.SurfaceType.Smooth
	parte.Transparency = 1
	parte.Size = Vector3.one
end

local function nuevaParte(forma: Enum.PartType?): Part
	local parte = Instance.new("Part")
	configurarParte(parte)
	if forma then
		parte.Shape = forma
	end
	return parte
end

local fabricas: { [string]: () -> any } = {
	Bola = function()
		return nuevaParte(Enum.PartType.Ball)
	end,
	Bloque = function()
		return nuevaParte(Enum.PartType.Block)
	end,
	Cilindro = function()
		return nuevaParte(Enum.PartType.Cylinder)
	end,
	Malla = function()
		local parte = nuevaParte(Enum.PartType.Block)
		local malla = Instance.new("SpecialMesh")
		malla.Name = "Malla"
		malla.MeshType = Enum.MeshType.FileMesh
		malla.Parent = parte
		return parte
	end,
	Emisor = function()
		local parte = nuevaParte(Enum.PartType.Block)
		local emisor = Instance.new("ParticleEmitter")
		emisor.Name = "Emisor"
		emisor.Enabled = false
		emisor.Rate = 0
		emisor.LightInfluence = 0
		emisor.Parent = parte
		return parte
	end,
	Luz = function()
		local parte = nuevaParte(Enum.PartType.Ball)
		parte.Size = Vector3.one * 0.2
		local luz = Instance.new("PointLight")
		luz.Name = "Luz"
		luz.Shadows = false
		luz.Enabled = false
		luz.Parent = parte
		return parte
	end,
	Rastro = function()
		local parte = nuevaParte(Enum.PartType.Block)
		parte.Size = Vector3.one * 0.2
		local a0 = Instance.new("Attachment")
		a0.Name = "A0"
		a0.Parent = parte
		local a1 = Instance.new("Attachment")
		a1.Name = "A1"
		a1.Parent = parte
		local rastro = Instance.new("Trail")
		rastro.Name = "Rastro"
		rastro.Attachment0 = a0
		rastro.Attachment1 = a1
		rastro.FaceCamera = true
		rastro.LightInfluence = 0
		rastro.Enabled = false
		rastro.Parent = parte
		return parte
	end,
	Haz = function()
		local raiz = nuevaParte(Enum.PartType.Block)
		raiz.Size = Vector3.one * 0.2
		local adjuntos, rayos = {}, {}
		for indice = 1, MAXIMO_SEGMENTOS + 1 do
			local adjunto = Instance.new("Attachment")
			adjunto.Name = `P{indice}`
			adjunto.Parent = raiz
			adjuntos[indice] = adjunto
		end
		for indice = 1, MAXIMO_SEGMENTOS do
			local rayo = Instance.new("Beam")
			rayo.Name = `R{indice}`
			rayo.Attachment0 = adjuntos[indice]
			rayo.Attachment1 = adjuntos[indice + 1]
			rayo.FaceCamera = true
			rayo.Segments = 1
			rayo.LightInfluence = 0
			rayo.Enabled = false
			rayo.Parent = raiz
			rayos[indice] = rayo
		end
		return { Raiz = raiz, Adjuntos = adjuntos, Rayos = rayos } :: Haz
	end,
}

-- ===== Reciclado =====

local function raizDe(objeto: any): Part
	if typeof(objeto) == "Instance" then
		return objeto :: Part
	end
	return (objeto :: Haz).Raiz
end

-- Deja el objeto como nuevo antes de guardarlo.
local function limpiar(clase: string, objeto: any)
	if clase == "Emisor" then
		local emisor = (objeto :: Part):FindFirstChild("Emisor") :: ParticleEmitter
		emisor.Enabled = false
		emisor.Rate = 0
		emisor:Clear()
	elseif clase == "Luz" then
		((objeto :: Part):FindFirstChild("Luz") :: PointLight).Enabled = false
	elseif clase == "Rastro" then
		local rastro = (objeto :: Part):FindFirstChild("Rastro") :: Trail
		rastro.Enabled = false
		rastro:Clear()
	elseif clase == "Haz" then
		for _, rayo in (objeto :: Haz).Rayos do
			rayo.Enabled = false
		end
	end
	raizDe(objeto).Transparency = 1
end

local function obtener(clase: string): any
	local cesta = libres[clase]
	local objeto = if cesta and #cesta > 0 then table.remove(cesta) else fabricas[clase]()
	claseDe[objeto] = clase
	raizDe(objeto).Parent = Pool.Carpeta()
	return objeto
end

-- ===== API =====

function Pool.Parte(clase: string): Part
	return obtener(clase) :: Part
end

-- Devuelve la Part y su ParticleEmitter (apagado y sin partículas).
function Pool.Emisor(): (Part, ParticleEmitter)
	local parte = obtener("Emisor") :: Part
	return parte, parte:FindFirstChild("Emisor") :: ParticleEmitter
end

function Pool.Luz(): (Part, PointLight)
	local parte = obtener("Luz") :: Part
	return parte, parte:FindFirstChild("Luz") :: PointLight
end

-- Devuelve la Part, el Trail y sus dos Attachments.
function Pool.Rastro(): (Part, Trail, Attachment, Attachment)
	local parte = obtener("Rastro") :: Part
	return parte,
		parte:FindFirstChild("Rastro") :: Trail,
		parte:FindFirstChild("A0") :: Attachment,
		parte:FindFirstChild("A1") :: Attachment
end

function Pool.Haz(): Haz
	return obtener("Haz") :: Haz
end

-- Devuelve el objeto (de cualquier clase) a su cesta. Es seguro llamarlo dos veces.
function Pool.Liberar(objeto: any)
	local clase = claseDe[objeto]
	if clase == nil then
		return -- ya liberado, o no es del pool
	end
	claseDe[objeto] = nil

	limpiar(clase, objeto)
	local raiz = raizDe(objeto)
	raiz.Parent = nil

	local cesta = libres[clase]
	if cesta == nil then
		cesta = {}
		libres[clase] = cesta
	end
	if #cesta < MAXIMO_LIBRES then
		table.insert(cesta, objeto)
	else
		raiz:Destroy()
	end
end

-- Libera el objeto pasado un tiempo.
function Pool.LiberarEn(objeto: any, segundos: number)
	task.delay(segundos, Pool.Liberar, objeto)
end

--[[
	Crea de antemano unos cuantos objetos (repartidos en varios fotogramas) para que el primer efecto
	no provoque un tirón al fabricarlos.
]]
function Pool.Precalentar()
	local pedido = { Bola = 8, Bloque = 12, Cilindro = 8, Emisor = 10, Luz = 3, Rastro = 4, Haz = 3 }
	task.spawn(function()
		for clase, cantidad in pedido do
			local creados = {}
			for _ = 1, cantidad do
				table.insert(creados, obtener(clase))
			end
			for _, objeto in creados do
				Pool.Liberar(objeto)
			end
			task.wait()
		end
	end)
end

Pool.MaximoSegmentos = MAXIMO_SEGMENTOS

return Pool
