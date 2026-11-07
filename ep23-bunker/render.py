"""Серия 23 «Бункер» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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










# ================================================================== БУНКЕР В ЛЕСУ
OLIVE = ("#4d7c0f", "#365314")
CHALK = "#f1f5f9"
RUST = "#9a3412"
HAND = [0, 0]  # последняя позиция руки с фонарём (для луча)


def flashlight(c, x, y, ang=0.0, s=1.0, on=True):
    HAND[0], HAND[1] = c.user_to_device(x, y)
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s, s)
    rr(c, -14, -44, 28, 64, 8)
    fill(c, "#1f2937")
    rr(c, -20, -64, 40, 26, 8)
    fill(c, "#374151")
    for k in range(3):
        line(c, -12, -20 + k * 14, 12, -20 + k * 14, 3, "#4b5563")
    ell(c, 0, -64, 18, 6)
    fill(c, "#fef9c3" if on else "#6b7280")
    c.restore()


def explorer(ctx, x, y, sc, e, t, arms="fwd", look=(0, 0), walk=None, back=False, legs=True, tremble=0.0,
             light=True, lamp=True, ang=0.0, item=None):
    """Герой в оливковой ветровке, рюкзак с запасным фонарём, налобный фонарь."""
    rr(ctx, x - 92 * sc, y - (380 if legs else 210) * sc, 184 * sc, 200 * sc, 30 * sc)  # рюкзак
    fill(ctx, "#78350f")
    rr(ctx, x - 70 * sc, y - (300 if legs else 130) * sc, 140 * sc, 60 * sc, 14 * sc)
    fill(ctx, "#92400e")
    flashlight(ctx, x - 80 * sc, y - (320 if legs else 150) * sc, -0.4, 0.8 * sc, on=False)  # запасной
    it = item
    if it is None and light:
        it = lambda c, hx, hy: flashlight(c, hx, hy, ang, 1.1 * sc)  # noqa: E731
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, walk=walk, back=back, legs=legs, tremble=tremble,
         rim="#fde68a", rim_a=0.55, hood=OLIVE, hand_item=it)
    hy = y - (455 if legs else 285) * sc
    if lamp and not back:  # налобный фонарь
        rr(ctx, x - 110 * sc, hy - 92 * sc, 220 * sc, 18 * sc, 8 * sc)
        fill(ctx, "#111827")
        rr(ctx, x - 26 * sc, hy - 110 * sc, 52 * sc, 40 * sc, 10 * sc)
        fill(ctx, "#374151")
        ctx.arc(x, hy - 90 * sc, 12 * sc, 0, TAU)
        fill(ctx, "#fef9c3")
        glow(ctx, x, hy - 90 * sc, 60 * sc, "#fef9c3", 0.6)


def darkness(ctx, t, beams, a=0.93, amb=()):
    """Темнота в экранных координатах; beams: [(x, y, ang, length, spread)], amb: [(x, y, r)]."""
    ctx.save()
    ctx.identity_matrix()
    ctx.push_group()
    ctx.rectangle(0, 0, W, H)
    fill(ctx, "#020308", a)
    ctx.set_operator(cairo.OPERATOR_DEST_OUT)
    for (x, y, ang, L, sp) in beams:
        g = cairo.RadialGradient(x, y, 10, x, y, L)
        fl = 0.92 + 0.08 * math.sin(t * 23)
        g.add_color_stop_rgba(0, 0, 0, 0, fl)
        g.add_color_stop_rgba(0.75, 0, 0, 0, 0.75 * fl)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.move_to(x, y)
        ctx.arc(x, y, L, ang - sp, ang + sp)
        ctx.close_path()
        ctx.set_source(g)
        ctx.fill()
        g2 = cairo.RadialGradient(x, y, 0, x, y, 160)
        g2.add_color_stop_rgba(0, 0, 0, 0, 0.8)
        g2.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.arc(x, y, 160, 0, TAU)
        ctx.set_source(g2)
        ctx.fill()
    for (x, y, r) in amb:
        g = cairo.RadialGradient(x, y, 0, x, y, r)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.85)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.arc(x, y, r, 0, TAU)
        ctx.set_source(g)
        ctx.fill()
    ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.pop_group_to_source()
    ctx.paint()
    # пыль в лучах
    r = random.Random(3)
    for (x, y, ang, L, sp) in beams:
        for i in range(30):
            d = r.uniform(80, L * 0.9)
            aa = ang + r.uniform(-sp, sp) * 0.9
            px = x + math.cos(aa) * d + math.sin(t * 0.7 + i) * 14
            py = y + math.sin(aa) * d + math.cos(t * 0.5 + i * 1.7) * 14
            ctx.arc(px, py, r.uniform(1.5, 4), 0, TAU)
            fill(ctx, "#fef9c3", 0.35 * (1 - d / L))
    ctx.restore()


def beam_from_hand(ang, L=1300, sp=0.32):
    return (HAND[0], HAND[1], ang, L, sp)


# ------------------------------------------------------------------ лес
def leaf(ctx, x, y, s, rot, col):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ctx.move_to(0, -20)
    ctx.curve_to(16, -10, 16, 10, 0, 22)
    ctx.curve_to(-16, 10, -16, -10, 0, -20)
    fill(ctx, col)
    line(ctx, 0, -18, 0, 22, 2, shade(col, 0.6))
    ctx.restore()


LEAF_COLS = ("#f59e0b", "#ea580c", "#facc15", "#b45309", "#dc2626")


def falling_leaves(ctx, t, n=26, x0=-200, x1=1300, y0=-200, y1=2300, seed=2):
    r = random.Random(seed)
    for i in range(n):
        sp = r.uniform(80, 160)
        ph = r.random()
        y = y0 + ((t * sp / (y1 - y0) + ph) % 1) * (y1 - y0)
        x = r.uniform(x0, x1) + math.sin(t * 1.5 + i) * 60
        leaf(ctx, x, y, r.uniform(0.8, 1.4), t * 2 + i, r.choice(LEAF_COLS))


def mushroom(ctx, x, y, s, kind=0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 0, 40, 8, 0.3)
    rr(ctx, -12, -60, 24, 60, 10)
    fill(ctx, "#f5f5f4")
    if kind == 0:  # мухомор
        ctx.arc(0, -58, 46, math.pi, TAU)
        ctx.close_path()
        fill(ctx, "#dc2626")
        for (dx, dy) in ((-22, -76), (8, -88), (26, -68), (-4, -70)):
            ctx.arc(dx, dy, 6, 0, TAU)
            fill(ctx, "#ffffff")
        rr(ctx, -16, -40, 32, 8, 4)
        fill(ctx, "#e7e5e4")
    else:  # боровик
        ctx.arc(0, -56, 40, math.pi, TAU)
        ctx.close_path()
        fill(ctx, "#7c2d12")
        ell(ctx, -12, -78, 14, 6)
        fill(ctx, "#a16207", 0.6)
    ctx.restore()


def fern(ctx, x, y, s, t, seed=0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for k in range(5):
        a = -math.pi / 2 + (k - 2) * 0.35 + math.sin(t + seed + k) * 0.03
        ex, ey = math.cos(a) * 150, math.sin(a) * 150
        line(ctx, 0, 0, ex, ey, 4, "#3f6212")
        for j in range(1, 8):
            px, py = ex * j / 8, ey * j / 8
            for sd in (-1, 1):
                line(ctx, px, py, px + math.cos(a + sd * 1.2) * (30 - j * 3), py + math.sin(a + sd * 1.2) * (30 - j * 3),
                     5, "#4d7c0f")
    ctx.restore()


def autumn_tree(ctx, x, y, s, t, seed, birch=False):
    r = random.Random(seed)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rr(ctx, -22, -560, 44, 560, 14)
    fill(ctx, "#f5f5f4" if birch else "#57381f")
    if birch:
        for k in range(9):
            rr(ctx, -22 + r.uniform(0, 20), -540 + k * 60, r.uniform(10, 24), 8, 3)
            fill(ctx, "#1c1917")
    else:
        for k in range(5):
            line(ctx, -8 + k * 4, -540, -4 + k * 4, -20, 2, "#3f2713", 0.6)
    line(ctx, 0, -380, -130, -480, 14, "#57381f" if not birch else "#d6d3d1")
    line(ctx, 0, -330, 120, -440, 12, "#57381f" if not birch else "#d6d3d1")
    for k in range(16):
        cx = r.uniform(-200, 200) + math.sin(t * 0.8 + k) * 5
        cy = -620 + r.uniform(-170, 120)
        ctx.arc(cx, cy, r.uniform(70, 120), 0, TAU)
        fill(ctx, r.choice(("#d97706", "#ea580c", "#f59e0b", "#b45309", "#facc15", "#65a30d")))
    for k in range(10):
        ctx.arc(r.uniform(-170, 150), -660 + r.uniform(-120, 80), r.uniform(26, 46), 0, TAU)
        fill(ctx, "#fde68a", 0.45)
    # корни
    for sd in (-1, 1):
        ctx.move_to(sd * 18, -30)
        ctx.curve_to(sd * 50, -10, sd * 80, 0, sd * 120, 10)
        ctx.set_line_width(14)
        src(ctx, "#57381f" if not birch else "#a8a29e")
        ctx.stroke()
    ctx.restore()


def autumn_forest(ctx, t, ground=1500, seed=1, dark=0.0):
    vgrad(ctx, -1500, -1200, 4000, 2900, [(0, "#fcd34d"), (0.5, "#fdba74"), (1, "#a8a29e")])
    glow(ctx, 900, 300, 700, "#fff7ed", 0.6)
    r = random.Random(seed)
    for i in range(18):  # дальние ели
        pine(ctx, -1000 + i * 190 + r.uniform(-40, 40), ground - 140, r.uniform(0.6, 0.8), "#57534e", snow=False)
    for i in range(10):
        autumn_tree(ctx, -1100 + i * 380 + r.uniform(-60, 60), ground - 40, r.uniform(0.7, 0.9), t, seed * 10 + i,
                    birch=(i % 3 == 1))
    ctx.rectangle(-1500, ground - 60, 4000, 2000)
    lgrad(ctx, 0, ground - 60, 0, ground + 900, [(0, "#4d7c0f"), (1, "#365314")])
    ctx.fill()
    for i in range(60):  # мох-кочки
        ell(ctx, -1200 + i * 70 + r.uniform(-20, 20), ground - 50 + r.uniform(0, 600), r.uniform(30, 70), r.uniform(12, 22))
        fill(ctx, r.choice(("#65a30d", "#3f6212", "#84cc16")), 0.7)
    for i in range(90):  # опавшие листья
        leaf(ctx, -1200 + r.uniform(0, 3400), ground + r.uniform(-30, 800), r.uniform(0.7, 1.3), r.uniform(0, 6),
             r.choice(LEAF_COLS))
    rr(ctx, -900, ground + 90, 560, 60, 30)  # поваленное бревно
    fill(ctx, "#57381f")
    ell(ctx, -340, ground + 120, 30, 30)
    fill(ctx, "#a16207")
    for k in range(3):
        ctx.arc(-340, ground + 120, 8 + k * 8, 0, TAU)
        ctx.set_line_width(2)
        src(ctx, "#78350f")
        ctx.stroke()
    for k in range(4):
        ell(ctx, -800 + k * 120, ground + 92, 40, 12)
        fill(ctx, "#65a30d")
    for (x, kind, s) in ((-120, 0, 1.0), (-60, 0, 0.7), (1150, 1, 1.0), (1220, 0, 0.8), (260, 1, 0.7)):
        mushroom(ctx, x, ground + 260 + (x % 7) * 10, s, kind)
    for (x, s) in ((-300, 1.0), (1300, 1.2), (60, 0.8)):
        fern(ctx, x, ground + 200, s, t, x)
    if dark:
        ctx.rectangle(-1500, -1200, 4000, 4000)
        fill(ctx, "#1c1917", dark)


# ------------------------------------------------------------------ люк
def star5(ctx, x, y, R, col, a=1.0):
    for k in range(10):
        rr_ = R if k % 2 == 0 else R * 0.42
        ang = -math.pi / 2 + k * math.pi / 5
        (ctx.move_to if k == 0 else ctx.line_to)(x + math.cos(ang) * rr_, y + math.sin(ang) * rr_)
    ctx.close_path()
    fill(ctx, col, a)


def hatch_top(ctx, x, y, R, t, labels=True, seed=7, wheel_rot=0.0, red=False):
    ctx.save()
    ctx.translate(x, y)
    for k in range(26):  # мох по краю
        a = k / 26 * TAU
        ell(ctx, math.cos(a) * (R + 30), math.sin(a) * (R + 30), 60, 40)
        fill(ctx, ("#3f6212", "#4d7c0f", "#65a30d")[k % 3])
    ctx.arc(0, 0, R + 14, 0, TAU)
    fill(ctx, "#1c1917")
    g = cairo.RadialGradient(-R * 0.3, -R * 0.3, 10, 0, 0, R)
    g.add_color_stop_rgb(0, 0.55, 0.57, 0.6)
    g.add_color_stop_rgb(1, 0.27, 0.29, 0.31)
    ctx.arc(0, 0, R, 0, TAU)
    ctx.set_source(g)
    ctx.fill()
    r = random.Random(seed)
    for k in range(14):  # ржавчина
        a = r.uniform(0, TAU)
        d = r.uniform(0.2, 0.95) * R
        ell(ctx, math.cos(a) * d, math.sin(a) * d, r.uniform(14, 50), r.uniform(10, 30))
        fill(ctx, r.choice((RUST, "#7c2d12", "#b45309")), r.uniform(0.4, 0.8))
    for k in range(24):  # заклёпки
        a = k / 24 * TAU
        ctx.arc(math.cos(a) * (R - 26), math.sin(a) * (R - 26), 9, 0, TAU)
        fill(ctx, "#9ca3af")
        ctx.arc(math.cos(a) * (R - 26) + 2, math.sin(a) * (R - 26) + 2, 9, 0, TAU)
        fill(ctx, "#1f2937", 0.4)
    ctx.arc(0, 0, R - 50, 0, TAU)
    ctx.set_line_width(6)
    src(ctx, "#1f2937", 0.5)
    ctx.stroke()
    if labels:
        star5(ctx, 0, -R * 0.62, R * 0.13, "#e11d48" if red else "#6b7280")
        text(ctx, "БУНКЕР №7", 0, -R * 0.36, R * 0.15, "#d1d5db", "#111827", 4)
        text(ctx, "ОТКРЫВАТЬ ТОЛЬКО", 0, R * 0.5, R * 0.085, "#d1d5db", "#111827", 3)
        text(ctx, "ПО СИГНАЛУ", 0, R * 0.62, R * 0.085, "#d1d5db", "#111827", 3)
    # штурвал
    ctx.save()
    ctx.translate(0, R * 0.08)
    ctx.rotate(wheel_rot)
    ctx.arc(0, 0, R * 0.26, 0, TAU)
    ctx.set_line_width(R * 0.05)
    src(ctx, "#111827")
    ctx.stroke()
    for k in range(4):
        a = k * math.pi / 2
        line(ctx, 0, 0, math.cos(a) * R * 0.26, math.sin(a) * R * 0.26, R * 0.035, "#111827")
        ctx.arc(math.cos(a) * R * 0.3, math.sin(a) * R * 0.3, R * 0.03, 0, TAU)
        fill(ctx, "#374151")
    ctx.arc(0, 0, R * 0.06, 0, TAU)
    fill(ctx, "#4b5563")
    ctx.restore()
    for k in range(5):  # листья на люке
        leaf(ctx, r.uniform(-R, R) * 0.7, r.uniform(-R, R) * 0.7, 2.0, r.uniform(0, 6), r.choice(LEAF_COLS))
    ctx.restore()


# ------------------------------------------------------------------ внутри
def concrete_wall(ctx, x0, x1, y0, y1, seed=3):
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
    lgrad(ctx, 0, y0, 0, y1, [(0, "#57534e"), (1, "#44403c")])
    ctx.fill()
    r = random.Random(seed)
    for k in range(int((x1 - x0) / 300) + 1):  # швы плит
        line(ctx, x0 + k * 300, y0, x0 + k * 300, y1, 4, "#292524", 0.6)
    for k in range(int((x1 - x0) / 40)):  # пятна и трещины
        x = r.uniform(x0, x1)
        y = r.uniform(y0, y1)
        ell(ctx, x, y, r.uniform(20, 80), r.uniform(10, 50))
        fill(ctx, "#292524", 0.15)
    for k in range(int((x1 - x0) / 400)):
        x = r.uniform(x0, x1)
        y = r.uniform(y0, y1)
        ctx.move_to(x, y)
        for j in range(5):
            x += r.uniform(-30, 30)
            y += r.uniform(10, 40)
            ctx.line_to(x, y)
        ctx.set_line_width(2)
        src(ctx, "#1c1917", 0.7)
        ctx.stroke()


def gasmask(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    line(ctx, 0, -60, 0, -20, 4, "#9ca3af")  # крючок
    ell(ctx, 0, 30, 46, 58)
    fill(ctx, "#3f3f46")
    for sd in (-1, 1):
        ctx.arc(sd * 20, 14, 15, 0, TAU)
        fill(ctx, "#a5f3fc", 0.5)
        ctx.arc(sd * 20, 14, 15, 0, TAU)
        ctx.set_line_width(4)
        src(ctx, "#18181b")
        ctx.stroke()
    ctx.arc(0, 66, 20, 0, TAU)
    fill(ctx, "#52525b")
    for k in range(3):
        line(ctx, -12, 60 + k * 6, 12, 60 + k * 6, 2, "#27272a")
    ctx.move_to(0, 86)
    ctx.curve_to(10, 140, -30, 160, -10, 200)
    ctx.set_line_width(10)
    src(ctx, "#52525b")
    ctx.stroke()
    ctx.restore()


def cd_poster(ctx, x, y, w, h, kind=0):
    rr(ctx, x, y, w, h, 4)
    fill(ctx, "#e7e5e4")
    rr(ctx, x + 10, y + 10, w - 20, 50, 2)
    fill(ctx, "#b91c1c")
    text(ctx, ("ПРИ ТРЕВОГЕ", "УКРЫТИЕ", "ПРОТИВОГАЗ")[kind % 3], x + w / 2, y + 36, 26, "#ffffff")
    for k in range(3):  # схематичные человечки
        cx = x + 40 + k * (w - 80) / 2
        ctx.arc(cx, y + 100, 14, 0, TAU)
        fill(ctx, "#1c1917")
        line(ctx, cx, y + 114, cx, y + 160, 8, "#1c1917")
        line(ctx, cx, y + 130, cx + 20 * (1 if k % 2 else -1), y + 150, 6, "#1c1917")
    for k in range(3):
        line(ctx, x + 20, y + 190 + k * 18, x + w - 20 - k * 30, y + 190 + k * 18, 4, "#78716c")
    ell(ctx, x + w - 30, y + h - 20, 30, 18)  # подтёк
    fill(ctx, "#a8a29e", 0.5)


def chalk_arrow(ctx, x, y, s, k=1.0, d=1, col=CHALK, num=None, down=False):
    if k <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    if down:
        ctx.rotate(math.pi / 2)
    ctx.scale(s * d, s)
    L = 150 * k
    line(ctx, -75, 0, -75 + L, 0, 12, col, 0.9)
    if k > 0.7:
        line(ctx, 75, 0, 40, -34, 12, col, 0.9)
        line(ctx, 75, 0, 40, 34, 12, col, 0.9)
    ctx.restore()
    if num is not None and k > 0.9:
        text(ctx, str(num), x, y - 50 * s, 34 * s, col, alpha=0.85)


def drips(ctx, t, xs, y0, y1, seed=1):
    for i, x in enumerate(xs):
        ph = (t * 0.8 + i * 0.37) % 1
        ctx.arc(x, lerp(y0, y1, ph ** 2), 6, 0, TAU)
        fill(ctx, "#93c5fd", 0.7)
        ell(ctx, x, y1 + 6, 30 * ph, 6 * ph)
        ctx.set_line_width(2)
        src(ctx, "#93c5fd", 0.5 * (1 - ph))
        ctx.stroke()


def cables(ctx, x0, x1, y, t):
    for k, col in enumerate(("#1f2937", "#7f1d1d", "#374151", "#1e3a8a")):
        ctx.move_to(x0, y + k * 16)
        n = int((x1 - x0) / 300)
        for j in range(n):
            xa = x0 + j * 300
            ctx.curve_to(xa + 100, y + k * 16 + 50, xa + 200, y + k * 16 + 50, xa + 300, y + k * 16)
        ctx.set_line_width(10)
        src(ctx, col)
        ctx.stroke()
    for j in range(int((x1 - x0) / 300) + 1):  # скобы
        rr(ctx, x0 + j * 300 - 8, y - 20, 16, 90, 4)
        fill(ctx, "#78716c")


def pipe(ctx, x0, x1, y, r=22, col="#57534e"):
    rr(ctx, x0, y - r, x1 - x0, 2 * r, r)
    lgrad(ctx, 0, y - r, 0, y + r, [(0, "#78716c"), (0.5, col), (1, "#292524")])
    ctx.fill()
    for x in range(int(x0) + 200, int(x1), 600):  # вентили и фланцы
        rr(ctx, x - 10, y - r - 8, 20, 2 * r + 16, 4)
        fill(ctx, "#44403c")
        ctx.arc(x + 70, y - r - 40, 30, 0, TAU)
        ctx.set_line_width(8)
        src(ctx, "#b91c1c")
        ctx.stroke()
        line(ctx, x + 70, y - r - 10, x + 70, y - r, 8, "#44403c")


def cage_lamp(ctx, x, y, on=0.0):
    rr(ctx, x - 30, y, 60, 50, 20)
    fill(ctx, "#fef3c7" if on else "#57534e")
    for k in range(4):
        line(ctx, x - 30 + k * 20, y, x - 30 + k * 20, y + 50, 3, "#1c1917")
    line(ctx, x - 32, y + 25, x + 32, y + 25, 3, "#1c1917")
    if on:
        glow(ctx, x, y + 25, 260, "#fde68a", 0.5 * on)


def crate(ctx, x, y, w, h, label, col="#4d5d3a"):
    shadow(ctx, x + w / 2, y + h, w * 0.6, 14, 0.4)
    rr(ctx, x, y, w, h, 6)
    fill(ctx, col)
    rr(ctx, x + 10, y + 10, w - 20, h - 20, 4)
    ctx.set_line_width(4)
    src(ctx, shade(col, 0.7))
    ctx.stroke()
    line(ctx, x + 10, y + 10, x + w - 10, y + h - 10, 4, shade(col, 0.7))
    text(ctx, label, x + w / 2, y + h / 2, min(40, w / max(4, len(label)) * 1.6), "#e7e5e4", alpha=0.85)
    for (cx, cy) in ((x + 14, y + 14), (x + w - 14, y + 14), (x + 14, y + h - 14), (x + w - 14, y + h - 14)):
        ctx.arc(cx, cy, 5, 0, TAU)
        fill(ctx, "#a8a29e")


def corridor(ctx, t, x0=-1200, x1=3200, arrows=(), floor=1900, door_xs=(300, 1700), lamps_on=0.0, seed=3,
             extra=None):
    """Бетонный коридор (вид сбоку). arrows: [(x, y, k, dir, col, num)]."""
    concrete_wall(ctx, x0, x1, 300, floor, seed)
    ctx.rectangle(x0, 160, x1 - x0, 140)
    fill(ctx, "#292524")
    cables(ctx, x0, x1, 330, t)
    pipe(ctx, x0, x1, 520, 26)
    for x in range(int(x0) + 150, int(x1), 700):
        cage_lamp(ctx, x, 600, lamps_on)
    for x in door_xs:  # проёмы-развилки
        rr(ctx, x - 160, 900, 320, floor - 900, 10)
        fill(ctx, "#0c0a09")
        rr(ctx, x - 180, 880, 360, 30, 6)
        fill(ctx, "#78716c")
        text(ctx, f"ОТСЕК {abs(int(x)) // 100 % 9 + 1}", x, 850, 30, "#d6d3d1", "#000", 4)
    r = random.Random(seed)
    for k, x in enumerate(range(int(x0) + 450, int(x1), 900)):
        if any(abs(x - d) < 300 for d in door_xs):
            continue
        if k % 2:
            cd_poster(ctx, x - 110, 760, 220, 300, k)
        else:
            for j in range(3):
                gasmask(ctx, x - 100 + j * 100, 880, 0.9)
    for (x, y, k, d, col, num) in arrows:
        chalk_arrow(ctx, x, y, 1.0, k, d, col, num)
    if extra:
        extra(ctx)
    ctx.rectangle(x0, floor, x1 - x0, 1200)
    lgrad(ctx, 0, floor, 0, floor + 600, [(0, "#3f3a36"), (1, "#1c1917")])
    ctx.fill()
    for k in range(int((x1 - x0) / 500)):
        ell(ctx, x0 + 200 + k * 500 + r.uniform(-80, 80), floor + r.uniform(60, 300), r.uniform(80, 160), 18)
        fill(ctx, "#1e3a5f", 0.5)
    for k in range(int((x1 - x0) / 120)):  # мусор, крошка
        rr(ctx, r.uniform(x0, x1), floor + r.uniform(10, 400), r.uniform(6, 20), r.uniform(4, 10), 2)
        fill(ctx, "#78716c", 0.6)
    drips(ctx, t, [x0 + 600 + k * 830 for k in range(int((x1 - x0) / 830))], 300, floor + 80)


def console(ctx, x, y, t, touched=-1, blink=True):
    """Пульт с рычагами, кнопками и лампами."""
    shadow(ctx, x + 400, y + 520, 460, 30, 0.5)
    rr(ctx, x, y, 800, 520, 16)
    lgrad(ctx, 0, y, 0, y + 520, [(0, "#4b5563"), (1, "#1f2937")])
    ctx.fill()
    rr(ctx, x + 30, y + 30, 740, 160, 10)
    fill(ctx, "#111827")
    for k in range(3):  # стрелочные приборы
        cx = x + 140 + k * 260
        ctx.arc(cx, y + 110, 60, 0, TAU)
        fill(ctx, "#f5f5f4")
        for j in range(9):
            a = math.pi + j * math.pi / 8
            line(ctx, cx + math.cos(a) * 46, y + 110 + math.sin(a) * 46, cx + math.cos(a) * 56,
                 y + 110 + math.sin(a) * 56, 3, "#1c1917")
        a = math.pi + (0.3 + 0.2 * k + 0.05 * math.sin(t * 3 + k)) * math.pi
        line(ctx, cx, y + 110, cx + math.cos(a) * 48, y + 110 + math.sin(a) * 48, 4, "#dc2626")
    for k in range(10):  # лампочки
        on = blink and (int(t * 3 + k * 1.7) % 3 == 0)
        ctx.arc(x + 70 + k * 74, y + 240, 16, 0, TAU)
        col = ("#ef4444", "#22c55e", "#facc15")[k % 3]
        fill(ctx, col if on else shade(col, 0.35))
        if on:
            glow(ctx, x + 70 + k * 74, y + 240, 50, col, 0.6)
    for k in range(8):  # кнопки
        rr(ctx, x + 60 + k * 88, y + 300, 60, 50, 8)
        fill(ctx, "#b91c1c" if k == 3 else "#e7e5e4")
        rr(ctx, x + 60 + k * 88, y + 344, 60, 8, 3)
        fill(ctx, "#000", 0.3)
    text(ctx, "ПУСК", x + 60 + 3 * 88 + 30, y + 375, 20, "#fca5a5")
    for k in range(4):  # рычаги
        lx = x + 120 + k * 180
        rr(ctx, lx - 40, y + 410, 80, 70, 10)
        fill(ctx, "#111827")
        ang = -0.4 if k % 2 else 0.4
        line(ctx, lx, y + 450, lx + math.sin(ang) * 110, y + 450 - math.cos(ang) * 110, 14, "#9ca3af")
        ctx.arc(lx + math.sin(ang) * 110, y + 450 - math.cos(ang) * 110, 22, 0, TAU)
        fill(ctx, ("#dc2626", "#111827", "#facc15", "#111827")[k])
    rr(ctx, x + 560, y - 60, 200, 60, 6)
    fill(ctx, "#a16207")
    text(ctx, "НЕ ТРОГАТЬ", x + 660, y - 30, 28, "#1c1917")


def radio_wall(ctx, x, y, s, t, on=0.0, glitch=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 10, 230, 330, 30, 0.5)
    rr(ctx, -300, -220, 600, 440, 20)
    lgrad(ctx, 0, -220, 0, 220, [(0, "#4d5d3a"), (1, "#2f3a24")])
    ctx.fill()
    rr(ctx, -270, -190, 540, 120, 8)
    fill(ctx, "#fef3c7" if on else "#3f3f2a")
    for k in range(14):
        line(ctx, -250 + k * 36, -190, -250 + k * 36, -160, 3, "#78350f")
    if on:
        glow(ctx, 0, -130, 300, "#fde68a", 0.4 * on)
        line(ctx, -100 + 60 * math.sin(t * 0.7), -190, -100 + 60 * math.sin(t * 0.7), -70, 5, "#dc2626")
    for k in range(9):  # решётка динамика
        line(ctx, -260, -30 + k * 24, 0, -30 + k * 24, 8, "#1c1917")
    for k in range(2):
        ctx.arc(110 + k * 110, 40, 44, 0, TAU)
        fill(ctx, "#1c1917")
        line(ctx, 110 + k * 110, 40, 110 + k * 110 + 34 * math.cos(1 + k), 40 + 34 * math.sin(1 + k), 6, "#d6d3d1")
    ctx.arc(160, 160, 16, 0, TAU)
    fill(ctx, "#ef4444" if on and (t * 2) % 1 < 0.5 else "#450a0a")
    rr(ctx, -340, -60, 50, 160, 10)  # трубка
    fill(ctx, "#111827")
    ctx.move_to(-315, 100)
    for k in range(10):
        ctx.line_to(-315 + (14 if k % 2 else -14), 120 + k * 16)
    ctx.set_line_width(6)
    src(ctx, "#111827")
    ctx.stroke()
    if on:  # волна звука
        for k in range(36):
            hh = (0.2 + 0.8 * abs(nz(t * 8 + k * 0.3, 4))) * 50 * on
            line(ctx, -250 + k * 14, -130 - hh, -250 + k * 14, -130 + hh, 6, "#b45309", 0.8)
    if glitch:
        r = random.Random(int(t * 20))
        for i in range(8):
            ctx.rectangle(-300, r.uniform(-220, 220), 600, r.uniform(4, 20))
            fill(ctx, "#ffffff", 0.2 * glitch)
    ctx.restore()


def phone_map(t, sent=0.0):
    def f(c, x, y, w, h):
        c.rectangle(x, y, w, h)
        fill(c, "#dcfce7")
        r = random.Random(4)
        for k in range(30):
            ell(c, x + r.uniform(0, w), y + r.uniform(0, h * 0.6), r.uniform(30, 90), r.uniform(30, 90))
            fill(c, "#86efac", 0.7)
        c.move_to(x, y + 300)
        c.curve_to(x + 200, y + 260, x + 300, y + 500, x + w, y + 460)
        c.set_line_width(14)
        src(c, "#fde68a")
        c.stroke()
        for k in range(10):  # тропа пунктиром
            ctx_x = x + 80 + k * 40
            ctx_y = y + 600 - k * 22
            c.arc(ctx_x, ctx_y, 5, 0, TAU)
            fill(c, "#78350f")
        px, py = x + w / 2 + 60, y + 330
        c.arc(px, py - 40, 40, 0, TAU)
        fill(c, "#ef4444")
        c.move_to(px - 30, py - 20)
        c.line_to(px, py + 30)
        c.line_to(px + 30, py - 20)
        fill(c, "#ef4444")
        c.arc(px, py - 40, 14, 0, TAU)
        fill(c, "#ffffff")
        k = 0.5 + 0.5 * math.sin(t * 6)
        c.arc(px, py + 30, 30 + 30 * k, 0, TAU)
        c.set_line_width(4)
        src(c, "#ef4444", 1 - k)
        c.stroke()
        rr(c, x + 20, y + h * 0.58, w - 40, h * 0.4, 30)
        fill(c, "#0c0c12", 0.95)
        text(c, "Денис", x + 50, y + h * 0.58 + 50, 36, "#ffffff", align="left")
        text(c, "в сети", x + 50, y + h * 0.58 + 88, 24, "#22c55e", align="left")
        msg = typed("Я тут. Вернусь до 18:00", t, 0, 1) if sent < 1 else "Я тут. Вернусь до 18:00"
        rr(c, x + w - 40 - 480, y + h * 0.58 + 130, 480, 140, 26)
        fill(c, "#2f7cf6")
        rr(c, x + w - 40 - 480, y + h * 0.58 + 130, 480, 60, 26)
        fill(c, "#1d4ed8")
        text(c, "ГЕОТОЧКА  55.7° / 37.6°", x + w - 280, y + h * 0.58 + 160, 24, "#dbeafe")
        text(c, msg, x + w - 500, y + h * 0.58 + 225, 32, "#ffffff", align="left")
        if sent > 0:
            text(c, "отправлено", x + w - 60, y + h * 0.58 + 300, 24, "#93c5fd", align="right", alpha=sent)
    return f


def phone_chat_twist(t, k_new=0.0, glitch=0.0):
    msgs = [(1, "Я тут. Вернусь до 18:00", 1.0), (1, "Нашёл бункер, спускаюсь. Фонари 2/2", 1.0),
            (1, "Спускайся во второй люк. Я жду внизу.", k_new)]
    return chat_screen(msgs, t, header="Денис", glitch=glitch)


# ================================================================== СЦЕНЫ
def s0_hook(ctx, t, u, D):
    fa = EV["fall"]
    ctx.save()
    if t < fa + 0.25:
        cam(ctx, t, lerp(300, 540, seg(u, 0, fa)), 1350, 0.95, shake=0.2)
        autumn_forest(ctx, t, 1500, 1)
        explorer(ctx, lerp(150, 540, seg(t, 0, fa)), 1950, 1.0, emo("calm"), t, arms="relax", walk=t * 6,
                 light=False, lamp=False)
        if t > fa - 0.1:  # мох проваливается
            for k in range(14):
                a = seg(t, fa - 0.1, fa + 0.25)
                ell(ctx, 540 + math.cos(k) * 200 * a, 1960 + a * 120 + math.sin(k * 3) * 30, 30, 14)
                fill(ctx, "#4d7c0f")
    else:
        k = seg(t, fa + 0.25, fa + 0.6)
        cam(ctx, t, 540, 1150, lerp(1.25, 1.0, ease(seg(u, fa, D))), shake=0.25 + 1.6 * (1 - k))
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1c1917"), (1, "#0c0a09")])
        ctx.save()  # яма в мху: вид сверху
        ctx.translate(540, 1200)
        for j in range(40):
            a = j / 40 * TAU
            ell(ctx, math.cos(a) * 520, math.sin(a) * 520, 120, 80)
            fill(ctx, ("#3f6212", "#4d7c0f", "#365314")[j % 3])
        for j in range(30):  # корни и земля в стенках ямы
            a = j / 30 * TAU
            line(ctx, math.cos(a) * 480, math.sin(a) * 480, math.cos(a + 0.1) * 400, math.sin(a + 0.1) * 400, 10,
                 "#57381f")
        ctx.restore()
        hatch_top(ctx, 540, 1200, 380, t, labels=False)
        mushroom(ctx, 160, 1000, 1.2, 0)
        mushroom(ctx, 920, 1720, 1.0, 1)
        explorer(ctx, 560, 1380, 0.9, emo("shock"), t, arms="shock", legs=False, light=False, lamp=False)
        for j in range(16):  # земля и листья сыплются сверху
            a = (t * 1.3 + j / 16) % 1
            leaf(ctx, 200 + j * 45, -100 + a * 1800, 1.5, t * 3 + j, LEAF_COLS[j % 5])
    ctx.restore()
    falling_leaves(ctx, t, 14, seed=4)


def s1_sign(ctx, t, u, D):
    sg = EV["sign"]
    ctx.save()
    cam(ctx, t, 540, lerp(1050, 950, seg(u, 0, D)), lerp(1.0, 1.25, ease(seg(u, 0, D))), shake=0.15)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#292524"), (1, "#1c1917")])
    for j in range(80):
        r = random.Random(j)
        leaf(ctx, r.uniform(-300, 1400), r.uniform(-200, 2200), 2.2, r.uniform(0, 6), r.choice(LEAF_COLS))
    hatch_top(ctx, 540, 1000, 480, t, labels=True)
    # рука смахивает мох и листья
    k = seg(t, sg - 1.0, sg + 1.0)
    hx = lerp(1000, -700, ease(k))
    line(ctx, 1400, 1700, hx + 60, 1000 - 60, 120, OLIVE[0])
    ctx.arc(hx, 1000 - 100, 70, 0, TAU)
    fill(ctx, HEAD)
    for j in range(8):
        a = (t * 2 + j / 8) % 1
        leaf(ctx, hx - 60 - a * 300, 900 + j * 30 + a * 80, 2.0, t * 5 + j, LEAF_COLS[j % 5])
    ctx.restore()


def s2_friend(ctx, t, u, D):
    se = EV["send"]
    ctx.save()
    cam(ctx, t, 540, 1350, 0.9, shake=0.15)
    autumn_forest(ctx, t, 1500, 2)
    ctx.restore()
    ctx.save()
    ctx.rectangle(0, 0, W, H)
    fill(ctx, "#000", 0.35)
    ctx.restore()
    hands_phone(ctx, t, phone_map(t, seg(t, se + 1.0, se + 1.4)), tremble=0.4, sc=0.85, cx=540,
                cy=1050, hood=OLIVE)
    if t > se + 1.0:
        checkmark(ctx, 880, 1500, 1.4, OK, seg(t, se + 1.0, se + 1.4))
    step_card(ctx, t, EV["steps"][0], 1, "НЕ ЛЕЗЬ ОДИН\nТОЧКУ — ДРУГУ")


def shaft(ctx, t, depth=0.0):
    """Шахта с лестницей вниз (вид сбоку)."""
    concrete_wall(ctx, -400, 1500, -600, 3000, 9)
    rr(ctx, 280, -600, 520, 3600, 0)
    fill(ctx, "#1c1917")
    for k in range(-6, 30):  # перекладины
        y = k * 120 + (depth * 600) % 120
        line(ctx, 330, y, 750, y, 14, "#78716c")
        ell(ctx, 330 + (k * 37) % 400, y + 6, 18, 6)
        fill(ctx, RUST, 0.6)
    for x in (330, 750):
        line(ctx, x, -600, x, 3000, 18, "#57534e")
    cables(ctx, -400, 280, 200, t)
    pipe(ctx, 800, 1500, 800, 24)


def s3_lights(ctx, t, u, D):
    sp = EV["spare"]
    ctx.save()
    cam(ctx, t, 540, 1200, 1.0, shake=0.2)
    shaft(ctx, t, seg(u, 0, D))
    ang = -math.pi / 2 + 0.6 + math.sin(t * 1.3) * 0.25
    explorer(ctx, 540, 1950, 1.05, emo("determined"), t, arms="fwd", look=(0.3, 0.6), ang=ang + math.pi / 2)
    ctx.restore()
    beams = [(HAND[0], HAND[1], math.pi / 2 + math.sin(t * 1.3) * 0.25, 1300, 0.33)]
    if t > sp:  # запасной включается
        beams.append((540, 980, -math.pi / 2 - 0.3 + math.sin(t) * 0.2, 1100 * seg(t, sp, sp + 0.3) + 10, 0.25))
    darkness(ctx, t, beams, 0.94, amb=((540, 1450, 300),))
    for k in range(2):  # счётчик фонарей
        on = k == 0 or t > sp
        rr(ctx, 380 + k * 180, 620, 140, 140, 30)
        fill(ctx, "#0b0b12", 0.85)
        flashlight(ctx, 450 + k * 180, 720, 0, 1.4, on)
        if on:
            glow(ctx, 450 + k * 180, 640, 80, "#fef9c3", 0.6)
    text(ctx, f"{1 + (t > sp)}/2", 540, 820, 54, "#fde68a", "#000", 8)
    step_card(ctx, t, EV["steps"][1], 2, "ФОНАРЬ\nИ ЗАПАСНОЙ")


def s4_air(ctx, t, u, D):
    wa = EV["wait"]
    ctx.save()
    cam(ctx, t, 540, 1350, 0.95, shake=0.15)
    autumn_forest(ctx, t, 1250, 3, dark=0.15)
    ctx.save()  # открытый люк в перспективе
    ctx.translate(540, 1650)
    ctx.scale(1, 0.32)
    ctx.arc(0, 0, 360, 0, TAU)
    fill(ctx, "#4d7c0f")
    ctx.arc(0, 0, 300, 0, TAU)
    fill(ctx, "#0c0a09")
    ctx.restore()
    ctx.save()  # откинутая крышка
    ctx.translate(540, 1560)
    ctx.scale(1, 0.95)
    hatch_top(ctx, 0, -300, 300, t, labels=False)
    ctx.restore()
    k = 1 - seg(t, wa, TL.shots[5][0] - 0.5)  # газ выходит и рассеивается
    for j in range(16):
        a = (t * 0.35 + j / 16) % 1
        ell(ctx, 540 + math.sin(t + j) * 150 * a, 1640 - a * 900, 80 + a * 220, 50 + a * 120)
        fill(ctx, "#a3e635", 0.16 * (1 - a) * (0.2 + 0.8 * k))
    explorer(ctx, 950, 1950, 0.95, emo("calm"), t, arms="relax", light=False, look=(-0.6, 0.2))
    for j in range(4):  # верёвка, рюкзак, перчатки
        line(ctx, 100 + j * 30, 1880, 160 + j * 30, 1900, 10, "#ca8a04")
    ctx.restore()
    rem = max(0, 15 * 60 * (1 - seg(t, wa, TL.shots[5][0])))
    rr(ctx, 290, 640, 500, 170, 30)
    fill(ctx, "#0b0b12", 0.85)
    text(ctx, "ПРОВЕТРИВАНИЕ", 540, 680, 32, "#a3e635")
    text(ctx, f"{int(rem // 60):02d}:{int(rem % 60):02d}", 540, 755, 80, "#ffffff")
    step_card(ctx, t, EV["steps"][2], 3, "ВОЗДУХ\nЖДИ 15 МИНУТ")


def s5_notouch(ctx, t, u, D):
    nt = EV["notouch"]
    ctx.save()
    cx = 540 if t < nt[1] else (760 if t < nt[2] else 1100)
    camx = lerp(500, cx, ease(seg(u, 0.5, D)))
    cam(ctx, t, camx, 1350, 0.9, shake=0.2)
    concrete_wall(ctx, -800, 2400, 300, 1800, 11)
    cables(ctx, -800, 2400, 330, t)
    cd_poster(ctx, -260, 700, 240, 320, 0)
    for j in range(3):
        gasmask(ctx, 1500 + j * 110, 820, 0.95)
    console(ctx, 140, 1000, t)
    crate(ctx, 1000, 1350, 300, 220, "НЕ ВСКРЫВАТЬ")
    crate(ctx, 1320, 1400, 240, 170, "ОБР. 7", "#57534e")
    crate(ctx, 1060, 1150, 220, 200, "ОСТОРОЖНО", "#6b5a2e")
    ctx.rectangle(-800, 1800, 3200, 1200)
    fill(ctx, "#292524")
    explorer(ctx, camx + 20, 2150, 1.0, emo("worry"), t, arms="down", look=(0.4, -0.2), light=True, ang=0)
    for j, (x, y) in enumerate(((420, 1330), (520, 1500), (1150, 1450))):
        if t > nt[j]:
            crossmark(ctx, x, y, 1.6)
    ctx.restore()
    darkness(ctx, t, [], 0.55, amb=((540, 1000, 900),))
    step_card(ctx, t, EV["steps"][3], 4, "НИЧЕГО\nНЕ ТРОГАЙ")


def arrows_upto(n, k_last=1.0, x0=-600, dx=320):
    out = []
    for i in range(n):
        out.append((x0 + i * dx, 1180 + (i % 2) * 40, 1.0 if i < n - 1 else k_last, 1, CHALK, i + 1))
    return out


def s6_chalk(ctx, t, u, D):
    ch = EV["chalk"]
    ctx.save()
    n = 3 + int(seg(t, ch, TL.shots[7][0]) * 3)
    hx = lerp(300 * 2 - 30, 300 * (n - 1) - 30, 1.0)
    cam(ctx, t, hx, 1350, 0.9, shake=0.2)
    k_last = (t * 1.6) % 1 if t > ch else 1.0
    corridor(ctx, t, arrows=arrows_upto(n, k_last, x0=0, dx=300), door_xs=(-200, 1500))
    explorer(ctx, 300 * (n - 1) + 120, 2000, 1.0, emo("determined"), t, arms="paint", look=(-0.5, -0.3),
             item=lambda c, x, y: (rr(c, x - 8, y - 24, 16, 40, 4), fill(c, CHALK)))
    ctx.restore()
    darkness(ctx, t, [(W / 2 + 120, 960, math.pi + 0.2, 900, 0.5)], 0.72, amb=((W / 2 + 100, 1250, 560),))
    text(ctx, f"СТРЕЛОК: {n}", 540, 640, 60, CHALK, "#000", 8)
    step_card(ctx, t, EV["steps"][4], 5, "МЕТЬ ПУТЬ\nМЕЛОМ")


def ic_pin(c, x, y, col, a):
    c.arc(x, y - 10, 18, 0, TAU)
    fill(c, col, a)
    c.move_to(x - 14, y)
    c.line_to(x, y + 28)
    c.line_to(x + 14, y)
    fill(c, col, a)


def ic_torch(c, x, y, col, a):
    rr(c, x - 10, y - 10, 20, 40, 5)
    fill(c, col, a)
    rr(c, x - 16, y - 26, 32, 18, 5)
    fill(c, col, a)


def ic_wind(c, x, y, col, a):
    for k in range(3):
        line(c, x - 26, y - 16 + k * 16, x + 20 - k * 8, y - 16 + k * 16, 6, col, a)


def ic_button(c, x, y, col, a):
    c.arc(x, y, 24, 0, TAU)
    fill(c, col, a)
    c.arc(x, y, 12, 0, TAU)
    fill(c, "#0b0b12", a)


def ic_arrow(c, x, y, col, a):
    line(c, x - 26, y, x + 22, y, 7, col, a)
    line(c, x + 24, y, x + 8, y - 14, 7, col, a)
    line(c, x + 24, y, x + 8, y + 14, 7, col, a)


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА СПУСКА", [
        ("ТОЧКА ДРУГУ", "отправлена", 1.0, "#ef4444", "1/1", ic_pin),
        ("ФОНАРИ", "основной + запасной", 1.0, "#fde68a", "2/2", ic_torch),
        ("ВОЗДУХ", "проветрено 15 минут", 1.0, "#a3e635", "1/1", ic_wind),
        ("ТРОНУТО КНОПОК", "ни одной", 0.0, "#60a5fa", "0", ic_button),
        ("СТРЕЛКИ МЕЛОМ", "на каждом повороте", 1.0, CHALK, "23", ic_arrow)], EV["tally"])


def s8_done(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1150, 1.0, shake=0.15)
    shaft(ctx, t, -seg(u, 0, D))
    explorer(ctx, 540, 1900, 1.0, emo("happy"), t, arms="up", look=(0, -0.8), light=False)
    ctx.restore()
    darkness(ctx, t, [(540, -100, math.pi / 2, 1900, 0.35)], 0.8, amb=((540, 1500, 400),))
    glow(ctx, 540, 0, 500, "#fff7ed", 0.5)
    k = back_out(seg(t, EV["right"] - 0.6, EV["right"]))
    if k > 0:
        ctx.save()
        ctx.translate(540, 780)
        ctx.scale(max(0.02, k), max(0.02, k))
        text(ctx, "ВЫХОД НАВЕРХУ", 0, 0, 84, "#22c55e", "#000", 12, shadow=True)
        ctx.restore()


def s9_count(ctx, t, u, D):
    n24 = EV["n24"]
    ctx.save()
    hx = lerp(6200, 300, seg(u, 0, D) ** 0.8)
    cam(ctx, t, hx, 1350, 0.85, shake=0.25 + 0.6 * seg(t, n24, n24 + 0.3))
    arr = [(x, y, k, 1, col, None) for (x, y, k, d, col, num) in arrows_upto(23, 1.0, x0=0, dx=280)]
    arr.append((-170, 1450, 1.0, 1, "#b91c1c", None))
    corridor(ctx, t, x0=-1000, x1=7400, arrows=arr, door_xs=(1300, 3500, 5600), seed=5)
    explorer(ctx, hx + 140, 2000, 1.0, emo("worry") if t > n24 else emo("calm"), t, arms="fwd", walk=None if t > n24 else t * 6,
             look=(-0.6, 0), ang=-math.pi / 2)
    ctx.restore()
    darkness(ctx, t, [(HAND[0], HAND[1], math.pi, 1000, 0.42)], 0.86, amb=((W / 2 + 140, 1150, 420),))
    seen = min(24, 1 + int(seg(t, TL.shots[9][0], n24 + 0.1) * 23.99))
    rr(ctx, 290, 600, 500, 160, 30)
    fill(ctx, "#0b0b12", 0.85)
    text(ctx, "СТРЕЛОК", 540, 640, 32, "#94a3b8")
    text(ctx, str(seen), 540, 710, 90, "#ef4444" if seen == 24 else CHALK)


def s10_extra(ctx, t, u, D):
    dn = EV["down"]
    ctx.save()
    k = ease(seg(t, dn - 0.4, dn + 0.8))
    cam(ctx, t, 540, lerp(1050, 1700, k), lerp(1.2, 0.85, k), shake=0.35)
    concrete_wall(ctx, -800, 2000, 0, 1900, 21)
    pipe(ctx, -800, 2000, 300, 24)
    # красная стрелка с подтёками
    ctx.save()
    ctx.translate(540, 1000)
    line(ctx, 0, -260, 0, 160, 34, "#991b1b")
    line(ctx, 0, 190, -110, 70, 34, "#991b1b")
    line(ctx, 0, 190, 110, 70, 34, "#991b1b")
    for j in range(6):
        dl = 60 + 140 * seg(t, TL.shots[10][0] + j * 0.3, TL.shots[10][0] + 2 + j * 0.3)
        line(ctx, -14 + (j - 3) * 12, -200 + j * 60, -14 + (j - 3) * 12, -200 + j * 60 + dl, 8, "#7f1d1d", 0.9)
    ctx.restore()
    chalk_arrow(ctx, 120, 800, 1.0, 1.0, -1, CHALK, 23)
    ctx.rectangle(-800, 1900, 2800, 1200)
    fill(ctx, "#1c1917")
    ctx.save()  # второй люк в полу
    ctx.translate(540, 2150)
    ctx.scale(1, 0.38)
    hatch_top(ctx, 0, 0, 360, t, labels=True, seed=13, red=True)
    ctx.restore()
    for j in range(5):  # свежие царапины вокруг
        line(ctx, 200 + j * 150, 2050 + (j % 2) * 140, 260 + j * 150, 2080 + (j % 2) * 140, 4, "#d6d3d1", 0.7)
    ctx.restore()
    darkness(ctx, t, [(540, 300, math.pi / 2, 1900, 0.42)], 0.88)


def s11_radio(ctx, t, u, D):
    ro = EV["radio_on"]
    de = EV["descend"]
    ctx.save()
    cam(ctx, t, 540, 1150, lerp(0.95, 1.1, seg(u, 0, D)), shake=0.25)
    concrete_wall(ctx, -800, 2000, 0, 2200, 31)
    cables(ctx, -800, 2000, 200, t)
    radio_wall(ctx, 470, 860, 1.05, t, on=seg(t, ro - 0.2, ro + 0.2), glitch=0.6 if t > de else 0.0)
    cd_poster(ctx, 60, 1400, 220, 300, 2)
    gasmask(ctx, 920, 1440, 1.1)
    explorer(ctx, 820, 1720, 1.2, emo("fear"), t, arms="down", legs=False, look=(-0.7, -0.4), tremble=0.6,
             light=False)
    ctx.restore()
    darkness(ctx, t, [], 0.6, amb=((540, 1100, 750),))
    if t > de - 0.3:
        a = seg(t, de - 0.3, de)
        rr(ctx, 120, 560, 840, 150, 40)
        fill(ctx, "#0b0b12", 0.85 * a)
        text(ctx, "ДЕНИС: «Я СПУСКАЮСЬ К ТЕБЕ»", 540, 635, 44, "#fde68a", alpha=a)


def s12_second(ctx, t, u, D):
    sc = EV["second"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        ctx.save()
        cam(ctx, t, 540, 1000, 1.0, shake=0.2)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1c1917"), (1, "#0c0a09")])
        ctx.restore()
        kn = seg(t, TL.shots[12][0] + 0.6, TL.shots[12][0] + 1.0)
        hands_phone(ctx, t, phone_chat_twist(t, kn, glitch=0.5 * seg(t, sc, sc + 0.5)), tremble=1.4, sc=0.9, cy=1000, hood=OLIVE)
        if t > sc:
            a = seg(t, sc, sc + 0.3)
            rr(ctx, 140, 1430, 800, 120, 30)
            fill(ctx, "#7f1d1d", 0.9 * a)
            text(ctx, "ТЫ ЭТО НЕ ПИСАЛ", 540, 1490, 60, "#ffffff", alpha=a)
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
        text(ctx, "Кто пишет твоему другу?", 0, 180, 64, "#fca5a5")
    ctx.restore()


SCENES = [s0_hook, s1_sign, s2_friend, s3_lights, s4_air, s5_notouch, s6_chalk, s7_tally, s8_done, s9_count,
          s10_extra, s11_radio, s12_second]
LABELS = {9: "ОБРАТНЫЙ ПУТЬ", 10: "ОБРАТНЫЙ ПУТЬ", 11: "ОБРАТНЫЙ ПУТЬ"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("два", "из", "двух"), "2 из 2"), (("двадцать", "три"), "23"), (("двадцать", "четыре"), "24"),
         (("ноль",), "0")]


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
        text(ctx, "В ЛЕСУ ЛЮК", 0, 10, 116, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -330, 90, 660, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "БУНКЕР №7", 0, 155, 100, "#ffffff")
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
