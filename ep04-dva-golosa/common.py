"""Таймлайн серии «Два голоса»: голос -> шоты -> звуковые события."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

LEAD = 0.5
TAIL = 4.2
GAP = {0: 0.55, 1: 0.6, 2: 0.55, 3: 0.35, 4: 0.5, 5: 0.35, 6: 0.6, 7: 0.5, 8: 0.45, 9: 0.6, 10: 0.7,
       11: 0.6, 12: 0.7}
TRANS = {1: "cut", 2: "whip", 3: "flash", 4: "cut", 5: "whip", 6: "flash", 7: "whip", 8: "cut", 9: "flash",
         10: "whip", 11: "flash", 12: "whip", 13: "cut"}


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
        e["flicker"] = self.wt(0, "мигнул")
        e["sleep"] = self.wt(0, "закрыли")
        e["sub1"] = [self.wt(1, "стюардесса"), self.wt(1, "у"), self.wt(1, "самолет")]
        e["fall"] = self.wt(1, "падает")
        e["tablet"] = self.wt(1, "выскальзывает")
        e["bank"] = self.wt(1, "ложится")
        e["fuel"] = self.wt(2, "мигает")
        e["radio_on"] = self.lend(3) - 0.3
        e["push"] = self.wt(5, "толкаешь")
        e["burst"] = self.wt(5, "врывается")
        e["mountains"] = self.wt(6, "горы")
        e["radar"] = self.wt(9, "радаре")
        e["countdown"] = (self.wt(10, "топлива"), self.lend(10))
        e["light"] = self.wt(11, "вспыхивает")
        e["tail"] = self.wt(11, "хвосте")
        e["raise"] = self.wt(12, "подносишь")
        e["radio"] = [self.lines[i]["start"] for i, l in enumerate(self.lines) if l.get("spk") in ("A", "B", "R")]
        e["alarm"] = (self.wt(2, "мигает"), self.lend(10))
        e["end_card"] = self.voice_end + 2.4
        self.ev = e


if __name__ == "__main__":
    tl = Timeline()
    for i, (a, b) in enumerate(tl.shots):
        print(f"shot {i:2d} {a:6.2f}-{b:6.2f} ({b - a:4.1f}s) {TRANS.get(i, 'cut'):5s} "
              f"{tl.lines[i].get('spk')} {tl.lines[i]['text'][:45]}")
    print("total", round(tl.total, 2), "frames", tl.nframes)
    print(tl.ev)
