"""Детализированные предметы: посуда, еда, мебель, улица. Тени, градиенты, блики."""
import math
import random

import cairo

from draw import TAU, clamp, ell, fill, glow, hexc, line, mix, rr, src, text


def lgrad(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *(hexc(c) if isinstance(c, str) else c))
    ctx.set_source(g)


def shade(c, k):
    """k<0 темнее, k>0 светлее."""
    base = hexc(c) if isinstance(c, str) else c
    return mix(base, (0, 0, 0, base[3]) if k < 0 else (1, 1, 1, base[3]), abs(k))


def shadow(ctx, x, y, rx, ry, a=0.35):
    ctx.new_path()
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
    g.add_color_stop_rgba(0, 0, 0, 0, a)
    g.add_color_stop_rgba(0.6, 0, 0, 0, a * 0.5)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.arc(0, 0, 1, 0, TAU)
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()


def outline(ctx, w=4, c="#00000055"):
    ctx.set_line_width(w)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    src(ctx, c)
    ctx.stroke()


# ------------------------------------------------------------ КОФЕ
def coffee_cup(ctx, x, y, s=1.0, t=0.0, heart=True):
    """Чашка капучино на блюдце с ложкой. (x,y) — центр блюдца."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 20, 40, 300, 70, 0.45)
    # блюдце
    ell(ctx, 0, 10, 250, 66)
    lgrad(ctx, 0, -60, 0, 80, [(0, "#ffffff"), (1, "#c9c4bb")])
    ctx.fill()
    ell(ctx, 0, 4, 200, 48)
    lgrad(ctx, 0, -40, 0, 50, [(0, "#d8d3ca"), (1, "#f7f4ef")])
    ctx.fill()
    # ложка
    ctx.save()
    ctx.translate(150, 10)
    ctx.rotate(-0.35)
    rr(ctx, -10, -8, 150, 16, 8)
    lgrad(ctx, 0, -8, 0, 8, [(0, "#f1f3f5"), (1, "#8a9099")])
    ctx.fill()
    ell(ctx, -20, 0, 42, 24)
    lgrad(ctx, 0, -24, 0, 24, [(0, "#ffffff"), (1, "#8a9099")])
    ctx.fill()
    ctx.restore()
    # тень чашки на блюдце
    ell(ctx, 10, 6, 140, 30)
    fill(ctx, "#000000", 0.18)
    # ручка
    ctx.arc(150, -110, 52, -1.45, 1.45)
    ctx.set_line_width(26)
    src(ctx, "#e7e3dc")
    ctx.stroke()
    ctx.arc(150, -110, 52, -1.2, 0.2)
    ctx.set_line_width(8)
    src(ctx, "#ffffff")
    ctx.stroke()
    # корпус
    ctx.move_to(-150, -210)
    ctx.line_to(150, -210)
    ctx.curve_to(148, -60, 90, 2, 0, 2)
    ctx.curve_to(-90, 2, -148, -60, -150, -210)
    ctx.close_path()
    lgrad(ctx, -150, 0, 150, 0, [(0, "#d6d1c8"), (0.35, "#ffffff"), (0.7, "#f1ede6"), (1, "#bdb7ad")])
    ctx.fill()
    # блик
    ctx.move_to(-110, -190)
    ctx.curve_to(-112, -120, -90, -60, -60, -30)
    ctx.set_line_width(12)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    src(ctx, "#ffffff", 0.85)
    ctx.stroke()
    # полоска-декор
    ctx.move_to(-146, -170)
    ctx.curve_to(-60, -160, 60, -160, 146, -170)
    ctx.set_line_width(10)
    src(ctx, "#c0392b", 0.85)
    ctx.stroke()
    # кромка и пенка
    ell(ctx, 0, -210, 150, 34)
    src(ctx, "#f4f1ea")
    ctx.fill()
    ell(ctx, 0, -206, 134, 27)
    g = cairo.RadialGradient(0, -206, 10, 0, -206, 134)
    g.add_color_stop_rgba(0, *hexc("#e9cfa6"))
    g.add_color_stop_rgba(0.75, *hexc("#b47a45"))
    g.add_color_stop_rgba(1, *hexc("#6e3f1d"))
    ctx.set_source(g)
    ctx.save()
    ctx.translate(0, -206)
    ctx.scale(1, 27 / 134)
    ctx.arc(0, 0, 134, 0, TAU)
    ctx.restore()
    ctx.fill()
    if heart:  # латте-арт
        ctx.save()
        ctx.translate(0, -206)
        ctx.scale(1, 0.24)
        ctx.move_to(0, 60)
        ctx.curve_to(-90, 0, -60, -70, 0, -30)
        ctx.curve_to(60, -70, 90, 0, 0, 60)
        ctx.restore()
        fill(ctx, "#fbf3e4", 0.92)
        line(ctx, 0, -214, 0, -196, 3, "#c79a6b")
    ctx.restore()


def croissant(ctx, x, y, s=1.0, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    shadow(ctx, 10, 30, 190, 40, 0.35)
    segs = [(-150, 18, 34, 0.5), (-95, 2, 46, 0.25), (-35, -8, 56, 0.0), (30, -8, 56, 0.0), (90, 2, 46, -0.25),
            (145, 18, 34, -0.5)]
    for i, (sx, sy, r, a) in enumerate(segs):
        ctx.save()
        ctx.translate(sx, sy)
        ctx.rotate(a)
        ell(ctx, 0, 0, r * 0.95, r)
        g = cairo.LinearGradient(0, -r, 0, r)
        g.add_color_stop_rgba(0, *hexc("#f6c66b"))
        g.add_color_stop_rgba(0.5, *hexc("#d98c2b"))
        g.add_color_stop_rgba(1, *hexc("#9c5a17"))
        ctx.set_source(g)
        ctx.fill()
        ctx.arc(0, -r * 0.1, r * 0.75, TAU * 0.6, TAU * 0.9)
        ctx.set_line_width(4)
        src(ctx, "#8a4c12", 0.6)
        ctx.stroke()
        ctx.restore()
    for i in range(14):  # сахарная пудра
        r = random.Random(i)
        ctx.arc(r.uniform(-120, 120), r.uniform(-50, 0), r.uniform(2, 4), 0, TAU)
        fill(ctx, "#fffaf0", 0.8)
    ctx.restore()


def sugar_packet(ctx, x, y, rot, col="#e74c3c", word="SUGAR"):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    shadow(ctx, 6, 14, 80, 18, 0.3)
    rr(ctx, -70, -26, 140, 52, 6)
    fill(ctx, "#ffffff")
    rr(ctx, -70, -26, 34, 52, 6)
    fill(ctx, col)
    text(ctx, word, 14, 0, 22, col)
    ctx.restore()


def napkin_fork(ctx, x, y, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    shadow(ctx, 8, 10, 120, 70, 0.25)
    rr(ctx, -110, -70, 220, 140, 8)
    fill(ctx, "#f8f6f1")
    line(ctx, -110, 0, 110, 0, 2, "#d8d3c8")
    rr(ctx, -12, -140, 24, 200, 10)
    lgrad(ctx, -12, 0, 12, 0, [(0, "#9aa1aa"), (0.5, "#f4f6f8"), (1, "#7b828c")])
    ctx.fill()
    for k in range(4):
        rr(ctx, -16 + k * 10, -200, 6, 70, 3)
        fill(ctx, "#c9ced4")
    ctx.restore()


def flower_vase(ctx, x, y, s=1.0, t=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 10, 60, 16, 0.3)
    for k, (a, h, c) in enumerate(((-0.3, 210, "#f472b6"), (0.05, 260, "#facc15"), (0.35, 200, "#f87171"))):
        sway = math.sin(t * 1.3 + k) * 0.03
        ex, ey = math.sin(a + sway) * h, -math.cos(a + sway) * h
        line(ctx, 0, -60, ex, ey, 6, "#2f855a")
        ell(ctx, ex * 0.55 + 14, ey * 0.55, 20, 9)
        fill(ctx, "#38a169")
        for p in range(6):
            pa = p * TAU / 6
            ctx.arc(ex + math.cos(pa) * 18, ey + math.sin(pa) * 18, 14, 0, TAU)
            fill(ctx, c)
        ctx.arc(ex, ey, 11, 0, TAU)
        fill(ctx, "#fde68a")
    ctx.move_to(-40, -90)
    ctx.curve_to(-60, -40, -50, 0, -30, 6)
    ctx.line_to(30, 6)
    ctx.curve_to(50, 0, 60, -40, 40, -90)
    ctx.close_path()
    lgrad(ctx, -50, 0, 50, 0, [(0, "#7dd3fc80"), (0.4, "#e0f2fe"), (1, "#38bdf880")])
    ctx.fill()
    ctx.restore()


# ------------------------------------------------------------ ЕДА
def plate(ctx, x, y, rx, ry):
    shadow(ctx, x + 10, y + ry * 0.5, rx * 1.1, ry * 1.1, 0.35)
    ell(ctx, x, y, rx, ry)
    lgrad(ctx, 0, y - ry, 0, y + ry, [(0, "#ffffff"), (1, "#cfcac2")])
    ctx.fill()
    ell(ctx, x, y - ry * 0.05, rx * 0.72, ry * 0.68)
    lgrad(ctx, 0, y - ry, 0, y + ry, [(0, "#dcd7cf"), (1, "#ffffff")])
    ctx.fill()


def burger2(ctx, x, y, s=1.0):
    """Бургер с тенями: булка с кунжутом, салат, томат, сыр, котлета."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rr(ctx, -82, 20, 164, 38, 18)  # нижняя булка
    lgrad(ctx, 0, 20, 0, 58, [(0, "#e8a85a"), (1, "#b06f2c")])
    ctx.fill()
    rr(ctx, -88, -6, 176, 34, 16)  # котлета
    lgrad(ctx, 0, -6, 0, 28, [(0, "#7a4423"), (1, "#3f200e")])
    ctx.fill()
    for k in range(7):
        line(ctx, -70 + k * 22, 2, -60 + k * 22, 18, 4, "#2b1508", 0.6)
    ctx.move_to(-92, -10)  # сыр с подтёками
    for k in range(9):
        xx = -92 + k * 23
        ctx.line_to(xx + 11, -10 + (22 if k % 2 == 0 else 6))
        ctx.line_to(xx + 23, -10)
    ctx.line_to(92, -20)
    ctx.line_to(-92, -20)
    ctx.close_path()
    fill(ctx, "#ffc93c")
    rr(ctx, -84, -32, 168, 16, 8)  # томат
    fill(ctx, "#e53935")
    ctx.move_to(-96, -30)  # салат волной
    for k in range(13):
        ctx.line_to(-96 + k * 16, -30 + (10 if k % 2 else -6))
    ctx.line_to(96, -40)
    ctx.line_to(-96, -40)
    ctx.close_path()
    fill(ctx, "#43a047")
    ctx.move_to(-86, -36)  # верхняя булка
    ctx.curve_to(-86, -120, 86, -120, 86, -36)
    ctx.close_path()
    g = cairo.RadialGradient(-20, -100, 10, 0, -60, 110)
    g.add_color_stop_rgba(0, *hexc("#f8c57a"))
    g.add_color_stop_rgba(1, *hexc("#b8702a"))
    ctx.set_source(g)
    ctx.fill()
    r = random.Random(int(x * 3 + y))
    for k in range(9):
        ctx.save()
        ctx.translate(r.uniform(-55, 55), r.uniform(-95, -55))
        ctx.rotate(r.uniform(-1, 1))
        ell(ctx, 0, 0, 6, 3.5)
        fill(ctx, "#fff4dc")
        ctx.restore()
    ctx.restore()


def fries(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    r = random.Random(int(x))
    for k in range(13):
        xx = -55 + k * 9 + r.uniform(-3, 3)
        rr(ctx, xx, -150 + r.uniform(0, 40), 14, 140, 4)
        lgrad(ctx, xx, 0, xx + 14, 0, [(0, "#ffd54f"), (1, "#f0a818")])
        ctx.fill()
    ctx.move_to(-70, -70)
    ctx.line_to(70, -70)
    ctx.line_to(55, 40)
    ctx.line_to(-55, 40)
    ctx.close_path()
    lgrad(ctx, -70, 0, 70, 0, [(0, "#b71c1c"), (0.5, "#ef3b2d"), (1, "#b71c1c")])
    ctx.fill()
    ctx.arc(0, -10, 22, 0, TAU)
    fill(ctx, "#ffd54f")
    ctx.restore()


def pizza_whole(ctx, x, y, rx, ry, cut=1):
    """Пицца в открытой коробке, один кусок вынут."""
    shadow(ctx, x + 10, y + ry * 0.6, rx * 1.3, ry * 1.2, 0.35)
    rr(ctx, x - rx * 1.15, y - ry * 1.2, rx * 2.3, ry * 2.4, 10)
    fill(ctx, "#d6b48a")
    rr(ctx, x - rx * 1.08, y - ry * 1.12, rx * 2.16, ry * 2.24, 8)
    fill(ctx, "#c49d6f")
    ell(ctx, x, y, rx, ry)
    fill(ctx, "#d48a3a")
    ell(ctx, x, y, rx * 0.88, ry * 0.86)
    fill(ctx, "#f4c542")
    # вынутый кусок
    ctx.move_to(x, y)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1.01, -0.5, 0.35)
    ctx.restore()
    ctx.close_path()
    fill(ctx, "#c49d6f")
    r = random.Random(int(x + y))
    for k in range(14):
        a, d = r.uniform(0.4, TAU - 0.55), r.uniform(0.15, 0.75)
        px, py = x + math.cos(a) * rx * d, y + math.sin(a) * ry * d
        ell(ctx, px, py, rx * 0.09, ry * 0.09)
        fill(ctx, "#c62828")
        ell(ctx, px - rx * 0.02, py - ry * 0.02, rx * 0.03, ry * 0.03)
        fill(ctx, "#ef5350")
    for k in range(10):
        a, d = r.uniform(0.4, TAU - 0.55), r.uniform(0.1, 0.8)
        ell(ctx, x + math.cos(a) * rx * d, y + math.sin(a) * ry * d, 7, 4)
        fill(ctx, "#2e7d32")
    for k in range(6):
        a = 0.35 + k * (TAU - 0.85) / 6
        line(ctx, x, y, x + math.cos(a) * rx * 0.88, y + math.sin(a) * ry * 0.86, 2, "#b57a2a", 0.6)


def donut2(ctx, x, y, s=1.0, icing="#f472b6"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s * 0.6)
    ctx.new_path()
    ctx.arc(0, 0, 55, 0, TAU)
    ctx.arc_negative(0, 0, 18, TAU, 0)
    lgrad(ctx, 0, -55, 0, 55, [(0, "#e7b071"), (1, "#a8692e")])
    ctx.fill()
    ctx.new_path()
    ctx.arc(0, -6, 48, 0, TAU)
    ctx.arc_negative(0, -6, 20, TAU, 0)
    src(ctx, icing)
    ctx.fill()
    ctx.new_path()
    r = random.Random(int(x * 13 + y))
    for k in range(14):
        a, d = r.uniform(0, TAU), r.uniform(26, 42)
        ctx.save()
        ctx.translate(math.cos(a) * d, math.sin(a) * d - 6)
        ctx.rotate(r.uniform(0, 3))
        rr(ctx, -6, -2, 12, 4, 2)
        fill(ctx, r.choice(["#ffffff", "#facc15", "#60a5fa", "#34d399", "#f87171"]))
        ctx.restore()
    ctx.arc(-18, -26, 10, 3.6, 5.0)
    ctx.set_line_width(5)
    src(ctx, "#ffffff", 0.6)
    ctx.stroke()
    ctx.restore()


def soda_cup(ctx, x, y, s=1.0, col="#ef4444"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 6, 64, 50, 12, 0.35)
    ctx.move_to(-42, -70)
    ctx.line_to(42, -70)
    ctx.line_to(32, 64)
    ctx.line_to(-32, 64)
    ctx.close_path()
    lgrad(ctx, -42, 0, 42, 0, [(0, shade(col, -0.3)), (0.4, col), (1, shade(col, -0.35))])
    ctx.fill()
    ctx.arc(0, 0, 20, 0, TAU)
    fill(ctx, "#ffffff", 0.9)
    rr(ctx, -48, -84, 96, 18, 8)
    fill(ctx, "#f5f5f5")
    rr(ctx, 4, -170, 10, 92, 4)
    fill(ctx, "#ffffff")
    rr(ctx, 4, -170, 10, 30, 4)
    fill(ctx, col)
    ctx.restore()


def cake_stand(ctx, x, y, w, h):
    """Двухъярусная подставка."""
    line(ctx, x, y - h, x, y, 12, "#d4af37")
    for k, (yy, ww) in enumerate(((y, w), (y - h, w * 0.65))):
        ell(ctx, x, yy, ww, ww * 0.22)
        lgrad(ctx, 0, yy - ww * 0.22, 0, yy + ww * 0.22, [(0, "#ffffff"), (1, "#c9c3b8")])
        ctx.fill()
        ell(ctx, x, yy + ww * 0.2, ww, 6)
        fill(ctx, "#d4af37")


# ------------------------------------------------------------ ДОМ / МЕБЕЛЬ
def plant(ctx, x, y, s=1.0, t=0.0, pot="#c2410c"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 4, 80, 16, 0.3)
    for k in range(9):
        a = -1.2 + k * 0.3 + math.sin(t * 1.1 + k) * 0.03
        L = 150 + (k % 3) * 40
        ex, ey = math.sin(a) * L, -math.cos(a) * L - 80
        ctx.move_to(0, -80)
        ctx.curve_to(ex * 0.3, ey * 0.6, ex * 0.8, ey * 0.9, ex, ey)
        ctx.curve_to(ex * 0.9 + 18, ey * 0.7, ex * 0.4 + 12, -90, 0, -80)
        fill(ctx, "#2f855a" if k % 2 else "#38a169")
        line(ctx, 0, -80, ex * 0.85, ey * 0.85, 2, "#1f5f3d", 0.6)
    ctx.move_to(-62, -90)
    ctx.line_to(62, -90)
    ctx.line_to(48, 0)
    ctx.line_to(-48, 0)
    ctx.close_path()
    lgrad(ctx, -62, 0, 62, 0, [(0, shade(pot, -0.25)), (0.4, pot), (1, shade(pot, -0.3))])
    ctx.fill()
    rr(ctx, -70, -104, 140, 22, 6)
    fill(ctx, shade(pot, 0.1))
    ctx.restore()


def curtain(ctx, x, y, w, h, col="#c0392b", t=0.0, side=1):
    for k in range(6):
        xx = x + k * w / 6
        sway = math.sin(t * 0.8 + k) * 4
        ctx.move_to(xx, y)
        ctx.curve_to(xx + sway, y + h * 0.4, xx - sway, y + h * 0.7, xx + sway * side, y + h)
        ctx.line_to(xx + w / 6 + sway * side, y + h)
        ctx.curve_to(xx + w / 6 - sway, y + h * 0.7, xx + w / 6 + sway, y + h * 0.4, xx + w / 6, y)
        ctx.close_path()
        lgrad(ctx, xx, 0, xx + w / 6, 0, [(0, shade(col, -0.25)), (0.5, col), (1, shade(col, -0.15))])
        ctx.fill()
    rr(ctx, x - 20, y - 18, w + 40, 18, 9)
    fill(ctx, "#5b3a22")


def poster(ctx, x, y, w, h, kind=0, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    shadow(ctx, 8, 12, w * 0.6, h * 0.6, 0.18)
    rr(ctx, -w / 2, -h / 2, w, h, 4)
    fill(ctx, "#fdfcf8")
    if kind == 0:  # космос
        rr(ctx, -w / 2 + 12, -h / 2 + 12, w - 24, h - 24, 2)
        fill(ctx, "#1e1b4b")
        ctx.arc(0, -h * 0.08, w * 0.22, 0, TAU)
        fill(ctx, "#f59e0b")
        ell(ctx, 0, -h * 0.08, w * 0.36, w * 0.07)
        ctx.set_line_width(5)
        src(ctx, "#fde68a")
        ctx.stroke()
        for k in range(10):
            r = random.Random(k)
            ctx.arc(r.uniform(-w / 2.6, w / 2.6), r.uniform(-h / 2.6, h / 2.6), 2.5, 0, TAU)
            fill(ctx, "#ffffff")
        text(ctx, "SPACE", 0, h * 0.33, w * 0.16, "#fde68a")
    else:  # горы
        rr(ctx, -w / 2 + 12, -h / 2 + 12, w - 24, h - 24, 2)
        fill(ctx, "#bae6fd")
        ctx.move_to(-w / 2 + 12, h / 2 - 12)
        ctx.line_to(-w * 0.15, -h * 0.15)
        ctx.line_to(w * 0.05, h * 0.1)
        ctx.line_to(w * 0.22, -h * 0.25)
        ctx.line_to(w / 2 - 12, h / 2 - 12)
        ctx.close_path()
        fill(ctx, "#334155")
        ctx.arc(w * 0.25, -h * 0.32, w * 0.08, 0, TAU)
        fill(ctx, "#fbbf24")
    line(ctx, 0, -h / 2 - 2, 0, -h / 2 + 6, 10, "#ef4444")
    ctx.restore()


def bookshelf(ctx, x, y, w, rows=2, seed=1):
    r = random.Random(seed)
    for k in range(rows):
        yy = y + k * 130
        rr(ctx, x, yy + 110, w, 16, 3)
        fill(ctx, "#6b4226")
        xx = x + 10
        while xx < x + w - 30:
            bw = r.uniform(18, 34)
            bh = r.uniform(70, 105)
            tilt = 0 if r.random() > 0.15 else 0.15
            ctx.save()
            ctx.translate(xx, yy + 110)
            ctx.rotate(tilt)
            rr(ctx, 0, -bh, bw, bh, 3)
            fill(ctx, r.choice(["#b91c1c", "#1d4ed8", "#15803d", "#a16207", "#7e22ce", "#334155", "#be185d"]))
            line(ctx, 3, -bh * 0.8, bw - 3, -bh * 0.8, 3, "#ffffff", 0.5)
            ctx.restore()
            xx += bw + 3 + (12 if tilt else 0)


def table_lamp(ctx, x, y, s=1.0, on=True):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if on:
        glow(ctx, 0, -150, 260, "#ffd27a", 0.45)
    ell(ctx, 0, 0, 50, 12)
    fill(ctx, "#5b3a22")
    line(ctx, 0, 0, 0, -120, 10, "#5b3a22")
    ctx.move_to(-70, -110)
    ctx.line_to(70, -110)
    ctx.line_to(45, -200)
    ctx.line_to(-45, -200)
    ctx.close_path()
    fill(ctx, "#fde7b0" if on else "#8a7d63")
    ctx.restore()


def rug(ctx, x, y, rx, ry, col="#9f1239"):
    ell(ctx, x, y, rx, ry)
    fill(ctx, col)
    ell(ctx, x, y, rx * 0.85, ry * 0.8)
    ctx.set_line_width(8)
    src(ctx, "#fde68a", 0.7)
    ctx.stroke()
    ell(ctx, x, y, rx * 0.5, ry * 0.45)
    ctx.set_line_width(6)
    src(ctx, "#fde68a", 0.5)
    ctx.stroke()


def slippers(ctx, x, y):
    for k in (-1, 1):
        ell(ctx, x + k * 40, y, 32, 16)
        fill(ctx, "#60a5fa")
        ell(ctx, x + k * 40 + 6, y - 4, 20, 9)
        fill(ctx, "#dbeafe")


def glass_water(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(-28, -90)
    ctx.line_to(28, -90)
    ctx.line_to(22, 0)
    ctx.line_to(-22, 0)
    ctx.close_path()
    fill(ctx, "#cfe8ff", 0.35)
    ctx.move_to(-25, -50)
    ctx.line_to(25, -50)
    ctx.line_to(22, 0)
    ctx.line_to(-22, 0)
    ctx.close_path()
    fill(ctx, "#7dd3fc", 0.45)
    line(ctx, -16, -80, -12, -10, 4, "#ffffff", 0.6)
    ctx.restore()


# ------------------------------------------------------------ УЛИЦА
def lamp_post(ctx, x, y, h=620, on=False):
    rr(ctx, x - 14, y - h, 28, h, 8)
    lgrad(ctx, x - 14, 0, x + 14, 0, [(0, "#1f2937"), (0.5, "#4b5563"), (1, "#111827")])
    ctx.fill()
    ctx.move_to(x, y - h + 10)
    ctx.curve_to(x, y - h - 60, x + 90, y - h - 70, x + 120, y - h - 40)
    ctx.set_line_width(14)
    src(ctx, "#1f2937")
    ctx.stroke()
    rr(ctx, x + 90, y - h - 46, 70, 26, 10)
    fill(ctx, "#1f2937")
    ell(ctx, x + 125, y - h - 18, 30, 8)
    fill(ctx, "#fff7cc" if on else "#d1d5db")
    rr(ctx, x - 24, y - 40, 48, 40, 6)
    fill(ctx, "#111827")


def tree(ctx, x, y, s=1.0, t=0.0, seed=0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 0, 120, 20, 0.3)
    rr(ctx, -18, -300, 36, 300, 12)
    fill(ctx, "#6b4226")
    r = random.Random(seed)
    for k in range(9):
        cx = r.uniform(-120, 120) + math.sin(t + k) * 4
        cy = -330 + r.uniform(-110, 60)
        ctx.arc(cx, cy, r.uniform(70, 110), 0, TAU)
        fill(ctx, r.choice(["#2f855a", "#38a169", "#276749"]))
    for k in range(6):
        ctx.arc(r.uniform(-100, 60), -380 + r.uniform(-60, 40), r.uniform(30, 50), 0, TAU)
        fill(ctx, "#68d391", 0.5)
    rr(ctx, -70, -16, 140, 16, 4)  # приствольная решётка
    fill(ctx, "#4b5563")
    ctx.restore()


def trash_bin(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 0, 60, 12, 0.3)
    rr(ctx, -46, -150, 92, 150, 10)
    lgrad(ctx, -46, 0, 46, 0, [(0, "#14532d"), (0.5, "#22c55e"), (1, "#14532d")])
    ctx.fill()
    rr(ctx, -54, -168, 108, 24, 8)
    fill(ctx, "#166534")
    for k in range(3):
        line(ctx, -26 + k * 26, -130, -26 + k * 26, -20, 5, "#14532d")
    ctx.restore()


def hydrant(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 0, 50, 10, 0.3)
    rr(ctx, -30, -110, 60, 110, 10)
    fill(ctx, "#dc2626")
    ctx.arc(0, -110, 30, TAU / 2, TAU)
    fill(ctx, "#b91c1c")
    rr(ctx, -50, -80, 100, 24, 8)
    fill(ctx, "#b91c1c")
    rr(ctx, -40, -10, 80, 12, 4)
    fill(ctx, "#7f1d1d")
    ctx.restore()


def parked_car(ctx, x, y, s=1.0, col="#3b82f6", door_open=False):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 0, 300, 24, 0.4)
    rr(ctx, -280, -150, 560, 110, 40)
    lgrad(ctx, 0, -150, 0, -40, [(0, shade(col, 0.15)), (1, shade(col, -0.25))])
    ctx.fill()
    ctx.move_to(-170, -145)
    ctx.line_to(-110, -230)
    ctx.line_to(120, -230)
    ctx.line_to(190, -145)
    ctx.close_path()
    fill(ctx, shade(col, -0.1))
    ctx.move_to(-150, -150)
    ctx.line_to(-100, -215)
    ctx.line_to(0, -215)
    ctx.line_to(0, -150)
    ctx.close_path()
    fill(ctx, "#bfdbfe")
    ctx.move_to(14, -150)
    ctx.line_to(14, -215)
    ctx.line_to(110, -215)
    ctx.line_to(165, -150)
    ctx.close_path()
    fill(ctx, "#bfdbfe")
    line(ctx, -40, -200, -10, -165, 8, "#ffffff", 0.6)
    ell(ctx, 268, -110, 14, 18)
    fill(ctx, "#fef9c3")
    rr(ctx, -284, -100, 20, 26, 6)
    fill(ctx, "#ef4444")
    if door_open:
        ctx.move_to(14, -225)
        ctx.line_to(-80, -260)
        ctx.line_to(-80, -60)
        ctx.line_to(14, -40)
        ctx.close_path()
        fill(ctx, shade(col, -0.2))
        ctx.move_to(8, -215)
        ctx.line_to(-70, -245)
        ctx.line_to(-70, -160)
        ctx.line_to(8, -150)
        ctx.close_path()
        fill(ctx, "#93c5fd")
    for wx in (-170, 170):
        ctx.arc(wx, -40, 58, 0, TAU)
        fill(ctx, "#111")
        ctx.arc(wx, -40, 30, 0, TAU)
        fill(ctx, "#9ca3af")
        ctx.arc(wx, -40, 10, 0, TAU)
        fill(ctx, "#4b5563")
    ctx.restore()


def awning(ctx, x, y, w, h, col):
    n = max(4, int(w / 60))
    for k in range(n):
        ctx.move_to(x + k * w / n, y)
        ctx.line_to(x + (k + 1) * w / n, y)
        ctx.line_to(x + (k + 1) * w / n + 12, y + h)
        ctx.line_to(x + k * w / n + 12, y + h)
        ctx.close_path()
        fill(ctx, col if k % 2 == 0 else "#f8fafc")
    for k in range(n):
        ctx.arc(x + (k + 0.5) * w / n + 12, y + h, w / n / 2, 0, TAU / 2)
        fill(ctx, col if k % 2 == 0 else "#f8fafc")


def newspaper(ctx, x, y, rot, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    rr(ctx, -60, -40, 120, 80, 3)
    fill(ctx, "#f1efe8")
    rr(ctx, -50, -32, 100, 16, 2)
    fill(ctx, "#333")
    for k in range(4):
        line(ctx, -50, -6 + k * 11, 50, -6 + k * 11, 3, "#999")
    ctx.restore()


def chair(ctx, x, y, s=1.0, col="#7c4a2d"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rr(ctx, -60, -260, 18, 260, 6)
    fill(ctx, col)
    rr(ctx, 42, -130, 18, 130, 6)
    fill(ctx, col)
    rr(ctx, -64, -140, 128, 20, 6)
    fill(ctx, shade(col, 0.15))
    rr(ctx, -64, -260, 18, 120, 6)
    fill(ctx, col)
    for k in range(3):
        rr(ctx, -64, -250 + k * 35, 100, 12, 6)
        fill(ctx, col)
    ctx.restore()


def hanging_lamp(ctx, x, y, L=200, on=True, col="#1f2937"):
    line(ctx, x, y - 2000, x, y, 4, "#111")
    ctx.move_to(x - 60, y + 40)
    ctx.curve_to(x - 50, y - 20, x + 50, y - 20, x + 60, y + 40)
    ctx.close_path()
    fill(ctx, col)
    if on:
        ell(ctx, x, y + 40, 40, 10)
        fill(ctx, "#fff3c4")
        glow(ctx, x, y + 80, 260, "#ffd27a", 0.35)


def bench(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 0, 200, 18, 0.3)
    for k in range(3):
        rr(ctx, -180, -110 - k * 30, 360, 20, 6)
        fill(ctx, "#a0522d")
    for k in (-150, 150):
        rr(ctx, k - 10, -110, 20, 110, 4)
        fill(ctx, "#374151")
    ctx.restore()


def water_tank(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 40, 40, 170, 140, 0.45)
    ctx.arc(0, 0, 130, 0, TAU)
    g = cairo.RadialGradient(-40, -40, 10, 0, 0, 140)
    g.add_color_stop_rgba(0, *hexc("#cbd5e1"))
    g.add_color_stop_rgba(1, *hexc("#64748b"))
    ctx.set_source(g)
    ctx.fill()
    for r in (100, 70, 40):
        ctx.arc(0, 0, r, 0, TAU)
        ctx.set_line_width(4)
        src(ctx, "#475569", 0.6)
        ctx.stroke()
    ctx.restore()


def ac_unit(ctx, x, y, s=1.0, t=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 30, 30, 130, 100, 0.45)
    rr(ctx, -110, -90, 220, 180, 12)
    fill(ctx, "#e5e7eb")
    ctx.arc(0, 0, 70, 0, TAU)
    fill(ctx, "#374151")
    for k in range(4):
        a = t * 3 + k * TAU / 4
        ell(ctx, math.cos(a) * 34, math.sin(a) * 34, 26, 12)
        fill(ctx, "#9ca3af")
    ctx.arc(0, 0, 12, 0, TAU)
    fill(ctx, "#111827")
    ctx.restore()


def paint_bucket(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 20, 20, 70, 60, 0.4)
    ctx.arc(0, 0, 55, 0, TAU)
    fill(ctx, "#cbd5e1")
    ctx.arc(0, 0, 45, 0, TAU)
    fill(ctx, "#e3261f")
    ell(ctx, -14, -12, 14, 8)
    fill(ctx, "#ff7a6e", 0.7)
    ctx.restore()


def mailboxes(ctx, x, y, cols=4, rows=3):
    rr(ctx, x - 8, y - 8, cols * 70 + 16, rows * 54 + 16, 6)
    fill(ctx, "#1f2937")
    for i in range(rows):
        for j in range(cols):
            rr(ctx, x + j * 70, y + i * 54, 62, 46, 4)
            fill(ctx, "#4b5563")
            rr(ctx, x + j * 70 + 10, y + i * 54 + 10, 40, 6, 3)
            fill(ctx, "#111")


def apartment_door(ctx, x, y, w=220, h=420, num="12"):
    rr(ctx, x - 10, y - h - 10, w + 20, h + 10, 6)
    fill(ctx, "#111")
    rr(ctx, x, y - h, w, h, 4)
    lgrad(ctx, x, 0, x + w, 0, [(0, "#3f2a1d"), (0.5, "#5c3d29"), (1, "#3a2619")])
    ctx.fill()
    for k in range(2):
        rr(ctx, x + 24, y - h + 30 + k * 190, w - 48, 160, 4)
        ctx.set_line_width(4)
        src(ctx, "#2a1a10")
        ctx.stroke()
    ctx.arc(x + w - 30, y - h / 2, 10, 0, TAU)
    fill(ctx, "#d4a849")
    text(ctx, num, x + w / 2, y - h + 20, 26, "#d4a849")


def sofa(ctx, x, y, w=760, col="#334155"):
    shadow(ctx, x, y + 10, w * 0.6, 30, 0.5)
    rr(ctx, x - w / 2, y - 330, w, 200, 60)
    lgrad(ctx, 0, y - 330, 0, y - 130, [(0, shade(col, 0.15)), (1, shade(col, -0.2))])
    ctx.fill()
    rr(ctx, x - w / 2 - 20, y - 170, w + 40, 150, 40)
    fill(ctx, shade(col, -0.05))
    for k in (-1, 1):
        rr(ctx, x + k * (w / 2 + 10) - 50, y - 260, 100, 250, 40)
        fill(ctx, shade(col, -0.15))
    for k in range(3):
        rr(ctx, x - w / 2 + 40 + k * (w - 80) / 3, y - 190, (w - 80) / 3 - 10, 40, 16)
        fill(ctx, shade(col, 0.08))
