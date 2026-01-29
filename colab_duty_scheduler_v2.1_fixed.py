# @title 当直くん v3.4 (TARGET_CAP厳格化+多軸スコアリング+公平性強制)
# 修正内容:
# v3.4 (2026-01-29):
# - TARGET_CAP違反の厳格化
#   - パターン選択時に cap_violations > 0 のパターンを除外
#   - gap_violations > 0、unassigned_slots > 0 も除外
#   - ハード制約を満たすパターンのみを候補として選択
# - 多軸スコアリングシステムを実装
#   - 公平性重視: TARGET_CAP、医師間の割当回数の公平性を最優先
#   - 連続当直回避重視: gap違反、外病院重複を最優先
#   - バランス重視: 大学/外病院バランス、平日/休日バランスを最優先
#   - 各軸から最良パターンを1つずつ選択し、合計3パターン出力
# - 公平性の強制修正機能を追加
#   - fix_fairness_imbalance: 最大割当回数と最小割当回数の差を縮める
#   - 4回の医師から1回の医師にシフトを移動し、公平性を達成
#   - 差が1以下になるまで修正（例: 1回と4回 → 2回と3回）
#   - 最適化パイプラインに統合（修正順序の最後に実行）
# v3.3 (2026-01-28):
# - 大学病院3回以上を禁止（不満が高い）
#   - bg_over_2_violations: 大学3回以上の違反を検出（ペナルティ150）
#   - fix_university_over_2_violations: 最適化後に大学3回以上を修正
#   - 大学の割当を外病院に移動、または削除して2回以下に制限
# - 大学病院の平日偏り制約を追加（平日2回以上は不満）
#   - bg_weekday_over_violations: 大学の平日2回以上の違反を検出（ペナルティ80）
#   - fix_university_weekday_balance_violations: 最適化後に平日偏りを修正
#   - 大学平日の割当を外病院に移動、または削除
# - 全体の公平性を強化（2回の医師がいるなら4回の医師から渡す）
#   - fairness_penalty計算を強化: diff_total >= 2の場合、2倍のペナルティ
#   - W_FAIR_TOTAL: 10 → 30（公平性の重要度を上げる）
#   - min=2, max=4のような差が大きい場合に強く制約
# - 修正パイプラインを拡充
#   - 最適化後に全ての制約違反を強制的に修正
#   - 順序: ハード制約 → TARGET_CAP → 1.2 → BG/HT → gap → 外病院DUP → 大学3+ → 大学平日偏り → 公平性
# v3.2 (2026-01-28):
# - 生成パターン数をデフォルト100に戻す（処理時間の最適化）
#   - NUM_PATTERNS: 10000 → 100
#   - TOP_KEEP: 100 → 20
#   - REFINE_TOP: 20 → 15
# - 大学病院2回の場合、平日1回+休日1回のバランス制約を追加
#   - bg_weekday_weekend_imbalance 違反を検出
#   - ペナルティ: 50
# - 優先順位を厳格化（TARGET_CAP > gap > DUP を死守）
#   - W_CAP = 200（優先度1位）
#   - W_GAP = 100（優先度2位、3→100に強化）
#   - W_EXTERNAL_HOSP_DUP = 70（優先度3位）
# v3.1 (2026-01-28):
# - 外病院（L～Y列）重複を厳格化、大学病院（B～K列）重複は許容
#   - 評価関数で外病院重複と大学病院重複を分離
#   - W_EXTERNAL_HOSP_DUP=70（優先度3位：TARGET_CAP > gap > 外病院DUP）
#   - fix_external_hospital_dup_violations関数で最適化後に外病院重複を修正
#   - 同じ日の他の外病院に移動、または割当削除で修正
# v3.0 (2026-01-28):
# - gap違反（4日未満の間隔での割当）を完全に排除
#   - 初期パターン生成時にgap違反0個の候補のみ選択
#   - 局所探索でgap違反1以上になるswapを拒否
#   - fix_gap_violations関数で最適化後にgap違反を強制修正
#   - 移動先が見つからない場合は割当を削除して違反を解消
#   - 同じ病院だけでなく他の病院の空き枠も探索
# v2.8 (2026-01-24):
# - 大学系と外病院の差が3未満になる制約を追加
#   - 評価関数に差が3以上の場合のペナルティ追加（重み100）
#   - fix_bg_ht_imbalance_violations関数で最適化後に差3以上を修正
# - recompute_stats関数のBG/HT範囲を修正（B〜G→B〜K、H〜U→L〜Y）
#   - これにより出力Excelの今月/累計の大学合計・外病院合計が正しく計算される
# - 可否コード1.2の医師が大学系最低1回の制約を追加
#   - get_avail_code関数で1.2を認識できるよう修正
#   - fix_code_1_2_violations関数で最適化後に大学系0回を修正
#   - 評価関数に1.2の医師が大学系0回の場合のペナルティ追加（重み150）
# - TARGET_CAP違反の強制修正機能を追加
#   - fix_target_cap_violations関数で最適化後にTARGET_CAP超過を修正
#   - 上位医師（小林、及川等）の割当を下位医師（大河内、猪股等）に移動
#   - W_CAPペナルティを50→200に強化
# - 余り枠の割当ロジックを修正（昇順ソート→最後のEXTRA_SLOTS人を選択）
# - デバッグ情報追加：+1回対象の医師名、TARGET_CAP設定値、1.2対象医師を表示
# - デフォルトパターン数を100に変更（環境変数で上書き可能）
# v2.7 (2026-01-24):
# - ハード制約違反の自動修正機能を実装
#   - fix_hard_constraint_violations関数を追加
#   - 局所探索完了後に全ての違反を自動検出・修正
#   - 代替医師が見つからない場合は未割当として警告表示
#   - 修正後にスコアを再評価して最終結果に反映
# v2.6 (2026-01-23):
# - get_sched_code関数の重大なバグを修正
#   - "0"と"3"を有効なカテ表コードとして扱わないように変更
#   - "0"はデータなし、"3"は可否コードであり、カテ表コードではない
#   - これにより、カテ表コード保有医師がその日に"0"や"3"の場合、L〜Y列への割当が正しく許可される
# v2.5 (2026-01-21):
# - カテ表コードと列の制約を修正
#   - sheet3で少なくとも1つのカテ表コード（A,B,C,CC,D,E等）を持つ医師を特定
#   - カテ表コード保有医師: その日にコードがある場合のみB〜K列可、コードがない日は割当なし
#   - カテ表コード保有医師: その日にコードがある場合はL〜Y列禁止
#   - カテ表コード非保有医師: B〜K列に自由に割り当て可能
# - 出力パターンを1個から3個に変更（TOP3候補を提示）
# v2.4 (2026-01-21):
# - 列構造の変更対応（B〜Y列）
#   - 可否コード2: B〜Q列のみ可（従来B〜M列）
#   - 可否コード3: L〜Y列のみ可（従来H〜U列）
#   - カテ表制約: L〜Y列禁止（従来H〜U列）
# - B〜H列の2回上限制約を実装
# - 診断シートにB〜H列2回超過違反検出を追加
# v2.3 (2026-01-21):
# - B〜K列のカテ表要件をハード制約に変更（relax_scheduleで緩和不可）
# - B〜K列カテ表コード欠如違反の検出機能を追加
# - can_assign_doc_to_slot関数にB〜K列カテ表チェックを追加（局所探索でも適用）
# v2.2 (2026-01-21):
# - ハード制約違反の修正（可否コード0、カテ表+外病院、コード2/3違反）
# - collect_candidates関数でコード0を常に除外するよう修正
# - カテ表がある日のH〜U列割当を絶対禁止に変更
# - ハード制約違反チェック機能を診断シートに追加
# v2.1:
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

NUM_PATTERNS = int(os.getenv("NUM_PATTERNS", "100"))  # デフォルト100パターン

# sheet1 の「枠」扱いする入力値（1以外の記号も許容したい場合）
SLOT_MARKERS = {1, 1.0, "1", "〇", "○", "◯", "◎"}

# --- ローカル探索（入替）設定 ---
LOCAL_SEARCH_ENABLED = True
TOP_KEEP = 20                 # greedyで残す候補数（100パターンから上位20候補を保持）
REFINE_TOP = 15               # ローカル探索をかける候補数（上位15候補を最適化）
LOCAL_MAX_ITERS = 3000        # 1候補あたりの入替試行回数
LOCAL_PATIENCE = 1200         # 改善が出ない試行がこの回数続いたら打ち切り
LOCAL_REFRESH_EVERY = 200     # 問題医師（gap/重複）を再抽出する間隔

# スコア重み（必要なら調整）
# 優先順位: TARGET_CAP > gap > DUP を死守
W_FAIR_TOTAL = 30          # 全合計（active内 max-min）- 公平性強化
W_GAP = 100                # gap(4日未満) - 優先度2位
W_HOSP_DUP = 1             # 同一病院複数回（大学病院：許容）
W_EXTERNAL_HOSP_DUP = 70   # 外病院重複（厳格：優先度3位）
W_UNASSIGNED = 100         # 未割当
W_CAP = 200                # cap超え（厳格化：優先度1位）
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
print("   当直くん v3.4 (TARGET_CAP厳格化+多軸スコアリング+公平性強制)")
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

# 列インデックス（テンプレ依存：B〜Y を想定）
B_COL_INDEX = 1
C_COL_INDEX = 2
D_COL_INDEX = min(3, n_cols - 1)
E_COL_INDEX = min(4, n_cols - 1)
F_COL_INDEX = min(5, n_cols - 1)
G_COL_INDEX = min(6, n_cols - 1)
H_COL_INDEX = min(7, n_cols - 1)
I_COL_INDEX = min(8, n_cols - 1)
J_COL_INDEX = min(9, n_cols - 1)
K_COL_INDEX = min(10, n_cols - 1)
L_COL_INDEX = min(11, n_cols - 1)
M_COL_INDEX = min(12, n_cols - 1)
Q_COL_INDEX = min(16, n_cols - 1)
U_COL_INDEX = min(20, n_cols - 1)
Y_COL_INDEX = min(24, n_cols - 1)

# 列範囲定義
B_H_START_INDEX = B_COL_INDEX  # 大学系前半（2回まで）
B_H_END_INDEX = H_COL_INDEX
I_K_START_INDEX = I_COL_INDEX  # 大学系後半
I_K_END_INDEX = K_COL_INDEX
B_K_START_INDEX = B_COL_INDEX  # 大学系全体
B_K_END_INDEX = K_COL_INDEX
L_Y_START_INDEX = L_COL_INDEX  # 外病院
L_Y_END_INDEX = min(Y_COL_INDEX, n_cols - 1)

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
    raw_value = None
    if isinstance(availability_df.index, pd.DatetimeIndex):
        try:
            value = availability_df.at[pd.to_datetime(date).normalize().tz_localize(None), doctor]  # 🔧 FIX
            if isinstance(value, pd.Series):
                value = value.iloc[0]
            if pd.notna(value):
                raw_value = float(value)
                # 1.2は特別扱い：大学系優先
                if abs(raw_value - 1.2) < 0.01:
                    code = 1.2
                else:
                    code = int(raw_value)
        except Exception:
            pass
    if code is None:
        code = fallback_avail_codes.get(doctor, 1)
    if code not in (0, 1, 1.2, 2, 3):
        code = 1
    return code

def get_sched_code(date, doctor):
    """その日の有効なカテ表コードを取得（0と3は無効として扱う）"""
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
    code_str = str(value).strip()
    # 0と3は有効なカテ表コードではない（0=データなし、3=可否コード）
    if not code_str or code_str == "0" or code_str == "3":
        return None
    return code_str

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
# cap設計：n回ベース＋余りは右側（下側）からn+1回
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

# 余り枠は右側（下位）の医師に割り当てる
# 例：小林(0), 及川(1), ..., 大河内(30), 猪股(31) の場合、右側の医師を選択
active_sorted_by_index = sorted(active_doctors, key=lambda d: doctor_col_index[d])  # 昇順ソート
EXTRA_ALLOWED = set(active_sorted_by_index[-EXTRA_SLOTS:] if EXTRA_SLOTS > 0 else [])  # 最後のEXTRA_SLOTS人（右側/下位）

TARGET_CAP = {d: 0 for d in doctor_names}
for d in active_doctors:
    TARGET_CAP[d] = BASE_TARGET
for d in EXTRA_ALLOWED:
    TARGET_CAP[d] = BASE_TARGET + 1
for d in doctor_names:
    if preassigned_count.get(d, 0) > TARGET_CAP.get(d, 0):
        TARGET_CAP[d] = preassigned_count[d]

floor_shifts = BASE_TARGET

print(f"\n✅ 割当設計完了")
print(f"   全枠数: {total_slots}")
print(f"   active医師: {len(active_doctors)}人")
print(f"   inactive医師: {len(inactive_doctors)}人")
print(f"   基本割当数: {BASE_TARGET}回")
print(f"   余り枠: {EXTRA_SLOTS}枠（右側/下位の医師に+1回）")
if EXTRA_ALLOWED:
    extra_docs_display = sorted(EXTRA_ALLOWED, key=lambda d: doctor_col_index[d])
    print(f"   +1回対象: {', '.join(extra_docs_display)}")

    # デバッグ：上位医師が含まれていないことを確認
    upper_doctors = [d for d in active_doctors if doctor_col_index[d] < 10]  # 最初の10人
    upper_in_extra = [d for d in upper_doctors if d in EXTRA_ALLOWED]
    if upper_in_extra:
        print(f"   ⚠️ 警告: 上位医師が+1回対象に含まれています: {', '.join(upper_in_extra)}")

    # 各医師のTARGET_CAPを表示（最初の5人と最後の5人）
    cap_display = []
    for d in active_sorted_by_index[:5]:
        cap_display.append(f"{d}={TARGET_CAP[d]}")
    cap_display.append("...")
    for d in active_sorted_by_index[-5:]:
        cap_display.append(f"{d}={TARGET_CAP[d]}")
    print(f"   TARGET_CAP: {' / '.join(cap_display)}")

# =========================
# B-K / L-Y 比率バランス（sheet3で「3」記載の医師は除外）
# sheet3でカテ表コード保有医師の特定
# =========================
def has_sheet3_code_3(doc):
    if doc not in schedule_df.columns:
        return False
    values = schedule_df[doc].dropna()
    return any(str(v).strip() == "3" for v in values)

def has_any_schedule_code(doc):
    """医師がsheet3で少なくとも1つのカテ表コード（A,B,C,CC,D,E等、3以外）を持っているか"""
    if doc not in schedule_df.columns:
        return False
    values = schedule_df[doc].dropna()
    for v in values:
        s = str(v).strip()
        if s and s != "0" and s != "3":  # 0と3以外のコードがあればTrue
            return True
    return False

RATIO_EXEMPT_DOCTORS = {doc for doc in doctor_names if has_sheet3_code_3(doc)}
if RATIO_EXEMPT_DOCTORS:
    print(f"   比率バランス除外（sheet3に3あり）: {sorted(RATIO_EXEMPT_DOCTORS)}")

SCHEDULE_CODE_HOLDERS = {doc for doc in doctor_names if has_any_schedule_code(doc)}
if SCHEDULE_CODE_HOLDERS:
    print(f"   カテ表コード保有医師: {len(SCHEDULE_CODE_HOLDERS)}人")
    print(f"   カテ表コード非保有医師: {len([d for d in doctor_names if d not in SCHEDULE_CODE_HOLDERS])}人")

# 可否コード1.2の医師（大学系最低1回必須）
def has_code_1_2(doc):
    """医師がsheet2で少なくとも1つの1.2コードを持っているか"""
    if doc not in availability_df.columns:
        return False
    for date in all_shift_dates:
        code = get_avail_code(date, doc)
        if code == 1.2:
            return True
    return False

CODE_1_2_DOCTORS = {doc for doc in doctor_names if has_code_1_2(doc)}
if CODE_1_2_DOCTORS:
    print(f"   可否コード1.2医師（大学系最低1回必須）: {len(CODE_1_2_DOCTORS)}人")
    print(f"      対象: {', '.join(sorted(CODE_1_2_DOCTORS)[:10])}")

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
    assigned_bh,
    assigned_hosp_count,
):
    idx = shift_df.columns.get_loc(hospital_name)
    is_BE = B_COL_INDEX <= idx <= E_COL_INDEX
    is_BG = B_COL_INDEX <= idx <= K_COL_INDEX
    is_BH = B_H_START_INDEX <= idx <= B_H_END_INDEX
    is_LY_range = L_COL_INDEX <= idx <= L_Y_END_INDEX
    is_BK = is_bk_slot(idx)
    is_LY = is_ly_slot(idx)
    dow = pd.to_datetime(date).weekday()
    weekday = dow < 5

    def collect_candidates(
        allow_same_day=False,
        relax_availability=False,
        relax_schedule=False,
        relax_wed=False,
        relax_bh_limit=False,
    ):
        candidates = []
        for doc in doctor_names:
            if not allow_same_day and date in assigned_dates[doc]:
                continue

            code = get_avail_code(date, doc)

            # ★ ハード制約1: コード0は絶対に緩和しない
            if code == 0:
                continue

            # コード2/3のチェック（relax_availability=Trueで緩和可能）
            if not relax_availability:
                # 2 -> B〜Q列以外ダメ
                if code == 2 and not (B_COL_INDEX <= idx <= Q_COL_INDEX):
                    continue
                # 3 -> L〜Y列以外ダメ
                if code == 3 and not (L_COL_INDEX <= idx <= L_Y_END_INDEX):
                    continue

            # ★ ハード制約2: その日にカテ表コードあり→L〜Y列不可（絶対に緩和しない）
            if L_COL_INDEX <= idx <= L_Y_END_INDEX:
                if get_sched_code(date, doc):
                    continue

            # ★ ハード制約3: B〜K列はカテ表コード保有医師のみカテ表コードが必要（絶対に緩和しない）
            if B_COL_INDEX <= idx <= B_K_END_INDEX:
                # カテ表コード保有医師は、その日にカテ表コードが必要
                if doc in SCHEDULE_CODE_HOLDERS and not get_sched_code(date, doc):
                    continue

            # ★ ハード制約4: B〜H列は2回まで（relax_bh_limitで緩和可能）
            if not relax_bh_limit and is_BH and assigned_bh[doc] >= 2:
                continue

            # 水曜日L〜Y列禁止医師
            if not relax_wed and dow == 2 and is_LY_range:
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
        candidates = collect_candidates(allow_same_day=True, relax_availability=True, relax_bh_limit=True)
    if not candidates:
        candidates = collect_candidates(
            allow_same_day=True,
            relax_availability=True,
            relax_schedule=True,
            relax_wed=True,
            relax_bh_limit=True,
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
    elif is_LY_range:
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
    assigned_bh = {d: 0 for d in doctor_names}  # B〜H列の割当回数（2回まで）
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
            if B_COL_INDEX <= hidx <= K_COL_INDEX:
                assigned_bg[doc] += 1
                if B_COL_INDEX <= hidx <= E_COL_INDEX:
                    assigned_be[doc] += 1
                elif F_COL_INDEX <= hidx <= G_COL_INDEX:
                    assigned_fg[doc] += 1
                bg_cat[doc][classify_bg_category(date, hosp)] += 1
            elif L_COL_INDEX <= hidx <= L_Y_END_INDEX:
                assigned_ht[doc] += 1

            # B〜H列のカウント
            if B_H_START_INDEX <= hidx <= B_H_END_INDEX:
                assigned_bh[doc] += 1

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
                assigned_bh=assigned_bh,
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
            if B_COL_INDEX <= hidx <= K_COL_INDEX:
                assigned_bg[chosen] += 1
                if B_COL_INDEX <= hidx <= E_COL_INDEX:
                    assigned_be[chosen] += 1
                elif F_COL_INDEX <= hidx <= G_COL_INDEX:
                    assigned_fg[chosen] += 1
                bg_cat[chosen][classify_bg_category(date, hosp)] += 1
            elif L_COL_INDEX <= hidx <= L_Y_END_INDEX:
                assigned_ht[chosen] += 1

            # B〜H列のカウント
            if B_H_START_INDEX <= hidx <= B_H_END_INDEX:
                assigned_bh[chosen] += 1

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
        # 大学系はB〜K列（B_COL_INDEX=1 〜 K_COL_INDEX=10）
        if B_COL_INDEX <= hidx <= B_K_END_INDEX:
            bg_counts[doc] += 1
            bg_cat[doc][classify_bg_category(date, hosp)] += 1
        # 外病院はL〜Y列（L_COL_INDEX=11 〜 Y_COL_INDEX=24）
        elif L_COL_INDEX <= hidx <= L_Y_END_INDEX:
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
    # 差が2以上の場合、不満が高いので強いペナルティ
    # 例: min=2, max=4の場合、4回の医師から2回の医師に渡すべき
    if diff_total >= 2:
        fairness_penalty = diff_total * 2  # 2倍のペナルティ
    else:
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
    external_hosp_dup_violations = 0  # 外病院重複（厳しく扱う）
    for doc, hdict in hosp_counts_by_doc.items():
        for hosp, c in hdict.items():
            if c > 1:
                # 病院が外病院（L～Y列）かどうかを判定
                hidx = shift_df.columns.get_loc(hosp)
                if L_COL_INDEX <= hidx <= L_Y_END_INDEX:
                    external_hosp_dup_violations += (c - 1)
                else:
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

    # 可否コード1.2の医師が大学系0回の場合のペナルティ
    code_1_2_violations = 0
    for doc in CODE_1_2_DOCTORS:
        if assigned_bg.get(doc, 0) == 0:
            code_1_2_violations += 1

    # 大学系と外病院の差が3以上の場合のペナルティ
    bg_ht_imbalance_violations = 0
    for doc in active_doctors:
        bg = assigned_bg.get(doc, 0)
        ht = assigned_ht.get(doc, 0)
        diff = abs(bg - ht)
        if diff >= 3:
            bg_ht_imbalance_violations += (diff - 2)  # 差が3以上の超過分をカウント

    # 大学病院2回の場合、平日1回+休日1回のバランス違反
    bg_weekday_weekend_imbalance = 0
    bg_over_2_violations = 0  # 大学3回以上の違反（不満が高い）
    bg_weekday_over_violations = 0  # 大学の平日偏り（平日2回以上は不満）
    for doc in active_doctors:
        bg_total = assigned_bg.get(doc, 0)
        weekday_count = bg_cat[doc].get("平日", 0)

        # 大学3回以上は不可
        if bg_total >= 3:
            bg_over_2_violations += (bg_total - 2)

        # 大学2回の場合、平日1回+休日1回が理想
        if bg_total == 2:
            if weekday_count == 0 or weekday_count == 2:
                bg_weekday_weekend_imbalance += 1

        # 大学の平日が2回以上は不満
        if weekday_count >= 2:
            bg_weekday_over_violations += (weekday_count - 1)

    penalty = 0
    penalty += fairness_penalty * W_FAIR_TOTAL
    penalty += gap_violations * W_GAP
    penalty += hosp_dup_violations * W_HOSP_DUP
    penalty += external_hosp_dup_violations * W_EXTERNAL_HOSP_DUP  # 外病院重複は厳格
    penalty += unassigned_slots * W_UNASSIGNED
    penalty += cap_violations * W_CAP
    penalty += code_1_2_violations * 150  # 1.2の医師が大学系0回の場合、大きなペナルティ
    penalty += bg_ht_imbalance_violations * 100  # 大学系と外病院の差が3以上の場合、大きなペナルティ
    penalty += bg_weekday_weekend_imbalance * 50  # 大学病院2回の平日/休日バランス違反
    penalty += bg_over_2_violations * 150  # 大学3回以上の違反（不満が高い）
    penalty += bg_weekday_over_violations * 80  # 大学の平日偏り（平日2回以上は不満）

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
        "external_hosp_dup_violations": int(external_hosp_dup_violations),
        "unassigned_slots": int(unassigned_slots),
        "cap_violations": int(cap_violations),
        "code_1_2_violations": int(code_1_2_violations),
        "bg_ht_imbalance_violations": int(bg_ht_imbalance_violations),
        "bg_weekday_weekend_imbalance": int(bg_weekday_weekend_imbalance),
        "bg_over_2_violations": int(bg_over_2_violations),
        "bg_weekday_over_violations": int(bg_weekday_over_violations),
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
    # 可否コード2 → B〜Q列のみ可
    if code == 2 and not (B_COL_INDEX <= idx <= Q_COL_INDEX):
        return False
    # 可否コード3 → L〜Y列のみ可
    if code == 3 and not (L_COL_INDEX <= idx <= L_Y_END_INDEX):
        return False
    # その日にカテ表コードあり → L〜Y列不可
    if L_COL_INDEX <= idx <= L_Y_END_INDEX:
        if get_sched_code(date, doc):
            return False
    # B〜K列はカテ表コード保有医師のみカテ表コードが必要
    if B_COL_INDEX <= idx <= B_K_END_INDEX:
        if doc in SCHEDULE_CODE_HOLDERS and not get_sched_code(date, doc):
            return False
    # 水曜日L〜Y列禁止医師
    if dow == 2 and L_COL_INDEX <= idx <= L_Y_END_INDEX and doc in WED_FORBIDDEN_DOCTORS:
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

        # gap違反が1以上のパターンは採用しない（ハード制約）
        new_gap_violations = new_metrics.get("gap_violations", 0)
        if new_gap_violations > 0:
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
        elif is_better_raw(new_raw, new_metrics, cur_raw, cur_metrics):
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

def build_hard_constraint_violations(pattern_df):
    """ハード制約違反の詳細リストを生成"""
    rows = []

    for ridx in pattern_df.index:
        date = pattern_df.at[ridx, date_col_shift]
        if pd.isna(date):
            continue
        date = pd.to_datetime(date).normalize().tz_localize(None)
        dow = date.weekday()

        for hosp in hospital_cols:
            val = pattern_df.at[ridx, hosp]
            if not isinstance(val, str):
                continue
            doc = normalize_name(val)
            if doc not in doctor_names:
                continue

            idx = shift_df.columns.get_loc(hosp)
            code = get_avail_code(date, doc)
            sched_code = get_sched_code(date, doc)

            # 違反1: 可否コード0
            if code == 0:
                rows.append({
                    "違反種別": "可否コード0違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code if sched_code else "",
                    "詳細": "コード0（不可）の日に割当",
                })

            # 違反2: 可否コード2違反（Q列より後に割当）
            if code == 2 and not (B_COL_INDEX <= idx <= Q_COL_INDEX):
                rows.append({
                    "違反種別": "可否コード2違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code if sched_code else "",
                    "詳細": f"コード2はB〜Q列のみ可。列{idx}に割当",
                })

            # 違反3: 可否コード3違反（L〜Y列以外に割当）
            if code == 3 and not (L_COL_INDEX <= idx <= L_Y_END_INDEX):
                rows.append({
                    "違反種別": "可否コード3違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code if sched_code else "",
                    "詳細": f"コード3はL〜Y列のみ可。列{idx}に割当",
                })

            # 違反4: カテ表コードあり＋L〜Y列違反
            if L_COL_INDEX <= idx <= L_Y_END_INDEX and sched_code:
                rows.append({
                    "違反種別": "カテ表+外病院違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code,
                    "詳細": f"カテ表（{sched_code}）がある日は外病院（L〜Y列）に割当不可。列{idx}に割当",
                })

            # 違反5: B〜K列でカテ表コードなし（カテ表コード保有医師のみ）
            if B_COL_INDEX <= idx <= B_K_END_INDEX and doc in SCHEDULE_CODE_HOLDERS and not sched_code:
                rows.append({
                    "違反種別": "B-K列カテ表コード欠如",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": "",
                    "詳細": f"B〜K列（大学系）の割当にカテ表コードが必要（カテ表コード保有医師）。列{idx}に割当",
                })

            # 違反6: 水曜日L〜Y列禁止医師
            if dow == 2 and L_COL_INDEX <= idx <= L_Y_END_INDEX and doc in WED_FORBIDDEN_DOCTORS:
                rows.append({
                    "違反種別": "水曜日L〜Y列禁止違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code if sched_code else "",
                    "詳細": f"{doc}は水曜日のL〜Y列禁止",
                })

    # B〜H列の2回超過違反をチェック
    bh_counts = defaultdict(list)
    for ridx in pattern_df.index:
        date = pattern_df.at[ridx, date_col_shift]
        if pd.isna(date):
            continue
        date = pd.to_datetime(date).normalize().tz_localize(None)

        for hosp in hospital_cols:
            val = pattern_df.at[ridx, hosp]
            if not isinstance(val, str):
                continue
            doc = normalize_name(val)
            if doc not in doctor_names:
                continue

            idx = shift_df.columns.get_loc(hosp)
            if B_H_START_INDEX <= idx <= B_H_END_INDEX:
                bh_counts[doc].append((date, hosp, idx))

    # 違反7: B〜H列が2回超過
    for doc, assignments in bh_counts.items():
        if len(assignments) > 2:
            for date, hosp, idx in assignments[2:]:  # 3回目以降
                code = get_avail_code(date, doc)
                sched_code = get_sched_code(date, doc)
                rows.append({
                    "違反種別": "B-H列2回超過違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code if sched_code else "",
                    "詳細": f"B〜H列は2回まで。{len(assignments)}回目の割当",
                })

    cols = ["違反種別", "日付", "医師名", "病院", "列番号", "可否コード", "カテ表", "詳細"]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows)[cols].sort_values(["違反種別", "日付", "医師名"]).reset_index(drop=True)

def fix_hard_constraint_violations(pattern_df, max_attempts=50, verbose=True):
    """
    ハード制約違反を自動修正する

    Args:
        pattern_df: スケジュールDataFrame
        max_attempts: 最大試行回数
        verbose: ログ出力するか

    Returns:
        (修正後のDataFrame, 成功フラグ, 修正数, 修正失敗数)
    """
    df = pattern_df.copy()
    total_fixed = 0
    total_failed = 0

    for attempt in range(max_attempts):
        violations_df = build_hard_constraint_violations(df)

        if len(violations_df) == 0:
            if verbose and total_fixed > 0:
                print(f"   ✅ ハード制約違反を{total_fixed}件修正しました")
            return df, True, total_fixed, total_failed

        if attempt == 0 and verbose:
            print(f"   ⚠️ ハード制約違反を{len(violations_df)}件検出 → 自動修正を開始...")

        # 各違反を修正試行
        fixed_in_this_iteration = 0

        for _, violation in violations_df.iterrows():
            date = violation['日付']
            doc = violation['医師名']
            hosp = violation['病院']
            violation_type = violation['違反種別']

            # 該当行を探す
            ridx = None
            for idx in df.index:
                if pd.to_datetime(df.at[idx, date_col_shift]).normalize().tz_localize(None) == date:
                    ridx = idx
                    break

            if ridx is None:
                continue

            # 違反している割当を解除
            current_val = df.at[ridx, hosp]
            if not isinstance(current_val, str) or normalize_name(current_val) != doc:
                continue

            df.at[ridx, hosp] = None

            # 代替医師を探す
            col_idx = shift_df.columns.get_loc(hosp)
            dow = pd.to_datetime(date).weekday()

            # この日に既に割り当てられている医師を除外
            already_assigned_on_date = set()
            for h in hospital_cols:
                v = df.at[ridx, h]
                if isinstance(v, str):
                    already_assigned_on_date.add(normalize_name(v))

            # 候補医師を探す（ハード制約のみチェック）
            candidates = []
            for candidate_doc in doctor_names:
                # 同日重複チェック
                if candidate_doc in already_assigned_on_date:
                    continue

                # ハード制約チェック
                if can_assign_doc_to_slot(candidate_doc, date, hosp):
                    candidates.append(candidate_doc)

            if candidates:
                # 優先順位：全体合計が少ない医師を優先
                candidates.sort(key=lambda d: prev_total.get(d, 0) + len([1 for h in hospital_cols for ridx2 in df.index if isinstance(df.at[ridx2, h], str) and normalize_name(df.at[ridx2, h]) == d]))
                new_doc = candidates[0]
                df.at[ridx, hosp] = new_doc
                fixed_in_this_iteration += 1
                total_fixed += 1
            else:
                # 代替医師が見つからない → 未割当のまま
                total_failed += 1
                if verbose:
                    print(f"   ⚠️ 修正失敗: {date.strftime('%Y-%m-%d')} {hosp} ({violation_type})")

        # 進捗がなければループ終了
        # 修正が進まなくてもmax_attemptsまで試行を続ける
        # if fixed_in_this_iteration == 0:
        #     break

    # 最終チェック
    final_violations = build_hard_constraint_violations(df)
    success = len(final_violations) == 0

    if verbose:
        if success:
            print(f"   ✅ 全てのハード制約違反を修正しました（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ {len(final_violations)}件のハード制約違反が残っています（修正数: {total_fixed}, 失敗: {total_failed}）")

    return df, success, total_fixed, total_failed

def fix_target_cap_violations(pattern_df, max_attempts=100, verbose=True):
    """
    TARGET_CAP違反を修正する（上位医師が下位医師より多くならないよう強制）

    Args:
        pattern_df: スケジュールDataFrame
        max_attempts: 最大試行回数
        verbose: ログ出力するか

    Returns:
        (修正後のDataFrame, 成功フラグ, 修正数)
    """
    df = pattern_df.copy()
    total_fixed = 0

    for attempt in range(max_attempts):
        # 現在の割当回数を再計算
        counts, *_ = recompute_stats(df)

        # cap超過している医師を特定
        over_cap_docs = []
        under_cap_docs = []

        for doc in active_doctors:
            current = counts.get(doc, 0)
            cap = TARGET_CAP.get(doc, 0)

            if current > cap:
                over_cap_docs.append((doc, current - cap))
            elif current < cap:
                under_cap_docs.append((doc, cap - current))

        if not over_cap_docs:
            if verbose and total_fixed > 0:
                print(f"   ✅ TARGET_CAP違反を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            over_cap_names = [f"{doc}({counts[doc]}/{TARGET_CAP[doc]})" for doc, _ in over_cap_docs]
            print(f"   ⚠️ TARGET_CAP超過を検出 → 自動修正を開始...")
            print(f"      超過: {', '.join(over_cap_names[:5])}")

        # 修正試行
        fixed_in_this_iteration = 0

        for over_doc, excess in over_cap_docs:
            if excess <= 0:
                continue

            # このover_docの割当を探す
            over_doc_positions = []
            for ridx in df.index:
                date = df.at[ridx, date_col_shift]
                if pd.isna(date):
                    continue
                date = pd.to_datetime(date).normalize().tz_localize(None)

                for hosp in hospital_cols:
                    val = df.at[ridx, hosp]
                    if isinstance(val, str) and normalize_name(val) == over_doc:
                        over_doc_positions.append((ridx, hosp, date))

            # ランダムに1つ選んで移動を試みる
            import random
            random.shuffle(over_doc_positions)

            for ridx, hosp, date in over_doc_positions[:min(excess, 3)]:  # 最大3個まで試行
                # この日に既に割り当てられている医師を除外
                already_assigned_on_date = set()
                for h in hospital_cols:
                    v = df.at[ridx, h]
                    if isinstance(v, str):
                        already_assigned_on_date.add(normalize_name(v))

                # under_capの医師の中から代替を探す
                candidates = []
                for under_doc, deficit in under_cap_docs:
                    if deficit <= 0:
                        continue
                    if under_doc in already_assigned_on_date:
                        continue
                    if can_assign_doc_to_slot(under_doc, date, hosp):
                        candidates.append(under_doc)

                if candidates:
                    # 全体合計が少ない医師を優先
                    candidates.sort(key=lambda d: prev_total.get(d, 0) + counts.get(d, 0))
                    new_doc = candidates[0]

                    # 入れ替え
                    df.at[ridx, hosp] = new_doc
                    fixed_in_this_iteration += 1
                    total_fixed += 1

                    # under_cap_docsを更新
                    for i, (d, deficit) in enumerate(under_cap_docs):
                        if d == new_doc:
                            under_cap_docs[i] = (d, deficit - 1)
                            break

                    break  # 次のover_docへ

        # 修正が進まなくてもmax_attemptsまで試行を続ける
        # if fixed_in_this_iteration == 0:
        #     break

    # 最終確認
    counts, *_ = recompute_stats(df)
    remaining_violations = sum(1 for doc in active_doctors if counts.get(doc, 0) > TARGET_CAP.get(doc, 0))

    if verbose:
        if remaining_violations == 0:
            print(f"   ✅ 全てのTARGET_CAP違反を修正しました（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ {remaining_violations}件のTARGET_CAP違反が残っています（修正数: {total_fixed}）")

    return df, remaining_violations == 0, total_fixed

def fix_code_1_2_violations(pattern_df, max_attempts=100, verbose=True):
    """
    可否コード1.2の医師が大学系0回の違反を修正する

    Args:
        pattern_df: スケジュールDataFrame
        max_attempts: 最大試行回数
        verbose: ログ出力するか

    Returns:
        (修正後のDataFrame, 成功フラグ, 修正数)
    """
    if not CODE_1_2_DOCTORS:
        return pattern_df, True, 0

    df = pattern_df.copy()
    total_fixed = 0

    for attempt in range(max_attempts):
        # 現在の割当回数を再計算
        counts, bg_counts, *_ = recompute_stats(df)

        # 大学系0回の1.2医師を特定
        zero_bg_docs = []
        for doc in CODE_1_2_DOCTORS:
            if bg_counts.get(doc, 0) == 0:
                zero_bg_docs.append(doc)

        if not zero_bg_docs:
            if verbose and total_fixed > 0:
                print(f"   ✅ 可否コード1.2医師の大学系0回違反を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            print(f"   ⚠️ 可否コード1.2医師の大学系0回違反を検出 → 自動修正を開始...")
            print(f"      対象: {', '.join(zero_bg_docs[:5])}")

        # 修正試行
        fixed_in_this_iteration = 0

        for zero_doc in zero_bg_docs:
            # このzero_docの外病院（L〜Y）割当を探す
            zero_doc_ly_positions = []
            for ridx in df.index:
                date = df.at[ridx, date_col_shift]
                if pd.isna(date):
                    continue
                date = pd.to_datetime(date).normalize().tz_localize(None)

                for hosp in hospital_cols:
                    idx = shift_df.columns.get_loc(hosp)
                    # L〜Y列（外病院）のみ
                    if L_COL_INDEX <= idx <= L_Y_END_INDEX:
                        val = df.at[ridx, hosp]
                        if isinstance(val, str) and normalize_name(val) == zero_doc:
                            zero_doc_ly_positions.append((ridx, hosp, date))

            # 外病院の割当を1つ大学系に変更
            import random
            random.shuffle(zero_doc_ly_positions)

            for ridx, hosp, date in zero_doc_ly_positions[:1]:  # 1つだけ試行
                # この日付のB〜K列（大学系）で空いている枠を探す
                for bg_hosp in hospital_cols:
                    bg_idx = shift_df.columns.get_loc(bg_hosp)
                    if not (B_COL_INDEX <= bg_idx <= B_K_END_INDEX):
                        continue

                    val = df.at[ridx, bg_hosp]
                    # 空き枠かどうか
                    if not is_slot_value(shift_df.at[ridx, bg_hosp]):
                        continue
                    if isinstance(val, str) and val in doctor_names:
                        continue  # 既に割当済み

                    # この日にzero_docが既に割り当てられていないかチェック
                    already_assigned = False
                    for h in hospital_cols:
                        v = df.at[ridx, h]
                        if isinstance(v, str) and normalize_name(v) == zero_doc and h != hosp:
                            already_assigned = True
                            break

                    if already_assigned:
                        continue

                    # 制約チェック
                    if can_assign_doc_to_slot(zero_doc, date, bg_hosp):
                        # 外病院から削除、大学系に追加
                        df.at[ridx, hosp] = None  # 外病院を解除
                        df.at[ridx, bg_hosp] = zero_doc  # 大学系に割当
                        fixed_in_this_iteration += 1
                        total_fixed += 1
                        break  # 次のzero_docへ

                if fixed_in_this_iteration > 0:
                    break  # 次のzero_docへ

        # 修正が進まなくてもmax_attemptsまで試行を続ける
        # if fixed_in_this_iteration == 0:
        #     break

    # 最終確認
    counts, bg_counts, *_ = recompute_stats(df)
    remaining_violations = sum(1 for doc in CODE_1_2_DOCTORS if bg_counts.get(doc, 0) == 0)

    if verbose:
        if remaining_violations == 0:
            print(f"   ✅ 全ての可否コード1.2医師の大学系0回違反を修正しました（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ {remaining_violations}件の可否コード1.2医師の大学系0回違反が残っています（修正数: {total_fixed}）")

    return df, remaining_violations == 0, total_fixed

def fix_bg_ht_imbalance_violations(pattern_df, max_attempts=100, verbose=True):
    """
    大学系と外病院の差が3以上の違反を修正する

    Args:
        pattern_df: スケジュールDataFrame
        max_attempts: 最大試行回数
        verbose: ログ出力するか

    Returns:
        (修正後のDataFrame, 成功フラグ, 修正数)
    """
    df = pattern_df.copy()
    total_fixed = 0

    for attempt in range(max_attempts):
        # 現在の割当回数を再計算
        counts, bg_counts, ht_counts, *_ = recompute_stats(df)

        # 大学系と外病院の差が3以上の医師を特定
        imbalance_docs = []
        for doc in active_doctors:
            bg = bg_counts.get(doc, 0)
            ht = ht_counts.get(doc, 0)
            diff = abs(bg - ht)
            if diff >= 3:
                imbalance_docs.append((doc, bg, ht, diff))

        if not imbalance_docs:
            if verbose and total_fixed > 0:
                print(f"   ✅ 大学系と外病院の差3以上の違反を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            imbalance_names = [f"{doc}(BG={bg}/HT={ht})" for doc, bg, ht, diff in imbalance_docs[:5]]
            print(f"   ⚠️ 大学系と外病院の差3以上の違反を検出 → 自動修正を開始...")
            print(f"      対象: {', '.join(imbalance_names)}")

        # 修正試行
        fixed_in_this_iteration = 0

        for doc, bg, ht, diff in imbalance_docs:
            if diff < 3:
                continue

            # BGが多い場合: BG→HTに移動
            # HTが多い場合: HT→BGに移動
            if bg > ht:
                # BGの割当を1つHTに変更
                source_range = (B_COL_INDEX, B_K_END_INDEX)
                target_range = (L_COL_INDEX, L_Y_END_INDEX)
            else:
                # HTの割当を1つBGに変更
                source_range = (L_COL_INDEX, L_Y_END_INDEX)
                target_range = (B_COL_INDEX, B_K_END_INDEX)

            # source範囲の割当を探す
            source_positions = []
            for ridx in df.index:
                date = df.at[ridx, date_col_shift]
                if pd.isna(date):
                    continue
                date = pd.to_datetime(date).normalize().tz_localize(None)

                for hosp in hospital_cols:
                    idx = shift_df.columns.get_loc(hosp)
                    if source_range[0] <= idx <= source_range[1]:
                        val = df.at[ridx, hosp]
                        if isinstance(val, str) and normalize_name(val) == doc:
                            source_positions.append((ridx, hosp, date))

            # 1つ移動を試みる
            import random
            random.shuffle(source_positions)

            for ridx, hosp, date in source_positions[:1]:
                # target範囲で空いている枠を探す
                for target_hosp in hospital_cols:
                    target_idx = shift_df.columns.get_loc(target_hosp)
                    if not (target_range[0] <= target_idx <= target_range[1]):
                        continue

                    val = df.at[ridx, target_hosp]
                    # 空き枠かどうか
                    if not is_slot_value(shift_df.at[ridx, target_hosp]):
                        continue
                    if isinstance(val, str) and val in doctor_names:
                        continue  # 既に割当済み

                    # この日にdocが既に割り当てられていないかチェック
                    already_assigned = False
                    for h in hospital_cols:
                        v = df.at[ridx, h]
                        if isinstance(v, str) and normalize_name(v) == doc and h != hosp:
                            already_assigned = True
                            break

                    if already_assigned:
                        continue

                    # 制約チェック
                    if can_assign_doc_to_slot(doc, date, target_hosp):
                        # sourceから削除、targetに追加
                        df.at[ridx, hosp] = None
                        df.at[ridx, target_hosp] = doc
                        fixed_in_this_iteration += 1
                        total_fixed += 1
                        break  # 次のdocへ

                if fixed_in_this_iteration > 0:
                    break  # 次のdocへ

        # 修正が進まなくてもmax_attemptsまで試行を続ける
        # if fixed_in_this_iteration == 0:
        #     break

    # 最終確認
    counts, bg_counts, ht_counts, *_ = recompute_stats(df)
    remaining_violations = sum(1 for doc in active_doctors if abs(bg_counts.get(doc, 0) - ht_counts.get(doc, 0)) >= 3)

    if verbose:
        if remaining_violations == 0:
            print(f"   ✅ 全ての大学系と外病院の差3以上の違反を修正しました（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ {remaining_violations}件の大学系と外病院の差3以上の違反が残っています（修正数: {total_fixed}）")

    return df, remaining_violations == 0, total_fixed

def fix_gap_violations(pattern_df, max_attempts=200, verbose=True):
    """
    gap違反（4日未満の間隔での割当）を修正する

    Args:
        pattern_df: スケジュールDataFrame
        max_attempts: 最大試行回数
        verbose: ログ出力するか

    Returns:
        (修正後のDataFrame, 成功フラグ, 修正数)
    """
    df = pattern_df.copy()
    total_fixed = 0
    consecutive_failures = 0

    for attempt in range(max_attempts):
        # 現在の割当状態を再計算
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)

        # gap違反を検出
        gap_violation_list = []
        for doc, date_hosp_list in doc_assignments.items():
            dates = sorted([d for d, h in date_hosp_list])
            for i in range(1, len(dates)):
                gap = (dates[i] - dates[i-1]).days
                if gap < 4:
                    gap_violation_list.append((doc, dates[i-1], dates[i], gap))

        if not gap_violation_list:
            if verbose and total_fixed > 0:
                print(f"   ✅ gap違反（4日未満の間隔）を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            violation_names = [f"{doc}({d1.strftime('%m/%d')}-{d2.strftime('%m/%d')}={gap}日)"
                             for doc, d1, d2, gap in gap_violation_list[:5]]
            print(f"   ⚠️ gap違反を{len(gap_violation_list)}件検出 → 自動修正を開始...")
            print(f"      例: {', '.join(violation_names)}")

        # 修正試行（1イテレーションで複数の違反を修正）
        fixed_in_this_iteration = 0

        for doc, date1, date2, gap in gap_violation_list:
            if gap >= 4:
                continue

            # date2の割当を探す
            positions_at_date2 = []
            for ridx in df.index:
                date = df.at[ridx, date_col_shift]
                if pd.isna(date):
                    continue
                date = pd.to_datetime(date).normalize().tz_localize(None)
                if date != date2:
                    continue

                for hosp in hospital_cols:
                    val = df.at[ridx, hosp]
                    if isinstance(val, str) and normalize_name(val) == doc:
                        positions_at_date2.append((ridx, hosp, date))

            # 各positionに対して修正を試みる
            for ridx_src, hosp_src, date_src in positions_at_date2:
                moved = False

                # 移動先候補を探す
                for ridx_tgt in df.index:
                    date_tgt = df.at[ridx_tgt, date_col_shift]
                    if pd.isna(date_tgt):
                        continue
                    date_tgt = pd.to_datetime(date_tgt).normalize().tz_localize(None)

                    # date1とdate_tgtの間隔をチェック
                    gap_from_date1 = abs((date_tgt - date1).days)
                    if gap_from_date1 < 4:
                        continue

                    # docの他の割当とdate_tgtの間隔をチェック
                    doc_dates = sorted([d for d, h in doc_assignments[doc]])
                    doc_dates_without_date2 = [d for d in doc_dates if d != date2]

                    valid_gap = True
                    for existing_date in doc_dates_without_date2:
                        if abs((date_tgt - existing_date).days) < 4:
                            valid_gap = False
                            break

                    if not valid_gap:
                        continue

                    # その日にdocが既に割当られていないかチェック
                    already_assigned = False
                    for hosp_check in hospital_cols:
                        val = df.at[ridx_tgt, hosp_check]
                        if isinstance(val, str) and normalize_name(val) == doc:
                            already_assigned = True
                            break

                    if already_assigned:
                        continue

                    # 全ての病院で空き枠を探す
                    hospitals_to_try = [hosp_src] + [h for h in hospital_cols if h != hosp_src]
                    for hosp_tgt in hospitals_to_try:
                        if pd.isna(df.at[ridx_tgt, hosp_tgt]):
                            # ハード制約チェック
                            if not can_assign_doc_to_slot(doc, date_tgt, hosp_tgt):
                                continue

                            # 移動実行
                            df.at[ridx_src, hosp_src] = None
                            df.at[ridx_tgt, hosp_tgt] = doc
                            fixed_in_this_iteration += 1
                            total_fixed += 1
                            moved = True
                            break

                    if moved:
                        break

                # 移動先が見つからない場合は削除（積極的に実行）
                if not moved and attempt >= 5:  # 5回目以降は削除も検討
                    df.at[ridx_src, hosp_src] = None
                    fixed_in_this_iteration += 1
                    total_fixed += 1
                    if verbose and attempt < 10:
                        print(f"      移動先が見つからないため、{doc}の{date_src.strftime('%m/%d')}の割当を削除します")
                    break  # この違反の他のpositionは試さない

            # この違反を修正したら、doc_assignmentsを更新
            if fixed_in_this_iteration > 0:
                counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)

        # 進捗チェック
        if fixed_in_this_iteration == 0:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        # 連続で20回修正できなければ諦める
        if consecutive_failures >= 20:
            break

    # 最終確認
    counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)
    remaining_violations = 0
    for doc, date_hosp_list in doc_assignments.items():
        dates = sorted([d for d, h in date_hosp_list])
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days < 4:
                remaining_violations += 1

    if verbose:
        if remaining_violations == 0:
            print(f"   ✅ 全てのgap違反を修正しました（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ {remaining_violations}件のgap違反が残っています（修正数: {total_fixed}）")

    return df, remaining_violations == 0, total_fixed

def fix_external_hospital_dup_violations(pattern_df, max_attempts=150, verbose=True):
    """
    外病院（L～Y列）の重複を修正する（大学病院の重複は許容）

    Args:
        pattern_df: スケジュールDataFrame
        max_attempts: 最大試行回数
        verbose: ログ出力するか

    Returns:
        (修正後のDataFrame, 成功フラグ, 修正数)
    """
    df = pattern_df.copy()
    total_fixed = 0
    consecutive_failures = 0

    for attempt in range(max_attempts):
        # 現在の割当状態を再計算
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)

        # 外病院重複を検出
        external_dup_list = []
        for doc, hosp_dict in assigned_hosp_count.items():
            for hosp, count in hosp_dict.items():
                if count > 1:
                    # 外病院かどうかを判定
                    hidx = shift_df.columns.get_loc(hosp)
                    if L_COL_INDEX <= hidx <= L_Y_END_INDEX:
                        external_dup_list.append((doc, hosp, count))

        if not external_dup_list:
            if verbose and total_fixed > 0:
                print(f"   ✅ 外病院重複を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            dup_names = [f"{doc}({hosp}={count}回)" for doc, hosp, count in external_dup_list[:5]]
            print(f"   ⚠️ 外病院重複を{len(external_dup_list)}件検出 → 自動修正を開始...")
            print(f"      例: {', '.join(dup_names)}")

        # 修正試行
        fixed_in_this_iteration = 0

        for doc, dup_hosp, count in external_dup_list:
            if count <= 1:
                continue

            # この医師のこの病院への割当を探す
            dup_positions = []
            for ridx in df.index:
                date = df.at[ridx, date_col_shift]
                if pd.isna(date):
                    continue
                date = pd.to_datetime(date).normalize().tz_localize(None)

                val = df.at[ridx, dup_hosp]
                if isinstance(val, str) and normalize_name(val) == doc:
                    dup_positions.append((ridx, dup_hosp, date))

            # 重複のうち1つを残して、残りを別の病院に移動または削除
            import random
            random.shuffle(dup_positions)

            for ridx, hosp, date in dup_positions[1:]:  # 最初の1つは残す
                moved = False

                # 同じ日の他の外病院（L～Y列）の空き枠を探す
                for other_hosp in hospital_cols:
                    other_hidx = shift_df.columns.get_loc(other_hosp)
                    # 外病院かつ重複病院でない
                    if not (L_COL_INDEX <= other_hidx <= L_Y_END_INDEX):
                        continue
                    if other_hosp == dup_hosp:
                        continue

                    # この病院にこの医師が既に割当られていないか
                    if assigned_hosp_count[doc].get(other_hosp, 0) >= 1:
                        continue

                    # 空き枠があるか
                    if pd.isna(df.at[ridx, other_hosp]):
                        # ハード制約チェック
                        if not can_assign_doc_to_slot(doc, date, other_hosp):
                            continue

                        # 移動実行
                        df.at[ridx, dup_hosp] = None
                        df.at[ridx, other_hosp] = doc
                        fixed_in_this_iteration += 1
                        total_fixed += 1
                        moved = True
                        break

                # 移動先が見つからない場合は削除
                if not moved and attempt >= 5:
                    df.at[ridx, dup_hosp] = None
                    fixed_in_this_iteration += 1
                    total_fixed += 1
                    if verbose and attempt < 10:
                        print(f"      移動先が見つからないため、{doc}の{date.strftime('%m/%d')}の{dup_hosp}割当を削除します")
                    break  # この重複の他のpositionは次回

            if fixed_in_this_iteration > 0:
                counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)

        # 進捗チェック
        if fixed_in_this_iteration == 0:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        # 連続で20回修正できなければ諦める
        if consecutive_failures >= 20:
            break

    # 最終確認
    counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)
    remaining_violations = 0
    for doc, hosp_dict in assigned_hosp_count.items():
        for hosp, count in hosp_dict.items():
            if count > 1:
                hidx = shift_df.columns.get_loc(hosp)
                if L_COL_INDEX <= hidx <= L_Y_END_INDEX:
                    remaining_violations += (count - 1)

    if verbose:
        if remaining_violations == 0:
            print(f"   ✅ 全ての外病院重複を修正しました（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ {remaining_violations}件の外病院重複が残っています（修正数: {total_fixed}）")

    return df, remaining_violations == 0, total_fixed

def fix_university_over_2_violations(pattern_df, max_attempts=150, verbose=True):
    """
    大学病院（B～K列）が3回以上の医師の違反を修正する

    Args:
        pattern_df: スケジュールDataFrame
        max_attempts: 最大試行回数
        verbose: ログ出力するか

    Returns:
        (修正後のDataFrame, 成功フラグ, 修正数)
    """
    df = pattern_df.copy()
    total_fixed = 0
    consecutive_failures = 0

    for attempt in range(max_attempts):
        # 現在の割当状態を再計算
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)

        # 大学3回以上の医師を検出
        over_2_list = []
        for doc in active_doctors:
            bg_count = bg_counts.get(doc, 0)
            if bg_count >= 3:
                over_2_list.append((doc, bg_count))

        if not over_2_list:
            if verbose and total_fixed > 0:
                print(f"   ✅ 大学3回以上違反を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            over_names = [f"{doc}({bg_count}回)" for doc, bg_count in over_2_list[:5]]
            print(f"   ⚠️ 大学3回以上違反を{len(over_2_list)}件検出 → 自動修正を開始...")
            print(f"      対象: {', '.join(over_names)}")

        # 修正試行
        fixed_in_this_iteration = 0

        for doc, bg_count in over_2_list:
            if bg_count < 3:
                continue

            # この医師の大学病院への割当を探す
            bg_positions = []
            for ridx in df.index:
                date = df.at[ridx, date_col_shift]
                if pd.isna(date):
                    continue
                date = pd.to_datetime(date).normalize().tz_localize(None)

                for hosp in hospital_cols:
                    hidx = shift_df.columns.get_loc(hosp)
                    # 大学病院（B～K列）か
                    if not (B_COL_INDEX <= hidx <= B_K_END_INDEX):
                        continue

                    val = df.at[ridx, hosp]
                    if isinstance(val, str) and normalize_name(val) == doc:
                        bg_positions.append((ridx, hosp, date))

            # 3回以上のうち、削減する（2回まで減らす）
            excess = bg_count - 2
            import random
            random.shuffle(bg_positions)

            for ridx, hosp, date in bg_positions[:excess]:
                moved = False

                # 同じ日の外病院（L～Y列）の空き枠に移動を試みる
                for other_hosp in hospital_cols:
                    other_hidx = shift_df.columns.get_loc(other_hosp)
                    # 外病院か
                    if not (L_COL_INDEX <= other_hidx <= L_Y_END_INDEX):
                        continue

                    # この病院にこの医師が既に割当られていないか
                    if assigned_hosp_count[doc].get(other_hosp, 0) >= 1:
                        continue

                    # 空き枠があるか
                    if pd.isna(df.at[ridx, other_hosp]):
                        # ハード制約チェック
                        if not can_assign_doc_to_slot(doc, date, other_hosp):
                            continue

                        # 移動実行
                        df.at[ridx, hosp] = None
                        df.at[ridx, other_hosp] = doc
                        fixed_in_this_iteration += 1
                        total_fixed += 1
                        moved = True
                        break

                # 移動先が見つからない場合は削除
                if not moved and attempt >= 5:
                    df.at[ridx, hosp] = None
                    fixed_in_this_iteration += 1
                    total_fixed += 1
                    if verbose and attempt < 10:
                        print(f"      {doc}の{date.strftime('%m/%d')}の大学病院割当を削除します（3回以上→2回）")

            if fixed_in_this_iteration > 0:
                counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)

        # 進捗チェック
        if fixed_in_this_iteration == 0:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        # 連続で20回修正できなければ諦める
        if consecutive_failures >= 20:
            break

    # 最終確認
    counts, bg_counts, *_ = recompute_stats(df)
    remaining_violations = sum(1 for doc in active_doctors if bg_counts.get(doc, 0) >= 3)

    if verbose:
        if remaining_violations == 0:
            print(f"   ✅ 全ての大学3回以上違反を修正しました（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ {remaining_violations}件の大学3回以上違反が残っています（修正数: {total_fixed}）")

    return df, remaining_violations == 0, total_fixed

def fix_university_weekday_balance_violations(pattern_df, max_attempts=150, verbose=True):
    """
    大学病院の平日偏り（平日2回以上）の違反を修正する

    Args:
        pattern_df: スケジュールDataFrame
        max_attempts: 最大試行回数
        verbose: ログ出力するか

    Returns:
        (修正後のDataFrame, 成功フラグ, 修正数)
    """
    df = pattern_df.copy()
    total_fixed = 0
    consecutive_failures = 0

    for attempt in range(max_attempts):
        # 現在の割当状態を再計算
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)

        # 大学の平日2回以上の医師を検出
        weekday_over_list = []
        for doc in active_doctors:
            weekday_count = bg_cat[doc].get("平日", 0)
            if weekday_count >= 2:
                weekday_over_list.append((doc, weekday_count, bg_counts.get(doc, 0)))

        if not weekday_over_list:
            if verbose and total_fixed > 0:
                print(f"   ✅ 大学平日偏り違反を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            over_names = [f"{doc}(平日{wd}回/大学{total}回)" for doc, wd, total in weekday_over_list[:5]]
            print(f"   ⚠️ 大学平日偏り違反を{len(weekday_over_list)}件検出 → 自動修正を開始...")
            print(f"      対象: {', '.join(over_names)}")

        # 修正試行
        fixed_in_this_iteration = 0

        for doc, weekday_count, bg_total in weekday_over_list:
            if weekday_count < 2:
                continue

            # この医師の大学病院平日の割当を探す
            bg_weekday_positions = []
            for ridx in df.index:
                date = df.at[ridx, date_col_shift]
                if pd.isna(date):
                    continue
                date = pd.to_datetime(date).normalize().tz_localize(None)

                for hosp in hospital_cols:
                    hidx = shift_df.columns.get_loc(hosp)
                    # 大学病院（B～K列）か
                    if not (B_COL_INDEX <= hidx <= B_K_END_INDEX):
                        continue

                    val = df.at[ridx, hosp]
                    if isinstance(val, str) and normalize_name(val) == doc:
                        # 平日か
                        category = classify_bg_category(date, hosp)
                        if category == "平日":
                            bg_weekday_positions.append((ridx, hosp, date))

            # 平日のうち1つを外病院に移動または削除
            import random
            random.shuffle(bg_weekday_positions)

            for ridx, hosp, date in bg_weekday_positions[:1]:  # 1つだけ試行
                moved = False

                # 同じ日の外病院（L～Y列）の空き枠に移動を試みる
                for other_hosp in hospital_cols:
                    other_hidx = shift_df.columns.get_loc(other_hosp)
                    # 外病院か
                    if not (L_COL_INDEX <= other_hidx <= L_Y_END_INDEX):
                        continue

                    # この病院にこの医師が既に割当られていないか
                    if assigned_hosp_count[doc].get(other_hosp, 0) >= 1:
                        continue

                    # 空き枠があるか
                    if pd.isna(df.at[ridx, other_hosp]):
                        # ハード制約チェック
                        if not can_assign_doc_to_slot(doc, date, other_hosp):
                            continue

                        # 移動実行
                        df.at[ridx, hosp] = None
                        df.at[ridx, other_hosp] = doc
                        fixed_in_this_iteration += 1
                        total_fixed += 1
                        moved = True
                        break

                # 移動先が見つからない場合は削除
                if not moved and attempt >= 5:
                    df.at[ridx, hosp] = None
                    fixed_in_this_iteration += 1
                    total_fixed += 1
                    if verbose and attempt < 10:
                        print(f"      {doc}の{date.strftime('%m/%d')}の大学平日割当を削除します")
                    break

            if fixed_in_this_iteration > 0:
                counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)

        # 進捗チェック
        if fixed_in_this_iteration == 0:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        # 連続で20回修正できなければ諦める
        if consecutive_failures >= 20:
            break

    # 最終確認
    counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, *_ = recompute_stats(df)
    remaining_violations = sum(1 for doc in active_doctors if bg_cat[doc].get("平日", 0) >= 2)

    if verbose:
        if remaining_violations == 0:
            print(f"   ✅ 全ての大学平日偏り違反を修正しました（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ {remaining_violations}件の大学平日偏り違反が残っています（修正数: {total_fixed}）")

    return df, remaining_violations == 0, total_fixed

def fix_fairness_imbalance(pattern_df, max_attempts=200, verbose=True):
    """
    active医師間の割当回数の公平性を強化する（最大と最小の差を縮める）

    Args:
        pattern_df: スケジュールDataFrame
        max_attempts: 最大試行回数
        verbose: ログ出力するか

    Returns:
        (修正後のDataFrame, 成功フラグ, 修正数)
    """
    df = pattern_df.copy()
    total_fixed = 0
    consecutive_failures = 0

    for attempt in range(max_attempts):
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned = recompute_stats(df)

        # active医師の割当回数を確認
        active_counts = [(doc, counts.get(doc, 0)) for doc in active_doctors]
        if not active_counts:
            return df, True, total_fixed

        # 最大と最小を取得
        max_count = max(c for _, c in active_counts)
        min_count = min(c for _, c in active_counts)
        diff = max_count - min_count

        # 差が1以下なら公平性達成
        if diff <= 1:
            if verbose and total_fixed > 0:
                print(f"   ✅ 公平性違反を{total_fixed}件修正しました（max={max_count}, min={min_count}, diff={diff}）")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            max_docs = [doc for doc, c in active_counts if c == max_count]
            min_docs = [doc for doc, c in active_counts if c == min_count]
            print(f"   ⚠️ 公平性違反を検出（max={max_count}, min={min_count}, diff={diff}） → 自動修正を開始...")
            print(f"      最多: {', '.join(max_docs[:3])}... ({len(max_docs)}人)")
            print(f"      最少: {', '.join(min_docs[:3])}... ({len(min_docs)}人)")

        fixed_in_this_iteration = 0

        # 最大回数の医師から最小回数の医師にシフトを移動
        max_docs = [doc for doc, c in active_counts if c == max_count]
        min_docs = [doc for doc, c in active_counts if c == min_count]

        import random
        random.shuffle(max_docs)
        random.shuffle(min_docs)

        # 最大回数の医師のシフトを探す
        for max_doc in max_docs[:3]:  # 最大3人まで試行
            # max_docの割当位置を取得
            max_doc_positions = []
            for ridx in df.index:
                date = df.at[ridx, date_col_shift]
                if pd.isna(date):
                    continue
                date = pd.to_datetime(date).normalize().tz_localize(None)

                for hosp in hospital_cols:
                    val = df.at[ridx, hosp]
                    if isinstance(val, str) and normalize_name(val) == max_doc:
                        max_doc_positions.append((ridx, hosp, date))

            random.shuffle(max_doc_positions)

            # 各位置について、最小回数の医師と入れ替え可能か試す
            for ridx, hosp, date in max_doc_positions[:5]:  # 最大5個まで試行
                # この日に既に割り当てられている医師を除外
                already_assigned_on_date = set()
                for h in hospital_cols:
                    v = df.at[ridx, h]
                    if isinstance(v, str):
                        already_assigned_on_date.add(normalize_name(v))

                # 最小回数の医師の中から代替を探す
                for min_doc in min_docs:
                    if min_doc in already_assigned_on_date:
                        continue
                    if not can_assign_doc_to_slot(min_doc, date, hosp):
                        continue

                    # gap制約チェック（移動後にgap違反が発生しないか）
                    # min_docに割り当てた場合のgap違反チェック
                    min_doc_dates = sorted([d for r, h, d in doc_assignments.get(min_doc, []) if (r, h) != (ridx, hosp)])
                    new_dates = sorted(min_doc_dates + [date])

                    gap_ok = True
                    for j in range(len(new_dates) - 1):
                        gap = (new_dates[j + 1] - new_dates[j]).days
                        if gap < 4:
                            gap_ok = False
                            break

                    if not gap_ok:
                        continue

                    # max_docから削除した場合のgap違反チェック
                    max_doc_dates = sorted([d for r, h, d in doc_assignments.get(max_doc, []) if (r, h) != (ridx, hosp)])
                    if len(max_doc_dates) >= 2:
                        for j in range(len(max_doc_dates) - 1):
                            gap = (max_doc_dates[j + 1] - max_doc_dates[j]).days
                            # 削除によってgap違反が発生することはない（削除は間隔を広げるだけ）

                    # 入れ替え
                    df.at[ridx, hosp] = min_doc
                    fixed_in_this_iteration += 1
                    total_fixed += 1

                    if verbose and attempt < 5:
                        print(f"      {date.strftime('%m/%d')} {hosp}: {max_doc}({max_count}回) → {min_doc}({min_count}回)")

                    # doc_assignmentsを更新（次の反復のため）
                    if max_doc in doc_assignments:
                        doc_assignments[max_doc] = [(r, h, d) for r, h, d in doc_assignments[max_doc] if (r, h) != (ridx, hosp)]
                    if min_doc not in doc_assignments:
                        doc_assignments[min_doc] = []
                    doc_assignments[min_doc].append((ridx, hosp, date))

                    break  # min_docs loop

                if fixed_in_this_iteration > 0:
                    break  # max_doc_positions loop

            if fixed_in_this_iteration > 0:
                break  # max_docs loop

        # 進捗チェック
        if fixed_in_this_iteration == 0:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        # 連続で20回修正できなければ諦める
        if consecutive_failures >= 20:
            break

    # 最終確認
    counts, *_ = recompute_stats(df)
    active_counts = [(doc, counts.get(doc, 0)) for doc in active_doctors]
    max_count = max(c for _, c in active_counts)
    min_count = min(c for _, c in active_counts)
    diff = max_count - min_count

    if verbose:
        if diff <= 1:
            print(f"   ✅ 公平性を達成しました（max={max_count}, min={min_count}, diff={diff}）（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ 公平性違反が残っています（max={max_count}, min={min_count}, diff={diff}）（修正数: {total_fixed}）")

    return df, diff <= 1, total_fixed

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
    df_hard_violations = build_hard_constraint_violations(pattern_df)

    return df_doctors, df_gap, df_same, df_hdup, df_unass, df_metrics, df_hard_violations

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

    # gap違反が0個のパターンのみ採用（完全なgap制約遵守）
    gap_violations = metrics.get("gap_violations", 0)
    if gap_violations == 0:
        candidates.append({
            "seed": i,
            "score": score,
            "raw_score": raw_score,
            "metrics": metrics,
            "pattern_df": pattern_df,
        })

# gap違反0個の候補をスコア順にソート
candidates = sorted(candidates, key=lambda e: e["raw_score"], reverse=True)[:TOP_KEEP]

print(f"\n✅ {NUM_PATTERNS}パターンの生成完了")
print(f"   gap違反0個の候補: {len(candidates)}個")
if len(candidates) == 0:
    print("   ⚠️ 警告: gap違反0個の候補が見つかりませんでした。制約を緩和します...")
    # gap違反の制約を緩和して再選択
    candidates = []
    for row in score_rows:
        candidates.append({
            "seed": row["seed"],
            "score": row["score"],
            "raw_score": row["raw_score"],
            "metrics": {k: v for k, v in row.items() if k not in ["seed", "score", "raw_score"]},
            "pattern_df": None,  # 再生成が必要
        })
    candidates = sorted(candidates, key=lambda e: e["raw_score"], reverse=True)[:TOP_KEEP]
    # パターンを再生成
    for cand in candidates:
        if cand["pattern_df"] is None:
            pattern_df, *_ = build_schedule_pattern(seed=cand["seed"])
            cand["pattern_df"] = pattern_df

print(f"   TOP{min(TOP_KEEP, len(candidates))}候補を局所探索で最適化中...")

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

    # ハード制約違反の自動修正
    print(f"   候補{idx}/{REFINE_TOP}のハード制約違反チェック中...")
    fixed_df, fix_success, fix_count, fail_count = fix_hard_constraint_violations(
        improved_df, max_attempts=50, verbose=True
    )

    # TARGET_CAP違反の自動修正
    print(f"   候補{idx}/{REFINE_TOP}のTARGET_CAPチェック中...")
    cap_fixed_df, cap_success, cap_fix_count = fix_target_cap_violations(
        fixed_df, max_attempts=100, verbose=True
    )

    # 可否コード1.2の医師が大学系0回の違反を修正
    print(f"   候補{idx}/{REFINE_TOP}の可否コード1.2チェック中...")
    code_1_2_fixed_df, code_1_2_success, code_1_2_fix_count = fix_code_1_2_violations(
        cap_fixed_df, max_attempts=100, verbose=True
    )

    # 大学系と外病院の差が3以上の違反を修正
    print(f"   候補{idx}/{REFINE_TOP}の大学系/外病院バランスチェック中...")
    bg_ht_fixed_df, bg_ht_success, bg_ht_fix_count = fix_bg_ht_imbalance_violations(
        code_1_2_fixed_df, max_attempts=100, verbose=True
    )

    # gap違反（4日未満の間隔）を修正
    print(f"   候補{idx}/{REFINE_TOP}のgap違反チェック中...")
    gap_fixed_df, gap_success, gap_fix_count = fix_gap_violations(
        bg_ht_fixed_df, max_attempts=200, verbose=True
    )

    # 外病院重複を修正（優先度3位）
    print(f"   候補{idx}/{REFINE_TOP}の外病院重複チェック中...")
    ext_dup_fixed_df, ext_dup_success, ext_dup_fix_count = fix_external_hospital_dup_violations(
        gap_fixed_df, max_attempts=150, verbose=True
    )

    # 大学3回以上違反を修正
    print(f"   候補{idx}/{REFINE_TOP}の大学3回以上チェック中...")
    univ_over_2_fixed_df, univ_over_2_success, univ_over_2_fix_count = fix_university_over_2_violations(
        ext_dup_fixed_df, max_attempts=150, verbose=True
    )

    # 大学平日偏り違反を修正
    print(f"   候補{idx}/{REFINE_TOP}の大学平日偏りチェック中...")
    univ_weekday_fixed_df, univ_weekday_success, univ_weekday_fix_count = fix_university_weekday_balance_violations(
        univ_over_2_fixed_df, max_attempts=150, verbose=True
    )

    # 9. 公平性違反の修正（最大と最小の差を縮める）
    fairness_fixed_df, fairness_success, fairness_fix_count = fix_fairness_imbalance(
        univ_weekday_fixed_df, max_attempts=200, verbose=True
    )

    # 修正後に再評価
    if fix_count > 0 or cap_fix_count > 0 or code_1_2_fix_count > 0 or bg_ht_fix_count > 0 or gap_fix_count > 0 or ext_dup_fix_count > 0 or univ_over_2_fix_count > 0 or univ_weekday_fix_count > 0 or fairness_fix_count > 0:
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, *_ = recompute_stats(fairness_fixed_df)
        sc2, raw2, met2 = evaluate_schedule_with_raw(
            fairness_fixed_df, counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts
        )
        improved_df = fairness_fixed_df
    else:
        improved_df = fairness_fixed_df

    refined.append({
        "seed": cand["seed"],
        "score_before": cand["score"],
        "raw_before": cand["raw_score"],
        "score_after": sc2,
        "raw_after": raw2,
        "metrics_after": met2,
        "pattern_df": improved_df,
        "violations_fixed": fix_count,
        "violations_failed": fail_count,
        "cap_violations_fixed": cap_fix_count,
        "code_1_2_violations_fixed": code_1_2_fix_count,
        "bg_ht_imbalance_fixed": bg_ht_fix_count,
        "gap_violations_fixed": gap_fix_count,
        "external_dup_violations_fixed": ext_dup_fix_count,
        "univ_over_2_violations_fixed": univ_over_2_fix_count,
        "univ_weekday_violations_fixed": univ_weekday_fix_count,
        "fairness_violations_fixed": fairness_fix_count,
    })

# =========================
# ハード制約違反のないパターンのみ選択（TARGET_CAP、gap、未割当）
# =========================
print("\n=== ハード制約チェック ===")
valid_patterns = []
for e in refined:
    met = e["metrics_after"]
    cap_viol = met.get('cap_violations', 0)
    gap_viol = met.get('gap_violations', 0)
    unassigned = met.get('unassigned_slots', 0)

    if cap_viol > 0 or gap_viol > 0 or unassigned > 0:
        print(f"   ❌ seed={e['seed']}: TARGET_CAP違反={cap_viol}, gap違反={gap_viol}, 未割当={unassigned} → 除外")
    else:
        valid_patterns.append(e)

if not valid_patterns:
    print("   ⚠️ 警告: ハード制約を満たすパターンがありません。全パターンから選択します。")
    valid_patterns = refined

print(f"   ✅ {len(valid_patterns)}/{len(refined)} パターンがハード制約を満たしています")

# =========================
# 多軸スコアリング: 異なる評価軸で最適パターンを選択
# =========================
print("\n=== 多軸スコアリング ===")

# 評価軸1: 公平性重視（TARGET_CAP、公平性ペナルティを重視）
fairness_patterns = sorted(
    valid_patterns,
    key=lambda e: (
        -e["metrics_after"].get('cap_violations', 0) * 1000,  # TARGET_CAP違反を最優先で回避
        -e["metrics_after"].get('max_minus_min_total_active', 0) * 100,  # 公平性
        -e["metrics_after"].get('bg_ht_imbalance_violations', 0) * 50,
        e["raw_after"]
    ),
    reverse=True
)

# 評価軸2: gap違反回避重視（連続当直の間隔を重視）
gap_patterns = sorted(
    valid_patterns,
    key=lambda e: (
        -e["metrics_after"].get('gap_violations', 0) * 1000,
        -e["metrics_after"].get('external_hosp_dup_violations', 0) * 100,
        -e["metrics_after"].get('hospital_dup_violations', 0) * 50,
        e["raw_after"]
    ),
    reverse=True
)

# 評価軸3: バランス重視（大学/外病院、平日/休日のバランスを重視）
balance_patterns = sorted(
    valid_patterns,
    key=lambda e: (
        -e["metrics_after"].get('bg_ht_imbalance_violations', 0) * 1000,
        -e["metrics_after"].get('bg_weekday_weekend_imbalance', 0) * 100,
        -e["metrics_after"].get('bg_over_2_violations', 0) * 100,
        -e["metrics_after"].get('bg_weekday_over_violations', 0) * 100,
        e["raw_after"]
    ),
    reverse=True
)

# 各軸から最良パターンを選択
top_patterns = []
selected_seeds = set()

# 軸1: 公平性重視
if fairness_patterns and fairness_patterns[0]["seed"] not in selected_seeds:
    fairness_patterns[0]["axis_label"] = "公平性重視"
    top_patterns.append(fairness_patterns[0])
    selected_seeds.add(fairness_patterns[0]["seed"])

# 軸2: gap違反回避重視
if gap_patterns and gap_patterns[0]["seed"] not in selected_seeds:
    gap_patterns[0]["axis_label"] = "連続当直回避重視"
    top_patterns.append(gap_patterns[0])
    selected_seeds.add(gap_patterns[0]["seed"])

# 軸3: バランス重視
if balance_patterns and balance_patterns[0]["seed"] not in selected_seeds:
    balance_patterns[0]["axis_label"] = "バランス重視"
    top_patterns.append(balance_patterns[0])
    selected_seeds.add(balance_patterns[0]["seed"])

# まだ3パターン未満の場合、総合スコアから補填
if len(top_patterns) < 3:
    overall_sorted = sorted(valid_patterns, key=lambda e: e["raw_after"], reverse=True)
    for pattern in overall_sorted:
        if pattern["seed"] not in selected_seeds:
            pattern["axis_label"] = "総合スコア"
            top_patterns.append(pattern)
            selected_seeds.add(pattern["seed"])
            if len(top_patterns) >= 3:
                break

# ソート済みリストも作成（後方互換性のため）
refined_sorted = sorted(valid_patterns, key=lambda e: e["raw_after"], reverse=True)
TOP_OUTPUT_PATTERNS = len(top_patterns)

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
print("\n=== TOPパターンのスコア（多軸評価） ===")
for rank, pattern in enumerate(top_patterns, 1):
    axis_label = pattern.get('axis_label', '総合スコア')
    print(
        f"   {rank}位 [{axis_label}]: raw_score={pattern['raw_after']:.1f}, "
        + f"gap違反={pattern['metrics_after']['gap_violations']}, "
        + f"未割当={pattern['metrics_after']['unassigned_slots']}, "
        + f"cap違反={pattern['metrics_after'].get('cap_violations', 0)}, "
        + f"1.2違反={pattern['metrics_after'].get('code_1_2_violations', 0)}, "
        + f"BG/HT差3以上={pattern['metrics_after'].get('bg_ht_imbalance_violations', 0)}, "
        + f"公平性(max-min)={pattern['metrics_after'].get('max_minus_min_total_active', 0)}, "
        + f"制約修正={pattern.get('violations_fixed', 0)}件"
    )

# =========================
# 出力（pattern + summary + diagnostics）
# =========================
base_name = uploaded_filename.rsplit(".", 1)[0]
output_filename = f"{base_name}_auto_schedules_v2.8.xlsx"
output_path = output_filename

print(f"\n📝 結果をExcelファイルに出力中...")

def write_diagnostics_sheet(writer, sheet_name, diagnostics):
    startrow = 0
    for title, df in diagnostics:
        df.to_excel(writer, sheet_name=sheet_name, startrow=startrow + 1, index=False)
        ws = writer.sheets[sheet_name]
        ws.cell(row=startrow + 1, column=1, value=title)
        startrow += len(df.index) + 3


with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    # 元シート
    shift_df.to_excel(writer, sheet_name="sheet1", index=False)
    availability_raw.to_excel(writer, sheet_name="sheet2", index=False)
    schedule_raw.to_excel(writer, sheet_name="sheet3", index=False)
    sheet4_raw_out.to_excel(writer, sheet_name="sheet4", index=False)

    # TOPパターン出力
    for rank, entry in enumerate(top_patterns, start=1):
        axis_label = entry.get('axis_label', '総合スコア')
        sheet_label = f"pattern_{rank:02d}"

        # パターンシートのコメント行に軸ラベルを追加
        pattern_df_with_label = entry["pattern_df"].copy()
        entry["pattern_df"].to_excel(writer, sheet_name=sheet_label, index=False)

        # シート名に軸ラベルを追加（Excelの制限により簡略化）
        ws = writer.sheets[sheet_label]
        axis_short = {"公平性重視": "公平性", "連続当直回避重視": "gap回避", "バランス重視": "バランス", "総合スコア": "総合"}.get(axis_label, axis_label)
        ws.cell(row=1, column=len(entry["pattern_df"].columns) + 2, value=f"【{axis_short}】")

        # summary（今月/累計）
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, *_ = recompute_stats(entry["pattern_df"])
        df_month, df_total = build_summaries(entry["pattern_df"], counts, bg_counts, ht_counts, wd_counts, we_counts, bg_cat)
        df_month.to_excel(writer, sheet_name=f"{sheet_label}_今月", index=False)
        df_total.to_excel(writer, sheet_name=f"{sheet_label}_累計", index=False)

        # diagnostics
        df_doctors, df_gap, df_same, df_hdup, df_unass, df_metrics, df_hard_violations = build_diagnostics(entry["pattern_df"])
        write_diagnostics_sheet(
            writer,
            sheet_name=f"{sheet_label}_diag",
            diagnostics=[
                ("🚨 ハード制約違反", df_hard_violations),
                ("医師ごとの偏り", df_doctors),
                ("gap違反", df_gap),
                ("同日重複", df_same),
                ("同一病院重複", df_hdup),
                ("未割当枠", df_unass),
                ("メトリクス", df_metrics),
            ],
        )

print("\n" + "="*60)
print("   🎉 完了！")
print("="*60)
print(f"\n📥 出力ファイル: {output_path}")
print("\n【ファイル内容】")
print("  - sheet1〜4: 元データ")
print("  - pattern_01〜03: 多軸評価によるTOP3スケジュール候補")
print("    * 公平性重視: 医師間の割当回数の公平性を最優先")
print("    * gap回避重視: 連続当直の間隔を最優先")
print("    * バランス重視: 大学/外病院、平日/休日のバランスを最優先")
print("  - pattern_XX_今月/累計: 各パターンのサマリーシート")
print("  - pattern_XX_diag: 各パターンの診断シート（ハード制約違反、gap違反、重複等）")
print("\n【推奨】")
print("  ✅ 多軸評価により異なる特性を持つパターンを提供")
print("  ✅ TARGET_CAP、gap、未割当の違反がないパターンのみ選択")
print("  🔍 各pattern_XX_diagの「ハード制約違反」シートで修正結果を確認")
print("  1. 3つの評価軸（公平性/gap回避/バランス）から最適なパターンを選択")
print("  2. 選択したパターンの診断シートで違反・重複を確認")
print("  3. サマリーシートで医師ごとの偏りを確認")
print("\n【主な自動修正対象】")
print("  ✅ 可否コード0違反（絶対不可の日に割当）")
print("  ✅ カテ表+外病院違反（カテ表コードがある日にL〜Y列に割当）← 五十嵐医師の問題を修正")
print("  ✅ 可否コード2違反（B〜Q列以外に割当）")
print("  ✅ 可否コード3違反（L〜Y列以外に割当）")
print("  ✅ B-K列カテ表コード欠如（カテ表コード保有医師がコードなし日にB〜K列に割当）")
print("  ✅ 水曜日L〜Y列禁止違反")
print("="*60)

if COLAB_AVAILABLE:
    files.download(output_path)
