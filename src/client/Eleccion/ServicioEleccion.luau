--!strict
--[[
	ServicioEleccion (cliente): la pantalla de elección de bando de la PRIMERA entrada al juego.

	Al arrancar el cliente se pone una cortina negra (para que no se vea el juego un instante antes de la pantalla) y
	se esperan los datos del jugador:
	  - si ya tiene bando, la cortina se funde y se juega normal;
	  - si su bando es "Ninguno", se monta la pantalla: el jugador queda quieto y sin interfaz (Bloqueo), la cámara
	    fija mira la escena (Escena) con los dos planetas y la grieta, y la interfaz (Interfaz) le enseña cada bando.

	Elegir es UN clic (o soltar el dedo) sobre un lado: se pide al servidor con el remoto ElegirBando. Mientras
	responde, el planeta "toma aire" (anticipación). Cuando llegan los datos con el bando ya puesto (DatosJugador),
	estalla la confirmación, la pantalla se funde a negro, se desmonta todo y se vuelve al juego con otro fundido.
	Las reglas (cuándo se muestra, que solo se pida una vez, reintentar si el servidor no responde) están en
	Eleccion/Flujo; la validación de verdad la hace el servidor (Servicios/ServicioBandos).

	Si algo falla al montar la escena 3D, la pantalla sigue funcionando solo con la interfaz: el jugador nunca se
	queda atascado sin poder elegir, ni con la pantalla en negro.

	`ServicioEleccion.Terminada` se dispara (con el bando) cuando el jugador vuelve al juego tras elegir: ahí se
	engancha lo que empieza después, como el tutorial.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Eleccion.Config)
local Flujo = require(Shared.Eleccion.Flujo)
local Senal = require(Shared.Utilidades.Senal)
local Pantalla = require(script.Parent.Parent.VFX.Pantalla)
local ServicioDatos = require(script.Parent.Parent.Servicios.ServicioDatos)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)
local Bloqueo = require(script.Parent.Bloqueo)
local Escena = require(script.Parent.Escena)
local Interfaz = require(script.Parent.Interfaz)

local ServicioEleccion = {}

-- Se dispara (con el bando) cuando el jugador, tras elegir, ya está de vuelta en el juego.
ServicioEleccion.Terminada = Senal.nueva()

local flujo: Flujo.Flujo = Flujo.nuevo(Config.Tiempos.EsperaConfirmacion)
local iniciado = false
local conEscena = false

-- Ejecuta `funcion` protegida: si falla, avisa en la consola y devuelve false.
local function protegido(nombre: string, funcion: () -> ()): boolean
	-- El envoltorio devuelve nil para que xpcall dé siempre dos resultados (éxito y error).
	local ok, motivo = xpcall(function(): any
		funcion()
		return nil
	end, function(err: any): string
		return debug.traceback(tostring(err), 2)
	end)
	if not ok then
		warn(`[Elección] Falló {nombre}: {motivo}`)
	end
	return ok
end

-- ===== Resaltar y elegir =====

local function resaltar(bando: string?)
	if Flujo.Resaltar(flujo, bando) then
		Interfaz.Resaltar(bando)
		if conEscena then
			protegido("el resaltado de la escena", function()
				Escena.Resaltar(bando)
			end)
		end
	end
end

-- Si el servidor no confirma a tiempo, se deja volver a elegir.
local function vigilarEspera()
	task.delay(Config.Tiempos.EsperaConfirmacion + 0.1, function()
		if Flujo.RevisarEspera(flujo, os.clock()) then
			Interfaz.Error()
			if conEscena then
				Escena.Cancelar()
			end
		end
	end)
end

local function elegir(bando: string)
	if not Flujo.Elegir(flujo, bando, os.clock()) then
		return
	end
	if not ServicioRed.Enviar("ElegirBando", bando) then
		-- No llegó a salir (el límite del remoto): se reabre la elección enseguida.
		Flujo.RevisarEspera(flujo, math.huge)
		return
	end
	Interfaz.Resaltar(bando)
	Interfaz.Esperando(true)
	if conEscena then
		protegido("la anticipación", function()
			Escena.Anticipar(bando)
		end)
	end
	vigilarEspera()
end

-- Teclado y mando: izquierda / derecha mueven el resaltado e Intro / Ⓐ eligen el resaltado.
local function alPulsar(tecla: Bloqueo.Tecla)
	if not Flujo.PuedeElegir(flujo) then
		return
	end
	if tecla == "Elegir" then
		if flujo.Resaltado then
			elegir(flujo.Resaltado)
		end
	else
		resaltar(Flujo.Vecino(Config.Orden, flujo.Resaltado, if tecla == "Izquierda" then -1 else 1))
	end
end

-- ===== Mostrar, confirmar y cerrar =====

-- Desmonta la pantalla y devuelve el juego al jugador (sin fundidos). Siempre deja al jugador libre.
local function desmontar()
	protegido("desmontar la escena", Escena.Destruir)
	protegido("desmontar la interfaz", Interfaz.Destruir)
	protegido("devolver los controles", Bloqueo.Desactivar)
	if Config.Interfaz.BarrasCine then
		protegido("quitar las barras de cine", function()
			Pantalla.Cine(false, 0)
		end)
	end
	conEscena = false
end

local function mostrar()
	Bloqueo.Activar(alPulsar)
	conEscena = protegido("montar la escena 3D", Escena.Construir)
	if not conEscena then
		protegido("desmontar la escena a medias", Escena.Destruir)
	end
	local conInterfaz = protegido("montar la interfaz", function()
		Interfaz.Crear({ AlResaltar = resaltar, AlElegir = elegir })
	end)
	if not conInterfaz then
		-- Sin interfaz no se puede elegir: mejor devolver el juego que dejarle atascado (el servidor lo mantiene
		-- protegido, y la próxima vez que entre volverá a ver la pantalla).
		desmontar()
		Flujo.Terminar(flujo)
		Interfaz.Fundir(0, Config.Tiempos.FundidoEntrada)
		Interfaz.QuitarCortina()
		return
	end
	if Config.Interfaz.BarrasCine then
		protegido("poner las barras de cine", function()
			Pantalla.Cine(true, Config.Tiempos.FundidoEntrada)
		end)
	end
	Interfaz.Fundir(0, Config.Tiempos.FundidoEntrada)
end

local function confirmar(bando: string)
	Interfaz.Esperando(false)
	protegido("el mensaje de confirmación", function()
		Interfaz.Confirmar(bando)
	end)
	if conEscena then
		protegido("la confirmación de la escena", function()
			Escena.Confirmar(bando)
		end)
	end

	-- La celebración, fundido a negro, se desmonta todo con la pantalla en negro y se vuelve al juego.
	local t = Config.Tiempos
	task.wait(t.Celebracion)
	Interfaz.Fundir(1, t.FundidoSalida)
	desmontar()
	Flujo.Terminar(flujo)
	task.wait(t.NegroMantenido)
	Interfaz.Fundir(0, t.FundidoVuelta)
	Interfaz.QuitarCortina()
	ServicioEleccion.Terminada:Disparar(bando)
end

local function omitir()
	Interfaz.Fundir(0, Config.Tiempos.FundidoEntrada)
	Interfaz.QuitarCortina()
end

-- Llega una copia de los datos del servidor: el flujo decide qué hacer.
local function alRecibirDatos(datos: any)
	local accion, bando = Flujo.AlRecibirDatos(flujo, datos)
	if accion == "Mostrar" then
		task.spawn(function()
			if not protegido("mostrar la pantalla", mostrar) then
				desmontar()
				Flujo.Terminar(flujo)
				Interfaz.QuitarCortina()
			end
		end)
	elseif accion == "Omitir" then
		task.spawn(omitir)
	elseif accion == "Confirmar" and bando ~= nil then
		task.spawn(function()
			if not protegido("confirmar la elección", function()
				confirmar(bando)
			end) then
				desmontar()
				Flujo.Terminar(flujo)
				Interfaz.QuitarCortina()
			end
		end)
	end
end

-- ===== Arranque =====

-- ¿Se está mostrando la pantalla de elección?
function ServicioEleccion.Activa(): boolean
	return flujo.Mostrada and flujo.Estado ~= "Terminado"
end

--[[
	Arranca la pantalla de elección. Debe llamarse una vez, después de ServicioDatos.Iniciar() y de los servicios
	del juego (combate, naves, exploración), para poder pausarlos y ocultar su interfaz.
]]
function ServicioEleccion.Iniciar()
	if iniciado then
		return
	end
	iniciado = true

	Interfaz.CrearCortina()
	ServicioDatos.Actualizados:Conectar(alRecibirDatos)
	-- Puede que los datos ya hubieran llegado antes de que este servicio escuchara.
	local datos = ServicioDatos.Obtener()
	if datos ~= nil then
		alRecibirDatos(datos)
	end

	-- La cortina nunca se queda puesta: si los datos no llegan (el servidor expulsa al jugador si no pudo cargarlos),
	-- se quita igualmente.
	task.delay(Config.Tiempos.EsperaMaximaDatos, function()
		if flujo.Estado == "Esperando" then
			warn("[Elección] Los datos del jugador no han llegado: se quita la cortina")
			Interfaz.QuitarCortina()
		end
	end)
end

return ServicioEleccion
