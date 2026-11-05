--!strict
--[[
	AlturasRegion: la CAPA DE COLISIÓN FIJA del terreno de la región 1, a partir de datos/alturas (lo genera
	herramientas/exportar_alturas.py muestreando en Blender los mismos trozos de terreno que se ven).

	Por qué existe (probado en Studio): la colisión de las mallas de terreno no es fiable. Con PreciseConvexDecomposition,
	51 de los 64 trozos tienen agujeros y el 6_5 no tiene ninguna colisión (son láminas abiertas de 19.200 triángulos que
	Roblox aproxima con pocas envolturas convexas). Por esos agujeros se atravesaba el suelo. Esta capa no depende de la
	colisión de Roblox, ni del nivel de detalle que se esté dibujando, ni de lo que haya llegado al cliente.

	Uso:
		local mapa = AlturasRegion.cargar(require(Region1.Datos.alturas))
		local r = mapa:radio(direccion)   -- radio del suelo en esa dirección (coordenadas del planeta), o nil
	Las coordenadas del planeta son las de los datos: centro en el origen, la región en la cara +Y.
]]

local AlturasRegion = {}

export type Datos = { N: number, L: number, Radio: number, Base: number, Escala: number, Datos: string }

export type Mapa = {
	N: number,
	L: number,
	Radio: number,
	Base: number,
	Escala: number,
	Valores: buffer,
	radio: (self: Mapa, direccion: Vector3) -> number?,
}

local ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

local function decodificarBase64(texto: string): buffer
	local tabla = table.create(256, -1)
	for i = 1, #ALFABETO do
		tabla[string.byte(ALFABETO, i) + 1] = i - 1
	end
	local largo = #texto
	local relleno = 0
	if string.sub(texto, -2) == "==" then
		relleno = 2
	elseif string.sub(texto, -1) == "=" then
		relleno = 1
	end
	local salida = buffer.create(largo // 4 * 3 - relleno)
	local o = 0
	local total = buffer.len(salida)
	for i = 1, largo, 4 do
		local a, b, c, d = string.byte(texto, i, i + 3)
		local n = bit32.bor(
			bit32.lshift(tabla[a + 1], 18),
			bit32.lshift(tabla[b + 1], 12),
			bit32.lshift(math.max(tabla[(c or 61) + 1], 0), 6),
			math.max(tabla[(d or 61) + 1], 0)
		)
		if o < total then
			buffer.writeu8(salida, o, bit32.extract(n, 16, 8))
		end
		if o + 1 < total then
			buffer.writeu8(salida, o + 1, bit32.extract(n, 8, 8))
		end
		if o + 2 < total then
			buffer.writeu8(salida, o + 2, bit32.extract(n, 0, 8))
		end
		o += 3
	end
	return salida
end

local function valor(m: Mapa, i: number, j: number): number
	return buffer.readu16(m.Valores, (i * m.N + j) * 2)
end

-- Radio del suelo en `direccion` (coordenadas del planeta). nil fuera de la cara de la región o sin datos.
local function radio(self: Mapa, direccion: Vector3): number?
	local x, y, z = direccion.X, direccion.Y, direccion.Z
	if y <= 0 or y < math.abs(x) or y < math.abs(z) then
		return nil -- fuera de la cara +Y
	end
	-- Coordenadas de diseño (geo.py): Roblox (x, y, z) -> Blender (x, -z, y); x_d = R·atan(x_b/z_b), y_d = R·atan(y_b/z_b).
	local xd = self.Radio * math.atan2(x, y)
	local yd = self.Radio * math.atan2(-z, y)
	local paso = 2 * self.L / (self.N - 1)
	local fj = (xd + self.L) / paso
	local fi = (yd + self.L) / paso
	local j0, i0 = math.floor(fj), math.floor(fi)
	if j0 < 0 or i0 < 0 or j0 >= self.N - 1 or i0 >= self.N - 1 then
		return nil
	end
	local tj, ti = fj - j0, fi - i0
	local suma, peso = 0, 0
	for _, e in { { 0, 0, (1 - ti) * (1 - tj) }, { 0, 1, (1 - ti) * tj }, { 1, 0, ti * (1 - tj) }, { 1, 1, ti * tj } } do
		local v = valor(self, i0 + e[1], j0 + e[2])
		if v > 0 then
			suma += v * e[3]
			peso += e[3]
		end
	end
	if peso < 1e-6 then
		return nil
	end
	return self.Base + suma / peso * self.Escala
end

function AlturasRegion.cargar(datos: Datos): Mapa
	return {
		N = datos.N,
		L = datos.L,
		Radio = datos.Radio,
		Base = datos.Base,
		Escala = datos.Escala,
		Valores = decodificarBase64(datos.Datos),
		radio = radio,
	}
end

return AlturasRegion
