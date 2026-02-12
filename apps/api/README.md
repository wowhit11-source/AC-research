# AC-research API (FastAPI)

Backend for AC-research: SEC/DART/YouTube/Papers search and Excel export.

## Endpoints

- `GET /health` — `{"ok": true}` (Render health check용)
- `POST /api/research` — Body: `{"query": "string"}`. Returns JSON with `results.dart`, `results.sec`, `results.youtube`, `results.papers`, and `meta.elapsed_ms`, `meta.errors`.
- `GET /api/research/{slug}/excel` — Download `research_{slug}.xlsx` (해당 쿼리 검색 후 10분 이내 캐시 사용).

## Local run

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API: http://127.0.0.1:8000

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DART_API_KEY` | DART 사용 시 | [opendart.fss.or.kr](https://opendart.fss.or.kr) 발급. 없으면 DART 제외. |
| `YOUTUBE_API_KEY` | YouTube 사용 시 | Google Cloud YouTube Data API v3. 없으면 YouTube 제외. |
| `ALLOWED_ORIGINS` | Production 권장 | CORS 허용 도메인. 쉼표 구분 (예: `https://ac-research-web.vercel.app`). 비우면 `*`. |
| `ENV` | Optional | `production`이면 FastAPI debug=False. |

SEC·OpenAlex(논문)는 API 키 불필요.

---

## Render 배포 방법

1. **GitHub에 푸시**  
   이 리포지토리를 GitHub에 push합니다.

2. **Render 로그인**  
   [render.com](https://render.com) → Sign In → GitHub 연결.

3. **New Web Service**  
   - Dashboard → **New** → **Web Service**
   - GitHub 저장소 선택
   - **Root Directory**: `apps/api` 로 설정 (반드시 지정)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free (또는 유료 플랜)

4. **Environment Variables (Secrets)**  
   **Environment** 탭에서 추가:
   - `DART_API_KEY`: (opendart 키)
   - `YOUTUBE_API_KEY`: (Google YouTube API 키)
   - `ALLOWED_ORIGINS`: `https://your-app.vercel.app` (Vercel 배포 후 실제 URL로 교체)

5. **Health Check**  
   Render 대시보드에서 **Health Check Path**: `/health` 로 설정 (선택 사항, 기본 통과).

6. **Deploy**  
   **Create Web Service** 클릭. 빌드·배포 후 서비스 URL 예: `https://ac-research-api.onrender.com`

7. **Blueprint (선택)**  
   저장소 루트가 아닌 `apps/api` 에서만 배포할 경우, Render 대시보드에서 **Root Directory**를 `apps/api`로 지정하면 `render.yaml` 대신 수동 설정이 적용됩니다. `render.yaml`을 쓰려면 Blueprint로 한 번에 배포할 수 있습니다.

---

## Deployment Checklist

배포 후 점검 항목은 루트 `docs/DEPLOYMENT_CHECKLIST.md` 참고.

- [ ] `/health` 200
- [ ] `POST /api/research` 200
- [ ] `GET /api/research/{slug}/excel` 다운로드
- [ ] Vercel 프론트에서 API 호출 성공, CORS 에러 없음
- [ ] 환경변수 (DART, YOUTUBE, ALLOWED_ORIGINS) 설정

---

## CORS

- 로컬: `ALLOWED_ORIGINS` 미설정 시 `*` (모든 origin 허용).
- Production: Render에서 `ALLOWED_ORIGINS`에 Vercel 프론트 URL만 설정 (쉼표로 여러 개 가능). 예: `https://ac-research-web.vercel.app`
