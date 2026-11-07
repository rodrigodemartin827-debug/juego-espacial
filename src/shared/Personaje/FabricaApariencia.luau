--!strict
--[[
	FabricaApariencia: las reglas de una apariencia de editor de personaje, sin Roblox (se prueban con Lune), comunes a
	los dos bandos. Cada bando (Personaje/Apariencia para los Humanos, Personaje/AparienciaMonstruo) las crea con su
	configuración y se queda con un módulo con esta forma:

	  · Campos / CamposOpcion / CamposColor: los campos (el orden es el de los argumentos del remoto que guarda).
	  · Categorias: las filas de la lista del editor (con flechas ‹ ›), en orden.
	  · Opciones(campo) / Ids(campo) / Buscar(campo, id) / Indice(campo, id): las opciones de un campo de opciones.
	  · EsCampoColor(campo) / EsColor(valor) / NormalizarColor(valor) / PatronColor: colores "#RRGGBB".
	  · ValorValido(campo, valor): ¿vale `valor` para `campo`? (lo que comprueba el servidor).
	  · Validar(tabla): una apariencia completa y válida (lo que falte o no exista, por defecto).
	  · Hecha(tabla): si el jugador ya guardó una apariencia de este editor.
	  · Mover(campo, id, paso): la opción anterior o siguiente (las flechas), dando la vuelta.
	  · Aleatoria(azar): una apariencia al azar.
	  · Colores(a): el color de cada rol de las piezas.
]]

export type Categoria = { Campo: string, Nombre: string }

export type Config = {
	Datos: any, -- Defecto y Muestras
	CamposOpcion: { string },
	CamposColor: { string },
	Categorias: { Categoria },
	Listas: { [string]: { any } }, -- campo -> opciones
	-- Campos que, al azar, suelen quedarse en «nada» (el valor por defecto): si no, casi todo saldría con cicatriz...
	Raros: { [string]: boolean },
	-- Campos de opción que tiene que haber guardado un jugador para que cuente como «ya hizo su personaje».
	CamposHecha: { string },
	Colores: (a: any) -> { [string]: string },
	-- Pone en `resultado` los colores al azar.
	AzarColores: (azar: any, resultado: { [string]: string }) -> (),
}

local Fabrica = {}

function Fabrica.Crear(cfg: Config): any
	local A: any = {}
	local Datos = cfg.Datos

	A.CamposOpcion = cfg.CamposOpcion
	A.CamposColor = cfg.CamposColor
	A.Campos = table.clone(cfg.CamposOpcion)
	for _, campo in cfg.CamposColor do
		table.insert(A.Campos, campo)
	end
	A.Categorias = cfg.Categorias
	A.PatronColor = "^#%x%x%x%x%x%x$"

	local ES_COLOR: { [string]: boolean } = {}
	for _, campo in cfg.CamposColor do
		ES_COLOR[campo] = true
	end

	function A.EsCampoColor(campo: string): boolean
		return ES_COLOR[campo] == true
	end

	function A.Opciones(campo: string): { any }
		return cfg.Listas[campo] or {}
	end

	function A.Ids(campo: string): { string }
		local ids = {}
		for _, opcion in A.Opciones(campo) do
			table.insert(ids, opcion.Id)
		end
		return ids
	end

	function A.Buscar(campo: string, id: any): any
		for _, opcion in A.Opciones(campo) do
			if opcion.Id == id then
				return opcion
			end
		end
		return nil
	end

	function A.Indice(campo: string, id: any): number?
		for i, opcion in A.Opciones(campo) do
			if opcion.Id == id then
				return i
			end
		end
		return nil
	end

	function A.EsColor(valor: any): boolean
		return type(valor) == "string" and string.match(valor, A.PatronColor) ~= nil
	end

	-- "#a1b2c3" -> "#A1B2C3" (así dos colores iguales se guardan igual). nil si no es un color.
	function A.NormalizarColor(valor: any): string?
		if not A.EsColor(valor) then
			return nil
		end
		return string.upper(valor)
	end

	function A.ValorValido(campo: string, valor: any): boolean
		if ES_COLOR[campo] then
			return A.EsColor(valor)
		end
		return A.Buscar(campo, valor) ~= nil
	end

	function A.Validar(tabla: any): any
		local fuente = if type(tabla) == "table" then tabla else {}
		local resultado: { [string]: string } = {}
		for _, campo in A.Campos do
			local valor = fuente[campo]
			if ES_COLOR[campo] then
				resultado[campo] = A.NormalizarColor(valor) or Datos.Defecto[campo]
			else
				resultado[campo] = if A.Buscar(campo, valor) ~= nil then valor else Datos.Defecto[campo]
			end
		end
		return resultado
	end

	function A.Hecha(tabla: any): boolean
		if type(tabla) ~= "table" then
			return false
		end
		for _, campo in cfg.CamposHecha do
			if A.Buscar(campo, tabla[campo]) == nil then
				return false
			end
		end
		return true
	end

	-- La opción `paso` posiciones más allá (1 = siguiente, -1 = anterior), dando la vuelta al final de la lista.
	function A.Mover(campo: string, id: any, paso: number): string
		local lista = A.Opciones(campo)
		assert(#lista > 0, "campo sin opciones: " .. campo)
		local i = A.Indice(campo, id) or 1
		local nuevo = ((i - 1 + paso) % #lista) + 1
		return lista[nuevo].Id
	end

	function A.Aleatoria(azar: any): any
		local resultado: { [string]: string } = {}
		for _, campo in A.CamposOpcion do
			local lista = A.Opciones(campo)
			if cfg.Raros[campo] and azar:NextInteger(1, 10) <= 7 then
				resultado[campo] = Datos.Defecto[campo]
			else
				resultado[campo] = lista[azar:NextInteger(1, #lista)].Id
			end
		end
		cfg.AzarColores(azar, resultado)
		return resultado
	end

	function A.Colores(a: any): { [string]: string }
		return cfg.Colores(a)
	end

	return A
end

return Fabrica
