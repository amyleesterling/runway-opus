import subprocess, numpy as np, glob, json, os, sys
out = {}
for p in sorted(glob.glob((sys.argv[1] if len(sys.argv) > 1 else 'media/vo') + '/*.mp3')):
    raw = subprocess.run(['ffmpeg','-v','quiet','-i',p,'-f','s16le','-ac','1','-ar','16000','-'],capture_output=True).stdout
    x = np.frombuffer(raw,np.int16).astype(np.float32)/32768
    hop = 160  # 10ms
    e = np.array([np.sqrt((x[i:i+320]**2).mean()) for i in range(0, len(x)-320, hop)])
    thr = max(0.012, e.max()*0.06)
    on = e > thr
    segs=[]; i=0
    while i < len(on):
        if on[i]:
            j=i
            while j < len(on) and on[j]: j+=1
            segs.append([i/100, j/100]); i=j
        else: i+=1
    # merge gaps < 0.18s
    m=[]
    for s in segs:
        if m and s[0]-m[-1][1] < 0.18: m[-1][1]=s[1]
        else: m.append(s)
    m=[s for s in m if s[1]-s[0]>0.06]
    out[os.path.basename(p)[:-4]] = {"dur": len(x)/16000, "a": m[0][0], "b": m[-1][1], "segs": [[round(a,2),round(b,2)] for a,b in m]}
json.dump(out, open(sys.argv[2] if len(sys.argv) > 2 else 'media/vo.json','w'), indent=1)
for k,v in out.items(): print(k, round(v['a'],2), round(v['b'],2), v['segs'])
