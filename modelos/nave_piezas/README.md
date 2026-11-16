# Piezas modulares de nave (100)

Piezas para construir naves por bloques en el hangar: 20 cascos, 15 alas, 15 motores, 20 armas, 10 defensas,
10 cabinas y 10 utilidades, en 5 tiers. Todo sale de `modelos/herramientas/nave_piezas.py` (Blender sin pantalla,
`bpy`) y se puede regenerar; no hay nada hecho a mano.

| Tier | Estilo | Cómo se ve |
| --- | --- | --- |
| 1 | Básico | Chapa gris remachada, mugre en los huecos, óxido, arañazos y franjas de aviso amarillas |
| 2 | Militar | Blanco pulido y naranja, marcas de escuadrón (franjas, chevrón y número) en los cascos |
| 3 | Avanzado | Metal oscuro, juntas que brillan en cian y franjas de neón |
| 4 | Élite | Negro con molduras de oro, neón dorado y rojo, formas facetadas |
| 5 | Legendario | Escamas irisadas, venas de neón púrpura, cristal, formas orgánicas |

## Qué hay en cada carpeta

`nave_piezas/<pieza>/`:

| Archivo | Para qué |
| --- | --- |
| `<pieza>.fbx` | El modelo (ver «Importar en Studio») |
| `<pieza>.json` | Triángulos, tamaño, mallas, texturas y **puntos de acople** |
| `<pieza>_turnaround.jpg` | 6 vistas (frente, detrás, izquierda, derecha, arriba, 3/4), una con los acoples marcados y la ficha |
| `texturas/<pieza>_color.png` | Atlas 1024 × 1024: color base (con la oclusión horneada) |
| `texturas/<pieza>_normal.png` | Normales en espacio tangente (OpenGL) |
| `texturas/<pieza>_rugosidad.png`, `_metal.png` | Rugosidad y metal (escala de grises) |
| `texturas/<pieza>_emision.png` | Solo si algo de la textura brilla (juntas de neón, pantallas, venas) |

En la raíz: `catalogo.json` (índice de las 100 con los tipos de conector y la regla de encaje),
`montar_acoples.luau` (script de Studio, ver abajo) y `rondas/ronda_NN.jpg` (la vista 3/4 de las 10 piezas de cada
ronda, para revisarlas de un vistazo).

### Mallas de cada FBX

| Malla | En Studio |
| --- | --- |
| `<pieza>` | El cuerpo: `SurfaceAppearance` con `ColorMap`, `NormalMap`, `RoughnessMap` y `MetalnessMap` |
| `<pieza>_<grupo>` | Partes con el mismo atlas que se mueven aparte: `_cabeza` (torretas), `_canones` (gatling), `_canon` (retroceso), `_plato` (radar), `_anillos` y `_orbita` (motores T5), `_tobera` (VTOL), `_patas` (tren retráctil), `_extendida` / `_plegada` (ala variable) |
| `..._neon`, `..._neon2` | Material **Neon** con el `color` del JSON |
| `..._cristal` | Material **Glass**, color del JSON, Transparency 0,35 |
| `..._domo` | Material **ForceField** (escudos, campo del ala de energía y del blindaje energético) |
| `..._llama` | Neon semitransparente (llama del postquemador) |

Las **alas** son las únicas piezas con lado: el FBX trae `<pieza>_izq...` y `<pieza>_der...` (la derecha es el
reflejo). Las armas y el blindaje no lo necesitan: tienen bridas en los dos costados (ver abajo).

El mapa de emisión se genera por si se usa en una `SurfaceAppearance` con emisión; lo que más brilla (franjas,
núcleos, anillos) va siempre en las mallas `_neon`, que son lo que da el brillo en Roblox.

## Importar en Studio

Las piezas están modeladas a **1 unidad = 1 stud**, con las escalas aplicadas (*FBX All*) y la malla girada 180°
alrededor del eje vertical antes de exportar (`GIRO_IMPORTACION` en `herramientas/piezas_nave/datos.py`).

1. **File → Import 3D** y elige el `.fbx`.
2. **File Dimensions → Scale Unit: Stud** (el FBX está en studs; con *Meter* saldría 3,57 veces más grande).
3. *Anchored* desactivado (salvo para enseñarla), *Import only as model* activado.
4. Pon las texturas en la `SurfaceAppearance` del cuerpo (Asset Manager → Bulk Import) y el material de las mallas
   `_neon`, `_cristal`, `_domo` según la tabla de arriba (el JSON da el color de cada una).
5. Selecciona el modelo y pega `montar_acoples.luau` en la Command Bar: crea los `Attachment` de acople.

**Comprobar en el primer import** (aquí no hay Studio): la pieza debe medir lo que dice `tamano` en su JSON y
mirar a **-Z** (en el turnaround, la vista «Frente» es la cara que mira a -Z). Si llega girada 180°, cambia
`GIRO_IMPORTACION` a 0 y regenera; si llega a otra escala, revisa *Scale Unit*.

## Puntos de acople

Cada acople del JSON:

```json
{
  "nombre": "acople_lateral_izq",
  "malla": "casco_caza_t1",
  "posicion": [-2.04, 0.22, 0.69],
  "orientacion": [0.0, 90.0, 0.0],
  "normal": [-1.0, 0.0, 0.0],
  "arriba": [0.0, 1.0, 0.0],
  "tipo": "CASCO_LATERAL",
  "direccion": "salida",
  "brida": 1.6
}
```

- `posicion` en studs, **relativa al centro de la caja de su `malla`** (la `Position` de esa MeshPart), con los ejes
  de Studio: delante -Z, arriba +Y, derecha +X. Es la cara exterior de la brida.
- `orientacion` es la `Orientation` del `Attachment` (grados, orden de Roblox Y-X-Z): su `LookVector` es `normal`
  (hacia fuera de la pieza) y su `UpVector` es `arriba`.
- `brida`: lado (cuadrada) o diámetro (redonda) en studs. Cada tipo de conector tiene siempre la misma brida, y está
  modelada en las dos piezas: al encajar, quedan cara con cara.
- Las entradas llevan `acepta`: los tipos de salida donde pueden ir.

| Tipo | Brida | Dónde |
| --- | --- | --- |
| `CASCO_LATERAL` | □ 1,6 | Costados del casco: alas, armas, blindaje |
| `CASCO_TRASERO` | ○ 2,4 | Popa: motores |
| `CASCO_SUPERIOR` | □ 2,0 | Lomo: cabina, torretas, escudos, aletas (`acople_superior_cola`) |
| `CASCO_INFERIOR` | □ 1,2 | Panza: tren, tanques, bahía de carga |
| `CASCO_FRONTAL` | ○ 1,2 | Bajo el morro: armas pesadas (por su `acople_trasero`) |
| `ALA_PUNTA` | □ 0,9 | Bajo la punta del ala y en los hardpoints: armas, tanques, retro, VTOL |
| `ALA_MOTOR` | ○ 1,6 | Góndolas del borde de salida del ala: motores pequeños y medianos |
| `MOTOR_ESCAPE` | — | Salida de la tobera (solo visual: estela y llama) |
| `UNIVERSAL` | ○ 0,8 | Motores auxiliares, radar y contramedidas: van en cualquier conector |

**Regla de encaje** (la que debe aplicar el hangar):

- Una entrada encaja en una salida si el tipo de la salida está en `acepta` (o alguno de los dos es `UNIVERSAL`) y
  `brida(entrada) <= brida(salida)`.
- Se coloca así: `pieza.CFrame = salida.WorldCFrame * CFrame.Angles(0, math.pi, 0) * entrada.CFrame:Inverse()`
  (con un Model, `PivotTo` usando la MeshPart que tiene la entrada). Las normales quedan opuestas y los «arriba»
  coinciden, así que la pieza nunca sale rodada.

Cómo se usan los lados:

- **Alas:** `_izq` va en `acople_lateral_izq` del casco y `_der` en `acople_lateral_der`.
- **Armas y blindaje:** las armas tienen `acople_lateral_izq` (en su costado izquierdo) y `acople_lateral_der`; en el
  costado **derecho** del casco se usa la brida izquierda del arma y al revés, y el cañón sigue mirando hacia
  delante. También se cuelgan por `acople_colgar` (ALA_PUNTA) y las pesadas van en la proa por `acople_trasero`.
  El blindaje es simétrico delante/detrás: con su única entrada vale para los dos costados.
- **Motores:** se acoplan por delante (`acople_montaje`); `acople_escape` marca la salida de la tobera.

Además, algunos JSON traen `anclajes_vfx` (bocas de fuego de las armas, asientos de las cabinas, repulsores) y
notas para las mallas que se mueven (`pivote_cabeza`, `retroceso`, `posiciones`...).

## Regenerar

Requiere el mismo entorno que el resto de modelos (`modelos/herramientas/requirements.txt`, `bpy` 5.2):

```bash
.venv/bin/python modelos/herramientas/nave_piezas.py --salida modelos/nave_piezas --ronda 3        # piezas 21–30
.venv/bin/python modelos/herramientas/nave_piezas.py --salida modelos/nave_piezas --solo radar_t2   # una pieza
.venv/bin/python modelos/herramientas/nave_piezas.py --salida modelos/nave_piezas --todas
.venv/bin/python modelos/herramientas/piezas_nave/verificar.py modelos/nave_piezas                  # comprobaciones
.venv/bin/python modelos/herramientas/piezas_nave/hoja_ronda.py modelos/nave_piezas 3              # hoja de ronda
```

`--rapido` hace texturas de 256 y renders pequeños para probar cambios. A calidad completa son unos 25–35 s por
pieza con 4 núcleos.

| Archivo (`herramientas/piezas_nave/`) | Qué hace |
| --- | --- |
| `datos.py` | Colores y detalle de cada tier, conectores, giro de importación y límites de triángulos |
| `catalogo.py` | Las 100 piezas con sus parámetros, el índice y el script de Studio |
| `geo.py` | Constructor de mallas (lofts, revoluciones, alas, toros...) y bridas de acople |
| `cascos.py`, `alas.py`, `motores.py`, `armas.py`, `otras.py` | Una familia cada uno |
| `texturas.py` | Hornea posición, normal, ranura y oclusión y pinta el atlas PBR con numpy |
| `final.py` | Bisel, sombreado, mallas separadas, UV, simplificación si se pasa del límite, FBX y JSON |
| `render.py` | Turnaround y hoja |

Límites: 5.000 triángulos por pieza (por variante en las alas) y 8.000 en los cascos grandes (transporte en
adelante). Si una pieza se pasa, se simplifica el cuerpo con un colapso de aristas suave.
