--!strict
--[[
	Ambiente (Planetas, cliente): la luz, el cielo y la atmósfera según la zona en la que está el jugador.

	EL PROBLEMA: en Roblox, Lighting es GLOBAL. Hay una sola luz direccional (el sol o la luna del cielo), un solo
	cielo y una sola atmósfera para todo el lugar. No se puede poner "un sol aquí y un agujero negro allí".

	LA SOLUCIÓN: cada cliente ajusta SU Lighting según dónde está SU cámara (los cambios de Lighting hechos en un
	cliente no se replican a nadie):

	  1. Se calcula el preset que toca (Planetas/Datos/Iluminacion): en el espacio, una mezcla de EspacioProfundo,
	     EspacioHumanos y EspacioMonstruos según la distancia al sol y al agujero negro; en una superficie, el suyo.
	  2. La luz direccional apunta HACIA la fuente real: en el espacio, al sol o al agujero negro (o una mezcla
	     suave entre los dos); en una superficie, a la dirección en que se ve su sol en ese cielo. Así los planetas
	     tienen un lado iluminado y otro en sombra, y la sombra cae del lado correcto.
	  3. Roblox no deja fijar esa dirección directamente: sale de ClockTime y GeographicLatitude. Al arrancar se
	     prepara una tabla preguntando a Lighting (GetSunDirection / GetMoonDirection) por muchas combinaciones, y
	     después Planetas/Luz.Resolver busca la que apunta hacia donde se quiere. No se depende de la fórmula
	     interna de Roblox: se mide.
	  4. En el espacio la luz es la LUNA (Fuente = "Luna"): así el cielo sigue negro y con estrellas aunque la luz
	     venga de un lado. En la superficie humana es el SOL (cielo azul de día).
	  5. Todo cambia con una transición suave (Ajustes.Rapidez). Al cambiar de zona (aterrizar o despegar, con la
	     pantalla en negro) se salta directamente al preset nuevo.

	Límite conocido: la luz direccional de Roblox no puede venir de debajo del horizonte. Si la fuente está por
	debajo (por ejemplo, volando por encima del sol), se usa la misma dirección subida a ElevacionMinima grados.
]]

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Datos = require(Shared.Planetas.Datos)
local DatosLuz = require(Shared.Planetas.Datos.Iluminacion)
local Espacio = require(Shared.Planetas.Espacio)
local Luz = require(Shared.Planetas.Luz)
local V = require(Shared.Planetas.Vectores)
local Experimento = require(Shared.Experimentos.PlanetaRedondo)

-- EXPERIMENTO planeta redondo: por debajo de esta altura sobre su superficie se usa la luz de superficie.
local ALTURA_LUZ_SUPERFICIE = 1200

type Vec = V.Vec

local Ambiente = {}

local ajustes = DatosLuz.Ajustes
local presets = DatosLuz.Presets

local INTERVALO_MEZCLA = 0.1 -- segundos entre dos cálculos de la mezcla de presets

local iniciado = false
local tabla: { Luz.Muestra }? = nil
local actual: any = nil -- preset aplicado ahora mismo
local direccionActual: Vec? = nil
local direccionResuelta: Vec? = nil
local fuenteResuelta: string? = nil
local proximaOrientacion = 0
local acumulado = 0
local zonaAnterior: Espacio.Zona? = nil

local resplandor: BloomEffect? = nil
local rayos: SunRaysEffect? = nil
local atmosfera: Atmosphere? = nil
local cielo: Sky? = nil
local correccion: ColorCorrectionEffect? = nil

local function color(hex: string): Color3
	return Color3.fromHex(hex)
end

local function aVec(v: Vector3): Vec
	return { X = v.X, Y = v.Y, Z = v.Z }
end

-- Lo que vale Lighting para una hora y una latitud (cambia Lighting un instante; luego se pone lo bueno).
local function evaluar(hora: number, latitud: number): (Vec, Vec)
	Lighting.ClockTime = hora
	Lighting.GeographicLatitude = latitud
	return aVec(Lighting:GetSunDirection()), aVec(Lighting:GetMoonDirection())
end

-- ===== Preset y dirección que tocan =====

local function objetivoDe(zona: Espacio.Zona, posicion: Vec): (any, Vec)
	-- EXPERIMENTO planeta redondo: cerca de su superficie se usa la luz de superficie (cielo de día) en el lado que da
	-- al Sol y la del espacio (noche) en el otro, con la dirección real del Sol. Cada cliente pone la suya.
	if Experimento.Activado() then
		local centro = Experimento.Centro()
		local desde = Vector3.new(posicion.X, posicion.Y, posicion.Z) - centro
		if desde.Magnitude - Experimento.Radio < ALTURA_LUZ_SUPERFICIE then
			local direccion = Luz.DireccionEspacio(posicion)
			local arriba = desde.Unit
			local deDia = arriba.X * direccion.X + arriba.Y * direccion.Y + arriba.Z * direccion.Z > -0.05
			if deDia then
				-- Hora dorada: el sol, como mucho a ElevacionMaximaSuperficie grados sobre el horizonte de aquí.
				direccion = Luz.TopeElevacion(direccion, aVec(arriba), ajustes.ElevacionMaximaSuperficie)
			end
			return presets[if deDia then "SuperficieHumanos" else "EspacioHumanos"], direccion
		end
	end
	if zona.Tipo == "Superficie" and zona.Planeta then
		local planeta = zona.Planeta :: string
		local preset = presets[Datos.Planetas[planeta].Superficie.Iluminacion]
		local _, fuente = Espacio.FuenteDeLuz(planeta)
		local direccion = Espacio.DireccionEnCielo(planeta, fuente)
		if preset.Fuente == "Sol" then
			direccion = Luz.TopeElevacion(direccion, { X = 0, Y = 1, Z = 0 }, ajustes.ElevacionMaximaSuperficie)
		end
		return preset, direccion
	end
	local nombres, pesos = Luz.PesosEspacio(posicion)
	local lista = {}
	for indice, nombre in nombres do
		lista[indice] = presets[nombre]
	end
	return Luz.Mezclar(lista, pesos), Luz.DireccionEspacio(posicion)
end

-- ===== Aplicar =====

local function aplicarPreset(p: any)
	Lighting.Brightness = p.Brillo
	Lighting.Ambient = color(p.Ambiente)
	Lighting.OutdoorAmbient = color(p.AmbienteExterior)
	Lighting.ExposureCompensation = p.Exposicion
	Lighting.ColorShift_Top = color(p.TonoLuz)
	Lighting.EnvironmentDiffuseScale = p.Difusa
	Lighting.EnvironmentSpecularScale = p.Especular
	Lighting.ShadowSoftness = p.SombrasSuaves

	local b = resplandor :: BloomEffect
	b.Intensity = p.Resplandor.Intensidad
	b.Size = p.Resplandor.Tamano
	b.Threshold = p.Resplandor.Umbral
	local r = rayos :: SunRaysEffect
	r.Intensity = p.RayosSol.Intensidad
	r.Spread = p.RayosSol.Dispersion

	local a = atmosfera :: Atmosphere
	local datosAtmosfera = p.Atmosfera
	if datosAtmosfera.Densidad <= 0.001 then
		a.Parent = nil -- sin atmósfera (en el espacio)
	else
		a.Density = datosAtmosfera.Densidad
		a.Offset = datosAtmosfera.Desfase
		a.Color = color(datosAtmosfera.Color)
		a.Decay = color(datosAtmosfera.Decaimiento)
		a.Glare = datosAtmosfera.Brillo
		a.Haze = datosAtmosfera.Bruma
		a.Parent = Lighting
	end

	local s = cielo :: Sky
	s.StarCount = math.floor(p.Cielo.Estrellas)
	s.CelestialBodiesShown = p.Cielo.Astros

	local c = correccion :: ColorCorrectionEffect
	c.TintColor = color(p.Color.Tinte)
	c.Saturation = p.Color.Saturacion
	c.Contrast = p.Color.Contraste
	c.Brightness = p.Color.Brillo
end

-- Orienta la luz hacia `direccion` con la fuente del preset ("Sol" o "Luna").
local function orientar(direccion: Vec, fuente: string)
	local t = tabla
	if t == nil then
		return -- todavía calibrando
	end
	local objetivo = Luz.LimitarElevacion(direccion, ajustes.ElevacionMinima)
	if
		fuenteResuelta == fuente
		and direccionResuelta
		and V.angulo(objetivo, direccionResuelta :: Vec) < ajustes.UmbralGrados
	then
		return
	end
	local hora, latitud, errorGrados =
		Luz.Resolver(objetivo, fuente, evaluar, t, ajustes.PasoHora, ajustes.PasoLatitud, ajustes.Refinados)
	Lighting.ClockTime = hora
	Lighting.GeographicLatitude = latitud
	direccionResuelta = objetivo
	fuenteResuelta = fuente
	if errorGrados > 3 then
		warn(`[Ambiente] La luz apunta con {math.floor(errorGrados)}° de error ({fuente})`)
	end
end

local function paso(dt: number)
	local camara = workspace.CurrentCamera
	if camara == nil then
		return
	end
	acumulado += dt
	if acumulado < INTERVALO_MEZCLA and actual ~= nil then
		return
	end
	local transcurrido = acumulado
	acumulado = 0

	local posicion = aVec(camara.CFrame.Position)
	local zona = Espacio.ZonaDe(posicion)
	local objetivo, direccion = objetivoDe(zona, posicion)

	-- Al cambiar de zona (transición con la pantalla en negro) se salta sin mezcla.
	local salto = actual == nil or zonaAnterior == nil or not Espacio.MismaZona(zonaAnterior :: Espacio.Zona, zona)
	zonaAnterior = zona
	if salto then
		actual = Luz.Mezclar({ objetivo }, { 1 })
		direccionActual = V.unitario(direccion)
		direccionResuelta = nil
	else
		actual = Luz.Acercar(actual, objetivo, transcurrido, ajustes.Rapidez)
		local alfa = 1 - math.exp(-ajustes.Rapidez * transcurrido)
		direccionActual = V.unitario(V.mezclar(direccionActual :: Vec, V.unitario(direccion), alfa))
	end
	aplicarPreset(actual)

	local ahora = os.clock()
	if salto or ahora >= proximaOrientacion then
		proximaOrientacion = ahora + 1 / ajustes.HzOrientacion
		orientar(direccionActual :: Vec, actual.Fuente)
	end
end

-- Prepara la tabla de calibración repartiendo el trabajo entre fotogramas.
local function calibrar()
	local antesHora, antesLatitud = Lighting.ClockTime, Lighting.GeographicLatitude
	local nueva = Luz.CrearTabla(evaluar, ajustes.PasoHora, ajustes.PasoLatitud, function()
		Lighting.ClockTime, Lighting.GeographicLatitude = antesHora, antesLatitud
		task.wait()
	end)
	tabla = nueva
	direccionResuelta = nil
end

-- Empieza a ajustar la iluminación cada fotograma. Debe llamarse una vez.
function Ambiente.Iniciar()
	if iniciado then
		return
	end
	iniciado = true

	local nuevaAtmosfera = Instance.new("Atmosphere")
	nuevaAtmosfera.Name = "AtmosferaPlaneta"
	atmosfera = nuevaAtmosfera

	-- Un cielo propio: si el lugar ya tiene uno, se aparta (dos Sky a la vez no se sabe cuál se usa).
	for _, hijo in Lighting:GetChildren() do
		if hijo:IsA("Sky") then
			hijo.Parent = nil
		end
	end
	local nuevoCielo = Instance.new("Sky")
	nuevoCielo.Name = "CieloPlaneta"
	nuevoCielo.Parent = Lighting
	cielo = nuevoCielo

	-- Resplandor y rayos de sol: se reutiliza el efecto que ya haya en Lighting (así no se duplica) o se crea.
	local nuevoResplandor = Lighting:FindFirstChildOfClass("BloomEffect") or Instance.new("BloomEffect")
	nuevoResplandor.Parent = Lighting
	resplandor = nuevoResplandor
	local nuevosRayos = Lighting:FindFirstChildOfClass("SunRaysEffect") or Instance.new("SunRaysEffect")
	nuevosRayos.Name = "RayosPlaneta"
	nuevosRayos.Parent = Lighting
	rayos = nuevosRayos

	local nuevaCorreccion = Instance.new("ColorCorrectionEffect")
	nuevaCorreccion.Name = "ColorPlaneta"
	nuevaCorreccion.Parent = Lighting
	correccion = nuevaCorreccion

	task.spawn(calibrar)
	RunService.Heartbeat:Connect(paso)
end

-- Fuerza a recalcular todo en el siguiente fotograma (tras una transición).
function Ambiente.Reiniciar()
	actual = nil
	zonaAnterior = nil
	direccionResuelta = nil
	acumulado = INTERVALO_MEZCLA
end

return Ambiente
