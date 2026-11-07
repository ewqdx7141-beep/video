"""Серия 26 «Тонущий корабль» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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










# ================================================================== ТОНУЩИЙ КОРАБЛЬ
ROSE = ("#be123c", "#881337")
VEST = "#f97316"
SHIP_NAME = "ПОЛЯРНАЯ ЗВЕЗДА"


def vest_on(ctx, x, y, sc, legs=True, back=False):
    by = y - (345 if legs else 175) * sc
    rr(ctx, x - 92 * sc, by, 184 * sc, 175 * sc, 30 * sc)
    fill(ctx, VEST)
    for k in range(2):  # светоотражающие полосы
        rr(ctx, x - 92 * sc, by + (50 + k * 60) * sc, 184 * sc, 16 * sc, 4 * sc)
        fill(ctx, "#e5e7eb")
    if not back:
        line(ctx, x, by, x, by + 175 * sc, 5 * sc, "#c2410c")
        ctx.arc(x - 50 * sc, by + 26 * sc, 10 * sc, 0, TAU)  # свисток
        fill(ctx, "#facc15")
        ctx.arc(x + 50 * sc, by + 26 * sc, 10 * sc, 0, TAU)  # лампочка
        fill(ctx, "#fef08a")
        glow(ctx, x + 50 * sc, by + 26 * sc, 40 * sc, "#fef08a", 0.7)


def sailor(ctx, x, y, sc, e, t, arms="relax", look=(0, 0), walk=None, back=False, legs=True, tremble=0.0, item=None,
           vest=True):
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, walk=walk, back=back, legs=legs, tremble=tremble,
         rim="#bae6fd", rim_a=0.55, hood=ROSE, hand_item=item)
    if vest:
        vest_on(ctx, x, y, sc, legs, back)


def life_jacket(ctx, x, y, s, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ctx.move_to(-120, -160)
    ctx.line_to(-40, -160)
    ctx.line_to(-30, -60)
    ctx.line_to(30, -60)
    ctx.line_to(40, -160)
    ctx.line_to(120, -160)
    ctx.line_to(140, 160)
    ctx.line_to(-140, 160)
    ctx.close_path()
    fill(ctx, VEST)
    for k in range(2):
        rr(ctx, -140, 20 + k * 70, 280, 22, 4)
        fill(ctx, "#e5e7eb")
    line(ctx, 0, -60, 0, 160, 6, "#c2410c")
    ctx.arc(-70, -100, 14, 0, TAU)
    fill(ctx, "#facc15")
    line(ctx, -70, -86, -60, -40, 3, "#111")
    ctx.arc(70, -100, 14, 0, TAU)
    fill(ctx, "#fef08a")
    text(ctx, "12", 70, 100, 40, "#7c2d12")
    ctx.restore()


def night_sea(ctx, t, horizon=1000, dawn=0.0, moon=True):
    vgrad(ctx, -1500, -1200, 4000, horizon + 1200, [(0, mixh("#020617", "#fb923c", dawn * 0.6)),
                                                    (1, mixh("#1e293b", "#fde68a", dawn))])
    if dawn < 0.5:
        stars(ctx, 12, 1080, horizon, t, 70)
    if moon:
        ctx.arc(820, 300, 70, 0, TAU)
        fill(ctx, "#f8fafc", 1 - dawn)
        glow(ctx, 820, 300, 300, "#e0f2fe", 0.4 * (1 - dawn))
    ctx.rectangle(-1500, horizon, 4000, 2400)
    lgrad(ctx, 0, horizon, 0, horizon + 1400, [(0, mixh("#0f172a", "#475569", dawn)), (1, "#020617")])
    ctx.fill()
    if moon and dawn < 1:
        for k in range(14):  # лунная дорожка
            y = horizon + 20 + k * 50
            w = 40 + k * 18 + math.sin(t * 2 + k) * 10
            rr(ctx, 820 - w / 2 + math.sin(t + k) * 20, y, w, 8, 4)
            fill(ctx, "#e0f2fe", 0.5 * (1 - k / 14) * (1 - dawn))
    waves(ctx, t, horizon + 60, 10, "#93c5fd", 0.35, 14)


def mixh(c1, c2, k):
    a, b = hexc(c1), hexc(c2)
    return "#%02x%02x%02x" % tuple(int(255 * (a[i] + (b[i] - a[i]) * clamp(k))) for i in range(3))


def waves(ctx, t, y0, amp=12, col="#ffffff", a=0.6, n=8):
    for k in range(n):
        y = y0 + k * 44
        ctx.move_to(-1500, y)
        for i in range(60):
            x = -1500 + i * 70
            ctx.line_to(x, y + math.sin(x * 0.01 + t * 2 + k) * amp)
        ctx.set_line_width(4)
        src(ctx, col, a * (1 - k / n))
        ctx.stroke()


def liner(ctx, x, y, s, t, tilt=0.0, lights=1.0, sink=0.0, dawn=0.0, smoke=True):
    """Круизный лайнер сбоку; (x, y) — ватерлиния по центру."""
    ctx.save()
    ctx.translate(x, y + sink)
    ctx.rotate(tilt)
    ctx.scale(s, s)
    ctx.move_to(-900, -260)  # корпус
    ctx.line_to(900, -260)
    ctx.line_to(820, 60)
    ctx.line_to(-760, 60)
    ctx.curve_to(-860, 0, -900, -120, -900, -260)
    ctx.close_path()
    fill(ctx, "#f8fafc")
    ctx.move_to(-780, 0)
    ctx.line_to(838, 0)
    ctx.line_to(820, 60)
    ctx.line_to(-760, 60)
    ctx.close_path()
    fill(ctx, "#1e3a8a")
    line(ctx, -880, -120, 870, -120, 10, "#1d4ed8")
    for k in range(4):  # надстройка
        w = 1500 - k * 220
        rr(ctx, -w / 2 - 40, -260 - (k + 1) * 90, w, 90, 6)
        fill(ctx, "#f1f5f9" if k % 2 == 0 else "#e2e8f0")
        line(ctx, -w / 2 - 40, -260 - (k + 1) * 90, w / 2 - 40, -260 - (k + 1) * 90, 4, "#94a3b8")
        for j in range(int(w / 50)):  # окна
            on = random.Random(k * 100 + j).random() < 0.75 * lights
            rr(ctx, -w / 2 - 20 + j * 50, -260 - (k + 1) * 90 + 26, 30, 36, 4)
            fill(ctx, "#fde68a" if on else "#334155")
    for j in range(32):  # иллюминаторы
        ctx.arc(-800 + j * 52, -190, 11, 0, TAU)
        fill(ctx, "#fde68a" if random.Random(500 + j).random() < 0.7 * lights else "#334155")
    for k in range(6):  # шлюпки на шлюпбалках
        bx = -620 + k * 230
        line(ctx, bx - 60, -380, bx - 60, -300, 6, "#64748b")
        line(ctx, bx + 60, -380, bx + 60, -300, 6, "#64748b")
        rr(ctx, bx - 90, -330, 180, 50, 24)
        fill(ctx, VEST)
        rr(ctx, bx - 70, -340, 140, 16, 6)
        fill(ctx, "#fff7ed")
    for k in range(2):  # трубы
        fx = -150 + k * 300
        ctx.move_to(fx - 70, -620)
        ctx.line_to(fx + 60, -620)
        ctx.line_to(fx + 80, -800)
        ctx.line_to(fx - 40, -800)
        ctx.close_path()
        fill(ctx, "#b91c1c")
        rr(ctx, fx - 46, -800, 126, 30, 4)
        fill(ctx, "#111827")
        rr(ctx, fx - 60, -720, 130, 26, 4)
        fill(ctx, "#1d4ed8")
        if smoke:
            puff(ctx, fx + 20, -820, t, 30 + k, n=5, col="#94a3b8", life=2.0, rate=0.4, dx=-160, dy=-120, a=0.35)
    text(ctx, SHIP_NAME, -520, -60, 46, "#1e3a8a")
    line(ctx, -900, -270, 900, -270, 4, "#94a3b8")  # леер
    for j in range(36):
        line(ctx, -880 + j * 50, -300, -880 + j * 50, -270, 2, "#94a3b8")
    if lights:
        glow(ctx, 0, -400, 1200, "#fde68a", 0.18 * lights)
    ctx.restore()


def porthole(ctx, x, y, r, t, tilt=0.0):
    ctx.save()
    ctx.arc(x, y, r, 0, TAU)
    ctx.clip()
    ctx.translate(x, y)
    ctx.rotate(-tilt)
    vgrad(ctx, -r * 2, -r * 2, r * 4, r * 4, [(0, "#020617"), (0.5, "#1e293b"), (1, "#0f172a")])
    ctx.rectangle(-r * 2, 0, r * 4, r * 2)
    fill(ctx, "#0f172a")
    for k in range(4):
        line(ctx, -r * 2, 10 + k * 18 + math.sin(t * 2 + k) * 6, r * 2, 10 + k * 18 + math.cos(t * 2 + k) * 6, 3,
             "#93c5fd", 0.4)
    ctx.arc(r * 0.4, -r * 0.4, r * 0.15, 0, TAU)
    fill(ctx, "#f8fafc")
    ctx.restore()
    ctx.arc(x, y, r, 0, TAU)
    ctx.set_line_width(r * 0.18)
    src(ctx, "#b45309")
    ctx.stroke()
    for k in range(8):
        a = k / 8 * TAU
        ctx.arc(x + math.cos(a) * r * 1.0, y + math.sin(a) * r * 1.0, r * 0.05, 0, TAU)
        fill(ctx, "#fde68a")


def cabin_room(ctx, t, tilt=0.0, slide=0.0, wardrobe_open=0.0):
    ctx.save()
    ctx.translate(540, 1300)
    ctx.rotate(tilt)
    ctx.translate(-540, -1300)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#1e293b"), (1, "#0f172a")])
    rr(ctx, -600, 200, 2400, 1500, 0)
    fill(ctx, "#334155")
    for k in range(-6, 16):  # обои с узором
        for j in range(10):
            ctx.arc(k * 140 + (j % 2) * 70, 260 + j * 140, 8, 0, TAU)
            fill(ctx, "#475569")
    porthole(ctx, 540, 560, 150, t, tilt)
    rr(ctx, 120, 700, 200, 150, 6)  # картина
    fill(ctx, "#78350f")
    rr(ctx, 134, 714, 172, 122, 4)
    fill(ctx, "#38bdf8")
    ctx.move_to(134, 836)
    ctx.line_to(220, 760)
    ctx.line_to(306, 836)
    fill(ctx, "#0e7490")
    rr(ctx, 800, 500, 340, 1000, 10)  # шкаф
    fill(ctx, "#78350f")
    if wardrobe_open > 0:
        rr(ctx, 820, 520, 300, 960, 6)
        fill(ctx, "#1c1917")
        for k in range(2):
            life_jacket(ctx, 900 + k * 150, 860, 0.45, 0.05 * k)
        rr(ctx, 1120, 520, 300 * wardrobe_open, 960, 6)
        fill(ctx, "#92400e")
    else:
        line(ctx, 970, 520, 970, 1480, 4, "#451a03")
    rr(ctx, 840, 560, 260, 70, 6)
    fill(ctx, "#fde68a")
    text(ctx, "ЖИЛЕТЫ", 970, 595, 32, "#7c2d12")
    rr(ctx, -500, 1250, 760, 200, 20)  # кровать
    fill(ctx, "#f1f5f9")
    rr(ctx, -500, 1200, 300, 90, 30)
    fill(ctx, "#e2e8f0")
    rr(ctx, -300, 1250, 560, 150, 20)
    fill(ctx, "#1d4ed8")
    rr(ctx, 300, 1200, 180, 180, 10)  # тумбочка
    fill(ctx, "#92400e")
    ctx.save()  # лампа на тумбочке клонится
    ctx.translate(360, 1200)
    ctx.rotate(-tilt * 1.5 + math.sin(t * 3) * 0.05)
    table_lamp(ctx, 0, 0, 0.7, on=True)
    ctx.restore()
    ctx.save()  # бокал
    ctx.translate(440 - slide * 60, 1200)
    ctx.rotate(-tilt * 2)
    ctx.move_to(-20, -80)
    ctx.line_to(20, -80)
    ctx.line_to(10, -40)
    ctx.line_to(-10, -40)
    ctx.close_path()
    fill(ctx, "#fecaca", 0.8)
    line(ctx, 0, -40, 0, 0, 4, "#e5e7eb")
    line(ctx, -16, 0, 16, 0, 4, "#e5e7eb")
    ctx.restore()
    ctx.rectangle(-1200, 1700, 3600, 1200)
    fill(ctx, "#7f1d1d")
    for k in range(-10, 24):  # ковёр с узором
        ctx.arc(k * 120, 1800 + (k % 2) * 60, 16, 0, TAU)
        fill(ctx, "#facc15", 0.4)
    ctx.save()  # чемодан скользит
    ctx.translate(lerp(-200, 700, slide), 1700)
    rr(ctx, -110, -180, 220, 180, 16)
    fill(ctx, "#0e7490")
    rr(ctx, -40, -210, 80, 30, 10)
    fill(ctx, "#164e63")
    for sd in (-80, 80):
        ctx.arc(sd, 8, 12, 0, TAU)
        fill(ctx, "#111")
    ctx.restore()
    ctx.restore()


def ship_corridor(ctx, t, x0=-1200, x1=3000, tilt=0.0, nums=range(700, 730, 2), siren=0.0, dark=0.0):
    ctx.save()
    ctx.translate(540, 1300)
    ctx.rotate(tilt)
    ctx.translate(-540, -1300)
    vgrad(ctx, x0 - 800, -800, x1 - x0 + 1600, 3600, [(0, "#fef3c7"), (1, "#fde68a")])
    ctx.rectangle(x0 - 800, 1150, x1 - x0 + 1600, 600)
    fill(ctx, "#78350f")
    line(ctx, x0 - 800, 1150, x1 + 800, 1150, 10, "#d4a849")
    for i, n in enumerate(nums):  # двери кают
        dx = x0 + 200 + i * 360
        rr(ctx, dx, 760, 220, 940, 6)
        fill(ctx, "#92400e")
        rr(ctx, dx + 20, 780, 180, 360, 4)
        ctx.set_line_width(4)
        src(ctx, "#78350f")
        ctx.stroke()
        rr(ctx, dx + 60, 680, 100, 54, 6)
        fill(ctx, "#d4a849")
        text(ctx, str(n), dx + 110, 708, 32, "#451a03")
        ctx.arc(dx + 190, 1240, 10, 0, TAU)
        fill(ctx, "#d4a849")
        rr(ctx, dx + 40, 1300, 140, 50, 6)
        fill(ctx, "#ffffff")
        text(ctx, f"ШЛЮПКА {(n // 2) % 14 + 1}", dx + 110, 1325, 18, "#c2410c")
        if i % 2 == 0:  # бра
            rr(ctx, dx + 280, 600, 40, 60, 10)
            fill(ctx, "#fef3c7")
            glow(ctx, dx + 300, 630, 140, "#fde68a", 0.4)
    for i in range(int((x1 - x0) / 900) + 1):
        ex = x0 + 400 + i * 900
        rr(ctx, ex, 320, 260, 90, 8)
        fill(ctx, "#16a34a")
        text(ctx, "ВЫХОД", ex + 110, 365, 40, "#ffffff")
        line(ctx, ex + 210, 390, ex + 210, 340, 6, "#ffffff")
        line(ctx, ex + 210, 340, ex + 192, 360, 6, "#ffffff")
        line(ctx, ex + 210, 340, ex + 228, 360, 6, "#ffffff")
    ctx.rectangle(x0 - 800, 1700, x1 - x0 + 1600, 1200)
    fill(ctx, "#57534e")
    ctx.rectangle(x0 - 800, 1760, x1 - x0 + 1600, 260)  # ковровая дорожка
    fill(ctx, "#991b1b")
    for k in range(int((x1 - x0) / 160) + 10):
        xk = x0 - 800 + k * 160
        ctx.move_to(xk, 1890)
        ctx.line_to(xk + 40, 1800)
        ctx.line_to(xk + 80, 1890)
        ctx.line_to(xk + 40, 1980)
        ctx.close_path()
        fill(ctx, "#facc15", 0.6)
    line(ctx, x0 - 800, 1775, x1 + 800, 1775, 6, "#facc15")
    line(ctx, x0 - 800, 2005, x1 + 800, 2005, 6, "#facc15")
    ctx.restore()
    if siren:
        ctx.save()
        ctx.identity_matrix()
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#dc2626", 0.25 * siren * (0.5 + 0.5 * math.sin(t * 8)))
        ctx.restore()
    if dark:
        ctx.save()
        ctx.identity_matrix()
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#000", dark)
        ctx.restore()


def crowd_vests(ctx, t, seed=3, n=6, y0=1800, x0=-200, dx=260, blanket=False, walking=True, sc=1.0):
    r = random.Random(seed)
    for i in range(n):
        p = Npc(r, x0 + i * dx, y0 + (i % 3) * 50, sc * (0.9 + (i % 3) * 0.08), r.choice((-1, 1)), 0.6)
        p.item = "none"
        npc(ctx, p, t * 0.8 + i, walking=walking)
        s_ = p.sc
        vy = p.y - 330 * s_
        rr(ctx, p.x - 62 * s_, vy, 124 * s_, 130 * s_, 18 * s_)
        fill(ctx, VEST)
        rr(ctx, p.x - 62 * s_, vy + 50 * s_, 124 * s_, 12 * s_, 3 * s_)
        fill(ctx, "#e5e7eb")
        if blanket:
            rr(ctx, p.x - 80 * s_, vy - 20 * s_, 160 * s_, 200 * s_, 30 * s_)
            fill(ctx, ("#a8a29e", "#64748b", "#7c3aed")[i % 3], 0.85)
            for k in range(3):
                line(ctx, p.x - 70 * s_, vy + (20 + k * 50) * s_, p.x + 70 * s_, vy + (20 + k * 50) * s_, 4 * s_,
                     "#ffffff", 0.3)


def lifeboat(ctx, x, y, s, t, people=3, seed=5):
    ctx.save()
    ctx.translate(x, y + math.sin(t * 1.4) * 14)
    ctx.rotate(math.sin(t * 1.1) * 0.03)
    ctx.scale(s, s)
    r = random.Random(seed)
    for i in range(people):  # люди в пледах
        px = -260 + i * (520 / max(1, people - 1))
        ctx.arc(px, -150, 46, 0, TAU)
        fill(ctx, r.choice(SKINS))
        ell(ctx, px, -200, 50, 22)
        fill(ctx, r.choice(HAIRS))
        rr(ctx, px - 60, -110, 120, 120, 30)
        fill(ctx, r.choice(("#a8a29e", "#64748b", "#7c3aed")))
    ctx.move_to(-420, -60)
    ctx.line_to(420, -60)
    ctx.line_to(340, 60)
    ctx.line_to(-340, 60)
    ctx.close_path()
    fill(ctx, VEST)
    rr(ctx, -420, -80, 840, 30, 12)
    fill(ctx, "#fff7ed")
    text(ctx, "12", 0, 0, 60, "#7c2d12")
    for k in range(6):
        ctx.arc(-300 + k * 120, -66, 8, 0, TAU)
        fill(ctx, "#1e293b")
    ctx.restore()


# ================================================================== СЦЕНЫ
def tilt_at(t):
    return 0.12 * ease(seg(t, EV["impact"], EV["impact"] + 1.2))


def s0_hook(ctx, t, u, D):
    im = EV["impact"]
    ctx.save()
    jolt = seg(t, im, im + 0.1) * (1 - seg(t, im + 0.1, im + 0.9))
    cam(ctx, t, 540, 1250, lerp(0.9, 1.0, seg(u, 0, D)), shake=0.2 + 2.2 * jolt)
    tl = tilt_at(t)
    cabin_room(ctx, t, tl, slide=seg(t, EV["tilt"] - 0.5, EV["tilt"] + 1.5))
    if t < im:  # спит в кровати
        ctx.save()
        ctx.translate(80, 1180)
        hero_head(ctx, 0, 0, 90, emo("sleep"), t, rim="#bae6fd", rim_a=0.4)
        ctx.restore()
        text(ctx, "z", 220, 1020 - (t * 60) % 120, 50, "#e0f2fe", alpha=0.7)
    else:
        sailor(ctx, 300, 1950, 1.0, emo("shock"), t, arms="shock", vest=False, tremble=0.4, look=(0.6, -0.3))
    ctx.restore()


def s1_siren(ctx, t, u, D):
    lo = EV["long"]
    ctx.save()
    cam(ctx, t, lerp(400, 800, seg(u, 0, D)), 1300, 0.85, rot=-0.12, shake=0.4)
    ship_corridor(ctx, t, siren=1.0)
    crowd_vests(ctx, t, 2, 7, 1900, -300, 300, walking=True)
    ctx.restore()
    n = min(7, int((t - TL.shots[1][0]) / 0.35))  # 7 коротких + 1 длинный
    for k in range(8):
        x = 160 + k * 110
        if k < 7:
            rr(ctx, x - 30, 700, 60, 60, 12)
            fill(ctx, "#ef4444" if k < n else "#334155")
        else:
            rr(ctx, x - 30, 700, 160, 60, 12)
            fill(ctx, "#ef4444" if t > lo else "#334155")
    rr(ctx, 140, 560, 800, 110, 30)
    fill(ctx, "#0b0b12", 0.9)
    text(ctx, "ПОКИНУТЬ СУДНО", 540, 615, 60, "#ef4444" if (t * 3) % 1 < 0.6 else "#ffffff")


def s2_vest(ctx, t, u, D):
    wd, po = EV["wardrobe"], EV["puton"]
    ctx.save()
    cam(ctx, t, 700, 1250, 0.9, shake=0.3)
    cabin_room(ctx, t, 0.12, slide=1.0, wardrobe_open=seg(t, wd - 0.3, wd + 0.3))
    sailor(ctx, 520, 1950, 1.0, emo("determined"), t, arms="fwd" if t < po else "relax", vest=t > po,
           look=(0.7, -0.2))
    ctx.restore()
    if t > po:
        checkmark(ctx, 880, 1350, 1.6, OK, seg(t, po, po + 0.3))
    step_card(ctx, t, EV["steps"][0], 1, "ЖИЛЕТ\nНАДЕВАЙ СРАЗУ")


def s3_stairs(ctx, t, u, D):
    li = EV["lifts"]
    ctx.save()
    cam(ctx, t, 540, lerp(1500, 1150, seg(u, 0, D)), 0.85, rot=-0.08, shake=0.3)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#fef3c7"), (1, "#fcd34d")])
    for k in range(14):  # лестница вверх
        x = -100 + k * 110
        y = 2100 - k * 110
        rr(ctx, x, y, 140, 30, 4)
        fill(ctx, "#991b1b")
        rr(ctx, x, y + 30, 140, 110, 0)
        fill(ctx, "#78350f")
    line(ctx, -100, 1850, 1450, 300, 12, "#d4a849")  # поручень
    for k in range(14):
        line(ctx, -40 + k * 110, 2060 - k * 110, -40 + k * 110, 1830 - k * 110, 6, "#d4a849")
    rr(ctx, 760, 1300, 360, 600, 8)  # лифт
    lgrad(ctx, 760, 0, 1120, 0, [(0, "#9ca3af"), (0.5, "#e5e7eb"), (1, "#9ca3af")])
    ctx.fill()
    line(ctx, 940, 1300, 940, 1900, 4, "#4b5563")
    rr(ctx, 790, 1220, 300, 60, 8)
    fill(ctx, "#111")
    text(ctx, "НЕ РАБОТАЕТ", 940, 1250, 30, "#ef4444")
    if t > li:
        crossmark(ctx, 940, 1600, 2.4)
    k = seg(u, 0, D)
    sailor(ctx, lerp(150, 560, k), lerp(2070, 1640, k), 0.9, emo("determined"), t, arms="relax", walk=t * 7,
           look=(0.5, -0.5))
    crowd_vests(ctx, t, 4, 3, 1950, -500, 250, walking=True, sc=0.9)
    ctx.restore()
    step_card(ctx, t, EV["steps"][1], 2, "НАВЕРХ\nПО ЛЕСТНИЦЕ")


def s4_boat(ctx, t, u, D):
    bn = EV["boatno"]
    ctx.save()
    cam(ctx, t, 540, 1150, 0.85, rot=-0.06, shake=0.3)
    night_sea(ctx, t, 1500, moon=True)
    rr(ctx, -1200, 1500, 3600, 120, 0)  # палуба
    fill(ctx, "#a16207")
    for k in range(-12, 30):
        line(ctx, k * 120, 1500, k * 120 - 40, 1620, 3, "#78350f")
    for k in range(-8, 20):  # леер
        line(ctx, k * 120, 1380, k * 120, 1500, 6, "#e5e7eb")
    line(ctx, -1200, 1380, 2400, 1380, 8, "#e5e7eb")
    for k in range(2):  # шлюпки на шлюпбалках
        bx = 200 + k * 700
        line(ctx, bx - 220, 1380, bx - 220, 700, 16, "#64748b")
        line(ctx, bx - 220, 700, bx - 120, 760, 16, "#64748b")
        line(ctx, bx + 220, 1380, bx + 220, 700, 16, "#64748b")
        line(ctx, bx + 220, 700, bx + 120, 760, 16, "#64748b")
        ctx.save()
        ctx.translate(bx, 900)
        ctx.scale(0.6, 0.6)
        ctx.move_to(-380, -60)
        ctx.line_to(380, -60)
        ctx.line_to(300, 80)
        ctx.line_to(-300, 80)
        ctx.close_path()
        fill(ctx, VEST)
        rr(ctx, -380, -90, 760, 36, 14)
        fill(ctx, "#fff7ed")
        text(ctx, str(11 + k), 0, 10, 80, "#7c2d12")
        ctx.restore()
    rr(ctx, 680, 1080, 300, 120, 12)  # табличка
    fill(ctx, "#ffffff")
    text(ctx, "ШЛЮПКА 12", 830, 1140, 46, "#c2410c")
    crowd_vests(ctx, t, 6, 6, 1900, -400, 280, walking=False, blanket=True)
    sailor(ctx, 540, 2000, 1.0, emo("determined"), t, arms="relax", look=(0.6, -0.4))
    ctx.restore()
    if t > bn:  # дверь каюты с номером шлюпки
        a = seg(t, bn, bn + 0.3)
        rr(ctx, 60, 1180, 400, 260, 20)
        fill(ctx, "#92400e", a)
        rr(ctx, 120, 1220, 280, 70, 8)
        fill(ctx, "#d4a849", a)
        text(ctx, "712", 260, 1255, 44, "#451a03", alpha=a)
        rr(ctx, 100, 1320, 320, 80, 8)
        fill(ctx, "#ffffff", a)
        text(ctx, "ШЛЮПКА 12", 260, 1360, 40, "#c2410c", alpha=a)
    step_card(ctx, t, EV["steps"][2], 3, "К СВОЕЙ\nШЛЮПКЕ")


def s5_warm(ctx, t, u, D):
    cl, wa = EV["clothes"], EV["water"]
    ctx.save()
    cam(ctx, t, 540, 1200, 0.95, rot=-0.05, shake=0.2)
    cabin_room(ctx, t, 0.1, slide=1.0, wardrobe_open=1.0)
    sailor(ctx, 540, 1950, 1.0, emo("calm"), t, arms="relax")
    if t > cl:  # куртка-плед поверх
        a = seg(t, cl, cl + 0.3)
        rr(ctx, 540 - 120, 1950 - 360, 240, 230, 40)
        fill(ctx, "#475569", 0.9 * a)
        for k in range(4):
            line(ctx, 430, 1620 + k * 50, 650, 1620 + k * 50, 5, "#ffffff", 0.25 * a)
        ctx.arc(540, 1950 - 540, 112, math.pi * 1.08, math.pi * 1.92)  # шапка
        ctx.close_path()
        fill(ctx, "#be123c", a)
    ctx.restore()
    for k in range(2):  # бутылки воды
        if t > wa + k * 0.3:
            a = seg(t, wa + k * 0.3, wa + k * 0.3 + 0.3)
            x = 780 + k * 120
            rr(ctx, x - 34, 1100, 68, 200, 20)
            fill(ctx, "#7dd3fc", 0.85 * a)
            rr(ctx, x - 20, 1070, 40, 34, 6)
            fill(ctx, "#1d4ed8", a)
            rr(ctx, x - 34, 1170, 68, 50, 4)
            fill(ctx, "#ffffff", a)
    text(ctx, "+8°C В МОРЕ", 300, 780, 60, "#93c5fd", "#000", 8, alpha=seg(t, wa + 0.5, wa + 0.8))
    step_card(ctx, t, EV["steps"][3], 4, "ТЕПЛО\nИ ВОДА")


def s6_jump(ctx, t, u, D):
    ju = EV["jump"]
    ctx.save()
    k = ease(seg(t, ju - 0.4, ju + 1.4))
    cam(ctx, t, 540, lerp(1000, 1500, k), 0.8, shake=0.3)
    night_sea(ctx, t, 1700, moon=True)
    rr(ctx, -1200, -400, 1100, 2100, 0)  # борт корабля
    fill(ctx, "#f8fafc")
    for j in range(16):
        ctx.arc(-200, -300 + j * 120, 18, 0, TAU)
        fill(ctx, "#fde68a")
    line(ctx, -100, -400, -100, 1700, 8, "#94a3b8")
    sailor(ctx, 280, lerp(900, 1900, k ** 1.6), 1.0, emo("determined"), t, arms="hug", look=(0, 0.5))
    if t > ju + 1.0:
        sp = seg(t, ju + 1.0, ju + 1.8)
        for j in range(14):
            a_ = j / 14 * math.pi
            ctx.arc(280 + math.cos(a_) * 200 * sp, 1720 - math.sin(a_) * 260 * sp + 200 * sp * sp, 14, 0, TAU)
            fill(ctx, "#bfdbfe", 1 - sp)
    ctx.restore()
    rr(ctx, 600, 640, 380, 300, 26)
    fill(ctx, "#0b0b12", 0.85)
    line(ctx, 790, 680, 790, 860, 12, "#facc15")
    line(ctx, 790, 880, 750, 830, 12, "#facc15")
    line(ctx, 790, 880, 830, 830, 12, "#facc15")
    text(ctx, "НОГАМИ ВНИЗ", 790, 905, 34, "#ffffff")
    step_card(ctx, t, EV["steps"][4], 5, "В ВОДУ —\nНОГАМИ ВНИЗ")


def ic_vest(c, x, y, col, a):
    rr(c, x - 20, y - 24, 40, 50, 8)
    fill(c, col, a)
    line(c, x, y - 24, x, y + 26, 3, "#0b0b12", a)


def ic_boat(c, x, y, col, a):
    c.move_to(x - 30, y - 6)
    c.line_to(x + 30, y - 6)
    c.line_to(x + 20, y + 16)
    c.line_to(x - 20, y + 16)
    c.close_path()
    fill(c, col, a)


def ic_bottle(c, x, y, col, a):
    rr(c, x - 12, y - 18, 24, 44, 8)
    fill(c, col, a)
    rr(c, x - 7, y - 28, 14, 12, 3)
    fill(c, col, a)


def ic_coat(c, x, y, col, a):
    c.move_to(x - 26, y - 20)
    c.line_to(x + 26, y - 20)
    c.line_to(x + 30, y + 26)
    c.line_to(x - 30, y + 26)
    c.close_path()
    fill(c, col, a)


def ic_calm(c, x, y, col, a):
    c.arc(x, y, 24, 0, TAU)
    c.set_line_width(5)
    src(c, col, a)
    c.stroke()
    c.arc(x, y + 2, 12, 0.3, math.pi - 0.3)
    c.stroke()


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА ЭВАКУАЦИИ", [
        ("ЖИЛЕТ", "надет в каюте", 1.0, VEST, "1/1", ic_vest),
        ("ШЛЮПКА", "своя, по номеру", 1.0, "#38bdf8", "№12", ic_boat),
        ("ВОДА", "две бутылки", 0.5, "#7dd3fc", "2", ic_bottle),
        ("ТЁПЛАЯ ОДЕЖДА", "куртка и шапка", 1.0, "#a78bfa", "1/1", ic_coat),
        ("ПАНИКА", "ни разу", 0.0, "#ef4444", "0", ic_calm)], EV["tally"])


def s8_done(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1200, 0.9, shake=0.2)
    night_sea(ctx, t, 1150, moon=True)
    liner(ctx, 900, 1150, 0.35, t, tilt=0.25, lights=0.4, sink=60, smoke=False)
    lifeboat(ctx, 540, 1650, 1.1, t, people=4, seed=7)
    sailor(ctx, 380, 1700, 0.75, emo("calm"), t, arms="relax", legs=False)
    ctx.restore()


def s9_dawn(ctx, t, u, D):
    li = EV["lights"]
    dn = seg(t, TL.shots[9][0], EV["dawn"] + 1.5)
    ctx.save()
    cam(ctx, t, 540, 1200, 0.9, shake=0.15)
    night_sea(ctx, t, 1150, dawn=dn, moon=True)
    if t > li - 0.3:
        a = seg(t, li - 0.3, li + 0.5)
        for k in range(5):
            ctx.arc(700 + k * 40, 1120, 8, 0, TAU)
            fill(ctx, "#fde68a", a)
            glow(ctx, 700 + k * 40, 1120, 60, "#fde68a", 0.6 * a)
        liner(ctx, 780, 1150, 0.12 + 0.05 * seg(t, li, TL.shots[10][0]), t, lights=1.0, smoke=False)
    lifeboat(ctx, 400, 1650, 1.1, t, people=4, seed=7)
    ctx.restore()


def s10_board(ctx, t, u, D):
    ca, cn = EV["carpet"], EV["cabno"]
    ctx.save()
    cam(ctx, t, lerp(300, 900, seg(u, 0, D)), 1350, lerp(0.85, 1.0, seg(t, cn - 0.3, cn + 0.5)), shake=0.2)
    ship_corridor(ctx, t, nums=range(706, 720, 2))
    crowd_vests(ctx, t, 9, 3, 2000, -200, 400, walking=False, blanket=True)
    sailor(ctx, 760, 2050, 1.0, emo("worry"), t, arms="relax", look=(0.5, -0.4), back=False)
    ctx.restore()
    if t > ca:
        a = seg(t, ca, ca + 0.3)
        text(ctx, "ТА ЖЕ ДОРОЖКА", 540, 720, 60, "#facc15", "#000", 8, alpha=a)
    if t > cn:
        a = seg(t, cn, cn + 0.3)
        rr(ctx, 340, 800, 400, 140, 20)
        fill(ctx, "#d4a849", a)
        text(ctx, "712", 540, 870, 100, "#451a03", alpha=a)


def s11_same(ctx, t, u, D):
    wh = EV["whole"]
    ctx.save()
    cam(ctx, t, 540, 1100, lerp(0.8, 0.95, seg(u, 0, D)), shake=0.15)
    night_sea(ctx, t, 1400, dawn=1.0, moon=False)
    liner(ctx, 540, 1400, 0.6, t, lights=1.0)
    ctx.restore()
    if t > wh:
        a = seg(t, wh, wh + 0.3)
        text(ctx, "БЕЗ ЕДИНОЙ ЦАРАПИНЫ", 540, 1300, 64, "#22c55e", "#000", 10, alpha=a)
    if t > EV["same"]:
        text(ctx, SHIP_NAME, 540, 700, 70, "#ffffff", "#1e3a8a", 10, alpha=seg(t, EV["same"], EV["same"] + 0.3))


def captain(ctx, x, y, sc, t, talk=0.0):
    p = Npc(random.Random(91), x, y, sc, -1)
    p.shirt, p.pants, p.style, p.item, p.beard, p.hair = "#f8fafc", "#f8fafc", "short", "none", True, "#9a9a9a"
    p.collar = "shirt"
    npc(ctx, p, t, walking=False, grin=0.4)
    hy = y - 470 * sc
    ell(ctx, x, hy - 70 * sc, 95 * sc, 26 * sc)  # фуражка
    fill(ctx, "#111827")
    rr(ctx, x - 80 * sc, hy - 140 * sc, 160 * sc, 74 * sc, 24 * sc)
    fill(ctx, "#f8fafc")
    rr(ctx, x - 80 * sc, hy - 86 * sc, 160 * sc, 18 * sc, 4 * sc)
    fill(ctx, "#111827")
    ctx.arc(x, hy - 108 * sc, 14 * sc, 0, TAU)
    fill(ctx, "#d4a849")
    for sd in (-1, 1):  # погоны
        rr(ctx, x + sd * 70 * sc - 26 * sc, y - 360 * sc, 52 * sc, 16 * sc, 4 * sc)
        fill(ctx, "#d4a849")


def s12_captain(ctx, t, u, D):
    ca, fv = EV["captain"], EV["five"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        ctx.save()
        cam(ctx, t, 540, 1250, lerp(0.9, 1.1, seg(u, 0, ec)), shake=0.2)
        cabin_room(ctx, t, 0.0, slide=0.0)
        rr(ctx, 380, 260, 320, 120, 20)  # динамик
        fill(ctx, "#111827")
        for k in range(5):
            line(ctx, 410, 290 + k * 16, 670, 290 + k * 16, 5, "#374151")
        sailor(ctx, 300, 1950, 1.0, emo("fear"), t, arms="shock", vest=True, tremble=0.6, look=(-0.2, -0.6))
        ctx.restore()
        if t > ca - 0.2:  # капитан в окне-врезке
            a = seg(t, ca - 0.2, ca + 0.2)
            ctx.save()
            ctx.push_group()
            rr(ctx, 560, 900, 440, 560, 30)
            fill(ctx, "#1e3a8a")
            ctx.save()
            rr(ctx, 560, 900, 440, 560, 30)
            ctx.clip()
            captain(ctx, 780, 1700, 1.2, t)
            ctx.restore()
            rr(ctx, 560, 900, 440, 560, 30)
            ctx.set_line_width(8)
            src(ctx, "#d4a849")
            ctx.stroke()
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)
            ctx.restore()
        if t > fv:
            a = seg(t, fv, fv + 0.3)
            rr(ctx, 140, 640, 800, 130, 30)
            fill(ctx, "#0b0b12", 0.9 * a)
            text(ctx, "ОТПРАВЛЕНИЕ: 05:00", 540, 705, 60, "#facc15", alpha=a)
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
        text(ctx, "Сколько раз ты уже тонул?", 0, 180, 60, "#93c5fd")
    ctx.restore()


SCENES = [s0_hook, s1_siren, s2_vest, s3_stairs, s4_boat, s5_warm, s6_jump, s7_tally, s8_done, s9_dawn,
          s10_board, s11_same, s12_captain]
LABELS = {9: "РАССВЕТ", 10: "РАССВЕТ", 11: "РАССВЕТ", 12: "РАССВЕТ"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("номер", "двенадцать"), "№12"), (("две", "бутылки"), "2 бутылки"), (("ноль",), "0"),
         (("пять", "минут"), "5 минут"), (("семь", "коротких"), "7 коротких")]


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
        text(ctx, "ЛАЙНЕР ТОНЕТ", 0, 10, 112, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -300, 90, 600, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "НОЧЬЮ?", 0, 155, 100, "#ffffff")
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
