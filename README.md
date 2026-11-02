# CRANE+ V2：ACTで学ぶ手振り動作

Physical AI 応用編1の最終課題（sonodd2026）。Day4・Day5の ROS 2 / Gazebo / LeRobot ACT を使い、講義の「お辞儀」を手振りとハンド開閉へ変更した。

**実測結果：ACTで手振り・ハンド開閉を確認した。教師どおり3回で止まり、原点へ戻る動作は未達。** 動画では教師デモとACT推論を区別している。Gazeboが物理計算し、その関節状態をRVizで表示した映像であり、実機の映像ではない。

## 構成とAIの役割

- 教師デモ：`scripts/wave_demo.py` が20 Hzで関節指令を生成。人のテレオペ記録ではない。
- データ：振幅・周期・向きを変えた12エピソード、2,844フレーム。seed=99の1本は学習に使わない。
- AI：LeRobot ACT。入力は5関節の現在角度。講義と同じ形式でstate/environment_stateの両キーへ渡す。独立した10個のセンサ値ではない。
- 出力：アーム4軸とハンド1軸の目標角度。16時刻（0.05秒間隔）を予測し、先頭の1時刻だけ実行。
- 学習：CPU、4,000ステップ、batch size 2、Adam、学習率0.0001、seed 2026。
- 閉ループ推論：実際の関節状態からACTで推論し、ROS 2のJointTrajectoryを送る。教師ノードは停止。
- 画像・言語・物体認識や実機検証は含まない。

## 結果と限界

`outputs/manifest.json` と `outputs/rollout-summary.json` に数値、`outputs/act-01.csv`〜`act-03.csv` に20 Hzの状態・指令を保存した。

- 未学習のseed=99デモ（221フレーム）に対する記録状態上の行動予測RMSE：**0.039523 rad**（全5軸の二乗誤差平均の平方根）。これは閉ループ成功率ではない。
- 3回の閉ループ試験は同じ初期姿勢・25秒（シミュレーション時間）。リセットは試行前だけ行う。
- 手首が+0.15 rad、-0.15 radを交互に超えた正負の組を数える。原点復帰は終了時の全5軸が絶対角度0.1 rad未満。
- 手振りの継続は確認できたが、回数制御と原点復帰は未達。状態だけでは動作の進行を十分に区別できない可能性がある。履歴入力と停止条件の改善が今後の課題。
- 予備比較では2,000ステップのモデルも手振りを行った。3,000ステップ・8時刻実行の試行は原点付近で停滞した。提出動画の3試行は4,000ステップ・1時刻実行で統一。

動画は録画時の等速。シミュレーション時間と実時間には差があり、モデル読み込みの待ち時間も収録される。Gazebo GUIがこの環境で起動しなかったため、実状態をRVizで表示した。

## 公開コードと依存元

自作スクリプト、評価結果、自分で生成した学習データを公開する。講義PDFや内部リポジトリは含めない。依存コード・ロボットモデルは各公開元から取得する。

- [講義Docker環境](https://github.com/AI-Robot-Book-Humble/docker-ros2-desktop-ai-robot-book-humble)
- [pai_training](https://github.com/matsuolab/pai_training)：`b4d6b5459066a80433475a83567504988875248a`
- [LeRobot](https://github.com/huggingface/lerobot)：submodule `768e36660d1408c71118a2760f831c037fbfa17d`
- [physicalai_teleop](https://github.com/matsuolab/physicalai_teleop)：トピック名と関節指令形式を参照。
- [CRANE+モデル](https://github.com/AI-Robot-Book-Humble/crane_plus)

実装・検証補助・文書作成には生成AIを利用した。ロボットを動かすAIはデータから学習したACTである。

## 再現手順

ホストでこのリポジトリをカレントにする。Docker DesktopとGitが必要。Apple Siliconではamd64エミュレーションを使う。Dockerイメージは展開後約25 GB。既存の`pai_ros2`を再利用する場合、このディレクトリが`/workspace`へマウントされていることを確認する。

```bash
bash run_pai_container.sh
# このlaunchは1つだけ起動し、実行したままにする
# 別ターミナルで後続を実行する
docker exec -it -u ubuntu pai_ros2 bash /workspace/scripts/launch_gazebo.sh
```

`http://localhost:6080` からコンテナのデスクトップを開く。Gazeboの物理サーバーとコントローラが動いていれば、以下のRVizで状態を表示できる。

```bash
docker exec -it -u ubuntu pai_ros2 bash -lc 'source /workspace/scripts/ros_env.sh; rviz2 -d /workspace/configs/wave.rviz'
```

### 1. データと学習環境

生成済みデータを使う場合：

```bash
tar -xzf data/generated-lerobot-datasets.tar.gz
```

自分で収集する場合は、既存データのない状態で次を実行する。既存エピソードは上書きしない。

```bash
docker exec -u ubuntu pai_ros2 bash /workspace/scripts/collect.sh 12
```

固定commitの上流と追加依存を導入する。講義イメージのPyTorchを利用する。

```bash
docker exec -u ubuntu pai_ros2 bash /workspace/scripts/setup_training.sh
docker exec -it -u ubuntu pai_ros2 bash
# 以下はコンテナ内
export PYTHONPATH=/home/ubuntu/pai_runtime:/home/ubuntu/pai_training/lerobot
export WANDB_MODE=disabled
cd /home/ubuntu/pai_training
# 新規rosbagを収集した場合のみ変換（生成済みデータを使うなら不要）
python3 scripts/rosbag2lerobot.py
python3 /workspace/scripts/train_wave.py --upstream /home/ubuntu/pai_training --workspace /workspace --steps 4000
```

今回の実測はMacのPython 3.10 / PyTorch 2.7.0で変換・学習し、講義コンテナのPyTorch 2.6.0で推論した。Mac学習環境のパッケージは`requirements-native.txt`。ネイティブで再学習する場合はその環境へ依存を入れ、`configure_training.py`と`train_wave.py`へホストの絶対パスを渡す。OS・PyTorch・実行タイミングの違いにより結果が完全一致しないことがある。

### 2. 推論

教師・テレオペ・別の推論ノードを停止して実行する。モデル読み込みには少し時間がかかる。

```bash
docker exec -u ubuntu pai_ros2 bash -lc 'source /workspace/scripts/ros_env.sh; python3 /workspace/scripts/reset_pose.py'
docker exec -u ubuntu pai_ros2 bash /workspace/scripts/run_infer.sh \
  --model-path /workspace/checkpoints/crane_plus_wave_act \
  --duration 25 --action-steps 1 --log /workspace/outputs/new-trial.csv
```

学習済みモデルは[GitHub Releases v1.0](https://github.com/sonodd/pai2026-advanced1-crane-wave/releases/tag/v1.0)の`crane-wave-act-4000.tar.gz`から取得し、このリポジトリのルートで展開する。`checkpoints/crane_plus_wave_act/`へ配置され、上の推論コマンドを実行できる。100 MBを超えるモデルはGit履歴に含めない。

```bash
tar -xzf crane-wave-act-4000.tar.gz
```

### 3. 評価と成果物

同じPython環境で保存したCSVを評価する：

```bash
python scripts/analyze_rollout.py outputs/act-01.csv outputs/act-02.csv outputs/act-03.csv --output outputs/rollout-summary.json
python scripts/evaluate_policy.py --dataset-root dataset/lerobot_dataset/heldout --model-path checkpoints/crane_plus_wave_act --output-dir outputs/offline-evaluation
```

`record_run.sh`は課題専用コンテナのRViz描画領域だけを録画する。936×976のVNCデスクトップで最大化した画面に合わせ、886×782を切り出す。他の寸法では座標調整が必要。`build_video.py`は実録画へ見出しを付け、`build_report.py`は保存済み数値からPDFを作る。

## 講義コードに加えた変更

`configure_training.py`は固定commitの外部checkoutに対し、パス・データ名・関節順・時刻を調整する。関節順は`joint1, joint2, joint4, joint3, hand`で統一。行動列は20 Hzに合わせて現在から0.05秒間隔、変換も同じ間隔にした。CPUスレッド数4、DataLoader worker数0、seed 2026、途中チェックポイント保存を設定する。

教師は手首とハンドの位相をずらし、ベースの向きを徐々に変える。12個のseedの指令について関節角度・速度上限内であることを数値確認した。シミュレーション用の実装であり、実機検証はしていない。
