"""
설교 자동화 시스템 - Gemini API 클라이언트

google.genai 라이브러리를 래핑하여
시스템 프롬프트와 사용자 프롬프트를 조합해 Gemini에 요청을 보냅니다.
Exponential Backoff 재시도 로직으로 일시적 오류(503, 429)에 자동 대응합니다.
"""

import time

from google import genai
from google.genai import types
from rich.console import Console

from src.config import GEMINI_API_KEY, GEMINI_MODEL, MAX_OUTPUT_TOKENS, TEMPERATURE

console = Console()

# ──────────────────────────────────────────
# 재시도 설정
# ──────────────────────────────────────────
MAX_RETRIES = 3          # 최대 재시도 횟수
INITIAL_DELAY = 2.0      # 첫 번째 재시도까지 대기 시간(초)
BACKOFF_FACTOR = 2.0     # 대기 시간 배수 (2초 → 4초 → 8초)

# 재시도할 가치가 있는 HTTP 상태 코드 (일시적 오류)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class GeminiClient:
    """Gemini API와의 통신을 담당하는 클라이언트 클래스.

    왜 클래스로 만들었나?
    - API 키 설정과 클라이언트 초기화를 한 번만 수행하고 재사용하기 위함입니다.
    - Phase별로 다른 시스템 프롬프트를 적용하면서도 동일한 클라이언트를 공유합니다.
    """

    def __init__(self) -> None:
        """API 키를 설정하고 Gemini 클라이언트를 초기화합니다."""
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = GEMINI_MODEL

    def _is_retryable(self, error: Exception) -> bool:
        """오류가 재시도할 가치가 있는 일시적 오류인지 판단합니다.

        판단 기준 (우선순위 순):
        1. 예외 타입 검사 — ConnectionError, TimeoutError, OSError 등
           네트워크 관련 예외는 메시지 언어와 무관하게 재시도 대상입니다.
        2. HTTP 상태 코드 검사 — 503, 429 등 일시적 서버 오류
        3. 키워드 검사 — 영어/한국어 오류 메시지 패턴 매칭
        """
        # 1단계: 예외 타입으로 판단 (가장 신뢰할 수 있는 방법)
        #   - ConnectionError: 서버 연결 실패
        #   - TimeoutError: 요청 시간 초과
        #   - OSError: WinError 10060 등 OS 수준 네트워크 오류
        if isinstance(error, (ConnectionError, TimeoutError, OSError)):
            return True

        error_str = str(error)

        # 2단계: HTTP 상태 코드가 오류 메시지에 포함되어 있는지 확인
        for code in RETRYABLE_STATUS_CODES:
            if str(code) in error_str:
                return True

        # 3단계: 키워드 매칭 (영어 + 한국어 + Windows 오류 패턴)
        retryable_keywords = [
            # 영어 키워드
            "timeout", "connection", "unavailable", "temporarily",
            "service unavailable", "deadline exceeded",
            # 한국어 키워드 (Windows 한국어 에러 메시지 대응)
            "연결", "응답이 없", "시간 초과", "끊어졌",
            # Windows 특유의 네트워크 오류
            "winerror",
        ]
        return any(keyword in error_str.lower() for keyword in retryable_keywords)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """시스템 프롬프트와 사용자 프롬프트를 조합하여 텍스트를 생성합니다.

        Exponential Backoff 패턴으로 일시적 오류 시 자동 재시도합니다.
        - 1차 실패 → 2초 대기 후 재시도
        - 2차 실패 → 4초 대기 후 재시도
        - 3차 실패 → 8초 대기 후 재시도
        - 그래도 실패 → 예외 발생

        Args:
            system_prompt: AI의 역할과 행동 규칙을 정의하는 프롬프트.
                          예시: "당신은 설교 조력자 윤비서입니다..."
            user_prompt:   사용자의 구체적 요청 내용.
                          예시: "에스겔 36-37장에서 설교 본문을 선정해주세요"

        Returns:
            Gemini가 생성한 텍스트 응답.

        Raises:
            Exception: 모든 재시도가 실패하거나 재시도 불가능한 오류 시 예외를 발생시킵니다.
        """
        last_error = None
        delay = INITIAL_DELAY

        for attempt in range(1, MAX_RETRIES + 2):  # 최초 1회 + 재시도 MAX_RETRIES회
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        max_output_tokens=MAX_OUTPUT_TOKENS,
                        temperature=TEMPERATURE,
                    ),
                )
                return response.text

            except Exception as e:
                last_error = e

                # 재시도 불가능한 오류(인증 실패 등)는 즉시 실패 처리
                if not self._is_retryable(e):
                    console.print(f"[bold red]❌ Gemini API 오류 (재시도 불가):[/bold red] {e}")
                    raise

                # 최대 재시도 횟수를 초과하면 실패 처리
                if attempt > MAX_RETRIES:
                    console.print(
                        f"[bold red]❌ Gemini API 오류: {MAX_RETRIES}회 재시도 후에도 실패했습니다.[/bold red]"
                    )
                    raise

                # 재시도 안내 메시지 출력 후 대기
                console.print(
                    f"[bold yellow]⚠️  일시적 오류 발생 (시도 {attempt}/{MAX_RETRIES + 1}): {e}[/bold yellow]"
                )
                console.print(
                    f"[dim]   → {delay:.0f}초 후 재시도합니다...[/dim]"
                )
                time.sleep(delay)
                delay *= BACKOFF_FACTOR  # 대기 시간을 배로 늘림

        # 이론적으로 도달하지 않지만, 안전장치로 추가
        raise last_error
