# THE G.O.A.T. — *Greatest Of All Tinder*

A comedy short about the Gävle Goat. Since 1966, Sweden has built a 13-metre straw Yule goat every year, and
people keep destroying it: 43 of 60 have been burned, stolen, hit by a Volvo, or shot with a flaming arrow by
arsonists dressed as Santa Claus and the Gingerbread Man. In 2023 jackdaws ate it.

Every event in the film is real. The dialogue is dramatised.

Written & directed by Claude “The Goatfather”. Produced by @amyleesterling.

## Pipeline

All footage, voices, sound effects and music come from the Runway API. The edit, motion graphics and mix are code.

| Stage | Script | Models |
|---|---|---|
| Keyframes (16 stills, all anchored to one hero goat for continuity) | `keyframes.py` | Gemini Image 3 Pro |
| Animation | `videos.py` | Veo 3.1 (hero shots + synced dialogue), Gen-4.5 (montage) |
| Voices, SFX, score | `audio.py` | ElevenLabs v3, ElevenLabs SFX, Seed Audio |
| Fire VFX plates (fireball, flame wall, embers, shockwave, pyro, burning title) shot on black and screen-composited | `fire.py` | Gen-4.5, Gemini Image 3 Pro |
| Edit | `edit.py` | builds `render/timeline.json` + the mix |
| Motion graphics / compositing | `render/engine.js` | canvas compositor, rendered frame-by-frame in headless Chromium |
| Render | `render/render.mjs` | Playwright → ffmpeg |

`edit.py` lays every sequence out on a running cursor and syncs graphics to measured phrase timings in the
voiceover (`vo_analyze.py`). The audio is normalised per asset (`levels.py`), mixed as dialogue and bed stems,
and the bed is sidechain-ducked under the dialogue.

## Run it

```bash
export RUNWAY_KEY_FILE=/path/to/key          # file containing the Runway API key
python3 keyframes.py && python3 videos.py && python3 audio.py && python3 fire.py
python3 vo_analyze.py && python3 levels.py && ./extract.sh
python3 edit.py --audio
node render/render.mjs media/goat.mp4 --workers 4
ffmpeg -i media/goat.mp4 -i media/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -af loudnorm=I=-14:TP=-1.5 goat_final.mp4
```

Generated media lives in `media/` (git-ignored). Everything is cached, so a re-run only regenerates missing assets.
