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

type Arbol = { tipo: string, categoria: string, cf: CFrame, escala: number, parte: MeshPart?, nivel: string }
type TrozoVeg = { centro: Vector3, radio: number, arboles: { Arbol }, activo: boolean }

-- ¿Queda algo (centro, radio) por encima del horizonte visto desde `camara`? (planeta centrado en el origen)
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
	local terrenoLejos: { [string]: { plantilla: MeshPart, posicion: Vector3 } } = {}
	for _, t in opciones.Montaje.Datos.terreno do
		if t.nivel ~= "detalle" then
			local plantilla = opciones.Montaje.Terreno:FindFirstChild(t.nombre)
			if plantilla and plantilla:IsA("MeshPart") then
				terrenoLejos[t.trozo] = {
					plantilla = plantilla :: MeshPart,
					posicion = Vector3.new(t.posicion[1], t.posicion[2], t.posicion[3]),
				}
			end
		end
	end
	local silueta: BasePart? = nil
	for _, d in opciones.Region:GetDescendants() do
		local lod = d:GetAttribute("Lod")
		if typeof(lod) ~= "string" then
			continue
		end
		if lod == "silueta" and d:IsA("BasePart") then
			silueta = d
			continue
		end
		if not d:IsA("Model") then
			continue
		end
		table.insert(entradas, {
			modelo = d,
			tipo = lod,
			sitio = (d:GetAttribute("Sitio") or "") :: string,
			centro = d:GetAttribute("Centro") :: Vector3,
			radio = d:GetAttribute("Radio") :: number,
			grupo = gruposPorNombre[d.Name],
			detalle = d:FindFirstChild("Detalle"),
			lejos = nil,
			nivel = "detalle",
		})
	end

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
			p.CFrame = CFrame.new(info.posicion)
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
			g.cframe[1], g.cframe[2], g.cframe[3], g.cframe[4], g.cframe[5], g.cframe[6],
			g.cframe[7], g.cframe[8], g.cframe[9], g.cframe[10], g.cframe[11], g.cframe[12]
		)
		for _, entrada in g.piezas do
			MontarRegion.copiarPieza(opciones.Montaje, entrada[1] :: string, true, cf, entrada, m)
		end
		e.lejos = m
		return m
	end

	local function poner(e: Entrada, nivel: string)
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
						a[3] :: number, a[4] :: number, a[5] :: number, a[6] :: number, a[7] :: number,
						a[8] :: number, a[9] :: number, a[10] :: number, a[11] :: number, a[12] :: number,
						a[13] :: number, a[14] :: number
					),
					escala = a[15] :: number,
					parte = nil,
					nivel = "oculto",
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
		local entrada = { a.tipo, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, a.escala, a.escala, a.escala, "#FFFFFF" }
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
		local p = camara.CFrame.Position
		local margen = cfg.horizonte_margen
		local auroraLejos = false
		if silueta then
			local c = (silueta :: BasePart):GetAttribute("Centro") :: Vector3
			auroraLejos = (p - c).Magnitude > cfg.silueta_aurora
			local visible = auroraLejos and sobreHorizonte(p, c, 300, margen)
			;(silueta :: BasePart).LocalTransparencyModifier = if visible then 0 else 1
		end
		for _, e in entradas do
			local d = math.max((p - e.centro).Magnitude - e.radio, 0)
			local nivel
			if not sobreHorizonte(p, e.centro, e.radio, margen) then
				nivel = if e.tipo == "terreno" then "simple" else "oculto"
			elseif e.tipo == "terreno" then
				nivel = if d <= cfg.terreno.detalle then "detalle" else "simple"
			else
				local c = (cfg :: any)[if e.tipo == "vegetacion" then "vegetacion" else e.tipo]
				nivel = nivelPor(d, c or cfg.mobiliario)
				if e.sitio == "Aurora" and e.tipo == "edificios" and auroraLejos then
					nivel = "oculto"
				end
			end
			poner(e, nivel)
		end
		for _, t in trozosVeg do
			local d = math.max((p - t.centro).Magnitude - t.radio, 0)
			local activo = d <= math.max(cfg.vegetacion.simple, cfg.arboles.simple)
			if not activo and not t.activo then
				continue
			end
			t.activo = activo
			for _, a in t.arboles do
				local c = if a.categoria == "hierba" then cfg.hierba elseif esArbol(a.tipo) then cfg.arboles else cfg.vegetacion
				local pos = a.cf.Position
				local nivel = "oculto"
				if activo and sobreHorizonte(p, pos, 30, margen) then
					nivel = nivelPor((p - pos).Magnitude, c)
				end
				ponerArbol(a, nivel)
			end
		end
	end)
	return function()
		conexion:Disconnect()
	end
end

return LodRegion
