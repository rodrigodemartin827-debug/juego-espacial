--!strict
--[[
	Gestor (VFX): reproduce los efectos de una habilidad por FASES.

	Cada habilidad tiene una receta en Datos/EfectosVFX con hasta cinco fases, y cada fase es una lista de
	CAPAS que se disparan a la vez (cada una con su propio `Retraso`):

	  Anticipacion  desde que el servidor acepta la habilidad: carga, aura, destellos de aviso
	  Lanzamiento   cuando termina la carga y sale el poder: proyectil, rayo, onda de salida
	  Impacto       cuando el servidor confirma el golpe: explosión, ondas, escombros, cráter, pantalla
	  Residuo       lo que queda después: humo, chispas, brasas, luz que se apaga
	  Golpeado      se repite sobre CADA enemigo alcanzado: destello, partículas, reacción

	El gestor solo sabe SECUENCIAR; qué hace cada capa lo decide su módulo (VFX/Capas) y cómo se ve, los datos.

	Cada capa se ejecuta aislada: si una falla, se avisa y las demás siguen. Los efectos lejanos (fuera de
	la vista) se omiten salvo la pantalla; los lentos se aligeran con VFX/Calidad.
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Datos = ReplicatedStorage:WaitForChild("Shared").Combate.Datos
local Cinematicas = require(Datos.Cinematicas)
local EfectosVFX = require(Datos.EfectosVFX)
local Paleta = require(Datos.Paleta)
local Poderes = require(Datos.Poderes)
local Recursos = require(Datos.Recursos)

local Animador = require(script.Parent.Animador)
local Calidad = require(script.Parent.Calidad)
local Camara = require(script.Parent.Camara)
local Formas = require(script.Parent.Capas.Formas)
local Haz = require(script.Parent.Capas.Haz)
local Movimiento = require(script.Parent.Capas.Movimiento)
local Pantalla = require(script.Parent.Pantalla)
local Particulas = require(script.Parent.Capas.Particulas)
local Pool = require(script.Parent.Pool)
local Terreno = require(script.Parent.Capas.Terreno)
local Utiles = require(script.Parent.Utiles)

local Gestor = {}

-- Distancia a partir de la cual un efecto ajeno se omite (salvo los de pantalla).
local DISTANCIA_MAXIMA = 280

local activas: { [Model]: any } = setmetatable({}, { __mode = "k" }) :: any

-- Recetas de otros sistemas que usan este mismo motor (las naves): se registran con Gestor.RegistrarRecetas.
local recetasExtra: { [string]: any } = {}

-- ===== Capas de pantalla y sonido =====

-- ¿Le toca a ESTE jugador ver el efecto de pantalla de la capa?
local function aplicaAlJugador(capa: any, ctx: any, porDefecto: string): boolean
	local para: string = capa.Para or porDefecto
	if para == "Todos" then
		return true
	elseif para == "Lanzador" then
		return ctx.EsLocal
	elseif para == "Golpeados" then
		return ctx.LocalGolpeado == true
	end
	return ctx.EsLocal or ctx.LocalGolpeado == true -- "Implicados"
end

local function capaTinte(capa: any, ctx: any)
	if aplicaAlJugador(capa, ctx, "Implicados") then
		Pantalla.Tinte(capa, Utiles.Color(capa.Color or "Nucleo", ctx.Paleta))
	end
end

local function capaDesenfoque(capa: any, ctx: any)
	if aplicaAlJugador(capa, ctx, "Implicados") then
		Pantalla.Desenfoque(capa)
	end
end

local function capaZoom(capa: any, ctx: any)
	if aplicaAlJugador(capa, ctx, "Implicados") then
		Pantalla.FOV(capa)
	end
end

local function capaSacudida(capa: any, ctx: any)
	if aplicaAlJugador(capa, ctx, "Todos") then
		Pantalla.Sacudida(capa, ctx.Punto)
	end
end

local function capaHitstop(capa: any, ctx: any)
	if not aplicaAlJugador(capa, ctx, "Implicados") then
		return
	end
	local modelos: { Model } = { ctx.Lanzador }
	for _, victima in ctx.Victimas do
		table.insert(modelos, victima)
	end
	Pantalla.Hitstop(modelos, capa.Duracion or 0.08)
end

local function capaSonido(capa: any, ctx: any)
	local id = Recursos.Sonidos[capa.Sonido]
	if id == nil or id == "" then
		return -- sin sonido asignado
	end
	local parte = Pool.Parte("Bola")
	parte.CFrame = Utiles.Ancla(ctx, capa.Anclaje, capa.Desplazamiento)
	local sonido = Instance.new("Sound")
	sonido.SoundId = id
	sonido.Volume = capa.Volumen or 0.8
	sonido.PlaybackSpeed = capa.Velocidad or 1
	sonido.RollOffMaxDistance = 220
	sonido.Parent = parte
	sonido:Play()
	task.delay(8, function()
		sonido:Destroy()
		Pool.Liberar(parte)
	end)
end

-- Tipo de capa -> función que la reproduce. Para añadir un tipo nuevo basta con registrarlo aquí.
local TIPOS: { [string]: (capa: any, ctx: any) -> () } = {
	Particulas = Particulas.Reproducir,
	Onda = Formas.Onda,
	Esfera = Formas.Esfera,
	Luz = Formas.Luz,
	Proyectil = Movimiento.Proyectil,
	Corte = Movimiento.Corte,
	Haz = Haz.Reproducir,
	Escombros = Terreno.Escombros,
	Crater = Terreno.Crater,
	Tinte = capaTinte,
	Desenfoque = capaDesenfoque,
	Zoom = capaZoom,
	Sacudida = capaSacudida,
	Hitstop = capaHitstop,
	Sonido = capaSonido,
}

-- Los tipos que afectan a la pantalla del jugador: no se omiten aunque el efecto quede lejos.
local DE_PANTALLA = { Tinte = true, Desenfoque = true, Zoom = true, Sacudida = true, Hitstop = true }

local function ejecutarCapa(capa: any, ctx: any, fase: string)
	-- Si la habilidad fue interrumpida, las capas de carga y de salida que aún no habían empezado no se reproducen.
	if ctx.Cancelado and (fase == "Anticipacion" or fase == "Lanzamiento") then
		return
	end
	if not Calidad.Permite(capa.Minimo) then
		return
	end
	if ctx.Lejos and not DE_PANTALLA[capa.Tipo] then
		return
	end
	local funcion = TIPOS[capa.Tipo]
	if funcion == nil then
		warn(`[VFX] Tipo de capa desconocido: '{capa.Tipo}' en {ctx.Hab.Efecto}`)
		return
	end
	local ok, motivo = pcall(funcion, capa, ctx)
	if not ok then
		warn(`[VFX] Falló una capa '{capa.Tipo}' de {ctx.Hab.Efecto}: {motivo}`)
	end
end

-- ===== Fases =====

--[[
	Dispara todas las capas de una fase. Las capas con `Retraso` se programan para más tarde.
]]
function Gestor.ReproducirFase(ctx: any, fase: string)
	local capas = ctx.Receta.Fases[fase]
	if capas == nil then
		return
	end
	for _, capa in capas do
		local retraso: number = capa.Retraso or 0
		if retraso <= 0 then
			ejecutarCapa(capa, ctx, fase)
		else
			task.delay(retraso, ejecutarCapa, capa, ctx, fase)
		end
	end
end

-- ===== Contexto =====

local function nuevoContexto(
	hab: Poderes.Habilidad,
	lanzador: Model,
	origen: Vector3,
	destino: Vector3,
	direccion: Vector3
): any
	local receta = EfectosVFX[hab.Efecto]
	local camara = workspace.CurrentCamera
	local jugador = Players.LocalPlayer
	local lejos = false
	if camara then
		lejos = (camara.CFrame.Position - destino).Magnitude > DISTANCIA_MAXIMA
	end
	local esLocal = lanzador == jugador.Character
	return {
		Hab = hab,
		Receta = receta,
		Paleta = Paleta[receta.Paleta],
		Lanzador = lanzador,
		Raiz = lanzador:FindFirstChild("HumanoidRootPart"),
		Origen = origen,
		Destino = destino,
		Punto = destino,
		Direccion = direccion,
		SueloY = (Utiles.Suelo(destino)),
		AlturaCielo = receta.AlturaCielo or 140,
		Carga = hab.Tiempos.Carga,
		Viaje = hab.Tiempos.Viaje,
		Victimas = {},
		EsLocal = esLocal,
		LocalGolpeado = false,
		Lejos = lejos and not esLocal,
		Cancelado = false,
	}
end

-- ¿Queda el punto de impacto fuera de la zona que se dibuja?
local function camaraLejos(ctx: any): boolean
	local camara = workspace.CurrentCamera
	return camara ~= nil and (camara.CFrame.Position - ctx.Punto).Magnitude > DISTANCIA_MAXIMA
end

local function estaMuerto(modelo: Model): boolean
	local humanoid = modelo:FindFirstChildOfClass("Humanoid")
	return humanoid == nil or humanoid.Health <= 0
end

-- ===== API =====

--[[
	El servidor ha aceptado una habilidad: reproduce la animación de carga y las fases de anticipación y
	lanzamiento (esta última cuando termina el tiempo de carga).
]]
function Gestor.Iniciar(idHab: string, lanzador: Model, origen: Vector3, destino: Vector3, direccion: Vector3)
	local hab = Poderes.Obtener(idHab)
	if hab == nil or EfectosVFX[hab.Efecto] == nil then
		return
	end
	local ctx = nuevoContexto(hab, lanzador, origen, destino, direccion)
	activas[lanzador] = ctx

	if hab.Animaciones.Carga then
		Animador.Reproducir(lanzador, hab.Animaciones.Carga)
	end
	Gestor.ReproducirFase(ctx, "Anticipacion")

	if hab.Cinematica and ctx.EsLocal and Cinematicas[hab.Cinematica] then
		Camara.Reproducir(Cinematicas[hab.Cinematica], ctx)
	end

	task.delay(hab.Tiempos.Carga, function()
		if estaMuerto(lanzador) then
			ctx.Cancelado = true
			return
		end
		if hab.Animaciones.Lanzamiento then
			Animador.Reproducir(lanzador, hab.Animaciones.Lanzamiento)
		end
		Gestor.ReproducirFase(ctx, "Lanzamiento")
	end)
end

--[[
	El servidor ha interrumpido al lanzador (aturdido o muerto): se paran sus animaciones de la habilidad y se
	cancelan los efectos de carga y de salida que seguían en marcha (los que siguen a su ancla, los chorros de
	partículas, el proyectil y la cinemática de cámara) o que estaban por empezar.
]]
function Gestor.Interrumpir(lanzador: Model)
	local ctx = activas[lanzador]
	if ctx == nil or ctx.Cancelado then
		return
	end
	ctx.Cancelado = true
	local animaciones = ctx.Hab.Animaciones
	for _, nombre in { animaciones.Carga, animaciones.Lanzamiento } do
		Animador.Detener(lanzador, nombre)
	end
end

-- Destello de color sobre un personaje golpeado (Highlight).
local function destello(victima: Model, color: Color3)
	local resalte = Instance.new("Highlight")
	resalte.FillColor = color
	resalte.OutlineColor = Color3.new(1, 1, 1)
	resalte.FillTransparency = 0.15
	resalte.OutlineTransparency = 0.2
	resalte.DepthMode = Enum.HighlightDepthMode.Occluded
	resalte.Adornee = victima
	resalte.Parent = victima
	Utiles.Tween(resalte, 0.35, { FillTransparency = 1, OutlineTransparency = 1 }, "Quad", true)
	task.delay(0.4, function()
		resalte:Destroy()
	end)
end

--[[
	El servidor confirma el impacto en `punto` y la lista de golpeados: reproduce Impacto, Residuo y, por cada
	golpeado, su fase "Golpeado" con su animación de reacción.
]]
function Gestor.Impacto(idHab: string, lanzador: Model, punto: Vector3, direccion: Vector3, golpeados: { Model })
	local hab = Poderes.Obtener(idHab)
	if hab == nil or EfectosVFX[hab.Efecto] == nil then
		return
	end
	local ctx = activas[lanzador]
	if ctx == nil or ctx.Hab ~= hab then
		ctx = nuevoContexto(hab, lanzador, lanzador:GetPivot().Position, punto, direccion)
	end

	ctx.Punto = punto
	ctx.Direccion = direccion
	ctx.SueloY = (Utiles.Suelo(punto))
	ctx.Victimas = golpeados
	ctx.LocalGolpeado = table.find(golpeados, Players.LocalPlayer.Character :: Model) ~= nil
	ctx.Cancelado = false
	ctx.Lejos = camaraLejos(ctx) and not ctx.EsLocal and not ctx.LocalGolpeado

	Gestor.ReproducirFase(ctx, "Impacto")
	Gestor.ReproducirFase(ctx, "Residuo")

	-- Hitstop: si hay golpeados y este jugador está implicado, se congela un instante a quien golpea y a los golpeados.
	if #golpeados > 0 and (ctx.EsLocal or ctx.LocalGolpeado) and (ctx.Receta.Hitstop or 0) > 0 then
		local modelos: { Model } = { lanzador }
		for _, victima in golpeados do
			table.insert(modelos, victima)
		end
		Pantalla.Hitstop(modelos, ctx.Receta.Hitstop)
	end

	for _, victima in golpeados do
		local copia = table.clone(ctx)
		copia.Victima = victima
		copia.Semillas = nil
		Gestor.ReproducirFase(copia, "Golpeado")
		Animador.Reproducir(victima, "Impacto")
		destello(victima, Utiles.Color("Principal", ctx.Paleta))
	end
end

-- ===== Recetas sin habilidad (otros sistemas) =====

--[[
	Añade recetas de efectos de otro sistema (con el mismo formato que Datos/EfectosVFX). Así el motor no depende
	de quien lo usa: cada sistema registra las suyas al arrancar.
]]
function Gestor.RegistrarRecetas(recetas: { [string]: any })
	for nombre, receta in recetas do
		recetasExtra[nombre] = receta
	end
end

--[[
	Reproduce una receta que no pertenece a una habilidad: disparos, explosiones y propulsores de las naves.

	  receta     nombre de una receta de EfectosVFX o registrada con RegistrarRecetas
	  fases      nombre de una fase ("Impacto") o lista de fases, que se disparan en ese orden
	  opciones   Origen (de dónde sale), Punto (dónde ocurre; por defecto, el origen), Direccion (hacia dónde mira,
	             en 3D), Lanzador (Model con los Attachments que usan las anclas por nombre), Raiz (la parte que
	             sigue el ancla "Lanzador"), Viaje (segundos de vuelo de los proyectiles), Victima, EsLocal,
	             LocalGolpeado y DistanciaMaxima (más lejos que esto, solo se ven los efectos de pantalla)

	Devuelve el contexto: poner `Cancelado = true` en él corta los efectos de carga y de salida que sigan en marcha.
]]
function Gestor.Reproducir(receta: string, fases: string | { string }, opciones: any): any
	local datos = EfectosVFX[receta] or recetasExtra[receta]
	if datos == nil then
		warn(`[VFX] Receta desconocida: '{receta}'`)
		return nil
	end

	local origen: Vector3 = opciones.Origen or opciones.Punto or Vector3.zero
	local punto: Vector3 = opciones.Punto or origen
	local direccion: Vector3 = opciones.Direccion or Vector3.new(0, 0, -1)
	local camara = workspace.CurrentCamera
	local esLocal = opciones.EsLocal == true
	local lejos = camara ~= nil
		and (camara.CFrame.Position - punto).Magnitude > (opciones.DistanciaMaxima or DISTANCIA_MAXIMA)
	local viaje: number = opciones.Viaje or 0.2

	local ctx: any = {
		Hab = { Efecto = receta, Tiempos = { Carga = 0, Viaje = viaje }, Animaciones = {} },
		Receta = datos,
		Paleta = Paleta[datos.Paleta],
		Lanzador = opciones.Lanzador,
		Raiz = opciones.Raiz,
		Origen = origen,
		Destino = punto,
		Punto = punto,
		Direccion = direccion,
		SueloY = punto.Y, -- en el espacio no hay suelo: las capas de terreno usan la altura del propio punto
		AlturaCielo = datos.AlturaCielo or 140,
		Carga = 0,
		Viaje = viaje,
		Victimas = opciones.Victimas or {},
		Victima = opciones.Victima,
		EsLocal = esLocal,
		LocalGolpeado = opciones.LocalGolpeado == true,
		Lejos = lejos and not esLocal,
		Cancelado = false,
		Espacial = true, -- las anclas miran en 3D (con cabeceo) en lugar de solo en horizontal
	}

	local lista: { string } = if type(fases) == "string" then { fases } else fases
	for _, fase in lista do
		Gestor.ReproducirFase(ctx, fase)
	end
	return ctx
end

return Gestor
