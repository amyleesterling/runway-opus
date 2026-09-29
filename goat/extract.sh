#!/bin/bash
# Extract every generated clip to 1080p JPEG frames (skips clips already extracted).
cd "$(dirname "$0")"
for v in media/vid/*.mp4; do
  n=$(basename "$v" .mp4); d=media/frames/$n
  [ -f "$d/.done" ] && continue
  mkdir -p "$d"
  ffmpeg -v error -y -i "$v" -vf "fps=24,scale=1920:1080:flags=lanczos" -q:v 2 "$d/%04d.jpg" && touch "$d/.done" && echo "extracted $n ($(ls $d | wc -l) frames)"
done
