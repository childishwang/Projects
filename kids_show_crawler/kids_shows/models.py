"""共用資料結構。"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Show:
    source: str                     # 資料來源，例如 "文化部" / "KKTIX"
    title: str
    url: str = ""
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    venue: str = ""
    city: str = ""
    price: str = ""
    organizer: str = ""
    description: str = ""
    image: str = ""
    category: str = ""
    # 以下欄位由 age.classify() 填入
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    age_note: str = ""              # 判斷依據（原文片段）
    suitable: Optional[bool] = None
    score: int = 0                  # 越高越像 3-10 歲兒童節目
    tags: list[str] = field(default_factory=list)

    def key(self) -> str:
        """用來去除重複：標題 + 開始日期。"""
        day = self.start.date().isoformat() if self.start else ""
        norm = "".join(self.title.split()).lower()
        return f"{norm}|{day}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["start"] = self.start.isoformat(timespec="minutes") if self.start else ""
        d["end"] = self.end.isoformat(timespec="minutes") if self.end else ""
        d["tags"] = ",".join(self.tags)
        return d
