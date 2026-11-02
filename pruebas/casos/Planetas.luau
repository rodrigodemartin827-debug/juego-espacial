--[[
	Pruebas de la lógica pura de los planetas: datos del sistema solar, zonas, cielo de las superficies,
	atracción del agujero negro, calor del sol, iluminación por zonas, ruido, generador de terreno y aspecto de
	los planetas.
]]

local Entorno = require("../infraestructura/Entorno")

local function cargar(ruta: string)
	local entorno = Entorno.nuevo()
	return entorno.servidor.requerir(`ReplicatedStorage.Shared.{ruta}`)
end

local function casi(Marco, real: number, esperado: number, detalle: string?, tolerancia: number?)
	Marco.verdadero(
		math.abs(real - esperado) <= (tolerancia or 1e-6),
		`{detalle or "valor"}: se esperaba {esperado} y se obtuvo {real}`
	)
end

-- Modelo de mentira del cielo de Roblox para probar el buscador de hora y latitud: el sol recorre un círculo
-- máximo (con la hora) inclinado por la latitud, y la luna está justo enfrente. No es la fórmula de Roblox (el
-- buscador no la necesita), pero tiene la misma forma: dos ángulos que mueven una dirección por toda la esfera.
local function cieloDePrueba(hora: number, latitud: number)
	local angulo = (hora / 24) * math.pi * 2 - math.pi / 2
	local x, y = math.cos(angulo), math.sin(angulo)
	local inclinacion = math.rad(latitud)
	local sol = { X = x, Y = y * math.cos(inclinacion), Z = y * math.sin(inclinacion) }
	local luna = { X = -sol.X, Y = -sol.Y, Z = -sol.Z }
	return sol, luna
end

-- Nombres de Enum.Material de terreno que existen en Roblox (los que puede usar el generador).
local MATERIALES_TERRENO = {
	Air = true,
	Asphalt = true,
	Basalt = true,
	Brick = true,
	Cobblestone = true,
	Concrete = true,
	CrackedLava = true,
	Glacier = true,
	Grass = true,
	Ground = true,
	Ice = true,
	LeafyGrass = true,
	Limestone = true,
	Mud = true,
	Pavement = true,
	Rock = true,
	Salt = true,
	Sand = true,
	Sandstone = true,
	Slate = true,
	Snow = true,
	Water = true,
	WoodPlanks = true,
}

return function(Marco)
	local Datos = cargar("Planetas.Datos")
	local Iluminacion = cargar("Planetas.Datos.Iluminacion")
	local Espacio = cargar("Planetas.Espacio")
	local Gravedad = cargar("Planetas.Gravedad")
	local Calor = cargar("Planetas.Calor")
	local Luz = cargar("Planetas.Luz")
	local Ruido = cargar("Planetas.Ruido")
	local GeneradorTerreno = cargar("Planetas.GeneradorTerreno")
	local Apariencia = cargar("Planetas.Apariencia")
	local V = cargar("Planetas.Vectores")
	local Estadisticas = cargar("Naves.Estadisticas")
	local NavesConfig = cargar("Naves.Config")
	local NavesReglas = cargar("Naves.Reglas")
	local CombateReglas = cargar("Combate.Reglas")

	local base = Estadisticas.Calcular({})
	local tope = Estadisticas.Calcular({ Motor = 10 })

	-- ===== Datos y mapa =====

	Marco.grupo("Planetas: datos y mapa", function()
		Marco.prueba("hay un planeta Humanos y otro Monstruos, cada uno con superficie, puerto y aspecto", function()
			for _, id in { "Humanos", "Monstruos" } do
				local planeta = Datos.Planetas[id]
				Marco.distinto(planeta, nil, id)
				Marco.igual(planeta.Id, id)
				Marco.verdadero(#planeta.Apariencia > 0, `{id}: sin aspecto`)
				Marco.distinto(Iluminacion.Presets[planeta.Superficie.Iluminacion], nil, `{id}: preset de luz`)
				Marco.verdadero(planeta.Radio > 1000, `{id}: debe verse enorme desde el espacio`)
			end
			Marco.igualProfundo(Datos.OrdenPlanetas, { "Humanos", "Monstruos" })
		end)

		Marco.prueba("el viaje entre planetas dura unos 10 minutos a la velocidad de crucero de la nave", function()
			local minutos = Espacio.TiempoViaje(base.VelocidadMax) / 60
			Marco.verdadero(minutos >= 9 and minutos <= 11, `con la nave sin mejorar dura {minutos} min`)
			-- Con el motor al máximo es bastante más corto (las mejoras se notan), pero sigue siendo un viaje.
			local rapido = Espacio.TiempoViaje(tope.VelocidadMax) / 60
			Marco.verdadero(rapido < minutos and rapido > 3, `con el motor al máximo dura {rapido} min`)
		end)

		Marco.prueba(
			"todo lo jugable cabe en el radio seguro (precisión de coma flotante y límites del terreno)",
			function()
				local radio = Datos.Espacio.Radio
				Marco.igual(radio, NavesConfig.RadioMundo, "el espacio de Planetas y la vigilancia de Naves coinciden")
				Marco.verdadero(radio <= 50000, "más allá de 50 000 studs la precisión empieza a notarse")
				for _, id in Datos.OrdenPlanetas do
					local planeta = Datos.Planetas[id]
					Marco.verdadero(
						V.largo(planeta.Centro) + planeta.Radio + planeta.Atmosfera < radio,
						`{id} se sale del espacio`
					)
					-- La superficie (y el techo) también caben, y dentro de lo que Terrain admite (±131 000 studs).
					local s = planeta.Superficie
					local esquina = V.largo({
						X = math.abs(s.Centro.X) + s.Tamano / 2,
						Y = s.Centro.Y + s.Techo,
						Z = math.abs(s.Centro.Z) + s.Tamano / 2,
					})
					Marco.verdadero(esquina < radio, `la superficie de {id} queda lejos del origen ({esquina})`)
				end
				Marco.verdadero(V.largo(Datos.Sol.Centro) + Datos.Sol.Radio < radio, "el sol se sale")
				Marco.verdadero(V.largo(Datos.AgujeroNegro.Centro) < radio, "el agujero negro se sale")
			end
		)

		Marco.prueba("las superficies están lejos de todo lo que hay en el espacio y no se tocan", function()
			local cosas = { { X = 0, Y = 0, Z = 0 }, Datos.Sol.Centro, Datos.AgujeroNegro.Centro }
			for _, id in Datos.OrdenPlanetas do
				table.insert(cosas, Datos.Planetas[id].Centro)
			end
			for _, id in Datos.OrdenPlanetas do
				local s = Datos.Planetas[id].Superficie
				for _, cosa in cosas do
					-- Más que de sobra para que el streaming no cargue las dos cosas a la vez.
					Marco.verdadero(V.distancia(cosa, s.Centro) > 15000, `la superficie de {id} está cerca de algo`)
					Marco.igual(Espacio.SuperficieDe(cosa), nil)
				end
			end
			local h, m = Datos.Planetas.Humanos.Superficie, Datos.Planetas.Monstruos.Superficie
			local separacion = math.abs(h.Centro.X - m.Centro.X) - (h.Tamano + m.Tamano) / 2 - h.Margen - m.Margen
			Marco.verdadero(separacion > 8000, "las dos superficies están demasiado juntas")
		end)

		Marco.prueba("los terrenos están alineados con las celdas de 4 studs de Terrain", function()
			for _, id in Datos.OrdenPlanetas do
				local s = Datos.Planetas[id].Superficie
				local t = s.Terreno
				Marco.igual(t.Resolucion, 4)
				for _, valor in { s.Centro.X, s.Centro.Y, s.Centro.Z, s.Tamano / 2 } do
					Marco.igual(valor % 4, 0, `{id}: {valor} no es múltiplo de 4`)
				end
				Marco.igual((s.Tamano / t.Resolucion) % t.Trozo, 0, `{id}: los trozos no cubren el terreno justo`)
				Marco.igual(
					Datos.Planetas[id].Puerto.Posicion.Y,
					t.PuertoAltura,
					`{id}: el puerto no está en el suelo`
				)
				Marco.verdadero(s.Techo > t.BordeAltura + t.AlturaBase + 200, `{id}: el techo choca con las montañas`)
			end
		end)

		Marco.prueba("los bandos guardados (antiguos y nuevos) llevan a su planeta", function()
			Marco.igual(Espacio.PlanetaDeBando("Humanos"), "Humanos")
			Marco.igual(Espacio.PlanetaDeBando("Monstruos"), "Monstruos")
			Marco.igual(Espacio.PlanetaDeBando("Heroes"), "Humanos")
			Marco.igual(Espacio.PlanetaDeBando("Villanos"), "Monstruos")
			Marco.esNil(Espacio.PlanetaDeBando("Ninguno"))
			Marco.esNil(Espacio.PlanetaDeBando(nil))
			Marco.esNil(Espacio.PlanetaDeBando(42))
		end)
	end)

	-- ===== Zonas y transiciones =====

	Marco.grupo("Planetas: zonas, aterrizaje y despegue", function()
		Marco.prueba("cada punto cae en su zona: espacio, superficie o fuera", function()
			Marco.igual(Espacio.ZonaDe({ X = 0, Y = 0, Z = 0 }).Tipo, "Espacio")
			Marco.igual(Espacio.ZonaDe({ X = 0, Y = 0, Z = 60000 }).Tipo, "Fuera")
			for _, id in Datos.OrdenPlanetas do
				local zona = Espacio.ZonaDe(Datos.Planetas[id].Superficie.Centro)
				Marco.igual(zona.Tipo, "Superficie")
				Marco.igual(zona.Planeta, id)
				Marco.igual(Espacio.ZonaDe(Datos.Planetas[id].Centro).Tipo, "Espacio")
			end
			Marco.verdadero(Espacio.MismaZona({ Tipo = "Espacio" }, { Tipo = "Espacio" }))
			Marco.falso(
				Espacio.MismaZona(
					{ Tipo = "Superficie", Planeta = "Humanos" },
					{ Tipo = "Superficie", Planeta = "Monstruos" }
				)
			)
		end)

		Marco.prueba("al aterrizar se llega a la superficie del planeta, bajo el techo y fuera del suelo", function()
			for _, id in Datos.OrdenPlanetas do
				local punto, mirada = Espacio.PuntoLlegada(id)
				local zona = Espacio.ZonaDe(punto)
				Marco.igual(zona.Tipo, "Superficie")
				Marco.igual(zona.Planeta, id)
				Marco.falso(Espacio.SuperaTecho(id, punto), "llegaría y volvería a despegar")
				local terreno = Datos.Planetas[id].Superficie.Terreno
				Marco.verdadero(
					Espacio.AlturaEnSuperficie(id, punto) > terreno.PuertoAltura + 50,
					"llega bajo el suelo"
				)
				casi(Marco, V.largo(mirada), 1, "mirada unitaria")
			end
		end)

		Marco.prueba("al despegar se sale al espacio por fuera de la atmósfera, mirando hacia fuera", function()
			for _, id in Datos.OrdenPlanetas do
				local punto, mirada = Espacio.PuntoOrbita(id)
				Marco.igual(Espacio.ZonaDe(punto).Tipo, "Espacio")
				Marco.esNil((Espacio.EnAtmosfera(punto)), "aparece dentro de la atmósfera: aterrizaría al instante")
				Marco.esNil((Espacio.CuerpoSolido(punto, NavesConfig.RadioNave)))
				local haciaFuera = V.unitario(V.restar(punto, Datos.Planetas[id].Centro))
				Marco.verdadero(V.punto(haciaFuera, mirada) > 0.99, "no mira hacia fuera del planeta")
				-- Está en la zona segura del planeta (nadie le dispara nada más salir).
				Marco.igual(Espacio.EnZonaSeguraEspacio(punto), id)
			end
		end)

		Marco.prueba("entrar en la atmósfera se detecta antes de tocar el planeta", function()
			for _, id in Datos.OrdenPlanetas do
				local planeta = Datos.Planetas[id]
				local justoDentro = V.sumar(planeta.Centro, { X = 0, Y = planeta.Radio + planeta.Atmosfera - 5, Z = 0 })
				local justoFuera = V.sumar(planeta.Centro, { X = 0, Y = planeta.Radio + planeta.Atmosfera + 5, Z = 0 })
				Marco.igual((Espacio.EnAtmosfera(justoDentro)), id)
				Marco.esNil((Espacio.EnAtmosfera(justoFuera)))
				Marco.esNil((Espacio.CuerpoSolido(justoDentro)), "la atmósfera no es sólida")
				Marco.igual((Espacio.CuerpoSolido(planeta.Centro)), id)
			end
			Marco.igual((Espacio.CuerpoSolido(Datos.Sol.Centro)), "Sol")
			Marco.esNil(
				(Espacio.CuerpoSolido(Datos.AgujeroNegro.Centro)),
				"el agujero negro no es sólido: se cae dentro"
			)
		end)

		Marco.prueba("subir por encima del techo de la superficie devuelve al espacio", function()
			for _, id in Datos.OrdenPlanetas do
				local s = Datos.Planetas[id].Superficie
				local alto = V.sumar(s.Centro, { X = 0, Y = s.Techo + 1, Z = 0 })
				Marco.verdadero(Espacio.SuperaTecho(id, alto))
				-- Al superarlo todavía cuenta como superficie (el servidor lo ve antes de que se salga de la zona).
				Marco.igual(Espacio.ZonaDe(alto).Planeta, id)
			end
		end)
	end)

	-- ===== Zonas seguras =====

	Marco.grupo("Planetas: zonas seguras", function()
		Marco.prueba("donde se aparece y donde se aterriza es zona segura; lejos del puerto, no", function()
			local zonas = Espacio.ZonasSegurasCombate()
			Marco.igual(#zonas, 2)
			for _, id in Datos.OrdenPlanetas do
				for _, punto in { Espacio.PuntoAparicion(id), Espacio.PuntoBajada(id), Espacio.PosicionPuerto(id) } do
					Marco.igual(Espacio.EnZonaSeguraSuperficie(punto), id)
					Marco.verdadero(CombateReglas.EnZonaSegura(punto, zonas))
				end
				local lejos = V.sumar(Espacio.PosicionPuerto(id), { X = 900, Y = 0, Z = 0 })
				Marco.esNil(Espacio.EnZonaSeguraSuperficie(lejos))
				Marco.falso(CombateReglas.EnZonaSegura(lejos, zonas))
				-- Muy por encima del puerto ya no está protegido (la zona es un cilindro con techo).
				local arriba = V.sumar(
					Espacio.PosicionPuerto(id),
					{ X = 0, Y = Datos.Planetas[id].Puerto.AltoZonaSegura + 10, Z = 0 }
				)
				Marco.falso(CombateReglas.EnZonaSegura(arriba, zonas))
			end
		end)

		Marco.prueba("la zona segura impide el golpe si el lanzador o el objetivo están dentro", function()
			local zonas = { { Centro = { X = 0, Y = 0, Z = 0 }, Radio = 10, AltoMin = -5, AltoMax = 20 } }
			local dentro, fuera = { X = 1, Y = 0, Z = 1 }, { X = 50, Y = 0, Z = 0 }
			Marco.verdadero(CombateReglas.ZonaSeguraImpide(dentro, fuera, zonas))
			Marco.verdadero(CombateReglas.ZonaSeguraImpide(fuera, dentro, zonas))
			Marco.falso(CombateReglas.ZonaSeguraImpide(fuera, { X = 60, Y = 0, Z = 0 }, zonas))
			Marco.falso(CombateReglas.EnZonaSegura({ X = 0, Y = 30, Z = 0 }, zonas), "por encima del techo")
			Marco.falso(CombateReglas.EnZonaSegura({ X = 0, Y = 0, Z = 0 }, {}), "sin zonas")
		end)

		Marco.prueba(
			"alrededor de cada planeta de bando hay zona segura de naves, pero no en mitad del viaje",
			function()
				for _, id in Datos.OrdenPlanetas do
					local planeta = Datos.Planetas[id]
					Marco.verdadero(planeta.RadioZonaSeguraEspacio > planeta.Radio + planeta.Atmosfera)
					Marco.igual(Espacio.EnZonaSeguraEspacio(planeta.Centro), id)
				end
				Marco.esNil(Espacio.EnZonaSeguraEspacio({ X = 0, Y = 0, Z = 0 }))
				Marco.falso(Espacio.EnZonaSegura({ X = 0, Y = 0, Z = 0 }))
			end
		)
	end)

	-- ===== Cielo =====

	Marco.grupo("Planetas: el cielo de las superficies", function()
		Marco.prueba("la base del cielo es una rotación (ejes unitarios, perpendiculares y sin reflejo)", function()
			for _, id in Datos.OrdenPlanetas do
				local este, arriba, sur = Espacio.BaseCielo(id)
				for _, eje in { este, arriba, sur } do
					casi(Marco, V.largo(eje), 1, "eje unitario", 1e-6)
				end
				casi(Marco, V.punto(este, arriba), 0, "este·arriba", 1e-6)
				casi(Marco, V.punto(este, sur), 0, "este·sur", 1e-6)
				casi(Marco, V.punto(arriba, sur), 0, "arriba·sur", 1e-6)
				-- este × arriba = sur (como X × Y = Z): no está reflejada.
				casi(Marco, V.punto(V.cruz(este, arriba), sur), 1, "orientación", 1e-6)
				-- La normal del planeta es el "arriba" del terreno.
				local normal = Espacio.EspacioACielo(id, Datos.Planetas[id].NormalAterrizaje)
				casi(Marco, normal.Y, 1, "la normal apunta arriba", 1e-4)
				-- Ida y vuelta.
				local d = V.unitario({ X = 0.3, Y = -0.4, Z = 0.8 })
				local vuelta = Espacio.CieloAEspacio(id, Espacio.EspacioACielo(id, d))
				casi(Marco, V.angulo(d, vuelta), 0, "ida y vuelta", 1e-3)
			end
		end)

		Marco.prueba("desde cada puerto se ven el otro planeta y su fuente de luz sobre el horizonte", function()
			for _, id in Datos.OrdenPlanetas do
				local otro = Datos.Planetas[Espacio.OtroPlaneta(id)]
				local _, fuente = Espacio.FuenteDeLuz(id)
				local elevacionOtro = Espacio.Elevacion(Espacio.DireccionEnCielo(id, otro.Centro))
				local elevacionLuz = Espacio.Elevacion(Espacio.DireccionEnCielo(id, fuente))
				Marco.verdadero(
					elevacionOtro >= Datos.Espacio.ElevacionMinimaCielo,
					`{id}: el otro planeta está a {elevacionOtro}°`
				)
				Marco.verdadero(elevacionLuz >= 25, `{id}: su sol está a {elevacionLuz}°, demasiado bajo`)
				-- El sol y el otro planeta no se tapan entre sí.
				local separacion =
					V.angulo(Espacio.DireccionEnCielo(id, otro.Centro), Espacio.DireccionEnCielo(id, fuente))
				Marco.verdadero(separacion > 30, `{id}: el sol y el otro planeta salen juntos ({separacion}°)`)
			end
			Marco.igual((Espacio.FuenteDeLuz("Humanos")), "Sol")
			Marco.igual((Espacio.FuenteDeLuz("Monstruos")), "AgujeroNegro")
		end)

		Marco.prueba("SobreHorizonte sube lo que está bajo y deja lo que ya está alto", function()
			local bajo = Espacio.SobreHorizonte({ X = 1, Y = -0.5, Z = 0 }, 10)
			casi(Marco, Espacio.Elevacion(bajo), 10, "elevación", 1e-6)
			Marco.verdadero(bajo.X > 0.9, "conserva el rumbo")
			local alto = Espacio.SobreHorizonte({ X = 0, Y = 1, Z = 1 }, 10)
			casi(Marco, Espacio.Elevacion(alto), 45, "no se toca", 1e-6)
		end)
	end)

	-- ===== Agujero negro =====

	Marco.grupo("Planetas: atracción del agujero negro", function()
		local params = Datos.AgujeroNegro.Atraccion
		local centro = Datos.AgujeroNegro.Centro

		Marco.prueba(
			"la atracción crece al acercarse, vale lo indicado en el radio sin retorno y tiene tope",
			function()
				Marco.igual(Gravedad.Arrastre(params.RadioInfluencia, params), 0)
				Marco.igual(Gravedad.Arrastre(params.RadioInfluencia + 1000, params), 0)
				casi(
					Marco,
					Gravedad.Arrastre(params.RadioSinRetorno, params),
					params.VelocidadSinRetorno,
					"sin retorno",
					1e-6
				)
				local anterior = -1
				for d = params.RadioInfluencia, 10, -250 do
					local valor = Gravedad.Arrastre(d, params)
					Marco.verdadero(valor >= anterior, `no crece en {d}`)
					Marco.verdadero(valor <= params.VelocidadMaxima)
					anterior = valor
				end
				Marco.igual(Gravedad.Arrastre(1, params), params.VelocidadMaxima)
				Marco.igual(Gravedad.Arrastre(0 / 0, params), 0)
			end
		)

		Marco.prueba(
			"una nave sin mejorar no escapa desde dentro del radio sin retorno; con el motor al máximo, sí",
			function()
				Marco.falso(Gravedad.PuedeEscapar(params.RadioSinRetorno * 0.9, base.VelocidadMax, params))
				Marco.verdadero(Gravedad.PuedeEscapar(params.RadioSinRetorno * 1.2, base.VelocidadMax, params))
				Marco.verdadero(Gravedad.PuedeEscapar(params.RadioSinRetorno * 0.9, tope.VelocidadMax, params))
				-- El turbo deja escapar desde todavía más adentro.
				local radioTurbo = Gravedad.RadioDeEscape(tope.VelocidadMax * tope.TurboMult, params)
				Marco.verdadero(radioTurbo < Gravedad.RadioDeEscape(tope.VelocidadMax, params))
				Marco.verdadero(radioTurbo > Datos.AgujeroNegro.RadioHorizonte, "el horizonte es una trampa siempre")
				casi(
					Marco,
					Gravedad.Arrastre(Gravedad.RadioDeEscape(base.VelocidadMax, params), params),
					base.VelocidadMax,
					"RadioDeEscape es la inversa",
					1e-6
				)
			end
		)

		Marco.prueba("el vector de arrastre apunta al centro y no afecta a los planetas ni a su órbita", function()
			local p = V.sumar(centro, { X = 3000, Y = 0, Z = 0 })
			local x, y, z = Gravedad.VectorArrastre(p, centro, params)
			Marco.verdadero(x < 0 and math.abs(y) < 1e-9 and math.abs(z) < 1e-9)
			casi(Marco, math.sqrt(x * x + y * y + z * z), Gravedad.Arrastre(3000, params), "módulo", 1e-6)
			for _, id in Datos.OrdenPlanetas do
				local orbita = Espacio.PuntoOrbita(id)
				Marco.igual(Gravedad.Arrastre(V.distancia(orbita, centro), params), 0, `atrae en la órbita de {id}`)
				local planeta = Datos.Planetas[id]
				Marco.verdadero(
					V.distancia(planeta.Centro, centro) - planeta.RadioZonaSeguraEspacio > params.RadioInfluencia,
					`la zona segura de {id} toca la atracción`
				)
			end
		end)

		Marco.prueba("el servidor acepta caer y volar normal, pero no escapar más deprisa de lo posible", function()
			local holgura, margen = NavesConfig.HolguraVelocidad, NavesConfig.MargenPosicion
			local dt = 0.2
			local v = base.VelocidadMax
			-- Cayendo hacia el centro a la velocidad del motor más el arrastre: válido.
			local p0 = V.sumar(centro, { X = 2500, Y = 0, Z = 0 })
			local caida = v + Gravedad.Arrastre(2500 - (v + 400) * dt, params)
			local p1 = V.sumar(p0, { X = -caida * dt, Y = 0, Z = 0 })
			Marco.verdadero(Gravedad.MovimientoValido(p0, p1, dt, v, centro, params, holgura, margen), "caer")
			-- Lejos del agujero, a la velocidad normal: válido.
			local lejos = V.sumar(centro, { X = 20000, Y = 0, Z = 0 })
			Marco.verdadero(
				Gravedad.MovimientoValido(
					lejos,
					V.sumar(lejos, { X = v * dt, Y = 0, Z = 0 }),
					dt,
					v,
					centro,
					params,
					holgura,
					margen
				),
				"volar lejos"
			)
			-- Dentro del radio sin retorno, alejarse a toda velocidad (ignorando la atracción): trampa.
			local q0 = V.sumar(centro, { X = params.RadioSinRetorno * 0.8, Y = 0, Z = 0 })
			local q1 = V.sumar(q0, { X = v * 3 * dt, Y = 0, Z = 0 })
			Marco.falso(Gravedad.MovimientoValido(q0, q1, dt, v, centro, params, holgura, margen), "escapar")
			-- Moverse de lado (en órbita) sí se puede.
			local q2 = V.sumar(q0, { X = 0, Y = 0, Z = v * dt })
			Marco.verdadero(Gravedad.MovimientoValido(q0, q2, dt, v, centro, params, holgura, margen), "de lado")
			-- Datos rotos: no válido.
			Marco.falso(
				Gravedad.MovimientoValido(q0, { X = 0 / 0, Y = 0, Z = 0 }, dt, v, centro, params, holgura, margen)
			)
		end)

		Marco.prueba("ContenerFuera quita la velocidad que entra en un cuerpo sólido y deja salir", function()
			local c = { X = 0, Y = 0, Z = 0 }
			-- Fuera del radio: sin cambios.
			local x, y, z = Gravedad.ContenerFuera(0, 200, 0, 0, -50, 0, c, 100)
			Marco.igualProfundo({ x, y, z }, { 0, -50, 0 })
			-- Dentro, yendo hacia el centro: la parte radial pasa a ser hacia fuera; la tangencial se conserva.
			x, y, z = Gravedad.ContenerFuera(0, 99, 0, 30, -50, 0, c, 100)
			Marco.verdadero(y > 0, "sigue entrando")
			casi(Marco, x, 30, "tangencial")
			-- Dentro pero saliendo: se le ayuda a salir, nunca se le frena.
			x, y, z = Gravedad.ContenerFuera(0, 99, 0, 0, 20, 0, c, 100)
			Marco.verdadero(y >= 20)
		end)
	end)

	-- ===== Sol =====

	Marco.grupo("Planetas: recalentamiento junto al sol", function()
		local params = Datos.Sol.Calor

		Marco.prueba("el calor objetivo es 0 lejos, crece al acercarse y es el máximo en el núcleo", function()
			Marco.igual(Calor.Objetivo(params.RadioAviso, params), 0)
			Marco.igual(Calor.Objetivo(params.RadioAviso * 2, params), 0)
			casi(Marco, Calor.Objetivo(params.RadioNucleo, params), params.CalorMax, "núcleo")
			casi(Marco, Calor.Objetivo(Datos.Sol.Radio, params), params.CalorMax, "en la superficie del sol")
			local anterior = -1
			for d = params.RadioAviso, params.RadioNucleo, -200 do
				local valor = Calor.Objetivo(d, params)
				Marco.verdadero(valor >= anterior, `no crece en {d}`)
				anterior = valor
			end
			Marco.verdadero(Datos.Sol.Radio < params.RadioNucleo, "el núcleo de calor envuelve al sol")
		end)

		Marco.prueba(
			"el calor se acerca poco a poco al objetivo, con la subida limitada, y se enfría al alejarse",
			function()
				local calor = 0
				local d = params.RadioNucleo
				calor = Calor.Paso(calor, d, 1, params)
				Marco.verdadero(calor <= params.SubidaMaxima + 1e-9, "sube de golpe")
				for _ = 1, 200 do
					calor = Calor.Paso(calor, d, 0.2, params)
				end
				casi(Marco, calor, params.CalorMax, "acaba en el máximo", 0.5)
				-- Lejos se enfría.
				local antes = calor
				calor = Calor.Paso(calor, params.RadioAviso * 2, 1, params)
				Marco.verdadero(calor < antes)
				for _ = 1, 300 do
					calor = Calor.Paso(calor, params.RadioAviso * 2, 0.2, params)
				end
				casi(Marco, calor, 0, "se enfría del todo", 0.5)
				-- Igual da llamarlo con pasos cortos o largos (sin subida limitada).
				local a, b = 10, 10
				for _ = 1, 10 do
					a = Calor.Paso(a, params.RadioAviso * 2, 0.1, params)
				end
				b = Calor.Paso(b, params.RadioAviso * 2, 1, params)
				casi(Marco, a, b, "independiente del paso", 1e-6)
				Marco.igual(
					Calor.Paso(0 / 0, d, 0.2, params) == Calor.Paso(0, d, 0.2, params),
					true,
					"NaN cuenta como 0"
				)
			end
		)

		Marco.prueba("solo hay daño por encima del umbral, y es el máximo con el calor al máximo", function()
			Marco.igual(Calor.DanoPorSegundo(params.UmbralDano, params), 0)
			Marco.igual(Calor.DanoPorSegundo(0, params), 0)
			casi(Marco, Calor.DanoPorSegundo(params.CalorMax, params), params.DanoPorSegundo, "máximo")
			Marco.igual(Calor.Nivel(0, params), "Normal")
			Marco.igual(Calor.Nivel(params.UmbralAviso, params), "Aviso")
			Marco.igual(Calor.Nivel(params.UmbralDano + 1, params), "Peligro")
			-- Quedarse a la distancia segura nunca llega a dañar.
			local seguro = Calor.DistanciaSegura(params)
			casi(Marco, Calor.Objetivo(seguro, params), params.UmbralDano, "distancia segura", 1e-6)
			Marco.verdadero(seguro > params.RadioNucleo and seguro < params.RadioAviso)
		end)

		Marco.prueba("el planeta humano y su órbita no se calientan", function()
			local planeta = Datos.Planetas.Humanos
			local orbita = Espacio.PuntoOrbita("Humanos")
			Marco.igual(Calor.Objetivo(V.distancia(orbita, Datos.Sol.Centro), params), 0)
			Marco.verdadero(
				V.distancia(planeta.Centro, Datos.Sol.Centro) - planeta.RadioZonaSeguraEspacio > params.RadioAviso,
				"la zona segura está dentro del calor"
			)
		end)

		Marco.prueba("el daño del calor puede saltarse el escudo", function()
			local stats = base
			local estado = NavesReglas.NuevoEstado(stats, 0)
			local r = NavesReglas.AplicarDano(estado, stats, 10, 100, true)
			Marco.verdadero(r.Aplicado)
			Marco.igual(r.DanoEscudo, 0)
			Marco.igual(r.DanoCasco, 10)
			Marco.igual(estado.Vida, stats.VidaMax - 10)
			-- Sin la opción, el escudo absorbe primero (como siempre).
			local otro = NavesReglas.NuevoEstado(stats, 0)
			local r2 = NavesReglas.AplicarDano(otro, stats, 10, 100)
			Marco.igual(r2.DanoEscudo, 10)
			Marco.igual(r2.DanoCasco, 0)
		end)
	end)

	-- ===== Iluminación =====

	Marco.grupo("Planetas: iluminación por zonas", function()
		Marco.prueba("los colores en hexadecimal van y vuelven", function()
			local r, g, b = Luz.Hex("#1E5BB8")
			Marco.igualProfundo({ r, g, b }, { 30, 91, 184 })
			Marco.igual(Luz.AHex(30, 91, 184), "#1E5BB8")
			Marco.igual(Luz.AHex(-5, 300, 12.4), "#00FF0C")
			Marco.igualProfundo({ Luz.Hex("basura") }, { 0, 0, 0 })
		end)

		Marco.prueba("todos los presets tienen los mismos campos (se pueden mezclar entre sí)", function()
			local referencia = Iluminacion.Presets.EspacioProfundo
			for nombre, preset in Iluminacion.Presets do
				for clave, valor in referencia do
					Marco.distinto(preset[clave], nil, `{nombre} no tiene {clave}`)
					if type(valor) == "table" then
						for subclave in valor do
							Marco.distinto(preset[clave][subclave], nil, `{nombre}.{clave} no tiene {subclave}`)
						end
					end
				end
				Marco.verdadero(preset.Fuente == "Sol" or preset.Fuente == "Luna", `{nombre}: Fuente`)
			end
			for _, mezcla in { Iluminacion.Mezcla.Sol, Iluminacion.Mezcla.AgujeroNegro } do
				Marco.distinto(Iluminacion.Presets[mezcla.Preset], nil)
			end
			Marco.distinto(Iluminacion.Presets[Iluminacion.Mezcla.Profundo], nil)
		end)

		Marco.prueba("mezclar presets interpola números y colores y el más pesado decide lo demás", function()
			local a = { N = 0, C = "#000000", F = "Sol", T = { X = 2 } }
			local b = { N = 10, C = "#FFFFFF", F = "Luna", T = { X = 4 } }
			local mitad = Luz.Mezclar({ a, b }, { 0.4, 0.6 })
			casi(Marco, mitad.N, 6, "número")
			Marco.igual(mitad.C, "#999999")
			Marco.igual(mitad.F, "Luna")
			casi(Marco, mitad.T.X, 3.2, "tabla anidada")
			local soloA = Luz.Mezclar({ a, b }, { 1, 0 })
			Marco.igualProfundo(soloA, { N = 0, C = "#000000", F = "Sol", T = { X = 2 } })
			-- Acercar: con mucho tiempo se llega al objetivo; con poco, se avanza poco.
			Marco.igual(Luz.Acercar(a, b, 100, 2).N, 10)
			local paso = Luz.Acercar(a, b, 0.05, 1)
			Marco.verdadero(paso.N > 0 and paso.N < 1)
		end)

		Marco.prueba(
			"en la estación del centro es espacio profundo; junto al sol, luz del sol, y junto al agujero, la suya",
			function()
				local _, pesos = Luz.PesosEspacio({ X = 0, Y = 0, Z = 0 })
				casi(Marco, pesos[3], 1, "estación")
				for _, caso in
					{
						{ Datos.Planetas.Humanos.Centro, 1, Datos.Sol.Centro },
						{ Datos.Planetas.Monstruos.Centro, 2, Datos.AgujeroNegro.Centro },
					}
				do
					local nombres, p = Luz.PesosEspacio(caso[1])
					casi(Marco, p[1] + p[2] + p[3], 1, "suman 1")
					Marco.verdadero(p[caso[2]] > 0.99, `en {nombres[caso[2]]} pesa {p[caso[2]]}`)
					local direccion = Luz.DireccionEspacio(caso[1])
					local hacia = V.unitario(V.restar(caso[3], caso[1]))
					Marco.verdadero(V.angulo(direccion, hacia) < 0.5, "la luz no viene de su fuente")
				end
				-- En medio la dirección sigue siendo unitaria (nunca se queda sin luz).
				casi(Marco, V.largo(Luz.DireccionEspacio({ X = 0, Y = 0, Z = 0 })), 1, "unitaria")
			end
		)

		Marco.prueba("la luz nunca viene de debajo del horizonte", function()
			local d = Luz.LimitarElevacion({ X = 0, Y = -1, Z = 1 }, 4)
			casi(Marco, math.deg(math.asin(d.Y)), 4, "elevación", 1e-6)
			Marco.verdadero(d.Z > 0.99)
			local alto = Luz.LimitarElevacion({ X = 1, Y = 1, Z = 0 }, 4)
			casi(Marco, alto.Y, math.sqrt(0.5), "no se toca")
		end)

		Marco.prueba(
			"el buscador de hora y latitud apunta la luz (sol o luna) a menos de 0,5° de lo pedido",
			function()
				local ajustes = Iluminacion.Ajustes
				local tabla = Luz.CrearTabla(cieloDePrueba, ajustes.PasoHora, ajustes.PasoLatitud)
				Marco.verdadero(#tabla > 1000)
				local objetivos = {
					{ X = 0.3, Y = 0.8, Z = 0.2 },
					{ X = -0.9, Y = 0.1, Z = 0.4 },
					{ X = 0.1, Y = 0.07, Z = -1 },
					{ X = 0, Y = 1, Z = 0 },
					Luz.DireccionEspacio(Datos.Planetas.Humanos.Centro),
				}
				for _, objetivo in objetivos do
					local o = Luz.LimitarElevacion(objetivo, ajustes.ElevacionMinima)
					for _, fuente in { "Sol", "Luna" } do
						local hora, latitud, error = Luz.Resolver(
							o,
							fuente,
							cieloDePrueba,
							tabla,
							ajustes.PasoHora,
							ajustes.PasoLatitud,
							ajustes.Refinados
						)
						Marco.verdadero(error < 0.5, `{fuente}: error de {error}°`)
						Marco.verdadero(hora >= 0 and hora < 24 and latitud >= -90 and latitud <= 90)
						local sol, luna = cieloDePrueba(hora, latitud)
						if fuente == "Luna" then
							Marco.verdadero(sol.Y < 0, "con la luna tiene que ser de noche (cielo estrellado)")
							Marco.verdadero(V.angulo(luna, o) < 0.5)
						else
							Marco.verdadero(sol.Y > 0)
						end
					end
				end
			end
		)
	end)

	-- ===== Ruido y terreno =====

	Marco.grupo("Planetas: ruido y terreno procedural", function()
		Marco.prueba("el ruido es determinista, continuo y depende de la semilla", function()
			local a, b, c = Ruido.nuevo(7), Ruido.nuevo(7), Ruido.nuevo(8)
			local distintos = false
			local maximo = 0
			for i = 1, 400 do
				local x, z = i * 0.37, i * 0.61 - 40
				local va = a:Valor(x, z)
				Marco.igual(va, b:Valor(x, z))
				distintos = distintos or math.abs(va - c:Valor(x, z)) > 1e-6
				maximo = math.max(maximo, math.abs(va))
				-- Continuo: un paso pequeño cambia poco.
				Marco.verdadero(math.abs(a:Valor(x + 0.001, z) - va) < 0.01, "salto en el ruido")
			end
			Marco.verdadero(distintos, "la semilla no cambia nada")
			Marco.verdadero(maximo <= 1.05 and maximo > 0.3, `rango del ruido: {maximo}`)
			Marco.igual(a:Valor(3, 5), 0, "vale 0 en los enteros")
			local crestas = a:Crestas(12.3, 45.6, 10)
			Marco.verdadero(crestas >= 0 and crestas <= 1)
		end)

		for _, id in { "Humanos", "Monstruos" } do
			local superficie = Datos.Planetas[id].Superficie
			local parametros = superficie.Terreno
			local puerto = Datos.Planetas[id].Puerto.Posicion
			local generador = GeneradorTerreno.nuevo(parametros, superficie.Tamano, puerto)

			Marco.prueba(`{id}: el puerto es llano y el borde del mapa es una muralla de montañas`, function()
				for _, punto in { { 0, 0 }, { 60, 0 }, { -60, 30 }, { 0, -120 }, { 100, 100 } } do
					casi(
						Marco,
						generador:Altura(puerto.X + punto[1], puerto.Z + punto[2]),
						parametros.PuertoAltura,
						"puerto llano",
						1e-6
					)
				end
				local mitad = superficie.Tamano / 2
				local interior, borde = 0, 0
				for i = 1, 40 do
					local t = -mitad + i * (superficie.Tamano / 41)
					interior += generador:Altura(t * 0.5, t * 0.3)
					borde += generador:Altura(mitad - 8, t)
				end
				Marco.verdadero(borde / 40 > interior / 40 + parametros.BordeAltura * 0.5, "el borde no es más alto")
			end)

			Marco.prueba(`{id}: el terreno es determinista y los trozos tienen el formato de WriteVoxels`, function()
				local otro = GeneradorTerreno.nuevo(parametros, superficie.Tamano, puerto)
				Marco.igual(generador:Altura(123.4, -567.8), otro:Altura(123.4, -567.8))

				local lista = generador:Trozos()
				local lado = generador:TrozosPorLado()
				Marco.igual(#lista, lado * lado)
				-- El primero es el del puerto.
				local ancho = parametros.Trozo * parametros.Resolucion
				local primero = lista[1]
				local x0 = -superficie.Tamano / 2 + primero.I * ancho
				local z0 = -superficie.Tamano / 2 + primero.J * ancho
				Marco.verdadero(puerto.X >= x0 - ancho and puerto.X <= x0 + 2 * ancho, "no empieza por el puerto")
				Marco.verdadero(puerto.Z >= z0 - ancho and puerto.Z <= z0 + 2 * ancho, "no empieza por el puerto")

				local trozo = generador:Trozo(primero.I, primero.J)
				Marco.igual(#trozo.Materiales, trozo.Celdas.X)
				Marco.igual(#trozo.Materiales[1], trozo.Celdas.Y)
				Marco.igual(#trozo.Materiales[1][1], trozo.Celdas.Z)
				Marco.igual(#trozo.Ocupacion[1][1], trozo.Celdas.Z)
				Marco.igual(trozo.Origen.X % 4, 0)
				Marco.igual(trozo.Origen.Y % 4, 0)
				Marco.verdadero(trozo.Celdas.Y < 200, `trozo demasiado alto: {trozo.Celdas.Y} celdas`)
				local solidas = 0
				for x = 1, trozo.Celdas.X do
					for y = 1, trozo.Celdas.Y do
						for z = 1, trozo.Celdas.Z do
							local material = trozo.Materiales[x][y][z]
							local ocupacion = trozo.Ocupacion[x][y][z]
							Marco.verdadero(MATERIALES_TERRENO[material] == true, `material desconocido: {material}`)
							Marco.verdadero(ocupacion >= 0 and ocupacion <= 1)
							if material == "Air" then
								Marco.igual(ocupacion, 0)
							elseif ocupacion > 0 then
								solidas += 1
							end
						end
					end
				end
				Marco.verdadero(solidas > trozo.Celdas.X * trozo.Celdas.Z, "el trozo está casi vacío")
			end)

			Marco.prueba(
				`{id}: hay suelo en cada columna (sin agujeros) y los materiales del estilo aparecen`,
				function()
					local vistos = {}
					local lista = generador:Trozos()
					-- Unos cuantos trozos repartidos por el mapa.
					for indice = 1, #lista, math.max(1, math.floor(#lista / 9)) do
						local t = lista[indice]
						local trozo = generador:Trozo(t.I, t.J)
						for x = 1, trozo.Celdas.X do
							for z = 1, trozo.Celdas.Z do
								local tieneSuelo = false
								for y = 1, trozo.Celdas.Y do
									local material = trozo.Materiales[x][y][z]
									vistos[material] = true
									if material ~= "Air" and material ~= "Water" and trozo.Ocupacion[x][y][z] > 0 then
										tieneSuelo = true
									end
								end
								Marco.verdadero(tieneSuelo, `columna sin suelo en el trozo {t.I},{t.J}`)
							end
						end
					end
					local m = parametros.Materiales
					if id == "Humanos" then
						for _, clave in { "Hierba", "Agua", "Roca", "Puerto" } do
							Marco.verdadero(vistos[m[clave]], `no aparece {clave} ({m[clave]})`)
						end
					else
						for _, clave in { "Base", "Grieta", "Puerto" } do
							Marco.verdadero(vistos[m[clave]], `no aparece {clave} ({m[clave]})`)
						end
						Marco.esNil(vistos.Water, "en el planeta de los monstruos no hay agua")
					end
				end
			)
		end
	end)

	-- ===== Aspecto desde el espacio =====

	Marco.grupo("Planetas: aspecto desde el espacio", function()
		Marco.prueba("las piezas se reparten igual con la misma semilla y se apoyan sobre la esfera", function()
			for _, id in Datos.OrdenPlanetas do
				local planeta = Datos.Planetas[id]
				for _, capa in planeta.Apariencia do
					if capa.Tipo ~= "Manchas" and capa.Tipo ~= "Nubes" then
						continue
					end
					local a = Apariencia.Piezas(capa, planeta.Radio)
					local b = Apariencia.Piezas(capa, planeta.Radio)
					Marco.igualProfundo(a, b)
					Marco.verdadero(#a >= capa.Cantidad, `{id}: pocas piezas`)
					for _, pieza in a do
						casi(Marco, V.largo(pieza.Direccion), 1, "dirección unitaria", 1e-6)
						if capa.Tipo == "Manchas" then
							-- Lo más alto de la pieza asoma justo `Relieve` sobre la superficie.
							local cima = pieza.Distancia + pieza.Tamano.Y / 2
							casi(Marco, cima, planeta.Radio * (1 + capa.Relieve), "relieve", 1e-6)
							Marco.verdadero(pieza.Tamano.Y < pieza.Tamano.Z, "debe ser una lente aplanada")
						else
							Marco.verdadero(pieza.Distancia > planeta.Radio, "nubes bajo el suelo")
						end
						if capa.Latitud and not capa.Polos then
							-- Las piezas se desvían un poco de su grupo: se acepta un margen.
							local latitud = math.deg(math.asin(pieza.Direccion.Y))
							Marco.verdadero(latitud <= capa.Latitud[2] + 25 and latitud >= capa.Latitud[1] - 25)
						end
					end
				end
			end
		end)

		Marco.prueba("cada planeta usa pocas partes (rendimiento en móvil)", function()
			for _, id in Datos.OrdenPlanetas do
				local partes = Apariencia.ContarPartes(id)
				Marco.verdadero(partes <= 140, `{id} usa {partes} partes`)
				Marco.verdadero(partes >= 20, `{id} usa muy pocas partes ({partes}): se verá pobre`)
			end
		end)
	end)
end
