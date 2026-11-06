--!strict
--[[
	Flujo (Elección de bando): las reglas de la pantalla de elección, sin nada de Roblox (se prueban con Lune).

	El cliente que pinta la pantalla (client/Eleccion) solo pregunta aquí qué hacer; este módulo decide:

	  Esperando    aún no han llegado los datos del jugador: no se sabe si tiene bando.
	  Eligiendo    su bando es "Ninguno": se muestra la escena y puede resaltar y elegir.
	  Enviado      ya pidió un bando al servidor y espera su respuesta. No se puede elegir otra vez; si el servidor
	               no responde en `EsperaConfirmacion` segundos, se vuelve a Eligiendo.
	  Confirmado   el servidor ha aplicado un bando (el que pidió... o el que el servidor diga: manda el servidor).
	  Terminado    no hay que mostrar nada (ya tenía bando al entrar) o la pantalla ya se cerró.

	Esto es solo CORTESÍA para que la interfaz no envíe peticiones absurdas. La regla de verdad (solo se elige una
	vez, solo Humanos o Monstruos) la hace cumplir el servidor: Servicios/ServicioBandos.
]]

local Bandos = require(script.Parent.Parent.Juego.Bandos)

export type Estado = "Esperando" | "Eligiendo" | "Enviado" | "Confirmado" | "Terminado"

-- Lo que el cliente debe hacer tras recibir unos datos.
export type Accion = "Mostrar" | "Omitir" | "Confirmar" | "Nada"

export type Flujo = {
	Estado: Estado,
	Resaltado: string?, -- bando bajo el ratón o el dedo (nil = ninguno)
	Pedido: string?, -- bando que se pidió al servidor
	PedidoEn: number, -- instante de la petición
	Confirmado: string?, -- bando que confirmó el servidor
	EsperaConfirmacion: number,
	Mostrada: boolean, -- se llegó a mostrar la pantalla
}

local Modulo = {}

-- ¿Hay que enseñar la pantalla de elección con estos datos? Solo si ya llegaron y el bando es "Ninguno".
function Modulo.DebeMostrar(datos: any): boolean
	return type(datos) == "table" and datos.Bando == Bandos.Ninguno
end

-- Crea el flujo. `esperaConfirmacion` = segundos que se espera la respuesta del servidor antes de dejar reintentar.
function Modulo.nuevo(esperaConfirmacion: number): Flujo
	return {
		Estado = "Esperando",
		Resaltado = nil,
		Pedido = nil,
		PedidoEn = 0,
		Confirmado = nil,
		EsperaConfirmacion = esperaConfirmacion,
		Mostrada = false,
	}
end

--[[
	Llegan datos nuevos del servidor (la primera copia o una actualización). Devuelve qué hacer:
	  "Mostrar"    primera copia y el bando es Ninguno: hay que montar la pantalla (o ha vuelto a ser Ninguno
	               después de cerrarla, con el comando de pruebas de Studio)
	  "Omitir"     primera copia y ya tiene bando: no se muestra nada
	  "Confirmar"  estaba en pantalla y el servidor ya le ha puesto un bando (segundo valor: cuál)
	  "Nada"       nada que hacer (datos repetidos, o la pantalla ya terminó)
]]
function Modulo.AlRecibirDatos(flujo: Flujo, datos: any): (Accion, string?)
	if type(datos) ~= "table" then
		return "Nada", nil
	end
	local bando = datos.Bando

	if flujo.Estado == "Esperando" then
		if bando == Bandos.Ninguno then
			flujo.Estado = "Eligiendo"
			flujo.Mostrada = true
			return "Mostrar", nil
		end
		flujo.Estado = "Terminado"
		return "Omitir", nil
	end

	-- La pantalla ya se cerró, pero el bando ha vuelto a ser "Ninguno" (solo pasa con el comando de pruebas de
	-- Studio, ver Servicios/ServicioBandos): se vuelve a mostrar desde cero.
	if flujo.Estado == "Terminado" and bando == Bandos.Ninguno then
		flujo.Estado = "Eligiendo"
		flujo.Resaltado = nil
		flujo.Pedido = nil
		flujo.PedidoEn = 0
		flujo.Confirmado = nil
		flujo.Mostrada = true
		return "Mostrar", nil
	end

	if flujo.Estado == "Eligiendo" or flujo.Estado == "Enviado" then
		if Bandos.EsElegible(bando) then
			-- Manda el servidor: si confirma otro bando distinto del pedido, se muestra el suyo.
			flujo.Estado = "Confirmado"
			flujo.Confirmado = bando
			flujo.Resaltado = bando
			return "Confirmar", bando
		end
	end
	return "Nada", nil
end

-- ¿Puede el jugador interactuar ahora (resaltar y elegir)?
function Modulo.PuedeElegir(flujo: Flujo): boolean
	return flujo.Estado == "Eligiendo"
end

--[[
	El ratón o el dedo pasa por un lado (o sale de los dos: nil). Devuelve true si el resaltado ha cambiado.
	Mientras se espera la respuesta del servidor se queda resaltado el bando pedido.
]]
function Modulo.Resaltar(flujo: Flujo, bando: string?): boolean
	if flujo.Estado ~= "Eligiendo" then
		return false
	end
	if bando ~= nil and not Bandos.EsElegible(bando) then
		return false
	end
	if flujo.Resaltado == bando then
		return false
	end
	flujo.Resaltado = bando
	return true
end

--[[
	El jugador hace clic (o toca) en un lado. Devuelve true si hay que enviar la petición ElegirBando al servidor:
	solo una vez, solo un bando elegible y solo mientras se está eligiendo.
]]
function Modulo.Elegir(flujo: Flujo, bando: any, ahora: number): boolean
	if flujo.Estado ~= "Eligiendo" or not Bandos.EsElegible(bando) then
		return false
	end
	flujo.Estado = "Enviado"
	flujo.Pedido = bando
	flujo.PedidoEn = ahora
	flujo.Resaltado = bando
	return true
end

--[[
	Se llama de vez en cuando mientras se espera la respuesta. Si el servidor no ha confirmado a tiempo (se perdió
	la petición, o la rechazó porque aún no tenía los datos cargados), devuelve true y deja volver a elegir.
]]
function Modulo.RevisarEspera(flujo: Flujo, ahora: number): boolean
	if flujo.Estado ~= "Enviado" or ahora - flujo.PedidoEn < flujo.EsperaConfirmacion then
		return false
	end
	flujo.Estado = "Eligiendo"
	flujo.Pedido = nil
	return true
end

-- La pantalla se ha cerrado (tras la transición, o por un error): ya no se hace nada más.
function Modulo.Terminar(flujo: Flujo)
	flujo.Estado = "Terminado"
	flujo.Resaltado = nil
end

-- Bando del lado indicado (1 = izquierda, 2 = derecha) según el orden de la pantalla.
function Modulo.BandoDelLado(orden: { string }, lado: number): string?
	return orden[lado]
end

-- El bando vecino al resaltado al pulsar izquierda (-1) o derecha (+1) con teclado o mando.
function Modulo.Vecino(orden: { string }, actual: string?, paso: number): string
	if actual == nil then
		return if paso < 0 then orden[1] else orden[#orden]
	end
	local indice = table.find(orden, actual) or 1
	return orden[math.clamp(indice + paso, 1, #orden)]
end

return Modulo
