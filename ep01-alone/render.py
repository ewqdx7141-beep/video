"""Рендер видеоряда: python3 render.py [--stills 1.0,5.2,...] [--jobs 4]

Каждый кадр рисуется кодом (Cairo) и отправляется в ffmpeg. Сцены = фразы озвучки (common.Timeline).
"""
import argparse
import math
import os
import random
import subprocess
import sys
from multiprocessing import Pool

import cairo

from common import FPS, H, ROOT, TRANS, W, Timeline
from draw import *  # noqa: F401,F403
from props import *  # noqa: F401,F403

TL = Timeline()
EV = TL.ev


def L(i):  # абсолютное время начала строки
    return TL.lines[i]["start"]


def wl(i, word, n=0, end=False):  # время слова относительно начала шота i
    return TL.wt(i, word, n, end) - TL.shots[i][0]


def cam(ctx, t, cx, cy, z, rot=0.0, shake=0.4):
    ctx.translate(W / 2 + nz(t * 1.3, 1) * 14 * shake, H / 2 + nz(t * 1.1, 2) * 14 * shake)
    ctx.rotate(rot + nz(t * 0.9, 3) * 0.008 * shake)
    ctx.scale(z, z)
    ctx.translate(-cx, -cy)


def blink_at(t, seed=0.0, every=3.1):
    ph = (t + seed) % every
    return clamp(1 - abs(ph - 0.08) / 0.08) if ph < 0.16 else 0.0


def xmark(ctx, x, y, s, k):
    if k <= 0:
        return
    a = ease_out(k)
    line(ctx, x - 70 * s, y - 70 * s, x - 70 * s + 140 * s * a, y - 70 * s + 140 * s * a, 22 * s, "#ef2b2b")
    k2 = seg(k, 0.4, 1)
    if k2 > 0:
        b = ease_out(k2)
        line(ctx, x + 70 * s, y - 70 * s, x + 70 * s - 140 * s * b, y - 70 * s + 140 * s * b, 22 * s, "#ef2b2b")


def bubble_icon(ctx, x, y, s, k, kind):
    """Иконка в белом круге с красным крестом (машина / голос / птица / сеть / wifi)."""
    if k <= 0:
        return
    sc = back_out(seg(k, 0, 0.35)) * s
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    ctx.arc(0, 0, 95, 0, TAU)
    fill(ctx, "#ffffff")
    ctx.arc(0, 0, 95, 0, TAU)
    ctx.set_line_width(10)
    src(ctx, "#111")
    ctx.stroke()
    c = "#1b1b1b"
    if kind == "car":
        rr(ctx, -60, -10, 120, 40, 14)
        fill(ctx, c)
        rr(ctx, -36, -40, 72, 40, 14)
        fill(ctx, c)
        for px in (-34, 34):
            ctx.arc(px, 32, 15, 0, TAU)
            fill(ctx, c)
    elif kind == "voice":
        rr(ctx, -55, -45, 110, 70, 24)
        fill(ctx, c)
        ctx.move_to(-20, 20)
        ctx.line_to(-40, 50)
        ctx.line_to(5, 22)
        fill(ctx, c)
    elif kind == "bird":
        ctx.move_to(-60, -5)
        ctx.curve_to(-30, -45, -10, -20, 0, 0)
        ctx.curve_to(10, -20, 30, -45, 60, -5)
        ctx.set_line_width(14)
        src(ctx, c)
        ctx.stroke()
    elif kind == "net":
        for i in range(4):
            rr(ctx, -55 + i * 30, 35 - i * 25, 20, 25 + i * 25, 4)
            fill(ctx, c)
    elif kind == "wifi":
        for i, r in enumerate((20, 45, 70)):
            ctx.arc(0, 35, r, TAU * 0.62, TAU * 0.88)
            ctx.set_line_width(13)
            src(ctx, c)
            ctx.stroke()
        ctx.arc(0, 35, 8, 0, TAU)
        fill(ctx, c)
    ctx.restore()
    xmark(ctx, x, y, s * 0.8, seg(k, 0.25, 0.6))


# ======================================================================= СЦЕНЫ
def s0_bedroom(ctx, t, u, D):
    wake = 0.75
    sit = ease_out(seg(u, wake, wake + 0.45), 3)
    boom = wl(0, "тишина")
    sn = seg(u, boom - 0.05, boom + 0.12)
    z = lerp(0.92, 1.18, ease(seg(u, 0, boom))) + 0.35 * ease_out(sn) - 0.12 * ease(seg(u, boom + 0.2, D))
    cy = lerp(1150, 1080, ease(seg(u, 0, boom)))
    ctx.save()
    cam(ctx, t, 540, cy, z, shake=0.5 + 0.6 * sn)
    # стена
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#e8c79c"), (1, "#c99a6c")])
    # окно
    ctx.save()
    rr(ctx, 120, 200, 840, 860, 16)
    ctx.clip()
    sky(ctx, 1080, 1060, "morning")
    ctx.translate(0, 0)
    skyline(ctx, 3, 100, 980, 1060, 220, 520, "#9db4c8", "#cfdde8", 0.5)
    skyline(ctx, 4, 60, 1000, 1060, 120, 330, "#7f97ad", "#b4c6d4", 0.35, wmin=120, wmax=220)
    # солнце-блик
    glow(ctx, 820, 330, 260, "#fff2c6", 0.8)
    ctx.restore()
    # рама
    for x0 in (120, 535, 950):
        ctx.rectangle(x0 - 10, 200, 20, 860)
        fill(ctx, "#fbf7f0")
    for y0 in (200, 620, 1050):
        ctx.rectangle(110, y0 - 10, 860, 20)
        fill(ctx, "#fbf7f0")
    # подоконник: кактус, цветок, кружка-копилка, шторы
    rr(ctx, 90, 1050, 900, 34, 6)
    fill(ctx, "#f3eee6")
    shadow(ctx, 540, 1090, 460, 14, 0.25)
    plant(ctx, 250, 1052, 0.55, t, "#2563eb")
    ctx.save()
    ctx.translate(760, 1052)
    rr(ctx, -34, -60, 68, 60, 8)
    fill(ctx, "#e76f51")
    rr(ctx, -20, -150, 40, 100, 20)
    fill(ctx, "#4d7c0f")
    for k in range(5):
        line(ctx, -20, -130 + k * 18, -28, -134 + k * 18, 3, "#fef9c3")
        line(ctx, 20, -126 + k * 18, 28, -130 + k * 18, 3, "#fef9c3")
    ctx.arc(0, -150, 12, 0, TAU)
    fill(ctx, "#f472b6")
    ctx.restore()
    rr(ctx, 560, 990, 60, 62, 10)
    fill(ctx, "#fde68a")
    curtain(ctx, 40, 190, 230, 900, "#c2410c", t, 1)
    curtain(ctx, 810, 190, 230, 900, "#c2410c", t, -1)
    # солнечный луч на стене
    ctx.move_to(150, 1060)
    ctx.line_to(950, 1060)
    ctx.line_to(1250, 2100)
    ctx.line_to(-50, 2100)
    ctx.close_path()
    fill(ctx, "#fff3d0", 0.12)
    # тумбочка + будильник
    rr(ctx, 840, 1330, 230, 300, 12)
    lgrad(ctx, 840, 0, 1070, 0, [(0, "#6f4528"), (0.5, "#94623f"), (1, "#6f4528")])
    ctx.fill()
    for k in range(2):
        rr(ctx, 860, 1360 + k * 130, 190, 110, 8)
        ctx.set_line_width(4)
        src(ctx, "#5a3820")
        ctx.stroke()
        ctx.arc(955, 1415 + k * 130, 9, 0, TAU)
        fill(ctx, "#d4a849")
    glass_water(ctx, 1050, 1332, 0.8)
    rr(ctx, 880, 1240, 150, 92, 22)
    fill(ctx, "#222")
    text(ctx, "07:00", 955, 1286, 46, "#ff4d4d")
    # кровать
    rr(ctx, 40, 1180, 760, 210, 40)
    fill(ctx, "#6f4a33")
    for k in range(6):  # резьба изголовья
        rr(ctx, 80 + k * 120, 1210, 80, 140, 20)
        fill(ctx, "#5e3d29")
    rr(ctx, 90, 1300, 300, 120, 50)
    lgrad(ctx, 0, 1300, 0, 1420, [(0, "#ffffff"), (1, "#d6d0c4")])
    ctx.fill()
    for k in range(4):
        line(ctx, 130 + k * 70, 1310, 130 + k * 70, 1410, 6, "#a5b4fc", 0.5)
    # герой: лежит -> рывком садится
    e = emo("sleep") if u < wake else emo("worry", "shock", seg(u, boom - 0.1, boom + 0.1))
    look = (0.5, -0.7) if u < boom else (0, 0)
    ang = lerp(-1.42, 0, sit)
    ctx.save()
    ctx.translate(420, 1470)
    ctx.rotate(ang)
    hero(ctx, 0, 0, 0.95, e, t, arms=arms_lerp("down", "shock", seg(u, boom, boom + 0.25)),
         look=look, blink=blink_at(u, 0.7) if u > wake + 0.3 else 0, legs=False,
         tremble=0.6 if u > boom else 0, rim_a=0.6)
    ctx.restore()
    # одеяло
    ctx.move_to(0, 1460)
    ctx.curve_to(250, 1400 - 30 * (1 - sit), 600, 1420, 860, 1450)
    ctx.line_to(860, 2200)
    ctx.line_to(0, 2200)
    ctx.close_path()
    fill(ctx, "#3456c4")
    for i in range(7):  # клетка на одеяле
        line(ctx, 40 + i * 130, 1500, 90 + i * 130, 2100, 12, "#2a46a8")
    for j in range(5):
        line(ctx, 0, 1560 + j * 110, 860, 1580 + j * 110, 10, "#5b7be0", 0.55)
    ctx.move_to(0, 1460)
    ctx.curve_to(250, 1400 - 30 * (1 - sit), 600, 1420, 860, 1450)
    ctx.set_line_width(26)
    src(ctx, "#f4f1ea")
    ctx.stroke()
    ctx.restore()
    # Ни машин, ни голосов, ни птиц
    for k, (w, kind) in enumerate((("машин", "car"), ("голосов", "voice"), ("птиц", "bird"))):
        tk = wl(0, w)
        bubble_icon(ctx, 230 + k * 310, 560 + (k % 2) * 60, 1.0, seg(u, tk - 0.05, tk + 0.6), kind)


def s1_street(ctx, t, u, D):
    tb = wl(1, "автобус")
    camx = lerp(420, 1380, ease(seg(u, 0.3, tb + 0.6)))
    z = lerp(0.78, 0.92, ease(seg(u, tb, D)))
    cy = lerp(1080, 1180, ease(seg(u, tb, D)))
    ctx.save()
    cam(ctx, t, camx, cy, z, shake=0.45)
    sky(ctx, 1080, 1250, "day")
    ctx.save()
    ctx.translate(camx * 0.65, 0)  # параллакс дальнего плана
    skyline(ctx, 11, -1400, 2200, 1100, 300, 700, "#a9c7e0", None)
    ctx.restore()
    ctx.save()
    ctx.translate(camx * 0.3, 0)
    skyline(ctx, 12, -1200, 2600, 1150, 250, 520, "#7d9bb8", "#a9c2d8", 0.4, wmin=150, wmax=260)
    ctx.restore()
    # ближние дома-магазины
    r = random.Random(5)
    x = -900
    cols = ["#e9a46b", "#d9d2c4", "#b6c8a8", "#e6c86e", "#c9a0a0"]
    while x < 3200:
        w = r.uniform(420, 620)
        h = r.uniform(600, 820)
        ctx.rectangle(x, 1250 - h, w, h)
        fill(ctx, r.choice(cols))
        rr(ctx, x + 40, 1250 - 330, w - 80, 250, 10)
        fill(ctx, "#33465c")
        # витрина: полки с товаром и блик
        for sh in range(3):
            line(ctx, x + 50, 1250 - 270 + sh * 70, x + w - 50, 1250 - 270 + sh * 70, 5, "#1f2d3d")
            for it in range(int((w - 120) / 40)):
                rr(ctx, x + 60 + it * 40, 1250 - 300 + sh * 70, 26, 30, 4)
                fill(ctx, r.choice(["#f87171", "#fbbf24", "#60a5fa", "#34d399", "#f9fafb"]))
        ctx.move_to(x + 60, 1250 - 80)
        ctx.line_to(x + 160, 1250 - 330)
        ctx.line_to(x + 220, 1250 - 330)
        ctx.line_to(x + 120, 1250 - 80)
        fill(ctx, "#ffffff", 0.12)
        sc_ = r.choice(["#d8332a", "#2f6fdb", "#1f9d61"])
        rr(ctx, x + 30, 1250 - 400, w - 60, 60, 8)
        fill(ctx, sc_)
        text(ctx, r.choice(["ПРОДУКТЫ", "АПТЕКА", "КАФЕ", "ЦВЕТЫ", "ПЕКАРНЯ", "ОПТИКА"]), x + w / 2, 1250 - 370, 38, "#ffffff")
        awning(ctx, x + 30, 1250 - 340, w - 60, 46, sc_)
        # водосток и кондиционер на фасаде
        rr(ctx, x + w - 22, 1250 - h, 12, h, 4)
        fill(ctx, "#9ca3af", 0.7)
        rr(ctx, x + 40, 1250 - h + 210, 90, 60, 6)
        fill(ctx, "#e5e7eb")
        for k in range(2):
            rr(ctx, x + 60 + k * (w / 2 - 20), 1250 - h + 70, w / 2 - 100, 120, 8)
            fill(ctx, "#cfe3f2")
        x += w + 20
    # тротуар и дорога
    ctx.rectangle(-1500, 1250, 5000, 150)
    fill(ctx, "#b8b3aa")
    ctx.rectangle(-1500, 1390, 5000, 22)
    fill(ctx, "#8e8a82")
    ctx.rectangle(-1500, 1410, 5000, 700)
    fill(ctx, "#3d3f45")
    for i in range(-10, 30):
        rr(ctx, i * 260, 1690, 140, 18, 9)
        fill(ctx, "#f2f2f2")
    # уличная мебель
    for lx in (-420, 480, 1380, 2280):
        lamp_post(ctx, lx, 1330)
    tree(ctx, 120, 1300, 0.8, t, 1)
    tree(ctx, 1900, 1300, 0.8, t, 2)
    trash_bin(ctx, 380, 1320, 0.9)
    hydrant(ctx, 950, 1330, 0.9)
    # брошенная машина с открытой дверью
    parked_car(ctx, -350, 1560, 1.0, "#3b82f6", door_open=True)
    # газеты гонит ветер
    for k in range(3):
        nx = (-500 + k * 700 + t * 160) % 2600 - 400
        newspaper(ctx, nx, 1200 + k * 60 + math.sin(t * 2 + k) * 50, math.sin(t * 3 + k) * 0.8, 0.9)
    # светофор мигает жёлтым
    line(ctx, 1040, 1270, 1040, 820, 18, "#2d2d2d")
    rr(ctx, 1000, 700, 80, 210, 20)
    fill(ctx, "#1d1d1d")
    for k, c in enumerate(("#3a1212", "#ffcc00" if (t * 1.6) % 1 < 0.5 else "#4a3a10", "#0e2b16")):
        ctx.arc(1040, 740 + k * 66, 24, 0, TAU)
        fill(ctx, c)
    if (t * 1.6) % 1 < 0.5:
        glow(ctx, 1040, 806, 110, "#ffcc00", 0.5)
    # брошенный самокат и пакет
    ctx.save()
    ctx.translate(700, 1360)
    ctx.rotate(-0.08)
    line(ctx, -90, 0, 90, 0, 14, "#1fb26b")
    ctx.arc(-90, 6, 20, 0, TAU)
    fill(ctx, "#222")
    ctx.arc(90, 6, 20, 0, TAU)
    fill(ctx, "#222")
    line(ctx, 90, 0, 130, -60, 12, "#1fb26b")
    ctx.restore()
    rr(ctx, 260, 1300, 70, 80, 10)
    fill(ctx, "#f0f0f0")
    # автобус
    bx, by = 1180, 1700
    rr(ctx, bx, by - 470, 1080, 430, 40)
    fill(ctx, "#f2b31b")
    rr(ctx, bx, by - 130, 1080, 50, 10)
    fill(ctx, "#d18f0a")
    for k in range(6):
        rr(ctx, bx + 40 + k * 168, by - 430, 140, 160, 14)
        fill(ctx, "#2b3d52")
        rr(ctx, bx + 50 + k * 168, by - 420, 40, 140, 10)
        fill(ctx, "#4f6a88", 0.6)
    # открытые двери
    for dx in (250, 700):
        rr(ctx, bx + dx, by - 400, 130, 330, 8)
        fill(ctx, "#111820")
        rr(ctx, bx + dx - 34, by - 400, 30, 330, 6)
        fill(ctx, "#c8901a")
        rr(ctx, bx + dx + 134, by - 400, 30, 330, 6)
        fill(ctx, "#c8901a")
    rr(ctx, bx + 20, by - 462, 1040, 26, 12)
    fill(ctx, "#fcd34d", 0.7)
    rr(ctx, bx + 880, by - 470, 180, 60, 8)
    fill(ctx, "#111")
    text(ctx, "47 ЦЕНТР", bx + 970, by - 440, 30, "#fb923c")
    ell(ctx, bx + 1060, by - 150, 22, 30)
    fill(ctx, "#fef9c3")
    glow(ctx, bx + 1060, by - 150, 90, "#fef9c3", 0.6)
    rr(ctx, bx + 1074, by - 420, 14, 120, 6)
    fill(ctx, "#111")
    rr(ctx, bx + 1060, by - 320, 50, 70, 10)
    fill(ctx, "#1f2937")
    for k in range(6):
        line(ctx, bx + 70 + k * 168, by - 260, bx + 70 + k * 168, by - 160, 4, "#d18f0a")
    shadow(ctx, bx + 540, by + 20, 600, 30, 0.45)
    for wx in (bx + 190, bx + 880):
        ctx.arc(wx, by - 50, 96, TAU / 2, TAU)
        fill(ctx, "#b07a10")
        ctx.arc(wx, by - 50, 78, 0, TAU)
        fill(ctx, "#1c1c1c")
        ctx.arc(wx, by - 50, 40, 0, TAU)
        fill(ctx, "#9aa0a6")
        for k in range(6):
            a_ = k * TAU / 6
            ctx.arc(wx + math.cos(a_) * 26, by - 50 + math.sin(a_) * 26, 5, 0, TAU)
            fill(ctx, "#4b5563")
    # двигатель ещё работает: вибрация и выхлоп
    puff(ctx, bx + 1100, by - 70, t, 7, rate=0.18, dx=220, dy=-140, a=0.55, col="#b9bec5")
    # герой
    stop = tb + 0.4
    hxp = lerp(-80, 760, ease(seg(u, 0, stop))) if u < stop else 760
    walking = u < stop
    ew = wl(1, "двигатель")
    e = emo("neutral") if u < tb else emo("worry", "shock", seg(u, ew, ew + 0.3))
    hero(ctx, hxp, 1340, 0.82, e, t, arms="relax" if walking else arms_lerp("relax", "shock", seg(u, ew, ew + 0.3)),
         walk=t * 8 if walking else None, look=(0.8, 0) if u > tb - 0.6 else (0.4, 0),
         blink=blink_at(u, 0.3), tremble=0.5 if u > ew else 0)
    ctx.restore()


def phone_chat(lines_, typing=True, sent_visible=1.0, title="Мама ❤", unsent=None, t=0.0):
    def f(ctx, x, y, w, h):
        vgrad(ctx, x, y, w, h, [(0, "#0f1724"), (1, "#16233a")])
        ctx.rectangle(x, y, w, 150)
        fill(ctx, "#1b2638")
        ctx.arc(x + 70, y + 100, 30, 0, TAU)
        fill(ctx, "#f59e0b")
        text(ctx, title, x + 120, y + 100, 34, "#ffffff", align="left")
        yy = y + 220
        for side, s in lines_:
            tw = text_w(ctx, s, 34)
            bw = min(w - 80, tw + 50)
            bx = x + 30 if side == 0 else x + w - 30 - bw
            rr(ctx, bx, yy, bw, 74, 26)
            fill(ctx, "#2a3a55" if side == 0 else "#2f7cf6")
            text(ctx, s, bx + 25, yy + 37, 34, "#ffffff", align="left")
            yy += 100
        if unsent is not None:
            rr(ctx, x + 20, y + h - 130, w - 40, 90, 40)
            fill(ctx, "#202d42")
            text(ctx, unsent, x + 44, y + h - 85, 28, "#ffffff", align="left")
            if (t * 1.8) % 1 < 0.55:
                cw = text_w(ctx, unsent, 28)
                line(ctx, x + 50 + cw, y + h - 104, x + 50 + cw, y + h - 66, 5, "#7fb2ff", cap=cairo.LINE_CAP_BUTT)
            ctx.arc(x + w - 48, y + h - 85, 22, 0, TAU)
            fill(ctx, "#2f7cf6")
    return f


def s2_cafe(ctx, t, u, D):
    tp = wl(2, "телефон")
    k = ease(seg(u, tp - 0.3, tp + 0.5))
    cx = lerp(390, 700, k)
    cy = lerp(1120, 1180, k)
    z = lerp(1.25, 1.42, ease(seg(u, 0, tp))) * lerp(1, 1.05, k)
    ctx.save()
    cam(ctx, t, cx, cy, z, shake=0.35)
    # фон кафе: окно и боке
    vgrad(ctx, -600, -600, 2400, 1700, [(0, "#3a2a22"), (1, "#6b4a35")])
    r = random.Random(21)
    for i in range(26):
        glow(ctx, r.uniform(-300, 1400), r.uniform(300, 1000), r.uniform(60, 160),
             r.choice(["#ffd27a", "#ffb35a", "#fff1c9", "#9fd3ff"]), r.uniform(0.25, 0.55))
    # стол
    vgrad(ctx, -600, 1000, 2400, 1400, [(0, "#a8704a"), (1, "#6e4227")])
    for i in range(12):
        line(ctx, -600, 1040 + i * 90, 1800, 1060 + i * 90 + (i % 3) * 8, 3, "#5a361f", 0.35)
    # окно кафе: переплёт и подвесные лампы на фоне
    for xx in (-200, 300, 800, 1300):
        rr(ctx, xx - 10, 200, 20, 820, 4)
        fill(ctx, "#2a1c15", 0.8)
    rr(ctx, -600, 600, 2400, 18, 4)
    fill(ctx, "#2a1c15", 0.8)
    for lx in (120, 620, 1120):
        hanging_lamp(ctx, lx, 260, on=True, col="#1f2937")
    chair(ctx, 1100, 1010, 1.2, "#3b2418")
    flower_vase(ctx, 980, 1060, 0.9, t)
    # меню-подставка
    ctx.save()
    ctx.translate(560, 1010)
    rr(ctx, -50, -150, 100, 150, 6)
    fill(ctx, "#1f2937")
    text(ctx, "МЕНЮ", 0, -110, 24, "#fbbf24")
    for k in range(4):
        line(ctx, -32, -70 + k * 18, 32, -70 + k * 18, 3, "#9ca3af")
    ctx.restore()
    # круассан на тарелке, сахар, салфетка с вилкой
    plate(ctx, 150, 1420, 210, 62)
    croissant(ctx, 150, 1400, 0.8, -0.15)
    sugar_packet(ctx, 520, 1330, 0.4, "#e74c3c", "САХАР")
    sugar_packet(ctx, 560, 1395, -0.2, "#8b5a2b", "САХАР")
    napkin_fork(ctx, 1000, 1560, 0.25)
    # капучино
    coffee_cup(ctx, 390, 1240, 0.95, t)
    steam(ctx, 390, 1020, t, h=330, a=0.55)
    # телефон с недописанным сообщением
    ctx.save()
    ctx.translate(760, 1220)
    ctx.rotate(-0.1)
    shadow(ctx, 20, 30, 220, 360, 0.4)
    phone_body(ctx, 0, 0, 330, 640,
               phone_chat([(0, "Ты где?"), (0, "Ужин готов!")], unsent="Я почти дом", t=t,
                          title="Мама"))
    ctx.restore()
    ctx.restore()


CROWD = None


def crowd():
    global CROWD
    if CROWD is None:
        r = random.Random(42)
        CROWD = []
        for row, (y, sc, n) in enumerate(((1180, 0.58, 9), (1360, 0.74, 7), (1560, 0.92, 6))):
            for i in range(n):
                d = r.choice((-1, 1))
                p = Npc(r, -200 + i * (1500 / n) + r.uniform(-60, 60), y, sc, d, r.uniform(0.7, 1.15))
                CROWD.append(p)
    return CROWD


def s3_crowd(ctx, t, u, D):
    tf = wl(3, "посреди")
    td = wl(3, "удалить")
    frozen = u > tf
    z = lerp(1.0, 0.86, ease(seg(u, td, D)))
    ctx.save()
    cam(ctx, t, 540, lerp(1120, 1060, ease(seg(u, td, D))), z, shake=0.3)
    sky(ctx, 1080, 1100, "day")
    skyline(ctx, 31, -600, 1700, 1050, 300, 650, "#9fbad3", "#c2d4e4", 0.35)
    ctx.rectangle(-600, 1040, 2300, 1200)
    fill(ctx, "#d8cfbf")
    for i in range(-6, 16):  # плитка площади
        line(ctx, i * 120, 1040, i * 220 - 600, 2200, 3, "#c4b9a6")
    for j in range(8):
        line(ctx, -600, 1080 + j * j * 22, 1700, 1080 + j * j * 22, 3, "#c4b9a6")
    # фонтан
    ell(ctx, 540, 1110, 220, 40)
    fill(ctx, "#9aa4ad")
    ell(ctx, 540, 1100, 190, 30)
    fill(ctx, "#7ec4e8")
    tt = u if not frozen else tf
    for k in range(5):
        a = (tt * 2 + k / 5) % 1
        ctx.arc(540 + (k - 2) * 30, 1090 - 120 * math.sin(a * math.pi), 8, 0, TAU)
        fill(ctx, "#bfe6ff", 0.8)
    for idx, p in enumerate(crowd()):
        delay = (p.x + 300) / 1700 * 0.55 + (idx % 3) * 0.05
        ts = u - td - delay
        if ts < 0:
            npc(ctx, p, u, walking=True, frozen_t=tf)
        else:
            x = p.x + p.dir * 95 * p.speed * tf
            # вещи падают на землю
            if p.item in ("bag", "phone", "coffee"):
                c = {"bag": "#7c4a2d", "phone": "#111", "coffee": "#f5f5f4"}[p.item]
                rr(ctx, x - 18 * p.sc, p.y - 30 * p.sc, 50 * p.sc, 26 * p.sc, 6)
                fill(ctx, c)
            if ts < 0.6:
                npc(ctx, p, u, walking=True, frozen_t=tf, alpha=1 - ts / 0.6, wipe=1 - ts / 0.6)
            particles_from(ctx, p, x, ts, idx)
    ctx.restore()
    # замороженный кадр: лёгкий синий тон + значок паузы
    if frozen and u < td + 0.2:
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#2a3c66", 0.18 * seg(u, tf, tf + 0.2))
        a = seg(u, tf, tf + 0.15)
        rr(ctx, 70, 420, 34, 100, 6)
        fill(ctx, "#ffffff", a)
        rr(ctx, 124, 420, 34, 100, 6)
        fill(ctx, "#ffffff", a)
    # диалог «Удалить?»
    da = seg(u, tf + 0.5, tf + 0.8) * (1 - seg(u, td + 0.15, td + 0.3))
    if da > 0:
        s = back_out(seg(u, tf + 0.5, tf + 0.85))
        ctx.save()
        ctx.translate(540, 760)
        ctx.scale(s, s)
        ctx.push_group()
        rr(ctx, -410, -190, 820, 380, 34)
        fill(ctx, "#f4f6fa")
        rr(ctx, -410, -190, 820, 90, 34)
        fill(ctx, "#dfe4ee")
        ctx.rectangle(-410, -130, 820, 30)
        fill(ctx, "#dfe4ee")
        text(ctx, "Люди.exe", -370, -145, 38, "#333", align="left")
        text(ctx, "Удалить всех людей?", 0, -30, 50, "#111")
        rr(ctx, -360, 50, 320, 100, 22)
        fill(ctx, "#cfd5df")
        text(ctx, "Отмена", -200, 100, 42, "#333")
        pressed = u > td - 0.05
        rr(ctx, 40, 50 + (6 if pressed else 0), 320, 100, 22)
        fill(ctx, "#b91c1c" if pressed else "#ef4444")
        text(ctx, "УДАЛИТЬ", 200, 100 + (6 if pressed else 0), 42, "#fff")
        # курсор
        cx = lerp(-120, 220, ease(seg(u, tf + 0.9, td - 0.1)))
        cyc = lerp(250, 110, ease(seg(u, tf + 0.9, td - 0.1)))
        ctx.move_to(cx, cyc)
        ctx.line_to(cx, cyc + 80)
        ctx.line_to(cx + 22, cyc + 60)
        ctx.line_to(cx + 40, cyc + 96)
        ctx.line_to(cx + 54, cyc + 88)
        ctx.line_to(cx + 36, cyc + 54)
        ctx.line_to(cx + 62, cyc + 52)
        ctx.close_path()
        src(ctx, "#ffffff")
        ctx.fill_preserve()
        ctx.set_line_width(5)
        src(ctx, "#000")
        ctx.stroke()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(da)
        ctx.restore()
    # вспышка удаления
    fa = 1 - seg(u, td, td + 0.35)
    if u > td and fa > 0:
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#ffffff", 0.6 * fa)


ANCHOR = Npc(random.Random(9), 0, 0)
ANCHOR.style, ANCHOR.shirt, ANCHOR.item, ANCHOR.hair = "short", "#1e3a8a", "none", "#2b1d14"


def tv_screen(ctx, x, y, w, h, t, glitch):
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    vgrad(ctx, x, y, w, h, [(0, "#16316b"), (1, "#0b1a3a")])
    ctx.save()
    ctx.translate(x + w * 0.5, y + h * 1.12)
    ctx.scale(w / 520, w / 520)
    npc(ctx, ANCHOR, 0, walking=False)
    ctx.restore()
    ctx.rectangle(x, y + h * 0.72, w, h * 0.16)
    fill(ctx, "#d61f1f")
    text(ctx, "СРОЧНО: ЛЮДИ ИСЧЕЗ", x + 8, y + h * 0.8, h * 0.1, "#fff", align="left")
    text(ctx, "06:59", x + w - 10, y + h * 0.12, h * 0.09, "#fff", align="right")
    r = random.Random(int(t * 24))
    for i in range(int(4 + 20 * glitch)):
        yy = y + r.random() * h
        ctx.rectangle(x, yy, w, r.uniform(2, 8))
        fill(ctx, "#ffffff", r.uniform(0.05, 0.25 + 0.4 * glitch))
    ctx.restore()


def s4_tv(ctx, t, u, D):
    g = [wl(4, "связи"), wl(4, "интернета"), wl(4, "застывший")]
    z = lerp(0.82, 1.08, ease(seg(u, 0, D)))
    rot = lerp(-0.05, 0.03, ease(seg(u, 0, D)))
    cx = lerp(470, 610, ease(seg(u, 0, D)))
    ctx.save()
    cam(ctx, t, cx, 1000, z, rot, shake=0.4)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0b0f1a"), (1, "#1a2233")])
    on = seg(u, g[2] - 0.2, g[2] + 0.1)
    for row in range(5):
        for col in range(4):
            x = -170 + col * 360
            y = 160 + row * 250
            rr(ctx, x - 12, y - 12, 334, 214, 14)
            fill(ctx, "#05070c")
            gl = 0
            for gg in g:
                gl = max(gl, 1 - abs(u - gg) / 0.25) if abs(u - gg) < 0.25 else gl
            if on > 0:
                tv_screen(ctx, x, y, 310, 190, t if gl > 0 else 0.0, gl)
            else:  # нет сигнала: серый шум
                r = random.Random(int(t * 20) + row * 7 + col)
                ctx.rectangle(x, y, 310, 190)
                fill(ctx, "#2a2f3a")
                for i in range(30):
                    ctx.rectangle(x + r.random() * 300, y + r.random() * 185, r.uniform(6, 40), 4)
                    fill(ctx, "#ffffff", r.uniform(0.05, 0.3))
                text(ctx, "НЕТ СИГНАЛА", x + 155, y + 95, 30, "#ffffff", alpha=0.7)
            glow(ctx, x + 155, y + 95, 260, "#3b82f6", 0.12 + 0.1 * on)
            rr(ctx, x + 110, y + 196, 90, 34, 4)
            fill(ctx, "#facc15")
            text(ctx, f"{39 + (row * 4 + col) * 7}990", x + 155, y + 213, 20, "#111")
    # пол витрины
    ctx.rectangle(-800, 1430, 2700, 1200)
    fill(ctx, "#0c0f16")
    # герой со спины, с телефоном
    hero(ctx, 540, 1880, 0.95, emo("neutral"), t, arms="phone", back=True, rim="#4f8cff", rim_a=0.9,
         hand_item=lambda c, x, y: (rr(c, x - 30, y - 120, 60, 110, 10), fill(c, "#111")))
    ctx.restore()
    bubble_icon(ctx, 260, 470, 1.0, seg(u, g[0] - 0.05, g[0] + 0.7) * (1 - seg(u, g[2] - 0.3, g[2])), "net")
    bubble_icon(ctx, 820, 600, 1.0, seg(u, g[1] - 0.05, g[1] + 0.7) * (1 - seg(u, g[2] - 0.3, g[2])), "wifi")


def car(ctx, x, y, t, sc=1.0, e=None):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(sc, sc)
    # герой в кабине
    ctx.save()
    ctx.translate(-30, -150)
    hero(ctx, 0, 0, 0.62, e, t, arms="wheel", legs=False, rim_a=0.5, look=(0.7, -0.1))
    ctx.restore()
    ctx.move_to(-470, -40)
    ctx.curve_to(-470, -150, -380, -170, -230, -180)
    ctx.line_to(-120, -280)
    ctx.curve_to(0, -300, 120, -290, 200, -200)
    ctx.line_to(420, -170)
    ctx.curve_to(500, -160, 520, -100, 510, -40)
    ctx.close_path()
    fill(ctx, "#e11d2e")
    # стекло (вырез у кабины)
    ctx.move_to(-190, -185)
    ctx.line_to(-100, -265)
    ctx.curve_to(-10, -280, 90, -275, 160, -205)
    ctx.close_path()
    fill(ctx, "#bfe3ff", 0.35)
    line(ctx, -440, -70, 480, -70, 6, "#9e0f1e")
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


def s5_fun(ctx, t, u, D):
    a, b, c = (x - TL.shots[5][0] for x in EV["sub5"])
    ctx.save()
    if u < a:  # тележка из супермаркета на пустой дороге
        k = u / a
        cam(ctx, t, 540, 1100, lerp(0.9, 1.05, k), shake=0.8)
        sky(ctx, 1080, 1250, "day")
        skyline(ctx, 51, -800 - u * 300, 2400, 1150, 300, 650, "#9fbad3", "#c2d4e4", 0.35)
        ctx.rectangle(-800, 1250, 3000, 1000)
        fill(ctx, "#3d3f45")
        for i in range(-10, 20):
            rr(ctx, (i * 260 - u * 1500) % 3400 - 1000, 1600, 140, 18, 9)
            fill(ctx, "#f2f2f2")
        x = lerp(200, 640, k)
        hero(ctx, x, 1420, 0.85, emo("happy"), t, arms="cheer", bob=-abs(math.sin(u * 9)) * 18)
        # тележка
        ctx.save()
        ctx.translate(x - 20, 1460)
        rr(ctx, -150, -230, 300, 180, 10)
        src(ctx, "#c0c6cc")
        ctx.set_line_width(10)
        ctx.stroke()
        for i in range(5):
            line(ctx, -150 + i * 75, -230, -150 + i * 75, -50, 5, "#c0c6cc")
        for wx in (-110, 110):
            ctx.arc(wx, -20, 22, 0, TAU)
            fill(ctx, "#222")
        ctx.restore()
        speed_lines(ctx, 1080, 1900, t, a=0.35)
        text(ctx, "НЕДЕЛЯ 1", 540, 560, 120, "#ffd400", "#000", 16, shadow=True)
    elif u < b:  # машина мечты
        k = (u - a) / (b - a)
        cam(ctx, t, 540, 1150, lerp(0.95, 1.1, k), shake=1.0)
        sky(ctx, 1080, 1300, "sunset")
        glow(ctx, 760, 900, 380, "#ffd36b", 0.9)
        ctx.arc(760, 900, 120, 0, TAU)
        fill(ctx, "#ffe08a")
        ctx.save()
        ctx.translate(-(u * 250) % 1400, 0)
        for rep in range(3):
            skyline(ctx, 61, -800 + rep * 1400, 600 + rep * 1400, 1300, 100, 420, "#4b2a52", None, wmin=180, wmax=320)
        ctx.restore()
        ctx.rectangle(-800, 1300, 3000, 900)
        fill(ctx, "#2b2b33")
        for i in range(-4, 12):
            rr(ctx, (i * 300 - u * 3600) % 3600 - 1200, 1560, 170, 16, 8)
            fill(ctx, "#ffd400")
        car(ctx, 540, 1520, t, 1.0, emo("joy"))
        speed_lines(ctx, 1080, 1900, t, n=34, a=0.5)
    elif u < c:  # президентский люкс
        k = (u - b) / (c - b)
        cam(ctx, t, 540, 1050, lerp(1.0, 0.92, k), shake=0.6)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#2b1640"), (1, "#5b2f6b")])
        for i in range(-3, 8):
            ctx.rectangle(i * 200, -800, 6, 3600)
            fill(ctx, "#e7c66a", 0.15)
        # люстра
        line(ctx, 540, -200, 540, 260, 6, "#e7c66a")
        for i in range(7):
            glow(ctx, 380 + i * 53, 300 + abs(i - 3) * -10, 60, "#fff2b0", 0.8)
        curtain(ctx, -260, 200, 300, 1300, "#7e1d4f", t, 1)
        curtain(ctx, 1040, 200, 300, 1300, "#7e1d4f", t, -1)
        for nx in (-30, 1110):
            rr(ctx, nx - 80, 1220, 160, 180, 10)
            fill(ctx, "#5b2b16")
            table_lamp(ctx, nx, 1220, 0.9)
        rr(ctx, 120, 860, 840, 360, 60)
        lgrad(ctx, 120, 0, 960, 0, [(0, "#a8801f"), (0.5, "#f1d27a"), (1, "#a8801f")])
        ctx.fill()
        for k in range(5):
            ctx.arc(220 + k * 160, 1000, 40, 0, TAU)
            ctx.set_line_width(8)
            src(ctx, "#a8801f")
            ctx.stroke()
        rr(ctx, 60, 1160, 960, 360, 40)
        fill(ctx, "#f2ece2")
        for k, px in enumerate((160, 330, 750, 920)):
            rr(ctx, px - 80, 1120 - (k % 2) * 10, 160, 90, 40)
            fill(ctx, "#fff7ed" if k % 3 else "#f9a8d4")
        rr(ctx, 60, 1300, 960, 260, 30)
        lgrad(ctx, 0, 1300, 0, 1560, [(0, "#a83a5c"), (1, "#6e1e38")])
        ctx.fill()
        for k in range(8):
            line(ctx, 60, 1330 + k * 30, 1020, 1330 + k * 30, 3, "#f1d27a", 0.35)
        jump = abs(math.sin(u * 6.5)) * 260
        hero(ctx, 540, 1250 - jump, 0.85, emo("happy"), t, arms="up", walk=u * 3)
        r = random.Random(3)
        for i in range(16):
            px = r.uniform(80, 1000)
            py = 1100 - ((u * r.uniform(150, 300) + r.uniform(0, 900)) % 900)
            ctx.save()
            ctx.translate(px + math.sin(u * 3 + i) * 30, py)
            ctx.rotate(math.sin(u * 2 + i))
            ell(ctx, 0, 0, 16, 6)
            fill(ctx, "#ffffff", 0.9)
            ctx.restore()
        text(ctx, "ЛЮКС", 540, 560, 130, "#ffd400", "#000", 16, shadow=True)
    else:  # всё, что хочешь: фудкорт и ровно сервированный стол
        k = (u - c) / max(0.01, D - c)
        cam(ctx, t, 540, 1150, lerp(0.92, 1.12, ease(k)), shake=0.5)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#ffd9a0"), (1, "#f59e6b")])
        # вывески фудкорта
        for i, (nm, col) in enumerate((("БУРГЕРЫ", "#dc2626"), ("ПИЦЦА", "#16a34a"), ("ДОНАТЫ", "#db2777"),
                                       ("СУШИ", "#1d4ed8"))):
            x = -230 + i * 400
            rr(ctx, x, 260, 360, 420, 16)
            fill(ctx, "#fff7ed")
            rr(ctx, x, 260, 360, 90, 16)
            fill(ctx, col)
            text(ctx, nm, x + 180, 305, 44, "#ffffff")
            for j in range(4):
                rr(ctx, x + 30, 380 + j * 70, 200, 18, 6)
                fill(ctx, "#d6d3d1")
                text(ctx, f"{(j + 2) * 90} р", x + 300, 389 + j * 70, 30, col)
        for lx in (60, 540, 1020):
            hanging_lamp(ctx, lx, 760, on=True, col="#7c2d12")
        hero(ctx, 540, 1480, 0.95, emo("joy"), t, arms="hold", bob=math.sin(u * 10) * 6,
             hand_item=lambda cc, x, y: burger2(cc, x - 40, y - 40, 0.75))
        # стол с клетчатой скатертью
        rr(ctx, -300, 1360, 1680, 1000, 20)
        fill(ctx, "#fafaf9")
        for i in range(-4, 20):
            ctx.rectangle(-300 + i * 90, 1360, 45, 1000)
            fill(ctx, "#ef4444", 0.75)
        for j in range(12):
            ctx.rectangle(-300, 1360 + j * 90, 1680, 45)
            fill(ctx, "#ef4444", 0.35)
        rr(ctx, -300, 1360, 1680, 26, 6)
        fill(ctx, "#000", 0.12)
        # центр: двухъярусная подставка с бургерами
        cake_stand(ctx, 540, 1560, 300, 230)
        for bx_ in (420, 540, 660):
            burger2(ctx, bx_, 1500, 0.72)
        for bx_ in (470, 610):
            burger2(ctx, bx_, 1270, 0.6)
        # слева пицца в коробке, справа донаты на тарелке
        pizza_whole(ctx, 120, 1690, 190, 110)
        plate(ctx, 960, 1700, 200, 70)
        for i, (dx, dy, ic) in enumerate(((-90, -10, "#f472b6"), (0, -20, "#8b5a2b"), (90, -10, "#fde68a"),
                                          (-45, 25, "#60a5fa"), (45, 25, "#f472b6"))):
            donut2(ctx, 960 + dx, 1700 + dy, 0.8, ic)
        # ряд напитков и картошка
        for i, col in enumerate(("#ef4444", "#f59e0b", "#3b82f6")):
            soda_cup(ctx, 290 + i * 90, 1860, 0.85, col)
        fries(ctx, 720, 1880, 0.9)
        fries(ctx, 830, 1890, 0.9)
    ctx.restore()


def s6_silence(ctx, t, u, D):
    z = lerp(1.5, 0.82, ease_out(seg(u, 0, D), 2))
    ctx.save()
    cam(ctx, t, 540, lerp(1250, 1050, ease(seg(u, 0, D))), z, shake=0.2)
    vgrad(ctx, -1200, -1200, 3500, 4400, [(0, "#070a16"), (1, "#121a33")])
    ctx.save()
    rr(ctx, -300, 0, 1680, 1500, 0)
    ctx.clip()
    sky(ctx, 1080, 1500, "night")
    stars(ctx, 5, 1080, 900, t)
    ctx.arc(820, 300, 90, 0, TAU)
    fill(ctx, "#f3f0dc")
    glow(ctx, 820, 300, 300, "#cfd8ff", 0.35)
    skyline(ctx, 71, -400, 1500, 1500, 350, 900, "#0b1124", None)
    skyline(ctx, 72, -400, 1500, 1500, 150, 520, "#060a17", None, wmin=160, wmax=260)
    ctx.restore()
    for x0 in (-300, 260, 820, 1380):
        ctx.rectangle(x0 - 12, 0, 24, 1500)
        fill(ctx, "#05070e")
    ctx.rectangle(-1200, 1500, 3500, 1500)
    fill(ctx, "#0a0e1c")
    # диван и торшер (выключен)
    rr(ctx, -260, 1330, 520, 200, 50)
    fill(ctx, "#1b2440")
    rr(ctx, -280, 1420, 560, 120, 40)
    fill(ctx, "#222c4d")
    line(ctx, 1240, 1500, 1240, 1050, 10, "#0f1428")
    ctx.move_to(1160, 1060)
    ctx.line_to(1320, 1060)
    ctx.line_to(1280, 950)
    ctx.line_to(1200, 950)
    fill(ctx, "#1b2440")
    plant(ctx, 960, 1520, 0.9, t, "#334155")
    # отражение луны на полу
    glow(ctx, 640, 1600, 280, "#9fb4ff", 0.12)
    hero(ctx, 540, 1640, 0.9, emo("sad"), t, arms="hug", legs=False, knees=True, rim="#7ea0ff",
         rim_a=0.8, look=(0, 0.6), blink=blink_at(u, 1.2, 3.6))
    ctx.restore()


def s7_mannequin(ctx, t, u, D):
    tg = wl(7, "ставишь")
    tw = wl(7, "ждешь")
    cx = lerp(470, 620, ease(seg(u, 0, D)))
    z = lerp(0.9, 1.05, ease(seg(u, 0, D))) + 0.12 * ease(seg(u, tw, D))
    ctx.save()
    cam(ctx, t, cx, 1120, z, lerp(0.02, -0.02, ease(seg(u, 0, D))), shake=0.35)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#11262b"), (1, "#1f3c40")])
    # витрины ТЦ на заднем плане
    for i in range(-1, 4):
        x = i * 420 - 120
        rr(ctx, x, 380, 380, 640, 8)
        fill(ctx, "#18343a")
        rr(ctx, x + 20, 400, 340, 600, 6)
        fill(ctx, "#2b5258", 0.6)
        rr(ctx, x, 330, 380, 60, 6)
        fill(ctx, "#0c1a1d")
        text(ctx, ["SALE", "МОДА", "ОБУВЬ", "-70%", "NEW"][(i + 1) % 5], x + 190, 360, 34, "#5eead4", alpha=0.5)
    # манекены за стеклом (один медленно поворачивает голову к герою)
    turn = -ease(seg(u, D - 1.6, D - 0.3))
    for i, mx in enumerate((-60, 160, 1040, 1250)):
        mannequin(ctx, mx, 1000, 0.95, head_turn=turn if i == 2 else 0.0)
    for lx in (-100, 400, 900, 1400):
        hanging_lamp(ctx, lx, 180, on=True, col="#0f2a2e")
    ctx.rectangle(-800, 1000, 2700, 1500)
    lgrad(ctx, 0, 1000, 0, 2500, [(0, "#2a3b3e"), (1, "#1a2628")])
    ctx.fill()
    for i in range(-3, 6):
        glow(ctx, i * 420 + 90, 1060, 200, "#5eead4", 0.08)
    for i in range(-6, 14):
        line(ctx, i * 150, 1000, i * 260 - 900, 2400, 3, "#334a4e")
    plant(ctx, -60, 1300, 1.1, t, "#0f766e")
    plant(ctx, 1180, 1320, 1.0, t, "#0f766e")
    bench(ctx, 1150, 1180, 0.8)
    # собеседник-манекен
    mannequin(ctx, 800, 1520, 1.15, pose=0.2)
    # герой
    if u < tg:
        arms = "shrug" if (u * 1.4) % 2 < 1 else "fwd"
        e = emo("crazy")
    elif u < tw:
        arms = arms_lerp("down", "give", seg(u, tg, tg + 0.4))
        e = emo("calm")
    else:
        arms = "down"
        e = emo("calm", "sad", seg(u, tw + 0.3, tw + 1.0))
    hero(ctx, 300, 1640, 1.05, e, t, arms=arms, look=(0.8, 0.1), blink=blink_at(u, 0.4), rim="#5eead4",
         rim_a=0.8)
    # стол
    ell(ctx, 560, 1440, 330, 70)
    fill(ctx, "#e5e0d6")
    ell(ctx, 560, 1430, 320, 62)
    fill(ctx, "#f5f2ea")
    rr(ctx, 540, 1460, 40, 400, 10)
    fill(ctx, "#b8b2a6")
    # чашки
    def cup(x, y):
        coffee_cup(ctx, x, y + 6, 0.36, t, heart=True)
    cup(420, 1440)
    kk = ease(seg(u, tg + 0.1, tg + 0.7))
    cup(lerp(500, 690, kk), lerp(1300, 1440, kk) - math.sin(kk * math.pi) * 60)
    if u > tg + 0.7:
        steam(ctx, 690, 1360, t, h=120, a=0.35)
    # пузыри речи
    if u < tg:
        k = back_out(seg(u, 0.2, 0.5))
        ctx.save()
        ctx.translate(330, 760)
        ctx.scale(k, k)
        rr(ctx, -200, -80, 400, 140, 60)
        fill(ctx, "#ffffff")
        text(ctx, "Как дела?", 0, -10, 52, "#111")
        ctx.restore()
    if u > tw:
        k = back_out(seg(u, tw, tw + 0.3))
        ctx.save()
        ctx.translate(820, 830)
        ctx.scale(k, k)
        rr(ctx, -120, -70, 240, 120, 55)
        fill(ctx, "#ffffff")
        for i in range(3):
            ctx.arc(-50 + i * 50, -10, 13, 0, TAU)
            fill(ctx, "#111", 0.3 + 0.7 * ((t * 2 + i * 0.33) % 1 < 0.5))
        ctx.restore()
    ctx.restore()


def s8_roof(ctx, t, u, D):
    p0, p1 = EV["paint"]
    pk = seg(t, p0 + 0.2, p1)
    z = lerp(1.45, 0.6, ease(seg(u, 0.6, D)))
    hx0 = lerp(-60, 1100, pk)
    hy0 = 1000 + math.sin(pk * 18) * 160
    kf = ease(seg(u, 0.6, D))
    ctx.save()
    cam(ctx, t, lerp(hx0 + 60, 540, kf), lerp(hy0 + 60, 980, kf), z,
        rot=lerp(0.06, -0.02, ease(seg(u, 0, D))), shake=0.4)
    # улица внизу и соседние крыши
    ctx.rectangle(-3000, -3000, 7000, 8000)
    fill(ctx, "#3a2f3d")
    r = random.Random(8)
    for i in range(30):
        x, y = r.uniform(-1600, 2600), r.uniform(-1200, 3200)
        if -200 < x < 1300 and 150 < y < 1850:
            continue
        rr(ctx, x, y, r.uniform(260, 600), r.uniform(260, 600), 10)
        fill(ctx, r.choice(["#5b4a55", "#6a5560", "#4a3d48"]))
    # крыша героя
    rr(ctx, -120, 200, 1320, 1620, 20)
    fill(ctx, "#8d8a86")
    rr(ctx, -120, 200, 1320, 1620, 20)
    ctx.set_line_width(30)
    src(ctx, "#6b6764")
    ctx.stroke()
    for (x, y) in ((40, 360), (980, 1620), (1000, 360)):
        rr(ctx, x - 60, y - 60, 120, 120, 14)
        fill(ctx, "#6e6b67")
        ctx.arc(x, y, 34, 0, TAU)
        fill(ctx, "#4c4a47")
    water_tank(ctx, 1020, 1640, 0.9)
    ac_unit(ctx, 60, 1660, 0.8, t)
    ac_unit(ctx, 260, 1680, 0.7, t + 1)
    line(ctx, 1080, 300, 1080, 520, 8, "#4b5563")  # антенна
    for k in range(3):
        line(ctx, 1030, 340 + k * 50, 1130, 340 + k * 50, 6, "#4b5563")
    for k in range(9):  # швы кровли
        line(ctx, -100, 300 + k * 180, 1180, 300 + k * 180, 3, "#7a7773", 0.6)
    # след от валика
    ctx.save()
    ctx.translate(540, 1000)
    ctx.rectangle(-700, 420, 1400 * pk, 50)
    ctx.restore()
    fill(ctx, "#e3261f", 0.45)
    paint_bucket(ctx, -40, 1500, 1.0)
    # надпись Я ЗДЕСЬ — проявляется по мере покраски
    ctx.save()
    ctx.translate(540, 1000)
    ctx.rotate(-0.04)
    ctx.rectangle(-700, -700, 1400 * pk, 1400)
    ctx.clip()
    text(ctx, "Я", 0, -330, 420, "#e3261f")
    text(ctx, "ЗДЕСЬ", 0, 160, 300, "#e3261f")
    ctx.restore()
    # герой с валиком у кромки краски
    hx = lerp(-60, 1100, pk)
    hy = 1000 + math.sin(pk * 18) * 160
    hero(ctx, hx, hy + 260, 0.55, emo("determined"), t, arms="paint", walk=t * 7 if 0 < pk < 1 else None,
         rim="#ff9a3c", hand_item=lambda c, x, y: (line(c, x, y, x + 40, y + 120, 10, "#333"),
                                                    rr(c, x - 10, y + 110, 110, 40, 12), fill(c, "#e3261f")))
    ctx.restore()
    # тёплый закатный свет
    g = cairo.LinearGradient(0, 0, W, H)
    g.add_color_stop_rgba(0, 1, 0.6, 0.3, 0.35)
    g.add_color_stop_rgba(1, 0.4, 0.1, 0.4, 0.25)
    ctx.set_source(g)
    ctx.paint()


def lock_screen(ctx, x, y, w, h, notif=1.0, t=0.0):
    vgrad(ctx, x, y, w, h, [(0, "#1e1b4b"), (1, "#0f172a")])
    text(ctx, "03:17", x + w / 2, y + h * 0.2, w * 0.24, "#ffffff")
    text(ctx, "среда, 12 ноября", x + w / 2, y + h * 0.29, w * 0.06, "#c7d2fe")
    text(ctx, "НЕТ СЕТИ", x + 40, y + 70, w * 0.04, "#94a3b8", align="left")
    if notif > 0:
        s = back_out(notif)
        ctx.save()
        ctx.translate(x + w / 2, y + h * 0.45)
        ctx.scale(s, s)
        rr(ctx, -w * 0.44, -h * 0.07, w * 0.88, h * 0.14, 30)
        fill(ctx, "#ffffff", 0.92)
        rr(ctx, -w * 0.4, -h * 0.045, h * 0.09, h * 0.09, 18)
        fill(ctx, "#22c55e")
        text(ctx, "Номер скрыт", -w * 0.4 + h * 0.11, -h * 0.02, w * 0.055, "#111", align="left")
        text(ctx, "1 новое сообщение", -w * 0.4 + h * 0.11, h * 0.03, w * 0.045, "#555", align="left")
        ctx.restore()


def s9_vibrate(ctx, t, u, D):
    tv = wl(9, "вибрирует")
    on = u > tv
    sn = seg(u, tv, tv + 0.15)
    z = lerp(0.95, 1.15, ease(seg(u, 0, tv))) + 0.45 * ease_out(sn)
    cxx = lerp(540, 760, ease(seg(u, tv - 0.1, tv + 0.2)))
    ctx.save()
    cam(ctx, t, cxx, lerp(1150, 1260, sn), z, shake=0.3 + 0.8 * sn)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0a1024"), (1, "#141c36")])
    # окно с луной
    rr(ctx, 120, 200, 840, 700, 10)
    fill(ctx, "#0e1a3a")
    stars(ctx, 9, 900, 800, t, 30)
    ctx.arc(760, 380, 70, 0, TAU)
    fill(ctx, "#e8e6d6")
    for x0 in (120, 535, 950):
        ctx.rectangle(x0 - 10, 200, 20, 700)
        fill(ctx, "#1c2442")
    # лунный свет
    ctx.move_to(130, 900)
    ctx.line_to(950, 900)
    ctx.line_to(1200, 2000)
    ctx.line_to(-100, 2000)
    fill(ctx, "#9fb4ff", 0.06)
    # кровать + спящий герой
    rr(ctx, 0, 1200, 700, 210, 40)
    fill(ctx, "#2a1e30")
    wake = seg(u, tv + 0.35, tv + 0.8)
    ctx.save()
    ctx.translate(560, 1490)
    ctx.rotate(lerp(-1.42, 0, ease_out(wake)))
    hero(ctx, 0, 0, 0.9, emo("sleep") if wake <= 0 else emo("shock"), t, legs=False, rim="#7ea0ff",
         rim_a=0.5, arms="down", look=(0.9, 0.3))
    ctx.restore()
    ctx.move_to(0, 1480)
    ctx.curve_to(250, 1430, 500, 1440, 720, 1470)
    ctx.line_to(720, 2200)
    ctx.line_to(0, 2200)
    fill(ctx, "#1d2d6b")
    # тумбочка и телефон
    rr(ctx, 680, 1300, 320, 400, 14)
    lgrad(ctx, 680, 0, 1000, 0, [(0, "#2a1e1c"), (0.5, "#3f2d2a"), (1, "#2a1e1c")])
    ctx.fill()
    ctx.arc(840, 1420, 9, 0, TAU)
    fill(ctx, "#8a7a5a")
    glass_water(ctx, 960, 1300, 0.9)
    for k, col in enumerate(("#7f1d1d", "#1e3a8a", "#14532d")):  # стопка книг
        rr(ctx, 690 + k * 4, 1300 - 26 * (k + 1), 120, 24, 4)
        fill(ctx, col)
    table_lamp(ctx, 940, 1170, 0.7, on=False)
    ctx.move_to(880, 1300)  # провод зарядки
    ctx.curve_to(900, 1420, 1000, 1380, 1010, 1600)
    ctx.set_line_width(5)
    src(ctx, "#e5e7eb", 0.7)
    ctx.stroke()
    if on:
        glow(ctx, 840, 1260, 520, "#7dd3fc", 0.45 * (0.8 + 0.2 * math.sin(t * 30)))
    ctx.save()
    vib = math.sin(t * 90) * 8 if on and (u - tv) % 0.9 < 0.55 else 0
    ctx.translate(840 + vib, 1265)
    ctx.scale(1, 0.38)
    phone_body(ctx, 0, 0, 180, 340, lambda c, x, y, w, h: lock_screen(c, x, y, w, h, 1, t), on=1.0 if on else 0)
    ctx.restore()
    if on:
        for k in range(2):
            for side in (-1, 1):
                ctx.arc(840, 1265, 150 + k * 40 + (t * 120) % 40, -0.5 + (0 if side > 0 else math.pi),
                        0.5 + (0 if side > 0 else math.pi))
                ctx.set_line_width(8)
                src(ctx, "#ffffff", 0.6 - k * 0.25)
                ctx.stroke()
    ctx.restore()
    if not on:
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#000", 0.25)


def hands_phone(ctx, t, screen, tremble=1.0, sc=1.0):
    ctx.save()
    ctx.translate(540 + math.sin(t * 37) * 5 * tremble, 1000 + math.sin(t * 29) * 5 * tremble)
    ctx.scale(sc, sc)
    glow(ctx, 0, 0, 1100, "#60a5fa", 0.25)
    for side in (-1, 1):
        line(ctx, side * 600, 900, side * 380, 300, 150, HOOD)
        ctx.arc(side * 340, 230, 90, 0, TAU)
        fill(ctx, HEAD)
    phone_body(ctx, 0, 0, 620, 1240, screen)
    for side in (-1, 1):
        ell(ctx, side * 320, 120, 48, 90)
        fill(ctx, HEAD)
    ctx.restore()


def s10_lock(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, 1000, lerp(0.92, 1.05, ease(seg(u, 0, D))), shake=0.6)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#020308"), (1, "#0a0f1e")])
    n = seg(u, wl(10, "сообщение") - 0.3, wl(10, "сообщение") + 0.2)
    hands_phone(ctx, t, lambda c, x, y, w, h: lock_screen(c, x, y, w, h, n, t), tremble=1.0)
    ctx.restore()


def s11_message(ctx, t, u, D):
    msg = "Не выключай свет. Они думают, что забрали всех."
    words = TL.lines[11]["words"]
    # сколько символов показать — синхронно с голосом
    shown = 0
    acc = 0
    parts = msg.split(" ")
    for i, w in enumerate(words):
        ws = w["t"] + TL.lines[11]["start"] - TL.shots[11][0]
        if u >= ws:
            k = clamp((u - ws) / max(0.05, w["d"]))
            shown = acc + int(round(len(parts[i]) * k)) if i < len(parts) else len(msg)
        acc += len(parts[i]) + 1 if i < len(parts) else 0
    txt = msg[:shown]
    glitch = 1 - abs(u - wl(11, "всех")) / 0.3 if abs(u - wl(11, "всех")) < 0.3 else 0

    def screen(c, x, y, w, h):
        vgrad(c, x, y, w, h, [(0, "#0b0b0f"), (1, "#14141c")])
        c.rectangle(x, y, w, 170)
        fill(c, "#1a1a22")
        c.arc(x + 80, y + 110, 36, 0, TAU)
        fill(c, "#3f3f46")
        text(c, "?", x + 80, y + 110, 44, "#fff")
        text(c, "Номер скрыт", x + 140, y + 110, 40, "#ffffff", align="left")
        # пузырь с переносом строк
        fs = 46
        maxw = w - 130
        rows, cur = [], ""
        for wd in txt.split(" "):
            test = (cur + " " + wd).strip()
            if text_w(c, test, fs) > maxw and cur:
                rows.append(cur)
                cur = wd
            else:
                cur = test
        if cur:
            rows.append(cur)
        if rows:
            bh = 40 + len(rows) * 62
            rr(c, x + 30, y + 240, w - 60, bh, 32)
            fill(c, "#26262e")
            for i, row in enumerate(rows):
                text(c, row, x + 65, y + 290 + i * 62, fs, "#ffffff", align="left")
        if shown >= len(msg):
            text(c, "03:17 · прочитано", x + w - 40, y + 300 + len(rows) * 62, 28, "#71717a", align="right")
        if glitch > 0:
            r = random.Random(int(t * 30))
            for i in range(14):
                c.rectangle(x, y + r.random() * h, w, r.uniform(4, 30))
                fill(c, r.choice(["#ff0040", "#00e5ff", "#ffffff"]), 0.35 * glitch)
    ctx.save()
    cam(ctx, t, 540, 820, lerp(1.25, 1.5, ease(seg(u, 0, D))), shake=0.5)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#000"), (1, "#05060a")])
    hands_phone(ctx, t, screen, tremble=1.3)
    ctx.restore()


def stairwell(ctx, t, u, s0, steps):
    """Разрез подъезда: 9 этажей, тень поднимается, лампы гаснут за ней."""
    FH = 520  # высота этажа
    n_steps = sum(1 for s in steps if s <= t)
    pos = n_steps + ease(seg(t - (steps[n_steps - 1] if n_steps else 0), 0, 0.3)) - 1 if n_steps else 0
    floor_f = pos / 2.0  # 2 шага на пролёт
    vgrad(ctx, -800, -6000, 2700, 9000, [(0, "#1a1c22"), (1, "#24272f")])
    for f in range(10):
        y = 1700 - f * FH
        # площадка
        ctx.rectangle(-300, y, 1700, 30)
        fill(ctx, "#3a3d46")
        # лестница
        ctx.move_to(100, y)
        for k in range(10):
            ctx.line_to(100 + k * 80, y - k * (FH / 10))
            ctx.line_to(100 + (k + 1) * 80, y - k * (FH / 10))
        ctx.line_to(900, y - FH)
        ctx.line_to(900, y)
        ctx.close_path()
        fill(ctx, "#2f323b")
        text(ctx, str(f + 1), 980, y - 300, 120, "#5a5f6b")
        # перила
        line(ctx, 100, y - 140, 900, y - FH - 140, 8, "#4b5563")
        for k in range(9):
            line(ctx, 140 + k * 85, y - 10 - k * (FH / 10), 140 + k * 85, y - 140 - k * (FH / 10) - 10, 4, "#4b5563")
        apartment_door(ctx, -230, y, 200, 380, str(f * 4 + 1))
        apartment_door(ctx, 1130, y, 200, 380, str(f * 4 + 2))
        if f == 0:
            mailboxes(ctx, 920, y - 520, 3, 3)
        # трещины на стене
        r_ = random.Random(f)
        ctx.move_to(r_.uniform(300, 800), y - FH + 40)
        for k in range(4):
            ctx.rel_line_to(r_.uniform(-30, 30), r_.uniform(20, 50))
        ctx.set_line_width(3)
        src(ctx, "#0b0c10", 0.6)
        ctx.stroke()
        # лампа: гаснет, когда тень проходит этаж
        alive = f > floor_f + 0.3 or f > 8
        flick = alive and (f == int(floor_f + 1)) and random.Random(int(t * 15) + f).random() < 0.3
        lit = alive and not flick
        line(ctx, 540, y - FH + 30, 540, y - FH + 90, 5, "#111")
        ctx.arc(540, y - FH + 105, 22, 0, TAU)
        fill(ctx, "#ffe8a3" if lit else "#3a3a3a")
        if lit:
            glow(ctx, 540, y - FH + 160, 420, "#ffd27a", 0.35)
    # тень на стене
    fy = 1700 - floor_f * FH
    sx = 200 + (pos % 2) * 300
    stranger_shadow(ctx, sx, fy, 1100, pos, 0.85)
    return 1700 - floor_f * FH


def s12_final(ctx, t, u, D):
    steps = EV["steps"]
    a, b, c, d = EV["sub12"]
    if t < b:
        ctx.save()
        s0 = TL.shots[12][0]
        floor_y = 1700 - (sum(1 for s in steps if s <= t) / 2.0) * 520
        cy = min(1100, floor_y - 300) if t > a - 0.5 else 1100
        k = seg(t, s0, b)
        cam(ctx, t, 540, lerp(1100, cy, 0.85), lerp(0.9, 0.75, k), shake=0.5)
        stairwell(ctx, t, u, s0, steps)
        ctx.restore()
    elif t < c:  # лицо героя, эффект «вертиго»
        k = seg(t, b, c)
        ctx.save()
        cam(ctx, t, 540, 960, 1.0, shake=0.7)
        ctx.save()
        ctx.translate(540, 900)
        ctx.scale(lerp(1.3, 0.75, k), lerp(1.3, 0.75, k))
        ctx.translate(-540, -900)
        vgrad(ctx, -1500, -1500, 4000, 5000, [(0, "#2a1c14"), (1, "#120c08")])
        rr(ctx, 140, 100, 800, 2000, 10)
        fill(ctx, "#4a3022")
        rr(ctx, 180, 140, 720, 1900, 8)
        fill(ctx, "#5c3b29")
        ctx.arc(820, 1050, 28, 0, TAU)
        fill(ctx, "#d4a849")
        ctx.arc(540, 520, 22, 0, TAU)  # глазок
        fill(ctx, "#d4a849")
        ctx.arc(540, 520, 12, 0, TAU)
        fill(ctx, "#111")
        for k in range(5):  # цепочка
            ell(ctx, 760 + k * 22, 900 + k * 8, 14, 8)
            ctx.set_line_width(5)
            src(ctx, "#c0c4ca")
            ctx.stroke()
        ctx.restore()
        hero(ctx, 540, lerp(1385, 1555, k), lerp(1.7, 2.3, k), emo("fear"), t, arms="shock", legs=False,
             look=(0, 0), tremble=1.2, rim="#ffb36b")
        # капля пота
        ell(ctx, 700, lerp(820, 1100, k), 16, 24)
        fill(ctx, "#bfe6ff", 0.9)
        ctx.restore()
    elif t < d:  # щель под дверью: свет, тени ног
        k = seg(t, c, d)
        ctx.save()
        cam(ctx, t, 540, 960, lerp(1.0, 1.15, k), shake=0.3)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0c0907"), (1, "#18110c")])
        rr(ctx, 120, -200, 840, 1520, 6)
        fill(ctx, "#2b1c13")
        # свет под дверью
        ctx.rectangle(120, 1320, 840, 26)
        fill(ctx, "#ffcf7a")
        glow(ctx, 540, 1400, 500, "#ffb54a", 0.35)
        # ноги появляются на последних шагах
        near = clamp(sum(1 for s in steps if c <= s <= t) / 3)
        if near > 0:
            for side in (-1, 1):
                ctx.rectangle(540 + side * 120 - 70, 1320, 140 * near, 26)
                fill(ctx, "#000")
        # пол комнаты, коврик, ручка двери
        ctx.rectangle(-800, 1346, 2700, 1500)
        fill(ctx, "#140e0a")
        for k in range(8):
            line(ctx, -800, 1400 + k * k * 12, 1900, 1400 + k * k * 12, 3, "#24180f")
        rr(ctx, 240, 1400, 600, 120, 14)
        fill(ctx, "#3b2a1a")
        text(ctx, "ДОБРО ПОЖАЛОВАТЬ", 540, 1460, 34, "#6b4f33")
        rr(ctx, 860, 700, 60, 26, 10)
        fill(ctx, "#a88a4a")
        ctx.restore()
        # свет мигает и гаснет
        if t > d - 0.9:
            r = random.Random(int(t * 20))
            ctx.rectangle(0, 0, W, H)
            fill(ctx, "#000", 1.0 if t > d - 0.25 else (0.85 if r.random() < 0.5 else 0.0))
    else:  # финальная карточка
        k = seg(t, d, d + 0.6)
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#000")
        s = back_out(k)
        ctx.save()
        ctx.translate(540, 860)
        ctx.scale(s, s)
        text(ctx, "ПРОДОЛЖЕНИЕ", 0, -170, 70, "#ffffff")
        text(ctx, "ЧАСТЬ 2", 0, 0, 190, "#ffd400", "#d8332a", 18)
        text(ctx, "Кто такие «ОНИ»?", 0, 200, 66, "#ff4d4d")
        ctx.restore()
        ea = seg(t, d + 0.4, d + 1.0)
        ctx.save()
        ctx.translate(540, 1350)
        ctx.scale(0.7, 0.7)
        hero_head(ctx, 0, 0, 120, emo("sly"), t, rim_a=ea, look=(0.5, 0))
        ctx.restore()
        ctx.rectangle(0, 0, W, H)
        fill(ctx, "#000", 1 - ea)


SCENES = [s0_bedroom, s1_street, s2_cafe, s3_crowd, s4_tv, s5_fun, s6_silence, s7_mannequin, s8_roof,
          s9_vibrate, s10_lock, s11_message, s12_final]
DAYS = {1: "ДЕНЬ 1", 2: "ДЕНЬ 1", 4: "ДЕНЬ 2", 6: "ДЕНЬ 21", 7: "ДЕНЬ 33", 8: "ДЕНЬ 40", 9: "НОЧЬ 40",
        10: "НОЧЬ 40", 11: "НОЧЬ 40", 12: "НОЧЬ 40"}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ======================================================================= ОВЕРЛЕИ
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
        CH = [chunks(l["words"]) for l in TL.lines]
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
        y = {11: 1600, 12: 1720}.get(li, 1480)
        ctx.save()
        ctx.translate(540, y)
        ctx.scale(lerp(0.6, 1, pop) * fit, lerp(0.6, 1, pop) * fit)
        x = -total / 2
        for w, wd, ww in zip(words, ch, widths):
            cur = wd["t"] - 0.03 <= u
            col = "#ffd400" if cur and u < wd["t"] + wd["d"] + 0.25 and wd is ch[-1] or (
                cur and u < wd["t"] + wd["d"]) else "#ffffff"
            text(ctx, w, x, 0, fs, col, "#000000", 16, align="left", shadow=True)
            x += ww + sp
        ctx.restore()
        break


def overlays(ctx, t, i):
    vignette(ctx, W, H, 0.5)
    if t < EV["end_card"]:
        rr(ctx, 50, 90, 200, 70, 35)
        fill(ctx, "#d8332a")
        text(ctx, "ЧАСТЬ 1", 150, 125, 38, "#ffffff")
    if i in DAYS and t < EV["end_card"]:
        a = seg(t, TL.shots[i][0], TL.shots[i][0] + 0.3)
        text(ctx, DAYS[i], W - 60, 125, 46, "#ffffff", "#000", 10, align="right", alpha=a)
    # хук-заголовок
    if t < 3.2:
        k1 = back_out(seg(t, 0.0, 0.35))
        out = 1 - seg(t, 2.85, 3.2)
        ctx.save()
        ctx.translate(540, 470)
        ctx.scale(k1, k1)
        ctx.push_group()
        text(ctx, "ЧТО, ЕСЛИ", 0, -150, 92, "#ffffff", "#000", 16, shadow=True)
        text(ctx, "ТЫ ОСТАЛСЯ ОДИН", 0, -20, 104, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -330, 70, 660, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "НА ЗЕМЛЕ?", 0, 135, 100, "#ffffff")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(out)
        ctx.restore()
    if t < EV["end_card"]:
        subtitles(ctx, t)


# ======================================================================= КАДР
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
    nxt = TRANS.get(i + 1)
    if nxt == "black" and t > b - 0.3:
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
