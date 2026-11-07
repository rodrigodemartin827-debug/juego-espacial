"""
Mallas de los efectos de las pistolas de portales: el portal, el proyectil y el fogonazo de la boca.

  * CHATARRA (verde, inestable): anillo roto en tramos que no casan, borde de llamas desiguales, remolino con ruido,
    proyectil grumoso con aletas y fogonazo de chispazos irregulares.
  * VIP (morado y cian, perfecto): anillo y aro interior exactos, marcas ordenadas, remolino de espiral limpia,
    proyectil con aro y fogonazo simétrico.

Todo está en STUDS (como las pistolas; en Studio: Scale Unit = Stud), con grosor real (ni un plano de una sola cara),
normales hacia fuera y los mismos ejes: el portal es vertical y mira hacia -Y de Blender (= -Z de Roblox, «delante»);
el fogonazo y el proyectil apuntan a -Y. El portal mide 4,4 x 6,2 studs (un R6 mide 2 x 5): pasa de sobra.

Uso:  python modelos/herramientas/portal_vfx.py --salida modelos/pistola_portales/vfx
Escribe <salida>/chatarra/{Portal_Chatarra,Disparo_Chatarra}.fbx|json y lo mismo en vip/. Las texturas las hace
texturas_vfx.py (<salida>/texturas/). No lleva texturas incrustadas: las mallas tienen UV y en Studio se les pone la
textura (o solo Material Neon y color: ver vfx_portal.md).
"""

import argparse
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import comun as c  # noqa: E402
import pistola_portales as pp  # noqa: E402  (pone c.ESTUDIO = 1: todo en studs)
from pistola_portales import Pieza, mat_neon  # noqa: E402

# --------------------------------------------------------------------------------------------------------------
# Datos ajustables
# --------------------------------------------------------------------------------------------------------------

# Semiejes del portal (studs): el anillo llega a 2,2 x 3,1; el remolino llena el hueco.
SEMI_X, SEMI_Z = 2.2, 3.1
RADIO_REMOLINO = 2.05  # el remolino es un círculo que gira dentro del hueco
COLORES = {
    "Chatarra": {"anillo": "#7DFF3A", "borde": "#B6FF4A", "remolino": "#7DFF3A", "onda": "#B6FF4A",
                 "proyectil": "#7DFF3A", "fogonazo": "#C8FF8A"},
    "VIP": {"anillo": "#A64BFF", "interior": "#3FF0FF", "marcas": "#3FF0FF", "remolino": "#FFFFFF",
            "onda": "#3FF0FF", "nucleo": "#C46BFF", "aro": "#3FF0FF", "fogonazo": "#E8FBFF"},
}
SEMILLA = 11


# --------------------------------------------------------------------------------------------------------------
# Constructores con UV
# --------------------------------------------------------------------------------------------------------------


def _objeto(nombre, bm, material):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    malla = bpy.data.meshes.new(nombre)
    bm.to_mesh(malla)
    bm.free()
    ob = bpy.data.objects.new(nombre, malla)
    bpy.context.scene.collection.objects.link(ob)
    malla.materials.append(material() if callable(material) else material)
    for p in malla.polygons:
        p.use_smooth = True
    return ob


def tubo_elipse(nombre, material, a, b, radio, n, m, arco=(0.0, math.tau), radio_fn=None, desp_fn=None, rep=8):
    """
    Aro de sección circular (`m` lados) a lo largo de una elipse de semiejes a (X) y b (Z) en el plano XZ.
    `arco`: ángulos de inicio y fin (si no es la vuelta entera, queda cerrado con tapas). `radio_fn(theta)` varía el
    grosor y `desp_fn(theta)` desplaza el centro (para el aro irregular). UV: u a lo largo (`rep` repeticiones), v alrededor.
    """
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    t0, t1 = arco
    completo = abs((t1 - t0) - math.tau) < 1e-6
    pasos = n if completo else n + 1
    vs = []
    for i in range(pasos):
        th = t0 + (t1 - t0) * i / n
        cth, sth = math.cos(th), math.sin(th)
        centro = Vector((a * cth, 0, b * sth))
        if desp_fn:
            centro += Vector(desp_fn(th))
        normal = Vector((cth / a, 0, sth / b)).normalized()  # hacia fuera, en el plano
        r = radio * (radio_fn(th) if radio_fn else 1.0)
        vs.append([bm.verts.new(centro + (normal * math.cos(2 * math.pi * j / m) +
                                          Vector((0, 1, 0)) * math.sin(2 * math.pi * j / m)) * r) for j in range(m)])
    tramos = n if completo else n
    for i in range(tramos):
        i2 = (i + 1) % pasos if completo else i + 1
        for j in range(m):
            j2 = (j + 1) % m
            f = bm.faces.new((vs[i][j], vs[i][j2], vs[i2][j2], vs[i2][j]))
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
                lp[uv].uv = (ii / n * rep, jj / m)
    if not completo:
        bm.faces.new(list(reversed(vs[0])))
        bm.faces.new(vs[-1])
    return _objeto(nombre, bm, material)


def disco_elipse(nombre, material, a, b, grosor, n, ruido=0.0, semilla=1):
    """
    Disco elíptico con grosor (dos caras y canto): el remolino. UV plano (u = x, v = z) en la cara de delante; en la de
    atrás se refleja u para que la textura se lea bien desde los dos lados. `ruido` (0..1) rompe el borde (chatarra).
    """
    rng = random.Random(semilla)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    radios = [1 - ruido * 0.10 * rng.random() for _ in range(n)]
    delante, atras = [], []
    for i in range(n):
        th = math.tau * i / n
        x, z = a * radios[i] * math.cos(th), b * radios[i] * math.sin(th)
        delante.append(bm.verts.new((x, -grosor / 2, z)))
        atras.append(bm.verts.new((x, grosor / 2, z)))
    cd = bm.verts.new((0, -grosor / 2, 0))
    ca = bm.verts.new((0, grosor / 2, 0))

    def uv_de(v, espejo=False):
        u = (v.co.x / a + 1) / 2
        return (1 - u if espejo else u, (v.co.z / b + 1) / 2)

    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((cd, delante[j], delante[i]))  # delante: mira a -Y
        for lp in f.loops:
            lp[uv].uv = uv_de(lp.vert)
        f = bm.faces.new((ca, atras[i], atras[j]))  # detrás: mira a +Y
        for lp in f.loops:
            lp[uv].uv = uv_de(lp.vert, True)
        f = bm.faces.new((delante[i], delante[j], atras[j], atras[i]))
        for lp in f.loops:
            lp[uv].uv = (0.5, 0.5)
    return _objeto(nombre, bm, material)


def anillo_plano(nombre, material, a, b, ancho, grosor, n):
    """Corona elíptica plana con grosor (la onda expansiva): cabe entre los semiejes a-ancho y a (b-ancho y b)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    ext_d, ext_a, int_d, int_a = [], [], [], []
    k = (b - ancho) / b
    for i in range(n):
        th = math.tau * i / n
        co, si = math.cos(th), math.sin(th)
        for lista, y, f in ((ext_d, -grosor / 2, 1.0), (ext_a, grosor / 2, 1.0), (int_d, -grosor / 2, k),
                            (int_a, grosor / 2, k)):
            lista.append(bm.verts.new((a * f * co, y, b * f * si)))
    for i in range(n):
        j = (i + 1) % n
        for cuad, uvs in (((ext_d[i], ext_d[j], int_d[j], int_d[i]), None),  # cara de delante
                          ((ext_a[i], int_a[i], int_a[j], ext_a[j]), None),  # cara de atrás
                          ((ext_d[i], ext_a[i], ext_a[j], ext_d[j]), None),  # canto exterior
                          ((int_d[i], int_d[j], int_a[j], int_a[i]), None)):  # canto interior
            f = bm.faces.new(cuad)
            for lp in f.loops:
                lp[uv].uv = ((lp.vert.co.x / a + 1) / 2, (lp.vert.co.z / b + 1) / 2)
    return _objeto(nombre, bm, material)


def aleta(bm, base, direccion, largo, ancho, grosor):
    """Hoja de llama: pirámide aplastada con grosor, en el plano XZ (`direccion` en ese plano), base en `base`."""
    d = Vector(direccion).normalized()
    t = Vector((0, 1, 0)).cross(d).normalized()
    y = Vector((0, 1, 0))
    p = Vector(base)
    b = [p - t * ancho / 2 - y * grosor / 2, p + t * ancho / 2 - y * grosor / 2,
         p + t * ancho / 2 + y * grosor / 2, p - t * ancho / 2 + y * grosor / 2]
    punta = p + d * largo
    vb = [bm.verts.new(q) for q in b]
    vp = bm.verts.new(punta)
    bm.faces.new(list(reversed(vb)))
    for i in range(4):
        bm.faces.new((vb[i], vb[(i + 1) % 4], vp))


# --------------------------------------------------------------------------------------------------------------
# CHATARRA
# --------------------------------------------------------------------------------------------------------------


def portal_chatarra():
    random.seed(SEMILLA)
    col = COLORES["Chatarra"]
    neon = mat_neon("pch_anillo", col["anillo"])
    objs = {}
    # Anillo: seis tramos que no encajan del todo (distinto grosor, desplazados), con huecos entre ellos
    fases = [random.uniform(0, math.tau) for _ in range(3)]
    tramos = []
    cortes = [0.0, 0.9, 2.2, 3.05, 4.1, 5.0, math.tau]
    for k in range(6):
        t0, t1 = cortes[k] + 0.07, cortes[k + 1] - 0.07
        grosor = random.uniform(0.7, 1.15)
        dx, dz = random.uniform(-0.09, 0.09), random.uniform(-0.09, 0.09)

        def rf(th, g=grosor, f=fases):
            return g * (1 + 0.28 * math.sin(3 * th + f[0]) + 0.12 * math.sin(7 * th + f[1]))

        def df(th, dx=dx, dz=dz):
            return (dx, 0, dz)

        tramos.append(tubo_elipse(f"_tramo{k}", neon, SEMI_X, SEMI_Z, 0.17, 10, 8, (t0, t1), rf, df, rep=2))
    # unir los tramos en una sola malla «PortalCh_Anillo»
    bpy.ops.object.select_all(action="DESELECT")
    for o in tramos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = tramos[0]
    bpy.ops.object.join()
    anillo = bpy.context.active_object
    anillo.name = "PortalCh_Anillo"
    anillo.data.name = "PortalCh_Anillo"
    objs["PortalCh_Anillo"] = anillo

    # Borde de llamas: hojas de distinto largo y algo torcidas alrededor del anillo
    bm = bmesh.new()
    n = 30
    for i in range(n):
        th = math.tau * (i + random.uniform(-0.3, 0.3)) / n
        base = Vector((SEMI_X * math.cos(th), 0, SEMI_Z * math.sin(th)))
        nrm = Vector((math.cos(th) / SEMI_X, 0, math.sin(th) / SEMI_Z)).normalized()
        base = base + nrm * 0.16
        giro = random.uniform(-0.55, 0.55)
        d = Matrix.Rotation(giro, 3, "Y") @ nrm
        aleta(bm, base, d, random.uniform(0.28, 0.85) * (1.35 if i % 7 == 0 else 1.0), random.uniform(0.16, 0.30), 0.05)
    objs["PortalCh_Borde"] = _objeto("PortalCh_Borde", bm, mat_neon("pch_borde", col["borde"]))

    # Remolino
    mr = c.material("pch_remolino", c.srgb(col["remolino"]), rugosidad=0.5, emision=c.srgb(col["remolino"]),
                    fuerza_emision=1.0)
    # El remolino es un CÍRCULO (así gira rígido dentro del anillo elíptico) y el Fondo, la elipse fija que lo rodea
    objs["PortalCh_Fondo"] = disco_elipse("PortalCh_Fondo", mr, SEMI_X - 0.12, SEMI_Z - 0.12, 0.02, 40, 0.8, 6)
    objs["PortalCh_Remolino"] = disco_elipse("PortalCh_Remolino", mr, RADIO_REMOLINO, RADIO_REMOLINO, 0.06, 40, 0.8, 5)
    # Onda expansiva (para la apertura): corona plana que se agranda
    objs["PortalCh_Onda"] = anillo_plano("PortalCh_Onda", mat_neon("pch_onda", col["onda"]), SEMI_X, SEMI_Z, 0.22,
                                         0.05, 40)
    return objs


def disparo_chatarra():
    random.seed(SEMILLA + 1)
    col = COLORES["Chatarra"]
    objs = {}
    # Proyectil: bola grumosa de ~0,6 studs con tres aletas torcidas atrás (que miran a +Y: va hacia -Y)
    p = Pieza("Proyectil_Chatarra", {"n": mat_neon("pch_proy", col["proyectil"])})
    p.esfera((0, 0, 0), 0.26, "n", sub=2, escala=(1, 1.15, 1))
    for v in p.bm.verts:
        v.co += Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))) * 0.05
    for k in range(3):
        a = k * math.tau / 3 + 0.4
        d = Vector((math.cos(a), 0.0, math.sin(a))) * 0.5 + Vector((0, 1.1, 0))
        p.tubo([Vector((0, 0.18, 0)) + Vector((math.cos(a), 0, math.sin(a))) * 0.1,
                Vector((0, 0.18, 0)) + d * 0.5, Vector((0, 0.18, 0)) + d * 0.95], 0.06, "n", lados=4,
               radios=[0.06, 0.045, 0.012])
    objs["Proyectil_Chatarra"] = p.objeto()
    # Fogonazo: chispazos de largo desigual abiertos hacia -Y, más cuatro cortos hacia los lados
    f = Pieza("Fogonazo_Chatarra", {"n": mat_neon("pch_fogo", col["fogonazo"])})
    for k in range(9):
        a = random.uniform(0, math.tau)
        ap = random.uniform(0.05, 0.62)  # apertura respecto a -Y
        d = Vector((math.sin(ap) * math.cos(a), -math.cos(ap), math.sin(ap) * math.sin(a)))
        largo = random.uniform(0.55, 1.35)
        f.perfil((0, 0, 0), d, [(0, 0.1), (largo * 0.35, 0.075), (largo, 0.0)], "n", lados=5)
    for k in range(4):
        a = k * math.tau / 4 + random.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), -0.2, math.sin(a)))
        f.perfil((0, 0.0, 0), d, [(0, 0.07), (0.3, 0.0)], "n", lados=4)
    f.esfera((0, -0.08, 0), 0.16, "n", sub=1)
    objs["Fogonazo_Chatarra"] = f.objeto()
    return objs


# --------------------------------------------------------------------------------------------------------------
# VIP
# --------------------------------------------------------------------------------------------------------------


def portal_vip():
    col = COLORES["VIP"]
    objs = {}
    objs["PortalVIP_Anillo"] = tubo_elipse("PortalVIP_Anillo", mat_neon("pvip_anillo", col["anillo"]), SEMI_X,
                                           SEMI_Z, 0.15, 56, 10, rep=12)
    k = (SEMI_Z - 0.3) / SEMI_Z
    objs["PortalVIP_Interior"] = tubo_elipse("PortalVIP_Interior", mat_neon("pvip_int", col["interior"]),
                                             SEMI_X * k, SEMI_Z * k, 0.05, 48, 6, rep=12)
    # Marcas: 16 pletinas finas, ordenadas, alrededor del aro (por fuera)
    p = Pieza("PortalVIP_Marcas", {"n": mat_neon("pvip_marcas", col["marcas"])})
    for i in range(16):
        th = math.tau * i / 16 + math.pi / 16
        pos = Vector((SEMI_X * math.cos(th), 0, SEMI_Z * math.sin(th)))
        nrm = Vector((math.cos(th) / SEMI_X, 0, math.sin(th) / SEMI_Z)).normalized()
        pos = pos + nrm * 0.42
        giro = Matrix.Rotation(-math.atan2(nrm.x, nrm.z), 3, "Y")
        p.caja(pos, (0.05, 0.05, 0.34 if i % 2 == 0 else 0.2), "n", giro=giro)
    objs["PortalVIP_Marcas"] = p.objeto()
    mr = c.material("pvip_remolino", c.srgb("#FFFFFF"), rugosidad=0.5, emision=c.srgb("#FFFFFF"), fuerza_emision=1.0)
    objs["PortalVIP_Fondo"] = disco_elipse("PortalVIP_Fondo", mr, SEMI_X - 0.1, SEMI_Z - 0.1, 0.02, 56)
    objs["PortalVIP_Remolino"] = disco_elipse("PortalVIP_Remolino", mr, RADIO_REMOLINO, RADIO_REMOLINO, 0.06, 56)
    objs["PortalVIP_Onda"] = anillo_plano("PortalVIP_Onda", mat_neon("pvip_onda", col["onda"]), SEMI_X, SEMI_Z,
                                          0.12, 0.04, 56)
    return objs


def disparo_vip():
    col = COLORES["VIP"]
    objs = {}
    n = Pieza("Proyectil_VIP_Nucleo", {"n": mat_neon("pvip_proy", col["nucleo"])})
    n.esfera((0, 0, 0), 0.2, "n", sub=2, escala=(1, 1.4, 1))
    objs["Proyectil_VIP_Nucleo"] = n.objeto()
    a = Pieza("Proyectil_VIP_Aro", {"n": mat_neon("pvip_aro", col["aro"])})
    a.toro((0, 0, 0), "Y", 0.3, 0.025, "n", n_mayor=20, n_menor=6)
    objs["Proyectil_VIP_Aro"] = a.objeto()
    f = Pieza("Fogonazo_VIP", {"n": mat_neon("pvip_fogo", col["fogonazo"])})
    for k in range(8):  # estrella simétrica de 8 puntas abierta hacia delante
        a_ = k * math.tau / 8
        d = Vector((math.sin(0.42) * math.cos(a_), -math.cos(0.42), math.sin(0.42) * math.sin(a_)))
        f.perfil((0, 0, 0), d, [(0, 0.06), (0.9, 0.0)], "n", lados=6)
    f.perfil((0, 0, 0), (0, -1, 0), [(0, 0.1), (0.55, 0.075), (2.0, 0.0)], "n", lados=8)  # chorro central
    f.toro((0, -0.25, 0), "Y", 0.3, 0.02, "n", n_mayor=24, n_menor=4)  # aro de luz
    objs["Fogonazo_VIP"] = f.objeto()
    return objs


# --------------------------------------------------------------------------------------------------------------
# Salida
# --------------------------------------------------------------------------------------------------------------


def exportar(ruta, objetos, vacios):
    bpy.ops.object.select_all(action="DESELECT")
    for o in list(objetos) + list(vacios):
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, object_types={"MESH", "EMPTY"}, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", bake_space_transform=True, axis_forward="-Z", axis_up="Y",
        use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=False, add_leaf_bones=False, bake_anim=False,
        embed_textures=False, path_mode="AUTO")
    print("[ok] FBX:", ruta)


def guardar(carpeta, nombre, objs, vacios_pos, usos):
    """Exporta `objs` a <nombre>.fbx y escribe <nombre>.json con centros, tamaños, comprobaciones y uso en Studio."""
    vacios = []
    for n, p in vacios_pos.items():
        e = bpy.data.objects.new(n, None)
        e.empty_display_type = "ARROWS"
        e.location = p
        bpy.context.scene.collection.objects.link(e)
        vacios.append(e)
    exportar(os.path.join(carpeta, f"{nombre}.fbx"), list(objs.values()), vacios)
    datos = {"piezas": {}, "anclajes": {e.name: pp.a_roblox(e.location) for e in vacios}}
    for n, o in objs.items():
        mn, mx = c.caja_limite([o])
        datos["piezas"][n] = {"centro": pp.a_roblox((mn + mx) / 2),
                              "tamano": [round(v, 3) for v in (mx.x - mn.x, mx.z - mn.z, mx.y - mn.y)],
                              **pp.revisar(o), **usos.get(n, {})}
    datos["triangulos_total"] = sum(p["triangulos"] for p in datos["piezas"].values())
    with open(os.path.join(carpeta, f"{nombre}.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    print(f"[info] {nombre}: {datos['triangulos_total']} triángulos")
    for n, p in datos["piezas"].items():
        print(f"   {n}: {p['triangulos']} tri, abiertas {p['aristas_abiertas']}, volumen {p['volumen']}, "
              f"tamaño {p['tamano']}")
    return datos


USOS = {
    "PortalCh_Anillo": {"material": "Neon", "color": COLORES["Chatarra"]["anillo"], "textura": "anillo_banda_chatarra.png"},
    "PortalCh_Borde": {"material": "Neon", "color": COLORES["Chatarra"]["borde"]},
    "PortalCh_Remolino": {"material": "Neon (o SurfaceAppearance)", "color": "#FFFFFF", "textura": "portal_remolino_chatarra.png"},
    "PortalCh_Fondo": {"material": "Neon (o SurfaceAppearance)", "color": "#FFFFFF", "textura": "portal_fondo_chatarra.png"},
    "PortalCh_Onda": {"material": "Neon", "color": COLORES["Chatarra"]["onda"]},
    "Proyectil_Chatarra": {"material": "Neon", "color": COLORES["Chatarra"]["proyectil"]},
    "Fogonazo_Chatarra": {"material": "Neon", "color": COLORES["Chatarra"]["fogonazo"]},
    "PortalVIP_Anillo": {"material": "Neon", "color": COLORES["VIP"]["anillo"], "textura": "anillo_banda_vip.png"},
    "PortalVIP_Interior": {"material": "Neon", "color": COLORES["VIP"]["interior"]},
    "PortalVIP_Marcas": {"material": "Neon", "color": COLORES["VIP"]["marcas"]},
    "PortalVIP_Remolino": {"material": "Neon (o SurfaceAppearance)", "color": "#FFFFFF", "textura": "portal_remolino_vip.png"},
    "PortalVIP_Fondo": {"material": "Neon (o SurfaceAppearance)", "color": "#FFFFFF", "textura": "portal_fondo_vip.png"},
    "PortalVIP_Onda": {"material": "Neon", "color": COLORES["VIP"]["onda"]},
    "Proyectil_VIP_Nucleo": {"material": "Neon", "color": COLORES["VIP"]["nucleo"]},
    "Proyectil_VIP_Aro": {"material": "Neon", "color": COLORES["VIP"]["aro"]},
    "Fogonazo_VIP": {"material": "Neon", "color": COLORES["VIP"]["fogonazo"]},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    sal = os.path.abspath(a.salida)
    resumen = {}
    for nombre, f_portal, f_disparo, carpeta in (("Chatarra", portal_chatarra, disparo_chatarra, "chatarra"),
                                                  ("VIP", portal_vip, disparo_vip, "vip")):
        dest = os.path.join(sal, carpeta)
        os.makedirs(dest, exist_ok=True)
        c.escena_vacia()
        # Puntos para los emisores: el centro (destello, onda, luz) y ocho puntos en el borde (chispas) cada 45 grados
        puntos = {"Centro": Vector((0, 0, 0))}
        for k in range(8):
            th = math.tau * (k + 0.5) / 8
            puntos[f"Borde_{k + 1}"] = Vector((SEMI_X * math.cos(th), 0, SEMI_Z * math.sin(th)))
        resumen[f"Portal_{nombre}"] = guardar(dest, f"Portal_{nombre}", f_portal(), puntos, USOS)
        c.escena_vacia()
        resumen[f"Disparo_{nombre}"] = guardar(dest, f"Disparo_{nombre}", f_disparo(), {"Origen": Vector((0, 0, 0))}, USOS)


if __name__ == "__main__":
    main()
