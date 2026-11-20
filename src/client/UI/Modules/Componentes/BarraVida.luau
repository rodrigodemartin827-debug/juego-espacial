--!strict
--[[
	BarraVida: barra de vida, escudo o energía reutilizable.

	  - Vida: el color pasa de verde a ámbar y a rojo según el porcentaje (Theme.ColorVida).
	  - Escudo: degradado cian. Energía: degradado púrpura (fina, sin marcas).
	  - Al cambiar, el relleno se interpola 0,3 s (EaseOut).
	  - Barra "fantasma": al recibir daño, una barra roja se queda donde estaba la vida y baja medio segundo después,
	    para que se vea cuánto daño acabas de recibir. Al curarse, la fantasma sube a la vez.
	  - Marcas cada 10 % y un brillo arriba para darle volumen.
]]

local Theme = require(script.Parent.Parent.Temas.EspacialTheme)
local UITweens = require(script.Parent.Parent.Animaciones.UITweens)
local P = require(script.Parent.Primitivas)

local C = Theme.Colores

local BarraVida = {}

export type Tipo = "Vida" | "Escudo" | "Energia"

export type BarraVida = {
	Marco: Frame,
	Poner: (actual: number, maximo: number, instantaneo: boolean?) -> (),
}

export type Opciones = {
	Tipo: Tipo,
	Ancho: number,
	Alto: number,
	Posicion: UDim2?,
	Orden: number?,
	Z: number?,
}

function BarraVida.Crear(padre: Instance, o: Opciones): BarraVida
	local z = o.Z or 1
	local fina = o.Tipo == "Energia"
	local marco = P.Marco(padre, {
		Nombre = `Barra{o.Tipo}`,
		Tamano = UDim2.fromOffset(o.Ancho, o.Alto),
		Posicion = o.Posicion,
		Color = C.FondoProfundo,
		Transparencia = Theme.Alpha.HUDFondo,
		Radio = UDim.new(0, if fina then 2 else 3),
		Recortar = true,
		Orden = o.Orden,
		Z = z,
	})
	P.Borde(marco, if fina then C.Energia else C.Acento, 0.7, Theme.Tamanos.Trazo)

	local margen = if fina then 0 else 1
	local interior = UDim2.new(0, -2 * margen, 1, -2 * margen)

	-- Barra roja de daño reciente (debajo del relleno).
	local fantasma = P.Marco(marco, {
		Nombre = "Fantasma",
		Tamano = UDim2.new(1, interior.X.Offset, 1, interior.Y.Offset),
		Posicion = UDim2.fromOffset(margen, margen),
		Color = C.Fantasma,
		Transparencia = Theme.Alpha.Fantasma,
		Radio = UDim.new(0, 2),
		Z = z + 1,
	})
	fantasma.Visible = not fina

	local relleno = P.Marco(marco, {
		Nombre = "Relleno",
		Tamano = UDim2.new(1, interior.X.Offset, 1, interior.Y.Offset),
		Posicion = UDim2.fromOffset(margen, margen),
		Color = if o.Tipo == "Vida" then C.VidaAlta else C.Blanco,
		Radio = UDim.new(0, 2),
		Z = z + 2,
	})
	if o.Tipo == "Escudo" then
		P.Degradado(relleno, Theme.Degradados.Escudo, 0)
	elseif o.Tipo == "Energia" then
		P.Degradado(relleno, Theme.Degradados.Energia, 0)
	end

	if not fina then
		-- Brillo superior (volumen).
		local brillo = P.Marco(
			relleno,
			{ Nombre = "Brillo", Tamano = UDim2.fromScale(1, 0.55), Color = C.Blanco, Transparencia = 0, Z = z + 3 }
		)
		P.Degradado(brillo, ColorSequence.new(C.Blanco), 90, NumberSequence.new(0.6, 1))
		-- Marcas cada 10 %.
		for i = 1, 9 do
			P.Marco(marco, {
				Nombre = "Marca",
				Tamano = UDim2.new(0, 1, 1, 0),
				Posicion = UDim2.fromScale(i / 10, 0),
				Color = C.Negro,
				Transparencia = 0.65,
				Z = z + 4,
			})
		end
	end

	local proporcionActual = 1
	local retraso: thread? = nil

	local function poner(actual: number, maximo: number, instantaneo: boolean?)
		local p = if maximo > 0 then math.clamp(actual / maximo, 0, 1) else 0
		local anterior = proporcionActual
		proporcionActual = p
		if instantaneo then
			relleno.Size = UDim2.new(p, interior.X.Offset * p, 1, interior.Y.Offset)
			fantasma.Size = relleno.Size
		else
			UITweens.Tween(
				relleno,
				Theme.Tweens.Barra,
				{ Size = UDim2.new(p, interior.X.Offset * p, 1, interior.Y.Offset) }
			)
			if retraso then
				task.cancel(retraso)
				retraso = nil
			end
			if p < anterior then
				-- Daño: la fantasma espera y luego baja.
				retraso = task.delay(Theme.Tiempos.RetrasoFantasma, function()
					retraso = nil
					UITweens.Tween(
						fantasma,
						Theme.Tweens.Fantasma,
						{ Size = UDim2.new(p, interior.X.Offset * p, 1, interior.Y.Offset) }
					)
				end)
			else
				UITweens.Tween(
					fantasma,
					Theme.Tweens.Barra,
					{ Size = UDim2.new(p, interior.X.Offset * p, 1, interior.Y.Offset) }
				)
			end
		end
		if o.Tipo == "Vida" then
			UITweens.Tween(relleno, Theme.Tweens.Barra, { BackgroundColor3 = Theme.ColorVida(p) })
		end
	end

	return { Marco = marco, Poner = poner }
end

return BarraVida
