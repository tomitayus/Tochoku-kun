"""
当直スケジューラー - FastAPI バックエンド
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import io
from datetime import datetime

from scheduler import DutyScheduler, SchedulerConfig


app = FastAPI(
    title="当直スケジューラー API",
    description="医師の当直スケジュールを自動生成するAPI",
    version="1.0.0"
)

# CORS設定（本番環境では制限すること）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では特定のドメインのみ許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== データモデル =====

class ConfigModel(BaseModel):
    """スケジューラー設定"""
    holidays: List[str] = Field(default_factory=list, description="祝日リスト（YYYY-MM-DD形式）")
    wed_forbidden_doctors: List[str] = Field(default_factory=list, description="水曜H〜U禁止医師")
    num_patterns: int = Field(default=1000, ge=10, le=10000, description="生成パターン数")
    local_search_enabled: bool = Field(default=True, description="局所探索を有効化")

    # スコア重み（v6.0.0以降: GAP/CAP/外病院重複はABS制約に格上げされペナルティ重み0）
    w_fair_total: float = Field(default=30, description="全合計の公平性重み")
    w_gap: float = Field(default=0, description="gap違反の重み（ABS-007で対応、ペナルティ不要）")
    w_hosp_dup: float = Field(default=0, description="同一病院重複の重み（ABS-008で対応、ペナルティ不要）")
    w_unassigned: float = Field(default=500, description="未割当の重み")
    w_cap: float = Field(default=0, description="cap超過の重み（ABS-010で対応、ペナルティ不要）")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "holidays": ["2026-01-01", "2026-05-03"],
                "wed_forbidden_doctors": ["金城", "山田"],
                "num_patterns": 1000,
                "local_search_enabled": True
            }]
        }
    }


class TaskStatus(BaseModel):
    """タスクステータス"""
    task_id: str
    status: str  # processing, completed, failed
    progress: int = 0
    message: Optional[str] = None
    result_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ===== タスク管理 =====
# 本番環境ではRedis/DBを使用すること
tasks: Dict[str, Dict[str, Any]] = {}


def create_scheduler_config(config_model: ConfigModel) -> SchedulerConfig:
    """ConfigModelからSchedulerConfigを生成"""
    import pandas as pd

    config = SchedulerConfig(
        holidays={pd.to_datetime(d) for d in config_model.holidays},
        wed_forbidden_doctors=set(config_model.wed_forbidden_doctors),
        num_patterns=config_model.num_patterns,
        local_search_enabled=config_model.local_search_enabled,
        w_fair_total=config_model.w_fair_total,
        w_gap=config_model.w_gap,
        w_hosp_dup=config_model.w_hosp_dup,
        w_unassigned=config_model.w_unassigned,
        w_cap=config_model.w_cap,
    )

    return config


# ===== エンドポイント =====

@app.get("/")
async def root():
    """ルート"""
    return {
        "message": "当直スケジューラー API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/api/schedule/generate", response_model=TaskStatus)
async def generate_schedule(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Excel入力ファイル"),
    config: Optional[str] = None  # JSON文字列として受け取り
):
    """
    スケジュール生成を開始

    - **file**: sheet1〜sheet4を含むExcelファイル
    - **config**: 設定（JSON形式、オプション）
    """
    # ファイルバリデーション
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Excelファイル（.xlsx/.xls）を指定してください")

    # サイズチェック（10MB制限）
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="ファイルサイズは10MB以下にしてください")

    # 設定のパース
    config_model = ConfigModel()
    if config:
        import json
        try:
            config_dict = json.loads(config)
            config_model = ConfigModel(**config_dict)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"設定のパースに失敗: {e}")

    # タスク作成
    task_id = str(uuid.uuid4())
    now = datetime.now()

    tasks[task_id] = {
        "task_id": task_id,
        "status": "processing",
        "progress": 0,
        "message": "処理を開始しました",
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }

    # バックグラウンド処理
    background_tasks.add_task(
        process_schedule,
        task_id=task_id,
        file_content=content,
        config_model=config_model
    )

    return TaskStatus(
        task_id=task_id,
        status="processing",
        progress=0,
        message="処理を開始しました",
        created_at=now,
        updated_at=now
    )


async def process_schedule(task_id: str, file_content: bytes, config_model: ConfigModel):
    """スケジュール生成の実処理（バックグラウンド）"""
    try:
        # 進捗更新
        def update_progress(progress: int, message: str):
            tasks[task_id]["progress"] = progress
            tasks[task_id]["message"] = message
            tasks[task_id]["updated_at"] = datetime.now()

        update_progress(5, "Excelファイルを読み込み中...")

        # スケジューラー初期化
        config = create_scheduler_config(config_model)
        scheduler = DutyScheduler(config)

        # データ読み込み
        update_progress(15, "データを解析中...")
        scheduler.load_excel(file_content)

        # スケジュール生成
        update_progress(30, f"スケジュールを生成中（{config_model.num_patterns}パターン）...")
        patterns = scheduler.generate_schedules()

        # Excel出力
        update_progress(90, "結果をExcelに出力中...")
        result_bytes = scheduler.export_excel(patterns)

        # 完了
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["message"] = "処理が完了しました"
        tasks[task_id]["result"] = result_bytes
        tasks[task_id]["result_url"] = f"/api/schedule/download/{task_id}"
        tasks[task_id]["updated_at"] = datetime.now()

    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = str(e)
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["updated_at"] = datetime.now()
        print(f"Error in task {task_id}: {e}")
        import traceback
        traceback.print_exc()


@app.get("/api/schedule/status/{task_id}", response_model=TaskStatus)
async def get_schedule_status(task_id: str):
    """
    タスクのステータスを取得

    - **task_id**: タスクID
    """
    task = tasks.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    return TaskStatus(
        task_id=task["task_id"],
        status=task["status"],
        progress=task["progress"],
        message=task.get("message"),
        result_url=task.get("result_url"),
        created_at=task["created_at"],
        updated_at=task["updated_at"]
    )


@app.get("/api/schedule/download/{task_id}")
async def download_schedule(task_id: str):
    """
    生成されたスケジュールをダウンロード

    - **task_id**: タスクID
    """
    task = tasks.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"タスクが完了していません（status: {task['status']}）"
        )

    if not task.get("result"):
        raise HTTPException(status_code=500, detail="結果ファイルが見つかりません")

    # ファイル名生成
    timestamp = task["created_at"].strftime("%Y%m%d_%H%M%S")
    filename = f"duty_schedule_{timestamp}.xlsx"

    return StreamingResponse(
        io.BytesIO(task["result"]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@app.delete("/api/schedule/{task_id}")
async def delete_task(task_id: str):
    """
    タスクを削除

    - **task_id**: タスクID
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    del tasks[task_id]
    return {"message": "タスクを削除しました", "task_id": task_id}


@app.get("/api/tasks")
async def list_tasks():
    """全タスクの一覧を取得（管理用）"""
    return {
        "tasks": [
            {
                "task_id": t["task_id"],
                "status": t["status"],
                "progress": t["progress"],
                "created_at": t["created_at"],
            }
            for t in tasks.values()
        ]
    }


# ===== 起動 =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
