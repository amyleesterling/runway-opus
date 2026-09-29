"""v4 assets: the Norse goat myth opening + the unmasking / Naruto-run finale.

The two 'culprits' are deliberately grotesque latex puppets (political satire), never photoreal people.
"""
import sys
import runway

PAINT = ("Epic 19th-century Scandinavian romantic oil painting, dramatic chiaroscuro, rich colours, visible brushwork, "
         "museum masterpiece, humorous undertone, 16:9, no text.")
PUPPET = ("grotesque satirical foam-latex puppet in the style of 1980s British political satire TV: huge sculpted rubber head "
          "about three times too big, glossy painted latex skin with visible seams, hinged puppet mouth, glass eyes, stiff felt hands, "
          "unmistakably a handmade puppet and not a real person")
TRUMP = f"a {PUPPET}, caricaturing Donald Trump through his giant swoop of golden hair, orange tan and pursed pout"
OBAMA = f"a {PUPPET}, caricaturing Barack Obama through his huge jug ears, short grey hair and enormous confident grin"
SCENE = ("Night, heavy snow, old Swedish town square with red wooden houses, a giant straw Yule goat engulfed in flames in the "
         "background, fire glow, cinematic photography, 16:9, no text, no captions, no logos.")

IMAGES = {
    "myth_chariot": ("A mighty red-bearded Norse thunder god from Viking legend, holding a short-handled war hammer, rides a wooden war chariot pulled by "
                     "two enormous wild goats galloping across a stormy night sky, lightning forking around them. " + PAINT, None),
    "myth_feast": ("Inside a smoky Viking longhouse at night, a red-bearded Norse thunder god from Viking legend sits at a long table happily eating roast goat by the hearth while a "
                   "shocked peasant family stares; two goat skins lie spread on the floor with bones piled on them. " + PAINT, None),
    "myth_rise": ("Dawn outside a Viking longhouse: a red-bearded Norse thunder god from Viking legend raises his war hammer over two goat skins and the goats magically spring back to "
                  "life in a burst of golden light; one goat stands on a comically crooked limping back leg looking annoyed. " + PAINT, None),
    "myth_julbock": ("A snowy 1800s Swedish farmhouse at night: a villager in a homemade straw goat costume with tall horns (the "
                     "julbock) knocks at the door with a sack of presents while delighted children in nightgowns peek out; warm "
                     "candlelight. " + PAINT, None),
    "unmask_a": ("Santa Claus in a red suit and tactical vest and a person in a full-body gingerbread-man costume stand side by side "
                 "facing the camera, each gripping the edge of their own mask (Santa's beard, the gingerbread head) as if about to "
                 "pull it off. " + SCENE, None),
    "unmask_b": (f"Same two figures and same scene as the reference image, but they have pulled off their masks: Santa is revealed "
                 f"as {TRUMP}, holding the fake white beard; the gingerbread man is revealed as {OBAMA}, holding the gingerbread head "
                 f"under his arm. Both grin guiltily. " + SCENE, "unmask_a"),
    "naruto": (f"The two satirical puppets from the reference image, {TRUMP} in the Santa suit and {OBAMA} in the gingerbread "
               f"costume, doing the classic anime ninja run away across the snowy square: torsos leaning forward at 45 degrees, BOTH arms "
               f"stretched perfectly straight backwards behind them, palms up, heads forward, legs mid-stride, motion blur, snow kicked up, the straw goat burning behind them. " + SCENE, "unmask_b"),
}

VIDEOS = {  # name: (model, secs, first image, last image, prompt)
    "myth_chariot": ("gen4.5", 5, "myth_chariot", None, "The goats gallop hard, the chariot thunders across the sky, lightning flashes, "
                     "the god raises his hammer. The painting comes alive, slow push-in."),
    "myth_feast": ("gen4.5", 5, "myth_feast", None, "The thunder god happily tears into the roast goat and chews, the peasants stare in horror, "
                   "firelight flickers. The painting comes alive."),
    "myth_rise": ("gen4.5", 5, "myth_rise", None, "Golden light bursts, the two goats spring up alive and shake themselves; one "
                  "limps on its crooked leg and glares at the camera. The painting comes alive."),
    "myth_julbock": ("gen4.5", 5, "myth_julbock", None, "The straw goat figure knocks and bows, the children giggle and reach for "
                     "presents, snow falls, candlelight flickers. The painting comes alive."),
    "unmask": ("veo3.1", 8, "unmask_a", "unmask_b", "Santa and the gingerbread man face the camera, pause dramatically, then "
               "simultaneously rip off their disguises, revealing two grotesque satirical latex puppets who grin guiltily. "
               "Fire crackles behind them. Comedic reveal."),
    "unmask_pre": ("gen4.5", 4, "unmask_a", None, "Santa and the gingerbread man stare into the camera, slowly tighten their grip on "
                   "their masks, dramatic pause, snow falling, fire crackling behind them. Tense, comedic."),
    "unmask_post": ("gen4.5", 5, "unmask_b", None, "The two satirical latex puppets grin guiltily at the camera, glance at each "
                    "other, shrug, and slowly lower the masks they are holding. Fire crackles behind them. Comedic."),
    "naruto": ("gen4.5", 6, "naruto", None, "The two satirical puppets Naruto-run at full speed across the snowy square and out "
               "of frame to the right, arms stretched straight behind them, snow spraying, the goat burning behind. Fast, comedic."),
}


def image(name):
    prompt, ref = IMAGES[name]
    body = {"model": "gemini_image3_pro", "promptText": prompt, "ratio": "2752:1536"}
    if ref:
        body["referenceImages"] = [{"uri": runway.url_of(f"media/img/{ref}.png"), "tag": "ref", "subject": "object"}]
    return runway.run("text_to_image", body, f"media/img/{name}.png", name)


def video(name):
    model, secs, first, last, prompt = VIDEOS[name]
    pi = runway.url_of(f"media/img/{first}.png")
    body = {"model": model, "promptText": prompt, "duration": secs}
    if model.startswith("veo"):
        body |= {"ratio": "1920:1080", "audio": False,
                 "promptImage": [{"uri": pi, "position": "first"}] + ([{"uri": runway.url_of(f"media/img/{last}.png"), "position": "last"}] if last else [])}
    else:
        body |= {"ratio": "1280:720", "promptImage": pi}
    return runway.run("image_to_video", body, f"media/vid/{name}.mp4", name)


if __name__ == "__main__":
    what = sys.argv[1]
    names = sys.argv[2:] or list(IMAGES if what == "img" else VIDEOS)
    for n in names:
        try:
            print("ok", n, (image if what == "img" else video)(n), flush=True)
        except Exception as e:
            print("FAIL", n, e, flush=True)
