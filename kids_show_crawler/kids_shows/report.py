"""輸出成 CSV / JSON / HTML。"""
from __future__ import annotations

import csv
import html
import json
from datetime import datetime
from pathlib import Path

from .models import Show

COLUMNS = ["start", "title", "tags", "age_note", "city", "venue", "price", "source", "url",
           "organizer", "end", "age_min", "age_max", "score"]
HEADERS = {"start": "開始時間", "title": "節目", "tags": "標籤", "age_note": "年齡依據",
           "city": "縣市", "venue": "場地", "price": "票價", "source": "來源", "url": "連結",
           "organizer": "主辦/演出", "end": "結束時間", "age_min": "最小年齡",
           "age_max": "最大年齡", "score": "分數"}


def write_csv(shows: list[Show], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig 讓 Excel 正常顯示中文
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writerow(HEADERS)
        for s in shows:
            w.writerow(s.to_dict())


def write_json(shows: list[Show], path: Path) -> None:
    path.write_text(json.dumps([s.to_dict() for s in shows], ensure_ascii=False, indent=2),
                    encoding="utf-8")


def write_html(shows: list[Show], path: Path, tmin: int, tmax: int) -> None:
    e = html.escape
    rows = []
    for s in shows:
        when = s.start.strftime("%Y/%m/%d (%a) %H:%M").replace(" 00:00", "") if s.start else "—"
        tags = "".join(f"<span class=tag>{e(t)}</span>" for t in s.tags[:5])
        link = f'<a href="{e(s.url)}" target=_blank rel=noopener>{e(s.title)}</a>' if s.url else e(s.title)
        rows.append(
            f"<tr data-city='{e(s.city)}'><td class=when>{e(when)}</td><td>{link}<div class=tags>{tags}</div>"
            f"<div class=note>{e(s.age_note)}</div></td><td>{e(s.city)}<br><small>{e(s.venue)}</small></td>"
            f"<td><small>{e(s.price[:60])}</small></td><td><small>{e(s.source)}</small></td></tr>")
    cities = sorted({s.city for s in shows if s.city})
    opts = "".join(f"<option>{e(c)}</option>" for c in cities)
    path.write_text(f"""<!doctype html><html lang=zh-Hant><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>{tmin}-{tmax} 歲兒童演出</title>
<style>
:root{{--bg:#fffdf8;--fg:#222;--mut:#777;--line:#eee;--tag:#ffe8b3}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1b1b1d;--fg:#eee;--mut:#999;--line:#333;--tag:#5a4615}}}}
body{{font-family:system-ui,"PingFang TC","Microsoft JhengHei",sans-serif;background:var(--bg);color:var(--fg);margin:0;padding:16px}}
h1{{font-size:1.4rem}} table{{border-collapse:collapse;width:100%}}
td,th{{border-bottom:1px solid var(--line);padding:8px;vertical-align:top;text-align:left}}
.when{{white-space:nowrap}} .tag{{background:var(--tag);border-radius:8px;padding:1px 6px;margin-right:4px;font-size:.75rem}}
.note,small{{color:var(--mut);font-size:.8rem}} a{{color:inherit}}
input,select{{padding:6px;margin:0 8px 12px 0;font-size:1rem}}
@media (max-width:640px){{td:nth-child(4),td:nth-child(5),th:nth-child(4),th:nth-child(5){{display:none}}}}
</style>
<h1>適合 {tmin}-{tmax} 歲的演出（共 {len(shows)} 場）</h1>
<p><small>更新時間 {datetime.now():%Y/%m/%d %H:%M}・年齡為自動判斷，購票前請再確認主辦單位說明</small></p>
<input id=q placeholder="搜尋節目/場地"><select id=c><option value="">全部縣市</option>{opts}</select>
<table><thead><tr><th>時間</th><th>節目</th><th>地點</th><th>票價</th><th>來源</th></tr></thead>
<tbody id=t>{''.join(rows)}</tbody></table>
<script>
const q=document.getElementById('q'),c=document.getElementById('c');
function f(){{const k=q.value.trim().toLowerCase(),cv=c.value;
for(const r of document.querySelectorAll('#t tr')){{
r.style.display=(!k||r.textContent.toLowerCase().includes(k))&&(!cv||r.dataset.city===cv)?'':'none'}}}}
q.oninput=f;c.onchange=f;
</script></html>""", encoding="utf-8")
