"""Серия 23 «Лифт с незнакомцем». Звук: голос по таймлайну + синтезированная музыка и шумовые эффекты -> build/mix.wav

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


def tray_crash():
    t = T(1.2)
    s = hp(rng.standard_normal(len(t)), 1500) * np.exp(-t * 9) * 0.8
    for f in (1800, 2400, 3100):
        s += np.sin(2 * np.pi * f * t) * np.exp(-t * 7) * 0.25
    return s


def power_down():
    t = T(1.4)
    f = 220 * np.exp(-t * 2.5) + 30
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.5) * 0.6
    return s + glitch(1.4) * 0.3


def subway(d):
    """Гул вагона + стук колёс «та-дам»."""
    t = T(d)
    s = lp(rng.standard_normal(len(t)), 220) * 1.0 + bp(rng.standard_normal(len(t)), 600, 2000) * 0.08
    s += np.sin(2 * np.pi * 48 * t) * 0.15
    s = s * env(len(t), 0.5, 0.5)
    for tt in np.arange(0.3, d - 0.5, 1.1):
        for dt in (0.0, 0.16):
            i = int((tt + dt) * SR)
            c = lp(rng.standard_normal(int(0.08 * SR)), 900) * np.exp(-T(0.08) * 40) * 1.4
            s[i:i + len(c)] += c[:len(s) - i]
    return s


def hiss(d=0.8):
    t = T(d)
    return hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 3) * 0.5 * env(len(t), 0.02)


def ding():
    return note(hz(88), 0.8, "bell", 0.5) + note(hz(93), 0.8, "bell", 0.3)


def brake_squeal(d=1.6):
    t = T(d)
    f = 2400 - 600 * t / d
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35 + bp(rng.standard_normal(len(t)), 2000, 6000) * 0.4
    return s * np.exp(-t * 0.8) * env(len(t), 0.02, 0.2)


def beep_err():
    t = T(0.5)
    s = np.sign(np.sin(2 * np.pi * 420 * t)) * 0.3 * (((t * 6) % 1) < 0.5)
    return lp(s, 2500) * env(len(t), 0.005, 0.05)


def beep_ok():
    return note(hz(84), 0.25, "pluck", 0.4) + np.concatenate([np.zeros(int(0.12 * SR)), note(hz(91), 0.25, "pluck", 0.4)])[:int(0.25 * SR)]


def siren(d):
    t = T(d)
    f = 700 + 250 * np.sin(2 * np.pi * 0.9 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15 * env(len(t), 0.5, 0.5)


def door_creak():
    return creak(1.2)


def crowd_roar(d):
    t = T(d)
    s = bp(rng.standard_normal(len(t)), 300, 2500) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t))
    return s * env(len(t), 0.5, 0.05)


def concert_beat(d):
    """Тяжёлый концертный бит 128 bpm с басом."""
    out = np.zeros(int(d * SR))
    beat = 60 / 128
    k = 0
    tt = 0.0
    while tt < d - 0.5:
        i = int(tt * SR)
        kick = np.sin(2 * np.pi * np.cumsum(140 * np.exp(-T(0.3) * 25) + 45) / SR) * np.exp(-T(0.3) * 9)
        out[i:i + len(kick)] += kick[:len(out) - i] * 0.9
        if k % 2:
            sn = hp(rng.standard_normal(int(0.15 * SR)), 1500) * np.exp(-T(0.15) * 20) * 0.5
            out[i:i + len(sn)] += sn[:len(out) - i]
        b = note(hz([33, 33, 36, 31][(k // 4) % 4]), beat * 0.9, "bass", 0.6)
        out[i:i + len(b)] += b[:len(out) - i]
        for j in range(2):
            hh = hp(rng.standard_normal(int(0.05 * SR)), 7000) * np.exp(-T(0.05) * 60) * 0.2
            ii = int((tt + j * beat / 2) * SR)
            out[ii:ii + len(hh)] += hh[:len(out) - ii]
        tt += beat
        k += 1
    return out


def growl(d=1.6, loud=1.0):
    t = T(d)
    f = 70 + 20 * np.sin(2 * np.pi * 3 * t)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + lp(rng.standard_normal(len(t)), 500) * 0.8
    s *= (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 7 * t)))
    return lp(s, 900) * env(len(t), 0.1, 0.4) * loud


def crunch():
    t = T(0.25)
    return bp(rng.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 18) * 0.5 * (rng.random(len(t)) < 0.4)


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
        add(voice, x.astype(np.float64) / 32768, l["start"], 1.0)
    voice = hp(voice, 80)
    voice = reverb(voice, 0.5, 0.06)
    S = TL.shots
    ev = TL.ev
    d = ev["end_card"]

    add(music, wind(TL.total) * 0.25, 0.0, 0.3)  # гул шахты
    add(sfx, screech(0.8), ev["stop"] - 0.2, 0.5)
    add(sfx, boom(1.2, 60), ev["stop"], 0.9)
    add(sfx, crunch(), ev["stop"] + 0.05, 0.5)
    for k in range(5):
        add(sfx, buzz(0.15), ev["blink"] + k * 0.27, 0.3)
    for k in range(3):
        add(sfx, click(), ev["silent"] - 0.6 + k * 0.4, 0.6)
    add(sfx, beep_err(), ev["silent"], 0.5)
    add(sfx, creak(1.4), ev["doors"], 0.4)
    for k in range(9):
        add(sfx, knock(), ev["knock"] + (k // 3) * 1.2 + (k % 3) * 0.4, 0.8)
    for k in range(2):
        add(sfx, lp(rng.standard_normal(int(2.5 * SR)), 600) * 0.3 * env(int(2.5 * SR), 1.0, 1.2),
            ev["breathe"] + k * 4, 0.4)
    add(sfx, click(), ev["light"], 0.6)
    for s_ in ev["steps"]:
        add(sfx, hit(0.5), s_ - 0.05, 0.3)
    for k, s_ in enumerate(ev["tally"]):
        add(sfx, note(hz(76 + k * 2), 0.5, "bell", 0.4), s_)
    add(sfx, radio_fx(squelch()), TL.shots[8][0] + 0.2, 0.5)
    add(sfx, note(hz(84), 1.2, "bell", 0.4), ev["right"])
    add(sfx, ding(), ev["open"] - 0.3, 0.6)
    add(sfx, roller(1.4), ev["open"], 0.4)
    add(sfx, sting(), ev["ask"], 0.7)
    add(sfx, glitch(0.4), ev["nobody"], 0.7)
    add(sfx, boom(2.0, 45), ev["only"], 0.8)
    add(sfx, sting(), ev["name"], 0.8)
    for w in ev["whoosh"]:
        add(sfx, whoosh(), w - 0.15, 0.3)
    for h in ev["hit"]:
        add(sfx, hit(), h, 0.35)
    add(sfx, boom(2.5, 50), d, 0.9)
    add(sfx, note(hz(81), 2.5, "bell", 0.3), d + 0.4)
    tt, k = 0.3, 0
    end1 = TL.shots[9][0]
    while tt < end1:  # тревожная пульсация гайда
        add(music, note(hz([57, 60, 64, 62][k % 4]), 0.25, "pluck", 0.1), tt)
        if k % 2 == 0:
            add(music, note(hz(33), 0.4, "bass", 0.3), tt)
        tt += 0.5
        k += 1
    dr = pad([hz(31), hz(32), hz(43)], d - end1, 0.6, 300)
    dr *= np.linspace(0.3, 1.4, len(dr))
    dr[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    add(music, dr, end1)
    tt = ev["ask"]
    while tt < d - 0.3:
        add(sfx, heartbeat(), tt, 0.7)
        tt += 0.65

    venv = lp(np.abs(voice), 4)
    venv = np.clip(venv / (venv.max() * 0.25 + 1e-9), 0, 1)
    duck = 1 - 0.6 * venv
    mix = voice * 1.0 + music * 0.5 * duck + sfx * 0.6 * (1 - 0.4 * venv)
    mix /= np.max(np.abs(mix)) * 1.05
    out = os.path.join(ROOT, "build", "mix_raw.wav")
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-af",
                           "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), os.path.join(ROOT, "build", "mix.wav")])
    print("audio ->", os.path.join(ROOT, "build", "mix.wav"), round(N / SR, 2), "s")


if __name__ == "__main__":
    build()
