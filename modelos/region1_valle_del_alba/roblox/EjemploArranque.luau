--!strict
--[[
	EjemploArranque: cómo se usan MontarRegion y LodRegion. Es un EJEMPLO: no está enganchado al juego (src/) porque
	la región todavía no se ha importado ni probado en Studio.

	Se espera esta estructura en ReplicatedStorage (la parte de datos la puede sincronizar Rojo: cada .json de
	roblox/datos se convierte en un ModuleScript que devuelve su tabla):

	  ReplicatedStorage.Region1
	    Datos       (ModuleScripts) piezas, terreno, silueta_Aurora, lod, edificios_<Sitio>, objetos_<Sitio>
	      vegetacion (ModuleScripts) <f>_<c>  (uno por trozo de terreno)
	    Piezas      (MeshParts importadas de roblox/piezas, con el atlas puesto)
	    Terreno     (MeshParts importadas de roblox/terreno)
	    Silueta     (MeshPart importada de roblox/silueta)

	1) En Studio, UNA vez (barra de comandos): EjemploArranque.montarEnStudio({...ids...}) y guardar el lugar.
	2) En el cliente (un LocalScript): EjemploArranque.iniciarCliente().
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local MontarRegion = require(script.Parent:WaitForChild("MontarRegion"))
local LodRegion = require(script.Parent:WaitForChild("LodRegion"))

local EjemploArranque = {}

local function datosDe(carpeta: Instance): MontarRegion.Datos
	local d = carpeta:WaitForChild("Datos")
	local grupos = {}
	for _, m in d:GetChildren() do
		if m:IsA("ModuleScript") and (string.find(m.Name, "^edificios_") or string.find(m.Name, "^objetos_")) then
			grupos[m.Name] = require(m) :: any
		end
	end
	local silueta = d:FindFirstChild("silueta_Aurora")
	return {
		piezas = require(d:WaitForChild("piezas") :: ModuleScript) :: any,
		grupos = grupos,
		terreno = require(d:WaitForChild("terreno") :: ModuleScript) :: any,
		silueta = if silueta then require(silueta :: ModuleScript) :: any else nil,
	}
end

local function opcionesMontaje(
	idAtlas: string?,
	idsTerreno: { [string]: string }?,
	destino: Instance,
	origen: CFrame?
): MontarRegion.Opciones
	local carpeta = ReplicatedStorage:WaitForChild("Region1")
	local silueta = carpeta:FindFirstChild("Silueta")
	local sil: MeshPart? = nil
	if silueta then
		local s = silueta:FindFirstChildWhichIsA("MeshPart")
		if s then
			sil = s
		elseif silueta:IsA("MeshPart") then
			sil = silueta
		end
	end
	return {
		Piezas = carpeta:WaitForChild("Piezas"),
		Terreno = carpeta:WaitForChild("Terreno"),
		Silueta = sil,
		IdAtlas = idAtlas,
		IdsTerreno = idsTerreno,
		Destino = destino,
		Datos = datosDe(carpeta),
		Origen = origen,
	}
end

-- En Studio: monta la región en Workspace (con el atlas y las texturas de terreno ya subidas). `origen` es el marco del
-- centro del planeta (nil = el origen del mundo, como en Blender).
function EjemploArranque.montarEnStudio(idAtlas: string, idsTerreno: { [string]: string }, origen: CFrame?): Model
	return MontarRegion.montar(opcionesMontaje(idAtlas, idsTerreno, workspace, origen))
end

-- En el cliente: niveles de detalle y vegetación. Devuelve una función para pararlo.
function EjemploArranque.iniciarCliente(idAtlas: string?, origen: CFrame?): () -> ()
	local carpeta = ReplicatedStorage:WaitForChild("Region1")
	local region = workspace:WaitForChild("Region1_ValleDelAlba") :: Model
	local montaje = opcionesMontaje(idAtlas, nil, workspace, origen)
	local d = carpeta:WaitForChild("Datos")
	local vegetacion: { [string]: { { any } } } = {}
	local carpetaVeg = d:FindFirstChild("vegetacion")
	if carpetaVeg then
		for _, m in carpetaVeg:GetChildren() do
			if m:IsA("ModuleScript") then
				vegetacion[m.Name] = require(m) :: any
			end
		end
	end
	local trozos: { [string]: { centro: Vector3, radio: number } } = {}
	for _, t in montaje.Datos.terreno do
		if t.nivel == "detalle" then
			trozos[t.trozo] =
				{ centro = Vector3.new(t.centro_lod[1], t.centro_lod[2], t.centro_lod[3]), radio = t.radio }
		end
	end
	return LodRegion.iniciar({
		Region = region,
		Montaje = montaje,
		Lod = require(d:WaitForChild("lod") :: ModuleScript) :: any,
		Vegetacion = vegetacion,
		TrozosTerreno = trozos,
	})
end

return EjemploArranque
