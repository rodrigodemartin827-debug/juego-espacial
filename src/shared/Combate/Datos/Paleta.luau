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
}

return Paleta
