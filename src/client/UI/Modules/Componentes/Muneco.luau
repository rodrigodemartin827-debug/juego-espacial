--!strict
--[[
	Muneco: el "paper doll" del personaje: 4 slots a cada lado y el personaje en el centro.

	  [Casco]                 [Amuleto]
	  [Armadura]  (personaje) [Anillo]
	  [Espada]                [Cinturón]
	  [Arma]                  [Botas]
	        Explorador Estelar

	El personaje es un ViewportFrame con una copia del personaje R6 del jugador (sin scripts), sobre una plataforma
	holográfica, girando despacio mientras la pantalla está abierta. Hasta que hay personaje se ve la silueta R6
	discontinua (icono ui_holo_r6).
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Parent.Iconos.IconBuilder)
local DatosDemo = require(script.Parent.Parent.Datos.DatosDemo)
local EstadoUI = require(script.Parent.Parent.EstadoUI)
local P = require(script.Parent.Primitivas)
local SlotEquipo = require(script.Parent.SlotEquipo)

local C = Theme.Colores

local Muneco = {}

export type Muneco = {
	Marco: Frame,
	Refrescar: () -> (), -- vuelve a pintar los slots con el equipo actual
	MarcarObjetivo: (slot: string?) -> (), -- resalta el slot donde se puede equipar lo seleccionado
	Activar: (visible: boolean) -> (), -- gira el personaje solo mientras se ve
	ActualizarPersonaje: () -> (),
}

export type Opciones = {
	Compacto: boolean?,
	Tamano: UDim2,
	Posicion: UDim2,
	AlPulsarSlot: (slot: string) -> (),
	AlEntrarSlot: ((slot: string, boton: GuiObject) -> ())?,
	AlSalirSlot: ((slot: string) -> ())?,
}

-- Copia del personaje sin scripts ni sonidos, anclada, para el ViewportFrame.
local function copiarPersonaje(): Model?
	local jugador = Players.LocalPlayer
	local personaje = jugador and jugador.Character
	if personaje == nil or personaje:FindFirstChild("HumanoidRootPart") == nil then
		return nil
	end
	local archivable = personaje.Archivable
	personaje.Archivable = true
	local copia = personaje:Clone()
	personaje.Archivable = archivable
	if copia == nil then
		return nil
	end
	for _, hijo in copia:GetDescendants() do
		if hijo:IsA("BaseScript") or hijo:IsA("Sound") or hijo:IsA("ForceField") or hijo:IsA("ParticleEmitter") then
			hijo:Destroy()
		elseif hijo:IsA("BasePart") then
			hijo.Anchored = true
		end
	end
	local humanoid = copia:FindFirstChildOfClass("Humanoid")
	if humanoid then
		humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	end
	return copia
end

function Muneco.Crear(padre: Instance, o: Opciones): Muneco
	local compacto = o.Compacto == true
	local lado = Theme.Tamanos.SlotEquipo
	local separacion = if compacto then 10 else 12
	local marco = P.Marco(padre, { Nombre = "Muneco", Tamano = o.Tamano, Posicion = o.Posicion, Z = 3 })

	-- Columnas de slots.
	local columnas = {
		P.Marco(marco, { Nombre = "Izquierda", Tamano = UDim2.new(0, lado, 1, 0), Z = 3 }),
		P.Marco(marco, {
			Nombre = "Derecha",
			Tamano = UDim2.new(0, lado, 1, 0),
			Posicion = UDim2.fromScale(1, 0),
			Ancla = Vector2.new(1, 0),
			Z = 3,
		}),
	}
	for _, columna in columnas do
		P.Lista(columna, Enum.FillDirection.Vertical, separacion)
	end
	local slots: { [string]: SlotEquipo.SlotEquipo } = {}
	for i, slot in DatosDemo.Slots do
		slots[slot.Id] = SlotEquipo.Crear(columnas[slot.Lado + 1], {
			Slot = slot,
			Orden = i,
			AlPulsar = o.AlPulsarSlot,
			AlEntrar = o.AlEntrarSlot,
			AlSalir = o.AlSalirSlot,
		})
	end

	-- Centro: plataforma, personaje y título.
	local centro = P.Marco(marco, {
		Nombre = "Centro",
		Tamano = UDim2.new(1, -2 * (lado + 6), 1, 0),
		Posicion = UDim2.fromOffset(lado + 6, 0),
		Z = 3,
	})
	local altoTitulo = if compacto then 14 else 26
	local escenario = P.Marco(centro, { Nombre = "Escenario", Tamano = UDim2.new(1, 0, 1, -altoTitulo), Z = 3 })

	-- Plataforma holográfica: dos elipses (marcos aplastados) con borde cian.
	local colorBando = if EstadoUI.Jugador().Bando == "Monstruos" then C.BandoMonstruos else C.BandoHumanos
	local plataforma = P.Marco(escenario, {
		Nombre = "Plataforma",
		Tamano = UDim2.new(0.9, 0, 0, 18),
		Posicion = UDim2.new(0.5, 0, 1, -4),
		Ancla = Vector2.new(0.5, 1),
		Z = 3,
	})
	local aro = P.Marco(
		plataforma,
		{ Tamano = UDim2.fromScale(1, 1), Color = colorBando, Transparencia = 0.92, Radio = UDim.new(0.5, 0), Z = 3 }
	)
	P.Borde(aro, colorBando, 0.6)
	local nucleo = P.Marco(plataforma, {
		Tamano = UDim2.fromScale(0.62, 0.6),
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Color = colorBando,
		Transparencia = 0.82,
		Radio = UDim.new(0.5, 0),
		Z = 3,
	})
	P.Borde(nucleo, colorBando, 0.4)
	UITweens.Pulso(nucleo, "BackgroundTransparency", 0.88, 0.7, Theme.Tweens.PulsoLento)

	-- Silueta R6 discontinua mientras no hay personaje.
	local silueta = IconBuilder.Icono(escenario, "ui_holo_r6", {
		Tamano = UDim2.new(1, 0, 1, -6),
		Color = colorBando,
		Transparencia = 0.2,
		Posicion = UDim2.new(0.5, 0, 1, 0),
		Ancla = Vector2.new(0.5, 1),
		Z = 4,
	})

	local vista = P.Crear("ViewportFrame", {
		Name = "Personaje",
		BackgroundTransparency = 1,
		Size = UDim2.new(1, 0, 1, -6),
		Ambient = C.Fondo3:Lerp(C.Blanco, 0.55),
		LightColor = C.Blanco,
		LightDirection = Vector3.new(-1, -1, -1.5),
		ZIndex = 5,
		Parent = escenario,
	}) :: ViewportFrame
	local mundo = Instance.new("WorldModel")
	mundo.Parent = vista
	local camara = Instance.new("Camera")
	camara.FieldOfView = 30
	camara.Parent = vista
	vista.CurrentCamera = camara

	local modelo: Model? = nil
	local giro: RBXScriptConnection? = nil

	local function colocar(angulo: number)
		local m = modelo
		if m then
			m:PivotTo(CFrame.Angles(0, math.pi + angulo, 0))
		end
	end

	local function actualizarPersonaje()
		if modelo then
			modelo:Destroy()
			modelo = nil
		end
		local copia = copiarPersonaje()
		silueta.Visible = copia == nil
		if copia == nil then
			return
		end
		copia.Parent = mundo
		modelo = copia
		colocar(0)
		-- Encuadre: el personaje R6 mide ~5 studs; la cámara lo mira de frente, un poco desde arriba.
		local _, tamano = copia:GetBoundingBox()
		local distancia = (tamano.Y * 0.5) / math.tan(math.rad(camara.FieldOfView / 2)) + 1.5
		camara.CFrame = CFrame.lookAt(Vector3.new(0, 0.3, -distancia), Vector3.new(0, -0.2, 0))
	end

	if not compacto then
		P.Texto(centro, {
			Nombre = "Titulo",
			Texto = EstadoUI.Jugador().Titulo,
			Tamano = Theme.Texto.Cuerpo,
			Fuente = Theme.Fuentes.Titulo,
			Color = C.Acento,
			Espaciado = true,
			Posicion = UDim2.new(0.5, 0, 1, -14),
			Ancla = Vector2.new(0.5, 1),
			Z = 4,
		})
		P.Texto(centro, {
			Nombre = "Subtitulo",
			Texto = "R6",
			Tamano = Theme.Texto.Mini,
			Fuente = Theme.Fuentes.Titulo,
			Color = C.TextoSecundario,
			Transparencia = Theme.Alpha.TextoSecundario,
			Espaciado = true,
			Posicion = UDim2.new(0.5, 0, 1, 0),
			Ancla = Vector2.new(0.5, 1),
			Z = 4,
		})
	else
		P.Texto(centro, {
			Nombre = "Titulo",
			Texto = EstadoUI.Jugador().Titulo,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Titulo,
			Color = C.Acento,
			Espaciado = true,
			Posicion = UDim2.new(0.5, 0, 1, 0),
			Ancla = Vector2.new(0.5, 1),
			Z = 4,
		})
	end

	local function refrescar()
		local equipado = EstadoUI.Equipado()
		for id, slot in slots do
			local objeto = if equipado[id] then EstadoUI.Objeto(equipado[id]) else nil
			slot.PonerObjeto(if objeto then objeto.Arte else nil, if objeto then objeto.Rareza else nil)
		end
	end
	refrescar()

	local jugador = Players.LocalPlayer
	if jugador then
		jugador.CharacterAppearanceLoaded:Connect(function()
			task.wait(0.2)
			actualizarPersonaje()
		end)
	end

	return {
		Marco = marco,
		Refrescar = refrescar,
		MarcarObjetivo = function(idSlot: string?)
			for id, slot in slots do
				slot.MarcarObjetivo(id == idSlot)
			end
		end,
		ActualizarPersonaje = actualizarPersonaje,
		Activar = function(visible: boolean)
			if giro then
				giro:Disconnect()
				giro = nil
			end
			if visible then
				if modelo == nil then
					actualizarPersonaje()
				end
				-- Vaivén suave (±25°) solo mientras se ve: así no gasta nada con la pantalla cerrada.
				local inicio = os.clock()
				giro = RunService.RenderStepped:Connect(function()
					colocar(math.sin((os.clock() - inicio) * 0.6) * math.rad(25))
				end)
			end
		end,
	}
end

return Muneco
