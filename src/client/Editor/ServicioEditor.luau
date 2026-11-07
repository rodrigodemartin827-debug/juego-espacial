--!strict
--[[
	ServicioEditor (cliente): el editor de personaje, segundo paso de la entrada (bando → editor → gráficos →
	cinemática).

	Cuando termina el paso de bando: si el jugador es Humano y aún no ha hecho su personaje (o en Studio con el modo
	de pruebas), se abre el editor con lo que tenga guardado:
	  · Editor/Estudio: la escena 3D con una copia de su R6 que cambia al instante.
	  · Editor/Pantalla: la interfaz (piel, categorías con flechas, rueda de color, ATRÁS / ALEATORIO / CONTINUAR).
	  · CONTINUAR: se guarda en el servidor (remoto GuardarAparienciaHumano, que lo valida) y se pasa al paso
	    siguiente.
	  · ATRÁS: se vuelve a la elección de bando (remoto VolverEleccionBando; el servidor solo lo deja mientras no se
	    haya terminado el primer personaje). Al elegir otra vez, el editor vuelve a empezar (o no sale, si eligió
	    Monstruos).
	Los Monstruos tendrán su propio editor: de momento su paso se da por terminado.

	`ServicioEditor.EsperarFin()` bloquea hasta que este paso ha terminado (la pantalla de gráficos lo usa).
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Apariencia = require(Shared.Personaje.Apariencia)
local Bandos = require(Shared.Juego.Bandos)
local Config = require(Shared.Personaje.ConfigEditor)
local Senal = require(Shared.Utilidades.Senal)
local ServicioDatos = require(script.Parent.Parent.Servicios.ServicioDatos)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)
local ServicioEleccion = require(script.Parent.Parent.Eleccion.ServicioEleccion)
local Estudio = require(script.Parent.Estudio)
local Pantalla = require(script.Parent.Pantalla)

local ServicioEditor = {}

-- Segundos que se espera a que el servidor confirme la vuelta a la elección de bando.
local ESPERA_VOLVER = 6

local iniciado = false
local fin = false
local senalFin = Senal.nueva()
local azar = Random.new()

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

local function guardar(a: Apariencia.Apariencia)
	local valores = {}
	for i, campo in Apariencia.Campos do
		valores[i] = (a :: any)[campo]
	end
	ServicioRed.Enviar("GuardarAparienciaHumano", table.unpack(valores))
end

local function cerrar()
	Pantalla.Cerrar()
	Estudio.Cerrar()
end

local paso: () -> ()

-- Espera (hasta `segundos`) a que `condicion()` se cumpla. Devuelve si se cumplió.
local function esperarA(condicion: () -> boolean, segundos: number): boolean
	local limite = os.clock() + segundos
	while not condicion() do
		if os.clock() > limite then
			return false
		end
		task.wait(0.1)
	end
	return true
end

local function abrir(guardada: any)
	local jugador = Players.LocalPlayer
	-- Espera al personaje (puede estar reapareciendo tras elegir bando).
	esperarA(function()
		local p = jugador.Character
		return p ~= nil and p:FindFirstChild("HumanoidRootPart") ~= nil and p:FindFirstChild("Head") ~= nil
	end, 10)
	local personaje = jugador.Character
	if personaje == nil then
		warn("[Editor] No hay personaje: se salta el editor")
		terminarPaso()
		return
	end
	local inicial = Apariencia.Validar(guardada)
	if not Estudio.Abrir(personaje, inicial) then
		warn("[Editor] No se pudo montar la escena del editor: se salta")
		terminarPaso()
		return
	end
	local opciones: Pantalla.Opciones = {
		Inicial = inicial,
		AlCambiar = function(a: Apariencia.Apariencia, tipo: string)
			if tipo == "Color" then
				Estudio.Colorear(a)
			else
				Estudio.Aplicar(a, true)
			end
		end,
		AlDisponer = function(disposicion: Pantalla.Disposicion)
			Estudio.Encuadrar(Config.Camara.PosicionX[disposicion])
		end,
		AlAleatorio = function(): Apariencia.Apariencia
			return Apariencia.Aleatoria(azar)
		end,
		AlAtras = function()
			cerrar()
			ServicioRed.Enviar("VolverEleccionBando")
			-- Si el servidor lo acepta, el bando vuelve a «Ninguno» y sale otra vez la elección; al elegir, se repite
			-- este paso. Si no (ya hizo su personaje), se vuelve al editor.
			local volvio = esperarA(function()
				local d = ServicioDatos.Obtener()
				return d ~= nil and d.Bando == Bandos.Ninguno
			end, ESPERA_VOLVER)
			if volvio then
				ServicioEleccion.Terminada:Esperar()
				task.spawn(paso)
			else
				abrir(guardada)
			end
		end,
		AlTerminar = function(a: Apariencia.Apariencia)
			guardar(a)
			cerrar()
			terminarPaso()
		end,
	}
	local ok, err = pcall(function(): any
		Pantalla.Abrir(opciones)
		return nil
	end)
	if not ok then
		warn(`[Editor] No se pudo abrir el editor: {err}`)
		cerrar()
		terminarPaso()
	end
end

paso = function()
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
	abrir(guardada)
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
