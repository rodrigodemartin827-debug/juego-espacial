--[[
	Pruebas del andar de los monstruos:
	  - los datos de las animaciones (Personajes/Datos/AnimacionesMonstruo) están bien formados y, horneados, son
	    animaciones R6 válidas (articulaciones R6, tiempos crecientes, bucles que cierran),
	  - los pies: con la cinemática real del R6 los pies pisan el suelo sin hundirse ni flotar y la velocidad de la
	    animación cuadra con la de andar (no patinan),
	  - la cinemática y el horneado hacen lo que dicen,
	  - qué personajes reciben el andar de monstruo y qué animación toca en cada momento (Personajes/Locomocion).
	Lo que se ve en Studio (el controlador del cliente) está en la lista de comprobación del README.
]]

local Entorno = require("../infraestructura/Entorno")
local Pisada = require("../infraestructura/Pisada")

local PIEZAS_R6 = {
	Torso = true,
	Head = true,
	["Right Arm"] = true,
	["Left Arm"] = true,
	["Right Leg"] = true,
	["Left Leg"] = true,
}
local ESTADOS = { "Reposo", "Andar", "Correr", "Saltar", "Caer" }

local function cargar()
	local entorno = Entorno.nuevo()
	local function m(ruta)
		return entorno.servidor.requerir(`ReplicatedStorage.Shared.{ruta}`)
	end
	return {
		Datos = m("Personajes.Datos.AnimacionesMonstruo"),
		Horneado = m("Animacion.Horneado"),
		Cinematica = m("Animacion.CinematicaR6"),
		Catalogo = m("Animacion.Catalogo"),
		Locomocion = m("Personajes.Locomocion"),
		Recursos = m("Combate.Datos.Recursos"),
		Animaciones = m("Combate.Datos.Animaciones"),
	}
end

local function cerca(a: number, b: number, tolerancia: number?): boolean
	return math.abs(a - b) <= (tolerancia or 1e-6)
end

local function vectorCerca(a, b, tolerancia: number?): boolean
	return cerca(a[1], b[1], tolerancia) and cerca(a[2], b[2], tolerancia) and cerca(a[3], b[3], tolerancia)
end

local function fmt(v): string
	return string.format("(%.3f, %.3f, %.3f)", v[1], v[2], v[3])
end

-- Animación mínima válida con todas las piezas quietas, para probar el horneado.
local function animacionQuieta(extra)
	local function canal(pose)
		return { Claves = { { T = 0, Pose = pose }, { T = 1, Pose = pose } } }
	end
	local definicion = {
		Duracion = 1,
		Bucle = true,
		Canales = {
			Torso = canal({ 0, 0, 0 }),
			Head = canal({ 0, 0, 0 }),
			["Right Arm"] = canal({ 0, 0, 0 }),
			["Left Arm"] = canal({ 0, 0, 0 }),
			["Right Leg"] = canal({ 0, 0, 0 }),
			["Left Leg"] = canal({ 0, 0, 0 }),
		},
	}
	for clave, valor in extra or {} do
		definicion[clave] = valor
	end
	return definicion
end

return function(Marco)
	local M = cargar()
	local Datos, Horneado, Cinematica, Locomocion = M.Datos, M.Horneado, M.Cinematica, M.Locomocion

	Marco.grupo("Andar de monstruo: datos de las animaciones", function()
		Marco.prueba("hay reposo, andar, correr, saltar y caer, y ninguna tiene problemas", function()
			for _, estado in ESTADOS do
				local definicion = Datos.Definiciones[estado]
				Marco.distinto(definicion, nil, `falta la animación '{estado}'`)
				local problemas = Horneado.Validar(definicion)
				Marco.igual(#problemas, 0, `{estado}:\n{table.concat(problemas, "\n")}`)
			end
		end)

		Marco.prueba("reposo, andar, correr y caer se repiten; saltar no", function()
			for _, estado in { "Reposo", "Andar", "Correr", "Caer" } do
				Marco.verdadero(Datos.Definiciones[estado].Bucle, `{estado} debería ser un bucle`)
			end
			Marco.falso(Datos.Definiciones.Saltar.Bucle, "Saltar se reproduce una vez")
		end)

		Marco.prueba("cada estado tiene un nombre único, con su hueco para un ID en Recursos", function()
			local vistos = {}
			for _, estado in ESTADOS do
				local nombre = Datos.Nombres[estado]
				Marco.distinto(nombre, nil, `{estado} no tiene nombre`)
				Marco.esNil(vistos[nombre], `el nombre '{nombre}' está repetido`)
				vistos[nombre] = true
				Marco.esNil(M.Animaciones.Definiciones[nombre], `'{nombre}' choca con una animación del combate`)
				Marco.igual(type(M.Recursos.Animaciones[nombre]), "string", `Recursos.Animaciones.{nombre}`)
				Marco.distinto(M.Catalogo.Definicion(nombre), nil, `el catálogo no encuentra '{nombre}'`)
			end
		end)

		Marco.prueba("todas van con prioridad Movement (encima del Animate, debajo del combate)", function()
			for _, estado in ESTADOS do
				Marco.igual(Datos.Definiciones[estado].Prioridad, "Movement", estado)
				Marco.igual(M.Catalogo.Definicion(Datos.Nombres[estado]).Prioridad, "Movement", estado)
			end
			-- Las del combate no dicen nada: el Animador las carga con Action.
			for nombre, definicion in M.Animaciones.Definiciones do
				Marco.verdadero(definicion.Prioridad == nil or definicion.Prioridad == "Action", nombre)
			end
		end)

		Marco.prueba("horneadas: articulaciones R6, tiempos crecientes, lineales y bucles que cierran", function()
			for _, estado in ESTADOS do
				local original = Datos.Definiciones[estado]
				local horneada = M.Catalogo.Definicion(Datos.Nombres[estado])
				local cuadros = horneada.Cuadros
				Marco.verdadero(#cuadros >= 10, `{estado}: solo {#cuadros} cuadros`)
				Marco.igual(cuadros[1].T, 0, `{estado}: el primer cuadro debe estar en 0`)
				Marco.verdadero(cerca(cuadros[#cuadros].T, original.Duracion), `{estado}: el último en Duracion`)
				local anterior = -1
				for indice, cuadro in cuadros do
					Marco.verdadero(cuadro.T > anterior, `{estado}[{indice}]: T no crece`)
					anterior = cuadro.T
					Marco.igual(cuadro.Easing, "Linear", `{estado}[{indice}]: el horneado ya lleva el easing`)
					local cuantas = 0
					for pieza, pose in cuadro.Poses do
						cuantas += 1
						Marco.verdadero(PIEZAS_R6[pieza], `{estado}[{indice}]: '{pieza}' no es una pieza R6`)
						Marco.igual(#pose, 6, `{estado}[{indice}].{pieza}: la pose debe tener 6 valores`)
						for componente, valor in pose do
							Marco.verdadero(valor == valor and math.abs(valor) < 1e6, `{estado} {pieza}: NaN`)
							if componente <= 3 then
								Marco.verdadero(math.abs(valor) <= 180, `{estado} {pieza}: {valor}°`)
							end
						end
					end
					Marco.igual(cuantas, 6, `{estado}[{indice}]: cada cuadro debe llevar las 6 piezas`)
				end
				if horneada.Bucle then
					for pieza in PIEZAS_R6 do
						local a, b = cuadros[1].Poses[pieza], cuadros[#cuadros].Poses[pieza]
						for componente = 1, 6 do
							Marco.verdadero(
								cerca(a[componente], b[componente], 1e-4),
								`{estado}.{pieza}: el bucle no cierra ({a[componente]} vs {b[componente]})`
							)
						end
					end
				end
			end
		end)

		Marco.prueba("el catálogo da los nombres ordenados, sin repetir, y conserva los del combate", function()
			local nombres = M.Catalogo.Nombres()
			for i = 2, #nombres do
				Marco.verdadero(nombres[i - 1] < nombres[i], `orden: {nombres[i - 1]} / {nombres[i]}`)
			end
			for nombre in M.Animaciones.Definiciones do
				Marco.distinto(table.find(nombres, nombre), nil, nombre)
				Marco.igual(M.Catalogo.Definicion(nombre), M.Animaciones.Definiciones[nombre], nombre)
			end
			Marco.esNil(M.Catalogo.Definicion("NoExiste"))
		end)

		Marco.prueba("los umbrales del controlador son coherentes", function()
			local a = Datos.Ajustes
			Marco.verdadero(a.PararAndar < a.EmpezarAndar, "histéresis de andar")
			Marco.verdadero(a.EmpezarAndar < a.PararCorrer, "andar antes que correr")
			Marco.verdadero(a.PararCorrer < a.EmpezarCorrer, "histéresis de correr")
			Marco.verdadero(a.RitmoMinimo > 0 and a.RitmoMinimo < 1 and a.RitmoMaximo > 1, "límites de ritmo")
			Marco.verdadero(a.VelocidadCaida < 0 and a.VelocidadSalto > 0, "velocidades verticales")
			Marco.verdadero(a.IntervaloOtros > 0 and a.IntervaloOtros <= 0.25, "intervalo de los demás")
		end)
	end)

	Marco.grupo("Andar de monstruo: los pies (cinemática R6)", function()
		Marco.prueba("en reposo los dos pies pisan: ni se hunden ni flotan más de 0,12 studs", function()
			local definicion = Datos.Definiciones.Reposo
			local n = 96
			for i = 0, n do
				local t = definicion.Duracion * i / n
				local piezas = Cinematica.Piezas(Horneado.PoseEn(definicion, t))
				for _, pierna in { "Right Leg", "Left Leg" } do
					local altura = Cinematica.AlturaPie(piezas[pierna]) - Cinematica.ALTURA_SUELO
					Marco.verdadero(altura > -0.01, `{pierna} se hunde {-altura} en t={t}`)
					Marco.verdadero(altura < 0.12, `{pierna} flota {altura} en t={t}`)
				end
			end
		end)

		for _, estado in { "Andar", "Correr" } do
			Marco.prueba(`{estado}: los pies no patinan a la velocidad de referencia`, function()
				local definicion = Datos.Definiciones[estado]
				local analisis = Pisada.Analizar(Horneado, Cinematica, definicion)
				local referencia = definicion.VelocidadReferencia
				Marco.verdadero(
					math.abs(referencia - analisis.VelocidadNatural) / analisis.VelocidadNatural < 0.1,
					`VelocidadReferencia = {referencia}, pero los pies se mueven a {analisis.VelocidadNatural} studs/s`
				)
				Marco.verdadero(
					analisis.Patinaje < 0.35,
					`el pie de apoyo se aparta de media un {math.round(analisis.Patinaje * 100)} % de esa velocidad`
				)
				Marco.verdadero(analisis.Hundimiento < 0.01, `un pie se hunde {analisis.Hundimiento} studs`)
			end)
		end

		Marco.prueba("andando siempre hay un pie en el suelo; corriendo, poco tiempo en el aire", function()
			local andar = Pisada.Analizar(Horneado, Cinematica, Datos.Definiciones.Andar)
			Marco.igual(andar.Aire, 0, "andar no tiene fase aérea")
			local correr = Pisada.Analizar(Horneado, Cinematica, Datos.Definiciones.Correr)
			Marco.verdadero(correr.Aire > 0.05 and correr.Aire < 0.35, `aire al correr: {correr.Aire}`)
		end)

		Marco.prueba("a la velocidad normal de un jugador (16) corre sin salirse de los límites de ritmo", function()
			local a = Datos.Ajustes
			local correr = Datos.Definiciones.Correr.VelocidadReferencia
			local andar = Datos.Definiciones.Andar.VelocidadReferencia
			Marco.verdadero(16 / correr <= a.RitmoMaximo and 16 / correr >= 1, `ritmo a 16: {16 / correr}`)
			-- En toda la franja de andar, el ritmo necesario cabe en los límites (salvo justo al arrancar).
			Marco.verdadero(a.EmpezarCorrer / andar <= a.RitmoMaximo, `ritmo andando a tope: {a.EmpezarCorrer / andar}`)
			Marco.verdadero(
				a.PararCorrer / correr >= a.RitmoMinimo,
				`ritmo corriendo despacio: {a.PararCorrer / correr}`
			)
		end)

		Marco.prueba("la cabeza se queda mirando al frente: nunca gira más de 45° en el mundo", function()
			for _, estado in { "Reposo", "Andar", "Correr" } do
				local definicion = Datos.Definiciones[estado]
				for i = 0, 60 do
					local t = definicion.Duracion * i / 60
					local cabeza = Cinematica.Piezas(Horneado.PoseEn(definicion, t)).Head
					-- La cara mira hacia -Z de la cabeza: su dirección en el mundo no debe apartarse mucho del frente.
					local frente = Cinematica.Aplicar(cabeza.R, { 0, 0, -1 })
					Marco.verdadero(
						-frente[3] > math.cos(math.rad(45)),
						`{estado} t={t}: la cabeza mira a {fmt(frente)}`
					)
				end
			end
		end)
	end)

	Marco.grupo("Andar de monstruo: cinemática y horneado", function()
		Marco.prueba("en reposo cada pieza del R6 está en su sitio y los pies en el suelo", function()
			local piezas = Cinematica.Piezas({})
			Marco.verdadero(vectorCerca(piezas.Torso.P, { 0, 0, 0 }), fmt(piezas.Torso.P))
			Marco.verdadero(vectorCerca(piezas.Head.P, { 0, 1.5, 0 }), fmt(piezas.Head.P))
			Marco.verdadero(vectorCerca(piezas["Right Arm"].P, { 1.5, 0, 0 }), fmt(piezas["Right Arm"].P))
			Marco.verdadero(vectorCerca(piezas["Left Arm"].P, { -1.5, 0, 0 }), fmt(piezas["Left Arm"].P))
			Marco.verdadero(vectorCerca(piezas["Right Leg"].P, { 0.5, -2, 0 }), fmt(piezas["Right Leg"].P))
			Marco.verdadero(vectorCerca(piezas["Left Leg"].P, { -0.5, -2, 0 }), fmt(piezas["Left Leg"].P))
			Marco.verdadero(cerca(Cinematica.AlturaPie(piezas["Right Leg"]), Cinematica.ALTURA_SUELO))
		end)

		Marco.prueba("los ángulos mueven las piezas hacia donde dice la documentación", function()
			-- Brazo derecho con cabeceo 90: la mano va hacia delante (-Z).
			local mano =
				Cinematica.Punto(Cinematica.Piezas({ ["Right Arm"] = { 90, 0, 0 } })["Right Arm"], { 0, -1, 0 })
			Marco.verdadero(mano[3] < -1.4, `mano: {fmt(mano)}`)
			-- Pierna derecha con ladeo 30: el pie se va a la derecha (+X).
			local pie = Cinematica.Punto(Cinematica.Piezas({ ["Right Leg"] = { 0, 0, 30 } })["Right Leg"], { 0, -1, 0 })
			Marco.verdadero(pie[1] > 1, `pie: {fmt(pie)}`)
			-- Torso con cabeceo 30: la cabeza va hacia delante y abajo.
			local cabeza = Cinematica.Piezas({ Torso = { 30, 0, 0 } }).Head.P
			Marco.verdadero(cabeza[3] < -0.5 and cabeza[2] < 1.5, `cabeza: {fmt(cabeza)}`)
			-- Torso con giro 30: el hombro derecho avanza.
			local hombro = Cinematica.Piezas({ Torso = { 0, 30, 0 } })["Right Arm"].P
			Marco.verdadero(hombro[3] < -0.5, `hombro: {fmt(hombro)}`)
		end)

		Marco.prueba("AngulosXYZ deshace RotacionXYZ", function()
			for _, angulos in { { 10, 20, 30 }, { -40, 15, -70 }, { 120, -60, 5 }, { 0, 0, 0 } } do
				local m = Cinematica.RotacionXYZ(angulos[1], angulos[2], angulos[3])
				local x, y, z = Cinematica.AngulosXYZ(m)
				Marco.verdadero(vectorCerca({ x, y, z }, angulos, 1e-6), `{fmt(angulos)} -> {fmt({ x, y, z })}`)
			end
		end)

		Marco.prueba("una pieza Mundo queda igual en el mundo aunque el torso se incline", function()
			local definicion = animacionQuieta()
			definicion.Canales.Torso = {
				Claves = { { T = 0, Pose = { 40, 15, -10 } }, { T = 1, Pose = { 40, 15, -10 } } },
			}
			definicion.Canales["Right Leg"].Mundo = true
			definicion.Canales.Head.Mundo = true
			definicion.Canales.Head.Claves = { { T = 0, Pose = { 0, 0, 25 } }, { T = 1, Pose = { 0, 0, 25 } } }
			local piezas = Cinematica.Piezas(Horneado.PoseEn(definicion, 0.5))
			local abajo = Cinematica.Aplicar(piezas["Right Leg"].R, { 0, 1, 0 })
			Marco.verdadero(vectorCerca(abajo, { 0, 1, 0 }, 1e-6), `la pierna debería seguir vertical: {fmt(abajo)}`)
			local esperada = Cinematica.RotacionDePose("Head", { 0, 0, 25 })
			for i = 1, 3 do
				for j = 1, 3 do
					Marco.verdadero(
						cerca(piezas.Head.R[i][j], esperada[i][j]),
						"la cabeza conserva su ladeo en el mundo"
					)
				end
			end
		end)

		Marco.prueba("AlturaAutomatica pone el pie más bajo en el suelo (más la altura pedida)", function()
			local definicion = animacionQuieta({ AlturaAutomatica = true })
			local inclinado = { 35, 0, 0, 0, 0, 0 }
			definicion.Canales.Torso = { Claves = { { T = 0, Pose = inclinado }, { T = 1, Pose = inclinado } } }
			local piezas = Cinematica.Piezas(Horneado.PoseEn(definicion, 0))
			local pie = math.min(Cinematica.AlturaPie(piezas["Right Leg"]), Cinematica.AlturaPie(piezas["Left Leg"]))
			Marco.verdadero(cerca(pie, Cinematica.ALTURA_SUELO), `pie a {pie}`)

			local enAire = { 35, 0, 0, 0, 0.4, 0 }
			definicion.Canales.Torso = { Claves = { { T = 0, Pose = enAire }, { T = 1, Pose = enAire } } }
			piezas = Cinematica.Piezas(Horneado.PoseEn(definicion, 0))
			pie = math.min(Cinematica.AlturaPie(piezas["Right Leg"]), Cinematica.AlturaPie(piezas["Left Leg"]))
			Marco.verdadero(cerca(pie, Cinematica.ALTURA_SUELO + 0.4), `pie a {pie}`)
		end)

		Marco.prueba("el desfase adelanta un canal dentro del ciclo", function()
			local definicion = animacionQuieta()
			definicion.Canales["Right Arm"] = {
				Desfase = 0.25,
				Claves = {
					{ T = 0, Pose = { 0, 0, 0 } },
					{ T = 0.5, Pose = { 40, 0, 0 }, Easing = "Linear" },
					{ T = 1, Pose = { 0, 0, 0 }, Easing = "Linear" },
				},
			}
			Marco.verdadero(cerca(Horneado.Evaluar(definicion, 0)["Right Arm"][1], 20))
			Marco.verdadero(cerca(Horneado.Evaluar(definicion, 0.25)["Right Arm"][1], 40))
			Marco.verdadero(cerca(Horneado.Evaluar(definicion, 0.9)["Right Arm"][1], 12))
		end)

		Marco.prueba("los easing empiezan en 0 y acaban en 1; Constant espera y Back se pasa", function()
			for _, estilo in Horneado.ESTILOS do
				for _, direccion in Horneado.DIRECCIONES do
					Marco.verdadero(cerca(Horneado.Easing(estilo, direccion, 0), 0), `{estilo} {direccion} en 0`)
					Marco.verdadero(cerca(Horneado.Easing(estilo, direccion, 1), 1), `{estilo} {direccion} en 1`)
				end
			end
			Marco.igual(Horneado.Easing("Constant", "Out", 0.99), 0)
			Marco.verdadero(Horneado.Easing("Back", "Out", 0.6) > 1, "Back Out se pasa de largo")
			Marco.verdadero(Horneado.Easing("Cubic", "In", 0.5) < 0.5, "Cubic In arranca despacio")
			Marco.verdadero(Horneado.Easing("Cubic", "Out", 0.5) > 0.5, "Cubic Out frena al llegar")
		end)

		Marco.prueba("la validación detecta los errores típicos", function()
			local function problemas(cambiar)
				local definicion = animacionQuieta()
				cambiar(definicion)
				return table.concat(Horneado.Validar(definicion), "\n")
			end
			Marco.igual(problemas(function() end), "", "la animación de base es correcta")
			Marco.contiene(
				problemas(function(d)
					d.Canales.Head = nil
				end),
				"falta el canal de 'Head'"
			)
			Marco.contiene(
				problemas(function(d)
					d.Canales.Cola = d.Canales.Torso
				end),
				"'Cola' no es una pieza animable de R6"
			)
			Marco.contiene(
				problemas(function(d)
					d.Canales.Torso.Claves[2].T = 0
				end),
				"no es mayor"
			)
			Marco.contiene(
				problemas(function(d)
					d.Canales.Torso.Claves[2].Pose = { 10, 0, 0 }
				end),
				"no cierra"
			)
			Marco.contiene(
				problemas(function(d)
					d.Canales.Torso.Claves[2].Easing = "Rebotito"
				end),
				"easing desconocido"
			)
			Marco.contiene(
				problemas(function(d)
					d.Canales.Torso.Claves[2].Pose = { 0, 0 }
				end),
				"3 ángulos"
			)
			Marco.contiene(
				problemas(function(d)
					d.Canales.Torso.Claves[2].T = 0.5
				end),
				"T = Duracion"
			)
			Marco.lanzaError(function()
				local definicion = animacionQuieta()
				definicion.Canales.Head = nil
				Horneado.Hornear(definicion)
			end, "mal formada")
		end)
	end)

	Marco.grupo("Andar de monstruo: qué personajes lo llevan y qué animación toca", function()
		Marco.prueba("solo el bando Monstruos se mueve como monstruo", function()
			Marco.verdadero(Locomocion.EsMonstruo("Monstruos"))
			Marco.falso(Locomocion.EsMonstruo("Humanos"))
			Marco.falso(Locomocion.EsMonstruo("Ninguno"))
		end)

		Marco.prueba("el bando de un jugador sale de su Player; el de un muñeco, de su modelo", function()
			Marco.igual(Locomocion.BandoDe(true, "Monstruos", nil), "Monstruos")
			Marco.igual(Locomocion.BandoDe(true, "Humanos", "Monstruos"), "Humanos", "manda el del jugador")
			Marco.igual(Locomocion.BandoDe(true, nil, "Monstruos"), "Ninguno", "sin datos cargados no es monstruo")
			Marco.igual(Locomocion.BandoDe(false, nil, "Monstruos"), "Monstruos", "muñeco monstruo")
			Marco.igual(Locomocion.BandoDe(false, "Monstruos", "Humanos"), "Humanos", "muñeco humano")
			Marco.igual(Locomocion.BandoDe(true, "Zombis", nil), "Ninguno", "un valor desconocido no cuenta")
			Marco.igual(Locomocion.BandoDe(true, 7, nil), "Ninguno")
		end)

		local a = Datos.Ajustes
		local REF = {
			Andar = Datos.Definiciones.Andar.VelocidadReferencia,
			Correr = Datos.Definiciones.Correr.VelocidadReferencia,
		}
		local function entrada(cambios)
			local e = {
				Velocidad = 0,
				VelocidadVertical = 0,
				EstadoHumanoid = "Running",
				EnSuelo = true,
				Sentado = false,
				Muerto = false,
			}
			for clave, valor in cambios or {} do
				e[clave] = valor
			end
			return e
		end
		local function decidir(anterior, cambios)
			return Locomocion.Decidir(anterior, entrada(cambios), a, REF)
		end

		Marco.prueba("quieto = Reposo, despacio = Andar, a la velocidad normal (16) = Correr", function()
			Marco.igual(decidir(nil, { Velocidad = 0 }), "Reposo")
			Marco.igual(decidir("Reposo", { Velocidad = 5 }), "Andar")
			Marco.igual(decidir("Andar", { Velocidad = 16 }), "Correr")
			Marco.igual(decidir(nil, { Velocidad = 16 }), "Correr")
		end)

		Marco.prueba("los umbrales tienen histéresis: no parpadea en el límite", function()
			local entreAndar = (a.PararAndar + a.EmpezarAndar) / 2
			Marco.igual(decidir("Reposo", { Velocidad = entreAndar }), "Reposo")
			Marco.igual(decidir("Andar", { Velocidad = entreAndar }), "Andar")
			local entreCorrer = (a.PararCorrer + a.EmpezarCorrer) / 2
			Marco.igual(decidir("Andar", { Velocidad = entreCorrer }), "Andar")
			Marco.igual(decidir("Correr", { Velocidad = entreCorrer }), "Correr")
			Marco.igual(decidir("Correr", { Velocidad = 0 }), "Reposo", "frenar en seco vuelve a reposo")
		end)

		Marco.prueba("el ritmo sigue a la velocidad (pies sin patinar) dentro de los límites", function()
			local _, ritmo = decidir("Andar", { Velocidad = REF.Andar * 1.3 })
			Marco.verdadero(cerca(ritmo, 1.3), `ritmo {ritmo}`)
			_, ritmo = decidir("Correr", { Velocidad = REF.Correr })
			Marco.verdadero(cerca(ritmo, 1), `ritmo {ritmo}`)
			_, ritmo = decidir("Correr", { Velocidad = 500 })
			Marco.igual(ritmo, a.RitmoMaximo)
			_, ritmo = decidir("Andar", { Velocidad = a.PararAndar })
			Marco.igual(ritmo, a.RitmoMinimo)
			_, ritmo = decidir(nil, { Velocidad = 0 })
			Marco.igual(ritmo, 1, "el reposo va a su ritmo")
		end)

		Marco.prueba("sentado, muerto, trepando o nadando no lleva animación de monstruo", function()
			Marco.esNil(decidir("Andar", { Sentado = true }))
			Marco.esNil(decidir("Correr", { Muerto = true, Velocidad = 16 }))
			for _, estado in { "Seated", "Climbing", "Swimming", "Dead", "Ragdoll", "PlatformStanding" } do
				Marco.esNil(decidir("Andar", { EstadoHumanoid = estado, Velocidad = 6 }), estado)
			end
		end)

		Marco.prueba("personaje propio: salta, cae y al aterrizar vuelve al suelo", function()
			Marco.igual(decidir("Correr", { EstadoHumanoid = "Jumping", VelocidadVertical = 40 }), "Saltar")
			Marco.igual(
				decidir("Saltar", { EstadoHumanoid = "Freefall", VelocidadVertical = 20 }),
				"Saltar",
				"sigue subiendo"
			)
			Marco.igual(
				decidir("Saltar", { EstadoHumanoid = "Freefall", VelocidadVertical = 20, SaltoTerminado = true }),
				"Caer",
				"la animación de saltar terminó"
			)
			Marco.igual(decidir("Saltar", { EstadoHumanoid = "Freefall", VelocidadVertical = -5 }), "Caer")
			Marco.igual(decidir("Reposo", { EstadoHumanoid = "Freefall", VelocidadVertical = -30 }), "Caer")
			Marco.igual(decidir("Caer", { EstadoHumanoid = "Landed", Velocidad = 0 }), "Reposo")
			Marco.igual(decidir("Caer", { EstadoHumanoid = "Running", Velocidad = 16 }), "Correr")
		end)

		Marco.prueba(
			"personaje ajeno (sin estado del Humanoid): se deduce del suelo y la velocidad vertical",
			function()
				local function ajeno(anterior, cambios)
					local e = entrada(cambios)
					e.EstadoHumanoid = nil
					return Locomocion.Decidir(anterior, e, a, REF)
				end
				Marco.igual(ajeno("Andar", { EnSuelo = false, VelocidadVertical = 40 }), "Saltar")
				Marco.igual(ajeno("Saltar", { EnSuelo = false, VelocidadVertical = 1 }), "Saltar", "en lo alto")
				Marco.igual(ajeno("Saltar", { EnSuelo = false, VelocidadVertical = -1 }), "Caer", "empieza a bajar")
				Marco.igual(ajeno("Correr", { EnSuelo = false, VelocidadVertical = -30 }), "Caer", "cae de un borde")
				Marco.igual(ajeno("Caer", { EnSuelo = true, Velocidad = 0 }), "Reposo", "aterriza")
				Marco.igual(ajeno("Caer", { EnSuelo = true, Velocidad = 7 }), "Andar")
				-- Bajando una rampa (velocidad vertical algo negativa pero con suelo): sigue en el suelo.
				Marco.igual(ajeno("Correr", { EnSuelo = true, Velocidad = 16, VelocidadVertical = -8 }), "Correr")
				-- Un tropiezo sin suelo pero casi sin velocidad vertical no cuenta como caída.
				Marco.igual(ajeno("Andar", { EnSuelo = false, VelocidadVertical = -1, Velocidad = 6 }), "Andar")
			end
		)
	end)
end
