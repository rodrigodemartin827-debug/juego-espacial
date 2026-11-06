--!strict
--[[
	LodRegion (CLIENTE): niveles de detalle de la región 1 según la cámara. Hace lo mismo que
	modelos/region1_valle_del_alba/herramientas/lod.py en los renders de Blender:

	  * Edificios y objetos: la versión DETALLADA hasta Lod[tipo].detalle studs, la SIMPLE hasta Lod[tipo].simple y
	    nada más allá. La simple se crea aquí la primera vez que hace falta (con MontarRegion.copiarPieza) y se guarda.
	  * Aurora: más allá de Lod.silueta_aurora, todos sus edificios se cambian por la silueta (una malla).
	  * Terreno: cada trozo detallado se oculta (LocalTransparencyModifier = 1: su colisión sigue ahí) y se pone el
	    simple, que no choca, cuando la cámara está a más de Lod.terreno.detalle.
	  * Horizonte: lo que queda entero por debajo del horizonte del planeta no se dibuja. Con radio 2400 la curva tapa
	    muchísimo: desde el suelo el horizonte está a unos 155 studs.
	  * Vegetación: se crea por trozos de terreno, solo en los trozos cercanos, a partir de los datos
	    (datos/vegetacion/<f>_<c>.json), y cada árbol cambia de detallado a simple con la distancia.

	Todo es local (no se replica): el servidor no ve nada de esto. Las distancias vienen de datos/lod.json.
	NO SE HA PROBADO EN STUDIO.
]]

local RunService = game:GetService("RunService")

local MontarRegion = require(script.Parent:WaitForChild("MontarRegion"))

local LodRegion = {}

--[[
	Ajustes del nivel de gráficos (client/Graficos los cambia; se aplican en la siguiente actualización):
	  · Distancia: multiplica las distancias de detalle de edificios, mobiliario y terreno.
	  · Vegetacion: multiplica las distancias de árboles, matas y hierba.
	  · Densidad: fracción (0..1) de matas y hierba que se dibujan; los árboles se dibujan siempre.
]]
LodRegion.Ajustes = { Distancia = 1, Vegetacion = 1, Densidad = 1 }

local function escalar(cfg: { detalle: number, simple: number }, k: number): { detalle: number, simple: number }
	if k == 1 then
		return cfg
	end
	return { detalle = cfg.detalle * k, simple = cfg.simple * k }
end

local RADIO_PLANETA = 2400
local INTERVALO = 0.25 -- segundos entre actualizaciones

export type Config = {
	edificios: { detalle: number, simple: number },
	mobiliario: { detalle: number, simple: number },
	vegetacion: { detalle: number, simple: number },
	arboles: { detalle: number, simple: number },
	hierba: { detalle: number, simple: number },
	terreno: { detalle: number, simple: number },
	silueta_aurora: number,
	horizonte_margen: number,
}

type Entrada = {
	modelo: Model,
	tipo: string,
	sitio: string,
	centro: Vector3,
	radio: number,
	grupo: MontarRegion.Grupo?,
	detalle: Instance?,
	lejos: Instance?,
	nivel: string,
}

type Arbol = {
	tipo: string,
	categoria: string,
	cf: CFrame,
	escala: number,
	parte: MeshPart?,
	nivel: string,
	sorteo: number, -- 0..1 fijo por planta: se dibuja si es menor que Ajustes.Densidad
}
type TrozoVeg = { centro: Vector3, radio: number, arboles: { Arbol }, activo: boolean }

-- ¿Queda algo (centro, radio) por encima del horizonte visto desde `camara`? (todo en coordenadas del planeta)
local function sobreHorizonte(camara: Vector3, centro: Vector3, radio: number, margen: number): boolean
	local rh = RADIO_PLANETA - margen
	local rc = camara.Magnitude
	if rc <= rh then
		return true
	end
	local ro = math.max(centro.Magnitude + radio, rh)
	local cosang = math.clamp(camara.Unit:Dot(centro.Unit), -1, 1)
	return math.acos(cosang) <= math.acos(rh / rc) + math.acos(rh / ro)
end

-- Los árboles (no los arbustos ni las rocas) se ven de lejos en su versión simple: son los bosques.
local function esArbol(tipo: string): boolean
	return string.find(tipo, "^Frondoso") ~= nil
		or string.find(tipo, "^Pino") ~= nil
		or string.find(tipo, "^Abedul") ~= nil
		or string.find(tipo, "^Arbol") ~= nil
end

local function nivelPor(distancia: number, cfg: { detalle: number, simple: number }): string
	if distancia <= cfg.detalle then
		return "detalle"
	elseif distancia <= cfg.simple then
		return "simple"
	end
	return "oculto"
end

export type Opciones = {
	Region: Model, -- el Model que creó MontarRegion
	Montaje: MontarRegion.Opciones, -- las mismas opciones del montaje (piezas, datos...), para crear lo lejano
	Lod: Config,
	Vegetacion: { [string]: { { any } } }?, -- datos/vegetacion: clave «f_c» -> lista de instancias
	TrozosTerreno: { [string]: { centro: Vector3, radio: number } }?, -- para repartir la vegetación
}

function LodRegion.iniciar(opciones: Opciones): () -> ()
	local cfg = opciones.Lod
	local entradas: { Entrada } = {}
	local gruposPorNombre: { [string]: MontarRegion.Grupo } = {}
	for _, lista in opciones.Montaje.Datos.grupos do
		for _, g in lista do
			gruposPorNombre[g.nombre] = g
		end
	end
	local terrenoLejos: { [string]: { plantilla: MeshPart, posicion: Vector3, textura: string } } = {}
	for _, t in opciones.Montaje.Datos.terreno do
		if t.nivel ~= "detalle" then
			local plantilla = opciones.Montaje.Terreno:FindFirstChild(t.nombre)
			if plantilla and plantilla:IsA("MeshPart") then
				terrenoLejos[t.trozo] = {
					plantilla = plantilla :: MeshPart,
					posicion = Vector3.new(t.posicion[1], t.posicion[2], t.posicion[3]),
					textura = t.textura,
				}
			end
		end
	end
	local silueta: BasePart? = nil
	local registrados: { [Instance]: boolean } = {}
	--[[
		Registra un modelo con LOD (o la silueta). PROBADO EN STUDIO: la región llega al cliente POCO A POCO (aunque sea
		Persistent), así que lo que no estaba al arrancar se registra cuando llega (DescendantAdded). Antes se recogía
		todo una sola vez y los edificios que llegaban tarde se quedaban siempre en detalle.
	]]
	local function registrar(d: Instance)
		if registrados[d] then
			return
		end
		local lod = d:GetAttribute("Lod")
		if typeof(lod) ~= "string" then
			return
		end
		if lod == "silueta" and d:IsA("BasePart") then
			registrados[d] = true
			silueta = d
			return
		end
		if not d:IsA("Model") then
			return
		end
		registrados[d] = true
		table.insert(entradas, {
			modelo = d,
			tipo = lod :: string,
			sitio = (d:GetAttribute("Sitio") or "") :: string,
			centro = d:GetAttribute("Centro") :: Vector3,
			radio = d:GetAttribute("Radio") :: number,
			grupo = gruposPorNombre[d.Name],
			detalle = d:FindFirstChild("Detalle"),
			lejos = nil,
			nivel = "detalle",
		})
	end
	for _, d in opciones.Region:GetDescendants() do
		registrar(d)
	end
	local llegada = opciones.Region.DescendantAdded:Connect(registrar)

	-- crea (una vez) la versión lejana de una entrada
	local function lejosDe(e: Entrada): Instance?
		if e.lejos ~= nil then
			return e.lejos
		end
		if e.tipo == "terreno" then
			local trozo = string.sub(e.modelo.Name, 7) -- «Trozo_3_4» -> «3_4»
			local info = terrenoLejos[trozo]
			if info == nil then
				return nil
			end
			local p = info.plantilla:Clone()
			p.Name = "Lejos"
			p.Anchored = true
			p.CanCollide = false
			p.CanQuery = false
			p.CanTouch = false
			p.CastShadow = false
			p.CFrame = MontarRegion.origen(opciones.Montaje) * CFrame.new(info.posicion) * MontarRegion.GIRO_TERRENO
			-- La textura del trozo lejano (terreno_lejos.png). Sin ella sale del color por defecto (probado en Studio).
			local ids = opciones.Montaje.IdsTerreno
			if ids and ids[info.textura] then
				p.TextureID = ids[info.textura]
			end
			e.lejos = p
			return p
		end
		local g = e.grupo
		if g == nil then
			return nil
		end
		local m = Instance.new("Model")
		m.Name = "Lejos"
		local cf = CFrame.new(
			g.cframe[1],
			g.cframe[2],
			g.cframe[3],
			g.cframe[4],
			g.cframe[5],
			g.cframe[6],
			g.cframe[7],
			g.cframe[8],
			g.cframe[9],
			g.cframe[10],
			g.cframe[11],
			g.cframe[12]
		)
		for _, entrada in g.piezas do
			MontarRegion.copiarPieza(opciones.Montaje, entrada[1] :: string, true, cf, entrada, m)
		end
		e.lejos = m
		return m
	end

	local function poner(e: Entrada, nivel: string)
		-- El Detalle puede llegar al cliente después que su modelo: si llega ya con otro nivel puesto, se vuelve a aplicar.
		if e.detalle == nil then
			e.detalle = e.modelo:FindFirstChild("Detalle")
			if e.detalle ~= nil and e.nivel ~= "detalle" then
				e.nivel = "detalle"
			end
		end
		if nivel == e.nivel then
			return
		end
		e.nivel = nivel
		if e.tipo == "terreno" then
			local det = e.detalle
			if det and det:IsA("BasePart") then
				det.LocalTransparencyModifier = if nivel == "detalle" then 0 else 1
			end
			local l = if nivel == "simple" then lejosDe(e) else e.lejos
			if l then
				l.Parent = if nivel == "simple" then e.modelo else nil
			end
			return
		end
		if e.detalle then
			(e.detalle :: Instance).Parent = if nivel == "detalle" then e.modelo else nil
		end
		local l = if nivel == "simple" then lejosDe(e) else e.lejos
		if l then
			l.Parent = if nivel == "simple" then e.modelo else nil
		end
	end

	-- vegetación por trozos
	local trozosVeg: { [string]: TrozoVeg } = {}
	if opciones.Vegetacion and opciones.TrozosTerreno then
		for clave, lista in opciones.Vegetacion :: { [string]: { { any } } } do
			local info = (opciones.TrozosTerreno :: { [string]: { centro: Vector3, radio: number } })[clave]
			if info == nil then
				continue
			end
			local arboles: { Arbol } = {}
			for _, a in lista do
				table.insert(arboles, {
					tipo = a[1] :: string,
					categoria = a[2] :: string,
					cf = CFrame.new(
						a[3] :: number,
						a[4] :: number,
						a[5] :: number,
						a[6] :: number,
						a[7] :: number,
						a[8] :: number,
						a[9] :: number,
						a[10] :: number,
						a[11] :: number,
						a[12] :: number,
						a[13] :: number,
						a[14] :: number
					),
					escala = a[15] :: number,
					parte = nil,
					nivel = "oculto",
					sorteo = (#arboles * 0.6180339887) % 1,
				})
			end
			trozosVeg[clave] = { centro = info.centro, radio = info.radio, arboles = arboles, activo = false }
		end
	end
	local carpetaVeg = Instance.new("Folder")
	carpetaVeg.Name = "Vegetacion_Local"
	carpetaVeg.Parent = opciones.Region

	local function ponerArbol(a: Arbol, nivel: string)
		if nivel == a.nivel then
			return
		end
		if a.parte then
			(a.parte :: MeshPart):Destroy()
			a.parte = nil
		end
		a.nivel = nivel
		if nivel == "oculto" then
			return
		end
		local entrada: { any } = { a.tipo, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, a.escala, a.escala, a.escala, "#FFFFFF" }
		a.parte = MontarRegion.copiarPieza(opciones.Montaje, a.tipo, nivel == "simple", a.cf, entrada, carpetaVeg)
	end

	local acumulado = 0
	local conexion = RunService.Heartbeat:Connect(function(dt: number)
		acumulado += dt
		if acumulado < INTERVALO then
			return
		end
		acumulado = 0
		local camara = workspace.CurrentCamera
		if camara == nil then
			return
		end
		-- La cámara, en coordenadas del planeta (las de los datos y los atributos Centro).
		local p = MontarRegion.origen(opciones.Montaje):PointToObjectSpace(camara.CFrame.Position)
		local margen = cfg.horizonte_margen
		local auroraLejos = false
		if silueta then
			local c = (silueta :: BasePart):GetAttribute("Centro") :: Vector3
			auroraLejos = (p - c).Magnitude > cfg.silueta_aurora
			local visible = auroraLejos and sobreHorizonte(p, c, 300, margen);
			(silueta :: BasePart).LocalTransparencyModifier = if visible then 0 else 1
		end
		for _, e in entradas do
			local d = math.max((p - e.centro).Magnitude - e.radio, 0)
			local nivel
			if not sobreHorizonte(p, e.centro, e.radio, margen) then
				nivel = if e.tipo == "terreno" then "simple" else "oculto"
			elseif e.tipo == "terreno" then
				nivel = if d <= cfg.terreno.detalle * LodRegion.Ajustes.Distancia then "detalle" else "simple"
			else
				local c = (cfg :: any)[if e.tipo == "vegetacion" then "vegetacion" else e.tipo]
				nivel = nivelPor(d, escalar(c or cfg.mobiliario, LodRegion.Ajustes.Distancia))
				if e.sitio == "Aurora" and e.tipo == "edificios" and auroraLejos then
					nivel = "oculto"
				end
			end
			poner(e, nivel)
		end
		for _, t in trozosVeg do
			local d = math.max((p - t.centro).Magnitude - t.radio, 0)
			local kVeg = LodRegion.Ajustes.Vegetacion
			local activo = d <= math.max(cfg.vegetacion.simple, cfg.arboles.simple) * kVeg
			if not activo and not t.activo then
				continue
			end
			t.activo = activo
			for _, a in t.arboles do
				local c = if a.categoria == "hierba"
					then cfg.hierba
					elseif esArbol(a.tipo) then cfg.arboles
					else cfg.vegetacion
				local pos = a.cf.Position
				local nivel = "oculto"
				local dibujar = esArbol(a.tipo) or a.sorteo < LodRegion.Ajustes.Densidad
				if activo and dibujar and sobreHorizonte(p, pos, 30, margen) then
					nivel = nivelPor((p - pos).Magnitude, escalar(c, kVeg))
				end
				ponerArbol(a, nivel)
			end
		end
	end)
	return function()
		conexion:Disconnect()
		llegada:Disconnect()
	end
end

return LodRegion
