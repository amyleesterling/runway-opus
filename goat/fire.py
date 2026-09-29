"""Stage 4 (flametastic pass): fire VFX elements on pure black, for additive/screen compositing."""
import concurrent.futures as cf
import runway

BLACK = ("Isolated on a pure solid black background, nothing else in frame, no ground, no smoke haze, locked-off camera, "
         "high-speed cinematic VFX stock element, photoreal fire, extreme detail.")
ELEMENTS = {  # name: (seconds, prompt)
    "fx_fireball": (5, "A massive fireball explosion erupts from the center and billows outward in slow motion, rolling orange "
                       "and yellow flame, bright white-hot core, embers flying. " + BLACK),
    "fx_flamewall": (6, "A wall of tall roaring flames rises from the bottom edge of frame and licks upward, filling the lower "
                        "half of the frame, flickering orange fire. " + BLACK),
    "fx_embers": (6, "Thousands of glowing orange embers and sparks swirl and drift upward through the frame, some streaking, "
                     "shallow depth of field bokeh. " + BLACK),
    "fx_shockwave": (5, "A fiery ring shockwave expands rapidly outward from the center, a circular blast of flame and sparks, "
                        "slow motion. " + BLACK),
    "fx_burst": (5, "Two giant jets of flame burst upward from the left and right bottom corners like stadium pyrotechnics, "
                    "then fade. " + BLACK),
}
TITLE = ("Giant three-dimensional letters spelling 'THE G.O.A.T.' made of burning golden straw, completely engulfed in "
         "roaring flames, embers swirling, on a pure black background, epic movie title, photoreal, centered, 16:9.")


def element(name):
    secs, prompt = ELEMENTS[name]
    return runway.run("text_to_video", {"model": "gen4.5", "promptText": prompt, "ratio": "1280:720", "duration": secs},
                      f"media/vid/{name}.mp4", name)


def title():
    img = runway.run("text_to_image", {"model": "gemini_image3_pro", "promptText": TITLE, "ratio": "2752:1536"},
                     "media/img/fire_title.png", "fire_title_img")
    return runway.run("image_to_video", {"model": "gen4.5", "promptImage": runway.url_of(img), "ratio": "1280:720",
                                         "duration": 5, "promptText": "The flames roar and dance over the burning straw "
                                         "letters, embers swirl upward, slow push-in. Letters stay perfectly legible."},
                      "media/vid/fire_title.mp4", "fire_title")


if __name__ == "__main__":
    jobs = [title] + [lambda n=n: element(n) for n in ELEMENTS]
    for j in jobs:  # gen4.5 allows one at a time
        try:
            print("ok", j(), flush=True)
        except Exception as e:
            print("FAIL", e, flush=True)
    print("credits", runway.credits())
