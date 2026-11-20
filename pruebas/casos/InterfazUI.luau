--[[
	Interfaz (src/client/UI): las reglas del encargo y que todo esté conectado.

	La interfaz construye GUIs de Roblox (TweenService, UIScale, ViewportFrame...) que la simulación no tiene, así que
	aquí se prueba lo que sí se puede comprobar fuera de Studio:
	  - reglas: --!strict en todos los módulos, NINGÚN emoji, colores solo desde EspacialTheme, los colores del encargo;
	  - iconos: los 22 pedidos y todos los que usa el código existen como .svg y .png (128×128 los iconos, 256×256 el arte),
	    tienen entrada en IdsIconos y están en el sprite del preview (preview y archivos son los mismos);
	  - datos: DatosDemo, CatalogoUI y ConfigUI son coherentes con el juego (objetos, especies, poderes, teclas) y la tienda
	    no vende nada de combate por gemas ni Robux (sin pay-to-win);
	  - el preview HTML es un solo archivo sin dependencias externas.
	Lo visual (aspecto, animaciones) se revisa en Studio y en el preview: ver src/client/UI/README.md.
]]

local fs = require("@lune/fs")

local Entorno = require("../infraestructura/Entorno")

local UI = "src/client/UI"
local RUTA_UI = "StarterPlayer.StarterPlayerScripts.Client.UI.Modules"

-- Archivos de un directorio (recursivo) con una de las extensiones dadas.
local function archivos(directorio: string, extensiones: { string }, resultado: { string }?): { string }
	local lista = resultado or {}
	for _, nombre in fs.readDir(directorio) do
		local ruta = `{directorio}/{nombre}`
		if fs.isDir(ruta) then
			archivos(ruta, extensiones, lista)
		else
			for _, ext in extensiones do
				if string.sub(nombre, -#ext) == ext then
					table.insert(lista, ruta)
				end
			end
		end
	end
	return lista
end

-- Primer emoji (o símbolo pictográfico) de un texto UTF-8, o nil.
local function primerEmoji(texto: string): string?
	local ok, resultado = pcall(function()
		for _, c in utf8.codes(texto) do
			if
				(c >= 0x1F000 and c <= 0x1FAFF) -- emojis, banderas, símbolos pictográficos
				or (c >= 0x2600 and c <= 0x27BF) -- símbolos varios y dingbats (★ ☆ ✓ ✔ ⚔ ...)
				or (c >= 0x2B00 and c <= 0x2BFF) -- flechas y estrellas de colores (⭐ ⬡ ...)
				or (c >= 0x2300 and c <= 0x23FF and c ~= 0x2318) -- relojes y botones (⌚ ⏳ ⏸ ...)
				or c == 0xFE0F -- selector de variante "como emoji"
				or c == 0x200D -- unión de emojis
			then
				return string.format("U+%04X", c)
			end
		end
		return nil
	end)
	return if ok then resultado else nil
end

-- Ancho y alto de un PNG (cabecera IHDR).
local function tamanoPng(ruta: string): (number, number)
	local datos = fs.readFile(ruta)
	assert(string.sub(datos, 2, 4) == "PNG", `{ruta} no es un PNG`)
	return string.unpack(">I4I4", datos, 17)
end

return function(Marco)
	local entorno = Entorno.nuevo()
	local function cargarUI(nombre: string)
		return entorno.cliente.requerir(`{RUTA_UI}.{nombre}`)
	end
	local function cargarShared(nombre: string)
		return entorno.cliente.requerir(`ReplicatedStorage.Shared.{nombre}`)
	end
	local IdsIconos = cargarUI("Iconos.IdsIconos")
	local DatosDemo = cargarUI("Datos.DatosDemo")
	local CatalogoUI = cargarUI("Datos.CatalogoUI")
	local ConfigUI = cargarUI("Datos.ConfigUI")

	local RAREZAS = { Comun = true, PocoComun = true, Raro = true, Epico = true, Legendario = true, Mitico = true }
	local STATS = { Fuerza = true, Aguante = true, Espada = true, Arma = true, Habilidad = true }

	Marco.grupo("Interfaz: reglas del código", function()
		Marco.prueba("todos los módulos Luau de la UI empiezan con --!strict", function()
			local sin = {}
			for _, ruta in archivos(UI, { ".luau" }) do
				if string.sub(fs.readFile(ruta), 1, 9) ~= "--!strict" then
					table.insert(sin, ruta)
				end
			end
			Marco.igual(#sin, 0, table.concat(sin, ", "))
		end)

		Marco.prueba("ningún emoji en la UI, los iconos, el preview ni las herramientas de iconos", function()
			local encontrados = {}
			for _, ruta in archivos(UI, { ".luau", ".html", ".svg", ".md" }) do
				local emoji = primerEmoji(fs.readFile(ruta))
				if emoji then
					table.insert(encontrados, `{ruta} ({emoji})`)
				end
			end
			for _, ruta in archivos("herramientas/iconos_ui", { ".mjs" }) do
				local emoji = primerEmoji(fs.readFile(ruta))
				if emoji then
					table.insert(encontrados, `{ruta} ({emoji})`)
				end
			end
			Marco.igual(#encontrados, 0, table.concat(encontrados, "\n"))
		end)

		Marco.prueba("los colores solo se escriben en EspacialTheme", function()
			local fuera = {}
			for _, ruta in archivos(UI, { ".luau" }) do
				if not string.find(ruta, "EspacialTheme", 1, true) then
					local texto = fs.readFile(ruta)
					for _, patron in { "Color3%.fromRGB", "Color3%.fromHex", "Color3%.new", "BrickColor" } do
						if string.find(texto, patron) then
							table.insert(fuera, `{ruta}: {patron}`)
						end
					end
				end
			end
			Marco.igual(#fuera, 0, table.concat(fuera, "\n"))
		end)

		Marco.prueba("EspacialTheme tiene los colores del encargo", function()
			local tema = fs.readFile(`{UI}/Modules/Temas/EspacialTheme.luau`)
			-- Fondos, acento, texto, tienda, stats, rarezas, estados y rangos.
			for _, hex in
				{
					"0A142D",
					"0B1628",
					"101B35",
					"3DF2FF",
					"E0E6F0",
					"FFB800",
					"FF8800",
					"FF8844",
					"4AFF8B",
					"FF4444",
					"A07AE8",
					"888888",
					"4488FF",
					"555555",
					"CD7F32",
					"C0C0C0",
					"FFD700",
					"4AE0E0",
					"B9F2FF",
				}
			do
				Marco.contiene(tema, `"{hex}"`, `falta el color #{hex}`)
			end
			Marco.contiene(tema, "GothamSSm", "la fuente debe ser GothamSSm")
		end)

		Marco.prueba("están todos los módulos de la estructura pedida", function()
			for _, ruta in
				{
					"HUDController",
					"Modules/Sidebar",
					"Modules/PanelPersonaje",
					"Modules/PanelInventario",
					"Modules/PanelPoderes",
					"Modules/PanelClan",
					"Modules/PanelRanked",
					"Modules/PanelIndice",
					"Modules/PanelMapa",
					"Modules/PanelAjustes",
					"Modules/PanelTienda",
					"Modules/HUDPartida",
					"Modules/Componentes/BarraVida",
					"Modules/Componentes/SlotEquipo",
					"Modules/Componentes/CardItem",
					"Modules/Componentes/FilaMiembro",
					"Modules/Componentes/CardModo",
					"Modules/Componentes/EntradaIndice",
					"Modules/Componentes/BotonSidebar",
					"Modules/Componentes/TabSelector",
					"Modules/Componentes/StatRow",
					"Modules/Componentes/Tooltip",
					"Modules/Componentes/Notificacion",
					"Modules/Iconos/IconBuilder",
					"Modules/Animaciones/UITweens",
					"Modules/Temas/EspacialTheme",
				}
			do
				Marco.verdadero(fs.isFile(`{UI}/{ruta}.luau`), `falta {ruta}.luau`)
			end
		end)
	end)

	Marco.grupo("Interfaz: iconos", function()
		Marco.prueba("existen los 22 SVG pedidos", function()
			for _, nombre in
				{
					"sidebar_personaje",
					"sidebar_inventario",
					"sidebar_poderes",
					"sidebar_clan",
					"sidebar_ranked",
					"sidebar_indice",
					"sidebar_mapa",
					"sidebar_ajustes",
					"sidebar_tienda",
					"slot_casco",
					"slot_armadura",
					"slot_espada",
					"slot_arma",
					"slot_amuleto",
					"slot_anillo",
					"slot_cinturon",
					"slot_botas",
					"stat_fuerza",
					"stat_aguante",
					"stat_espada",
					"stat_arma",
					"stat_habilidad",
				}
			do
				Marco.verdadero(fs.isFile(`{UI}/Assets/IconSVGs/{nombre}.svg`), `falta {nombre}.svg`)
			end
		end)

		Marco.prueba(
			"cada icono tiene SVG blanco de 128 y PNG de 128×128; cada arte, SVG y PNG de 256×256",
			function()
				for nombre in IdsIconos.Iconos do
					local svg = `{UI}/Assets/IconSVGs/{nombre}.svg`
					Marco.verdadero(fs.isFile(svg), `falta {svg}`)
					local texto = fs.readFile(svg)
					Marco.contiene(texto, 'viewBox="0 0 128 128"')
					Marco.falso(
						string.find(texto, "currentColor", 1, true),
						`{nombre}.svg debe ser blanco (se tiñe en Roblox)`
					)
					local ancho, alto = tamanoPng(`{UI}/Assets/IconPNGs/{nombre}.png`)
					Marco.igual(ancho, 128, nombre)
					Marco.igual(alto, 128, nombre)
				end
				for nombre in IdsIconos.Arte do
					Marco.verdadero(fs.isFile(`{UI}/Assets/ArteSVGs/{nombre}.svg`), `falta el arte {nombre}.svg`)
					local ancho, alto = tamanoPng(`{UI}/Assets/ArtePNGs/{nombre}.png`)
					Marco.igual(ancho, 256, nombre)
					Marco.igual(alto, 256, nombre)
				end
			end
		)

		Marco.prueba("no sobran archivos: cada SVG y PNG tiene su entrada en IdsIconos", function()
			for _, par in
				{
					{ "IconSVGs", IdsIconos.Iconos },
					{ "IconPNGs", IdsIconos.Iconos },
					{ "ArteSVGs", IdsIconos.Arte },
					{ "ArtePNGs", IdsIconos.Arte },
				}
			do
				for _, archivo in fs.readDir(`{UI}/Assets/{par[1]}`) do
					local nombre = string.gsub(archivo, "%.%w+$", "")
					Marco.distinto(par[2][nombre], nil, `{par[1]}/{archivo} no está en IdsIconos`)
				end
			end
		end)

		Marco.prueba("todos los iconos y artes que nombra el código existen", function()
			local prefijos = "^(%a+)_[%w_]+$"
			local validos = {
				sidebar = true,
				slot = true,
				stat = true,
				ui = true,
				aj = true,
				raza = true,
				hab = true,
				rango = true,
				item = true,
				criatura = true,
				planta = true,
				planeta = true,
				skin = true,
				estela = true,
				aura = true,
				pack = true,
				pase = true,
			}
			local faltan = {}
			for _, ruta in archivos(UI, { ".luau" }) do
				if not string.find(ruta, "IdsIconos", 1, true) then
					for cadena in string.gmatch(fs.readFile(ruta), '"([%w_]+)"') do
						local prefijo = string.match(cadena, prefijos)
						if
							prefijo
							and validos[prefijo]
							and IdsIconos.Iconos[cadena] == nil
							and IdsIconos.Arte[cadena] == nil
						then
							table.insert(faltan, `{ruta}: {cadena}`)
						end
					end
				end
			end
			Marco.igual(#faltan, 0, table.concat(faltan, "\n"))
		end)

		Marco.prueba("el sprite del preview tiene todos los iconos y artes (los mismos que los archivos)", function()
			local html = fs.readFile(`{UI}/preview_ui_completa.html`)
			for nombre in IdsIconos.Iconos do
				Marco.contiene(html, `<symbol id="i-{nombre}"`, `falta el icono {nombre} en el preview`)
			end
			for nombre in IdsIconos.Arte do
				Marco.contiene(html, `<symbol id="a-{nombre}"`, `falta el arte {nombre} en el preview`)
			end
		end)
	end)

	Marco.grupo("Interfaz: datos", function()
		local Objetos = cargarShared("Exploracion.Datos.Objetos")
		local Especies = cargarShared("Exploracion.Datos.Especies")
		local Poderes = cargarShared("Combate.Datos.Poderes")

		Marco.prueba("CatalogoUI presenta todos los objetos y especies del juego", function()
			for id in Objetos.Lista do
				local p = CatalogoUI.Objetos[id]
				Marco.distinto(p, nil, `falta el objeto {id} en CatalogoUI.Objetos`)
				Marco.verdadero(RAREZAS[p.Rareza], `rareza desconocida en {id}`)
				Marco.distinto(IdsIconos.Arte[p.Arte], nil, `arte {p.Arte} de {id}`)
			end
			for id, especie in Especies.Lista do
				local p = CatalogoUI.Especies[id]
				Marco.distinto(p, nil, `falta la especie {id} en CatalogoUI.Especies`)
				Marco.distinto(IdsIconos.Arte[p.Arte], nil, `arte {p.Arte} de {id}`)
				Marco.distinto(CatalogoUI.RarezaEspecie[especie.Rareza], nil, `rareza {especie.Rareza} sin traducir`)
				Marco.distinto(
					CatalogoUI.CategoriaIndice[especie.Categoria],
					nil,
					`categoría {especie.Categoria} sin pestaña`
				)
			end
		end)

		Marco.prueba("el equipo de demostración es coherente: slots, rarezas, stats y arte", function()
			local slots = {}
			for _, slot in DatosDemo.Slots do
				Marco.esNil(slots[slot.Id], `slot repetido {slot.Id}`)
				slots[slot.Id] = true
				Marco.distinto(IdsIconos.Iconos[slot.Icono], nil, slot.Icono)
			end
			Marco.igual(#DatosDemo.Slots, 8)
			local porId = {}
			for _, o in DatosDemo.Objetos do
				porId[o.Id] = o
				Marco.verdadero(RAREZAS[o.Rareza], `rareza de {o.Id}`)
				Marco.distinto(IdsIconos.Arte[o.Arte], nil, `arte de {o.Id}`)
				if o.Slot then
					Marco.verdadero(slots[o.Slot], `slot de {o.Id}`)
				end
				for _, s in o.Stats or {} do
					Marco.verdadero(STATS[s.Stat], `stat {s.Stat} de {o.Id}`)
				end
			end
			for slot, id in DatosDemo.Equipado do
				Marco.distinto(porId[id], nil, `equipado {id}`)
				Marco.igual(porId[id].Slot, slot, `{id} está en el slot {slot}`)
			end
		end)

		Marco.prueba("el árbol de poderes: cada rama progresa por tiers y acaba en una ultimate", function()
			for _, rama in DatosDemo.Arbol do
				local tier = 0
				for _, nodo in rama.Nodos do
					Marco.verdadero(nodo.T >= tier, `tiers desordenados en {rama.Id}`)
					tier = nodo.T
					Marco.distinto(IdsIconos.Iconos[nodo.I], nil, `icono {nodo.I}`)
				end
				Marco.igual(rama.Nodos[#rama.Nodos].T, 4, `la rama {rama.Id} acaba en ultimate`)
			end
		end)

		Marco.prueba("sin pay-to-win: con gemas o Robux no se vende nada de combate", function()
			for _, p in DatosDemo.Tienda.Productos do
				Marco.verdadero(p.Moneda == "Monedas" or p.Moneda == "Gemas" or p.Moneda == "Robux", `moneda de {p.Id}`)
				Marco.verdadero(RAREZAS[p.Rareza], `rareza de {p.Id}`)
				Marco.distinto(IdsIconos.Arte[p.A], nil, `arte de {p.Id}`)
				if p.Moneda ~= "Monedas" then
					for _, categoria in p.Cat do
						Marco.verdadero(
							categoria ~= "Armas" and categoria ~= "Armadura",
							`{p.Id} se vende por {p.Moneda} en {categoria}`
						)
					end
				end
			end
		end)

		Marco.prueba("las habilidades del HUD existen en Poderes y tienen icono", function()
			for _, id in ConfigUI.HUD.Habilidades do
				Marco.distinto(Poderes.Presentacion(id), nil, `la habilidad {id} no existe en Combate/Datos/Poderes`)
				Marco.distinto(IdsIconos.Iconos[ConfigUI.HUD.IconosHabilidad[id]], nil, `icono de {id}`)
			end
		end)

		Marco.prueba("las teclas de la UI no chocan con las del juego ni con las de los poderes", function()
			local ocupadas = {}
			for _, tecla in ConfigUI.TeclasDelJuego do
				ocupadas[tecla] = "el juego"
			end
			for _, id in Poderes.Orden do
				local hab = Poderes.Presentacion(id)
				if hab and hab.Tecla ~= "Click" then
					ocupadas[hab.Tecla] = `el poder {id}`
				end
			end
			for accion, tecla in ConfigUI.Teclas do
				Marco.esNil(ocupadas[tecla], `{accion} usa {tecla}, que ya usa {ocupadas[tecla]}`)
			end
		end)

		Marco.prueba("la barra lateral tiene los 8 botones y la tienda, con iconos", function()
			Marco.igual(#ConfigUI.Sidebar, 8)
			for _, b in ConfigUI.Sidebar do
				Marco.distinto(IdsIconos.Iconos[b.Icono], nil, b.Icono)
			end
			Marco.igual(ConfigUI.BotonTienda.Icono, "sidebar_tienda")
		end)
	end)

	Marco.grupo("Interfaz: preview HTML", function()
		Marco.prueba("es un solo archivo sin dependencias externas", function()
			local html = fs.readFile(`{UI}/preview_ui_completa.html`)
			Marco.falso(string.find(html, "<script%s+src"), "no puede cargar scripts externos")
			Marco.falso(string.find(html, "<link%s"), "no puede cargar hojas de estilo externas")
			local sinNamespace = string.gsub(html, "http://www%.w3%.org/2000/svg", "")
			Marco.falso(string.find(sinNamespace, "https?://"), "no puede pedir nada a internet")
			Marco.contiene(html, "<!-- ICONOS:INICIO -->")
			Marco.contiene(html, "<!-- ICONOS:FIN -->")
		end)

		Marco.prueba("usa los mismos productos, objetos y datos que DatosDemo", function()
			local html = fs.readFile(`{UI}/preview_ui_completa.html`)
			for _, p in DatosDemo.Tienda.Productos do
				Marco.contiene(html, `Id: "{p.Id}"`, `producto {p.Id}`)
			end
			for _, o in DatosDemo.Objetos do
				Marco.contiene(html, `Id: "{o.Id}"`, `objeto {o.Id}`)
			end
			Marco.contiene(html, DatosDemo.Clan.Lema)
		end)
	end)
end
