# 環境構築

## uv インストール
パッケージマネージャーは [uv](https://docs.astral.sh/uv/) を利用。  
[こちら](https://docs.astral.sh/uv/getting-started/installation/
)のドキュメントに従って uv をインストールする。

## 依存パッケージ
下記の依存パッケージをダウンロードする。
- opencv-python 
- ultralytics
``` bash
uv sync
```

# 精度評価

``` bash
uv run python framework/accuracy_evaluation/main.py
```
