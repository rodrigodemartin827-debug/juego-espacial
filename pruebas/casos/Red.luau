--[[
	Pruebas de las piezas compartidas de la red: LimitadorDeTasa y Validador.
]]

local Entorno = require("../infraestructura/Entorno")

local function cargar(nombre: string)
	local entorno = Entorno.nuevo()
	return entorno.servidor.requerir(`ReplicatedStorage.Shared.Red.{nombre}`), entorno
end

return function(Marco)
	-- Comprueba que el validador rechaza `valor` y que el motivo contiene `fragmento`.
	local function rechaza(validador, valor, fragmento)
		local valido, motivo = validador(valor)
		Marco.falso(valido, "debería rechazar el valor")
		Marco.contiene(motivo, fragmento)
	end

	Marco.grupo("LimitadorDeTasa", function()
		-- Crea un limitador con un reloj que la prueba controla a mano.
		local function limitadorConReloj(limite: number, rafaga: number?)
			local LimitadorDeTasa = cargar("LimitadorDeTasa")
			local reloj = { tiempo = 0 }
			local limitador = LimitadorDeTasa.nuevo(limite, rafaga, function()
				return reloj.tiempo
			end)
			return limitador, reloj
		end

		Marco.prueba("acepta una ráfaga igual al límite y rechaza la siguiente", function()
			local limitador = limitadorConReloj(5)
			local aceptadas = 0
			for _ = 1, 8 do
				if limitador:Permitir("a") then
					aceptadas += 1
				end
			end
			Marco.igual(aceptadas, 5)
		end)

		Marco.prueba("recupera una ficha cada 1/límite segundos", function()
			local limitador, reloj = limitadorConReloj(5)
			for _ = 1, 5 do
				limitador:Permitir("a")
			end

			reloj.tiempo = 0.19
			Marco.falso(limitador:Permitir("a"), "a los 0,19 s todavía no hay ficha")
			reloj.tiempo = 0.2
			Marco.verdadero(limitador:Permitir("a"), "a los 0,2 s ya hay una ficha")
			Marco.falso(limitador:Permitir("a"), "y se gasta")
		end)

		Marco.prueba("cada clave tiene su propio cubo", function()
			local limitador = limitadorConReloj(1)
			Marco.verdadero(limitador:Permitir("ana"))
			Marco.falso(limitador:Permitir("ana"))
			Marco.verdadero(limitador:Permitir("beto"))
		end)

		Marco.prueba("el cubo no se llena por encima de su capacidad aunque pase mucho tiempo", function()
			local limitador, reloj = limitadorConReloj(5)
			limitador:Permitir("a")
			reloj.tiempo = 1000

			local aceptadas = 0
			for _ = 1, 20 do
				if limitador:Permitir("a") then
					aceptadas += 1
				end
			end
			Marco.igual(aceptadas, 5)
		end)

		Marco.prueba("la ráfaga se puede ajustar por separado del ritmo", function()
			local limitador = limitadorConReloj(1, 3)
			local aceptadas = 0
			for _ = 1, 10 do
				if limitador:Permitir("a") then
					aceptadas += 1
				end
			end
			Marco.igual(aceptadas, 3)
		end)

		Marco.prueba("un ritmo sostenido exactamente igual al límite nunca se rechaza", function()
			-- Sin tolerancia de coma flotante, el error de redondeo rechazaría peticiones legítimas.
			local limitador, reloj = limitadorConReloj(5, 1)
			local aceptadas = 0
			for indice = 1, 100 do
				reloj.tiempo = 1000 + indice * 0.2
				if limitador:Permitir("a") then
					aceptadas += 1
				end
			end
			Marco.igual(aceptadas, 100)
		end)

		Marco.prueba("un ritmo del doble del límite se queda en la mitad", function()
			local limitador, reloj = limitadorConReloj(5, 1)
			local aceptadas = 0
			for indice = 1, 100 do
				reloj.tiempo = indice * 0.1
				if limitador:Permitir("a") then
					aceptadas += 1
				end
			end
			Marco.igual(aceptadas, 50)
		end)

		Marco.prueba("admite límites menores que 1 por segundo", function()
			local limitador, reloj = limitadorConReloj(0.5)
			Marco.verdadero(limitador:Permitir("a"), "la capacidad mínima es una ficha")
			reloj.tiempo = 1
			Marco.falso(limitador:Permitir("a"))
			reloj.tiempo = 2
			Marco.verdadero(limitador:Permitir("a"))
		end)

		Marco.prueba("Olvidar reinicia el cubo de esa clave", function()
			local limitador = limitadorConReloj(1)
			limitador:Permitir("a")
			Marco.falso(limitador:Permitir("a"))
			limitador:Olvidar("a")
			Marco.verdadero(limitador:Permitir("a"))
		end)

		Marco.prueba("un reloj que retrocede no rompe nada", function()
			local limitador, reloj = limitadorConReloj(1)
			reloj.tiempo = 10
			Marco.verdadero(limitador:Permitir("a"))
			reloj.tiempo = 5
			Marco.falso(limitador:Permitir("a"))
		end)

		Marco.prueba("rechaza un límite que no sea un número positivo", function()
			local LimitadorDeTasa = cargar("LimitadorDeTasa")
			Marco.lanzaError(function()
				LimitadorDeTasa.nuevo(0)
			end, "limitePorSegundo")
			Marco.lanzaError(function()
				LimitadorDeTasa.nuevo(-3)
			end, "limitePorSegundo")
		end)
	end)

	Marco.grupo("Validador", function()
		Marco.prueba("Numero acepta números finitos y respeta los límites (incluidos)", function()
			local Validador = cargar("Validador")
			Marco.verdadero(Validador.Numero()(5))
			Marco.verdadero(Validador.Numero()(-2.5))
			Marco.verdadero(Validador.Numero(0, 10)(0))
			Marco.verdadero(Validador.Numero(0, 10)(10))
			rechaza(Validador.Numero(0, 10), -1, ">= 0")
			rechaza(Validador.Numero(0, 10), 11, "<= 10")
		end)

		Marco.prueba("Numero rechaza NaN, infinitos y valores que no son números", function()
			local Validador = cargar("Validador")
			local esNumero = Validador.Numero()
			rechaza(esNumero, 0 / 0, "no es finito")
			rechaza(esNumero, math.huge, "no es finito")
			rechaza(esNumero, -math.huge, "no es finito")
			rechaza(esNumero, "5", "número")
			rechaza(esNumero, nil, "número")
			rechaza(esNumero, {}, "número")
			rechaza(esNumero, true, "número")
		end)

		Marco.prueba("Entero rechaza decimales y respeta los límites", function()
			local Validador = cargar("Validador")
			local esEntero = Validador.Entero(1, 5)
			Marco.verdadero(esEntero(3))
			rechaza(esEntero, 2.5, "entero")
			rechaza(esEntero, 0, ">= 1")
			rechaza(esEntero, 6, "<= 5")
			rechaza(esEntero, 0 / 0, "no es finito")
			rechaza(esEntero, "3", "número")
		end)

		Marco.prueba("Cadena limita la longitud (256 por defecto) y puede exigir un patrón", function()
			local Validador = cargar("Validador")
			Marco.verdadero(Validador.Cadena()("hola"))
			Marco.verdadero(Validador.Cadena()(string.rep("a", 256)))
			rechaza(Validador.Cadena(), string.rep("a", 257), "256")
			rechaza(Validador.Cadena(), 5, "cadena")
			rechaza(Validador.Cadena({ MinLongitud = 3 }), "ab", "al menos 3")
			rechaza(Validador.Cadena({ MaxLongitud = 5 }), "abcdef", "como máximo 5")

			local conPatron = Validador.Cadena({ Patron = "^[%w_]+$" })
			Marco.verdadero(conPatron("Nave_1"))
			rechaza(conPatron, "con espacio", "formato")
		end)

		Marco.prueba("Booleano solo acepta true o false", function()
			local Validador = cargar("Validador")
			Marco.verdadero(Validador.Booleano()(false))
			Marco.verdadero(Validador.Booleano()(true))
			rechaza(Validador.Booleano(), 1, "true o false")
			rechaza(Validador.Booleano(), "true", "true o false")
		end)

		Marco.prueba("Enumeracion solo acepta los valores indicados", function()
			local Validador = cargar("Validador")
			local esBando = Validador.Enumeracion({ "Heroes", "Villanos" })
			Marco.verdadero(esBando("Heroes"))
			rechaza(esBando, "Otro", "Heroes, Villanos")
			rechaza(esBando, "heroes", "no permitido")
			rechaza(esBando, 5, "no permitido")
			rechaza(esBando, nil, "no permitido")
			rechaza(esBando, {}, "no permitido")
		end)

		Marco.prueba("Vector3 acepta vectores finitos y rechaza NaN, infinitos y otros tipos", function()
			local Validador, entorno = cargar("Validador")
			local Vector3 = entorno.mundo.Vector3
			local esVector = Validador.Vector3(100)

			Marco.verdadero(esVector(Vector3.new(1, 2, 3)))
			rechaza(esVector, Vector3.new(0 / 0, 0, 0), "no es finito")
			rechaza(esVector, Vector3.new(0, math.huge, 0), "no es finito")
			rechaza(esVector, Vector3.new(0, 0, -math.huge), "no es finito")
			rechaza(esVector, Vector3.new(100, 100, 0), "<= 100")
			rechaza(esVector, { X = 1, Y = 2, Z = 3 }, "Vector3")
			rechaza(esVector, "1,2,3", "Vector3")
			Marco.verdadero(Validador.Vector3()(Vector3.new(1e6, 0, 0)), "sin límite de magnitud")
		end)

		Marco.prueba("Instancia comprueba la clase (admitiendo herencia)", function()
			local Validador, entorno = cargar("Validador")
			local Instance = entorno.mundo.Instance
			local script = Instance.new("Script")

			Marco.verdadero(Validador.Instancia()(script))
			Marco.verdadero(Validador.Instancia("Script")(script))
			Marco.verdadero(Validador.Instancia("LuaSourceContainer")(script))
			rechaza(Validador.Instancia("Player"), script, "Player")
			rechaza(Validador.Instancia(), "no soy una instancia", "Instancia")
			rechaza(Validador.Instancia(), nil, "Instancia")
		end)

		Marco.prueba("Opcional acepta nil y valida el resto", function()
			local Validador = cargar("Validador")
			local opcional = Validador.Opcional(Validador.Entero(0, 9))
			Marco.verdadero(opcional(nil))
			Marco.verdadero(opcional(4))
			rechaza(opcional, 10, "<= 9")
			rechaza(opcional, "x", "número")
		end)

		Marco.prueba("ValidarArgumentos comprueba cada posición y cuántos argumentos llegan", function()
			local Validador = cargar("Validador")
			local esquema = {
				Validador.Enumeracion({ "A", "B" }),
				Validador.Opcional(Validador.Entero(0, 9)),
			}

			Marco.verdadero(Validador.ValidarArgumentos(esquema, "A"), "el opcional puede omitirse")
			Marco.verdadero(Validador.ValidarArgumentos(esquema, "A", 3))

			local valido, motivo = Validador.ValidarArgumentos(esquema, "A", 3, "extra")
			Marco.falso(valido)
			Marco.contiene(motivo, "demasiados argumentos")

			valido, motivo = Validador.ValidarArgumentos(esquema)
			Marco.falso(valido, "falta el argumento obligatorio")
			Marco.contiene(motivo, "argumento 1")

			valido, motivo = Validador.ValidarArgumentos(esquema, "A", 99)
			Marco.falso(valido)
			Marco.contiene(motivo, "argumento 2")

			valido, motivo = Validador.ValidarArgumentos(esquema, nil, 3)
			Marco.falso(valido, "nil en el primer argumento")
			Marco.contiene(motivo, "argumento 1")
		end)

		Marco.prueba("ValidarArgumentos cuenta también los nil explícitos de más", function()
			local Validador = cargar("Validador")
			local esquema = { Validador.Opcional(Validador.Entero()) }
			local valido, motivo = Validador.ValidarArgumentos(esquema, nil, nil)
			Marco.falso(valido)
			Marco.contiene(motivo, "demasiados argumentos")
		end)

		Marco.prueba("con un esquema vacío solo se aceptan peticiones sin argumentos", function()
			local Validador = cargar("Validador")
			Marco.verdadero(Validador.ValidarArgumentos({}))
			Marco.falso(Validador.ValidarArgumentos({}, 1))
		end)
	end)
end
