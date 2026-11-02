--!strict
--[[
	Crafteo (reglas): decide si se puede fabricar una receta y qué cambia en los datos del jugador. FUNCIONES PURAS.

	  Planificar   mira los datos del jugador y devuelve un PLAN: si se puede, qué se gasta y qué se obtiene; si no,
	               el motivo. NO modifica nada.
	  Aplicar      ejecuta un plan que salió bien, modificando los datos EN SITIO.

	El servidor llama a las dos seguidas, sin esperas entre medias (Servicios/ServicioCrafteo), así que no hay forma de
	que los datos cambien entre la comprobación y el cobro. El cliente usa solo Planificar para pintar la lista de
	ingredientes (en verde lo que tiene, en rojo lo que falta) y activar o no el botón.

	Los datos que usa son los del jugador (Datos/Tipos): Inventario, Monedas y MejorasNave.
]]

local Estadisticas = require(script.Parent.Parent.Naves.Estadisticas)
local Inventario = require(script.Parent.Inventario)
local Mejoras = require(script.Parent.Parent.Naves.Datos.Mejoras)
local Config = require(script.Parent.Config)
local Recetas = require(script.Parent.Datos.Recetas)

export type Requisito = {
	Id: string, -- id del objeto, o "Monedas"
	Necesita: number,
	Tiene: number,
}

-- Por qué no se puede fabricar.
export type Motivo =
	"RecetaDesconocida"
	| "CantidadInvalida"
	| "NivelMaximo"
	| "FaltanMateriales"
	| "FaltanMonedas"
	| "BodegaLlena"

export type Plan = {
	Ok: boolean,
	Motivo: Motivo?,
	Receta: string,
	Cantidad: number, -- veces que se fabrica la receta
	Requisitos: { Requisito }, -- ingredientes (y monedas) con lo que se necesita y lo que se tiene
	Quita: { [string]: number }, -- objetos que se gastan
	Monedas: number, -- monedas que se gastan
	Anade: { [string]: number }, -- objetos que se obtienen
	Mejora: string?, -- id de la mejora de la nave que sube...
	NivelNuevo: number?, -- ...y el nivel al que pasa
}

type DatosCrafteo = {
	Inventario: { [string]: number },
	Monedas: number,
	MejorasNave: { [string]: number },
}

local Crafteo = {}

-- Textos para mostrar al jugador, uno por motivo.
Crafteo.Mensajes = table.freeze(({
	RecetaDesconocida = "Esa receta no existe",
	CantidadInvalida = "Cantidad no válida",
	NivelMaximo = "Esa mejora ya está al máximo",
	FaltanMateriales = "Te faltan materiales",
	FaltanMonedas = "Te faltan monedas",
	BodegaLlena = "No te cabe en la bodega: mejora la Carga o libera espacio",
} :: any) :: { [string]: string })

-- Cantidad que pide una receta para ese nivel: fija, o `Base + PorNivel * nivel` redondeado hacia arriba.
function Crafteo.Cantidad(valor: Recetas.Cantidad, nivel: number): number
	if type(valor) == "number" then
		return valor
	end
	return math.ceil(valor.Base + valor.PorNivel * nivel)
end

local function nivelDe(datos: DatosCrafteo, idMejora: string): number
	return Estadisticas.NivelValido(datos.MejorasNave[idMejora])
end

local function fallo(motivo: Motivo, receta: string, cantidad: number, requisitos: { Requisito }?): Plan
	return {
		Ok = false,
		Motivo = motivo,
		Receta = receta,
		Cantidad = cantidad,
		Requisitos = requisitos or {},
		Quita = {},
		Monedas = 0,
		Anade = {},
	}
end

--[[
	Evalúa fabricar `cantidad` veces la receta `idReceta` (las mejoras solo se fabrican de una en una) con los datos del
	jugador y el límite de su bodega. Devuelve siempre un plan; si `Ok` es false, `Motivo` dice por qué y `Requisitos` sigue
	rellenado para poder enseñarlo en la interfaz.
]]
function Crafteo.Planificar(datos: DatosCrafteo, idReceta: string, capacidad: number, cantidad: number?): Plan
	local veces = cantidad or 1
	local receta = Recetas.Lista[idReceta]
	if receta == nil then
		return fallo("RecetaDesconocida", idReceta, veces)
	end
	if
		veces ~= veces
		or veces ~= math.floor(veces)
		or veces < 1
		or veces > Config.CantidadMaximaPorPeticion
		or (receta.Categoria == "Mejora" and veces ~= 1)
	then
		return fallo("CantidadInvalida", idReceta, veces)
	end

	-- Una mejora cuesta según el nivel que tiene ahora; un objeto, siempre como nivel 0.
	local idMejora = receta.Resultado.Mejora
	local nivel = if idMejora then nivelDe(datos, idMejora) else 0
	if idMejora and (Mejoras.Lista[idMejora] == nil or nivel >= Mejoras.NivelMaximo) then
		return fallo("NivelMaximo", idReceta, veces)
	end

	-- Requisitos: ingredientes en el orden de la receta (alfabético, para que sea estable) y monedas.
	local quita: { [string]: number } = {}
	local requisitos: { Requisito } = {}
	local faltaMaterial = false
	local ids = {}
	for id in receta.Ingredientes do
		table.insert(ids, id)
	end
	table.sort(ids)
	for _, id in ids do
		local necesita = Crafteo.Cantidad(receta.Ingredientes[id], nivel) * veces
		local tiene = Inventario.Cantidad(datos.Inventario, id)
		quita[id] = necesita
		table.insert(requisitos, { Id = id, Necesita = necesita, Tiene = tiene })
		if tiene < necesita then
			faltaMaterial = true
		end
	end
	local monedas = if receta.Monedas then Crafteo.Cantidad(receta.Monedas, nivel) * veces else 0
	if monedas > 0 then
		table.insert(requisitos, { Id = "Monedas", Necesita = monedas, Tiene = datos.Monedas })
	end

	local plan: Plan = {
		Ok = false,
		Receta = idReceta,
		Cantidad = veces,
		Requisitos = requisitos,
		Quita = quita,
		Monedas = monedas,
		Anade = {},
	}

	if faltaMaterial then
		plan.Motivo = "FaltanMateriales"
		return plan
	end
	if datos.Monedas < monedas then
		plan.Motivo = "FaltanMonedas"
		return plan
	end

	if idMejora then
		plan.Mejora = idMejora
		plan.NivelNuevo = nivel + 1
	else
		local objeto = receta.Resultado.Objeto :: string
		plan.Anade[objeto] = (receta.Resultado.Cantidad or 1) * veces

		-- ¿Cabe el resultado una vez gastados los ingredientes? (Se prueba sobre una copia.)
		local copia = table.clone(datos.Inventario)
		for id, cuanto in quita do
			Inventario.Quitar(copia, id, cuanto)
		end
		for id, cuanto in plan.Anade do
			if Inventario.Anadir(copia, capacidad, id, cuanto) < cuanto then
				plan.Motivo = "BodegaLlena"
				return plan
			end
		end
	end

	plan.Ok = true
	return plan
end

--[[
	Ejecuta un plan que salió bien: gasta los ingredientes y las monedas y entrega el resultado (objetos al inventario o
	un nivel más en la mejora). Modifica `datos` en sitio. Con un plan que no esté Ok, o si los datos ya no lo permiten,
	no cambia nada y devuelve false.
]]
function Crafteo.Aplicar(datos: DatosCrafteo, plan: Plan, capacidad: number): boolean
	if not plan.Ok then
		return false
	end
	-- Se vuelve a comprobar contra los datos actuales: si algo cambió desde Planificar, no se cobra nada.
	local actual = Crafteo.Planificar(datos, plan.Receta, capacidad, plan.Cantidad)
	if not actual.Ok then
		return false
	end

	for id, cuanto in actual.Quita do
		Inventario.Quitar(datos.Inventario, id, cuanto)
	end
	datos.Monedas -= actual.Monedas
	for id, cuanto in actual.Anade do
		Inventario.Anadir(datos.Inventario, capacidad, id, cuanto)
	end
	if actual.Mejora and actual.NivelNuevo then
		datos.MejorasNave[actual.Mejora] = actual.NivelNuevo
	end
	return true
end

return Crafteo
