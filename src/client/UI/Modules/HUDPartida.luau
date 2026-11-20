--!strict
--[[
	HUDPartida: el HUD que se ve DURANTE el juego. Mínimo y limpio, para no tapar la acción.

	  ┌──────────────────────────────────────────────────────────────────────────────┐
	  │      [VIDA ████████░░] [ESCUDO ████░░]     │ SECTOR 7-B │ ARENA 2v2 │         │
	  │       2.400/3.200       800/1.200                 02:34          ( MINIMAPA ) │
	  │      ENERGÍA ▬▬▬▬▬▬▬▬▬▬                                                        │
	  │                                                     [E] Recoger               │
	  │      ESPADA DE PLASMA        (Z) (X) (C) (V)              DMG  SPD  DEF        │
	  │      [1][2]                   cooldowns                    168  16   320       │
	  └──────────────────────────────────────────────────────────────────────────────┘

	  - Vida: la del Humanoid (real), verde → rojo según el porcentaje, con barra fantasma roja del daño reciente.
	  - Escudo personal: de demostración (todavía no existe en el juego). Energía: la del combate (real).
	  - Minimapa circular: tú en el centro (flecha cian), aliados en verde y enemigos en rojo (jugadores y objetivos de
	    combate cercanos). Gira con la cámara. M lo amplía.
	  - Armas: 2 casillas (1 y 2); la activa con borde cian y halo, la otra al 40 %.
	  - Habilidades: 4 casillas con los poderes reales (tecla, nombre y cooldown de Combate/Datos/Poderes). El cooldown
	    es un velo oscuro que se vacía en el sentido de las agujas del reloj, con los segundos que faltan.
	  - Aviso de interacción: sustituye al de los ProximityPrompt ("[E] Recoger · Contenedor"); en móvil se toca.
	  - Se oculta con un fundido de 0,2 s al abrir un menú o al pilotar una nave.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Theme = require(script.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Componentes.Primitivas)
local BarraVida = require(script.Parent.Componentes.BarraVida)
local Lienzo = require(script.Parent.Componentes.Lienzo)
local ConfigUI = require(script.Parent.Datos.ConfigUI)
local DatosDemo = require(script.Parent.Datos.DatosDemo)
local EstadoUI = require(script.Parent.EstadoUI)

local Shared = ReplicatedStorage:WaitForChild("Shared")
local ConfigCombate = require(Shared.Combate.Config)
local Senal = require(Shared.Utilidades.Senal)

local C = Theme.Colores
local A = Theme.Alpha
local H = Theme.HUD

local HUDPartida = {}

-- Se dispara con 1 (cuerpo a cuerpo) o 2 (arma de fuego) al cambiar de arma. TODO(armas): conectarlo al sistema de armas.
HUDPartida.ArmaCambiada = Senal.nueva()

-- ===== Estado =====
local raizHUD: Frame = nil :: any
local cambiarEscala: (k: number) -> () = function(_: number) end
local visible = true
local solicitar: (id: string) -> () = function(_: string) end

local barraVida: BarraVida.BarraVida = nil :: any
local barraEscudo: BarraVida.BarraVida = nil :: any
local barraEnergia: BarraVida.BarraVida = nil :: any
local textoVida: TextLabel = nil :: any
local textoEscudo: TextLabel = nil :: any

local textoSector: TextLabel = nil :: any
local textoModo: TextLabel = nil :: any
local textoTiempo: TextLabel = nil :: any
local finTemporizador: number? = nil

local minimapa: Frame = nil :: any
local disco: CanvasGroup = nil :: any
local capaPuntos: Frame = nil :: any
local norte: TextLabel = nil :: any
local puntos: { Frame } = {} -- reserva de puntos reutilizables
local minimapaGrande = false

local aviso: TextButton = nil :: any
local avisoTecla: TextLabel = nil :: any
local avisoTexto: TextLabel = nil :: any
local avisoSub: TextLabel = nil :: any
local avisoBarra: Frame = nil :: any
local promptActual: ProximityPrompt? = nil

local slotsArma: { Frame } = {}
local nombreArma: TextLabel = nil :: any
local armaActiva = 1

type CasillaHabilidad = {
	Id: string,
	Marco: Frame,
	Circulo: TextButton,
	Icono: ImageLabel,
	Halo: UIStroke,
	MitadIzq: UIGradient,
	MitadDer: UIGradient,
	CirculoIzq: Frame,
	CirculoDer: Frame,
	Tiempo: TextLabel,
	Pie: TextLabel,
	Nombre: string,
	Coste: number,
	EnCooldown: boolean,
	UltimoTexto: string,
}
local casillas: { CasillaHabilidad } = {}

-- ===== Vida, escudo y energía =====

local function construirVitales()
	local V = H.Vitales
	local marco = P.Marco(raizHUD, {
		Nombre = "Vitales",
		Tamano = UDim2.fromOffset(V.AnchoVida + V.AnchoEscudo + 10, 56),
		Posicion = UDim2.fromOffset(V.X, V.Y),
		Z = 10,
	})
	local function bloque(
		nombre: string,
		icono: string,
		color: Color3,
		ancho: number,
		x: number,
		tipo: BarraVida.Tipo
	): (BarraVida.BarraVida, TextLabel)
		local cab = P.Marco(marco, { Tamano = UDim2.fromOffset(ancho, 10), Posicion = UDim2.fromOffset(x, 0), Z = 10 })
		P.Lista(cab, Enum.FillDirection.Horizontal, 4, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
		IconBuilder.Icono(cab, icono, { Tamano = 9, Color = color, Orden = 1, Z = 11 })
		P.Texto(cab, {
			Texto = nombre,
			Tamano = Theme.Texto.Mini,
			Fuente = Theme.Fuentes.Negrita,
			Color = C.TextoPrincipal,
			Transparencia = A.TextoMedio,
			Espaciado = true,
			Contorno = true,
			Orden = 2,
			Z = 11,
		})
		local barra = BarraVida.Crear(
			marco,
			{ Tipo = tipo, Ancho = ancho, Alto = V.AltoBarra, Posicion = UDim2.fromOffset(x, 13), Z = 10 }
		)
		local texto = P.Texto(marco, {
			Texto = "",
			Rico = true,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Negrita,
			Posicion = UDim2.fromOffset(x, 27),
			Contorno = true,
			Z = 10,
		})
		return barra, texto
	end
	barraVida, textoVida = bloque("VIDA", "stat_aguante", C.Aguante, V.AnchoVida, 0, "Vida")
	barraEscudo, textoEscudo = bloque("ESCUDO", "hab_escudo", C.Acento, V.AnchoEscudo, V.AnchoVida + 10, "Escudo")

	local energia = P.Marco(raizHUD, {
		Nombre = "Energia",
		Tamano = UDim2.fromOffset(V.AnchoEnergia + 40, 8),
		Posicion = UDim2.fromOffset(V.X, V.Y + 44),
		Z = 10,
	})
	P.Texto(energia, {
		Texto = "ENERGÍA",
		Tamano = Theme.Texto.Micro + 0.5,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Energia,
		Espaciado = true,
		Contorno = true,
		Posicion = UDim2.fromScale(0, 0.5),
		Ancla = Vector2.new(0, 0.5),
		Z = 10,
	})
	barraEnergia = BarraVida.Crear(
		energia,
		{ Tipo = "Energia", Ancho = V.AnchoEnergia, Alto = 4, Posicion = UDim2.new(0, 36, 0.5, -2), Z = 10 }
	)
end

local function texto2(actual: number, maximo: number): string
	return `{P.Numero(actual)}<font transparency="0.55" size="{Theme.Texto.Mini}">/{P.Numero(maximo)}</font>`
end

local humanoid: Humanoid? = nil
local function pintarVida(instantaneo: boolean?)
	local h = humanoid
	if h == nil then
		return
	end
	local maximo = math.max(h.MaxHealth, 1)
	local actual = math.clamp(h.Health, 0, maximo)
	barraVida.Poner(actual, maximo, instantaneo)
	textoVida.Text = texto2(math.ceil(actual), math.ceil(maximo))
	if not instantaneo and actual < maximo * 0.999 then
		-- Pequeña sacudida de los números al recibir daño.
		UITweens.Sacudir(textoVida, 1.5)
	end
end

local function seguirPersonaje(personaje: Model)
	local h = personaje:WaitForChild("Humanoid", 10)
	if h == nil or not h:IsA("Humanoid") then
		return
	end
	humanoid = h
	local anterior = h.Health
	h.HealthChanged:Connect(function(nueva)
		pintarVida(nueva >= anterior)
		anterior = nueva
	end)
	h:GetPropertyChangedSignal("MaxHealth"):Connect(function()
		pintarVida(true)
	end)
	pintarVida(true)
end

-- ===== Info de partida =====

local function construirInfo()
	local info = P.Marco(raizHUD, {
		Nombre = "InfoPartida",
		Tamano = UDim2.fromOffset(0, 40),
		Posicion = UDim2.new(0.5, 50, 0, H.Info.Y),
		Ancla = Vector2.new(0.5, 0),
		Z = 10,
	})
	info.AutomaticSize = Enum.AutomaticSize.X
	local fila = P.Marco(info, {
		Nombre = "Fila",
		Tamano = UDim2.fromOffset(0, 22),
		Posicion = UDim2.fromScale(0.5, 0),
		Ancla = Vector2.new(0.5, 0),
		Color = C.FondoProfundo,
		Transparencia = A.HUDFondo,
		Radio = UDim.new(0, 6),
		Z = 10,
	})
	fila.AutomaticSize = Enum.AutomaticSize.X
	P.Borde(fila, C.Acento, A.BordeSutil)
	P.Lista(fila, Enum.FillDirection.Horizontal, 0, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)
	local sector = P.Marco(fila, { Tamano = UDim2.fromOffset(0, 22), Orden = 1, Z = 11 })
	sector.AutomaticSize = Enum.AutomaticSize.X
	P.Relleno(sector, 0, 10)
	P.Lista(sector, Enum.FillDirection.Horizontal, 5, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)
	IconBuilder.Icono(sector, "sidebar_mapa", { Tamano = 10, Color = C.Acento, Orden = 1, Z = 12 })
	textoSector = P.Texto(sector, {
		Texto = "",
		Tamano = Theme.Texto.Pequeno + 0.5,
		Fuente = Theme.Fuentes.Negrita,
		Espaciado = true,
		Orden = 2,
		Z = 12,
	})
	P.Marco(
		fila,
		{ Tamano = UDim2.fromOffset(1, 22), Color = C.Acento, Transparencia = A.BordeActivo, Orden = 2, Z = 11 }
	)
	local modo = P.Marco(fila, { Tamano = UDim2.fromOffset(0, 22), Orden = 3, Z = 11 })
	modo.AutomaticSize = Enum.AutomaticSize.X
	P.Relleno(modo, 0, 10)
	P.Lista(modo, Enum.FillDirection.Horizontal, 0, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)
	textoModo = P.Texto(modo, {
		Texto = "",
		Tamano = Theme.Texto.Pequeno + 0.5,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Acento,
		Espaciado = true,
		Z = 12,
	})
	textoTiempo = P.Texto(info, {
		Texto = "",
		Tamano = Theme.Texto.Grande,
		Fuente = Theme.Fuentes.Negrita,
		Posicion = UDim2.new(0.5, 0, 0, 25),
		Ancla = Vector2.new(0.5, 0),
		Contorno = true,
		Z = 10,
	})
	textoTiempo.Visible = false
end

-- Cambia el sector, el modo y (opcional) un temporizador en segundos (ranked, raids...).
function HUDPartida.PonerInfo(sector: string, modo: string, segundos: number?)
	textoSector.Text = P.Espaciar(string.upper(sector))
	textoModo.Text = P.Espaciar(string.upper(modo))
	textoModo.TextColor3 = if string.find(string.upper(modo), "RAID") then C.Peligro else C.Acento
	finTemporizador = if segundos then os.clock() + segundos else nil
	textoTiempo.Visible = segundos ~= nil
end

-- ===== Minimapa =====

local function construirMinimapa()
	local M = H.Minimapa
	minimapa = P.Marco(raizHUD, {
		Nombre = "Minimapa",
		Tamano = UDim2.fromOffset(M.Pequeno, M.Pequeno),
		Posicion = UDim2.new(1, -M.Margen, 0, M.Y),
		Ancla = Vector2.new(1, 0),
		Z = 10,
	})
	-- El disco es un CanvasGroup para recortar los puntos en círculo (UICorner 0,5).
	disco = P.Grupo(minimapa, { Nombre = "Disco", Color = C.Fondo3, Transparencia = 0.15, Z = 10 })
	P.Esquinas(disco, UDim.new(0.5, 0))
	P.Degradado(disco, ColorSequence.new(C.Fondo3, C.FondoProfundo), 90)
	-- Anillos de distancia.
	for _, r in { 0.33, 0.66 } do
		local anillo = P.Marco(disco, {
			Tamano = UDim2.fromScale(r, r),
			Posicion = UDim2.fromScale(0.5, 0.5),
			Ancla = Vector2.new(0.5, 0.5),
			Radio = UDim.new(0.5, 0),
			Z = 11,
		})
		P.Borde(anillo, C.Acento, 0.88)
	end
	-- Cono de visión de la cámara (siempre hacia arriba).
	local cono = P.Marco(disco, {
		Tamano = UDim2.fromScale(0.7, 0.42),
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 1),
		Color = C.Acento,
		Transparencia = 0,
		Z = 11,
	})
	P.Degradado(cono, ColorSequence.new(C.Acento), 90, NumberSequence.new(1, 0.82))
	capaPuntos = P.Marco(disco, { Nombre = "Puntos", Z = 12 })
	-- Tú: flecha cian en el centro.
	IconBuilder.Icono(
		disco,
		"ui_posicion",
		{ Tamano = 12, Color = C.Acento, Posicion = UDim2.fromScale(0.5, 0.5), Ancla = Vector2.new(0.5, 0.5), Z = 14 }
	)
	local borde = P.Marco(minimapa, { Nombre = "Borde", Radio = UDim.new(0.5, 0), Z = 13 })
	P.Borde(borde, C.Acento, 0.62, Theme.Tamanos.TrazoActivo)
	norte = P.Texto(minimapa, {
		Texto = "N",
		Tamano = Theme.Texto.Mini,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Acento,
		AlineacionX = Enum.TextXAlignment.Center,
		Caja = UDim2.fromOffset(12, 12),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 15,
	})
	norte.BackgroundColor3 = C.FondoProfundo
	norte.BackgroundTransparency = 0.1
	P.Esquinas(norte, UDim.new(0.5, 0))
	P.Borde(norte, C.Acento, A.BordeActivo)
	local pie = P.Marco(
		minimapa,
		{ Tamano = UDim2.fromOffset(0, 12), Posicion = UDim2.new(0.5, 0, 1, 4), Ancla = Vector2.new(0.5, 0), Z = 10 }
	)
	pie.AutomaticSize = Enum.AutomaticSize.X
	P.Lista(pie, Enum.FillDirection.Horizontal, 4, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)
	P.Tecla(pie, ConfigUI.Teclas.Mapa, { Z = 11 }).LayoutOrder = 1
	P.Texto(pie, {
		Texto = "AMPLIAR",
		Tamano = Theme.Texto.Micro + 0.5,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Espaciado = true,
		Contorno = true,
		Orden = 2,
		Z = 11,
	})
end

-- Punto reutilizable número `i` de la reserva.
local function puntoMinimapa(i: number): Frame
	local existente: Frame? = puntos[i]
	if existente then
		existente.Visible = true
		return existente
	end
	local nuevo = P.Marco(capaPuntos, {
		Tamano = UDim2.fromOffset(6, 6),
		Ancla = Vector2.new(0.5, 0.5),
		Color = C.Exito,
		Radio = UDim.new(0.5, 0),
		Z = 13,
	})
	P.Borde(nuevo, C.FondoProfundo, 0.2)
	puntos[i] = nuevo
	return nuevo
end

local function actualizarMinimapa()
	local camara = workspace.CurrentCamera
	local jugador = Players.LocalPlayer
	local personaje = jugador and jugador.Character
	local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
	if camara == nil or raiz == nil or not raiz:IsA("BasePart") then
		return
	end
	-- Ángulo de la cámara en el plano horizontal (0 = mirando al -Z, el "norte" del mapa).
	local mirada = camara.CFrame.LookVector
	local yaw = math.atan2(-mirada.X, -mirada.Z)
	local radioPx = minimapa.Size.X.Offset / 2
	local escala = (radioPx - 6) / H.Minimapa.RadioStuds
	local miBando = personaje and personaje:GetAttribute(ConfigCombate.AtributoBando)
	local n = 0
	local function pintar(posicion: Vector3, aliado: boolean)
		local d = posicion - raiz.Position
		-- Gira el desplazamiento para que la dirección de la cámara quede arriba.
		local x = d.X * math.cos(yaw) - d.Z * math.sin(yaw)
		local z = d.X * math.sin(yaw) + d.Z * math.cos(yaw)
		local plano = Vector2.new(x, z) * escala
		if plano.Magnitude > radioPx - 5 then
			return
		end
		n += 1
		local punto = puntoMinimapa(n)
		punto.Position = UDim2.new(0.5, plano.X, 0.5, plano.Y)
		punto.BackgroundColor3 = if aliado then C.Exito else C.Peligro
	end
	if ConfigUI.HUD.MinimapaJugadores then
		for _, otro in Players:GetPlayers() do
			local p = otro.Character
			local r = p and p:FindFirstChild("HumanoidRootPart")
			if otro ~= jugador and r and r:IsA("BasePart") then
				local bando = p and p:GetAttribute(ConfigCombate.AtributoBando)
				pintar(r.Position, bando ~= nil and bando == miBando)
			end
		end
	end
	if ConfigUI.HUD.MinimapaObjetivos then
		for _, modelo in CollectionService:GetTagged(ConfigCombate.EtiquetaObjetivo) do
			if modelo ~= personaje and modelo:IsA("Model") and Players:GetPlayerFromCharacter(modelo) == nil then
				local r = modelo:FindFirstChild("HumanoidRootPart")
				if r and r:IsA("BasePart") then
					local bando = modelo:GetAttribute(ConfigCombate.AtributoBando)
					pintar(r.Position, bando ~= nil and bando == miBando)
				end
			end
		end
	end
	for i = n + 1, #puntos do
		puntos[i].Visible = false
	end
	-- La N gira por el borde: el norte (-Z) visto desde la cámara.
	local angulo = -yaw - math.pi / 2
	norte.Position = UDim2.new(0.5, math.cos(angulo) * (radioPx - 1), 0.5, math.sin(angulo) * (radioPx - 1))
end

function HUDPartida.ToggleMinimap()
	minimapaGrande = not minimapaGrande
	local lado = if minimapaGrande then H.Minimapa.Grande else H.Minimapa.Pequeno
	UITweens.Tween(minimapa, Theme.Tweens.Normal, { Size = UDim2.fromOffset(lado, lado) })
end

-- Transparencia extra del minimapa (ajuste "Transparencia del minimapa", 0..0,8).
function HUDPartida.TransparenciaMinimapa(t: number)
	disco.GroupTransparency = math.clamp(t, 0, 0.9)
end

-- ===== Aviso de interacción (ProximityPrompt) =====

local function construirAviso()
	local I = H.Interaccion
	aviso = P.Crear("TextButton", {
		Name = "Interaccion",
		Text = "",
		AutoButtonColor = false,
		Size = UDim2.fromOffset(0, 28),
		AutomaticSize = Enum.AutomaticSize.X,
		ClipsDescendants = true,
		Position = UDim2.fromOffset(I.X, I.Y),
		BackgroundColor3 = C.FondoProfundo,
		BackgroundTransparency = 1,
		Visible = false,
		ZIndex = 12,
		Parent = raizHUD,
	}) :: TextButton
	P.Esquinas(aviso, UDim.new(0, 7))
	P.Borde(aviso, C.Acento, 1)
	-- Fila con la tecla y los textos (la barra de progreso va aparte, pegada abajo).
	local fila = P.Marco(aviso, { Nombre = "Fila", Tamano = UDim2.fromOffset(0, 28), Z = 13 })
	fila.AutomaticSize = Enum.AutomaticSize.X
	P.Relleno(fila, 5, 10, 5, 5)
	P.Lista(fila, Enum.FillDirection.Horizontal, 7, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	avisoTecla = P.Texto(fila, {
		Texto = "E",
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.TextoSobreAcento,
		AlineacionX = Enum.TextXAlignment.Center,
		Orden = 1,
		Z = 13,
	})
	avisoTecla.AutomaticSize = Enum.AutomaticSize.X
	avisoTecla.Size = UDim2.fromOffset(18, 18)
	avisoTecla.BackgroundColor3 = C.Acento
	avisoTecla.BackgroundTransparency = 0
	P.Esquinas(avisoTecla, UDim.new(0, 3))
	P.Relleno(avisoTecla, 0, 4)
	local textos = P.Marco(fila, { Tamano = UDim2.fromOffset(0, 20), Orden = 2, Z = 13 })
	textos.AutomaticSize = Enum.AutomaticSize.X
	avisoTexto = P.Texto(textos, { Texto = "", Tamano = Theme.Texto.Cuerpo, Fuente = Theme.Fuentes.Negrita, Z = 13 })
	avisoSub = P.Texto(textos, {
		Texto = "",
		Tamano = Theme.Texto.Mini,
		Fuente = Theme.Fuentes.Medio,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Posicion = UDim2.fromOffset(0, 12),
		Z = 13,
	})
	-- Progreso de mantener pulsado (prompts con HoldDuration).
	avisoBarra = P.Marco(aviso, {
		Nombre = "Progreso",
		Tamano = UDim2.new(0, 0, 0, 2),
		Posicion = UDim2.fromScale(0, 1),
		Ancla = Vector2.new(0, 1),
		Color = C.Acento,
		Z = 14,
	})
	-- Toque/clic: mantiene pulsado el prompt (móvil).
	aviso.MouseButton1Down:Connect(function()
		local p = promptActual
		if p then
			p:InputHoldBegin()
		end
	end)
	aviso.MouseButton1Up:Connect(function()
		local p = promptActual
		if p then
			p:InputHoldEnd()
		end
	end)
end

local function mostrarAviso(prompt: ProximityPrompt?)
	promptActual = prompt
	if prompt then
		local tecla = if UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
			then "TOCA"
			else prompt.KeyboardKeyCode.Name
		avisoTecla.Text = tecla
		avisoTexto.Text = prompt.ActionText
		avisoSub.Text = prompt.ObjectText
		avisoSub.Visible = prompt.ObjectText ~= ""
		avisoTexto.Position = UDim2.fromOffset(0, if prompt.ObjectText ~= "" then 0 else 5)
		avisoBarra.Size = UDim2.new(0, 0, 0, 2)
		aviso.Visible = true
		UITweens.Tween(aviso, Theme.Tweens.Fundido, { BackgroundTransparency = A.HUDFondo })
		local borde = aviso:FindFirstChildOfClass("UIStroke")
		if borde then
			UITweens.Tween(borde, Theme.Tweens.Fundido, { Transparency = A.BordeActivo })
		end
	else
		local borde = aviso:FindFirstChildOfClass("UIStroke")
		if borde then
			UITweens.Tween(borde, Theme.Tweens.Fundido, { Transparency = 1 })
		end
		local t = UITweens.Tween(aviso, Theme.Tweens.Fundido, { BackgroundTransparency = 1 })
		t.Completed:Once(function()
			if promptActual == nil then
				aviso.Visible = false
			end
		end)
	end
end

local function conectarPrompts()
	ProximityPromptService.PromptShown:Connect(function(prompt)
		if not ConfigUI.AvisoInteraccionPropio then
			return
		end
		-- Se dibuja con el aviso del HUD en lugar del de Roblox (solo en este cliente).
		prompt.Style = Enum.ProximityPromptStyle.Custom
		mostrarAviso(prompt)
	end)
	ProximityPromptService.PromptHidden:Connect(function(prompt)
		if promptActual == prompt then
			mostrarAviso(nil)
		end
	end)
	ProximityPromptService.PromptButtonHoldBegan:Connect(function(prompt)
		if prompt == promptActual and prompt.HoldDuration > 0 then
			avisoBarra.Size = UDim2.new(0, 0, 0, 2)
			UITweens.Tween(
				avisoBarra,
				TweenInfo.new(prompt.HoldDuration, Enum.EasingStyle.Linear),
				{ Size = UDim2.new(1, 0, 0, 2) }
			)
		end
	end)
	ProximityPromptService.PromptButtonHoldEnded:Connect(function(prompt)
		if prompt == promptActual then
			UITweens.Tween(avisoBarra, Theme.Tweens.Rapido, { Size = UDim2.new(0, 0, 0, 2) })
		end
	end)
end

-- ===== Armas =====

local function construirArmas()
	local W = H.Armas
	local marco = P.Marco(raizHUD, {
		Nombre = "Armas",
		Tamano = UDim2.fromOffset(W.Lado * 2 + 8, W.Lado + 16),
		Posicion = UDim2.new(0, W.X, 1, -W.Margen),
		Ancla = Vector2.new(0, 1),
		Z = 10,
	})
	nombreArma = P.Texto(marco, {
		Texto = "",
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Espada,
		Espaciado = true,
		Contorno = true,
		Z = 10,
	})
	for i, slot in { "Espada", "Arma" } do
		local casilla = P.Marco(marco, {
			Nombre = slot,
			Tamano = UDim2.fromOffset(W.Lado, W.Lado),
			Posicion = UDim2.new(0, (i - 1) * (W.Lado + 8), 1, 0),
			Ancla = Vector2.new(0, 1),
			Color = C.FondoProfundo,
			Transparencia = A.HUDFondo,
			Radio = UDim.new(0, 9),
			Z = 10,
		})
		P.Borde(casilla, C.Blanco, 0.88, Theme.Tamanos.TrazoActivo)
		P.Tecla(casilla, tostring(i), { Posicion = UDim2.fromOffset(3, 3), Z = 13 })
		local boton = P.Crear("TextButton", {
			Name = "Pulsar",
			Text = "",
			BackgroundTransparency = 1,
			Size = UDim2.fromScale(1, 1),
			ZIndex = 14,
			Parent = casilla,
		}) :: TextButton
		boton.Activated:Connect(function()
			HUDPartida.CambiarArma(i)
		end)
		table.insert(slotsArma, casilla)
	end
end

local function pintarArmas()
	local equipado = EstadoUI.Equipado()
	for i, casilla in slotsArma do
		local slot = if i == 1 then "Espada" else "Arma"
		local viejo = casilla:FindFirstChild("Imagen")
		if viejo then
			viejo:Destroy()
		end
		local id = equipado[slot]
		local objeto = if id then EstadoUI.Objeto(id) else nil
		local imagen = if objeto
			then IconBuilder.Arte(casilla, objeto.Arte, {
				Nombre = "Imagen",
				Tamano = UDim2.new(1, -12, 1, -12),
				Posicion = UDim2.fromScale(0.5, 0.5),
				Ancla = Vector2.new(0.5, 0.5),
				Z = 11,
			})
			else IconBuilder.Icono(casilla, if i == 1 then "slot_espada" else "slot_arma", {
				Nombre = "Imagen",
				Tamano = 26,
				Color = C.Gris,
				Posicion = UDim2.fromScale(0.5, 0.5),
				Ancla = Vector2.new(0.5, 0.5),
				Z = 11,
			})
		local activa = i == armaActiva
		imagen.ImageTransparency = if activa then 0 else A.Arma_Inactiva
		casilla.BackgroundTransparency = if activa then 0.15 else 0.5
		casilla.BackgroundColor3 = if activa then C.Fondo3 else C.FondoProfundo
		local borde = casilla:FindFirstChildOfClass("UIStroke")
		if borde then
			borde.Color = if activa then C.Acento else C.Blanco
			borde.Transparency = if activa then 0 else 0.88
			borde.Thickness = if activa then Theme.Tamanos.TrazoGrueso else Theme.Tamanos.TrazoActivo
		end
		if activa then
			nombreArma.Text = P.Espaciar(
				string.upper(if objeto then objeto.Nombre elseif i == 1 then "Cuerpo a cuerpo" else "Sin arma")
			)
			nombreArma.TextColor3 = if i == 1 then C.Espada else C.Fuerza
		end
	end
end

function HUDPartida.CambiarArma(n: number)
	if n ~= armaActiva and (n == 1 or n == 2) then
		armaActiva = n
		pintarArmas()
		UITweens.Destello(slotsArma[n], 1.08)
		HUDPartida.ArmaCambiada:Disparar(n)
	end
end

-- ===== Habilidades =====

-- Media "porción" de reloj: un marco que recorta una mitad y un círculo oscuro con un degradado de borde duro.
local function mitadReloj(padre: Instance, derecha: boolean): (Frame, UIGradient)
	local mitad = P.Marco(padre, {
		Nombre = if derecha then "MitadDer" else "MitadIzq",
		Tamano = UDim2.fromScale(0.5, 1),
		Posicion = UDim2.fromScale(if derecha then 0.5 else 0, 0),
		Recortar = true,
		Z = 14,
	})
	local circulo = P.Marco(mitad, {
		Nombre = "Velo",
		Tamano = UDim2.fromScale(2, 1),
		Posicion = UDim2.fromScale(if derecha then -1 else 0, 0),
		Color = C.FondoNegro,
		Transparencia = A.Cooldown,
		Radio = UDim.new(0.5, 0),
		Z = 14,
	})
	local degradado = P.Degradado(
		circulo,
		ColorSequence.new(C.FondoNegro),
		0,
		NumberSequence.new({
			NumberSequenceKeypoint.new(0, 0),
			NumberSequenceKeypoint.new(0.499, 0),
			NumberSequenceKeypoint.new(0.5, 1),
			NumberSequenceKeypoint.new(1, 1),
		})
	)
	return circulo, degradado
end

-- Pinta el velo del cooldown: `restante` (0..1) de la vuelta sigue oscura, vaciándose en el sentido del reloj desde las 12.
local function pintarReloj(c: CasillaHabilidad, restante: number)
	if restante <= 0 then
		c.CirculoIzq.Visible = false
		c.CirculoDer.Visible = false
		return
	end
	local theta = (1 - math.clamp(restante, 0, 1)) * 360
	-- Mitad derecha (0°-180°): oscura de theta a 180. Mitad izquierda (180°-360°): oscura de max(theta, 180) a 360.
	c.CirculoDer.Visible = theta < 180
	c.MitadDer.Rotation = theta - 180
	c.CirculoIzq.Visible = true
	c.MitadIzq.Rotation = if theta < 180 then 0 else theta - 180
end

local function construirHabilidades()
	local Hb = H.Habilidades
	local fila = P.Marco(raizHUD, {
		Nombre = "Habilidades",
		Tamano = UDim2.fromOffset(0, Hb.LadoDefinitiva + 14),
		Posicion = UDim2.new(0.5, 0, 1, -Hb.Margen),
		Ancla = Vector2.new(0.5, 1),
		Z = 10,
	})
	fila.AutomaticSize = Enum.AutomaticSize.X
	P.Lista(
		fila,
		Enum.FillDirection.Horizontal,
		Hb.Separacion,
		Enum.HorizontalAlignment.Center,
		Enum.VerticalAlignment.Bottom
	)
	for i, id in ConfigUI.HUD.Habilidades do
		local hab = EstadoUI.Habilidad(id)
		if hab then
			local definitiva = hab.Categoria == "Definitiva"
			local lado = if definitiva then Hb.LadoDefinitiva else Hb.Lado
			local color = if definitiva then C.Dorado else C.Acento
			local marco =
				P.Marco(fila, { Nombre = id, Tamano = UDim2.fromOffset(lado + 30, lado + 14), Orden = i, Z = 10 })
			local circulo = P.Crear("TextButton", {
				Name = "Circulo",
				Text = "",
				AutoButtonColor = false,
				Size = UDim2.fromOffset(lado, lado),
				Position = UDim2.new(0.5, 0, 0, 0),
				AnchorPoint = Vector2.new(0.5, 0),
				BackgroundColor3 = C.Fondo3,
				ZIndex = 11,
				Parent = marco,
			}) :: TextButton
			P.Esquinas(circulo, UDim.new(0.5, 0))
			P.Degradado(circulo, ColorSequence.new(C.Fondo3:Lerp(C.Acento, 0.08), C.FondoProfundo), 90)
			local halo = P.Borde(circulo, color, 0.55, Theme.Tamanos.TrazoGrueso)
			local icono = IconBuilder.Icono(circulo, ConfigUI.HUD.IconosHabilidad[id] or "stat_habilidad", {
				Tamano = if definitiva then 28 else 24,
				Color = color,
				Posicion = UDim2.fromScale(0.5, 0.5),
				Ancla = Vector2.new(0.5, 0.5),
				Z = 12,
			})
			local circuloIzq, mitadIzq = mitadReloj(circulo, false)
			local circuloDer, mitadDer = mitadReloj(circulo, true)
			local tiempo = P.Texto(circulo, {
				Texto = "",
				Tamano = Theme.Texto.Grande,
				Fuente = Theme.Fuentes.Negrita,
				Posicion = UDim2.fromScale(0.5, 0.5),
				Ancla = Vector2.new(0.5, 0.5),
				Contorno = true,
				Z = 16,
			})
			local tecla = if hab.Tecla == "Click" then "CLIC" else hab.Tecla
			P.Tecla(marco, tecla, { Posicion = UDim2.new(0.5, 0, 0, -5), Ancla = Vector2.new(0.5, 0), Z = 17 })
			local pie = P.Texto(marco, {
				Texto = hab.Nombre,
				Tamano = Theme.Texto.Mini,
				Fuente = Theme.Fuentes.Titulo,
				Color = C.TextoPrincipal,
				Transparencia = A.TextoSecundario,
				Posicion = UDim2.new(0.5, 0, 1, 0),
				Ancla = Vector2.new(0.5, 1),
				Contorno = true,
				Z = 11,
			})
			local casilla: CasillaHabilidad = {
				Id = id,
				Marco = marco,
				Circulo = circulo,
				Icono = icono,
				Halo = halo,
				MitadIzq = mitadIzq,
				MitadDer = mitadDer,
				CirculoIzq = circuloIzq,
				CirculoDer = circuloDer,
				Tiempo = tiempo,
				Pie = pie,
				Nombre = hab.Nombre,
				Coste = hab.Energia,
				EnCooldown = false,
				UltimoTexto = "",
			}
			pintarReloj(casilla, 0)
			-- Lista para usar: el borde brilla suavemente.
			UITweens.Pulso(halo, "Transparency", 0.55, 0.05, Theme.Tweens.PulsoLento)
			UITweens.Hover(circulo)
			circulo.Activated:Connect(function()
				solicitar(id)
			end)
			table.insert(casillas, casilla)
		end
	end
end

local function actualizarHabilidades()
	local energia = EstadoUI.EnergiaActual()
	local combate = EstadoUI.Combate()
	barraEnergia.Poner(energia, combate.EnergiaMax, true)
	for _, c in casillas do
		local restante, total = EstadoUI.Cooldown(c.Id)
		local enCooldown = restante > 0
		pintarReloj(c, if enCooldown then restante / math.max(total, 0.01) else 0)
		local texto = if enCooldown
			then (if restante >= 10 then `{math.ceil(restante)}s` else `{string.format("%.1f", restante)}s`)
			else ""
		if texto ~= c.UltimoTexto then
			c.UltimoTexto = texto
			c.Tiempo.Text = texto
			c.Pie.Text = if enCooldown then texto else c.Nombre
			c.Pie.TextTransparency = if enCooldown then 0 else A.TextoSecundario
		end
		if c.EnCooldown and not enCooldown then
			-- Se acaba de recargar: destello.
			UITweens.Destello(c.Circulo, 1.15)
		end
		c.EnCooldown = enCooldown
		-- Sin energía suficiente, el icono se apaga.
		c.Icono.ImageTransparency = if energia + 1e-6 < c.Coste then 0.55 else 0
	end
	if finTemporizador then
		local segundos = math.max(0, finTemporizador - os.clock())
		local t = P.MinSeg(segundos)
		if textoTiempo.Text ~= t then
			textoTiempo.Text = t
			textoTiempo.TextColor3 = if segundos <= 30 then C.PeligroClaro else C.TextoPrincipal
		end
	end
end

-- ===== Estadísticas rápidas =====

local function construirRapidas()
	local marco = P.Marco(raizHUD, {
		Nombre = "Rapidas",
		Tamano = UDim2.fromOffset(0, 46),
		Posicion = UDim2.new(1, -H.Rapidas.Margen, 1, -16),
		Ancla = Vector2.new(1, 1),
		Color = C.FondoProfundo,
		Transparencia = 0.45,
		Radio = Theme.Tamanos.BorderRadius,
		Z = 10,
	})
	marco.AutomaticSize = Enum.AutomaticSize.X
	P.Borde(marco, C.Acento, A.BordeSutil)
	P.Relleno(marco, 6, 10)
	P.Lista(marco, Enum.FillDirection.Horizontal, 12, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)
	for i, r in DatosDemo.Rapidas do
		local info = Theme.Stats[r.Stat]
		local columna = P.Marco(marco, { Tamano = UDim2.fromOffset(30, 34), Orden = i, Z = 11 })
		P.Lista(columna, Enum.FillDirection.Vertical, 0, Enum.HorizontalAlignment.Center)
		IconBuilder.Icono(columna, info.Icono, { Tamano = 9, Color = info.Color, Orden = 1, Z = 12 })
		P.Texto(columna, {
			Texto = r.Etiqueta,
			Tamano = Theme.Texto.Micro + 0.5,
			Fuente = Theme.Fuentes.Negrita,
			Color = C.TextoSecundario,
			Transparencia = A.TextoSecundario,
			Orden = 2,
			Z = 12,
		})
		P.Texto(columna, {
			Texto = P.Decimal(r.Valor),
			Tamano = Theme.Texto.Medio,
			Fuente = Theme.Fuentes.Negrita,
			Orden = 3,
			Z = 12,
		})
		P.Texto(columna, {
			Texto = `+{P.Decimal(r.Bonus)}`,
			Tamano = Theme.Texto.Micro + 0.5,
			Fuente = Theme.Fuentes.Negrita,
			Color = info.Color,
			Orden = 4,
			Z = 12,
		})
	end
end

-- ===== API =====

--[[
	Construye el HUD dentro de `raiz` (el lienzo). `alSolicitar(id)` se llama al tocar una casilla de habilidad (lo
	conecta el controlador con ServicioCombate.Solicitar, que pide la habilidad al servidor).
]]
function HUDPartida.Iniciar(raiz: Frame, alSolicitar: (id: string) -> ())
	solicitar = alSolicitar
	local marco, cambiar = Lienzo.SubEscala(raiz, "HUD")
	marco.ZIndex = 10
	raizHUD = marco
	cambiarEscala = cambiar

	construirVitales()
	construirInfo()
	construirMinimapa()
	construirAviso()
	construirArmas()
	construirHabilidades()
	construirRapidas()
	HUDPartida.PonerInfo(ConfigUI.HUD.SectorInicial, ConfigUI.HUD.ModoInicial)

	-- Escudo personal: de demostración hasta que exista.
	barraEscudo.Poner(DatosDemo.Escudo[1], DatosDemo.Escudo[2], true)
	textoEscudo.Text = texto2(DatosDemo.Escudo[1], DatosDemo.Escudo[2])

	local jugador = Players.LocalPlayer
	if jugador.Character then
		task.spawn(seguirPersonaje, jugador.Character)
	end
	jugador.CharacterAdded:Connect(seguirPersonaje)

	pintarArmas()
	EstadoUI.Cambio:Conectar(function(que: string)
		if que == "Equipo" then
			pintarArmas()
		end
	end)
	conectarPrompts()

	-- Un solo bucle por fotograma para cooldowns y energía, y el minimapa a 15 Hz. Nada corre con el HUD oculto.
	local acumulado = 0
	RunService.RenderStepped:Connect(function(dt)
		if not visible then
			return
		end
		actualizarHabilidades()
		acumulado += dt
		if acumulado >= 1 / H.Minimapa.Hz then
			acumulado = 0
			actualizarMinimapa()
		end
	end)
end

-- Fundido de entrada (0,2 s).
function HUDPartida.Mostrar()
	if visible then
		return
	end
	visible = true
	UITweens.FundirMarco(raizHUD, true)
end

-- Fundido de salida (0,2 s), al abrir un menú o al subir a una nave.
function HUDPartida.Ocultar()
	if not visible then
		return
	end
	visible = false
	if promptActual then
		mostrarAviso(nil)
	end
	UITweens.FundirMarco(raizHUD, false)
end

-- Ajuste "Tamaño del HUD" (1 = 100 %).
function HUDPartida.Escalar(k: number)
	cambiarEscala(k)
end

return HUDPartida
