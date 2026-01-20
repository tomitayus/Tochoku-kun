# @title 当直くん v2.1 (バグ修正版)
# 修正内容:
# - タイムゾーン問題の修正
# - 医師名の正規化（空白除去）
# - sheet4ヘッダ検出範囲の拡大（30→50行）
# - date_doc_countのKeyError対策（defaultdict化）
# - 同日重複チェックの強化
# - エラーハンドリングの改善

import io
import pandas as pd
import numpy as np
from collections import defaultdict
import random
import importlib.util
import os

COLAB_AVAILABLE = (
    importlib.util.find_spec("google") is not None
    and importlib.util.find_spec("google.colab") is not None
)
if COLAB_AVAILABLE:
    from google.colab import files

# =========================
# ユーザー設定
# =========================
HOLIDAYS = set()  # 祝日を入れるならここ（例: {pd.Timestamp("2026-01-01"), ...}）
BG_DAY_COLS = set()    # 列名で「昼」固定したい大学枠があれば追加
BG_NIGHT_COLS = set()  # 列名で「夜」固定したい大学枠があれば追加

WED_FORBIDDEN_DOCTORS = {'金城', '山田', '野寺'}  # 水曜の H〜U を禁止したい医師

NUM_PATTERNS = int(os.getenv("NUM_PATTERNS", "10000"))  # 100/1000/10000 など

# sheet1 の「枠」扱いする入力値（1以外の記号も許容したい場合）
SLOT_MARKERS = {1, 1.0, "1", "〇", "○", "◯", "◎"}

# --- ローカル探索（入替）設定 ---
LOCAL_SEARCH_ENABLED = True
TOP_KEEP = 15                 # greedyで残す候補数（この中に最良が残る確率↑）
REFINE_TOP = 15               # ローカル探索をかける候補数（<= TOP_KEEP）
LOCAL_MAX_ITERS = 3000        # 1候補あたりの入替試行回数
LOCAL_PATIENCE = 1200         # 改善が出ない試行がこの回数続いたら打ち切り
LOCAL_REFRESH_EVERY = 200     # 問題医師（gap/重複）を再抽出する間隔

# スコア重み（必要なら調整）
W_FAIR_TOTAL = 10          # 全合計（active内 max-min-1）
W_GAP = 3                  # gap(4日未満)
W_HOSP_DUP = 1             # 同一病院複数回
W_UNASSIGNED = 100         # 未割当
W_CAP = 50                 # cap超え
W_BG_SPREAD = 3            # 大学合計（累計）ばらつき
W_HT_SPREAD = 3            # 外病院合計（累計）ばらつき
W_WD_SPREAD = 2            # 平日（累計）ばらつき
W_WE_SPREAD = 3            # 休日合計（累計）ばらつき
W_BK_LY_BALANCE = 2        # B-K/L-Y の比率バランス（なるべく1:1）

# =========================
# ユーティリティ
# =========================
def strip_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    return df

def make_unique(names):
    """重複列名を _2, _3 ... でユニーク化"""
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

# 🔧 FIX: 医師名の正規化関数を追加
def normalize_name(name):
    """医師名を正規化（全角/半角スペース除去）"""
    if pd.isna(name):
        return ""
    return str(name).strip().replace(" ", "").replace("　", "")

def find_sheet_name(xls: pd.ExcelFile, target: str):
    """sheet名の大小・表記ゆれに耐える"""
    if target in xls.sheet_names:
        return target
    low_map = {s.lower(): s for s in xls.sheet_names}
    if target.lower() in low_map:
        return low_map[target.lower()]
    for s in xls.sheet_names:
        if s.strip().lower() == target.strip().lower():
            return s
    return None

def is_slot_value(v) -> bool:
    if isinstance(v, str):
        return v.strip() in SLOT_MARKERS
    if isinstance(v, (int, float, np.integer, np.floating)):
        return float(v) == 1.0
    return False

# =========================
# sheet4 読み込み（ヘッダ行自動検出＋重複耐性）
# 🔧 FIX: 検索範囲を30→50行に拡大
# =========================
def parse_sheet4_from_grid(grid: pd.DataFrame) -> pd.DataFrame:
    g = grid.copy()
    g = g.dropna(how="all").reset_index(drop=True)

    if len(g) == 0:
        raise ValueError("sheet4 が空です")

    # ヘッダ行を探す（'氏名' がある行）
    header_row_idx = None
    search_limit = min(50, len(g))  # 🔧 FIX: 30→50に拡大
    for i in range(search_limit):
        row = g.iloc[i].astype(str).str.strip()
        if (row == "氏名").any():
            header_row_idx = i
            break
    if header_row_idx is None:
        raise ValueError(f"sheet4 のヘッダ行に '氏名' 列が見つかりません（先頭{search_limit}行を検索）")

    headers = [safe_str(x) for x in g.iloc[header_row_idx].tolist()]
    headers = [h if (h != "" and h.lower() != "nan") else f"Unnamed_{j}" for j, h in enumerate(headers)]
    headers = make_unique(headers)

    data = g.iloc[header_row_idx + 1:].reset_index(drop=True)
    data.columns = headers

    if "氏名" not in data.columns:
        raise ValueError("sheet4 のヘッダ行に '氏名' 列が見つかりません（sheet4の形式を確認してください）")

    # 氏名の空行削除
    data["氏名"] = data["氏名"].astype(str).str.strip()
    data = data[(data["氏名"].notna()) & (data["氏名"] != "") & (data["氏名"].str.lower() != "nan")].reset_index(drop=True)

    # 数値化（氏名以外）
    for col in data.columns:
        if col == "氏名":
            continue
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)

    return data

# =========================
# 入力ファイルのアップロード
# =========================
print("="*60)
print("   当直スケジュール自動生成ツール v2.1 (バグ修正版)")
print("="*60)
print("\n【主な修正内容】")
print("✅ タイムゾーン問題の修正")
print("✅ 医師名の正規化（空白による制約ミスを防止）")
print("✅ sheet4ヘッダ検出範囲の拡大（30→50行）")
print("✅ date_doc_countのKeyError対策")
print("✅ 同日重複チェックの強化")
print("="*60)
print("\n【使い方】")
print("1. 下のファイル選択ダイアログでExcelファイルを選択")
print("2. 処理が自動で開始されます（5-10分かかります）")
print("3. 完了したらダウンロードリンクが表示されます")
print("="*60)
print("\nsheet1〜sheet4（またはSheet4）が入った当直Excelファイルを選択してください")

if COLAB_AVAILABLE:
    uploaded = files.upload()
    uploaded_filename = list(uploaded.keys())[0]

    try:
        xls = pd.ExcelFile(io.BytesIO(uploaded[uploaded_filename]))
    except Exception as e:
        raise ValueError(f"❌ Excelファイルの読み込みに失敗しました: {e}")

    sheet1_name = find_sheet_name(xls, "sheet1")
    sheet2_name = find_sheet_name(xls, "sheet2")
    sheet3_name = find_sheet_name(xls, "sheet3")
    sheet4_name = find_sheet_name(xls, "sheet4") or find_sheet_name(xls, "Sheet4")

    missing = [k for k, v in [("sheet1", sheet1_name), ("sheet2", sheet2_name), ("sheet3", sheet3_name), ("sheet4", sheet4_name)] if v is None]
    if missing:
        raise ValueError(f"❌ 必要なシートが見つかりません: {missing}\n実際のシート名: {xls.sheet_names}")

    # --------- Excel 読み込み ---------
    shift_df = strip_cols(pd.read_excel(xls, sheet_name=sheet1_name))
    availability_raw = strip_cols(pd.read_excel(xls, sheet_name=sheet2_name))
    schedule_raw = strip_cols(pd.read_excel(xls, sheet_name=sheet3_name))

    shift_df.columns = make_unique(list(shift_df.columns))
    availability_raw.columns = make_unique(list(availability_raw.columns))
    schedule_raw.columns = make_unique(list(schedule_raw.columns))

    # sheet4 は「出力用」と「解析用（header=None）」を分ける
    sheet4_raw_out = strip_cols(pd.read_excel(xls, sheet_name=sheet4_name))
    sheet4_raw_out.columns = make_unique(list(sheet4_raw_out.columns))

    sheet4_grid = pd.read_excel(xls, sheet_name=sheet4_name, header=None)
    sheet4_data = parse_sheet4_from_grid(sheet4_grid)
else:
    from tochoku_data_complete import DATA as LOCAL_DATA

    uploaded_filename = "Tochoku.local.xlsx"
    shift_df = strip_cols(pd.DataFrame(LOCAL_DATA["sheet1"]))
    availability_raw = strip_cols(pd.DataFrame(LOCAL_DATA["sheet2"]))
    schedule_raw = strip_cols(pd.DataFrame(LOCAL_DATA["sheet3"]))

    shift_df.columns = make_unique(list(shift_df.columns))
    availability_raw.columns = make_unique(list(availability_raw.columns))
    schedule_raw.columns = make_unique(list(schedule_raw.columns))

    sheet4_raw_out = strip_cols(pd.DataFrame(LOCAL_DATA["Sheet4"]))
    sheet4_raw_out.columns = make_unique(list(sheet4_raw_out.columns))

    sheet4_data = sheet4_raw_out.copy()
    if "氏名" not in sheet4_data.columns:
        raise ValueError("❌ Sheet4 の '氏名' 列が見つかりません（ローカルデータを確認してください）")
    sheet4_data["氏名"] = sheet4_data["氏名"].astype(str).str.strip()
    for col in sheet4_data.columns:
        if col == "氏名":
            continue
        sheet4_data[col] = pd.to_numeric(sheet4_data[col], errors="coerce").fillna(0)

# =========================
# 日付列の整形
# 🔧 FIX: タイムゾーン問題の修正
# =========================
date_col_shift = shift_df.columns[0]
shift_df[date_col_shift] = pd.to_datetime(shift_df[date_col_shift], errors="coerce").dt.normalize().dt.tz_localize(None)  # 🔧 FIX
if shift_df[date_col_shift].isna().all():
    raise ValueError("❌ sheet1 の先頭列が日付として解釈できません（列の形式を確認してください）")

date_col_avail = availability_raw.columns[0]
availability_raw[date_col_avail] = pd.to_datetime(availability_raw[date_col_avail], errors="coerce").dt.normalize().dt.tz_localize(None)  # 🔧 FIX
availability_df = availability_raw.set_index(date_col_avail)

date_col_sched = schedule_raw.columns[0]
schedule_raw[date_col_sched] = pd.to_datetime(schedule_raw[date_col_sched], errors="coerce").dt.normalize().dt.tz_localize(None)  # 🔧 FIX
schedule_df = schedule_raw.set_index(date_col_sched)

# 🔧 FIX: 祝日もタイムゾーン正規化
HOLIDAYS = {pd.to_datetime(d).normalize().tz_localize(None) for d in HOLIDAYS}

def is_holiday(date):
    return pd.to_datetime(date).normalize().tz_localize(None) in HOLIDAYS

# =========================
# 基本情報
# 🔧 FIX: 医師名を正規化
# =========================
doctor_names = [normalize_name(x) for x in list(availability_raw.columns[1:])]  # 🔧 FIX
doctor_col_index = {doc: idx for idx, doc in enumerate(doctor_names)}

# 🔧 FIX: 禁止医師名も正規化
WED_FORBIDDEN_DOCTORS = {normalize_name(d) for d in WED_FORBIDDEN_DOCTORS}  # 🔧 FIX

hospital_cols = list(shift_df.columns[1:])
n_cols = len(shift_df.columns)

# 列インデックス（テンプレ依存：B〜U を想定）
B_COL_INDEX = 1
C_COL_INDEX = 2
D_COL_INDEX = min(3, n_cols - 1)
E_COL_INDEX = min(4, n_cols - 1)
F_COL_INDEX = min(5, n_cols - 1)
G_COL_INDEX = min(6, n_cols - 1)
H_COL_INDEX = min(7, n_cols - 1)
M_COL_INDEX = min(12, n_cols - 1)
U_COL_INDEX = min(20, n_cols - 1)

B_K_START_INDEX = B_COL_INDEX
B_K_END_INDEX = min(10, n_cols - 1)
L_Y_START_INDEX = min(11, n_cols - 1)
L_Y_END_INDEX = n_cols - 1

print(f"✅ Excelファイル読み込み完了")
print(f"   医師数: {len(doctor_names)}人")
print(f"   病院列数: {len(hospital_cols)}列")
print(f"   対象日数: {len(shift_df)}日")

# =========================
# sheet2 可否コード
# =========================
fallback_avail_codes = {}
for doc in doctor_names:
    col_vals = availability_raw[doc]
    first_val = None
    for v in col_vals:
        if pd.notna(v):
            first_val = v
            break
    if first_val is None:
        fallback_avail_codes[doc] = 1
    else:
        try:
            c = int(first_val)
        except Exception:
            c = 1
        if c not in (0, 1, 2, 3):
            c = 1
        fallback_avail_codes[doc] = c

def get_avail_code(date, doctor):
    code = None
    if isinstance(availability_df.index, pd.DatetimeIndex):
        try:
            value = availability_df.at[pd.to_datetime(date).normalize().tz_localize(None), doctor]  # 🔧 FIX
            if isinstance(value, pd.Series):
                value = value.iloc[0]
            if pd.notna(value):
                code = int(value)
        except Exception:
            pass
    if code is None:
        code = fallback_avail_codes.get(doctor, 1)
    if code not in (0, 1, 2, 3):
        code = 1
    return code

def get_sched_code(date, doctor):
    if doctor not in schedule_df.columns:
        return None
    try:
        value = schedule_df.at[pd.to_datetime(date).normalize().tz_localize(None), doctor]  # 🔧 FIX
        if isinstance(value, pd.Series):
            value = value.iloc[0]
    except Exception:
        return None
    if pd.isna(value):
        return None
    return str(value).strip()

# sheet2 と sheet3 の医師列がズレていないか（ズレてても動くが、制約が弱くなる）
sched_doctors = [normalize_name(x) for x in list(schedule_raw.columns[1:])]  # 🔧 FIX
if doctor_names != sched_doctors:
    print("⚠️ WARNING: sheet2(可否) と sheet3(カテ表) の医師列が一致していません。")
    only2 = [d for d in doctor_names if d not in sched_doctors]
    only3 = [d for d in sched_doctors if d not in doctor_names]
    if only2:
        print(f"   sheet2 only (先頭10): {only2[:10]}")
    if only3:
        print(f"   sheet3 only (先頭10): {only3[:10]}")
    print("   ※H〜U の『カテ表あり不可』制約が一部の医師で効かない可能性があります。")

# =========================
# sheet4 前月まで累積
# =========================
name_to_row = {row["氏名"]: row for _, row in sheet4_data.iterrows()}
prev_names = list(sheet4_data["氏名"])

def match_prev_name(doc):
    if doc in name_to_row:
        return doc
    ms = [p for p in prev_names if str(p).startswith(doc) or doc.startswith(str(p))]
    return ms[0] if len(ms) == 1 else None

name_match = {doc: match_prev_name(doc) for doc in doctor_names}
unmatched = [d for d in doctor_names if name_match.get(d) is None]
if unmatched:
    print(f"⚠️ WARNING: sheet4(累積)で名前が一致しない医師がいます（累積が0扱いになります）: {unmatched}")

def prev_get(doc, colname):
    pname = name_match.get(doc)
    if pname and pname in name_to_row:
        row = name_to_row[pname]
        v = row.get(colname, 0)
        try:
            return float(v or 0)
        except Exception:
            return 0.0
    return 0.0

prev_total   = {d: prev_get(d, "全合計")   for d in doctor_names}
prev_bg      = {d: prev_get(d, "大学合計") for d in doctor_names}
prev_ht      = {d: prev_get(d, "外病院合計") for d in doctor_names}
prev_weekday = {d: prev_get(d, "平日")     for d in doctor_names}
prev_weekend = {d: prev_get(d, "休日合計") for d in doctor_names}

# =========================
# 全枠数カウント + slots_by_date 前計算
# =========================
slots_by_date = defaultdict(lambda: {"preassigned": [], "free": []})
preassigned_count = {d: 0 for d in doctor_names}
total_slots = 0

for ridx in shift_df.index:
    date = shift_df.at[ridx, date_col_shift]
    if pd.isna(date):
        continue
    date = pd.to_datetime(date).normalize().tz_localize(None)  # 🔧 FIX

    for hosp in hospital_cols:
        val = shift_df.at[ridx, hosp]

        # 固定割当（セルに医師名が入っている）
        val_str = normalize_name(val) if isinstance(val, str) else ""  # 🔧 FIX
        if val_str in doctor_names:
            doc = val_str
            slots_by_date[date]["preassigned"].append((ridx, hosp, doc))
            preassigned_count[doc] += 1
            total_slots += 1
            continue

        # 自動枠（1/〇など）
        if is_slot_value(val):
            slots_by_date[date]["free"].append((ridx, hosp))
            total_slots += 1

if len(doctor_names) == 0:
    raise ValueError("❌ sheet2 に医師名がありません")

all_dates = sorted(slots_by_date.keys())
all_shift_dates = sorted(pd.to_datetime(shift_df[date_col_shift].dropna()).dt.normalize().dt.tz_localize(None).unique())  # 🔧 FIX

# =========================
# cap設計：n回ベース＋余りは「下の方（後ろ）」の医師に+1
# =========================
def is_always_unavailable(doc):
    if preassigned_count.get(doc, 0) > 0:
        return False
    return all(get_avail_code(d, doc) == 0 for d in all_shift_dates)

inactive_doctors = [d for d in doctor_names if is_always_unavailable(d)]
active_doctors = [d for d in doctor_names if d not in inactive_doctors]
if len(active_doctors) == 0:
    raise ValueError("❌ 当月に割り当て可能な医師がいません")

BASE_TARGET = total_slots // len(active_doctors)
EXTRA_SLOTS = total_slots - BASE_TARGET * len(active_doctors)

active_sorted_bottom = sorted(active_doctors, key=lambda d: doctor_col_index[d])
EXTRA_ALLOWED = set(active_sorted_bottom[-EXTRA_SLOTS:]) if EXTRA_SLOTS > 0 else set()

TARGET_CAP = {d: 0 for d in doctor_names}
for d in active_doctors:
    TARGET_CAP[d] = BASE_TARGET + (1 if d in EXTRA_ALLOWED else 0)
for d in doctor_names:
    if preassigned_count.get(d, 0) > TARGET_CAP.get(d, 0):
        TARGET_CAP[d] = preassigned_count[d]

floor_shifts = BASE_TARGET

print(f"\n✅ 割当設計完了")
print(f"   全枠数: {total_slots}")
print(f"   active医師: {len(active_doctors)}人")
print(f"   inactive医師: {len(inactive_doctors)}人")
print(f"   基本割当数: {BASE_TARGET}回")
print(f"   余り枠: {EXTRA_SLOTS}枠（下の方の医師に+1回）")

# =========================
# B-K / L-Y 比率バランス（sheet3で「3」記載の医師は除外）
# =========================
def has_sheet3_code_3(doc):
    if doc not in schedule_df.columns:
        return False
    values = schedule_df[doc].dropna()
    return any(str(v).strip() == "3" for v in values)

RATIO_EXEMPT_DOCTORS = {doc for doc in doctor_names if has_sheet3_code_3(doc)}
if RATIO_EXEMPT_DOCTORS:
    print(f"   比率バランス除外（sheet3に3あり）: {sorted(RATIO_EXEMPT_DOCTORS)}")

# =========================
# 大学(B〜G)の昼夜判定 & 7分類
# =========================
def is_bg_day_shift(hosp_name, col_idx):
    if hosp_name in BG_DAY_COLS:
        return True
    if hosp_name in BG_NIGHT_COLS:
        return False
    # デフォルト：B,C,E,F=昼 / D,G=夜
    if col_idx in (B_COL_INDEX, C_COL_INDEX, E_COL_INDEX, F_COL_INDEX):
        return True
    if col_idx in (D_COL_INDEX, G_COL_INDEX):
        return False
    mid = (B_COL_INDEX + G_COL_INDEX) // 2
    return col_idx <= mid

def is_bk_slot(col_idx):
    return B_K_START_INDEX <= col_idx <= B_K_END_INDEX

def is_ly_slot(col_idx):
    return L_Y_START_INDEX <= col_idx <= L_Y_END_INDEX

def classify_bg_category(date, hosp_name):
    idx = shift_df.columns.get_loc(hosp_name)
    is_day = is_bg_day_shift(hosp_name, idx)
    dow = pd.to_datetime(date).weekday()
    holi = is_holiday(date)

    weekday = dow < 5
    # 平日かつ C,D,F,G は祝日扱い
    if weekday and idx in (C_COL_INDEX, D_COL_INDEX, F_COL_INDEX, G_COL_INDEX):
        holi = True

    if holi and weekday:
        base = "祝日"
    elif dow == 5:
        base = "土曜"
    elif dow == 6:
        base = "日曜"
    else:
        return "平日"

    return base + ("昼" if is_day else "夜")

# =========================
# 1枠の医師選択（greedy）
# =========================
def choose_doctor_for_slot(
    date,
    hospital_name,
    assigned_count,
    assigned_dates,
    assigned_bg,
    assigned_ht,
    assigned_weekday,
    assigned_weekend,
    assigned_be,
    assigned_fg,
    assigned_bk,
    assigned_ly,
    assigned_hosp_count,
):
    idx = shift_df.columns.get_loc(hospital_name)
    is_BE = B_COL_INDEX <= idx <= E_COL_INDEX
    is_BG = B_COL_INDEX <= idx <= G_COL_INDEX
    is_HU = H_COL_INDEX <= idx <= U_COL_INDEX
    is_BK = is_bk_slot(idx)
    is_LY = is_ly_slot(idx)
    dow = pd.to_datetime(date).weekday()
    weekday = dow < 5

    def collect_candidates(
        allow_same_day=False,
        relax_availability=False,
        relax_schedule=False,
        relax_wed=False,
    ):
        candidates = []
        for doc in doctor_names:
            if not allow_same_day and date in assigned_dates[doc]:
                continue

            if not relax_availability:
                code = get_avail_code(date, doc)
                if code == 0:
                    continue
                # 2 -> B〜M列以外ダメ
                if code == 2 and not (B_COL_INDEX <= idx <= M_COL_INDEX):
                    continue
                # 3 -> H〜U列以外ダメ
                if code == 3 and not (H_COL_INDEX <= idx <= U_COL_INDEX):
                    continue

            if not relax_schedule and H_COL_INDEX <= idx <= U_COL_INDEX:
                if get_sched_code(date, doc):
                    continue

            if not relax_wed and dow == 2 and H_COL_INDEX <= idx <= U_COL_INDEX:
                if doc in WED_FORBIDDEN_DOCTORS:
                    continue

            if assigned_count[doc] >= TARGET_CAP.get(doc, 0):
                continue

            candidates.append(doc)
        return candidates

    candidates = collect_candidates()
    if not candidates:
        candidates = collect_candidates(allow_same_day=True)
    if not candidates:
        candidates = collect_candidates(allow_same_day=True, relax_availability=True)
    if not candidates:
        candidates = collect_candidates(
            allow_same_day=True,
            relax_availability=True,
            relax_schedule=True,
            relax_wed=True,
        )

    if not candidates:
        return None

    any_under_floor = any(assigned_count[d] < floor_shifts for d in active_doctors)
    if any_under_floor:
        under_floor = [d for d in candidates if assigned_count[d] < floor_shifts]
        if under_floor:
            candidates = under_floor

    # gap
    gaps = {}
    for d in candidates:
        if not assigned_dates[d]:
            gaps[d] = 999
        else:
            gaps[d] = min(abs((pd.to_datetime(date) - x).days) for x in assigned_dates[d])

    # 優先順位: 7,4,5,比率(B-K/L-Y),2,3,6,8,1(>=4),10

    # 7 全体（前月+今月）
    metric_total = {d: prev_total[d] + assigned_count[d] for d in candidates}
    min_total = min(metric_total.values())
    candidates = [d for d in candidates if metric_total[d] == min_total]

    # 4 大学/外病院偏り（前月+今月）
    if is_BG:
        metric_bg = {d: prev_bg[d] + assigned_bg[d] for d in candidates}
        mb = min(metric_bg.values())
        candidates = [d for d in candidates if metric_bg[d] == mb]
    elif is_HU:
        metric_ht = {d: prev_ht[d] + assigned_ht[d] for d in candidates}
        mh = min(metric_ht.values())
        candidates = [d for d in candidates if metric_ht[d] == mh]

    # 5 B〜E / F〜G
    if is_BG:
        if is_BE:
            mbe = min(assigned_be[d] for d in candidates)
            candidates = [d for d in candidates if assigned_be[d] == mbe]
        else:
            mfg = min(assigned_fg[d] for d in candidates)
            candidates = [d for d in candidates if assigned_fg[d] == mfg]

    # B-K / L-Y の比率バランス（除外医師以外）
    if (is_BK or is_LY) and candidates:
        def imbalance_score(doc):
            if doc in RATIO_EXEMPT_DOCTORS:
                return 0
            bk = assigned_bk[doc] + (1 if is_BK else 0)
            ly = assigned_ly[doc] + (1 if is_LY else 0)
            return abs(bk - ly)

        min_imbalance = min(imbalance_score(d) for d in candidates)
        candidates = [d for d in candidates if imbalance_score(d) == min_imbalance]

    # 2 同一病院0回優先
    no_dup = [d for d in candidates if assigned_hosp_count[d].get(hospital_name, 0) == 0]
    if no_dup:
        candidates = no_dup

    # 3 B〜G はカテ表あり優先（ソフト優先）
    if is_BG:
        with_sched = [d for d in candidates if get_sched_code(date, d)]
        if with_sched:
            candidates = with_sched

    # 6 平日/休日偏り（前月+今月）
    holi_flag = (
        is_holiday(date)
        or dow >= 5
        or (weekday and idx in (C_COL_INDEX, D_COL_INDEX, F_COL_INDEX, G_COL_INDEX))
    )
    if holi_flag:
        metric_we = {d: prev_weekend[d] + assigned_weekend[d] for d in candidates}
        mwe = min(metric_we.values())
        candidates = [d for d in candidates if metric_we[d] == mwe]
    else:
        metric_wd = {d: prev_weekday[d] + assigned_weekday[d] for d in candidates}
        mwd = min(metric_wd.values())
        candidates = [d for d in candidates if metric_wd[d] == mwd]

    # 8 floor未満優先
    under_floor = [d for d in candidates if assigned_count[d] < floor_shifts]
    if under_floor:
        candidates = under_floor

    # 1 gap>=4
    gap_ok = [d for d in candidates if gaps[d] >= 4]
    if gap_ok:
        candidates = gap_ok

    # 10 同点なら右側
    return max(candidates, key=lambda d: doctor_col_index[d])

# =========================
# 1ヶ月分生成（greedy）
# =========================
def build_schedule_pattern(seed=0):
    random.seed(seed)

    df = shift_df.copy()
    for col in hospital_cols:
        df[col] = df[col].astype(object)

    assigned_count = {d: 0 for d in doctor_names}
    assigned_dates = {d: set() for d in doctor_names}

    assigned_bg = {d: 0 for d in doctor_names}
    assigned_ht = {d: 0 for d in doctor_names}
    assigned_weekday = {d: 0 for d in doctor_names}
    assigned_weekend = {d: 0 for d in doctor_names}
    assigned_be = {d: 0 for d in doctor_names}
    assigned_fg = {d: 0 for d in doctor_names}
    assigned_bk = {d: 0 for d in doctor_names}
    assigned_ly = {d: 0 for d in doctor_names}
    assigned_hosp_count = {d: defaultdict(int) for d in doctor_names}
    bg_cat = {d: defaultdict(int) for d in doctor_names}

    # 固定当直
    for date in all_dates:
        for ridx, hosp, doc in slots_by_date[date]["preassigned"]:
            df.at[ridx, hosp] = doc
            assigned_count[doc] += 1
            assigned_dates[doc].add(date)
            assigned_hosp_count[doc][hosp] += 1

            hidx = shift_df.columns.get_loc(hosp)
            if B_COL_INDEX <= hidx <= G_COL_INDEX:
                assigned_bg[doc] += 1
                if B_COL_INDEX <= hidx <= E_COL_INDEX:
                    assigned_be[doc] += 1
                elif F_COL_INDEX <= hidx <= G_COL_INDEX:
                    assigned_fg[doc] += 1
                bg_cat[doc][classify_bg_category(date, hosp)] += 1
            elif H_COL_INDEX <= hidx <= U_COL_INDEX:
                assigned_ht[doc] += 1

            dow = date.weekday()
            weekday = dow < 5
            holi_flag = (
                is_holiday(date)
                or dow >= 5
                or (weekday and hidx in (C_COL_INDEX, D_COL_INDEX, F_COL_INDEX, G_COL_INDEX))
            )
            if holi_flag:
                assigned_weekend[doc] += 1
            else:
                assigned_weekday[doc] += 1

            if is_bk_slot(hidx):
                assigned_bk[doc] += 1
            elif is_ly_slot(hidx):
                assigned_ly[doc] += 1

    # 自動割当
    for date in all_dates:
        free_slots = slots_by_date[date]["free"].copy()
        random.shuffle(free_slots)

        for ridx, hosp in free_slots:
            chosen = choose_doctor_for_slot(
                date=date,
                hospital_name=hosp,
                assigned_count=assigned_count,
                assigned_dates=assigned_dates,
                assigned_bg=assigned_bg,
                assigned_ht=assigned_ht,
                assigned_weekday=assigned_weekday,
                assigned_weekend=assigned_weekend,
                assigned_be=assigned_be,
                assigned_fg=assigned_fg,
                assigned_bk=assigned_bk,
                assigned_ly=assigned_ly,
                assigned_hosp_count=assigned_hosp_count,
            )
            if chosen is None:
                remaining = [d for d in doctor_names if assigned_count[d] < TARGET_CAP.get(d, 0)]
                if remaining:
                    fallback_doc = min(remaining, key=lambda d: (assigned_count[d], doctor_col_index[d]))
                else:
                    fallback_doc = min(doctor_names, key=lambda d: (assigned_count[d], doctor_col_index[d]))
                df.at[ridx, hosp] = fallback_doc
                chosen = fallback_doc
            else:
                df.at[ridx, hosp] = chosen

            assigned_count[chosen] += 1
            assigned_dates[chosen].add(date)
            assigned_hosp_count[chosen][hosp] += 1

            hidx = shift_df.columns.get_loc(hosp)
            if B_COL_INDEX <= hidx <= G_COL_INDEX:
                assigned_bg[chosen] += 1
                if B_COL_INDEX <= hidx <= E_COL_INDEX:
                    assigned_be[chosen] += 1
                elif F_COL_INDEX <= hidx <= G_COL_INDEX:
                    assigned_fg[chosen] += 1
                bg_cat[chosen][classify_bg_category(date, hosp)] += 1
            elif H_COL_INDEX <= hidx <= U_COL_INDEX:
                assigned_ht[chosen] += 1

            dow = date.weekday()
            weekday = dow < 5
            holi_flag = (
                is_holiday(date)
                or dow >= 5
                or (weekday and hidx in (C_COL_INDEX, D_COL_INDEX, F_COL_INDEX, G_COL_INDEX))
            )
            if holi_flag:
                assigned_weekend[chosen] += 1
            else:
                assigned_weekday[chosen] += 1

            if is_bk_slot(hidx):
                assigned_bk[chosen] += 1
            elif is_ly_slot(hidx):
                assigned_ly[chosen] += 1

    return (
        df,
        assigned_count,
        assigned_bg,
        assigned_ht,
        assigned_weekday,
        assigned_weekend,
        assigned_bk,
        assigned_ly,
        bg_cat,
    )

# =========================
# slot_meta / movable_positions（ローカル探索用）
# =========================
slot_meta = {}  # (ridx,hosp) -> (date, fixed)
movable_positions = []  # (ridx,hosp,date)

for date in all_dates:
    for ridx, hosp, doc in slots_by_date[date]["preassigned"]:
        slot_meta[(ridx, hosp)] = (date, True)
    for ridx, hosp in slots_by_date[date]["free"]:
        slot_meta[(ridx, hosp)] = (date, False)
        movable_positions.append((ridx, hosp, date))

# =========================
# パターン統計再計算（pattern_df から）
# =========================
def recompute_stats(pattern_df):
    counts = {d: 0 for d in doctor_names}
    bg_counts = {d: 0 for d in doctor_names}
    ht_counts = {d: 0 for d in doctor_names}
    wd_counts = {d: 0 for d in doctor_names}
    we_counts = {d: 0 for d in doctor_names}
    bk_counts = {d: 0 for d in doctor_names}
    ly_counts = {d: 0 for d in doctor_names}
    bg_cat = {d: defaultdict(int) for d in doctor_names}
    assigned_hosp_count = {d: defaultdict(int) for d in doctor_names}
    doc_assignments = {d: [] for d in doctor_names}  # (date,hosp)
    unassigned = []  # (date,hosp,ridx)

    for (ridx, hosp), (date, fixed) in slot_meta.items():
        val = pattern_df.at[ridx, hosp]
        if not isinstance(val, str):
            continue
        v = normalize_name(val)  # 🔧 FIX

        if v == "UNASSIGNED":
            unassigned.append((date, hosp, ridx))
            continue
        if v not in doctor_names:
            continue

        doc = v
        counts[doc] += 1
        assigned_hosp_count[doc][hosp] += 1
        doc_assignments[doc].append((date, hosp))

        hidx = shift_df.columns.get_loc(hosp)
        if B_COL_INDEX <= hidx <= G_COL_INDEX:
            bg_counts[doc] += 1
            bg_cat[doc][classify_bg_category(date, hosp)] += 1
        elif H_COL_INDEX <= hidx <= U_COL_INDEX:
            ht_counts[doc] += 1

        dow = date.weekday()
        weekday = dow < 5
        holi_flag = (
            is_holiday(date)
            or dow >= 5
            or (weekday and hidx in (C_COL_INDEX, D_COL_INDEX, F_COL_INDEX, G_COL_INDEX))
        )
        if holi_flag:
            we_counts[doc] += 1
        else:
            wd_counts[doc] += 1

        if is_bk_slot(hidx):
            bk_counts[doc] += 1
        elif is_ly_slot(hidx):
            ly_counts[doc] += 1

    return (
        counts,
        bg_counts,
        ht_counts,
        wd_counts,
        we_counts,
        bk_counts,
        ly_counts,
        bg_cat,
        assigned_hosp_count,
        doc_assignments,
        unassigned,
    )

# =========================
# スコア評価（raw_scoreも保持して 0 で潰れないように）
# =========================
def evaluate_schedule_with_raw(
    pattern_df,
    assigned_count,
    assigned_bg,
    assigned_ht,
    assigned_weekday,
    assigned_weekend,
    assigned_bk,
    assigned_ly,
):
    # UNASSIGNED
    unassigned_slots = 0
    for ridx in pattern_df.index:
        for hosp in hospital_cols:
            v = pattern_df.at[ridx, hosp]
            if isinstance(v, str) and normalize_name(v) == "UNASSIGNED":  # 🔧 FIX
                unassigned_slots += 1

    # cap違反
    cap_violations = 0
    for doc in doctor_names:
        cap = TARGET_CAP.get(doc, 0)
        if assigned_count.get(doc, 0) > cap:
            cap_violations += (assigned_count[doc] - cap)

    # 全合計公平性（activeのみ）
    active_counts = [assigned_count.get(d, 0) for d in active_doctors]
    max_c = max(active_counts) if active_counts else 0
    min_c = min(active_counts) if active_counts else 0
    diff_total = max_c - min_c
    fairness_penalty = max(0, diff_total - 1)

    # gap(4日未満) と 同一病院重複
    dates_by_doc = defaultdict(list)
    hosp_counts_by_doc = {doc: defaultdict(int) for doc in doctor_names}

    for ridx in pattern_df.index:
        date = pattern_df.at[ridx, date_col_shift]
        if pd.isna(date):
            continue
        date = pd.to_datetime(date).normalize().tz_localize(None)  # 🔧 FIX
        for hosp in hospital_cols:
            val = pattern_df.at[ridx, hosp]
            val_norm = normalize_name(val) if isinstance(val, str) else ""  # 🔧 FIX
            if val_norm in doctor_names:
                dates_by_doc[val_norm].append(date)
                hosp_counts_by_doc[val_norm][hosp] += 1

    gap_violations = 0
    for doc, dlist in dates_by_doc.items():
        dlist = sorted(dlist)
        for i in range(1, len(dlist)):
            if (dlist[i] - dlist[i - 1]).days < 4:
                gap_violations += 1

    hosp_dup_violations = 0
    for doc, hdict in hosp_counts_by_doc.items():
        for _, c in hdict.items():
            if c > 1:
                hosp_dup_violations += (c - 1)

    # 偏り（累計：前月+今月）の spread
    bg_vals = [prev_bg[d] + assigned_bg.get(d, 0) for d in active_doctors]
    ht_vals = [prev_ht[d] + assigned_ht.get(d, 0) for d in active_doctors]
    wd_vals = [prev_weekday[d] + assigned_weekday.get(d, 0) for d in active_doctors]
    we_vals = [prev_weekend[d] + assigned_weekend.get(d, 0) for d in active_doctors]

    bg_spread = (max(bg_vals) - min(bg_vals)) if bg_vals else 0
    ht_spread = (max(ht_vals) - min(ht_vals)) if ht_vals else 0
    wd_spread = (max(wd_vals) - min(wd_vals)) if wd_vals else 0
    we_spread = (max(we_vals) - min(we_vals)) if we_vals else 0

    bk_ly_imbalance = 0
    for doc in active_doctors:
        if doc in RATIO_EXEMPT_DOCTORS:
            continue
        bk_val = assigned_bk.get(doc, 0)
        ly_val = assigned_ly.get(doc, 0)
        bk_ly_imbalance += abs(bk_val - ly_val)

    penalty = 0
    penalty += fairness_penalty * W_FAIR_TOTAL
    penalty += gap_violations * W_GAP
    penalty += hosp_dup_violations * W_HOSP_DUP
    penalty += unassigned_slots * W_UNASSIGNED
    penalty += cap_violations * W_CAP

    penalty += max(0, bg_spread - 1) * W_BG_SPREAD
    penalty += max(0, ht_spread - 1) * W_HT_SPREAD
    penalty += max(0, wd_spread - 1) * W_WD_SPREAD
    penalty += max(0, we_spread - 1) * W_WE_SPREAD
    penalty += bk_ly_imbalance * W_BK_LY_BALANCE

    raw_score = 100 - penalty
    score = max(raw_score, 0)

    metrics = {
        "raw_score": float(raw_score),
        "penalty_total": float(penalty),
        "max_minus_min_total_active": int(diff_total),
        "gap_violations": int(gap_violations),
        "hospital_dup_violations": int(hosp_dup_violations),
        "unassigned_slots": int(unassigned_slots),
        "cap_violations": int(cap_violations),
        "bg_spread_cum": float(bg_spread),
        "ht_spread_cum": float(ht_spread),
        "weekday_spread_cum": float(wd_spread),
        "weekend_spread_cum": float(we_spread),
        "bk_ly_imbalance": int(bk_ly_imbalance),
    }
    return score, raw_score, metrics

# =========================
# ローカル探索（入替 swap）
# 🔧 FIX: date_doc_count を完全な defaultdict(lambda: defaultdict(int)) に変更
# 🔧 FIX: 同日重複チェックの強化
# =========================
def can_assign_doc_to_slot(doc, date, hosp):
    """ハード制約のみ（同日重複は別チェック）"""
    idx = shift_df.columns.get_loc(hosp)
    dow = pd.to_datetime(date).weekday()

    code = get_avail_code(date, doc)
    if code == 0:
        return False
    if code == 2 and not (B_COL_INDEX <= idx <= M_COL_INDEX):
        return False
    if code == 3 and not (H_COL_INDEX <= idx <= U_COL_INDEX):
        return False
    if H_COL_INDEX <= idx <= U_COL_INDEX:
        if get_sched_code(date, doc):
            return False
    if dow == 2 and H_COL_INDEX <= idx <= U_COL_INDEX and doc in WED_FORBIDDEN_DOCTORS:
        return False
    return True

def build_date_doc_count(pattern_df):
    """date -> doc -> count（同日複数割当検出も兼ねる）"""
    # 🔧 FIX: 完全な nested defaultdict に変更
    date_doc_count = defaultdict(lambda: defaultdict(int))
    for (ridx, hosp), (date, fixed) in slot_meta.items():
        val = pattern_df.at[ridx, hosp]
        if isinstance(val, str):
            v = normalize_name(val)  # 🔧 FIX
            if v in doctor_names:
                date_doc_count[date][v] += 1
    return date_doc_count

def collect_violation_docs_from_assignments(doc_assignments, assigned_hosp_count):
    bad = set()
    # gap
    for doc, assigns in doc_assignments.items():
        dlist = sorted([d for d, _ in assigns])
        for i in range(1, len(dlist)):
            if (dlist[i] - dlist[i - 1]).days < 4:
                bad.add(doc)
                break
    # hospital dup
    for doc, hdict in assigned_hosp_count.items():
        if any(c > 1 for c in hdict.values()):
            bad.add(doc)
    return bad

def is_better_raw(new_raw, new_metrics, cur_raw, cur_metrics):
    if new_raw > cur_raw:
        return True
    if new_raw < cur_raw:
        return False
    # tie-break（重要度順）
    keys = [
        "unassigned_slots",
        "cap_violations",
        "gap_violations",
        "hospital_dup_violations",
        "max_minus_min_total_active",
        "bk_ly_imbalance",
        "bg_spread_cum",
        "ht_spread_cum",
        "weekday_spread_cum",
        "weekend_spread_cum",
    ]
    return tuple(new_metrics.get(k, 0) for k in keys) < tuple(cur_metrics.get(k, 0) for k in keys)

def local_search_swap(pattern_df, max_iters=2000, patience=800, refresh_every=200, seed=0):
    """入替（swap）局所探索：preassignedは動かさず、free枠のみを対象に改善する"""
    if not movable_positions:
        # 動かせる枠が無い（全部固定など）
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, *_ = recompute_stats(pattern_df)
        score, raw_score, metrics = evaluate_schedule_with_raw(
            pattern_df,
            counts,
            bg_counts,
            ht_counts,
            wd_counts,
            we_counts,
            bk_counts,
            ly_counts,
        )
        return pattern_df.copy(), score, raw_score, metrics

    rng = random.Random(seed)
    df = pattern_df.copy()

    counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)
    cur_score, cur_raw, cur_metrics = evaluate_schedule_with_raw(
        df,
        counts,
        bg_counts,
        ht_counts,
        wd_counts,
        we_counts,
        bk_counts,
        ly_counts,
    )
    date_doc_count = build_date_doc_count(df)

    no_improve = 0
    bad_positions = None

    for it in range(1, max_iters + 1):
        if no_improve >= patience:
            break

        if it == 1 or it % refresh_every == 0:
            bad_docs = collect_violation_docs_from_assignments(doc_assignments, assigned_hosp_count)
            if bad_docs:
                tmp = []
                for (ridx, hosp, date) in movable_positions:
                    v = df.at[ridx, hosp]
                    if isinstance(v, str) and normalize_name(v) in bad_docs:  # 🔧 FIX
                        tmp.append((ridx, hosp, date))
                bad_positions = tmp if tmp else None
            else:
                bad_positions = None

        p1 = rng.choice(bad_positions if bad_positions is not None else movable_positions)
        p2 = rng.choice(movable_positions)
        if p1 == p2:
            no_improve += 1
            continue

        r1, h1, d1 = p1
        r2, h2, d2 = p2

        v1 = df.at[r1, h1]
        v2 = df.at[r2, h2]
        if not (isinstance(v1, str) and isinstance(v2, str)):
            no_improve += 1
            continue

        doc1 = normalize_name(v1)  # 🔧 FIX
        doc2 = normalize_name(v2)  # 🔧 FIX
        if doc1 not in doctor_names or doc2 not in doctor_names:
            no_improve += 1
            continue
        if doc1 == doc2:
            no_improve += 1
            continue

        # 🔧 FIX: 同日重複を作らない（同じ日同士のswapもチェック）
        if d1 == d2:
            # 同じ日のslot同士をswapする場合、元々同じdoctorがいなければOK
            # （既にdoc1!=doc2を確認済みなので、追加チェック不要）
            pass
        else:
            # 異なる日のswap
            if date_doc_count[d2][doc1] > 0:  # doc1がd2に既にいる
                no_improve += 1
                continue
            if date_doc_count[d1][doc2] > 0:  # doc2がd1に既にいる
                no_improve += 1
                continue

        # ハード制約
        if not can_assign_doc_to_slot(doc1, d2, h2):
            no_improve += 1
            continue
        if not can_assign_doc_to_slot(doc2, d1, h1):
            no_improve += 1
            continue

        # swap（in-place）
        df.at[r1, h1], df.at[r2, h2] = doc2, doc1

        # 🔧 FIX: date_doc_count 更新（defaultdictなのでKeyErrorなし）
        if d1 != d2:
            date_doc_count[d1][doc1] -= 1
            if date_doc_count[d1][doc1] <= 0:
                del date_doc_count[d1][doc1]
            date_doc_count[d2][doc2] -= 1
            if date_doc_count[d2][doc2] <= 0:
                del date_doc_count[d2][doc2]
            date_doc_count[d1][doc2] += 1
            date_doc_count[d2][doc1] += 1

        # 再評価（全再計算）
        counts2, bg2, ht2, wd2, we2, bk2, ly2, bg_cat2, assigned_hosp_count2, doc_assignments2, unassigned2 = recompute_stats(df)
        new_score, new_raw, new_metrics = evaluate_schedule_with_raw(
            df,
            counts2,
            bg2,
            ht2,
            wd2,
            we2,
            bk2,
            ly2,
        )

        if is_better_raw(new_raw, new_metrics, cur_raw, cur_metrics):
            cur_score, cur_raw, cur_metrics = new_score, new_raw, new_metrics
            counts, bg_counts, ht_counts, wd_counts, we_counts, bg_cat = counts2, bg2, ht2, wd2, we2, bg_cat2
            assigned_hosp_count, doc_assignments = assigned_hosp_count2, doc_assignments2
            no_improve = 0
        else:
            # revert
            df.at[r1, h1], df.at[r2, h2] = doc1, doc2
            if d1 != d2:
                date_doc_count[d1][doc2] -= 1
                if date_doc_count[d1][doc2] <= 0:
                    del date_doc_count[d1][doc2]
                date_doc_count[d2][doc1] -= 1
                if date_doc_count[d2][doc1] <= 0:
                    del date_doc_count[d2][doc1]
                date_doc_count[d1][doc1] += 1
                date_doc_count[d2][doc2] += 1
            no_improve += 1

    return df, cur_score, cur_raw, cur_metrics

# =========================
# サマリー列（Sheet4 の列を基準に自動生成）
# =========================
META_COLS_SHEET4 = {"カテ当番", "出張日", "出張先"}
BASE_SUMMARY_COLS = {"全合計", "大学合計", "外病院合計", "平日", "休日合計"}

UNIV7_SET = {"大学平日", "大学土曜昼", "大学土曜夜", "大学日曜昼", "大学日曜夜", "大学祝日昼", "大学祝日夜"}
UNIV7_ORDER = [c for c in sheet4_raw_out.columns if c in UNIV7_SET]
if not UNIV7_ORDER:
    UNIV7_ORDER = ["大学土曜昼", "大学土曜夜", "大学日曜昼", "大学日曜夜", "大学祝日昼", "大学祝日夜", "大学平日"]

DETAIL_COLS = [
    c for c in sheet4_raw_out.columns
    if c not in META_COLS_SHEET4 and c not in ["氏名"] and c not in BASE_SUMMARY_COLS and c not in UNIV7_SET
]

SUMMARY_DETAIL_COLS = UNIV7_ORDER + DETAIL_COLS
SUMMARY_COLS = ["氏名", "全合計", "大学合計", "外病院合計", "平日", "休日合計"] + SUMMARY_DETAIL_COLS

def count_doc_in_column(df, colname, doc):
    if colname not in df.columns:
        return 0
    s = df[colname]
    cnt = 0
    for v in s:
        if isinstance(v, str) and normalize_name(v) == doc:  # 🔧 FIX
            cnt += 1
    return cnt

def build_summaries(pattern_df, counts, bg_counts, ht_counts, wd_counts, we_counts, bg_cat_local):
    rows_month = []
    rows_total = []

    uni_map = {
        "大学平日": "平日",
        "大学土曜昼": "土曜昼",
        "大学土曜夜": "土曜夜",
        "大学日曜昼": "日曜昼",
        "大学日曜夜": "日曜夜",
        "大学祝日昼": "祝日昼",
        "大学祝日夜": "祝日夜",
    }

    for doc in doctor_names:
        pname = name_match.get(doc)
        base_row = name_to_row.get(pname) if pname and pname in name_to_row else None

        def prev_val(colname):
            if base_row is None:
                return 0.0
            v = base_row.get(colname, 0)
            try:
                return float(v or 0)
            except Exception:
                return 0.0

        # 今月
        row_m = {c: 0.0 for c in SUMMARY_COLS}
        row_m["氏名"] = doc
        row_m["全合計"] = float(counts.get(doc, 0))
        row_m["大学合計"] = float(bg_counts.get(doc, 0))
        row_m["外病院合計"] = float(ht_counts.get(doc, 0))
        row_m["平日"] = float(wd_counts.get(doc, 0))
        row_m["休日合計"] = float(we_counts.get(doc, 0))

        # 大学7分類
        for col in UNIV7_ORDER:
            cat = uni_map.get(col)
            if cat:
                row_m[col] = float(bg_cat_local[doc].get(cat, 0))

        # 病院列（Sheet4準拠）をそのまま数える
        for col in DETAIL_COLS:
            row_m[col] = float(count_doc_in_column(pattern_df, col, doc))

        # 累計（前月＋今月）
        row_t = {c: 0.0 for c in SUMMARY_COLS}
        row_t["氏名"] = doc
        for c in SUMMARY_COLS:
            if c == "氏名":
                continue
            row_t[c] = prev_val(c) + float(row_m.get(c, 0))

        rows_month.append(row_m)
        rows_total.append(row_t)

    return pd.DataFrame(rows_month)[SUMMARY_COLS], pd.DataFrame(rows_total)[SUMMARY_COLS]

# =========================
# 診断シート生成（偏り & gap違反一覧）
# =========================
def build_gap_details(doc_assignments):
    rows = []
    for doc, assigns in doc_assignments.items():
        assigns_sorted = sorted(assigns, key=lambda x: (x[0], x[1]))
        for i in range(1, len(assigns_sorted)):
            d_prev, h_prev = assigns_sorted[i - 1]
            d_cur, h_cur = assigns_sorted[i]
            gap = (d_cur - d_prev).days
            if gap < 4:
                rows.append({
                    "氏名": doc,
                    "前回日付": d_prev,
                    "前回病院": h_prev,
                    "今回日付": d_cur,
                    "今回病院": h_cur,
                    "間隔(日)": gap,
                })
    cols = ["氏名", "前回日付", "前回病院", "今回日付", "今回病院", "間隔(日)"]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows)[cols].sort_values(["氏名", "今回日付"]).reset_index(drop=True)

def build_same_day_duplicates(doc_assignments):
    rows = []
    for doc, assigns in doc_assignments.items():
        by_date = defaultdict(list)
        for d, h in assigns:
            by_date[d].append(h)
        for d, hs in by_date.items():
            if len(hs) > 1:
                rows.append({"氏名": doc, "日付": d, "件数": len(hs), "病院": ", ".join(sorted(hs))})
    cols = ["氏名", "日付", "件数", "病院"]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows)[cols].sort_values(["日付", "氏名"]).reset_index(drop=True)

def build_hosp_dup_details(assigned_hosp_count):
    rows = []
    for doc, hdict in assigned_hosp_count.items():
        for hosp, c in hdict.items():
            if c > 1:
                rows.append({"氏名": doc, "病院": hosp, "回数": c, "超過": c - 1})
    cols = ["氏名", "病院", "回数", "超過"]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows)[cols].sort_values(["超過", "氏名"], ascending=[False, True]).reset_index(drop=True)

def build_unassigned_details(unassigned):
    rows = [{"日付": d, "病院": hosp, "row_index": ridx} for d, hosp, ridx in unassigned]
    cols = ["日付", "病院", "row_index"]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows)[cols].sort_values(["日付", "病院"]).reset_index(drop=True)

def build_doctor_diag(counts, bg_counts, ht_counts, wd_counts, we_counts, doc_assignments, assigned_hosp_count):
    rows = []
    active_set = set(active_doctors)

    for doc in doctor_names:
        assigns = sorted(doc_assignments.get(doc, []), key=lambda x: x[0])
        gaps = [(assigns[i][0] - assigns[i - 1][0]).days for i in range(1, len(assigns))]
        gap_viol = sum(1 for g in gaps if g < 4)
        min_gap = min(gaps) if gaps else None
        hosp_excess = sum(max(0, c - 1) for c in assigned_hosp_count.get(doc, {}).values())

        row = {
            "氏名": doc,
            "active": 1 if doc in active_set else 0,
            "cap": TARGET_CAP.get(doc, 0),
            "preassigned": preassigned_count.get(doc, 0),

            "今月_全合計": counts.get(doc, 0),
            "累計_全合計": prev_total.get(doc, 0) + counts.get(doc, 0),

            "今月_大学合計": bg_counts.get(doc, 0),
            "累計_大学合計": prev_bg.get(doc, 0) + bg_counts.get(doc, 0),

            "今月_外病院合計": ht_counts.get(doc, 0),
            "累計_外病院合計": prev_ht.get(doc, 0) + ht_counts.get(doc, 0),

            "今月_平日": wd_counts.get(doc, 0),
            "累計_平日": prev_weekday.get(doc, 0) + wd_counts.get(doc, 0),

            "今月_休日合計": we_counts.get(doc, 0),
            "累計_休日合計": prev_weekend.get(doc, 0) + we_counts.get(doc, 0),

            "gap違反回数": gap_viol,
            "最小間隔(日)": min_gap if min_gap is not None else "",
            "同一病院重複超過": hosp_excess,
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # 偏り（active平均との差）も出しておく
    active_rows = df[df["active"] == 1]
    for col in ["累計_全合計", "累計_大学合計", "累計_外病院合計", "累計_平日", "累計_休日合計"]:
        if len(active_rows) > 0:
            mean_val = float(active_rows[col].mean())
            df[col + "_平均との差"] = df[col] - mean_val
        else:
            df[col + "_平均との差"] = 0.0

    return df.sort_values(["active", "累計_全合計"], ascending=[False, False]).reset_index(drop=True)

def build_metrics_df(score_clamped, raw_score, metrics):
    row = {"score": float(score_clamped), "raw_score": float(raw_score), **metrics}
    return pd.DataFrame([row])

def build_diagnostics(pattern_df):
    counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(pattern_df)
    score, raw, metrics = evaluate_schedule_with_raw(
        pattern_df,
        counts,
        bg_counts,
        ht_counts,
        wd_counts,
        we_counts,
        bk_counts,
        ly_counts,
    )

    df_doctors = build_doctor_diag(counts, bg_counts, ht_counts, wd_counts, we_counts, doc_assignments, assigned_hosp_count)
    df_gap = build_gap_details(doc_assignments)
    df_same = build_same_day_duplicates(doc_assignments)
    df_hdup = build_hosp_dup_details(assigned_hosp_count)
    df_unass = build_unassigned_details(unassigned)
    df_metrics = build_metrics_df(score, raw, metrics)

    return df_doctors, df_gap, df_same, df_hdup, df_unass, df_metrics

# =========================
# パターン探索（greedy → top候補に局所探索 → top3）
# =========================
print("\n🚀 スケジュール生成を開始します...")
print(f"   パターン数: {NUM_PATTERNS}")
print(f"   局所探索: {'有効' if LOCAL_SEARCH_ENABLED else '無効'}")
print(f"   ※処理時間: 約5-10分（パターン数に依存）\n")

score_rows = []
candidates = []  # TOP_KEEPだけ保持

for i in range(1, NUM_PATTERNS + 1):
    if i % 100 == 0 or i == 1:
        print(f"   進捗: {i}/{NUM_PATTERNS} パターン生成中...")

    (
        pattern_df,
        counts,
        bg_counts,
        ht_counts,
        wd_counts,
        we_counts,
        bk_counts,
        ly_counts,
        bg_cat,
    ) = build_schedule_pattern(seed=i)
    score, raw_score, metrics = evaluate_schedule_with_raw(
        pattern_df,
        counts,
        bg_counts,
        ht_counts,
        wd_counts,
        we_counts,
        bk_counts,
        ly_counts,
    )

    score_rows.append({"seed": i, "score": score, "raw_score": raw_score, **metrics})

    candidates.append({
        "seed": i,
        "score": score,
        "raw_score": raw_score,
        "metrics": metrics,
        "pattern_df": pattern_df,
    })
    candidates = sorted(candidates, key=lambda e: e["raw_score"], reverse=True)[:TOP_KEEP]

print(f"\n✅ {NUM_PATTERNS}パターンの生成完了")
print(f"   TOP{TOP_KEEP}候補を局所探索で最適化中...")

# ローカル探索で候補を改善
refined = []
for idx, cand in enumerate(candidates[:REFINE_TOP], 1):
    print(f"   候補{idx}/{REFINE_TOP}を最適化中...")
    if LOCAL_SEARCH_ENABLED:
        improved_df, sc2, raw2, met2 = local_search_swap(
            cand["pattern_df"],
            max_iters=LOCAL_MAX_ITERS,
            patience=LOCAL_PATIENCE,
            refresh_every=LOCAL_REFRESH_EVERY,
            seed=1000 + cand["seed"],
        )
    else:
        improved_df = cand["pattern_df"]
        sc2 = cand["score"]
        raw2 = cand["raw_score"]
        met2 = cand["metrics"]

    refined.append({
        "seed": cand["seed"],
        "score_before": cand["score"],
        "raw_before": cand["raw_score"],
        "score_after": sc2,
        "raw_after": raw2,
        "metrics_after": met2,
        "pattern_df": improved_df,
    })

refined_sorted = sorted(refined, key=lambda e: e["raw_after"], reverse=True)
top_patterns = refined_sorted[:3]

scores_df = pd.DataFrame(score_rows).sort_values(["raw_score", "seed"], ascending=[False, True]).reset_index(drop=True)

refined_df = pd.DataFrame([
    {
        "seed": e["seed"],
        "score_before": e["score_before"],
        "raw_before": e["raw_before"],
        "score_after": e["score_after"],
        "raw_after": e["raw_after"],
        **{f"after_{k}": v for k, v in e["metrics_after"].items() if k not in ("raw_score", "penalty_total")},
    }
    for e in refined_sorted
]).sort_values(["raw_after", "seed"], ascending=[False, True]).reset_index(drop=True)

print("\n✅ 局所探索完了")
print("\n=== TOP3パターンのスコア ===")
for rank, pattern in enumerate(top_patterns, 1):
    print(f"   {rank}位: raw_score={pattern['raw_after']:.1f}, " +
          f"gap違反={pattern['metrics_after']['gap_violations']}, " +
          f"未割当={pattern['metrics_after']['unassigned_slots']}")

# =========================
# 出力（pattern + summary + diagnostics）
# =========================
base_name = uploaded_filename.rsplit(".", 1)[0]
output_filename = f"{base_name}_auto_schedules_v2.1.xlsx"
output_path = output_filename

print(f"\n📝 結果をExcelファイルに出力中...")

best_pattern = top_patterns[0]["pattern_df"]
counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, *_ = recompute_stats(best_pattern)
df_month, df_total = build_summaries(best_pattern, counts, bg_counts, ht_counts, wd_counts, we_counts, bg_cat)
df_doctors, df_gap, df_same, df_hdup, df_unass, df_metrics = build_diagnostics(best_pattern)

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    best_pattern.to_excel(writer, sheet_name="schedule", index=False)
    df_month.to_excel(writer, sheet_name="summary_今月", index=False)
    df_total.to_excel(writer, sheet_name="summary_累計", index=False)

analysis_path = f"{base_name}_analysis.txt"
sorted_counts = sorted(
    counts.items(),
    key=lambda item: (item[1], doctor_col_index[item[0]]),
    reverse=True,
)

with open(analysis_path, "w", encoding="utf-8") as f:
    f.write("当直スケジュール解析結果\n")
    f.write("=" * 60 + "\n")
    f.write(f"出力Excel: {output_path}\n")
    f.write(f"全枠数: {total_slots}\n")
    f.write(f"active医師: {len(active_doctors)}人\n")
    f.write(f"基本割当数: {BASE_TARGET}回\n")
    f.write(f"余り枠: {EXTRA_SLOTS}枠（下の方の医師に+1回）\n")
    f.write("\n--- メトリクス ---\n")
    if not df_metrics.empty:
        metrics_row = df_metrics.iloc[0].to_dict()
        for key, value in metrics_row.items():
            f.write(f"{key}: {value}\n")
    f.write("\n--- 当直回数一覧 ---\n")
    for doc, cnt in sorted_counts:
        f.write(f"{doc}: {cnt}回\n")
    f.write("\n--- 未割当枠 ---\n")
    if df_unass.empty:
        f.write("なし\n")
    else:
        for _, row in df_unass.iterrows():
            f.write(f"{row['日付']} {row['病院']} (row_index={row['row_index']})\n")
    f.write("\n--- gap違反 ---\n")
    if df_gap.empty:
        f.write("なし\n")
    else:
        for _, row in df_gap.iterrows():
            f.write(
                f"{row['氏名']} {row['前回日付']}({row['前回病院']}) -> "
                f"{row['今回日付']}({row['今回病院']}) gap={row['間隔(日)']}\n"
            )
    f.write("\n--- 同日重複 ---\n")
    if df_same.empty:
        f.write("なし\n")
    else:
        for _, row in df_same.iterrows():
            f.write(f"{row['氏名']} {row['日付']} 件数={row['件数']} 病院={row['病院']}\n")
    f.write("\n--- 同一病院重複超過 ---\n")
    if df_hdup.empty:
        f.write("なし\n")
    else:
        for _, row in df_hdup.iterrows():
            f.write(f"{row['氏名']} {row['病院']} 回数={row['回数']} 超過={row['超過']}\n")

print("\n📄 解析結果（txt）を出力しました:")
print(f"   {analysis_path}")

print("\n📌 当直回数一覧")
for doc, cnt in sorted_counts:
    print(f"   {doc}: {cnt}回")

print("\n" + "="*60)
print("   🎉 完了！")
print("="*60)
print(f"\n📥 出力ファイル: {output_path}")
print("\n【ファイル内容】")
print("  - schedule: 最良パターンのスケジュール")
print("  - summary_今月 / summary_累計: サマリー")
print("="*60)

if COLAB_AVAILABLE:
    files.download(output_path)
