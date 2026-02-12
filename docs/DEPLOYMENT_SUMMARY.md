# AC-research 배포 요약

## 1. Render 배포 절차 요약

1. GitHub에 코드 push (monorepo, `apps/api` 포함).
2. [Render](https://render.com) → **New** → **Web Service** → 저장소 선택.
3. **Root Directory**: `apps/api` 지정.
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. **Environment** 탭에서 Secrets 추가:
   - `DART_API_KEY` (선택)
   - `YOUTUBE_API_KEY` (선택)
   - `ALLOWED_ORIGINS`: Vercel 배포 후 `https://<your-vercel-app>.vercel.app` 입력
7. **Create Web Service** → 배포 완료 후 URL 복사 (예: `https://ac-research-api.onrender.com`).

---

## 2. Vercel 배포 절차 요약

1. GitHub에 코드 push (monorepo, `apps/web` 포함).
2. [Vercel](https://vercel.com) → **Add New** → **Project** → 저장소 선택.
3. **Root Directory**: `apps/web` 로 Override.
4. **Environment Variables**:
   - `NEXT_PUBLIC_BACKEND_URL` = Render API URL (예: `https://ac-research-api.onrender.com`)
5. **Deploy** → 배포 완료 후 URL 복사 (예: `https://ac-research-web.vercel.app`).
6. Render로 돌아가서 `ALLOWED_ORIGINS`에 위 Vercel URL 추가 후 재배포(또는 환경변수만 저장).

---

## 3. 예상 운영 비용

| 서비스 | 플랜 | 비용 | 비고 |
|--------|------|------|------|
| **Render** (API) | Free | $0/월 | 인스턴스 슬립 가능, 요청 시 콜드 스타트. 750시간/월. |
| **Render** (API) | Starter | $7/월 | 항상 켜짐, 슬립 없음. |
| **Vercel** (Web) | Hobby | $0/월 | 개인/사이드 프로젝트. 대역폭 제한 있음. |
| **Vercel** (Web) | Pro | $20/월 | 팀·상업용. |

- **무료로 시작**: Render Free + Vercel Hobby → $0.  
- **안정적인 서비스**: Render Starter ($7) + Vercel Hobby ($0) 또는 Pro ($20).

---

## 4. 향후 확장 방향

- **로그인**: Clerk 또는 NextAuth로 소셜/이메일 로그인.
- **사용자별 저장**: 로그인 사용자별 검색 이력·저장 목록 → DB 필요.
- **사용량 제한**: IP/유저당 일일 요청 제한 → Redis 또는 DB 카운터.
- **Stripe 결제**: 유료 플랜(검색 횟수 확대, 엑셀 대량 등) 도입 시.
- **Redis 캐시**: 현재 10분 메모리 캐시 → Redis로 전환 시 다중 인스턴스·재시작 후에도 캐시 유지.
- **DB(PostgreSQL)**: 사용자, 저장된 검색, 사용량 이력 등 영구 저장.
