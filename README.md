# ACTによるCRANE+ V2の挨拶動作

Physical AI 応用編1 最終課題（sonodd2026）。講義のROS 2 / Gazebo / LeRobot ACTで手振りとハンド開閉を学習した。

自作教師デモ12本・2,844フレームで4,000ステップ学習。5関節の現在角度から20 Hzで指令を推論する。25秒×3試行で手首の正負の振りを各9組確認したが、**3回で停止・原点復帰は未達**。評価ログは`outputs/`。動画は教師デモとAI実行1試行を収録した、Gazebo実状態のRViz表示・等速録画。

工夫：手首とハンドの位相をずらし、向きを徐々に変える教師動作を作成。変換・学習・推論の関節順と0.05秒間隔を統一した。

## 実行

Docker Desktopを起動し、このリポジトリで実行する（Apple Siliconはamd64エミュレーション）。既存`pai_ros2`を使う場合、このディレクトリが`/workspace`へマウントされていることを確認する。

```bash
bash run_pai_container.sh
# 1つだけ起動し、以降は別ターミナルで実行
# ブラウザ表示：http://localhost:6080
docker exec -it -u ubuntu pai_ros2 bash /workspace/scripts/launch_gazebo.sh
```

[学習済みモデル](https://github.com/sonodd/pai2026-advanced1-crane-wave/releases/tag/v1.0)をダウンロードして展開し、依存を導入する。

```bash
tar -xzf crane-wave-act-4000.tar.gz
docker exec -u ubuntu pai_ros2 bash /workspace/scripts/setup_training.sh
# 教師・テレオペ・別の推論を停止して実行
docker exec -u ubuntu pai_ros2 bash -lc 'source /workspace/scripts/ros_env.sh; python3 /workspace/scripts/reset_pose.py'
docker exec -u ubuntu pai_ros2 bash /workspace/scripts/run_infer.sh \
  --model-path /workspace/checkpoints/crane_plus_wave_act \
  --duration 25 --action-steps 1 --log /workspace/outputs/new-trial.csv
```

Gazebo GUIが表示されない場合は、別ターミナルでRVizを起動する。

```bash
docker exec -it -u ubuntu pai_ros2 bash -lc 'source /workspace/scripts/ros_env.sh; rviz2 -d /workspace/configs/wave.rviz'
```

## 再学習・評価

```bash
tar -xzf data/generated-lerobot-datasets.tar.gz
docker exec -u ubuntu pai_ros2 bash -lc 'export PYTHONPATH=/home/ubuntu/pai_runtime:/home/ubuntu/pai_training/lerobot; WANDB_MODE=disabled python3 /workspace/scripts/train_wave.py --upstream /home/ubuntu/pai_training --workspace /workspace --steps 4000'
# NumPyのあるPython環境で実行
python scripts/analyze_rollout.py outputs/act-01.csv outputs/act-02.csv outputs/act-03.csv --output outputs/rollout-summary.json
```

教師データを新規収集する場合は`collect.sh 12`、変換は上流の`rosbag2lerobot.py`を使う。設定は`setup_training.sh`が適用する。既存データは上書きしない。

今回の学習はMac / Python 3.10 / PyTorch 2.7.0、推論は講義Docker / PyTorch 2.6.0。学習環境は`requirements-native.txt`。batch size 2、Adam、学習率0.0001、seed 2026、予測16時刻・実行1時刻。環境やタイミングにより結果は変動する。

## 依存・出典

- [pai_training](https://github.com/matsuolab/pai_training)：`b4d6b5459066a80433475a83567504988875248a`
- [LeRobot](https://github.com/huggingface/lerobot)：`768e36660d1408c71118a2760f831c037fbfa17d`
- [講義Docker](https://github.com/AI-Robot-Book-Humble/docker-ros2-desktop-ai-robot-book-humble)・[CRANE+モデル](https://github.com/AI-Robot-Book-Humble/crane_plus)
- [physicalai_teleop](https://github.com/matsuolab/physicalai_teleop)：関節指令形式を参照。

実装・文書作成に生成AIの支援を利用。実機検証は未実施。
