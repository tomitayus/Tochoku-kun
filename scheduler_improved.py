#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当直スケジュール自動生成ツール v2.1.1（改良版）
基本的な制約を考慮した実用的なスケジュール生成
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import random
import sys

# データ読み込み
print("=" * 60)
print("   当直スケジュール自動生成ツール v2.1.1（改良版）")
print("=" * 60)

sys.path.insert(0, '/home/user/Tochoku-kun')
from tochoku_data import DATA as ORIG_DATA
from sheet3_sheet4_data import sheet3_data, sheet4_data

DATA = ORIG_DATA.copy()
DATA['sheet3'] = sheet3_data
DATA['Sheet4'] = sheet4_data

shift_df_orig = pd.DataFrame(DATA['sheet1'])
availability_df = pd.DataFrame(DATA['sheet2'])
schedule_df = pd.DataFrame(DATA['sheet3'])
sheet4_df = pd.DataFrame(DATA['Sheet4'])

# 日付変換
shift_df_orig['Date'] = pd.to_datetime(shift_df_orig['Date']).dt.normalize().dt.tz_localize(None)
availability_df['Date'] = pd.to_datetime(availability_df['Date']).dt.normalize().dt.tz_localize(None)
schedule_df['Date'] = pd.to_datetime(schedule_df['Date']).dt.normalize().dt.tz_localize(None)

# インデックス設定
availability_df = availability_df.set_index('Date')
schedule_df = schedule_df.set_index('Date')

# 基本情報
doctor_names = list(availability_df.columns)
hospital_cols = list(shift_df_orig.columns[1:])

print(f"\n✅ データ読み込み完了")
print(f"   医師数: {len(doctor_names)}人")
print(f"   病院数: {len(hospital_cols)}列")
print(f"   日数: {len(shift_df_orig)}日")

# 設定
WED_FORBIDDEN_DOCTORS = {'金城', '山田', '野寺'}
B_COL_IDX = 1
G_COL_IDX = 6  # Changed from J to G to avoid overlap with H~U
H_COL_IDX = 7
U_COL_IDX = 20

# ユーティリティ関数
def normalize_name(name):
    if pd.isna(name):
        return ""
    return str(name).strip().replace(" ", "").replace("　", "")

def get_avail_code(date, doctor):
    """可否コード取得 (0=不可, 1=可, 2=B〜M, 3=H〜U)"""
    try:
        value = availability_df.loc[date, doctor]
        if pd.notna(value):
            return int(value)
    except:
        pass
    return 1

def get_sched_code(date, doctor):
    """sheet3のカテーテル表取得"""
    try:
        value = schedule_df.loc[date, doctor]
        if pd.notna(value) and str(value).strip() not in ['', 'nan', 'NaT']:
            return str(value).strip()
    except:
        pass
    return None

def is_slot(val):
    """当直枠かどうか"""
    if isinstance(val, (int, float, np.integer, np.floating)):
        return val == 1
    if isinstance(val, str):
        return val.strip() in ['1', '〇', '○', '◯', '◎']
    return False

def can_assign(doctor, date, hosp_idx):
    """医師を割り当て可能か判定"""
    # 可否コードチェック
    code = get_avail_code(date, doctor)
    if code == 0:
        return False
    if code == 2 and not (B_COL_IDX <= hosp_idx <= 12):  # B〜M列のみ
        return False
    if code == 3 and not (H_COL_IDX <= hosp_idx <= U_COL_IDX):  # H〜U列のみ
        return False

    # B〜G列はsheet3記載必須（大学病院）
    if B_COL_IDX <= hosp_idx <= G_COL_IDX:
        if not get_sched_code(date, doctor):
            return False

    # H〜U列はカテ表あり不可
    if H_COL_IDX <= hosp_idx <= U_COL_IDX:
        if get_sched_code(date, doctor):
            return False

    # 水曜日H〜U禁止医師
    if date.weekday() == 2:  # 水曜日
        if H_COL_IDX <= hosp_idx <= U_COL_IDX:
            if normalize_name(doctor) in WED_FORBIDDEN_DOCTORS:
                return False

    return True

print("\n🚀 スケジュール生成開始...")

# デバッグ: データをチェック
print("\n🔍 デバッグ: データをチェック")
for row_idx in [0, 1, 2]:  # 最初の3行をチェック
    date_val = shift_df_orig.at[row_idx, 'Date']
    print(f"\n行{row_idx} ({date_val}):")
    slots_found = []
    for hosp in hospital_cols:
        val = shift_df_orig.at[row_idx, hosp]
        if is_slot(val):
            slots_found.append(hosp)
        if val != 0 and not isinstance(val, str):  # 0以外の数値
            print(f"  {hosp}: {repr(val)} (is_slot: {is_slot(val)})")
    if slots_found:
        print(f"  → 当直枠: {len(slots_found)}個 ({', '.join(slots_found[:3])}...)")
    else:
        print(f"  → 当直枠: 0個")

# スケジュール生成
result_df = shift_df_orig.copy()
for col in hospital_cols:
    result_df[col] = result_df[col].astype(object)

assigned_counts = {doc: 0 for doc in doctor_names}
daily_assignments = defaultdict(set)  # date -> set of assigned doctors

total_slots = 0
total_assigned = 0

for idx in shift_df_orig.index:
    date = shift_df_orig.at[idx, 'Date']
    if pd.isna(date):
        continue

    for hosp_idx, hosp in enumerate(hospital_cols, start=1):
        val = shift_df_orig.at[idx, hosp]

        # 既に医師名が入っている場合（固定）
        val_str = normalize_name(val) if isinstance(val, str) else ""
        if val_str in doctor_names:
            result_df.at[idx, hosp] = val_str
            assigned_counts[val_str] += 1
            daily_assignments[date].add(val_str)
            continue

        # 当直枠の場合
        if is_slot(val):
            total_slots += 1
            # 割り当て可能な医師を探す
            candidates = []
            for doc in doctor_names:
                # 同日重複チェック
                if doc in daily_assignments[date]:
                    continue
                # 制約チェック
                if can_assign(doc, date, hosp_idx):
                    candidates.append(doc)

            if candidates:
                # 割り当て回数が少ない医師を優先
                candidates.sort(key=lambda d: assigned_counts[d])
                selected = candidates[0]
                result_df.at[idx, hosp] = selected
                assigned_counts[selected] += 1
                daily_assignments[date].add(selected)
                total_assigned += 1
            else:
                result_df.at[idx, hosp] = "UNASSIGNED"

print("✅ スケジュール生成完了")

# 統計
unassigned_count = sum(1 for idx in result_df.index for hosp in hospital_cols
                       if result_df.at[idx, hosp] == "UNASSIGNED")
print(f"\n📊 結果統計:")
print(f"   検出した当直枠: {total_slots}枠")
print(f"   割り当て成功: {total_assigned}枠")
print(f"   未割当: {unassigned_count}枠")
print(f"   割当回数:")
for doc in sorted(doctor_names, key=lambda d: assigned_counts[d], reverse=True)[:10]:
    print(f"     {doc}: {assigned_counts[doc]}回")
print(f"   ...")

# サマリーシート作成
summary_data = []
for doc in doctor_names:
    summary_data.append({
        '氏名': doc,
        '割当回数': assigned_counts[doc]
    })
summary_df = pd.DataFrame(summary_data)

# 出力
output_path = "/home/user/Tochoku-kun/schedule_improved_result.xlsx"
print(f"\n📝 結果を出力中: {output_path}")

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    result_df.to_excel(writer, sheet_name="schedule", index=False)
    summary_df.to_excel(writer, sheet_name="summary", index=False)
    shift_df_orig.to_excel(writer, sheet_name="original", index=False)

print("\n" + "=" * 60)
print("   🎉 完了！")
print("=" * 60)
print(f"\n📥 出力ファイル: {output_path}")
print("\n【制約チェック実装済み】")
print("✅ 可否コード (0/1/2/3)")
print("✅ 同日重複不可")
print("✅ B〜G列はsheet3記載必須（大学病院）")
print("✅ H〜U列はカテ表あり不可（外病院）")
print("✅ 水曜H〜Uの特定医師禁止")
print("✅ 割り当て回数の公平性考慮")
print("\n【注意】")
print("これは簡易版です。完全版では以下も実装されます：")
print("- ローカル探索による最適化")
print("- より詳細なスコア評価")
print("- gap制約（4日間隔）")
print("- 詳細な診断シート")
print("=" * 60)
