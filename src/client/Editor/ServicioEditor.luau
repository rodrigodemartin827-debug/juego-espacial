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
local Perfiles = require(Shared.Personaje.PerfilEditor)
local AvatarR6 = require(Shared.Personaje.AvatarR6)
local Bandos = require(Shared.Juego.Bandos)
local Config = require(Shared.Personaje.ConfigEditor)
local Senal = require(Shared.Utilidades.Senal)
local ServicioDatos = require(script.Parent.Parent.Servicios.ServicioDatos)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)
local ServicioEleccion = require(script.Parent.Parent.Eleccion.ServicioEleccion)
local Estudio = require(script.Parent.Estudio)
local Pantalla = require(script.Parent.Pantalla)

local ServicioEditor = {}

-- El perfil del bando del jugador (Personaje/PerfilEditor) y sus reglas: se ponen al abrir el editor.
local perfilActual: any = Perfiles.Humanos
local Apariencia: any = Perfiles.Humanos.Apariencia

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

local function guardar(a: any, usarAvatar: boolean)
	local valores = {}
	for i, campo in Apariencia.Campos do
		valores[i] = a[campo]
	end
	local cuantos = #Apariencia.Campos
	if perfilActual.Avatar then
		valores[cuantos + 1] = usarAvatar
		cuantos += 1
	end
	ServicioRed.Enviar(perfilActual.Remoto, table.unpack(valores, 1, cuantos))
end

-- El avatar de Roblox de este jugador (se pide una vez; el servidor lo vuelve a pedir con su UserId, esto es solo la
-- vista previa). nil si Roblox no responde.
local avatar: HumanoidDescription? = nil
local function cargarAvatar(): HumanoidDescription?
	if avatar then
		return avatar
	end
	for intento = 1, Config.Avatar.Intentos do
		local ok, d = pcall(function()
			return Players:GetHumanoidDescriptionFromUserId(Players.LocalPlayer.UserId)
		end)
		if ok and d then
			avatar = d
			return d
		end
		if intento < Config.Avatar.Intentos then
			task.wait(Config.Avatar.EsperaIntento)
		end
	end
	return nil
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

local function abrir(guardada: any, usarAvatarInicial: boolean, perfil: any)
	perfilActual = perfil
	Apariencia = perfil.Apariencia
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
	if not Estudio.Abrir(personaje, inicial, perfil) then
		warn("[Editor] No se pudo montar la escena del editor: se salta")
		terminarPaso()
		return
	end
	local actual = inicial -- las piezas elegidas (se conservan mientras se usa el avatar)
	local usarAvatar = false
	local pedido = 0 -- número de la última petición de cambio de modo: una carga lenta no pisa a una más nueva

	-- Pasa a ver el avatar de Roblox en la copia y avisa de lo que no se pudo convertir.
	local function ponerAvatar()
		pedido += 1
		local mio = pedido
		Pantalla.AvatarCargando(true)
		Pantalla.Informe({})
		task.spawn(function()
			local d = cargarAvatar()
			if mio ~= pedido or not Pantalla.Abierta() then
				return
			end
			if d == nil then
				Pantalla.AvatarCargando(false)
				Pantalla.Informe({ Config.Textos.ErrorAvatar })
				return
			end
			local copiaDescripcion = d:Clone()
			local informe = AvatarR6.Preparar(copiaDescripcion, Config.Avatar.MaxAccesorios)
			Estudio.AplicarAvatar(copiaDescripcion, function()
				if mio ~= pedido or not Pantalla.Abierta() then
					return
				end
				usarAvatar = true
				Pantalla.PonerAvatar(true)
				Pantalla.AvatarCargando(false)
				Pantalla.Informe(AvatarR6.Textos(informe))
			end)
		end)
	end

	local opciones: Pantalla.Opciones = {
		Perfil = perfil,
		Inicial = inicial,
		UsarAvatar = false, -- se pone en cuanto carga si estaba guardado (ver más abajo)
		AlCambiar = function(a: any, tipo: string)
			actual = a
			if usarAvatar then
				return -- el avatar no cambia con las piezas
			end
			if tipo == "Color" then
				Estudio.Colorear(a)
			else
				Estudio.Aplicar(a, true)
			end
		end,
		AlAvatar = function(activo: boolean)
			if activo then
				ponerAvatar()
			else
				pedido += 1
				usarAvatar = false
				Pantalla.PonerAvatar(false)
				Pantalla.AvatarCargando(false)
				Estudio.Aplicar(actual, true)
			end
		end,
		AlDisponer = function(disposicion: Pantalla.Disposicion)
			Estudio.Encuadrar(Config.Camara.PosicionX[disposicion])
		end,
		AlAleatorio = function(): any
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
				abrir(guardada, usarAvatar, perfil)
			end
		end,
		AlTerminar = function(a: any, conAvatar: boolean)
			guardar(a, conAvatar)
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
		return
	end
	if usarAvatarInicial then
		ponerAvatar()
	end
end

paso = function()
	ServicioEleccion.EsperarFin()
	local datos = ServicioDatos.Obtener()
	local perfil = if datos then Perfiles[datos.Bando] else nil
	if datos == nil or perfil == nil then
		terminarPaso()
		return
	end
	local guardada = datos.Apariencia and datos.Apariencia[perfil.CampoDatos]
	local mostrar = not perfil.Apariencia.Hecha(guardada) or (RunService:IsStudio() and Config.MostrarSiempreEnStudio)
	if not mostrar then
		terminarPaso()
		return
	end
	local usarAvatar = perfil.Avatar and datos.Apariencia ~= nil and datos.Apariencia.UsarAvatar == true
	abrir(guardada, usarAvatar, perfil)
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
