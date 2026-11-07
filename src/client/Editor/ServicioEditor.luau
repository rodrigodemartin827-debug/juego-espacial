--!strict
--[[
	ServicioEditor (cliente): el editor de personaje, segundo paso de la entrada (bando → editor → gráficos →
	cinemática).

	Cuando termina el paso de bando: si el jugador es Humano y aún no ha hecho su personaje (o en Studio con el modo
	de pruebas), se abre el editor con lo que tenga guardado; al pulsar CONTINUAR se guarda en el servidor (remoto
	GuardarAparienciaHumano) y se pasa al paso siguiente. Los Monstruos tendrán su propio editor: de momento su paso
	se da por terminado.

	La vista previa la pone este cliente en su propio personaje (Personaje/Constructor); al guardar, el servidor pone
	la de verdad, que ven todos.
	`ServicioEditor.EsperarFin()` bloquea hasta que este paso ha terminado (la pantalla de gráficos lo usa).
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Apariencia = require(Shared.Personaje.Apariencia)
local Bandos = require(Shared.Juego.Bandos)
local Config = require(Shared.Personaje.ConfigEditor)
local Constructor = require(Shared.Personaje.Constructor)
local Senal = require(Shared.Utilidades.Senal)
local ServicioDatos = require(script.Parent.Parent.Servicios.ServicioDatos)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)
local ServicioEleccion = require(script.Parent.Parent.Eleccion.ServicioEleccion)
local Pantalla = require(script.Parent.Pantalla)

local ServicioEditor = {}

local iniciado = false
local fin = false
local senalFin = Senal.nueva()

local function terminarPaso()
	if not fin then
		fin = true
		senalFin:Disparar()
	end
end

function ServicioEditor.EsperarFin()
	if not fin then
		senalFin:Esperar()
	end
end

local function vistaPrevia(a: Apariencia.Apariencia)
	local personaje = Players.LocalPlayer.Character
	if personaje then
		local ok, err = pcall(Constructor.Aplicar, personaje, a)
		if not ok then
			warn(`[Editor] No se pudo poner la vista previa: {err}`)
		end
	end
end

local function guardar(a: Apariencia.Apariencia)
	local valores = {}
	for i, campo in Apariencia.Campos do
		valores[i] = (a :: any)[campo]
	end
	ServicioRed.Enviar("GuardarAparienciaHumano", table.unpack(valores))
end

local function paso()
	ServicioEleccion.EsperarFin()
	local datos = ServicioDatos.Obtener()
	if datos == nil or datos.Bando ~= Bandos.Humanos then
		terminarPaso()
		return
	end
	local guardada = datos.Apariencia and datos.Apariencia.Humano
	local mostrar = not Apariencia.Hecha(guardada) or (RunService:IsStudio() and Config.MostrarSiempreEnStudio)
	if not mostrar then
		terminarPaso()
		return
	end
	-- Espera al personaje (puede estar reapareciendo tras elegir bando).
	local jugador = Players.LocalPlayer
	local limite = os.clock() + 10
	while
		(jugador.Character == nil or jugador.Character:FindFirstChild("HumanoidRootPart") == nil)
		and os.clock() < limite
	do
		task.wait(0.1)
	end
	local ok, err = pcall(Pantalla.Abrir, {
		Inicial = Apariencia.Validar(guardada),
		AlCambiar = vistaPrevia,
		AlTerminar = function(a: Apariencia.Apariencia)
			guardar(a)
			terminarPaso()
		end,
	})
	if not ok then
		warn(`[Editor] No se pudo abrir el editor: {err}`)
		terminarPaso()
	end
end

-- Arranca. Una vez, después de ServicioDatos.Iniciar() y de ServicioEleccion.Iniciar().
function ServicioEditor.Iniciar()
	if iniciado then
		return
	end
	iniciado = true
	task.spawn(paso)
end

return ServicioEditor
