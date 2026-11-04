"""Таймлайн серии «Лифт вниз»: голос -> шоты -> звуковые события."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

LEAD = 0.5
TAIL = 4.4
GAP = {0: 0.5, 1: 0.4, 2: 0.6, 3: 0.6, 4: 0.3, 5: 0.6, 6: 0.9, 7: 0.8, 8: 0.6, 9: 0.6, 10: 0.8}
TRANS = {1: "cut", 2: "whip", 3: "cut", 4: "whip", 5: "cut", 6: "cut", 7: "flash", 8: "black", 9: "cut",
         10: "whip", 11: "cut"}


def norm(w):
    return w.lower().replace("ё", "е").strip(".,:;!?—-«»")


class Timeline:
    def __init__(self):
        self.lines = json.load(open(os.path.join(ROOT, "audio", "lines.json"), encoding="utf-8"))
        t = LEAD
        for i, l in enumerate(self.lines):
            w = l["words"][-1]
            l["speech"] = w["t"] + w["d"] + 0.08
            l["start"] = t
            t += l["speech"] + GAP.get(i, 0.5)
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

    def wt(self, li, word, n=0, end=False):
        l = self.lines[li]
        k = 0
        for w in l["words"]:
            if norm(w["w"]) == norm(word):
                if k == n:
                    return l["start"] + w["t"] + (w["d"] if end else 0)
                k += 1
        raise KeyError(f"{word!r}#{n} not in line {li}: {[w['w'] for w in l['words']]}")

    def lend(self, li):
        return self.lines[li]["start"] + self.lines[li]["speech"]

    def shot_at(self, t):
        for i, (a, b) in enumerate(self.shots):
            if a <= t < b:
                return i
        return len(self.shots) - 1

    def floor_at(self, t):
        """Этаж на табло в момент t."""
        pts = self.ev["floors"]
        if t <= pts[0][0]:
            return pts[0][1]
        for (t0, f0), (t1, f1) in zip(pts, pts[1:]):
            if t0 <= t < t1:
                if abs(f1 - f0) <= 1:
                    return f0
                k = (t - t0) / (t1 - t0)
                return int(round(f0 + (f1 - f0) * k))
        return pts[-1][1]

    def _events(self):
        e = {}
        e["whoosh"] = [self.shots[i][0] for i, k in TRANS.items() if k == "whip"]
        e["hit"] = [self.shots[i][0] for i, k in TRANS.items() if k == "flash"]
        e["press"] = self.wt(0, "нажимаешь")
        e["close"] = self.wt(0, "закрываются")
        e["floors"] = [(0.0, 9), (self.wt(0, "закрываются") + 0.3, 9), (self.wt(1, "три") - 1.2, 4),
                       (self.wt(1, "три"), 3), (self.wt(1, "два"), 2), (self.wt(1, "один"), 1),
                       (self.wt(1, "ноль"), 0), (self.wt(1, "один", 1), -1), (self.wt(1, "два", 1), -2),
                       (self.wt(3, "двадцать"), -20), (self.wt(3, "пятьдесят"), -50),
                       (self.wt(8, "сто"), -100)]
        e["nosignal"] = self.wt(3, "сеть")
        e["hot"] = self.wt(3, "жарко")
        e["call"] = self.wt(4, "кнопку")
        e["shout"] = self.wt(6, "первый")
        e["stop"] = self.wt(8, "останавливается")
        e["open"] = self.wt(8, "открываются")
        e["same"] = self.wt(9, "такая")
        e["backs"] = self.wt(10, "спиной")
        e["turn"] = self.wt(11, "оборачивается")
        e["smile"] = self.wt(11, "улыбается")
        e["radio"] = [self.lines[i]["start"] for i, l in enumerate(self.lines) if l.get("spk") == "A"]
        e["end_card"] = self.voice_end + 2.6
        self.ev = e


if __name__ == "__main__":
    tl = Timeline()
    for i, (a, b) in enumerate(tl.shots):
        print(f"shot {i:2d} {a:6.2f}-{b:6.2f} ({b - a:4.1f}s) {TRANS.get(i, 'cut'):5s} "
              f"{tl.lines[i].get('spk')} {tl.lines[i]['text'][:45]}")
    print("total", round(tl.total, 2), "frames", tl.nframes)
    print(tl.ev)
