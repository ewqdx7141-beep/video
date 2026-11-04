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


SPK = {  # N — рассказчик; A — диспетчер-женщина; B — второй голос (сорванный); R — финал, голос рассказчика в рации
    "N": dict(voice="ru-RU-DmitryNeural", rate="-3%", pitch="-6Hz"),
    "A": dict(voice="ru-RU-SvetlanaNeural", rate="-1%", pitch="-2Hz"),
    "B": dict(voice="ru-RU-DmitryNeural", rate="-10%", pitch="-14Hz"),
    "R": dict(voice="ru-RU-DmitryNeural", rate="-12%", pitch="-8Hz"),
}


async def one(i, text):
    spk = "N"
    if "|" in text[:3]:
        spk, text = text.split("|", 1)
    path = os.path.join(ROOT, "audio", "lines", f"{i:02d}.mp3")
    words = []
    for attempt in range(15):
        try:
            words = []
            com = edge_tts.Communicate(text, SPK[spk]["voice"], rate=SPK[spk]["rate"], pitch=SPK[spk]["pitch"], boundary="WordBoundary")
            with open(path, "wb") as f:
                async for ch in com.stream():
                    if ch["type"] == "audio":
                        f.write(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        words.append({"w": ch["text"], "t": ch["offset"] / 1e7, "d": ch["duration"] / 1e7})
            break
        except Exception as e:  # сеть
            print("retry", i, e, file=sys.stderr)
            if attempt == 14:
                raise
            await asyncio.sleep(min(20, 2 + attempt * 2))
    return {"i": i, "spk": spk, "text": text, "file": os.path.relpath(path, ROOT), "dur": probe(path), "words": words}


async def main():
    """Инкрементально: готовые строки (тот же текст и голос) не перегенерируются, json пишется после каждой."""
    os.makedirs(os.path.join(ROOT, "audio", "lines"), exist_ok=True)
    lines = [l.strip() for l in open(os.path.join(ROOT, "script", "voice.txt"), encoding="utf-8") if l.strip()]
    force = {int(a) for a in sys.argv[1:]}
    p = os.path.join(ROOT, "audio", "lines.json")
    old = {}
    if os.path.exists(p):
        old = {r["i"]: r for r in json.load(open(p, encoding="utf-8"))}
    res = []
    for i, t in enumerate(lines):
        spk, txt = (t.split("|", 1) if "|" in t[:3] else ("N", t))
        key = f"{SPK[spk]}"
        o = old.get(i)
        if i not in force and o and o["text"] == txt and o.get("spk") == spk and o.get("key") == key \
                and os.path.exists(os.path.join(ROOT, o["file"])):
            res.append(o)
        else:
            r = await one(i, t)
            r["key"] = key
            res.append(r)
            force.discard(i)
        json.dump(res + [old[j] for j in sorted(old) if j > i], open(p, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    json.dump(res, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in res:
        print(f"{r['i']:2d} {r['dur']:5.2f}s {len(r['words']):2d}w  {r['text'][:50]}")
    print("total", round(sum(r["dur"] for r in res), 1))


asyncio.run(main())
