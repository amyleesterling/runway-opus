"""Measure mean loudness (dBFS) of every audio asset so edit.py can normalise before mixing."""
import glob, json, re, subprocess
out = {}
for p in sorted(glob.glob('media/vo/*.mp3') + glob.glob('media/sfx/*.mp3') + glob.glob('media/music/*.wav') + glob.glob('media/vid/*.mp4')):
    r = subprocess.run(['ffmpeg', '-i', p, '-af', 'silenceremove=stop_periods=-1:stop_threshold=-45dB,volumedetect', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    m = re.search(r'mean_volume: (-?[\d.]+) dB', r)
    if m:
        out[p] = float(m.group(1))
json.dump(out, open('media/levels.json', 'w'), indent=1)
for k, v in out.items(): print(f'{v:6.1f}  {k}')
