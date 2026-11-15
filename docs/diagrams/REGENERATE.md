# Regenerating the architecture figures

The published figures are generated from the Python scripts in this folder:

- `architecture.py`  -> `architecture.svg` / `architecture.png` and
  `architecture-explained.svg` / `architecture-explained.png`
- `architecture-v2-detailed.py` -> `architecture-v2-detailed.svg` / `.png`

Each script hand-builds the SVG and then rasterises the PNG with headless
Chrome (`--screenshot`). Regenerating the **PNG** therefore needs a local
toolchain that the offline CI sandbox does not have:

- `lxml` and `Pillow` (SVG assembly and font metrics), and
- headless `google-chrome` / `chromium` for the PNG screenshot.

## When the KPI labels / date changed (15 November 2026)

The KPI scorecard card now shows the **measured** values from the committed run
`eval/results/demo-2026-11-15T111652Z.json` (completeness 0.762, uniqueness
0.875, consistency 0.714, currentness 0.40, key match 0.857), labelled
"measured, run demo-2026-11-15T111652Z", and the footer date is 15 November
2026. The generators and the `.svg` files in this folder were updated together
so they stay in step.

The committed `.png` files were **not** regenerated in the sandbox (no browser
or SVG rasteriser, no network). To refresh them on a machine that has the
toolchain:

```
cd docs/diagrams
python3 architecture.py              # writes architecture.svg/.png + explained
python3 architecture-v2-detailed.py  # writes architecture-v2-detailed.svg/.png
```

Then commit the regenerated PNG/SVG. Do **not** replace these icon figures with
a box-only Mermaid diagram.
