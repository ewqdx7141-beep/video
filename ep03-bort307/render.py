"""Серия 3 «Борт 307»: python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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


def cabin(ctx, t, x0, x1, mode="sleep", flash=0.0, hero_x=None, hero_e=None, hero_walk=None, stew_x=1650):
    """Салон в разрезе: багажные полки, иллюминаторы, ряды кресел с пассажирами."""
    vgrad(ctx, -2000, -800, 6000, 3600, [(0, "#cbd5e1"), (1, "#94a3b8")])
    # полки
    rr(ctx, -2000, 330, 6000, 220, 30)
    lgrad(ctx, 0, 330, 0, 550, [(0, "#f1f5f9"), (1, "#cbd5e1")])
    ctx.fill()
    for k in range(-8, 16):
        line(ctx, k * 300, 340, k * 300, 540, 4, "#94a3b8")
        rr(ctx, k * 300 + 110, 440, 80, 14, 6)
        fill(ctx, "#94a3b8")
        ell(ctx, k * 300 + 150, 560, 30, 10)
        fill(ctx, "#fde68a" if mode != "dark" else "#475569")
        if k % 3 == 0:  # табло «пристегните ремни»
            rr(ctx, k * 300 + 40, 585, 90, 34, 8)
            fill(ctx, "#111827")
            on_ = (t * 1.5) % 1 < 0.7 if mode == "sleep" else True
            rr(ctx, k * 300 + 52, 592, 28, 20, 4)
            fill(ctx, "#fbbf24" if on_ else "#3f3f46")
            ctx.arc(k * 300 + 104, 602, 9, 0, TAU)
            fill(ctx, "#fbbf24" if on_ else "#3f3f46")
        if k % 4 == 1 and mode == "sleep":  # лампа для чтения
            ctx.move_to(k * 300 + 135, 570)
            ctx.line_to(k * 300 + 165, 570)
            ctx.line_to(k * 300 + 260, 1400)
            ctx.line_to(k * 300 + 40, 1400)
            ctx.close_path()
            fill(ctx, "#fef3c7", 0.12)
    # открытая багажная полка с сумкой
    for k in (2, 9):
        ctx.save()
        ctx.translate(k * 300, 330)
        ctx.rotate(-0.5)
        rr(ctx, 0, -20, 290, 30, 8)
        fill(ctx, "#e2e8f0")
        ctx.restore()
        rr(ctx, k * 300 + 40, 470, 140, 90, 14)
        fill(ctx, "#7c3aed")
        line(ctx, k * 300 + 120, 560, k * 300 + 130, 700, 6, "#111827")
    # иллюминаторы
    for k in range(-8, 16):
        cx = k * 300 + 150
        rr(ctx, cx - 50, 640, 100, 150, 46)
        fill(ctx, "#0f1b3d")
        if flash > 0:
            rr(ctx, cx - 50, 640, 100, 150, 46)
            fill(ctx, "#e0e7ff", flash)
        sh = (k * 37 % 5) / 5  # шторки на разной высоте
        if sh > 0.3:
            ctx.save()
            rr(ctx, cx - 50, 640, 100, 150, 46)
            ctx.clip()
            ctx.rectangle(cx - 50, 640, 100, 150 * sh)
            fill(ctx, "#e5e7eb")
            line(ctx, cx - 50, 640 + 150 * sh, cx + 50, 640 + 150 * sh, 4, "#94a3b8")
            ctx.restore()
        rr(ctx, cx - 50, 640, 100, 150, 46)
        ctx.set_line_width(10)
        src(ctx, "#e2e8f0")
        ctx.stroke()
    # пол
    ctx.rectangle(-2000, 1700, 6000, 800)
    fill(ctx, "#334155")
    for k in range(-20, 40):
        line(ctx, k * 120, 1710, k * 120 + 60, 1900, 4, "#3f4b5f")
        ctx.arc(k * 120 + 40, 1780, 6, 0, TAU)
        fill(ctx, "#475569")
    # вещи на полу
    for k in range(-6, 14):
        rk = random.Random(k * 3 + 1)
        fx = k * 300 + rk.uniform(80, 220)
        kind = rk.choice(["shoe", "mag", "phone", "bottle", None, None])
        if kind == "shoe":
            ell(ctx, fx, 1700, 30, 14)
            fill(ctx, rk.choice(["#7c2d12", "#111827", "#f8fafc"]))
        elif kind == "mag":
            ctx.save()
            ctx.translate(fx, 1702)
            ctx.rotate(0.15)
            rr(ctx, -40, -8, 80, 14, 2)
            fill(ctx, "#f472b6")
            ctx.restore()
        elif kind == "phone" and mode == "sleep":
            rr(ctx, fx - 22, 1694, 44, 12, 3)
            fill(ctx, "#111")
            glow(ctx, fx, 1690, 60, "#7dd3fc", 0.5)
        elif kind == "bottle":
            ctx.save()
            ctx.translate(fx, 1696)
            ctx.rotate(1.5)
            rr(ctx, -10, -30, 20, 60, 8)
            fill(ctx, "#7dd3fc", 0.7)
            ctx.restore()
    r = random.Random(13)
    rows = list(range(-6, 14))
    for k in rows:
        sx = k * 300
        if sx < x0 - 400 or sx > x1 + 400:
            continue
        p = Npc(random.Random(k * 31 + 7), sx + 120, 1640, 0.95, 1)
        p.item = "phone" if k % 4 == 0 else "none"
        rk = random.Random(k * 11 + 5)
        p.neck_pillow = rk.random() < 0.35
        p.mask = mode == "sleep" and rk.random() < 0.3
        # спинка кресла (за пассажиром)
        rr(ctx, sx + 20, 1060, 120, 520, 40)
        lgrad(ctx, sx + 20, 0, sx + 140, 0, [(0, "#1e3a8a"), (1, "#2563eb")])
        ctx.fill()
        rr(ctx, sx + 30, 1040, 100, 70, 20)
        fill(ctx, "#e2e8f0")
        ctx.save()
        tilt_ = (0.12 if k % 2 else -0.06) if mode == "sleep" else 0.0
        ctx.translate(sx + 120, 1640)
        ctx.rotate(tilt_)
        ctx.translate(-(sx + 120), -1640)
        npc(ctx, p, t, walking=False, sleep=(mode == "sleep"), clap=(mode == "clap"),
            grin=0.25 if mode == "clap" else 0.0)
        ctx.restore()
        # сиденье, плед, подлокотник
        rr(ctx, sx + 60, 1470, 220, 90, 30)
        fill(ctx, "#1d4ed8")
        if rk.random() < 0.5:
            rr(ctx, sx + 70, 1420, 200, 110, 30)
            fill(ctx, rk.choice(["#b91c1c", "#0f766e", "#a16207", "#6d28d9"]))
            for j in range(3):
                line(ctx, sx + 90 + j * 60, 1424, sx + 80 + j * 60, 1526, 5, "#ffffff", 0.25)
        # откидной столик впереди с напитком
        rr(ctx, sx + 250, 1400, 90, 14, 4)
        fill(ctx, "#cbd5e1")
        it = rk.choice(["cup", "can", "snack", None])
        if it == "cup":
            rr(ctx, sx + 280, 1360, 26, 40, 4)
            fill(ctx, "#f8fafc")
        elif it == "can":
            rr(ctx, sx + 282, 1356, 22, 44, 6)
            fill(ctx, rk.choice(["#ef4444", "#22c55e", "#3b82f6"]))
        elif it == "snack":
            rr(ctx, sx + 270, 1380, 50, 20, 4)
            fill(ctx, "#f59e0b")
        rr(ctx, sx + 150, 1420, 140, 30, 12)
        fill(ctx, "#475569")
        line(ctx, sx + 120, 1560, sx + 120, 1700, 14, "#1f2937")
        line(ctx, sx + 250, 1560, sx + 250, 1700, 14, "#1f2937")
    # стюардесса и тележка
    if x0 - 400 < stew_x < x1 + 400:
        st = Npc(random.Random(5), stew_x, 1700, 0.95, 1)
        st.style, st.shirt, st.pants, st.item = "bun", "#1e3a8a", "#1e3a8a", "none"
        st.uniform, st.glasses, st.headphones, st.earrings = "stew", False, False, True
        cx = stew_x + 250
        rr(ctx, cx - 100, 1380, 200, 300, 10)
        lgrad(ctx, cx - 100, 0, cx + 100, 0, [(0, "#94a3b8"), (0.5, "#e2e8f0"), (1, "#94a3b8")])
        ctx.fill()
        for k in range(3):
            line(ctx, cx - 90, 1440 + k * 70, cx + 90, 1440 + k * 70, 4, "#64748b")
            rr(ctx, cx - 20, 1462 + k * 70, 40, 10, 4)
            fill(ctx, "#475569")
        rr(ctx, cx - 70, 1600, 140, 36, 6)
        fill(ctx, "#d8332a")
        text(ctx, "БОРТ 307", cx, 1618, 22, "#ffffff")
        for k in range(4):  # стаканчики и бутылки
            rr(ctx, cx - 90 + k * 22, 1340, 18, 40, 3)
            fill(ctx, "#f8fafc")
        for k, c_ in enumerate(("#16a34a", "#f59e0b")):
            rr(ctx, cx + 10 + k * 34, 1310, 26, 70, 8)
            fill(ctx, c_, 0.85)
        ctx.arc(cx - 70, 1690, 16, 0, TAU)
        fill(ctx, "#111")
        ctx.arc(cx + 70, 1690, 16, 0, TAU)
        fill(ctx, "#111")
        # опрокинутый кофейник: капли
        ctx.save()
        ctx.translate(cx + 40, 1360)
        ctx.rotate(1.2 if mode == "sleep" else 0)
        rr(ctx, -30, -70, 60, 80, 12)
        fill(ctx, "#1f2937")
        ctx.restore()
        if mode == "sleep":
            for k in range(6):
                age = (t * 1.3 + k / 6) % 1
                ell(ctx, cx + 110, 1380 + age * 300, 6, 9)
                fill(ctx, "#5a3420", 1 - age * 0.6)
            ell(ctx, cx + 110, 1705, 70, 12)
            fill(ctx, "#5a3420", 0.85)
        ctx.save()
        if mode == "sleep":
            ctx.translate(stew_x, 1700)
            ctx.rotate(0.38)
            ctx.translate(-stew_x, -1700)
        npc(ctx, st, t, walking=False, sleep=(mode == "sleep"), clap=(mode == "clap"),
            grin=0.25 if mode == "clap" else 0.0)
        ctx.restore()
    if hero_x is not None:
        hero(ctx, hero_x, 1880, 1.0, hero_e, t, arms="relax" if hero_walk is None else "relax",
             walk=hero_walk, rim="#93c5fd", rim_a=0.6, look=(0.6, 0))


# ================================================================== СЦЕНЫ
def s0_wake(ctx, t, u, D):
    wk = EV["wake"] - TL.shots[0][0]
    fl = 0.0
    for lt in EV["lightning"]:
        if 0 <= t - lt < 0.35:
            fl = max(fl, 1 - (t - lt) / 0.35)
    ctx.save()
    if u < wk:
        cam(ctx, t, 540, 960, lerp(0.75, 0.9, seg(u, 0, wk)), shake=0.6)
        night_sky(ctx, t, fl)
        clouds(ctx, t, 1, 300, 1600, 600, "#334155", 0.6, 12, 1.3)
        if fl > 0.3:
            bolt(ctx, 820, -200, 1100, int(t), fl)
        airliner(ctx, 540, 960, 0.75, t)
        clouds(ctx, t, 2, 1300, 2200, 1200, "#475569", 0.8, 10, 1.6)
    else:
        k = seg(u, wk, D)
        cam(ctx, t, 520, 1050, lerp(1.25, 1.4, ease(k)), shake=0.5)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1e293b"), (1, "#0f172a")])
        rr(ctx, 60, 520, 300, 440, 140)
        fill(ctx, "#0f1b3d")
        if fl > 0:
            rr(ctx, 60, 520, 300, 440, 140)
            fill(ctx, "#e0e7ff", fl)
        rr(ctx, 60, 520, 300, 440, 140)
        ctx.set_line_width(26)
        src(ctx, "#cbd5e1")
        ctx.stroke()
        # спинка кресла и сосед, спящий с открытым ртом
        rr(ctx, 380, 760, 420, 900, 100)
        fill(ctx, "#1e3a8a")
        p = Npc(random.Random(3), 880, 1700, 1.25, -1)
        p.neck_pillow, p.mask = True, True
        ctx.save()
        ctx.translate(880, 1700)
        ctx.rotate(-0.25)
        ctx.translate(-880, -1700)
        ctx.rectangle(0, 0, 2000, 1420)
        ctx.clip()
        npc(ctx, p, t, walking=False, sleep=True)
        ctx.restore()
        rr(ctx, 380, 1380, 900, 600, 60)
        fill(ctx, "#1d4ed8")
        e = emo("sleep") if u < wk + 0.25 else emo("shock")
        hero(ctx, 560, 1640, 1.05, e, t, arms="down", legs=False, look=(0.8, 0.1), rim="#93c5fd",
             tremble=0.4 if u > wk + 0.25 else 0)
    ctx.restore()
    if fl > 0:
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#e0e7ff", 0.25 * fl)


def s1_cabin(ctx, t, u, D):
    camx = lerp(300, 1650, ease(seg(u, 0, D)))
    ctx.save()
    cam(ctx, t, camx, 1300, 1.05, shake=0.35)
    cabin(ctx, t, camx - 700, camx + 700, "sleep", hero_x=camx - 120, hero_e=emo("fear"), hero_walk=t * 5)
    ctx.restore()


def s2_cockpit(ctx, t, u, D):
    tr = wl(2, "красное")
    k = ease(seg(u, tr - 0.2, tr + 0.5))
    ctx.save()
    cam(ctx, t, lerp(540, 910, k), lerp(1150, 1140, k), lerp(0.75, 1.35, k) + 0.1 * ease(seg(u, 0, tr)),
        shake=0.5 + 0.5 * k)
    cockpit(ctx, t, warn=1.0 if u > tr else 0.0)
    # дверь кабины качается, герой в проёме (со спины)
    if u < tr:
        hero(ctx, 540, 2250, 1.4, emo("shock"), t, arms="shock", back=True, rim="#ef4444", rim_a=0.6)
    ctx.restore()


def s3_shout(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(1.0, 1.25, ease_out(seg(u, 0, D))), shake=1.0)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1f0a0a"), (1, "#0b0f16")])
    on = (t * 3) % 1 < 0.6
    for k in range(10):
        rr(ctx, -200 + k * 160, 300, 100, 60, 10)
        fill(ctx, "#ef4444" if (on and k % 3 == 0) else "#334155")
    if on:
        glow(ctx, 540, 600, 1200, "#ef4444", 0.4)
    sh = wl(3, "помогите")
    e = emo("worry") if u < sh else emo("shock")

    def mic(c, x, y):
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
    hero(ctx, 540, 1750, 1.6, e, t, arms="phone", legs=False, rim="#ef4444", tremble=1.2 if u > sh else 0.5,
         hand_item=mic)
    ctx.restore()
    if u > sh:
        text(ctx, "ПОМОГИТЕ!", 540, 420, 120, "#ffffff", "#b91c1c", 16, alpha=seg(u, sh, sh + 0.1))


def radio_unit(ctx, x, y, s, t, on=0.0, li=None, col="#22c55e"):
    """Рация: частота, лампа, решётка динамика, осциллограф по голосу строки li."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 330, 520, 60, 0.5)
    rr(ctx, -460, -300, 920, 600, 40)
    lgrad(ctx, 0, -300, 0, 300, [(0, "#374151"), (1, "#111827")])
    ctx.fill()
    rr(ctx, -400, -250, 500, 160, 16)
    fill(ctx, "#020617")
    text(ctx, "118.307", -150, -170, 90, col if on > 0.5 else "#1f2937")
    ctx.arc(330, -170, 36, 0, TAU)
    fill(ctx, col if on > 0.5 else "#14532d")
    if on > 0.5:
        glow(ctx, 330, -170, 160, col, 0.6)
    for k in range(9):  # решётка
        line(ctx, -400, -40 + k * 30, 100, -40 + k * 30, 10, "#0b0f16")
    rr(ctx, 150, -40, 270, 280, 16)
    fill(ctx, "#020617")
    # осциллограф
    amp = 0.0
    if li is not None:
        l = TL.lines[li]
        uu = t - l["start"]
        for w in l["words"]:
            if w["t"] <= uu <= w["t"] + w["d"]:
                amp = 1.0
    ctx.move_to(165, 100)
    for k in range(60):
        xx = 165 + k * 4.2
        yy = 100 + math.sin(k * 0.9 + t * 40) * 80 * amp * math.sin(k / 60 * math.pi) * (0.6 + 0.4 * math.sin(k * 3.1 + t * 17))
        ctx.line_to(xx, yy)
    ctx.set_line_width(5)
    src(ctx, col, 0.4 + 0.6 * on)
    ctx.stroke()
    for k, kx in enumerate((-300, -120)):
        ctx.arc(kx, 230, 50, 0, TAU)
        fill(ctx, "#1f2937")
        line(ctx, kx, 230, kx + math.cos(k + t * 0.3) * 40, 230 + math.sin(k + t * 0.3) * 40, 8, "#9ca3af")
    ctx.restore()


def s4_answer(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 960, lerp(0.95, 1.1, ease(seg(u, 0, D))), shake=0.4)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0b1120"), (1, "#020617")])
    on = seg(u, D - 0.5, D - 0.3)
    radio_unit(ctx, 540, 900, 1.0, t, on)
    if on > 0:
        glow(ctx, 540, 900, 900, "#22c55e", 0.15 * on)
    ctx.restore()


def s5_hear(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(1.0, 1.08, ease(seg(u, 0, D))), shake=0.4)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#04140c"), (1, "#020617")])
    glow(ctx, 540, 600, 900, "#22c55e", 0.2)
    radio_unit(ctx, 540, 520, 0.8, t, 1.0, li=5)
    e = emo("worry", "calm", seg(u, 0.8, 2.0))
    hero(ctx, 540, 1700, 1.25, e, t, arms="down", legs=False, rim="#22c55e", look=(0, -0.7))
    ctx.restore()


def s6_commands(ctx, t, u, D):
    c1, c2, c3 = (x - TL.shots[6][0] for x in EV["cmd"])
    ctx.save()
    if u < c2:  # штурвал на себя
        k = ease(seg(u, c1, c1 + 0.8))
        cam(ctx, t, 540, 1000, lerp(1.0, 1.1, k), shake=0.5)
        cockpit(ctx, t, warn=1.0, horizon=-k, slump=1.0, speed=lerp(280, 260, k))
        ctx.save()
        ctx.translate(540, 1700)
        sc = lerp(1.0, 1.35, k)
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
        text(ctx, "НА СЕБЯ", 540, 640, 110, "#22c55e", "#000", 14, alpha=seg(u, c1, c1 + 0.2))
    elif u < c3:  # скорость 240
        k = ease(seg(u, c2, c2 + 1.0))
        cam(ctx, t, 540, 960, 1.0, shake=0.4)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0b1120"), (1, "#020617")])
        ctx.arc(540, 960, 400, 0, TAU)
        fill(ctx, "#020617")
        ctx.arc(540, 960, 400, 0, TAU)
        ctx.set_line_width(20)
        src(ctx, "#334155")
        ctx.stroke()
        for v in range(0, 360, 20):
            a = -math.pi * 1.25 + v / 360 * math.pi * 1.5
            line(ctx, 540 + math.cos(a) * 340, 960 + math.sin(a) * 340, 540 + math.cos(a) * 380,
                 960 + math.sin(a) * 380, 8 if v % 60 == 0 else 4, "#e5e7eb")
            if v % 60 == 0:
                text(ctx, str(v), 540 + math.cos(a) * 290, 960 + math.sin(a) * 290, 40, "#e5e7eb")
        ctx.arc(540, 960, 380, -math.pi * 1.25 + 230 / 360 * math.pi * 1.5, -math.pi * 1.25 + 250 / 360 * math.pi * 1.5)
        ctx.set_line_width(26)
        src(ctx, "#22c55e")
        ctx.stroke()
        v = lerp(300, 240, k) + math.sin(t * 9) * 3 * (1 - k)
        a = -math.pi * 1.25 + v / 360 * math.pi * 1.5
        line(ctx, 540, 960, 540 + math.cos(a) * 330, 960 + math.sin(a) * 330, 16, "#ef4444")
        ctx.arc(540, 960, 40, 0, TAU)
        fill(ctx, "#e5e7eb")
        text(ctx, f"{int(v)}", 540, 1180, 90, "#22c55e")
    else:  # шасси
        k = ease(seg(u, c3, c3 + 0.6))
        cam(ctx, t, 540, 1000, lerp(1.0, 1.08, k), shake=0.5 + 0.8 * seg(u, c3 + 0.5, c3 + 0.7))
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#111827"), (1, "#020617")])
        rr(ctx, 380, 500, 320, 900, 30)
        fill(ctx, "#1f2937")
        rr(ctx, 520, 560, 40, 780, 20)
        fill(ctx, "#020617")
        hy = lerp(620, 1240, k)
        rr(ctx, 450, hy - 40, 180, 80, 30)
        fill(ctx, "#e5e7eb")
        ctx.arc(540, hy, 30, 0, TAU)
        fill(ctx, "#9ca3af")
        text(ctx, "UP", 760, 640, 50, "#9ca3af")
        text(ctx, "DOWN", 790, 1240, 50, "#9ca3af")
        for i in range(3):
            on = u > c3 + 0.6 + i * 0.25
            ctx.arc(320 + i * 220, 1580, 50, 0, TAU)
            fill(ctx, "#22c55e" if on else "#14532d")
            if on:
                glow(ctx, 320 + i * 220, 1580, 120, "#22c55e", 0.6)
        ctx.arc(540 + 160, hy - 60, 60, 0, TAU)  # рука героя
        fill(ctx, HEAD)
    ctx.restore()


def runway_scene(ctx, t, u, D, t_light, t_imp, t_sp, t_sil):
    night_sky(ctx, t)
    ctx.rectangle(-1200, 1200, 3500, 1500)
    fill(ctx, "#05080f")
    # полоса в перспективе
    lit = seg(t, t_light, t_light + 0.6)
    ctx.move_to(440, 1210)
    ctx.line_to(640, 1210)
    ctx.line_to(1500, 2200)
    ctx.line_to(-420, 2200)
    ctx.close_path()
    fill(ctx, "#1f2937")
    for k in range(12):
        f = k / 12
        y = 1210 + (f ** 1.8) * 990
        wx = lerp(100, 960, f ** 1.8)
        for side in (-1, 1):
            ctx.arc(540 + side * wx, y, lerp(4, 18, f), 0, TAU)
            fill(ctx, "#fde68a", lit)
            if lit > 0:
                glow(ctx, 540 + side * wx, y, lerp(20, 80, f), "#fbbf24", 0.6 * lit)
        rr(ctx, 540 - lerp(4, 24, f), y, lerp(8, 48, f), lerp(6, 40, f), 3)
        fill(ctx, "#e5e7eb", 0.8)
    # огни подхода «бегущие»
    for k in range(6):
        on = (t * 4 - k * 0.2) % 1 < 0.2
        ctx.arc(540, 1190 - k * 30, 6, 0, TAU)
        fill(ctx, "#ffffff", lit * (1.0 if on else 0.2))
    # самолёт: снижается к полосе
    k = seg(t, t_light - 0.6, t_imp)
    py = lerp(600, 1520, ease_in(k, 1.4))
    s = lerp(0.3, 0.68, k)
    bump = 30 * math.sin(seg(t, t_imp, t_imp + 0.5) * math.pi) if t > t_imp else 0
    airliner(ctx, lerp(380, 540, k), py - bump, s, t, gear=True, tilt=lerp(-0.06, 0.02, k))
    if t > t_sp - 0.1 and t < t_sil + 0.2:
        r = random.Random(int(t * 30))
        for i in range(40):
            a = r.uniform(math.pi * 0.85, math.pi * 1.25)
            L = r.uniform(40, 260)
            for gx in (-200, 560):
                x0, y0 = 540 + gx * 0.68, 1520 + 186 * 0.68
                line(ctx, x0, y0, x0 + math.cos(a) * L, y0 + math.sin(a) * L * 0.4, 4,
                     r.choice(["#fde68a", "#fb923c", "#ffffff"]))


def s7_landing(ctx, t, u, D):
    tl_, ti, ts, tsil = EV["runway"], EV["impact"], EV["sparks"], EV["silence"]
    sh = 2.0 if ti <= t < ti + 0.4 else (1.0 if ts <= t < tsil else 0.4)
    ctx.save()
    cam(ctx, t, 540, 1150, lerp(0.85, 1.0, ease(seg(t, tl_, ti))), shake=sh)
    runway_scene(ctx, t, u, D, tl_, ti, ts, tsil)
    ctx.restore()
    if t >= tsil:
        a = 1 - seg(t, tsil, tsil + 0.5)
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#ffffff", a)
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#000", 0.5 * seg(t, tsil + 0.3, tsil + 1.0))


def s8_applause(ctx, t, u, D):
    ap = EV["applause"][0] - TL.shots[8][0]
    camx = lerp(900, 1200, ease(seg(u, 0, D)))
    ctx.save()
    cam(ctx, t, camx, 1300, lerp(1.05, 1.15, ease(seg(u, 0, D))), shake=0.3)
    mode = "awake" if u < ap else "clap"
    cabin(ctx, t, camx - 700, camx + 700, mode, hero_x=camx, hero_e=emo("worry"), stew_x=1650)
    ctx.restore()
    if u > ap:
        text(ctx, "👏", 0, 0, 1, "#000", alpha=0)
        for k in range(3):
            a = seg(u, ap + k * 0.3, ap + k * 0.3 + 0.2) * (1 - seg(u, D - 0.4, D))
            text(ctx, "ХЛОП", 220 + k * 320, 480 + (k % 2) * 90, 70, "#ffd400", "#000", 10, alpha=a)


def s9_run(ctx, t, u, D):
    camx = lerp(200, 900, ease(seg(u, 0, D)))
    ctx.save()
    cam(ctx, t, camx, 1100, lerp(0.8, 0.7, seg(u, 0, D)), shake=0.8)
    night_sky(ctx, t)
    ctx.arc(900, 300, 90, 0, TAU)
    fill(ctx, "#f1f5f9")
    glow(ctx, 1250, 380, 500, "#cbd5e1", 0.15)
    tower_ext(ctx, 1250, 1400, 0.8, t, lit=True, moon_x=-1)
    airliner(ctx, -300, 1300, 0.6, t, gear=True, landing_lights=False, lit=False)
    ctx.rectangle(-2000, 1400, 6000, 1500)
    fill(ctx, "#111827")
    for k in range(-10, 30):
        ctx.arc(k * 160, 1420, 7, 0, TAU)
        fill(ctx, "#60a5fa")
        line(ctx, k * 300, 1600, k * 300 + 160, 1600, 10, "#e5e7eb", 0.5)
    hero(ctx, camx - 100, 1700, 0.9, emo("worry"), t, arms="relax", walk=t * 12, rim="#93c5fd",
         look=(0.8, -0.3), bob=-abs(math.sin(t * 12)) * 10)
    ctx.restore()


def tower_room(ctx, t, beam=None):
    vgrad(ctx, -1200, -1200, 3500, 4400, [(0, "#0b1120"), (1, "#05070d")])
    # панорамные окна с трещинами и дырами
    for k in range(5):
        x = -260 + k * 360
        rr(ctx, x, 200, 330, 620, 6)
        fill(ctx, "#0f1b3d")
        stars(ctx, 20 + k, 330, 620, t, 6) if False else None
    stars(ctx, 4, 1080, 800, t, 40)
    ctx.arc(820, 380, 80, 0, TAU)
    fill(ctx, "#e2e8f0")
    glow(ctx, 820, 380, 320, "#cbd5e1", 0.3)
    for k in range(6):
        ctx.rectangle(-280 + k * 360, 180, 30, 660)
        fill(ctx, "#111827")
    ctx.rectangle(-1200, 160, 3500, 40)
    fill(ctx, "#111827")
    ctx.rectangle(-1200, 820, 3500, 40)
    fill(ctx, "#111827")
    r = random.Random(3)
    for k in range(4):  # трещины
        cx, cy = r.uniform(-100, 1200), r.uniform(260, 760)
        for j in range(7):
            a = j * TAU / 7 + r.uniform(-0.2, 0.2)
            L = r.uniform(60, 160)
            line(ctx, cx, cy, cx + math.cos(a) * L, cy + math.sin(a) * L, 3, "#94a3b8", 0.7)
    # лунный луч
    ctx.move_to(700, 250)
    ctx.line_to(940, 250)
    ctx.line_to(700, 1900)
    ctx.line_to(200, 1900)
    ctx.close_path()
    fill(ctx, "#cbd5e1", 0.06)
    dust(ctx, 9, 1080, 1900, t, 70, "#e2e8f0", 0.35)
    # пульт
    ctx.rectangle(-1200, 1100, 3500, 900)
    lgrad(ctx, 0, 1100, 0, 2000, [(0, "#1f2937"), (1, "#0b0f16")])
    ctx.fill()
    for k in range(4):
        x = -120 + k * 340
        rr(ctx, x, 880, 280, 200, 10)
        fill(ctx, "#020617")
        line(ctx, x + 30, 900, x + 220, 1060, 3, "#334155")
        line(ctx, x + 200, 900, x + 90, 1040, 3, "#334155")
    rr(ctx, -1200, 1080, 3500, 30, 6)
    fill(ctx, "#475569", 0.4)
    # потолок, провода, качающаяся разбитая лампа
    ctx.rectangle(-1200, -1200, 3500, 1370)
    fill(ctx, "#0b0f16")
    for k in range(-4, 12):
        line(ctx, k * 160, 150, k * 160 + 40, 170, 3, "#1f2937")
    for k, (cx_, L_) in enumerate(((120, 140), (430, 90), (760, 170))):
        ctx.move_to(cx_, 150)
        ctx.curve_to(cx_ + 20, 150 + L_ * 0.5, cx_ - 30, 150 + L_ * 0.8, cx_ + 10, 150 + L_)
        ctx.set_line_width(4)
        src(ctx, "#111827")
        ctx.stroke()
    sw = math.sin(t * 1.3) * 0.25
    lx, ly = 600 + math.sin(sw) * 160, 150 + math.cos(sw) * 160
    line(ctx, 600, 150, lx, ly, 3, "#111827")
    ctx.arc(lx, ly + 14, 16, 0, TAU)
    fill(ctx, "#334155")
    line(ctx, lx - 8, ly + 6, lx + 6, ly + 22, 2, "#94a3b8")
    # старый радар, бинокль, кружка, планшет, календарь
    ctx.arc(150, 1280, 120, 0, TAU)
    fill(ctx, "#022c22")
    for rr_ in (40, 80, 115):
        ctx.arc(150, 1280, rr_, 0, TAU)
        ctx.set_line_width(2)
        src(ctx, "#14532d")
        ctx.stroke()
    line(ctx, 60, 1200, 230, 1370, 3, "#94a3b8", 0.6)
    line(ctx, 150, 1280, 150 + math.cos(t * 0.3) * 115, 1280 + math.sin(t * 0.3) * 115, 3, "#166534")
    for k in range(2):
        rr(ctx, 520 + k * 60, 1150, 50, 90, 20)
        fill(ctx, "#111827")
        ctx.arc(545 + k * 60, 1150, 24, 0, TAU)
        fill(ctx, "#334155")
    rr(ctx, 760, 1150, 60, 76, 8)
    fill(ctx, "#e5e7eb")
    ctx.arc(824, 1188, 18, -1.3, 1.3)
    ctx.set_line_width(7)
    src(ctx, "#e5e7eb")
    ctx.stroke()
    ell(ctx, 790, 1152, 26, 7)
    fill(ctx, "#365314")
    ctx.save()
    ctx.translate(900, 1170)
    ctx.rotate(-0.2)
    rr(ctx, -60, -80, 120, 160, 6)
    fill(ctx, "#d6d3d1")
    rr(ctx, -24, -90, 48, 20, 4)
    fill(ctx, "#78716c")
    for k in range(6):
        line(ctx, -44, -50 + k * 22, 44, -50 + k * 22, 3, "#78716c")
    ctx.restore()
    ctx.save()
    ctx.translate(1180, 520)
    ctx.rotate(0.06)
    rr(ctx, -70, -90, 140, 180, 4)
    fill(ctx, "#e7e5e4")
    rr(ctx, -70, -90, 140, 40, 4)
    fill(ctx, "#b91c1c")
    text(ctx, "2009", 0, -70, 26, "#ffffff")
    for i in range(4):
        for j in range(5):
            ctx.rectangle(-58 + j * 24, -40 + i * 30, 18, 22)
            fill(ctx, "#a8a29e", 0.6)
    ctx.restore()
    # паутина в углу
    for k in range(6):
        a = k * 0.25
        line(ctx, -40, 200, -40 + math.cos(a) * 300, 200 + math.sin(a) * 300, 2, "#cbd5e1", 0.35)
    for rr_ in (80, 160, 240):
        ctx.arc(-40, 200, rr_, 0, 1.3)
        ctx.set_line_width(2)
        src(ctx, "#cbd5e1", 0.3)
        ctx.stroke()
    # бумаги на полу, опрокинутый стул
    for k in range(5):
        newspaper(ctx, 100 + k * 220 + math.sin(t + k) * 10, 1820 + (k % 2) * 40, 0.3 * math.sin(k * 2 + t * 0.5), 0.9)
    chair(ctx, 1000, 1800, 1.0, "#374151")


def s10_tower(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(420, 640, ease(seg(u, 0, D))), 1050, lerp(0.85, 1.0, ease(seg(u, 0, D))), shake=0.35)
    tower_room(ctx, t)
    hero(ctx, 300, 1900, 1.0, emo("fear"), t, arms=((0.18, 0.05), (1.5, -0.2)), look=(0.6, -0.5), rim="#cbd5e1",
         blink=blink_at(u, 0.5),
         hand_item=lambda c, x, y: (rr(c, x - 18, y - 20, 70, 36, 10), fill(c, "#111827")))
    # луч фонарика
    a = -0.35 + math.sin(t * 0.7) * 0.25
    ctx.move_to(380, 1350)
    ctx.line_to(380 + math.cos(a - 0.15) * 1400, 1350 + math.sin(a - 0.15) * 1400)
    ctx.line_to(380 + math.cos(a + 0.15) * 1400, 1350 + math.sin(a + 0.15) * 1400)
    ctx.close_path()
    fill(ctx, "#fef9c3", 0.12)
    ctx.restore()


def badge(ctx, x, y, s, t, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    shadow(ctx, 20, 30, 300, 380, 0.5)
    ctx.move_to(-20, -330)
    ctx.curve_to(-300, -700, 300, -700, 20, -330)
    ctx.set_line_width(26)
    src(ctx, "#1d4ed8")
    ctx.stroke()
    rr(ctx, -260, -330, 520, 700, 30)
    fill(ctx, "#f8fafc")
    rr(ctx, -260, -330, 520, 120, 30)
    fill(ctx, "#1d4ed8")
    ctx.rectangle(-260, -250, 520, 40)
    fill(ctx, "#1d4ed8")
    text(ctx, "ДИСПЕТЧЕР", 0, -270, 54, "#ffffff")
    rr(ctx, -150, -170, 300, 330, 10)
    fill(ctx, "#cbd5e1")
    ctx.save()
    rr(ctx, -150, -170, 300, 330, 10)
    ctx.clip()
    hero_head(ctx, 0, 10, 130, emo("calm"), t, rim_a=0.0)
    rr(ctx, -110, 120, 220, 80, 30)
    fill(ctx, HOOD)
    ctx.restore()
    text(ctx, "СМЕНА: 3:07", 0, 220, 40, "#334155")
    text(ctx, "БОРТ 307", 0, 290, 40, "#d8332a")
    # пыль поверх
    r = random.Random(1)
    for i in range(120):
        ctx.arc(r.uniform(-260, 260), r.uniform(-330, 370), r.uniform(1, 4), 0, TAU)
        fill(ctx, "#94a3b8", 0.35)
    ctx.restore()


def s11_badge(ctx, t, u, D):
    bd = EV["badge"] - TL.shots[11][0]
    ph = EV["photo"] - TL.shots[11][0]
    k = ease(seg(u, ph - 0.2, ph + 0.4))
    ctx.save()
    cam(ctx, t, 540, lerp(1000, 880, k), lerp(0.9, 1.6, k), shake=0.4)
    ctx.rectangle(-1200, -1200, 3500, 4400)
    lgrad(ctx, 0, 0, 0, 1920, [(0, "#1f2937"), (1, "#0b0f16")])
    ctx.fill()
    for k2 in range(14):  # клавиши пульта
        rr(ctx, -200 + (k2 % 7) * 220, 1500 + (k2 // 7) * 140, 180, 100, 12)
        fill(ctx, "#111827")
    badge(ctx, 540, 1000, 1.0, t, -0.08)
    ctx.restore()
    # круг фонарика открывает кадр
    rad = lerp(260, 1600, ease(seg(u, bd - 0.3, bd + 1.2)))
    g = cairo.RadialGradient(540, 960, rad * 0.6, 540, 960, rad)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.97)
    ctx.set_source(g)
    ctx.paint()


def s12_turn(ctx, t, u, D):
    hs = EV["hiss"] - TL.shots[12][0]
    on = u > hs
    k = seg(u, 0, D)
    ctx.save()
    cam(ctx, t, 540, 950, 1.0, shake=0.6)
    ctx.save()
    ctx.translate(540, 900)
    ctx.scale(lerp(1.25, 0.85, k), lerp(1.25, 0.85, k))  # вертиго
    ctx.translate(-540, -900)
    tower_room(ctx, t)
    radio_unit(ctx, 880, 1000, 0.35, t, 1.0 if on else 0.0)
    if on:
        glow(ctx, 880, 960, 400, "#22c55e", 0.5)
    ctx.restore()
    hero(ctx, 420, lerp(1680, 1780, k), lerp(1.7, 2.0, k), emo("fear"), t, arms="down", legs=False,
         look=(0.9, 0), tremble=1.0, rim="#22c55e" if on else "#cbd5e1")
    ctx.restore()


def s13_radio(ctx, t, u, D):
    ec = EV["end_card"] - TL.shots[13][0]
    ctx.save()
    if u < ec - 1.2:
        cam(ctx, t, 540, 960, lerp(1.0, 1.25, ease(seg(u, 0, ec))), shake=0.4)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#04140c"), (1, "#020617")])
        glow(ctx, 540, 960, 1000, "#22c55e", 0.25)
        dust(ctx, 9, 1080, 1900, t, 50, "#e2e8f0", 0.3)
        radio_unit(ctx, 540, 960, 1.0, t, 1.0, li=13)
    elif u < ec:
        k = seg(u, ec - 1.2, ec)
        cam(ctx, t, 540, 900, lerp(1.0, 1.2, k), shake=1.0)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#04140c"), (1, "#020617")])
        glow(ctx, 540, 1300, 900, "#22c55e", 0.3)
        hero(ctx, 540, 1700, 2.1, emo("shock"), t, arms="shock", legs=False, tremble=1.4, rim="#22c55e")
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
        text(ctx, "Кто сидел в башне?", 0, 180, 66, "#22c55e")
        ea = seg(u, ec + 0.4, ec + 1.0)
        ctx.translate(0, 470)
        ctx.scale(0.7 * ea + 0.01, 0.7 * ea + 0.01)
        radio_unit(ctx, 0, 0, 0.5, t, 1.0)
    ctx.restore()


SCENES = [s0_wake, s1_cabin, s2_cockpit, s3_shout, s4_answer, s5_hear, s6_commands, s7_landing, s8_applause,
          s9_run, s10_tower, s11_badge, s12_turn, s13_radio]
LABELS = {0: "10 000 М", 1: "10 000 М", 2: "10 000 М", 3: "10 000 М", 4: "18 МИН", 5: "17 МИН", 6: "16 МИН",
          7: "ПОСАДКА", 8: "ПОСЛЕ ПОСАДКИ", 9: "АЭРОПОРТ", 10: "БАШНЯ", 11: "БАШНЯ", 12: "БАШНЯ", 13: "БАШНЯ"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("десять", "тысяч"), "10 000"), (("двести", "сорок"), "240"), (("двести",), "200"),
         (("восемнадцать",), "18")]


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
            radio = TL.lines[li].get("spk") == "R"
            if radio:
                col = "#ffffff" if on else "#4ade80"
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
    hook_end = EV["wake"] + 0.2
    if t < hook_end:  # заголовок-хук
        k1 = back_out(seg(t, 0.0, 0.3))
        out = 1 - seg(t, hook_end - 0.3, hook_end)
        ctx.save()
        ctx.translate(540, 360)
        ctx.scale(k1, k1)
        ctx.push_group()
        text(ctx, "ЧТО, ЕСЛИ", 0, -110, 88, "#ffffff", "#000", 16, shadow=True)
        text(ctx, "ВСЕ УСНУЛИ,", 0, 10, 110, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -330, 90, 660, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "КРОМЕ ТЕБЯ?", 0, 155, 100, "#ffffff")
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
