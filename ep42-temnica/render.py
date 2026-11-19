"""Серия 42 «Средневековая темница» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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


def hands_phone(ctx, t, screen, tremble=1.0, sc=1.0, cx=540, cy=1000, hood=None):
    HC, HDk = hood if hood else (HOOD, HOOD_D)
    ctx.save()
    ctx.translate(cx + math.sin(t * 37) * 5 * tremble, cy + math.sin(t * 29) * 5 * tremble)
    ctx.scale(sc, sc)
    glow(ctx, 0, 0, 1100, "#60a5fa", 0.22)
    for side in (-1, 1):
        line(ctx, side * 600, 900, side * 380, 300, 150, HC)
        line(ctx, side * 640, 980, side * 420, 380, 30, HDk, 0.5)
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










# ================================================================== СРЕДНЕВЕКОВАЯ ТЕМНИЦА
TUNIC = ("#78350f", "#451a03")
STONE = "#57534e"


def peasant(ctx, x, y, sc, e, t, arms="relax", look=(0, 0), walk=None, back=False, legs=True, tremble=0.0, item=None,
            shackles=False):
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, walk=walk, back=back, legs=legs, tremble=tremble,
         rim="#fdba74", rim_a=0.55, hood=TUNIC, hand_item=item)
    rr(ctx, x - 92 * sc, y - (240 if legs else 70) * sc, 184 * sc, 22 * sc, 6 * sc)  # верёвочный пояс
    fill(ctx, "#a16207")
    if shackles and legs:
        for sd in (-1, 1):
            rr(ctx, x + sd * 30 * sc - 22 * sc, y - 60 * sc, 44 * sc, 20 * sc, 6 * sc)
            fill(ctx, "#57534e")
        line(ctx, x - 30 * sc, y - 50 * sc, x + 30 * sc, y - 50 * sc, 5 * sc, "#78716c")


def torch(ctx, x, y, s, t):
    rr(ctx, x - 8 * s, y, 16 * s, 90 * s, 4 * s)
    fill(ctx, "#78350f")
    rr(ctx, x - 22 * s, y + 30 * s, 44 * s, 14 * s, 4 * s)
    fill(ctx, "#44403c")
    for k in range(5):
        a = (t * 3 + k / 5) % 1
        ell(ctx, x + math.sin(t * 9 + k) * 6 * s, y - 20 * s - a * 50 * s, (20 - 12 * a) * s, (30 - 14 * a) * s)
        fill(ctx, ("#facc15", "#f97316", "#ef4444")[k % 3], 1 - a)
    glow(ctx, x, y - 20 * s, 300 * s, "#f59e0b", 0.45 + 0.08 * math.sin(t * 13))


def stone_wall(ctx, x0, y0, x1, y1, seed=1, col=STONE):
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    fill(ctx, shade(col, 0.6))
    r = random.Random(seed)
    for j in range(int((y1 - y0) / 90) + 1):
        off = 0 if j % 2 == 0 else 80
        for i in range(int((x1 - x0) / 160) + 2):
            x = x0 + i * 160 - off
            y = y0 + j * 90
            rr(ctx, x + 4, y + 4, 152, 82, 12)
            fill(ctx, mixh(col, "#78716c", r.random() * 0.5))
            if r.random() < 0.15:
                ell(ctx, x + r.uniform(20, 130), y + r.uniform(20, 60), 20, 10)
                fill(ctx, "#3f6212", 0.5)


def dungeon(ctx, t, dark=0.5, chains=True, drip=True):
    stone_wall(ctx, -1200, -800, 2400, 1700, 3)
    rr(ctx, 380, 300, 320, 200, 100)  # решётчатое окошко под потолком
    fill(ctx, "#0b1022")
    for k in range(5):
        line(ctx, 410 + k * 65, 300, 410 + k * 65, 500, 10, "#292524")
    ctx.move_to(420, 500)  # лунный луч
    ctx.line_to(660, 500)
    ctx.line_to(900, 1700)
    ctx.line_to(300, 1700)
    ctx.close_path()
    fill(ctx, "#e0f2fe", 0.08)
    if chains:
        for x in (120, 960):
            rr(ctx, x - 20, 700, 40, 40, 8)
            fill(ctx, "#292524")
            for k in range(8):
                ell(ctx, x + math.sin(t + k * 0.3) * 4, 760 + k * 34, 12, 18)
                ctx.set_line_width(6)
                src(ctx, "#78716c")
                ctx.stroke()
            rr(ctx, x - 40, 1030, 80, 30, 10)
            fill(ctx, "#57534e")
    torch(ctx, 250, 650, 1.0, t)
    torch(ctx, 830, 650, 1.0, t + 1)
    ctx.rectangle(-1200, 1700, 3600, 1200)
    fill(ctx, "#292524")
    r = random.Random(4)
    for k in range(40):  # солома
        x = r.uniform(-200, 1300)
        y = r.uniform(1720, 2100)
        line(ctx, x, y, x + r.uniform(-40, 40), y + r.uniform(-10, 10), 4, "#ca8a04", 0.7)
    rr(ctx, 800, 1640, 120, 80, 14)  # миска и кувшин
    fill(ctx, "#78350f")
    ell(ctx, 300, 1730, 70, 20)
    fill(ctx, "#57534e")
    if drip:
        ph = (t * 0.9) % 1
        ctx.arc(600, lerp(300, 1700, ph ** 2), 8, 0, TAU)
        fill(ctx, "#93c5fd", 0.8)
        ell(ctx, 600, 1720, 50 * ph, 10 * ph)
        ctx.set_line_width(3)
        src(ctx, "#93c5fd", 1 - ph)
        ctx.stroke()
    # крыса
    ell(ctx, 1000, 1760, 40, 20)
    fill(ctx, "#44403c")
    ctx.arc(1040, 1750, 14, 0, TAU)
    fill(ctx, "#44403c")
    line(ctx, 960, 1765, 900, 1780 + math.sin(t * 6) * 8, 3, "#57534e")
    if dark:
        ctx.rectangle(-1200, -800, 3600, 3600)
        fill(ctx, "#0c0a09", dark)
        glow(ctx, 250, 630, 420, "#f59e0b", 0.3)
        glow(ctx, 830, 630, 420, "#f59e0b", 0.3)


def townsman(ctx, x, y, sc, t, kind="judge", facing=-1, grin=0.0, stare=0.0):
    p = Npc(random.Random({"judge": 11, "scribe": 12, "guar": 13, "w1": 14, "w2": 15, "guard": 16}.get(kind, 17)),
            x, y, sc, facing)
    p.item = "none"
    if kind == "judge":
        p.shirt, p.pants, p.hair, p.beard = "#7f1d1d", "#1c1917", "#9a9a9a", True
    elif kind == "scribe":
        p.shirt, p.pants, p.style, p.glasses = "#334155", "#1c1917", "bald", True
    elif kind == "guar":
        p.shirt, p.pants, p.mustache = "#1e3a8a", "#1c1917", True
    elif kind == "guard":
        p.shirt, p.pants = "#57534e", "#1c1917"
    else:
        p.shirt = ("#166534", "#a16207")[kind == "w2"]
    npc(ctx, p, t, walking=False, grin=grin, stare=stare)
    hy = y - 370 * sc
    if kind == "judge":  # чёрная шапочка
        ctx.arc(x, hy - 30 * sc, 64 * sc, math.pi, TAU)
        fill(ctx, "#111827")
    if kind == "guard":  # шлем и алебарда
        ctx.arc(x, hy - 20 * sc, 66 * sc, math.pi, TAU)
        fill(ctx, "#9ca3af")
        rr(ctx, x - 80 * sc, hy - 26 * sc, 160 * sc, 14 * sc, 4 * sc)
        fill(ctx, "#6b7280")
        line(ctx, x - facing * 90 * sc, y, x - facing * 90 * sc, y - 640 * sc, 8 * sc, "#78350f")
        ctx.move_to(x - facing * 90 * sc, y - 640 * sc)
        ctx.line_to(x - facing * 150 * sc, y - 580 * sc)
        ctx.line_to(x - facing * 90 * sc, y - 560 * sc)
        fill(ctx, "#9ca3af")


def courtroom(ctx, t):
    stone_wall(ctx, -1200, -800, 2400, 1700, 9, "#78716c")
    for x in (-60, 1140):  # гобелены
        rr(ctx, x - 120, 300, 240, 600, 6)
        fill(ctx, "#7f1d1d")
        for k in range(4):
            line(ctx, x - 100, 360 + k * 130, x + 100, 360 + k * 130, 6, "#facc15", 0.6)
    rr(ctx, 300, 260, 480, 260, 10)  # герб
    fill(ctx, "#1e3a8a")
    ctx.move_to(540, 300)
    ctx.line_to(640, 340)
    ctx.line_to(620, 470)
    ctx.line_to(540, 500)
    ctx.line_to(460, 470)
    ctx.line_to(440, 340)
    ctx.close_path()
    fill(ctx, "#facc15")
    rr(ctx, 60, 1180, 960, 70, 8)  # судейский стол
    fill(ctx, "#451a03")
    rr(ctx, 60, 1250, 960, 300, 0)
    fill(ctx, "#78350f")
    for k in range(3):
        rr(ctx, 150 + k * 300, 1280, 200, 240, 6)
        ctx.set_line_width(4)
        src(ctx, "#451a03")
        ctx.stroke()
    for k in range(4):  # свечи
        x = 140 + k * 260
        rr(ctx, x - 10, 1110, 20, 70, 4)
        fill(ctx, "#fef3c7")
        ell(ctx, x, 1100, 8, 16)
        fill(ctx, "#facc15")
        glow(ctx, x, 1100, 120, "#f59e0b", 0.4)
    ctx.rectangle(-1200, 1700, 3600, 1200)
    fill(ctx, "#44403c")


def scroll(ctx, x, y, w, h, t, rows=(), k=1.0, rot=0.0, hl=-1):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    rr(ctx, -w / 2, -h / 2, w, h, 6)
    fill(ctx, "#fef3c7")
    for sd in (-1, 1):
        rr(ctx, -w / 2 - 14, sd * h / 2 - 20, w + 28, 40, 20)
        fill(ctx, "#d6a77a")
    for i, rw in enumerate(rows):
        a = seg(k, i / max(1, len(rows)), (i + 1) / max(1, len(rows)))
        if i == hl:
            rr(ctx, -w / 2 + 20, -h / 2 + 50 + i * 60, w - 40, 50, 6)
            fill(ctx, "#fecaca", a)
        text(ctx, rw, -w / 2 + 40, -h / 2 + 75 + i * 60, 34, "#451a03", align="left", alpha=a)
    ctx.restore()


def town_square(ctx, t, crowd=True, stocks=True, thrown=0.0):
    vgrad(ctx, -1500, -1200, 4000, 2400, [(0, "#93c5fd"), (1, "#fef3c7")])
    for k in range(5):  # фахверковые дома
        x = -500 + k * 420
        rr(ctx, x, 500, 380, 800, 4)
        fill(ctx, "#fef3c7")
        for j in range(4):
            line(ctx, x, 500 + j * 200, x + 380, 500 + j * 200, 12, "#451a03")
        line(ctx, x, 500, x + 380, 1300, 10, "#451a03")
        line(ctx, x + 380, 500, x, 1300, 10, "#451a03")
        ctx.move_to(x - 30, 520)
        ctx.line_to(x + 190, 260)
        ctx.line_to(x + 410, 520)
        fill(ctx, "#991b1b")
        rr(ctx, x + 140, 1050, 100, 250, 6)
        fill(ctx, "#78350f")
    rr(ctx, 860, 120, 160, 400, 6)  # колокольня
    fill(ctx, "#a8a29e")
    ctx.arc(940, 260, 50, 0, TAU)
    fill(ctx, "#facc15")
    ctx.rectangle(-1500, 1300, 4000, 1600)  # брусчатка
    fill(ctx, "#a8a29e")
    for j in range(10):
        for i in range(-12, 30):
            ell(ctx, i * 110 + (j % 2) * 55, 1330 + j * 70, 50, 28)
            fill(ctx, "#78716c", 0.6)
    if stocks:  # колодки на помосте
        rr(ctx, 240, 1460, 600, 60, 6)
        fill(ctx, "#78350f")
        for x in (300, 780):
            rr(ctx, x - 15, 1180, 30, 300, 6)
            fill(ctx, "#57381f")
        rr(ctx, 240, 1220, 600, 120, 10)
        fill(ctx, "#92400e")
        line(ctx, 240, 1280, 840, 1280, 4, "#451a03")
    if crowd:
        r = random.Random(23)
        for i in range(8):
            p = Npc(r, -400 + i * 260, 2050 + (i % 2) * 80, 1.05, r.choice((-1, 1)))
            p.item = "none"
            p.shirt = r.choice(("#78350f", "#166534", "#7f1d1d", "#a16207", "#57534e"))
            npc(ctx, p, t, walking=False, grin=0.5)
    for k in range(int(6 * thrown)):  # гнилые овощи летят
        a = (t * 0.8 + k / 6) % 1
        x = lerp(-100 + k * 220, 540, a)
        y = lerp(1900, 1250, a) - 300 * math.sin(a * math.pi)
        ctx.arc(x, y, 22, 0, TAU)
        fill(ctx, ("#ef4444", "#84cc16", "#a16207")[k % 3])


def mixh(c1, c2, k):
    a, b = hexc(c1), hexc(c2)
    return "#%02x%02x%02x" % tuple(int(255 * (a[i] + (b[i] - a[i]) * clamp(k))) for i in range(3))


def iron_maiden(ctx, x, y, s, t, open_k=0.0, dust=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 20, 300, 30, 0.5)
    if open_k:  # раскрытая створка с шипами (без жертвы)
        ctx.save()
        ctx.translate(200, -500)
        ctx.scale(open_k, 1)
        rr(ctx, 0, -500, 300, 1000, 80)
        fill(ctx, "#44403c")
        for k in range(18):
            cx = 60 + (k % 3) * 90
            cy = -420 + (k // 3) * 150
            ctx.move_to(cx - 14, cy)
            ctx.line_to(cx + 14, cy)
            ctx.line_to(cx, cy - 40)
            fill(ctx, "#9ca3af")
        ctx.restore()
    rr(ctx, -200, -1000, 400, 1000, 160)
    lgrad(ctx, -200, 0, 200, 0, [(0, "#44403c"), (0.5, "#78716c"), (1, "#44403c")])
    ctx.fill()
    ctx.arc(0, -820, 120, 0, TAU)  # «лицо»
    fill(ctx, "#a8a29e")
    for sd in (-1, 1):
        ell(ctx, sd * 40, -840, 18, 10)
        fill(ctx, "#1c1917")
    line(ctx, -30, -770, 30, -770, 6, "#1c1917")
    for k in range(6):  # заклёпки и обручи
        line(ctx, -200, -640 + k * 110, 200, -640 + k * 110, 6, "#292524")
        for j in range(4):
            ctx.arc(-160 + j * 107, -640 + k * 110, 8, 0, TAU)
            fill(ctx, "#d6d3d1")
    if dust:
        for k in range(25):
            r_ = random.Random(k)
            ctx.arc(r_.uniform(-260, 260), (r_.uniform(-1100, 0) + t * 30) % 1100 - 1100, 3, 0, TAU)
            fill(ctx, "#e7e5e4", 0.4 * dust)
    ctx.restore()


def museum_plaque(ctx, x, y, w, t, a=1.0):
    rr(ctx, x - w / 2, y - 110, w, 220, 10)
    fill(ctx, "#d4a849", a)
    rr(ctx, x - w / 2 + 12, y - 98, w - 24, 196, 6)
    fill(ctx, "#1c1917", a)
    text(ctx, "«ЖЕЛЕЗНАЯ ДЕВА»", x, y - 50, 44, "#facc15", alpha=a)
    text(ctx, "собрана ок. 1800-х годов", x, y + 10, 32, "#e7e5e4", alpha=a)
    text(ctx, "из разных старых деталей", x, y + 60, 32, "#e7e5e4", alpha=a)


# ================================================================== СЦЕНЫ
def s0_hook(ctx, t, u, D):
    wk, ac = EV["wake"], EV["accuse"]
    ctx.save()
    cam(ctx, t, 540, 1350, lerp(0.85, 0.95, seg(u, 0, D)), shake=0.15)
    dungeon(ctx, t, dark=0.45)
    peasant(ctx, 540, 2050, 1.0, emo("sleep") if t < wk else emo("shock"), t, arms="relax" if t < wk else "shock",
            shackles=True)
    ctx.restore()
    if t > ac:
        a = seg(t, ac, ac + 0.3)
        ctx.save()
        scroll(ctx, 540, 820, 700, 260, t, ("ОБВИНЯЕТСЯ:", "в краже кошеля"), seg(t, ac, ac + 1.2), -0.03)
        ctx.restore()


def s1_court(ctx, t, u, D):
    co = EV["court"]
    ctx.save()
    if t < co - 0.3:
        cam(ctx, t, 540, lerp(1300, 1100, seg(u, 0, D)), 1.0, shake=0.1)
        dungeon(ctx, t, dark=0.35)
        peasant(ctx, 540, 2050, 1.0, emo("worry"), t, arms="relax", look=(0, -0.8), shackles=True)
    else:
        cam(ctx, t, 540, 1300, 0.85, shake=0.1)
        courtroom(ctx, t)
        townsman(ctx, 540, 1180, 1.0, t, "judge", -1)
        townsman(ctx, 200, 1180, 0.9, t, "scribe", 1)
        townsman(ctx, 900, 1180, 0.9, t, "guard", -1)
        r = random.Random(7)
        for i in range(5):
            p = Npc(r, -200 + i * 330, 2100, 1.0, 1)
            p.item = "none"
            p.shirt = r.choice(("#78350f", "#166534", "#7f1d1d"))
            npc(ctx, p, t, walking=False, back=True)
    ctx.restore()


def s2_guar(ctx, t, u, D):
    gu = EV["guar"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.85, shake=0.1)
    courtroom(ctx, t)
    townsman(ctx, 540, 1180, 1.0, t, "judge", -1)
    townsman(ctx, 820, 2050, 1.1, t, "guar", -1, grin=0.4)
    peasant(ctx, 280, 2050, 1.0, emo("worry"), t, arms="relax", look=(0.7, 0), shackles=True)
    ctx.restore()
    if t > gu:
        a = seg(t, gu, gu + 0.3)
        rr(ctx, 440, 640, 600, 120, 30)
        fill(ctx, "#fef3c7", a)
        text(ctx, "«Ручаюсь за него!»", 740, 700, 44, "#451a03", alpha=a)
    step_card(ctx, t, EV["steps"][0], 1, "НАЙДИ\nПОРУЧИТЕЛЯ")


def rack_shadow(ctx, t, k):
    """Дыба — только тенью на стене, без подробностей."""
    ctx.save()
    ctx.translate(540, 1150)
    ctx.scale(1.4, 1.4)
    col = "#0c0a09"
    a = 0.75
    rr(ctx, -380, 60, 760, 40, 6)
    fill(ctx, col, a)
    for x in (-360, 340):
        rr(ctx, x, -60, 30, 180, 6)
        fill(ctx, col, a)
    ctx.save()  # ворот
    ctx.translate(-345, -40)
    ctx.rotate(k * 0.8)
    for j in range(4):
        line(ctx, 0, 0, math.cos(j * math.pi / 2) * 70, math.sin(j * math.pi / 2) * 70, 12, col, a)
    ctx.restore()
    ell(ctx, 0, 30, 260, 34)  # силуэт лежащего человека
    fill(ctx, col, a)
    ctx.arc(280, 20, 34, 0, TAU)
    fill(ctx, col, a)
    line(ctx, -330, -40, -250, 30, 6, col, a)
    line(ctx, 340, 20, 360, -40, 6, col, a)
    ctx.restore()


def s3_law(ctx, t, u, D):
    tr, rp = EV["torture"], EV["repeat"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.9, shake=0.1)
    dungeon(ctx, t, dark=0.55, chains=False, drip=False)
    rack_shadow(ctx, t, seg(t, tr - 0.5, tr + 2.0))
    townsman(ctx, 160, 2050, 1.0, t, "scribe", 1)
    townsman(ctx, 940, 2050, 1.1, t, "guard", -1)
    ctx.restore()
    if t > rp:
        a = seg(t, rp, rp + 0.3)
        scroll(ctx, 540, 720, 840, 280, t, ("ЗАКОН 1532 г.:", "признание под пыткой —", "повторить без пытки"),
               seg(t, rp, rp + 1.2), 0.02)
    step_card(ctx, t, EV["steps"][1], 2, "ПОМНИ ЗАКОН\nПРИЗНАНИЕ — ПОВТОРИТЬ")


def s4_scribe(ctx, t, u, D):
    sc_, cm = EV["scribe"], EV["compare"]
    ctx.save()
    cam(ctx, t, 540, 1150, 1.0, shake=0.1)
    courtroom(ctx, t)
    ctx.restore()
    rows = ("1-й допрос: был на рынке", "2-й допрос: был на рынке", "3-й допрос: был на рынке")
    scroll(ctx, 540, 1000, 900, 360, t, rows, seg(t, sc_, cm), 0.0)
    rr(ctx, 840, 1180, 30, 160, 6)  # перо
    fill(ctx, "#f8fafc")
    if t > cm:
        for i in range(3):
            checkmark(ctx, 920, 900 + i * 60, 0.5, OK, seg(t, cm + i * 0.2, cm + i * 0.2 + 0.2))
    step_card(ctx, t, EV["steps"][2], 3, "НЕ ПУТАЙСЯ\nВ СЛОВАХ")


def s5_stocks(ctx, t, u, D):
    st, ca = EV["stocks"], EV["calm"]
    ctx.save()
    cam(ctx, t, 540, 1450, 0.8, shake=0.1)
    town_square(ctx, t, thrown=1.0 - 0.8 * seg(t, ca, ca + 2.0))
    hero_head(ctx, 540, 1250, 70, emo("determined"), t, rim="#fdba74", rim_a=0.5)
    for sd in (-1, 1):
        ctx.arc(540 + sd * 150, 1280, 26, 0, TAU)
        fill(ctx, HEAD)
    rr(ctx, 400, 1340, 280, 160, 30)
    fill(ctx, TUNIC[0])
    ctx.restore()
    rr(ctx, 340, 640, 400, 120, 30)
    fill(ctx, "#0b0b12", 0.8)
    text(ctx, f"ЧАС {1 + int(seg(u, 0, D) * 2.99)} ИЗ 3", 540, 700, 50, "#fdba74")
    step_card(ctx, t, EV["steps"][3], 4, "КОЛОДКИ —\nСТОЙ СПОКОЙНО")


def s6_wit(ctx, t, u, D):
    wt_ = EV["wit"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.85, shake=0.1)
    courtroom(ctx, t)
    townsman(ctx, 540, 1180, 1.0, t, "judge", -1)
    townsman(ctx, 700, 2050, 1.05, t, "w1", -1, grin=0.3)
    townsman(ctx, 950, 2050, 1.05, t, "w2", -1, grin=0.3)
    peasant(ctx, 260, 2050, 1.0, emo("calm"), t, arms="relax", look=(0.7, 0))
    ctx.restore()
    if t > wt_:
        for i, x in enumerate((700, 950)):
            a = seg(t, wt_ + i * 0.3, wt_ + i * 0.3 + 0.3)
            rr(ctx, x - 150, 700 + i * 40, 300, 100, 24)
            fill(ctx, "#fef3c7", a)
            text(ctx, ("«Видел его!»", "«И я видел!»")[i], x, 750 + i * 40, 34, "#451a03", alpha=a)
    step_card(ctx, t, EV["steps"][4], 5, "ДВОЕ\nСВИДЕТЕЛЕЙ")


def ic_hand3(c, x, y, col, a):
    rr(c, x - 18, y - 6, 36, 30, 10)
    fill(c, col, a)
    for k in range(4):
        rr(c, x - 16 + k * 10, y - 24, 8, 22, 4)
        fill(c, col, a)


def ic_quill(c, x, y, col, a):
    line(c, x - 20, y + 22, x + 20, y - 22, 6, col, a)
    ell(c, x + 10, y - 12, 8, 18)
    fill(c, col, a)


def ic_scroll(c, x, y, col, a):
    rr(c, x - 18, y - 22, 36, 44, 4)
    fill(c, col, a)
    for k in range(3):
        line(c, x - 10, y - 10 + k * 10, x + 10, y - 10 + k * 10, 3, "#0b0b12", a)


def ic_stocks(c, x, y, col, a):
    rr(c, x - 26, y - 10, 52, 20, 4)
    fill(c, col, a)
    for dx in (-14, 0, 14):
        c.arc(x + dx, y, 4, 0, TAU)
        fill(c, "#0b0b12", a)


def ic_eye2(c, x, y, col, a):
    ell(c, x, y, 24, 13)
    fill(c, col, a)
    c.arc(x, y, 7, 0, TAU)
    fill(c, "#0b0b12", a)


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА СУДА", [
        ("ПОРУЧИТЕЛЬ", "найден", 1.0, "#facc15", "1/1", ic_hand3),
        ("ПРИЗНАНИЯ", "ни одного", 0.0, "#ef4444", "0", ic_quill),
        ("СЛОВА", "без противоречий", 1.0, "#fdba74", "3/3", ic_scroll),
        ("КОЛОДКИ", "часов", 1.0, "#a16207", "3", ic_stocks),
        ("СВИДЕТЕЛИ", "честных", 1.0, "#22c55e", "2", ic_eye2)], EV["tally"])


def s8_free(ctx, t, u, D):
    fr = EV["free"]
    ctx.save()
    cam(ctx, t, 540, 1400, 0.8, shake=0.1)
    town_square(ctx, t, crowd=True, stocks=False)
    peasant(ctx, 540, 2150, 1.0, emo("happy"), t, arms="cheer" if t > fr else "relax")
    ctx.restore()


def s9_cellar(ctx, t, u, D):
    ma = EV["maiden"]
    ctx.save()
    k = ease(seg(t, ma - 0.6, ma + 0.8))
    cam(ctx, t, 540, lerp(1400, 1150, k), lerp(0.8, 1.0, k), shake=0.15)
    dungeon(ctx, t, dark=0.6, chains=True, drip=True)
    iron_maiden(ctx, 760, 1700, 0.9, t)
    peasant(ctx, 260, 2050, 1.0, emo("fear") if t > ma else emo("worry"), t, arms="shock" if t > ma else "relax",
            look=(0.8, -0.3))
    ctx.restore()
    if t > ma:
        text(ctx, "ЖЕЛЕЗНАЯ ДЕВА", 540, 640, 80, "#fca5a5", "#000", 10, alpha=seg(t, ma, ma + 0.3))


def s10_spikes(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1100, 1.05, shake=0.15)
    dungeon(ctx, t, dark=0.65, chains=False, drip=False)
    iron_maiden(ctx, 400, 1750, 1.0, t, open_k=ease(seg(t, EV["spikes"] - 0.6, EV["spikes"] + 0.4)))
    ctx.restore()
    if t > EV["whisper"]:
        text(ctx, "…ш-ш-ш…", 760, 700, 60, "#a8a29e", "#000", 6, alpha=seg(t, EV["whisper"], EV["whisper"] + 0.3))


def s11_noproof(ctx, t, u, D):
    npf = EV["noproof"]
    ctx.save()
    cam(ctx, t, 540, 1150, 1.0, shake=0.1)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#fef3c7"), (1, "#fde68a")])
    bookshelf(ctx, -100, 300, 640, rows=4, seed=11)
    rr(ctx, 60, 1250, 960, 50, 8)
    fill(ctx, "#78350f")
    for i in range(4):  # архивные свитки и книги
        scroll(ctx, 200 + i * 230, 1150, 180, 140, t, ("1450", "1500", "1550", "1600")[i:i + 1], 1.0, (i - 1.5) * 0.05)
    hero_head(ctx, 820, 760, 110, emo("worry"), t, rim_a=0.0)  # историк в очках
    for sd in (-1, 1):
        ctx.arc(820 + sd * 40, 765, 28, 0, TAU)
        ctx.set_line_width(6)
        src(ctx, "#a8a29e")
        ctx.stroke()
    ctx.restore()
    if t > npf:
        a = seg(t, npf, npf + 0.3)
        rr(ctx, 160, 1290, 760, 140, 30)
        fill(ctx, "#0b0b12", 0.9 * a)
        text(ctx, "ДОКАЗАТЕЛЬСТВ: 0", 540, 1360, 64, "#facc15", alpha=a)


def s12_museum(ctx, t, u, D):
    c19, mu = EV["c19"], EV["museum"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        ctx.save()
        cam(ctx, t, 540, 1300, lerp(0.8, 0.95, seg(u, 0, ec)), shake=0.1)
        vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#e7e5e4"), (1, "#d6d3d1")])
        for k in range(-3, 7):
            rr(ctx, k * 300, 200, 20, 1500, 4)
            fill(ctx, "#a8a29e")
        rr(ctx, 260, 1600, 560, 120, 10)  # постамент
        fill(ctx, "#78716c")
        iron_maiden(ctx, 540, 1620, 0.85, t, dust=0.0)
        line(ctx, -200, 1500, 1300, 1500, 8, "#b91c1c")  # ограждение
        for x in (-150, 260, 820, 1230):
            line(ctx, x, 1500, x, 1800, 10, "#d4a849")
        r = random.Random(31)
        for i in range(5):  # посетители XIX века
            p = Npc(r, -250 + i * 350, 2100, 1.0, r.choice((-1, 1)))
            p.item = "none"
            p.shirt = r.choice(("#1c1917", "#7f1d1d", "#1e3a8a"))
            npc(ctx, p, t, walking=False, stare=0.8)
            if i % 2 == 0:  # цилиндр
                rr(ctx, p.x - 50, p.y - 520, 100, 110, 6)
                fill(ctx, "#111827")
                rr(ctx, p.x - 74, p.y - 420, 148, 16, 6)
                fill(ctx, "#111827")
        ctx.restore()
        museum_plaque(ctx, 540, 470, 760, t, seg(t, c19 - 0.3, c19))
        if t > mu:
            text(ctx, "СТРАШИЛКА ДЛЯ МУЗЕЕВ", 540, 1250, 54, "#7f1d1d", "#fff", 8, alpha=seg(t, mu, mu + 0.3))
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
        text(ctx, "Какие ещё страшилки о Средневековье —", 0, 170, 44, "#fdba74")
        text(ctx, "ложь?", 0, 230, 60, "#fdba74")
    ctx.restore()


SCENES = [s0_hook, s1_court, s2_guar, s3_law, s4_scribe, s5_stocks, s6_wit, s7_tally, s8_free, s9_cellar,
          s10_spikes, s11_noproof, s12_museum]
LABELS = {11: "ПРАВДА", 12: "ПРАВДА"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("шестнадцатого", "века,"), "XVI века,"), (("шестнадцатого", "века"), "XVI века"), (("ноль.",), "0."),
         (("ноль",), "0"), (("три.",), "3."), (("двое.",), "2."), (("девятнадцатом", "веке,"), "XIX веке,"),
         (("девятнадцатом", "веке"), "XIX веке")]


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
        rr(ctx, 730, 90, 300, 70, 35)
        fill(ctx, "#92400e")
        text(ctx, "СРЕДНЕВЕКОВЬЕ", 880, 125, 30, "#ffffff")
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
        text(ctx, "ТЫ В ТЕМНИЦЕ", 0, 10, 112, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -330, 90, 660, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "XVI ВЕКА?", 0, 155, 100, "#ffffff")
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
