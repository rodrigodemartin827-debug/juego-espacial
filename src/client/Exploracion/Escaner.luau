--!strict
--[[
	Escaner (cliente): el escáner de mano. Mantén Q (o el botón táctil "Escanear") apuntando a una criatura, una planta o un
	mineral: mientras dura el análisis se ve una barra de progreso y los efectos de escaneo; al terminar aparece la ficha.

	Qué hace este módulo (el servidor decide todo lo importante, ver Servicios/ServicioEscaner):
	  - al pulsar, busca el objetivo con Apuntar y se lo propone al servidor (EscanearObjetivo);
	  - al soltar antes de tiempo, avisa (CancelarEscaneo);
	  - dibuja la barra de progreso de SU escaneo y enseña la ficha cuando el servidor la manda (FichaEscaner).

	El alcance que se usa para buscar sale de la mejora Escáner del jugador (mismo cálculo que el servidor). La
	velocidad la aplica el servidor: aquí solo se muestra el tiempo que dice.
]]

local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Exploracion.Config)
local Estadisticas = require(Shared.Naves.Estadisticas)
local Apuntar = require(script.Parent.Apuntar)
local Avisos = require(script.Parent.Avisos)
local Estilo = require(script.Parent.Estilo)
local Ficha = require(script.Parent.Ficha)
local ServicioDatos = require(script.Parent.Parent.Servicios.ServicioDatos)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)

local Escaner = {}

local ACCION = "EscanerDeMano"

local pantalla: ScreenGui? = nil
local marcoBarra: Frame? = nil
local relleno: Frame? = nil
local textoBarra: TextLabel? = nil

local pulsado = false -- el jugador mantiene la tecla
local escaneando = false -- el servidor ha aceptado MI escaneo y está en marcha
local inicio = 0
local duracion = 1

local function pilotando(): boolean
	local personaje = Players.LocalPlayer.Character
	return personaje ~= nil and personaje:GetAttribute(Config.AtributoPilotando) == true
end

-- ===== Barra de progreso =====

local function construirBarra()
	local nueva = Estilo.Pantalla("EscanerHUD", 17)
	nueva.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	pantalla = nueva

	local marco = Estilo.Panel(
		nueva,
		UDim2.fromOffset(if Estilo.EsMovil then 220 else 280, 46),
		UDim2.new(0.5, 0, 1, if Estilo.EsMovil then -110 else -92),
		Estilo.CIAN
	)
	marco.AnchorPoint = Vector2.new(0.5, 1)
	marco.Visible = false
	marcoBarra = marco

	textoBarra =
		Estilo.Etiqueta(marco, "ANALIZANDO…", 12, Estilo.CIAN, UDim2.new(1, -20, 0, 16), UDim2.fromOffset(10, 5))
	relleno = Estilo.Barra(marco, UDim2.new(1, -20, 0, 10), UDim2.fromOffset(10, 28), Estilo.CIAN)
end

local function mostrarBarra(visible: boolean)
	if marcoBarra then
		marcoBarra.Visible = visible
	end
end

local function alActualizar()
	if not escaneando or relleno == nil then
		return
	end
	local fraccion = math.clamp((os.clock() - inicio) / duracion, 0, 1)
	relleno.Size = UDim2.fromScale(fraccion, 1)
	if textoBarra then
		textoBarra.Text = `ANALIZANDO… {math.floor(fraccion * 100)} %`
	end
end

-- ===== Pulsar y soltar =====

local function empezar()
	if pilotando() or escaneando then
		return
	end
	local datos = ServicioDatos.Obtener()
	if datos == nil then
		return
	end
	local alcance = Estadisticas.Calcular(datos.MejorasNave).AlcanceEscaner
	local objetivo = Apuntar.Buscar(Config.EtiquetaEscaneable, alcance, Config.AnguloAyudaApuntado)
	if objetivo == nil then
		Avisos.Mostrar("Apunta a una criatura, planta o mineral al alcance", "Info")
		return
	end
	ServicioRed.Enviar("EscanearObjetivo", objetivo)
end

local function soltar()
	if escaneando then
		escaneando = false
		mostrarBarra(false)
		ServicioRed.Enviar("CancelarEscaneo")
	end
end

local function alAccion(_nombre: string, estado: Enum.UserInputState, _entrada: InputObject): Enum.ContextActionResult?
	if estado == Enum.UserInputState.Begin then
		pulsado = true
		empezar()
	else
		pulsado = false
		soltar()
	end
	return Enum.ContextActionResult.Sink
end

-- ===== Avisos del servidor =====

local function alIniciarEscaneo(personaje: any, _objetivo: any, segundos: any)
	if personaje ~= Players.LocalPlayer.Character or type(segundos) ~= "number" then
		return
	end
	escaneando = true
	inicio = os.clock()
	duracion = math.max(segundos, 0.1)
	mostrarBarra(true)
	-- Si soltó la tecla mientras el servidor aún decidía, se cancela enseguida (el escáner es de mantener pulsado).
	if not pulsado then
		soltar()
	end
end

local function alTerminar(personaje: any)
	if personaje ~= Players.LocalPlayer.Character then
		return
	end
	escaneando = false
	mostrarBarra(false)
end

local function alRecibirFicha(especie: any, nuevo: any, xp: any, monedas: any, veces: any)
	if type(especie) ~= "string" or type(xp) ~= "number" or type(monedas) ~= "number" or type(veces) ~= "number" then
		return
	end
	Ficha.Mostrar(especie, nuevo == true, xp, monedas, veces)
end

-- Arranca el escáner del cliente. Debe llamarse una vez, después de ServicioRed.Iniciar().
function Escaner.Iniciar()
	construirBarra()

	ServicioRed.Conectar("EscaneoIniciado", alIniciarEscaneo)
	ServicioRed.Conectar("EscaneoCancelado", alTerminar)
	ServicioRed.Conectar("EscaneoCompletado", function(personaje: any)
		alTerminar(personaje)
	end)
	ServicioRed.Conectar("FichaEscaner", alRecibirFicha)
	RunService.RenderStepped:Connect(alActualizar)

	-- Q en el teclado; el botón táctil lo crea ContextActionService.
	ContextActionService:BindAction(ACCION, alAccion, true, Enum.KeyCode.Q, Enum.KeyCode.ButtonL1)
	ContextActionService:SetTitle(ACCION, "Escanear")
	ContextActionService:SetPosition(ACCION, UDim2.new(1, -170, 1, -230))
end

return Escaner
