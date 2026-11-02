--!strict
--[[
	ServicioNaves (cliente): une el vuelo, la cámara, el panel, los controles y los efectos.

	El servidor manda la foto del estado de la nave (EstadoNave) cuando el jugador despega, unas veces por
	segundo y cuando ocurre algo. Este servicio reacciona a ella:

	  Activa y no lista    la nave está arrancando los motores: se muestra el panel y la cámara la sigue.
	  Activa y lista       el piloto ya puede volar: se activan los mandos (Vuelo).
	  No activa            aterrizó, fue destruida o el piloto cayó: se devuelve todo a la vista de a pie.

	Mientras se pilota se pausa el combate a pie (sus teclas, su ratón y su interfaz) para que disparar la nave
	no lance un combo del personaje.
]]

local ServicioCombate = require(script.Parent.Parent.Combate.ServicioCombate)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)
local Camara = require(script.Parent.Camara)
local Efectos = require(script.Parent.Efectos)
local Panel = require(script.Parent.Panel)
local Vuelo = require(script.Parent.Vuelo)

local ServicioNaves = {}

local enNave = false -- hay una nave del jugador (aunque aún esté arrancando)
local volando = false -- los mandos ya están activos
local preparando = false -- se están activando los mandos (puede tardar: espera a que el modelo termine de replicarse)
local iniciado = false

local ROJO = Color3.fromRGB(255, 120, 130)

local function pedirAterrizar()
	ServicioRed.Enviar("AterrizarNave")
end

-- Vuelve a la vista de a pie.
local function salir(destruida: boolean)
	preparando = false
	if volando then
		Vuelo.Detener()
		volando = false
	end
	if enNave then
		enNave = false
		Camara.Detener()
		Panel.Ocultar()
		Efectos.PonerNavePropia(nil)
		ServicioCombate.Pausar(false)
	end
	if destruida then
		Panel.AvisoFinal("NAVE DESTRUIDA")
	end
end

local function alRecibirEstado(datos: any)
	if type(datos) ~= "table" then
		return
	end
	if datos.Activa ~= true then
		salir(datos.Destruida == true)
		-- Un mensaje del servidor sin nave: por qué no ha podido despegar, por ejemplo.
		if type(datos.Aviso) == "string" then
			Panel.AvisoFinal(datos.Aviso, Color3.fromRGB(255, 210, 120))
		end
		return
	end

	local modelo = datos.Modelo
	if typeof(modelo) ~= "Instance" or not (modelo :: Instance):IsA("Model") then
		return -- el modelo aún no ha llegado a este cliente: el servidor repite el estado enseguida
	end

	if not enNave then
		enNave = true -- antes de esperar al modelo: así un segundo mensaje no repite la entrada
		local raiz = (modelo :: Model).PrimaryPart or (modelo :: Model):WaitForChild("Fuselaje", 5)
		if raiz == nil or not raiz:IsA("BasePart") then
			enNave = false
			return
		end
		Efectos.PonerNavePropia(modelo :: Model)
		ServicioCombate.Pausar(true)
		Panel.Mostrar(raiz)
		Camara.Iniciar(raiz, datos.VelocidadMax)
	end

	Panel.Actualizar(datos)
	if type(datos.Aviso) == "string" then
		Panel.Aviso(datos.Aviso, ROJO)
	end

	if datos.Lista == true then
		if volando then
			Vuelo.Actualizar(datos)
		elseif not preparando then
			preparando = true
			volando = Vuelo.Iniciar(datos, pedirAterrizar) and enNave
			preparando = false
		end
	end
end

-- Arranca el sistema de naves del cliente. Debe llamarse una vez, después de ServicioRed.Iniciar() y de ServicioCombate.Iniciar().
function ServicioNaves.Iniciar()
	if iniciado then
		return
	end
	iniciado = true

	Efectos.Iniciar(Vuelo.Chocar)
	ServicioRed.Conectar("EstadoNave", alRecibirEstado)
	-- Por si el servidor ya había enviado el estado antes de que este cliente estuviera escuchando.
	ServicioRed.Enviar("PedirEstadoNave")
end

return ServicioNaves
