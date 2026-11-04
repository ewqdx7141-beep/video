"""Серия 5 «Последний поезд»: python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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




# ================================================================== МЕТРО
LIVE = "#ef4444"


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


def lights_at(t):
    f = EV["flicker"]
    if t < f:
        return 1.0
    u = t - f
    if u < 1.0:
        return 0.2 if int(u * 16) % 3 == 0 else 1.0
    return 0.85


def stare_order_main(i):
    """Все поднимают головы почти одновременно (разброс 0.25 с)."""
    return EV["lookup"] + ((i * 37) % 9) * 0.03


# ================================================================== СЦЕНЫ
def s0_train(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(400, 700, ease(seg(u, 0, D))), 1380, lerp(1.25, 1.35, seg(u, 0, D)), shake=0.35)
    metro_car(ctx, t, lights=1.0)
    hero(ctx, 260, 2000, 1.15, emo("neutral"), t, arms="relax", back=True, rim="#93c5fd", rim_a=0.5)
    ctx.restore()


def s1_skip(ctx, t, u, D):
    p1, p2 = EV["pass1"], EV["pass2"]
    pl = max(1 - abs(t - p1 - 0.6) / 0.8, 1 - abs(t - p2 - 0.4) / 0.7, 0)
    ctx.save()
    cam(ctx, t, 700, 1250, lerp(1.25, 1.35, seg(u, 0, D)), shake=0.6 + 0.6 * pl)
    metro_car(ctx, t, lights=lights_at(t), platform=pl)
    hero(ctx, 300, 1950, 1.15, emo("worry"), t, arms="relax", look=(0.8, -0.3), rim="#93c5fd", rim_a=0.6)
    ctx.restore()
    if pl > 0.2:
        text(ctx, "СТАНЦИЯ ПРОЕХАЛИ", 540, 300, 56, "#ffffff", "#000", 10, alpha=pl)


def s2_lookup(ctx, t, u, D):
    lu = EV["lookup"]
    sn = seg(t, EV["stare"] - 0.05, EV["stare"] + 0.15)
    ctx.save()
    cam(ctx, t, 760, 1380, lerp(1.3, 1.45, ease(seg(t, lu, D + TL.shots[2][0]))) + 0.25 * ease_out(sn),
        shake=0.3 + 0.8 * sn)
    metro_car(ctx, t, lights=0.85, stare_order=stare_order_main)
    ctx.restore()


def s3_faces(ctx, t, u, D):
    tb = EV["baby"] - TL.shots[3][0]
    ctx.save()
    if u < tb:
        cam(ctx, t, lerp(300, 700, ease(seg(u, 0, tb))), 1260, 2.0, shake=0.25)
    else:
        cam(ctx, t, 400 + 30 * 0, 1320, lerp(2.4, 2.7, seg(u, tb, D)), shake=0.2)
    metro_car(ctx, t, lights=0.85, stare_order=lambda i: -10)
    ctx.restore()


def s4_doors(ctx, t, u, D):
    td = EV["doors"] - TL.shots[4][0]
    tt = EV["turn"]
    op = ease(seg(u, td, td + 0.8))
    ctx.save()
    cam(ctx, t, 540, 1050, lerp(0.9, 1.15, ease(seg(u, td, D))), shake=0.3)
    # соседний вагон за дверью
    ctx.save()
    ctx.translate(540, 1050)
    ctx.scale(0.75, 0.75)
    ctx.translate(-540, -1050)
    metro_car(ctx, t, lights=0.85, seed=9, stare_order=lambda i: tt + (i % 7) * 0.22)
    ctx.restore()
    # межвагонная дверь
    ctx.rectangle(-1200, -800, 3600, 3600)
    rr(ctx, 290, 260, 500, 1560, 20)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill(ctx, "#94a3b8")
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    for side in (-1, 1):
        x0 = 290 if side < 0 else 540
        dx = side * 250 * op
        rr(ctx, x0 + dx, 260, 250, 1560, 10)
        lgrad(ctx, x0 + dx, 0, x0 + dx + 250, 0, [(0, "#9ca3af"), (0.5, "#d1d5db"), (1, "#9ca3af")])
        ctx.fill()
        rr(ctx, x0 + dx + 40, 420, 170, 400, 14)
        fill(ctx, "#1f2937", 0.6)
    hero(ctx, 540, 2150, 1.4, emo("worry"), t, arms="relax", back=True, rim="#93c5fd", rim_a=0.6)
    ctx.restore()


def live_screen(t, notif=0.0, viewers=0):
    def f(c, x, y, w, h):
        vgrad(c, x, y, w, h, [(0, "#111827"), (1, "#020617")])
        text(c, "НЕТ СЕТИ", x + 40, y + 70, 30, "#94a3b8", align="left")
        text(c, "23:58", x + w / 2, y + h * 0.22, w * 0.22, "#ffffff")
        if notif > 0:
            s = max(0.02, back_out(notif))
            c.save()
            c.translate(x + w / 2, y + h * 0.45)
            c.scale(s, s)
            rr(c, -w * 0.44, -h * 0.09, w * 0.88, h * 0.18, 30)
            fill(c, "#ffffff", 0.95)
            c.arc(-w * 0.33, 0, 34, 0, TAU)
            fill(c, LIVE)
            text(c, "LIVE", -w * 0.33, 0, 22, "#ffffff")
            text(c, "Вы в прямом эфире", -w * 0.22, -h * 0.03, w * 0.055, "#111", align="left")
            text(c, f"Зрителей: {viewers}", -w * 0.22, h * 0.035, w * 0.05, "#dc2626", align="left")
            c.restore()
    return f


def s5_live(ctx, t, u, D):
    n = seg(t, EV["notif"] - 0.2, EV["notif"] + 0.2)
    v = int(lerp(1, 243, ease(seg(t, EV["viewers"] - 0.4, EV["viewers"] + 1.2))))
    ctx.save()
    cam(ctx, t, 540, 900, lerp(1.1, 1.3, ease(seg(u, 0, D))), shake=0.5)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0b1120"), (1, "#020617")])
    hands_phone(ctx, t, live_screen(t, n, v), tremble=0.9)
    ctx.restore()


def s6_screens(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, lerp(200, 1100, ease(seg(u, 0, D))), 1240, 1.6, shake=0.3)
    metro_car(ctx, t, lights=0.85, stare_order=lambda i: -10, phones_live=1.0 if (t * 2) % 1 < 0.7 else 0.4)
    ctx.restore()


def s7_turn(ctx, t, u, D):
    k = ease(seg(u, 0.2, D - 0.2))
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(1.0, 1.3, k), shake=0.4)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#94a3b8"), (1, "#475569")])
    ctx.rectangle(-800, -800, 2700, 3600)
    fill(ctx, "#020617", 0.45)
    a = ease(seg(k, 0.35, 0.65))
    for back_, al in ((True, 1 - a), (False, a)):
        if al <= 0:
            continue
        ctx.push_group()
        ctx.save()
        ctx.translate(540, 1750)
        ctx.rotate(lerp(-0.08, 0.08, k))
        ctx.translate(-540, -1750)
        hero(ctx, 540, 1750, 1.9, emo("fear"), t, arms="down", legs=False, back=back_, rim="#93c5fd",
             look=(lerp(-0.9, 0, a), 0), tremble=0.6)
        ctx.restore()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(al)
    ctx.restore()


def s8_phone(ctx, t, u, D):
    tp = EV["phone_found"] - TL.shots[8][0]
    tc = EV["chat"]
    ctx.save()
    cam(ctx, t, lerp(540, 700, ease(seg(u, 0, D))), lerp(1250, 1300, seg(u, 0, D)), lerp(1.0, 2.1, ease(seg(u, tp - 0.3, D))),
        shake=0.3)
    metro_car(ctx, t, lights=0.75, empty=True)
    # телефон на сиденье, снимает
    ctx.save()
    ctx.translate(700, 1300)
    ctx.rotate(-0.12)
    rr(ctx, -80, -150, 160, 300, 18)
    fill(ctx, "#111")
    rr(ctx, -72, -140, 144, 280, 12)
    fill(ctx, "#0f172a")
    ctx.save()
    rr(ctx, -72, -140, 144, 280, 12)
    ctx.clip()
    hero(ctx, 0, 150, 0.35, emo("fear"), t, legs=False, rim_a=0.0)
    for j in range(5):  # чат
        a = seg(t, tc + j * 0.25, tc + j * 0.25 + 0.2)
        if a > 0:
            rr(ctx, -66, -40 + j * 34, 132, 28, 8)
            fill(ctx, "#000", 0.55 * a)
            text(ctx, ["он заметил", "ОН ЗАМЕТИЛ", "наконец-то", "!!!", "оборачивается"][j], -60, -26 + j * 34, 16,
                 "#ffffff", align="left", alpha=a)
    ctx.restore()
    ctx.arc(56, -124, 7, 0, TAU)
    fill(ctx, LIVE, 0.5 + 0.5 * math.sin(t * 6))
    ctx.restore()
    ctx.restore()


def ghost_station(ctx, t, sign_k=0.0):
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#1c1917"), (1, "#0c0a09")])
    for i in range(-10, 20):  # старая плитка
        for j in range(-4, 16):
            rr(ctx, i * 120 + (j % 2) * 60, j * 90, 112, 82, 6)
            fill(ctx, "#2b2622" if (i + j) % 3 else "#332d28")
    for k in range(-2, 6):  # колонны
        rr(ctx, k * 480, -800, 120, 3000, 10)
        lgrad(ctx, k * 480, 0, k * 480 + 120, 0, [(0, "#1c1917"), (0.5, "#44403c"), (1, "#1c1917")])
        ctx.fill()
    for k in range(-2, 5):  # лампы
        on = random.Random(int(t * 10) + k).random() > 0.2
        ctx.arc(k * 480 + 300, 200, 22, 0, TAU)
        fill(ctx, "#fef3c7" if on else "#44403c")
        if on:
            glow(ctx, k * 480 + 300, 260, 360, "#fde68a", 0.3)
    ctx.rectangle(-1200, 1500, 3600, 900)
    fill(ctx, "#1c1917")
    line(ctx, -1200, 1500, 2400, 1500, 14, "#ca8a04")
    for k in range(6):  # туман
        ell(ctx, (k * 400 + t * 40) % 2400 - 600, 1450, 420, 80)
        fill(ctx, "#a8a29e", 0.08)
    # табличка
    rr(ctx, 140, 640, 800, 300, 16)
    fill(ctx, "#1e3a8a")
    rr(ctx, 160, 660, 760, 260, 10)
    ctx.set_line_width(5)
    src(ctx, "#f8fafc")
    ctx.stroke()
    text(ctx, "СТАНЦИЯ", 540, 720, 54, "#f8fafc")
    if sign_k < 1:
        r = random.Random(int(t * 12))
        junk = "".join(r.choice("АБВГДЕЖЗИКЛМНОПРСТУФЫЭЮЯ") for _ in range(6))
        text(ctx, junk, 540, 830, 96, "#f8fafc", alpha=1 - sign_k)
    if sign_k > 0:
        ctx.save()
        ctx.translate(540, 830)
        ctx.scale(max(0.02, sign_k), max(0.02, sign_k))
        text(ctx, "« ТЫ »", 0, 0, 110, "#facc15")
        ctx.restore()


def s9_brake(ctx, t, u, D):
    tb = EV["brake"] - TL.shots[9][0]
    to = EV["doors2"] - TL.shots[9][0]
    br = ease(seg(u, tb, tb + 0.5)) * (1 - ease(seg(u, tb + 0.6, tb + 1.2)))
    ctx.save()
    if u < to:
        cam(ctx, t, 600, 1100, 1.0, rot=0.04 * br, shake=0.4 + 2.0 * br)
        metro_car(ctx, t, lights=lights_at(t), stare_order=lambda i: -10, brake=br)
    else:
        op = ease(seg(u, to, to + 0.8))
        cam(ctx, t, 540, 1050, lerp(0.9, 1.05, seg(u, to, D)), shake=0.3)
        ghost_station(ctx, t, 0.0)
        ctx.rectangle(-1200, -800, 3600, 3600)
        rr(ctx, 290 - 250 * op, 260, 500 + 500 * op, 1560, 20)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        fill(ctx, "#94a3b8")
        ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        hero(ctx, 540, 2150, 1.4, emo("fear"), t, arms="relax", back=True, rim="#fde68a", rim_a=0.6)
    ctx.restore()


def s10_sign(ctx, t, u, D):
    nm = EV["name"]
    ec = EV["end_card"] - TL.shots[10][0]
    ctx.save()
    if u < ec:
        sk = ease(seg(t, nm - 0.2, nm + 0.4))
        cam(ctx, t, 540, 800, lerp(1.0, 1.25, ease(seg(u, 0, ec))), shake=0.4 + 0.6 * seg(t, nm, nm + 0.2))
        ghost_station(ctx, t, sk)
        # пассажиры встают и выходят за спиной героя
        for i in range(5):
            p = Npc(random.Random(i * 13 + 3), 100 + i * 220, 2050, 1.1, -1 if i > 2 else 1)
            npc(ctx, p, t, walking=False, stare=1.0, alpha=seg(u, 1.0 + i * 0.2, 1.6 + i * 0.2))
        hero(ctx, 540, 2150, 1.4, emo("fear"), t, arms="relax", back=True, rim="#fde68a", rim_a=0.6)
        ctx.rectangle(-800, -800, 2700, 3600)
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
        text(ctx, "Что на этой станции?", 0, 180, 64, "#facc15")
    ctx.restore()


SCENES = [s0_train, s1_skip, s2_lookup, s3_faces, s4_doors, s5_live, s6_screens, s7_turn, s8_phone, s9_brake,
          s10_sign]
LABELS = {0: "23:56", 1: "23:57", 2: "23:57", 3: "23:57", 4: "23:58", 5: "23:58", 6: "23:58", 7: "23:59",
          8: "23:59", 9: "00:00", 10: "00:00"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("двести", "сорок", "три"), "243")]


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
    hook_end = TL.lines[0]["start"] + TL.lines[0]["speech"] + 0.3
    if t < hook_end:  # заголовок-хук
        k1 = back_out(seg(t, 0.0, 0.3))
        out = 1 - seg(t, hook_end - 0.3, hook_end)
        ctx.save()
        ctx.translate(540, 360)
        ctx.scale(k1, k1)
        ctx.push_group()
        text(ctx, "ЧТО, ЕСЛИ ВЕСЬ", 0, -110, 84, "#ffffff", "#000", 16, shadow=True)
        text(ctx, "ВАГОН МЕТРО", 0, 10, 112, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -400, 90, 800, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "СМОТРИТ НА ТЕБЯ?", 0, 155, 84, "#ffffff")
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
