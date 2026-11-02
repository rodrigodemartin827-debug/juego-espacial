--!strict
--[[
	Animador: reproduce las animaciones del combate en cualquier personaje (R15).

	Para cada nombre de animación decide qué usar:
	  1. Si Datos/Recursos.Animaciones[nombre] tiene un ID, usa ese asset (animación hecha en el editor).
	  2. Si está vacío, construye una KeyframeSequence a partir de Datos/Animaciones (provisional, por código),
	     la registra con KeyframeSequenceProvider y la usa como si fuera un asset.

	Así se puede sustituir cualquier animación cambiando SOLO el ID en el módulo de datos.

	Nota: las animaciones registradas por código solo existen en el cliente que las registró, por eso cada
	cliente reproduce las de TODOS los luchadores por su cuenta (al recibir el aviso del servidor), en vez de
	fiarse de que se repliquen. Con un ID de asset real también funciona, y verlas dos veces es inofensivo.
]]

local KeyframeSequenceProvider = game:GetService("KeyframeSequenceProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Datos = ReplicatedStorage:WaitForChild("Shared").Combate.Datos
local Animaciones = require(Datos.Animaciones)
local Recursos = require(Datos.Recursos)

local Animador = {}

local ESTILOS: { [string]: Enum.PoseEasingStyle } = {
	Linear = Enum.PoseEasingStyle.Linear,
	Constant = Enum.PoseEasingStyle.Constant,
	Elastic = Enum.PoseEasingStyle.Elastic,
	Cubic = Enum.PoseEasingStyle.Cubic,
	Bounce = Enum.PoseEasingStyle.Bounce,
}

local PRIORIDADES: { [string]: Enum.AnimationPriority } = {
	Core = Enum.AnimationPriority.Core,
	Idle = Enum.AnimationPriority.Idle,
	Movement = Enum.AnimationPriority.Movement,
	Action = Enum.AnimationPriority.Action,
}

local idsRegistrados: { [string]: string } = {} -- nombre -> ID de contenido (por código)
local pistas: { [Animator]: { [string]: AnimationTrack } } = setmetatable({}, { __mode = "k" }) :: any
local avisados: { [string]: boolean } = {}

local function avisarUnaVez(clave: string, mensaje: string)
	if not avisados[clave] then
		avisados[clave] = true
		warn(`[Animador] {mensaje}`)
	end
end

-- Construye la KeyframeSequence de una animación definida por código.
local function construir(nombre: string, definicion: any): KeyframeSequence
	local secuencia = Instance.new("KeyframeSequence")
	secuencia.Name = nombre
	secuencia.Loop = definicion.Bucle == true
	secuencia.Priority = PRIORIDADES[definicion.Prioridad or "Action"] or Enum.AnimationPriority.Action

	-- Valor acumulado de cada parte: un cuadro que no nombra una parte mantiene el anterior.
	local actual: { [string]: { number } } = {}

	for _, cuadro in definicion.Cuadros do
		for parte, rotacion in cuadro.Poses do
			actual[parte] = rotacion
		end
		local estilo = ESTILOS[cuadro.Easing or "Linear"] or Enum.PoseEasingStyle.Linear

		local function crearPose(nodo: any): Pose
			local pose = Instance.new("Pose")
			pose.Name = nodo.Nombre
			local rotacion = actual[nodo.Nombre]
			if rotacion then
				pose.CFrame = CFrame.Angles(math.rad(rotacion[1]), math.rad(rotacion[2]), math.rad(rotacion[3]))
				pose.Weight = 1
			else
				pose.Weight = 0
			end
			pose.EasingStyle = estilo
			pose.EasingDirection = Enum.PoseEasingDirection.Out
			for _, hijo in nodo.Hijos do
				crearPose(hijo).Parent = pose
			end
			return pose
		end

		local fotograma = Instance.new("Keyframe")
		fotograma.Time = cuadro.T
		crearPose(Animaciones.Rig).Parent = fotograma
		fotograma.Parent = secuencia
	end
	return secuencia
end

-- ID de contenido de la animación `nombre` (de Recursos, o registrando la de código), o nil si no existe.
local function resolverId(nombre: string): string?
	local externo = Recursos.Animaciones[nombre]
	if externo ~= nil and externo ~= "" then
		return externo
	end

	local guardado = idsRegistrados[nombre]
	if guardado then
		return guardado
	end
	local definicion = Animaciones.Definiciones[nombre]
	if definicion == nil then
		avisarUnaVez(nombre, `La animación '{nombre}' no existe en Datos/Animaciones ni tiene ID en Datos/Recursos`)
		return nil
	end
	local ok, resultado = pcall(function()
		return KeyframeSequenceProvider:RegisterKeyframeSequence(construir(nombre, definicion))
	end)
	if not ok then
		avisarUnaVez(nombre, `No se pudo registrar la animación '{nombre}': {resultado}`)
		return nil
	end
	idsRegistrados[nombre] = resultado
	return resultado
end

local function animadorDe(modelo: Model): Animator?
	local humanoid = modelo:FindFirstChildOfClass("Humanoid")
	if humanoid == nil then
		return nil
	end
	if humanoid.RigType ~= Enum.HumanoidRigType.R15 then
		avisarUnaVez("R6", "Las animaciones del combate están hechas para R15: este personaje las ignora")
		return nil
	end
	local animador = humanoid:FindFirstChildOfClass("Animator")
	if animador == nil then
		local nuevo = Instance.new("Animator")
		nuevo.Parent = humanoid
		animador = nuevo
	end
	return animador
end

--[[
	Reproduce la animación `nombre` en el personaje. Devuelve la pista (para poder pararla) o nil si no se
	pudo. `velocidad` multiplica la rapidez (1 = normal).
]]
function Animador.Reproducir(modelo: Model, nombre: string, velocidad: number?): AnimationTrack?
	local animador = animadorDe(modelo)
	if animador == nil then
		return nil
	end

	local delPersonaje = pistas[animador]
	if delPersonaje == nil then
		delPersonaje = {}
		pistas[animador] = delPersonaje
	end

	local pista = delPersonaje[nombre]
	if pista == nil then
		local id = resolverId(nombre)
		if id == nil then
			return nil
		end
		local animacion = Instance.new("Animation")
		animacion.AnimationId = id
		local ok, cargada = pcall(function()
			return animador:LoadAnimation(animacion)
		end)
		if not ok then
			avisarUnaVez(nombre, `No se pudo cargar la animación '{nombre}': {cargada}`)
			return nil
		end
		pista = cargada
		pista.Priority = Enum.AnimationPriority.Action
		delPersonaje[nombre] = pista
	end

	pista:Play(0.05, 1, velocidad or 1)
	return pista
end

-- Para una animación en marcha (con un pequeño fundido).
function Animador.Detener(modelo: Model, nombre: string)
	local humanoid = modelo:FindFirstChildOfClass("Humanoid")
	local animador = humanoid and humanoid:FindFirstChildOfClass("Animator")
	local pista = animador and pistas[animador] and pistas[animador][nombre]
	if pista then
		pista:Stop(0.1)
	end
end

return Animador
