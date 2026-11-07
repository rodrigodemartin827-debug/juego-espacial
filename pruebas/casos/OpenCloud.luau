--[[
	Pruebas de herramientas/OpenCloud.luau: lo que no necesita red de la subida de modelos (cuerpo multipart, qué
	archivos subir, lectura de las respuestas de la API y del creador).
]]

local OpenCloud = require("../../herramientas/OpenCloud")

return function(Marco)
	Marco.grupo("OpenCloud", function()
		Marco.prueba("tipo de contenido y nombre por la extensión", function()
			Marco.igual(OpenCloud.tipoContenido("piezas/Puente.fbx"), "model/fbx")
			Marco.igual(OpenCloud.tipoContenido("a/B.FBX"), "model/fbx")
			Marco.igual(OpenCloud.tipoContenido("x.glb"), "model/gltf-binary")
			Marco.esNil(OpenCloud.tipoContenido("atlas.png"))
			-- Las imágenes solo si se piden, y se suben como Decal.
			Marco.igual(OpenCloud.tipoContenido("texturas/Ojos_Redondos.png", true), "image/png")
			Marco.igual(OpenCloud.tipoRecurso("texturas/Ojos_Redondos.png"), "Decal")
			Marco.igual(OpenCloud.tipoRecurso("Cabellos.fbx"), "Model")
			Marco.igual(OpenCloud.peticion("Ojos", "d", { userId = "1" }, nil, "Decal").assetType, "Decal")
			Marco.igual(OpenCloud.nombreBase("piezas/Puente__lejos.fbx"), "Puente__lejos")
			Marco.igual(OpenCloud.clave(".\\piezas\\Puente.fbx"), "piezas/Puente.fbx")
		end)

		Marco.prueba("el cuerpo multipart lleva los dos campos y el archivo intacto", function()
			local binario = "FBX\0\1\2\255fin"
			local cuerpo, tipo = OpenCloud.multipart('{"a":1}', "Puente.fbx", "model/fbx", binario, "XYZ")
			Marco.igual(tipo, "multipart/form-data; boundary=XYZ")
			Marco.contiene(cuerpo, 'name="request"\r\nContent-Type: application/json\r\n\r\n{"a":1}\r\n--XYZ')
			Marco.contiene(cuerpo, 'name="fileContent"; filename="Puente.fbx"\r\nContent-Type: model/fbx\r\n\r\n')
			Marco.verdadero(string.find(cuerpo, "\r\n\r\n" .. binario .. "\r\n--XYZ--\r\n", 1, true) ~= nil)
			Marco.igual(string.sub(cuerpo, 1, 5), "--XYZ")
		end)

		Marco.prueba("falla si la frontera aparece dentro del archivo", function()
			Marco.lanzaError(function()
				OpenCloud.multipart("{}", "a.fbx", "model/fbx", "...--XYZ...", "XYZ")
			end, "frontera")
		end)

		Marco.prueba("petición: al crear lleva el creador; al actualizar, también el ID", function()
			local p = OpenCloud.peticion("Puente", "d", { userId = "123" })
			Marco.igual(p.assetType, "Model")
			Marco.igual(p.creationContext.creator.userId, "123")
			Marco.esNil(p.assetId)
			Marco.igual(OpenCloud.peticion("Puente", "d", { userId = "123" }, 456).assetId, "456")
		end)

		Marco.prueba("creador: usuario o grupo (el grupo manda) y solo números", function()
			Marco.igualProfundo((OpenCloud.creador("123", nil)), { userId = "123" })
			Marco.igualProfundo((OpenCloud.creador("123", "77")), { groupId = "77" })
			local c, motivo = OpenCloud.creador(nil, nil)
			Marco.esNil(c)
			Marco.contiene(motivo, "ROBLOX_CREATOR_ID")
			Marco.esNil((OpenCloud.creador("abc", nil)))
		end)

		Marco.prueba("lee la operación de la respuesta y su resultado al terminar", function()
			Marco.igual(OpenCloud.idOperacion({ path = "operations/ab-12" }), "ab-12")
			Marco.esNil(OpenCloud.idOperacion({}))
			Marco.esNil((OpenCloud.resultado({ done = false })))
			local id, mod = OpenCloud.resultado({
				done = true,
				response = { assetId = "987", moderationResult = { moderationState = "MODERATION_STATE_APPROVED" } },
			})
			Marco.igual(id, 987)
			Marco.igual(mod, "MODERATION_STATE_APPROVED")
			Marco.igual((OpenCloud.resultado({ done = true, response = { path = "assets/55" } })), 55)
		end)

		Marco.prueba("solo sube lo que ha cambiado; con ID, actualiza ese recurso", function()
			local candidatos = { ["piezas/A.fbx"] = "h1", ["piezas/B.fbx"] = "h2", ["piezas/C.fbx"] = "h3" }
			local registro = {
				["piezas/A.fbx"] = { id = 10, sha256 = "h1" }, -- sin cambios
				["piezas/B.fbx"] = { id = 20, sha256 = "viejo" }, -- cambiado
			}
			local lista = OpenCloud.pendientes(candidatos, registro, nil, false)
			Marco.igual(#lista, 2)
			Marco.igual(lista[1].ruta, "piezas/B.fbx")
			Marco.igual(lista[1].id, 20)
			Marco.igual(lista[2].ruta, "piezas/C.fbx")
			Marco.esNil(lista[2].id)
			Marco.igual(#OpenCloud.pendientes(candidatos, registro, { "piezas/A.fbx" }, false), 0)
			Marco.igual(#OpenCloud.pendientes(candidatos, registro, { "piezas/A.fbx" }, true), 1)
			Marco.lanzaError(function()
				OpenCloud.pendientes(candidatos, registro, { "piezas/Z.fbx" }, false)
			end, "no existe")
		end)
	end)
end
