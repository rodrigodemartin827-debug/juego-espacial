--!strict
--[[
	Sube modelos (.fbx) a Roblox con la API Open Cloud y apunta sus IDs en <carpeta>/datos/ids_modelos.json, para
	insertarlos después en Studio por su ID (ver src/shared/Herramientas/ModelosNube.luau) en vez de importarlos a mano.

	Uso, desde la raíz del repositorio:
		lune run herramientas/subir_modelos <carpeta> piezas/Puente.fbx silueta/Aurora_Silueta.fbx
		lune run herramientas/subir_modelos <carpeta>              -- solo enseña qué ha cambiado (no sube nada)
		lune run herramientas/subir_modelos <carpeta> --todo       -- sube todo lo que ha cambiado
	Opciones:
		--prueba   no se conecta: dice qué subiría
		--forzar   sube aunque el archivo no haya cambiado
		--nuevo    crea un recurso nuevo aunque ya tenga ID (por defecto se actualiza el mismo ID)

	<carpeta> es la carpeta «roblox» de una región (por ejemplo modelos/region1_valle_del_alba/roblox). Se miran
	todos los modelos que haya dentro, salvo la carpeta «datos». Un archivo solo se sube si su contenido ha cambiado
	desde la última vez (se compara su SHA-256).

	Variables de entorno (de la cuenta de Windows; se leen aunque se hayan creado con la terminal ya abierta):
		ROBLOX_API_KEY      la clave de API (permiso «Assets», lectura y escritura). NUNCA se escribe en ningún sitio.
		ROBLOX_CREATOR_ID   el ID numérico de la cuenta dueña de los modelos
		ROBLOX_GROUP_ID     (opcional) para subirlos a un grupo en vez de a la cuenta
]]

local fs = require("@lune/fs")
local net = require("@lune/net")
local process = require("@lune/process")
local serde = require("@lune/serde")
local task = require("@lune/task")

local OpenCloud = require("./OpenCloud")

-- ===== Argumentos =====

local carpeta: string? = nil
local pedidos: { string } = {}
local opciones = { prueba = false, forzar = false, nuevo = false, todo = false }
for _, a in process.args do
	if string.sub(a, 1, 2) == "--" then
		local o = string.sub(a, 3)
		if (opciones :: any)[o] == nil then
			error("opción desconocida: " .. a)
		end
		(opciones :: any)[o] = true
	elseif carpeta == nil then
		carpeta = string.gsub(a, "[/\\]+$", "")
	else
		table.insert(pedidos, a)
	end
end
if carpeta == nil then
	print("Uso: lune run herramientas/subir_modelos <carpeta> [archivos...] [--todo] [--prueba] [--forzar] [--nuevo]")
	process.exit(1)
end
local raiz = carpeta :: string
local rutaRegistro = raiz .. "/datos/ids_modelos.json"

-- ===== Archivos y registro =====

local function listar(rel: string, salida: { [string]: string })
	local dir = if rel == "" then raiz else raiz .. "/" .. rel
	for _, nombre in fs.readDir(dir) do
		local r = if rel == "" then nombre else rel .. "/" .. nombre
		local completa = raiz .. "/" .. r
		if fs.isDir(completa) then
			if r ~= "datos" then
				listar(r, salida)
			end
		elseif OpenCloud.tipoContenido(r) then
			salida[r] = serde.hash("sha256", fs.readFile(completa))
		end
	end
end

local candidatos: { [string]: string } = {}
listar("", candidatos)

local registro: OpenCloud.Registro = {}
if fs.isFile(rutaRegistro) then
	registro = serde.decode("json", fs.readFile(rutaRegistro))
end

local function guardarRegistro()
	-- Claves ordenadas para que los cambios se lean bien en git.
	local claves = {}
	for k in registro do
		table.insert(claves, k)
	end
	table.sort(claves)
	local lineas = {}
	for _, k in claves do
		local e = registro[k]
		table.insert(
			lineas,
			string.format(
				'  %s: {"id": %d, "sha256": "%s", "subido": "%s"}',
				serde.encode("json", k),
				e.id,
				e.sha256,
				e.subido or ""
			)
		)
	end
	fs.writeFile(rutaRegistro, "{\n" .. table.concat(lineas, ",\n") .. "\n}\n")
end

if #pedidos == 0 and not opciones.todo then
	local lista = OpenCloud.pendientes(candidatos, registro, nil, false)
	local total = 0
	for _ in candidatos do
		total += 1
	end
	print(string.format("%d modelos en %s; %d han cambiado o no se han subido nunca:", total, raiz, #lista))
	for i, p in lista do
		if i > 40 then
			print(string.format("  ... y %d más", #lista - 40))
			break
		end
		print("  " .. p.ruta .. (if p.id then "  (ya tiene ID " .. p.id .. ")" else ""))
	end
	print("Para subirlos: añade las rutas o --todo.")
	process.exit(0)
end

local lista = OpenCloud.pendientes(candidatos, registro, pedidos, opciones.forzar)
if #lista == 0 then
	print("Nada que subir: no ha cambiado ninguno.")
	process.exit(0)
end
for _, p in lista do
	local tam = #fs.readFile(raiz .. "/" .. p.ruta)
	assert(tam <= OpenCloud.TAMANO_MAXIMO, p.ruta .. " pasa de 20 MB")
end
if opciones.prueba then
	for _, p in lista do
		local accion = if p.id and not opciones.nuevo then "actualizar " .. p.id else "crear"
		print(string.format("  %-40s %s", p.ruta, accion))
	end
	print(string.format("%d modelos (prueba: no se ha subido nada)", #lista))
	process.exit(0)
end

-- ===== Credenciales (la clave no se imprime nunca) =====

local function variable(nombre: string): string?
	local v = process.env[nombre]
	if v and v ~= "" then
		return v
	end
	-- En Windows, una variable de usuario recién creada no llega a las terminales que ya estaban abiertas: se lee
	-- directamente de la cuenta. La salida va a esta variable, no a la pantalla.
	if process.os == "windows" then
		local r = process.exec("powershell", {
			"-NoProfile",
			"-NonInteractive",
			"-Command",
			string.format("[Environment]::GetEnvironmentVariable('%s','User')", nombre),
		})
		local s = string.gsub(r.stdout, "%s+$", "")
		if r.ok and s ~= "" then
			return s
		end
	end
	return nil
end

local clave = variable(OpenCloud.VARIABLE_CLAVE)
if clave == nil then
	print("Falta la variable de entorno " .. OpenCloud.VARIABLE_CLAVE .. " (ver docs/open_cloud.md).")
	process.exit(1)
end
local creador, motivo = OpenCloud.creador(variable(OpenCloud.VARIABLE_USUARIO), variable(OpenCloud.VARIABLE_GRUPO))
if creador == nil then
	print("No se puede subir: " .. tostring(motivo) .. " (ver docs/open_cloud.md).")
	process.exit(1)
end

-- ===== Red =====

local function pedir(metodo: string, url: string, cuerpo: string?, tipo: string?): (number, any)
	local cabeceras: { [string]: string } = { ["x-api-key"] = clave :: string }
	if tipo then
		cabeceras["content-type"] = tipo
	end
	for intento = 1, 5 do
		local r = net.request({ url = url, method = metodo :: any, headers = cabeceras, body = cuerpo })
		if r.statusCode == 429 or r.statusCode >= 500 then
			-- Límite de peticiones o error del servidor: se espera y se reintenta.
			task.wait(2 * intento)
		else
			local ok, datos = pcall(serde.decode, "json" :: "json", r.body)
			return r.statusCode, if ok then datos else r.body
		end
	end
	return 0, "sin respuesta tras 5 intentos"
end

local function fronteraPara(contenido: string): string
	while true do
		local f = "----juego-espacial-"
			.. string.format("%08x%08x", math.random(0, 0x7fffffff), math.random(0, 0x7fffffff))
		if not string.find(contenido, f, 1, true) then
			return f
		end
	end
end

local function esperarOperacion(idOp: string): (number?, string?)
	for _ = 1, 90 do
		local codigo, op = pedir("GET", OpenCloud.URL_OPERACIONES .. idOp)
		if codigo ~= 200 then
			return nil, "operación " .. idOp .. ": HTTP " .. codigo .. " " .. serde.encode("json", op)
		end
		local id, moderacion = OpenCloud.resultado(op)
		if id then
			return id, moderacion
		end
		task.wait(2)
	end
	return nil, "la operación " .. idOp .. " no ha terminado en 3 minutos"
end

-- ===== Subida =====

local fallos = 0
for _, p in lista do
	local contenido = fs.readFile(raiz .. "/" .. p.ruta)
	local nombre = OpenCloud.nombreBase(p.ruta)
	local actualizar = p.id ~= nil and not opciones.nuevo and OpenCloud.extension(p.ruta) == "fbx"
	local peticion = OpenCloud.peticion(
		nombre,
		"juego-espacial: " .. p.ruta,
		creador :: OpenCloud.Creador,
		if actualizar then p.id else nil
	)
	local cuerpo, tipo = OpenCloud.multipart(
		serde.encode("json", peticion),
		string.match(p.ruta, "([^/]+)$") or p.ruta,
		OpenCloud.tipoContenido(p.ruta) :: string,
		contenido,
		fronteraPara(contenido)
	)
	local url = if actualizar then OpenCloud.URL_RECURSOS .. "/" .. tostring(p.id) else OpenCloud.URL_RECURSOS
	local codigo, respuesta = pedir(if actualizar then "PATCH" else "POST", url, cuerpo, tipo)
	local idOp = if codigo == 200 and type(respuesta) == "table" then OpenCloud.idOperacion(respuesta) else nil
	if idOp == nil then
		fallos += 1
		print(string.format("✗ %s: HTTP %d %s", p.ruta, codigo, serde.encode("json", respuesta)))
		continue
	end
	local id, moderacion = esperarOperacion(idOp)
	if id == nil then
		fallos += 1
		print("✗ " .. p.ruta .. ": " .. tostring(moderacion))
		continue
	end
	registro[p.ruta] = { id = id, sha256 = p.sha256, subido = os.date("!%Y-%m-%dT%H:%M:%SZ") :: string }
	guardarRegistro() -- después de cada uno: si algo falla a medias, lo subido queda apuntado
	print(
		string.format(
			"✓ %s -> %d (%s%s)",
			p.ruta,
			id,
			if actualizar then "actualizado" else "nuevo",
			if moderacion then ", " .. moderacion else ""
		)
	)
end
print(string.format("%d subidos, %d con error. IDs en %s", #lista - fallos, fallos, rutaRegistro))
process.exit(if fallos > 0 then 1 else 0)
