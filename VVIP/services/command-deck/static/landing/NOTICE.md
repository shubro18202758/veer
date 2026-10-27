# static/landing — the landing page's console screenshots

Four screenshots of the Veer console, shown on `/welcome` (the landing page) and captioned there
"Console screenshot · exercise data":

| File | Screen |
|---|---|
| `console-decide-{800,1600}.webp` | Decide — a stolen-vehicle decision waiting for a named officer (the hero window) |
| `console-map-{800,1600}.webp` | Map — the photoreal 3D city ("Photoreal 3D city from Google, via Cesium ion · not a live image") |
| `console-home-{800,1600}.webp` | Home — the decision that needs an officer now and the city pulse |
| `console-plan-{800,1600}.webp` | Plan a movement — start, destination and protection class beside a satellite map |

How they were made: a development deck of this tree, backed by a sandbox copy of the stack running **exercise
(emulated) data** — the demo stolen vehicle, its FIR and its camera reads are emulated and labelled so on screen. No
duty officer was named, so every registration mark is **masked** (`GJ27EM•••1`) and "Plates hidden" shows in the top
bar. The browser clock of the capture was set back so the demo decision's waiting time reads as a fresh one; nothing
else was edited. Images were resized and encoded to WebP only.

Third-party content visible inside them keeps its own terms and is credited on screen: satellite and aerial imagery
(© Microsoft Corporation, © Maxar, via Cesium ion), Google Photorealistic 3D Tiles via Cesium ion, map data
© OpenStreetMap contributors (ODbL 1.0), the airport reference photo on the Plan screen (Rupturestriker, CC BY 4.0,
Wikimedia Commons — `static/photos/NOTICE.md`), and the attribution marks the map draws (Cesium ion, Google), which
belong to their owners. The vehicle and convoy pictures inside them are Veer's own illustrations.
