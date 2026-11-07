"""Серия 20 «1990» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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


def hiker(ctx, x, y, sc, e, t, arms="relax", look=(0, 0), tremble=0.0, walk=None, back=False, tilt=0.0, legs=True,
          item=None):
    """Герой в тёплой куртке с рюкзаком и шапкой, изо рта пар."""
    rr(ctx, x - 90 * sc, y - 380 * sc, 180 * sc, 200 * sc, 30 * sc)  # рюкзак
    fill(ctx, "#166534")
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, tremble=tremble, walk=walk, back=back, tilt=tilt,
         legs=legs, rim="#e0f2fe", rim_a=0.6, hood=("#ea580c", "#9a3412"), hand_item=item)
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




def bar(ctx, x, y, w, k, col):
    rr(ctx, x, y, w, 26, 13)
    fill(ctx, "#334155")
    if k > 0:
        rr(ctx, x, y, max(26, w * k), 26, 13)
        fill(ctx, col)



# ================================================================== ЗОМБИ-ГОРОД
TOOK = ("#475569", "#334155")      # серая худи героя в этой серии
WALL = "#e7ddd0"


def apt_hero(ctx, x, y, sc, e, t, arms="relax", walk=None, look=(0, 0), back=False, tremble=0.0, item=None,
             legs=True, rim="#fde68a"):
    hero(ctx, x, y, sc, e, t, arms=arms, walk=walk, look=look, back=back, tremble=tremble, rim=rim, rim_a=0.6,
         hood=TOOK, hand_item=item, legs=legs)


ZCROWD = {}


def zcrowd(seed, n, y0, y1, x0=-900, x1=2000):
    key = (seed, n)
    if key not in ZCROWD:
        r = random.Random(seed)
        L = []
        for i in range(n):
            y = r.uniform(y0, y1)
            sc = lerp(0.35, 1.1, (y - y0) / max(1, y1 - y0))
            p = Npc(r, r.uniform(x0, x1), y, sc, r.choice((-1, 1)), r.uniform(0.25, 0.6))
            p.item = "none"
            L.append(p)
        ZCROWD[key] = sorted(L, key=lambda q: q.y)
    return ZCROWD[key]


def draw_zombies(ctx, t, crowd, mode="shamble", t_turn=0.0):
    """shamble — бредут; freeze — замерли; flee — разворачиваются и бегут влево."""
    for p in crowd:
        x0, d0, s0 = p.x, p.dir, p.speed
        if mode == "shamble":
            p.x = x0 + math.sin(t * 0.4 + p.seed) * 60
            npc(ctx, p, t, walking=True, zombie=1.0) if False else None
            npc(ctx, p, t * 0.5, walking=False, zombie=1.0)
        elif mode == "freeze":
            npc(ctx, p, t_turn, walking=False, zombie=1.0)
        else:
            k = clamp((t - t_turn - (p.seed % 1) * 0.6) / 0.4)
            p.dir = -1
            p.speed = 3.5
            npc(ctx, p, max(0.0, t - t_turn - 0.3), walking=k > 0.5, zombie=1.0)
        p.x, p.dir, p.speed = x0, d0, s0


def burning_car(ctx, x, y, s, t, col="#3b82f6"):
    parked_car(ctx, x, y, s, col, door_open=True)
    for k in range(5):
        a = (t * 2.5 + k / 5) % 1
        ell(ctx, x + math.sin(t * 6 + k) * 30 * s, y - 230 * s - a * 200 * s, 70 * s * (1 - a), 110 * s * (1 - a))
        fill(ctx, ["#f97316", "#facc15", "#ef4444"][k % 3], 0.85)
    puff(ctx, x, y - 400 * s, t, int(x) % 97, n=6, col="#1f2937", life=2.4, rate=0.25, dx=120 * s, dy=-600 * s,
         a=0.6)
    glow(ctx, x, y - 200 * s, 500 * s, "#f97316", 0.35)


def helicopter(ctx, x, y, s, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ell(ctx, 0, 0, 120, 50)
    fill(ctx, "#1f2937")
    rr(ctx, 80, -10, 200, 20, 8)
    fill(ctx, "#1f2937")
    ell(ctx, -40, -6, 50, 30)
    fill(ctx, "#93c5fd", 0.6)
    a = t * 40
    line(ctx, -200 * math.cos(a), -60, 200 * math.cos(a), -60, 8, "#111")
    line(ctx, 0, -50, 0, -62, 8, "#111")
    line(ctx, 280, -30 * math.cos(a * 1.3), 280, 30 * math.cos(a * 1.3), 6, "#111")
    line(ctx, -60, 50, 60, 50, 6, "#111")
    glow(ctx, 0, 30, 60, "#ef4444", 0.6 + 0.4 * math.sin(t * 8))
    ctx.move_to(-40, 40)  # прожектор
    ctx.line_to(-260, 900)
    ctx.line_to(80, 900)
    ctx.close_path()
    fill(ctx, "#fef9c3", 0.12)
    ctx.restore()


def city(ctx, t, night=0.0, crowd_mode="shamble", t_turn=0.0, glow_lights=True, show_crowd=True):
    """Улица города в катастрофе: небо с дымом, дома с окнами, вывески, горящие машины, вертолёт, толпа зомби."""
    vgrad(ctx, -1500, -1200, 4000, 2600, [(0, mix(hexc("#f59e0b"), hexc("#0b1022"), night)),
                                          (1, mix(hexc("#fed7aa"), hexc("#1e1b4b"), night))])
    if night > 0.5:
        stars(ctx, 4, 1080, 600, t, 40)
    for k in range(5):  # столбы дыма над крышами
        puff(ctx, -400 + k * 500, 700, t + k, 30 + k, n=8, col="#374151", life=4.0, rate=0.5, dx=200, dy=-900,
             a=0.45)
    skyline(ctx, 21, -1400, 2600, 1000, 300, 800, "#334155" if night < 0.5 else "#1e293b",
            "#fde68a" if glow_lights else None, 0.12 * (1 - night * 0.6), wmin=140, wmax=240)
    helicopter(ctx, (t * 90) % 2400 - 700, 260 + math.sin(t) * 20, 0.8, t)
    # ближний ряд домов с вывесками
    r = random.Random(8)
    x = -1300
    cols = ["#9a3412", "#57534e", "#1e3a8a", "#3f6212", "#7c2d12"]
    while x < 2600:
        w = r.uniform(400, 560)
        h = r.uniform(520, 760)
        ctx.rectangle(x, 1300 - h, w, h)
        fill(ctx, r.choice(cols))
        if night > 0.5:
            ctx.rectangle(x, 1300 - h, w, h)
            fill(ctx, "#020617", 0.5)
        for row in range(int(h // 130) - 1):
            for c in range(3):
                broken = r.random() < 0.25
                rr(ctx, x + 40 + c * (w - 80) / 3, 1300 - h + 50 + row * 130, (w - 80) / 3 - 30, 80, 4)
                fill(ctx, "#0f172a" if not broken else "#111827")
                if broken:
                    ctx.move_to(x + 50 + c * (w - 80) / 3, 1300 - h + 60 + row * 130)
                    ctx.line_to(x + 80 + c * (w - 80) / 3, 1300 - h + 100 + row * 130)
                    ctx.set_line_width(3)
                    src(ctx, "#94a3b8")
                    ctx.stroke()
        rr(ctx, x + 30, 1300 - 260, w - 60, 54, 6)
        fill(ctx, "#111827")
        nm = r.choice(["АПТЕКА", "ПРОДУКТЫ", "КАФЕ", "БАНК", "ОПТИКА"])
        flick = 1 if (int(t * 7 + x) % 5) else 0.2
        text(ctx, nm, x + w / 2, 1300 - 233, 34, r.choice(["#22c55e", "#f472b6", "#38bdf8"]), alpha=flick)
        x += w + 16
    # дорога, разметка, мусор, брошенные машины
    ctx.rectangle(-1500, 1300, 4000, 1400)
    fill(ctx, "#3f3f46")
    ctx.rectangle(-1500, 1300, 4000, 90)
    fill(ctx, "#78716c")
    for i in range(-10, 30):
        rr(ctx, i * 260, 1700, 140, 16, 8)
        fill(ctx, "#e5e7eb", 0.6)
    for i in range(14):
        rx = r.uniform(-900, 2000)
        newspaper(ctx, rx + math.sin(t + i) * 20, r.uniform(1400, 2200), r.uniform(-1, 1), 0.8)
    for i in range(8):
        ell(ctx, r.uniform(-900, 2000), r.uniform(1450, 2300), r.uniform(40, 90), 14)
        fill(ctx, "#7f1d1d", 0.5)
    parked_car(ctx, -500, 1560, 0.9, "#facc15", door_open=True)
    burning_car(ctx, 1400, 1600, 0.9, t, "#3b82f6")
    trash_bin(ctx, 200, 1390, 0.9)
    hydrant(ctx, 800, 1390, 0.9)
    lamp_post(ctx, -100, 1390, 520, on=(int(t * 3) % 4 != 0) and night > 0.3)
    lamp_post(ctx, 1100, 1390, 520, on=night > 0.3)
    if show_crowd:
        draw_zombies(ctx, t, zcrowd(77, 34, 1420, 2250), crowd_mode, t_turn)


def apartment(ctx, t, dark=0.0, curtains=0.0, window_fn=None, tv=True):
    """Квартира героя: окно на город, шторы, диван, полки, лампа, ковёр, ТВ с экстренным выпуском, часы, растения."""
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, WALL), (1, "#cfc2b0")])
    for k in range(-6, 16):  # обои
        line(ctx, k * 120, -800, k * 120, 1700, 3, "#d6c9b6", 0.6)
    rr(ctx, 120, 220, 840, 820, 10)
    fill(ctx, "#1e293b")
    ctx.save()
    rr(ctx, 130, 230, 820, 800, 6)
    ctx.clip()
    if window_fn:
        ctx.save()
        ctx.translate(130, 230)
        ctx.scale(820 / 1080, 800 / 1500)
        ctx.translate(0, -700)
        window_fn(ctx)
        ctx.restore()
    ctx.restore()
    for x0 in (130, 540, 950):
        ctx.rectangle(x0 - 10, 220, 20, 820)
        fill(ctx, "#f5f5f4")
    ctx.rectangle(120, 620, 840, 18)
    fill(ctx, "#f5f5f4")
    rr(ctx, 100, 1040, 880, 34, 6)  # подоконник
    fill(ctx, "#fafaf9")
    plant(ctx, 260, 1042, 0.5, t, "#c2410c")
    rr(ctx, 700, 990, 60, 52, 10)
    fill(ctx, "#fde68a")
    cl = ease(curtains)
    curtain(ctx, lerp(20, 130, cl), 200, lerp(160, 420, cl), 900, "#7f1d1d", t, 1)
    curtain(ctx, lerp(900, 540, cl), 200, lerp(160, 420, cl), 900, "#7f1d1d", t, -1)
    # полки, книги, фото
    rr(ctx, -560, 300, 520, 16, 4)
    fill(ctx, "#6b4226")
    bookshelf(ctx, -560, 180, 520, 2, 5)
    rr(ctx, -500, 640, 120, 150, 6)
    fill(ctx, "#fafaf9")
    hero_head(ctx, -440, 715, 40, emo("happy"), t, rim_a=0.0)
    # часы
    ctx.arc(1230, 400, 80, 0, TAU)
    fill(ctx, "#fafaf9")
    ctx.arc(1230, 400, 80, 0, TAU)
    ctx.set_line_width(10)
    src(ctx, "#1f2937")
    ctx.stroke()
    line(ctx, 1230, 400, 1230 + math.sin(t * 0.2) * 50, 400 - math.cos(t * 0.2) * 50, 6, "#111")
    line(ctx, 1230, 400, 1230 + math.sin(t * 2) * 64, 400 - math.cos(t * 2) * 64, 3, "#dc2626")
    # ТВ с экстренным выпуском
    if tv:
        rr(ctx, 1100, 760, 420, 260, 12)
        fill(ctx, "#020617")
        ctx.save()
        rr(ctx, 1112, 772, 396, 236, 6)
        ctx.clip()
        vgrad(ctx, 1112, 772, 396, 236, [(0, "#7f1d1d"), (1, "#450a0a")])
        text(ctx, "ЭКСТРЕННО", 1310, 820, 40, "#ffffff")
        text(ctx, "НЕ ВЫХОДИТЕ ИЗ ДОМА", 1310, 880, 26, "#fde68a")
        rr(ctx, 1112, 950, 396, 40, 0)
        fill(ctx, "#dc2626")
        text(ctx, "ОСТАВАЙТЕСЬ ДОМА · ОСТАВАЙТЕСЬ ДОМА ·", 1310 - (t * 80) % 200, 970, 22, "#ffffff")
        ctx.restore()
        rr(ctx, 1260, 1020, 100, 40, 6)
        fill(ctx, "#1f2937")
    # пол, ковёр, диван, торшер, журнальный столик
    ctx.rectangle(-1200, 1500, 3600, 1400)
    lgrad(ctx, 0, 1500, 0, 2900, [(0, "#a16207"), (1, "#713f12")])
    ctx.fill()
    for k in range(-12, 26):
        line(ctx, k * 110, 1500, k * 110 - 80, 2900, 3, "#854d0e", 0.6)
    rug(ctx, 540, 1900, 600, 160, "#1e3a8a")
    sofa(ctx, -300, 1640, 640, "#64748b")
    table_lamp(ctx, 1300, 1500, 1.2, on=dark < 0.5)
    rr(ctx, 380, 1760, 320, 30, 8)
    fill(ctx, "#78350f")
    for k in range(2):
        line(ctx, 410 + k * 260, 1790, 410 + k * 260, 1880, 10, "#78350f")
    coffee_cup(ctx, 470, 1760, 0.18, t)
    rr(ctx, 560, 1734, 90, 26, 6)  # пульт
    fill(ctx, "#111827")
    if dark > 0:
        ctx.rectangle(-1200, -800, 3600, 3600)
        fill(ctx, "#020617", 0.72 * dark)


def wardrobe(ctx, x, y, s, push=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.rotate(-0.04 * push)
    shadow(ctx, 0, 0, 260, 26, 0.4)
    rr(ctx, -220, -900, 440, 900, 8)
    lgrad(ctx, -220, 0, 220, 0, [(0, "#78350f"), (0.5, "#a16207"), (1, "#713f12")])
    ctx.fill()
    line(ctx, 0, -880, 0, -20, 4, "#451a03")
    for side in (-1, 1):
        ctx.arc(side * 30, -460, 10, 0, TAU)
        fill(ctx, "#fde68a")
        rr(ctx, side * 110 - 80, -840, 160, 340, 6)
        ctx.set_line_width(4)
        src(ctx, "#451a03")
        ctx.stroke()
    ctx.restore()


# ================================================================== СЦЕНЫ
def radio_box(ctx, x, y, s, t, on=1.0, glitch=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 180, 420, 40, 0.45)
    rr(ctx, -380, -200, 760, 380, 40)
    lgrad(ctx, 0, -200, 0, 180, [(0, "#a16207"), (1, "#713f12")])
    ctx.fill()
    ctx.arc(-170, 0, 130, 0, TAU)
    fill(ctx, "#292524")
    for k in range(6):
        ctx.arc(-170, 0, 20 + k * 18, 0, TAU)
        ctx.set_line_width(3)
        src(ctx, "#57534e")
        ctx.stroke()
    rr(ctx, 30, -150, 300, 90, 10)
    fill(ctx, "#fef3c7" if on else "#44403c")
    for k in range(12):
        line(ctx, 50 + k * 22, -150, 50 + k * 22, -120, 3, "#78350f")
    nx = 60 + (math.sin(t * 0.7) * 0.5 + 0.5) * 240 if glitch > 0 else 200
    line(ctx, nx, -150, nx, -60, 5, "#dc2626")
    for k in range(2):
        ctx.arc(110 + k * 140, 60, 44, 0, TAU)
        fill(ctx, "#292524")
        line(ctx, 110 + k * 140, 60, 110 + k * 140 + 30 * math.cos(t + k), 60 + 30 * math.sin(t + k), 6, "#d6d3d1")
    line(ctx, 300, -200, 380, -420, 8, "#9ca3af")
    if on:
        glow(ctx, 180, -100, 200, "#fde68a", 0.5)
    ctx.restore()


def tally_rows(ctx, t, title, items, tl):
    ctx.save()
    cam(ctx, t, 540, 960, 1.0, shake=0.15)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0f172a"), (1, "#020617")])
    text(ctx, title, 540, 300, 84, "#ffffff", "#000", 12)
    for i, (nm, val, fr, col, frac, icon) in enumerate(items):
        y = 480 + i * 175
        a = seg(t, tl[i] - 0.2, tl[i] + 0.1)
        if a <= 0:
            continue
        rr(ctx, 80, y - 70, 920, 150, 26)
        fill(ctx, "#1e293b", a)
        icon(ctx, 140, y, col, a)
        text(ctx, nm, 200, y - 22, 44, col, align="left", alpha=a)
        text(ctx, val, 200, y + 32, 32, "#cbd5e1", align="left", alpha=a)
        bar(ctx, 580, y - 14, 250, fr * ease(seg(t, tl[i], tl[i] + 0.6)), col)
        text(ctx, frac, 960, y, 46, "#ffffff", align="right", alpha=a)
    ctx.restore()


def ic_drop(c, x, y, col, a):
    c.move_to(x, y - 34)
    c.curve_to(x + 30, y, x + 24, y + 30, x, y + 30)
    c.curve_to(x - 24, y + 30, x - 30, y, x, y - 34)
    fill(c, col, a)


def ic_tent(c, x, y, col, a):
    c.move_to(x - 36, y + 28)
    c.line_to(x, y - 30)
    c.line_to(x + 36, y + 28)
    c.close_path()
    fill(c, col, a)


def ic_sun(c, x, y, col, a):
    c.arc(x, y, 18, 0, TAU)
    fill(c, col, a)
    for k in range(8):
        an = k * TAU / 8
        line(c, x + math.cos(an) * 24, y + math.sin(an) * 24, x + math.cos(an) * 34, y + math.sin(an) * 34, 5, col, a)


def ic_mirror(c, x, y, col, a):
    rr(c, x - 26, y - 30, 52, 60, 10)
    fill(c, col, a)
    line(c, x - 10, y - 18, x + 6, y + 14, 4, "#ffffff", a)


def ic_bolt(c, x, y, col, a):
    c.move_to(x + 6, y - 34)
    c.line_to(x - 20, y + 4)
    c.line_to(x, y + 4)
    c.line_to(x - 8, y + 34)
    c.line_to(x + 22, y - 6)
    c.line_to(x + 2, y - 6)
    c.close_path()
    fill(c, col, a)



def ic_flame(c, x, y, col, a):
    ell(c, x, y + 4, 22, 30)
    fill(c, col, a)
    ell(c, x, y + 12, 10, 16)
    fill(c, "#fde047", a)


def ic_can(c, x, y, col, a):
    rr(c, x - 24, y - 30, 48, 60, 8)
    fill(c, "#94a3b8", a)
    rr(c, x - 24, y - 10, 48, 22, 0)
    fill(c, col, a)




def day_city(ctx, t, sun=1.0):
    vgrad(ctx, -1500, -1200, 4000, 2600, [(0, "#38bdf8"), (1, "#e0f2fe")])
    ctx.arc(840, 260, 90, 0, TAU)
    fill(ctx, "#fef9c3")
    glow(ctx, 840, 260, 300, "#fde68a", 0.5)
    for k in range(3):
        cx = (k * 600 + t * 15) % 2400 - 700
        for j in range(4):
            ell(ctx, cx + j * 70, 380 + k * 60, 80, 34)
            fill(ctx, "#ffffff", 0.9)
    skyline(ctx, 41, -1400, 2600, 1150, 300, 750, "#94a3b8", "#e0f2fe", 0.35, wmin=150, wmax=260)
    ctx.rectangle(-1500, 1150, 4000, 1600)
    fill(ctx, "#a8a29e")
    ctx.rectangle(-1500, 1400, 4000, 1400)
    fill(ctx, "#4b5563")
    for i in range(-10, 30):
        rr(ctx, i * 260, 1650, 140, 14, 7)
        fill(ctx, "#f8fafc", 0.7)
    for x in (-400, 400, 1200):
        tree(ctx, x, 1300, 0.7, t, int(x) % 7)
        lamp_post(ctx, x + 300, 1300, 480)


def street_people(ctx, t, seed=1, n=8, y0=1700, mood="walk", alpha=1.0):
    r = random.Random(seed)
    xs = []
    for i in range(n):
        p = Npc(r, -500 + i * 280, y0 + (i % 3) * 70, 0.9 + (i % 3) * 0.08, r.choice((-1, 1)), 0.5)
        p.item = r.choice(["phone", "bag", "none", "coffee"])
        if mood == "walk":
            xs.append(npc(ctx, p, t * 0.6, walking=True, alpha=alpha))
        elif mood == "joy":
            xs.append(npc(ctx, p, t, walking=False, clap=True, grin=0.6, alpha=alpha))
        else:
            xs.append(npc(ctx, p, t, walking=False, stare=0.8, alpha=alpha))
    return xs






# ================================================================== 1990
def soviet_room(ctx, t, calendar=True, tv_on=False, dark=0.0):
    """Квартира 1990: обои в цветочек, ковёр на стене, сервант с хрусталём, ТВ с антенной, календарь с котёнком."""
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#d9c7a0"), (1, "#c4ae84")])
    r = random.Random(1990)
    for i in range(-10, 22):  # обои в цветочек
        for j in range(-6, 22):
            x, y = i * 110 + (55 if j % 2 else 0), j * 110
            for k in range(5):
                a = k * TAU / 5
                ctx.arc(x + math.cos(a) * 12, y + math.sin(a) * 12, 8, 0, TAU)
                fill(ctx, "#b45309", 0.35)
            ctx.arc(x, y, 6, 0, TAU)
            fill(ctx, "#facc15", 0.5)
    # ковёр на стене
    rr(ctx, -560, 300, 1000, 640, 10)
    fill(ctx, "#7f1d1d")
    rr(ctx, -520, 340, 920, 560, 6)
    ctx.set_line_width(14)
    src(ctx, "#facc15")
    ctx.stroke()
    for k in range(4):
        ell(ctx, -60, 620, 380 - k * 80, 220 - k * 50)
        ctx.set_line_width(10)
        src(ctx, ["#1e3a8a", "#facc15", "#065f46", "#fef3c7"][k])
        ctx.stroke()
    for k in range(-5, 6):
        line(ctx, -540 + (k + 5) * 92, 900, -540 + (k + 5) * 92, 960, 5, "#facc15")  # бахрома
    # сервант с хрусталём
    rr(ctx, 560, 380, 560, 1220, 10)
    lgrad(ctx, 560, 0, 1120, 0, [(0, "#5c2a0a"), (0.5, "#7c3a12"), (1, "#5c2a0a")])
    ctx.fill()
    for row in range(3):
        rr(ctx, 600, 420 + row * 220, 480, 190, 6)
        fill(ctx, "#fef3c7", 0.25)
        for k in range(5):
            x = 640 + k * 90
            y = 590 + row * 220
            ctx.move_to(x - 26, y)
            ctx.line_to(x - 14, y - 90)
            ctx.line_to(x + 14, y - 90)
            ctx.line_to(x + 26, y)
            ctx.close_path()
            fill(ctx, "#e0f2fe", 0.75)
            line(ctx, x - 8, y - 80, x - 2, y - 10, 3, "#ffffff", 0.9)
    rr(ctx, 600, 1110, 480, 440, 6)
    fill(ctx, "#4a1f07")
    # календарь 1990 с котёнком
    if calendar:
        rr(ctx, 160, 1000, 260, 340, 6)
        fill(ctx, "#fefce8")
        rr(ctx, 180, 1020, 220, 160, 4)
        fill(ctx, "#fde68a")
        ctx.arc(290, 1110, 46, 0, TAU)
        fill(ctx, "#f97316")
        for side in (-1, 1):
            ctx.move_to(290 + side * 40, 1080)
            ctx.line_to(290 + side * 30, 1040)
            ctx.line_to(290 + side * 14, 1074)
            fill(ctx, "#f97316")
        text(ctx, "1990", 290, 1230, 60, "#b91c1c")
        text(ctx, "МАРТ", 290, 1290, 30, "#1f2937")
    # пол, палас, тумба с ТВ
    ctx.rectangle(-1200, 1600, 3600, 1600)
    fill(ctx, "#78350f")
    for k in range(-12, 26):
        line(ctx, k * 120, 1600, k * 120 - 60, 3200, 3, "#5c2a0a")
    rr(ctx, -500, 1700, 1300, 260, 20)
    fill(ctx, "#065f46")
    rr(ctx, -200, 1340, 500, 260, 8)  # тумба
    fill(ctx, "#5c2a0a")
    rr(ctx, -180, 1080, 460, 280, 30)  # телевизор
    fill(ctx, "#57534e")
    rr(ctx, -150, 1110, 330, 220, 40)
    fill(ctx, "#94a3b8" if tv_on else "#1f2937")
    if tv_on:
        text(ctx, "ВРЕМЯ", 15, 1220, 50, "#1e3a8a")
        r2 = random.Random(int(t * 20))
        for k in range(6):
            line(ctx, -150, 1110 + r2.random() * 220, 180, 1110 + r2.random() * 220, 2, "#ffffff", 0.3)
    for k in range(3):
        ctx.arc(230, 1150 + k * 60, 16, 0, TAU)
        fill(ctx, "#a8a29e")
    line(ctx, 40, 1080, -40, 940, 6, "#9ca3af")  # антенна-рога
    line(ctx, 40, 1080, 140, 940, 6, "#9ca3af")
    if dark:
        ctx.rectangle(-1200, -800, 3600, 3600)
        fill(ctx, "#020617", 0.6 * dark)


def dial_phone(ctx, x, y, s, t, ring=0.0):
    ctx.save()
    ctx.translate(x + math.sin(t * 50) * 6 * ring, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 20, 200, 30, 0.4)
    ctx.move_to(-180, 0)
    ctx.line_to(-140, -160)
    ctx.line_to(140, -160)
    ctx.line_to(180, 0)
    ctx.close_path()
    fill(ctx, "#b91c1c")
    rr(ctx, -200, -230, 400, 80, 40)  # трубка
    fill(ctx, "#991b1b")
    ctx.arc(0, -70, 90, 0, TAU)
    fill(ctx, "#fef2f2")
    for k in range(10):
        a = -math.pi * 0.2 + k * TAU / 12
        ctx.arc(math.cos(a) * 62, -70 + math.sin(a) * 62, 16, 0, TAU)
        fill(ctx, "#111")
    ctx.arc(0, -70, 30, 0, TAU)
    fill(ctx, "#fca5a5")
    ctx.move_to(180, -20)
    for k in range(10):
        ctx.line_to(200 + k * 14, -10 + math.sin(k) * 20)
    ctx.set_line_width(6)
    src(ctx, "#111")
    ctx.stroke()
    ctx.restore()


def zhiguli(ctx, x, y, s, col="#f8fafc"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 0, 330, 26, 0.4)
    rr(ctx, -320, -150, 640, 110, 14)
    fill(ctx, col)
    ctx.move_to(-200, -150)
    ctx.line_to(-150, -250)
    ctx.line_to(160, -250)
    ctx.line_to(220, -150)
    fill(ctx, col)
    for wx0, wx1 in ((-180, -10), (10, 190)):
        ctx.move_to(wx0, -155)
        ctx.line_to(wx0 + 34, -235)
        ctx.line_to(wx1 - 20, -235)
        ctx.line_to(wx1, -155)
        fill(ctx, "#bfdbfe", 0.7)
    rr(ctx, 300, -130, 30, 40, 6)
    fill(ctx, "#fef9c3")
    rr(ctx, -330, -60, 660, 16, 6)
    fill(ctx, "#cbd5e1")
    for wx in (-200, 200):
        ctx.arc(wx, -40, 52, 0, TAU)
        fill(ctx, "#111")
        ctx.arc(wx, -40, 24, 0, TAU)
        fill(ctx, "#cbd5e1")
    ctx.restore()


def kvass_barrel(ctx, x, y, s, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 0, 260, 24, 0.35)
    ell(ctx, 0, -180, 240, 150)
    fill(ctx, "#facc15")
    for k in range(3):
        line(ctx, -180 + k * 180, -320, -180 + k * 180, -40, 6, "#ca8a04")
    text(ctx, "КВАС", 0, -180, 80, "#b91c1c")
    for wx in (-120, 120):
        ctx.arc(wx, -20, 40, 0, TAU)
        fill(ctx, "#111")
    rr(ctx, -40, -60, 80, 20, 4)  # кран
    fill(ctx, "#9ca3af")
    ctx.restore()


def street90(ctx, t, rain=0.0):
    """Улица 1990: хрущёвки, гастроном «МОЛОКО», киоск «Союзпечать», автомат, «Жигули», бочка кваса, массовка."""
    vgrad(ctx, -1500, -1200, 4000, 2600, [(0, "#93c5fd"), (1, "#e0f2fe")])
    for k in range(4):
        bx = -900 + k * 700
        rr(ctx, bx, 400, 620, 800, 4)
        fill(ctx, "#cbd5e1")
        for row in range(5):
            for col in range(4):
                rr(ctx, bx + 40 + col * 145, 450 + row * 150, 100, 100, 4)
                fill(ctx, "#475569")
                line(ctx, bx + 90 + col * 145, 450 + row * 150, bx + 90 + col * 145, 550 + row * 150, 3, "#e2e8f0")
        rr(ctx, bx + 200, 380, 220, 30, 4)
        fill(ctx, "#94a3b8")
    rr(ctx, -300, 1000, 640, 200, 6)  # гастроном
    fill(ctx, "#fef3c7")
    rr(ctx, -300, 940, 640, 70, 6)
    fill(ctx, "#1e3a8a")
    text(ctx, "ГАСТРОНОМ", 20, 975, 44, "#fef3c7")
    rr(ctx, -260, 1030, 200, 140, 4)
    fill(ctx, "#bfdbfe")
    text(ctx, "МОЛОКО", -160, 1100, 26, "#1e3a8a")
    rr(ctx, 700, 960, 300, 260, 10)  # киоск
    fill(ctx, "#2563eb")
    rr(ctx, 720, 1000, 260, 120, 6)
    fill(ctx, "#bfdbfe")
    text(ctx, "СОЮЗПЕЧАТЬ", 850, 980, 30, "#fef3c7")
    for k in range(4):
        rr(ctx, 730 + k * 62, 1020, 52, 80, 2)
        fill(ctx, ["#fef3c7", "#fecaca", "#fde68a", "#e5e7eb"][k])
    rr(ctx, 1200, 820, 180, 400, 10)  # телефон-автомат
    fill(ctx, "#b91c1c")
    rr(ctx, 1220, 860, 140, 120, 6)
    fill(ctx, "#bfdbfe")
    text(ctx, "ТЕЛЕФОН", 1290, 840, 26, "#ffffff")
    ctx.rectangle(-1500, 1200, 4000, 1600)
    fill(ctx, "#a8a29e")
    ctx.rectangle(-1500, 1500, 4000, 1300)
    fill(ctx, "#57534e")
    zhiguli(ctx, -500, 1700, 0.9, "#f8fafc")
    zhiguli(ctx, 600, 1750, 0.9, "#b91c1c")
    kvass_barrel(ctx, 1500, 1450, 0.8, t)
    r = random.Random(90)
    for i in range(8):  # массовка в пальто, ушанках, с авоськами
        p = Npc(r, -500 + i * 260, 1450 + (i % 2) * 60, 0.85, r.choice((-1, 1)), 0.5)
        p.shirt = r.choice(["#57534e", "#78350f", "#1e3a8a", "#3f3f46", "#7f1d1d"])
        p.item = r.choice(["bag", "none", "bag"])
        p.style = r.choice(["cap", "bun", "short", "long"])
        p.headphones = False
        npc(ctx, p, t * 0.5, walking=True)
    for k in range(5):  # тополиный пух
        r2 = random.Random(k)
        x = (r2.uniform(-200, 1300) + t * 30) % 1500 - 200
        y = (r2.uniform(0, 1800) + t * 20) % 1800
        ctx.arc(x, y, 5, 0, TAU)
        fill(ctx, "#ffffff", 0.7)


# ================================================================== СЦЕНЫ
def s0_hook(ctx, t, u, D):
    yr = EV["year"]
    ctx.save()
    cam(ctx, t, lerp(400, 290, ease(seg(t, yr - 1.5, yr))), lerp(1300, 1150, ease(seg(t, yr - 1.5, yr))),
        lerp(0.8, 1.8, ease(seg(t, yr - 1.5, yr))), shake=0.3)
    soviet_room(ctx, t)
    hero(ctx, 300, 2050, 1.0, emo("sleep") if u < 1.0 else emo("shock"), t, arms="shock" if u > 1.2 else "relax",
         rim="#fde68a")
    ctx.restore()


def s1_room(ctx, t, u, D):
    dl = EV["dial"]
    ctx.save()
    if t < dl - 0.2:
        cam(ctx, t, lerp(-200, 700, ease(seg(u, 0, D * 0.6))), 1100, 0.8, shake=0.2)
        soviet_room(ctx, t)
    else:
        cam(ctx, t, 540, 1100, 1.0, shake=0.2)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#d9c7a0"), (1, "#a8916a")])
        rr(ctx, 100, 1250, 880, 600, 10)  # тумба в прихожей
        fill(ctx, "#5c2a0a")
        rr(ctx, 140, 300, 400, 600, 8)  # зеркало и вешалка
        fill(ctx, "#cbd5e1")
        line(ctx, 700, 300, 1000, 300, 10, "#5c2a0a")
        for k in range(3):
            ctx.move_to(720 + k * 100, 310)
            ctx.line_to(700 + k * 100, 700)
            ctx.line_to(780 + k * 100, 700)
            fill(ctx, ["#57534e", "#7f1d1d", "#1e3a8a"][k])
        dial_phone(ctx, 540, 1250, 1.3, t)
    ctx.restore()


def s2_money(ctx, t, u, D):
    pw = EV["pawn"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.9, shake=0.2)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#57534e"), (1, "#292524")])
    rr(ctx, 100, 300, 880, 180, 10)
    fill(ctx, "#1c1917")
    text(ctx, "ЛОМБАРД", 540, 390, 80, "#facc15")
    rr(ctx, 100, 700, 880, 620, 10)  # окошко с решёткой
    fill(ctx, "#fef3c7", 0.6)
    for k in range(9):
        line(ctx, 140 + k * 100, 700, 140 + k * 100, 1320, 8, "#44403c")
    p = Npc(random.Random(7), 540, 1300, 1.1, -1)
    p.glasses, p.style, p.hair, p.item = True, "bald", "#9ca3af", "none"
    npc(ctx, p, t, walking=False)
    rr(ctx, 100, 1320, 880, 60, 6)
    fill(ctx, "#78350f")
    if t > pw:  # часы → пачка рублей
        k = seg(t, pw, pw + 1.0)
        ctx.arc(lerp(700, 400, k), 1340, 30, 0, TAU)
        fill(ctx, "#facc15")
        for j in range(int(5 * k)):
            rr(ctx, 600 + j * 12, 1310 - j * 8, 120, 60, 4)
            fill(ctx, "#a3e635")
            text(ctx, "25", 660 + j * 12, 1340 - j * 8, 22, "#365314")
    rr(ctx, -300, 1700, 1400, 60, 8)  # карта в руке героя
    hero(ctx, 840, 2150, 1.05, emo("worry"), t, arms="give", back=True, rim="#fde68a",
         hand_item=lambda c, x, y: (rr(c, x - 40, y - 26, 80, 52, 8), fill(c, "#2563eb")))
    ctx.restore()
    step_card(ctx, t, EV["steps"][0], 1, "ДЕНЬГИ\nКАРТА НЕ РАБОТАЕТ")


def s3_call(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 1150, 1400, 1.0, shake=0.2)
    street90(ctx, t)
    r = random.Random(3)
    for i in range(3):  # очередь к автомату
        p = Npc(r, 900 - i * 160, 1500, 0.9, 1)
        p.shirt, p.item = r.choice(["#57534e", "#7f1d1d", "#1e3a8a"]), "none"
        npc(ctx, p, t, walking=False)
    hero(ctx, 1290, 1600, 1.0, emo("worry"), t, arms="phone", rim="#fde68a",
         hand_item=lambda c, x, y: (rr(c, x - 20, y - 70, 40, 90, 10), fill(c, "#111")))
    if t > EV["coin"]:
        ctx.arc(1300, 1000, 18, 0, TAU)
        fill(ctx, "#d6d3d1")
        text(ctx, "2", 1300, 1000, 22, "#57534e")
    ctx.restore()
    step_card(ctx, t, EV["steps"][1], 2, "СВЯЗЬ\nДВУШКА В АВТОМАТ")


def s4_queue(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(-350, 500, ease(seg(u, 0, D))), 1450, 0.95, shake=0.2)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#fef3c7"), (1, "#e7e5e4")])
    rr(ctx, -800, 300, 2400, 120, 6)
    fill(ctx, "#1e3a8a")
    text(ctx, "КОЛБАСА · МОЛОКО · ХЛЕБ", 400, 360, 60, "#fef3c7")
    rr(ctx, 800, 900, 700, 400, 10)  # прилавок
    fill(ctx, "#a8a29e")
    for k in range(6):
        rr(ctx, 830 + k * 110, 820, 90, 80, 30)
        fill(ctx, "#b91c1c")
    for k in range(8):  # молоко в бутылках
        rr(ctx, 840 + k * 80, 1180, 50, 110, 12)
        fill(ctx, "#f8fafc")
        rr(ctx, 846 + k * 80, 1172, 38, 16, 4)
        fill(ctx, "#facc15" if k % 2 else "#e5e7eb")
    r = random.Random(11)
    for i in range(9):  # длинная очередь
        p = Npc(r, 700 - i * 170, 1700, 0.95, 1)
        p.shirt = r.choice(["#57534e", "#78350f", "#1e3a8a", "#7f1d1d", "#3f3f46"])
        p.item = "bag"
        p.style = r.choice(["bun", "cap", "long", "short"])
        p.headphones = False
        npc(ctx, p, t, walking=False)
    hero(ctx, -650, 1700, 0.95, emo("worry"), t, arms="hold", rim="#fde68a",
         hand_item=lambda c, x, y: (rr(c, x - 40, y - 30, 80, 50, 4), fill(c, "#fde68a"), text(c, "ТАЛОН", x, y - 6, 16, "#78350f")))
    ctx.restore()
    step_card(ctx, t, EV["steps"][2], 3, "ЕДА\nТАЛОНЫ И ОЧЕРЕДИ")


def s5_news(ctx, t, u, D):
    vr = EV["vremya"]
    ctx.save()
    if t < vr - 0.3:
        cam(ctx, t, 850, 1100, 1.4, shake=0.2)
        street90(ctx, t)
        hero(ctx, 700, 1700, 1.0, emo("calm"), t, arms="hold", rim="#fde68a",
             hand_item=lambda c, x, y: (rr(c, x - 70, y - 90, 140, 110, 3), fill(c, "#f5f5f4"),
                                        text(c, "ПРАВДА", x, y - 70, 20, "#b91c1c")))
    else:
        cam(ctx, t, 100, 1300, 1.0, shake=0.15)
        soviet_room(ctx, t, tv_on=True, dark=0.6)
        glow(ctx, 15, 1220, 400, "#bfdbfe", 0.4)
        sofa(ctx, 200, 1900, 700, "#57534e")
        hero(ctx, 200, 1850, 1.0, emo("calm"), t, arms="relax", legs=False, back=True, rim="#bfdbfe")
    ctx.restore()
    step_card(ctx, t, EV["steps"][3], 4, "НОВОСТИ\nГАЗЕТА И «ВРЕМЯ»")


def s6_hide(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 620, 1500, 0.85, shake=0.15)
    soviet_room(ctx, t)
    for k in range(4):  # гости за столом
        p = Npc(random.Random(40 + k), 200 + k * 220, 1900, 1.0, 1 if k < 2 else -1)
        p.item, p.headphones = "none", False
        npc(ctx, p, t, walking=False, grin=0.3)
    rr(ctx, 100, 1700, 900, 40, 6)  # стол с салатами
    fill(ctx, "#f8fafc")
    for k in range(4):
        ell(ctx, 230 + k * 200, 1680, 70, 26)
        fill(ctx, ["#fde68a", "#fca5a5", "#86efac", "#f8fafc"][k])
    rr(ctx, 520, 1400, 70, 120, 14)  # ящик серванта со смартфоном
    hero(ctx, 1080, 2050, 1.0, emo("worry"), t, arms="relax", rim="#fde68a", look=(-0.6, 0))
    ctx.restore()
    ctx.save()
    ctx.translate(840, 1150)
    ctx.arc(0, 0, 120, 0, TAU)
    fill(ctx, "#0b0b12", 0.85)
    text(ctx, "WI-FI", 0, 0, 40, "#ffffff")
    crossmark(ctx, 0, 0, 2.0)
    ctx.restore()
    step_card(ctx, t, EV["steps"][4], 5, "НЕ ВЫДАВАЙ СЕБЯ\nНИ СЛОВА О БУДУЩЕМ")


def ic_rub(c, x, y, col, a):
    rr(c, x - 30, y - 18, 60, 36, 4)
    fill(c, col, a)
    text(c, "Р", x, y, 26, "#365314", alpha=a)


def ic_bottle(c, x, y, col, a):
    rr(c, x - 14, y - 26, 28, 56, 8)
    fill(c, col, a)
    rr(c, x - 10, y - 32, 20, 10, 3)
    fill(c, "#facc15", a)


def ic_dial(c, x, y, col, a):
    c.arc(x, y, 26, 0, TAU)
    fill(c, col, a)
    for k in range(6):
        an = k * TAU / 6
        c.arc(x + math.cos(an) * 16, y + math.sin(an) * 16, 4, 0, TAU)
        fill(c, "#111", a)


def ic_eye(c, x, y, col, a):
    ell(c, x, y, 30, 16)
    fill(c, col, a)
    c.arc(x, y, 9, 0, TAU)
    fill(c, "#0b0b12", a)


def ic_smart(c, x, y, col, a):
    rr(c, x - 16, y - 28, 32, 56, 6)
    fill(c, col, a)


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА НЕДЕЛИ", [
        ("РУБЛИ", "40 из 50", 0.8, "#a3e635", "40/50", ic_rub),
        ("ЕДА", "на неделю", 1.0, "#f8fafc", "7/7", ic_bottle),
        ("СВЯЗЬ", "автомат во дворе", 1.0, "#ef4444", "1/1", ic_dial),
        ("ПОДОЗРЕНИЯ", "ноль", 0.0, "#facc15", "0", ic_eye),
        ("СМАРТФОН", "спрятан", 1.0, "#38bdf8", "1/1", ic_smart)], EV["tally"])


def s8_week(ctx, t, u, D):
    wk = EV["week"]
    ctx.save()
    cam(ctx, t, 540, 1100, 1.0, shake=0.15)
    soviet_room(ctx, t)
    rr(ctx, 160, 1000, 260, 340, 6)  # листки календаря облетают
    fill(ctx, "#fefce8")
    for k in range(7):
        a = seg(t, wk - 1.5 + k * 0.2, wk - 1.0 + k * 0.2)
        if 0 < a < 1:
            ctx.save()
            ctx.translate(290 + a * 300, 1170 - a * 400)
            ctx.rotate(a * 3)
            rr(ctx, -60, -40, 120, 80, 4)
            fill(ctx, "#fefce8")
            text(ctx, str(12 + k), 0, 0, 40, "#b91c1c")
            ctx.restore()
    hero(ctx, 700, 2050, 1.05, emo("happy"), t, arms="cheer", rim="#fde68a")
    ctx.restore()
    s = back_out(seg(t, wk, wk + 0.4))
    if s > 0:
        ctx.save()
        ctx.translate(540, 1000)
        ctx.scale(max(0.02, s), max(0.02, s))
        text(ctx, "7/7 ДНЕЙ", 0, 0, 130, "#16a34a", "#000", 16, shadow=True)
        ctx.restore()


def grey_coat(seed, x, y, sc, d=1):
    p = Npc(random.Random(seed), x, y, sc, d)
    p.shirt, p.pants, p.style, p.hair, p.item = "#6b7280", "#374151", "cap", "#111", "none"
    p.glasses, p.headphones, p.collar, p.print_, p.beard = False, False, "shirt", None, False
    return p


def s9_bell(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1350, 0.9, shake=0.2)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#78716c"), (1, "#44403c")])
    apartment_door(ctx, 320, 1700, 440, 1000, "47")
    rr(ctx, 820, 1000, 60, 80, 8)  # звонок
    fill(ctx, "#fef3c7")
    ctx.rectangle(-1200, 1700, 3600, 1400)
    fill(ctx, "#57534e")
    for k in range(3):
        npc(ctx, grey_coat(70 + k, 300 + k * 240, 1900, 1.1, 1), t, walking=False, stare=0.6)
    ctx.restore()
    if int(t * 4) % 2 == 0 and t > EV["bell"]:
        text(ctx, "ДЗЫНЬ!", 540, 600, 100, "#ffffff", "#000", 12)


def s10_phone(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1100, lerp(1.0, 1.4, ease(seg(u, 0, D))), shake=0.2)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#292524"), (1, "#0c0a09")])
    hanging_lamp(ctx, 540, 300, on=True, col="#065f46")
    rr(ctx, -200, 1200, 1480, 700, 20)
    fill(ctx, "#5c2a0a")
    rr(ctx, 380, 900, 320, 560, 30)  # смартфон
    fill(ctx, "#111")
    rr(ctx, 400, 920, 280, 520, 20)
    fill(ctx, "#1e293b")
    text(ctx, "30%", 540, 1100, 90, "#22c55e")
    rr(ctx, 470, 1160, 140, 50, 8)
    ctx.set_line_width(6)
    src(ctx, "#22c55e")
    ctx.stroke()
    for side in (-1, 1):
        g = grey_coat(80 + side, 540 + side * 420, 2000, 1.2, -side)
        npc(ctx, g, t, walking=False, stare=0.8)
    ctx.restore()


def s11_waited(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 600, 1450, lerp(1.3, 1.5, seg(u, 0, D)), shake=0.2)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#292524"), (1, "#0c0a09")])
    hanging_lamp(ctx, 540, 300, on=True, col="#065f46")
    g = grey_coat(90, 620, 1950, 1.5, -1)
    g.hair, g.style = "#d6d3d1", "short"
    npc(ctx, g, t, walking=False, grin=0.3)
    ctx.restore()
    text(ctx, "36 ЛЕТ", 540, 600, 120, "#ffffff", "#7f1d1d", 14, alpha=seg(t, EV["waited"], EV["waited"] + 0.3))


def s12_lab(ctx, t, u, D):
    hd = EV["hundreds"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        k = ease(seg(t, hd - 0.5, hd + 2.0))
        cam(ctx, t, 540, lerp(1300, 1100, k), lerp(1.2, 0.55, k), shake=0.2)
        vgrad(ctx, -3000, -2000, 7000, 6000, [(0, "#1c1917"), (1, "#0c0a09")])
        for row in range(5):
            for col in range(-3, 6):
                x, y = col * 360 - 100, 700 + row * 300
                hanging_lamp(ctx, x + 150, y - 160, on=True, col="#065f46")
                rr(ctx, x, y, 300, 40, 6)
                fill(ctx, "#5c2a0a")
                for j in range(4):
                    rr(ctx, x + 20 + j * 70, y - 90, 54, 90, 8)
                    fill(ctx, "#111")
                    rr(ctx, x + 25 + j * 70, y - 84, 44, 78, 6)
                    fill(ctx, "#1e293b")
                rr(ctx, x + 40, y + 40, 220, 60, 4)
                fill(ctx, "#a16207")
                text(ctx, "СДЕЛАНО В СССР 1990", x + 150, y + 70, 18, "#fef3c7")
        hero(ctx, 540, 2300, 1.6, emo("shock"), t, arms="down", back=True, legs=False, rim="#22c55e")
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
        text(ctx, "Кто ещё вернулся из будущего?", 0, 180, 54, "#fde68a")
    ctx.restore()


SCENES = [s0_hook, s1_room, s2_money, s3_call, s4_queue, s5_news, s6_hide, s7_tally, s8_week, s9_bell,
          s10_phone, s11_waited, s12_lab]
LABELS = {1: "ДЕНЬ 1", 2: "ДЕНЬ 1", 3: "ДЕНЬ 2", 4: "ДЕНЬ 3", 5: "ДЕНЬ 4", 6: "ДЕНЬ 6", 9: "ДЕНЬ 7",
          10: "ДЕНЬ 7", 11: "ДЕНЬ 7", 12: "ДЕНЬ 7"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("тысяча", "девятьсот", "девяностый"), "1990-й"), (("тысяча", "девятьсот", "девяностого"), "1990"),
         (("сорок", "из", "пятидесяти"), "40 из 50"), (("тридцать", "шесть", "лет"), "36 лет"),
         (("тридцать", "процентов"), "30%"), (("пять", "копеек"), "5 копеек"), (("трех",), "3"),
         (("девять",), "9")]


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
        rr(ctx, 790, 90, 240, 70, 35)
        fill(ctx, "#ca8a04")
        text(ctx, "ЧЕЛЛЕНДЖ", 910, 125, 34, "#ffffff")
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
        text(ctx, "ЧТО, ЕСЛИ", 0, -110, 88, "#ffffff", "#000", 16, shadow=True)
        text(ctx, "ТЫ ПРОСНУЛСЯ", 0, 10, 110, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -330, 90, 660, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "В 1990 ГОДУ?", 0, 155, 96, "#ffffff")
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
