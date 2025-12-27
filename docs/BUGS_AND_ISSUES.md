# 当直くん - バグと問題点の分析

## 🔴 クリティカルなバグ

### 1. **date_doc_count の KeyError リスク** (local_search_swap関数)
```python
date_doc_count[d1][doc1] -= 1
if date_doc_count[d1][doc1] <= 0:
    del date_doc_count[d1][doc1]
```
**問題**: swap後のrevert時に、既に削除されたキーにアクセスしようとするとKeyErrorが発生
**修正**: defaultdictを使うか、キーの存在チェックを追加

### 2. **同日重複チェックの不完全性**
```python
if date in assigned_dates[doc]:
    continue
```
**問題**: local searchのswap時に同日チェックが `d1 != d2` の条件下でのみ実施される
**影響**: 同じ日のslot同士をswapする際に重複が発生しうる

### 3. **列インデックスのハードコーディング**
```python
B_COL_INDEX = 1
C_COL_INDEX = 2
# ...
U_COL_INDEX = min(20, n_cols - 1)
```
**問題**: Excelの列構造が変わると完全に破綻する
**修正**: 列名からインデックスを動的に取得すべき

### 4. **医師名の完全一致依存**
```python
WED_FORBIDDEN_DOCTORS = {'金城', '山田', '野寺'}
```
**問題**: 全角/半角スペース、表記ゆれで制約が効かない
**修正**: 名前の正規化処理を追加

## 🟡 重大な問題点

### 5. **メモリ使用量の爆発**
```python
NUM_PATTERNS = 10000
candidates.append({...})  # DataFrameを含む辞書
```
**問題**: 各パターンがDataFrame全体を保持するため、10000パターンでメモリ不足
**修正**: TOP_KEEP分のみ保持（現在は実装済みだが、初期ループで全保持）

### 6. **タイムゾーン問題**
```python
date = pd.to_datetime(date).normalize()
```
**問題**: タイムゾーン情報が混在すると比較に失敗
**修正**: 明示的に `tz_localize(None)` を追加

### 7. **cap超過を許容するフォールバック**
```python
cap_ok = [d for d in base_candidates if assigned_count[d] < TARGET_CAP.get(d, 0)]
candidates = cap_ok if cap_ok else base_candidates
```
**問題**: cap_okが空の時、cap超過を許可するが、スコアペナルティが大きくなる
**意図**: 「割り当てない」より「cap超過」を選ぶ設計だが、文書化されていない

### 8. **sheet4のヘッダ検出の脆弱性**
```python
for i in range(min(30, len(g))):
    row = g.iloc[i].astype(str).str.strip()
    if (row == "氏名").any():
        header_row_idx = i
        break
```
**問題**: 「氏名」が30行以内に無いと誤作動
**修正**: エラーメッセージを改善するか、検索範囲を拡大

### 9. **平日/祝日判定の矛盾**
```python
if weekday and idx in (C_COL_INDEX, D_COL_INDEX, F_COL_INDEX, G_COL_INDEX):
    holi = True
```
**問題**: 平日なのに祝日扱いになるロジックがドメイン固有すぎる
**修正**: コメントで説明を追加、または設定化

### 10. **重複列名処理の副作用**
```python
headers = make_unique(headers)
```
**問題**: sheet4で「大学病院」が2列あると「大学病院_2」になり、集計列名と不一致
**修正**: 元データの重複を許さないバリデーション追加

## 🟢 軽微な問題

### 11. **非active医師へのcap設定**
```python
TARGET_CAP = {d: 0 for d in doctor_names}
for d in active_doctors:
    TARGET_CAP[d] = BASE_TARGET + (1 if d in EXTRA_ALLOWED else 0)
```
**問題**: inactive医師のcapが0のまま残るが、preassignedがある場合に矛盾
**修正済み**: 次の行で `if preassigned_count.get(d, 0) > TARGET_CAP.get(d, 0)` で補正済み

### 12. **エラーハンドリングの不足**
- ファイルアップロードが空の場合
- 必須列が存在しない場合
- 日付パースに失敗した場合
**修正**: try-exceptと明確なエラーメッセージを追加

### 13. **性能問題**
- `recompute_stats()` が毎回全DataFrame走査（O(n)）
- local searchで毎iteration全再計算
**改善**: 差分更新（delta update）の実装

## 🔵 設計上の改善点

### 14. **マジックナンバーの多用**
```python
W_FAIR_TOTAL = 10
W_GAP = 3
LOCAL_MAX_ITERS = 3000
```
**改善**: 設定ファイルまたはUI経由で調整可能にする

### 15. **ハードコードされた病院名/医師名**
```python
BG_DAY_COLS = set()
WED_FORBIDDEN_DOCTORS = {'金城', '山田', '野寺'}
```
**改善**: 外部設定ファイル（JSON/YAML）化

### 16. **スコアリングの透明性不足**
- ユーザーがスコアの内訳を理解しにくい
**改善**: 診断シートにスコア計算の詳細を追加済み（良い対応）

## 🛠️ 推奨修正の優先順位

1. **HIGH**: バグ #1, #2, #3 (動作不良につながる)
2. **MEDIUM**: 問題 #5, #6, #8 (データによって失敗する)
3. **LOW**: その他（ユーザビリティ改善）

## 📝 テストケース不足

- 端境条件のテスト（医師数=1, slot数=0等）
- 制約違反データでのテスト
- 大規模データでの性能テスト

## 🔒 セキュリティ懸念（Web化時）

- ファイルアップロードのサイズ制限なし
- 悪意あるExcelファイルの処理（XXE攻撃等）
- ユーザーデータの保存場所・期間の未定義
