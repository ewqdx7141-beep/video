"""Серия 12 «Зомби» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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
def s0_wake(ctx, t, u, D):
    k = ease(seg(u, 0.8, 2.4))
    ctx.save()
    cam(ctx, t, lerp(540, 540, k), lerp(1500, 900, k), lerp(1.0, 0.85, k), shake=0.25)
    apartment(ctx, t, window_fn=lambda c: city(c, t))
    apt_hero(ctx, 560, 1960, 1.1, emo("sleep") if u < 1.5 else emo("shock"), t, arms="relax" if u < 1.5 else "shock",
             look=(0, -0.7), tremble=0.5 if u > 1.5 else 0, item=lambda c, x, y: coffee_cup(c, x - 10, y + 40, 0.22, t))
    ctx.restore()


def s1_street(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(300, 800, ease(seg(u, 0, D))), 1500, lerp(0.7, 0.8, seg(u, 0, D)), shake=0.4)
    city(ctx, t)
    ctx.restore()
    if (t * 2) % 1 < 0.5:  # мигалки
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#ef4444", 0.06)
    else:
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#3b82f6", 0.06)


def s2_barricade(ctx, t, u, D):
    bk = ease(seg(t, EV["barricade"], EV["barricade"] + 1.6))
    ctx.save()
    cam(ctx, t, 540, 1200, 0.85, shake=0.3 + 0.6 * seg(t, EV["barricade"] + 1.4, EV["barricade"] + 1.7))
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, WALL), (1, "#cfc2b0")])
    ctx.rectangle(-1200, 1500, 3600, 1400)
    fill(ctx, "#854d0e")
    apartment_door(ctx, 330, 1500, 420, 1000, "47")
    for k in range(3):  # замки и цепочка
        rr(ctx, 690, 900 + k * 70, 40, 30, 6)
        fill(ctx, "#a8a29e")
    hanging_lamp(ctx, 540, 120, on=True)
    mailboxes(ctx, -560, 700, 2, 2)
    plant(ctx, 1250, 1500, 1.1, t, "#1d4ed8")
    if bk > 0.6:  # доски крест-накрест
        for a in (0.4, -0.4):
            ctx.save()
            ctx.translate(540, 1000)
            ctx.rotate(a)
            rr(ctx, -330, -24, 660, 48, 6)
            fill(ctx, "#b45309")
            for j in range(3):
                ctx.arc(-280 + j * 280, 0, 8, 0, TAU)
                fill(ctx, "#57534e")
            ctx.restore()
    wardrobe(ctx, lerp(1500, 540, bk), 1520, 0.95, bk)
    apt_hero(ctx, lerp(1900, 900, bk), 2000, 1.05, emo("determined"), t, arms="fwd", walk=t * 5 if bk < 1 else None)
    ctx.restore()
    # удары с той стороны двери
    if t > EV["barricade"] + 1.8 and int(t * 2) % 3 == 0:
        text(ctx, "БУМ", 540, 560, 110, "#ffffff", "#b91c1c", 14)
    step_card(ctx, t, EV["steps"][0], 1, "НЕ ВЫХОДИ\nБАРРИКАДИРУЙ ДВЕРЬ")


def s3_water(ctx, t, u, D):
    tb = EV["tub"]
    k = seg(t, tb - 0.5, TL.shots[4][0])
    ctx.save()
    cam(ctx, t, 540, 1300, 0.9, shake=0.2)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#e0f2fe"), (1, "#bae6fd")])
    for i in range(-10, 20):  # плитка
        for j in range(-4, 20):
            rr(ctx, i * 120, j * 120, 114, 114, 6)
            fill(ctx, "#f8fafc" if (i + j) % 2 else "#e2e8f0")
    rr(ctx, 700, 300, 300, 420, 30)  # зеркало
    fill(ctx, "#cbd5e1")
    line(ctx, 740, 340, 800, 460, 6, "#ffffff", 0.6)
    ctx.rectangle(-1200, 1700, 3600, 1200)
    fill(ctx, "#94a3b8")
    # ванна
    rr(ctx, -260, 1300, 900, 420, 80)
    lgrad(ctx, 0, 1300, 0, 1720, [(0, "#ffffff"), (1, "#cbd5e1")])
    ctx.fill()
    rr(ctx, -220, 1340, 820, 300 * 0.95, 60)
    fill(ctx, "#e2e8f0")
    lv = 260 * k
    rr(ctx, -220, 1640 - lv, 820, lv + 10, 40)
    fill(ctx, "#38bdf8", 0.75)
    line(ctx, 560, 1180, 560, 1640 - lv, 14, "#7dd3fc", 0.9 * (k < 1))
    rr(ctx, 520, 1140, 120, 50, 14)
    fill(ctx, "#a8a29e")
    # ряды бутылок и кастрюли
    for j in range(8):
        f = clamp(k * 1.4 - j * 0.1)
        rr(ctx, 720 + (j % 4) * 80, 1520 + (j // 4) * 180, 60, 150, 14)
        fill(ctx, "#bae6fd", 0.5)
        rr(ctx, 720 + (j % 4) * 80, 1670 + (j // 4) * 180 - 150 * f, 60, 150 * f, 14)
        fill(ctx, "#38bdf8", 0.8)
        rr(ctx, 735 + (j % 4) * 80, 1505 + (j // 4) * 180, 30, 20, 4)
        fill(ctx, "#2563eb")
    for j in range(3):
        rr(ctx, -500 + j * 200, 1800, 170, 120, 14)
        fill(ctx, "#78716c")
        rr(ctx, -500 + j * 200, 1800, 170, 30, 10)
        fill(ctx, "#38bdf8", 0.7 * clamp(k * 2 - j * 0.3))
    apt_hero(ctx, 260, 2150, 1.05, emo("determined"), t, arms="hold", look=(0.6, 0.5),
             item=lambda c, x, y: (rr(c, x - 30, y - 60, 60, 120, 14), fill(c, "#38bdf8", 0.8)))
    ctx.restore()
    step_card(ctx, t, EV["steps"][1], 2, "ВОДА\nНАПОЛНИ ВАННУ")


def s4_food(ctx, t, u, D):
    fr = EV["fridge"]
    op = ease(seg(t, fr - 0.3, fr + 0.6))
    ctx.save()
    cam(ctx, t, lerp(400, 900, ease(seg(t, fr - 1.0, fr + 0.3))), 1150, 0.95, shake=0.2)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#fef3c7"), (1, "#fde68a")])
    for i in range(-10, 20):  # фартук кухни
        rr(ctx, i * 80, 900, 76, 40, 4)
        fill(ctx, "#fbbf24", 0.4)
    ctx.rectangle(-1200, 1500, 3600, 1400)
    fill(ctx, "#78350f")
    rr(ctx, -500, 1000, 1700, 500, 10)  # столешница с консервами
    fill(ctx, "#a16207")
    rr(ctx, -500, 980, 1700, 30, 6)
    fill(ctx, "#e7e5e4")
    r = random.Random(3)
    for j in range(18):
        x = -440 + j * 70
        h = r.uniform(70, 110)
        kind = j % 4
        if kind == 0:
            rr(ctx, x, 980 - h, 56, h, 8)
            fill(ctx, "#94a3b8")
            rr(ctx, x, 980 - h * 0.7, 56, h * 0.4, 0)
            fill(ctx, r.choice(["#dc2626", "#16a34a", "#f59e0b"]))
        elif kind == 1:
            rr(ctx, x, 980 - h - 40, 60, h + 40, 4)
            fill(ctx, r.choice(["#facc15", "#f97316"]))
            text(ctx, "ГРЕЧА" if j % 3 else "РИС", x + 30, 980 - h / 2 - 20, 14, "#78350f")
        elif kind == 2:
            rr(ctx, x, 940, 66, 36, 4)
            fill(ctx, "#7c2d12")
            text(ctx, "ШОКО", x + 33, 958, 14, "#fde68a")
        else:
            rr(ctx, x, 980 - h, 50, h, 12)
            fill(ctx, "#bae6fd", 0.7)
    # холодильник открывается, свет мигает
    rr(ctx, 1200, 500, 360, 1000, 20)
    fill(ctx, "#e5e7eb")
    if op > 0:
        rr(ctx, 1210, 510, 340, 980, 14)
        fill(ctx, "#fefce8" if int(t * 6) % 5 else "#78716c")
        glow(ctx, 1380, 1000, 400, "#fef9c3", 0.5 * op)
        for j in range(4):
            line(ctx, 1220, 700 + j * 200, 1540, 700 + j * 200, 6, "#cbd5e1")
        for j in range(5):
            rr(ctx, 1240 + j * 60, 600 + (j % 2) * 200, 46, 90, 8)
            fill(ctx, r.choice(["#f87171", "#fbbf24", "#86efac", "#ffffff"]))
    ctx.save()
    ctx.translate(1200, 500)
    ctx.scale(1 - op * 0.9, 1)
    rr(ctx, 0, 0, 360, 1000, 20)
    fill(ctx, "#d1d5db")
    rr(ctx, 300, 300, 20, 200, 8)
    fill(ctx, "#9ca3af")
    ctx.restore()
    apt_hero(ctx, 560, 2050, 1.05, emo("determined"), t, arms="hold", look=(-0.6, -0.3),
             item=lambda c, x, y: (rr(c, x - 30, y - 40, 60, 70, 8), fill(c, "#dc2626")))
    ctx.restore()
    step_card(ctx, t, EV["steps"][2], 3, "ЕДА\nКОНСЕРВЫ И КРУПЫ")


def s5_dark(ctx, t, u, D):
    cu = EV["curtains"]
    lt = EV["light"]
    cl = seg(t, cu - 0.3, cu + 0.8)
    ctx.save()
    cam(ctx, t, 540, 1250, 0.85, shake=0.2)
    apartment(ctx, t, dark=0.7 * cl, curtains=cl, window_fn=lambda c: city(c, t, night=0.6))
    # свечи и телефон без звука
    for j in range(3):
        rr(ctx, 400 + j * 70, 1700, 34, 70, 6)
        fill(ctx, "#fef3c7")
        ell(ctx, 417 + j * 70, 1688, 10, 18)
        fill(ctx, "#fbbf24")
        glow(ctx, 417 + j * 70, 1690, 120, "#fbbf24", 0.4 * cl)
    apt_hero(ctx, 900, 2050, 1.0, emo("worry"), t, arms="phone", rim="#fbbf24",
             item=lambda c, x, y: (rr(c, x - 26, y - 100, 52, 96, 8), fill(c, "#111")))
    ctx.restore()
    if t > lt:
        ctx.save()
        ctx.translate(540, 1200)
        ctx.arc(0, 0, 130, 0, TAU)
        fill(ctx, "#0b0b12", 0.85)
        rr(ctx, -30, -60, 60, 100, 10)
        fill(ctx, "#e5e7eb")
        crossmark(ctx, 0, 0, 2.0)
        text(ctx, "БЕЗ ЗВУКА", 0, 90, 30, "#ffffff")
        ctx.restore()
    step_card(ctx, t, EV["steps"][3], 4, "ТИШИНА\nИ ТЕМНОТА")


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


def s6_radio(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1400, lerp(0.9, 1.0, seg(u, 0, D)), shake=0.2)
    apartment(ctx, t, dark=0.7, curtains=1.0, window_fn=lambda c: city(c, t, night=0.8))
    radio_box(ctx, 540, 1580, 0.75, t, 1.0)
    for j in range(4):  # батарейки
        rr(ctx, 860 + j * 46, 1640, 36, 80, 8)
        fill(ctx, "#facc15")
        rr(ctx, 860 + j * 46, 1640, 36, 24, 6)
        fill(ctx, "#111827")
    for j in range(3):  # волны звука
        a = (t * 0.8 + j / 3) % 1
        ctx.arc(420, 1580, 120 + a * 260, -2.4, -0.7)
        ctx.set_line_width(6)
        src(ctx, "#fde68a", 0.6 * (1 - a))
        ctx.stroke()
    apt_hero(ctx, 150, 2050, 1.0, emo("calm"), t, arms="down", look=(0.9, 0.4), rim="#fde68a")
    ctx.restore()
    step_card(ctx, t, EV["steps"][4], 5, "СВЯЗЬ\nРАДИО НА БАТАРЕЙКАХ")


def s7_tally(ctx, t, u, D):
    tl = EV["tally"]
    ctx.save()
    cam(ctx, t, 540, 960, 1.0, shake=0.15)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0f172a"), (1, "#020617")])
    text(ctx, "СВЕРКА ЗАПАСОВ", 540, 300, 84, "#ffffff", "#000", 12)
    items = [("ВОДА", "40 л из 60", 40 / 60, "#38bdf8", "40/60"), ("ЕДА", "10 дней из 14", 10 / 14, "#facc15", "10/14"),
             ("БАРРИКАДА", "есть", 1.0, "#a16207", "1/1"), ("АПТЕЧКА", "есть", 1.0, "#ef4444", "1/1"),
             ("РАДИО", "работает", 1.0, "#22c55e", "1/1")]
    for i, (nm, val, fr, col, frac) in enumerate(items):
        y = 480 + i * 175
        a = seg(t, tl[i] - 0.2, tl[i] + 0.1)
        if a <= 0:
            continue
        rr(ctx, 80, y - 70, 920, 150, 26)
        fill(ctx, "#1e293b", a)
        ix = 140
        if i == 0:
            ctx.move_to(ix, y - 34)
            ctx.curve_to(ix + 30, y, ix + 24, y + 30, ix, y + 30)
            ctx.curve_to(ix - 24, y + 30, ix - 30, y, ix, y - 34)
            fill(ctx, col, a)
        elif i == 1:
            rr(ctx, ix - 26, y - 30, 52, 64, 8)
            fill(ctx, "#94a3b8", a)
            rr(ctx, ix - 26, y - 10, 52, 24, 0)
            fill(ctx, col, a)
        elif i == 2:
            for j in range(3):
                rr(ctx, ix - 34, y - 30 + j * 22, 68, 16, 4)
                fill(ctx, col, a)
        elif i == 3:
            rr(ctx, ix - 32, y - 28, 64, 56, 10)
            fill(ctx, "#f8fafc", a)
            rr(ctx, ix - 6, y - 20, 12, 40, 2)
            fill(ctx, col, a)
            rr(ctx, ix - 20, y - 6, 40, 12, 2)
            fill(ctx, col, a)
        else:
            rr(ctx, ix - 34, y - 20, 68, 44, 8)
            fill(ctx, "#a16207", a)
            ctx.arc(ix - 14, y + 2, 12, 0, TAU)
            fill(ctx, "#292524", a)
            line(ctx, ix + 20, y - 20, ix + 34, y - 44, 4, "#9ca3af", a)
        text(ctx, nm, 200, y - 22, 46, col, align="left", alpha=a)
        text(ctx, val, 200, y + 32, 32, "#cbd5e1", align="left", alpha=a)
        bar(ctx, 560, y - 14, 260, fr * ease(seg(t, tl[i], tl[i] + 0.6)), col)
        text(ctx, frac, 960, y, 46, "#ffffff", align="right", alpha=a)
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
    ctx.arc(540, 900, 300, math.pi * 0.75, math.pi * 0.75 + math.pi * 1.5 * 0.85 * k)
    ctx.set_line_width(50)
    src(ctx, "#22c55e")
    ctx.stroke()
    text(ctx, f"{int(85 * k)}%", 540, 880, 170, "#ffffff")
    text(ctx, "ДОЖИТЬ ДО СПАСЕНИЯ", 540, 1040, 46, "#94a3b8")
    for j in range(8):  # «дни» под шкалой
        rr(ctx, 210 + j * 85, 1260, 70, 70, 12)
        fill(ctx, "#22c55e" if j < int(8 * k) else "#1e293b")
    ctx.restore()


def s9_silent(ctx, t, u, D):
    sl = EV["silent"]
    fz = EV["freeze"]
    ctx.save()
    if t < fz - 0.3:
        cam(ctx, t, 540, 1350, 1.2, shake=0.15)
        apartment(ctx, t, dark=0.8, curtains=1.0, window_fn=lambda c: city(c, t, night=1.0))
        radio_box(ctx, 540, 1580, 0.75, t, 0.0 if t > sl else 1.0, glitch=1.0 if t > sl - 0.5 else 0)
        if t > sl:
            text(ctx, "...", 540, 1250, 120, "#94a3b8")
    else:
        cam(ctx, t, 540, 1650, 0.9, shake=0.1)
        city(ctx, t, night=1.0, crowd_mode="freeze", t_turn=fz)
        # герой подсматривает из-за шторы: силуэт в окне сверху
    ctx.restore()


def s10_flee(ctx, t, u, D):
    tu = EV["turn"]
    rn = EV["run"]
    ctx.save()
    cam(ctx, t, lerp(540, 300, ease(seg(t, rn, TL.shots[11][0]))), 1650, 0.85, shake=0.2 + 0.6 * seg(t, rn, rn + 0.3))
    if t < rn:
        city(ctx, t, night=1.0, crowd_mode="freeze", t_turn=tu, show_crowd=False)
        for p in zcrowd(77, 34, 1420, 2250):
            d0 = p.dir
            p.dir = -1 if t > tu + (p.seed % 1) * 0.5 else d0
            npc(ctx, p, tu, walking=False, zombie=1.0)
            p.dir = d0
    else:
        city(ctx, t, night=1.0, crowd_mode="flee", t_turn=rn)
    ctx.restore()


def s11_fled(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1500, lerp(1.5, 1.7, seg(u, 0, D)), shake=0.4)
    city(ctx, t, night=1.0, show_crowd=False)
    r = random.Random(9)
    lt = t - TL.shots[11][0]
    for i in range(9):  # бегущие зомби крупно, с испуганными лицами
        p = Npc(r, 900 + i * 230, 1950 + (i % 3) * 70, 1.1, -1, 3.0)
        p.item = "none"
        x = npc(ctx, p, lt, walking=True, zombie=1.0)
        ell(ctx, x - 75, p.y - 520, 10, 16)  # капля пота
        fill(ctx, "#bfe6ff", 0.8)
    speed_lines(ctx, 1080, 2400, t, n=30, a=0.4)
    ctx.restore()


def monster(ctx, x, y, s, t, eyes=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(-900, 600)
    ctx.curve_to(-900, -500, -500, -1100, 0, -1150)
    ctx.curve_to(500, -1100, 900, -500, 900, 600)
    ctx.close_path()
    fill(ctx, "#1c0606")
    ctx.move_to(-900, 600)
    ctx.curve_to(-900, -500, -500, -1100, 0, -1150)
    ctx.curve_to(500, -1100, 900, -500, 900, 600)
    ctx.set_line_width(14)
    src(ctx, "#ef4444", 0.6)
    ctx.stroke()
    for k in range(9):  # шипы
        a = -math.pi * 0.9 + k * math.pi * 0.8 / 8
        bx, by = math.cos(a) * 850, math.sin(a) * 1050
        ctx.move_to(bx - 50, by + 20)
        ctx.line_to(bx * 1.18, by * 1.18)
        ctx.line_to(bx + 50, by + 20)
        fill(ctx, "#020617")
    for side in (-1, 1):
        ex, ey = side * 260, -620
        glow(ctx, ex, ey, 360, "#ef4444", 0.6 * eyes)
        ell(ctx, ex, ey, 130, 60 * eyes + 1)
        fill(ctx, "#fde047")
        ell(ctx, ex, ey, 30, 55 * eyes + 1)
        fill(ctx, "#7f1d1d")
    ctx.restore()


def s12_rise(ctx, t, u, D):
    ri = EV["rise"]
    ey = EV["eyes"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        k = ease(seg(t, ri - 0.8, ey))
        cam(ctx, t, 540, lerp(1300, 900, k), lerp(0.9, 0.75, k), shake=0.3 + 0.8 * k)
        vgrad(ctx, -1500, -1200, 4000, 2600, [(0, "#0b1022"), (1, "#3b0a0a")])
        stars(ctx, 4, 1080, 600, t, 40)
        monster(ctx, 540, lerp(2500, 1000, k), 0.9, t, eyes=ease(seg(t, ey - 0.2, ey + 0.4)))
        skyline(ctx, 21, -1400, 2600, 1300, 300, 800, "#0f172a", "#fde68a", 0.05, wmin=140, wmax=240)
        for j in range(6):  # птицы улетают
            bx = (j * 300 + t * 200) % 1800 - 300
            by = 500 + j * 40 + math.sin(t * 3 + j) * 20
            ctx.move_to(bx - 26, by)
            ctx.curve_to(bx - 13, by - 14, bx - 4, by - 8, bx, by)
            ctx.curve_to(bx + 4, by - 8, bx + 13, by - 14, bx + 26, by)
            ctx.set_line_width(5)
            src(ctx, "#94a3b8")
            ctx.stroke()
        apt_hero(ctx, 540, 2450, 1.6, emo("shock"), t, arms="down", back=True, legs=False, rim="#ef4444")
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
        text(ctx, "От чего они бегут?", 0, 180, 70, "#ef4444")
    ctx.restore()


SCENES = [s0_wake, s1_street, s2_barricade, s3_water, s4_food, s5_dark, s6_radio, s7_tally, s8_chance, s9_silent,
          s10_flee, s11_fled, s12_rise]
LABELS = {1: "ДЕНЬ 1", 2: "ДЕНЬ 1", 3: "ДЕНЬ 1", 4: "ДЕНЬ 1", 5: "ДЕНЬ 2", 6: "ДЕНЬ 3", 9: "НОЧЬ 12",
          10: "НОЧЬ 12", 11: "НОЧЬ 12", 12: "НОЧЬ 12"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("сорок", "литров", "из", "шестидесяти"), "40 л из 60"), (("десять", "дней", "из", "четырнадцати"), "10 дней из 14"),
         (("восемьдесят", "пять", "процентов"), "85%"), (("двенадцатую",), "12-ю")]


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
        text(ctx, "ЧТО, ЕСЛИ", 0, -110, 88, "#ffffff", "#000", 16, shadow=True)
        text(ctx, "НАЧАЛСЯ", 0, 10, 116, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -440, 90, 880, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "ЗОМБИ-АПОКАЛИПСИС?", 0, 155, 76, "#ffffff")
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
