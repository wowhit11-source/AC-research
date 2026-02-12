@echo off
chcp 65001 >nul
set REPO_URL=https://github.com/wowhit11-source/AC-research.git
pushd "%~dp0"

if not defined GIT (
  where git >nul 2>&1 && set GIT=git
)
if not defined GIT (
  if exist "C:\Program Files\Git\bin\git.exe" set "GIT=C:\Program Files\Git\bin\git.exe"
)
if not defined GIT (
  if exist "C:\Program Files (x86)\Git\bin\git.exe" set "GIT=C:\Program Files (x86)\Git\bin\git.exe"
)
if not defined GIT (
  echo ERROR: git not found in PATH. Run this script from Cursor Terminal (bottom panel).
  exit /b 1
)

echo [1] Git status / init
if not exist .git (
  "%GIT%" init
  echo   git init done.
) else (
  echo   .git exists, skip init.
)

echo.
echo [2] user.name / user.email
"%GIT%" config user.name >nul 2>&1 || "%GIT%" config --global user.name "kim"
"%GIT%" config user.email >nul 2>&1 || "%GIT%" config --global user.email "wowhit11-source@users.noreply.github.com"
echo   user.name / user.email set if missing.

echo.
echo [3] git add .
"%GIT%" add .

echo.
echo [4] git commit
"%GIT%" commit -m "initial monorepo deploy ready"
if errorlevel 1 echo   No changes to commit or already committed.

echo.
echo [5] git branch -M main
"%GIT%" branch -M main

echo.
echo [6] remote origin
"%GIT%" remote get-url origin >nul 2>&1
if errorlevel 1 (
  "%GIT%" remote add origin %REPO_URL%
  echo   remote add origin done.
) else (
  "%GIT%" remote set-url origin %REPO_URL%
  echo   remote set-url origin done.
)

echo.
echo [7] git push -u origin main
"%GIT%" push -u origin main
if errorlevel 1 (
  echo   PUSH FAILED. If auth required, use Personal Access Token or SSH.
  popd
  exit /b 1
)
echo   Push success.
popd
exit /b 0
