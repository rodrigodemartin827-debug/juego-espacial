--!strict
--[[
	Compras (reglas): decide si un jugador puede comprar un artículo en una tienda y qué cambia en sus datos.
	FUNCIONES PURAS, igual que Exploracion/Crafteo:

	  Planificar   mira los datos del jugador y devuelve un PLAN: si se puede, cuánto cuesta y qué se obtiene; si no, el
	               motivo. NO modifica nada.
	  Aplicar      ejecuta un plan que salió bien, modificando los datos EN SITIO (vuelve a comprobarlo todo antes).

	El servidor llama a las dos seguidas, sin esperas entre medias (Servicios/ServicioTiendas), así que nadie puede colarse
	entre la comprobación y el cobro ni duplicar una compra mandando dos peticiones a la vez. El cliente usa solo
	Planificar para pintar el panel (precio en verde o en rojo, botón activo o no).

	Lo que NO comprueba (porque depende del mundo, no de los datos): la distancia al mostrador y si el jugador está vivo o
	pilotando. Eso lo hace el servicio del servidor antes de planificar.
]]

local Estadisticas = require(script.Parent.Parent.Naves.Estadisticas)
local Inventario = require(script.Parent.Parent.Exploracion.Inventario)
local Mejoras = require(script.Parent.Parent.Naves.Datos.Mejoras)
local Objetos = require(script.Parent.Parent.Exploracion.Datos.Objetos)
local Catalogo = require(script.Parent.Datos.Catalogo)
local Config = require(script.Parent.Config)

-- Por qué no se puede comprar, en el orden en que se comprueba.
export type Motivo =
	"TiendaDesconocida"
	| "ArticuloDesconocido"
	| "NoSeVendeAqui"
	| "CantidadInvalida"
	| "BandoVetado"
	| "PersianaBajada"
	| "NivelMaximo"
	| "FaltanMonedas"
	| "BodegaLlena"

export type Plan = {
	Ok: boolean,
	Motivo: Motivo?,
	Tienda: string,
	Articulo: string,
	Cantidad: number, -- veces que se compra el artículo
	PrecioUnidad: number, -- monedas de una compra
	Precio: number, -- monedas en total
	Tiene: number, -- monedas que tiene el jugador (para la interfaz)
	Anade: { [string]: number }, -- objetos que se obtienen
	Mejora: string?, -- id de la mejora de la nave que sube...
	NivelNuevo: number?, -- ...y el nivel al que pasa
}

type DatosCompra = {
	Bando: string,
	Inventario: { [string]: number },
	Monedas: number,
	MejorasNave: { [string]: number },
}

local Compras = {}

-- Textos para mostrar al jugador, uno por motivo.
Compras.Mensajes = table.freeze(({
	TiendaDesconocida = "Esa tienda no existe",
	ArticuloDesconocido = "Ese artículo no existe",
	NoSeVendeAqui = "Esta tienda no vende eso",
	CantidadInvalida = "Cantidad no válida",
	BandoVetado = "Aquí no se atiende a los monstruos",
	PersianaBajada = "La tienda está cerrada: hay un monstruo cerca",
	NivelMaximo = "Esa mejora ya está al máximo",
	FaltanMonedas = "No tienes monedas suficientes",
	BodegaLlena = "No te cabe en la bodega: mejora la Carga o libera espacio",
} :: any) :: { [string]: string })

-- ¿Las tiendas se niegan a atender a este bando? (Config.BandosVetados: los Monstruos.)
function Compras.EsVetado(bando: any): boolean
	return type(bando) == "string" and table.find(Config.BandosVetados, bando) ~= nil
end

-- Precio de una compra para ese nivel: fijo, o `Base + PorNivel * nivel` redondeado hacia arriba.
function Compras.Precio(precio: Catalogo.Precio, nivel: number): number
	if type(precio) == "number" then
		return precio
	end
	return math.ceil(precio.Base + precio.PorNivel * nivel)
end

local function esCantidadValida(cantidad: number, maximo: number): boolean
	return cantidad == cantidad and cantidad == math.floor(cantidad) and cantidad >= 1 and cantidad <= maximo
end

--[[
	Evalúa comprar `cantidad` veces (1 si se omite) el artículo `idArticulo` en la tienda `idTienda`, con los datos del
	jugador y el espacio de su bodega (`capacidad`). `persianaBajada` es el estado de la persiana de ESA tienda según el
	servidor. Devuelve siempre un plan; si `Ok` es false, `Motivo` dice por qué.
]]
function Compras.Planificar(
	datos: DatosCompra,
	idTienda: string,
	idArticulo: string,
	capacidad: number,
	cantidad: number?,
	persianaBajada: boolean?
): Plan
	local veces = cantidad or 1
	local plan: Plan = {
		Ok = false,
		Tienda = idTienda,
		Articulo = idArticulo,
		Cantidad = veces,
		PrecioUnidad = 0,
		Precio = 0,
		Tiene = datos.Monedas,
		Anade = {},
	}
	local function fallo(motivo: Motivo): Plan
		plan.Motivo = motivo
		return plan
	end

	if Catalogo.Tiendas[idTienda] == nil then
		return fallo("TiendaDesconocida")
	end
	local articulo = Catalogo.Articulos[idArticulo]
	if articulo == nil then
		return fallo("ArticuloDesconocido")
	end
	if not Catalogo.Vende(idTienda, idArticulo) then
		return fallo("NoSeVendeAqui")
	end
	local maximo = if articulo.Categoria == "Mejora" then 1 else Config.CantidadMaximaPorPeticion
	if type(veces) ~= "number" or not esCantidadValida(veces, maximo) then
		return fallo("CantidadInvalida")
	end
	if Compras.EsVetado(datos.Bando) then
		return fallo("BandoVetado")
	end
	if persianaBajada == true and Config.CerradaParaTodosConPersianaBajada then
		return fallo("PersianaBajada")
	end

	-- Una mejora cuesta según el nivel que tiene ahora; un material, siempre lo mismo.
	local idMejora = articulo.Resultado.Mejora
	local nivel = if idMejora then Estadisticas.NivelValido(datos.MejorasNave[idMejora]) else 0
	plan.PrecioUnidad = Compras.Precio(articulo.Precio, nivel)
	plan.Precio = plan.PrecioUnidad * veces
	if idMejora and (Mejoras.Lista[idMejora] == nil or nivel >= Mejoras.NivelMaximo) then
		return fallo("NivelMaximo")
	end
	if datos.Monedas < plan.Precio then
		return fallo("FaltanMonedas")
	end

	if idMejora then
		plan.Mejora = idMejora
		plan.NivelNuevo = nivel + 1
	else
		local objeto = articulo.Resultado.Objeto :: string
		local unidades = (articulo.Resultado.Cantidad or 1) * veces
		plan.Anade[objeto] = unidades
		if Objetos.Lista[objeto] == nil or Inventario.CuantoCabe(datos.Inventario, capacidad, objeto) < unidades then
			return fallo("BodegaLlena")
		end
	end

	plan.Ok = true
	return plan
end

--[[
	Ejecuta un plan que salió bien: cobra las monedas y entrega el resultado (objetos al inventario o un nivel más en la
	mejora). Modifica `datos` en sitio. Si el plan no está Ok, o los datos ya no lo permiten (se vuelve a planificar con
	los datos actuales), no cambia nada y devuelve false.
]]
function Compras.Aplicar(datos: DatosCompra, plan: Plan, capacidad: number, persianaBajada: boolean?): boolean
	if not plan.Ok then
		return false
	end
	local actual = Compras.Planificar(datos, plan.Tienda, plan.Articulo, capacidad, plan.Cantidad, persianaBajada)
	if not actual.Ok or actual.Precio ~= plan.Precio then
		return false
	end

	datos.Monedas -= actual.Precio
	for id, cuanto in actual.Anade do
		Inventario.Anadir(datos.Inventario, capacidad, id, cuanto)
	end
	if actual.Mejora and actual.NivelNuevo then
		datos.MejorasNave[actual.Mejora] = actual.NivelNuevo
	end
	return true
end

return Compras
