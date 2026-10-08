"""Two-part 3D-printable carry case for the OBSBOT Tiny 3 Lite; the camera lies on its back. Run via `make`, see README.md."""
import argparse
import base64
import json
import os

import numpy as np
import shapely
import trimesh
from manifold3d import CrossSection, FillRule, Manifold

ap = argparse.ArgumentParser()
ap.add_argument("--variant", default="friction", choices=("friction", "snap", "magnet", "magnet4"))
ap.add_argument("--out", default="out")
ap.add_argument("--check", action="store_true")
ap.add_argument("--preview", action="store_true")
ap.add_argument("--index", nargs="*", metavar="VARIANT", help="write <out>/index.html linking these variants' outputs")
ARGS = ap.parse_args()
VARIANT = {"friction": {}, "snap": {"SNAP": 0.3, "WALL": 2.8, "LIP_T": 1.2},
           "magnet": {"MAG": 2, "FIT": 0.35}, "magnet4": {"MAG": 4, "FIT": 0.35}}[ARGS.variant]

P = lambda k, d: float(os.environ.get(k, VARIANT.get(k, d)))  # env > variant default > default
CAM_W, CAM_D, CAM_H = P("CAM_W", 41), P("CAM_D", 41), P("CAM_H", 58)
CLEAR_L, CLEAR_W, CLEAR_H = P("CLEAR_L", 1.0), P("CLEAR_W", 2.1), P("CLEAR_H", 1.0)
WALL, FLOOR = P("WALL", 2.4), P("FLOOR", 2.4)
R_IN, R_EDGE = P("R_IN", 4), P("R_EDGE", 3)
TRAY, LIP_H, LIP_T, FIT = P("TRAY", 15), P("LIP_H", 5), P("LIP_T", 1.0), P("FIT", 0.2)
NOTCH_R, RIB = P("NOTCH_R", 4), P("RIB", 0.6)
SNAP, SNAP_L = P("SNAP", 0), P("SNAP_L", 20)
MAG, MAG_D, MAG_T = int(P("MAG", 0)), P("MAG_D", 6), P("MAG_T", 3)  # magnet pairs (0 / 2 / 4); disc diameter x thickness
POCKET_D, POCKET_DEPTH, LOBE_R, BLEND = P("POCKET_D", 6.4), P("POCKET_DEPTH", 3.2), P("LOBE_R", 5.0), P("BLEND", 5.0)

# Lying pose: the camera's 58 height runs along x, 41 width along y, 41 depth is the cavity height.
IN_L, IN_W, IN_H = CAM_H + 2 * CLEAR_L, CAM_W + 2 * CLEAR_W, CAM_D + 2 * CLEAR_H
OUT_L, OUT_W, OUT_H = IN_L + 2 * WALL, IN_W + 2 * WALL, IN_H + 2 * FLOOR
R_OUT = R_IN + WALL
Z_SPLIT = FLOOR + TRAY
# Magnet pockets sit in outward lobes on the long walls, 0.8 mm of skin outside the lid's groove wall.
MAG_OFF = LIP_T + FIT + 0.8 + POCKET_D / 2  # pocket centre distance outside the cavity face
MAG_XY = [(x, s * (IN_W / 2 + MAG_OFF)) for x in {0: [], 2: [0], 4: [-IN_L / 4, IN_L / 4]}[MAG] for s in (1, -1)]
LEAD = 0.6  # tongue tip lead-in height; tip is 0.4 thinner
BASE_H = 23  # camera model base height (standing)

# Standing camera frame: z up, base bottom at z=0, lens facing -y. ENV is its spec bounding box.
ENV = Manifold.cube((CAM_W, CAM_D, CAM_H)).translate((-CAM_W / 2, -CAM_D / 2, 0))
_lie_rot = lambda m: m.rotate((-90, 0, 0)).rotate((0, 0, -90))  # (x, y, z) -> (z, -x, -y): lens up, base end at -x
_b = _lie_rot(ENV).bounding_box()
LIE_T = (-(_b[0] + _b[3]) / 2, -(_b[1] + _b[4]) / 2, FLOOR + CLEAR_H - _b[2])  # centre in cavity, CLEAR_H above floor


def lie(m):
    """Standing camera frame -> lying in the cavity."""
    return _lie_rot(m).translate(LIE_T)


def lie_pt(p):
    return [p[2] + LIE_T[0], -p[0] + LIE_T[1], -p[1] + LIE_T[2]]


def rrect(w, d, r):
    """Centered w x d rounded rectangle with corner radius r, as a shapely polygon."""
    return shapely.box(-w / 2 + r, -d / 2 + r, w / 2 - r, d / 2 - r).buffer(r, quad_segs=16)


def cs(poly):
    """shapely polygon (no holes) -> manifold CrossSection."""
    return CrossSection([np.asarray(poly.exterior.coords)[:-1]], FillRule.EvenOdd)


def ring(t, h, z):
    """Wall ring hugging the cavity outline: thickness t outward, height h, bottom at z."""
    return (cs(rrect(IN_L + 2 * t, IN_W + 2 * t, R_IN + t)) - cs(rrect(IN_L, IN_W, R_IN))).extrude(h).translate((0, 0, z))


def outline():
    """Plan outline: rounded rectangle plus magnet lobes, blended by a morphological closing (concave fillets)."""
    o = rrect(OUT_L, OUT_W, R_OUT)
    if MAG_XY:
        o = shapely.unary_union([o] + [shapely.Point(p).buffer(LOBE_R, quad_segs=16) for p in MAG_XY])
        o = o.buffer(BLEND, quad_segs=16).buffer(-BLEND, quad_segs=16)
    return o


def outer():
    """Outline extruded with every edge rounded by R_EDGE: Minkowski sum of the inset prism and a sphere."""
    prism = cs(outline().buffer(-R_EDGE, quad_segs=16)).extrude(OUT_H - 2 * R_EDGE).translate((0, 0, R_EDGE))
    return Manifold.minkowski_sum(prism, Manifold.sphere(R_EDGE, 24))


def wedge(y_base, z_base, y_tip, z_tip, length):
    """Trapezoidal prisms along x on both +-y long walls: face at y_base spanning z_base, face at y_tip spanning z_tip."""
    pts = [(sx * length / 2, y, z) for sx in (-1, 1) for y, zz in ((y_base, z_base), (y_tip, z_tip)) for z in zz]
    w = Manifold.hull_points(np.array(pts, float))
    return w + w.mirror((0, 1, 0))


def inside(a, b, tol=1e-6):
    a, b = a.bounding_box(), b.bounding_box()
    return all(a[i] >= b[i] - tol and a[i + 3] <= b[i + 3] + tol for i in range(3))


def camera():
    """Approximate Tiny 3 Lite, standing (see ENV). Eyeballed from photos; for visualisation only. Parts overlap 0.5."""
    base = cs(rrect(41, 41, 8)).extrude(BASE_H)
    table = Manifold.cylinder(5, 16.5).translate((0, 0, BASE_H - 0.5))  # turntable z 23..27.5
    post = Manifold.cube((9, 14, 18)).translate((11.5, -7, 27))  # arm post x 11.5..20.5, z 27.5..45
    post += Manifold.cylinder(9, 7).rotate((0, 90, 0)).translate((11.5, 0, 45))  # rounded arm top, reaches z 52
    axle = Manifold.cylinder(3, 8).rotate((0, 90, 0)).translate((9, 0, 44))  # axle disc x 9.5..11.5
    head = Manifold.batch_hull([Manifold.sphere(6, 32).translate((x, y, z))  # 30 x 26 x 28, edge radius 6
                                for x in (-14.5, 3.5) for y in (-14.5, -0.5) for z in (36, 52)])
    recess = Manifold.cylinder(2.5, 9).rotate((90, 0, 0)).translate((-5.5, -19, 44))  # 1.5 deep from y=-20.5
    lens = Manifold.cylinder(1.5, 6.5).rotate((90, 0, 0)).translate((-5.5, -18.5, 44))  # 1.0 proud of recess floor
    cam = base + table + post + axle + head - recess + lens
    assert inside(cam, ENV), cam.bounding_box()
    return cam


RING_STAND = (-5.5, -20.5, 44)  # lens ring centre on the standing camera's front face


def build():
    body = outer()
    cavity = cs(rrect(IN_L, IN_W, R_IN)).extrude(IN_H).translate((0, 0, FLOOR))
    tongue = ring(LIP_T, LIP_H - LEAD, Z_SPLIT) + ring(LIP_T - 0.4, LEAD, Z_SPLIT + LIP_H - LEAD)
    groove = ring(LIP_T + FIT, LIP_H + 0.4, Z_SPLIT - 0.01)

    tray = body.trim_by_plane((0, 0, -1), -Z_SPLIT) - cavity + tongue
    if RIB > 0:  # 2 crush ribs on the long (+-y) walls under the camera base; none on the end walls (only CLEAR_L there)
        h = Z_SPLIT - 1 - FLOOR
        rib = Manifold.cube((2, RIB + 0.5, h), True)  # overlaps 0.5 into the wall
        x = lie_pt((0, 0, BASE_H / 2))[0]
        for s in (1, -1):
            tray += rib.translate((x, s * (IN_W / 2 - RIB + (RIB + 0.5) / 2), FLOOR + h / 2))

    notch = Manifold.cylinder(10, NOTCH_R, center=True).rotate((0, 90, 0))
    lid = body.trim_by_plane((0, 0, 1), Z_SPLIT) - cavity - groove
    lid = lid - notch.translate((OUT_L / 2, 0, Z_SPLIT)) - notch.translate((-OUT_L / 2, 0, Z_SPLIT))

    if SNAP > 0:  # detent: bump on the lid groove wall snaps into a recess in the tongue; band above the recess retains
        gw, tf, z = IN_W / 2 + LIP_T + FIT, IN_W / 2 + LIP_T, Z_SPLIT  # groove wall, tongue face
        lid += wedge(gw + 0.3, (z + 1.6, z + 3.0), gw - FIT - SNAP, (z + 2.1, z + 2.5), SNAP_L)
        tray -= wedge(tf + 0.3, (z + 1.45, z + 3.15), tf - SNAP - 0.05, (z + 1.95, z + 2.65), SNAP_L + 0.6)

    pockets = Manifold()  # blind magnet pockets, open at the split plane: tray's go down, lid's go up
    if MAG_XY:
        pocket = Manifold.cylinder(POCKET_DEPTH, POCKET_D / 2, circular_segments=48)
        pockets = Manifold.compose([pocket.translate((x, y, z)) for x, y in MAG_XY for z in (Z_SPLIT - POCKET_DEPTH, Z_SPLIT)])
        tray, lid = tray - pockets, lid - pockets
    return tray, lid, tongue, groove, cavity, pockets


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


def size(m):
    b = m.bounding_box()
    return np.array(b[3:]) - np.array(b[:3])


def export(parts, out):
    print(f"--- {ARGS.variant} ---")
    print(f"{'part':10s} {'bbox (mm)':>22s} {'vol cm3':>8s} {'g@1.24':>7s}  watertight")
    for name, m in parts.items():
        tm = to_trimesh(m)
        tm.export(os.path.join(out, f"tiny3lite_{name}.stl"))
        vol = m.volume() / 1000
        print(f"{name:10s} {'x'.join(f'{s:.1f}' for s in size(m)):>22s} {vol:8.1f} {vol * 1.24:7.1f}  {tm.is_watertight}")


def check(tray, lid, tongue, groove, cavity, pockets, cam_stand, cam, parts):
    print(f"--- {ARGS.variant} ---")
    for name, m in parts.items():
        assert m.volume() > 0 and to_trimesh(m).is_watertight, name
        print(f"PASS {name}: volume > 0, watertight")
    assert (tray ^ lid).volume() < 1e-6
    print("PASS no interference between tray and lid")
    box = lie(ENV)
    assert (box ^ tray).volume() < 1e-6 and (box ^ lid).volume() < 1e-6
    print(f"PASS lying {CAM_H:g} x {CAM_W:g} x {CAM_D:g} box clears tray (incl. ribs) and lid")
    assert (cam ^ tray).volume() < 1e-6 and (cam ^ lid).volume() < 1e-6 and inside(cam, box)
    print("PASS camera model clears tray and lid and stays inside that box")
    ob = outline().bounds
    assert np.allclose(size(tray + lid), (ob[2] - ob[0], ob[3] - ob[1], OUT_H), atol=0.05), size(tray + lid)
    print(f"PASS assembled bbox = {ob[2] - ob[0]:g} x {ob[3] - ob[1]:g} x {OUT_H:g}")
    assert abs((tongue ^ groove).volume() - tongue.volume()) < 1e-6
    assert abs(lid.bounding_box()[2] - Z_SPLIT) < 1e-6 and abs(tray.bounding_box()[5] - Z_SPLIT - LIP_H) < 1e-6
    print("PASS tongue sits fully inside the groove")
    assert inside(cam_stand, ENV)
    print(f"PASS camera model within {CAM_W:g} x {CAM_D:g} x {CAM_H:g} standing")
    v = (tray ^ lid.translate((0, 0, 1.0))).volume()
    if SNAP > 0:
        assert v > 0.5, v
        print(f"PASS snap engages: lifting the lid 1 mm interferes by {v:.1f} mm³")
    else:
        assert v < 1e-6, v
        print("PASS slip fit: lifting the lid 1 mm has no interference")
    thin = LIP_T - (SNAP + 0.05)
    assert thin >= 0.6, f"tongue only {thin:.2f} mm thick under the snap recess (< 0.6): raise LIP_T or lower SNAP"
    print(f"PASS tongue keeps {thin:.2f} mm under the recess")
    if MAG:
        assert (pockets ^ (tray + lid)).volume() < 1e-6 and abs(pockets.volume() - 2 * MAG * np.pi * (POCKET_D / 2) ** 2 * POCKET_DEPTH) < 2 * MAG
        big = Manifold.cylinder(POCKET_DEPTH + 0.8, POCKET_D / 2 + 0.8, circular_segments=48)  # pocket + 0.8 mm skin, open face kept
        shell = Manifold.compose([big.translate((x, y, z)) for x, y in MAG_XY for z in (Z_SPLIT - POCKET_DEPTH - 0.8, Z_SPLIT)]) - pockets
        assert abs((shell ^ (tray + lid)).volume() - shell.volume()) < 1e-3, "magnet pocket breaks through a wall / groove"
        assert (shell ^ (cavity + groove + tongue)).volume() < 1e-6
        print(f"PASS {MAG} magnet pairs: {2 * MAG} pockets Ø{POCKET_D:g} x {POCKET_DEPTH:g} mm, coaxial across the split, >= 0.8 mm skin")
        rec = POCKET_DEPTH - MAG_T
        assert rec >= 0.1, f"magnets would stand proud: pocket {POCKET_DEPTH} < magnet {MAG_T} + 0.1"
        print(f"PASS Ø{MAG_D:g} x {MAG_T:g} mm magnets sit {rec:.1f} mm recessed per side ({2 * rec:.1f} mm gap, never touch)")


HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Tiny 3 Lite Case – __VARIANT__</title>
<style>body{margin:0;background:#1e1f24;font:13px system-ui,sans-serif;color:#ddd}canvas{display:block}
#ui{position:fixed;top:10px;left:10px;background:#000a;padding:8px 12px;border-radius:6px;line-height:1.9}#ui label{margin-right:10px}</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script></head><body>
<div id="ui"><label><input type="checkbox" id="tray" checked> Tray</label><label><input type="checkbox" id="lid" checked> Lid</label>
<label><input type="checkbox" id="cam" checked> Camera</label><label><input type="checkbox" id="xray" checked> X-ray lid</label>
<label><input type="checkbox" id="cut"> Cut at x=0</label><br>
<label>Explode <input type="range" id="explode" min="0" max="70" value="0"></label><button id="mode">As printed</button><br><span id="info"></span></div>
<script id="data" type="application/json">__DATA__</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {STLLoader} from 'three/addons/loaders/STLLoader.js';
const D = JSON.parse(document.getElementById('data').textContent), $ = id => document.getElementById(id);
THREE.Object3D.DEFAULT_UP.set(0, 0, 1);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x1e1f24);
const camera = new THREE.PerspectiveCamera(45, innerWidth / innerHeight, 1, 2000);
camera.up.set(0, 0, 1); camera.position.set(120, -140, 100); camera.lookAt(0, 0, 24);
const renderer = new THREE.WebGLRenderer({antialias: true}); renderer.localClippingEnabled = true;
renderer.setPixelRatio(devicePixelRatio); renderer.setSize(innerWidth, innerHeight); document.body.appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true; controls.target.set(0, 0, D.OUT_H / 2);
scene.add(new THREE.HemisphereLight(0xffffff, 0x404060, 1.2));
const sun = new THREE.DirectionalLight(0xffffff, 1.5); sun.position.set(100, -80, 150); scene.add(sun);
const fill = new THREE.DirectionalLight(0xffffff, 0.5); fill.position.set(-80, 100, 60); scene.add(fill);
const grid = new THREE.GridHelper(200, 20, 0x555555, 0x333333); grid.rotation.x = Math.PI / 2; scene.add(grid);
const loader = new STLLoader();
const geo = b64 => { const g = loader.parse(Uint8Array.from(atob(b64), c => c.charCodeAt(0)).buffer); g.computeVertexNormals(); return g; };
const mat = o => new THREE.MeshStandardMaterial({side: THREE.DoubleSide, ...o});
const lidMat = mat({color: 0x5aa0d8, roughness: .55, transparent: true});
const tray = new THREE.Mesh(geo(D.tray), mat({color: 0x4a86c5, roughness: .55}));
const lid = new THREE.Mesh(geo(D.lid), lidMat);
const cam = new THREE.Group();
cam.add(new THREE.Mesh(geo(D.cam), mat({color: 0x1a1a1a, metalness: .25, roughness: .5})));
const ring = new THREE.Mesh(new THREE.TorusGeometry(12, 0.9, 16, 64), mat({color: 0xe3242b, emissive: 0x400000}));
ring.position.set(...D.ring); cam.add(ring);
const magGeo = new THREE.CylinderGeometry(D.mag.r, D.mag.r, D.mag.h, 32).rotateX(Math.PI / 2), magMat = mat({color: 0xa8a8a8, metalness: .5, roughness: .5});
for (const [part, list] of [[tray, D.mag.tray], [lid, D.mag.lid]]) for (const p of list) { const m = new THREE.Mesh(magGeo, magMat); m.position.set(...p); part.add(m); }
scene.add(tray, lid, cam);
const plane = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 0), mats = [tray.material, lidMat, cam.children[0].material, ring.material, magMat];
let printed = false;
function update() {
  tray.visible = $('tray').checked; lid.visible = $('lid').checked; cam.visible = $('cam').checked && !printed;
  const xray = $('xray').checked && !printed;
  lidMat.opacity = xray ? 0.3 : 1; lidMat.depthWrite = !xray;
  for (const m of mats) m.clippingPlanes = $('cut').checked ? [plane] : [];
  if (printed) { tray.position.set(-40, 0, 0); lid.rotation.x = 0; lid.position.set(40, 0, 0); }
  else { tray.position.set(0, 0, 0); lid.rotation.x = Math.PI; lid.position.set(0, 0, D.OUT_H + +$('explode').value); }
  $('mode').textContent = printed ? 'Assembled' : 'As printed';
}
$('mode').onclick = () => { printed = !printed; update(); };
for (const id of ['tray', 'lid', 'cam', 'xray', 'cut', 'explode']) $(id).oninput = update;
const mm = a => a.map(v => v.toFixed(1)).join(' x ') + ' mm';
$('info').textContent = `${D.variant}: case ${mm(D.OUT)}  |  camera model (approx.) ${mm(D.cam_dims)}`;
const H = Object.fromEntries(location.hash.slice(1).split('&').filter(Boolean).map(s => s.split('=')));  // #cut&explode=30&printed&noxray
if ('cut' in H) $('cut').checked = true; if ('explode' in H) $('explode').value = H.explode;
if ('printed' in H) printed = true; if ('noxray' in H) $('xray').checked = false;
update();
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
</script></body></html>
"""


def preview(tray, lid, cam, parts, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    def section(ax, m, slab, cols, c):  # intersect with a thin slab, draw the triangles projected onto axes `cols`
        tm = to_trimesh(m ^ slab)
        ax.add_collection(PolyCollection(tm.vertices[tm.faces][:, :, cols], facecolors=c, edgecolors=c, linewidths=0.3))

    blue, red, grey = "#3a6ea5", "#c0504d", "#777777"
    fig = plt.figure(figsize=(20, 5))
    fig.suptitle(f"variant: {ARGS.variant}")
    for i, name in enumerate(("case_tray", "case_lid")):
        ax = fig.add_subplot(1, 4, i + 1, projection="3d")
        tm = to_trimesh(parts[name])
        ax.plot_trisurf(*tm.vertices.T, triangles=tm.faces, color="#8fb3c9", edgecolor="none")
        ax.set_box_aspect(size(parts[name]))
        ax.view_init(30, -55)
        ax.set_title(f"{name} (as printed)")
    ax = fig.add_subplot(1, 4, 3)
    slab = Manifold.cube((2 * OUT_L, 0.1, 2 * OUT_H), True).translate((0, 0, OUT_H / 2))
    for m, c in ((tray, blue), (lid, red), (cam, grey)):
        section(ax, m, slab, [0, 2], c)
    b = lie(ENV).bounding_box()
    ax.add_patch(plt.Rectangle((b[0], b[2]), b[3] - b[0], b[5] - b[2], fill=False, ls="--", ec="k", label="camera envelope"))
    ax.set_aspect("equal")
    ax.autoscale()
    ax.set(title="XZ section at y=0 (assembled, camera grey)", xlabel="x (mm)", ylabel="z (mm)")
    ax.legend(loc="lower right")
    ax = fig.add_subplot(1, 4, 4)
    xs = MAG_XY[0][0] if MAG_XY else 0  # cut through a magnet pocket when there is one
    slab = Manifold.cube((0.1, 4 * OUT_W, 2 * OUT_H), True).translate((xs, 0, OUT_H / 2))
    for m, c in ((tray, blue), (lid, red)):
        section(ax, m, slab, [1, 2], c)
    ax.set(xlim=(IN_W / 2 - 2, outline().bounds[3] + 1), ylim=(Z_SPLIT - 2 - (POCKET_DEPTH if MAG else 0), Z_SPLIT + LIP_H + 2),
           title=f"rim detail, YZ at x={xs:g}", xlabel="y (mm)", ylabel="z (mm)")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "preview.png"), dpi=110)
    print("wrote", os.path.join(out, "preview.png"))

    b64 = lambda m: base64.b64encode(to_trimesh(m).export(file_type="stl")).decode()
    zt, zl = Z_SPLIT - POCKET_DEPTH + MAG_T / 2, Z_SPLIT + POCKET_DEPTH - MAG_T / 2  # magnet centres, seated at the pocket bottoms
    data = {"variant": ARGS.variant, "tray": b64(parts["case_tray"]), "lid": b64(parts["case_lid"]), "cam": b64(cam),
            "ring": lie_pt(RING_STAND), "OUT": size(tray + lid).tolist(), "OUT_H": OUT_H, "Z_SPLIT": Z_SPLIT, "cam_dims": size(cam).tolist(),
            "mag": {"r": MAG_D / 2, "h": MAG_T, "tray": [[x, y, zt] for x, y in MAG_XY],
                    "lid": [[x, -y, OUT_H - zl] for x, y in MAG_XY]}}  # lid magnets in the printed (flipped) lid's frame
    with open(os.path.join(out, "preview.html"), "w") as f:
        f.write(HTML.replace("__VARIANT__", ARGS.variant).replace("__DATA__", json.dumps(data)))
    print("wrote", os.path.join(out, "preview.html"))
    meta = {"outer": size(tray + lid).tolist(), "grams": round(sum(parts[p].volume() for p in ("case_tray", "case_lid")) / 1000 * 1.24),
            "stl": [f"tiny3lite_{p}.stl" for p in parts], "hardware": f"{2 * MAG}&times; &Oslash;{MAG_D:g}&times;{MAG_T:g} mm disc magnets" if MAG else "no hardware"}
    with open(os.path.join(out, "meta.json"), "w") as f:
        json.dump(meta, f)


VARIANT_INFO = {"friction": ("Friction fit", "Slip-fit tongue and groove, no hardware. Easiest to print and tune. "
                                             "Stays shut on a desk; not guaranteed upside down in a bag."),
                "snap": ("Snap detent", "A 20 mm ridge inside the lid clicks into a recess in the tongue, so the lid stays "
                                        "closed in a bag. Thicker walls; tune SNAP per printer."),
                "magnet": ("Magnetic, 2 pairs", "Glide-fit tongue and groove held shut by two pairs of glued disc magnets in "
                                                "blended lobes on the long walls. Easy one-hand open, firm hold."),
                "magnet4": ("Magnetic, 4 pairs", "Same lobes, four magnet pairs for a stronger hold; lift one end at the thumb "
                                                 "notch to peel two pairs at a time.")}

INDEX = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>OBSBOT Tiny 3 Lite case</title>
<style>:root{--bg:#14171c;--panel:#1e232b;--ink:#e8eaee;--muted:#9aa3b0;--accent:#5aa0d8;--line:#313945}
*{box-sizing:border-box;margin:0}body{background:var(--bg);color:var(--ink);padding:40px 20px;font:15px/1.5 -apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1080px;margin:0 auto}h1{font-size:30px}h1 span{color:var(--accent)}.tagline{color:var(--muted);margin:6px 0 8px}a{color:var(--accent)}
.grid{display:grid;gap:18px;margin-top:28px;grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}
article{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}article img{width:100%;border-radius:8px;background:#fff}
article h2{font-size:17px;margin:12px 0 4px}.geo{color:var(--muted);font-size:13px;margin-bottom:10px}
.btn{display:inline-block;background:var(--accent);color:#08141c;font-weight:600;text-decoration:none;padding:8px 14px;border-radius:8px;font-size:14px}
details{margin-top:10px;font-size:13px;color:var(--muted)}details a{color:var(--ink)}details li{margin:3px 0 3px 18px}
footer{color:var(--muted);font-size:13px;margin-top:32px}</style></head><body><main>
<h1><span>OBSBOT Tiny 3 Lite</span> carry case</h1>
<p class="tagline">3D-printable two-part case for the OBSBOT Tiny 3 Lite webcam. The camera lies flat in a shallow tray under a deep lid; grab it by the body, never by the gimbal. Parametric, generated from Python.</p>
<p><a href="https://github.com/Ardakilic/obsbot-tiny3-lite-case">Source, print settings &amp; design notes on GitHub</a></p>
<div class="grid">__CARDS__</div>
<footer>Camera: 41 x 41 x 58 mm, 73 g (OBSBOT spec). Case cavity 60 x 45.2 x 43 mm. Print both parts open side up, no supports, PETG or PLA. Models CC BY 4.0, code MIT.</footer>
</main></body></html>
"""

CARD = """<article><a href="{v}/preview.png"><img loading="lazy" src="{v}/preview.png" alt="{title} variant renders"></a>
<h2>{title}</h2><p class="geo">{outer} mm outer &middot; ~{grams} g of filament &middot; {hardware} &middot; {desc}</p>
<p><a class="btn" href="{v}/preview.html">Interactive 3D preview</a> &nbsp; <a href="{v}/preview.html#cut&explode=12">section view</a></p>
<details><summary>STL downloads</summary><ul>{stls}</ul></details></article>
"""


def index(variants, out):
    cards = []
    for v in variants:
        with open(os.path.join(out, v, "meta.json")) as f:
            m = json.load(f)
        title, desc = VARIANT_INFO.get(v, (v, ""))
        stls = "".join(f'<li><a href="{v}/{s}">{s}</a></li>' for s in m["stl"])
        cards.append(CARD.format(v=v, title=title, desc=desc, grams=m["grams"], stls=stls, hardware=m.get("hardware", ""),
                                 outer=" x ".join(f"{d:.1f}" for d in m["outer"])))
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(INDEX.replace("__CARDS__", "".join(cards)))
    print("wrote", os.path.join(out, "index.html"))


if __name__ == "__main__":
    if ARGS.index is not None:
        index(ARGS.index, ARGS.out)
        raise SystemExit
    os.makedirs(ARGS.out, exist_ok=True)
    tray, lid, tongue, groove, cavity, pockets = build()
    lid_print = lid.rotate((180, 0, 0))
    lid_print = lid_print.translate((0, 0, -lid_print.bounding_box()[2]))
    cam_stand = camera()
    cam = lie(cam_stand)
    parts = {"case_tray": tray, "case_lid": lid_print, "camera": cam}

    if ARGS.check:
        check(tray, lid, tongue, groove, cavity, pockets, cam_stand, cam, parts)
    elif ARGS.preview:
        preview(tray, lid, cam, parts, ARGS.out)
    else:
        export(parts, ARGS.out)
