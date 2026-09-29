"""Stage 1: keyframe stills, all anchored on the hero goat for continuity."""
import concurrent.futures as cf
import runway

GOAT = ("the giant 13-metre straw Yule goat from the reference image (golden straw bundles, huge curved straw horns, "
        "red ribbon bands on neck, belly and legs)")
LOOK = ("Photorealistic, shot on 35mm anamorphic, cinematic lighting, hyper-saturated candy-colored grade "
        "like a big-budget animated blockbuster made real, 16:9 film frame, no text, no captions, no watermark.")

FRAMES = {
    "soliloquy": f"Extreme close-up portrait of the face of {GOAT}, at night on a snowy square, lit by a single theatrical "
                 "spotlight from above like a Shakespearean actor on a stage, snowflakes drifting through the beam, "
                 "deep black background, its straw eye catching a glint of light, noble and tragic.",
    "y1966": f"Vintage 1966 New Year's Eve at midnight: {GOAT} fully ablaze in a snowy Swedish town square, towering flames, "
             "fireworks bursting overhead, a crowd in 1960s wool coats and fur hats staring in shock, champagne bottles. "
             "Grainy Kodachrome film look, warm faded colors.",
    "y1973": f"Dawn in a tiny 1970s Swedish suburban backyard: {GOAT} has been stolen and is absurdly crammed into the small "
             "garden between a laundry line and a wooden fence, its horns poking above the roof of a red cottage. A middle-aged "
             "man in a bathrobe and slippers stands beside it calmly sipping coffee, garden gnome at his feet. Kodachrome.",
    "y1976": f"Night, snow: a 1960s Volvo Amazon car crashing into the hind leg of {GOAT}; a frozen-in-time explosion of "
             "straw and snow mid-air, headlights blazing, dramatic action-movie slow-motion moment.",
    "y2010": f"Night heist thriller: a black helicopter with searchlights lifts {GOAT} into the snowy sky over a sleeping "
             "Swedish town with steel cables, straw raining down, dramatic low angle, Mission-Impossible energy.",
    "burning": f"{GOAT} completely engulfed in towering orange flames at night in a snowy square, embers swirling into the "
               "dark blue sky, firefighters with hoses silhouetted, fire trucks with flashing lights, epic and tragic.",
    "y2016": f"Dusk: {GOAT} celebrating its 50th birthday: wearing a gigantic striped party hat, a huge '50' balloon tied to "
             "a horn, confetti in the air, bunting and a birthday banner, a crowd of Swedes holding a giant cake with sparklers. "
             "Joyful and ridiculous.",
    "guard": f"Mockumentary interview framing: a weary middle-aged Swedish security guard with a moustache, hi-vis jacket and "
             f"fur trapper hat, standing off-centre facing camera at night, {GOAT} glowing behind him in the snow, frost on his "
             "moustache, flat awkward documentary lighting.",
    "santa": f"Night, heavy snow, epic heist: Santa Claus and a person in a full-body human-sized gingerbread-man costume "
             "crouch behind a snowbank like special-forces commandos. Santa draws a wooden longbow with a flaming arrow, the "
             f"gingerbread man holds binoculars. {GOAT} glows in the distance across the square.",
    "arrow": f"Extreme slow-motion macro shot of a flaming arrow in flight through falling snowflakes at night, fire trailing, "
             f"sparks and embers, {GOAT} out of focus in the far background. Epic.",
    "impact": f"The flaming arrow strikes {GOAT}: a colossal bloom of fire engulfs it, embers exploding outward. In the "
              "foreground Santa Claus and a person in a gingerbread-man costume high-five, silhouetted against the fireball.",
    "triumph": f"Heroic low-angle shot of {GOAT}, completely intact, in the snowy square at golden sunrise, god rays through "
               "clouds, fireworks and a rainbow, confetti, a choir of townspeople cheering. Triumphant, glorious, over the top.",
    "birds": f"Overcast grey day: {GOAT} being swarmed by hundreds of black jackdaws pecking at it, tearing out straw, "
             "straw and feathers flying everywhere, Hitchcock 'The Birds' horror energy.",
    "storm": f"Violent night storm, horizontal snow and wind: {GOAT} tilting forward, starting to topple onto its nose, "
             "straw ripping away in the gale, street lamps swaying.",
    "ink": "A traditional ancient Chinese ink-wash painting on aged silk: a giant straw Yule goat with curved horns standing "
           "serenely on a misty mountain ledge beside a pine tree, an old sage riding an ox passing by below, red seal stamp. "
           "Minimal, elegant, lots of empty space. No text.",
}


def job(name, prompt):
    body = {"model": "gemini_image3_pro", "promptText": prompt + " " + LOOK, "ratio": "2752:1536",
            "referenceImages": [{"uri": runway.url_of("media/img/hero_goat.png"), "tag": "goat", "subject": "object"}]}
    if name == "ink":
        body["promptText"] = prompt
    return runway.run("text_to_image", body, f"media/img/{name}.png", name)


if __name__ == "__main__":
    with cf.ThreadPoolExecutor(2) as ex:
        futs = {ex.submit(job, n, p): n for n, p in FRAMES.items()}
        for f in cf.as_completed(futs):
            try:
                print("ok", futs[f], f.result(), flush=True)
            except Exception as e:
                print("FAIL", futs[f], e, flush=True)
    print("credits", runway.credits())
