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
