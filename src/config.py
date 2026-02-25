"""
설교 자동화 시스템 - 환경 설정 모듈

.env 파일에서 API 키와 모델 설정을 읽어옵니다.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트 기준)
load_dotenv(Path(__file__).parent.parent / ".env")


# ──────────────────────────────────────────
# Gemini API 설정
# ──────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ──────────────────────────────────────────
# 파이프라인 설정
# ──────────────────────────────────────────
# 각 Phase에서 Gemini에 보낼 최대 토큰 수
MAX_OUTPUT_TOKENS: int = 8192

# 생성 텍스트의 '창의성' 조절 (0.0~1.0, 높을수록 창의적)
TEMPERATURE: float = 0.7

# 출력 디렉토리
OUTPUT_DIR: Path = Path(__file__).parent.parent / "output"


def validate_config() -> None:
    """필수 설정값이 올바르게 입력되었는지 검증합니다."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_api_key_here":
        raise ValueError(
            "❌ GEMINI_API_KEY가 설정되지 않았습니다.\n"
            "   1. .env.example을 .env로 복사하세요.\n"
            "   2. https://aistudio.google.com/app/apikey 에서 API 키를 발급받으세요.\n"
            "   3. .env 파일에 GEMINI_API_KEY를 입력하세요."
        )
