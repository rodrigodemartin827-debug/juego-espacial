--!strict
--[[
	Tooltip: ficha flotante de un objeto (inventario y slots del muñeco).

	  ┌──────────────────────────────┐   borde del color de la rareza
	  │ [img] (estrella) Espada de Plasma │   nombre en el color de la rareza (12, negrita)
	  │       Raro | Nivel 45         │
	  │ DMG ............... 168 (+29) │   stats con su color
	  │ Descripción (9, gris)         │
	  │ Pasiva: ... (cian)            │
	  │ [EQUIPAR] [TIRAR] [INFO]      │   solo cuando el objeto está seleccionado
	  └──────────────────────────────┘

	Aparece al lado del objeto (a la derecha, o a la izquierda si no cabe) sin salirse de la pantalla, con escala
	0,95 → 1 y un fundido de 0,15 s. Solo hay uno, reutilizado.
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local IconBuilder = require(script.Parent.Parent.Iconos.IconBuilder)
local P = require(script.Parent.Primitivas)
local EstadoUI = require(script.Parent.Parent.EstadoUI)

local C = Theme.Colores
local A = Theme.Alpha

local Tooltip = {}

local ANCHO = 214

export type Accion = { Texto: string, Estilo: P.EstiloBoton, AlPulsar: () -> () }

local lienzo: Frame? = nil
local aUnidades: ((Vector2) -> Vector2)? = nil
local grupo: CanvasGroup? = nil
local visible = false

-- Prepara el tooltip dentro del lienzo de los menús.
function Tooltip.Iniciar(raiz: Frame, convertir: (Vector2) -> Vector2)
	lienzo = raiz
	aUnidades = convertir
	local g = P.Grupo(raiz, {
		Nombre = "Tooltip",
		Tamano = UDim2.fromOffset(ANCHO, 0),
		Color = C.FondoProfundo,
		Transparencia = 0.03,
		Z = 60,
	})
	g.AutomaticSize = Enum.AutomaticSize.Y
	g.Visible = false
	P.Esquinas(g, Theme.Tamanos.BorderRadius)
	P.Relleno(g, 10)
	P.Lista(g, Enum.FillDirection.Vertical, 7)
	grupo = g
end

local function limpiar(g: CanvasGroup)
	for _, hijo in g:GetChildren() do
		if not (hijo:IsA("UIPadding") or hijo:IsA("UIListLayout") or hijo:IsA("UICorner")) then
			hijo:Destroy()
		end
	end
end

-- Enseña la ficha de `objeto` junto a `ancla`. Con `acciones`, añade los botones al pie.
function Tooltip.Mostrar(objeto: EstadoUI.ObjetoUI, ancla: GuiObject, acciones: { Accion }?)
	local g, convertir, raiz = grupo, aUnidades, lienzo
	if g == nil or convertir == nil or raiz == nil then
		return
	end
	limpiar(g)
	local rareza = Theme.Rareza[objeto.Rareza] or Theme.Rareza.Comun
	P.Borde(g, rareza.Color, 0, Theme.Tamanos.TrazoActivo)

	-- Cabecera: imagen, nombre y rareza.
	local cabecera = P.Marco(g, { Nombre = "Cabecera", Tamano = UDim2.new(1, 0, 0, 40), Orden = 1, Z = 61 })
	local marcoImagen = P.Marco(cabecera, {
		Nombre = "Imagen",
		Tamano = UDim2.fromOffset(40, 40),
		Color = C.Fondo1,
		Transparencia = 0.2,
		Radio = UDim.new(0, 6),
		Z = 61,
	})
	P.Borde(marcoImagen, rareza.Color, 0.3)
	IconBuilder.Arte(marcoImagen, objeto.Arte, {
		Tamano = UDim2.new(1, -6, 1, -6),
		Posicion = UDim2.fromScale(0.5, 0.5),
		Ancla = Vector2.new(0.5, 0.5),
		Z = 62,
		ColorRespaldo = rareza.Color,
	})
	-- Legendarios y míticos llevan una estrella (icono custom) delante del nombre.
	local destacado = objeto.Rareza == "Legendario" or objeto.Rareza == "Mitico"
	if destacado then
		IconBuilder.Icono(
			cabecera,
			"ui_estrella",
			{ Tamano = 10, Color = rareza.Color, Posicion = UDim2.fromOffset(48, 6), Z = 62 }
		)
	end
	P.Texto(cabecera, {
		Texto = objeto.Nombre,
		Tamano = Theme.Texto.Titulo,
		Fuente = Theme.Fuentes.Negrita,
		Color = rareza.Color,
		Caja = UDim2.new(1, if destacado then -61 else -48, 0, 16),
		Posicion = UDim2.fromOffset(if destacado then 61 else 48, 3),
		Envolver = false,
		Z = 62,
	})
	local partes = { rareza.Nombre }
	if objeto.Nivel then
		table.insert(partes, `Nivel {objeto.Nivel}`)
	end
	if objeto.Cantidad then
		table.insert(partes, `x{objeto.Cantidad}`)
	end
	P.Texto(cabecera, {
		Texto = table.concat(partes, " | "),
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Titulo,
		Color = C.TextoSecundario,
		Transparencia = A.TextoSecundario,
		Posicion = UDim2.fromOffset(48, 22),
		Z = 62,
	})

	-- Estadísticas.
	if objeto.Stats then
		for i, fila in objeto.Stats do
			local info = Theme.Stats[fila.Stat]
			local linea = P.Marco(g, { Nombre = "Stat", Tamano = UDim2.new(1, 0, 0, 12), Orden = 1 + i, Z = 61 })
			P.Texto(linea, {
				Texto = fila.Etiqueta,
				Tamano = Theme.Texto.Pequeno,
				Fuente = Theme.Fuentes.Titulo,
				Color = C.TextoPrincipal,
				Transparencia = A.TextoMedio,
				Espaciado = true,
				Z = 62,
			})
			local valor = P.Decimal(fila.Valor)
			if fila.Bonus > 0 then
				valor ..= ` <font transparency="0.4">(+{P.Decimal(fila.Bonus)})</font>`
			end
			P.Texto(linea, {
				Texto = valor,
				Rico = true,
				Tamano = Theme.Texto.Pequeno,
				Fuente = Theme.Fuentes.Negrita,
				Color = if info then info.Color else C.TextoPrincipal,
				Posicion = UDim2.fromScale(1, 0),
				Ancla = Vector2.new(1, 0),
				Z = 62,
			})
		end
	end

	P.Texto(g, {
		Nombre = "Descripcion",
		Texto = objeto.Descripcion,
		Tamano = Theme.Texto.Pequeno,
		Fuente = Theme.Fuentes.Cuerpo,
		Color = C.TextoPrincipal,
		Transparencia = 0.45,
		Caja = UDim2.new(1, 0, 0, 0),
		Envolver = true,
		Orden = 20,
		Z = 62,
	}).AutomaticSize =
		Enum.AutomaticSize.Y
	if objeto.Pasiva then
		P.Texto(g, {
			Nombre = "Pasiva",
			Texto = `Pasiva: {objeto.Pasiva}`,
			Tamano = Theme.Texto.Pequeno,
			Fuente = Theme.Fuentes.Medio,
			Color = C.Acento,
			Caja = UDim2.new(1, 0, 0, 0),
			Envolver = true,
			Orden = 21,
			Z = 62,
		}).AutomaticSize =
			Enum.AutomaticSize.Y
	end

	if acciones and #acciones > 0 then
		local fila = P.Marco(g, { Nombre = "Acciones", Tamano = UDim2.new(1, 0, 0, 21), Orden = 30, Z = 61 })
		P.Lista(fila, Enum.FillDirection.Horizontal, 5)
		local ancho = (ANCHO - 20 - 5 * (#acciones - 1)) / #acciones
		for i, accion in acciones do
			P.Boton(fila, {
				Texto = accion.Texto,
				Estilo = accion.Estilo,
				Tamano = UDim2.fromOffset(ancho, 21),
				TamanoTexto = Theme.Texto.Pequeno,
				Orden = i,
				Z = 62,
				AlPulsar = accion.AlPulsar,
			})
		end
	end

	-- Posición: a la derecha del ancla, o a la izquierda si no cabe; nunca fuera del lienzo.
	local esquina = convertir(ancla.AbsolutePosition)
	local tamanoAncla = ancla.AbsoluteSize / (raiz.AbsoluteSize.X / raiz.Size.X.Offset)
	local x = esquina.X + tamanoAncla.X + 8
	if x + ANCHO > raiz.Size.X.Offset - 10 then
		x = esquina.X - ANCHO - 8
	end
	g.Position = UDim2.fromOffset(x, esquina.Y)
	if not visible then
		UITweens.Aparecer(g)
	end
	visible = true
	-- La altura real se conoce un fotograma después (AutomaticSize): se corrige para que no se salga por abajo.
	task.defer(function()
		local alto = g.AbsoluteSize.Y / (raiz.AbsoluteSize.X / raiz.Size.X.Offset)
		local maxY = raiz.Size.Y.Offset - 10 - alto
		if esquina.Y > maxY then
			g.Position = UDim2.fromOffset(x, math.max(8, maxY))
		end
	end)
end

function Tooltip.Ocultar()
	local g = grupo
	if g == nil or not visible then
		return
	end
	visible = false
	UITweens.Fundir(g, false, Theme.Tweens.Tooltip)
end

function Tooltip.EstaVisible(): boolean
	return visible
end

return Tooltip
