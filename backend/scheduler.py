"""
当直スケジューラー - コアロジック
Google Colab依存を削除し、Web化に対応
"""

import io
import pandas as pd
import numpy as np
from collections import defaultdict
import random
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field


@dataclass
class SchedulerConfig:
    """スケジューラー設定"""
    holidays: Set[pd.Timestamp] = field(default_factory=set)
    bg_day_cols: Set[str] = field(default_factory=set)
    bg_night_cols: Set[str] = field(default_factory=set)
    wed_forbidden_doctors: Set[str] = field(default_factory=set)
    num_patterns: int = 1000
    local_search_enabled: bool = True
    top_keep: int = 15
    refine_top: int = 15
    local_max_iters: int = 3000
    local_patience: int = 1200
    local_refresh_every: int = 200

    # スコア重み（v6.0.0以降: GAP/CAP/外病院重複はABS制約に格上げされペナルティ重み0）
    w_fair_total: float = 30
    w_gap: float = 0             # ABS-007で対応
    w_hosp_dup: float = 0        # ABS-008で対応
    w_unassigned: float = 500    # v6.0.2: fix_unassigned_slots有効化に伴い復活
    w_cap: float = 0             # ABS-010で対応
    w_bg_spread: float = 0       # 削除（簡略化）
    w_ht_spread: float = 0       # 削除（簡略化）
    w_wd_spread: float = 0       # 削除（簡略化）
    w_we_spread: float = 0       # 削除（簡略化）

    # 枠マーカー
    slot_markers: Set = field(default_factory=lambda: {1, 1.0, "1", "〇", "○", "◯", "◎"})

    # 列インデックス（動的に設定）
    b_col_index: int = 1
    c_col_index: int = 2
    d_col_index: int = 3
    e_col_index: int = 4
    f_col_index: int = 5
    g_col_index: int = 6
    h_col_index: int = 7
    m_col_index: int = 12
    u_col_index: int = 20

    def normalize_holidays(self):
        """祝日を正規化"""
        self.holidays = {pd.to_datetime(d).normalize().tz_localize(None) for d in self.holidays}


class DutyScheduler:
    """当直スケジューラー本体"""

    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self.config.normalize_holidays()

        # データ
        self.shift_df: Optional[pd.DataFrame] = None
        self.availability_df: Optional[pd.DataFrame] = None
        self.schedule_df: Optional[pd.DataFrame] = None
        self.sheet4_data: Optional[pd.DataFrame] = None

        # メタデータ
        self.doctor_names: List[str] = []
        self.hospital_cols: List[str] = []
        self.active_doctors: List[str] = []
        self.inactive_doctors: List[str] = []
        self.target_cap: Dict[str, int] = {}

        # キャッシュ
        self.fallback_avail_codes: Dict[str, int] = {}
        self.name_match: Dict[str, Optional[str]] = {}
        self.prev_total: Dict[str, float] = {}
        self.prev_bg: Dict[str, float] = {}
        self.prev_ht: Dict[str, float] = {}
        self.prev_weekday: Dict[str, float] = {}
        self.prev_weekend: Dict[str, float] = {}

    # =========== ユーティリティ ===========

    @staticmethod
    def strip_cols(df: pd.DataFrame) -> pd.DataFrame:
        """列名の空白を除去"""
        df = df.copy()
        df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
        return df

    @staticmethod
    def make_unique(names: List) -> List[str]:
        """重複列名をユニーク化"""
        seen = {}
        out = []
        for n in names:
            n = "" if pd.isna(n) else str(n)
            if n not in seen:
                seen[n] = 1
                out.append(n)
            else:
                seen[n] += 1
                out.append(f"{n}_{seen[n]}")
        return out

    @staticmethod
    def safe_str(x) -> str:
        """安全な文字列変換"""
        if pd.isna(x):
            return ""
        return str(x).strip()

    def is_slot_value(self, v) -> bool:
        """枠マーカーかどうか"""
        if isinstance(v, str):
            return v.strip() in self.config.slot_markers
        if isinstance(v, (int, float, np.integer, np.floating)):
            return float(v) == 1.0
        return False

    def is_holiday(self, date: pd.Timestamp) -> bool:
        """祝日判定"""
        return pd.to_datetime(date).normalize().tz_localize(None) in self.config.holidays

    # =========== データ読み込み ===========

    def load_excel(self, file_content: bytes) -> Dict[str, Any]:
        """
        Excelファイルを読み込み、各シートをパース

        Args:
            file_content: Excelファイルのバイナリ

        Returns:
            読み込み結果の辞書
        """
        try:
            xls = pd.ExcelFile(io.BytesIO(file_content))
        except Exception as e:
            raise ValueError(f"Excelファイルの読み込みに失敗しました: {e}")

        # シート名検索
        sheet1_name = self._find_sheet_name(xls, "sheet1")
        sheet2_name = self._find_sheet_name(xls, "sheet2")
        sheet3_name = self._find_sheet_name(xls, "sheet3")
        sheet4_name = self._find_sheet_name(xls, "sheet4") or self._find_sheet_name(xls, "Sheet4")

        missing = []
        if not sheet1_name:
            missing.append("sheet1")
        if not sheet2_name:
            missing.append("sheet2")
        if not sheet3_name:
            missing.append("sheet3")
        if not sheet4_name:
            missing.append("sheet4")

        if missing:
            raise ValueError(
                f"必要なシートが見つかりません: {missing}\n"
                f"実際のシート名: {xls.sheet_names}"
            )

        # シート読み込み
        self.shift_df = self._load_shift_sheet(xls, sheet1_name)
        self.availability_df = self._load_availability_sheet(xls, sheet2_name)
        self.schedule_df = self._load_schedule_sheet(xls, sheet3_name)
        self.sheet4_data = self._load_sheet4(xls, sheet4_name)

        # メタデータ抽出
        self._extract_metadata()

        return {
            "shift_df": self.shift_df,
            "availability_df": self.availability_df,
            "schedule_df": self.schedule_df,
            "sheet4_data": self.sheet4_data,
            "doctor_names": self.doctor_names,
            "hospital_cols": self.hospital_cols,
        }

    def _find_sheet_name(self, xls: pd.ExcelFile, target: str) -> Optional[str]:
        """シート名の大小文字を許容して検索"""
        if target in xls.sheet_names:
            return target
        low_map = {s.lower(): s for s in xls.sheet_names}
        if target.lower() in low_map:
            return low_map[target.lower()]
        for s in xls.sheet_names:
            if s.strip().lower() == target.strip().lower():
                return s
        return None

    def _load_shift_sheet(self, xls: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
        """sheet1（シフト）読み込み"""
        df = self.strip_cols(pd.read_excel(xls, sheet_name=sheet_name))
        df.columns = self.make_unique(list(df.columns))

        # 日付列の正規化（修正: タイムゾーン対応）
        date_col = df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.normalize().dt.tz_localize(None)

        if df[date_col].isna().all():
            raise ValueError("sheet1 の先頭列が日付として解釈できません")

        return df

    def _load_availability_sheet(self, xls: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
        """sheet2（可否）読み込み"""
        df = self.strip_cols(pd.read_excel(xls, sheet_name=sheet_name))
        df.columns = self.make_unique(list(df.columns))

        date_col = df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.normalize().dt.tz_localize(None)

        return df.set_index(date_col)

    def _load_schedule_sheet(self, xls: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
        """sheet3（カテ表）読み込み"""
        df = self.strip_cols(pd.read_excel(xls, sheet_name=sheet_name))
        df.columns = self.make_unique(list(df.columns))

        date_col = df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.normalize().dt.tz_localize(None)

        return df.set_index(date_col)

    def _load_sheet4(self, xls: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
        """sheet4（前月累積）読み込み - ヘッダ行自動検出"""
        grid = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        grid = grid.dropna(how="all").reset_index(drop=True)

        if len(grid) == 0:
            raise ValueError("sheet4 が空です")

        # ヘッダ行検索（修正: 範囲拡大）
        header_row_idx = None
        search_limit = min(50, len(grid))  # 30→50に拡大
        for i in range(search_limit):
            row = grid.iloc[i].astype(str).str.strip()
            if (row == "氏名").any():
                header_row_idx = i
                break

        if header_row_idx is None:
            raise ValueError(
                f"sheet4 のヘッダ行に '氏名' 列が見つかりません（先頭{search_limit}行を検索）"
            )

        headers = [self.safe_str(x) for x in grid.iloc[header_row_idx].tolist()]
        headers = [h if (h != "" and h.lower() != "nan") else f"Unnamed_{j}" for j, h in enumerate(headers)]
        headers = self.make_unique(headers)

        data = grid.iloc[header_row_idx + 1:].reset_index(drop=True)
        data.columns = headers

        if "氏名" not in data.columns:
            raise ValueError("sheet4 のヘッダ行に '氏名' 列が見つかりません")

        # 空行削除
        data["氏名"] = data["氏名"].astype(str).str.strip()
        data = data[
            (data["氏名"].notna()) &
            (data["氏名"] != "") &
            (data["氏名"].str.lower() != "nan")
        ].reset_index(drop=True)

        # 数値化
        for col in data.columns:
            if col == "氏名":
                continue
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)

        return data

    def _extract_metadata(self):
        """メタデータを抽出"""
        # 医師名
        self.doctor_names = [
            self.safe_str(x)
            for x in list(self.availability_df.columns)
        ]

        # 医師名の正規化（修正: 空白除去）
        self.doctor_names = [name.replace(" ", "").replace("　", "") for name in self.doctor_names]
        self.config.wed_forbidden_doctors = {
            name.replace(" ", "").replace("　", "")
            for name in self.config.wed_forbidden_doctors
        }

        # 病院列
        self.hospital_cols = list(self.shift_df.columns[1:])

        # 列インデックスの動的設定（修正: 安全な取得）
        n_cols = len(self.shift_df.columns)
        self.config.b_col_index = 1
        self.config.c_col_index = min(2, n_cols - 1)
        self.config.d_col_index = min(3, n_cols - 1)
        self.config.e_col_index = min(4, n_cols - 1)
        self.config.f_col_index = min(5, n_cols - 1)
        self.config.g_col_index = min(6, n_cols - 1)
        self.config.h_col_index = min(7, n_cols - 1)
        self.config.m_col_index = min(12, n_cols - 1)
        self.config.u_col_index = min(20, n_cols - 1)

        # 可否コードのフォールバック値
        self._build_fallback_avail_codes()

        # sheet4とのマッチング
        self._build_name_matching()

        # 前月累積の取得
        self._extract_prev_month_stats()

    def _build_fallback_avail_codes(self):
        """可否コードのデフォルト値を設定"""
        self.fallback_avail_codes = {}
        for doc in self.doctor_names:
            col_vals = self.availability_df[doc]
            first_val = None
            for v in col_vals:
                if pd.notna(v):
                    first_val = v
                    break

            if first_val is None:
                code = 1
            else:
                try:
                    code = int(first_val)
                except Exception:
                    code = 1
                if code not in (0, 1, 2, 3):
                    code = 1

            self.fallback_avail_codes[doc] = code

    def _build_name_matching(self):
        """sheet4との医師名マッチング"""
        prev_names = list(self.sheet4_data["氏名"])
        name_to_row = {row["氏名"]: row for _, row in self.sheet4_data.iterrows()}

        def match_prev_name(doc: str) -> Optional[str]:
            if doc in name_to_row:
                return doc
            # 部分一致検索
            matches = [p for p in prev_names if str(p).startswith(doc) or doc.startswith(str(p))]
            return matches[0] if len(matches) == 1 else None

        self.name_match = {doc: match_prev_name(doc) for doc in self.doctor_names}

        # 未マッチの警告
        unmatched = [d for d in self.doctor_names if self.name_match.get(d) is None]
        if unmatched:
            print(f"WARNING: sheet4で名前が一致しない医師（累積=0扱い）: {unmatched}")

    def _extract_prev_month_stats(self):
        """前月累積データを抽出"""
        name_to_row = {row["氏名"]: row for _, row in self.sheet4_data.iterrows()}

        def prev_get(doc: str, colname: str) -> float:
            pname = self.name_match.get(doc)
            if pname and pname in name_to_row:
                row = name_to_row[pname]
                v = row.get(colname, 0)
                try:
                    return float(v or 0)
                except Exception:
                    return 0.0
            return 0.0

        self.prev_total = {d: prev_get(d, "全合計") for d in self.doctor_names}
        self.prev_bg = {d: prev_get(d, "大学合計") for d in self.doctor_names}
        self.prev_ht = {d: prev_get(d, "外病院合計") for d in self.doctor_names}
        self.prev_weekday = {d: prev_get(d, "平日") for d in self.doctor_names}
        self.prev_weekend = {d: prev_get(d, "休日合計") for d in self.doctor_names}

    # =========== （以下、既存のロジックをメソッド化） ===========
    # ※ 長さの関係で主要部分のみ記載

    def generate_schedules(self) -> List[Dict[str, Any]]:
        """
        スケジュールパターンを生成

        Returns:
            TOP3パターンのリスト
        """
        # TODO: 既存の build_schedule_pattern, local_search, evaluate などを実装
        pass

    def export_excel(self, patterns: List[Dict]) -> bytes:
        """
        結果をExcelファイルとして出力

        Args:
            patterns: スケジュールパターンのリスト

        Returns:
            Excelファイルのバイナリ
        """
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 元シート
            self.shift_df.to_excel(writer, sheet_name="sheet1", index=False)
            # TODO: 他のシートも出力

            # パターン出力
            for rank, pattern in enumerate(patterns[:3], start=1):
                sheet_label = f"pattern_{rank:02d}"
                pattern["df"].to_excel(writer, sheet_name=sheet_label, index=False)

        output.seek(0)
        return output.getvalue()
