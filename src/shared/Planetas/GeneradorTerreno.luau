--!strict
--[[
	GeneradorTerreno (Planetas): el terreno de las superficies como FUNCIONES PURAS.

	Calcula, a partir de una semilla y de los parámetros de Datos (Superficie.Terreno), la altura y el material de
	cada punto, y prepara los datos de un TROZO con el formato de Terrain:WriteVoxels (materiales y ocupaciones
	por celda de 4 studs). El servidor (ServicioPlanetas/Terreno) solo tiene que traducir los nombres de material
	a Enum.Material y escribirlos, trozo a trozo y cediendo entre trozos para no congelar el juego.

	Todo es determinista: la misma semilla da el mismo terreno, y las pruebas lo comprueban sin Studio.

	Coordenadas LOCALES: (0, 0, 0) es el centro de la superficie (Datos.Planetas[id].Superficie.Centro).

	Estilos:
	  "Humanos"    colinas verdes, lagos, playas, roca en las pendientes y nieve en lo alto
	  "Monstruos"  roca negra, agujas retorcidas y grietas profundas con roca fundida al fondo

	En los dos: montañas en el borde (para que nadie salga del mapa) y el puerto aplanado.

	Solo se rellena una "corteza" bajo la superficie (Grosor celdas, o hasta el vecino más bajo para que los
	acantilados no tengan huecos): lo de más abajo nunca se ve y así se generan muchas menos celdas.
]]

local Ruido = require(script.Parent.Ruido)
local V = require(script.Parent.Vectores)

export type Trozo = {
	I: number,
	J: number,
	Origen: V.Vec, -- esquina mínima del trozo, en studs locales
	Celdas: V.Vec, -- número de celdas en X, Y y Z
	Materiales: { { { string } } }, -- [x][y][z], nombres de Enum.Material ("Air" = vacío)
	Ocupacion: { { { number } } }, -- [x][y][z], 0..1
}

local GeneradorTerreno = {}
GeneradorTerreno.__index = GeneradorTerreno

export type Generador = typeof(setmetatable(
	{} :: {
		Parametros: { [string]: any },
		Tamano: number,
		Puerto: V.Vec,
		Ruido: Ruido.Ruido,
		RuidoDetalle: Ruido.Ruido,
	},
	GeneradorTerreno
))

--[[
	Crea un generador. `parametros` es Superficie.Terreno, `tamano` el lado del cuadrado (studs) y `puerto` la
	posición local del puerto (solo cuentan X y Z).
]]
function GeneradorTerreno.nuevo(parametros: { [string]: any }, tamano: number, puerto: V.Vec): Generador
	return setmetatable({
		Parametros = parametros,
		Tamano = tamano,
		Puerto = puerto,
		Ruido = Ruido.nuevo(parametros.Semilla),
		RuidoDetalle = Ruido.nuevo(parametros.Semilla + 7919),
	}, GeneradorTerreno)
end

-- ===== Altura =====

--[[
	Altura del suelo (studs locales) en (x, z), y un segundo valor 0..1: cuánto de "grieta" hay ahí (solo en el
	estilo Monstruos; 1 = el fondo de una grieta).
]]
function GeneradorTerreno.Columna(self: Generador, x: number, z: number): (number, number)
	local p = self.Parametros
	local ruido = self.Ruido
	local altura = p.AlturaBase + ruido:Fractal(x, z, p.Capas)
	local grieta = 0

	if p.Estilo == "Monstruos" then
		-- Agujas: donde un ruido de detalle supera el umbral, la roca se dispara hacia arriba.
		local agujas = p.Agujas
		if agujas then
			local n = self.RuidoDetalle:Valor(x / agujas.Escala, z / agujas.Escala)
			if n > agujas.Umbral then
				local k = (n - agujas.Umbral) / (1 - agujas.Umbral)
				altura += k * k * agujas.Altura
			end
		end
		-- Grietas: líneas finas donde el terreno se hunde.
		local grietas = p.Grietas
		if grietas then
			local c = ruido:Crestas(x, z, grietas.Escala)
			local limite = 1 - grietas.Anchura
			if c > limite then
				grieta = (c - limite) / grietas.Anchura
				altura -= grietas.Profundidad * grieta ^ 1.5
			end
		end
	end

	-- Montañas en el borde del mapa.
	local mitad = self.Tamano / 2
	local alBorde = math.min(mitad - math.abs(x), mitad - math.abs(z))
	local borde = 1 - V.suave(0, p.BordeAncho, alBorde)
	if borde > 0 then
		local variacion = 0.75 + 0.25 * self.RuidoDetalle:Valor(x / 180 + 9.1, z / 180 - 3.3)
		altura += borde * borde * p.BordeAltura * variacion
		grieta *= 1 - borde
	end

	-- El puerto: llano a PuertoAltura, con una transición suave hacia el terreno natural.
	local dx, dz = x - self.Puerto.X, z - self.Puerto.Z
	local distancia = math.sqrt(dx * dx + dz * dz)
	local natural = V.suave(p.PuertoRadioPlano, p.PuertoRadioPlano + p.PuertoTransicion, distancia)
	altura = p.PuertoAltura + (altura - p.PuertoAltura) * natural
	grieta *= natural

	return altura, grieta
end

-- Solo la altura.
function GeneradorTerreno.Altura(self: Generador, x: number, z: number): number
	local altura = self:Columna(x, z)
	return altura
end

-- ===== Material =====

--[[
	Material de la superficie en (x, z) con esa altura, pendiente (subida por stud) y grieta. `profundidad` es
	cuántas celdas hay por encima (0 = la de arriba del todo): las de debajo son el subsuelo.
]]
function GeneradorTerreno.Material(
	self: Generador,
	x: number,
	z: number,
	altura: number,
	pendiente: number,
	grieta: number,
	profundidad: number
): string
	local p = self.Parametros
	local m = p.Materiales
	local dx, dz = x - self.Puerto.X, z - self.Puerto.Z
	local enPuerto = dx * dx + dz * dz <= (p.PuertoRadioPlano * 0.72) ^ 2

	if p.Estilo == "Monstruos" then
		if enPuerto and profundidad <= 1 then
			return m.Puerto
		end
		if grieta > 0.55 then
			return m.Grieta -- el fondo de las grietas: roca fundida que brilla
		end
		if profundidad > 1 then
			return m.Base
		end
		if pendiente > p.PendienteRoca then
			return m.Roca
		end
		local variedad = self.RuidoDetalle:Valor(x / p.EscalaHierba + 3.7, z / p.EscalaHierba + 1.9)
		return if variedad > 0.15 then m.Ceniza else m.Base
	end

	-- Humanos.
	if enPuerto and profundidad <= 1 then
		return m.Puerto
	end
	if profundidad > 2 then
		return m.Roca
	elseif profundidad > 0 then
		return if pendiente > p.PendienteRoca then m.Roca else m.Tierra
	end
	if altura <= p.NivelAgua + p.AnchoPlaya then
		return m.Arena
	end
	if pendiente > p.PendienteRoca then
		return m.Roca
	end
	if altura >= p.AlturaNieve then
		return m.Nieve
	end
	local variedad = self.RuidoDetalle:Valor(x / p.EscalaHierba + 3.7, z / p.EscalaHierba + 1.9)
	return if variedad > 0.25 then m.HierbaAlta else m.Hierba
end

-- ===== Trozos =====

-- Número de trozos por lado.
function GeneradorTerreno.TrozosPorLado(self: Generador): number
	local p = self.Parametros
	return math.ceil(self.Tamano / (p.Trozo * p.Resolucion))
end

-- Lista de trozos { I, J } ordenada del más cercano al puerto al más lejano (el puerto se genera primero).
function GeneradorTerreno.Trozos(self: Generador): { { I: number, J: number } }
	local p = self.Parametros
	local lado = self:TrozosPorLado()
	local ancho = p.Trozo * p.Resolucion
	local mitad = self.Tamano / 2
	local lista = {}
	for i = 0, lado - 1 do
		for j = 0, lado - 1 do
			table.insert(lista, { I = i, J = j })
		end
	end
	local function distancia(t: { I: number, J: number }): number
		local cx = -mitad + (t.I + 0.5) * ancho - self.Puerto.X
		local cz = -mitad + (t.J + 0.5) * ancho - self.Puerto.Z
		return cx * cx + cz * cz
	end
	table.sort(lista, function(a, b)
		local da, db = distancia(a), distancia(b)
		if da == db then
			return a.I * lado + a.J < b.I * lado + b.J
		end
		return da < db
	end)
	return lista
end

--[[
	Prepara el trozo (i, j): las celdas de `Trozo` × `Trozo` columnas, con la altura justa para su relieve.
]]
function GeneradorTerreno.Trozo(self: Generador, i: number, j: number): Trozo
	local p = self.Parametros
	local n: number = p.Trozo
	local res: number = p.Resolucion
	local grosor: number = p.Grosor
	local mitad = self.Tamano / 2
	local x0 = -mitad + i * n * res
	local z0 = -mitad + j * n * res
	local agua: number? = p.NivelAgua

	-- Alturas con un borde de una celda (para la pendiente y para no dejar huecos en los acantilados).
	local alturas: { { number } } = table.create(n + 2)
	local grietas: { { number } } = table.create(n + 2)
	for a = 0, n + 1 do
		local filaAltura = table.create(n + 2, 0)
		local filaGrieta = table.create(n + 2, 0)
		local x = x0 + (a - 0.5) * res
		for b = 0, n + 1 do
			local h, g = self:Columna(x, z0 + (b - 0.5) * res)
			filaAltura[b + 1] = h
			filaGrieta[b + 1] = g
		end
		alturas[a + 1] = filaAltura
		grietas[a + 1] = filaGrieta
	end

	-- Altura mínima y máxima del trozo, en celdas.
	local minimo, maximo = math.huge, -math.huge
	for a = 2, n + 1 do
		local fila = alturas[a]
		for b = 2, n + 1 do
			local h = fila[b]
			local vecino = math.min(alturas[a - 1][b], alturas[a + 1][b], fila[b - 1], fila[b + 1])
			minimo = math.min(minimo, math.min(h, vecino) - grosor * res)
			maximo = math.max(maximo, h)
		end
	end
	if agua then
		maximo = math.max(maximo, agua)
	end
	local kMin = math.floor(minimo / res)
	local kMax = math.floor(maximo / res)
	local alto = kMax - kMin + 1

	local materiales: { { { string } } } = table.create(n)
	local ocupacion: { { { number } } } = table.create(n)
	for a = 1, n do
		local capaMat: { { string } } = table.create(alto)
		local capaOcu: { { number } } = table.create(alto)
		for k = 1, alto do
			capaMat[k] = table.create(n, "Air")
			capaOcu[k] = table.create(n, 0)
		end
		materiales[a] = capaMat
		ocupacion[a] = capaOcu
	end

	for a = 1, n do
		local x = x0 + (a - 0.5) * res
		local fila = alturas[a + 1]
		for b = 1, n do
			local z = z0 + (b - 0.5) * res
			local h = fila[b + 1]
			local vecino = math.min(alturas[a][b + 1], alturas[a + 2][b + 1], fila[b], fila[b + 2])
			local fondo = math.min(h, vecino) - grosor * res
			local pendiente = math.max(
				math.abs(alturas[a + 2][b + 1] - alturas[a][b + 1]),
				math.abs(fila[b + 2] - fila[b])
			) / (2 * res)
			local grieta = grietas[a + 1][b + 1]
			local superior = math.floor(h / res)

			for k = kMin, kMax do
				local abajo = k * res
				local arriba = abajo + res
				local y = k - kMin + 1
				if arriba <= fondo then
					continue -- bajo la corteza: vacío (nunca se ve)
				elseif abajo < h then
					local profundidad = superior - k
					local material = self:Material(x, z, h, pendiente, grieta, profundidad)
					materiales[a][y][b] = material
					ocupacion[a][y][b] = math.clamp((h - abajo) / res, 0, 1)
				elseif agua and abajo < agua then
					materiales[a][y][b] = p.Materiales.Agua
					ocupacion[a][y][b] = math.clamp((agua - abajo) / res, 0, 1)
				end
			end
		end
	end

	return {
		I = i,
		J = j,
		Origen = { X = x0, Y = kMin * res, Z = z0 },
		Celdas = { X = n, Y = alto, Z = n },
		Materiales = materiales,
		Ocupacion = ocupacion,
	}
end

return GeneradorTerreno
