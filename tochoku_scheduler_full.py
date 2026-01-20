#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当直スケジュール自動生成ツール v2.1.1（ローカル統合版）
元のColabコードをローカル環境で実行できるよう変換

使用方法:
1. このファイルに元のColabコードの「# =========================」以降の部分をコピー
2. ファイルアップロード部分は削除（下記のデータ読み込みコードで置き換え済み）
3. `python3 tochoku_scheduler_full.py` で実行

"""

import pandas as pd
import numpy as np
from collections import defaultdict
import random
from datetime import datetime
import sys

# =========================
# データ統合部分（ファイルアップロードの代わり）
# =========================
print("=" * 60)
print("   当直スケジュール自動生成ツール v2.1.1（統合版）")
print("=" * 60)
print("\n📊 データを読み込み中...")

# 完全なデータをインポート
sys.path.insert(0, '/home/user/Tochoku-kun')
from tochoku_data import DATA as ORIG_DATA
from sheet3_sheet4_data import sheet3_data, sheet4_data

# データを統合
DATA = ORIG_DATA.copy()
DATA['sheet3'] = sheet3_data
DATA['Sheet4'] = sheet4_data

# DataFrameに変換
shift_df_raw = pd.DataFrame(DATA['sheet1'])
availability_df_raw = pd.DataFrame(DATA['sheet2'])
schedule_df_raw = pd.DataFrame(DATA['sheet3'])
sheet4_df_raw = pd.DataFrame(DATA['Sheet4'])

# 日付列の変換
if 'Date' in shift_df_raw.columns:
    shift_df_raw['Date'] = pd.to_datetime(shift_df_raw['Date'], errors='coerce').dt.normalize().dt.tz_localize(None)
if 'Date' in availability_df_raw.columns:
    availability_df_raw['Date'] = pd.to_datetime(availability_df_raw['Date'], errors='coerce').dt.normalize().dt.tz_localize(None)
if 'Date' in schedule_df_raw.columns:
    schedule_df_raw['Date'] = pd.to_datetime(schedule_df_raw['Date'], errors='coerce').dt.normalize().dt.tz_localize(None)

print(f"✅ データ読み込み完了")
print(f"   sheet1: {len(shift_df_raw)} 行 × {len(shift_df_raw.columns)} 列")
print(f"   sheet2: {len(availability_df_raw)} 行 × {len(availability_df_raw.columns)} 列")
print(f"   sheet3: {len(schedule_df_raw)} 行 × {len(schedule_df_raw.columns)} 列")
print(f"   sheet4: {len(sheet4_df_raw)} 行 × {len(sheet4_df_raw.columns)} 列")

# 元のColabコードとの互換性のため、変数名を合わせる
shift_df = shift_df_raw.copy()
availability_raw = availability_df_raw.copy()
schedule_raw = schedule_df_raw.copy()
sheet4_raw_out = sheet4_df_raw.copy()

# xlsオブジェクトの代わり（元のコードで使用されている部分をエミュレート）
class MockExcelFile:
    def __init__(self, data_dict):
        self.data_dict = data_dict
        self.sheet_names = list(data_dict.keys())

xls = MockExcelFile(DATA)

# 元のファイル名（出力用）
uploaded_filename = "Tochoku.ver9_2026.01.xlsx"

print("\n" + "=" * 60)
print("🔧 以下に元のColabコードの「ユーザー設定」以降をコピーしてください")
print("   （# =========================）")
print("   （# ユーザー設定）")
print("   （# =========================）")
print("   から始まる部分")
print("=" * 60)

# =========================
# ★★★ ここから下に元のColabコードをコピー ★★★
# =========================

# 元のColabコードの「ユーザー設定」から最後までをここにコピーしてください。
# 以下は例として一部を示しています：

# =========================
# ユーザー設定
# =========================
HOLIDAYS = set()  # 祝日
BG_DAY_COLS = set()
BG_NIGHT_COLS = set()
WED_FORBIDDEN_DOCTORS = {'金城', '山田', '野寺'}
NUM_PATTERNS = 10  # テスト用に少数（本番は100/1000）
SLOT_MARKERS = {1, 1.0, "1", "〇", "○", "◯", "◎"}

# ローカル探索設定
LOCAL_SEARCH_ENABLED = True
TOP_KEEP = 5
REFINE_TOP = 3
LOCAL_MAX_ITERS = 500
LOCAL_PATIENCE = 200
LOCAL_REFRESH_EVERY = 100

# スコア重み
W_FAIR_TOTAL = 10
W_GAP = 3
W_HOSP_DUP = 1
W_UNASSIGNED = 100
W_CAP = 50
W_FLOOR = 50
W_BG_SPREAD = 3
W_HT_SPREAD = 3
W_WD_SPREAD = 2
W_WE_SPREAD = 3

REQUIRE_SHEET3_FOR_BJ = True

print("\n⚙️  設定完了")
print(f"   パターン数: {NUM_PATTERNS}")
print(f"   局所探索: {'有効' if LOCAL_SEARCH_ENABLED else '無効'}")

# ==========================================
# ★ 注意: ここから先は元のColabコードの関数定義と
#   メインロジックをすべてコピーしてください
# ==========================================

# 例: ユーティリティ関数
def strip_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    return df

def make_unique(names):
    seen = {}
    out = []
    for n in names:
        n = "" if pd.isna(n) else n
        if n not in seen:
            seen[n] = 1
            out.append(n)
        else:
            seen[n] += 1
            out.append(f"{n}_{seen[n]}")
    return out

def safe_str(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

def normalize_name(name):
    if pd.isna(name):
        return ""
    return str(name).strip().replace(" ", "").replace("　", "")

# ... 元のColabコードの残りの関数とロジックをすべてここにコピー ...

print("\n" + "=" * 60)
print("💡 ヒント: 元のColabコードをコピーして実行してください")
print("=" * 60)
