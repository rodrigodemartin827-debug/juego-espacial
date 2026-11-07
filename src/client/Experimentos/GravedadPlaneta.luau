--!strict
--[[
	EXPERIMENTO (cliente): andar sobre un planeta redondo. Ver shared/Experimentos/PlanetaRedondo.

	El Humanoid de Roblox solo sabe andar con el "arriba" del mundo (+Y): no se puede tumbar. Por eso, cerca del
	planeta, el personaje pasa a un CONTROLADOR PROPIO:
	  - El Humanoid se pone en estado Physics (no aplica fuerzas) y el script Animate se pausa.
	  - Una VectorForce anula la gravedad del mundo; la gravedad del planeta (hacia su centro) y el resto del
	    movimiento se calculan aquí y se escriben en la velocidad de la raíz cada paso de física.
	  - El suelo se busca con un rayo hacia el centro; un muelle mantiene la raíz a su altura (3 studs en R6), así
	    que sube y baja por las colinas sin tropezar.
	  - Una AlignOrientation pone el cuerpo de pie sobre la superficie y lo gira hacia donde anda.
	  - Andar, correr (Mayús izquierda) y saltar (Espacio) con las animaciones del propio Animate.
	  - La CÁMARA es propia: orbita con el botón derecho y la rueda, y su "arriba" es el del planeta. Su rumbo se
	    TRANSPORTA al andar (se conserva al dar la vuelta al planeta, sin giros bruscos en los polos).
	Lejos del planeta (o pilotando una nave) todo vuelve a ser lo normal de Roblox.

	Como el personaje es del cliente (propiedad de red), la física se calcula aquí, igual que hace Roblox.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Experimento = require(Shared.Experimentos.PlanetaRedondo)
local NavesConfig = require(Shared.Naves.Config)
local ConfigEleccion = require(Shared.Eleccion.Config)
local ConfigGraficos = require(Shared.Graficos.Config)

type Estado = {
	Personaje: Model,
	Humanoid: Humanoid,
	Raiz: BasePart,
	Adjunto: Attachment,
	Fuerza: VectorForce,
	Giro: AlignOrientation,
	Frente: Vector3,
	Pistas: { [string]: AnimationTrack },
	PistaActual: string?,
	Animate: LocalScript?,
	UltimoSalto: number,
	SaltoSoltado: boolean, -- el botón de saltar se ha soltado desde el último salto
	EnSuelo: boolean,
	Colisiones: { [BasePart]: string }, -- grupo de colisión de cada parte antes de activar (se devuelve al desactivar)
}

local GravedadPlaneta = {}

local jugador = Players.LocalPlayer
local estado: Estado? = nil
-- Capa de colisión fija de la región 1 (AlturasRegion), si está en el lugar. Ver iniciarRegion1.
local mapaRegion: any = nil
local controles: any = nil
local parametros = RaycastParams.new()
parametros.FilterType = Enum.RaycastFilterType.Exclude
parametros.IgnoreWater = true

-- Cámara.
local camFrente = Vector3.zAxis
local camCabeceo = Experimento.Camara.CabeceoInicial
local camDistancia = Experimento.Camara.Distancia
local rotando = false
local giroPendiente = Vector2.zero

local NOMBRE_CAMARA = "PlanetaRedondoCamara"
local ESTADOS_DESACTIVADOS = {
	Enum.HumanoidStateType.FallingDown,
	Enum.HumanoidStateType.Ragdoll,
	Enum.HumanoidStateType.GettingUp,
	Enum.HumanoidStateType.Climbing,
	Enum.HumanoidStateType.Swimming,
}

-- ===== Utilidades =====

local function proyectar(v: Vector3, arriba: Vector3, alternativa: Vector3): Vector3
	local p = v - arriba * v:Dot(arriba)
	if p.Magnitude < 1e-3 then
		p = alternativa - arriba * alternativa:Dot(arriba)
		if p.Magnitude < 1e-3 then
			return Experimento.Marco(Vector3.zero, arriba, Vector3.xAxis).LookVector
		end
	end
	return p.Unit
end

-- Acerca el vector `actual` a `objetivo` como mucho `paso` (aceleración limitada).
local function acercar(actual: Vector3, objetivo: Vector3, paso: number): Vector3
	local diferencia = objetivo - actual
	local largo = diferencia.Magnitude
	if largo <= paso or largo < 1e-4 then
		return objetivo
	end
	return actual + diferencia * (paso / largo)
end

local function obtenerControles(): any
	if controles == nil then
		pcall(function()
			local modulo =
				require(jugador:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: ModuleScript) :: any
			controles = modulo:GetControls()
		end)
	end
	return controles
end

-- ===== Animaciones (las del Animate del personaje, para que sean las mismas que fuera del planeta) =====

local ANIMACIONES: { [string]: boolean } = { idle = true, walk = true, run = true, jump = false, fall = true }

local function cargarPistas(personaje: Model, humanoid: Humanoid): { [string]: AnimationTrack }
	local pistas = {}
	local animate = personaje:FindFirstChild("Animate")
	local animator = humanoid:FindFirstChildOfClass("Animator")
	if animate == nil or animator == nil then
		return pistas
	end
	for nombre, enBucle in ANIMACIONES do
		local carpeta = animate:FindFirstChild(nombre)
		local animacion = carpeta and carpeta:FindFirstChildOfClass("Animation")
		if animacion then
			local pista = (animator :: Animator):LoadAnimation(animacion)
			pista.Priority = Enum.AnimationPriority.Movement
			pista.Looped = enBucle
			pistas[nombre] = pista
		end
	end
	return pistas
end

local function reproducir(e: Estado, nombre: string, velocidad: number?)
	local pista = e.Pistas[nombre]
	if e.PistaActual ~= nombre then
		local anterior = e.PistaActual and e.Pistas[e.PistaActual]
		if anterior then
			anterior:Stop(0.15)
		end
		if pista then
			pista:Play(0.15)
		end
		e.PistaActual = nombre
	end
	if pista and velocidad then
		pista:AdjustSpeed(velocidad)
	end
end

-- ===== Activar y desactivar =====

local function activar(personaje: Model, humanoid: Humanoid, raiz: BasePart)
	local arriba = Experimento.Arriba(raiz.Position)

	for _, tipo in ESTADOS_DESACTIVADOS do
		humanoid:SetStateEnabled(tipo, false)
	end
	humanoid.AutoRotate = false
	humanoid:ChangeState(Enum.HumanoidStateType.Physics)

	-- Se pausa el Animate (decide por los estados del Humanoid, que aquí no cambian) y se paran sus pistas.
	local animate = personaje:FindFirstChild("Animate")
	if animate and animate:IsA("LocalScript") then
		animate.Enabled = false
	end
	local animator = humanoid:FindFirstChildOfClass("Animator")
	if animator then
		for _, pista in animator:GetPlayingAnimationTracks() do
			if pista.Priority == Enum.AnimationPriority.Core or pista.Priority == Enum.AnimationPriority.Idle then
				pista:Stop(0.1)
			end
		end
	end

	local adjunto = Instance.new("Attachment")
	adjunto.Name = "PlanetaRedondo"
	adjunto.Parent = raiz
	local fuerza = Instance.new("VectorForce")
	fuerza.Name = "PlanetaRedondoAntigravedad"
	fuerza.Attachment0 = adjunto
	fuerza.RelativeTo = Enum.ActuatorRelativeTo.World
	fuerza.ApplyAtCenterOfMass = true
	fuerza.Force = Vector3.new(0, raiz.AssemblyMass * workspace.Gravity, 0)
	fuerza.Parent = raiz
	local giro = Instance.new("AlignOrientation")
	giro.Name = "PlanetaRedondoOrientacion"
	giro.Mode = Enum.OrientationAlignmentMode.OneAttachment
	giro.Attachment0 = adjunto
	giro.MaxTorque = math.huge
	giro.Responsiveness = 60
	giro.Parent = raiz

	-- El cuerpo no choca con nada: la altura la lleva el muelle y las paredes, el barrido de pasoFisica. Si el torso
	-- chocara, se engancharía en cada arista pequeña del terreno (solo tiene unos 2 studs de holgura sobre el suelo).
	local colisiones: { [BasePart]: string } = {}
	for _, parte in personaje:GetDescendants() do
		if parte:IsA("BasePart") then
			colisiones[parte] = parte.CollisionGroup
			parte.CollisionGroup = Experimento.Personaje.GrupoColision
		end
	end

	local frente = proyectar(raiz.CFrame.LookVector, arriba, Vector3.zAxis)
	giro.CFrame = Experimento.Marco(Vector3.zero, arriba, frente)
	parametros.FilterDescendantsInstances = { personaje }

	estado = {
		Personaje = personaje,
		Humanoid = humanoid,
		Raiz = raiz,
		Adjunto = adjunto,
		Fuerza = fuerza,
		Giro = giro,
		Frente = frente,
		Pistas = cargarPistas(personaje, humanoid),
		PistaActual = nil,
		Animate = if animate and animate:IsA("LocalScript") then animate else nil,
		UltimoSalto = 0,
		SaltoSoltado = false,
		EnSuelo = false,
		Colisiones = colisiones,
	}

	-- La cámara empieza mirando hacia donde mira el personaje.
	camFrente = frente
	camCabeceo = Experimento.Camara.CabeceoInicial
	local camara = workspace.CurrentCamera
	if camara and not personaje:GetAttribute(NavesConfig.AtributoPilotando) then
		camara.CameraType = Enum.CameraType.Scriptable
	end
end

local function desactivar(restaurarCamara: boolean)
	local e = estado
	if e == nil then
		return
	end
	estado = nil
	for _, pista in e.Pistas do
		pista:Stop(0.1)
	end
	e.Adjunto:Destroy()
	e.Fuerza:Destroy()
	e.Giro:Destroy()
	for parte, antes in e.Colisiones do
		if parte.Parent ~= nil then
			parte.CollisionGroup = antes
		end
	end
	if e.Personaje.Parent ~= nil and e.Humanoid.Health > 0 then
		for _, tipo in ESTADOS_DESACTIVADOS do
			e.Humanoid:SetStateEnabled(tipo, true)
		end
		e.Humanoid.AutoRotate = true
		if not e.Personaje:GetAttribute(NavesConfig.AtributoPilotando) then
			e.Humanoid:ChangeState(Enum.HumanoidStateType.Freefall)
			-- De vuelta al "arriba" del mundo, de pie.
			local posicion = e.Raiz.Position
			local frente = proyectar(e.Raiz.CFrame.LookVector, Vector3.yAxis, Vector3.zAxis)
			e.Raiz.CFrame = CFrame.lookAt(posicion, posicion + frente)
		end
	end
	if e.Animate and e.Animate.Parent ~= nil then
		e.Animate.Enabled = true
	end
	local camara = workspace.CurrentCamera
	if restaurarCamara and camara and camara.CameraType == Enum.CameraType.Scriptable then
		camara.CameraType = Enum.CameraType.Custom
		camara.CameraSubject = e.Humanoid
	end
end

-- ===== Física (cada paso, antes de simular) =====

local function pasoFisica(dt: number)
	local personaje = jugador.Character
	local humanoid = personaje and personaje:FindFirstChildOfClass("Humanoid")
	local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart") :: BasePart?
	local e = estado

	-- El personaje cambió (reapareció): se suelta el anterior.
	if e and e.Personaje ~= personaje then
		desactivar(true)
		e = nil
	end
	if personaje == nil or humanoid == nil or raiz == nil then
		return
	end
	local pilotando = personaje:GetAttribute(NavesConfig.AtributoPilotando) == true
	local altura = (raiz.Position - Experimento.Centro()).Magnitude - Experimento.Radio
	local dentro = altura < Experimento.Personaje.Alcance and humanoid.Health > 0 and not pilotando

	if dentro and e == nil then
		activar(personaje, humanoid, raiz)
		e = estado
	elseif not dentro and e ~= nil then
		desactivar(not pilotando)
		return
	end
	if e == nil then
		return
	end

	local p = Experimento.Personaje
	if humanoid:GetState() ~= Enum.HumanoidStateType.Physics then
		humanoid:ChangeState(Enum.HumanoidStateType.Physics)
	end
	e.Fuerza.Force = Vector3.new(0, raiz.AssemblyMass * workspace.Gravity, 0)

	local arriba = Experimento.Arriba(raiz.Position)
	local velocidad = raiz.AssemblyLinearVelocity
	local radial = velocidad:Dot(arriba)
	local tangente = velocidad - arriba * radial

	-- Lo que pide el jugador, en el sistema de la cámara (su frente y su derecha sobre el plano tangente).
	local mover = Vector3.zero
	local mandos = obtenerControles()
	if mandos then
		mover = mandos:GetMoveVector()
	end
	local frenteCamara = proyectar(camFrente, arriba, e.Frente)
	local derechaCamara = frenteCamara:Cross(arriba)
	local deseo = derechaCamara * mover.X - frenteCamara * mover.Z
	if deseo.Magnitude > 1 then
		deseo = deseo.Unit
	end
	local UserInputService = game:GetService("UserInputService")
	local corriendo = UserInputService:IsKeyDown(Enum.KeyCode.LeftShift)
	-- Solo para pruebas en Studio: el atributo VelocidadPruebaPlaneta del jugador fija la velocidad (dar la vuelta al
	-- planeta en poco tiempo). El experimento entero solo existe en Studio.
	local velocidadPrueba = jugador:GetAttribute("VelocidadPruebaPlaneta")
	local rapidezPedida = if type(velocidadPrueba) == "number"
		then velocidadPrueba
		elseif corriendo then p.Correr
		else p.Andar
	local objetivo = deseo * rapidezPedida
	-- Suelo: rayo hacia el centro del planeta. Se alarga con la velocidad de caída: a pocos FPS, en un fotograma se
	-- puede bajar más que el alcance normal del rayo y colarse a través del suelo.
	-- La complexión del personaje (Personaje/Constructor.Complexion) cambia lo larga que es la pierna: la raíz tiene que
	-- flotar más o menos sobre el suelo. Sin esto, un personaje alto se hunde en el suelo y uno bajo flota.
	local alturaRaiz = p.AlturaRaiz + (tonumber(raiz:GetAttribute("AlturaExtra")) or 0)
	local alcanceRayo = alturaRaiz + p.MargenSuelo + 4 + math.max(0, -radial) * dt
	local golpe = workspace:Raycast(raiz.Position, -arriba * alcanceRayo, parametros)
	local distancia = if golpe then golpe.Distance else math.huge
	-- Capa de colisión fija de la región 1 (su mapa de alturas): el suelo de verdad aunque la colisión de la malla
	-- tenga agujeros. Se usa la más alta de las dos (el rayo también ve edificios, puentes y piedras).
	local relativa = raiz.Position - Experimento.Centro()
	-- Solo para comparar en Studio (antes/después): con el atributo PruebaSinMapaAlturas en el jugador no se usa el mapa.
	local mapa = if jugador:GetAttribute("PruebaSinMapaAlturas") then nil else mapaRegion
	local sueloMapa = if mapa then mapa:radio(relativa) else nil
	if sueloMapa then
		distancia = math.min(distancia, relativa.Magnitude - sueloMapa)
	end
	-- Sonda por delante, hacia donde el jugador QUIERE ir (no hacia donde se mueve: si una piedra le frena, la sonda
	-- tiene que seguir viéndola). Si allí el suelo está más alto, el muelle sube ANTES de que el torso choque, así que
	-- las piedras y escalones de hasta AlturaPaso studs se pasan sin saltar. Cuanto más rápido, más lejos mira.
	if deseo.Magnitude > 0.1 then
		local sonda = p.SondaDelante + rapidezPedida * p.SondaPorVelocidad
		-- El rayo sale a AlturaPaso sobre los pies: lo que sea más alto que eso no lo ve (hay que saltarlo).
		local elevacion = p.AlturaPaso - alturaRaiz
		local origen = raiz.Position + deseo.Unit * sonda + arriba * elevacion
		local delante = workspace:Raycast(origen, -arriba * (alcanceRayo + elevacion), parametros)
		if delante then
			distancia = math.min(distancia, delante.Distance - elevacion)
		end
		if mapa and sueloMapa then
			local sueloDelante = mapa:radio(relativa + deseo.Unit * sonda)
			if sueloDelante and sueloDelante - sueloMapa <= p.AlturaPaso then
				distancia = math.min(distancia, relativa.Magnitude - sueloDelante)
			end
		end
	end
	local ahora = os.clock()
	local enSuelo = distancia <= alturaRaiz + p.MargenSuelo and radial <= 2 and ahora - e.UltimoSalto > 0.2
	e.EnSuelo = enSuelo

	tangente = acercar(tangente, objetivo, (if enSuelo then p.Aceleracion else p.AceleracionAire) * dt)

	-- Paredes: se barre una esfera a la altura del torso en la dirección del movimiento. Si toca algo empinado que
	-- además es más alto que el paso (lo bajo ya lo sube el muelle), no se avanza contra ello: se resbala a lo largo.
	local rapidez = tangente.Magnitude
	if rapidez > 0.05 then
		local barrido = workspace:Spherecast(
			raiz.Position + arriba * p.AlturaBarrido,
			p.RadioCuerpo,
			tangente.Unit * (rapidez * dt + p.MargenPared),
			parametros
		)
		-- Las caras que miran hacia abajo (la triangulación del Terrain las da a veces en las cuestas) no son pared.
		local inclinacion = if barrido then barrido.Normal:Dot(arriba) else 1
		if barrido and inclinacion < p.PendienteMaxima and inclinacion > -0.2 then
			local alturaChoque = (barrido.Position - raiz.Position):Dot(arriba) + alturaRaiz
			if alturaChoque > p.AlturaPaso then
				local normal = barrido.Normal - arriba * barrido.Normal:Dot(arriba)
				if normal.Magnitude > 1e-3 then
					normal = normal.Unit
					local contra = tangente:Dot(normal)
					if contra < 0 then
						tangente -= normal * contra
					end
				end
			end
		end
	end

	-- Salto: UNA vez por pulsación. Los controles de Roblox ponen Humanoid.Jump a true en cada fotograma mientras el botón
	-- está pulsado; si se saltara cada vez que vale true, al tocar el suelo con el botón aún pulsado se volvería a
	-- saltar (el «doble salto»). Solo cuenta el paso de suelto a pulsado.
	local pulsado = humanoid.Jump
	if not pulsado then
		e.SaltoSoltado = true
	end
	if enSuelo then
		if pulsado and e.SaltoSoltado then
			e.SaltoSoltado = false
			radial = p.Salto
			e.UltimoSalto = ahora
			e.EnSuelo = false
		else
			-- Muelle: la raíz vuelve a su altura sobre el suelo (sube las cuestas y baja los escalones).
			-- Si se ha quedado por debajo del suelo (llegó cayendo muy deprisa), sube sin el tope: no se hunde.
			local subida = if distancia < alturaRaiz - p.AlturaPaso then 80 else p.SubidaMaxima
			radial = math.clamp((alturaRaiz - distancia) * p.RigidezSuelo, -60, subida)
		end
	else
		radial -= p.Gravedad * dt
	end

	-- Terreno sin cargar (StreamingEnabled): cerca de la superficie pero sin nada debajo, no se cae a través del
	-- planeta; se queda quieto hasta que el motor traiga el suelo.
	if golpe == nil and sueloMapa == nil and not enSuelo then
		if altura < p.AlturaEsperaTerreno then
			local abajo = workspace:Raycast(raiz.Position, -arriba * (altura + p.AlturaEsperaTerreno), parametros)
			if abajo == nil then
				tangente = Vector3.zero
				radial = 0
			end
		end
	end
	raiz.AssemblyLinearVelocity = tangente + arriba * radial

	-- Orientación: de pie sobre la superficie, girando hacia donde anda.
	if deseo.Magnitude > 0.1 then
		local alfa = 1 - math.exp(-p.Giro * dt)
		e.Frente = proyectar(e.Frente:Lerp(deseo.Unit, alfa), arriba, deseo)
	else
		e.Frente = proyectar(e.Frente, arriba, frenteCamara)
	end
	e.Giro.CFrame = Experimento.Marco(Vector3.zero, arriba, e.Frente)

	-- Animación.
	rapidez = tangente.Magnitude
	if not e.EnSuelo then
		reproducir(e, if radial > 0 then "jump" else "fall")
	elseif rapidez > 0.6 then
		if rapidez > (p.Andar + p.Correr) / 2 and e.Pistas.run then
			reproducir(e, "run", rapidez / p.Correr)
		else
			reproducir(e, "walk", rapidez / p.Andar)
		end
	else
		reproducir(e, "idle")
	end
end

-- ===== Cámara =====

local function pasoCamara(_dt: number)
	local e = estado
	local camara = workspace.CurrentCamera
	if e == nil or camara == nil or e.Personaje:GetAttribute(NavesConfig.AtributoPilotando) then
		return
	end
	-- Mientras elige bando, la cámara es de la pantalla de elección (PROBADO EN STUDIO: esta, que va justo después,
	-- la pisaba y se veía al personaje delante de su casa en lugar de la escena).
	if
		jugador:GetAttribute(ConfigEleccion.AtributoEligiendo)
		or jugador:GetAttribute(ConfigEleccion.AtributoEnPantalla)
		or jugador:GetAttribute(ConfigGraficos.AtributoCamara)
	then
		return
	end
	if camara.CameraType ~= Enum.CameraType.Scriptable then
		camara.CameraType = Enum.CameraType.Scriptable
	end
	local c = Experimento.Camara
	local raiz = e.Raiz
	local arriba = Experimento.Arriba(raiz.Position)

	-- Rumbo transportado: se proyecta sobre el nuevo plano tangente (se conserva al moverse por la esfera).
	camFrente = proyectar(camFrente, arriba, e.Frente)
	if giroPendiente.Magnitude > 0 then
		camFrente = CFrame.fromAxisAngle(arriba, -giroPendiente.X * c.Sensibilidad):VectorToWorldSpace(camFrente)
		camCabeceo = math.clamp(camCabeceo + giroPendiente.Y * c.Sensibilidad, c.CabeceoMin, c.CabeceoMax)
		giroPendiente = Vector2.zero
	end

	local mirada = camFrente * math.cos(camCabeceo) - arriba * math.sin(camCabeceo)
	local foco = raiz.Position + arriba * c.Altura
	local distancia = camDistancia
	-- Que la cámara no se meta dentro del terreno.
	local golpe = workspace:Raycast(foco, -mirada * (distancia + 0.5), parametros)
	if golpe then
		distancia = math.max(0.5, golpe.Distance - 0.5)
	end
	local posicion = foco - mirada * distancia
	camara.CFrame = CFrame.lookAt(posicion, foco, arriba)
	camara.Focus = CFrame.new(foco)
end

--[[
	PRUEBA (rama prueba/region1-valle-alba): en cuanto el servidor monta la región 1, se arranca su LOD en este
	cliente (versiones detallada y simple, silueta de Aurora y vegetación). Ver server/Experimentos/PlanetaRedondo.
]]
local function iniciarRegion1()
	local carpeta = ReplicatedStorage:FindFirstChild("Region1")
	if not Experimento.Region1.Activa or carpeta == nil then
		return
	end
	task.spawn(function()
		workspace:WaitForChild("Region1_ValleDelAlba", math.huge) -- sin límite: el servidor la monta al arrancar (antes que el terreno)
		local ok, err = pcall(function()
			local ids = require(carpeta:WaitForChild("Datos"):WaitForChild("ids_texturas") :: ModuleScript) :: any
			local alturas = carpeta:FindFirstChild("AlturasRegion")
			local datosAlturas = carpeta:WaitForChild("Datos"):FindFirstChild("alturas")
			if alturas and datosAlturas then
				mapaRegion = (require(alturas :: ModuleScript) :: any).cargar(
					require(datosAlturas :: ModuleScript) :: any
				)
			end
			local ejemplo = require(carpeta:WaitForChild("EjemploArranque") :: ModuleScript) :: any
			ejemplo.iniciarCliente(ids[Experimento.Region1.Atlas], CFrame.new(Experimento.Centro()), ids)
		end)
		if not ok then
			warn(`[PlanetaRedondo] No se pudo arrancar el LOD de la región 1: {err}`)
		end
	end)
end

-- ===== API =====

function GravedadPlaneta.Iniciar()
	if not Experimento.Activado() then
		return
	end
	iniciarRegion1()
	local UserInputService = game:GetService("UserInputService")

	UserInputService.InputBegan:Connect(function(entrada, procesada)
		if estado == nil then
			return
		end
		if entrada.UserInputType == Enum.UserInputType.MouseButton2 and not procesada then
			rotando = true
			UserInputService.MouseBehavior = Enum.MouseBehavior.LockCurrentPosition
		end
	end)
	UserInputService.InputEnded:Connect(function(entrada)
		if entrada.UserInputType == Enum.UserInputType.MouseButton2 and rotando then
			rotando = false
			UserInputService.MouseBehavior = Enum.MouseBehavior.Default
		end
	end)
	UserInputService.InputChanged:Connect(function(entrada: InputObject, procesada: boolean)
		if estado == nil then
			return
		end
		if entrada.UserInputType == Enum.UserInputType.MouseMovement and rotando then
			giroPendiente += Vector2.new(entrada.Delta.X, entrada.Delta.Y)
		elseif entrada.UserInputType == Enum.UserInputType.MouseWheel and not procesada then
			local c = Experimento.Camara
			camDistancia = math.clamp(camDistancia * (1 - entrada.Position.Z * 0.12), c.DistanciaMin, c.DistanciaMax)
		end
	end)

	RunService.PreSimulation:Connect(pasoFisica)
	RunService:BindToRenderStep(NOMBRE_CAMARA, Enum.RenderPriority.Camera.Value + 1, pasoCamara)
end

-- Para las pruebas en Studio: ¿está el controlador del planeta llevando al personaje? ¿pisa suelo?
function GravedadPlaneta.Estado(): (boolean, boolean)
	return estado ~= nil, estado ~= nil and (estado :: Estado).EnSuelo
end

return GravedadPlaneta
