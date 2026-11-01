--[[
	Pruebas de las reglas del combate (Combate/Reglas), de los datos de poderes y de los remotos de combate.
]]

local Entorno = require("../infraestructura/Entorno")

local function cargar(ruta: string)
	local entorno = Entorno.nuevo()
	return entorno.servidor.requerir(`ReplicatedStorage.Shared.{ruta}`), entorno
end

local function punto(x: number, y: number, z: number)
	return { X = x, Y = y, Z = z }
end

return function(Marco)
	local Reglas = cargar("Combate.Reglas")
	local Poderes = cargar("Combate.Datos.Poderes")
	local Config = cargar("Combate.Config")

	Marco.grupo("Combate: estado, cooldown y energía", function()
		Marco.prueba("un luchador vivo y libre puede actuar", function()
			local ok = Reglas.PuedeActuar({ Vivo = true, AturdidoHasta = 0, OcupadoHasta = 0 }, 10)
			Marco.verdadero(ok)
		end)

		Marco.prueba("muerto, aturdido u ocupado no puede actuar, y se indica el motivo", function()
			local ok, motivo = Reglas.PuedeActuar({ Vivo = false, AturdidoHasta = 0, OcupadoHasta = 0 }, 10)
			Marco.falso(ok)
			Marco.igual(motivo, "muerto")

			ok, motivo = Reglas.PuedeActuar({ Vivo = true, AturdidoHasta = 12, OcupadoHasta = 0 }, 10)
			Marco.falso(ok)
			Marco.igual(motivo, "aturdido")

			ok, motivo = Reglas.PuedeActuar({ Vivo = true, AturdidoHasta = 0, OcupadoHasta = 11 }, 10)
			Marco.falso(ok)
			Marco.igual(motivo, "ocupado")

			ok = Reglas.PuedeActuar({ Vivo = true, AturdidoHasta = 12, OcupadoHasta = 11 }, 12)
			Marco.verdadero(ok, "justo cuando terminan el aturdimiento y la ocupación ya puede actuar")
		end)

		Marco.prueba("el cooldown solo está listo cuando ha pasado su fin", function()
			Marco.verdadero(Reglas.CooldownListo(nil, 5), "nunca usada")
			Marco.falso(Reglas.CooldownListo(8, 5))
			Marco.verdadero(Reglas.CooldownListo(8, 8))
			Marco.igual(Reglas.CooldownRestante(8, 5), 3)
			Marco.igual(Reglas.CooldownRestante(8, 9), 0)
			Marco.igual(Reglas.CooldownRestante(nil, 9), 0)
		end)

		Marco.prueba("la energía se regenera con el tiempo sin pasar del máximo", function()
			Marco.igual(Reglas.EnergiaActual(10, 100, 5, 0, 4), 30)
			Marco.igual(Reglas.EnergiaActual(95, 100, 5, 0, 4), 100)
			Marco.igual(Reglas.EnergiaActual(10, 100, 5, 4, 0), 10, "el tiempo no retrocede")
		end)

		Marco.prueba("TieneEnergia compara con el coste", function()
			Marco.verdadero(Reglas.TieneEnergia(8, 8))
			Marco.falso(Reglas.TieneEnergia(7.9, 8))
		end)
	end)

	Marco.grupo("Combate: alcance y bandos", function()
		Marco.prueba("se acepta una distancia dentro del rango y se rechaza una exagerada", function()
			local ok, d = Reglas.AjustarAlcance(40, 50)
			Marco.verdadero(ok)
			Marco.igual(d, 40)

			ok, d = Reglas.AjustarAlcance(55, 50)
			Marco.verdadero(ok, "dentro de la holgura")
			Marco.igual(d, 50, "se recorta al rango real")

			ok = Reglas.AjustarAlcance(80, 50)
			Marco.falso(ok)
			ok = Reglas.AjustarAlcance(-1, 50)
			Marco.falso(ok)
			ok = Reglas.AjustarAlcance(0 / 0, 50)
			Marco.falso(ok, "NaN")
		end)

		Marco.prueba("la pendiente se limita", function()
			Marco.igual(Reglas.LimitarPendiente(0.9), Config.PendienteMaxima)
			Marco.igual(Reglas.LimitarPendiente(-0.9), -Config.PendienteMaxima)
			Marco.igual(Reglas.LimitarPendiente(0.1), 0.1)
		end)

		Marco.prueba("los del mismo bando no se hacen daño", function()
			Marco.falso(Reglas.SonEnemigos("Heroes", "Heroes"))
			Marco.falso(Reglas.SonEnemigos("Villanos", "Villanos"))
			Marco.verdadero(Reglas.SonEnemigos("Heroes", "Villanos"))
			Marco.verdadero(Reglas.SonEnemigos("Villanos", "Heroes"))
		end)

		Marco.prueba("quien no tiene bando puede dañar y ser dañado por todos", function()
			Marco.verdadero(Reglas.SonEnemigos("Ninguno", "Heroes"))
			Marco.verdadero(Reglas.SonEnemigos("Villanos", "Ninguno"))
			Marco.verdadero(Reglas.SonEnemigos("Ninguno", "Ninguno"))
		end)
	end)

	Marco.grupo("Combate: combo", function()
		Marco.prueba("encadenar a tiempo sube de golpe; pasada la ventana vuelve al primero", function()
			Marco.igual(Reglas.PasoDeCombo(0, 0, 10, 0.7, 4), 1)
			Marco.igual(Reglas.PasoDeCombo(1, 10, 10.3, 0.7, 4), 2)
			Marco.igual(Reglas.PasoDeCombo(2, 10, 10.7, 0.7, 4), 3)
			Marco.igual(Reglas.PasoDeCombo(2, 10, 11, 0.7, 4), 1, "tarde")
		end)

		Marco.prueba("tras el cuarto golpe se reinicia", function()
			Marco.igual(Reglas.PasoDeCombo(4, 10, 10.1, 0.7, 4), 1)
		end)
	end)

	Marco.grupo("Combate: geometría de los golpes", function()
		local origen = punto(0, 0, 0)
		local dir = punto(0, 0, -1)

		Marco.prueba("la distancia a un segmento", function()
			Marco.igual(Reglas.DistanciaASegmento(punto(3, 0, -5), origen, punto(0, 0, -10)), 3)
			Marco.igual(Reglas.DistanciaASegmento(punto(0, 0, 4), origen, punto(0, 0, -10)), 4, "antes del inicio")
			Marco.igual(Reglas.DistanciaASegmento(punto(0, 0, -13), origen, punto(0, 0, -10)), 3, "tras el final")
			Marco.igual(Reglas.DistanciaASegmento(punto(3, 4, 0), origen, origen), 5, "segmento de largo 0")
		end)

		Marco.prueba("Linea: golpea a lo que queda a lo largo del haz y no a lo que queda al lado", function()
			local golpe = {
				Forma = "Linea",
				Origen = origen,
				Destino = punto(0, 0, -50),
				Direccion = dir,
				Rango = 50,
				Radio = 3,
			}
			Marco.verdadero(Reglas.EnForma(golpe, punto(1, 0, -30)))
			Marco.verdadero(Reglas.EnForma(golpe, punto(5, 0, -30)), "radio 3 + cuerpo 2.5")
			Marco.falso(Reglas.EnForma(golpe, punto(9, 0, -30)))
			Marco.falso(Reglas.EnForma(golpe, punto(0, 0, -70)), "pasado el final")
			Marco.falso(Reglas.EnForma(golpe, punto(0, 0, 20)), "detrás del lanzador")
		end)

		Marco.prueba("Area: golpea dentro del radio alrededor del destino", function()
			local golpe = {
				Forma = "Area",
				Origen = origen,
				Destino = punto(0, 0, -40),
				Direccion = dir,
				Rango = 50,
				Radio = 14,
			}
			Marco.verdadero(Reglas.EnForma(golpe, punto(10, 0, -40)))
			Marco.falso(Reglas.EnForma(golpe, punto(20, 0, -40)))
			Marco.falso(Reglas.EnForma(golpe, origen), "el lanzador está lejos del destino")
		end)

		Marco.prueba("Circulo: alrededor del lanzador", function()
			local golpe = {
				Forma = "Circulo",
				Origen = origen,
				Destino = punto(0, 0, -40),
				Direccion = dir,
				Rango = 10,
				Radio = 10,
			}
			Marco.verdadero(Reglas.EnForma(golpe, punto(8, 0, 4)))
			Marco.falso(Reglas.EnForma(golpe, punto(20, 0, 0)))
		end)

		Marco.prueba("Cono: golpea delante, no detrás ni fuera del ángulo", function()
			local golpe = {
				Forma = "Cono",
				Origen = origen,
				Destino = punto(0, 0, -7),
				Direccion = dir,
				Rango = 7,
				Radio = 7,
				Angulo = 90,
			}
			Marco.verdadero(Reglas.EnForma(golpe, punto(0, 0, -6)))
			Marco.verdadero(Reglas.EnForma(golpe, punto(3, 0, -5)), "dentro de ±45°")
			Marco.falso(Reglas.EnForma(golpe, punto(8, 0, -2)), "fuera del ángulo")
			Marco.falso(Reglas.EnForma(golpe, punto(0, 0, 6)), "detrás")
			Marco.falso(Reglas.EnForma(golpe, punto(0, 0, -20)), "demasiado lejos")
			Marco.verdadero(Reglas.EnForma(golpe, punto(0, 0, 1)), "pegado al lanzador")
		end)

		Marco.prueba("una forma desconocida no golpea a nadie", function()
			Marco.falso(Reglas.EnForma({
				Forma = "Rara",
				Origen = origen,
				Destino = origen,
				Direccion = dir,
				Rango = 10,
				Radio = 10,
			}, origen))
		end)

		Marco.prueba("AlAlcance compara con la distancia máxima", function()
			Marco.verdadero(Reglas.AlAlcance(punto(3, 4, 0), origen, 5))
			Marco.falso(Reglas.AlAlcance(punto(3, 4, 0), origen, 4.9))
		end)

		Marco.prueba("la vida nunca baja de cero ni sube por un daño negativo", function()
			Marco.igual(Reglas.VidaTrasDano(100, 30), 70)
			Marco.igual(Reglas.VidaTrasDano(10, 30), 0)
			Marco.igual(Reglas.VidaTrasDano(100, -50), 100)
		end)
	end)

	Marco.grupo("Combate: árbitro (petición de habilidad)", function()
		local Arbitro = cargar("Combate.Arbitro")

		-- Luchador nuevo en el instante 100.
		local function nuevo()
			return Arbitro.NuevoLuchador(100)
		end

		Marco.prueba(
			"una petición correcta se acepta y se cobra la energía, el cooldown y el tiempo ocupado",
			function()
				local l = nuevo()
				local r = Arbitro.Evaluar(l, "Rayo_Basico", 100, 40)
				Marco.verdadero(r.Ok)
				Marco.igual(r.Habilidad.Id, "Rayo_Basico")
				Marco.igual(r.Distancia, 40)

				local duracion = Arbitro.Aplicar(l, "Rayo_Basico", r, 100)
				local hab = Poderes.Habilidades.Rayo_Basico
				Marco.igual(l.Energia, Config.EnergiaMaxima - hab.Energia)
				Marco.igual(l.Cooldowns.Rayo_Basico, 100 + hab.Cooldown)
				Marco.igual(l.Estado.OcupadoHasta, 100 + duracion)
			end
		)

		Marco.prueba("no se puede repetir la habilidad mientras dura el cooldown", function()
			local l = nuevo()
			local r = Arbitro.Evaluar(l, "Rayo_Fuerte", 100, 30)
			Arbitro.Aplicar(l, "Rayo_Fuerte", r, 100)
			l.Estado.OcupadoHasta = 0 -- ya no está ocupado, pero el cooldown sigue

			r = Arbitro.Evaluar(l, "Rayo_Fuerte", 101, 30)
			Marco.falso(r.Ok)
			Marco.igual(r.Motivo, "cooldown")

			r = Arbitro.Evaluar(l, "Rayo_Fuerte", 100 + Poderes.Habilidades.Rayo_Fuerte.Cooldown, 30)
			Marco.verdadero(r.Ok, "al terminar el cooldown vuelve a poder")
		end)

		Marco.prueba("los cooldowns de habilidades distintas son independientes", function()
			local l = nuevo()
			Arbitro.Aplicar(l, "Rayo_Basico", Arbitro.Evaluar(l, "Rayo_Basico", 100, 30), 100)
			l.Estado.OcupadoHasta = 0
			Marco.verdadero(Arbitro.Evaluar(l, "Gravedad_Basico", 100, 30).Ok)
		end)

		Marco.prueba("sin energía suficiente se rechaza, y la energía se regenera con el tiempo", function()
			local l = nuevo()
			l.Energia = 5
			local r = Arbitro.Evaluar(l, "Rayo_Basico", 100, 30)
			Marco.falso(r.Ok)
			Marco.igual(r.Motivo, "energia")

			-- Coste 8: faltan 3 puntos; con 7 por segundo tarda menos de un segundo.
			r = Arbitro.Evaluar(l, "Rayo_Basico", 101, 30)
			Marco.verdadero(r.Ok)
		end)

		Marco.prueba("una distancia fuera de alcance se rechaza; ligeramente excedida se recorta", function()
			local l = nuevo()
			local rango = Poderes.Habilidades.Rayo_Fuerte.Rango
			local r = Arbitro.Evaluar(l, "Rayo_Fuerte", 100, rango * 3)
			Marco.falso(r.Ok)
			Marco.igual(r.Motivo, "distancia")

			r = Arbitro.Evaluar(l, "Rayo_Fuerte", 100, rango * 1.1)
			Marco.verdadero(r.Ok)
			Marco.igual(r.Distancia, rango)
		end)

		Marco.prueba("muerto, aturdido u ocupado no puede lanzar nada", function()
			local l = nuevo()
			l.Estado.Vivo = false
			Marco.igual(Arbitro.Evaluar(l, "Rayo_Basico", 100, 30).Motivo, "muerto")
			l.Estado.Vivo = true
			l.Estado.AturdidoHasta = 105
			Marco.igual(Arbitro.Evaluar(l, "Rayo_Basico", 100, 30).Motivo, "aturdido")
			l.Estado.AturdidoHasta = 0
			l.Estado.OcupadoHasta = 105
			Marco.igual(Arbitro.Evaluar(l, "Rayo_Basico", 100, 30).Motivo, "ocupado")
		end)

		Marco.prueba("una habilidad inexistente se rechaza", function()
			Marco.igual(Arbitro.Evaluar(nuevo(), "Inventada", 100, 5).Motivo, "desconocida")
			Marco.igual(Arbitro.Evaluar(nuevo(), "Combo2", 100, 5).Habilidad, nil, "Combo2 no es un id pedible")
		end)

		Marco.prueba("evaluar no modifica el estado", function()
			local l = nuevo()
			Arbitro.Evaluar(l, "Rayo_Basico", 100, 30)
			Marco.igual(l.Energia, Config.EnergiaMaxima)
			Marco.igual(next(l.Cooldowns), nil)
			Marco.igual(l.Estado.OcupadoHasta, 0)
		end)

		Marco.prueba("la definitiva hace invulnerable al lanzador mientras dura", function()
			local l = nuevo()
			local r = Arbitro.Evaluar(l, "Rayo_Definitiva", 100, 50)
			Marco.verdadero(r.Ok)
			local duracion = Arbitro.Aplicar(l, "Rayo_Definitiva", r, 100)
			Marco.igual(l.InvulnerableHasta, 100 + duracion)
			Marco.falso(Arbitro.PuedeSerGolpeado("Villanos", "Heroes", l, 101))
			Marco.verdadero(Arbitro.PuedeSerGolpeado("Villanos", "Heroes", l, 100 + duracion))
		end)

		Marco.prueba("el combo avanza golpe a golpe, se reinicia tarde y tras el cuarto", function()
			local l = nuevo()
			local ahora = 100
			local vistos = {}
			for _ = 1, 4 do
				local r = Arbitro.Evaluar(l, "Combo", ahora, 0)
				Marco.verdadero(r.Ok, "el golpe se acepta")
				table.insert(vistos, r.Habilidad.Id)
				Arbitro.Aplicar(l, "Combo", r, ahora)
				ahora = l.Cooldowns.Combo + 0.1 -- se encadena justo después del cooldown
				l.Estado.OcupadoHasta = 0
			end
			Marco.igualProfundo(vistos, { "Combo1", "Combo2", "Combo3", "Combo4" })

			-- Tras el cuarto golpe, el siguiente vuelve a ser el primero.
			local r = Arbitro.Evaluar(l, "Combo", ahora, 0)
			Marco.igual(r.Habilidad.Id, "Combo1")
			Arbitro.Aplicar(l, "Combo", r, ahora)

			-- Si se deja pasar la ventana, vuelve a empezar.
			l.Estado.OcupadoHasta = 0
			r = Arbitro.Evaluar(l, "Combo", l.Cooldowns.Combo + 5, 0)
			Marco.igual(r.Habilidad.Id, "Combo1")
		end)

		Marco.prueba("el combo respeta el cooldown entre golpes", function()
			local l = nuevo()
			Arbitro.Aplicar(l, "Combo", Arbitro.Evaluar(l, "Combo", 100, 0), 100)
			l.Estado.OcupadoHasta = 0
			Marco.igual(Arbitro.Evaluar(l, "Combo", 100.05, 0).Motivo, "cooldown")
		end)

		Marco.prueba("fuego amistoso: el mismo bando no se golpea; sin bando y bandos distintos, sí", function()
			local objetivo = nuevo()
			Marco.falso(Arbitro.PuedeSerGolpeado("Heroes", "Heroes", objetivo, 100))
			Marco.verdadero(Arbitro.PuedeSerGolpeado("Heroes", "Villanos", objetivo, 100))
			Marco.verdadero(Arbitro.PuedeSerGolpeado("Ninguno", "Heroes", objetivo, 100))
			objetivo.Estado.Vivo = false
			Marco.falso(Arbitro.PuedeSerGolpeado("Heroes", "Villanos", objetivo, 100), "un muerto no se golpea")
		end)
	end)

	Marco.grupo("Combate: datos de las habilidades", function()
		Marco.prueba("las habilidades pedibles existen y 'Combo' se resuelve a sus 4 golpes", function()
			for _, id in Poderes.Solicitables do
				Marco.distinto(Poderes.Presentacion(id), nil, `falta la habilidad {id}`)
			end
			for paso = 1, Poderes.GolpesCombo do
				local golpe = Poderes.Obtener(`Combo{paso}`)
				Marco.distinto(golpe, nil, `falta Combo{paso}`)
				Marco.igual(golpe.Combo.Paso, paso)
				Marco.igual(golpe.Combo.Total, Poderes.GolpesCombo)
			end
		end)

		Marco.prueba("los golpes del combo internos no se pueden pedir por red", function()
			for _, id in Poderes.Solicitables do
				Marco.falso(string.match(id, "^Combo%d") ~= nil, `{id} no debería ser pedible`)
			end
		end)

		Marco.prueba("cada habilidad tiene valores coherentes", function()
			for id, hab in Poderes.Habilidades do
				Marco.igual(hab.Id, id)
				Marco.verdadero(hab.Dano > 0, `{id}: daño`)
				Marco.verdadero(hab.Cooldown > 0, `{id}: cooldown`)
				Marco.verdadero(hab.Rango > 0 and hab.Radio > 0, `{id}: alcance`)
				Marco.verdadero(hab.Tiempos.Carga >= 0 and hab.Tiempos.Viaje >= 0, `{id}: tiempos`)
				Marco.verdadero(hab.Energia >= 0, `{id}: energía`)
				Marco.verdadero(
					hab.Forma == "Linea" or hab.Forma == "Area" or hab.Forma == "Cono" or hab.Forma == "Circulo",
					`{id}: forma desconocida {hab.Forma}`
				)
				if hab.Forma == "Cono" then
					Marco.distinto(hab.Angulo, nil, `{id}: un cono necesita ángulo`)
				end
				Marco.verdadero(hab.Energia <= Config.EnergiaMaxima, `{id}: cuesta más que la energía máxima`)
			end
		end)

		Marco.prueba("cada poder tiene básico, fuerte y definitiva; la definitiva tiene cinemática", function()
			for _, poder in { "Rayo", "Gravedad" } do
				local categorias = {}
				for _, hab in Poderes.Habilidades do
					if hab.Poder == poder then
						categorias[hab.Categoria] = hab
					end
				end
				Marco.distinto(categorias.Basico, nil, `{poder}: falta el básico`)
				Marco.distinto(categorias.Fuerte, nil, `{poder}: falta el fuerte`)
				Marco.distinto(categorias.Definitiva, nil, `{poder}: falta la definitiva`)
				Marco.distinto(categorias.Definitiva.Cinematica, nil, `{poder}: la definitiva necesita cinemática`)
			end
		end)

		Marco.prueba("los datos están congelados", function()
			Marco.verdadero(table.isfrozen(Poderes.Habilidades.Rayo_Basico))
			Marco.lanzaError(function()
				Poderes.Habilidades.Rayo_Basico.Dano = 9999
			end)
		end)
	end)

	Marco.grupo("Combate: remotos", function()
		Marco.prueba("UsarHabilidad solo acepta ids conocidos, direcciones razonables y distancias finitas", function()
			local Remotos = cargar("Red.Remotos")
			local Validador = cargar("Red.Validador")
			local def = Remotos.Definiciones.UsarHabilidad
			local entorno = Entorno.nuevo()
			local V3 = entorno.mundo.Vector3
			local v3 = V3.new

			local function acepta(...)
				return (Validador.ValidarArgumentos(def.Argumentos, ...))
			end

			Marco.verdadero(acepta("Rayo_Basico", v3(0, 0, -1), 30))
			Marco.verdadero(acepta("Combo", v3(0, 0, 0), 0))
			Marco.falso(acepta("Combo1", v3(0, 0, -1), 5), "los golpes internos no son pedibles")
			Marco.falso(acepta("Inventada", v3(0, 0, -1), 5))
			Marco.falso(acepta("Rayo_Basico", v3(0, 0, -9), 5), "dirección gigante")
			Marco.falso(acepta("Rayo_Basico", v3(0, 0, -1), 1e9), "distancia enorme")
			Marco.falso(acepta("Rayo_Basico", v3(0, 0, -1), -1), "distancia negativa")
			Marco.falso(acepta("Rayo_Basico", v3(0, 0, -1), 0 / 0), "NaN")
			Marco.falso(acepta("Rayo_Basico", v3(0, 0, -1)), "falta un argumento")
		end)
	end)
end
