--!strict
--[[
	Camara: cinemáticas de cámara de las habilidades definitivas.

	Una cinemática (Datos/Cinematicas) es una lista de PLANOS. Cada plano mueve la cámara de un punto a
	otro durante unos segundos, mirando a un objetivo, con su propio zoom (FOV):

	  { Duracion = 1.2, Easing = "Cubic",
	    Desde = { Pos = { Ancla = "Lanzador", Desplazamiento = { 5, 3, 10 } }, Mirar = { Ancla = "Lanzador" }, FOV = 60 },
	    Hasta = { Pos = ..., Mirar = ..., FOV = 80 } }

	Los puntos son "anclas" (ver Utiles.Ancla), que se evalúan en cada fotograma: si el lanzador se mueve, la
	cámara lo acompaña. Si el plano no tiene `Hasta`, la cámara se queda quieta en `Desde`.

	Solo la cinemática del propio jugador toma la cámara. Al terminar (o si el lanzador muere) se devuelve
	el control al juego sin saltos.
]]

local Players = game:GetService("Players")

local Pantalla = require(script.Parent.Pantalla)
local Utiles = require(script.Parent.Utiles)

local Camara = {}

local activa = false

-- Posición y mirada de un extremo del plano.
local function resolver(ctx: any, extremo: any): (Vector3, Vector3, number?)
	local posicion = Utiles.Ancla(ctx, extremo.Pos.Ancla, extremo.Pos.Desplazamiento).Position
	local mirar = extremo.Mirar or { Ancla = "Objetivo" }
	local objetivo = Utiles.Ancla(ctx, mirar.Ancla, mirar.Desplazamiento).Position
	return posicion, objetivo, extremo.FOV
end

--[[
	Reproduce la cinemática `definicion` en la cámara del jugador. `ctx` es el contexto de la habilidad
	(lanzador, destino...). Devuelve su duración total en segundos.
]]
function Camara.Reproducir(definicion: any, ctx: any): number
	if activa then
		return 0
	end
	local camara = workspace.CurrentCamera
	if camara == nil then
		return 0
	end

	local planos: { any } = definicion.Planos
	local total = 0
	for _, plano in planos do
		total += plano.Duracion
	end

	activa = true
	local tipoOriginal = camara.CameraType
	local fovOriginal = camara.FieldOfView
	local inicio = os.clock()
	local humanoid = if ctx.Lanzador then ctx.Lanzador:FindFirstChildOfClass("Humanoid") else nil

	if definicion.Barras ~= false then
		Pantalla.Cine(true, 0.45)
	end
	camara.CameraType = Enum.CameraType.Scriptable

	Pantalla.ControlarCamara(function(cam, _)
		local t = os.clock() - inicio
		local muerto = humanoid ~= nil and humanoid.Health <= 0
		if t >= total or muerto or ctx.Cancelado then
			-- Devuelve la cámara al juego.
			activa = false
			cam.CameraType = tipoOriginal
			cam.FieldOfView = fovOriginal
			if humanoid then
				cam.CameraSubject = humanoid
			end
			if definicion.Barras ~= false then
				Pantalla.Cine(false, 0.5)
			end
			return false
		end

		-- Plano actual y avance dentro de él.
		local acumulado = 0
		for _, plano in planos do
			if t < acumulado + plano.Duracion then
				local alfa = Utiles.Suavizar((t - acumulado) / plano.Duracion, plano.Easing or "Quad")
				local posA, objA, fovA = resolver(ctx, plano.Desde)
				local posicion, objetivo, fov = posA, objA, fovA
				if plano.Hasta then
					local posB, objB, fovB = resolver(ctx, plano.Hasta)
					posicion = posA:Lerp(posB, alfa)
					objetivo = objA:Lerp(objB, alfa)
					if fovA and fovB then
						fov = fovA + (fovB - fovA) * alfa
					end
				end
				cam.CFrame = CFrame.lookAt(posicion, objetivo)
				cam.FieldOfView = fov or fovOriginal
				break
			end
			acumulado += plano.Duracion
		end
		return true
	end)

	return total
end

-- ¿Hay una cinemática en marcha?
function Camara.Activa(): boolean
	return activa
end

return Camara
