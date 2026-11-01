--[[
	Pruebas de las utilidades compartidas: Tablas y Senal.
]]

local Entorno = require("../infraestructura/Entorno")

-- Crea un entorno nuevo y carga la utilidad `nombre`. Devuelve el módulo y el entorno.
local function cargar(nombre: string)
	local entorno = Entorno.nuevo()
	return entorno.servidor.requerir(`ReplicatedStorage.Shared.Utilidades.{nombre}`), entorno
end

return function(Marco)
	Marco.grupo("Tablas.CopiaProfunda", function()
		Marco.prueba("copia las tablas anidadas sin compartir referencias", function()
			local Tablas = cargar("Tablas")
			local original = { a = 1, b = { c = { 2, 3 } }, d = "x" }
			local copia = Tablas.CopiaProfunda(original)

			Marco.distinto(copia, original)
			Marco.distinto(copia.b, original.b)
			Marco.distinto(copia.b.c, original.b.c)
			Marco.igualProfundo(copia, original)
		end)

		Marco.prueba("modificar la copia no afecta al original", function()
			local Tablas = cargar("Tablas")
			local original = { lista = { 1, 2, 3 } }
			local copia = Tablas.CopiaProfunda(original)
			copia.lista[1] = 99
			Marco.igual(original.lista[1], 1)
		end)

		Marco.prueba("los valores que no son tablas se devuelven tal cual", function()
			local Tablas = cargar("Tablas")
			Marco.igual(Tablas.CopiaProfunda(5), 5)
			Marco.igual(Tablas.CopiaProfunda("hola"), "hola")
			Marco.igual(Tablas.CopiaProfunda(true), true)
			Marco.esNil(Tablas.CopiaProfunda(nil))
		end)
	end)

	Marco.grupo("Senal", function()
		Marco.prueba("Disparar llama a todos los manejadores con los argumentos", function()
			local Senal = cargar("Senal")
			local senal = Senal.nueva()
			local llamadas = {}
			senal:Conectar(function(...)
				table.insert(llamadas, { "uno", ... })
			end)
			senal:Conectar(function(...)
				table.insert(llamadas, { "dos", ... })
			end)

			senal:Disparar(1, "x")

			Marco.igual(#llamadas, 2)
			Marco.igualProfundo(llamadas[1], { "uno", 1, "x" })
			Marco.igualProfundo(llamadas[2], { "dos", 1, "x" })
		end)

		Marco.prueba("Desconectar deja de llamar al manejador (y se puede repetir)", function()
			local Senal = cargar("Senal")
			local senal = Senal.nueva()
			local cuenta = 0
			local conexion = senal:Conectar(function()
				cuenta += 1
			end)

			senal:Disparar()
			conexion:Desconectar()
			conexion:Desconectar()
			senal:Disparar()

			Marco.igual(cuenta, 1)
			Marco.falso(conexion.Conectada)
		end)

		Marco.prueba("los argumentos se pasan por referencia, sin copiar las tablas", function()
			local Senal = cargar("Senal")
			local senal = Senal.nueva()
			local recibido
			senal:Conectar(function(valor)
				recibido = valor
			end)
			local tabla = {}
			senal:Disparar(tabla)
			Marco.igual(recibido, tabla)
		end)

		Marco.prueba("desconectar dentro de un manejador no altera la ronda en curso", function()
			local Senal = cargar("Senal")
			local senal = Senal.nueva()
			local orden = {}
			local primera
			primera = senal:Conectar(function()
				table.insert(orden, "A")
				primera:Desconectar()
			end)
			senal:Conectar(function()
				table.insert(orden, "B")
			end)

			senal:Disparar()
			senal:Disparar()

			Marco.igual(table.concat(orden, ","), "A,B,B")
		end)

		Marco.prueba("un error en un manejador no impide que respondan los demás", function()
			local Senal, entorno = cargar("Senal")
			local senal = Senal.nueva()
			local respondio = false
			senal:Conectar(function()
				error("fallo intencionado de la prueba", 0)
			end)
			senal:Conectar(function()
				respondio = true
			end)

			senal:Disparar()

			Marco.verdadero(respondio)
			Marco.igual(#entorno.mundo.Errores, 1)
			Marco.contiene(entorno.mundo.Errores[1], "fallo intencionado de la prueba")
			table.clear(entorno.mundo.Errores) -- el error era el objetivo de la prueba
		end)

		Marco.prueba("Esperar pausa el hilo hasta el siguiente disparo y devuelve sus argumentos", function()
			local Senal, entorno = cargar("Senal")
			local senal = Senal.nueva()
			local resultado
			entorno.mundo.task.spawn(function()
				resultado = table.pack(senal:Esperar())
			end)
			Marco.esNil(resultado, "el hilo debería seguir esperando")

			senal:Disparar("a", "b")
			Marco.igual(resultado.n, 2)
			Marco.igual(resultado[1], "a")
			Marco.igual(resultado[2], "b")

			senal:Disparar("otra vez")
			Marco.igual(resultado.n, 2, "Esperar solo debe responder una vez")
		end)

		Marco.prueba("Destruir desconecta a todos", function()
			local Senal = cargar("Senal")
			local senal = Senal.nueva()
			local cuenta = 0
			senal:Conectar(function()
				cuenta += 1
			end)
			senal:Destruir()
			senal:Disparar()
			Marco.igual(cuenta, 0)
		end)
	end)
end
