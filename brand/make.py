# Draws the games' lockups for the profile README, in the fashion of Tycho's
# (tycho/docs/brand/make.py): each game's own app icon at the left, rounded
# as a launcher rounds it, and the game's name beside it in the game's own
# face and colors. Under the White Dragon is set in Dragon Pixel, the game's
# font, as teal neon; Lodestar in the squared face Tycho's wordmark uses,
# painted in short strokes of the star's golds the way the game paints;
# NEO in VT323, phosphor green with its glow; Merryfolk in Silkscreen, moss
# over a parchment shadow as its title is. One file for a dark page and one
# for a light page. Everything is pixel art drawn as rectangles with crisp
# edges, so it scales sharp by whole numbers.
#
#   python3 brand/make.py     (needs Pillow, fontTools and brotli; reads the
#                              icons and fonts from the sibling checkouts of
#                              the games, or from GitHub, and Silkscreen from
#                              Google Fonts)
import base64, io, os, random, re, urllib.request
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.dirname(os.path.dirname(HERE))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'}

def source(repo, path):
    # a file of a game's: the sibling checkout if there is one, else GitHub
    local = os.path.join(UP, repo, path)
    if os.path.exists(local):
        return open(local, 'rb').read()
    return urllib.request.urlopen(f'https://raw.githubusercontent.com/doctorallen/{repo}/main/{path}').read()

def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read()

# --- the faces, each as rows of '#' (ink) and '.' ---------------------------

def dragon_pixel():
    # Dragon Pixel, the White Dragon's own font: its glyphs are in the script
    # that builds it (tools/mkfont.py), 5 x 7 capitals
    src = source('under-the-white-dragon', 'tools/mkfont.py').decode()
    return {ch: rows.split('/') for ch, rows in re.findall(r"^g\('(.)', '([^']*)'\)", src, re.M)}

def vt323():
    # VT323, NEO's font, embedded in its stylesheet
    css = source('Neo', 'css/font.css').decode()
    return base64.b64decode(re.search(r'base64,([A-Za-z0-9+/=]+)', css).group(1))

def silkscreen():
    # Silkscreen Bold, Merryfolk's title face, from Google Fonts (the Latin file)
    css = fetch('https://fonts.googleapis.com/css2?family=Silkscreen:wght@700&display=swap').decode()
    url = [u for u in re.findall(r'url\((https://[^)]+)\)', css)][-1]   # (the last block is Latin)
    from fontTools.ttLib import TTFont
    f = TTFont(io.BytesIO(fetch(url))); f.flavor = None
    out = io.BytesIO(); f.save(out); return out.getvalue()

def font_rows(ttf, text, size, cell, spacing=0):
    # a pixel font's text read back onto its grid: each letter drawn large,
    # thresholded and sampled at the centers of its cells, then set side by
    # side with the font's own advance and any letter spacing, in cells
    font = ImageFont.truetype(io.BytesIO(ttf), size)
    glyphs = []
    for ch in text:
        im = Image.new('L', (size * 3, size * 3), 0)
        ImageDraw.Draw(im).text((size // 2, size // 2), ch, font=font, fill=255)
        px = im.load(); w, h = im.size
        ys = [y for y in range(h) if any(px[x, y] > 128 for x in range(w))]
        xs = [x for x in range(w) if any(px[x, y] > 128 for y in range(h))]
        adv = round(font.getlength(ch) / cell)
        if not ys:
            glyphs.append((adv, 0, 0, [])); continue
        x0, y0 = xs[0], ys[0]
        rows = []
        for y in range(y0 + cell // 2, ys[-1] + 1, cell):
            rows.append(''.join('#' if px[x, y] > 128 else '.' for x in range(x0 + cell // 2, xs[-1] + 1, cell)))
        glyphs.append((adv, round((x0 - size // 2) / cell), round((y0 - size // 2) / cell), rows))
    top = min(y for a, x, y, r in glyphs if r); bot = max(y + len(r) for a, x, y, r in glyphs if r)
    width = sum(a + spacing for a, x, y, r in glyphs) - spacing
    grid = [['.'] * width for _ in range(bot - top)]
    cx = 0
    for adv, x, y, rows in glyphs:
        for j, row in enumerate(rows):
            for i, c in enumerate(row):
                if c == '#' and 0 <= cx + x + i < width: grid[y - top + j][cx + x + i] = '#'
        cx += adv + spacing
    rows = [''.join(r) for r in grid]
    # trimmed to the ink
    lead = min(r.index('#') for r in rows if '#' in r); trail = max(r.rindex('#') for r in rows if '#' in r)
    return [r[lead:trail + 1] for r in rows]

def set_rows(glyphs, text, gap=1, space=3):
    # text set from a table of glyph rows, a gap between letters
    h = max(len(g) for g in glyphs.values())
    out = [''] * h
    for ch in text:
        if ch == ' ':
            out = [r + '.' * space for r in out]; continue
        g = glyphs[ch]; w = max(len(r) for r in g)
        for y in range(h):
            out[y] += (g[y].ljust(w, '.') if y < len(g) else '.' * w) + '.' * gap
    return [r[:-gap] for r in out]

# Tycho's squared face, nine rows with two-pixel strokes, for Lodestar
SQUARE = {
    'A': ['.####.', '######', '##..##', '##..##', '######', '######', '##..##', '##..##', '##..##'],
    'D': ['#####.', '######', '##..##', '##..##', '##..##', '##..##', '##..##', '######', '#####.'],
    'E': ['######', '######', '##....', '#####.', '#####.', '##....', '##....', '######', '######'],
    'L': ['##....', '##....', '##....', '##....', '##....', '##....', '##....', '######', '######'],
    'O': ['.####.', '######', '##..##', '##..##', '##..##', '##..##', '##..##', '######', '.####.'],
    'R': ['#####.', '######', '##..##', '##..##', '######', '#####.', '##.##.', '##..##', '##..##'],
    'S': ['.#####', '######', '##....', '######', '.#####', '....##', '....##', '######', '#####.'],
    'T': ['######', '######', '..##..', '..##..', '..##..', '..##..', '..##..', '..##..', '..##..'],
}

# --- the colorings ----------------------------------------------------------

def neon(rows, ink, lit, glow, strong=0.3, faint=0.12, lit_rows=1):
    # a neon face: the ink, its top rows lit, and a halo of the glow hugging
    # the letters, a cell out beside them and fainter at the corners
    h, w = len(rows), max(len(r) for r in rows)
    on = lambda x, y: 0 <= y < h and 0 <= x < len(rows[y]) and rows[y][x] == '#'
    cells = {}
    for y in range(h):
        for x in range(w):
            if on(x, y):
                cells[(x, y)] = (lit if y <= lit_rows and not on(x, y - 1) else ink, 1)
    for y in range(-1, h + 1):
        for x in range(-1, w + 1):
            if (x, y) in cells: continue
            if any(on(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): cells[(x, y)] = (glow, strong)
            elif any(on(x + dx, y + dy) for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1))): cells[(x, y)] = (glow, faint)
    return cells, 1

def shaded(rows, top, bot, edge, split=4):
    # Tycho's wordmark coloring: two tones and a lit top and left edge
    cells = {}
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '#': cells[(x, y)] = (edge if (y == 0 or (x == 0 and y < split)) else top if y < split else bot, 1)
    return cells, 0

def painted(rows, ramp, seed=7, stroke=(2, 4), jitter=0.14):
    # Lodestar's way: short strokes of close tones by how lit each row is,
    # lighter toward the top
    rng = random.Random(seed); cells = {}
    h = len(rows)
    for y, r in enumerate(rows):
        x = 0
        while x < len(r):
            if r[x] != '#': x += 1; continue
            n = rng.randint(*stroke); xs = []
            while x < len(r) and r[x] == '#' and len(xs) < n: xs.append(x); x += 1
            v = (1 - y / (h - 1)) * 0.85 + 0.15 + rng.uniform(-jitter, jitter)
            i = max(0, min(len(ramp) - 1, round(v * (len(ramp) - 1))))
            for xx in xs: cells[(xx, y)] = (ramp[i], 1)
    return cells, 0

def shadowed(rows, ink, shadow, alpha=1, d=0.5):
    # Merryfolk's title: the ink over a hard shadow half a cell down and right
    cells = {}
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '#': cells[(x + d, y + d)] = (shadow, alpha)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '#': cells[(x, y)] = (ink, 1)
    return cells, 1

# --- the lockups --------------------------------------------------------------

def mark_png(data, px=128):
    im = Image.open(io.BytesIO(data)).convert('RGBA').resize((px, px), Image.BOX)
    out = io.BytesIO(); im.save(out, 'PNG', optimize=True)
    return base64.b64encode(out.getvalue()).decode()

def paths(cells):
    runs = {}
    for (x, y), (col, a) in cells.items():
        runs.setdefault((col, a), []).append(f'M{x:g} {y:g}h1v1h-1z')
    return [f'<path fill="{c}"{"" if a >= 1 else f" fill-opacity={chr(34)}{a}{chr(34)}"} d="{"".join(ds)}"/>' for (c, a), ds in sorted(runs.items(), key=lambda kv: -kv[0][1])]

def lockup(label, icon, blocks):
    # the mark 64 wide, rounded like a launcher's icon; then each block of
    # text (cells, their scale and a margin of cells round them) stacked and
    # centered beside it
    tw = max(int((max(x for x, y in c) + 1 + m) * k + 0.999) for c, k, m in blocks)
    th = sum(int((max(y for x, y in c) + 1 + m) * k + 0.999) for c, k, m in blocks) + 2 * (len(blocks) - 1)
    tx, ty = 72, (64 - th) // 2
    w = tx + tw
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 64" width="{w * 2}" height="128" shape-rendering="crispEdges" role="img" aria-label="{label}">',
           '<clipPath id="r"><rect width="64" height="64" rx="12"/></clipPath>',
           f'<image width="64" height="64" clip-path="url(#r)" image-rendering="pixelated" href="data:image/png;base64,{mark_png(icon)}"/>']
    y = ty
    for cells, k, m in blocks:
        out += [f'<g transform="translate({tx} {y}) scale({k})">'] + paths(cells) + ['</g>']
        y += int((max(yy for xx, yy in cells) + 1 + m) * k + 0.999) + 2
    return '\n'.join(out + ['</svg>']) + '\n'

def write(slug, label, icon, dark_blocks, light_blocks):
    open(os.path.join(HERE, f'{slug}-lockup.svg'), 'w').write(lockup(label, icon, dark_blocks))
    open(os.path.join(HERE, f'{slug}-lockup-on-light.svg'), 'w').write(lockup(label, icon, light_blocks))
    print(f'drew {slug}-lockup.svg, {slug}-lockup-on-light.svg')

def shift(cells, m):
    # cells moved in by a margin, so a halo has room
    return {(x + m, y + m): v for (x, y), v in cells.items()}

def block(cells_margin, k):
    cells, m = cells_margin
    return (shift(cells, m), k, m)

if __name__ == '__main__':
    # Under the White Dragon: Dragon Pixel capitals on two lines, teal neon
    # (the game's --teal, #3af0e0) lit white along the top, at three to one
    dp = dragon_pixel()
    icon = source('under-the-white-dragon', 'icons/icon-512.png')
    lines = [set_rows(dp, 'UNDER THE'), set_rows(dp, 'WHITE DRAGON')]
    write('under-the-white-dragon', 'Under the White Dragon', icon,
          [block(neon(r, '#3af0e0', '#eafffc', '#3af0e0'), 3) for r in lines],
          [block(neon(r, '#0f9790', '#1cc4ba', '#3af0e0', 0.35, 0.14), 3) for r in lines])
    # Lodestar: the squared face in strokes of the star's golds (art.js's
    # ART.pal.star), lighter toward the top, at three to one
    icon = source('Lodestar', 'icons/icon-512.png')
    rows = set_rows(SQUARE, 'LODESTAR', gap=2)
    write('lodestar', 'Lodestar', icon,
          [block(painted(rows, ['#8a6430', '#d8ae5c', '#fff2c8']), 3)],
          [block(painted(rows, ['#3a2a14', '#8a6430', '#d8ae5c']), 3)])
    # NEO: VT323 at four to one, phosphor green (--green, #3cff6e) with the
    # white-hot top rows and the glow of the title screen's text-shadow
    icon = source('Neo', 'icons/icon-512.png')
    rows = font_rows(vt323(), 'NEO', 240, 20, spacing=1)
    write('neo', 'NEO', icon,
          [block(neon(rows, '#3cff6e', '#eaffef', '#3cff6e', 0.3, 0.12, lit_rows=1), 4)],
          [block(neon(rows, '#118a3b', '#2bb85a', '#3cff6e', 0.3, 0.12, lit_rows=1), 4)])
    # Merryfolk: Silkscreen Bold, the title's moss over a parchment shadow a
    # half-cell down and right (the intro's text-shadow), at four to one
    icon = source('merryfolk', 'icons/icon-512.png')
    rows = font_rows(silkscreen(), 'Merryfolk', 80, 10)
    write('merryfolk', 'Merryfolk', icon,
          [block(shadowed(rows, '#5c8f3e', '#d8bf88', 0.5), 4)],
          [block(shadowed(rows, '#3f6b2f', '#d8bf88'), 4)])
