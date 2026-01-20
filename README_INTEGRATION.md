# 当直スケジューラー統合版 使用方法

## 概要
このディレクトリには、元のColabコードをローカル環境で実行できるように変換したバージョンが含まれています。

## ファイル構成
- `tochoku_scheduler.py` - メインスクリプト（まだ作成中）
- `tochoku_data.py` - データファイル（sheet1, sheet2は含まれているが、sheet3とSheet4は未完成）
- `test_simple.py` - データ読み込みテスト用

## データ統合方法

### 方法1: tochoku_data.pyを直接編集

`tochoku_data.py`ファイルを開き、以下の部分を編集します:

```python
# 現在:
 'sheet3': [],  # 空
 'Sheet4': []   # 空

# 変更後:
 'sheet3': [ユーザー提供のsheet3データをここにコピー],
 'Sheet4': [ユーザー提供のSheet4データをここにコピー]
```

### 方法2: 別ファイルから読み込み

より簡単な方法として、元のExcelファイルがある場合は以下のように読み込むことができます:

```python
import pandas as pd

# Excelファイルから直接読み込み
xls = pd.ExcelFile('Tochoku.ver9_2026.01.xlsx')
shift_df = pd.read_excel(xls, sheet_name='sheet1')
availability_df = pd.read_excel(xls, sheet_name='sheet2')
schedule_df = pd.read_excel(xls, sheet_name='sheet3')
sheet4_df = pd.read_excel(xls, sheet_name='sheet4')
```

## 次のステップ

1. `tochoku_data.py`にsheet3とSheet4のデータを追加
2. メインスクリプト`tochoku_scheduler_full.py`を作成（元のColabコード全体を統合）
3. テスト実行

##注意事項
- sheet3とSheet4のデータは非常に大きいため、直接編集する場合は慎重に行ってください
- Pythonファイルのサイズが大きくなりすぎる場合は、Excelファイルから直接読み込む方法を推奨します
