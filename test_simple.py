#!/usr/bin/env python3
"""
簡易テスト: データ読み込み確認
"""
import pandas as pd
from tochoku_data import DATA

print("=== データ読み込みテスト ===")

# sheet1
df1 = pd.DataFrame(DATA['sheet1'])
print(f"\nsheet1: {len(df1)} 行 × {len(df1.columns)} 列")
print(f"先頭列: {df1.columns[0]}")
print(f"日付範囲: {df1['Date'].min()} 〜 {df1['Date'].max()}")

# sheet2
df2 = pd.DataFrame(DATA['sheet2'])
print(f"\nsheet2: {len(df2)} 行 × {len(df2.columns)} 列")
print(f"医師数: {len(df2.columns) - 1}")
print(f"医師名（先頭5名）: {list(df2.columns[1:6])}")

# sheet3
df3 = pd.DataFrame(DATA['sheet3'])
print(f"\nsheet3: {len(df3)} 行 × {len(df3.columns)} 列")

# Sheet4
df4 = pd.DataFrame(DATA['Sheet4'])
print(f"\nSheet4: {len(df4)} 行 × {len(df4.columns)} 列")

if len(df3) > 0:
    print(f"sheet3 医師数: {len(df3.columns) - 1}")
if len(df4) > 0:
    print(f"Sheet4 医師数: {len(df4)}")

print("\n✅ データ読み込み成功")
