# OBSBOT Tiny 3 Lite case — every command runs inside Docker (python:3.12-slim);
# nothing is installed on the host. Requires only Docker and make.
#
#   make              # STLs + geometry checks + previews + index.html, both variants
#   make stl          # <variant>/tiny3lite_case_tray.stl, _case_lid.stl, _camera.stl
#   make check        # geometry self-checks (fit, interference, watertight, detent)
#   make preview      # <variant>/preview.png + preview.html (three.js viewer)
#   make index        # index.html (GitHub Pages landing page)
#   make build        # (re)build the Docker image only
#   make clean        # delete generated outputs
#
#   make VARIANTS=snap SNAP=0.25      # one variant, tuned (any parameter in PARAMS)

IMAGE    ?= obsbot-tiny3-lite-case
OUT      ?= .
VARIANTS ?= friction snap
PARAMS = CAM_W CAM_D CAM_H CLEAR_L CLEAR_W CLEAR_H WALL FLOOR R_IN R_EDGE TRAY LIP_H LIP_T FIT NOTCH_R RIB SNAP SNAP_L
RUN = docker run --rm -v "$(CURDIR)":/work -w /work $(foreach v,$(PARAMS),-e $(v)) $(IMAGE) python case.py

.PHONY: all build stl check preview index clean
all: stl check preview index

build:
	docker build -t $(IMAGE) .

stl: build
	for v in $(VARIANTS); do $(RUN) --variant $$v --out $(OUT)/$$v || exit 1; done

check: build
	for v in $(VARIANTS); do $(RUN) --variant $$v --out $(OUT)/$$v --check || exit 1; done

preview: build
	for v in $(VARIANTS); do $(RUN) --variant $$v --out $(OUT)/$$v --preview || exit 1; done

index: build
	$(RUN) --out $(OUT) --index $(VARIANTS)

clean:
	rm -rf $(addprefix $(OUT)/,$(VARIANTS)) $(OUT)/index.html
