# 当直くん - Web化移行プラン

## 🎯 目標

Google Colab依存のコードをWebアプリケーションに変換する

## 🏗️ アーキテクチャ選択肢

### オプション1: Flask/FastAPI + JavaScript フロントエンド（推奨）

**構成**:
```
Frontend (HTML/JS) ──HTTP──> Backend (Python/FastAPI)
     │                              │
     │                              ├─ pandas/openpyxl
     │                              ├─ numpy
     │                              └─ スケジューリングロジック
     │
    User Browser
```

**メリット**:
- 既存のPythonコードをほぼそのまま利用可能
- pandasの高速処理を活かせる
- デバッグが容易

**デメリット**:
- サーバー環境が必要（コスト）
- スケーラビリティの考慮が必要

---

### オプション2: Pyodide (Python in Browser)

**構成**:
```
Browser (WebAssembly + Pyodide)
    ├─ Python interpreter
    ├─ pandas/numpy (WASM版)
    └─ スケジューリングロジック
```

**メリット**:
- サーバー不要（静的ホスティング可）
- プライバシー保護（ファイルがサーバーに送信されない）
- 低コスト

**デメリット**:
- 初回ロードが遅い（20-30MB）
- ブラウザのメモリ制限
- デバッグが困難

---

### オプション3: Streamlit（最速プロトタイプ）

**構成**:
```
Streamlit App (Python)
    ├─ ファイルアップロードUI
    ├─ スケジューリングロジック
    └─ 結果表示UI
```

**メリット**:
- 最小限のコード変更で動作
- UIを自動生成
- デプロイが簡単（Streamlit Cloud）

**デメリット**:
- カスタマイズ性が低い
- 商用利用の制限

---

## 📋 推奨: オプション1（FastAPI）の詳細設計

### ディレクトリ構造
```
duty-roster-scheduler/
├── backend/
│   ├── app.py              # FastAPI エントリーポイント
│   ├── scheduler.py        # スケジューリングロジック
│   ├── models.py           # データモデル
│   ├── utils.py            # ユーティリティ関数
│   ├── config.py           # 設定管理
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── components/
│       ├── FileUpload.js
│       ├── SettingsPanel.js
│       └── ResultsView.js
├── tests/
│   ├── test_scheduler.py
│   └── sample_data/
├── docs/
│   ├── API.md
│   └── USER_GUIDE.md
├── .gitignore
├── README.md
└── docker-compose.yml
```

### API設計

```yaml
POST /api/schedule/generate
  Request:
    - file: Excel file (multipart/form-data)
    - config: JSON
      {
        "num_patterns": 1000,
        "local_search_enabled": true,
        "weights": {
          "fair_total": 10,
          "gap": 3,
          ...
        },
        "wed_forbidden_doctors": ["金城", "山田"],
        "holidays": ["2026-01-01", ...]
      }
  Response:
    {
      "task_id": "uuid-xxxx",
      "status": "processing"
    }

GET /api/schedule/status/{task_id}
  Response:
    {
      "status": "completed|processing|failed",
      "progress": 75,
      "result_url": "/api/schedule/download/uuid-xxxx"
    }

GET /api/schedule/download/{task_id}
  Response:
    - Excel file (binary)
```

### フロントエンド主要機能

1. **ファイルアップロード**
   ```javascript
   // Drag & Drop対応
   dropZone.addEventListener('drop', (e) => {
     const file = e.dataTransfer.files[0];
     uploadFile(file);
   });
   ```

2. **設定パネル**
   - パターン数選択（100/1000/10000）
   - 重み調整スライダー
   - 祝日カレンダー入力
   - 禁止医師設定

3. **進捗表示**
   ```javascript
   // WebSocketまたはポーリングで進捗取得
   const checkStatus = async (taskId) => {
     const res = await fetch(`/api/schedule/status/${taskId}`);
     const data = await res.json();
     updateProgressBar(data.progress);
   };
   ```

4. **結果表示**
   - TOP3パターンのプレビュー
   - スコア比較表
   - 診断シート表示（gap違反、重複等）

---

## 🔧 コード分割戦略

### 1. backend/scheduler.py
```python
# Google Colab依存部分を削除
# - from google.colab import files → 削除
# - files.upload() → FastAPIのUploadFileで受け取り
# - files.download() → BytesIOで返却

class DutyScheduler:
    def __init__(self, config: dict):
        self.config = config
        # 設定の読み込み

    def load_excel(self, file_content: bytes) -> dict:
        """Excelファイルを解析"""
        xls = pd.ExcelFile(io.BytesIO(file_content))
        # 既存のparse処理
        return {...}

    def generate_schedules(self, data: dict) -> list:
        """スケジュール生成（既存ロジック）"""
        # build_schedule_pattern()の処理
        return patterns

    def optimize_local_search(self, pattern: pd.DataFrame) -> pd.DataFrame:
        """局所探索（既存ロジック）"""
        # local_search_swap()の処理
        return optimized_pattern

    def export_excel(self, patterns: list) -> bytes:
        """結果をExcelに出力"""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 既存の出力処理
        return output.getvalue()
```

### 2. backend/app.py
```python
from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
import uuid

app = FastAPI()

# タスク管理（本番はRedis/DB使用）
tasks = {}

@app.post("/api/schedule/generate")
async def generate_schedule(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    config: dict = None
):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing", "progress": 0}

    # バックグラウンドで処理
    background_tasks.add_task(process_schedule, task_id, file, config)

    return {"task_id": task_id, "status": "processing"}

async def process_schedule(task_id: str, file: UploadFile, config: dict):
    try:
        content = await file.read()
        scheduler = DutyScheduler(config or {})

        # 処理（進捗更新付き）
        data = scheduler.load_excel(content)
        tasks[task_id]["progress"] = 20

        patterns = scheduler.generate_schedules(data)
        tasks[task_id]["progress"] = 80

        result = scheduler.export_excel(patterns)
        tasks[task_id]["result"] = result
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 100

    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)

@app.get("/api/schedule/download/{task_id}")
async def download_schedule(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] != "completed":
        return {"error": "Task not found or not completed"}

    return StreamingResponse(
        io.BytesIO(task["result"]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=schedule.xlsx"}
    )
```

### 3. frontend/app.js
```javascript
class SchedulerApp {
  constructor() {
    this.apiBase = '/api/schedule';
  }

  async uploadFile(file, config) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('config', JSON.stringify(config));

    const res = await fetch(`${this.apiBase}/generate`, {
      method: 'POST',
      body: formData
    });

    const { task_id } = await res.json();
    this.pollStatus(task_id);
  }

  async pollStatus(taskId) {
    const interval = setInterval(async () => {
      const res = await fetch(`${this.apiBase}/status/${taskId}`);
      const data = await res.json();

      this.updateProgress(data.progress);

      if (data.status === 'completed') {
        clearInterval(interval);
        this.showDownloadButton(taskId);
      } else if (data.status === 'failed') {
        clearInterval(interval);
        this.showError(data.error);
      }
    }, 1000);
  }

  showDownloadButton(taskId) {
    const btn = document.createElement('a');
    btn.href = `${this.apiBase}/download/${taskId}`;
    btn.textContent = 'ダウンロード';
    btn.download = 'schedule.xlsx';
    document.body.appendChild(btn);
  }
}
```

---

## 🚀 デプロイ戦略

### 開発環境
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload

# Frontend
cd frontend
python -m http.server 8080
```

### 本番環境（例: Render.com）

1. **backend**: Render Web Service
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`

2. **frontend**: Render Static Site or Netlify

### Docker化
```dockerfile
# backend/Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## ✅ マイグレーションチェックリスト

- [ ] Colab依存の削除（files.upload/download）
- [ ] 設定の外部化（YAML/JSON）
- [ ] エラーハンドリング強化
- [ ] バリデーション追加（ファイルサイズ、形式）
- [ ] セキュリティ対策（ファイルスキャン、サイズ制限）
- [ ] ログ機構追加
- [ ] ユニットテスト作成
- [ ] API文書化（OpenAPI/Swagger）
- [ ] フロントエンドのレスポンシブ対応
- [ ] 多言語対応（i18n）準備
- [ ] パフォーマンステスト（1000パターン生成）
- [ ] CI/CD設定（GitHub Actions）

---

## 📊 想定される性能

| パターン数 | 処理時間（推定） | メモリ使用量 |
|-----------|----------------|-------------|
| 100       | 5-10秒         | 200MB       |
| 1000      | 30-60秒        | 500MB       |
| 10000     | 5-10分         | 2GB         |

**最適化案**:
- Celery/RQでタスクキュー化
- 並列処理（multiprocessing）
- Cython化（ホットパス）
