"""Таймлайн серии «Борт 307»: голос -> шоты -> звуковые события."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

LEAD = 0.9
TAIL = 4.6
GAP = {0: 0.5, 1: 0.45, 2: 0.55, 3: 0.35, 4: 0.25, 5: 0.4, 6: 0.6, 7: 1.3, 8: 0.6, 9: 0.6, 10: 0.7, 11: 0.9,
       12: 0.35}
TRANS = {1: "whip", 2: "whip", 3: "flash", 4: "cut", 5: "cut", 6: "whip", 7: "flash", 8: "black", 9: "whip",
         10: "black", 11: "cut", 12: "cut", 13: "cut"}


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
        e["lightning"] = [0.55, self.wt(0, "один")]
        e["wake"] = self.wt(0, "понимаешь")
        e["alarm"] = (self.wt(2, "красное"), self.lend(6))
        e["radio"] = [self.lines[i]["start"] for i, l in enumerate(self.lines) if l.get("spk") == "R"]
        e["cmd"] = [self.wt(6, "штурвал"), self.wt(6, "скорость"), self.wt(6, "выпустить")]
        e["runway"] = self.wt(7, "вспыхивают")
        e["impact"] = self.wt(7, "удар")
        e["sparks"] = self.wt(7, "искры")
        e["silence"] = self.wt(7, "тишина")
        e["applause"] = (self.wt(8, "аплодирует"), self.lend(8) + 0.4)
        e["run"] = (self.shots[9][0], self.shots[10][0])
        e["badge"] = self.wt(11, "бейдж")
        e["photo"] = self.wt(11, "фотографией")
        e["hiss"] = self.wt(12, "шипит")
        e["end_card"] = self.voice_end + 2.3
        self.ev = e


if __name__ == "__main__":
    tl = Timeline()
    for i, (a, b) in enumerate(tl.shots):
        print(f"shot {i:2d} {a:6.2f}-{b:6.2f} ({b - a:4.1f}s) {TRANS.get(i, 'cut'):5s} "
              f"{tl.lines[i].get('spk')} {tl.lines[i]['text'][:45]}")
    print("total", round(tl.total, 2), "frames", tl.nframes)
    print(tl.ev)
