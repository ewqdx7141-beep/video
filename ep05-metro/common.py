"""Таймлайн серии «Последний поезд»: голос -> шоты -> звуковые события."""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30

LEAD = 0.5
TAIL = 4.4
GAP = {0: 0.5, 1: 0.55, 2: 0.8, 3: 0.6, 4: 0.6, 5: 0.6, 6: 0.6, 7: 1.0, 8: 0.7, 9: 0.6}
TRANS = {1: "cut", 2: "flash", 3: "cut", 4: "whip", 5: "whip", 6: "flash", 7: "cut", 8: "whip", 9: "black",
         10: "cut"}


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
        e["pass1"] = self.wt(1, "проносится")
        e["pass2"] = self.wt(1, "второй")
        e["flicker"] = self.wt(1, "мигает")
        e["lookup"] = self.wt(2, "поднимают")
        e["stare"] = self.wt(2, "смотрят")
        e["baby"] = self.wt(3, "малыш")
        e["doors"] = self.wt(4, "разъезжаются")
        e["turn"] = self.wt(4, "поворачиваются")
        e["notif"] = self.wt(5, "уведомление")
        e["viewers"] = self.wt(5, "двести")
        e["screens"] = self.wt(6, "экране")
        e["phone_found"] = self.wt(8, "телефон")
        e["chat"] = self.wt(8, "сообщения")
        e["brake"] = self.wt(9, "тормозит")
        e["doors2"] = self.wt(9, "открываются")
        e["name"] = self.wt(10, "имя")
        e["end_card"] = self.voice_end + 2.6
        self.ev = e


if __name__ == "__main__":
    tl = Timeline()
    for i, (a, b) in enumerate(tl.shots):
        print(f"shot {i:2d} {a:6.2f}-{b:6.2f} ({b - a:4.1f}s) {TRANS.get(i, 'cut'):5s} "
              f"{tl.lines[i].get('spk')} {tl.lines[i]['text'][:45]}")
    print("total", round(tl.total, 2), "frames", tl.nframes)
    print(tl.ev)
