# 当直くん v5.0 制約仕様書

> 本ドキュメントは制約ルールの完全な定義を提供します。
> 実装コード: `colab_duty_scheduler_v4.7.py`

---

## §1 定義

### 1.1 用語定義

| 用語 | 定義 | コード上の表現 |
|------|------|----------------|
| **active医師** | 当月に割り当て可能な医師。sheet2で少なくとも1日は可否コード≠0、または事前割当がある医師 | `active_doctors` |
| **inactive医師** | 当月に割り当て不可の医師。sheet2で全日が可否コード0かつ事前割当なし。**解析処理から除外し、出力データのみに記載** | `inactive_doctors` |
| **BASE_TARGET** | 基本割当回数。`全枠数 ÷ active医師数`（端数切り捨て） | `BASE_TARGET` |
| **EXTRA_SLOTS** | 余り枠数。`全枠数 - (BASE_TARGET × active医師数)` | `EXTRA_SLOTS` |
| **TARGET_CAP** | 医師別の上限回数。通常は`BASE_TARGET`、余り対象医師は`BASE_TARGET + 1` | `TARGET_CAP[doc]` |
| **BG** | 大学系病院（B〜K列）の略称。Big Group の意 | `bg_counts` |
| **HT** | 外病院（L〜Y列）の略称。Hospital (外) の意 | `ht_counts` |
| **カテ当番** | その日にカテ表（sheet3）でアルファベット（A,B,C,CC,D,E等）が入っている状態 | `get_sched_code()` |
| **カテ保有医師** | sheet3で少なくとも1日、何らかのカテ表コードを持つ医師 | `SCHEDULE_CODE_HOLDERS` |
| **カテなし医師** | sheet3に1つもカテ表コードがない医師（自由に配置可能） | `NO_KATE_DOCTORS` |
| **CC** | 大型連休特別シフト。公平性・重複計算から除外される | `is_cc_assignment()` |
| **gap** | 当直間隔。連続する2つの当直日の日数差 | `gap = date2 - date1` |

### 1.2 列定義（Column Classification）

| 列範囲 | インデックス | 分類 | 説明 |
|--------|-------------|------|------|
| **B列** | 1 | 大学平日① | 平日の大学系当直（昼） |
| **C-H列** | 2-7 | 大学休日 | 土日祝の大学系当直 |
| **I列** | 8 | 大学平日② | 平日の大学系当直（昼） |
| **J-K列** | 9-10 | 大学平日③ | 平日の大学系当直 |
| **L-Y列** | 11-24 | 外病院 | 外部病院への派遣当直 |

**時間帯分類（C-H列内）:**
- **昼（Day）**: C列、E列、F列
- **夜（Night）**: D列、G列

**グループ定義:**
```
B-K列（大学系）= B + C-H + I-K = インデックス 1-10
L-Y列（外病院）= インデックス 11-24
```

### 1.3 可否コード定義（Sheet2）

| コード | 意味 | 配置可能列 | 備考 |
|--------|------|-----------|------|
| **0** | 不可 | なし | その日は割り当て禁止（絶対禁忌） |
| **1** | 可 | B〜Y全て | 通常の配置対象 |
| **1.2** | 大学優先 | B〜Y全て | 大学系（B-K）を最低1回必須（準ハード） |
| **2** | 大学専用 | B〜Q列のみ | 外病院不可、EXTRA枠対象外 |
| **3** | 外病院専用 | L〜Y列のみ | 大学系不可、比率バランス除外 |

**特記事項:**
- **全日0の医師**: `inactive_doctors`として解析処理から完全除外。出力Excelには0回として記載
- **コード2医師**: `BASE_TARGET`を超える割当（n+1回）は禁止（ハード制約）

### 1.4 パラメータ定義

#### TARGET_CAP算出方法
```python
BASE_TARGET = total_slots // len(active_doctors)
EXTRA_SLOTS = total_slots - BASE_TARGET * len(active_doctors)

# 余り枠は右側（sheet2で右にいる医師）から順に割当
# ただしCODE_2医師は除外
EXTRA_ALLOWED = extra_eligible[-EXTRA_SLOTS:]

TARGET_CAP[doc] = BASE_TARGET                    # 通常医師
TARGET_CAP[doc] = BASE_TARGET + 1                # EXTRA対象医師
TARGET_CAP[doc] = max(TARGET_CAP[doc], 事前割当数)  # 事前割当優先
```

#### gap（間隔）の計算方法
```
間隔 = 次回当直日 - 前回当直日 の日数差

例:
  1/1 → 1/2 : gap = 1日 → NG（3日未満）
  1/1 → 1/3 : gap = 2日 → NG（3日未満）
  1/1 → 1/4 : gap = 3日 → OK（3日以上）

判定: gap < 3 → 違反
```

---

## §2 制約一覧

### 2.1 絶対禁忌（違反=即却下・配置不可）

| # | 制約名 | 条件 | 実装 |
|---|--------|------|------|
| 1 | 可否コード0禁止 | `get_avail_code(date, doc) == 0` | `collect_candidates`で除外 |
| 2 | コード2の列制約 | コード2医師がR〜Y列に配置 | `collect_candidates`で除外 |
| 3 | コード3の列制約 | コード3医師がB〜K列に配置 | `collect_candidates`で除外 |
| 4 | カテ当番日の外病院禁止 | カテ保有医師がカテ当番日にL〜Y列配置 | `collect_candidates`で除外 |
| 5 | 同日重複禁止 | 同一医師が同一日に2枠以上 | ロジックで排除 |

### 2.2 ハード制約（違反=パターン除外）

パターン選択時に以下の違反が1件でもあれば候補から除外:

| # | 制約名 | 違反判定 | ペナルティ重み |
|---|--------|----------|---------------|
| 1 | TARGET_CAP超過 | `assigned_count > TARGET_CAP[doc]` | W_CAP=200 |
| 2 | gap違反 | 連続当直の間隔 < 3日 | W_GAP=100 |
| 3 | 未割当枠 | 空き枠が残存 | W_UNASSIGNED=100 |
| 4 | CODE_2のn+1違反 | CODE_2医師が`BASE_TARGET`超過 | ハード制約 |
| 5 | 大学3回以上 | `bg_count >= 3`（CC除く） | ペナルティ150 |
| 6 | 外病院0回 | active医師が`ht_count == 0` | ペナルティ300 |

### 2.3 準ハード制約（条件付き緩和可）

選択肢がない場合に限り、以下の順序で緩和:

| # | 制約名 | 緩和フラグ | 緩和順序 |
|---|--------|-----------|---------|
| 1 | B-K列カテ要件 | `relax_bh_limit=True` | 2番目 |
| 2 | C-H列カテ当番 | `relax_ch_kate=True` | 3番目 |
| 3 | gap制約 | `relax_gap=True` | 4番目 |
| 4 | 大学最低1回 | - | 修正フェーズで対応 |

**緩和適用フロー:**
```
1. 通常制約でチェック
   ↓ 候補なし
2. relax_bh_limit=True で再試行
   ↓ 候補なし
3. relax_ch_kate=True で再試行
   ↓ 候補なし
4. relax_gap=True で再試行
```

### 2.4 ソフト制約（ペナルティ加算）

| # | 制約名 | ペナルティ重み | 説明 |
|---|--------|---------------|------|
| 1 | 公平性 | W_FAIR_TOTAL=30 | `max(割当数) - min(割当数)` の差 |
| 2 | 大学同一病院重複 | W_HOSP_DUP=0 | 許容（ペナルティなし） |
| 3 | 外病院同一病院重複 | W_EXTERNAL_HOSP_DUP=150 | ほぼ禁忌 |
| 4 | 大学ばらつき | W_BG_SPREAD=3 | 累計の標準偏差 |
| 5 | 外病院ばらつき | W_HT_SPREAD=3 | 累計の標準偏差 |
| 6 | 平日ばらつき | W_WD_SPREAD=2 | 累計の標準偏差 |
| 7 | 休日ばらつき | W_WE_SPREAD=3 | 累計の標準偏差 |
| 8 | B-K/L-Y比率バランス | W_BK_LY_BALANCE=2 | 1:1に近づける |
| 9 | CODE_1.2大学0回 | 150 | 大学最低1回未達 |
| 10 | 大学平日2回以上 | 80 | 平日偏り回避 |
| 11 | BG/HT差3以上 | 100 | 大学と外病院の不均衡 |

---

## §3 ペナルティスケール

### スケール解釈

| 範囲 | 意味 | 例 |
|------|------|-----|
| **0** | 許容（制約なし） | 大学同一病院重複 |
| **1-50** | 軽微な非推奨 | ばらつき（2-3）、公平性（30） |
| **51-100** | 中程度の回避対象 | gap違反（100）、平日偏り（80） |
| **101-200** | 強い回避対象 | 外病院重複（150）、CAP超過（200） |
| **200超** | ほぼ禁忌 | 外病院0回（300） |

### 重み定数一覧

```python
# 優先順位: TARGET_CAP > gap > 外病院DUP
W_CAP = 200                # 1位: cap超え（最優先）
W_GAP = 100                # 2位: gap違反
W_EXTERNAL_HOSP_DUP = 150  # 3位: 外病院重複
W_UNASSIGNED = 100         # 未割当
W_FAIR_TOTAL = 30          # 公平性
W_HOSP_DUP = 0             # 大学重複（許容）
W_BG_SPREAD = 3            # 大学ばらつき
W_HT_SPREAD = 3            # 外病院ばらつき
W_WD_SPREAD = 2            # 平日ばらつき
W_WE_SPREAD = 3            # 休日ばらつき
W_BK_LY_BALANCE = 2        # 比率バランス
```

---

## §4 配置ロジック

> 注意: 本セクションは制約定義ではなく、配置アルゴリズムの仕様です。

### 4.1 配置優先順序

```
1. 大学休日（C-H列）← カテ当番制約があるため先に配置
2. 大学平日（B列、I-K列）
3. 外病院（L-Y列）
```

### 4.2 C-H列（休日大学系）の配置ルール

**配置可能条件（OR条件）:**
1. その日にカテ当番がある（sheet3でアルファベットあり）
2. カテなし医師（sheet3に1つもアルファベットがない）

### 4.3 B/I-K列（平日大学系）の配置ルール

**配置可能条件（OR条件）:**
1. カテなし医師
2. その日にカテ当番がある
3. sheet3で「1」を持つ医師（緩和対象）

### 4.4 修正パイプライン（実行順序）

```
#1  fix_hard_constraint_violations()      # 絶対禁忌の修正
#2  fix_code_2_extra_violations()         # CODE_2のn+1違反
#3  fix_target_cap_violations()           # TARGET_CAP超過
#4  fix_university_minimum_requirement()  # 大学最低1回
#5  fix_code_1_2_violations()             # CODE_1.2違反
#6  fix_ch_kate_violations()              # C-Hカテ当番違反
#7  fix_bg_ht_imbalance_violations()      # BG/HT不均衡
#8  fix_gap_violations()                  # gap違反
#9  fix_external_hospital_dup_violations()# 外病院重複
#10 fix_university_over_2_violations()    # 大学3回以上
#11 fix_university_weekday_balance()      # 大学平日偏り
#12 fix_fairness_imbalance()              # 公平性
#13 fix_unassigned_slots()                # 未割当枠
```

---

## §5 inactive医師の扱い

### 定義
```python
def is_always_unavailable(doc):
    # 事前割当があれば対象外
    if preassigned_count.get(doc, 0) > 0:
        return False
    # 全日コード0ならinactive
    return all(get_avail_code(d, doc) == 0 for d in all_shift_dates)

inactive_doctors = [d for d in doctor_names if is_always_unavailable(d)]
```

### 処理方針

| フェーズ | inactive医師の扱い |
|----------|-------------------|
| **解析処理** | 完全除外（候補に含めない） |
| **TARGET_CAP計算** | 除外（active医師のみで計算） |
| **パターン生成** | 除外 |
| **最適化** | 除外 |
| **出力Excel** | 0回として記載（氏名は表示） |

---

## §6 クイックリファレンス

### 列インデックス対応表

| 列名 | インデックス | 分類 | カテ制約 |
|------|-------------|------|---------|
| B | 1 | 大学平日 | 緩和可（sheet3「1」） |
| C | 2 | 大学休日 | カテ当番必須 |
| D | 3 | 大学休日 | カテ当番必須 |
| E | 4 | 大学休日 | カテ当番必須 |
| F | 5 | 大学休日 | カテ当番必須 |
| G | 6 | 大学休日 | カテ当番必須 |
| H | 7 | 大学休日 | カテ当番必須 |
| I | 8 | 大学平日 | 緩和可 |
| J | 9 | 大学平日 | 緩和可 |
| K | 10 | 大学平日 | 緩和可 |
| L-Y | 11-24 | 外病院 | カテ当番日は禁止 |

### 医師分類早見表

| 分類 | 判定条件 | 主な制約 |
|------|----------|---------|
| active | sheet2で1日でも≠0 | 通常配置対象 |
| inactive | sheet2全日=0 | 解析除外、出力のみ |
| CODE_2 | sheet2にコード2あり | 大学専用、n+1禁止 |
| CODE_3 | sheet2にコード3あり | 外病院専用 |
| CODE_1.2 | sheet2にコード1.2あり | 大学最低1回必須 |
| カテ保有 | sheet3にアルファベットあり | カテ当番日のみB-K可 |
| カテなし | sheet3にアルファベットなし | B-K自由配置可 |
| SHEET3「1」 | sheet3に「1」あり | 平日大学系緩和対象 |
| SHEET3「3」 | sheet3に「3」あり | 比率バランス除外 |

---

## 更新履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-01-30 | v5.0 | 制約仕様書を新規作成。用語定義、列分類、ペナルティスケールを明確化 |
