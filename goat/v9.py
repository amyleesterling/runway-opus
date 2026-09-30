"""v9 assets: flying Volvo, Santa actually firing a flaming arrow (Gingerbread Man flossing), the ashy guy speaking."""
import sys
import runway

GOAT = ("the giant 13-metre straw Yule goat from the reference image (golden straw, huge curved horns, red ribbon bands)")
LOOK = "Photorealistic, cinematic 35mm, rich saturated colour grade, 16:9 film frame, no text, no captions, no watermark."

IMAGES = {
    "volvo_fly": f"Night, snowy Swedish town square, action-movie moment: a red 1960s Volvo Amazon is airborne, launched off a "
                 f"snowbank, flying through the air with headlights blazing and snow spraying, about to smash into {GOAT}. "
                 f"Dramatic low angle, sparks, motion. {LOOK}",
    "santa_floss": f"Night, heavy snow, wide shot: on a snowbank Santa Claus in a red suit and tactical vest has just released a "
                   f"flaming arrow from his longbow; the arrow flies toward {GOAT} in the distance, trailing bright fire. Next to "
                   f"Santa, a person in a full-body gingerbread-man costume dances the 'floss' dance in celebration, arms swinging. "
                   f"Comedic. {LOOK}",
}

VIDEOS = {  # name: (model, seconds, image, prompt, audio)
    "volvo_fly": ("gen4.5", 5, "volvo_fly", "Super slow motion: the airborne Volvo flies into the straw goat and smashes through it; "
                  "the goat EXPLODES in a massive fireball, burning straw and debris blasting everywhere, fire engulfing everything. "
                  "Epic action movie.", False),
    "santa_floss": ("gen4.5", 5, "santa_floss", "The flaming arrow streaks through the snowy night toward the straw goat with a "
                    "bright fire trail; Santa lowers his bow triumphantly while the gingerbread man keeps doing the floss dance, "
                    "swinging his arms and hips back and forth. Comedic.", False),
    "ashy": ("veo3.1_fast", 6, "n2015", "The man with the soot-blackened face and singed smoking eyebrows looks sheepishly into "
             "the camera and says, in a Swedish accent: \"This was an extremely bad idea.\" He shrugs. Police flashlights sweep "
             "over him, a straw goat burns behind. Crackling fire, no music.", True),
}


def image(name):
    body = {"model": "gemini_image3_pro", "promptText": IMAGES[name], "ratio": "2752:1536",
            "referenceImages": [{"uri": runway.url_of("media/img/hero_goat.png"), "tag": "goat", "subject": "object"}]}
    return runway.run("text_to_image", body, f"media/img/{name}.png", name)


def video(name):
    model, secs, img, prompt, audio = VIDEOS[name]
    body = {"model": model, "promptImage": runway.url_of(f"media/img/{img}.png"), "promptText": prompt, "duration": secs}
    body |= {"ratio": "1280:720", "audio": audio} if model.startswith("veo") else {"ratio": "1280:720"}
    return runway.run("image_to_video", body, f"media/vid/{name}.mp4", name)


if __name__ == "__main__":
    what, names = sys.argv[1], sys.argv[2:]
    for n in names or list(IMAGES if what == "img" else VIDEOS):
        try:
            print("ok", n, (image if what == "img" else video)(n), flush=True)
        except Exception as e:
            print("FAIL", n, e, flush=True)
