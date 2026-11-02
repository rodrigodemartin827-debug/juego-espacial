--!strict
--[[
	AnimacionesMonstruo: la forma de moverse de los jugadores del bando MONSTRUOS (rig R6).

	Estilo: criatura encorvada que no termina de ser humana. Nada copiado de personajes ni animaciones conocidas;
	las ideas que lo hacen inquietante son:
	  - el torso muy inclinado hacia delante y torcido hacia un lado,
	  - la cabeza ladeada y "clavada" en el mundo (Mundo = true): el cuerpo se sacude pero ella sigue mirando al
	    frente, y de vez en cuando da un tirón seco (easing Back/Constant en tramos de 1 a 3 cuadros),
	  - los brazos colgando como peso muerto, cada uno con su propio ritmo (no van acompasados con las piernas),
	  - una cojera al andar (la pierna izquierda se arrastra con la punta rozando el suelo) y una carrera a saltos
	    desiguales, como un galope roto.
	Se lee a distancia y en móvil porque la silueta (encorvada, cabeza torcida, brazos largos colgando) es muy
	distinta de la de un humano, no por detalles pequeños.

	Cada animación está escrita como curvas por pieza; Animacion/Horneado las convierte en cuadros (y calcula la
	altura del cuerpo para que los pies pisen el suelo). El formato está explicado allí. Resumen de los ángulos
	(grados, desde el punto de vista del personaje):
	  cabeceo +  el extremo libre va hacia DELANTE (torso/cabeza: se inclina hacia delante)
	  giro    +  gira hacia la IZQUIERDA visto desde arriba
	  ladeo   +  el extremo libre va hacia la DERECHA del personaje (en la pierna/brazo izquierdo, hacia dentro)
	  Torso: { cabeceo, giro, ladeo, derecha, arriba, adelante }; con AlturaAutomatica, "arriba" es la altura del pie
	  más bajo sobre el suelo (0 = pisando).
	Las piezas con Mundo = true (cabeza, brazos y piernas) se escriben respecto al personaje ERGUIDO: una pierna a 0
	está vertical aunque el torso vaya inclinado 40°.

	Para sustituir una animación por otra hecha en el editor de Roblox no hay que tocar código: se pone su ID en
	Combate/Datos/Recursos.Animaciones (Monstruo_Reposo, Monstruo_Andar...). Ver animaciones/README.md.

	VelocidadReferencia (studs/s): velocidad del personaje a la que esa animación, a velocidad 1, deja los pies
	quietos en el suelo. El cliente reproduce la animación a (velocidad real / VelocidadReferencia), dentro de los
	límites de Ajustes, para que los pies no patinen. La prueba "AndarMonstruo" mide la velocidad natural de los
	pies con la cinemática del R6 y comprueba que este número la respeta: si cambias las zancadas, cámbialo.
]]

local Horneado = require(script.Parent.Parent.Parent.Animacion.Horneado)

type Clave = Horneado.Clave
type Definicion = Horneado.Definicion

local AnimacionesMonstruo = {}

-- Clave abreviada: k(T, pose, easing, direccion).
local function k(t: number, pose: { number }, easing: string?, direccion: string?): Clave
	return { T = t, Pose = pose, Easing = easing, Direccion = direccion }
end

--[[
	Ajustes del controlador (cliente: Personajes/AndarMonstruo). Velocidades en studs/s (velocidad horizontal de la
	HumanoidRootPart). Un jugador normal anda a 16 (WalkSpeed por defecto): eso ya es "Correr". "Andar" se ve con
	el joystick a medias en móvil, al moverse despacio o si el juego baja la velocidad.
]]
AnimacionesMonstruo.Ajustes = {
	-- Umbrales con histéresis (para que no parpadee entre dos estados en el límite).
	EmpezarAndar = 0.9, -- por encima, pasa de Reposo a Andar
	PararAndar = 0.5, -- por debajo, vuelve a Reposo
	-- El cambio entre andar y correr está donde los dos ritmos caben en los límites de abajo: Andar a 8 va a 1,9x
	-- y Correr a 7,4 va a 0,57x (ver la prueba "límites de ritmo" de AndarMonstruo).
	EmpezarCorrer = 8, -- por encima, pasa de Andar a Correr
	PararCorrer = 7.4, -- por debajo, vuelve a Andar

	-- Límites de la velocidad de reproducción (fuera de ellos los pies patinan un poco, pero no se ve ridículo).
	RitmoMinimo = 0.55,
	RitmoMaximo = 2,
	-- Reposo y aire: variación aleatoria del ritmo de cada personaje, para que varios monstruos no vayan
	-- sincronizados (0.08 = entre 0.92 y 1.08).
	VariacionRitmo = 0.08,

	-- Fundidos al cambiar de animación (s). Un fundido corto hace el cambio más brusco: va con el estilo.
	Fundido = 0.18,
	FundidoAlSuelo = 0.08, -- al aterrizar
	FundidoSalida = 0.25, -- al dejar de aplicar el andar (deja de ser monstruo, se sienta, muere...)

	-- Aire: velocidad vertical (studs/s) que cuenta como salto o como caída si además no hay suelo debajo.
	VelocidadSalto = 4,
	VelocidadCaida = -6,
	-- Distancia (studs) bajo los pies a la que se busca el suelo en los personajes de otros jugadores.
	DistanciaSuelo = 1.2,

	-- Cada cuánto (s) se recalcula el estado de los personajes de OTROS jugadores y de los muñecos (el propio va
	-- cada cuadro). Más alto = menos coste en móvil, pero cambia de animación con más retraso.
	IntervaloOtros = 0.1,
	-- Más allá de esta distancia a la cámara (studs), los demás se recalculan cuatro veces menos.
	DistanciaDetalle = 150,
}

--[[
	Postura de reposo del Torso: 31° hacia delante y adelantado sobre los pies. Casi sin ladeo: en R6 las dos
	piernas cuelgan del Torso, así que ladearlo sube una cadera y deja un pie en el aire (con 6° ya flota 0,2 studs).
	Lo "torcido" lo ponen la cabeza y los brazos.
]]
local REPOSO = { 31, 0, -1.5, 0, 0, 0.3 }

AnimacionesMonstruo.Definiciones = {} :: { [string]: Definicion }

--[[
	REPOSO: respira hundiendo el pecho, con un ritmo irregular. A los 1,6 s la cabeza da un latigazo al otro lado y
	los hombros se encogen; a los 3,6 s, tres tics secos de la cabeza y una sacudida del brazo izquierdo.
	Las piernas quedan plantadas (Mundo) aunque el torso se mueva.
]]
AnimacionesMonstruo.Definiciones.Reposo = {
	Duracion = 4.8,
	Bucle = true,
	Prioridad = "Movement", -- todas en Movement: por encima de las del Animate (Core) y por debajo del combate (Action)
	AlturaAutomatica = true,
	Canales = {
		Torso = {
			Claves = {
				k(0, REPOSO),
				k(1.15, { 35, -2, -2, 0, 0, 0.33 }), -- se hunde despacio al soltar el aire
				k(1.55, { 35, -2, -2, 0, 0, 0.33 }, "Linear"),
				k(1.63, { 27, 5, -5, 0.05, 0, 0.26 }, "Back", "Out"), -- encoge los hombros de golpe
				k(2.3, { 30, 1, -2, 0, 0, 0.29 }),
				k(3.3, { 34, 0, -1, 0, 0, 0.32 }),
				k(3.66, { 32, -3, -3, 0, 0, 0.31 }, "Cubic", "Out"),
				k(4.8, REPOSO),
			},
		},
		Head = {
			Mundo = true,
			Claves = {
				k(0, { -4, 0, 28 }),
				k(1.5, { -2, 5, 33 }), -- se va ladeando cada vez más...
				k(1.58, { -14, -24, -16 }, "Back", "Out"), -- ...y da un latigazo al otro lado
				k(1.95, { -12, -22, -14 }, "Linear"),
				k(2.04, { -6, 3, 36 }, "Back", "Out"), -- vuelve de golpe pasándose
				k(2.6, { -4, 0, 28 }),
				k(3.55, { -4, 0, 28 }, "Linear"),
				k(3.6, { -4, 11, 23 }, "Constant"), -- tics secos
				k(3.68, { -4, -7, 31 }, "Constant"),
				k(3.77, { -5, 5, 26 }, "Constant"),
				k(4.3, { -4, 0, 28 }),
				k(4.8, { -4, 0, 28 }),
			},
		},
		["Right Arm"] = {
			Mundo = true,
			Claves = {
				k(0, { 7, 0, 6 }),
				k(1.25, { 11, 0, 4 }),
				k(1.7, { -4, 0, 13 }, "Quad", "Out"), -- el encogimiento de hombros lo lanza atrás
				k(2.4, { 10, 0, 5 }),
				k(3.6, { 6, 0, 7 }),
				k(4.8, { 7, 0, 6 }),
			},
		},
		["Left Arm"] = {
			Mundo = true,
			Claves = {
				k(0, { 15, 0, -3 }),
				k(1.7, { 9, 0, -9 }, "Quad", "Out"),
				k(2.5, { 14, 0, -4 }),
				k(3.6, { 14, 0, -4 }, "Linear"),
				k(3.68, { 27, 7, -11 }, "Back", "Out"), -- sacudida
				k(4.4, { 15, 0, -3 }),
				k(4.8, { 15, 0, -3 }),
			},
		},
		["Right Leg"] = {
			Mundo = true,
			Claves = { k(0, { -7, 0, 8 }), k(4.8, { -7, 0, 8 }) },
		},
		["Left Leg"] = {
			Mundo = true,
			Claves = { k(0, { 6, -10, -4 }), k(4.8, { 6, -10, -4 }) },
		},
	},
}

--[[
	ANDAR: cojera. La pierna derecha da un paso largo y firme; la izquierda se arrastra (sale tarde, despacio y
	con la punta rozando el suelo) y el cuerpo se desploma hacia ella cuando la pisa. El brazo derecho se balancea
	con retraso y el izquierdo cuelga casi muerto. La cabeza se queda mirando al frente, con un tirón por ciclo.
	Los tramos de apoyo de las piernas son lineales: así el pie que pisa se mueve hacia atrás a velocidad
	constante y no patina.
	Fases (s): 0 pisa la derecha · 0-0,48 apoyo derecho · 0,46 pisa la izquierda · 0,46-0,9 apoyo izquierdo.
]]
AnimacionesMonstruo.Definiciones.Andar = {
	Duracion = 0.9,
	Bucle = true,
	Prioridad = "Movement",
	AlturaAutomatica = true,
	VelocidadReferencia = 4.2,
	Canales = {
		Torso = {
			Claves = {
				k(0, { 30, 8, 2, 0, 0, 0.32 }),
				k(0.12, { 29, 5, 5, 0, 0, 0.3 }), -- carga el peso en la pierna buena
				k(0.4, { 31, -4, 5, 0, 0, 0.3 }),
				k(0.47, { 33, -6, -5, 0, 0, 0.33 }),
				k(0.57, { 39, -8, -13, -0.08, 0, 0.36 }, "Quad", "Out"), -- se desploma sobre la pierna mala
				k(0.75, { 36, -2, -9, -0.06, 0, 0.35 }),
				k(0.9, { 30, 8, 2, 0, 0, 0.32 }),
			},
		},
		Head = {
			Mundo = true,
			Claves = {
				k(0, { -6, 2, 26 }),
				k(0.3, { -3, 0, 24 }),
				k(0.6, { 4, -4, 34 }, "Quad", "Out"), -- el golpe del desplome le llega tarde a la cabeza
				k(0.67, { -10, 14, 18 }, "Back", "Out"), -- tirón
				k(0.9, { -6, 2, 26 }),
			},
		},
		["Right Arm"] = {
			Mundo = true,
			Desfase = 0.12,
			Claves = {
				k(0, { -20, 0, 8 }),
				k(0.45, { 26, 0, 4 }),
				k(0.9, { -20, 0, 8 }),
			},
		},
		["Left Arm"] = {
			Mundo = true,
			Desfase = -0.2,
			Claves = {
				k(0, { 16, 0, -4 }),
				k(0.5, { 6, 0, -8 }),
				k(0.9, { 16, 0, -4 }),
			},
		},
		["Right Leg"] = { -- pierna buena
			Mundo = true,
			Claves = {
				k(0, { 30, 0, 3 }),
				k(0.48, { -26, 0, 3 }, "Linear"), -- apoyo
				k(0.55, { -33, 0, 6 }, "Quad", "Out"),
				k(0.7, { 2, 0, 14 }, "Quad", "InOut"), -- pasa abriéndose para no rozar
				k(0.85, { 32, 0, 5 }, "Quad", "Out"),
				k(0.9, { 30, 0, 3 }),
			},
		},
		["Left Leg"] = { -- pierna que se arrastra
			Mundo = true,
			Claves = {
				k(0, { -30, 4, -3 }),
				k(0.16, { -28, 10, -7 }, "Sine", "Out"), -- tarda en despegar y se tuerce
				k(0.33, { 0, 6, -6 }, "Quad", "In"), -- la arrastra hacia delante, rozando
				k(0.46, { 22, 0, -3 }, "Quad", "Out"),
				k(0.9, { -30, 4, -3 }, "Linear"), -- apoyo
			},
		},
	},
}

--[[
	CORRER: carrera rota, muy agachado y con el cuerpo retorciéndose. Las dos zancadas no duran lo mismo (la
	derecha es más corta y rápida): se ve "desacompasado". Al despegar, cada pierna se dispara hacia atrás antes
	de volver, como una articulación que no funciona bien. El brazo izquierdo va arrastrado atrás, rígido; el
	derecho se agita suelto, a destiempo. La cabeza, clavada al frente.
	Fases (s): 0-0,2 apoyo derecho · 0,2-0,26 en el aire · 0,26-0,48 apoyo izquierdo · 0,48-0,56 en el aire.
]]
AnimacionesMonstruo.Definiciones.Correr = {
	Duracion = 0.56,
	Bucle = true,
	Prioridad = "Movement",
	AlturaAutomatica = true,
	VelocidadReferencia = 13,
	Canales = {
		Torso = {
			Claves = {
				k(0, { 42, 10, 6, 0, 0, 0.45 }),
				k(0.1, { 46, 2, 6, 0, 0, 0.4 }, "Quad", "Out"), -- se aplasta al pisar
				k(0.2, { 41, -6, 4, 0, 0, 0.45 }),
				k(0.23, { 40, -9, -6, 0, 0.18, 0.45 }, "Quad", "Out"), -- impulso (en el aire)
				k(0.26, { 43, -10, -10, 0, 0, 0.44 }, "Quad", "In"),
				k(0.36, { 47, -2, -10, 0, 0, 0.42 }, "Quad", "Out"),
				k(0.43, { 49, 2, -15, 0, 0, 0.42 }, "Back", "Out"), -- espasmo hacia el lado malo
				k(0.48, { 44, 6, -9, 0, 0, 0.44 }),
				k(0.52, { 41, 9, 2, 0, 0.18, 0.46 }, "Quad", "Out"),
				k(0.56, { 42, 10, 6, 0, 0, 0.45 }, "Quad", "In"),
			},
		},
		Head = {
			Mundo = true,
			Claves = {
				k(0, { -10, 0, 16 }),
				k(0.14, { -6, -3, 20 }),
				k(0.3, { -12, 2, 13 }),
				k(0.44, { -4, -8, 26 }, "Back", "Out"), -- el espasmo del torso le llega de golpe
				k(0.56, { -10, 0, 16 }),
			},
		},
		["Right Arm"] = {
			Mundo = true,
			Desfase = 0.09,
			Claves = {
				k(0, { -45, 0, 14 }),
				k(0.16, { 30, 0, 22 }, "Quad", "Out"),
				k(0.3, { 52, 0, 10 }),
				k(0.43, { -12, 0, 26 }, "Quad", "In"),
				k(0.56, { -45, 0, 14 }),
			},
		},
		["Left Arm"] = {
			Mundo = true,
			Claves = {
				k(0, { -38, 4, -10 }),
				k(0.28, { -46, 4, -14 }),
				k(0.45, { -30, 4, -7 }, "Quad", "Out"),
				k(0.56, { -38, 4, -10 }),
			},
		},
		["Right Leg"] = {
			Mundo = true,
			Claves = {
				k(0, { 36, 0, 4 }),
				k(0.2, { -36, 0, 4 }, "Linear"), -- apoyo
				k(0.26, { -56, 0, 8 }, "Quad", "Out"), -- se dispara hacia atrás
				k(0.37, { 0, 0, 16 }, "Quad", "In"),
				k(0.48, { 42, 0, 6 }, "Quad", "Out"),
				k(0.56, { 36, 0, 4 }),
			},
		},
		["Left Leg"] = {
			Mundo = true,
			Claves = {
				k(0, { -52, 0, -8 }),
				k(0.1, { 0, 0, -16 }, "Quad", "In"),
				k(0.2, { 42, 0, -6 }, "Quad", "Out"),
				k(0.26, { 38, 0, -4 }),
				k(0.48, { -38, 0, -4 }, "Linear"), -- apoyo
				k(0.53, { -56, 0, -8 }, "Quad", "Out"), -- se dispara hacia atrás
				k(0.56, { -52, 0, -8 }),
			},
		},
	},
}

--[[
	SALTAR (no se repite): se encoge un instante y se estira con los brazos echados atrás y abiertos y la cabeza
	hacia atrás, como si algo tirara de ella. El controlador pasa a Caer al empezar a bajar.
]]
AnimacionesMonstruo.Definiciones.Saltar = {
	Duracion = 0.45,
	Bucle = false,
	Prioridad = "Movement",
	Canales = {
		Torso = {
			Claves = {
				k(0, { 40, 0, -6 }),
				k(0.07, { 50, 0, -8, 0, -0.15, 0.2 }, "Quad", "Out"),
				k(0.2, { 12, 0, -4, 0, 0.1, 0 }, "Back", "Out"),
				k(0.45, { 18, 0, -5 }),
			},
		},
		Head = {
			Mundo = true,
			Claves = {
				k(0, { -8, 0, 20 }),
				k(0.1, { 10, 0, 24 }),
				k(0.22, { -38, 0, 12 }, "Back", "Out"),
				k(0.45, { -30, 6, 18 }),
			},
		},
		["Right Arm"] = {
			Mundo = true,
			Claves = { k(0, { -10, 0, 8 }), k(0.08, { 20, 0, 6 }), k(0.24, { -70, 0, 38 }, "Back", "Out") },
		},
		["Left Arm"] = {
			Mundo = true,
			Claves = {
				k(0, { -10, 0, -8 }),
				k(0.12, { 18, 0, -6 }), -- el izquierdo, más tarde
				k(0.3, { -62, 0, -44 }, "Back", "Out"),
			},
		},
		["Right Leg"] = {
			Mundo = true,
			Claves = { k(0, { 10, 0, 6 }), k(0.2, { 34, 0, 10 }, "Quad", "Out"), k(0.45, { 24, 0, 8 }) },
		},
		["Left Leg"] = {
			Mundo = true,
			Claves = { k(0, { -6, 0, -6 }), k(0.2, { -28, 0, -12 }, "Quad", "Out"), k(0.45, { -20, 0, -10 }) },
		},
	},
}

--[[
	CAER (bucle): cuelga del aire como una marioneta: los brazos suben y bajan cada uno a su ritmo, las piernas
	se mueven solas y la cabeza se descuelga hacia atrás y da tirones.
]]
AnimacionesMonstruo.Definiciones.Caer = {
	Duracion = 1.2,
	Bucle = true,
	Prioridad = "Movement",
	Canales = {
		Torso = {
			Claves = {
				k(0, { 14, 0, -6 }),
				k(0.6, { 20, 4, -10 }),
				k(1.2, { 14, 0, -6 }),
			},
		},
		Head = {
			Mundo = true,
			Claves = {
				k(0, { -34, 0, 22 }),
				k(0.5, { -26, -8, 30 }),
				k(0.56, { -40, 10, 10 }, "Constant"), -- tirón
				k(1.2, { -34, 0, 22 }),
			},
		},
		["Right Arm"] = {
			Mundo = true,
			Claves = { k(0, { 120, 0, 30 }), k(0.55, { 150, 0, 18 }), k(1.2, { 120, 0, 30 }) },
		},
		["Left Arm"] = {
			Mundo = true,
			Desfase = 0.35,
			Claves = { k(0, { 100, 0, -40 }), k(0.7, { 140, 0, -24 }), k(1.2, { 100, 0, -40 }) },
		},
		["Right Leg"] = {
			Mundo = true,
			Claves = { k(0, { 18, 0, 10 }), k(0.6, { -10, 0, 14 }), k(1.2, { 18, 0, 10 }) },
		},
		["Left Leg"] = {
			Mundo = true,
			Desfase = 0.25,
			Claves = { k(0, { -14, 0, -12 }), k(0.6, { 12, 0, -8 }), k(1.2, { -14, 0, -12 }) },
		},
	},
}

--[[
	Nombre con el que cada estado del controlador busca su animación en VFX/Animador y en
	Combate/Datos/Recursos.Animaciones (ahí se puede poner un ID de asset para sustituirla).
]]
AnimacionesMonstruo.Nombres = {
	Reposo = "Monstruo_Reposo",
	Andar = "Monstruo_Andar",
	Correr = "Monstruo_Correr",
	Saltar = "Monstruo_Saltar",
	Caer = "Monstruo_Caer",
} :: { [string]: string }

return AnimacionesMonstruo
