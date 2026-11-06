"""Таймлайн серии «Лес» (формат «что делать», сверка запасов): голос -> шоты -> события."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

LEAD = 0.5
TAIL = 3.6
GAP = {0: 0.25, 1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25, 5: 0.25, 6: 0.25, 7: 0.3, 8: 0.45, 9: 0.35, 10: 0.45, 11: 0.5}
TRANS = {1: "flash", 2: "whip", 3: "whip", 4: "whip", 5: "whip", 6: "whip", 7: "flash", 8: "cut", 9: "black",
         10: "cut", 11: "flash", 12: "cut"}


def norm(w):
    return w.lower().replace("ё", "е").strip(".,:;!?—-«»")


class Timeline:
    def __init__(self):
        self.lines = json.load(open(os.path.join(ROOT, "audio", "lines.json"), encoding="utf-8"))
        t = LEAD
        for i, l in enumerate(self.lines):
            w = l["words"][-1]
            l["speech"] = max(w["t"] + w["d"] + 0.08, l["dur"] - 0.85)  # если метки слов оборвались
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

    def _events(self):
        e = {}
        e["whoosh"] = [self.shots[i][0] for i, k in TRANS.items() if k == "whip"]
        e["hit"] = [self.shots[i][0] for i, k in TRANS.items() if k == "flash"]
        e["dead"] = self.wt(0, "сел")
        e["steps"] = [self.wt(i, "шаг") for i in range(2, 7)]
        e["sit"] = self.wt(2, "сядь")
        e["hut"] = self.wt(3, "шалаш")
        e["fire"] = self.wt(4, "береста")
        e["melt"] = self.wt(5, "растопи")
        e["whistle"] = self.wt(6, "свистка")
        e["knock"] = self.wt(6, "удара")
        e["tally"] = [self.wt(7, w) for w in ("вода", "укрытие", "огонь", "свисток", "еда")]
        e["chance"] = self.wt(8, "восемьдесят")
        e["closer"] = self.wt(9, "ближе")
        e["creak"] = self.wt(10, "скрипит")
        e["move"] = self.wt(10, "двигаются")
        e["heli"] = self.wt(11, "вертолет")
        e["circle"] = self.wt(11, "круг")
        e["shrink"] = self.wt(12, "сжимается")
        e["radio"] = []
        e["end_card"] = self.voice_end + 2.6
        self.ev = e


if __name__ == "__main__":
    tl = Timeline()
    for i, (a, b) in enumerate(tl.shots):
        print(f"shot {i:2d} {a:6.2f}-{b:6.2f} ({b - a:4.1f}s) {TRANS.get(i, 'cut'):5s} "
              f"{tl.lines[i].get('spk')} {tl.lines[i]['text'][:45]}")
    print("total", round(tl.total, 2), "frames", tl.nframes)
    print(tl.ev)
