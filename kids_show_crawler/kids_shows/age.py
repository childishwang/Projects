"""從節目文字判斷適合年齡，並決定是否適合 3-10 歲兒童。

台灣售票網站常見寫法：
  - 建議 4 歲以上觀賞 / 適合 3 歲(含)以上
  - 適合年齡：3-12 歲 / 3～8歲 / 3 至 10 歲
  - 未滿 7 歲請勿入場 / 未滿六歲謝絕入場
  - 0-3 歲寶寶 / 學齡前 / 國小低年級
注意：「2 歲以上需購票」「3 歲以下免費」是票務規定，不是觀賞年齡，要排除。
"""
from __future__ import annotations

import re
from typing import Optional

from .models import Show

TARGET_MIN = 3
TARGET_MAX = 10

_CN_NUM = {"零": 0, "〇": 0, "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5,
           "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12,
           "十三": 13, "十四": 14, "十五": 15, "十六": 16, "十八": 18}
_NUM = r"(\d{1,2}|十[一二三四五六八]?|[零〇一二兩三四五六七八九])"
_DASH = r"\s*(?:-|－|–|—|~|～|〜|至|到)\s*"
_SUI = r"\s*(?:足?歲|y/?o)"
_YISHANG = r"\s*(?:\(含\)|（含）|含)?\s*以上"
_YIXIA = r"\s*(?:\(含\)|（含）|含)?\s*以下"
# 票務相關字眼：出現在年齡描述後面時，代表是「購票規定」而非「觀賞年齡」
_TICKET = r"(?:[^。；;\n]{0,8})(?:購票|購買|持票|一人一票|憑票|票價|免費|免票|免購票|半價|優待|需票|需購|入場須|兒童票|敬老|長者|學生票|愛心)"

_RE_RANGE = re.compile(_NUM + r"\s*(?:歲)?" + _DASH + _NUM + _SUI)
_RE_ABOVE = re.compile(_NUM + _SUI + _YISHANG)
_RE_BELOW = re.compile(_NUM + _SUI + _YIXIA)
_RE_UNDER_BAN = re.compile(r"未滿\s*" + _NUM + _SUI + r"[^。；;\n]{0,12}?(?:不得|謝絕|請勿|勿|無法|不宜|禁止|不建議|恕不)")
_RE_ADULT = re.compile(r"(?:限制級|輔\s*1[25]|輔導級|18\s*歲以上|十八歲以上|未滿\s*18|未滿十八)")
_RE_HEIGHT = re.compile(r"身高\s*(?:未滿)?\s*\d{2,3}\s*(?:cm|公分)", re.I)

KID_KEYWORDS = {
    "親子": 3, "兒童": 3, "孩童": 2, "小朋友": 3, "孩子": 2, "幼兒": 2, "童話": 2,
    "繪本": 3, "偶戲": 2, "布袋戲": 1, "人偶": 2, "兒童劇": 4, "親子劇": 4,
    "闔家": 2, "全家": 2, "家庭": 1, "寶貝": 1, "小學": 1, "國小": 1, "幼稚園": 2,
    "幼兒園": 2, "學齡": 2, "魔術": 1, "動畫": 1, "互動": 1, "說故事": 2,
    "故事": 1, "卡通": 1, "kids": 2, "family": 2, "children": 2,
}
BABY_ONLY = ("0-3歲", "0~3歲", "0至3歲", "0-2歲", "嬰幼兒", "寶寶劇場", "baby")
NEGATIVE_KEYWORDS = ("講座", "研習", "徵選", "工作坊招生", "成人", "微醺", "酒吧", "脫口秀", "驚悚", "恐怖")


def _n(tok: str) -> int:
    tok = tok.strip()
    return int(tok) if tok.isdigit() else _CN_NUM[tok]


def _snippet(text: str, m: re.Match, pad: int = 10) -> str:
    s, e = max(0, m.start() - pad), min(len(text), m.end() + pad)
    return text[s:e].replace("\n", " ").strip()


def _is_ticket_rule(text: str, m: re.Match) -> bool:
    return re.match(_TICKET, text[m.end():m.end() + 20]) is not None


def parse_age(text: str) -> tuple[Optional[int], Optional[int], str]:
    """回傳 (最小年齡, 最大年齡, 依據原文)。找不到就回傳 None。"""
    if not text:
        return None, None, ""
    text = _RE_HEIGHT.sub("", text)
    lo: Optional[int] = None
    hi: Optional[int] = None
    notes: list[str] = []

    for m in _RE_RANGE.finditer(text):
        a, b = _n(m.group(1)), _n(m.group(2))
        if a > b or b > 99 or _is_ticket_rule(text, m):
            continue
        lo = a if lo is None else min(lo, a)
        hi = b if hi is None else max(hi, b)
        notes.append(_snippet(text, m))

    # 「N 歲以上」「未滿 N 歲謝絕入場」是硬性下限：取最嚴格的那個
    hard_lows: list[int] = []
    for m in _RE_UNDER_BAN.finditer(text):
        hard_lows.append(_n(m.group(1)))
        notes.append(_snippet(text, m))
    for m in _RE_ABOVE.finditer(text):
        a = _n(m.group(1))
        # 「65 歲以上敬老票」這類大於 18 的通常是優待票，不是觀賞年齡
        if a > 18 or _is_ticket_rule(text, m):
            continue
        hard_lows.append(a)
        notes.append(_snippet(text, m))
    if hard_lows:
        lo = max(hard_lows) if lo is None else max(lo, max(hard_lows))

    for m in _RE_BELOW.finditer(text):
        if _is_ticket_rule(text, m):
            continue
        b = _n(m.group(1))
        hi = b if hi is None else max(hi, b)
        notes.append(_snippet(text, m))

    if lo is not None and hi is not None and lo > hi:
        hi = None  # 互相矛盾時，以最低年齡限制為準
    # 去重保留順序
    seen, uniq = set(), []
    for n in notes:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    return lo, hi, " / ".join(uniq[:3])


def classify(show: Show, tmin: int = TARGET_MIN, tmax: int = TARGET_MAX) -> Show:
    """填入 show.age_* / suitable / score / tags。"""
    text = f"{show.title}\n{show.category}\n{show.description}"
    low = text.lower()
    lo, hi, note = parse_age(text)
    show.age_min, show.age_max, show.age_note = lo, hi, note

    score = 0
    tags: list[str] = []
    for kw, w in KID_KEYWORDS.items():
        if kw in low:
            score += w
            tags.append(kw)
    if "親子" in show.category or "兒童" in show.category:
        score += 3
    for kw in NEGATIVE_KEYWORDS:
        if kw in text:
            score -= 3

    if _RE_ADULT.search(text):
        show.suitable, show.score, show.tags = False, -10, ["成人限定"]
        return show

    if lo is not None or hi is not None:
        a = lo if lo is not None else 0
        b = hi if hi is not None else 99
        overlap = min(b, tmax) - max(a, tmin)
        if overlap >= 0:
            suitable = True
            score += 5
            tags.insert(0, f"{a}-{b if b < 99 else ''}歲".replace("-歲", "歲以上"))
        else:
            suitable = False
            score -= 10
    else:
        if any(k.lower() in low for k in BABY_ONLY):
            suitable = False
            tags.insert(0, "嬰幼兒專場")
        else:
            # 沒寫年齡：靠關鍵字判斷，分數夠才算
            suitable = score >= 3
            if suitable:
                tags.insert(0, "未標年齡")

    show.suitable, show.score, show.tags = suitable, score, tags
    return show
