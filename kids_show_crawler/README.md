# 兒童演出爬蟲 (3-10 歲)

這個爬蟲會從台灣幾個主要的演出資料來源抓節目，自動判斷每個節目適合幾歲，
最後只留下 **3-10 歲小朋友可以看** 的演出，輸出成可以搜尋的網頁、Excel 能開的 CSV，以及 JSON。

## 資料來源

| 代號 | 來源 | 說明 |
|---|---|---|
| `culture` | 文化部藝文活動開放資料 | 政府公開 API，彙整全台場館、兩廳院、各縣市文化局的演出。抓「親子、戲劇、舞蹈、音樂、綜藝」五類 |
| `kktix` | KKTIX | 用公開的 Atom feed 搜尋「親子、兒童劇、兒童、小朋友、偶戲、繪本」 |

要加其他網站（OPENTIX、寬宏、年代、ibon），在 `kids_shows/sources/` 新增一個模組，
實作 `NAME` 與 `fetch(fetcher, **opts) -> list[Show]`，再登記到 `sources/__init__.py`。

## 安裝與執行

```bash
cd kids_show_crawler
pip install -r requirements.txt
python -m kids_shows
```

跑完後打開 `output/kids_shows.html`。

### 常用選項

```bash
python -m kids_shows --city 台北 --city 新北     # 只看雙北
python -m kids_shows --days 30                   # 只看未來 30 天
python -m kids_shows --min-age 4 --max-age 6     # 改年齡區間
python -m kids_shows --strict                    # 只留有明確寫年齡的
python -m kids_shows --details                   # KKTIX 逐頁抓詳細說明（慢，但更準）
python -m kids_shows --sources culture           # 只用文化部資料
```

## 年齡怎麼判斷（`kids_shows/age.py`）

1. 從標題和介紹找年齡描述：「建議 4 歲以上」「適合 3-12 歲」「未滿 6 歲謝絕入場」「五至十歲」等，中文數字也能讀
2. 排除票務規定，例如「2 歲以上需購票」「3 歲以下免費」「65 歲以上敬老票」「身高未滿 110 公分」
3. 年齡區間和 3-10 歲有重疊就保留；限制級或 18 歲以上的直接排除；只寫 0-3 歲的寶寶場也排除
4. 沒寫年齡的節目，用「親子、兒童劇、繪本、偶戲…」等關鍵字打分數，分數夠高才保留，並標上「未標年齡」

年齡是程式自動判斷的，**購票前請再看一次主辦單位的說明**。

## 測試

```bash
python -m pytest -q
```

## 注意

- 預設每次請求間隔 1 秒，請不要調得太低，以免造成網站負擔
- 網站改版時解析可能失效，看到 log 有錯誤時要更新對應的 `sources/*.py`
