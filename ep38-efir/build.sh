#!/usr/bin/env bash
# Сборка серии «Прямой эфир»: озвучка -> видеоряд -> звук -> out/ep38-efir.mp4
set -euo pipefail
cd "$(dirname "$0")"
pip install -q pycairo edge-tts numpy scipy
mkdir -p ~/.fonts && cp ../lib/fonts/*.ttf ~/.fonts/ && fc-cache -f >/dev/null
[ -f audio/lines.json ] || python3 tts.py
python3 render.py --jobs "$(nproc)"
python3 audio.py
mkdir -p out
ffmpeg -y -loglevel error -i build/video.mp4 -i build/mix.wav \
  -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart out/ep38-efir.mp4
echo "готово: out/ep38-efir.mp4"
