--!strict
--[[
	Pantalla: los efectos que afectan a TODA la imagen del jugador.

	  Tinte        destello o cambio de color (ColorCorrection: brillo, contraste, saturación, tinte)
	  Desenfoque   Blur de pantalla
	  FOV          campo de visión (zoom de impacto)
	  Sacudida     temblor de cámara, más débil cuanto más lejos ocurre la explosión
	  Hitstop      congela un instante las animaciones de quien golpea y de quien recibe (da "peso" al golpe)
	  Cine         barras negras de cinemática

	Varios efectos a la vez se SUMAN (dos destellos seguidos no se pisan). Cada uno es un "pulso" con su
	curva de entrada, mantenimiento y salida; un único bucle por fotograma los evalúa, y solo está
	conectado mientras hay algo en marcha.

	La cámara se modifica DESPUÉS del script de cámara de Roblox (BindToRenderStep con prioridad de
	cámara + 1), así que no hay que desactivar nada.
]]

local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local Calidad = require(script.Parent.Calidad)
local Utiles = require(script.Parent.Utiles)

type Pulso = {
	Inicio: number,
	Entrada: number,
	Mantener: number,
	Salida: number,
	[string]: any,
}

local Pantalla = {}

local NOMBRE_PASO = "VFX_Camara"

local tintes: { Pulso } = {}
local desenfoques: { Pulso } = {}
local zooms: { Pulso } = {}
local sacudidas: { Pulso } = {}
local gancho: ((camara: Camera, dt: number) -> boolean)? = nil -- cinemática de cámara

local correccion: ColorCorrectionEffect? = nil
local desenfoque: BlurEffect? = nil
local fovBase: number? = nil
local conectado = false
local barras: { Frame } = {}

-- ===== Envolvente de un pulso =====

-- Valor 0..1 del pulso en este instante; nil cuando ya ha terminado.
local function envolvente(pulso: Pulso, ahora: number): number?
	local t = ahora - pulso.Inicio
	if t < 0 then
		return 0
	end
	if t < pulso.Entrada then
		return Utiles.Suavizar(t / math.max(pulso.Entrada, 1e-3), "Quad")
	end
	t -= pulso.Entrada
	if t < pulso.Mantener then
		return 1
	end
	t -= pulso.Mantener
	if t < pulso.Salida then
		return 1 - Utiles.Suavizar(t / math.max(pulso.Salida, 1e-3), "Quad")
	end
	return nil
end

-- Quita de la lista los pulsos terminados.
local function limpiar(lista: { Pulso }, ahora: number)
	for indice = #lista, 1, -1 do
		local pulso = lista[indice]
		if ahora - pulso.Inicio >= pulso.Entrada + pulso.Mantener + pulso.Salida then
			table.remove(lista, indice)
		end
	end
end

-- ===== Bucle de cámara y filtros =====

local function hayAlgo(): boolean
	return #tintes > 0 or #desenfoques > 0 or #zooms > 0 or #sacudidas > 0 or gancho ~= nil
end

local function aplicarFiltros(ahora: number)
	local cc = correccion :: ColorCorrectionEffect
	if #tintes > 0 then
		local brillo, contraste, saturacion = 0, 0, 0
		local tinte = Color3.new(1, 1, 1)
		for _, pulso in tintes do
			local peso = envolvente(pulso, ahora) or 0
			brillo += pulso.Brillo * peso
			contraste += pulso.Contraste * peso
			saturacion += pulso.Saturacion * peso
			tinte = tinte:Lerp(pulso.Color, peso)
		end
		cc.Enabled = true
		cc.Brightness = brillo
		cc.Contrast = contraste
		cc.Saturation = saturacion
		cc.TintColor = tinte
	elseif cc.Enabled then
		cc.Enabled = false
	end

	local blur = desenfoque :: BlurEffect
	if #desenfoques > 0 then
		local maximo = 0
		for _, pulso in desenfoques do
			maximo = math.max(maximo, pulso.Tamano * (envolvente(pulso, ahora) or 0))
		end
		blur.Enabled = maximo > 0.1
		blur.Size = maximo
	elseif blur.Enabled then
		blur.Enabled = false
	end
end

local function paso(dt: number)
	local camara = workspace.CurrentCamera
	if camara == nil then
		return
	end
	local ahora = os.clock()

	-- 1. Cinemática (si hay): coloca la cámara.
	if gancho then
		local sigue = gancho(camara, dt)
		if not sigue then
			gancho = nil
		end
	end

	-- 2. Zoom (FOV).
	if #zooms > 0 then
		if fovBase == nil then
			fovBase = camara.FieldOfView
		end
		local delta = 0
		for _, pulso in zooms do
			delta += pulso.Delta * (envolvente(pulso, ahora) or 0)
		end
		camara.FieldOfView = (fovBase :: number) + delta
	elseif fovBase ~= nil then
		camara.FieldOfView = fovBase
		fovBase = nil
	end

	-- 3. Sacudida: se suma sobre la posición actual de la cámara (sin acumularse de un fotograma a otro).
	if #sacudidas > 0 then
		local posicionCamara = camara.CFrame.Position
		local ex, ey, ez, px, py = 0, 0, 0, 0, 0
		for _, pulso in sacudidas do
			local t = ahora - pulso.Inicio
			local total = pulso.Entrada + pulso.Mantener + pulso.Salida
			local atenuacion = math.max(0, 1 - t / total) ^ 2
			local lejania = 1
			if pulso.Origen and pulso.Radio then
				lejania = math.clamp(1 - (posicionCamara - pulso.Origen).Magnitude / pulso.Radio, 0, 1) ^ 1.5
			end
			local fuerza = pulso.Intensidad * atenuacion * lejania
			local x = t * pulso.Frecuencia
			ex += math.noise(x, pulso.Semilla, 0) * fuerza * 0.03
			ey += math.noise(x, pulso.Semilla, 10) * fuerza * 0.03
			ez += math.noise(x, pulso.Semilla, 20) * fuerza * 0.015
			px += math.noise(x, pulso.Semilla, 30) * fuerza * 0.1
			py += math.noise(x, pulso.Semilla, 40) * fuerza * 0.1
		end
		camara.CFrame = camara.CFrame * CFrame.new(px, py, 0) * CFrame.Angles(ex, ey, ez)
	end

	aplicarFiltros(ahora)

	for _, lista in { tintes, desenfoques, zooms, sacudidas } do
		limpiar(lista, ahora)
	end

	if not hayAlgo() then
		-- Nada en marcha: se desconecta hasta el próximo efecto.
		RunService:UnbindFromRenderStep(NOMBRE_PASO)
		conectado = false
		aplicarFiltros(ahora)
	end
end

local function asegurarConectado()
	if not conectado then
		conectado = true
		RunService:BindToRenderStep(NOMBRE_PASO, Enum.RenderPriority.Camera.Value + 1, paso)
	end
end

local function nuevoPulso(params: any, extra: { [string]: any }): Pulso
	local pulso: any = {
		Inicio = os.clock(),
		Entrada = params.Entrada or 0.05,
		Mantener = params.Mantener or 0.05,
		Salida = params.Salida or 0.4,
	}
	for clave, valor in extra do
		pulso[clave] = valor
	end
	return pulso :: Pulso
end

-- ===== API =====

-- Crea los filtros de pantalla. Debe llamarse una vez al arrancar.
function Pantalla.Iniciar()
	local cc = Instance.new("ColorCorrectionEffect")
	cc.Name = "VFX_Color"
	cc.Enabled = false
	cc.Parent = Lighting
	correccion = cc

	local blur = Instance.new("BlurEffect")
	blur.Name = "VFX_Blur"
	blur.Size = 0
	blur.Enabled = false
	blur.Parent = Lighting
	desenfoque = blur
end

--[[
	Destello o cambio de color.
	  Brillo, Contraste, Saturacion  cuánto se suma en el punto máximo (p. ej. Brillo = 0.6 es un flash)
	  Color    tinte (Color3)
	  Entrada, Mantener, Salida  segundos
]]
function Pantalla.Tinte(params: any, color: Color3)
	table.insert(
		tintes,
		nuevoPulso(params, {
			Brillo = params.Brillo or 0,
			Contraste = params.Contraste or 0,
			Saturacion = params.Saturacion or 0,
			Color = color,
		})
	)
	asegurarConectado()
end

function Pantalla.Desenfoque(params: any)
	if Calidad.Factor("Desenfoque") <= 0 then
		return
	end
	table.insert(desenfoques, nuevoPulso(params, { Tamano = params.Tamano or 12 }))
	asegurarConectado()
end

-- Zoom: `Delta` grados que se suman al campo de visión (negativo = acercar).
function Pantalla.FOV(params: any)
	table.insert(zooms, nuevoPulso(params, { Delta = params.Delta or -10 }))
	asegurarConectado()
end

--[[
	Temblor de cámara.
	  Intensidad  fuerza (1 = leve, 5 = fuerte, 10 = brutal)
	  Duracion    segundos
	  Frecuencia  sacudidas por segundo (20)
	  origen, radio  si se indican, el temblor se debilita con la distancia desde `origen` hasta `radio`
]]
function Pantalla.Sacudida(params: any, origen: Vector3?)
	local duracion: number = params.Duracion or 0.5
	table.insert(
		sacudidas,
		nuevoPulso({ Entrada = 0, Mantener = 0, Salida = duracion }, {
			Intensidad = params.Intensidad or 3,
			Frecuencia = params.Frecuencia or 20,
			Semilla = Utiles.Azar:NextNumber(0, 1000),
			Origen = origen,
			Radio = if origen then (params.Radio or 140) else nil,
		})
	)
	asegurarConectado()
end

--[[
	Registra una cinemática de cámara: `funcion(camara, dt)` se llama cada fotograma después del script de
	cámara de Roblox y devuelve `true` mientras siga activa. Solo puede haber una.
]]
function Pantalla.ControlarCamara(funcion: (camara: Camera, dt: number) -> boolean)
	gancho = funcion
	asegurarConectado()
end

-- Pistas congeladas ahora mismo: su velocidad original y cuántos hitstops las tienen congeladas.
local congeladas: { [AnimationTrack]: { Velocidad: number, Cuenta: number } } = {}

-- Congela un instante las animaciones de los personajes indicados (hitstop). Admite solaparse.
function Pantalla.Hitstop(modelos: { Model }, duracion: number)
	local mias: { AnimationTrack } = {}
	for _, modelo in modelos do
		local humanoid = modelo:FindFirstChildOfClass("Humanoid")
		local animador = humanoid and humanoid:FindFirstChildOfClass("Animator")
		if animador then
			for _, pista in animador:GetPlayingAnimationTracks() do
				local estado = congeladas[pista]
				if estado then
					estado.Cuenta += 1
				else
					congeladas[pista] = { Velocidad = pista.Speed, Cuenta = 1 }
					pista:AdjustSpeed(0.02)
				end
				table.insert(mias, pista)
			end
		end
	end
	task.delay(duracion, function()
		for _, pista in mias do
			local estado = congeladas[pista]
			if estado then
				estado.Cuenta -= 1
				if estado.Cuenta <= 0 then
					pista:AdjustSpeed(estado.Velocidad)
					congeladas[pista] = nil
				end
			end
		end
	end)
end

-- Barras negras de cinemática: entran (true) o salen (false) en `segundos`.
function Pantalla.Cine(activar: boolean, segundos: number?)
	if #barras == 0 then
		local jugador = Players.LocalPlayer
		local gui = Instance.new("ScreenGui")
		gui.Name = "VFXCine"
		gui.IgnoreGuiInset = true
		gui.ResetOnSpawn = false
		gui.DisplayOrder = 40
		for indice = 1, 2 do
			local barra = Instance.new("Frame")
			barra.BorderSizePixel = 0
			barra.BackgroundColor3 = Color3.new(0, 0, 0)
			barra.AnchorPoint = Vector2.new(0, if indice == 1 then 0 else 1)
			barra.Position = UDim2.fromScale(0, if indice == 1 then 0 else 1)
			barra.Size = UDim2.fromScale(1, 0)
			barra.Parent = gui
			table.insert(barras, barra)
		end
		gui.Parent = jugador:WaitForChild("PlayerGui")
	end
	for _, barra in barras do
		Utiles.Tween(barra, segundos or 0.5, { Size = UDim2.fromScale(1, if activar then 0.11 else 0) }, "Quad")
	end
end

return Pantalla
