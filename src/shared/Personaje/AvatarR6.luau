--!strict
--[[
	AvatarR6: prepara el avatar real de Roblox del jugador (un HumanoidDescription) para ponerlo en un personaje R6.

	Sirve igual con un avatar R15 que con uno R6: el HumanoidDescription no depende del tipo de cuerpo, y aplicado a un
	Humanoid R6 se queda con lo que un R6 puede llevar. Lo que NO se puede (o no conviene) se quita antes y se apunta
	en el informe, para avisar al jugador:
	  · Ropa en capas (layered clothing): necesita el cuerpo R15, en R6 no se ajusta.
	  · Accesorios de más: máximo ConfigEditor.Avatar.MaxAccesorios, por rendimiento en móvil.
	  · Tamaño del cuerpo (alto, ancho, proporciones): el R6 mide siempre lo mismo.
	  · Animaciones y emotes del avatar: el juego usa las suyas.
	  · Partes del cuerpo de paquetes (torso, brazos, piernas): se ponen como en un R6 y pueden verse distintas.

	Lo usan el servidor (el personaje de verdad, con el UserId del jugador: no se fía del cliente) y el cliente (la vista
	previa del editor). Funciona sobre cualquier objeto con la forma de un HumanoidDescription (así se prueba con Lune).
]]

local AvatarR6 = {}

export type Informe = {
	Capas: number, -- prendas en capas quitadas
	Exceso: number, -- accesorios quitados por pasarse del máximo
	Limite: number, -- el máximo de accesorios
	Escalas: boolean, -- el cuerpo tenía un tamaño distinto del normal
	Animaciones: boolean, -- el avatar traía animaciones propias
	Emotes: number, -- emotes del avatar
	Partes: boolean, -- traía partes del cuerpo de un paquete
	Accesorios: number, -- accesorios que se quedan
}

-- Escalas y su valor normal. Todas se dejan en el normal.
local ESCALAS: { [string]: number } = {
	HeightScale = 1,
	WidthScale = 1,
	HeadScale = 1,
	DepthScale = 1,
	BodyTypeScale = 0,
	ProportionScale = 0,
}
local ANIMACIONES = {
	"ClimbAnimation",
	"FallAnimation",
	"IdleAnimation",
	"JumpAnimation",
	"MoodAnimation",
	"RunAnimation",
	"SwimAnimation",
	"WalkAnimation",
}
local PARTES = { "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg" }

--[[
	Deja `descripcion` lista para un R6 (la modifica: pásale una copia) y devuelve el informe de lo que se quitó.
	`limite`: máximo de accesorios que se dejan.
]]
function AvatarR6.Preparar(descripcion: any, limite: number): Informe
	local informe: Informe = {
		Capas = 0,
		Exceso = 0,
		Limite = limite,
		Escalas = false,
		Animaciones = false,
		Emotes = 0,
		Partes = false,
		Accesorios = 0,
	}

	-- Accesorios: fuera la ropa en capas; del resto, solo los primeros `limite`.
	local todos = descripcion:GetAccessories(true)
	local quedan = {}
	for _, a in todos do
		if a.IsLayered then
			informe.Capas += 1
		elseif #quedan < limite then
			table.insert(quedan, a)
		else
			informe.Exceso += 1
		end
	end
	if informe.Capas > 0 or informe.Exceso > 0 then
		descripcion:SetAccessories(quedan, true)
	end
	informe.Accesorios = #quedan

	for nombre, normal in ESCALAS do
		if math.abs((descripcion[nombre] :: number) - normal) > 1e-3 then
			informe.Escalas = true
			descripcion[nombre] = normal
		end
	end
	for _, nombre in ANIMACIONES do
		if descripcion[nombre] ~= 0 then
			informe.Animaciones = true
			descripcion[nombre] = 0
		end
	end
	local emotes = descripcion:GetEmotes()
	for _, _ in emotes do
		informe.Emotes += 1
	end
	if informe.Emotes > 0 then
		descripcion:SetEmotes({})
	end
	for _, nombre in PARTES do
		if descripcion[nombre] ~= 0 then
			informe.Partes = true
		end
	end
	return informe
end

-- Lo que no se pudo poner, en frases para el jugador. Vacía si se pudo todo.
function AvatarR6.Textos(informe: Informe): { string }
	local t = {}
	if informe.Capas > 0 then
		table.insert(t, `{informe.Capas} prenda(s) de ropa en capas no se pueden poner en R6.`)
	end
	if informe.Exceso > 0 then
		table.insert(
			t,
			`{informe.Exceso} accesorio(s) quitado(s): el máximo es {informe.Limite} para que vaya bien en móvil.`
		)
	end
	if informe.Escalas then
		table.insert(t, "El tamaño de tu cuerpo no se usa: el R6 mide siempre lo mismo.")
	end
	if informe.Animaciones or informe.Emotes > 0 then
		table.insert(t, "Tus animaciones y emotes de Roblox no se usan: el juego tiene los suyos.")
	end
	if informe.Partes then
		table.insert(t, "Las partes del cuerpo de tu paquete se ponen como en R6 y pueden verse distintas.")
	end
	return t
end

return AvatarR6
