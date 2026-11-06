--!strict
--[[
	Persianas (cliente): anima la persiana de cada tienda cuando el servidor la sube o la baja.

	El servidor solo publica el estado en el atributo Config.AtributoPersiana del modelo; aquí se convierte en la
	animación completa (Tiendas/Persiana da la curva y Tiendas/Datos/Persiana todos los números):

	  BAJAR   alarma y baliza roja, la persiana asoma y se suelta, cae acelerando, se clava en el suelo (hitstop) con
	          polvo, chispas, golpe y temblor de cámara, rebota, y el cartel pasa a "CERRADO".
	  SUBIR   cerrojo, tiembla al soltarse, sube suave, se asienta en el cajón y el cartel vuelve a "ABIERTO".

	Rendimiento (móvil):
	  - Las lamas se mueven todas de golpe con workspace:BulkMoveTo, y solo mientras hay una animación en marcha.
	  - Cada tienda crea UNA vez sus emisores de partículas y sus sonidos y los reutiliza (Emit / Play).
	  - Las partículas se multiplican por el factor de calidad del dispositivo.
	  - La baliza solo late si la tienda está cerca de la cámara.
	  - Las tiendas que entran y salen por streaming se registran y se sueltan solas; al entrar se colocan en su estado
	    actual sin animación.

	Las piezas las construye el servidor (Servicios/ServicioTiendas/Modelo) en la posición de CERRADA; este módulo las
	desplaza hacia arriba a lo largo del eje vertical de `Origen` y oculta las que quedan dentro del cajón.
]]

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Compras = require(Shared.Tiendas.Compras)
local Config = require(Shared.Tiendas.Config)
local Curvas = require(Shared.Tiendas.Persiana)
local DatosPersiana = require(Shared.Tiendas.Datos.Persiana)
local Recursos = require(Shared.Combate.Datos.Recursos)
local Avisos = require(script.Parent.Parent.Exploracion.Avisos)
local Calidad = require(script.Parent.Parent.VFX.Calidad)
local Pantalla = require(script.Parent.Parent.VFX.Pantalla)
local Utiles = require(script.Parent.Parent.VFX.Utiles)
local ServicioDatos = require(script.Parent.Parent.Servicios.ServicioDatos)

type Pieza = {
	Parte: BasePart,
	Local: CFrame, -- respecto a Origen, con la persiana CERRADA
	Inferior: number, -- altura (respecto a Origen) de su borde inferior, con la persiana CERRADA
	Gui: SurfaceGui?, -- el rótulo pintado se muestra con su SurfaceGui, no con la transparencia
	TransparenciaVisible: number,
	Visible: boolean?,
}

type Animacion = {
	Tipo: Curvas.Tipo,
	Inicio: number,
	Desde: number, -- cierre en el que estaba al empezar (si interrumpe a otra animación)
	Eventos: { [string]: boolean }, -- eventos ya disparados
}

type Tienda = {
	Modelo: Model,
	Origen: BasePart,
	Piezas: { Pieza },
	Partes: { BasePart }, -- las mismas piezas, en una lista para BulkMoveTo
	Recorrido: number,
	AlturaCajon: number,
	Cierre: number, -- posición actual (0 = recogida, 1 = en el suelo)
	Bajada: boolean,
	Animacion: Animacion?,
	Baliza: BasePart?,
	LuzBaliza: PointLight?,
	ColorBalizaApagada: Color3?,
	Estado: TextLabel?,
	Polvo: ParticleEmitter?,
	Chispas: ParticleEmitter?,
	Sonidos: { [string]: Sound },
	Conexiones: { RBXScriptConnection },
	DestelloHasta: number,
}

local Persianas = {}

local tiendas: { [Model]: Tienda } = {}
local conexionBucle: RBXScriptConnection? = nil
local iniciado = false

local COLOR_ABIERTO = Utiles.Hex(DatosPersiana.Colores.Abierto)
local COLOR_CERRADO = Utiles.Hex(DatosPersiana.Colores.Cerrado)

-- ===== Preparación de cada tienda =====

local function crearSonidos(padre: Instance): { [string]: Sound }
	local sonidos: { [string]: Sound } = {}
	for nombre, datos in DatosPersiana.Sonidos :: any do
		if type(datos) == "table" and datos.Id ~= "" then
			-- Si la tienda vuelve a entrar tras salir del mundo, se reutilizan los que ya tenía.
			local existente = padre:FindFirstChild(`Persiana{nombre}`)
			local sonido = if existente and existente:IsA("Sound") then existente else Instance.new("Sound")
			sonido.Name = `Persiana{nombre}`
			sonido.SoundId = datos.Id
			sonido.Volume = datos.Volumen
			sonido.PlaybackSpeed = datos.Velocidad
			sonido.RollOffMaxDistance = DatosPersiana.Sonidos.DistanciaMaxima
			sonido.RollOffMinDistance = 10
			sonido.Parent = padre
			sonidos[nombre] = sonido
		end
	end
	return sonidos
end

-- Emisores del impacto: se crean apagados (Rate 0) y se disparan con Emit.
local function crearEmisores(zona: BasePart): (ParticleEmitter, ParticleEmitter)
	local polvoExistente = zona:FindFirstChild("PolvoPersiana")
	local chispasExistentes = zona:FindFirstChild("ChispasPersiana")
	if
		polvoExistente
		and polvoExistente:IsA("ParticleEmitter")
		and chispasExistentes
		and chispasExistentes:IsA("ParticleEmitter")
	then
		return polvoExistente, chispasExistentes
	end

	local polvo = Instance.new("ParticleEmitter")
	polvo.Name = "PolvoPersiana"
	polvo.Texture = Recursos.Texturas.Polvo
	polvo.Color = ColorSequence.new(Utiles.Hex(DatosPersiana.Colores.Polvo))
	polvo.Rate = 0
	polvo.Enabled = true
	polvo.Lifetime = NumberRange.new(0.7, 1.4)
	polvo.Speed = NumberRange.new(5, 11)
	polvo.SpreadAngle = Vector2.new(70, 15)
	polvo.EmissionDirection = Enum.NormalId.Front -- hacia la calle
	polvo.Shape = Enum.ParticleEmitterShape.Box
	polvo.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	polvo.Drag = 3.5
	polvo.Acceleration = Vector3.new(0, 2.5, 0)
	polvo.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1.2),
		NumberSequenceKeypoint.new(1, 4.2),
	})
	polvo.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.45),
		NumberSequenceKeypoint.new(1, 1),
	})
	polvo.Rotation = NumberRange.new(0, 360)
	polvo.RotSpeed = NumberRange.new(-40, 40)
	polvo.Parent = zona

	local chispas = Instance.new("ParticleEmitter")
	chispas.Name = "ChispasPersiana"
	chispas.Texture = Recursos.Texturas.Chispa
	chispas.Color = ColorSequence.new(Utiles.Hex(DatosPersiana.Colores.Chispas))
	chispas.LightEmission = 1
	chispas.Rate = 0
	chispas.Lifetime = NumberRange.new(0.25, 0.55)
	chispas.Speed = NumberRange.new(12, 24)
	chispas.SpreadAngle = Vector2.new(65, 65)
	chispas.EmissionDirection = Enum.NormalId.Top
	chispas.Shape = Enum.ParticleEmitterShape.Box
	chispas.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	chispas.Acceleration = Vector3.new(0, -70, 0)
	chispas.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.32),
		NumberSequenceKeypoint.new(1, 0),
	})
	chispas.Parent = zona
	return polvo, chispas
end

local function sonar(tienda: Tienda, nombre: string)
	local sonido = tienda.Sonidos[nombre]
	if sonido then
		sonido.TimePosition = 0
		sonido:Play()
	end
end

-- Cartel ABIERTO / CERRADO.
local function pintarEstado(tienda: Tienda, cerrado: boolean)
	local etiqueta = tienda.Estado
	if etiqueta then
		etiqueta.Text = if cerrado then DatosPersiana.Textos.Cerrado else DatosPersiana.Textos.Abierto
		etiqueta.TextColor3 = if cerrado then COLOR_CERRADO else COLOR_ABIERTO
	end
end

-- Enciende o apaga la baliza (el latido lo hace el bucle).
local function pintarBaliza(tienda: Tienda, encendida: boolean)
	local baliza, luz = tienda.Baliza, tienda.LuzBaliza
	if baliza then
		baliza.Material = if encendida then Enum.Material.Neon else Enum.Material.Glass
		baliza.Color = if encendida then COLOR_CERRADO else (tienda.ColorBalizaApagada or baliza.Color)
	end
	if luz then
		luz.Enabled = encendida and Calidad.Factor("Luces") > 0
	end
end

-- Coloca la persiana con un cierre dado (0 = recogida, 1 = en el suelo).
local function colocar(tienda: Tienda, cierre: number)
	tienda.Cierre = cierre
	local desplazamiento = (1 - cierre) * tienda.Recorrido
	local base = tienda.Origen.CFrame * CFrame.new(0, desplazamiento, 0)
	local destinos: { CFrame } = table.create(#tienda.Piezas)
	for indice, pieza in tienda.Piezas do
		destinos[indice] = base * pieza.Local
		-- Visible mientras su borde inferior quede por debajo del cajón; si no, está recogida dentro.
		local visible = pieza.Inferior + desplazamiento < tienda.AlturaCajon - 1e-3
		if pieza.Visible ~= visible then
			pieza.Visible = visible
			if pieza.Gui then
				pieza.Gui.Enabled = visible
			else
				pieza.Parte.Transparency = if visible then pieza.TransparenciaVisible else 1
			end
		end
	end
	workspace:BulkMoveTo(tienda.Partes, destinos, Enum.BulkMoveMode.FireCFrameChanged)
end

local function soltar(modelo: Model)
	local tienda = tiendas[modelo]
	if tienda == nil then
		return
	end
	tiendas[modelo] = nil
	for _, conexion in tienda.Conexiones do
		conexion:Disconnect()
	end
end

-- ===== Bucle de animación =====

local function camaraCerca(tienda: Tienda): boolean
	local camara = workspace.CurrentCamera
	return camara ~= nil
		and (camara.CFrame.Position - tienda.Origen.Position).Magnitude <= DatosPersiana.DistanciaAnimacion
end

-- Dispara los eventos de una animación al llegar su momento (cada uno una sola vez).
local function eventos(tienda: Tienda, animacion: Animacion, transcurrido: number, ahora: number)
	local t = DatosPersiana.Tiempos
	local hechos = animacion.Eventos
	if animacion.Tipo == "Cierre" then
		if not hechos.Caida and transcurrido >= t.Anticipacion then
			hechos.Caida = true
			sonar(tienda, "Bajada")
		end
		if not hechos.Impacto and transcurrido >= Curvas.InstanteImpacto() then
			hechos.Impacto = true
			local bajada = tienda.Sonidos.Bajada
			if bajada then
				bajada:Stop()
			end
			sonar(tienda, "Golpe")
			local factor = Calidad.Factor("Particulas")
			local impacto = DatosPersiana.Impacto
			if tienda.Polvo then
				tienda.Polvo:Emit(Utiles.Cantidad(impacto.Polvo, factor))
			end
			if tienda.Chispas then
				tienda.Chispas:Emit(Utiles.Cantidad(impacto.Chispas, factor))
			end
			Pantalla.Sacudida(impacto.Sacudida, tienda.Origen.Position)
			tienda.DestelloHasta = ahora + impacto.DestelloBaliza
			pintarEstado(tienda, true)
		end
	else
		if not hechos.Subida and transcurrido >= t.Desbloqueo then
			hechos.Subida = true
			sonar(tienda, "Subida")
			pintarBaliza(tienda, false)
		end
	end
end

-- Late la baliza mientras la persiana está bajada (más fuerte un instante tras el golpe).
local function latirBaliza(tienda: Tienda, ahora: number)
	local luz = tienda.LuzBaliza
	if luz == nil or not luz.Enabled then
		return
	end
	local datos = DatosPersiana.Baliza
	local latido = (math.sin(ahora * math.pi * 2 * datos.LatidosPorSegundo) + 1) / 2
	luz.Brightness = if ahora < tienda.DestelloHasta
		then datos.BrilloMax * 1.6
		else datos.BrilloMin + (datos.BrilloMax - datos.BrilloMin) * latido
end

local function paso()
	local ahora = os.clock()
	local activa = false
	for _, tienda in tiendas do
		local animacion = tienda.Animacion
		if animacion then
			activa = true
			local transcurrido = ahora - animacion.Inicio
			eventos(tienda, animacion, transcurrido, ahora)
			local curva = Curvas.Valor(animacion.Tipo, transcurrido)
			-- Si interrumpe a otra animación, la curva se estira para empezar donde estaba la persiana.
			local cierre = if animacion.Tipo == "Cierre"
				then animacion.Desde + curva * (1 - animacion.Desde)
				else curva * animacion.Desde
			colocar(tienda, cierre)
			if transcurrido >= Curvas.Duracion(animacion.Tipo) then
				tienda.Animacion = nil
				if animacion.Tipo == "Apertura" then
					pintarEstado(tienda, false)
				end
			end
		end
		if tienda.Bajada and camaraCerca(tienda) then
			activa = true
			latirBaliza(tienda, ahora)
		end
	end
	if not activa and conexionBucle then
		conexionBucle:Disconnect()
		conexionBucle = nil
	end
end

local function asegurarBucle()
	if conexionBucle == nil then
		conexionBucle = RunService.RenderStepped:Connect(paso)
	end
end

-- ===== Cambios de estado =====

-- Avisa al jugador local si es un monstruo y la persiana le acaba de bajar en las narices.
local function avisarSiEsMonstruo(tienda: Tienda)
	local datos = ServicioDatos.Obtener()
	local personaje = Players.LocalPlayer.Character
	local raiz = if personaje then personaje:FindFirstChild("HumanoidRootPart") else nil
	if datos == nil or not Compras.EsVetado(datos.Bando) or raiz == nil or not raiz:IsA("BasePart") then
		return
	end
	if (raiz.Position - tienda.Origen.Position).Magnitude <= Config.RadioApertura then
		Avisos.Mostrar("Los humanos te bajan la persiana: aquí no se vende a monstruos", "Mal")
	end
end

local function alCambiar(tienda: Tienda)
	local bajada = tienda.Modelo:GetAttribute(Config.AtributoPersiana) == true
	if bajada == tienda.Bajada then
		return
	end
	tienda.Bajada = bajada
	tienda.Animacion = {
		Tipo = (if bajada then "Cierre" else "Apertura") :: Curvas.Tipo,
		Inicio = os.clock(),
		Desde = tienda.Cierre,
		Eventos = {},
	}
	if bajada then
		sonar(tienda, "Alarma")
		pintarBaliza(tienda, true)
		avisarSiEsMonstruo(tienda)
	else
		sonar(tienda, "Cerrojo")
	end
	asegurarBucle()
end

-- ===== Registro =====

local function registrar(instancia: Instance)
	if not instancia:IsA("Model") or tiendas[instancia] ~= nil then
		return
	end
	local modelo = instancia :: Model
	-- Con streaming atómico las piezas llegan juntas, pero se espera un poco por si acaso.
	local origen = modelo:WaitForChild("Origen", 5)
	local cortina = modelo:WaitForChild("Cortina", 5)
	if origen == nil or cortina == nil or not origen:IsA("BasePart") or tiendas[modelo] ~= nil then
		return
	end
	if not modelo:IsDescendantOf(workspace) then
		return -- salió del streaming mientras se esperaba
	end

	local base = (origen :: BasePart).CFrame
	local piezas: { Pieza } = {}
	local partes: { BasePart } = {}
	for _, hijo in cortina:GetChildren() do
		if hijo:IsA("BasePart") then
			local gui = hijo:FindFirstChildOfClass("SurfaceGui")
			local relativo = base:ToObjectSpace(hijo.CFrame)
			table.insert(piezas, {
				Parte = hijo,
				Local = relativo,
				Inferior = relativo.Position.Y - hijo.Size.Y / 2,
				Gui = if hijo.Name == "Rotulo" then gui else nil,
				TransparenciaVisible = if hijo.Name == "Rotulo" then 1 else 0,
				Visible = nil,
			})
			table.insert(partes, hijo)
		end
	end

	local zona = modelo:FindFirstChild("ZonaPolvo")
	local cajon = modelo:FindFirstChild("Cajon")
	local baliza = modelo:FindFirstChild("Baliza")
	local estado = modelo:FindFirstChild("Estado")
	local etiqueta = if estado then estado:FindFirstChild("Etiqueta", true) else nil
	local polvo, chispas = nil, nil
	if zona and zona:IsA("BasePart") then
		polvo, chispas = crearEmisores(zona)
	end

	local tienda: Tienda = {
		Modelo = modelo,
		Origen = origen :: BasePart,
		Piezas = piezas,
		Partes = partes,
		Recorrido = (cortina:GetAttribute("Recorrido") :: number?) or DatosPersiana.Medidas.AltoHueco,
		AlturaCajon = (cortina:GetAttribute("AlturaCajon") :: number?) or DatosPersiana.Medidas.AltoHueco,
		Cierre = 1,
		Bajada = modelo:GetAttribute(Config.AtributoPersiana) == true,
		Animacion = nil,
		Baliza = if baliza and baliza:IsA("BasePart") then baliza else nil,
		LuzBaliza = if baliza then baliza:FindFirstChildOfClass("PointLight") else nil,
		ColorBalizaApagada = if baliza and baliza:IsA("BasePart") then baliza.Color else nil,
		Estado = if etiqueta and etiqueta:IsA("TextLabel") then etiqueta else nil,
		Polvo = polvo,
		Chispas = chispas,
		Sonidos = crearSonidos(if cajon then cajon else origen),
		Conexiones = {},
		DestelloHasta = 0,
	}
	tiendas[modelo] = tienda

	-- Estado actual, sin animación.
	colocar(tienda, if tienda.Bajada then 1 else 0)
	pintarEstado(tienda, tienda.Bajada)
	pintarBaliza(tienda, tienda.Bajada)
	if tienda.Bajada then
		asegurarBucle()
	end

	table.insert(
		tienda.Conexiones,
		modelo:GetAttributeChangedSignal(Config.AtributoPersiana):Connect(function()
			alCambiar(tienda)
		end)
	)
	table.insert(
		tienda.Conexiones,
		modelo.AncestryChanged:Connect(function()
			if not modelo:IsDescendantOf(workspace) then
				soltar(modelo)
			end
		end)
	)
end

-- ¿Está bajada la persiana de esta tienda? (Lo que ve el cliente: el atributo que publica el servidor.)
function Persianas.Bajada(modelo: Model): boolean
	return modelo:GetAttribute(Config.AtributoPersiana) == true
end

-- Empieza a animar las persianas de todas las tiendas, también las que lleguen después por streaming.
function Persianas.Iniciar()
	if iniciado then
		return
	end
	iniciado = true
	for _, modelo in CollectionService:GetTagged(Config.EtiquetaTienda) do
		task.spawn(registrar, modelo)
	end
	CollectionService:GetInstanceAddedSignal(Config.EtiquetaTienda):Connect(function(modelo)
		task.spawn(registrar, modelo)
	end)
	CollectionService:GetInstanceRemovedSignal(Config.EtiquetaTienda):Connect(function(modelo)
		if modelo:IsA("Model") then
			soltar(modelo)
		end
	end)
end

return Persianas
