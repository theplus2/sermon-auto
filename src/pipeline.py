"""
설교 자동화 시스템 - 파이프라인 오케스트레이터

Phase 1~5를 순차 실행하며 각 Phase의 결과를 다음 Phase에 전달합니다.
"완전 자동 모드"로 설계되어 최초 성경 범위 입력 후 최종 설교 패키지까지
사람 개입 없이 자동 실행됩니다.
"""

from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.api_client import GeminiClient
from src.config import OUTPUT_DIR
from src.prompts.phase1 import PHASE1_SYSTEM, get_phase1_prompt
from src.prompts.phase2 import PHASE2_SYSTEM, get_phase2_prompt
from src.prompts.phase3 import PHASE3_SYSTEM, get_phase3_prompt
from src.prompts.phase4 import PHASE4_SYSTEM, get_phase4_prompt
from src.prompts.phase5 import PHASE5_SYSTEM, get_phase5_prompt

console = Console()


class SermonPipeline:
    """설교 작성 파이프라인.

    Phase 1 → 2 → 3 → 4 → 5를 자동으로 순차 실행합니다.
    각 Phase의 결과는 output/ 디렉토리에 저장되며,
    최종적으로 Word 파일로 내보냅니다.
    """

    def __init__(self) -> None:
        self.client = GeminiClient()
        self.results: dict[str, str] = {}
        self.output_dir: Path = OUTPUT_DIR
        # 설교 예정일 기준 하위 폴더 (run() 호출 시 설정됨)
        self.date_dir: Path = OUTPUT_DIR
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """출력 디렉토리가 없으면 생성합니다."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _save_result(self, filename: str, content: str) -> Path:
        """Phase 결과를 마크다운 파일로 저장합니다.

        Args:
            filename: 저장할 파일명 (예: "phase1_본문선정.md")
            content:  저장할 내용

        Returns:
            저장된 파일의 경로
        """
        filepath = self.date_dir / filename
        filepath.write_text(content, encoding="utf-8")
        return filepath

    def run_phase(
        self,
        phase_num: int,
        phase_name: str,
        system_prompt: str,
        user_prompt: str,
        filename: str,
    ) -> str:
        """하나의 Phase를 실행하고 결과를 저장합니다.

        Args:
            phase_num:     Phase 번호 (1-5)
            phase_name:    Phase 한글 이름 (예: "본문 선정")
            system_prompt: 해당 Phase의 시스템 프롬프트
            user_prompt:   해당 Phase의 사용자 프롬프트
            filename:      결과를 저장할 파일명

        Returns:
            Gemini가 생성한 결과 텍스트
        """
        console.print()
        console.print(
            Panel(
                f"[bold]Phase {phase_num}: {phase_name}[/bold]",
                style="cyan",
                width=50,
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Phase {phase_num} 처리 중... (Gemini 응답 대기)", total=None
            )

            result = self.client.generate(system_prompt, user_prompt)
            progress.update(task, completed=True)

        # 결과 저장
        filepath = self._save_result(filename, result)
        console.print(f"  💾 저장 완료: [green]{filepath}[/green]")

        return result

    def run(
        self,
        bible_range: str,
        sermon_date: str = "",
        sermon_context: str | None = None,
        sermon_tone: str = "일상",
        sermon_duration: str = "40",
    ) -> dict[str, str]:
        """전체 파이프라인을 실행합니다.

        Args:
            bible_range:     사용자가 입력한 성경 범위. 예: "에스겔 36-37장"
            sermon_date:     설교 예정일. 예: "2026년 02월 23일"
            sermon_context:  이번 주 성도들의 삶의 상황·교회 분위기 (선택)
            sermon_tone:     설교 어조. 도전/위로/교육/일상 중 택일
            sermon_duration: 설교 예상 시간(분). '15'/'30'/'40'/'60'

        Returns:
            각 Phase의 결과를 담은 딕셔너리.
            키: "phase1", "phase2", ..., "phase5"
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 설교 예정일 기준으로 하위 폴더 생성 (예: output/2026 0302/)
        if sermon_date:
            try:
                parsed = datetime.strptime(sermon_date, "%Y년 %m월 %d일")
                self.date_dir = self.output_dir / parsed.strftime("%Y %m%d")
            except ValueError:
                self.date_dir = self.output_dir / datetime.now().strftime("%Y %m%d")
        else:
            self.date_dir = self.output_dir / datetime.now().strftime("%Y %m%d")
        self.date_dir.mkdir(parents=True, exist_ok=True)

        console.print()
        console.print(
            Panel(
                "[bold yellow]🔖 설교 작성 자동화 시스템[/bold yellow]\n"
                f"📖 성경 범위: [cyan]{bible_range}[/cyan]\n"
                f"📅 설교 예정일: [cyan]{sermon_date}[/cyan]\n"
                f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                title="[bold]Sermon Auto v1.0[/bold]",
                width=60,
            )
        )

        # ── Phase 1: 본문 선정 ──
        phase1 = self.run_phase(
            phase_num=1,
            phase_name="본문 선정 및 주제 개발",
            system_prompt=PHASE1_SYSTEM,
            user_prompt=get_phase1_prompt(bible_range, sermon_context),
            filename=f"{timestamp}_phase1_본문선정.md",
        )
        self.results["phase1"] = phase1

        # ── Phase 2: 개요 상세화 ──
        phase2 = self.run_phase(
            phase_num=2,
            phase_name="설교 개요 상세화",
            system_prompt=PHASE2_SYSTEM,
            user_prompt=get_phase2_prompt(phase1, sermon_duration),
            filename=f"{timestamp}_phase2_개요.md",
        )
        self.results["phase2"] = phase2

        # ── Phase 3: 피드백 시뮬레이션 ──
        phase3 = self.run_phase(
            phase_num=3,
            phase_name="통합 피드백 및 시뮬레이션",
            system_prompt=PHASE3_SYSTEM,
            user_prompt=get_phase3_prompt(phase2),
            filename=f"{timestamp}_phase3_피드백.md",
        )
        self.results["phase3"] = phase3

        # ── Phase 4: 원고 작성 ──
        phase4 = self.run_phase(
            phase_num=4,
            phase_name="설교문 원고 작성",
            system_prompt=PHASE4_SYSTEM,
            user_prompt=get_phase4_prompt(phase2, phase3, sermon_context, sermon_tone, sermon_duration),
            filename=f"{timestamp}_phase4_원고.md",
        )
        self.results["phase4"] = phase4

        # ── Phase 5: 최종 완성 ──
        phase5 = self.run_phase(
            phase_num=5,
            phase_name="최종 수정 및 완료",
            system_prompt=PHASE5_SYSTEM,
            user_prompt=get_phase5_prompt(phase4, sermon_date),
            filename=f"{timestamp}_phase5_최종.md",
        )
        self.results["phase5"] = phase5

        # 완료 메시지
        console.print()
        console.print(
            Panel(
                "[bold green]🎉 설교 작성이 완료되었습니다![/bold green]\n\n"
                f"📂 결과 파일: [cyan]{self.date_dir}[/cyan]",
                title="[bold]완료[/bold]",
                width=60,
            )
        )

        return self.results
