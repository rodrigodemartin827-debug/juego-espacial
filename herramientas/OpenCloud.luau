--!strict
--[[
	Partes puras (sin red) de la subida de modelos a Roblox con la API Open Cloud de recursos («Assets»).
	Las usa herramientas/subir_modelos.luau y se prueban en pruebas/casos/OpenCloud.luau.

	API (https://create.roblox.com/docs/cloud/guides/usage-assets):
	  * Crear:      POST  https://apis.roblox.com/assets/v1/assets              (multipart: «request» y «fileContent»)
	  * Actualizar: PATCH https://apis.roblox.com/assets/v1/assets/{assetId}    (beta; solo .fbx; conserva el ID)
	  * Operación:  GET   https://apis.roblox.com/assets/v1/operations/{id}     (hasta que «done» sea true)
	  La clave va en la cabecera «x-api-key». Necesita el permiso «Assets» con lectura y escritura.

	LA CLAVE NUNCA SE ESCRIBE en ningún archivo ni en la salida: solo se lee de la variable de entorno y se manda en
	la cabecera.
]]

local OpenCloud = {}

OpenCloud.URL_RECURSOS = "https://apis.roblox.com/assets/v1/assets"
OpenCloud.URL_OPERACIONES = "https://apis.roblox.com/assets/v1/operations/"
OpenCloud.VARIABLE_CLAVE = "ROBLOX_API_KEY"
OpenCloud.VARIABLE_USUARIO = "ROBLOX_CREATOR_ID" -- ID numérico de la cuenta dueña de los modelos
OpenCloud.VARIABLE_GRUPO = "ROBLOX_GROUP_ID" -- o, si se sube a un grupo, su ID (tiene prioridad)
OpenCloud.TAMANO_MAXIMO = 20 * 1024 * 1024 -- 20 MB por archivo

-- Tipo de contenido por extensión (solo los formatos de modelo que acepta la API).
OpenCloud.TIPOS = {
	fbx = "model/fbx",
	gltf = "model/gltf+json",
	glb = "model/gltf-binary",
	rbxm = "model/x-rbxm",
	rbxmx = "model/x-rbxm",
}

export type Entrada = { id: number, sha256: string, subido: string? }
export type Registro = { [string]: Entrada } -- ruta relativa (con «/») -> recurso subido
export type Creador = { userId: string } | { groupId: string }

-- Extensión en minúsculas de una ruta, o nil.
function OpenCloud.extension(ruta: string): string?
	local ext = string.match(ruta, "%.([%w]+)$")
	return if ext then string.lower(ext) else nil
end

-- Imágenes: solo se suben si se pide (--imagenes), porque las carpetas de modelos tienen texturas que van
-- incrustadas en los .fbx y no deben subirse sueltas. Se suben como «Decal».
OpenCloud.IMAGENES = {
	png = "image/png",
}

function OpenCloud.tipoContenido(ruta: string, conImagenes: boolean?): string?
	local ext = OpenCloud.extension(ruta)
	if ext == nil then
		return nil
	end
	return OpenCloud.TIPOS[ext] or (if conImagenes then OpenCloud.IMAGENES[ext] else nil)
end

-- Tipo de recurso de Roblox según el archivo: «Decal» para imágenes, «Animation» para los .rbxm/.rbxmx cuando se
-- sube con --animaciones (son KeyframeSequence) y «Model» para el resto de modelos.
function OpenCloud.tipoRecurso(ruta: string, comoAnimacion: boolean?): string
	local ext = OpenCloud.extension(ruta)
	if ext and OpenCloud.IMAGENES[ext] then
		return "Decal"
	end
	if comoAnimacion and (ext == "rbxm" or ext == "rbxmx") then
		return "Animation"
	end
	return "Model"
end

-- Nombre del archivo sin carpeta ni extensión («piezas/Puente__lejos.fbx» -> «Puente__lejos»).
function OpenCloud.nombreBase(ruta: string): string
	local archivo = string.match(ruta, "([^/\\]+)$") or ruta
	return (string.gsub(archivo, "%.[^%.]+$", ""))
end

-- Normaliza una ruta relativa para usarla como clave del registro (barras «/», sin «./» delante).
function OpenCloud.clave(ruta: string): string
	local r = string.gsub(ruta, "\\", "/")
	r = string.gsub(r, "^%./", "")
	return r
end

-- Creador a partir de las variables de entorno (el grupo tiene prioridad). Devuelve nil y el motivo si falta.
function OpenCloud.creador(usuario: string?, grupo: string?): (Creador?, string?)
	if grupo and grupo ~= "" then
		if not string.match(grupo, "^%d+$") then
			return nil, OpenCloud.VARIABLE_GRUPO .. " tiene que ser un número"
		end
		return { groupId = grupo }, nil
	end
	if usuario and usuario ~= "" then
		if not string.match(usuario, "^%d+$") then
			return nil, OpenCloud.VARIABLE_USUARIO .. " tiene que ser un número"
		end
		return { userId = usuario }, nil
	end
	return nil, "falta " .. OpenCloud.VARIABLE_USUARIO .. " (o " .. OpenCloud.VARIABLE_GRUPO .. ")"
end

-- JSON del campo «request». Al crear lleva el creador; al actualizar, el ID del recurso.
function OpenCloud.peticion(
	nombre: string,
	descripcion: string,
	creador: Creador,
	idExistente: number?,
	tipoRecurso: string?
): { [string]: any }
	local p: { [string]: any } = {
		assetType = tipoRecurso or "Model",
		displayName = nombre,
		description = descripcion,
		creationContext = { creator = creador },
	}
	if idExistente then
		p.assetId = tostring(idExistente)
	end
	return p
end

--[[
	Cuerpo multipart/form-data con los dos campos de la API. Devuelve el cuerpo y la cabecera Content-Type.
	El contenido del archivo va tal cual (binario): las cadenas de Luau admiten cualquier byte.
]]
function OpenCloud.multipart(
	peticionJson: string,
	nombreArchivo: string,
	tipo: string,
	contenido: string,
	frontera: string
): (string, string)
	assert(not string.find(contenido, "--" .. frontera, 1, true), "la frontera aparece dentro del archivo")
	local partes = {
		"--" .. frontera,
		'Content-Disposition: form-data; name="request"',
		"Content-Type: application/json",
		"",
		peticionJson,
		"--" .. frontera,
		string.format('Content-Disposition: form-data; name="fileContent"; filename="%s"', nombreArchivo),
		"Content-Type: " .. tipo,
		"",
		contenido,
		"--" .. frontera .. "--",
		"",
	}
	return table.concat(partes, "\r\n"), "multipart/form-data; boundary=" .. frontera
end

-- ID de operación de la respuesta de crear/actualizar ({"path": "operations/<id>"}).
function OpenCloud.idOperacion(respuesta: { [string]: any }): string?
	local ruta = respuesta.path
	if type(ruta) ~= "string" then
		return nil
	end
	return string.match(ruta, "operations/([%w%-]+)$")
end

-- Resultado de una operación terminada: ID del recurso y estado de moderación (o nil si aún no ha terminado).
function OpenCloud.resultado(operacion: { [string]: any }): (number?, string?)
	if operacion.done ~= true then
		return nil, nil
	end
	local r = operacion.response
	if type(r) ~= "table" then
		return nil, nil
	end
	local id = tonumber(r.assetId) or tonumber(string.match(tostring(r.path or ""), "assets/(%d+)"))
	local moderacion = if type(r.moderationResult) == "table" then r.moderationResult.moderationState else nil
	return id, moderacion
end

--[[
	Qué archivos hay que subir: los pedidos (o todos los candidatos, si no se pide ninguno) cuyo contenido ha cambiado
	desde la última subida. Devuelve una lista ordenada de { ruta, sha256, id? }: con id, se actualiza ese recurso.
]]
function OpenCloud.pendientes(
	candidatos: { [string]: string }, -- ruta -> sha256 actual
	registro: Registro,
	pedidos: { string }?,
	forzar: boolean?
): { { ruta: string, sha256: string, id: number? } }
	local lista = {}
	local rutas: { string } = {}
	if pedidos and #pedidos > 0 then
		for _, r in pedidos do
			table.insert(rutas, OpenCloud.clave(r))
		end
	else
		for r in candidatos do
			table.insert(rutas, r)
		end
	end
	table.sort(rutas)
	for _, r in rutas do
		local hash = candidatos[r]
		assert(hash ~= nil, "no existe el archivo " .. r)
		local anterior = registro[r]
		if forzar or anterior == nil or anterior.sha256 ~= hash then
			table.insert(lista, { ruta = r, sha256 = hash, id = if anterior then anterior.id else nil })
		end
	end
	return lista
end

return OpenCloud
