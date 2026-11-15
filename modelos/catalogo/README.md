# Catálogo de modelos «Humanos vs Monstruos»

Los 80 assets 3D del juego (81 archivos: el cofre sale cerrado y abierto), low-poly estilizado, generados con scripts de
Python en Blender sin pantalla (`bpy` 5.2). Nada está hecho a mano: todo sale de `herramientas/` y se puede regenerar.

> **Nada de esto se ha visto todavía en Roblox Studio.** La sesión que lo generó no tiene Studio. Según CLAUDE.md, el
> director tiene que importarlo y probarlo con capturas antes de darlo por bueno. Ver
> [«Qué hay que comprobar en Studio»](#qué-hay-que-comprobar-en-studio).

`rondas/rNN.jpg` es la hoja de cada ronda (la vista 3/4 de cada modelo).

## Qué hay en cada carpeta de modelo

`<categoria>/<modelo>/`:

| Archivo | Qué es |
| --- | --- |
| `<modelo>.fbx` | El modelo. 1 unidad = 1 stud, arriba = Y, con el GIRO_IMPORTACION aplicado |
| `<modelo>_color.png` | Base Color del atlas 1024 × 1024 (con la oclusión ambiental horneada) → `ColorMap` |
| `<modelo>_normal.png` | Normales (tangente, formato OpenGL) → `NormalMap` |
| `<modelo>_roughness.png` | Rugosidad (gris) → `RoughnessMap` |
| `<modelo>_metalness.png` | Metal (gris) → `MetalnessMap` |
| `<modelo>_emision.png` | Máscara de lo que brilla (solo si el modelo tiene algo que brille) |
| `<modelo>_turnaround.png` | Frente, 3/4, lateral, 3/4 trasera, arriba y malla, renderizado **con las texturas horneadas** |
| `<modelo>.json` | Triángulos, tamaño, piezas (centro, pivote, padre) y anclas, en studs y ejes de Roblox |
| `montar_<modelo>.luau` | Solo enemigos: script de la barra de comandos que crea los Motor6D |

## Rondas

| Ronda | Carpeta | Modelos |
| --- | --- | --- |
| 1 | `edificios_humanos/` | tienda_humana, edificio_residencial, torre_oficinas, hangar_humano, forja_humana, cuartel_humano, hospital_humano, centro_mando |
| 2 | `edificios_monstruos/` | guarida_monstruo, torre_cristal_oscuro, nido_monstruo, altar_monstruo, mercado_monstruo, forja_monstruo |
| 3 | `vegetacion_humana/` | arbol_roble, arbol_pino (3 alturas), arbol_frutal, arbusto_01, hierba_grupo |
| 4 | `vegetacion_monstruo/` | arbol_alienigena_01, arbol_alienigena_02, hongo_gigante, coral_alienigena, esporas_suelo |
| 5 | `minerales/` | piedra_comun (3 formas), piedra_grande, mineral_hierro, mineral_cobre, mineral_oro, mineral_cristal_azul, mineral_cristal_purpura, mineral_cristal_naranja |
| 6 | `armas/` | pico_madera, pico_hierro, pico_acero, espada_hierro, espada_acero, hacha_hierro, escudo_hierro, escudo_acero |
| 7 | `armaduras/`, `estructuras/` | armadura_hierro, armadura_acero, casco_hierro, casco_acero · plataforma_lanzamiento, torreta_defensa, generador_energia |
| 8 | `enemigos/` | escarabajo_gigante, jabali_roca, golem_musgo, arana_cristal, serpiente_sombra, guardian_oscuro |
| 9 | `props/` | farola_humana, farola_monstruo, barril_madera, caja_madera, letrero_madera, banco_piedra |
| 10 | `props/` | fuente_humana, antorcha_muro, bandera_humana, bandera_monstruo, cofre_tesoro, cofre_tesoro_abierto, portal_base |
| 11 | `nave/` | casco_nave_pequeno, casco_nave_mediano, casco_nave_grande, cabina_basica, cabina_avanzada, ala_pequena, ala_grande, motor_basico |
| 12 | `nave/` | motor_avanzado, motor_turbo, arma_laser_nave, arma_misiles_nave, escudo_nave, estabilizador, tren_aterrizaje |

Los nombres van sin «ñ» (`arana_cristal`, `casco_nave_pequeno`, `ala_pequena`): los nombres de archivo con «ñ» dan
problemas al subir assets.

## Decisiones que conviene conocer

- **Un atlas por modelo, varias piezas.** Todas las mallas de un FBX comparten el mismo atlas. Lo que brilla y lo que
  es cristal sale como **mallas aparte** dentro del FBX (`<modelo>_neon`, `_neon_azul`, `_cristal`, `_llama`, `_agua`…)
  para ponerles `Material = Neon` o `Glass` en Roblox, que es lo que de verdad brilla y transparenta allí. También
  están pintadas en el atlas, así que con `SurfaceAppearance` se ven bien igualmente.
- **Las vetas y ventanas luminosas** (vetas violeta de los monstruos, ventanas de la torre de oficinas, ojos de los
  enemigos) no son piezas aparte: van pintadas en el color y marcadas en `_emision.png`.
- **Piezas móviles** (persiana de la tienda, puertas del hangar, tapa del cofre, cabeza y cañones de las torretas,
  pata del tren de aterrizaje, cartel de los letreros…) son mallas aparte con su `pivote` en el JSON.
- **Carteles en blanco**: `<modelo>_cartel` es la pieza donde va el `SurfaceGui` con el texto.
- **Límites de triángulos**: 5.000 por modelo, 10.000 en edificios grandes, 15.000 el hangar. Todos quedan por debajo
  (el JSON y la cabecera del turnaround dan la cifra exacta).
- **Grosor real**: no hay planos sueltos; toldos, banderas, cúpulas y membranas tienen espesor.

## Importar en Studio

1. **File → Import 3D** y elige el `.fbx`. Las texturas están en la misma carpeta con el nombre que el FBX espera.
2. En el importador: **Scale Unit = Stud** (los números del FBX ya son studs). `Anchored` activado para escenario.
3. Cada malla del FBX es una `MeshPart` con el mismo nombre. En la pieza principal, crea (o revisa) la
   `SurfaceAppearance`: `ColorMap`, `NormalMap`, `RoughnessMap`, `MetalnessMap` con los cuatro PNG.
4. Piezas `_neon*`, `_llama`, `_lava`, `_runas`, `_gema`: **Material Neon** y el color de la tabla de abajo.
   Piezas `_cristal`, `_agua`, `_domo`: **Material Glass**, Transparency 0,3–0,5.
5. Anclas: el JSON de cada modelo da los puntos útiles (`LuzToldo`, `Puerta`, `Yunque`, `Llama`, `Centro` del portal,
   `Boca` de los cañones, acoples de las piezas de nave…). Son `Attachment` que hay que crear con ese nombre.

| Pieza | Color |
| --- | --- |
| `_neon` humano | cian `#3DF2FF` |
| `_neon_azul` (hospital) | `#2E7BFF` |
| `_neon_naranja`, `_llama` | `#FF8A1F` / `#FFB52E` |
| `_neon_rojo` (balizas) | `#FF3B30` |
| `_neon` monstruo, `_lava` | violeta `#C04DFF` / `#D24DFF` |
| `_neon_magenta` | `#FF3DD4` |
| `_runas` (portal), `_gema` | `#6FE8FF` / `#35D8FF` |
| `_cristal` humano | `#4CC9EA` |
| `_cristal` de minerales | azul `#35D8FF`, púrpura `#9A3DFF`, naranja `#FF9A1F` |

### Ejes y GIRO_IMPORTACION

Los modelos se construyen en Blender con Z arriba y el frente hacia -Y. Antes de exportar se les aplica el
**GIRO_IMPORTACION** (180° sobre la vertical), el mismo que `MontarRegion.GIRO_IMPORTACION` corrige a mano en la región 1:
así, una vez importada, la malla coincide con la conversión del proyecto **Blender (x, y, z) → Roblox (x, z, -y)**.
Todas las coordenadas de los JSON están ya en ejes de Roblox con esa conversión. El frente del modelo queda
mirando a **+Z** de Roblox.

### Enemigos (rig por piezas, estilo R6)

Cada enemigo son piezas rígidas (sin huesos ni deformación, como pide «Solo R6»), cada una con su articulación:

1. Importa el FBX con **Anchored desactivado** y pon la `SurfaceAppearance` en todas las piezas (comparten atlas).
2. Selecciona el modelo importado, abre **View → Command Bar**, pega `montar_<enemigo>.luau` y pulsa Enter.
3. El script crea un `HumanoidRootPart` que mira al frente de la criatura, une cada pieza a su padre con un
   `Motor6D` en su articulación y añade `AnimationController` + `Animator` (o `Humanoid` R6 en el guardián).

`guardian_oscuro` usa los nombres de R6 (`Torso`, `Head`, `Left Arm`, `Right Arm`, `Left Leg`, `Right Leg`) más `Arma`,
con juntas `Neck`, `Left Shoulder`… Mide 2,4 veces un R6 normal, así que las animaciones R6 de Roblox le quedarán
pequeñas de recorrido: necesita las suyas. Los `EspecieId` de los scripts (`Criatura_GolemMusgo`, etc.) **no están
dados de alta** en `src/shared/Exploracion/Datos/Especies.luau`: eso es diseño del juego.

### Armaduras y cascos

`armadura_*`: el origen es el centro del `Torso` R6; `_peto` va soldado al torso y `_hombrera_izq/_der` a cada brazo
(su `pivote` es el centro del brazo). `casco_*`: el origen es el centro de `Head`.

### Piezas de nave

El origen de cada pieza es su punto de acople y el morro mira al frente del modelo. Las anclas de los cascos
(`Cabina`, `AlaIzq`, `AlaDer`, `Motor…`, `Arma…`, `Tren…`, `Estabilizador`, `Escudo`) dicen dónde va cada módulo. Solo
hay ala **derecha**: su perfil es simétrico arriba/abajo, así que la izquierda es la misma malla girada 180° sobre el
eje morro-cola (Roblox no refleja mallas). Los motores expulsan hacia atrás (ancla `Escape`).

## Qué hay que comprobar en Studio

- Que con **Scale Unit = Stud** los modelos entran con el tamaño del JSON (`tam_studs`). Si salen 100 veces más grandes
  o más pequeños, el importador está leyendo otra unidad.
- Que las piezas quedan con orientación (0, 0, 0) y que el frente mira a +Z, como dice este documento.
- Que el importador enlaza solo las cuatro texturas; si no, la `SurfaceAppearance` a mano.
- Los `montar_<enemigo>.luau`: que las articulaciones caen en su sitio y que `HipHeight` del guardián lo deja en el suelo.
- El mapa de normales en superficies grandes (panelado de los edificios): si en Roblox se ve invertido, hay que
  invertir el canal verde.
- La cúpula del `centro_mando`, el domo de `escudo_nave` y el tubo del `generador_energia` son cristal con grosor:
  comprobar que con Glass se ve el interior.

## Regenerar

```bash
python3 -m venv .venv && .venv/bin/pip install bpy==5.2.3 pillow numpy
```

```bash
.venv/bin/python modelos/catalogo/herramientas/generar.py r01
```

```bash
.venv/bin/python modelos/catalogo/herramientas/hoja_ronda.py
```

`generar.py rNN` acepta `--solo modelo1,modelo2`, `--faltan` (solo los que no tienen JSON) y `--rapido` (atlas de
256 y renders pequeños, para probar formas en segundos; con `--salida /otra/carpeta` no pisa los buenos). A calidad
completa tarda alrededor de un minuto por modelo con 4 núcleos.

| Script | Para qué |
| --- | --- |
| `lib.py` | Primitivas (cajas, revoluciones, tubos, lofts, prismas, cristales, rocas), materiales procedurales, horneado del atlas, turnaround y exportación FBX |
| `paleta.py` | **Todos los colores y materiales**: lo que hay que tocar para cambiar el aspecto de una facción |
| `comunes.py` | Piezas repetidas: ventanas, barandillas, antenas, banderas, cristales, setas, runas, ramas |
| `rNN_*.py` | Los modelos de cada ronda. Las medidas van arriba de cada función |
| `generar.py`, `hoja_ronda.py` | Lanzar una ronda y montar su hoja |
| `plantilla_montar_rig.luau` | Plantilla del script de Studio de los enemigos |
| `verificar_fbx.py` | Reimporta un FBX y lista mallas, triángulos, tamaño, UV y texturas |
