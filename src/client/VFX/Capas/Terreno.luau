--!strict
--[[
	Capas que tocan el suelo: "Escombros" y "Crater".

	"Escombros"  Trozos de roca que salen del suelo, vuelan y caen (o flotan, o son atraídos hacia un punto).
	  Cantidad        trozos (se reduce en móviles lentos)
	  RadioMin, Radio anillo del suelo donde nacen
	  Tamano          { mín, máx } de cada trozo
	  Impulso         { mín, máx } velocidad inicial hacia arriba
	  Dispersion      { mín, máx } velocidad horizontal hacia fuera
	  Gravedad        multiplicador de la gravedad (1 normal, 0 flotan, negativo = suben)
	  Atraccion       fuerza con la que son atraídos al ancla (agujero negro); 0 = ninguna
	  Vida            segundos antes de encogerse y desaparecer
	  Color, Material ("Roca"), Neon (true = brillan), Giro (velocidad de giro, rad/s)
	  Emerge          si es true nacen medio enterrados, como arrancados del suelo
	  Libre           si es true no hay suelo (espacio): nacen alrededor del ancla y salen disparados en todas
	                  direcciones con velocidad `Dispersion`, sin `Impulso` ni rebote

	"Crater"  Cráter temporal: disco oscuro, resplandor, grietas luminosas y rocas levantadas en el borde.
	  Radio, Duracion (segundos visible), Desvanecer (segundos de fundido final)
	  Grietas         número de grietas radiales luminosas
	  Rocas           número de rocas en el borde
	  Color (resplandor y grietas), ColorSuelo (disco), Material
]]

local Actores = require(script.Parent.Parent.Actores)
local Calidad = require(script.Parent.Parent.Calidad)
local Pool = require(script.Parent.Parent.Pool)
local Utiles = require(script.Parent.Parent.Utiles)

local Terreno = {}

-- Altura del suelo para una capa: la del punto de impacto, o la que hay bajo su ancla si es otra (p. ej. el lanzador).
local function alturaSuelo(capa: any, ctx: any, centro: Vector3): number
	local ancla = capa.Anclaje
	if ancla == nil or ancla == "Suelo" or ancla == "Objetivo" then
		return ctx.SueloY
	end
	return (Utiles.Suelo(centro))
end

local GRAVEDAD = 130 -- studs/s² (algo más que la real, para que los escombros caigan con peso)

local MATERIALES: { [string]: Enum.Material } = {
	Roca = Enum.Material.Slate,
	Basalto = Enum.Material.Basalt,
	Neon = Enum.Material.Neon,
	Arena = Enum.Material.Sand,
}

type Trozo = {
	Parte: Part,
	Posicion: Vector3,
	Velocidad: Vector3,
	Giro: Vector3,
	Orientacion: CFrame,
	Tamano: number,
	Base: Vector3, -- tamaño completo del Part
	Reposo: boolean,
	Edad: number,
}

function Terreno.Escombros(capa: any, ctx: any)
	local factor = Calidad.Factor("Escombros")
	local cantidad = Utiles.Cantidad(capa.Cantidad or 12, factor)
	if cantidad == 0 then
		return
	end

	local centro = Utiles.Ancla(ctx, capa.Anclaje or "Suelo", capa.Desplazamiento).Position
	local sueloY = alturaSuelo(capa, ctx, centro)
	local radioMin: number = capa.RadioMin or 0
	local radio: number = capa.Radio or 8
	local gravedad: number = GRAVEDAD * (if capa.Gravedad ~= nil then capa.Gravedad else 1)
	local atraccion: number = capa.Atraccion or 0
	local vida: number = capa.Vida or 2
	local color = Utiles.Color(capa.Color or "Oscuro", ctx.Paleta)
	local material = if capa.Neon
		then Enum.Material.Neon
		else (MATERIALES[capa.Material or "Roca"] or Enum.Material.Slate)

	local trozos: { Trozo } = {}
	for _ = 1, cantidad do
		local angulo = Utiles.Azar:NextNumber(0, math.pi * 2)
		local distancia = Utiles.Azar:NextNumber(radioMin, radio)
		local tamano = Utiles.Elegir(capa.Tamano, 1.5)
		local posicion = Vector3.new(
			centro.X + math.cos(angulo) * distancia,
			sueloY + (if capa.Emerge then -tamano * 0.3 else tamano * 0.5),
			centro.Z + math.sin(angulo) * distancia
		)
		local fuera = Vector3.new(math.cos(angulo), 0, math.sin(angulo))
		local velocidad = fuera * Utiles.Elegir(capa.Dispersion, 4) + Vector3.yAxis * Utiles.Elegir(capa.Impulso, 30)
		if capa.Libre then
			-- En el espacio: una dirección al azar en 3D (esfera) desde el ancla.
			local cenit = Utiles.Azar:NextNumber(-1, 1)
			local radioHorizontal = math.sqrt(1 - cenit * cenit)
			local salida = Vector3.new(math.cos(angulo) * radioHorizontal, cenit, math.sin(angulo) * radioHorizontal)
			posicion = centro + salida * distancia
			velocidad = salida * Utiles.Elegir(capa.Dispersion, 20)
		end

		local parte = Pool.Parte("Bloque")
		local medidas =
			Vector3.new(tamano, tamano * Utiles.Azar:NextNumber(0.6, 1.1), tamano * Utiles.Azar:NextNumber(0.7, 1.2))
		parte.Size = medidas
		parte.Color = color
		parte.Material = material
		parte.Transparency = 0
		local orientacion = CFrame.Angles(
			Utiles.Azar:NextNumber(0, 6.28),
			Utiles.Azar:NextNumber(0, 6.28),
			Utiles.Azar:NextNumber(0, 6.28)
		)
		parte.CFrame = CFrame.new(posicion) * orientacion

		local giro = capa.Giro or 4
		table.insert(trozos, {
			Parte = parte,
			Posicion = posicion,
			Velocidad = velocidad,
			Giro = Vector3.new(
				Utiles.Azar:NextNumber(-giro, giro),
				Utiles.Azar:NextNumber(-giro, giro),
				Utiles.Azar:NextNumber(-giro, giro)
			),
			Orientacion = orientacion,
			Tamano = tamano,
			Base = medidas,
			Reposo = false,
			Edad = 0,
		})
	end

	local encogimiento = 0.5 -- segundos que tarda en encogerse al final
	local restantes = #trozos
	Actores.Agregar(function(dt)
		for _, trozo in trozos do
			if trozo.Parte.Parent == nil then
				continue
			end
			trozo.Edad += dt

			if not trozo.Reposo then
				local aceleracion = Vector3.new(0, -gravedad, 0)
				if atraccion > 0 then
					local hacia = centro + Vector3.new(0, 6, 0) - trozo.Posicion
					local distancia = math.max(hacia.Magnitude, 1)
					aceleracion += hacia.Unit * atraccion * (1 + 8 / distancia)
				end
				trozo.Velocidad += aceleracion * dt
				trozo.Posicion += trozo.Velocidad * dt

				-- Choca con el suelo: rebota un poco y se queda quieto.
				local altura = sueloY + trozo.Tamano * 0.35
				if trozo.Posicion.Y <= altura and trozo.Velocidad.Y < 0 and gravedad > 0 then
					trozo.Posicion = Vector3.new(trozo.Posicion.X, altura, trozo.Posicion.Z)
					if trozo.Velocidad.Magnitude < 12 then
						trozo.Reposo = true
					else
						trozo.Velocidad =
							Vector3.new(trozo.Velocidad.X * 0.5, -trozo.Velocidad.Y * 0.3, trozo.Velocidad.Z * 0.5)
					end
				end
				trozo.Orientacion = trozo.Orientacion
					* CFrame.Angles(trozo.Giro.X * dt, trozo.Giro.Y * dt, trozo.Giro.Z * dt)
			end

			local escala = 1
			if trozo.Edad > vida then
				escala = math.max(0, 1 - (trozo.Edad - vida) / encogimiento)
			end
			if escala <= 0 then
				Pool.Liberar(trozo.Parte)
				restantes -= 1
			else
				trozo.Parte.CFrame = CFrame.new(trozo.Posicion) * trozo.Orientacion
				if escala < 1 then
					trozo.Parte.Size = trozo.Base * escala
				end
			end
		end
		return restantes <= 0
	end)
end

function Terreno.Crater(capa: any, ctx: any)
	local factor = Calidad.Factor("Escombros")
	local centro = Utiles.Ancla(ctx, capa.Anclaje or "Suelo", capa.Desplazamiento).Position
	local sueloY = alturaSuelo(capa, ctx, centro)
	local radio: number = capa.Radio or 10
	local duracion: number = capa.Duracion or 5
	local fundido: number = capa.Desvanecer or 1.5
	local material = MATERIALES[capa.Material or "Basalto"] or Enum.Material.Basalt
	local base = Vector3.new(centro.X, sueloY + 0.1, centro.Z)

	local aLiberar: { Part } = {}
	local function registrar(parte: Part): Part
		table.insert(aLiberar, parte)
		return parte
	end

	-- Disco oscuro que "quema" el suelo: aparece de golpe y se agranda.
	local disco = registrar(Pool.Parte("Cilindro"))
	disco.Color = Utiles.Color(capa.ColorSuelo or "Oscuro", ctx.Paleta)
	disco.Material = material
	disco.Transparency = 0.1
	disco.CFrame = CFrame.new(base) * CFrame.Angles(0, 0, math.pi / 2)
	disco.Size = Vector3.new(0.2, radio * 0.6, radio * 0.6)
	Utiles.Tween(disco, 0.18, { Size = Vector3.new(0.2, radio * 2, radio * 2) }, "Quart")
	Utiles.Tween(disco, fundido, { Transparency = 1 }, "Lineal", true)

	-- Resplandor interior que se apaga despacio.
	local resplandor = registrar(Pool.Parte("Cilindro"))
	resplandor.Color = Utiles.Color(capa.Color or "Principal", ctx.Paleta)
	resplandor.Transparency = 0.35
	resplandor.CFrame = CFrame.new(base + Vector3.new(0, 0.06, 0)) * CFrame.Angles(0, 0, math.pi / 2)
	resplandor.Size = Vector3.new(0.15, radio * 0.4, radio * 0.4)
	Utiles.Tween(resplandor, 0.25, { Size = Vector3.new(0.15, radio * 1.5, radio * 1.5) }, "Quart")
	Utiles.Tween(resplandor, duracion * 0.7, { Transparency = 1 }, "Quad", true)

	-- Grietas luminosas que se abren desde el centro.
	local grietas = Utiles.Cantidad(capa.Grietas or 8, factor)
	for indice = 1, grietas do
		local angulo = (indice / grietas) * math.pi * 2 + Utiles.Azar:NextNumber(-0.2, 0.2)
		local largo = radio * Utiles.Azar:NextNumber(0.7, 1.15)
		local direccion = Vector3.new(math.cos(angulo), 0, math.sin(angulo))
		local grieta = registrar(Pool.Parte("Bloque"))
		grieta.Color = Utiles.Color(capa.Color or "Principal", ctx.Paleta)
		grieta.Transparency = 0.05
		grieta.Size = Vector3.new(Utiles.Azar:NextNumber(0.4, 0.9), 0.12, 0.5)
		grieta.CFrame = CFrame.lookAt(base + Vector3.new(0, 0.12, 0), base + direccion * 10)
		-- Crece hacia fuera: se va alargando y su centro se desplaza.
		Utiles.Tween(grieta, 0.22, {
			Size = Vector3.new(grieta.Size.X, 0.12, largo),
			CFrame = CFrame.lookAt(
				base + direccion * (largo / 2) + Vector3.new(0, 0.12, 0),
				base + direccion * 100 + Vector3.new(0, 0.12, 0)
			),
		}, "Quart")
		Utiles.Tween(grieta, duracion * 0.85, { Transparency = 1 }, "Quad", true)
	end

	-- Rocas levantadas en el borde.
	local rocas = Utiles.Cantidad(capa.Rocas or 10, factor)
	for indice = 1, rocas do
		local angulo = (indice / rocas) * math.pi * 2 + Utiles.Azar:NextNumber(-0.25, 0.25)
		local distancia = radio * Utiles.Azar:NextNumber(0.85, 1.05)
		local tamano = Utiles.Azar:NextNumber(1.6, 3.4)
		local posicion =
			Vector3.new(base.X + math.cos(angulo) * distancia, sueloY, base.Z + math.sin(angulo) * distancia)
		local fuera = Vector3.new(math.cos(angulo), 0, math.sin(angulo))
		local roca = registrar(Pool.Parte("Bloque"))
		roca.Color = Utiles.Color("Oscuro", ctx.Paleta):Lerp(Color3.fromRGB(90, 88, 98), 0.4)
		roca.Material = material
		roca.Transparency = 0
		roca.Size = Vector3.new(tamano, tamano * 0.6, tamano * 1.1)
		-- Inclinada hacia fuera, hundida al principio y levantada después.
		local inclinada = CFrame.lookAt(posicion, posicion + fuera)
			* CFrame.Angles(math.rad(Utiles.Azar:NextNumber(20, 45)), Utiles.Azar:NextNumber(-0.4, 0.4), 0)
		roca.CFrame = inclinada + Vector3.new(0, -tamano, 0)
		Utiles.Tween(roca, 0.22, { CFrame = inclinada + Vector3.new(0, tamano * 0.15, 0) }, "Back")
		task.delay(duracion, function()
			if roca.Parent then
				Utiles.Tween(roca, fundido, { Transparency = 1, Size = roca.Size * 0.3 }, "Quad", true)
			end
		end)
	end

	task.delay(duracion + fundido + 0.1, function()
		for _, parte in aLiberar do
			Pool.Liberar(parte)
		end
	end)
end

return Terreno
