# GitHub 초기 푸시 실행 안내

## 자동 실행 실패 시 (에이전트 터미널)

에이전트 터미널에서는 한글 경로·PATH 이슈로 `git_init_and_push.bat` 실행이 실패할 수 있습니다.

**Cursor 하단 "Terminal"**에서 아래를 실행하세요.

```cmd
cd "C:\Users\kim\OneDrive\업무\커서\SEC_project"
git_init_and_push.bat
```

또는 탐색기에서 `SEC_project` 폴더를 연 뒤 `git_init_and_push.bat` 더블클릭.

---

## 스크립트가 하는 일

1. `.git` 없으면 `git init`
2. `user.name` / `user.email` 없으면 `kim`, `wowhit11-source@users.noreply.github.com` 설정
3. `git add .` → `git commit -m "initial monorepo deploy ready"`
4. `git branch -M main`
5. `origin` 없으면 `git remote add origin https://github.com/wowhit11-source/AC-research.git`, 있으면 `git remote set-url origin ...`
6. `git push -u origin main`

---

## 인증 필요 시

- **HTTPS**: GitHub Personal Access Token (Settings → Developer settings → Personal access tokens) 생성 후, push 시 비밀번호 대신 토큰 입력.
- **SSH**: `git remote set-url origin git@github.com:wowhit11-source/AC-research.git` 로 바꾼 뒤 SSH 키 등록 후 push.

---

## .gitignore

이미 루트에 있으며 다음을 제외합니다: `node_modules/`, `.venv/`, `__pycache__/`, `.env`, `.next/` 등.
