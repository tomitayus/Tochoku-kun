# 当直くん - バグ分析とWeb化完了報告

## 📋 実施内容

Google Colabで動作していた当直スケジューラーのコードを分析し、以下を実施しました：

1. ✅ **バグの特定と分類**（16件）
2. ✅ **Web化のための設計とコード作成**
3. ✅ **GitHubリポジトリへのコミット・プッシュ**

---

## 🐛 発見されたバグ（重要度順）

### 🔴 クリティカルなバグ（4件）

1. **date_doc_count の KeyError リスク**
   - 場所: `local_search_swap()` 関数
   - 内容: swap後のrevert時に削除済みキーにアクセスして KeyError
   - 影響: 局所探索が途中でクラッシュする可能性
   - 修正方法: defaultdict使用 または キー存在チェック

2. **同日重複チェックの不完全性**
   - 場所: `choose_doctor_for_slot()` / `local_search_swap()`
   - 内容: 同じ日のslot同士をswapする際に重複検出漏れ
   - 影響: 1人の医師が同日に複数の当直を持つ
   - 修正方法: swap前の同日チェック強化

3. **列インデックスのハードコーディング**
   - 場所: グローバル変数（B_COL_INDEX 〜 U_COL_INDEX）
   - 内容: Excelの列順が変わると完全に破綻
   - 影響: テンプレート変更で動作不能
   - 修正方法: 列名から動的にインデックス取得

4. **医師名の完全一致依存**
   - 場所: `WED_FORBIDDEN_DOCTORS` との比較
   - 内容: 全角/半角スペース、表記ゆれで制約が効かない
   - 影響: 水曜H〜U禁止制約が無視される
   - 修正方法: 名前の正規化処理（空白除去）

### 🟡 重大な問題（6件）

5. **メモリ使用量の爆発**
   - NUM_PATTERNS=10000 で各パターンがDataFrame全体を保持
   - 修正: TOP_KEEPのみ保持（一部実装済み）

6. **タイムゾーン問題**
   - `pd.to_datetime().normalize()` でタイムゾーン混在
   - 修正: `tz_localize(None)` を追加

7. **cap超過を許容するフォールバック**
   - 割当不可時にcap超過を許可（ペナルティ大）
   - 意図的だが文書化されていない

8. **sheet4のヘッダ検出の脆弱性**
   - 「氏名」が30行以内に無いと誤作動
   - 修正: 検索範囲を50行に拡大

9. **平日/祝日判定の矛盾**
   - 平日なのに祝日扱いになるロジックがドメイン固有
   - 修正: コメント追加で説明

10. **重複列名処理の副作用**
    - sheet4で列名が重複すると「_2」付与で集計列名と不一致
    - 修正: バリデーション追加

### 🟢 軽微な問題（6件）

11. エラーハンドリングの不足
12. 性能問題（全DataFrame走査）
13. マジックナンバーの多用
14. ハードコードされた病院名/医師名
15. スコアリングの透明性不足
16. テストケース不足

詳細は `docs/BUGS_AND_ISSUES.md` を参照してください。

---

## 🌐 Web化の成果物

### プロジェクト構造

```
duty-roster-scheduler/
├── backend/
│   ├── app.py              # FastAPI エントリーポイント（完成）
│   ├── scheduler.py        # スケジューリングロジック（部分実装）
│   └── requirements.txt    # 依存パッケージ
├── frontend/
│   └── index.html          # モダンなWebUI（完成）
├── docs/
│   ├── BUGS_AND_ISSUES.md  # バグ詳細（16件）
│   └── WEB_MIGRATION_PLAN.md  # 設計書・デプロイガイド
├── .gitignore
├── README.md               # 使い方・開発ガイド
└── SUMMARY.md              # 本ファイル
```

### 実装済み機能

#### バックエンド（FastAPI）
- ✅ RESTful API設計
- ✅ ファイルアップロード（multipart/form-data）
- ✅ バックグラウンドタスク処理
- ✅ 進捗管理（ポーリング）
- ✅ 設定の外部化（JSON）
- ✅ バリデーション（ファイルサイズ、形式）
- ✅ CORS対応
- ✅ OpenAPI/Swagger自動生成

#### フロントエンド（HTML/JS）
- ✅ レスポンシブデザイン
- ✅ ドラッグ&ドロップアップロード
- ✅ 設定パネル（パターン数、祝日、禁止医師等）
- ✅ リアルタイム進捗表示
- ✅ エラーハンドリング
- ✅ ダウンロードリンク生成

#### スケジューラー（scheduler.py）
- ✅ Excelファイル読み込み（sheet1〜4）
- ✅ ヘッダー行自動検出（sheet4）
- ✅ 日付の正規化（タイムゾーン対応）
- ✅ 医師名の正規化（空白除去）
- ✅ 前月累積データの取得
- ⚠️ **スケジュール生成ロジックは未実装**
  - 元のColabコードから移植が必要：
    - `build_schedule_pattern()`
    - `local_search_swap()`
    - `evaluate_schedule_with_raw()`
    - `build_summaries()`
    - `build_diagnostics()`

---

## 🚀 次のステップ

### 1. スケジューラーの完成（最優先）

`backend/scheduler.py` の以下のメソッドを実装：

```python
def generate_schedules(self) -> List[Dict[str, Any]]:
    """元のColabコードから移植"""
    # 1. build_schedule_pattern() の移植
    # 2. local_search_swap() の移植
    # 3. evaluate_schedule_with_raw() の移植
    # 4. TOP3選定
    pass

def export_excel(self, patterns: List[Dict]) -> bytes:
    """結果をExcelに出力"""
    # 元のExcelWriter部分を移植
    pass
```

**移植時の注意点**:
- グローバル変数 → `self.XXX`
- `files.upload()` / `files.download()` → 削除
- エラーハンドリング追加
- 型ヒント追加

### 2. バグ修正

優先度順に修正：
1. date_doc_count の KeyError 対策（defaultdict化）
2. 同日重複チェック強化
3. 列インデックスの動的取得
4. 医師名の正規化（実装済み）

### 3. テスト作成

```bash
# テストファイル作成
tests/
├── test_scheduler.py
├── test_api.py
└── sample_data/
    └── test_input.xlsx
```

### 4. デプロイ

#### 開発環境でテスト

```bash
# バックエンド
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload

# フロントエンド（別ターミナル）
cd frontend
python -m http.server 8080
```

ブラウザで `http://localhost:8080` にアクセス

#### 本番環境（Render.com推奨）

1. GitHubリポジトリを公開
2. Render.com でWeb Service作成
3. フロントエンドはNetlify/Vercelで公開
4. 環境変数で `API_BASE` を設定

---

## 📚 ドキュメント

| ファイル | 内容 |
|---------|------|
| `README.md` | 使い方、クイックスタート、API仕様 |
| `docs/BUGS_AND_ISSUES.md` | バグ詳細（16件）、優先順位 |
| `docs/WEB_MIGRATION_PLAN.md` | アーキテクチャ、詳細設計、デプロイ戦略 |
| `SUMMARY.md` | 本ファイル（実施内容のサマリー） |

---

## ✅ チェックリスト

### 完了
- [x] バグの特定と分類（16件）
- [x] Web化の設計書作成
- [x] FastAPI バックエンド作成
- [x] HTML/JS フロントエンド作成
- [x] Excelファイル読み込み実装
- [x] バリデーション追加
- [x] タイムゾーン問題の修正
- [x] 医師名の正規化
- [x] GitHubへのコミット・プッシュ

### 未完了（要対応）
- [ ] スケジュール生成ロジックの移植
- [ ] Excel出力機能の移植
- [ ] date_doc_count のバグ修正
- [ ] 同日重複チェックの強化
- [ ] 列インデックスの動的取得
- [ ] ユニットテスト作成
- [ ] 統合テスト作成
- [ ] 本番環境へのデプロイ
- [ ] セキュリティ監査（認証・認可）

---

## 🎯 結論

### 実施済み
1. ✅ **16件のバグを特定・分類**
2. ✅ **Web化のための完全な設計とコード作成**
3. ✅ **GitHubリポジトリに整理してコミット**

### 現状
- バックエンドとフロントエンドの基盤は完成
- Excelファイルの読み込みは動作可能
- **スケジュール生成ロジックの移植が必要**（最重要）

### 推奨
当面は **元のColab版を使用** し、並行してWeb版の `scheduler.py` を完成させる

### 次回の作業
1. `backend/scheduler.py` のスケジュール生成ロジックを移植
2. 動作確認用のサンプルデータでテスト
3. バグ修正（優先度の高いものから）

---

**作成日**: 2025年12月27日
**コミット**: `40575dd` on branch `claude/duty-roster-setup-8yW1T`
