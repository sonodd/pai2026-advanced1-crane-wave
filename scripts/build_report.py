"""Build the submission PDF from verified measurements in outputs/manifest.json."""
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
m = json.loads((OUT / 'manifest.json').read_text())
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
base = ParagraphStyle('base', fontName='HeiseiKakuGo-W5', fontSize=9.5, leading=15,
                      wordWrap='CJK', textColor=colors.HexColor('#203048'), spaceAfter=7)
title = ParagraphStyle('title', parent=base, fontSize=20, leading=28, spaceAfter=10)
head = ParagraphStyle('head', parent=base, fontSize=12, leading=18, spaceBefore=9, spaceAfter=6,
                      textColor=colors.HexColor('#12665e'))
small = ParagraphStyle('small', parent=base, fontSize=8, leading=12, spaceAfter=5)
story = []
def add(text, style=base):
    story.append(Paragraph(text, style))
def table(rows, widths):
    t = Table([[Paragraph(str(v), small) for v in row] for row in rows], colWidths=widths)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4f1ef')),
                          ('GRID',(0,0),(-1,-1),.3,colors.HexColor('#c7d2df')),
                          ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                          ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.append(t)

add('模倣学習によるロボットアームの挨拶動作', title)
add('Physical AI 応用編1 最終課題 / sonodd2026 / 2026-11-02', small)
add('1. 目的と講義との関係', head)
add('CRANE+ V2が手を振って挨拶するタスクを実装した。Day4・Day5で学んだROS 2のトピック通信、'
    'Gazeboでのロボット制御、rosbagによるデータ収集、LeRobot ACTによる模倣学習を組み合わせた。'
    '講義の「お辞儀」を、腕を構え、手首を振りながらハンドを開閉する動作に変更した。')
add('2. AIが担う部分', head)
add('教師デモは自作スクリプトで生成し、Gazeboの関節状態と指令をrosbagに記録した。人のテレオペ記録ではない。'
    'ACTは、アーム4軸とハンド1軸の現在角度を入力し、次の目標関節角度を推論する。'
    '実行時には教師デモを停止し、学習したモデルの出力だけをROS 2のコントローラへ送る。')
table([['工程','実装・役割'],
       ['シミュレーション','講義Docker / ROS 2 Humble / Gazebo / CRANE+ V2'],
       ['教師データ','20 Hzの関節指令。振幅・周期・向きを変えた12エピソード'],
       ['変換と学習',f'LeRobotDataset {m["frames"]}フレーム → ACT / CPU / {m["steps"]:,}ステップ'],
       ['デプロイ','関節状態 → ACT → JointTrajectory。16時刻を予測し、先頭1時刻を実行'],
       ['動画表示','Gazeboで計算した関節状態をRVizで可視化し、画面を録画']], [80,430])
add('3. 工夫した点', head)
add('手首の往復とハンド開閉の位相をずらし、向きも左から右へ徐々に変えることで、現在の関節状態から'
    '動作の進み具合を区別しやすくすることを狙った。教師の周期は2.2〜2.5秒とし、関節速度上限2 rad/s以内に収めた。'
    '変換と推論の関節順を揃え、20 Hzに対応する0.05秒間隔で将来の行動を学習する設定にした。')
add('学習用12本とは別にseed=99のデモを1本収集した。記録済み状態での予測誤差と、実際にモデルで動かす'
    '閉ループ試験を区別し、出力指令・実際の関節状態・評価結果を保存した。')
story.append(PageBreak())

add('4. 実測結果', head)
add(f'Apple SiliconのMacで学習を行い、Docker内で推論した。学習側はPyTorch 2.7.0、推論側は2.6.0。'
    f'学習に含めない1エピソード（seed=99）の記録済み状態に対する行動予測RMSEは'
    f'{m["heldout_rmse_rad"]:.4f} rad（全5軸の二乗誤差平均の平方根）だった。これは記録状態での予測精度であり、動作の成功率ではない。')
rows = [['試行','手首の正負の振りの組','終了時の最大角度','原点への復帰']]
for i,r in enumerate(m['rollouts'],1):
    rows.append([i,r['wrist_positive_negative_pairs'],f'{max(abs(x) for x in r["final_state_rad"]):.3f} rad',
                 '確認' if r['returned_home_within_0_1_rad'] else '未達'])
table(rows,[45,155,155,155])
add('手首が+0.15 radと-0.15 radを交互に超える動きを数えた。原点復帰は、終了時の全5軸の絶対角度が'
    '0.1 rad未満かどうかで判定した。各試行は初期姿勢へ戻してからモデルだけで動かした。',small)
add(m['result_description'])
preview = OUT / 'preview.png'
if preview.exists():
    from PIL import Image as PILImage
    with PILImage.open(preview) as im:
        w,h=im.size
    story.append(Image(str(preview), width=250, height=250*h/w))
    add('図. Gazeboの実際の関節状態を表示したRViz画面。動画内で教師デモとACT推論を明示した。',small)
add('5. 限界と考察', head)
add('画像・言語・物体認識は使用していない。入力はシミュレータが出力する関節角度であり、実機での検証も未実施。'
    '少数データでの模倣学習なので、動作回数や原点への復帰は教師と完全には一致しない。'
    '今後は停止条件の学習、状態履歴の導入、初期姿勢や速度を変えた評価を行う。')
add('6. 再現・出典・AI利用', head)
add('公開コードのREADMEに環境構築、収集、変換、学習、推論の手順を記載した。'
    '実装と文書作成には生成AIの支援を使用。ロボット動作中のAIは学習済みACTである。',small)
add('<link href="https://github.com/sonodd/pai2026-advanced1-crane-wave" color="#12665e">github.com/sonodd/pai2026-advanced1-crane-wave</link>',small)
add('出典: github.com/matsuolab/pai_training（b4d6b545）、github.com/huggingface/lerobot（768e3666）、'
    'github.com/matsuolab/physicalai_teleop、AI-Robot-Book-HumbleのDocker環境およびCRANE+モデル。',small)

def footer(c,doc):
    c.setFont('HeiseiKakuGo-W5',8)
    c.setFillColor(colors.HexColor('#667085'))
    c.drawString(42,24,'PAI最終課題_sonodd2026')
    c.drawRightString(A4[0]-42,24,str(doc.page))

target=OUT/'説明資料_PAI最終課題_sonodd2026.pdf'
SimpleDocTemplate(str(target),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=34,bottomMargin=40,
                  title='模倣学習によるロボットアームの挨拶動作',author='sonodd2026').build(story,onFirstPage=footer,onLaterPages=footer)
print(target)
