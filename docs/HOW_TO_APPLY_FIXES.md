# バグ修正の適用方法

元のColabノートブックにバグ修正を適用する方法を説明します。

---

## 🎯 方法1: 修正版ファイルを使う（推奨・最も簡単）

### ステップ1: 修正版ファイルをダウンロード

GitHubリポジトリから：
```
当直くん_v2.1_バグ修正版.py
```

### ステップ2: Colabで新しいノートブックを作成

1. [Google Colab](https://colab.research.google.com/) にアクセス
2. **「ファイル」→「ノートブックを新規作成」**

### ステップ3: 修正版コードを貼り付け

1. **新しいコードセルを作成**
2. `当直くん_v2.1_バグ修正版.py` の内容を **全選択してコピー**
3. Colabのコードセルに **貼り付け**

### ステップ4: 保存

1. **「ファイル」→「ドライブにコピーを保存」**
2. ファイル名を変更: `当直くん_v2.1_バグ修正版.ipynb`

### ステップ5: 実行

1. **「ランタイム」→「すべてのセルを実行」**
2. ファイル選択ダイアログでExcelファイルを選択
3. 処理完了を待つ

---

## 🎯 方法2: 既存のColabノートブックに修正を適用

元のノートブックを維持しながら、バグ修正だけを適用する方法。

### 修正箇所リスト

以下の修正を**順番に**適用してください：

---

#### 修正1: 医師名の正規化関数を追加

**場所**: `safe_str()` 関数の直後

**追加するコード**:
```python
# 🔧 FIX: 医師名の正規化関数を追加
def normalize_name(name):
    """医師名を正規化（全角/半角スペース除去）"""
    if pd.isna(name):
        return ""
    return str(name).strip().replace(" ", "").replace("　", "")
```

---

#### 修正2: sheet4ヘッダ検出範囲の拡大

**場所**: `parse_sheet4_from_grid()` 関数内

**変更前**:
```python
search_limit = min(30, len(g))  # 元のコード
```

**変更後**:
```python
search_limit = min(50, len(g))  # 🔧 FIX: 30→50に拡大
```

---

#### 修正3: タイムゾーンの正規化

**場所**: 日付列の整形部分（3箇所）

**変更前**:
```python
shift_df[date_col_shift] = pd.to_datetime(shift_df[date_col_shift], errors="coerce").dt.normalize()
```

**変更後**:
```python
shift_df[date_col_shift] = pd.to_datetime(shift_df[date_col_shift], errors="coerce").dt.normalize().dt.tz_localize(None)  # 🔧 FIX
```

**適用箇所**:
- `shift_df[date_col_shift]` の行
- `availability_raw[date_col_avail]` の行
- `schedule_raw[date_col_sched]` の行

**追加**: 祝日の正規化も修正
```python
# 変更前
HOLIDAYS = {pd.to_datetime(d).normalize() for d in HOLIDAYS}

# 変更後
HOLIDAYS = {pd.to_datetime(d).normalize().tz_localize(None) for d in HOLIDAYS}  # 🔧 FIX
```

---

#### 修正4: 医師名リストの正規化

**場所**: 基本情報の抽出部分

**変更前**:
```python
doctor_names = [safe_str(x) for x in list(availability_raw.columns[1:])]
```

**変更後**:
```python
doctor_names = [normalize_name(x) for x in list(availability_raw.columns[1:])]  # 🔧 FIX
```

**追加**: 禁止医師名も正規化
```python
# 🔧 FIX: 禁止医師名も正規化
WED_FORBIDDEN_DOCTORS = {normalize_name(d) for d in WED_FORBIDDEN_DOCTORS}
```

---

#### 修正5: 固定割当の医師名正規化

**場所**: `slots_by_date` の前計算部分

**変更前**:
```python
if isinstance(val, str) and val.strip() in doctor_names:
    doc = val.strip()
```

**変更後**:
```python
val_str = normalize_name(val) if isinstance(val, str) else ""  # 🔧 FIX
if val_str in doctor_names:
    doc = val_str
```

---

#### 修正6: date_doc_count の defaultdict 化

**場所**: `build_date_doc_count()` 関数

**変更前**:
```python
def build_date_doc_count(pattern_df):
    """date -> doc -> count（同日複数割当検出も兼ねる）"""
    date_doc_count = defaultdict(lambda: defaultdict(int))  # これは既に正しい
```

この部分は**既に修正済み**の可能性が高いです。確認してください。

---

#### 修正7: recompute_stats() での医師名正規化

**場所**: `recompute_stats()` 関数内

**変更前**:
```python
v = val.strip()
```

**変更後**:
```python
v = normalize_name(val)  # 🔧 FIX
```

---

#### 修正8: evaluate_schedule_with_raw() での正規化

**場所**: `evaluate_schedule_with_raw()` 関数内

**変更前**:
```python
if isinstance(v, str) and v.strip() == "UNASSIGNED":
```

**変更後**:
```python
if isinstance(v, str) and normalize_name(v) == "UNASSIGNED":  # 🔧 FIX
```

**追加**: 日付の正規化
```python
date = pd.to_datetime(date).normalize().tz_localize(None)  # 🔧 FIX
```

**追加**: 医師名の正規化
```python
val_norm = normalize_name(val) if isinstance(val, str) else ""  # 🔧 FIX
if val_norm in doctor_names:
    dates_by_doc[val_norm].append(date)
    hosp_counts_by_doc[val_norm][hosp] += 1
```

---

#### 修正9: local_search_swap() での正規化

**場所**: `local_search_swap()` 関数内

**変更前**:
```python
doc1 = v1.strip()
doc2 = v2.strip()
```

**変更後**:
```python
doc1 = normalize_name(v1)  # 🔧 FIX
doc2 = normalize_name(v2)  # 🔧 FIX
```

---

#### 修正10: count_doc_in_column() での正規化

**場所**: `count_doc_in_column()` 関数

**変更前**:
```python
if isinstance(v, str) and v.strip() == doc:
```

**変更後**:
```python
if isinstance(v, str) and normalize_name(v) == doc:  # 🔧 FIX
```

---

### 修正の確認

すべての修正を適用したら、以下をテスト：

1. **ファイルアップロード**が正常に動作するか
2. **医師名に空白が含まれるデータ**で実行
3. **エラーメッセージ**が表示されないか確認

---

## 🎯 方法3: 差分パッチを適用（上級者向け）

Gitの差分パッチ機能を使う方法。

### ステップ1: 元のファイルとの差分を生成

```bash
# 元のファイル（仮に old_version.py とする）と修正版の差分
diff -u old_version.py 当直くん_v2.1_バグ修正版.py > fixes.patch
```

### ステップ2: パッチを適用

```bash
# 元のファイルにパッチを適用
patch old_version.py < fixes.patch
```

---

## 📝 修正の優先順位

時間がない場合は、以下の順で修正してください：

### 🔴 最優先（クリティカル）

1. **医師名の正規化** (修正1, 4, 5, 7, 8, 9, 10)
   - 空白による制約ミスを防止

2. **タイムゾーン問題** (修正3)
   - 日付比較の失敗を防止

### 🟡 重要

3. **sheet4ヘッダ検出** (修正2)
   - 一部のExcelファイルで読み込み失敗を防止

4. **date_doc_count** (修正6)
   - KeyError を防止

### 🟢 推奨

5. **その他の正規化** (修正7-10)
   - より堅牢な動作を保証

---

## ✅ 修正完了のチェックリスト

- [ ] `normalize_name()` 関数を追加した
- [ ] sheet4のヘッダ検出範囲を50行に拡大した
- [ ] すべての日付に `.tz_localize(None)` を追加した
- [ ] 医師名リストを `normalize_name()` で処理した
- [ ] 禁止医師名を正規化した
- [ ] 固定割当の医師名を正規化した
- [ ] `recompute_stats()` で医師名を正規化した
- [ ] `evaluate_schedule_with_raw()` で正規化した
- [ ] `local_search_swap()` で正規化した
- [ ] `count_doc_in_column()` で正規化した
- [ ] テストデータで動作確認した

---

## 🆘 困ったときは

### 「どこを修正すればいいかわからない」

→ **方法1（修正版ファイルを使う）** が最も簡単です

### 「修正したけどエラーが出る」

→ 以下を確認：
1. `normalize_name()` 関数が定義されているか
2. すべての `normalize_name()` 呼び出しが正しいか
3. インデント（字下げ）が正しいか

### 「元のファイルと修正版の違いを確認したい」

→ GitHubで差分を確認：
```
https://github.com/tomitayus/-/compare/...
```

---

## 📚 参考情報

- [バグ詳細リスト](BUGS_AND_ISSUES.md)
- [Colab-GitHub連携ガイド](COLAB_GITHUB_GUIDE.md)
- [Web化移行プラン](WEB_MIGRATION_PLAN.md)
