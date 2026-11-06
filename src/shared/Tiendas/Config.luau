--!strict
--[[
	Config (Tiendas): constantes de las tiendas del planeta humano y de su persiana. Lo comparten servidor y cliente.

	Aquí solo hay reglas y distancias. Lo que se vende y a qué precio está en Tiendas/Datos/Catalogo; el aspecto, los
	tiempos y los sonidos de la animación de la persiana, en Tiendas/Datos/Persiana.

	Cómo funciona la persiana (la decide SIEMPRE el servidor, Servicios/ServicioTiendas):
	  - Si un jugador de un bando vetado (los Monstruos) entra a menos de RadioCierre de una tienda, la persiana baja.
	  - Vuelve a subir cuando no queda ninguno a menos de RadioApertura durante SegundosParaReabrir seguidos.
	    RadioApertura es mayor que RadioCierre (histéresis): así un monstruo que ronda el borde no la hace subir y bajar
	    sin parar.
	  - El estado se publica en el atributo AtributoPersiana del modelo de la tienda; los clientes lo animan.
]]

local Config = {
	-- ===== Etiquetas (CollectionService) y atributos =====
	EtiquetaTienda = "Tienda", -- todo modelo de tienda
	AtributoTiendaId = "TiendaId", -- en el modelo: id de la tienda en Datos/Catalogo.Tiendas
	AtributoPersiana = "PersianaBajada", -- en el modelo: true mientras la persiana está bajada (lo escribe el servidor)
	AtributoPilotando = "Pilotando", -- en el personaje: true mientras va dentro de una nave (ver Naves/Config)

	-- ===== Quién no puede comprar =====
	-- Bandos a los que las tiendas no venden nada y ante los que bajan la persiana.
	BandosVetados = table.freeze({ "Monstruos" }),
	-- true = con la persiana bajada la tienda no vende a NADIE (está cerrada). false = solo se niega a los vetados.
	CerradaParaTodosConPersianaBajada = true,

	-- ===== Comprar =====
	AlcanceTienda = 14, -- studs: distancia máxima al mostrador para comprar
	HolguraAlcance = 1.2, -- el servidor acepta hasta alcance * esto (latencia y movimiento)
	CantidadMaximaPorPeticion = 20, -- unidades de un material que se pueden comprar de una vez

	-- ===== Persiana =====
	RadioCierre = 40, -- studs: un monstruo a esta distancia o menos hace bajar la persiana
	RadioApertura = 55, -- studs: la persiana no sube mientras quede un monstruo a esta distancia o menos
	SegundosParaReabrir = 2.5, -- segundos sin monstruos cerca antes de volver a subir
	IntervaloVigilancia = 0.2, -- cada cuánto revisa el servidor la distancia de los monstruos a las tiendas
}

return table.freeze(Config)
