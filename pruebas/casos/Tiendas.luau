--[[
	Pruebas de la lógica pura de las tiendas: catálogo, reglas de compra (bando, persiana, monedas, nivel máximo,
	bodega, atomicidad), cuándo sube y baja la persiana y las curvas de su animación.
]]

local Entorno = require("../infraestructura/Entorno")

local function cargar(ruta: string)
	return Entorno.nuevo().servidor.requerir(`ReplicatedStorage.Shared.{ruta}`)
end

return function(Marco)
	local Config = cargar("Tiendas.Config")
	local Catalogo = cargar("Tiendas.Datos.Catalogo")
	local DatosPersiana = cargar("Tiendas.Datos.Persiana")
	local Compras = cargar("Tiendas.Compras")
	local Persiana = cargar("Tiendas.Persiana")
	local Objetos = cargar("Exploracion.Datos.Objetos")
	local Recetas = cargar("Exploracion.Datos.Recetas")
	local Crafteo = cargar("Exploracion.Crafteo")
	local Mejoras = cargar("Naves.Datos.Mejoras")
	local Estadisticas = cargar("Naves.Estadisticas")
	local Bandos = cargar("Juego.Bandos")
	local Esquema = Entorno.nuevo().servidor.requerir("ServerScriptService.Server.Servicios.ServicioDatos.Esquema")

	local TIENDA = "MercadoColonia"

	-- Datos de un jugador con lo indicado (el resto, de un jugador nuevo).
	local function jugador(bando, monedas, inventario, mejoras)
		local datos = Esquema.Nuevo()
		datos.Bando = bando or "Humanos"
		datos.Monedas = monedas or 0
		datos.Inventario = inventario or {}
		for id, nivel in mejoras or {} do
			datos.MejorasNave[id] = nivel
		end
		return datos
	end

	local function capacidad(datos)
		return Estadisticas.Calcular(datos.MejorasNave).Capacidad
	end

	Marco.grupo("Tiendas: catálogo", function()
		Marco.prueba("todos los artículos están en Orden y tienen datos completos", function()
			local enOrden = {}
			for _, id in Catalogo.Orden do
				Marco.falso(enOrden[id], `'{id}' está repetido en Orden`)
				enOrden[id] = true
				Marco.distinto(Catalogo.Articulos[id], nil, `Orden nombra '{id}', que no existe`)
			end
			for id, articulo in Catalogo.Articulos do
				Marco.verdadero(enOrden[id], `'{id}' no está en Catalogo.Orden`)
				Marco.verdadero(#articulo.Nombre > 0 and #articulo.Descripcion > 0, `{id}: falta texto`)
				if articulo.Categoria == "Material" then
					Marco.distinto(Objetos.Lista[articulo.Resultado.Objeto], nil, `{id}: da un objeto que no existe`)
					Marco.verdadero((articulo.Resultado.Cantidad or 1) >= 1, `{id}: cantidad`)
					Marco.igual(type(articulo.Precio), "number", `{id}: un material tiene precio fijo`)
				else
					Marco.igual(articulo.Categoria, "Mejora", `{id}: categoría`)
					Marco.distinto(Mejoras.Lista[articulo.Resultado.Mejora], nil, `{id}: mejora que no existe`)
				end
				for nivel = 0, Mejoras.NivelMaximo - 1 do
					local precio = Compras.Precio(articulo.Precio, nivel)
					Marco.verdadero(precio >= 1 and precio == math.floor(precio), `{id}: precio {precio} en nivel {nivel}`)
				end
			end
		end)

		Marco.prueba("cada tienda vende artículos que existen, sin repetir, y hay al menos una", function()
			Marco.verdadero(#Catalogo.IdsTiendas() >= 1)
			Marco.distinto(Catalogo.Tiendas[TIENDA], nil, "la tienda de ejemplo existe")
			for id, tienda in Catalogo.Tiendas do
				Marco.verdadero(#tienda.Articulos > 0, `{id}: no vende nada`)
				local vistos = {}
				for _, articulo in tienda.Articulos do
					Marco.distinto(Catalogo.Articulos[articulo], nil, `{id} vende '{articulo}', que no existe`)
					Marco.falso(vistos[articulo], `{id} repite '{articulo}'`)
					vistos[articulo] = true
				end
			end
		end)

		Marco.prueba("la tienda de ejemplo vende materiales y todas las mejoras de la nave", function()
			local mejoras = {}
			local hayMaterial = false
			for _, id in Catalogo.Tiendas[TIENDA].Articulos do
				local articulo = Catalogo.Articulos[id]
				if articulo.Categoria == "Mejora" then
					mejoras[articulo.Resultado.Mejora] = true
				else
					hayMaterial = true
				end
			end
			Marco.verdadero(hayMaterial, "vende materiales")
			for _, id in Mejoras.Orden do
				Marco.verdadero(mejoras[id], `no vende la mejora {id}`)
			end
		end)

		Marco.prueba("Vende distingue lo que vende cada tienda", function()
			Marco.verdadero(Catalogo.Vende("Suministros", "Hierro"))
			Marco.falso(Catalogo.Vende("Suministros", "MejoraCasco"))
			Marco.verdadero(Catalogo.Vende("Astillero", "MejoraCasco"))
			Marco.falso(Catalogo.Vende("NoExiste", "Hierro"))
		end)

		Marco.prueba("comprar una mejora cuesta más monedas que fabricarla en la mesa (no hace inútil explorar)", function()
			for _, idReceta in Recetas.Orden do
				local receta = Recetas.Lista[idReceta]
				local idMejora = receta.Resultado.Mejora
				if idMejora then
					for _, idArticulo in Catalogo.Orden do
						local articulo = Catalogo.Articulos[idArticulo]
						if articulo.Resultado.Mejora == idMejora then
							for nivel = 0, Mejoras.NivelMaximo - 1 do
								local mesa = if receta.Monedas then Crafteo.Cantidad(receta.Monedas, nivel) else 0
								Marco.verdadero(
									Compras.Precio(articulo.Precio, nivel) > mesa * 2,
									`{idArticulo} nivel {nivel}: demasiado barata frente a la mesa`
								)
							end
						end
					end
				end
			end
		end)

		Marco.prueba("los Monstruos son el bando vetado y los Humanos no", function()
			Marco.verdadero(Compras.EsVetado(Bandos.Monstruos))
			Marco.falso(Compras.EsVetado(Bandos.Humanos))
			Marco.falso(Compras.EsVetado(Bandos.Ninguno))
			Marco.falso(Compras.EsVetado(nil))
			Marco.falso(Compras.EsVetado(7))
		end)

		Marco.prueba("la configuración es coherente", function()
			Marco.verdadero(Config.RadioApertura > Config.RadioCierre, "la histéresis necesita RadioApertura > RadioCierre")
			Marco.verdadero(Config.RadioCierre > Config.AlcanceTienda, "la persiana baja antes de que el monstruo llegue")
			Marco.verdadero(Config.SegundosParaReabrir > 0)
			Marco.verdadero(Config.IntervaloVigilancia > 0 and Config.IntervaloVigilancia <= 0.5)
			Marco.verdadero(Config.CantidadMaximaPorPeticion >= 1)
			for _, bando in Config.BandosVetados do
				Marco.verdadero(Bandos.EsElegible(bando), `bando vetado desconocido: {bando}`)
			end
		end)
	end)

	Marco.grupo("Tiendas: reglas de compra", function()
		Marco.prueba("un humano con monedas compra un material: cobra y lo mete en la bodega", function()
			local datos = jugador("Humanos", 100)
			local plan = Compras.Planificar(datos, TIENDA, "Hierro", capacidad(datos), 5)
			Marco.verdadero(plan.Ok, plan.Motivo)
			Marco.igual(plan.Precio, Catalogo.Articulos.Hierro.Precio * 5)
			Marco.igual(plan.Anade.Hierro, 5)
			Marco.igual(datos.Monedas, 100, "Planificar no cambia nada")

			Marco.verdadero(Compras.Aplicar(datos, plan, capacidad(datos)))
			Marco.igual(datos.Monedas, 100 - plan.Precio)
			Marco.igual(datos.Inventario.Hierro, 5)
		end)

		Marco.prueba("sin cantidad se compra una vez", function()
			local datos = jugador("Humanos", 100)
			local plan = Compras.Planificar(datos, TIENDA, "Cobre", capacidad(datos))
			Marco.verdadero(plan.Ok)
			Marco.igual(plan.Cantidad, 1)
			Marco.igual(plan.Anade.Cobre, 1)
		end)

		Marco.prueba("una mejora sube un nivel y su precio crece con el nivel", function()
			local datos = jugador("Humanos", 100000, nil, { Casco = 3 })
			local plan = Compras.Planificar(datos, TIENDA, "MejoraCasco", capacidad(datos))
			Marco.verdadero(plan.Ok, plan.Motivo)
			Marco.igual(plan.Mejora, "Casco")
			Marco.igual(plan.NivelNuevo, 4)
			Marco.igual(plan.Precio, Compras.Precio(Catalogo.Articulos.MejoraCasco.Precio, 3))
			Marco.verdadero(Compras.Aplicar(datos, plan, capacidad(datos)))
			Marco.igual(datos.MejorasNave.Casco, 4)
			Marco.igual(datos.Monedas, 100000 - plan.Precio)

			local siguiente = Compras.Planificar(datos, TIENDA, "MejoraCasco", capacidad(datos))
			Marco.verdadero(siguiente.Precio > plan.Precio, "el nivel siguiente cuesta más")
		end)

		Marco.prueba("a un monstruo no se le vende nada, tenga lo que tenga", function()
			local datos = jugador("Monstruos", 1000000)
			for _, id in Catalogo.Tiendas[TIENDA].Articulos do
				local plan = Compras.Planificar(datos, TIENDA, id, capacidad(datos))
				Marco.falso(plan.Ok, id)
				Marco.igual(plan.Motivo, "BandoVetado", id)
				Marco.falso(Compras.Aplicar(datos, plan, capacidad(datos)), id)
			end
			Marco.igual(datos.Monedas, 1000000)
			Marco.igual(next(datos.Inventario), nil)
		end)

		Marco.prueba("con la persiana bajada la tienda está cerrada para todos", function()
			local datos = jugador("Humanos", 1000)
			local plan = Compras.Planificar(datos, TIENDA, "Hierro", capacidad(datos), 1, true)
			Marco.falso(plan.Ok)
			Marco.igual(plan.Motivo, if Config.CerradaParaTodosConPersianaBajada then "PersianaBajada" else nil)
			Marco.verdadero(Compras.Planificar(datos, TIENDA, "Hierro", capacidad(datos), 1, false).Ok)
		end)

		Marco.prueba("si la persiana baja entre Planificar y Aplicar, no se cobra", function()
			local datos = jugador("Humanos", 1000)
			local plan = Compras.Planificar(datos, TIENDA, "Hierro", capacidad(datos), 2, false)
			Marco.verdadero(plan.Ok)
			Marco.falso(Compras.Aplicar(datos, plan, capacidad(datos), true))
			Marco.igual(datos.Monedas, 1000)
			Marco.esNil(datos.Inventario.Hierro)
		end)

		Marco.prueba("sin monedas suficientes no se compra, y el plan dice cuánto falta", function()
			local datos = jugador("Humanos", 10)
			local plan = Compras.Planificar(datos, TIENDA, "Titanio", capacidad(datos), 1)
			Marco.falso(plan.Ok)
			Marco.igual(plan.Motivo, "FaltanMonedas")
			Marco.igual(plan.Tiene, 10)
			Marco.igual(plan.Precio, Catalogo.Articulos.Titanio.Precio)
		end)

		Marco.prueba("con el dinero justo se puede, con uno menos no", function()
			local precio = Catalogo.Articulos.Cristal.Precio * 3
			Marco.verdadero(Compras.Planificar(jugador("Humanos", precio), TIENDA, "Cristal", 1000, 3).Ok)
			Marco.igual(
				Compras.Planificar(jugador("Humanos", precio - 1), TIENDA, "Cristal", 1000, 3).Motivo,
				"FaltanMonedas"
			)
		end)

		Marco.prueba("una mejora al máximo no se vende", function()
			local datos = jugador("Humanos", 10000000, nil, { Motor = Mejoras.NivelMaximo })
			local plan = Compras.Planificar(datos, TIENDA, "MejoraMotor", capacidad(datos))
			Marco.falso(plan.Ok)
			Marco.igual(plan.Motivo, "NivelMaximo")
		end)

		Marco.prueba("si no cabe en la bodega no se compra (y no se cobra)", function()
			local datos = jugador("Humanos", 100000)
			local cap = capacidad(datos)
			-- Bodega llena de hierro.
			datos.Inventario.Hierro = math.floor(cap / Objetos.Volumen("Hierro"))
			local plan = Compras.Planificar(datos, TIENDA, "Cobre", cap, 1)
			Marco.falso(plan.Ok)
			Marco.igual(plan.Motivo, "BodegaLlena")
			Marco.falso(Compras.Aplicar(datos, plan, cap))
			Marco.igual(datos.Monedas, 100000)
		end)

		Marco.prueba("las mejoras no ocupan bodega: se compran aunque esté llena", function()
			local datos = jugador("Humanos", 100000)
			local cap = capacidad(datos)
			datos.Inventario.Hierro = math.floor(cap / Objetos.Volumen("Hierro"))
			Marco.verdadero(Compras.Planificar(datos, TIENDA, "MejoraCarga", cap).Ok)
		end)

		Marco.prueba("cantidades no válidas se rechazan; las mejoras solo de una en una", function()
			local datos = jugador("Humanos", 100000)
			local cap = capacidad(datos)
			for _, cantidad in { 0, -1, 1.5, 0 / 0, math.huge, Config.CantidadMaximaPorPeticion + 1 } do
				Marco.igual(
					Compras.Planificar(datos, TIENDA, "Hierro", cap, cantidad).Motivo,
					"CantidadInvalida",
					tostring(cantidad)
				)
			end
			Marco.igual(Compras.Planificar(datos, TIENDA, "MejoraCasco", cap, 2).Motivo, "CantidadInvalida")
			Marco.verdadero(Compras.Planificar(datos, TIENDA, "Hierro", cap, Config.CantidadMaximaPorPeticion).Ok)
		end)

		Marco.prueba("tiendas y artículos desconocidos, o que la tienda no vende, se rechazan", function()
			local datos = jugador("Humanos", 100000)
			local cap = capacidad(datos)
			Marco.igual(Compras.Planificar(datos, "NoExiste", "Hierro", cap).Motivo, "TiendaDesconocida")
			Marco.igual(Compras.Planificar(datos, TIENDA, "NoExiste", cap).Motivo, "ArticuloDesconocido")
			Marco.igual(Compras.Planificar(datos, "Suministros", "MejoraCasco", cap).Motivo, "NoSeVendeAqui")
			Marco.igual(Compras.Planificar(datos, "Astillero", "Hierro", cap).Motivo, "NoSeVendeAqui")
		end)

		Marco.prueba("dos compras seguidas con dinero para una sola: la segunda no se cobra", function()
			local precio = Catalogo.Articulos.PlacaTitanio.Precio
			local datos = jugador("Humanos", precio + 5)
			local cap = capacidad(datos)
			-- Las dos peticiones se planifican antes de aplicar ninguna (como si llegaran a la vez).
			local primera = Compras.Planificar(datos, TIENDA, "PlacaTitanio", cap)
			local segunda = Compras.Planificar(datos, TIENDA, "PlacaTitanio", cap)
			Marco.verdadero(primera.Ok and segunda.Ok)
			Marco.verdadero(Compras.Aplicar(datos, primera, cap))
			Marco.falso(Compras.Aplicar(datos, segunda, cap), "Aplicar vuelve a comprobar las monedas")
			Marco.igual(datos.Monedas, 5)
			Marco.igual(datos.Inventario.PlacaTitanio, 1)
		end)

		Marco.prueba("si el precio cambió entre Planificar y Aplicar (subió el nivel), no se cobra", function()
			local datos = jugador("Humanos", 100000)
			local cap = capacidad(datos)
			local plan = Compras.Planificar(datos, TIENDA, "MejoraEscudo", cap)
			datos.MejorasNave.Escudo = 5 -- p. ej. lo subió en la mesa de crafteo entre medias
			Marco.falso(Compras.Aplicar(datos, plan, cap))
			Marco.igual(datos.Monedas, 100000)
			Marco.igual(datos.MejorasNave.Escudo, 5)
		end)

		Marco.prueba("Aplicar no acepta un plan que no salió bien", function()
			local datos = jugador("Humanos", 0)
			local plan = Compras.Planificar(datos, TIENDA, "Hierro", capacidad(datos))
			Marco.falso(plan.Ok)
			datos.Monedas = 1000 -- aunque ahora sí pudiera
			Marco.falso(Compras.Aplicar(datos, plan, capacidad(datos)))
			Marco.igual(datos.Monedas, 1000)
		end)

		Marco.prueba("hay un mensaje para cada motivo", function()
			for _, motivo in
				{
					"TiendaDesconocida",
					"ArticuloDesconocido",
					"NoSeVendeAqui",
					"CantidadInvalida",
					"BandoVetado",
					"PersianaBajada",
					"NivelMaximo",
					"FaltanMonedas",
					"BodegaLlena",
				}
			do
				Marco.verdadero(type(Compras.Mensajes[motivo]) == "string", motivo)
			end
		end)
	end)

	Marco.grupo("Tiendas: cuándo sube y baja la persiana", function()
		local REGLAS = { RadioCierre = 40, RadioApertura = 55, SegundosParaReabrir = 2 }

		Marco.prueba("empieza subida y no baja sin monstruos cerca", function()
			local estado = Persiana.Nuevo()
			Marco.falso(estado.Bajada)
			Marco.falso(Persiana.Evaluar(estado, math.huge, 0, REGLAS))
			Marco.falso(Persiana.Evaluar(estado, 41, 1, REGLAS))
			Marco.falso(estado.Bajada)
		end)

		Marco.prueba("baja en cuanto un monstruo entra en el radio de cierre", function()
			local estado = Persiana.Nuevo()
			Marco.verdadero(Persiana.Evaluar(estado, 40, 0, REGLAS), "justo en el borde también cierra")
			Marco.verdadero(estado.Bajada)
			Marco.falso(Persiana.Evaluar(estado, 10, 0.2, REGLAS), "ya estaba bajada: no hay cambio")
		end)

		Marco.prueba("no sube mientras el monstruo siga dentro del radio de apertura (histéresis)", function()
			local estado = Persiana.Nuevo()
			Persiana.Evaluar(estado, 30, 0, REGLAS)
			for t = 1, 20 do
				Marco.falso(Persiana.Evaluar(estado, 50, t, REGLAS), `segundo {t}`)
			end
			Marco.verdadero(estado.Bajada)
		end)

		Marco.prueba("sube cuando lleva los segundos indicados sin monstruos", function()
			local estado = Persiana.Nuevo()
			Persiana.Evaluar(estado, 30, 0, REGLAS)
			Marco.falso(Persiana.Evaluar(estado, math.huge, 10, REGLAS), "empieza a contar")
			Marco.falso(Persiana.Evaluar(estado, math.huge, 11.9, REGLAS), "aún no")
			Marco.verdadero(Persiana.Evaluar(estado, math.huge, 12, REGLAS), "ya")
			Marco.falso(estado.Bajada)
			Marco.esNil(estado.LibreDesde)
		end)

		Marco.prueba("si el monstruo vuelve antes de tiempo, la cuenta empieza de cero", function()
			local estado = Persiana.Nuevo()
			Persiana.Evaluar(estado, 30, 0, REGLAS)
			Persiana.Evaluar(estado, 80, 1, REGLAS) -- se va
			Persiana.Evaluar(estado, 45, 2.5, REGLAS) -- vuelve (dentro del radio de apertura)
			Marco.falso(Persiana.Evaluar(estado, 80, 3.2, REGLAS))
			Marco.falso(Persiana.Evaluar(estado, 80, 5.1, REGLAS), "solo lleva 1,9 s libre")
			Marco.verdadero(Persiana.Evaluar(estado, 80, 5.2, REGLAS))
		end)

		Marco.prueba("una distancia NaN cuenta como monstruo encima", function()
			local estado = Persiana.Nuevo()
			Marco.verdadero(Persiana.Evaluar(estado, 0 / 0, 0, REGLAS))
			Marco.verdadero(estado.Bajada)
		end)

		Marco.prueba("sin reglas usa las de Tiendas/Config", function()
			local estado = Persiana.Nuevo()
			Marco.falso(Persiana.Evaluar(estado, Config.RadioCierre + 0.01, 0))
			Marco.verdadero(Persiana.Evaluar(estado, Config.RadioCierre, 0))
		end)
	end)

	Marco.grupo("Tiendas: curvas de la animación de la persiana", function()
		local T = DatosPersiana.Tiempos

		Marco.prueba("bajar empieza recogida y termina exactamente en el suelo", function()
			Marco.igual(Persiana.Valor("Cierre", 0), 0)
			Marco.igual(Persiana.Valor("Cierre", -1), 0)
			Marco.igual(Persiana.Valor("Cierre", Persiana.Duracion("Cierre")), 1)
			Marco.igual(Persiana.Valor("Cierre", Persiana.Duracion("Cierre") + 5), 1)
		end)

		Marco.prueba("subir empieza en el suelo y termina exactamente recogida", function()
			Marco.igual(Persiana.Valor("Apertura", 0), 1)
			Marco.igual(Persiana.Valor("Apertura", Persiana.Duracion("Apertura")), 0)
			Marco.igual(Persiana.Valor("Apertura", Persiana.Duracion("Apertura") + 5), 0)
		end)

		Marco.prueba("anticipación: antes de caer asoma un poco y vuelve a recogerse", function()
			local medio = Persiana.Valor("Cierre", T.Anticipacion / 2)
			Marco.verdadero(medio > 0 and medio <= T.AmplitudAnticipacion + 1e-9, `asoma {medio}`)
			Marco.verdadero(Persiana.Valor("Cierre", T.Anticipacion - 1e-4) < 0.005, "se recoge antes de caer")
		end)

		Marco.prueba("la caída se acelera (cada tramo recorre más que el anterior)", function()
			local anterior, tramoAnterior = Persiana.Valor("Cierre", T.Anticipacion), 0
			for paso = 1, 10 do
				local valor = Persiana.Valor("Cierre", T.Anticipacion + T.Caida * paso / 10 - 1e-6)
				local tramo = valor - anterior
				Marco.verdadero(tramo > tramoAnterior - 1e-6, `tramo {paso}`)
				anterior, tramoAnterior = valor, tramo
			end
		end)

		Marco.prueba("impacto: se queda clavada (hitstop) y luego rebota sin pasar del suelo", function()
			local impacto = Persiana.InstanteImpacto()
			Marco.igual(impacto, T.Anticipacion + T.Caida)
			Marco.igual(Persiana.Valor("Cierre", impacto + T.Congelado / 2), 1)
			local minimo = 1
			for paso = 0, 40 do
				local valor = Persiana.Valor("Cierre", impacto + T.Congelado + T.Rebote * paso / 40)
				Marco.verdadero(valor <= 1 + 1e-9, "nunca atraviesa el suelo")
				minimo = math.min(minimo, valor)
			end
			Marco.verdadero(minimo < 1 - T.AmplitudRebote * 0.3, "el rebote se nota")
			Marco.verdadero(minimo >= 1 - T.AmplitudRebote - 1e-9, "el rebote no es exagerado")
		end)

		Marco.prueba("las curvas no se salen nunca de un margen razonable", function()
			for _, tipo in { "Cierre", "Apertura" } do
				local duracion = Persiana.Duracion(tipo)
				for paso = 0, 200 do
					local valor = Persiana.Valor(tipo, duracion * paso / 200)
					Marco.verdadero(valor >= -0.1 and valor <= 1, `{tipo} en el paso {paso}: {valor}`)
				end
			end
		end)

		Marco.prueba("las duraciones suman sus fases y son ágiles (menos de 1,5 s)", function()
			Marco.igual(Persiana.Duracion("Cierre"), T.Anticipacion + T.Caida + T.Congelado + T.Rebote)
			Marco.igual(Persiana.Duracion("Apertura"), T.Desbloqueo + T.Subida + T.Asentado)
			Marco.verdadero(Persiana.Duracion("Cierre") < 1.5)
			Marco.verdadero(Persiana.Duracion("Apertura") < 1.5)
		end)

		Marco.prueba("los datos de la persiana son válidos", function()
			for nombre, color in DatosPersiana.Colores do
				Marco.verdadero(string.match(color, "^#%x%x%x%x%x%x$") ~= nil, `color {nombre}`)
			end
			for nombre, sonido in DatosPersiana.Sonidos do
				if type(sonido) == "table" then
					Marco.igual(type(sonido.Id), "string", nombre)
					Marco.verdadero(sonido.Volumen > 0 and sonido.Volumen <= 1, `volumen de {nombre}`)
					Marco.verdadero(sonido.Velocidad > 0, `velocidad de {nombre}`)
				end
			end
			local m = DatosPersiana.Medidas
			Marco.verdadero(m.Lamas >= 4 and m.Lamas <= 30, "número de lamas razonable (rendimiento en móvil)")
			Marco.verdadero(m.AltoBarra < m.AltoHueco)
		end)
	end)
end
