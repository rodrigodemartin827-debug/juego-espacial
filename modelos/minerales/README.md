# Los 100 minerales

Minerales y piedras para picar, de 7 rarezas, generados con Blender sin pantalla (`bpy`). No hay nada hecho a mano:
todo sale de `modelos/herramientas/minerales*.py` y se puede regenerar.

| Rareza | Color HUD | % aparición | Valor | Cantidad | Triángulos que se buscan |
| --- | --- | --- | --- | --- | --- |
| Común | `#FFFFFF` blanco | 35 % | 1–5 | 25 | ~1.600 |
| Poco común | `#4CD964` verde | 25 % | 6–15 | 20 | ~2.000 |
| Raro | `#3D8BFF` azul | 18 % | 16–40 | 18 | ~2.400 |
| Épico | `#A855F7` púrpura | 12 % | 41–100 | 15 | ~2.800 |
| Legendario | `#FF9F1C` naranja | 7 % | 101–300 | 12 | ~2.850 |
| Mítico | `#E0213B` carmesí | 2,5 % | 301–800 | 7 | ~2.900 |
| Celestial | `#3DF2FF` cian | 0,5 % | 801–2.000 | 3 | ~2.900 |

Límite duro: **3.000 triángulos** por mineral (sumando todas sus partes); el script falla si se pasa. Los comunes
van más ligeros porque son los que más aparecen a la vez en pantalla (móvil).

## Qué hay en cada carpeta

```
minerales/<id>/
  <id>.fbx          las MeshPart del mineral (ver «Partes»)
  <id>.json         triángulos, tamaño en studs, rareza, valor, % de aparición y cómo montar cada parte
  turnaround.jpg    6 vistas: Frente, 3/4, Lateral, 3/4 trasera, Arriba y la malla (wireframe)
  texturas/         atlas 1024×1024 común a todas las partes:
    <id>_color.png      color base (con la oclusión ambiental horneada)
    <id>_normal.png     normales (espacio tangente, de la malla alta)
    <id>_rugosidad.png  rugosidad (gris)
    <id>_metal.png      metal (gris)
    <id>_emision.png    emisión (solo si el mineral brilla)
catalogo.json       los 100 JSON juntos, con la tabla de rarezas
hoja_todos.jpg      los 100 de un vistazo (nombre en el color de su rareza)
rondas/ronda_XX.jpg la vista 3/4 de los 10 minerales de cada ronda, para revisarlos de un vistazo
```

## Medidas, ejes y giro

- **1 unidad de Blender = 1 stud.** El FBX se exporta con *Apply Scalings = FBX All*. En el importador de Studio
  comprueba que el tamaño coincide con `tamano_studs` del JSON; si sale 3,57 veces mayor o menor, cambia
  *Scale Unit* (Stud/Meter).
- **GIRO_IMPORTACION:** antes de exportar se gira 180° sobre el eje vertical (la Y de Roblox), el mismo giro que
  `MontarRegion.GIRO_IMPORTACION`. No hay que girarlos en Studio.
- La base está en y = 0 y centrada: se apoyan en el suelo (se pueden hundir un poco).
- Todas las mallas son cerradas, con las normales hacia fuera.

## Partes y cómo montarlas en Studio

Importa con **Avatar → Import 3D**, *Anchored* activado. Cada parte llega como una `MeshPart`:

| Parte | Qué es | En Studio |
| --- | --- | --- |
| `<id>` | El cuerpo opaco (roca, metal, gema opaca) | `SurfaceAppearance` con ColorMap, NormalMap, RoughnessMap y MetalnessMap del atlas |
| `<id>_cristal` | Lo translúcido | Material **Glass** con el `Color` y la `Transparency` del JSON |
| `<id>_neon` | Lo que brilla | Material **Neon** con el `Color` del JSON (y la PointLight de `luz_recomendada`) |
| `<id>_interior` | Lo que se ve dentro de un cristal (humo, fósil, paisaje) | Como el cuerpo |
| `<id>_orbita` | Trozos que flotan alrededor | Como el cuerpo (o Neon si el JSON lo dice); se animan en el cliente |

Todas las partes comparten el mismo atlas UV, así que las texturas se suben una vez por mineral. Las animaciones
(órbitas, latidos, discos que giran) están descritas en el campo `Animacion` de cada parte del JSON y son del
cliente (TweenService / RenderStepped), nunca del servidor. Con muchos minerales a la vista, deja la PointLight
solo en los cercanos.

## Regenerar

```bash
python3 -m venv .venv && .venv/bin/pip install -r modelos/herramientas/requirements.txt
.venv/bin/python modelos/herramientas/minerales.py --ronda 1          # minerales 1–10 (y su hoja)
.venv/bin/python modelos/herramientas/minerales.py --solo pirita       # uno o varios, separados por comas
.venv/bin/python modelos/herramientas/minerales.py --ronda 1 --rapido  # texturas y renders pequeños, para probar
.venv/bin/python modelos/herramientas/minerales.py --catalogo          # junta los JSON en catalogo.json
```

Unos 30–60 s por mineral con 4 núcleos (`MIN_HILOS=2` limita los hilos para lanzar dos rondas a la vez).

| Script | Para qué |
| --- | --- |
| `minerales_datos.py` | **Los 100 minerales**: rareza, valor, forma, tamaño, pinturas PBR y montaje en Studio. Todo lo ajustable |
| `minerales_formas.py` | Biblioteca de formas en bmesh (roca, canto, columnas, láminas, cristales, geoda...) y las piezas únicas (singularidad, semilla cósmica, fragmento de dios...) |
| `minerales_pintura.py` | Relieve de la malla alta (grietas, poros, estratos, surcos) y pintura por vértice (color, rugosidad, metal, emisión) |
| `minerales.py` | La cadena: alta → baja → atlas → horneado → turnaround → FBX → JSON |

Cómo se hace cada mineral: las piezas se remallan por voxel (ALTA, cientos de miles de triángulos), se les da
relieve y se pintan por vértice. La malla de juego (BAJA) es la forma limpia (cristales de caras planas) o la ALTA
simplificada (rocas). Todas las piezas se despliegan juntas en un atlas y se hornea ALTA → BAJA por grupos, para
que un cristal no recoja el color de la roca que tiene detrás.

Comprobado aquí: los 100 FBX se reimportan con su tamaño en studs (1 unidad = 1 stud), con todas las partes y con
UV, y ninguno pasa de 2.900 triángulos. 40 minerales brillan y llevan mapa de emisión.

**Lo que hay que comprobar en Studio** (esta sesión no tiene Studio): el tamaño al importar, que las texturas
del atlas casan con las partes y cómo se ven el Glass y el Neon con la luz del planeta.
