"""Серия 4 «Два голоса»: python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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
from aviation import airliner, tower_ext  # noqa: E402

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



# ================================================================== АВИА-РЕКВИЗИТ
def clouds(ctx, t, seed, y0, y1, speed, col, a, n=10, scale=1.0):
    r = random.Random(seed)
    for i in range(n):
        x0 = r.uniform(-600, 1800)
        y = r.uniform(y0, y1)
        w = r.uniform(260, 620) * scale
        x = (x0 - t * speed * r.uniform(0.8, 1.2)) % 2600 - 700
        for k in range(5):
            ell(ctx, x + k * w / 5, y + math.sin(k * 1.7 + i) * 20, w / 3.2, w / 6.5)
            fill(ctx, col, a)


def bolt(ctx, x, y, h, seed, a=1.0):
    r = random.Random(seed)
    ctx.move_to(x, y)
    xx, yy = x, y
    while yy < y + h:
        xx += r.uniform(-60, 60)
        yy += r.uniform(40, 90)
        ctx.line_to(xx, yy)
    ctx.set_line_width(10)
    src(ctx, "#e0e7ff", a)
    ctx.stroke_preserve()
    ctx.set_line_width(26)
    src(ctx, "#a5b4fc", 0.35 * a)
    ctx.stroke()


def night_sky(ctx, t, flash=0.0):
    vgrad(ctx, -1200, -1200, 3500, 4400, [(0, "#020617"), (0.6, "#0f1b3d"), (1, "#1e2b52")])
    stars(ctx, 3, 1080, 1200, t, 70)
    if flash > 0:
        ctx.rectangle(-1200, -1200, 3500, 4400)
        fill(ctx, "#c7d2fe", 0.45 * flash)


def pilot_back(ctx, x, y, s, slump=0.3, wake=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rr(ctx, -170, -330, 340, 420, 60)  # спинка кресла
    lgrad(ctx, -170, 0, 170, 0, [(0, "#1f2937"), (0.5, "#374151"), (1, "#1f2937")])
    ctx.fill()
    ctx.rotate(lerp(slump, 0, wake))
    rr(ctx, -130, -250, 260, 220, 70)
    fill(ctx, "#1e293b")
    for side in (-1, 1):
        rr(ctx, side * 95 - 30, -250, 60, 22, 6)
        fill(ctx, "#1e293b")
        for k in range(3):
            line(ctx, side * 95 - 24, -244 + k * 6, side * 95 + 24, -244 + k * 6, 3, "#facc15")
    ctx.translate(0, lerp(40, 0, wake))
    ctx.move_to(-40, -250)
    ctx.line_to(0, -210)
    ctx.line_to(40, -250)
    fill(ctx, "#f8fafc")
    ctx.arc(0, -320, 70, 0, TAU)
    fill(ctx, "#3b2a1d")
    ctx.arc(0, -330, 76, math.pi * 1.05, math.pi * 1.95)
    ctx.set_line_width(10)
    src(ctx, "#111827")
    ctx.stroke()
    for side in (-1, 1):
        rr(ctx, side * 78 - 16, -340, 32, 46, 10)
        fill(ctx, "#111827")
    line(ctx, -78, -300, -40, -280, 4, "#111827")
    rr(ctx, -78, -400, 156, 50, 14)
    fill(ctx, "#111827")
    rr(ctx, -84, -362, 168, 14, 6)
    fill(ctx, "#facc15")
    ctx.restore()


def cockpit(ctx, t, warn=0.0, fuel_txt="18 МИН", horizon=0.0, speed=180, slump=1.0, wake=0.0, flash=0.0):
    # лобовое стекло
    night_sky(ctx, t, flash)
    clouds(ctx, t, 4, 200, 900, 900, "#cbd5e1", 0.18, 8, 1.4)
    # рама кабины
    ctx.rectangle(-1200, 980, 3500, 3000)
    lgrad(ctx, 0, 980, 0, 2200, [(0, "#1f2937"), (1, "#0b0f16")])
    ctx.fill()
    for xx, sl in ((-400, 0.25), (300, 0.05), (780, -0.05), (1480, -0.25)):
        ctx.save()
        ctx.translate(xx, 0)
        ctx.rotate(sl)
        rr(ctx, -40, -300, 80, 1400, 20)
        fill(ctx, "#111827")
        ctx.restore()
    rr(ctx, -1200, -360, 3500, 140, 0)
    fill(ctx, "#111827")
    # приборная панель
    rr(ctx, -300, 1000, 1680, 360, 30)
    fill(ctx, "#0f172a")
    for k, px in enumerate((40, 330, 620, 910)):
        rr(ctx, px - 120, 1040, 240, 200, 14)
        fill(ctx, "#020617")
        ctx.save()
        rr(ctx, px - 112, 1048, 224, 184, 10)
        ctx.clip()
        if k == 0:  # авиагоризонт
            ctx.save()
            ctx.translate(px, 1140)
            ctx.rotate(horizon * 0.3)
            ctx.rectangle(-300, -300 + horizon * 60, 600, 300)
            fill(ctx, "#3b82f6")
            ctx.rectangle(-300, horizon * 60, 600, 300)
            fill(ctx, "#a16207")
            line(ctx, -300, horizon * 60, 300, horizon * 60, 3, "#ffffff")
            ctx.restore()
            line(ctx, px - 50, 1140, px + 50, 1140, 6, "#facc15")
        elif k == 1:  # скорость
            text(ctx, f"{int(speed)}", px, 1130, 70, "#22c55e")
            text(ctx, "УЗЛ", px, 1195, 26, "#64748b")
        elif k == 2:  # навигация
            for rr_ in (40, 70, 95):
                ctx.arc(px, 1200, rr_, TAU / 2, TAU)
                ctx.set_line_width(2)
                src(ctx, "#22d3ee", 0.6)
                ctx.stroke()
            ctx.move_to(px, 1180)
            ctx.line_to(px - 12, 1205)
            ctx.line_to(px + 12, 1205)
            fill(ctx, "#ffffff")
        else:  # топливо
            on = warn > 0 and (t * 3) % 1 < 0.6
            ctx.rectangle(px - 112, 1048, 224, 184)
            fill(ctx, "#7f1d1d" if on else "#111827")
            text(ctx, "ТОПЛИВО", px, 1095, 30, "#fecaca" if on else "#64748b")
            text(ctx, fuel_txt, px, 1165, 50, "#ffffff" if on else "#ef4444")
        ctx.restore()
    for k in range(18):  # кнопки
        on = (k * 7 + int(t * 2)) % 5 == 0
        rr(ctx, -200 + k * 80, 1280, 50, 30, 6)
        fill(ctx, "#22c55e" if on else "#334155")
    if warn > 0:
        on = (t * 3) % 1 < 0.6
        rr(ctx, 440, 960, 200, 60, 12)
        fill(ctx, "#ef4444" if on else "#450a0a")
        text(ctx, "MASTER WARN", 540, 990, 24, "#fff")
        if on:
            glow(ctx, 540, 990, 500, "#ef4444", 0.35 * warn)
    # верхняя панель с тумблерами
    rr(ctx, -200, -330, 1480, 110, 10)
    fill(ctx, "#1f2937")
    for k in range(28):
        ctx.arc(-160 + k * 52, -275, 9, 0, TAU)
        fill(ctx, "#22c55e" if (k * 5 + int(t)) % 7 == 0 else "#64748b")
    # центральный пульт: РУДы
    rr(ctx, 400, 1360, 280, 500, 20)
    fill(ctx, "#111827")
    for k in range(2):
        line(ctx, 470 + k * 140, 1600, 470 + k * 140, 1440, 20, "#475569")
        rr(ctx, 430 + k * 140, 1410, 80, 44, 14)
        fill(ctx, "#e5e7eb")
    rr(ctx, 600, 1700, 60, 120, 8)
    fill(ctx, "#f8fafc")
    text(ctx, "ЧЕК-ЛИСТ", 630, 1690, 18, "#94a3b8")
    pilot_back(ctx, 120, 1700, 1.15, slump * 0.35, wake)
    pilot_back(ctx, 960, 1700, 1.15, -slump * 0.3, wake)



COL_A = "#38bdf8"   # диспетчер-женщина
COL_B = "#fb923c"   # второй голос


def passenger_state(k, t):
    """Сон пассажира ряда k: 0 — бодрствует, 1 — спит (волна по салону)."""
    d = EV["sleep"] + 0.06 * ((k * 7) % 11)
    return ease(seg(t, d, d + 0.5))


def cabin2(ctx, t, x0, x1, sleep_fn, clap=False, hero_x=None, hero_e=None, hero_walk=None, stew_fall=0.0,
           lights=1.0, bank=0.0, no_tablet=False):
    """Салон в разрезе с массовкой: каждый пассажир чем-то занят, потом засыпает."""
    vgrad(ctx, -2000, -800, 6000, 3600, [(0, "#cbd5e1"), (1, "#94a3b8")])
    rr(ctx, -2000, 330, 6000, 220, 30)
    lgrad(ctx, 0, 330, 0, 550, [(0, "#f1f5f9"), (1, "#cbd5e1")])
    ctx.fill()
    for k in range(-8, 16):
        line(ctx, k * 300, 340, k * 300, 540, 4, "#94a3b8")
        rr(ctx, k * 300 + 110, 440, 80, 14, 6)
        fill(ctx, "#94a3b8")
        ell(ctx, k * 300 + 150, 560, 30, 10)
        fill(ctx, "#fde68a", lights)
        if k % 3 == 0:
            rr(ctx, k * 300 + 40, 585, 90, 34, 8)
            fill(ctx, "#111827")
            on_ = (t * 1.5) % 1 < 0.7
            for j, xx in enumerate((66, 104)):
                ctx.arc(k * 300 + xx, 602, 9, 0, TAU)
                fill(ctx, "#fbbf24" if on_ else "#3f3f46")
        if k % 4 == 1 and lights > 0.5:
            ctx.move_to(k * 300 + 135, 570)
            ctx.line_to(k * 300 + 165, 570)
            ctx.line_to(k * 300 + 260, 1400)
            ctx.line_to(k * 300 + 40, 1400)
            ctx.close_path()
            fill(ctx, "#fef3c7", 0.12 * lights)
    for k in range(-8, 16):
        cx = k * 300 + 150
        rr(ctx, cx - 50, 640, 100, 150, 46)
        fill(ctx, "#0f1b3d")
        ctx.save()
        rr(ctx, cx - 50, 640, 100, 150, 46)
        ctx.clip()
        ctx.translate(cx, 715)
        ctx.rotate(-bank * 1.5)
        ctx.rectangle(-200, 20, 400, 300)  # горизонт за окном
        fill(ctx, "#1e2b52")
        ctx.restore()
        sh = (k * 37 % 5) / 5
        if sh > 0.3:
            ctx.save()
            rr(ctx, cx - 50, 640, 100, 150, 46)
            ctx.clip()
            ctx.rectangle(cx - 50, 640, 100, 150 * sh)
            fill(ctx, "#e5e7eb")
            ctx.restore()
        rr(ctx, cx - 50, 640, 100, 150, 46)
        ctx.set_line_width(10)
        src(ctx, "#e2e8f0")
        ctx.stroke()
    ctx.rectangle(-2000, 1700, 6000, 800)
    fill(ctx, "#334155")
    for k in range(-20, 40):
        line(ctx, k * 120, 1710, k * 120 + 60, 1900, 4, "#3f4b5f")
        ctx.arc(k * 120 + 40, 1780, 6, 0, TAU)
        fill(ctx, "#475569")
    for k in range(-6, 14):
        sx = k * 300
        if sx < x0 - 400 or sx > x1 + 400:
            continue
        rk = random.Random(k * 11 + 5)
        kid = k == 3
        p = Npc(random.Random(k * 31 + 7), sx + 120, 1640, 0.7 if kid else 0.95, 1)
        act = "tablet" if kid else rk.choice(["phone", "book", "laptop", "food", "music", "talk"])
        p.item = "phone" if act == "phone" else "none"
        p.neck_pillow = (not kid) and rk.random() < 0.3
        p.headphones = p.headphones or act == "music"
        sl = sleep_fn(k, t)
        p.mask = False
        rr(ctx, sx + 20, 1060, 120, 520, 40)
        lgrad(ctx, sx + 20, 0, sx + 140, 0, [(0, "#1e3a8a"), (1, "#2563eb")])
        ctx.fill()
        rr(ctx, sx + 30, 1040, 100, 70, 20)
        fill(ctx, "#e2e8f0")
        ctx.save()
        tilt_ = (0.14 if k % 2 else -0.08) * sl
        ctx.translate(sx + 120, 1640)
        ctx.rotate(tilt_)
        ctx.translate(-(sx + 120), -1640)
        npc(ctx, p, t, walking=False, sleep=sl > 0.5, clap=clap, grin=0.2 if clap else 0.0)
        ctx.restore()
        rr(ctx, sx + 60, 1470, 220, 90, 30)
        fill(ctx, "#1d4ed8")
        if rk.random() < 0.45:
            rr(ctx, sx + 70, 1420, 200, 110, 30)
            fill(ctx, rk.choice(["#b91c1c", "#0f766e", "#a16207", "#6d28d9"]))
        rr(ctx, sx + 250, 1400, 90, 14, 4)
        fill(ctx, "#cbd5e1")
        # занятие пассажира
        if act == "laptop":
            rr(ctx, sx + 240, 1380, 100, 20, 3)
            fill(ctx, "#9ca3af")
            ctx.move_to(sx + 300, 1380)
            ctx.line_to(sx + 330 - 60 * sl, 1300 + 70 * sl)
            ctx.line_to(sx + 340 - 60 * sl, 1300 + 70 * sl)
            ctx.line_to(sx + 312, 1380)
            fill(ctx, "#1f2937")
            if sl < 0.5:
                glow(ctx, sx + 325, 1330, 70, "#60a5fa", 0.5)
        elif act == "food":
            rr(ctx, sx + 250, 1384, 80, 16, 4)
            fill(ctx, "#f8fafc")
            ell(ctx, sx + 290, 1382, 26, 8)
            fill(ctx, "#f59e0b")
            rr(ctx, sx + 320, 1356, 16, 30, 3)
            fill(ctx, "#ef4444")
        elif act == "book":
            ctx.save()
            ctx.translate(sx + 190, 1430 - 120 * (1 - sl))
            ctx.rotate(-0.3 + 1.6 * sl)
            rr(ctx, -40, -30, 80, 60, 4)
            fill(ctx, rk.choice(["#7c2d12", "#1e40af", "#166534"]))
            rr(ctx, -36, -26, 72, 52, 3)
            fill(ctx, "#f5f5f4", 0.9)
            line(ctx, 0, -26, 0, 26, 3, "#a8a29e")
            ctx.restore()
        elif act == "talk" and sl < 0.5:
            rr(ctx, sx + 150, 1150, 70, 40, 16)
            fill(ctx, "#ffffff")
            for j in range(3):
                ctx.arc(sx + 168 + j * 17, 1170, 4, 0, TAU)
                fill(ctx, "#111")
        elif act == "tablet" and not no_tablet:
            ctx.save()
            ctx.translate(sx + 190, 1420 + 260 * ease_in(sl, 2))
            ctx.rotate(sl * 1.4)
            rr(ctx, -45, -32, 90, 64, 8)
            fill(ctx, "#111827")
            rr(ctx, -38, -26, 76, 52, 5)
            fill(ctx, "#22d3ee")
            ctx.arc(-10, -6, 9, 0, TAU)
            fill(ctx, "#facc15")
            ctx.restore()
        line(ctx, sx + 120, 1560, sx + 120, 1700, 14, "#1f2937")
        line(ctx, sx + 250, 1560, sx + 250, 1700, 14, "#1f2937")
    # стюардесса падает с подносом
    stew_x = 1650
    if x0 - 400 < stew_x < x1 + 400:
        st = Npc(random.Random(5), stew_x, 1700, 0.95, 1)
        st.style, st.shirt, st.pants, st.item = "bun", "#1e3a8a", "#1e3a8a", "none"
        st.uniform, st.glasses, st.headphones, st.earrings = "stew", False, False, True
        cx = stew_x + 250
        rr(ctx, cx - 100, 1380, 200, 300, 10)
        lgrad(ctx, cx - 100, 0, cx + 100, 0, [(0, "#94a3b8"), (0.5, "#e2e8f0"), (1, "#94a3b8")])
        ctx.fill()
        for j in range(3):
            line(ctx, cx - 90, 1440 + j * 70, cx + 90, 1440 + j * 70, 4, "#64748b")
            rr(ctx, cx - 20, 1462 + j * 70, 40, 10, 4)
            fill(ctx, "#475569")
        rr(ctx, cx - 70, 1600, 140, 36, 6)
        fill(ctx, "#d8332a")
        text(ctx, "БОРТ 307", cx, 1618, 22, "#ffffff")
        for j in range(4):
            rr(ctx, cx - 90 + j * 22, 1340, 18, 40, 3)
            fill(ctx, "#f8fafc")
        ctx.arc(cx - 70, 1690, 16, 0, TAU)
        fill(ctx, "#111")
        ctx.arc(cx + 70, 1690, 16, 0, TAU)
        fill(ctx, "#111")
        f = ease_in(stew_fall, 1.6)
        ctx.save()
        ctx.translate(stew_x, 1700)
        ctx.rotate(-1.35 * f)
        ctx.translate(-stew_x, -1700)
        npc(ctx, st, t, walking=False, sleep=stew_fall > 0.05)
        ctx.restore()
        # поднос и чашки летят
        tx = lerp(stew_x + 70, stew_x - 320, f)
        ty = lerp(1360, 1690, f) - math.sin(f * math.pi) * 120
        ctx.save()
        ctx.translate(tx, ty)
        ctx.rotate(-f * 2.4)
        rr(ctx, -70, -6, 140, 12, 4)
        fill(ctx, "#cbd5e1")
        ctx.restore()
        for j in range(3):
            jx = tx + (j - 1) * 50 * (1 + f) - f * 60 * j
            jy = ty - 30 - math.sin(f * math.pi) * (60 + j * 40) + f * 20
            ctx.save()
            ctx.translate(jx, jy)
            ctx.rotate(f * (3 + j))
            rr(ctx, -14, -18, 28, 36, 4)
            fill(ctx, "#f8fafc")
            ctx.restore()
            if f > 0.3:
                ell(ctx, jx + 10, jy + 26, 8, 4)
                fill(ctx, "#5a3420", 0.8)
        if stew_fall >= 1:
            ell(ctx, stew_x - 260, 1705, 120, 14)
            fill(ctx, "#5a3420", 0.8)
    if hero_x is not None:
        hero(ctx, hero_x, 1880, 1.0, hero_e, t, arms="relax", walk=hero_walk, rim="#93c5fd", rim_a=0.6,
             look=(0.6, 0))
    if lights < 1:
        ctx.rectangle(-2000, -1200, 6000, 4400)
        fill(ctx, "#020617", 0.6 * (1 - lights))


def flicker_at(t, t0):
    """Мерцание света 0..1 после t0."""
    if t < t0:
        return 1.0
    u = t - t0
    if u > 1.2:
        return 0.55
    return 0.15 if int(u * 14) % 3 == 0 else (0.9 if u < 0.6 else 0.55)


def radio_amp(li, t):
    l = TL.lines[li]
    uu = t - l["start"]
    for w in l["words"]:
        if w["t"] <= uu <= w["t"] + w["d"]:
            return 0.6 + 0.4 * abs(math.sin(uu * 23))
    return 0.0


def radio2(ctx, x, y, s, t, col, label, li=None, glitch=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 330, 520, 60, 0.5)
    rr(ctx, -460, -300, 920, 600, 40)
    lgrad(ctx, 0, -300, 0, 300, [(0, "#374151"), (1, "#111827")])
    ctx.fill()
    for k in range(6):  # винты
        ctx.arc(-430 + (k % 2) * 860, -270 + (k // 2) * 270, 9, 0, TAU)
        fill(ctx, "#6b7280")
    rr(ctx, -400, -250, 560, 160, 16)
    fill(ctx, "#020617")
    text(ctx, "118.307", -120, -190, 80, col)
    text(ctx, label, -120, -125, 30, col, alpha=0.8)
    ctx.arc(330, -170, 36, 0, TAU)
    fill(ctx, col)
    glow(ctx, 330, -170, 160, col, 0.6)
    for k in range(9):
        line(ctx, -400, -40 + k * 30, 100, -40 + k * 30, 10, "#0b0f16")
    rr(ctx, 150, -40, 270, 280, 16)
    fill(ctx, "#020617")
    for k in range(5):
        line(ctx, 160, -20 + k * 60, 410, -20 + k * 60, 1, col, 0.25)
    amp = radio_amp(li, t) if li is not None else 0.0
    ctx.move_to(165, 100)
    for k in range(60):
        xx = 165 + k * 4.2
        yy = 100 + math.sin(k * 0.9 + t * 40) * 90 * amp * math.sin(k / 60 * math.pi) * (
            0.6 + 0.4 * math.sin(k * 3.1 + t * 17))
        ctx.line_to(xx, yy)
    ctx.set_line_width(5)
    src(ctx, col)
    ctx.stroke()
    if glitch > 0:
        r = random.Random(int(t * 30))
        for i in range(10):
            ctx.rectangle(-460, -300 + r.random() * 600, 920, r.uniform(4, 26))
            fill(ctx, r.choice([COL_B, "#ffffff", "#ef4444"]), 0.4 * glitch)
    ctx.restore()


def mic_item(c, x, y):
    rr(c, x - 30, y - 110, 60, 110, 20)
    fill(c, "#111")
    for k in range(4):
        line(c, x - 18, y - 92 + k * 18, x + 18, y - 92 + k * 18, 3, "#4b5563")
    c.move_to(x, y)
    for k in range(8):
        c.line_to(x + 30 + math.sin(k * 1.4) * 20, y + 30 + k * 40)
    c.set_line_width(6)
    src(c, "#111")
    c.stroke()


# ================================================================== СЦЕНЫ
def s0_midnight(ctx, t, u, D):
    camx = lerp(500, 1100, ease(seg(u, 0, D)))
    lt = flicker_at(t, EV["flicker"])
    ctx.save()
    cam(ctx, t, camx, 1300, 1.05, shake=0.3)
    cabin2(ctx, t, camx - 700, camx + 700, passenger_state, lights=lt)
    ctx.restore()


def s1_falling(ctx, t, u, D):
    a, b, c = EV["sub1"]
    ctx.save()
    if t < a:  # все, кроме тебя: герой в кресле, соседи спят
        k = seg(t, TL.shots[1][0], a)
        cam(ctx, t, 540, 1080, lerp(1.2, 1.32, k), shake=0.5)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1e293b"), (1, "#0f172a")])
        rr(ctx, 60, 520, 300, 440, 140)
        fill(ctx, "#0f1b3d")
        rr(ctx, 60, 520, 300, 440, 140)
        ctx.set_line_width(26)
        src(ctx, "#cbd5e1")
        ctx.stroke()
        rr(ctx, 380, 760, 420, 900, 100)
        fill(ctx, "#1e3a8a")
        for px, sc_, d_ in ((900, 1.2, -1), (180, 1.0, 1)):
            p = Npc(random.Random(int(px)), px, 1700, sc_, d_)
            p.neck_pillow = True
            ctx.save()
            ctx.translate(px, 1700)
            ctx.rotate(-0.2 * d_)
            ctx.translate(-px, -1700)
            ctx.rectangle(-500, 0, 2500, 1430)
            ctx.clip()
            npc(ctx, p, t, walking=False, sleep=True)
            ctx.restore()
        rr(ctx, -100, 1380, 1400, 600, 60)
        fill(ctx, "#1d4ed8")
        hero(ctx, 560, 1640, 1.05, emo("shock"), t, arms="shock", legs=False, look=(math.sin(t * 3), 0),
             rim="#93c5fd", tremble=0.6)
    elif t < b:  # стюардесса падает
        camx = 1750
        cam(ctx, t, camx, 1350, 1.15, shake=0.5)
        cabin2(ctx, t, camx - 700, camx + 700, lambda k, tt: 1.0, lights=0.55,
               stew_fall=seg(t, EV["fall"] - 0.1, EV["fall"] + 0.7))
    elif t < c:  # планшет выскальзывает у мальчика
        k = seg(t, b, c)
        cam(ctx, t, 1020, 1380, lerp(1.9, 2.1, k), shake=0.3)
        cabin2(ctx, t, 300, 1700, lambda kk, tt: 1.0, lights=0.55, no_tablet=True)
        # перекрываем планшет мальчика анимированным
        tb = EV["tablet"]
        f = ease_in(seg(t, tb - 0.1, tb + 0.8), 2)
        ctx.save()
        ctx.translate(1090 + 60 * f, 1420 + 300 * f)
        ctx.rotate(f * 2.2)
        rr(ctx, -45, -32, 90, 64, 8)
        fill(ctx, "#111827")
        rr(ctx, -38, -26, 76, 52, 5)
        fill(ctx, "#22d3ee")
        ctx.arc(-10, -6, 9, 0, TAU)
        fill(ctx, "#facc15")
        ctx.restore()
        glow(ctx, 1090 + 60 * f, 1420 + 300 * f, 140, "#22d3ee", 0.4)
    else:  # самолёт ложится на крыло
        k = seg(t, c, TL.shots[2][0])
        cam(ctx, t, 540, 960, lerp(0.85, 0.95, k), rot=-0.25 * ease(k), shake=0.6)
        night_sky(ctx, t)
        ctx.arc(860, 300, 80, 0, TAU)
        fill(ctx, "#f1f5f9")
        glow(ctx, 860, 300, 300, "#cbd5e1", 0.3)
        clouds(ctx, t, 1, 300, 1700, 500, "#334155", 0.6, 12, 1.3)
        airliner(ctx, 540, 960, 0.62, t, tilt=0.35 * ease(k), contrail=True)
        clouds(ctx, t, 2, 1400, 2300, 1100, "#475569", 0.8, 10, 1.6)
    ctx.restore()


def s2_pilots(ctx, t, u, D):
    tf = EV["fuel"] - TL.shots[2][0]
    k = ease(seg(u, tf - 0.2, tf + 0.5))
    ctx.save()
    cam(ctx, t, lerp(540, 910, k), lerp(1150, 1140, k), lerp(0.75, 1.35, k), rot=0.06, shake=0.5 + 0.5 * k)
    cockpit(ctx, t, warn=1.0 if u > tf else 0.0, fuel_txt="19 МИН", horizon=0.8)
    ctx.restore()


def s3_grab(ctx, t, u, D):
    on = seg(t, EV["radio_on"], EV["radio_on"] + 0.2)
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(1.0, 1.15, ease(seg(u, 0, D))), shake=0.8)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1f0a0a"), (1, "#0b0f16")])
    blink_ = (t * 3) % 1 < 0.6
    for k in range(10):
        rr(ctx, -200 + k * 160, 300, 100, 60, 10)
        fill(ctx, "#ef4444" if (blink_ and k % 3 == 0) else "#334155")
    glow(ctx, 540, 600, 1200, "#ef4444" if on < 0.5 else COL_A, 0.35)
    hero(ctx, 540, 1750, 1.6, emo("fear", "worry", on), t, arms="phone", legs=False,
         rim="#ef4444" if on < 0.5 else COL_A, tremble=0.8, hand_item=mic_item)
    ctx.restore()


def radio_scene(ctx, t, u, D, li, col, label, emo_from, emo_to, glitch=0.0, look=(0, -0.7)):
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(1.0, 1.08, ease(seg(u, 0, D))), shake=0.4 + glitch * 0.6)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#020617"), (1, "#0b1120")])
    glow(ctx, 540, 600, 900, col, 0.25)
    radio2(ctx, 540, 560, 0.85, t, col, label, li, glitch)
    hero(ctx, 540, 1700, 1.25, emo(emo_from, emo_to, seg(u, 0.6, 1.6)), t, arms="phone", legs=False, rim=col,
         look=look, hand_item=mic_item, tremble=glitch)
    ctx.restore()


def s4_voiceA(ctx, t, u, D):
    radio_scene(ctx, t, u, D, 4, COL_A, "ДИСПЕТЧЕР", "worry", "calm")


def s5_push(ctx, t, u, D):
    tb = EV["burst"] - TL.shots[5][0]
    tp = EV["push"] - TL.shots[5][0]
    k = ease(seg(u, tp, tp + 0.8))
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(1.0, 1.08, k), shake=0.5 + 1.2 * seg(u, tb, tb + 0.2))
    cockpit(ctx, t, warn=1.0, fuel_txt="18 МИН", horizon=lerp(0.3, 0.9, k), speed=lerp(250, 280, k))
    ctx.save()
    ctx.translate(540, 1700)
    sc = lerp(1.25, 0.95, k)
    ctx.scale(sc, sc)
    line(ctx, 0, 300, 0, 0, 60, "#1f2937")
    rr(ctx, -260, -60, 520, 90, 40)
    fill(ctx, "#111827")
    for side in (-1, 1):
        rr(ctx, side * 260 - 50, -200, 100, 260, 40)
        fill(ctx, "#111827")
        ctx.arc(side * 260, -80, 60, 0, TAU)
        fill(ctx, HEAD)
    ctx.restore()
    ctx.restore()
    if u > tb:
        g = seg(u, tb, tb + 0.15) * (0.6 + 0.4 * math.sin(t * 40))
        r = random.Random(int(t * 30))
        for i in range(16):
            ctx.rectangle(0, r.random() * H, W, r.uniform(4, 40))
            fill(ctx, r.choice([COL_B, "#ffffff", "#ef4444"]), 0.35 * g)
        text(ctx, "ВТОРОЙ ГОЛОС", 540, 520, 96, COL_B, "#000", 14, alpha=seg(u, tb, tb + 0.2))


def s6_voiceB(ctx, t, u, D):
    radio_scene(ctx, t, u, D, 6, COL_B, "??? НЕИЗВЕСТНЫЙ", "fear", "shock", glitch=0.5)
    tm = EV["mountains"] - TL.shots[6][0]
    if u > tm:
        s = back_out(seg(u, tm, tm + 0.25))
        ctx.save()
        ctx.translate(540, 1180)
        ctx.scale(max(0.02, s), max(0.02, s))
        text(ctx, "ГОРЫ?!", 0, 0, 150, "#ffffff", "#b91c1c", 18)
        ctx.restore()


def s7_down(ctx, t, u, D):
    k = ease(seg(u, 0, D))
    ctx.save()
    cam(ctx, t, 540, lerp(700, 1200, k), lerp(0.9, 1.0, k), shake=0.4)
    night_sky(ctx, t)
    ctx.arc(820, 260, 80, 0, TAU)
    fill(ctx, "#f1f5f9")
    glow(ctx, 820, 260, 400, "#cbd5e1", 0.3)
    # море облаков внизу, без огней
    vgrad(ctx, -1200, 900, 3500, 2400, [(0, "#475569"), (1, "#1e293b")])
    for row in range(7):
        clouds(ctx, t * 0.4, 40 + row, 900 + row * 180, 960 + row * 180, 120 + row * 40,
               ["#64748b", "#475569", "#334155"][row % 3], 0.9, 14, 1.2 + row * 0.25)
    airliner(ctx, 540, lerp(820, 720, k), 0.45, t, tilt=0.12)
    ctx.restore()


def s8_voiceA2(ctx, t, u, D):
    radio_scene(ctx, t, u, D, 8, COL_A, "ДИСПЕТЧЕР", "worry", "worry", look=(-0.6, -0.5))
    # топливо падает
    f = lerp(17, 15, seg(u, 0, D))
    rr(ctx, 700, 1250, 300, 120, 20)
    fill(ctx, "#111827", 0.9)
    text(ctx, "ТОПЛИВО", 850, 1285, 30, "#fca5a5")
    text(ctx, f"{int(f)} МИН", 850, 1335, 50, "#ef4444")


def s9_terrain(ctx, t, u, D):
    tr = EV["radar"] - TL.shots[9][0]
    ctx.save()
    if u < tr:
        radio_scene(ctx, t, u, D, 9, COL_B, "??? НЕИЗВЕСТНЫЙ", "shock", "fear", glitch=0.7)
    else:  # экран рельефа: горы то есть, то нет
        k = seg(u, tr, D)
        cam(ctx, t, 540, 960, lerp(1.0, 1.15, k), shake=0.6)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#020617"), (1, "#0b1120")])
        rr(ctx, 90, 360, 900, 1100, 40)
        fill(ctx, "#111827")
        ctx.save()
        rr(ctx, 130, 400, 820, 1020, 24)
        ctx.clip()
        src(ctx, "#000")
        ctx.paint()
        show = int(t * 5) % 3 != 0  # мерцает: есть рельеф или нет
        if show:
            r = random.Random(4)
            for i in range(26):
                x, y = r.uniform(130, 950), r.uniform(420, 1000)
                rad = r.uniform(40, 120)
                ctx.arc(x, y, rad, 0, TAU)
                fill(ctx, r.choice(["#16a34a", "#ca8a04", "#dc2626"]), 0.7)
        for rr_ in (150, 300, 450):
            ctx.arc(540, 1400, rr_, math.pi, TAU)
            ctx.set_line_width(3)
            src(ctx, "#22d3ee", 0.6)
            ctx.stroke()
        ctx.move_to(540, 1360)
        ctx.line_to(510, 1420)
        ctx.line_to(570, 1420)
        fill(ctx, "#ffffff")
        ctx.restore()
        if show and (t * 4) % 1 < 0.6:
            text(ctx, "TERRAIN! PULL UP!", 540, 300, 64, "#ef4444", "#000", 10)
        else:
            text(ctx, "НЕТ ДАННЫХ", 540, 300, 64, "#64748b", "#000", 10)
    ctx.restore()


def s10_split(ctx, t, u, D):
    c0, c1 = EV["countdown"]
    secs = lerp(19 * 60, 12 * 60, ease(seg(t, c0, c1)))
    m, s = int(secs // 60), int(secs % 60)
    ctx.save()
    cam(ctx, t, 540, 960, 1.0, shake=0.5)
    ctx.rectangle(-500, -500, 1040, 3000)
    fill(ctx, "#03141f")
    ctx.rectangle(540, -500, 1100, 3000)
    fill(ctx, "#1f0f03")
    radio2(ctx, 270, 640, 0.42, t, COL_A, "ДИСПЕТЧЕР", 8)
    radio2(ctx, 810, 640, 0.42, t, COL_B, "???", 9, 0.3)
    text(ctx, "ВНИЗ", 270, 900, 90, COL_A, "#000", 12)
    text(ctx, "ВВЕРХ", 810, 900, 90, COL_B, "#000", 12)
    line(ctx, 540, -500, 540, 2500, 6, "#ffffff", 0.5)
    hero(ctx, 540, 1960, 1.4, emo("fear"), t, arms="down", legs=False, look=(math.sin(t * 4) * 0.9, 0),
         tremble=1.0, rim="#ffffff")
    # капля пота
    ell(ctx, 700, 1460 + (t * 200) % 120, 14, 22)
    fill(ctx, "#bfe6ff", 0.9)
    ctx.restore()
    rr(ctx, 290, 1100, 500, 150, 30)
    fill(ctx, "#000", 0.85)
    text(ctx, f"{m:02d}:{s:02d}", 540, 1175, 120, "#ef4444")


def other_cockpit_fn(t, k):
    def f(c):
        src(c, "#0b1220")
        c.paint()
        glow(c, 700, -40, 80, COL_B, 0.6)
        hero_head(c, 690, -50, 18, emo("neutral"), t, rim=COL_B, rim_a=0.8)
    return f


def s11_window(ctx, t, u, D):
    tl_ = EV["light"] - TL.shots[11][0]
    tt = EV["tail"] - TL.shots[11][0]
    ctx.save()
    if u < tt:
        k = seg(u, 0, tt)
        cam(ctx, t, 540, 960, lerp(0.8, 0.88, k), shake=0.4)
        night_sky(ctx, t, 0.6 * (1 - seg(u, tl_, tl_ + 0.4)) if u > tl_ else 0)
        ctx.arc(860, 300, 80, 0, TAU)
        fill(ctx, "#f1f5f9")
        clouds(ctx, t, 3, 300, 1800, 500, "#334155", 0.5, 12, 1.3)
        appear = ease(seg(u, tl_, tl_ + 1.2))
        airliner(ctx, lerp(1500, 560, appear), 620, 0.5, t, landing_lights=True, livery="#3b0d0d")
        airliner(ctx, 520, 1250, 0.58, t)
        clouds(ctx, t, 4, 1500, 2300, 1100, "#475569", 0.8, 10, 1.6)
    else:  # крупно хвост «307» соседнего самолёта
        k = seg(u, tt, D)
        cam(ctx, t, 540, 960, 1.0, shake=0.4)
        night_sky(ctx, t)
        clouds(ctx, t, 3, 1300, 1900, 700, "#334155", 0.6, 10, 1.3)
        airliner(ctx, lerp(1650, 1500, k), 1230, 2.2, t, livery="#3b0d0d")
    ctx.restore()


def double_nose(ctx, t, raise_k):
    """Крупно нос соседнего лайнера: в кабине двойник подносит рацию."""
    ctx.move_to(-400, 2200)
    ctx.line_to(-400, 700)
    ctx.curve_to(200, 520, 900, 560, 1400, 900)
    ctx.line_to(1500, 2200)
    ctx.close_path()
    lgrad(ctx, 0, 600, 0, 2200, [(0, "#f8fafc"), (0.6, "#cbd5e1"), (1, "#64748b")])
    ctx.fill()
    for k, (x0, x1) in enumerate(((60, 480), (520, 920))):
        ctx.move_to(x0, 880)
        ctx.line_to(x1, 860)
        ctx.line_to(x1 + 60, 1160)
        ctx.line_to(x0 + 10, 1180)
        ctx.close_path()
        fill(ctx, "#0b1220")
    ctx.save()
    ctx.move_to(60, 880)
    ctx.line_to(480, 860)
    ctx.line_to(540, 1160)
    ctx.line_to(70, 1180)
    ctx.close_path()
    ctx.clip()
    glow(ctx, 300, 1200, 400, COL_B, 0.5)
    e = emo("neutral")
    e["pup"] = 0.4
    a1 = lerp(0.18, 1.0, raise_k)
    a2 = lerp(0.05, -2.3, raise_k)
    hero(ctx, 290, 1300, 0.95, e, t, arms=((0.18, 0.05), (a1, a2)), legs=False, look=(0, 0), rim=COL_B,
         rim_a=1.0, hand_item=mic_item)
    ctx.restore()
    for (x0, x1) in ((60, 480), (520, 920)):
        line(ctx, x0 + 30, 900, x0 + 90, 1100, 6, "#ffffff", 0.15)
    rr(ctx, 1000, 1000, 160, 260, 40)
    ctx.set_line_width(4)
    src(ctx, "#94a3b8")
    ctx.stroke()
    ctx.rectangle(-400, 1500, 1900, 40)
    fill(ctx, "#d8332a")
    text(ctx, "307", 1100, 1400, 90, "#1e3a8a")


def s12_double(ctx, t, u, D):
    rk = ease(seg(t, EV["raise"] - 0.6, EV["raise"] + 0.9))
    k = seg(u, 0, D)
    ctx.save()
    cam(ctx, t, lerp(560, 300, ease(k)), lerp(1150, 1030, ease(k)), lerp(0.85, 1.9, ease(k)), shake=0.35)
    night_sky(ctx, t)
    clouds(ctx, t, 6, 1500, 2300, 900, "#334155", 0.7, 10, 1.4)
    double_nose(ctx, t, rk)
    ctx.restore()
    # рамка нашего бокового окна
    ctx.save()
    ctx.rectangle(0, 0, W, H)
    rr(ctx, 70, 230, 940, 1420, 160)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill(ctx, "#111827")
    ctx.restore()
    rr(ctx, 70, 230, 940, 1420, 160)
    ctx.set_line_width(20)
    src(ctx, "#374151")
    ctx.stroke()


def s13_dont(ctx, t, u, D):
    ec = EV["end_card"] - TL.shots[13][0]
    ctx.save()
    if u < ec - 1.3:
        radio_scene(ctx, t, u, D, 13, COL_B, "БОРТ 307 (2)", "fear", "shock", glitch=0.2)
    elif u < ec:
        k = seg(u, ec - 1.3, ec)
        cam(ctx, t, 540, 900, lerp(1.0, 1.2, k), shake=1.0)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1f0f03"), (1, "#020617")])
        glow(ctx, 540, 1300, 900, COL_B, 0.3)
        hero(ctx, 540, 1700, 2.1, emo("shock"), t, arms="shock", legs=False, tremble=1.4, rim=COL_B)
        ctx.rectangle(-800, -800, 2700, 3600)
        fill(ctx, "#000", seg(u, ec - 0.25, ec))
    else:
        k = seg(u, ec, ec + 0.6)
        src(ctx, "#000")
        ctx.paint()
        s = max(0.02, back_out(k))
        ctx.translate(540, 820)
        ctx.scale(s, s)
        text(ctx, "ПРОДОЛЖЕНИЕ", 0, -190, 70, "#ffffff")
        text(ctx, "ЧАСТЬ 2", 0, -10, 190, "#ffd400", "#d8332a", 18)
        text(ctx, "Кому верить?", 0, 180, 70, COL_B)
        ea = max(0.02, seg(u, ec + 0.4, ec + 1.0))
        ctx.translate(0, 470)
        ctx.scale(ea * 0.42, ea * 0.42)
        radio2(ctx, -280, 0, 0.5, t, COL_A, "ДИСПЕТЧЕР")
        radio2(ctx, 280, 0, 0.5, t, COL_B, "???")
    ctx.restore()


SCENES = [s0_midnight, s1_falling, s2_pilots, s3_grab, s4_voiceA, s5_push, s6_voiceB, s7_down, s8_voiceA2,
          s9_terrain, s10_split, s11_window, s12_double, s13_dont]
LABELS = {0: "00:00", 1: "00:00", 2: "19 МИН", 3: "19 МИН", 4: "18 МИН", 5: "18 МИН", 6: "17 МИН",
          7: "16 МИН", 8: "15 МИН", 9: "14 МИН", 10: "12 МИН", 11: "12 МИН", 12: "12 МИН", 13: "12 МИН"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("триста", "семь"), "307"), (("двести",), "200"), (("девятнадцать",), "19"),
         (("двенадцать",), "12")]


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
    hook_end = EV["sleep"] + 0.6
    if t < hook_end:  # заголовок-хук
        k1 = back_out(seg(t, 0.0, 0.3))
        out = 1 - seg(t, hook_end - 0.3, hook_end)
        ctx.save()
        ctx.translate(540, 360)
        ctx.scale(k1, k1)
        ctx.push_group()
        text(ctx, "ЧТО, ЕСЛИ В РАЦИИ", 0, -110, 80, "#ffffff", "#000", 16, shadow=True)
        text(ctx, "ДВА ГОЛОСА,", 0, 10, 116, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -330, 90, 660, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "ОДИН ЛЖЁТ?", 0, 155, 100, "#ffffff")
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
