# 当直くん コード品質レビュー報告書

> レビュー日: 2026-02-12
> 対象バージョン: ヘッダー v6.5.6 / VERSION定数 v6.5.0
> レビュー範囲: 全ファイル（colab_duty_scheduler.py, backend/*, frontend/*, docs/*）

---

## 概要

Claudeとの対話で段階的に構築されたコードベースについて、冗長性・矛盾・潜在的バグを網羅的にチェックした。
以下に発見事項を重大度順に報告する。

---

## 重大度：高（修正推奨）

### 1. VERSION定数とヘッダーバージョンの不一致

| 箇所 | バージョン |
|------|-----------|
| ヘッダー（1行目） | `v6.5.6` |
| `VERSION`定数（339行目） | `"6.5.0"` |

出力ファイル名に `VERSION` が使用されるため（`{base_name}_v{VERSION}.xlsx`）、実際の機能と異なるバージョンがファイル名に付与される。

**修正**: `VERSION = "6.5.6"` に更新する。

---

### 2. ABS-005/ABS-006 制約IDの定義コメント入れ違い

定義箇所（405-406行目）:
```python
CONSTRAINT_ABS_005 = "ABS-005"  # 同日重複禁止
CONSTRAINT_ABS_006 = "ABS-006"  # 水曜日L〜Y禁止医師
```

しかし実際のコード使用（1433行目, 5498行目等）:
- `"ABS-005"` → 水曜日L-Y禁止医師（コメントでの使用）
- `"ABS-006"` → 同日重複禁止（`validate_absolute_constraints`での使用）

**問題**: コード全体では定義コメントと逆の意味でIDが使われている。さらに`build_hard_constraint_violations`（3111行目）では`CONSTRAINT_ABS_006`を水曜禁止に使用しているため、**2つの異なる違反が同じID "ABS-006"** で報告される。

**修正**: 定義コメントをコードの実使用に合わせて修正するか、ID文字列自体を正しく付け直す。

---

### 3. 重み定数が3箇所で矛盾（コード・ドキュメント・バックエンド）

| 定数 | colab本体 (v6.0+) | CONSTRAINT_RULES.md (v5.2) | backend/scheduler.py | backend/app.py |
|------|-------------------|---------------------------|---------------------|---------------|
| `W_CAP` | **0** | 200 | 50 | 50 |
| `W_GAP` | **0** | 100 | 3 | 3 |
| `W_EXTERNAL_HOSP_DUP` | **0** | 150 | - | - |
| `W_UNASSIGNED` | **500** | 100 | 100 | 100 |
| `W_FAIR_TOTAL` | **30** | 30 | 10 | 10 |

v6.0.0以降、GAP/CAP/外病院重複は絶対禁忌(ABS)に格上げされペナルティ重み0に変更されたが、ドキュメントとバックエンドは旧仕様のまま。

**修正**:
- `CONSTRAINT_RULES.md` をv6.x仕様に更新する
- `backend/scheduler.py` と `backend/app.py` の重み定数をColab版と同期する

---

### 4. ABS-008「同一病院重複禁止」のスコープが関数ごとに不一致

| 関数 | スコープ | 行 |
|------|---------|-----|
| `collect_candidates` | **全列**（B-Y） | 1475-1477 |
| `is_valid_full_assignment` | **外病院のみ**（L-Y） | 2463-2465 |
| 各fix関数のemergency fallback | **外病院のみ**（L-Y） | 3305, 3664等 |
| `validate_absolute_constraints` | **全列**（B-Y） | 5518-5525 |

初期生成時（`collect_candidates`）は全列で重複を禁止するが、修正フェーズ（`is_valid_full_assignment`やfix関数）では外病院のみ禁止。修正フェーズが初期生成では許可されない配置を作り出す可能性がある。

**修正**: 意図的な設計判断（大学系は重複許容）であればコメントを統一する。意図しない不一致であればスコープを揃える。

---

### 5. `fix_unassigned_slots`の成功フラグが常にTrue

**5447行目**:
```python
return df, (total_fixed == 0 or total_fixed > 0), total_fixed
```

`(total_fixed == 0 or total_fixed > 0)` は任意の整数で常に`True`。未割当が残っていても成功と報告される。

**修正**: `return df, (remaining_unassigned == 0), total_fixed` のように残数ベースで判定する。

---

## 重大度：中（改善推奨）

### 6. CC除外の不整合（3つのfix関数の最終チェック）

以下のfix関数は、メインループではCC（大型連休）を除外して違反をカウントするが、**最終チェック**ではCC除外を忘れている:

| 関数 | メインループ | 最終チェック | 行 |
|------|------------|-----------|-----|
| `fix_bg_ht_imbalance_violations` | CC除外あり | CC除外なし | 4108-4109 |
| `fix_university_over_2_violations` | CC除外あり | CC除外なし | 4645 |
| `fix_external_hospital_dup_violations` | CC除外あり | CC除外なし | 4412-4420 |

結果として、CC割当がある場合に最終チェックで実際より多い違反数が報告される。

---

### 7. `fix_ch_kate_violations`のクロス日swapで同日重複チェック不足

**3914-3953行目**: C-H列違反の修正で異なる日のスロット間でswapする際、移動先の日に当該医師がすでに割り当てられているか（ABS-006同日重複）をチェックしていない。`can_assign_doc_to_slot`は静的制約のみチェックし、同日重複は確認しない。

---

### 8. `get_dayoff_request_priority`関数がどこからも呼ばれていない

**786-805行目**: v6.5.0で休み希望の優先度取得関数を定義しているが、`build_schedule_pattern`や`collect_candidates`からは呼ばれていない。実装途中の機能と思われる。

---

### 9. CONSTRAINT_RULES.md（v5.2仕様書）の乖離

ドキュメントはv5.2（2026-01-31作成）で止まっており、v6.x系で追加された以下の制約が反映されていない:

| 制約 | 追加バージョン | ドキュメント |
|------|-------------|------------|
| ABS-012改（大学系7日間隔） | v6.5.0 | 未記載 |
| ABS-013（C-H列カテ当番必須、旧SEMI-002格上げ） | v6.5.3 | 未記載 |
| ABS-015（属性2のB列カテ表コード欠如） | v6.5.6 | 未記載 |
| SEMI-001の属性による緩和可否 | v6.5.6 | 未記載 |
| 修正パイプラインの収束ループ（safe_fix） | v6.0.3 | 未記載 |
| 段階的ABS緩和（relax_abs） | v6.3.0 | 未記載 |

---

### 10. backend/scheduler.py が未完成のまま放置

`generate_schedules()` メソッドが `pass` のスタブ。`export_excel()` も最小限の実装のみ。`backend/app.py` はこれを呼び出すため、Web版は実行不可能な状態。

Web版固有の問題:
- `SchedulerConfig` に `bg_day_cols`, `bg_night_cols` フィールドがあるがColab版では直接的に対応するものがない
- `ConfigModel.Config.schema_extra` は Pydantic v2 では `model_config` に変更が必要（Pydantic v2.5.0を使用）

---

## 重大度：低（保守性改善）

### 11. 緊急フォールバックロジックの大規模コピペ（5箇所）

ABS-001〜ABS-008のチェックをほぼ同一のコードブロックとして以下の5つのfix関数内で重複定義:

1. `fix_hard_constraint_violations` (3279-3309行目)
2. `fix_code_2_extra_violations` (3636-3667行目)
3. `fix_university_over_2_violations` (4584-4613行目)
4. `fix_university_weekday_balance_violations` (4964-4993行目)
5. `fix_unassigned_slots` (5378-5413行目)

1つの制約ルールが変更されたら5箇所を個別に修正する必要がある。

**提案**: 共通の `is_valid_emergency_candidate(doc, date, hosp, ...)` 関数に抽出する。

---

### 12. `import random`の冗長インポート（9箇所）

334行目でモジュールレベルでインポート済みだが、以下のfix関数内で再インポートしている:
3417, 3486, 3589, 3761, 4063, 4357, 4524, 4904, 5213行目

---

### 13. 未使用変数（4箇所）

| 変数名 | 行 | 関数 |
|--------|-----|------|
| `is_university` | 3276 | `fix_hard_constraint_violations` |
| `is_university` | 3633 | `fix_code_2_extra_violations` |
| `is_university_hosp` | 4581 | `fix_university_over_2_violations` |
| `is_university_hosp` | 4961 | `fix_university_weekday_balance_violations` |

---

### 14. 未使用の関数・変数

| 名前 | 行 | 説明 |
|------|-----|------|
| `fix_code_1_2_violations` | 3817-3820 | 後方互換エイリアスだが呼び出し元なし |
| `wd_we_fix_count` | 5927 | 値を代入後、出力に含まれない |
| `get_dayoff_request_priority` | 786-805 | 定義のみで呼び出し元なし |
| `CONSTRAINT_SEMI_003` | 419 | 定義のみで使用箇所なし |
| `CONSTRAINT_SEMI_004` | 420 | 定義のみで使用箇所なし |

---

### 15. build_schedule_patternのカウント更新ロジック重複

固定割当のカウント更新（1706-1753行目）と自動割当のカウント更新（1860-1911行目）が、ほぼ同一の20行超のコードブロック。hidxの判定、bg/ht/bh/bi/chjk/weekday/weekend/bk/lyカウントの更新が2箇所で独立して書かれている。

**提案**: `update_assignment_counts(doc, date, hosp)` ヘルパー関数に抽出する。

---

### 16. コメントアウトされたearly-exit（3箇所）

以下の3箇所で進捗がない場合のループ早期終了が意図的にコメントアウトされている:

- `fix_hard_constraint_violations` (3328-3330行目)
- `fix_university_minimum_requirement` (3801-3803行目)
- `fix_bg_ht_imbalance_violations` (4103-4105行目)

最大試行回数（50-100回）まで無駄にループし続ける可能性がある。

---

### 17. frontend/index.html のXSS脆弱性

**500-508行目**:
```javascript
result.innerHTML = `
    <div style="color: #666;">
        ${message}
    </div>
`;
```

`showError` 関数でサーバーからのエラーメッセージをエスケープせずに `innerHTML` に挿入している。悪意あるファイル名やエラーメッセージによるXSSの可能性がある。

**修正**: `textContent` を使用するか、エスケープ処理を追加する。

---

## まとめ

| 重大度 | 件数 | 主な分類 |
|--------|------|---------|
| 高 | 5件 | バージョン不一致、制約ID混在、重み矛盾、スコープ不一致、常にTrue |
| 中 | 5件 | CC除外忘れ、同日重複チェック不足、未使用機能、ドキュメント乖離、未完成バックエンド |
| 低 | 7件 | コピペ重複、冗長import、未使用変数・関数、XSS |

最も優先度が高いのは **重み定数の3箇所矛盾（#3）** と **制約IDの入れ違い（#2）** である。
これらは実際の制約判定ロジックには直接影響しないケースもあるが、デバッグ・診断時に誤った情報を提供するリスクがある。
