--!strict
--[[
	Paleta: colores de cada poder, en hexadecimal "#RRGGBB".

	Los efectos (Datos/EfectosVFX) no usan colores sueltos, sino nombres de esta paleta ("Principal",
	"Nucleo"...). Así, para cambiar el color de TODO un poder basta con editar cuatro líneas aquí.

	  - Nucleo:     el centro blanco/brillante de los efectos.
	  - Principal:  color dominante.
	  - Secundario: color de apoyo (halos, partículas de relleno).
	  - Oscuro:     sombras, humo, cráteres.
]]

local Paleta = {
	Rayo = {
		Nucleo = "#FFFFFF",
		Principal = "#7FD6FF",
		Secundario = "#B28BFF",
		Oscuro = "#1B2A57",
	},
	Gravedad = {
		Nucleo = "#F3E4FF",
		Principal = "#A04BFF",
		Secundario = "#FF4BC8",
		Oscuro = "#14061F",
	},
	Cuerpo = {
		Nucleo = "#FFFFFF",
		Principal = "#FFD38A",
		Secundario = "#FF8A3D",
		Oscuro = "#3B2A1D",
	},

	-- ===== Naves (Naves/Datos/EfectosNave) =====
	-- Láseres: un color por bando, para distinguir de quién es cada disparo a primera vista.
	NaveLaserHumanos = {
		Nucleo = "#FFFFFF",
		Principal = "#4DF0FF",
		Secundario = "#2F7BFF",
		Oscuro = "#0B1B3A",
	},
	NaveLaserMonstruos = {
		Nucleo = "#FFF1E8",
		Principal = "#FF4D5E",
		Secundario = "#FF9A3D",
		Oscuro = "#3A0B14",
	},
	NaveLaserNeutral = {
		Nucleo = "#FFFFFF",
		Principal = "#B6FF6B",
		Secundario = "#38D68A",
		Oscuro = "#0E3321",
	},
	NaveExplosion = {
		Nucleo = "#FFFFFF",
		Principal = "#FFB347",
		Secundario = "#FF4D1F",
		Oscuro = "#2A1710",
	},
	NaveEscudo = {
		Nucleo = "#EAFBFF",
		Principal = "#58C8FF",
		Secundario = "#5A7BFF",
		Oscuro = "#10224A",
	},
	NavePropulsor = {
		Nucleo = "#FFFFFF",
		Principal = "#6FD8FF",
		Secundario = "#3D7BFF",
		Oscuro = "#0E1A3B",
	},
	NaveTurbo = {
		Nucleo = "#FFFFFF",
		Principal = "#B58CFF",
		Secundario = "#FF5BD8",
		Oscuro = "#1D0E3B",
	},
	Asteroide = {
		Nucleo = "#FFE9C7",
		Principal = "#C9A27A",
		Secundario = "#FF8B3D",
		Oscuro = "#4A433C",
	},

	-- ===== Exploración (Exploracion/Datos/EfectosExploracion) =====
	-- Escáner de mano: cian holográfico mientras analiza, verde al completar, rojo si se interrumpe.
	Escaner = {
		Nucleo = "#E8FFFF",
		Principal = "#35E6FF",
		Secundario = "#2F8BFF",
		Oscuro = "#08233A",
	},
	EscanerCompleto = {
		Nucleo = "#FFFFFF",
		Principal = "#7DFFB4",
		Secundario = "#35E6FF",
		Oscuro = "#0B3A2A",
	},
	EscanerFallo = {
		Nucleo = "#FFF1E8",
		Principal = "#FF6B6B",
		Secundario = "#FFA14D",
		Oscuro = "#3A0B14",
	},
	-- Un color por mineral (los nombres son "Mineral_" + el id de Exploracion/Datos/Minerales).
	Mineral_Hierro = {
		Nucleo = "#FFFFFF",
		Principal = "#C9C4BE",
		Secundario = "#8C8782",
		Oscuro = "#2C2A2E",
	},
	Mineral_Cobre = {
		Nucleo = "#FFE2C7",
		Principal = "#E08A4C",
		Secundario = "#C46A2E",
		Oscuro = "#3A2012",
	},
	Mineral_Cristal = {
		Nucleo = "#FFFFFF",
		Principal = "#5CE1FF",
		Secundario = "#B58CFF",
		Oscuro = "#10224A",
	},
	Mineral_Titanio = {
		Nucleo = "#F0F6FF",
		Principal = "#9DB6DA",
		Secundario = "#6E86AD",
		Oscuro = "#1D2636",
	},

	-- ===== Elección de bando (Eleccion/Datos/EfectosEleccion) =====
	-- Humanos: luz de amanecer, entre el azul de su cielo y el dorado de su sol.
	EleccionHumanos = {
		Nucleo = "#FFFFFF",
		Principal = "#6FD3FF",
		Secundario = "#FFD27A",
		Oscuro = "#0E2A4A",
	},
	-- Monstruos: rojo sangre sobre negro, con el violeta del agujero negro.
	EleccionMonstruos = {
		Nucleo = "#FFE8EC",
		Principal = "#FF2A45",
		Secundario = "#9B2BFF",
		Oscuro = "#07020A",
	},
	-- La grieta: energía violeta con núcleo blanco.
	EleccionGrieta = {
		Nucleo = "#FFFFFF",
		Principal = "#C04BFF",
		Secundario = "#6A2BFF",
		Oscuro = "#0A0214",
	},

	-- ===== Planetas y espacio (Planetas/Datos/Efectos) =====
	-- Entrada en la atmósfera: plasma incandescente alrededor de la nave.
	PlanetaAtmosfera = {
		Nucleo = "#FFF4E0",
		Principal = "#FF9A3D",
		Secundario = "#FF4A1F",
		Oscuro = "#3A1408",
	},
	-- Salida al espacio: estela fría y limpia.
	PlanetaDespegue = {
		Nucleo = "#FFFFFF",
		Principal = "#8FE3FF",
		Secundario = "#4D8BFF",
		Oscuro = "#0B1B3A",
	},
	-- Recalentamiento junto al sol.
	EspacioCalor = {
		Nucleo = "#FFF1C2",
		Principal = "#FFB23D",
		Secundario = "#FF5A1F",
		Oscuro = "#3A1A08",
	},
	-- Agujero negro: atracción y absorción.
	EspacioAgujero = {
		Nucleo = "#F6E6FF",
		Principal = "#B05CFF",
		Secundario = "#FF7A3D",
		Oscuro = "#0A0010",
	},
}

return Paleta
