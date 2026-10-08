# OBSBOT Tiny 3 Lite carry case

A 3D-printable two-part carry case for the **OBSBOT Tiny 3 Lite** webcam — there was
none. The camera lies flat in a shallow tray under a deep lid, so you pick it up by
the body and never by the gimbal head. Two closure variants, everything generated
from one parametric Python script, built entirely inside Docker.

**Browse the interactive 3D previews and download STLs at
[ardakilic.github.io/obsbot-tiny3-lite-case](https://ardakilic.github.io/obsbot-tiny3-lite-case/).**

![Snap variant: tray, lid, section with the camera, rim detail](snap/preview.png)
*Snap variant — tray and lid as printed, assembled section with the (approximate)
camera model, and the rim detail showing the detent seated in the tongue.*

## The two variants

| | Friction fit — [`friction/`](friction/) | Snap detent — [`snap/`](snap/) |
|---|---|---|
| Closure | Slip-fit tongue and groove, 0.2 mm clearance | Same tongue and groove plus a 20 mm ridge inside each long lid wall that clicks into a recess in the tongue |
| Stays closed in a bag? | Not guaranteed — friction only | Yes — lifting the lid needs the lid wall to flex over the detent |
| Hardware | none | none |
| Walls / tongue | 2.4 / 1.0 mm | 2.8 / 1.2 mm (room for the recess) |
| Outer size | 64.8 × 50.0 × 47.8 mm | 65.6 × 50.8 × 47.8 mm |
| Filament (PETG) | ≈ 44 g | ≈ 50 g |
| Preview | [friction/preview.html](https://ardakilic.github.io/obsbot-tiny3-lite-case/friction/preview.html) | [snap/preview.html](https://ardakilic.github.io/obsbot-tiny3-lite-case/snap/preview.html) |

Each folder holds `tiny3lite_case_tray.stl`, `tiny3lite_case_lid.stl`, a render sheet
`preview.png`, the interactive `preview.html`, and `tiny3lite_camera.stl` — an
approximate camera model used only for visualisation and the fit checks (don't print it).

## How it is designed

- **Camera lying flat, lens up.** The cavity is 60 × 45.2 × 43 mm: the 60 × 45.2
  pocket is taken from the community
  [Gridfinity organizer](https://www.printables.com/model/1620707-obsbot-tiny-3-lite-webcam-gridfinity-organizer)
  for this camera, whose author test-fitted a real unit (1 mm clearance per end,
  2.1 mm per side); 1 mm above and below the camera's 41 mm.
- **Shallow tray, deep lid.** The tray holds only the bottom 15 mm of the camera;
  26 mm of the body stands proud when the lid is off, so it lifts out by the base.
  No finger scoops are needed, so the closed case has no holes. The weight rests on
  the base; the gimbal head floats with clearance.
- **Tongue and groove** with a lead-in on the tongue tip, two thumb notches on the
  lid's end faces, two crush ribs under the camera base against rattle, rounded
  edges and corners all round.
- **Snap detent** (snap variant): a trapezoidal ridge on the lid's groove wall with
  ~45° ramps both ways, seated in a matching recess in the tongue; the full-thickness
  tongue band above the recess retains the lid.
- Both parts print open side up with no supports.

## Printing

0.2 mm layers, 3 or more perimeters, ~15 % infill, PETG (preferred, the snap flexes
better) or PLA, no supports, both parts as exported (open side up, flat on the bed).

Drop the camera in with the base toward the ribs (the −x end in the viewer), lens
up. Fit tuning after a test print — change parameters, never the geometry:

| Symptom | Fix |
|---|---|
| Lid too tight / too loose (friction) | `make VARIANTS=friction FIT=0.25` / `FIT=0.15` |
| Snap too hard to close | lower in 0.05 steps: `make VARIANTS=snap SNAP=0.25`, or shorten `SNAP_L` |
| Snap pops open | raise `SNAP` |
| Camera rattles / binds | `CLEAR_W` or `RIB` |

## Building it yourself

Requires only Docker and `make`; nothing is installed on the host.

```sh
make                          # STLs + geometry checks + previews + index.html, both variants
make stl                      # <variant>/tiny3lite_case_tray.stl, _case_lid.stl, _camera.stl
make check                    # self-checks: watertight, fit, no interference, detent engages
make preview                  # <variant>/preview.png + preview.html
make VARIANTS=snap SNAP=0.25  # one variant with overrides (any parameter below)
make clean
open snap/preview.html        # viewer: Tray / Lid / Camera / X-ray / Cut toggles, Explode slider,
                              # "As printed" layout; needs internet for the three.js CDN
```

`make check` builds every part in memory and asserts: watertight meshes, tray and lid
do not interfere when closed, a sharp 58 × 41 × 41 block *and* the camera model clear
the tray (ribs included) and the lid, assembled size equals the spec, the tongue sits
fully inside the groove, and — the closure test — lifting the lid 1 mm interferes by
≈7 mm³ on the snap variant and by exactly nothing on the friction variant.

### Parameters (mm, environment variables)

| Name | Default | Meaning |
|---|---|---|
| CAM_W, CAM_D, CAM_H | 41, 41, 58 | Camera bounding box, standing (width, depth, height) |
| CLEAR_L | 1.0 | Clearance per end along the camera's 58 mm length (cavity 60) |
| CLEAR_W | 2.1 | Clearance per side across the 41 mm width (cavity 45.2) |
| CLEAR_H | 1.0 | Clearance above and below the lying camera (cavity 43 tall) |
| WALL | 2.4 (snap 2.8) | Side wall thickness |
| FLOOR | 2.4 | Floor of the tray / ceiling of the lid |
| R_IN | 4 | Cavity vertical corner radius; outer radius = R_IN + WALL |
| R_EDGE | 3 | Rounding of the outer top and bottom edges |
| TRAY | 15 | Cavity height held by the tray; the lid holds the rest |
| LIP_H, LIP_T | 5, 1.0 (snap 1.2) | Tongue height and thickness (0.6 mm lead-in at the tip) |
| FIT | 0.2 | Radial clearance between tongue and groove |
| NOTCH_R | 4 | Thumb notch radius on the lid's end faces |
| RIB | 0.6 | Height of the two anti-rattle ribs (0 disables) |
| SNAP | 0 (snap 0.3) | Detent interference depth; 0 = no detent |
| SNAP_L | 20 | Detent length along each long wall |

## Camera dimensions (researched)

**41 × 41 × 58 mm (W × D × H), 73 g.** OBSBOT's own
[comparison table](https://www.obsbot.com/comparison?from=tiny-3-series) and every
retailer sheet agree ([JB Hi-Fi](https://www.jbhifi.com.au/products/obsbot-tiny-3-lite-ai-powered-ptz-4k-webcam)
labels the axes W × H × D = 41 × 58 × 41; [Thomann](https://www.thomann.de/be/obsbot_tiny_3_lite.htm);
[Micro Center](https://microcenter.com/quickView/705519/obsbot-tiny-3-lite-ai-powered-4k-ptz-webcam)).
The regular Tiny 3 is 37 × 37 × 49 mm / 63 g with a detachable magnetic mount, so its
files don't apply.

Shape (official photos and the user manual): square base with rounded corners, a
fold-flat stand hinged under the rear of the base, UNC 1/4-20 socket in the bottom,
USB-C on the back, round pan turntable with LED ring, an L-arm carrying the rounded
lens head with a red ring; the lens tilts down for sleep. Folded, it is the
41 × 41 × 58 box the case is designed around. The camera model in the previews is
eyeballed from those photos within that box.

## Project layout

```
case.py            the generator: parameters, camera model, case geometry, checks, previews, index page
Makefile           every target is a docker run; Dockerfile pins the image and wheels
friction/ snap/    generated outputs (committed, so GitHub Pages and the STL links just work)
index.html         generated Pages landing page
CLAUDE.md          design notes and rules for AI agents working on the repo (AGENTS.md points to it)
```

## License

Code: [MIT](LICENSE). Models and images: [CC BY 4.0](LICENSE-MODELS). The Gridfinity
organizer used as the fit reference is not included; see its
[Printables page](https://www.printables.com/model/1620707-obsbot-tiny-3-lite-webcam-gridfinity-organizer).
OBSBOT and Tiny 3 Lite are trademarks of their owner; this is an independent accessory.
