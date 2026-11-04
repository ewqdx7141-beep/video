"""Серия 10 «Лёд» (что делать): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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



# ================================================================== ОЗЕРО
ICE = "#dbeafe"
ICE_D = "#93c5fd"
WATER = "#0c2a4a"


def lake(ctx, t, hole=None, hole_r=0.0, cracks=0.0, frozen_k=0.0, face_k=0.0, knock=0.0):
    """Замёрзшее озеро: берег с елями, лёд с бликами, полынья, трещины, лицо подо льдом."""
    vgrad(ctx, -1500, -1200, 4000, 2400, [(0, "#94a3b8"), (1, "#e2e8f0")])
    r = random.Random(4)
    for i in range(14):
        pine(ctx, -900 + i * 240 + r.uniform(-60, 60), 1050 + r.uniform(-20, 20), 0.6 * r.uniform(0.8, 1.2), "#334155")
    ctx.rectangle(-1500, 1040, 4000, 3000)
    lgrad(ctx, 0, 1040, 0, 2800, [(0, "#bfdbfe"), (1, ICE)])
    ctx.fill()
    for i in range(16):  # блики и снежные полосы
        x = r.uniform(-800, 1800)
        y = r.uniform(1100, 2600)
        line(ctx, x, y, x + r.uniform(80, 260), y - r.uniform(10, 40), 4, "#ffffff", 0.6)
    for i in range(10):
        ell(ctx, r.uniform(-800, 1800), r.uniform(1100, 2600), r.uniform(80, 200), 16)
        fill(ctx, "#ffffff", 0.5)
    if hole:
        hx, hy = hole
        if cracks > 0:
            rc = random.Random(7)
            for j in range(9):
                a = j * TAU / 9 + rc.uniform(-0.2, 0.2)
                L = rc.uniform(160, 420) * cracks
                x0, y0 = hx, hy
                ctx.move_to(x0, y0)
                for s_ in range(5):
                    x0 += math.cos(a + rc.uniform(-0.4, 0.4)) * L / 5
                    y0 += math.sin(a + rc.uniform(-0.4, 0.4)) * L / 5 * 0.45
                    ctx.line_to(x0, y0)
                ctx.set_line_width(4)
                src(ctx, "#1e3a8a", 0.7)
                ctx.stroke()
        if hole_r > 0:
            rr_ = hole_r * (1 - frozen_k)
            if rr_ > 2:
                ell(ctx, hx, hy, rr_ + 14, (rr_ + 14) * 0.42)
                fill(ctx, "#ffffff")
                ell(ctx, hx, hy, rr_, rr_ * 0.4)
                fill(ctx, WATER)
                for k in range(4):  # обломки льда
                    a = k * 1.7 + t * 0.3
                    rr(ctx, hx + math.cos(a) * rr_ * 0.6 - 30, hy + math.sin(a) * rr_ * 0.2 - 10, 60, 22, 6)
                    fill(ctx, ICE)
    if face_k > 0 and hole:  # лицо подо льдом
        hx, hy = hole
        ctx.save()
        ell(ctx, hx, hy, 260, 120)
        ctx.clip()
        ctx.translate(0, -8 * knock)
        hero_head(ctx, hx, hy + 10, 110, emo("neutral"), t, rim="#38bdf8", rim_a=0.4 * face_k)
        for side in (-1, 1):  # ладони прижаты ко льду
            ell(ctx, hx + side * 170, hy - 10 - 10 * knock * (side > 0), 40, 26)
            fill(ctx, HEAD, face_k)
        ctx.restore()
        ell(ctx, hx, hy, 260, 120)  # слой льда поверх
        fill(ctx, ICE, 0.55 * (1 - 0.4 * face_k))
        for k in range(5):
            line(ctx, hx - 200 + k * 90, hy - 60, hx - 140 + k * 90, hy + 60, 3, "#ffffff", 0.5)


def underwater(ctx, t, k):
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1e3a8a"), (1, "#020617")])
    ctx.rectangle(-800, -800, 2700, 1100)
    fill(ctx, ICE, 0.85)
    ell(ctx, 540, 300, 240, 40)
    fill(ctx, "#38bdf8", 0.6)
    for i in range(30):  # пузыри
        r = random.Random(i)
        x = 540 + r.uniform(-260, 260)
        y = 1700 - ((t * r.uniform(150, 300) + r.uniform(0, 1400)) % 1400)
        ctx.arc(x, y, r.uniform(6, 16), 0, TAU)
        ctx.set_line_width(3)
        src(ctx, "#bfdbfe", 0.7)
        ctx.stroke()


# ================================================================== СЦЕНЫ
def s0_hook(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(400, 620, ease(seg(u, 0, D))), 1450, lerp(0.75, 0.85, seg(u, 0, D)), shake=0.25)
    lake(ctx, t)
    hiker(ctx, lerp(100, 520, ease(seg(u, 0, D))), 1900, 1.0, emo("happy"), t, walk=t * 7)
    for i in range(int(u * 3)):  # следы за героем
        ell(ctx, 80 + i * 40, 1910, 18, 8)
        fill(ctx, "#94a3b8", 0.6)
    snowfall(ctx, t, 50, 0.6)
    ctx.restore()


def s1_fall(ctx, t, u, D):
    cr = EV["crack"]
    fa = EV["fall"]
    f = ease_in(seg(t, fa, fa + 0.5), 2)
    ctx.save()
    if t < fa + 1.0:
        cam(ctx, t, 560, 1550, lerp(0.95, 1.2, seg(t, cr, fa)), shake=0.4 + 2.0 * seg(t, fa, fa + 0.3))
        lake(ctx, t, hole=(540, 1900), hole_r=230 * seg(t, fa - 0.1, fa + 0.2), cracks=seg(t, cr, fa))
        ctx.save()
        ctx.rectangle(-1500, -1200, 4000, 1900 + 1200 - 60 + 1200 * (1 - f))
        ctx.clip()
        hiker(ctx, 540, 1900 + 500 * f, 1.0, emo("shock"), t, arms="up" if f > 0 else "shock", tremble=0.8)
        ctx.restore()
        puff(ctx, 540, 1890, t, 3, n=6, col="#ffffff", life=0.8, rate=0.15, dx=0, dy=-200, a=0.6 * f)
    else:
        cam(ctx, t, 540, 960, 1.0, shake=0.6)
        underwater(ctx, t, 1)
        hero(ctx, 540, 1500, 1.2, emo("fear"), t, arms="up", rim="#38bdf8", rim_a=0.8, tremble=0.6,
             hood=("#ea580c", "#9a3412"))
    ctx.restore()


def in_hole(ctx, t, hk, cx=540, cy=1700, z=1.2, extra=None):
    ctx.save()
    cam(ctx, t, cx, cy, z, shake=0.3)
    lake(ctx, t, hole=(540, 1900), hole_r=230, cracks=1.0)
    ctx.save()
    ctx.rectangle(-1500, -1200, 4000, 1880 + 1200)
    ctx.clip()
    hiker(ctx, 540, hk.get("y", 2150), 1.0, hk.get("e", emo("fear")), t, arms=hk.get("arms", "up"),
          tremble=hk.get("tremble", 0.6), look=hk.get("look", (0, 0)), tilt=hk.get("tilt", 0.0))
    ctx.restore()
    if extra:
        extra()
    ctx.restore()


def s2_breathe(ctx, t, u, D):
    br = EV["breath"]
    k = ease(seg(t, br - 0.5, br + 0.5))
    in_hole(ctx, t, dict(e=emo("fear", "determined", k), tremble=1.0 - 0.8 * k))
    step_card(ctx, t, EV["steps"][0], 1, "НЕ ПАНИКУЙ\nПЕРЕЖИВИ 1 МИНУТУ")
    # таймер «1 минута» и волна дыхания
    rr(ctx, 380, 1150, 320, 120, 30)
    fill(ctx, "#000", 0.7)
    s_ = int(lerp(60, 0, seg(t, EV["steps"][0], TL.shots[3][0])))
    text(ctx, f"0:{s_:02d}", 540, 1210, 80, "#38bdf8")


def s3_turn(ctx, t, u, D):
    tu = EV["turn"]
    k = ease(seg(t, tu, tu + 1.2))
    in_hole(ctx, t, dict(e=emo("determined"), look=(lerp(0.9, -0.9, k), 0), tremble=0.3), cx=lerp(540, 300, k))
    step_card(ctx, t, EV["steps"][1], 2, "РАЗВЕРНИСЬ\nТУДА, ОТКУДА ПРИШЁЛ")
    if k > 0.3:
        ctx.save()
        ctx.translate(540, 1120)
        line(ctx, 160, 0, -200, 0, 18, OK)
        ctx.move_to(-250, 0)
        ctx.line_to(-190, -40)
        ctx.line_to(-190, 40)
        ctx.close_path()
        fill(ctx, OK)
        ctx.restore()
        text(ctx, "КРЕПКИЙ ЛЁД", 300, 1000, 48, OK, "#000", 8)


def s4_kick(ctx, t, u, D):
    kk = EV["kick"]
    k = ease(seg(t, kk, TL.shots[5][0]))
    ctx.save()
    cam(ctx, t, 540, 1700, 1.15, shake=0.35)
    lake(ctx, t, hole=(540, 1900), hole_r=230, cracks=1.0)
    ctx.save()
    ctx.translate(lerp(540, 330, k), lerp(1950, 1880, k))
    ctx.rotate(-math.pi / 2 * lerp(0.4, 1.0, k))
    hero(ctx, 0, 0, 0.9, emo("determined"), t, arms="up", walk=t * 12, back=True, rim_a=0.0, hood=("#ea580c", "#9a3412"))
    ctx.restore()
    ctx.restore()
    step_card(ctx, t, EV["steps"][2], 3, "РУКИ НА ЛЁД\nНОГАМИ, КАК ПЛОВЕЦ")


def s5_roll(ctx, t, u, D):
    ro = EV["roll"]
    k = ease(seg(t, ro, TL.shots[6][0]))
    ctx.save()
    cam(ctx, t, lerp(400, 100, k), 1750, 1.0, shake=0.3)
    lake(ctx, t, hole=(540, 1900), hole_r=230, cracks=1.0)
    for i in range(10):  # свои следы к берегу
        ell(ctx, 300 - i * 80, 1930 + (i % 2) * 20, 22, 10)
        fill(ctx, "#94a3b8", 0.7)
    ctx.save()
    ctx.translate(lerp(250, -250, k), 1900)
    ctx.rotate(-math.pi / 2 + k * 6)
    hero(ctx, 0, 0, 0.8, emo("determined"), t, arms="hug", back=False, rim_a=0.0, legs=True, hood=("#ea580c", "#9a3412"))
    ctx.restore()
    ctx.restore()
    step_card(ctx, t, EV["steps"][3], 4, "НЕ ВСТАВАЙ\nОТКАТИСЬ И ПОЛЗИ")
    crossmark(ctx, 880, 700, 1.4) if k < 0.2 else None


def s6_warm(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1200, lerp(1.0, 1.1, seg(u, 0, D)), shake=0.25)
    forest(ctx, t, dusk=0.4)
    # костёр
    for k in range(6):
        line(ctx, 700 + k * 20 - 60, 1880, 760 - k * 20, 1820, 14, "#78350f")
    for k in range(5):
        a = (t * 3 + k) % 1
        ell(ctx, 720 + math.sin(t * 7 + k) * 14, 1800 - a * 120, 40 * (1 - a), 70 * (1 - a))
        fill(ctx, ["#f97316", "#facc15", "#ef4444"][k % 3], 0.9)
    glow(ctx, 720, 1760, 500, "#f97316", 0.5)
    hero(ctx, 400, 1900, 1.1, emo("calm"), t, arms="hug", rim="#f97316", rim_a=0.8, hood=("#64748b", "#475569"))
    rr(ctx, 270, 1530, 260, 100, 30)  # плед на плечах
    fill(ctx, "#b91c1c", 0.9)
    rr(ctx, 860, 1800, 140, 60, 10)  # мокрая одежда на снегу
    fill(ctx, "#ea580c")
    puff(ctx, 930, 1790, t, 4, n=4, col="#ffffff", life=1.2, rate=0.4, dx=20, dy=-120, a=0.4)
    snowfall(ctx, t, 40, 0.5)
    ctx.restore()
    step_card(ctx, t, EV["steps"][4], 5, "СНИМИ МОКРОЕ\nСОГРЕЙСЯ")


def s7_score(ctx, t, u, D):
    sc = EV["score"]
    ctx.save()
    cam(ctx, t, 540, 960, 1.0, shake=0.2)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0f172a"), (1, "#020617")])
    text(ctx, "ПРОВЕРКА", 540, 330, 100, "#ffffff", "#000", 12)
    items = ["ПЕРЕЖИЛ 1 МИНУТУ", "РАЗВЕРНУЛСЯ НАЗАД", "ВЫПОЛЗ ГОРИЗОНТАЛЬНО", "НЕ ВСТАЛ, ОТКАТИЛСЯ",
             "СОГРЕЛСЯ"]
    total = 0
    for i, it in enumerate(items):
        y = 520 + i * 170
        a = seg(t, sc[i] - 0.9, sc[i] - 0.6)
        if a <= 0:
            continue
        rr(ctx, 90, y - 60, 900, 120, 24)
        fill(ctx, "#1e293b", a)
        text(ctx, f"{i + 1}. {it}", 130, y, 42, "#ffffff", align="left", alpha=a)
        ck = seg(t, sc[i], sc[i] + 0.3)
        if ck > 0:
            checkmark(ctx, 820, y - 6, 1.0, OK, ck)
            text(ctx, "+20", 930, y, 50, OK, align="right", alpha=ck)
            total += 20
    ctx.restore()
    rr(ctx, 240, 1360, 600, 160, 40)
    fill(ctx, "#000", 0.85)
    text(ctx, f"{total}/100", 540, 1440, 110, OK if total == 100 else "#facc15")


def s8_shore(ctx, t, u, D):
    tt = EV["total"]
    ctx.save()
    cam(ctx, t, 540, 1350, 0.85, shake=0.2)
    lake(ctx, t, hole=(900, 1500), hole_r=150, cracks=1.0)
    hero(ctx, 300, 1950, 1.1, emo("happy"), t, arms="cheer", rim="#f97316", rim_a=0.6, hood=("#64748b", "#475569"))
    snowfall(ctx, t, 40, 0.5)
    ctx.restore()
    s = back_out(seg(t, tt - 0.1, tt + 0.3))
    if s > 0:
        ctx.save()
        ctx.translate(540, 560)
        ctx.scale(max(0.02, s), max(0.02, s))
        text(ctx, "100/100", 0, 0, 200, OK, "#000", 20, shadow=True)
        ctx.restore()


def s9_whole(ctx, t, u, D):
    wh = EV["whole"]
    fk = ease(seg(t, EV["look"] + 0.3, wh))
    ctx.save()
    cam(ctx, t, lerp(540, 900, ease(seg(t, EV["look"], wh))), lerp(1350, 1500, fk), lerp(0.85, 1.4, fk), shake=0.2)
    lake(ctx, t, hole=(900, 1500), hole_r=150, cracks=1.0 - fk, frozen_k=fk)
    hero(ctx, 300, 1950, 1.1, emo("happy", "shock", seg(t, wh - 0.5, wh)), t, arms="down", back=True,
         rim="#38bdf8", rim_a=0.5, hood=("#64748b", "#475569"))
    ctx.restore()


def s10_face(ctx, t, u, D):
    fc = EV["face"]
    ctx.save()
    cam(ctx, t, 900, 1500, lerp(1.6, 2.4, ease(seg(u, 0, D))), shake=0.2)
    lake(ctx, t, hole=(900, 1500), hole_r=150, frozen_k=1.0, face_k=ease(seg(t, fc - 1.2, fc)))
    ctx.restore()


def s11_knock(ctx, t, u, D):
    ec = EV["end_card"] - TL.shots[11][0]
    kn = 0.0
    for k_ in EV["knocks"]:
        if 0 <= t - k_ < 0.2:
            kn = 1 - (t - k_) / 0.2
    ctx.save()
    if u < ec:
        cam(ctx, t, 900, 1500, 2.4 + 0.08 * kn, shake=0.2 + 1.5 * kn)
        lake(ctx, t, hole=(900, 1500), hole_r=150, frozen_k=1.0, face_k=1.0, knock=kn)
        if kn > 0:
            for j in range(6):  # трещинки от стука
                a = j * TAU / 6
                line(ctx, 1070, 1490, 1070 + math.cos(a) * 40, 1490 + math.sin(a) * 18, 3, "#1e3a8a", kn)
        ctx.restore()
        ctx.save()
        if kn > 0:
            text(ctx, "ТУК", 540, 520, 130, "#ffffff", "#000", 14, alpha=kn)
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
        text(ctx, "Кто остался подо льдом?", 0, 180, 62, "#38bdf8")
    ctx.restore()


SCENES = [s0_hook, s1_fall, s2_breathe, s3_turn, s4_kick, s5_roll, s6_warm, s7_score, s8_shore, s9_whole,
          s10_face, s11_knock]
LABELS = {}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("пять",), "5"), (("двадцать",), "20"), (("сто", "из", "ста"), "100/100")]


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
            text(ctx, LABELS[i], W - 60, 125, 46, "#ffffff", "#000", 10, align="right", alpha=a)
    hook_end = TL.lines[0]["start"] + TL.lines[0]["speech"] + 0.2
    if t < hook_end:  # заголовок-хук
        k1 = back_out(seg(t, 0.0, 0.3))
        out = 1 - seg(t, hook_end - 0.3, hook_end)
        ctx.save()
        ctx.translate(540, 360)
        ctx.scale(k1, k1)
        ctx.push_group()
        text(ctx, "ЧТО ДЕЛАТЬ, ЕСЛИ", 0, -110, 84, "#ffffff", "#000", 16, shadow=True)
        text(ctx, "ТЫ ПРОВАЛИЛСЯ", 0, 10, 104, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -300, 90, 600, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "ПОД ЛЁД?", 0, 155, 100, "#ffffff")
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
