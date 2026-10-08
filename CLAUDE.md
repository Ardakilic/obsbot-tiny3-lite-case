# CLAUDE.md — OBSBOT Tiny 3 Lite case

Parametric 3D-printed carry case for the **OBSBOT Tiny 3 Lite** webcam. Everything
(STLs, preview PNGs, three.js preview HTMLs, index.html) is **generated from
`case.py`** — never edit generated files by hand; change the script and run `make`.

Remote: `github.com/Ardakilic/obsbot-tiny3-lite-case` (public). GitHub Pages
(`ardakilic.github.io/obsbot-tiny3-lite-case`) republishes the whole checkout on
every push to `main` via `.github/workflows/pages.yml` (Pages source = Actions).
License: MIT for code (`LICENSE`), CC BY 4.0 for models/images (`LICENSE-MODELS`).

## Hard rules (from the owner)

- **Docker only.** No local Python, pip, venv or any other install on the host. Every
  command goes through the Makefile's `docker run`. One-off experiments: use the
  same image (`docker run --rm -v "$PWD":/work -w /work obsbot-tiny3-lite-case python ...`)
  or a throwaway container; scratch files go outside the repo.
- **Keep both variants** (`friction`, `snap`); every `make` regenerates both.
- **Keep the camera design.** The camera dimensions, the lying pose and the
  approximate camera model live in `case.py` (`CAM_*`, `lie()`, `camera()`); do not
  re-derive them from memory. Change them only with a cited source and update the
  "Verified camera geometry" section below.
- The `tiny-3-lite.stl` in the working folder is a third-party Printables model used
  only to measure the pocket. It is gitignored (license unknown); never commit it,
  never delete it, never need it at build time.
- `make check` must pass for both variants before committing; commit regenerated
  outputs together with the code change that produced them.

## Layout

```
case.py                      the whole generator: params, camera model, case geometry,
                             checks, matplotlib preview, three.js viewer template, index page
Makefile / Dockerfile        canonical build path (python:3.12-slim + pinned wheels)
.github/workflows/pages.yml  publishes the checkout to GitHub Pages on push to main
index.html                   generated Pages landing page (make index)
friction/  snap/             generated per variant: tiny3lite_case_tray.stl,
                             tiny3lite_case_lid.stl, tiny3lite_camera.stl (viewer only),
                             preview.png, preview.html, meta.json (for index.html)
README.md                    user-facing docs; AGENTS.md points here
```

## Commands

```bash
make                 # stl + check + preview + index, both variants (builds the image first)
make stl | check | preview | index
make VARIANTS=snap SNAP=0.25     # one variant, with parameter overrides (env vars)
make clean           # removes friction/ snap/ index.html
open snap/preview.html           # viewer; needs internet for the three.js CDN
```

Parameters are env vars read in `case.py` (`P()`): `env > variant default > default`.
`PARAMS` in the Makefile is the list passed through with `-e`; add a new parameter
in both places. A bare `make SNAP=0.25` turns the friction variant into a snap too,
so scope tuning runs with `VARIANTS=snap`.

## Verified camera geometry (do not re-derive)

Researched 2026-10-08. Sources: OBSBOT comparison table
(obsbot.com/comparison), JB Hi-Fi (labels W x H x D = 41 x 58 x 41), Thomann, Micro
Center, the Polish user manual PDF (OBSBOT_PW105), official product photos, reviews
(Tech4Gamers, Gizmochina, CGMagazine, The Cosmic Circus).

- **41 x 41 x 58 mm (W x D x H), 73 g.** All sources agree. The regular Tiny 3 is
  37 x 37 x 49 mm / 63 g with a detachable magnetic mount — a different product.
- Square base with rounded corners; **built-in fold-flat stand** hinged under the rear
  of the base (not magnetic, not detachable; flush when folded); UNC 1/4-20 socket in
  the bottom; USB-C on the back of the base; round pan turntable with LED ring; L-arm
  on one side carrying the rounded-square tilting lens head with a red ring; lens
  tilts straight down for sleep. Folded, it is the 41 x 41 x 58 box.
- OBSBOT publishes no corner radius; the cavity corner radius `R_IN` = 4 is small
  enough that a sharp-cornered block fits, so the real (rounder) camera fits.
- **Reference organizer** (Printables 1620707, "OBSBOT Tiny 3 Lite webcam gridfinity
  organizer"), measured by slicing its mesh: 2x2 Gridfinity bin 83.5 x 83.5 x 42 mm;
  pocket **60 x 45.2 mm, 34 mm deep**, camera lying on its side; a 1 mm deeper
  29 x 45 sub-pocket at one end (the base end) and finger scoops on both long sides
  at that end. Its clearances (1.0 per end on the 58, 2.1 per side on the 41) are
  the ones this case uses, because that author test-fitted a real camera.
- **Approximate camera model** (`camera()`, standing frame, z up, front = -y, must
  stay inside the 41 x 41 x 58 envelope — asserted): base rrect 41x41 r8 z0-23;
  turntable r16.5 z23-27.5; arm post 9 x 14 on the +x side z27.5-45 with a r7
  rounded top to z52; axle disc r8 at x 9.5-11.5, z44; head = hull of 8 r6 spheres,
  30 x 26 x 28 (x -20.5..9.5, y -20.5..5.5, z30-58); lens ring recess r9 1.5 deep,
  lens element r6.5. It is eyeballed from photos — for visualisation and the fit
  check only, never for printing. `RING_STAND` (-5.5, -20.5, 44) is the red ring
  centre used by the viewer.

## Design map

History: **v1 (rejected)** stood the camera upright in a 44 x 44 x 61 cup split at
36 mm — "just a box", and you would pull the camera out by the gimbal head.
**v2 (current)** lays it flat like the organizer. User question "will it stay
closed?" → honest answer no (slip fit) → the **snap** variant was added; both kept.

Shared geometry (mm, assembled coordinates, z up, tray floor at z=0, centred x/y):

- Lying pose: `lie()` = rotate(-90,0,0) then rotate(0,0,-90): (x,y,z) → (z,-x,-y);
  the camera's 58 runs along x, 41 width along y, 41 depth is the cavity height,
  **lens points up, base end at -x**. `LIE_T` centres it in the cavity, `CLEAR_H`
  above the floor.
- Cavity `IN_L x IN_W x IN_H` = (58+2·1.0) x (41+2·2.1) x (41+2·1.0) = 60 x 45.2 x 43,
  vertical corner radius `R_IN` 4. Outer = cavity + 2·WALL / 2·FLOOR, vertical
  corners `R_OUT` = R_IN + WALL, top/bottom edges rounded `R_EDGE` 3 (outer body =
  convex hull of 8 sampled tori, `outer()`).
- **Shallow tray + deep lid**: the tray holds `TRAY` = 15 of the 43 mm cavity
  (split plane `Z_SPLIT` = FLOOR + 15 = 17.4); the lid holds the other 28. With
  26 mm of the camera exposed when open you grab the body from the sides — that is
  why there are no finger scoops and no holes in the case. Weight rests on the base,
  the gimbal head floats.
- **Tongue and groove**: tongue = ring `LIP_T` thick outward from the cavity outline,
  `LIP_H` 5 tall on the tray rim, top 0.6 mm (`LEAD`) is 0.4 thinner as a lead-in.
  Lid groove = ring `LIP_T + FIT` thick, `LIP_H + 0.4` deep. Lid wall left outside the
  groove = WALL − LIP_T − FIT (1.2 friction / 1.4 snap).
- **Thumb notches**: two r4 cylinders along x at the lid rim on the ±x end faces.
- **Crush ribs**: two 2 mm wide, `RIB` 0.6 proud, on the ±y long walls of the tray,
  centred on the camera base's x-range (lying base = z 0..23 standing →
  x ≈ -29..-6), floor to Z_SPLIT−1. None on the end walls (only 1.0 clearance there).
- **Snap detent** (`SNAP` > 0, `wedge()` on both ±y walls, `SNAP_L` 20 long centred
  x=0): a trapezoidal bump on the LID's groove wall protruding inward `FIT + SNAP`
  (base z Z_SPLIT+1.6..3.0, tip z +2.1..+2.5, ≈45° ramps both ways) and a matching
  recess in the TONGUE (depth SNAP+0.05, base z +1.45..+3.15, deep face +1.95..+2.65,
  length SNAP_L+0.6). The full-thickness tongue band above the recess (+3.15..+4.4)
  retains the lid; the 1.4 mm lid wall flexes outward to click. Corners/end walls get
  nothing (too stiff; notches live there).
- Lid export: `lid.rotate((180,0,0))` then shifted so min z = 0 (open side up). The
  viewer puts it back with `rotation.x = π; position.z = OUT_H` (lid is symmetric in y).

| Variant | Defaults | Outer (mm) | ~g (PETG) |
|---|---|---|---|
| friction | SNAP 0, WALL 2.4, LIP_T 1.0, FIT 0.2 | 64.8 x 50.0 x 47.8 | 44 |
| snap | SNAP 0.3, WALL 2.8, LIP_T 1.2, FIT 0.2 | 65.6 x 50.8 x 47.8 | 50 |

Why the snap variant is thicker: the recess leaves `LIP_T − (SNAP+0.05)` of tongue
(0.85 at defaults); `make check` refuses < 0.6.

## Checks (`make check`, per variant, plain asserts → PASS lines)

watertight + volume > 0 (tray, lid, camera model); tray ∩ lid in place = 0; the sharp
lying 58 x 41 x 41 box clears tray (incl. ribs) and lid; camera model clears both and
stays inside that box; assembled bbox = OUT within 0.05; tongue fully inside groove
and lid min-z == Z_SPLIT, tray max-z == Z_SPLIT + LIP_H; camera model inside the
standing envelope; **closure**: lid lifted 1 mm interferes by > 0.5 mm³ (snap, ≈7 mm³
at defaults) or by 0 (friction); tongue thickness under the recess ≥ 0.6.
A new feature needs a new check here.

## Technology decisions

- **manifold3d** for solids/booleans (robust, fast, always watertight), **shapely**
  for the rounded-rectangle outlines (`buffer` = fillets), **trimesh** only to write
  binary STL and confirm watertightness, **matplotlib** (Agg) for `preview.png`.
  Pinned in the Dockerfile (manifold3d 3.5.4); bumping pins may re-triangulate
  every STL — regenerate and commit outputs with the bump.
- Convex outer shell via `Manifold.hull_points` of torus samples (no Minkowski
  needed); all other features are extruded CrossSections or hulls of 8 corners.
- `R_IN` must be ≤ ~3.4 × the smaller clearance or a sharp-cornered camera box
  cannot fit a rounded cavity; the check catches it.
- **Viewer** (`HTML` template in case.py): three.js **0.160.0 from the jsdelivr CDN via
  an import map** (works from `file://`, needs internet); the three STLs are embedded
  as base64 and parsed with STLLoader; z-up (`Object3D.DEFAULT_UP`), OrbitControls,
  clipping plane for "Cut at x=0", URL-hash presets `#cut&explode=30&printed&noxray`.
  Light intensities are on the r155+ physical scale. The camera STL is exported
  already lying in case coordinates, so the viewer applies no transform to it.
- **index.html** is generated by `case.py --index <variants>` from each variant's
  `meta.json` (outer dims, grams, STL names) — keep `VARIANT_INFO` text in sync.

## Verifying without a GPU

`make check` is the gate. To see the viewer, screenshot it with headless Chromium in
Docker (SwiftShader WebGL works; keep screenshots outside the repo):

```bash
docker run --rm -v "$PWD/snap":/shot zenika/alpine-chrome --headless --no-sandbox \
  --disable-gpu --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \
  --hide-scrollbars --window-size=1400,900 --virtual-time-budget=15000 \
  --screenshot=/tmp/shot.png "file:///shot/preview.html#cut&explode=12"
```

(Write the screenshot somewhere outside the checkout, e.g. mount a scratch dir on
`/tmp`.) `preview.png`'s fourth panel (rim detail, YZ at x=0) shows the tongue in the
groove and, for snap, the bump seated in the recess — look at it after any rim change.

## Open items / next steps

- No test print yet. After the first print: tune `FIT` (lid tight/loose), `SNAP`
  (hard to close → lower by 0.05; pops open → raise), `CLEAR_W`/`RIB` (rattle/bind).
- Possible additions if asked: magnet closure (needs ~5.6 mm end walls for 4 x 2 mm
  discs), a USB-C cable pocket, engraved lid text (see filtarr for the TextPath approach).
