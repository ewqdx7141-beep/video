"""Серия 27 «Читаешь мысли» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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










LIVE = "#ef4444"

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



def tunnel_window(ctx, x, y, w, h, t, platform=0.0):
    """Окно вагона: тёмный тоннель с огнями или яркая платформа, пролетающая мимо."""
    ctx.save()
    rr(ctx, x, y, w, h, 30)
    ctx.clip()
    src(ctx, "#05070c")
    ctx.paint()
    for k in range(6):  # кабели
        line(ctx, x, y + 30 + k * 18, x + w, y + 30 + k * 18, 3, "#1f2937")
    for k in range(3):  # огни тоннеля проносятся
        lx = x + ((k * 400 - t * 2600) % (w + 600)) - 300
        line(ctx, lx, y + h * 0.55, lx + 200, y + h * 0.55, 8, "#fde68a", 0.8)
        glow(ctx, lx + 100, y + h * 0.55, 80, "#fbbf24", 0.35)
    if platform > 0:
        ctx.rectangle(x, y, w, h)
        fill(ctx, "#fff7e0", platform * 0.85)
        for k in range(8):
            cx = x + ((k * 160 - t * 4200) % (w + 300)) - 150
            ctx.rectangle(cx, y, 40, h)
            fill(ctx, "#a8a29e", platform * 0.6)
    ctx.restore()
    rr(ctx, x, y, w, h, 30)
    ctx.set_line_width(14)
    src(ctx, "#9ca3af")
    ctx.stroke()
    line(ctx, x + 30, y + 20, x + 90, y + h - 20, 4, "#ffffff", 0.08)



def metro_car(ctx, t, lights=1.0, platform=0.0, look=0.0, empty=False, seed=0, stare_order=None, phones_live=0.0,
              brake=0.0):
    """Вагон метро: окна, реклама, схема линии, поручни, сидящие и стоящие пассажиры."""
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#e5e7eb"), (1, "#cbd5e1")])
    # реклама и схема линии
    for k in range(-3, 7):
        x = k * 420
        rr(ctx, x + 10, 220, 400, 120, 6)
        fill(ctx, ["#f59e0b", "#3b82f6", "#ec4899", "#10b981"][k % 4])
        text(ctx, ["КРЕДИТ 0%", "КУРСЫ IT", "ДОСТАВКА", "ОТПУСК"][k % 4], x + 210, 280, 44, "#ffffff")
    rr(ctx, -1200, 350, 3600, 50, 0)
    fill(ctx, "#f8fafc")
    line(ctx, -1100, 375, 2400, 375, 8, "#dc2626")
    for k in range(-10, 26):
        ctx.arc(k * 140, 375, 10, 0, TAU)
        fill(ctx, "#ffffff")
        ctx.arc(k * 140, 375, 10, 0, TAU)
        ctx.set_line_width(4)
        src(ctx, "#dc2626")
        ctx.stroke()
    # окна
    for k in range(-3, 7):
        tunnel_window(ctx, k * 420 + 30, 430, 360, 330, t + k * 0.13, platform)
    # двери с надписью
    for dx in (-500, 1300):
        rr(ctx, dx, 400, 300, 1300, 10)
        fill(ctx, "#94a3b8")
        line(ctx, dx + 150, 400, dx + 150, 1700, 6, "#64748b")
        text(ctx, "НЕ ПРИСЛОНЯТЬСЯ", dx + 150, 1100, 22, "#334155")
    # скамья
    rr(ctx, -1200, 1300, 3600, 60, 10)
    fill(ctx, "#1e40af")
    rr(ctx, -1200, 1360, 3600, 90, 10)
    fill(ctx, "#1d4ed8")
    ctx.rectangle(-1200, 1450, 3600, 260)
    fill(ctx, "#475569")
    # поручни
    line(ctx, -1200, 160, 2400, 160, 14, "#cbd5e1")
    for k in range(-6, 14):
        hx = k * 200 + 100
        sw = math.sin(t * 2 + k) * 0.12 + brake * 0.6
        ex, ey = hx + math.sin(sw) * 110, 160 + math.cos(sw) * 110
        line(ctx, hx, 160, ex, ey, 4, "#9ca3af")
        ctx.arc(ex, ey + 18, 20, 0, TAU)
        ctx.set_line_width(7)
        src(ctx, "#f8fafc")
        ctx.stroke()
    for px in (-300, 600, 1500):
        line(ctx, px, 160, px, 1700, 16, "#d1d5db")
    if not empty:
        r = random.Random(50 + seed)
        # сидящие
        for i in range(12):
            x = -800 + i * 200 + r.uniform(-20, 20)
            p = Npc(random.Random(i * 13 + 3 + seed), x, 1650, 0.95, 1)
            p.item = "phone"
            if i == 6:  # мама с малышом
                p.style, p.item = "long", "none"
            st = 0.0
            if stare_order is not None:
                st = ease(seg(t, stare_order(i), stare_order(i) + 0.35))
            p.dir = -1 if st > 0.5 else 1
            ctx.save()
            if brake:
                ctx.translate(x, 1650)
                ctx.rotate(-0.25 * brake)
                ctx.translate(-x, -1650)
            npc(ctx, p, t, walking=False, stare=st, look_down=(st < 0.5 and p.item == "phone"))
            ctx.restore()
            if p.item == "phone":
                glow(ctx, x + (40 if p.dir > 0 else -40) * 0.95, 1300, 70, "#93c5fd", 0.35 * (1 - st))
            if i == 6:  # малыш
                bx = x + 30 * p.dir
                ctx.arc(bx, 1360, 34, 0, TAU)
                fill(ctx, "#fde2c8")
                rr(ctx, bx - 45, 1380, 90, 80, 30)
                fill(ctx, "#fbcfe8")
                if st > 0.5:
                    for ex in (-10, 12):
                        ctx.arc(bx + ex, 1355, 9, 0, TAU)
                        fill(ctx, "#ffffff")
                        ctx.arc(bx + ex - 2, 1355, 4, 0, TAU)
                        fill(ctx, "#111")
                else:
                    for ex in (-10, 12):
                        ctx.arc(bx + ex, 1358, 5, 0.3, TAU / 2 - 0.3)
                        ctx.set_line_width(3)
                        src(ctx, "#111")
                        ctx.stroke()
            if phones_live > 0 and p.item == "phone":
                ph_x = x + (70 if p.dir > 0 else -70) * 0.95
                rr(ctx, ph_x - 48, 1330, 96, 170, 10)
                fill(ctx, "#111")
                rr(ctx, ph_x - 42, 1336, 84, 158, 7)
                fill(ctx, "#334155")
                ctx.save()
                ctx.rectangle(ph_x - 42, 1336, 84, 158)
                ctx.clip()
                hero(ctx, ph_x, 1560, 0.3, emo("neutral"), t, back=True, legs=False, rim_a=0.0)
                ctx.restore()
                rr(ctx, ph_x - 38, 1342, 34, 16, 4)
                fill(ctx, LIVE, phones_live)
                text(ctx, "LIVE", ph_x - 21, 1350, 11, "#ffffff", alpha=phones_live)
                glow(ctx, ph_x, 1410, 90, "#93c5fd", 0.3)
        # стоящие
        for i in range(6):
            x = -700 + i * 420 + r.uniform(-40, 40)
            p = Npc(random.Random(i * 7 + 101 + seed), x, 1880, 1.12, 1)
            p.item = "bag" if i % 2 else "phone"
            st = 0.0
            if stare_order is not None:
                st = ease(seg(t, stare_order(20 + i), stare_order(20 + i) + 0.35))
            p.dir = -1 if st > 0.5 else 1
            ctx.save()
            ctx.translate(x, 1880)
            ctx.rotate(-0.12 * brake + math.sin(t * 1.3 + i) * 0.015)
            ctx.translate(-x, -1880)
            npc(ctx, p, t, walking=False, stare=st, look_down=(st < 0.5 and p.item == "phone"))
            ctx.restore()
    ctx.rectangle(-1200, 1700, 3600, 600)
    fill(ctx, "#64748b")
    for k in range(-10, 26):
        line(ctx, k * 150, 1700, k * 150 - 80, 2200, 3, "#475569")
    if lights < 1:
        ctx.rectangle(-1200, -800, 3600, 3600)
        fill(ctx, "#020617", 0.7 * (1 - lights))



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



def coworkers(ctx, t, seed=8, n=4, y0=1350):
    r = random.Random(seed)
    for i in range(n):
        p = Npc(r, -150 + i * 420, y0 + (i % 2) * 60, 0.9, r.choice((-1, 1)))
        p.item = "none"
        npc(ctx, p, t, walking=False)
        office_desk(ctx, -150 + i * 420, y0 + 60 + (i % 2) * 60, 0.75, t, i)




# ================================================================== ЧИТАЕШЬ МЫСЛИ
CYAN = ("#0891b2", "#155e75")
THINK = "#f5f3ff"


def mind(ctx, x, y, sc, e, t, arms="relax", look=(0, 0), walk=None, back=False, legs=True, tremble=0.0, item=None,
         phones=False):
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, walk=walk, back=back, legs=legs, tremble=tremble,
         rim="#c4b5fd", rim_a=0.6, hood=CYAN, hand_item=item)
    if phones:
        hy = y - (455 if legs else 285) * sc
        ctx.arc(x, hy - 10 * sc, 125 * sc, math.pi * 1.05, math.pi * 1.95)
        ctx.set_line_width(16 * sc)
        src(ctx, "#111827")
        ctx.stroke()
        for sd in (-1, 1):
            rr(ctx, x + sd * 120 * sc - 26 * sc, hy - 40 * sc, 52 * sc, 90 * sc, 22 * sc)
            fill(ctx, "#ef4444")
            rr(ctx, x + sd * 120 * sc - 14 * sc, hy - 26 * sc, 28 * sc, 60 * sc, 12 * sc)
            fill(ctx, "#7f1d1d")
        for k in range(3):  # волны музыки
            a = (t * 1.2 + k / 3) % 1
            ctx.arc(x + 130 * sc, hy, (40 + a * 160) * sc, -0.7, 0.7)
            ctx.set_line_width(6 * sc)
            src(ctx, "#a78bfa", 1 - a)
            ctx.stroke()
            ctx.arc(x + (170 + a * 110) * sc, hy - (60 + a * 110) * sc, 10 * sc, 0, TAU)
            fill(ctx, "#c4b5fd", 1 - a)
            line(ctx, x + (180 + a * 110) * sc, hy - (60 + a * 110) * sc, x + (180 + a * 110) * sc,
                 hy - (110 + a * 110) * sc, 4 * sc, "#c4b5fd", 1 - a)


def thought(ctx, x, y, w, txt, a=1.0, hx=None, hy=None, icon=None, locked=False, col=THINK, tcol="#3b0764",
            size=34, blur=0.0, wob=0.0):
    """Облачко мысли с центром (x, y); пузырьки тянутся к голове (hx, hy)."""
    if a <= 0:
        return
    ctx.save()
    ctx.push_group()
    rows = txt.split("\n") if txt else []
    h = max(110, 50 + len(rows) * size * 1.2)
    r = random.Random(int(x * 7 + y))
    for k in range(12):  # кудрявые края
        ang = k / 12 * TAU
        ctx.arc(x + math.cos(ang) * w * 0.46 + math.sin(wob + k) * 4, y + math.sin(ang) * h * 0.42,
                h * 0.32 + r.uniform(-6, 6), 0, TAU)
        fill(ctx, col)
    ell(ctx, x, y, w * 0.5, h * 0.48)
    fill(ctx, col)
    if hx is not None:
        for k in range(3):
            f = (k + 1) / 4
            ctx.arc(lerp(x, hx, 0.35 + f * 0.6), lerp(y + h * 0.45, hy, 0.35 + f * 0.6), 18 - k * 5, 0, TAU)
            fill(ctx, col)
    if locked:
        rr(ctx, x - 40, y - 10, 80, 60, 10)
        fill(ctx, "#6b7280")
        ctx.arc(x, y - 12, 26, math.pi, TAU)
        ctx.set_line_width(10)
        src(ctx, "#6b7280")
        ctx.stroke()
        ctx.arc(x, y + 18, 8, 0, TAU)
        fill(ctx, "#f5f3ff")
    else:
        if icon:
            icon(ctx, x - w * 0.32, y)
        for i, rw in enumerate(rows):
            text(ctx, rw, x + (w * 0.08 if icon else 0), y - (len(rows) - 1) * size * 0.6 + i * size * 1.2, size, tcol)
    if blur:
        ell(ctx, x, y, w * 0.55, h * 0.55)
        fill(ctx, "#e9d5ff", 0.85 * blur)
        for k in range(4):
            line(ctx, x - w * 0.3, y - 20 + k * 14, x + w * 0.3, y - 20 + k * 14, 6, "#c4b5fd", 0.6 * blur)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def ic_milk(c, x, y):
    rr(c, x - 14, y - 22, 28, 44, 4)
    fill(c, "#60a5fa")


def ic_clock2(c, x, y):
    c.arc(x, y, 20, 0, TAU)
    fill(c, "#f59e0b")
    line(c, x, y, x, y - 12, 4, "#3b0764")
    line(c, x, y, x + 9, y, 4, "#3b0764")


def ic_heart2(c, x, y):
    c.move_to(x, y + 18)
    c.curve_to(x - 34, y - 4, x - 16, y - 26, x, y - 8)
    c.curve_to(x + 16, y - 26, x + 34, y - 4, x, y + 18)
    fill(c, "#ec4899")


def ic_money(c, x, y):
    rr(c, x - 22, y - 13, 44, 26, 4)
    fill(c, "#22c55e")


def ic_cat(c, x, y):
    c.arc(x, y, 18, 0, TAU)
    fill(c, "#f97316")
    for sd in (-1, 1):
        c.move_to(x + sd * 16, y - 6)
        c.line_to(x + sd * 14, y - 26)
        c.line_to(x + sd * 4, y - 14)
        fill(c, "#f97316")


THOUGHTS = [("опоздаю\nна планёрку", ic_clock2), ("купить\nмолоко", ic_milk), ("он мне\nнравится", ic_heart2),
            ("до зарплаты\n3 дня", ic_money), ("покормить\nкота", ic_cat), ("зачем я\nэто сказал", None),
            ("какой\nстранный тип", None), ("выключил\nли утюг?", None)]


def crowd_thoughts(ctx, t, seed=1, n=6, y0=1750, x0=-200, dx=300, a=1.0, blur=0.0, walking=True, sc=1.0, skip=()):
    r = random.Random(seed)
    heads = []
    for i in range(n):
        p = Npc(r, x0 + i * dx, y0 + (i % 2) * 60, sc * (0.92 + (i % 3) * 0.06), r.choice((-1, 1)), 0.5)
        p.item = r.choice(["phone", "bag", "coffee", "none"])
        npc(ctx, p, t * 0.6 + i, walking=walking)
        heads.append((p.x, p.y - 370 * p.sc))
    for i, (hx, hy) in enumerate(heads):
        if i in skip:
            continue
        txt, ic = THOUGHTS[(i + seed) % len(THOUGHTS)]
        k = seg(a, i / n * 0.6, i / n * 0.6 + 0.4) if a < 1 else 1.0
        thought(ctx, hx + (i % 2) * 40 - 20, hy - 270 - (i % 2) * 100, 340, txt, k, hx, hy - 70, ic, blur=blur,
                size=34, wob=t * 2)
    return heads


def lift_bg(ctx, t):
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#3f3f46"), (1, "#27272a")])
    rr(ctx, -100, 200, 1280, 1600, 0)
    lgrad(ctx, -100, 0, 1180, 0, [(0, "#6b7280"), (0.3, "#d1d5db"), (0.55, "#9ca3af"), (0.8, "#e5e7eb"), (1, "#6b7280")])
    ctx.fill()
    rr(ctx, 300, 380, 480, 700, 12)
    fill(ctx, "#cbd5e1")
    line(ctx, 340, 420, 450, 620, 10, "#ffffff", 0.4)
    rr(ctx, 860, 420, 180, 420, 14)
    fill(ctx, "#d4d4d8")
    for k in range(8):
        ctx.arc(905 + (k % 2) * 90, 470 + (k // 2) * 80, 24, 0, TAU)
        fill(ctx, "#a1a1aa")
    rr(ctx, -60, 520, 220, 120, 8)
    fill(ctx, "#22c55e")
    text(ctx, "ДОСТАВКА", 50, 580, 30, "#ffffff")
    rr(ctx, -100, 1300, 1280, 24, 12)
    fill(ctx, "#d4d4d8")
    ctx.rectangle(-1200, 1800, 3600, 900)
    fill(ctx, "#3f3f46")


def neighbor(ctx, x, y, sc, t, grin=0.7):
    p = Npc(random.Random(123), x, y, sc, -1)
    p.style, p.hair, p.shirt, p.item, p.glasses, p.earrings = "bun", "#9a9a9a", "#be185d", "bag", True, True
    npc(ctx, p, t, walking=False, grin=grin)
    return x, y - 370 * sc


def park(ctx, t, sunset=1.0):
    vgrad(ctx, -1500, -1200, 4000, 2600, [(0, "#7c3aed"), (0.5, "#f97316"), (1, "#fde68a")])
    ctx.arc(700, 900, 140, 0, TAU)
    fill(ctx, "#fef3c7")
    glow(ctx, 700, 900, 500, "#fdba74", 0.6)
    skyline(ctx, 21, -1400, 2600, 1150, 200, 500, "#4c1d95", "#fde68a", 0.15, wmin=150, wmax=260)
    ctx.rectangle(-1500, 1150, 4000, 1600)
    fill(ctx, "#4d7c0f")
    ctx.move_to(200, 1150)  # аллея в перспективе
    ctx.line_to(880, 1150)
    ctx.line_to(1600, 2600)
    ctx.line_to(-520, 2600)
    ctx.close_path()
    fill(ctx, "#d6d3d1")
    for k in range(12):
        line(ctx, 540 - 340 - k * 60, 1150 + k * 120, 540 + 340 + k * 60, 1150 + k * 120, 2, "#a8a29e", 0.5)
    for k, (x, s) in enumerate(((-150, 1.1), (1250, 1.1), (100, 0.7), (980, 0.7), (250, 0.5), (830, 0.5))):
        tree(ctx, x, 1150 + s * 500, s * 1.6, t, k)
        ctx.save()  # осенние кроны поверх
        r = random.Random(k)
        for j in range(8):
            ctx.arc(x + r.uniform(-150, 150) * s, 1150 + s * 500 - 560 * s + r.uniform(-120, 80) * s, 70 * s, 0, TAU)
            fill(ctx, r.choice(("#f59e0b", "#ea580c", "#facc15")), 0.75)
        ctx.restore()
    for x in (-300, 1350):
        lamp_post(ctx, x, 1900, 560, on=True)
    r = random.Random(3)
    for i in range(40):  # листья на аллее
        ell(ctx, r.uniform(-300, 1400), r.uniform(1300, 2400), 14, 8)
        fill(ctx, r.choice(("#f59e0b", "#ea580c", "#b45309")), 0.8)
    for i in range(10):
        a = (t * 0.2 + i / 10) % 1
        ell(ctx, (i * 170 + t * 40) % 1400 - 100, a * 2400, 12, 7)
        fill(ctx, ("#f59e0b", "#ea580c")[i % 2], 0.8)


def bedroom(ctx, t, dark=0.8):
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#1e1b4b"), (1, "#0f172a")])
    rr(ctx, 520, 300, 520, 700, 10)  # окно ночью
    fill(ctx, "#0b1022")
    for k in range(6):
        rr(ctx, 540 + k * 85, 700 - (k % 3) * 100, 70, 300 + (k % 3) * 100, 4)
        fill(ctx, "#111827")
        for j in range(4):
            ctx.rectangle(555 + k * 85, 720 - (k % 3) * 100 + j * 60, 14, 14)
            fill(ctx, "#fde68a", 0.6 if (k + j) % 3 else 0.0)
    line(ctx, 780, 300, 780, 1000, 12, "#334155")
    line(ctx, 520, 650, 1040, 650, 12, "#334155")
    rr(ctx, 500, 280, 560, 40, 8)
    fill(ctx, "#334155")
    curtain(ctx, 460, 280, 110, 760, "#312e81", t, 1)
    curtain(ctx, 990, 280, 110, 760, "#312e81", t, -1)
    rr(ctx, -300, 1350, 820, 240, 30)  # кровать
    fill(ctx, "#334155")
    rr(ctx, -300, 1290, 280, 100, 40)
    fill(ctx, "#e2e8f0")
    rr(ctx, -100, 1360, 620, 180, 30)
    fill(ctx, "#4338ca")
    rr(ctx, 560, 1300, 200, 220, 10)  # тумбочка, часы
    fill(ctx, "#1e293b")
    rr(ctx, 590, 1230, 140, 70, 10)
    fill(ctx, "#020617")
    text(ctx, "03:07", 660, 1265, 34, "#ef4444")
    ctx.rectangle(-1200, 1700, 3600, 1200)
    fill(ctx, "#1e293b")
    if dark:
        ctx.rectangle(-1200, -800, 3600, 3600)
        fill(ctx, "#000", 0.35 * dark)


# ================================================================== СЦЕНЫ
def s0_hook(ctx, t, u, D):
    th = EV["thoughts"]
    ctx.save()
    cam(ctx, t, 540, 1250, lerp(0.8, 0.9, seg(u, 0, D)), shake=0.2)
    day_city(ctx, t)
    crowd_thoughts(ctx, t, 1, 6, 1850, -300, 330, a=seg(t, th - 0.4, th + 1.0) * 0.999)
    mind(ctx, 540, 2100, 1.0, emo("shock") if t > th else emo("calm"), t, arms="shock" if t > th else "relax")
    ctx.restore()


def s1_lift(ctx, t, u, D):
    sm, tk = EV["smile"], EV["thinks"]
    ctx.save()
    cam(ctx, t, 540, 1350, 0.9, shake=0.15)
    lift_bg(ctx, t)
    hx, hy = neighbor(ctx, 760, 1850, 1.2, t, grin=0.8)
    mind(ctx, 300, 1850, 1.0, emo("calm") if t < tk else emo("worry"), t, arms="relax", look=(0.6, 0))
    ctx.restore()
    bubble_sp(ctx, 760, 760, 420, "Доброе утро!", sm, t)
    if t > tk:
        thought(ctx, 640, 1100, 600, "опять топал\nвсю ночь, слон...", seg(t, tk, tk + 0.3), 760, 1250, size=40,
                col="#fee2e2", tcol="#7f1d1d", wob=t * 2)


def bubble_sp(ctx, x, y, w, txt, t0, t, col="#ffffff", tcol="#111827", size=42):
    a = seg(t, t0, t0 + 0.25)
    if a <= 0:
        return
    rr(ctx, x - w / 2, y - 50, w, 100, 30)
    fill(ctx, col, a)
    ctx.move_to(x - 20, y + 48)
    ctx.line_to(x + 10, y + 100)
    ctx.line_to(x + 30, y + 48)
    fill(ctx, col, a)
    text(ctx, txt, x, y, size, tcol, alpha=a)


def s2_silent(ctx, t, u, D):
    al = EV["aloud"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.85, shake=0.2)
    office(ctx, t)
    crowd_thoughts(ctx, t, 3, 4, 1800, -150, 420, walking=False)
    mind(ctx, 540, 2150, 1.0, emo("determined"), t, arms="shock", look=(0, 0.2))
    ctx.restore()
    if t > al:  # перечёркнутый ответ вслух
        a = seg(t, al, al + 0.3)
        rr(ctx, 200, 1000, 680, 110, 40)
        fill(ctx, "#ffffff", a)
        text(ctx, "«Я СЛЫШУ, ЧТО ТЫ ДУМАЕШЬ!»", 540, 1055, 34, "#111827", alpha=a)
        crossmark(ctx, 540, 1055, 2.0)
    step_card(ctx, t, EV["steps"][0], 1, "НЕ ОТВЕЧАЙ\nНА МЫСЛИ ВСЛУХ")


def s3_phones(ctx, t, u, D):
    ph, mu = EV["phones"], EV["muffle"]
    ctx.save()
    cam(ctx, t, 540, 1250, 0.8, shake=0.2)
    metro_car(ctx, t)
    r = random.Random(4)
    bl = seg(t, mu, mu + 0.8)
    for i in range(14):  # десятки мыслей в вагоне
        x = -300 + (i % 7) * 260 + r.uniform(-30, 30)
        y = 900 + (i // 7) * 260 + r.uniform(-40, 40)
        txt, ic = THOUGHTS[i % len(THOUGHTS)]
        thought(ctx, x, y, 240, txt, 1.0, x + 30, y + 200, None, size=26, blur=bl, wob=t * 2 + i)
    mind(ctx, 540, 2150, 1.05, emo("calm") if t > ph else emo("worry"), t, arms="relax", phones=t > ph)
    ctx.restore()
    step_card(ctx, t, EV["steps"][1], 2, "НАУШНИКИ\nГЛУШАТ ТОЛПУ")


def wallet(ctx, x, y, s=1.0):
    rr(ctx, x - 60 * s, y - 40 * s, 120 * s, 80 * s, 12 * s)
    fill(ctx, "#be185d")
    rr(ctx, x - 60 * s, y - 40 * s, 120 * s, 30 * s, 12 * s)
    fill(ctx, "#9d174d")
    ctx.arc(x + 40 * s, y - 20 * s, 8 * s, 0, TAU)
    fill(ctx, "#facc15")
    for k in range(3):
        ctx.arc(x - 20 * s + k * 20 * s, y + 10 * s, 6 * s, 0, TAU)
        fill(ctx, "#f9a8d4")


def s4_help(ctx, t, u, D):
    gi, wa, fo = EV["girl"], EV["wallet"], EV["found"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.85, shake=0.15)
    day_city(ctx, t)
    bench(ctx, 280, 1850, 1.4)
    p = Npc(random.Random(61), 820, 1900, 0.7, -1)  # девочка
    p.style, p.hair, p.shirt, p.item = "long", "#d9b46a", "#f472b6", "bag"
    npc(ctx, p, t, walking=False, grin=0.0 if t < fo else 0.8)
    if t < fo:
        wallet(ctx, 260, 1830, 0.9)
    k = ease(seg(t, fo - 1.2, fo))
    mind(ctx, lerp(100, 420, k), 2050, 1.0, emo("calm") if t < fo else emo("happy"), t,
         arms="give" if t > fo else "relax", walk=t * 6 if 0 < k < 1 else None,
         item=(lambda c, x, y: wallet(c, x, y, 0.5)) if t > fo else None)
    ctx.restore()
    if t > wa - 0.4:
        thought(ctx, 760, 1000, 520, "где мой\nкошелёк?!", seg(t, wa - 0.4, wa) * (1 - seg(t, fo + 0.3, fo + 0.6)),
                800, 1250, size=42, col="#fef3c7", tcol="#7c2d12", wob=t * 2)
    if t > fo + 0.3:
        bubble_sp(ctx, 330, 1250, 460, "Это не ваш?", fo + 0.3, t)
        thought(ctx, 800, 1000, 380, "спасибо!", seg(t, fo + 0.6, fo + 0.9), 800, 1250, ic_heart2, size=40,
                wob=t * 2)
    step_card(ctx, t, EV["steps"][2], 3, "ПОМОГАЙ\nНЕЗАМЕТНО")


def s5_close(ctx, t, u, D):
    cl = EV["close"]
    ctx.save()
    cam(ctx, t, 540, 1250, 0.9, shake=0.15)
    kitchen(ctx, t)
    p = Npc(random.Random(77), 760, 1900, 1.15, -1)  # мама
    p.style, p.hair, p.shirt, p.item, p.glasses = "bun", "#5a3a22", "#16a34a", "none", True
    npc(ctx, p, t, walking=False, grin=0.5)
    mind(ctx, 300, 1950, 1.0, emo("calm"), t, arms="relax", look=(0.6, 0) if t < cl else (-0.6, 0), phones=True)
    ctx.restore()
    thought(ctx, 760, 1000, 360, "", seg(t, cl - 0.3, cl), 760, 1250, locked=True, wob=t * 2)
    if t > EV["know"]:
        text(ctx, "НЕ ЧИТАТЬ", 760, 1180, 50, "#6b7280", "#fff", 8, alpha=seg(t, EV["know"], EV["know"] + 0.3))
    step_card(ctx, t, EV["steps"][3], 4, "НЕ ЛЕЗЬ\nВ МЫСЛИ БЛИЗКИХ")


def s6_quiet(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, lerp(1500, 1400, seg(u, 0, D)), 0.85, shake=0.1)
    park(ctx, t)
    bench(ctx, 560, 2000, 1.6)
    mind(ctx, 560, 1960, 1.0, emo("calm"), t, arms="relax", legs=False, phones=False)
    ctx.restore()
    rem = 40 * 60 * (1 - seg(t, EV["quiet"], TL.shots[7][0]) * 0.1)
    rr(ctx, 340, 640, 400, 150, 30)
    fill(ctx, "#0b0b12", 0.8)
    text(ctx, "ТИШИНА", 540, 680, 32, "#c4b5fd")
    text(ctx, f"{int(rem // 60):02d}:{int(rem % 60):02d}", 540, 750, 64, "#ffffff")
    step_card(ctx, t, EV["steps"][4], 5, "К ВЕЧЕРУ —\nТИШИНА")


def ic_hand(c, x, y, col, a):
    rr(c, x - 18, y - 6, 36, 32, 10)
    fill(c, col, a)
    for k in range(4):
        rr(c, x - 16 + k * 10, y - 26, 8, 24, 4)
        fill(c, col, a)


def ic_mask(c, x, y, col, a):
    ell(c, x, y, 28, 18)
    fill(c, col, a)
    for sd in (-1, 1):
        ell(c, x + sd * 12, y - 2, 7, 5)
        fill(c, "#0b0b12", a)


def ic_lock2(c, x, y, col, a):
    rr(c, x - 20, y - 4, 40, 30, 6)
    fill(c, col, a)
    c.arc(x, y - 6, 13, math.pi, TAU)
    c.set_line_width(6)
    src(c, col, a)
    c.stroke()


def ic_phones(c, x, y, col, a):
    c.arc(x, y + 4, 22, math.pi, TAU)
    c.set_line_width(6)
    src(c, col, a)
    c.stroke()
    for sd in (-1, 1):
        rr(c, x + sd * 22 - 8, y, 16, 26, 6)
        fill(c, col, a)


def ic_leaf(c, x, y, col, a):
    ell(c, x, y, 14, 24)
    fill(c, col, a)


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА ДНЯ", [
        ("ПОМОГ", "людям — незаметно", 0.7, "#22c55e", "7", ic_hand),
        ("ВЫДАЛ СЕБЯ", "ни разу", 0.0, "#ef4444", "0", ic_mask),
        ("МЫСЛИ БЛИЗКИХ", "не слушал", 0.0, "#a78bfa", "0", ic_lock2),
        ("НАУШНИКИ", "весь день", 1.0, "#f97316", "1/1", ic_phones),
        ("ТИШИНА", "парк, лавка", 0.66, "#facc15", "40 мин", ic_leaf)], EV["tally"])


def s8_done(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1300, 0.9, shake=0.1)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#fef3c7"), (1, "#fde68a")])
    bookshelf(ctx, -100, 500, 500, rows=3, seed=4)
    table_lamp(ctx, 900, 1450, 1.0, on=True)
    poster(ctx, 560, 500, 300, 380, 2, 0.03)
    plant(ctx, 1150, 1700, 1.0, t)
    rug(ctx, 540, 1950, 600, 90, "#9f1239")
    sofa(ctx, 540, 1850, 900, "#0e7490")
    mind(ctx, 540, 1800, 1.0, emo("happy"), t, arms="relax", legs=False)
    ctx.restore()


def s9_night(ctx, t, u, D):
    al, nb = EV["alien"], EV["nobody"]
    ctx.save()
    cam(ctx, t, 540, 1300, lerp(0.85, 1.0, seg(u, 0, D)), shake=0.15)
    bedroom(ctx, t, 0.8)
    ctx.save()
    ctx.translate(80, 1260)
    hero_head(ctx, 0, 0, 100, emo("worry") if t > al else emo("calm"), t, look=(0.6, -0.3), rim="#c4b5fd", rim_a=0.4)
    ctx.restore()
    ctx.restore()
    if t > al:
        thought(ctx, 640, 900, 360, "...", seg(t, al, al + 0.4), 500, 1150, size=80, col="#e9d5ff", wob=t * 2)
    if t > nb:
        text(ctx, "ДОМА НИКОГО", 540, 1350, 60, "#c4b5fd", "#000", 8, alpha=seg(t, nb, nb + 0.3))


def s10_voice(ctx, t, u, D):
    fi = EV["finally"]
    ctx.save()
    cam(ctx, t, 540, 1300, lerp(1.0, 1.15, seg(u, 0, D)), shake=0.2)
    bedroom(ctx, t, 1.0)
    ctx.save()
    ctx.translate(120, 1260)
    hero_head(ctx, 0, 0, 100, emo("fear"), t, look=(0.6, -0.5), rim="#c4b5fd", rim_a=0.6)
    ctx.restore()
    ctx.restore()
    ctx.rectangle(0, 0, W, H)
    fill(ctx, "#000", 0.35)
    thought(ctx, 540, 900, 860, typed("Наконец-то\nон меня слышит", t, fi - 0.2, fi + 1.0) if t > fi - 0.2 else "\n",
            1.0, 540, 1400, size=72, col="#e9d5ff", tcol="#3b0764", wob=t * 2)


def s11_own(ctx, t, u, D):
    ow = EV["own"]
    ctx.save()
    k = ease(seg(t, ow - 0.6, ow + 0.4))
    cam(ctx, t, 540, lerp(1300, 1150, k), lerp(0.85, 1.2, k), shake=0.3)
    bedroom(ctx, t, 0.9)
    mind(ctx, 540, 1950, 1.0, emo("fear"), t, arms="shock", tremble=0.7, look=(0, -0.8))
    thought(ctx, 540, 1100, 520, "я здесь", 1.0, 540, 1400, size=60, col="#e9d5ff", wob=t * 2)
    ctx.restore()
    if t > ow:  # стрелка от облачка в голову героя
        a = seg(t, ow, ow + 0.3)
        text(ctx, "ИЗ ТВОЕЙ ГОЛОВЫ", 540, 600, 66, "#e9d5ff", "#3b0764", 10, alpha=a)


def s12_reflect(ctx, t, u, D):
    ye, sw = EV["years"], EV["swap"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        ctx.save()
        cam(ctx, t, 540, 1150, lerp(0.95, 1.15, seg(u, 0, ec)), shake=0.2)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0f0a1f"), (1, "#020617")])
        rr(ctx, 100, 300, 880, 1300, 14)  # окно-отражение
        fill(ctx, "#0b1022")
        for k in range(8):
            rr(ctx, 120 + k * 110, 1100 - (k % 3) * 150, 90, 500 + (k % 3) * 150, 4)
            fill(ctx, "#111827")
        ctx.save()  # отражение — другая мимика
        rr(ctx, 100, 300, 880, 1300, 14)
        ctx.clip()
        ctx.push_group()
        hero(ctx, 540, 1700, 1.4, emo("sly"), t, arms="relax", legs=False, rim="#a78bfa", rim_a=0.9, hood=CYAN)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(0.55)
        ctx.restore()
        line(ctx, 540, 300, 540, 1600, 14, "#334155")
        line(ctx, 100, 900, 980, 900, 14, "#334155")
        rr(ctx, 100, 300, 880, 1300, 14)
        ctx.set_line_width(20)
        src(ctx, "#334155")
        ctx.stroke()
        mind(ctx, 540, 2350, 1.4, emo("fear"), t, arms="relax", legs=False, back=True)
        ctx.restore()
        if t > ye:
            a = seg(t, ye, ye + 0.3)
            text(ctx, "20 ЛЕТ ВНУТРИ", 540, 420, 80, "#e9d5ff", "#3b0764", 12, alpha=a)
        if t > sw:
            a = seg(t, sw, sw + 0.3)
            text(ctx, "ПОМЕНЯЕМСЯ?", 540, 1300, 76, "#f472b6", "#000", 10, alpha=a)
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
        text(ctx, "Кто живёт в твоей голове?", 0, 180, 60, "#c4b5fd")
    ctx.restore()


SCENES = [s0_hook, s1_lift, s2_silent, s3_phones, s4_help, s5_close, s6_quiet, s7_tally, s8_done, s9_night,
          s10_voice, s11_own, s12_reflect]
LABELS = {9: "НОЧЬ", 10: "НОЧЬ", 11: "НОЧЬ", 12: "НОЧЬ"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("семи", "людям"), "7 людям"), (("ноль", "раз."), "0 раз"), (("ноль", "раз"), "0 раз"),
         (("сорок", "минут"), "40 минут"), (("двадцать", "лет."), "20 лет"), (("двадцать", "лет"), "20 лет")]


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
        text(ctx, "ЧИТАЕШЬ МЫСЛИ", 0, 10, 110, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -300, 90, 600, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "ОДИН ДЕНЬ?", 0, 155, 100, "#ffffff")
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
