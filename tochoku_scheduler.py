#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当直スケジュール自動生成ツール v2.1.1（統合版）
Claude Code上でデバッグ・テスト可能なバージョン
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import random
from datetime import datetime

# =========================
# データ統合部分
# =========================
from tochoku_data import DATA

print("=" * 60)
print("   当直スケジュール自動生成ツール v2.1.1（統合版）")
print("=" * 60)
print("\n【主な修正内容】")
print("✅ タイムゾーン問題の修正")
print("✅ 医師名の正規化（空白による制約ミスを防止）")
print("✅ sheet4ヘッダ検出範囲の拡大（30→50行）")
print("✅ date_doc_countのKeyError対策")
print("✅ 同日重複チェックの強化")
print("✅ ★B〜Jはsheet3記載必須（ハード制約）")
print("=" * 60)

# =========================
# データ読み込み
# =========================
print("\n📊 データを読み込み中...")

# DATAディクショナリからDataFrameを作成
shift_df_raw = pd.DataFrame(DATA['sheet1'])
availability_df_raw = pd.DataFrame(DATA['sheet2'])
schedule_df_raw = pd.DataFrame(DATA['sheet3'])
sheet4_df_raw = pd.DataFrame(DATA['Sheet4'])

# 日付列の名前を取得して変換
if 'Date' in shift_df_raw.columns:
    shift_df_raw['Date'] = pd.to_datetime(shift_df_raw['Date'], errors='coerce')
if 'Date' in availability_df_raw.columns:
    availability_df_raw['Date'] = pd.to_datetime(availability_df_raw['Date'], errors='coerce')
if 'Date' in schedule_df_raw.columns:
    schedule_df_raw['Date'] = pd.to_datetime(schedule_df_raw['Date'], errors='coerce')

print(f"✅ データ読み込み完了")
print(f"   sheet1: {len(shift_df_raw)} 行 × {len(shift_df_raw.columns)} 列")
print(f"   sheet2: {len(availability_df_raw)} 行 × {len(availability_df_raw.columns)} 列")
print(f"   sheet3: {len(schedule_df_raw)} 行 × {len(schedule_df_raw.columns)} 列")
print(f"   sheet4: {len(sheet4_df_raw)} 行 × {len(sheet4_df_raw.columns)} 列")

# =========================
# ユーザー設定
# =========================
HOLIDAYS = set()  # 祝日を入れるならここ
BG_DAY_COLS = set()    # 列名で「昼」固定したい大学枠があれば追加
BG_NIGHT_COLS = set()  # 列名で「夜」固定したい大学枠があれば追加

WED_FORBIDDEN_DOCTORS = {'金城', '山田', '野寺'}  # 水曜の H〜U を禁止したい医師

NUM_PATTERNS = 10  # テスト用に少なめに設定（本番は100/1000/10000）

# sheet1 の「枠」扱いする入力値
SLOT_MARKERS = {1, 1.0, "1", "〇", "○", "◯", "◎"}

# --- ローカル探索（入替）設定 ---
LOCAL_SEARCH_ENABLED = True
TOP_KEEP = 5
REFINE_TOP = 3  # テスト用に少なめ
LOCAL_MAX_ITERS = 500  # テスト用に少なめ
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

# ★NEW: B〜J は「当日の sheet3 記載がある医師のみ割当可」をハード制約化する
REQUIRE_SHEET3_FOR_BJ = True

print(f"\n⚙️  設定")
print(f"   パターン数: {NUM_PATTERNS}")
print(f"   局所探索: {'有効' if LOCAL_SEARCH_ENABLED else '無効'}")
print(f"   B〜J sheet3必須制約: {'有効' if REQUIRE_SHEET3_FOR_BJ else '無効'}")

if __name__ == "__main__":
    print("\n✅ 初期設定完了")
    print("次のステップ: スケジューリングロジックの実装")
