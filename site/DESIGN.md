# actnode design

**Reference object:** a US interstate overhead guide sign on a steel gantry (MUTCD green guide sign, yellow "EXIT ONLY" panel for a lane that ends), the route shield, and a variable message sign. The metaphor: Node 20 is a lane that ends; actnode tells you to move to the Node 24 lanes.

- **Palette:** #116b46 guide green · #f5f8f0 reflective white · #f2b705 exit-only yellow · #2b2d2a asphalt · #1a1a17 legend black on yellow · #8b928c galvanized steel (posts, truss, bolts).
- **Type:** Overpass 400–900 (open-source descendant of Highway Gothic) for everything; Overpass Mono only for commands and the VMS.
- **Texture:** faint hexagonal microprism pattern of retroreflective sheeting; sign construction details (inset white border, rounded corners, bolts). No paper, no shadows, no gradients for colour.
- **Rendering:** flat sign-engineering vectors + CSS perspective road.
- **Layout:** first screen is one full-width gantry sign; the h1 is the sign legend ("Node 24 all lanes"). Below it the page is a highway: a yellow centre line runs down the page, sections are exit signs on posts alternating left and right.
- **Motion:** sign approaches on load, lane lines stream, the yellow Node 20 lane narrows and fades (merge), the VMS flips through real upgrades, the centre line moves with scroll and exit signs come toward you as they enter the viewport. `prefers-reduced-motion`: everything static in its final state.
- **Logo:** green interstate-style route shield, white border, "ACT" over "24" (Overpass, converted to paths by `.github/make_logo.py`).
- OG image and social preview use the same gantry composition (`.github/assets/og.html`, `render.sh`).
