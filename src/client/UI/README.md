# Interfaz (UI/HUD)

Toda la interfaz del juego: el HUD en partida, la barra lateral y las nueve pantallas de menú (Personaje, Inventario,
Poderes, Tripulación, Ranked, Índice, Mapa galáctico, Ajustes y Tienda). Estructura y estética inspiradas en Vox Seas,
adaptadas al espacio.

## Ver el diseño sin Studio: el preview

Abre `preview_ui_completa.html` en el navegador (doble clic). Es un solo archivo, sin internet ni dependencias.

- Simula la pantalla de Roblox a 1280×720, con todas las pantallas y la barra lateral funcionando.
- Abajo hay botones para saltar a cada pantalla, cambiar de bando (Humano/Monstruo), recibir daño, curarse, ver el HUD
  sobre una escena clara y abrir la **galería de iconos**.
- Teclas: `P` personaje · `I` inventario · `K` poderes · `M` mapa (en partida: minimapa) · `Esc` cerrar · `1`/`2` armas ·
  `Z X C V` habilidades · `E` interactuar (pasa el ratón por el contenedor del suelo).
- Arrastrar sobre la escena gira la "cámara" y con ella el minimapa. En el inventario se puede arrastrar un objeto a su slot.

Lo que se aprueba en el preview es lo que construye el código: mismos colores (EspacialTheme), mismas medidas (unidades
de diseño, ver abajo), mismos iconos (el mismo SVG) y los mismos datos de demostración (DatosDemo). La fuente del preview es
Montserrat porque GothamSSm no se puede incrustar; en Roblox se usa GothamSSm.

## Unidades de diseño

Todo se diseña en un lienzo de **960×540** que se escala a la pantalla (`Componentes/Lienzo`): a 1280×720 una unidad son
1,33 px y a 1920×1080, 2 px. Así los tamaños del encargo (barra lateral de 52, slots de 46, casillas de 65, letras de 6 a 14)
se leen bien en cualquier pantalla y el preview y Roblox coinciden.

## Estructura

```
UI/
├── HUDController.luau          Controlador: crea la ScreenGui, abre/cierra pantallas, teclas, desenfoque
├── Modules/
│   ├── Sidebar, HUDPartida, Panel*.luau      Una pantalla por módulo
│   ├── EstadoUI.luau            Única fuente de datos de la UI (reales + demostración)
│   ├── Contexto.luau            Lo que el controlador da a cada pantalla
│   ├── Componentes/             BarraVida, SlotEquipo, CardItem, FilaMiembro, CardModo, EntradaIndice, BotonSidebar,
│   │                            TabSelector, StatRow, Tooltip, Notificacion + Primitivas, Lienzo, Ventana, Modal,
│   │                            Controles (deslizador, interruptor, desplegable, tecla) y Muneco (paper doll)
│   ├── Iconos/                  IconBuilder (crea los ImageLabel) e IdsIconos (ID de Roblox de cada PNG)
│   ├── Animaciones/UITweens     Todas las transiciones (TweenService)
│   ├── Temas/EspacialTheme      Colores, tamaños, fuentes y tiempos: la única fuente de colores
│   └── Datos/                   ConfigUI (teclas, ajustes, productos), CatalogoUI (arte de lo que ya existe),
│                                DatosDemo (lo que aún no existe en el juego)
├── Assets/                      SVG fuente y PNG de iconos (IconSVGs, IconPNGs) y de arte a color (ArteSVGs, ArtePNGs)
└── preview_ui_completa.html
```

`HUDController` es un **ModuleScript** y no un LocalScript aparte: lo arranca `init.client.luau` después de la red, los datos,
el combate y la exploración. Un segundo LocalScript correría en paralelo y podría usar la red antes de que esté lista.

## Iconos: siluetas propias, ningún emoji

Opción A del encargo: SVG propios → PNG de 128×128 → ImageLabel teñido con `ImageColor3`.

- La fuente de todos los iconos es `herramientas/iconos_ui/iconos.mjs` (65 iconos de una tinta: los 22 pedidos más interfaz,
  ajustes, razas, habilidades y las 8 insignias de rango) y `arte.mjs` (40 piezas a color: objetos, criaturas, plantas,
  planetas y tienda, con los colores de los modelos 3D del repositorio).
- `node herramientas/iconos_ui/generar.mjs` escribe los `.svg`, los `.png` (fondo transparente), el sprite del preview y
  la lista de `IdsIconos.luau` (conservando los ID ya pegados). Necesita Node 18+ y Playwright.

**Subir los iconos (una vez, y cada vez que cambie alguno):**

1. Studio → View → Asset Manager → **Bulk Import**. Elige todos los PNG de `Assets/IconPNGs` y `Assets/ArtePNGs` (súbelos al
   grupo del juego, como los modelos).
2. Clic derecho en cada imagen → **Copy ID** y pégalo en `Modules/Iconos/IdsIconos.luau` como `"rbxassetid://<número>"`.

Mientras falte un ID, en su lugar se ve un marcador (un rombo del color del icono, o una esfera del color del objeto) y la
consola avisa una sola vez de cuáles faltan. **Hasta subirlos, en Studio no se verán los iconos.**

## De dónde salen los datos

| Real (servidor) | Demostración (`DatosDemo`, hasta que exista el sistema) |
| --- | --- |
| nombre, nivel, XP, monedas, bando | gemas, clan, título, clase, puntos de atributos y de poderes |
| materiales de la bodega y su capacidad (mejora Carga) | equipo (armas, armaduras, accesorios), consumibles, especiales |
| especies descubiertas y veces escaneadas (Índice) | árbol de poderes con puntos, tripulación, ranked, builds |
| poderes del HUD: nombre, tecla, cooldown, energía | planetas pequeños del mapa e índice de planetas |
| vida (Humanoid) | escudo personal, estadísticas detalladas, estadísticas rápidas |

Lo que el jugador "cambia" en datos de demostración (equipar, repartir puntos, desbloquear un nodo) solo cambia esta sesión,
y los avisos lo dicen. Las compras con monedas y gemas avisan de que falta el servidor; las de Robux abren la compra de
Roblox si el ID está en `ConfigUI` (y entonces hace falta un `ProcessReceipt` en el servidor, que aún no existe).

## Integración con lo que ya había

Con `ConfigUI.SustituirInterfacesAntiguas = true` (por defecto):

- El HUD de combate antiguo (`Combate/Interfaz`) se oculta: el nuevo enseña la misma vida, energía y cooldowns, y sus
  casillas piden las habilidades con `ServicioCombate.Solicitar`. El antiguo sigue llevando la cuenta de los cooldowns.
- La pastilla y el panel de la bodega (`Exploracion/PanelInventario`) se ocultan y la tecla I abre el inventario nuevo.
- Los `ProximityPrompt` se dibujan con el aviso del HUD ("[E] Recoger") en vez del de Roblox (`ConfigUI.AvisoInteraccionPropio`).
- Al pilotar una nave el HUD se oculta (`ServicioCombate.PausaCambiada`).

## Teclas (y por qué no son las del boceto)

El juego ya usa `W A S D` (andar), `Q` (escanear), `R` (picar), `E` (interactuar), `F` (aterrizar), `Z X C` (Rayo), `V B N`
(Gravedad) y `C`/`Ctrl` (bajar con la nave). Por eso:

- **Personaje = P** (no C, que es la definitiva del Rayo).
- Las cuatro casillas de habilidad enseñan las **teclas reales** de `Combate/Datos/Poderes` (Z, X, C, V) en vez de Q/W/E/R:
  W es andar, Q escanear, E interactuar y R picar. Si se cambia una tecla en Poderes, el HUD la cambia solo.
- Inventario = I, Poderes = K, Mapa = M, armas = 1 y 2. Todas en `ConfigUI.Teclas` y cambiables en Ajustes.
- `Escape` puede quedárselo Roblox para su menú: la X roja de cada ventana siempre cierra.

## Rendimiento (móvil)

- Los marcos grandes (ventanas, HUD) son Frames normales; solo durante el fundido se meten en un CanvasGroup temporal.
- Un único bucle por fotograma para cooldowns y energía; el minimapa se actualiza a 15 Hz y reutiliza sus puntos; nada corre
  con el HUD oculto. El personaje 3D del muñeco solo gira con la pestaña a la vista.
- El desenfoque del menú es más suave en móvil (`Theme.Tiempos.DesenfoqueMenuMovil`).

## Comprobado y pendiente

- Comprobado fuera de Studio: análisis de tipos con `luau-lsp` (modo estricto) sin errores en la UI, `lune run pruebas/ejecutar`
  (prueba `InterfazUI`: --!strict, ningún emoji, colores solo del tema, iconos completos y sincronizados, datos coherentes,
  sin pay-to-win, teclas sin choques) y capturas del preview en Chromium.
- **No probado en Studio** (esta sesión no lo tiene). Hay que revisar con capturas: el escalado en distintas pantallas y en
  móvil, el ViewportFrame del personaje, el reloj de cooldown, los fundidos, el minimapa, el arrastrar y soltar y el aviso de
  los ProximityPrompt. El espaciado de letras de los títulos usa espacios finos (U+2009): si la fuente no los tiene, se
  verían cajitas y habría que quitar `Espaciado = true`.
- Sin efecto todavía: distancia de render, sensibilidad, idioma y región (Ajustes); los ajustes no se guardan entre sesiones.
- Pendientes de servidor: equipo, atributos, árbol de poderes, clanes, ranked, gemas, compras de la tienda, consumibles, tirar
  objetos y viajar desde el mapa.
