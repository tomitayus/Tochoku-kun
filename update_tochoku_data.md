# tochoku_data.py の更新方法

## 手順

1. `/home/user/Tochoku-kun/tochoku_data.py` ファイルを開く

2. ファイルの末尾にある以下の行を探す:
```python
 'sheet3': [],  # ファイルサイズの都合で省略、必要に応じて追加
 'Sheet4': []}  # ファイルサイズの都合で省略、必要に応じて追加
```

3. 上記の行を、ユーザーが提供した元のDATAの該当部分に置き換える:
```python
 'sheet3': [ユーザー提供のsheet3データ全て],
 'Sheet4': [ユーザー提供のSheet4データ全て]}
```

4. ファイルを保存

## または

元のExcelファイル（`Tochoku.ver9_2026.01.xlsx`）がある場合は、
それを `/home/user/Tochoku-kun/` ディレクトリに配置し、
スクリプトを修正してExcelから直接読み込むようにすることもできます。

## 次のステップ

データが完全に統合されたら:
```bash
python3 tochoku_scheduler_full.py
```

でスケジューラーを実行できます。
