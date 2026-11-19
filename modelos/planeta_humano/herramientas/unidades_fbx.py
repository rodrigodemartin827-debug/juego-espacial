"""Corrige la unidad declarada en los FBX ya generados: de «1 unidad = 1 m» a «1 unidad = 0,28 m» (1 stud).

Solo cambia dos números de la cabecera (UnitScaleFactor y OriginalUnitScaleFactor); la geometría no se toca.
Después reimporta cada FBX y comprueba piezas, triángulos y tamaño contra su JSON.

    python unidades_fbx.py
"""
import glob
import json
import os
import struct

import bpy

import ph

RAIZ = ph.RAIZ


def parchear(ruta):
    datos = bytearray(open(ruta, "rb").read())
    cambios = 0
    for clave in (b"UnitScaleFactor", b"OriginalUnitScaleFactor"):
        inicio = 0
        while True:
            i = datos.find(clave, inicio)
            if i < 0:
                break
            inicio = i + len(clave)
            if datos[i - 8:i] == b"Original" and clave == b"UnitScaleFactor":
                continue  # es la otra clave
            for pos in range(i + len(clave), i + len(clave) + 80):
                if datos[pos:pos + 1] == b"D":
                    v = struct.unpack("<d", datos[pos + 1:pos + 9])[0]
                    if abs(v - 100.0) < 1e-3:
                        datos[pos + 1:pos + 9] = struct.pack("<d", ph.METROS_POR_STUD * 100.0)
                        cambios += 1
                    break
    if cambios:
        open(ruta, "wb").write(bytes(datos))
    return cambios


def verificar(ruta, datos_json):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.scale_length = ph.METROS_POR_STUD
    bpy.ops.import_scene.fbx(filepath=ruta)
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    mn, mx = ph._caja(objs)
    d = mx - mn
    t = datos_json["tam_studs"]
    esperado = (t["ancho_x"], t["fondo_z"], t["alto_y"])
    tris = sum(ph._tris(o) for o in objs)
    ok = (len(objs) == len(datos_json["piezas"]) and tris == datos_json["triangulos"] and
          all(abs(a - b) < 0.03 for a, b in zip((d.x, d.y, d.z), esperado)))
    return ok, (round(d.x, 2), round(d.y, 2), round(d.z, 2)), tris


if __name__ == "__main__":
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "*", "*", "*.fbx"))):
        nombre = os.path.basename(ruta)[:-4]
        rjson = ruta[:-4] + ".json"
        antes = ph.unidad_fbx(ruta)
        n = parchear(ruta)
        datos = json.load(open(rjson, encoding="utf-8"))
        ok, dims, tris = verificar(ruta, datos)
        datos["escala"] = "1 unidad = 1 stud (FBX_SCALE_ALL); el FBX declara 0,28 m por unidad"
        datos["verificacion_fbx"]["unidad_fbx_m"] = ph.unidad_fbx(ruta)
        datos["verificacion_fbx"]["ok"] = datos["verificacion_fbx"]["ok"] and ok
        with open(rjson, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        print(f"{nombre:<26} unidad {antes} -> {ph.unidad_fbx(ruta)} m  ({n} cambios)  tamaño {dims}  tris {tris}  "
              f"{'OK' if ok else 'FALLO'}", flush=True)
