"""資料來源。每個來源提供 fetch(fetcher, **opts) -> list[Show]。

要新增來源（例如 OPENTIX、寬宏、年代），在這個資料夾加一個模組，
實作 NAME 與 fetch()，再加進下面的 SOURCES 即可。
"""
from . import culture_gov, kktix

SOURCES = {
    culture_gov.NAME: culture_gov,
    kktix.NAME: kktix,
}
