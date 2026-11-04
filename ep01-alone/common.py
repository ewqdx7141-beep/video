"""Общий таймлайн: голос -> шоты -> звуковые события. Используется render.py и audio.py."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

LEAD = 0.75          # тишина перед первой фразой (успевает появиться заголовок-хук)
TAIL = 6.2           # после последней фразы: шаги, ноги под дверью, финальная карточка
GAP = {0: 0.45, 1: 0.45, 2: 0.55, 3: 1.4, 4: 0.55, 5: 0.65, 6: 1.0,
       7: 0.65, 8: 0.85, 9: 1.25, 10: 0.7, 11: 1.0}
# переход В шот i: cut / whip / flash / fade / black
TRANS = {1: "whip", 2: "whip", 3: "flash", 4: "whip", 5: "flash", 6: "fade", 7: "whip",
         8: "whip", 9: "black", 10: "flash", 11: "cut", 12: "black"}


def norm(w):
    return w.lower().replace("ё", "е").strip(".,:;!?—-«»")


class Timeline:
    def __init__(self):
        self.lines = json.load(open(os.path.join(ROOT, "audio", "lines.json"), encoding="utf-8"))
        t = LEAD
        for i, l in enumerate(self.lines):
            w = l["words"][-1]
            l["speech"] = w["t"] + w["d"] + 0.08   # файл заканчивается ~0.85 с тишины
            l["start"] = t
            t += l["speech"] + GAP.get(i, 0.45)
        last = self.lines[-1]
        self.voice_end = last["start"] + last["speech"]
        self.total = self.voice_end + TAIL
        self.shots = []
        for i, l in enumerate(self.lines):
            a = 0.0 if i == 0 else l["start"] - 0.12
            b = self.total if i == len(self.lines) - 1 else self.lines[i + 1]["start"] - 0.12
            self.shots.append((a, b))
        self.nframes = int(round(self.total * FPS))
        self._events()

    # абсолютное время начала слова (точное совпадение, n-е вхождение)
    def wt(self, li, word, n=0, end=False):
        l = self.lines[li]
        k = 0
        for w in l["words"]:
            if norm(w["w"]) == norm(word):
                if k == n:
                    return l["start"] + w["t"] + (w["d"] if end else 0)
                k += 1
        raise KeyError(f"{word!r} not in line {li}: {[w['w'] for w in l['words']]}")

    def shot_at(self, t):
        for i, (a, b) in enumerate(self.shots):
            if a <= t < b:
                return i
        return len(self.shots) - 1

    def _events(self):
        e = {}
        e["whoosh"] = [self.shots[i][0] for i, k in TRANS.items() if k == "whip"]
        e["hit"] = [self.shots[i][0] for i, k in TRANS.items() if k in ("flash",)]
        e["boom"] = [self.wt(0, "тишина"), self.wt(9, "вибрирует")]
        # шот 5: смена подсцен
        e["sub5"] = [self.wt(5, "гоняешь"), self.wt(5, "спишь"), self.wt(5, "ешь")]
        e["whoosh"] += e["sub5"]
        e["delete"] = self.wt(3, "удалить")
        e["freeze"] = self.wt(3, "посреди")
        e["glitch"] = [self.wt(4, "связи"), self.wt(4, "интернета"), self.wt(4, "застывший")]
        e["vibrate"] = self.wt(9, "вибрирует")
        e["paint"] = (self.shots[8][0], self.wt(8, "здесь", end=True))
        # шаги: от слова «шаги» до конца, с ускорением в конце — и обрыв
        s0 = self.wt(12, "шаги")
        steps, t, dt = [], s0, 0.62
        stop = self.voice_end + 3.3
        while t < stop:
            steps.append(t)
            t += dt
            dt = max(0.5, dt * 0.985)
        e["steps"] = steps
        e["sub12"] = [self.wt(12, "этаж"), self.wt(12, "они"), self.voice_end + 0.5, self.voice_end + 3.9]
        e["end_card"] = self.voice_end + 3.9
        self.ev = e


if __name__ == "__main__":
    tl = Timeline()
    for i, (a, b) in enumerate(tl.shots):
        print(f"shot {i:2d} {a:6.2f}-{b:6.2f} ({b - a:4.1f}s) {TRANS.get(i, 'cut'):5s} {tl.lines[i]['text'][:45]}")
    print("total", round(tl.total, 2), "frames", tl.nframes)
    print({k: v for k, v in tl.ev.items() if k != "steps"}, "steps", len(tl.ev["steps"]))
