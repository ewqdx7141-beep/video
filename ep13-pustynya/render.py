"""Серия 13 «Пустыня» (что делать, сверка запасов): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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



# ================================================================== ПУСТЫНЯ
DUNE = "#e9b872"
DUNE_D = "#c98e4a"
ROBE_D = ("#f5f5f4", "#d6d3d1")     # светлая длинная одежда героя от солнца


def traveler(ctx, x, y, sc, e, t, arms="relax", walk=None, look=(0, 0), back=False, tremble=0.0, item=None,
             legs=True, covered=False, rim="#fde68a"):
    hero(ctx, x, y, sc, e, t, arms=arms, walk=walk, look=look, back=back, tremble=tremble, rim=rim, rim_a=0.6,
         hood=ROBE_D if covered else ("#0ea5e9", "#0369a1"), hand_item=item, legs=legs)
    if covered and not back:  # платок на голове
        hy = y - (455 if legs else 285) * sc
        ctx.arc(x, hy - 10 * sc, 128 * sc, math.pi * 1.0, math.pi * 2.0)
        ctx.close_path()
        fill(ctx, "#f5f5f4")
        ctx.move_to(x - 120 * sc, hy)
        ctx.line_to(x - 150 * sc, hy + 160 * sc)
        ctx.line_to(x - 90 * sc, hy + 60 * sc)
        fill(ctx, "#e7e5e4")
        rr(ctx, x - 128 * sc, hy - 30 * sc, 256 * sc, 24 * sc, 10 * sc)
        fill(ctx, "#a8a29e")


def desert(ctx, t, night=0.0, haze=True, storm=0.0, city_k=0.0):
    """Пустыня: небо, солнце/звёзды, барханы слоями, кактусы, камни, черепа, грифы, марево, следы шин."""
    day = [(0, "#38bdf8"), (0.7, "#fde68a"), (1, "#fdba74")]
    ngt = [(0, "#020617"), (0.7, "#1e1b4b"), (1, "#312e81")]
    stops = [(o, mix(hexc(a), hexc(b), night)) for (o, a), (_, b) in zip(day, ngt)]
    vgrad(ctx, -1500, -1200, 4000, 2400, stops)
    if night > 0.4:
        stars(ctx, 6, 1080, 900, t, 160)
        for k in range(80):  # млечный путь
            r = random.Random(k)
            ctx.arc(r.uniform(-200, 1300), 200 + r.uniform(-80, 80) + (r.uniform(-200, 1300)) * 0.2, r.uniform(1, 3), 0, TAU)
            fill(ctx, "#e0e7ff", 0.5 * night)
        ctx.arc(820, 260, 70, 0, TAU)
        fill(ctx, "#f1f5f9", night)
    else:
        glow(ctx, 760, 260, 420, "#fef08a", 0.9)
        ctx.arc(760, 260, 110, 0, TAU)
        fill(ctx, "#fffbeb")
    if city_k > 0:  # таинственный город на горизонте
        ctx.save()
        ctx.translate(0, 0)
        for k in range(16):
            x = 40 + k * 66
            h = 120 + (k * 37 % 5) * 50 + (180 if k in (6, 9) else 0)
            rr(ctx, x, 1020 - h, 56, h, 4)
            fill(ctx, "#1c1917", city_k)
            if k in (6, 9):
                ctx.arc(x + 28, 1020 - h, 40, math.pi, TAU)
                fill(ctx, "#1c1917", city_k)
            for j in range(int(h // 40)):
                if (k + j) % 3 == 0:
                    rr(ctx, x + 18, 1020 - h + 20 + j * 40, 18, 22, 3)
                    fill(ctx, "#fbbf24", city_k)
        glow(ctx, 540, 960, 700, "#f59e0b", 0.35 * city_k)
        ctx.restore()
    # барханы слоями
    for i, (y, col, amp) in enumerate(((1000, "#d6a35e", 60), (1120, "#e2ad66", 90), (1280, DUNE, 120))):
        ctx.move_to(-1500, 4200)
        for x in range(-1500, 2600, 40):
            ctx.line_to(x, y + math.sin(x * 0.004 + i * 2) * amp + math.sin(x * 0.011 + i) * amp * 0.3)
        ctx.line_to(2600, 4200)
        ctx.close_path()
        c = mix(hexc(col), hexc("#1e1b4b"), night * 0.7)
        src(ctx, c)
        ctx.fill()
        for x in range(-1400, 2500, 180):  # рябь ветра
            yy = y + 60 + math.sin(x * 0.004 + i * 2) * amp
            line(ctx, x, yy, x + 90, yy - 6, 3, mix(hexc(col), hexc("#000000"), 0.15), 0.6)
    r = random.Random(3)
    for i in range(6):  # кактусы
        x, y = r.uniform(-700, 1800), r.uniform(1350, 1700)
        s = r.uniform(0.5, 0.9)
        rr(ctx, x - 22 * s, y - 260 * s, 44 * s, 260 * s, 22 * s)
        fill(ctx, mix(hexc("#3f6212"), hexc("#0f172a"), night * 0.6))
        for side in (-1, 1):
            rr(ctx, x + side * 50 * s - 14 * s, y - 200 * s, 28 * s, 90 * s, 14 * s)
            fill(ctx, mix(hexc("#3f6212"), hexc("#0f172a"), night * 0.6))
            line(ctx, x + side * 22 * s, y - 120 * s, x + side * 50 * s, y - 120 * s, 26 * s,
                 mix(hexc("#3f6212"), hexc("#0f172a"), night * 0.6))
    for i in range(10):  # камни
        ell(ctx, r.uniform(-700, 1800), r.uniform(1400, 2400), r.uniform(20, 60), r.uniform(12, 30))
        fill(ctx, mix(hexc("#a8a29e"), hexc("#0f172a"), night * 0.6))
    sx, sy = r.uniform(100, 400), 1900  # череп и рога
    ell(ctx, sx, sy, 50, 36)
    fill(ctx, "#f5f5f4")
    for side in (-1, 1):
        ctx.arc(sx + side * 18, sy - 4, 10, 0, TAU)
        fill(ctx, "#292524")
        ctx.move_to(sx + side * 40, sy - 20)
        ctx.curve_to(sx + side * 90, sy - 50, sx + side * 110, sy - 20, sx + side * 130, sy - 70)
        ctx.set_line_width(10)
        src(ctx, "#f5f5f4")
        ctx.stroke()
    if night < 0.5:  # грифы кружат
        for k in range(3):
            a = t * 0.5 + k * 2.1
            bx, by = 540 + math.cos(a) * 300, 520 + math.sin(a) * 80
            ctx.move_to(bx - 50, by)
            ctx.curve_to(bx - 25, by - 26, bx - 10, by - 16, bx, by)
            ctx.curve_to(bx + 10, by - 16, bx + 25, by - 26, bx + 50, by)
            ctx.set_line_width(9)
            src(ctx, "#1c1917")
            ctx.stroke()
    if haze and night < 0.5:  # марево
        for k in range(6):
            y = 1050 + k * 40
            ctx.move_to(-1500, y)
            for x in range(-1500, 2600, 60):
                ctx.line_to(x, y + math.sin(x * 0.02 + t * 4 + k) * 6)
            ctx.set_line_width(4)
            src(ctx, "#ffffff", 0.12)
            ctx.stroke()
    if storm > 0:
        ctx.rectangle(-1500, -1200, 4000, 4400)
        fill(ctx, "#b45309", 0.7 * storm)
        rs = random.Random(int(t * 20))
        for i in range(160):
            x, y = rs.uniform(-200, 1300), rs.uniform(-200, 2400)
            line(ctx, x, y, x + 80, y + 8, rs.uniform(2, 5), "#fde68a", 0.5 * storm)


def jeep(ctx, x, y, s, t, hood=0.0, steam_=0.0, lights=0.0, tent=0.0, night=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 10, 420, 40, 0.45)
    body = mix(hexc("#b91c1c"), hexc("#1e1b4b"), night * 0.5)
    rr(ctx, -380, -230, 760, 170, 30)
    src(ctx, body)
    ctx.fill()
    ctx.move_to(-260, -230)
    ctx.line_to(-200, -380)
    ctx.line_to(200, -380)
    ctx.line_to(240, -230)
    ctx.close_path()
    src(ctx, body)
    ctx.fill()
    for wx0, wx1 in ((-230, -20), (10, 210)):
        ctx.move_to(wx0, -240)
        ctx.line_to(wx0 + 40, -360)
        ctx.line_to(wx1 - 10, -360)
        ctx.line_to(wx1 + 10, -240)
        ctx.close_path()
        fill(ctx, "#bae6fd", 0.7)
    rr(ctx, -200, -420, 400, 40, 8)  # багажник на крыше
    fill(ctx, "#57534e")
    for k in range(3):
        rr(ctx, -170 + k * 120, -470, 100, 50, 8)
        fill(ctx, ["#78350f", "#1d4ed8", "#a16207"][k])
    rr(ctx, -460, -200, 90, 120, 20)  # запаска
    fill(ctx, "#1c1917")
    ctx.arc(-415, -140, 30, 0, TAU)
    fill(ctx, "#57534e")
    for wx in (-230, 230):
        ctx.arc(wx, -40, 80, 0, TAU)
        fill(ctx, "#1c1917")
        ctx.arc(wx, -40, 36, 0, TAU)
        fill(ctx, "#a8a29e")
    rr(ctx, 360, -170, 40, 30, 8)
    fill(ctx, "#fef9c3")
    if lights > 0:
        glow(ctx, 400, -155, 300, "#fef9c3", 0.8 * lights)
        ctx.move_to(400, -170)
        ctx.line_to(1600, -400)
        ctx.line_to(1600, 100)
        ctx.close_path()
        fill(ctx, "#fef9c3", 0.15 * lights)
    if hood > 0:  # открытый капот
        ctx.save()
        ctx.translate(240, -230)
        ctx.rotate(-1.1 * hood)
        rr(ctx, 0, -10, 150, 20, 6)
        src(ctx, body)
        ctx.fill()
        ctx.restore()
    if steam_ > 0:
        puff(ctx, 300, -240, t, 5, n=6, col="#e5e7eb", life=1.4, rate=0.2, dx=60, dy=-300, a=0.6 * steam_)
    if tent > 0:  # тент от крыши к земле
        k = ease(tent)
        ctx.move_to(-200, -380)
        ctx.line_to(-200 - 600 * k, 0)
        ctx.line_to(200 - 600 * k + 300, 0)
        ctx.line_to(200, -380)
        ctx.close_path()
        fill(ctx, "#0f766e", 0.85)
        for j in range(5):
            line(ctx, -200 + j * 100, -380, -200 - 600 * k + j * 160, 0, 3, "#134e4a")
    ctx.restore()
    # следы шин
    for k in range(20):
        line(ctx, x - 600 - k * 80, y + 10 + k * 4, x - 560 - k * 80, y + 10 + k * 4, 10, DUNE_D, 0.8)


# ================================================================== СЦЕНЫ
def s0_stall(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(300, 540, ease(seg(u, 0, D))), 1450, lerp(0.75, 0.85, seg(u, 0, D)), shake=0.25)
    desert(ctx, t)
    jx = lerp(-200, 560, ease_out(seg(u, 0, 2.5)))
    jeep(ctx, jx, 1750, 1.0, t, hood=ease(seg(u, 3.5, 4.5)), steam_=seg(u, 2.0, 3.0))
    if u > 4.0:
        traveler(ctx, jx + 420, 1900, 0.95, emo("worry"), t, arms="shrug", look=(-0.6, -0.3))
    ctx.restore()


def s1_heat(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, lerp(900, 1500, ease(seg(u, 0, D))), lerp(0.9, 1.1, seg(u, 0, D)), shake=0.25)
    desert(ctx, t)
    jeep(ctx, 560, 1750, 1.0, t, hood=1.0)
    traveler(ctx, 900, 1900, 0.95, emo("fear"), t, arms="down", look=(0, -0.8), tremble=0.3)
    # термометр
    rr(ctx, 120, 500, 80, 420, 40)
    fill(ctx, "#f8fafc")
    rr(ctx, 140, 520 + 380 * (1 - seg(u, 0, D)), 40, 380 * seg(u, 0, D), 20)
    fill(ctx, "#ef4444")
    ctx.arc(160, 940, 56, 0, TAU)
    fill(ctx, "#ef4444")
    ctx.restore()
    text(ctx, "+50°C", 540, 560, 140, "#ffffff", "#b91c1c", 16, alpha=seg(u, 0.3, 0.6))


def s2_stay(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, lerp(1400, 1100, ease(seg(u, 0, D))), lerp(0.9, 0.55, ease(seg(u, 1.0, D))), shake=0.2)
    desert(ctx, t)
    jeep(ctx, 560, 1750, 1.0, t, hood=1.0)
    traveler(ctx, 900, 1900, 0.95, emo("determined"), t, arms="down", look=(-0.6, 0))
    helicopter(ctx, (t * 120) % 2200 - 600, 300, 0.7, t)
    ctx.restore()
    step_card(ctx, t, EV["steps"][0], 1, "НЕ УХОДИ\nОТ МАШИНЫ")
    if u > 2.0:
        ctx.save()
        ctx.translate(820, 660)
        ctx.arc(0, 0, 140, 0, TAU)
        fill(ctx, "#0b0b12", 0.85)
        hero(ctx, -20, 70, 0.22, emo("worry"), t, walk=t * 6, rim_a=0.0)
        crossmark(ctx, 0, 0, 2.2)
        ctx.restore()


def s3_tent(ctx, t, u, D):
    tn = EV["tent"]
    k = seg(t, tn, tn + 2.0)
    ctx.save()
    cam(ctx, t, 400, 1600, 1.05, shake=0.2)
    desert(ctx, t)
    jeep(ctx, 700, 1750, 1.0, t, hood=1.0, tent=k)
    if k > 0.6:
        ctx.move_to(100, 1750)  # прохладная тень
        ctx.line_to(600, 1750)
        ctx.line_to(700, 1980)
        ctx.line_to(0, 1980)
        fill(ctx, "#1e3a8a", 0.2)
    traveler(ctx, lerp(900, 300, ease(seg(t, tn + 1.5, tn + 2.8))), 1960, 0.95, emo("determined") if k < 1 else emo("calm"),
             t, arms="up" if k < 1 else "relax", walk=t * 6 if k >= 1 and t < tn + 2.8 else None)
    ctx.restore()
    step_card(ctx, t, EV["steps"][1], 2, "ТЕНЬ\nНАТЯНИ ТЕНТ")


def s4_water(ctx, t, u, D):
    ng = EV["night"]
    nk = ease(seg(t, ng - 0.5, ng + 0.6))
    ctx.save()
    cam(ctx, t, 540, 1550, 1.1, shake=0.2)
    desert(ctx, t, night=nk)
    jeep(ctx, 800, 1750, 1.0, t, hood=1.0, tent=1.0, night=nk)
    for j in range(6):  # канистры и бутылки
        rr(ctx, 120 + j * 70, 1820, 56, 120, 12)
        fill(ctx, "#bae6fd", 0.7)
        rr(ctx, 120 + j * 70, 1940 - 120 * (0.7 if j < 4 else 0), 56, 120 * (0.7 if j < 4 else 0), 12)
        fill(ctx, "#38bdf8")
    traveler(ctx, 560, 1980, 1.0, emo("calm"), t, arms="phone", rim="#38bdf8",
             item=lambda c, x, y: (rr(c, x - 22, y - 90, 44, 90, 10), fill(c, "#38bdf8", 0.8)))
    ctx.restore()
    step_card(ctx, t, EV["steps"][2], 3, "ВОДА — ГЛОТКАМИ\nИДИ ТОЛЬКО НОЧЬЮ")


def s5_cover(ctx, t, u, D):
    cv = EV["cover"]
    k = seg(t, cv - 0.3, cv + 0.3)
    ctx.save()
    cam(ctx, t, 540, 1450, lerp(1.2, 1.4, seg(u, 0, D)), shake=0.2)
    desert(ctx, t)
    traveler(ctx, 540, 1950, 1.1, emo("determined"), t, arms="relax", covered=k > 0.5)
    ctx.restore()
    if k < 0.5:
        ctx.save()
        ctx.translate(840, 1150)
        ctx.arc(0, 0, 110, 0, TAU)
        fill(ctx, "#0b0b12", 0.85)
        glow(ctx, 0, 0, 90, "#ef4444", 0.6)
        text(ctx, "ОЖОГ", 0, 0, 40, "#ffffff")
        ctx.restore()
    else:
        checkmark(ctx, 860, 1150, 1.6, OK, seg(t, cv + 0.3, cv + 0.8))
    step_card(ctx, t, EV["steps"][3], 4, "ЗАКРОЙ КОЖУ\nРУКАВА И ПЛАТОК")


def s6_signal(ctx, t, u, D):
    mr = EV["mirror"]
    fr = EV["fire"]
    nk = ease(seg(t, fr - 0.6, fr))
    ctx.save()
    cam(ctx, t, 540, 1500, 0.95, shake=0.2)
    desert(ctx, t, night=nk)
    jeep(ctx, 800, 1750, 1.0, t, hood=1.0, tent=1.0, lights=nk, night=nk)
    if t > mr and nk < 0.5:  # блик зеркала в небо
        ctx.move_to(420, 1500)
        ctx.line_to(1300, 200)
        ctx.line_to(1340, 260)
        ctx.close_path()
        fill(ctx, "#fffbeb", 0.6 * (0.5 + 0.5 * math.sin(t * 10)))
        glow(ctx, 420, 1500, 160, "#ffffff", 0.9)
    if nk > 0.3:  # костёр из запаски
        for j in range(5):
            a = (t * 3 + j / 5) % 1
            ell(ctx, 260 + math.sin(t * 7 + j) * 12, 1900 - a * 220, 60 * (1 - a), 110 * (1 - a))
            fill(ctx, ["#f97316", "#facc15", "#ef4444"][j % 3], 0.9 * nk)
        ell(ctx, 260, 1930, 80, 30)
        fill(ctx, "#1c1917")
        glow(ctx, 260, 1860, 600, "#f97316", 0.5 * nk)
        puff(ctx, 260, 1700, t, 3, n=6, col="#292524", life=3, rate=0.3, dx=100, dy=-900, a=0.6 * nk)
    traveler(ctx, 480, 1980, 1.0, emo("determined"), t, arms="up", covered=True,
             item=lambda c, x, y: (rr(c, x - 30, y - 50, 60, 50, 6), fill(c, "#e0f2fe")))
    ctx.restore()
    step_card(ctx, t, EV["steps"][4], 5, "СИГНАЛ\nЗЕРКАЛО И ОГОНЬ")


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


def s7_tally(ctx, t, u, D):
    tally_rows(ctx, t, "СВЕРКА ЗАПАСОВ", [
        ("ВОДА", "4 л из 6", 4 / 6, "#38bdf8", "4/6", ic_drop),
        ("ТЕНЬ", "тент натянут", 1.0, "#14b8a6", "1/1", ic_tent),
        ("ОТ СОЛНЦА", "рукава и платок", 1.0, "#facc15", "1/1", ic_sun),
        ("СИГНАЛ", "зеркало и огонь", 1.0, "#e5e7eb", "1/1", ic_mirror),
        ("СИЛЫ", "на 3 дня", 3 / 5, "#f97316", "3/5", ic_bolt)], EV["tally"])


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
    ctx.arc(540, 900, 300, math.pi * 0.75, math.pi * 0.75 + math.pi * 1.5 * 0.9 * k)
    ctx.set_line_width(50)
    src(ctx, "#22c55e")
    ctx.stroke()
    text(ctx, f"{int(90 * k)}%", 540, 880, 170, "#ffffff")
    text(ctx, "ТЕБЯ НАЙДУТ", 540, 1040, 50, "#94a3b8")
    helicopter(ctx, 540 + math.sin(t) * 200, 1350, 0.6, t)
    ctx.restore()


def s9_storm(ctx, t, u, D):
    st = EV["storm"]
    lg = EV["lights"]
    sk = seg(t, st - 0.3, st + 0.6) * (1 - seg(t, lg - 1.2, lg - 0.2))
    ctx.save()
    cam(ctx, t, 540, 1350, 0.85, shake=0.2 + 1.2 * sk)
    desert(ctx, t, night=1.0, storm=sk, city_k=seg(t, lg - 0.3, lg + 0.8))
    jeep(ctx, 800, 1750, 1.0, t, hood=1.0, tent=1.0, night=1.0, lights=0.6)
    traveler(ctx, 360, 1960, 1.0, emo("fear") if sk > 0.3 else emo("shock"), t, arms="shock" if sk > 0.3 else "down",
             covered=True, back=t > lg, tremble=sk)
    ctx.restore()


def s10_city(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, lerp(1000, 950, seg(u, 0, D)), lerp(1.0, 1.6, ease(seg(u, 0, D))), shake=0.2)
    desert(ctx, t, night=1.0, city_k=1.0, haze=False)
    ctx.restore()
    rr(ctx, 160, 300, 760, 130, 30)
    fill(ctx, "#000", 0.75)
    text(ctx, "НЕТ НА КАРТАХ", 540, 365, 70, "#fbbf24")


OLD = None


def old_people():
    global OLD
    if OLD is None:
        r = random.Random(1923)
        OLD = []
        for i in range(9):
            p = Npc(r, -200 + i * 170, 1700 + (i % 3) * 70, 0.9 + (i % 3) * 0.1, 1)
            p.shirt = r.choice(["#78350f", "#57534e", "#1e3a8a", "#7f1d1d", "#3f3f46"])
            p.pants = "#292524"
            p.style = r.choice(["cap", "short", "bun", "long"])
            p.item = "none"
            p.glasses, p.headphones, p.print_ = False, False, None
            p.collar = "shirt"
            OLD.append(p)
    return OLD


def lantern(ctx, x, y, t):
    line(ctx, x, y - 60, x, y, 4, "#292524")
    rr(ctx, x - 22, y, 44, 60, 8)
    fill(ctx, "#fbbf24")
    glow(ctx, x, y + 30, 160, "#fbbf24", 0.6 + 0.2 * math.sin(t * 9 + x))


def s11_gate(ctx, t, u, D):
    gk = ease(seg(t, EV["gate"] - 0.5, EV["gate"] + 1.5))
    ctx.save()
    cam(ctx, t, 540, 1300, 0.85, shake=0.2)
    vgrad(ctx, -1500, -1200, 4000, 2400, [(0, "#020617"), (1, "#1e1b4b")])
    stars(ctx, 6, 1080, 600, t, 100)
    # стены и ворота города
    rr(ctx, -900, 500, 2900, 900, 0)
    fill(ctx, "#44403c")
    for k in range(-9, 22):
        rr(ctx, k * 100, 460, 60, 50, 0)
        fill(ctx, "#44403c")
    for k in range(-2, 4):
        rr(ctx, k * 420, 300, 220, 400, 10)
        fill(ctx, "#57534e")
        ctx.arc(k * 420 + 110, 300, 110, math.pi, TAU)
        fill(ctx, "#57534e")
        rr(ctx, k * 420 + 80, 400, 60, 90, 30)
        fill(ctx, "#fbbf24", 0.8)
    ctx.arc(540, 1000, 300, math.pi, TAU)  # арка ворот
    ctx.line_to(840, 1400)
    ctx.line_to(240, 1400)
    ctx.close_path()
    fill(ctx, "#fbbf24", 0.25 + 0.5 * gk)
    glow(ctx, 540, 1100, 600, "#fbbf24", 0.5 * gk)
    for side in (-1, 1):
        rr(ctx, 540 + side * (300 * gk) - (300 if side < 0 else 0), 700, 300, 700, 6)
        fill(ctx, "#78350f")
    text(ctx, "1923", 540, 640, 60, "#fde68a")
    ctx.rectangle(-1500, 1400, 4000, 1400)
    fill(ctx, mix(hexc(DUNE_D), hexc("#1e1b4b"), 0.6))
    for p in old_people():
        p0 = p.x
        p.x = lerp(540, p0, gk)
        x = npc(ctx, p, t, walking=False, stare=0.8, alpha=gk)
        lantern(ctx, x + 70 * p.sc, p.y - 330 * p.sc, t)
        p.x = p0
    traveler(ctx, 540, 2350, 1.4, emo("shock"), t, arms="down", back=True, legs=False, covered=True)
    ctx.restore()


def s12_old(ctx, t, u, D):
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        hk = ease(seg(t, EV["hundred"] - 0.3, EV["hundred"] + 1.5))
        cam(ctx, t, 560, lerp(1150, 1050, hk), lerp(1.3, 0.75, hk), shake=0.2)
        desert(ctx, t, night=1.0, city_k=1.0, haze=False)
        if hk > 0:  # сотня одинаковых машин, наполовину в песке
            for row in range(4):
                for k in range(9):
                    jx = -600 + k * 260 + (row % 2) * 130
                    jy = 1250 + row * 160
                    ctx.save()
                    ctx.rectangle(-2000, -2000, 5000, jy + 2000 - 40)
                    ctx.clip()
                    jeep(ctx, jx, jy + 40 - row * 6, 0.35 + row * 0.05, t, hood=1.0, night=1.0)
                    ctx.restore()
                    ell(ctx, jx, jy - 40, 160 * (0.35 + row * 0.05) * 1.6, 26)
                    fill(ctx, mix(hexc(DUNE_D), hexc("#1e1b4b"), 0.6), hk)
            ctx.rectangle(-2000, -2000, 5000, 5000)
            fill(ctx, "#020617", 0.25 * (1 - hk))
        for k in range(5):  # жители с фонарями за стариком
            q = Npc(random.Random(300 + k), 160 + k * 200, 1780, 0.8, 1)
            q.shirt, q.item, q.glasses, q.headphones = ["#78350f", "#57534e", "#1e3a8a", "#7f1d1d", "#3f3f46"][k], "none", False, False
            xq = npc(ctx, q, t, walking=False, stare=0.8, alpha=1 - hk * 0.7)
            lantern(ctx, xq + 56, 1780 - 260, t)
        p = Npc(random.Random(1900), 620, 1950, 1.6, -1)
        p.shirt, p.pants, p.style, p.hair, p.beard = "#57534e", "#292524", "short", "#e5e7eb", True
        p.glasses, p.headphones, p.collar, p.print_, p.item = True, False, "shirt", None, "none"
        x = npc(ctx, p, t, walking=False, grin=0.4 if t > EV["hundred"] else 0.0)
        lantern(ctx, x - 120, 1350, t)
        if t > EV["hundred"]:  # за спиной старика — сотня одинаковых машин в песке
            pass
        ctx.restore()
        ctx.save()
        if t > EV["hundred"]:
            rr(ctx, 220, 300, 640, 140, 30)
            fill(ctx, "#000", 0.8)
            text(ctx, "100-Й РАЗ", 540, 370, 90, "#fbbf24")
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
        text(ctx, "Что это за город?", 0, 180, 70, "#fbbf24")
    ctx.restore()


SCENES = [s0_stall, s1_heat, s2_stay, s3_tent, s4_water, s5_cover, s6_signal, s7_tally, s8_chance, s9_storm,
          s10_city, s11_gate, s12_old]
LABELS = {1: "ДЕНЬ 1", 2: "ДЕНЬ 1", 3: "ДЕНЬ 1", 4: "ДЕНЬ 1", 5: "ДЕНЬ 2", 6: "ДЕНЬ 2", 9: "НОЧЬ 3",
          10: "НОЧЬ 3", 11: "НОЧЬ 3", 12: "НОЧЬ 3"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("четыре", "литра", "из", "шести"), "4 л из 6"), (("девяносто", "процентов"), "90%"),
         (("плюс", "пятьдесят"), "+50"), (("двести",), "200"), (("три", "дня"), "3 дня")]


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
        text(ctx, "ТЫ ЗАСТРЯЛ", 0, 10, 112, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -360, 90, 720, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "В ПУСТЫНЕ?", 0, 155, 100, "#ffffff")
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
