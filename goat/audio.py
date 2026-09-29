"""Stage 3: voiceover (ElevenLabs v3), sound effects (ElevenLabs SFX), score (Seed Audio)."""
import concurrent.futures as cf
import runway

HYPE, GOAT, DEADPAN, SAGE = "Kendrick", "Malachi", "James", "Ragnar"

VO = {
    "hype_intro": (HYPE, "[excited] This is a THIRTEEN-METRE GOAT. Made of STRAW. Sweden builds it every single year... "
                         "[shouting] and every single year, SWEDEN TRIES TO DESTROY IT!"),
    "hype_count": (HYPE, "[shouting] Burned! Stolen! Hit by a car! Shot with a FLAMING ARROW! FORTY-THREE TIMES!"),
    "goat_solo": (GOAT, "To burn... or not to burn? [sighs] That is never the question. "
                        "Each December they raise me up. Three tonnes of straw... and hope. "
                        "And each December, some reveller with a lighter composes my eulogy. "
                        "Out, out, brief candle! [pause] ...I am the candle."),
    "log_1966": (HYPE, "Nineteen sixty-six! The very first goat! Burned at midnight on New Year's Eve!"),
    "log_1973": (HYPE, "Seventy-three! Stolen! Found in a guy's back garden!"),
    "log_1976": (HYPE, "Seventy-six! Hit! By a VOLVO!"),
    "log_2001": (HYPE, "Two thousand one! An American tourist burns it down. His defence? [laughs] He thought it was a legal tradition!"),
    "log_2001b": (DEADPAN, "The court confiscated his lighter, on the grounds that he was not able to handle it."),
    "log_2010": (HYPE, "Twenty-ten! Someone offers a guard fifty thousand kronor to look away... so they can steal the goat. [whispers] By helicopter."),
    "log_2010b": (DEADPAN, "It did not work."),
    "log_2012": (HYPE, "Twenty-twelve! The goat's official account tweets: feeling good. [pause] Ten minutes later..."),
    "log_2016": (HYPE, "Twenty-sixteen! Its fiftieth birthday party! [shouting] Burned! The same! Night!"),
    "xkcd": (DEADPAN, "What if you tried to protect a straw goat? Sweden tried everything. A fence. Chicken wire. Soldiers. "
                      "Taxi drivers. They sprayed it with aircraft fire retardant, which worked, but made the goat look, quote, "
                      "like a brown terrier. They covered it in ice. [pause] The ice melted. "
                      "In two thousand three it was so cold that the guards went inside a restaurant. [pause] "
                      "The goat did not go inside the restaurant."),
    "santa_setup": (HYPE, "[whispers] But the greatest attack of all came on the third of December, two thousand five... "
                          "when Santa Claus... and the Gingerbread Man..."),
    "santa_pay": (HYPE, "[shouting] SHOT IT WITH A FLAMING ARROW!"),
    "santa_true": (DEADPAN, "This is real. It was featured on Sweden's version of America's Most Wanted."),
    "twist_count": (HYPE, "[excited] Then, twenty seventeen: it survives! Twenty eighteen! Twenty nineteen! Twenty twenty! "
                          "[shouting] FOUR YEARS UNDEFEATED!"),
    "goat_triumph": (GOAT, "[triumphant] Behold! Four winters! The fire cannot touch me! I am... ETERNAL!"),
    "birds_2023": (DEADPAN, "Twenty twenty-three. [pause] It was eaten by birds."),
    "birds_why": (DEADPAN, "The straw had unusually many seeds in it. Jackdaws."),
    "sage": (SAGE, "It withstood fire. Ice. Arrows. A Volvo. And a helicopter. [pause] It was undone by small birds... "
                   "who were simply hungry. [pause] Nature does not hurry... yet everything is accomplished."),
    "post_2025": (DEADPAN, "Twenty twenty-five. A storm blew it over. [pause] It landed on its nose."),
    "goat_fine": (GOAT, "[muffled, face down in the snow] ...I'm fine."),
    "hype_outro": (HYPE, "[excited] It will be rebuilt. It ALWAYS is."),
}

SFX = {
    "match": ("A single match striking and flaring into flame, close and crisp, in silence", 2),
    "boom": ("Huge cinematic trailer impact boom with deep sub bass and metallic ring", 3),
    "braam": ("Massive Inception-style brass BRAAM trailer hit, long decay", 4),
    "whoosh": ("Fast airy swoosh transition whoosh", 1),
    "whoosh2": ("Deep heavy cinematic swoosh pass-by", 1.5),
    "riser": ("Tense rising cinematic riser building to a climax, synth and strings", 4),
    "scratch": ("Vinyl record scratch stop, comedic", 1),
    "register": ("Cash register cha-ching", 1.5),
    "counter": ("Rapid digital counter ticking up fast, game show slot machine clicks", 2),
    "ding": ("Game show correct answer ding ding ding", 1.5),
    "buzzer": ("Game show wrong answer buzzer", 1.5),
    "fire": ("Huge roaring bonfire, crackling and whooshing flames", 6),
    "ignite": ("Petrol fireball igniting whoomph, big", 2),
    "crash": ("Vintage car crashing into a giant pile of straw, crunch and soft explosion of hay", 2.5),
    "heli": ("Helicopter hovering overhead at night, rotor thumping", 6),
    "tweet": ("Cute notification chirp tweet sound", 1),
    "clock": ("Loud clock ticking, suspenseful, speeding up", 4),
    "arrow": ("Flaming arrow whistling past in slow motion, fire whoosh", 2.5),
    "crowd_gasp": ("Crowd of people gasping in shock", 2),
    "crowd_cheer": ("Large crowd cheering wildly with applause and whistles", 4),
    "party": ("Party horn blower toot and confetti cannon pop", 1.5),
    "birds": ("Huge flock of jackdaws cawing and flapping wings, chaotic", 6),
    "wind": ("Violent winter storm wind howling", 6),
    "thud": ("Giant soft object falling face first into deep snow, big muffled thud", 2),
    "snow_amb": ("Quiet snowy winter night ambience, soft wind, very distant town", 10),
    "gong": ("Deep resonant Chinese temple gong, long decay", 5),
    "pencil": ("Pencil scribbling quickly on paper", 2),
    "shutter": ("Camera shutter click and flash whine", 1),
    "bow": ("Wooden longbow string creaking as it is drawn tight", 2),
    "gulp": ("Cartoon gulp swallow", 1),
    "heavenly": ("Heavenly choir 'aaah' swell, angelic", 3),
    "stamp": ("Heavy rubber stamp slam on paper", 1),
}

MUSIC = {
    "m_serene": "Gentle Swedish Christmas choir humming a slow peaceful hymn, soft celesta and strings, snowy night, instrumental with wordless choir, 20 seconds",
    "m_hype": "High-energy YouTube hype trap beat, 150 BPM, punchy 808 bass, brass stabs, air horns, aggressive and exciting, instrumental, 30 seconds",
    "m_shakes": "Dramatic tragic Elizabethan theatre music, solo harpsichord and mournful strings, Shakespearean, slow and grand, instrumental, 30 seconds",
    "m_montage": "Driving fast heist-movie montage music, breakbeat drums, surf-rock guitar, orchestral hits, spy thriller, instrumental, 30 seconds",
    "m_xkcd": "Quirky playful pizzicato strings and glockenspiel, nerdy explainer video background music, light and curious, instrumental, 30 seconds",
    "m_epic": "Epic slow-motion Hans Zimmer style orchestral cue, huge choir, taiko drums, rising brass, heroic and ridiculous, instrumental, 30 seconds",
    "m_triumph": "Triumphant victorious orchestral fanfare, trumpets, timpani, cymbals, glorious sports victory, instrumental, 15 seconds",
    "m_zen": "Serene ancient Chinese guzheng and bamboo flute, meditative, slow, sparse, instrumental, 25 seconds",
    "m_credits": "Joyful upbeat Swedish folk polka with fiddle and accordion, celebratory end credits, instrumental, 25 seconds",
}


def vo(name):
    voice, text = VO[name]
    body = {"model": "eleven_v3", "promptText": text, "voice": {"type": "runway-preset", "presetId": voice}}
    if voice == HYPE:
        body["speed"] = 1.1
    return runway.run("text_to_speech", body, f"media/vo/{name}.mp3", name)


def sfx(name):
    prompt, dur = SFX[name]
    return runway.run("sound_effect", {"model": "eleven_text_to_sound_v2", "promptText": prompt, "duration": dur},
                      f"media/sfx/{name}.mp3", name)


def music(name):
    return runway.run("sound_effect", {"model": "seed_audio", "promptText": MUSIC[name], "outputFormat": "wav",
                                       "sampleRate": 44100}, f"media/music/{name}.wav", name)


def lane(fn, names):
    for n in names:
        try:
            fn(n)
            print("ok", n, flush=True)
        except Exception as e:
            print("FAIL", n, e, flush=True)


if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["vo", "sfx", "music"]
    lanes = {"vo": (vo, list(VO)), "sfx": (sfx, list(SFX)), "music": (music, list(MUSIC))}
    with cf.ThreadPoolExecutor(3) as ex:
        list(ex.map(lambda k: lane(*lanes[k]), which))
