#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════
#   N E O N   P A C - M A N  ·  single-file pygame build
#   pip install pygame          (numpy optional → enables sound)
#   python neon_pacman.py
#   ARROWS/WASD move · P pause · M sound · ENTER start · ESC quit
#   ── WINDOW: auto-sizes to ~1000px tall, and shrinks itself to fit
#      smaller screens/laptops. Tweak the 27 in set_window_size() to override.
# ═══════════════════════════════════════════════════════════════════════════
import math, os, random, sys
import pygame as pg

# ─────────────────────────────── board ───────────────────────────────────
COLS, ROWS = 28, 31

TILE = 27                                       # provisional size; refined below
PS = TILE / 20.0                                # global pixel-scale factor
W, H = COLS * TILE, ROWS * TILE
TOP, BOT = round(60 * PS), round(46 * PS)
WIN_W, WIN_H = W, TOP + H + BOT
OY = TOP
HALF = TILE / 2

def set_window_size():
    """Pick the biggest tile size that fits this screen (target ≈ 1000px tall)."""
    global TILE, PS, W, H, TOP, BOT, WIN_W, WIN_H, OY, HALF
    info = pg.display.Info()
    sw = info.current_w or 1280
    sh = info.current_h or 800
    # full window ≈ 36.3 tiles tall × 28 tiles wide + room for taskbar/titlebar
    fit = min((sh - 90) / 36.3, (sw - 40) / 28)
    TILE = int(max(15, min(27, fit)))              # 27 → 756×980 window
    PS = TILE / 20.0                               # global pixel-scale factor
    W, H = COLS * TILE, ROWS * TILE
    TOP, BOT = round(60 * PS), round(46 * PS)
    WIN_W, WIN_H = W, TOP + H + BOT
    OY = TOP
    HALF = TILE / 2

MAZE = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "xxxxx#.##### ## #####.#xxxxx",
    "xxxxx#.##          ##.#xxxxx",
    "xxxxx#.## ###--### ##.#xxxxx",
    "######.## #      # ##.######",
    "      .   #      #   .      ",
    "######.## #      # ##.######",
    "xxxxx#.## ######## ##.#xxxxx",
    "xxxxx#.##          ##.#xxxxx",
    "xxxxx#.## ######## ##.#xxxxx",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#o..##.......  .......##..o#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################",
]

# ─────────────────────────────── constants ───────────────────────────────
BG        = (5, 6, 15)
PELLET_C  = (255, 193, 156)
POWER_C   = (255, 233, 180)
DOOR_C    = (255, 179, 226)
PAC_C     = (255, 222, 0)
WHITE     = (235, 240, 255)
GREY      = (130, 140, 170)
RED       = (255, 80, 80)
READY_C   = (255, 230, 90)
FRIGHT_C  = (38, 38, 224)
FLASH_C   = (228, 228, 255)
EYE_C     = (250, 250, 255)
PUPIL_C   = (24, 48, 224)

ORDER = [(0, -1), (-1, 0), (0, 1), (1, 0)]      # up, left, down, right
UP, LEFT, DOWN, RIGHT = ORDER
SCATTER_PLAN = [7, 20, 7, 20, 5, 20, 5, 10**9]  # scatter/chase waves

PAC_SPEED, GHOST_SPEED = 7.7, 7.15              # tiles per second
FRIGHT_SPEED, TUNNEL_SPEED, EYES_SPEED = 4.6, 4.2, 15.0

PALETTES = [  # (line colour, wall fill) per level, cycles
    ((88, 148, 255), (16, 32, 96)),
    ((70, 225, 190), (14, 70, 62)),
    ((255, 128, 96), (92, 32, 22)),
    ((196, 130, 255), (58, 26, 96)),
    ((140, 210, 80), (34, 70, 18)),
]
GHOST_DEFS = [  # (name, colour, scatter tile, home x (in tiles), release delay)
    ("blinky", (255, 62, 62),   (25, -2), 14.0, 0.0),
    ("pinky",  (255, 148, 232), (2, -2),  14.0, 1.2),
    ("inky",   (0, 220, 255),   (27, 33), 12.0, 4.0),
    ("clyde",  (255, 160, 64),  (0, 33),  16.0, 7.0),
]
HS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neon_pac_highscore.txt")

def passable(c, r):
    if r < 0 or r >= ROWS:
        return False
    return MAZE[r][c % COLS] not in "#x-"

def load_hs():
    try:
        return int(open(HS_FILE).read().strip() or 0)
    except Exception:
        return 0

def save_hs(v):
    try:
        open(HS_FILE, "w").write(str(int(v)))
    except Exception:
        pass

# ─────────────────────────────── sound synth ─────────────────────────────
def build_sounds():
    """Tiny chiptune synth. Needs numpy — silently goes silent without it."""
    try:
        import numpy as np
        if pg.mixer.get_init() is None:
            return {}
        SR = 22050

        def arr(freq, ms, vol=0.5, wave="square", sweep=None, vib=0.0):
            n = max(1, int(SR * ms / 1000))
            t = np.arange(n) / SR
            f = np.full(n, float(freq))
            if sweep: f = np.linspace(freq, sweep, n)
            if vib:   f = f + vib * np.sin(2 * np.pi * 8 * t)
            ph = np.cumsum(2 * np.pi * f / SR)
            if wave == "square": s = np.sign(np.sin(ph))
            elif wave == "saw":  s = 2 * ((ph / (2 * np.pi)) % 1.0) - 1
            else:                s = np.sin(ph)
            env = np.minimum(1.0, t / 0.004) * np.exp(-2.6 * t / max(ms / 1000, 1e-4))
            return (s * env * vol).astype(np.float32)

        def lfo(base, depth, period, vol, wave="sine"):     # seamless loops
            n = int(SR * period)
            t = np.arange(n) / SR
            f = base + depth * np.sin(2 * np.pi * t / period)
            ph = np.cumsum(2 * np.pi * f / SR)
            s = np.sin(ph) if wave == "sine" else np.sign(np.sin(ph))
            return (s * vol).astype(np.float32)

        def cat(parts):
            a = np.clip(np.concatenate(parts), -1, 1)
            return pg.sndarray.make_sound(
                (np.column_stack([a, a]) * 32767).astype(np.int16))

        def seq(notes, vol=0.45, wave="square"):
            return cat([arr(f, ms, vol, wave) for f, ms in notes])

        return {
            "waka1": cat([arr(260, 55, 0.30, sweep=560)]),
            "waka2": cat([arr(560, 55, 0.30, sweep=260)]),
            "power": cat([arr(140, 330, 0.50, sweep=560)]),
            "ghost": cat([arr(180, 330, 0.50, sweep=1150)]),
            "fruit": seq([(660, 70), (990, 110)]),
            "life":  seq([(523, 90), (659, 90), (784, 90), (1047, 220)]),
            "clear": seq([(523, 80), (659, 80), (784, 80), (1047, 90), (1319, 260)]),
            "death": cat([arr(640, 950, 0.5, sweep=110, vib=50),
                          arr(0, 70, 0), arr(330, 110, 0.4),
                          arr(0, 50, 0), arr(165, 230, 0.4)]),
            "jingle": seq([(494,130),(988,130),(740,130),(622,130),(988,65),(740,65),(622,250),
                           (523,130),(1047,130),(784,130),(659,130),(1047,65),(784,65),(659,250),
                           (494,130),(988,130),(740,130),(622,130),(988,65),(740,65),
                           (622,65),(740,65),(622,220)], vol=0.35),
            "siren":       cat([lfo(420, 150, 0.90, 0.30)]),
            "fright_loop": cat([lfo(240, 120, 0.42, 0.22, wave="square")]),
        }
    except Exception:
        return {}

def play(snd, name, vol=1.0):
    if snd and name in snd:
        snd[name].set_volume(vol)
        snd[name].play()

# ─────────────────────────────── art helpers ─────────────────────────────
_glow_cache = {}
def glow_dot(col, r, alpha=45):
    key = (col, r, alpha)
    if key not in _glow_cache:
        s = pg.Surface((r * 4, r * 4), pg.SRCALPHA)
        for rad, a in ((r * 1.9, alpha * 0.45), (r * 1.25, alpha * 0.7), (r * 0.8, alpha)):
            pg.draw.circle(s, (*col, int(a)), (r * 2, r * 2), int(rad))
        _glow_cache[key] = s
    return _glow_cache[key]

def blur(s, k):
    w, h = s.get_size()
    sm = pg.transform.smoothscale(s, (max(1, w // k), max(1, h // k)))
    return pg.transform.smoothscale(sm, (w, h))

def neon_text(font, s, col):
    base = font.render(s, True, col)
    w, h = base.get_size()
    pad = round(22 * PS)
    img = pg.Surface((w + pad * 2, h + pad * 2), pg.SRCALPHA)
    for k, a in ((10, 70), (5, 85)):
        g = blur(base, k)
        g.fill((255, 255, 255, a), special_flags=pg.BLEND_RGBA_MULT)
        img.blit(g, (pad, pad), special_flags=pg.BLEND_RGB_ADD)
    img.blit(base, (pad, pad))
    return img

def build_scanlines(w, h):
    s = pg.Surface((w, h), pg.SRCALPHA)
    for y in range(0, h, 3):
        s.fill((0, 0, 0, 22), (0, y, w, 1))
    return s

def wall_segments(P=5):
    """Neon outline of every wall face that borders open space (+ corner chamfers)."""
    def block(c, r):
        if c < 0 or c >= COLS or r < 0 or r >= ROWS:
            return True
        return MAZE[r][c] in "#x-"
    segs, verts = [], set()
    def seg(a, b):
        segs.append((a, b)); verts.add(a); verts.add(b)
    for r in range(ROWS):
        for c in range(COLS):
            if MAZE[r][c] != "#":
                continue
            x, y = c * TILE, r * TILE
            u, d = not block(c, r - 1), not block(c, r + 1)
            l, rt = not block(c - 1, r), not block(c + 1, r)
            x0, x1, y0, y1 = x + P, x + TILE - P, y + P, y + TILE - P
            if u:  seg((x0 if l else x, y0), (x1 if rt else x + TILE, y0))
            if d:  seg((x0 if l else x, y1), (x1 if rt else x + TILE, y1))
            if l:  seg((x0, y0 if u else y), (x0, y1 if d else y + TILE))
            if rt: seg((x1, y0 if u else y), (x1, y1 if d else y + TILE))
            ul, ur = block(c - 1, r - 1), block(c + 1, r - 1)
            dl, dr = block(c - 1, r + 1), block(c + 1, r + 1)
            if u and not l and ul:   seg((x, y0), (x - P, y))
            if u and not rt and ur:  seg((x + TILE, y0), (x + TILE + P, y))
            if d and not l and dl:   seg((x, y1), (x - P, y + TILE))
            if d and not rt and dr:  seg((x + TILE, y1), (x + TILE + P, y + TILE))
            if l and not u and ul:   seg((x0, y), (x, y - P))
            if rt and not u and ur:  seg((x1, y), (x + TILE, y - P))
            if l and not d and dl:   seg((x0, y + TILE), (x, y + TILE + P))
            if rt and not d and dr:  seg((x1, y + TILE), (x + TILE, y + TILE + P))
    return segs, verts

def build_maze(core, fill):
    surf = pg.Surface((W, H), pg.SRCALPHA)
    body = pg.Surface((W, H), pg.SRCALPHA)
    for r in range(ROWS):
        for c in range(COLS):
            if MAZE[r][c] == "#":
                body.fill((*fill, 70), (c * TILE, r * TILE, TILE, TILE))
    surf.blit(body, (0, 0))
    lines = pg.Surface((W, H), pg.SRCALPHA)
    segs, verts = wall_segments(max(5, round(TILE / 4)))
    lw = max(3, round(3 * PS))
    for a, b in segs:
        pg.draw.line(lines, core, a, b, lw)
    for v in verts:
        pg.draw.circle(lines, core, v, 1.6 * PS)
    pg.draw.line(lines, DOOR_C, (13 * TILE, 12 * TILE + HALF), (15 * TILE, 12 * TILE + HALF),
                 max(4, round(4 * PS)))
    surf.blit(blur(lines, 7), (0, 0), special_flags=pg.BLEND_RGB_ADD)
    surf.blit(blur(lines, 3), (0, 0), special_flags=pg.BLEND_RGB_ADD)
    surf.blit(lines, (0, 0))
    return surf

def draw_pac(surf, x, y, face, f, r=None, col=PAC_C):
    if r is None:
        r = 0.78 * TILE
    base = math.atan2(face[1], face[0])
    half = (0.05 + 0.95 * max(0.0, min(1.0, f))) * math.pi
    n, pts = 28, [(x, y)]
    for k in range(n + 1):
        a = base + half + (2 * math.pi - 2 * half) * k / n
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
    pg.draw.polygon(surf, col, pts)

def draw_ghost(surf, x, y, color, dirv, t, mode="normal", flash=False):
    w = h = int(TILE * 1.8)
    s = pg.Surface((w, h), pg.SRCALPHA)
    e = w / 36.0                                    # feature scale
    body, feat = None, EYE_C
    if mode == "fright":
        body = FLASH_C if flash else FRIGHT_C
        feat = (255, 96, 96) if flash else EYE_C
    elif mode != "eyes":
        body = color
    R, cy, wave_y = w / 2 - 1, w / 2 + 1 - 1, h - 5
    pts, n = [], 16
    for k in range(n + 1):
        a = math.pi + math.pi * k / n
        pts.append((w / 2 + math.cos(a) * R, cy + math.sin(a) * R * 0.92))
    pts.append((w - 1, wave_y))
    ph = t * 11
    for k in range(13):
        px = (w - 1) - (w - 2) * k / 12
        pts.append((px, wave_y + 2.4 * e * math.sin(px / w * 6 * math.pi + ph)))
    pts.append((1, wave_y))
    if body:
        surf.blit(glow_dot(body, round(16 * PS), 40), (x - 32 * PS, y - 32 * PS))
        pg.draw.polygon(s, body, pts)
    ey = cy - 2 * e
    if mode == "fright":
        for cx in (w * 0.33, w * 0.67):
            pg.draw.circle(s, feat, (cx, ey), 2.4 * e)
        zig = [(w * 0.18 + w * 0.64 * k / 8,
                h * 0.66 + (2.4 * e if k % 2 else -1.2 * e)) for k in range(9)]
        pg.draw.lines(s, feat, False, zig, 2)
    else:
        dx, dy = dirv if dirv else LEFT
        for cx in (w * 0.33, w * 0.67):
            pg.draw.ellipse(s, EYE_C, (cx - 4 * e, ey - 5 * e, 8.5 * e, 10 * e))
            pg.draw.circle(s, PUPIL_C, (cx + dx * 2.4 * e, ey - 0.5 * e + dy * 2.6 * e), 2.6 * e)
    surf.blit(s, (x - w / 2, y - h / 2))

def draw_fruit(surf, x, y, kind, t=0.0):
    s = TILE / 20.0
    y += math.sin(t * 3) * 1.5 * s
    lw = max(2, round(2 * s))
    if kind == 1:      # cherries
        for cx in (x - 5 * s, x + 5 * s):
            pg.draw.circle(surf, (235, 60, 60), (cx, y + 3 * s), 5.5 * s)
            pg.draw.circle(surf, (255, 150, 150), (cx - 1.8 * s, y + 1.2 * s), 1.6 * s)
        pg.draw.line(surf, (90, 200, 80), (x - 4 * s, y + 1 * s), (x + 2 * s, y - 7 * s), lw)
        pg.draw.line(surf, (90, 200, 80), (x + 5 * s, y), (x + 2 * s, y - 7 * s), lw)
    elif kind == 2:    # strawberry
        pg.draw.polygon(surf, (235, 60, 90),
                        [(x, y + 8 * s), (x - 7 * s, y), (x - 5 * s, y - 4 * s),
                         (x + 5 * s, y - 4 * s), (x + 7 * s, y)])
        pg.draw.line(surf, (90, 200, 80), (x, y - 8 * s), (x, y - 4 * s), lw)
        for sx, sy in ((-3, 0), (3, 1), (0, 4)):
            pg.draw.circle(surf, (255, 230, 230), (x + sx * s, y + sy * s), 1 * s)
    elif kind == 3:    # orange
        pg.draw.circle(surf, (255, 150, 40), (x, y + 2 * s), 7 * s)
        pg.draw.line(surf, (90, 170, 60), (x, y - 5 * s), (x + 3 * s, y - 9 * s), lw)
        pg.draw.circle(surf, (110, 200, 70), (x - 3 * s, y - 6 * s), 3 * s)
    elif kind == 4:    # apple
        pg.draw.circle(surf, (220, 40, 40), (x - 2.5 * s, y + 2 * s), 5.5 * s)
        pg.draw.circle(surf, (220, 40, 40), (x + 2.5 * s, y + 2 * s), 5.5 * s)
        pg.draw.line(surf, (110, 70, 40), (x, y - 3 * s), (x + 1 * s, y - 8 * s), lw)
    else:              # melon
        pg.draw.circle(surf, (90, 200, 70), (x, y + 2 * s), 7.5 * s)
        for sx1, sy1, sx2, sy2 in ((-5, -3, -3, 8), (0, -5.5, 0, 9), (5, -3, 3, 8)):
            pg.draw.line(surf, (40, 130, 50),
                         (x + sx1 * s, y + sy1 * s), (x + sx2 * s, y + sy2 * s), 1)

def txt(surf, s, font, col, x, y, anchor="center"):
    surf.blit(font.render(s, True, col), font.render(s, True, col).get_rect(**{anchor: (x, y)}))

# ─────────────────────────────── actors ──────────────────────────────────
def _next_center(p, sign):
    if sign > 0:
        return (math.floor((p - HALF) / TILE) + 1) * TILE + HALF
    return (math.ceil((p - HALF) / TILE) - 1) * TILE + HALF

class Actor:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.dir = None

    @property
    def tile(self):
        return int(self.x // TILE) % COLS, int(self.y // TILE)

    def _set_axis(self, v, horiz):
        if horiz: self.x = v % W          # tunnel wrap
        else:     self.y = v

    def advance(self, dist, decide):
        """Grid-locked movement; decide() runs exactly on every tile centre."""
        guard = 0
        while dist > 1e-6 and guard < 60:
            guard += 1
            if self.dir is None:
                decide()
                if self.dir is None:
                    return
            dx, dy = self.dir
            horiz = dx != 0
            pos = self.x if horiz else self.y
            sign = dx if horiz else dy
            nc = _next_center(pos, sign)
            gap = abs(nc - pos)
            if gap > dist:
                self._set_axis(pos + sign * dist, horiz)
                return
            self._set_axis(nc, horiz)
            dist -= gap
            decide()

class Pac(Actor):
    def __init__(self):
        super().__init__(0, 0)
        self.face, self.want, self.mouth = LEFT, None, 0.0
        self.reset()

    def reset(self):
        self.x, self.y = 14 * TILE, 23.5 * TILE
        self.dir = self.face = LEFT
        self.want, self.mouth = None, 0.0

    def _decide(self):
        c, r = self.tile
        if self.want and passable(c + self.want[0], r + self.want[1]):
            self.dir = self.want
        if self.dir and not passable(c + self.dir[0], r + self.dir[1]):
            self.dir = None

    def update(self, dt, game):
        if self.want and self.dir and self.want == (-self.dir[0], -self.dir[1]):
            self.dir = self.want                       # instant about-face
        self.advance(PAC_SPEED * game.pace * TILE * dt, self._decide)
        if self.dir:
            self.face = self.dir
            self.mouth += dt * 11

class Ghost(Actor):
    def __init__(self, name, color, scatter, home_x, release):
        super().__init__(home_x, 14.5 * TILE)
        self.name, self.color, self.scatter = name, color, scatter
        self.home_x, self.base_release = home_x, release
        self.game, self.frightened, self.bob = None, False, 1
        self.state = "house"
        self.reset()

    def reset(self):
        scale = max(0.35, 1 - 0.12 * (self.game.level - 1)) if self.game else 1.0
        self.frightened = False
        self.bob = random.choice((-1, 1))
        if self.name == "blinky":
            self.x, self.y = 14 * TILE, 11.5 * TILE
            self.dir, self.state = LEFT, "roam"
        else:
            self.x, self.y = self.home_x, 14.5 * TILE
            self.dir = (0, self.bob)
            self.state, self.release = "house", self.base_release * scale

    def speed(self):
        if self.state == "eyes":
            return EYES_SPEED * TILE
        if self.frightened:
            return FRIGHT_SPEED * TILE
        c, r = self.tile
        if r == 14 and (c < 6 or c > 21):               # tunnel slowdown
            return TUNNEL_SPEED * TILE
        return GHOST_SPEED * self.game.pace * TILE

    def chase_target(self):
        g = self.game
        pc, pr = g.pac.tile
        dx, dy = g.pac.dir or g.pac.face
        if self.name == "blinky":
            return (pc, pr)
        if self.name == "pinky":
            return (pc + 4 * dx, pr + 4 * dy)
        if self.name == "inky":
            b = g.ghosts[0].tile
            ax, ay = pc + 2 * dx, pr + 2 * dy
            return (2 * ax - b[0], 2 * ay - b[1])
        ct, rt = self.tile                              # clyde
        return (pc, pr) if (pc - ct) ** 2 + (pr - rt) ** 2 > 64 else self.scatter

    def _decide(self):
        c, r = self.tile
        rev = (-self.dir[0], -self.dir[1]) if self.dir else None
        opts = [d for d in ORDER if d != rev and passable(c + d[0], r + d[1])]
        if not opts:
            self.dir = rev or random.choice(ORDER)
            return
        if self.state == "roam" and self.frightened:
            self.dir = random.choice(opts)
            return
        if self.state == "eyes":
            tgt = (13, 11)
        elif self.game.mode == "scatter":
            tgt = self.scatter
        else:
            tgt = self.chase_target()
        self.dir = min(opts, key=lambda d: (c + d[0] - tgt[0]) ** 2 + (r + d[1] - tgt[1]) ** 2)

    def update(self, dt):
        sp = self.speed()
        st = self.state
        if st == "house":
            self.release -= dt
            self.y += 14 * PS * dt * self.bob
            lim = 0.2 * TILE
            if self.y > 14.5 * TILE + lim: self.bob, self.y = -1, 14.5 * TILE + lim
            if self.y < 14.5 * TILE - lim: self.bob, self.y = 1, 14.5 * TILE - lim
            self.dir = (0, self.bob)
            if self.release <= 0:
                self.state = "exit"
        elif st == "exit":
            if abs(self.x - 14 * TILE) > 0.5:
                step = min(sp * dt, abs(self.x - 14 * TILE))
                self.dir = (1, 0) if self.x < 14 * TILE else (-1, 0)
                self.x += math.copysign(step, 14 * TILE - self.x)
            else:
                self.x = 14 * TILE
                self.dir = UP
                self.y -= sp * dt
                if self.y <= 11.5 * TILE:
                    self.y = 11.5 * TILE
                    self.state = "roam"
                    self.dir = random.choice((LEFT, RIGHT))
        elif st == "enter":
            self.dir = DOWN
            self.y += sp * dt
            if self.y >= 14.5 * TILE:
                self.y = 14.5 * TILE
                self.frightened = False
                self.state = "exit"
        else:
            if st == "eyes":
                c, r = self.tile
                if r == 11 and c in (13, 14):           # glide onto the door, drop in
                    tx, step = 14 * TILE, sp * dt
                    if abs(self.x - tx) <= step:
                        self.x, self.y, self.state = tx, 11.5 * TILE, "enter"
                    else:
                        self.dir = LEFT if self.x > tx else RIGHT
                        self.x += math.copysign(step, tx - self.x)
                    return
            self.advance(sp * dt, self._decide)

class Particle:
    __slots__ = ("x", "y", "vx", "vy", "col", "life", "ttl", "r")
    def __init__(self, x, y, vx, vy, col, life, r):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.col, self.life, self.ttl, self.r = col, life, life, r

# ─────────────────────────────── game ────────────────────────────────────
class Game:
    def __init__(self, screen, snd):
        self.screen, self.snd = screen, {}
        self.ch_siren, self.siren_now, self.muted = None, None, False
        if snd:
            try:
                pg.mixer.set_reserved(1)
                self.ch_siren = pg.mixer.Channel(0)
                self.snd = snd
            except Exception:
                pass

        def fs(px):
            return pg.font.SysFont("arialblack,verdana,arial", max(12, round(px * PS)))

        self.f_title = fs(54)
        self.f_big = fs(30)
        self.f_mid = fs(19)
        self.f_sm = fs(15)
        self.f_xs = fs(12)
        self.scan = build_scanlines(WIN_W, WIN_H)
        self.img_title = neon_text(self.f_title, "PAC-MAN", PAC_C)
        self.img_ready = neon_text(self.f_big, "READY!", READY_C)
        self.img_over = neon_text(self.f_big, "GAME OVER", RED)
        self.high = load_hs()
        self.pac = Pac()
        self.ghosts = [Ghost(n, c, s, hx * TILE, rel) for n, c, s, hx, rel in GHOST_DEFS]
        for gh in self.ghosts:
            gh.game = self
        self.popups, self.parts = [], []
        self.score, self.lives, self.extra = 0, 3, False
        self.level = 0
        self.state, self.state_t = "menu", 0.0
        self.paused = False
        self.freeze, self.death_snd, self.burst_done = 0.0, False, False
        self.fruit_t, self.fruit_kind = 0.0, 1
        self.new_level()

    # ── setup / flow ──────────────────────────────────────────────────
    def new_level(self):
        self.level += 1
        self.pace = min(1.28, 1 + 0.045 * (self.level - 1))
        core, fill = PALETTES[(self.level - 1) % len(PALETTES)]
        self.maze_img = build_maze(core, fill)
        self.maze_flash = build_maze(FLASH_C, (70, 70, 110))
        self.dots = {(c, r) for r in range(ROWS) for c in range(COLS) if MAZE[r][c] == "."}
        self.powers = {(c, r) for r in range(ROWS) for c in range(COLS) if MAZE[r][c] == "o"}
        self.dots_eaten, self.fruit_hits = 0, set()
        self.fruit_t, self.fright_t, self.combo = 0.0, 0.0, 0
        self.mode_i, self.mode, self.mode_t = 0, "scatter", SCATTER_PLAN[0]
        self.reset_actors(full=True)

    def reset_actors(self, full=False):
        self.pac.reset()
        for gh in self.ghosts:
            gh.reset()
        self.freeze = 0.0
        if full:
            self.popups.clear()
            self.parts.clear()

    def new_game(self):
        self.score, self.lives, self.extra = 0, 3, False
        self.level = 0
        self.new_level()
        self.state, self.state_t = "ready", 4.3
        play(self.snd, "jingle")

    def flip_mode(self):
        self.mode_i += 1
        self.mode = "scatter" if self.mode_i % 2 == 0 else "chase"
        self.mode_t = SCATTER_PLAN[min(self.mode_i, len(SCATTER_PLAN) - 1)]
        for gh in self.ghosts:
            if gh.state == "roam" and gh.dir:
                gh.dir = (-gh.dir[0], -gh.dir[1])

    def add_score(self, n):
        self.score += n
        self.high = max(self.high, self.score)

    # ── fx ────────────────────────────────────────────────────────────
    def spark(self, x, y, col, n, sp):
        for _ in range(n):
            a = random.uniform(0, 2 * math.pi)
            v = random.uniform(sp * 0.3, sp) * PS
            self.parts.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v, col,
                                       random.uniform(0.25, 0.6),
                                       random.uniform(1.5, 3.2) * PS))

    def popup(self, x, y, s, col):
        self.popups.append([x, y, s, col, 0.0])

    def set_siren(self):
        if not self.snd:
            return
        want = None
        if self.state == "play" and not self.paused and self.freeze <= 0:
            if self.fright_t > 0:
                want = "fright_loop"
            elif self.dots or self.powers:
                want = "siren"
        if want != self.siren_now:
            self.siren_now = want
            self.ch_siren.stop()
            if want:
                self.ch_siren.play(self.snd[want], loops=-1)
        self.ch_siren.set_volume(0.0 if self.muted else 0.30)

    # ── gameplay bits ─────────────────────────────────────────────────
    def power_up(self):
        self.fright_t = max(1.8, 7.5 - (self.level - 1) * 0.75)
        self.combo = 0
        for gh in self.ghosts:
            if gh.state in ("roam", "house", "exit"):
                gh.frightened = True
                if gh.state == "roam" and gh.dir:
                    gh.dir = (-gh.dir[0], -gh.dir[1])
        play(self.snd, "power")

    def maybe_clear(self):
        if not self.dots and not self.powers:
            self.state, self.state_t = "clear", 0.0
            play(self.snd, "clear")
            return True
        return False

    def eat_check(self):
        c, r = self.pac.tile
        if (c, r) in self.dots:
            self.dots.discard((c, r))
            self.add_score(10)
            self.dots_eaten += 1
            play(self.snd, "waka1" if self.dots_eaten % 2 else "waka2")
            self.spark(c * TILE + HALF, r * TILE + HALF, PELLET_C, 2, 40)
            self.check_fruit()
            self.maybe_clear()
        elif (c, r) in self.powers:
            self.powers.discard((c, r))
            self.add_score(50)
            self.dots_eaten += 1
            self.spark(c * TILE + HALF, r * TILE + HALF, POWER_C, 12, 110)
            self.check_fruit()
            if not self.maybe_clear():
                self.power_up()

    def check_fruit(self):
        if self.dots_eaten in (70, 170) and self.dots_eaten not in self.fruit_hits:
            self.fruit_hits.add(self.dots_eaten)
            self.fruit_t, self.fruit_kind = 9.5, 1 + (self.level - 1) % 5

    def collide(self):
        px, py = self.pac.x, self.pac.y
        for gh in self.ghosts:
            if gh.state not in ("roam", "exit"):
                continue
            if (gh.x - px) ** 2 + (gh.y - py) ** 2 > (TILE * 0.68) ** 2:
                continue
            if gh.frightened:
                gh.frightened = False
                gh.state = "eyes"
                self.combo += 1
                pts = 100 * 2 ** self.combo          # 200 400 800 1600
                self.add_score(pts)
                self.popup(gh.x, gh.y, str(pts), (140, 230, 255))
                self.spark(gh.x, gh.y, gh.color, 14, 130)
                play(self.snd, "ghost")
                self.freeze = 0.32
            else:
                self.state, self.state_t = "dying", 0.0
                self.death_snd = self.burst_done = False
                break

    # ── update ────────────────────────────────────────────────────────
    def update(self, dt):
        for p in self.parts:
            p.life -= dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= 1 - 2.2 * dt
            p.vy *= 1 - 2.2 * dt
        self.parts = [p for p in self.parts if p.life > 0]
        for p in self.popups:
            p[4] += dt
        self.popups = [p for p in self.popups if p[4] < 0.9]

        if self.paused:
            self.set_siren()
            return
        st = self.state

        if st == "ready":
            self.state_t -= dt
            if self.state_t <= 0:
                self.state = "play"

        elif st == "play":
            if self.freeze > 0:
                self.freeze -= dt
                self.set_siren()
                return
            if self.fright_t > 0:
                self.fright_t -= dt
                if self.fright_t <= 0:
                    self.fright_t = 0
                    for gh in self.ghosts:
                        gh.frightened = False
            else:
                self.mode_t -= dt
                if self.mode_t <= 0:
                    self.flip_mode()
            self.pac.update(dt, self)
            self.eat_check()
            if self.state == "play":
                for gh in self.ghosts:
                    gh.update(dt)
                self.collide()
            if self.fruit_t > 0:
                self.fruit_t -= dt
                if (self.pac.x - 14 * TILE) ** 2 + (self.pac.y - 17.5 * TILE) ** 2 < (TILE * 0.6) ** 2:
                    self.fruit_t = 0
                    pts = (100, 300, 500, 700, 1000)[self.fruit_kind - 1]
                    self.add_score(pts)
                    self.popup(14 * TILE, 17 * TILE, str(pts), (255, 170, 120))
                    self.spark(14 * TILE, 17.5 * TILE, (235, 60, 60), 10, 110)
                    play(self.snd, "fruit")
            if not self.extra and self.score >= 10000:
                self.extra = True
                self.lives += 1
                self.popup(self.pac.x, self.pac.y - 14 * PS, "EXTRA LIFE!", (120, 255, 140))
                play(self.snd, "life")

        elif st == "dying":
            self.state_t += dt
            if self.state_t >= 0.55 and not self.death_snd:
                self.death_snd = True
                play(self.snd, "death")
            if self.state_t >= 1.75 and not self.burst_done:
                self.burst_done = True
                self.spark(self.pac.x, self.pac.y, PAC_C, 16, 120)
            if self.state_t >= 2.5:
                self.lives -= 1
                if self.lives <= 0:
                    self.state, self.state_t = "over", 0.0
                    save_hs(self.high)
                else:
                    self.reset_actors()
                    self.state, self.state_t = "ready", 1.7

        elif st == "clear":
            self.state_t += dt
            if self.state_t >= 2.4:
                self.new_level()
                self.state, self.state_t = "ready", 2.0

        elif st == "over":
            self.state_t += dt
            if self.state_t >= 8:
                self.state = "menu"
        self.set_siren()

    # ── input ─────────────────────────────────────────────────────────
    def handle_events(self):
        for e in pg.event.get():
            if e.type == pg.QUIT:
                self.quit()
            elif e.type == pg.KEYDOWN:
                k = e.key
                if k == pg.K_ESCAPE:
                    self.quit()
                elif k == pg.K_m:
                    self.muted = not self.muted
                elif k == pg.K_p and self.state in ("play", "ready"):
                    self.paused = not self.paused
                elif self.state == "menu" and k in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_SPACE):
                    self.new_game()
                elif self.state == "over" and self.state_t > 1 and k in (pg.K_RETURN, pg.K_KP_ENTER):
                    self.state = "menu"
                elif self.state in ("play", "ready") and not self.paused:
                    d = {pg.K_UP: UP, pg.K_w: UP, pg.K_LEFT: LEFT, pg.K_a: LEFT,
                         pg.K_DOWN: DOWN, pg.K_s: DOWN, pg.K_RIGHT: RIGHT, pg.K_d: RIGHT}.get(k)
                    if d:
                        self.pac.want = d

    def quit(self):
        save_hs(self.high)
        pg.quit()
        sys.exit()

    # ── render ────────────────────────────────────────────────────────
    def draw(self):
        scr = self.screen
        scr.fill(BG)
        t = pg.time.get_ticks() / 1000
        F = self.f_sm

        # top HUD
        if int(t * 2.5) % 2 == 0 or self.state != "play":
            txt(scr, "1UP", F, WHITE, 70 * PS, 14 * PS)
        txt(scr, "00" if self.score == 0 else str(self.score), F, WHITE, 70 * PS, 32 * PS)
        txt(scr, "HIGH SCORE", F, WHITE, WIN_W // 2, 14 * PS)
        txt(scr, str(self.high), F, WHITE, WIN_W // 2, 32 * PS)
        txt(scr, f"LV{self.level}", F, GREY, WIN_W - 48 * PS, 14 * PS)

        # maze
        mz = self.maze_flash if (self.state == "clear" and int(self.state_t * 3.2) % 2 == 0) else self.maze_img
        scr.blit(mz, (0, OY))

        # pellets
        show_power = self.state != "play" or (t * 3.1) % 1.0 < 0.72
        for (c, r) in self.dots:
            pg.draw.circle(scr, PELLET_C, (c * TILE + HALF, OY + r * TILE + HALF), 2.3 * PS)
        for (c, r) in self.powers:
            if show_power:
                x, y = c * TILE + HALF, OY + r * TILE + HALF
                scr.blit(glow_dot(POWER_C, round(7 * PS), 42), (x - 14 * PS, y - 14 * PS))
                pg.draw.circle(scr, POWER_C, (x, y), (4.6 + math.sin(t * 7 + c) * 1.1) * PS)

        # fruit
        if self.fruit_t > 0 and self.state == "play":
            draw_fruit(scr, 14 * TILE, OY + 17.5 * TILE, self.fruit_kind, t)

        # particles
        for p in self.parts:
            k = max(0.0, p.life / p.ttl)
            rr = p.r * (0.35 + 0.65 * k)
            if rr >= 0.6:
                pg.draw.circle(scr, p.col, (p.x, OY + p.y), rr)

        # ghosts
        hide = self.state in ("menu", "over", "clear") or (self.state == "dying" and self.state_t > 0.55)
        if not hide:
            flash = self.fright_t < 1.8 and int(self.fright_t * 6) % 2 == 1
            for gh in self.ghosts:
                mode = "eyes" if gh.state == "eyes" else ("fright" if gh.frightened else "normal")
                draw_ghost(scr, gh.x, OY + gh.y, gh.color, gh.dir, t, mode, flash)

        # pac
        if self.state == "dying":
            if self.state_t < 0.55:
                scr.blit(glow_dot(PAC_C, round(13 * PS), 34),
                         (self.pac.x - 26 * PS, OY + self.pac.y - 26 * PS))
                draw_pac(scr, self.pac.x, OY + self.pac.y, self.pac.face, 0.24)
            else:
                k = min(1.0, (self.state_t - 0.55) / 1.2)
                if k < 1.0:
                    draw_pac(scr, self.pac.x, OY + self.pac.y, UP, k ** 0.8, r=TILE * (0.85 - 0.35 * k))
        elif self.state not in ("menu", "over"):
            scr.blit(glow_dot(PAC_C, round(13 * PS), 34),
                     (self.pac.x - 26 * PS, OY + self.pac.y - 26 * PS))
            mf = 0.16 if self.state != "play" else 0.02 + 0.24 * abs(math.sin(self.pac.mouth))
            draw_pac(scr, self.pac.x, OY + self.pac.y, self.pac.face, mf)

        # popups
        for x, y, s, col, age in self.popups:
            txt(scr, s, self.f_sm, col, x, OY + y - age * 20 * PS)

        # centre messages
        msg_y = OY + 17.5 * TILE
        if self.state == "ready":
            scr.blit(self.img_ready, self.img_ready.get_rect(center=(W // 2, msg_y)))
        elif self.state == "over":
            scr.blit(self.img_over, self.img_over.get_rect(center=(W // 2, msg_y)))

        # bottom HUD: spare lives + level fruits
        by = WIN_H - BOT // 2
        for i in range(max(0, self.lives - 1)):
            draw_pac(scr, 28 * PS + i * 26 * PS, by, LEFT, 0.22, r=8 * PS)
        for i in range(min(self.level - 1, 6)):
            lv = self.level - 1 - i
            draw_fruit(scr, WIN_W - 26 * PS - i * 26 * PS, by - 2 * PS, 1 + (lv - 1) % 5)

        # menu / attract screen
        if self.state == "menu":
            ov = pg.Surface((WIN_W, WIN_H), pg.SRCALPHA)
            ov.fill((4, 5, 14, 190))
            scr.blit(ov, (0, 0))
            scr.blit(self.img_title, self.img_title.get_rect(center=(WIN_W // 2, 150 * PS)))
            gx0 = WIN_W // 2 - 3 * 62 * PS
            for i, gh in enumerate(self.ghosts):
                gx = gx0 + i * 124 * PS
                gy = 250 * PS + math.sin(t * 2.4 + i * 1.4) * 4 * PS
                dd = RIGHT if int(t + i * 0.7) % 4 < 2 else LEFT
                draw_ghost(scr, gx, gy, gh.color, dd, t, "normal")
                txt(scr, gh.name.upper(), self.f_xs, gh.color, gx, gy + 28 * PS)
            cy = 345 * PS
            phase = t % 9
            if phase < 4.5:
                px = -60 * PS + (phase / 4.5) * (WIN_W + 120 * PS)
                draw_pac(scr, px, cy, RIGHT, 0.05 + 0.22 * abs(math.sin(t * 11)))
                for i, gh in enumerate(self.ghosts):
                    draw_ghost(scr, px - 44 * PS - i * 34 * PS, cy, gh.color, RIGHT, t + i * 0.3, "normal")
            else:
                px = WIN_W + 60 * PS - ((phase - 4.5) / 4.5) * (WIN_W + 120 * PS)
                draw_pac(scr, px, cy, LEFT, 0.05 + 0.22 * abs(math.sin(t * 11)))
                for i, gh in enumerate(self.ghosts):
                    draw_ghost(scr, px + 44 * PS + i * 34 * PS, cy, gh.color, LEFT, t + i * 0.3, "fright")
            if int(t * 1.6) % 2 == 0:
                txt(scr, "PRESS  ENTER", self.f_mid, WHITE, WIN_W // 2, 440 * PS)
            txt(scr, f"HIGH SCORE  {self.high}", F, GREY, WIN_W // 2, 480 * PS)
            txt(scr, "ARROWS / WASD MOVE  ·  P PAUSE  ·  M SOUND  ·  ESC QUIT",
                self.f_xs, GREY, WIN_W // 2, 520 * PS)

        if self.paused:
            ov = pg.Surface((WIN_W, WIN_H), pg.SRCALPHA)
            ov.fill((0, 0, 10, 130))
            scr.blit(ov, (0, 0))
            txt(scr, "PAUSED", self.f_big, WHITE, W // 2, msg_y)
        if self.muted:
            txt(scr, "MUTED", self.f_xs, GREY, WIN_W - 36 * PS, WIN_H - 12 * PS)

        scr.blit(self.scan, (0, 0))
        pg.display.flip()

# ─────────────────────────────── main ────────────────────────────────────
def main():
    pg.mixer.pre_init(22050, -16, 2, 512)
    pg.init()
    set_window_size()                                # measures your screen first
    pg.display.set_caption("NEON PAC-MAN")
    icon = pg.Surface((32, 32), pg.SRCALPHA)
    pg.draw.circle(icon, PAC_C, (16, 16), 15)
    pg.display.set_icon(icon)
    screen = pg.display.set_mode((WIN_W, WIN_H))
    clock = pg.time.Clock()
    game = Game(screen, build_sounds())
    while True:
        dt = min(clock.tick(120) / 1000.0, 1 / 30)
        game.handle_events()
        game.update(dt)
        game.draw()

if __name__ == "__main__":
    main()