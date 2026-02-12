@echo off
chcp 65001 >nul
cd /d "C:\Users\kim\OneDrive\업무\커서\SEC_project"
echo.
echo [Streamlit] 프로젝트 루트: %CD%
echo [Streamlit] 접속: http://127.0.0.1:8501
echo 종료: Ctrl+C
echo.
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
pause
