import subprocess, sys
from PIL import Image, ImageDraw
# usage: tsheet.py video out.jpg t1 t2 ...  (5 columns, 384x216 tiles)
v, out, ts = sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3:]]
W, H, C = 384, 216, 5
sh = Image.new('RGB', (W * C, H * ((len(ts) + C - 1) // C)))
for i, t in enumerate(ts):
    subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-ss', str(t), '-i', v, '-frames:v', '1', '-s', f'{W}x{H}', '/tmp/_t.jpg'])
    im = Image.open('/tmp/_t.jpg'); ImageDraw.Draw(im).text((4, 4), f'{t:.1f}', fill='yellow')
    sh.paste(im, ((i % C) * W, (i // C) * H))
sh.save(out, quality=88)
