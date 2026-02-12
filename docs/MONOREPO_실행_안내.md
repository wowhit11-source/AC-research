# AC-research 모노레포 실행 안내 (Next.js + FastAPI)

프론트(Next.js)와 백엔드(FastAPI)를 분리한 웹 서비스 구조입니다.

## 디렉터리 구조

```
SEC_project/
  apps/
    api/          # FastAPI (백엔드)
    web/          # Next.js (프론트)
  app.py          # 기존 Streamlit (로컬용)
  src/            # 기존 스크래퍼 (Streamlit용)
```

## 1. 백엔드 API 실행

```powershell
cd apps\api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

환경변수 (선택):

- `DART_API_KEY` — 국내 DART 재무제표용 (opendart.fss.or.kr 발급)
- `YOUTUBE_API_KEY` — YouTube 검색용 (Google Cloud 발급)

```powershell
uvicorn app.main:app --reload --port 8000
```

API: http://127.0.0.1:8000  
문서: http://127.0.0.1:8000/docs

## 2. 프론트(Next.js) 실행

```powershell
cd apps\web
npm install
npm run dev
```

웹: http://localhost:3000

백엔드 주소가 8000이 아니면 `apps/web/.env.local`에 설정:

```env
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

## 3. 동시 실행 (로컬에서 web + api)

1. **터미널 1** — API  
   `cd apps\api` → `.venv\Scripts\activate` → `uvicorn app.main:app --reload --port 8000`

2. **터미널 2** — Web  
   `cd apps\web` → `npm run dev`

3. 브라우저에서 http://localhost:3000 접속 후 검색창에 쿼리 입력 → 검색 → 탭으로 결과 확인 → "엑셀 다운로드"로 `research_{slug}.xlsx` 받기

## API 엔드포인트 요약

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /health | 상태 확인 `{"ok": true}` |
| POST | /api/research | Body: `{"query": "string"}` → JSON 결과 (dart/sec/youtube/papers) |
| GET | /api/research/{slug}/excel | 동일 쿼리 검색 후 10분 이내에 다운로드 가능 |

엑셀 파일명: `research_{slug}.xlsx` (기존 규칙 유지)
