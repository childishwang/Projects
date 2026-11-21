import pytest

from kids_shows.age import classify, parse_age
from kids_shows.models import Show


@pytest.mark.parametrize("text,lo,hi", [
    ("建議4歲以上觀賞", 4, None),
    ("適合3歲(含)以上兒童", 3, None),
    ("適合年齡：3-12歲", 3, 12),
    ("適合 3～8 歲小朋友", 3, 8),
    ("建議年齡 五至十歲", 5, 10),
    ("未滿7歲請勿入場", 7, None),
    ("未滿六歲謝絕入場", 6, None),
    ("2歲以上需購票入場", None, None),          # 票務規定，不是觀賞年齡
    ("3歲以下免費入場，不佔位", None, None),
    ("65歲以上敬老票五折", None, None),
    ("身高未滿110公分兒童免費", None, None),
    ("建議6歲以上；未滿4歲謝絕入場", 6, None),
    ("一場愉快的音樂會", None, None),
])
def test_parse_age(text, lo, hi):
    a, b, _ = parse_age(text)
    assert (a, b) == (lo, hi)


def _c(title, desc="", cat=""):
    return classify(Show(source="t", title=title, description=desc, category=cat))


def test_suitable_with_age():
    s = _c("小紅帽兒童劇", "適合 4-10 歲")
    assert s.suitable and s.age_min == 4 and s.age_max == 10


def test_too_old():
    assert not _c("莎士比亞悲劇", "建議12歲以上觀賞").suitable


def test_baby_only_range():
    assert not _c("寶寶音樂會", "0-2歲寶寶與家長").suitable


def test_adult():
    assert not _c("午夜脫口秀", "未滿18歲禁止入場，限制級").suitable


def test_no_age_but_kid_keywords():
    s = _c("繪本音樂會", "親子同樂，帶孩子一起聽故事", cat="親子")
    assert s.suitable and s.tags[0] == "未標年齡"


def test_no_age_no_keywords():
    assert not _c("貝多芬第九號交響曲", "國家交響樂團").suitable
