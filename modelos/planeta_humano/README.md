# Planeta Humano: 105 modelos

Todos los edificios, props, vegetación y terreno de la colonia humana, generados con Blender sin pantalla (`bpy`) a
partir de los scripts de `herramientas/`. Nada está hecho a mano: cualquier modelo se puede regenerar.

Estilo: ciencia ficción limpia, paneles metálicos blancos y grises con acentos cyan `#3DF2FF`. Todo es geometría con
volumen (sólidos cerrados, con grosor): las frutas son esferas, los rótulos son letras 3D, las hojas son rombos con
grosor y la hierba son briznas piramidales. Ninguna pieza es un plano con textura.

## Qué hay en cada carpeta

`planeta_humano/<nombre>/`:

| Archivo | Para qué |
| --- | --- |
| `<nombre>.fbx` | El modelo. Una malla por pieza (ver abajo) |
| `<nombre>_color.png` | Atlas 1024×1024 de color base, con la oclusión ambiental horneada |
| `<nombre>_normal.png` | Atlas de normales (espacio tangente) con el relieve de los materiales |
| `<nombre>_roughness.png` / `_metalness.png` | Rugosidad y metal (escala de grises) |
| `<nombre>_emision.png` | Solo si el modelo tiene partes que brillan |
| `<nombre>_turnaround.png` | 6 vistas: Frente, 3/4, Lateral, 3/4 trasera, Arriba y Wireframe, con estudio de 3 luces |
| `<nombre>.json` | Triángulos, tamaño en studs, piezas con su material de Roblox, anclajes, notas y el resultado de la verificación |

`indice.json` resume los 105 (lo genera `herramientas/auditar.py`).

## Piezas de cada FBX

- `<nombre>`: el cuerpo, con `SurfaceAppearance` (color, normal, rugosidad, metal del atlas).
- `<nombre>_neon`, `_naranja_neon`, `_verde_neon`, `_blanco_luz`…: lo que brilla. En Studio, **Material = Neon** con
  el color que indica el JSON (`#3DF2FF` para el cyan humano).
- `<nombre>_cristal` / `_escaparate_cristal` / `_agua`: **Material = Glass** con la transparencia del JSON (0,45; los
  escaparates 0,8 para que se vea lo expuesto).
- Piezas móviles aparte para animarlas por código: `puerta`, `puerta_izq/der`, `porton_*`, `tapa`, `cajon_*`,
  `torreta_*`, `foco`, `radar`, `horquilla`, `ventilador`, `rodillos`, `banda`, `puente_grua`, `bandera_*`, etc.

## Medidas y ejes

- **1 unidad = 1 stud.** Exportado con *Apply Scalings: FBX All*. Al importar deja *Scale Unit* tal cual: el modelo
  llega con el tamaño de su JSON (`tamano_studs`).
- **GIRO_IMPORTACION:** antes de exportar se gira 180° alrededor de la vertical (el eje Y de Roblox), para que la
  fachada quede mirando a −Z, el delante de Roblox.
- La base de cada modelo está en Y = 0 (nada baja del suelo).
- Los `anclajes_roblox` del JSON (humo de chimeneas, chispas, centro del portal, bocas de las torretas…) están ya en
  coordenadas de Roblox, relativas al origen del modelo: sirven para colocar `Attachment` de VFX.

## Verificación

Cada FBX se reimporta en una escena vacía después de exportarlo y se comprueba: número de triángulos, nombres de las
piezas, tamaño, que no haya aristas abiertas (piezas sin grosor) y que las normales miren hacia fuera. El resultado
queda en `verificacion_fbx` del JSON. `python herramientas/auditar.py` revisa además que estén todos los archivos.

**Falta probarlos en Studio** (este trabajo se hizo en la nube, sin Studio): importarlos, montar la
`SurfaceAppearance` y hacer capturas, como pide `CLAUDE.md`, antes de darlos por buenos.

## Regenerar

Requisitos: `pip install bpy==5.2.3 pillow numpy` (Python 3.13).

```bash
cd modelos/planeta_humano/herramientas
python generar.py casa_pequena_a            # un modelo (escena limpia propia)
python generar.py --ronda 3 -j 3            # los modelos 21-30, tres procesos a la vez
python comprobar_geometria.py               # solo geometría, sin hornear: errores, tamaño y presupuesto
./reanudar.sh                               # genera los que no tengan JSON, de 6 en 6, y hace commit y push
python auditar.py                           # revisión final de los 105
```

| Script | Qué hace |
| --- | --- |
| `geometria.py` | Primitivas sólidas (caja, cilindro, torno, barrido, prisma, texto 3D, hoja, brizna, roca…) |
| `materiales.py` | Paleta PBR procedural (paneles, chapa, madera, corteza, piedra, tela, neón…) |
| `tuberia.py` | UV + atlas, horneado de los 5 mapas, turnaround, exportación FBX, JSON y verificación |
| `ronda_01.py` … `ronda_11.py` | Los 105 modelos, uno por función |

Cada modelo corre en su propio proceso con `read_factory_settings()`: un modelo = una escena limpia, sin geometría
compartida entre modelos.
