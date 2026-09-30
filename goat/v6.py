"""v6 assets: more destruction stories, Santa actually aiming at the goat, and a goat that never moves."""
import sys
import runway

GOAT = ("the giant 13-metre straw Yule goat from the reference image (golden straw, huge curved horns, red ribbon bands) — a rigid, "
        "motionless straw sculpture on a wooden frame")
LOOK = "Photorealistic, cinematic 35mm, rich saturated colour grade, 16:9 film frame, no text, no captions, no watermark."
STATIC = " The straw goat is a rigid inanimate sculpture and does not move at all; only fire, smoke, snow and people move."

IMAGES = {  # name: prompt (all anchored on the hero goat)
    "n1970": f"Night, snowy Swedish town square: {GOAT} is engulfed in roaring flames while two drunk 1970s teenagers in flared "
             f"jeans and big hair sprint away toward the camera, one still holding a bottle, panicked grins. {LOOK}",
    "n1985": f"Night, snowy square: three 1980s Swedish army soldiers in winter uniforms and a Securitas guard stand at attention in "
             f"front of a metal fence, proudly facing the camera, completely unaware that {GOAT} behind them is on fire, huge "
             f"flames rising. Comedic. {LOOK}",
    "n2012": f"Night: {GOAT} completely ablaze in a colossal inferno, a towering column of flame and black smoke, embers swirling "
             f"into the sky, the whole square lit orange, a small crowd silhouetted. Epic. {LOOK}",
    "n2015": ("Night, snow, police flashlight beams: a sheepish 26-year-old man caught by two Swedish police officers, his face "
              "blackened with soot, eyebrows singed and smoking, hair frizzled, holding a lighter and a petrol can, a burning straw "
              f"goat glowing behind him. Deadpan comedy. {LOOK}"),
    "santa_aim": (f"Night, heavy snow, epic heist: over-the-shoulder shot from behind Santa Claus (red suit, tactical vest) kneeling "
                  f"on a snowbank, drawing a wooden longbow with a flaming arrow pointed straight at {GOAT} which stands in the "
                  f"centre of the square in the distance; a person in a gingerbread-man costume crouches beside him with binoculars "
                  f"also looking at the goat. {LOOK}"),
    "arrow_hit": (f"Night, snowy square, wide shot: a flaming arrow streaks in a bright arc across the dark sky from the left and "
                  f"is about to strike {GOAT}, which stands in the centre; sparks and a fiery trail behind the arrow. {LOOK}"),
}

VIDEOS = {  # name: (model, seconds, image, prompt)
    "n1970": ("gen4_turbo", 5, "n1970", "The teenagers sprint toward and past the camera laughing and panicking, the fire roars higher."),
    "n1985": ("gen4_turbo", 5, "n1985", "The soldiers stand proudly at attention, one salutes; behind them the fire grows enormous. "
              "They do not notice."),
    "n2012": ("gen4_turbo", 5, "n2012", "The inferno roars and billows, embers and smoke pour into the sky, slow push-in."),
    "n2015": ("gen4_turbo", 5, "n2015", "The man looks at the camera, his singed eyebrows smoke, he shrugs awkwardly; police "
              "flashlights sweep over him."),
    "n1973": ("gen4_turbo", 5, "y1973", "The man in the bathrobe sips his coffee and looks deadpan at the camera, laundry flutters."),
    "n2025": ("gen4_turbo", 5, "storm", "A violent gust hits: the whole rigid straw sculpture tips forward as one solid object, "
              "without bending, and crashes flat onto its face in the snow, snow exploding upward. Slow motion."),
    "santa_aim": ("gen4.5", 5, "santa_aim", "Santa slowly draws the bow tighter, aiming at the straw goat, the arrow flame flickers, "
                  "then he releases and the flaming arrow flies straight toward the goat."),
    "arrow_hit": ("gen4.5", 5, "arrow_hit", "The flaming arrow arcs across the sky and slams into the straw goat, which instantly "
                  "erupts in a huge fireball explosion, flames engulfing it."),
}


def image(name):
    body = {"model": "gemini_image3_pro", "promptText": IMAGES[name], "ratio": "2752:1536",
            "referenceImages": [{"uri": runway.url_of("media/img/hero_goat.png"), "tag": "goat", "subject": "object"}]}
    return runway.run("text_to_image", body, f"media/img/{name}.png", name)


def video(name):
    model, secs, img, prompt = VIDEOS[name]
    if name != "n2025":  # the storm shot is the one where the goat is meant to fall
        prompt += STATIC
    body = {"model": model, "promptImage": runway.url_of(f"media/img/{img}.png"), "promptText": prompt, "ratio": "1280:720",
            "duration": secs}
    return runway.run("image_to_video", body, f"media/vid/{name}.mp4", name)


if __name__ == "__main__":
    what, names = sys.argv[1], sys.argv[2:]
    names = names or list(IMAGES if what == "img" else VIDEOS)
    for n in names:
        try:
            print("ok", n, (image if what == "img" else video)(n), flush=True)
        except Exception as e:
            print("FAIL", n, e, flush=True)


# ---- narration: ONE narrator, one accent, excited the whole way ----------------------------------------
NARRATION = {
    "myth": "A thousand years ago, the Norse god of thunder had two magic goats. Every night... he ATE them! [laughs] "
            "And every morning, BOOM, magic hammer, they are alive again!",
    "thesis": "So in Sweden, the goat is Christmas! A goat that dies... and comes BACK!",
    "g1966": "Nineteen sixty-six! The town of Gävle builds the biggest goat EVER! Thirteen metres! Designed by... "
             "the fire chief's brother! [pause] It burned on New Year's Eve.",
    "grid": "Since then? Forty-three goats DESTROYED! [excited] Let me tell you about some of them!",
    "r1970": "Nineteen seventy! Two drunk teenagers. Six hours. GONE!",
    "r1973": "Seventy-three! Stolen! Found in a man's back garden!",
    "r1976": "Seventy-six! Hit by a VOLVO! [laughs] A Swedish goat, killed by a Swedish car!",
    "r1985": "Eighty-five! A fence! Security guards! The ARMY! [pause] Burned anyway.",
    "r2001": "Two thousand one! An American tourist burns it down. He says, I thought it was a tradition! [laughs] It was NOT a tradition!",
    "r2003": "Two thousand three! Minus twenty degrees, so the guards go inside for soup. [pause] The goat does not go inside for soup.",
    "r2005": "Two thousand five! The WORST one! Santa Claus... and the Gingerbread Man... with a bow... and a FLAMING ARROW!",
    "r2012": "Twenty-twelve! The goat's own Twitter says: feeling good. [pause] Ten minutes later... [shouting] FIRE!",
    "r2015": "Twenty-fifteen! Police catch a guy running away. Burned face, smells like petrol, holding a lighter. "
             "He says: this was an extremely bad idea. [laughs]",
    "r2016": "Twenty-sixteen! The fiftieth birthday party! Burned. The. Same. NIGHT!",
    "r2023": "Twenty twenty-three... EATEN! By BIRDS!",
    "r2025": "Twenty twenty-five! A storm! It falls flat on its FACE!",
    "reveal": "But wait! The Santa and Gingerbread Man from two thousand five... finally unmasked! [gasps] WHAT?!",
    "run": "[shouting] They are running away!",
    "outro": "Next year, Sweden builds the goat again! And then... [laughs] we see what happens! Ja!",
}


def narrate(voice, accent, names=None):
    for n in names or NARRATION:
        runway.run("text_to_speech", {"model": "eleven_v3", "voice": {"type": "runway-preset", "presetId": voice},
                                      "promptText": f"[strong {accent} accent] [excited] " + NARRATION[n], "style": 0.9},
                   f"media/vo6/{n}.mp3", "vo6_" + n)
        print("ok", n, flush=True)


# ---- v9 narration additions (same narrator) ------------------------------------------------------
NARRATION_V9 = {
    "g1966b": "Nineteen sixty-six! A little town called Gävle decides: we build a GIANT goat! Thirteen metres tall! "
              "Designed by... the fire chief's brother! [pause] But then...",
    "grid2": "Since then... Swedes keep TORCHING the goat! [excited] Forty-three out of sixty! [laughs] Let me tell you about some of them!",
    "r2012b": "Twenty-twelve! The goat's own Twitter says: feeling good. [pause] Ten minutes later... [shouting] feeling HOT!",
    "r2015b": "Twenty-fifteen! Police catch a guy running away. Burned face, smells like petrol, holding a lighter. And he says...",
    "outro2": "This year, Sweden builds the goat again! Will it survive... or become a BONFIRE? [excited] Make your prediction in the comments!",
}


def narrate_v9(voice="Ragnar", accent="Swedish", names=None):
    for n in names or NARRATION_V9:
        runway.run("text_to_speech", {"model": "eleven_v3", "voice": {"type": "runway-preset", "presetId": voice},
                                      "promptText": f"[strong {accent} accent] [excited] " + NARRATION_V9[n], "style": 0.9},
                   f"media/vo6/{n}.mp3", "vo9_" + n)
        print("ok", n, flush=True)
