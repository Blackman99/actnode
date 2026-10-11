"""Generate site/logo.svg: green interstate-style route shield with '24' (glyphs as paths)."""
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.varLib.instancer import instantiateVariableFont

SRC = "/usr/share/fonts/truetype/sand-box/google/Overpass/Overpass-VariableFont_wght.ttf"


def text_path(txt, wght, size, cx, baseline):
    f = instantiateVariableFont(TTFont(SRC), {"wght": wght})
    gs, cmap, upm = f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm
    s = size / upm
    width = sum(gs[cmap[ord(c)]].width for c in txt) * s
    x = cx - width / 2
    pen = SVGPathPen(gs)
    for c in txt:
        g = gs[cmap[ord(c)]]
        g.draw(TransformPen(pen, (s, 0, 0, -s, x, baseline)))
        x += g.width * s
    return pen.getCommands()


GREEN, WHITE = "#116b46", "#f5f8f0"
# shield: flat-topped crest band, curved sides meeting at a point
OUT = "M256 18 C300 40 360 40 420 18 L478 74 C500 250 430 400 256 494 C82 400 12 250 34 74 L92 18 C152 40 212 40 256 18 Z"
INN = "M256 44 C298 64 356 64 414 44 L452 84 C470 246 408 380 256 464 C104 380 42 246 60 84 L98 44 C156 64 214 64 256 44 Z"
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="actnode">
<path d="{OUT}" fill="{WHITE}"/>
<path d="{INN}" fill="{GREEN}"/>
<path d="M66 128 H446" stroke="{WHITE}" stroke-width="10"/>
<path fill="{WHITE}" d="{text_path("ACT", 800, 64, 256, 112)}"/>
<path fill="{WHITE}" d="{text_path("24", 900, 250, 256, 352)}"/>
</svg>
'''
open("site/logo.svg", "w").write(svg)
fav = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
<path d="{OUT}" fill="{WHITE}"/><path d="{INN}" fill="{GREEN}"/>
<path fill="{WHITE}" d="{text_path("24", 900, 290, 256, 360)}"/>
</svg>
'''
open("site/favicon.svg", "w").write(fav)
