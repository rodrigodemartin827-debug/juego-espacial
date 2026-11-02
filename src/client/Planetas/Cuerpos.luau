--!strict
--[[
	Cuerpos (Planetas, cliente): coloca los planetas, el sol y el agujero negro donde se ven.

	EN EL ESPACIO son objetos 3D en su posición real. Pero están a decenas de miles de studs, y tan lejos el motor
	puede dejar de dibujarlos o perder precisión. Por eso se usa un "DOBLE":

	  - A menos de Datos.Espacio.DistanciaReal, el cuerpo está en su sitio y a su tamaño real.
	  - Más lejos, se dibuja en la MISMA dirección pero más cerca, encogido en la misma proporción (escala s):
	    a distancia d·s y con tamaño R·s. El tamaño aparente (R/d) es idéntico, la luz le da por el mismo lado y,
	    como no hay nada entre medias a esas distancias, no se nota la diferencia.
	  - La escala se cambia solo cuando se desvía más de un 4 % (reescalar mallas cuesta más que moverlas); entre
	    medias, la posición d·s mantiene el tamaño aparente exacto.

	EN UNA SUPERFICIE (el terreno de un planeta) se ve el CIELO: los cuerpos de Datos.Espacio.Cielo se dibujan a
	DistanciaCielo del jugador, en la dirección en que se verían desde ese punto del planeta
	(Planetas/Espacio.DireccionEnCielo) y girados igual, así que el lado iluminado sigue mirando a su sol.

	Los cuerpos lejanos se recolocan HzLejanos veces por segundo; el cercano, cada fotograma. Todo se mueve con
	workspace:BulkMoveTo (una sola llamada por cuerpo).
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Datos = require(Shared.Planetas.Datos)
local Espacio = require(Shared.Planetas.Espacio)
local Construccion = require(script.Parent.Construccion)

type Cuerpo = Construccion.Cuerpo

type Estado = {
	Cuerpo: Cuerpo,
	Escala: number,
	Visible: boolean,
	Proxima: number,
	Cerca: boolean,
}

local Cuerpos = {}

local DESVIO_ESCALA = 0.04
local NOMBRE_PASO = "PlanetasCuerpos"

local carpeta: Folder? = nil
local estados: { Estado } = {}
local porNombre: { [string]: Estado } = {}
local modo = "Espacio" -- "Espacio" | "Cielo"
local planetaCielo: string? = nil
local inicio = os.clock()
local iniciado = false

local function v3(v: Espacio.Vec): Vector3
	return Vector3.new(v.X, v.Y, v.Z)
end

-- Giro que lleva direcciones del espacio al cielo del terreno de un planeta (ver Espacio.BaseCielo).
local function rotacionCielo(id: string): CFrame
	local este, arriba, sur = Espacio.BaseCielo(id)
	-- Las columnas son las imágenes de los ejes X, Y y Z del espacio en el terreno.
	return CFrame.fromMatrix(
		Vector3.zero,
		Vector3.new(este.X, arriba.X, sur.X),
		Vector3.new(este.Y, arriba.Y, sur.Y),
		Vector3.new(este.Z, arriba.Z, sur.Z)
	)
end

local function ponerVisible(estado: Estado, visible: boolean)
	if estado.Visible == visible then
		return
	end
	estado.Visible = visible
	estado.Cuerpo.Carpeta.Parent = if visible then carpeta else nil
	estado.Proxima = 0
end

-- Coloca todas las piezas del cuerpo con centro, escala y giro dados.
local function colocar(estado: Estado, centro: Vector3, escala: number, giro: CFrame)
	local cuerpo = estado.Cuerpo
	local partes: { BasePart } = table.create(#cuerpo.Elementos)
	local marcos: { CFrame } = table.create(#cuerpo.Elementos)
	local base = CFrame.new(centro) * giro
	for indice, elemento in cuerpo.Elementos do
		local l = elemento.Local
		partes[indice] = elemento.Parte
		marcos[indice] = base * (l - l.Position + l.Position * escala)
		local visible = elemento.Tamano * escala
		if elemento.Aplicado ~= visible then
			elemento.Aplicado = visible
			local malla = elemento.Malla
			if malla then
				malla.Scale = visible / elemento.Parte.Size
			else
				elemento.Parte.Size = visible
			end
		end
	end
	workspace:BulkMoveTo(partes, marcos, Enum.BulkMoveMode.FireCFrameChanged)
	if escala ~= estado.Escala then
		for _, halo in cuerpo.Halos do
			local diametro = halo.Diametro * escala
			halo.Gui.Size = UDim2.fromScale(diametro, diametro)
		end
	end
	estado.Escala = escala
end

local function animar(estado: Estado, t: number, dt: number, cerca: boolean)
	local animacion = estado.Cuerpo.Animar
	if animacion then
		animacion(t, dt, cerca)
	end
	estado.Cerca = cerca
end

local function paso(dt: number)
	local camara = workspace.CurrentCamera
	if camara == nil then
		return
	end
	local ojo = camara.CFrame.Position
	local ahora = os.clock()
	local t = ahora - inicio
	local espacio = Datos.Espacio
	local intervalo = 1 / espacio.HzLejanos

	for _, estado in estados do
		if not estado.Visible then
			continue
		end
		local cuerpo = estado.Cuerpo

		if modo == "Cielo" and planetaCielo then
			if ahora < estado.Proxima then
				continue
			end
			estado.Proxima = ahora + intervalo
			local id = planetaCielo :: string
			local origen = Espacio.PuntoDeAterrizaje(id)
			local real = (cuerpo.Centro - v3(origen)).Magnitude
			local direccion = Espacio.SobreHorizonte(
				Espacio.DireccionEnCielo(id, { X = cuerpo.Centro.X, Y = cuerpo.Centro.Y, Z = cuerpo.Centro.Z }),
				espacio.ElevacionMinimaCielo
			)
			local escala = espacio.DistanciaCielo / math.max(real, 1)
			animar(estado, t, intervalo, false)
			colocar(estado, ojo + v3(direccion) * espacio.DistanciaCielo, escala, rotacionCielo(id))
			continue
		end

		-- En el espacio.
		local hacia = cuerpo.Centro - ojo
		local distancia = hacia.Magnitude
		local cerca = distancia < espacio.DistanciaReal * 1.2
		if not cerca and ahora < estado.Proxima then
			continue
		end
		estado.Proxima = ahora + intervalo
		animar(estado, t, if cerca then dt else intervalo, distancia - cuerpo.Radio < espacio.DistanciaDetalle)

		if distancia <= espacio.DistanciaReal then
			colocar(estado, cuerpo.Centro, 1, CFrame.identity)
		else
			local objetivo = espacio.DistanciaReal / distancia
			local escala = estado.Escala
			if escala <= 0 or escala >= 1 or math.abs(escala / objetivo - 1) > DESVIO_ESCALA then
				escala = objetivo
			end
			colocar(estado, ojo + hacia * escala, escala, CFrame.identity)
		end
	end
end

-- ===== API =====

--[[
	Cambia lo que se ve según la zona del jugador: en el espacio, todos los cuerpos; en una superficie, solo los
	de su cielo. `zona` es la de Planetas/Espacio.ZonaDe.
]]
function Cuerpos.PonerZona(zona: Espacio.Zona)
	if zona.Tipo == "Superficie" and zona.Planeta then
		modo = "Cielo"
		planetaCielo = zona.Planeta
		local visibles: { [string]: boolean } = {}
		local lista: { string } = Datos.Espacio.Cielo[zona.Planeta] or {}
		for _, nombre in lista do
			visibles[nombre] = true
		end
		for nombre, estado in porNombre do
			ponerVisible(estado, visibles[nombre] == true)
			estado.Proxima = 0
		end
	else
		modo = "Espacio"
		planetaCielo = nil
		for _, estado in estados do
			ponerVisible(estado, true)
			estado.Proxima = 0
		end
	end
end

-- Construye los cuerpos y empieza a colocarlos cada fotograma. Debe llamarse una vez.
function Cuerpos.Iniciar()
	if iniciado then
		return
	end
	iniciado = true
	local nueva = Instance.new("Folder")
	nueva.Name = "CuerposCelestes"
	nueva.Parent = workspace
	carpeta = nueva

	local lista = {}
	for _, id in Datos.OrdenPlanetas do
		table.insert(lista, Construccion.Planeta(id, nueva))
	end
	table.insert(lista, Construccion.Sol(nueva))
	table.insert(lista, Construccion.AgujeroNegro(nueva))
	for _, cuerpo in lista do
		-- Escala −1: "aún sin colocar" (así la primera vez se ajustan también los halos).
		local estado: Estado = { Cuerpo = cuerpo, Escala = -1, Visible = true, Proxima = 0, Cerca = true }
		table.insert(estados, estado)
		porNombre[cuerpo.Nombre] = estado
	end

	-- Justo antes de dibujar, después de que la cámara se haya movido en este fotograma.
	RunService:BindToRenderStep(NOMBRE_PASO, Enum.RenderPriority.Camera.Value + 5, paso)
end

return Cuerpos
