"""Edit actual simulator recordings; never synthesize robot motion.

Requires ffmpeg and Pillow. All source clips retain their recorded speed.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

p = argparse.ArgumentParser()
p.add_argument('--font', type=Path, required=True, help='Japanese TrueType/OpenType font')
args = p.parse_args()
root = Path(__file__).resolve().parents[1]
out = root / 'outputs'
segments = out / 'segments'
segments.mkdir(exist_ok=True)
m = json.loads((out / 'manifest.json').read_text())
ffmpeg = shutil.which('ffmpeg')
if not ffmpeg:
    raise RuntimeError('ffmpeg is required')
W, H = 886, 882
BG, FG, ACCENT = '#111d2d', '#f0f5fa', '#6de3c4'
def font(size):
    return ImageFont.truetype(str(args.font), size)
def run(*arguments):
    subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', *map(str, arguments)], check=True)
def encode_tail():
    return ['-an','-r','25','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p']
files = []
def card(name, title, lines, seconds):
    im = Image.new('RGB', (W,H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((48,160,838,166), fill=ACCENT)
    d.text((48,205),title,font=font(34),fill=FG)
    for i,line in enumerate(lines):
        d.text((48,310+i*60),line,font=font(25),fill=FG)
    d.text((48,790),'Physical AI 応用編1  |  sonodd2026',font=font(21),fill=ACCENT)
    png, video = segments/f'{name}.png', segments/f'{name}.mp4'
    im.save(png)
    run('-loop','1','-framerate','25','-i',png,'-t',seconds,*encode_tail(),video)
    files.append(video)
def clip(name, title, subtitle):
    im=Image.new('RGB',(W,100),BG)
    d=ImageDraw.Draw(im)
    d.text((25,12),title,font=font(28),fill=ACCENT)
    d.text((25,56),subtitle,font=font(20),fill=FG)
    png, video=segments/f'{name}-header.png',segments/f'{name}.mp4'
    im.save(png)
    run('-i',out/f'{name}-raw.mp4','-i',png,
        '-filter_complex',f'[0:v]pad={W}:{H}:0:100:color=0x111d2d[base];[base][1:v]overlay=0:0[v]',
        '-map','[v]',*encode_tail(),video)
    files.append(video)

card('intro','ACTで学ぶ、ロボットの挨拶',[
    'CRANE+ V2 / ROS 2 / Gazebo / LeRobot',
    '講義のお辞儀を、手振りとハンド開閉へ変更',
    '教師デモ → 12本収集 → ACT学習 → 自律実行',
    '録画は等速。Gazeboの状態をRVizで表示。'],8)
clip('teacher-demo','教師デモ：スクリプトによる指令','腕を構える → 手首を3回振る・開閉 → 原点へ戻る')
card('method','ここからは、学習済みACTが制御',[
    f'学習：12エピソード / {m["frames"]}フレーム / 4,000 steps',
    '入力：5関節の現在角度。画像入力は使わない。',
    '出力：次の目標角度。20 Hzで繰り返し推論。',
    '各試行の前だけ初期姿勢へ戻す。教師指令は停止。'],8)
for i in range(1,4):
    clip(f'act-{i:02d}',f'ACTによる実行：試行 {i} / 3','Gazebo物理シミュレーションの実状態 / 録画を等速再生')
counts='・'.join(str(r['wrist_positive_negative_pairs']) for r in m['rollouts'])
card('results','結果と残った課題',[
    f'25秒 × 3試行で、手首の正負の振りは {counts} 組',
    'AIによる手振りとハンド開閉を確認。',
    '3回で止まること・原点への復帰は未達。',
    f'未学習デモの行動予測RMSE：{m["heldout_rmse_rad"]:.4f} rad',
    '記録状態での誤差は、タスク成功率とは異なる。'],10)
concat=segments/'concat.txt'
concat.write_text(''.join(f"file '{path.name}'\n" for path in files))
target=out/'PAI最終課題_sonodd2026.mp4'
run('-f','concat','-safe','0','-i',concat,'-c','copy','-movflags','+faststart',target)
print(target)
