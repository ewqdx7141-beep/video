"""Звук: голос по таймлайну + синтезированная музыка и шумовые эффекты -> build/mix.wav

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


# ------------------------------------------------------------------ сборка
def build():
    voice = np.zeros(N)
    music = np.zeros(N)
    sfx = np.zeros(N)
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    # голос
    for l in TL.lines:
        wav = os.path.join(ROOT, "build", f"line{l['i']:02d}.wav")
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(ROOT, l["file"]),
                               "-ac", "1", "-ar", str(SR), wav])
        sr, x = wavfile.read(wav)
        x = x.astype(np.float64) / 32768
        add(voice, x, l["start"], 1.0)
    voice = hp(voice, 80)
    voice = reverb(voice, 0.5, 0.08)

    S = TL.shots
    # --- музыка: часть 1 (тревожная тишина) 0 .. начало шота 5
    a, b = 0.0, S[5][0]
    music_seg = pad([hz(45), hz(52), hz(57), hz(60)], b - a + 1.5, 0.55, 700)
    add(music, music_seg, a)
    for k, tt in enumerate(np.arange(1.2, b, 1.9)):
        add(music, note(hz([76, 79, 72, 74, 76, 71][k % 6]), 2.5, "bell", 0.12), tt)
    # часть 2 (весёлая неделя) — 120 bpm
    a, b = S[5][0], S[6][0]
    beat = 0.5
    prog = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)]
    k = 0
    tt = a
    while tt < b:
        ch = prog[(k // 4) % 4]
        add(music, note(hz(ch[0] - 24), beat * 0.95, "bass", 0.5), tt)
        kick = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-T(0.3) * 25) + 45) / SR) * np.exp(-T(0.3) * 10)
        add(music, kick, tt, 0.6)
        if k % 2:
            add(music, hp(rng.standard_normal(int(0.08 * SR)), 6000) * np.exp(-T(0.08) * 50), tt, 0.25)
        for j in range(2):
            add(music, note(hz(ch[(k * 2 + j) % 3] + 12), 0.4, "pluck", 0.22), tt + j * beat / 2)
        tt += beat
        k += 1
    # часть 3 (одиночество): медленное пианино
    a, b = S[6][0], S[9][0]
    add(music, pad([hz(41), hz(48), hz(57)], b - a + 1.0, 0.45, 600), a)
    mel = [69, 67, 65, 64, 65, 64, 62, 60, 62, 64, 57, 60]
    for k, tt in enumerate(np.arange(a + 0.4, b - 0.5, 1.35)):
        add(music, note(hz(mel[k % len(mel)]), 2.6, "piano", 0.2), tt)
        if k % 2 == 0:
            add(music, note(hz(mel[k % len(mel)] - 24), 2.6, "piano", 0.12), tt)
    # часть 4 (ночь, сообщение, шаги): гул и диссонанс, до последнего шага
    a, b = S[9][0], EV["steps"][-1] + 0.05
    dr = pad([hz(33), hz(34), hz(45)], b - a, 0.6, 300)
    dr *= np.linspace(0.6, 1.3, len(dr))
    dr[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    add(music, dr, a)
    # высокий скрип-струнный кластер на сообщении
    t = T(b - S[11][0])
    s = sum(np.sin(2 * np.pi * f * t) for f in (hz(84), hz(85), hz(91))) * 0.03 * np.linspace(0, 1, len(t))
    s[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    add(music, s, S[11][0])

    # --- эффекты
    for w in EV["whoosh"]:
        add(sfx, whoosh(), w - 0.15, 0.55)
    for h in EV["hit"]:
        add(sfx, hit(), h, 0.7)
    for bm in EV["boom"]:
        add(sfx, boom(), bm, 0.9)
    add(sfx, wind(S[3][0] - S[1][0]), S[1][0], 0.12)
    add(sfx, engine(S[2][0] - S[1][0] - 0.3), S[1][0] + 0.2, 0.35)
    add(sfx, zap(), EV["delete"], 0.6)
    add(sfx, glitch(0.15), EV["freeze"], 0.5)
    for g in EV["glitch"]:
        add(sfx, glitch(), g, 0.6)
    add(sfx, vroom(), EV["sub5"][0], 0.6)
    add(sfx, roller(EV["paint"][1] - EV["paint"][0]), EV["paint"][0], 0.35)
    for k in range(4):
        add(sfx, buzz(0.55), EV["vibrate"] + k * 0.9, 0.7)
    # «печать» сообщения
    for w in TL.lines[11]["words"]:
        for j in range(4):
            add(sfx, click(), TL.lines[11]["start"] + w["t"] + j * w["d"] / 4, 0.6)
    # сердцебиение
    tt = S[10][0]
    while tt < TL.voice_end + 0.3:
        add(sfx, heartbeat(), tt, 0.9)
        tt += 0.8
    # шаги — громче и ближе
    st = EV["steps"]
    steps = np.zeros(N)
    for k, s in enumerate(st):
        add(steps, step(0.35 + 0.65 * k / max(1, len(st) - 1)), s, 1.0)
    sfx += reverb(steps, 1.4, 0.45)
    # мерцание лампы и щелчок выключателя
    d = EV["end_card"]
    for k in range(5):
        add(sfx, glitch(0.06), d - 0.9 + k * 0.15, 0.4)
    add(sfx, click() * 4, d - 0.25, 1.0)
    add(sfx, boom(2.5, 50), d, 0.9)
    add(sfx, note(hz(81), 2.5, "bell", 0.3), d + 0.4)

    # дакинг музыки под голос
    venv = np.abs(voice)
    venv = lp(venv, 4)
    venv = np.clip(venv / (venv.max() * 0.25 + 1e-9), 0, 1)
    duck = 1 - 0.55 * venv
    mix = voice * 1.0 + music * 0.55 * duck + sfx * 0.6
    mix = reverb(mix, 0.3, 0.0)
    mix /= np.max(np.abs(mix)) * 1.05
    out = os.path.join(ROOT, "build", "mix_raw.wav")
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))
    # громкость под соцсети: -14 LUFS
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-af",
                           "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), os.path.join(ROOT, "build", "mix.wav")])
    print("audio ->", os.path.join(ROOT, "build", "mix.wav"), round(N / SR, 2), "s")


if __name__ == "__main__":
    build()
