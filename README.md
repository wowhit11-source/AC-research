# 티커 URL 수집기 (Ticker Links Collector)

티커(symbol)를 입력하면 SEC, 논문(arXiv), 뉴스, 리서치 4개 소스에서 관련 URL을 수집하여 하나의 CSV 파일로 저장합니다.

**LLM 미사용** - 일반 웹 요청과 파싱만 사용합니다.

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

```bash
# 사용법: python main.py AAPL
python main.py AAPL
```

```bash
python src/youtube_scraper.py
```

출력: `data/AAPL_links.csv`

### 옵션

- `-o, --output`: 출력 CSV 경로 지정 (기본: data/{ticker}_links.csv)

## CSV 컬럼

| 컬럼 | 설명 |
|------|------|
| source_type | SEC / paper / news / research |
| title | 제목 |
| url | 웹페이지/문서 URL |
| published_date | 게시일 (가능한 경우) |
| ticker | 종목 티커 |

## API 키 설정

다음 소스는 API 키가 필요합니다. 코드 내 PLACEHOLDER를 본인 키로 교체하세요.

1. **뉴스 (NewsAPI)**  
   `src/news_scraper.py` → `NEWS_API_KEY = "YOUR_NEWSAPI_KEY_HERE"`  
   - 발급: https://newsapi.org/

2. **리서치 (Bing Web Search)**  
   `src/research_scraper.py` → `BING_SEARCH_KEY = "YOUR_BING_SEARCH_KEY_HERE"`  
   - 발급: Azure Portal

API 키가 없으면 해당 소스는 건너뛰고, SEC·arXiv는 별도 키 없이 동작합니다.
