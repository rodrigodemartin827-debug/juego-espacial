--!strict
--[[
	Terreno (ServicioPlanetas): escribe en Terrain la superficie de un planeta.

	Las cuentas (altura, material y celdas de cada trozo) las hace Planetas/GeneradorTerreno, que es puro y está
	probado. Aquí solo se traducen los nombres de material a Enum.Material y se llama a Terrain:WriteVoxels,
	TROZO A TROZO y cediendo un fotograma entre trozos (task.wait), para que la generación no congele el servidor.

	El orden de los trozos empieza por el puerto: en unos segundos ya se puede aparecer allí, mientras el resto del
	terreno se sigue generando alrededor. `Generar` avisa con `alPuertoListo` cuando el puerto ya está.

	Con StreamingEnabled el terreno también se transmite por partes a cada cliente: el servidor pide la zona
	(RequestStreamAroundAsync) antes de colocar a alguien en ella (ver ServicioPlanetas).
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Datos = require(ReplicatedStorage.Shared.Planetas.Datos)
local GeneradorTerreno = require(ReplicatedStorage.Shared.Planetas.GeneradorTerreno)

local Terreno = {}

-- Trozos que se escriben seguidos antes de ceder un fotograma.
local TROZOS_POR_FOTOGRAMA = 1

-- Caché de nombre -> Enum.Material (Enum.Material[nombre] lanza un error si el nombre no existe).
local materiales: { [string]: Enum.Material } = {}
local function material(nombre: string): Enum.Material
	local guardado = materiales[nombre]
	if guardado then
		return guardado
	end
	local ok, valor = pcall(function()
		return (Enum.Material :: any)[nombre]
	end)
	local resultado: Enum.Material = if ok and valor then valor else Enum.Material.Rock
	if not ok or valor == nil then
		warn(`[Terreno] Material desconocido '{nombre}': se usa Rock`)
	end
	materiales[nombre] = resultado
	return resultado
end

-- Escribe un trozo ya calculado en el mundo, desplazado al centro de la superficie.
local function escribir(trozo: GeneradorTerreno.Trozo, centro: Vector3, resolucion: number)
	local celdas = trozo.Celdas
	local nombres = trozo.Materiales
	local enumerados = table.create(celdas.X)
	for x = 1, celdas.X do
		local capaNombres = nombres[x]
		local capa = table.create(celdas.Y)
		for y = 1, celdas.Y do
			local filaNombres = capaNombres[y]
			local fila = table.create(celdas.Z)
			for z = 1, celdas.Z do
				fila[z] = material(filaNombres[z])
			end
			capa[y] = fila
		end
		enumerados[x] = capa
	end
	local minimo = centro + Vector3.new(trozo.Origen.X, trozo.Origen.Y, trozo.Origen.Z)
	local maximo = minimo + Vector3.new(celdas.X, celdas.Y, celdas.Z) * resolucion
	local region = Region3.new(minimo, maximo):ExpandToGrid(resolucion)
	workspace.Terrain:WriteVoxels(region, resolucion, enumerados, trozo.Ocupacion)
end

--[[
	Genera la superficie del planeta `id`. Cede entre trozos, así que conviene llamarla con task.spawn.
	`alPuertoListo` se llama una vez, en cuanto están escritos todos los trozos que rodean el puerto.
	Devuelve el número de trozos escritos.
]]
function Terreno.Generar(id: string, alPuertoListo: (() -> ())?): number
	local planeta = Datos.Planetas[id]
	local superficie = planeta.Superficie
	local parametros = superficie.Terreno
	local c = superficie.Centro
	local centro = Vector3.new(c.X, c.Y, c.Z)
	local generador = GeneradorTerreno.nuevo(parametros, superficie.Tamano, planeta.Puerto.Posicion)

	-- El puerto está listo cuando se han escrito todos los trozos a menos de esta distancia de él.
	local anchoTrozo = parametros.Trozo * parametros.Resolucion
	local radioPuerto = parametros.PuertoRadioPlano + parametros.PuertoTransicion + anchoTrozo
	local mitad = superficie.Tamano / 2
	local puerto = planeta.Puerto.Posicion
	local avisado = false

	local inicio = os.clock()
	local lista = generador:Trozos()
	for indice, t in lista do
		local trozo = generador:Trozo(t.I, t.J)
		local ok, err = pcall(escribir, trozo, centro, parametros.Resolucion)
		if not ok then
			warn(`[Terreno] No se pudo escribir el trozo {t.I},{t.J} de {id}: {err}`)
		end

		if not avisado then
			-- La lista va ordenada por distancia al puerto: cuando el siguiente ya queda lejos, el puerto está.
			local siguiente = lista[indice + 1]
			local lejos = true
			if siguiente then
				local cx = -mitad + (siguiente.I + 0.5) * anchoTrozo - puerto.X
				local cz = -mitad + (siguiente.J + 0.5) * anchoTrozo - puerto.Z
				lejos = math.sqrt(cx * cx + cz * cz) > radioPuerto
			end
			if lejos then
				avisado = true
				if alPuertoListo then
					task.spawn(alPuertoListo)
				end
			end
		end

		if indice % TROZOS_POR_FOTOGRAMA == 0 then
			task.wait()
		end
	end
	print(`[Terreno] Superficie de {planeta.Nombre}: {#lista} trozos en {math.floor(os.clock() - inicio)} s`)
	return #lista
end

return Terreno
