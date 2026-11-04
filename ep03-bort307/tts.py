"""Озвучка: каждая строка script/voice.txt -> audio/lines/NN.mp3 + тайминги слов.

Голос: Microsoft Edge TTS (ru-RU-DmitryNeural). Результат: audio/lines.json
[{ "i": 0, "text": "...", "file": "audio/lines/00.mp3", "dur": 4.81,
   "words": [{"w": "Ты", "t": 0.1, "d": 0.2}, ...] }, ...]
"""
import asyncio, json, os, ssl, subprocess, sys

import edge_tts
import edge_tts.communicate as ec

CA = "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):  # корпоративный прокси в облачной среде
    ec._SSL_CTX = ssl.create_default_context(cafile=CA)

VOICE = os.environ.get("VOICE", "ru-RU-DmitryNeural")
RATE = os.environ.get("RATE", "-7%")
PITCH = os.environ.get("PITCH", "-6Hz")  # ниже и спокойнее
ROOT = os.path.dirname(os.path.abspath(__file__))


def probe(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path])
    return float(out)


SPK = {  # N — рассказчик, R — голос в рации (тот же голос, чуть собраннее; радиофильтр в audio.py)
    "N": dict(rate="-7%", pitch="-6Hz"),
    "R": dict(rate="-2%", pitch="-4Hz"),
}


async def one(i, text):
    spk = "N"
    if "|" in text[:3]:
        spk, text = text.split("|", 1)
    path = os.path.join(ROOT, "audio", "lines", f"{i:02d}.mp3")
    words = []
    for attempt in range(4):
        try:
            words = []
            com = edge_tts.Communicate(text, VOICE, rate=SPK[spk]["rate"], pitch=SPK[spk]["pitch"], boundary="WordBoundary")
            with open(path, "wb") as f:
                async for ch in com.stream():
                    if ch["type"] == "audio":
                        f.write(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        words.append({"w": ch["text"], "t": ch["offset"] / 1e7, "d": ch["duration"] / 1e7})
            break
        except Exception as e:  # сеть
            print("retry", i, e, file=sys.stderr)
            await asyncio.sleep(2 ** attempt)
    return {"i": i, "spk": spk, "text": text, "file": os.path.relpath(path, ROOT), "dur": probe(path), "words": words}


async def main():
    os.makedirs(os.path.join(ROOT, "audio", "lines"), exist_ok=True)
    lines = [l.strip() for l in open(os.path.join(ROOT, "script", "voice.txt"), encoding="utf-8") if l.strip()]
    only = {int(a) for a in sys.argv[1:]}
    old = {}
    p = os.path.join(ROOT, "audio", "lines.json")
    if only and os.path.exists(p):
        old = {r["i"]: r for r in json.load(open(p, encoding="utf-8"))}
    res = []
    for i, t in enumerate(lines):
        if only and i not in only and i in old and old[i]["text"] == t.split("|", 1)[-1]:
            res.append(old[i])
        else:
            res.append(await one(i, t))
    json.dump(res, open(os.path.join(ROOT, "audio", "lines.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in res:
        print(f"{r['i']:2d} {r['dur']:5.2f}s {len(r['words']):2d}w  {r['text'][:50]}")
    print("total", round(sum(r["dur"] for r in res), 1))


asyncio.run(main())
