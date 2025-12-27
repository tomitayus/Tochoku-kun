# Google Colab → GitHub 管理ガイド

Google Colabで作成したノートブック（.ipynb）をGitHubで管理する完全ガイドです。

---

## 📋 前提条件

- Google Colabにノートブックがある
- GitHubアカウントを持っている
- （オプション）Gitコマンドの基本知識

---

## 🎯 方法1: Colabから直接GitHubに保存（最も簡単）

### ステップ1: Colabでノートブックを開く

既存のノートブックを開きます。

### ステップ2: GitHubに保存

1. メニューから **「ファイル」→「GitHubにコピーを保存」** を選択
   ```
   File → Save a copy in GitHub
   ```

2. **GitHubアカウントを認証**（初回のみ）
   - ポップアップが表示されたら「承認」をクリック
   - GoogleアカウントとGitHubを連携

3. **保存先を設定**
   ```
   Repository: tomitayus/-  （または任意のリポジトリ）
   Branch: claude/duty-roster-setup-8yW1T  （または main）
   File path: colab/当直くん_v2.1.ipynb
   Commit message: feat: Add Colab notebook for duty roster scheduler v2.1
   ```

4. **「OK」をクリック**

5. **確認**
   - GitHubリポジトリをブラウザで開く
   - `colab/当直くん_v2.1.ipynb` が追加されていることを確認

### メリット
- ✅ 最も簡単（クリックだけ）
- ✅ バージョン管理が自動
- ✅ Colabから直接編集→保存が可能

### デメリット
- ⚠️ 大きなファイル（実行結果含む）も保存される
- ⚠️ 細かいGit操作ができない

---

## 🎯 方法2: ダウンロード → Git管理（推奨）

ローカルでGit操作を行いたい場合。

### ステップ1: Colabからノートブックをダウンロード

1. Colabで **「ファイル」→「ダウンロード」→「.ipynb をダウンロード」**
   ```
   File → Download → Download .ipynb
   ```

2. ダウンロードしたファイルを確認
   ```
   当直くん.ipynb
   ```

### ステップ2: ローカルのGitリポジトリに配置

```bash
# ダウンロードフォルダから移動
mv ~/Downloads/当直くん.ipynb /path/to/your/git/repo/colab/

# または、直接コピー
cp ~/Downloads/当直くん.ipynb /path/to/your/git/repo/colab/当直くん_v2.1.ipynb
```

### ステップ3: Gitにコミット

```bash
cd /path/to/your/git/repo

# ファイル追加
git add colab/当直くん_v2.1.ipynb

# コミット
git commit -m "feat: Add Colab notebook for duty roster scheduler v2.1

- Original version with all dependencies
- Includes data loading, greedy scheduling, and local search
- Ready to use in Google Colab environment
"

# プッシュ
git push origin claude/duty-roster-setup-8yW1T
```

### ステップ4: 確認

```bash
# GitHubで確認
# https://github.com/tomitayus/-/blob/claude/duty-roster-setup-8yW1T/colab/当直くん_v2.1.ipynb
```

---

## 🎯 方法3: Google Drive経由でGitHub同期（自動化）

ColabのノートブックをGoogle Driveに保存し、それをGitHubと同期。

### ステップ1: Colabノートブックをドライブに保存

1. Colabで **「ファイル」→「ドライブにコピーを保存」**
   ```
   File → Save a copy in Drive
   ```

2. 保存場所を指定
   ```
   マイドライブ/Colab Notebooks/当直くん_v2.1.ipynb
   ```

### ステップ2: Google Drive Desktop をインストール

1. [Google Drive Desktop](https://www.google.com/drive/download/) をダウンロード
2. インストール後、Googleアカウントでログイン
3. 同期するフォルダを選択

### ステップ3: ローカルでGit管理

```bash
# Google Driveのフォルダをシンボリックリンク
ln -s ~/Google\ Drive/My\ Drive/Colab\ Notebooks /path/to/your/git/repo/colab

# または、定期的にコピー
cp ~/Google\ Drive/My\ Drive/Colab\ Notebooks/当直くん_v2.1.ipynb \
   /path/to/your/git/repo/colab/

# Gitにコミット
git add colab/当直くん_v2.1.ipynb
git commit -m "chore: Update Colab notebook from Drive"
git push
```

### ステップ4: 自動化（オプション）

**シェルスクリプト作成** (`sync_colab.sh`):

```bash
#!/bin/bash

DRIVE_PATH="$HOME/Google Drive/My Drive/Colab Notebooks"
GIT_REPO="/path/to/your/git/repo"
COLAB_FILE="当直くん_v2.1.ipynb"

# コピー
cp "$DRIVE_PATH/$COLAB_FILE" "$GIT_REPO/colab/"

# Git操作
cd "$GIT_REPO"
git add "colab/$COLAB_FILE"

# 変更があればコミット
if ! git diff --cached --quiet; then
    git commit -m "chore: Auto-sync Colab notebook from Drive"
    git push origin claude/duty-roster-setup-8yW1T
    echo "✅ Synced and pushed to GitHub"
else
    echo "ℹ️ No changes detected"
fi
```

**実行権限付与**:
```bash
chmod +x sync_colab.sh
```

**定期実行（cron）**:
```bash
# crontab -e で以下を追加
# 毎日23時に同期
0 23 * * * /path/to/sync_colab.sh >> /var/log/colab_sync.log 2>&1
```

---

## 📝 ベストプラクティス

### 1. 実行結果をクリアしてからコミット

Colabノートブックは実行結果（セルの出力）も含まれるため、ファイルサイズが大きくなります。

**クリア方法**:
1. Colabで **「編集」→「すべての出力をクリア」**
   ```
   Edit → Clear all outputs
   ```

2. 保存してからGitHubにコミット

### 2. .gitignore の設定

Colabの一時ファイルを除外：

```gitignore
# .gitignore に追加
.ipynb_checkpoints/
*.pyc
__pycache__/
```

### 3. コミットメッセージの工夫

```bash
# 良い例
git commit -m "feat: Add gap violation penalty to scheduler v2.1"
git commit -m "fix: Resolve timezone issue in date parsing"
git commit -m "docs: Add usage examples in Colab notebook"

# 悪い例
git commit -m "update"
git commit -m "fix bug"
```

### 4. ブランチ戦略

```bash
# 機能追加は別ブランチで
git checkout -b feature/improve-local-search

# 編集 → コミット
git add colab/当直くん_v2.1.ipynb
git commit -m "feat: Improve local search algorithm"

# プッシュ
git push origin feature/improve-local-search

# GitHub でプルリクエスト作成
```

---

## 🔄 GitHub → Colab の読み込み

逆に、GitHubのノートブックをColabで開く方法：

### 方法1: URLから直接開く

```
https://colab.research.google.com/github/tomitayus/-/blob/claude/duty-roster-setup-8yW1T/colab/当直くん_v2.1.ipynb
```

URLパターン:
```
https://colab.research.google.com/github/{user}/{repo}/blob/{branch}/{path}
```

### 方法2: Colabから開く

1. Colab で **「ファイル」→「ノートブックを開く」**
2. **「GitHub」タブ** を選択
3. リポジトリとブランチを選択
4. ファイルをクリック

---

## 🛠️ トラブルシューティング

### 問題1: 「GitHub認証に失敗しました」

**解決策**:
1. Googleアカウントの連携を確認
2. GitHubの[Settings → Applications](https://github.com/settings/installations) で "Google Colaboratory" を確認
3. 必要に応じて再認証

### 問題2: 「ファイルサイズが大きすぎます」

**原因**: 実行結果（画像、大量の出力）が含まれている

**解決策**:
1. Colabで **「編集」→「すべての出力をクリア」**
2. 再度GitHubに保存

### 問題3: 「コンフリクトが発生しました」

**原因**: 複数の場所から同じファイルを編集

**解決策**:
```bash
# ローカルで最新を取得
git pull origin claude/duty-roster-setup-8yW1T

# コンフリクトを解決
# エディタでファイルを開き、<<<<<<< と >>>>>>> の間を編集

# コミット
git add colab/当直くん_v2.1.ipynb
git commit -m "fix: Resolve merge conflict in Colab notebook"
git push
```

---

## 📚 参考資料

- [Google Colab公式ドキュメント](https://colab.research.google.com/notebooks/welcome.ipynb)
- [GitHub と Colab の連携](https://colab.research.google.com/github/googlecolab/colabtools/blob/master/notebooks/colab-github-demo.ipynb)
- [Jupyter Notebook のバージョン管理](https://nextjournal.com/schmudde/how-to-version-control-jupyter)

---

## ✅ まとめ

| 方法 | 難易度 | 推奨度 | 用途 |
|-----|--------|--------|------|
| **方法1: Colabから直接保存** | ⭐ | ⭐⭐⭐⭐⭐ | 初心者、手軽に管理したい |
| **方法2: ダウンロード→Git** | ⭐⭐⭐ | ⭐⭐⭐⭐ | 細かいGit操作が必要 |
| **方法3: Drive経由で自動化** | ⭐⭐⭐⭐ | ⭐⭐⭐ | 頻繁に更新する場合 |

**初心者の方は方法1がおすすめです！**
