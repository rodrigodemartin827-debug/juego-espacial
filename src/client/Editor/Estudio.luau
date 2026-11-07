--!strict
--[[
	Estudio (cliente): la escena 3D del editor de personaje. Solo la ve este jugador.

	  · Una sala redonda de metal oscuro con tiras de luz cian, una plataforma con un anillo de neón, luz de
	    estudio (clave cálida, contraluz cian y relleno azulado) y motas de luz flotando. Se monta lejos del mapa
	    (ConfigEditor.Escena.Centro), así nada del pueblo se pone delante de la cámara.
	  · En medio, una COPIA local del personaje R6 del jugador (sin scripts ni física), quieta con la animación de
	    reposo. El editor le pone cada cambio al instante (Personaje/Constructor) y un barrido de luz la recorre.
	  · Se gira arrastrando el ratón o el dedo fuera de la interfaz, con inercia al soltar.
	  · Cámara fija de frente encuadrando el cuerpo entero; el personaje se coloca en el hueco libre de la pantalla
	    (Encuadrar).

	El personaje de verdad se queda donde estaba (quieto y protegido por el servidor) y el servidor le pone la
	apariencia al guardar.
]]

local KeyframeSequenceProvider = game:GetService("KeyframeSequenceProvider")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Personaje.ConfigEditor)
local ConfigGraficos = require(Shared.Graficos.Config)
local Constructor = require(Shared.Personaje.Constructor)

local Estudio = {}

local PASO_CAMARA = "EditorEstudioCamara"
local CLASES_FUERA = {
	"Script",
	"LocalScript",
	"ForceField",
	"Sound",
	"VectorForce",
	"AlignOrientation",
	"AlignPosition",
	"LinearVelocity",
	"AngularVelocity",
	"BodyGyro",
	"BodyVelocity",
	"BodyPosition",
	"BodyForce",
}

local jugador = Players.LocalPlayer
local sala: Folder? = nil
local copia: Model? = nil
local raiz: BasePart? = nil
local anillo: BasePart? = nil
local destello: PointLight? = nil
local conexiones: { RBXScriptConnection } = {}
local pista: AnimationTrack? = nil
local giro = Config.Giro.Inicial
local velocidad = 0
local arrastrando = false
local ultimoMovimiento = 0
local posicionX = 0
local campoAntes = 70
local apariencia: any = nil
local reaplicar = false

local function color(hex: string): Color3
	return Color3.fromHex(hex)
end

local function centro(): Vector3
	local c = Config.Escena.Centro
	return Vector3.new(c[1], c[2], c[3])
end

local function pieza(padre: Instance, props: { [string]: any }): Part
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = false
	p.CastShadow = true
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	for k, v in props do
		(p :: any)[k] = v
	end
	p.Parent = padre
	return p
end

-- ===== Sala =====

local function construirSala(): Folder
	local e = Config.Escena
	local c = centro()
	local carpeta = Instance.new("Folder")
	carpeta.Name = "EditorEstudio"

	-- Suelo y techo (el techo tapa el sol: la luz es la del estudio).
	pieza(carpeta, {
		Name = "Suelo",
		Shape = Enum.PartType.Cylinder,
		Size = Vector3.new(0.6, e.RadioSala * 2 + 2, e.RadioSala * 2 + 2),
		CFrame = CFrame.new(c - Vector3.new(0, 0.3, 0)) * CFrame.Angles(0, 0, math.pi / 2),
		Color = color(e.ColorSuelo),
		Material = Enum.Material.DiamondPlate,
	})
	pieza(carpeta, {
		Name = "Techo",
		Size = Vector3.new(e.RadioSala * 2 + 4, 0.6, e.RadioSala * 2 + 4),
		CFrame = CFrame.new(c + Vector3.new(0, e.AltoSala, 0)),
		Color = color(e.ColorPared),
		Material = Enum.Material.Metal,
		CastShadow = false,
	})

	-- Pared: paneles en círculo con una tira de luz vertical entre cada dos y una línea de luz baja.
	local n = e.Paneles
	local ancho = 2 * e.RadioSala * math.tan(math.pi / n) + 0.1
	for i = 0, n - 1 do
		local a = (i + 0.5) / n * 2 * math.pi
		local dir = Vector3.new(math.sin(a), 0, math.cos(a))
		local base = c + dir * e.RadioSala
		local mira = CFrame.lookAt(base, c)
		pieza(carpeta, {
			Name = "Panel",
			Size = Vector3.new(ancho, e.AltoSala, 0.6),
			CFrame = mira * CFrame.new(0, e.AltoSala / 2, 0),
			Color = color(e.ColorPared),
			Material = Enum.Material.Metal,
			CastShadow = false,
		})
		-- Remaches: un saliente horizontal en cada panel le da relieve.
		pieza(carpeta, {
			Name = "Moldura",
			Size = Vector3.new(ancho * 0.9, 0.35, 0.3),
			CFrame = mira * CFrame.new(0, 5.5, -0.4),
			Color = color(e.ColorPlataforma),
			Material = Enum.Material.Metal,
			CastShadow = false,
		})
		local b = i / n * 2 * math.pi
		local dirB = Vector3.new(math.sin(b), 0, math.cos(b))
		pieza(carpeta, {
			Name = "Tira",
			Size = Vector3.new(0.12, e.AltoSala - 3, 0.12),
			CFrame = CFrame.lookAt(c + dirB * (e.RadioSala - 0.45), c) * CFrame.new(0, e.AltoSala / 2 + 0.5, 0),
			Color = color(e.ColorLuz),
			Material = Enum.Material.Neon,
			Transparency = 0.25,
			CastShadow = false,
		})
	end
	pieza(carpeta, {
		Name = "LineaBaja",
		Shape = Enum.PartType.Cylinder,
		Size = Vector3.new(0.12, (e.RadioSala - 0.6) * 2, (e.RadioSala - 0.6) * 2),
		CFrame = CFrame.new(c + Vector3.new(0, 0.9, 0)) * CFrame.Angles(0, 0, math.pi / 2),
		Color = color(e.ColorLuz),
		Material = Enum.Material.Neon,
		Transparency = 0.55,
		CastShadow = false,
	})

	-- Plataforma: hexágono de metal con anillo de neón y un disco de luz bajo los pies.
	local r = e.RadioPlataforma
	for k = 0, 5 do
		pieza(carpeta, {
			Name = "Plataforma",
			Size = Vector3.new(r * 2 * math.tan(math.pi / 6) + 0.02, e.AltoPlataforma, r),
			CFrame = CFrame.new(c + Vector3.new(0, e.AltoPlataforma / 2, 0))
				* CFrame.Angles(0, k * math.pi / 3, 0)
				* CFrame.new(0, 0, r / 2),
			Color = color(e.ColorPlataforma),
			Material = Enum.Material.Metal,
		})
	end
	pieza(carpeta, {
		Name = "Anillo",
		Shape = Enum.PartType.Cylinder,
		Size = Vector3.new(0.1, r * 2 + 0.3, r * 2 + 0.3),
		-- Por debajo de la tapa de la plataforma: de este disco solo se ve el canto que asoma alrededor.
		CFrame = CFrame.new(c + Vector3.new(0, e.AltoPlataforma - 0.12, 0)) * CFrame.Angles(0, 0, math.pi / 2),
		Color = color(e.ColorLuz),
		Material = Enum.Material.Neon,
		CastShadow = false,
	})
	pieza(carpeta, {
		Name = "Disco",
		Shape = Enum.PartType.Cylinder,
		Size = Vector3.new(0.02, r * 1.1, r * 1.1),
		CFrame = CFrame.new(c + Vector3.new(0, e.AltoPlataforma + 0.01, 0)) * CFrame.Angles(0, 0, math.pi / 2),
		Color = color(e.ColorLuz),
		Material = Enum.Material.Neon,
		Transparency = 0.93,
		CastShadow = false,
	})

	-- Luces: clave cálida delante a la izquierda, contraluz cian detrás y relleno azulado.
	local function foco(nombre: string, pos: Vector3, datos: { Brillo: number, Color: string }, angulo: number)
		local soporte = pieza(carpeta, {
			Name = nombre,
			Size = Vector3.new(0.2, 0.2, 0.2),
			CFrame = CFrame.lookAt(pos, c + Vector3.new(0, 3, 0)),
			Transparency = 1,
			CastShadow = false,
		})
		local luz = Instance.new("SpotLight")
		luz.Brightness = datos.Brillo
		luz.Color = color(datos.Color)
		luz.Range = 26
		luz.Angle = angulo
		luz.Shadows = true
		luz.Face = Enum.NormalId.Front
		luz.Parent = soporte
	end
	foco("LuzClave", c + Vector3.new(5, 9, -9), e.LuzClave, 55)
	foco("LuzContra", c + Vector3.new(-3, 8, 8), e.LuzContra, 60)
	foco("LuzRelleno", c + Vector3.new(-7, 4, -6), e.LuzRelleno, 70)
	local cara = pieza(carpeta, {
		Name = "LuzCara",
		Size = Vector3.new(0.2, 0.2, 0.2),
		CFrame = CFrame.new(c + Vector3.new(0, e.AltoPlataforma + 5, -6)),
		Transparency = 1,
		CastShadow = false,
	})
	local luzCara = Instance.new("PointLight")
	luzCara.Brightness = e.LuzCara.Brillo
	luzCara.Color = color(e.LuzCara.Color)
	luzCara.Range = 12
	luzCara.Shadows = false
	luzCara.Parent = cara

	-- Motas de luz flotando por la sala.
	local emisor = pieza(carpeta, {
		Name = "Motas",
		Size = Vector3.new(e.RadioSala * 1.4, 1, e.RadioSala * 1.4),
		CFrame = CFrame.new(c + Vector3.new(0, 1, 0)),
		Transparency = 1,
		CastShadow = false,
	})
	local motas = Instance.new("ParticleEmitter")
	motas.Rate = e.Motas
	motas.Lifetime = NumberRange.new(5, 8)
	motas.Speed = NumberRange.new(0.6, 1.4)
	motas.SpreadAngle = Vector2.new(20, 20)
	motas.EmissionDirection = Enum.NormalId.Top
	motas.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(0.2, 0.09),
		NumberSequenceKeypoint.new(1, 0),
	})
	motas.Transparency = NumberSequence.new(0.2)
	motas.LightEmission = 1
	motas.Color = ColorSequence.new(color(e.ColorLuz))
	motas.Parent = emisor

	-- Anillo del barrido (se reutiliza en cada cambio).
	local a = pieza(carpeta, {
		Name = "Barrido",
		Shape = Enum.PartType.Cylinder,
		Size = Vector3.new(0.06, 3.4, 3.4),
		CFrame = CFrame.new(c) * CFrame.Angles(0, 0, math.pi / 2),
		Color = color(e.Barrido.Color),
		Material = Enum.Material.Neon,
		Transparency = 1,
		CastShadow = false,
	})
	anillo = a
	local d = Instance.new("PointLight")
	d.Color = color(e.Barrido.Color)
	d.Range = 8
	d.Brightness = 0
	d.Parent = a
	destello = d

	carpeta.Parent = workspace
	return carpeta
end

-- ===== Copia del personaje =====

local function idReposo(): string
	local r = Config.Reposo
	if RunService:IsStudio() then
		local carpeta: Instance? = ReplicatedStorage
		for _, nombre in r.Carpeta do
			carpeta = carpeta and carpeta:FindFirstChild(nombre)
		end
		local secuencia = carpeta and carpeta:FindFirstChild(r.Nombre)
		if secuencia and secuencia:IsA("KeyframeSequence") then
			local ok, id = pcall(function()
				return KeyframeSequenceProvider:RegisterKeyframeSequence(secuencia)
			end)
			if ok then
				return id
			end
		end
	end
	return r.Id
end

local function crearCopia(origen: Model): Model?
	local antes = origen.Archivable
	origen.Archivable = true
	local m = origen:Clone() :: Model?
	origen.Archivable = antes
	if m == nil then
		return nil
	end
	for _, d in m:GetDescendants() do
		if table.find(CLASES_FUERA, d.ClassName) then
			d:Destroy()
		end
	end
	m.Name = "EditorCopia"
	local humanoide = m:FindFirstChildOfClass("Humanoid")
	local r = m:FindFirstChild("HumanoidRootPart")
	if humanoide == nil or r == nil or not r:IsA("BasePart") then
		m:Destroy()
		return nil
	end
	humanoide.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	humanoide.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	humanoide.BreakJointsOnDeath = false
	humanoide:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = d == r
			d.CanCollide = false
			d.CanTouch = false
			d.CanQuery = false
		end
	end
	raiz = r
	return m
end

local function colocar()
	local r = raiz
	if r == nil then
		return
	end
	local altura = Config.Escena.AltoPlataforma + 3 -- la raíz del R6 está a 3 studs de los pies
	r.CFrame = CFrame.new(centro() + Vector3.new(0, altura, 0)) * CFrame.Angles(0, giro, 0)
end

local function reproducirReposo(m: Model)
	local humanoide = m:FindFirstChildOfClass("Humanoid") :: Humanoid
	local existente = humanoide:FindFirstChildOfClass("Animator")
	local animador: Animator = if existente then existente else Instance.new("Animator")
	animador.Parent = humanoide
	local anim = Instance.new("Animation")
	anim.AnimationId = idReposo()
	local ok, p = pcall(function()
		return animador:LoadAnimation(anim)
	end)
	if ok and p then
		p.Looped = true
		p:Play(0)
		pista = p
	else
		warn(`[Editor] No se pudo cargar la animación de reposo: {p}`)
	end
end

-- ===== Barrido de luz =====

local tweenAnillo: Tween? = nil
local function barrer()
	local a, d, r = anillo, destello, raiz
	if a == nil or d == nil or r == nil then
		return
	end
	local b = Config.Escena.Barrido
	local pies = r.Position.Y - 3
	a.CFrame = CFrame.new(r.Position.X, pies + 0.1, r.Position.Z) * CFrame.Angles(0, 0, math.pi / 2)
	a.Transparency = 0.15
	d.Brightness = 3
	if tweenAnillo then
		tweenAnillo:Cancel()
	end
	local info = TweenInfo.new(b.Segundos, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	local t = TweenService:Create(a, info, {
		CFrame = CFrame.new(r.Position.X, pies + 5.6, r.Position.Z) * CFrame.Angles(0, 0, math.pi / 2),
		Transparency = 1,
	})
	TweenService:Create(d, info, { Brightness = 0 }):Play()
	t:Play()
	tweenAnillo = t
end

-- ===== Apariencia =====

--[[
	Pone la apariencia `a` en la copia. Con `conBarrido`, un barrido de luz la recorre. Si alguna pieza 3D aún no ha
	llegado del servidor (las plantillas se crean al arrancar), se vuelve a poner cuando llegue.
]]
function Estudio.Aplicar(a: any, conBarrido: boolean?)
	apariencia = a
	local m = copia
	if m == nil then
		return
	end
	local ok, faltan = pcall(Constructor.Aplicar, m, a)
	if not ok then
		warn(`[Editor] No se pudo poner la apariencia: {faltan}`)
		return
	end
	reaplicar = (faltan :: number) > 0
	if conBarrido then
		barrer()
	end
end

-- Solo repinta los colores (mientras se arrastra por la rueda de color: rehacer las piezas sería demasiado).
function Estudio.Colorear(a: any)
	apariencia = a
	local m = copia
	if m then
		local ok, err = pcall(function(): any
			Constructor.Colorear(m, a)
			return nil
		end)
		if not ok then
			warn(`[Editor] No se pudieron poner los colores: {err}`)
		end
	end
end

-- ===== Cámara y giro =====

function Estudio.Encuadrar(x: number)
	posicionX = x
end

local function camara(dt: number)
	local cam = workspace.CurrentCamera
	local r = raiz
	if cam == nil or r == nil then
		return
	end
	-- Inercia al soltar.
	if not arrastrando and math.abs(velocidad) > 1e-4 then
		giro += velocidad * dt
		velocidad *= math.exp(-Config.Giro.Inercia * dt)
	end
	colocar()

	local c = Config.Camara
	cam.CameraType = Enum.CameraType.Scriptable
	cam.FieldOfView = c.CampoVision
	local base = Vector3.new(r.Position.X, r.Position.Y + c.Mira, r.Position.Z)
	local medioV = math.rad(c.CampoVision) / 2
	local distancia = (c.AltoVisible / 2) / math.tan(medioV)
	local aspecto = cam.ViewportSize.X / math.max(cam.ViewportSize.Y, 1)
	local medioH = math.atan(math.tan(medioV) * aspecto)
	local desde = base + Vector3.new(0, 0.5, -distancia)
	local cf = CFrame.lookAt(desde, base + Vector3.new(0, 0.1, 0))
	-- Desplazar la cámara a un lado coloca al personaje en el otro lado de la pantalla.
	cf += cf.RightVector * (-posicionX * distancia * math.tan(medioH))
	cam.CFrame = cf
end

local function conectarGiro()
	table.insert(
		conexiones,
		UserInputService.InputBegan:Connect(function(entrada: InputObject, procesada: boolean)
			if procesada then
				return -- sobre un botón de la interfaz
			end
			local t = entrada.UserInputType
			if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.Touch then
				arrastrando = true
				velocidad = 0
			end
		end)
	)
	table.insert(
		conexiones,
		UserInputService.InputEnded:Connect(function(entrada: InputObject)
			local t = entrada.UserInputType
			if t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.Touch then
				arrastrando = false
				-- Si se quedó quieto antes de soltar, no sigue girando.
				if os.clock() - ultimoMovimiento > 0.12 then
					velocidad = 0
				end
			end
		end)
	)
	table.insert(
		conexiones,
		UserInputService.InputChanged:Connect(function(entrada: InputObject)
			local t = entrada.UserInputType
			if arrastrando and (t == Enum.UserInputType.MouseMovement or t == Enum.UserInputType.Touch) then
				local paso = entrada.Delta.X * Config.Giro.Sensibilidad
				giro += paso
				-- La velocidad para la inercia (rad/s), suavizada entre movimientos.
				local ahora = os.clock()
				local dt = math.clamp(ahora - ultimoMovimiento, 1 / 120, 0.1)
				ultimoMovimiento = ahora
				velocidad = velocidad * 0.4 + (paso / dt) * 0.6
			end
		end)
	)
end

-- ===== Abrir y cerrar =====

-- Monta la escena con una copia de `origen` (el personaje del jugador) vestida con `a`. Devuelve true si se pudo.
function Estudio.Abrir(origen: Model, a: any): boolean
	Estudio.Cerrar()
	sala = construirSala()
	local m = crearCopia(origen)
	if m == nil then
		Estudio.Cerrar()
		return false
	end
	copia = m
	giro = Config.Giro.Inicial
	velocidad = 0
	colocar()
	m.Parent = sala
	Estudio.Aplicar(a, false)
	reproducirReposo(m)

	-- Las piezas que aún no estaban se ponen en cuanto llegan sus plantillas.
	task.spawn(function()
		local plantillas = ReplicatedStorage:WaitForChild(Constructor.CARPETA_PLANTILLAS, 30)
		if plantillas == nil then
			return
		end
		table.insert(
			conexiones,
			plantillas.ChildAdded:Connect(function()
				if reaplicar then
					reaplicar = false
					task.defer(function()
						if copia and apariencia then
							Estudio.Aplicar(apariencia, false)
						end
					end)
				end
			end)
		)
		if reaplicar and copia and apariencia then
			Estudio.Aplicar(apariencia, false)
		end
	end)

	local cam = workspace.CurrentCamera
	campoAntes = if cam then cam.FieldOfView else 70
	jugador:SetAttribute(ConfigGraficos.AtributoCamara, true)
	RunService:BindToRenderStep(PASO_CAMARA, Enum.RenderPriority.Camera.Value + 2, camara)
	conectarGiro()
	return true
end

function Estudio.Cerrar()
	RunService:UnbindFromRenderStep(PASO_CAMARA)
	for _, c in conexiones do
		c:Disconnect()
	end
	table.clear(conexiones)
	if pista then
		pista:Stop(0)
		pista = nil
	end
	if sala then
		sala:Destroy()
		sala = nil
	end
	copia = nil
	raiz = nil
	anillo = nil
	destello = nil
	arrastrando = false
	if jugador:GetAttribute(ConfigGraficos.AtributoCamara) then
		jugador:SetAttribute(ConfigGraficos.AtributoCamara, nil)
		local cam = workspace.CurrentCamera
		if cam then
			cam.FieldOfView = campoAntes
			local personaje = jugador.Character
			local r = personaje and personaje:FindFirstChild("HumanoidRootPart")
			if not (r and r:FindFirstChild("PlanetaRedondoAntigravedad")) then
				cam.CameraType = Enum.CameraType.Custom
			end
		end
	end
end

return Estudio
