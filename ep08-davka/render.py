"""Серия 8 «Давка» (что делать): python3 render.py [--stills shots|t1,t2] [--jobs 4]"""
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






# ================================================================== КОНЦЕРТ
COL_A = "#a855f7"
COL_B = "#e5e7eb"      # голос человека в чёрном
OK = "#22c55e"
NO = "#ef4444"


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
    """Плашка шага сверху: «ШАГ N» + короткое правило + галочка/крест."""
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


def stage_bg(ctx, t, lights=1.0, music=1.0):
    vgrad(ctx, -1500, -1200, 4000, 4200, [(0, "#0a0614"), (1, "#1a0b2e")])
    # сцена, фермы, экран
    rr(ctx, -400, 180, 1880, 520, 10)
    fill(ctx, "#07040c")
    for x in (-380, 1440):
        rr(ctx, x, -200, 40, 900, 4)
        fill(ctx, "#27272a")
        for k in range(9):
            line(ctx, x, -200 + k * 100, x + 40, -150 + k * 100, 3, "#52525b")
    rr(ctx, -400, -220, 1880, 40, 4)
    fill(ctx, "#27272a")
    rr(ctx, 140, 230, 800, 420, 10)
    fill(ctx, "#111827")
    ctx.save()
    rr(ctx, 150, 240, 780, 400, 6)
    ctx.clip()
    vgrad(ctx, 150, 240, 780, 400, [(0, "#7c3aed"), (1, "#db2777")])
    for k in range(18):  # эквалайзер
        h = (0.3 + 0.7 * abs(math.sin(t * 6 + k * 0.7))) * 300 * music
        rr(ctx, 170 + k * 42, 630 - h, 30, h, 4)
        fill(ctx, "#ffffff", 0.7)
    ctx.restore()
    # прожекторы и лазеры
    for k in range(7):
        x = -300 + k * 280
        a = math.sin(t * 1.3 + k) * 0.5
        col = ["#a855f7", "#22d3ee", "#f472b6", "#facc15"][k % 4]
        ctx.move_to(x, -180)
        ctx.line_to(x + math.sin(a - 0.12) * 2600, -180 + math.cos(a - 0.12) * 2600)
        ctx.line_to(x + math.sin(a + 0.12) * 2600, -180 + math.cos(a + 0.12) * 2600)
        ctx.close_path()
        fill(ctx, col, 0.12 * lights)
        ctx.arc(x, -180, 26, 0, TAU)
        fill(ctx, col, lights)
    for k in range(5):
        a = math.sin(t * 2.1 + k * 1.3) * 0.9
        line(ctx, 540, 200, 540 + math.sin(a) * 3000, 200 + math.cos(a) * 3000, 4, "#22c55e", 0.5 * lights * music)
    for k in range(6):  # дым
        ell(ctx, (k * 500 + t * 30) % 2600 - 700, 760, 520, 120)
        fill(ctx, "#c4b5fd", 0.06)
    # ограждение у сцены
    rr(ctx, -400, 760, 1880, 70, 6)
    fill(ctx, "#3f3f46")
    for k in range(-4, 16):
        line(ctx, k * 120, 760, k * 120, 830, 8, "#52525b")


CROWD8 = None


def crowd8():
    global CROWD8
    if CROWD8 is None:
        r = random.Random(808)
        CROWD8 = []
        for row, (y, sc, n) in enumerate(((1200, 0.75, 10), (1380, 0.9, 9), (1580, 1.05, 8), (1800, 1.2, 7))):
            for i in range(n):
                x = -380 + i * (1840 / n) + r.uniform(-40, 40) + (row % 2) * 60
                if row == 2 and abs(x - 540) < 120:
                    continue  # место героя
                p = Npc(r, x, y, sc, r.choice((-1, 1)))
                p.item = "none"
                p.row = row
                CROWD8.append(p)
    return CROWD8


def draw_crowd(ctx, t, squeeze=0.0, back=False, turn=None, clap=False, sway=1.0, freeze=None, hero_fn=None,
               cheer=True):
    """squeeze 0..1 — толпа сжимается к центру; turn(t, p) -> 0..1 поворот к камере."""
    tt = t if freeze is None else min(t, freeze)
    drawn_hero = False
    for p in sorted(crowd8(), key=lambda q: q.y):
        if hero_fn and not drawn_hero and p.row >= 3:
            hero_fn()
            drawn_hero = True
        ox = (540 - p.x) * 0.22 * squeeze + math.sin(tt * 2 + p.seed) * 12 * sway
        oy = -abs(math.sin(tt * 4 + p.seed)) * 18 * sway * (0 if freeze is not None and t > freeze else 1)
        x0, y0 = p.x, p.y
        p.x, p.y = x0 + ox, y0 + oy
        tk = turn(t, p) if turn else 0.0
        if tk < 1:
            npc(ctx, p, tt, walking=False, back=back, clap=(cheer and not back and int(p.seed) % 2 == 0),
                alpha=1 - tk if tk > 0 else 1)
        if tk > 0:
            npc(ctx, p, tt, walking=False, stare=1.0, clap=clap, alpha=tk)
        p.x, p.y = x0, y0
    if hero_fn and not drawn_hero:
        hero_fn()


def concert_front(ctx, t, squeeze=0.0, hero_kw=None, cheer=True):
    """Вид со сцены на толпу: лица к камере, в центре герой."""
    vgrad(ctx, -1500, -1200, 4000, 4200, [(0, "#1a0b2e"), (1, "#0a0614")])
    for k in range(7):
        x = -300 + k * 280
        a = math.sin(t * 1.3 + k) * 0.6
        ctx.move_to(540, -400)
        ctx.line_to(x + math.sin(a) * 600, 2400)
        ctx.line_to(x + math.sin(a) * 600 + 260, 2400)
        ctx.close_path()
        fill(ctx, ["#a855f7", "#22d3ee", "#f472b6", "#facc15"][k % 4], 0.08)
    ctx.rectangle(-1500, 2000, 4000, 1000)
    fill(ctx, "#0a0614")
    hk = hero_kw or {}

    def hf():
        hero(ctx, 540, hk.get("y", 1780), hk.get("sc", 1.15), hk.get("e", emo("fear")), t,
             arms=hk.get("arms", "down"), rim="#a855f7", rim_a=0.8, look=hk.get("look", (0, 0)),
             tremble=hk.get("tremble", 0.4), tilt=hk.get("tilt", 0.0), legs=hk.get("legs", True))
    draw_crowd(ctx, t, squeeze, back=False, hero_fn=hf, cheer=cheer)


# ================================================================== СЦЕНЫ
def s0_hook(ctx, t, u, D):
    ctx.save()
    cam(ctx, t, 540, lerp(1000, 1150, ease(seg(u, 0, D))), lerp(0.8, 0.95, seg(u, 0, D)), shake=0.4)
    stage_bg(ctx, t)
    draw_crowd(ctx, t, 0.0, back=True, hero_fn=lambda: hero(ctx, 540, 1640, 1.0, emo("happy"), t, arms="cheer",
                                                              back=True, rim="#a855f7", rim_a=0.6))
    ctx.restore()


def s1_surge(ctx, t, u, D):
    sq = ease(seg(t, EV["surge"] - 0.3, EV["surge"] + 1.2))
    ctx.save()
    cam(ctx, t, 540, 1350, lerp(0.95, 1.25, ease(seg(u, 0, D))), shake=0.5 + 1.2 * sq)
    concert_front(ctx, t, sq, dict(e=emo("fear"), arms="down", tremble=1.0), cheer=False)
    ctx.restore()
    if sq > 0.5:  # «нечем дышать»
        for k in range(3):
            a = (t * 1.5 + k / 3) % 1
            ctx.arc(700 + k * 30, 900 - a * 200, 10 + a * 20, 0, TAU)
            ctx.set_line_width(4)
            src(ctx, "#ffffff", 0.6 * (1 - a))
            ctx.stroke()


def s2_boxer(ctx, t, u, D):
    st = EV["steps"][0]
    k = ease(seg(t, st + 0.4, st + 1.0))
    ctx.save()
    cam(ctx, t, 540, 1300, lerp(1.25, 1.45, ease(seg(u, 0, D))), shake=0.5)
    concert_front(ctx, t, 0.9, dict(e=emo("fear", "determined", k), arms=arms_lerp("down", "hug", k),
                                    tremble=0.6 * (1 - k)), cheer=False)
    ctx.restore()
    step_card(ctx, t, st, 1, "РУКИ К ГРУДИ\nКАК У БОКСЁРА")
    if k > 0.5:  # схема: место для вдоха
        ctx.arc(540, 1090, 150, 0, TAU)
        ctx.set_dash([18, 12])
        ctx.set_line_width(6)
        src(ctx, OK, 0.8)
        ctx.stroke()
        ctx.set_dash([])


def s3_diagonal(ctx, t, u, D):
    st = EV["steps"][1]
    k = ease(seg(t, st + 1.0, TL.shots[4][0]))
    ctx.save()
    cam(ctx, t, lerp(540, 820, k), 1300, 1.1, shake=0.5)
    concert_front(ctx, t, 0.7, dict(e=emo("determined"), arms="hug", tremble=0.3), cheer=False)
    ctx.restore()
    step_card(ctx, t, st, 2, "С ТОЛПОЙ\nНАИСКОСОК К КРАЮ")
    # стрелки: против толпы — нет, наискосок — да
    a = seg(t, st + 0.8, st + 1.2)
    if a > 0:
        ctx.save()
        ctx.translate(540, 1150)
        line(ctx, 0, 0, 0, -260, 18, NO, a)
        crossmark(ctx, 0, -300, 1.0)
        line(ctx, 40, 20, 300, -200, 18, OK, a)
        ctx.move_to(330, -230)
        ctx.line_to(260, -220)
        ctx.line_to(320, -160)
        ctx.close_path()
        fill(ctx, OK, a)
        ctx.restore()


def feet_floor(ctx, t, phone_k, hand_k):
    vgrad(ctx, -1200, -800, 3600, 3600, [(0, "#1c1917"), (1, "#0c0a09")])
    r = random.Random(2)
    for i in range(16):  # ноги толпы
        x = r.uniform(-200, 1300)
        y = r.uniform(800, 1700)
        sw = math.sin(t * 5 + i) * 30
        line(ctx, x + sw, -200, x + sw * 0.5, y, 60, r.choice(PANTS))
        ell(ctx, x + sw * 0.5 + 20, y + 20, 60, 28)
        fill(ctx, r.choice(["#111", "#f8fafc", "#7c2d12", "#1d4ed8"]))
    # телефон падает и светится
    py = lerp(300, 1300, ease_in(phone_k, 2))
    ctx.save()
    ctx.translate(560, py)
    ctx.rotate(phone_k * 4)
    rr(ctx, -60, -110, 120, 220, 16)
    fill(ctx, "#111")
    rr(ctx, -52, -100, 104, 200, 10)
    fill(ctx, "#38bdf8")
    ctx.restore()
    glow(ctx, 560, py, 200, "#38bdf8", 0.4)
    # рука тянется и останавливается
    hx = 540
    hy = lerp(-200, 700, hand_k)
    line(ctx, hx - 200, -400, hx, hy, 90, HOOD)
    ctx.arc(hx, hy, 55, 0, TAU)
    fill(ctx, HEAD)


def s4_phone(ctx, t, u, D):
    pd = EV["phone_drop"]
    pk = seg(t, pd - 0.1, pd + 0.8)
    hand = ease(seg(t, pd + 0.6, pd + 1.2)) * (1 - ease(seg(t, pd + 1.6, pd + 2.2)))
    ctx.save()
    cam(ctx, t, 540, 960, lerp(1.0, 1.1, seg(u, 0, D)), shake=0.5)
    feet_floor(ctx, t, pk, hand)
    ctx.restore()
    step_card(ctx, t, EV["steps"][2], 3, "НЕ НАКЛОНЯЙСЯ\nЗА ВЕЩАМИ", good=False)
    if hand > 0.3:
        crossmark(ctx, 540, 1250, 2.0)


def s5_fall(ctx, t, u, D):
    fa = EV["fall"]
    cu = EV["curl"]
    ctx.save()
    if t < cu:
        f = ease(seg(t, fa - 0.4, fa)) * (1 - ease(seg(t, fa + 0.3, fa + 0.9)))
        cam(ctx, t, 540, 1350, 1.15, shake=0.6)
        concert_front(ctx, t, 0.6, dict(e=emo("shock") if f > 0.3 else emo("determined"), arms="hug",
                                        tilt=-1.3 * f, y=1780 + 160 * f), cheer=False)
    else:  # схема: на боку, голова закрыта руками
        cam(ctx, t, 540, 1000, 1.0, shake=0.3)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#1f2937"), (1, "#0b0f16")])
        rr(ctx, 120, 560, 840, 760, 40)
        fill(ctx, "#f8fafc", 0.06)
        ctx.save()
        ctx.translate(560, 1050)
        ctx.rotate(-1.5)
        hero(ctx, 0, 0, 0.9, emo("fear"), t, arms="shock", knees=True, legs=False, rim="#22c55e", rim_a=0.8)
        ctx.restore()
        checkmark(ctx, 880, 650, 1.5, OK, seg(t, cu + 0.3, cu + 0.8))
        text(ctx, "НА БОКУ", 540, 1420, 60, OK, "#000", 8)
        text(ctx, "ГОЛОВА ЗАКРЫТА", 540, 1500, 60, OK, "#000", 8)
    ctx.restore()
    step_card(ctx, t, EV["steps"][3], 4, "УПАЛ — СРАЗУ\nВСТАВАЙ")


def s6_exit(ctx, t, u, D):
    ex = EV["exit"]
    ctx.save()
    cam(ctx, t, lerp(540, 900, ease(seg(t, ex - 0.3, ex + 1.0))), 1250, 1.05, shake=0.4)
    concert_front(ctx, t, 0.4, dict(e=emo("calm"), arms="hug", look=(0.9, -0.5), tremble=0.0), cheer=False)
    # знак выхода справа
    rr(ctx, 1150, 700, 360, 140, 10)
    fill(ctx, "#16a34a")
    glow(ctx, 1330, 770, 300, "#22c55e", 0.6)
    text(ctx, "ВЫХОД", 1330, 770, 70, "#ffffff")
    # ограждение слева с крестом
    rr(ctx, -400, 1500, 300, 400, 10)
    fill(ctx, "#52525b")
    for k in range(5):
        line(ctx, -380 + k * 60, 1500, -380 + k * 60, 1900, 8, "#3f3f46")
    crossmark(ctx, -250, 1450, 1.6)
    ctx.restore()
    step_card(ctx, t, EV["steps"][4], 5, "БЕРЕГИ СИЛЫ\nИЩИ ВЫХОД")


def s7_score(ctx, t, u, D):
    sc = EV["score"]
    ctx.save()
    cam(ctx, t, 540, 960, 1.0, shake=0.2)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#0f172a"), (1, "#020617")])
    text(ctx, "ПРОВЕРКА", 540, 330, 100, "#ffffff", "#000", 12)
    items = ["РУКИ У ГРУДИ", "НАИСКОСОК К КРАЮ", "ТЕЛЕФОН ОСТАВИЛ", "УСТОЯЛ", "БЕРЁГ СИЛЫ"]
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


def s8_hundred(ctx, t, u, D):
    tt = EV["total"]
    ctx.save()
    cam(ctx, t, 540, 1150, lerp(0.95, 1.1, seg(u, 0, D)), shake=0.25)
    stage_bg(ctx, t)
    draw_crowd(ctx, t, 0.0, back=True)
    hero(ctx, 540, 1900, 1.3, emo("happy"), t, arms="cheer", rim="#22c55e", rim_a=0.9)
    ctx.restore()
    s = back_out(seg(t, tt - 0.1, tt + 0.3))
    if s > 0:
        ctx.save()
        ctx.translate(540, 560)
        ctx.scale(max(0.02, s), max(0.02, s))
        text(ctx, "100/100", 0, 0, 200, "#22c55e", "#000", 20, shadow=True)
        ctx.restore()


def turn_fn(t, p):
    t0 = EV["turn"] + (p.seed % 1) * 0.0 + ((int(p.seed * 10) % 7) * 0.04)
    return ease(seg(t, t0, t0 + 0.3))


def s9_freeze(ctx, t, u, D):
    st = EV["stop"]
    music = 0.0 if t > st else 1.0
    ctx.save()
    cam(ctx, t, 540, 1250, lerp(0.95, 1.2, ease(seg(t, EV["turn"], TL.shots[10][0]))), shake=0.2)
    stage_bg(ctx, t, lights=0.4 if t > st else 1.0, music=music)
    draw_crowd(ctx, t, 0.0, back=True, turn=turn_fn, freeze=st, sway=0 if t > st else 1)
    hero(ctx, 540, 2150, 1.4, emo("fear"), t, arms="down", back=True, rim="#a855f7", rim_a=0.6, legs=False)
    ctx.restore()


def s10_clap(ctx, t, u, D):
    cl = EV["clap"]
    ac = EV["actors"]
    ctx.save()
    cam(ctx, t, 540, 1300, lerp(1.0, 1.1, seg(u, 0, D)), shake=0.25)
    stage_bg(ctx, t, lights=0.5, music=0.0)
    for p in sorted(crowd8(), key=lambda q: q.y):
        npc(ctx, p, t, walking=False, stare=1.0, clap=t > cl + (int(p.seed * 10) % 5) * 0.15,
            grin=0.5 if t > ac else 0.0)
    hero(ctx, 540, 2150, 1.4, emo("shock"), t, arms="down", back=True, rim="#a855f7", rim_a=0.6, legs=False)
    ctx.restore()
    if t > ac:
        rr(ctx, 160, 300, 760, 150, 30)
        fill(ctx, "#000", 0.8)
        text(ctx, "ЭТО БЫЛИ АКТЁРЫ", 540, 375, 66, "#facc15")


def man_in_black(x, y, sc):
    p = Npc(random.Random(7007), x, y, sc, -1)
    p.shirt, p.pants, p.style, p.hair, p.item = "#0a0a0a", "#0a0a0a", "short", "#111", "none"
    p.glasses, p.headphones, p.beard, p.mustache, p.collar, p.print_ = True, True, False, False, "shirt", None
    p.skin = "#d6b08c"
    return p


def badge7(ctx, x, y, s, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.rotate(math.sin(t * 1.5) * 0.05)
    line(ctx, -60, -260, 0, -120, 8, "#111")
    line(ctx, 60, -260, 0, -120, 8, "#111")
    rr(ctx, -150, -120, 300, 200, 16)
    fill(ctx, "#f8fafc")
    rr(ctx, -150, -120, 300, 60, 16)
    fill(ctx, "#111")
    text(ctx, "КАНДИДАТ", 0, -90, 34, "#ffffff")
    text(ctx, "№7", 0, -10, 70, "#111")
    text(ctx, "100/100", 0, 50, 40, OK)
    ctx.restore()


def s11_badge(ctx, t, u, D):
    bd = EV["badge"]
    ctx.save()
    cam(ctx, t, 540, lerp(1150, 1100, seg(u, 0, D)), lerp(1.0, 1.3, ease(seg(t, bd - 0.5, bd + 1.0))), shake=0.25)
    vgrad(ctx, -800, -800, 2700, 3600, [(0, "#18181b"), (1, "#09090b")])
    # фургон на фоне
    rr(ctx, -300, 600, 900, 520, 40)
    fill(ctx, "#111")
    rr(ctx, 400, 680, 180, 420, 6)
    fill(ctx, "#fde68a", 0.25)
    for wx in (-160, 420):
        ctx.arc(wx, 1120, 70, 0, TAU)
        fill(ctx, "#050505")
    p = man_in_black(840, 1950, 1.5)
    npc(ctx, p, t, walking=False)
    hero(ctx, 330, 1950, 1.25, emo("worry", "shock", seg(t, bd, bd + 0.3)), t, arms="down", rim="#facc15",
         rim_a=0.6, look=(0.8, 0))
    if t > bd - 0.3:
        badge7(ctx, 330, lerp(1100, 1490, ease(seg(t, bd - 0.3, bd + 0.3))), 0.75, t)
    ctx.restore()


def s12_final(ctx, t, u, D):
    ec = EV["end_card"] - TL.shots[12][0]
    ctx.save()
    if u < ec:
        cam(ctx, t, 600, 1100, lerp(1.4, 1.7, seg(u, 0, ec)), shake=0.2)
        vgrad(ctx, -800, -800, 2700, 3600, [(0, "#18181b"), (1, "#09090b")])
        p = man_in_black(620, 1950, 2.0)
        npc(ctx, p, t, walking=False, grin=0.3)
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
        text(ctx, "Куда тебя везут?", 0, 180, 70, "#facc15")
    ctx.restore()


SCENES = [s0_hook, s1_surge, s2_boxer, s3_diagonal, s4_phone, s5_fall, s6_exit, s7_score, s8_hundred, s9_freeze,
          s10_clap, s11_badge, s12_final]
LABELS = {}


def draw_scene(ctx, i, t):
    a, b = TL.shots[i]
    ctx.save()
    SCENES[i](ctx, t, t - a, b - a)
    ctx.restore()


# ================================================================== СУБТИТРЫ
MERGE = [(("пять",), "5"), (("двадцать",), "20"), (("сто", "из", "ста"), "100/100"), (("двести",), "200")]


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
        text(ctx, "ТЫ ПОПАЛ", 0, 10, 116, "#ffd400", "#000", 18, shadow=True)
        rr(ctx, -300, 90, 600, 130, 22)
        fill(ctx, "#d8332a")
        text(ctx, "В ДАВКУ?", 0, 155, 100, "#ffffff")
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
