"""
Lector mínimo de FBX binario, para comprobar qué guarda de verdad un archivo exportado (sin fiarse de lo que
hacemos en Blender): unidades, ejes, posición del objeto, y el tamaño y la caja envolvente de los vértices.

Formato (FBX binario 7.x): cabecera de 27 bytes + versión (4 bytes); luego nodos con
  [fin (4 u 8 bytes), nº de propiedades, bytes de propiedades, largo del nombre, nombre, propiedades, hijos]
y un nodo nulo al final de cada lista. Las propiedades de tipo array pueden ir comprimidas con zlib.

Uso:
    python modelos/planeta_prueba/herramientas/leer_fbx.py archivo.fbx [...]
"""

import struct
import sys
import zlib

import numpy as np


class Nodo:
    def __init__(self, nombre, props, hijos):
        self.nombre, self.props, self.hijos = nombre, props, hijos

    def hijo(self, nombre):
        return next((h for h in self.hijos if h.nombre == nombre), None)

    def todos(self, nombre):
        return [h for h in self.hijos if h.nombre == nombre]


def _prop(b, p):
    t = chr(b[p])
    p += 1
    simples = {"Y": ("<h", 2), "C": ("<?", 1), "I": ("<i", 4), "F": ("<f", 4), "D": ("<d", 8), "L": ("<q", 8)}
    if t in simples:
        fmt, n = simples[t]
        return struct.unpack_from(fmt, b, p)[0], p + n
    if t in "fdlib":
        dt = {"f": "<f4", "d": "<f8", "l": "<i8", "i": "<i4", "b": "?"}[t]
        n, enc, comp = struct.unpack_from("<III", b, p)
        p += 12
        datos = b[p : p + comp]
        if enc == 1:
            datos = zlib.decompress(datos)
        return np.frombuffer(datos, dtype=dt, count=n), p + comp
    if t in "SR":
        n = struct.unpack_from("<I", b, p)[0]
        p += 4
        dato = bytes(b[p : p + n])
        return (dato.decode("latin-1") if t == "S" else dato), p + n
    raise ValueError(f"tipo de propiedad desconocido {t!r}")


def _nodos(b, p, fin_lista, version):
    salida = []
    ancho = 8 if version >= 7500 else 4
    while p < fin_lista:
        fmt = "<QQQ" if ancho == 8 else "<III"
        fin, n_props, _ = struct.unpack_from(fmt, b, p)
        p0 = p + 3 * ancho
        if fin == 0:
            break
        largo = b[p0]
        nombre = bytes(b[p0 + 1 : p0 + 1 + largo]).decode("latin-1")
        q = p0 + 1 + largo
        props = []
        for _ in range(n_props):
            v, q = _prop(b, q)
            props.append(v)
        hijos = _nodos(b, q, fin, version) if q < fin else []
        salida.append(Nodo(nombre, props, hijos))
        p = fin
    return salida


def leer(ruta: str) -> Nodo:
    with open(ruta, "rb") as f:
        b = f.read()
    assert b[:20] == b"Kaydara FBX Binary  ", "no es un FBX binario"
    version = struct.unpack_from("<I", b, 23)[0]
    raiz = Nodo("raiz", [], _nodos(b, 27, len(b), version))
    raiz.version = version
    return raiz


def propiedades70(nodo: Nodo) -> dict:
    p70 = nodo.hijo("Properties70")
    return {h.props[0]: h.props[4:] for h in p70.hijos if h.nombre == "P"} if p70 else {}


def resumen(ruta: str) -> dict:
    raiz = leer(ruta)
    gs = propiedades70(raiz.hijo("GlobalSettings"))
    objetos = raiz.hijo("Objects")
    geo = objetos.hijo("Geometry")
    verts = geo.hijo("Vertices").props[0].reshape(-1, 3)
    normales = geo.hijo("LayerElementNormal")
    modelo = objetos.hijo("Model")
    mp = propiedades70(modelo)
    return dict(
        version=raiz.version,
        eje_arriba=gs.get("UpAxis", [None])[0], signo_arriba=gs.get("UpAxisSign", [None])[0],
        eje_delante=gs.get("FrontAxis", [None])[0], signo_delante=gs.get("FrontAxisSign", [None])[0],
        eje_coord=gs.get("CoordAxis", [None])[0], signo_coord=gs.get("CoordAxisSign", [None])[0],
        unidad_factor=gs.get("UnitScaleFactor", [None])[0],
        original_unidad_factor=gs.get("OriginalUnitScaleFactor", [None])[0],
        nombre_modelo=modelo.props[1].split("\x00")[0],
        traslacion=tuple(mp["Lcl Translation"][-3:]) if "Lcl Translation" in mp else None,
        rotacion=tuple(mp["Lcl Rotation"][-3:]) if "Lcl Rotation" in mp else None,
        escala=tuple(mp["Lcl Scaling"][-3:]) if "Lcl Scaling" in mp else None,
        n_vertices=len(verts), vertice_min=verts.min(axis=0), vertice_max=verts.max(axis=0),
        normales=(normales.hijo("MappingInformationType").props[0], len(normales.hijo("Normals").props[0]) // 3)
        if normales else None,
        uv=len(geo.hijo("LayerElementUV").hijo("UV").props[0]) // 2 if geo.hijo("LayerElementUV") else None,
        triangulos=int(sum(1 for i in geo.hijo("PolygonVertexIndex").props[0] if i < 0)),
    )


if __name__ == "__main__":
    for ruta in sys.argv[1:]:
        print("==", ruta)
        for k, v in resumen(ruta).items():
            print(f"  {k}: {v}")
