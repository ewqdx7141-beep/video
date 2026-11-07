"""Серия 28 «Один город» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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










# ================================================================== ОДИН ГОРОД
INDIGO = ("#4f46e5", "#3730a3")


def citizen(ctx, x, y, sc, e, t, arms="relax", look=(0, 0), walk=None, back=False, legs=True, tremble=0.0, item=None,
            phones=False):
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, walk=walk, back=back, legs=legs, tremble=tremble,
         rim="#c7d2fe", rim_a=0.6, hood=INDIGO, hand_item=item)
    if phones:
        hy = y - (455 if legs else 285) * sc
        ctx.arc(x, hy - 10 * sc, 125 * sc, math.pi * 1.05, math.pi * 1.95)
        ctx.set_line_width(16 * sc)
        src(ctx, "#111827")
        ctx.stroke()
        for sd in (-1, 1):
            rr(ctx, x + sd * 120 * sc - 26 * sc, hy - 40 * sc, 52 * sc, 90 * sc, 22 * sc)
            fill(ctx, "#334155")


def tv_tower(ctx, x, y, h, t):
    ctx.move_to(x - 60, y)
    ctx.line_to(x + 60, y)
    ctx.line_to(x + 14, y - h * 0.7)
    ctx.line_to(x - 14, y - h * 0.7)
    ctx.close_path()
    fill(ctx, "#cbd5e1")
    for k in range(6):
        line(ctx, x - 50 + k * 8, y - k * h * 0.11, x + 50 - k * 8, y - k * h * 0.11, 4, "#94a3b8")
    ell(ctx, x, y - h * 0.7, 60, 34)
    fill(ctx, "#e2e8f0")
    rr(ctx, x - 50, y - h * 0.7 - 8, 100, 14, 4)
    fill(ctx, "#38bdf8")
    line(ctx, x, y - h * 0.7, x, y - h, 8, "#cbd5e1")
    on = (t * 1.5) % 1 < 0.5
    for k in range(3):
        ctx.arc(x, y - h * (0.78 + k * 0.08), 8, 0, TAU)
        fill(ctx, "#ef4444" if on else "#7f1d1d")


def fog(ctx, t, x0, x1, y0, y1, a=0.9, seed=1):
    r = random.Random(seed)
    for k in range(40):
        x = r.uniform(x0, x1) + math.sin(t * 0.3 + k) * 40
        y = r.uniform(y0, y1)
        ell(ctx, x, y, r.uniform(160, 340), r.uniform(60, 140))
        fill(ctx, "#f1f5f9", a * r.uniform(0.25, 0.5))


def city_pano(ctx, t, night=0.0, fog_a=1.0, wall=0.0, lit=0.7, fog_x=0.0):
    vgrad(ctx, -1500, -1200, 4000, 2600, [(0, mixh("#7dd3fc", "#0b1022", night)), (1, mixh("#e0f2fe", "#312e81", night))])
    if wall > 0:  # белая стена до неба
        ctx.rectangle(-1500, -1200, 4000, 2400)
        fill(ctx, "#f8fafc", wall)
    skyline(ctx, 51, -1400, 2600, 1150, 300, 650, mixh("#94a3b8", "#1e293b", night), "#fde68a",
            lit * (0.3 + 0.7 * night), wmin=120, wmax=220)
    tv_tower(ctx, 760, 1150, 900, t)
    skyline(ctx, 52, -1400, 2600, 1250, 150, 420, mixh("#64748b", "#111827", night), "#fde68a",
            lit * (0.3 + 0.7 * night), wmin=150, wmax=260)
    ctx.rectangle(-1500, 1250, 4000, 200)  # река
    fill(ctx, mixh("#38bdf8", "#1e3a8a", night))
    for k in range(6):
        line(ctx, -1400 + k * 500 + (t * 40) % 500, 1300 + k % 3 * 30, -1300 + k * 500 + (t * 40) % 500,
             1300 + k % 3 * 30, 4, "#e0f2fe", 0.5)
    rr(ctx, -200, 1230, 1500, 30, 6)  # мост
    fill(ctx, "#475569")
    for k in range(8):
        line(ctx, -150 + k * 200, 1230, -150 + k * 200, 1300, 10, "#475569")
    ctx.rectangle(-1500, 1450, 4000, 1500)
    fill(ctx, mixh("#a8a29e", "#1f2937", night))
    if fog_a > 0:  # туман по краям
        fog(ctx, t, -1500 - fog_x, -300 - fog_x, 400, 1500, fog_a, 1)
        fog(ctx, t, 1400 + fog_x, 2600 + fog_x, 400, 1500, fog_a, 2)
        fog(ctx, t, -1500, 2600, 500 - fog_x * 0.3, 900 - fog_x * 0.3, fog_a * 0.6, 3)


def mixh(c1, c2, k):
    a, b = hexc(c1), hexc(c2)
    return "#%02x%02x%02x" % tuple(int(255 * (a[i] + (b[i] - a[i]) * clamp(k))) for i in range(3))


def flight_board(ctx, x, y, t, k=1.0):
    rr(ctx, x, y, 900, 640, 16)
    fill(ctx, "#0b0b12")
    text(ctx, "ВЫЛЕТ", x + 40, y + 50, 40, "#facc15", align="left")
    text(ctx, f"{int(9 + t // 60) % 24:02d}:{int(t) % 60:02d}", x + 860, y + 50, 40, "#facc15", align="right")
    rows = (("08:10", "СОЧИ"), ("08:35", "КАЗАНЬ"), ("09:00", "СТАМБУЛ"), ("09:20", "ДУБАЙ"), ("09:45", "МИНСК"),
            ("10:05", "БАКУ"), ("10:30", "ПЕКИН"))
    for i, (tm, city) in enumerate(rows):
        yy = y + 120 + i * 72
        text(ctx, tm, x + 40, yy, 36, "#e5e7eb", align="left")
        text(ctx, city, x + 200, yy, 36, "#e5e7eb", align="left")
        on = k * 7 > i
        flick_ = (int(t * 10) + i) % 4 == 0 and not on
        text(ctx, "ОТМЕНЁН" if on else ("ПО РАСПИСАНИЮ" if not flick_ else "████"), x + 860, yy, 32,
             "#ef4444" if on else "#22c55e", align="right")


def ring_train(ctx, x, y, s, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for k in range(4):
        cx = k * 330
        rr(ctx, cx, -170, 320, 170, 24)
        fill(ctx, "#dc2626" if k == 0 else "#f1f5f9")
        rr(ctx, cx, -60, 320, 20, 4)
        fill(ctx, "#1e3a8a")
        for j in range(4):
            rr(ctx, cx + 20 + j * 74, -140, 56, 56, 8)
            fill(ctx, "#bae6fd")
        for j in (60, 260):
            ctx.arc(cx + j, 0, 26, 0, TAU)
            fill(ctx, "#111827")
    ctx.restore()


def greenhouse(ctx, x, y, w, h, t):
    rr(ctx, x, y - h, w, h, 10)
    fill(ctx, "#bbf7d0", 0.55)
    ctx.move_to(x, y - h)
    ctx.line_to(x + w / 2, y - h - 90)
    ctx.line_to(x + w, y - h)
    fill(ctx, "#bbf7d0", 0.55)
    for k in range(int(w / 70) + 1):
        line(ctx, x + k * 70, y - h, x + k * 70, y, 4, "#e5e7eb")
    for k in range(int(w / 60)):  # грядки
        for j in range(3):
            ctx.arc(x + 30 + k * 60, y - 40 - j * 60, 22, 0, TAU)
            fill(ctx, ("#22c55e", "#16a34a", "#ef4444")[(k + j) % 3])
    line(ctx, x, y, x + w, y, 8, "#78350f")


def pallets(ctx, x, y, n=4, seed=1):
    r = random.Random(seed)
    for k in range(n):
        px = x + k * 240
        rr(ctx, px, y - 20, 220, 20, 3)
        fill(ctx, "#a16207")
        for j in range(3):
            for i in range(2):
                rr(ctx, px + 10 + i * 104, y - 20 - (j + 1) * 80, 96, 76, 6)
                fill(ctx, r.choice(("#d6a77a", "#c2410c", "#facc15", "#94a3b8")))
                text(ctx, r.choice(("КРУПА", "КОНСЕРВЫ", "МУКА", "ВОДА", "САХАР")), px + 58 + i * 104,
                     y - 20 - (j + 1) * 80 + 38, 16, "#451a03")


def power_plant(ctx, x, y, t):
    for k in range(2):
        cx = x + k * 260
        ctx.move_to(cx - 90, y)
        ctx.curve_to(cx - 50, y - 300, cx - 50, y - 400, cx - 70, y - 520)
        ctx.line_to(cx + 70, y - 520)
        ctx.curve_to(cx + 50, y - 400, cx + 50, y - 300, cx + 90, y)
        ctx.close_path()
        fill(ctx, "#cbd5e1")
        rr(ctx, cx - 72, y - 400, 144, 26, 4)
        fill(ctx, "#ef4444")
        puff(ctx, cx, y - 540, t, 40 + k, n=6, col="#f8fafc", life=2.4, rate=0.4, dx=-80, dy=-220, a=0.6)
    rr(ctx, x - 200, y - 220, 260, 220, 8)
    fill(ctx, "#94a3b8")
    for k in range(3):
        line(ctx, x + 400 + k * 120, y, x + 380 + k * 120, y - 460, 10, "#64748b")
        line(ctx, x + 330 + k * 120, y - 400, x + 450 + k * 120, y - 400, 6, "#64748b")


def solar_roof(ctx, x, y, w, t):
    rr(ctx, x, y, w, 400, 4)
    fill(ctx, "#475569")
    for k in range(int(w / 110)):
        ctx.save()
        ctx.translate(x + 20 + k * 110, y - 10)
        ctx.transform(cairo.Matrix(1, 0, -0.3, 1, 0, 0))
        rr(ctx, 0, -70, 96, 70, 4)
        fill(ctx, "#1e3a8a")
        for j in range(3):
            line(ctx, 0, -70 + j * 23, 96, -70 + j * 23, 2, "#93c5fd")
        line(ctx, 48, -70, 48, 0, 2, "#93c5fd")
        ctx.restore()
        glow(ctx, x + 60 + k * 110, y - 40, 50, "#fef9c3", 0.2 + 0.1 * math.sin(t * 2 + k))


# ================================================================== СЦЕНЫ
def globe_screen(t, k=0.0):
    def f(c, x, y, w, h):
        vgrad(c, x, y, w, h, [(0, "#0b1022"), (1, "#111827")])
        text(c, "КАРТА МИРА", x + w / 2, y + 90, 40, "#93c5fd")
        cx, cy, R = x + w / 2, y + h * 0.45, w * 0.38
        c.arc(cx, cy, R, 0, TAU)
        fill(c, "#1e3a8a")
        r = random.Random(3)
        for i in range(9):  # материки исчезают
            ell(c, cx + r.uniform(-R * 0.6, R * 0.6), cy + r.uniform(-R * 0.6, R * 0.6), r.uniform(40, 90),
                r.uniform(30, 70))
            fill(c, "#22c55e", max(0.0, 1 - k * 1.3))
        c.arc(cx + 30, cy - 20, 14, 0, TAU)
        fill(c, "#ef4444")
        glow(c, cx + 30, cy - 20, 60 + 20 * math.sin(t * 6), "#ef4444", 0.7)
        text(c, "ГОРОДОВ НАЙДЕНО: 1", x + w / 2, y + h - 140, 34, "#fca5a5" if k > 0.5 else "#e5e7eb")
    return f


def s0_hook(ctx, t, u, D):
    on = EV["one"]
    ctx.save()
    cam(ctx, t, 540, 1250, lerp(0.8, 0.9, seg(u, 0, D)), shake=0.15)
    city_pano(ctx, t, fog_a=seg(t, on, on + 1.5))
    street_people(ctx, t, 6, 7, 1800, mood="stare")
    citizen(ctx, 540, 2150, 1.0, emo("shock") if t > on else emo("calm"), t, arms="phone")
    ctx.restore()
    if t > 0.6:
        s = ease(seg(t, 0.6, 1.2))
        ctx.save()
        ctx.translate(780, lerp(2400, 1250, s))
        ctx.scale(0.7, 0.7)
        phone_body(ctx, 0, 0, 420, 820, globe_screen(t, seg(t, on - 0.5, on + 1.0)))
        ctx.restore()


def s1_closed(ctx, t, u, D):
    pl, tr, fg = EV["planes"], EV["trains"], EV["fog"]
    ctx.save()
    if t < tr:
        cam(ctx, t, 540, 1000, 1.0, shake=0.15)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#e2e8f0"), (1, "#cbd5e1")])
        for k in range(4):  # окна аэропорта с самолётом на земле
            rr(ctx, -100 + k * 340, 1300, 320, 500, 8)
            fill(ctx, "#bae6fd")
        ell(ctx, 540, 1650, 400, 50)
        fill(ctx, "#f8fafc")
        flight_board(ctx, 90, 400, t, seg(t, pl - 0.3, pl + 1.0))
        street_people(ctx, t, 8, 5, 2050, mood="stare")
    elif t < fg - 0.2:
        cam(ctx, t, 540, 1200, 0.9, shake=0.15)
        city_pano(ctx, t, fog_a=0.9)
        line(ctx, -1500, 1700, 2600, 1700, 14, "#57534e")
        for k in range(-12, 26):
            line(ctx, k * 120, 1690, k * 120, 1720, 8, "#78350f")
        ring_train(ctx, lerp(1300, -600, seg(t, tr, fg)), 1690, 1.0, t)
        text(ctx, "ОБРАТНО", 540, 800, 70, "#ef4444", "#000", 10)
    else:
        cam(ctx, t, 540, 1200, 0.9, shake=0.15)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#cbd5e1"), (1, "#94a3b8")])
        ctx.move_to(380, 1100)  # дорога уходит в туман
        ctx.line_to(700, 1100)
        ctx.line_to(1500, 2600)
        ctx.line_to(-420, 2600)
        ctx.close_path()
        fill(ctx, "#374151")
        for k in range(8):
            rr(ctx, 530, 1150 + k * 170, 20, 80 + k * 10, 4)
            fill(ctx, "#f8fafc")
        for k in range(5):  # столбы растворяются
            a = 1 - k / 5
            line(ctx, 200 - k * 30, 2100 - k * 220, 200 - k * 30, 1700 - k * 260, 14 - k * 2, "#1f2937", a)
            line(ctx, 880 + k * 30, 2100 - k * 220, 880 + k * 30, 1700 - k * 260, 14 - k * 2, "#1f2937", a)
        line(ctx, 830, 1500, 830, 1700, 10, "#475569")
        rr(ctx, 700, 1360, 260, 140, 10)
        fill(ctx, "#1d4ed8")
        text(ctx, "ГРАНИЦА", 830, 1410, 32, "#ffffff")
        text(ctx, "ГОРОДА", 830, 1455, 32, "#ffffff")
        fog(ctx, t, -800, 1900, 600, 1500, 1.0, 9)
    ctx.restore()


def s2_fog(ctx, t, u, D):
    go = EV["gone"]
    ctx.save()
    cam(ctx, t, 540, 1250, 0.9, shake=0.15)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#e2e8f0"), (1, "#94a3b8")])
    ctx.rectangle(-800, 1500, 2700, 1400)
    fill(ctx, "#57534e")
    for k in range(6):  # ограждение-ленты
        line(ctx, -800, 1600 + k * 4, 1900, 1600 + k * 4, 6, "#ef4444" if k % 2 else "#f8fafc")
    for x in (-200, 300, 800, 1300):
        line(ctx, x, 1520, x, 1700, 12, "#ca8a04")
    rr(ctx, 300, 1150, 480, 160, 12)
    fill(ctx, "#facc15")
    text(ctx, "НЕ ВХОДИТЬ", 540, 1210, 52, "#111827")
    text(ctx, "ТУМАН", 540, 1270, 40, "#111827")
    if t > go:  # следы уходят и обрываются
        for k in range(8):
            ell(ctx, 520 + (k % 2) * 40, 1500 - k * 70, 16, 26)
            fill(ctx, "#292524", 0.7 * (1 - k / 8))
    fog(ctx, t, -800, 1900, 300, 1500, 1.0, 4)
    citizen(ctx, 540, 2200, 1.0, emo("worry"), t, arms="relax", back=True)
    ctx.restore()
    step_card(ctx, t, EV["steps"][0], 1, "НЕ ИДИ\nВ ТУМАН")


def s3_supplies(ctx, t, u, D):
    sp = EV["supplies"]
    ctx.save()
    cx = 540 if t < sp[1] else (1900 if t < sp[2] else 3300)
    cam(ctx, t, lerp(540, cx, ease(seg(t, sp[0], sp[2] + 0.4))), 1250, 0.85, shake=0.15)
    vgrad(ctx, -800, -800, 5200, 3600, [(0, "#7dd3fc"), (1, "#e0f2fe")])
    # крыша с теплицами
    rr(ctx, -200, 1500, 1500, 800, 0)
    fill(ctx, "#64748b")
    greenhouse(ctx, 0, 1500, 500, 300, t)
    greenhouse(ctx, 600, 1500, 500, 300, t)
    ac_unit(ctx, 1200, 1500, 1.0, t)
    citizen(ctx, 540, 2000, 1.0, emo("happy"), t, arms="relax",
            item=lambda c, x, y: (c.arc(x, y, 30, 0, TAU), fill(c, "#ef4444")))
    # склад
    rr(ctx, 1300, 700, 1300, 1600, 0)
    fill(ctx, "#cbd5e1")
    for k in range(6):
        line(ctx, 1300, 700 + k * 260, 2600, 700 + k * 260, 6, "#94a3b8")
    pallets(ctx, 1380, 1900, 5, 2)
    text(ctx, "СКЛАД №3", 1950, 800, 70, "#1e3a8a")
    # ферма
    rr(ctx, 2600, 1500, 1500, 800, 0)
    fill(ctx, "#65a30d")
    for k in range(10):
        line(ctx, 2600, 1560 + k * 50, 4100, 1560 + k * 50, 6, "#3f6212")
    rr(ctx, 3000, 1100, 500, 400, 8)
    fill(ctx, "#b91c1c")
    ctx.move_to(2960, 1110)
    ctx.line_to(3250, 900)
    ctx.line_to(3540, 1110)
    fill(ctx, "#7f1d1d")
    for k in range(3):  # коровы
        ell(ctx, 2800 + k * 400, 1850, 110, 60)
        fill(ctx, "#f8fafc")
        ctx.arc(2880 + k * 400, 1820, 36, 0, TAU)
        fill(ctx, "#f8fafc")
        ell(ctx, 2780 + k * 400, 1840, 30, 20)
        fill(ctx, "#111827")
        for j in range(4):
            line(ctx, 2720 + k * 400 + j * 50, 1890, 2720 + k * 400 + j * 50, 1960, 10, "#f8fafc")
    ctx.restore()
    step_card(ctx, t, EV["steps"][1], 2, "ЗАПАСЫ\nГОРОД КОРМИТ СЕБЯ")


def s4_council(ctx, t, u, D):
    co = EV["council"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.85, shake=0.15)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#fef3c7"), (1, "#fde68a")])
    for k in range(-2, 6):
        rr(ctx, k * 330, 300, 280, 600, 10)
        fill(ctx, "#bae6fd")
        curtain(ctx, k * 330 - 20, 280, 60, 640, "#991b1b", t, 1)
    rr(ctx, 380, 700, 320, 440, 10)  # флипчарт
    fill(ctx, "#ffffff")
    line(ctx, 420, 1140, 380, 1400, 8, "#57534e")
    line(ctx, 660, 1140, 700, 1400, 8, "#57534e")
    for i, (nm, col) in enumerate((("ВРАЧИ", "#ef4444"), ("ИНЖЕНЕРЫ", "#2563eb"), ("УЧИТЕЛЯ", "#16a34a"))):
        a = seg(t, co[i] - 0.2, co[i] + 0.2)
        text(ctx, nm, 540, 790 + i * 110, 46, col, alpha=a)
        if a > 0.9:
            checkmark(ctx, 660, 790 + i * 110, 0.5, col)
    r = random.Random(12)
    for row in range(2):  # сидящая массовка с табличками ролей
        for i in range(6):
            p = Npc(r, -250 + i * 300 + row * 150, 1700 + row * 260, 0.95, 1 if i % 2 else -1)
            p.item = "none"
            npc(ctx, p, t, walking=False, back=True)
            rol = ("ВРАЧ", "ИНЖ.", "УЧИТ.")[(i + row) % 3]
            rr(ctx, p.x - 60, p.y - 230, 120, 44, 8)
            fill(ctx, ("#ef4444", "#2563eb", "#16a34a")[(i + row) % 3])
            text(ctx, rol, p.x, p.y - 208, 24, "#ffffff")
    rr(ctx, -600, 1950, 2400, 60, 8)
    fill(ctx, "#78350f")
    ctx.restore()
    step_card(ctx, t, EV["steps"][2], 3, "СОВЕТ\nКАЖДЫЙ НА СВОЁМ МЕСТЕ")


def s5_energy(ctx, t, u, D):
    en = EV["energy"]
    ev = seg(t, en[2] - 0.3, en[2] + 0.6)
    ctx.save()
    cam(ctx, t, 540, 1250, 0.85, shake=0.15)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, mixh("#7dd3fc", "#1e1b4b", ev)), (1, mixh("#e0f2fe", "#7c2d12", ev))])
    skyline(ctx, 61, -1400, 2600, 1300, 200, 500, mixh("#94a3b8", "#1e293b", ev), "#fde68a", 0.2 + 0.5 * ev,
            wmin=140, wmax=240)
    power_plant(ctx, 100, 1300, t)
    solar_roof(ctx, 650, 1500, 700, t)
    ctx.rectangle(-1200, 1800, 3600, 1000)
    fill(ctx, "#475569")
    for k in range(8):  # окна гаснут — экономия
        rr(ctx, -300 + k * 220, 1880, 120, 140, 6)
        fill(ctx, "#fde68a" if (k % 3 or ev < 0.5) else "#1f2937")
    ctx.restore()
    rr(ctx, 290, 650, 500, 150, 30)
    fill(ctx, "#0b0b12", 0.85)
    text(ctx, "СЕТЬ ГОРОДА", 540, 690, 32, "#facc15")
    pw = int(lerp(70, 90, seg(t, en[0], en[2] + 1)))
    text(ctx, f"{pw}%", 540, 760, 70, "#22c55e")
    step_card(ctx, t, EV["steps"][3], 4, "ЭНЕРГИЯ\nТЭЦ И ПАНЕЛИ")


def s6_radio(ctx, t, u, D):
    ro = EV["radio_on"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.9, shake=0.15)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#1e293b"), (1, "#0f172a")])
    for k in range(3):  # стойки с аппаратурой
        rr(ctx, -100 + k * 420, 500, 380, 900, 10)
        fill(ctx, "#334155")
        for j in range(5):
            rr(ctx, -80 + k * 420, 530 + j * 170, 340, 140, 6)
            fill(ctx, "#1f2937")
            for i in range(4):
                ctx.arc(-40 + k * 420 + i * 70, 600 + j * 170, 12, 0, TAU)
                fill(ctx, ("#22c55e", "#ef4444", "#facc15", "#3b82f6")[(i + j + k) % 4],
                     0.4 + 0.6 * ((int(t * 3) + i + j) % 3 == 0))
    rr(ctx, -300, 1500, 1700, 60, 8)  # стол
    fill(ctx, "#78350f")
    rr(ctx, 300, 1300, 480, 200, 14)  # приёмник
    fill(ctx, "#111827")
    fr = 88.0 + ((t - ro) * 7.3) % 20 if t > ro else 88.0
    text(ctx, f"{fr:.1f} МГц", 540, 1360, 50, "#22c55e")
    for k in range(30):
        h = abs(nz(t * 6 + k * 0.4, 7)) * 40
        line(ctx, 330 + k * 14, 1460 - h, 330 + k * 14, 1460, 6, "#22c55e", 0.7)
    citizen(ctx, 540, 2000, 1.1, emo("determined"), t, arms="relax", back=True, legs=False, phones=True)
    ctx.restore()
    rr(ctx, 260, 640, 560, 110, 30)
    fill(ctx, "#0b0b12", 0.85)
    text(ctx, "ВСЕ ЧАСТОТЫ: ТИШИНА", 540, 695, 40, "#94a3b8")
    step_card(ctx, t, EV["steps"][4], 5, "СВЯЗЬ\nРАДИО НА ВСЕХ ЧАСТОТАХ")


def ic_food(c, x, y, col, a):
    c.arc(x, y + 4, 22, 0, math.pi)
    fill(c, col, a)
    line(c, x - 24, y + 4, x + 24, y + 4, 5, col, a)


def ic_bolt2(c, x, y, col, a):
    c.move_to(x + 6, y - 28)
    c.line_to(x - 14, y + 4)
    c.line_to(x, y + 4)
    c.line_to(x - 6, y + 28)
    c.line_to(x + 14, y - 4)
    c.line_to(x, y - 4)
    c.close_path()
    fill(c, col, a)


def ic_cross(c, x, y, col, a):
    rr(c, x - 8, y - 24, 16, 48, 3)
    fill(c, col, a)
    rr(c, x - 24, y - 8, 48, 16, 3)
    fill(c, col, a)


def ic_antenna(c, x, y, col, a):
    line(c, x, y + 24, x, y - 10, 5, col, a)
    for k in range(2):
        c.arc(x, y - 10, 12 + k * 10, -2.4, -0.7)
        c.set_line_width(4)
        src(c, col, a)
        c.stroke()


def ic_cloud(c, x, y, col, a):
    for dx in (-14, 0, 14):
        c.arc(x + dx, y - abs(dx) * 0.3, 14, 0, TAU)
        fill(c, col, a)


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА ГОРОДА", [
        ("ЕДА", "месяцев из 12", 8 / 12, "#22c55e", "8/12", ic_food),
        ("ЭНЕРГИЯ", "ТЭЦ + панели", 0.9, "#facc15", "90%", ic_bolt2),
        ("ВРАЧИ", "на своих местах", 1.0, "#ef4444", "140", ic_cross),
        ("СИГНАЛЫ ИЗВНЕ", "все частоты", 0.0, "#60a5fa", "0", ic_antenna),
        ("УШЕДШИЕ В ТУМАН", "никто", 0.0, "#e5e7eb", "0", ic_cloud)], EV["tally"])


def s8_done(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1250, 0.85, shake=0.1)
    city_pano(ctx, t, night=0.8, fog_a=0.6, lit=1.0)
    rr(ctx, -400, 1800, 1900, 900, 0)  # крыша
    fill(ctx, "#334155")
    greenhouse(ctx, -200, 1800, 400, 220, t)
    citizen(ctx, 600, 2150, 1.0, emo("happy"), t, arms="relax", look=(0, -0.4))
    ctx.restore()


def s9_retreat(ctx, t, u, D):
    rt = EV["retreat"]
    ctx.save()
    cam(ctx, t, 540, 1200, lerp(0.85, 0.75, seg(t, rt, rt + 2)), shake=0.15)
    k = ease(seg(t, rt - 0.3, rt + 2.5))
    city_pano(ctx, t, fog_a=1.0, wall=0.0, fog_x=k * 900)
    ctx.restore()
    text(ctx, "ЧЕРЕЗ ГОД", 540, 400, 70, "#ffffff", "#000", 10, alpha=seg(t, TL.shots[9][0] + 0.2, TL.shots[9][0] + 0.5))
    if t > rt:
        text(ctx, "+1 КМ", 540, 760, 90, "#22c55e", "#000", 12, alpha=seg(t, rt, rt + 0.3))


def s10_wall(ctx, t, u, D):
    wl_, sk = EV["wall"], EV["sky"]
    ctx.save()
    k = ease(seg(t, wl_ - 0.4, sk + 0.6))
    cam(ctx, t, 540, lerp(1700, 900, k), lerp(1.0, 0.5, k), shake=0.15)
    vgrad(ctx, -3000, -3000, 7000, 7000, [(0, "#f8fafc"), (1, "#e2e8f0")])
    for k2 in range(-30, 40):  # швы белой стены
        line(ctx, k2 * 200, -3000, k2 * 200, 2000, 3, "#cbd5e1", 0.6)
    for j in range(-15, 10):
        line(ctx, -3000, j * 200, 4000, j * 200, 2, "#e2e8f0")
    ctx.rectangle(-3000, 2000, 7000, 2000)
    fill(ctx, "#57534e")
    fog(ctx, t, -2000, 3000, 1700, 2200, 0.6, 7)
    citizen(ctx, 540, 2100, 0.6, emo("shock"), t, arms="shock", look=(0, -0.9))
    p = Npc(random.Random(4), 300, 2100, 0.55, 1)
    npc(ctx, p, t, walking=False, stare=0.9)
    p = Npc(random.Random(5), 800, 2100, 0.55, -1)
    npc(ctx, p, t, walking=False, stare=0.9)
    ctx.restore()


def mural(ctx, t, lit=1.0):
    """Огромный рисунок города на стене: улицы, дома, горящее окно."""
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#f8fafc"), (1, "#e2e8f0")])
    r = random.Random(8)
    ctx.save()
    for k in range(40):  # кварталы-линии
        x = r.uniform(-400, 1500)
        y = r.uniform(300, 1700)
        rr(ctx, x, y, r.uniform(80, 200), r.uniform(120, 320), 4)
        ctx.set_line_width(4)
        src(ctx, "#475569", 0.7)
        ctx.stroke()
        for j in range(4):
            ctx.rectangle(x + 14 + (j % 2) * 40, y + 20 + (j // 2) * 50, 20, 26)
            ctx.set_line_width(2)
            src(ctx, "#475569", 0.5)
            ctx.stroke()
    ctx.move_to(-400, 1100)  # река на рисунке
    ctx.curve_to(200, 1000, 600, 1300, 1500, 1150)
    ctx.set_line_width(26)
    src(ctx, "#93c5fd", 0.7)
    ctx.stroke()
    line(ctx, 760, 1700, 760, 500, 6, "#475569")  # телебашня на рисунке
    ell(ctx, 760, 760, 40, 22)
    ctx.set_line_width(4)
    src(ctx, "#475569")
    ctx.stroke()
    ctx.restore()
    rr(ctx, 380, 980, 160, 300, 4)  # твой дом
    fill(ctx, "#f1f5f9")
    rr(ctx, 380, 980, 160, 300, 4)
    ctx.set_line_width(6)
    src(ctx, "#1e293b")
    ctx.stroke()
    for j in range(6):
        on = (j == 3)
        ctx.rectangle(400 + (j % 2) * 70, 1000 + (j // 2) * 90, 50, 60)
        if on:
            fill(ctx, "#facc15", lit)
            glow(ctx, 495, 1210, 120, "#facc15", 0.8 * lit)
        else:
            ctx.set_line_width(3)
            src(ctx, "#1e293b")
            ctx.stroke()


def s11_mural(ctx, t, u, D):
    wi = EV["window"]
    ctx.save()
    k = ease(seg(t, wi - 0.6, wi + 0.8))
    cam(ctx, t, lerp(540, 495, k), lerp(1000, 1210, k), lerp(0.75, 2.2, k), shake=0.15)
    mural(ctx, t, lit=0.5 + 0.5 * math.sin(t * 4) ** 2)
    ctx.restore()
    if t > wi:
        text(ctx, "ТВОЁ ОКНО", 540, 600, 80, "#facc15", "#000", 12, alpha=seg(t, wi, wi + 0.3))


def s12_plaque(ctx, t, u, D):
    ex = EV["exhibit"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        ctx.save()
        cam(ctx, t, 540, 1100, lerp(0.85, 1.0, seg(u, 0, ec)), shake=0.15)
        mural(ctx, t, 1.0)
        rr(ctx, 160, 1350, 760, 380, 16)  # музейная табличка
        fill(ctx, "#d4a849")
        rr(ctx, 180, 1370, 720, 340, 10)
        fill(ctx, "#1c1917")
        a = seg(t, ex - 0.3, ex)
        text(ctx, "ЭКСПОНАТ №4", 540, 1440, 64, "#facc15", alpha=a)
        text(ctx, "«САМЫЙ ЖИВУЧИЙ»", 540, 1530, 50, "#f5f5f4", alpha=seg(t, EV["alive"] - 0.3, EV["alive"]))
        text(ctx, "город, 1 шт. • под туманом", 540, 1620, 30, "#a8a29e", alpha=a)
        for sx in (200, 880):
            ctx.arc(sx, 1390, 10, 0, TAU)
            fill(ctx, "#78350f")
        ctx.restore()
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
        text(ctx, "Где экспонаты 1, 2 и 3?", 0, 180, 62, "#c7d2fe")
    ctx.restore()


SCENES = [s0_hook, s1_closed, s2_fog, s3_supplies, s4_council, s5_energy, s6_radio, s7_tally, s8_done, s9_retreat,
          s10_wall, s11_mural, s12_plaque]
LABELS = {9: "ГОД СПУСТЯ", 10: "ГОД СПУСТЯ", 11: "ГОД СПУСТЯ", 12: "ГОД СПУСТЯ"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("восемь", "месяцев", "из", "двенадцати"), "8 из 12"), (("девяносто", "процентов"), "90%"),
         (("сто", "сорок"), "140"), (("ноль",), "0"), (("номер", "четыре"), "№4")]


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
        text(ctx, "НА ЗЕМЛЕ ОСТАЛСЯ", 0, 10, 96, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -330, 90, 660, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "ОДИН ГОРОД?", 0, 155, 96, "#ffffff")
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
