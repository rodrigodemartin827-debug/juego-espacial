--!strict
--[[
	Camara (Naves): cámara de persecución para pilotar.

	Va detrás y un poco por encima de la nave, siguiéndola con suavidad (así se nota la inercia y los giros), se
	aleja y abre el campo de visión con la velocidad, y se abre aún más con el turbo para dar sensación de
	velocidad. Mira un punto por delante de la nave, no a la nave, de modo que la mira queda a la vista.

	Se ejecuta con la prioridad de cámara de Roblox: los efectos de pantalla del combate (Vfx/Pantalla: sacudidas,
	zoom...) corren justo DESPUÉS y se aplican encima, así que las explosiones sacuden esta cámara igual que
	sacuden la de a pie.
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local Calidad = require(script.Parent.Parent.VFX.Calidad)

local Camara = {}

local NOMBRE_PASO = "NaveCamara"

local DISTANCIA_BASE = 21
local DISTANCIA_MAXIMA = 30
local ALTURA = 5.5
local FOV_BASE = 70
local FOV_MAXIMO_EXTRA = 12
local FOV_TURBO_EXTRA = 8
local SUAVIDAD_POSICION = 9
local SUAVIDAD_ORIENTACION = 7

local raiz: BasePart? = nil
local velocidadMaxima = 100
local turbo = false
local marco: CFrame? = nil -- la cámara suavizada
local fovAnterior = FOV_BASE
local tipoAnterior: Enum.CameraType = Enum.CameraType.Custom

local function paso(dt: number)
	local camara = workspace.CurrentCamera
	local nave = raiz
	if camara == nil or nave == nil or nave.Parent == nil then
		return
	end

	local movil = Calidad.EsMovil
	local velocidad = nave.AssemblyLinearVelocity.Magnitude
	local rapidez = math.clamp(velocidad / math.max(velocidadMaxima, 1), 0, 1.6)

	-- Orientación deseada: la de la nave sin el alabeo (la cámara no debe rodar con ella).
	local rx, ry = nave.CFrame:ToOrientation()
	local orientacion = CFrame.fromEulerAnglesYXZ(rx, ry, 0)
	local distancia = (DISTANCIA_BASE + (DISTANCIA_MAXIMA - DISTANCIA_BASE) * math.min(rapidez, 1))
		* (if movil then 1.15 else 1)

	local deseada = CFrame.new(nave.Position) * orientacion * CFrame.new(0, ALTURA, distancia)
	local mirada = nave.Position + orientacion.LookVector * 40 + orientacion.UpVector * 2
	local objetivo = CFrame.lookAt(deseada.Position, mirada)

	if marco == nil then
		marco = objetivo
	else
		-- Aproximación exponencial: igual de suave a 30 que a 144 fotogramas por segundo.
		local alfaPosicion = 1 - math.exp(-SUAVIDAD_POSICION * dt)
		local alfaOrientacion = 1 - math.exp(-SUAVIDAD_ORIENTACION * dt)
		local posicion = marco.Position:Lerp(objetivo.Position, alfaPosicion)
		local rotacion = (marco - marco.Position):Lerp(objetivo - objetivo.Position, alfaOrientacion)
		marco = CFrame.new(posicion) * rotacion
	end
	camara.CFrame = marco :: CFrame

	local fovDeseado = FOV_BASE + FOV_MAXIMO_EXTRA * math.min(rapidez, 1) + (if turbo then FOV_TURBO_EXTRA else 0)
	camara.FieldOfView += (fovDeseado - camara.FieldOfView) * (1 - math.exp(-4 * dt))
end

--[[
	Empieza a seguir la nave. `velocidadMax` es la de la nave sin turbo (el campo de visión crece hasta ahí).
]]
function Camara.Iniciar(parteNave: BasePart, velocidadMax: number)
	raiz = parteNave
	velocidadMaxima = velocidadMax
	marco = nil
	local camara = workspace.CurrentCamera
	if camara then
		tipoAnterior = camara.CameraType
		fovAnterior = camara.FieldOfView
		camara.CameraType = Enum.CameraType.Scriptable
	end
	RunService:UnbindFromRenderStep(NOMBRE_PASO)
	RunService:BindToRenderStep(NOMBRE_PASO, Enum.RenderPriority.Camera.Value, paso)
end

function Camara.PonerTurbo(activo: boolean)
	turbo = activo
end

function Camara.ActualizarVelocidadMaxima(velocidadMax: number)
	velocidadMaxima = velocidadMax
end

-- Devuelve la cámara al personaje.
function Camara.Detener()
	RunService:UnbindFromRenderStep(NOMBRE_PASO)
	raiz = nil
	marco = nil
	turbo = false
	local camara = workspace.CurrentCamera
	if camara then
		camara.CameraType = if tipoAnterior == Enum.CameraType.Scriptable then Enum.CameraType.Custom else tipoAnterior
		camara.FieldOfView = fovAnterior
		local personaje = Players.LocalPlayer.Character
		local humanoid = personaje and personaje:FindFirstChildOfClass("Humanoid")
		if humanoid then
			camara.CameraSubject = humanoid
		end
	end
end

return Camara
