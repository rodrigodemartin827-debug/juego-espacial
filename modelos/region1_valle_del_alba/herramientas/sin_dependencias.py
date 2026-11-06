"""
Permite importar kit.py (y malla.py, atlas.py) con el Python de Blender, que trae numpy pero no PIL ni scipy.

  * PIL solo se usa para GUARDAR el atlas pintado (atlas.py).
  * scipy solo se usa para las copas de los árboles (ConvexHull en malla.py).

Las herramientas que solo rehacen paredes, tejados y otras piezas de caras planas (revisar_caras.py,
rehacer_piezas.py) importan este módulo antes que kit.py: si falta PIL o scipy, se ponen en su lugar módulos que
avisan con un error claro si alguien intenta usarlos. Si están instalados, no se toca nada.
"""

import sys
import types


def _falta(nombre):
    def usar(*_a, **_k):
        raise RuntimeError(f"{nombre} no está instalado en este Python: esta herramienta no puede usarlo")

    return usar


try:
    import PIL  # noqa: F401
except ImportError:
    pil = types.ModuleType("PIL")
    imagen = types.ModuleType("PIL.Image")
    imagen.fromarray = _falta("PIL")
    imagen.open = _falta("PIL")
    pil.Image = imagen
    sys.modules["PIL"] = pil
    sys.modules["PIL.Image"] = imagen

try:
    import scipy.spatial  # noqa: F401
except ImportError:
    scipy = types.ModuleType("scipy")
    espacial = types.ModuleType("scipy.spatial")
    espacial.ConvexHull = _falta("scipy (ConvexHull)")
    scipy.spatial = espacial
    sys.modules["scipy"] = scipy
    sys.modules["scipy.spatial"] = espacial
