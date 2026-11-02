"""Build a one-page submission report from measured results."""
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph

out = Path(__file__).resolve().parents[1] / 'outputs'
m = json.loads((out / 'manifest.json').read_text())
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
base = ParagraphStyle('body', fontName='HeiseiKakuGo-W5', fontSize=11, leading=18,
                      wordWrap='CJK', spaceAfter=10, textColor=colors.HexColor('#203048'))
title = ParagraphStyle('title', parent=base, fontSize=19, leading=28, spaceAfter=10)
head = ParagraphStyle('head', parent=base, fontSize=12, leading=19, spaceBefore=13,
                      spaceAfter=6, textColor=colors.HexColor('#12665e'))
small = ParagraphStyle('small', parent=base, fontSize=9, leading=14)
story = []
def add(text, style=base):
    story.append(Paragraph(text, style))

add('ACTによるロボットアームの挨拶動作', title)
add('Physical AI 応用編1 最終課題 / sonodd2026', small)
add('目的', head)
add('Day4・Day5のROS 2、Gazebo、LeRobot ACTを使い、CRANE+ V2に手振りとハンド開閉による挨拶を学習させる。')
add('方法', head)
add(f'教師デモは自作スクリプトで生成し、rosbagに記録した。12エピソード・{m["frames"]:,}フレームでACTを'
    f'{m["steps"]:,}ステップ学習。実行時は5関節の現在角度から目標角度を20 Hzで推論し、教師指令を停止した状態で制御する。')
add('工夫', head)
add('講義のお辞儀を手振りへ変更した。手首とハンドの位相をずらし、向きを徐々に変えて動作の進行を区別しやすくすることを狙った。データ変換と推論の関節順・時間間隔を統一した。')
add('結果と課題', head)
counts='・'.join(str(r['wrist_positive_negative_pairs']) for r in m['rollouts'])
add(f'25秒の評価3試行で、手首の正負の振りをそれぞれ{counts}組確認した（±0.15 radを交互に超えた組数）。'
    'ハンド開閉も確認したが、3回で停止して原点へ戻る条件は未達。停止条件と状態履歴の改善が課題である。')
add('動画は教師デモとAI実行1試行を収録。Gazeboの実状態をRVizで表示した等速録画であり、実機検証は行っていない。', small)
add('コード・出典', head)
add('<link href="https://github.com/sonodd/pai2026-advanced1-crane-wave" color="#12665e">github.com/sonodd/pai2026-advanced1-crane-wave</link>',small)
add('使用：matsuolab/pai_training、Hugging Face LeRobot、AI-Robot-Book-HumbleのDocker・CRANE+モデル。実装と文書作成に生成AIの支援を利用した。',small)

target = out / '説明資料_PAI最終課題_sonodd2026.pdf'
SimpleDocTemplate(str(target), pagesize=A4, leftMargin=48, rightMargin=48,
                  topMargin=42, bottomMargin=40, title='ACTによるロボットアームの挨拶動作',
                  author='sonodd2026').build(story)
print(target)
