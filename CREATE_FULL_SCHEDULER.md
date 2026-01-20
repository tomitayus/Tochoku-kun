# 完全版スケジューラー作成手順

## 最も簡単な方法

元のColabコードをほぼそのままコピーして使用します。

### 手順

1. 新しいファイル`scheduler_complete.py`を作成
2. 以下のヘッダーを追加：

```python
#!/usr/bin/env python3
import pandas as pd
import numpy as np
from collections import defaultdict
import random
import sys

# データ読み込み
sys.path.insert(0, '/home/user/Tochoku-kun')
from tochoku_data import DATA as ORIG_DATA
from sheet3_sheet4_data import sheet3_data, sheet4_data

DATA = ORIG_DATA.copy()
DATA['sheet3'] = sheet3_data
DATA['Sheet4'] = sheet4_data

# DataFrameに変換
shift_df = pd.DataFrame(DATA['sheet1'])
availability_raw = pd.DataFrame(DATA['sheet2'])
schedule_raw = pd.DataFrame(DATA['sheet3'])
sheet4_raw_out = pd.DataFrame(DATA['Sheet4'])

# 日付変換
shift_df['Date'] = pd.to_datetime(shift_df['Date']).dt.normalize().dt.tz_localize(None)
availability_raw['Date'] = pd.to_datetime(availability_raw['Date']).dt.normalize().dt.tz_localize(None)
schedule_raw['Date'] = pd.to_datetime(schedule_raw['Date']).dt.normalize().dt.tz_localize(None)

# モックExcelFile
class MockExcelFile:
    def __init__(self, data_dict):
        self.sheet_names = list(data_dict.keys())

xls = MockExcelFile(DATA)
uploaded_filename = "Tochoku.ver9_2026.01.xlsx"

print("=" * 60)
print("   当直スケジュール自動生成ツール v2.1.1（統合版）")
print("=" * 60)
```

3. 元のColabコードの以下の部分を**削除**：
```python
from google.colab import files
# ...
uploaded = files.upload()
uploaded_filename = list(uploaded.keys())[0]
# ...
xls = pd.ExcelFile(io.BytesIO(uploaded[uploaded_filename]))
```

4. 元のColabコードの以下の部分も**削除**（最後の行）：
```python
files.download(output_path)
```

5. 残りの元のColabコード全体（# ユーザー設定 以降）をそのままコピー

6. 実行：
```bash
python3 scheduler_complete.py
```

## 自動化スクリプト

上記の手順を自動化するスクリプトを作成しました。
以下のコマンドで、元のColabコードを自動的に適応させることができます（開発中）。

## 現時点での推奨

時間の制約を考慮して、以下の方法を推奨します：

1. **最速**: `tochoku_scheduler_full.py`を開き、指示に従って元のColabコードをコピー
2. **確実**: 上記の手順に従って手動で適応
3. **代替**: 元のColabで実行し、結果をダウンロード
