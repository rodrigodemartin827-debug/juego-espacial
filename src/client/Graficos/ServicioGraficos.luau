--!strict
--[[
	ServicioGraficos (cliente): aplica el nivel de gráficos y monta la pantalla para elegirlo.

	Es el tercer paso de la entrada (bando → editor → gráficos → cinemática). Al llegar los datos se aplica el nivel
	guardado (o el recomendado); cuando termina el paso anterior:
	  · si hay que mostrar la pantalla (nunca ha elegido, o Studio con el modo de pruebas), se muestra con el nivel
	    guardado o el recomendado marcado, y al pulsar CONTINUAR se guarda y se pasa al siguiente paso;
	  · si no, se aplica el nivel guardado sin enseñar nada.
	`ServicioGraficos.EsperarListo()` bloquea hasta que este paso ha terminado (para el paso siguiente).
	El botón de ajustes vuelve a abrir la pantalla en cualquier momento (sin pasar al bando después).

	Aplicar un nivel solo toca cosas del cliente: VFX/Calidad, sombras, postefectos de Lighting y las distancias y
	la densidad de la región (LodRegion.Ajustes). Ver Graficos/Config.
]]

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Graficos.Config)
local Niveles = require(Shared.Graficos.Niveles)
local Senal = require(Shared.Utilidades.Senal)
local Calidad = require(script.Parent.Parent.VFX.Calidad)
local ServicioDatos = require(script.Parent.Parent.Servicios.ServicioDatos)
local ServicioRed = require(script.Parent.Parent.Servicios.ServicioRed)
local Pantalla = require(script.Parent.Pantalla)
local ServicioEleccion = require(script.Parent.Parent.Eleccion.ServicioEleccion)

local ServicioGraficos = {}

ServicioGraficos.Cambio = Senal.nueva() -- (nivel) cada vez que se aplica un nivel

local iniciado = false
local listo = false
local senalListo = Senal.nueva()
local actual: string? = nil
local decidido = false -- ya se ha decidido qué hacer con los primeros datos

-- ===== Aplicar =====

local function aplicarPostefecto(efecto: Instance, nivel: Config.Nivel)
	if not efecto:IsA("PostEffect") or string.sub(efecto.Name, 1, 4) == "VFX_" then
		return
	end
	efecto.Enabled = table.find(nivel.Postefectos, efecto.ClassName) ~= nil
end

local function ajustesRegion(): any
	local region = ReplicatedStorage:FindFirstChild("Region1")
	local modulo = region and region:FindFirstChild("LodRegion")
	if modulo and modulo:IsA("ModuleScript") then
		local ok, lod = pcall(require, modulo)
		if ok and type(lod) == "table" then
			return (lod :: any).Ajustes
		end
	end
	return nil
end

-- Aplica un nivel ("Baja" | "Media" | "Alta" | "Ultra") en este cliente.
function ServicioGraficos.Aplicar(nombre: string)
	local nivel = Config.Niveles[nombre]
	if nivel == nil then
		return
	end
	actual = nombre
	Calidad.Forzar(nivel.Calidad) -- fijo: el ajuste automático ya no lo baja ni lo sube por su cuenta
	Lighting.GlobalShadows = nivel.Sombras
	for _, efecto in Lighting:GetChildren() do
		aplicarPostefecto(efecto, nivel)
	end
	local region = ajustesRegion()
	if region then
		region.Distancia = nivel.Distancia
		region.Vegetacion = nivel.Vegetacion
		region.Densidad = nivel.Densidad
		region.Arboles = nivel.Arboles
		region.ArbolesLejos = nivel.ArbolesLejos
	end
	ServicioGraficos.Cambio:Disparar(nombre)
end

function ServicioGraficos.Actual(): string?
	return actual
end

-- El nivel recomendado para este dispositivo.
function ServicioGraficos.Recomendado(): string
	local esMovil = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
	local calidadRoblox = 0
	pcall(function()
		local ajustes = UserSettings():GetService("UserGameSettings") :: any
		calidadRoblox = (ajustes.SavedQualityLevel :: EnumItem).Value
	end)
	return Niveles.Recomendado(esMovil, calidadRoblox)
end

-- ===== Pantalla =====

local function terminarPaso()
	if not listo then
		listo = true
		senalListo:Disparar()
	end
end

-- Abre la pantalla. `primeraVez`: es el paso de la entrada (el botón dice CONTINUAR y después viene el bando).
local function abrir(primeraVez: boolean)
	if Pantalla.Abierta() then
		return
	end
	local datos = ServicioDatos.Obtener()
	local guardado = if datos and Niveles.Valido(datos.Graficos) then datos.Graficos else nil
	Pantalla.Abrir({
		Inicial = guardado or ServicioGraficos.Recomendado(),
		Recomendado = ServicioGraficos.Recomendado(),
		PrimeraVez = primeraVez,
		AlProbar = ServicioGraficos.Aplicar, -- al pulsar un nivel se ve el cambio en el mundo
		AlTerminar = function(nivel: string)
			ServicioGraficos.Aplicar(nivel)
			ServicioRed.Enviar("ElegirGraficos", nivel)
			if primeraVez then
				terminarPaso()
			end
		end,
	})
end

-- Abre la pantalla desde los ajustes.
function ServicioGraficos.AbrirAjustes()
	abrir(false)
end

-- ¿Ha terminado el paso de gráficos de la entrada?
function ServicioGraficos.Listo(): boolean
	return listo
end

-- Bloquea hasta que el paso de gráficos de la entrada ha terminado.
function ServicioGraficos.EsperarListo()
	if not listo then
		senalListo:Esperar()
	end
end

local function alRecibirDatos(datos: any)
	if decidido then
		return
	end
	decidido = true
	local guardado = if Niveles.Valido(datos.Graficos) then datos.Graficos else nil
	ServicioGraficos.Aplicar(guardado or ServicioGraficos.Recomendado())
	if Niveles.HayQueMostrar(datos.Graficos, RunService:IsStudio()) then
		-- Después del paso anterior de la entrada (de momento, el bando; el editor irá entre los dos).
		task.spawn(function()
			ServicioEleccion.EsperarFin()
			abrir(true)
		end)
	else
		terminarPaso()
	end
end

-- Arranca. Una vez, después de ServicioDatos.Iniciar().
function ServicioGraficos.Iniciar()
	if iniciado then
		return
	end
	iniciado = true
	-- Los postefectos que aparezcan después (los de los planetas, por ejemplo) también siguen el nivel.
	Lighting.ChildAdded:Connect(function(efecto)
		local nivel = actual and Config.Niveles[actual]
		if nivel then
			aplicarPostefecto(efecto, nivel)
		end
	end)
	ServicioDatos.Actualizados:Conectar(alRecibirDatos)
	local datos = ServicioDatos.Obtener()
	if datos ~= nil then
		alRecibirDatos(datos)
	end
	Pantalla.CrearBotonAjustes(ServicioGraficos.AbrirAjustes)
	-- Nunca bloquea la entrada: si los datos no llegan, se sigue con el recomendado.
	task.delay(20, function()
		if not decidido then
			decidido = true
			ServicioGraficos.Aplicar(ServicioGraficos.Recomendado())
			terminarPaso()
		end
	end)
end

return ServicioGraficos
