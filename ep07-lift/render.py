"""Серия 7 «Лифт вниз»: python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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






# ================================================================== ЛИФТ
COL_A = "#f97316"   # голос из динамика
COL_B = "#f97316"
STEEL = [(0, "#6b7280"), (0.3, "#d1d5db"), (0.55, "#9ca3af"), (0.8, "#e5e7eb"), (1, "#6b7280")]


def floor_label(f):
    return str(f) if f >= 0 else "-" + str(-f)


def heat_at(t):
    return ease(seg(t, EV["hot"] - 1.0, EV["hot"] + 1.0)) * (1 - ease(seg(t, EV["open"], EV["open"] + 1.0)) * 0.5)


def led(ctx, x, y, w, h, txt, t, col="#ef4444", arrow=True):
    rr(ctx, x - w / 2, y - h / 2, w, h, 14)
    fill(ctx, "#050505")
    glow(ctx, x, y, w * 0.7, col, 0.25)
    text(ctx, "888", x + 30, y, h * 0.62, col, alpha=0.08)
    text(ctx, txt, x + 30, y, h * 0.62, col)
    if arrow:
        ax, ay = x - w / 2 + 50, y
        ctx.move_to(ax - 22, ay - 14)
        ctx.line_to(ax + 22, ay - 14)
        ctx.line_to(ax, ay + 20)
        ctx.close_path()
        fill(ctx, col, 0.5 + 0.5 * ((t * 2) % 1 < 0.6))


def lift_doors(ctx, x0, y0, w, h, open_k):
    for side in (0, 1):
        dw = w / 2 * (1 - open_k)
        if dw < 1:
            continue
        dx = x0 if side == 0 else x0 + w - dw
        rr(ctx, dx, y0, dw, h, 4)
        lgrad(ctx, dx, 0, dx + dw, 0, STEEL)
        ctx.fill()
        ex = dx + (dw - 3 if side == 0 else 3)
        line(ctx, ex, y0, ex, y0 + h, 4, "#4b5563")


def lift_interior(ctx, t, heat=0.0, open_k=0.0, outside_fn=None, flick=1.0):
    """Кабина лифта изнутри, смотрим на двери: табло, кнопки, связь, поручень, наклейки."""
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#3f3f46"), (1, "#27272a")])
    rr(ctx, -300, 120, 1680, 1700, 0)
    lgrad(ctx, -300, 0, 1380, 0, STEEL)
    ctx.fill()
    for k in range(-2, 12):
        line(ctx, k * 140, 120, k * 140, 1820, 2, "#ffffff", 0.06)
    rr(ctx, 200, 420, 680, 1300, 6)
    fill(ctx, "#18181b")
    if open_k > 0 and outside_fn:
        ctx.save()
        rr(ctx, 200, 420, 680, 1300, 6)
        ctx.clip()
        outside_fn(ctx)
        ctx.restore()
    lift_doors(ctx, 200, 420, 680, 1300, open_k)
    led(ctx, 540, 280, 360, 150, floor_label(TL.floor_at(t)), t)
    rr(ctx, 950, 600, 200, 620, 16)
    lgrad(ctx, 950, 0, 1150, 0, [(0, "#9ca3af"), (0.5, "#e5e7eb"), (1, "#9ca3af")])
    ctx.fill()
    for k in range(9):
        bx, by = 1000 + (k % 2) * 100, 660 + (k // 2) * 90
        n = 9 - k
        ctx.arc(bx, by, 32, 0, TAU)
        fill(ctx, "#fbbf24" if n == 1 else "#d4d4d8")
        ctx.arc(bx, by, 32, 0, TAU)
        ctx.set_line_width(4)
        src(ctx, "#71717a")
        ctx.stroke()
        text(ctx, str(n), bx, by, 30, "#18181b")
    ctx.arc(1050, 1130, 34, 0, TAU)
    fill(ctx, "#facc15")
    ctx.move_to(1036, 1140)
    ctx.curve_to(1036, 1110, 1064, 1110, 1064, 1140)
    ctx.close_path()
    fill(ctx, "#18181b")
    for k in range(5):
        line(ctx, 990, 1180 + k * 8, 1110, 1180 + k * 8, 3, "#52525b")
    rr(ctx, -300, 1250, 480, 30, 15)
    fill(ctx, "#d4d4d8")
    rr(ctx, 30, 700, 140, 200, 6)
    fill(ctx, "#fef3c7")
    text(ctx, "400 кг", 100, 760, 30, "#78350f")
    text(ctx, "5 чел.", 100, 830, 30, "#78350f")
    rr(ctx, -200, 950, 300, 200, 6)
    fill(ctx, "#f472b6")
    text(ctx, "ПИЦЦА 24/7", -50, 1050, 30, "#ffffff")
    ctx.rectangle(-1200, 1720, 3600, 900)
    fill(ctx, "#3f3f46")
    for k in range(-10, 20):
        line(ctx, k * 90, 1720, k * 90 - 40, 2600, 2, "#27272a")
    rr(ctx, 240, 40, 600, 50, 20)
    fill(ctx, "#fefce8" if flick > 0.5 else "#52525b")
    if heat > 0:
        ctx.rectangle(-1200, -800, 3600, 3600)
        fill(ctx, "#dc2626", 0.25 * heat)
        for k in range(8):
            y = (k * 260 - t * 120) % 2200 - 200
            ctx.move_to(-300, y)
            for j in range(20):
                ctx.line_to(-300 + j * 90, y + math.sin(j + t * 3 + k) * 14)
            ctx.set_line_width(3)
            src(ctx, "#fde68a", 0.15 * heat)
            ctx.stroke()
    if flick < 1:
        ctx.rectangle(-1200, -800, 3600, 3600)
        fill(ctx, "#000", 0.55 * (1 - flick))


def flick_at(t):
    return 0.2 if (heat_at(t) > 0.3 and random.Random(int(t * 9)).random() < 0.12) else 1.0


def landing_bg(ctx, t, lamp=1.0):
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#d6cfc4"), (1, "#b9b0a2")])
    ctx.rectangle(-1200, 1150, 3600, 300)
    fill(ctx, "#4b6b5a")
    line(ctx, -1200, 1150, 2400, 1150, 8, "#3f594b")
    plant(ctx, -120, 1700, 1.2, t, "#7c2d12")
    plant(ctx, 1200, 1700, 1.0, t, "#1d4ed8")
    ctx.rectangle(-2000, 1700, 5200, 2400)
    fill(ctx, "#8b7d6b")
    for i in range(-16, 30):
        line(ctx, i * 120, 1700, i * 120 - 120, 4000, 3, "#7a6c5a")
    line(ctx, 540, -200, 540, 120, 4, "#111")
    ctx.arc(540, 140, 30, 0, TAU)
    fill(ctx, "#fef9c3" if lamp > 0.5 else "#6b7280")
    if lamp > 0.5:
        glow(ctx, 540, 260, 700, "#fde68a", 0.3)


def home_landing(ctx, t, red=0.0):
    landing_bg(ctx, t)
    apartment_door(ctx, 330, 1700, 420, 900, "47")
    rr(ctx, 360, 1700, 360, 40, 8)
    fill(ctx, "#7c2d12")
    text(ctx, "WELCOME", 540, 1720, 24, "#fcd34d")
    if red > 0:
        ctx.rectangle(-2000, -800, 5200, 4400)
        fill(ctx, "#7f1d1d", 0.35 * red)


def radio_amp(li, t):
    l = TL.lines[li]
    uu = t - l["start"]
    for w in l["words"]:
        if w["t"] <= uu <= w["t"] + w["d"]:
            return 0.6 + 0.4 * abs(math.sin(uu * 23))
    return 0.0


# ================================================================== СЦЕНЫ
def s0_enter(ctx, t, u, D):
    cl = EV["close"]
    pr = EV["press"]
    ctx.save()
    if t < pr - 0.2:
        cam(ctx, t, 540, 1200, lerp(0.8, 0.9, seg(u, 0, pr)), shake=0.3)
        landing_bg(ctx, t)
        rr(ctx, 230, 560, 620, 1150, 8)
        fill(ctx, "#52525b")
        rr(ctx, 260, 600, 560, 1100, 4)
        fill(ctx, "#fef3c7")
        led(ctx, 540, 470, 200, 90, "9", t, arrow=False)
        hero(ctx, lerp(200, 540, ease(seg(u, 0, pr - 0.3))), 1850, 1.0, emo("calm"), t, arms="relax", back=True,
             walk=t * 7, rim="#fde68a", rim_a=0.5)
    else:
        k = ease(seg(t, cl - 0.2, cl + 0.9))
        z = lerp(1.6, 0.85, ease(seg(t, pr + 0.4, cl)))
        cam(ctx, t, lerp(1000, 540, ease(seg(t, pr + 0.4, cl))), lerp(700, 1000, ease(seg(t, pr + 0.4, cl))), z,
            shake=0.3)
        lift_interior(ctx, t, open_k=1 - k, outside_fn=lambda c: landing_bg(c, t))
        hero(ctx, 540, 2250, 1.5, emo("calm"), t, arms="down", back=True, legs=False, rim="#fde68a", rim_a=0.4)
    ctx.restore()


def s1_count(ctx, t, u, D):
    m1 = TL.wt(1, "один", 1)
    ctx.save()
    if t < m1:
        cam(ctx, t, 540, 300, lerp(1.6, 1.9, seg(t, TL.shots[1][0], m1)), shake=0.25)
        lift_interior(ctx, t)
    else:
        sn = seg(t, m1, m1 + 0.15)
        cam(ctx, t, 540, 900, 0.9 + 0.2 * ease_out(sn), shake=0.4 + 0.6 * sn)
        lift_interior(ctx, t)
        hero(ctx, 540, 2150, 1.5, emo("shock"), t, arms="shock", legs=False, rim="#fde68a", rim_a=0.5,
             look=(0, -0.9), tremble=0.5)
    ctx.restore()


def shaft(ctx, t, cab_y):
    vgrad(ctx, -1200, -3000, 3600, 3000, [(0, "#0b1120"), (1, "#1e293b")])
    rr(ctx, 140, -2400, 800, 2400, 4)
    fill(ctx, "#334155")
    for row in range(10):
        for col in range(4):
            rr(ctx, 190 + col * 190, -2330 + row * 230, 120, 140, 4)
            fill(ctx, "#fde68a" if (row * 7 + col * 3) % 5 == 0 else "#0f172a")
    y = 0
    for col, hgt in (("#5b3a1e", 300), ("#4a2f17", 500), ("#3f3f46", 700), ("#292524", 900), ("#1c1917", 1500),
                     ("#450a0a", 2500), ("#7f1d1d", 4000)):
        ctx.rectangle(-1200, y, 3600, hgt)
        fill(ctx, col)
        y += hgt
    r = random.Random(3)
    for i in range(90):
        x, yy = r.uniform(-600, 1700), r.uniform(50, 10000)
        kind = r.random()
        if kind < 0.5:
            ell(ctx, x, yy, r.uniform(20, 70), r.uniform(14, 40))
            fill(ctx, "#57534e", 0.8)
        elif kind < 0.7 and yy < 1200:
            line(ctx, x, yy, x + r.uniform(-80, 80), yy + r.uniform(60, 200), 6, "#3f2a1d")
        elif kind < 0.85:
            rr(ctx, x - 150, yy, 300, 26, 13)
            fill(ctx, "#6b7280")
        else:
            line(ctx, x - 40, yy, x + 40, yy, 10, "#e7e5e4", 0.7)
            ctx.arc(x - 46, yy, 12, 0, TAU)
            fill(ctx, "#e7e5e4", 0.7)
            ctx.arc(x + 46, yy, 12, 0, TAU)
            fill(ctx, "#e7e5e4", 0.7)
    glow(ctx, 540, 9000, 3000, "#ef4444", 0.4)
    ctx.rectangle(440, -2400, 200, 14000)
    fill(ctx, "#0a0a0a")
    for k in range(-30, 140):
        line(ctx, 440, k * 100, 640, k * 100, 2, "#27272a")
    line(ctx, 540, -2400, 540, cab_y - 110, 3, "#71717a")
    rr(ctx, 455, cab_y - 110, 170, 220, 8)
    lgrad(ctx, 455, 0, 625, 0, STEEL)
    ctx.fill()
    glow(ctx, 540, cab_y, 160, "#fde68a", 0.5)
    hero_head(ctx, 540, cab_y - 10, 34, emo("shock"), t, rim_a=0.0)
    line(ctx, -1200, 0, 2400, 0, 8, "#365314")


def s2_shaft(ctx, t, u, D):
    cab = lerp(-300, 1400, ease_in(seg(u, 0, D), 1.3))
    ctx.save()
    cam(ctx, t, 540, cab - 100, lerp(0.75, 0.9, seg(u, 0, D)), shake=0.3)
    shaft(ctx, t, cab)
    ctx.restore()
    led(ctx, 540, 360, 280, 120, floor_label(TL.floor_at(t)), t)


def s3_hot(ctx, t, u, D):
    ns = EV["nosignal"] - TL.shots[3][0]
    ctx.save()
    if u < ns:
        cam(ctx, t, 540, 600, lerp(1.0, 1.1, seg(u, 0, ns)), shake=0.5)
        lift_interior(ctx, t, heat=heat_at(t), flick=flick_at(t))
        hero(ctx, 540, 2050, 1.5, emo("fear"), t, arms="down", legs=False, rim="#f97316", rim_a=0.6, tremble=0.5,
             look=(0, -0.9))
    else:
        def scr(c, x, y, w, h):
            vgrad(c, x, y, w, h, [(0, "#111827"), (1, "#020617")])
            text(c, "НЕТ СЕТИ", x + w / 2, y + 220, 70, "#ef4444")
            for k in range(4):
                rr(c, x + w / 2 - 90 + k * 50, y + 400 - k * 30, 34, 40 + k * 30, 6)
                fill(c, "#374151")
            line(c, x + w / 2 - 110, y + 300, x + w / 2 + 110, y + 460, 10, "#ef4444")
            text(c, "44°C", x + w / 2, y + 700, 90, "#f97316")
        cam(ctx, t, 540, 900, lerp(1.1, 1.2, seg(u, ns, D)), shake=0.6)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#450a0a"), (1, "#1c0505")])
        hands_phone(ctx, t, scr, tremble=1.0)
    ctx.restore()


def speaker_close(ctx, t, li, red=0.0):
    rr(ctx, 140, 380, 800, 900, 60)
    lgrad(ctx, 140, 0, 940, 0, STEEL)
    ctx.fill()
    for k in range(14):
        line(ctx, 220, 460 + k * 40, 860, 460 + k * 40, 14, "#3f3f46")
    amp = radio_amp(li, t) if li is not None else 0
    if amp > 0:
        glow(ctx, 540, 720, 420, "#f97316" if red < 0.5 else "#ef4444", 0.5 * amp)
    ctx.arc(540, 1120, 90, 0, TAU)
    fill(ctx, "#facc15")
    ctx.move_to(500, 1150)
    ctx.curve_to(500, 1070, 580, 1070, 580, 1150)
    ctx.close_path()
    fill(ctx, "#18181b")


def s4_call(ctx, t, u, D):
    cl = EV["call"] - TL.shots[4][0]
    k = ease(seg(u, 0, cl + 0.3))
    ctx.save()
    cam(ctx, t, lerp(700, 1050, k), lerp(900, 1130, k), lerp(1.0, 2.4, k), shake=0.4)
    lift_interior(ctx, t, heat=heat_at(t), flick=flick_at(t))
    px = lerp(1250, 1062, ease(seg(u, cl - 0.3, cl)))
    line(ctx, px + 20, 1170, px + 300, 1500, 70, HOOD)
    ctx.arc(px, 1150, 46, 0, TAU)
    fill(ctx, HEAD)
    ctx.restore()


def s5_voice(ctx, t, u, D, li=5, red=0.0):
    ctx.save()
    cam(ctx, t, 540, 820, lerp(1.0, 1.1, seg(u, 0, D)), shake=0.3)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#27272a"), (1, "#09090b")])
    speaker_close(ctx, t, li, red)
    ctx.restore()
    text(ctx, "ДИСПЕТЧЕР", 540, 1420, 70, "#f97316" if red < 0.5 else "#ef4444", "#000", 10)
    if heat_at(t) > 0:
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#dc2626", 0.18 * heat_at(t))


def s6_shout(ctx, t, u, D):
    sh = EV["shout"] - TL.shots[6][0]
    ctx.save()
    cam(ctx, t, 540, 950, lerp(1.0, 1.2, ease(seg(u, sh, D))), shake=0.4 + (1.0 if sh < u < sh + 0.6 else 0))
    lift_interior(ctx, t, heat=heat_at(t), flick=flick_at(t))
    hero(ctx, 540, 2000, 1.7, emo("shock") if u > sh else emo("fear"), t, arms="fwd" if u > sh else "down",
         legs=False, rim="#f97316", rim_a=0.6, look=(0.8, 0.3), tremble=0.6)
    ctx.restore()
    if sh < u < sh + 1.2:
        text(ctx, "ПЕРВЫЙ!", 540, 600, 160, "#ffffff", "#b91c1c", 18, alpha=1 - seg(u, sh + 0.9, sh + 1.2))


def s7_voice2(ctx, t, u, D):
    s5_voice(ctx, t, u, D, li=7, red=1.0)
    if (t * 2) % 1 < 0.5:
        led(ctx, 540, 330, 360, 150, "ВНИЗ", t, arrow=True)


def s8_open(ctx, t, u, D):
    st = EV["stop"]
    op = ease(seg(t, EV["open"], EV["open"] + 1.6))
    jolt = 1 - seg(t, st, st + 0.5) if t > st else 0
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(0.85, 0.95, seg(u, 0, D)), shake=0.3 + 2.5 * jolt)
    lift_interior(ctx, t, heat=heat_at(t), open_k=op, outside_fn=lambda c: home_landing(c, t, 1.0))
    hero(ctx, 540, 2250, 1.5, emo("fear"), t, arms="down", back=True, legs=False, rim="#ef4444", rim_a=0.5)
    ctx.restore()


def s9_same(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, lerp(1300, 1250, seg(u, 0, D)), lerp(0.7, 0.85, ease(seg(u, 0, D))), shake=0.25)
    home_landing(ctx, t, 0.8)
    ctx.restore()
    for k, (txt, y) in enumerate((("ТОТ ЖЕ КОВРИК", 1250), ("ТОТ ЖЕ ЦВЕТОК", 1360))):
        tw = TL.wt(9, ["коврик", "цветок"][k]) - TL.shots[9][0]
        if u > tw:
            text(ctx, txt, 540, y, 64, "#ffffff", "#000", 10, alpha=seg(u, tw, tw + 0.2))


CROWD7 = None


def crowd7():
    global CROWD7
    if CROWD7 is None:
        r = random.Random(12)
        CROWD7 = []
        for x, y, sc in ((60, 1820, 1.2), (330, 1780, 1.1), (620, 1800, 1.15), (900, 1790, 1.2), (180, 1950, 1.35),
                         (760, 1960, 1.4), (480, 2000, 1.5)):
            p = Npc(r, x, y, sc, 1)
            p.item = "none"
            CROWD7.append(p)
        lady = CROWD7[6]
        lady.shirt, lady.style, lady.hair, lady.glasses, lady.female = "#f9a8d4", "bun", "#9a9a9a", True, True
    return CROWD7


def s10_backs(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1350, lerp(0.75, 0.9, ease(seg(u, 0, D))), shake=0.2)
    home_landing(ctx, t, 1.0)
    for p in sorted(crowd7(), key=lambda q: q.y):
        npc(ctx, p, t, walking=False, back=True)
    ctx.restore()


def s11_turn(ctx, t, u, D):
    tu = EV["turn"]
    sm = EV["smile"]
    ec = EV["end_card"] - TL.shots[11][0]
    ctx.save()
    if u < ec:
        k = ease(seg(t, tu, tu + 1.2))
        cam(ctx, t, 480, lerp(1350, 1300, k), lerp(0.9, 1.9, ease(seg(t, tu, sm + 0.5))), shake=0.25)
        home_landing(ctx, t, 1.0)
        lady = crowd7()[6]
        for p in sorted(crowd7(), key=lambda q: q.y):
            if p is lady:
                if k < 0.6:
                    npc(ctx, p, t, walking=False, back=True, alpha=1 - seg(k, 0.3, 0.6))
                if k > 0.3:
                    npc(ctx, p, t, walking=False, grin=1.2 if t > sm else 0.0, stare=1.0, alpha=seg(k, 0.3, 0.6))
            else:
                npc(ctx, p, t, walking=False, back=True)
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
        text(ctx, "Кто живёт на минус сотом?", 0, 180, 58, "#f97316")
    ctx.restore()


SCENES = [s0_enter, s1_count, s2_shaft, s3_hot, s4_call, s5_voice, s6_shout, s7_voice2, s8_open, s9_same,
          s10_backs, s11_turn]
LABELS = {}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("минус", "один"), "-1"), (("минус", "два"), "-2"), (("минус", "двадцать"), "-20"),
         (("минус", "пятьдесят"), "-50"), (("минус", "сто"), "-100"), (("три",), "3"), (("два",), "2"),
         (("один",), "1"), (("ноль",), "0")]


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
        if i in LABELS:
            a = seg(t, TL.shots[i][0], TL.shots[i][0] + 0.3)
            text(ctx, LABELS[i], W - 60, 125, 46, "#ffffff", "#000", 10, align="right", alpha=a)
    hook_end = EV["close"] + 0.4
    if t < hook_end:  # заголовок-хук
        k1 = back_out(seg(t, 0.0, 0.3))
        out = 1 - seg(t, hook_end - 0.3, hook_end)
        ctx.save()
        ctx.translate(540, 360)
        ctx.scale(k1, k1)
        ctx.push_group()
        text(ctx, "ЧТО, ЕСЛИ ЛИФТ", 0, -110, 88, "#ffffff", "#000", 16, shadow=True)
        text(ctx, "ЕДЕТ ВНИЗ", 0, 10, 116, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -330, 90, 660, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "БЕЗ КОНЦА?", 0, 155, 96, "#ffffff")
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
