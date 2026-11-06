--!strict
--[[
	MontarRegion: monta en el lugar la región 1 (Valle del Alba) a partir de las piezas importadas y de los datos que
	escribe modelos/region1_valle_del_alba/herramientas/exportar.py. Pensado para ejecutarse UNA vez en Studio (desde
	la barra de comandos o un script de herramientas) y guardar el lugar.

	Idea: cada pieza del kit (pared con ventana, tramo de tejado, farola...) se importa UNA vez como MeshPart y aquí
	se COPIA tantas veces como aparece. Todas las copias comparten la malla (MeshId) y el atlas (TextureID): Roblox
	solo guarda y sube una vez cada malla. El color de cada copia (MeshPart.Color) se ve a través de las zonas
	transparentes del atlas (yeso, tejas, contraventanas, puertas, toldos).

	Lo que crea, dentro de `opciones.Destino` (un Model «Region1_ValleDelAlba»):
	  * Edificios/<Sitio>/<nombre>: Model con «Detalle» (sus piezas detalladas) y «Colision» (una caja invisible:
	    las piezas no chocan, así la física es mucho más barata).
	  * Objetos/<Sitio>/<nombre>: igual (mobiliario, molinos, torre, fuente...).
	  * Terreno/Trozo_<f>_<c>: Model con «Detalle» (el trozo detallado, con colisión precisa).
	  * Silueta_Aurora: la silueta de Aurora para verla de lejos.
	Cada Model lleva los atributos que usa LodRegion: Lod (texto), Centro (Vector3), Radio (número), Sitio.
	Las versiones LEJANAS no se guardan en el lugar: las crea LodRegion en el cliente, solo cuando hacen falta
	(con MontarRegion.copiarPieza). La vegetación tampoco: LodRegion la crea por trozos, solo cerca de la cámara.

	PROBADO EN STUDIO: el importador respeta los ejes y la escala en studs (los tamaños coinciden con los datos). El
	Color solo se ve a través de la transparencia del atlas si cada plantilla lleva un SurfaceAppearance con
	AlphaMode = Overlay (EjemploArranque.prepararPiezasEnStudio); con solo TextureID se ve el ruido del atlas.
]]

local MontarRegion = {}

export type Nivel = { centro: { number }, tamano: { number }, triangulos: number }
export type InfoPieza = {
	detalle: Nivel,
	lejos: Nivel?,
	sin_lejos: boolean,
	color: string,
	doble_cara: boolean?, -- lona de una capa: DoubleSided en la plantilla
	colision: boolean?, -- se pisa (el puente): la versión detallada choca, con colisión precisa en la plantilla
}
export type Grupo = {
	nombre: string,
	lod: string,
	cframe: { number },
	centro: { number },
	radio: number,
	piezas: { { any } },
	caja: { number }?,
}
export type Trozo = {
	nombre: string,
	nivel: string,
	trozo: string,
	posicion: { number },
	centro_lod: { number },
	radio: number,
	textura: string,
}
export type Silueta = { cframe: { number }, centro: { number }, centro_lod: { number } }
export type Datos = {
	piezas: { [string]: InfoPieza },
	grupos: { [string]: { Grupo } }, -- clave: «edificios_Aurora», «objetos_Pradoverde»...
	terreno: { Trozo },
	silueta: Silueta?,
}
export type Opciones = {
	Piezas: Instance, -- carpeta con las MeshPart importadas, con el nombre de la pieza («Pared_Ventana», «Pared_Ventana__lejos»)
	Terreno: Instance, -- carpeta con las MeshPart de los trozos («Terreno_3_4», «Terreno_3_4__lejos»)
	Silueta: MeshPart?,
	IdAtlas: string?, -- rbxassetid del atlas del kit (si las MeshPart importadas no lo llevan ya)
	IdsTerreno: { [string]: string }?, -- textura de cada trozo: «terreno_1_2.png» -> rbxassetid
	Destino: Instance,
	Datos: Datos,
	-- Marco del CENTRO DEL PLANETA en el mundo. Los datos están en coordenadas del planeta (centrado en el origen, como en
	-- Blender); Nueva Tierra está en otro sitio, así que todo se coloca con Origen * (lo de los datos). nil = el origen.
	Origen: CFrame?,
}

-- Las piezas pequeñas no proyectan sombra (en móvil las sombras cuestan mucho y aquí no se notan).
local SIN_SOMBRA = {
	Contraventanas = true,
	Jardinera = true,
	Puerta = true,
	Farolillo = true,
	Cornisa = true,
	Cornisa_Esquina = true,
	Esquina = true,
	Cumbrera_16 = true,
	Cumbrera_24 = true,
	Cumbrera_Remate_16 = true,
	Cumbrera_Remate_24 = true,
}

--[[
	PROBADO EN STUDIO: el importador 3D deja TODAS las mallas de estos FBX (exportados con delante -Z y arriba Y) giradas
	180° sobre su eje vertical respecto a los datos. Sin este giro:
	  * los trozos de terreno dejan huecos de decenas de studs entre ellos y no casan con caminos ni edificios;
	  * las piezas de los edificios quedan del revés: cada pared mira hacia DENTRO, y desde fuera se ve su cara trasera
	    (es decir, nada: «láminas transparentes») y a través de ella el interior de la pared de enfrente.
	Se aplica alrededor del centro de cada malla: a las piezas (copiarPieza), al terreno detallado (aquí) y al lejano
	(LodRegion) y a la silueta de Aurora (probado: girada, su torre cae sobre la torre de verdad; sin girar quedaban dos torres
	y la silueta se mezclaba con los edificios, lo que parecía «textura mal puesta»).
]]
MontarRegion.GIRO_IMPORTACION = CFrame.Angles(0, math.pi, 0)
MontarRegion.GIRO_TERRENO = MontarRegion.GIRO_IMPORTACION

-- Marco del centro del planeta (ver Opciones.Origen).
function MontarRegion.origen(opciones: Opciones): CFrame
	return opciones.Origen or CFrame.identity
end

local function v3(t: { number }): Vector3
	return Vector3.new(t[1], t[2], t[3])
end

-- CFrame guardado como 12 números a partir de la posición `i` de la lista.
local function aCFrame(t: { any }, i: number): CFrame
	return CFrame.new(
		t[i] :: number,
		t[i + 1] :: number,
		t[i + 2] :: number,
		t[i + 3] :: number,
		t[i + 4] :: number,
		t[i + 5] :: number,
		t[i + 6] :: number,
		t[i + 7] :: number,
		t[i + 8] :: number,
		t[i + 9] :: number,
		t[i + 10] :: number,
		t[i + 11] :: number
	)
end

local function carpeta(padre: Instance, nombre: string): Instance
	local f = padre:FindFirstChild(nombre)
	if f == nil then
		local nueva = Instance.new("Folder")
		nueva.Name = nombre
		nueva.Parent = padre
		return nueva
	end
	return f :: Instance
end

local function modelo(padre: Instance, nombre: string): Model
	local m = Instance.new("Model")
	m.Name = nombre
	m.Parent = padre
	return m
end

--[[
	RenderFidelity y CollisionFidelity solo se pueden cambiar en Studio, NO durante el juego (PROBADO: "lacking capability
	PluginOrOpenCloud"). Las pone en las plantillas EjemploArranque.prepararPiezasEnStudio; las copias las heredan y
	aquí solo se intenta si la plantilla no la trae (en Studio funciona; en el juego no se toca).
]]
local function ponerRenderFidelity(p: MeshPart, valor: Enum.RenderFidelity)
	if p.RenderFidelity ~= valor then
		pcall(function()
			p.RenderFidelity = valor
		end)
	end
end

local function prepararParte(p: BasePart, colision: boolean)
	p.Anchored = true
	p.CanCollide = colision
	p.CanQuery = colision
	p.CanTouch = false
end

-- Copia una pieza (detallada o lejana) y la coloca. Devuelve nil si esa pieza no tiene versión para ese nivel.
function MontarRegion.copiarPieza(
	opciones: Opciones,
	nombre: string,
	lejos: boolean,
	cfGrupo: CFrame,
	entrada: { any },
	destino: Instance
): MeshPart?
	local info = opciones.Datos.piezas[nombre]
	if info == nil then
		warn(`MontarRegion: la pieza {nombre} no está en los datos`)
		return nil
	end
	local nivel: Nivel? = info.detalle
	local nombreMalla = nombre
	if lejos then
		if info.sin_lejos then
			return nil
		end
		if info.lejos ~= nil then
			nivel = info.lejos
			nombreMalla = nombre .. "__lejos"
		end
	end
	local plantilla = opciones.Piezas:FindFirstChild(nombreMalla)
	if plantilla == nil or not plantilla:IsA("MeshPart") or nivel == nil then
		warn(`MontarRegion: falta la MeshPart {nombreMalla}`)
		return nil
	end
	local escala = Vector3.new(entrada[14] :: number, entrada[15] :: number, entrada[16] :: number)
	local parte = (plantilla :: MeshPart):Clone()
	-- Roblox centra cada malla en su caja: se compensa con el centro guardado (escalado)
	parte.Size = parte.MeshSize * escala
	parte.CFrame = MontarRegion.origen(opciones)
		* cfGrupo
		* aCFrame(entrada, 2)
		* CFrame.new(v3(nivel.centro) * escala)
		* MontarRegion.GIRO_IMPORTACION
	parte.Color = Color3.fromHex(entrada[17] :: string)
	if opciones.IdAtlas then
		parte.TextureID = opciones.IdAtlas :: string
	end
	parte.CastShadow = not (SIN_SOMBRA[nombre] == true) and not lejos
	ponerRenderFidelity(parte, Enum.RenderFidelity.Performance)
	-- Solo chocan las piezas marcadas «colision» (el puente), y solo en su versión detallada.
	prepararParte(parte, info.colision == true and not lejos)
	parte.Parent = destino
	return parte
end

local function montarGrupo(opciones: Opciones, g: Grupo, sitio: string, destino: Instance)
	local m = modelo(destino, g.nombre)
	m:SetAttribute("Lod", g.lod)
	m:SetAttribute("Centro", v3(g.centro))
	m:SetAttribute("Radio", g.radio)
	m:SetAttribute("Sitio", sitio)
	local cf = aCFrame(g.cframe, 1)
	local detalle = modelo(m, "Detalle")
	for _, entrada in g.piezas do
		local nombre = entrada[1] :: string
		MontarRegion.copiarPieza(opciones, nombre, false, cf, entrada, detalle)
	end
	-- caja de colisión del edificio (los muros; el tejado no hace falta para andar por el pueblo)
	if g.caja ~= nil then
		local caja = g.caja :: { number }
		local ancho, fondo, alto = caja[1], caja[2], caja[3]
		local c = Instance.new("Part")
		c.Name = "Colision"
		c.Transparency = 1
		c.Size = Vector3.new(ancho, alto, fondo)
		-- en el edificio, x ∈ [0, ancho], el fondo hacia -Z (en Blender era +Y) y la altura hacia +Y
		c.CFrame = MontarRegion.origen(opciones) * cf * CFrame.new(ancho / 2, alto / 2, -fondo / 2)
		prepararParte(c, true)
		c.CanQuery = true
		c.Parent = m
	end
end

function MontarRegion.montar(opciones: Opciones): Model
	local raiz = opciones.Destino:FindFirstChild("Region1_ValleDelAlba")
	if raiz then
		raiz:Destroy()
	end
	local region = modelo(opciones.Destino, "Region1_ValleDelAlba")
	local datos = opciones.Datos
	local nGrupos, nPiezas = 0, 0
	for clave, lista in datos.grupos do
		local tipo, sitio = string.match(clave, "^(%a+)_(.+)$")
		local destino =
			carpeta(carpeta(region, if tipo == "edificios" then "Edificios" else "Objetos"), sitio or "Region")
		for _, g in lista do
			montarGrupo(opciones, g, sitio or "Region", destino)
			nGrupos += 1
			nPiezas += #g.piezas
		end
	end
	-- terreno: un Model por trozo, con el trozo detallado (el lejano lo pone LodRegion en el cliente)
	local terreno = carpeta(region, "Terreno")
	for _, t in datos.terreno do
		if t.nivel ~= "detalle" then
			continue
		end
		local m = terreno:FindFirstChild("Trozo_" .. t.trozo) :: Model?
		if m == nil then
			m = modelo(terreno, "Trozo_" .. t.trozo)
			local mm = m :: Model
			mm:SetAttribute("Lod", "terreno")
			mm:SetAttribute("Centro", v3(t.centro_lod))
			mm:SetAttribute("Radio", t.radio)
		end
		local plantilla = opciones.Terreno:FindFirstChild(t.nombre)
		if plantilla and plantilla:IsA("MeshPart") then
			local p = plantilla:Clone()
			p.Name = "Detalle"
			p.CFrame = MontarRegion.origen(opciones) * CFrame.new(v3(t.posicion)) * MontarRegion.GIRO_TERRENO
			local ids = opciones.IdsTerreno
			if ids and ids[t.textura] then
				p.TextureID = ids[t.textura]
			end
			prepararParte(p, true)
			-- CollisionFidelity solo se puede cambiar en Studio (no durante el juego): si la plantilla ya la trae, no se toca.
			if p.CollisionFidelity ~= Enum.CollisionFidelity.PreciseConvexDecomposition then
				pcall(function()
					p.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition
				end)
			end
			ponerRenderFidelity(p, Enum.RenderFidelity.Precise) -- evita grietas entre trozos
			p.Parent = m
		else
			warn(`MontarRegion: falta el trozo de terreno {t.nombre}`)
		end
	end
	if opciones.Silueta and datos.silueta then
		local s = (opciones.Silueta :: MeshPart):Clone()
		local info = datos.silueta :: Silueta
		s.Name = "Silueta_Aurora"
		s.CFrame = MontarRegion.origen(opciones)
			* aCFrame(info.cframe, 1)
			* CFrame.new(v3(info.centro))
			* MontarRegion.GIRO_IMPORTACION
		if opciones.IdAtlas then
			s.TextureID = opciones.IdAtlas :: string
		end
		prepararParte(s, false)
		s.CastShadow = false
		s:SetAttribute("Lod", "silueta")
		s:SetAttribute("Centro", v3(info.centro_lod))
		s:SetAttribute("Radio", 300)
		s:SetAttribute("Sitio", "Aurora")
		s.Parent = region
	end
	print(`MontarRegion: {nGrupos} grupos, {nPiezas} piezas detalladas colocadas`)
	return region
end

return MontarRegion
