"""Таймлайн серии «Билет на Марс» (формат «что делать», сверка запасов): голос -> шоты -> события."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

LEAD = 0.5
TAIL = 3.4
GAP = {0: 0.2, 1: 0.2, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.2, 6: 0.2, 7: 0.25, 8: 0.4, 9: 0.3, 10: 0.35, 11: 0.4}
TRANS = {1: "cut", 2: "whip", 3: "whip", 4: "whip", 5: "whip", 6: "whip", 7: "flash", 8: "cut", 9: "black",
         10: "cut", 11: "flash", 12: "flash"}


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
        e["ticket"] = self.wt(0, "билет")
        e["days"] = self.wt(0, "тридцать")
        e["g"] = self.wt(1, "перегрузки")
        e["suit"] = self.wt(1, "скафандр")
        e["kg"] = self.wt(1, "два")
        e["steps"] = [self.wt(i, "шаг") for i in range(2, 7)]
        e["dark"] = self.wt(2, "темнеть")
        e["bag"] = self.wt(3, "пакета")
        e["teeth"] = self.wt(3, "зубы")
        e["items"] = [self.wt(4, w) for w in ("фото", "флешка", "зерно")]
        e["iso"] = self.wt(5, "изоляции")
        e["letters"] = self.wt(6, "каждому")
        e["tally"] = [self.wt(7, w) for w in ("центрифуга", "вещи", "изоляция", "письма")]
        e["start"] = self.wt(8, "старт")
        e["right"] = self.wt(8, "правильно")
        e["land"] = self.wt(9, "садится")
        e["hatch"] = self.wt(9, "люк")
        e["desert"] = self.wt(10, "пустыня")
        e["dome"] = self.wt(10, "купол")
        e["note"] = self.wt(11, "записка")
        e["hand"] = self.wt(11, "почерком")
        e["dont"] = self.wt(12, "выходи")
        e["first"] = self.wt(12, "первым")
        e["last"] = self.wt(12, "прошлый")
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
