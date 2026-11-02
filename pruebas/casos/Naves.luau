--[[
	Pruebas de la lógica pura de las naves: estadísticas por mejoras, reglas de daño/escudo/disparo/turbo,
	física del vuelo y generador de asteroides.
]]

local Entorno = require("../infraestructura/Entorno")

local function cargar(ruta: string)
	local entorno = Entorno.nuevo()
	return entorno.servidor.requerir(`ReplicatedStorage.Shared.{ruta}`), entorno
end

-- Compara números decimales con tolerancia.
local function casi(Marco, real: number, esperado: number, detalle: string?, tolerancia: number?)
	Marco.verdadero(
		math.abs(real - esperado) <= (tolerancia or 1e-6),
		`{detalle or "valor"}: se esperaba {esperado} y se obtuvo {real}`
	)
end

return function(Marco)
	local Azar = cargar("Utilidades.Azar")
	local Config = cargar("Naves.Config")
	local Mejoras = cargar("Naves.Datos.Mejoras")
	local Estadisticas = cargar("Naves.Estadisticas")
	local Reglas = cargar("Naves.Reglas")
	local Fisica = cargar("Naves.Fisica")
	local Generador = cargar("Naves.GeneradorAsteroides")
	local Esquema = Entorno.nuevo().servidor.requerir("ServerScriptService.Server.Servicios.ServicioDatos.Esquema")

	-- ===== Azar =====

	Marco.grupo("Naves: generador de números aleatorios", function()
		Marco.prueba("la misma semilla da la misma secuencia y otra semilla, otra distinta", function()
			local a, b, c = Azar.nuevo(42), Azar.nuevo(42), Azar.nuevo(43)
			local iguales, distintos = true, false
			for _ = 1, 50 do
				local x, y, z = a:Siguiente(), b:Siguiente(), c:Siguiente()
				iguales = iguales and x == y
				distintos = distintos or x ~= z
			end
			Marco.verdadero(iguales, "misma semilla")
			Marco.verdadero(distintos, "semillas distintas")
		end)

		Marco.prueba("los valores caen en el rango pedido, incluida la semilla 0", function()
			local azar = Azar.nuevo(0)
			for _ = 1, 500 do
				local n = azar:Siguiente()
				Marco.verdadero(n >= 0 and n < 1, "Siguiente fuera de [0,1)")
				local e = azar:Entero(3, 6)
				Marco.verdadero(e >= 3 and e <= 6 and e == math.floor(e), "Entero fuera de rango")
				local r = azar:Entre(-2, 5)
				Marco.verdadero(r >= -2 and r <= 5, "Entre fuera de rango")
			end
		end)

		Marco.prueba("las direcciones son unitarias", function()
			local azar = Azar.nuevo(7)
			for _ = 1, 100 do
				local x, y, z = azar:Direccion()
				casi(Marco, math.sqrt(x * x + y * y + z * z), 1, "longitud", 1e-9)
			end
		end)
	end)

	-- ===== Estadísticas =====

	Marco.grupo("Naves: estadísticas según las mejoras", function()
		Marco.prueba("las mejoras de los datos del jugador y las de la nave son las mismas", function()
			local plantilla = Esquema.Nuevo().MejorasNave
			local enDatos, enNaves = {}, {}
			for id in plantilla do
				table.insert(enDatos, id)
			end
			for id in Mejoras.Lista do
				table.insert(enNaves, id)
			end
			table.sort(enDatos)
			table.sort(enNaves)
			Marco.igualProfundo(enNaves, enDatos, "Esquema.MejorasNave y Naves/Datos/Mejoras no coinciden")
			Marco.igual(#Mejoras.Orden, #enNaves, "Orden debe nombrar todas las mejoras")
			for _, id in Mejoras.Orden do
				Marco.distinto(Mejoras.Lista[id], nil, `Orden nombra '{id}', que no existe`)
			end
		end)

		Marco.prueba("sin mejorar (nivel 0) se usan los valores base", function()
			local stats = Estadisticas.Calcular(Esquema.Nuevo().MejorasNave)
			Marco.igual(stats.VidaMax, Mejoras.Lista.Casco.Efectos.VidaMax.Base)
			Marco.igual(stats.VelocidadMax, Mejoras.Lista.Motor.Efectos.VelocidadMax.Base)
			Marco.igual(stats.Capacidad, Mejoras.Lista.Carga.Efectos.Capacidad.Base)
			for _, id in Mejoras.Orden do
				Marco.igual(stats.Niveles[id], 0)
			end
		end)

		Marco.prueba("cada mejora sube sus estadísticas (y el retraso del escudo baja)", function()
			local base = Estadisticas.Calcular({})
			local casco = Estadisticas.Calcular({ Casco = 5 })
			Marco.verdadero(casco.VidaMax > base.VidaMax, "Casco -> VidaMax")
			Marco.igual(casco.EscudoMax, base.EscudoMax, "Casco no toca el escudo")

			local escudo = Estadisticas.Calcular({ Escudo = 5 })
			Marco.verdadero(escudo.EscudoMax > base.EscudoMax, "Escudo -> EscudoMax")
			Marco.verdadero(escudo.RegenEscudo > base.RegenEscudo, "Escudo -> recarga")
			Marco.verdadero(escudo.RetrasoEscudo < base.RetrasoEscudo, "Escudo -> menos espera")

			local motor = Estadisticas.Calcular({ Motor = 5 })
			Marco.verdadero(motor.VelocidadMax > base.VelocidadMax, "Motor -> velocidad")
			Marco.verdadero(motor.Aceleracion > base.Aceleracion, "Motor -> aceleración")
			Marco.verdadero(motor.TurboMult > base.TurboMult, "Motor -> turbo")

			local armas = Estadisticas.Calcular({ Armas = 5 })
			Marco.verdadero(armas.Dano > base.Dano and armas.Cadencia > base.Cadencia, "Armas -> daño y cadencia")
			Marco.verdadero(armas.Alcance > base.Alcance, "Armas -> alcance")

			Marco.verdadero(Estadisticas.Calcular({ Escaner = 5 }).RadioEscaner > base.RadioEscaner, "Escáner")
			Marco.verdadero(Estadisticas.Calcular({ Carga = 5 }).Capacidad > base.Capacidad, "Carga")
		end)

		Marco.prueba("el retraso del escudo nunca baja de su mínimo", function()
			local stats = Estadisticas.Calcular({ Escudo = Mejoras.NivelMaximo })
			Marco.verdadero(stats.RetrasoEscudo >= Mejoras.Lista.Escudo.Efectos.RetrasoEscudo.Min :: number)
		end)

		Marco.prueba("los datos raros se corrigen: nil, negativos, decimales, NaN, texto y niveles de más", function()
			Marco.igual(Estadisticas.Calcular(nil).Niveles.Casco, 0)
			local stats = Estadisticas.Calcular({
				Casco = -4,
				Escudo = 2.9,
				Motor = 0 / 0,
				Armas = "mucho" :: any,
				Escaner = 999,
				Carga = math.huge,
			})
			Marco.igual(stats.Niveles.Casco, 0)
			Marco.igual(stats.Niveles.Escudo, 2)
			Marco.igual(stats.Niveles.Motor, 0)
			Marco.igual(stats.Niveles.Armas, 0)
			Marco.igual(stats.Niveles.Escaner, Mejoras.NivelMaximo)
			Marco.igual(stats.Niveles.Carga, Mejoras.NivelMaximo)
			for _, valor in stats do
				if type(valor) == "number" then
					Marco.verdadero(
						valor == valor and valor > -math.huge and valor < math.huge,
						"estadística no finita"
					)
				end
			end
		end)

		Marco.prueba("no se modifica la tabla de entrada y cada llamada devuelve una tabla nueva", function()
			local entrada = { Casco = 3 }
			local a = Estadisticas.Calcular(entrada)
			local b = Estadisticas.Calcular(entrada)
			Marco.distinto(a, b)
			Marco.igualProfundo(entrada, { Casco = 3 })
		end)
	end)

	-- ===== Reglas =====

	Marco.grupo("Naves: daño, escudo y choques", function()
		local stats = Estadisticas.Calcular({ Casco = 2, Escudo = 2 }) -- VidaMax 190, EscudoMax 110
		local function nueva(ahora: number)
			local estado = Reglas.NuevoEstado(stats, ahora)
			estado.InmuneHasta = 0 -- salvo en la prueba de inmunidad
			return estado
		end

		Marco.prueba("una nave nueva sale con todo lleno e inmune unos segundos", function()
			local estado = Reglas.NuevoEstado(stats, 10)
			Marco.igual(estado.Vida, stats.VidaMax)
			Marco.igual(estado.Escudo, stats.EscudoMax)
			local resultado = Reglas.AplicarDano(estado, stats, 50, 10.5)
			Marco.falso(resultado.Aplicado, "inmune")
			Marco.igual(estado.Escudo, stats.EscudoMax)
			resultado = Reglas.AplicarDano(estado, stats, 50, 10 + Config.SegundosInmunidadInicial + 0.01)
			Marco.verdadero(resultado.Aplicado, "pasada la inmunidad")
		end)

		Marco.prueba("el escudo absorbe primero y el sobrante pasa al casco", function()
			local estado = nueva(0)
			local r = Reglas.AplicarDano(estado, stats, 40, 1)
			Marco.igual(r.DanoEscudo, 40)
			Marco.igual(r.DanoCasco, 0)
			Marco.igual(estado.Vida, stats.VidaMax)
			Marco.igual(estado.Escudo, stats.EscudoMax - 40)

			r = Reglas.AplicarDano(estado, stats, stats.EscudoMax, 1) -- justo el escudo que queda + 40 de casco
			Marco.igual(r.DanoEscudo, stats.EscudoMax - 40)
			Marco.igual(r.DanoCasco, 40)
			Marco.igual(estado.Escudo, 0)
			Marco.igual(estado.Vida, stats.VidaMax - 40)
			Marco.falso(r.Destruida)
		end)

		Marco.prueba("sin escudo, el daño va directo al casco y la nave se destruye al llegar a 0", function()
			local estado = nueva(0)
			estado.Escudo = 0
			local r = Reglas.AplicarDano(estado, stats, stats.VidaMax + 500, 1)
			Marco.verdadero(r.Destruida)
			Marco.igual(estado.Vida, 0, "la vida no baja de 0")
			r = Reglas.AplicarDano(estado, stats, 10, 2)
			Marco.falso(r.Aplicado, "una nave destruida no recibe más daño")
			Marco.verdadero(r.Destruida)
		end)

		Marco.prueba("los daños inválidos se ignoran", function()
			local estado = nueva(0)
			for _, dano in { 0, -10, 0 / 0 } do
				Marco.falso(Reglas.AplicarDano(estado, stats, dano, 1).Aplicado, `daño {dano}`)
			end
			Marco.igual(estado.Escudo, stats.EscudoMax)
			Marco.igual(estado.DesdeEscudo, 0, "un daño ignorado no reinicia la recarga")
		end)

		Marco.prueba("el escudo se recarga tras la espera y a su ritmo, sin pasar del máximo", function()
			local estado = nueva(0)
			Reglas.AplicarDano(estado, stats, 60, 10)
			local restante = stats.EscudoMax - 60
			casi(Marco, Reglas.EscudoActual(estado, stats, 10), restante, "justo tras el daño")
			casi(
				Marco,
				Reglas.EscudoActual(estado, stats, 10 + stats.RetrasoEscudo - 0.1),
				restante,
				"durante la espera"
			)
			casi(
				Marco,
				Reglas.EscudoActual(estado, stats, 10 + stats.RetrasoEscudo + 2),
				restante + 2 * stats.RegenEscudo,
				"recargando"
			)
			casi(Marco, Reglas.EscudoActual(estado, stats, 10_000), stats.EscudoMax, "tope")
		end)

		Marco.prueba("recibir daño reinicia la espera de la recarga", function()
			local estado = nueva(0)
			Reglas.AplicarDano(estado, stats, 30, 10)
			Reglas.AplicarDano(estado, stats, 30, 10 + stats.RetrasoEscudo + 3) -- ya recargaba; otro golpe
			local tras = Reglas.EscudoActual(estado, stats, 10 + stats.RetrasoEscudo + 3)
			casi(
				Marco,
				Reglas.EscudoActual(estado, stats, 10 + stats.RetrasoEscudo + 3 + stats.RetrasoEscudo - 0.01),
				tras,
				"vuelve a esperar"
			)
		end)

		Marco.prueba("no se puede aterrizar justo después de recibir daño", function()
			Marco.verdadero(Reglas.PuedeAterrizar(nil, 10), "sin daño reciente")
			Marco.falso(Reglas.PuedeAterrizar(10, 10 + Config.SegundosSinDanoParaAterrizar - 0.1))
			Marco.verdadero(Reglas.PuedeAterrizar(10, 10 + Config.SegundosSinDanoParaAterrizar))
		end)

		Marco.prueba("el daño de choque crece con la velocidad y el tamaño, con mínimo y tope", function()
			Marco.igual(Reglas.DanoChoque(Config.VelocidadMinimaChoque, 12), 0, "roce lento")
			Marco.igual(Reglas.DanoChoque(0, 12), 0)
			local lento = Reglas.DanoChoque(60, 12)
			local rapido = Reglas.DanoChoque(120, 12)
			Marco.verdadero(lento > 0 and rapido > lento, "más velocidad, más daño")
			Marco.verdadero(Reglas.DanoChoque(100, 30) > Reglas.DanoChoque(100, 6), "más tamaño, más daño")
			Marco.igual(Reglas.DanoChoque(100_000, 100), Config.DanoChoqueMaximo, "tope")
			Marco.igual(Reglas.DanoChoque(0 / 0, 10), 0)
		end)
	end)

	Marco.grupo("Naves: armas", function()
		local function longitud(v)
			return math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z)
		end
		local function angulo(a, b)
			return math.deg(math.acos(math.clamp(a.X * b.X + a.Y * b.Y + a.Z * b.Z, -1, 1)))
		end
		local proa = { X = 0, Y = 0, Z = -1 }

		Marco.prueba("la cadencia limita el ritmo, con un poco de tolerancia", function()
			casi(Marco, Reglas.IntervaloDisparo(4), 0.25)
			Marco.verdadero(Reglas.PuedeDisparar(nil, 5, 4), "el primero siempre sale")
			Marco.falso(Reglas.PuedeDisparar(5, 5.1, 4), "demasiado pronto")
			Marco.verdadero(Reglas.PuedeDisparar(5, 5.22, 4), "dentro de la tolerancia")
			Marco.verdadero(Reglas.PuedeDisparar(5, 5.25, 4))
			Marco.verdadero(Reglas.IntervaloDisparo(0) < math.huge, "cadencia 0 no divide por cero")
		end)

		Marco.prueba("una dirección dentro del cono se respeta", function()
			local pedida = { X = math.sin(math.rad(10)), Y = 0, Z = -math.cos(math.rad(10)) }
			local r = Reglas.LimitarCono(proa, pedida)
			casi(Marco, r.X, pedida.X)
			casi(Marco, r.Z, pedida.Z)
		end)

		Marco.prueba("fuera del cono se recorta al borde, hacia el mismo lado", function()
			local pedida = { X = 0, Y = 1, Z = 0 } -- recto arriba: 90° de la proa
			local r = Reglas.LimitarCono(proa, pedida)
			casi(Marco, longitud(r), 1, "unitaria", 1e-9)
			casi(Marco, angulo(r, proa), Config.ConoDisparo, "justo en el borde", 1e-6)
			Marco.verdadero(r.Y > 0, "sigue apuntando hacia arriba")
			casi(Marco, r.X, 0, "sin desviarse a un lado", 1e-9)
		end)

		Marco.prueba(
			"disparar hacia atrás o con una dirección inútil sale recto, y se admiten vectores sin normalizar",
			function()
				local atras = Reglas.LimitarCono(proa, { X = 0, Y = 0, Z = 1 })
				casi(Marco, angulo(atras, proa), 0, "hacia atrás -> recto")
				local cero = Reglas.LimitarCono(proa, { X = 0, Y = 0, Z = 0 })
				casi(Marco, angulo(cero, proa), 0, "vector nulo -> recto")
				local grande = Reglas.LimitarCono({ X = 0, Y = 0, Z = -5 }, { X = 0, Y = 0, Z = -300 })
				casi(Marco, longitud(grande), 1, "se normaliza", 1e-9)
				local personal = Reglas.LimitarCono(proa, { X = 1, Y = 0, Z = -1 }, 90)
				casi(Marco, angulo(personal, proa), 45, "cono propio de 90° lo deja pasar", 1e-6)
			end
		)
	end)

	Marco.grupo("Naves: turbo y vigilancia del movimiento", function()
		local stats = Estadisticas.Calcular({ Motor = 0 }) -- EnergiaTurbo 60

		Marco.prueba("el turbo gasta energía mientras está activo y la recupera al soltarlo", function()
			local turbo = { Energia = stats.EnergiaTurbo, Desde = 0, Activo = false }
			Marco.verdadero(Reglas.CambiarTurbo(turbo, stats, true, 0))
			casi(Marco, Reglas.EnergiaTurbo(turbo, stats, 1), stats.EnergiaTurbo - Config.TurboConsumo)
			Marco.verdadero(Reglas.TurboActivo(turbo, stats, 1))
			Marco.falso(Reglas.TurboActivo(turbo, stats, 100), "se agota")
			Marco.igual(Reglas.EnergiaTurbo(turbo, stats, 100), 0)

			Reglas.CambiarTurbo(turbo, stats, false, 100)
			casi(Marco, Reglas.EnergiaTurbo(turbo, stats, 102), 2 * Config.TurboRegeneracion)
			casi(Marco, Reglas.EnergiaTurbo(turbo, stats, 10_000), stats.EnergiaTurbo, "tope")
		end)

		Marco.prueba("no se puede encender el turbo sin energía mínima", function()
			local turbo = { Energia = Config.TurboMinimo - 1, Desde = 0, Activo = false }
			Marco.falso(Reglas.CambiarTurbo(turbo, stats, true, 0))
			Marco.falso(turbo.Activo)
			Marco.verdadero(Reglas.CambiarTurbo(turbo, stats, true, 5), "tras recuperar algo, sí")
		end)

		Marco.prueba("la velocidad tope sube con el turbo", function()
			Marco.igual(Reglas.VelocidadTope(stats, false), stats.VelocidadMax)
			Marco.igual(Reglas.VelocidadTope(stats, true), stats.VelocidadMax * stats.TurboMult)
		end)

		Marco.prueba("un movimiento creíble se acepta y un salto de posición no", function()
			local tope = 100
			Marco.verdadero(Reglas.MovimientoValido(20, 0.2, tope), "a velocidad normal")
			Marco.verdadero(Reglas.MovimientoValido(0, 0.2, tope), "parada")
			Marco.falso(Reglas.MovimientoValido(300, 0.2, tope), "teletransporte")
			Marco.falso(Reglas.MovimientoValido(1, 0.2, 0 / 0), "NaN en el tope")
			Marco.falso(Reglas.MovimientoValido(0 / 0, 0.2, tope), "NaN en la distancia")
		end)

		Marco.prueba("una pausa larga no regala un margen ilimitado", function()
			local maximo = 100 * Config.HolguraVelocidad * Config.DtMaximo + Config.MargenPosicion
			Marco.verdadero(Reglas.MovimientoValido(maximo - 1, 3600, 100))
			Marco.falso(Reglas.MovimientoValido(maximo + 1, 3600, 100))
		end)

		Marco.prueba("el mundo jugable es una esfera alrededor del origen", function()
			Marco.verdadero(Reglas.DentroDelMundo({ X = 0, Y = 0, Z = 0 }))
			Marco.verdadero(Reglas.DentroDelMundo({ X = Config.RadioMundo - 1, Y = 0, Z = 0 }))
			Marco.falso(Reglas.DentroDelMundo({ X = 0, Y = Config.RadioMundo + 1, Z = 0 }))
		end)
	end)

	-- ===== Física =====

	Marco.grupo("Naves: física del vuelo", function()
		local function modulo(x, y, z)
			return math.sqrt(x * x + y * y + z * z)
		end

		Marco.prueba("la zona muerta anula lo pequeño y reescala el resto", function()
			Marco.igual(Fisica.ZonaMuerta(0.1, 0.2), 0)
			Marco.igual(Fisica.ZonaMuerta(-0.2, 0.2), 0)
			casi(Marco, Fisica.ZonaMuerta(1, 0.2), 1)
			casi(Marco, Fisica.ZonaMuerta(-1, 0.2), -1)
			casi(Marco, Fisica.ZonaMuerta(0.6, 0.2), 0.5)
		end)

		Marco.prueba("el giro está limitado por segundo, la guiñada da la vuelta y el cabeceo tiene tope", function()
			local g, c = Fisica.Girar(0, 0, 100, 100, 0.1)
			casi(Marco, g, Config.GiroMaximo * 0.1)
			casi(Marco, c, Config.GiroMaximo * 0.1)

			g = Fisica.Girar(math.pi - 0.01, 0, 1, 0, 1)
			Marco.verdadero(g < 0 and g >= -math.pi, "da la vuelta completa")

			local _, cabeceo = 0, 0
			for _ = 1, 200 do
				_, cabeceo = Fisica.Girar(0, cabeceo, 0, 1, 0.1)
			end
			casi(Marco, cabeceo, Config.CabeceoMaximo, "tope de cabeceo")
		end)

		Marco.prueba("el alabeo se inclina hacia el lado del giro y vuelve a cero sin él", function()
			local derecha = 0
			for _ = 1, 60 do
				derecha = Fisica.Alabeo(derecha, 2, 0, 1 / 60)
			end
			Marco.verdadero(derecha > 0, "girando a la izquierda (guiñada +) se inclina a la izquierda (alabeo +)")
			Marco.verdadero(
				Fisica.Alabeo(0, 0, 1, 1) < 0,
				"desplazándose a la derecha se inclina a la derecha (alabeo -)"
			)
			for _ = 1, 240 do
				derecha = Fisica.Alabeo(derecha, 0, 0, 1 / 60)
			end
			casi(Marco, derecha, 0, "se endereza", 0.01)
			Marco.verdadero(math.abs(Fisica.Alabeo(0, 100, 1, 10)) <= math.rad(55) + 1e-9, "tope de inclinación")
		end)

		Marco.prueba("la velocidad objetivo avanza por -Z y nunca supera la máxima", function()
			local x, y, z =
				Fisica.VelocidadObjetivo({ Adelante = 1, Lateral = 0, Vertical = 0, Turbo = false }, 100, 1.5)
			casi(Marco, x, 0)
			casi(Marco, y, 0)
			casi(Marco, z, -100)

			x, y, z = Fisica.VelocidadObjetivo({ Adelante = 1, Lateral = 1, Vertical = 1, Turbo = false }, 100, 1.5)
			casi(Marco, modulo(x, y, z), 100, "la diagonal se recorta", 1e-6)

			x, y, z = Fisica.VelocidadObjetivo({ Adelante = -1, Lateral = 0, Vertical = 0, Turbo = false }, 100, 1.5)
			casi(Marco, z, 100 * Config.FraccionMarchaAtras, "marcha atrás más lenta")

			x, y, z = Fisica.VelocidadObjetivo({ Adelante = 0, Lateral = 1, Vertical = 0, Turbo = false }, 100, 1.5)
			casi(Marco, x, 100 * Config.FraccionLateral, "lateral más lento")

			x, y, z = Fisica.VelocidadObjetivo({ Adelante = 50, Lateral = -9, Vertical = 0, Turbo = false }, 100, 1.5)
			Marco.verdadero(modulo(x, y, z) <= 100 + 1e-6, "una entrada fuera de rango se recorta")
		end)

		Marco.prueba("el turbo multiplica la velocidad y empuja aunque no se pulse avanzar", function()
			local _, _, z =
				Fisica.VelocidadObjetivo({ Adelante = 0, Lateral = 0, Vertical = 0, Turbo = true }, 100, 1.5)
			casi(Marco, z, -150)
		end)

		Marco.prueba("la velocidad se acerca a la objetivo sin pasarse, con inercia", function()
			local x, y, z = Fisica.AcercarVelocidad(0, 0, 0, 0, 0, -100, 30)
			casi(Marco, modulo(x, y, z), 30, "un paso", 1e-6)
			casi(Marco, z, -30)
			x, y, z = Fisica.AcercarVelocidad(0, 0, -90, 0, 0, -100, 30)
			casi(Marco, z, -100, "llega y se para")
			x, y, z = Fisica.AcercarVelocidad(5, 5, 5, 5, 5, 5, 30)
			casi(Marco, modulo(x, y, z), modulo(5, 5, 5), "ya en el objetivo")
		end)

		Marco.prueba("sin órdenes el estabilizador frena más deprisa de lo que acelera", function()
			Marco.verdadero(Fisica.Aceleracion(50, false) > Fisica.Aceleracion(50, true))
			Marco.igual(Fisica.Aceleracion(50, true), 50)
		end)

		Marco.prueba("el rebote refleja la parte que va contra la superficie y deja una salida mínima", function()
			local vx, vy, vz = Fisica.Rebote(0, 0, -100, 0, 0, 1, 0.5)
			casi(Marco, vz, 50, "rebota a la mitad")
			vx, vy, vz = Fisica.Rebote(30, 0, -100, 0, 0, 1, 0)
			casi(Marco, vx, 30, "lo tangencial se conserva")
			casi(Marco, vz, Config.ImpulsoSeparacion, "pero sale despedida con un mínimo")
			vx, vy, vz = Fisica.Rebote(0, 0, 40, 0, 0, 1, 0.5)
			casi(Marco, vz, 40, "si ya se aleja, no cambia")
		end)
	end)

	-- ===== Generador de asteroides =====

	Marco.grupo("Naves: generador de campos de asteroides", function()
		local opciones = {
			Semilla = 2024,
			Cantidad = 60,
			Centro = { X = 100, Y = 50, Z = -300 },
			Radio = 220,
		}

		local function distancia(a, b)
			return math.sqrt((a.X - b.X) ^ 2 + (a.Y - b.Y) ^ 2 + (a.Z - b.Z) ^ 2)
		end

		Marco.prueba("con la misma semilla sale el mismo campo, y con otra, uno distinto", function()
			local a = Generador.Generar(opciones)
			local b = Generador.Generar(opciones)
			Marco.igualProfundo(a, b)
			local otra = table.clone(opciones)
			otra.Semilla = 99
			Marco.distinto(Generador.Generar(otra)[1].Posicion.X, a[1].Posicion.X)
		end)

		Marco.prueba("coloca la cantidad pedida dentro de la región", function()
			local campo = Generador.Generar(opciones)
			Marco.igual(#campo, opciones.Cantidad)
			for _, asteroide in campo do
				Marco.verdadero(
					distancia(asteroide.Posicion, opciones.Centro) <= opciones.Radio + 1e-6,
					"fuera de la región"
				)
			end
		end)

		Marco.prueba("los asteroides no se solapan y dejan hueco para pasar", function()
			local campo = Generador.Generar(opciones)
			for i = 1, #campo do
				for j = i + 1, #campo do
					local a, b = campo[i], campo[j]
					local huecoMinimo = (a.Tamano + b.Tamano) * 0.5 * 1.35 + 10
					Marco.verdadero(
						distancia(a.Posicion, b.Posicion) >= huecoMinimo - 1e-6,
						`los asteroides {i} y {j} están demasiado juntos`
					)
				end
			end
		end)

		Marco.prueba("respeta las zonas de exclusión", function()
			local zona = { Centro = { X = 100, Y = 50, Z = -300 }, Radio = 90 }
			local con = table.clone(opciones)
			con.Exclusiones = { zona }
			for _, asteroide in Generador.Generar(con) do
				Marco.verdadero(distancia(asteroide.Posicion, zona.Centro) >= zona.Radio, "dentro de la zona excluida")
			end
		end)

		Marco.prueba("hay muchos más pequeños que grandes, dentro de los tamaños pedidos", function()
			local campo = Generador.Generar({
				Semilla = 5,
				Cantidad = 150,
				Centro = { X = 0, Y = 0, Z = 0 },
				Radio = 900,
				TamanoMin = 5,
				TamanoMax = 28,
			})
			local pequenos = 0
			for _, asteroide in campo do
				Marco.verdadero(asteroide.Tamano >= 5 and asteroide.Tamano <= 28, "tamaño fuera de rango")
				if asteroide.Tamano < 16.5 then
					pequenos += 1
				end
			end
			Marco.verdadero(pequenos > #campo * 0.6, `solo {pequenos} de {#campo} son pequeños`)
		end)

		Marco.prueba("cada asteroide tiene vida proporcional, fragmentos y material válidos", function()
			for _, asteroide in Generador.Generar(opciones) do
				Marco.verdadero(asteroide.Vida >= 1, "vida")
				Marco.igual(asteroide.Vida, Generador.VidaPara(asteroide.Tamano))
				Marco.verdadero(asteroide.Material == "Roca" or asteroide.Material == "Basalto", "material")
				Marco.verdadero(asteroide.Tono >= 0 and asteroide.Tono <= 1, "tono")
				Marco.verdadero(#asteroide.Fragmentos >= 2 and #asteroide.Fragmentos <= 4, "fragmentos")
				for _, fragmento in asteroide.Fragmentos do
					Marco.verdadero(fragmento.Forma == "Bloque" or fragmento.Forma == "Esfera", "forma")
				end
			end
		end)

		Marco.prueba("un cinturón aplanado reparte los asteroides cerca de su plano", function()
			local disco = table.clone(opciones)
			disco.Aplanado = 0.1
			for _, asteroide in Generador.Generar(disco) do
				Marco.verdadero(math.abs(asteroide.Posicion.Y - opciones.Centro.Y) <= opciones.Radio * 0.1 + 1e-6)
			end
		end)

		Marco.prueba("si no cabe todo termina igualmente, con los que haya colocado", function()
			local campo = Generador.Generar({
				Semilla = 1,
				Cantidad = 400,
				Centro = { X = 0, Y = 0, Z = 0 },
				Radio = 40,
				TamanoMin = 20,
				TamanoMax = 28,
			})
			Marco.verdadero(#campo < 400 and #campo >= 1)
		end)
	end)
end
