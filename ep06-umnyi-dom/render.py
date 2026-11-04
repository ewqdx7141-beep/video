"""Серия 6 «Умный дом»: python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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





# ================================================================== УМНЫЙ ДОМ
ROBE = ("#5b7fbf", "#3f5f99")      # халат двойника
RED_ = "#ef4444"
GREEN_ = "#22c55e"


def police(seed, x, y, sc=1.0, d=1):
    p = Npc(random.Random(seed), x, y, sc, d)
    p.shirt, p.pants, p.style, p.item = "#1e3a8a", "#172554", "cap", "none"
    p.glasses, p.headphones, p.earrings = False, False, False
    return p


def landing_bg(ctx, t, lamp=1.0):
    """Лестничная площадка: плитка, двери соседей, щиток, почтовые ящики, растение, коврики."""
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#d6cfc4"), (1, "#b9b0a2")])
    ctx.rectangle(-1200, 1150, 3600, 300)
    fill(ctx, "#4b6b5a")
    line(ctx, -1200, 1150, 2400, 1150, 8, "#3f594b")
    for x, nm in ((-440, "46"), (1220, "48")):
        apartment_door(ctx, x, 1700, 300, 700, nm)
    rr(ctx, 1280, 520, 160, 220, 6)
    fill(ctx, "#6b7280")
    rr(ctx, 1290, 530, 140, 200, 4)
    ctx.set_line_width(3)
    src(ctx, "#4b5563")
    ctx.stroke()
    plant(ctx, -280, 1700, 1.2, t, "#7c2d12")
    ctx.rectangle(-2000, 1700, 5200, 2400)
    fill(ctx, "#8b7d6b")
    for i in range(-16, 30):
        line(ctx, i * 120, 1700, i * 120 - 120, 4000, 3, "#7a6c5a")
    line(ctx, 540, -200, 540, 120, 4, "#111")
    ctx.arc(540, 140, 30, 0, TAU)
    fill(ctx, "#fef9c3" if lamp > 0.5 else "#6b7280")
    if lamp > 0.5:
        glow(ctx, 540, 260, 700, "#fde68a", 0.3)


def my_door(ctx, t, open_k=0.0, inside_fn=None, lock_state=None):
    """Дверь героя с умным замком. lock_state: None/'scan'/'red'/'green'."""
    shadow(ctx, 540, 1700, 420, 30, 0.4)
    rr(ctx, 280, 600, 520, 1100, 6)
    fill(ctx, "#0b0b0d")
    if open_k > 0:
        ctx.save()
        rr(ctx, 290, 610, 500, 1090, 4)
        ctx.clip()
        vgrad(ctx, 290, 610, 500, 1090, [(0, "#fde68a"), (1, "#f59e0b")])
        if inside_fn:
            inside_fn(ctx)
        ctx.restore()
    w = 500 * (1 - 0.85 * open_k)
    rr(ctx, 290, 610, w, 1090, 4)
    lgrad(ctx, 290, 0, 290 + w, 0, [(0, "#3f2a1d"), (0.5, "#5c3d29"), (1, "#3a2619")])
    ctx.fill()
    if open_k < 0.5:
        for k in range(2):
            rr(ctx, 330, 670 + k * 520, 420, 440, 6)
            ctx.set_line_width(5)
            src(ctx, "#2a1a10")
            ctx.stroke()
        text(ctx, "47", 540, 640, 40, "#d4a849")
        # умный замок
        rr(ctx, 650, 1030, 110, 220, 22)
        lgrad(ctx, 650, 0, 760, 0, [(0, "#111827"), (0.5, "#374151"), (1, "#111827")])
        ctx.fill()
        rr(ctx, 665, 1050, 80, 90, 12)
        col = {"scan": "#38bdf8", "red": RED_, "green": GREEN_}.get(lock_state, "#1f2937")
        fill(ctx, col if lock_state else "#020617")
        if lock_state == "scan":
            yy = 1060 + (t * 120) % 70
            line(ctx, 670, yy, 740, yy, 3, "#ffffff")
        if lock_state:
            glow(ctx, 705, 1095, 160, col, 0.5)
        for k in range(9):
            ctx.arc(678 + (k % 3) * 27, 1165 + (k // 3) * 25, 7, 0, TAU)
            fill(ctx, "#4b5563")
        rr(ctx, 690, 1270, 40, 110, 14)
        fill(ctx, "#9ca3af")
    rr(ctx, 360, 1700, 360, 40, 8)
    fill(ctx, "#7c2d12")
    text(ctx, "WELCOME", 540, 1720, 24, "#fcd34d")


def s0_lock(ctx, t, u, D):
    dn = EV["denied"] - TL.shots[0][0]
    state = "scan" if u < dn else ("red" if (t * 3) % 1 < 0.7 else None)
    ctx.save()
    cam(ctx, t, lerp(540, 690, ease(seg(u, dn - 1.0, dn))), lerp(1250, 1120, ease(seg(u, dn - 1.0, dn))),
        lerp(0.95, 1.6, ease(seg(u, dn - 1.2, dn))), shake=0.3 + 0.6 * seg(u, dn, dn + 0.2))
    landing_bg(ctx, t)
    my_door(ctx, t, lock_state=state)
    hero(ctx, 470, 1960, 1.0, emo("neutral") if u < dn else emo("worry", "shock", seg(u, dn, dn + 0.3)), t,
         arms="relax", back=False, look=(0.9, -0.3), rim="#fde68a", rim_a=0.5,
         hand_item=lambda c, x, y: (rr(c, x - 30, y - 10, 60, 40, 8), fill(c, "#7c2d12")))
    ctx.restore()
    if u > dn:
        rr(ctx, 140, 380, 800, 120, 30)
        fill(ctx, RED_, 0.92)
        text(ctx, "ЛИЦО НЕ РАСПОЗНАНО", 540, 440, 58, "#ffffff")


def s1_tries(ctx, t, u, D):
    a, b, c = (x - TL.shots[1][0] for x in EV["sub1"])
    ctx.save()
    cam(ctx, t, 540, 960, 1.0, shake=0.6)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1f2937"), (1, "#0b0f16")])
    if u < b:  # код
        rr(ctx, 290, 360, 500, 900, 60)
        fill(ctx, "#111827")
        rr(ctx, 330, 420, 420, 140, 20)
        fill(ctx, "#020617")
        n = int(seg(u, a - 0.3, a + 0.6) * 4)
        text(ctx, "•" * n + "_" * (4 - n), 540, 490, 80, "#e5e7eb")
        for k in range(12):
            x, y = 380 + (k % 3) * 160, 640 + (k // 3) * 150
            pressed = int(t * 6) % 12 == k and u < a + 0.6
            ctx.arc(x, y, 58, 0, TAU)
            fill(ctx, "#38bdf8" if pressed else "#374151")
            text(ctx, "123456789*0#"[k], x, y, 54, "#ffffff")
        if u > a + 0.6:
            text(ctx, "НЕВЕРНЫЙ КОД", 540, 1380, 70, RED_, "#000", 10)
        hand_x = 380 + (int(t * 6) % 3) * 160
        ctx.arc(hand_x + 20, 1100 + (int(t * 6) // 3 % 3) * 20, 60, 0, TAU)
        fill(ctx, HEAD)
    elif u < c:  # отпечаток
        ctx.arc(540, 820, 300, 0, TAU)
        fill(ctx, "#111827")
        ok = u < b + 0.5
        for r_ in range(30, 260, 26):
            ctx.arc(540, 840, r_, math.pi * 1.1, math.pi * 1.9 + (r_ % 3) * 0.2)
            ctx.set_line_width(9)
            src(ctx, "#38bdf8" if ok else RED_)
            ctx.stroke()
        if not ok:
            text(ctx, "ОТПЕЧАТОК НЕ НАЙДЕН", 540, 1300, 62, RED_, "#000", 10)
        ctx.arc(540, 1240, 130, 0, TAU)
        fill(ctx, HEAD, 0.0)
    else:  # приложение
        def scr(cc, x, y, w, h):
            vgrad(cc, x, y, w, h, [(0, "#0f172a"), (1, "#1e293b")])
            text(cc, "Мой дом", x + w / 2, y + 140, 60, "#ffffff")
            rr(cc, x + 60, y + 260, w - 120, 300, 30)
            fill(cc, "#1f2937")
            text(cc, "Входная дверь", x + w / 2, y + 340, 44, "#cbd5e1")
            text(cc, "ДОСТУП ЗАПРЕЩЁН", x + w / 2, y + 460, 52, RED_)
            rr(cc, x + 60, y + 620, w - 120, 200, 30)
            fill(cc, "#1f2937")
            text(cc, "Владелец: дома", x + w / 2, y + 720, 44, GREEN_)
        hands_phone(ctx, t, scr, tremble=0.8)
    ctx.restore()


def building(ctx, t, lit_mine=1.0, shadow_x=None):
    vgrad(ctx, -1200, -1200, 3600, 4400, [(0, "#020617"), (0.7, "#0f1b3d"), (1, "#1e2b52")])
    stars(ctx, 2, 1080, 900, t, 60)
    ctx.arc(880, 220, 70, 0, TAU)
    fill(ctx, "#f1f5f9")
    # многоэтажка
    rr(ctx, 40, 260, 1000, 1500, 4)
    fill(ctx, "#2b2f3a")
    r = random.Random(5)
    for row in range(9):
        for col in range(5):
            x, y = 90 + col * 190, 320 + row * 150
            mine = (row == 4 and col == 2)
            on = r.random() < 0.18
            rr(ctx, x, y, 130, 100, 4)
            fill(ctx, "#fde68a" if (on or (mine and lit_mine > 0)) else "#111827")
            if mine and lit_mine > 0:
                glow(ctx, x + 65, y + 50, 160, "#fbbf24", 0.6)
                # штора и тень за ней
                rr(ctx, x + 6, y + 6, 118, 88, 3)
                fill(ctx, "#fcd34d", 0.6)
                if shadow_x is not None:
                    sx = x + 30 + shadow_x * 60
                    ctx.arc(sx, y + 34, 14, 0, TAU)
                    fill(ctx, "#78350f", 0.8)
                    rr(ctx, sx - 16, y + 46, 32, 50, 10)
                    fill(ctx, "#78350f", 0.8)
            line(ctx, x, y + 50, x + 130, y + 50, 3, "#2b2f3a")
            rr(ctx, x - 6, y + 100, 142, 10, 2)
            fill(ctx, "#3b404c")
    ctx.rectangle(-1200, 1760, 3600, 800)
    fill(ctx, "#111827")
    for k in range(-4, 10):
        lamp_post(ctx, k * 500, 1900, 500, on=True)
        glow(ctx, k * 500 + 125, 1400 + 20, 220, "#fde68a", 0.25)
    parked_car(ctx, 820, 2000, 0.9, "#6b7280")
    tree(ctx, 120, 1900, 0.9, t, 4)


def s2_window(ctx, t, u, D):
    lt = EV["light"] - TL.shots[2][0]
    sh = EV["shadow"] - TL.shots[2][0]
    k = ease(seg(u, lt, D))
    ctx.save()
    cam(ctx, t, lerp(540, 535, k), lerp(1300, 970, k), lerp(0.75, 2.2, k), shake=0.3)
    building(ctx, t, 1.0, shadow_x=(math.sin(t * 1.2) if u > sh - 0.6 else None))
    ctx.restore()
    if u < lt:
        hero(ctx, 540, 1950, 1.2, emo("worry"), t, arms="relax", back=True, rim="#fde68a", rim_a=0.5)


def intercom(ctx, x, y, s, t, talking):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 0, 300, 260, 30, 0.4)
    rr(ctx, -220, -320, 440, 640, 30)
    lgrad(ctx, -220, 0, 220, 0, [(0, "#1f2937"), (0.5, "#4b5563"), (1, "#1f2937")])
    ctx.fill()
    rr(ctx, -170, -270, 340, 220, 16)
    fill(ctx, "#020617")
    if talking:
        ctx.move_to(-150, -160)
        for k in range(40):
            ctx.line_to(-150 + k * 7.5, -160 + math.sin(k * 0.8 + t * 30) * 50 * abs(math.sin(t * 9 + k * 0.1)))
        ctx.set_line_width(5)
        src(ctx, "#38bdf8")
        ctx.stroke()
    for k in range(6):
        line(ctx, -150, 20 + k * 22, 150, 20 + k * 22, 8, "#111827")
    ctx.arc(0, 230, 46, 0, TAU)
    fill(ctx, "#38bdf8" if talking else "#374151")
    ctx.restore()


def s3_intercom(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(1.0, 1.12, ease(seg(u, 0, D))), shake=0.4)
    landing_bg(ctx, t)
    intercom(ctx, 540, 820, 1.0, t, True)
    hero(ctx, 540, 2300, 1.6, emo("shock"), t, arms="down", back=True, rim="#38bdf8", rim_a=0.6, legs=False)
    ctx.restore()
    rr(ctx, 120, 1250, 840, 220, 30)
    fill(ctx, "#000", 0.75)
    text(ctx, "ХОЗЯИН УЖЕ ДОМА", 540, 1320, 66, "#38bdf8")
    text(ctx, "Отойдите от двери", 540, 1410, 48, "#ffffff", alpha=seg(u, 1.5, 1.8))


def neighbor_peek(ctx, x, y, seed, t, k, d=1, sc=1.0, robe=None):
    p = Npc(random.Random(seed), x, y, sc, d)
    if robe:
        p.shirt = robe
    ctx.save()
    ctx.rectangle(x - 400, -2000, 800, 4000)
    ctx.clip()
    ctx.translate(-d * 120 * (1 - k), 0)
    npc(ctx, p, t, walking=False, stare=0.6)
    ctx.restore()


def s4_neighbors(ctx, t, u, D):
    cl = EV["call"] - TL.shots[4][0]
    ctx.save()
    cam(ctx, t, 540, 1320, lerp(0.55, 0.62, seg(u, 0, D)), shake=0.35)
    landing_bg(ctx, t)
    # соседние двери приоткрыты, выглядывают соседи
    for i, (dx, seed, d, robe) in enumerate(((-440, 21, 1, "#f9a8d4"), (1220, 33, -1, None))):
        k = ease(seg(u, 0.4 + i * 0.6, 1.2 + i * 0.6))
        rr(ctx, dx, 1000, 300, 700, 4)
        fill(ctx, "#fde68a", k)
        rr(ctx, dx + (0 if d > 0 else 300 - 300 * (1 - k * 0.75)), 1000, 300 * (1 - k * 0.75), 700, 4)
        fill(ctx, "#3f2a1d")
        p = Npc(random.Random(seed), dx + 150, 1720, 1.15, d)
        if robe:
            p.shirt = robe
        npc(ctx, p, t, walking=False, stare=0.7, alpha=k)
    my_door(ctx, t, lock_state="red" if (t * 2) % 1 < 0.5 else None)
    # ребёнок из-за перил
    kid = Npc(random.Random(77), 1250, 1720, 0.6, -1)
    npc(ctx, kid, t, walking=False, stare=0.8)
    hero(ctx, 540, 2000, 1.1, emo("worry"), t, arms="phone", rim="#fde68a", rim_a=0.5, look=(0.5, -0.2),
         hand_item=lambda c, x, y: (rr(c, x - 26, y - 100, 52, 96, 8), fill(c, "#111")))
    ctx.restore()
    if u > cl:
        rr(ctx, 290, 360, 500, 140, 40)
        fill(ctx, "#16a34a", 0.95)
        text(ctx, "ЗВОНОК 112", 540, 430, 64, "#ffffff")


def double_inside(t, mug=True, e_name="calm"):
    def f(ctx):
        rr(ctx, 290, 700, 500, 400, 0)
        fill(ctx, "#fcd34d", 0.4)
        hero(ctx, 540, 1700, 1.1, emo(e_name), t, arms=((0.18, 0.05), (0.35, -1.6)), rim="#fde68a", rim_a=0.8,
             hood=ROBE, look=(-0.4, 0),
             hand_item=(lambda c, x, y: coffee_cup(c, x - 10, y + 40, 0.28, t)) if mug else None)
    return f


def s5_door(ctx, t, u, D):
    do = EV["door_open"] - TL.shots[5][0]
    yo = EV["you"] - TL.shots[5][0]
    op = ease(seg(u, do, do + 1.0))
    ctx.save()
    cam(ctx, t, 540, lerp(1250, 1150, ease(seg(u, yo, D))), lerp(0.8, 1.35, ease(seg(u, yo - 0.3, D))),
        shake=0.35)
    landing_bg(ctx, t)
    my_door(ctx, t, op, double_inside(t), lock_state="green" if op > 0 else None)
    for i, x in enumerate((-80, 1160)):  # полицейские по бокам
        p = police(41 + i, x, 1900, 1.15, 1 if i == 0 else -1)
        npc(ctx, p, t, walking=False)
        rr(ctx, x + (10 if i == 0 else -50), 1420, 40, 26, 4)
        fill(ctx, "#facc15")
    # мигалки отражаются на стене
    blink_ = (t * 3) % 1 < 0.5
    ctx.rectangle(-1200, -800, 3600, 3600)
    fill(ctx, "#ef4444" if blink_ else "#3b82f6", 0.06)
    hero(ctx, 300, 2200, 1.25, emo("worry", "shock", seg(u, yo, yo + 0.3)), t, arms="down", back=True,
         rim="#fde68a", rim_a=0.5, legs=False)
    ctx.restore()


def passport(ctx, x, y, s, t, photo=True, label="ПАСПОРТ"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    shadow(ctx, 10, 20, 260, 340, 0.45)
    rr(ctx, -230, -320, 460, 640, 20)
    fill(ctx, "#7f1d1d")
    rr(ctx, -210, -300, 420, 600, 14)
    fill(ctx, "#fdf6e3")
    for k in range(12):
        line(ctx, -200, -280 + k * 50, 200, -260 + k * 50, 2, "#e7d8b8")
    text(ctx, label, 0, -250, 36, "#7f1d1d")
    rr(ctx, -170, -200, 170, 220, 6)
    fill(ctx, "#e5e7eb")
    if photo:
        ctx.save()
        rr(ctx, -170, -200, 170, 220, 6)
        ctx.clip()
        hero_head(ctx, -85, -90, 70, emo("calm"), t, rim_a=0.0)
        rr(ctx, -150, -20, 130, 60, 20)
        fill(ctx, ROBE[0])
        ctx.restore()
    else:
        ctx.set_dash([12, 10])
        rr(ctx, -170, -200, 170, 220, 6)
        ctx.set_line_width(4)
        src(ctx, "#9ca3af")
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, "?", -85, -90, 120, "#9ca3af")
    for k in range(5):
        line(ctx, 30, -170 + k * 40, 180, -170 + k * 40, 6, "#334155", 0.7)
    ctx.arc(110, 170, 70, 0, TAU)
    ctx.set_line_width(6)
    src(ctx, "#1d4ed8", 0.6)
    ctx.stroke()
    text(ctx, "МВД", 110, 170, 30, "#1d4ed8", alpha=0.6)
    ctx.restore()


def s6_docs(ctx, t, u, D):
    ok = EV["fake_ok"] - TL.shots[6][0]
    em = EV["empty"] - TL.shots[6][0]
    ctx.save()
    cam(ctx, t, lerp(500, 580, ease(seg(u, em - 0.6, em))), 960, lerp(0.95, 1.02, seg(u, 0, D)), shake=0.35)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1f2937"), (1, "#0b0f16")])
    passport(ctx, 300, 980, 0.95, t, True, "ПАСПОРТ")
    passport(ctx, 790, 1000, 0.95, t, False, "ПАСПОРТ")
    # луч фонарика
    fx = lerp(300, 790, ease(seg(u, em - 0.6, em)))
    g = cairo.RadialGradient(fx, 960, 60, fx, 960, 420)
    g.add_color_stop_rgba(0, 1, 1, 0.85, 0.25)
    g.add_color_stop_rgba(1, 1, 1, 0.85, 0)
    ctx.set_source(g)
    ctx.arc(fx, 960, 420, 0, TAU)
    ctx.fill()
    ctx.restore()
    if u > ok:
        text(ctx, "НАСТОЯЩИЙ", 300, 380, 60, GREEN_, "#000", 10, alpha=seg(u, ok, ok + 0.2))
    if u > em:
        text(ctx, "НЕТ ФОТО", 790, 380, 60, RED_, "#000", 10, alpha=seg(u, em, em + 0.2))


def s7_neighbor(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 420, 1260, lerp(1.35, 1.5, seg(u, 0, D)), shake=0.3)
    landing_bg(ctx, t)
    my_door(ctx, t, 1.0, double_inside(t), lock_state="green")
    lady = Npc(random.Random(21), 160, 1950, 1.25, 1)
    lady.shirt, lady.style, lady.hair, lady.glasses = "#f9a8d4", "bun", "#9a9a9a", True
    npc(ctx, lady, t, walking=False)
    # шёпот: рука у рта
    ctx.arc(250, 1470, 20, 0, TAU)
    fill(ctx, lady.skin)
    ctx.restore()
    for k in range(3):
        a = seg(u, 0.3 + k * 0.2, 0.6 + k * 0.2)
        ctx.arc(330 + k * 50, 520 - k * 30, 14 + k * 6, 0, TAU)
        fill(ctx, "#ffffff", 0.7 * a)


def s8_again(ctx, t, u, D):
    ag = EV["again"] - TL.shots[8][0]
    ctx.save()
    cam(ctx, t, 540, 900, lerp(1.0, 1.25, ease(seg(u, 0, D))), shake=0.25)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#fde68a"), (1, "#b45309")])
    rr(ctx, -200, -400, 400, 3000, 0)
    fill(ctx, "#78350f", 0.4)
    hero(ctx, 540, 1750, 1.9, emo("calm") if u < ag else emo("sly"), t, arms=((0.18, 0.05), (0.35, -1.6)),
         legs=False, hood=ROBE, rim="#fde68a", rim_a=0.9, look=(0.4, 0),
         hand_item=lambda c, x, y: coffee_cup(c, x - 10, y + 40, 0.4, t))
    ctx.restore()


def s9_third(ctx, t, u, D):
    nd = EV["nod"] - TL.shots[9][0]
    ec = EV["end_card"] - TL.shots[9][0]
    ctx.save()
    if u < ec:
        nod = math.sin(seg(u, nd, nd + 0.8) * math.pi * 2) * 0.12
        cam(ctx, t, 540, 1200, lerp(1.2, 1.35, seg(u, 0, ec)), shake=0.3)
        landing_bg(ctx, t, lamp=1.0 if u < ec - 0.8 else (1.0 if random.Random(int(t * 12)).random() > 0.4 else 0.0))
        my_door(ctx, t, 1.0, double_inside(t, e_name="sly"), lock_state="green")
        p = police(41, 640, 2150, 1.9, -1)
        ctx.save()
        ctx.translate(640, 2150 - 370 * 1.9)
        ctx.rotate(nod)
        ctx.translate(-640, -(2150 - 370 * 1.9))
        npc(ctx, p, t, walking=False)
        ctx.restore()
        rr(ctx, 470, 1560, 90, 56, 8)
        fill(ctx, "#facc15")
        text(ctx, "112", 515, 1588, 28, "#1e3a8a")
        ctx.restore()
        ctx.save()
        if u > nd + 0.8:
            text(ctx, "ТРЕТИЙ ЗА НЕДЕЛЮ", 540, 520, 84, "#ffffff", RED_, 14, alpha=seg(u, nd + 0.8, nd + 1.0))
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
        text(ctx, "Где первые двое?", 0, 180, 70, "#38bdf8")
    ctx.restore()


SCENES = [s0_lock, s1_tries, s2_window, s3_intercom, s4_neighbors, s5_door, s6_docs, s7_neighbor, s8_again,
          s9_third]
LABELS = {0: "02:00", 1: "02:01", 2: "02:03", 3: "02:04", 4: "02:05", 5: "02:15", 6: "02:17", 7: "02:18",
          8: "02:19", 9: "02:19"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("два", "часа"), "2:00"), (("десять",), "10"), (("пять",), "5")]


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
    hook_end = EV["denied"] - 0.2
    if t < hook_end:  # заголовок-хук
        k1 = back_out(seg(t, 0.0, 0.3))
        out = 1 - seg(t, hook_end - 0.3, hook_end)
        ctx.save()
        ctx.translate(540, 360)
        ctx.scale(k1, k1)
        ctx.push_group()
        text(ctx, "ЧТО, ЕСЛИ", 0, -110, 88, "#ffffff", "#000", 16, shadow=True)
        text(ctx, "ТВОЙ ДОМ", 0, 10, 116, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -380, 90, 760, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "ТЕБЯ НЕ УЗНАЛ?", 0, 155, 92, "#ffffff")
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
