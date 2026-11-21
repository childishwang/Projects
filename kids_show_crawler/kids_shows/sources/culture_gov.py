"""文化部「藝文活動」開放資料 (cloud.culture.tw)。

這是政府公開的 JSON API，彙整了全台各場館、兩廳院、縣市文化局等的演出，
是最穩定、最完整的來源。分類代碼：
  1 音樂、2 戲劇、3 舞蹈、4 親子、5 獨立音樂、6 展覽、7 講座、8 電影、
  11 綜藝、13 競賽、14 徵選、15 其他、17 演唱會、19 研習課程
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Optional

from ..fetch import Fetcher
from ..models import Show

log = logging.getLogger(__name__)

NAME = "culture"
LABEL = "文化部藝文活動"
API = "https://cloud.culture.tw/frontsite/trans/SearchShowAction.do?method=doFindTypeJ&category={cat}"
CATEGORIES = {"4": "親子", "2": "戲劇", "3": "舞蹈", "1": "音樂", "11": "綜藝"}
CITIES = ("臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", "基隆市", "新竹市",
          "嘉義市", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣", "屏東縣",
          "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣")


def _dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            pass
    return None


def city_of(location: str) -> str:
    loc = location.replace("台", "臺")
    for c in CITIES:
        if loc.startswith(c) or c in loc[:8]:
            return c
    return ""


def parse(items: list[dict], category_label: str = "", now: Optional[datetime] = None) -> list[Show]:
    """把 API 回傳的 JSON 轉成 Show。每個場次（showInfo）各一筆。"""
    now = now or datetime.now()
    shows: list[Show] = []
    for it in items:
        title = (it.get("title") or "").strip()
        if not title:
            continue
        desc = " ".join(filter(None, [it.get("descriptionFilterHtml"), it.get("comment"),
                                       it.get("discountInfo")]))
        url = it.get("webSales") or it.get("sourceWebPromote") or ""
        units = list(it.get("masterUnit") or []) + [it.get("showUnit") or ""]
        organizer = "、".join(u.strip() for u in units if u and u.strip())
        infos = it.get("showInfo") or [{}]
        for si in infos:
            start = _dt(si.get("time", "")) or _dt(it.get("startDate", ""))
            end = _dt(si.get("endTime", "")) or _dt(it.get("endDate", ""))
            if (end or start) and (end or start) < now:
                continue  # 已結束
            loc = si.get("location", "") or ""
            shows.append(Show(
                source=LABEL, title=title, url=url, start=start, end=end,
                venue=(si.get("locationName") or "").strip(), city=city_of(loc),
                price=(si.get("price") or "").strip(), organizer=organizer,
                description=re.sub(r"\s+", " ", desc).strip(),
                image=it.get("imageUrl") or "", category=category_label,
            ))
    return shows


def fetch(fetcher: Fetcher, categories: Optional[list[str]] = None, **_) -> list[Show]:
    out: list[Show] = []
    for cat in categories or list(CATEGORIES):
        url = API.format(cat=cat)
        try:
            data = fetcher.get(url).json()
        except Exception as e:  # noqa: BLE001
            log.error("文化部分類 %s 抓取失敗：%s", cat, e)
            continue
        got = parse(data, CATEGORIES.get(cat, cat))
        log.info("文化部 分類%s(%s)：%d 場次", cat, CATEGORIES.get(cat, ""), len(got))
        out.extend(got)
    return out
