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
	NaveLaserHeroes = {
		Nucleo = "#FFFFFF",
		Principal = "#4DF0FF",
		Secundario = "#2F7BFF",
		Oscuro = "#0B1B3A",
	},
	NaveLaserVillanos = {
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
}

return Paleta
