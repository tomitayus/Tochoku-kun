#!/usr/bin/env python3
# Complete data file with all sheets integrated
# This combines tochoku_data.py with sheet3_sheet4_data.py

import sys
sys.path.insert(0, '/home/user/Tochoku-kun')

# Import original data
from tochoku_data import DATA as ORIG_DATA

# Import sheet3 and sheet4 data
from sheet3_sheet4_data import sheet3_data, sheet4_data

# Create complete DATA dictionary
DATA = ORIG_DATA.copy()
DATA['sheet3'] = sheet3_data
DATA['Sheet4'] = sheet4_data

print("✅ 完全なデータファイル作成完了")
print(f"   sheet1: {len(DATA['sheet1'])} 行")
print(f"   sheet2: {len(DATA['sheet2'])} 行")
print(f"   sheet3: {len(DATA['sheet3'])} 行")
print(f"   Sheet4: {len(DATA['Sheet4'])} 行")
