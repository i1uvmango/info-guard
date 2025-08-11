#!/usr/bin/env python3
"""
Info-Guard 통합 테스트 환경 설정 스크립트
필요한 Python 패키지들을 설치합니다.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """명령어 실행 및 결과 출력"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 완료")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 실패: {e}")
        if e.stderr:
            print(f"에러: {e.stderr}")
        return False

def check_python_version():
    """Python 버전 확인"""
    version = sys.version_info
    print(f"🐍 Python 버전: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        return False
    
    print("✅ Python 버전 요구사항 충족")
    return True

def install_requirements():
    """requirements.txt에서 패키지 설치"""
    requirements_file = Path("src/python-server/requirements.txt")
    
    if requirements_file.exists():
        print(f"📦 requirements.txt 파일 발견: {requirements_file}")
        return run_command(
            f"pip install -r {requirements_file}",
            "requirements.txt 패키지 설치"
        )
    else:
        print("⚠️ requirements.txt 파일을 찾을 수 없습니다.")
        return False

def install_integration_test_deps():
    """통합 테스트에 필요한 추가 패키지 설치"""
    packages = [
        "aiohttp",
        "websockets",
        "asyncio"
    ]
    
    for package in packages:
        if not run_command(f"pip install {package}", f"{package} 설치"):
            print(f"⚠️ {package} 설치 실패, 계속 진행...")

def check_servers():
    """서버 상태 확인"""
    print("\n🔍 서버 상태 확인...")
    
    # Python 서버 확인
    try:
        import requests
        response = requests.get("http://localhost:8000/health/", timeout=5)
        if response.status_code == 200:
            print("✅ Python 서버 실행 중 (포트 8000)")
        else:
            print("⚠️ Python 서버 응답 이상 (포트 8000)")
    except:
        print("❌ Python 서버 연결 실패 (포트 8000)")
    
    # Node.js 서버 확인
    try:
        response = requests.get("http://localhost:3000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Node.js 서버 실행 중 (포트 3000)")
        else:
            print("⚠️ Node.js 서버 응답 이상 (포트 3000)")
    except:
        print("❌ Node.js 서버 연결 실패 (포트 3000)")

def create_test_config():
    """테스트 설정 파일 생성"""
    config_content = """# Info-Guard 통합 테스트 설정
PYTHON_SERVER_URL=http://localhost:8000
NODEJS_SERVER_URL=http://localhost:3000
TEST_TIMEOUT=30
LOG_LEVEL=INFO
"""
    
    try:
        with open("test_config.env", "w", encoding="utf-8") as f:
            f.write(config_content)
        print("✅ 테스트 설정 파일 생성 완료: test_config.env")
        return True
    except Exception as e:
        print(f"❌ 테스트 설정 파일 생성 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 Info-Guard 통합 테스트 환경 설정 시작")
    print("=" * 50)
    
    # Python 버전 확인
    if not check_python_version():
        print("❌ Python 버전 요구사항을 충족하지 않습니다.")
        sys.exit(1)
    
    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"📁 현재 작업 디렉토리: {current_dir}")
    
    # Python 서버 디렉토리로 이동
    python_server_dir = current_dir / "src" / "python-server"
    if python_server_dir.exists():
        os.chdir(python_server_dir)
        print(f"📁 Python 서버 디렉토리로 이동: {python_server_dir}")
    else:
        print("❌ Python 서버 디렉토리를 찾을 수 없습니다.")
        sys.exit(1)
    
    # 가상환경 활성화 확인
    if "VIRTUAL_ENV" in os.environ:
        print(f"✅ 가상환경 활성화됨: {os.environ['VIRTUAL_ENV']}")
    else:
        print("⚠️ 가상환경이 활성화되지 않았습니다.")
        print("💡 Python 서버 디렉토리에서 가상환경을 활성화하는 것을 권장합니다.")
    
    # 패키지 설치
    print("\n📦 패키지 설치 중...")
    install_requirements()
    install_integration_test_deps()
    
    # 원래 디렉토리로 복귀
    os.chdir(current_dir)
    
    # 테스트 설정 파일 생성
    print("\n⚙️ 테스트 설정 파일 생성 중...")
    create_test_config()
    
    # 서버 상태 확인
    print("\n🔍 서버 상태 확인 중...")
    try:
        import requests
        check_servers()
    except ImportError:
        print("⚠️ requests 라이브러리가 설치되지 않아 서버 상태를 확인할 수 없습니다.")
    
    print("\n" + "=" * 50)
    print("🎉 통합 테스트 환경 설정 완료!")
    print("\n📋 다음 단계:")
    print("1. Python 서버 실행: cd src/python-server && python main.py")
    print("2. Node.js 서버 실행: cd src/nodejs-server && npm start")
    print("3. 통합 테스트 실행: python src/integration-test.py")
    print("\n💡 서버가 실행되지 않은 상태에서 테스트를 실행하면 연결 오류가 발생할 수 있습니다.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ 설정이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 설정 중 오류 발생: {e}")
        sys.exit(1)
