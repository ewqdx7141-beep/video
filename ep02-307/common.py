"""Таймлайн серии «Сообщение из 3:07»: голос -> шоты -> звуковые события."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

LEAD = 0.35          # хук начинается почти сразу
TAIL = 5.6           # после последней фразы: ручка двери поворачивается, затем карточка
GAP = {0: 0.55, 1: 0.4, 2: 0.6, 3: 0.6, 4: 0.5, 5: 0.55, 6: 0.75, 7: 0.6, 8: 0.85, 9: 0.9, 10: 1.6, 11: 0.8}
TRANS = {1: "black", 2: "cut", 3: "whip", 4: "black", 5: "flash", 6: "whip", 7: "flash", 8: "fade",
         9: "black", 10: "black", 11: "flash", 12: "cut"}


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
        e["flip1"] = self.shots[1][0] + 0.35          # часы 3:06 -> 3:07
        e["vib"] = [self.shots[1][0] + 0.8, self.wt(4, "купи") - 0.35, self.wt(9, "сообщение"),
                    self.wt(12, "вибрирует")]
        e["evening"] = self.wt(3, "вечером")
        e["buy"] = self.wt(4, "купи")
        e["x40"] = self.wt(5, "сорок")
        e["reply"] = self.wt(6, "ты", 2)
        e["sub7"] = [self.wt(7, "квартира"), self.wt(7, "машина"), self.wt(7, "друзья")]
        e["whoosh"] += e["sub7"] + [e["evening"]]
        e["flip8"] = self.lend(8) - 0.3
        knock = self.wt(10, "стук")
        e["knocks"] = [knock, knock + 0.42, knock + 0.84]
        e["reveal"] = self.wt(11, "стоишь")
        e["wave"] = self.wt(11, "машешь")
        e["notme"] = self.wt(12, "это")
        e["handle"] = (self.voice_end + 0.9, self.voice_end + 3.6)
        e["end_card"] = self.voice_end + 3.9
        # сообщения: (строка, первое слово, последнее слово) для печати по буквам и щелчков
        e["typing"] = [(2, self.lines[2]["start"] + self.lines[2]["words"][0]["t"], self.lend(2)),
                       (4, e["buy"], self.lend(4)),
                       (6, self.wt(6, "кто"), self.wt(6, "ты", 1, end=True)),
                       (9, self.wt(9, "завтра"), self.lend(9)),
                       (12, e["notme"], self.lend(12))]
        self.ev = e


if __name__ == "__main__":
    tl = Timeline()
    for i, (a, b) in enumerate(tl.shots):
        print(f"shot {i:2d} {a:6.2f}-{b:6.2f} ({b - a:4.1f}s) {TRANS.get(i, 'cut'):5s} {tl.lines[i]['text'][:45]}")
    print("total", round(tl.total, 2), "frames", tl.nframes)
    print(tl.ev)
