--!strict
--[[
	Modelo (Tiendas): construye por código el local de una tienda humana con su persiana metálica.

	El local mira hacia los clientes: `origen` es un CFrame en el suelo, en el centro del escaparate, con su LookVector
	apuntando a la calle. Por dentro (detrás del escaparate) están el mostrador, las estanterías con género y la luz.

	Piezas que usa el cliente para animar la persiana (Cliente/Tiendas/Persianas), con estos nombres:
	  Origen            parte invisible en `origen` (PrimaryPart): todas las medidas se toman respecto a ella
	  Cortina/          las piezas que se mueven: Lama1..LamaN, Barra (la barra inferior) y Rotulo ("CERRADO" pintado)
	                    El servidor las deja en la posición de CERRADA y nunca las mueve; el cliente las desplaza hacia
	                    arriba según la animación y oculta las que quedan dentro del cajón. Empiezan transparentes para
	                    que, si el cliente aún no las ha colocado, no tapen el escaparate.
	  Cajon             el cajón del rodillo; su cara inferior es donde se esconden las lamas
	  Baliza            luz de aviso sobre el cajón
	  Estado            cartel "ABIERTO" / "CERRADO"
	  ZonaPolvo         caja invisible en el suelo, bajo la persiana: de ahí salen el polvo y las chispas del impacto
	  Mostrador         donde se compra: lleva el ProximityPrompt y es el punto desde el que se mide el alcance

	Atributos del modelo: Config.AtributoTiendaId (id en Datos/Catalogo) y Config.AtributoPersiana (estado de la persiana).
	Atributos de Cortina: Recorrido (cuánto sube) y AlturaCajon (altura de la cara inferior del cajón), en studs desde Origen.
]]

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage.Shared
local Catalogo = require(Shared.Tiendas.Datos.Catalogo)
local Config = require(Shared.Tiendas.Config)
local DatosPersiana = require(Shared.Tiendas.Datos.Persiana)
local Objetos = require(Shared.Exploracion.Datos.Objetos)

local Modelo = {}

local function hex(texto: string): Color3
	return Color3.fromHex(texto)
end

-- Colores del local (ciudad humana: luminosa, limpia, con el azul del bando).
local COLOR_PARED = Color3.fromRGB(226, 222, 212)
local COLOR_ZOCALO = Color3.fromRGB(120, 126, 140)
local COLOR_SUELO = Color3.fromRGB(176, 172, 164)
local COLOR_ACENTO = Color3.fromRGB(70, 140, 255)
local COLOR_MADERA = Color3.fromRGB(140, 98, 64)
local COLOR_METAL = Color3.fromRGB(60, 64, 74)

type Opciones = {
	Color: Color3,
	Material: Enum.Material,
	Colision: boolean?,
	Transparencia: number?,
	Forma: Enum.PartType?,
}

-- Crea una parte anclada en la posición `local` (relativa a `origen`) con la rotación de `origen`.
local function parte(
	padre: Instance,
	origen: CFrame,
	nombre: string,
	tamano: Vector3,
	posicionLocal: Vector3,
	opciones: Opciones
): Part
	local p = Instance.new("Part")
	p.Name = nombre
	p.Size = tamano
	p.CFrame = origen * CFrame.new(posicionLocal)
	p.Color = opciones.Color
	p.Material = opciones.Material
	p.Anchored = true
	p.CanCollide = if opciones.Colision == nil then true else opciones.Colision
	p.Transparency = opciones.Transparencia or 0
	if opciones.Forma then
		p.Shape = opciones.Forma
	end
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = padre
	return p
end

-- Un SurfaceGui con un texto grande en la cara delantera (la que mira a la calle) de `soporte`.
local function rotulo(soporte: BasePart, texto: string, color: Color3, fondo: Color3?, nombre: string?): TextLabel
	local gui = Instance.new("SurfaceGui")
	gui.Name = nombre or "Texto"
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 40
	gui.LightInfluence = 0
	gui.Brightness = 2
	gui.Parent = soporte

	local etiqueta = Instance.new("TextLabel")
	etiqueta.Name = "Etiqueta"
	etiqueta.Size = UDim2.fromScale(1, 1)
	etiqueta.BackgroundTransparency = if fondo then 0 else 1
	etiqueta.BackgroundColor3 = fondo or Color3.new()
	etiqueta.Text = texto
	etiqueta.TextColor3 = color
	etiqueta.TextScaled = true
	etiqueta.Font = Enum.Font.GothamBlack
	etiqueta.Parent = gui
	local relleno = Instance.new("UIPadding")
	relleno.PaddingLeft = UDim.new(0.04, 0)
	relleno.PaddingRight = UDim.new(0.04, 0)
	relleno.PaddingTop = UDim.new(0.12, 0)
	relleno.PaddingBottom = UDim.new(0.12, 0)
	relleno.Parent = etiqueta
	return etiqueta
end

-- La persiana: cajón, guías, lamas, barra, rótulo, baliza y la zona del polvo.
local function construirPersiana(modelo: Model, origen: CFrame)
	local medidas = DatosPersiana.Medidas
	local colores = DatosPersiana.Colores
	local ancho, alto = medidas.AnchoHueco, medidas.AltoHueco
	local zPersiana = -0.55 -- delante del plano de la fachada (z = 0)

	-- Cajón del rodillo: su cara inferior está a la altura del hueco. Más profundo que las lamas, para taparlas.
	local cajon = parte(
		modelo,
		origen,
		"Cajon",
		Vector3.new(ancho + 1.4, 1.7, 1.5),
		Vector3.new(0, alto + 0.85, -0.65),
		{ Color = hex(colores.Cajon), Material = Enum.Material.DiamondPlate }
	)
	cajon.CastShadow = true

	-- Guías laterales.
	for _, lado in { -1, 1 } do
		parte(
			modelo,
			origen,
			"Guia",
			Vector3.new(0.35, alto, 0.6),
			Vector3.new(lado * (ancho / 2 + 0.1), alto / 2, zPersiana),
			{ Color = COLOR_METAL, Material = Enum.Material.Metal }
		)
	end

	local cortina = Instance.new("Folder")
	cortina.Name = "Cortina"
	cortina.Parent = modelo
	cortina:SetAttribute("Recorrido", alto - medidas.AltoBarra)
	cortina:SetAttribute("AlturaCajon", alto)

	-- Lamas, alternando dos tonos de acero. Empiezan transparentes (ver la cabecera).
	local altoLama = (alto - medidas.AltoBarra) / medidas.Lamas
	for indice = 1, medidas.Lamas do
		local y = alto - altoLama * (indice - 0.5)
		local lama = parte(
			cortina,
			origen,
			`Lama{indice}`,
			Vector3.new(ancho, altoLama * 0.94, medidas.GrosorLama),
			Vector3.new(0, y, zPersiana),
			{
				Color = hex(if indice % 2 == 0 then colores.LamaOscura else colores.Lama),
				Material = Enum.Material.CorrodedMetal,
				Colision = false,
				Transparencia = 1,
			}
		)
		lama.CanQuery = false
		lama.CanTouch = false
	end

	local barra = parte(
		cortina,
		origen,
		"Barra",
		Vector3.new(ancho, medidas.AltoBarra, medidas.GrosorLama + 0.2),
		Vector3.new(0, medidas.AltoBarra / 2, zPersiana),
		{ Color = hex(colores.Barra), Material = Enum.Material.Metal, Colision = false, Transparencia = 1 }
	)
	barra.CanQuery = false
	barra.CanTouch = false
	-- Asa de la barra.
	local asa = parte(
		cortina,
		origen,
		"Asa",
		Vector3.new(2.2, 0.25, 0.25),
		Vector3.new(0, medidas.AltoBarra / 2, zPersiana - 0.4),
		{ Color = COLOR_METAL, Material = Enum.Material.Metal, Colision = false, Transparencia = 1 }
	)
	asa.CanQuery = false
	asa.CanTouch = false

	-- "CERRADO" pintado sobre la persiana (una superficie transparente con el texto).
	local pintura = parte(
		cortina,
		origen,
		"Rotulo",
		Vector3.new(ancho * 0.82, 2.4, 0.05),
		Vector3.new(0, alto * 0.52, zPersiana - medidas.GrosorLama / 2 - 0.04),
		{ Color = Color3.new(), Material = Enum.Material.SmoothPlastic, Colision = false, Transparencia = 1 }
	)
	pintura.CanQuery = false
	pintura.CanTouch = false
	local textoPintado = rotulo(pintura, DatosPersiana.Textos.RotuloPersiana, hex(colores.Cerrado), nil, "Pintura")
	textoPintado.Font = Enum.Font.Arcade
	;(textoPintado.Parent :: SurfaceGui).Enabled = false

	-- Baliza de aviso sobre el cajón (apagada: la enciende el cliente).
	local baliza = parte(
		modelo,
		origen,
		"Baliza",
		Vector3.new(0.9, 1, 0.9),
		Vector3.new(-(ancho / 2 - 0.4), alto + 2.2, -0.9),
		{ Color = hex(colores.Cerrado):Lerp(Color3.new(), 0.6), Material = Enum.Material.Glass, Colision = false }
	)
	baliza.Shape = Enum.PartType.Cylinder
	baliza.CFrame = baliza.CFrame * CFrame.Angles(0, 0, math.pi / 2)
	local luz = Instance.new("PointLight")
	luz.Name = "Luz"
	luz.Color = hex(colores.Cerrado)
	luz.Range = DatosPersiana.Baliza.Alcance
	luz.Brightness = 0
	luz.Enabled = false
	luz.Parent = baliza

	-- Zona del polvo: bajo la persiana, a ras de suelo.
	local polvo = parte(
		modelo,
		origen,
		"ZonaPolvo",
		Vector3.new(ancho, 0.3, 1.2),
		Vector3.new(0, 0.2, zPersiana - 0.4),
		{ Color = Color3.new(), Material = Enum.Material.SmoothPlastic, Colision = false, Transparencia = 1 }
	)
	polvo.CanQuery = false
	polvo.CanTouch = false
end

-- Estanterías del fondo con cajas del color de cada material.
local function construirEstanterias(modelo: Model, origen: CFrame)
	local colores = {}
	for _, id in Objetos.Orden do
		table.insert(colores, hex(Objetos.Lista[id].Color))
	end
	for nivel = 1, 3 do
		local y = 1.4 + (nivel - 1) * 2.6
		parte(
			modelo,
			origen,
			"Balda",
			Vector3.new(18, 0.25, 2),
			Vector3.new(0, y, 10.8),
			{ Color = COLOR_MADERA, Material = Enum.Material.WoodPlanks }
		)
		for columna = 1, 8 do
			local color = colores[((nivel * 3 + columna) % #colores) + 1]
			local tamano = if (columna + nivel) % 3 == 0 then Vector3.new(1.4, 1.6, 1.4) else Vector3.new(1.6, 1.2, 1.4)
			local caja = parte(
				modelo,
				origen,
				"Caja",
				tamano,
				Vector3.new(-7.9 + (columna - 1) * 2.25, y + 0.125 + tamano.Y / 2, 10.8),
				{ Color = color, Material = Enum.Material.SmoothPlastic, Colision = false }
			)
			caja.CanQuery = false
		end
	end
end

--[[
	Construye el local de la tienda `idTienda` (un id de Datos/Catalogo.Tiendas) en `origen` y lo devuelve sin padre.
	ServicioTiendas.CrearTienda lo registra, le pone el ProximityPrompt y lo coloca en el mundo.
]]
function Modelo.Construir(idTienda: string, origen: CFrame): Model
	local tienda = Catalogo.Tiendas[idTienda]
	assert(tienda ~= nil, `La tienda '{idTienda}' no está en Tiendas/Datos/Catalogo`)
	local medidas = DatosPersiana.Medidas
	local ancho, alto = medidas.AnchoHueco, medidas.AltoHueco
	local altoLocal = alto + 3.5
	local mitad = ancho / 2 + 3.5 -- media anchura exterior del local

	local modelo = Instance.new("Model")
	modelo.Name = `Tienda_{idTienda}`
	modelo.ModelStreamingMode = Enum.ModelStreamingMode.Atomic -- la persiana y su cajón llegan siempre juntos
	modelo:SetAttribute(Config.AtributoTiendaId, idTienda)
	modelo:SetAttribute(Config.AtributoPersiana, false)

	local ancla = parte(
		modelo,
		origen,
		"Origen",
		Vector3.one * 0.2,
		Vector3.zero,
		{ Color = Color3.new(), Material = Enum.Material.SmoothPlastic, Colision = false, Transparencia = 1 }
	)
	ancla.CanQuery = false
	ancla.CanTouch = false
	modelo.PrimaryPart = ancla

	-- Suelo (con una acera delante) y estructura.
	parte(
		modelo,
		origen,
		"Suelo",
		Vector3.new(mitad * 2, 0.4, 17),
		Vector3.new(0, -0.2, 5),
		{ Color = COLOR_SUELO, Material = Enum.Material.Pavement }
	)
	parte(
		modelo,
		origen,
		"ParedFondo",
		Vector3.new(mitad * 2, altoLocal, 1),
		Vector3.new(0, altoLocal / 2, 12.5),
		{ Color = COLOR_PARED, Material = Enum.Material.Plaster }
	)
	for _, lado in { -1, 1 } do
		parte(
			modelo,
			origen,
			"ParedLateral",
			Vector3.new(1, altoLocal, 13),
			Vector3.new(lado * (mitad - 0.5), altoLocal / 2, 6),
			{ Color = COLOR_PARED, Material = Enum.Material.Plaster }
		)
		-- Pilares de la fachada, a los lados del hueco, con zócalo.
		local anchoPilar = mitad - ancho / 2 - 0.25
		parte(
			modelo,
			origen,
			"Pilar",
			Vector3.new(anchoPilar, altoLocal, 1),
			Vector3.new(lado * (ancho / 2 + 0.25 + anchoPilar / 2), altoLocal / 2, 0),
			{ Color = COLOR_PARED, Material = Enum.Material.Plaster }
		)
		parte(
			modelo,
			origen,
			"Zocalo",
			Vector3.new(anchoPilar + 0.1, 1.2, 1.1),
			Vector3.new(lado * (ancho / 2 + 0.25 + anchoPilar / 2), 0.6, 0),
			{ Color = COLOR_ZOCALO, Material = Enum.Material.Slate }
		)
	end
	-- Dintel sobre el hueco y techo.
	parte(
		modelo,
		origen,
		"Dintel",
		Vector3.new(ancho + 0.6, altoLocal - alto, 1),
		Vector3.new(0, alto + (altoLocal - alto) / 2, 0),
		{ Color = COLOR_PARED, Material = Enum.Material.Plaster }
	)
	parte(
		modelo,
		origen,
		"Techo",
		Vector3.new(mitad * 2 + 0.6, 0.8, 14),
		Vector3.new(0, altoLocal + 0.4, 6),
		{ Color = COLOR_ZOCALO, Material = Enum.Material.Concrete }
	)

	-- Toldo a rayas con el azul de los Humanos, inclinado hacia la calle.
	local franjas = 7
	local anchoFranja = (mitad * 2) / franjas
	for indice = 1, franjas do
		local x = -mitad + anchoFranja * (indice - 0.5)
		local franja = parte(
			modelo,
			origen,
			"Toldo",
			Vector3.new(anchoFranja, 0.2, 4),
			Vector3.new(x, altoLocal - 0.2, -2.1),
			{
				Color = if indice % 2 == 0 then Color3.fromRGB(245, 245, 250) else COLOR_ACENTO,
				Material = Enum.Material.Fabric,
				Colision = false,
			}
		)
		franja.CFrame = franja.CFrame * CFrame.Angles(math.rad(-16), 0, 0)
	end

	-- Letrero con el nombre de la tienda, sobre el cajón.
	local letrero = parte(
		modelo,
		origen,
		"Letrero",
		Vector3.new(ancho - 1, 1.5, 0.3),
		Vector3.new(0, alto + 2.65, -0.7),
		{ Color = Color3.fromRGB(18, 22, 36), Material = Enum.Material.SmoothPlastic }
	)
	rotulo(letrero, string.upper(tienda.Nombre), Color3.fromRGB(235, 240, 255), Color3.fromRGB(18, 22, 36))

	-- Cartel de estado en el pilar derecho.
	local estado = parte(
		modelo,
		origen,
		"Estado",
		Vector3.new(2.6, 0.9, 0.2),
		Vector3.new(ancho / 2 + 1.9, 6.2, -0.62),
		{ Color = Color3.fromRGB(12, 14, 20), Material = Enum.Material.SmoothPlastic }
	)
	rotulo(estado, DatosPersiana.Textos.Abierto, hex(DatosPersiana.Colores.Abierto), Color3.fromRGB(12, 14, 20))

	-- Interior: mostrador de lado a lado (no se puede entrar), estanterías y luz.
	local mostrador = parte(
		modelo,
		origen,
		"Mostrador",
		Vector3.new(ancho, 3.4, 1.8),
		Vector3.new(0, 1.7, 2.2),
		{ Color = COLOR_PARED:Lerp(COLOR_ACENTO, 0.15), Material = Enum.Material.SmoothPlastic }
	)
	parte(
		modelo,
		origen,
		"Encimera",
		Vector3.new(ancho + 0.2, 0.25, 2.1),
		Vector3.new(0, 3.5, 2.2),
		{ Color = COLOR_MADERA, Material = Enum.Material.Wood }
	)
	-- Franja luminosa del mostrador.
	parte(
		modelo,
		origen,
		"FranjaMostrador",
		Vector3.new(ancho - 0.4, 0.2, 0.1),
		Vector3.new(0, 2.6, 1.28),
		{ Color = COLOR_ACENTO, Material = Enum.Material.Neon, Colision = false }
	)
	construirEstanterias(modelo, origen)

	local lampara = parte(
		modelo,
		origen,
		"Lampara",
		Vector3.new(6, 0.25, 1),
		Vector3.new(0, altoLocal - 0.2, 6),
		{ Color = Color3.fromRGB(255, 244, 220), Material = Enum.Material.Neon, Colision = false }
	)
	local luz = Instance.new("SurfaceLight")
	luz.Face = Enum.NormalId.Bottom
	luz.Color = Color3.fromRGB(255, 236, 205)
	luz.Brightness = 2.5
	luz.Range = 16
	luz.Angle = 120
	luz.Parent = lampara

	construirPersiana(modelo, origen)
	return modelo
end

return Modelo
