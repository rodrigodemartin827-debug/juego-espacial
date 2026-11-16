--!strict
-- Crea los Attachments de acople en las piezas de nave importadas (generado por nave_piezas.py: no editar a mano).
--
-- Uso: importa el .fbx de una o varias piezas, selecciónalas en el Explorer (el Model o sus MeshParts) y pega este
-- script en View → Command Bar. En cada MeshPart que tenga acoples crea un Attachment con el nombre del acople,
-- su Position y Orientation, y los atributos Tipo, Direccion, Brida y Acepta (tipos separados por comas).
--
-- Regla de encaje (la que debe aplicar el hangar):
--   * Una entrada encaja en una salida si el tipo de la salida está en Acepta de la entrada (o alguno es UNIVERSAL)
--     y su brida no es más grande que la de la salida.
--   * pieza.CFrame = salida.WorldCFrame * CFrame.Angles(0, math.pi, 0) * entrada.CFrame:Inverse()
--     (las normales quedan opuestas y los "arriba" coinciden). Con MeshParts el CFrame de la pieza es el de la
--     MeshPart que tiene la entrada; el resto del Model se mueve con ella (PivotTo).

local Selection = game:GetService("Selection")

type Acople = {
	malla: string,
	nombre: string,
	tipo: string,
	direccion: string,
	brida: number,
	pos: Vector3,
	rot: Vector3,
	acepta: { string },
}

local PIEZAS: { [string]: { Acople } } = {
--[[PIEZAS]]
}

-- Índice malla -> lista de acoples
local porMalla: { [string]: { Acople } } = {}
for _, lista in PIEZAS do
	for _, a in lista do
		porMalla[a.malla] = porMalla[a.malla] or {}
		table.insert(porMalla[a.malla], a)
	end
end

local creados = 0
local function montar(parte: Instance)
	if not parte:IsA("MeshPart") then
		return
	end
	local lista = porMalla[parte.Name]
	if not lista then
		return
	end
	for _, a in lista do
		local att = parte:FindFirstChild(a.nombre)
		if not (att and att:IsA("Attachment")) then
			att = Instance.new("Attachment")
			att.Name = a.nombre
			att.Parent = parte
		end
		local at = att :: Attachment
		at.Position = a.pos
		at.Orientation = a.rot
		at:SetAttribute("Tipo", a.tipo)
		at:SetAttribute("Direccion", a.direccion)
		at:SetAttribute("Brida", a.brida)
		at:SetAttribute("Acepta", table.concat(a.acepta, ","))
		creados += 1
	end
end

for _, sel in Selection:Get() do
	montar(sel)
	for _, d in sel:GetDescendants() do
		montar(d)
	end
end
print(string.format("[montar_acoples] %d acoples creados o actualizados", creados))
