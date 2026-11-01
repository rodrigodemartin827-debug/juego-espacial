--[[
	Pruebas de BloqueoSesion: las decisiones del bloqueo de sesión como funciones puras sobre el
	registro del DataStore (tomar, guardar y soltar).
]]

local Entorno = require("../infraestructura/Entorno")

local function cargarBloqueoSesion()
	return Entorno.nuevo().servidor.requerir("ServerScriptService.Server.Servicios.ServicioDatos.BloqueoSesion")
end

local AHORA = 1000000
local CADUCIDAD = 300

local function crearBloqueo(idSesion: string, ultimaActividad: number?)
	return {
		IdSesion = idSesion,
		IdServidor = "servidor-" .. idSesion,
		IdLugar = 1,
		UltimaActividad = ultimaActividad or AHORA,
	}
end

local function crearOpciones(version: number?)
	return {
		Version = version or 1,
		CrearDatos = function()
			return { Monedas = 0 }
		end,
		Caducidad = CADUCIDAD,
	}
end

-- Un registro libre (sin bloqueo) con unos datos reconocibles.
local function crearRegistro(bloqueo: any?)
	return {
		Version = 1,
		Datos = { Monedas = 77 },
		Bloqueo = bloqueo,
		Meta = { Creado = AHORA - 5000, UltimoGuardado = AHORA - 100 },
	}
end

return function(Marco)
	Marco.grupo("BloqueoSesion.Tomar", function()
		Marco.prueba("crea un registro nuevo con el bloqueo cuando el jugador no tenía datos", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local bloqueo = crearBloqueo("A")

			local resultado, registro = BloqueoSesion.Tomar(nil, bloqueo, AHORA, crearOpciones())

			Marco.igual(resultado, "Nuevo")
			Marco.igual(registro.Version, 1)
			Marco.igualProfundo(registro.Datos, { Monedas = 0 })
			Marco.igual(registro.Bloqueo, bloqueo)
			Marco.igual(registro.Meta.Creado, AHORA)
		end)

		Marco.prueba("toma un registro libre sin tocar sus datos", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local bloqueo = crearBloqueo("A")
			local libre = crearRegistro(nil)

			local resultado, registro = BloqueoSesion.Tomar(libre, bloqueo, AHORA, crearOpciones())

			Marco.igual(resultado, "Tomado")
			Marco.igual(registro.Bloqueo, bloqueo)
			Marco.igualProfundo(registro.Datos, { Monedas = 77 })
		end)

		Marco.prueba("no puede tomarlo si otro servidor activo lo tiene, y no modifica nada", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local ajeno = crearBloqueo("B", AHORA - 10)
			local ocupado = crearRegistro(ajeno)

			local resultado, registro, dueno = BloqueoSesion.Tomar(ocupado, crearBloqueo("A"), AHORA, crearOpciones())

			Marco.igual(resultado, "Ocupado")
			Marco.esNil(registro, "no hay nada que escribir")
			Marco.igual(dueno, ajeno, "se informa de quién lo tiene")
			Marco.igual(ocupado.Bloqueo, ajeno, "el registro original no debe cambiar")
		end)

		Marco.prueba("toma el bloqueo de un servidor caído cuando pasa la caducidad", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local opciones = crearOpciones()

			local justoAntes = crearRegistro(crearBloqueo("B", AHORA - (CADUCIDAD - 1)))
			Marco.igual(BloqueoSesion.Tomar(justoAntes, crearBloqueo("A"), AHORA, opciones), "Ocupado")

			local justoEnElLimite = crearRegistro(crearBloqueo("B", AHORA - CADUCIDAD))
			local resultado, registro = BloqueoSesion.Tomar(justoEnElLimite, crearBloqueo("A"), AHORA, opciones)
			Marco.igual(resultado, "TomadoPorCaducidad")
			Marco.igual(registro.Bloqueo.IdSesion, "A")
			Marco.igualProfundo(registro.Datos, { Monedas = 77 })
		end)

		Marco.prueba("un bloqueo con la hora en el futuro (relojes distintos) cuenta como activo", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local delFuturo = crearRegistro(crearBloqueo("B", AHORA + 5000))
			Marco.igual(BloqueoSesion.Tomar(delFuturo, crearBloqueo("A"), AHORA, crearOpciones()), "Ocupado")
		end)

		Marco.prueba(
			"si el bloqueo ya era de esta misma sesión, lo renueva (reintento tras perder la respuesta)",
			function()
				local BloqueoSesion = cargarBloqueoSesion()
				local registro = crearRegistro(crearBloqueo("A", AHORA - 10))

				local resultado, nuevo = BloqueoSesion.Tomar(registro, crearBloqueo("A", AHORA), AHORA, crearOpciones())

				Marco.igual(resultado, "Tomado")
				Marco.igual(nuevo.Bloqueo.UltimaActividad, AHORA)
			end
		)

		Marco.prueba("un bloqueo mal formado se considera abandonado", function()
			local BloqueoSesion = cargarBloqueoSesion()
			for _, malo in { "texto", 5, {}, { IdSesion = "B" }, { IdSesion = "B", UltimaActividad = "ayer" } } do
				local resultado = BloqueoSesion.Tomar(crearRegistro(malo), crearBloqueo("A"), AHORA, crearOpciones())
				Marco.igual(resultado, "TomadoPorCaducidad", `bloqueo mal formado: {tostring(malo)}`)
			end
		end)

		Marco.prueba("un registro corrupto se rechaza sin tocarlo", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local corruptos = {
				"texto",
				5,
				{},
				{ Version = 1 }, -- sin Datos
				{ Datos = {} }, -- sin Version
				{ Version = "1", Datos = {} },
				{ Version = 1, Datos = "no soy una tabla" },
			}
			for _, corrupto in corruptos do
				local resultado, registro = BloqueoSesion.Tomar(corrupto, crearBloqueo("A"), AHORA, crearOpciones())
				Marco.igual(resultado, "Corrupto", `registro: {tostring(corrupto)}`)
				Marco.esNil(registro)
			end
		end)

		Marco.prueba("rechaza un registro guardado con una versión de esquema más nueva", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local futuro = crearRegistro(nil)
			futuro.Version = 3

			local resultado, registro = BloqueoSesion.Tomar(futuro, crearBloqueo("A"), AHORA, crearOpciones(2))
			Marco.igual(resultado, "VersionFutura")
			Marco.esNil(registro)

			-- Una versión igual o anterior sí se acepta (se migrará al cargar).
			Marco.igual(BloqueoSesion.Tomar(futuro, crearBloqueo("A"), AHORA, crearOpciones(3)), "Tomado")
			Marco.igual(BloqueoSesion.Tomar(futuro, crearBloqueo("A"), AHORA, crearOpciones(5)), "Tomado")
		end)
	end)

	Marco.grupo("BloqueoSesion.Guardar", function()
		Marco.prueba("guarda los datos y refresca la actividad si el bloqueo es nuestro", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local registro = crearRegistro(crearBloqueo("A", AHORA - 50))
			local datos = { Monedas = 500, Inventario = { hierro = 3 } }

			local resultado, nuevo = BloqueoSesion.Guardar(registro, "A", datos, AHORA, 2, false)

			Marco.igual(resultado, "Guardado")
			Marco.igualProfundo(nuevo.Datos, datos)
			Marco.distinto(nuevo.Datos, datos, "debe guardar una copia, no la tabla viva")
			Marco.distinto(nuevo.Datos.Inventario, datos.Inventario)
			Marco.igual(nuevo.Version, 2)
			Marco.igual(nuevo.Bloqueo.IdSesion, "A", "el bloqueo se mantiene")
			Marco.igual(nuevo.Bloqueo.UltimaActividad, AHORA, "y se refresca")
			Marco.igual(nuevo.Meta.UltimoGuardado, AHORA)
			Marco.igual(nuevo.Meta.Creado, AHORA - 5000, "conserva la fecha de creación")
		end)

		Marco.prueba("con liberar suelta el bloqueo", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local registro = crearRegistro(crearBloqueo("A"))

			local resultado, nuevo = BloqueoSesion.Guardar(registro, "A", { Monedas = 9 }, AHORA, 1, true)

			Marco.igual(resultado, "Guardado")
			Marco.esNil(nuevo.Bloqueo)
			Marco.igualProfundo(nuevo.Datos, { Monedas = 9 })
		end)

		Marco.prueba("no escribe nada si el bloqueo es de otra sesión", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local registro = crearRegistro(crearBloqueo("B"))

			local resultado, nuevo = BloqueoSesion.Guardar(registro, "A", { Monedas = 1 }, AHORA, 1, false)

			Marco.igual(resultado, "BloqueoPerdido")
			Marco.esNil(nuevo)
			Marco.igualProfundo(registro.Datos, { Monedas = 77 }, "los datos del otro servidor deben quedar intactos")
		end)

		Marco.prueba("no escribe nada si el registro no tiene bloqueo, no existe o está corrupto", function()
			local BloqueoSesion = cargarBloqueoSesion()
			for _, registro in { crearRegistro(nil), "texto", { Datos = {} }, { Bloqueo = "x" } } do
				local resultado, nuevo = BloqueoSesion.Guardar(registro, "A", {}, AHORA, 1, false)
				Marco.igual(resultado, "BloqueoPerdido")
				Marco.esNil(nuevo)
			end
			local resultado = BloqueoSesion.Guardar(nil, "A", {}, AHORA, 1, false)
			Marco.igual(resultado, "BloqueoPerdido")
		end)

		Marco.prueba("crea la información Meta si el registro no la tenía", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local registro = crearRegistro(crearBloqueo("A"))
			registro.Meta = nil

			local _, nuevo = BloqueoSesion.Guardar(registro, "A", {}, AHORA, 1, false)
			Marco.igual(nuevo.Meta.UltimoGuardado, AHORA)
		end)
	end)

	Marco.grupo("BloqueoSesion.Soltar", function()
		Marco.prueba("suelta el bloqueo sin tocar los datos", function()
			local BloqueoSesion = cargarBloqueoSesion()
			local registro = crearRegistro(crearBloqueo("A"))

			local resultado, nuevo = BloqueoSesion.Soltar(registro, "A")

			Marco.igual(resultado, "Liberado")
			Marco.esNil(nuevo.Bloqueo)
			Marco.igualProfundo(nuevo.Datos, { Monedas = 77 })
			Marco.igual(nuevo.Meta.UltimoGuardado, AHORA - 100, "no cuenta como un guardado")
		end)

		Marco.prueba("no hace nada si el bloqueo es de otro o ya estaba libre", function()
			local BloqueoSesion = cargarBloqueoSesion()

			local ajeno = crearRegistro(crearBloqueo("B"))
			local resultado, nuevo = BloqueoSesion.Soltar(ajeno, "A")
			Marco.igual(resultado, "BloqueoPerdido")
			Marco.esNil(nuevo)
			Marco.igual(ajeno.Bloqueo.IdSesion, "B")

			resultado, nuevo = BloqueoSesion.Soltar(crearRegistro(nil), "A")
			Marco.igual(resultado, "BloqueoPerdido")
			Marco.esNil(nuevo)

			resultado = BloqueoSesion.Soltar(nil, "A")
			Marco.igual(resultado, "BloqueoPerdido")
		end)
	end)
end
