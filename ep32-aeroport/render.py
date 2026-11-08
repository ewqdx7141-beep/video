"""Серия 32 «Сутки в аэропорту» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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










# ================================================================== СУТКИ В АЭРОПОРТУ
SKY = ("#0284c7", "#075985")
sys.path.insert(0, os.path.join(ROOT, "..", "lib"))
from aviation import airliner  # noqa: E402


def traveler(ctx, x, y, sc, e, t, arms="relax", look=(0, 0), walk=None, back=False, legs=True, tremble=0.0, item=None,
             pack=True):
    if pack and not back:
        rr(ctx, x - 92 * sc, y - (380 if legs else 210) * sc, 184 * sc, 200 * sc, 30 * sc)
        fill(ctx, "#334155")
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, walk=walk, back=back, legs=legs, tremble=tremble,
         rim="#bae6fd", rim_a=0.6, hood=SKY, hand_item=item)
    if pack and back:
        rr(ctx, x - 92 * sc, y - (380 if legs else 210) * sc, 184 * sc, 200 * sc, 30 * sc)
        fill(ctx, "#334155")
        rr(ctx, x - 60 * sc, y - (300 if legs else 130) * sc, 120 * sc, 60 * sc, 14 * sc)
        fill(ctx, "#475569")


def board(ctx, x, y, t, mode="cancel", k=1.0, home=0.0, rows_n=7):
    rr(ctx, x, y, 900, 140 + rows_n * 72, 16)
    fill(ctx, "#0b0b12")
    text(ctx, "ВЫЛЕТ", x + 40, y + 50, 40, "#facc15", align="left")
    hh = int(19 + t / 3) % 24
    text(ctx, f"{hh:02d}:{int(t * 7) % 60:02d}", x + 860, y + 50, 40, "#facc15", align="right")
    rows = (("19:10", "СОЧИ", "S7 1043"), ("19:35", "КАЗАНЬ", "SU 1270"), ("20:00", "МИНСК", "B2 954"),
            ("20:20", "ТБИЛИСИ", "A9 152"), ("20:45", "АСТАНА", "KC 980"), ("21:05", "ЕРЕВАН", "FV 6611"),
            ("21:30", "ДОМОЙ", "—"))
    for i, (tm, city, fl) in enumerate(rows[:rows_n]):
        yy = y + 120 + i * 72
        mine = (i == 2)
        if mine:
            rr(ctx, x + 10, yy - 32, 880, 64, 8)
            fill(ctx, "#1e3a8a")
        text(ctx, tm, x + 40, yy, 34, "#e5e7eb", align="left")
        nm = city
        if mine and home > 0:
            nm = "ДОМОЙ" if home > 0.5 else "██████"
        text(ctx, nm, x + 190, yy, 34, "#e5e7eb" if not (mine and home > 0.5) else "#facc15", align="left")
        if mode == "cancel":
            st, col = ("ОТМЕНЁН", "#ef4444") if (mine and k > 0.5) else ("ПО РАСПИС.", "#22c55e")
        elif mode == "delay":
            on = (t * 2) % 1 < 0.6
            st, col = ("ЗАДЕРЖАН", "#f59e0b") if on or not mine else ("", "#f59e0b")
            if not mine:
                st = ("ЗАДЕРЖАН", "ОТМЕНЁН", "ЗАДЕРЖАН")[i % 3]
                col = "#f59e0b" if st == "ЗАДЕРЖАН" else "#ef4444"
        else:  # boarding
            st, col = ("ПОСАДКА", "#22c55e") if mine else ("ОТМЕНЁН", "#6b7280")
        text(ctx, st, x + 860, yy, 30, col, align="right")


def terminal(ctx, t, night=0.4, x0=-1200, x1=2400, planes=True, ground_y=1700, empty=False):
    vgrad(ctx, x0 - 600, -800, x1 - x0 + 1200, 3600, [(0, "#e2e8f0"), (1, "#cbd5e1")])
    ctx.save()  # панорамные окна с перроном
    rr(ctx, x0 - 600, 200, x1 - x0 + 1200, 900, 0)
    ctx.clip()
    vgrad(ctx, x0 - 600, 200, x1 - x0 + 1200, 900, [(0, mixh("#7dd3fc", "#0b1022", night)), (1, mixh("#e0f2fe", "#1e293b", night))])
    ctx.rectangle(x0 - 600, 850, x1 - x0 + 1200, 250)
    fill(ctx, mixh("#64748b", "#1f2937", night))
    for k in range(int((x1 - x0) / 120) + 10):
        ctx.arc(x0 - 600 + k * 120, 880, 6, 0, TAU)
        fill(ctx, "#facc15" if k % 2 else "#60a5fa")
    if planes:
        airliner(ctx, x0 + 600, 820, 0.35, t, lit=night > 0.3)
        airliner(ctx, x0 + 2000, 840, 0.3, t, lit=night > 0.3, livery="#b91c1c")
    ctx.restore()
    for k in range(int((x1 - x0) / 300) + 6):  # рамы окон
        line(ctx, x0 - 600 + k * 300, 200, x0 - 600 + k * 300, 1100, 12, "#94a3b8")
    line(ctx, x0 - 600, 650, x1 + 600, 650, 8, "#94a3b8")
    for k in range(int((x1 - x0) / 400) + 4):  # светильники
        rr(ctx, x0 - 600 + k * 400, 120, 260, 30, 10)
        fill(ctx, "#ffffff")
    ctx.rectangle(x0 - 600, 1100, x1 - x0 + 1200, ground_y - 1100)
    fill(ctx, "#f1f5f9")
    ctx.rectangle(x0 - 600, ground_y, x1 - x0 + 1200, 1400)
    fill(ctx, "#cbd5e1")
    for k in range(int((x1 - x0) / 200) + 10):
        line(ctx, x0 - 600 + k * 200, ground_y, x0 - 600 + k * 200 - 260, ground_y + 1200, 2, "#94a3b8", 0.5)
    rr(ctx, x0 - 600, ground_y + 120, x1 - x0 + 1200, 140, 0)  # ковровая полоса
    fill(ctx, "#1e3a8a", 0.25)


def seat_row(ctx, x, y, n, t, seed=1, people=True, sleepers=0.5, s=1.0):
    r = random.Random(seed)
    for i in range(n):
        sx = x + i * 150 * s
        rr(ctx, sx, y - 90 * s, 130 * s, 90 * s, 14 * s)
        fill(ctx, "#475569")
        rr(ctx, sx, y - 10 * s, 130 * s, 26 * s, 8 * s)
        fill(ctx, "#334155")
    line(ctx, x - 10, y + 16 * s, x + n * 150 * s, y + 16 * s, 8 * s, "#94a3b8")
    for k in (0, n - 1):
        line(ctx, x + k * 150 * s + 60 * s, y + 16 * s, x + k * 150 * s + 60 * s, y + 80 * s, 8 * s, "#94a3b8")
    if people:
        for i in range(n):
            if r.random() < 0.8:
                p = Npc(r, x + i * 150 * s + 65 * s, y + 50 * s, 0.75 * s, r.choice((-1, 1)))
                p.item = r.choice(("phone", "none", "coffee"))
                p.neck_pillow = r.random() < 0.3
                npc(ctx, p, t, walking=False, sleep=r.random() < sleepers)


def suitcase2(ctx, x, y, s, col):
    rr(ctx, x - 60 * s, y - 160 * s, 120 * s, 160 * s, 14 * s)
    fill(ctx, col)
    for k in range(3):
        line(ctx, x - 40 * s + k * 40 * s, y - 150 * s, x - 40 * s + k * 40 * s, y - 10 * s, 3 * s, shade(col, 0.7))
    line(ctx, x - 30 * s, y - 160 * s, x - 30 * s, y - 230 * s, 6 * s, "#475569")
    line(ctx, x + 30 * s, y - 160 * s, x + 30 * s, y - 230 * s, 6 * s, "#475569")
    line(ctx, x - 30 * s, y - 230 * s, x + 30 * s, y - 230 * s, 8 * s, "#475569")
    for sd in (-1, 1):
        ctx.arc(x + sd * 40 * s, y + 6 * s, 8 * s, 0, TAU)
        fill(ctx, "#111")


def gate_sign(ctx, x, y, num="47"):
    rr(ctx, x, y, 320, 130, 12)
    fill(ctx, "#facc15")
    text(ctx, "ВЫХОД", x + 110, y + 65, 40, "#111827")
    rr(ctx, x + 200, y + 15, 100, 100, 10)
    fill(ctx, "#111827")
    text(ctx, num, x + 250, y + 65, 52, "#facc15")


def mixh(c1, c2, k):
    a, b = hexc(c1), hexc(c2)
    return "#%02x%02x%02x" % tuple(int(255 * (a[i] + (b[i] - a[i]) * clamp(k))) for i in range(3))


def attendant(ctx, x, y, sc, t, grin=0.6, scan=0.0):
    p = Npc(random.Random(131), x, y, sc, -1)
    p.shirt, p.style, p.hair, p.item, p.uniform = "#1e3a8a", "bun", "#2b1d14", "none", "stew"
    npc(ctx, p, t, walking=False, grin=grin, stare=0.3)
    if scan:
        rr(ctx, x - 140 * sc, y - 270 * sc, 70 * sc, 40 * sc, 8 * sc)
        fill(ctx, "#111827")
        line(ctx, x - 200 * sc, y - 250 * sc, x - 140 * sc, y - 250 * sc, 4 * sc, "#ef4444", scan)


# ================================================================== СЦЕНЫ
def s0_hook(ctx, t, u, D):
    ca, h = EV["cancel"], EV["h24"]
    ctx.save()
    cam(ctx, t, 540, 1200, lerp(0.75, 0.85, seg(u, 0, D)), shake=0.15)
    terminal(ctx, t, night=0.3)
    board(ctx, 90, 300, t, "cancel", seg(t, ca - 0.2, ca + 0.2), rows_n=5)
    seat_row(ctx, -600, 1650, 6, t, 1, sleepers=0.2)
    suitcase2(ctx, 1150, 1950, 1.0, "#ef4444")
    traveler(ctx, 560, 2050, 1.0, emo("shock") if t > ca else emo("calm"), t, arms="shock" if t > ca else "relax")
    ctx.restore()
    if t > h:
        a = seg(t, h, h + 0.3)
        rr(ctx, 340, 930, 400, 140, 30)
        fill(ctx, "#0b0b12", 0.9 * a)
        text(ctx, f"{23 - int((t - h) * 2) % 24:02d}:59:{59 - int(t * 7) % 60:02d}", 540, 1000, 60, "#ef4444", alpha=a)


def s1_delay(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(400, 700, seg(u, 0, D)), 1250, 0.7, shake=0.15)
    terminal(ctx, t, night=0.6)
    board(ctx, 90, 280, t, "delay", 1.0, rows_n=6)
    for row in range(2):
        seat_row(ctx, -900 + row * 80, 1650 + row * 250, 12, t, 3 + row, sleepers=0.6)
    for k in range(5):
        suitcase2(ctx, -700 + k * 520, 2200, 0.9, ("#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#a855f7")[k])
    traveler(ctx, 900, 2350, 1.0, emo("worry"), t, arms="relax", look=(-0.6, -0.4))
    ctx.restore()


def s2_spot(ctx, t, u, D):
    so = EV["socket"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.85, shake=0.1)
    terminal(ctx, t, night=0.6, x0=-800, x1=2000)
    gate_sign(ctx, 600, 1150, "47")
    seat_row(ctx, -200, 1750, 4, t, 9, people=False)
    rr(ctx, 950, 1550, 80, 110, 10)  # розетка
    fill(ctx, "#f8fafc")
    for sd in (-1, 1):
        rr(ctx, 990 + sd * 14 - 4, 1590, 8, 26, 2)
        fill(ctx, "#111827")
    if t > so:
        ctx.move_to(990, 1610)  # провод зарядки
        ctx.curve_to(900, 1800, 700, 1700, 560, 1760)
        ctx.set_line_width(8)
        src(ctx, "#f8fafc")
        ctx.stroke()
        glow(ctx, 990, 1600, 80, "#22c55e", 0.6)
    traveler(ctx, 340, 1950, 1.0, emo("happy"), t, arms="phone", legs=True)
    ctx.restore()
    step_card(ctx, t, EV["steps"][0], 1, "МЕСТО\nУГОЛ + РОЗЕТКА")


def s3_food(ctx, t, u, D):
    fo, fc = EV["fountain"], EV["foodcourt"]
    ctx.save()
    cam(ctx, t, 540 if t < fc else 1700, 1300, 0.85, shake=0.1)
    terminal(ctx, t, night=0.5, x0=-800, x1=3000, planes=False)
    rr(ctx, 200, 1300, 180, 400, 16)  # фонтанчик
    fill(ctx, "#94a3b8")
    rr(ctx, 170, 1280, 240, 60, 20)
    fill(ctx, "#cbd5e1")
    if t > fo:
        ctx.arc(330, 1280, 60, math.pi * 1.1, math.pi * 1.6)
        ctx.set_line_width(8)
        src(ctx, "#38bdf8")
        ctx.stroke()
    rr(ctx, 600, 1250, 260, 90, 10)
    fill(ctx, "#0ea5e9")
    text(ctx, "ПИТЬЕВАЯ ВОДА", 730, 1295, 26, "#ffffff")
    rr(ctx, 1100, 900, 600, 120, 10)  # кафе у входа — дорого
    fill(ctx, "#7c2d12")
    text(ctx, "КОФЕ 490", 1400, 960, 50, "#fef3c7")
    crossmark(ctx, 1400, 1150, 2.0)
    for k in range(3):  # фудкорт у служебной зоны
        rr(ctx, 1700 + k * 360, 950, 320, 300, 10)
        fill(ctx, ("#16a34a", "#ea580c", "#0891b2")[k])
        text(ctx, ("ЩИ", "ПЛОВ", "БЛИНЫ")[k], 1860 + k * 360, 1010, 46, "#ffffff")
        text(ctx, ("190", "250", "160")[k], 1860 + k * 360, 1090, 40, "#fef08a")
    for k in range(4):  # столики с подносами
        rr(ctx, 1700 + k * 280, 1600, 220, 30, 6)
        fill(ctx, "#a8a29e")
        rr(ctx, 1740 + k * 280, 1570, 140, 30, 6)
        fill(ctx, "#f97316")
    rr(ctx, 2800, 1000, 220, 120, 8)
    fill(ctx, "#475569")
    text(ctx, "СЛУЖЕБНЫЙ", 2910, 1060, 26, "#ffffff")
    traveler(ctx, 560 if t < fc else 1900, 1950, 1.0, emo("calm"), t, arms="relax",
             item=(lambda c, x, y: (rr(c, x - 20, y - 30, 40, 70, 10), fill(c, "#7dd3fc"))))
    ctx.restore()
    step_card(ctx, t, EV["steps"][1], 2, "ЕДА\nНЕ В ПЕРВОМ КАФЕ")


def s4_hygiene(ctx, t, u, D):
    mo, sh = EV["mother"], EV["shower"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.85, shake=0.1)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#f0f9ff"), (1, "#e0f2fe")])
    for i in range(-6, 14):
        for j in range(12):
            rr(ctx, i * 100, j * 100 + 200, 96, 96, 4)
            fill(ctx, "#f8fafc" if (i + j) % 2 else "#e0f2fe")
    for k, (lbl, col, tm) in enumerate((("КОМНАТА МАТЕРИ\nИ РЕБЁНКА", "#ec4899", mo), ("ДУШ • 500", "#0891b2", sh))):
        x = 60 + k * 520
        rr(ctx, x, 920, 440, 760, 14)
        fill(ctx, "#94a3b8")
        rr(ctx, x + 20, 940, 400, 720, 10)
        fill(ctx, "#cbd5e1")
        rr(ctx, x, 740, 440, 160, 14)
        fill(ctx, col, 0.4 + 0.6 * seg(t, tm - 0.3, tm))
        for i_, rw in enumerate(lbl.split("\n")):
            text(ctx, rw, x + 220, 800 + i_ * 50 - (len(lbl.split("\n")) - 1) * 20, 36, "#ffffff")
        ctx.arc(x + 380, 1200, 14, 0, TAU)
        fill(ctx, "#475569")
    ctx.rectangle(-800, 1700, 2700, 1200)
    fill(ctx, "#cbd5e1")
    traveler(ctx, 540, 2050, 1.0, emo("calm"), t, arms="relax",
             item=(lambda c, x, y: (rr(c, x - 30, y - 10, 60, 90, 10), fill(c, "#fde68a"))))
    ctx.restore()
    step_card(ctx, t, EV["steps"][2], 3, "ГИГИЕНА\nДУШ ЗА 500")


def s5_sleep(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1350, 0.9, shake=0.1)
    terminal(ctx, t, night=0.95, x0=-800, x1=2000)
    seat_row(ctx, 0, 1750, 6, t, 11, people=False, s=1.2)
    rr(ctx, 60, 1560, 220, 120, 30)  # рюкзак под головой
    fill(ctx, "#334155")
    ctx.save()  # герой лежит на креслах
    ctx.translate(520, 1600)
    ctx.rotate(-math.pi / 2)
    traveler(ctx, 0, 0, 0.9, emo("sleep"), t, arms="relax", pack=False)
    ctx.restore()
    if t > EV["strap"]:  # ремень на руке
        line(ctx, 330, 1600, 200, 1620, 10, "#111827")
    text(ctx, "z", 120, 1350 - (t * 60) % 120, 60, "#bae6fd", alpha=0.7)
    ctx.restore()
    rr(ctx, 360, 620, 360, 120, 30)
    fill(ctx, "#0b0b12", 0.85)
    text(ctx, f"0{int(2 + seg(u, 0, D) * 2)}:{int(t * 17) % 60:02d}", 540, 680, 64, "#bae6fd")
    step_card(ctx, t, EV["steps"][3], 4, "СОН ПО СМЕНАМ\nРЕМЕНЬ НА РУКУ")


def s6_board(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1150, 0.85, shake=0.1)
    terminal(ctx, t, night=0.7)
    board(ctx, 90, 300, t, "delay", rows_n=6)
    traveler(ctx, 540, 2000, 1.0, emo("determined"), t, arms="relax", back=True)
    ctx.restore()
    for k in range(4):  # часы проверок
        a = seg(t, TL.shots[6][0] + k * 0.6, TL.shots[6][0] + k * 0.6 + 0.3)
        rr(ctx, 120 + k * 220, 1200, 180, 90, 20)
        fill(ctx, "#0b0b12", 0.85 * a)
        text(ctx, f"{2 + k * 2:02d}:00", 210 + k * 220, 1245, 40, "#22c55e", alpha=a)
        checkmark(ctx, 270 + k * 220, 1180, 0.5, OK, a)
    step_card(ctx, t, EV["steps"][4], 5, "ТАБЛО\nКАЖДЫЕ 2 ЧАСА")


def ic_rub(c, x, y, col, a):
    c.arc(x, y, 24, 0, TAU)
    c.set_line_width(5)
    src(c, col, a)
    c.stroke()
    text(c, "Р", x, y + 2, 28, col, alpha=a)


def ic_moon(c, x, y, col, a):
    c.arc(x, y, 22, 0, TAU)
    fill(c, col, a)
    c.arc(x + 10, y - 8, 18, 0, TAU)
    fill(c, "#1e293b", a)


def ic_bat(c, x, y, col, a):
    rr(c, x - 26, y - 14, 46, 28, 5)
    fill(c, col, a)
    rr(c, x + 20, y - 6, 6, 12, 2)
    fill(c, col, a)


def ic_spk(c, x, y, col, a):
    rr(c, x - 22, y - 10, 16, 20, 3)
    fill(c, col, a)
    c.move_to(x - 6, y - 10)
    c.line_to(x + 12, y - 24)
    c.line_to(x + 12, y + 24)
    c.line_to(x - 6, y + 10)
    c.close_path()
    fill(c, col, a)


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА СУТОК", [
        ("ПОТРАЧЕНО", "вода, обед, душ", 0.3, "#facc15", "900 руб.", ic_rub),
        ("СОН", "по сменам", 5 / 8, "#a78bfa", "5 ч", ic_moon),
        ("ЗАРЯД", "розетка у гейта", 1.0, "#22c55e", "100%", ic_bat),
        ("ПРОПУЩЕНО", "объявлений", 0.0, "#ef4444", "0", ic_spk)], EV["tally"])


def s8_board(ctx, t, u, D):
    bo = EV["boarding"]
    ctx.save()
    cam(ctx, t, 540, 1150, 0.85, shake=0.1)
    terminal(ctx, t, night=0.1)
    board(ctx, 90, 300, t, "boarding" if t > bo else "delay", rows_n=6)
    rr(ctx, 420, 1150, 240, 120, 20)  # динамик
    fill(ctx, "#111827")
    for k in range(4):
        line(ctx, 440, 1170 + k * 22, 640, 1170 + k * 22, 5, "#374151")
    traveler(ctx, 540, 2000, 1.0, emo("happy"), t, arms="cheer")
    ctx.restore()


def s9_gate(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(300, 700, seg(u, 0, D)), 1350, 0.75, shake=0.1)
    terminal(ctx, t, night=0.2, planes=False)
    gate_sign(ctx, 700, 1150, "47")
    for row in range(2):
        seat_row(ctx, -900 + row * 80, 1700 + row * 250, 12, t, 3 + row, people=False)
    traveler(ctx, lerp(-200, 700, seg(u, 0, D)), 2350, 1.0, emo("worry"), t, arms="relax",
             walk=t * 6 if u < D * 0.9 else None, look=(0.3, -0.3))
    ctx.restore()
    if t > EV["nobody"]:
        text(ctx, "НИ ОДНОГО ПАССАЖИРА", 540, 700, 60, "#ffffff", "#000", 10, alpha=seg(t, EV["nobody"], EV["nobody"] + 0.3))


def s10_scan(ctx, t, u, D):
    sc_, on = EV["scan"], EV["only"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.9, shake=0.1)
    terminal(ctx, t, night=0.2, planes=False)
    gate_sign(ctx, 360, 900, "47")
    attendant(ctx, 760, 1750, 1.15, t, grin=0.7, scan=1.0 if t > sc_ else 0.0)
    rr(ctx, 520, 1500, 460, 260, 10)  # стойка
    fill(ctx, "#1e3a8a")
    text(ctx, "ПОСАДКА", 750, 1580, 40, "#facc15")
    traveler(ctx, 230, 2050, 1.0, emo("worry"), t, arms="give",
             item=(lambda c, x, y: (rr(c, x - 10, y - 40, 120, 70, 6), fill(c, "#f8fafc"))))
    ctx.restore()
    if t > on:
        a = seg(t, on, on + 0.3)
        rr(ctx, 160, 640, 760, 130, 30)
        fill(ctx, "#ffffff", a)
        text(ctx, "Вы единственный, кто дождался", 540, 705, 40, "#111827", alpha=a)


def s11_plane(ctx, t, u, D):
    nm = EV["nomarks"]
    ctx.save()
    k = ease(seg(t, EV["plane"] - 0.3, nm + 0.6))
    cam(ctx, t, 540, lerp(1100, 800, k), lerp(0.85, 1.1, k), shake=0.1)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#cbd5e1"), (1, "#94a3b8")])
    ctx.save()
    rr(ctx, -100, 300, 1300, 1000, 0)
    ctx.clip()
    vgrad(ctx, -100, 300, 1300, 1000, [(0, "#fde68a"), (1, "#fef3c7")])
    ctx.rectangle(-100, 1050, 1300, 300)
    fill(ctx, "#64748b")
    airliner(ctx, 560, 1000, 0.7, t, lit=False, livery="#f8fafc", marks=False)
    ctx.restore()
    for k2 in range(5):
        line(ctx, -100 + k2 * 320, 300, -100 + k2 * 320, 1300, 14, "#94a3b8")
    traveler(ctx, 540, 2300, 1.2, emo("fear"), t, arms="relax", back=True, legs=False)
    ctx.restore()
    if t > nm:
        a = seg(t, nm, nm + 0.3)
        text(ctx, "НИ НАЗВАНИЯ. НИ НОМЕРА.", 540, 1350, 54, "#ffffff", "#000", 10, alpha=a)


def s12_home(ctx, t, u, D):
    ho = EV["home"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        ctx.save()
        cam(ctx, t, 540, 900, lerp(0.95, 1.15, seg(u, 0, ec)), shake=0.15)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0f172a"), (1, "#020617")])
        board(ctx, 90, 400, t, "boarding", home=seg(t, ho - 0.6, ho), rows_n=5)
        ctx.restore()
        if t > EV["nocity"]:
            a = seg(t, EV["nocity"], EV["nocity"] + 0.3)
            text(ctx, "БЕЗ ГОРОДА", 540, 1300, 80, "#facc15", "#000", 12, alpha=a)
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
        text(ctx, "Куда летит рейс домой?", 0, 180, 62, "#7dd3fc")
    ctx.restore()


SCENES = [s0_hook, s1_delay, s2_spot, s3_food, s4_hygiene, s5_sleep, s6_board, s7_tally, s8_board, s9_gate,
          s10_scan, s11_plane, s12_home]
LABELS = {9: "ВЫХОД 47", 10: "ВЫХОД 47", 11: "ВЫХОД 47", 12: "ВЫХОД 47"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("двадцать", "четыре", "часа"), "24 часа"), (("девятьсот", "рублей"), "900 руб."),
         (("пять", "часов"), "5 часов"), (("сто", "процентов"), "100%"), (("ноль",), "0"), (("два", "часа"), "2 часа")]


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
        text(ctx, "СУТКИ", 0, 10, 116, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -330, 90, 660, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "В АЭРОПОРТУ?", 0, 155, 90, "#ffffff")
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
