# Deployment Checklist (배포 후 점검)

배포 후 아래 항목을 순서대로 확인하세요.

## Render (API)

- [ ] **Health**  
  `GET https://<your-render-url>/health` → `{"ok": true}` 응답 (200)
- [ ] **Research**  
  `POST https://<your-render-url>/api/research`  
  Body: `{"query": "DIS"}` → 200, JSON에 `query`, `slug`, `results`, `meta` 포함
- [ ] **Excel**  
  동일 쿼리로 검색 후  
  `GET https://<your-render-url>/api/research/<slug>/excel`  
  → 파일 다운로드, 파일명 `research_<slug>.xlsx`
- [ ] **환경변수**  
  Render 대시보드 → Environment: `DART_API_KEY`, `YOUTUBE_API_KEY`, `ALLOWED_ORIGINS` 설정 여부

## Vercel (Web)

- [ ] **프론트 접속**  
  `https://<your-vercel-url>` 접속 시 검색 화면 로드
- [ ] **API 호출 성공**  
  검색창에 쿼리 입력 → 검색 → 결과 탭(DART/SEC/YouTube/Papers)에 데이터 표시
- [ ] **CORS 에러 없음**  
  브라우저 개발자도구(F12) → Console/Network에 CORS 관련 에러 없음
- [ ] **엑셀 다운로드**  
  검색 후 "엑셀 다운로드" 클릭 → `research_<slug>.xlsx` 다운로드
- [ ] **환경변수**  
  Vercel → Settings → Environment Variables: `NEXT_PUBLIC_BACKEND_URL` = Render API URL

## 연동 확인

- [ ] Vercel 도메인이 Render의 `ALLOWED_ORIGINS`에 포함되어 있음
- [ ] `NEXT_PUBLIC_BACKEND_URL`에 슬래시 없이 입력 (예: `https://ac-research-api.onrender.com`)
