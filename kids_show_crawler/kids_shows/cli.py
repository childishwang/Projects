"""命令列入口：python -m kids_shows [選項]"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

from . import age, report
from .fetch import Fetcher
from .models import Show
from .sources import SOURCES

log = logging.getLogger("kids_shows")


def select(shows: list[Show], *, tmin: int, tmax: int, days: int, cities: list[str],
           include_unknown: bool) -> list[Show]:
    now = datetime.now()
    until = now + timedelta(days=days)
    norm_cities = [c.replace("台", "臺") for c in cities]
    picked: dict[str, Show] = {}
    for s in shows:
        age.classify(s, tmin, tmax)
        if not s.suitable:
            continue
        if not include_unknown and s.age_min is None and s.age_max is None:
            continue
        if s.start and s.start > until:
            continue
        if norm_cities and not any(c in (s.city + s.venue).replace("台", "臺") for c in norm_cities):
            continue
        k = s.key()
        if k not in picked or s.score > picked[k].score:
            picked[k] = s
    return sorted(picked.values(), key=lambda s: (s.start or datetime.max, -s.score))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="kids_shows", description="爬取各大售票/藝文網站，找出適合 3-10 歲兒童的演出")
    p.add_argument("--sources", default=",".join(SOURCES), help=f"資料來源，逗號分隔（可用：{','.join(SOURCES)}）")
    p.add_argument("--min-age", type=int, default=age.TARGET_MIN)
    p.add_argument("--max-age", type=int, default=age.TARGET_MAX)
    p.add_argument("--days", type=int, default=90, help="只列出未來幾天內的演出（預設 90）")
    p.add_argument("--city", action="append", default=[], help="篩選縣市，可重複，例如 --city 台北 --city 新北")
    p.add_argument("--strict", action="store_true", help="只保留有明確標示年齡的節目")
    p.add_argument("--details", action="store_true", help="KKTIX 逐一進活動頁抓詳細說明（較慢，但年齡判斷更準）")
    p.add_argument("--delay", type=float, default=1.0, help="每次請求間隔秒數（預設 1，請勿調太低）")
    p.add_argument("-o", "--out", default="output", help="輸出資料夾")
    p.add_argument("-v", "--verbose", action="store_true")
    a = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    fetcher = Fetcher(delay=a.delay)
    raw: list[Show] = []
    for name in [x.strip() for x in a.sources.split(",") if x.strip()]:
        mod = SOURCES.get(name)
        if not mod:
            p.error(f"未知來源：{name}")
        raw.extend(mod.fetch(fetcher, details=a.details))

    shows = select(raw, tmin=a.min_age, tmax=a.max_age, days=a.days, cities=a.city,
                   include_unknown=not a.strict)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    report.write_csv(shows, out / "kids_shows.csv")
    report.write_json(shows, out / "kids_shows.json")
    report.write_html(shows, out / "kids_shows.html", a.min_age, a.max_age)

    log.info("共抓到 %d 筆，符合 %d-%d 歲的有 %d 場", len(raw), a.min_age, a.max_age, len(shows))
    for s in shows[:15]:
        when = s.start.strftime("%m/%d %H:%M") if s.start else "  --  "
        where = s.venue if s.city and s.city in s.venue else f"{s.city}{s.venue}"
        print(f"  {when}  [{s.tags[0] if s.tags else ''}] {s.title}  @ {where}")
    if len(shows) > 15:
        print(f"  …還有 {len(shows) - 15} 場，詳見 {out / 'kids_shows.html'}")
    print(f"\n輸出：{out / 'kids_shows.html'}、kids_shows.csv、kids_shows.json")
    return 0
