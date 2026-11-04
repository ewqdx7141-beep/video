"""Таймлайн серии «Умный дом»: голос -> шоты -> звуковые события."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

LEAD = 0.5
TAIL = 4.4
GAP = {0: 0.6, 1: 0.6, 2: 0.6, 3: 0.6, 4: 0.7, 5: 0.7, 6: 0.7, 7: 0.7, 8: 0.9}
TRANS = {1: "whip", 2: "whip", 3: "flash", 4: "whip", 5: "black", 6: "whip", 7: "cut", 8: "flash", 9: "cut"}


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

    def _events(self):
        e = {}
        e["whoosh"] = [self.shots[i][0] for i, k in TRANS.items() if k == "whip"]
        e["hit"] = [self.shots[i][0] for i, k in TRANS.items() if k == "flash"]
        e["denied"] = self.wt(0, "лицо", 1) if False else self.wt(0, "распознано")
        e["sub1"] = [self.wt(1, "код"), self.wt(1, "отпечаток"), self.wt(1, "приложение")]
        e["light"] = self.wt(2, "свет")
        e["shadow"] = self.wt(2, "ходит")
        e["intercom"] = self.lines[3]["start"]
        e["neighbors"] = self.lines[4]["start"]
        e["call"] = self.wt(4, "звонишь")
        e["door_open"] = self.wt(5, "открывается")
        e["you"] = self.wt(5, "стоишь")
        e["fake_ok"] = self.wt(6, "настоящий")
        e["empty"] = self.wt(6, "пустое")
        e["again"] = self.wt(8, "опять")
        e["nod"] = self.wt(9, "кивает")
        e["end_card"] = self.voice_end + 2.6
        self.ev = e


if __name__ == "__main__":
    tl = Timeline()
    for i, (a, b) in enumerate(tl.shots):
        print(f"shot {i:2d} {a:6.2f}-{b:6.2f} ({b - a:4.1f}s) {TRANS.get(i, 'cut'):5s} "
              f"{tl.lines[i].get('spk')} {tl.lines[i]['text'][:45]}")
    print("total", round(tl.total, 2), "frames", tl.nframes)
    print(tl.ev)
