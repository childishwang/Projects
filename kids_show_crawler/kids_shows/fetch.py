"""有禮貌的 HTTP 抓取：固定 User-Agent、逾時、重試、每次請求之間暫停。"""
from __future__ import annotations

import logging
import time

import requests

log = logging.getLogger(__name__)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 kids-show-crawler/1.0")


class Fetcher:
    def __init__(self, delay: float = 1.0, timeout: float = 20.0, retries: int = 3):
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self._last = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA,
                                     "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"})

    def get(self, url: str, **kw) -> requests.Response:
        err: Exception | None = None
        for attempt in range(1, self.retries + 1):
            wait = self.delay - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            try:
                self._last = time.monotonic()
                r = self.session.get(url, timeout=self.timeout, **kw)
                r.raise_for_status()
                if not r.encoding or r.encoding.lower() == "iso-8859-1":
                    r.encoding = r.apparent_encoding
                return r
            except requests.RequestException as e:
                err = e
                log.warning("GET %s 失敗 (第 %d 次): %s", url, attempt, e)
                time.sleep(2 ** attempt)
        raise RuntimeError(f"無法取得 {url}: {err}")
