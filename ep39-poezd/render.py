"""Серия 39 «Пустая электричка» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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










# ================================================================== ПУСТАЯ ЭЛЕКТРИЧКА
TEAL2 = ("#0891b2", "#155e75")
STATIONS = ("Сосновка", "Луговая", "47 км", "Берёзки", "Платформа 0", "Заречье")


def rider2(ctx, x, y, sc, e, t, arms="relax", look=(0, 0), walk=None, back=False, legs=True, tremble=0.0, item=None):
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, walk=walk, back=back, legs=legs, tremble=tremble,
         rim="#a5f3fc", rim_a=0.6, hood=TEAL2, hand_item=item)


def train_window(ctx, x, y, w, h, t, lit=0.0, reflect=None):
    ctx.save()
    rr(ctx, x, y, w, h, 24)
    ctx.clip()
    src(ctx, "#020617")
    ctx.paint()
    for k in range(3):  # редкие тени деревьев/столбов
        px = x + ((k * 300 - t * 1800) % (w + 400)) - 200
        line(ctx, px, y, px, y + h, 10, "#0f172a")
    if lit:
        ctx.rectangle(x, y, w, h)
        fill(ctx, "#fef3c7", 0.8 * lit)
    if reflect:
        reflect(ctx)
    ctx.restore()
    rr(ctx, x, y, w, h, 24)
    ctx.set_line_width(14)
    src(ctx, "#94a3b8")
    ctx.stroke()
    line(ctx, x + 30, y + 20, x + 80, y + h - 20, 4, "#ffffff", 0.08)


def carriage(ctx, t, x0=-1200, x1=2400, lights=1.0, lit_out=0.0, sway=0.0, doors=True, board_txt="ПЛАТФОРМА 0",
             reflect=None, empty=True):
    ctx.save()
    ctx.translate(540, 1300)
    ctx.rotate(sway * math.sin(t * 2))
    ctx.translate(-540, -1300)
    vgrad(ctx, x0 - 600, -800, x1 - x0 + 1200, 3600, [(0, "#d6d3d1"), (1, "#a8a29e")])
    for k in range(int((x1 - x0) / 420) + 2):  # окна
        train_window(ctx, x0 + k * 420 + 30, 420, 360, 340, t + k * 0.13, lit_out, reflect if k == 1 else None)
    rr(ctx, 280, 230, 520, 120, 10)  # табло станции
    fill(ctx, "#0b0b12")
    text(ctx, board_txt, 540, 290, 46, "#ef4444" if (t * 2) % 1 < 0.7 else "#7f1d1d")
    rr(ctx, x0 - 600, 360, x1 - x0 + 1200, 40, 0)  # схема линии
    fill(ctx, "#f8fafc")
    line(ctx, x0 - 500, 380, x1 + 500, 380, 6, "#16a34a")
    for k in range(-8, 20):
        ctx.arc(k * 150, 380, 9, 0, TAU)
        fill(ctx, "#ffffff")
        ctx.arc(k * 150, 380, 9, 0, TAU)
        ctx.set_line_width(4)
        src(ctx, "#16a34a")
        ctx.stroke()
    line(ctx, x0 - 600, 170, x1 + 600, 170, 14, "#cbd5e1")  # поручни
    for k in range(int((x1 - x0) / 200) + 6):
        hx = x0 - 600 + k * 200
        ex = hx + math.sin(t * 2 + k) * 14
        line(ctx, hx, 170, ex, 290, 4, "#9ca3af")
        ctx.arc(ex, 308, 18, 0, TAU)
        ctx.set_line_width(6)
        src(ctx, "#f8fafc")
        ctx.stroke()
    for k in range(int((x1 - x0) / 300) + 2):  # деревянные сиденья
        sx = x0 + k * 300
        rr(ctx, sx, 1200, 260, 60, 10)
        fill(ctx, "#92400e")
        for j in range(4):
            rr(ctx, sx + 6, 1000 + j * 48, 248, 36, 6)
            fill(ctx, "#a16207")
        rr(ctx, sx + 20, 1260, 20, 220, 4)
        fill(ctx, "#57534e")
        rr(ctx, sx + 220, 1260, 20, 220, 4)
        fill(ctx, "#57534e")
    if doors:
        for dx in (x0 + 900, x1 - 900):
            rr(ctx, dx, 420, 300, 1280, 10)
            fill(ctx, "#9ca3af")
            line(ctx, dx + 150, 420, dx + 150, 1700, 6, "#6b7280")
            rr(ctx, dx + 20, 500, 110, 340, 10)
            fill(ctx, "#020617")
            rr(ctx, dx + 170, 500, 110, 340, 10)
            fill(ctx, "#020617")
            text(ctx, "НЕ ПРИСЛОНЯТЬСЯ", dx + 150, 1000, 20, "#334155")
    ctx.rectangle(x0 - 600, 1700, x1 - x0 + 1200, 1200)
    fill(ctx, "#57534e")
    for k in range(int((x1 - x0) / 150) + 8):
        line(ctx, x0 - 600 + k * 150, 1700, x0 - 600 + k * 150 - 80, 2900, 3, "#44403c")
    r = random.Random(3)
    for k in range(8):  # мусор: билетик, газета, бутылка
        rr(ctx, r.uniform(x0, x1), 1760 + r.uniform(0, 300), r.uniform(30, 70), r.uniform(14, 24), 4)
        fill(ctx, r.choice(("#fef3c7", "#e7e5e4", "#86efac")))
    ctx.restore()
    if lights < 1:
        ctx.save()
        ctx.identity_matrix()
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#020617", 0.7 * (1 - lights))
        ctx.restore()


def intercom(ctx, x, y, s, t, pressed=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rr(ctx, -140, -220, 280, 440, 20)
    fill(ctx, "#d4d4d8")
    rr(ctx, -110, -190, 220, 80, 10)
    fill(ctx, "#facc15")
    text(ctx, "СВЯЗЬ С", 0, -165, 26, "#111827")
    text(ctx, "МАШИНИСТОМ", 0, -130, 26, "#111827")
    for k in range(8):
        line(ctx, -90, -80 + k * 18, 90, -80 + k * 18, 6, "#52525b")
    ctx.arc(0, 120, 60 - 6 * pressed, 0, TAU)
    fill(ctx, "#dc2626" if not pressed else "#b91c1c")
    ctx.arc(0, 120, 60, 0, TAU)
    ctx.set_line_width(8)
    src(ctx, "#71717a")
    ctx.stroke()
    if pressed:
        glow(ctx, 0, 120, 160, "#ef4444", 0.6 * pressed)
    ctx.restore()


def stop_crane(ctx, x, y, s):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rr(ctx, -120, -200, 240, 400, 16)
    fill(ctx, "#dc2626")
    text(ctx, "СТОП-КРАН", 0, -150, 34, "#ffffff")
    rr(ctx, -30, -100, 60, 220, 14)
    fill(ctx, "#111827")
    ctx.arc(0, 40, 20, 0, TAU)  # пломба
    fill(ctx, "#facc15")
    line(ctx, -40, 30, 40, 50, 3, "#94a3b8")
    ctx.restore()


def platform(ctx, t, crowd=True, sign=0.0, lit=1.0, train_x=None, clap=False):
    vgrad(ctx, -1500, -1200, 4000, 2600, [(0, "#0b1022"), (1, "#1e293b")])
    for k in range(-3, 8):  # фонари
        lamp_post(ctx, k * 400, 1500, 900, on=True)
        glow(ctx, k * 400 + 125, 640, 380, "#fef3c7", 0.45 * lit)
    rr(ctx, -1500, 1500, 4000, 120, 0)  # край платформы
    fill(ctx, "#facc15")
    ctx.rectangle(-1500, 1620, 4000, 1200)
    fill(ctx, "#cbd5e1")
    for k in range(-14, 30):
        line(ctx, k * 140, 1620, k * 140 - 120, 2800, 2, "#94a3b8")
    rr(ctx, 340, 300, 400, 120, 10)  # название
    fill(ctx, "#1d4ed8")
    text(ctx, "ПЛАТФОРМА 0", 540, 360, 46, "#ffffff")
    if crowd:
        r = random.Random(11)
        for i in range(8):
            p = Npc(r, -400 + i * 260, 1950 + (i % 2) * 70, 1.0, r.choice((-1, 1)))
            p.item = "none"
            npc(ctx, p, t, walking=False, clap=clap, grin=0.7)
            if i in (2, 5):  # цветы
                for j in range(3):
                    ctx.arc(p.x + 40 * p.dir + j * 12, p.y - 300, 14, 0, TAU)
                    fill(ctx, ("#f43f5e", "#facc15", "#f8fafc")[j])
        if sign:
            rr(ctx, 160, 1250, 760, 200, 16)
            fill(ctx, "#ffffff", sign)
            text(ctx, "С ВОЗВРАЩЕНИЕМ!", 540, 1350, 64, "#dc2626", alpha=sign)
            for sx in (260, 820):
                line(ctx, sx, 1450, sx, 1700, 10, "#78350f", sign)


def train_side(ctx, x, y, s, t, lit=1.0, doors_open=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for k in range(3):
        cx = k * 1100
        rr(ctx, cx, -700, 1060, 700, 40)
        fill(ctx, "#16a34a")
        rr(ctx, cx, -200, 1060, 60, 0)
        fill(ctx, "#15803d")
        rr(ctx, cx, -660, 1060, 30, 10)
        fill(ctx, "#f8fafc")
        for j in range(4):
            rr(ctx, cx + 60 + j * 250, -580, 200, 220, 14)
            fill(ctx, "#fef3c7" if lit else "#020617")
        rr(ctx, cx + 440, -600, 180 * (1 - doors_open) + 4, 560, 8)
        fill(ctx, "#9ca3af")
        for wx in (100, 960):
            ctx.arc(cx + wx, 0, 50, 0, TAU)
            fill(ctx, "#111827")
    ctx.restore()


def mixh(c1, c2, k):
    a, b = hexc(c1), hexc(c2)
    return "#%02x%02x%02x" % tuple(int(255 * (a[i] + (b[i] - a[i]) * clamp(k))) for i in range(3))


# ================================================================== СЦЕНЫ
def s0_hook(ctx, t, u, D):
    wk = EV["woke"]
    ctx.save()
    cam(ctx, t, 540, 1300, lerp(0.8, 0.9, seg(u, 0, D)), shake=0.2)
    carriage(ctx, t, sway=0.01, board_txt="———")
    rider2(ctx, 540, 1700, 1.0, emo("sleep") if t < wk else emo("shock"), t, arms="relax" if t < wk else "shock",
           legs=False)
    if t < wk:
        text(ctx, "z", 700, 1200 - (t * 60) % 120, 60, "#0891b2", alpha=0.7)
    ctx.restore()


def s1_board(ctx, t, u, D):
    ns = EV["noscheme"]
    ctx.save()
    cam(ctx, t, 540, lerp(700, 400, ease(seg(u, 0, D))), lerp(0.9, 1.4, ease(seg(u, 0, D))), shake=0.2)
    carriage(ctx, t, sway=0.01, board_txt="ПЛАТФОРМА 0")
    ctx.restore()
    if t > ns:
        rr(ctx, 120, 1250, 840, 260, 20)
        fill(ctx, "#f8fafc")
        line(ctx, 160, 1380, 920, 1380, 8, "#16a34a")
        for k, nm in enumerate(STATIONS[:4] + STATIONS[5:]):
            ctx.arc(200 + k * 170, 1380, 14, 0, TAU)
            fill(ctx, "#16a34a")
            text(ctx, nm, 200 + k * 170, 1430, 20, "#111827")
        text(ctx, "«ПЛАТФОРМА 0» — НЕТ НА СХЕМЕ", 540, 1300, 32, "#dc2626")


def s2_intercom(ctx, t, u, D):
    ic = EV["intercom"]
    ctx.save()
    cam(ctx, t, 540, 1250, 0.95, shake=0.15)
    carriage(ctx, t, sway=0.008)
    stop_crane(ctx, 200, 1150, 1.0)
    crossmark(ctx, 200, 1150, 2.4)
    intercom(ctx, 800, 1150, 1.0, t, pressed=seg(t, ic, ic + 0.3))
    rider2(ctx, 560, 2050, 1.0, emo("determined"), t, arms="fwd", look=(0.7, -0.3))
    ctx.restore()
    if t > ic + 0.6:
        text(ctx, "ш-ш-ш…", 800, 760, 50, "#94a3b8", "#000", 6)
    step_card(ctx, t, EV["steps"][0], 1, "НЕ СТОП-КРАН\nСНАЧАЛА СВЯЗЬ")


def s3_head(ctx, t, u, D):
    hx = lerp(-200, 1200, seg(u, 0, D))
    n = 1 + int(seg(u, 0, D) * 7.99)
    ctx.save()
    cam(ctx, t, hx, 1300, 0.85, shake=0.15)
    carriage(ctx, t, x0=-1600, x1=2800, sway=0.008)
    rider2(ctx, hx, 2050, 1.0, emo("determined"), t, arms="relax", walk=t * 6)
    ctx.restore()
    rr(ctx, 340, 1240, 400, 150, 30)
    fill(ctx, "#0b0b12", 0.85)
    text(ctx, "ВАГОН", 540, 1280, 32, "#a5f3fc")
    text(ctx, f"{n} / 8", 540, 1350, 70, "#ffffff")
    step_card(ctx, t, EV["steps"][1], 2, "ИДИ\nК ГОЛОВЕ ПОЕЗДА")


def geo_screen(t, k):
    def f(c, x, y, w, h):
        c.rectangle(x, y, w, h)
        fill(c, "#e2e8f0")
        r = random.Random(4)
        for i in range(12):
            ell(c, x + r.uniform(0, w), y + r.uniform(0, h * 0.6), r.uniform(40, 100), r.uniform(30, 80))
            fill(c, "#bbf7d0", 0.8)
        line(c, x, y + h * 0.35, x + w, y + h * 0.2, 10, "#16a34a")
        px = x + w * (0.3 + 0.5 * ((t * 0.3) % 1))
        c.arc(px, y + h * 0.3, 18, 0, TAU)
        fill(c, "#2563eb")
        glow(c, px, y + h * 0.3, 60, "#2563eb", 0.6)
        rr(c, x + 20, y + h * 0.52, w - 40, h * 0.44, 24)
        fill(c, "#0b0b12", 0.95)
        text(c, "ВРЕМЯ  03:07", x + 50, y + h * 0.52 + 50, 30, "#e5e7eb", align="left")
        for i, nm in enumerate(("Сосновка  23:41", "Луговая  23:58", "47 км  00:12", "???  —")):
            text(c, nm, x + 50, y + h * 0.52 + 110 + i * 56, 30, "#ef4444" if i == 3 else "#a5f3fc", align="left",
                 alpha=seg(k, i / 4, i / 4 + 0.25))
    return f


def s4_geo(ctx, t, u, D):
    ge = EV["geo"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.9, shake=0.15)
    carriage(ctx, t, sway=0.008)
    ctx.restore()
    ctx.rectangle(0, 0, W, H)
    fill(ctx, "#000", 0.35)
    hands_phone(ctx, t, geo_screen(t, seg(t, ge, TL.shots[5][0])), tremble=0.6, sc=0.8, cy=1050, hood=TEAL2)
    step_card(ctx, t, EV["steps"][2], 3, "ГДЕ ТЫ\nГЕО И ИСТОРИЯ")


def s5_doors(ctx, t, u, D):
    do = EV["doors"]
    ctx.save()
    cam(ctx, t, 600, 1150, 1.0, shake=0.25)
    carriage(ctx, t, sway=0.012)
    rider2(ctx, 300, 2000, 1.0, emo("worry"), t, arms="relax", look=(0.8, -0.2))
    ctx.restore()
    speed_lines(ctx, W, H, t, n=30, a=0.25, seed=5)
    if t > do:
        crossmark(ctx, 870, 1100, 3.0)
    rr(ctx, 380, 1360, 320, 110, 30)
    fill(ctx, "#0b0b12", 0.85)
    text(ctx, "120 КМ/Ч", 540, 1415, 54, "#ef4444")
    step_card(ctx, t, EV["steps"][3], 4, "ДВЕРИ\nНЕ ОТКРЫВАЙ")


def s6_platform(ctx, t, u, D):
    li = EV["lit"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.85, shake=0.15)
    carriage(ctx, t, lit_out=seg(t, li - 0.4, li + 0.4), sway=0.004)
    rider2(ctx, 540, 2050, 1.0, emo("determined"), t, arms="relax", look=(0, -0.3))
    ctx.restore()
    for k in range(2):
        a = seg(t, li, li + 0.3)
        if k == 0:
            checkmark(ctx, 260, 760, 1.2, OK, a)
        else:
            rr(ctx, 600, 680, 400, 120, 20)
            fill(ctx, "#020617", a)
            text(ctx, "ТЁМНАЯ", 800, 740, 40, "#94a3b8", alpha=a)
            crossmark(ctx, 800, 740, 1.4)
    step_card(ctx, t, EV["steps"][4], 5, "ВЫХОДИ\nНА СВЕТЛУЮ")


def ic_talk(c, x, y, col, a):
    rr(c, x - 20, y - 24, 40, 48, 8)
    fill(c, col, a)
    for k in range(3):
        line(c, x - 12, y - 12 + k * 10, x + 12, y - 12 + k * 10, 3, "#0b0b12", a)


def ic_wagon(c, x, y, col, a):
    rr(c, x - 26, y - 16, 52, 30, 6)
    fill(c, col, a)
    for k in range(3):
        rr(c, x - 20 + k * 15, y - 10, 10, 10, 2)
        fill(c, "#0b0b12", a)


def ic_crane(c, x, y, col, a):
    rr(c, x - 16, y - 24, 32, 48, 6)
    fill(c, col, a)
    c.arc(x, y + 6, 6, 0, TAU)
    fill(c, "#facc15", a)


def ic_doors(c, x, y, col, a):
    rr(c, x - 22, y - 24, 44, 48, 4)
    fill(c, col, a)
    line(c, x, y - 24, x, y + 24, 4, "#0b0b12", a)


def ic_lamp(c, x, y, col, a):
    line(c, x, y + 24, x, y - 10, 5, col, a)
    c.arc(x, y - 16, 12, 0, TAU)
    fill(c, col, a)


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА ПОЕЗДКИ", [
        ("ПЕРЕГОВОРКА", "нажата", 1.0, "#facc15", "1/1", ic_talk),
        ("ВАГОНЫ", "пройдено", 1.0, "#22c55e", "8", ic_wagon),
        ("СТОП-КРАН", "не тронут", 0.0, "#ef4444", "0", ic_crane),
        ("ДВЕРИ", "закрыты", 0.0, "#94a3b8", "0", ic_doors),
        ("ПЛАТФОРМА", "освещённая", 1.0, "#fde68a", "1/1", ic_lamp)], EV["tally"])


def s8_stop(ctx, t, u, D):
    st = EV["stop"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.8, shake=0.15)
    platform(ctx, t, crowd=False)
    train_side(ctx, lerp(1400, -900, ease(seg(t, TL.shots[8][0], st + 0.6))), 1500, 1.0, t)
    ctx.restore()


def s9_welcome(ctx, t, u, D):
    sg = EV["sign"]
    ctx.save()
    cam(ctx, t, 540, 1350, 0.8, shake=0.1)
    platform(ctx, t, crowd=True, sign=seg(t, sg - 0.4, sg))
    rider2(ctx, 540, 2300, 1.1, emo("worry"), t, arms="relax", back=True)
    ctx.restore()


def s10_thirty(ctx, t, u, D):
    th = EV["thirty"]
    ctx.save()
    cam(ctx, t, 540, 1350, 0.8, shake=0.1)
    platform(ctx, t, crowd=True, sign=1.0, clap=True)
    rider2(ctx, 540, 2300, 1.1, emo("fear"), t, arms="shock", back=False, tremble=0.3)
    ctx.restore()
    if t > th:
        a = seg(t, th, th + 0.3)
        rr(ctx, 200, 640, 680, 130, 30)
        fill(ctx, "#0b0b12", 0.9 * a)
        text(ctx, "30 ЛЕТ", 540, 705, 80, "#fde68a", alpha=a)
        text(ctx, "1996 — 2026", 540, 820, 46, "#ffffff", "#000", 6, alpha=a)


def s11_reflect(ctx, t, u, D):
    no = EV["notold"]
    ctx.save()
    cam(ctx, t, 540, 1050, lerp(1.0, 1.15, seg(u, 0, D)), shake=0.1)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#16a34a"), (1, "#14532d")])
    rr(ctx, 140, 300, 800, 1200, 30)  # окно вагона с отражением
    fill(ctx, "#020617")
    ctx.save()
    rr(ctx, 140, 300, 800, 1200, 30)
    ctx.clip()
    ctx.push_group()
    rider2(ctx, 540, 1600, 1.6, emo("fear"), t, arms="relax", legs=False)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(0.55)
    for k in range(6):
        glow(ctx, 200 + k * 140, 1300, 80, "#fef3c7", 0.3)
    ctx.restore()
    rr(ctx, 140, 300, 800, 1200, 30)
    ctx.set_line_width(20)
    src(ctx, "#94a3b8")
    ctx.stroke()
    ctx.restore()
    if t > no:
        text(ctx, "НИ НА ДЕНЬ", 540, 220, 80, "#ffffff", "#000", 10, alpha=seg(t, no, no + 0.3))


def s12_next(ctx, t, u, D):
    cl, nx = EV["close"], EV["next"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        ctx.save()
        cam(ctx, t, 540, 1300, 0.8, shake=0.1)
        platform(ctx, t, crowd=False, lit=1.0)
        k = ease(seg(t, cl + 0.5, nx + 1.5))
        train_side(ctx, -900 - 2600 * k, 1500, 1.0, t, lit=1.0, doors_open=1 - seg(t, cl - 0.2, cl + 0.4))
        p_crowd = random.Random(11)
        for i in range(5):
            p = Npc(p_crowd, 100 + i * 220, 2100 + (i % 2) * 60, 1.0, 1)
            p.item = "none"
            npc(ctx, p, t, walking=False, back=True)
        rider2(ctx, 540, 2350, 1.1, emo("fear"), t, arms="relax", back=True)
        ctx.restore()
        if t > nx:
            text(ctx, "ЗА СЛЕДУЮЩИМ", 540, 640, 80, "#a5f3fc", "#000", 10, alpha=seg(t, nx, nx + 0.3))
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
        text(ctx, "Кого привезёт электричка?", 0, 180, 58, "#a5f3fc")
    ctx.restore()


SCENES = [s0_hook, s1_board, s2_intercom, s3_head, s4_geo, s5_doors, s6_platform, s7_tally, s8_stop, s9_welcome,
          s10_thirty, s11_reflect, s12_next]
LABELS = {}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("восемь",), "8"), (("тридцать", "лет"), "30 лет")]


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
        text(ctx, "ТЫ ПРОСНУЛСЯ", 0, 10, 110, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -380, 90, 760, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "В ПУСТОМ ПОЕЗДЕ?", 0, 155, 80, "#ffffff")
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
