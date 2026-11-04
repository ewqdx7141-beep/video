"""Серия 2 «Сообщение из 3:07»: python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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


def bedroom_night(ctx, t, lit=0.0):
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#090d1f"), (1, "#131a33")])
    rr(ctx, 120, 200, 840, 700, 10)
    fill(ctx, "#0c1636")
    stars(ctx, 9, 900, 800, t, 30)
    skyline(ctx, 91, 130, 950, 900, 120, 420, "#060a1c", "#ffd27a", 0.06)
    ctx.arc(760, 360, 70, 0, TAU)
    fill(ctx, "#e8e6d6")
    for x0 in (120, 535, 950):
        ctx.rectangle(x0 - 10, 200, 20, 700)
        fill(ctx, "#1c2442")
    curtain(ctx, 40, 190, 200, 760, "#1e293b", t, 1)
    curtain(ctx, 840, 190, 200, 760, "#1e293b", t, -1)
    ctx.move_to(130, 900)
    ctx.line_to(950, 900)
    ctx.line_to(1200, 2000)
    ctx.line_to(-100, 2000)
    fill(ctx, "#9fb4ff", 0.05)
    poster(ctx, -40, 560, 160, 230, 0, 0.04)
    if lit > 0:
        ctx.rectangle(-800, -800, 2700, 3600)
        fill(ctx, "#60a5fa", 0.12 * lit)


def nightstand(ctx, t, clock_txt, phone_on, vib, glow_a=1.0):
    rr(ctx, 640, 1300, 380, 420, 14)
    lgrad(ctx, 640, 0, 1020, 0, [(0, "#22181a"), (0.5, "#3a2a2a"), (1, "#22181a")])
    ctx.fill()
    for k in range(2):
        rr(ctx, 665, 1330 + k * 190, 330, 160, 8)
        ctx.set_line_width(4)
        src(ctx, "#1a1112")
        ctx.stroke()
        ctx.arc(830, 1410 + k * 190, 9, 0, TAU)
        fill(ctx, "#8a7a5a")
    clock_digits(ctx, 760, 1210, 0.55, clock_txt)
    glass_water(ctx, 990, 1300, 0.8)
    ctx.save()
    v = math.sin(t * 90) * 7 if vib else 0
    ctx.translate(900 + v, 1288)
    ctx.scale(1, 0.34)
    if phone_on:
        glow(ctx, 0, 0, 520, "#7dd3fc", 0.6 * glow_a)
    phone_body(ctx, 0, 0, 170, 320, (lambda c, x, y, w, h: (vgrad(c, x, y, w, h, [(0, "#1e1b4b"), (1, "#0f172a")]),
                                                             rr(c, x + 14, y + 110, w - 28, 70, 12),
                                                             fill(c, "#ffffff", 0.9))) if phone_on else None)
    ctx.restore()


def bed_with_hero(ctx, t, sit, e, look=(0.9, 0.2), x=470):
    rr(ctx, -40, 1200, 700, 210, 40)
    fill(ctx, "#2a1e30")
    rr(ctx, 30, 1300, 260, 110, 50)
    fill(ctx, "#cbd5e1")
    ctx.save()
    ctx.translate(x, 1490)
    ctx.rotate(lerp(-1.42, 0, ease_out(sit)))
    hero(ctx, 0, 0, 0.92, e, t, legs=False, rim="#7ea0ff", rim_a=0.55, arms="down", look=look,
         blink=0 if sit > 0 else 1)
    ctx.restore()
    ctx.move_to(-40, 1480)
    ctx.curve_to(250, 1430, 500, 1440, 680, 1470)
    ctx.line_to(680, 2200)
    ctx.line_to(-40, 2200)
    fill(ctx, "#1d2d6b")
    for i in range(6):
        line(ctx, 30 + i * 120, 1500, 70 + i * 120, 2100, 10, "#16245a")


def bus(ctx, bx, by, t, sc=1.0, rot=0.0, doors_open=True):
    ctx.save()
    ctx.translate(bx, by)
    ctx.rotate(rot)
    ctx.scale(sc, sc)
    shadow(ctx, 540, 20, 600, 30, 0.45)
    rr(ctx, 0, -470, 1080, 430, 40)
    lgrad(ctx, 0, -470, 0, -40, [(0, "#f8c537"), (1, "#d99a0b")])
    ctx.fill()
    rr(ctx, 20, -462, 1040, 26, 12)
    fill(ctx, "#fcd34d", 0.7)
    for k in range(6):
        rr(ctx, 40 + k * 168, -430, 140, 160, 14)
        fill(ctx, "#2b3d52")
        rr(ctx, 50 + k * 168, -420, 40, 140, 10)
        fill(ctx, "#4f6a88", 0.6)
    for dx in (250, 700):
        rr(ctx, dx, -400, 130, 330, 8)
        fill(ctx, "#111820" if doors_open else "#3b4b5e")
        if doors_open:
            rr(ctx, dx - 34, -400, 30, 330, 6)
            fill(ctx, "#c8901a")
            rr(ctx, dx + 134, -400, 30, 330, 6)
            fill(ctx, "#c8901a")
    rr(ctx, 880, -470, 180, 60, 8)
    fill(ctx, "#111")
    text(ctx, "47", 970, -440, 40, "#fb923c")
    ell(ctx, 1060, -150, 22, 30)
    fill(ctx, "#fef9c3")
    for wx in (190, 880):
        ctx.arc(wx, -50, 96, TAU / 2, TAU)
        fill(ctx, "#b07a10")
        ctx.arc(wx, -50, 78, 0, TAU)
        fill(ctx, "#1c1c1c")
        ctx.arc(wx, -50, 40, 0, TAU)
        fill(ctx, "#9aa0a6")
    ctx.restore()


def car(ctx, x, y, t, sc=1.0, e=None, col="#e11d2e"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    ctx.save()
    ctx.translate(-30, -150)
    hero(ctx, 0, 0, 0.62, e, t, arms="wheel", legs=False, rim_a=0.5, look=(0.7, -0.1))
    ctx.restore()
    shadow(ctx, 0, 40, 520, 30, 0.5)
    ctx.move_to(-470, -40)
    ctx.curve_to(-470, -150, -380, -170, -230, -180)
    ctx.line_to(-120, -280)
    ctx.curve_to(0, -300, 120, -290, 200, -200)
    ctx.line_to(420, -170)
    ctx.curve_to(500, -160, 520, -100, 510, -40)
    ctx.close_path()
    lgrad(ctx, 0, -300, 0, -40, [(0, shade(col, 0.2)), (1, shade(col, -0.3))])
    ctx.fill()
    ctx.move_to(-190, -185)
    ctx.line_to(-100, -265)
    ctx.curve_to(-10, -280, 90, -275, 160, -205)
    ctx.close_path()
    fill(ctx, "#bfe3ff", 0.35)
    line(ctx, -440, -70, 480, -70, 6, shade(col, -0.4))
    line(ctx, -300, -150, 300, -160, 10, "#ffffff", 0.25)
    for wx in (-300, 300):
        ctx.arc(wx, -30, 82, 0, TAU)
        fill(ctx, "#141414")
        ctx.arc(wx, -30, 46, 0, TAU)
        fill(ctx, "#c9ccd1")
        for k in range(5):
            a = -t * 40 + k * TAU / 5
            line(ctx, wx, -30, wx + math.cos(a) * 42, -30 + math.sin(a) * 42, 8, "#6b6f75")
    ell(ctx, 495, -110, 20, 14)
    fill(ctx, "#fff7c2")
    ctx.restore()


def penthouse_bg(ctx, t, lights=0.35, warm=True):
    vgrad(ctx, -1200, -1200, 3500, 4400, [(0, "#0b1022"), (1, "#151c36")])
    ctx.save()
    rr(ctx, -300, 0, 1680, 1400, 0)
    ctx.clip()
    sky(ctx, 1080, 1400, "night")
    stars(ctx, 5, 1080, 700, t, 50)
    skyline(ctx, 71, -400, 1500, 1400, 350, 900, "#0b1124", "#ffd27a", lights, lit_seed=3)
    skyline(ctx, 72, -400, 1500, 1400, 150, 520, "#060a17", "#ffb84a", lights * 0.8, wmin=160, wmax=260)
    ctx.restore()
    for x0 in (-300, 260, 820, 1380):
        ctx.rectangle(x0 - 12, 0, 24, 1400)
        fill(ctx, "#05070e")
    ctx.rectangle(-1200, 1400, 3500, 1600)
    lgrad(ctx, 0, 1400, 0, 3000, [(0, "#2b2420"), (1, "#15110e")])
    ctx.fill()
    rug(ctx, 540, 1700, 520, 120, "#3f1d2b")


def sofa(ctx, x, y, w=760, col="#334155"):
    shadow(ctx, x, y + 10, w * 0.6, 30, 0.5)
    rr(ctx, x - w / 2, y - 330, w, 200, 60)
    lgrad(ctx, 0, y - 330, 0, y - 130, [(0, shade(col, 0.15)), (1, shade(col, -0.2))])
    ctx.fill()
    rr(ctx, x - w / 2 - 20, y - 170, w + 40, 150, 40)
    fill(ctx, shade(col, -0.05))
    for k in (-1, 1):
        rr(ctx, x + k * (w / 2 + 10) - 50, y - 260, 100, 250, 40)
        fill(ctx, shade(col, -0.15))
    for k in range(3):
        rr(ctx, x - w / 2 + 40 + k * (w - 80) / 3, y - 190, (w - 80) / 3 - 10, 40, 16)
        fill(ctx, shade(col, 0.08))


def wall_clock_digital(ctx, x, y, s, txt):
    clock_digits(ctx, x, y, s, txt, 1.0, "#ff3b30")


def strings(ctx, pts, t, a=0.4):
    for k, (x, y) in enumerate(pts):
        sw = math.sin(t * 1.5 + k) * 10
        ctx.move_to(x + sw, -1200)
        ctx.line_to(x, y)
        ctx.set_line_width(3)
        src(ctx, "#e5e7eb", a)
        ctx.stroke()
    # крестовина
    cx = sum(p[0] for p in pts) / len(pts)
    rr(ctx, cx - 260, -300 + math.sin(t) * 6, 520, 22, 8)
    fill(ctx, "#6b4226", a * 1.6)


# ================================================================== СЦЕНЫ
def s0_hook(ctx, t, u, D):
    """Холодный старт: экран переписки с «Я», глитч, вспышки двойника."""
    msgs = ["Не отвечай.", "Не открывай дверь.", "Он уже рядом.", "Это не я.", "НЕ ОТВЕЧАЙ", "3:07"]
    k = u * 2.6
    shown = [(0, m, 1.0) for m in msgs[:min(len(msgs), int(k) + 1)]]
    gl = 0.6 + 0.4 * math.sin(t * 13)
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(1.25, 1.05, ease_out(seg(u, 0, D))), rot=lerp(0.05, 0.0, seg(u, 0, D)), shake=1.0)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#000"), (1, "#05060a")])
    hands_phone(ctx, t, chat_screen(shown[-4:], t, typing=True, double=True, glitch=gl), tremble=1.6)
    ctx.restore()
    # вспышки двойника (по 3–4 кадра)
    for f0 in (0.95, 1.9):
        if f0 <= u < f0 + 0.12:
            src(ctx, "#000")
            ctx.paint()
            hero_head(ctx, 540, 900, 380, emo("crazy"), t, rim=DOUBLE_RIM, rim_a=1.0)
            r = random.Random(int(t * 40))
            for i in range(12):
                ctx.rectangle(0, r.random() * H, W, r.uniform(6, 40))
                fill(ctx, r.choice(["#ff0040", "#00e5ff", "#7CFF6B"]), 0.35)
    # перемотка назад в конце хука
    if u > D - 0.45:
        r = random.Random(int(t * 30))
        for i in range(10):
            y = r.random() * H
            ctx.rectangle(0, y, W, r.uniform(3, 12))
            fill(ctx, "#ffffff", 0.35)
        rr(ctx, 90, 880, 900, 160, 30)
        fill(ctx, "#000", 0.8)
        for k in range(2):
            ctx.move_to(150 + k * 60, 960)
            ctx.line_to(210 + k * 60, 920)
            ctx.line_to(210 + k * 60, 1000)
            ctx.close_path()
            fill(ctx, "#ffffff")
        text(ctx, "ГОД НАЗАД", 600, 960, 84, "#ffffff", "#000", 12)


def s1_wake(ctx, t, u, D):
    flip = EV["flip1"] - TL.shots[1][0]
    vib = EV["vib"][0] - TL.shots[1][0]
    on = u > vib
    wake = seg(u, vib + 0.4, vib + 0.9)
    z = lerp(0.95, 1.12, ease(seg(u, 0, D))) + 0.3 * ease_out(seg(u, wl(1, "собственного") - 0.1,
                                                                 wl(1, "собственного") + 0.15))
    ctx.save()
    cam(ctx, t, lerp(560, 760, ease(seg(u, vib, D))), lerp(1150, 1250, ease(seg(u, vib, D))), z, shake=0.35)
    bedroom_night(ctx, t, 1.0 if on else 0.0)
    bed_with_hero(ctx, t, wake, emo("sleep") if wake <= 0 else emo("neutral", "shock", seg(u, wl(1, "собственного"),
                                                                                         wl(1, "собственного") + .2)))
    nightstand(ctx, t, "3:06" if u < flip else "3:07", on, on and (u - vib) % 1.0 < 0.5)
    ctx.restore()
    # уведомление на экране
    if on:
        k = back_out(seg(u, vib, vib + 0.35))
        ctx.save()
        ctx.translate(540, 360)
        ctx.scale(k, k)
        rr(ctx, -440, -90, 880, 180, 40)
        fill(ctx, "#f4f4f5", 0.95)
        me_avatar(ctx, -350, 0, 55, t)
        text(ctx, "Я", -270, -30, 44, "#111", align="left")
        text(ctx, "1 новое сообщение · 3:07", -270, 30, 34, "#52525b", align="left")
        ctx.restore()
    if not on:
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#000", 0.3)


def s2_bus_msg(ctx, t, u, D):
    a, b = EV["typing"][0][1], EV["typing"][0][2]
    msg = typed("Не садись завтра в автобус 47.", t, a, b)
    ctx.save()
    cam(ctx, t, 540, 860, lerp(1.2, 1.4, ease(seg(u, 0, D))), shake=0.6)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#000"), (1, "#05060a")])
    hands_phone(ctx, t, chat_screen([(0, msg, 1.0)], t, typing=len(msg) < 30), tremble=1.0)
    ctx.restore()


def s3_bus_news(ctx, t, u, D):
    ev = EV["evening"] - TL.shots[3][0]
    ctx.save()
    if u < ev:  # утро: остановка, автобус 47 ждёт с открытыми дверями, герой уходит пешком
        k = u / ev
        cam(ctx, t, lerp(500, 700, k), 1120, lerp(0.8, 0.88, k), shake=0.4)
        sky(ctx, 1080, 1250, "morning")
        skyline(ctx, 12, -1200, 2600, 1150, 250, 520, "#8fb0cc", "#b9cfe0", 0.4, wmin=150, wmax=260)
        ctx.rectangle(-1500, 1250, 5000, 150)
        fill(ctx, "#b8b3aa")
        ctx.rectangle(-1500, 1390, 5000, 22)
        fill(ctx, "#8e8a82")
        ctx.rectangle(-1500, 1410, 5000, 700)
        fill(ctx, "#3d3f45")
        for i in range(-10, 30):
            rr(ctx, i * 260, 1690, 140, 18, 9)
            fill(ctx, "#f2f2f2")
        # остановка
        rr(ctx, 840, 820, 520, 30, 8)
        fill(ctx, "#334155")
        for px in (860, 1320):
            rr(ctx, px, 840, 18, 430, 6)
            fill(ctx, "#475569")
        rr(ctx, 900, 880, 380, 300, 10)
        fill(ctx, "#bfdbfe", 0.35)
        rr(ctx, 1040, 990, 120, 160, 8)
        fill(ctx, "#f59e0b")
        text(ctx, "47", 1100, 1050, 70, "#111")
        bench(ctx, 1100, 1270, 0.7)
        lamp_post(ctx, 300, 1330)
        tree(ctx, -150, 1300, 0.85, t, 3)
        trash_bin(ctx, 1450, 1320, 0.9)
        bus(ctx, 1500 - 900 * ease_out(seg(u, 0, 1.2)), 1700, t, 0.95)
        # прохожие ждут
        r = random.Random(4)
        for i in range(2):
            p = Npc(r, 980 + i * 200, 1300, 0.62, -1)
            npc(ctx, p, t, walking=False)
        lw = wl(3, "смеешься")
        e = emo("happy") if u < lw + 1.1 else emo("sly")
        hero(ctx, lerp(560, -80, ease(seg(u, lw + 1.2, ev))), 1340, 0.85, e, t, arms="relax",
             walk=t * 8 if u > lw + 1.2 else None, look=(-0.6, 0), blink=blink_at(u, 0.2))
        if u < lw + 1.2:
            text(ctx, "ХА-ХА", 640, 640, 80, "#ffd400", "#000", 12, alpha=seg(u, lw, lw + 0.2))
    else:  # вечер: новости по ТВ
        k = seg(u, ev, D)
        cam(ctx, t, 540, lerp(900, 980, k), lerp(0.9, 1.15, ease(k)), shake=0.4)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#2b2333"), (1, "#18131f")])
        # ТВ на стене
        rr(ctx, 60, 300, 960, 600, 20)
        fill(ctx, "#050507")
        ctx.save()
        rr(ctx, 80, 320, 920, 560, 10)
        ctx.clip()
        vgrad(ctx, 80, 320, 920, 560, [(0, "#1e2a44"), (1, "#3b4660")])
        # мост
        ctx.rectangle(80, 690, 920, 40)
        fill(ctx, "#6b7280")
        for k2 in range(4):
            ctx.arc(200 + k2 * 230, 820, 115, TAU / 2, TAU)
            ctx.set_line_width(14)
            src(ctx, "#4b5563")
            ctx.stroke()
        for k2 in range(12):
            line(ctx, 80 + k2 * 80, 650, 80 + k2 * 80, 690, 6, "#9ca3af")
        line(ctx, 80, 650, 1000, 650, 6, "#9ca3af")
        ctx.rectangle(80, 730, 920, 150)
        fill(ctx, "#1e3a5f")
        bus(ctx, 250, 760, t, 0.5, rot=-0.42, doors_open=False)  # опрокинут
        puff(ctx, 560, 600, t, 5, rate=0.2, dx=40, dy=-200, a=0.5, col="#6b7280")
        # мигалки
        for k2, px in enumerate((160, 860)):
            on = (t * 4 + k2) % 1 < 0.5
            glow(ctx, px, 640, 150, "#ef4444" if on else "#3b82f6", 0.7)
            rr(ctx, px - 60, 640, 120, 50, 10)
            fill(ctx, "#f8fafc")
        ctx.rectangle(80, 790, 920, 90)
        fill(ctx, "#d61f1f")
        text(ctx, "СРОЧНО: АВТОБУС №47 НА МОСТУ", 100, 835, 44, "#ffffff", align="left")
        rr(ctx, 860, 340, 110, 46, 8)
        fill(ctx, "#d61f1f")
        text(ctx, "LIVE", 915, 363, 30, "#fff")
        r = random.Random(int(t * 24))
        for i in range(5):
            ctx.rectangle(80, 320 + r.random() * 560, 920, 2)
            fill(ctx, "#ffffff", 0.12)
        ctx.restore()
        glow(ctx, 540, 600, 700, "#60a5fa", 0.15)
        # комната
        ctx.rectangle(-800, 1250, 2700, 1500)
        fill(ctx, "#1f1a24")
        sofa(ctx, 540, 1700, 900, "#3b3346")
        plant(ctx, 1080, 1300, 1.0, t, "#57534e")
        ld = wl(3, "лежит")
        hero(ctx, 540, 1640, 1.05, emo("neutral", "shock", seg(u, ld - 0.1, ld + 0.2)), t,
             arms=arms_lerp("hold", "shock", seg(u, ld, ld + 0.25)), legs=False, look=(0, -0.6),
             tremble=0.8 if u > ld else 0, rim="#60a5fa",
             hand_item=(lambda c, x, y: coffee_cup(c, x - 30, y + 40, 0.3, t)) if u < ld else None)
        if u > ld:  # кружка падает
            kk = seg(u, ld, ld + 0.6)
            ctx.save()
            ctx.translate(700, 1300 + 500 * ease_in(kk))
            ctx.rotate(kk * 3)
            coffee_cup(ctx, 0, 0, 0.3, t, heart=False)
            ctx.restore()
    ctx.restore()


def s4_stocks_msg(ctx, t, u, D):
    buy = EV["buy"] - TL.shots[4][0]
    ctx.save()
    if u < buy:  # часы 3:07 крупно, герой ухмыляется в свете телефона
        cam(ctx, t, 600, 1150, lerp(1.0, 1.2, ease(seg(u, 0, buy))), shake=0.3)
        bedroom_night(ctx, t, 0.6)
        bed_with_hero(ctx, t, 1.0, emo("sly"), look=(0.9, 0.3))
        nightstand(ctx, t, "3:07", True, (u % 1.0) < 0.5)
    else:
        a, b = EV["typing"][1][1], EV["typing"][1][2]
        msg = typed("Купи акции NOVA. О ней никто не слышал.", t, a, b)
        cam(ctx, t, 540, 860, lerp(1.2, 1.35, ease(seg(u, buy, D))), shake=0.5)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#000"), (1, "#05060a")])
        old = [(0, "Не садись завтра в автобус 47.", 0.45)]
        hands_phone(ctx, t, chat_screen(old + [(0, msg, 1.0)], t, typing=len(msg) < 39), tremble=0.6)
    ctx.restore()


def s5_rocket(ctx, t, u, D):
    x40 = EV["x40"] - TL.shots[5][0]
    k = seg(u, 0, x40 + 0.4)
    ctx.save()
    cam(ctx, t, 540, 960, lerp(0.95, 1.05, ease(seg(u, 0, D))), shake=0.6 + 0.6 * seg(u, x40, x40 + 0.2))
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#04140c"), (1, "#0b1f18")])
    for i in range(-4, 16):
        line(ctx, -400, 200 + i * 120, 1500, 200 + i * 120, 2, "#1f3d31")
        line(ctx, -400 + i * 120, -200, -400 + i * 120, 2200, 2, "#1f3d31")
    text(ctx, "NOVA", 80, 330, 70, "#e5e7eb", align="left")
    pct = int(3900 * ease_in(k, 2.2))
    text(ctx, f"+{pct}%", 80, 420, 64, "#22c55e", align="left")
    # свечи
    r = random.Random(5)
    n = 26
    prev = 1500
    pts = []
    for i in range(n):
        x = 60 + i * 38
        if i / n > k:
            break
        target = 1500 - 1200 * ((i / n) ** 3.2)
        o, c_ = prev, target + r.uniform(-40, 40)
        up = c_ < o
        rr(ctx, x, min(o, c_), 26, max(8, abs(c_ - o)), 4)
        fill(ctx, "#22c55e" if up else "#ef4444")
        line(ctx, x + 13, min(o, c_) - 20, x + 13, max(o, c_) + 20, 3, "#22c55e" if up else "#ef4444")
        pts.append((x + 13, c_))
        prev = c_
    if len(pts) > 1:
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.set_line_width(8)
        src(ctx, "#86efac", 0.8)
        ctx.stroke()
        glow(ctx, pts[-1][0], pts[-1][1], 120, "#86efac", 0.8)
        # ракета на конце графика
        ctx.save()
        ctx.translate(pts[-1][0] + 30, pts[-1][1] - 40)
        ctx.rotate(-0.8)
        rr(ctx, -20, -60, 40, 110, 20)
        fill(ctx, "#e5e7eb")
        ctx.move_to(-20, 20)
        ctx.line_to(-38, 50)
        ctx.line_to(-20, 40)
        fill(ctx, "#ef4444")
        ctx.move_to(20, 20)
        ctx.line_to(38, 50)
        ctx.line_to(20, 40)
        fill(ctx, "#ef4444")
        ctx.arc(0, -20, 10, 0, TAU)
        fill(ctx, "#60a5fa")
        puff(ctx, 0, 60, t, 3, rate=0.06, dx=0, dy=120, a=0.7, col="#fbbf24", life=0.4)
        ctx.restore()
    # деньги
    if u > x40 - 0.2:
        r = random.Random(11)
        for i in range(30):
            x = r.uniform(-100, 1180)
            y = (r.uniform(-600, 0) + (u - x40 + 0.2) * r.uniform(500, 900))
            ctx.save()
            ctx.translate(x + math.sin(t * 3 + i) * 30, y)
            ctx.rotate(math.sin(t * 2 + i))
            rr(ctx, -60, -30, 120, 60, 6)
            fill(ctx, "#4ade80")
            rr(ctx, -50, -22, 100, 44, 4)
            ctx.set_line_width(3)
            src(ctx, "#166534")
            ctx.stroke()
            text(ctx, "100", 0, 0, 26, "#166534")
            ctx.restore()
    hero(ctx, 540, 1880 - abs(math.sin(u * 7)) * 120 * seg(u, x40 - 0.3, x40), 1.0,
         emo("joy") if u > x40 - 0.3 else emo("sly"), t, arms="cheer" if u > x40 - 0.3 else "hold", rim="#22c55e")
    ctx.restore()
    if u > x40:
        s = back_out(seg(u, x40, x40 + 0.3))
        ctx.save()
        ctx.translate(540, 760)
        ctx.scale(s, s)
        ctx.rotate(-0.08)
        text(ctx, "×40", 0, 0, 260, "#ffd400", "#000", 22, shadow=True)
        ctx.restore()


def s6_who(ctx, t, u, D):
    a, b = EV["typing"][2][1], EV["typing"][2][2]
    rep = EV["reply"] - TL.shots[6][0]
    q = typed("Кто ты?", t, a, b)
    ans = typed("Ты. Только на год старше.", t, EV["reply"], TL.lend(6))
    old = [(0, "Не садись завтра в автобус 47.", 0.35), (0, "Купи акции NOVA. О ней никто не слышал.", 0.35)]
    ctx.save()
    if u < D - 0.9:
        cam(ctx, t, 540, 860, lerp(1.2, 1.32, ease(seg(u, 0, D))), shake=0.5)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#000"), (1, "#05060a")])
        msgs = old + [(1, q, 1.0)] + ([(0, ans, 1.0)] if u >= rep else [])
        hands_phone(ctx, t, chat_screen(msgs, t, typing=(b - TL.shots[6][0] < u < rep) or (0 < len(ans) < 24),
                                        glitch=0.4 if abs(u - rep) < 0.2 else 0), tremble=0.8)
    else:  # лицо в шоке, лёгкий наезд
        k = seg(u, D - 0.9, D)
        cam(ctx, t, 540, 900, lerp(1.0, 1.15, k), shake=0.8)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0a1024"), (1, "#141c36")])
        glow(ctx, 540, 1400, 900, "#60a5fa", 0.35)
        hero(ctx, 540, 1700, 2.0, emo("shock"), t, arms="down", legs=False, tremble=1.0, rim="#60a5fa")
    ctx.restore()


PARTY = None


def party_crowd():
    global PARTY
    if PARTY is None:
        r = random.Random(77)
        PARTY = []
        for i, (x, y, sc, d) in enumerate(((60, 1500, 0.95, 1), (230, 1350, 0.75, 1), (850, 1350, 0.75, -1),
                                           (1020, 1500, 0.95, -1), (400, 1200, 0.6, 1), (700, 1200, 0.6, -1),
                                           (-120, 1350, 0.8, 1), (1200, 1350, 0.8, -1))):
            PARTY.append(Npc(r, x, y, sc, d))
    return PARTY


def s7_life(ctx, t, u, D):
    s0 = TL.shots[7][0]
    a, b, c = (x - s0 for x in EV["sub7"])
    ctx.save()
    if u < b:  # пентхаус с видом
        k = seg(u, 0, b)
        cam(ctx, t, lerp(400, 640, k), 1080, lerp(1.0, 0.85, ease(k)), shake=0.3)
        penthouse_bg(ctx, t, 0.45)
        hanging_lamp(ctx, 540, 260, on=True, col="#d4a849")
        sofa(ctx, 540, 1650, 820, "#e7e5e4")
        plant(ctx, 1080, 1600, 1.2, t, "#a8a29e")
        table_lamp(ctx, 100, 1500, 1.0)
        hero(ctx, 540, 1600, 0.95, emo("happy"), t, arms="hold", legs=False,
             hand_item=lambda cc, x, y: coffee_cup(cc, x - 30, y + 40, 0.3, t))
        text(ctx, "ГОД СПУСТЯ", 540, 600, 96, "#ffffff", "#000", 14, alpha=seg(u, 0.1, 0.4) * (1 - seg(u, a + 1.2, a + 1.5)))
    elif u < c:  # машина мечты
        k = seg(u, b, c)
        cam(ctx, t, 540, 1150, lerp(0.95, 1.08, k), shake=0.9)
        sky(ctx, 1080, 1300, "dusk")
        ctx.save()
        ctx.translate(-(u * 300) % 1400, 0)
        for rep in range(3):
            skyline(ctx, 61, -800 + rep * 1400, 600 + rep * 1400, 1300, 200, 700, "#1a1630", "#ffd27a", 0.3,
                    wmin=150, wmax=280)
        ctx.restore()
        ctx.rectangle(-800, 1300, 3000, 900)
        fill(ctx, "#1f1f26")
        for i in range(-4, 12):
            rr(ctx, (i * 300 - u * 3600) % 3600 - 1200, 1560, 170, 16, 8)
            fill(ctx, "#fde68a")
        car(ctx, 540, 1520, t, 1.0, emo("joy"), "#111827")
        speed_lines(ctx, 1080, 1900, t, n=30, a=0.45)
    else:  # вечеринка: друзья слишком внимательные
        k = seg(u, c, D)
        cam(ctx, t, 540, 1150, lerp(0.95, 1.25, ease(k)), shake=0.4)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1b0f2e"), (1, "#2d1446")])
        for i in range(6):  # диско-лучи
            ang = t * 0.8 + i * TAU / 6
            ctx.move_to(540, 200)
            ctx.line_to(540 + math.cos(ang) * 2000, 200 + abs(math.sin(ang)) * 2000)
            ctx.line_to(540 + math.cos(ang + 0.12) * 2000, 200 + abs(math.sin(ang + 0.12)) * 2000)
            ctx.close_path()
            fill(ctx, ["#f472b6", "#60a5fa", "#facc15"][i % 3], 0.12)
        ctx.arc(540, 200, 70, 0, TAU)
        fill(ctx, "#cbd5e1")
        for i in range(8):
            rr(ctx, 500 + (i % 4) * 22, 150 + (i // 4) * 30, 18, 18, 3)
            fill(ctx, "#ffffff", 0.5 + 0.5 * math.sin(t * 6 + i))
        ctx.rectangle(-800, 1200, 2700, 1500)
        fill(ctx, "#140a20")
        crowd_ = party_crowd()
        wide = seg(u, wl(7, "внимательными") - 0.4, wl(7, "внимательными") + 0.3)
        for p in sorted(crowd_, key=lambda q: q.y):
            # все смотрят на героя
            p.dir = 1 if p.x < 540 else -1
            npc(ctx, p, t, walking=False, grin=0.4 + 0.8 * wide)
        hero(ctx, 540, 1700, 0.95, emo("happy", "worry", wide), t, arms="cheer" if wide < 0.5 else "down",
             look=(math.sin(t * 2) * 0.8 * wide, 0), rim="#f472b6")
        r = random.Random(2)
        for i in range(40):  # конфетти
            x = r.uniform(-100, 1180)
            y = (r.uniform(-400, 1800) + u * r.uniform(150, 300)) % 2000 - 100
            ctx.save()
            ctx.translate(x, y)
            ctx.rotate(t * 3 + i)
            ctx.rectangle(-8, -4, 16, 8)
            fill(ctx, r.choice(["#f472b6", "#60a5fa", "#facc15", "#34d399"]))
            ctx.restore()
    ctx.restore()


def s8_puppet(ctx, t, u, D):
    flip = EV["flip8"] - TL.shots[8][0]
    ctx.save()
    cam(ctx, t, 540, lerp(1050, 1150, ease(seg(u, 0, D))), lerp(0.85, 1.15, ease(seg(u, 0, D))), shake=0.2)
    penthouse_bg(ctx, t, 0.08, warm=False)
    ctx.rectangle(-1200, -1200, 3500, 4400)
    fill(ctx, "#000", 0.35)
    wall_clock_digital(ctx, 540, 260, 0.9, "3:06" if u < flip else "3:07")
    sofa(ctx, 540, 1650, 820, "#334155")
    # герой-марионетка: неподвижный взгляд на часы
    e = emo("neutral")
    e["pup"] = 0.45
    e["lid"] = 0.05
    hero(ctx, 540, 1600, 0.95, e, t, arms="relax", legs=False, look=(0, -0.9), rim="#ef4444",
         rim_a=0.4 + 0.6 * seg(u, flip, flip + 0.2))
    hx, hy = 540, 1600 + 170 * 0.95
    strings(ctx, [(hx - 150, hy - 330), (hx + 150, hy - 330), (hx, hy - 560)], t, 0.35)
    ctx.restore()
    if u > flip:
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#ef4444", 0.12 * (1 - seg(u, flip, flip + 0.5)))


def s9_last(ctx, t, u, D):
    a, b = EV["typing"][3][1], EV["typing"][3][2]
    msg = typed("Завтра я перестану писать. Что бы ни случилось — не открывай дверь.", t, a, b)
    old = [(0, "Купи акции NOVA. О ней никто не слышал.", 0.3), (1, "Кто ты?", 0.3),
           (0, "Ты. Только на год старше.", 0.3)]
    fl = 0.7 if random.Random(int(t * 12)).random() < 0.12 else 0.0
    ctx.save()
    cam(ctx, t, 540, 860, lerp(1.15, 1.35, ease(seg(u, 0, D))), shake=0.6)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#000"), (1, "#05060a")])
    hands_phone(ctx, t, chat_screen(old + [(0, msg, 1.0)], t, typing=0 < len(msg) < 60, flicker=fl), tremble=1.0)
    ctx.restore()


def hallway(ctx, t, shake_k=0.0, under=1.0):
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0d0b0a"), (1, "#1a1512")])
    for i in range(-3, 9):  # обои
        line(ctx, i * 160, -800, i * 160, 2400, 6, "#16120f")
    # вешалка, куртка, обувь
    rr(ctx, -140, 520, 240, 24, 8)
    fill(ctx, "#3b2a1a")
    ctx.move_to(-110, 540)
    ctx.line_to(-170, 950)
    ctx.line_to(30, 950)
    ctx.line_to(-30, 540)
    fill(ctx, "#1e3a5f")
    for k in range(3):
        ell(ctx, -120 + k * 90, 1410, 40, 16)
        fill(ctx, "#2b2b2b")
    mirror_x = 1110
    rr(ctx, mirror_x - 110, 480, 220, 380, 100)
    fill(ctx, "#2b2b30")
    rr(ctx, mirror_x - 95, 495, 190, 350, 90)
    fill(ctx, "#4b5563", 0.5)
    # дверь
    dx = math.sin(t * 70) * 10 * shake_k
    ctx.save()
    ctx.translate(dx, 0)
    rr(ctx, 230, 280, 620, 1150, 6)
    fill(ctx, "#0a0806")
    rr(ctx, 250, 300, 580, 1110, 4)
    lgrad(ctx, 250, 0, 830, 0, [(0, "#3f2a1d"), (0.5, "#5c3d29"), (1, "#3a2619")])
    ctx.fill()
    for k in range(2):
        rr(ctx, 300, 360 + k * 520, 480, 440, 6)
        ctx.set_line_width(5)
        src(ctx, "#2a1a10")
        ctx.stroke()
    ctx.arc(540, 560, 22, 0, TAU)
    fill(ctx, "#d4a849")
    ctx.arc(540, 560, 12, 0, TAU)
    fill(ctx, "#111")
    rr(ctx, 740, 820, 70, 28, 10)
    fill(ctx, "#a88a4a")
    for k in range(5):
        ell(ctx, 690 + k * 22, 700 + k * 8, 14, 8)
        ctx.set_line_width(5)
        src(ctx, "#c0c4ca")
        ctx.stroke()
    ctx.restore()
    ctx.rectangle(250, 1410, 580, 14)
    fill(ctx, "#ffcf7a", under)
    glow(ctx, 540, 1440, 380, "#ffb54a", 0.35 * under)
    ctx.rectangle(-800, 1424, 2700, 1500)
    fill(ctx, "#120d0a")
    rr(ctx, 300, 1450, 480, 90, 12)
    fill(ctx, "#2b1d12")


def s10_knock(ctx, t, u, D):
    kn = [k - TL.shots[10][0] for k in EV["knocks"]]
    sk = 0.0
    for k in kn:
        if 0 <= u - k < 0.25:
            sk = 1 - (u - k) / 0.25
    z = lerp(0.85, 1.0, ease(seg(u, 0, D))) + 0.06 * sk
    ctx.save()
    cam(ctx, t, 540, 960, z, shake=0.3 + 1.2 * sk)
    under = 1.0 if random.Random(int(t * 10)).random() > 0.15 or u < kn[0] else 0.3
    hallway(ctx, t, sk, under)
    # пыль с косяка
    for k in kn:
        if u > k:
            r = random.Random(int(k * 100))
            for i in range(14):
                age = u - k
                if age > 1.6:
                    continue
                ctx.arc(250 + r.uniform(0, 580), 300 + age * r.uniform(200, 400), r.uniform(2, 5), 0, TAU)
                fill(ctx, "#d6d3d1", 0.6 * (1 - age / 1.6))
    hero(ctx, 900, 2050, 1.4, emo("fear"), t, arms="down", back=True, rim="#ffb36b", rim_a=0.7,
         tremble=0.6 if u > kn[0] else 0)
    ctx.restore()
    if sk > 0:
        text(ctx, "ТУК", 540 + (kn.index(min(kn, key=lambda q: abs(u - q))) - 1) * 260, 420, 110, "#ffffff",
             "#000", 14, alpha=sk)


def landing(ctx, t, lamp=1.0):
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#2a2620"), (1, "#141210")])
    ctx.rectangle(-800, 1350, 2700, 1200)
    fill(ctx, "#2a2a2a")
    for i in range(-6, 14):
        line(ctx, 540, 1350, i * 200 - 600, 2400, 3, "#1f1f1f")
    line(ctx, -200, 300, 1300, 300, 5, "#3a352c")
    apartment_door(ctx, -60, 1350, 240, 520, "48")
    apartment_door(ctx, 900, 1350, 240, 520, "50")
    line(ctx, 540, 0, 540, 220, 5, "#111")
    ctx.arc(540, 240, 26, 0, TAU)
    fill(ctx, "#fff3c4" if lamp > 0.5 else "#3a3a3a")
    if lamp > 0.5:
        glow(ctx, 540, 300, 700, "#ffe08a", 0.45)


def s11_peephole(ctx, t, u, D):
    rv = EV["reveal"] - TL.shots[11][0]
    wv = EV["wave"] - TL.shots[11][0]
    src(ctx, "#000")
    ctx.paint()
    R = 470
    cx, cy = 540, 900
    ctx.save()
    ctx.arc(cx, cy, R, 0, TAU)
    ctx.clip()
    ctx.save()
    zz = lerp(1.0, 1.12, ease(seg(u, 0, D)))
    ctx.translate(cx, cy)
    ctx.scale(zz * 0.8, zz * 0.8)  # «рыбий глаз»
    ctx.translate(-540, -900)
    lamp = 0.0 if random.Random(int(t * 9)).random() < 0.1 else 1.0
    landing(ctx, t, lamp)
    if u >= rv:
        e = emo("crazy")
        e["pup"] = 0.35
        wave = seg(u, wv - 0.2, wv)
        arms = ((0.18, 0.05), (lerp(0.18, 2.5, wave), lerp(0.05, 0.4 * math.sin(t * 9), wave)))
        hero(ctx, 540, 1650, 1.9, e, t, arms=arms, look=(0, 0), rim=DOUBLE_RIM, rim_a=1.0,
             tilt=0.08 * math.sin(t * 0.7))
    ctx.restore()
    # линза: затемнение по краю и блики
    g = cairo.RadialGradient(cx, cy, R * 0.55, cx, cy, R)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.92)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    ctx.arc(cx, cy, R, 0, TAU)
    ctx.set_line_width(10)
    src(ctx, "#1a1a1a")
    ctx.stroke()
    ell(ctx, cx - 160, cy - 200, 90, 40)
    fill(ctx, "#ffffff", 0.06)
    if rv <= u < rv + 0.12:
        src(ctx, "#ffffff", 0.5)
        ctx.paint()


def s12_notme(ctx, t, u, D):
    nm = EV["notme"] - TL.shots[12][0]
    h0, h1 = (x - TL.shots[12][0] for x in EV["handle"])
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < nm:  # лицо героя у двери, телефон вибрирует в руке
        cam(ctx, t, 540, 960, lerp(1.0, 1.12, ease(seg(u, 0, nm))), shake=0.7)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#120d0a"), (1, "#0a0706")])
        glow(ctx, 760, 1500, 700, "#60a5fa", 0.35 * (0.7 + 0.3 * math.sin(t * 30)))
        hero(ctx, 540, 1650, 1.9, emo("fear"), t, arms="phone", legs=False, tremble=1.2, rim="#60a5fa",
             look=(0.6, 0.7), hand_item=lambda c, x, y: (rr(c, x - 40, y - 140, 80, 150, 12), fill(c, "#111"),
                                                         rr(c, x - 32, y - 132, 64, 120, 8), fill(c, "#7dd3fc")))
    elif u < h0:
        a, b = EV["typing"][4][1], EV["typing"][4][2]
        msg = typed("Это не я.", t, a, b)
        old = [(0, "Завтра я перестану писать. Что бы ни случилось — не открывай дверь.", 0.35)]
        cam(ctx, t, 540, 860, lerp(1.25, 1.5, ease(seg(u, nm, h0))), shake=0.8)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#000"), (1, "#05060a")])
        hands_phone(ctx, t, chat_screen(old + [(0, msg, 1.0)], t, glitch=0.5 if u > nm + 0.8 else 0.0),
                    tremble=1.5)
    elif u < ec:  # ручка двери медленно поворачивается
        k = seg(u, h0, h1)
        cam(ctx, t, 740, 840, lerp(1.6, 2.0, ease(seg(u, h0, ec))), shake=0.25)
        hallway(ctx, t, 0.0, 1.0)
        ctx.save()
        ctx.translate(740, 834)
        ctx.rotate(-0.55 * ease(k))
        ctx.translate(-740, -834)
        rr(ctx, 730, 810, 110, 34, 14)
        fill(ctx, "#c9a24a")
        ctx.restore()
        ctx.arc(740, 834, 26, 0, TAU)
        fill(ctx, "#a88a4a")
        if u > ec - 0.5:
            ctx.restore()
            ctx.save()
            ctx.rectangle(0, 0, W, H)
            fill(ctx, "#000", seg(u, ec - 0.5, ec - 0.1))
    else:  # финальная карточка
        k = seg(u, ec, ec + 0.6)
        src(ctx, "#000")
        ctx.paint()
        s = back_out(k)
        ctx.translate(540, 820)
        ctx.scale(s, s)
        text(ctx, "ПРОДОЛЖЕНИЕ", 0, -190, 70, "#ffffff")
        text(ctx, "ЧАСТЬ 2", 0, -10, 190, "#ffd400", "#d8332a", 18)
        text(ctx, "Кто стоит за дверью?", 0, 180, 64, "#7CFF6B")
        ea = seg(u, ec + 0.4, ec + 1.0)
        ctx.translate(0, 470)
        ctx.scale(0.7, 0.7)
        e = emo("crazy")
        e["pup"] = 0.35
        hero_head(ctx, 0, 0, 120 * ea + 0.01, e, t, rim=DOUBLE_RIM, rim_a=ea)
    ctx.restore()


SCENES = [s0_hook, s1_wake, s2_bus_msg, s3_bus_news, s4_stocks_msg, s5_rocket, s6_who, s7_life, s8_puppet,
          s9_last, s10_knock, s11_peephole, s12_notme]
LABELS = {1: "НОЧЬ 1", 2: "НОЧЬ 1", 3: "ДЕНЬ 1", 4: "НОЧЬ 2", 5: "ДЕНЬ 31", 6: "НОЧЬ 31", 7: "ДЕНЬ 300",
          8: "ДЕНЬ 365", 9: "ДЕНЬ 365", 10: "3:07", 11: "3:07", 12: "3:07"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("три", "ноль", "семь"), "3:07"), (("сорок", "семь"), "47"), (("сорок",), "40")]


def disp_words(li):
    ws = TL.lines[li]["words"]
    out, i = [], 0
    while i < len(ws):
        for pat, rep in MERGE:
            n = len(pat)
            if tuple(w["w"].lower() for w in ws[i:i + n]) == pat:
                last = ws[i + n - 1]
                rep2 = "×40" if (li == 5 and rep == "40") else rep
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
        if i in LABELS:
            a = seg(t, TL.shots[i][0], TL.shots[i][0] + 0.3)
            text(ctx, LABELS[i], W - 60, 125, 46, "#ffffff", "#000", 10, align="right", alpha=a)
    if t < TL.shots[1][0]:  # заголовок-хук
        k1 = back_out(seg(t, 0.0, 0.3))
        out = 1 - seg(t, TL.shots[1][0] - 0.3, TL.shots[1][0])
        ctx.save()
        ctx.translate(540, 360)
        ctx.scale(k1, k1)
        ctx.push_group()
        text(ctx, "ЧТО, ЕСЛИ", 0, -110, 88, "#ffffff", "#000", 16, shadow=True)
        text(ctx, "ТЕБЕ ПИШЕШЬ", 0, 10, 110, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -260, 90, 520, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "ТЫ САМ?", 0, 155, 104, "#ffffff")
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
