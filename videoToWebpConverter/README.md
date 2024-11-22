# Video to WebP Converter

動画や GIF 画像を WebP 形式に簡単に変換できる GUI ツールです。ドラッグ＆ドロップで簡単に操作でき、様々な形式の動画に対応しています。

## 特徴

- ドラッグ＆ドロップで簡単変換
- 複数の動画フォーマットに対応（MP4, MOV, AVI, MKV, GIF）
- カスタマイズ可能な設定（フレームレート、品質、サイズ）
- プログレスバーによる変換進捗の可視化

## 必要要件

- Python 3.7 以上
- FFmpeg（動画変換用）
- tkinter
- tkinterdnd2

## インストール手順

### 1. Python の依存パッケージのインストール

```bash
pip install tkinter
pip install tkinterdnd2
```

### 2. FFmpeg のインストール

#### Windows:

1. [FFmpeg 公式サイト](https://www.ffmpeg.org/download.html)から最新版をダウンロード
2. ダウンロードした zip ファイルを解凍
3. bin フォルダを環境変数 PATH に追加

#### macOS:

```bash
brew install ffmpeg
```

#### Linux:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg
```

## 使用方法

1. スクリプトを実行してアプリケーションを起動:

```bash
python main.py
```

2. メインウィンドウの設定項目:

   - **フレームレート (FPS)**

     - デフォルト: 10fps
     - 推奨範囲: 5-30fps

   - **幅 (ピクセル)**

     - デフォルト: 640px
     - 高さは自動的にアスペクト比を維持

   - **品質 (0-100)**
     - デフォルト: 75
     - 高品質: 80-100
     - 低容量: 0-50

3. 変換したい動画ファイルをウィンドウにドラッグ＆ドロップ
4. 変換完了後、元のファイルと同じフォルダに変換された WebP ファイルが生成されます

## 注意事項

- GIF 変換時はプログレスバーが不確定モードになります
- 大きなファイルの変換には時間がかかる場合があります
- 同名ファイルが存在する場合は自動的に連番が付加されます

## トラブルシューティング

- **「ffmpeg: command not found」エラー**
  → FFmpeg が正しくインストールされ、環境変数 PATH に追加されているか確認してください
- **変換エラー**
  → 入力ファイルが破損していないか、十分なディスク容量があるか確認してください

## ライセンス

MIT License

## 作者

このツールは個人ブログ [UhiyamaLab](https://uhiyama-lab.com/) の記事用に作成されました。
