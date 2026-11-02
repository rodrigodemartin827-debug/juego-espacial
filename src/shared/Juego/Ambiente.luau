--!strict
--[[
	Ambiente: la iluminación del espacio (noche cerrada, luz ambiente fría, resplandor y contraste).

	Lo aplica ZonaPruebas al arrancar. Para retocar el aspecto del juego, cambia solo estos números.

	Ojo con el resplandor (Bloom): todo lo que es Neon brilla por encima de 1, así que con un umbral bajo
	(< 1) resplandece todo a la vez y la imagen se "quema", sobre todo con los propulsores de las naves y los
	efectos de los poderes. Con el umbral por encima de 1 solo resplandecen los núcleos más intensos.
]]

local Ambiente = {}

Ambiente.Iluminacion = {
	ClockTime = 0,
	Ambient = Color3.fromRGB(38, 42, 68),
	OutdoorAmbient = Color3.fromRGB(46, 52, 86),
	ExposureCompensation = 0.25,
	EnvironmentDiffuseScale = 0.6,
	EnvironmentSpecularScale = 0.8,
}

Ambiente.Resplandor = {
	Intensity = 0.4, -- fuerza del halo
	Size = 20, -- tamaño del halo
	Threshold = 1.4, -- solo resplandece lo que brilla más que esto
}

Ambiente.Color = {
	Contrast = 0.12,
	Saturation = 0.18,
}

return Ambiente
