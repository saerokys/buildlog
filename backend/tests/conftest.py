import os

# 테스트는 .env 파일 없이도 실행되어야 하므로 테스트용 값을 먼저 넣습니다.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-real-use")
