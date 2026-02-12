# Streamlit 실행 안내 (AC-research)

## ⚠️ Command line navigation 사용 금지

- **상단/Agent의 "Command line navigation"에서 실행하지 마세요.**  
  거기서 실행하면 백그라운드로만 돌아가서 브라우저 접속이 안 됩니다.
- **반드시 Cursor 하단 "Terminal" 탭**에서 아래 명령을 직접 실행하세요.

---

## 실행 절차

### 1. 하단 Terminal 탭 열기

Cursor 하단에서 **"Terminal"** 탭을 클릭해 터미널을 엽니다.

### 2. 아래 두 줄을 순서대로 실행

**첫 번째 줄:** 프로젝트 루트로 이동

```powershell
cd "C:\Users\kim\OneDrive\업무\커서\SEC_project"
```

**두 번째 줄:** Streamlit 포그라운드 실행 (서버가 이 터미널에서 계속 실행됩니다)

```powershell
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

### 3. 실행 로그 확인

실행이 되면 터미널에 예를 들어 다음과 같이 나와야 합니다:

```
Local URL: http://127.0.0.1:8501
Network URL: http://127.0.0.1:8501
```

**이 문구가 보이면** 브라우저 주소창에 **반드시 포트 번호까지** 입력하세요:
- **http://127.0.0.1:8501** (8501로 실행한 경우)
- `127.0.0.1` 만 입력하면 포트 80으로 접속해 **ERR_CONNECTION_REFUSED** 가 납니다.

이메일 입력 창이 나오면 **Enter**만 눌러 건너뛰면 됩니다.

### 4. 종료 방법

서버를 끄려면 **해당 Terminal 탭에서 `Ctrl+C`** 를 누르세요.

---

## 현재 경로 확인

Terminal에서 프로젝트 루트에 있는지 확인하려면:

```powershell
Get-Location
```

출력에 `SEC_project` 가 포함되어 있으면 올바른 폴더입니다.  
다른 경로라면 위의 `cd "C:\Users\kim\OneDrive\업무\커서\SEC_project"` 를 다시 실행한 뒤 Streamlit 명령을 실행하세요.

---

## DART API 설정 방법 (국내 재무제표 검색용)

국내 종목번호(6자리)로 재무제표를 검색하려면 DART Open API 인증키가 필요합니다.

### 1. PowerShell에서 환경변수 설정

아래 명령을 **한 번만** 실행합니다.

```powershell
setx DART_API_KEY "3f82974d72dcfa0884b605dc78190f6cf44b6191"
```

### 2. 터미널 재시작

**터미널을 완전히 닫았다가 다시 열어야** 환경변수가 적용됩니다.

### 3. 적용 여부 확인

새 터미널에서 다음 명령으로 키가 설정되었는지 확인합니다.

```powershell
echo $env:DART_API_KEY
```

위 명령 실행 시 `3f82974d72dcfa0884b605dc78190f6cf44b6191` 이 출력되면 정상입니다.

### 4. Streamlit 실행

이후 앱을 실행합니다.

```powershell
python -m streamlit run app.py
```

- **키가 설정되지 않은 상태**에서 국내 종목(예: 005930) 재무제표를 검색하면  
  화면에 **"DART API 키가 설정되지 않았습니다. 실행 안내 문서를 확인하세요."** 메시지가 표시됩니다.
- 키 설정 후에는 동일한 검색이 정상 동작합니다.

---

## 리서치 보조 도구 로고 파일

- **위치**: `assets/logos/` (또는 `assets/`).  
- **파일명 규칙**: 소문자, 확장자 `.png` 하나만 사용 — `chatgpt.png`, `gemini.png`, `claude.png`, `notebooklm.png`.  
- 이중 확장자(`.png.png`)는 탐색기에서 확장자 표시를 켠 뒤 `chatgpt.png` 등으로 수정하면 됩니다.
