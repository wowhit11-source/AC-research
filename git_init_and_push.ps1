# SEC_project: Git 초기화 및 첫 push
# Cursor 하단 Terminal에서 프로젝트 루트로 이동 후 실행: .\git_init_and_push.ps1
# GitHub repo URL은 아래 $REPO_URL에 넣거나, 실행 후 물어보면 입력.

param(
    [Parameter(Mandatory=$false)]
    [string]$REPO_URL
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

# 1) 이미 초기화되어 있으면 재초기화하지 않음
if (-not (Test-Path .git)) {
    git init
    Write-Host "[OK] git init"
} else {
    Write-Host "[SKIP] Git already initialized"
}

# 2) user.name / user.email 없으면 안내
$name = git config user.name 2>$null
$email = git config user.email 2>$null
if (-not $name -or -not $email) {
    Write-Host ""
    Write-Host "Git user.name 또는 user.email이 설정되지 않았습니다. 한 번만 설정하세요:"
    Write-Host '  git config --global user.name "Your Name"'
    Write-Host '  git config --global user.email "your@email.com"'
    Write-Host ""
    if (-not $name) { $name = "User" }
    if (-not $email) { $email = "user@local" }
}

# 3) add & commit
git add .
git status -s
git commit -m "initial monorepo deploy ready"
Write-Host "[OK] git add . && git commit"

# 4) main 브랜치
git branch -M main
Write-Host "[OK] git branch -M main"

# 5) remote & push
if (-not $REPO_URL) {
    $REPO_URL = Read-Host "GitHub repository URL 입력 (예: https://github.com/username/SEC_project.git)"
}
if ($REPO_URL) {
    git remote remove origin 2>$null
    git remote add origin $REPO_URL
    git push -u origin main
    Write-Host "[OK] git remote add origin & git push -u origin main"
} else {
    Write-Host ""
    Write-Host "GitHub URL을 입력하지 않았습니다. 아래를 직접 실행하세요:"
    Write-Host "  git remote add origin <your-repo-url>"
    Write-Host "  git push -u origin main"
}
