"""Серия 3 «Борт 307». Звук: голос по таймлайну + синтезированная музыка и шумовые эффекты -> build/mix.wav

Всё генерируется кодом (numpy/scipy), без сторонних сэмплов.
"""
import os
import subprocess

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

from common import ROOT, Timeline

SR = 48000
TL = Timeline()
EV = TL.ev
N = int((TL.total + 0.5) * SR)
rng = np.random.default_rng(7)


def T(sec):
    return np.arange(int(sec * SR)) / SR


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


def bp(x, f1, f2, order=2):
    return sosfilt(butter(order, [f1, f2], "band", fs=SR, output="sos"), x)


def add(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n] * gain


def env(n, a=0.005, r=None):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    if r:
        nr = min(n, int(r * SR))
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def reverb(x, sec=1.6, mix=0.3):
    t = T(sec)
    ir = rng.standard_normal(len(t)) * np.exp(-t * 5.0 / sec)
    ir = lp(ir, 5000)
    ir /= np.sqrt(np.sum(ir ** 2))
    wet = fftconvolve(x, ir)[:len(x)]
    return x * (1 - mix) + wet * mix


def note(f, dur, kind="pluck", amp=1.0):
    t = T(dur)
    if kind == "pluck":
        s = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) + 0.15 * np.sin(6 * np.pi * f * t))
        s *= np.exp(-t * 4.5)
    elif kind == "bell":
        s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3)
        s *= np.exp(-t * 1.6)
    elif kind == "piano":
        s = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.6 for k in range(1, 6)) * np.exp(-t * 2.2)
    elif kind == "bass":
        s = np.sin(2 * np.pi * f * t) + 0.3 * np.sign(np.sin(2 * np.pi * f * t)) * 0.3
        s = lp(s, 400) * np.exp(-t * 3)
    return s * env(len(t), 0.004, 0.05) * amp


def pad(freqs, dur, amp=0.2, bright=900):
    t = T(dur)
    s = np.zeros(len(t))
    for f in freqs:
        for det in (-0.6, 0.0, 0.7):
            ph = rng.uniform(0, 6.28)
            s += np.sin(2 * np.pi * (f + det) * t + ph) + 0.25 * np.sin(2 * np.pi * 2 * (f + det) * t + ph)
    s = lp(s, bright)
    s *= 1 + 0.15 * np.sin(2 * np.pi * 0.2 * t)
    s *= env(len(t), 1.5, 1.5)
    return s / (len(freqs) * 3) * amp


def hz(n):  # midi -> Гц
    return 440 * 2 ** ((n - 69) / 12)


# ------------------------------------------------------------------ эффекты
def whoosh(d=0.4):
    n = rng.standard_normal(int(d * SR))
    t = T(d)
    out = np.zeros_like(n)
    for k, (a, b) in enumerate(((300, 900), (900, 2500), (2500, 5000), (900, 2500))):
        seg = slice(int(len(n) * k / 4), int(len(n) * (k + 1) / 4))
        out[seg] = bp(n, a, b)[seg]
    out = lp(out, 4000)
    return out * np.sin(np.pi * t / d) ** 2 * 0.9


def boom(d=1.6, f0=70):
    t = T(d)
    f = f0 * np.exp(-t * 1.4) + 30
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    s += lp(rng.standard_normal(len(t)), 300) * np.exp(-t * 8) * 0.6
    return s * env(len(t), 0.002)


def hit(d=0.9):
    t = T(d)
    s = boom(d, 90) * 0.8 + hp(rng.standard_normal(len(t)), 2000) * np.exp(-t * 18) * 0.5
    return s


def zap(d=0.9):
    t = T(d)
    f = 1800 * np.exp(-t * 4) + 80
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3
    s += (rng.random(len(t)) < 0.02) * rng.standard_normal(len(t))
    return lp(s, 6000) * np.exp(-t * 2.5)


def glitch(d=0.25):
    t = T(d)
    s = np.repeat(rng.standard_normal(int(len(t) / 60) + 1), 60)[:len(t)]
    return hp(s, 300) * 0.5 * env(len(t), 0.002, 0.03)


def buzz(d=0.5):
    t = T(d)
    s = np.sign(np.sin(2 * np.pi * 165 * t)) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t))
    s = lp(s, 900) * 0.5
    return s * env(len(t), 0.01, 0.05)


def step(loud=1.0):
    t = T(0.5)
    s = np.sin(2 * np.pi * 62 * t) * np.exp(-t * 18) * 1.1
    s += lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 35) * 0.8
    s += hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 90) * 0.15
    return s * loud


def heartbeat():
    t = T(0.6)
    one = np.sin(2 * np.pi * 50 * t) * np.exp(-t * 22)
    out = np.zeros(int(0.9 * SR))
    out[:len(one)] += one
    out[int(0.22 * SR):int(0.22 * SR) + len(one)] += one * 0.7
    return lp(out, 200)


def click():
    t = T(0.03)
    return hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 300) * 0.4


def engine(d):
    t = T(d)
    f = 38 + 2 * np.sin(2 * np.pi * 0.7 * t)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + lp(rng.standard_normal(len(t)), 200) * 0.6
    return lp(s, 260) * env(len(t), 0.4, 0.4)


def vroom(d=2.0):
    t = T(d)
    f = 60 + 160 * (1 - np.exp(-t * 2))
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 2) / SR)
    return lp(s, 1200) * 0.35 * env(len(t), 0.05, 0.5)


def wind(d):
    s = lp(rng.standard_normal(int(d * SR)), 500)
    t = T(d)
    return s * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t)) * env(len(t), 1.0, 1.0)


def roller(d):
    t = T(d)
    s = bp(rng.standard_normal(len(t)), 400, 1800) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 1.6 * t)))
    return s * env(len(t), 0.2, 0.3) * 0.5


def tick(loud=1.0):
    t = T(0.05)
    return hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 160) * 0.5 * loud


def knock():
    t = T(0.9)
    s = np.sin(2 * np.pi * 95 * t) * np.exp(-t * 14) * 1.3
    s += lp(rng.standard_normal(len(t)), 700) * np.exp(-t * 40) * 1.0
    s += np.sin(2 * np.pi * 210 * t) * np.exp(-t * 25) * 0.4
    return s


def creak(d=2.4):
    t = T(d)
    f = 180 + 60 * np.sin(2 * np.pi * 0.6 * t) + 30 * np.sin(2 * np.pi * 7 * t)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (rng.random(len(t)) < 0.35)
    return bp(s, 300, 2500) * 0.35 * env(len(t), 0.3, 0.4)


def sting():
    t = T(2.0)
    s = sum(np.sin(2 * np.pi * f * t) for f in (hz(72), hz(73), hz(78), hz(79))) * np.exp(-t * 1.5) * 0.25
    return s + boom(2.0, 60) * 0.6


def cash():
    t = T(0.6)
    s = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 6) for f in (2093, 2637, 3136)) * 0.3
    return s + hp(rng.standard_normal(len(t)), 5000) * np.exp(-t * 20) * 0.2


def radio_fx(x):
    """Голос «по рации»: полоса 300–3000 Гц, лёгкий перегруз, шипение."""
    y = bp(x, 300, 3000, 3)
    y = np.tanh(y * 3.5) / np.tanh(3.5)
    y += hp(rng.standard_normal(len(y)), 2000) * 0.015 * (np.abs(y) > 0.01)
    return y * 0.9


def squelch():
    t = T(0.35)
    s = hp(rng.standard_normal(len(t)), 1500) * 0.4 * env(len(t), 0.005, 0.1)
    s[:int(0.06 * SR)] += np.sin(2 * np.pi * 1200 * T(0.06)) * 0.3
    return s


def jet(d):
    t = T(d)
    s = lp(rng.standard_normal(len(t)), 300) * 1.2 + bp(rng.standard_normal(len(t)), 1500, 4000) * 0.15
    s += np.sin(2 * np.pi * 55 * t) * 0.2
    return s * env(len(t), 0.5, 0.5)


def alarm(d):
    t = T(d)
    gate = ((t * 2.5) % 1) < 0.5
    s = np.sign(np.sin(2 * np.pi * 880 * t)) * 0.25 * gate
    return lp(s, 3000) * env(len(t), 0.01, 0.05)


def thunder():
    t = T(3.0)
    s = lp(rng.standard_normal(len(t)), 180) * np.exp(-t * 1.2) * 2.0
    s += lp(rng.standard_normal(len(t)), 1200) * np.exp(-t * 8) * 0.6
    return s


def screech(d=1.6):
    t = T(d)
    f = 1400 + 300 * np.sin(2 * np.pi * 5 * t)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 + bp(rng.standard_normal(len(t)), 1500, 5000) * 0.6
    return s * np.exp(-t * 1.5) * env(len(t), 0.01)


def applause(d):
    out = np.zeros(int(d * SR))
    for k in range(int(d * 90)):
        c = hp(rng.standard_normal(int(0.03 * SR)), 1200) * np.exp(-T(0.03) * 120)
        i = rng.integers(0, len(out) - len(c))
        out[i:i + len(c)] += c * rng.uniform(0.2, 0.6)
    return out * env(len(out), 0.3, 0.8)


def gust(d):
    t = T(d)
    s = bp(rng.standard_normal(len(t)), 200, 900) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t) ** 2)
    return s * env(len(t), 1.0, 1.0)


# ------------------------------------------------------------------ сборка
def build():
    voice = np.zeros(N)
    music = np.zeros(N)
    sfx = np.zeros(N)
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    for l in TL.lines:
        wav = os.path.join(ROOT, "build", f"line{l['i']:02d}.wav")
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(ROOT, l["file"]),
                               "-ac", "1", "-ar", str(SR), wav])
        sr, x = wavfile.read(wav)
        x = x.astype(np.float64) / 32768
        if l.get("spk") == "R":
            x = radio_fx(x)
        add(voice, x, l["start"], 1.0)
    voice = hp(voice, 80)
    voice = reverb(voice, 0.5, 0.06)
    S = TL.shots
    ev = TL.ev

    # двигатели: весь полёт до посадки
    add(sfx, jet(ev["impact"] + 1.0), 0.0, 0.35)
    for lt in ev["lightning"]:
        add(sfx, thunder(), lt + 0.15, 0.7)
    a0, a1 = ev["alarm"]
    add(sfx, alarm(a1 - a0), a0, 0.35)
    for r_ in ev["radio"]:
        add(sfx, squelch(), r_ - 0.25, 0.8)
    for c in ev["cmd"]:
        add(sfx, hit(0.6), c, 0.35)
    add(sfx, glitch(0.25), ev["cmd"][2] + 0.6, 0.4)  # шасси вышли
    add(sfx, boom(1.8, 60), ev["impact"], 1.0)
    add(sfx, screech(2.0), ev["sparks"] - 0.1, 0.6)
    add(sfx, applause(4.5), ev["applause"][0] - 0.2, 0.7)
    for tt in np.arange(ev["run"][0] + 0.2, ev["run"][1] - 0.2, 0.32):
        add(sfx, step(0.4), tt, 0.4)
    add(sfx, gust(TL.total - S[10][0]), S[10][0], 0.25)
    add(sfx, sting(), ev["photo"], 0.6)
    add(sfx, squelch(), ev["hiss"], 1.0)
    for w in ev["whoosh"]:
        add(sfx, whoosh(), w - 0.15, 0.45)
    for h in ev["hit"]:
        add(sfx, hit(), h, 0.5)
    d = ev["end_card"]
    add(sfx, boom(2.5, 50), d, 0.9)
    add(sfx, note(hz(81), 2.5, "bell", 0.3), d + 0.4)

    # музыка: тревога в воздухе -> пульс во время посадки -> тишина -> жуть в башне
    add(music, pad([hz(38), hz(45), hz(50)], ev["alarm"][0] + 1.0, 0.5, 600), 0.0)
    a, b = ev["alarm"][0], ev["silence"]
    tt, k = a, 0
    while tt < b:
        add(music, note(hz(33), 0.3, "bass", 0.6), tt)
        if k % 2 == 0:
            add(music, note(hz(69 + (k // 8) % 3), 0.25, "pluck", 0.12), tt)
        tt += 0.5 - 0.15 * (tt - a) / (b - a)
        k += 1
    add(music, pad([hz(55), hz(59), hz(62), hz(67)], 5.0, 0.4, 900), ev["applause"][0] - 1.0)
    a = S[10][0]
    dr = pad([hz(31), hz(32), hz(43)], ev["end_card"] - a, 0.6, 300)
    dr *= np.linspace(0.5, 1.3, len(dr))
    dr[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    add(music, dr, a)
    tt = S[11][0]
    while tt < ev["end_card"] - 0.3:
        add(sfx, heartbeat(), tt, 0.8)
        tt += 0.8

    venv = lp(np.abs(voice), 4)
    venv = np.clip(venv / (venv.max() * 0.25 + 1e-9), 0, 1)
    duck = 1 - 0.55 * venv
    mix = voice * 1.0 + music * 0.5 * duck + sfx * 0.6 * (1 - 0.35 * venv)
    mix /= np.max(np.abs(mix)) * 1.05
    out = os.path.join(ROOT, "build", "mix_raw.wav")
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-af",
                           "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), os.path.join(ROOT, "build", "mix.wav")])
    print("audio ->", os.path.join(ROOT, "build", "mix.wav"), round(N / SR, 2), "s")


if __name__ == "__main__":
    build()
