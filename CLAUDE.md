# Juego espacial de Roblox: guía del proyecto

Lee esto entero antes de hacer nada. Es la visión del juego y la forma de trabajar.

## El juego

Juego de Roblox de exploración espacial con PvP, de **calidad alta**. Nada de obbies ni juegos "brainrot": buscamos algo que enganche, con mapas, modelos y animaciones propias, VFX espectaculares y comunidad. El objetivo es que gane dinero sin ser pay-to-win.

Inspiración: la exploración de No Man's Sky y lo adictivo de Blox Fruits (poderes, progresión larga, PvP con recompensa).

### Bandos
- Dos bandos: **Héroes** y **Villanos**. Se elige al empezar y es permanente, pero se puede cambiar pagando muchas monedas del juego, como máximo una vez cada 7 días.
- Cada bando tiene su **planeta grande**, que hace de base y de tutorial.
- Alrededor de cada planeta de bando hay una **zona segura** sin PvP de naves.
- En la v1 no se puede aterrizar en el planeta del bando contrario: está protegido.
- Los del mismo bando no se hacen daño.

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
- 1 nave con mejoras: Casco, Escudo, Motor, Armas, Escaner, Carga. ("Escaner" va sin tilde a propósito: es la clave del código).
- 1 campo de asteroides y los eventos del primer viaje.
- Niveles.
- 8-10 poderes, 3-4 armas, escáner, crafteo básico.
- PvP en naves y en un planeta disputado, que es uno de los 4 planetas pequeños.
- Cambio de bando de pago (monedas del juego, una vez cada 7 días).

Lo que no esté en esta lista no se hace hasta después del lanzamiento. Por ejemplo, el motor de salto queda para después.

### Monetización (sin pay-to-win)
Gamepasses (x2 monedas, VIP, almacén extra), skins de nave y de poderes, pase de temporada. Nada que haga ganar peleas comprando.

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
