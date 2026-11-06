--!strict
--[[
	EXPERIMENTO (servidor): el Terrain esférico del planeta redondo. Ver shared/Experimentos/PlanetaRedondo.

	Generarlo tarda casi un minuto (probado en Studio: 56 s; colinas 41 s y corteza 14 s), así que NO se genera al
	arrancar: se genera UNA vez en Studio (hornearEnStudio) y se guarda con el lugar. Al arrancar, el servidor
	compara la «firma» guardada en el Terrain con la de los ajustes actuales:
	  * coinciden: el terreno ya está, no se hace nada;
	  * no coinciden (se cambiaron los ajustes o no se ha horneado): se genera como antes y se avisa de que hay que
	    volver a hornear en Studio.

	No depende de los servicios del juego: se puede usar desde la barra de comandos de Studio.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Experimento = require(ReplicatedStorage.Shared.Experimentos.PlanetaRedondo)

local TerrenoPlaneta = {}

-- Cambiar si cambia la forma de generar (no los ajustes: esos ya entran en la firma).
TerrenoPlaneta.VERSION = 1
TerrenoPlaneta.ATRIBUTO_FIRMA = "FirmaPlanetaRedondo"

export type Parametros = { centro: Vector3, radio: number, normalPuerto: Vector3 }

local ANGULO_AUREO = math.pi * (3 - math.sqrt(5))

-- Centro, radio de la esfera de Terrain y normal del puerto, a partir de los ajustes.
function TerrenoPlaneta.parametros(): Parametros
	local Datos = require(ReplicatedStorage.Shared.Planetas.Datos) :: any
	local n = Datos.Planetas[Experimento.Planeta].NormalAterrizaje
	return {
		centro = Experimento.Centro(),
		-- La esfera puede ir hundida (Terreno.Hundimiento) para dejar sitio a una región hecha con mallas.
		radio = Experimento.Radio - (Experimento.Terreno.Hundimiento or 0),
		normalPuerto = Vector3.new(n.X, n.Y, n.Z).Unit,
	}
end

-- Texto estable con todo lo que decide el terreno: versión, centro, radio, normal del puerto y ajustes.
local function serializar(v: any): string
	if type(v) == "table" then
		local claves = {}
		for k in v do
			table.insert(claves, tostring(k))
		end
		table.sort(claves)
		local partes = {}
		for _, k in claves do
			local valor = v[k]
			if valor == nil then
				valor = v[tonumber(k)]
			end
			table.insert(partes, k .. "=" .. serializar(valor))
		end
		return "{" .. table.concat(partes, ",") .. "}"
	elseif type(v) == "number" then
		return string.format("%.4f", v)
	end
	return tostring(v)
end

function TerrenoPlaneta.firma(p: Parametros?): string
	local q = p or TerrenoPlaneta.parametros()
	local function vec(x: Vector3)
		return string.format("%.3f,%.3f,%.3f", x.X, x.Y, x.Z)
	end
	return string.format(
		"v%d|%s|%.3f|%s|%s",
		TerrenoPlaneta.VERSION,
		vec(q.centro),
		q.radio,
		vec(q.normalPuerto),
		serializar(Experimento.Terreno)
	)
end

-- ¿Está ya en el lugar el terreno de estos ajustes?
function TerrenoPlaneta.yaGenerado(p: Parametros?): boolean
	return workspace.Terrain:GetAttribute(TerrenoPlaneta.ATRIBUTO_FIRMA) == TerrenoPlaneta.firma(p)
end

-- ===== Generación =====

-- Punto i de n repartidos de forma uniforme sobre la esfera unidad (espiral de Fibonacci).
local function puntoFibonacci(i: number, n: number): Vector3
	local y = 1 - (i + 0.5) * 2 / n
	local r = math.sqrt(math.max(0, 1 - y * y))
	local fi = i * ANGULO_AUREO
	return Vector3.new(math.cos(fi) * r, y, math.sin(fi) * r)
end

local function direccionAleatoria(azar: Random): Vector3
	local y = azar:NextNumber(-1, 1)
	local fi = azar:NextNumber(0, 2 * math.pi)
	local r = math.sqrt(1 - y * y)
	return Vector3.new(math.cos(fi) * r, y, math.sin(fi) * r)
end

local function mat(nombre: string): Enum.Material
	return (Enum.Material :: any)[nombre]
end

-- Material de la superficie en una dirección: casquetes de nieve, y manchas según un ruido 3D.
local function materialEn(n: Vector3, radio: number): Enum.Material
	local t = Experimento.Terreno
	local m = t.Materiales
	local latitud = math.deg(math.asin(math.clamp(n.Y, -1, 1)))
	if math.abs(latitud) > t.LatitudNieve then
		return mat(m.Nieve)
	end
	local p = n * radio * t.EscalaRuido
	local ruido = math.noise(p.X, p.Y + t.Semilla, p.Z)
	if ruido > 0.3 then
		return mat(m.Alta)
	elseif ruido < -0.38 then
		return mat(m.Arena)
	elseif ruido < -0.25 then
		return mat(m.Tierra)
	end
	return mat(m.Base)
end

-- ¿Cae la dirección `n` en la cara del cubo inflado reservada para una región de mallas (Terreno.CaraReservada)?
-- Ahí no se ponen colinas ni rocas: asomarían a través de las mallas de la región.
local function enCaraReservada(n: Vector3): boolean
	local cara = Experimento.Terreno.CaraReservada
	if cara ~= "YP" then
		return false
	end
	return n.Y > math.max(math.abs(n.X), math.abs(n.Z)) - 0.08
end

-- ¿Está la dirección `n` cerca del puerto? (ahí no se ponen colinas ni rocas)
local function cercaDelPuerto(n: Vector3, normalPuerto: Vector3, radio: number, distancia: number): boolean
	return math.acos(math.clamp(n:Dot(normalPuerto), -1, 1)) * radio < distancia
end

--[[
	Genera la esfera de terreno y guarda la firma en el Terrain. Devuelve un resumen con tiempos y cantidades.
	`alAvanzar(fraccion)` (opcional) se llama de vez en cuando con el avance de 0 a 1.
]]
function TerrenoPlaneta.generar(p: Parametros?, alAvanzar: ((number) -> ())?): { [string]: any }
	local q = p or TerrenoPlaneta.parametros()
	local centro, radio, normalPuerto = q.centro, q.radio, q.normalPuerto
	local t = Experimento.Terreno
	local terreno = workspace.Terrain
	local azar = Random.new(t.Semilla)
	local inicio = os.clock()
	-- Se cede el hilo en cuanto se lleva un rato trabajando (si no, Roblox corta el script por tiempo).
	local ultimaPausa = os.clock()
	local area = 4 * math.pi * radio * radio
	local colinas = math.floor(t.ColinasPorMillon * area / 1e6)
	local losas = math.ceil(area / (t.SeparacionLosas * t.SeparacionLosas))
	local rocas = math.floor(t.RocasPorMillon * area / 1e6)
	local total = colinas + losas + rocas + t.PiedrasPuerto
	local hechos = 0
	local function pausa()
		hechos += 1
		if os.clock() - ultimaPausa > t.SegundosPorTanda then
			if alAvanzar then
				alAvanzar(hechos / total)
			end
			task.wait()
			ultimaPausa = os.clock()
		end
	end

	-- 1. Colinas: bolas medio enterradas (cúpulas), más pequeñas que grandes.
	local hechas = 0
	for _ = 1, colinas do
		local n = direccionAleatoria(azar)
		local rmin, rmax = t.RadioColina[1], t.RadioColina[2]
		local r = rmin + (rmax - rmin) * azar:NextNumber() ^ 2
		if enCaraReservada(n) or cercaDelPuerto(n, normalPuerto, radio, 260 + r) then
			pausa()
			continue
		end
		local material = materialEn(n, radio)
		if material == mat(t.Materiales.Arena) then
			material = mat(t.Materiales.Base)
		end
		local centroColina = centro + n * (radio - r * t.Enterrado)
		terreno:FillBall(centroColina, r, material)
		if t.GrosorColina > 0 and r > t.GrosorColina + 8 then
			terreno:FillBall(centroColina, r - t.GrosorColina, Enum.Material.Air)
		end
		-- Las más grandes asoman una cima de roca.
		if r > 250 then
			local cima = centro + n * (radio + r * (1 - t.Enterrado) - r * 0.15)
			terreno:FillBall(cima, r * 0.25, mat(t.Materiales.Roca))
		end
		hechas += 1
		pausa()
	end
	local tiempoColinas = os.clock() - inicio

	-- 2. Corteza: losas tangentes (FillBall no acepta radios tan grandes).
	local tamano = Vector3.new(t.AnchoLosa, t.Grosor, t.AnchoLosa)
	for i = 0, losas - 1 do
		local n = puntoFibonacci(i, losas)
		local marco = Experimento.Marco(centro + n * (radio - t.Grosor / 2), n, Vector3.zAxis)
		terreno:FillBlock(marco, tamano, materialEn(n, radio))
		pausa()
	end
	local tiempoCorteza = os.clock() - inicio - tiempoColinas

	-- 3. Rocas sueltas.
	for _ = 1, rocas do
		local n = direccionAleatoria(azar)
		if enCaraReservada(n) or cercaDelPuerto(n, normalPuerto, radio, 120) then
			pausa()
			continue
		end
		local r = azar:NextNumber(t.RadioRoca[1], t.RadioRoca[2])
		terreno:FillBall(centro + n * (radio + r * 0.15), r, mat(t.Materiales.Roca))
		pausa()
	end

	-- 3b. Piedras pequeñas alrededor del puerto (prueba de pasar por encima sin saltar).
	local referencia = Experimento.Marco(Vector3.zero, normalPuerto, Vector3.zAxis)
	for _ = 1, t.PiedrasPuerto do
		local angulo = azar:NextNumber(0, 2 * math.pi)
		local d = azar:NextNumber(t.ZonaPiedras[1], t.ZonaPiedras[2])
		local tangente = referencia.RightVector * math.cos(angulo) + referencia.LookVector * math.sin(angulo)
		local n = (normalPuerto + tangente * (d / radio)).Unit
		local r = azar:NextNumber(t.RadioPiedra[1], t.RadioPiedra[2])
		terreno:FillBall(centro + n * (radio + r * 0.2), r, mat(t.Materiales.Roca))
		pausa()
	end

	-- 4. Explanada del puerto (pavimento, a ras del suelo).
	local marcoPlano = Experimento.Marco(centro + normalPuerto * (radio - 4), normalPuerto, Vector3.zAxis)
	terreno:FillBlock(marcoPlano, Vector3.new(220, 8, 220), Enum.Material.Pavement)

	terreno:SetAttribute(TerrenoPlaneta.ATRIBUTO_FIRMA, TerrenoPlaneta.firma(q))
	return {
		Losas = losas,
		Colinas = hechas,
		Rocas = rocas,
		SegundosCorteza = tiempoCorteza,
		SegundosColinas = tiempoColinas,
		SegundosTotal = os.clock() - inicio,
	}
end

--[[
	SOLO EN STUDIO (modo edición, barra de comandos): genera el terreno y lo deja en el lugar; después hay que
	GUARDAR el lugar. Si ya hay terreno de otros ajustes, no lo toca salvo con `reemplazar = true` (entonces lo
	borra entero antes). Devuelve el resumen, o nil y el motivo si no hace nada.
]]
function TerrenoPlaneta.hornearEnStudio(reemplazar: boolean?): ({ [string]: any }?, string?)
	local terreno = workspace.Terrain
	if TerrenoPlaneta.yaGenerado() then
		return nil, "el terreno de estos ajustes ya está en el lugar"
	end
	local hayTerreno = terreno:CountCells() > 0
	if hayTerreno and not reemplazar then
		return nil, "ya hay terreno de otros ajustes: llama con reemplazar = true para borrarlo y generarlo de nuevo"
	end
	if hayTerreno then
		terreno:Clear()
	end
	return TerrenoPlaneta.generar(), nil
end

return TerrenoPlaneta
