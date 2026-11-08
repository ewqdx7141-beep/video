"""Серия 30 «Закрытый ТЦ» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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










# ================================================================== ЗАКРЫТЫЙ ТЦ
PINK = ("#db2777", "#9d174d")
SHOPS = (("МОДА", "#ec4899"), ("ОБУВЬ", "#f59e0b"), ("КОФЕ", "#92400e"), ("ТЕХНО", "#2563eb"), ("КНИГИ", "#16a34a"),
         ("ИГРУШКИ", "#ef4444"), ("ОПТИКА", "#0891b2"), ("СПОРТ", "#7c3aed"))


def shopper(ctx, x, y, sc, e, t, arms="relax", look=(0, 0), walk=None, back=False, legs=True, tremble=0.0, item=None):
    hero(ctx, x, y, sc, e, t, arms=arms, look=look, walk=walk, back=back, legs=legs, tremble=tremble,
         rim="#fbcfe8", rim_a=0.6, hood=PINK, hand_item=item)


def bag_item(c, x, y, s=1.0):
    rr(c, x - 40 * s, y, 80 * s, 100 * s, 6 * s)
    fill(c, "#f472b6")
    c.arc(x, y, 24 * s, math.pi, TAU)
    c.set_line_width(6 * s)
    src(c, "#9d174d")
    c.stroke()
    text(c, "М", x, y + 50 * s, 40 * s, "#ffffff")


def shopfront(ctx, x, y, w, h, name, col, t, grille=1.0, lit=0.0, dusty=0.0, seed=0, mann=True):
    rr(ctx, x, y - 90, w, 80, 6)
    fill(ctx, col)
    text(ctx, name, x + w / 2, y - 50, 44, "#ffffff")
    if lit:
        glow(ctx, x + w / 2, y - 50, w * 0.6, col, 0.35 * lit)
    rr(ctx, x, y, w, h, 4)
    fill(ctx, "#1f2937")
    rr(ctx, x + 10, y + 10, w - 20, h - 20, 4)
    fill(ctx, mixh("#e0f2fe", "#94a3b8", dusty))
    r = random.Random(seed)
    if mann:
        for k in range(2):
            mannequin(ctx, x + w * (0.3 + 0.4 * k), y + h - 20, 0.55, 0.0, 0.2 * k,
                      color=mixh("#e9e4dc", "#a8a29e", dusty))
            rr(ctx, x + w * (0.3 + 0.4 * k) - 40, y + h - 220, 80, 110, 14)  # одежда на манекене
            fill(ctx, mixh(r.choice(("#f472b6", "#60a5fa", "#facc15", "#a78bfa")), "#78716c", dusty * 0.7))
    else:
        for k in range(3):
            rr(ctx, x + 30, y + 60 + k * 90, w - 60, 10, 2)
            fill(ctx, "#94a3b8")
            for j in range(5):
                rr(ctx, x + 40 + j * (w - 80) / 5, y + 20 + k * 90, (w - 100) / 5, 40, 4)
                fill(ctx, r.choice(("#ef4444", "#22c55e", "#3b82f6", "#f59e0b")))
    if lit:
        rr(ctx, x + 10, y + 10, w - 20, h - 20, 4)
        fill(ctx, "#fef9c3", 0.25 * lit)
    if grille:
        gh = (h - 10) * grille
        for k in range(int(gh / 26)):
            line(ctx, x + 6, y + 6 + k * 26, x + w - 6, y + 6 + k * 26, 4, "#9ca3af", 0.9)
        for k in range(int(w / 40)):
            line(ctx, x + 6 + k * 40, y + 6, x + 6 + k * 40, y + 6 + gh, 2, "#6b7280", 0.8)
    if dusty:
        for k in range(3):  # паутина
            cx, cy = x + 10, y + 10
            for j in range(5):
                a = j * math.pi / 10
                line(ctx, cx, cy, cx + math.cos(a) * 80, cy + math.sin(a) * 80, 1.5, "#e5e7eb", 0.5 * dusty)
            for rr_ in (30, 55, 80):
                ctx.arc(cx, cy, rr_, 0, math.pi / 2)
                ctx.set_line_width(1.5)
                src(ctx, "#e5e7eb", 0.4 * dusty)
                ctx.stroke()


def exit_sign(ctx, x, y, t):
    rr(ctx, x, y, 200, 70, 8)
    fill(ctx, "#16a34a")
    glow(ctx, x + 100, y + 35, 160, "#22c55e", 0.45)
    text(ctx, "ВЫХОД", x + 80, y + 35, 32, "#ffffff")
    line(ctx, x + 150, y + 35, x + 185, y + 35, 6, "#ffffff")
    line(ctx, x + 185, y + 35, x + 170, y + 22, 6, "#ffffff")
    line(ctx, x + 185, y + 35, x + 170, y + 48, 6, "#ffffff")


def mall(ctx, t, dark=0.85, dusty=0.0, lit_idx=(), grille=1.0, x0=-1200, x1=2400, esc=True, fountain=True):
    vgrad(ctx, x0 - 600, -800, x1 - x0 + 1200, 3600, [(0, "#e2e8f0"), (1, "#cbd5e1")])
    ctx.rectangle(x0 - 600, 100, x1 - x0 + 1200, 60)  # стеклянная крыша-фермы
    fill(ctx, "#94a3b8")
    for k in range(int((x1 - x0) / 200) + 6):
        line(ctx, x0 - 600 + k * 200, 0, x0 - 600 + k * 200 + 100, 160, 6, "#94a3b8")
    for fl, fy in enumerate((380, 1100)):  # два этажа витрин
        for k in range(int((x1 - x0) / 420) + 1):
            idx = fl * 10 + k
            nm, col = SHOPS[(idx + 3) % len(SHOPS)]
            shopfront(ctx, x0 + k * 420 + 20, fy, 380, 520, nm, col, t, grille=0 if idx in lit_idx else grille,
                      lit=1.0 if idx in lit_idx else 0.0, dusty=dusty, seed=idx, mann=(idx % 2 == 0))
        rr(ctx, x0 - 600, fy + 520, x1 - x0 + 1200, 40, 4)  # балкон-перила
        fill(ctx, "#f1f5f9")
        line(ctx, x0 - 600, fy + 500, x1 + 600, fy + 500, 6, "#94a3b8")
    for k in range(int((x1 - x0) / 840) + 1):  # баннеры распродаж
        bx = x0 + 300 + k * 840
        line(ctx, bx, 160, bx, 240, 3, "#64748b")
        line(ctx, bx + 160, 160, bx + 160, 240, 3, "#64748b")
        rr(ctx, bx - 20, 240, 200, 110, 6)
        fill(ctx, mixh("#dc2626", "#78716c", dusty))
        text(ctx, "-50%", bx + 80, 295, 50, "#ffffff")
    if esc:  # эскалатор
        ctx.move_to(200, 1640)
        ctx.line_to(320, 1640)
        ctx.line_to(900, 920)
        ctx.line_to(780, 920)
        ctx.close_path()
        fill(ctx, "#475569")
        for k in range(14):
            line(ctx, 210 + k * 44, 1630 - k * 52, 320 + k * 44, 1630 - k * 52, 4, "#1f2937")
        line(ctx, 190, 1560, 770, 840, 12, "#111827")
        line(ctx, 330, 1560, 910, 840, 12, "#111827")
    ctx.rectangle(x0 - 600, 1640, x1 - x0 + 1200, 1200)  # пол-плитка
    fill(ctx, mixh("#f1f5f9", "#a8a29e", dusty))
    for k in range(int((x1 - x0) / 160) + 10):
        line(ctx, x0 - 600 + k * 160, 1640, x0 - 600 + k * 160 - 200, 2800, 2, "#cbd5e1")
    for j in range(6):
        line(ctx, x0 - 600, 1700 + j * 150, x1 + 600, 1700 + j * 150, 2, "#cbd5e1")
    if fountain:
        ell(ctx, 1500, 1820, 300, 70)
        fill(ctx, "#94a3b8")
        ell(ctx, 1500, 1810, 260, 55)
        fill(ctx, "#7dd3fc" if not dusty else "#78716c")
        rr(ctx, 1480, 1600, 40, 210, 10)
        fill(ctx, "#cbd5e1")
        if not dusty and dark < 0.5:
            for k in range(6):
                a = (t * 1.5 + k / 6) % 1
                ctx.arc(1500 + math.cos(k) * 120 * a, 1600 - 140 * math.sin(a * math.pi), 8, 0, TAU)
                fill(ctx, "#bae6fd", 0.8)
    for x in (x0 + 100, x1 - 300):
        plant(ctx, x, 1720, 1.0, t, "#78350f")
        bench(ctx, x + 250, 1760, 1.0)
    exit_sign(ctx, x0 + 700, 980, t)
    exit_sign(ctx, x1 - 600, 980, t)
    if dusty:
        r = random.Random(3)
        for k in range(30):
            ell(ctx, r.uniform(x0, x1), r.uniform(1660, 2600), r.uniform(60, 200), 14)
            fill(ctx, "#78716c", 0.25 * dusty)
        for k in range(5):  # выцветшие постеры
            ctx.save()
            ctx.translate(x0 + 400 + k * 600, 1250)
            ctx.rotate(0.06 * (k % 2 * 2 - 1))
            rr(ctx, -80, -100, 160, 200, 4)
            fill(ctx, "#fef3c7", 0.8)
            text(ctx, "2011", 0, -40, 34, "#a8a29e")
            text(ctx, "СКИДКИ", 0, 20, 28, "#a8a29e")
            ctx.restore()
    if dark:
        ctx.rectangle(x0 - 1200, -1200, x1 - x0 + 2400, 4800)
        fill(ctx, "#020617", dark)


def lamp_spots(ctx, spots, a=1.0):
    for (x, y, r) in spots:
        glow(ctx, x, y, r, "#fef3c7", 0.35 * a)


def receipt(ctx, x, y, s=1.0, rot=0.0, date=None):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ctx.move_to(-40, -90)
    ctx.line_to(40, -90)
    ctx.line_to(40, 90)
    for k in range(8):
        ctx.line_to(40 - k * 10 - 5, 96 if k % 2 == 0 else 90)
    ctx.line_to(-40, 90)
    ctx.close_path()
    fill(ctx, "#ffffff")
    for k in range(7):
        line(ctx, -30, -70 + k * 20, 30 - (k % 3) * 10, -70 + k * 20, 3, "#9ca3af")
    if date:
        text(ctx, date, 0, 70, 13, "#b91c1c")
    ctx.restore()


def guard(ctx, x, y, sc, t, facing=-1, light=True, stare=0.0):
    p = Npc(random.Random(41), x, y, sc, facing)
    p.shirt, p.pants, p.style, p.item, p.mustache = "#1e3a8a", "#111827", "cap", "none", True
    npc(ctx, p, t, walking=False, stare=stare)
    rr(ctx, x - 30 * sc, y - 300 * sc, 60 * sc, 26 * sc, 4 * sc)  # нашивка
    fill(ctx, "#facc15")
    text(ctx, "ОХРАНА", x, y - 287 * sc, 12 * sc, "#111827")
    if light:
        lx, ly = x + facing * 70 * sc, y - 200 * sc
        rr(ctx, lx - 10 * sc, ly - 30 * sc, 20 * sc, 60 * sc, 6 * sc)
        fill(ctx, "#111")
        glow(ctx, lx + facing * 120 * sc, ly, 260 * sc, "#fef9c3", 0.5)


def security_post(ctx, t):
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#1e293b"), (1, "#0f172a")])
    for i in range(4):  # стена мониторов
        for j in range(3):
            x, y = 160 + i * 200, 400 + j * 170
            rr(ctx, x, y, 180, 150, 8)
            fill(ctx, "#111827")
            rr(ctx, x + 8, y + 8, 164, 134, 4)
            fill(ctx, "#334155")
            for k in range(4):
                line(ctx, x + 8, y + 20 + k * 30 + (t * 30) % 30, x + 172, y + 20 + k * 30 + (t * 30) % 30, 2,
                     "#64748b", 0.5)
            text(ctx, f"CAM {i * 3 + j + 1:02d}", x + 50, y + 25, 16, "#22c55e")
            ctx.arc(x + 160, y + 22, 5, 0, TAU)
            fill(ctx, "#ef4444" if (t * 2 + i + j) % 1 < 0.5 else "#7f1d1d")
    rr(ctx, -200, 1200, 1500, 60, 8)
    fill(ctx, "#475569")
    rr(ctx, 200, 1150, 160, 50, 8)  # рация
    fill(ctx, "#111827")
    for k in range(5):  # ключи на доске
        line(ctx, 1000 + k * 40, 600, 1000 + k * 40, 660, 3, "#9ca3af")
        ctx.arc(1000 + k * 40, 670, 10, 0, TAU)
        fill(ctx, "#facc15")
    ctx.rectangle(-1200, 1700, 3600, 1000)
    fill(ctx, "#334155")


def phone_batt(t, pct=3, bright=1.0, calling=False):
    def f(c, x, y, w, h):
        vgrad(c, x, y, w, h, [(0, "#111827"), (1, "#1f2937")])
        text(c, f"{pct}%", x + w / 2, y + 160, 120, "#ef4444")
        rr(c, x + w / 2 - 120, y + 260, 240, 100, 14)
        c.set_line_width(8)
        src(c, "#e5e7eb")
        c.stroke()
        rr(c, x + w / 2 - 110, y + 270, 24, 80, 6)
        fill(c, "#ef4444" if (t * 2) % 1 < 0.6 else "#7f1d1d")
        text(c, "Яркость", x + 60, y + 470, 34, "#9ca3af", align="left")
        line(c, x + 60, y + 530, x + w - 60, y + 530, 10, "#374151")
        bx = x + 60 + (w - 120) * bright
        line(c, x + 60, y + 530, bx, y + 530, 10, "#facc15")
        c.arc(bx, y + 530, 22, 0, TAU)
        fill(c, "#ffffff")
        if calling:
            rr(c, x + 40, y + 640, w - 80, 160, 24)
            fill(c, "#16a34a")
            text(c, "Вызов: 112", x + w / 2, y + 700, 44, "#ffffff")
            text(c, "1 звонок", x + w / 2, y + 760, 32, "#dcfce7")
        if bright < 0.3:
            c.rectangle(x, y, w, h)
            fill(c, "#000", 0.35)
    return f


def mixh(c1, c2, k):
    a, b = hexc(c1), hexc(c2)
    return "#%02x%02x%02x" % tuple(int(255 * (a[i] + (b[i] - a[i]) * clamp(k))) for i in range(3))


# ================================================================== СЦЕНЫ
def fitting_room(ctx, t, dark=0.0):
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#fdf2f8"), (1, "#fce7f3")])
    rr(ctx, 300, 300, 480, 1100, 10)  # зеркало
    lgrad(ctx, 300, 300, 780, 1400, [(0, "#e2e8f0"), (0.5, "#f8fafc"), (1, "#cbd5e1")])
    ctx.fill()
    line(ctx, 360, 360, 480, 640, 10, "#ffffff", 0.6)
    for k in range(3):  # крючки с одеждой
        x = 870 + k * 70
        line(ctx, x, 500, x, 540, 6, "#9ca3af")
        rr(ctx, x - 40, 540, 80, 200 - k * 30, 14)
        fill(ctx, ("#f472b6", "#60a5fa", "#facc15")[k])
    line(ctx, -200, 160, 1300, 160, 12, "#9ca3af")  # штанга шторки
    for k in range(10):
        rr(ctx, -200 + k * 40, 170, 36, 1500, 12)
        fill(ctx, "#be185d" if k % 2 else "#9d174d")
    rr(ctx, 100, 1500, 880, 80, 10)  # пуф
    fill(ctx, "#78350f")
    ctx.rectangle(-800, 1700, 2700, 1200)
    fill(ctx, "#e5e7eb")
    rr(ctx, 700, 1600, 200, 120, 14)  # гора вещей
    fill(ctx, "#a78bfa")
    rr(ctx, 760, 1560, 160, 80, 14)
    fill(ctx, "#34d399")
    if dark:
        ctx.rectangle(-1200, -1200, 3600, 4800)
        fill(ctx, "#020617", dark)


def s0_hook(ctx, t, u, D):
    wk, lo = EV["woke"], EV["lightsoff"]
    dk = seg(t, lo - 0.6, lo + 0.2) * 0.8
    ctx.save()
    cam(ctx, t, 540, 1250, lerp(0.9, 1.0, seg(u, 0, D)), shake=0.15 + 0.6 * seg(t, wk, wk + 0.2) * (1 - seg(t, wk + 0.3, wk + 0.8)))
    fitting_room(ctx, t, dk)
    sleepy = t < wk
    shopper(ctx, 540, 1550, 1.0, emo("sleep") if sleepy else emo("shock"), t, arms="relax" if sleepy else "shock",
            legs=False, item=(lambda c, x, y: bag_item(c, x, y, 0.8)))
    if sleepy:
        text(ctx, "z", 700, 1050 - (t * 60) % 120, 60, "#9d174d", alpha=0.7)
    ctx.restore()
    if t > lo:
        glow(ctx, 540, 1100, 400, "#fbcfe8", 0.25)


def s1_frozen(ctx, t, u, D):
    pc = EV["pct"]
    ctx.save()
    cam(ctx, t, lerp(500, 700, seg(u, 0, D)), 1250, 0.75, shake=0.15)
    mall(ctx, t, dark=0.75, grille=ease(seg(t, EV["grilles"] - 0.6, EV["grilles"] + 0.4)))
    lamp_spots(ctx, ((300, 1000, 300), (1700, 1000, 300)))
    shopper(ctx, 650, 2050, 1.0, emo("worry"), t, arms="relax", look=(-0.6, -0.4),
            item=(lambda c, x, y: bag_item(c, x, y, 0.8)))
    ctx.restore()
    if t > pc - 0.4:
        s = ease(seg(t, pc - 0.4, pc))
        ctx.save()
        ctx.translate(800, lerp(2500, 1050, s))
        ctx.scale(0.55, 0.55)
        phone_body(ctx, 0, 0, 480, 900, phone_batt(t, 3))
        ctx.restore()


def s2_vitrines(ctx, t, u, D):
    vi = EV["vitrines"]
    ctx.save()
    hx = lerp(-400, 900, seg(u, 0, D))
    cam(ctx, t, hx + 100, 1350, 0.8, shake=0.15)
    mall(ctx, t, dark=0.72, lit_idx=(10, 11, 12, 13), esc=False, x0=-1200, x1=2600)
    lamp_spots(ctx, [(-1000 + k * 420 + 200, 1360, 260) for k in range(10)], a=1.0)
    shopper(ctx, hx, 2050, 1.0, emo("determined"), t, arms="relax", walk=t * 6, item=(lambda c, x, y: bag_item(c, x, y, 0.8)))
    ctx.restore()
    step_card(ctx, t, EV["steps"][0], 1, "НЕ БЕГАЙ\nИДИ ВДОЛЬ СВЕТА")


def s3_post(ctx, t, u, D):
    po = EV["post"]
    ctx.save()
    cam(ctx, t, 540, 1250, 0.85, shake=0.15)
    mall(ctx, t, dark=0.6, esc=False)
    rr(ctx, 160, 600, 760, 900, 20)  # стенд-план ТЦ
    fill(ctx, "#f8fafc")
    rr(ctx, 160, 600, 760, 100, 20)
    fill(ctx, "#1e3a8a")
    text(ctx, "ПЛАН 1 ЭТАЖА", 540, 650, 44, "#ffffff")
    r = random.Random(4)
    for i in range(12):
        rr(ctx, 200 + (i % 4) * 175, 740 + (i // 4) * 200, 160, 180, 6)
        fill(ctx, r.choice(("#fbcfe8", "#bfdbfe", "#bbf7d0", "#fde68a")))
    ctx.arc(420, 1300, 22, 0, TAU)
    fill(ctx, "#ef4444")
    text(ctx, "ВЫ ЗДЕСЬ", 420, 1350, 26, "#ef4444")
    if t > po:
        a = seg(t, po, po + 0.3)
        rr(ctx, 720, 1160, 180, 120, 10)
        fill(ctx, "#facc15", a)
        text(ctx, "ОХРАНА", 810, 1220, 30, "#111827", alpha=a)
        ctx.move_to(440, 1300)
        ctx.line_to(600, 1300)
        ctx.line_to(600, 1220)
        ctx.line_to(710, 1220)
        ctx.set_line_width(8)
        ctx.set_dash([18, 12])
        src(ctx, "#16a34a", a)
        ctx.stroke()
        ctx.set_dash([])
    if t > EV["parking"]:
        a = seg(t, EV["parking"], EV["parking"] + 0.3)
        rr(ctx, 200, 1380, 160, 90, 10)
        fill(ctx, "#2563eb", a)
        text(ctx, "P", 280, 1425, 60, "#ffffff", alpha=a)
    shopper(ctx, 1000, 2100, 1.0, emo("calm"), t, arms="relax", look=(-0.8, -0.3))
    ctx.restore()
    step_card(ctx, t, EV["steps"][1], 2, "ИЩИ ПОСТ\nОХРАНЫ")


def s4_battery(ctx, t, u, D):
    br, ca = EV["bright"], EV["call"]
    ctx.save()
    cam(ctx, t, 540, 1250, 0.85, shake=0.1)
    mall(ctx, t, dark=0.8, esc=True)
    ctx.restore()
    bright = 1 - 0.9 * ease(seg(t, br - 0.2, br + 0.6))
    hands_phone(ctx, t, phone_batt(t, 3, bright, calling=t > ca), tremble=0.3, sc=0.75, cy=1050, hood=PINK)
    step_card(ctx, t, EV["steps"][2], 3, "БЕРЕГИ ЗАРЯД\n1 ЗВОНОК")


def alarm_door(ctx, x, y, t):
    rr(ctx, x - 200, y - 700, 400, 700, 8)
    fill(ctx, "#9ca3af")
    line(ctx, x, y - 700, x, y, 6, "#6b7280")
    rr(ctx, x - 160, y - 380, 320, 30, 10)  # штанга «антипаника»
    fill(ctx, "#dc2626")
    rr(ctx, x - 180, y - 860, 360, 120, 10)
    fill(ctx, "#dc2626")
    text(ctx, "ПОЖАРНЫЙ ВЫХОД", x, y - 820, 30, "#ffffff")
    text(ctx, "ДВЕРЬ НА СИГНАЛИЗАЦИИ", x, y - 775, 22, "#fee2e2")
    on = (t * 2) % 1 < 0.5
    ctx.arc(x + 230, y - 760, 30, 0, TAU)
    fill(ctx, "#ef4444" if on else "#7f1d1d")
    if on:
        glow(ctx, x + 230, y - 760, 120, "#ef4444", 0.6)


def s5_alarm(ctx, t, u, D):
    al = EV["alarm"]
    ctx.save()
    cam(ctx, t, 540, 1250, 0.85, shake=0.15)
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#334155"), (1, "#1e293b")])
    for k in range(-4, 10):
        line(ctx, k * 200, 0, k * 200, 1700, 3, "#475569")
    alarm_door(ctx, 540, 1700, t)
    ctx.rectangle(-1200, 1700, 3600, 1000)
    fill(ctx, "#475569")
    for k in range(4):  # коробки в служебном коридоре
        rr(ctx, -200 + k * 140, 1580 - (k % 2) * 60, 130, 120 + (k % 2) * 60, 6)
        fill(ctx, "#a16207")
    shopper(ctx, 980, 2100, 1.0, emo("determined"), t, arms="relax", look=(-0.7, -0.4))
    if t > EV["steps"][3] + 0.6:
        crossmark(ctx, 540, 1300, 3.0)
    ctx.restore()
    if t > al:
        text(ctx, "ВИУ-ВИУ — ТОЛЬКО ТЕБЕ", 540, 700, 54, "#fca5a5", "#000", 8, alpha=seg(t, al, al + 0.3))
    step_card(ctx, t, EV["steps"][3], 4, "НЕ ТРОГАЙ\nДВЕРИ С СИРЕНОЙ")


def s6_receipts(ctx, t, u, D):
    ch = EV["check"]
    ctx.save()
    hx = lerp(0, 1300, seg(u, 0, D))
    cam(ctx, t, hx + 100, 1350, 0.8, shake=0.15)
    mall(ctx, t, dark=0.65, esc=False, x0=-1200, x1=3000)
    lamp_spots(ctx, [(-1000 + k * 420 + 200, 1360, 260) for k in range(10)], a=0.8)
    n = 0
    for k in range(9):
        rx = -200 + k * 200
        if rx < hx - 40 or t > ch + k * 0.15:
            receipt(ctx, rx, 1900 + (k % 2) * 40, 0.6, 0.3 * (k % 3 - 1))
            n += 1
    shopper(ctx, hx, 2050, 1.0, emo("calm"), t, arms="give", walk=t * 6, look=(0.3, 0.4))
    ctx.restore()
    rr(ctx, 340, 640, 400, 150, 30)
    fill(ctx, "#0b0b12", 0.85)
    text(ctx, "ЧЕКОВ", 540, 680, 32, "#fbcfe8")
    text(ctx, str(min(9, n)), 540, 750, 70, "#ffffff")
    step_card(ctx, t, EV["steps"][4], 5, "МЕТКИ\nЧЕК НА ПОВОРОТЕ")


def ic_batt(c, x, y, col, a):
    rr(c, x - 26, y - 14, 46, 28, 5)
    c.set_line_width(4)
    src(c, col, a)
    c.stroke()
    rr(c, x - 22, y - 10, 8, 20, 2)
    fill(c, col, a)


def ic_call(c, x, y, col, a):
    c.arc(x, y, 22, 0.6, 2.6)
    c.set_line_width(10)
    src(c, col, a)
    c.stroke()


def ic_siren(c, x, y, col, a):
    c.arc(x, y + 6, 20, math.pi, TAU)
    fill(c, col, a)
    rr(c, x - 24, y + 6, 48, 12, 3)
    fill(c, col, a)


def ic_receipt(c, x, y, col, a):
    rr(c, x - 16, y - 24, 32, 48, 3)
    fill(c, col, a)
    for k in range(3):
        line(c, x - 10, y - 12 + k * 12, x + 10, y - 12 + k * 12, 3, "#0b0b12", a)


def ic_shield(c, x, y, col, a):
    c.move_to(x, y - 26)
    c.line_to(x + 22, y - 16)
    c.curve_to(x + 22, y + 10, x + 10, y + 22, x, y + 28)
    c.curve_to(x - 10, y + 22, x - 22, y + 10, x - 22, y - 16)
    c.close_path()
    fill(c, col, a)


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА НОЧИ", [
        ("ЗАРЯД", "сохранён на звонок", 0.03, "#ef4444", "3%", ic_batt),
        ("ЗВОНКИ", "только один", 0.1, "#22c55e", "1", ic_call),
        ("СИРЕНЫ", "ни одной", 0.0, "#f97316", "0", ic_siren),
        ("ЧЕКИ-МЕТКИ", "на поворотах", 0.9, "#f8fafc", "9", ic_receipt),
        ("ПОСТ ОХРАНЫ", "найден", 1.0, "#facc15", "1/1", ic_shield)], EV["tally"])


def s8_guard(ctx, t, u, D):
    op = EV["open"]
    ctx.save()
    cam(ctx, t, 540, 1300, 0.9, shake=0.15)
    security_post(ctx, t)
    k = ease(seg(t, op - 0.3, op + 0.6))
    rr(ctx, 700, 700, 380, 1000, 6)  # дверь поста
    fill(ctx, "#fef9c3" if k > 0 else "#475569")
    rr(ctx, 700, 700, 380 * (1 - k), 1000, 6)
    fill(ctx, "#64748b")
    if k > 0:
        guard(ctx, 890, 1950, 1.1, t, -1, light=True)
    shopper(ctx, 300, 2050, 1.0, emo("happy"), t, arms="cheer", item=None)
    ctx.restore()


def s9_how(ctx, t, u, D):
    ho = EV["how"]
    ctx.save()
    cam(ctx, t, 540, 1300, lerp(0.9, 1.05, seg(u, 0, D)), shake=0.15)
    security_post(ctx, t)
    guard(ctx, 820, 2000, 1.2, t, -1, light=True, stare=0.8)
    shopper(ctx, 300, 2050, 1.0, emo("worry") if t > ho - 0.5 else emo("calm"), t, arms="relax",
            item=(lambda c, x, y: bag_item(c, x, y, 0.8)))
    ctx.restore()
    if t > ho - 1.2:
        a = seg(t, ho - 1.2, ho - 0.9)
        rr(ctx, 260, 640, 660, 120, 30)
        fill(ctx, "#ffffff", a)
        text(ctx, "Как вы сюда попали?", 590, 700, 46, "#111827", alpha=a)


def s10_closed(ctx, t, u, D):
    ye = EV["years"]
    ctx.save()
    cam(ctx, t, 540, 1150, 0.8, shake=0.15)
    mall(ctx, t, dark=0.35, dusty=seg(t, ye - 0.5, ye + 1.0), esc=True, grille=1 - seg(t, ye - 0.5, ye + 1.0))
    ctx.restore()
    if t > ye:
        a = seg(t, ye, ye + 0.3)
        rr(ctx, 140, 640, 800, 200, 20)
        fill(ctx, "#7f1d1d", 0.92 * a)
        text(ctx, "ЗАКРЫТО С 2011", 540, 720, 70, "#ffffff", alpha=a)
        text(ctx, "15 ЛЕТ", 540, 800, 50, "#fecaca", alpha=a)


def s11_dust(ctx, t, u, D):
    mn = EV["mann"]
    ctx.save()
    k = ease(seg(t, mn - 0.3, mn + 1.0))
    cam(ctx, t, lerp(540, 230, k), lerp(1150, 1300, k), lerp(0.8, 1.4, k), shake=0.15)
    mall(ctx, t, dark=0.3, dusty=1.0, esc=True, grille=0.0)
    shopper(ctx, 1100, 2100, 1.0, emo("fear"), t, arms="shock", tremble=0.5,
            item=(lambda c, x, y: bag_item(c, x, y, 0.8)))
    ctx.restore()


def s12_receipt(ctx, t, u, D):
    bg, dt = EV["bag"], EV["date"]
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        ctx.save()
        cam(ctx, t, 540, 1050, lerp(0.95, 1.15, seg(u, 0, ec)), shake=0.2)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#44403c"), (1, "#1c1917")])
        for k in range(40):  # пыль в луче
            r = random.Random(k)
            ctx.arc(r.uniform(0, 1080), (r.uniform(0, 2000) + t * 20) % 2000, r.uniform(2, 5), 0, TAU)
            fill(ctx, "#e7e5e4", 0.3)
        ctx.save()
        ctx.translate(320, 1300)
        ctx.scale(4, 4)
        bag_item(ctx, 0, -40, 1.0)
        ctx.restore()
        receipt(ctx, 720, 1000, 3.4, 0.08, date="08.11.2026" if t > dt - 0.3 else None)
        ctx.restore()
        if t > dt:
            a = seg(t, dt, dt + 0.3)
            text(ctx, "СЕГОДНЯ", 540, 600, 90, "#ef4444", "#000", 12, alpha=a)
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
        text(ctx, "Кто тебе продал эту вещь?", 0, 180, 60, "#f9a8d4")
    ctx.restore()


SCENES = [s0_hook, s1_frozen, s2_vitrines, s3_post, s4_battery, s5_alarm, s6_receipts, s7_tally, s8_guard, s9_how,
          s10_closed, s11_dust, s12_receipt]
LABELS = {10: "ПРАВДА", 11: "ПРАВДА", 12: "ПРАВДА"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("три", "процента"), "3%"), (("один",), "1"), (("ноль",), "0"), (("девять",), "9"),
         (("пятнадцать", "лет"), "15 лет")]


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
        text(ctx, "ЗАСТРЯЛ НОЧЬЮ", 0, 10, 110, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -330, 90, 660, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "В ТЦ?", 0, 155, 100, "#ffffff")
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
