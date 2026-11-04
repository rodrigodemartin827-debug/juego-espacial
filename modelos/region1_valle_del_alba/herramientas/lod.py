"""
Niveles de detalle (LOD) de la escena en Blender, para una posición de cámara. Hace lo mismo que hará el script de
Roblox (ver exportar.py y roblox/lod_region.luau), así que los renders enseñan lo que se verá en el juego.

Reglas (distancias en diseno.LOD):
  * Edificios, mobiliario, vegetación suelta, campos: DETALLADO hasta «detalle», SIMPLE hasta «simple», oculto más
    allá. La distancia se mide desde la cámara al borde de la esfera envolvente del objeto.
  * Aurora: si la cámara está a más de LOD["silueta_aurora"] del centro, todos sus edificios se cambian por la
    silueta (una malla). Si está más cerca, la silueta se oculta.
  * Terreno: cada trozo, detallado si la cámara está a menos de LOD["terreno"]["detalle"] de su borde; si no, simple.
  * Horizonte: lo que queda entero por debajo del horizonte del planeta no se dibuja (con radio 2400 la curvatura
    tapa muchísimo: desde el suelo el horizonte está a ~155 studs). Prueba: un objeto de centro C y radio r es
    visible desde la cámara P si el ángulo entre ellos es menor que acos(Rh/|P|) + acos(Rh/(|C|+r)), con Rh el
    radio del planeta menos un margen.
  * Las nubes de vegetación (Geometry Nodes) cambian el índice de cada punto (detallada / simple) o lo marcan como
    oculto.
"""

import math

import bpy
import numpy as np

import diseno as D
import geo

R = geo.RADIO


def _angulo(a, b):
    na, nb = np.linalg.norm(a, axis=-1), np.linalg.norm(b, axis=-1)
    c = np.sum(a * b, axis=-1) / (na * nb)
    return np.arccos(np.clip(c, -1.0, 1.0))


def sobre_horizonte(cam, centros, radios):
    """True para los objetos (centros (n,3), radios (n,)) que no quedan enteros bajo el horizonte."""
    Rh = R - D.LOD["horizonte_margen"]
    rc = np.linalg.norm(cam)
    if rc <= Rh:
        return np.ones(len(centros), bool)
    ro = np.linalg.norm(centros, axis=-1) + radios
    a_cam = math.acos(Rh / rc)
    a_obj = np.arccos(np.clip(Rh / np.maximum(ro, Rh), -1, 1))
    return _angulo(cam[None, :], centros) <= a_cam + a_obj


def _centro_mundo(ob):
    """El centro guardado está en coordenadas del planeta sin girar; el planeta cuelga de Pivote_Planeta."""
    c = np.array(ob["centro"], float)
    piv = bpy.data.objects.get("Pivote_Planeta")
    if piv is not None:
        m = np.array(piv.matrix_world)
        c = m[:3, :3] @ c + m[:3, 3]
    return c


def nivel(dist, cfg):
    if dist <= cfg["detalle"]:
        return "detalle"
    if dist <= cfg["simple"]:
        return "simple"
    return "oculto"


def _poner_nivel(ob, niv):
    """Cambia un objeto (o los hijos de un grupo) a su malla detallada o simple, u oculta."""
    hijos = [ob] if ob.type == "MESH" else list(ob.children)
    ob.hide_render = niv == "oculto"
    for h in hijos:
        if "pieza" not in h:
            continue
        if niv == "oculto":
            h.hide_render = True
            continue
        nombre = "K_" + h["pieza"] + ("__lejos" if niv == "simple" else "")
        me = bpy.data.meshes.get(nombre)
        if me is None and niv == "simple":
            # sin versión simple propia: la misma malla, salvo las piezas que de lejos no se pintan
            if h.get("sin_lejos"):
                h.hide_render = True
                continue
            me = bpy.data.meshes.get("K_" + h["pieza"])
        h.data = me
        h.hide_render = False


def aplicar(cam, informe=False):
    cam = np.asarray(cam, float)
    piv = bpy.data.objects.get("Pivote_Planeta")
    # todo se calcula en coordenadas del planeta sin girar
    if piv is not None:
        m = np.array(piv.matrix_world)
        cam_p = m[:3, :3].T @ (cam - m[:3, 3])
    else:
        cam_p = cam
    L = D.LOD
    cuenta = {}
    obs = [o for o in bpy.data.objects if "lod" in o.keys() and o.parent in (None, piv)]
    centros = np.array([o["centro"] for o in obs if o["lod"] != "nube"], float)
    radios = np.array([o["radio"] for o in obs if o["lod"] != "nube"], float)
    visibles = sobre_horizonte(cam_p, centros, radios) if len(centros) else []
    s_aur = geo.Sitio(D.SITIOS["Aurora"]["x"], D.SITIOS["Aurora"]["y"])
    c_aur = s_aur.centro * (R + 20)
    silueta = np.linalg.norm(cam_p - c_aur) > L["silueta_aurora"]
    k = 0
    for o in obs:
        tipo = o["lod"]
        if tipo == "nube":
            continue
        c = np.array(o["centro"], float)
        dist = max(np.linalg.norm(cam_p - c) - o["radio"], 0.0)
        vis = bool(visibles[k])
        k += 1
        if tipo == "terreno":
            quiero = "detalle" if dist <= L["terreno"]["detalle"] else "lejos"
            o.hide_render = (o["nivel"] != quiero) or not vis
        elif tipo == "silueta":
            o.hide_render = not (silueta and vis)
        else:
            cfg = L["vegetacion" if tipo in ("vegetacion", "campos") else tipo]
            niv = nivel(dist, cfg) if vis else "oculto"
            if o.get("sitio") == "Aurora" and tipo == "edificios" and silueta:
                niv = "oculto"
            if tipo == "campos" and niv == "simple":
                niv = "oculto"  # de lejos los campos son solo la textura del terreno
            _poner_nivel(o, niv)
        cuenta[(tipo, "oculto" if o.hide_render else "visible")] = cuenta.get(
            (tipo, "oculto" if o.hide_render else "visible"), 0) + 1
    # nubes de vegetación
    from region import NV

    for o in [o for o in obs if o["lod"] == "nube"]:
        me = o.data
        n = len(me.vertices)
        co = np.zeros(n * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        base = np.zeros(n, np.int32)
        me.attributes["tipo_base"].data.foreach_get("value", base)
        cfg = L["hierba" if o.get("categoria") == "hierba" else "vegetacion"]
        dist = np.linalg.norm(co - cam_p[None, :], axis=1)
        vis = sobre_horizonte(cam_p, co, np.full(n, 30.0))
        lejos = dist > cfg["detalle"]
        oculto = (dist > cfg["simple"]) | ~vis
        tipo = base + NV * lejos
        me.attributes["tipo"].data.foreach_set("value", tipo.astype(np.int32))
        me.attributes["oculto"].data.foreach_set("value", oculto)
        me.update()
        cuenta[("nube " + o.name, "detalle")] = int((~lejos & ~oculto).sum())
        cuenta[("nube " + o.name, "simple")] = int((lejos & ~oculto).sum())
    if informe:
        for kk, v in sorted(cuenta.items()):
            print("   ", kk, v)
    return cuenta
