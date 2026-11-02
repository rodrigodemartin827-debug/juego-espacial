--[[
	Pruebas de la pantalla de elección de bando (lo que se puede comprobar sin Studio):

	  - Flujo: cuándo se muestra la pantalla, que solo se pide UNA vez, que manda el servidor y que se puede
	    reintentar si el servidor no responde.
	  - Encuadre: que los dos planetas quepan en cualquier pantalla y que la interfaz se adapte.
	  - Grieta: que la forma sea estable (misma semilla, misma grieta) y no se salga de su sitio.
	  - Datos: textos de cada bando con sus ventajas, escena coherente y recetas de VFX válidas para el motor.

	Lo que hace el servidor al elegir (validación, guardado, protección del personaje) está en Integracion.
]]

local Entorno = require("../infraestructura/Entorno")

local function cargar(ruta: string)
	local entorno = Entorno.nuevo()
	return entorno.servidor.requerir(`ReplicatedStorage.Shared.{ruta}`)
end

local TIPOS = {
	Particulas = true,
	Onda = true,
	Esfera = true,
	Luz = true,
	Proyectil = true,
	Corte = true,
	Haz = true,
	Escombros = true,
	Crater = true,
	Tinte = true,
	Desenfoque = true,
	Zoom = true,
	Sacudida = true,
	Hitstop = true,
	Sonido = true,
}
local FASES = { Anticipacion = true, Lanzamiento = true, Impacto = true, Residuo = true, Golpeado = true }
-- La pantalla de elección solo pone estas dos anclas (ver client/Eleccion/Escena).
local ANCLAS = { Origen = true, Objetivo = true }
local PARA = { Lanzador = true, Golpeados = true, Implicados = true, Todos = true }
local MINIMOS = { Bajo = true, Medio = true, Alto = true }
local DE_PANTALLA = { Tinte = true, Desenfoque = true, Zoom = true, Sacudida = true, Hitstop = true }

local function esHex(texto: any): boolean
	return type(texto) == "string" and string.match(texto, "^#%x%x%x%x%x%x$") ~= nil
end

local function paraCadaCapa(Recetas, f)
	for nombre, receta in Recetas do
		for fase, capas in receta.Fases do
			for indice, capa in capas do
				f(nombre, fase, indice, capa)
			end
		end
	end
end

local function tiposDe(capas)
	local tipos = {}
	for _, capa in capas do
		tipos[capa.Tipo] = true
	end
	return tipos
end

return function(Marco)
	local Flujo = cargar("Eleccion.Flujo")
	local Encuadre = cargar("Eleccion.Encuadre")
	local Grieta = cargar("Eleccion.Grieta")
	local Config = cargar("Eleccion.Config")
	local Textos = cargar("Eleccion.Datos.Textos")
	local Recetas = cargar("Eleccion.Datos.EfectosEleccion")
	local Bandos = cargar("Juego.Bandos")
	local Paleta = cargar("Combate.Datos.Paleta")
	local Recursos = cargar("Combate.Datos.Recursos")
	local Combate = cargar("Combate.Datos.EfectosVFX")
	local Naves = cargar("Naves.Datos.EfectosNave")

	local ESPERA = 8

	-- Un flujo que ya está mostrando la pantalla.
	local function flujoEnPantalla()
		local flujo = Flujo.nuevo(ESPERA)
		Marco.igual(Flujo.AlRecibirDatos(flujo, { Bando = "Ninguno" }), "Mostrar")
		return flujo
	end

	Marco.grupo("Elección de bando: cuándo se muestra", function()
		Marco.prueba("solo se muestra si los datos ya llegaron y el bando es Ninguno", function()
			Marco.verdadero(Flujo.DebeMostrar({ Bando = "Ninguno" }))
			Marco.falso(Flujo.DebeMostrar({ Bando = "Humanos" }))
			Marco.falso(Flujo.DebeMostrar({ Bando = "Monstruos" }))
			Marco.falso(Flujo.DebeMostrar(nil), "sin datos todavía no se sabe")
			Marco.falso(Flujo.DebeMostrar("Ninguno"), "basura")
		end)

		Marco.prueba("la primera vez (sin bando) se muestra la pantalla", function()
			local flujo = Flujo.nuevo(ESPERA)
			Marco.igual(flujo.Estado, "Esperando")
			Marco.falso(Flujo.PuedeElegir(flujo), "sin datos no se puede elegir")
			Marco.igual(Flujo.AlRecibirDatos(flujo, { Bando = "Ninguno" }), "Mostrar")
			Marco.igual(flujo.Estado, "Eligiendo")
			Marco.verdadero(Flujo.PuedeElegir(flujo))
		end)

		Marco.prueba("quien ya tiene bando no la ve nunca, aunque lleguen más datos", function()
			for _, bando in { "Humanos", "Monstruos" } do
				local flujo = Flujo.nuevo(ESPERA)
				Marco.igual(Flujo.AlRecibirDatos(flujo, { Bando = bando }), "Omitir")
				Marco.igual(flujo.Estado, "Terminado")
				Marco.igual(Flujo.AlRecibirDatos(flujo, { Bando = "Ninguno" }), "Nada", "una vez decidido, no vuelve")
				Marco.falso(Flujo.Elegir(flujo, "Humanos", 0))
				Marco.falso(flujo.Mostrada)
			end
		end)

		Marco.prueba("datos repetidos sin bando no vuelven a montar la pantalla", function()
			local flujo = flujoEnPantalla()
			Marco.igual(Flujo.AlRecibirDatos(flujo, { Bando = "Ninguno" }), "Nada")
			Marco.igual(Flujo.AlRecibirDatos(flujo, nil), "Nada")
			Marco.igual(Flujo.AlRecibirDatos(flujo, "basura"), "Nada")
			Marco.igual(flujo.Estado, "Eligiendo")
		end)
	end)

	Marco.grupo("Elección de bando: elegir una sola vez", function()
		Marco.prueba("un clic pide el bando una sola vez; los siguientes no envían nada", function()
			local flujo = flujoEnPantalla()
			Marco.verdadero(Flujo.Elegir(flujo, "Monstruos", 10), "el primer clic se envía")
			Marco.igual(flujo.Estado, "Enviado")
			Marco.igual(flujo.Pedido, "Monstruos")
			Marco.falso(Flujo.Elegir(flujo, "Monstruos", 10.1), "doble clic")
			Marco.falso(Flujo.Elegir(flujo, "Humanos", 10.2), "cambiar de idea mientras se espera")
			Marco.falso(Flujo.PuedeElegir(flujo))
		end)

		Marco.prueba("solo se pueden pedir los bandos elegibles", function()
			local flujo = flujoEnPantalla()
			for _, malo in { "Ninguno", "Piratas", "", 1, true, { Bando = "Humanos" } } do
				Marco.falso(Flujo.Elegir(flujo, malo, 0), `no debería pedir {tostring(malo)}`)
			end
			Marco.igual(flujo.Estado, "Eligiendo")
		end)

		Marco.prueba("resaltar solo funciona mientras se elige y con bandos elegibles", function()
			local flujo = Flujo.nuevo(ESPERA)
			Marco.falso(Flujo.Resaltar(flujo, "Humanos"), "aún no hay pantalla")
			Flujo.AlRecibirDatos(flujo, { Bando = "Ninguno" })
			Marco.verdadero(Flujo.Resaltar(flujo, "Humanos"))
			Marco.falso(Flujo.Resaltar(flujo, "Humanos"), "ya estaba resaltado: no hay cambio")
			Marco.falso(Flujo.Resaltar(flujo, "Ninguno"))
			Marco.verdadero(Flujo.Resaltar(flujo, nil), "salir de los dos lados")
			Marco.esNil(flujo.Resaltado)
			Flujo.Elegir(flujo, "Monstruos", 0)
			Marco.falso(Flujo.Resaltar(flujo, "Humanos"), "esperando al servidor el resaltado no se mueve")
			Marco.igual(flujo.Resaltado, "Monstruos")
		end)

		Marco.prueba("la confirmación del servidor cierra la elección con su bando", function()
			local flujo = flujoEnPantalla()
			Flujo.Elegir(flujo, "Humanos", 0)
			local accion, bando = Flujo.AlRecibirDatos(flujo, { Bando = "Humanos" })
			Marco.igual(accion, "Confirmar")
			Marco.igual(bando, "Humanos")
			Marco.igual(flujo.Estado, "Confirmado")
			Marco.igual(Flujo.AlRecibirDatos(flujo, { Bando = "Humanos" }), "Nada", "solo se celebra una vez")
			Marco.falso(Flujo.Elegir(flujo, "Monstruos", 1))
		end)

		Marco.prueba("manda el servidor: si confirma otro bando, se muestra el suyo", function()
			local flujo = flujoEnPantalla()
			Flujo.Elegir(flujo, "Humanos", 0)
			local accion, bando = Flujo.AlRecibirDatos(flujo, { Bando = "Monstruos" })
			Marco.igual(accion, "Confirmar")
			Marco.igual(bando, "Monstruos")
			Marco.igual(flujo.Resaltado, "Monstruos")
		end)

		Marco.prueba("si el bando llega sin haberlo pedido desde la pantalla, también se cierra", function()
			local flujo = flujoEnPantalla()
			local accion, bando = Flujo.AlRecibirDatos(flujo, { Bando = "Humanos" })
			Marco.igual(accion, "Confirmar")
			Marco.igual(bando, "Humanos")
		end)

		Marco.prueba("si el servidor no responde a tiempo, se puede volver a elegir", function()
			local flujo = flujoEnPantalla()
			Flujo.Elegir(flujo, "Humanos", 100)
			Marco.falso(Flujo.RevisarEspera(flujo, 100 + ESPERA - 0.1), "todavía hay que esperar")
			Marco.verdadero(Flujo.RevisarEspera(flujo, 100 + ESPERA), "pasado el tiempo, se reabre")
			Marco.igual(flujo.Estado, "Eligiendo")
			Marco.esNil(flujo.Pedido)
			Marco.verdadero(Flujo.Elegir(flujo, "Monstruos", 120), "se puede pedir de nuevo")
			Marco.falso(Flujo.RevisarEspera(flujo, 121))
		end)

		Marco.prueba("terminar la pantalla impide cualquier acción", function()
			local flujo = flujoEnPantalla()
			Flujo.Terminar(flujo)
			Marco.falso(Flujo.Elegir(flujo, "Humanos", 0))
			Marco.falso(Flujo.Resaltar(flujo, "Humanos"))
			Marco.igual(Flujo.AlRecibirDatos(flujo, { Bando = "Humanos" }), "Nada")
		end)

		Marco.prueba("teclado y mando se mueven entre los bandos sin salirse", function()
			local orden = Config.Orden
			Marco.igual(Flujo.Vecino(orden, nil, -1), orden[1])
			Marco.igual(Flujo.Vecino(orden, nil, 1), orden[#orden])
			Marco.igual(Flujo.Vecino(orden, orden[1], 1), orden[2])
			Marco.igual(Flujo.Vecino(orden, orden[1], -1), orden[1], "no se sale por la izquierda")
			Marco.igual(Flujo.Vecino(orden, orden[#orden], 1), orden[#orden], "ni por la derecha")
			Marco.igual(Flujo.BandoDelLado(orden, 1), "Humanos", "los humanos van a la izquierda")
			Marco.igual(Flujo.BandoDelLado(orden, 2), "Monstruos")
		end)
	end)

	Marco.grupo("Elección de bando: encuadre en PC y móvil", function()
		local cam = Config.Camara
		local function campo(aspecto)
			return Encuadre.CampoVertical(aspecto, cam.MitadAnchoVisible, cam.DistanciaReferencia, 1, 179)
		end

		Marco.prueba("el ancho de la escena cabe en cualquier proporción de pantalla", function()
			for _, aspecto in { 4 / 3, 16 / 10, 16 / 9, 19.5 / 9, 21 / 9 } do
				local grados = Encuadre.CampoVertical(
					aspecto,
					cam.MitadAnchoVisible,
					cam.DistanciaReferencia,
					cam.CampoMinimo,
					cam.CampoMaximo
				)
				-- Mitad del ancho visible a la distancia de referencia con ese campo vertical.
				local mitad = math.tan(math.rad(grados) / 2) * aspecto * cam.DistanciaReferencia
				Marco.verdadero(
					mitad >= cam.MitadAnchoVisible - 0.01 or grados >= cam.CampoMaximo,
					`aspecto {aspecto}: solo se ven {mitad} studs`
				)
			end
		end)

		Marco.prueba("las pantallas estrechas abren el campo y las anchas lo cierran, con límites", function()
			Marco.verdadero(campo(4 / 3) > campo(16 / 9))
			Marco.verdadero(campo(16 / 9) > campo(21 / 9))
			Marco.igual(Encuadre.CampoVertical(0.3, 58, 78, 38, 78), 78, "en vertical se limita al máximo")
			Marco.igual(Encuadre.CampoVertical(10, 58, 78, 38, 78), 38, "ultra panorámica: mínimo")
			local porDefecto = Encuadre.CampoVertical(0 / 0, 58, 78, 38, 78)
			Marco.verdadero(porDefecto >= 38 and porDefecto <= 78, "tamaño desconocido: valor razonable")
		end)

		Marco.prueba("los dos planetas caben enteros a lo ancho en el encuadre mínimo", function()
			for _, planeta in { Config.PlanetaHumanos, Config.PlanetaMonstruos } do
				local distancia = -planeta.Posicion[3]
				local borde = math.abs(planeta.Posicion[1]) + planeta.Radio
				local mitad = cam.MitadAnchoVisible * distancia / cam.DistanciaReferencia
				Marco.verdadero(borde <= mitad, `un planeta se sale: borde {borde} > {mitad}`)
			end
		end)

		Marco.prueba("la interfaz se adapta: compacta en móvil, normal en PC, apilada en vertical", function()
			local pc = Encuadre.Disposicion(1920, 1080)
			Marco.falso(pc.Compacta)
			Marco.falso(pc.Vertical)
			local movil = Encuadre.Disposicion(844, 390)
			Marco.verdadero(movil.Compacta)
			Marco.verdadero(movil.Escala >= 0.62, "el texto se tiene que poder leer")
			local vertical = Encuadre.Disposicion(390, 844)
			Marco.verdadero(vertical.Vertical)
			Marco.verdadero(vertical.AnchoPanel > movil.AnchoPanel, "en vertical los paneles ocupan todo el ancho")
			local enorme = Encuadre.Disposicion(7680, 4320)
			Marco.verdadero(enorme.Escala <= 1.6, "en una pantalla enorme no crece sin límite")
			local nada = Encuadre.Disposicion(0, 0)
			Marco.verdadero(nada.Escala > 0, "sin tamaño todavía no se rompe")
		end)
	end)

	Marco.grupo("Elección de bando: forma de la grieta", function()
		local g = Config.Grieta
		local function forma()
			return Grieta.nueva(g.Semilla, g.Puntos, g.Alto, g.Desvio, g.Temblor, g.VelocidadTemblor)
		end

		Marco.prueba("misma semilla, misma grieta; otra semilla, otra grieta", function()
			local a = Grieta.Puntos(forma(), 1.5)
			local b = Grieta.Puntos(forma(), 1.5)
			Marco.igualProfundo(a, b)
			local otra = Grieta.Puntos(Grieta.nueva(g.Semilla + 1, g.Puntos, g.Alto, g.Desvio, g.Temblor, 1), 1.5)
			local distintos = 0
			for indice = 1, #a do
				if math.abs(a[indice].X - otra[indice].X) > 1e-6 then
					distintos += 1
				end
			end
			Marco.verdadero(distintos > #a / 2)
		end)

		Marco.prueba("va de punta a punta, cerrada en las puntas y abierta en el medio", function()
			local puntos = Grieta.Puntos(forma(), 0)
			Marco.igual(#puntos, g.Puntos)
			Marco.verdadero(math.abs(puntos[1].Y + g.Alto / 2) < 1e-6, "punta de abajo")
			Marco.verdadero(math.abs(puntos[#puntos].Y - g.Alto / 2) < 1e-6, "punta de arriba")
			Marco.verdadero(math.abs(puntos[1].X) < 1e-6 and math.abs(puntos[#puntos].X) < 1e-6)
			local centro = puntos[math.ceil(#puntos / 2)]
			Marco.verdadero(centro.Grosor > puntos[1].Grosor, "más gruesa en el medio")
			for indice = 2, #puntos do
				Marco.verdadero(puntos[indice].Y > puntos[indice - 1].Y, "los vértices suben en orden")
			end
		end)

		Marco.prueba("es un zigzag de verdad y tiembla sin salirse de su sitio", function()
			local f = forma()
			local cambiosDeLado = 0
			local anterior = 0
			for _, x in f.Base do
				if anterior ~= 0 and (x > 0) ~= (anterior > 0) then
					cambiosDeLado += 1
				end
				anterior = x
			end
			Marco.verdadero(cambiosDeLado >= #f.Base / 2, `solo {cambiosDeLado} cambios de lado`)

			local maximo = Grieta.DesvioMaximo(f, 1.6)
			local cambia = false
			local inicial = Grieta.Puntos(f, 0)
			for t = 0, 20, 0.37 do
				local puntos = Grieta.Puntos(f, t, 1.6)
				for indice, punto in puntos do
					Marco.verdadero(math.abs(punto.X) <= maximo + 1e-6, "el zigzag se sale")
					if math.abs(punto.X - inicial[indice].X * 1.6) > 0.05 then
						cambia = true
					end
				end
			end
			Marco.verdadero(cambia, "la grieta debe moverse con el tiempo")
			Marco.verdadero(maximo * 2 < math.abs(Config.PlanetaHumanos.Posicion[1]), "no invade a los planetas")
		end)

		Marco.prueba("las ramas salen del centro hacia los dos lados y terminan finas", function()
			local ramas = Grieta.Ramas(g.Semilla, g.Ramas.Cantidad, g.Puntos, g.Ramas.Largo, g.Ramas.Puntos)
			Marco.igual(#ramas, g.Ramas.Cantidad)
			local izquierda, derecha = 0, 0
			local principal = Grieta.Puntos(forma(), 0)
			for _, rama in ramas do
				Marco.verdadero(rama.Desde >= 2 and rama.Desde <= g.Puntos - 1, "sale de un vértice interior")
				Marco.verdadero(rama.Largo >= g.Ramas.Largo[1] and rama.Largo <= g.Ramas.Largo[2])
				if math.cos(rama.Angulo) < 0 then
					izquierda += 1
				else
					derecha += 1
				end
				local puntos = Grieta.PuntosRama(rama, principal[rama.Desde], 0.5, 1)
				Marco.igual(#puntos, rama.Puntos + 1)
				Marco.verdadero(puntos[#puntos].Grosor < puntos[1].Grosor)
			end
			Marco.verdadero(izquierda > 0 and derecha > 0, "debe haber ramas a los dos lados")
		end)
	end)

	Marco.grupo("Elección de bando: datos", function()
		Marco.prueba("el orden de la pantalla son exactamente los bandos elegibles", function()
			Marco.igual(#Config.Orden, #Bandos.Elegibles)
			for _, bando in Bandos.Elegibles do
				Marco.verdadero(table.find(Config.Orden, bando) ~= nil, `falta {bando} en la pantalla`)
			end
		end)

		Marco.prueba("cada bando tiene nombre, lema, ventajas, debilidad y mensaje de bienvenida", function()
			for _, bando in Bandos.Elegibles do
				local t = Textos.Bandos[bando]
				Marco.distinto(t, nil, `faltan los textos de {bando}`)
				for _, campo in { "Nombre", "Lema", "Debilidad", "Confirmacion", "Dificultad" } do
					Marco.verdadero(type(t[campo]) == "string" and #t[campo] > 0, `{bando}: falta {campo}`)
				end
				Marco.verdadero(#t.Ventajas >= 3, `{bando}: pocas ventajas`)
				Marco.verdadero(esHex(t.Color) and esHex(t.ColorSuave), `{bando}: colores no válidos`)
			end
			Marco.distinto(Textos.Bandos.Humanos.Color, Textos.Bandos.Monstruos.Color, "cada lado su color")
			for _, campo in { "Titulo", "Subtitulo", "AyudaRaton", "AyudaTactil", "Esperando", "ErrorConfirmacion" } do
				Marco.verdadero(type(Textos[campo]) == "string" and #Textos[campo] > 0, `falta el texto {campo}`)
			end
		end)

		Marco.prueba("las ventajas dicen lo que dice el diseño del juego", function()
			local function todo(bando)
				return string.lower(
					table.concat(Textos.Bandos[bando].Ventajas, " ") .. " " .. Textos.Bandos[bando].Dificultad
				)
			end
			local humanos, monstruos = todo("Humanos"), todo("Monstruos")
			for _, palabra in { "tiendas", "materiales", "naves", "tecnolog", "fácil" } do
				Marco.contiene(humanos, palabra, "Humanos")
			end
			for _, palabra in { "fuerza", "agilidad", "vida" } do
				Marco.contiene(monstruos, palabra, "Monstruos")
			end
			Marco.contiene(string.lower(Textos.Bandos.Monstruos.Debilidad), "materiales")
		end)

		Marco.prueba("los colores de la escena son hexadecimales válidos", function()
			local malos = {}
			local function revisar(valor, ruta)
				if type(valor) == "table" then
					for clave, hijo in valor do
						revisar(hijo, `{ruta}.{tostring(clave)}`)
					end
				elseif type(valor) == "string" and string.sub(valor, 1, 1) == "#" and not esHex(valor) then
					table.insert(malos, `{ruta} = {valor}`)
				end
			end
			revisar(Config, "Config")
			Marco.igual(#malos, 0, table.concat(malos, "\n"))
		end)

		Marco.prueba("todo está delante de la cámara y las luces llegan a su planeta", function()
			for _, nombre in { "PlanetaHumanos", "PlanetaMonstruos", "Sol", "AgujeroNegro", "Grieta" } do
				Marco.verdadero(Config[nombre].Posicion[3] < 0, `{nombre} está detrás de la cámara`)
			end
			local function distancia(a, b)
				return math.sqrt((a[1] - b[1]) ^ 2 + (a[2] - b[2]) ^ 2 + (a[3] - b[3]) ^ 2)
			end
			local luzSol = Config.Sol.Luz
			local luzAgujero = Config.AgujeroNegro.Luz
			Marco.verdadero(luzSol.Rango <= 60 and luzAgujero.Rango <= 60, "Roblox no deja luces de más de 60 studs")
			Marco.verdadero(
				distancia(luzSol.Posicion, Config.PlanetaHumanos.Posicion) < luzSol.Rango,
				"la luz del sol no llega al planeta humano"
			)
			Marco.verdadero(
				distancia(luzAgujero.Posicion, Config.PlanetaMonstruos.Posicion) < luzAgujero.Rango,
				"la luz del agujero negro no llega al planeta de los monstruos"
			)
		end)

		Marco.prueba("las figuras son R6: solo las seis piezas de un personaje R6", function()
			local R6 = { Head = true, Torso = true, ["Left Arm"] = true, ["Right Arm"] = true }
			R6["Left Leg"] = true
			R6["Right Leg"] = true
			for _, nombre in { "FiguraHumanos", "FiguraMonstruos" } do
				local figura = Config[nombre]
				local piezas = 0
				for pieza in figura.Colores do
					Marco.verdadero(R6[pieza], `{nombre}: '{pieza}' no es una pieza R6`)
					piezas += 1
				end
				Marco.igual(piezas, 6, `{nombre}: faltan piezas`)
				for pieza in figura.Estiramiento or {} do
					Marco.verdadero(R6[pieza], `{nombre}: '{pieza}' no es una pieza R6`)
				end
			end
		end)

		Marco.prueba("los tiempos son razonables y la espera del servidor es generosa", function()
			local t = Config.Tiempos
			for clave, valor in t do
				Marco.verdadero(type(valor) == "number" and valor >= 0 and valor < 30, `tiempo {clave} absurdo`)
			end
			Marco.verdadero(t.EsperaConfirmacion >= 3, "con mala conexión la confirmación tarda")
			local salida = t.Celebracion + t.FundidoSalida + t.NegroMantenido + t.FundidoVuelta
			Marco.verdadero(salida <= 7, `la vuelta al juego tarda demasiado ({salida} s)`)
			Marco.verdadero(t.EsperaMaximaDatos > t.EsperaConfirmacion)
		end)
	end)

	Marco.grupo("Elección de bando: efectos", function()
		Marco.prueba("existen todas las recetas que pide la pantalla y no chocan con otras", function()
			for _, bando in Bandos.Elegibles do
				for _, prefijo in { "Eleccion_Anticipar_", "Eleccion_Confirmar_", "Eleccion_Grieta_Resaltar_" } do
					Marco.distinto(Recetas[prefijo .. bando], nil, `falta {prefijo}{bando}`)
				end
			end
			Marco.distinto(Recetas.Eleccion_Grieta_Chispazo, nil)
			for nombre in Recetas do
				Marco.esNil(Combate[nombre], `'{nombre}' existe también en el combate`)
				Marco.esNil(Naves[nombre], `'{nombre}' existe también en las naves`)
			end
		end)

		Marco.prueba("paletas, fases, tipos, anclas, destinatarios y mínimos conocidos", function()
			for nombre, receta in Recetas do
				Marco.distinto(Paleta[receta.Paleta], nil, `{nombre}: paleta '{receta.Paleta}' inexistente`)
				for fase, capas in receta.Fases do
					Marco.verdadero(FASES[fase], `{nombre}: fase desconocida '{fase}'`)
					Marco.verdadero(#capas > 0, `{nombre}/{fase}: fase vacía`)
				end
			end
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				local donde = `{nombre}/{fase}[{indice}]`
				Marco.verdadero(TIPOS[capa.Tipo], `{donde}: tipo desconocido '{capa.Tipo}'`)
				for _, campo in { "Anclaje", "Desde", "Hasta" } do
					if capa[campo] ~= nil then
						Marco.verdadero(ANCLAS[capa[campo]], `{donde}: ancla '{capa[campo]}' que la pantalla no pone`)
					end
				end
				if capa.Para ~= nil then
					Marco.verdadero(PARA[capa.Para], `{donde}: destinatario desconocido`)
				end
				if capa.Minimo ~= nil then
					Marco.verdadero(MINIMOS[capa.Minimo], `{donde}: mínimo desconocido`)
				end
				if capa.Retraso ~= nil then
					Marco.verdadero(capa.Retraso >= 0 and capa.Retraso < 3, `{donde}: retraso absurdo`)
				end
				-- Los efectos de pantalla solo deben verse en el cliente que elige.
				if DE_PANTALLA[capa.Tipo] then
					Marco.igual(capa.Para, "Lanzador", `{donde}: un efecto de pantalla debe ser solo para quien elige`)
				end
			end)
		end)

		Marco.prueba("colores, texturas y sonidos existen", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				local donde = `{nombre}/{fase}[{indice}]`
				local paleta = Paleta[Recetas[nombre].Paleta]
				for _, campo in { "Color", "ColorNucleo" } do
					local valor = capa[campo]
					local lista = if type(valor) == "table" then valor elseif valor ~= nil then { valor } else {}
					for _, color in lista do
						Marco.verdadero(paleta[color] ~= nil or esHex(color), `{donde}: color '{color}' desconocido`)
					end
				end
				if capa.Textura ~= nil then
					Marco.distinto(Recursos.Texturas[capa.Textura], nil, `{donde}: textura sin definir`)
				end
				if capa.Sonido ~= nil then
					Marco.distinto(Recursos.Sonidos[capa.Sonido], nil, `{donde}: sonido sin definir`)
				end
			end)
			Marco.distinto(Recursos.Sonidos.EleccionAmbiente, nil, "falta el sonido de ambiente de la grieta")
		end)

		Marco.prueba("nada que sature un móvil", function()
			paraCadaCapa(Recetas, function(nombre, fase, indice, capa)
				local donde = `{nombre}/{fase}[{indice}]`
				if capa.Tipo == "Particulas" then
					Marco.verdadero((capa.Cantidad or 0) <= 250, `{donde}: demasiadas partículas`)
					Marco.verdadero((capa.Tasa or 0) <= 200, `{donde}: demasiadas partículas por segundo`)
				elseif capa.Tipo == "Haz" then
					Marco.verdadero((capa.Segmentos or 8) <= 12 and (capa.Ramas or 0) <= 10, `{donde}: rayo cargado`)
				elseif capa.Tipo == "Luz" then
					local rango = if type(capa.Rango) == "table" then math.max(table.unpack(capa.Rango)) else capa.Rango
					Marco.verdadero((rango or 0) <= 60, `{donde}: Roblox no deja luces de más de 60 studs`)
				end
			end)
			Marco.verdadero(Config.Grieta.Motas.Tasa + Config.Grieta.Vacio.Tasa <= 120, "la grieta suelta demasiado")
		end)

		Marco.prueba(
			"la confirmación es espectacular: todas las capas, varias etapas, y cada bando distinto",
			function()
				local principales = {}
				for _, bando in Bandos.Elegibles do
					local receta = Recetas[`Eleccion_Confirmar_{bando}`]
					local impacto = receta.Fases.Impacto
					local tipos = tiposDe(impacto)
					for _, requerido in
						{
							"Esfera",
							"Onda",
							"Luz",
							"Particulas",
							"Haz",
							"Tinte",
							"Sacudida",
							"Zoom",
							"Desenfoque",
							"Sonido",
						}
					do
						Marco.verdadero(tipos[requerido], `Eleccion_Confirmar_{bando}: falta una capa {requerido}`)
					end
					local escalonadas = 0
					for _, capa in impacto do
						if (capa.Retraso or 0) > 0 then
							escalonadas += 1
						end
					end
					Marco.verdadero(escalonadas >= 4, `{bando}: el estallido debe tener etapas`)
					Marco.verdadero(#impacto >= 20, `{bando}: solo {#impacto} capas`)
					Marco.distinto(receta.Fases.Residuo, nil, `{bando}: debe quedar algo flotando hasta el fundido`)
					principales[Paleta[receta.Paleta].Principal] = true
				end
				local distintos = 0
				for _ in principales do
					distintos += 1
				end
				Marco.igual(distintos, 2, "los dos bandos deben verse distintos")
				Marco.verdadero(tiposDe(Recetas.Eleccion_Confirmar_Monstruos.Fases.Impacto).Particulas)
			end
		)

		Marco.prueba("la anticipación recoge energía (implosión) y avisa con un temblor leve", function()
			for _, bando in Bandos.Elegibles do
				local capas = Recetas[`Eleccion_Anticipar_{bando}`].Fases.Anticipacion
				local implosion, sacudida = false, nil
				for _, capa in capas do
					if capa.Tipo == "Esfera" and capa.Diametro[1] > capa.Diametro[2] then
						implosion = true
					elseif capa.Tipo == "Sacudida" then
						sacudida = capa
					end
				end
				Marco.verdadero(implosion, `{bando}: la anticipación debe encoger, no estallar`)
				Marco.distinto(sacudida, nil)
				Marco.verdadero(
					sacudida.Intensidad < 3,
					"la anticipación tiembla poco: el golpe fuerte es al confirmar"
				)
			end
		end)
	end)
end
