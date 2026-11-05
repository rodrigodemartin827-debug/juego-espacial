--!strict
--[[
	SOLO EN STUDIO (modo edición): inserta modelos subidos con herramientas/subir_modelos.luau por su ID y sustituye
	las plantillas de una carpeta, en vez de importar los .fbx a mano con el importador 3D.

	Cada modelo subido es un Model con una MeshPart dentro. La MeshPart nueva ocupa el sitio de la plantilla con su
	mismo nombre: conserva sus atributos, su CFrame, su color y su padre; la vieja se borra. Lo que solo se puede poner
	en Studio (SurfaceAppearance, RenderFidelity, colisión precisa) lo pone después el paso de preparación de cada
	región (por ejemplo EjemploArranque.prepararPiezasEnStudio en la región 1).
]]

local InsertService = game:GetService("InsertService")

local ModelosNube = {}

export type Resultado = { nombre: string, antes: string?, despues: string, id: number }

-- Carga el recurso y devuelve su MeshPart (la primera que tenga). Falla si no hay ninguna.
function ModelosNube.cargarMalla(id: number): MeshPart
	local ok, modelo = pcall(function()
		return InsertService:LoadAsset(id)
	end)
	local raiz: Instance
	if ok and modelo then
		raiz = modelo
	else
		-- En algunos contextos de Studio LoadAsset no deja; GetObjects sí carga lo que es de la cuenta.
		local objetos = (game :: any):GetObjects("rbxassetid://" .. tostring(id))
		assert(objetos and objetos[1], "no se ha podido cargar el recurso " .. id .. ": " .. tostring(modelo))
		raiz = objetos[1]
	end
	local malla = if raiz:IsA("MeshPart") then raiz else raiz:FindFirstChildWhichIsA("MeshPart", true)
	assert(malla, "el recurso " .. id .. " no tiene ninguna MeshPart")
	local m = malla :: MeshPart
	m.Parent = nil
	if raiz ~= m then
		raiz:Destroy()
	end
	-- Los modelos subidos por Open Cloud llegan como paquetes: la plantilla no debe quedar enlazada.
	for _, d in m:GetDescendants() do
		if d:IsA("PackageLink") then
			d:Destroy()
		end
	end
	return m
end

-- Pone `nueva` en lugar de la plantilla `nombre` de `carpeta` (si no existe, la añade). Devuelve el MeshId anterior.
function ModelosNube.sustituir(carpeta: Instance, nombre: string, nueva: MeshPart): string?
	local vieja = carpeta:FindFirstChild(nombre)
	nueva.Name = nombre
	nueva.Anchored = true
	local antes: string? = nil
	if vieja and vieja:IsA("MeshPart") then
		antes = vieja.MeshId
		for k, v in vieja:GetAttributes() do
			nueva:SetAttribute(k, v)
		end
		nueva.CFrame = vieja.CFrame
		nueva.Color = vieja.Color
		nueva.CanCollide = vieja.CanCollide
		nueva.CastShadow = vieja.CastShadow
	end
	nueva.Parent = carpeta
	if vieja then
		vieja:Destroy()
	end
	return antes
end

--[[
	Inserta varios: `ids` es el registro de subir_modelos ({ ["piezas/Puente.fbx"] = { id = ... } }) y `destino` dice,
	para cada ruta, en qué carpeta va y con qué nombre (o nil para saltarla). `solo` limita a esas rutas.
]]
function ModelosNube.insertar(
	ids: { [string]: { id: number } },
	destino: (ruta: string) -> (Instance?, string?),
	solo: { string }?
): { Resultado }
	local rutas: { string } = {}
	if solo then
		rutas = table.clone(solo)
	else
		for r in ids do
			table.insert(rutas, r)
		end
	end
	table.sort(rutas)
	local resultados = {}
	for _, r in rutas do
		local e = ids[r]
		assert(e, "no hay ID para " .. r .. " (súbelo antes con herramientas/subir_modelos)")
		local carpeta, nombre = destino(r)
		if carpeta and nombre then
			local nueva = ModelosNube.cargarMalla(e.id)
			local antes = ModelosNube.sustituir(carpeta, nombre, nueva)
			table.insert(resultados, { nombre = nombre, antes = antes, despues = nueva.MeshId, id = e.id })
		end
	end
	return resultados
end

return ModelosNube
