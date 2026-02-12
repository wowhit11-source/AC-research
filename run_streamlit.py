# -*- coding: utf-8 -*-
"""
Streamlit 앱 실행 스크립트.
- 모든 인터페이스(0.0.0.0)에서 접속 가능하도록 실행
- 8501 포트 사용 중이면 8502, 8503 ... 순으로 재시도
- Windows 방화벽 안내 출력
- 접속 URL 명시적 출력 후 서버 유지 (에러 시 로그 출력하고 대기)
"""
import socket
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_FILE = BASE_DIR / "app.py"
PORT_START = 8501
PORT_MAX_TRIES = 5


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


def find_available_port() -> int:
    for i in range(PORT_MAX_TRIES):
        port = PORT_START + i
        if not is_port_in_use(port):
            return port
    return PORT_START


def print_firewall_guide(port: int) -> None:
    if sys.platform != "win32":
        return
    print("-" * 60)
    print("[방화벽 안내] Windows 방화벽에서 연결이 차단될 수 있습니다.")
    print("  접속이 되지 않으면 다음을 확인하세요:")
    print("  1. 설정 > 개인 정보 보호 및 보안 > Windows 보안 > 방화벽 및 네트워크 보호")
    print("  2. 고급 설정 > 인바운드 규칙 > 새 규칙")
    print("  3. 포트 > TCP > 특정 로컬 포트: %d" % port)
    print("  4. 연결 허용 > (프로필 선택) > 이름 예: Streamlit %d" % port)
    print("-" * 60)


def main() -> None:
    port = find_available_port()
    if port != PORT_START:
        print("[포트] %d 사용 중이어서 포트 %d 로 실행합니다." % (PORT_START, port))

    print()
    print("  Local URL:   http://localhost:%d" % port)
    print("  Network URL: http://127.0.0.1:%d" % port)
    print("  (같은 PC 브라우저: 위 주소로 접속)")
    print()
    print_firewall_guide(port)
    print("서버를 시작합니다. 종료하려면 Ctrl+C 를 누르세요.")
    print()

    cmd = [
        sys.executable, "-m", "streamlit", "run", str(APP_FILE),
        "--server.address", "0.0.0.0",
        "--server.port", str(port),
    ]
    try:
        p = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            env={**dict(__import__("os").environ), "STREAMLIT_SERVER_HEADLESS": "true"},
        )
        sys.exit(p.returncode if p.returncode is not None else 0)
    except FileNotFoundError as e:
        print("[에러] Streamlit을 찾을 수 없습니다: %s" % e, file=sys.stderr)
        print("  다음으로 설치 후 다시 실행하세요: python -m pip install streamlit", file=sys.stderr)
        try:
            input("\n엔터를 누르면 종료합니다...")
        except EOFError:
            pass
        sys.exit(1)
    except Exception as e:
        print("[에러] %s" % e, file=sys.stderr)
        import traceback
        traceback.print_exc()
        try:
            input("\n엔터를 누르면 종료합니다...")
        except EOFError:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
