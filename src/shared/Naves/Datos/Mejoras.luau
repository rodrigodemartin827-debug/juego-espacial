--!strict
--[[
	Mejoras (Naves): qué hace cada mejora de la nave, nivel a nivel.

	Los niveles de las mejoras se guardan en los datos del jugador (`MejorasNave`, ver
	ServicioDatos/Esquema). Este módulo dice qué ESTADÍSTICAS de la nave cambia cada una; el cálculo está en
	Naves/Estadisticas. Para equilibrar el juego basta con tocar los números de aquí.

	Cada estadística vale `Base + PorNivel * nivel`, limitada por `Min` y `Max` si se indican. Un nivel 0
	significa "sin mejorar": se usa la base.

	Los identificadores ("Casco", "Escudo"...) se guardan en el DataStore y no deben cambiarse.
]]

export type Efecto = {
	Base: number,
	PorNivel: number,
	Min: number?,
	Max: number?,
}

export type Mejora = {
	Nombre: string, -- texto para mostrar
	Descripcion: string,
	Efectos: { [string]: Efecto }, -- estadística -> cómo crece
}

local Mejoras = {}

-- Nivel máximo de cualquier mejora. Un dato guardado por encima de esto se trata como este máximo.
Mejoras.NivelMaximo = 10

-- Orden en que se muestran.
Mejoras.Orden = table.freeze({ "Casco", "Escudo", "Motor", "Armas", "Escaner", "Carga" })

Mejoras.Lista = {
	Casco = {
		Nombre = "Casco",
		Descripcion = "Más puntos de estructura: aguanta más impactos cuando el escudo cae.",
		Efectos = {
			VidaMax = { Base = 120, PorNivel = 35 },
		},
	},
	Escudo = {
		Nombre = "Escudo",
		Descripcion = "Más capacidad y recarga más rápida, y empieza a recargarse antes tras recibir daño.",
		Efectos = {
			EscudoMax = { Base = 60, PorNivel = 25 },
			RegenEscudo = { Base = 6, PorNivel = 1.4 },
			RetrasoEscudo = { Base = 5, PorNivel = -0.35, Min = 1.5 },
		},
	},
	Motor = {
		Nombre = "Motor",
		Descripcion = "Más velocidad, más aceleración y un turbo más potente y duradero.",
		Efectos = {
			VelocidadMax = { Base = 110, PorNivel = 10 },
			Aceleracion = { Base = 55, PorNivel = 6 },
			TurboMult = { Base = 1.5, PorNivel = 0.04 },
			EnergiaTurbo = { Base = 60, PorNivel = 6 },
		},
	},
	Armas = {
		Nombre = "Armas",
		Descripcion = "Los láseres hacen más daño, disparan más deprisa y llegan más lejos.",
		Efectos = {
			Dano = { Base = 16, PorNivel = 2.5 },
			Cadencia = { Base = 3, PorNivel = 0.3 },
			Alcance = { Base = 420, PorNivel = 30 },
		},
	},
	Escaner = {
		Nombre = "Escáner",
		Descripcion = "El radar de la nave ve más lejos y el escáner de mano analiza desde más lejos y más deprisa.",
		Efectos = {
			RadioEscaner = { Base = 350, PorNivel = 120 }, -- radar de la nave (studs)
			AlcanceEscaner = { Base = 40, PorNivel = 9 }, -- escáner de mano: distancia máxima (studs)
			VelocidadEscaner = { Base = 1, PorNivel = 0.15 }, -- escáner de mano: 1 = normal, 2 = el doble de rápido
		},
	},
	Carga = {
		Nombre = "Carga",
		Descripcion = "Más espacio en la bodega: es el límite del inventario (minerales y componentes).",
		Efectos = {
			Capacidad = { Base = 20, PorNivel = 10 },
		},
	},
} :: { [string]: Mejora }

return Mejoras
