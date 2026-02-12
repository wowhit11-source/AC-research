# AC-research Web (Next.js)

Frontend for AC-research. Single page: search box, result tabs (DART / SEC / YouTube / Papers), Excel download.

## Environment

Create `.env.local` (local):

```env
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

Default is `http://127.0.0.1:8000` if unset.  
Production: `.env.production.example` 참고 → Vercel에서 `NEXT_PUBLIC_BACKEND_URL` 설정.

## Local run

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000

## Build

```bash
npm run build
npm start
```

---

## Vercel 배포 방법

1. **GitHub에 푸시**  
   이 리포지토리를 GitHub에 push합니다.

2. **Vercel 로그인**  
   [vercel.com](https://vercel.com) → Sign In → GitHub 연결.

3. **Import Project**  
   - **Add New** → **Project**
   - GitHub 저장소 선택
   - **Root Directory**: `apps/web` 로 설정 (**Override** 클릭 후 `apps/web` 입력)
   - **Framework Preset**: Next.js (자동 인식)

4. **Environment Variable**  
   - **Key**: `NEXT_PUBLIC_BACKEND_URL`
   - **Value**: Render에 배포한 API URL (예: `https://ac-research-api.onrender.com`)
   - **Environment**: Production (및 Preview 원하면 선택)

5. **Deploy**  
   **Deploy** 클릭. 빌드 후 배포 URL 예: `https://ac-research-web.vercel.app`

6. **CORS**  
   Render API의 **Environment Variables**에 `ALLOWED_ORIGINS` = `https://ac-research-web.vercel.app` (위에서 나온 실제 Vercel URL) 로 설정해야 프론트에서 API 호출 시 CORS 에러가 나지 않습니다.

---

## Deployment Checklist

배포 후 점검: `docs/DEPLOYMENT_CHECKLIST.md` 참고.

- [ ] Vercel 프론트 접속 정상
- [ ] 검색 → API 호출 성공, CORS 에러 없음
- [ ] 엑셀 다운로드 정상
- [ ] `NEXT_PUBLIC_BACKEND_URL` 설정

---

## API 호출

모든 API 요청은 `process.env.NEXT_PUBLIC_BACKEND_URL` (또는 기본값)을 사용합니다.  
`app/page.tsx`에서 `fetch(\`${BACKEND_URL}/api/research\`, ...)` 로 호출합니다.
