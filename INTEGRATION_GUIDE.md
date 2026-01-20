# 当直スケジューラー統合ガイド

## 完了した作業 ✅

1. **データ統合**
   - `tochoku_data.py`: sheet1とsheet2を含む基本データ
   - `sheet3_sheet4_data.py`: sheet3（カテーテル表）とsheet4（累積データ）
   - `tochoku_data_complete.py`: 上記を統合したテストスクリプト

2. **テスト環境**
   - `test_simple.py`: データ読み込みの動作確認（✅ 成功）
   - 必要なパッケージインストール完了（pandas, numpy, openpyxl）

## 統合方法

### 方法1: 元のColabコードを適応させる（推奨）

以下の手順で、元のColabコードをローカル環境で実行できます：

#### ステップ1: ファイルアップロード部分を置き換え

元のColabコードの以下の部分を削除：
```python
from google.colab import files
# ... (ファイルアップロード関連のコード)
uploaded = files.upload()
```

#### ステップ2: データ読み込みコードに置き換え

削除した部分を以下のコードに置き換え：
```python
import sys
sys.path.insert(0, '/home/user/Tochoku-kun')

# データインポート
from tochoku_data import DATA as ORIG_DATA
from sheet3_sheet4_data import sheet3_data, sheet4_data

# データ統合
DATA = ORIG_DATA.copy()
DATA['sheet3'] = sheet3_data
DATA['Sheet4'] = sheet4_data

# DataFrameに変換
shift_df_raw = pd.DataFrame(DATA['sheet1'])
availability_df_raw = pd.DataFrame(DATA['sheet2'])
schedule_df_raw = pd.DataFrame(DATA['sheet3'])
sheet4_df_raw = pd.DataFrame(DATA['Sheet4'])

# 日付列の変換
shift_df_raw['Date'] = pd.to_datetime(shift_df_raw['Date']).dt.normalize().dt.tz_localize(None)
availability_df_raw['Date'] = pd.to_datetime(availability_df_raw['Date']).dt.normalize().dt.tz_localize(None)
schedule_df_raw['Date'] = pd.to_datetime(schedule_df_raw['Date']).dt.normalize().dt.tz_localize(None)

# 元のコードとの互換性
shift_df = shift_df_raw.copy()
availability_raw = availability_df_raw.copy()
schedule_raw = schedule_df_raw.copy()
sheet4_raw_out = sheet4_df_raw.copy()

# xlsオブジェクトのモック
class MockExcelFile:
    def __init__(self, data_dict):
        self.sheet_names = list(data_dict.keys())

xls = MockExcelFile(DATA)
uploaded_filename = "Tochoku.ver9_2026.01.xlsx"
```

#### ステップ3: Excel読み込み部分を調整

元のコードの以下の部分：
```python
shift_df = strip_cols(pd.read_excel(xls, sheet_name=sheet1_name))
availability_raw = strip_cols(pd.read_excel(xls, sheet_name=sheet2_name))
# ...
```

これらは既に上記のコードで`shift_df`等が定義されているので、
以下のように変更：
```python
shift_df = strip_cols(shift_df)
availability_raw = strip_cols(availability_raw)
schedule_raw = strip_cols(schedule_raw)
# ...
```

#### ステップ4: sheet4読み込み部分を調整

元のコードの：
```python
sheet4_raw_out = strip_cols(pd.read_excel(xls, sheet_name=sheet4_name))
sheet4_grid = pd.read_excel(xls, sheet_name=sheet4_name, header=None)
sheet4_data = parse_sheet4_from_grid(sheet4_grid)
```

これを：
```python
sheet4_raw_out = strip_cols(sheet4_df_raw)
# parse_sheet4は既にデータが正しい形式なのでスキップ可能
# または、そのまま使用
sheet4_data = sheet4_df_raw
```

#### ステップ5: 出力部分を調整

元のコードの最後の：
```python
files.download(output_path)
```

これを：
```python
print(f"\n✅ 出力ファイル: {output_path}")
print(f"📁 保存場所: /home/user/Tochoku-kun/{output_path}")
```

### 方法2: テンプレートを使用（より簡単）

`tochoku_scheduler_full.py`を開き、指示に従って元のColabコードをコピーペーストします。

### 方法3: 完全自動化スクリプト（作成中）

現在、元のColabコード全体を自動で適応させるスクリプトを作成中です。

## 検証

データが正しく統合されたことを確認：
```bash
python3 test_simple.py
```

期待される出力：
```
=== データ読み込みテスト ===

sheet1: 31 行 × 25 列
sheet2: 31 行 × 33 列
sheet3: 31 行 × 33 列
Sheet4: 32 行 × 多数列

✅ データ読み込み成功
```

## データ構造

### sheet1 (当直枠)
- 31日分の当直枠データ
- 列: Date, 大学平日, 大学土曜昼, ..., ふたば医療

### sheet2 (可否コード)
- 32名の医師 × 31日
- 値: 0(不可), 1(可), 2(条件付き), 3(特定列のみ)

### sheet3 (カテーテル表)
- 32名の医師 × 31日
- 値: None, A, B, C, D, E, CC

### sheet4 (累積データ)
- 32名の医師の前月までの統計
- 列: 氏名, カテ当番, 出張日, 全合計, 大学合計, ...

## トラブルシューティング

### エラー: ModuleNotFoundError: No module named 'pandas'
```bash
pip3 install pandas numpy openpyxl
```

### エラー: KeyError: 'Date'
- データの列名が正しいか確認
- `test_simple.py`でデータ構造を確認

### エラー: 日付の型が合わない
- `pd.to_datetime(...).dt.normalize().dt.tz_localize(None)`を使用

## 次のステップ

1. 元のColabコードを上記の方法で適応
2. テスト実行
3. 出力Excelファイルの確認
4. 必要に応じてパラメータ調整（NUM_PATTERNS等）

## サポート

問題が発生した場合は、以下を確認：
- `test_simple.py`が成功するか
- データファイルが正しくインポートされているか
- 元のColabコードのバージョンが最新か
