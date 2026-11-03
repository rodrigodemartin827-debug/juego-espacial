--!strict
--[[
	Coloca en Workspace los trozos importados del planeta de prueba y los deja con colisión precisa.

	NO lo edites a mano: lo genera planeta_prueba.py con los números de los trozos. Los ajustes que sí puedes tocar
	están en AJUSTES, justo debajo.

	Cómo se usa (README.md, paso a paso):
	  1. Importa los FBX de piezas/ (Scale Unit = Stud) y sube paleta_color.png una vez.
	  2. Pega el ID de la paleta en AJUSTES.IdPaleta.
	  3. Selecciona lo que ha creado el importador (o nada, y se busca en todo Workspace).
	  4. Pega este script en la barra de comandos (View → Command Bar) y pulsa Enter.

	Qué hace:
	  - Busca las MeshPart por su nombre (Planeta_XP_0_0, ...) y comprueba que el TAMAÑO es el esperado: si no, el
	    importador ha usado otra escala y lo dice, con el factor que hay que poner.
	  - Las mueve a su sitio, las ancla, les pone colisión PreciseConvexDecomposition y la textura de paleta, y las
	    mete en un Model en Workspace.
	  - Comprueba el resultado lanzando rayos contra la colisión desde fuera del planeta y comparándolos con la
	    superficie esperada. Si no se ha fijado el giro, prueba 0° y 180° (por si el importador gira cada trozo) y se
	    queda con el que mejor coincide.

	Hay que guardar el lugar después (File → Save) para que la colisión calculada se quede con él.
]]

type Ajustes = {
	IdPaleta: string, -- "rbxassetid://123..." de paleta_color.png (la imagen se sube una sola vez)
	Centro: Vector3, -- dónde queda el centro del planeta
	GiroYGrados: number?, -- nil: se detecta solo (prueba 0° y 180°)
	Fidelidad: Enum.CollisionFidelity,
	NombreModelo: string,
	ToleranciaTamano: number, -- fracción: 0.02 = el tamaño puede diferir un 2 %
	ToleranciaColision: number, -- studs: error máximo aceptable entre la colisión y la malla
	EsperaFisica: number, -- segundos que se espera a que el motor prepare la colisión antes de medirla
}

local AJUSTES: Ajustes = {
	IdPaleta = "",
	Centro = Vector3.new(0, 0, 0),
	GiroYGrados = nil,
	Fidelidad = Enum.CollisionFidelity.PreciseConvexDecomposition,
	NombreModelo = "PlanetaPrueba",
	ToleranciaTamano = 0.02,
	ToleranciaColision = 4,
	EsperaFisica = 3,
}

-- ===== Datos generados por planeta_prueba.py =====

type Pieza = {
	Nombre: string,
	Centro: Vector3, -- centro de la caja envolvente, respecto al centro del planeta
	Tamano: Vector3, -- tamaño de esa caja
	Triangulos: number,
}

local RADIO: number = --RADIO--
local ALTURA_RAYO = 400 -- los rayos salen a esta altura sobre el nivel del mar (la cumbre más alta mide menos)
local LARGO_RAYO = 650 -- y bajan hasta bien por debajo del fondo de la superficie

local PIEZAS: { Pieza } = {
--PIEZAS--
}

-- Cada muestra: { dirección x, y, z (unitaria), radio esperado de la superficie TRIANGULADA en esa dirección }.
local MUESTRAS: { { number } } = {
--MUESTRAS--
}

-- ===== Comprobaciones previas =====

local Workspace = game:GetService("Workspace")
local Selection = game:GetService("Selection")

local function recogerMallas(): { [string]: MeshPart }
	local origenes: { Instance } = Selection:Get()
	if #origenes == 0 then
		origenes = { Workspace }
	end
	local mallas: { [string]: MeshPart } = {}
	local repetidas = 0
	local function mirar(instancia: Instance)
		if instancia:IsA("MeshPart") and string.sub(instancia.Name, 1, 8) == "Planeta_" then
			if mallas[instancia.Name] ~= nil then
				repetidas += 1
			end
			mallas[instancia.Name] = instancia
		end
	end
	for _, origen in origenes do
		mirar(origen)
		for _, d in origen:GetDescendants() do
			mirar(d)
		end
	end
	if repetidas > 0 then
		warn(`[Planeta] hay {repetidas} MeshPart con nombre repetido: se usa la última encontrada de cada nombre.`)
	end
	return mallas
end

local function tamanoCorrecto(real: Vector3, esperado: Vector3): boolean
	local tol = AJUSTES.ToleranciaTamano
	return math.abs(real.X - esperado.X) <= esperado.X * tol + 0.5
		and math.abs(real.Y - esperado.Y) <= esperado.Y * tol + 0.5
		and math.abs(real.Z - esperado.Z) <= esperado.Z * tol + 0.5
end

-- ===== Colocar =====

local function prepararPiezas(mallas: { [string]: MeshPart }, modelo: Model): { [string]: MeshPart }
	local colocadas: { [string]: MeshPart } = {}
	local faltan: { string } = {}
	local tamanoMal: { string } = {}
	local razon = 0
	local contados = 0
	for _, pieza in PIEZAS do
		local malla = mallas[pieza.Nombre]
		if malla == nil then
			table.insert(faltan, pieza.Nombre)
			continue
		end
		if not tamanoCorrecto(malla.Size, pieza.Tamano) then
			table.insert(tamanoMal, pieza.Nombre)
			razon += (malla.Size.X + malla.Size.Y + malla.Size.Z) / (pieza.Tamano.X + pieza.Tamano.Y + pieza.Tamano.Z)
			contados += 1
		end
		malla.Anchored = true
		malla.CanCollide = true
		malla.CanQuery = true
		malla.CastShadow = true
		malla.Material = Enum.Material.Ground -- sonido y fricción de tierra; el aspecto lo da la textura
		malla.RenderFidelity = Enum.RenderFidelity.Precise -- sin simplificar por distancia: evita grietas entre trozos
		malla.CollisionFidelity = AJUSTES.Fidelidad

		local vieja = malla:FindFirstChildOfClass("SurfaceAppearance")
		if vieja ~= nil then
			vieja:Destroy()
		end
		if AJUSTES.IdPaleta ~= "" then
			local aspecto = Instance.new("SurfaceAppearance")
			aspecto.ColorMap = AJUSTES.IdPaleta
			aspecto.Parent = malla
		end
		malla.Parent = modelo
		colocadas[pieza.Nombre] = malla
	end
	if #faltan > 0 then
		warn(`[Planeta] faltan {#faltan} trozos en lo importado, por ejemplo {faltan[1]}. Importa los {#PIEZAS} FBX de piezas/.`)
	end
	if #tamanoMal > 0 then
		local factor = razon / math.max(contados, 1)
		warn(
			`[Planeta] {#tamanoMal} trozos NO tienen el tamaño esperado (por ejemplo {tamanoMal[1]}: el importador ha `
				.. `dejado un tamaño {string.format("%.3f", factor)} veces el esperado). En el importador pon `
				.. `Scale Unit = Stud, o deja Custom Scale Factor = {string.format("%.4f", 1 / factor)}, y vuelve a importar.`
		)
	end
	if AJUSTES.IdPaleta == "" then
		warn("[Planeta] AJUSTES.IdPaleta está vacío: los trozos se quedan sin textura de color por altura.")
	end
	return colocadas
end

local function orientar(colocadas: { [string]: MeshPart }, giroGrados: number)
	for _, pieza in PIEZAS do
		local malla = colocadas[pieza.Nombre]
		if malla ~= nil then
			malla.CFrame = CFrame.new(AJUSTES.Centro + pieza.Centro) * CFrame.Angles(0, math.rad(giroGrados), 0)
		end
	end
end

-- ===== Verificar =====

type Resultado = {
	Muestras: number,
	Fallos: number, -- rayos que no tocaron nada
	Media: number, -- error medio (studs) entre la colisión y la superficie esperada
	P95: number,
	Maximo: number,
}

local function verificar(modelo: Model): Resultado
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { modelo }
	local errores: { number } = {}
	local fallos = 0
	for _, m in MUESTRAS do
		local direccion = Vector3.new(m[1], m[2], m[3])
		local esperado = m[4]
		local origen = AJUSTES.Centro + direccion * (RADIO + ALTURA_RAYO)
		local resultado = Workspace:Raycast(origen, -direccion * LARGO_RAYO, params)
		if resultado == nil then
			fallos += 1
		else
			table.insert(errores, math.abs((resultado.Position - AJUSTES.Centro).Magnitude - esperado))
		end
	end
	table.sort(errores)
	local suma = 0
	for _, e in errores do
		suma += e
	end
	local n = #errores
	return {
		Muestras = #MUESTRAS,
		Fallos = fallos,
		Media = if n > 0 then suma / n else math.huge,
		P95 = if n > 0 then errores[math.max(1, math.ceil(n * 0.95))] else math.huge,
		Maximo = if n > 0 then errores[n] else math.huge,
	}
end

local function describir(r: Resultado): string
	return `{r.Muestras - r.Fallos}/{r.Muestras} rayos con impacto · error medio {string.format("%.2f", r.Media)}, `
		.. `p95 {string.format("%.2f", r.P95)}, máximo {string.format("%.2f", r.Maximo)} studs`
end

-- ===== Principal =====

local function ejecutar()
	local mallas = recogerMallas()
	local total = 0
	for _ in mallas do
		total += 1
	end
	if total == 0 then
		warn("[Planeta] No hay ninguna MeshPart llamada Planeta_* en la selección ni en Workspace. Importa primero los FBX.")
		return
	end

	-- Si ya hay un modelo de una ejecución anterior se reutiliza: destruirlo destruiría también las mallas que
	-- hay dentro (que son las que acabamos de recoger) y ya no se podrían volver a colocar.
	local existente = Workspace:FindFirstChild(AJUSTES.NombreModelo)
	local modelo: Model
	if existente ~= nil and existente:IsA("Model") then
		modelo = existente
	else
		modelo = Instance.new("Model")
		modelo.Name = AJUSTES.NombreModelo
		modelo.Parent = Workspace
	end

	local colocadas = prepararPiezas(mallas, modelo)
	print(`[Planeta] {total} MeshPart encontradas, {#PIEZAS} esperadas. Colocando con {AJUSTES.Fidelidad.Name}...`)

	local giros: { number } = if AJUSTES.GiroYGrados ~= nil then { AJUSTES.GiroYGrados } else { 0, 180 }
	local mejorGiro = giros[1]
	local mejor: Resultado? = nil
	for _, giro in giros do
		orientar(colocadas, giro)
		task.wait(AJUSTES.EsperaFisica)
		local r = verificar(modelo)
		print(`[Planeta] giro {giro}°: {describir(r)}`)
		if mejor == nil or r.Media < mejor.Media then
			mejor, mejorGiro = r, giro
		end
	end
	orientar(colocadas, mejorGiro)

	if mejor ~= nil and mejor.Fallos == 0 and mejor.Maximo <= AJUSTES.ToleranciaColision then
		print(`[Planeta] CORRECTO con giro {mejorGiro}°. Guarda el lugar (File → Save) para conservar la colisión.`)
	else
		warn(
			`[Planeta] REVISAR: con el mejor giro ({mejorGiro}°) el error máximo supera {AJUSTES.ToleranciaColision} `
				.. `studs o hay rayos sin impacto. Mira README.md, apartado «Si la comprobación falla».`
		)
	end
	if not Workspace.StreamingEnabled then
		warn("[Planeta] Workspace.StreamingEnabled está desactivado: con un planeta así conviene activarlo.")
	end
end

ejecutar()
