"""KKTIX 活動搜尋 (Atom feed)。

KKTIX 提供公開的 Atom feed：https://kktix.com/events.atom?search=關鍵字
feed 的摘要通常不含完整介紹，用 --details 會再進每個活動頁抓「適合年齡」等說明。
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from urllib.parse import quote

from bs4 import BeautifulSoup

from ..fetch import Fetcher
from ..models import Show
from .culture_gov import city_of

log = logging.getLogger(__name__)

NAME = "kktix"
LABEL = "KKTIX"
FEED = "https://kktix.com/events.atom?locale=zh-TW&search={q}"
KEYWORDS = ("親子", "兒童劇", "兒童", "小朋友", "偶戲", "繪本")
NS = {"a": "http://www.w3.org/2005/Atom"}

_DATE = re.compile(r"(20\d{2})[/\-.](\d{1,2})[/\-.](\d{1,2})(?:\D{0,6}?(\d{1,2}):(\d{2}))?")
_LOC = re.compile(r"(?:地點|場地|地址)\s*[:：]\s*([^\n]+)")


def _text(html: str) -> str:
    return BeautifulSoup(html or "", "html.parser").get_text("\n", strip=True)


def _first_date(text: str) -> Optional[datetime]:
    m = _DATE.search(text)
    if not m:
        return None
    y, mo, d, h, mi = m.groups()
    try:
        return datetime(int(y), int(mo), int(d), int(h or 0), int(mi or 0))
    except ValueError:
        return None


def parse_feed(xml: str | bytes) -> list[Show]:
    root = ET.fromstring(xml)
    shows: list[Show] = []
    for e in root.findall("a:entry", NS):
        title = (e.findtext("a:title", "", NS) or "").strip()
        link_el = e.find("a:link[@rel='alternate']", NS)
        if link_el is None:  # Element 沒有子節點時為 falsy，不能用 or
            link_el = e.find("a:link", NS)
        url = link_el.get("href", "") if link_el is not None else ""
        body = _text(e.findtext("a:content", "", NS) or e.findtext("a:summary", "", NS))
        loc_m = _LOC.search(body)
        venue = loc_m.group(1).strip() if loc_m else ""
        author = e.findtext("a:author/a:name", "", NS) or ""
        shows.append(Show(
            source=LABEL, title=title, url=url, start=_first_date(body),
            venue=venue, city=city_of(venue), organizer=author.strip(),
            description=body, category="",
        ))
    return shows


def parse_detail(html: str) -> dict:
    """活動頁：抓介紹文字、時間、地點。"""
    soup = BeautifulSoup(html, "html.parser")
    desc_el = soup.select_one(".description") or soup.select_one("#event-description") or soup.body
    info = " ".join(x.get_text(" ", strip=True) for x in soup.select(".event-info li, .info-desc"))
    og_img = soup.find("meta", property="og:image")
    return {
        "description": desc_el.get_text("\n", strip=True) if desc_el else "",
        "info": info,
        "image": og_img.get("content", "") if og_img else "",
    }


def fetch(fetcher: Fetcher, keywords: Optional[list[str]] = None, details: bool = False, **_) -> list[Show]:
    seen: dict[str, Show] = {}
    for kw in keywords or KEYWORDS:
        try:
            r = fetcher.get(FEED.format(q=quote(kw)))
            got = parse_feed(r.content)
        except Exception as e:  # noqa: BLE001
            log.error("KKTIX 搜尋「%s」失敗：%s", kw, e)
            continue
        log.info("KKTIX 搜尋「%s」：%d 筆", kw, len(got))
        for s in got:
            seen.setdefault(s.url or s.title, s)

    shows = list(seen.values())
    if details:
        for s in shows:
            if not s.url:
                continue
            try:
                d = parse_detail(fetcher.get(s.url).text)
            except Exception as e:  # noqa: BLE001
                log.warning("KKTIX 活動頁失敗 %s: %s", s.url, e)
                continue
            s.description = f"{s.description}\n{d['info']}\n{d['description']}"
            s.image = s.image or d["image"]
            if not s.start:
                s.start = _first_date(d["info"] + d["description"])
            if not s.venue:
                m = _LOC.search(d["info"] + "\n" + d["description"])
                if m:
                    s.venue = m.group(1).strip()
                    s.city = city_of(s.venue)
    return shows
