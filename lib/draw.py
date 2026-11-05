"""Библиотека рисования: герой, массовка, окружение, текст. Всё векторно на Cairo."""
import math
import random

import cairo

FONT = "Russo One"
TAU = math.tau


# ---------------------------------------------------------------- утилиты
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):  # smoothstep
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t, p=3):
    t = clamp(t)
    return 1 - (1 - t) ** p


def ease_in(t, p=2):
    t = clamp(t)
    return t ** p


def back_out(t, s=1.7):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def seg(t, a, b):
    """0..1 прогресс t на отрезке [a,b]."""
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def nz(t, seed=0.0):
    """Гладкий псевдошум -1..1."""
    return (math.sin(t * 1.37 + seed * 3.1) * 0.5 + math.sin(t * 2.71 + seed * 1.7) * 0.3
            + math.sin(t * 5.13 + seed * 7.3) * 0.2)


def hexc(h, a=1.0):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def mix(c1, c2, t):
    return tuple(lerp(a, b, t) for a, b in zip(c1, c2))


def src(ctx, c, a=None):
    if isinstance(c, str):
        c = hexc(c)
    if a is not None:
        c = (c[0], c[1], c[2], (c[3] if len(c) > 3 else 1) * a)
    if len(c) == 3:
        ctx.set_source_rgb(*c)
    else:
        ctx.set_source_rgba(*c)


def rr(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -TAU / 4, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, TAU / 4)
    ctx.arc(x + r, y + h - r, r, TAU / 4, TAU / 2)
    ctx.arc(x + r, y + r, r, TAU / 2, 3 * TAU / 4)
    ctx.close_path()


def ell(ctx, x, y, rx, ry):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, TAU)
    ctx.restore()


def fill(ctx, c, a=None):
    src(ctx, c, a)
    ctx.fill()


def vgrad(ctx, x, y, w, h, stops):
    g = cairo.LinearGradient(x, y, x, y + h)
    for o, c in stops:
        g.add_color_stop_rgba(o, *(hexc(c) if isinstance(c, str) else c))
    ctx.rectangle(x, y, w, h)
    ctx.set_source(g)
    ctx.fill()


def glow(ctx, x, y, r, c, a=1.0):
    c = hexc(c) if isinstance(c, str) else c
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, c[0], c[1], c[2], a)
    g.add_color_stop_rgba(0.4, c[0], c[1], c[2], a * 0.35)
    g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, TAU)
    ctx.fill()


def line(ctx, x0, y0, x1, y1, w, c, a=None, cap=cairo.LINE_CAP_ROUND):
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.set_line_width(w)
    ctx.set_line_cap(cap)
    src(ctx, c, a)
    ctx.stroke()


# ---------------------------------------------------------------- текст
def text(ctx, s, x, y, size, color="#ffffff", stroke=None, sw=0.0, align="center", alpha=1.0,
         shadow=False):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    xb, yb, tw, th, xa, ya = ctx.text_extents(s)
    if align == "center":
        x0 = x - xa / 2
    elif align == "right":
        x0 = x - xa
    else:
        x0 = x
    y0 = y + size * 0.36
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if shadow:
        ctx.move_to(x0 + size * 0.06, y0 + size * 0.08)
        ctx.text_path(s)
        src(ctx, (0, 0, 0, 0.55 * alpha))
        ctx.fill()
    if stroke:
        ctx.move_to(x0, y0)
        ctx.text_path(s)
        ctx.set_line_width(sw)
        src(ctx, stroke, alpha)
        ctx.stroke()
    ctx.move_to(x0, y0)
    ctx.text_path(s)
    src(ctx, color, alpha)
    ctx.fill()
    return xa


def text_w(ctx, s, size):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    return ctx.text_extents(s)[4]


# ---------------------------------------------------------------- ГЕРОЙ
HOOD = "#d8332a"
HOOD_D = "#a3221c"
JEANS = "#26314d"
HEAD = "#0e0e12"

# эмоции: размер глаз, веко сверху (0..1), наклон века (+ злой/хитрый, - грустный), зрачок, рот
EMO = {
    "neutral": dict(es=1.0, lid=0.18, tilt=0.0, pup=1.0, mouth="line"),
    "calm": dict(es=1.0, lid=0.32, tilt=0.0, pup=1.0, mouth="smile_s"),
    "sly": dict(es=1.0, lid=0.48, tilt=0.28, pup=1.0, mouth="smirk"),
    "shock": dict(es=1.38, lid=0.0, tilt=0.0, pup=0.55, mouth="O"),
    "fear": dict(es=1.28, lid=0.0, tilt=-0.18, pup=0.5, mouth="wave"),
    "happy": dict(es=1.0, lid=0.0, tilt=0.0, pup=1.0, mouth="grin", arc=True),
    "joy": dict(es=1.15, lid=0.0, tilt=0.0, pup=1.1, mouth="grin"),
    "sad": dict(es=1.0, lid=0.42, tilt=-0.42, pup=1.0, mouth="frown"),
    "crazy": dict(es=1.2, lid=0.0, tilt=0.0, pup=0.45, mouth="grin", odd=True),
    "worry": dict(es=1.12, lid=0.12, tilt=-0.3, pup=0.8, mouth="wave"),
    "determined": dict(es=1.0, lid=0.4, tilt=0.35, pup=1.0, mouth="line"),
    "sleep": dict(es=1.0, lid=1.0, tilt=0.0, pup=1.0, mouth="line"),
}


def _lerp_emo(a, b, t):
    ea, eb = EMO[a], EMO[b]
    out = {}
    for k in ("es", "lid", "tilt", "pup"):
        out[k] = lerp(ea[k], eb[k], t)
    src_e = eb if t > 0.5 else ea
    out["mouth"] = src_e["mouth"]
    out["arc"] = src_e.get("arc", False)
    out["odd"] = src_e.get("odd", False)
    return out


def emo(name, to=None, t=0.0):
    if to is None:
        return _lerp_emo(name, name, 0)
    return _lerp_emo(name, to, ease(t))


def _eye(ctx, x, y, rx, ry, e, side, look, blink):
    lid = clamp(max(e["lid"], blink))
    if e.get("arc") and blink < 0.5:
        # счастливые глаза-дуги ^ ^
        ctx.save()
        ctx.translate(x, y + ry * 0.3)
        ctx.scale(rx, ry)
        ctx.arc(0, 0, 0.85, TAU / 2 + 0.25, TAU - 0.25)
        ctx.restore()
        ctx.set_line_width(rx * 0.42)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        src(ctx, "#ffffff")
        ctx.stroke()
        return
    ctx.save()
    ell(ctx, x, y, rx, ry)
    ctx.clip()
    src(ctx, "#ffffff")
    ctx.paint()
    pr = min(rx, ry) * 0.46 * e["pup"]
    px = x + look[0] * rx * 0.42
    py = y + look[1] * ry * 0.38
    ell(ctx, px, py, pr, pr * 1.08)
    fill(ctx, "#0b0b0b")
    ell(ctx, px - pr * 0.35, py - pr * 0.4, pr * 0.3, pr * 0.3)
    fill(ctx, "#ffffff", 0.9)
    if lid > 0.001:
        # веко: многоугольник цвета головы, срезающий верх глаза под наклоном
        yl = y - ry + 2 * ry * lid
        k = -e["tilt"] * ry * 1.4 * side  # + : внутренний край ниже (хитрый/злой), - : грустный
        ctx.move_to(x - rx * 1.3, -1e4)
        ctx.line_to(x + rx * 1.3, -1e4)
        ctx.line_to(x + rx * 1.3, yl + k)
        ctx.line_to(x - rx * 1.3, yl - k)
        ctx.close_path()
        fill(ctx, HEAD)
    ctx.restore()


def _mouth(ctx, kind, x, y, s, t):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    w = 9 * s
    if kind == "line":
        line(ctx, x - 20 * s, y, x + 20 * s, y, w, "#ffffff")
    elif kind == "smile_s":
        ctx.arc(x, y - 16 * s, 26 * s, 0.5, TAU / 2 - 0.5)
        ctx.set_line_width(w)
        src(ctx, "#ffffff")
        ctx.stroke()
    elif kind == "smirk":
        ctx.move_to(x - 24 * s, y + 2 * s)
        ctx.curve_to(x - 4 * s, y + 10 * s, x + 16 * s, y + 6 * s, x + 30 * s, y - 10 * s)
        ctx.set_line_width(w)
        src(ctx, "#ffffff")
        ctx.stroke()
    elif kind == "frown":
        ctx.arc(x, y + 22 * s, 24 * s, TAU / 2 + 0.6, TAU - 0.6)
        ctx.set_line_width(w)
        src(ctx, "#ffffff")
        ctx.stroke()
    elif kind == "O":
        o = 1 + 0.06 * math.sin(t * 20)
        ell(ctx, x, y + 6 * s, 17 * s * o, 25 * s * o)
        fill(ctx, "#ffffff")
        ell(ctx, x, y + 8 * s, 11 * s * o, 18 * s * o)
        fill(ctx, "#5a1010")
    elif kind == "wave":
        ctx.move_to(x - 28 * s, y)
        for i in range(1, 9):
            ctx.line_to(x - 28 * s + i * 7 * s, y + (6 * s if i % 2 else -6 * s) + math.sin(t * 30 + i) * 1.5 * s)
        ctx.set_line_width(w * 0.8)
        src(ctx, "#ffffff")
        ctx.stroke()
    elif kind == "grin":
        ctx.move_to(x - 38 * s, y - 6 * s)
        ctx.curve_to(x - 30 * s, y + 40 * s, x + 30 * s, y + 40 * s, x + 38 * s, y - 6 * s)
        ctx.close_path()
        fill(ctx, "#ffffff")
        ctx.move_to(x - 24 * s, y + 14 * s)
        ctx.curve_to(x - 12 * s, y + 30 * s, x + 12 * s, y + 30 * s, x + 24 * s, y + 14 * s)
        ctx.close_path()
        fill(ctx, "#c43b3b")


def hero_head(ctx, x, y, r, e, t, look=(0, 0), blink=0.0, rim="#ff5a2a", rim_a=0.9, back=False):
    """Голова героя: чёрный шар, большие белые глаза, огненный контровой."""
    if rim_a > 0:
        glow(ctx, x, y, r * 1.35, rim, 0.35 * rim_a)
    ctx.arc(x, y, r, 0, TAU)
    fill(ctx, HEAD)
    # контровой ободок
    if rim_a > 0:
        ctx.new_path()
        ctx.arc(x, y, r - 2, -TAU * 0.2, TAU * 0.28)
        ctx.set_line_width(r * 0.06)
        src(ctx, rim, 0.85 * rim_a)
        ctx.stroke()
    # блик
    ell(ctx, x - r * 0.42, y - r * 0.5, r * 0.22, r * 0.12)
    fill(ctx, "#ffffff", 0.10)
    if back:
        return
    s = r / 110
    ex, ey = 44 * s, -6 * s
    rx, ry = 30 * s * e["es"], 37 * s * e["es"]
    if e.get("odd"):
        _eye(ctx, x - ex, y + ey, rx * 1.15, ry * 1.15, e, -1, look, blink)
        _eye(ctx, x + ex, y + ey, rx * 0.8, ry * 0.8, e, 1, look, blink)
    else:
        _eye(ctx, x - ex, y + ey, rx, ry, e, -1, look, blink)
        _eye(ctx, x + ex, y + ey, rx, ry, e, 1, look, blink)
    _mouth(ctx, e["mouth"], x, y + 52 * s, s, t)


def _arm_pts(sx, sy, a1, a2, side, L1=92, L2=86):
    d1 = (side * math.sin(a1), math.cos(a1))
    ex, ey = sx + d1[0] * L1, sy + d1[1] * L1
    d2 = (side * math.sin(a1 + a2), math.cos(a1 + a2))
    return (ex, ey), (ex + d2[0] * L2, ey + d2[1] * L2)


ARMS = {
    "down": ((0.18, 0.05), (0.18, 0.05)),
    "relax": ((0.25, -0.25), (0.25, -0.25)),
    "up": ((2.7, 0.15), (2.7, 0.15)),
    "cheer": ((2.3, 0.5), (2.3, 0.5)),
    "shock": ((1.0, 1.9), (1.0, 1.9)),      # руки к лицу
    "fwd": ((0.9, 0.8), (0.9, 0.8)),
    "hold": ((0.35, -1.6), (0.35, -1.6)),   # держит перед собой
    "phone": ((0.3, -2.3), (0.25, 0.05)),
    "wheel": ((0.6, -1.4), (0.6, -1.4)),
    "hug": ((0.4, -2.4), (0.4, -2.4)),
    "paint": ((0.5, -0.5), (1.4, 0.4)),
    "give": ((0.2, 0.05), (1.3, -0.1)),
    "shrug": ((0.9, -2.2), (0.9, -2.2)),
}


def arms_lerp(a, b, t):
    A, B = ARMS[a] if isinstance(a, str) else a, ARMS[b] if isinstance(b, str) else b
    t = ease(t)
    return tuple(tuple(lerp(A[i][j], B[i][j], t) for j in range(2)) for i in range(2))


def hero(ctx, x, y, sc=1.0, e=None, t=0.0, arms="down", walk=None, look=(0, 0), blink=0.0,
         legs=True, rim="#ff5a2a", rim_a=0.9, back=False, tilt=0.0, bob=0.0, hand_item=None,
         tremble=0.0, knees=False, hood=None):
    """Герой. (x,y) — точка между ступнями (или бёдра, если legs=False)."""
    e = e or emo("neutral")
    A = ARMS[arms] if isinstance(arms, str) else arms
    HC, HD = (hood if hood else (HOOD, HOOD_D))
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    if not legs:
        ctx.translate(0, 170)
    if tremble:
        ctx.translate(math.sin(t * 61) * 3 * tremble, math.sin(t * 47) * 2 * tremble)
    ph = walk if walk is not None else None
    yb = -abs(math.sin(ph)) * 10 if ph is not None else 0
    yb += bob
    # ноги
    if legs:
        for side in (-1, 1):
            a = math.sin(ph + (0 if side < 0 else math.pi)) * 0.45 if ph is not None else 0
            hx, hy = side * 34, -175 + yb
            fx, fy = hx + math.sin(a) * 165, hy + math.cos(a) * 165
            line(ctx, hx, hy, fx, fy - 8, 50, JEANS)
            # кроссовок
            ell(ctx, fx + 10 * (1 if not back else -1) * 0.3 + side * 6, fy, 38, 20)
            fill(ctx, "#f2f2f2")
            line(ctx, fx - 18 + side * 6, fy + 10, fx + 26 + side * 6, fy + 10, 7, "#d8332a")
    ctx.translate(0, yb)
    ctx.rotate(tilt)
    # тело-худи
    ctx.move_to(-98, -330)
    ctx.curve_to(-110, -250, -100, -190, -92, -150)
    ctx.line_to(92, -150)
    ctx.curve_to(100, -190, 110, -250, 98, -330)
    ctx.curve_to(60, -355, -60, -355, -98, -330)
    ctx.close_path()
    g = cairo.LinearGradient(-100, 0, 100, 0)
    g.add_color_stop_rgba(0, *hexc(HD))
    g.add_color_stop_rgba(0.45, *hexc(HC))
    g.add_color_stop_rgba(1, *hexc(HD))
    ctx.set_source(g)
    ctx.fill()
    if not back:
        rr(ctx, -62, -235, 124, 58, 22)  # карман
        fill(ctx, HD)
        line(ctx, -22, -330, -26, -270, 6, "#f4f4f4")
        line(ctx, 22, -330, 26, -270, 6, "#f4f4f4")
    if knees:  # сидит, обняв колени
        for side in (-1, 1):
            rr(ctx, side * 48 - 44, -330, 88, 200, 44)
            fill(ctx, JEANS)
            ell(ctx, side * 48, -140, 44, 22)
            fill(ctx, "#f2f2f2")
    # капюшон за головой
    ell(ctx, 0, -340, 92, 34)
    fill(ctx, HD)
    # руки
    items = []
    for i, side in enumerate((-1, 1)):
        a1, a2 = A[i]
        sx, sy = side * 92, -315
        (exx, eyy), (hx, hy) = _arm_pts(sx, sy, a1, a2, side)
        ctx.move_to(sx, sy)
        ctx.line_to(exx, eyy)
        ctx.line_to(hx, hy)
        ctx.set_line_width(44)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        src(ctx, HC if not back else HD)
        ctx.stroke()
        items.append((hx, hy))
    head_r = 118
    hero_head(ctx, 0, -455, head_r, e, t, look, blink, rim, rim_a, back)
    for i, (hx, hy) in enumerate(items):
        ctx.arc(hx, hy, 25, 0, TAU)
        fill(ctx, HEAD)
        if hand_item and i == 1:
            hand_item(ctx, hx, hy)
    ctx.restore()


# ---------------------------------------------------------------- МАССОВКА
SKINS = ["#f1c7a3", "#e0a77f", "#c68a62", "#8d5a3b", "#f6d6bd", "#b97850"]
HAIRS = ["#2b1d14", "#5a3a22", "#d9b46a", "#1a1a1a", "#8a2f1c", "#9a9a9a"]
SHIRTS = ["#3b82f6", "#22a06b", "#f59e0b", "#8b5cf6", "#ef4444", "#14b8a6", "#f472b6", "#64748b",
          "#eab308", "#0ea5e9"]
PANTS = ["#1f2937", "#334155", "#3f3f46", "#1e3a8a", "#57534e", "#0f172a"]


class Npc:
    def __init__(self, rnd, x, y, sc=1.0, dirx=1, speed=1.0):
        self.x, self.y, self.sc, self.dir, self.speed = x, y, sc, dirx, speed
        self.skin = rnd.choice(SKINS)
        self.hair = rnd.choice(HAIRS)
        self.shirt = rnd.choice(SHIRTS)
        self.pants = rnd.choice(PANTS)
        self.style = rnd.choice(["short", "long", "bun", "cap", "bald", "short"])
        self.item = rnd.choice(["phone", "bag", "none", "coffee", "none", "umbrella"])
        self.phase = rnd.random() * TAU
        self.female = self.style in ("long", "bun")
        self.seed = rnd.random() * 100
        # детали внешности — отдельный генератор, чтобы не сдвигать раскладку старых сцен
        r2 = random.Random(int(self.seed * 7919) + 1)
        self.glasses = r2.random() < 0.28
        self.headphones = r2.random() < 0.15
        self.beard = (not self.female) and r2.random() < 0.3
        self.mustache = (not self.female) and not self.beard and r2.random() < 0.2
        self.earrings = self.female and r2.random() < 0.5
        self.freckles = r2.random() < 0.18
        self.collar = r2.choice(["round", "v", "shirt", "hood"])
        self.print_ = r2.choice([None, None, "stripe", "logo"])
        self.neck_pillow = False   # включается сценой (самолёт)
        self.mask = False
        self.uniform = None        # "stew" — стюардесса, "pilot" — пилот

    def colors(self):
        return [self.skin, self.hair, self.shirt, self.pants]


def npc(ctx, p, t, walking=True, alpha=1.0, wipe=1.0, frozen_t=None, grin=0.0, sleep=False, clap=False, stare=0.0, look_down=False, back=False, zombie=0.0):
    """Простой мультяшный прохожий. wipe<1 — растворение снизу вверх. zombie 0..1 — превращение."""
    if zombie > 0:
        class _Z:
            pass
        z = _Z()
        z.__dict__.update(p.__dict__)
        z.skin = "#%02x%02x%02x" % tuple(int(255 * v) for v in mix(hexc(p.skin), hexc("#8fae7a"), 0.85 * zombie)[:3])
        z.shirt = "#%02x%02x%02x" % tuple(int(255 * v) for v in mix(hexc(p.shirt), hexc("#4b5563"), 0.45 * zombie)[:3])
        z.glasses = False
        z.zombie = zombie
        p = z
    tt = t if frozen_t is None else min(t, frozen_t)
    ph = p.phase + tt * 7.5 * p.speed if walking else None
    x = p.x + (p.dir * 95 * p.speed * tt if walking else 0)
    ctx.save()
    ctx.translate(x, p.y)
    ctx.scale(p.sc * p.dir, p.sc)
    if wipe < 1:
        ctx.rectangle(-300, -800, 600, 800 * wipe)
        ctx.clip()
    ctx.push_group()
    yb = -abs(math.sin(ph)) * 8 if ph is not None else 0
    for side in (-1, 1):
        a = math.sin(ph + (0 if side < 0 else math.pi)) * 0.5 if ph is not None else 0
        hx, hy = side * 22, -150 + yb
        fx, fy = hx + math.sin(a) * 145, hy + math.cos(a) * 145
        line(ctx, hx, hy, fx, fy, 36, p.pants)
        ell(ctx, fx + 8, fy + 2, 24, 13)
        fill(ctx, "#222")
    ctx.translate(0, yb)
    # тело
    if p.female:
        ctx.move_to(-62, -300)
        ctx.line_to(62, -300)
        ctx.line_to(80, -140)
        ctx.line_to(-80, -140)
        ctx.close_path()
    else:
        rr(ctx, -62, -305, 124, 170, 30)
    g_ = cairo.LinearGradient(-70, 0, 70, 0)
    c_ = hexc(p.shirt)
    g_.add_color_stop_rgba(0, *mix(c_, (0, 0, 0, 1), 0.22))
    g_.add_color_stop_rgba(0.45, *c_)
    g_.add_color_stop_rgba(1, *mix(c_, (0, 0, 0, 1), 0.28))
    ctx.set_source(g_)
    ctx.fill()
    dark_ = mix(c_, (0, 0, 0, 1), 0.35)
    if p.print_ == "stripe":
        for k in range(3):
            ctx.rectangle(-60, -260 + k * 40, 120, 12)
            fill(ctx, "#ffffff", 0.35)
    elif p.print_ == "logo":
        ctx.arc(10, -240, 18, 0, TAU)
        fill(ctx, "#ffffff", 0.5)
    if p.uniform == "stew":
        for k in range(3):
            ctx.arc(14, -270 + k * 34, 5, 0, TAU)
            fill(ctx, "#facc15")
        rr(ctx, 26, -268, 34, 14, 3)
        fill(ctx, "#f8fafc")
    elif p.collar == "v":
        ctx.move_to(-22, -303)
        ctx.line_to(14, -262)
        ctx.line_to(40, -303)
        fill(ctx, p.skin)
    elif p.collar == "shirt":
        ctx.move_to(-26, -305)
        ctx.line_to(8, -280)
        ctx.line_to(-6, -305)
        fill(ctx, "#f8fafc")
        ctx.move_to(44, -305)
        ctx.line_to(10, -280)
        ctx.line_to(24, -305)
        fill(ctx, "#f8fafc")
        for k in range(3):
            ctx.arc(10, -262 + k * 32, 3.5, 0, TAU)
            fill(ctx, dark_)
    elif p.collar == "hood":
        ell(ctx, -20, -300, 50, 18)
        fill(ctx, dark_)
        line(ctx, 4, -296, 2, -250, 4, "#f8fafc")
        line(ctx, 22, -296, 24, -252, 4, "#f8fafc")
    else:
        ctx.arc(10, -305, 26, 0, TAU / 2)
        ctx.set_line_width(5)
        src(ctx, dark_)
        ctx.stroke()
    # руки
    sw = math.sin(ph) * 0.5 if ph is not None else 0
    for side, s2 in ((-1, sw), (1, -sw)):
        ax, ay = side * 58, -290
        hx, hy = ax + math.sin(s2) * 120, ay + math.cos(s2) * 120
        if getattr(p, "zombie", 0) > 0.5:  # руки вытянуты вперёд
            hx = ax + 140 + math.sin(tt * 3 + side) * 10
            hy = ay + 30 + side * 14
            line(ctx, ax, ay, hx, hy, 28, p.shirt)
        elif clap:  # аплодирует: кисти перед лицом
            hx = 34 + side * (6 + 22 * abs(math.sin(t * 13 + p.seed)))
            hy = -350
            line(ctx, ax, ay, hx, hy, 28, p.shirt)
        elif p.item == "phone" and side == 1 and not sleep:
            hx, hy = ax + 30, ay + 40
            line(ctx, ax, ay, ax + 50, ay + 90, 28, p.shirt)
            line(ctx, ax + 50, ay + 90, hx + 20, hy - 10, 28, p.shirt)
            hx, hy = hx + 20, hy - 10
            rr(ctx, hx - 6, hy - 40, 26, 44, 5)
            fill(ctx, "#111")
        else:
            line(ctx, ax, ay, hx, hy, 28, p.shirt)
        ctx.arc(hx, hy, 15, 0, TAU)
        fill(ctx, p.skin)
        if side == -1 and p.item == "bag":
            rr(ctx, hx - 30, hy, 60, 55, 10)
            fill(ctx, "#7c4a2d")
        if side == -1 and p.item == "coffee":
            rr(ctx, hx - 12, hy - 34, 26, 36, 4)
            fill(ctx, "#f5f5f4")
        if side == -1 and p.item == "umbrella":
            line(ctx, hx, hy, hx, hy + 70, 6, "#222")
    # голова
    hy0 = -370
    if p.neck_pillow:
        ctx.arc(0, hy0 + 52, 46, -0.3, math.pi + 0.3)
        ctx.set_line_width(26)
        src(ctx, "#a78bfa")
        ctx.stroke()
    if p.uniform == "stew":  # шейный платок
        ctx.move_to(-20, hy0 + 60)
        ctx.line_to(46, hy0 + 60)
        ctx.line_to(30, hy0 + 100)
        ctx.close_path()
        fill(ctx, "#facc15")
    if p.style == "long":
        rr(ctx, -60, hy0 - 50, 120, 150, 50)
        fill(ctx, p.hair)
    # ухо и голова с лёгкой тенью
    ell(ctx, -26, hy0 + 6, 12, 16)
    fill(ctx, mix(hexc(p.skin), (0, 0, 0, 1), 0.12))
    ctx.arc(0, hy0, 58, 0, TAU)
    gh = cairo.RadialGradient(20, hy0 - 20, 10, 0, hy0, 62)
    gh.add_color_stop_rgba(0, *mix(hexc(p.skin), (1, 1, 1, 1), 0.12))
    gh.add_color_stop_rgba(1, *mix(hexc(p.skin), (0, 0, 0, 1), 0.12))
    ctx.set_source(gh)
    ctx.fill()
    if p.earrings:
        ctx.arc(-26, hy0 + 26, 5, 0, TAU)
        fill(ctx, "#facc15")
    if p.beard:
        ctx.move_to(-28, hy0 + 2)
        ctx.curve_to(-30, hy0 + 64, 50, hy0 + 70, 58, hy0 + 14)
        ctx.line_to(48, hy0 + 18)
        ctx.curve_to(40, hy0 + 44, 0, hy0 + 44, -14, hy0 + 2)
        ctx.close_path()
        fill(ctx, p.hair)
    if p.style in ("short", "long", "bun"):
        ctx.arc(0, hy0 - 6, 60, TAU / 2 + 0.15, TAU - 0.15)
        ctx.close_path()
        fill(ctx, p.hair)
        if p.style == "bun":
            ctx.arc(-10, hy0 - 66, 24, 0, TAU)
            fill(ctx, p.hair)
    elif p.style == "cap":
        ctx.arc(0, hy0 - 8, 61, TAU / 2, TAU)
        ctx.close_path()
        fill(ctx, p.shirt)
        rr(ctx, 0, hy0 - 16, 82, 14, 7)
        fill(ctx, p.shirt)
    if back:  # стоит спиной: затылок, без лица
        ctx.arc(0, hy0, 60, 0, TAU)
        fill(ctx, p.hair if p.style != "bald" else p.skin)
        if p.style == "bun":
            ctx.arc(-4, hy0 - 60, 24, 0, TAU)
            fill(ctx, p.hair)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
        ctx.restore()
        return x
    if p.uniform == "stew":  # шляпка-таблетка
        rr(ctx, -40, hy0 - 70, 80, 30, 10)
        fill(ctx, p.shirt)
        rr(ctx, -40, hy0 - 48, 80, 6, 3)
        fill(ctx, "#facc15")
    # брови, нос, румянец
    if not sleep:
        line(ctx, 8, hy0 - 14, 24, hy0 - 16, 4, p.hair if p.style != "bald" else "#5a3a22")
        line(ctx, 34, hy0 - 16, 48, hy0 - 13, 4, p.hair if p.style != "bald" else "#5a3a22")
    ctx.move_to(50, hy0 + 4)
    ctx.curve_to(60, hy0 + 14, 58, hy0 + 18, 50, hy0 + 18)
    ctx.set_line_width(3.5)
    src(ctx, mix(hexc(p.skin), (0, 0, 0, 1), 0.3))
    ctx.stroke()
    ell(ctx, 12, hy0 + 20, 9, 5)
    fill(ctx, "#f87171", 0.25)
    if p.freckles:
        for k in range(5):
            ctx.arc(8 + k * 7, hy0 + 14 + (k % 2) * 4, 1.6, 0, TAU)
            fill(ctx, "#8b5a2b", 0.6)
    # лицо (в профиль-три-четверти)
    if getattr(p, "zombie", 0) > 0.5:  # пустые белые глаза, рот, шрамы, рваная одежда
        for ex in (16, 40):
            ctx.arc(ex, hy0 + 2, 9, 0, TAU)
            fill(ctx, "#f1f5f9")
            ctx.arc(ex + 1, hy0 + 2, 2.5, 0, TAU)
            fill(ctx, "#7f1d1d")
        ell(ctx, 30, hy0 + 30, 12, 9)
        fill(ctx, "#3f1d1d")
        line(ctx, -10, hy0 - 30, 14, hy0 - 22, 4, "#7f1d1d", 0.8)
        for k in range(3):
            ctx.move_to(-50 + k * 40, -160)
            ctx.line_to(-40 + k * 40, -140)
            ctx.line_to(-30 + k * 40, -160)
            fill(ctx, "#1f2937")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
        ctx.restore()
        return x
    if sleep and p.mask:
        rr(ctx, -10, hy0 - 12, 66, 24, 10)
        fill(ctx, "#1e3a8a")
        line(ctx, -10, hy0, -40, hy0 - 6, 5, "#1e3a8a")
        ell(ctx, 30, hy0 + 28, 9, 12)
        fill(ctx, "#4a1d14")
    elif sleep:  # закрытые глаза, открытый рот
        for ex in (16, 40):
            ctx.arc(ex, hy0, 7, 0.2, TAU / 2 - 0.2)
            ctx.set_line_width(3.5)
            src(ctx, "#1b1b1b")
            ctx.stroke()
        ell(ctx, 30, hy0 + 28, 9, 12)
        fill(ctx, "#4a1d14")
    elif stare > 0:  # немигающий взгляд в упор
        for ex in (16, 40):
            ctx.arc(ex, hy0 + 2, 6 + 6 * stare, 0, TAU)
            fill(ctx, "#ffffff")
            ctx.arc(ex + 2, hy0 + 2, 3.2, 0, TAU)
            fill(ctx, "#111")
    elif look_down:
        for ex in (16, 40):
            ctx.arc(ex, hy0 + 6, 6, 0.3, TAU / 2 - 0.3)
            ctx.set_line_width(3.5)
            src(ctx, "#1b1b1b")
            ctx.stroke()
    else:
        ell(ctx, 16, hy0 + 2, 6, 8)
        fill(ctx, "#1b1b1b")
        ell(ctx, 40, hy0 + 2, 5, 7)
        fill(ctx, "#1b1b1b")
    if sleep:
        pass
    elif stare > 0:
        line(ctx, 18, hy0 + 26, 42, hy0 + 26, 4, "#5a2b1b")
    elif grin > 0:  # слишком широкая улыбка
        ctx.move_to(4, hy0 + 18)
        ctx.curve_to(10, hy0 + 18 + 34 * grin, 50, hy0 + 18 + 34 * grin, 56, hy0 + 14)
        ctx.close_path()
        fill(ctx, "#ffffff")
        ctx.move_to(4, hy0 + 18)
        ctx.curve_to(10, hy0 + 18 + 34 * grin, 50, hy0 + 18 + 34 * grin, 56, hy0 + 14)
        ctx.close_path()
        ctx.set_line_width(3)
        src(ctx, "#5a2b1b")
        ctx.stroke()
        for k in range(4):
            line(ctx, 14 + k * 11, hy0 + 18, 14 + k * 11, hy0 + 18 + 24 * grin, 2, "#c9c2b8")
    else:
        ctx.arc(30, hy0 + 26, 10, 0.3, TAU / 2 - 0.3)
        ctx.set_line_width(4)
        src(ctx, "#5a2b1b")
        ctx.stroke()
    if p.mustache:
        ctx.move_to(14, hy0 + 20)
        ctx.curve_to(26, hy0 + 12, 40, hy0 + 12, 52, hy0 + 20)
        ctx.set_line_width(7)
        src(ctx, p.hair)
        ctx.stroke()
    if p.glasses and not (sleep and p.mask):
        for ex in (16, 40):
            ctx.arc(ex, hy0 + 2, 12, 0, TAU)
            ctx.set_line_width(3.5)
            src(ctx, "#111")
            ctx.stroke()
        line(ctx, 28, hy0 + 2, 28, hy0 + 2, 3.5, "#111")
        line(ctx, 4, hy0, -24, hy0 - 2, 3, "#111")
        ell(ctx, 12, hy0 - 2, 4, 3)
        fill(ctx, "#ffffff", 0.5)
    if p.headphones:
        ctx.arc(-4, hy0 - 4, 62, math.pi * 1.05, math.pi * 1.95)
        ctx.set_line_width(9)
        src(ctx, "#111827")
        ctx.stroke()
        rr(ctx, -42, hy0 - 12, 30, 40, 10)
        fill(ctx, "#ef4444" if int(p.seed) % 2 else "#111827")
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    return x


def particles_from(ctx, p, x, t_since, seed, n=46, colors=None):
    """Пиксельная пыль, в которую рассыпается человек."""
    r = random.Random(seed)
    cols = colors or p.colors()
    for i in range(n):
        px = x + (r.random() - 0.5) * 130 * p.sc
        py = p.y - r.random() * 470 * p.sc
        delay = (1 - (p.y - py) / (470 * p.sc)) * 0.0 + r.random() * 0.25
        k = clamp((t_since - delay) / 1.4)
        if k <= 0 or k >= 1:
            continue
        dx = (40 + r.random() * 160) * k + math.sin(k * 6 + i) * 20
        dy = -(120 + r.random() * 380) * ease_out(k, 2)
        sz = (8 + r.random() * 12) * p.sc * (1 - k * 0.6)
        ctx.save()
        ctx.translate(px + dx, py + dy)
        ctx.rotate(k * (r.random() - 0.5) * 6)
        ctx.rectangle(-sz / 2, -sz / 2, sz, sz)
        src(ctx, r.choice(cols), (1 - k) ** 1.2)
        ctx.fill()
        ctx.restore()


def mannequin(ctx, x, y, sc=1.0, head_turn=0.0, pose=0.0, color="#e9e4dc"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    line(ctx, 0, -10, 0, -160, 10, "#9ca3af")
    ell(ctx, 0, -6, 60, 12)
    fill(ctx, "#6b7280")
    dark = mix(hexc(color), hexc("#000000"), 0.18)
    rr(ctx, -60, -330, 120, 180, 40)
    fill(ctx, color)
    for side in (-1, 1):
        line(ctx, side * 58, -315, side * (70 + 30 * pose), -170, 26, dark)
    line(ctx, 0, -330, 0, -355, 30, dark)
    ell(ctx, 0 + head_turn * 10, -400, 52, 60)
    fill(ctx, color)
    # «тень» на лице, которая выдаёт поворот головы
    if head_turn:
        ell(ctx, head_turn * 26, -398, 18 * abs(head_turn), 44)
        fill(ctx, dark, 0.7)
    ctx.restore()


def stranger_shadow(ctx, x, y, h, step, alpha=0.85):
    """Вытянутая тень незнакомца на стене."""
    ctx.save()
    ctx.translate(x, y)
    s = h / 900
    ctx.scale(s * 0.75, s)
    ctx.push_group()
    a = math.sin(step * math.pi) * 0.35
    for side in (-1, 1):
        aa = a * side
        line(ctx, side * 28, -380, side * 28 + math.sin(aa) * 380, -380 + math.cos(aa) * 380, 60, "#000")
    ctx.move_to(-80, -720)
    ctx.line_to(80, -720)
    ctx.line_to(70, -360)
    ctx.line_to(-70, -360)
    ctx.close_path()
    fill(ctx, "#000")
    for side in (-1, 1):
        line(ctx, side * 80, -700, side * 100, -330, 40, "#000")
    ell(ctx, 0, -800, 70, 86)
    fill(ctx, "#000")
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)
    ctx.restore()


# ---------------------------------------------------------------- ОКРУЖЕНИЕ
def skyline(ctx, seed, x0, x1, base, hmin, hmax, col, win_col=None, win_p=0.0, wmin=90, wmax=200,
            t=0.0, lit_seed=0):
    r = random.Random(seed)
    x = x0
    while x < x1:
        w = r.uniform(wmin, wmax)
        h = r.uniform(hmin, hmax)
        ctx.rectangle(x, base - h, w + 1, h + 400)
        fill(ctx, col)
        if r.random() < 0.3:
            ctx.rectangle(x + w * 0.4, base - h - 40, 6, 40)
            fill(ctx, col)
        if win_col:
            cols = int(w // 34)
            rows = int(h // 46)
            rl = random.Random(seed * 31 + int(x) + lit_seed)
            for cy in range(rows):
                for cx in range(cols):
                    on = rl.random() < win_p
                    if on:
                        ctx.rectangle(x + 12 + cx * 34, base - h + 18 + cy * 46, 16, 24)
                        fill(ctx, win_col)
        x += w + r.uniform(0, 14)


def sky(ctx, w, h, kind):
    P = {
        "morning": ["#9fd3f0", "#cfe8f3", "#ffe8c2"],
        "day": ["#4aa8e8", "#8fd0f5", "#d8f0fb"],
        "sunset": ["#3b2a6b", "#c2416b", "#ff9a3c"],
        "night": ["#05060f", "#0c1430", "#1c2850"],
        "dusk": ["#1d2347", "#4a3870", "#8a5470"],
    }[kind]
    vgrad(ctx, -2000, -2000, 6000, 2000 + h * 0.75, [(0, P[0]), (0.75, P[1]), (1, P[2])])
    vgrad(ctx, -2000, h * 0.75 - 1, 6000, 4000, [(0, P[2]), (1, P[2])])


def stars(ctx, seed, w, h, t, n=90):
    r = random.Random(seed)
    for i in range(n):
        x, y = r.uniform(-200, w + 200), r.uniform(-300, h)
        a = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * r.uniform(1, 3) + i))
        ctx.arc(x, y, r.uniform(1.2, 3), 0, TAU)
        fill(ctx, "#ffffff", a)


def dust(ctx, seed, w, h, t, n=40, col="#ffffff", a=0.25):
    r = random.Random(seed)
    for i in range(n):
        x0, y0 = r.uniform(0, w), r.uniform(0, h)
        sp = r.uniform(8, 25)
        x = (x0 + math.sin(t * 0.5 + i) * 30 + t * sp) % w
        y = (y0 - t * sp * 0.6) % h
        ctx.arc(x, y, r.uniform(2, 5), 0, TAU)
        fill(ctx, col, a * (0.5 + 0.5 * math.sin(t + i)))


def puff(ctx, x, y, t, seed, n=6, col="#cfd4da", life=1.6, rate=0.28, dx=-60, dy=-90, a=0.5):
    """Клубы пара/дыма из точки."""
    r = random.Random(seed)
    k0 = int(t / rate)
    for k in range(k0 - int(life / rate) - 1, k0 + 1):
        age = t - k * rate
        if age < 0 or age > life:
            continue
        rr_ = random.Random(seed * 1000 + k)
        u = age / life
        px = x + dx * u + math.sin(u * 4 + k) * 14
        py = y + dy * u
        rad = 14 + 50 * u * rr_.uniform(0.7, 1.2)
        ctx.arc(px, py, rad, 0, TAU)
        fill(ctx, col, a * (1 - u) ** 1.4)


def steam(ctx, x, y, t, h=160, a=0.55, n=3):
    for i in range(n):
        ctx.move_to(x + (i - 1) * 22, y)
        for k in range(1, 12):
            yy = y - k * h / 11
            xx = x + (i - 1) * 22 + math.sin(t * 2.2 + k * 0.6 + i * 2) * 14 * (k / 11)
            ctx.line_to(xx, yy)
        ctx.set_line_width(9)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        src(ctx, "#ffffff", a * (0.6 + 0.4 * math.sin(t * 1.5 + i)))
        ctx.stroke()


def speed_lines(ctx, w, h, t, n=26, a=0.5, seed=7, vertical=False):
    r = random.Random(seed)
    for i in range(n):
        y = r.uniform(0, h)
        L = r.uniform(150, 500)
        x = (r.uniform(0, w * 2) - t * r.uniform(2400, 4200)) % (w + L * 2) - L
        if vertical:
            line(ctx, y * w / h, x, y * w / h, x + L, r.uniform(3, 8), "#ffffff", a)
        else:
            line(ctx, x, y, x + L, y, r.uniform(3, 8), "#ffffff", a)


def phone_body(ctx, x, y, w, h, screen_fn=None, on=1.0):
    rr(ctx, x - w / 2 - 10, y - h / 2 - 10, w + 20, h + 20, 46)
    fill(ctx, "#15161b")
    rr(ctx, x - w / 2, y - h / 2, w, h, 38)
    fill(ctx, "#05060a")
    if screen_fn and on > 0:
        ctx.save()
        rr(ctx, x - w / 2, y - h / 2, w, h, 38)
        ctx.clip()
        ctx.push_group()
        screen_fn(ctx, x - w / 2, y - h / 2, w, h)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(on)
        ctx.restore()
    rr(ctx, x - 50, y - h / 2 + 14, 100, 26, 13)
    fill(ctx, "#000")


def burger(ctx, x, y, s):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.arc(0, -10, 60, TAU / 2, TAU)
    fill(ctx, "#e7a14a")
    rr(ctx, -64, -12, 128, 16, 8)
    fill(ctx, "#4caf50")
    rr(ctx, -60, 2, 120, 22, 10)
    fill(ctx, "#6b3a1e")
    rr(ctx, -62, 22, 124, 10, 5)
    fill(ctx, "#ffcc33")
    rr(ctx, -58, 30, 116, 24, 12)
    fill(ctx, "#e7a14a")
    for i in range(5):
        ell(ctx, -30 + i * 15, -40 + (i % 2) * 8, 4, 2.5)
        fill(ctx, "#fff3d6")
    ctx.restore()


def donut(ctx, x, y, s, col="#f472b6"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.arc(0, 0, 50, 0, TAU)
    fill(ctx, "#d79a59")
    ctx.arc(0, -3, 44, 0, TAU)
    fill(ctx, col)
    ctx.arc(0, -3, 16, 0, TAU)
    fill(ctx, "#d79a59")
    r = random.Random(int(x * 7 + y))
    for i in range(10):
        a = r.uniform(0, TAU)
        d = r.uniform(22, 38)
        line(ctx, math.cos(a) * d, math.sin(a) * d - 3, math.cos(a) * d + 6, math.sin(a) * d + 3, 4,
             r.choice(["#fff", "#facc15", "#60a5fa", "#34d399"]))
    ctx.restore()


def pizza(ctx, x, y, s, rot=0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ctx.move_to(0, -70)
    ctx.line_to(55, 50)
    ctx.line_to(-55, 50)
    ctx.close_path()
    fill(ctx, "#facc15")
    rr(ctx, -60, 40, 120, 20, 10)
    fill(ctx, "#c2772f")
    for px, py in ((0, -20), (-18, 20), (20, 18)):
        ctx.arc(px, py, 10, 0, TAU)
        fill(ctx, "#dc2626")
    ctx.restore()


def soda(ctx, x, y, s):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(-34, -60)
    ctx.line_to(34, -60)
    ctx.line_to(26, 60)
    ctx.line_to(-26, 60)
    ctx.close_path()
    fill(ctx, "#ef4444")
    rr(ctx, -38, -70, 76, 14, 6)
    fill(ctx, "#fafafa")
    line(ctx, 8, -70, 20, -120, 6, "#fafafa")
    ctx.restore()


def vignette(ctx, w, h, a=0.55, col=(0, 0, 0)):
    g = cairo.RadialGradient(w / 2, h / 2, h * 0.28, w / 2, h / 2, h * 0.75)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], 0)
    g.add_color_stop_rgba(1, col[0], col[1], col[2], a)
    ctx.set_source(g)
    ctx.paint()
