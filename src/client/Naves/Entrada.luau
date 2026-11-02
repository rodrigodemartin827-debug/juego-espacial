--!strict
--[[
	Entrada (Naves): junta en una sola lectura todo lo que el piloto puede usar para volar.

	  Ordenador   W/S acelerar y frenar · A/D desplazarse de lado · Espacio subir · Ctrl o C bajar ·
	              Shift turbo · ratón: orientar (se bloquea al centro de la pantalla) · clic: disparar · F: aterrizar
	  Mando       palanca izquierda: mover · palanca derecha: orientar · R2/RT: disparar · L2/LT: turbo ·
	              A subir · B bajar · Y aterrizar
	  Móvil       joystick, arrastrar para apuntar y botones (ver Mandos)

	`Leer` devuelve la intención del piloto en este fotograma, sin tocar la nave.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Config = require(ReplicatedStorage:WaitForChild("Shared").Naves.Config)
local Fisica = require(ReplicatedStorage.Shared.Naves.Fisica)
local Calidad = require(script.Parent.Parent.VFX.Calidad)
local Mandos = require(script.Parent.Mandos)

export type Lectura = Mandos.Lectura

local Entrada = {}

local ZONA_MUERTA = 0.15
local MANDO = Enum.UserInputType.Gamepad1

local teclas: { [Enum.KeyCode]: boolean } = {}
local ratonDisparando = false
local conexiones: { RBXScriptConnection } = {}
local activa = false
local comportamientoRaton: Enum.MouseBehavior? = nil
local iconoRaton = true

local function pulsada(...: Enum.KeyCode): boolean
	for _, tecla in { ... } do
		if teclas[tecla] then
			return true
		end
	end
	return false
end

local function eje(positiva: boolean, negativa: boolean): number
	return (if positiva then 1 else 0) - (if negativa then 1 else 0)
end

-- Estado actual de los botones y palancas del mando, por tecla (vacío si no hay mando conectado).
local function estadoMando(): { [Enum.KeyCode]: InputObject? }
	local estados: { [Enum.KeyCode]: InputObject? } = {}
	if UserInputService.GamepadEnabled then
		for _, estado in UserInputService:GetGamepadState(MANDO) do
			estados[estado.KeyCode] = estado
		end
	end
	return estados
end

--[[
	Empieza a escuchar. `alAterrizar` se llama cuando el piloto pide aterrizar (F, Y del mando o el botón táctil).
]]
function Entrada.Activar(alAterrizar: () -> ())
	if activa then
		return
	end
	activa = true
	teclas = {}
	ratonDisparando = false

	table.insert(
		conexiones,
		UserInputService.InputBegan:Connect(function(entrada: InputObject, procesado: boolean)
			if procesado then
				return -- escribiendo en el chat o pulsando un botón de la interfaz
			end
			if entrada.UserInputType == Enum.UserInputType.Keyboard then
				teclas[entrada.KeyCode] = true
				if entrada.KeyCode == Enum.KeyCode.F then
					alAterrizar()
				end
			elseif entrada.UserInputType == Enum.UserInputType.MouseButton1 then
				ratonDisparando = true
			elseif entrada.KeyCode == Enum.KeyCode.ButtonY then
				alAterrizar()
			end
		end)
	)
	table.insert(
		conexiones,
		UserInputService.InputEnded:Connect(function(entrada: InputObject)
			if entrada.UserInputType == Enum.UserInputType.Keyboard then
				teclas[entrada.KeyCode] = nil
			elseif entrada.UserInputType == Enum.UserInputType.MouseButton1 then
				ratonDisparando = false
			end
		end)
	)

	if Calidad.EsMovil then
		Mandos.Mostrar(true, alAterrizar)
	else
		-- Ratón bloqueado en el centro: así siempre hay movimiento que leer y el cursor no se sale de la ventana.
		comportamientoRaton = UserInputService.MouseBehavior
		iconoRaton = UserInputService.MouseIconEnabled
		UserInputService.MouseBehavior = Enum.MouseBehavior.LockCenter
		UserInputService.MouseIconEnabled = false
	end
end

-- Deja de escuchar y devuelve el ratón a como estaba.
function Entrada.Desactivar()
	if not activa then
		return
	end
	activa = false
	for _, conexion in conexiones do
		conexion:Disconnect()
	end
	table.clear(conexiones)
	teclas = {}
	ratonDisparando = false
	Mandos.Mostrar(false)
	if comportamientoRaton then
		UserInputService.MouseBehavior = comportamientoRaton
		UserInputService.MouseIconEnabled = iconoRaton
		comportamientoRaton = nil
	end
end

-- Qué quiere hacer el piloto en este fotograma. `dt` convierte las palancas del mando en giro.
function Entrada.Leer(dt: number): Lectura
	local lectura: Lectura = {
		Adelante = eje(pulsada(Enum.KeyCode.W, Enum.KeyCode.Up), pulsada(Enum.KeyCode.S, Enum.KeyCode.Down)),
		Lateral = eje(pulsada(Enum.KeyCode.D, Enum.KeyCode.Right), pulsada(Enum.KeyCode.A, Enum.KeyCode.Left)),
		Vertical = eje(pulsada(Enum.KeyCode.Space), pulsada(Enum.KeyCode.LeftControl, Enum.KeyCode.C)),
		Turbo = pulsada(Enum.KeyCode.LeftShift, Enum.KeyCode.RightShift),
		Disparar = ratonDisparando,
		DGuinada = 0,
		DCabeceo = 0,
	}

	if not Calidad.EsMovil then
		local delta = UserInputService:GetMouseDelta()
		lectura.DGuinada = -delta.X * Config.SensibilidadRaton
		lectura.DCabeceo = -delta.Y * Config.SensibilidadRaton
	end

	-- Mando.
	local mando = estadoMando()
	local izquierda = mando[Enum.KeyCode.Thumbstick1]
	local derecha = mando[Enum.KeyCode.Thumbstick2]
	if izquierda then
		lectura.Lateral += Fisica.ZonaMuerta(izquierda.Position.X, ZONA_MUERTA)
		lectura.Adelante += Fisica.ZonaMuerta(izquierda.Position.Y, ZONA_MUERTA)
	end
	if derecha then
		lectura.DGuinada -= Fisica.ZonaMuerta(derecha.Position.X, ZONA_MUERTA) * Config.GiroMaximo * dt
		lectura.DCabeceo += Fisica.ZonaMuerta(derecha.Position.Y, ZONA_MUERTA) * Config.GiroMaximo * dt
	end
	local gatilloDerecho, gatilloIzquierdo = mando[Enum.KeyCode.ButtonR2], mando[Enum.KeyCode.ButtonL2]
	if gatilloDerecho and gatilloDerecho.Position.Z > 0.4 then
		lectura.Disparar = true
	end
	if gatilloIzquierdo and gatilloIzquierdo.Position.Z > 0.4 then
		lectura.Turbo = true
	end
	local botonA, botonB = mando[Enum.KeyCode.ButtonA], mando[Enum.KeyCode.ButtonB]
	local sube = if botonA then botonA.Position.Z > 0.5 else false
	local baja = if botonB then botonB.Position.Z > 0.5 else false
	lectura.Vertical += eje(sube, baja)

	-- Táctil.
	if Calidad.EsMovil then
		local tactil = Mandos.Leer()
		lectura.Adelante += tactil.Adelante
		lectura.Lateral += tactil.Lateral
		lectura.Vertical += tactil.Vertical
		lectura.Turbo = lectura.Turbo or tactil.Turbo
		lectura.Disparar = lectura.Disparar or tactil.Disparar
		lectura.DGuinada += tactil.DGuinada
		lectura.DCabeceo += tactil.DCabeceo
	end

	lectura.Adelante = math.clamp(lectura.Adelante, -1, 1)
	lectura.Lateral = math.clamp(lectura.Lateral, -1, 1)
	lectura.Vertical = math.clamp(lectura.Vertical, -1, 1)
	return lectura
end

return Entrada
