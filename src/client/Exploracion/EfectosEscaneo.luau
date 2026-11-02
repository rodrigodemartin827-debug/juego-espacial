--!strict
--[[
	EfectosEscaneo (Exploración): lo que se VE del escáner y de la minería, con el mismo motor de efectos del combate
	(client/VFX/Gestor) y las recetas de Exploracion/Datos/EfectosExploracion.

	Cuando el servidor avisa de que alguien empieza a escanear (EscaneoIniciado) se monta, en todos los clientes cercanos:

	  1. La CARGA de la mano (Escaner_Carga) y, en la pantalla de quien escanea, un ligero zoom y tinte cian.
	  2. Un bucle de PULSOS (Escaner_Pulso) cada 0,4 s mientras dura el análisis: rayo con halo desde la mano, paquetes de
	     datos, anillos y chispas sobre el objetivo.
	  3. Un CONTORNO pulsante sobre el objetivo (Highlight) y BARRIDOS de luz que lo recorren de abajo arriba, con un
	     disco brillante y un anillo fino que van acompañados de su propia luz.
	  4. Al terminar (EscaneoCompletado): estallido final (Escaner_Completado) y un destello del contorno que se desvanece.
	     Si se interrumpe (EscaneoCancelado): chisporroteo rojo (Escaner_Cancelado) y se recoge todo.

	También reproduce los golpes y roturas de minerales (MineralGolpeado, MineralRoto). Todo es visual: nada de lo que pase
	aquí cambia el juego.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Especies = require(Shared.Exploracion.Datos.Especies)
local EfectosExploracion = require(Shared.Exploracion.Datos.EfectosExploracion)
local Paleta = require(Shared.Combate.Datos.Paleta)
local Calidad = require(script.Parent.Parent.VFX.Calidad)
local Estilo = require(script.Parent.Estilo)
local Gestor = require(script.Parent.Parent.VFX.Gestor)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)
local Utiles = require(script.Parent.Parent.VFX.Utiles)

local EfectosEscaneo = {}

-- Más lejos que esto, el escaneo de otro jugador no se dibuja.
local DISTANCIA_MAXIMA = 220
-- Segundos entre pulsos del rayo.
local INTERVALO_PULSO = 0.4
-- Cada cuántos segundos empieza un barrido de luz sobre el objetivo.
local INTERVALO_BARRIDO = 0.9

type Sesion = {
	Personaje: Model,
	Objetivo: Instance,
	Inicio: number,
	Duracion: number,
	EsLocal: boolean,
	Activa: boolean,
	Resalte: Highlight?,
	Conexion: RBXScriptConnection?,
}

local sesiones: { [Model]: Sesion } = {}
local carpeta: Folder? = nil

-- ===== Utilidades =====

local function esModelo(valor: any): boolean
	return typeof(valor) == "Instance" and (valor :: Instance):IsA("Model")
end

local function esVector(valor: any): boolean
	return typeof(valor) == "Vector3"
end

local function carpetaLocal(): Folder
	if carpeta == nil or carpeta.Parent == nil then
		carpeta = Estilo.CarpetaLocal("EscaneoLocal")
	end
	return carpeta :: Folder
end

-- Caja (marco y tamaño) que envuelve al objetivo.
local function caja(objetivo: Instance): (CFrame, Vector3)
	if objetivo:IsA("Model") then
		return objetivo:GetBoundingBox()
	elseif objetivo:IsA("BasePart") then
		return objetivo.CFrame, objetivo.Size
	end
	return CFrame.new(), Vector3.one
end

-- Punta de la mano derecha (R6: el brazo derecho entero) o, si no está, el cuerpo.
local function posicionMano(personaje: Model): Vector3
	local brazo = personaje:FindFirstChild("Right Arm")
	if brazo and brazo:IsA("BasePart") then
		return (brazo.CFrame * CFrame.new(0, -1, 0)).Position
	end
	return personaje:GetPivot().Position
end

local function distanciaACamara(punto: Vector3): number
	local camara = workspace.CurrentCamera
	return if camara then (camara.CFrame.Position - punto).Magnitude else 0
end

-- Opciones del motor de efectos para este instante (la mano se mueve, así que se recalcula en cada pulso).
local function opciones(sesion: Sesion): any
	local origen = posicionMano(sesion.Personaje)
	local punto = caja(sesion.Objetivo).Position
	local direccion = punto - origen
	local raiz = sesion.Personaje:FindFirstChild("HumanoidRootPart")
	return {
		Lanzador = sesion.Personaje,
		Raiz = raiz,
		Origen = origen,
		Punto = punto,
		Direccion = if direccion.Magnitude > 0.01 then direccion.Unit else Vector3.new(0, 0, -1),
		EsLocal = sesion.EsLocal,
		DistanciaMaxima = DISTANCIA_MAXIMA,
	}
end

-- Color del contorno según la categoría del objetivo (criatura, planta, mineral).
local function colorDeCategoria(objetivo: Instance): Color3
	local especie = Especies.Lista[objetivo:GetAttribute("EspecieId") :: any]
	local categoria = if especie then especie.Categoria else ""
	if categoria == "Criatura" then
		return Color3.fromRGB(255, 140, 120)
	elseif categoria == "Planta" then
		return Color3.fromRGB(120, 255, 160)
	elseif categoria == "Mineral" then
		return Color3.fromRGB(190, 170, 255)
	end
	return Estilo.CIAN
end

-- ===== Contorno y barridos =====

local function crearContorno(sesion: Sesion)
	local color = colorDeCategoria(sesion.Objetivo)
	local resalte = Instance.new("Highlight")
	resalte.Name = "ContornoEscaneo"
	resalte.FillColor = color
	resalte.OutlineColor = Color3.new(1, 1, 1)
	resalte.FillTransparency = 0.8
	resalte.OutlineTransparency = 0.1
	resalte.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop
	resalte.Adornee = sesion.Objetivo
	resalte.Parent = sesion.Objetivo
	sesion.Resalte = resalte

	-- Late más rápido a medida que avanza el análisis.
	sesion.Conexion = RunService.Heartbeat:Connect(function()
		if not sesion.Activa or resalte.Parent == nil then
			return
		end
		local progreso = math.clamp((os.clock() - sesion.Inicio) / sesion.Duracion, 0, 1)
		local frecuencia = 6 + progreso * 10
		resalte.FillTransparency = 0.65 + 0.2 * math.sin(os.clock() * frecuencia)
		resalte.OutlineTransparency = 0.05 + 0.15 * (0.5 + 0.5 * math.sin(os.clock() * frecuencia * 0.5))
	end)
end

-- Un barrido: un disco brillante y un anillo fino recorren el objetivo de abajo arriba, con una luz que los acompaña.
local function barrido(sesion: Sesion, subir: boolean)
	if not Calidad.Permite("Medio") then
		return
	end
	local marco, tamano = caja(sesion.Objetivo)
	local radio = math.max(tamano.X, tamano.Z) * 0.62 + 0.6
	local abajo = marco.Position - Vector3.new(0, tamano.Y / 2 + 0.2, 0)
	local arriba = marco.Position + Vector3.new(0, tamano.Y / 2 + 0.2, 0)
	local desde, hasta = if subir then abajo else arriba, if subir then arriba else abajo
	local segundos = math.clamp(sesion.Duracion * 0.45, 0.5, 1.1)
	local color = colorDeCategoria(sesion.Objetivo)

	local function disco(grosor: number, diametro: number, transparencia: number, color3: Color3): Part
		local parte = Instance.new("Part")
		parte.Shape = Enum.PartType.Cylinder
		parte.Size = Vector3.new(grosor, diametro, diametro) -- el cilindro de Roblox tiene su eje en X
		parte.CFrame = CFrame.new(desde) * CFrame.Angles(0, 0, math.pi / 2) -- tumbado: el eje apunta hacia arriba
		parte.Color = color3
		parte.Material = Enum.Material.Neon
		parte.Transparency = transparencia
		parte.Anchored = true
		parte.CanCollide = false
		parte.CanQuery = false
		parte.CanTouch = false
		parte.CastShadow = false
		parte.Parent = carpetaLocal()
		return parte
	end

	local plano = disco(0.12, radio * 2, 0.55, color)
	local anillo = disco(0.35, radio * 2.25, 0.2, Color3.new(1, 1, 1))
	local luz = Instance.new("PointLight")
	luz.Color = color
	luz.Range = math.clamp(radio * 3, 8, 28)
	luz.Brightness = 2.5
	luz.Parent = plano

	local destino = CFrame.new(hasta) * CFrame.Angles(0, 0, math.pi / 2)
	Utiles.Tween(plano, segundos, { CFrame = destino, Transparency = 0.95 }, "Sine")
	Utiles.Tween(anillo, segundos, { CFrame = destino, Transparency = 0.9 }, "Sine")
	Utiles.Tween(luz, segundos, { Brightness = 0 }, "Quad")
	task.delay(segundos + 0.05, function()
		plano:Destroy()
		anillo:Destroy()
	end)
end

-- Recoge el contorno y la conexión de una sesión.
local function limpiar(sesion: Sesion)
	sesion.Activa = false
	if sesion.Conexion then
		sesion.Conexion:Disconnect()
		sesion.Conexion = nil
	end
	local resalte = sesion.Resalte
	sesion.Resalte = nil
	if resalte then
		Utiles.Tween(resalte, 0.35, { FillTransparency = 1, OutlineTransparency = 1 }, "Quad")
		task.delay(0.4, function()
			resalte:Destroy()
		end)
	end
	if sesiones[sesion.Personaje] == sesion then
		sesiones[sesion.Personaje] = nil
	end
end

-- ===== Eventos del servidor =====

local function alIniciar(personaje: any, objetivo: any, duracion: any)
	if not esModelo(personaje) or typeof(objetivo) ~= "Instance" or type(duracion) ~= "number" then
		return
	end
	local modelo = personaje :: Model
	local destino = objetivo :: Instance
	local esLocal = modelo == Players.LocalPlayer.Character
	if not esLocal and distanciaACamara(modelo:GetPivot().Position) > DISTANCIA_MAXIMA then
		return
	end
	local anterior = sesiones[modelo]
	if anterior then
		limpiar(anterior)
	end

	local sesion: Sesion = {
		Personaje = modelo,
		Objetivo = destino,
		Inicio = os.clock(),
		Duracion = duracion,
		EsLocal = esLocal,
		Activa = true,
	}
	sesiones[modelo] = sesion

	Gestor.Reproducir("Escaner_Carga", "Anticipacion", opciones(sesion))
	crearContorno(sesion)

	-- Pulsos y barridos mientras dure el análisis.
	task.spawn(function()
		local ultimoBarrido = -math.huge
		local subir = true
		while sesion.Activa and os.clock() - sesion.Inicio < sesion.Duracion + 0.1 do
			if modelo.Parent == nil or destino.Parent == nil then
				break
			end
			Gestor.Reproducir("Escaner_Pulso", "Lanzamiento", opciones(sesion))
			if os.clock() - ultimoBarrido >= INTERVALO_BARRIDO then
				ultimoBarrido = os.clock()
				barrido(sesion, subir)
				subir = not subir
			end
			task.wait(INTERVALO_PULSO)
		end
	end)
end

local function alCancelar(personaje: any)
	if not esModelo(personaje) then
		return
	end
	local sesion = sesiones[personaje :: Model]
	if sesion == nil then
		return
	end
	local datos = opciones(sesion)
	local llevaDentro = sesion.Activa
	limpiar(sesion)
	if llevaDentro and (sesion.EsLocal or distanciaACamara(datos.Origen) <= DISTANCIA_MAXIMA) then
		Gestor.Reproducir("Escaner_Cancelado", "Impacto", datos)
	end
end

local function alCompletar(personaje: any, objetivo: any, punto: any)
	if not esModelo(personaje) or not esVector(punto) then
		return
	end
	local sesion = sesiones[personaje :: Model]
	local punto3 = punto :: Vector3
	local esLocal = personaje == Players.LocalPlayer.Character
	if not esLocal and distanciaACamara(punto3) > DISTANCIA_MAXIMA then
		if sesion then
			limpiar(sesion)
		end
		return
	end

	local datos = if sesion
		then opciones(sesion)
		else {
			Lanzador = personaje,
			Origen = posicionMano(personaje :: Model),
			Punto = punto3,
			Direccion = (punto3 - posicionMano(personaje :: Model)).Unit,
			EsLocal = esLocal,
			DistanciaMaxima = DISTANCIA_MAXIMA,
		}
	datos.Punto = punto3
	Gestor.Reproducir("Escaner_Completado", { "Impacto", "Residuo" }, datos)

	-- Último destello del contorno: se enciende de golpe y se apaga.
	if sesion then
		local resalte = sesion.Resalte
		if resalte then
			resalte.FillTransparency = 0.1
			resalte.OutlineTransparency = 0
		end
		limpiar(sesion)
	end
	if typeof(objetivo) == "Instance" and Calidad.Permite("Medio") then
		-- Un barrido final, rápido, hacia arriba.
		local falsa: Sesion = {
			Personaje = personaje :: Model,
			Objetivo = objetivo :: Instance,
			Inicio = os.clock(),
			Duracion = 1,
			EsLocal = esLocal,
			Activa = true,
		}
		barrido(falsa, true)
	end
end

-- ===== Minería =====

local function direccionHaciaCamara(punto: Vector3): Vector3
	local camara = workspace.CurrentCamera
	if camara == nil then
		return Vector3.yAxis
	end
	local direccion = camara.CFrame.Position - punto
	return if direccion.Magnitude > 0.01 then direccion.Unit else Vector3.yAxis
end

local function alGolpearMineral(punto: any, tipo: any, _fraccion: any)
	if not esVector(punto) or type(tipo) ~= "string" then
		return
	end
	local receta = `Minado_Golpe_{tipo}`
	if (Paleta :: any)[`Mineral_{tipo}`] == nil then
		return
	end
	Gestor.Reproducir(receta, "Impacto", {
		Punto = punto,
		Direccion = direccionHaciaCamara(punto :: Vector3),
		DistanciaMaxima = 160,
	})
end

local function alRomperMineral(punto: any, tipo: any)
	if not esVector(punto) or type(tipo) ~= "string" or (Paleta :: any)[`Mineral_{tipo}`] == nil then
		return
	end
	Gestor.Reproducir(`Minado_Rotura_{tipo}`, { "Impacto", "Residuo" }, {
		Punto = punto,
		Direccion = direccionHaciaCamara(punto :: Vector3),
		DistanciaMaxima = 260,
		LocalGolpeado = distanciaACamara(punto :: Vector3) < 30, -- el tinte de pantalla solo sale a quien está cerca
	})
end

-- Empieza a escuchar al servidor. Debe llamarse una vez, después de ServicioRed.Iniciar().
function EfectosEscaneo.Iniciar()
	Gestor.RegistrarRecetas(EfectosExploracion)
	ServicioRed.Conectar("EscaneoIniciado", alIniciar)
	ServicioRed.Conectar("EscaneoCancelado", alCancelar)
	ServicioRed.Conectar("EscaneoCompletado", alCompletar)
	ServicioRed.Conectar("MineralGolpeado", alGolpearMineral)
	ServicioRed.Conectar("MineralRoto", alRomperMineral)
end

return EfectosEscaneo
