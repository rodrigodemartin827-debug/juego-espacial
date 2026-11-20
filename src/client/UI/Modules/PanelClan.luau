--!strict
--[[
	PanelClan: pantalla TRIPULACIÓN (clan). Tabla de miembros al estilo de Vox Seas.

	  [AX] ARBUSTIX [NIVEL 12]                                  MIEMBROS 24/50 ▬▬▬
	       "Exploradores del cosmos"
	  RANGO        NOMBRE           NIVEL   ESTADO               │ RESUMEN
	  (estrella) Líder  Rodrixx_777   127   ● Online             │ #87 ranking de clanes
	  ...                                                        │ Planeta base, puntos
	  [INVITAR]  [CONFIGURAR]  [DEJAR CLAN]                      │ ACTIVIDAD

	CONFIGURAR solo se ve si eres líder u oficial. DEJAR CLAN pide confirmación.
	Los clanes todavía no existen en el juego: todo sale de DatosDemo.Clan.
]]

local Theme = require(script.Parent.Temas.EspacialTheme)
local IconBuilder = require(script.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Componentes.Primitivas)
local Ventana = require(script.Parent.Componentes.Ventana)
local FilaMiembro = require(script.Parent.Componentes.FilaMiembro)
local Modal = require(script.Parent.Componentes.Modal)
local DatosDemo = require(script.Parent.Datos.DatosDemo)
local Contexto = require(script.Parent.Contexto)

local C = Theme.Colores
local A = Theme.Alpha

local PanelClan = {}

local ctx: Contexto.Contexto = nil :: any
local ventana: Ventana.Ventana = nil :: any

local function construirCabecera(cuerpo: Frame)
	local clan = DatosDemo.Clan
	local caja = P.Caja(
		cuerpo,
		{ Nombre = "Cabecera", Tamano = UDim2.fromOffset(600, 76), Posicion = UDim2.fromOffset(12, 12), Z = 3 }
	)

	-- Estandarte (placeholder): cuadrado con degradado, hexágono oscuro y las siglas.
	local estandarte = P.Marco(caja, {
		Nombre = "Estandarte",
		Tamano = UDim2.fromOffset(56, 56),
		Posicion = UDim2.new(0, 10, 0.5, 0),
		Ancla = Vector2.new(0, 0.5),
		Color = C.Blanco,
		Radio = UDim.new(0, 10),
		Z = 4,
	})
	P.Degradado(estandarte, ColorSequence.new(C.AcentoOscuro, C.Habilidad:Lerp(C.Fondo1, 0.35)), 45)
	P.Borde(estandarte, C.Blanco, 0.7, Theme.Tamanos.TrazoActivo)
	IconBuilder.Icono(estandarte, "sidebar_personaje", {
		Tamano = 46,
		Color = C.Fondo1,
		Transparencia = 0.45,
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 5,
	})
	P.Texto(estandarte, {
		Texto = clan.Siglas,
		Tamano = Theme.Texto.Destacado + 1,
		Fuente = Theme.Fuentes.Negrita,
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 6,
		Contorno = true,
	})

	local nombre = P.Marco(caja, { Tamano = UDim2.fromOffset(300, 20), Posicion = UDim2.fromOffset(78, 18), Z = 4 })
	P.Lista(nombre, Enum.FillDirection.Horizontal, 8, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center)
	P.Texto(nombre, {
		Texto = clan.Nombre,
		Tamano = Theme.Texto.Destacado + 2,
		Fuente = Theme.Fuentes.Negrita,
		Espaciado = true,
		Orden = 1,
		Z = 4,
	})
	local nivel = P.Texto(nombre, {
		Texto = `NIVEL {clan.Nivel}`,
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Negrita,
		Color = C.Acento,
		Espaciado = true,
		Orden = 2,
		Z = 4,
	})
	nivel.BackgroundColor3 = C.Acento
	nivel.BackgroundTransparency = 0.88
	P.Esquinas(nivel, UDim.new(0, 4))
	P.Borde(nivel, C.Acento, A.BordeActivo)
	P.Relleno(nivel, 3, 7)
	P.Texto(caja, {
		Texto = `"{clan.Lema}"`,
		Tamano = Theme.Texto.Cuerpo,
		Fuente = Theme.Fuentes.Cursiva,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Posicion = UDim2.fromOffset(78, 44),
		Z = 4,
	})

	P.Etiqueta(caja, "MIEMBROS", { Posicion = UDim2.new(1, -12, 0, 16), Ancla = Vector2.new(1, 0), Z = 4 })
	P.Texto(caja, {
		Texto = `{clan.Miembros}<font size="{Theme.Texto.Medio}" transparency="0.6">/{clan.Maximo}</font>`,
		Rico = true,
		Tamano = Theme.Texto.Destacado,
		Fuente = Theme.Fuentes.Negrita,
		Posicion = UDim2.new(1, -12, 0, 28),
		Ancla = Vector2.new(1, 0),
		Z = 4,
	})
	local _, relleno = P.BarraProgreso(
		caja,
		{ Tamano = UDim2.fromOffset(110, 4), Posicion = UDim2.new(1, -12, 0, 52), Ancla = Vector2.new(1, 0), Z = 4 }
	)
	relleno.Size = UDim2.fromScale(clan.Miembros / clan.Maximo, 1)
end

local function construirTabla(cuerpo: Frame)
	local caja = P.Caja(cuerpo, {
		Nombre = "Tabla",
		Tamano = UDim2.new(0, 600, 1, -146),
		Posicion = UDim2.fromOffset(12, 96),
		Recortar = true,
		Z = 3,
	})
	local col = FilaMiembro.Columnas
	local cabecera = P.Marco(caja, { Nombre = "Cabecera", Tamano = UDim2.new(1, 0, 0, 26), Z = 4 })
	P.Marco(cabecera, {
		Tamano = UDim2.new(1, 0, 0, 1),
		Posicion = UDim2.fromScale(0, 1),
		Color = C.Acento,
		Transparencia = A.BordeSutil,
		Z = 4,
	})
	P.Etiqueta(cabecera, "RANGO", { Posicion = UDim2.new(0, 12, 0.5, 0), Ancla = Vector2.new(0, 0.5), Z = 5 })
	P.Etiqueta(
		cabecera,
		"NOMBRE",
		{ Posicion = UDim2.new(0, 12 + col.Rango, 0.5, 0), Ancla = Vector2.new(0, 0.5), Z = 5 }
	)
	P.Etiqueta(
		cabecera,
		"NIVEL",
		{ Posicion = UDim2.new(1, -(12 + col.Estado + col.Nivel / 2), 0.5, 0), Ancla = Vector2.new(0.5, 0.5), Z = 5 }
	)
	P.Etiqueta(
		cabecera,
		"ESTADO",
		{ Posicion = UDim2.new(1, -(12 + col.Estado), 0.5, 0), Ancla = Vector2.new(0, 0.5), Z = 5 }
	)

	local lista = P.Crear("ScrollingFrame", {
		Name = "Filas",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 1, -26),
		Position = UDim2.fromOffset(0, 26),
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 4,
		ScrollBarImageColor3 = C.Acento,
		ScrollBarImageTransparency = 0.5,
		ZIndex = 4,
		Parent = caja,
	}) :: ScrollingFrame
	P.Lista(lista, Enum.FillDirection.Vertical, 0)
	for i, miembro in DatosDemo.Clan.Lista do
		FilaMiembro.Crear(lista, miembro, i)
	end
end

local function construirBotones(cuerpo: Frame)
	local fila = P.Marco(cuerpo, {
		Nombre = "Botones",
		Tamano = UDim2.fromOffset(600, 28),
		Posicion = UDim2.new(0, 12, 1, -12),
		Ancla = Vector2.new(0, 1),
		Z = 3,
	})
	P.Lista(fila, Enum.FillDirection.Horizontal, 8)
	local miRango = "Miembro"
	for _, miembro in DatosDemo.Clan.Lista do
		if miembro.Tu then
			miRango = miembro.Rango
		end
	end
	P.Boton(fila, {
		Texto = "INVITAR",
		Estilo = "Cian",
		Tamano = UDim2.fromOffset(120, 28),
		Orden = 1,
		Z = 4,
		AlPulsar = function()
			-- TODO(servidor): lista de jugadores del servidor y petición de invitación.
			ctx.Notificar({
				Titulo = "Invitar",
				Texto = "Elige a un jugador del servidor",
				Color = C.Acento,
				Icono = "sidebar_clan",
			})
		end,
	})
	if miRango ~= "Miembro" then
		P.Boton(fila, {
			Texto = "CONFIGURAR",
			Estilo = "Gris",
			Tamano = UDim2.fromOffset(130, 28),
			Orden = 2,
			Z = 4,
			AlPulsar = function()
				ctx.Notificar({
					Titulo = "Configurar clan",
					Texto = "Nombre, lema, estandarte y permisos",
					Color = C.Gris,
					Icono = "sidebar_ajustes",
				})
			end,
		})
	end
	P.Boton(fila, {
		Texto = "DEJAR CLAN",
		Estilo = "Rojo",
		Tamano = UDim2.fromOffset(120, 28),
		Orden = 3,
		Z = 4,
		AlPulsar = function()
			local sucesor = if DatosDemo.Clan.Lista[2] then DatosDemo.Clan.Lista[2].Nombre else "otro miembro"
			Modal.Confirmar({
				Titulo = "¿DEJAR EL CLAN?",
				Texto = if miRango == "Lider"
					then `Saldrás de <b>{DatosDemo.Clan.Nombre}</b>. Como eres el líder, el liderazgo pasará a <b>{sucesor}</b>.`
					else `Saldrás de <b>{DatosDemo.Clan.Nombre}</b>.`,
				Color = C.Peligro,
				TextoSi = "DEJAR CLAN",
				EstiloSi = "Rojo",
				AlSi = function()
					ctx.Notificar({
						Titulo = "Dejar el clan",
						Texto = "Pendiente del servidor (demo)",
						Color = C.Peligro,
						Icono = "sidebar_clan",
					})
				end,
			})
		end,
	})
end

local function construirLado(cuerpo: Frame)
	local clan = DatosDemo.Clan
	local caja = P.Caja(cuerpo, {
		Nombre = "Resumen",
		Tamano = UDim2.new(0, 224, 1, -24),
		Posicion = UDim2.new(1, -12, 0, 12),
		Ancla = Vector2.new(1, 0),
		Z = 3,
	})
	P.Relleno(caja, 12)
	P.Lista(caja, Enum.FillDirection.Vertical, 8)
	P.Etiqueta(caja, "RESUMEN", { Orden = 1, Z = 4 })
	type Dato = { Icono: string, Color: Color3, Valor: string, Nombre: string }
	local datos: { Dato } = {
		{ Icono = "sidebar_ranked", Color = C.Dorado, Valor = `#{clan.Ranking}`, Nombre = "RANKING DE CLANES" },
		{ Icono = "sidebar_mapa", Color = C.Aguante, Valor = clan.Planeta, Nombre = "PLANETA BASE" },
		{ Icono = "stat_habilidad", Color = C.Acento, Valor = P.Numero(clan.Puntos), Nombre = "PUNTOS DE CLAN" },
	}
	for i, d in datos do
		local fila = P.Marco(caja, {
			Tamano = UDim2.new(1, 0, 0, 38),
			Color = C.FondoProfundo,
			Transparencia = 0.55,
			Radio = UDim.new(0, 6),
			Orden = 1 + i,
			Z = 4,
		})
		IconBuilder.Icono(
			fila,
			d.Icono,
			{ Tamano = 16, Color = d.Color, Posicion = UDim2.new(0, 10, 0.5, 0), Ancla = Vector2.new(0, 0.5), Z = 5 }
		)
		P.Texto(fila, {
			Texto = d.Valor,
			Tamano = Theme.Texto.Medio,
			Fuente = Theme.Fuentes.Negrita,
			Posicion = UDim2.fromOffset(34, 7),
			Z = 5,
		})
		P.Texto(fila, {
			Texto = d.Nombre,
			Tamano = Theme.Texto.Mini,
			Fuente = Theme.Fuentes.Negrita,
			Color = C.TextoSecundario,
			Transparencia = A.TextoSecundario,
			Espaciado = true,
			Posicion = UDim2.fromOffset(34, 22),
			Z = 5,
		})
	end
	P.Etiqueta(caja, "ACTIVIDAD", { Orden = 10, Z = 4 })
	for i, a in clan.Actividad do
		local fila = P.Marco(caja, { Tamano = UDim2.new(1, 0, 0, 28), Orden = 10 + i, Z = 4 })
		P.Texto(fila, {
			Texto = `<font color="#{C.Acento:ToHex()}"><b>{a.Quien}</b></font> {a.Que}`,
			Rico = true,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Medio,
			Color = C.TextoPrincipal,
			Transparencia = A.TextoMedio,
			Z = 5,
		})
		P.Texto(fila, {
			Texto = a.Cuando,
			Tamano = Theme.Texto.Micro + 0.5,
			Fuente = Theme.Fuentes.Titulo,
			Color = C.TextoSecundario,
			Transparencia = A.TextoSecundario,
			Posicion = UDim2.fromOffset(0, 13),
			Z = 5,
		})
		P.Marco(fila, {
			Tamano = UDim2.new(1, 0, 0, 1),
			Posicion = UDim2.fromScale(0, 1),
			Color = C.Blanco,
			Transparencia = 0.96,
			Z = 5,
		})
	end
end

function PanelClan.Iniciar(contexto: Contexto.Contexto)
	ctx = contexto
	ventana = Ventana.Crear(contexto.Raiz, {
		Nombre = "Clan",
		Titulo = "TRIPULACIÓN",
		Subtitulo = "TU CLAN",
		Icono = "sidebar_clan",
		AlCerrar = contexto.Cerrar,
	})
	construirCabecera(ventana.Cuerpo)
	construirTabla(ventana.Cuerpo)
	construirBotones(ventana.Cuerpo)
	construirLado(ventana.Cuerpo)
end

function PanelClan.Mostrar()
	ventana.Abrir()
end

function PanelClan.Ocultar()
	ventana.Cerrar()
end

return PanelClan
