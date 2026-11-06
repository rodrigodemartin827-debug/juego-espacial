--!strict
--[[
	Efectos (Naves): lo que se VE de las naves, con el mismo motor de efectos del combate (client/VFX/Gestor).

	Escucha los avisos del servidor y reproduce la receta que toca (Naves/Datos/EfectosNave):

	  NaveDisparo         fogonazo, proyectil con estela y haz de luz del color del bando
	  NaveImpacto         el láser pega en un escudo, un casco, un asteroide o el escenario
	  NaveChoque          una nave roza o choca con un asteroide
	  NaveDestruida       explosión de una nave
	  AsteroideDestruido  un asteroide estalla, con más fuerza cuanto más grande es
	  NaveDespegue        los motores arrancan en el hangar

	Además mantiene los PROPULSORES de todas las naves que se mueven: cada pocas décimas lanza un pulso de
	partículas, luz y brillo desde las dos toberas (receta normal o de turbo según el atributo "Turbo" que fija el
	servidor), y avisa con un destello cuando alguien enciende el turbo. Las naves lejanas se omiten.

	Todo es visual: nada de lo que pase aquí cambia el juego.
]]

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Naves.Config)
local EfectosNave = require(Shared.Naves.Datos.EfectosNave)
local Calidad = require(script.Parent.Parent.VFX.Calidad)
local Gestor = require(script.Parent.Parent.VFX.Gestor)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)
local Vuelo = require(script.Parent.Vuelo)

local Efectos = {}

-- Más lejos que esto, el efecto de una nave se omite (salvo las explosiones, que se ven desde lejos).
local DISTANCIA_PROPULSORES = 450
local DISTANCIA_EFECTOS = 900
local DISTANCIA_EXPLOSION = 1400

-- Segundos entre pulsos de los propulsores (los pulsos duran 0,3 s, así que se solapan y no hay huecos).
local INTERVALO_PULSO = 0.2
local INTERVALO_PULSO_BAJO = 0.35
-- Velocidad a partir de la cual una nave ajena se considera "propulsada".
local VELOCIDAD_MINIMA_PROPULSION = 6

local navePropia: Model? = nil
local alChocarPropia: ((normal: Vector3) -> ())? = nil
local conectadas: { [Model]: boolean } = setmetatable({}, { __mode = "k" }) :: any

-- ===== Utilidades =====

local function esModelo(valor: any): boolean
	return typeof(valor) == "Instance" and (valor :: Instance):IsA("Model")
end

local function esVector(valor: any): boolean
	return typeof(valor) == "Vector3"
end

local function recetaDeLaser(bando: any): string
	if bando == "Humanos" then
		return "Nave_Laser_Humanos"
	elseif bando == "Monstruos" then
		return "Nave_Laser_Monstruos"
	end
	return "Nave_Laser_Neutral"
end

-- ¿Está `punto` encima de la nave del piloto local? (para saber si es a él a quien le pasa)
local function esMiNave(punto: Vector3, radio: number): boolean
	local propia = navePropia
	return propia ~= nil and propia.PrimaryPart ~= nil and (propia.PrimaryPart.Position - punto).Magnitude <= radio
end

local function distanciaACamara(punto: Vector3): number
	local camara = workspace.CurrentCamera
	return if camara then (camara.CFrame.Position - punto).Magnitude else 0
end

-- ===== Avisos del servidor =====

local function alDisparar(modelo: any, origen: any, punto: any, direccion: any, viaje: any, bando: any)
	if not esModelo(modelo) or not esVector(origen) or not esVector(punto) or not esVector(direccion) then
		return
	end
	if type(viaje) ~= "number" or viaje ~= viaje then
		return
	end
	Gestor.Reproducir(recetaDeLaser(bando), "Lanzamiento", {
		Lanzador = modelo,
		Raiz = (modelo :: Model).PrimaryPart,
		Origen = origen,
		Punto = punto,
		Direccion = direccion,
		Viaje = math.clamp(viaje, 0.02, 3),
		EsLocal = modelo == navePropia,
		DistanciaMaxima = DISTANCIA_EFECTOS,
	})
end

local function alImpactar(_modelo: any, punto: any, direccion: any, tipo: any)
	if not esVector(punto) or not esVector(direccion) or type(tipo) ~= "string" then
		return
	end
	local receta = if tipo == "Escudo"
		then "Nave_Impacto_Escudo"
		elseif tipo == "Asteroide" then "Nave_Impacto_Asteroide"
		else "Nave_Impacto_Casco" -- "Casco" y "Estructura"
	local golpeaAMi = (tipo == "Escudo" or tipo == "Casco") and esMiNave(punto, 14)
	Gestor.Reproducir(receta, { "Impacto", "Residuo" }, {
		Origen = punto,
		Punto = punto,
		Direccion = direccion,
		LocalGolpeado = golpeaAMi,
		DistanciaMaxima = DISTANCIA_EFECTOS,
	})
end

local function alChocar(modelo: any, punto: any, normal: any, escudo: any, intensidad: any)
	if not esModelo(modelo) or not esVector(punto) or not esVector(normal) or type(intensidad) ~= "number" then
		return
	end
	local propia = modelo == navePropia
	-- Si es la nave del piloto local, el vuelo comprueba que haya rebotado.
	if propia and alChocarPropia then
		alChocarPropia(normal :: Vector3)
	end
	if intensidad < 0.04 then
		return -- un roce sin daño: solo el rebote
	end
	Gestor.Reproducir(if escudo == true then "Nave_Choque_Escudo" else "Nave_Choque_Casco", { "Impacto", "Residuo" }, {
		Origen = punto,
		Punto = punto,
		Direccion = normal,
		EsLocal = propia,
		LocalGolpeado = propia,
		DistanciaMaxima = DISTANCIA_EFECTOS,
	})
end

local function alDestruirseNave(posicion: any, _bando: any)
	if not esVector(posicion) then
		return
	end
	-- La nave del piloto local ya no existe cuando llega el aviso, pero estaba aquí mismo.
	local mia = esMiNave(posicion, 40) or distanciaACamara(posicion) < 45
	Gestor.Reproducir("Nave_Explosion", { "Impacto", "Residuo" }, {
		Origen = posicion,
		Punto = posicion,
		Direccion = Vector3.new(0, 0, -1),
		EsLocal = mia,
		LocalGolpeado = mia,
		DistanciaMaxima = DISTANCIA_EXPLOSION,
	})
end

local function alDestruirseAsteroide(posicion: any, tamano: any)
	if not esVector(posicion) or type(tamano) ~= "number" then
		return
	end
	local receta = if tamano < 10
		then "Nave_Asteroide_Pequeno"
		elseif tamano < 20 then "Nave_Asteroide_Mediano"
		else "Nave_Asteroide_Grande"
	Gestor.Reproducir(receta, { "Impacto", "Residuo" }, {
		Origen = posicion,
		Punto = posicion,
		Direccion = Vector3.new(0, 0, -1),
		DistanciaMaxima = DISTANCIA_EXPLOSION,
	})
end

local function alDespegar(_modelo: any, posicion: any, direccion: any)
	if not esVector(posicion) or not esVector(direccion) then
		return
	end
	Gestor.Reproducir("Nave_Despegue", "Lanzamiento", {
		Origen = posicion,
		Punto = posicion,
		Direccion = direccion,
		DistanciaMaxima = DISTANCIA_EFECTOS,
	})
end

-- ===== Propulsores =====

-- Destello cuando una nave enciende el turbo (el servidor cambia su atributo "Turbo").
local function vigilarTurbo(modelo: Model)
	if conectadas[modelo] then
		return
	end
	conectadas[modelo] = true
	modelo:GetAttributeChangedSignal("Turbo"):Connect(function()
		local raiz = modelo.PrimaryPart
		if raiz and modelo:GetAttribute("Turbo") == true then
			Gestor.Reproducir("Nave_Turbo_Arranque", "Lanzamiento", {
				Lanzador = modelo,
				Raiz = raiz,
				Origen = raiz.Position,
				Punto = raiz.Position,
				Direccion = raiz.CFrame.LookVector,
				EsLocal = modelo == navePropia,
				DistanciaMaxima = DISTANCIA_PROPULSORES,
			})
		end
	end)
end

local function pulsoPropulsores()
	for _, instancia in CollectionService:GetTagged(Config.EtiquetaNave) do
		if not instancia:IsA("Model") then
			continue
		end
		local modelo = instancia
		local raiz = modelo.PrimaryPart
		if raiz == nil then
			continue
		end
		vigilarTurbo(modelo)

		local propia = modelo == navePropia
		local propulsada = raiz.AssemblyLinearVelocity.Magnitude > VELOCIDAD_MINIMA_PROPULSION
			or (propia and Vuelo.Acelerando())
		if not propulsada or distanciaACamara(raiz.Position) > DISTANCIA_PROPULSORES then
			continue
		end
		local turbo = modelo:GetAttribute("Turbo") == true
		Gestor.Reproducir(if turbo then "Nave_Propulsor_Turbo" else "Nave_Propulsor", "Lanzamiento", {
			Lanzador = modelo,
			Raiz = raiz,
			Origen = raiz.Position,
			Punto = raiz.Position,
			Direccion = raiz.CFrame.LookVector,
			EsLocal = propia,
			DistanciaMaxima = DISTANCIA_PROPULSORES,
		})
	end
end

-- ===== API =====

-- Indica cuál es la nave del piloto local (nil al aterrizar). Se usa para los efectos de pantalla.
function Efectos.PonerNavePropia(modelo: Model?)
	navePropia = modelo
end

--[[
	Registra las recetas, escucha al servidor y arranca los propulsores. `alChocar` se llama cuando el servidor
	avisa de un choque de la nave propia (con la normal de la roca).
]]
function Efectos.Iniciar(alChocarNavePropia: (normal: Vector3) -> ())
	alChocarPropia = alChocarNavePropia
	Gestor.RegistrarRecetas(EfectosNave)

	ServicioRed.Conectar("NaveDisparo", alDisparar)
	ServicioRed.Conectar("NaveImpacto", alImpactar)
	ServicioRed.Conectar("NaveChoque", alChocar)
	ServicioRed.Conectar("NaveDestruida", alDestruirseNave)
	ServicioRed.Conectar("AsteroideDestruido", alDestruirseAsteroide)
	ServicioRed.Conectar("NaveDespegue", alDespegar)

	task.spawn(function()
		while true do
			pcall(pulsoPropulsores)
			task.wait(if Calidad.Nivel() == "Bajo" then INTERVALO_PULSO_BAJO else INTERVALO_PULSO)
		end
	end)
end

return Efectos
