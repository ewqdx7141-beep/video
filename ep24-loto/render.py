"""Серия 24 «Лотерея» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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











def kitchen(ctx, t, lamp=True):
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#fef3c7"), (1, "#fde68a")])
    for i in range(-10, 20):  # кафель-фартук
        for j in range(4):
            rr(ctx, i * 90, 860 + j * 60, 86, 56, 4)
            fill(ctx, "#ffffff" if (i + j) % 2 else "#e0f2fe")
    rr(ctx, 150, 200, 500, 520, 10)  # окно со двором
    fill(ctx, "#bae6fd")
    for k in range(3):
        rr(ctx, 170 + k * 160, 500 - k * 60, 120, 220 + k * 60, 4)
        fill(ctx, "#94a3b8")
    for x0 in (150, 400, 650):
        ctx.rectangle(x0 - 8, 200, 16, 520)
        fill(ctx, "#ffffff")
    rr(ctx, 120, 720, 560, 26, 6)
    fill(ctx, "#ffffff")
    plant(ctx, 260, 722, 0.45, t, "#c2410c")
    rr(ctx, 520, 680, 50, 44, 8)  # банка с ложками
    fill(ctx, "#a7f3d0", 0.8)
    for k in range(3):
        line(ctx, 535 + k * 10, 680, 530 + k * 14, 620, 4, "#9ca3af")
    rr(ctx, 780, 260, 400, 280, 10)  # шкафчики
    fill(ctx, "#ffffff")
    line(ctx, 980, 260, 980, 540, 4, "#d6d3d1")
    for k in range(2):
        rr(ctx, 940 + k * 60, 380, 14, 50, 6)
        fill(ctx, "#a8a29e")
    rr(ctx, -600, 1100, 2400, 50, 8)  # столешница
    fill(ctx, "#d6d3d1")
    rr(ctx, -600, 1150, 2400, 500, 0)
    fill(ctx, "#a16207")
    for k in range(-2, 6):
        rr(ctx, k * 280 + 20, 1190, 240, 420, 10)
        ctx.set_line_width(4)
        src(ctx, "#78350f")
        ctx.stroke()
        rr(ctx, k * 280 + 120, 1220, 40, 12, 6)
        fill(ctx, "#fde68a")
    # плита с кастрюлей и чайник
    rr(ctx, 860, 1060, 300, 40, 6)
    fill(ctx, "#334155")
    rr(ctx, 900, 960, 140, 100, 14)
    fill(ctx, "#94a3b8")
    puff(ctx, 970, 950, t, 3, n=4, col="#ffffff", life=1.2, rate=0.4, dx=20, dy=-120, a=0.4)
    ctx.rectangle(-1200, 1650, 3600, 1400)
    fill(ctx, "#78350f")
    for k in range(-12, 26):
        line(ctx, k * 110, 1650, k * 110 - 60, 3000, 3, "#5c2a0a", 0.6)
    if lamp:
        hanging_lamp(ctx, 540, 120, on=True, col="#f59e0b")



def atm(ctx, x, y, s, t, receipt=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rr(ctx, -120, -420, 240, 420, 16)
    lgrad(ctx, -120, 0, 120, 0, [(0, "#1e3a8a"), (0.5, "#2563eb"), (1, "#1e3a8a")])
    ctx.fill()
    rr(ctx, -90, -380, 180, 120, 8)
    fill(ctx, "#bbf7d0")
    text(ctx, "ДОЛГ: 0", 0, -320, 30, "#166534")
    for k in range(12):
        rr(ctx, -80 + (k % 3) * 56, -230 + (k // 3) * 36, 44, 26, 4)
        fill(ctx, "#cbd5e1")
    rr(ctx, -60, -90, 120, 12, 4)
    fill(ctx, "#111")
    if receipt > 0:
        rr(ctx, -40, -84, 80, 160 * receipt, 2)
        fill(ctx, "#ffffff")
        text(ctx, "ПОГАШЕН", 0, -84 + 80 * receipt, 18, "#16a34a", alpha=receipt)
    ctx.restore()




# ================================================================== ЛОТЕРЕЯ 500 МЛН
TEAL = ("#0d9488", "#115e59")
GOLD = "#fbbf24"


def lucky(ctx, x, y, sc, e, t, arms="relax", look=(0, 0), walk=None, back=False, legs=True, tremble=0.0, item=None):
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, walk=walk, back=back, legs=legs, tremble=tremble,
         rim="#fde68a", rim_a=0.6, hood=TEAL, hand_item=item)


def ticket(ctx, x, y, s, t, back=False, rot=0.0, glow_k=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    shadow(ctx, 0, 230, 300, 24, 0.35)
    if glow_k:
        glow(ctx, 0, 0, 600, GOLD, 0.5 * glow_k)
    rr(ctx, -300, -200, 600, 400, 18)
    fill(ctx, "#fffbeb")
    for k in range(-280, 300, 40):  # перфорация
        ctx.arc(k, -200, 6, 0, TAU)
        fill(ctx, "#e7e5e4")
    if not back:
        rr(ctx, -300, -200, 600, 80, 18)
        fill(ctx, "#dc2626")
        text(ctx, "ЛОТО-МИЛЛИОН", -40, -158, 44, "#ffffff")
        star = cairo.LinearGradient(160, -100, 280, 0)
        for k, c in enumerate(("#f472b6", "#60a5fa", "#a3e635", "#facc15", "#f472b6")):
            star.add_color_stop_rgb(k / 4, *hexc(c)[:3])
        ell(ctx, 220, -40, 56, 40)  # голограмма
        ctx.set_source(star)
        ctx.fill()
        line(ctx, 180 + (t * 80) % 80, -76, 200 + (t * 80) % 80, -4, 6, "#ffffff", 0.6)
        nums = (7, 14, 23, 31, 42, 48)
        for i, n in enumerate(nums):
            cx = -230 + i * 80
            ctx.arc(cx, 40, 32, 0, TAU)
            fill(ctx, "#fde68a")
            ctx.arc(cx, 40, 32, 0, TAU)
            ctx.set_line_width(4)
            src(ctx, "#dc2626")
            ctx.stroke()
            text(ctx, str(n), cx, 42, 30, "#7f1d1d")
        for k in range(46):  # штрихкод
            line(ctx, -270 + k * 7, 110, -270 + k * 7, 170, 2 + (k * 7 % 3), "#1c1917")
        text(ctx, "№ 0047-118-205", 170, 140, 26, "#57534e")
        text(ctx, "ТИРАЖ 1307", -150, -80, 26, "#78716c")
    else:
        for k in range(9):
            line(ctx, -260, -140 + k * 30, 260 - (k % 3) * 60, -140 + k * 30, 3, "#d6d3d1")
        text(ctx, "Условия розыгрыша на сайте", 0, 160, 22, "#a8a29e")
    ctx.restore()


def lotto_drum(ctx, x, y, s, t, spin=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    line(ctx, -160, 260, -60, 120, 16, "#6b7280")
    line(ctx, 160, 260, 60, 120, 16, "#6b7280")
    rr(ctx, -200, 250, 400, 30, 10)
    fill(ctx, "#374151")
    ctx.arc(0, 0, 170, 0, TAU)
    fill(ctx, "#e0f2fe", 0.35)
    r = random.Random(5)
    for k in range(22):
        a = r.uniform(0, TAU) + t * spin * r.uniform(1, 3)
        d = r.uniform(30, 130)
        ctx.arc(math.cos(a) * d, math.sin(a) * d * 0.8 + 30, 24, 0, TAU)
        fill(ctx, r.choice(("#ef4444", "#facc15", "#22c55e", "#3b82f6", "#f97316", "#ffffff")))
    ctx.arc(0, 0, 170, 0, TAU)
    ctx.set_line_width(10)
    src(ctx, "#94a3b8")
    ctx.stroke()
    for k in range(6):
        a = k * math.pi / 3 + t * spin
        line(ctx, math.cos(a) * 170, math.sin(a) * 170, math.cos(a + math.pi) * 170, math.sin(a + math.pi) * 170, 3,
             "#cbd5e1", 0.5)
    ctx.restore()


def kiosk(ctx, x, y, t, rain=False, seller_grin=0.0):
    ctx.save()
    ctx.translate(x, y)
    shadow(ctx, 0, 0, 420, 30, 0.4)
    rr(ctx, -380, -900, 760, 900, 16)
    lgrad(ctx, -380, 0, 380, 0, [(0, "#1d4ed8"), (0.5, "#2563eb"), (1, "#1e40af")])
    ctx.fill()
    rr(ctx, -420, -1000, 840, 130, 14)
    fill(ctx, "#dc2626")
    text(ctx, "ЛОТЕРЕИ", 0, -935, 76, "#ffffff", "#7f1d1d", 6)
    for k in range(8):  # бахрома-навес
        ctx.arc(-370 + k * 106, -870, 53, 0, math.pi)
        fill(ctx, "#ffffff" if k % 2 else "#dc2626")
    rr(ctx, -300, -760, 600, 420, 10)  # окно
    fill(ctx, "#fef3c7")
    glow(ctx, 0, -560, 400, "#fde68a", 0.5)
    p = Npc(random.Random(77), 0, -360, 0.75, -1)
    p.style, p.hair, p.shirt, p.glasses, p.earrings, p.item = "bun", "#78350f", "#be185d", True, True, "none"
    npc(ctx, p, t, walking=False, grin=seller_grin, stare=0.4 * seller_grin)
    lotto_drum(ctx, 200, -520, 0.45, t)
    for k in range(6):  # билеты-веером
        ctx.save()
        ctx.translate(-220 + k * 20, -420)
        ctx.rotate(-0.3 + k * 0.1)
        rr(ctx, -30, -50, 60, 100, 6)
        fill(ctx, ("#fef08a", "#fecaca", "#bbf7d0")[k % 3])
        ctx.restore()
    rr(ctx, -300, -340, 600, 26, 4)
    fill(ctx, "#64748b")
    rr(ctx, -340, -300, 300, 260, 8)  # плакаты
    fill(ctx, "#facc15")
    text(ctx, "ДЖЕКПОТ", -190, -250, 40, "#b91c1c")
    text(ctx, "500 МЛН", -190, -170, 52, "#7f1d1d")
    rr(ctx, 40, -300, 300, 260, 8)
    fill(ctx, "#22c55e")
    text(ctx, "ТИРАЖ", 190, -230, 40, "#ffffff")
    text(ctx, "КАЖДУЮ", 190, -170, 34, "#ffffff")
    text(ctx, "СУББОТУ", 190, -125, 34, "#ffffff")
    ctx.restore()
    if rain:
        r = random.Random(int(t * 20))
        for i in range(90):
            xx, yy = r.uniform(-300, 1400), r.uniform(0, 2300)
            line(ctx, xx, yy, xx - 10, yy + 46, 2, "#bfdbfe", 0.5)


def office_desk(ctx, x, y, s, t, seed=1, monitor="#1e3a8a"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rr(ctx, -260, -20, 520, 30, 6)
    fill(ctx, "#d6d3d1")
    for sx in (-240, 220):
        rr(ctx, sx, 10, 20, 260, 4)
        fill(ctx, "#a8a29e")
    rr(ctx, -150, -260, 300, 200, 10)
    fill(ctx, "#111827")
    rr(ctx, -136, -246, 272, 172, 6)
    fill(ctx, monitor)
    r = random.Random(seed)
    for k in range(5):
        line(ctx, -120, -226 + k * 30, -120 + r.uniform(80, 240), -226 + k * 30, 6, "#93c5fd", 0.6)
    rr(ctx, -20, -60, 40, 40, 4)
    fill(ctx, "#374151")
    rr(ctx, -120, -36, 200, 20, 4)  # клавиатура
    fill(ctx, "#e5e7eb")
    coffee_cup(ctx, 180, -20, 0.18, t, heart=False)
    for k in range(3):  # стикеры
        rr(ctx, 150 + k * 4, -250 + k * 40, 40, 36, 2)
        fill(ctx, ("#fde047", "#f9a8d4", "#86efac")[k])
    ctx.restore()


def cooler(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rr(ctx, -70, -300, 140, 300, 10)
    fill(ctx, "#f1f5f9")
    rr(ctx, -60, -520, 120, 220, 50)
    fill(ctx, "#7dd3fc", 0.7)
    for k in range(2):
        rr(ctx, -40 + k * 50, -230, 30, 26, 4)
        fill(ctx, "#ef4444" if k else "#3b82f6")
    rr(ctx, -50, -120, 100, 10, 3)
    fill(ctx, "#94a3b8")
    ctx.restore()


def office(ctx, t, seed=3):
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#f1f5f9"), (1, "#e2e8f0")])
    for k in range(-4, 10):
        rr(ctx, k * 300, 140, 220, 30, 8)
        fill(ctx, "#ffffff")
        glow(ctx, k * 300 + 110, 160, 200, "#ffffff", 0.3)
    for k in range(4):  # окна
        rr(ctx, -300 + k * 480, 320, 380, 520, 10)
        fill(ctx, "#bae6fd")
        skyline(ctx, 60 + k, -300 + k * 480, 80 + k * 480, 840, 120, 380, "#94a3b8")
        for j in range(5):  # жалюзи
            line(ctx, -300 + k * 480, 360 + j * 90, 80 + k * 480, 360 + j * 90, 6, "#e2e8f0", 0.8)
    rr(ctx, 1500, 400, 200, 260, 6)  # календарь
    fill(ctx, "#ffffff")
    rr(ctx, 1500, 400, 200, 60, 6)
    fill(ctx, "#dc2626")
    plant(ctx, -380, 1200, 0.9, t)
    cooler(ctx, 1400, 1200, 1.0)
    ctx.rectangle(-1200, 1200, 3600, 1600)
    fill(ctx, "#cbd5e1")
    for k in range(-12, 26):
        line(ctx, k * 140, 1200, k * 140 - 60, 2800, 3, "#94a3b8", 0.5)


def coworkers(ctx, t, seed=8, n=4, y0=1350):
    r = random.Random(seed)
    for i in range(n):
        p = Npc(r, -150 + i * 420, y0 + (i % 2) * 60, 0.9, r.choice((-1, 1)))
        p.item = "none"
        npc(ctx, p, t, walking=False)
        office_desk(ctx, -150 + i * 420, y0 + 60 + (i % 2) * 60, 0.75, t, i)


def bank_hall(ctx, t):
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#ecfeff"), (1, "#cffafe")])
    for k in range(-2, 6):  # окошки операционистов
        x = k * 330
        rr(ctx, x, 500, 300, 560, 10)
        fill(ctx, "#ffffff")
        rr(ctx, x + 20, 540, 260, 300, 6)
        fill(ctx, "#bae6fd", 0.6)
        rr(ctx, x + 90, 450, 120, 50, 8)
        fill(ctx, "#0e7490")
        text(ctx, str(k + 3), x + 150, 476, 34, "#ffffff")
        p = Npc(random.Random(k + 40), x + 150, 900, 0.55, 1)
        p.item = "none"
        npc(ctx, p, t, walking=False)
    rr(ctx, 300, 200, 480, 180, 14)  # табло очереди
    fill(ctx, "#0f172a")
    text(ctx, "А-017  →  ОКНО 4", 540, 260, 44, "#22c55e")
    text(ctx, "Б-203  →  ОКНО 2", 540, 330, 44, "#facc15")
    ctx.rectangle(-1200, 1060, 3600, 60)
    fill(ctx, "#0e7490")
    ctx.rectangle(-1200, 1120, 3600, 1600)
    fill(ctx, "#e5e7eb")
    for i in range(-10, 20):
        for j in range(8):
            rr(ctx, i * 160, 1120 + j * 160, 156, 156, 2)
            fill(ctx, "#f3f4f6" if (i + j) % 2 else "#e5e7eb")


def money_stack(ctx, x, y, s, n=5, col="#86efac"):
    for k in range(n):
        rr(ctx, x - 60 * s, y - k * 18 * s, 120 * s, 16 * s, 3 * s)
        fill(ctx, col)
        rr(ctx, x - 14 * s, y - k * 18 * s, 28 * s, 16 * s, 2 * s)
        fill(ctx, "#fef3c7")


# ================================================================== СЦЕНЫ
def amount_text(ctx, t, t0, y=1250, size=110, final=500_000_000):
    k = ease(seg(t, t0 - 0.2, t0 + 0.9))
    if k <= 0:
        return
    v = int(final * k)
    s = max(0.02, back_out(seg(t, t0 - 0.2, t0 + 0.2)))
    ctx.save()
    ctx.translate(540, y)
    ctx.scale(s, s)
    glow(ctx, 0, 0, 500, GOLD, 0.4)
    text(ctx, fmt_rub(v), 0, 0, size, GOLD, "#000", 14, shadow=True)
    text(ctx, "РУБЛЕЙ", 0, size * 0.85, size * 0.45, "#ffffff", "#000", 8)
    ctx.restore()


def fmt_rub(v):
    return f"{int(v):,}".replace(",", " ")


def lotto_screen(t, win=0.0):
    def f(c, x, y, w, h):
        vgrad(c, x, y, w, h, [(0, "#1e1b4b"), (1, "#312e81")])
        text(c, "ТИРАЖ 1307", x + w / 2, y + 120, 44, "#c7d2fe")
        text(c, "Выигрышные числа", x + w / 2, y + 190, 34, "#a5b4fc")
        for i, n in enumerate((7, 14, 23, 31, 42, 48)):
            k = seg(t, i * 0.35, i * 0.35 + 0.3)
            cx = x + 80 + (i % 3) * 150 + 30
            cy = y + 320 + (i // 3) * 150
            c.arc(cx, cy, 58 * max(0.02, back_out(k)), 0, TAU)
            fill(c, ("#ef4444", "#facc15", "#22c55e", "#3b82f6", "#f97316", "#ec4899")[i])
            if k > 0.5:
                text(c, str(n), cx, cy + 4, 50, "#ffffff")
        if win > 0:
            rr(c, x + 30, y + 650, w - 60, 300, 30)
            fill(c, GOLD, win)
            text(c, "6 ИЗ 6", x + w / 2, y + 730, 70, "#7f1d1d", alpha=win)
            text(c, "ДЖЕКПОТ", x + w / 2, y + 820, 64, "#7f1d1d", alpha=win)
            text(c, "500 000 000", x + w / 2, y + 900, 50, "#7f1d1d", alpha=win)
    return f


def s0_hook(ctx, t, u, D):
    wn = EV["win"]
    ctx.save()
    cam(ctx, t, 540, 1150, lerp(0.95, 1.1, seg(u, 0, D)), shake=0.2 + 1.0 * seg(t, wn, wn + 0.2) * (1 - seg(t, wn + 0.3, wn + 1)))
    kitchen(ctx, t)
    rr(ctx, -200, 1280, 1500, 40, 8)  # стол
    fill(ctx, "#92400e")
    for k in range(5):
        cookie_x = 120 + k * 50
        ctx.arc(cookie_x, 1270, 26, math.pi, TAU)
        fill(ctx, "#d97706")
    lucky(ctx, 400, 1900, 1.0, emo("shock") if t > wn else emo("neutral"), t,
          arms="phone" if t < wn else "shock", look=(0.5, -0.3))
    ctx.restore()
    if t < wn + 0.4:
        ctx.save()
        ctx.translate(720, 1000)
        ctx.scale(0.8, 0.8)
        phone_body(ctx, 0, 0, 380, 760, lotto_screen(t, seg(t, wn - 0.4, wn)))
        ctx.restore()
    amount_text(ctx, t, wn, 900)
    if t > wn:
        money_burst_k = seg(t, wn, wn + 2)
        r = random.Random(1)
        for i in range(30):
            a = r.uniform(0, TAU)
            d = 900 * money_burst_k * r.uniform(0.5, 1)
            ctx.save()
            ctx.translate(540 + math.cos(a) * d, 1250 + math.sin(a) * d + 400 * money_burst_k ** 2)
            ctx.rotate(t * 3 + i)
            rr(ctx, -50, -25, 100, 50, 4)
            fill(ctx, "#86efac", 1 - money_burst_k * 0.5)
            ctx.restore()


def s1_ticket(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1050, lerp(1.0, 1.15, seg(u, 0, D)), shake=0.2)
    rr(ctx, -800, -800, 2700, 3600, 0)  # стол сверху
    lgrad(ctx, 0, -800, 0, 2800, [(0, "#a16207"), (1, "#78350f")])
    ctx.fill()
    for k in range(-10, 20):
        line(ctx, -800, k * 90 + math.sin(k) * 20, 2000, k * 90 + 40 + math.cos(k) * 20, 3, "#5c2a0a", 0.4)
    ctx.save()  # чашка остывшего чая сверху
    ctx.translate(820, 620)
    shadow(ctx, 10, 100, 160, 30, 0.4)
    ctx.arc(0, 0, 150, 0, TAU)
    fill(ctx, "#f5f5f4")
    ctx.arc(0, 0, 120, 0, TAU)
    fill(ctx, "#92400e")
    ell(ctx, -40, -40, 40, 20)
    fill(ctx, "#ffffff", 0.2)
    rr(ctx, 140, -30, 80, 60, 30)
    ctx.set_line_width(20)
    src(ctx, "#f5f5f4")
    ctx.stroke()
    line(ctx, 60, -60, 260, -260, 3, "#e7e5e4")  # ниточка пакетика
    rr(ctx, 250, -310, 60, 70, 4)
    fill(ctx, "#facc15")
    ctx.restore()
    ctx.save()  # тарелка с печеньем и крошки
    ctx.translate(230, 520)
    ctx.arc(0, 0, 170, 0, TAU)
    fill(ctx, "#e0f2fe")
    ctx.arc(0, 0, 130, 0, TAU)
    fill(ctx, "#f0f9ff")
    for k in range(4):
        ctx.arc(-60 + (k % 2) * 110, -40 + (k // 2) * 90, 55, 0, TAU)
        fill(ctx, "#d97706")
        for j in range(5):
            ctx.arc(-60 + (k % 2) * 110 + math.cos(j * 1.3) * 28, -40 + (k // 2) * 90 + math.sin(j * 1.3) * 28, 6, 0, TAU)
            fill(ctx, "#451a03")
    ctx.restore()
    r = random.Random(2)
    for k in range(30):
        ctx.arc(r.uniform(100, 600), r.uniform(650, 900), r.uniform(3, 8), 0, TAU)
        fill(ctx, "#d97706")
    rr(ctx, 600, 1500, 300, 30, 15)  # ложка
    fill(ctx, "#cbd5e1")
    ell(ctx, 940, 1515, 60, 36)
    fill(ctx, "#cbd5e1")
    tr = 1.0 if t > EV["shake"] else 0.3
    ticket(ctx, 540 + math.sin(t * 37) * 6 * tr, 1150 + math.sin(t * 31) * 6 * tr, 1.3, t, rot=-0.05, glow_k=0.6)
    for side in (-1, 1):  # трясущиеся руки
        hx = 540 + side * 470 + math.sin(t * 40 + side) * 10 * tr
        line(ctx, hx + side * 400, 1900, hx, 1350, 130, TEAL[0])
        ctx.arc(hx, 1330, 80, 0, TAU)
        fill(ctx, HEAD)
    ctx.restore()


def s2_silence(ctx, t, u, D):
    po, ca = EV["post"], EV["call"]
    ctx.save()
    cam(ctx, t, 540, 1150, 1.0, shake=0.2)
    kitchen(ctx, t, lamp=False)
    ctx.restore()
    msgs = [(0, "Тётя Галя: как дела? давно не звонил", 1.0), (0, "Брат: скинь 500 до зп", 1.0),
            (1, typed("Я ВЫИГРАЛ ПОЛМИЛЛИАРДА!!!", t, TL.shots[2][0] + 0.2, po), 1.0 if t < po + 0.3 else 0.3)]
    hands_phone(ctx, t, chat_screen(msgs, t, header="Семья", typing=True), tremble=0.6, sc=0.8, cy=1050, hood=TEAL)
    if t > po + 0.2:
        crossmark(ctx, 700, 1120, 2.0)
        rr(ctx, 260, 1340, 560, 90, 30)
        fill(ctx, "#dc2626")
        text(ctx, "УДАЛИТЬ ЧЕРНОВИК", 540, 1385, 42, "#ffffff")
    if t > ca:
        a = seg(t, ca, ca + 0.3)
        rr(ctx, 200, 1440, 680, 100, 40)
        fill(ctx, "#0b0b12", 0.9 * a)
        text(ctx, "ВХОДЯЩИЙ: МАМА — ПОТОМ", 540, 1490, 38, "#fca5a5", alpha=a)
    step_card(ctx, t, EV["steps"][0], 1, "МОЛЧИ\nНИКОМУ НИ СЛОВА")


def lawyer_office(ctx, t):
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#f5f5f4"), (1, "#e7e5e4")])
    for k in range(-2, 6):
        rr(ctx, k * 300, 0, 14, 1400, 0)
        fill(ctx, "#d6d3d1")
    for k in range(3):
        bookshelf(ctx, -200 + k * 520, 300, 460, rows=3, seed=k + 3)
    for k in range(10):  # папки на полке
        rr(ctx, 1500 + k * 46, 380, 40, 160, 4)
        fill(ctx, ("#1d4ed8", "#dc2626", "#16a34a", "#ca8a04")[k % 4])
    rr(ctx, 400, 700, 280, 200, 8)  # диплом
    fill(ctx, "#78350f")
    rr(ctx, 420, 720, 240, 160, 4)
    fill(ctx, "#fffbeb")
    text(ctx, "ДИПЛОМ", 540, 790, 34, "#78350f")
    ctx.rectangle(-1200, 1450, 3600, 1600)
    fill(ctx, "#57534e")
    rug(ctx, 540, 1700, 700, 120, "#7f1d1d")


def s3_lawyer(ctx, t, u, D):
    la, ad = EV["lawyer"], EV["advisor"]
    ctx.save()
    cam(ctx, t, 540, 1250, 0.9, shake=0.15)
    lawyer_office(ctx, t)
    p = Npc(random.Random(31), 250, 1520, 1.0, 1)
    p.style, p.shirt, p.collar, p.glasses, p.item, p.beard = "short", "#1f2937", "shirt", True, "none", True
    npc(ctx, p, t, walking=False, alpha=seg(t, la - 0.3, la))
    q = Npc(random.Random(32), 830, 1520, 1.0, -1)
    q.style, q.shirt, q.collar, q.item, q.earrings = "bun", "#7c3aed", "shirt", "none", True
    npc(ctx, q, t, walking=False, alpha=seg(t, ad - 0.3, ad))
    rr(ctx, -100, 1500, 1280, 50, 8)  # стол переговоров
    fill(ctx, "#78350f")
    rr(ctx, -100, 1550, 1280, 300, 0)
    fill(ctx, "#5c2a0a")
    for k in range(3):  # договоры
        rr(ctx, 320 + k * 40, 1440 - k * 6, 200, 60, 4)
        fill(ctx, "#ffffff")
    ctx.arc(160, 1470, 40, 0, TAU)  # печать
    fill(ctx, "#1d4ed8")
    rr(ctx, 140, 1390, 40, 60, 10)
    fill(ctx, "#111827")
    rr(ctx, 700, 1360, 240, 140, 8)  # ноутбук с графиком
    fill(ctx, "#111827")
    for k in range(6):
        rr(ctx, 720 + k * 36, 1480 - (k + 2) * 14, 26, (k + 2) * 14, 3)
        fill(ctx, "#22c55e")
    rr(ctx, 340, 1520, 400, 40, 6)
    fill(ctx, "#fef3c7")
    text(ctx, "ЮРИСТ • СОВЕТНИК", 540, 1541, 24, "#78350f")
    lucky(ctx, 60, 2250, 1.0, emo("calm"), t, arms="down", back=True, legs=False)
    ctx.restore()
    step_card(ctx, t, EV["steps"][1], 2, "ЮРИСТ\nИ ФИН. СОВЕТНИК")


def s4_debts(ctx, t, u, D):
    db = EV["debts"]
    ctx.save()
    if t < db[2] - 0.2:
        cam(ctx, t, 540, 1150, 0.95, shake=0.15)
        bank_hall(ctx, t)
        atm(ctx, 950, 1700, 1.4, t, receipt=seg(t, db[0], db[0] + 1))
        lucky(ctx, 520, 2100, 1.0, emo("happy"), t, arms="relax", back=False)
    else:
        cam(ctx, t, 540, 1250, 0.9, shake=0.15)
        day_city(ctx, t)
        ctx.save()  # дом родителей
        rr(ctx, 160, 700, 760, 700, 10)
        fill(ctx, "#fde68a")
        ctx.move_to(100, 720)
        ctx.line_to(540, 400)
        ctx.line_to(980, 720)
        fill(ctx, "#b91c1c")
        for k in range(2):
            rr(ctx, 230 + k * 450, 820, 180, 180, 6)
            fill(ctx, "#bae6fd")
            curtain(ctx, 230 + k * 450, 820, 90, 180, "#f472b6", t, 1)
        rr(ctx, 470, 1050, 140, 350, 6)
        fill(ctx, "#7c2d12")
        ctx.restore()
        for k, sd in enumerate((-1, 1)):
            p = Npc(random.Random(50 + k), 540 + sd * 260, 1750, 1.0, -sd)
            p.hair, p.style, p.item = "#d4d4d8", ("bald", "bun")[k], "none"
            p.glasses = True
            npc(ctx, p, t, walking=False, clap=True, grin=0.6)
        ctx.save()  # ключи с бантиком
        ctx.translate(540, 1300)
        ctx.rotate(math.sin(t * 3) * 0.2)
        line(ctx, 0, -120, 0, 0, 4, "#9ca3af")
        ctx.arc(0, 20, 30, 0, TAU)
        ctx.set_line_width(8)
        src(ctx, "#facc15")
        ctx.stroke()
        rr(ctx, -8, 50, 16, 80, 4)
        fill(ctx, "#facc15")
        for sd in (-1, 1):
            ell(ctx, sd * 40, -120, 40, 22)
            fill(ctx, "#dc2626")
        ctx.restore()
    ctx.restore()
    # список долгов
    rr(ctx, 120, 560, 840, 280, 30)
    fill(ctx, "#0b0b12", 0.85)
    for k, (nm, sm) in enumerate((("ИПОТЕКА", "8 400 000"), ("КРЕДИТЫ", "1 200 000"), ("ДОЛГ РОДИТЕЛЕЙ", "3 100 000"))):
        y = 620 + k * 80
        text(ctx, nm, 160, y, 40, "#ffffff", align="left")
        text(ctx, sm, 920, y, 40, "#fca5a5", align="right")
        if t > db[k]:
            line(ctx, 150, y, 150 + 780 * seg(t, db[k], db[k] + 0.3), y, 8, "#22c55e")
    step_card(ctx, t, EV["steps"][2], 3, "ЗАКРОЙ\nВСЕ ДОЛГИ")


def s5_cushion(ctx, t, u, D):
    de, ca = EV["deposit"], EV["car"]
    ctx.save()
    cam(ctx, t, 540, 1250, 0.9, shake=0.15)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#0f172a"), (1, "#1e293b")])
    for k in range(-3, 8):  # ячейки хранилища
        for j in range(5):
            rr(ctx, k * 200, 300 + j * 180, 180, 160, 10)
            fill(ctx, "#475569")
            ctx.arc(k * 200 + 140, 380 + j * 180, 14, 0, TAU)
            fill(ctx, "#cbd5e1")
            text(ctx, str(100 + k * 5 + j), k * 200 + 50, 330 + j * 180, 22, "#94a3b8")
    ctx.rectangle(-1200, 1250, 3600, 1600)
    fill(ctx, "#334155")
    for k in range(7):  # пачки денег растут
        money_stack(ctx, 160 + k * 130, 1500, 1.0, int(2 + 10 * seg(t, de - 0.5 + k * 0.1, de + 0.7)))
    parked_car(ctx, 860, 1900, 1.0, "#dc2626")
    if t > ca:
        crossmark(ctx, 860, 1800, 2.6)
    lucky(ctx, 300, 2050, 1.0, emo("determined"), t, arms="relax")
    ctx.restore()
    # круговая диаграмма
    ctx.save()
    ctx.translate(540, 720)
    k = ease(seg(t, de - 0.5, de + 0.5))
    ctx.move_to(0, 0)
    ctx.arc(0, 0, 130, -math.pi / 2, -math.pi / 2 + TAU * 0.8 * k)
    fill(ctx, "#22c55e")
    ctx.move_to(0, 0)
    ctx.arc(0, 0, 130, -math.pi / 2 + TAU * 0.8 * k, -math.pi / 2 + TAU * k)
    fill(ctx, "#f59e0b")
    ctx.arc(0, 0, 60, 0, TAU)
    fill(ctx, "#0f172a")
    text(ctx, "80%", 0, 0, 40, "#ffffff")
    text(ctx, "ВКЛАДЫ", 260, -20, 40, "#22c55e", "#000", 6)
    ctx.restore()
    step_card(ctx, t, EV["steps"][3], 4, "ПОДУШКА\nНЕ СПОРТКАР")


def s6_same(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(400, 700, seg(u, 0, D)), 1250, 0.85, shake=0.15)
    office(ctx, t)
    coworkers(ctx, t, 8, 4, 1350)
    lucky(ctx, 560, 2150, 1.0, emo("calm"), t, arms="relax")
    office_desk(ctx, 560, 2000, 0.9, t, 9)
    text(ctx, "1 ГОД", 1600, 560, 60, "#dc2626")
    ctx.restore()
    step_card(ctx, t, EV["steps"][4], 5, "ЖИЗНЬ НЕ МЕНЯЙ\nХОТЯ БЫ ГОД")


def ic_lock(c, x, y, col, a):
    rr(c, x - 22, y - 4, 44, 34, 6)
    fill(c, col, a)
    c.arc(x, y - 6, 15, math.pi, TAU)
    c.set_line_width(6)
    src(c, col, a)
    c.stroke()


def ic_bank(c, x, y, col, a):
    c.move_to(x - 28, y - 10)
    c.line_to(x, y - 28)
    c.line_to(x + 28, y - 10)
    fill(c, col, a)
    for k in range(3):
        rr(c, x - 22 + k * 18, y - 8, 8, 28, 2)
        fill(c, col, a)


def ic_gift(c, x, y, col, a):
    rr(c, x - 24, y - 14, 48, 40, 4)
    fill(c, col, a)
    line(c, x, y - 14, x, y + 26, 5, "#0b0b12", a)
    for sd in (-1, 1):
        ell(c, x + sd * 10, y - 22, 12, 8)
        fill(c, col, a)


def ic_me(c, x, y, col, a):
    c.arc(x, y - 10, 14, 0, TAU)
    fill(c, col, a)
    rr(c, x - 20, y + 6, 40, 22, 10)
    fill(c, col, a)


def ic_post(c, x, y, col, a):
    rr(c, x - 24, y - 24, 48, 48, 12)
    c.set_line_width(5)
    src(c, col, a)
    c.stroke()
    c.arc(x, y, 10, 0, TAU)
    c.set_line_width(5)
    c.stroke()


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА ВЫИГРЫША", [
        ("ДОЛГИ", "ипотека, кредиты, родители", 0.0, "#22c55e", "0", ic_lock),
        ("ВКЛАД", "400 млн из 500", 0.8, "#38bdf8", "400", ic_bank),
        ("БЛИЗКИМ", "50 млн подарков", 0.1, "#f472b6", "50", ic_gift),
        ("СЕБЕ", "10 млн", 0.02, GOLD, "10", ic_me),
        ("ПОСТЫ", "в соцсетях", 0.0, "#ef4444", "0", ic_post)], EV["tally"])


def s8_done(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1250, 0.95, shake=0.15)
    kitchen(ctx, t)
    rr(ctx, -200, 1280, 1500, 40, 8)
    fill(ctx, "#92400e")
    coffee_cup(ctx, 300, 1280, 0.3, t, heart=True)
    lucky(ctx, 600, 1950, 1.0, emo("happy"), t, arms="relax")
    ctx.restore()
    k = back_out(seg(t, EV["right"] - 0.4, EV["right"]))
    if k > 0:
        ctx.save()
        ctx.translate(540, 760)
        ctx.scale(max(0.02, k), max(0.02, k))
        text(ctx, "ЖИЗНЬ ЦЕЛА", 0, 0, 100, "#22c55e", "#000", 14, shadow=True)
        ctx.restore()


def call_screen(t, who="ЛОТЕРЕЯ «ЛОТО-МИЛЛИОН»"):
    def f(c, x, y, w, h):
        vgrad(c, x, y, w, h, [(0, "#14532d"), (1, "#052e16")])
        text(c, "входящий вызов", x + w / 2, y + 200, 36, "#bbf7d0")
        rr(c, x + w / 2 - 110, y + 280, 220, 220, 110)
        fill(c, "#dc2626")
        text(c, "ЛОТО", x + w / 2, y + 390, 56, "#ffffff")
        rows = who.split(" ")
        for i, rw in enumerate(rows):
            text(c, rw, x + w / 2, y + 580 + i * 60, 46, "#ffffff")
        k = (t * 1.5) % 1
        for sd, col in ((-1, "#ef4444"), (1, "#22c55e")):
            c.arc(x + w / 2 + sd * 150, y + h - 180, 70 + 10 * k * (sd > 0), 0, TAU)
            fill(c, col)
    return f


def s9_call(ctx, t, u, D):
    ri = EV["ring"]
    ctx.save()
    cam(ctx, t, 600, 1250, 0.9, shake=0.15)
    office(ctx, t)
    coworkers(ctx, t, 8, 4, 1350)
    lucky(ctx, 560, 2150, 1.0, emo("worry") if t > ri else emo("calm"), t, arms="phone" if t > ri else "relax")
    ctx.restore()
    text(ctx, "ЧЕРЕЗ МЕСЯЦ", 540, 360, 70, "#ffffff", "#000", 10, alpha=seg(t, TL.shots[9][0] + 0.3, TL.shots[9][0] + 0.6))
    if t > ri - 0.3:
        s = ease(seg(t, ri - 0.3, ri + 0.2))
        phone_body(ctx, 540, lerp(2600, 1000, s), 420, 840, call_screen(t))


def s10_only(ctx, t, u, D):
    on, em = EV["only"], EV["empty"]
    ctx.save()
    cam(ctx, t, 540, 1000, 1.0, shake=0.2)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1e1b4b"), (1, "#020617")])
    lotto_drum(ctx, 540, 1500, 1.1, t, 0.4)
    rr(ctx, 120, 420, 840, 720, 30)
    fill(ctx, "#0b0b12", 0.9)
    text(ctx, "ИСТОРИЯ ТИРАЖЕЙ", 540, 480, 44, "#c7d2fe")
    n = int(10 * seg(t, TL.shots[10][0], em))
    for i in range(10):
        y = 550 + i * 56
        if i > n:
            break
        nm = 1307 - 9 + i
        win = (nm == 1307)
        text(ctx, f"ТИРАЖ {nm}", 170, y, 34, "#ffffff" if win else "#94a3b8", align="left")
        text(ctx, "1 ПОБЕДИТЕЛЬ" if win else "0 ПОБЕДИТЕЛЕЙ", 910, y, 34, GOLD if win else "#64748b", align="right")
        if win and t > on:
            rr(ctx, 140, y - 26, 800, 52, 12)
            ctx.set_line_width(4)
            src(ctx, GOLD)
            ctx.stroke()
    ctx.restore()
    if t > em:
        text(ctx, "ВСЕ ОСТАЛЬНЫЕ — ПУСТЫЕ", 540, 1260, 54, "#ef4444", "#000", 8, alpha=seg(t, em, em + 0.3))


def s11_back(ctx, t, u, D):
    nm, dt = EV["name"], EV["date"]
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(1.0, 1.15, seg(u, 0, D)), shake=0.2)
    rr(ctx, -800, -800, 2700, 3600, 0)
    lgrad(ctx, 0, -800, 0, 2800, [(0, "#78350f"), (1, "#451a03")])
    ctx.fill()
    ticket(ctx, 540, 950, 1.4, t, back=True, rot=0.03)
    # лупа
    mx = lerp(900, 560, ease(seg(t, EV["back"], nm)))
    my = lerp(1500, 1000, ease(seg(t, EV["back"], nm)))
    ctx.save()
    ctx.arc(mx, my, 230, 0, TAU)
    ctx.clip()
    src(ctx, "#fffbeb")
    ctx.paint()
    a1 = seg(t, nm - 0.3, nm)
    text(ctx, "ПОБЕДИТЕЛЬ:", mx, my - 60, 46, "#57534e", alpha=a1)
    text(ctx, "ТЫ", mx, my + 10, 90, "#7f1d1d", alpha=a1)
    a2 = seg(t, dt - 0.2, dt + 0.2)
    text(ctx, "печать: 14.03.2025", mx, my + 100, 30, "#b91c1c", alpha=a2)
    ctx.restore()
    ctx.arc(mx, my, 230, 0, TAU)
    ctx.set_line_width(30)
    src(ctx, "#1f2937")
    ctx.stroke()
    ctx.arc(mx, my, 230, 0, TAU)
    ctx.set_line_width(8)
    src(ctx, "#9ca3af")
    ctx.stroke()
    line(ctx, mx + 160, my + 160, mx + 380, my + 420, 50, "#1f2937")
    ctx.restore()
    if t > dt + 0.4:
        a = seg(t, dt + 0.4, dt + 0.7)
        rr(ctx, 160, 1370, 760, 100, 30)
        fill(ctx, "#0b0b12", 0.9 * a)
        text(ctx, "КУПЛЕН: 14.03.2026", 540, 1420, 46, "#ffffff", alpha=a)


def s12_kiosk(ctx, t, u, D):
    ki = EV["kiosk"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        ctx.save()
        cam(ctx, t, 540, lerp(1200, 1000, seg(u, 0, ec)), lerp(0.85, 1.25, ease(seg(u, 0, ec))), shake=0.2)
        night_street(ctx, t)
        kiosk(ctx, 540, 1750, t, rain=False, seller_grin=seg(t, ki - 0.5, ki))
        ctx.restore()
        r = random.Random(int(t * 20))
        for i in range(90):
            xx, yy = r.uniform(-100, 1200), r.uniform(0, 2000)
            line(ctx, xx, yy, xx - 10, yy + 46, 2, "#bfdbfe", 0.5)
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
        text(ctx, "Кто выбрал тебя?", 0, 180, 70, GOLD)
    ctx.restore()


def night_street(ctx, t):
    vgrad(ctx, -1500, -1200, 4000, 2600, [(0, "#0b1022"), (1, "#1e293b")])
    skyline(ctx, 3, -1400, 2600, 1300, 400, 900, "#111827", "#fde68a", 0.2, wmin=150, wmax=260)
    ctx.rectangle(-1500, 1300, 4000, 1600)
    fill(ctx, "#1f2937")
    for i in range(-6, 12):  # лужи с отражениями
        ell(ctx, i * 300 + 80, 1850 + (i % 3) * 60, 120, 18)
        fill(ctx, "#334155")
    for x in (-500, 1500):
        lamp_post(ctx, x, 1320, 600, on=True)
        glow(ctx, x + 125, 720, 260, "#fde68a", 0.35)


SCENES = [s0_hook, s1_ticket, s2_silence, s3_lawyer, s4_debts, s5_cushion, s6_same, s7_tally, s8_done, s9_call,
          s10_only, s11_back, s12_kiosk]
LABELS = {10: "ЧЕРЕЗ МЕСЯЦ", 11: "ЧЕРЕЗ МЕСЯЦ", 12: "ЧЕРЕЗ МЕСЯЦ"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("пятьсот", "миллионов", "рублей"), "500 000 000 руб."), (("четыреста", "миллионов"), "400 млн"),
         (("пятьдесят",), "50 млн"), (("десять",), "10 млн"), (("ноль",), "0")]


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
        text(ctx, "500 МИЛЛИОНОВ", 0, 10, 110, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -330, 90, 660, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "В ЛОТЕРЕЮ?", 0, 155, 100, "#ffffff")
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
