"""用假資料測試解析與篩選（不連網）。格式仿照各來源實際回傳。"""
from datetime import datetime, timedelta

from kids_shows.cli import select
from kids_shows.sources import culture_gov, kktix

FUTURE = datetime.now() + timedelta(days=10)
F = FUTURE.strftime("%Y/%m/%d")

CULTURE = [
    {"UID": "1", "title": "《小狐狸的森林冒險》兒童劇", "category": "4",
     "showInfo": [{"time": f"{F} 14:30:00", "location": "臺北市中正區中山南路21-1號",
                   "locationName": "國家戲劇院", "price": "500,800", "endTime": f"{F} 16:00:00"},
                  {"time": "2020/01/01 14:30:00", "location": "臺北市", "locationName": "舊場",
                   "price": "", "endTime": "2020/01/01 16:00:00"}],
     "descriptionFilterHtml": "適合年齡：4-10歲。互動式親子劇場", "masterUnit": ["某某劇團"],
     "showUnit": "", "webSales": "https://example.com/1", "imageUrl": "", "startDate": F, "endDate": F},
    {"UID": "2", "title": "馬勒第五號", "category": "1",
     "showInfo": [{"time": f"{F} 19:30:00", "location": "高雄市", "locationName": "衛武營",
                   "price": "", "endTime": ""}],
     "descriptionFilterHtml": "建議12歲以上觀賞", "masterUnit": [], "showUnit": "",
     "webSales": "", "startDate": F, "endDate": F},
]

ATOM = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>KKTIX</title>
<entry><title>魔法泡泡親子秀</title>
<link rel="alternate" type="text/html" href="https://demo.kktix.cc/events/bubble"/>
<content type="html">&lt;p&gt;時間：{F}(六) 10:30(+0800)&lt;/p&gt;&lt;p&gt;地點：新北市板橋區 府中15&lt;/p&gt;&lt;p&gt;建議3歲以上觀賞&lt;/p&gt;</content>
<author><name>泡泡工作室</name></author></entry>
<entry><title>成人微醺爵士夜</title>
<link rel="alternate" href="https://demo.kktix.cc/events/jazz"/>
<content type="html">時間：{F} 21:00 未滿18歲禁止入場</content></entry>
</feed>"""


def test_culture_parse_skips_past_sessions():
    shows = culture_gov.parse(CULTURE, "親子")
    assert [s.venue for s in shows] == ["國家戲劇院", "衛武營"]
    assert shows[0].city == "臺北市" and shows[0].organizer == "某某劇團"


def test_kktix_feed():
    shows = kktix.parse_feed(ATOM)
    assert shows[0].title == "魔法泡泡親子秀"
    assert shows[0].url.endswith("/bubble")
    assert shows[0].start.hour == 10 and shows[0].city == "新北市"


def test_kktix_detail():
    d = kktix.parse_detail('<html><head><meta property="og:image" content="x.jpg"></head>'
                           '<body><div class="description">適合 3-8 歲</div></body></html>')
    assert d["description"] == "適合 3-8 歲" and d["image"] == "x.jpg"


def test_select_end_to_end():
    shows = culture_gov.parse(CULTURE, "親子") + kktix.parse_feed(ATOM)
    got = select(shows, tmin=3, tmax=10, days=30, cities=[], include_unknown=True)
    assert {s.title for s in got} == {"《小狐狸的森林冒險》兒童劇", "魔法泡泡親子秀"}
    only_taipei = select(shows, tmin=3, tmax=10, days=30, cities=["台北"], include_unknown=True)
    assert [s.title for s in only_taipei] == ["《小狐狸的森林冒險》兒童劇"]
