"""
Genera preview_naves.html: una página autocontenida (1280x900) con las naves humanas.

Reutiliza los FBX ya exportados: los reimporta, revive el neón (emisión cyan/rojo) y renderiza una toma
"héroe" limpia de cada nave + una comparación de escala de las 3 en fila con un maniquí R6 al lado. La sección
transversal de cada nave se toma de los renders ya hechos (render/<nave>_interior.png).

Uso: python modelos/herramientas/preview_naves.py [--rapido]
"""

import argparse
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from PIL import Image  # noqa: E402

import comun as c  # noqa: E402
import naves_humanas_comun as h  # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELOS = os.path.join(RAIZ, "modelos")

NAVES = [
    {"id": "interceptor", "archivo": "nave_interceptor", "nombre": "Interceptor", "clase": "Pequeña",
     "tam": "30 × 16 × 6 studs", "trip": "2-3 tripulantes", "largo": 30.0,
     "estaciones": ["Timón", "Ancla lateral", "2 cañones", "2 motores"],
     "desc": "Caza de reconocimiento rápido. Cubierta abierta tipo lancha espacial. Ágil pero frágil."},
    {"id": "fragata", "archivo": "nave_fragata", "nombre": "Fragata Estelar", "clase": "Mediana",
     "tam": "50 × 22 × 13 studs", "trip": "4-6 tripulantes", "largo": 50.0,
     "estaciones": ["Timón elevado", "Ancla", "4 cañones", "3 motores", "Mesa de navegación",
                    "2 cofres", "Reparación", "2 escaleras"],
     "desc": "Nave de combate versátil de dos niveles. Ariete angular en la proa y 3 motores en triángulo."},
    {"id": "acorazado", "archivo": "nave_acorazado", "nombre": "Acorazado Titán", "clase": "Grande",
     "tam": "80 × 32 × 26 studs", "trip": "6-10 tripulantes", "largo": 80.0,
     "estaciones": ["Timón (torre)", "Ancla doble", "4 cañones", "Cañón frontal", "Cañón trasero",
                    "4 motores", "Mesa de navegación", "4 cofres", "2 reparaciones", "2 escaleras + rampa"],
     "desc": "La nave insignia. Tres niveles, torre de mando, cañón frontal grande. Lenta pero devastadora."},
]


def revivir_neon(objs):
    """A cada pieza de neón importada le vuelve a poner emisión fuerte (rojo si es Neon_04 del acorazado)."""
    for o in objs:
        if o.type != "MESH" or "Neon" not in o.name:
            continue
        rojo = o.name.endswith("Neon_04") and "corazado" in o.name
        col = c.srgb(h.ROJO if rojo else h.CYAN)
        for ms in o.material_slots:
            m = ms.material
            if not m or not m.use_nodes:
                continue
            b = m.node_tree.nodes.get("Principled BSDF")
            if b:
                b.inputs["Emission Color"].default_value = (*col, 1)
                b.inputs["Emission Strength"].default_value = 6.0


def cargar_fbx(ruta, desplazar=Vector((0, 0, 0))):
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=ruta)
    nuevos = [o for o in bpy.data.objects if o not in antes]
    for o in nuevos:
        o.location = o.location + desplazar
    revivir_neon(nuevos)
    return nuevos


def b64(ruta, max_ancho=None, calidad=82):
    im = Image.open(ruta).convert("RGB")
    if max_ancho and im.width > max_ancho:
        im = im.resize((max_ancho, round(im.height * max_ancho / im.width)), Image.LANCZOS)
    tmp = ruta + ".jpg"
    im.save(tmp, "JPEG", quality=calidad, optimize=True)
    with open(tmp, "rb") as f:
        d = base64.b64encode(f.read()).decode()
    os.remove(tmp)
    return "data:image/jpeg;base64," + d


def render_vista(nave, etiqueta, az, el, rapido, con_r6=True, r6_en_cubierta=False):
    c.escena_vacia()
    objs = [o for o in cargar_fbx(os.path.join(MODELOS, nave["archivo"], f"{nave['archivo']}.fbx")) if o.type == "MESH"]
    c.preparar_estudio(mundo=0.5, luz_clave=1100)
    mn, mx = c.caja_limite(objs)
    extra = []
    if con_r6:
        zc = (0.0 if r6_en_cubierta else mx.z / c.ESTUDIO) + 0.1
        extra = [h.maniqui_r6((0.0, (mn.y + mx.y) / 2 / c.ESTUDIO, zc))]
    sal = os.path.join("/tmp", f"{etiqueta}_{nave['id']}")
    rutas = c.renderizar_vistas(objs + extra, sal, [(etiqueta, az, el)],
                                tam=360 if rapido else 760, muestras=16 if rapido else 64,
                                con_malla=False, margen=1.05, centro=(mn + mx) / 2)
    return rutas[0][1]


def render_escala(rapido):
    """Las 3 naves en fila (a escala real entre ellas) con un maniquí R6 delante."""
    c.escena_vacia()
    x = 0.0
    todos = []
    for nave in NAVES:
        objs = cargar_fbx(os.path.join(MODELOS, nave["archivo"], f"{nave['archivo']}.fbx"),
                          desplazar=Vector((x * c.ESTUDIO, 0, 0)))
        todos += [o for o in objs if o.type == "MESH"]
        x += nave["largo"] * 0.62 + 18  # separación proporcional
    # Maniquí R6 delante de la primera nave.
    r6 = h.maniqui_r6((-14, -20, 0))
    todos2 = todos + [r6]
    c.preparar_estudio(mundo=0.5, luz_clave=1300)
    mn, mx = c.caja_limite(todos2)
    sal = "/tmp/escala_naves"
    rutas = c.renderizar_vistas(todos2, sal, [("escala", -30, 16)],
                                tam=420 if rapido else 900, muestras=12 if rapido else 48,
                                con_malla=False, margen=1.06, centro=(mn + mx) / 2, lente=70)
    return rutas[0][1]


HTML = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Naves humanas</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--cyan:#3DF2FF;--bg:#05070f;--panel:#0d1322;--linea:#1d2740;--txt:#cdd6ea;--tenue:#7f8aa6}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;overflow-x:hidden}
#estrellas{position:fixed;inset:0;z-index:0;pointer-events:none}
.envoltura{position:relative;z-index:1;max-width:1280px;margin:0 auto;padding:28px 24px 60px}
header h1{font-size:30px;letter-spacing:1px;color:#fff}
header h1 b{color:var(--cyan)}
header p{color:var(--tenue);margin-top:6px;font-size:14px}
.rejilla{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:26px}
.card{background:var(--panel);border:1px solid var(--linea);border-radius:14px;overflow:hidden;cursor:pointer;
  transition:transform .18s,border-color .18s,box-shadow .18s}
.card:hover{transform:translateY(-4px);border-color:var(--cyan);box-shadow:0 10px 34px #0bc9e033}
.card .img{aspect-ratio:16/10;background:#060a14 center/cover}
.card .cuerpo{padding:14px 16px 18px}
.card .clase{display:inline-block;font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:var(--cyan);
  border:1px solid #16465a;background:#0a2730;border-radius:20px;padding:3px 10px;margin-bottom:9px}
.card h2{font-size:19px;color:#fff}
.card .meta{color:var(--tenue);font-size:13px;margin-top:5px}
.escala{margin-top:34px;background:var(--panel);border:1px solid var(--linea);border-radius:14px;padding:18px}
.escala h3{font-size:16px;color:#fff;margin-bottom:4px}.escala p{color:var(--tenue);font-size:13px;margin-bottom:12px}
.escala img{width:100%;border-radius:10px;display:block}
.pie{margin-top:34px;color:var(--tenue);font-size:12px;line-height:1.7;border-top:1px solid var(--linea);padding-top:16px}
.modal{position:fixed;inset:0;z-index:10;background:#02040ad8;backdrop-filter:blur(6px);display:none;
  align-items:center;justify-content:center;padding:28px}
.modal.on{display:flex}
.modal .caja{background:var(--panel);border:1px solid var(--cyan);border-radius:16px;max-width:1120px;width:100%;
  max-height:90vh;overflow:auto;box-shadow:0 0 60px #0bc9e022}
.modal .top{display:flex;justify-content:space-between;align-items:flex-start;padding:20px 24px;border-bottom:1px solid var(--linea)}
.modal .top h2{font-size:24px;color:#fff}.modal .top .clase{color:var(--cyan);font-size:13px;letter-spacing:1.5px}
.cerrar{background:none;border:1px solid var(--linea);color:var(--txt);border-radius:8px;width:34px;height:34px;cursor:pointer;font-size:18px}
.cerrar:hover{border-color:var(--cyan);color:var(--cyan)}
.modal .vistas{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:22px 24px}
.modal .vistas figure{background:#060a14;border:1px solid var(--linea);border-radius:10px;overflow:hidden}
.modal .vistas img{width:100%;display:block}
.modal .vistas figcaption{padding:8px 12px;font-size:12px;color:var(--tenue)}
.modal .info{padding:0 24px 24px}
.modal .info .fila{display:flex;gap:26px;flex-wrap:wrap;margin-bottom:14px}
.modal .info .dato .k{color:var(--tenue);font-size:11px;text-transform:uppercase;letter-spacing:1px}
.modal .info .dato .v{color:#fff;font-size:16px;margin-top:2px}
.modal .info h4{color:var(--cyan);font-size:13px;letter-spacing:1px;text-transform:uppercase;margin:14px 0 8px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chips span{background:#0a2730;border:1px solid #16465a;color:#bfeef6;border-radius:8px;padding:5px 11px;font-size:13px}
@media(max-width:820px){.rejilla{grid-template-columns:1fr}.modal .vistas{grid-template-columns:1fr}}
</style></head>
<body>
<canvas id="estrellas"></canvas>
<div class="envoltura">
  <header>
    <h1>Naves humanas · <b>Humanos vs Monstruos</b></h1>
    <p>Tres naves tripulables de la facción humana — metal, paneles y energía cyan #3DF2FF. Haz clic en una nave para ver su sección interior y sus estaciones.</p>
  </header>
  <div class="rejilla">{CARDS}</div>
  <div class="escala">
    <h3>Comparación de escala</h3>
    <p>Las 3 naves a escala real entre ellas, con un personaje R6 (5 studs) a la izquierda.</p>
    <img src="{ESCALA}" alt="Comparación de escala">
  </div>
  <div class="pie">
    Modelado procedural en Blender (bpy) · ejes de Roblox, 1 stud = 0,28 m · cada nave en piezas separadas (casco, cubierta, timón, cañones, motores, neón…) con marcas de interacción para los ProximityPrompts.<br>
    Las 3 naves monstruo se construyen aparte (los monstruos usan criaturas, no naves tecnológicas); sus cards se añadirán cuando estén en el repositorio.
  </div>
</div>
<div class="modal" id="modal"><div class="caja">
  <div class="top"><div><div class="clase" id="m_clase"></div><h2 id="m_nombre"></h2></div>
    <button class="cerrar" onclick="cerrar()">×</button></div>
  <div class="vistas">
    <figure><img id="m_ext"><figcaption>Exterior (con maniquí R6 para escala)</figcaption></figure>
    <figure><img id="m_int"><figcaption id="m_intcap">Sección interior — niveles</figcaption></figure>
  </div>
  <div class="info">
    <div class="fila" id="m_datos"></div>
    <h4>Estaciones interactivas</h4><div class="chips" id="m_est"></div>
  </div>
</div></div>
<script>
const NAVES={DATOS};
function abrir(i){const n=NAVES[i];
  m_clase.textContent=n.clase+' · '+n.trip;m_nombre.textContent=n.nombre;
  m_ext.src=n.heroe;m_int.src=n.interior;
  document.getElementById('m_intcap').textContent=n.intcap;
  m_datos.innerHTML=[['Clase',n.clase],['Tamaño',n.tam],['Tripulación',n.trip]].map(d=>
    `<div class="dato"><div class="k">${d[0]}</div><div class="v">${d[1]}</div></div>`).join('')+
    `<div class="dato" style="flex:1;min-width:200px"><div class="k">Concepto</div><div class="v" style="font-size:13px;color:#cdd6ea">${n.desc}</div></div>`;
  m_est.innerHTML=n.estaciones.map(e=>`<span>${e}</span>`).join('');
  modal.classList.add('on');}
function cerrar(){modal.classList.remove('on');}
modal.addEventListener('click',e=>{if(e.target===modal)cerrar();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')cerrar();});
// Campo de estrellas.
const cv=document.getElementById('estrellas'),cx=cv.getContext('2d');
function estrellas(){cv.width=innerWidth;cv.height=innerHeight;cx.clearRect(0,0,cv.width,cv.height);
  for(let i=0;i<220;i++){const x=Math.random()*cv.width,y=Math.random()*cv.height,r=Math.random()*1.3;
    cx.fillStyle=Math.random()<0.15?'rgba(61,242,255,.9)':'rgba(255,255,255,'+(0.3+Math.random()*0.6)+')';
    cx.beginPath();cx.arc(x,y,r,0,7);cx.fill();}}
estrellas();addEventListener('resize',estrellas);
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()

    for n in NAVES:
        n["_heroe"] = render_vista(n, "heroe", -42, 20, args.rapido)
        interior = os.path.join(MODELOS, n["archivo"], "render", f"{n['archivo']}_interior.png")
        if os.path.exists(interior):
            n["_interior"] = interior
            n["_intcap"] = "Sección interior — niveles"
        else:
            # Nave de cubierta abierta (Interceptor): vista cenital de la cubierta como "interior".
            n["_interior"] = render_vista(n, "cubierta", 0, 86, args.rapido, r6_en_cubierta=True)
            n["_intcap"] = "Cubierta (vista cenital) — nave de un nivel abierto"
    escala = render_escala(args.rapido)

    import json
    datos = []
    cards = ""
    for i, n in enumerate(NAVES):
        hb = b64(n["_heroe"], max_ancho=760)
        ib = b64(n["_interior"], max_ancho=900)
        datos.append({"nombre": n["nombre"], "clase": n["clase"], "tam": n["tam"], "trip": n["trip"],
                      "desc": n["desc"], "estaciones": n["estaciones"], "heroe": hb, "interior": ib,
                      "intcap": n["_intcap"]})
        cards += (f'<div class="card" onclick="abrir({i})"><div class="img" style="background-image:url({hb})"></div>'
                  f'<div class="cuerpo"><span class="clase">{n["clase"]}</span><h2>{n["nombre"]}</h2>'
                  f'<div class="meta">{n["tam"]} · {n["trip"]}</div></div></div>')
    html = HTML.replace("{CARDS}", cards).replace("{ESCALA}", b64(escala, max_ancho=1200)) \
               .replace("{DATOS}", json.dumps(datos, ensure_ascii=False))
    destino = os.path.join(MODELOS, "preview_naves.html")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[ok] {destino}  ({os.path.getsize(destino)//1024} KB)")


if __name__ == "__main__":
    main()
