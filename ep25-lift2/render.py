"""Серия 25 «Лифт с незнакомцем» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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










# ================================================================== ЛИФТ С НЕЗНАКОМЦЕМ
STEEL = [(0, "#6b7280"), (0.3, "#d1d5db"), (0.55, "#9ca3af"), (0.8, "#e5e7eb"), (1, "#6b7280")]
NAVY = ("#1e40af", "#1e3a8a")
COAT = "#a8916b"
COAT_D = "#7c6a4c"


def me(ctx, x, y, sc, e, t, arms="relax", look=(0, 0), walk=None, back=False, legs=True, tremble=0.0, item=None,
       knees=False):
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, walk=walk, back=back, legs=legs, tremble=tremble,
         rim="#93c5fd", rim_a=0.55, hood=NAVY, hand_item=item, knees=knees)


def suitcase(ctx, x, y, s, tag=True, swing=0.0, t=0.0):
    """Кожаный чемодан; (x, y) — низ по центру."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 0, 170, 18, 0.4)
    rr(ctx, -160, -260, 320, 260, 22)
    lgrad(ctx, 0, -260, 0, 0, [(0, "#92400e"), (1, "#5c2a0a")])
    ctx.fill()
    for sx in (-110, 110):  # ремни
        rr(ctx, sx - 16, -262, 32, 264, 4)
        fill(ctx, "#451a03")
        rr(ctx, sx - 22, -160, 44, 34, 4)
        fill(ctx, "#d4a849")
    for k in range(4):  # уголки
        cx, cy = (-160 if k % 2 == 0 else 128), (-260 if k < 2 else -32)
        rr(ctx, cx, cy, 32, 32, 8)
        fill(ctx, "#d4a849")
    line(ctx, -150, -140, 150, -140, 3, "#451a03", 0.6)
    for k in range(6):  # потёртости
        ell(ctx, -100 + k * 40, -60 - (k % 3) * 50, 20, 8)
        fill(ctx, "#b45309", 0.35)
    ctx.arc(0, -262, 50, math.pi, TAU)  # ручка
    ctx.set_line_width(16)
    src(ctx, "#451a03")
    ctx.stroke()
    if tag:
        ctx.save()
        ctx.translate(40, -262)
        ctx.rotate(0.5 + math.sin(t * 2) * 0.08 + swing)
        line(ctx, 0, 0, 0, 70, 3, "#78350f")
        rr(ctx, -40, 70, 80, 110, 8)
        fill(ctx, "#fef3c7")
        ctx.arc(0, 86, 7, 0, TAU)
        fill(ctx, "#78350f")
        for k in range(3):
            line(ctx, -26, 110 + k * 20, 26 - k * 8, 110 + k * 20, 3, "#a8a29e")
        ctx.restore()
    ctx.restore()


def stranger(ctx, x, y, sc, t, sit=False, talk=0.0, alpha=1.0, look=0.0):
    """Мужчина в плаще и шляпе; лицо в тени полей шляпы. (x, y) — между ступнями."""
    ctx.push_group()
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    shadow(ctx, 0, 0, 130, 18, 0.4)
    hy = -560 if not sit else -380
    if not sit:
        for sd in (-1, 1):
            rr(ctx, sd * 50 - 22, -220, 44, 220, 12)
            fill(ctx, "#27272a")
            rr(ctx, sd * 50 - 32, -26, 70, 26, 10)
            fill(ctx, "#111")
    else:
        for sd in (-1, 1):
            rr(ctx, sd * 40 - 22, -90, 140 * 1, 44, 14)
            fill(ctx, "#27272a")
            rr(ctx, sd * 40 + 100, -90, 40, 90, 10)
            fill(ctx, "#27272a")
            rr(ctx, sd * 40 + 96, -26, 70, 26, 10)
            fill(ctx, "#111")
    top = hy + 90
    bot = -170 if not sit else -60
    ctx.move_to(-100, top)  # плащ
    ctx.line_to(100, top)
    ctx.line_to(130, bot)
    ctx.line_to(-130, bot)
    ctx.close_path()
    fill(ctx, COAT)
    line(ctx, 0, top + 10, 0, bot, 4, COAT_D)
    for k in range(3):
        ctx.arc(-16, top + 70 + k * 70, 7, 0, TAU)
        fill(ctx, "#451a03")
    rr(ctx, -120, top + 190, 240, 26, 6)  # пояс
    fill(ctx, COAT_D)
    ctx.move_to(-60, top)  # лацканы
    ctx.line_to(0, top + 90)
    ctx.line_to(60, top)
    ctx.set_line_width(8)
    src(ctx, COAT_D)
    ctx.stroke()
    for sd in (-1, 1):  # руки
        line(ctx, sd * 100, top + 20, sd * 120, top + 230, 50, COAT)
        ctx.arc(sd * 122, top + 262, 24, 0, TAU)
        fill(ctx, "#d6a77a")
    ctx.arc(0, hy, 76, 0, TAU)  # голова
    fill(ctx, "#d6a77a")
    ell(ctx, 0, hy - 10, 80, 50)
    fill(ctx, "#000", 0.55)  # тень от шляпы
    for sd in (-1, 1):  # глаза блестят из тени
        ctx.arc(sd * 26 + look * 14, hy - 4, 6, 0, TAU)
        fill(ctx, "#f5f5f4", 0.85)
    m = 6 + 10 * talk * abs(math.sin(t * 18))
    ell(ctx, 0, hy + 40, 22, m * 0.5)
    fill(ctx, "#451a03")
    rr(ctx, -30, hy + 22, 60, 10, 5)  # усы
    fill(ctx, "#3f2a1d")
    ell(ctx, 0, hy - 50, 130, 26)  # шляпа
    fill(ctx, "#292524")
    rr(ctx, -78, hy - 140, 156, 100, 30)
    fill(ctx, "#292524")
    rr(ctx, -78, hy - 70, 156, 20, 4)
    fill(ctx, "#7f1d1d")
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(alpha)


def led_between(ctx, x, y, w, h, t, f1="7", f2="8", col="#ef4444"):
    rr(ctx, x - w / 2, y - h / 2, w, h, 14)
    fill(ctx, "#050505")
    glow(ctx, x, y, w * 0.7, col, 0.25)
    text(ctx, f1, x - w * 0.25, y, h * 0.6, col)
    text(ctx, f2, x + w * 0.25, y, h * 0.6, col, alpha=0.35)
    on = (t * 2) % 1 < 0.5
    ctx.move_to(x - 16, y - 10)
    ctx.line_to(x + 16, y - 10)
    ctx.line_to(x, y + 14)
    ctx.close_path()
    fill(ctx, col, 0.8 if on else 0.2)


def flick(t, k=1.0):
    r = random.Random(int(t * 11))
    return 0.25 if r.random() < 0.18 * k else 1.0


def cabin(ctx, t, light=1.0, mirror_fn=None):
    """Кабина сбоку: задняя стенка с зеркалом, поручень, наклейки, панель, табло 7/8."""
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#3f3f46"), (1, "#27272a")])
    rr(ctx, -100, 200, 1280, 1600, 0)
    lgrad(ctx, -100, 0, 1180, 0, STEEL)
    ctx.fill()
    for k in range(-1, 10):
        line(ctx, k * 140, 200, k * 140, 1800, 2, "#ffffff", 0.07)
    r = random.Random(4)
    for k in range(26):  # царапины
        x0, y0 = r.uniform(-50, 1100), r.uniform(300, 1700)
        line(ctx, x0, y0, x0 + r.uniform(-60, 60), y0 + r.uniform(-20, 20), 2, "#52525b", 0.6)
    rr(ctx, 200, 380, 520, 760, 12)  # зеркало
    lgrad(ctx, 200, 380, 720, 1140, [(0, "#cbd5e1"), (0.5, "#e2e8f0"), (1, "#94a3b8")])
    ctx.fill()
    if mirror_fn:
        ctx.save()
        rr(ctx, 200, 380, 520, 760, 12)
        ctx.clip()
        mirror_fn(ctx)
        ctx.restore()
    line(ctx, 260, 420, 380, 640, 10, "#ffffff", 0.4)
    line(ctx, 300, 420, 420, 640, 4, "#ffffff", 0.3)
    rr(ctx, 200, 380, 520, 760, 12)
    ctx.set_line_width(10)
    src(ctx, "#71717a")
    ctx.stroke()
    for (x, y, w, h, col, tx) in ((-60, 520, 200, 120, "#22c55e", "ДОСТАВКА 15 МИН"),
                                  (-60, 680, 200, 90, "#f97316", "ЕДА 24/7"),
                                  (780, 980, 220, 100, "#3b82f6", "ГРУЗЧИКИ"),
                                  (800, 1110, 170, 80, "#ec4899", "ПОТОЛКИ")):
        rr(ctx, x, y, w, h, 8)
        fill(ctx, col)
        text(ctx, tx, x + w / 2, y + h / 2, min(26, w / len(tx) * 1.8), "#ffffff")
    rr(ctx, 860, 420, 200, 480, 14)  # панель
    lgrad(ctx, 860, 0, 1060, 0, [(0, "#9ca3af"), (0.5, "#e5e7eb"), (1, "#9ca3af")])
    ctx.fill()
    for k in range(10):
        bx, by = 910 + (k % 2) * 100, 470 + (k // 2) * 72
        ctx.arc(bx, by, 26, 0, TAU)
        fill(ctx, "#fbbf24" if 10 - k == 8 else "#d4d4d8")
        text(ctx, str(10 - k), bx, by, 24, "#18181b")
    ctx.arc(960, 850, 28, 0, TAU)
    fill(ctx, "#facc15")
    text(ctx, "ВЫЗОВ", 960, 890, 20, "#18181b")
    rr(ctx, -100, 1300, 1280, 26, 13)  # поручень
    fill(ctx, "#d4d4d8")
    for x in (-60, 1120):
        rr(ctx, x, 1300, 16, 60, 4)
        fill(ctx, "#a1a1aa")
    led_between(ctx, 460, 280, 280, 110, t)
    rr(ctx, 200, 140, 520, 40, 16)  # плафон
    fill(ctx, "#fefce8" if light > 0.5 else "#52525b")
    if light > 0.5:
        glow(ctx, 460, 200, 500, "#fef9c3", 0.25)
    ctx.rectangle(-1200, 1800, 3600, 900)
    fill(ctx, "#3f3f46")
    for k in range(-10, 20):
        line(ctx, k * 90, 1800, k * 90 - 40, 2600, 2, "#27272a")
    rr(ctx, 860, 1770, 140, 30, 4)  # фантик на полу
    fill(ctx, "#ef4444")
    if light < 1:
        ctx.rectangle(-1200, -800, 3600, 3600)
        fill(ctx, "#000", 0.6 * (1 - light))


def lift_doors(ctx, x0, y0, w, h, open_k):
    for side in (0, 1):
        dw = w / 2 * (1 - open_k)
        if dw < 1:
            continue
        dx = x0 if side == 0 else x0 + w - dw
        rr(ctx, dx, y0, dw, h, 4)
        lgrad(ctx, dx, 0, dx + dw, 0, STEEL)
        ctx.fill()
        ex = dx + (dw - 3 if side == 0 else 3)
        line(ctx, ex, y0, ex, y0 + h, 4, "#4b5563")


def landing(ctx, t):
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#d6cfc4"), (1, "#b9b0a2")])
    ctx.rectangle(-1200, 1150, 3600, 300)
    fill(ctx, "#4b6b5a")
    line(ctx, -1200, 1150, 2400, 1150, 8, "#3f594b")
    mailboxes(ctx, -350, 900, 4, 3)
    plant(ctx, 1200, 1700, 1.0, t, "#1d4ed8")
    apartment_door(ctx, 760, 1700, 380, 860, "47")
    rr(ctx, 790, 1700, 320, 36, 8)
    fill(ctx, "#7c2d12")
    ctx.rectangle(-2000, 1700, 5200, 2400)
    fill(ctx, "#8b7d6b")
    for i in range(-16, 30):
        line(ctx, i * 120, 1700, i * 120 - 120, 4000, 3, "#7a6c5a")
    text(ctx, "ЭТАЖ 7", 200, 700, 60, "#3f594b")
    line(ctx, 540, -200, 540, 120, 4, "#111")
    ctx.arc(540, 140, 30, 0, TAU)
    fill(ctx, "#fef9c3")
    glow(ctx, 540, 260, 700, "#fde68a", 0.3)


def mechanic(ctx, x, y, sc, t, seed, facing=1, box=False):
    p = Npc(random.Random(seed), x, y, sc, facing)
    p.shirt, p.pants, p.style, p.item, p.collar = "#ea580c", "#1e3a8a", "cap", "none", "round"
    npc(ctx, p, t, walking=False, stare=0.9)
    if box:
        rr(ctx, x + 60 * sc * facing - 60 * sc, y - 230 * sc, 120 * sc, 70 * sc, 8 * sc)
        fill(ctx, "#dc2626")
        rr(ctx, x + 60 * sc * facing - 30 * sc, y - 250 * sc, 60 * sc, 20 * sc, 6 * sc)
        ctx.set_line_width(6 * sc)
        src(ctx, "#111")
        ctx.stroke()


def bubble(ctx, x, y, w, txt, t0, t, col="#ffffff", tcol="#111827", tail=-1, size=40):
    a = seg(t, t0, t0 + 0.25)
    if a <= 0:
        return
    rows = txt.split("\n")
    h = 40 + len(rows) * size * 1.25
    rr(ctx, x - w / 2, y - h / 2, w, h, 30)
    fill(ctx, col, 0.95 * a)
    ctx.move_to(x + tail * w * 0.25 - 20, y + h / 2 - 2)
    ctx.line_to(x + tail * w * 0.35, y + h / 2 + 50)
    ctx.line_to(x + tail * w * 0.25 + 20, y + h / 2 - 2)
    fill(ctx, col, 0.95 * a)
    for i, rw in enumerate(rows):
        text(ctx, rw, x, y - (len(rows) - 1) * size * 0.62 + i * size * 1.25, size, tcol, alpha=a)


def phone_light(ctx, x, y, t, a=1.0):
    rr(ctx, x - 50, y - 12, 100, 24, 6)
    fill(ctx, "#111")
    ctx.arc(x - 30, y - 12, 5, 0, TAU)
    fill(ctx, "#ffffff")
    glow(ctx, x - 30, y - 300, 500, "#f8fafc", 0.25 * a)


# ================================================================== СЦЕНЫ
def both(ctx, t, sit=False, talk=0.0, e=None, arms="relax", st_alpha=1.0, hero_x=300, st_x=780, knees=False,
         item=None, look=(0.6, 0)):
    if sit:
        me(ctx, hero_x, 1900, 1.0, e or emo("calm"), t, arms=arms, legs=False, look=look, item=item)
        suitcase(ctx, st_x + 230, 1880, 0.7, t=t)
        stranger(ctx, st_x, 1880, 1.0, t, sit=True, talk=talk, alpha=st_alpha, look=-1)
    else:
        suitcase(ctx, st_x + 200, 1800, 0.75, t=t)
        stranger(ctx, st_x, 1800, 1.0, t, talk=talk, alpha=st_alpha, look=-1)
        me(ctx, hero_x, 1800, 1.0, e or emo("worry"), t, arms=arms, look=look, item=item, knees=knees)


def s0_hook(ctx, t, u, D):
    stp = EV["stop"]
    ctx.save()
    jolt = seg(t, stp, stp + 0.15) * (1 - seg(t, stp + 0.15, stp + 0.8))
    cam(ctx, t, 540, lerp(1150, 1250, seg(u, 0, D)) - 60 * jolt, lerp(0.85, 0.95, seg(u, 0, D)), shake=0.2 + 2.0 * jolt)
    cabin(ctx, t, light=flick(t, 0.4) if t > stp else 1.0)
    both(ctx, t, e=emo("shock") if t > stp else emo("neutral"), arms="shock" if t > stp else "relax")
    if t > EV["case"] - 0.2:
        a = seg(t, EV["case"] - 0.2, EV["case"] + 0.2)
        ctx.arc(980, 1650, 190, 0, TAU)
        ctx.set_line_width(8)
        src(ctx, "#facc15", a)
        ctx.stroke()
    ctx.restore()


def s1_button(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(1.0, 1.1, seg(u, 0, D)), shake=0.3)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#52525b"), (1, "#27272a")])
    ctx.translate(0, -170)
    rr(ctx, 140, 220, 800, 1500, 30)
    lgrad(ctx, 140, 0, 940, 0, [(0, "#9ca3af"), (0.5, "#e5e7eb"), (1, "#9ca3af")])
    ctx.fill()
    for k in range(4):  # винты
        ctx.arc(190 + (k % 2) * 700, 270 + (k // 2) * 1400, 14, 0, TAU)
        fill(ctx, "#52525b")
        line(ctx, 180 + (k % 2) * 700, 270 + (k // 2) * 1400, 200 + (k % 2) * 700, 270 + (k // 2) * 1400, 3, "#27272a")
    for k in range(12):  # решётка динамика
        line(ctx, 340, 380 + k * 22, 740, 380 + k * 22, 8, "#3f3f46")
    pressed = (t * 2.5) % 1 < 0.3
    ctx.arc(540, 900 + (6 if pressed else 0), 150, 0, TAU)
    fill(ctx, "#facc15" if not pressed else "#eab308")
    ctx.arc(540, 900, 150, 0, TAU)
    ctx.set_line_width(14)
    src(ctx, "#71717a")
    ctx.stroke()
    ctx.move_to(490, 940)
    ctx.curve_to(490, 840, 590, 840, 590, 940)
    ctx.close_path()
    fill(ctx, "#18181b")
    text(ctx, "ВЫЗОВ ДИСПЕТЧЕРА", 540, 1110, 40, "#18181b")
    ctx.arc(540, 1200, 18, 0, TAU)
    fill(ctx, "#450a0a")
    text(ctx, "НЕТ СВЯЗИ", 540, 1270, 36, "#b91c1c", alpha=0.5 + 0.5 * ((t * 3) % 1 < 0.5))
    # палец
    line(ctx, 1100, 1700, 640, 980 + (20 if pressed else 0), 110, NAVY[0])
    ctx.arc(620, 960 + (20 if pressed else 0), 60, 0, TAU)
    fill(ctx, HEAD)
    rr(ctx, 160, 1400, 760, 280, 30)  # телефон без сети внизу
    fill(ctx, "#0b0b12")
    for k in range(4):
        rr(ctx, 230 + k * 36, 1560 - k * 26, 24, 30 + k * 26, 4)
        fill(ctx, "#3f3f46")
    line(ctx, 210, 1600, 380, 1480, 8, "#ef4444")
    text(ctx, "Нет сети", 640, 1540, 52, "#f87171")
    ctx.restore()
    if flick(t, 1.2) < 1:
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#000", 0.5)


def s2_doors(ctx, t, u, D):
    dr = EV["doors"]
    wh = EV["where"]
    ctx.save()
    cam(ctx, t, 540, 1100, 0.95, shake=0.2)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#3f3f46"), (1, "#27272a")])
    rr(ctx, -300, 120, 1680, 1700, 0)
    lgrad(ctx, -300, 0, 1380, 0, STEEL)
    ctx.fill()
    rr(ctx, 200, 420, 680, 1300, 6)
    fill(ctx, "#18181b")
    lift_doors(ctx, 200, 420, 680, 1300, 0.04 + 0.02 * math.sin(t * 9))
    led_between(ctx, 540, 280, 300, 120, t)
    ctx.rectangle(-1200, 1720, 3600, 900)
    fill(ctx, "#3f3f46")
    for sd in (-1, 1):  # руки в щели двери
        line(ctx, 540 + sd * 420, 1900, 540 + sd * 40, 1050, 110, NAVY[0])
        ctx.arc(540 + sd * 30, 1040, 56, 0, TAU)
        fill(ctx, HEAD)
    if t > dr:
        crossmark(ctx, 540, 1000, 3.0)
    ctx.restore()
    if t > wh - 0.2:  # схема: кабина между этажами
        a = seg(t, wh - 0.2, wh + 0.2)
        ctx.save()
        rr(ctx, 620, 1160, 380, 330, 24)
        fill(ctx, "#0b0b12", 0.9 * a)
        for k, fl in enumerate(("8", "7")):
            y = 1210 + k * 150
            line(ctx, 650, y + 60, 960, y + 60, 6, "#94a3b8", a)
            text(ctx, fl, 670, y + 30, 34, "#94a3b8", alpha=a)
        rr(ctx, 740, 1250 + 40 * math.sin(t), 160, 140, 8)
        fill(ctx, "#facc15", 0.85 * a)
        text(ctx, "?", 820, 1320 + 40 * math.sin(t), 70, "#18181b", alpha=a)
        ctx.restore()
    step_card(ctx, t, EV["steps"][0], 1, "НЕ ОТКРЫВАЙ\nДВЕРИ САМ")


def s3_knock(ctx, t, u, D):
    kn = EV["knock"]
    ctx.save()
    cam(ctx, t, 540, 1250, 0.9, shake=0.2)
    cabin(ctx, t, light=flick(t, 0.3))
    ph = (t - kn) % 1.2 if t > kn else 9
    hit_ = ph < 0.12
    both(ctx, t, e=emo("determined"), arms="paint" if hit_ else "relax", look=(-0.8, -0.2), hero_x=200, st_x=800)
    n = 0 if t < kn else min(3, int((t - kn) / 0.4) + 1)
    for k in range(n):
        a = 1 - seg(t, kn + k * 0.4, kn + k * 0.4 + 1.5)
        text(ctx, "ТУК!", -40 + k * 30, 1050 - k * 110, 70, "#facc15", "#000", 8, alpha=max(0.25, a))
    ctx.restore()
    rr(ctx, 290, 600, 500, 170, 30)
    fill(ctx, "#0b0b12", 0.85)
    text(ctx, "КАЖДЫЕ 5 МИНУТ", 540, 645, 32, "#facc15")
    rem = 300 - (t * 20) % 300
    text(ctx, f"{int(rem // 60):02d}:{int(rem % 60):02d}", 540, 720, 70, "#ffffff")
    step_card(ctx, t, EV["steps"][1], 2, "ВЫЗОВ\nИ ТРИ УДАРА")


def s4_air(ctx, t, u, D):
    si = EV["sit"]
    ctx.save()
    cam(ctx, t, 540, lerp(1250, 1500, ease(seg(t, si, si + 0.6))), 0.9, shake=0.15)
    cabin(ctx, t, light=0.85)
    if t < si:
        both(ctx, t, e=emo("worry"))
    else:
        both(ctx, t, sit=True, e=emo("calm"), arms="relax")
    ctx.restore()
    if t > EV["breathe"] - 0.3:  # дыхательный круг
        ph = (t - EV["breathe"]) % 8
        k = ease(ph / 4) if ph < 4 else ease(1 - (ph - 4) / 4)
        ctx.arc(540, 760, 80 + 70 * k, 0, TAU)
        fill(ctx, "#38bdf8", 0.25)
        ctx.arc(540, 760, 80 + 70 * k, 0, TAU)
        ctx.set_line_width(6)
        src(ctx, "#38bdf8")
        ctx.stroke()
        text(ctx, "ВДОХ" if ph < 4 else "ВЫДОХ", 540, 760, 44, "#ffffff", "#000", 6)
    step_card(ctx, t, EV["steps"][2], 3, "БЕРЕГИ ВОЗДУХ\nСЯДЬ, ДЫШИ")


def s5_talk(ctx, t, u, D):
    tk = EV["talk"]
    ctx.save()
    cam(ctx, t, 540, 1550, 0.95, shake=0.15)
    cabin(ctx, t, light=0.8)
    talking = 1.0 if tk + 1.6 < t < tk + 3.0 else 0.0
    both(ctx, t, sit=True, talk=talking, e=emo("calm"), arms="relax")
    ctx.restore()
    bubble(ctx, 330, 800, 520, "Вы на какой\nэтаж?", tk + 0.2, t, tail=-1, size=50)
    bubble(ctx, 800, 740, 400, "На ваш.", tk + 1.6, t, col="#a8916b", tcol="#1c1917", tail=1, size=54)
    if t > EV["half"]:
        text(ctx, "СПОКОЙНЫЙ РЯДОМ = 50%", 540, 1180, 52, "#22c55e", "#000", 8, alpha=seg(t, EV["half"], EV["half"] + 0.3))
    step_card(ctx, t, EV["steps"][3], 4, "ГОВОРИ\nС ПОПУТЧИКОМ")


def s6_light(ctx, t, u, D):
    li = EV["light"]
    ctx.save()
    cam(ctx, t, 540, 1550, 0.95, shake=0.15)
    cabin(ctx, t, light=0.15)
    both(ctx, t, sit=True, e=emo("calm"), arms="relax")
    phone_light(ctx, 560, 1900, t)
    ctx.restore()
    dark_k = 0.8
    ctx.save()
    ctx.push_group()
    ctx.rectangle(0, 0, W, H)
    fill(ctx, "#000", dark_k)
    ctx.set_operator(cairo.OPERATOR_DEST_OUT)
    g = cairo.RadialGradient(540, 1350, 30, 540, 1350, 800)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.95)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.arc(540, 1350, 800, 0, TAU)
    ctx.set_source(g)
    ctx.fill()
    ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.pop_group_to_source()
    ctx.paint()
    ctx.restore()
    bat = int(lerp(62, 40, seg(t, TL.shots[6][0], TL.shots[7][0])))
    rr(ctx, 380, 640, 320, 120, 24)
    fill(ctx, "#0b0b12", 0.9)
    rr(ctx, 420, 670, 180, 60, 10)
    ctx.set_line_width(5)
    src(ctx, "#ffffff")
    ctx.stroke()
    rr(ctx, 428, 678, 164 * bat / 100, 44, 6)
    fill(ctx, "#facc15" if bat < 50 else "#22c55e")
    text(ctx, f"{bat}%", 650, 700, 40, "#ffffff")
    step_card(ctx, t, EV["steps"][4], 5, "ЭКОНОМЬ\nСВЕТ ТЕЛЕФОНА")


def ic_bell(c, x, y, col, a):
    c.arc(x, y, 22, math.pi, TAU)
    c.line_to(x + 26, y + 16)
    c.line_to(x - 26, y + 16)
    c.close_path()
    fill(c, col, a)
    c.arc(x, y + 22, 6, 0, TAU)
    fill(c, col, a)


def ic_fist(c, x, y, col, a):
    rr(c, x - 22, y - 18, 44, 40, 10)
    fill(c, col, a)
    for k in range(3):
        line(c, x - 12 + k * 12, y - 18, x - 12 + k * 12, y - 4, 3, "#0b0b12", a)


def ic_battery(c, x, y, col, a):
    rr(c, x - 26, y - 14, 46, 28, 5)
    c.set_line_width(4)
    src(c, col, a)
    c.stroke()
    rr(c, x - 22, y - 10, 18, 20, 3)
    fill(c, col, a)
    rr(c, x + 20, y - 6, 6, 12, 2)
    fill(c, col, a)


def ic_heart(c, x, y, col, a):
    c.move_to(x, y + 22)
    c.curve_to(x - 40, y - 4, x - 18, y - 30, x, y - 10)
    c.curve_to(x + 18, y - 30, x + 40, y - 4, x, y + 22)
    fill(c, col, a)


def ic_clock(c, x, y, col, a):
    c.arc(x, y, 24, 0, TAU)
    c.set_line_width(5)
    src(c, col, a)
    c.stroke()
    line(c, x, y, x, y - 14, 4, col, a)
    line(c, x, y, x + 10, y + 4, 4, col, a)


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА ДВУХ ЧАСОВ", [
        ("ВЫЗОВЫ", "кнопка диспетчера", 0.6, "#facc15", "6", ic_bell),
        ("СТУКИ", "по 3 удара", 0.9, "#f97316", "18", ic_fist),
        ("ЗАРЯД", "один фонарь на двоих", 0.4, "#22c55e", "40/100", ic_battery),
        ("ПАНИКА", "ни разу", 0.0, "#ef4444", "0", ic_heart),
        ("ВРЕМЯ", "в кабине", 1.0, "#60a5fa", "2 ч", ic_clock)], EV["tally"])


def s8_done(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1550, 0.95, shake=0.15)
    cabin(ctx, t, light=1.0)
    both(ctx, t, sit=True, e=emo("happy"), arms="relax")
    ctx.restore()
    bubble(ctx, 540, 760, 700, "ДИСПЕТЧЕР: механики\nуже едут, держитесь!", TL.shots[8][0] + 0.3, t, col="#facc15",
           size=42, tail=1)


def s9_open(ctx, t, u, D):
    op = EV["open"]
    ok = ease(seg(t, op, op + 1.4))
    ctx.save()
    cam(ctx, t, 540, 1100, lerp(0.95, 1.05, seg(u, 0, D)), shake=0.15)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#3f3f46"), (1, "#27272a")])
    rr(ctx, -300, 120, 1680, 1700, 0)
    lgrad(ctx, -300, 0, 1380, 0, STEEL)
    ctx.fill()
    rr(ctx, 200, 420, 680, 1300, 6)
    fill(ctx, "#18181b")
    if ok > 0:
        ctx.save()
        rr(ctx, 200, 420, 680, 1300, 6)
        ctx.clip()
        ctx.translate(200, 420)
        ctx.scale(0.62, 0.62)
        landing(ctx, t)
        for k, sd in enumerate((-1, 1)):
            mechanic(ctx, 540 + sd * 260, 2050, 1.1, t, 70 + k, -sd, box=(k == 0))
        ctx.restore()
    lift_doors(ctx, 200, 420, 680, 1300, ok)
    led_between(ctx, 540, 280, 300, 120, t, "7", "", "#22c55e")
    ctx.rectangle(-1200, 1720, 3600, 900)
    fill(ctx, "#3f3f46")
    ctx.restore()
    if t > EV["floor"]:
        text(ctx, "ТВОЙ ЭТАЖ", 540, 600, 70, "#22c55e", "#000", 10, alpha=seg(t, EV["floor"], EV["floor"] + 0.3))


def s10_mech(ctx, t, u, D):
    ask = EV["ask"]
    ctx.save()
    cam(ctx, t, 540, 1250, lerp(0.85, 0.95, seg(u, 0, D)), shake=0.2)
    landing(ctx, t)
    mechanic(ctx, 200, 1950, 1.2, t, 70, 1, box=True)
    mechanic(ctx, 880, 1950, 1.2, t, 71, -1)
    rr(ctx, 380, 1820, 200, 110, 10)  # ящик с инструментами на полу
    fill(ctx, "#dc2626")
    for k in range(3):
        line(ctx, 400 + k * 60, 1820, 410 + k * 60, 1770, 10, ("#9ca3af", "#facc15", "#6b7280")[k])
    me(ctx, 540, 2250, 1.15, emo("worry"), t, arms="relax", back=True, legs=False)
    ctx.restore()
    bubble(ctx, 540, 820, 760, "А с кем вы разговаривали\nдва часа?", ask - 0.6, t, size=44, tail=-1)


def s11_empty(ctx, t, u, D):
    nb = EV["nobody"]
    ctx.save()
    cam(ctx, t, lerp(540, 900, ease(seg(t, EV["only"] - 0.3, EV["only"] + 0.6))), 1350,
        lerp(0.9, 1.25, ease(seg(t, EV["only"] - 0.3, EV["only"] + 0.6))), shake=0.25)
    cabin(ctx, t, light=flick(t, 0.5))
    stranger(ctx, 780, 1800, 1.0, t, alpha=1 - seg(t, nb - 0.6, nb), look=-1)
    suitcase(ctx, 980, 1800, 0.75, t=t)
    me(ctx, 300, 1800, 1.0, emo("fear"), t, arms="shock", look=(0.8, 0.2), tremble=0.6)
    if t > nb:  # шляпа осталась на полу
        ell(ctx, 760, 1790, 110, 22)
        fill(ctx, "#292524", seg(t, nb, nb + 0.3))
    ctx.restore()


def s12_tag(ctx, t, u, D):
    nm = EV["name"]
    fl = EV["flat"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        ctx.save()
        cam(ctx, t, 540, 1000, lerp(1.0, 1.2, seg(u, 0, ec)), shake=0.2)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#3f3f46"), (1, "#18181b")])
        ctx.save()  # чемодан крупно
        ctx.translate(540, 1900)
        ctx.scale(3.2, 3.2)
        suitcase(ctx, 0, 0, 1.0, tag=False)
        ctx.restore()
        ctx.save()  # бирка крупно
        ctx.translate(560, 560)
        ctx.rotate(0.08 + math.sin(t * 2) * 0.03)
        line(ctx, 0, -120, 0, 40, 8, "#78350f")
        rr(ctx, -260, 40, 520, 640, 30)
        fill(ctx, "#fef3c7")
        ctx.arc(0, 90, 22, 0, TAU)
        fill(ctx, "#78350f")
        text(ctx, "ВЛАДЕЛЕЦ:", 0, 220, 50, "#78350f")
        text(ctx, "ТЫ", 0, 330, 120, "#7f1d1d", alpha=seg(t, nm - 0.3, nm))
        line(ctx, -200, 420, 200, 420, 3, "#a8a29e")
        text(ctx, "АДРЕС:", 0, 480, 44, "#78350f")
        text(ctx, "КВ. 47", 0, 580, 100, "#7f1d1d", alpha=seg(t, fl - 0.3, fl))
        ctx.restore()
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
        text(ctx, "Что в чемодане?", 0, 180, 70, "#fcd34d")
    ctx.restore()


SCENES = [s0_hook, s1_button, s2_doors, s3_knock, s4_air, s5_talk, s6_light, s7_tally, s8_done, s9_open,
          s10_mech, s11_empty, s12_tag]
LABELS = {9: "2 ЧАСА СПУСТЯ", 10: "2 ЧАСА СПУСТЯ", 11: "2 ЧАСА СПУСТЯ"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("шесть",), "6"), (("восемнадцать",), "18"), (("сорок", "процентов", "из", "ста"), "40 из 100"),
         (("ноль",), "0"), (("два", "часа"), "2 часа"), (("пять", "минут"), "5 минут")]


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
        text(ctx, "ЗАСТРЯЛ В ЛИФТЕ", 0, 10, 104, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -380, 90, 760, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "С НЕЗНАКОМЦЕМ?", 0, 155, 88, "#ffffff")
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
