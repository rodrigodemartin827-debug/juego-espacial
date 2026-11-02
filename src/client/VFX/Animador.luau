--!strict
--[[
	Animador: reproduce las animaciones del juego (combate y andar de monstruo) en cualquier personaje R6.

	Para cada nombre de animación decide qué usar:
	  1. Si Combate/Datos/Recursos.Animaciones[nombre] tiene un ID, usa ese asset (animación hecha en el editor).
	  2. Si está vacío, construye una KeyframeSequence a partir de la definición por código (Animacion/Catalogo:
	     las de Combate/Datos/Animaciones y las de Personajes/Datos/AnimacionesMonstruo), la registra con
	     KeyframeSequenceProvider y la usa como si fuera un asset.

	Así se puede sustituir cualquier animación cambiando SOLO el ID en el módulo de datos.

	Nota: las animaciones registradas por código solo existen en el cliente que las registró, por eso cada
	cliente reproduce las de TODOS los personajes por su cuenta (los golpes al recibir el aviso del servidor, el
	andar de monstruo en Personajes/AndarMonstruo), en vez de fiarse de que se repliquen. Precargar() registra
	todas al arrancar y siempre en el mismo orden, para que un mismo ID temporal signifique la misma animación en
	todos los clientes.
]]

local KeyframeSequenceProvider = game:GetService("KeyframeSequenceProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Animaciones = require(Shared.Combate.Datos.Animaciones)
local Catalogo = require(Shared.Animacion.Catalogo)
local Recursos = require(Shared.Combate.Datos.Recursos)

local Animador = {}

local ESTILOS: { [string]: Enum.PoseEasingStyle } = {
	Linear = Enum.PoseEasingStyle.Linear,
	Constant = Enum.PoseEasingStyle.Constant,
	Elastic = Enum.PoseEasingStyle.Elastic,
	Cubic = Enum.PoseEasingStyle.Cubic,
	Bounce = Enum.PoseEasingStyle.Bounce,
}

local DIRECCIONES: { [string]: Enum.PoseEasingDirection } = {
	In = Enum.PoseEasingDirection.In,
	Out = Enum.PoseEasingDirection.Out,
	InOut = Enum.PoseEasingDirection.InOut,
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
		local direccion = DIRECCIONES[cuadro.Direccion or "Out"] or Enum.PoseEasingDirection.Out

		local function crearPose(nodo: any): Pose
			local pose = Instance.new("Pose")
			pose.Name = nodo.Nombre
			local rotacion = actual[nodo.Nombre]
			if rotacion and nodo.Eje then
				-- Del sistema del personaje (cabeceo, giro, ladeo) al Transform del Motor6D de esa parte.
				local m, t = Animaciones.Articulacion(nodo, rotacion)
				pose.CFrame = CFrame.new(t[1], t[2], t[3], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9])
				pose.Weight = 1
			else
				pose.Weight = 0
			end
			pose.EasingStyle = estilo
			pose.EasingDirection = direccion
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
	local definicion = Catalogo.Definicion(nombre)
	if definicion == nil then
		avisarUnaVez(nombre, `La animación '{nombre}' no existe en Animacion/Catalogo ni tiene ID en Datos/Recursos`)
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
	if humanoid.RigType ~= Enum.HumanoidRigType.R6 then
		avisarUnaVez("RigNoR6", "Las animaciones del combate están hechas para R6: este personaje las ignora")
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

-- Prioridad con la que se carga la animación `nombre` (la de su definición; Action si no dice nada).
local function prioridadDe(nombre: string): Enum.AnimationPriority
	local definicion = Catalogo.Definicion(nombre)
	local prioridad = definicion and definicion.Prioridad
	return PRIORIDADES[prioridad or "Action"] or Enum.AnimationPriority.Action
end

-- ID de contenido que se usa para la animación `nombre` (el de Recursos o el registrado), o nil si no existe.
function Animador.Id(nombre: string): string?
	return resolverId(nombre)
end

--[[
	Registra ya todas las animaciones hechas por código, en orden alfabético. Se llama una vez al arrancar el
	cliente: evita el tirón de construirlas en mitad de una pelea y hace que los IDs temporales coincidan entre
	clientes (todos registran lo mismo en el mismo orden).
]]
function Animador.Precargar()
	for _, nombre in Catalogo.Nombres() do
		resolverId(nombre)
	end
end

--[[
	Pista de la animación `nombre` en el personaje, cargada una sola vez por Animator (no la reproduce). Lleva la
	prioridad de su definición. Devuelve nil si el personaje no es R6 o la animación no se puede cargar.
]]
function Animador.Cargar(modelo: Model, nombre: string): AnimationTrack?
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
	if not pista then
		local id = resolverId(nombre)
		if id == nil then
			return nil
		end
		local animacion = Instance.new("Animation")
		animacion.Name = nombre
		animacion.AnimationId = id
		local ok, cargada = pcall(function()
			return animador:LoadAnimation(animacion)
		end)
		if not ok then
			avisarUnaVez(nombre, `No se pudo cargar la animación '{nombre}': {cargada}`)
			return nil
		end
		local nueva: AnimationTrack = cargada
		nueva.Priority = prioridadDe(nombre)
		delPersonaje[nombre] = nueva
		return nueva
	end
	return pista
end

-- ¿Es `pista` una de las que ha cargado este cliente con Animador en ese personaje?
function Animador.EsPropia(modelo: Model, pista: AnimationTrack): boolean
	local humanoid = modelo:FindFirstChildOfClass("Humanoid")
	local animador = humanoid and humanoid:FindFirstChildOfClass("Animator")
	local delPersonaje = animador and pistas[animador]
	if delPersonaje == nil then
		return false
	end
	for _, propia in delPersonaje do
		if rawequal(propia, pista) then
			return true
		end
	end
	return false
end

--[[
	Reproduce la animación `nombre` en el personaje. Devuelve la pista (para poder pararla) o nil si no se
	pudo. `velocidad` multiplica la rapidez (1 = normal).
]]
function Animador.Reproducir(modelo: Model, nombre: string, velocidad: number?): AnimationTrack?
	local pista = Animador.Cargar(modelo, nombre)
	if pista == nil then
		return nil
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
