"""Stage 2: animate keyframes. One worker per model (tier allows 1 concurrent each)."""
import concurrent.futures as cf
import pathlib
import sys
import time
import runway

# name: (model, seconds, audio, motion prompt)
SHOTS = {
    # --- Veo 3.1 lane ---
    "open": ("veo3.1", 8, False, "Very slow majestic cinematic push-in toward the giant straw goat in the snowy square at night. "
             "Snow falls gently, lamps glow, a couple walks past. Perfect stillness and peace."),
    "guard": ("veo3.1", 8, True, "Mockumentary interview. The tired Swedish security guard looks into the camera and says in a flat, "
              "deadpan Swedish accent: \"It was minus twenty. The goat seemed fine. So we went to the restaurant.\" "
              "He pauses, stares, blinks slowly. Awkward silence. Wind and distant snow ambience, no music."),
    "santa": ("veo3.1", 8, True, "Night heist. Santa Claus, crouched behind the snowbank, slowly draws the longbow; the flaming arrow "
              "crackles. He whispers gravely: \"Ho. Ho. Go.\" The gingerbread man lowers his binoculars and nods. "
              "Crackling fire, soft wind, tense silence. Cinematic."),
    "impact": ("veo3.1", 8, False, "Slow-motion: the fireball blooms across the giant straw goat, embers erupt into the night sky "
               "like fireworks, Santa and the gingerbread man high-five in silhouette, snow and sparks swirl. Epic, spectacular."),
    # --- Gen-4.5 lane ---
    "soliloquy": ("gen4.5", 10, False, "Slow dramatic orbit around the straw goat's face under the theatrical spotlight. The goat slowly "
                  "raises its head and turns toward the camera as if delivering a tragic Shakespearean monologue. Snow drifts through the beam."),
    "y1966": ("gen4.5", 5, False, "Flames roar higher up the burning goat, fireworks burst, the shocked 1960s crowd gasps and "
              "clutches each other, a champagne cork pops. Vintage film grain."),
    "y1973": ("gen4.5", 5, False, "The man in the bathrobe takes a slow sip of coffee and looks deadpan at the camera; laundry "
              "flutters in the breeze. The giant straw goat's head slowly turns to look at him."),
    "y1976": ("gen4.5", 5, False, "Super slow motion: the vintage Volvo slams into the goat's leg, straw explodes outward in a huge "
              "golden cloud, snow and straw fly past the camera. Action movie."),
    "y2010": ("gen4.5", 6, False, "The helicopter lifts the giant straw goat higher into the snowy night sky, cables swaying, "
              "searchlights sweeping, straw raining down on the town. Thriller tension, camera tilts up."),
    "burning": ("gen4.5", 6, False, "The fire roars and climbs the giant goat, embers spiral into the sky, firefighters spray "
                "water, lights flash. Epic slow push-in."),
    "y2016": ("gen4.5", 5, False, "The crowd cheers and throws confetti, sparklers fizz on the cake, the balloon bobs, the party-hat "
              "goat stands proudly. Joyful celebration, handheld camera."),
    "arrow": ("gen4.5", 6, False, "Extreme slow-motion tracking shot following the flaming arrow as it flies through falling snow, "
              "fire and sparks trailing, the goat growing larger ahead. Epic."),
    "triumph": ("gen4.5", 5, False, "Heroic slow crane up past the intact straw goat at sunrise, fireworks burst, confetti falls, "
                "god rays shimmer, the crowd cheers. Glorious."),
    "birds": ("gen4.5", 8, False, "Hundreds of jackdaws swarm and peck the straw goat, ripping out straw that flies in all directions, "
              "the goat slowly disintegrating. Chaotic, Hitchcock horror."),
    "storm": ("gen4.5", 6, False, "A violent gust of wind: the giant straw goat topples forward and falls face-first onto its nose in "
              "the snow with a heavy thud, snow bursting up. Comedic, slow motion."),
    "ink": ("gen4.5", 6, False, "Subtle living ink painting: mist drifts slowly across the mountain, the pine sways gently, "
            "the sage on the ox walks slowly past. Calm, meditative."),
}


def job(name):
    model, secs, audio, prompt = SHOTS[name]
    img = pathlib.Path(f"media/img/{'hero_goat' if name == 'open' else name}.png")
    while not img.exists():
        time.sleep(10)
    body = {"model": model, "promptText": prompt, "promptImage": runway.url_of(img), "duration": secs}
    if model.startswith("veo"):
        body |= {"ratio": "1920:1080", "audio": audio}
    else:
        body |= {"ratio": "1280:720"}
    return runway.run("image_to_video", body, f"media/vid/{name}.mp4", name)


def lane(names):
    for n in names:
        try:
            print("ok", n, job(n), flush=True)
        except Exception as e:
            print("FAIL", n, e, flush=True)


if __name__ == "__main__":
    want = sys.argv[1:] or list(SHOTS)
    veo = [n for n in want if SHOTS[n][0].startswith("veo")]
    gen = [n for n in want if not SHOTS[n][0].startswith("veo")]
    with cf.ThreadPoolExecutor(2) as ex:
        list(ex.map(lane, [veo, gen]))
    print("credits", runway.credits())
