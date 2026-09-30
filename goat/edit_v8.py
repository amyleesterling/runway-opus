"""THE G.O.A.T. — v8 edit: v6 with a tease ending ("we know who really did it") instead of the unmasking. Builds render/timeline.json + media/mix.wav.

Every sequence is laid out on a running cursor and synced to measured VO phrase timings (media/vo.json).
"""
import json
import pathlib
import subprocess

FPS = 24
VOJ = json.load(open("media/vo.json"))
LAYERS, AUDIO = [], []


def clipinfo():
    out = {}
    for d in sorted(pathlib.Path("media/frames").glob("*")):
        out[d.name] = {"frames": len(list(d.glob("*.jpg")))}
    return out


def V(clip, start, dur, **kw):
    LAYERS.append({"type": "video", "clip": clip, "start": start, "dur": dur, **kw})


def G(type_, start, dur, **kw):
    LAYERS.append({"type": type_, "start": start, "dur": dur, **kw})


def A(src, start, gain=0.0, trim=0.0, dur=None, fi=0.0, fo=0.0, fx=None):
    AUDIO.append({"src": src, "start": start, "gain": gain, "trim": trim, "dur": dur, "fi": fi, "fo": fo, "fx": fx})


def S(name, start, gain=-4.0, **kw):
    A(f"media/sfx/{name}.mp3", start, gain, **kw)


def M(name, start, dur, gain=-12.0, fi=0.3, fo=1.0, trim=0.0):
    p = pathlib.Path(f"media/music/{name}.wav")
    if p.exists():
        A(str(p), start, gain, trim=trim, dur=dur, fi=fi, fo=fo)


def VO(name, start, gain=0.0, fx=None, maxgap=None):
    """Place VO so its first phrase begins at `start`. Returns (length, phrase list in timeline time).
    With maxgap, pauses longer than maxgap seconds are shortened by splitting the line at its phrases."""
    v = VOJ[name]
    if not maxgap:
        A(f"media/vo/{name}.mp3", start, gain, trim=v["a"], dur=v["b"] - v["a"] + 0.15, fx=fx)
        segs = [[start + s - v["a"], start + e - v["a"]] for s, e in v["segs"]]
        return v["b"] - v["a"], segs
    # group phrases separated by short gaps, then re-space groups
    groups = [[v["segs"][0][0], v["segs"][0][1]]]
    for s, e in v["segs"][1:]:
        if s - groups[-1][1] > maxgap:
            groups.append([s, e])
        else:
            groups[-1][1] = e
    shift, t, out = {}, start, []
    for gi, (gs, ge) in enumerate(groups):
        pre = 0.05
        A(f"media/vo/{name}.mp3", t - pre, gain, trim=max(0, gs - pre), dur=ge - gs + pre + 0.12, fx=fx)
        for s, e in v["segs"]:
            if gs <= s < ge + 1e-6:
                out.append([t + s - gs, t + e - gs])
        t += ge - gs + maxgap
    return t - maxgap - start, out


def FX(clip, t, dur, alpha=1.0, **kw):
    """Composite a Runway fire plate (shot on black) with screen blending."""
    kw.setdefault("grade", {"con": 1.4, "bri": 1.05, "sat": 1.2})
    V(clip, t, dur, blend="screen", alpha=alpha, **kw)


def BOOM(t, big=1.0, x=None, y=None):
    """Fireball + shockwave + audio for an explosion beat."""
    FX("fx_fireball", t, 2.4, kb={"z0": 1.1 * big, "z1": 1.4 * big}, fo=.8)
    G("shock", t, .9, **({"x": x} if x else {}), **({"y": y} if y else {}))
    S("ignite", t, -2); S("boom", t, -4)


def grade_vintage():
    return {"sepia": .35, "sat": .85, "con": 1.1}


# =====================================================================


VO6J = json.load(open("media/vo6.json"))


def N(name, start, gain=1.0, maxgap=.3, speed=1.2):
    """Narrator line (media/vo6) at `start`, sped up `speed`x (pitch kept), long pauses squeezed. Returns (length, phrases)."""
    v = VO6J[name]
    groups = [[v["segs"][0][0], v["segs"][0][1]]]
    for s_, e_ in v["segs"][1:]:
        if s_ - groups[-1][1] > maxgap * speed:
            groups.append([s_, e_])
        else:
            groups[-1][1] = e_
    t, out = start, []
    for gs, ge in groups:
        A(f"media/vo6/{name}.mp3", t - .05 / speed, gain, trim=max(0, gs - .05), dur=ge - gs + .17, fx=f"atempo={speed}")
        out += [[t + (s_ - gs) / speed, t + (e_ - gs) / speed] for s_, e_ in v["segs"] if gs <= s_ < ge + 1e-6]
        t += (ge - gs) / speed + maxgap
    return t - maxgap - start, out


def wipe(t, dir=1):
    G("wipe", t - .3, .6, dir=dir)
    S("whoosh2", t - .3, -6)


def slam(year, st):
    FX("fx_fireball", st - .05, 1.1, alpha=.3 if year == 1973 else .6, kb={"z0": 1.6}, fo=.4)
    G("yearSlam", st, .8, year=year)
    G("flash", st, .15, color="#fff", alpha=.6); G("shock", st, .6)
    S("boom", st, -6); S("whoosh", st - .08, -8)


def burn(st, dur, h=560):
    """Fire all over the frame: procedural flames + heat haze + crackle."""
    G("fire", st, dur, h=h, size=90, fi=.1)
    G("heat", st, dur, amt=.6)
    S("fire", st, -12, dur=dur, fo=.4)


def story(year, clip, line, tag, title, sub, *, speed=1.0, from_=0.0, fire=True, tail=.35, kb=None, grade=None):
    global T
    st = T
    slam(year, st)
    L, ph = N(line, st + .2)
    en = st + .2 + L + tail
    V(clip, st, en - st, speed=speed, from_=from_, kb=kb or {"z0": 1.05, "z1": 1.2}, grade=grade or {"sat": 1.25, "con": 1.08})
    G("lower", st + .7, en - st - .7, tag=tag, title=title, sub=sub)
    if fire:
        burn(st + .5, en - st - .5)
    T = en
    return st, en, ph


T = 0.0
# ---- MYTH -------------------------------------------------------------------------
M("m_epic", 0, 13.0, gain=-14, fi=.3, fo=.6)
L, ph = N("myth", .4)
cut1 = next((p[0] for p in ph if p[0] > .4 + L * .35), .4 + L * .4) - .1   # "Every night..."
cut2 = next((p[0] for p in ph if p[0] > .4 + L * .65), .4 + L * .7) - .1   # "And every morning..."
end = .4 + L + .3
V("myth_chariot", 0, cut1, kb={"z0": 1.12, "z1": 1.35}, fi=.3)
G("lower", .5, cut1 - .5, tag="NORSE MYTH", title="THE THUNDER GOD'S GOATS", sub="Tanngrisnir & Tanngnjóstr")
V("myth_feast", cut1, cut2 - cut1, kb={"z0": 1.0, "z1": 1.15})
G("beast", cut1, cut2 - cut1, words=[{"t": .6, "text": "HE ATE THEM!", "fill": "#ff2a2a", "size": 170, "y": 240, "rot": -3, "hold": 9}])
S("gulp", cut1 + .9, -2)
V("myth_rise", cut2, end - cut2, kb={"z0": 1.05, "z1": 1.2})
G("flash", cut2 + .5, .3, color="#ffe9a8", alpha=.7); G("shock", cut2 + .5, .7)
S("boom", cut2 + .5, -3); S("heavenly", cut2 + .6, -8)
G("beast", cut2, end - cut2, words=[{"t": .6, "text": "BOOM! ALIVE AGAIN!", "fill": "#ffd400", "size": 140, "y": 220, "rot": 2, "hold": 9}])
T = end
wipe(T)
st = T
L, ph = N("thesis", st + .2)
en = st + .2 + L + .4
V("myth_julbock", st, en - st, kb={"z0": 1.15, "z1": 1.3})
M("m_credits", st, en - st + .2, gain=-11, fi=.1, fo=.2)
G("beast", st, en - st, words=[{"t": ph[-1][0] - st - .1, "text": "A GOAT THAT DIES...", "fill": "#fff", "size": 110, "y": 200, "rot": -2, "hold": 9},
                               {"t": ph[-1][0] - st + .9, "text": "AND COMES BACK!", "fill": "#ff8a1f", "size": 130, "y": 340, "rot": 2, "hold": 9}])
T = en

# ---- 1966 -------------------------------------------------------------------------------
wipe(T)
st = T
M("m_montage", st, 30.0, gain=-16, fi=.2, fo=.8)
L, ph = N("g1966", st + .2)
t_burn = ph[-1][0] - .1          # "It burned on New Year's Eve."
V("open", st, t_burn - st, kb={"z0": 1.0, "z1": 1.1})
G("ruler", st + .6, min(4.0, t_burn - st - .6), x=1420, y0=930, y1=140, metres=13, items=[
    {"kind": "giraffe", "m": 5.5, "x": 1620, "label": "GIRAFFE", "t": 1.0}, {"kind": "human", "m": 1.8, "x": 1800, "label": "YOU", "t": 1.3}])
G("stamp", t_burn - 2.2, 2.1, text="DESIGNED BY:\nTHE FIRE CHIEF'S BROTHER", x=620, y=520, size=70, rot=-6, color="#ff2a2a")
S("stamp", t_burn - 2.2, -2)
en = ph[-1][1] + 1.6
V("y1966", t_burn, en - t_burn, kb={"z0": 1.15, "z1": 1.3}, grade=grade_vintage(), shake={"amp": 10, "decay": 1.5})
BOOM(t_burn, big=1.2)
burn(t_burn, en - t_burn)
G("yearSlam", t_burn + .1, 1.4, year="31 DEC 1966", size=150, y=220)
S("crowd_gasp", t_burn + .4, -6)
T = en

# ---- 43 --------------------------------------------------------------------------------
wipe(T, -1)
st = T
L, ph = N("grid", st + .2)
en = st + .2 + L + .6
G("solid", st, en - st, color="#0b1024")
G("particles", st, en - st, kind="embers", n=140, alpha=.7)
import random
order = random.Random(1966).sample(range(60), 43)
G("goatgrid", st, en - st, order=order, t0=.3, t1=min(en - st - .5, 3.0))
S("counter", st + .3, -10, dur=2.7); S("register", st + 3.0, -3); G("shock", st + 3.0, .8, y=140)
T = en

# ---- THE RAP SHEET (14 destructions) ----------------------------------------------------
story(1970, "n1970", "r1970", "1970", "6 HOURS", "two drunk teenagers")
story(1973, "n1973", "r1973", "1973", "STOLEN", "found in a man's back garden", fire=False, grade=grade_vintage())
st, en, ph = story(1976, "y1976", "r1976", "1976", "HIT BY A VOLVO", "Volvo Amazon · hind legs", speed=.7, fire=False, grade=grade_vintage())
S("crash", st + .35, -2); G("zoomblur", st + .4, .4)
st, en, ph = story(1985, "n1985", "r1985", "1985", "GUARDED BY THE ARMY", "burned anyway")
G("stamp", ph[-1][0], en - ph[-1][0], text="BURNED\nANYWAY", x=1450, y=300, size=100, rot=-10)
S("stamp", ph[-1][0], -2)
st, en, ph = story(2001, "burning", "r2001", "2001", "THE TOURIST", "“I thought it was a tradition”", speed=.6)
G("stamp", ph[-1][0], en - ph[-1][0], text="NOT A\nTRADITION", x=1400, y=300, size=100, rot=-10)
S("stamp", ph[-1][0], -2)
# 2005 — the arrow (Santa now actually aims at the goat)
wipe(T)
st = T
slam(2005, st)
L, ph = N("r2005", st + .2)
t_arrow = ph[-1][0] - .2
D = t_arrow - st
V("santa_aim", st, D, speed=min(1.0, 2.3 / D), kb={"z0": 1.0, "z1": 1.15})   # ends on the release, before the goat ignites
G("news", st + .3, D - .3, tag="2005", headline="SANTA & GINGERBREAD MAN OPEN FIRE",
  ticker="NORTH POLE DENIES INVOLVEMENT  •  GINGERBREAD MAN SEEN WITH BINOCULARS  •  GOAT UNAVAILABLE FOR COMMENT")
S("bow", t_arrow - .9, 0)
KB = t_arrow + 1.25                  # arrow lands, goat explodes (inside the arrow_hit clip)
V("arrow_hit", t_arrow, 4.4, kb={"z0": 1.0, "z1": 1.15}, shake={"amp": 22, "decay": 1.0})
S("arrow", t_arrow, -1); FX("fx_embers", t_arrow, 4.4, alpha=.7)
BOOM(KB, big=1.4); FX("fx_shockwave", KB + .1, 2.0, alpha=.9, fo=.5)
FX("fx_fireball", KB + .4, 2.4, alpha=.55, kb={"z0": 2.0, "x0": -.25}, fo=.8)
FX("fx_fireball", KB + .7, 2.4, alpha=.55, kb={"z0": 1.8, "x0": .28}, fo=.8)
G("zoomblur", KB, .8, amt=2); G("rgbsplit", KB, .9, amt=24); G("particles", KB, 1.6, kind="sparks", n=220, fi=0)
burn(KB, t_arrow + 4.4 - KB, h=660)
S("braam", KB + .1, -3)
Im = t_arrow + 4.4
V("impact", Im, 3.4, from_=1.0, kb={"z0": 1.15, "z1": 1.0}, grade={"sat": 1.45, "con": 1.15}, shake={"amp": 10, "decay": 1.5})
burn(Im, 3.4, h=620)
G("beast", Im, 3.4, words=[{"t": .05, "text": "FLAMING", "fill": "#ffb300", "rot": -4, "size": 230, "y": 430, "hold": 4},
                           {"t": .5, "text": "ARROW!!!", "fill": "#ff2a2a", "rot": 3, "size": 260, "y": 660, "hold": 4}])
S("crowd_cheer", Im, -12, dur=3.4)
M("m_epic", t_arrow - 1.0, 8.0, gain=-10, fi=.3, fo=1.2, trim=8.0)
T = Im + 3.4

# 2012 — "feeling good"
wipe(T, -1)
st = T
slam(2012, st)
L, ph = N("r2012", st + .2)
t_fire = ph[-1][0] - .05
V("n2012", st, t_fire - st, kb={"z0": 1.3, "z1": 1.4}, grade={"bri": .35, "blur": 5})
G("tweet", st + .5, t_fire - st - .5, text="feeling good", clockT=max(.8, t_fire - st - 2.8), clockD=2.0)
S("tweet", st + 1.0, -6); S("clock", t_fire - 2.3, -8, dur=2.3)
en = ph[-1][1] + 1.8
V("n2012", t_fire, en - t_fire, from_=1.0, kb={"z0": 1.2, "z1": 1.0}, grade={"sat": 1.5, "con": 1.2}, shake={"amp": 16, "decay": 2})
BOOM(t_fire, big=1.3); burn(t_fire, en - t_fire, h=700)
G("beast", t_fire, en - t_fire, words=[{"t": .05, "text": "FIRE!!!", "fill": "#ff2a2a", "size": 260, "hold": 9, "rot": -3}])
T = en

st, en, ph = story(2015, "n2015", "r2015", "2015", "CAUGHT", "burned face · smelled of petrol · holding a lighter", fire=False)
G("stamp", ph[-1][0] - .3, en - ph[-1][0] + .3, text="“EXTREMELY\nBAD IDEA”", x=1420, y=300, size=90, rot=-8, color="#ffd400")
S("stamp", ph[-1][0] - .3, -2)

# 2016 — the birthday
st = T
slam(2016, st)
L, ph = N("r2016", st + .2)
t_b = ph[max(0, len(ph) - 4)][0] - .05 if len(ph) >= 4 else st + .2 + L * .55
en = st + .2 + L + .9
V("y2016", st, en - st, kb={"z0": 1.05, "z1": 1.3}, grade={"sat": 1.3})
G("particles", st, t_b - st, kind="confetti", n=120)
G("lower", st + .7, t_b - st - .7, tag="2016", title="50th BIRTHDAY PARTY", sub="party hats: optional")
S("party", st + .8, -5)
for i, p in enumerate(ph[-3:]):
    FX("fx_fireball", p[0] - .05, 1.3, alpha=.8, kb={"z0": 1.3}, fo=.5); S("boom", p[0], -6)
burn(t_b, en - t_b, h=640)
G("beast", t_b, en - t_b, words=[{"t": p[0] - t_b, "text": w, "fill": c, "size": 210, "rot": r}
                                 for p, w, c, r in zip(ph[-3:], ["BURNED.", "SAME.", "NIGHT!"], ["#ff2a2a", "#fff", "#ffd400"], [-4, 3, -2])])
T = en

st, en, ph = story(2023, "birds", "r2023", "2023", "EATEN BY BIRDS", "jackdaws · the straw had extra seeds", fire=False)
S("birds", st, -6, dur=en - st, fo=.5)
st, en, ph = story(2025, "n2025", "r2025", "2025", "FACEPLANT", "Storm Johannes", fire=False)
S("wind", st, -7, dur=en - st); S("thud", st + 2.4, 2); G("zoomblur", st + 2.45, .5, amt=1.2)

# ---- THE TEASE: no unmasking, no run -------------------------------------------------------
wipe(T)
R0 = T
TD = 5.2
V("unmask_pre", R0, TD, speed=3.6 / TD, kb={"z0": 1.0, "z1": 1.25})   # still masked, staring into camera
G("solid", R0, TD, color="#000", alpha=.35, fi=.4)
S("riser", R0, -8, dur=TD); S("snow_amb", R0, -10, dur=TD)
G("caption", R0 + .5, TD - .5, text="Santa & the Gingerbread Man, 2005.", font="700 44px Mono", y=170, fill="#ddd", ls="4px", fi=.4)
G("beast", R0, TD, words=[{"t": 1.6, "text": "WE KNOW WHO", "fill": "#fff", "size": 150, "y": 760, "rot": -2, "hold": 9},
                          {"t": 2.5, "text": "REALLY DID IT...", "fill": "#ff2a2a", "size": 160, "y": 920, "rot": 2, "hold": 9}])
S("boom", R0 + 1.6, -6); S("braam", R0 + 2.5, -3)
T = R0 + TD

# ---- END CARD --------------------------------------------------------------------------------
Z = T
L, ph = N("outro", Z + .4)
ZD = max(5.0, L + 1.4)
V("fire_title", Z, ZD, speed=.8, grade={"con": 1.15, "sat": 1.2}, kb={"z0": .8, "z1": .86, "y0": -.07}, fi=.2)
FX("fx_embers", Z, ZD, alpha=.8)
for dx in (-.34, 0, .34):
    FX("fx_flamewall", Z, ZD, alpha=.55, kb={"z0": 1.1, "x0": dx, "y0": .34}, fo=.8)
G("shock", Z, .8); S("ignite", Z, -4)
M("m_credits", Z, ZD, gain=-12, fi=.3, fo=1.0)
G("caption", Z + 1.0, ZD - 1.0, text="Written & Directed by Claude “The Goatfather”   ·   Produced by @amyleesterling", font="500 30px Inter5", y=960, fill="#e6d2b0", ls="3px", fi=.4, fo=.5)
T += ZD

TOTAL = T

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    for L in LAYERS:
        if "from_" in L:
            L["from"] = L.pop("from_")
    def z(L):  # footage < fire fx < graphics/text < post effects
        if L["type"] in ("video", "still"):
            return 1 if L.get("blend") else 0
        if L["type"] in ("particles", "fire", "shock", "heat"):
            return 1
        if L["type"] in ("zoomblur", "rgbsplit", "flash", "whip", "wipe"):
            return 3
        return 2
    LAYERS.sort(key=z)
    tl = {"fps": FPS, "dur": TOTAL, "clips": clipinfo(), "layers": LAYERS}
    pathlib.Path("render/timeline.json").write_text(json.dumps(tl))
    print(f"timeline: {TOTAL:.1f}s, {len(LAYERS)} layers, {len(AUDIO)} audio cues")
    if "--audio" in sys.argv:
        lev = json.load(open("media/levels.json"))

        def build(stem):
            ins, fl = ["-f", "lavfi", "-t", f"{TOTAL:.3f}", "-i", "anullsrc=r=48000:cl=stereo"], ["[0:a]anull[a0]"]
            for a in AUDIO:
                isvo = "/vo/" in a["src"] or "/vid/" in a["src"]
                if (stem == "vo") != isvo or not pathlib.Path(a["src"]).exists():
                    continue
                norm = max(-12.0, min(12.0, -18.0 - lev.get(a["src"], -18.0)))
                ins += ["-i", a["src"]]
                k = len(fl)
                f = f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=start={a['trim']}"
                if a["dur"]:
                    f += f":duration={a['dur']}"
                f += ",asetpts=PTS-STARTPTS"
                if a["fx"]:
                    f += "," + a["fx"]
                if a["fi"]:
                    f += f",afade=t=in:d={a['fi']}"
                if a["fo"] and a["dur"]:
                    f += f",afade=t=out:st={max(0, a['dur'] - a['fo'])}:d={a['fo']}"
                f += f",volume={a['gain'] + norm:.2f}dB,adelay={int(a['start'] * 1000)}:all=1[a{k}]"
                fl.append(f)
            n = len(fl)
            fl.append("".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0:dropout_transition=0,atrim=duration={TOTAL}[out]")
            pathlib.Path(f"media/mix_{stem}.txt").write_text(";\n".join(fl))
            subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex_script", f"media/mix_{stem}.txt",
                            "-map", "[out]", "-ar", "48000", f"media/mix_{stem}.wav"], check=True)

        build("vo"); build("bed")
        # duck the bed under dialogue, then glue and limit
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "media/mix_bed.wav", "-i", "media/mix_vo.wav", "-filter_complex",
                        "[1:a]asplit=2[sc][vo];[0:a][sc]sidechaincompress=threshold=0.02:ratio=6:attack=8:release=350:knee=4[bd];"
                        "[bd][vo]amix=inputs=2:normalize=0,alimiter=limit=0.89:level=false[out]",
                        "-map", "[out]", "-ar", "48000", "media/mix.wav"], check=True)
        print("mix written")


