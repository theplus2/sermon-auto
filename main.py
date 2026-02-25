"""
설교 자동화 시스템 - CLI 엔트리포인트

사용법:
    python main.py                           # 대화형 모드 (성경 범위를 입력)
    python main.py --range "에스겔 36-37장"  # 직접 성경 범위 지정
"""

import click
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel

from src.config import validate_config, OUTPUT_DIR
from src.pipeline import SermonPipeline
from src.exporter import SermonExporter

console = Console()


@click.command()
@click.option(
    "--range", "bible_range",
    type=str,
    default=None,
    help='설교할 성경 범위 (예: "에스겔 36-37장")',
)
@click.option(
    "--date", "sermon_date",
    type=str,
    default=None,
    help='설교 예정일 (예: "2026-02-23"). 미입력 시 다음 주일 자동 설정.',
)
@click.option(
    "--context", "sermon_context",
    type=str,
    default=None,
    help=(
        '이번 주 성도들의 삶의 상황·교회 분위기 (선택). '
        '예: "새가족 환영회 후, 성도들이 직장 스트레스를 나눔" '
        '→ 서론 Hook과 대지 3 적용이 이 상황에 맞게 작성됩니다.'
    ),
)
@click.option(
    "--tone", "sermon_tone",
    type=click.Choice(["도전", "위로", "교육", "일상"], case_sensitive=False),
    default="일상",
    show_default=True,
    help=(
        '설교 전체 어조 선택.\n'
        '  도전: 강한 회개/결단 촉구\n'
        '  위로: 부드러운 은혜/공감\n'
        '  교육: 원어 분석 중심\n'
        '  일상: 생활 밀착형 대화체 (기본값)'
    ),
)
@click.option(
    "--duration", "sermon_duration",
    type=click.Choice(["15", "30", "40", "60"]),
    default="40",
    show_default=True,
    help=(
        '설교 예상 시간(분). '
        '15=새벽기도/수요예배, 30=짧은 주일설교, 40=주일설교(기본), 60=특별집회'
    ),
)
def main(
    bible_range: str | None,
    sermon_date: str | None,
    sermon_context: str | None,
    sermon_tone: str,
    sermon_duration: str,
) -> None:
    """🔖 설교 작성 자동화 시스템 (Sermon Auto v1.0)

    성경 범위와 설교 예정일을 입력하면 Phase 1~5를 자동으로 실행하여
    완성된 설교 원고를 Word 파일로 출력합니다.

    \b
    [사용 예시]
    python main.py                                      # 대화형 모드
    python main.py --range "에스겔 36장" --date 2026-03-01
    python main.py --range "요한복음 3장" --tone 위로 --duration 30
    python main.py --range "로마서 8장" --context "이번 주 교인이 많이 힘들어함"

    \b
    [명령어 전체 목록 확인]
    python main.py --help
    """

    # ── 헤더 출력 ──
    console.print()
    console.print(
        Panel(
            "[bold yellow]🔖 설교 작성 자동화 시스템[/bold yellow]\n"
            "[dim]Powered by Gemini AI & 성결교회 사중복음 신학[/dim]",
            title="[bold]Sermon Auto v1.0[/bold]",
            subtitle="윤비서와 함께하는 설교 준비",
            width=60,
        )
    )

    # ── 설정 검증 ──
    try:
        validate_config()
    except ValueError as e:
        console.print(f"\n{e}")
        return

    # ── 성경 범위 입력 ──
    if bible_range is None:
        console.print()
        bible_range = click.prompt(
            "📖 설교할 성경 범위를 입력하세요",
            type=str,
        )

    if not bible_range.strip():
        console.print("[red]❌ 성경 범위를 입력해주세요.[/red]")
        return

    # ── 설교 예정일 입력 ──
    # 기본값: 다음 주일(일요일)
    def _next_sunday() -> str:
        today = datetime.now()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7  # 오늘이 일요일이면 다음 주일
        return (today + timedelta(days=days_until_sunday)).strftime("%Y-%m-%d")

    if sermon_date is None:
        console.print()
        default_date = _next_sunday()
        sermon_date = click.prompt(
            "📅 설교 예정일을 입력하세요 (YYYY-MM-DD)",
            type=str,
            default=default_date,
        )

    # 날짜 형식 검증
    try:
        parsed_date = datetime.strptime(sermon_date.strip(), "%Y-%m-%d")
        sermon_date_str = parsed_date.strftime("%Y년 %m월 %d일")
    except ValueError:
        console.print("[red]❌ 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.[/red]")
        return

    # ── 파이프라인 실행 ──
    console.print()
    console.print(f"📖 [bold]{bible_range}[/bold] 범위로 설교를 준비합니다...")
    console.print(f"📅 설교 예정일: [bold]{sermon_date_str}[/bold]")
    console.print(f"🎙️  설교 톤: [bold]{sermon_tone}[/bold]  ⏱️ 예상 시간: [bold]{sermon_duration}분[/bold]")
    if sermon_context:
        console.print(f"📌 이번 주 상황: [italic]{sermon_context}[/italic]")
    console.print("[dim]Phase 1→2→3→4→5 완전 자동 실행 모드[/dim]")
    console.print()

    pipeline = SermonPipeline()

    try:
        results = pipeline.run(
            bible_range,
            sermon_date_str,
            sermon_context=sermon_context,
            sermon_tone=sermon_tone,
            sermon_duration=sermon_duration,
        )
    except Exception as e:
        console.print(f"\n[bold red]❌ 오류 발생:[/bold red] {e}")
        console.print("[dim]API 키를 확인하거나 네트워크 연결을 점검해주세요.[/dim]")
        return

    # ── Word 파일 출력 ──
    console.print()
    console.print("[bold]📄 Word 파일 생성 중...[/bold]")

    try:
        exporter = SermonExporter(OUTPUT_DIR)
        docx_path = exporter.export(results, bible_range, sermon_date_str)
    except Exception as e:
        console.print(f"\n[bold red]❌ Word 파일 생성 오류:[/bold red] {e}")
        console.print("[dim]python-docx 설치를 확인해주세요: pip install python-docx[/dim]")
        return

    # ── 완료 메시지 ──
    console.print()
    console.print(
        Panel(
            "[bold green]🎉 설교 준비가 완료되었습니다![/bold green]\n\n"
            f"📅 설교 예정일: [bold]{sermon_date_str}[/bold]\n"
            f"📄 Word 파일: [cyan]{docx_path}[/cyan]\n"
            f"📂 Phase별 결과: [cyan]{pipeline.date_dir}[/cyan]\n\n"
            "[dim]각 Phase별 상세 결과는 날짜 폴더에서 확인하실 수 있습니다.[/dim]",
            title="[bold]✅ 완료[/bold]",
            width=60,
        )
    )


if __name__ == "__main__":
    main()
