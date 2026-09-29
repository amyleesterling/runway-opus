"""THE G.O.A.T. — the edit. Builds render/timeline.json (picture) and media/mix.wav (sound).

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

# ---- A. COLD OPEN ----------------------------------------------------
V("open", 0, 8.0, kb={"z0": 1.0, "z1": 1.07}, fi=1.0)
G("particles", 0, 8.0, kind="snow", n=120, alpha=.5)
G("vignette", 0, 8.0, amt=.6)
G("grad", 0.6, 7.2, fi=.8, fo=.6)
G("caption", .4, 3.4, text="@amyleesterling  presents", font="500 34px Inter5", x=960, y=120, fill="#f3e3c0", ls="8px", fi=.8, fo=.8)
G("quote", 1.0, 6.6, y=800, fo=.6, lines=[
    {"text": "“The goat that is built will be burned.", "t": 0},
    {"text": "The goat that is burned will be built.”", "t": 1.4},
    {"text": "— Lao Tzu  (citation needed)", "t": 3.2, "dy": 170, "font": "500 32px Inter5", "fill": "#d9d9d9"}])
S("snow_amb", 0, -10, fo=1.0, dur=8.2)
M("m_serene", 0, 8.2, gain=-14, fi=1.5, fo=.4)
S("match", 7.55, -2)
G("solid", 7.55, 1.05, color="#000", fi=.12)
G("match", 7.6, 1.0)
T = 8.6

# ---- B. MR BEAST ----------------------------------------------------
B = T
S("boom", B, -1)
G("flash", B, .25, color="#fff")
L1, s1 = VO("hype_intro", B + .25)
cuts = [("open", 3.0, {"z0": 1.5, "z1": 1.7, "y0": .12}), ("soliloquy", 1.0, {"z0": 1.2, "z1": 1.35}),
        ("y2016", 0.5, {"z0": 1.1, "z1": 1.25}), ("santa", 0.0, {"z0": 1.15, "z1": 1.3}), ("burning", 0.0, {"z0": 1.1, "z1": 1.3})]
bounds = [B] + [s[0] - .08 for s in s1[1:]] + [s1[-1][1] + .35]
for i, (c, fr, kb) in enumerate(cuts):
    st, en = bounds[i], bounds[i + 1]
    V(c, st, en - st, from_=fr, kb=kb, grade={"sat": 1.45, "con": 1.12}, punch=[0.0, .6],
      shake={"amp": 10 if c == "burning" else 3})
    if i:
        S("whoosh", st - .1, -9)
words = [
    (s1[0][0] + .15, "13 METRES", "#ffe600", -4), (s1[0][0] + .85, "OF GOAT", "#fff", 3),
    (s1[1][0] + .05, "MADE OF STRAW", "#ffe600", -3),
    (s1[2][0] + .1, "EVERY.", "#fff", -4), (s1[2][0] + .75, "SINGLE.", "#fff", 3), (s1[2][0] + 1.35, "YEAR.", "#ffe600", -2),
    (s1[3][0] + .05, "AND EVERY YEAR...", "#fff", 2),
    (s1[4][0] + .05, "SWEDEN TRIES TO", "#fff", -3), (s1[4][0] + .8, "DESTROY IT!", "#ff2a2a", 4)]
G("beast", B, bounds[-1] - B, words=[{"t": t - B, "text": w, "fill": f, "rot": r, "size": 170} for t, w, f, r in words])
BOOM(s1[4][0] + .8)
G("fire", s1[4][0] + .8, bounds[-1] - s1[4][0] - .8, h=520, fi=.2)
G("rgbsplit", s1[4][0] + .8, .5, amt=18)
T = bounds[-1]

L2, s2 = VO("hype_count", T)
seq = [("burning", "BURNED!", "#ff2a2a"), ("y1973", "STOLEN!", "#ffe600"), ("y1976", "HIT BY A CAR!", "#fff"),
       ("arrow", "SHOT WITH A", "#fff"), ("impact", "FLAMING ARROW!", "#ff8a00")]
for i, (c, w, f) in enumerate(seq):
    st = T if i == 0 else s2[i][0] - .05
    en = s2[i + 1][0] - .05
    V(c, st, en - st, from_=1.0, kb={"z0": 1.15, "z1": 1.35}, grade={"sat": 1.5, "con": 1.15}, punch=[0.05], shake={"amp": 8})
    G("beast", st, en - st, words=[{"t": .05, "text": w, "fill": f, "rot": [-5, 4, -3, 3, -4][i], "size": 190}])
    S("whoosh2" if i % 2 else "whoosh", st - .05, -7)
    G("flash", st, .12, color="#fff", alpha=.5)
cst = s2[5][0] - .05
V("burning", cst, 3.2, from_=2.0, kb={"z0": 1.3, "z1": 1.5}, grade={"sat": 1.2, "bri": .45, "blur": 3}, shake={"amp": 6})
for dx in (-.34, 0, .34):
    FX("fx_flamewall", cst + .9, 2.3, kb={"z0": 1.15, "x0": dx, "y0": .12}, fi=.15, fo=.4)
G("fire", cst + .9, 2.3, h=600, size=90, fi=.1)
G("shock", cst + 1.0, 1.0, y=470)
G("counter", cst, 3.2, **{"from": 0, "to": 43, "t0": 0, "t1": 1.0, "label": "TIMES DESTROYED", "y": 470})
S("counter", cst, -8)
S("register", cst + 1.0, -4)
S("boom", cst + 1.0, -4)
G("particles", cst, 3.2, kind="embers", n=180)
G("stamp", cst + 1.9, 1.3, text="(TRUE STORY)", x=1560, y=160, size=70, rot=8, color="#ffe600")
S("stamp", cst + 1.9, -3)
M("m_hype", B, cst + 3.2 - B, gain=-11, fi=.05, fo=.25)
T = cst + 3.2

# ---- C. TITLE --------------------------------------------------------
C = T
G("particles", C, 4.0, kind="embers", n=260, fi=.05)
V("fire_title", C, 4.0, speed=.85, grade={"con": 1.15, "sat": 1.2}, kb={"z0": .8, "z1": .86, "y0": -.07})
FX("fx_embers", C, 4.0, alpha=.8)
G("fire", C, 4.0, h=300, size=60, fi=.3, intensity=.8)
G("caption", C + .8, 3.0, text="Greatest Of All Tinder", font="italic 600 70px Cormorant", y=880, fill="#ffe9c4", fi=.5, fo=.4)
G("caption", C + 1.3, 2.5, text="A TRUE STORY  ·  GÄVLE, SWEDEN  ·  1966 – 2025", font="500 28px Inter5", y=960, fill="#e6d2b0", ls="10px", fi=.5, fo=.4)
G("shock", C, .8)
G("zoomblur", C, .5, amt=1.4)
S("braam", C, -2)
S("ignite", C, -6)
T = C + 4.0

# ---- D. SOLILOQUY ----------------------------------------------------
D = T
Ld, sd = VO("goat_solo", D + 1.0, gain=1, maxgap=.85)
end = sd[-1][1] + 1.2
V("soliloquy", D, sd[8][0] - D, speed=.52, fi=.8, grade={"con": 1.08})
V("open", sd[8][0], sd[9][0] - sd[8][0], from_=2.0, speed=.5, kb={"z0": 1.1, "z1": 1.0}, grade={"bri": .8})
V("soliloquy", sd[9][0], end - sd[9][0], from_=9.9, kb={"z0": 1.0, "z1": 1.12}, fo=.6)
G("particles", D, end - D, kind="snow", n=90, alpha=.6)
G("letterbox", D, end - D, h=135)
G("vignette", D, end - D, amt=.7)
G("caption", D + .6, 4.0, text="ACT I, SCENE I.   A Goat, alone.", font="italic 600 40px Cormorant", x=140, y=190,
  align="left", fill="#f3dfb3", fi=.8, fo=.8)
phr = ["To burn...", "...or not to burn?", "That is never the question.", "Each December they raise me up.",
       "Three tonnes of straw...", "...and hope.", "And each December,",
       "some reveller with a lighter\ncomposes my eulogy.", "Out, out, brief candle!", "...I am the candle."]
G("subs", D, end - D, y=880, font="64px Fell", lines=[
    {"t0": s[0] - D - .05, "t1": (sd[i + 1][0] - D - .1) if i + 1 < len(sd) else s[1] - D + 1.0, "text": phr[i]} for i, s in enumerate(sd)])
M("m_shakes", D, end - D, gain=-15, fi=1.0, fo=1.0)
S("snow_amb", D, -16, dur=end - D)
T = end

# ---- E. ATTACK LOG ---------------------------------------------------
E = T
S("scratch", E - .1, -6)


def entry(year, clip, vo, lower, grade=None, kb=None, speed=1.0, from_=0.0, extra=None, tail=.45):
    st = T
    V(clip, st, 99, from_=from_, speed=speed, kb=kb or {"z0": 1.05, "z1": 1.18}, grade=grade or {"sat": 1.2})
    LAYERS[-1]["_open"] = True
    S("boom", st, -9)
    S("whoosh", st - .08, -8)
    G("flash", st, .15, color="#fff", alpha=.6)
    FX("fx_fireball", st - .05, 1.1, alpha=.45 if year == 1973 else .7, kb={"z0": 1.6}, fo=.4)
    G("yearSlam", st, .75, year=year)
    Lv, sv = VO(vo, st + .1)
    ln = Lv + .1 + tail
    if lower:
        G("lower", st + .8, ln - .8, **lower)
    return st, ln, sv


def close_open(at):
    for L in LAYERS:
        if L.get("_open"):
            L["dur"] = at - L["start"]
            del L["_open"]


# 1966
st, ln, sv = entry(1966, "y1966", "log_1966", {"tag": "ATTACK #1", "title": "BURNED AT MIDNIGHT", "sub": "New Year's Eve · its very first year"},
                   grade=grade_vintage())
S("crowd_gasp", st + 1.2, -8); S("fire", st + .5, -14, dur=ln - .5, fo=.4)
T = st + ln; close_open(T)
# 1973
st, ln, sv = entry(1973, "y1973", "log_1973", {"tag": "1973", "title": "STOLEN", "sub": "found in a man's back garden"}, grade=grade_vintage())
S("gulp", sv[-1][1] + .1, -6)
T = st + ln + .3; close_open(T)
# 1976
st, ln, sv = entry(1976, "y1976", "log_1976", {"tag": "1976", "title": "HIT BY A VOLVO", "sub": "Volvo Amazon · hind legs"},
                   grade=grade_vintage(), speed=.7)
S("crash", st + .35, -3); G("zoomblur", st + .4, .4)
T = st + ln + .2; close_open(T)
# 2001 — court
st = T
FX("fx_fireball", st - .05, 1.1, alpha=.7, kb={"z0": 1.6}, fo=.4); G("yearSlam", st, .75, year=2001); S("boom", st, -9); S("whoosh", st - .08, -8)
L01, s01 = VO("log_2001", st + .1)
L01b, s01b = VO("log_2001b", st + .1 + L01 + .35)
en = st + .1 + L01 + .35 + L01b + .6
V("burning", st, en - st, from_=0, speed=.6, kb={"z0": 1.2, "z1": 1.3, "x0": -.2}, grade={"bri": .5, "blur": 4, "sat": 1.3})
G("verdict", st + .6, en - st - .6, rows=[["DEFENDANT", "American tourist, 51\nCleveland, Ohio"],
                                          ["DEFENCE", "“I thought it was a legal\ntradition.”"],
                                          ["SENTENCE", "Jail + SEK 100,000 damages\n(went home without paying)"],
                                          ["ALSO", "Lighter CONFISCATED."]])
G("stamp", s01b[-1][0] + .6, en - s01b[-1][0] - .6, text="NOT ABLE TO\nHANDLE IT", x=1250, y=640, size=100, rot=-14)
S("stamp", s01b[-1][0] + .6, -1)
G("caption", st + .9, en - st - .9, text="2001", font="140px Anton", x=330, y=300, fill="#ffe600", fi=.2)
G("caption", st + .9, en - st - .9, text="THE TOURIST", font="800 64px Inter", x=330, y=410, fi=.2)
T = en
# 2010 — heist
st = T
FX("fx_fireball", st - .05, 1.1, alpha=.7, kb={"z0": 1.6}, fo=.4); G("yearSlam", st, .75, year=2010); S("boom", st, -9); S("whoosh", st - .08, -8)
L10, s10 = VO("log_2010", st + .1)
t_fail = st + .1 + L10 + .3
L10b, s10b = VO("log_2010b", t_fail + .1)
en = t_fail + L10b + 1.4
V("y2010", st, en - st, speed=.9, kb={"z0": 1.0, "z1": 1.15}, grade={"sat": 1.1, "con": 1.1})
G("blueprint", st + .5, t_fail - st - .5, items=[
    {"t": .6, "text": "> BRIBE OFFERED ....... SEK 50,000"},
    {"t": 1.8, "text": "> GUARD INSTRUCTIONS . 'LOOK AWAY BRIEFLY'"},
    {"t": 3.6, "text": "> EXTRACTION ......... HELICOPTER"},
    {"t": 5.2, "text": "> DESTINATION ........ STOCKHOLM"}], cx=1130, cy=560, cx1=1180, cy1=230)
S("heli", st + .2, -9, dur=t_fail - st, fo=.3)
S("riser", t_fail - 3.8, -12)
G("solid", t_fail, en - t_fail, color="#000", alpha=.35)
G("stamp", t_fail + .15, en - t_fail - .15, text="STATUS: FAILED\nGOAT: FINE", size=120, rot=-9, color="#27e35a")
S("buzzer", t_fail + .1, -6); S("stamp", t_fail + .15, -2)
T = en
# 2012 — tweet
st = T
FX("fx_fireball", st - .05, 1.1, alpha=.7, kb={"z0": 1.6}, fo=.4); G("yearSlam", st, .75, year=2012); S("boom", st, -9); S("whoosh", st - .08, -8)
L12, s12 = VO("log_2012", st + .1)
t_fire = st + .1 + L12 + .15
V("open", st, t_fire - st, from_=4, speed=.5, kb={"z0": 1.3, "z1": 1.4}, grade={"bri": .35, "blur": 5})
G("tweet", st + .8, t_fire - st - .8, text="feeling good", clockT=s12[2][0] - st - .8, clockD=2.2)
S("tweet", s12[1][0] + .8, -6)
S("clock", s12[2][0] - .2, -8, dur=2.6, fo=.2)
V("burning", t_fire, 2.6, from_=2.5, kb={"z0": 1.25, "z1": 1.1}, grade={"sat": 1.5, "con": 1.2}, shake={"amp": 14, "decay": 2})
G("flash", t_fire, .3, color="#fff")
BOOM(t_fire, big=1.2)
G("caption", t_fire + .1, 2.5, text="23:56", font="170px Anton", x=1500, y=220, fill="#ff2a2a", pop=True)
G("particles", t_fire, 2.6, kind="embers", n=200)
S("ignite", t_fire, 0); S("fire", t_fire, -8, dur=2.6, fo=.5)
T = t_fire + 2.6
# 2016 — birthday
st = T
FX("fx_fireball", st - .05, 1.1, alpha=.4, kb={"z0": 1.6}, fo=.4); G("yearSlam", st, .75, year=2016); S("boom", st, -9); S("whoosh", st - .08, -8)
L16, s16 = VO("log_2016", st + .1)
t_b = s16[2][0] - .05
V("y2016", st, t_b - st, kb={"z0": 1.05, "z1": 1.15}, grade={"sat": 1.3})
G("particles", st, t_b - st, kind="confetti", n=120)
G("lower", st + .8, t_b - st - .8, tag="27 NOV 2016", title="50th BIRTHDAY PARTY", sub="Party hats: optional")
S("party", st + .9, -5); S("crowd_cheer", st + .5, -14, dur=t_b - st)
en = s16[-1][1] + 1.0
V("burning", t_b, en - t_b, from_=1, kb={"z0": 1.1, "z1": 1.35}, grade={"sat": 1.4, "con": 1.2}, shake={"amp": 10}, punch=[0, s16[3][0] - t_b, s16[4][0] - t_b])
for w_ in s16[2:]:
    FX("fx_fireball", w_[0] - .05, 1.4, alpha=.9, kb={"z0": 1.3}, fo=.5)
G("fire", t_b, en - t_b, h=560, size=85, fi=.1)
G("beast", t_b, en - t_b, words=[{"t": s16[2][0] - t_b, "text": "BURNED.", "fill": "#ff2a2a", "rot": -4, "size": 200},
                                  {"t": s16[3][0] - t_b, "text": "SAME.", "fill": "#fff", "rot": 3, "size": 200},
                                  {"t": s16[4][0] - t_b, "text": "NIGHT.", "fill": "#ffe600", "rot": -2, "size": 220}])
for s in s16[2:]:
    S("boom", s[0], -8)
S("ignite", t_b, -2); S("fire", t_b, -12, dur=en - t_b)
G("particles", t_b, en - t_b, kind="embers", n=160)
T = en
M("m_montage", E, 30.0, gain=-15, fi=.1, fo=.8)
M("m_montage", E + 29.2, T - E - 29.2, gain=-15, fi=.8, fo=.8)

# ---- F. XKCD ---------------------------------------------------------
F = T
Lx, sx = VO("xkcd", F + .6, gain=1, maxgap=1.1)
end = sx[-1][1] + 1.2
rel = lambda i: sx[i][0] - F
G("xkcd", F, end - F, tt={"list": [rel(2), rel(3), rel(4), rel(5)], "p1End": rel(6) - .1, "arrow": rel(6) + .3,
                           "terrier": rel(9) - .2, "ice": rel(10) - .1, "melt": rel(11) - .1, "p2End": rel(12) - .1,
                           "dots": rel(13) + 1.0, "fire": sx[14][1] - F - .2},
  list=["A FENCE", "CHICKEN WIRE", "SOLDIERS", "TAXI DRIVERS"])
G("flash", F, .2, color="#fff")
S("pencil", F + .1, -8)
for i in (2, 3, 4, 5):
    S("pencil", sx[i][0] + .3, -12)
S("pencil", sx[6][0], -10); S("pencil", sx[12][0], -10)
S("ding", sx[9][0] + .5, -10)
M("m_xkcd", F, end - F, gain=-16, fi=.3, fo=.6)
T = end

# ---- G. GUARD (Veo dialogue) -----------------------------------------
Gs = T
V("guard", Gs, 9.6, kb={"z0": 1.0, "z1": 1.06})
A("media/vid/guard.mp4", Gs, 0, dur=8.0, fo=.1)
G("lower", Gs + .6, 4.5, tag="DRAMATISATION", tagColor="#555", title="NIGHT GUARD", sub="Guards really did go to a restaurant in 2003")
S("snow_amb", Gs + 7.9, -12, dur=1.7)
T = Gs + 9.6

# ---- H. SANTA ---------------------------------------------------------
H0 = T
Ls, ss = VO("santa_setup", H0 + .5)
sh_end = ss[-1][1] + .4
LAYERS.append({"type": "still", "src": "../media/img/santa.png", "start": H0, "dur": sh_end - H0,
               "kb": {"z0": 1.35, "z1": 1.05, "x0": .08, "y0": .05}, "fi": .4})
G("solid", H0, sh_end - H0, color="#001", alpha=.35)
G("particles", H0, sh_end - H0, kind="snow", n=150, alpha=.7)
G("caption", ss[0][0], sh_end - ss[0][0], text="3 DECEMBER 2005", font="700 64px Mono", x=960, y=150, fill="#fff", ls="8px")
G("beast", H0, sh_end - H0, words=[{"t": ss[1][0] - H0 + .35, "text": "SANTA CLAUS", "fill": "#ff2a2a", "rot": -3, "size": 150, "y": 820, "hold": 99},
                                   ])
G("beast", H0, sh_end - H0, words=[{"t": ss[2][0] - H0 + .3, "text": "& THE GINGERBREAD MAN", "fill": "#d38b3a", "rot": 2, "size": 110, "y": 960, "hold": 99}])
S("riser", H0 + .5, -14)
M("m_epic", H0, sh_end - H0 + .2, gain=-18, fi=.5, fo=.2, trim=0)
T = sh_end
# Veo clip with its own audio ("Ho. Ho. Go."), cut on the bow release
SC = 6.1
V("santa", T, SC, kb={"z0": 1.0, "z1": 1.12}, grade={"sat": 1.2})
A("media/vid/santa.mp4", T, 1, dur=SC, fo=.1)
G("letterbox", T, SC + 5.0, h=120)
G("subs", T, SC, font="italic 600 58px Cormorant", lines=[{"t0": 1.6, "t1": 4.6, "text": "[whispering]  Ho.  Ho.  Go."}])
S("bow", T + 4.3, 0)
T += SC
# arrow slow-mo
Ar = T
V("arrow", Ar, 5.0, speed=.8, kb={"z0": 1.0, "z1": 1.25}, grade={"sat": 1.35, "con": 1.1})
FX("fx_embers", Ar, 5.0, alpha=.7, speed=.8)
S("arrow", Ar, -2); S("riser", Ar + 1.0, -8)
G("particles", Ar, 5.0, kind="snow", n=120, alpha=.5)
M("m_epic", Ar, 18.0, gain=-10, fi=.2, fo=1.5, trim=8.0)
T = Ar + 5.0
# IMPACT
Im = T
Lp, sp = VO("santa_pay", Im + .1, gain=2)
V("impact", Im, 8.0, kb={"z0": 1.2, "z1": 1.0}, grade={"sat": 1.45, "con": 1.15}, shake={"amp": 26, "decay": 1.2})
G("flash", Im, .3, color="#fff", alpha=.5)
BOOM(Im, big=1.3)
FX("fx_fireball", Im + .5, 2.4, alpha=.5, kb={"z0": 2.0, "x0": -.25}, fo=.8)
FX("fx_fireball", Im + .8, 2.4, alpha=.5, kb={"z0": 1.8, "x0": .28}, fo=.8)
G("fire", Im, 8.0, h=640, size=100, fi=.05)
G("heat", Im + .3, 3.2, amt=.8)
G("zoomblur", Im, .8, amt=2)
G("rgbsplit", Im, .9, amt=24)
G("particles", Im, 1.6, kind="sparks", n=220, fi=0)
G("particles", Im, 8.0, kind="embers", n=240)
G("beast", Im, 3.0, words=[{"t": .1, "text": "FLAMING", "fill": "#ffb300", "rot": -4, "size": 230, "y": 430, "hold": 3},
                           {"t": .7, "text": "ARROW!!!", "fill": "#ff2a2a", "rot": 3, "size": 260, "y": 660, "hold": 3}])
S("ignite", Im, 2); S("boom", Im, 0); S("braam", Im + .1, -3); S("fire", Im + .5, -10, dur=7, fo=1)
# wanted posters
Wt = Im + 3.6
Lt, st_ = VO("santa_true", Wt + .3)
G("solid", Wt, Im + 8.0 - Wt + 1.2, color="#000", alpha=.45, fi=.3)
G("wanted", Wt, Im + 8.0 - Wt + 1.2, posters=[
    {"t": .2, "src": "../media/img/santa.png", "crop": [540, 290, 600, 500], "x": 620, "y": 540, "rot": -6, "name": "SANTA CLAUS", "crime": "Arson (flaming arrow)", "crime2": "Last seen: North Pole?"},
    {"t": .6, "src": "../media/img/santa.png", "crop": [150, 470, 540, 450], "x": 1300, "y": 560, "rot": 5, "name": "THE GINGERBREAD MAN", "crime": "Accessory. Binoculars.", "crime2": "Run, run, as fast as you can"}])
S("whoosh2", Wt + .2, -6); S("whoosh2", Wt + .6, -6); S("stamp", Wt + .9, -6)
T = Im + 8.0 + 1.2

# ---- I. TWIST -----------------------------------------------------------
I0 = T
Lc, sc = VO("twist_count", I0 + .4)
en = sc[-1][1] + .9
V("triumph", I0, en - I0, speed=.55, kb={"z0": 1.0, "z1": 1.2}, grade={"sat": 1.35})
G("particles", I0, en - I0, kind="confetti", n=150)
G("checks", I0, en - I0, x0=390, dx=380, y=330, items=[{"year": y, "t": sc[i][0] - I0 + .1} for y, i in
                                                       (("2017", 1), ("2018", 2), ("2019", 4), ("2020", 5))])
for i in (1, 2, 4, 5):
    S("ding", sc[i][0] + .1, -8)
G("beast", I0, en - I0, words=[{"t": sc[-1][0] - I0, "text": "4 YEARS UNDEFEATED", "fill": "#ffd400", "size": 150, "y": 800, "hold": 9}])
S("crowd_cheer", sc[-1][0], -6)
FX("fx_burst", sc[-1][0] - .1, en - sc[-1][0] + .1, fo=.4)
FX("fx_shockwave", sc[-1][0] - .1, 2.0, alpha=.8, fo=.5)
S("ignite", sc[-1][0], -4)
M("m_triumph", I0, en - I0 + 9.6, gain=-9, fi=.2, fo=1.0)
T = en
Tg = T
Lg, sg = VO("goat_triumph", Tg + .4, gain=1)
en = sg[-1][1] + .6
V("soliloquy", Tg, en - Tg, from_=6.0, speed=.45, kb={"z0": 1.05, "z1": 1.3}, grade={"sat": 1.2, "bri": 1.15, "sepia": .25})
G("letterbox", Tg, en - Tg + .8, h=120)
G("particles", Tg, en - Tg, kind="confetti", n=80, alpha=.7)
G("subs", Tg, en - Tg, lines=[{"t0": s[0] - Tg, "t1": (sg[i + 1][0] - Tg - .05) if i + 1 < len(sg) else en - Tg, "text": t}
                              for i, (s, t) in enumerate(zip(sg, ["Behold!", "Four winters! The fire cannot touch me!", "I am...", "ETERNAL!"]))])
S("heavenly", Tg + .2, -10)
T = en
# record scratch → 2023
S("scratch", T, -2)
V("soliloquy", T, .9, from_=9.0, grade={"gray": 1, "bri": .8}, kb={"z0": 1.3})
T += .9
Bd = T
Lb, sb = VO("birds_2023", Bd + .1)
G("solid", Bd, sb[1][0] - Bd - .1, color="#000")
G("yearSlam", Bd, sb[1][0] - Bd - .1, year=2023, fill="#fff", rot=0)
S("boom", Bd, -8)
tb = sb[1][0] - .1
Lw, sw = VO("birds_why", sb[-1][1] + .5, maxgap=1.3)
en = sw[-1][1] + 1.0
V("birds", tb, en - tb, kb={"z0": 1.0, "z1": 1.2}, grade={"sat": .8, "con": 1.2}, shake={"amp": 3})
S("birds", tb, -6, dur=en - tb, fo=.8)
G("lower", sb[-1][1] + .5, en - sb[-1][1] - .5, tag="CAUSE OF DEATH", title="JACKDAWS", sub="The straw had unusually many seeds")
T = en

# ---- J. SAGE --------------------------------------------------------------
J = T
Lz, sz = VO("sage", J + 1.2, gain=1, maxgap=1.4)
en = sz[-1][1] + 2.2
V("ink", J, en - J, speed=6.0 / (en - J), kb={"z0": 1.0, "z1": 1.12, "x0": .0, "x1": -.03}, fi=.8, fo=.8)
S("gong", J, -4)
M("m_zen", J, en - J, gain=-13, fi=1.0, fo=1.2)
ink = "#2a2016"
G("quote", sz[0][0] - .1, sz[5][0] - sz[0][0] - .2, x=1360, y=260, fo=.4, lines=[
    {"text": "It withstood fire.", "t": 0, "fill": ink, "size": 76},
    {"text": "Ice.  Arrows.", "t": sz[1][0] - sz[0][0], "fill": ink, "size": 76},
    {"text": "A Volvo.", "t": sz[3][0] - sz[0][0], "fill": ink, "size": 76},
    {"text": "And a helicopter.", "t": sz[4][0] - sz[0][0], "fill": ink, "size": 76}])
G("quote", sz[5][0] - .1, sz[8][0] - sz[5][0] - .2, x=1300, y=360, fo=.4, lines=[
    {"text": "It was undone by small birds", "t": 0, "fill": ink, "size": 76},
    {"text": "who were simply hungry.", "t": sz[7][0] - sz[5][0], "fill": ink, "size": 76}])
G("quote", sz[8][0] - .1, en - sz[8][0] + .1, x=1260, y=320, fo=.8, lines=[
    {"text": "Nature does not hurry,", "t": 0, "fill": ink, "size": 84},
    {"text": "yet everything is accomplished.", "t": sz[9][0] - sz[8][0], "fill": ink, "size": 84},
    {"text": "— Lao Tzu  (this one is real)", "t": sz[9][1] - sz[8][0] + .2, "dy": 200, "font": "500 30px Inter5", "fill": "#5a4a3a"}])
G("seal", sz[9][1] + .5, en - sz[9][1] - .5, x=1720, y=860)
S("stamp", sz[9][1] + .5, -10)
T = en

# ---- K. CREDITS -------------------------------------------------------------
K = T
Kd = 19.0
V("triumph", K, Kd, speed=.3, grade={"bri": .3, "blur": 6, "sat": 1.2}, fi=.5)
G("particles", K, Kd, kind="confetti", n=60, alpha=.5)
rows = [{"text": "AN  @amyleesterling  PRODUCTION", "head": True}, {"gap": 20}, {"text": "THE G.O.A.T.", "big": True}, {"gap": 10},
        {"text": "60 goats built.  43 destroyed or damaged."},
        {"text": "Every event in this film really happened.*"},
        {"text": "*Dialogue dramatised. Santa's tactical vest unconfirmed.", "head": True}, {"gap": 90},
        {"text": "STARRING", "head": True}, {"text": "The Gävle Goat  as itself"}, {"gap": 40},
        {"text": "ALSO STARRING", "head": True}, {"text": "Santa Claus  &  The Gingerbread Man  (allegedly)"},
        {"text": "One Volvo Amazon"}, {"text": "Several hundred jackdaws"}, {"text": "Storm Johannes"}, {"gap": 40},
        {"text": "WRITTEN, DIRECTED, ANIMATED & EDITED BY", "head": True}, {"text": "Claude  “The Goatfather”"}, {"gap": 40},
        {"text": "EXECUTIVE PRODUCER  &  CHIEF ARSONIST OF CREDITS", "head": True}, {"text": "@amyleesterling"}, {"gap": 40},
        {"text": "IMAGES · VIDEO · VOICES · SOUND · SCORE", "head": True},
        {"text": "Runway API — Gemini Image 3 Pro · Veo 3.1 · Gen-4.5"}, {"text": "ElevenLabs v3 · ElevenLabs SFX · Seed Audio"}, {"gap": 40},
        {"text": "NO GOATS WERE HARMED IN THE MAKING OF THIS FILM", "head": True}, {"text": "(by us)"}]
G("fire", K, Kd, h=380, size=70, intensity=.75, fi=1.0, fo=1.0)
FX("fx_embers", K, 6.0, alpha=.6, fo=1.0)
FX("fx_embers", K + 6.0, 6.0, alpha=.6, fi=1.0, fo=1.0)
FX("fx_embers", K + 12.0, Kd - 12.0, alpha=.6, fi=1.0, fo=1.0)
G("credits", K, Kd, rows=rows, speed=150)
M("m_credits", K, Kd, gain=-8, fi=.3, fo=1.5)
T = K + Kd

# ---- L. POST-CREDITS -----------------------------------------------------------
Lp0 = T
G("solid", Lp0, 1.0, color="#000")
G("caption", Lp0 + .1, .9, text="MEANWHILE...", font="700 44px Mono", fill="#aaa", ls="10px")
T += 1.0
P = T
Lq, sq = VO("post_2025", P + .3, maxgap=1.3)
V("storm", P, 6.0, grade={"sat": 1.2, "con": 1.1}, kb={"z0": 1.0, "z1": 1.1})
S("wind", P, -6, dur=6.0, fo=.3)
S("thud", P + 3.25, 2); S("boom", P + 3.25, -10); G("zoomblur", P + 3.3, .5, amt=1.2)
G("lower", P + .4, 4.8, tag="27 DEC 2025", title="STORM JOHANNES", sub="The goat did not burn. It fell over.")
T = max(P + 6.0, sq[-1][1] + .3)
V("storm", P + 6.0, T - (P + 6.0) + 2.4, from_=5.95, grade={"sat": 1.0, "bri": .9}, kb={"z0": 1.1, "z1": 1.2})  # hold on the faceplant
Lf, sf = VO("goat_fine", T + .3, gain=-2, fx="lowpass=f=900,volume=1.6")
G("subs", T, 2.4, font="italic 600 60px Cormorant", lines=[{"t0": .3, "t1": 2.3, "text": "[muffled, face-down in the snow]   ...I'm fine."}])
S("snow_amb", T, -10, dur=2.4)
T += 2.4
G("solid", T, 4.2, color="#000")
G("particles", T, 4.2, kind="embers", n=200)
Lo, so = VO("hype_outro", T + .3)
G("beast", T, 4.2, words=[{"t": .3, "text": "IT WILL BE REBUILT.", "fill": "#fff", "size": 120, "y": 440, "hold": 9},
                          {"t": so[-1][0] - T, "text": "IT ALWAYS IS.", "fill": "#ffb300", "size": 150, "y": 620, "hold": 9}])
S("braam", so[-1][0], -6)
G("fire", T, 4.2, h=420, size=75, fi=.5, intensity=.9)
BOOM(so[-1][0], big=.9)
T += 4.2
G("particles", T, 4.0, kind="embers", n=260, fi=.05)
V("fire_title", T, 4.0, speed=.85, grade={"con": 1.15, "sat": 1.2}, kb={"z0": .8, "z1": .86, "y0": -.07}, fo=.8)
for dx in (-.34, 0, .34):
    FX("fx_flamewall", T, 4.0, alpha=.6, kb={"z0": 1.1, "x0": dx, "y0": .34}, fo=.8)
G("caption", T + .6, 3.2, text="Greatest Of All Tinder", font="italic 600 70px Cormorant", y=880, fill="#ffe9c4", fi=.5, fo=.6)
G("caption", T + 1.0, 2.8, text="Written & Directed by Claude “The Goatfather”   ·   Produced by @amyleesterling", font="500 28px Inter5", y=960, fill="#e6d2b0", ls="4px", fi=.5, fo=.6)
G("zoomblur", T, .5, amt=1.4)
S("ignite", T, -6)
T += 4.0
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
        if L["type"] in ("zoomblur", "rgbsplit", "flash", "whip"):
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
