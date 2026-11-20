--!strict
--[[
	Contexto: lo que el controlador (HUDController) le da a cada pantalla al iniciarla.

	Las pantallas no se conocen entre sí ni conocen al controlador: para abrir otra pantalla o avisar al jugador usan
	estas funciones. Así se pueden quitar o añadir pantallas sin tocar las demás.
]]

local Notificacion = require(script.Parent.Componentes.Notificacion)

export type Contexto = {
	Raiz: Frame, -- lienzo de los menús (960×540 unidades, escalado)
	AUnidades: (pixeles: Vector2) -> Vector2, -- convierte AbsolutePosition a unidades del lienzo
	Abrir: (id: string) -> (), -- abre otra pantalla ("personaje", "inventario", "mapa"...)
	Cerrar: () -> (), -- cierra el menú y vuelve a la partida
	Notificar: (aviso: Notificacion.Aviso) -> (),
	-- Avisa al controlador de que la pantalla ha cambiado de pestaña (para marcar el botón de la barra lateral).
	MarcarPantalla: (id: string) -> (),
}

-- Una pantalla de menú.
export type Pantalla = {
	Iniciar: (contexto: Contexto) -> (),
	Mostrar: (subvista: string?) -> (),
	Ocultar: () -> (),
}

return {}
