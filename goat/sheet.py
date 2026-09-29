import subprocess, sys, json
from PIL import Image, ImageDraw
# usage: sheet.py out.jpg clip1 clip2 ...  -> 4 frames per clip in a row
clips = sys.argv[2:]; W, H = 480, 270
sheet = Image.new('RGB', (W * 4, H * len(clips)))
for r, c in enumerate(clips):
    p = f'media/vid/{c}.mp4'
    dur = float(subprocess.run(['ffmpeg', '-i', p], capture_output=True, text=True).stderr.split('Duration: ')[1].split(',')[0].split(':')[2])
    for k in range(4):
        t = dur * (k + .5) / 4
        subprocess.run(['ffmpeg', '-v', 'quiet', '-y', '-ss', str(t), '-i', p, '-frames:v', '1', '-s', f'{W}x{H}', '/tmp/_f.jpg'])
        im = Image.open('/tmp/_f.jpg'); ImageDraw.Draw(im).text((5, 5), f'{c} {t:.1f}s', fill='yellow')
        sheet.paste(im, (k * W, r * H))
sheet.save(sys.argv[1], quality=85)
