"""Авиа-модели высокой детализации: лайнер в профиль и диспетчерская башня снаружи."""
import math
import random

import cairo

from draw import TAU, ell, fill, glow, hexc, line, rr, src, text


def _lg(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *(hexc(c) if isinstance(c, str) else c))
    ctx.set_source(g)


def _fuselage_path(ctx):
    ctx.move_to(-760, -30)
    ctx.curve_to(-760, -80, -700, -112, -600, -116)
    ctx.line_to(520, -116)
    ctx.curve_to(650, -116, 740, -80, 780, -10)
    ctx.curve_to(790, 20, 760, 50, 690, 58)
    ctx.line_to(-560, 62)
    ctx.curve_to(-660, 60, -730, 40, -760, -30)
    ctx.close_path()


def airliner(ctx, x, y, s, t, gear=False, lit=True, tilt=0.0, contrail=False, cockpit_fn=None,
             landing_lights=None, livery="#1e3a8a", marks=True):
    """Лайнер в профиль, нос вправо. cockpit_fn(ctx) рисует содержимое кабины (окно ~ x 640..760, y -80..-40)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(tilt)
    ctx.scale(s, s)
    if landing_lights is None:
        landing_lights = gear
    if contrail:
        for k, yy in enumerate((40, 90)):
            g = cairo.LinearGradient(-3000, 0, -150, 0)
            g.add_color_stop_rgba(0, 1, 1, 1, 0)
            g.add_color_stop_rgba(1, 1, 1, 1, 0.55)
            ctx.set_source(g)
            ctx.rectangle(-3000, yy + 120 - 10 - k * 4, 2850, 16 + k * 10)
            ctx.fill()
    # --- дальние элементы: крыло, двигатель, стабилизатор
    ctx.move_to(-40, -40)
    ctx.line_to(-330, -230)
    ctx.line_to(-280, -240)
    ctx.line_to(180, -40)
    fill(ctx, "#7c8aa0")
    rr(ctx, -150, -150, 170, 60, 30)
    fill(ctx, "#64748b")
    ctx.move_to(-640, -70)
    ctx.line_to(-780, -160)
    ctx.line_to(-740, -165)
    ctx.line_to(-560, -70)
    fill(ctx, "#7c8aa0")
    # --- киль
    ctx.move_to(-600, -100)
    ctx.curve_to(-680, -200, -760, -340, -800, -400)
    ctx.line_to(-700, -400)
    ctx.curve_to(-640, -300, -560, -180, -420, -100)
    ctx.close_path()
    _lg(ctx, -800, 0, -420, 0, [(0, "#0f1f4d" if marks else "#e2e8f0"), (1, livery)])
    ctx.fill()
    line(ctx, -790, -380, -650, -130, 3, "#ffffff", 0.25)  # руль направления
    if marks:  # логотип на киле
        ctx.save()
        ctx.translate(-680, -270)
        ctx.arc(0, 0, 46, 0, TAU)
        fill(ctx, "#ffffff")
        ctx.arc(0, 0, 38, 0, TAU)
        fill(ctx, "#d8332a")
        ctx.move_to(-26, 10)
        ctx.curve_to(-6, -30, 14, -30, 30, -20)
        ctx.curve_to(10, -10, 0, 6, -26, 10)
        fill(ctx, "#ffffff")
        ctx.restore()
    if marks:
        text(ctx, "307", -710, -160, 40, "#ffffff")
    # --- фюзеляж
    _fuselage_path(ctx)
    _lg(ctx, 0, -116, 0, 62, [(0, "#ffffff"), (0.35, "#f1f5f9"), (0.7, "#cbd5e1"), (1, "#7c8aa0")])
    ctx.fill()
    ctx.save()
    _fuselage_path(ctx)
    ctx.clip()
    ctx.rectangle(-800, 18, 1600, 60)  # тёмное брюхо (ливрея)
    _lg(ctx, 0, 18, 0, 70, [(0, livery), (1, "#0b1530")])
    ctx.fill()
    ctx.rectangle(-800, 6, 1600, 10)
    fill(ctx, "#d8332a")
    line(ctx, -740, -100, 720, -100, 4, "#ffffff", 0.7)  # блик по верху
    for k in range(18):  # панельные швы
        xx = -560 + k * 72
        line(ctx, xx, -114, xx, 60, 1.5, "#94a3b8", 0.35)
    ctx.restore()
    if marks:
        text(ctx, "СКАЙЛАЙН", 160, -18, 34, livery)
    # двери
    for dx in (-560, 420):
        rr(ctx, dx, -96, 40, 98, 10)
        ctx.set_line_width(3)
        src(ctx, "#94a3b8")
        ctx.stroke()
        rr(ctx, dx + 8, -86, 24, 22, 8)
        fill(ctx, "#1e293b")
    rr(ctx, -60, -82, 30, 54, 8)  # аварийный выход над крылом
    ctx.set_line_width(2.5)
    src(ctx, "#94a3b8")
    ctx.stroke()
    # иллюминаторы
    for k in range(30):
        wx = -510 + k * 32
        if -575 < wx < -510 or -70 < wx < -20 or 410 < wx < 470:
            continue
        rr(ctx, wx, -76, 15, 22, 7)
        fill(ctx, "#ffd98a" if lit else "#1e293b")
        if lit:
            rr(ctx, wx + 2, -74, 5, 10, 3)
            fill(ctx, "#fff7d6", 0.8)
    # кабина пилотов
    ctx.move_to(640, -78)
    ctx.line_to(708, -76)
    ctx.line_to(752, -48)
    ctx.line_to(700, -44)
    ctx.line_to(640, -50)
    ctx.close_path()
    fill(ctx, "#0b1220")
    if cockpit_fn:
        ctx.save()
        ctx.move_to(640, -78)
        ctx.line_to(708, -76)
        ctx.line_to(752, -48)
        ctx.line_to(700, -44)
        ctx.line_to(640, -50)
        ctx.close_path()
        ctx.clip()
        cockpit_fn(ctx)
        ctx.restore()
    line(ctx, 690, -77, 680, -46, 4, "#cbd5e1")
    line(ctx, 728, -63, 716, -45, 3, "#cbd5e1")
    line(ctx, 650, -72, 700, -72, 2, "#ffffff", 0.35)
    # --- ближний стабилизатор
    ctx.move_to(-620, -20)
    ctx.line_to(-800, 60)
    ctx.line_to(-745, 70)
    ctx.line_to(-520, -10)
    ctx.close_path()
    _lg(ctx, 0, -20, 0, 70, [(0, "#e2e8f0"), (1, "#94a3b8")])
    ctx.fill()
    # --- ближнее крыло
    ctx.move_to(-130, 20)
    ctx.line_to(-460, 260)
    ctx.line_to(-380, 268)
    ctx.line_to(200, 34)
    ctx.close_path()
    _lg(ctx, 0, 20, 0, 268, [(0, "#e2e8f0"), (1, "#8b9ab0")])
    ctx.fill()
    line(ctx, -150, 60, -420, 250, 3, "#64748b", 0.6)  # закрылки
    line(ctx, -40, 50, -330, 250, 2, "#64748b", 0.4)
    ctx.move_to(-460, 260)  # винглет
    ctx.line_to(-500, 200)
    ctx.line_to(-470, 196)
    ctx.line_to(-430, 262)
    fill(ctx, livery)
    # пилон + двигатель
    ctx.move_to(-20, 40)
    ctx.line_to(60, 40)
    ctx.line_to(40, 96)
    ctx.line_to(-60, 96)
    fill(ctx, "#94a3b8")
    rr(ctx, -200, 80, 290, 110, 50)
    _lg(ctx, 0, 80, 0, 190, [(0, "#f8fafc"), (0.5, "#cbd5e1"), (1, "#64748b")])
    ctx.fill()
    rr(ctx, -200, 80, 290, 110, 50)
    ctx.set_line_width(2)
    src(ctx, "#64748b")
    ctx.stroke()
    ctx.move_to(-200, 110)
    ctx.line_to(-250, 124)
    ctx.line_to(-250, 148)
    ctx.line_to(-200, 162)
    fill(ctx, "#475569")
    ell(ctx, 88, 135, 22, 54)  # воздухозаборник
    fill(ctx, "#0f172a")
    ctx.save()
    ell(ctx, 88, 135, 18, 48)
    ctx.clip()
    for k in range(10):
        a = t * 30 + k * TAU / 10
        line(ctx, 88, 135, 88 + math.cos(a) * 6, 135 + math.sin(a) * 50, 3, "#64748b")
    ctx.restore()
    ell(ctx, 92, 135, 6, 12)
    fill(ctx, "#e2e8f0")
    text(ctx, "307", -60, 135, 26, "#64748b", alpha=0.6)
    # шасси
    if gear:
        for gx, n in ((-200, 2), (560, 1)):
            line(ctx, gx, 50, gx, 150, 12, "#475569")
            line(ctx, gx - 4, 60, gx + 30, 110, 5, "#64748b")
            for k in range(n):
                ctx.arc(gx + k * 52 - (26 if n == 2 else 0), 160, 26, 0, TAU)
                fill(ctx, "#111")
                ctx.arc(gx + k * 52 - (26 if n == 2 else 0), 160, 11, 0, TAU)
                fill(ctx, "#6b7280")
    # огни
    if landing_lights:
        g = cairo.LinearGradient(700, 30, 1700, 260)
        g.add_color_stop_rgba(0, 1, 0.98, 0.85, 0.55)
        g.add_color_stop_rgba(1, 1, 0.98, 0.85, 0)
        ctx.move_to(690, 20)
        ctx.line_to(1800, 140)
        ctx.line_to(1800, 420)
        ctx.close_path()
        ctx.set_source(g)
        ctx.fill()
        glow(ctx, 690, 26, 50, "#fff7cc", 1.0)
    on = (t * 1.1) % 1 < 0.1
    if on:
        glow(ctx, -470, 250, 90, "#ffffff", 1.0)
        glow(ctx, -790, -20, 60, "#ffffff", 0.9)
    glow(ctx, -470, 262, 30, "#22c55e", 0.8)
    b = 0.5 + 0.5 * math.sin(t * 7)
    glow(ctx, 0, -118, 45, "#ef4444", b)
    glow(ctx, 100, 64, 40, "#ef4444", 1 - b)
    ctx.restore()


def tower_ext(ctx, x, y, s, t=0.0, lit=False, moon_x=-1.0):
    """Диспетчерская башня снаружи (заброшенная). (x,y) — основание."""
    r = random.Random(7)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    # трава и забор
    for k in range(60):
        gx = r.uniform(-700, 700)
        line(ctx, gx, 0, gx + r.uniform(-12, 12), -r.uniform(20, 70), 4, "#1f3a2a")
    for k in range(-7, 8):
        line(ctx, k * 100, 0, k * 100, -170, 6, "#4b5563")
    for yy in (-60, -110, -160):
        line(ctx, -700, yy, 700, yy, 2, "#6b7280", 0.8)
    for k in range(-14, 15):  # колючая проволока
        ctx.arc(k * 50, -175, 10, 0, TAU)
        ctx.set_line_width(2)
        src(ctx, "#6b7280")
        ctx.stroke()
    # здание у основания
    rr(ctx, -380, -300, 760, 300, 6)
    _lg(ctx, -380, 0, 380, 0, [(0, "#2b2f38"), (0.4, "#3b414d"), (1, "#20242c")])
    ctx.fill()
    for k in range(6):
        wx = -330 + k * 110
        rr(ctx, wx, -240, 70, 90, 4)
        fill(ctx, "#0b1120")
        if k == 4 and lit:
            rr(ctx, wx, -240, 70, 90, 4)
            fill(ctx, "#fde68a", 0.5 + 0.5 * (math.sin(t * 13) > 0.6))
        line(ctx, wx + 35, -240, wx + 35, -150, 2, "#475569")
    rr(ctx, -40, -130, 80, 130, 4)
    fill(ctx, "#111827")
    rr(ctx, -120, -290, 240, 40, 4)
    fill(ctx, "#1f2937")
    text(ctx, "КДП", 0, -270, 30, "#9ca3af")
    # ствол башни
    ctx.move_to(-130, -300)
    ctx.line_to(-95, -1350)
    ctx.line_to(95, -1350)
    ctx.line_to(130, -300)
    ctx.close_path()
    _lg(ctx, -130, 0, 130, 0, [(0, "#4b5563") if moon_x < 0 else (0, "#1f2937"), (0.35, "#374151"),
                                (1, "#111827") if moon_x < 0 else (1, "#4b5563")])
    ctx.fill()
    for k in range(12):  # швы бетона
        yy = -380 - k * 85
        line(ctx, -128 + k * 2.8, yy, 128 - k * 2.8, yy, 2, "#1f2937", 0.8)
    for k in range(9):  # окна лестницы
        rr(ctx, -16, -420 - k * 105, 32, 56, 4)
        fill(ctx, "#0b1120")
    for k in range(4):  # подтёки ржавчины
        rx = r.uniform(-90, 60)
        ry = -r.uniform(500, 1200)
        ctx.move_to(rx, ry)
        ctx.curve_to(rx + 4, ry + 60, rx - 4, ry + 120, rx + 2, ry + r.uniform(150, 260))
        ctx.set_line_width(r.uniform(5, 10))
        src(ctx, "#7c2d12", 0.45)
        ctx.stroke()
    # балкон
    rr(ctx, -230, -1380, 460, 34, 4)
    fill(ctx, "#1f2937")
    for k in range(12):
        line(ctx, -220 + k * 40, -1380, -220 + k * 40, -1430, 3, "#475569")
    line(ctx, -230, -1430, 230, -1430, 5, "#475569")
    # стеклянная кабина (перевёрнутая трапеция)
    ctx.move_to(-240, -1440)
    ctx.line_to(240, -1440)
    ctx.line_to(300, -1650)
    ctx.line_to(-300, -1650)
    ctx.close_path()
    fill(ctx, "#0a1328")
    panes = 7
    for k in range(panes):
        f0, f1 = k / panes, (k + 1) / panes
        xb0, xb1 = -240 + 480 * f0, -240 + 480 * f1
        xt0, xt1 = -300 + 600 * f0, -300 + 600 * f1
        ctx.move_to(xb0 + 4, -1444)
        ctx.line_to(xb1 - 4, -1444)
        ctx.line_to(xt1 - 4, -1646)
        ctx.line_to(xt0 + 4, -1646)
        ctx.close_path()
        if k == 2:  # выбитое стекло
            fill(ctx, "#020409")
            ctx.move_to(xt0 + 4, -1646)
            ctx.line_to(xt0 + 40, -1600)
            ctx.line_to(xt0 + 20, -1560)
            ctx.line_to(xt0 + 50, -1520)
            ctx.line_to(xt0 + 4, -1500)
            fill(ctx, "#1e3a5f", 0.8)
        else:
            _lg(ctx, xt0, -1646, xb1, -1444, [(0, "#1e3a5f"), (0.5, "#0f1f3d"), (1, "#14284d")])
            ctx.fill()
            line(ctx, xt0 + 14, -1630, xb0 + 30, -1470, 3, "#94a3b8", 0.25)
            if k in (4, 5):  # трещины
                cx_, cy_ = (xt0 + xb1) / 2, -1560
                for j in range(6):
                    a = j * TAU / 6 + k
                    line(ctx, cx_, cy_, cx_ + math.cos(a) * 34, cy_ + math.sin(a) * 34, 2, "#cbd5e1", 0.7)
        line(ctx, xb0, -1440, xt0, -1650, 6, "#111827")
    line(ctx, -300, -1650, 300, -1650, 8, "#111827")
    # крыша, антенны, радар-купол
    ctx.move_to(-330, -1650)
    ctx.line_to(330, -1650)
    ctx.line_to(290, -1700)
    ctx.line_to(-290, -1700)
    fill(ctx, "#1f2937")
    line(ctx, -200, -1700, -200, -1860, 6, "#4b5563")
    for k in range(3):
        line(ctx, -240, -1760 - k * 30, -160, -1760 - k * 30, 4, "#4b5563")
    line(ctx, 60, -1700, 60, -1950, 5, "#4b5563")
    ctx.arc(170, -1760, 60, math.pi, TAU)
    _lg(ctx, 110, -1820, 230, -1760, [(0, "#e5e7eb"), (1, "#9ca3af")])
    ctx.fill()
    rr(ctx, 110, -1760, 120, 20, 4)
    fill(ctx, "#4b5563")
    if (t * 0.8) % 1 < 0.15:
        glow(ctx, 60, -1955, 50, "#ef4444", 0.8)
    ctx.restore()
