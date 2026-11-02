--[[
	Pruebas de la lógica pura de la exploración: catálogos (objetos, minerales, especies, recetas), inventario con
	límite según la mejora Carga, escáner (duración, recompensa, puntería) y crafteo.
]]

local Entorno = require("../infraestructura/Entorno")

local function cargar(ruta: string)
	return Entorno.nuevo().servidor.requerir(`ReplicatedStorage.Shared.{ruta}`)
end

return function(Marco)
	local Config = cargar("Exploracion.Config")
	local Objetos = cargar("Exploracion.Datos.Objetos")
	local Minerales = cargar("Exploracion.Datos.Minerales")
	local Especies = cargar("Exploracion.Datos.Especies")
	local Recetas = cargar("Exploracion.Datos.Recetas")
	local Inventario = cargar("Exploracion.Inventario")
	local Escaner = cargar("Exploracion.Escaner")
	local Crafteo = cargar("Exploracion.Crafteo")
	local Mejoras = cargar("Naves.Datos.Mejoras")
	local Estadisticas = cargar("Naves.Estadisticas")
	local Esquema = Entorno.nuevo().servidor.requerir("ServerScriptService.Server.Servicios.ServicioDatos.Esquema")

	-- Datos de un jugador con lo indicado (el resto, de un jugador nuevo).
	local function jugador(inventario, monedas, mejoras)
		local datos = Esquema.Nuevo()
		datos.Inventario = inventario or {}
		datos.Monedas = monedas or 0
		for id, nivel in mejoras or {} do
			datos.MejorasNave[id] = nivel
		end
		return datos
	end

	Marco.grupo("Exploración: catálogos", function()
		Marco.prueba("todos los objetos están en el orden de la interfaz y tienen datos completos", function()
			local enOrden = {}
			for _, id in Objetos.Orden do
				enOrden[id] = true
				Marco.distinto(Objetos.Lista[id], nil, `Orden nombra '{id}', que no existe`)
			end
			for id, objeto in Objetos.Lista do
				Marco.verdadero(enOrden[id], `'{id}' no está en Objetos.Orden`)
				Marco.verdadero(objeto.Categoria == "Mineral" or objeto.Categoria == "Componente", id)
				Marco.verdadero(string.match(objeto.Color, "^#%x%x%x%x%x%x$") ~= nil, `{id}: color no válido`)
				Marco.verdadero(Objetos.Volumen(id) >= 1, `{id}: el volumen debe ser al menos 1`)
			end
			Marco.igual(Objetos.Volumen("NoExiste"), 1)
		end)

		Marco.prueba("cada mineral suelta un objeto de categoría Mineral y tiene valores razonables", function()
			for _, id in Minerales.Orden do
				local mineral = Minerales.Lista[id]
				Marco.distinto(mineral, nil, id)
				local objeto = Objetos.Lista[mineral.Objeto]
				Marco.distinto(objeto, nil, `{id}: suelta '{mineral.Objeto}', que no existe`)
				Marco.igual(objeto.Categoria, "Mineral")
				Marco.verdadero(mineral.Vida > 0, `{id}: sin vida`)
				Marco.verdadero(
					mineral.Cantidad[1] >= 1 and mineral.Cantidad[2] >= mineral.Cantidad[1],
					`{id}: cantidad`
				)
				Marco.verdadero(#mineral.Origen > 0, `{id}: sin origen`)
				for _, origen in mineral.Origen do
					Marco.verdadero(origen == "Planeta" or origen == "Asteroide", `{id}: origen '{origen}'`)
				end
			end
			-- Todo mineral del inventario se puede conseguir picando.
			for id, objeto in Objetos.Lista do
				if objeto.Categoria == "Mineral" then
					local hayNodo = false
					for _, nodo in Minerales.Lista do
						hayNodo = hayNodo or nodo.Objeto == id
					end
					Marco.verdadero(hayNodo, `el mineral '{id}' no se puede picar en ningún nodo`)
				end
			end
			Marco.verdadero(#Minerales.De("Planeta") >= 3, "debe haber varios minerales en los planetas")
			Marco.verdadero(#Minerales.De("Asteroide") >= 3, "debe haber varios minerales en los asteroides")
		end)

		Marco.prueba("el reparto de minerales por azar respeta el origen y los pesos", function()
			-- Titanio solo sale en asteroides; nunca en planetas.
			for paso = 0, 99 do
				Marco.distinto(Minerales.Elegir("Planeta", paso / 100), "Titanio", "el titanio no sale en los planetas")
			end
			local cuentas = {}
			for paso = 0, 999 do
				local tipo = Minerales.Elegir("Asteroide", paso / 1000)
				Marco.distinto(tipo, nil)
				cuentas[tipo] = (cuentas[tipo] or 0) + 1
			end
			Marco.verdadero(
				cuentas.Hierro > cuentas.Cristal,
				"el hierro (peso 5) es más común que el cristal (peso 2)"
			)
			Marco.verdadero(cuentas.Titanio > 0, "el titanio sale en los asteroides")
			Marco.esNil(Minerales.Elegir("Luna", 0.5), "un origen sin minerales no devuelve nada")
			Marco.distinto(Minerales.Elegir("Planeta", 5), nil, "un azar fuera de rango se acota")
			Marco.distinto(Minerales.Elegir("Planeta", -5), nil)
		end)

		Marco.prueba("las especies tienen ficha completa y hay una por cada mineral", function()
			local categorias = { Criatura = 0, Planta = 0, Mineral = 0 }
			for id, especie in Especies.Lista do
				categorias[especie.Categoria] = (categorias[especie.Categoria] or 0) + 1
				Marco.distinto(Especies.ColoresRareza[especie.Rareza], nil, `{id}: rareza '{especie.Rareza}'`)
				Marco.verdadero(especie.Duracion > 0 and especie.XP > 0 and especie.Monedas > 0, id)
				Marco.verdadero(#especie.Datos > 0, `{id}: sin filas en la ficha`)
				for _, fila in especie.Datos do
					Marco.verdadero(type(fila[1]) == "string" and type(fila[2]) == "string", `{id}: fila mal formada`)
				end
			end
			Marco.verdadero(categorias.Criatura >= 1 and categorias.Planta >= 1, "faltan criaturas o plantas")
			Marco.igual(categorias.Mineral, #Minerales.Orden)
			for _, id in Minerales.Orden do
				Marco.distinto(Especies.Lista[Especies.IdDeMineral(id)], nil, id)
			end
			Marco.verdadero(#Especies.Ids() == categorias.Criatura + categorias.Planta + categorias.Mineral)
		end)

		Marco.prueba("la plantilla de datos guarda los descubrimientos y se repara si está mal", function()
			Marco.igualProfundo(Esquema.Nuevo().Descubrimientos, {})
			local datos = Esquema.Conciliar({ Descubrimientos = { Bien = 2, Mal = -1, [5] = 3 } })
			Marco.igual(datos.Descubrimientos.Bien, 2)
			Marco.esNil(datos.Descubrimientos.Mal)
			Marco.esNil(datos.Descubrimientos[5])
		end)
	end)

	Marco.grupo("Exploración: la mejora Escáner", function()
		Marco.prueba("sube el alcance y la velocidad del escáner de mano nivel a nivel", function()
			local base = Estadisticas.Calcular({})
			local alto = Estadisticas.Calcular({ Escaner = 10 })
			Marco.igual(base.VelocidadEscaner, 1)
			Marco.verdadero(base.AlcanceEscaner > 20, "el alcance base debe servir para algo")
			Marco.verdadero(alto.AlcanceEscaner > base.AlcanceEscaner * 2)
			Marco.verdadero(alto.VelocidadEscaner >= 2)
			Marco.verdadero(alto.RadioEscaner > base.RadioEscaner, "el radar de la nave sigue mejorando")
			for nivel = 1, Mejoras.NivelMaximo do
				Marco.verdadero(
					Estadisticas.Calcular({ Escaner = nivel }).AlcanceEscaner
						> Estadisticas.Calcular({ Escaner = nivel - 1 }).AlcanceEscaner,
					`nivel {nivel}: el alcance debe crecer`
				)
			end
		end)

		Marco.prueba("la mejora Carga fija el límite del inventario", function()
			Marco.verdadero(Estadisticas.Calcular({ Carga = 5 }).Capacidad > Estadisticas.Calcular({}).Capacidad)
		end)
	end)

	Marco.grupo("Exploración: inventario con límite", function()
		Marco.prueba("el volumen suma cantidad × volumen de cada objeto", function()
			local inv = { Hierro = 4, LingoteHierro = 3, NoExiste = 2 }
			Marco.igual(Inventario.Volumen(inv), 4 + 3 * 2 + 2)
			Marco.igual(Inventario.EspacioLibre(inv, 20), 20 - 12)
			Marco.igual(Inventario.EspacioLibre(inv, 5), 0, "nunca negativo")
		end)

		Marco.prueba("añade solo lo que cabe y devuelve lo añadido", function()
			local inv = { Hierro = 8 }
			Marco.igual(Inventario.Anadir(inv, 10, "Cobre", 5), 2)
			Marco.igual(inv.Cobre, 2)
			Marco.igual(Inventario.Anadir(inv, 10, "Cobre", 1), 0, "bodega llena")
			Marco.igual(inv.Cobre, 2)
			Marco.igual(Inventario.Anadir(inv, 100, "NoExiste", 1), 0, "un objeto desconocido no se añade")
		end)

		Marco.prueba("los objetos grandes ocupan más: caben menos unidades", function()
			local inv = {}
			Marco.igual(Inventario.CuantoCabe(inv, 10, "Hierro"), 10)
			Marco.igual(Inventario.CuantoCabe(inv, 10, "NucleoEnergia"), 3)
			Marco.igual(Inventario.Anadir(inv, 10, "NucleoEnergia", 5), 3)
		end)

		Marco.prueba("rechaza cantidades inválidas", function()
			local inv = { Hierro = 1 }
			for _, mala in { 0, -3, 1.5, 0 / 0, math.huge } do
				Marco.igual(Inventario.Anadir(inv, 50, "Hierro", mala), 0, `añadir {mala}`)
				Marco.falso(Inventario.Quitar(inv, "Hierro", mala), `quitar {mala}`)
			end
			Marco.igual(inv.Hierro, 1)
		end)

		Marco.prueba("quitar exige tener suficiente y borra la entrada al llegar a 0", function()
			local inv = { Hierro = 3 }
			Marco.falso(Inventario.Quitar(inv, "Hierro", 4))
			Marco.igual(inv.Hierro, 3)
			Marco.verdadero(Inventario.Quitar(inv, "Hierro", 1))
			Marco.igual(inv.Hierro, 2)
			Marco.verdadero(Inventario.Quitar(inv, "Hierro", 2))
			Marco.esNil(inv.Hierro, "sin entradas con 0")
			Marco.falso(Inventario.Tiene(inv, "Hierro", 1))
		end)

		Marco.prueba("la capacidad crece con la mejora Carga", function()
			local nuevo = Estadisticas.Calcular({}).Capacidad
			local mejorado = Estadisticas.Calcular({ Carga = 3 }).Capacidad
			local inv = {}
			Marco.igual(Inventario.Anadir(inv, nuevo, "Hierro", 1000), nuevo)
			Marco.igual(Inventario.Anadir(inv, mejorado, "Hierro", 1000), mejorado - nuevo)
		end)
	end)

	Marco.grupo("Exploración: reglas del escáner", function()
		Marco.prueba("la velocidad del escáner acorta el análisis, con un mínimo", function()
			Marco.igual(Escaner.Duracion(2, 1), 2)
			Marco.igual(Escaner.Duracion(2, 2), 1)
			Marco.igual(Escaner.Duracion(2, 100), Config.DuracionMinimaEscaneo)
			Marco.igual(Escaner.Duracion(2, 0), 2, "una velocidad inválida cuenta como normal")
			local lento = Escaner.Duracion(2, Estadisticas.Calcular({}).VelocidadEscaner)
			local rapido = Escaner.Duracion(2, Estadisticas.Calcular({ Escaner = 10 }).VelocidadEscaner)
			Marco.verdadero(rapido < lento)
		end)

		Marco.prueba("el primer escaneo paga todo y los siguientes una fracción cada vez menor", function()
			local primera = Escaner.Recompensa(100, 40, 0)
			Marco.verdadero(primera.Nuevo)
			Marco.igual(primera.XP, 100)
			Marco.igual(primera.Monedas, 40)
			local segunda = Escaner.Recompensa(100, 40, 1)
			Marco.falso(segunda.Nuevo)
			Marco.verdadero(segunda.XP < 100 and segunda.XP > 0)
			Marco.verdadero(Escaner.Recompensa(100, 40, 50).XP > 0 or Escaner.FraccionRecompensa(50) > 0)
			Marco.verdadero(Escaner.FraccionRecompensa(2) <= Escaner.FraccionRecompensa(1))
			Marco.igual(Escaner.FraccionRecompensa(500), Escaner.FraccionRecompensa(#Config.RecompensaRepeticion + 1))
		end)

		Marco.prueba("el alcance admite una holgura solo si se pide, y rechaza NaN", function()
			Marco.verdadero(Escaner.EnAlcance(40, 40))
			Marco.falso(Escaner.EnAlcance(41, 40))
			Marco.verdadero(Escaner.EnAlcance(41, 40, true))
			Marco.falso(Escaner.EnAlcance(0 / 0, 40, true))
			Marco.falso(Escaner.EnAlcance(60, 40, true))
		end)

		Marco.prueba("elige el objetivo más cercano a la mira, dentro del cono y del alcance", function()
			local origen = { X = 0, Y = 0, Z = 0 }
			local mira = { X = 0, Y = 0, Z = -1 }
			local candidatos = {
				{ Posicion = { X = 10, Y = 0, Z = -10 } }, -- 45° a un lado
				{ Posicion = { X = 1, Y = 0, Z = -20 } }, -- casi recto
				{ Posicion = { X = 0, Y = 0, Z = -500 } }, -- recto pero lejísimos
				{ Posicion = { X = 0, Y = 0, Z = 20 } }, -- detrás
			}
			Marco.igual(Escaner.MejorObjetivo(origen, mira, candidatos, 60, 12), 2)
			Marco.esNil(Escaner.MejorObjetivo(origen, mira, candidatos, 60, 1), "fuera del cono")
			Marco.esNil(Escaner.MejorObjetivo(origen, mira, {}, 60, 12))
			Marco.esNil(Escaner.MejorObjetivo(origen, { X = 0, Y = 0, Z = 0 }, candidatos, 60, 12), "mira nula")
			Marco.igual(Escaner.MejorObjetivo(origen, mira, candidatos, 1000, 12), 3, "al ampliar el alcance sí entra")
		end)
	end)

	Marco.grupo("Exploración: recetas (datos)", function()
		Marco.prueba("todas las recetas usan objetos, mejoras y categorías que existen", function()
			local enOrden = {}
			for _, id in Recetas.Orden do
				enOrden[id] = true
				Marco.distinto(Recetas.Lista[id], nil, `Orden nombra '{id}', que no existe`)
			end
			for id, receta in Recetas.Lista do
				Marco.verdadero(enOrden[id], `'{id}' no está en Recetas.Orden`)
				Marco.verdadero(receta.Categoria == "Mejora" or receta.Categoria == "Objeto", id)
				Marco.verdadero(next(receta.Ingredientes) ~= nil, `{id}: sin ingredientes`)
				for ingrediente in receta.Ingredientes do
					Marco.distinto(Objetos.Lista[ingrediente], nil, `{id}: ingrediente '{ingrediente}' inexistente`)
				end
				if receta.Categoria == "Mejora" then
					Marco.distinto(Mejoras.Lista[receta.Resultado.Mejora], nil, `{id}: mejora inexistente`)
					Marco.esNil(receta.Resultado.Objeto, `{id}: una mejora no da objetos`)
				else
					Marco.distinto(Objetos.Lista[receta.Resultado.Objeto], nil, `{id}: resultado inexistente`)
					Marco.verdadero((receta.Resultado.Cantidad or 1) >= 1, id)
				end
			end
		end)

		Marco.prueba("hay una receta para subir cada mejora de la nave, una por mejora", function()
			local cubiertas = {}
			for _, receta in Recetas.Lista do
				if receta.Resultado.Mejora then
					Marco.esNil(cubiertas[receta.Resultado.Mejora], `dos recetas suben '{receta.Resultado.Mejora}'`)
					cubiertas[receta.Resultado.Mejora] = true
				end
			end
			for id in Mejoras.Lista do
				Marco.verdadero(cubiertas[id], `no hay receta para mejorar '{id}'`)
			end
		end)

		Marco.prueba("todo ingrediente se puede conseguir: es un mineral o lo fabrica otra receta", function()
			local fabricables = {}
			for _, receta in Recetas.Lista do
				if receta.Resultado.Objeto then
					fabricables[receta.Resultado.Objeto] = true
				end
			end
			for id, receta in Recetas.Lista do
				for ingrediente in receta.Ingredientes do
					Marco.verdadero(
						Objetos.Lista[ingrediente].Categoria == "Mineral" or fabricables[ingrediente],
						`{id}: nadie fabrica '{ingrediente}'`
					)
				end
			end
		end)

		Marco.prueba("ninguna receta necesita más de lo que cabe en una bodega mejorada al máximo", function()
			local maxima = Estadisticas.Calcular({ Carga = Mejoras.NivelMaximo }).Capacidad
			for id, receta in Recetas.Lista do
				local nivel = if receta.Categoria == "Mejora" then Mejoras.NivelMaximo - 1 else 0
				local volumen = 0
				for ingrediente, cantidad in receta.Ingredientes do
					volumen += Crafteo.Cantidad(cantidad, nivel) * Objetos.Volumen(ingrediente)
				end
				Marco.verdadero(
					volumen <= maxima,
					`{id}: necesita {volumen} de espacio y la bodega máxima tiene {maxima}`
				)
			end
		end)
	end)

	Marco.grupo("Exploración: crafteo (reglas)", function()
		Marco.prueba("las cantidades escaladas crecen con el nivel y se redondean hacia arriba", function()
			Marco.igual(Crafteo.Cantidad(3, 7), 3)
			Marco.igual(Crafteo.Cantidad({ Base = 2, PorNivel = 1 }, 0), 2)
			Marco.igual(Crafteo.Cantidad({ Base = 2, PorNivel = 1 }, 4), 6)
			Marco.igual(Crafteo.Cantidad({ Base = 1, PorNivel = 0.5 }, 1), 2)
		end)

		Marco.prueba("un objeto se fabrica: gasta ingredientes y entrega el resultado", function()
			local datos = jugador({ Hierro = 7 })
			local plan = Crafteo.Planificar(datos, "LingoteHierro", 50)
			Marco.verdadero(plan.Ok)
			Marco.igual(plan.Quita.Hierro, 3)
			Marco.igual(plan.Anade.LingoteHierro, 1)
			Marco.igual(datos.Inventario.Hierro, 7, "planificar no modifica nada")
			Marco.verdadero(Crafteo.Aplicar(datos, plan, 50))
			Marco.igual(datos.Inventario.Hierro, 4)
			Marco.igual(datos.Inventario.LingoteHierro, 1)
		end)

		Marco.prueba("se pueden fabricar varias unidades de golpe", function()
			local datos = jugador({ Hierro = 9 })
			local plan = Crafteo.Planificar(datos, "LingoteHierro", 50, 3)
			Marco.verdadero(plan.Ok)
			Marco.verdadero(Crafteo.Aplicar(datos, plan, 50))
			Marco.esNil(datos.Inventario.Hierro)
			Marco.igual(datos.Inventario.LingoteHierro, 3)
			Marco.igual(Crafteo.Planificar(jugador({ Hierro = 8 }), "LingoteHierro", 50, 3).Motivo, "FaltanMateriales")
		end)

		Marco.prueba("sin materiales no se fabrica y el plan dice qué falta", function()
			local datos = jugador({ Cristal = 1 })
			local plan = Crafteo.Planificar(datos, "LenteCristal", 50)
			Marco.falso(plan.Ok)
			Marco.igual(plan.Motivo, "FaltanMateriales")
			Marco.igual(#plan.Requisitos, 2)
			local porId = {}
			for _, requisito in plan.Requisitos do
				porId[requisito.Id] = requisito
			end
			Marco.igual(porId.Cristal.Necesita, 2)
			Marco.igual(porId.Cristal.Tiene, 1)
			Marco.igual(porId.Cobre.Tiene, 0)
			Marco.falso(Crafteo.Aplicar(datos, plan, 50), "un plan fallido no se aplica")
			Marco.igual(datos.Inventario.Cristal, 1)
		end)

		Marco.prueba("las monedas también se exigen y se cobran", function()
			local inventario = { Cristal = 3, CableCobre = 2, PlacaTitanio = 1 }
			local sinDinero = jugador(table.clone(inventario), 49)
			Marco.igual(Crafteo.Planificar(sinDinero, "NucleoEnergia", 50).Motivo, "FaltanMonedas")
			local conDinero = jugador(table.clone(inventario), 80)
			local plan = Crafteo.Planificar(conDinero, "NucleoEnergia", 50)
			Marco.verdadero(plan.Ok)
			Marco.verdadero(Crafteo.Aplicar(conDinero, plan, 50))
			Marco.igual(conDinero.Monedas, 30)
			Marco.igual(conDinero.Inventario.NucleoEnergia, 1)
		end)

		Marco.prueba("una mejora sube un nivel y cuesta más cuanto más alta está", function()
			local primero = Crafteo.Planificar(jugador({}, 0), "MejoraCasco", 50)
			local ids = {}
			for _, requisito in primero.Requisitos do
				ids[requisito.Id] = requisito.Necesita
			end
			Marco.igual(ids.PlacaTitanio, 1)
			Marco.igual(ids.Monedas, 40)

			local datos = jugador({ PlacaTitanio = 10, LingoteHierro = 10 }, 500, { Casco = 3 })
			local plan = Crafteo.Planificar(datos, "MejoraCasco", 100)
			Marco.verdadero(plan.Ok)
			Marco.igual(plan.Quita.PlacaTitanio, 4)
			Marco.igual(plan.Quita.LingoteHierro, 5)
			Marco.igual(plan.Monedas, 100)
			Marco.igual(plan.NivelNuevo, 4)
			Marco.verdadero(Crafteo.Aplicar(datos, plan, 100))
			Marco.igual(datos.MejorasNave.Casco, 4)
			Marco.igual(datos.Monedas, 400)
			Marco.igual(datos.Inventario.PlacaTitanio, 6)
		end)

		Marco.prueba("una mejora al nivel máximo no se fabrica", function()
			local datos = jugador({ PlacaTitanio = 99, LingoteHierro = 99 }, 9999, { Casco = Mejoras.NivelMaximo })
			Marco.igual(Crafteo.Planificar(datos, "MejoraCasco", 999).Motivo, "NivelMaximo")
		end)

		Marco.prueba("las mejoras solo se fabrican de una en una", function()
			local datos = jugador({ PlacaTitanio = 99, LingoteHierro = 99 }, 9999)
			Marco.igual(Crafteo.Planificar(datos, "MejoraCasco", 999, 2).Motivo, "CantidadInvalida")
		end)

		Marco.prueba("rechaza recetas desconocidas y cantidades absurdas", function()
			local datos = jugador({ Hierro = 99 })
			Marco.igual(Crafteo.Planificar(datos, "NoExiste", 50).Motivo, "RecetaDesconocida")
			for _, mala in { 0, -1, 1.5, 0 / 0, math.huge, Config.CantidadMaximaPorPeticion + 1 } do
				Marco.igual(Crafteo.Planificar(datos, "LingoteHierro", 50, mala).Motivo, "CantidadInvalida", `{mala}`)
			end
		end)

		Marco.prueba("el resultado debe caber en la bodega una vez gastados los ingredientes", function()
			-- Con las recetas de ahora el resultado siempre ocupa menos que los ingredientes, así que se prueba con una
			-- receta de mentira que engorda el inventario (en un entorno propio, para no tocar las demás pruebas).
			local entorno = Entorno.nuevo()
			local RecetasLocal = entorno.servidor.requerir("ReplicatedStorage.Shared.Exploracion.Datos.Recetas")
			local CrafteoLocal = entorno.servidor.requerir("ReplicatedStorage.Shared.Exploracion.Crafteo")
			RecetasLocal.Lista.Engorde = {
				Nombre = "Engorde",
				Descripcion = "",
				Categoria = "Objeto",
				Ingredientes = { Hierro = 1 },
				Resultado = { Objeto = "NucleoEnergia", Cantidad = 1 }, -- 1 de espacio → 3 de espacio
			}
			-- Libre: 10 - 9 = 1; gasta 1 (queda 2 libres) y el núcleo ocupa 3: no cabe.
			local llena = jugador({ Hierro = 9 })
			local plan = CrafteoLocal.Planificar(llena, "Engorde", 10)
			Marco.falso(plan.Ok)
			Marco.igual(plan.Motivo, "BodegaLlena")
			Marco.falso(CrafteoLocal.Aplicar(llena, plan, 10))
			Marco.igual(llena.Inventario.Hierro, 9, "no se cobra nada")
			-- Con un hueco más sí cabe (gasta 1 y quedan 3 libres).
			Marco.verdadero(CrafteoLocal.Planificar(jugador({ Hierro = 8 }), "Engorde", 10).Ok)

			-- Las recetas reales sí caben aunque la bodega esté justa: 3 de hierro (3) → 1 lingote (2).
			Marco.verdadero(Crafteo.Planificar(jugador({ Hierro = 3 }), "LingoteHierro", 3).Ok)
		end)

		Marco.prueba("aplicar no cobra nada si los datos cambiaron desde que se planificó", function()
			local datos = jugador({ Hierro = 3 })
			local plan = Crafteo.Planificar(datos, "LingoteHierro", 50)
			datos.Inventario.Hierro = 1 -- alguien gastó el hierro entre medias
			Marco.falso(Crafteo.Aplicar(datos, plan, 50))
			Marco.igual(datos.Inventario.Hierro, 1)
			Marco.esNil(datos.Inventario.LingoteHierro)
		end)

		Marco.prueba("se puede ir desde cero hasta la mejora máxima fabricando todo lo necesario", function()
			-- Con materiales de sobra, subir una mejora diez veces seguidas funciona y para en el nivel máximo.
			local datos = jugador({}, 100000)
			datos.Inventario = { PlacaTitanio = 200, LingoteHierro = 200 }
			for nivel = 1, Mejoras.NivelMaximo do
				local plan = Crafteo.Planificar(datos, "MejoraCasco", 100000)
				Marco.verdadero(plan.Ok, `nivel {nivel}`)
				Marco.verdadero(Crafteo.Aplicar(datos, plan, 100000))
				Marco.igual(datos.MejorasNave.Casco, nivel)
			end
			Marco.igual(Crafteo.Planificar(datos, "MejoraCasco", 100000).Motivo, "NivelMaximo")
		end)
	end)
end
