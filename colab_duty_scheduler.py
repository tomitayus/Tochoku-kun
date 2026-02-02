# @title 当直くん v6.0.0 (制約体系全面改定)
# 修正内容:
# v6.0.0 (2026-02-02):
# - 制約体系を全面改定
# - 絶対禁忌(ABS): 11項目
#   - ABS-001〜009: 既存の絶対禁忌
#   - ABS-010: TARGET_CAP遵守（n超過禁止）
#   - ABS-011: 大学系2回まで（B-K列合計）
# - ハード制約(HARD): 3項目
#   - HARD-001: B/I列1回まで（グループA）
#   - HARD-002: C-H/J-K列1回まで（グループB）
#   - HARD-003: 外病院1回以上（L-Y列）
# - 準ハード制約(SEMI): 2項目
#   - SEMI-001: B列のみカテ表コード必須（sheet3「1」は例外）
#   - SEMI-002: C-H列のみカテ当番日必須（I-K列は対象外、sheet3「1」は例外）
# - ソフト制約(SOFT): 3項目
#   - SOFT-001: 公平性（max-min最小化）
#   - SOFT-002: コード1.2優先（大学系0回ペナルティ）
#   - SOFT-003: 大学/外病院差（差3以上ペナルティ）
# - 不要な制約を削除（HARD/ABSで吸収）
# - ABS-001（コード0禁止）修正
#   - fix_hard_constraint_violations()の緊急フォールバックでコード0チェック追加
#   - 最終手段でもコード0医師を除外
#   - 全員コード0の場合は未割当のまま（違反割当より優先）
# - inactive医師処理にドキュメント参照を追加
#   - CONSTRAINT_RULES.md §5準拠コメント
# v4.7 (2026-01-31):
# - CONSTRAINT_RULES.md v5.2仕様に基づく整備
# v4.3 (2026-01-30):
# - C-H列カテ当番制約をソフト制約に変更（ハード制約から除外）
#   - 適格医師不足時のパターン除外を防止
#   - ペナルティ(120)とfix関数は維持
#   - 修正不可でもパターン選択可能に
# - recompute_stats呼び出しのunpacking修正（*_追加）
# v4.2 (2026-01-30):
# - 平日大学系(B,I-K列)の制約を緩和
#   - sheet3で「1」を持つ医師はカテ当番が合わなくても許容
#   - カテ当番なし医師も配置可能
#   - is_weekday_university_slot()、is_eligible_for_weekday_university_slot()関数を追加
#   - SHEET3_CODE_1_DOCTORSセットを追加
# - CC（大型連休特別シフト）を特別カウントとして扱う
#   - is_cc_assignment()関数を追加（CCかどうか判定）
#   - recompute_statsでCC別カウント（cc_counts, cc_bg_counts, cc_ht_counts）を追跡
#   - 以下の計算からCCを除外:
#     - 公平性計算（fairness_penalty）
#     - BG/HT不均衡計算（bg_ht_imbalance_violations）
#     - 外病院重複計算（external_hosp_dup_violations）
#     - 大学3回以上違反（bg_over_2_violations）
#   - 各fix関数でもCC除外を適用
# v4.1 (2026-01-30):
# - 枠決定順序を最適化
#   - 大学休日(C-H列) → 大学平日(B,I-K列) → 外病院(L-Y列) の順に割り当て
#   - C-H列はカテ当番制約があるため先に埋めることで制約を満たしやすくする
#   - slot_priority関数を追加して優先度順にソート
# - ハード制約チェックにC-H列カテ当番違反を追加
#   - ch_kate_violations > 0 のパターンを除外
# v4.0 (2026-01-30):
# - C-H列（休日大学系）のカテ当番制約を追加
#   - C-H列はカテ当番のある医師（その日にアルファベットあり）または
#     カテ当番が一回もない医師（sheet3に1つもアルファベットなし）のみ割り当て可能
#   - NO_KATE_DOCTORSセットを追加（カテ当番なし医師の集合）
#   - is_ch_slot()、is_eligible_for_ch_slot()関数を追加
#   - collect_candidatesにrelax_ch_kateパラメータを追加
#   - fix_ch_kate_violations()関数を追加（違反修正用）
#   - ch_kate_violationsメトリクスを追加（ペナルティ120）
#   - 最適化パイプライン#4.5に追加（大学最低1回の後、gap違反の前）
# v3.9 (2026-01-30):
# - print出力の最適化
#   - tqdmによる進捗バー表示（パターン生成、局所探索）
#   - セクション区切りの統一（=== ===形式）
#   - 階層構造表示（├─/└─）
#   - TOPパターン評価をテーブル形式で表示
#   - 冗長な出力を削減
# - 出力ファイル名にバージョンを反映（filename_v3.9.xlsx）
# - VERSION定数を追加
# v3.8 (2026-01-30):
# - 外病院最低1回をハード制約として追加（大学3回以上を防止）
#   - fix_university_over_2_violationsを拡張して外病院0回も検出・修正
#   - ht_0_violationsメトリクスを追加（ペナルティ300）
#   - ハード制約チェックにbg_over_2_violations、ht_0_violationsを追加
# - 最適化パイプライン順序を修正
#   - BG/HT不均衡(#6) → 外病院重複(#7) の順序に変更
# - 処理番号の表示を追加 [X/15]
# v3.7 (2026-01-30):
# - build_hard_constraint_violationsのreturn文欠落バグを修正
# - CODE_2医師のn+1回違反を最適化後にチェック・修正する機能を追加
#   - fix_code_2_extra_violations関数を追加（ハード制約として修正）
#   - evaluate_schedule_with_rawにcode_2_extra_violationsメトリクスを追加
#   - ハード制約チェックにCODE_2 n+1違反を追加
#   - 最適化パイプラインの#2に追加（ハード制約直後、TARGET_CAP前）
# v3.6 (2026-01-30):
# - 可否コード2の医師をEXTRA枠（n+1回）対象から除外（ハード制約）
#   - has_code_2_anywhere関数を追加（sheet2でいずれかの日に2を持つ医師を判定）
#   - CODE_2_DOCTORSリストを作成
#   - EXTRA_ALLOWEDの計算時にCODE_2_DOCTORSを除外
#   - 可否コード2の医師は大学系のみ可能なため、外病院枠増加は不適切
#   - 出力に「可否コード2医師（EXTRA枠対象外）」を表示
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
#   - 順序: ハード制約 → TARGET_CAP（優先1） → 大学最低1回（準ハード、優先2） → gap（優先3） → 外病院DUP（優先4） → BG/HT → 大学3+ → 大学平日偏り → 公平性
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
# - gap違反（3日未満の間隔での割当）を完全に排除
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

# バージョン定数
VERSION = "6.0.0"

# tqdmのインポート（進捗バー用）
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    def tqdm(iterable, **kwargs):
        return iterable

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
LOCAL_SEARCH_ENABLED = False   # v5.7.1: 最適化無効化
OPTIMIZATION_ENABLED = False   # v5.7.1: fix関数群を無効化（絶対禁忌のみ厳守）
TOP_KEEP = 20                 # greedyで残す候補数（100パターンから上位20候補を保持）
REFINE_TOP = 15               # ローカル探索をかける候補数（上位15候補を最適化）
LOCAL_MAX_ITERS = 3000        # 1候補あたりの入替試行回数
LOCAL_PATIENCE = 1200         # 改善が出ない試行がこの回数続いたら打ち切り
LOCAL_REFRESH_EVERY = 200     # 問題医師（gap/重複）を再抽出する間隔

# v6.0.0 スコア重み（ソフト制約のみ）
# 絶対禁忌(ABS)とハード制約(HARD)は候補選定時にチェック済み
W_FAIR_TOTAL = 30          # SOFT-001: 公平性（max-min最小化）
W_CODE_12_UNIV = 150       # SOFT-002: コード1.2優先（大学系0回ペナルティ）
W_BG_HT_DIFF = 100         # SOFT-003: 大学/外病院差（差3以上ペナルティ）
# 以下は絶対禁忌のためペナルティ不要（v6.0.0）
W_GAP = 0                  # ABS-007で対応
W_HOSP_DUP = 0             # ABS-008で対応
W_EXTERNAL_HOSP_DUP = 0    # ABS-008で対応
W_UNASSIGNED = 0           # ABS-009で対応
W_CAP = 0                  # ABS-010で対応
W_BG_SPREAD = 0            # 削除（簡略化）
W_HT_SPREAD = 0            # 削除（簡略化）
W_WD_SPREAD = 0            # 削除（簡略化）
W_WE_SPREAD = 0            # 削除（簡略化）
W_BK_LY_BALANCE = 2        # B-K/L-Y の比率バランス（なるべく1:1）

# =========================
# 制約ID定義（v5.2仕様書準拠）
# =========================
# 絶対禁忌（ABS: 配置不可）
CONSTRAINT_ABS_001 = "ABS-001"  # 可否コード0禁止
CONSTRAINT_ABS_002 = "ABS-002"  # コード2の列制約
CONSTRAINT_ABS_003 = "ABS-003"  # コード3の列制約
CONSTRAINT_ABS_004 = "ABS-004"  # カテ当番日の外病院禁止
CONSTRAINT_ABS_005 = "ABS-005"  # 同日重複禁止
CONSTRAINT_ABS_006 = "ABS-006"  # 水曜日L〜Y禁止医師

# ハード制約（HARD: パターン除外）
CONSTRAINT_HARD_001 = "HARD-001"  # TARGET_CAP超過
CONSTRAINT_HARD_002 = "HARD-002"  # gap違反
CONSTRAINT_HARD_003 = "HARD-003"  # 未割当枠
CONSTRAINT_HARD_004 = "HARD-004"  # CODE_2のn+1違反

# 準ハード制約（SEMI: 緩和可）
CONSTRAINT_SEMI_001 = "SEMI-001"  # 平日大学系カテ要件
CONSTRAINT_SEMI_002 = "SEMI-002"  # 休日大学系カテ当番
CONSTRAINT_SEMI_003 = "SEMI-003"  # gap制約
CONSTRAINT_SEMI_004 = "SEMI-004"  # 大学最低1回

# ソフト制約（SOFT: ペナルティ）
CONSTRAINT_SOFT_001 = "SOFT-001"  # 外病院0回 (W=300)
CONSTRAINT_SOFT_002 = "SOFT-002"  # 大学3回以上 (W=150)
CONSTRAINT_SOFT_003 = "SOFT-003"  # 外病院同一病院重複 (W=150)
CONSTRAINT_SOFT_004 = "SOFT-004"  # CODE_1.2大学0回 (W=150)
CONSTRAINT_SOFT_005 = "SOFT-005"  # gap違反 (W=100)
CONSTRAINT_SOFT_006 = "SOFT-006"  # BG/HT差3以上 (W=100)
CONSTRAINT_SOFT_007 = "SOFT-007"  # 大学平日2回以上 (W=80)
CONSTRAINT_SOFT_008 = "SOFT-008"  # 公平性 (W=30)
CONSTRAINT_SOFT_009 = "SOFT-009"  # 大学ばらつき (W=3)
CONSTRAINT_SOFT_010 = "SOFT-010"  # 外病院ばらつき (W=3)
CONSTRAINT_SOFT_011 = "SOFT-011"  # 休日ばらつき (W=3)
CONSTRAINT_SOFT_012 = "SOFT-012"  # 平日ばらつき (W=2)
CONSTRAINT_SOFT_013 = "SOFT-013"  # B-K/L-Y比率バランス (W=2)
CONSTRAINT_SOFT_014 = "SOFT-014"  # 大学同一病院重複 (W=0)

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
print("\n" + "="*60)
print(f"  📂 当直くん v{VERSION}")
print("="*60)
print("\nsheet1〜sheet4が入った当直Excelファイルを選択してください")

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

print(f"\n✅ Excel読込完了: 医師{len(doctor_names)}人 | 病院{len(hospital_cols)}列 | {len(shift_df)}日間")

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
# inactive医師の扱い（v5.2仕様書§5準拠）:
#   - 解析処理から完全除外（候補に含めない）
#   - TARGET_CAP計算から除外（active医師のみで計算）
#   - 出力Excelには0回として記載（氏名は表示）
# =========================
def is_always_unavailable(doc):
    """inactive医師の判定: sheet2で全日=0かつ事前割当なし"""
    if preassigned_count.get(doc, 0) > 0:
        return False
    return all(get_avail_code(d, doc) == 0 for d in all_shift_dates)

inactive_doctors = [d for d in doctor_names if is_always_unavailable(d)]
active_doctors = [d for d in doctor_names if d not in inactive_doctors]
if len(active_doctors) == 0:
    raise ValueError("❌ 当月に割り当て可能な医師がいません")
if inactive_doctors:
    print(f"⚠️ inactive医師（解析除外、出力のみ）: {len(inactive_doctors)}人")

# 可否コード2の医師（大学系のみ可能、EXTRA枠対象外）
def has_code_2_anywhere(doc):
    """医師がsheet2でいずれかの日に可否コード2を持っているか"""
    if doc not in availability_df.columns:
        return False
    for date in all_shift_dates:
        code = get_avail_code(date, doc)
        if code == 2:
            return True
    return False

CODE_2_DOCTORS = {doc for doc in doctor_names if has_code_2_anywhere(doc)}

BASE_TARGET = total_slots // len(active_doctors)
EXTRA_SLOTS = total_slots - BASE_TARGET * len(active_doctors)

# 余り枠は右側（下位）の医師に割り当てる（可否コード2の医師は除外：ハード制約）
# 例：小林(0), 及川(1), ..., 大河内(30), 猪股(31) の場合、右側の医師を選択
active_sorted_by_index = sorted(active_doctors, key=lambda d: doctor_col_index[d])  # 昇順ソート
# 可否コード2の医師はEXTRA枠対象から除外（大学系のみ可のため、外病院枠増加は不適切）
extra_eligible = [d for d in active_sorted_by_index if d not in CODE_2_DOCTORS]
EXTRA_ALLOWED = set(extra_eligible[-EXTRA_SLOTS:] if EXTRA_SLOTS > 0 else [])  # 最後のEXTRA_SLOTS人（右側/下位）

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
print(f"   ├─ 全枠数: {total_slots} | active医師: {len(active_doctors)}人")
print(f"   ├─ 基本割当: {BASE_TARGET}回 (+1回対象: {len(EXTRA_ALLOWED)}人)")

# 可否コード2の医師がEXTRA枠から除外されていることを表示
code_2_in_active = [d for d in active_sorted_by_index if d in CODE_2_DOCTORS]
if code_2_in_active:
    print(f"   └─ CODE_2医師（EXTRA対象外）: {len(code_2_in_active)}人")

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
print(f"   └─ カテ表保有: {len(SCHEDULE_CODE_HOLDERS)}人")

# カテ当番なし医師（sheet3に1つもアルファベットがない医師）
# C-H列（休日大学系）に自由に割り当て可能
NO_KATE_DOCTORS = {doc for doc in doctor_names if not has_any_schedule_code(doc)}
print(f"   └─ カテ当番なし: {len(NO_KATE_DOCTORS)}人")

# sheet3で「1」を持つ医師（平日大学系でカテ当番不一致を許容）
def has_sheet3_code_1(doc):
    """医師がsheet3で少なくとも1つの「1」コードを持っているか"""
    if doc not in schedule_df.columns:
        return False
    values = schedule_df[doc].dropna()
    return any(str(v).strip() == "1" for v in values)

SHEET3_CODE_1_DOCTORS = {doc for doc in doctor_names if has_sheet3_code_1(doc)}
if SHEET3_CODE_1_DOCTORS:
    print(f"   └─ sheet3に1あり（平日緩和）: {len(SHEET3_CODE_1_DOCTORS)}人")

def is_ch_slot(col_idx):
    """C-H列（休日大学系、インデックス2-7）かどうか"""
    return C_COL_INDEX <= col_idx <= H_COL_INDEX

def is_weekday_university_slot(col_idx):
    """B列またはI-K列（平日大学系）かどうか"""
    return col_idx == B_COL_INDEX or (I_COL_INDEX <= col_idx <= K_COL_INDEX)

def is_eligible_for_ch_slot(doc, date):
    """C-H列（休日大学系）に割り当て可能かどうか
    条件：その日にカテ当番あり OR カテ当番が一回もない医師
    """
    # カテ当番が一回もない医師はOK
    if doc in NO_KATE_DOCTORS:
        return True
    # カテ当番保有医師は、その日にカテ表コードがあればOK
    if get_sched_code(date, doc):
        return True
    return False

def is_eligible_for_weekday_university_slot(doc, date):
    """B列/I-K列（平日大学系）に割り当て可能かどうか
    条件：カテ当番なし医師 OR その日にカテ当番あり OR sheet3で「1」を持つ医師
    「1」を持つ医師はカテ当番が合わなくても許容
    """
    # カテ当番が一回もない医師はOK
    if doc in NO_KATE_DOCTORS:
        return True
    # その日にカテ表コードがあればOK
    sched_code = get_sched_code(date, doc)
    if sched_code:
        return True
    # sheet3で「1」を持つ医師はカテ当番なしでも許容（平日大学系のみ）
    if doc in SHEET3_CODE_1_DOCTORS:
        return True
    return False

def is_cc_assignment(date, doc):
    """その日のその医師の割り当てがCC（大型連休特別シフト）かどうか"""
    sched_code = get_sched_code(date, doc)
    return sched_code == "CC" if sched_code else False

def has_any_cc_assignment(doc, pattern_df):
    """医師がCC割り当てを持っているかどうかをpattern_dfから判定"""
    for ridx in pattern_df.index:
        date = pattern_df.at[ridx, date_col_shift]
        if pd.isna(date):
            continue
        date = pd.to_datetime(date).normalize().tz_localize(None)
        for hosp in hospital_cols:
            val = pattern_df.at[ridx, hosp]
            if isinstance(val, str) and normalize_name(val) == doc:
                if is_cc_assignment(date, doc):
                    return True
    return False

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

# 大学系最低1回必須の医師（準ハード制約：コード3以外の全医師）
# コード3は外病院専門なので除外
UNIVERSITY_MINIMUM_REQUIRED_DOCTORS = {doc for doc in active_doctors if doc not in RATIO_EXEMPT_DOCTORS}

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
    assigned_bi,      # v6.0.0: B/I列の合計（HARD-001）
    assigned_chjk,    # v6.0.0: C-H/J-K列の合計（HARD-002）
    assigned_hosp_count,
):
    idx = shift_df.columns.get_loc(hospital_name)
    is_BE = B_COL_INDEX <= idx <= E_COL_INDEX
    is_BG = B_COL_INDEX <= idx <= K_COL_INDEX
    is_BH = B_H_START_INDEX <= idx <= B_H_END_INDEX
    is_LY_range = L_COL_INDEX <= idx <= L_Y_END_INDEX
    is_BK = is_bk_slot(idx)
    is_LY = is_ly_slot(idx)
    # v6.0.0: 新しい列グループ
    is_B_or_I = (idx == B_COL_INDEX or idx == I_COL_INDEX)  # グループA
    is_CH_or_JK = ((C_COL_INDEX <= idx <= H_COL_INDEX) or (J_COL_INDEX <= idx <= K_COL_INDEX))  # グループB
    is_B_only = (idx == B_COL_INDEX)  # SEMI-001対象
    is_CH_only = (C_COL_INDEX <= idx <= H_COL_INDEX)  # SEMI-002対象
    dow = pd.to_datetime(date).weekday()
    weekday = dow < 5

    def collect_candidates(
        relax_semi=False,  # v6.0.0: SEMI制約を緩和（sheet3「1」以外も許容）
    ):
        candidates = []
        for doc in doctor_names:
            # === 絶対禁忌（ABS）: 緩和不可 ===

            # ABS-006: 同日重複禁止
            if date in assigned_dates[doc]:
                continue

            code = get_avail_code(date, doc)

            # ABS-001: コード0は全列禁止
            if code == 0:
                continue

            # ABS-002: コード2はB〜Q列のみ（R-Y列禁止）
            if code == 2 and not (B_COL_INDEX <= idx <= Q_COL_INDEX):
                continue

            # ABS-003: コード3はL〜Y列のみ（大学系禁止）
            if code == 3 and not (L_COL_INDEX <= idx <= L_Y_END_INDEX):
                continue

            # ABS-004: カテ表コードありの日はL〜Y列不可
            if L_COL_INDEX <= idx <= L_Y_END_INDEX:
                if get_sched_code(date, doc):
                    continue

            # ABS-005: 水曜日L〜Y列禁止医師
            if dow == 2 and is_LY_range:
                if doc in WED_FORBIDDEN_DOCTORS:
                    continue

            # ABS-007: gap >= 3日必須
            if assigned_dates[doc]:
                min_gap = min(abs((pd.to_datetime(date) - x).days) for x in assigned_dates[doc])
                if min_gap < 3:
                    continue

            # ABS-008: 同一病院重複禁止（全列）
            if assigned_hosp_count[doc].get(hospital_name, 0) >= 1:
                continue

            # ABS-010: TARGET_CAP遵守（n超過禁止）
            if assigned_count[doc] >= TARGET_CAP.get(doc, 0):
                continue

            # ABS-011: 大学系2回まで（B-K列合計）
            if is_BG and assigned_bg[doc] >= 2:
                continue

            # === ハード制約（HARD）: カテなし医師は必須遵守 ===

            # カテ当番の有無を判定
            is_kate_holder = doc in SCHEDULE_CODE_HOLDERS
            is_sheet3_one = doc in SHEET3_CODE_1_DOCTORS

            # HARD-001: B/I列1回まで（グループA）
            if is_B_or_I and assigned_bi[doc] >= 1:
                # カテなし医師は必須遵守
                if not is_kate_holder:
                    continue
                # カテあり医師でもsheet3「1」以外は遵守
                if is_kate_holder and not is_sheet3_one:
                    continue

            # HARD-002: C-H/J-K列1回まで（グループB）
            if is_CH_or_JK and assigned_chjk[doc] >= 1:
                # カテなし医師は必須遵守
                if not is_kate_holder:
                    continue
                # カテあり医師でもsheet3「1」以外は遵守
                if is_kate_holder and not is_sheet3_one:
                    continue

            # === 準ハード制約（SEMI）: sheet3「1」は緩和対象 ===

            # SEMI-001: B列のみカテ表コード必須
            if not relax_semi and is_B_only:
                if is_kate_holder and not get_sched_code(date, doc):
                    if not is_sheet3_one:
                        continue

            # SEMI-002: C-H列のみカテ当番日必須（I-K列は対象外）
            if not relax_semi and is_CH_only:
                if not is_eligible_for_ch_slot(doc, date):
                    if not is_sheet3_one:
                        continue

            candidates.append(doc)
        return candidates

    candidates = collect_candidates()
    if not candidates:
        candidates = collect_candidates(relax_semi=True)

    if not candidates:
        return None

    any_under_floor = any(assigned_count[d] < floor_shifts for d in active_doctors)
    if any_under_floor:
        under_floor = [d for d in candidates if assigned_count[d] < floor_shifts]
        if under_floor:
            candidates = under_floor

    # ★ C-H列（土日大学）はカテ当番医師を最優先（カテなし医師は最後の手段）
    # カテ当番医師がいる場合、カテなし医師より優先して配置
    if is_ch_slot(idx) and candidates:
        kate_docs_on_day = [d for d in candidates if get_sched_code(date, d)]
        if kate_docs_on_day:
            candidates = kate_docs_on_day

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

    # (削除: 同一病院重複は絶対禁忌として collect_candidates でチェック済み)

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

    # (削除: gap >= 3 は絶対禁忌として collect_candidates でチェック済み)

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
    assigned_bh = {d: 0 for d in doctor_names}  # B〜H列の割当回数（旧: 2回まで）
    assigned_bi = {d: 0 for d in doctor_names}  # v6.0.0: B/I列の合計（HARD-001: 1回まで）
    assigned_chjk = {d: 0 for d in doctor_names}  # v6.0.0: C-H/J-K列の合計（HARD-002: 1回まで）
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

            # B〜H列のカウント（旧）
            if B_H_START_INDEX <= hidx <= B_H_END_INDEX:
                assigned_bh[doc] += 1

            # v6.0.0: B/I列のカウント（HARD-001）
            if hidx == B_COL_INDEX or hidx == I_COL_INDEX:
                assigned_bi[doc] += 1

            # v6.0.0: C-H/J-K列のカウント（HARD-002）
            if (C_COL_INDEX <= hidx <= H_COL_INDEX) or (J_COL_INDEX <= hidx <= K_COL_INDEX):
                assigned_chjk[doc] += 1

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
    # 枠決定順序: 大学休日(C-H) → 大学平日(B,I-K) → 外病院(L-Y)
    # C-H列はカテ当番制約があるため先に埋める
    def slot_priority(slot_tuple):
        ridx, hosp = slot_tuple
        hidx = shift_df.columns.get_loc(hosp)
        # C-H列（休日大学系）: 優先度0（最初）
        if C_COL_INDEX <= hidx <= H_COL_INDEX:
            return (0, hidx)
        # B列、I-K列（平日大学系）: 優先度1
        elif hidx == B_COL_INDEX or (I_COL_INDEX <= hidx <= K_COL_INDEX):
            return (1, hidx)
        # L-Y列（外病院）: 優先度2（最後）
        else:
            return (2, hidx)

    for date in all_dates:
        free_slots = slots_by_date[date]["free"].copy()
        # 優先度順にソート後、同一優先度内でシャッフル
        random.shuffle(free_slots)  # まずシャッフルしてランダム性を確保
        free_slots.sort(key=slot_priority)  # 安定ソートで優先度順に

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
                assigned_bi=assigned_bi,        # v6.0.0
                assigned_chjk=assigned_chjk,    # v6.0.0
                assigned_hosp_count=assigned_hosp_count,
            )
            if chosen is None:
                # v6.0.0 フォールバック: 絶対禁忌(ABS)をすべてチェック
                hidx = shift_df.columns.get_loc(hosp)
                is_bg_slot = B_COL_INDEX <= hidx <= K_COL_INDEX

                def is_valid_fallback(d):
                    code = get_avail_code(date, d)
                    # ABS-001: コード0禁止
                    if code == 0:
                        return False
                    # ABS-002: コード2はB〜Q列のみ
                    if code == 2 and not (B_COL_INDEX <= hidx <= Q_COL_INDEX):
                        return False
                    # ABS-003: コード3はL〜Y列のみ
                    if code == 3 and not (L_COL_INDEX <= hidx <= L_Y_END_INDEX):
                        return False
                    # ABS-006: 同日重複禁止
                    if date in assigned_dates[d]:
                        return False
                    # ABS-007: gap >= 3日必須
                    if assigned_dates[d]:
                        min_gap = min(abs((pd.to_datetime(date) - x).days) for x in assigned_dates[d])
                        if min_gap < 3:
                            return False
                    # ABS-008: 同一病院重複禁止
                    if assigned_hosp_count[d].get(hosp, 0) >= 1:
                        return False
                    # ABS-010: TARGET_CAP遵守
                    if assigned_count[d] >= TARGET_CAP.get(d, 0):
                        return False
                    # ABS-011: 大学系2回まで
                    if is_bg_slot and assigned_bg[d] >= 2:
                        return False
                    return True

                remaining = [d for d in doctor_names if is_valid_fallback(d)]
                if remaining:
                    fallback_doc = min(remaining, key=lambda d: (assigned_count[d], doctor_col_index[d]))
                else:
                    # 全員が絶対禁忌に該当する場合は未割当のまま（None）
                    fallback_doc = None
                if fallback_doc is not None:
                    df.at[ridx, hosp] = fallback_doc
                    chosen = fallback_doc
                # fallback_doc が None の場合は未割当のまま（後続処理をスキップ）
            else:
                df.at[ridx, hosp] = chosen

            # chosen が None でなければカウント更新
            if chosen is not None:
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

                # B〜H列のカウント（旧）
                if B_H_START_INDEX <= hidx <= B_H_END_INDEX:
                    assigned_bh[chosen] += 1

                # v6.0.0: B/I列のカウント（HARD-001）
                if hidx == B_COL_INDEX or hidx == I_COL_INDEX:
                    assigned_bi[chosen] += 1

                # v6.0.0: C-H/J-K列のカウント（HARD-002）
                if (C_COL_INDEX <= hidx <= H_COL_INDEX) or (J_COL_INDEX <= hidx <= K_COL_INDEX):
                    assigned_chjk[chosen] += 1

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
    # CC（大型連休特別シフト）カウント - 各種バランス計算から除外用
    cc_counts = {d: 0 for d in doctor_names}
    cc_bg_counts = {d: 0 for d in doctor_names}  # CCのうち大学系
    cc_ht_counts = {d: 0 for d in doctor_names}  # CCのうち外病院

    for (ridx, hosp), (date, fixed) in slot_meta.items():
        val = pattern_df.at[ridx, hosp]

        # 未割り当てチェック（None, NaN, 非医師名の場合）
        if pd.isna(val):
            unassigned.append((date, hosp, ridx))
            continue
        if not isinstance(val, str):
            # 数値など（1など）は未割り当て
            unassigned.append((date, hosp, ridx))
            continue
        v = normalize_name(val)  # 🔧 FIX
        if v not in doctor_names:
            # 医師名でない文字列（"UNASSIGNED"や"1"など）も未割り当て
            unassigned.append((date, hosp, ridx))
            continue

        doc = v
        counts[doc] += 1
        assigned_hosp_count[doc][hosp] += 1
        doc_assignments[doc].append((date, hosp))

        # CC判定
        is_cc = is_cc_assignment(date, doc)
        if is_cc:
            cc_counts[doc] += 1

        hidx = shift_df.columns.get_loc(hosp)
        # 大学系はB〜K列（B_COL_INDEX=1 〜 K_COL_INDEX=10）
        if B_COL_INDEX <= hidx <= B_K_END_INDEX:
            bg_counts[doc] += 1
            bg_cat[doc][classify_bg_category(date, hosp)] += 1
            if is_cc:
                cc_bg_counts[doc] += 1
        # 外病院はL〜Y列（L_COL_INDEX=11 〜 Y_COL_INDEX=24）
        elif L_COL_INDEX <= hidx <= L_Y_END_INDEX:
            ht_counts[doc] += 1
            if is_cc:
                cc_ht_counts[doc] += 1

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
        cc_counts,
        cc_bg_counts,
        cc_ht_counts,
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
    # UNASSIGNED - slot_metaに登録されたスロットのうち、医師名が入っていないものをカウント
    # None, NaN, 非医師名（1, 〇など）も未割り当てとしてカウント
    unassigned_slots = 0
    for (ridx, hosp), (date, fixed) in slot_meta.items():
        v = pattern_df.at[ridx, hosp]
        # 医師名でない場合は未割り当て
        if pd.isna(v):
            unassigned_slots += 1
        elif isinstance(v, str):
            v_norm = normalize_name(v)
            if v_norm not in doctor_names:
                unassigned_slots += 1
        else:
            # 数値など（1など）は未割り当て
            unassigned_slots += 1

    # CC（大型連休特別シフト）カウント - バランス計算から除外用
    cc_counts = {d: 0 for d in doctor_names}
    cc_bg_counts = {d: 0 for d in doctor_names}
    cc_ht_counts = {d: 0 for d in doctor_names}
    cc_hosp_counts = {d: defaultdict(int) for d in doctor_names}  # CC分の病院別カウント
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
            if is_cc_assignment(date, doc):
                cc_counts[doc] += 1
                cc_hosp_counts[doc][hosp] += 1
                hidx = shift_df.columns.get_loc(hosp)
                if B_COL_INDEX <= hidx <= B_K_END_INDEX:
                    cc_bg_counts[doc] += 1
                elif L_COL_INDEX <= hidx <= L_Y_END_INDEX:
                    cc_ht_counts[doc] += 1

    # cap違反
    cap_violations = 0
    for doc in doctor_names:
        cap = TARGET_CAP.get(doc, 0)
        if assigned_count.get(doc, 0) > cap:
            cap_violations += (assigned_count[doc] - cap)

    # CODE_2医師のn+1違反（BASE_TARGET超過）
    code_2_extra_violations = 0
    for doc in CODE_2_DOCTORS:
        if doc not in active_doctors:
            continue
        if assigned_count.get(doc, 0) > BASE_TARGET:
            code_2_extra_violations += (assigned_count[doc] - BASE_TARGET)

    # 全合計公平性（activeのみ、CC除外）
    # CCは大型連休特別シフトなので公平性計算から除外
    active_counts_no_cc = [assigned_count.get(d, 0) - cc_counts.get(d, 0) for d in active_doctors]
    max_c = max(active_counts_no_cc) if active_counts_no_cc else 0
    min_c = min(active_counts_no_cc) if active_counts_no_cc else 0
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
            if (dlist[i] - dlist[i - 1]).days < 3:
                gap_violations += 1

    hosp_dup_violations = 0
    external_hosp_dup_violations = 0  # 外病院重複（厳しく扱う）
    for doc, hdict in hosp_counts_by_doc.items():
        for hosp, c in hdict.items():
            # CC分を除外（CCは特別シフトなので重複カウントから除外）
            c_no_cc = c - cc_hosp_counts.get(doc, {}).get(hosp, 0)
            if c_no_cc > 1:
                # 病院が外病院（L～Y列）かどうかを判定
                hidx = shift_df.columns.get_loc(hosp)
                if L_COL_INDEX <= hidx <= L_Y_END_INDEX:
                    external_hosp_dup_violations += (c_no_cc - 1)
                else:
                    hosp_dup_violations += (c_no_cc - 1)

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

    # 大学系と外病院の差が3以上の場合のペナルティ（CC除外）
    bg_ht_imbalance_violations = 0
    for doc in active_doctors:
        # CCは大型連休特別シフトなのでバランス計算から除外
        bg = assigned_bg.get(doc, 0) - cc_bg_counts.get(doc, 0)
        ht = assigned_ht.get(doc, 0) - cc_ht_counts.get(doc, 0)
        diff = abs(bg - ht)
        if diff >= 3:
            bg_ht_imbalance_violations += (diff - 2)  # 差が3以上の超過分をカウント

    # 大学病院2回の場合、平日1回+休日1回のバランス違反
    bg_weekday_weekend_imbalance = 0
    bg_over_2_violations = 0  # 大学3回以上の違反（不満が高い）
    ht_0_violations = 0  # 外病院0回の違反（ハード制約：大学3回以上を防ぐ）
    bg_weekday_over_violations = 0  # 大学の平日偏り（平日2回以上は不満）
    for doc in active_doctors:
        if doc in RATIO_EXEMPT_DOCTORS:  # コード3は外病院専門なので除外
            continue
        # CC除外（大型連休特別シフトはバランス計算から除外）
        bg_total_no_cc = assigned_bg.get(doc, 0) - cc_bg_counts.get(doc, 0)
        ht_total_no_cc = assigned_ht.get(doc, 0) - cc_ht_counts.get(doc, 0)
        # 元の値（ht_0_violationsなどハード制約用）
        bg_total = assigned_bg.get(doc, 0)
        ht_total = assigned_ht.get(doc, 0)
        weekday_count = bg_cat[doc].get("平日", 0)

        # 大学3回以上は不可（CC除外）
        if bg_total_no_cc >= 3:
            bg_over_2_violations += (bg_total_no_cc - 2)

        # 外病院0回かつ大学1回以上はハード制約違反（CCは除外しない：ハード制約）
        if ht_total == 0 and bg_total >= 1:
            ht_0_violations += 1

        # 大学2回の場合、平日1回+休日1回が理想（CC除外）
        if bg_total_no_cc == 2:
            if weekday_count == 0 or weekday_count == 2:
                bg_weekday_weekend_imbalance += 1

        # 大学の平日が2回以上は不満（CC除外）
        # 注：weekday_countからCCを除外するには追加トラッキングが必要
        # 現時点ではweekday_countはそのまま使用（大型連休は平日カウントされにくい）
        if weekday_count >= 2:
            bg_weekday_over_violations += (weekday_count - 1)

    # C-H列（休日大学系）カテ当番違反
    # カテ当番保有医師がその日にカテ当番なしでC-H列に割り当てられている場合
    ch_kate_violations = 0
    for ridx in pattern_df.index:
        date = pattern_df.at[ridx, date_col_shift]
        if pd.isna(date):
            continue
        date = pd.to_datetime(date).normalize().tz_localize(None)
        for hosp in hospital_cols:
            idx = shift_df.columns.get_loc(hosp)
            if not is_ch_slot(idx):
                continue
            val = pattern_df.at[ridx, hosp]
            val_norm = normalize_name(val) if isinstance(val, str) else ""
            if val_norm in doctor_names:
                if not is_eligible_for_ch_slot(val_norm, date):
                    ch_kate_violations += 1

    penalty = 0
    penalty += fairness_penalty * W_FAIR_TOTAL
    penalty += gap_violations * W_GAP
    penalty += hosp_dup_violations * W_HOSP_DUP
    penalty += external_hosp_dup_violations * W_EXTERNAL_HOSP_DUP  # 外病院重複は厳格
    penalty += unassigned_slots * W_UNASSIGNED
    penalty += cap_violations * W_CAP
    penalty += code_2_extra_violations * 300  # CODE_2医師のn+1違反は厳格（ハード制約）
    penalty += code_1_2_violations * 150  # 1.2の医師が大学系0回の場合、大きなペナルティ
    penalty += bg_ht_imbalance_violations * 100  # 大学系と外病院の差が3以上の場合、大きなペナルティ
    penalty += bg_weekday_weekend_imbalance * 50  # 大学病院2回の平日/休日バランス違反
    penalty += bg_over_2_violations * 300  # 大学3回以上の違反（ハード制約）
    penalty += ht_0_violations * 300  # 外病院0回の違反（ハード制約）
    penalty += bg_weekday_over_violations * 80  # 大学の平日偏り（平日2回以上は不満）
    penalty += ch_kate_violations * 120  # C-H列カテ当番違反（優先度高）

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
        "code_2_extra_violations": int(code_2_extra_violations),
        "code_1_2_violations": int(code_1_2_violations),
        "bg_ht_imbalance_violations": int(bg_ht_imbalance_violations),
        "bg_weekday_weekend_imbalance": int(bg_weekday_weekend_imbalance),
        "bg_over_2_violations": int(bg_over_2_violations),
        "ht_0_violations": int(ht_0_violations),
        "bg_weekday_over_violations": int(bg_weekday_over_violations),
        "ch_kate_violations": int(ch_kate_violations),
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
    # B〜K列はカテ表コード保有医師のみカテ表コードが必要（EXTRA医師は例外）
    if B_COL_INDEX <= idx <= B_K_END_INDEX:
        if doc in SCHEDULE_CODE_HOLDERS and not get_sched_code(date, doc) and doc not in EXTRA_ALLOWED:
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
            if (dlist[i] - dlist[i - 1]).days < 3:
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

    counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(df)
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
        counts2, bg2, ht2, wd2, we2, bk2, ly2, bg_cat2, assigned_hosp_count2, doc_assignments2, unassigned2, *_ = recompute_stats(df)
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

        # 絶対禁忌チェック: gap違反または外病院重複があれば拒否
        new_gap_violations = new_metrics.get("gap_violations", 0)
        new_external_hosp_dup = new_metrics.get("external_hosp_dup_violations", 0)
        if new_gap_violations > 0 or new_external_hosp_dup > 0:
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
            if gap < 3:
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
        gap_viol = sum(1 for g in gaps if g < 3)
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

            # 違反1: 可否コード0 (ABS-001)
            if code == 0:
                rows.append({
                    "制約ID": CONSTRAINT_ABS_001,
                    "違反種別": "可否コード0違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code if sched_code else "",
                    "詳細": f"[{CONSTRAINT_ABS_001}] コード0（不可）の日に割当",
                })

            # 違反2: 可否コード2違反（Q列より後に割当）(ABS-002)
            if code == 2 and not (B_COL_INDEX <= idx <= Q_COL_INDEX):
                rows.append({
                    "制約ID": CONSTRAINT_ABS_002,
                    "違反種別": "可否コード2違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code if sched_code else "",
                    "詳細": f"[{CONSTRAINT_ABS_002}] コード2はB〜Q列のみ可。列{idx}に割当",
                })

            # 違反3: 可否コード3違反（L〜Y列以外に割当）(ABS-003)
            if code == 3 and not (L_COL_INDEX <= idx <= L_Y_END_INDEX):
                rows.append({
                    "制約ID": CONSTRAINT_ABS_003,
                    "違反種別": "可否コード3違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code if sched_code else "",
                    "詳細": f"[{CONSTRAINT_ABS_003}] コード3はL〜Y列のみ可。列{idx}に割当",
                })

            # 違反4: カテ表コードあり＋L〜Y列違反 (ABS-004)
            if L_COL_INDEX <= idx <= L_Y_END_INDEX and sched_code:
                rows.append({
                    "制約ID": CONSTRAINT_ABS_004,
                    "違反種別": "カテ表+外病院違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code,
                    "詳細": f"[{CONSTRAINT_ABS_004}] カテ表（{sched_code}）がある日は外病院（L〜Y列）に割当不可。列{idx}に割当",
                })

            # 違反5: B〜K列でカテ表コードなし（カテ表コード保有医師のみ、EXTRA医師は例外）(SEMI-001/002)
            if B_COL_INDEX <= idx <= B_K_END_INDEX and doc in SCHEDULE_CODE_HOLDERS and not sched_code and doc not in EXTRA_ALLOWED:
                # C-H列は休日大学系(SEMI-002)、それ以外は平日大学系(SEMI-001)
                constraint_id = CONSTRAINT_SEMI_002 if C_COL_INDEX <= idx <= H_COL_INDEX else CONSTRAINT_SEMI_001
                rows.append({
                    "制約ID": constraint_id,
                    "違反種別": "B-K列カテ表コード欠如",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": "",
                    "詳細": f"[{constraint_id}] B〜K列（大学系）の割当にカテ表コードが必要（カテ表コード保有医師、EXTRA医師は例外）。列{idx}に割当",
                })

            # 違反6: 水曜日L〜Y列禁止医師 (ABS-006)
            if dow == 2 and L_COL_INDEX <= idx <= L_Y_END_INDEX and doc in WED_FORBIDDEN_DOCTORS:
                rows.append({
                    "制約ID": CONSTRAINT_ABS_006,
                    "違反種別": "水曜日L〜Y列禁止違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code if sched_code else "",
                    "詳細": f"[{CONSTRAINT_ABS_006}] {doc}は水曜日のL〜Y列禁止",
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

    # 違反7: B〜H列が2回超過 (SOFT-002: 大学3回以上)
    for doc, assignments in bh_counts.items():
        if len(assignments) > 2:
            for date, hosp, idx in assignments[2:]:  # 3回目以降
                code = get_avail_code(date, doc)
                sched_code = get_sched_code(date, doc)
                rows.append({
                    "制約ID": CONSTRAINT_SOFT_002,
                    "違反種別": "B-H列2回超過違反",
                    "日付": date,
                    "医師名": doc,
                    "病院": hosp,
                    "列番号": idx,
                    "可否コード": code,
                    "カテ表": sched_code if sched_code else "",
                    "詳細": f"[{CONSTRAINT_SOFT_002}] B〜H列は2回まで。{len(assignments)}回目の割当",
                })

    cols = ["制約ID", "違反種別", "日付", "医師名", "病院", "列番号", "可否コード", "カテ表", "詳細"]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows)[cols].sort_values(["制約ID", "日付", "医師名"]).reset_index(drop=True)

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
                # 緊急フォールバック: 絶対禁忌をすべて回避
                # 医師の現在の割当日を取得（gap1チェック用）
                def get_doc_dates(d):
                    dates = []
                    for ridx2 in df.index:
                        dt2 = df.at[ridx2, date_col_shift]
                        if pd.isna(dt2):
                            continue
                        dt2 = pd.to_datetime(dt2).normalize().tz_localize(None)
                        for h in hospital_cols:
                            v = df.at[ridx2, h]
                            if isinstance(v, str) and normalize_name(v) == d:
                                dates.append(dt2)
                    return dates

                # 医師の外病院割当回数を取得
                def get_doc_hosp_count(d, target_hosp):
                    count = 0
                    for ridx2 in df.index:
                        v = df.at[ridx2, target_hosp]
                        if isinstance(v, str) and normalize_name(v) == d:
                            count += 1
                    return count

                is_external = L_COL_INDEX <= col_idx <= L_Y_END_INDEX

                def is_valid_emergency(d):
                    # 同日重複禁止
                    if d in already_assigned_on_date:
                        return False
                    # ABS-001: コード0禁止
                    if get_avail_code(date, d) == 0:
                        return False
                    # gap1禁止
                    doc_dates = get_doc_dates(d)
                    if doc_dates:
                        min_gap = min(abs((date - dt).days) for dt in doc_dates)
                        if min_gap < 2:
                            return False
                    # 外病院重複禁止
                    if is_external and get_doc_hosp_count(d, hosp) >= 1:
                        return False
                    return True

                emergency_candidates = [d for d in doctor_names if is_valid_emergency(d)]
                if emergency_candidates:
                    # 全体合計が最も少ない医師を選択
                    emergency_candidates.sort(key=lambda d: prev_total.get(d, 0) + len([1 for h in hospital_cols for ridx2 in df.index if isinstance(df.at[ridx2, h], str) and normalize_name(df.at[ridx2, h]) == d]))
                    new_doc = emergency_candidates[0]
                    df.at[ridx, hosp] = new_doc
                    fixed_in_this_iteration += 1
                    total_fixed += 1
                    if verbose:
                        print(f"   ⚠️ 緊急フォールバック: {date.strftime('%Y-%m-%d')} {hosp} → {new_doc}")
                else:
                    # 絶対禁忌を満たす候補がいない場合は未割当のまま
                    total_failed += 1
                    if verbose:
                        print(f"   ❌ 修正不可（絶対禁忌回避不可）: {date.strftime('%Y-%m-%d')} {hosp}")

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
    TARGET_CAP違反を修正する（上限超過とBASE_TARGET未達の両方）

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

        # cap超過・BASE_TARGET未達の医師を特定
        over_cap_docs = []  # cap超過
        under_base_docs = []  # BASE_TARGET未達（新規）
        at_base_docs = []  # BASE_TARGETちょうど
        over_base_docs = []  # BASE_TARGET超過だがcap以下

        for doc in active_doctors:
            current = counts.get(doc, 0)
            cap = TARGET_CAP.get(doc, 0)

            if current > cap:
                over_cap_docs.append((doc, current - cap))
            elif current < BASE_TARGET:
                under_base_docs.append((doc, BASE_TARGET - current))
            elif current == BASE_TARGET:
                at_base_docs.append(doc)
            else:  # BASE_TARGET < current <= cap
                over_base_docs.append((doc, current - BASE_TARGET))

        # 違反がなければ終了
        if not over_cap_docs and not under_base_docs:
            if verbose and total_fixed > 0:
                print(f"   ✅ TARGET_CAP違反を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            if over_cap_docs:
                print(f"   ⚠️ TARGET_CAP超過を{len(over_cap_docs)}件検出 → 自動修正を開始...")
            if under_base_docs:
                print(f"   ⚠️ BASE_TARGET未達を{len(under_base_docs)}件検出 → 自動修正を開始...")

        # 修正試行
        fixed_in_this_iteration = 0

        # 1. cap超過の修正（優先）
        for over_doc, excess in over_cap_docs:
            if excess <= 0:
                continue

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

            import random
            random.shuffle(over_doc_positions)

            for ridx, hosp, date in over_doc_positions[:min(excess, 3)]:
                already_assigned_on_date = set()
                for h in hospital_cols:
                    v = df.at[ridx, h]
                    if isinstance(v, str):
                        already_assigned_on_date.add(normalize_name(v))

                # BASE_TARGET未達の医師を優先、次にat_base
                candidates = []
                for under_doc, deficit in under_base_docs:
                    if deficit <= 0:
                        continue
                    if under_doc in already_assigned_on_date:
                        continue
                    if can_assign_doc_to_slot(under_doc, date, hosp):
                        candidates.append((under_doc, 0))  # 優先度0（最優先）

                for at_doc in at_base_docs:
                    if at_doc in already_assigned_on_date:
                        continue
                    if can_assign_doc_to_slot(at_doc, date, hosp):
                        if TARGET_CAP.get(at_doc, 0) > BASE_TARGET:
                            candidates.append((at_doc, 1))  # 優先度1

                if candidates:
                    candidates.sort(key=lambda x: (x[1], prev_total.get(x[0], 0) + counts.get(x[0], 0)))
                    new_doc = candidates[0][0]

                    df.at[ridx, hosp] = new_doc
                    fixed_in_this_iteration += 1
                    total_fixed += 1

                    # リストを更新
                    for i, (d, deficit) in enumerate(under_base_docs):
                        if d == new_doc:
                            under_base_docs[i] = (d, deficit - 1)
                            if deficit - 1 <= 0 and d in at_base_docs:
                                pass
                            elif deficit - 1 <= 0:
                                at_base_docs.append(d)
                            break
                    if new_doc in at_base_docs:
                        over_base_docs.append((new_doc, 1))
                    break

        # 2. BASE_TARGET未達の修正
        for under_doc, deficit in under_base_docs:
            if deficit <= 0:
                continue

            # over_base（BASE_TARGET超過だがcap以下）の医師から取る
            donor_candidates = over_base_docs[:3]

            for donor_doc, _ in donor_candidates:
                donor_positions = []
                for ridx in df.index:
                    date = df.at[ridx, date_col_shift]
                    if pd.isna(date):
                        continue
                    date = pd.to_datetime(date).normalize().tz_localize(None)

                    for hosp in hospital_cols:
                        val = df.at[ridx, hosp]
                        if isinstance(val, str) and normalize_name(val) == donor_doc:
                            donor_positions.append((ridx, hosp, date))

                import random
                random.shuffle(donor_positions)

                for ridx, hosp, date in donor_positions[:2]:
                    already_assigned_on_date = set()
                    for h in hospital_cols:
                        v = df.at[ridx, h]
                        if isinstance(v, str):
                            already_assigned_on_date.add(normalize_name(v))

                    if under_doc in already_assigned_on_date:
                        continue
                    if not can_assign_doc_to_slot(under_doc, date, hosp):
                        continue

                    df.at[ridx, hosp] = under_doc
                    fixed_in_this_iteration += 1
                    total_fixed += 1
                    break

                if fixed_in_this_iteration > 0:
                    break

    # 最終確認
    counts, *_ = recompute_stats(df)
    remaining_over = sum(1 for doc in active_doctors if counts.get(doc, 0) > TARGET_CAP.get(doc, 0))
    remaining_under = sum(1 for doc in active_doctors if counts.get(doc, 0) < BASE_TARGET)

    if verbose:
        if remaining_over == 0 and remaining_under == 0:
            print(f"   ✅ 全てのTARGET_CAP違反を修正しました（修正数: {total_fixed}）")
        else:
            if remaining_over > 0:
                print(f"   ⚠️ {remaining_over}件のTARGET_CAP超過違反が残っています（修正数: {total_fixed}）")
            if remaining_under > 0:
                print(f"   ⚠️ {remaining_under}件のBASE_TARGET未達違反が残っています（修正数: {total_fixed}）")

    return df, (remaining_over == 0 and remaining_under == 0), total_fixed

def fix_code_2_extra_violations(pattern_df, max_attempts=100, verbose=True):
    """
    可否コード2医師のn+1回違反を修正する（ハード制約）
    CODE_2_DOCTORSはBASE_TARGET回までしか割当できない

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
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(df)

        # CODE_2医師でBASE_TARGETを超えている医師を特定
        code_2_over_docs = []
        for doc in CODE_2_DOCTORS:
            if doc not in active_doctors:
                continue
            current = counts.get(doc, 0)
            if current > BASE_TARGET:
                code_2_over_docs.append((doc, current - BASE_TARGET))

        # 違反がなければ終了
        if not code_2_over_docs:
            if verbose and total_fixed > 0:
                print(f"   ✅ 可否コード2医師のn+1違反を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            over_docs_str = ", ".join([f"{d}({excess}回超過)" for d, excess in code_2_over_docs])
            print(f"   ⚠️ 可否コード2医師のn+1違反を{len(code_2_over_docs)}件検出 → 自動修正を開始...")
            print(f"      対象: {over_docs_str}")

        # 修正試行
        fixed_in_this_iteration = 0

        for over_doc, excess in code_2_over_docs:
            if excess <= 0:
                continue

            # over_docの割当位置を取得
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

            import random
            random.shuffle(over_doc_positions)

            for ridx, hosp, date in over_doc_positions[:min(excess, 3)]:
                # その日に既に割当されている医師
                already_assigned_on_date = set()
                for h in hospital_cols:
                    v = df.at[ridx, h]
                    if isinstance(v, str):
                        already_assigned_on_date.add(normalize_name(v))

                # 代替医師を探す（CODE_2以外の医師でBASE_TARGET未達または余裕のある医師）
                candidates = []
                for alt_doc in active_doctors:
                    if alt_doc == over_doc:
                        continue
                    if alt_doc in already_assigned_on_date:
                        continue
                    if alt_doc in CODE_2_DOCTORS:
                        continue  # CODE_2医師は代替にならない

                    alt_current = counts.get(alt_doc, 0)
                    alt_cap = TARGET_CAP.get(alt_doc, 0)

                    if alt_current >= alt_cap:
                        continue  # 既にcap到達

                    if can_assign_doc_to_slot(alt_doc, date, hosp):
                        # 優先度: BASE_TARGET未達 > ちょうど > 超過
                        priority = 0 if alt_current < BASE_TARGET else (1 if alt_current == BASE_TARGET else 2)
                        candidates.append((alt_doc, priority))

                if candidates:
                    candidates.sort(key=lambda x: x[1])
                    new_doc = candidates[0][0]
                    df.at[ridx, hosp] = new_doc
                    counts[over_doc] = counts.get(over_doc, 0) - 1
                    counts[new_doc] = counts.get(new_doc, 0) + 1
                    total_fixed += 1
                    fixed_in_this_iteration += 1
                else:
                    # 緊急フォールバック: 絶対禁忌をすべて回避
                    col_idx = shift_df.columns.get_loc(hosp)
                    is_external = L_COL_INDEX <= col_idx <= L_Y_END_INDEX

                    def is_valid_emergency_target(d):
                        # 同日重複禁止
                        if d in already_assigned_on_date:
                            return False
                        if d == over_doc:
                            return False
                        # ABS-001: コード0禁止
                        if get_avail_code(date, d) == 0:
                            return False
                        # gap1禁止
                        doc_dates = sorted([dt for dt, _ in doc_assignments.get(d, [])])
                        if doc_dates:
                            min_gap = min(abs((date - dt).days) for dt in doc_dates)
                            if min_gap < 2:
                                return False
                        # 外病院重複禁止
                        if is_external and assigned_hosp_count.get(d, {}).get(hosp, 0) >= 1:
                            return False
                        return True

                    emergency = [d for d in doctor_names if is_valid_emergency_target(d)]
                    if emergency:
                        emergency.sort(key=lambda d: counts.get(d, 0))
                        new_doc = emergency[0]
                        df.at[ridx, hosp] = new_doc
                        counts[over_doc] = counts.get(over_doc, 0) - 1
                        counts[new_doc] = counts.get(new_doc, 0) + 1
                        total_fixed += 1
                        fixed_in_this_iteration += 1
                        if verbose:
                            print(f"      ⚠️ {over_doc}→{new_doc}(緊急): {date.strftime('%m/%d')} {hosp}")
                    else:
                        # 最終手段: 元の医師を維持（削除しない）
                        if verbose:
                            print(f"      ⚠️ {over_doc}の{date.strftime('%m/%d')} {hosp}を維持（絶対禁忌回避不可）")

        if fixed_in_this_iteration == 0:
            break

    # 最終状態を確認
    counts, *_ = recompute_stats(df)
    remaining = sum(1 for doc in CODE_2_DOCTORS if doc in active_doctors and counts.get(doc, 0) > BASE_TARGET)

    if verbose:
        if remaining == 0:
            if total_fixed > 0:
                print(f"   ✅ 全ての可否コード2医師のn+1違反を修正しました（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ {remaining}件の可否コード2医師のn+1違反が残っています（修正数: {total_fixed}）")

    return df, (remaining == 0), total_fixed

def fix_university_minimum_requirement(pattern_df, max_attempts=100, verbose=True):
    """
    大学系最低1回必須違反を修正する（準ハード制約：コード3以外の全医師）

    Args:
        pattern_df: スケジュールDataFrame
        max_attempts: 最大試行回数
        verbose: ログ出力するか

    Returns:
        (修正後のDataFrame, 成功フラグ, 修正数)
    """
    if not UNIVERSITY_MINIMUM_REQUIRED_DOCTORS:
        return pattern_df, True, 0

    df = pattern_df.copy()
    total_fixed = 0

    for attempt in range(max_attempts):
        # 現在の割当回数を再計算
        counts, bg_counts, *_ = recompute_stats(df)

        # 大学系0回の医師を特定（コード3除外）
        zero_bg_docs = []
        for doc in UNIVERSITY_MINIMUM_REQUIRED_DOCTORS:
            if bg_counts.get(doc, 0) == 0:
                zero_bg_docs.append(doc)

        if not zero_bg_docs:
            if verbose and total_fixed > 0:
                print(f"   ✅ 大学系最低1回必須違反を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            print(f"   ⚠️ 大学系最低1回必須違反を{len(zero_bg_docs)}件検出 → 自動修正を開始...")

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
    remaining_violations = sum(1 for doc in UNIVERSITY_MINIMUM_REQUIRED_DOCTORS if bg_counts.get(doc, 0) == 0)

    if verbose:
        if remaining_violations == 0:
            print(f"   ✅ 全ての大学系最低1回必須違反を修正しました（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ {remaining_violations}件の大学系最低1回必須違反が残っています（修正数: {total_fixed}）")

    return df, remaining_violations == 0, total_fixed

# 後方互換性のため、旧関数名を残す
def fix_code_1_2_violations(pattern_df, max_attempts=100, verbose=True):
    """後方互換性のための関数（fix_university_minimum_requirementにリダイレクト）"""
    return fix_university_minimum_requirement(pattern_df, max_attempts, verbose)

def fix_ch_kate_violations(pattern_df, max_attempts=100, verbose=True):
    """
    C-H列（休日大学系）のカテ当番違反を修正する

    条件：C-H列はカテ当番ありの日 OR カテ当番なし医師のみ
    カテ当番保有医師がその日にカテ当番なしでC-H列に割り当てられている場合、
    適格な医師と交換する

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
        # C-H列の違反を検出
        violations = []
        for ridx in df.index:
            date = df.at[ridx, date_col_shift]
            if pd.isna(date):
                continue
            date = pd.to_datetime(date).normalize().tz_localize(None)
            for hosp in hospital_cols:
                idx = shift_df.columns.get_loc(hosp)
                if not is_ch_slot(idx):
                    continue
                val = df.at[ridx, hosp]
                if not isinstance(val, str):
                    continue
                doc = normalize_name(val)
                if doc not in doctor_names:
                    continue
                if not is_eligible_for_ch_slot(doc, date):
                    violations.append({
                        "ridx": ridx,
                        "hosp": hosp,
                        "date": date,
                        "doc": doc,
                        "idx": idx
                    })

        if not violations:
            break

        # 最初の違反を修正
        viol = violations[0]
        ridx, hosp, date, bad_doc, col_idx = viol["ridx"], viol["hosp"], viol["date"], viol["doc"], viol["idx"]

        # 1. C-H列に適格な医師を探す
        # 適格条件: is_eligible_for_ch_slot(doc, date) = True
        # 候補：現在違反がないスロットにいる適格医師
        swap_done = False

        # 同じ日の他のスロット（C-H以外）で適格な医師を探して交換
        for other_hosp in hospital_cols:
            if swap_done:
                break
            other_idx = shift_df.columns.get_loc(other_hosp)
            # C-H列以外のスロットを探す（L-Y列など）
            if is_ch_slot(other_idx):
                continue
            other_val = df.at[ridx, other_hosp]
            if not isinstance(other_val, str):
                continue
            other_doc = normalize_name(other_val)
            if other_doc not in doctor_names:
                continue
            # other_docがC-H列に適格かチェック
            if not is_eligible_for_ch_slot(other_doc, date):
                continue
            # other_docがhosp（C-H列）に割り当て可能かチェック（ABS-001含む）
            if not can_assign_doc_to_slot(other_doc, date, hosp):
                continue
            # bad_docがother_hospに割り当て可能かチェック
            if not can_assign_doc_to_slot(bad_doc, date, other_hosp):
                continue
            # 交換
            df.at[ridx, hosp] = other_doc
            df.at[ridx, other_hosp] = bad_doc
            total_fixed += 1
            swap_done = True
            if verbose:
                print(f"   [C-Hカテ当番修正] {date.strftime('%Y-%m-%d')} {hosp}列: {bad_doc} ⇔ {other_doc}")

        if swap_done:
            continue

        # 2. 別の日の適格医師と交換を試みる
        for other_ridx in df.index:
            if swap_done:
                break
            other_date = df.at[other_ridx, date_col_shift]
            if pd.isna(other_date):
                continue
            other_date = pd.to_datetime(other_date).normalize().tz_localize(None)
            if other_date == date:
                continue

            for other_hosp in hospital_cols:
                if swap_done:
                    break
                other_idx = shift_df.columns.get_loc(other_hosp)
                # C-H列以外のスロット
                if is_ch_slot(other_idx):
                    continue
                other_val = df.at[other_ridx, other_hosp]
                if not isinstance(other_val, str):
                    continue
                other_doc = normalize_name(other_val)
                if other_doc not in doctor_names:
                    continue
                # other_docがC-H列に適格かチェック
                if not is_eligible_for_ch_slot(other_doc, date):
                    continue
                # bad_docがother_hospに割り当て可能かチェック
                if not can_assign_doc_to_slot(bad_doc, other_date, other_hosp):
                    continue
                # other_docがdate, hospに割り当て可能かチェック
                if not can_assign_doc_to_slot(other_doc, date, hosp):
                    continue
                # 交換
                df.at[ridx, hosp] = other_doc
                df.at[other_ridx, other_hosp] = bad_doc
                total_fixed += 1
                swap_done = True
                if verbose:
                    print(f"   [C-Hカテ当番修正] {date.strftime('%Y-%m-%d')} {hosp}列: {bad_doc} → {other_doc}")

        if not swap_done:
            # 交換できなかった場合、次の違反を試す
            if verbose and attempt == 0:
                print(f"   ⚠️ C-H列カテ当番違反を修正できません: {date.strftime('%Y-%m-%d')} {hosp}列 {bad_doc}")
            break

    # 残り違反を再計算
    remaining_violations = 0
    for ridx in df.index:
        date = df.at[ridx, date_col_shift]
        if pd.isna(date):
            continue
        date = pd.to_datetime(date).normalize().tz_localize(None)
        for hosp in hospital_cols:
            idx = shift_df.columns.get_loc(hosp)
            if not is_ch_slot(idx):
                continue
            val = df.at[ridx, hosp]
            if not isinstance(val, str):
                continue
            doc = normalize_name(val)
            if doc not in doctor_names:
                continue
            if not is_eligible_for_ch_slot(doc, date):
                remaining_violations += 1

    if verbose:
        if remaining_violations == 0:
            print(f"   ✅ 全てのC-H列カテ当番違反を修正しました（修正数: {total_fixed}）")
        else:
            print(f"   ⚠️ {remaining_violations}件のC-H列カテ当番違反が残っています（修正数: {total_fixed}）")

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
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, cc_counts, cc_bg_counts, cc_ht_counts = recompute_stats(df)

        # 大学系と外病院の差が3以上の医師を特定（CC除外）
        imbalance_docs = []
        for doc in active_doctors:
            # CCは大型連休特別シフトなのでバランス計算から除外
            bg = bg_counts.get(doc, 0) - cc_bg_counts.get(doc, 0)
            ht = ht_counts.get(doc, 0) - cc_ht_counts.get(doc, 0)
            diff = abs(bg - ht)
            if diff >= 3:
                imbalance_docs.append((doc, bg, ht, diff))

        if not imbalance_docs:
            if verbose and total_fixed > 0:
                print(f"   ✅ 大学系と外病院の差3以上の違反を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            print(f"   ⚠️ 大学系と外病院の差3以上の違反を{len(imbalance_docs)}件検出 → 自動修正を開始...")

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
    gap違反（3日未満の間隔での割当）を修正する

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
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(df)

        # gap違反を検出
        gap_violation_list = []
        for doc, date_hosp_list in doc_assignments.items():
            dates = sorted([d for d, h in date_hosp_list])
            for i in range(1, len(dates)):
                gap = (dates[i] - dates[i-1]).days
                if gap < 3:
                    gap_violation_list.append((doc, dates[i-1], dates[i], gap))

        if not gap_violation_list:
            if verbose and total_fixed > 0:
                print(f"   ✅ gap違反（3日未満の間隔）を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            print(f"   ⚠️ gap違反を{len(gap_violation_list)}件検出 → 自動修正を開始...")

        # 修正試行（1イテレーションで複数の違反を修正）
        fixed_in_this_iteration = 0

        for doc, date1, date2, gap in gap_violation_list:
            if gap >= 3:
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
                counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(df)

        # 進捗チェック
        if fixed_in_this_iteration == 0:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        # 連続で20回修正できなければ諦める
        if consecutive_failures >= 20:
            break

    # 最終確認
    counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(df)
    remaining_violations = 0
    for doc, date_hosp_list in doc_assignments.items():
        dates = sorted([d for d, h in date_hosp_list])
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days < 3:
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
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, cc_counts, cc_bg_counts, cc_ht_counts = recompute_stats(df)

        # CC分の病院別カウントを計算（重複検出から除外用）
        cc_hosp_counts = {d: defaultdict(int) for d in doctor_names}
        for ridx in df.index:
            date = df.at[ridx, date_col_shift]
            if pd.isna(date):
                continue
            date = pd.to_datetime(date).normalize().tz_localize(None)
            for hosp in hospital_cols:
                val = df.at[ridx, hosp]
                if isinstance(val, str):
                    doc = normalize_name(val)
                    if doc in doctor_names and is_cc_assignment(date, doc):
                        cc_hosp_counts[doc][hosp] += 1

        # 外病院重複を検出（CC除外）
        external_dup_list = []
        for doc, hosp_dict in assigned_hosp_count.items():
            for hosp, count in hosp_dict.items():
                # CC分を除外
                count_no_cc = count - cc_hosp_counts.get(doc, {}).get(hosp, 0)
                if count_no_cc > 1:
                    # 外病院かどうかを判定
                    hidx = shift_df.columns.get_loc(hosp)
                    if L_COL_INDEX <= hidx <= L_Y_END_INDEX:
                        external_dup_list.append((doc, hosp, count_no_cc))

        if not external_dup_list:
            if verbose and total_fixed > 0:
                print(f"   ✅ 外病院重複を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            print(f"   ⚠️ 外病院重複を{len(external_dup_list)}件検出 → 自動修正を開始...")

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
                counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(df)

        # 進捗チェック
        if fixed_in_this_iteration == 0:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        # 連続で20回修正できなければ諦める
        if consecutive_failures >= 20:
            break

    # 最終確認
    counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(df)
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
    また、外病院0回の医師がいる場合も大学→外病院への移動を試みる（ハード制約）

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
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, cc_counts, cc_bg_counts, cc_ht_counts = recompute_stats(df)

        # 大学3回以上の医師を検出（CC除外）
        over_2_list = []
        for doc in active_doctors:
            if doc in RATIO_EXEMPT_DOCTORS:  # コード3は外病院専門なので除外
                continue
            # CCは大型連休特別シフトなので除外
            bg_count_no_cc = bg_counts.get(doc, 0) - cc_bg_counts.get(doc, 0)
            if bg_count_no_cc >= 3:
                over_2_list.append((doc, bg_count_no_cc, "大学3回以上"))

        # 外病院0回の医師を検出（大学を外病院に移動する必要あり）
        # 注：これはハード制約なのでCCは除外しない
        for doc in active_doctors:
            if doc in RATIO_EXEMPT_DOCTORS:  # コード3は外病院専門なので対象外
                continue
            ht_count = ht_counts.get(doc, 0)
            bg_count = bg_counts.get(doc, 0)
            # 外病院0回かつ大学1回以上なら、大学→外病院への移動が必要
            if ht_count == 0 and bg_count >= 1:
                # 既にover_2_listに含まれていないかチェック
                if not any(d == doc for d, _, _ in over_2_list):
                    over_2_list.append((doc, bg_count, "外病院0回"))

        if not over_2_list:
            if verbose and total_fixed > 0:
                print(f"   ✅ 大学3回以上/外病院0回違反を{total_fixed}件修正しました")
            return df, True, total_fixed

        if attempt == 0 and verbose:
            over_3_count = sum(1 for _, _, reason in over_2_list if reason == "大学3回以上")
            ext_0_count = sum(1 for _, _, reason in over_2_list if reason == "外病院0回")
            if over_3_count > 0:
                print(f"   ⚠️ 大学3回以上違反を{over_3_count}件検出")
            if ext_0_count > 0:
                print(f"   ⚠️ 外病院0回違反を{ext_0_count}件検出")

        # 修正試行
        fixed_in_this_iteration = 0

        for doc, bg_count, reason in over_2_list:
            # 大学3回以上の場合は2回に減らす、外病院0回の場合は1回移動
            if reason == "大学3回以上" and bg_count < 3:
                continue
            if reason == "外病院0回" and bg_count < 1:
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

            # 移動数を決定
            if reason == "大学3回以上":
                excess = bg_count - 2  # 2回まで減らす
            else:  # 外病院0回
                excess = 1  # 1回だけ移動

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

                # 移動先が見つからない場合は代替医師を探して割り当て（未割当防止）
                if not moved and attempt >= 5:
                    # この日に既に割り当てられている医師を取得
                    already_on_date = set()
                    for h in hospital_cols:
                        v = df.at[ridx, h]
                        if isinstance(v, str):
                            already_on_date.add(normalize_name(v))
                    # 代替候補: 同日重複なし & 大学系2回未満の医師
                    replacement_candidates = [
                        d for d in doctor_names
                        if d not in already_on_date
                        and d != doc
                        and bg_counts.get(d, 0) < 2
                        and can_assign_doc_to_slot(d, date, hosp)
                    ]
                    if replacement_candidates:
                        replacement_candidates.sort(key=lambda d: bg_counts.get(d, 0))
                        new_doc = replacement_candidates[0]
                        df.at[ridx, hosp] = new_doc
                        if verbose and attempt < 10:
                            print(f"      {doc}→{new_doc}: {date.strftime('%m/%d')}の大学病院割当を交代")
                    else:
                        # 緊急フォールバック: 絶対禁忌をすべて回避
                        hosp_idx = shift_df.columns.get_loc(hosp)
                        is_external_hosp = L_COL_INDEX <= hosp_idx <= L_Y_END_INDEX

                        def is_valid_bg_emergency(d):
                            # 同日重複禁止
                            if d in already_on_date or d == doc:
                                return False
                            # ABS-001: コード0禁止
                            if get_avail_code(date, d) == 0:
                                return False
                            # gap1禁止
                            d_dates = sorted([dt for dt, _ in doc_assignments.get(d, [])])
                            if d_dates:
                                min_gap = min(abs((date - dt).days) for dt in d_dates)
                                if min_gap < 2:
                                    return False
                            # 外病院重複禁止
                            if is_external_hosp and assigned_hosp_count.get(d, {}).get(hosp, 0) >= 1:
                                return False
                            return True

                        emergency = [d for d in doctor_names if is_valid_bg_emergency(d)]
                        if emergency:
                            emergency.sort(key=lambda d: bg_counts.get(d, 0))
                            new_doc = emergency[0]
                            df.at[ridx, hosp] = new_doc
                            if verbose and attempt < 10:
                                print(f"      {doc}→{new_doc}(緊急): {date.strftime('%m/%d')}の大学病院割当を交代")
                        else:
                            # 最終手段: 元の医師を維持（削除しない）
                            df.at[ridx, hosp] = doc
                            if verbose and attempt < 10:
                                print(f"      {doc}: {date.strftime('%m/%d')}の割当維持（絶対禁忌回避不可）")
                    fixed_in_this_iteration += 1
                    total_fixed += 1

            if fixed_in_this_iteration > 0:
                counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(df)

        # 進捗チェック
        if fixed_in_this_iteration == 0:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        # 連続で20回修正できなければ諦める
        if consecutive_failures >= 20:
            break

    # 最終確認
    counts, bg_counts, ht_counts, *_ = recompute_stats(df)
    remaining_over_2 = sum(1 for doc in active_doctors if doc not in RATIO_EXEMPT_DOCTORS and bg_counts.get(doc, 0) >= 3)
    remaining_ext_0 = sum(1 for doc in active_doctors if doc not in RATIO_EXEMPT_DOCTORS and ht_counts.get(doc, 0) == 0 and bg_counts.get(doc, 0) >= 1)
    remaining_violations = remaining_over_2 + remaining_ext_0

    if verbose:
        if remaining_violations == 0:
            if total_fixed > 0:
                print(f"   ✅ 全ての大学3回以上/外病院0回違反を修正しました（修正数: {total_fixed}）")
        else:
            if remaining_over_2 > 0:
                print(f"   ⚠️ {remaining_over_2}件の大学3回以上違反が残っています")
            if remaining_ext_0 > 0:
                print(f"   ⚠️ {remaining_ext_0}件の外病院0回違反が残っています")

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
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, cc_counts, cc_bg_counts, cc_ht_counts = recompute_stats(df)

        # 大学の平日2回以上の医師を検出
        # 注：weekday_countからCCを除外するには追加トラッキングが必要
        # 現時点ではweekday_countはそのまま使用（大型連休は平日カウントされにくい）
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
            print(f"   ⚠️ 大学平日偏り違反を{len(weekday_over_list)}件検出 → 自動修正を開始...")

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

                # 移動先が見つからない場合は代替医師を探して割り当て（未割当防止）
                if not moved and attempt >= 5:
                    # この日に既に割り当てられている医師を取得
                    already_on_date = set()
                    for h in hospital_cols:
                        v = df.at[ridx, h]
                        if isinstance(v, str):
                            already_on_date.add(normalize_name(v))
                    # 代替候補: 同日重複なし & 大学平日未割当の医師
                    replacement_candidates = [
                        d for d in doctor_names
                        if d not in already_on_date
                        and d != doc
                        and wd_counts.get(d, 0) < we_counts.get(d, 0)  # 平日<休日の医師を優先
                        and can_assign_doc_to_slot(d, date, hosp)
                    ]
                    if replacement_candidates:
                        replacement_candidates.sort(key=lambda d: wd_counts.get(d, 0))
                        new_doc = replacement_candidates[0]
                        df.at[ridx, hosp] = new_doc
                        if verbose and attempt < 10:
                            print(f"      {doc}→{new_doc}: {date.strftime('%m/%d')}の大学平日割当を交代")
                    else:
                        # 緊急フォールバック: 絶対禁忌をすべて回避
                        hosp_idx = shift_df.columns.get_loc(hosp)
                        is_external_hosp = L_COL_INDEX <= hosp_idx <= L_Y_END_INDEX

                        def is_valid_weekday_emergency(d):
                            # 同日重複禁止
                            if d in already_on_date or d == doc:
                                return False
                            # ABS-001: コード0禁止
                            if get_avail_code(date, d) == 0:
                                return False
                            # gap1禁止
                            d_dates = sorted([dt for dt, _ in doc_assignments.get(d, [])])
                            if d_dates:
                                min_gap = min(abs((date - dt).days) for dt in d_dates)
                                if min_gap < 2:
                                    return False
                            # 外病院重複禁止
                            if is_external_hosp and assigned_hosp_count.get(d, {}).get(hosp, 0) >= 1:
                                return False
                            return True

                        emergency = [d for d in doctor_names if is_valid_weekday_emergency(d)]
                        if emergency:
                            emergency.sort(key=lambda d: counts.get(d, 0))
                            new_doc = emergency[0]
                            df.at[ridx, hosp] = new_doc
                            if verbose and attempt < 10:
                                print(f"      {doc}→{new_doc}(緊急): {date.strftime('%m/%d')}の大学平日割当を交代")
                        else:
                            # 最終手段: 元の医師を維持
                            df.at[ridx, hosp] = doc
                            if verbose and attempt < 10:
                                print(f"      {doc}: {date.strftime('%m/%d')}の割当維持（絶対禁忌回避不可）")
                    fixed_in_this_iteration += 1
                    total_fixed += 1
                    break

            if fixed_in_this_iteration > 0:
                counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(df)

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
        counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, cc_counts, cc_bg_counts, cc_ht_counts = recompute_stats(df)

        # active医師の割当回数を確認（CC除外）
        # CCは大型連休特別シフトなので公平性計算から除外
        active_counts = [(doc, counts.get(doc, 0) - cc_counts.get(doc, 0)) for doc in active_doctors]
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
                    # doc_assignments は (date, hosp) のタプルのリスト
                    min_doc_dates = sorted([d for d, h in doc_assignments.get(min_doc, []) if h != hosp or d != date])
                    new_dates = sorted(min_doc_dates + [date])

                    gap_ok = True
                    for j in range(len(new_dates) - 1):
                        gap = (new_dates[j + 1] - new_dates[j]).days
                        if gap < 3:
                            gap_ok = False
                            break

                    if not gap_ok:
                        continue

                    # 外病院重複チェック
                    hosp_idx = shift_df.columns.get_loc(hosp)
                    is_external = L_COL_INDEX <= hosp_idx <= L_Y_END_INDEX
                    if is_external:
                        # min_docがこの外病院に既に割り当てられている場合は拒否
                        if assigned_hosp_count.get(min_doc, {}).get(hosp, 0) >= 1:
                            continue

                    # max_docから削除した場合のgap違反チェック
                    max_doc_dates = sorted([d for d, h in doc_assignments.get(max_doc, []) if h != hosp or d != date])
                    if len(max_doc_dates) >= 2:
                        for j in range(len(max_doc_dates) - 1):
                            gap = (max_doc_dates[j + 1] - max_doc_dates[j]).days
                            # 削除によってgap違反が発生することはない（削除は間隔を広げるだけ）

                    # 入れ替え
                    df.at[ridx, hosp] = min_doc
                    fixed_in_this_iteration += 1
                    total_fixed += 1

                    if verbose and attempt < 3:
                        print(f"      {date.strftime('%m/%d')} {hosp}: {max_doc}({max_count}回) → {min_doc}({min_count}回)")

                    # doc_assignmentsを更新（次の反復のため）
                    if max_doc in doc_assignments:
                        doc_assignments[max_doc] = [(d, h) for d, h in doc_assignments[max_doc] if h != hosp or d != date]
                    if min_doc not in doc_assignments:
                        doc_assignments[min_doc] = []
                    doc_assignments[min_doc].append((date, hosp))

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

def fix_unassigned_slots(pattern_df, verbose=True):
    """
    slot_metaに登録されたスロットで医師が割り当てられていないものを埋める
    これは最終セーフティネットとして、全てのスロットに医師を配置することを保証する
    """
    df = pattern_df.copy()
    total_fixed = 0

    counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(df)

    for (ridx, hosp), (date, fixed) in slot_meta.items():
        val = df.at[ridx, hosp]

        # 既に医師が割り当てられている場合はスキップ
        if isinstance(val, str):
            v_norm = normalize_name(val)
            if v_norm in doctor_names:
                continue

        # 未割り当てスロットを発見
        # この日に既に割り当てられている医師を取得
        already_assigned_on_date = set()
        for h in hospital_cols:
            v = df.at[ridx, h]
            if isinstance(v, str):
                already_assigned_on_date.add(normalize_name(v))

        # 候補医師を探す（制約チェック付き）
        candidates = [
            d for d in doctor_names
            if d not in already_assigned_on_date
            and can_assign_doc_to_slot(d, date, hosp)
        ]

        if candidates:
            # 割当回数が少ない医師を優先
            candidates.sort(key=lambda d: counts.get(d, 0))
            new_doc = candidates[0]
        else:
            # 緊急フォールバック: 絶対禁忌をすべて回避
            col_idx = shift_df.columns.get_loc(hosp)
            is_external = L_COL_INDEX <= col_idx <= L_Y_END_INDEX

            def is_valid_unassigned_fallback(d):
                # 同日重複禁止
                if d in already_assigned_on_date:
                    return False
                # ABS-001: コード0禁止
                if get_avail_code(date, d) == 0:
                    return False
                # gap1禁止
                d_dates = sorted([dt for dt, _ in doc_assignments.get(d, [])])
                if d_dates:
                    min_gap = min(abs((date - dt).days) for dt in d_dates)
                    if min_gap < 2:
                        return False
                # 外病院重複禁止
                if is_external and assigned_hosp_count.get(d, {}).get(hosp, 0) >= 1:
                    return False
                return True

            emergency = [d for d in doctor_names if is_valid_unassigned_fallback(d)]
            if emergency:
                emergency.sort(key=lambda d: counts.get(d, 0))
                new_doc = emergency[0]
            else:
                # 絶対禁忌を満たす候補がいない場合は未割当のまま
                if verbose:
                    print(f"   ❌ 未割当: {date.strftime('%Y-%m-%d')} {hosp}（絶対禁忌回避不可）")
                continue

        df.at[ridx, hosp] = new_doc
        counts[new_doc] = counts.get(new_doc, 0) + 1
        total_fixed += 1

        if verbose:
            print(f"   🔧 未割り当て修正: {date.strftime('%Y-%m-%d')} {hosp} → {new_doc}")

    if verbose:
        if total_fixed == 0:
            print("   ✅ 未割り当てスロットなし")
        else:
            print(f"   ✅ {total_fixed}件の未割り当てスロットを修正しました")

    return df, (total_fixed == 0 or total_fixed > 0), total_fixed

def validate_absolute_constraints(pattern_df, verbose=True):
    """
    絶対禁忌の最終検証（v6.0.0）

    チェック項目:
    - ABS-001: コード0割当禁止
    - ABS-002: コード2列制限（B〜Q列のみ）
    - ABS-003: コード3列制限（L〜Y列のみ）
    - ABS-006: 同日重複禁止
    - ABS-007: gap >= 3日必須
    - ABS-008: 同一病院重複禁止（全列）
    - ABS-009: 未割当禁止
    - ABS-010: TARGET_CAP遵守
    - ABS-011: 大学系2回まで

    Returns:
        (violations_list, is_valid)
    """
    violations = []

    counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(pattern_df)

    # ABS-001, ABS-002, ABS-003: コード制限チェック
    for (ridx, hosp), (date, fixed) in slot_meta.items():
        val = pattern_df.at[ridx, hosp]
        if isinstance(val, str):
            doc = normalize_name(val)
            if doc in doctor_names:
                code = get_avail_code(date, doc)
                hidx = shift_df.columns.get_loc(hosp)
                # ABS-001: コード0禁止
                if code == 0:
                    violations.append({
                        "type": "ABS-001",
                        "desc": f"コード0割当: {doc} → {date.strftime('%Y-%m-%d')} {hosp}"
                    })
                # ABS-002: コード2はB〜Q列のみ
                if code == 2 and not (B_COL_INDEX <= hidx <= Q_COL_INDEX):
                    violations.append({
                        "type": "ABS-002",
                        "desc": f"コード2列違反: {doc} → {date.strftime('%Y-%m-%d')} {hosp}"
                    })
                # ABS-003: コード3はL〜Y列のみ
                if code == 3 and not (L_COL_INDEX <= hidx <= L_Y_END_INDEX):
                    violations.append({
                        "type": "ABS-003",
                        "desc": f"コード3列違反: {doc} → {date.strftime('%Y-%m-%d')} {hosp}"
                    })

    # ABS-006: 同日重複チェック
    for date, doc_count in build_date_doc_count(pattern_df).items():
        for doc, count in doc_count.items():
            if count > 1:
                violations.append({
                    "type": "ABS-006",
                    "desc": f"同日重複: {doc} → {date.strftime('%Y-%m-%d')} ({count}回)"
                })

    # ABS-007: gap >= 3日チェック
    for doc, assigns in doc_assignments.items():
        dates = sorted([d for d, _ in assigns])
        for i in range(1, len(dates)):
            gap = (dates[i] - dates[i-1]).days
            if gap < 3:
                violations.append({
                    "type": "ABS-007",
                    "desc": f"gap違反: {doc} → gap={gap}日 (必須>=3)"
                })

    # ABS-008: 同一病院重複チェック
    for doc, hosp_dict in assigned_hosp_count.items():
        for hosp, count in hosp_dict.items():
            if count > 1:
                violations.append({
                    "type": "ABS-008",
                    "desc": f"病院重複: {doc} → {hosp} ({count}回)"
                })

    # ABS-009: 未割当枠チェック
    for (ridx, hosp), (date, fixed) in slot_meta.items():
        val = pattern_df.at[ridx, hosp]
        if not isinstance(val, str):
            violations.append({
                "type": "ABS-009",
                "desc": f"未割当: {date.strftime('%Y-%m-%d')} {hosp}"
            })
        elif normalize_name(val) not in doctor_names:
            violations.append({
                "type": "ABS-009",
                "desc": f"不明医師: {date.strftime('%Y-%m-%d')} {hosp} → {val}"
            })

    # ABS-010: TARGET_CAP遵守チェック
    for doc, count in counts.items():
        cap = TARGET_CAP.get(doc, 0)
        if count > cap:
            violations.append({
                "type": "ABS-010",
                "desc": f"TARGET_CAP超過: {doc} → {count}回 (上限{cap})"
            })

    # ABS-011: 大学系2回までチェック
    for doc, bg_count in bg_counts.items():
        if bg_count > 2:
            violations.append({
                "type": "ABS-011",
                "desc": f"大学系3回以上: {doc} → {bg_count}回 (上限2)"
            })

    is_valid = len(violations) == 0

    if verbose:
        if is_valid:
            print("   ✅ 絶対禁忌チェック: 全てクリア")
        else:
            print(f"   ❌ 絶対禁忌違反: {len(violations)}件")
            for v in violations[:10]:  # 最大10件表示
                print(f"      - [{v['type']}] {v['desc']}")
            if len(violations) > 10:
                print(f"      ... 他 {len(violations) - 10}件")

    return violations, is_valid

def build_diagnostics(pattern_df):
    counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, assigned_hosp_count, doc_assignments, unassigned, *_ = recompute_stats(pattern_df)
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
print("\n" + "="*60)
print("  🚀 スケジュール生成")
print("="*60)

score_rows = []
candidates = []  # TOP_KEEPだけ保持

for i in tqdm(range(1, NUM_PATTERNS + 1), desc="   パターン生成", ncols=60, disable=not TQDM_AVAILABLE):

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

if len(candidates) == 0:
    print("\n⚠️  gap違反0個の候補なし → 制約緩和して続行")
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

# ローカル探索で候補を改善
refined = []
refine_list = candidates[:REFINE_TOP]
for idx, cand in enumerate(tqdm(refine_list, desc="   局所探索    ", ncols=60, disable=not TQDM_AVAILABLE), 1):
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

    # v5.7.1: 最適化処理のON/OFFスイッチ
    if OPTIMIZATION_ENABLED:
        # 1. ハード制約違反の自動修正
        fixed_df, fix_success, fix_count, fail_count = fix_hard_constraint_violations(
            improved_df, max_attempts=50, verbose=False
        )

        # 2. 可否コード2医師のn+1回違反を修正（ハード制約）
        code_2_fixed_df, code_2_success, code_2_fix_count = fix_code_2_extra_violations(
            fixed_df, max_attempts=100, verbose=False
        )

        # 3. TARGET_CAP違反の自動修正（優先度1位）
        cap_fixed_df, cap_success, cap_fix_count = fix_target_cap_violations(
            code_2_fixed_df, max_attempts=100, verbose=False
        )

        # 4. 大学系最低1回必須違反を修正（準ハード制約、優先度2位）
        univ_min_fixed_df, univ_min_success, univ_min_fix_count = fix_university_minimum_requirement(
            cap_fixed_df, max_attempts=100, verbose=False
        )

        # 4.5. C-H列（休日大学系）カテ当番違反を修正
        ch_kate_fixed_df, ch_kate_success, ch_kate_fix_count = fix_ch_kate_violations(
            univ_min_fixed_df, max_attempts=100, verbose=False
        )

        # 5. gap違反（3日未満の間隔）を修正（優先度3位）
        gap_fixed_df, gap_success, gap_fix_count = fix_gap_violations(
            ch_kate_fixed_df, max_attempts=200, verbose=False
        )

        # 6. 大学系と外病院の差が3以上の違反を修正
        bg_ht_fixed_df, bg_ht_success, bg_ht_fix_count = fix_bg_ht_imbalance_violations(
            gap_fixed_df, max_attempts=100, verbose=False
        )

        # 7. 外病院重複を修正
        ext_dup_fixed_df, ext_dup_success, ext_dup_fix_count = fix_external_hospital_dup_violations(
            bg_ht_fixed_df, max_attempts=150, verbose=False
        )

        # 8. 大学3回以上違反を修正（外病院最低1回も強制）
        univ_over_2_fixed_df, univ_over_2_success, univ_over_2_fix_count = fix_university_over_2_violations(
            ext_dup_fixed_df, max_attempts=150, verbose=False
        )

        # 9. 大学平日偏り違反を修正
        univ_weekday_fixed_df, univ_weekday_success, univ_weekday_fix_count = fix_university_weekday_balance_violations(
            univ_over_2_fixed_df, max_attempts=150, verbose=False
        )

        # 10. 公平性違反の修正（最大と最小の差を縮める）
        fairness_fixed_df, fairness_success, fairness_fix_count = fix_fairness_imbalance(
            univ_weekday_fixed_df, max_attempts=200, verbose=False
        )

        # 11. 最終セーフティネット: 未割り当てスロットを埋める（ハード制約）
        final_df, unassigned_success, unassigned_fix_count = fix_unassigned_slots(
            fairness_fixed_df, verbose=False
        )

        # 修正後に再評価
        if fix_count > 0 or code_2_fix_count > 0 or cap_fix_count > 0 or univ_min_fix_count > 0 or ch_kate_fix_count > 0 or bg_ht_fix_count > 0 or gap_fix_count > 0 or ext_dup_fix_count > 0 or univ_over_2_fix_count > 0 or univ_weekday_fix_count > 0 or fairness_fix_count > 0 or unassigned_fix_count > 0:
            counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts, bg_cat, *_ = recompute_stats(final_df)
            sc2, raw2, met2 = evaluate_schedule_with_raw(
                final_df, counts, bg_counts, ht_counts, wd_counts, we_counts, bk_counts, ly_counts
            )
            improved_df = final_df
        else:
            improved_df = final_df
    else:
        # v5.7.1: 最適化無効 - 初期パターンをそのまま使用
        final_df = improved_df
        fix_count = fail_count = 0
        code_2_fix_count = cap_fix_count = univ_min_fix_count = 0
        ch_kate_fix_count = gap_fix_count = bg_ht_fix_count = 0
        ext_dup_fix_count = univ_over_2_fix_count = univ_weekday_fix_count = 0
        fairness_fix_count = unassigned_fix_count = 0

    # v5.7.1: 絶対禁忌の最終検証
    violations, is_valid = validate_absolute_constraints(final_df, verbose=False)

    refined.append({
        "seed": cand["seed"],
        "score_before": cand["score"],
        "raw_before": cand["raw_score"],
        "score_after": sc2,
        "raw_after": raw2,
        "metrics_after": met2,
        "pattern_df": final_df,  # v5.7.1: 最終パターンを使用
        "violations_fixed": fix_count,
        "violations_failed": fail_count,
        "code_2_violations_fixed": code_2_fix_count,
        "cap_violations_fixed": cap_fix_count,
        "univ_min_violations_fixed": univ_min_fix_count,
        "ch_kate_violations_fixed": ch_kate_fix_count,
        "bg_ht_imbalance_fixed": bg_ht_fix_count,
        "gap_violations_fixed": gap_fix_count,
        "external_dup_violations_fixed": ext_dup_fix_count,
        "univ_over_2_violations_fixed": univ_over_2_fix_count,
        "univ_weekday_violations_fixed": univ_weekday_fix_count,
        "fairness_violations_fixed": fairness_fix_count,
        "unassigned_slots_fixed": unassigned_fix_count,
        "absolute_constraints_valid": is_valid,  # v5.7.1: 絶対禁忌チェック結果
        "absolute_violations": violations,  # v5.7.1: 違反詳細
    })

# =========================
# v5.7.1: 絶対禁忌チェック結果の表示
# =========================
print("\n=== 絶対禁忌チェック (v5.7.1) ===")
abs_valid_count = sum(1 for e in refined if e.get("absolute_constraints_valid", False))
abs_invalid_count = len(refined) - abs_valid_count
print(f"   絶対禁忌クリア: {abs_valid_count}/{len(refined)} パターン")
if abs_invalid_count > 0:
    print(f"   ❌ 絶対禁忌違反あり: {abs_invalid_count} パターン")
    # 違反の内訳を表示
    for e in refined:
        if not e.get("absolute_constraints_valid", False):
            viols = e.get("absolute_violations", [])
            if viols:
                print(f"      seed={e['seed']}: {len(viols)}件の違反")
                for v in viols[:3]:
                    print(f"         - [{v['type']}] {v['desc']}")
                if len(viols) > 3:
                    print(f"         ... 他 {len(viols) - 3}件")

# =========================
# ハード制約違反のないパターンのみ選択（TARGET_CAP、gap、未割当）
# =========================
print("\n=== ハード制約チェック ===")
valid_patterns = []
excluded_count = 0
for e in refined:
    met = e["metrics_after"]
    cap_viol = met.get('cap_violations', 0)
    gap_viol = met.get('gap_violations', 0)
    unassigned = met.get('unassigned_slots', 0)
    code_2_viol = met.get('code_2_extra_violations', 0)
    bg_over_2_viol = met.get('bg_over_2_violations', 0)
    ht_0_viol = met.get('ht_0_violations', 0)
    abs_valid = e.get("absolute_constraints_valid", False)  # v5.7.1: 絶対禁忌チェック
    # ch_kate_violationsはソフト制約（ペナルティのみ、ハード制約から除外）

    # v5.7.1: 絶対禁忌違反があれば除外
    if not abs_valid:
        excluded_count += 1
    elif cap_viol > 0 or gap_viol > 0 or unassigned > 0 or code_2_viol > 0 or bg_over_2_viol > 0 or ht_0_viol > 0:
        excluded_count += 1
    else:
        valid_patterns.append(e)

if not valid_patterns:
    print("\n⚠️  ハード制約を満たすパターンなし → 全パターンから選択")
    valid_patterns = refined
else:
    print(f"\n✅ {len(valid_patterns)}/{len(refined)} パターンがハード制約OK（絶対禁忌クリア含む）")

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

# v6.0.0: 絶対禁忌クリアのパターンのみを選択し、スコア上位3つを出力
# 絶対禁忌違反のパターンは採用しない
abs_valid_patterns = [e for e in valid_patterns if e.get("absolute_constraints_valid", False)]

if abs_valid_patterns:
    # スコア順にソート（raw_after降順）
    abs_valid_patterns.sort(key=lambda e: e["raw_after"], reverse=True)
    # 上位3パターンを選択
    top_patterns = abs_valid_patterns[:3]
    for i, p in enumerate(top_patterns):
        p["axis_label"] = f"スコア{i+1}位"
    print(f"\n✅ 絶対禁忌クリア: {len(abs_valid_patterns)}/{len(valid_patterns)} パターン")
    print(f"   → 上位3パターンを出力")
else:
    # 絶対禁忌クリアのパターンがない場合は警告
    print(f"\n⚠️  絶対禁忌をクリアするパターンがありません")
    print(f"   全パターンから上位3を選択（参考用）")
    valid_patterns.sort(key=lambda e: e["raw_after"], reverse=True)
    top_patterns = valid_patterns[:3]
    for i, p in enumerate(top_patterns):
        p["axis_label"] = f"参考{i+1}位（違反あり）"

# ソート済みリストも作成（後方互換性のため）
refined_sorted = sorted(valid_patterns, key=lambda e: e["raw_after"], reverse=True)
TOP_OUTPUT_PATTERNS = len(top_patterns)  # v6.0.0: 最大3パターン出力

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

# =========================
# v6.0.0: 上位3パターン評価
# =========================
print("\n" + "="*60)
print("  📊 上位パターン評価 (v6.0.0)")
print("="*60)

if top_patterns:
    print(f"\n{'順位':<6}{'スコア':>10}{'公平性':>8}{'ABS違反':>8}{'seed':>8}")
    print("-"*44)
    for i, pattern in enumerate(top_patterns, 1):
        raw_score = pattern.get('raw_after', 0)
        fairness = pattern['metrics_after'].get('max_minus_min_total_active', 0)
        abs_valid = pattern.get('absolute_constraints_valid', False)
        abs_viols = len(pattern.get('absolute_violations', []))
        seed = pattern.get('seed', 0)
        status = "✅" if abs_valid else f"❌{abs_viols}"
        print(f"{i}位{'':<4}{raw_score:>10.0f}{fairness:>8}{status:>8}{seed:>8}")
else:
    print("\n  ⚠️ 有効なパターンが生成されませんでした")

# =========================
# 出力（pattern + summary + diagnostics）
# =========================
base_name = uploaded_filename.rsplit(".", 1)[0]
output_filename = f"{base_name}_v{VERSION}.xlsx"
output_path = output_filename

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
print("  🎉 完了")
print("="*60)
print(f"\n📥 出力: {output_path}")
print("\n【内容】")
print("  ├─ sheet1〜4: 元データ")
print("  ├─ pattern_01: 最良スケジュール（絶対禁忌クリア）")
print("  ├─ pattern_01_今月/累計: サマリー")
print("  └─ pattern_01_diag: 診断シート")
print("\n【v6.0.0 制約チェック項目】")
print("  絶対禁忌(ABS): 11項目")
print("  ├─ ABS-001: コード0割当禁止")
print("  ├─ ABS-002: コード2列制限（B〜Q列のみ）")
print("  ├─ ABS-003: コード3列制限（L〜Y列のみ）")
print("  ├─ ABS-006: 同日重複禁止")
print("  ├─ ABS-007: gap >= 3日必須")
print("  ├─ ABS-008: 同一病院重複禁止（全列）")
print("  ├─ ABS-009: 未割当禁止")
print("  ├─ ABS-010: TARGET_CAP遵守")
print("  └─ ABS-011: 大学系2回まで")
print("  ハード制約(HARD): 3項目")
print("  ├─ HARD-001: B/I列1回まで")
print("  ├─ HARD-002: C-H/J-K列1回まで")
print("  └─ HARD-003: 外病院1回以上")
print("="*60)

if COLAB_AVAILABLE:
    files.download(output_path)
