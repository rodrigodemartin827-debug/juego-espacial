--[[
	Pruebas de Esquema: la plantilla de datos de un jugador nuevo, la conciliación (rellenar y reparar
	datos) y las migraciones entre versiones.
]]

local Entorno = require("../infraestructura/Entorno")
local NubeDatos = require("../infraestructura/NubeDatos")

local function cargarEsquema()
	return Entorno.nuevo().servidor.requerir("ServerScriptService.Server.Servicios.ServicioDatos.Esquema")
end

-- Comprueba que un DataStore real aceptaría guardar `datos` (lanza error si no).
local function comprobarGuardable(datos)
	NubeDatos.nueva():Escribir("almacen", "clave", datos)
end

return function(Marco)
	Marco.grupo("Esquema.Nuevo", function()
		Marco.prueba("devuelve los datos de un jugador nuevo", function()
			local Esquema = cargarEsquema()
			local datos = Esquema.Nuevo()

			Marco.igual(datos.Bando, "Ninguno")
			Marco.igual(datos.Nivel, 1)
			Marco.igual(datos.XP, 0)
			Marco.igual(datos.Monedas, 0)
			Marco.igualProfundo(datos.Inventario, {})
			for _, mejora in { "Casco", "Escudo", "Motor", "Armas", "Escaner", "Carga" } do
				Marco.igual(datos.MejorasNave[mejora], 0, `la mejora {mejora} debe empezar en 0`)
			end
		end)

		Marco.prueba("cada llamada devuelve una copia independiente de la plantilla", function()
			local Esquema = cargarEsquema()
			local primera = Esquema.Nuevo()
			primera.Monedas = 999
			primera.Inventario.hierro = 5
			primera.MejorasNave.Casco = 3

			local segunda = Esquema.Nuevo()
			Marco.igual(segunda.Monedas, 0)
			Marco.esNil(segunda.Inventario.hierro)
			Marco.igual(segunda.MejorasNave.Casco, 0)
		end)

		Marco.prueba("los datos nuevos ya cumplen el esquema y se pueden guardar", function()
			local Esquema = cargarEsquema()
			local datos, reparaciones = Esquema.Conciliar(Esquema.Nuevo())
			Marco.igual(reparaciones, 0)
			comprobarGuardable(datos)
		end)
	end)

	Marco.grupo("Esquema.Conciliar", function()
		Marco.prueba("rellena los campos que faltan sin contarlos como reparaciones", function()
			local Esquema = cargarEsquema()
			local datos, reparaciones = Esquema.Conciliar({ Monedas = 50, Nivel = 7 })

			Marco.igual(datos.Monedas, 50, "no debe pisar lo que ya había")
			Marco.igual(datos.Nivel, 7)
			Marco.igual(datos.XP, 0)
			Marco.igual(datos.Bando, "Ninguno")
			Marco.igual(datos.MejorasNave.Escudo, 0)
			Marco.igualProfundo(datos.Inventario, {})
			Marco.igual(reparaciones, 0, "un campo nuevo en jugadores antiguos es normal")
		end)

		Marco.prueba("añade las mejoras nuevas de la nave sin tocar las que ya existen", function()
			local Esquema = cargarEsquema()
			local datos = Esquema.Conciliar({ MejorasNave = { Casco = 4 } })
			Marco.igual(datos.MejorasNave.Casco, 4)
			Marco.igual(datos.MejorasNave.Motor, 0)
			Marco.igual(datos.MejorasNave.Carga, 0)
		end)

		Marco.prueba("conserva datos válidos y los campos que no conoce", function()
			local Esquema = cargarEsquema()
			local entrada = {
				Bando = "Monstruos",
				Nivel = 12,
				XP = 340,
				Monedas = 1500,
				Inventario = { hierro = 30, cristal = 2 },
				MejorasNave = { Casco = 2, Escudo = 1, Motor = 0, Armas = 5, Escaner = 3, Carga = 4 },
				CampoFuturo = "no lo borres",
			}
			local datos, reparaciones = Esquema.Conciliar(Esquema.Migrar(entrada, 1))

			Marco.igual(reparaciones, 0)
			Marco.igual(datos.Bando, "Monstruos")
			Marco.igual(datos.Inventario.hierro, 30)
			Marco.igual(datos.MejorasNave.Armas, 5)
			Marco.igual(datos.MejorasNave.Carga, 4)
			Marco.igual((datos :: any).CampoFuturo, "no lo borres")
		end)

		Marco.prueba("modifica la tabla en sitio y devuelve esa misma tabla", function()
			local Esquema = cargarEsquema()
			local entrada = { Monedas = 5 }
			local datos = Esquema.Conciliar(entrada)
			Marco.igual(datos, entrada)
			Marco.igual(entrada.XP, 0)
		end)

		Marco.prueba("si lo recibido no es una tabla, devuelve datos nuevos", function()
			local Esquema = cargarEsquema()
			for _, entrada in { "texto", 5, true } do
				local datos, reparaciones = Esquema.Conciliar(entrada)
				Marco.igual(datos.Nivel, 1)
				Marco.igual(reparaciones, 1)
			end
			Marco.igual(Esquema.Conciliar(nil).Nivel, 1)
		end)

		Marco.prueba("repara los campos con el tipo equivocado", function()
			local Esquema = cargarEsquema()
			local datos, reparaciones = Esquema.Conciliar({
				Nivel = "diez",
				XP = {},
				Monedas = true,
				Inventario = 5,
				MejorasNave = { Casco = "mucho", Escudo = 2 },
			})

			Marco.igual(datos.Nivel, 1)
			Marco.igual(datos.XP, 0)
			Marco.igual(datos.Monedas, 0)
			Marco.igualProfundo(datos.Inventario, {})
			Marco.igual(datos.MejorasNave.Casco, 0)
			Marco.igual(datos.MejorasNave.Escudo, 2)
			Marco.igual(reparaciones, 5)
		end)

		Marco.prueba("repara NaN, infinitos, negativos y decimales en los contadores", function()
			local Esquema = cargarEsquema()

			local datos, reparaciones = Esquema.Conciliar({
				Nivel = 0,
				XP = -5,
				Monedas = 0 / 0,
			})
			Marco.igual(datos.Nivel, 1, "el nivel mínimo es 1")
			Marco.igual(datos.XP, 0)
			Marco.igual(datos.Monedas, 0)
			Marco.igual(reparaciones, 3)

			datos, reparaciones = Esquema.Conciliar({ Monedas = math.huge, XP = -math.huge })
			Marco.igual(datos.Monedas, 0)
			Marco.igual(datos.XP, 0)
			Marco.igual(reparaciones, 2)

			datos, reparaciones = Esquema.Conciliar({ Monedas = 12.7, Nivel = 3.2 })
			Marco.igual(datos.Monedas, 12, "los decimales se truncan")
			Marco.igual(datos.Nivel, 3)
			Marco.igual(reparaciones, 2)
		end)

		Marco.prueba("repara un bando desconocido y respeta los válidos", function()
			local Esquema = cargarEsquema()
			Marco.igual(Esquema.Conciliar({ Bando = "Piratas" }).Bando, "Ninguno")
			Marco.igual(Esquema.Conciliar({ Bando = 5 }).Bando, "Ninguno")
			Marco.igual(Esquema.Conciliar({ Bando = "Humanos" }).Bando, "Humanos")
			Marco.igual(Esquema.Conciliar({ Bando = "Monstruos" }).Bando, "Monstruos")
			Marco.igual(Esquema.Conciliar({ Bando = "Ninguno" }).Bando, "Ninguno")
		end)

		Marco.prueba("limpia las entradas inválidas del inventario y de las mejoras", function()
			local Esquema = cargarEsquema()
			local datos, reparaciones = Esquema.Conciliar({
				Inventario = {
					hierro = 10,
					cristal = -3, -- negativa
					plasma = 0 / 0, -- NaN
					chatarra = 2.9, -- decimal
					[1] = 5, -- clave que no es texto
					raro = "mucho", -- no es un número
				},
				MejorasNave = { Casco = -1, Escudo = 2 },
			})

			Marco.igualProfundo(datos.Inventario, { hierro = 10, chatarra = 2 })
			Marco.igual(datos.MejorasNave.Casco, 0, "una mejora negativa vuelve a 0")
			Marco.igual(datos.MejorasNave.Escudo, 2)
			Marco.igual(reparaciones, 6)
		end)

		Marco.prueba("es idempotente: conciliar dos veces no repara nada la segunda", function()
			local Esquema = cargarEsquema()
			local datos = Esquema.Conciliar({ Nivel = "x", Monedas = 0 / 0, Inventario = { a = -1 } })
			local _, reparaciones = Esquema.Conciliar(datos)
			Marco.igual(reparaciones, 0)
		end)

		Marco.prueba("tras conciliar, unos datos corruptos se pueden guardar en un DataStore", function()
			local Esquema = cargarEsquema()
			local corruptos = {
				Nivel = 0 / 0,
				XP = math.huge,
				Monedas = -math.huge,
				Inventario = { hierro = 0 / 0, [1] = "x" },
				MejorasNave = { Casco = math.huge },
			}
			Marco.lanzaError(function()
				comprobarGuardable(corruptos)
			end, "104", "el DataStore simulado debe rechazar los datos sin conciliar")

			comprobarGuardable(Esquema.Conciliar(corruptos))
		end)
	end)

	Marco.grupo("Esquema.Migrar", function()
		Marco.prueba("sin migraciones definidas deja los datos como estaban", function()
			local Esquema = cargarEsquema()
			local datos = { Monedas = 5 }
			Marco.igual(Esquema.Migrar(datos, 1), datos)
			Marco.igualProfundo(datos, { Monedas = 5 })
		end)

		Marco.prueba("aplica en orden solo las migraciones posteriores a la versión de origen", function()
			local Esquema = cargarEsquema()
			Esquema.VERSION = 3
			local orden = {}
			Esquema.Migraciones[2] = function(datos)
				table.insert(orden, "2")
				datos.Monedas = datos.Oro -- el campo Oro pasó a llamarse Monedas
				datos.Oro = nil
			end
			Esquema.Migraciones[3] = function(datos)
				table.insert(orden, "3")
				datos.Nivel = (datos.Nivel or 0) + 1
			end

			local datos = Esquema.Migrar({ Oro = 40, Nivel = 1 }, 1)
			Marco.igual(table.concat(orden, ","), "2,3")
			Marco.igualProfundo(datos, { Monedas = 40, Nivel = 2 })

			table.clear(orden)
			Esquema.Migrar({}, 2)
			Marco.igual(table.concat(orden, ","), "3", "desde la versión 2 solo falta la 3")

			table.clear(orden)
			Esquema.Migrar({}, 3)
			Marco.igual(#orden, 0, "unos datos ya actuales no se migran")
		end)

		Marco.prueba("tolera versiones sin migración definida", function()
			local Esquema = cargarEsquema()
			Esquema.VERSION = 4
			Esquema.Migraciones[3] = function(datos)
				datos.Marca = true
			end

			local datos = Esquema.Migrar({}, 1)
			Marco.igual(datos.Marca, true)
		end)
	end)

	Marco.grupo("Esquema: migración a la versión 2 (Humanos y Monstruos)", function()
		Marco.prueba("los bandos antiguos pasan a Humanos y Monstruos", function()
			local Esquema = cargarEsquema()
			Marco.igual(Esquema.Migrar({ Bando = "Heroes" }, 1).Bando, "Humanos")
			Marco.igual(Esquema.Migrar({ Bando = "Villanos" }, 1).Bando, "Monstruos")
		end)

		Marco.prueba("sin bando o con Ninguno, no cambia nada", function()
			local Esquema = cargarEsquema()
			Marco.igual(Esquema.Migrar({ Bando = "Ninguno" }, 1).Bando, "Ninguno")
			Marco.esNil(Esquema.Migrar({}, 1).Bando)
		end)

		Marco.prueba("tras migrar y conciliar, el jugador conserva su bando", function()
			local Esquema = cargarEsquema()
			local datos = Esquema.Conciliar(Esquema.Migrar({ Bando = "Villanos", Monedas = 7 }, 1))
			Marco.igual(datos.Bando, "Monstruos", "sin la migración, Conciliar lo dejaría en Ninguno")
			Marco.igual(datos.Monedas, 7)
		end)

		Marco.prueba("los datos ya en la versión 2 no se tocan", function()
			local Esquema = cargarEsquema()
			Marco.igual(Esquema.Migrar({ Bando = "Humanos" }, 2).Bando, "Humanos")
		end)
	end)
end
