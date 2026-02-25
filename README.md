# 🔖 설교 작성 자동화 시스템 (Sermon Auto v1.0)

윤영천 목사님의 **설교 작성 SOP v3.0**을 Gemini AI로 자동화하는 CLI 도구입니다.

성경 범위만 입력하면 **본문 선정 → 개요 → 피드백 → 원고 → 최종 패키지**까지
5단계를 자동 실행하여 Word 파일로 제출합니다.

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 1-1. 의존성 설치
pip install -r requirements.txt

# 1-2. 환경 변수 설정
copy .env.example .env
# .env 파일을 열고 GEMINI_API_KEY를 입력하세요
# API 키 발급: https://aistudio.google.com/app/apikey
```

### 2. 실행

```bash
# 대화형 모드 (성경 범위를 직접 입력)
python main.py

# 직접 지정 모드
python main.py --range "에스겔 36-37장"
```

### 3. 결과 확인

`output/` 폴더에 다음 파일들이 생성됩니다:

| 파일명 | 설명 |
|--------|------|
| `*_phase1_본문선정.md` | Phase 1: 본문 선정 및 주제 개발 |
| `*_phase2_개요.md` | Phase 2: 설교 개요 상세화 |
| `*_phase3_피드백.md` | Phase 3: 통합 피드백 및 시뮬레이션 |
| `*_phase4_원고.md` | Phase 4: 설교문 원고 |
| `*_phase5_최종.md` | Phase 5: 최종 완성 패키지 |
| `*_설교_*.docx` | 📄 **최종 Word 파일** (설교 원고 + 부록) |

## 📂 프로젝트 구조

```
sermon-auto/
├── main.py                     # CLI 엔트리포인트
├── requirements.txt            # Python 의존성
├── .env.example                # 환경 변수 예제
├── sop/                        # SOP 원본 문서 (참조용)
├── src/
│   ├── config.py               # API 키, 모델 설정
│   ├── api_client.py           # Gemini API 클라이언트
│   ├── pipeline.py             # 파이프라인 오케스트레이터
│   ├── exporter.py             # Word(.docx) 출력
│   └── prompts/
│       ├── personas.py         # 윤비서 + 4인 페르소나 + 목회적 방어
│       ├── phase1.py           # 본문 선정 프롬프트
│       ├── phase2.py           # 개요 상세화 프롬프트
│       ├── phase3.py           # 피드백 시뮬레이션 프롬프트
│       ├── phase4.py           # 원고 작성 프롬프트
│       └── phase5.py           # 최종 수정 프롬프트
└── output/                     # 생성된 설교 파일
```

## 🎯 핵심 특징

- **원어 중심**: 히브리어/헬라어 원어의 신학적 함의 분석
- **사중복음**: 중생·성결·신유·재림의 균형잡힌 적용
- **4인 페르소나**: 지혜(워킹맘), 준서(청년), 민수(신앙인), 수진(새신자)
- **목회적 방어**: 복음의 날카로움 보존
- **완전 자동**: 성경 범위 입력 후 Phase 1~5 자동 실행

## ⚙️ 설정 커스터마이징

`.env` 파일에서 다음을 조정할 수 있습니다:

```env
GEMINI_API_KEY=your_api_key_here    # 필수
GEMINI_MODEL=gemini-2.0-flash       # 모델 변경 가능
```

## 📖 SOP 원본 문서

`sop/` 폴더에 원본 SOP v3.0 문서가 보관되어 있습니다.
프롬프트 커스터마이징 시 참고하세요.
