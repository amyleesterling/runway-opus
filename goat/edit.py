"""THE G.O.A.T. — v3 edit (90-second re-cut: every clip used once, motion-graphics explainer). Builds render/timeline.json (picture) and media/mix.wav (sound).

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

T = 0.0
TIGHT = .35   # max pause inside a VO line: keeps the jokes moving


def wipe(t, dir=1):
    G("wipe", t - .3, .6, dir=dir)
    S("whoosh2", t - .3, -6)


# ---- A. EXPLAINER: why is there a goat? (no VO, polka) ------------------
M("m_credits", 0, 12.1, gain=-9, fi=.2, fo=.05)
V("ink", 0, 5.0, speed=.6, kb={"z0": 1.0, "z1": 1.12}, fi=.4)
G("beast", 0, 5.0, words=[{"t": .25, "text": "IN SWEDEN,", "fill": "#fff", "size": 120, "y": 250, "x": 1350, "hold": 9, "rot": -3},
                          {"t": 1.1, "text": "CHRISTMAS HAS A GOAT.", "fill": "#ffd400", "size": 110, "y": 400, "x": 1250, "hold": 9, "rot": 2}])
S("whoosh", .2, -8); S("whoosh", 1.05, -8)
G("lower", 2.3, 2.7, tag="TRADITION", title="THE YULE GOAT", sub="Straw. Centuries old. (Thor's chariot was pulled by goats.)")
wipe(5.0)
V("open", 5.0, 8.1, kb={"z0": 1.0, "z1": 1.08})
G("caption", 5.2, 3.0, text="1966: THE TOWN OF GÄVLE BUILDS A BIG ONE.", font="800 54px Inter", x=80, y=110, align="left", fi=.2)
G("ruler", 5.6, 4.0, x=1420, y0=930, y1=140, metres=13, items=[
    {"kind": "giraffe", "m": 5.5, "x": 1620, "label": "GIRAFFE", "t": 1.2},
    {"kind": "human", "m": 1.8, "x": 1800, "label": "YOU", "t": 1.6}])
S("riser", 5.6, -12)
G("stamp", 8.2, 1.4, text="3 TONNES\nOF STRAW", x=420, y=520, size=90, rot=-8, color="#ffd400")
S("stamp", 8.2, -3)
G("solid", 9.6, 3.5, color="#000", alpha=.55, fi=.2)
G("caption", 9.7, 3.4, text="DESIGNED BY:", font="700 60px Mono", y=300, fi=.1)
G("stamp", 10.4, 2.7, text="THE FIRE CHIEF'S\nBROTHER", y=560, size=120, rot=-6, color="#ff2a2a")
S("stamp", 10.4, 0)
G("beast", 11.4, 1.7, words=[{"t": 0, "text": "?!", "fill": "#ffd400", "size": 200, "x": 1600, "y": 380, "rot": 10, "hold": 9}])
S("ding", 11.4, -8)
# music stops dead. beat.
G("caption", 12.3, 1.2, text="what could possibly go wrong", font="700 36px Mono", y=900, fill="#ddd", ls="4px")
S("snow_amb", 12.1, -10, dur=1.5)
S("match", 13.05, 0)
T = 13.6
# SMASH: it burned.
V("y1966", T, 4.0, kb={"z0": 1.15, "z1": 1.3}, grade=grade_vintage(), shake={"amp": 10, "decay": 1.5})
FX("fx_fireball", T, 2.4, kb={"z0": 1.3, "z1": 1.6}, fo=.8)
G("shock", T, .9); G("flash", T, .25, color="#fff")
S("ignite", T, 0); S("boom", T, -2); S("crowd_gasp", T + .5, -6); S("fire", T, -10, dur=4.0, fo=.6)
G("yearSlam", T + .1, 1.4, year="31 DEC 1966", size=150, y=220)
G("stamp", T + 1.4, 2.6, text="BURNED.\nYEAR ONE.", x=1450, y=640, size=120, rot=-10)
S("stamp", T + 1.4, -2)
T += 4.0

# ---- B. 60 GOATS, 43 IGNITE ---------------------------------------------
B = T
wipe(B, -1)
G("solid", B, 8.6, color="#0b1024")
G("particles", B, 8.6, kind="embers", n=120, alpha=.6)
Lc, sc = VO("hype_count", B + .3, maxgap=TIGHT)
import random
rng = random.Random(1966)
order = rng.sample(range(60), 43)
G("goatgrid", B, 8.6, order=order, t0=.35, t1=sc[-1][0] - B + .4)
g_end = sc[-1][0] + .4
S("counter", B + .4, -10, dur=g_end - B - .4)
S("register", g_end, -2); G("shock", g_end, .9, y=140)
for dx in (-.34, .34):
    FX("fx_flamewall", g_end, B + 8.6 - g_end, kb={"z0": 1.2, "x0": dx, "y0": .2}, fi=.1, fo=.3)
G("stamp", g_end + .9, B + 8.6 - g_end - .9, text="(ALL TRUE)", x=1600, y=950, size=64, rot=8, color="#ffd400")
S("stamp", g_end + .9, -4)
M("m_hype", B, 8.6, gain=-12, fi=.05, fo=.3)
T = B + 8.6

# ---- C. RAP SHEET (each clip once) -------------------------------------
E = T
M("m_montage", E, 30.0, gain=-15, fi=.1, fo=.8)


def slam(year, st, sub=None):
    G("yearSlam", st, .8, year=year)
    G("flash", st, .15, color="#fff", alpha=.6); G("shock", st, .6)
    S("boom", st, -7); S("whoosh", st - .08, -8)


# 1973
wipe(T)
st = T; slam(1973, st)
L, sv = VO("log_1973", st + .15, maxgap=TIGHT)
en = st + .15 + L + .5
V("y1973", st, en - st, kb={"z0": 1.05, "z1": 1.2}, grade=grade_vintage())
G("lower", st + .8, en - st - .8, tag="1973", title="STOLEN", sub="found in a man's back garden")
S("gulp", sv[-1][1] + .1, -6)
T = en
# 1976
st = T; slam(1976, st)
L, sv = VO("log_1976", st + .15, maxgap=TIGHT)
en = st + .15 + L + .6
V("y1976", st, en - st, speed=.7, kb={"z0": 1.05, "z1": 1.2}, grade=grade_vintage(), shake={"amp": 12, "decay": 1.2})
S("crash", st + .35, -3); G("zoomblur", st + .4, .4)
G("lower", st + .8, en - st - .8, tag="1976", title="HIT BY A VOLVO", sub="Volvo Amazon · hind legs")
T = en
# 2001 — the tourist and the lighter
st = T; slam(2001, st)
L1, s1 = VO("log_2001", st + .15, maxgap=TIGHT)
L2, s2 = VO("log_2001b", st + .15 + L1 + .3, maxgap=TIGHT)
en = st + .15 + L1 + .3 + L2 + .9
V("burning", st, en - st, speed=.6, kb={"z0": 1.2, "z1": 1.3, "x0": -.2}, grade={"bri": .5, "blur": 4, "sat": 1.3})
G("caption", st + .9, en - st - .9, text="2001", font="140px Anton", x=330, y=300, fill="#ffe600", fi=.2)
G("caption", st + .9, en - st - .9, text="THE TOURIST", font="800 64px Inter", x=330, y=410, fi=.2)
G("verdict", st + .5, en - st - .5, rows=[["DEFENDANT", "American tourist, 51\nCleveland, Ohio"],
                                          ["DEFENCE", "“I thought it was a legal\ntradition.”"],
                                          ["SENTENCE", "Jail + SEK 100,000 damages\n(went home without paying)"],
                                          ["ALSO", "Lighter CONFISCATED."]])
G("stamp", s2[-1][0] + .5, en - s2[-1][0] - .5, text="NOT ABLE TO\nHANDLE IT", x=1250, y=640, size=100, rot=-14)
S("stamp", s2[-1][0] + .5, -1)
T = en
# 2016 — birthday party catches fire
st = T; slam(2016, st)
L, sv = VO("log_2016", st + .15, maxgap=TIGHT)
t_b = sv[2][0] - .05
en = sv[-1][1] + .9
V("y2016", st, en - st, kb={"z0": 1.05, "z1": 1.3}, grade={"sat": 1.3}, punch=[t_b - st, sv[3][0] - st, sv[4][0] - st])
G("particles", st, t_b - st, kind="confetti", n=120)
G("lower", st + .8, t_b - st - .9, tag="27 NOV 2016", title="50th BIRTHDAY PARTY", sub="Party hats: optional")
S("party", st + .9, -5); S("crowd_cheer", st + .5, -14, dur=t_b - st)
G("fire", t_b, en - t_b, h=620, size=95, fi=.05); G("heat", t_b, en - t_b, amt=.7)
G("beast", t_b, en - t_b, words=[{"t": sv[2][0] - t_b, "text": "BURNED.", "fill": "#ff2a2a", "rot": -4, "size": 200},
                                  {"t": sv[3][0] - t_b, "text": "SAME.", "fill": "#fff", "rot": 3, "size": 200},
                                  {"t": sv[4][0] - t_b, "text": "NIGHT.", "fill": "#ffe600", "rot": -2, "size": 220}])
for s_ in sv[2:]:
    S("boom", s_[0], -8)
S("ignite", t_b, -2); S("fire", t_b, -12, dur=en - t_b)
T = en

# ---- D. THE GUARD (Veo dialogue) ---------------------------------------
wipe(T)
Gs = T
V("guard", Gs, 8.4, kb={"z0": 1.0, "z1": 1.08})
A("media/vid/guard.mp4", Gs, 0, dur=7.6, fo=.1)
G("lower", Gs + .5, 3.2, tag="DRAMATISATION", tagColor="#555", title="NIGHT GUARD", sub="2003: guards really did go to a restaurant")
G("beast", Gs + 7.6, .8, words=[{"t": 0, "text": "...", "fill": "#fff", "size": 160, "x": 1500, "y": 300, "hold": 9}])
T = Gs + 8.4

# ---- E. SANTA & THE GINGERBREAD MAN ------------------------------------
H0 = T
wipe(H0, -1)
Ls, ss = VO("santa_setup", H0 + .4, maxgap=TIGHT)
sh_end = ss[-1][1] + .3
G("solid", H0, sh_end - H0, color="#14080a")
G("particles", H0, sh_end - H0, kind="snow", n=150, alpha=.6)
G("news", H0, sh_end - H0, tag="BREAKING", headline="3 DEC 2005: GOAT SHOT WITH FLAMING ARROW",
  ticker="SUSPECTS: ONE SANTA, ONE GINGERBREAD MAN  •  POLICE BAFFLED  •  GOAT UNAVAILABLE FOR COMMENT  •  NORTH POLE DENIES INVOLVEMENT")
G("wanted", H0, sh_end - H0, posters=[
    {"t": ss[1][0] - H0 + .2, "src": "../media/img/santa.png", "crop": [540, 290, 600, 500], "x": 620, "y": 420, "rot": -6, "name": "SANTA CLAUS", "crime": "Arson (flaming arrow)", "crime2": "Last seen: North Pole?"},
    {"t": ss[2][0] - H0 + .2, "src": "../media/img/santa.png", "crop": [150, 470, 540, 450], "x": 1300, "y": 440, "rot": 5, "name": "THE GINGERBREAD MAN", "crime": "Accessory. Binoculars.", "crime2": "Run, run, as fast as you can"}])
G("beast", H0, ss[1][0] - H0 + .1, words=[{"t": .15, "text": "THE WORST ONE.", "fill": "#ff2a2a", "size": 170, "y": 430, "rot": -3, "hold": 9}])
S("boom", H0 + .15, -6)
S("whoosh2", ss[1][0], -6); S("whoosh2", ss[2][0], -6); S("riser", H0 + .5, -14)
M("m_epic", H0, sh_end - H0 + .2, gain=-18, fi=.5, fo=.2)
T = sh_end
SC = 6.1
V("santa", T, SC, kb={"z0": 1.0, "z1": 1.12}, grade={"sat": 1.2})
A("media/vid/santa.mp4", T, 1, dur=SC, fo=.1)
G("letterbox", T, SC + 3.4, h=120)
G("subs", T, SC, font="italic 600 58px Cormorant", lines=[{"t0": 1.6, "t1": 4.6, "text": "[whispering]  Ho.  Ho.  Go."}])
S("bow", T + 4.3, 0)
T += SC
Ar = T
V("arrow", Ar, 3.4, speed=.8, kb={"z0": 1.0, "z1": 1.25}, grade={"sat": 1.35, "con": 1.1})
FX("fx_embers", Ar, 3.4, alpha=.7, speed=.8)
S("arrow", Ar, -2); S("riser", Ar + .4, -8)
M("m_epic", Ar, 12.0, gain=-10, fi=.2, fo=1.5, trim=8.0)
T = Ar + 3.4
Im = T
Lp, sp = VO("santa_pay", Im + .1, gain=2)
V("impact", Im, 6.0, kb={"z0": 1.2, "z1": 1.0}, grade={"sat": 1.45, "con": 1.15}, shake={"amp": 26, "decay": 1.2})
G("flash", Im, .3, color="#fff", alpha=.5)
FX("fx_fireball", Im, 2.4, kb={"z0": 1.4, "z1": 1.7}, fo=.8)
FX("fx_shockwave", Im + .1, 2.0, alpha=.9, fo=.5)
G("shock", Im, .9)
G("zoomblur", Im, .8, amt=2); G("rgbsplit", Im, .9, amt=24)
G("particles", Im, 1.6, kind="sparks", n=220, fi=0)
G("fire", Im, 6.0, h=640, size=100, fi=.05); G("heat", Im + .3, 3.2, amt=.8)
G("beast", Im, 3.0, words=[{"t": .1, "text": "FLAMING", "fill": "#ffb300", "rot": -4, "size": 230, "y": 430, "hold": 3},
                           {"t": .7, "text": "ARROW!!!", "fill": "#ff2a2a", "rot": 3, "size": 260, "y": 660, "hold": 3}])
S("ignite", Im, 2); S("boom", Im, 0); S("braam", Im + .1, -3); S("fire", Im + .5, -10, dur=5, fo=1)
G("solid", Im + 3.3, 2.7, color="#000", alpha=.35, fi=.3)
G("stamp", Im + 3.4, 2.6, text="CASE STATUS:\nUNSOLVED", x=1420, y=230, size=90, rot=-8, color="#ffd400")
S("stamp", Im + 3.4, -4)
T = Im + 6.0

# ---- F. UNDEFEATED... UNTIL BIRDS ----------------------------------------
I0 = T
wipe(I0)
Lc, sc = VO("twist_count", I0 + .3, maxgap=TIGHT)
en = sc[-1][1] + .6
V("triumph", I0, en - I0, speed=.55, kb={"z0": 1.0, "z1": 1.2}, grade={"sat": 1.35})
G("particles", I0, en - I0, kind="confetti", n=150)
G("checks", I0, en - I0, x0=390, dx=380, y=330, items=[{"year": y, "t": sc[i][0] - I0 + .1} for y, i in
                                                       (("2017", 1), ("2018", 2), ("2019", 4), ("2020", 5))])
for i in (1, 2, 4, 5):
    S("ding", sc[i][0] + .1, -8)
G("beast", I0, en - I0, words=[{"t": sc[-1][0] - I0, "text": "4 YEARS UNDEFEATED", "fill": "#ffd400", "size": 150, "y": 800, "hold": 9}])
FX("fx_burst", sc[-1][0] - .1, en - sc[-1][0] + .1, fo=.3)
S("crowd_cheer", sc[-1][0], -6); S("ignite", sc[-1][0], -4)
M("m_triumph", I0, en - I0 + .1, gain=-9, fi=.2, fo=.1)
T = en
# record scratch. freeze. 2023.
S("scratch", T, -2)
G("solid", T, 1.2, color="#000")
G("yearSlam", T + .15, 1.05, year=2023, fill="#fff", rot=0)
Lb, sb = VO("birds_2023", T + .25, maxgap=.6)
tb = T + 1.2
en = sb[-1][1] + 1.6
V("birds", tb, en - tb, kb={"z0": 1.0, "z1": 1.2}, grade={"sat": .8, "con": 1.2}, shake={"amp": 3})
S("birds", tb, -6, dur=en - tb, fo=.8)
G("lower", tb + .3, en - tb - .3, tag="CAUSE OF DEATH", title="JACKDAWS", sub="The straw had unusually many seeds")
T = en

# ---- G. THE FACEPLANT --------------------------------------------------
wipe(T, -1)
P = T
Lq, sq = VO("post_2025", P + .2, maxgap=.8)
V("storm", P, 6.0, grade={"sat": 1.2, "con": 1.1}, kb={"z0": 1.0, "z1": 1.1})
S("wind", P, -6, dur=6.0, fo=.3)
S("thud", P + 3.25, 2); S("boom", P + 3.25, -10); G("zoomblur", P + 3.3, .5, amt=1.2)
G("lower", P + .3, 3.0, tag="27 DEC 2025", title="STORM JOHANNES", sub="It did not burn. It fell over.")
T = max(P + 6.0, sq[-1][1] + .2)
Lf, sf = VO("goat_fine", T + .1, gain=-2, fx="lowpass=f=900,volume=1.6")
G("subs", T - .1, 2.0, font="italic 600 60px Cormorant", lines=[{"t0": .1, "t1": 1.9, "text": "[muffled, face-down]   ...I'm fine."}])
V("storm", P + 6.0, T + 1.9 - (P + 6.0), from_=5.95)  # hold on the faceplant (same shot, not a reuse)
T += 1.9

# ---- H. END CARD ---------------------------------------------------------
Z = T
Lo, so = VO("hype_outro", Z + .5)
V("fire_title", Z, 5.0, speed=.8, grade={"con": 1.15, "sat": 1.2}, kb={"z0": .8, "z1": .86, "y0": -.07}, fi=.2)
FX("fx_embers", Z, 5.0, alpha=.8)
G("fire", Z, 5.0, h=320, size=60, fi=.3, intensity=.8)
G("shock", Z, .8); S("ignite", Z, -4); S("braam", so[-1][0], -6)
G("caption", Z + .6, 4.4, text="It will be rebuilt.  It always is.", font="italic 600 64px Cormorant", y=870, fill="#ffe9c4", fi=.4, fo=.5)
G("caption", Z + 1.2, 3.8, text="Written & Directed by Claude “The Goatfather”   ·   Produced by @amyleesterling", font="500 30px Inter5", y=960, fill="#e6d2b0", ls="3px", fi=.4, fo=.5)
T += 5.0

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

