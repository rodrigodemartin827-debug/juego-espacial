--!strict
--[[
	Vuelo (Naves): el piloto manda la nave desde su propio cliente.

	La física de una nave que lleva a un jugador la simula SU cliente (el servidor le cede la propiedad de red),
	así que el control responde al instante, sin esperar al servidor. Cada fotograma este módulo:

	  1. lee la intención del piloto (Entrada),
	  2. gira la orientación (guiñada y cabeceo) y calcula la velocidad que piden los mandos (Naves/Fisica),
	  3. acerca la velocidad real a esa con la aceleración de SU motor (inercia),
	  4. suma el arrastre del agujero negro (Planetas/Gravedad: una corriente hacia su centro que crece al
	     acercarse; si el motor no da más que ella, no se escapa) y no deja meterse dentro de un planeta o del sol,
	  5. predice choques con los asteroides y rebota al momento, sin esperar el aviso del servidor,
	  6. y lo escribe en las dos fuerzas del modelo: LinearVelocity (velocidad) y AlignOrientation (orientación).

	Todos los límites (velocidad máxima, aceleración, turbo, cadencia...) vienen de las estadísticas que el
	servidor calculó a partir de las mejoras guardadas del jugador. Si un tramposo se los salta, el servidor lo
	detecta (ServicioNaves.vigilar) y lo devuelve a su sitio: este cliente no es la autoridad, solo el piloto.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Naves.Config)
local Fisica = require(Shared.Naves.Fisica)
local DatosPlanetas = require(Shared.Planetas.Datos)
local Espacio = require(Shared.Planetas.Espacio)
local Gravedad = require(Shared.Planetas.Gravedad)
local Camara = require(script.Parent.Camara)
local Entrada = require(script.Parent.Entrada)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)

type Sesion = {
	Modelo: Model,
	Raiz: BasePart,
	Fuerza: LinearVelocity,
	Giro: AlignOrientation,
	Datos: any, -- último EstadoNave (límites del motor, armas...)
	Guinada: number,
	Cabeceo: number,
	Alabeo: number,
	Vx: number,
	Vy: number,
	Vz: number,
	TurboActivo: boolean,
	TurboEnergia: number,
	TurboBloqueado: boolean, -- se agotó con la tecla pulsada: hay que soltarla antes de volver a encenderlo
	TurboDesde: number,
	UltimoDisparo: number,
	UltimoRebote: number,
	Correccion: number,
	Acelerando: boolean,
}

local Vuelo = {}

local NOMBRE_PASO = "NaveVuelo"
local DT_MAXIMO = 0.1 -- un tirón de fotogramas no debe disparar la nave hacia delante

local sesion: Sesion? = nil

-- Cuerpos sólidos (planetas y sol) y agujero negro: no cambian, se leen una vez.
local SOLIDOS = Espacio.CuerposSolidos()
local AGUJERO = DatosPlanetas.AgujeroNegro

-- ===== Controles de Roblox =====

-- Los controles de a pie de Roblox (joystick en móvil, botón de salto...) sobran mientras se pilota.
local function controlesDeRoblox(activar: boolean)
	pcall(function()
		local modulo = require(
			Players.LocalPlayer:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule", 2) :: ModuleScript
		) :: any
		local controles = modulo:GetControls()
		if activar then
			controles:Enable()
		else
			controles:Disable()
		end
	end)
end

-- ===== Choques =====

local function parametrosAsteroides(): RaycastParams?
	local campos = workspace:FindFirstChild("CamposDeAsteroides")
	if campos == nil then
		return nil
	end
	local parametros = RaycastParams.new()
	parametros.FilterType = Enum.RaycastFilterType.Include
	parametros.FilterDescendantsInstances = { campos }
	return parametros
end

local function rebotar(s: Sesion, normal: Vector3)
	s.Vx, s.Vy, s.Vz = Fisica.Rebote(s.Vx, s.Vy, s.Vz, normal.X, normal.Y, normal.Z, Config.Elasticidad)
	s.UltimoRebote = os.clock()
end

-- ===== Turbo =====

local function encenderTurbo(s: Sesion)
	s.TurboActivo = true
	s.TurboDesde = os.clock()
	Camara.PonerTurbo(true)
	ServicioRed.Enviar("TurboNave", true)
end

local function apagarTurbo(s: Sesion, avisar: boolean)
	s.TurboActivo = false
	Camara.PonerTurbo(false)
	if avisar then
		ServicioRed.Enviar("TurboNave", false)
	end
end

-- Lleva el depósito de turbo (réplica del servidor, que manda) y decide si se enciende o se apaga.
local function gestionarTurbo(s: Sesion, pulsado: boolean, dt: number)
	if not pulsado then
		s.TurboBloqueado = false
	end
	if s.TurboActivo then
		s.TurboEnergia = math.max(0, s.TurboEnergia - Config.TurboConsumo * dt)
		if not pulsado then
			apagarTurbo(s, true)
		elseif s.TurboEnergia <= 0 then
			s.TurboBloqueado = true
			apagarTurbo(s, true)
		end
	else
		s.TurboEnergia = math.min(s.Datos.TurboMax, s.TurboEnergia + Config.TurboRegeneracion * dt)
		if pulsado and not s.TurboBloqueado and s.TurboEnergia >= Config.TurboMinimo then
			encenderTurbo(s)
		end
	end
end

-- ===== Disparo =====

local function disparar(s: Sesion, ahora: number)
	if ahora - s.UltimoDisparo < 1 / s.Datos.Cadencia then
		return
	end
	s.UltimoDisparo = ahora
	-- Se dispara hacia donde señala el centro de la pantalla (la mira), no solo recto desde la proa: los disparos
	-- convergen en el punto apuntado. El servidor limita la desviación a un cono delante de la nave.
	local camara = workspace.CurrentCamera
	local direccion = s.Raiz.CFrame.LookVector
	if camara then
		local punto = camara.CFrame.Position + camara.CFrame.LookVector * 400
		local hacia = punto - s.Raiz.Position
		if hacia.Magnitude > 1 then
			direccion = hacia.Unit
		end
	end
	ServicioRed.Enviar("DispararNave", direccion)
end

-- ===== Fotograma =====

local function paso(dt: number)
	local s = sesion
	if s == nil or s.Raiz.Parent == nil then
		return
	end
	dt = math.min(dt, DT_MAXIMO)
	if dt <= 0 then
		return
	end
	local ahora = os.clock()
	local datos = s.Datos
	local lectura = Entrada.Leer(dt)

	-- Orientación.
	s.Guinada, s.Cabeceo = Fisica.Girar(s.Guinada, s.Cabeceo, lectura.DGuinada, lectura.DCabeceo, dt)
	local giro = math.clamp(lectura.DGuinada / dt, -Config.GiroMaximo, Config.GiroMaximo)
	s.Alabeo = Fisica.Alabeo(s.Alabeo, giro, lectura.Lateral, dt)

	-- Velocidad que piden los mandos, en el sistema de la nave (sin alabeo) llevada al mundo.
	gestionarTurbo(s, lectura.Turbo, dt)
	local sinAlabeo = CFrame.fromEulerAnglesYXZ(s.Cabeceo, s.Guinada, 0)
	local lx, ly, lz = Fisica.VelocidadObjetivo({
		Adelante = lectura.Adelante,
		Lateral = lectura.Lateral,
		Vertical = lectura.Vertical,
		Turbo = s.TurboActivo,
	}, datos.VelocidadMax, datos.TurboMult)
	local objetivo = sinAlabeo:VectorToWorldSpace(Vector3.new(lx, ly, lz))

	-- Atracción del agujero negro: una corriente que se suma a lo que piden los mandos (el servidor la cuenta).
	local posicion = s.Raiz.Position
	local ax, ay, az = Gravedad.VectorArrastre(posicion :: any, AGUJERO.Centro, AGUJERO.Atraccion)
	if ax ~= 0 or ay ~= 0 or az ~= 0 then
		objetivo += Vector3.new(ax, ay, az)
	end

	-- Inercia: la velocidad real se acerca a la pedida con la aceleración del motor (el doble con turbo).
	local hayOrden = lectura.Adelante ~= 0 or lectura.Lateral ~= 0 or lectura.Vertical ~= 0 or s.TurboActivo
	s.Acelerando = hayOrden
	local aceleracion = Fisica.Aceleracion(datos.Aceleracion * (if s.TurboActivo then 2 else 1), hayOrden)
	s.Vx, s.Vy, s.Vz = Fisica.AcercarVelocidad(s.Vx, s.Vy, s.Vz, objetivo.X, objetivo.Y, objetivo.Z, aceleracion * dt)

	-- Planetas y sol son sólidos: la nave resbala por fuera en lugar de atravesarlos.
	for _, cuerpo in SOLIDOS do
		s.Vx, s.Vy, s.Vz = Gravedad.ContenerFuera(
			posicion.X,
			posicion.Y,
			posicion.Z,
			s.Vx,
			s.Vy,
			s.Vz,
			cuerpo.Centro,
			cuerpo.Radio + Config.RadioNave
		)
	end

	-- Choque previsto con un asteroide en este fotograma: rebota ya (el servidor aplica el daño).
	local avance = Vector3.new(s.Vx, s.Vy, s.Vz) * dt
	if avance.Magnitude > 0.01 then
		local parametros = parametrosAsteroides()
		if parametros then
			local golpe = workspace:Spherecast(s.Raiz.Position, Config.RadioNave, avance, parametros)
			if golpe then
				rebotar(s, golpe.Normal)
			end
		end
	end

	s.Fuerza.VectorVelocity = Vector3.new(s.Vx, s.Vy, s.Vz)
	s.Giro.CFrame = CFrame.fromEulerAnglesYXZ(s.Cabeceo, s.Guinada, s.Alabeo)

	if lectura.Disparar then
		disparar(s, ahora)
	end
end

-- ===== API =====

--[[
	Empieza a pilotar. `datos` es el EstadoNave del servidor (con el modelo de la nave y sus estadísticas).
	Devuelve false si la nave no está lista (falta alguna parte del modelo); se puede reintentar.
]]
function Vuelo.Iniciar(datos: any, alAterrizar: () -> ()): boolean
	if sesion then
		return true
	end
	local modelo: Model = datos.Modelo
	local raiz = modelo.PrimaryPart or modelo:WaitForChild("Fuselaje", 5)
	if raiz == nil or not raiz:IsA("BasePart") then
		return false
	end
	local fuerza = raiz:WaitForChild("Velocidad", 5)
	local giro = raiz:WaitForChild("Orientacion", 5)
	if fuerza == nil or giro == nil then
		return false
	end

	local rx, ry = raiz.CFrame:ToOrientation()
	sesion = {
		Modelo = modelo,
		Raiz = raiz,
		Fuerza = fuerza :: LinearVelocity,
		Giro = giro :: AlignOrientation,
		Datos = datos,
		Guinada = ry,
		Cabeceo = rx,
		Alabeo = 0,
		Vx = 0,
		Vy = 0,
		Vz = 0,
		TurboActivo = false,
		TurboEnergia = datos.Turbo,
		TurboBloqueado = false,
		TurboDesde = 0,
		UltimoDisparo = 0,
		UltimoRebote = 0,
		Correccion = datos.Correccion,
		Acelerando = false,
	}

	controlesDeRoblox(false)
	Entrada.Activar(alAterrizar)
	RunService:UnbindFromRenderStep(NOMBRE_PASO)
	RunService:BindToRenderStep(NOMBRE_PASO, Enum.RenderPriority.Input.Value + 1, paso)
	return true
end

-- Nueva foto del estado: límites del motor y armas al día, depósito de turbo resincronizado con el servidor.
function Vuelo.Actualizar(datos: any)
	local s = sesion
	if s == nil then
		return
	end
	s.Datos = datos
	s.TurboEnergia = datos.Turbo
	Camara.ActualizarVelocidadMaxima(datos.VelocidadMax)
	-- Si el servidor dice que el turbo ya no está activo (se agotó allí antes que aquí), se apaga sin avisar.
	if s.TurboActivo and not datos.TurboActivo and os.clock() - s.TurboDesde > 0.6 then
		apagarTurbo(s, false)
	end
	-- El servidor la ha devuelto a su sitio: se olvida de la velocidad que llevaba y se reorienta.
	if datos.Correccion ~= s.Correccion then
		s.Correccion = datos.Correccion
		s.Vx, s.Vy, s.Vz = 0, 0, 0
		local rx, ry = s.Raiz.CFrame:ToOrientation()
		s.Cabeceo, s.Guinada = rx, ry
	end
end

--[[
	El servidor avisa de un choque de ESTA nave. Si el rebote predicho aquí no ha ocurrido (la roca era muy pequeña
	o el cálculo local no la vio), se aplica ahora, y se la saca un poco de la roca.
]]
function Vuelo.Chocar(normal: Vector3)
	local s = sesion
	if s == nil or os.clock() - s.UltimoRebote < 0.3 then
		return
	end
	rebotar(s, normal)
	s.Modelo:PivotTo(s.Modelo:GetPivot() + normal * 3)
end

-- ¿Está el piloto dando órdenes de empuje ahora mismo? (para los propulsores)
function Vuelo.Acelerando(): boolean
	return sesion ~= nil and sesion.Acelerando
end

-- Deja de pilotar y devuelve los controles normales.
function Vuelo.Detener()
	RunService:UnbindFromRenderStep(NOMBRE_PASO)
	local s = sesion
	sesion = nil
	if s then
		if s.Fuerza.Parent then
			s.Fuerza.VectorVelocity = Vector3.zero
		end
		if s.TurboActivo then
			Camara.PonerTurbo(false)
		end
	end
	Entrada.Desactivar()
	controlesDeRoblox(true)
end

return Vuelo
