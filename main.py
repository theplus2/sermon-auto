"""
설교 자동화 시스템 - CLI 엔트리포인트

사용법:
    python main.py generate                        # 대화형 모드
    python main.py generate --range "에스겔 36장"   # 설교 생성
    python main.py feedback                        # 설교 후 피드백 수집
"""

import click
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from src.config import validate_config, OUTPUT_DIR, FEEDBACK_DIR
from src.pipeline import SermonPipeline
from src.exporter import SermonExporter

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """🔖 설교 작성 자동화 시스템 (Sermon Auto v1.0)

    \b
    [명령어 목록]
    python main.py generate   — 설교 원고 생성
    python main.py feedback   — 설교 후 피드백 수집
    python main.py --help     — 도움말 보기
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command(name="generate")
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
        '설교 전체 어조 선택. '
        '도전: 강한 회개/결단 촉구 | 위로: 부드러운 은혜/공감 | '
        '교육: 원어 분석 중심 | 일상: 생활 밀착형 대화체 (기본값)'
    ),
)
@click.option(
    "--duration", "sermon_duration",
    type=click.Choice(["15", "30", "40", "60"]),
    default="30",
    show_default=True,
    help=(
        '설교 예상 시간(분). '
        '15=새벽기도/수요예배, 30=주일설교(기본), 40=길게 보는 주일설교, 60=특별집회'
    ),
)
@click.option(
    "--audience", "sermon_audience",
    type=click.Choice(["일반", "어르신", "청소년", "새신자전용"], case_sensitive=False),
    default="일반",
    show_default=True,
    help=(
        '대상 청중 선택. '
        '일반(기본), 어르신(온유한 어조), '
        '청소년(정체성/미래 중심), 새신자전용(쉽고 짧은 문장)'
    ),
)
def main(
    bible_range: str | None,
    sermon_date: str | None,
    sermon_context: str | None,
    sermon_tone: str,
    sermon_duration: str,
    sermon_audience: str,
) -> None:
    """📖 설교 원고 생성

    \b
    [사용 예시]
    python main.py generate
    python main.py generate --range "에스겔 36장" --date 2026-03-01
    python main.py generate --range "요한복음 3장" --tone 위로 --duration 30
    python main.py generate --range "시편 23편" --audience 어르신 --duration 15
    python main.py generate --range "로마서 8장" --context "이번 주 교인이 힘들어함"
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
    console.print(f"🎙️  설교 톤: [bold]{sermon_tone}[/bold]  ⏱️ 예상 시간: [bold]{sermon_duration}분[/bold]  👥 청중: [bold]{sermon_audience}[/bold]")
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
            sermon_audience=sermon_audience,
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


@cli.command(name="feedback")
def feedback_cmd() -> None:
    """📝 설교 후 피드백 수집 (대화형)

    \b
    [사용법]
    python main.py feedback

    몇 가지 질문에 답하면 피드백이 feedback/ 폴더에 자동 저장됩니다.
    다음 설교 생성 시 AI가 자동으로 읽고 스타일에 반영합니다.
    """
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

    console.print()
    console.print(
        Panel(
            "[bold yellow]📝 설교 피드백 수집[/bold yellow]\n"
            "[dim]답변하신 내용은 feedback/ 폴더에 저장되어\n"
            "다음 설교 작성 시 AI가 자동으로 반영합니다.[/dim]",
            title="[bold]Sermon Auto — 피드백[/bold]",
            width=60,
        )
    )
    console.print()

    # Step 1: 대상 설교 날짜
    console.print("[bold cyan]①  어느 설교에 대한 피드백인가요?[/bold cyan]")
    console.print("[dim]   예: 2026-03-02  (미입력 시 오늘 날짜로 설정)[/dim]")
    feedback_date_raw = click.prompt("   날짜 (YYYY-MM-DD)", default=datetime.now().strftime("%Y-%m-%d"))
    try:
        feedback_date = datetime.strptime(feedback_date_raw.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        console.print("[red]❌ 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요.[/red]")
        return

    lines: list[str] = [
        f"# 피드백 — {feedback_date} 설교",
        f"_작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
    ]

    # Step 2: 질문세트 정의
    questions = [
        ("②", "이번 설교에서 가장 잘 맞은 부분은 무엇인가요? (유지하고 싶은 것)", "잘 된 부분"),
        ("③", "다음엔 더 나아졌으면 하는 대목이 있나요? (예: 서론이 너무 길었다, 예화가 어색했다)", "개선할 점"),
        ("④", "예화나 비유 중 성도들이 가장 공감한 것은 무엇이었나요?", "좋았던 예화 유형"),
        ("⑤", "피하고 싶은 예화 유형이 있나요? (없으면 Enter)", "피하고 싶은 예화"),
        ("⑥", "설교 분량에 대한 의견을 주세요. (예: 결론이 짧았다, 다음에는 30분으로 하고 싶다)", "분량 고려사항"),
        ("⑦", "신학적으로 더 강조했다면 좋았을 부분이 있나요? (없으면 Enter)", "신학적 강조점"),
        ("⑧", "기타 자유롭게 나누고 싶은 의견을 적어주세요. (없으면 Enter)", "기타"),
    ]

    console.print()
    for icon, question, label in questions:
        console.print(f"[bold cyan]{icon}  {question}[/bold cyan]")
        answer = click.prompt("   답변", default="", show_default=False)
        answer = answer.strip()
        lines.append(f"## {label}")
        lines.append(answer if answer else "(특별 의견 없음)")
        lines.append("")
        console.print()

    # Step 3: 파일 저장
    filename = f"{feedback_date}_피드백.md"
    filepath = FEEDBACK_DIR / filename
    filepath.write_text("\n".join(lines), encoding="utf-8")

    console.print(
        Panel(
            f"[bold green]✅ 피드백이 저장되었습니다![/bold green]\n\n"
            f"📂 저장 위치: [cyan]{filepath}[/cyan]\n\n"
            "[dim]다음에 'python main.py generate ...' 를 실행하면\n"
            "AI가 이 피드백을 자동으로 반영합니다.[/dim]",
            title="[bold]피드백 완료[/bold]",
            width=60,
        )
    )


if __name__ == "__main__":
    cli()
