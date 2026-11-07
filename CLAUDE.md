# Juego espacial de Roblox: guía del proyecto

Lee esto entero antes de hacer nada. Es la visión del juego y la forma de trabajar.

## El juego

Juego de Roblox de exploración espacial con PvP, de **calidad alta**. Nada de obbies ni juegos "brainrot": buscamos algo que enganche, con mapas, modelos y animaciones propias, VFX espectaculares y comunidad. El objetivo es que gane dinero sin ser pay-to-win.

Inspiración: la exploración de No Man's Sky y lo adictivo de Blox Fruits (poderes, progresión larga, PvP con recompensa).

### Bandos
- Dos bandos: **Humanos** y **Monstruos**. Se elige al empezar y es permanente, pero se puede cambiar pagando muchas monedas del juego, como máximo una vez cada 7 días.
- Los del mismo bando no se hacen daño.

**Humanos**
- Planeta como la Tierra: luminoso, con un sol normal, ciudades, tiendas y muchos materiales muy buenos.
- Más fácil para empezar. Su ventaja: tiendas, materiales y mejores naves y tecnología.
- Cuando llega un monstruo al planeta humano, las tiendas bajan las persianas y no le venden nada.

**Monstruos**
- Estilo creepypasta **original**: nada de copiar personajes conocidos. Forma de andar terrorífica.
- Planeta oscuro cuyo "sol" es un **agujero negro**, a unos 10 minutos de viaje del planeta humano.
- Más fuerza, agilidad y vida, pero menos materiales.
- En su planeta hay algo valioso que **solo existe allí**, para que a los humanos les compense el riesgo de ir.

**Planetas de bando**
- Cada bando tiene su **planeta grande**, que hace de base y de tutorial.
- Son **enormes**: desde el espacio se ven como esferas gigantes, y al aterrizar se pasa a un terreno inmenso.
- Desde tu planeta se ve el otro mundo a lo lejos, en el cielo.
- Se puede visitar el planeta del bando contrario y pelear allí, pero cada planeta tiene **zonas seguras para los visitantes** (por ejemplo, donde aterrizan).
- Alrededor de cada planeta de bando hay una **zona segura** sin PvP de naves.

**Primera entrada al juego**, en este orden y solo la primera vez (en Studio salen siempre, con el modo de pruebas):
1. **Elección de bando**: cámara fija, sin poder moverse; a un lado los Humanos con su planeta, en medio una grieta y al otro lado los Monstruos con su planeta. Se elige con un clic. Luego el bando solo se cambia pagando (ver arriba).
2. **Editor de personaje** del bando elegido: cada bando tiene su propio editor completo, con piezas propias (no el avatar de Roblox).
   - Interfaz de Roblox con el R6 real en medio, en reposo, que cambia al instante y se gira arrastrando. Estilo espacial: metal, luces cian y tipografía propia.
   - Humanos: a la izquierda, la piel (de clara a oscura) y las categorías con flechas ‹ › y número (cabello, cejas, ojos, nariz, boca, chaqueta, pantalón y accesorio). A la derecha, una rueda de color con brillo para el pelo, la chaqueta, el pantalón y los detalles. Abajo, Atrás, Aleatorio y Continuar. En móvil, las categorías van abajo en horizontal.
   - Peinados y accesorios: modelos de Blender de menos de 1.500 triángulos, puestos como Accessory. Cara: texturas (Decals). Ropa: el cuerpo se pinta y lleva detalles 3D que se pueden colorear.
   - **«Usar mi avatar de Roblox»** (solo Humanos): el personaje coge el avatar real del jugador (ropa, accesorios, cara y colores) en vez de las piezas del juego, siempre en R6. Un avatar R15 se convierte con su HumanoidDescription; lo que no cabe en R6 se quita y se avisa en el editor (ropa en capas, tamaño del cuerpo, animaciones y emotes, partes de paquetes). Máximo 6 accesorios por rendimiento en móvil (`ConfigEditor.Avatar`). Se puede volver a las piezas sin perder lo elegido.
   - El servidor carga el avatar con el UserId del jugador (no se fía del cliente), lo prepara con `Personaje/AvatarR6` y se lo pasa a un R6 limpio (`Constructor.PonerAvatar`). Guarda si usa avatar o piezas (`Apariencia.UsarAvatar`). Ojo: `Humanoid:ApplyDescription` falla en un personaje editado, por eso no se usa sobre el personaje.
   - «Atrás» vuelve gratis a la elección de bando solo mientras no se haya terminado el primer personaje.
   - El servidor valida todo: las opciones tienen que existir y los colores ser "#RRGGBB".
   - Monstruos: tendrán su propio editor, con otras categorías (silueta, ojos, piel, cuernos...).
3. **Gráficos**: Baja, Media, Alta o Ultra, con el recomendado para el dispositivo marcado. Se puede cambiar después desde los ajustes.
4. **Cinemática** del bando, de 45 a 60 s y que se puede saltar: «Esta es tu historia» → tu personaje mirando un atardecer → «5 años después» con escenas épicas → vuelta al atardecer → «Pero todo empieza aquí» → el jugador toma el control y empieza el tutorial.

### Bucle principal
1. Empiezas en el planeta de tu bando, que te enseña a moverte, pelear, escanear y craftear.
2. Misión inicial: **forjar tu primera nave** con la gente de tu planeta.
3. Despegas y viajas por el espacio esquivando **campos de asteroides** que dañan la nave.
4. Hay **10 planetas pequeños** a distintas distancias, cada uno con recursos, criaturas y peligros.
5. El primer viaje dura 2-3 minutos con eventos. Los lejanos, 8-10 minutos. Más tarde se desbloquea un motor de salto.
6. **PvP en naves** (armas de nave) en todo el espacio salvo las zonas seguras, y **PvP en planetas** (poderes y armas).
7. **Niveles, escáner y crafteo**: escaneas criaturas, plantas y minerales, recoges recursos y fabricas mejoras.

### Lista de la v1 (lo que entra en el lanzamiento)
- Los 2 planetas de bando y 4 planetas pequeños.
- 1 nave construida por piezas en el hangar (ver «Naves y armas»). Sus mejoras actuales son Casco, Escudo, Motor, Armas, Escaner y Carga. ("Escaner" va sin tilde a propósito: es la clave del código).
- 1 campo de asteroides y los eventos del primer viaje.
- Niveles.
- 8-10 poderes, 3-4 armas, escáner, crafteo básico.
- PvP en naves y en un planeta disputado, que es uno de los 4 planetas pequeños.
- Cambio de bando de pago (monedas del juego, una vez cada 7 días).
- Pantalla de elección de bando con la grieta (solo la primera vez).
- Persianas: las tiendas humanas no venden a los monstruos.
- Andar terrorífico de los monstruos.
- Un recurso exclusivo del planeta de los monstruos (uno solo y sencillo).
- NPCs y misiones (ver «Progresión y misiones»).
- Forja básica de armas.
- Poderes humanos desbloqueables.
- Maestría de armas y poderes.
- Algún jefe.

Lo que no esté en esta lista no se hace hasta después del lanzamiento. Para después quedan, por ejemplo: el motor de salto, la pistola de portales, los planetas invadidos y terraformar.

### Progresión y misiones
- **NPCs** con animación de reposo en pueblos y ciudades. Dan misiones (picar X minerales, cazar X criaturas...) a cambio de XP y monedas. Al principio son sencillas y luego más difíciles.
- **Nivel máximo: 3.000.**
- **Maestría:** cada arma y cada poder sube de nivel con el uso. Hacen falta desde 1 enemigo para desbloquear el primer ataque hasta 300 para el último. Vale para los dos bandos.
- **Poderes por bando:** los humanos no nacen con poderes; los desbloquean con nivel, dinero y yendo a un sitio especial. Los monstruos ya los tienen.

### Naves y armas
- **Naves por piezas** en el hangar: cabina, casco, motores, alas, armas y escudos. Cada pieza cambia cómo vuela la nave. Sustituyen a la nave predeterminada actual, que parece un avión y no es original.
- **Forja de armas** (espadas, etc.) con los minerales.

### Jefes
- Difíciles y épicos: gigantes, con fases que cambian sus ataques. Algunos son para ir en grupo, y sueltan materiales raros.
- **Leviatán:** jefe gigante que custodia un sector exterior. Hay que derrotarlo para poder entrar en ese sector.

### Llave Maestra
- Es el generador procedural de planetas por semilla. Una semilla da un planeta entero: bioma, relieve, mar, flora, minerales y nombre.
- Rodrigo lo tiene hecho aparte y se meterá en el repositorio más adelante.
- De ella salen los planetas de los sectores lejanos y los que se invaden.

### Descubrimiento y portales
- **«Descubierto por...»:** el primer jugador que descubre un planeta queda registrado para todo el juego. Quizá puede ponerle nombre.
- **Pistola de portales** (después de la v1):
  - **Normal:** se fabrica con materiales muy difíciles, gasta combustible en cada portal y solo lleva a planetas que TÚ has visitado.
  - **VIP** (gamepass de 500 Robux): no gasta combustible, es infinita y lleva a cualquier planeta que ALGÚN jugador haya descubierto.
  - Ninguna lleva a planetas que nadie ha descubierto ni a planetas invadidos.
  - Ninguna lleva a sectores cuyo requisito no hayas cumplido (el de radiación sin el escudo, el del Leviatán sin haberlo derrotado).
  - Hay un tiempo de espera corto entre portales, para que no sirvan para huir en mitad de un PvP.

### Planetas invadidos (final de juego, después de la v1)
- **Requisitos:** desde el nivel 2.000, cada jugador puede invadir UN planeta, que tiene que ser uno que nadie haya descubierto todavía. La Llave Maestra genera planetas infinitos, así que siempre habrá.
- **Fábricas:** en su planeta pone fábricas para sacar casi todo tipo de materiales y fabricar mejores armas. Producen mientras no está, pero mucho más despacio y con un tope.
- **Ataques:**
  - Otros jugadores se lo pueden invadir, así que puede poner escudos y defensas.
  - Solo se puede invadir el planeta de jugadores de nivel parecido.
  - Tras sufrir una invasión hay un escudo automático de unas horas.
  - Cuando el dueño sale del juego, su planeta desaparece y nadie puede atacarlo sin él.
- **Visualizador del planeta:** un mapa visto desde arriba para colocar defensas, fábricas y edificios sin dar la vuelta andando.
- **Terraformar:** plantar árboles, quitar montañas, poner ríos. Solo se guardan los cambios sobre la semilla de la Llave Maestra.
  - Ojo: quitar montañas o abrir ríos es difícil con planetas hechos de mallas. Más adelante habrá que buscar una técnica para esto.

### Monetización (sin pay-to-win)
Gamepasses (x2 monedas, VIP, almacén extra), skins de nave y de poderes, pase de temporada. Nada que haga ganar peleas comprando.
- **Pistola de portales VIP** (gamepass de 500 Robux, después de la v1). Es comodidad, no poder: no da daño, ni vida, ni armas. Límites (ver «Descubrimiento y portales»):
  - No lleva a sectores cuyo requisito no hayas cumplido: el de radiación sin el escudo, el del Leviatán sin haberlo derrotado.
  - No lleva a planetas que nadie ha descubierto ni a planetas invadidos.
  - Tiene un tiempo de espera corto entre portales, para que no sirva para huir en mitad de un PvP.

## Reglas técnicas
- **Solo R6.** Nunca uses partes de R15. La prueba `SoloR6` lo comprueba.
- **Servidor autoritario.** El cliente solo pide; el servidor valida (cooldown, distancia, estado) y aplica el daño, las monedas, las compras.
- Código en Luau con `--!strict`, en módulos, comentado en español.
- Proyecto con Rojo: `src/shared` → ReplicatedStorage, `src/server` → ServerScriptService, `src/client` → StarterPlayerScripts.
- Todo lo ajustable (colores, tiempos, daños, IDs de animaciones, texturas y sonidos) va en módulos de datos, no metido en el código.
- Rendimiento en móvil siempre: reutilizar objetos de VFX, limitar partículas, StreamingEnabled en mapas grandes.
- Pruebas: `lune run pruebas/ejecutar`. Tienen que pasar antes de fusionar.

## Calidad
- **Calidad por encima de velocidad.** Sin atajos ni partes a medias.
- Los VFX y las animaciones son lo que más se ve: incluso una habilidad común tiene que verse espectacular.
- Las animaciones de combate llevan anticipación, impacto exagerado, recuperación, hitstop y temblor de cámara.
- Si algo no se puede hacer bien, dilo en vez de entregarlo a medias.

## Forma de trabajar
- **Director (Claude Code en local)**: tiene Roblox Studio conectado por MCP. Prueba todo de verdad: `start_stop_play`, `screen_capture`, `user_keyboard_input`, `user_mouse_input`, `get_console_output`, `execute_luau`. Rojo sincroniza esta carpeta con Studio.
- **Nada está terminado hasta verlo funcionar en Studio con capturas.** Que las pruebas automáticas pasen no basta.
- El director puede repartir trabajo a sesiones en la nube (`claude --cloud "encargo"`), una por área: programación, VFX, animación, Blender. Esas sesiones no tienen Studio, así que el director revisa y prueba todo lo que entregan antes de darlo por bueno.
  - La sesión en la nube clona el repositorio de GitHub en la rama actual, no la copia local: **sube antes la rama** con lo que necesite.
  - Para seguir una sesión desde aquí: `claude --teleport <id>`. Para mandarle otro mensaje: `claude -p "mensaje" --cloud <id>`.
- Cada trabajo en su propia rama, con commits pequeños en español, y pull request a `main`.
- **Rodrigo da el visto bueno final.** Enséñale capturas del antes y el después.
