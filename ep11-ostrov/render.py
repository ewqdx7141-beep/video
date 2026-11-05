"""Серия 11 «Остров» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
import argparse
import math
import os
import random
import subprocess
import sys
from multiprocessing import Pool

import cairo

from common import FPS, H, ROOT, TRANS, W, Timeline

sys.path.insert(0, os.path.join(ROOT, "..", "lib"))
from draw import *  # noqa: E402,F401,F403
from props import *  # noqa: E402,F401,F403

TL = Timeline()
EV = TL.ev
DOUBLE_RIM = "#7CFF6B"  # двойник: ядовито-зелёный контровой


def wl(i, word, n=0, end=False):
    return TL.wt(i, word, n, end) - TL.shots[i][0]


def cam(ctx, t, cx, cy, z, rot=0.0, shake=0.4):
    ctx.translate(W / 2 + nz(t * 1.3, 1) * 14 * shake, H / 2 + nz(t * 1.1, 2) * 14 * shake)
    ctx.rotate(rot + nz(t * 0.9, 3) * 0.008 * shake)
    ctx.scale(z, z)
    ctx.translate(-cx, -cy)


def blink_at(t, seed=0.0, every=3.1):
    ph = (t + seed) % every
    return clamp(1 - abs(ph - 0.08) / 0.08) if ph < 0.16 else 0.0


def typed(msg, t, t0, t1):
    n = int(round(len(msg) * seg(t, t0, t1)))
    return msg[:n]


# ------------------------------------------------------------------ общие элементы
def clock_digits(ctx, x, y, s, txt, glow_a=0.6, col="#ff3b30"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 70, 230, 30, 0.4)
    rr(ctx, -210, -90, 420, 170, 26)
    lgrad(ctx, 0, -90, 0, 80, [(0, "#2a2a30"), (1, "#0d0d10")])
    ctx.fill()
    rr(ctx, -190, -72, 380, 134, 16)
    fill(ctx, "#050506")
    glow(ctx, 0, -5, 260, col, 0.25 * glow_a)
    text(ctx, "8:88", 0, -5, 120, col, alpha=0.08)
    text(ctx, txt, 0, -5, 120, col)
    ctx.restore()


def me_avatar(ctx, x, y, r, t, double=False):
    ctx.save()
    ctx.arc(x, y, r, 0, TAU)
    ctx.clip()
    src(ctx, "#3f3f46")
    ctx.paint()
    hero_head(ctx, x, y + r * 0.15, r * 0.85, emo("crazy" if double else "calm"), t, rim_a=0.0)
    ctx.restore()


def chat_screen(msgs, t, typing=False, header="Я", double=False, glitch=0.0, flicker=0.0):
    """msgs: [(side, text, alpha)] side 0 — входящее, 1 — исходящее."""
    def f(c, x, y, w, h):
        vgrad(c, x, y, w, h, [(0, "#0c0c12"), (1, "#15151e")])
        c.rectangle(x, y, w, 180)
        fill(c, "#18181f")
        me_avatar(c, x + 90, y + 115, 42, t, double)
        text(c, header, x + 155, y + 100, 46, "#ffffff", align="left")
        text(c, "в сети" if not typing else "печатает…", x + 155, y + 145, 28, "#22c55e" if typing else "#71717a",
             align="left")
        text(c, "3:07", x + w - 40, y + 60, 26, "#a1a1aa", align="right")
        fs = 44
        yy = y + 230
        for side, s, a in msgs:
            if not s:
                continue
            rows, cur = [], ""
            for wd in s.split(" "):
                test = (cur + " " + wd).strip()
                if text_w(c, test, fs) > w - 170 and cur:
                    rows.append(cur)
                    cur = wd
                else:
                    cur = test
            rows.append(cur)
            bw = min(w - 70, max(text_w(c, r_, fs) for r_ in rows) + 60)
            bh = 36 + len(rows) * 58
            bx = x + 30 if side == 0 else x + w - 30 - bw
            rr(c, bx, yy, bw, bh, 30)
            fill(c, "#2a2a35" if side == 0 else "#2f7cf6", a)
            for i, row in enumerate(rows):
                text(c, row, bx + 30, yy + 46 + i * 58, fs, "#ffffff", align="left", alpha=a)
            yy += bh + 22
        if typing:
            rr(c, x + 30, yy, 150, 70, 30)
            fill(c, "#2a2a35")
            for i in range(3):
                c.arc(x + 70 + i * 36, yy + 35, 10, 0, TAU)
                fill(c, "#a1a1aa", 0.3 + 0.7 * ((t * 2.5 + i * 0.33) % 1 < 0.5))
        if glitch > 0:
            r = random.Random(int(t * 30))
            for i in range(int(6 + 14 * glitch)):
                c.rectangle(x, y + r.random() * h, w, r.uniform(4, 34))
                fill(c, r.choice(["#ff0040", "#00e5ff", "#ffffff", "#7CFF6B"]), 0.35 * glitch)
        if flicker > 0:
            c.rectangle(x, y, w, h)
            fill(c, "#000", flicker)
    return f


def hands_phone(ctx, t, screen, tremble=1.0, sc=1.0, cx=540, cy=1000):
    ctx.save()
    ctx.translate(cx + math.sin(t * 37) * 5 * tremble, cy + math.sin(t * 29) * 5 * tremble)
    ctx.scale(sc, sc)
    glow(ctx, 0, 0, 1100, "#60a5fa", 0.22)
    for side in (-1, 1):
        line(ctx, side * 600, 900, side * 380, 300, 150, HOOD)
        line(ctx, side * 640, 980, side * 420, 380, 30, HOOD_D, 0.5)
        ctx.arc(side * 340, 230, 90, 0, TAU)
        fill(ctx, HEAD)
    phone_body(ctx, 0, 0, 620, 1240, screen)
    ell(ctx, -150, -560, 140, 30)
    fill(ctx, "#ffffff", 0.05)
    for side in (-1, 1):
        ell(ctx, side * 320, 120, 48, 90)
        fill(ctx, HEAD)
    ctx.restore()







# ================================================================== ЛЕС И МЕДВЕДЬ
COL_A = "#f97316"
COL_B = "#e5e7eb"
OK = "#22c55e"
NO = "#ef4444"
FUR = "#5b3a1e"
FUR_D = "#3f2713"
FUR_L = "#7c5230"


def checkmark(ctx, x, y, s, col=OK, k=1.0):
    if k <= 0:
        return
    ctx.move_to(x - 30 * s, y)
    ctx.line_to(x - 30 * s + 22 * s * min(1, k * 2), y + 22 * s * min(1, k * 2))
    if k > 0.5:
        kk = (k - 0.5) * 2
        ctx.line_to(x - 8 * s + 44 * s * kk, y + 22 * s - 50 * s * kk)
    ctx.set_line_width(12 * s)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    src(ctx, col)
    ctx.stroke()


def crossmark(ctx, x, y, s, col=NO):
    line(ctx, x - 26 * s, y - 26 * s, x + 26 * s, y + 26 * s, 12 * s, col)
    line(ctx, x + 26 * s, y - 26 * s, x - 26 * s, y + 26 * s, 12 * s, col)


def step_card(ctx, t, t0, n, txt, good=True):
    k = back_out(seg(t, t0 - 0.1, t0 + 0.25))
    if k <= 0:
        return
    ctx.save()
    ctx.translate(540, 330)
    ctx.scale(max(0.02, k), max(0.02, k))
    rr(ctx, -470, -120, 940, 240, 34)
    fill(ctx, "#0b0b12", 0.9)
    rr(ctx, -470, -120, 200, 240, 34)
    fill(ctx, OK if good else NO)
    text(ctx, "ШАГ", -370, -40, 46, "#ffffff")
    text(ctx, str(n), -370, 40, 96, "#ffffff")
    words = txt.split("\n")
    for i, wtxt in enumerate(words):
        text(ctx, wtxt, 110, -30 + i * 70 - (len(words) - 1) * 10, 58, "#ffffff")
    ctx.restore()


def pine(ctx, x, y, s, col="#14532d", snow=True):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rr(ctx, -16, -120, 32, 130, 6)
    fill(ctx, "#3f2a1d")
    for k in range(5):
        w = 200 - k * 34
        yy = -120 - k * 110
        ctx.move_to(-w, yy)
        ctx.line_to(w, yy)
        ctx.line_to(0, yy - 190)
        ctx.close_path()
        fill(ctx, col)
        if snow:
            ctx.move_to(-w * 0.7, yy - 50)
            ctx.line_to(0, yy - 190)
            ctx.line_to(w * 0.7, yy - 50)
            ctx.line_to(w * 0.3, yy - 70)
            ctx.line_to(0, yy - 60)
            ctx.line_to(-w * 0.3, yy - 70)
            ctx.close_path()
            fill(ctx, "#f1f5f9", 0.9)
    ctx.restore()


def snowfall(ctx, t, n=80, a=0.8):
    r = random.Random(9)
    for i in range(n):
        x = (r.uniform(-300, 1400) + math.sin(t * 0.8 + i) * 30) % 1700 - 300
        y = (r.uniform(-400, 2400) + t * r.uniform(60, 140)) % 2600 - 400
        ctx.arc(x, y, r.uniform(3, 8), 0, TAU)
        fill(ctx, "#ffffff", a * r.uniform(0.5, 1))


def forest(ctx, t, dusk=0.0):
    vgrad(ctx, -1500, -1200, 4000, 2600, [(0, "#94a3b8"), (1, "#e2e8f0")])
    if dusk:
        ctx.rectangle(-1500, -1200, 4000, 2600)
        fill(ctx, "#1e1b4b", 0.5 * dusk)
    r = random.Random(4)
    for layer, (y, sc, col) in enumerate(((1250, 0.7, "#64748b"), (1350, 0.9, "#334155"), (1450, 1.15, "#1f3a2a"))):
        for i in range(14):
            pine(ctx, -900 + i * 240 + r.uniform(-60, 60), y + r.uniform(-20, 20), sc * r.uniform(0.85, 1.2), col)
    ctx.rectangle(-1500, 1400, 4000, 2000)
    lgrad(ctx, 0, 1400, 0, 2600, [(0, "#e2e8f0"), (1, "#f8fafc")])
    ctx.fill()
    for i in range(20):  # сугробы
        ell(ctx, -800 + i * 180, 1420 + (i % 3) * 30, 160, 30)
        fill(ctx, "#f8fafc")


def bear(ctx, x, y, s, t, stand=0.0, walk=None, facing=-1, roar=0.0):
    """Бурый медведь. stand 0 — на четырёх лапах, 1 — на задних. facing -1 смотрит влево."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * facing * -1, s)
    shadow(ctx, 0, 0, 260, 30, 0.35)
    ph = walk if walk is not None else 0
    if stand < 0.5:
        for k, lx in enumerate((-150, -60, 90, 170)):  # лапы
            a = math.sin(ph + k * 1.6) * 0.3 if walk is not None else 0
            line(ctx, lx, -140, lx + math.sin(a) * 60, 0, 70, FUR_D if k % 2 else FUR)
            ell(ctx, lx + math.sin(a) * 60 + 14, -6, 46, 22)
            fill(ctx, FUR_D)
        ell(ctx, 0, -200, 260, 140)  # туловище
        lgrad(ctx, 0, -340, 0, -60, [(0, FUR_L), (1, FUR_D)])
        ctx.fill()
        ell(ctx, 120, -280, 90, 60)  # холка
        fill(ctx, FUR_L)
        hx, hy = -230, -230
    else:
        for side in (-1, 1):
            line(ctx, side * 70, -260, side * 80, 0, 90, FUR_D)
            ell(ctx, side * 80 + 10, -6, 60, 26)
            fill(ctx, FUR_D)
        ell(ctx, 0, -470, 170, 270)
        lgrad(ctx, 0, -740, 0, -200, [(0, FUR_L), (1, FUR_D)])
        ctx.fill()
        ell(ctx, 0, -430, 100, 170)
        fill(ctx, FUR_L, 0.5)
        for side in (-1, 1):  # передние лапы с когтями
            ex, ey = side * 200, -720
            line(ctx, side * 120, -620, ex, ey, 70, FUR)
            ctx.arc(ex, ey, 46, 0, TAU)
            fill(ctx, FUR_D)
            for c in range(4):
                line(ctx, ex - 24 + c * 16, ey - 40, ex - 28 + c * 18, ey - 80, 7, "#f5f5f4")
        hx, hy = 0, -790
    # голова
    for side in (-1, 1):
        ctx.arc(hx + side * 70, hy - 80, 40, 0, TAU)
        fill(ctx, FUR)
        ctx.arc(hx + side * 70, hy - 80, 20, 0, TAU)
        fill(ctx, FUR_D)
    ctx.arc(hx, hy, 115, 0, TAU)
    fill(ctx, FUR)
    ell(ctx, hx - (40 if stand < 0.5 else 0), hy + 40, 70, 54)
    fill(ctx, "#a07850")
    ell(ctx, hx - (60 if stand < 0.5 else 0), hy + 16, 26, 18)
    fill(ctx, "#111")
    for side in (-1, 1):
        ex = hx + side * 46 - (30 if stand < 0.5 else 0)
        ctx.arc(ex, hy - 30, 13, 0, TAU)
        fill(ctx, "#111")
        ctx.arc(ex - 4, hy - 34, 4, 0, TAU)
        fill(ctx, "#ffffff")
    if roar > 0:
        ell(ctx, hx - (40 if stand < 0.5 else 0), hy + 80, 40, 40 * roar)
        fill(ctx, "#7f1d1d")
        for side in (-1, 1):
            ctx.move_to(hx + side * 20 - (40 if stand < 0.5 else 0), hy + 50)
            ctx.line_to(hx + side * 12 - (40 if stand < 0.5 else 0), hy + 74)
            ctx.line_to(hx + side * 4 - (40 if stand < 0.5 else 0), hy + 50)
            fill(ctx, "#f5f5f4")
    ctx.restore()


def backpack_item(c, x, y):
    pass


def hiker(ctx, x, y, sc, e, t, arms="relax", look=(0, 0), tremble=0.0, walk=None, back=False, tilt=0.0, legs=True):
    """Герой в тёплой куртке с рюкзаком и шапкой, изо рта пар."""
    rr(ctx, x - 90 * sc, y - 380 * sc, 180 * sc, 200 * sc, 30 * sc)  # рюкзак
    fill(ctx, "#166534")
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, tremble=tremble, walk=walk, back=back, tilt=tilt,
         legs=legs, rim="#e0f2fe", rim_a=0.6, hood=("#ea580c", "#9a3412"))
    if not back and tilt == 0:  # шапка
        hy = y - (455 if legs else 285) * sc
        ctx.arc(x, hy - 40 * sc, 118 * sc, math.pi * 1.05, math.pi * 1.95)
        ctx.close_path()
        fill(ctx, "#1d4ed8")
        ctx.arc(x, hy - 160 * sc, 26 * sc, 0, TAU)
        fill(ctx, "#f8fafc")
        rr(ctx, x - 118 * sc, hy - 78 * sc, 236 * sc, 30 * sc, 12 * sc)
        fill(ctx, "#1e40af")
        puff(ctx, x + 40 * sc, hy + 70 * sc, t, 11, n=4, col="#ffffff", life=1.0, rate=0.5, dx=80 * sc, dy=-60 * sc,
             a=0.4)




# ================================================================== ОСТРОВ
SAND = "#f4d9a0"
SAND_D = "#d9b874"
SEA = "#0ea5e9"
SEA_D = "#0369a1"
CAST = ("#f59e0b", "#b45309")       # выцветшая футболка героя


def palm(ctx, x, y, s, t, lean=0.15):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 60, 0, 160, 24, 0.25)
    ctx.move_to(-14, 0)
    ctx.curve_to(-10, -200, lean * 400, -380, lean * 520, -560)
    ctx.line_to(lean * 520 + 26, -556)
    ctx.curve_to(lean * 400 + 30, -380, 18, -200, 18, 0)
    ctx.close_path()
    fill(ctx, "#8b5a2b")
    for k in range(10):
        yy = -50 - k * 52
        xx = lean * (abs(yy) ** 1.02) * 0.92
        line(ctx, xx - 10, yy, xx + 16, yy - 6, 4, "#6b4226", 0.6)
    tx, ty = lean * 520 + 12, -560
    for k in range(7):
        a = -math.pi + k * math.pi / 6 + math.sin(t * 1.2 + k) * 0.06
        ex, ey = tx + math.cos(a) * 230, ty + math.sin(a) * 120 + 60
        ctx.move_to(tx, ty)
        ctx.curve_to(tx + math.cos(a) * 120, ty - 60, ex - math.cos(a) * 30, ey - 40, ex, ey)
        ctx.curve_to(ex - math.cos(a) * 60, ey - 10, tx + math.cos(a) * 80, ty - 10, tx, ty)
        fill(ctx, "#15803d" if k % 2 else "#16a34a")
    for k in range(3):
        ctx.arc(tx - 20 + k * 22, ty + 20, 16, 0, TAU)
        fill(ctx, "#78350f")
    ctx.restore()


def waves(ctx, t, y0, amp=12, col="#ffffff", a=0.6, n=8):
    for k in range(n):
        y = y0 + k * 34
        ctx.move_to(-1500, y)
        for i in range(60):
            x = -1500 + i * 70
            ctx.line_to(x, y + math.sin(x * 0.01 + t * 2 + k) * amp)
        ctx.set_line_width(4)
        src(ctx, col, a * (1 - k / n))
        ctx.stroke()


def beach(ctx, t, tide=0.0, breathe=0.0, dusk=0.0, sea_y=1150):
    """Пляж: небо, океан, линия прибоя, песок, пальмы, камни, крабы, чайки."""
    vgrad(ctx, -1500, -1200, 4000, 2400, [(0, "#38bdf8"), (1, "#bae6fd")])
    if dusk:
        ctx.rectangle(-1500, -1200, 4000, 2400)
        fill(ctx, "#7c2d12", 0.35 * dusk)
    ctx.arc(860, 260, 90, 0, TAU)
    fill(ctx, "#fef3c7")
    glow(ctx, 860, 260, 300, "#fde68a", 0.5)
    for k in range(3):  # облака
        cx = (k * 600 + t * 20) % 2400 - 700
        for j in range(4):
            ell(ctx, cx + j * 70, 360 + k * 70 + math.sin(j) * 10, 80, 36)
            fill(ctx, "#ffffff", 0.85)
    # чайки
    for k in range(4):
        x = (k * 380 + t * 60) % 1800 - 300
        y = 450 + math.sin(t * 2 + k) * 30 + k * 40
        ctx.move_to(x - 30, y)
        ctx.curve_to(x - 15, y - 16, x - 6, y - 10, x, y)
        ctx.curve_to(x + 6, y - 10, x + 15, y - 16, x + 30, y)
        ctx.set_line_width(5)
        src(ctx, "#1f2937")
        ctx.stroke()
    sy = sea_y + 260 * tide
    ctx.rectangle(-1500, 700, 4000, sy - 700 + 400)
    lgrad(ctx, 0, 700, 0, sy, [(0, SEA_D), (1, SEA)])
    ctx.fill()
    waves(ctx, t, 760, 8, "#ffffff", 0.35, 10)
    lift = math.sin(t * 1.4) * 18 * breathe
    ctx.save()
    ctx.translate(0, -lift)
    ctx.move_to(-1500, sy + 20)
    for i in range(60):
        x = -1500 + i * 70
        ctx.line_to(x, sy + math.sin(x * 0.012 + t * 2.2) * 10)
    ctx.line_to(2500, 4000)
    ctx.line_to(-1500, 4000)
    ctx.close_path()
    lgrad(ctx, 0, sy, 0, sy + 1200, [(0, "#fde68a"), (0.3, SAND), (1, SAND_D)])
    ctx.fill()
    line(ctx, -1500, sy + 6, 2500, sy + 6, 10, "#ffffff", 0.7)
    r = random.Random(5)
    for i in range(40):  # ракушки, камешки
        x, y = r.uniform(-800, 1800), sy + r.uniform(60, 1300)
        ell(ctx, x, y, r.uniform(6, 14), r.uniform(4, 8))
        fill(ctx, r.choice(["#fcd34d", "#fecaca", "#e5e7eb", "#a8a29e"]))
    for i, (x, y) in enumerate(((-250, sy + 300), (1250, sy + 380))):  # крабы
        cx = x + math.sin(t * 1.5 + i) * 40
        ell(ctx, cx, y, 36, 22)
        fill(ctx, "#dc2626")
        for side in (-1, 1):
            line(ctx, cx + side * 30, y, cx + side * 56, y - 20, 6, "#dc2626")
            ctx.arc(cx + side * 60, y - 24, 10, 0, TAU)
            fill(ctx, "#dc2626")
        for side in (-1, 1):
            ctx.arc(cx + side * 10, y - 22, 5, 0, TAU)
            fill(ctx, "#111")
    ctx.restore()
    palm(ctx, -200, sy + 700, 1.3, t, 0.2)
    palm(ctx, 1200, sy + 650, 1.15, t, -0.25)
    palm(ctx, 1500, sy + 900, 1.4, t, -0.18)


def castaway(ctx, x, y, sc, e, t, arms="relax", walk=None, look=(0, 0), back=False, tremble=0.0, item=None,
             legs=True):
    hero(ctx, x, y, sc, e, t, arms=arms, walk=walk, look=look, back=back, tremble=tremble, rim="#fde68a",
         rim_a=0.6, hood=CAST, hand_item=item, legs=legs)


def bar(ctx, x, y, w, k, col):
    rr(ctx, x, y, w, 26, 13)
    fill(ctx, "#334155")
    if k > 0:
        rr(ctx, x, y, max(26, w * k), 26, 13)
        fill(ctx, col)


# ================================================================== СЦЕНЫ
def s0_hook(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, lerp(1100, 1400, ease(seg(u, 0, D))), lerp(0.7, 0.9, ease(seg(u, 0, D))), shake=0.2)
    beach(ctx, t)
    wake = ease(seg(u, 1.0, 2.0))
    ctx.save()
    ctx.translate(540, 1900)
    ctx.rotate(lerp(-1.45, 0, wake))
    castaway(ctx, 0, 0, 1.0, emo("sleep") if wake < 0.3 else emo("shock"), t, arms="down")
    ctx.restore()
    ctx.restore()


def s1_look(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(200, 900, ease(seg(u, 0, D))), 1300, 0.6, shake=0.2)
    beach(ctx, t)
    castaway(ctx, 540, 1900, 1.0, emo("worry"), t, arms="shrug", look=(math.sin(t * 1.5), -0.3))
    ctx.restore()


def s2_water(ctx, t, u, D):
    rn = EV["rain"]
    sn = EV["sea_no"]
    ctx.save()
    cam(ctx, t, 540, 1450, 1.05, shake=0.25)
    beach(ctx, t, dusk=0.3 * seg(t, rn - 1, rn))
    rainy = seg(t, rn - 0.5, rn) * (1 - seg(t, sn, sn + 0.5))
    # большой лист и бутылка собирают дождь
    ctx.save()
    ctx.translate(780, 1880)
    ctx.move_to(-160, -40)
    ctx.curve_to(-60, -140, 80, -140, 160, -40)
    ctx.curve_to(60, 10, -60, 10, -160, -40)
    fill(ctx, "#15803d")
    rr(ctx, -30, -10, 60, 120, 14)
    fill(ctx, "#bae6fd", 0.8)
    lvl = seg(t, rn, sn)
    rr(ctx, -26, 106 - 100 * lvl, 52, 100 * lvl, 10)
    fill(ctx, "#38bdf8")
    ctx.restore()
    castaway(ctx, 380, 1950, 1.05, emo("determined"), t, arms="up", look=(0.4, -0.8))
    if rainy > 0:
        r = random.Random(int(t * 20))
        for i in range(70):
            x, y = r.uniform(-200, 1300), r.uniform(600, 2300)
            line(ctx, x, y, x - 10, y + 50, 3, "#e0f2fe", 0.7 * rainy)
    ctx.restore()
    step_card(ctx, t, EV["steps"][0], 1, "ВОДА\nСОБИРАЙ ДОЖДЬ")
    if t > sn:
        ctx.save()
        ctx.translate(840, 1150)
        ctx.arc(0, 0, 120, 0, TAU)
        fill(ctx, "#0b0b12", 0.85)
        ell(ctx, 0, 10, 60, 30)
        fill(ctx, SEA)
        text(ctx, "МОРЕ", 0, -50, 30, "#ffffff")
        crossmark(ctx, 0, 10, 2.0)
        ctx.restore()


def s3_fire(ctx, t, u, D):
    fl = EV["flame"]
    k = seg(t, fl - 0.3, fl + 0.8)
    ctx.save()
    cam(ctx, t, 560, 1700, lerp(1.2, 1.5, ease(seg(u, 0, D))), shake=0.25)
    beach(ctx, t, dusk=0.6)
    # лучковое сверло и костёр
    for j in range(6):
        line(ctx, 640 - 60 + j * 22, 1960, 700 - j * 22 + 40, 1900, 12, "#78350f")
    if k > 0:
        for j in range(5):
            a = (t * 3 + j / 5) % 1
            ell(ctx, 680 + math.sin(t * 7 + j) * 12, 1890 - a * 140 * k, 46 * (1 - a) * k, 80 * (1 - a) * k)
            fill(ctx, ["#f97316", "#facc15", "#ef4444"][j % 3], 0.9)
        glow(ctx, 680, 1840, 600, "#f97316", 0.5 * k)
    puff(ctx, 680, 1880, t, 8, n=5, col="#e5e7eb", life=1.6, rate=0.3, dx=40, dy=-260, a=0.4 * (0.4 + k))
    line(ctx, 560, 1930, 820, 1880, 8, "#a16207")
    line(ctx, 690, 1960, 690, 1850, 10, "#78350f")
    castaway(ctx, 430, 2000, 1.05, emo("determined") if k < 0.5 else emo("happy"), t, arms="fwd", look=(0.7, 0.6),
             tremble=0.3 if k < 0.5 else 0)
    ctx.restore()
    step_card(ctx, t, EV["steps"][1], 2, "ОГОНЬ\nТЕПЛО И СИГНАЛ")


def s4_shelter(ctx, t, u, D):
    sh = EV["shelter"]
    k = ease(seg(t, sh, TL.shots[5][0] - 0.3))
    ctx.save()
    cam(ctx, t, 600, 1550, 0.95, shake=0.2)
    beach(ctx, t)
    # линия прилива
    ctx.set_dash([20, 14])
    line(ctx, -1500, 1500, 2500, 1500, 6, "#0369a1", 0.6)
    ctx.set_dash([])
    text(ctx, "ПРИЛИВ", 1000, 1470, 36, "#0369a1")
    # шалаш из пальмовых листьев (строится)
    n = int(9 * k)
    for j in range(n):
        x = 520 + j * 40
        line(ctx, 700, 1640, x, 1940, 10, "#78350f")
        ctx.move_to(x - 40, 1940)
        ctx.curve_to(x - 10, 1800, x + 20, 1700, 700, 1650)
        ctx.line_to(x + 40, 1940)
        ctx.close_path()
        fill(ctx, "#16a34a" if j % 2 else "#15803d")
    castaway(ctx, 320, 1980, 1.0, emo("determined"), t, arms="hold", look=(0.8, 0),
             item=lambda c, x, y: (c.move_to(x - 60, y), c.curve_to(x, y - 80, x + 60, y - 40, x + 100, y), fill(c, "#16a34a")))
    ctx.restore()
    step_card(ctx, t, EV["steps"][2], 3, "УКРЫТИЕ\nВЫШЕ ПРИЛИВА")


def s5_food(ctx, t, u, D):
    fd = EV["food"]
    ctx.save()
    cam(ctx, t, 540, 1700, 1.15, shake=0.2)
    beach(ctx, t, tide=0.4)
    for j, (x, y, kind) in enumerate(((330, 1940, "coco"), (620, 1900, "mussel"), (860, 1960, "fish"))):
        a = seg(t, fd[j] - 0.1, fd[j] + 0.3)
        if a <= 0:
            continue
        s = max(0.02, back_out(a)) * 1.7
        ctx.save()
        ctx.translate(x, y - 120)
        ctx.scale(s, s)
        if kind == "coco":
            ctx.arc(0, 0, 60, 0, TAU)
            fill(ctx, "#78350f")
            ctx.arc(10, 0, 44, -0.9, 0.9)
            fill(ctx, "#fefce8")
        elif kind == "mussel":
            ell(ctx, -50, 30, 80, 40)
            fill(ctx, "#78716c")
            for m in range(3):
                ell(ctx, -80 + m * 35, 0, 22, 12)
                fill(ctx, "#1e3a8a")
        else:
            ell(ctx, 0, 30, 110, 40)
            fill(ctx, "#38bdf8", 0.6)
            ell(ctx, 0, 20, 50, 20)
            fill(ctx, "#f59e0b")
            ctx.move_to(40, 20)
            ctx.line_to(70, 0)
            ctx.line_to(70, 40)
            fill(ctx, "#f59e0b")
        ctx.restore()
    ctx.restore()
    step_card(ctx, t, EV["steps"][3], 4, "ЕДА\nКОКОСЫ, МИДИИ, РЫБА")


def s6_sos(ctx, t, u, D):
    so = EV["sos"]
    k = seg(t, so, TL.shots[7][0] - 0.3)
    ctx.save()
    cam(ctx, t, 540, lerp(1500, 1450, k), lerp(1.0, 0.75, ease(seg(u, 0, D))), shake=0.2)
    vgrad(ctx, -1500, -1200, 4000, 4400, [(0, SAND), (1, SAND_D)])  # вид сверху на песок
    r = random.Random(3)
    for i in range(40):
        ell(ctx, r.uniform(-600, 1700), r.uniform(200, 2600), r.uniform(6, 14), r.uniform(4, 8))
        fill(ctx, r.choice(["#fcd34d", "#e5e7eb", "#a8a29e"]))
    ctx.rectangle(-1500, -1200, 4000, 1600)
    lgrad(ctx, 0, -1200, 0, 400, [(0, SEA_D), (1, SEA)])
    ctx.fill()
    waves(ctx, t, 300, 8, "#ffffff", 0.4, 6)
    # буквы SOS из камней появляются по мере выкладывания
    pts = []
    for letter, ox in (("S", -360), ("O", 0), ("S", 360)):
        if letter == "S":
            for j in range(16):
                a = j / 15
                yy = lerp(-260, 260, a)
                xx = 120 * math.sin(a * TAU) * (-1)
                pts.append((ox + xx, yy))
        else:
            for j in range(16):
                a = j / 16 * TAU
                pts.append((ox + math.cos(a) * 130, math.sin(a) * 260))
    n = int(len(pts) * k)
    for (px, py) in pts[:n]:
        ell(ctx, 540 + px, 1500 + py, 30, 22)
        fill(ctx, "#57534e")
        ell(ctx, 534 + px, 1494 + py, 12, 8)
        fill(ctx, "#a8a29e")
    if n < len(pts):
        hero(ctx, 540 + pts[n][0], 1500 + pts[n][1] + 300, 0.55, emo("determined"), t, arms="hold", rim_a=0.3,
             hood=CAST, walk=t * 6)
    ctx.restore()
    step_card(ctx, t, EV["steps"][4], 5, "СИГНАЛ\nSOS ИЗ КАМНЕЙ")


def s7_tally(ctx, t, u, D):
    tl = EV["tally"]
    ctx.save()
    cam(ctx, t, 540, 960, 1.0, shake=0.15)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0f172a"), (1, "#020617")])
    text(ctx, "СВЕРКА ЗАПАСОВ", 540, 300, 84, "#ffffff", "#000", 12)
    items = [("ВОДА", "7 л из 10", 0.7, "#38bdf8"), ("ОГОНЬ", "есть", 1.0, "#f97316"),
             ("ЕДА", "3 дня из 7", 3 / 7, "#facc15"), ("УКРЫТИЕ", "есть", 1.0, "#22c55e"),
             ("СИГНАЛ", "выложен", 1.0, "#e5e7eb")]
    fracs = ["7/10", "1/1", "3/7", "1/1", "1/1"]
    for i, (nm, val, fr, col) in enumerate(items):
        y = 480 + i * 175
        a = seg(t, tl[i] - 0.2, tl[i] + 0.1)
        if a <= 0:
            continue
        rr(ctx, 80, y - 70, 920, 150, 26)
        fill(ctx, "#1e293b", a)
        text(ctx, nm, 120, y - 22, 48, col, align="left", alpha=a)
        text(ctx, val, 120, y + 32, 34, "#cbd5e1", align="left", alpha=a)
        bar(ctx, 470, y - 14, 330, fr * ease(seg(t, tl[i], tl[i] + 0.6)), col)
        text(ctx, fracs[i], 960, y, 50, "#ffffff", align="right", alpha=a)
    ctx.restore()


def s8_chance(ctx, t, u, D):
    ch = EV["chance"]
    k = ease(seg(t, ch - 0.3, ch + 0.8))
    ctx.save()
    cam(ctx, t, 540, 960, 1.0, shake=0.15)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0f172a"), (1, "#020617")])
    ctx.arc(540, 900, 300, math.pi * 0.75, math.pi * 2.25)
    ctx.set_line_width(50)
    src(ctx, "#334155")
    ctx.stroke()
    ctx.arc(540, 900, 300, math.pi * 0.75, math.pi * 0.75 + math.pi * 1.5 * 0.8 * k)
    ctx.set_line_width(50)
    src(ctx, "#22c55e")
    ctx.stroke()
    text(ctx, f"{int(80 * k)}%", 540, 880, 170, "#ffffff")
    text(ctx, "ШАНСЫ ВЫЖИТЬ", 540, 1040, 50, "#94a3b8")
    ctx.restore()


def creature_eye(ctx, x, y, s, open_k, t, look=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ell(ctx, 0, 0, 340, 220)
    fill(ctx, "#365314")
    for k in range(10):  # чешуя/водоросли вокруг
        a = k * TAU / 10
        ell(ctx, math.cos(a) * 330, math.sin(a) * 210, 60, 40)
        fill(ctx, "#3f6212")
    ctx.save()
    ell(ctx, 0, 0, 280, 170 * open_k + 1)
    ctx.clip()
    g = cairo.RadialGradient(0, 0, 10, 0, 0, 280)
    g.add_color_stop_rgba(0, *hexc("#fde047"))
    g.add_color_stop_rgba(0.6, *hexc("#ca8a04"))
    g.add_color_stop_rgba(1, *hexc("#713f12"))
    ctx.set_source(g)
    ctx.paint()
    ell(ctx, look * 60, 0, 40, 150)
    fill(ctx, "#0a0a0a")
    ell(ctx, -90, -60, 40, 22)
    fill(ctx, "#ffffff", 0.7)
    ctx.restore()
    ell(ctx, 0, 0, 280, 170 * open_k + 1)
    ctx.set_line_width(14)
    src(ctx, "#1a2e05")
    ctx.stroke()
    ctx.restore()


def s9_tide(ctx, t, u, D):
    td = EV["tide"]
    k = ease(seg(t, td, TL.shots[10][0]))
    ctx.save()
    cam(ctx, t, 540, lerp(1400, 1200, k), lerp(0.85, 0.7, k), shake=0.15)
    beach(ctx, t, tide=-k * 1.2, dusk=0.5 * k)
    castaway(ctx, 540, 1950, 1.0, emo("calm", "worry", k), t, arms="down", back=True)
    ctx.restore()


def s10_breathe(ctx, t, u, D):
    br = EV["breath"]
    b = ease(seg(t, br - 0.5, br + 0.5))
    ctx.save()
    cam(ctx, t, 540, 1500, lerp(0.95, 1.15, ease(seg(u, 0, D))), shake=0.2 + 0.4 * b)
    beach(ctx, t, tide=-1.2, breathe=1.5 * b, dusk=0.5)
    lift = math.sin(t * 1.4) * 18 * 1.5 * b
    castaway(ctx, 540, 1950 - lift, 1.05, emo("fear"), t, arms="down", look=(0, 0.8), tremble=0.6)
    if b > 0:
        glow(ctx, 540, 2000, 700, "#ef4444", 0.12 * b * (0.5 + 0.5 * math.sin(t * 1.4)))
    ctx.restore()


def s11_eye(ctx, t, u, D):
    ey = EV["eye"]
    bl = EV["blink"]
    rise = ease(seg(t, ey - 1.0, ey + 0.5))
    op = 1.0
    if bl <= t < bl + 0.35:
        op = abs(1 - (t - bl) / 0.175)
    ctx.save()
    cam(ctx, t, 540, lerp(1150, 950, rise), lerp(0.75, 1.15, ease(seg(t, ey, bl + 0.6))), shake=0.4 + 0.8 * rise)
    beach(ctx, t, tide=-0.4, breathe=1.5, dusk=0.6)
    sy = 1150 - 260 * 0.4
    ctx.save()
    ctx.rectangle(-1500, -1200, 4000, sy + 1200)  # глаз только над водой, у рифа
    ctx.clip()
    creature_eye(ctx, 540, lerp(sy + 200, sy - 120, rise), 0.75, min(op, rise), t, math.sin(t * 0.6) * 0.5)
    for k in range(10):  # потоки воды стекают с века
        x_ = 340 + k * 42
        line(ctx, x_, sy - 260, x_ - 6, sy - 260 + (t * 300 + k * 50) % 260, 5, "#7dd3fc", 0.6 * rise)
    ctx.restore()
    waves(ctx, t, sy - 40, 6, "#ffffff", 0.5, 3)
    castaway(ctx, 540, 2250, 1.4, emo("shock"), t, arms="down", back=True, legs=False)
    ctx.restore()


def s12_alive(ctx, t, u, D):
    ec = EV["end_card"] - TL.shots[12][0]
    al = EV["alive"]
    ctx.save()
    if u < ec:
        k = ease(seg(t, al - 0.5, al + 2.5))
        # камера отлетает: остров — панцирь гигантского существа, которое плывёт
        cam(ctx, t, 540, 1000, lerp(1.0, 0.28, k), shake=0.2)
        vgrad(ctx, -4000, -4000, 9000, 9000, [(0, SEA_D), (1, "#082f49")])
        waves(ctx, t, -1500, 20, "#ffffff", 0.2, 30)
        sx, sy = 540, 1400
        # голова и ласты существа
        ell(ctx, sx + 1700, sy - 200, 520, 380)
        fill(ctx, "#365314")
        creature_eye(ctx, sx + 1800, sy - 300, 0.6, 1.0, t, 0.5)
        for side in (-1, 1):
            ctx.save()
            ctx.translate(sx + side * 900, sy + 900)
            ctx.rotate(side * (0.5 + math.sin(t * 1.5) * 0.25))
            ell(ctx, 0, 0, 700, 200)
            fill(ctx, "#3f6212")
            ctx.restore()
        ell(ctx, sx, sy, 1500, 1100)  # панцирь
        fill(ctx, "#4d7c0f")
        for k2 in range(12):
            a = k2 * TAU / 12
            ell(ctx, sx + math.cos(a) * 900, sy + math.sin(a) * 650, 260, 200)
            fill(ctx, "#3f6212")
        ctx.save()
        ctx.translate(0, 0)
        beach(ctx, t, tide=-1.2, breathe=1.5, dusk=0.4) if k < 0.15 else None
        ctx.restore()
        ell(ctx, sx, sy - 150, 900, 600)  # «остров» на спине
        fill(ctx, SAND)
        for px, py in ((sx - 400, sy - 200), (sx + 300, sy - 350), (sx + 500, sy + 50)):
            palm(ctx, px, py, 0.9, t, 0.2)
        castaway(ctx, sx, sy, 0.5, emo("shock"), t, arms="down")
        ctx.restore()
        ctx.save()
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#000", seg(u, ec - 0.3, ec))
    else:
        k = seg(u, ec, ec + 0.6)
        src(ctx, "#000")
        ctx.paint()
        s = max(0.02, back_out(k))
        ctx.translate(540, 820)
        ctx.scale(s, s)
        text(ctx, "ПРОДОЛЖЕНИЕ", 0, -190, 70, "#ffffff")
        text(ctx, "ЧАСТЬ 2", 0, -10, 190, "#ffd400", "#d8332a", 18)
        text(ctx, "Куда оно плывёт?", 0, 180, 70, "#84cc16")
    ctx.restore()


SCENES = [s0_hook, s1_look, s2_water, s3_fire, s4_shelter, s5_food, s6_sos, s7_tally, s8_chance, s9_tide,
          s10_breathe, s11_eye, s12_alive]
LABELS = {1: "ДЕНЬ 1", 2: "ДЕНЬ 1", 3: "ДЕНЬ 2", 4: "ДЕНЬ 2", 5: "ДЕНЬ 3", 6: "ДЕНЬ 4",
          9: "ДЕНЬ 7", 10: "ДЕНЬ 7", 11: "ДЕНЬ 7", 12: "ДЕНЬ 7"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("семь", "литров", "из", "десяти"), "7 л из 10"), (("три", "дня", "из", "семи"), "3 дня из 7"),
         (("восемьдесят", "процентов"), "80%"), (("три", "дня"), "3 дня")]


def disp_words(li):
    ws = TL.lines[li]["words"]
    out, i = [], 0
    while i < len(ws):
        for pat, rep in MERGE:
            n = len(pat)
            if tuple(w["w"].lower() for w in ws[i:i + n]) == pat:
                last = ws[i + n - 1]
                rep2 = rep
                out.append({"w": rep2, "t": ws[i]["t"], "d": last["t"] + last["d"] - ws[i]["t"]})
                i += n
                break
        else:
            out.append(dict(ws[i]))
            i += 1
    return out


def chunks(words):
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 3 or sum(len(x["w"]) for x in cur) > 12:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


CH = None


def subtitles(ctx, t):
    global CH
    if CH is None:
        CH = [chunks(disp_words(i)) for i in range(len(TL.lines))]
    for li, l in enumerate(TL.lines):
        s = l["start"]
        if not (s - 0.05 <= t <= s + l["speech"] + 0.25):
            continue
        u = t - s
        chs = CH[li]
        idx = 0
        for k, ch in enumerate(chs):
            if u >= ch[0]["t"] - 0.05:
                idx = k
        ch = chs[idx]
        pop = back_out(seg(u, ch[0]["t"] - 0.05, ch[0]["t"] + 0.12), 2.2)
        fs = 84
        words = [w["w"].upper() for w in ch]
        sp = 22
        widths = [text_w(ctx, w, fs) for w in words]
        total = sum(widths) + sp * (len(words) - 1)
        fit = min(1.0, 960 / total)
        y = 1560
        ctx.save()
        ctx.translate(540, y)
        ctx.scale(lerp(0.6, 1, pop) * fit, lerp(0.6, 1, pop) * fit)
        x = -total / 2
        for w, wd, ww in zip(words, ch, widths):
            on = wd["t"] - 0.03 <= u < wd["t"] + wd["d"] + (0.25 if wd is ch[-1] else 0)
            special = any(ch_ in w for ch_ in "0123456789")
            spk = TL.lines[li].get("spk")
            if spk in ("A", "B", "R"):
                base = COL_A if spk == "A" else COL_B
                col = "#ffffff" if on else base
            else:
                col = "#7CFF6B" if (on and special) else ("#ffd400" if on else "#ffffff")
            text(ctx, w, x, 0, fs, col, "#000000", 16, align="left", shadow=True)
            x += ww + sp
        ctx.restore()
        break


def overlays(ctx, t, i):
    vignette(ctx, W, H, 0.55)
    if t < EV["end_card"]:
        rr(ctx, 50, 90, 200, 70, 35)
        fill(ctx, "#d8332a")
        text(ctx, "ЧАСТЬ 1", 150, 125, 38, "#ffffff")
        rr(ctx, 830, 90, 200, 70, 35)
        fill(ctx, "#16a34a")
        text(ctx, "ГАЙД", 930, 125, 38, "#ffffff")
        if i in LABELS:
            a = seg(t, TL.shots[i][0], TL.shots[i][0] + 0.3)
            text(ctx, LABELS[i], W - 60, 210, 46, "#ffffff", "#000", 10, align="right", alpha=a)
    hook_end = TL.lines[0]["start"] + TL.lines[0]["speech"] + 0.2
    if t < hook_end:  # заголовок-хук
        k1 = back_out(seg(t, 0.0, 0.3))
        out = 1 - seg(t, hook_end - 0.3, hook_end)
        ctx.save()
        ctx.translate(540, 360)
        ctx.scale(k1, k1)
        ctx.push_group()
        text(ctx, "ЧТО ДЕЛАТЬ, ЕСЛИ", 0, -110, 84, "#ffffff", "#000", 16, shadow=True)
        text(ctx, "ТЫ ОДИН", 0, 10, 116, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -360, 90, 720, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "НА ОСТРОВЕ?", 0, 155, 100, "#ffffff")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(out)
        ctx.restore()
    if t < EV["end_card"]:
        subtitles(ctx, t)


# ================================================================== КАДР
def render_frame(ctx, t):
    i = TL.shot_at(t)
    a, b = TL.shots[i]
    kind = TRANS.get(i, "cut")
    src(ctx, "#000")
    ctx.paint()
    if kind == "whip" and t - a < 0.22 and i > 0:
        k = ease_in(seg(t, a, a + 0.22), 1.5)
        ctx.push_group()
        draw_scene(ctx, i - 1, t)
        prev = ctx.pop_group()
        ctx.push_group()
        draw_scene(ctx, i, t)
        cur = ctx.pop_group()
        ctx.save()
        ctx.translate(-k * W, 0)
        ctx.set_source(prev)
        ctx.paint()
        ctx.restore()
        ctx.save()
        ctx.translate((1 - k) * W, 0)
        ctx.set_source(cur)
        ctx.paint()
        ctx.restore()
        speed_lines(ctx, W, H, t, n=40, a=0.6 * math.sin(k * math.pi), seed=3)
    elif kind == "fade" and t - a < 0.6 and i > 0:
        draw_scene(ctx, i - 1, t)
        ctx.push_group()
        draw_scene(ctx, i, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(ease(seg(t, a, a + 0.6)))
    else:
        draw_scene(ctx, i, t)
    if kind == "flash" and t - a < 0.3:
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#ffffff", 0.9 * (1 - seg(t, a, a + 0.3)))
    if kind == "black":
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#000", 1 - seg(t, a, a + 0.35))
    if TRANS.get(i + 1) == "black" and t > b - 0.3:
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#000", seg(t, b - 0.3, b))
    overlays(ctx, t, i)


def render_range(args):
    k, f0, f1, out = args
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        ctx.save()
        render_frame(ctx, f / FPS)
        ctx.restore()
        surf.flush()
        ff.stdin.write(surf.get_data())
        if (f - f0) % 150 == 0:
            print(f"[{k}] {f - f0}/{f1 - f0}", flush=True)
    ff.stdin.close()
    ff.wait()
    return out


def stills(ts, outdir):
    os.makedirs(outdir, exist_ok=True)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    paths = []
    for t in ts:
        ctx.save()
        render_frame(ctx, t)
        ctx.restore()
        p = os.path.join(outdir, f"still_{t:06.2f}.png")
        surf.write_to_png(p)
        paths.append(p)
    return paths


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", default="")
    ap.add_argument("--outdir", default=os.path.join(ROOT, "build", "stills"))
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    a = ap.parse_args()
    if a.stills:
        if a.stills == "shots":
            ts = []
            for (s, e) in TL.shots:
                ts += [s + 0.4, (s + e) / 2, e - 0.3]
        else:
            ts = [float(x) for x in a.stills.split(",")]
        for p in stills(ts, a.outdir):
            print(p)
        sys.exit()
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    n = TL.nframes
    J = a.jobs
    parts = [(k, n * k // J, n * (k + 1) // J, os.path.join(ROOT, "build", f"seg{k}.mp4")) for k in range(J)]
    with Pool(J) as pool:
        outs = pool.map(render_range, parts)
    with open(os.path.join(ROOT, "build", "segs.txt"), "w") as f:
        for o in outs:
            f.write(f"file '{o}'\n")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
                           os.path.join(ROOT, "build", "segs.txt"), "-c", "copy",
                           os.path.join(ROOT, "build", "video.mp4")])
    print("video ->", os.path.join(ROOT, "build", "video.mp4"))
