# Git 초기화 및 GitHub 첫 push 안내

## 자동 실행이 안 되는 경우

에이전트 터미널에서는 한글 경로·Git PATH 이슈로 명령이 실패할 수 있습니다.  
**Cursor 하단 Terminal**에서 프로젝트 루트로 이동한 뒤 아래 중 하나를 실행하세요.

---

## 방법 1: 배치 파일 (Windows)

```cmd
cd "C:\Users\kim\OneDrive\업무\커서\SEC_project"
git_init_and_push.bat
```

URL 입력란에 GitHub 저장소 주소 입력 (예: `https://github.com/username/SEC_project.git`).

---

## 방법 2: PowerShell 스크립트

```powershell
cd "C:\Users\kim\OneDrive\업무\커서\SEC_project"
.\git_init_and_push.ps1
```

또는 URL을 인자로:

```powershell
.\git_init_and_push.ps1 -REPO_URL "https://github.com/username/SEC_project.git"
```

---

## 방법 3: 명령 직접 실행

```bash
cd "C:\Users\kim\OneDrive\업무\커서\SEC_project"
git init
git add .
git commit -m "initial monorepo deploy ready"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

**user.name / user.email 미설정 시** (처음 한 번):

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

이후 다시 `git commit` 실행.

---

## 생성된 .gitignore

- 제외: `node_modules/`, `.venv/`, `__pycache__/`, `.env`, `.env.local`, `secrets/`, `.streamlit/secrets.toml` 등
- 포함: `.env.local.example`, `.env.production.example` (예시만 커밋)
