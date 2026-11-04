"""Серия 9 «Медведь» (что делать): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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


# ================================================================== СЦЕНЫ
def s0_hook(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(400, 640, ease(seg(u, 0, D))), 1350, lerp(0.75, 0.85, seg(u, 0, D)), shake=0.25)
    forest(ctx, t)
    bear(ctx, lerp(1500, 1250, ease(seg(u, 1.5, D))), 1650, 0.7, t, walk=t * 3)
    hiker(ctx, lerp(100, 420, ease(seg(u, 0, D - 1))), 1900, 1.0, emo("happy") if u < D - 1.5 else emo("shock"), t,
          walk=t * 7 if u < D - 1 else None, look=(0.9, 0))
    snowfall(ctx, t)
    ctx.restore()


def s1_rise(ctx, t, u, D):
    bu = EV["bear_up"]
    st = ease(seg(t, bu - 0.2, bu + 0.4))
    ctx.save()
    cam(ctx, t, 720, 1300, lerp(0.85, 0.95, seg(u, 0, D)), shake=0.4 + 1.0 * seg(t, bu, bu + 0.4))
    forest(ctx, t)
    bear(ctx, 1000, 1700, 0.85, t, stand=st, roar=seg(t, bu + 0.3, bu + 0.6))
    hiker(ctx, 360, 1900, 1.05, emo("shock"), t, arms="shock", tremble=0.8, look=(0.9, -0.5))
    snowfall(ctx, t)
    ctx.restore()


def standoff(ctx, t, cx=700, z=0.95, bear_st=1.0, hiker_kw=None, bear_x=1000, hiker_x=360, roar=0.0):
    ctx.save()
    cam(ctx, t, cx, 1300, z, shake=0.3)
    forest(ctx, t)
    bear(ctx, bear_x, 1700, 0.85, t, stand=bear_st, roar=roar)
    hk = dict(e=emo("fear"), arms="down", look=(0.9, 0), tremble=0.4)
    hk.update(hiker_kw or {})
    hiker(ctx, hiker_x, 1900, 1.05, hk["e"], t, arms=hk["arms"], look=hk["look"], tremble=hk["tremble"],
          walk=hk.get("walk"))
    snowfall(ctx, t)
    ctx.restore()


def s2_dont_run(ctx, t, u, D):
    standoff(ctx, t, 700, 1.0, hiker_kw=dict(e=emo("fear"), arms="down"))
    step_card(ctx, t, EV["steps"][0], 1, "НЕ БЕГИ", good=False)
    a = seg(t, EV["steps"][0] + 0.8, EV["steps"][0] + 1.1)
    if a > 0:  # перечёркнутый бегущий человечек
        ctx.save()
        ctx.translate(820, 640)
        ctx.arc(0, -80, 26, 0, TAU)
        fill(ctx, "#ffffff", a)
        line(ctx, 0, -50, 0, 30, 14, "#ffffff", a)
        line(ctx, 0, 30, -40, 90, 14, "#ffffff", a)
        line(ctx, 0, 30, 40, 80, 14, "#ffffff", a)
        line(ctx, 0, -30, 40, 0, 14, "#ffffff", a)
        line(ctx, 0, -30, -40, -10, 14, "#ffffff", a)
        crossmark(ctx, 0, 0, 2.6)
        ctx.restore()


def s3_eyes(ctx, t, u, D):
    st = EV["steps"][1]
    k = ease(seg(t, st + 0.6, st + 1.2))
    standoff(ctx, t, lerp(700, 560, k), lerp(1.0, 1.5, k),
             hiker_kw=dict(e=emo("fear", "worry", k), arms="down", look=(lerp(0.9, -0.3, k), lerp(0, 0.8, k))))
    step_card(ctx, t, st, 2, "НЕ СМОТРИ\nВ ГЛАЗА", good=False)


def s4_big(ctx, t, u, D):
    au = EV["arms_up"]
    k = ease(seg(t, au - 0.2, au + 0.5))
    standoff(ctx, t, 700, 0.95, hiker_kw=dict(e=emo("worry", "determined", k), arms=arms_lerp("down", "up", k),
                                              tremble=0.2))
    step_card(ctx, t, EV["steps"][2], 3, "СТАНЬ БОЛЬШЕ\nГОВОРИ СПОКОЙНО")
    if k > 0.5:  # волны спокойного голоса
        for j in range(3):
            a = (t * 0.8 + j / 3) % 1
            ctx.arc(560, 1060, 60 + a * 160, -0.5, 0.5)
            ctx.set_line_width(6)
            src(ctx, OK, 0.7 * (1 - a))
            ctx.stroke()


def s5_back(ctx, t, u, D):
    ba = EV["back_away"]
    k = ease(seg(t, ba, TL.shots[6][0]))
    standoff(ctx, t, lerp(700, 560, k), 0.9, hiker_x=lerp(360, 60, k),
             hiker_kw=dict(e=emo("determined"), arms="up", walk=t * 2 if 0 < k < 1 else None, look=(0.9, 0)))
    step_card(ctx, t, EV["steps"][3], 4, "МЕДЛЕННО\nОТСТУПАЙ")
    if k > 0.1:
        ctx.save()
        ctx.translate(540, 1150)
        line(ctx, 100, 0, -200, 0, 16, OK)
        ctx.move_to(-240, 0)
        ctx.line_to(-190, -34)
        ctx.line_to(-190, 34)
        ctx.close_path()
        fill(ctx, OK)
        ctx.restore()


def s6_lie(ctx, t, u, D):
    li = EV["lie"]
    ctx.save()
    cam(ctx, t, 540, 1000, 1.0, shake=0.3)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#e2e8f0"), (1, "#cbd5e1")])
    rr(ctx, 100, 600, 880, 760, 40)
    fill(ctx, "#0f172a", 0.85)
    ctx.save()
    ctx.translate(540, 1080)
    ctx.rotate(-math.pi / 2)
    hero(ctx, 0, 0, 0.9, emo("fear"), t, arms="shock", back=True, rim_a=0.0, hood=("#ea580c", "#9a3412"))
    ctx.restore()
    for side in (-1, 1):  # руки на шее
        ctx.arc(540 - 300, 1080 + side * 40, 26, 0, TAU)
        fill(ctx, HEAD)
    checkmark(ctx, 880, 700, 1.5, OK, seg(t, li + 0.5, li + 1.0))
    text(ctx, "НА ЖИВОТ", 540, 1430, 64, OK, "#000", 8)
    text(ctx, "РУКИ НА ШЕЕ", 540, 1510, 64, OK, "#000", 8)
    ctx.restore()
    step_card(ctx, t, EV["steps"][4], 5, "НАПАЛ —\nЛОЖИСЬ НА ЖИВОТ")


def s7_score(ctx, t, u, D):
    sc = EV["score"]
    ctx.save()
    cam(ctx, t, 540, 960, 1.0, shake=0.2)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0f172a"), (1, "#020617")])
    text(ctx, "ПРОВЕРКА", 540, 330, 100, "#ffffff", "#000", 12)
    items = ["НЕ ПОБЕЖАЛ", "НЕ СМОТРЕЛ В ГЛАЗА", "СТАЛ БОЛЬШЕ", "ОТСТУПИЛ МЕДЛЕННО", "ЗНАЕШЬ, КАК ЛЕЧЬ"]
    total = 0
    for i, it in enumerate(items):
        y = 520 + i * 170
        a = seg(t, sc[i] - 0.9, sc[i] - 0.6)
        if a <= 0:
            continue
        rr(ctx, 90, y - 60, 900, 120, 24)
        fill(ctx, "#1e293b", a)
        text(ctx, f"{i + 1}. {it}", 130, y, 46, "#ffffff", align="left", alpha=a)
        ck = seg(t, sc[i], sc[i] + 0.3)
        if ck > 0:
            checkmark(ctx, 820, y - 6, 1.0, OK, ck)
            text(ctx, "+20", 930, y, 50, OK, align="right", alpha=ck)
            total += 20
    ctx.restore()
    rr(ctx, 240, 1360, 600, 160, 40)
    fill(ctx, "#000", 0.85)
    text(ctx, f"{total}/100", 540, 1440, 110, OK if total == 100 else "#facc15")


def s8_leave(ctx, t, u, D):
    lv = EV["leave"]
    tt = EV["total"]
    k = ease(seg(t, lv - 0.5, TL.shots[9][0]))
    ctx.save()
    cam(ctx, t, 700, 1300, 0.9, shake=0.25)
    forest(ctx, t, dusk=0.3)
    st = 1 - ease(seg(t, tt + 0.6, tt + 1.4))
    bear(ctx, lerp(1000, 1700, k), 1700, 0.85, t, stand=st, walk=t * 3 if k > 0 else None, facing=1 if k > 0 else -1)
    hiker(ctx, 300, 1900, 1.05, emo("happy") if k > 0.3 else emo("worry"), t, arms="down", look=(0.9, 0))
    snowfall(ctx, t)
    ctx.restore()
    s = back_out(seg(t, tt - 0.1, tt + 0.3))
    if s > 0:
        ctx.save()
        ctx.translate(540, 560)
        ctx.scale(max(0.02, s), max(0.02, s))
        text(ctx, "100/100", 0, 0, 200, OK, "#000", 20, shadow=True)
        ctx.restore()


def ranger(x, y, sc, d=-1):
    p = Npc(random.Random(4242), x, y, sc, d)
    p.shirt, p.pants, p.style, p.item, p.hair = "#4d7c0f", "#3f3f46", "cap", "none", "#5a3a22"
    p.beard, p.glasses, p.headphones, p.collar, p.print_ = True, False, False, "shirt", None
    return p


def s9_ranger(ctx, t, u, D):
    rg = EV["ranger"]
    a = ease(seg(t, rg - 0.3, rg + 0.6))
    ctx.save()
    cam(ctx, t, lerp(600, 760, a), 1350, lerp(0.9, 1.1, ease(seg(u, 0, D))), shake=0.25)
    forest(ctx, t, dusk=0.4)
    p = ranger(lerp(1500, 1000, a), 1880, 1.2)
    npc(ctx, p, t, walking=False, stare=1.0)
    rr(ctx, lerp(1500, 1000, a) - 20, 1300, 16, 400, 6)  # ружьё за спиной
    fill(ctx, "#292524")
    rr(ctx, lerp(1500, 1000, a) - 70, 1440, 140, 26, 6)  # оранжевый жилет
    fill(ctx, "#f97316")
    hiker(ctx, 360, 1900, 1.05, emo("worry"), t, arms="down", look=(0.9, 0))
    snowfall(ctx, t)
    ctx.restore()


def s10_never(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 600, 1250, lerp(1.6, 1.8, seg(u, 0, D)), shake=0.25)
    forest(ctx, t, dusk=0.5)
    p = ranger(680, 1900, 1.4)
    npc(ctx, p, t, walking=False, stare=1.0)
    snowfall(ctx, t)
    ctx.restore()


def footprints(ctx, t, k_bare):
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#e2e8f0"), (1, "#f8fafc")])
    for i in range(12):  # следы ботинок героя
        x = 360 + (i % 2) * 70
        y = 2000 - i * 150
        ell(ctx, x, y, 34, 60)
        fill(ctx, "#cbd5e1")
        for j in range(4):
            line(ctx, x - 20, y - 30 + j * 18, x + 20, y - 30 + j * 18, 4, "#94a3b8")
    n = int(12 * k_bare)
    for i in range(n):  # босые следы рядом
        x = 700 + (i % 2) * 60
        y = 2000 - i * 150
        ell(ctx, x, y, 26, 52)
        fill(ctx, "#94a3b8")
        for j in range(5):
            ctx.arc(x - 20 + j * 10, y - 62 + abs(j - 1) * 3, 6, 0, TAU)
            fill(ctx, "#94a3b8")


def s11_prints(ctx, t, u, D):
    bf = EV["barefoot"]
    tn = EV["tent"]
    ec = EV["end_card"] - TL.shots[11][0]
    ctx.save()
    if u < ec:
        k = ease(seg(t, tn - 0.5, tn + 1.5))
        cam(ctx, t, 600, lerp(1300, 400, k), lerp(1.0, 0.9, k), shake=0.25)
        footprints(ctx, t, seg(t, bf - 1.0, bf + 0.5))
        # палатка в конце следов, внутри свет и тень
        ctx.save()
        ctx.translate(700, -200)
        ctx.move_to(-300, 200)
        ctx.line_to(0, -200)
        ctx.line_to(300, 200)
        ctx.close_path()
        fill(ctx, "#f97316")
        ctx.move_to(-60, 200)
        ctx.line_to(0, 0)
        ctx.line_to(60, 200)
        ctx.close_path()
        fill(ctx, "#fde68a")
        ctx.arc(0, 120, 24, 0, TAU)
        fill(ctx, "#78350f", 0.8)
        rr(ctx, -22, 140, 44, 60, 12)
        fill(ctx, "#78350f", 0.8)
        ctx.restore()
        glow(ctx, 700, -60, 300, "#fde68a", 0.4)
        snowfall(ctx, t, 50, 0.6)
        ctx.restore()
        ctx.save()
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
        text(ctx, "Кто в твоей палатке?", 0, 180, 66, "#f97316")
    ctx.restore()


SCENES = [s0_hook, s1_rise, s2_dont_run, s3_eyes, s4_big, s5_back, s6_lie, s7_score, s8_leave, s9_ranger,
          s10_never, s11_prints]
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
        text(ctx, "ТЫ ВСТРЕТИЛ", 0, 10, 112, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -300, 90, 600, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "МЕДВЕДЯ?", 0, 155, 100, "#ffffff")
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
