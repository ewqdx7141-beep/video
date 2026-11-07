"""Таймлайн серии «Лифт с незнакомцем» (формат «что делать», сверка запасов): голос -> шоты -> события."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

LEAD = 0.5
TAIL = 3.4
GAP = {0: 0.2, 1: 0.2, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.2, 6: 0.2, 7: 0.25, 8: 0.4, 9: 0.3, 10: 0.35, 11: 0.4}
TRANS = {1: "cut", 2: "whip", 3: "whip", 4: "whip", 5: "whip", 6: "whip", 7: "flash", 8: "cut", 9: "black",
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
        e["stop"] = self.wt(0, "встал")
        e["case"] = self.wt(0, "чемоданом")
        e["blink"] = self.wt(1, "мигает")
        e["silent"] = self.wt(1, "молчит")
        e["steps"] = [self.wt(i, "шаг") for i in range(2, 7)]
        e["doors"] = self.wt(2, "двери")
        e["where"] = self.wt(2, "кабина")
        e["knock"] = self.wt(3, "удара")
        e["sit"] = self.wt(4, "сядь")
        e["breathe"] = self.wt(4, "дыши")
        e["talk"] = self.wt(5, "говори")
        e["half"] = self.wt(5, "половина")
        e["light"] = self.wt(6, "телефона")
        e["two"] = self.wt(6, "двоих")
        e["tally"] = [self.wt(7, w) for w in ("вызовов", "стуков", "заряд", "паники", "время")]
        e["right"] = self.wt(8, "правильно")
        e["open"] = self.wt(9, "открываются")
        e["floor"] = self.wt(9, "этаж")
        e["mech"] = self.wt(10, "механики")
        e["ask"] = self.wt(10, "разговаривали")
        e["nobody"] = self.wt(11, "никого")
        e["only"] = self.wt(11, "чемодан")
        e["tag"] = self.wt(12, "бирке")
        e["name"] = self.wt(12, "имя")
        e["flat"] = self.wt(12, "квартиры")
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
