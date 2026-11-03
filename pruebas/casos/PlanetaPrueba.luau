--[[
	Pruebas del experimento del planeta (modelos/planeta_prueba): los datos de los trozos y el script de Luau
	`colocar_planeta.luau`, que se ejecuta de verdad sobre una simulación mínima de Roblox (Vector3, CFrame, Instance y
	Workspace:Raycast) hecha aquí mismo, sin tocar la infraestructura compartida.

	El rayo simulado «acierta» donde dice la verdad de datos_piezas.json (las muestras), con un error grande si el giro de
	los trozos no es el que hace falta: así se comprueba que el script detecta el giro, avisa de la escala equivocada,
	de los trozos que faltan, etc. Lo que NO prueba, porque no se puede fuera de Studio: lo que hace el importador de
	FBX y la colisión de verdad (eso lo mide el propio script en Studio).
]]

local fs = require("@lune/fs")
local luau = require("@lune/luau")
local serde = require("@lune/serde")

local CARPETA = "modelos/planeta_prueba"

-- ===== Simulación mínima de Roblox =====

local Vector3Meta = {}
local Vector3 = {}

function Vector3.new(x: number, y: number, z: number)
	return setmetatable({ X = x, Y = y, Z = z }, Vector3Meta)
end

Vector3Meta.__index = function(v, clave)
	if clave == "Magnitude" then
		return math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z)
	end
	return nil
end
Vector3Meta.__add = function(a, b)
	return Vector3.new(a.X + b.X, a.Y + b.Y, a.Z + b.Z)
end
Vector3Meta.__sub = function(a, b)
	return Vector3.new(a.X - b.X, a.Y - b.Y, a.Z - b.Z)
end
Vector3Meta.__unm = function(a)
	return Vector3.new(-a.X, -a.Y, -a.Z)
end
Vector3Meta.__mul = function(a, b)
	if type(a) == "number" then
		return Vector3.new(b.X * a, b.Y * a, b.Z * a)
	elseif type(b) == "number" then
		return Vector3.new(a.X * b, a.Y * b, a.Z * b)
	end
	return Vector3.new(a.X * b.X, a.Y * b.Y, a.Z * b.Z)
end

-- CFrame reducido a lo que usa el script: una posición y un giro en Y.
local CFrameMeta = {}
local CFrame = {}

function CFrame.new(posicion)
	return setmetatable({ Position = posicion, Yaw = 0 }, CFrameMeta)
end

function CFrame.Angles(_giroX: number, giroY: number, _giroZ: number)
	return setmetatable({ Position = Vector3.new(0, 0, 0), Yaw = giroY }, CFrameMeta)
end

CFrameMeta.__mul = function(a, b)
	return setmetatable({ Position = a.Position, Yaw = a.Yaw + b.Yaw }, CFrameMeta)
end

-- Como en Roblox, Destroy destruye también a los descendientes y bloquea su Parent.
local destruidas = setmetatable({}, { __mode = "k" })

local function crearInstancia(clase: string)
	local hijos = {}
	local propiedades = { ClassName = clase, Name = clase }
	local objeto = {}
	local meta = {}

	local function quitarDelPadre()
		local padre = propiedades.Parent
		if padre then
			for i, h in padre.__hijos do
				if h == objeto then
					table.remove(padre.__hijos, i)
					break
				end
			end
		end
	end

	meta.__index = function(_, clave)
		if clave == "__hijos" then
			return hijos
		end
		return propiedades[clave]
	end
	meta.__newindex = function(_, clave, valor)
		if clave == "Parent" then
			if destruidas[objeto] then
				error(`The Parent property of {propiedades.Name} is locked, current parent: NULL, new parent {valor}`)
			end
			quitarDelPadre()
			propiedades.Parent = valor
			if valor then
				table.insert(valor.__hijos, objeto)
			end
		else
			propiedades[clave] = valor
		end
	end
	setmetatable(objeto, meta)

	local esMalla = clase == "MeshPart"
	propiedades.IsA = function(self, nombre)
		return nombre == clase or nombre == "Instance" or (nombre == "BasePart" and esMalla)
	end
	propiedades.GetDescendants = function(self)
		local salida = {}
		local function recorrer(nodo)
			for _, h in nodo.__hijos do
				table.insert(salida, h)
				recorrer(h)
			end
		end
		recorrer(self)
		return salida
	end
	propiedades.FindFirstChild = function(self, nombre)
		for _, h in hijos do
			if h.Name == nombre then
				return h
			end
		end
		return nil
	end
	propiedades.FindFirstChildOfClass = function(self, nombreClase)
		for _, h in hijos do
			if h.ClassName == nombreClase then
				return h
			end
		end
		return nil
	end
	propiedades.Destroy = function(self)
		for _, d in self:GetDescendants() do
			destruidas[d] = true
		end
		destruidas[objeto] = true
		quitarDelPadre()
		propiedades.Parent = nil
	end
	if esMalla then
		propiedades.Size = Vector3.new(1, 1, 1)
		propiedades.CFrame = CFrame.new(Vector3.new(0, 0, 0))
	end
	return objeto
end

-- Enum: cualquier Enum.X.Y devuelve un objeto con Name = "Y".
local function nuevoEnum()
	return setmetatable({}, {
		__index = function(tabla, categoria)
			local c = setmetatable({}, {
				__index = function(cat, item)
					local valor = { Name = item, Categoria = categoria }
					rawset(cat, item, valor)
					return valor
				end,
			})
			rawset(tabla, categoria, c)
			return c
		end,
	})
end

--[[
	Un mundo de prueba. `opciones`:
	  escala       factor sobre el tamaño de las mallas importadas (1 = bien; 3.5714 = unidad Metro)
	  giroReal     giro (grados) con el que la geometría queda bien colocada
	  errorBase    error (studs) de la colisión respecto a la malla cuando el giro es el bueno
	  sinImpacto   los rayos no tocan nada
	  quitar       cuántos trozos no se importan
	  idPaleta     ID que se pone en AJUSTES.IdPaleta
	  giroFijado   valor de AJUSTES.GiroYGrados (nil = detectar)
]]
local function nuevoMundo(datos, opciones)
	opciones = opciones or {}
	local salida = { impresiones = {}, avisos = {}, esperas = 0 }

	local workspace = crearInstancia("Workspace")
	workspace.StreamingEnabled = true
	local importado = crearInstancia("Folder")
	importado.Name = "Importado"
	importado.Parent = workspace

	local escala = opciones.escala or 1
	for k, p in datos.piezas do
		if k > #datos.piezas - (opciones.quitar or 0) then
			break
		end
		local malla = crearInstancia("MeshPart")
		malla.Name = p.nombre
		malla.Size = Vector3.new(p.tamano[1] * escala, p.tamano[2] * escala, p.tamano[3] * escala)
		malla.Parent = importado
	end

	local giroReal = math.rad(opciones.giroReal or 0)
	local errorBase = opciones.errorBase or 0.4

	workspace.Raycast = function(_self, _origen, direccion, _params)
		if opciones.sinImpacto then
			return nil
		end
		local largo = direccion.Magnitude
		local hacia_fuera = Vector3.new(-direccion.X / largo, -direccion.Y / largo, -direccion.Z / largo)
		-- La muestra más cercana a esta dirección da el radio esperado de la superficie.
		local mejor, mejorProducto = nil, -2
		for _, m in datos.muestras do
			local producto = m[1] * hacia_fuera.X + m[2] * hacia_fuera.Y + m[3] * hacia_fuera.Z
			if producto > mejorProducto then
				mejor, mejorProducto = m, producto
			end
		end
		local radio = mejor[4]
		-- ¿Qué giro tienen ahora los trozos? Se mira el de la primera pieza colocada en el modelo.
		local modelo = workspace:FindFirstChild("PlanetaPrueba")
		local giroActual = giroReal
		if modelo and #modelo.__hijos > 0 then
			giroActual = modelo.__hijos[1].CFrame.Yaw
		end
		local mal = math.abs(giroActual - giroReal) > 1e-6
		local desviacion = if mal then 60 else errorBase
		return { Position = hacia_fuera * (radio + desviacion), Instance = modelo }
	end

	local servicios = {
		Workspace = workspace,
		Selection = { Get = function()
			return {}
		end },
	}
	local juego = {
		GetService = function(_, nombre)
			return servicios[nombre]
		end,
	}

	local entorno = {
		game = juego,
		Vector3 = Vector3,
		CFrame = CFrame,
		Enum = nuevoEnum(),
		Instance = { new = crearInstancia },
		RaycastParams = { new = function()
			return {}
		end },
		task = { wait = function()
			salida.esperas += 1
		end },
		print = function(...)
			table.insert(salida.impresiones, table.concat(table.pack(...), " "))
		end,
		warn = function(...)
			table.insert(salida.avisos, table.concat(table.pack(...), " "))
		end,
	}
	entorno.math, entorno.string, entorno.table, entorno.type = math, string, table, type
	entorno.tostring, entorno.tonumber, entorno.setmetatable = tostring, tonumber, setmetatable
	salida.entorno = entorno
	salida.workspace = workspace
	salida.importado = importado
	return salida
end

local function ejecutarScript(datos, opciones)
	opciones = opciones or {}
	local mundo = nuevoMundo(datos, opciones)
	local fuente = fs.readFile(`{CARPETA}/colocar_planeta.luau`)
	if opciones.idPaleta then
		fuente = string.gsub(fuente, 'IdPaleta = ""', `IdPaleta = "{opciones.idPaleta}"`)
	end
	if opciones.giroFijado then
		fuente = string.gsub(fuente, "GiroYGrados = nil", `GiroYGrados = {opciones.giroFijado}`)
	end
	local ejecutar = luau.load(fuente, { debugName = "colocar_planeta", environment = mundo.entorno })
	ejecutar()
	return mundo
end

return function(Marco)
	local datos = serde.decode("json", fs.readFile(`{CARPETA}/datos_piezas.json`))

	Marco.grupo("Planeta de prueba: datos de los trozos", function()
		Marco.prueba("cada trozo respeta los límites de MeshPart (triángulos y tamaño)", function()
			Marco.igual(datos.limites.triangulos, 20000)
			for _, p in datos.piezas do
				Marco.verdadero(p.triangulos <= datos.limites.triangulos, `{p.nombre}: {p.triangulos} triángulos`)
				for _, lado in p.tamano do
					Marco.verdadero(lado <= datos.limites.lado, `{p.nombre}: lado de {lado} studs`)
				end
			end
		end)

		Marco.prueba("hay 6·K² trozos con nombres distintos y su triángulo total cuadra", function()
			Marco.igual(#datos.piezas, 6 * datos.lado * datos.lado)
			local nombres, total = {}, 0
			for _, p in datos.piezas do
				Marco.esNil(nombres[p.nombre], `nombre repetido {p.nombre}`)
				nombres[p.nombre] = true
				total += p.triangulos
			end
			Marco.igual(total, datos.total_triangulos)
		end)

		Marco.prueba("las costuras entre las caras del cubo coinciden y el relieve es transitable", function()
			Marco.verdadero(datos.hueco_costuras < 0.001, `hueco entre caras {datos.hueco_costuras}`)
			Marco.verdadero(datos.estadisticas.pendiente_tierra_p50 < 15, "la pendiente mediana en tierra es alta")
			Marco.verdadero(datos.estadisticas.pendiente_tierra_p99 < 50, "el 1 % más empinado pasa de 50°")
		end)

		Marco.prueba("colocar_planeta.luau está al día con datos_piezas.json", function()
			local fuente = fs.readFile(`{CARPETA}/colocar_planeta.luau`)
			local _, filas = string.gsub(fuente, '\n\t{ Nombre = "Planeta_', "")
			Marco.igual(filas, #datos.piezas)
			local primera = datos.piezas[1]
			Marco.contiene(fuente, `Nombre = "{primera.nombre}"`)
			Marco.contiene(fuente, `local RADIO: number = {datos.radio}`)
			local _, muestras = string.gsub(fuente, "\n\t{ %-?[%d%.]+, %-?[%d%.]+, %-?[%d%.]+, [%d%.]+ },", "")
			Marco.igual(muestras, #datos.muestras)
		end)

		Marco.prueba("el script de Luau compila", function()
			luau.compile(fs.readFile(`{CARPETA}/colocar_planeta.luau`))
		end)
	end)

	Marco.grupo("Planeta de prueba: colocar_planeta.luau", function()
		Marco.prueba("con tamaño y giro correctos termina en CORRECTO y sin avisos", function()
			local mundo = ejecutarScript(datos, { idPaleta = "rbxassetid://123" })
			Marco.algunoContiene(mundo.impresiones, "CORRECTO con giro 0°")
			Marco.igual(#mundo.avisos, 0, table.concat(mundo.avisos, " | "))
		end)

		Marco.prueba("deja cada trozo anclado, con colisión precisa, textura y en su sitio", function()
			local mundo = ejecutarScript(datos, { idPaleta = "rbxassetid://123" })
			local modelo = mundo.workspace:FindFirstChild("PlanetaPrueba")
			Marco.distinto(modelo, nil)
			Marco.igual(#modelo.__hijos, #datos.piezas)
			for k, malla in modelo.__hijos do
				local pieza = datos.piezas[k]
				Marco.igual(malla.Name, pieza.nombre)
				Marco.verdadero(malla.Anchored and malla.CanCollide and malla.CanQuery, pieza.nombre)
				Marco.igual(malla.CollisionFidelity.Name, "PreciseConvexDecomposition")
				Marco.igual(malla.RenderFidelity.Name, "Precise")
				local p = malla.CFrame.Position
				Marco.verdadero(math.abs(p.X - pieza.centro[1]) < 1e-9 and math.abs(p.Z - pieza.centro[3]) < 1e-9, pieza.nombre)
				local aspecto = malla:FindFirstChildOfClass("SurfaceAppearance")
				Marco.distinto(aspecto, nil, `{pieza.nombre} sin SurfaceAppearance`)
				Marco.igual(aspecto.ColorMap, "rbxassetid://123")
			end
			Marco.esNil(mundo.importado:FindFirstChild("Planeta_XP_0_0"), "las mallas pasan del importador al modelo")
		end)

		Marco.prueba("si el importador giró los trozos 180°, lo detecta y se queda con ese giro", function()
			local mundo = ejecutarScript(datos, { idPaleta = "rbxassetid://123", giroReal = 180 })
			Marco.algunoContiene(mundo.impresiones, "giro 0°: ")
			Marco.algunoContiene(mundo.impresiones, "CORRECTO con giro 180°")
			local modelo = mundo.workspace:FindFirstChild("PlanetaPrueba")
			Marco.verdadero(math.abs(modelo.__hijos[1].CFrame.Yaw - math.rad(180)) < 1e-9)
		end)

		Marco.prueba("con el giro fijado en los ajustes no prueba otros", function()
			local mundo = ejecutarScript(datos, { idPaleta = "rbxassetid://123", giroFijado = 0 })
			Marco.igual(mundo.esperas, 1)
			Marco.algunoContiene(mundo.impresiones, "CORRECTO con giro 0°")
		end)

		Marco.prueba("si la colisión se desvía más de lo tolerado, avisa de que hay que revisar", function()
			local mundo = ejecutarScript(datos, { idPaleta = "rbxassetid://123", errorBase = 9 })
			Marco.algunoContiene(mundo.avisos, "REVISAR")
		end)

		Marco.prueba("si los rayos no tocan nada, avisa de que hay que revisar", function()
			local mundo = ejecutarScript(datos, { idPaleta = "rbxassetid://123", sinImpacto = true })
			Marco.algunoContiene(mundo.avisos, "REVISAR")
			Marco.algunoContiene(mundo.impresiones, "0/")
		end)

		Marco.prueba("si el importador usó la unidad Metro (×3,571), dice qué escala poner", function()
			local mundo = ejecutarScript(datos, { idPaleta = "rbxassetid://123", escala = 25 / 7 })
			Marco.algunoContiene(mundo.avisos, "NO tienen el tamaño esperado")
			Marco.algunoContiene(mundo.avisos, "3.571 veces")
			Marco.algunoContiene(mundo.avisos, "Custom Scale Factor = 0.2800")
			Marco.algunoContiene(mundo.avisos, "Scale Unit = Stud")
		end)

		Marco.prueba("avisa de los trozos que faltan, y de la paleta sin ID", function()
			local mundo = ejecutarScript(datos, { quitar = 5 })
			Marco.algunoContiene(mundo.avisos, "faltan 5 trozos")
			Marco.algunoContiene(mundo.avisos, "IdPaleta está vacío")
		end)

		Marco.prueba("sin ninguna malla Planeta_* no hace nada y lo dice", function()
			local mundo = ejecutarScript(datos, { quitar = 1000 })
			Marco.algunoContiene(mundo.avisos, "No hay ninguna MeshPart llamada Planeta_*")
			Marco.esNil(mundo.workspace:FindFirstChild("PlanetaPrueba"))
		end)

		Marco.prueba("volver a ejecutarlo reutiliza el modelo (destruirlo destruiría las mallas) y no duplica", function()
			local mundo = ejecutarScript(datos, { idPaleta = "rbxassetid://123" })
			local primero = mundo.workspace:FindFirstChild("PlanetaPrueba")
			Marco.distinto(primero, nil)
			-- La segunda ejecución busca otra vez en todo Workspace: las mallas ya están dentro del primer modelo.
			local fuente = fs.readFile(`{CARPETA}/colocar_planeta.luau`)
			luau.load(fuente, { debugName = "otra_vez", environment = mundo.entorno })()
			local contador = 0
			for _, h in mundo.workspace.__hijos do
				if h.Name == "PlanetaPrueba" then
					contador += 1
				end
			end
			Marco.igual(contador, 1)
			Marco.igual(#primero.__hijos, #datos.piezas)
		end)
	end)
end
