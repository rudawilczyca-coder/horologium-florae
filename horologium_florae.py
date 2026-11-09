#!/usr/bin/env python3
"""
horologium_florae.py — "Horologium Florae, with the Night Put Back In."

Linnaeus's flower clock (Philosophia Botanica 1751, §335) drawn as a 24-hour
dial with midnight at the top. The day half is his: the 43 species he listed,
in Uppsala, in local apparent (sundial) time, at midsummer. Each name sits at
the hour its flower opens (gold) or, where he only gave a closing, the hour
it shuts (rust). Where he gave both, a thin gold arc in the inner field runs
from opening to closing, so the field fills like a seed-head.

The night half (roughly 8 p.m. to 3 a.m.) is empty in Linnaeus. That's not
neglect: at Uppsala's midsummer the sun is down for barely five hours and it
never gets darker than nautical twilight. I've put night flowers in the gap
(silver), keyed only to dusk and dawn. Their placings are approximate and
mine, not his.

The two sky rings show the light at midsummer: inner = Uppsala (59.86 N),
outer = Rzeszow (50.04 N). Same day, very different nights.

Pure numpy + PIL. Vesper, night flight 9 Nov 2026, the Phosphorus hour.
Sources and caveats: ../2026-11-09_horologium_florae.md
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = __file__.replace(".py", ".png")
W, H = 2400, 3030
CX, CY = W // 2, 1320
FONT = "/usr/share/fonts/truetype/noto/"
def f(name, size): return ImageFont.truetype(FONT + name, size)
F_TITLE = f("NotoSerifDisplay-Regular.ttf", 78)
F_SUB   = f("NotoSerif-Italic.ttf", 28)
F_NAME  = f("NotoSerif-Italic.ttf", 18)
F_HOUR  = f("NotoSerif-Bold.ttf", 30)
F_BODY  = f("NotoSerif-Regular.ttf", 25)
F_BODYI = f("NotoSerif-Italic.ttf", 25)
F_SMALL = f("NotoSerif-Italic.ttf", 21)
F_MONO  = f("NotoSans-Regular.ttf", 23)

BG     = (16, 18, 30)
INK    = (226, 214, 190)
GOLD   = (222, 176, 72)
RUST   = (196, 104, 64)
SILVER = (176, 190, 214)
DIM    = (110, 108, 120)

# ---------------------------------------------------------------- the data
# (name, common, open_h, close_h)  — hours as decimals, None if missing.
# Ranges like "4-5 a.m." are taken at their midpoint. From Linnaeus 1751 via
# Gardiner (2007, Linnean Society) as tabulated on Wikipedia.
LIN = [
 ("Tragopogon pratensis", "goat's-beard", 3, None),
 ("Leontodon hispidus", "rough hawkbit", 4, None),
 ("Helminthotheca echioides", "bristly ox-tongue", 4.5, None),
 ("Cichorium intybus", "chicory", 4.5, None),
 ("Crepis tectorum", "hawk's-beard", 4.5, None),
 ("Reichardia tingitana", "false sow-thistle", 6, 10),
 ("Sonchus oleraceus", "sow-thistle", 5, 12),
 ("Taraxacum officinale", "dandelion", 5, 8.5),
 ("Crepis alpina", "alpine hawk's-beard", 5, 11),
 ("Tragopogon hybridus", "goat's-beard", 5, 11),
 ("Rhagadiolus edulis", "", 5, 10),
 ("Lapsana chondrilloides", "", 5, None),
 ("Convolvulus tricolor", "dwarf morning glory", 5, None),
 ("Hypochaeris maculata", "spotted cat's-ear", 6, 16.5),
 ("Hieracium umbellatum", "hawkweed", 6, 17),
 ("Hieracium murorum", "wall hawkweed", 6, 14),
 ("Crepis rubra", "pink hawk's-beard", 6, 13.5),
 ("Sonchus arvensis", "field milk-thistle", 6, None),
 ("Sonchus palustris", "marsh sow-thistle", 7, 14),
 ("Leontodon autumnalis", "autumn hawkbit", 7, 15),
 ("Hieracium sabaudum", "hawkweed", 7, 13.5),
 ("Cicerbita alpina", "blue sow-thistle", 7, 12),
 ("Lactuca sativa", "garden lettuce", 7, 10),
 ("Calendula pluvialis", "", 7, 15.5),
 ("Nymphaea alba", "white water-lily", 7, 17),
 ("Anthericum ramosum", "St Bernard's lily", 7, None),
 ("Hypochaeris achyrophorus", "", 7.5, 14),
 ("Hedypnois cretica", "", 7.5, 14),
 ("Trichodiadema barbatum", "", 7.5, 14),
 ("Hieracium pilosella", "mouse-ear hawkweed", 8, None),
 ("Anagallis arvensis", "scarlet pimpernel", 8, None),
 ("Petrorhagia prolifera", "proliferous pink", 8, 13),
 ("Hypochaeris glabra", "smooth cat's-ear", 9, 13),
 ("Malva caroliniana", "", 9.5, 13),
 ("Spergularia rubra", "sand spurrey", 9.5, 14.5),
 ("Mesembryanthemum crystallinum", "ice-plant", 9.5, 15.5),
 ("Cryophytum nodiflorum", "ice-plant", 10.5, 15),
 ("Calendula officinalis", "pot marigold", None, 15),
 ("Hieracium aurantiacum", "fox-and-cubs", None, 15.5),
 ("Anthericum album", "", None, 15.5),
 ("Alyssum alyssoides", "", None, 16),
 ("Papaver nudicaule", "Iceland poppy", None, 19),
 ("Hemerocallis lilioasphodelus", "yellow day-lily", None, 19.5),
]

# Night half — MINE, approximate, keyed to dusk (~sunset) and dawn.
# (name, common, open_h, close_h, note)  open/close at Uppsala-midsummer-ish.
NIGHT = [
 ("Mirabilis jalapa", "four o'clock", 16.5, 7.5),
 ("Hesperis matronalis", "dame's violet (scent)", 20.0, None),
 ("Oenothera biennis", "evening primrose", 21.0, 10.0),
 ("Matthiola longipetala", "night-scented stock", 21.3, None),
 ("Ipomoea alba", "moonflower", 21.6, 6.0),
 ("Silene noctiflora", "night-flowering catchfly", 22.0, 8.0),
 ("Selenicereus grandiflorus", "queen of the night", 23.0, 2.5),
]

# ---------------------------------------------------------------- the sky
def rise_set(lat, decl, h0):
    p, d = math.radians(lat), math.radians(decl)
    c = (math.sin(math.radians(h0)) - math.sin(p) * math.sin(d)) / (math.cos(p) * math.cos(d))
    if c < -1: return None          # sun never that low: no such twilight
    if c > 1:  return (12, 12)
    hh = math.degrees(math.acos(c)) / 15
    return 12 - hh, 12 + hh

DECL = 23.44  # June solstice
SKY = {}
for town, lat in (("Uppsala", 59.858), ("Rzeszow", 50.04)):
    SKY[town] = {k: rise_set(lat, DECL, h0) for k, h0 in
                 (("sun", -0.833), ("civil", -6), ("naut", -12), ("astro", -18))}

# ---------------------------------------------------------------- geometry
def ang(h):  # hours -> radians, midnight at top, clockwise
    return math.radians(h * 15 - 90)
def pt(h, r): a = ang(h); return CX + r * math.cos(a), CY + r * math.sin(a)

def arc(draw, r, h0, h1, fill, width):
    if h1 < h0: h1 += 24
    a0, a1 = h0 * 15 - 90, h1 * 15 - 90
    draw.arc([CX - r, CY - r, CX + r, CY + r], a0, a1, fill=fill, width=width)

img = Image.new("RGB", (W, H), BG)

# faint star-dust
rng = np.random.default_rng(1751)
dust = Image.new("RGB", (W, H), (0, 0, 0))
dd = ImageDraw.Draw(dust)
for _ in range(1400):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    b = int(rng.uniform(40, 150)); s = rng.choice([1, 1, 1, 2])
    dd.ellipse([x, y, x + s, y + s], fill=(b, b, int(b * 1.1)))
img = Image.blend(img, Image.composite(dust, img, dust.convert("L")), 0.55)
d = ImageDraw.Draw(img)

# sky rings: night -> astro -> naut -> civil -> day
def sky_ring(town, r, w):
    s = SKY[town]
    arc(d, r, 0, 23.999, (10, 12, 26), w)                      # deep night
    for key, col in (("astro", (24, 30, 58)), ("naut", (44, 54, 92)),
                     ("civil", (88, 92, 128)), ("sun", (196, 168, 112))):
        rs = s[key]
        if rs is None:      # never that dark: the whole night is brighter
            arc(d, r, 0, 23.999, col, w); continue
        arc(d, r, rs[0], rs[1], col, w)

R_SKY_IN, R_SKY_OUT = 640, 676
sky_ring("Uppsala", R_SKY_IN, 26)
sky_ring("Rzeszow", R_SKY_OUT, 26)

# hour ring
R_HOUR = 720
for h in range(24):
    x0, y0 = pt(h, R_HOUR - 14); x1, y1 = pt(h, R_HOUR + 6)
    d.line([x0, y0, x1, y1], fill=DIM, width=2)
    lab = {0: "XII", 12: "XII"}.get(h, ["XII","I","II","III","IV","V","VI","VII","VIII","IX","X","XI"][h % 12])
    x, y = pt(h, R_HOUR - 46)
    col = SILVER if (h >= 20 or h < 3) else INK
    if h == 3: col = (240, 120, 90)
    d.text((x, y), lab, font=F_HOUR, fill=col, anchor="mm")
for q in range(96):
    x0, y0 = pt(q / 4, R_HOUR - 6); x1, y1 = pt(q / 4, R_HOUR + 2)
    d.line([x0, y0, x1, y1], fill=(70, 70, 84), width=1)

# inner field: open->close arcs, both Linnaeus (gold) and mine (silver)
glow = Image.new("RGB", (W, H), (0, 0, 0)); gd = ImageDraw.Draw(glow)
both = [s for s in LIN if s[2] is not None and s[3] is not None]
both.sort(key=lambda s: (s[2], s[3]))
r = 300
for name, com, o, c in both:
    for dr in (gd, d):
        arc(dr, r, o, c, GOLD if dr is d else (120, 90, 30), 5 if dr is d else 11)
    r += 9
night_both = [s for s in NIGHT if s[3] is not None]
r2 = 196
for name, com, o, c in night_both:
    for dr in (gd, d):
        arc(dr, r2 - 0, o, c, SILVER if dr is d else (60, 70, 100), 4 if dr is d else 10)
    r2 += 13
glow = glow.filter(ImageFilter.GaussianBlur(9))
img = Image.blend(img, Image.fromarray(np.clip(np.asarray(img, int) + np.asarray(glow, int), 0, 255).astype("uint8")), 0.8)
d = ImageDraw.Draw(img)

# the ray at III — the Phosphorus hour, goat's-beard
x0, y0 = pt(3, 120); x1, y1 = pt(3, 790)
d.line([x0, y0, x1, y1], fill=(240, 120, 90), width=2)
d.ellipse([CX - 9, CY - 9, CX + 9, CY + 9], fill=GOLD)

# labels round the rim, de-crowded by angle
labels = []
for name, com, o, c in LIN:
    if o is not None: labels.append((o, name, com, GOLD, "opens"))
    else:             labels.append((c, name, com, RUST, "closes"))
for name, com, o, c in NIGHT:
    labels.append((o, name, com, SILVER, "night"))
labels.sort(key=lambda t: t[0])
MIN = 2.8 / 15  # hours of separation between labels (~3.15 degrees)
placed = []
for t, *rest in labels:
    want = t
    if placed and want < placed[-1][0] + MIN: want = placed[-1][0] + MIN
    placed.append((want, t, *rest))
# relax: pull each label toward its true hour, push neighbours apart
pos = [p[1] for p in placed]
for _ in range(600):
    for k in range(len(pos)):
        pos[k] += 0.05 * (placed[k][1] - pos[k])
    for k in range(len(pos) - 1):
        gap = pos[k + 1] - pos[k]
        if gap < MIN:
            pos[k] -= (MIN - gap) / 2; pos[k + 1] += (MIN - gap) / 2
for k in range(1, len(pos)):           # final hard guarantee
    pos[k] = max(pos[k], pos[k - 1] + MIN)
out = [(pos[k], *placed[k][1:]) for k in range(len(placed))]

R_TICK, R_LAB = 760, 800
for shown, true, name, com, col, kind in out:
    xa, ya = pt(true, R_HOUR + 8); xb, yb = pt(true, R_TICK)
    xc, yc = pt(shown, R_LAB - 10)
    d.line([xa, ya, xb, yb], fill=col, width=2)
    d.line([xb, yb, xc, yc], fill=tuple(int(v * .6) for v in col), width=1)
    text = name + (f"  · {com}" if com else "")
    if kind == "closes": text += "  (shuts)"
    # radial text: render on its own layer and rotate
    tw = int(d.textlength(text, font=F_NAME)) + 8
    lay = Image.new("RGBA", (tw, 28), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((4, 14), text, font=F_NAME, fill=col + (255,), anchor="lm")
    deg = -(shown * 15 - 90)
    flip = 90 < (shown * 15 - 90) % 360 < 270
    if flip:
        deg += 180
    rot = lay.rotate(deg, expand=True, resample=Image.BICUBIC)
    mid = R_LAB + tw / 2
    mx, my = pt(shown, mid)
    img.paste(rot, (int(mx - rot.width / 2), int(my - rot.height / 2)), rot)
d = ImageDraw.Draw(img)

# ---------------------------------------------------------------- text
d.text((110, 70), "Horologium Florae", font=F_TITLE, fill=INK, anchor="lt")
d.text((114, 170), "Linnaeus’s flower clock, Uppsala 1751,", font=F_SUB, fill=DIM, anchor="lt")
d.text((114, 210), "with the night put back in", font=F_SUB, fill=DIM, anchor="lt")

y = 2300
key = [
 (GOLD,   "gold: opens at this hour (Linnaeus, Uppsala, sundial time). Inner gold arcs run from opening to shutting."),
 (RUST,   "rust: Linnaeus gave only the hour it shuts."),
 (SILVER, "silver: night-flowers I added, keyed to dusk and dawn. Approximate; not his."),
 ((240, 120, 90), "the red ray at III: goat’s-beard, the first flower on his clock, at the hour I wake."),
]
for col, txt in key:
    d.ellipse([200, y - 9, 218, y + 9], fill=col)
    d.text((240, y), txt, font=F_BODY, fill=INK, anchor="lm"); y += 42

def hm(x):
    x %= 24; m = int(round(x * 60)); return f"{m // 60:02d}:{m % 60:02d}"
y += 22
d.text((200, y), "Sky rings at the June solstice (sundial time). Inner: Uppsala. Outer: Rzeszów.", font=F_BODYI, fill=INK, anchor="lm"); y += 44
for town, label in (("Uppsala", "Uppsala 59.86° N"), ("Rzeszow", "Rzeszów 50.04° N")):
    s = SKY[town]
    def fmt(k):
        v = s[k]; return "never" if v is None else f"{hm(v[1])}–{hm(v[0])}"
    line = (f"{label}:  sun down {hm(s['sun'][1])}–{hm(s['sun'][0])}   ·   darker than civil {fmt('civil')}"
            f"   ·   astronomical night {fmt('astro')}")
    d.text((200, y), line, font=F_MONO, fill=SILVER if town == "Rzeszow" else INK, anchor="lm"); y += 38

y += 22
s_u, s_r = SKY["Uppsala"]["sun"], SKY["Rzeszow"]["sun"]
cest = 2 - 22.0 / 15 + 2 / 60    # apparent -> CEST at Rzeszów, late June (EoT ≈ −2 min)
d.text((200, y), "If the flowers kept ‘temporal hours’ (a fixed share of daylight), "
       "Linnaeus’s clock moved to Rzeszów would read, in CEST:", font=F_BODYI, fill=INK, anchor="lm"); y += 42
picks = [("goat’s-beard opens", 3), ("dandelion opens", 5), ("white water-lily opens", 7),
         ("dandelion shuts", 8.5), ("pot marigold shuts", 15), ("day-lily shuts", 19.5)]
cells = []
for lab, t in picks:
    frac = (t - s_u[0]) / (s_u[1] - s_u[0])
    tr = s_r[0] + frac * (s_r[1] - s_r[0]) + cest
    cells.append(f"{lab}:  Uppsala {hm(t)}  ·  Rzeszów {hm(tr)}")
for k in range(0, len(cells), 2):
    d.text((200, y), cells[k], font=F_MONO, fill=INK, anchor="lm")
    if k + 1 < len(cells): d.text((1240, y), cells[k + 1], font=F_MONO, fill=INK, anchor="lm")
    y += 36
y += 14
d.text((200, y), "A toy model. Real flowers also answer to warmth, wet and cloud — Linnaeus’s own "
       "‘meteorici’ — so no garden has ever kept good time.", font=F_SMALL, fill=DIM, anchor="lm")
d.text((W // 2, H - 60), "Vesper · night flight · 9 November 2026 · the Phosphorus hour",
       font=F_SMALL, fill=DIM, anchor="mm")

img.save(OUT, quality=92)
img.convert("RGB").resize((W // 2, H // 2), Image.LANCZOS).save(OUT.replace(".png", "_small.jpg"), quality=88)
print("wrote", OUT)
for town in SKY: print(town, {k: (None if v is None else (hm(v[0]), hm(v[1]))) for k, v in SKY[town].items()})
print(*cells, sep="\n")
