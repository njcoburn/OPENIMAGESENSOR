# Recreate the GF180 design workstation

## What localhost means here

The browser address `localhost:8080` opens a desktop in Docker. It is not the
storage location of the chip design. The project container mounts this Git
checkout as `/foss/designs`; saving there writes directly to the local checkout.
On this workstation the host path is `/home/njcoburn/code/OPENIMAGESENSOR`.
A colleague can clone elsewhere: the launch scripts calculate the checkout path.

The inspected running container is `openimagesensor-vnc`. Its design mount is the
checkout; no separate project volume needs copying. Xschem uses the repository's
`xschem/xschemrc`. The image supplies the PDK, Magic configuration and tool binaries.
Desktop/browser sessions, VNC credentials, caches and recent-file lists are not
needed to reconstruct the design and are not stored in Git. Save any unsaved GUI
edits to `/foss/designs` before making a later checkpoint.

## Prerequisites and pinned image

Use Linux with Docker Engine, or Windows with Docker Desktop running Linux
containers and WSL integration enabled for your distribution. Run these commands
from Bash in the Linux/WSL checkout. Host requirements: Git, Python 3 and Docker;
no host gdsfactory `.venv` is needed. Allow substantial disk space for the EDA
image and several GB of RAM for DRC; these are not measured minimum requirements.

```sh
git clone https://github.com/njcoburn/OPENIMAGESENSOR.git
cd OPENIMAGESENSOR
docker version
docker pull hpretl/iic-osic-tools@sha256:7371bae55da486f492cc270ea6137c4fcf3b11971de7a4506a74f62be143537a
```

This is the pullable repository digest of the image used for this checkpoint,
not the changing `latest` tag. It contains gdsfactory 9.44.0, KLayout 0.30.9,
Xschem 3.4.8RC, ngspice 46, Magic, Netgen and the GF180MCUD PDK. The flow selects
`PDK=gf180mcuD` and `/foss/pdks/gf180mcuD`. Set `IIC_OSIC_IMAGE` to deliberately
use another image; reverify results after doing so.

## Restore the checkpoint and inspect

On a **clean checkout**, run:

```sh
python3 scripts/restore-checkpoint.py
bash scripts/start-vnc.sh
```

The restore verifies archive and individual file SHA-256 hashes and refuses to
overwrite existing files. Open `docs/overview.html` directly in a browser for the
offline report. Open <http://localhost:8080/vnc.html?autoconnect=true&resize=scale>
for the live desktop; this image's default VNC password is `abc123`. Both the web
port 8080 and native VNC port 5902 bind only to the local host.

To open the schematic or a restored layout:

```sh
docker exec -d -e DISPLAY=:1 -e XAUTHORITY=/headless/.Xauthority openimagesensor-vnc xschem --rcfile /foss/designs/xschem/xschemrc /foss/designs/xschem/array_3x3.sch
docker exec -d -e DISPLAY=:1 -e XAUTHORITY=/headless/.Xauthority openimagesensor-vnc klayout -l /foss/pdks/gf180mcuD/libs.tech/klayout/tech/gf180mcu.lyp /foss/designs/build/size-study/20um/build/array_3x3.gds
```

Use `docker stop openimagesensor-vnc` and `docker start openimagesensor-vnc` to
stop/resume the desktop. The launcher leaves an existing container alone; inspect
its mounts if you reuse that name from another checkout. Avoid concurrently
editing the same design from two desktops. Headless verification does not require
VNC; `scripts/run-tools.sh` starts disposable containers sharing this checkout.

## Rebuild from source

To reproduce all historical data and the current comparison without restoring:

```sh
bash scripts/simulate-cycles.sh
bash scripts/run-tools.sh python3 scripts/check-repeatability.py
bash scripts/simulate-reset-candidate.sh
bash scripts/run-tools.sh python3 scripts/check-reset-candidate.py
python3 scripts/make-array-schematics.py
bash scripts/verify-array.sh
bash scripts/run-size-study.sh
```

The last command also rebuilds the HTML. Screenshot assets are saved observations;
refresh them separately after graphical schematic edits. Generated GDS timestamps
may change file hashes between builds; refreshed verification records the new
artifact. A different hash alone does not establish a geometry difference.

## What is saved

- Source: `layout/`, `xschem/`, `scripts/` and the unchanged original `test.py`.
- Readable evidence: `docs/overview.html`, images and `simulations/*.json`.
- Generated checkpoint: `checkpoints/gf180-3x3-size-study.tar.gz`, with a per-file
  inventory and hashes in `checkpoints/manifest.json`.
- The archive includes baseline and size-variant GDS, extracted/schematic netlists,
  DRC/LVS reports, simulation decks and waveforms required to inspect/rebuild the
  notebook. It does not contain the multi-GB Docker image or browser session.

To refresh the archive after verified work, run `python3 scripts/create-checkpoint.py`
and commit the archive and manifest alongside the matching source/results.
The digest depends on continued availability from the image registry. For an
independent offline backup, use `docker image save` to external storage; do not
put that large image archive in Git. Upstream tool and PDK licenses remain with
their respective projects. The reference lecture PDF is attributed in `docs/README.md`.

## Current limits

All three size variants pass local Magic and full installed KLayout DRC and match
both reference and Xschem in LVS. Their performance comparison uses typical-corner
electrical models and assumed photocurrent density. Extracted wiring/fill
parasitics, calibrated optical response, noise and manufacturing integration remain
future work. Restoring a checkpoint preserves this evidence; it does not rerun or
extend verification.
